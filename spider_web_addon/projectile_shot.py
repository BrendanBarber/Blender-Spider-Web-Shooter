import bpy
from typing import Tuple
from mathutils import Vector
from .config import SpiderShotConfig

class ProjectileShot:
    """Handles projectile spider web shots"""
    
    def __init__(self, origin: Tuple[float, float, float], target: Tuple[float, float, float], config: SpiderShotConfig):
        self.origin = origin
        self.target = target
        self.config = config
        self.shot_mesh = None
        self.trail_mesh = None

    def create_shot(self, context, origin_empty, target_empty, web_center_empty=None):
        """Create a projectile shot"""
        return self.create_shot_mesh(context, origin_empty, target_empty)

    def create_shot_mesh(self, context, origin_empty, target_empty):
        """Create the projectile mesh for non-tethered shots"""
        
        # Create projectile sphere
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=self.config.projectile_size,
            location=origin_empty.location
        )
        
        projectile_obj = context.active_object
        projectile_obj.name = "SpiderProjectile"
        
        # Store reference
        self.shot_mesh = projectile_obj
        
        # Apply projectile material
        self._apply_projectile_material(projectile_obj)
        
        # Create trail if specified
        if self.config.projectile_trail_length > 0:
            self._create_projectile_trail(context, origin_empty, target_empty)
        
        return projectile_obj

    def _apply_projectile_material(self, projectile_obj):
        """Apply material to the projectile"""
        mat_name = "SpiderProjectile_Material"
        
        if mat_name in bpy.data.materials:
            material = bpy.data.materials[mat_name]
        else:
            material = bpy.data.materials.new(name=mat_name)
            material.use_nodes = True
            nodes = material.node_tree.nodes
            nodes.clear()
            
            # Create emission shader for glowing effect
            emission = nodes.new(type='ShaderNodeEmission')
            emission.inputs['Color'].default_value = (0.9, 0.9, 1.0, 1.0)  # Slightly blue-white
            emission.inputs['Strength'].default_value = 2.0
            
            # Add some transparency
            transparent = nodes.new(type='ShaderNodeBsdfTransparent')
            mix = nodes.new(type='ShaderNodeMixShader')
            mix.inputs['Fac'].default_value = 0.3  # 30% transparent
            
            output = nodes.new(type='ShaderNodeOutputMaterial')
            
            # Connect nodes
            material.node_tree.links.new(transparent.outputs['BSDF'], mix.inputs[1])
            material.node_tree.links.new(emission.outputs['Emission'], mix.inputs[2])
            material.node_tree.links.new(mix.outputs['Shader'], output.inputs['Surface'])
        
        # Assign material
        projectile_obj.data.materials.append(material)

    def _create_projectile_trail(self, context, origin_empty, target_empty):
        """Create a trail effect for the projectile"""
        
        # Create a cylinder for the trail
        bpy.ops.mesh.primitive_cylinder_add(
            radius=self.config.projectile_size * 0.3,
            depth=self.config.projectile_trail_length,
            location=origin_empty.location
        )
        
        trail_obj = context.active_object
        trail_obj.name = "SpiderProjectileTrail"
        
        # Store reference
        self.trail_mesh = trail_obj
        
        # Apply trail material
        self._apply_trail_material(trail_obj)
        
        return trail_obj

    def _apply_trail_material(self, trail_obj):
        """Apply material to the projectile trail"""
        mat_name = "SpiderTrail_Material"
        
        if mat_name in bpy.data.materials:
            material = bpy.data.materials[mat_name]
        else:
            material = bpy.data.materials.new(name=mat_name)
            material.use_nodes = True
            material.blend_method = 'BLEND'  # Enable transparency
            
            nodes = material.node_tree.nodes
            nodes.clear()
            
            # Create emission shader with gradient
            emission = nodes.new(type='ShaderNodeEmission')
            emission.inputs['Color'].default_value = (0.7, 0.7, 1.0, 1.0)  # Light blue
            emission.inputs['Strength'].default_value = 1.0
            
            # Add transparency with gradient
            transparent = nodes.new(type='ShaderNodeBsdfTransparent')
            
            # Color ramp for gradient effect
            color_ramp = nodes.new(type='ShaderNodeValToRGB')
            color_ramp.color_ramp.elements[0].color = (1, 1, 1, 0)  # Transparent
            color_ramp.color_ramp.elements[1].color = (1, 1, 1, 1)  # Opaque
            
            # Texture coordinate for gradient
            tex_coord = nodes.new(type='ShaderNodeTexCoord')
            
            mix = nodes.new(type='ShaderNodeMixShader')
            output = nodes.new(type='ShaderNodeOutputMaterial')
            
            # Connect nodes for gradient transparency
            material.node_tree.links.new(tex_coord.outputs['Generated'], color_ramp.inputs['Fac'])
            material.node_tree.links.new(color_ramp.outputs['Alpha'], mix.inputs['Fac'])
            material.node_tree.links.new(transparent.outputs['BSDF'], mix.inputs[1])
            material.node_tree.links.new(emission.outputs['Emission'], mix.inputs[2])
            material.node_tree.links.new(mix.outputs['Shader'], output.inputs['Surface'])
        
        # Assign material
        trail_obj.data.materials.append(material)

    def animate_shot(self, context, origin_empty, target_empty, start_frame=1):
        """Animate the projectile shot from origin to target"""
        if not self.shot_mesh:
            # Create the projectile mesh first if it doesn't exist
            self.create_shot_mesh(context, origin_empty, target_empty)
        
        if not self.shot_mesh:
            print("Error: No shot mesh to animate")
            return
        
        # Get the projectile object
        projectile_obj = self.shot_mesh
        
        # Clear existing animation data
        if projectile_obj.animation_data:
            projectile_obj.animation_data_clear()
        
        # Convert shoot_time from seconds to frames
        scene = context.scene
        fps = scene.render.fps / scene.render.fps_base
        duration_frames = int(self.config.shoot_time * fps)
        end_frame = start_frame + duration_frames
        
        # Set up initial position at origin
        projectile_obj.location = origin_empty.location
        
        # Set keyframes for position animation
        projectile_obj.keyframe_insert(data_path="location", frame=start_frame)
        
        # Set final position at target
        projectile_obj.location = target_empty.location
        projectile_obj.keyframe_insert(data_path="location", frame=end_frame)
        
        # Set up interpolation for smooth movement
        if projectile_obj.animation_data and projectile_obj.animation_data.action:
            for fcurve in projectile_obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'LINEAR'  # or 'BEZIER' for more natural movement
         
        # Animate trail if enabled
        if hasattr(self, 'trail_mesh') and self.trail_mesh:
            self._animate_projectile_trail(context, origin_empty, target_empty, start_frame, end_frame, fps)

    def _animate_projectile_trail(self, context, origin_empty, target_empty, start_frame, end_frame, fps):
        """Animate the projectile trail effect"""
        if not hasattr(self, 'trail_mesh') or not self.trail_mesh:
            return
        
        trail_obj = self.trail_mesh
        
        # Clear existing animation
        if trail_obj.animation_data:
            trail_obj.animation_data_clear()
        
        # Calculate trail positions
        origin_pos = Vector(origin_empty.location)
        target_pos = Vector(target_empty.location)
        direction = (target_pos - origin_pos).normalized()
        
        # Trail starts invisible
        trail_obj.scale = (0.0, 0.0, 0.0)
        trail_obj.keyframe_insert(data_path="scale", frame=start_frame)
        
        # Trail grows as projectile moves
        for i in range(5):  # 5 intermediate positions
            frame = start_frame + int((end_frame - start_frame) * (i + 1) / 6)
            progress = (i + 1) / 6
            
            # Position trail behind the projectile
            trail_length = self.config.projectile_trail_length * progress
            trail_position = origin_pos + direction * (target_pos - origin_pos).length * progress
            trail_obj.location = trail_position - direction * trail_length * 0.5
            
            # Scale trail based on progress
            scale_factor = min(1.0, progress * 2)  # Grows quickly then stabilizes
            trail_obj.scale = (scale_factor, scale_factor, trail_length)
            
            trail_obj.keyframe_insert(data_path="location", frame=frame)
            trail_obj.keyframe_insert(data_path="scale", frame=frame)
        
        # Trail fades after impact (0.4 seconds after impact)
        fade_duration = 0.4  # seconds
        fade_frame = end_frame + int(fade_duration * fps)
        trail_obj.scale = (0.0, 0.0, 0.0)
        trail_obj.keyframe_insert(data_path="scale", frame=fade_frame)