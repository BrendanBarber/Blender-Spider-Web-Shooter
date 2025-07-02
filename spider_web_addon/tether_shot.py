import bpy
from typing import Tuple
from mathutils import Vector
from .config import SpiderShotConfig

class TetherShot:
    """Handles tethered spider web shots"""
    
    def __init__(self, origin: Tuple[float, float, float], target: Tuple[float, float, float], config: SpiderShotConfig):
        self.origin = origin
        self.target = target
        self.config = config
        self.tether_mesh = None

    def create_shot(self, context, origin_empty, target_empty, web_center_empty):
        """Create a tether shot"""
        return self.create_tether_mesh(context, origin_empty, web_center_empty)

    def create_tether_mesh(self, context, origin_empty, web_center_empty):
        """Creates a rope tether connecting origin to web_center"""
        
        # Create mesh data
        mesh = bpy.data.meshes.new(name="SpiderTether")
        
        # Create vertices - just two points for a simple line
        verts = [
            (0.0, 0.0, 0.0),  # Origin point (local space)
            (0.0, 0.0, 1.0)   # End point (will be positioned via constraints)
        ]
        
        # Create edge connecting the two vertices
        edges = [(0, 1)]
        
        # Create the mesh
        mesh.from_pydata(verts, edges, [])
        mesh.update()
        
        # Create mesh object
        tether_obj = bpy.data.objects.new("SpiderTether", mesh)
        context.collection.objects.link(tether_obj)
        
        # Position the tether at the origin empty's location
        tether_obj.location = origin_empty.location
        
        # Store reference to the mesh
        self.tether_mesh = tether_obj
        
        # Add constraints to make the tether stretch between the two points
        self._setup_tether_constraints(tether_obj, origin_empty, web_center_empty)
        
        # Apply tether styling
        self._apply_tether_styling(tether_obj)
        
        return tether_obj

    def _setup_tether_constraints(self, tether_obj, origin_empty, web_center_empty):
        """Set up constraints to make the tether follow the origin and stretch to web_center"""
        
        # Add a Copy Location constraint to follow the origin
        copy_loc_constraint = tether_obj.constraints.new(type='COPY_LOCATION')
        copy_loc_constraint.target = origin_empty
        copy_loc_constraint.name = "Follow_Origin"
        
        # Add a Track To constraint to point towards the web center
        track_constraint = tether_obj.constraints.new(type='TRACK_TO')
        track_constraint.target = web_center_empty
        track_constraint.track_axis = 'TRACK_Z'
        track_constraint.up_axis = 'UP_Y'
        track_constraint.name = "Point_To_Web_Center"
        
        # Calculate initial distance for scaling
        origin_pos = Vector(origin_empty.location)
        target_pos = Vector(web_center_empty.location)
        distance = (target_pos - origin_pos).length
        
        # Scale the tether to match the distance
        tether_obj.scale = (1.0, 1.0, distance)
        
        # Store references for manual updates
        tether_obj["origin_empty"] = origin_empty
        tether_obj["web_center_empty"] = web_center_empty

    def update_tether_length(self, tether_obj):
        """Manually update the tether length based on current positions"""
        if not tether_obj or "origin_empty" not in tether_obj or "web_center_empty" not in tether_obj:
            return
        
        origin_empty = tether_obj["origin_empty"]
        web_center_empty = tether_obj["web_center_empty"]
        
        if origin_empty and web_center_empty:
            origin_pos = Vector(origin_empty.location)
            target_pos = Vector(web_center_empty.location)
            distance = (target_pos - origin_pos).length
            
            # Update the Z scale to match the distance
            tether_obj.scale = (1.0, 1.0, distance)

    def _apply_tether_styling(self, tether_obj):
        """Apply visual styling to the tether"""
        
        # Create or get tether material
        mat_name = "SpiderTether_Material"
        if mat_name in bpy.data.materials:
            material = bpy.data.materials[mat_name]
        else:
            material = bpy.data.materials.new(name=mat_name)
            # Set up a basic material (you can customize this)
            material.use_nodes = True
            nodes = material.node_tree.nodes
            nodes.clear()
            
            # Add principled BSDF
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.8, 1.0)  # Light gray
            bsdf.inputs['Roughness'].default_value = 0.3
            
            # Add output node
            output = nodes.new(type='ShaderNodeOutputMaterial')
            
            # Connect nodes
            material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        # Assign material to tether
        tether_obj.data.materials.append(material)
        
        # For mesh thickness, we could use a Skin modifier or Solidify modifier
        # Adding a Skin modifier to give the edge thickness
        tether_width = self.config.tether_width if self.config.tether_width is not None else 0.1
        
        skin_modifier = tether_obj.modifiers.new(name="Skin", type='SKIN')
        
        # Set the skin radius for both vertices
        if tether_obj.data.skin_vertices:
            for sv in tether_obj.data.skin_vertices[0].data:
                sv.radius = (tether_width / 2, tether_width / 2)

    def animate_shot(self, context, origin_empty, target_empty, start_frame=1):
        """Animate the tether shot"""
        return self.animate_tether(context, origin_empty, target_empty, start_frame)

    def animate_tether(self, context, origin_empty, target_empty, start_frame=1):
        """Animate the tether appearance and connection"""
        if not self.tether_mesh:
            print("Error: No tether mesh to animate")
            return
        
        tether_obj = self.tether_mesh
        
        # Clear existing animation data
        if tether_obj.animation_data:
            tether_obj.animation_data_clear()
        
        # Convert shoot_time from seconds to frames
        scene = context.scene
        fps = scene.render.fps / scene.render.fps_base
        duration_frames = int(self.config.shoot_time * fps)
        end_frame = start_frame + duration_frames
        
        # Start with tether invisible (scale to 0)
        tether_obj.scale = (1.0, 1.0, 0.0)
        tether_obj.keyframe_insert(data_path="scale", frame=start_frame)
        
        # Calculate final distance for scaling
        origin_pos = Vector(origin_empty.location)
        target_pos = Vector(target_empty.location)
        distance = (target_pos - origin_pos).length
        
        # Animate tether growing to full length
        tether_obj.scale = (1.0, 1.0, distance)
        tether_obj.keyframe_insert(data_path="scale", frame=end_frame)
        
        # Set up interpolation for smooth growth
        if tether_obj.animation_data and tether_obj.animation_data.action:
            for fcurve in tether_obj.animation_data.action.fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = 'LINEAR'
        
        # Animate tether slack effect (optional)
        if self.config.tether_slack and self.config.tether_slack > 0:
            self._animate_tether_slack(tether_obj, start_frame, end_frame, fps)

    def _animate_tether_slack(self, tether_obj, start_frame, end_frame, fps):
        """Add slack animation to the tether for more realistic movement"""
        # This could involve adding a wave modifier or animating vertex positions
        # For now, we'll add a simple oscillation to the tether's rotation
        
        # Add slight rotation oscillation to simulate slack
        slack_duration_seconds = 0.4  # Duration of slack effect in seconds
        slack_frames = int(slack_duration_seconds * fps)
        slack_end_frame = end_frame + slack_frames
        
        # Initial rotation (straight)
        tether_obj.rotation_euler = (0, 0, 0)
        tether_obj.keyframe_insert(data_path="rotation_euler", frame=end_frame)
        
        # Add slight bend for slack
        slack_amount = self.config.tether_slack * 0.5  # Convert to radians
        tether_obj.rotation_euler = (slack_amount, 0, 0)
        tether_obj.keyframe_insert(data_path="rotation_euler", frame=end_frame + slack_frames // 2)
        
        # Return to straight
        tether_obj.rotation_euler = (0, 0, 0)
        tether_obj.keyframe_insert(data_path="rotation_euler", frame=slack_end_frame)