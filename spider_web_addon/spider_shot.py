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

    def create_tether_mesh(self, context, origin_empty, web_center_empty):
        """Creates a rope tether with NURBS path hooking to connect last point to web_center"""
        
        # Calculate initial distance for rope length
        origin_pos = Vector(origin_empty.location)
        web_center_pos = Vector(web_center_empty.location)
        base_distance = (web_center_pos - origin_pos).length
        
        # Add slack to make the rope longer than the direct distance
        rope_length = base_distance * (1.0 + self.config.tether_slack)
        
        # Create curve for the rope
        curve_data = bpy.data.curves.new(name="WebTetherCurve", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = self.config.tether_width / 2
        curve_data.bevel_resolution = 4
        
        # Create the curve object
        tether_obj = bpy.data.objects.new("WebTether", curve_data)
        context.collection.objects.link(tether_obj)
        
        # Create spline with multiple points for rope sagging
        spline = curve_data.splines.new('NURBS')
        num_points = 5  # Start, 3 middle points for sag, end
        spline.points.add(num_points - 1)
        
        # Calculate initial rope shape with catenary sag in world coordinates
        for i in range(num_points):
            t = i / (num_points - 1)  # 0 to 1
            
            # Calculate positions in world space
            world_pos = origin_pos.lerp(web_center_pos, t)
            
            # Add sag - maximum at center, using catenary approximation
            sag_factor = 4 * t * (1 - t)  # Parabolic, max at t=0.5
            sag_amount = (rope_length - base_distance) * 0.5  # How much extra length creates sag
            world_pos.z -= sag_factor * sag_amount  # Sag downward
            
            # Set world coordinates directly
            spline.points[i].co = (world_pos.x, world_pos.y, world_pos.z, 1.0)
        
        spline.order_u = min(4, num_points)
        spline.use_endpoint_u = True
        
        # Don't parent the curve - instead use hook modifiers for both ends
        
        # Create hook modifier for the first point (origin)
        hook_start_modifier = tether_obj.modifiers.new("StartPointHook", 'HOOK')
        hook_start_modifier.object = origin_empty
        
        # Create hook modifier for the last point (web_center)
        hook_end_modifier = tether_obj.modifiers.new("EndPointHook", 'HOOK')
        hook_end_modifier.object = web_center_empty
        
        # Switch to edit mode to assign the hook points
        context.view_layer.objects.active = tether_obj
        bpy.ops.object.mode_set(mode='EDIT')
        
        # Deselect all points first
        bpy.ops.curve.select_all(action='DESELECT')
        
        # Select and assign the first control point to start hook
        spline = tether_obj.data.splines[0]
        spline.points[0].select = True
        bpy.ops.object.hook_assign(modifier="StartPointHook")
        
        # Deselect all, then select and assign the last control point to end hook
        bpy.ops.curve.select_all(action='DESELECT')
        spline.points[-1].select = True
        bpy.ops.object.hook_assign(modifier="EndPointHook")
        
        # Return to object mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
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