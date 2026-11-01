import sqlite3

conn = sqlite3.connect('uploads/test_vid2_run/colmap_workspace/database_clean.db')
c = conn.cursor()
c.execute('''
    SELECT images.image_id, images.name, keypoints.rows 
    FROM keypoints 
    JOIN images ON keypoints.image_id = images.image_id 
    WHERE images.name >= 'frame_00068.jpg' AND images.name <= 'frame_00086.jpg' 
    ORDER BY images.name
''')
for r in c.fetchall():
    print(r)

