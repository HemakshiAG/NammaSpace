import numpy as np
from scipy.spatial import cKDTree
from pathlib import Path

def test_gaussian_synthesis():
    # Test importing test_fusion to get fused data
    import sys
    sys.path.insert(0, str(Path("scratch").resolve()))
    import test_fusion
    
    base_dir = Path("uploads/test_vid2_run/colmap_workspace/sparse_tuned")
    seq_ids = [1, 7, 3, 10, 9, 2, 5, 4]
    
    import pycolmap
    models = {sid: pycolmap.Reconstruction(base_dir / str(sid)) for sid in seq_ids if (base_dir / str(sid)).exists()}
    
    all_cam_list = []
    all_xyz = []
    all_rgb = []
    all_track_lens = []
    
    prev_model = None
    prev_end_cam_world = None
    prev_end_rot_world = None
    prev_velocity_world = None
    
    for sid in seq_ids:
        model = models[sid]
        sorted_imgs = sorted(model.images.values(), key=lambda im: im.name)
        img_names = [im.name for im in sorted_imgs]
        
        local_cams = []
        local_rots = []
        for img in sorted_imgs:
            cfw = img.cam_from_world() if callable(img.cam_from_world) else img.cam_from_world
            rot = cfw.rotation() if callable(cfw.rotation) else cfw.rotation
            R_cam_from_w = rot.matrix()
            t_cam_from_w = cfw.translation
            R_w_from_cam = R_cam_from_w.T
            C_local = -R_cam_from_w.T @ t_cam_from_w
            local_cams.append(C_local)
            local_rots.append(R_w_from_cam)
            
        local_cams = np.array(local_cams, dtype=np.float64)
        if len(local_cams) > 1:
            step_vectors = np.diff(local_cams, axis=0)
            step_dists = np.linalg.norm(step_vectors, axis=1)
            median_step = float(np.median(step_dists)) if len(step_dists) > 0 else 0.05
            local_vel = np.mean(step_vectors[-3:], axis=0) if len(step_vectors) >= 3 else step_vectors[-1]
        else:
            median_step = 0.05
            local_vel = np.array([0, 0, 0.05])
            
        if prev_model is not None:
            local_scale = median_step if median_step > 1e-4 else 0.05
            target_scale = prev_median_step_world
            s_rel = target_scale / local_scale
            start_rot_local = local_rots[0]
            R_trans = prev_end_rot_world @ start_rot_local.T
            
            prev_frame_num = int(prev_img_names[-1].replace("frame_", "").replace(".jpg", ""))
            curr_frame_num = int(img_names[0].replace("frame_", "").replace(".jpg", ""))
            delta_frames = max(1, curr_frame_num - prev_frame_num)
            
            start_cam_world = prev_end_cam_world + prev_velocity_world * delta_frames
            t_trans = start_cam_world - s_rel * (R_trans @ local_cams[0])
            model_s, model_R, model_t = s_rel, R_trans, t_trans
        else:
            model_s, model_R, model_t = 1.0, np.eye(3, dtype=np.float64), np.zeros(3, dtype=np.float64)
            
        for i, img in enumerate(sorted_imgs):
            pos_world = model_s * (model_R @ local_cams[i]) + model_t
            rot_world = model_R @ local_rots[i]
            forward = rot_world @ np.array([0, 0, 1.0])
            up = rot_world @ np.array([0, -1.0, 0])
            all_cam_list.append({
                "name": img.name,
                "pos": [float(pos_world[0]), float(pos_world[1]), float(pos_world[2])],
                "forward": [float(forward[0]), float(forward[1]), float(forward[2])],
                "up": [float(up[0]), float(up[1]), float(up[2])],
            })
            
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
            m_xyz_world = model_s * (m_xyz @ model_R.T) + model_t
            all_xyz.append(m_xyz_world)
            all_rgb.append(m_rgb)
            all_track_lens.append(m_tracks)
            
        last_cam_local = local_cams[-1]
        prev_end_cam_world = model_s * (model_R @ last_cam_local) + model_t
        prev_end_rot_world = model_R @ local_rots[-1]
        prev_velocity_world = model_s * (model_R @ local_vel)
        prev_median_step_world = model_s * median_step
        prev_img_names = img_names
        prev_model = model

    xyz = np.vstack(all_xyz).astype(np.float32)
    rgb = np.vstack(all_rgb)
    track_lens = np.concatenate(all_track_lens)
    
    # Floater purge
    tree = cKDTree(xyz)
    dists, indices = tree.query(xyz, k=4)
    nn_dist = dists[:, 1]
    median_dist = float(np.median(nn_dist))
    keep = nn_dist <= (median_dist * 4.0)
    
    xyz = xyz[keep]
    rgb = rgb[keep]
    dists = dists[keep]
    track_lens = track_lens[keep]
    N_clean = len(xyz)
    print(f"Clean points after floater purge: {N_clean:,} (retained {N_clean/len(keep)*100:.1f}%)")
    
    avg_neighbor_dist = np.mean(dists[:, 1:4], axis=1).astype(np.float32)
    s_xy = np.clip(avg_neighbor_dist * 1.25, 0.005, 0.5)
    s_z = s_xy * 0.25
    scales = np.stack([s_xy, s_xy, s_z], axis=1)
    
    quaternions = np.zeros((N_clean, 4), dtype=np.uint8)
    quaternions[:, 0] = 128
    quaternions[:, 1] = 128
    quaternions[:, 2] = 128
    quaternions[:, 3] = 255
    
    alpha = np.clip(160 + track_lens * 20, 180, 255).astype(np.uint8)
    rgba = np.column_stack([rgb, alpha])
    
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
    
    splat_test_path = Path("scratch/test_scene.splat")
    with open(splat_test_path, "wb") as f:
        f.write(buf.tobytes())
        
    print(f"Test .splat written: {splat_test_path.stat().st_size:,} bytes")

if __name__ == "__main__":
    test_gaussian_synthesis()

