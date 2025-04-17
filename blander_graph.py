import bpy
from mathutils import Vector
import csv
import os
import colorsys


# ─── 1) UPDATE THIS ────────────────────────────────────────────────────────────────
base_path  = "/Users/benyla/Desktop"    # ← your folder containing nodes.csv & edges.csv
nodes_csv  = os.path.join(base_path, "nodes.csv")
edges_csv  = os.path.join(base_path, "edges.csv")
# ────────────────────────────────────────────────────────────────────────────────

# ─── 2) Clear the existing scene ────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ─── Create Empty and Camera FIRST ───────────────────────────────────────────────
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
empty = bpy.context.object
empty.name = "GraphCenter"

# ─── Create Camera Safely (without relying on context) ───────────────────────────
cam_data = bpy.data.cameras.new("OrbitCamera")
camera = bpy.data.objects.new("OrbitCamera", cam_data)
bpy.context.collection.objects.link(camera)
camera.location = (0, -40, 10)

# Add track-to constraint to keep camera pointed at the graph center
cam_con = camera.constraints.new(type='TRACK_TO')
cam_con.target = empty
cam_con.track_axis = 'TRACK_NEGATIVE_Z'
cam_con.up_axis = 'UP_Y'

# Parent camera to empty for orbit animation
camera.parent = empty

# Set camera as active
scene = bpy.context.scene
scene.camera = camera

# ─── 360‑degree camera orbit setup ────────────────────────────────────────────
scene.frame_start = 1
scene.frame_end = 600  # <-- 300 frames = 5 seconds at 60 fps
scene.render.fps = 60 

radius = 20                    # <— move closer/farther by changing this
camera.location = (0, -radius, radius * 0.4)  # nice elevated starting point

# Animate the empty: 0 → 360° around Z
empty.rotation_euler = (0, 0, 0)
empty.keyframe_insert(data_path="rotation_euler", frame=scene.frame_start)

empty.rotation_euler = (0, 0, 6.28319)        # 2π rad = 360°
empty.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)

# Make the spin smooth & constant
for fcurve in empty.animation_data.action.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'LINEAR'

# (optional) slightly longer lens so graph fills the frame
camera.data.lens = 60


# ─── Add light and adjust background ────────────────────────────────────────────
bpy.ops.object.light_add(type='SUN', location=(0, 0, 50))  # Sunlight above the graph

# 💡 Additional soft fill light for contrast
bpy.ops.object.light_add(type='AREA', location=(30, -30, 20))
bpy.context.object.data.energy = 500

# Set ambient world brightness (optional, dimmer = 0.5)
try:
    bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[1].default_value = 0.5
except:
    print("Background node tree not found. Skipping dimming.")

# ─── 3) Compute max node‐size for normalization ─────────────────────────────────
with open(nodes_csv, newline='') as f:
    reader   = csv.DictReader(f)
    max_size = max(float(r['size']) for r in reader if r['size'].strip() != "")

# ─── 4) Create nodes (spheres + colored materials + labels) ─────────────────────
node_locations = {}
with open(nodes_csv, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # parse CSV fields
        node_id = row['id']
        x, y, z = float(row['x']), float(row['y']), float(row['z'])
        pos      = Vector((x*10, y*10, z*10))   # scale up for visibility
        label    = row.get('label', node_id)
        size_val = float(row.get('size', 1.0))

        # normalize size → [0,1]
        norm = size_val / max_size if max_size > 0 else 0.5
        # map normalized size to hue (0=red → 0.6=blue)
        hue = 0.6 - 0.6 * norm
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)

        # create and assign material
        mat = bpy.data.materials.new(name=f"Mat_{label}")
        mat.diffuse_color = (r, g, b, 1)

        # create sphere
        # map raw size to a [min_radius, max_radius] range
        min_r, max_r = 0.05, 0.3
        norm = size_val / max_size if max_size>0 else 0
        sphere_radius = min_r + norm * (max_r - min_r)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=sphere_radius, location=pos)
        sphere = bpy.context.object
        sphere.name = label
        sphere.data.materials.append(mat)

        # create text label above the sphere
        bpy.ops.object.text_add(location=pos + Vector((0, 0, sphere_radius + 0.2)))
        txt = bpy.context.object
        txt.data.body = label

        txt.data.size = 0.1
        txt.name = f"Label_{label}"

        node_locations[node_id] = pos

# ─── 5) Create edges as 3D curves ───────────────────────────────────────────────
with open(edges_csv, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        src = row['source']
        tgt = row['target']
        if src not in node_locations or tgt not in node_locations:
            continue

        p1 = node_locations[src]
        p2 = node_locations[tgt]

        # make a new 3D curve
        curve = bpy.data.curves.new("EdgeCurve", type='CURVE')
        curve.dimensions = '3D'
        curve.bevel_depth      = 0.005   # sets thickness of the line
        curve.bevel_resolution = 3      # smoothness
        spline = curve.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co = (*p1, 1)
        spline.points[1].co = (*p2, 1)

        obj = bpy.data.objects.new("Edge", curve)
        bpy.context.collection.objects.link(obj)
        
