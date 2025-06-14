import bpy

def create_web_curve_node_tree(name="WebCurveNodeTree"):
    """Create the geometry node tree for web curves"""
    
    # Create new node tree
    node_tree = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    
    # Create input and output nodes
    input_node = node_tree.nodes.new('NodeGroupInput')
    output_node = node_tree.nodes.new('NodeGroupOutput')
    
    # Position input/output nodes
    input_node.location = (-800, 0)
    output_node.location = (600, 0)
    
    # Create node tree interface in the correct order
    # Input sockets
    web_center_input = node_tree.interface.new_socket(name="Web Center", socket_type='NodeSocketObject', in_out='INPUT')
    web_spoke_input = node_tree.interface.new_socket(name="Web Spoke", socket_type='NodeSocketObject', in_out='INPUT')  
    web_origin_input = node_tree.interface.new_socket(name="Web Origin", socket_type='NodeSocketObject', in_out='INPUT')
    profile_radius_input = node_tree.interface.new_socket(name="Profile Radius", socket_type='NodeSocketFloat', in_out='INPUT')
    curve_resolution_input = node_tree.interface.new_socket(name="Curve Resolution", socket_type='NodeSocketInt', in_out='INPUT')
    curve_amount_input = node_tree.interface.new_socket(name="Curve Amount", socket_type="NodeSocketFloat", in_out='INPUT')
    
    # Set default values
    profile_radius_input.default_value = 0.01
    curve_resolution_input.default_value = 30
    curve_amount_input = 0.1
    
    # Output socket
    geometry_output = node_tree.interface.new_socket(name="Geometry", socket_type='NodeSocketGeometry', in_out='OUTPUT')
    
    # Create Object Info nodes
    obj_info_center = node_tree.nodes.new('GeometryNodeObjectInfo')
    obj_info_center.name = "Object Info Center"
    obj_info_center.location = (-600, 200)
    
    obj_info_spoke = node_tree.nodes.new('GeometryNodeObjectInfo')
    obj_info_spoke.name = "Object Info Spoke"
    obj_info_spoke.location = (-600, 0)
    
    obj_info_origin = node_tree.nodes.new('GeometryNodeObjectInfo')
    obj_info_origin.name = "Object Info Origin"
    obj_info_origin.location = (-600, -200)
    
    # Create Curve Line node
    curve_line = node_tree.nodes.new('GeometryNodeCurvePrimitiveLine')
    curve_line.location = (-400, 100)
    curve_line.inputs['Start'].default_value = (0, 0, 0)
    curve_line.inputs['End'].default_value = (0, 0, 1)
    
    # Create Resample Curve node
    resample_curve = node_tree.nodes.new('GeometryNodeResampleCurve')
    resample_curve.location = (-200, 100)
    resample_curve.mode = 'COUNT'
    
    # Create Spline Parameter node
    spline_param = node_tree.nodes.new('GeometryNodeSplineParameter')
    spline_param.location = (-200, -100)
    
    # Create Math nodes for the complex curve calculation
    math_005 = node_tree.nodes.new('ShaderNodeMath')
    math_005.name = "Math.005"
    math_005.location = (0, -50)
    math_005.operation = 'POWER'
    math_005.inputs[1].default_value = 2.0
    
    math_006 = node_tree.nodes.new('ShaderNodeMath')
    math_006.name = "Math.006"
    math_006.location = (0, -150)
    math_006.operation = 'SUBTRACT'
    
    math_007 = node_tree.nodes.new('ShaderNodeMath')
    math_007.name = "Math.007"
    math_007.location = (0, -250)
    math_007.operation = 'MULTIPLY'
    math_007.inputs[1].default_value = 4.0
    
    math_008 = node_tree.nodes.new('ShaderNodeMath')
    math_008.name = "Math.008"
    math_008.location = (0, -350)
    math_008.operation = 'MULTIPLY'
    math_008.inputs[1].default_value = 0.1
    
    # Create Vector Math nodes
    vec_math = node_tree.nodes.new('ShaderNodeVectorMath')
    vec_math.name = "Vector Math"
    vec_math.location = (-400, -200)
    vec_math.operation = 'ADD'
    
    vec_math_001 = node_tree.nodes.new('ShaderNodeVectorMath')
    vec_math_001.name = "Vector Math.001"
    vec_math_001.location = (-200, -200)
    vec_math_001.operation = 'SCALE'
    vec_math_001.inputs[3].default_value = 0.5
    
    vec_math_002 = node_tree.nodes.new('ShaderNodeVectorMath')
    vec_math_002.name = "Vector Math.002"
    vec_math_002.location = (-200, -300)
    vec_math_002.operation = 'ADD'
    
    vec_math_003 = node_tree.nodes.new('ShaderNodeVectorMath')
    vec_math_003.name = "Vector Math.003"
    vec_math_003.location = (-200, -400)
    vec_math_003.operation = 'NORMALIZE'
    
    vec_math_007 = node_tree.nodes.new('ShaderNodeVectorMath')
    vec_math_007.name = "Vector Math.007"
    vec_math_007.location = (200, -300)
    vec_math_007.operation = 'SCALE'

    vec_math_008 = node_tree.nodes.new('ShaderNodeVectorMath')
    vec_math_008.name = "Vector Math.008"
    vec_math_008.location = (200, -400)
    vec_math_008.operation = 'SUBTRACT'
    
    # Create Set Position node
    set_position = node_tree.nodes.new('GeometryNodeSetPosition')
    set_position.location = (200, 100)
    set_position.inputs['Selection'].default_value = True
    
    # Create Curve Circle node (profile)
    curve_circle = node_tree.nodes.new('GeometryNodeCurvePrimitiveCircle')
    curve_circle.location = (200, 300)
    curve_circle.mode = 'RADIUS'  # Set mode to radius instead of points
    curve_circle.inputs['Resolution'].default_value = 16
    
    # Create Curve to Mesh node
    curve_to_mesh = node_tree.nodes.new('GeometryNodeCurveToMesh')
    curve_to_mesh.location = (400, 200)
    curve_to_mesh.inputs['Fill Caps'].default_value = True
    
    # Link input nodes to Object Info nodes and other inputs
    node_tree.links.new(input_node.outputs['Web Center'], obj_info_center.inputs['Object'])
    node_tree.links.new(input_node.outputs['Web Spoke'], obj_info_spoke.inputs['Object'])
    node_tree.links.new(input_node.outputs['Web Origin'], obj_info_origin.inputs['Object'])
    node_tree.links.new(input_node.outputs['Profile Radius'], curve_circle.inputs['Radius'])
    node_tree.links.new(input_node.outputs['Curve Resolution'], resample_curve.inputs['Count'])
    
    # Link Object Info to Curve Line
    node_tree.links.new(obj_info_center.outputs['Location'], curve_line.inputs['Start'])
    node_tree.links.new(obj_info_spoke.outputs['Location'], curve_line.inputs['End'])
    
    # Link curve processing chain
    node_tree.links.new(curve_line.outputs['Curve'], resample_curve.inputs['Curve'])
    node_tree.links.new(resample_curve.outputs['Curve'], set_position.inputs['Geometry'])
    node_tree.links.new(set_position.outputs['Geometry'], curve_to_mesh.inputs['Curve'])
    
    # Link profile curve
    node_tree.links.new(curve_circle.outputs['Curve'], curve_to_mesh.inputs['Profile Curve'])
    
    # Link complex math for curve deformation
    node_tree.links.new(spline_param.outputs['Factor'], math_005.inputs[0])
    node_tree.links.new(spline_param.outputs['Factor'], math_005.inputs[0])  # Duplicate connection
    node_tree.links.new(math_005.outputs['Value'], math_006.inputs[0])
    node_tree.links.new(spline_param.outputs['Factor'], math_006.inputs[1])
    node_tree.links.new(math_006.outputs['Value'], math_007.inputs[0])
    node_tree.links.new(math_007.outputs['Value'], math_008.inputs[0])
    
    # Link vector math chain for position calculation
    node_tree.links.new(obj_info_center.outputs['Location'], vec_math.inputs[0])
    node_tree.links.new(obj_info_spoke.outputs['Location'], vec_math.inputs[1])
    node_tree.links.new(vec_math.outputs['Vector'], vec_math_001.inputs[0])
    node_tree.links.new(obj_info_origin.outputs['Location'], vec_math_002.inputs[0])
    node_tree.links.new(vec_math_001.outputs['Vector'], vec_math_002.inputs[1])
    node_tree.links.new(vec_math_002.outputs['Vector'], vec_math_003.inputs[0])
    node_tree.links.new(vec_math_003.outputs['Vector'], vec_math_007.inputs[0])
    node_tree.links.new(math_008.outputs['Value'], vec_math_007.inputs[3])
    node_tree.links.new(vec_math_007.outputs['Vector'], vec_math_008.inputs[0])
    node_tree.links.new(obj_info_origin.outputs['Location'], vec_math_008.inputs[1])

    # Link curvature input to curve amount
    node_tree.links.new(input_node.outputs['Curve Amount'], math_008.inputs[1])
    
    # Link final offset to set position
    node_tree.links.new(vec_math_008.outputs['Vector'], set_position.inputs['Offset'])
    
    # Link final output
    node_tree.links.new(curve_to_mesh.outputs['Mesh'], output_node.inputs['Geometry'])
    
    return node_tree