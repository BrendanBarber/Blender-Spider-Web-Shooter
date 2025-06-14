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

    def create_web(self, context):
        # Create main SpiderWeb empty at origin location
        spider_web_empty = create_control_point(self.origin, "SpiderWeb")
        spider_web_empty.empty_display_type = 'PLAIN_AXES'
        spider_web_empty.hide_select = True
        
        # Store both shot and spread configurations on the spider web empty
        self.spider_shot.store_config_on_empty(spider_web_empty)
        self.spider_spread.store_config_on_empty(spider_web_empty)
        
        # Create origin reference point as child of SpiderWeb
        origin_empty = create_control_point(self.origin, "WebOrigin", spider_web_empty)
        
        # Create target reference point as child of SpiderWeb
        target_empty = create_control_point(self.target, "WebTarget", spider_web_empty)

        # Create spread points
        self.spider_spread.create_spread(origin_empty, target_empty)
        self.spider_spread.create_mesh(context, origin_empty, target_empty)