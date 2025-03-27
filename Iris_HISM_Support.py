import bpy
import json
import os
from math import radians
from mathutils import Vector, Quaternion, Euler, Matrix

# === File Paths ===
# List of JSON map files exported from Unreal Engine that contain instancing data
json_paths = [
    # 'C:/game/maps/xxx.json',
    # 'C:/game/maps/xxx.json'
]

# === Offset Settings ===
# Global offset values applied to all instances (useful for manual adjustments)
x_offset = 0.0
y_offset = 0.0
z_offset = 0.0

# === Rotation Settings (Degrees) ===
# Rotation to apply to the blueprint parent and each instance (in degrees)
blueprint_rotation_deg = (0.0, 0.0, 0.0)
instance_rotation_deg = (0.0, 180.0, 180.0)

# === Mirror Settings ===
# Whether to mirror the blueprint or instance on X or Y axes
mirror_blueprint_x = False
mirror_blueprint_y = False
mirror_instance_x = False
mirror_instance_y = True

# === Build Quaternion Rotations ===
# Convert Euler angles to quaternion for later rotation applications
blueprint_rot_quat = Euler(
    tuple(radians(a) for a in blueprint_rotation_deg), 'XYZ').to_quaternion()
instance_rot_quat = Euler(
    tuple(radians(a) for a in instance_rotation_deg), 'XYZ').to_quaternion()

# === Used base objects for delayed cleanup ===
# Store base mesh objects that are used as templates, to be removed later
used_base_objects = set()

# === Process Each Map JSON ===
# Loop through all JSON files and apply their HISM data into Blender
for json_path in json_paths:
    if not os.path.exists(json_path):
        print(f"[Missing] File not found: {json_path}")
        continue

    print(f"\n=== Processing Map: {os.path.basename(json_path)} ===")

    # Load and parse the JSON file
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    entries = data if isinstance(data, list) else list(data.values())

    # Iterate through each entry and look for instanced mesh components
    for entry in entries:
        if entry.get("Type") != "InstancedStaticMeshComponent":
            continue

        outer_name = entry.get("Outer")
        if not outer_name:
            continue

        # Attempt to find the base object in Blender scene
        base_obj = bpy.data.objects.get(outer_name)
        if not base_obj:
            print(f"[Skipped] Missing base object: {outer_name}")
            continue

        per_instance_data = entry.get("PerInstanceSMData", [])
        if not per_instance_data:
            print(f"[Skipped] No instance data: {outer_name}")
            continue

        print(f"[Processing] {outer_name} ({len(per_instance_data)} instances)")

        # Get relative location offset from the component
        props = entry.get("Properties", {})
        rel = props.get("RelativeLocation", {})
        component_offset = Vector((
            rel.get("X", 0) / 100 + x_offset,
            rel.get("Y", 0) / -100 + y_offset,
            rel.get("Z", 0) / 100 + z_offset
        ))

        # === Process Each Instance ===
        for i, instance in enumerate(per_instance_data):
            tf = instance.get("TransformData")
            if not tf:
                print(f"  [Warning] Missing TransformData in instance {i}")
                continue

            # Get rotation, translation, and scale data
            rot = tf.get("Rotation", {})
            trans = tf.get("Translation", {})
            scale = tf.get("Scale3D", {})

            # Convert quaternion rotation from JSON
            raw_quat = Quaternion((
                rot.get("W", 1),
                rot.get("X", 0),
                rot.get("Y", 0),
                rot.get("Z", 0)
            )).normalized()

            # Apply mirroring to instance rotation
            if mirror_instance_x or mirror_instance_y:
                mat = raw_quat.to_matrix().to_4x4()
                mirror_vec = Vector((
                    -1 if mirror_instance_x else 1,
                    -1 if mirror_instance_y else 1,
                    1
                ))
                mirror_mat = Matrix.Diagonal(mirror_vec).to_4x4()
                mat = mirror_mat @ mat

                # Handle negative determinant (flipped object)
                if mat.to_3x3().determinant() < 0:
                    for j in range(3):
                        mat[j][2] *= -1
                    print(f"  [Mirror Fix] Z axis flipped in instance {i}")

                raw_quat = mat.to_quaternion().normalized()

            # Convert local position and apply blueprint rotation/mirroring
            local_pos = Vector((
                trans.get("X", 0) / 100,
                trans.get("Y", 0) / -100,
                trans.get("Z", 0) / 100
            ))

            if mirror_blueprint_x:
                local_pos.x *= -1
            if mirror_blueprint_y:
                local_pos.y *= -1

            rotated_pos = blueprint_rot_quat @ local_pos
            world_pos = component_offset + rotated_pos
            final_quat = blueprint_rot_quat @ (raw_quat @ instance_rot_quat)

            sca = Vector((
                scale.get("X", 1),
                scale.get("Y", 1),
                scale.get("Z", 1)
            ))

            # === Create a copy of the base object and apply transform ===
            dup = base_obj.copy()
            if base_obj.data:
                dup.data = base_obj.data.copy()
            dup.name = f"{outer_name}_Instance_{i}"
            bpy.context.collection.objects.link(dup)

            # Apply final transform (position, scale, rotation)
            dup.location = world_pos
            dup.scale = sca
            dup.rotation_mode = 'QUATERNION'
            dup.rotation_quaternion = final_quat

        # Store for deletion after all instances are created
        used_base_objects.add(base_obj.name)
        print(f"[Queued for Cleanup] {outer_name}")

# === Cleanup: Remove all used base objects ===
# Delete the original base objects to keep only the instances
for obj_name in used_base_objects:
    obj = bpy.data.objects.get(obj_name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)
        print(f"[Cleanup] Removed base object: {obj_name}")
