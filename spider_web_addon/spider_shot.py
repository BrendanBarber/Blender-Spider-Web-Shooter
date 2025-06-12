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