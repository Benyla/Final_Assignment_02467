import bpy
import csv
import os
import colorsys
from mathutils import Vector

# ─── 1) USER CONFIG ──────────────────────────────────────────────────────────────
base_path     = "/Users/benyla/Desktop"
nodes_csv     = os.path.join(base_path, "nodes.csv")
edges_csv     = os.path.join(base_path, "edges.csv")
frames_folder = os.path.join(base_path, "data_1")

# ─── 2) FRAME & OUTPUT SETUP ─────────────────────────────────────────────────────
scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end   = 600      # 10 s @ 60 FPS
scene.render.fps   = 60

os.makedirs(frames_folder, exist_ok=True)
scene.render.filepath               = os.path.join(frames_folder, "frame_####")
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent          = True

# ─── 3) CLEAR THE SCENE ──────────────────────────────────────────────────────────
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# ─── 4) CAMERA + ORBIT ANIMATION ────────────────────────────────────────────────
bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0,0,0))
empty = bpy.context.object
empty.name = "GraphCenter"

cam_data = bpy.data.cameras.new("OrbitCamera")
camera  = bpy.data.objects.new("OrbitCamera", cam_data)
bpy.context.collection.objects.link(camera)
camera.location = (0, -25, 10)
camera.data.lens = 60

trk = camera.constraints.new(type='TRACK_TO')
trk.target     = empty
trk.track_axis = 'TRACK_NEGATIVE_Z'
trk.up_axis    = 'UP_Y'

camera.parent = empty
scene.camera  = camera

empty.rotation_euler = (0,0,0)
empty.keyframe_insert(data_path="rotation_euler", frame=scene.frame_start)
empty.rotation_euler = (0,0,6.28319)
empty.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)
for fcu in empty.animation_data.action.fcurves:
    for kp in fcu.keyframe_points:
        kp.interpolation = 'LINEAR'

# ─── 5) SHADOW‑FREE DEPTH SHADING ────────────────────────────────────────────────
# 5a) remove any old lamps
for o in [o for o in bpy.data.objects if o.type == 'LIGHT']:
    bpy.data.objects.remove(o, do_unlink=True)

# 5b) neutral low ambient from the world
world = bpy.data.worlds['World']
world.use_nodes = True
bg = world.node_tree.nodes['Background']
# keep it quite dark so your lamps really shape the spheres
bg.inputs[0].default_value = (0.02, 0.02, 0.02, 1)  
bg.inputs[1].default_value = 0.2              

# 5c) add a sun for crisp directional shading…
sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy     = 3.0
# turn off *all* shadows
sun_data.use_shadow = False
if scene.render.engine == 'CYCLES':
    sun_data.cycles.cast_shadow = False

sun = bpy.data.objects.new("KeySun", sun_data)
bpy.context.collection.objects.link(sun)
sun.rotation_euler = (0.7, 0.0, 0.3)   # tip it over a bit

# 5d) add a big area as soft fill…
fill_data = bpy.data.lights.new(name="FillArea", type='AREA')
fill_data.energy     = 400
fill_data.size       = 20
fill_data.use_shadow = False
if scene.render.engine == 'CYCLES':
    fill_data.cycles.cast_shadow = False

fill = bpy.data.objects.new("FillArea", fill_data)
bpy.context.collection.objects.link(fill)
fill.location = (30, -30, 20)


# ─── 6) IMPORT & DRAW NODES + LABELS ─────────────────────────────────────────────
node_locations = {}
label_map       = {}

# find max size
with open(nodes_csv, newline='') as f:
    sizes = [float(r['size']) for r in csv.DictReader(f) if r['size'].strip()]
max_size = max(sizes) if sizes else 1.0

with open(nodes_csv, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        node_id  = row['id']
        x, y, z  = float(row['x']), float(row['y']), float(row['z'])
        pos      = Vector((x*10, y*10, z*10))
        label    = row.get('label', node_id)
        size_val = float(row.get('size', 1.0))

        # record label for later removal
        label_map[node_id] = label

        # color & radius
        norm   = size_val / max_size
        adjusted_norm = norm ** 0.5
        hue    = 0.6 - 0.6*adjusted_norm
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
        radius = 0.1 + 0.2*adjusted_norm

        # material
        mat = bpy.data.materials.new(f"Mat_{label}")
        mat.diffuse_color = (r, g, b, 1)

        # sphere
        bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=pos)
        sph = bpy.context.object
        sph.data.materials.append(mat)
        sph.name = node_id

        # label text
        bpy.ops.object.text_add(location=pos + Vector((0, 0, radius + 0.1)))
        txt = bpy.context.object
        txt.data.body = label
        txt.data.size = 0.1
        ttrk = txt.constraints.new(type='TRACK_TO')
        ttrk.target     = camera
        ttrk.track_axis = 'TRACK_Z'
        ttrk.up_axis    = 'UP_Y'
        txt.name = f"Label_{node_id}"

        node_locations[node_id] = pos

# ─── 7) REMOVE SELECTED ARTIST NODES ─────────────────────────────────────────────
to_remove = {
    "All Artist Adella", "Mimi Webb", "Harry Styles", "Olivia Rodrigo",
    "Lauren Spencer Smith", "Em Beihold", "GAYLE"
}
for node_id, label in list(label_map.items()):
    if label in to_remove:
        # delete sphere
        obj = bpy.data.objects.get(node_id)
        if obj:
            bpy.data.objects.remove(obj, do_unlink=True)
        # delete its label
        txt = bpy.data.objects.get(f"Label_{node_id}")
        if txt:
            bpy.data.objects.remove(txt, do_unlink=True)
        # drop from locations so edges skip it
        node_locations.pop(node_id, None)

# ─── 8) IMPORT & DRAW EDGES ─────────────────────────────────────────────────────
connected_ids = set()
with open(edges_csv, newline='') as f:
    reader = csv.DictReader(f)
    for row in reader:
        src, tgt = row['source'], row['target']
        # skip if either endpoint was removed or never created
        if src not in node_locations or tgt not in node_locations:
            continue
        p1, p2 = node_locations[src], node_locations[tgt]
        connected_ids.update((src, tgt))

        curve = bpy.data.curves.new("EdgeCurve", type='CURVE')
        curve.dimensions  = '3D'
        curve.bevel_depth = 0.005
        spline = curve.splines.new('POLY')
        spline.points.add(1)
        spline.points[0].co = (*p1, 1)
        spline.points[1].co = (*p2, 1)

        edge_obj = bpy.data.objects.new("Edge", curve)
        bpy.context.collection.objects.link(edge_obj)
