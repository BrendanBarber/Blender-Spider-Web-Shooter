import bpy
import math
from dataclasses import dataclass, field
from typing import Tuple, Optional
from mathutils import Vector, Matrix
from .utils import *
from .config import *

class SpiderShot:
    """The web shot"""
    def __init__(self, origin: Tuple[float, float, float], target: Tuple[float, float, float], config: SpiderShotConfig = None):
        self.origin = origin
        self.target = target
        self.config = config or SpiderShotConfig()

        self.shot_mesh = None
        self.tether_mesh = None
    
    def store_config_on_empty(self, empty):
        """Store the shot configuration as custom properties on the empty"""
        # Use Blender's proper custom property system with UI metadata
        empty["spider_shot_shoot_time"] = self.config.shoot_time
        empty.id_properties_ui("spider_shot_shoot_time").update(
            description="Time for web to shoot out and reach target (in frames)",
            default=1.0,
            min=1.0
        )
        
        empty["spider_shot_is_tethered"] = self.config.is_tethered
        empty.id_properties_ui("spider_shot_is_tethered").update(
            description="Whether the web shot is tethered or projectile",
            default=True
        )
        
        # Tether properties
        tether_width = self.config.tether_width if self.config.tether_width is not None else 0.1
        empty["spider_shot_tether_width"] = tether_width
        empty.id_properties_ui("spider_shot_tether_width").update(
            description="Width of the tether strand",
            default=0.1,
            min=0.001
        )
        
        tether_slack = self.config.tether_slack if self.config.tether_slack is not None else 0.05
        empty["spider_shot_tether_slack"] = tether_slack
        empty.id_properties_ui("spider_shot_tether_slack").update(
            description="Amount of slack in the tether",
            default=0.05,
            min=0.0
        )
        
        # Projectile properties
        projectile_size = self.config.projectile_size if self.config.projectile_size is not None else 0.5
        empty["spider_shot_projectile_size"] = projectile_size
        empty.id_properties_ui("spider_shot_projectile_size").update(
            description="Size of the projectile web ball",
            default=0.5,
            min=0.001
        )
        
        projectile_trail_length = self.config.projectile_trail_length if self.config.projectile_trail_length is not None else 1.0
        empty["spider_shot_projectile_trail_length"] = projectile_trail_length
        empty.id_properties_ui("spider_shot_projectile_trail_length").update(
            description="Length of the projectile trail",
            default=1.0,
            min=0.0
        )

    def create_shot(self, context, origin_empty, target_empty, web_center_empty):
        if self.config.is_tethered:
            self.create_tether_mesh(context, origin_empty, web_center_empty)
        else:
            self.create_shot_mesh(context, origin_empty, target_empty)

    def animate_shot(self):
        pass

    def create_shot_mesh(self, context, origin_empty, target_empty):
        """Creates the shot ball and trail for the web animation"""
        # Create sphere mesh
        bpy.ops.mesh.primitive_uv_sphere_add(location=(0,0,0))
        sphere_obj = context.active_object
        sphere_obj.name = "WebShot"
        sphere_obj.parent = origin_empty
        sphere_obj.parent_type = 'OBJECT'
        
        sphere_obj.scale = (self.config.projectile_size, self.config.projectile_size, self.config.projectile_size)
        sphere_obj.hide_viewport = True
        sphere_obj.hide_render = True
        
        self.shot_mesh = sphere_obj

    def create_tether_mesh(self, context, origin_empty, web_center_empty):
        """Creates a rope-like tether connecting origin to web center"""
        
        # Calculate the base distance between origin and web center
        origin_pos = Vector(origin_empty.location)
        web_center_pos = Vector(web_center_empty.location)
        base_distance = (web_center_pos - origin_pos).length
        
        # Add slack to the tether length
        tether_length = base_distance + (base_distance * self.config.tether_slack)
        
        # Create a curve object for the tether
        curve_data = bpy.data.curves.new(name="WebTetherCurve", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 64  # High resolution for smooth rope
        curve_data.bevel_depth = self.config.tether_width / 2  # Make it cylindrical
        curve_data.bevel_resolution = 8  # Circular cross-section
        
        # Create the curve object
        tether_obj = bpy.data.objects.new("WebTether", curve_data)
        context.collection.objects.link(tether_obj)
        
        # Create a spline (the actual curve path)
        spline = curve_data.splines.new('NURBS')
        
        # Calculate number of control points based on tether length for natural droop
        num_points = max(8, int(tether_length * 10))  # More points for longer tethers
        spline.points.add(num_points - 1)  # -1 because spline starts with 1 point
        
        # Set control points to create a catenary curve (rope hanging under gravity)
        for i in range(num_points):
            t = i / (num_points - 1)  # Parameter from 0 to 1
            
            # Linear interpolation between start and end points
            linear_pos = origin_pos.lerp(web_center_pos, t)
            
            # Add catenary sag (rope hanging under its own weight)
            # Use a simplified catenary approximation: y = a * cosh(x/a) - a
            sag_amount = self.config.tether_slack * base_distance * 0.5
            catenary_factor = math.cosh((t - 0.5) * 4) - 1  # Normalized catenary
            sag_offset = catenary_factor * sag_amount
            
            # Apply sag in the direction perpendicular to the rope
            rope_direction = (web_center_pos - origin_pos).normalized()
            
            # Find a perpendicular direction (preferably downward)
            if abs(rope_direction.z) < 0.9:
                sag_direction = Vector((0, 0, -1))  # Downward
            else:
                sag_direction = Vector((1, 0, 0))  # Sideways if rope is mostly vertical
            
            # Make sure sag direction is perpendicular to rope
            sag_direction = sag_direction - sag_direction.dot(rope_direction) * rope_direction
            sag_direction.normalize()
            
            # Apply the sag
            final_pos = linear_pos + sag_direction * sag_offset
            
            # Set the point (NURBS points use homogeneous coordinates, so w=1)
            spline.points[i].co = (final_pos.x, final_pos.y, final_pos.z, 1.0)
        
        # Set spline properties for smooth curve
        spline.order_u = min(4, num_points)  # Cubic or less if not enough points
        spline.use_endpoint_u = True
        
        # Parent the tether to the origin empty
        tether_obj.parent = origin_empty
        tether_obj.parent_type = 'OBJECT'
        
        # Use geometry nodes or drivers to make the tether dynamic
        # Create a geometry nodes modifier for dynamic rope behavior
        if hasattr(bpy.types, 'GeometryNodeTree'):
            # Add a geometry nodes modifier for dynamic curve updates
            geo_modifier = tether_obj.modifiers.new("TetherDynamic", 'NODES')
            
            # Create a simple node tree that can update curve points
            # For now, we'll use constraints as a simpler approach
        
        # Alternative approach: Use constraints to make the curve dynamic
        # Add a constraint to track the web center with the last control point
        constraint = tether_obj.constraints.new('TRACK_TO')
        constraint.target = web_center_empty
        constraint.track_axis = 'TRACK_Z'
        constraint.up_axis = 'UP_Y'
        constraint.influence = 0.3  # Partial influence for natural rope behavior
        
        # Add damped track for more natural movement
        damped_constraint = tether_obj.constraints.new('DAMPED_TRACK')
        damped_constraint.target = web_center_empty
        damped_constraint.track_axis = 'TRACK_Z'
        damped_constraint.influence = 0.5
        
        # Store reference to the tether mesh
        self.tether_mesh = tether_obj
        
        return tether_obj

    def animate_shot(self):
        pass

    def animate_tether(self):
        pass
    
    @staticmethod
    def load_config_from_empty(empty):
        """Load the shot configuration from custom properties on the empty"""
        config = SpiderShotConfig()
        
        if "spider_shot_shoot_time" in empty:
            config.shoot_time = empty["spider_shot_shoot_time"]
        if "spider_shot_is_tethered" in empty:
            config.is_tethered = empty["spider_shot_is_tethered"]
        if "spider_shot_tether_width" in empty:
            config.tether_width = empty["spider_shot_tether_width"] if empty["spider_shot_tether_width"] != 0.0 else None
        if "spider_shot_tether_slack" in empty:
            config.tether_slack = empty["spider_shot_tether_slack"] if empty["spider_shot_tether_slack"] != 0.0 else None
        if "spider_shot_projectile_size" in empty:
            config.projectile_size = empty["spider_shot_projectile_size"] if empty["spider_shot_projectile_size"] != 0.0 else None
        if "spider_shot_projectile_trail_length" in empty:
            config.projectile_trail_length = empty["spider_shot_projectile_trail_length"] if empty["spider_shot_projectile_trail_length"] != 0.0 else None
        
        return config