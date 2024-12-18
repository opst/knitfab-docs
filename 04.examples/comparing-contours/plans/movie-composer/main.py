from argparse import ArgumentParser
import os
import pathlib
import shutil

import cv2
import imageio.v2 as imageio


def compose_gif(frames: list[pathlib.Path], dest: pathlib.Path):
    f = [cv2.imread(str(source))[:, :, ::-1] for source in frames]  # BGR -> RGB
    imageio.mimsave(dest, f, duration=0.1)


def main(input_dir: pathlib.Path, output_dir: pathlib.Path):
    if not input_dir.exists:
        raise FileNotFoundError(f"input file {input_dir} not found")

    for d, _, files in os.walk(input_dir):
        dirpath = pathlib.Path(d)
        relpath = dirpath.relative_to(input_dir)
        outpath = output_dir / relpath
        os.makedirs(outpath, exist_ok=True)

        frames = {}

        for file in files:
            if "_frame_" in file:
                orig_name, *_ = file.split("_frame_")
                frames.setdefault(orig_name, []).append(file)
            else:
                shutil.copy(dirpath / file, outpath / file)

        for orig_name, frame_files in frames.items():
            frame_files.sort()  # Ensure the frames are in order
            print(f"Processing {dirpath / orig_name}")
            compose_gif(
                [dirpath / f for f in frame_files], outpath / f"{orig_name}.gif"
            )


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)

    args = parser.parse_args()
    main(input_dir=args.input, output_dir=args.output)
