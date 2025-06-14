import bpy
from mathutils import Vector
from bpy_extras.object_utils import AddObjectHelper, object_data_add

from .utils import *
from .config import SpiderWebConfig
from .spider_web import SpiderWeb
from .spider_spread import SpiderSpread
from .spider_shot import SpiderShot

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
    bl_description = "Update position of spider web based on origin and target empty positions"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            # Get selected objects
            selected_objects = context.selected_objects
            
            # Find spider web components by name patterns
            spider_web_empty = None
            origin_empty = None
            target_empty = None
            web_empties = []
            web_curves = []
            
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
                elif obj.type == 'MESH' and obj.name.startswith("WebCurve"):
                    web_curves.append(obj)
            
            # If we don't have all components, try to find them in all objects
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
                    elif obj.type == 'MESH' and obj.name.startswith("WebCurve") and obj not in web_curves:
                        web_curves.append(obj)
            
            if not spider_web_empty or not origin_empty or not target_empty:
                self.report({'ERROR'}, "Could not find SpiderWeb, WebOrigin and WebTarget empties")
                return {'CANCELLED'}
            
            # Load the original configuration from the SpiderWeb empty's custom properties
            props = context.scene.spider_web_props
            config = self.load_config_from_web(spider_web_empty, props)
            
            # Get new origin and target positions from the empties (convert to world coordinates)
            new_origin = origin_empty.matrix_world.translation
            new_target = target_empty.matrix_world.translation
            
            # Delete all existing web components except SpiderWeb, origin and target
            self.cleanup_web_components(web_empties, web_curves, spider_web_empty, origin_empty, target_empty)
            
            # Create new spider web with updated positions but original configuration
            spider_web = SpiderWeb(new_origin, new_target, config)
            
            # Create the spread using existing origin and target empties
            spider_web.spider_spread.create_spread(origin_empty, target_empty)
            spider_web.spider_spread.create_mesh(context, origin_empty, target_empty)
            
            # Update properties to match new positions (but don't change other settings)
            props.set_origin(new_origin)
            props.set_target(new_target)
            
            self.report({'INFO'}, f"Recreated spider web with original settings at new position from {new_origin} to {new_target}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error updating spider web position: {str(e)}")
            print(f"Spider web position update error: {e}")
            return {'CANCELLED'}
    
    def cleanup_web_components(self, web_empties, web_curves, spider_web_empty, origin_empty, target_empty):
        """Delete all web components except SpiderWeb, origin and target empties"""
        # Delete web curve objects
        for curve_obj in web_curves:
            bpy.data.objects.remove(curve_obj, do_unlink=True)
        
        # Delete web empties except SpiderWeb, origin and target
        empties_to_delete = [obj for obj in web_empties 
                           if not obj.name.startswith("SpiderWeb")
                           and not obj.name.startswith("WebOrigin") 
                           and not obj.name.startswith("WebTarget")]
        for empty in empties_to_delete:
            bpy.data.objects.remove(empty, do_unlink=True)
    
    def load_config_from_web(self, spider_web_empty, fallback_props):
        """Load the original configuration from the web's stored properties"""
        try:
            # Start with fallback config
            config = fallback_props.to_config()
            
            # Load spider spread config from SpiderWeb empty
            if spider_web_empty:
                spread_config = SpiderSpread.load_config_from_empty(spider_web_empty)
                config.spider_spread_config = spread_config
                
                # Load spider shot config from SpiderWeb empty
                shot_config = SpiderShot.load_config_from_empty(spider_web_empty)
                config.spider_shot_config = shot_config
            
            return config
            
        except Exception as e:
            print(f"Error loading config from web: {e}")
            # Fallback to current properties if loading fails
            return fallback_props.to_config()

class MESH_OT_update_spider_web_selected(bpy.types.Operator):
    bl_idname = "mesh.update_spider_web"
    bl_label = "Update Selected Web Properties"
    bl_description = "Update all properties of spider web that is currently selected"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            # Get the spider web properties from the scene
            props = context.scene.spider_web_props
            
            # Get selected objects
            selected_objects = context.selected_objects
            
            # Find spider web components by name patterns
            spider_web_empty = None
            origin_empty = None
            target_empty = None
            web_empties = []
            web_curves = []
            
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
                elif obj.type == 'MESH' and obj.name.startswith("WebCurve"):
                    web_curves.append(obj)
            
            # If we don't have components from selection, try to find them in all objects
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
                    elif obj.type == 'MESH' and obj.name.startswith("WebCurve") and obj not in web_curves:
                        web_curves.append(obj)
            
            if not spider_web_empty or not origin_empty or not target_empty:
                self.report({'ERROR'}, "Could not find SpiderWeb, WebOrigin and WebTarget empties")
                return {'CANCELLED'}
            
            # Update properties to match current empty positions (convert to world coordinates)
            props.set_origin(origin_empty.matrix_world.translation)
            props.set_target(target_empty.matrix_world.translation)
            
            # Delete all existing web components except SpiderWeb, origin and target
            self.cleanup_web_components(web_empties, web_curves, spider_web_empty, origin_empty, target_empty)
            
            # Regenerate the spider web with current properties from sidebar
            config = props.to_config()
            spider_web = SpiderWeb(props.origin_vector, props.target_vector, config)
            
            # Create the spread using existing origin and target empties
            spider_web.spider_spread.create_spread(origin_empty, target_empty)
            spider_web.spider_spread.create_mesh(context, origin_empty, target_empty)
            
            # Store updated config on the SpiderWeb empty
            spider_web.spider_shot.store_config_on_empty(spider_web_empty)
            spider_web.spider_spread.store_config_on_empty(spider_web_empty)
            
            self.report({'INFO'}, "Updated spider web with new properties from sidebar")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error updating spider web properties: {str(e)}")
            return {'CANCELLED'}
    
    def cleanup_web_components(self, web_empties, web_curves, spider_web_empty, origin_empty, target_empty):
        """Delete all web components except SpiderWeb, origin and target empties"""
        # Delete web curve objects
        for curve_obj in web_curves:
            bpy.data.objects.remove(curve_obj, do_unlink=True)
        
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
