import bpy
import math
from dataclasses import dataclass, field
from typing import Tuple, Optional
from mathutils import Vector, Matrix
from .utils import *
from .config import *

class SpiderSpread:    
    """The the web spread at the target"""
    def __init__(self, origin: Tuple[float, float, float], target: Tuple[float, float, float], config: SpiderSpreadConfig = None):
        self.origin = origin
        self.target = target
        self.config = config or SpiderSpreadConfig()

    def create_spread(self, origin_empty, target_empty):
        """Creates the control points for the web spread"""
        # Calculate actual web center offset
        web_center_vec = get_point_offset_from_end(self.origin, self.target, self.config.height)
        
        # Create web center point
        center_empty = create_control_point(web_center_vec, "WebCenter", target_empty)
        
        # Radially create the points
        radius = self.config.radius
        density_spoke = self.config.density_spoke
        density_rib = self.config.density_rib
        
        # Get the direction of the web
        web_direction = (Vector(self.target) - Vector(self.origin)).normalized()
        
        # Rotation matrix for aligning the web in the correct direction
        rotation_matrix = web_direction.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        
        # Calculate step angle for the spoke density
        spoke_step = (2 * math.pi) / density_spoke
        rib_step = radius / density_rib
        
        for i in range(density_spoke):
            # Create spoke point
            angle = spoke_step * i
            
            offset = Vector((
                radius * math.cos(angle),
                radius * math.sin(angle),
                0
            ))
            
            world_offset = rotation_matrix @ offset
            spoke_position = web_center_vec + world_offset
            
            spoke_empty = create_control_point(spoke_position, f"WebSpoke_{i}", center_empty)
            
            # Create rib points along spoke
            for j in range(1, density_rib+1):
                step = rib_step * j
                
                offset = Vector((
                    step * math.cos(angle),
                    step * math.sin(angle),
                    0
                ))
                
                world_offset = rotation_matrix @ offset
                rib_position = web_center_vec + world_offset
                
                create_control_point(rib_position, f"WebRib_{i}-{j}", spoke_empty)
    
    def store_config_on_empty(self, empty):
        """Store the spread configuration as custom properties on the empty"""
        # Use Blender's proper custom property system with UI metadata
        empty["spider_spread_radius"] = self.config.radius
        empty.id_properties_ui("spider_spread_radius").update(
            description="Radius of the web spread",
            default=1.0,
            min=0.01
        )
        
        empty["spider_spread_height"] = self.config.height
        empty.id_properties_ui("spider_spread_height").update(
            description="Height variation of the web",
            default=0.25,
            min=0.0
        )
        
        empty["spider_spread_spread_time"] = self.config.spread_time
        empty.id_properties_ui("spider_spread_spread_time").update(
            description="Time for web to spread out (in frames)",
            default=1.0,
            min=0.0
        )
        
        empty["spider_spread_density_spoke"] = self.config.density_spoke
        empty.id_properties_ui("spider_spread_density_spoke").update(
            description="Number of radial spokes",
            default=5,
            min=3,
            max=64
        )
        
        empty["spider_spread_density_rib"] = self.config.density_rib
        empty.id_properties_ui("spider_spread_density_rib").update(
            description="Number of concentric ribs",
            default=3,
            min=1,
            max=32
        )
        
        empty["spider_spread_curvature"] = self.config.curvature
        empty.id_properties_ui("spider_spread_curvature").update(
            description="Curvature of web strands",
            default=0.1,
            min=0.0,
            max=2.0
        )
        
        empty["spider_spread_random_spread_edge"] = self.config.random_spread_edge
        empty.id_properties_ui("spider_spread_random_spread_edge").update(
            description="Random variation at web edges",
            default=0.1,
            min=0.0,
            max=1.0
        )
        
        empty["spider_spread_random_spread_interior"] = self.config.random_spread_interior
        empty.id_properties_ui("spider_spread_random_spread_interior").update(
            description="Random variation in web interior",
            default=0.05,
            min=0.0,
            max=1.0
        )
    
    @staticmethod
    def load_config_from_empty(empty):
        """Load the spread configuration from custom properties on the empty"""
        config = SpiderSpreadConfig()
        
        if "spider_spread_radius" in empty:
            config.radius = empty["spider_spread_radius"]
        if "spider_spread_height" in empty:
            config.height = empty["spider_spread_height"]
        if "spider_spread_spread_time" in empty:
            config.spread_time = empty["spider_spread_spread_time"]
        if "spider_spread_density_spoke" in empty:
            config.density_spoke = empty["spider_spread_density_spoke"]
        if "spider_spread_density_rib" in empty:
            config.density_rib = empty["spider_spread_density_rib"]
        if "spider_spread_curvature" in empty:
            config.curvature = empty["spider_spread_curvature"]
        if "spider_spread_random_spread_edge" in empty:
            config.random_spread_edge = empty["spider_spread_random_spread_edge"]
        if "spider_spread_random_spread_interior" in empty:
            config.random_spread_interior = empty["spider_spread_random_spread_interior"]
        
        return config