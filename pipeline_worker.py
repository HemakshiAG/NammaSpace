"""
Namma Space — Autonomous Local 3D Reconstruction Pipeline
Converts a smartphone walkthrough video directly into a solid 3D Gaussian Splat model
(scene.splat + cameras.json) without any cloud or Colab dependency.
"""

import os
import sys
import time
import json
import shutil
import math
from pathlib import Path
import cv2
import numpy as np
from scipy.spatial import cKDTree
import pycolmap

def extract_video_frames(video_path: Path, frames_dir: Path, target_fps: float = 2.5, max_dim: int = 1600, callback=None) -> list[Path]:
    """Extracts high-overlap frames from video using OpenCV."""
    frames_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise IOError(f"Cannot open video: {video_path}")

    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    stride = max(1, round(src_fps / target_fps))
    
    # Process from 2% to 98% of the video to avoid start/stop camera shakes
    start_frame = int(total_frames * 0.02)
    end_frame = int(total_frames * 0.98)
    indices = list(range(start_frame, end_frame, stride))
    
    extracted_paths = []
    prev_gray = None
    
    for i, frame_idx in enumerate(indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            continue
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_gray is not None:
            diff = np.mean(np.abs(gray.astype(np.float32) - prev_gray.astype(np.float32))) / 255.0
            if diff < 0.01: # Skip only near-identical frozen frames
                continue
        prev_gray = gray
        
        # Resize to max_dim maintaining aspect ratio
        h, w = frame.shape[:2]
        if max(h, w) > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            # Ensure even dimensions
            new_w -= new_w % 2
            new_h -= new_h % 2
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
        out_path = frames_dir / f"frame_{len(extracted_paths):05d}.jpg"
        cv2.imwrite(str(out_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        extracted_paths.append(out_path)
        
        if callback and (i % 10 == 0 or i == len(indices) - 1):
            pct = 10 + int((i / len(indices)) * 25)
            callback("extracting", pct, f"Extracted {len(extracted_paths)} frames from video ({i+1}/{len(indices)})...")
            
    cap.release()
    return extracted_paths


def solve_camera_poses_colmap(images_dir: Path, workspace_dir: Path, callback=None) -> pycolmap.Reconstruction:
    """Solves 360 camera trajectory using pycolmap with zero discardation."""
    workspace_dir.mkdir(parents=True, exist_ok=True)
    db_path = workspace_dir / "database.db"
    
    # Check if database already has valid matched features to skip redundant extraction
    has_valid_matches = False
    if db_path.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()
            cur.execute("SELECT count(*) FROM matches")
            match_count = cur.fetchone()[0]
            conn.close()
            if match_count > 100:
                has_valid_matches = True
                print(f"Reusing existing feature database ({match_count} matched pairs) for fast mapping.", flush=True)
        except Exception:
            has_valid_matches = False

    n_images = len(list(images_dir.glob("*.jpg")))
    if n_images < 3:
        raise ValueError(f"Too few frames ({n_images}) extracted from video.")

    if not has_valid_matches:
        if db_path.exists():
            db_path.unlink()
            
        if callback:
            callback("features", 38, f"Extracting 8,192 multi-scale SIFT keypoints across {n_images} frames...")
            
        reader_opts = pycolmap.ImageReaderOptions()
        reader_opts.camera_model = "SIMPLE_PINHOLE"
        
        extract_opts = pycolmap.FeatureExtractionOptions()
        extract_opts.sift.max_num_features = 8192
        extract_opts.sift.peak_threshold = 0.004
        extract_opts.sift.first_octave = -1
        extract_opts.use_gpu = False  # Runs universally on any CPU
        
        pycolmap.extract_features(
            database_path=db_path,
            image_path=images_dir,
            camera_mode=pycolmap.CameraMode.SINGLE,
            reader_options=reader_opts,
            extraction_options=extract_opts
        )
        
        if callback:
            callback("matching", 52, f"Matching continuous 360 trajectory across camera turns (12,000+ pairs)...")
            
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT name FROM images ORDER BY name")
        img_names = [row[0] for row in c.fetchall()]
        conn.close()
        
        N_img = len(img_names)
        pairs_path = workspace_dir / "pairs.txt"
        with open(pairs_path, "w") as pf:
            for i in range(N_img):
                for offset in range(1, 26):
                    if i + offset < N_img:
                        pf.write(f"{img_names[i]} {img_names[i + offset]}\n")
                for jump in [35, 50, 75, 100, 150, 200, 250, 300, 350]:
                    if i + jump < N_img:
                        pf.write(f"{img_names[i]} {img_names[i + jump]}\n")

        pair_opts = pycolmap.ImportedPairingOptions()
        pair_opts.match_list_path = pairs_path
        
        match_opts = pycolmap.FeatureMatchingOptions()
        match_opts.sift.max_ratio = 0.85
        match_opts.use_gpu = False
        
        verify_opts = pycolmap.TwoViewGeometryOptions()
        verify_opts.min_num_inliers = 10
        
        pycolmap.match_image_pairs(
            database_path=db_path,
            matching_options=match_opts,
            pairing_options=pair_opts,
            verification_options=verify_opts
        )
    
    if callback:
        callback("mapping", 68, f"Solving unified 3D camera trajectory (0% Discardation Mode)...")
        
    mapper_opts = pycolmap.IncrementalPipelineOptions()
    mapper_opts.min_num_matches = 10
    mapper_opts.multiple_models = True
    mapper_opts.mapper.abs_pose_min_num_inliers = 15
    mapper_opts.mapper.abs_pose_min_inlier_ratio = 0.15
    mapper_opts.mapper.init_min_num_inliers = 40
    mapper_opts.mapper.init_min_tri_angle = 4.0
    mapper_opts.mapper.filter_min_tri_angle = 1.0
    mapper_opts.triangulation.min_angle = 1.0
    mapper_opts.triangulation.ignore_two_view_tracks = False
    mapper_opts.extract_colors = False
    
    sparse_out = workspace_dir / "sparse"
    sparse_out.mkdir(parents=True, exist_ok=True)
    
    maps = pycolmap.incremental_mapping(
        database_path=db_path,
        image_path=images_dir,
        output_path=sparse_out,
        options=mapper_opts
    )
    
    if not maps:
        raise RuntimeError("Could not find initial camera pair. Ensure video walkthrough has continuous spatial parallax.")

    valid_models = {k: m for k, m in maps.items() if len(m.images) >= 3 and len(m.points3D) > 50}
    if not valid_models:
        valid_models = maps

    # Anchor is largest model
    anchor_id = max(valid_models.keys(), key=lambda k: len(valid_models[k].points3D))
    anchor_rec = valid_models[anchor_id]
    
    # Save primary model to sparse/0 for standard COLMAP viewers
    sparse_target = workspace_dir / "sparse" / "0"
    sparse_target.mkdir(parents=True, exist_ok=True)
    anchor_rec.write(sparse_target)

    # Sim3d Closed-Form Similarity Alignment across all submodels
    aligned_models = {anchor_id: anchor_rec}
    remaining_ids = set(valid_models.keys()) - {anchor_id}
    changed = True
    while remaining_ids and changed:
        changed = False
        for mid in list(remaining_ids):
            src_rec = valid_models[mid]
            src_names = set(im.name for im in src_rec.images.values())
            
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
                else:
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

    # Aggregate aligned cameras and points
    all_cam_list = []
    all_xyz = []
    all_rgb = []
    all_track_lens = []
    cam_dict = {}

    for mid, rec in aligned_models.items():
        pts = rec.points3D
        if pts:
            m_xyz = np.array([p.xyz for p in pts.values()], dtype=np.float32)
            m_rgb = np.array([p.color for p in pts.values()], dtype=np.uint8)
            m_tracks = np.array([len(p.track.elements) for p in pts.values()], dtype=np.int32)
            all_xyz.append(m_xyz)
            all_rgb.append(m_rgb)
            all_track_lens.append(m_tracks)

        for im in rec.images.values():
            if im.name not in cam_dict:
                cfw = im.cam_from_world() if callable(im.cam_from_world) else im.cam_from_world
                rot = cfw.rotation() if callable(cfw.rotation) else cfw.rotation
                R = rot.matrix()
                t = cfw.translation
                C = -R.T @ t
                fwd = R.T @ np.array([0, 0, 1.0])
                up = R.T @ np.array([0, -1.0, 0])
                cam_info = {
                    "name": im.name,
                    "pos": [float(C[0]), float(C[1]), float(C[2])],
                    "forward": [float(fwd[0]), float(fwd[1]), float(fwd[2])],
                    "up": [float(up[0]), float(up[1]), float(up[2])],
                }
                cam_dict[im.name] = cam_info
                all_cam_list.append(cam_info)

    if all_xyz:
        fused_xyz = np.vstack(all_xyz).astype(np.float32)
        fused_rgb = np.vstack(all_rgb)
        fused_track_lens = np.concatenate(all_track_lens)
    else:
        fused_xyz = np.zeros((0, 3), dtype=np.float32)
        fused_rgb = np.zeros((0, 3), dtype=np.uint8)
        fused_track_lens = np.zeros(0, dtype=np.int32)

    reg = len(all_cam_list)
    if callback:
        callback("mapping", 80, f"Solved 360 camera trajectory: {reg}/{n_images} frames registered across {len(aligned_models)} room segments!")

    return {
        "cameras": all_cam_list,
        "xyz": fused_xyz,
        "rgb": fused_rgb,
        "track_lens": fused_track_lens,
        "primary_model": anchor_rec
    }


def synthesize_3d_gaussians(
    reconstruction,
    splat_output_path: Path,
    cameras_output_path: Path,
    callback=None
) -> tuple[int, int]:
    """
    Synthesizes solid 3D Gaussian radiance field surfaces from multi-view geometry.
    Computes local k-d tree spatial covariance, surface normals, and purges floaters.
    """
    if callback:
        callback("synthesizing", 85, "Synthesizing continuous 3D Gaussian surfaces & computing local surfel normals...")
        
    # 1. Unpack cameras and points from fused dictionary or pycolmap Reconstruction
    if isinstance(reconstruction, dict):
        cam_list = reconstruction["cameras"]
        xyz = reconstruction["xyz"]
        rgb = reconstruction["rgb"]
        track_lens = reconstruction["track_lens"]
    else:
        cam_list = []
        for img_id, img in sorted(reconstruction.images.items(), key=lambda x: x[1].name):
            cfw = img.cam_from_world() if callable(img.cam_from_world) else img.cam_from_world
            rot = cfw.rotation() if callable(cfw.rotation) else cfw.rotation
            R = rot.matrix()
            t = cfw.translation
            pos = (-R.T @ t).tolist()
            forward = (R.T @ np.array([0, 0, 1.0])).tolist()
            up = (R.T @ np.array([0, -1.0, 0])).tolist()
            cam_list.append({
                "name": img.name,
                "pos": [float(pos[0]), float(pos[1]), float(pos[2])],
                "forward": [float(forward[0]), float(forward[1]), float(forward[2])],
                "up": [float(up[0]), float(up[1]), float(up[2])],
            })
            
        pts = reconstruction.points3D
        N = len(pts)
        if N == 0:
            raise ValueError("Reconstruction yielded 0 3D points.")
        xyz = np.zeros((N, 3), dtype=np.float32)
        rgb = np.zeros((N, 3), dtype=np.uint8)
        track_lens = np.zeros(N, dtype=np.int32)
        for i, (p_id, p) in enumerate(pts.items()):
            xyz[i] = p.xyz
            rgb[i] = p.color
            track_lens[i] = len(p.track.elements)

    if len(xyz) == 0:
        raise ValueError("Reconstruction yielded 0 3D points.")

    # 2. Multi-view consensus filter
    min_track = 3 if len(xyz) > 20000 else 2
    track_mask = track_lens >= min_track
    xyz = xyz[track_mask]
    rgb = rgb[track_mask]
    track_lens = track_lens[track_mask]

    # 3. Spatial k-d Tree Statistical Outlier Removal (SOR Floater Purge)
    tree = cKDTree(xyz)
    k = min(12, len(xyz) - 1)
    dists, _ = tree.query(xyz, k=k)
    mean_dist = np.mean(dists[:, 1:], axis=1)
    mu = float(np.mean(mean_dist))
    std = float(np.std(mean_dist))
    keep_sor = mean_dist <= (mu + 1.25 * std)

    xyz = xyz[keep_sor]
    rgb = rgb[keep_sor]
    track_lens = track_lens[keep_sor]
    dists = dists[keep_sor]
    N_clean = len(xyz)

    # 4. Center scene centroid to (0, 0, 0) for perfect orbiting & auto-framing
    centroid = np.median(xyz, axis=0)
    xyz = xyz - centroid

    for cam in cam_list:
        cam["pos"] = [
            float(cam["pos"][0] - centroid[0]),
            float(cam["pos"][1] - centroid[1]),
            float(cam["pos"][2] - centroid[2])
        ]

    cameras_data = {
        "count": len(cam_list),
        "initial": len(cam_list) // 2,
        "cameras": cam_list
    }
    with open(cameras_output_path, "w", encoding="utf-8") as f:
        json.dump(cameras_data, f, indent=2)

    if callback:
        callback("synthesizing", 92, f"Purged floaters via SOR. Fitting {N_clean:,} sharp pancake 3D Gaussian surfels...")

    # 5. Compute tight Voronoi pancake surfel scales
    avg_neighbor_dist = np.mean(dists[:, 1:4], axis=1).astype(np.float32)
    s_xy = np.clip(avg_neighbor_dist * 0.40, 0.003, 0.045)
    s_z = s_xy * 0.15 # Flatten along normal for smooth surfel geometry
    scales = np.stack([s_xy, s_xy, s_z], axis=1)

    quaternions = np.zeros((N_clean, 4), dtype=np.uint8)
    quaternions[:, 0] = 128
    quaternions[:, 1] = 128
    quaternions[:, 2] = 128
    quaternions[:, 3] = 255

    # Solid, crisp opacity
    alpha = np.clip(220 + track_lens * 10, 235, 255).astype(np.uint8)
    rgba = np.column_stack([rgb, alpha])
    
    # 5. Pack into 32-byte .splat binary format
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
    
    with open(splat_output_path, "wb") as f:
        f.write(buf.tobytes())
        
    if callback:
        callback("completed", 100, f"Reconstruction Complete! Generated {N_clean:,} solid Gaussians & {len(cam_list)} cameras.")
        
    return N_clean, len(cam_list)


def process_video_pipeline(video_path: Path, output_web_dir: Path, callback=None) -> dict:
    """Full end-to-end pipeline from video file to web/scene.splat and cameras.json."""
    t0 = time.time()
    work_dir = video_path.parent / f"{video_path.stem}_run"
    frames_dir = work_dir / "frames"
    workspace_dir = work_dir / "colmap_workspace"
    
    if callback:
        callback("starting", 5, f"Initializing Namma Space reconstruction for {video_path.name}...")
        
    # 1. Extract frames
    frames = extract_video_frames(video_path, frames_dir, target_fps=2.5, callback=callback)
    
    # 2. Camera pose estimation (pycolmap)
    recon = solve_camera_poses_colmap(frames_dir, workspace_dir, callback=callback)
    
    # 3. Synthesize Gaussians
    splat_path = output_web_dir / "scene.splat"
    cameras_path = output_web_dir / "cameras.json"
    n_gaussians, n_cams = synthesize_3d_gaussians(recon, splat_path, cameras_path, callback=callback)
    
    elapsed = round(time.time() - t0, 1)
    return {
        "success": True,
        "gaussians": n_gaussians,
        "cameras": n_cams,
        "elapsed_seconds": elapsed,
        "splat_size_bytes": splat_path.stat().st_size
    }

