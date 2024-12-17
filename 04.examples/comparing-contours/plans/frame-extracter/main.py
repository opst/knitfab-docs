from argparse import ArgumentParser
import os
import pathlib
import shutil

import cv2


def extract_frames(video_path: pathlib.Path, output_dir: pathlib.Path):
    orig_name = video_path.stem
    if not video_path.exists():
        raise FileNotFoundError(f"video file {video_path} not found")

    cap = cv2.VideoCapture(str(video_path))
    frame_count = 0
    print(f"Extracting frames from {video_path}")
    while True:
        print(f"...frame #{frame_count}")
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imwrite(
            str(output_dir / f"{orig_name}_frame_{frame_count:010d}.jpg"), frame
        )
        frame_count += 1

    cap.release()


def main(input_dir: pathlib.Path, output_dir: pathlib.Path):
    if not input_dir.exists:
        raise FileNotFoundError(f"input file {input_dir} not found")

    for d, _, files in os.walk(input_dir):
        dirpath = pathlib.Path(d)
        relpath = dirpath.relative_to(input_dir)
        outpath = output_dir / relpath
        os.makedirs(outpath, exist_ok=True)

        for file in files:
            source = dirpath / file
            print(f"Processing {source}")
            if source.name.lower().endswith(".mp4"):
                os.makedirs(outpath / source.stem, exist_ok=True)
                extract_frames(source, outpath / source.stem)
            else:
                shutil.copy(dirpath / file, outpath / file)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)

    args = parser.parse_args()
    main(input_dir=args.input, output_dir=args.output)
