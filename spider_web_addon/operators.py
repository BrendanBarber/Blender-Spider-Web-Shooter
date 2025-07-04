import bpy
from mathutils import Vector
from bpy_extras.object_utils import AddObjectHelper, object_data_add

from .utils import *
from .config import SpiderWebConfig
from .spider_web import SpiderWeb
from .spider_spread import SpiderSpread
from .spider_shot import SpiderShot

def find_web_components(context):
    """Find all web components, prioritizing selected objects"""
    selected_objects = context.selected_objects
    
    spider_web_empty = None
    origin_empty = None
    target_empty = None
    web_empties = []
    web_curves = []
    shot_objects = []  # For tethers, projectiles, trails
    
    # Look for web components in selection first
    for obj in selected_objects:
        if obj.type == 'EMPTY':
            if obj.name.startswith("SpiderWeb"):
                spider_web_empty = obj
            elif obj.name.startswith("WebOrigin"):
                origin_empty = obj
            elif obj.name.startswith("WebTarget"):
                target_empty = obj
            elif obj.name.startswith("Web"):
                web_empties.append(obj)
        elif obj.type == 'MESH':
            if obj.name.startswith("Web"):
                web_curves.append(obj)
            elif obj.name.startswith("SpiderTether") or obj.name.startswith("SpiderProjectile") or obj.name.startswith("SpiderProjectileTrail"):
                shot_objects.append(obj)
    
    # If we don't have all components, search all objects
    if not spider_web_empty or not origin_empty or not target_empty:
        for obj in bpy.data.objects:
            if obj.type == 'EMPTY':
                if obj.name.startswith("SpiderWeb") and not spider_web_empty:
                    spider_web_empty = obj
                elif obj.name.startswith("WebOrigin") and not origin_empty:
                    origin_empty = obj
                elif obj.name.startswith("WebTarget") and not target_empty:
                    target_empty = obj
                elif obj.name.startswith("Web") and obj not in web_empties:
                    web_empties.append(obj)
            elif obj.type == 'MESH':
                if obj.name.startswith("Web") and obj not in web_curves:
                    web_curves.append(obj)
                elif (obj.name.startswith("SpiderTether") or obj.name.startswith("SpiderProjectile") or obj.name.startswith("SpiderProjectileTrail")) and obj not in shot_objects:
                    shot_objects.append(obj)
    
    return spider_web_empty, origin_empty, target_empty, web_empties, web_curves, shot_objects

class MESH_OT_create_spider_web_from_coords(bpy.types.Operator):
    bl_idname = "mesh.create_spider_web_coords"
    bl_label = "Create Web from Coordinates"
    bl_description = "Create spider web using the coordinates in the panel"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            props = context.scene.spider_web_props
            config = props.to_config()
            
            origin = props.origin_vector
            target = props.target_vector
            
            spider_web = SpiderWeb(origin, target, config)
            spider_web.create_web(context)
            
            self.report({'INFO'}, f"Created web from {origin} to {target}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create web: {str(e)}")
            print(f"Spider web creation error: {e}")
            return {'CANCELLED'}

