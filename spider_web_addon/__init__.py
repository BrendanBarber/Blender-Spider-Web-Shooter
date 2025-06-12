bl_info = {
    "name": "Spider Webshooter Generator",
    "author": "Brendan Barber",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Add > Mesh",
    "description": "Generate procedural spider webs that shoot",
    "warning": "",
    "doc_url": "",
    "category": "Add Mesh",
}

import bpy
from bpy.types import PropertyGroup
from bpy.props import PointerProperty

from . import operators
from . import panels
from . import properties

classes = [
    properties.SpiderShotProperties,
    properties.SpiderSpreadProperties, 
    properties.SpiderWebProperties,
    operators.MESH_OT_create_spider_web_from_coords,
    panels.VIEW3D_PT_spider_web_panel,
    panels.SPIDER_WEB_OT_load_config,
    panels.SPIDER_WEB_OT_save_config,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.spider_web_props = PointerProperty(type=properties.SpiderWebProperties)

def unregister():
    del bpy.types.Scene.spider_web_props
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()