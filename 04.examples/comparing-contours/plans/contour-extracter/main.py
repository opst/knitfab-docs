from argparse import ArgumentParser
import os
import pathlib
import shutil

import cv2


def extract_contour(imagefile_path: pathlib.Path, outputfile_path: pathlib.Path):
    img = cv2.imread(str(imagefile_path))
    edges = cv2.Canny(img, 100, 200)
    cv2.imwrite(str(outputfile_path), edges)


def main(input_dir: pathlib.Path, output_dir: pathlib.Path):
    if not input_dir.exists:
        raise FileNotFoundError(f"input file {input_dir} not found")

    for d, _, files in os.walk(input_dir):
        dirpath = pathlib.Path(d)
        relpath = dirpath.relative_to(input_dir)
        outpath_original = output_dir / "original" / relpath
        outpath_contour = output_dir / "contour" / relpath

        os.makedirs(outpath_original, exist_ok=True)
        os.makedirs(outpath_contour, exist_ok=True)

        for file in files:
            source = dirpath / file
            if not source.name.lower().endswith(".jpg"):
                continue

            print(f"Processing {source}")
            shutil.copy(source, outpath_original / file)
            extract_contour(source, outpath_contour / file)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)

    args = parser.parse_args()
    main(input_dir=args.input, output_dir=args.output)