class MESH_OT_update_spider_web_position(bpy.types.Operator):
    bl_idname = "mesh.update_spider_web_position"
    bl_label = "Update Selected Web Position"
    bl_description = "Update position of spider web based on origin and target empty positions (preserves all original properties)"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            # Find spider web components
            spider_web_empty, origin_empty, target_empty, web_empties, web_curves, shot_objects = find_web_components(context)
            
            if not spider_web_empty or not origin_empty or not target_empty:
                self.report({'ERROR'}, "Could not find SpiderWeb, WebOrigin and WebTarget empties")
                return {'CANCELLED'}
            
            # Load the ORIGINAL configuration from the SpiderWeb empty's custom properties
            # This preserves ALL original settings and ignores current panel settings
            original_config = self.load_original_config_from_web(spider_web_empty)
            
            # Load the existing random values from the SpiderWeb empty to preserve exact appearance
            existing_edge_random, existing_interior_random = SpiderSpread.load_random_values_from_empty(
                spider_web_empty, 
                original_config.spider_spread_config.density_spoke, 
                original_config.spider_spread_config.density_rib
            )
            
            # Get new origin and target positions from the empties (convert to world coordinates)
            new_origin = origin_empty.matrix_world.translation
            new_target = target_empty.matrix_world.translation
            
            # Delete all existing web components except SpiderWeb, origin and target
            self.cleanup_web_components(web_empties, web_curves, shot_objects)
            
            # Create new spider web with updated positions but ORIGINAL configuration
            spider_web = SpiderWeb(new_origin, new_target, original_config)
            
            # Restore the existing random values to preserve the web's exact appearance
            spider_web.spider_spread.set_random_values(existing_edge_random, existing_interior_random)
            
            # Create the spread using existing origin and target empties
            spider_web.spider_spread.create_spread(origin_empty, target_empty)
            spider_web.spider_spread.create_mesh(context, origin_empty, target_empty)
            
            # Create shot (tether or projectile) with original settings
            if original_config.spider_shot_config.is_tethered:
                # For tethered shots, we need web_center_empty for the tether connection
                web_center_empty = spider_web.spider_spread.web_center
                spider_web.spider_shot.create_shot(context, origin_empty, target_empty, web_center_empty)
            else:
                # For projectile shots
                spider_web.spider_shot.create_shot(context, origin_empty, target_empty)
            
            # Animate everything if enabled
            if spider_web.config.animate_web:
                # Animate the shot first
                spider_web.spider_shot.animate_shot(
                    context, origin_empty, target_empty, 
                    spider_web.config.start_frame
                )
                
                # Calculate when the spread should start (after shot completes)
                shot_travel_time = spider_web.config.spider_shot_config.shoot_time  # in seconds
                spread_start_frame = spider_web.config.start_frame + int(shot_travel_time * (context.scene.render.fps / context.scene.render.fps_base))
                
                # Animate the spread starting after the shot reaches the target
                spider_web.spider_spread.animate_spread(
                    context, origin_empty, target_empty, 
                    spread_start_frame,  # Start after shot completes
                    spider_web.config.spider_spread_config.spread_time
                )
            
            # Store the config back (preserving all original settings including random values)
            spider_web.spider_shot.store_config_on_empty(spider_web_empty)
            spider_web.spider_spread.store_config_on_empty(spider_web_empty)
            spider_web.store_config_on_empty(spider_web_empty)
            
            self.report({'INFO'}, f"Updated spider web position from {new_origin} to {new_target} with original settings preserved")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error updating spider web position: {str(e)}")
            print(f"Spider web position update error: {e}")
            return {'CANCELLED'}
    
    def load_original_config_from_web(self, spider_web_empty):
        """Load the original configuration from the web's stored properties, ignoring panel"""
        config = SpiderWebConfig()
        
        # Load spider spread config from SpiderWeb empty
        spread_config = SpiderSpread.load_config_from_empty(spider_web_empty)
        config.spider_spread_config = spread_config
        
        # Load spider shot config from SpiderWeb empty  
        shot_config = SpiderShot.load_config_from_empty(spider_web_empty)
        config.spider_shot_config = shot_config
        
        # Load web-level config if it exists
        if "spider_web_animate_web" in spider_web_empty:
            config.animate_web = spider_web_empty["spider_web_animate_web"]
        if "spider_web_start_frame" in spider_web_empty:
            config.start_frame = int(spider_web_empty["spider_web_start_frame"])
        
        return config
    
    def cleanup_web_components(self, web_empties, web_curves, shot_objects):
        """Delete all web components except SpiderWeb, origin and target empties"""
        # Delete web curve objects
        for curve_obj in web_curves:
            bpy.data.objects.remove(curve_obj, do_unlink=True)
        
        # Delete shot objects (tethers, projectiles, trails)
        for shot_obj in shot_objects:
            bpy.data.objects.remove(shot_obj, do_unlink=True)
        
        # Delete web empties except SpiderWeb, origin and target
        empties_to_delete = [obj for obj in web_empties 
                           if not obj.name.startswith("SpiderWeb")
                           and not obj.name.startswith("WebOrigin") 
                           and not obj.name.startswith("WebTarget")]
        for empty in empties_to_delete:
            bpy.data.objects.remove(empty, do_unlink=True)

