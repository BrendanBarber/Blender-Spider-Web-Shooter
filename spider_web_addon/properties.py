import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty
from bpy.types import PropertyGroup
from mathutils import Vector

from .config import SpiderWebConfig, SpiderShotConfig, SpiderSpreadConfig

class SpiderShotProperties(PropertyGroup):
    shoot_time: FloatProperty(
        name="Shoot Time",
        description="Time for web to shoot out and reach target (in seconds)",
        default=SpiderShotConfig().shoot_time,
        min=0.1,
        max=10.0
    )

    is_target_parent: BoolProperty(
        name="Target Is Parent",
        description="Whether the parent node of the web is the target or the origin",
        default=SpiderShotConfig().is_target_parent
    )
    
    is_tethered: BoolProperty(
        name="Is Tethered",
        description="Whether the web shot is tethered or projectile",
        default=SpiderShotConfig().is_tethered
    )
    
    # Tether properties
    tether_width: FloatProperty(
        name="Tether Width",
        description="Width of the tether strand",
        default=SpiderShotConfig().tether_width or 0.1,
        min=0.001,
    )
    
    tether_slack: FloatProperty(
        name="Tether Slack",
        description="Amount of slack in the tether",
        default=SpiderShotConfig().tether_slack or 0.05,
        min=0.0,
    )
    
    # Projectile properties
    projectile_size: FloatProperty(
        name="Projectile Size",
        description="Size of the projectile web ball",
        default=SpiderShotConfig().projectile_size or 0.5,
        min=0.001,
    )
    
    projectile_trail_length: FloatProperty(
        name="Trail Length",
        description="Length of the projectile trail",
        default=SpiderShotConfig().projectile_trail_length or 1.0,
        min=0.0,
    )

class SpiderSpreadProperties(PropertyGroup):
    radius: FloatProperty(
        name="Radius",
        description="Radius of the web spread",
        default=SpiderSpreadConfig().radius,
        min=0.01,
    )
    
    height: FloatProperty(
        name="Height",
        description="Height variation of the web",
        default=SpiderSpreadConfig().height,
        min=0.0,
    )
    
    spread_time: FloatProperty(
        name="Spread Time",
        description="Time for web to spread out (in seconds)",
        default=SpiderSpreadConfig().spread_time,
        min=0.1,
        max=10.0
    )
    
    density_spoke: IntProperty(
        name="Spoke Density",
        description="Number of radial spokes",
        default=SpiderSpreadConfig().density_spoke,
        min=3,
        max=64
    )
    
    density_rib: IntProperty(
        name="Rib Density",
        description="Number of concentric ribs",
        default=SpiderSpreadConfig().density_rib,
        min=1,
        max=32
    )

    web_thickness: FloatProperty(
        name="Web Thickness",
        description="Thickness of web strands",
        default=SpiderSpreadConfig().web_thickness,
        min=0.01,
    )
    
    curvature: FloatProperty(
        name="Curvature",
        description="Curvature of web strands",
        default=SpiderSpreadConfig().curvature,
        min=0.0,
        max=4.0
    )
    
    random_spread_edge: FloatProperty(
        name="Edge Randomness",
        description="Random variation at web edges",
        default=SpiderSpreadConfig().random_spread_edge,
        min=0.0,
        max=1.0
    )
    
    random_spread_interior: FloatProperty(
        name="Interior Randomness",
        description="Random variation in web interior",
        default=SpiderSpreadConfig().random_spread_interior,
        min=0.0,
        max=1.0
    )

