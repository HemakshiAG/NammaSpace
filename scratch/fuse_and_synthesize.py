import sys
import json
import time
from pathlib import Path
import numpy as np
import pycolmap
from scipy.spatial import cKDTree

def main():
    sparse_dir = Path("uploads/test_vid2_run/colmap_workspace/sparse_extended")
    splat_out = Path("web/scene.splat")
    cam_out = Path("web/cameras.json")
    
    # 1. Load all valid reconstructions
    models = {}
    for sub in sorted(sparse_dir.iterdir(), key=lambda x: int(x.name) if x.name.isdigit() else 999):
        if sub.is_dir() and (sub / "cameras.bin").exists():
            rec = pycolmap.Reconstruction(sub)
            if len(rec.points3D) > 50 and len(rec.images) >= 3:
                models[int(sub.name)] = rec
                print(f"Loaded Model {sub.name}: {len(rec.images)} imgs, {len(rec.points3D)} pts")
                
    if not models:
        print("No valid models found!")
        return
        
    # 2. Pick anchor model with maximum points
    anchor_id = max(models.keys(), key=lambda k: len(models[k].points3D))
    anchor_rec = models[anchor_id]
    print(f"\nAnchor Model is {anchor_id} ({len(anchor_rec.images)} imgs, {len(anchor_rec.points3D)} pts)")
    
    aligned_models = {anchor_id: anchor_rec}
    remaining_ids = set(models.keys()) - {anchor_id}
    
    # Iteratively align remaining models using exact Sim3d camera center alignment
    changed = True
    while remaining_ids and changed:
        changed = False
        for mid in list(remaining_ids):
            src_rec = models[mid]
            src_names = set(im.name for im in src_rec.images.values())
            
            # Find best target in aligned models
            best_target_id = None
            max_common = 0
            for aid, tgt_rec in aligned_models.items():
                tgt_names = set(im.name for im in tgt_rec.images.values())
                common = src_names.intersection(tgt_names)
                if len(common) > max_common:
                    max_common = len(common)
                    best_target_id = aid
                    
            if max_common >= 3:
                tgt_rec = aligned_models[best_target_id]
                sim3d = pycolmap.align_reconstructions_via_proj_centers(
                    src_reconstruction=src_rec,
                    tgt_reconstruction=tgt_rec,
                    max_proj_center_error=0.25
                )
                if sim3d is not None:
                    src_rec.transform(sim3d)
                    aligned_models[mid] = src_rec
                    remaining_ids.remove(mid)
                    changed = True
                    print(f"Successfully aligned Model {mid} into Model {best_target_id} ({max_common} common imgs)")
                else:
                    # Try reprojections
                    sim3d_rep = pycolmap.align_reconstructions_via_reprojections(
                        src_reconstruction=src_rec,
                        tgt_reconstruction=tgt_rec,
                        min_inlier_observations=0.2,
                        max_reproj_error=12.0
                    )
                    if sim3d_rep is not None:
                        src_rec.transform(sim3d_rep)
                        aligned_models[mid] = src_rec
                        remaining_ids.remove(mid)
                        changed = True
                        print(f"Aligned Model {mid} via reprojections into Model {best_target_id} ({max_common} common imgs)")
                        
    print(f"\nTotal aligned models: {len(aligned_models)} of {len(models)}")
    
    # 3. Aggregate all 3D points and cameras
    all_xyz = []
    all_rgb = []
    all_track_lens = []
    cam_dict = {}
    
    for mid, rec in aligned_models.items():
        # Points
        pts = rec.points3D
        if pts:
            m_xyz = np.array([p.xyz for p in pts.values()], dtype=np.float32)
            m_rgb = np.array([p.color for p in pts.values()], dtype=np.uint8)
            m_tracks = np.array([len(p.track.elements) for p in pts.values()], dtype=np.int32)
            all_xyz.append(m_xyz)
            all_rgb.append(m_rgb)
            all_track_lens.append(m_tracks)
            
        # Cameras
        for im in rec.images.values():
            if im.name not in cam_dict:
                cfw = im.cam_from_world() if callable(im.cam_from_world) else im.cam_from_world
                rot = cfw.rotation() if callable(cfw.rotation) else cfw.rotation
                R = rot.matrix()
                t = cfw.translation
                C = -R.T @ t
                fwd = R.T @ np.array([0, 0, 1.0])
                up = R.T @ np.array([0, -1.0, 0])
                cam_dict[im.name] = {
                    "name": im.name,
                    "pos": [float(C[0]), float(C[1]), float(C[2])],
                    "forward": [float(fwd[0]), float(fwd[1]), float(fwd[2])],
                    "up": [float(up[0]), float(up[1]), float(up[2])],
                }
                
    fused_xyz = np.vstack(all_xyz)
    fused_rgb = np.vstack(all_rgb)
    fused_tracks = np.concatenate(all_track_lens)
    print(f"Raw aggregate points: {len(fused_xyz):,}, Unique registered cameras: {len(cam_dict)}")
    
    # 4. Multi-view consensus & Floater Purge (Statistical Outlier Removal)
    # Require track length >= 3
    track_mask = fused_tracks >= 3
    xyz = fused_xyz[track_mask]
    rgb = fused_rgb[track_mask]
    tracks = fused_tracks[track_mask]
    print(f"After track length >= 3: {len(xyz):,} points")
    
    # k-d tree SOR
    tree = cKDTree(xyz)
    k = min(12, len(xyz) - 1)
    dists, _ = tree.query(xyz, k=k)
    mean_dist = np.mean(dists[:, 1:], axis=1)
    mu = float(np.mean(mean_dist))
    std = float(np.std(mean_dist))
    keep_sor = mean_dist <= (mu + 1.25 * std)
    
    xyz = xyz[keep_sor]
    rgb = rgb[keep_sor]
    tracks = tracks[keep_sor]
    dists = dists[keep_sor]
    N_clean = len(xyz)
    print(f"After SOR floater purge: {N_clean:,} sharp surfels (purged {len(fused_xyz) - N_clean:,} floaters)")
    
    # Center scene around (0, 0, 0) for perfect orbiting and viewing
    centroid = np.median(xyz, axis=0)
    print(f"Translating scene centroid {centroid} -> (0, 0, 0)")
    xyz = xyz - centroid
    
    for im_name, cam in cam_dict.items():
        cam["pos"] = [
            float(cam["pos"][0] - centroid[0]),
            float(cam["pos"][1] - centroid[1]),
            float(cam["pos"][2] - centroid[2])
        ]
    
    # 5. Compute tight pancake surfel scales
    avg_local = np.mean(dists[:, 1:4], axis=1).astype(np.float32)
    s_xy = np.clip(avg_local * 0.40, 0.003, 0.045) # 3mm to 4.5cm
    s_z = s_xy * 0.15 # thin pancake surfel
    scales = np.stack([s_xy, s_xy, s_z], axis=1)
    
    # Solid opaque alpha
    alpha = np.clip(220 + tracks * 10, 235, 255).astype(np.uint8)
    rgba = np.column_stack([rgb, alpha])
    
    # Quaternions (upward pancake surfels)
    quaternions = np.zeros((N_clean, 4), dtype=np.uint8)
    quaternions[:, 0] = 128
    quaternions[:, 1] = 128
    quaternions[:, 2] = 128
    quaternions[:, 3] = 255
    
    # 6. Pack into binary 32-byte .splat
    buf = np.zeros(N_clean, dtype=[
        ('x', '<f4'), ('y', '<f4'), ('z', '<f4'),
        ('sx', '<f4'), ('sy', '<f4'), ('sz', '<f4'),
        ('r', 'u1'), ('g', 'u1'), ('b', 'u1'), ('a', 'u1'),
        ('qx', 'u1'), ('qy', 'u1'), ('qz', 'u1'), ('qw', 'u1'),
    ])
    buf['x'], buf['y'], buf['z'] = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    buf['sx'], buf['sy'], buf['sz'] = scales[:, 0], scales[:, 1], scales[:, 2]
    buf['r'], buf['g'], buf['b'], buf['a'] = rgba[:, 0], rgba[:, 1], rgba[:, 2], rgba[:, 3]
    buf['qx'], buf['qy'], buf['qz'], buf['qw'] = quaternions[:, 0], quaternions[:, 1], quaternions[:, 2], quaternions[:, 3]
    
    with open(splat_out, "wb") as f:
        f.write(buf.tobytes())
    print(f"Wrote {splat_out.stat().st_size:,} bytes to {splat_out}")
    
    # 7. Write centered cameras.json
    sorted_cams = sorted(cam_dict.values(), key=lambda c: c["name"])
    cameras_data = {
        "count": len(sorted_cams),
        "initial": len(sorted_cams) // 2,
        "cameras": sorted_cams
    }
    with open(cam_out, "w", encoding="utf-8") as f:
        json.dump(cameras_data, f, indent=2)
    print(f"Wrote {len(sorted_cams)} camera poses to {cam_out}")
    
    # Print camera bounds and centroid for verification
    cam_positions = np.array([c["pos"] for c in sorted_cams])
    init_cam = sorted_cams[len(sorted_cams) // 2]
    print(f"Initial Camera Pose: pos={init_cam['pos']}, forward={init_cam['forward']}")
    print(f"Scene Bounding Box: min={np.min(xyz, axis=0)}, max={np.max(xyz, axis=0)}")
    print("SUCCESS: 3D scene fully generated and ready!")

if __name__ == "__main__":
    main()
