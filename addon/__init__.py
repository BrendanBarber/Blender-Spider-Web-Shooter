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

classes = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # Add properties to scene

def unregister():
    # Delete properties from scene

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()