class MESH_OT_update_spider_web_selected(bpy.types.Operator):
    bl_idname = "mesh.update_spider_web"
    bl_label = "Update Selected Web Properties"
    bl_description = "Update all properties of spider web using current panel settings (preserves positions)"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            # Find spider web components
            spider_web_empty, origin_empty, target_empty, web_empties, web_curves, shot_objects = find_web_components(context)
            
            if not spider_web_empty or not origin_empty or not target_empty:
                self.report({'ERROR'}, "Could not find SpiderWeb, WebOrigin and WebTarget empties")
                return {'CANCELLED'}
            
            # Get CURRENT positions from the empties (preserve these positions)
            current_origin = origin_empty.matrix_world.translation
            current_target = target_empty.matrix_world.translation
            
            # Get NEW configuration from panel properties
            props = context.scene.spider_web_props
            new_config = props.to_config()
            
            # Check if randomness settings have changed - if not, preserve existing random values
            old_config = self.load_original_config_from_web(spider_web_empty)
            preserve_random_values = (
                old_config.spider_spread_config.random_spread_edge == new_config.spider_spread_config.random_spread_edge and
                old_config.spider_spread_config.random_spread_interior == new_config.spider_spread_config.random_spread_interior and
                old_config.spider_spread_config.density_spoke == new_config.spider_spread_config.density_spoke and
                old_config.spider_spread_config.density_rib == new_config.spider_spread_config.density_rib
            )
            
            existing_edge_random = {}
            existing_interior_random = {}
            
            if preserve_random_values:
                # Load existing random values to preserve web appearance
                existing_edge_random, existing_interior_random = SpiderSpread.load_random_values_from_empty(
                    spider_web_empty, 
                    old_config.spider_spread_config.density_spoke, 
                    old_config.spider_spread_config.density_rib
                )
            
            # Delete all existing web components except SpiderWeb, origin and target
            self.cleanup_web_components(web_empties, web_curves, shot_objects)
            
            # Create new spider web with current positions and NEW properties from panel
            spider_web = SpiderWeb(current_origin, current_target, new_config)
            
            # If preserving random values, restore them before creating the spread
            if preserve_random_values and existing_edge_random and existing_interior_random:
                spider_web.spider_spread.set_random_values(existing_edge_random, existing_interior_random)
            
            # Create the spread using existing origin and target empties
            spider_web.spider_spread.create_spread(origin_empty, target_empty)
            spider_web.spider_spread.create_mesh(context, origin_empty, target_empty)

            # Create shot (tether or projectile) with new settings
            if new_config.spider_shot_config.is_tethered:
                # For tethered shots, we need web_center_empty for the tether connection
                web_center_empty = spider_web.spider_spread.web_center
                spider_web.spider_shot.create_shot(context, origin_empty, target_empty, web_center_empty)
            else:
                # For projectile shots
                spider_web.spider_shot.create_shot(context, origin_empty, target_empty)

            # Animate everything if enabled
            if spider_web.config.animate_web:
                # Animate the shot first
                spider_web.spider_shot.animate_shot(
                    context, origin_empty, target_empty, 
                    spider_web.config.start_frame
                )
                
                # Calculate when the spread should start (after shot completes)
                shot_travel_time = spider_web.config.spider_shot_config.shoot_time  # in seconds
                spread_start_frame = spider_web.config.start_frame + int(shot_travel_time * (context.scene.render.fps / context.scene.render.fps_base))
                
                # Animate the spread starting after the shot reaches the target
                spider_web.spider_spread.animate_spread(
                    context, origin_empty, target_empty, 
                    spread_start_frame,  # Start after shot completes
                    spider_web.config.spider_spread_config.spread_time
                )
            
            # Store updated config on the SpiderWeb empty
            spider_web.spider_shot.store_config_on_empty(spider_web_empty)
            spider_web.spider_spread.store_config_on_empty(spider_web_empty)
            spider_web.store_config_on_empty(spider_web_empty)
            
            if preserve_random_values:
                self.report({'INFO'}, "Updated spider web with new properties (preserved random pattern)")
            else:
                self.report({'INFO'}, "Updated spider web with new properties (new random pattern)")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error updating spider web properties: {str(e)}")
            print(f"Spider web property update error: {e}")
            return {'CANCELLED'}
    
    def load_original_config_from_web(self, spider_web_empty):
        """Load the original configuration from the web's stored properties"""
        config = SpiderWebConfig()
        
        # Load spider spread config from SpiderWeb empty
        spread_config = SpiderSpread.load_config_from_empty(spider_web_empty)
        config.spider_spread_config = spread_config
        
        # Load spider shot config from SpiderWeb empty  
        shot_config = SpiderShot.load_config_from_empty(spider_web_empty)
        config.spider_shot_config = shot_config
        
        # Load web-level config if it exists
        if "spider_web_animate_web" in spider_web_empty:
            config.animate_web = spider_web_empty["spider_web_animate_web"]
        if "spider_web_start_frame" in spider_web_empty:
            config.start_frame = int(spider_web_empty["spider_web_start_frame"])
        
        return config
    
    def cleanup_web_components(self, web_empties, web_curves, shot_objects):
        """Delete all web components except SpiderWeb, origin and target empties"""
        # Delete web curve objects
        for curve_obj in web_curves:
            bpy.data.objects.remove(curve_obj, do_unlink=True)
        
        # Delete shot objects (tethers, projectiles, trails)
        for shot_obj in shot_objects:
            bpy.data.objects.remove(shot_obj, do_unlink=True)
        
        # Delete web empties except SpiderWeb, origin and target
        empties_to_delete = [obj for obj in web_empties 
                           if not obj.name.startswith("SpiderWeb")
                           and not obj.name.startswith("WebOrigin") 
                           and not obj.name.startswith("WebTarget")]
        for empty in empties_to_delete:
            bpy.data.objects.remove(empty, do_unlink=True)

class MESH_OT_set_origin_from_cursor(bpy.types.Operator):
    bl_idname = "mesh.set_origin_cursor"
    bl_label = "Set Origin from Cursor"
    bl_description = "Set origin coordinates from 3D cursor position"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        cursor_loc = context.scene.cursor.location
        context.scene.spider_web_props.set_origin(cursor_loc)
        self.report({'INFO'}, f"Origin set to {cursor_loc}")
        return {'FINISHED'}

class MESH_OT_set_target_from_cursor(bpy.types.Operator):
    bl_idname = "mesh.set_target_cursor"
    bl_label = "Set Target from Cursor"
    bl_description = "Set target coordinates from 3D cursor position"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        cursor_loc = context.scene.cursor.location
        context.scene.spider_web_props.set_target(cursor_loc)
        self.report({'INFO'}, f"Target set to {cursor_loc}")
        return {'FINISHED'}