import bpy
import math
from dataclasses import dataclass, field
from typing import Tuple, Optional
from mathutils import Vector, Matrix
from .utils import *
from .config import *
from .spider_shot import *
from .spider_spread import *

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

    def create_web(self):
        # Create origin reference point
        origin_empty = create_control_point(self.origin, "WebOrigin")
        
        # Store both shot and spread configurations on the origin empty
        self.spider_shot.store_config_on_empty(origin_empty)
        self.spider_spread.store_config_on_empty(origin_empty)
        
        # Create target reference point
        target_empty = create_control_point(self.target, "WebTarget", origin_empty)

        # Create spread points
        self.spider_spread.create_spread(origin_empty, target_empty)