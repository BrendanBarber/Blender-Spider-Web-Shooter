import bpy
from .config import SpiderWebConfig

class VIEW3D_PT_spider_web_panel(bpy.types.Panel):
    bl_label = "Spider Web Generator"
    bl_idname = "VIEW3D_PT_spider_web"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Spider Web"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.spider_web_props
        
        # Coordinates Section
        box = layout.box()
        box.label(text="Web Coordinates", icon='EMPTY_ARROWS')
        
        # Origin coordinates
        col = box.column()
        col.label(text="Origin:")
        row = col.row(align=True)
        row.prop(props, "origin_x", text="X")
        row.prop(props, "origin_y", text="Y") 
        row.prop(props, "origin_z", text="Z")
        
        # Helper buttons for origin
        row = col.row(align=True)
        row.operator("mesh.set_origin_cursor", text="From Cursor", icon='CURSOR')
        
        col.separator()
        
        # Target coordinates
        col.label(text="Target:")
        row = col.row(align=True)
        row.prop(props, "target_x", text="X")
        row.prop(props, "target_y", text="Y")
        row.prop(props, "target_z", text="Z")
        
        # Helper buttons for target
        row = col.row(align=True)
        row.operator("mesh.set_target_cursor", text="From Cursor", icon='CURSOR')

        col.separator()
        
        # Shot Properties Section
        box = layout.box()
        box.label(text="Shot Properties", icon='PARTICLES')
        box.prop(props.shot_props, "shoot_time")
        box.prop(props.shot_props, "is_tethered")
        
        if props.shot_props.is_tethered:
            box.prop(props.shot_props, "tether_width")
            box.prop(props.shot_props, "tether_slack")
        else:
            box.prop(props.shot_props, "projectile_size")
            box.prop(props.shot_props, "projectile_trail_length")
        
        # Spread Properties Section
        box = layout.box()
        box.label(text="Spread Properties", icon='MESH_GRID')
        box.prop(props.spread_props, "radius")
        box.prop(props.spread_props, "height")
        box.prop(props.spread_props, "spread_time")
        
        row = box.row()
        row.prop(props.spread_props, "density_spoke")
        row.prop(props.spread_props, "density_rib")
        
        box.prop(props.spread_props, "web_thickness")
        box.prop(props.spread_props, "curvature")
        
        col = box.column()
        col.label(text="Randomness:")
        col.prop(props.spread_props, "random_spread_edge")
        col.prop(props.spread_props, "random_spread_interior")
        
        # Action buttons
        layout.separator()
        layout.label(text="Create Web:", icon='MESH_GRID')
        
        col = layout.column(align=True)
        col.operator("mesh.create_spider_web_coords", text="Create from Coordinates", icon='MESH_GRID')
        col.operator("mesh.update_spider_web_position", text="Update Selected Position", icon="EMPTY_ARROWS")
        col.operator("mesh.update_spider_web", text="Update Selected Properties", icon='LIGHT_POINT')
        
        layout.separator()
        layout.operator("spider_web.load_config", text="Reset to Defaults")

class SPIDER_WEB_OT_load_config(bpy.types.Operator):
    bl_idname = "spider_web.load_config"
    bl_label = "Load Config"
    bl_description = "Load configuration from default or file"
    
    def execute(self, context):
        # Load default config
        default_config = SpiderWebConfig()
        context.scene.spider_web_props.from_config(default_config)
        self.report({'INFO'}, "Loaded default configuration")
        return {'FINISHED'}

class SPIDER_WEB_OT_save_config(bpy.types.Operator):
    bl_idname = "spider_web.save_config"
    bl_label = "Export Config"
    bl_description = "Print current configuration (for debugging)"
    
    def execute(self, context):
        config = context.scene.spider_web_props.to_config()
        print("Current Config:")
        print(f"Shot: {config.spider_shot_config}")
        print(f"Spread: {config.spider_spread_config}")
        self.report({'INFO'}, "Configuration printed to console")
        return {'FINISHED'}