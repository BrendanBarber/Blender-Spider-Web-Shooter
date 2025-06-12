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

@dataclass
class SpiderShotConfig:
    shoot_time: float = 1.0
    is_tethered: bool = True
    
    # Tether specific properties
    tether_width: Optional[float] = 0.1
    tether_slack: Optional[float] = 0.05
    
    # Projectile specific properties (can still be used optionally with tether)
    projectile_size: Optional[float] = 0.5
    projectile_trail_length: Optional[float] = 1.0
    
    def __post_init__(self):
        """Set optional properties based on shot type"""
        if self.is_tethered:
            if self.tether_width is None:
                self.tether_width = 0.1
            if self.tether_slack is None:
                self.tether_slack = 0.05
        else:
            if self.projectile_size is None:
                self.projectile_size = 0.5
            if self.projectile_trail_length is None:
                self.projectile_trail_length = 1.0
        
class SpiderShot:
    """The web shot"""
    def __init__(self, origin: Tuple[float, float, float], target: Tuple[float, float, float], config: SpiderShotConfig = None):
        self.origin = origin
        self.target = target
        self.config = config or SpiderShotConfig()

@dataclass
class SpiderSpreadConfig:
    radius: float = 1.0
    height: float = 0.25
    spread_time: float = 1.0
    density_spoke: int = 5
    density_rib: int = 3
    curvature: float = 0.1
    random_spread_edge: float = 0.1
    random_spread_interior: float = 0.05

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

@dataclass
class SpiderWebConfig:
    spider_shot_config: SpiderShotConfig = field(default_factory=SpiderShotConfig)
    spider_spread_config: SpiderSpreadConfig = field(default_factory=SpiderSpreadConfig)

class SpiderWeb:
    """A generated spider web and shot animated"""
    def __init__(self, origin: Tuple[float, float, float], target: Tuple[float, float, float], config: SpiderWebConfig = None):
        self.origin = origin
        self.target = target
        self.config = config or SpiderWebConfig()
        
        # Shot and Spread data and behaviors 
        self.spider_shot = SpiderShot(origin, target, config.spider_shot_config if config else None)
        self.spider_spread = SpiderSpread(origin, target, config.spider_spread_config if config else None)
        
        # Blender Object
        self.web_object = None

    def create_web(self):  # Added 'self' parameter
        # Create origin reference point
        origin_empty = create_control_point(self.origin, "WebOrigin")
        # Create target reference point
        target_empty = create_control_point(self.target, "WebTarget", origin_empty)

        # Create spread points
        self.spider_spread.create_spread(origin_empty, target_empty)  # Added 'self.'

# Usage
web = SpiderWeb((0, 0, 0), (5, 3, 5))
web.create_web()