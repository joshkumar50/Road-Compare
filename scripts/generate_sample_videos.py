import cv2
import numpy as np
import os


def write_video(path: str, frames: list):
    h, w = frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, 10, (w, h))
    for f in frames:
        out.write(f)
    out.release()


def main():
    os.makedirs('sample_data', exist_ok=True)
    h, w = 360, 640
    base_frames = []
    present_frames = []
    for i in range(60):
        base = np.full((h, w, 3), 230, np.uint8)
        present = base.copy()
        # Draw a sign in base but remove later to simulate 'missing'
        if i < 40:
            cv2.rectangle(base, (200, 200), (260, 260), (50, 200, 50), 3)
        # Faded marking in present
        cv2.line(base, (100, 300), (540, 300), (255, 255, 255), 3)
        cv2.line(present, (100, 300), (540, 300), (150, 150, 150), 2)
        base_frames.append(base)
        present_frames.append(present)
    write_video('sample_data/base.mp4', base_frames)
    write_video('sample_data/present.mp4', present_frames)
    with open('sample_data/labels.csv', 'w') as f:
        f.write('id,element,issue_type,first_frame,last_frame\n')
        f.write('1,sign_board,missing,30,39\n')
        f.write('2,lane_marking,faded,0,59\n')
    print('Sample videos and labels written to sample_data/')


if __name__ == '__main__':
    main()





