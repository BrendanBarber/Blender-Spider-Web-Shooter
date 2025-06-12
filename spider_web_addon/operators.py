import bpy
from mathutils import Vector
from bpy_extras.object_utils import AddObjectHelper, object_data_add

from .config import SpiderWebConfig
from .spider_web import SpiderWeb

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
            spider_web.create_web()
            
            self.report({'INFO'}, f"Created web from {origin} to {target}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create web: {str(e)}")
            print(f"Spider web creation error: {e}")
            return {'CANCELLED'}
