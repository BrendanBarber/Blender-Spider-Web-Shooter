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
        
        # Create origin reference point as child of SpiderWeb
        origin_empty = create_control_point(self.origin, "WebOrigin", spider_web_empty)
        
        # Create target reference point as child of SpiderWeb
        target_empty = create_control_point(self.target, "WebTarget", spider_web_empty)

        # Create spread points
        self.spider_spread.create_spread(origin_empty, target_empty)
        self.spider_spread.create_mesh(context, origin_empty, target_empty)

        # Create projectile or tether first
        self.spider_shot.create_shot(context, origin_empty, target_empty, self.spider_spread.web_center)

        # Animate Shot
        if self.config.animate_web:
            self.spider_shot.animate_shot(context, origin_empty, target_empty, start_frame=self.config.start_frame)

        # Animate Web Spread (starting after shot completes)
        if self.config.animate_web:
            # Calculate when the spread should start (after shot completes)
            shot_travel_time = self.config.spider_shot_config.shoot_time  # in seconds
            spread_start_frame = self.config.start_frame + int(shot_travel_time * (context.scene.render.fps / context.scene.render.fps_base))
            
            self.spider_spread.animate_spread(context, origin_empty, target_empty, spread_start_frame, self.config.spider_spread_config.spread_time)

        # Store all configurations on the spider web empty
        self.spider_shot.store_config_on_empty(spider_web_empty)
        self.spider_spread.store_config_on_empty(spider_web_empty)
        self.store_config_on_empty(spider_web_empty)  # Store web-level config

    def store_config_on_empty(self, empty):
        """Store the web-level configuration as custom properties on the empty"""
        # Store web-level animation settings
        empty["spider_web_animate_web"] = self.config.animate_web
        empty.id_properties_ui("spider_web_animate_web").update(
            description="Whether to animate the web creation",
            default=True
        )
        
        empty["spider_web_start_frame"] = self.config.start_frame
        empty.id_properties_ui("spider_web_start_frame").update(
            description="Frame to start the web animation",
            default=1,
            min=1
        )