class SpiderWebProperties(PropertyGroup):
    shot_props: bpy.props.PointerProperty(type=SpiderShotProperties)
    spread_props: bpy.props.PointerProperty(type=SpiderSpreadProperties)
    
    # Animation settings
    animate_web: BoolProperty(
        name="Animate Web",
        description="Create keyframes for web animation",
        default=True
    )
    
    start_frame: IntProperty(
        name="Start Frame",
        description="Frame to start the web animation",
        default=1,
        min=1
    )
    
    # Coordinate properties
    origin_x: FloatProperty(
        name="Origin X",
        description="X coordinate of web origin",
        default=0.0,
        precision=3
    )
    origin_y: FloatProperty(
        name="Origin Y", 
        description="Y coordinate of web origin",
        default=0.0,
        precision=3
    )
    origin_z: FloatProperty(
        name="Origin Z",
        description="Z coordinate of web origin", 
        default=0.0,
        precision=3
    )
    
    target_x: FloatProperty(
        name="Target X",
        description="X coordinate of web target",
        default=2.0,
        precision=3
    )
    target_y: FloatProperty(
        name="Target Y",
        description="Y coordinate of web target",
        default=0.0,
        precision=3
    )
    target_z: FloatProperty(
        name="Target Z",
        description="Z coordinate of web target",
        default=0.0,
        precision=3
    )

    @property
    def origin_vector(self):
        """Get origin as Vector"""
        return Vector((self.origin_x, self.origin_y, self.origin_z))
    
    @property 
    def target_vector(self):
        """Get target as Vector"""
        return Vector((self.target_x, self.target_y, self.target_z))
    
    def set_origin(self, location):
        """Set origin from Vector or tuple"""
        self.origin_x = location[0]
        self.origin_y = location[1] 
        self.origin_z = location[2]
    
    def set_target(self, location):
        """Set target from Vector or tuple"""
        self.target_x = location[0]
        self.target_y = location[1]
        self.target_z = location[2]

    def to_config(self):
        """Convert Blender properties back to config dataclass"""
        shot_config = SpiderShotConfig(
            shoot_time=self.shot_props.shoot_time,
            is_target_parent=self.shot_props.is_target_parent,
            is_tethered=self.shot_props.is_tethered,
            tether_width=self.shot_props.tether_width if self.shot_props.is_tethered else None,
            tether_slack=self.shot_props.tether_slack if self.shot_props.is_tethered else None,
            projectile_size=self.shot_props.projectile_size if not self.shot_props.is_tethered else None,
            projectile_trail_length=self.shot_props.projectile_trail_length if not self.shot_props.is_tethered else None,
        )
        
        spread_config = SpiderSpreadConfig(
            radius=self.spread_props.radius,
            height=self.spread_props.height,
            spread_time=self.spread_props.spread_time,
            density_spoke=self.spread_props.density_spoke,
            density_rib=self.spread_props.density_rib,
            web_thickness=self.spread_props.web_thickness,
            curvature=self.spread_props.curvature,
            random_spread_edge=self.spread_props.random_spread_edge,
            random_spread_interior=self.spread_props.random_spread_interior,
        )
        
        return SpiderWebConfig(
            spider_shot_config=shot_config,
            spider_spread_config=spread_config,
            animate_web=self.animate_web,
            start_frame=self.start_frame
        )
    
    def from_config(self, config: SpiderWebConfig):
        """Load config dataclass into Blender properties"""
        # Shot properties
        self.shot_props.shoot_time = config.spider_shot_config.shoot_time
        self.shot_props.is_target_parent = config.spider_shot_config.is_target_parent
        self.shot_props.is_tethered = config.spider_shot_config.is_tethered
        
        if config.spider_shot_config.tether_width is not None:
            self.shot_props.tether_width = config.spider_shot_config.tether_width
        if config.spider_shot_config.tether_slack is not None:
            self.shot_props.tether_slack = config.spider_shot_config.tether_slack
        if config.spider_shot_config.projectile_size is not None:
            self.shot_props.projectile_size = config.spider_shot_config.projectile_size
        if config.spider_shot_config.projectile_trail_length is not None:
            self.shot_props.projectile_trail_length = config.spider_shot_config.projectile_trail_length
        
        # Spread properties
        self.spread_props.radius = config.spider_spread_config.radius
        self.spread_props.height = config.spider_spread_config.height
        self.spread_props.spread_time = config.spider_spread_config.spread_time
        self.spread_props.density_spoke = config.spider_spread_config.density_spoke
        self.spread_props.density_rib = config.spider_spread_config.density_rib
        self.spread_props.web_thickness = config.spider_spread_config.web_thickness
        self.spread_props.curvature = config.spider_spread_config.curvature
        self.spread_props.random_spread_edge = config.spider_spread_config.random_spread_edge
        self.spread_props.random_spread_interior = config.spider_spread_config.random_spread_interior