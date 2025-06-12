import bpy
import math
from dataclasses import dataclass, field
from typing import Tuple, Optional
from mathutils import Vector, Matrix

def create_control_point(location, name, parent=None):
    bpy.ops.object.empty_add(type='SPHERE', location=location)
    empty = bpy.context.active_object
    empty.name = name
    empty.empty_display_size = 0.05
    
    if parent is not None:
        empty.parent = parent
        empty.parent_type = 'OBJECT'
        empty.matrix_parent_inverse = parent.matrix_world.inverted()
    
    return empty

def get_point_offset_from_end(start, end, distance_from_end):
    start_vec = Vector(start)
    end_vec = Vector(end)
    
    direction = end_vec - start_vec
    line_length = direction.length
    
    if distance_from_end >= line_length:
        return start_vec
    if distance_from_end <= 0:
        return end_vec
    
    direction.normalize()
    return end_vec - direction * distance_from_end