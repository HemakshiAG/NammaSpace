import sys
import time
from pathlib import Path
import sqlite3
import pycolmap
import numpy as np

def main():
    db_path = Path("uploads/test_vid2_run/colmap_workspace/test_single_cam.db")
    img_dir = Path("uploads/test_vid2_run/frames")
    pairs_path = Path("uploads/test_vid2_run/colmap_workspace/pairs_extended.txt")
    sparse_out = Path("uploads/test_vid2_run/colmap_workspace/sparse_extended")
    
    # 1. Fetch images sorted by numerical name
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM images ORDER BY name")
    img_names = [row[0] for row in c.fetchall()]
    conn.close()
    
    N = len(img_names)
    print(f"Total frames in DB: {N}")
    
    # 2. Generate comprehensive pair graph:
    # - Consecutive window: t +- 1..25
    # - Loop closure jumps: t +- 35, 50, 75, 100, 150, 200, 250, 300, 350
    pairs = set()
    for i in range(N):
        # Local window
        for offset in range(1, 26):
            if i + offset < N:
                pairs.add((img_names[i], img_names[i + offset]))
        # Loop closure across room
        for jump in [35, 50, 75, 100, 150, 200, 250, 300, 350]:
            if i + jump < N:
                pairs.add((img_names[i], img_names[i + jump]))
                
    print(f"Generated {len(pairs)} chronological and loop-closure pairs.")
    with open(pairs_path, "w") as f:
        for p1, p2 in sorted(pairs):
            f.write(f"{p1} {p2}\n")
            
    # 3. Match pairs
    print("Matching image pairs...")
    pair_opts = pycolmap.ImportedPairingOptions()
    pair_opts.match_list_path = pairs_path
    
    match_opts = pycolmap.FeatureMatchingOptions()
    match_opts.sift.max_ratio = 0.85
    
    verify_opts = pycolmap.TwoViewGeometryOptions()
    verify_opts.min_num_inliers = 10
    
    t0 = time.time()
    pycolmap.match_image_pairs(
        database_path=db_path,
        matching_options=match_opts,
        pairing_options=pair_opts,
        verification_options=verify_opts
    )
    print(f"Matching finished in {time.time()-t0:.1f}s.")
    
    # 4. Incremental Mapping
    print("Running incremental mapping...")
    sparse_out.mkdir(parents=True, exist_ok=True)
    pipe_opts = pycolmap.IncrementalPipelineOptions()
    pipe_opts.min_num_matches = 10
    pipe_opts.mapper.abs_pose_min_num_inliers = 12
    pipe_opts.mapper.abs_pose_min_inlier_ratio = 0.10
    pipe_opts.mapper.init_min_num_inliers = 30
    pipe_opts.mapper.init_min_tri_angle = 3.0
    pipe_opts.mapper.filter_min_tri_angle = 1.0
    pipe_opts.triangulation.min_angle = 1.0
    pipe_opts.triangulation.ignore_two_view_tracks = False
    
    t1 = time.time()
    maps = pycolmap.incremental_mapping(
        database_path=db_path,
        image_path=img_dir,
        output_path=sparse_out,
        options=pipe_opts
    )
    print(f"Mapping finished in {time.time()-t1:.1f}s.")
    print(f"Resulting models: {len(maps)}")
    for k, v in maps.items():
        print(f"Model {k}: {len(v.images)} images, {len(v.points3D)} 3D points")

if __name__ == "__main__":
    main()
