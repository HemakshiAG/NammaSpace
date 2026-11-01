import sys
import json
from pathlib import Path
import numpy as np
import pycolmap
import cv2

def run_fusion_test():
    base_dir = Path("uploads/test_vid2_run/colmap_workspace/sparse_tuned")
    
    # Chronological sequence of models
    seq_ids = [1, 7, 3, 10, 9, 2, 5, 4]
    
    models = {}
    for sid in seq_ids:
        p = base_dir / str(sid)
        if p.exists():
            models[sid] = pycolmap.Reconstruction(p)
            
    print(f"Loaded {len(models)} models.")
    
    # Structure to hold all fused data in World Coordinates (Model 1 frame)
    all_cam_list = []
    all_xyz = []
    all_rgb = []
    all_track_lens = []
    
    # Cumulative transform from current model to Model 1: X_world = s * R * X + t
    # For model 1, transform is identity: s=1.0, R=I, t=0
    current_s = 1.0
    current_R = np.eye(3, dtype=np.float64)
    current_t = np.zeros(3, dtype=np.float64)
    
    prev_model = None
    prev_end_cam_world = None
    prev_end_rot_world = None
    prev_velocity_world = None
    
    for sid in seq_ids:
        model = models[sid]
        
        # Sort images by frame number
        sorted_imgs = sorted(model.images.values(), key=lambda im: im.name)
        img_names = [im.name for im in sorted_imgs]
        print(f"\nProcessing Model {sid}: {len(sorted_imgs)} images ({img_names[0]} .. {img_names[-1]}), {len(model.points3D)} points")
        
        # Extract camera centers and orientations in local model frame
        local_cams = []
        local_rots = [] # Camera orientation matrices (R_world_from_cam)
        for img in sorted_imgs:
            cfw = img.cam_from_world() if callable(img.cam_from_world) else img.cam_from_world
            rot = cfw.rotation() if callable(cfw.rotation) else cfw.rotation
            R_cam_from_w = rot.matrix()
            t_cam_from_w = cfw.translation
            R_w_from_cam = R_cam_from_w.T
            C_local = -R_cam_from_w.T @ t_cam_from_w
            local_cams.append(C_local)
            local_rots.append(R_w_from_cam)
            
        local_cams = np.array(local_cams, dtype=np.float64) # (N, 3)
        
        # Calculate local step sizes
        if len(local_cams) > 1:
            step_vectors = np.diff(local_cams, axis=0) # (N-1, 3)
            step_dists = np.linalg.norm(step_vectors, axis=1)
            median_step = float(np.median(step_dists)) if len(step_dists) > 0 else 0.05
            local_vel = np.mean(step_vectors[-3:], axis=0) if len(step_vectors) >= 3 else step_vectors[-1]
        else:
            median_step = 0.05
            local_vel = np.array([0, 0, 0.05])
            
        if prev_model is not None:
            # We need to compute transform (s_trans, R_trans, t_trans) from this model's local frame to World frame
            # 1. Scale matching: match median step distance to world scale
            local_scale = median_step if median_step > 1e-4 else 0.05
            target_scale = prev_median_step_world
            s_rel = target_scale / local_scale
            
            # 2. Rotation alignment: smooth orientation continuation across adjacent frames
            start_rot_local = local_rots[0] # First frame of current model
            # R_trans * start_rot_local = prev_end_rot_world  =>  R_trans = prev_end_rot_world * start_rot_local^T
            R_trans = prev_end_rot_world @ start_rot_local.T
            
            # 3. Translation alignment: smooth trajectory continuation
            # Gap in frame index:
            prev_frame_num = int(prev_img_names[-1].replace("frame_", "").replace(".jpg", ""))
            curr_frame_num = int(img_names[0].replace("frame_", "").replace(".jpg", ""))
            delta_frames = max(1, curr_frame_num - prev_frame_num)
            
            start_cam_world = prev_end_cam_world + prev_velocity_world * delta_frames
            # C_world = s_rel * R_trans * (C_local - C_local[0]) + start_cam_world
            # => C_world = s_rel * R_trans * C_local + (start_cam_world - s_rel * R_trans * C_local[0])
            t_trans = start_cam_world - s_rel * (R_trans @ local_cams[0])
            
            model_s = s_rel
            model_R = R_trans
            model_t = t_trans
        else:
            model_s = 1.0
            model_R = np.eye(3, dtype=np.float64)
            model_t = np.zeros(3, dtype=np.float64)
            
        # Transform all camera positions of this model to World frame
        for i, img in enumerate(sorted_imgs):
            pos_world = model_s * (model_R @ local_cams[i]) + model_t
            rot_world = model_R @ local_rots[i]
            forward = rot_world @ np.array([0, 0, 1.0])
            up = rot_world @ np.array([0, -1.0, 0])
            
            all_cam_list.append({
                "name": img.name,
                "model_id": sid,
                "pos": [float(pos_world[0]), float(pos_world[1]), float(pos_world[2])],
                "forward": [float(forward[0]), float(forward[1]), float(forward[2])],
                "up": [float(up[0]), float(up[1]), float(up[2])],
            })
            
        # Transform all 3D points of this model to World frame
        pts = model.points3D
        N_pts = len(pts)
        if N_pts > 0:
            m_xyz = np.zeros((N_pts, 3), dtype=np.float64)
            m_rgb = np.zeros((N_pts, 3), dtype=np.uint8)
            m_tracks = np.zeros(N_pts, dtype=np.int32)
            for pi, (pid, p) in enumerate(pts.items()):
                m_xyz[pi] = p.xyz
                m_rgb[pi] = p.color
                m_tracks[pi] = len(p.track.elements)
                
            # Apply (model_s, model_R, model_t)
            m_xyz_world = model_s * (m_xyz @ model_R.T) + model_t
            all_xyz.append(m_xyz_world)
            all_rgb.append(m_rgb)
            all_track_lens.append(m_tracks)
            
        # Update trackers for next model
        last_cam_local = local_cams[-1]
        prev_end_cam_world = model_s * (model_R @ last_cam_local) + model_t
        prev_end_rot_world = model_R @ local_rots[-1]
        prev_velocity_world = model_s * (model_R @ local_vel)
        prev_median_step_world = model_s * median_step
        prev_img_names = img_names
        prev_model = model

    all_xyz = np.vstack(all_xyz)
    all_rgb = np.vstack(all_rgb)
    all_track_lens = np.concatenate(all_track_lens)
    
    print("\n" + "="*50)
    print(f"FUSED RECONSTRUCTION SUMMARY:")
    print(f"Total Unified Registered Cameras: {len(all_cam_list)}")
    print(f"Total Unified 3D Points: {len(all_xyz):,}")
    print(f"Point Cloud X Bounds: [{all_xyz[:, 0].min():.2f}, {all_xyz[:, 0].max():.2f}]")
    print(f"Point Cloud Y Bounds: [{all_xyz[:, 1].min():.2f}, {all_xyz[:, 1].max():.2f}]")
    print(f"Point Cloud Z Bounds: [{all_xyz[:, 2].min():.2f}, {all_xyz[:, 2].max():.2f}]")
    print("="*50)

if __name__ == "__main__":
    run_fusion_test()

