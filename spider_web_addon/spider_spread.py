import bpy
import bmesh
import math
import random
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, List
from mathutils import Vector, Matrix
import threading
from concurrent.futures import ThreadPoolExecutor
import time
from .utils import *
from .config import *
from .node_graphs import *

class SpiderSpread:    
    """The the web spread at the target"""
    def __init__(self, origin: Tuple[float, float, float], target: Tuple[float, float, float], config: SpiderSpreadConfig = None):
        self.origin = origin
        self.target = target
        self.config = config or SpiderSpreadConfig()

        # Control Empties
        self.web_center = None
        self.web_spokes_ribs: Dict[bpy.types.Object, List[bpy.types.Object]] = {}

        # Mesh Objs
        self.mesh_objs = []
        
        # Store random values for consistency
        self.edge_random_offsets = {}  # spoke_index -> (x_offset, y_offset)
        self.interior_random_offsets = {}  # (spoke_index, rib_index) -> offset_amount

    def generate_random_values(self):
        """Pre-generate all random values for consistent results - only if not already loaded"""
        # Only generate if we don't already have random values loaded
        if not self.edge_random_offsets and not self.interior_random_offsets:
            # Generate edge randomness for each spoke
            for i in range(self.config.density_spoke):
                # Random offset in local X,Y plane (0 to edge_randomness)
                x_offset = random.uniform(0, self.config.random_spread_edge)
                y_offset = random.uniform(0, self.config.random_spread_edge)
                # Apply random sign
                x_offset *= random.choice([-1, 1])
                y_offset *= random.choice([-1, 1])
                self.edge_random_offsets[i] = (x_offset, y_offset)
            
            # Generate interior randomness for each rib
            for i in range(self.config.density_spoke):
                for j in range(self.config.density_rib):
                    # Random offset along spoke axis (0 to interior_randomness)
                    offset = random.uniform(0, self.config.random_spread_interior)
                    # Apply random sign (can move toward or away from center)
                    offset *= random.choice([-1, 1])
                    self.interior_random_offsets[(i, j)] = offset

    def calculate_curved_position(self, start_pos, end_pos, reference_pos, t, curve_amount):
        """
        Calculate the curved position along a line using the same formula as the node graph
        
        Args:
            start_pos: Starting position (Vector)
            end_pos: Ending position (Vector)
            reference_pos: Reference position for curve direction (Vector)
            t: Parameter from 0.0 to 1.0 along the curve
            curve_amount: Amount of curvature
        
        Returns:
            Vector: The curved position at parameter t
        """
        # Linear interpolation between start and end
        linear_pos = start_pos.lerp(end_pos, t)
        
        # Calculate midpoint between start and end
        midpoint = (start_pos + end_pos) * 0.5
        
        # Calculate direction from midpoint to reference point
        direction = (reference_pos - midpoint).normalized()
        
        # Parabolic curve formula: t^2 - t, scaled by 4, gives peak at t=0.5
        curve_factor = ((t * t - t) * 4.0 * curve_amount) * 0.5
        
        # Apply curve offset
        curved_pos = linear_pos - (direction * curve_factor)
        
        return curved_pos

    def create_spread(self, origin_empty, target_empty):
        """Creates the control points for the web spread"""
        # Generate random values if not already loaded (preserves existing values)
        self.generate_random_values()
        
        # Calculate actual web center offset
        web_center_vec = get_point_offset_from_end(self.origin, self.target, self.config.height)
        
        # Create web center point
        self.web_center = create_control_point(web_center_vec, "WebCenter", target_empty)
        
        # Radially create the points
        radius = self.config.radius
        height = self.config.height
        density_spoke = self.config.density_spoke
        density_rib = self.config.density_rib
        
        # Get the direction of the web
        web_direction = (Vector(self.target) - Vector(self.origin)).normalized()
        
        # Rotation matrix for aligning the web in the correct direction
        rotation_matrix = web_direction.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        
        # Calculate step angle for the spoke density
        spoke_step = (2 * math.pi) / density_spoke
        rib_step = radius / density_rib
        
        # Convert positions to vectors for curve calculation
        origin_vec = Vector(self.origin)
        web_center_vector = Vector(web_center_vec)
        
        for i in range(density_spoke):
            # Create spoke point
            angle = spoke_step * i

            offset = Vector((
                radius * math.cos(angle),
                radius * math.sin(angle),
                height
            ))
            
            # Apply edge randomness to the spoke endpoint
            if i in self.edge_random_offsets:
                x_rand, y_rand = self.edge_random_offsets[i]
                # Apply randomness in local coordinate system
                random_offset = Vector((x_rand, y_rand, 0))
                offset += random_offset

            world_offset = rotation_matrix @ offset
            spoke_position = web_center_vec + world_offset

            spoke_empty = create_control_point(spoke_position, f"WebSpoke_{i}", self.web_center)

            rib_empties = []
            for j in range(1, density_rib + 1):
                # Calculate parameter t along the spoke (0.0 at center, 1.0 at spoke end)
                t = j / density_rib
                
                # Calculate the curved position along the spoke using the same formula as the node graph
                curved_position = self.calculate_curved_position(
                    web_center_vector,  # Start position (web center)
                    Vector(spoke_position),  # End position (spoke end)
                    origin_vec,  # Reference position (origin for curve direction)
                    t,  # Parameter along curve
                    self.config.curvature  # Curve amount
                )
                
                # Apply interior randomness along the spoke axis
                if (i, j-1) in self.interior_random_offsets:  # j-1 because we start from 1
                    interior_offset = self.interior_random_offsets[(i, j-1)]
                    # Calculate spoke direction (from center to spoke end)
                    spoke_direction = (Vector(spoke_position) - web_center_vector).normalized()
                    # Apply offset along spoke direction
                    curved_position += spoke_direction * interior_offset

                rib_empty = create_control_point(curved_position, f"WebRib_{i}-{j}", spoke_empty)
                rib_empties.append(rib_empty)

            # Store spoke -> ribs mapping
            self.web_spokes_ribs[spoke_empty] = rib_empties
    
    

    def create_rib_meshes(self, context, origin_empty, target_empty):
        """Create the rib curves that connect between spokes"""
        web_curve_node_tree = create_web_curve_node_tree()
        
        # Get all spokes in order
        spokes = list(self.web_spokes_ribs.keys())
        
        # For each rib level (concentric circle)
        for rib_level in range(self.config.density_rib):
            # Collect all rib empties at this level from all spokes
            rib_points_at_level = []
            
            for spoke in spokes:
                ribs = self.web_spokes_ribs[spoke]
                if rib_level < len(ribs):
                    rib_points_at_level.append(ribs[rib_level])
            
            # Create curve segments connecting adjacent rib points
            for i in range(len(rib_points_at_level)):
                next_i = (i + 1) % len(rib_points_at_level)  # Wrap around to close the circle
                
                start_rib = rib_points_at_level[i]
                end_rib = rib_points_at_level[next_i]
                
                # Create mesh object for this rib segment
                mesh = bpy.data.meshes.new(f"WebRib_Level{rib_level}_Seg{i}")
                obj = bpy.data.objects.new(f"WebRib_Level{rib_level}_Seg{i}", mesh)
                context.collection.objects.link(obj)
                self.mesh_objs.append(obj)
                
                # Parent to origin
                obj.parent = self.web_center
                obj.parent_type = 'OBJECT'
                
                # Add geometry node modifier
                modifier = obj.modifiers.new("GeometryNodes", 'NODES')
                modifier.node_group = web_curve_node_tree
                
                # Set the inputs for the modifier
                modifier["Socket_0"] = start_rib      # Start of rib segment
                modifier["Socket_1"] = end_rib        # End of rib segment  
                modifier["Socket_2"] = self.web_center # Web Origin (center point for curve calculation)
                modifier["Socket_3"] = self.config.web_thickness
                modifier["Socket_4"] = 50  # Curve resolution
                modifier["Socket_5"] = self.config.curvature * 0.5  # Less curvature for ribs
                
                obj.select_set(True)

    def create_mesh(self, context, origin_empty, target_empty):
        """Creates both spokes and ribs for spider web mesh"""
        # Create the node tree (reuse if it exists)
        web_curve_node_tree = create_web_curve_node_tree()
        
        # Create spoke curves (your existing code)
        for i, spoke in enumerate(self.web_spokes_ribs):
            # Create object
            mesh = bpy.data.meshes.new(f"WebSpoke_{i}")
            obj = bpy.data.objects.new(f"WebSpoke_{i}", mesh)
            context.collection.objects.link(obj)
            self.mesh_objs.append(obj)

            # Parent
            obj.parent = self.web_center  # Changed from origin_empty to web_center
            obj.parent_type = 'OBJECT'

            # Add geometry node modifier
            modifier = obj.modifiers.new("GeometryNodes", 'NODES')
            modifier.node_group = web_curve_node_tree

            # Set the inputs for the modifier
            modifier["Socket_0"] = self.web_center
            modifier["Socket_1"] = spoke
            modifier["Socket_2"] = origin_empty
            modifier["Socket_3"] = self.config.web_thickness
            modifier["Socket_4"] = 50 # Temp
            modifier["Socket_5"] = -1 * self.config.curvature

            obj.select_set(True)
        
        # Create rib curves (new functionality)
        self.create_rib_meshes(context, origin_empty, target_empty)

        if self.mesh_objs:
            bpy.context.view_layer.objects.active = self.mesh_objs[-1]

    def animate_spread(self, context, origin_empty, target_empty, starting_frame=1, frame_length_seconds=1):
        """Animate the web spreading from the inside out"""
        
        # Get window manager for progress system
        wm = context.window_manager
        
        # Calculate animation parameters
        fps = context.scene.render.fps / context.scene.render.fps_base
        frame_length_frames = int(frame_length_seconds * fps)
        end_frame = starting_frame + frame_length_frames
        
        # Calculate total operations for progress tracking
        spoke_meshes = [obj for obj in self.mesh_objs if "WebSpoke_" in obj.name and "WebRib_" not in obj.name]
        total_ribs = sum(len(rib_empties) for rib_empties in self.web_spokes_ribs.values())
        total_operations = 4 + len(spoke_meshes) + (total_ribs * 2)  # Base ops + booleans + rib keyframes
        
        # Start progress system
        wm.progress_begin(0, total_operations)
        current_progress = 0
        
        # Disable viewport updates for performance
        original_screen_refresh = context.preferences.system.use_region_overlap
        context.preferences.system.use_region_overlap = False
        
        # Store original viewport shading mode and switch to solid for performance
        original_shading = context.space_data.shading.type if hasattr(context, 'space_data') else 'SOLID'
        if hasattr(context, 'space_data') and hasattr(context.space_data, 'shading'):
            context.space_data.shading.type = 'SOLID'
        
        try:
            # 1. Animate web center moving up
            wm.progress_update(current_progress)
            print("Animating web center...")
            
            start_position = self.target
            end_position = get_point_offset_from_end(self.origin, self.target, self.config.height)
            
            context.scene.frame_set(starting_frame)
            self.web_center.location = start_position
            self.web_center.keyframe_insert(data_path="location", frame=starting_frame)
            
            context.scene.frame_set(end_frame)
            self.web_center.location = end_position
            self.web_center.keyframe_insert(data_path="location", frame=end_frame)
            
            current_progress += 1
            wm.progress_update(current_progress)
            
            # 2. Create optimized expanding sphere
            print("Creating animation sphere...")
            
            sphere_radius_max = self.config.radius * 1.5
            
            # Create low-poly sphere for better performance
            bpy.ops.mesh.primitive_uv_sphere_add(location=(0,0,0))
            sphere_obj = context.active_object
            sphere_obj.name = "WebSpreadSphere"
            sphere_obj.parent = self.web_center
            sphere_obj.parent_type = 'OBJECT'
            
            # Make sphere invisible
            sphere_obj.hide_viewport = True
            sphere_obj.hide_render = True
            
            # Animate sphere scale
            context.scene.frame_set(starting_frame)
            sphere_obj.scale = (0.001, 0.001, 0.001)
            sphere_obj.keyframe_insert(data_path="scale", frame=starting_frame)
            
            context.scene.frame_set(end_frame)
            sphere_obj.scale = (sphere_radius_max, sphere_radius_max, sphere_radius_max)
            sphere_obj.keyframe_insert(data_path="scale", frame=end_frame)
            
            current_progress += 1
            wm.progress_update(current_progress)
            
            # 3. Apply boolean modifiers in batches
            print(f"Applying boolean modifiers to {len(spoke_meshes)} spoke meshes...")
            
            batch_size = 3  # Process 3 objects at a time to prevent freezing
            
            for i in range(0, len(spoke_meshes), batch_size):
                batch = spoke_meshes[i:i + batch_size]
                batch_end = min(i + batch_size, len(spoke_meshes))
                
                print(f"Processing boolean batch {i//batch_size + 1}/{(len(spoke_meshes) + batch_size - 1)//batch_size}")
                
                for j, spoke_mesh in enumerate(batch):
                    # Add boolean modifier with FAST solver for performance
                    bool_modifier = spoke_mesh.modifiers.new("WebSpreadBoolean", 'BOOLEAN')
                    bool_modifier.operation = 'INTERSECT'
                    bool_modifier.object = sphere_obj
                    bool_modifier.solver = 'FAST'  # Faster than EXACT solver, switch back if it looks bad
                    
                    current_progress += 1
                    wm.progress_update(current_progress)
                    
                    # Allow UI updates every few operations
                    if (current_progress % 5) == 0:
                        bpy.context.view_layer.update()
                        # Force a minimal redraw without full viewport refresh
                        for window in bpy.context.window_manager.windows:
                            for area in window.screen.areas:
                                if area.type == 'VIEW_3D':
                                    area.tag_redraw()
            
            # Force view layer update after all booleans
            bpy.context.view_layer.update()
            
            # 4. Animate ribs in optimized batches
            print(f"Animating {total_ribs} rib objects...")
            
            rib_batch_size = 5  # Process 5 ribs at a time
            all_rib_data = []
            
            # Collect all rib animation data first
            for spoke_empty, rib_empties in self.web_spokes_ribs.items():
                for rib_empty in rib_empties:
                    final_position = rib_empty.location.copy()
                    web_center_pos = Vector(end_position)
                    direction_to_final = (Vector(final_position) - web_center_pos).normalized()
                    start_position_rib = web_center_pos + (direction_to_final * 0.01)
                    
                    all_rib_data.append({
                        'rib': rib_empty,
                        'start_pos': start_position_rib,
                        'final_pos': final_position
                    })
            
            # Process ribs in batches
            for i in range(0, len(all_rib_data), rib_batch_size):
                batch = all_rib_data[i:i + rib_batch_size]
                batch_num = i // rib_batch_size + 1
                total_batches = (len(all_rib_data) + rib_batch_size - 1) // rib_batch_size
                
                print(f"Processing rib batch {batch_num}/{total_batches}")
                
                # Set starting keyframes for this batch
                context.scene.frame_set(starting_frame)
                for rib_data in batch:
                    rib_data['rib'].location = rib_data['start_pos']
                    rib_data['rib'].keyframe_insert(data_path="location", frame=starting_frame)
                    
                    current_progress += 1
                    wm.progress_update(current_progress)
                
                # Set ending keyframes for this batch
                context.scene.frame_set(end_frame)
                for rib_data in batch:
                    rib_data['rib'].location = rib_data['final_pos']
                    rib_data['rib'].keyframe_insert(data_path="location", frame=end_frame)
                    
                    current_progress += 1
                    wm.progress_update(current_progress)
                
                # Allow UI updates between batches
                if batch_num % 3 == 0:  # Every 3 batches
                    bpy.context.view_layer.update()
                    # Tag 3D viewport areas for redraw
                    for window in bpy.context.window_manager.windows:
                        for area in window.screen.areas:
                            if area.type == 'VIEW_3D':
                                area.tag_redraw()
            
            # 5. Apply keyframe easing efficiently
            print("Applying keyframe easing...")
            
            if context.scene.animation_data and context.scene.animation_data.action:
                fcurves = context.scene.animation_data.action.fcurves
                easing_batch_size = 20
                
                for i in range(0, len(fcurves), easing_batch_size):
                    batch = fcurves[i:i + easing_batch_size]
                    
                    for fcurve in batch:
                        for keyframe in fcurve.keyframe_points:
                            keyframe.interpolation = 'BEZIER'
                            keyframe.handle_left_type = 'AUTO'
                            keyframe.handle_right_type = 'AUTO'
                    
                    # Periodic UI updates during easing
                    if i % (easing_batch_size * 5) == 0:
                        for window in bpy.context.window_manager.windows:
                            for area in window.screen.areas:
                                if area.type == 'VIEW_3D':
                                    area.tag_redraw()
            
            current_progress += 1
            wm.progress_update(current_progress)
            
            # Store reference to sphere for cleanup if needed
            self.spread_sphere = sphere_obj
            
            print("Animation setup complete!")
            
        except Exception as e:
            print(f"Error during animation: {e}")
            raise
            
        finally:
            # Clean up - restore viewport settings and end progress
            context.preferences.system.use_region_overlap = original_screen_refresh
            if hasattr(context, 'space_data') and hasattr(context.space_data, 'shading'):
                context.space_data.shading.type = original_shading
            wm.progress_end()
            
            # Set frame back to start
            context.scene.frame_set(starting_frame)
            
            # Final view layer update
            bpy.context.view_layer.update()

    def store_config_on_empty(self, empty):
        """Store the spread configuration as custom properties on the empty"""
        # Use Blender's proper custom property system with UI metadata
        empty["spider_spread_radius"] = self.config.radius
        empty.id_properties_ui("spider_spread_radius").update(
            description="Radius of the web spread",
            default=1.0,
            min=0.01
        )
        
        empty["spider_spread_height"] = self.config.height
        empty.id_properties_ui("spider_spread_height").update(
            description="Height variation of the web",
            default=0.25,
            min=0.0
        )
        
        empty["spider_spread_spread_time"] = self.config.spread_time
        empty.id_properties_ui("spider_spread_spread_time").update(
            description="Time for web to spread out (in frames)",
            default=1.0,
            min=0.0
        )
        
        empty["spider_spread_density_spoke"] = self.config.density_spoke
        empty.id_properties_ui("spider_spread_density_spoke").update(
            description="Number of radial spokes",
            default=5,
            min=3,
            max=64
        )
        
        empty["spider_spread_density_rib"] = self.config.density_rib
        empty.id_properties_ui("spider_spread_density_rib").update(
            description="Number of concentric ribs",
            default=3,
            min=1,
            max=32
        )
        
        empty["spider_spread_curvature"] = self.config.curvature
        empty.id_properties_ui("spider_spread_curvature").update(
            description="Curvature of web strands",
            default=0.1,
            min=0.0,
            max=2.0
        )
        
        empty["spider_spread_random_spread_edge"] = self.config.random_spread_edge
        empty.id_properties_ui("spider_spread_random_spread_edge").update(
            description="Random variation at web edges",
            default=0.1,
            min=0.0,
            max=1.0
        )
        
        empty["spider_spread_random_spread_interior"] = self.config.random_spread_interior
        empty.id_properties_ui("spider_spread_random_spread_interior").update(
            description="Random variation in web interior",
            default=0.05,
            min=0.0,
            max=1.0
        )
        
        # Store random values for consistency/reproducibility
        self.store_random_values_on_empty(empty)
    
    def store_random_values_on_empty(self, empty):
        """Store the generated random values on the empty for consistency"""
        # Store edge random offsets
        for i, (x_offset, y_offset) in self.edge_random_offsets.items():
            empty[f"spider_spread_edge_random_x_{i}"] = x_offset
            empty[f"spider_spread_edge_random_y_{i}"] = y_offset
        
        # Store interior random offsets
        for (spoke_i, rib_j), offset in self.interior_random_offsets.items():
            empty[f"spider_spread_interior_random_{spoke_i}_{rib_j}"] = offset
    
    @staticmethod
    def load_config_from_empty(empty):
        """Load the spread configuration from custom properties on the empty"""
        config = SpiderSpreadConfig()
        
        if "spider_spread_radius" in empty:
            config.radius = empty["spider_spread_radius"]
        if "spider_spread_height" in empty:
            config.height = empty["spider_spread_height"]
        if "spider_spread_spread_time" in empty:
            config.spread_time = empty["spider_spread_spread_time"]
        if "spider_spread_density_spoke" in empty:
            config.density_spoke = empty["spider_spread_density_spoke"]
        if "spider_spread_density_rib" in empty:
            config.density_rib = empty["spider_spread_density_rib"]
        if "spider_spread_curvature" in empty:
            config.curvature = empty["spider_spread_curvature"]
        if "spider_spread_random_spread_edge" in empty:
            config.random_spread_edge = empty["spider_spread_random_spread_edge"]
        if "spider_spread_random_spread_interior" in empty:
            config.random_spread_interior = empty["spider_spread_random_spread_interior"]
        
        return config
    
    @staticmethod
    def load_random_values_from_empty(empty, density_spoke, density_rib):
        """Load the stored random values from the empty"""
        edge_random_offsets = {}
        interior_random_offsets = {}
        
        # Load edge random offsets
        for i in range(density_spoke):
            x_key = f"spider_spread_edge_random_x_{i}"
            y_key = f"spider_spread_edge_random_y_{i}"
            if x_key in empty and y_key in empty:
                edge_random_offsets[i] = (empty[x_key], empty[y_key])
        
        # Load interior random offsets
        for i in range(density_spoke):
            for j in range(density_rib):
                key = f"spider_spread_interior_random_{i}_{j}"
                if key in empty:
                    interior_random_offsets[(i, j)] = empty[key]
        
        return edge_random_offsets, interior_random_offsets
    
    def load_random_values_from_empty_instance(self, empty):
        """Load random values from empty into this instance"""
        self.edge_random_offsets, self.interior_random_offsets = self.load_random_values_from_empty(
            empty, self.config.density_spoke, self.config.density_rib
        )
    
    def set_random_values(self, edge_random_offsets, interior_random_offsets):
        """Set the random values directly (for preserving values during updates)"""
        self.edge_random_offsets = edge_random_offsets.copy() if edge_random_offsets else {}
        self.interior_random_offsets = interior_random_offsets.copy() if interior_random_offsets else {}