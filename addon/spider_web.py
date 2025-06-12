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

class SpiderSpread:    
    """The the web spread at the target"""
    def __init__(self, origin: Tuple[float, float, float], target: Tuple[float, float, float], config: SpiderSpreadConfig = None):
        self.origin = origin
        self.target = target
        self.config = config or SpiderSpreadConfig()

    def create_spread(self, origin_empty, target_empty):
        """Creates the control points for the web spread"""
        # Calculate actual web center offset
        web_center_vec = get_point_offset_from_end(self.origin, self.target, self.config.spider_spread_config.height)
        
        # Create web center point
        center_empty = create_control_point(web_center_vec, "WebCenter", target_empty)
        
        # Radially create the points
        radius = self.config.spider_spread_config.radius
        density_spoke = self.config.spider_spread_config.density_spoke
        density_rib = self.config.spider_spread_config.density_rib
        
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

class SpiderWeb:
    """A generated spider web and shot animated"""
    def __init__(self, origin: Tuple[float, float, float], target: Tuple[float, float, float], config: SpiderWebConfig = SpiderWebConfig()):
        self.origin = origin
        self.target = target
        self.config = config or SpiderWebConfig()
        
        # Shot and Spread data and behaviors 
        self.spider_shot = SpiderShot(origin, target, config.spider_shot_config)
        self.spider_spread = SpiderSpread(origin, target, config.spider_spread_config)
        
        # Blender Object
        self.web_object = None

    def create_web():
        # Create origin reference point
        origin_empty = create_control_point(self.origin, "WebOrigin")
        # Create target reference point
        target_empty = create_control_point(self.target, "WebTarget", origin_empty)

        # Create spread points
        spider_spread.create_spread(origin_empty, target_empty)

        