import bpy
from dataclasses import dataclass, field
from typing import Tuple, Optional

@dataclass
class SpiderShotConfig:
    shoot_time: float = 1.0
    is_target_parent: float = False
    is_tethered: bool = True
    
    # Tether specific properties
    tether_width: Optional[float] = 0.02
    tether_slack: Optional[float] = 0.05
    
    # Projectile specific properties (can still be used optionally with tether)
    projectile_size: Optional[float] = 0.1
    projectile_trail_length: Optional[float] = 0.5
    
    def __post_init__(self):
        """Set optional properties based on shot type"""
        if self.is_tethered:
            if self.tether_width is None:
                self.tether_width = 0.02
            if self.tether_slack is None:
                self.tether_slack = 0.05
        else:
            if self.projectile_size is None:
                self.projectile_size = 0.02
            if self.projectile_trail_length is None:
                self.projectile_trail_length = 0.5

@dataclass
class SpiderSpreadConfig:
    radius: float = 1.0
    height: float = 0.25
    spread_time: float = 1.0
    density_spoke: int = 5
    density_rib: int = 3
    web_thickness: float = 0.01
    curvature: float = 0.1
    random_spread_edge: float = 0.1
    random_spread_interior: float = 0.05

@dataclass
class SpiderWebConfig:
    spider_shot_config: SpiderShotConfig = field(default_factory=SpiderShotConfig)
    spider_spread_config: SpiderSpreadConfig = field(default_factory=SpiderSpreadConfig)
    animate_web: bool = True
    start_frame: int = 1