EXAMPLE: Image Processing Pipeline with Knitfab
================================================

This document introduces a case study of building an image processing pipeline using Knitfab.

Specifically, we will create a workflow to "extract contour lines from videos and images, and generate an HTML file comparing the original images with their contour line counterparts."

## Step 1. Overview

The process will proceed according to the following steps:

1. Overview
2. Setting up the environment
3. Collecting datasets and uploading them to Knitfab
4. Building the pipeline
5. Reviewing the results

## Step 2. Preparing a Knitfab Project

Before defining the plan, create a directory for this tutorial.

```
mkdir -p contour-compairing
cd contour-comparing
```

Next, set this directory as the working directory for Knitfab.

Run `knit init` to configure Knitfab for use in this directory.

```
knit init PATH/TO/handout/knitprofile
```

Additionally, write the common tags for the project in a `knitenv` file within this directory.

```yaml:knitenv
tag:
  - "project:comparing-contours"
```

This ensures that all subsequent `knit data push` and `knit plan template` commands will consistently set the tag `project:comparing-contours`

## Step 3. Uploading the Dataset

Collect the input dataset and upload it to Knitfab.

```
mkdir ./raw_videos_and_images
wget -O ./raw_videos_and_images/robot.jpg https://raw.githubusercontent.com/opst/knitfab-docs/main/04.examples/contour-comparing/dataset/raw_videos_and_images/robot.jpg
wget -O ./raw_videos_and_images/plant.jpg https://raw.githubusercontent.com/opst/knitfab-docs/main/04.examples/contour-comparing/dataset/raw_videos_and_images/plant.jpg
wget -O ./raw_videos_and_images/highway.mp4 https://raw.githubusercontent.com/opst/knitfab-docs/main/04.examples/contour-comparing/dataset/raw_videos_and_images/highway.mp4
wget -O ./raw_videos_and_images/sleeping-cat.mp4 https://raw.githubusercontent.com/opst/knitfab-docs/main/04.examples/contour-comparing/dataset/raw_videos_and_images/sleeping-cat.mp4
```

Then, upload the folder `./raw_videos_and_images` as Data to Knitfab.

```
knit data push -t format:mixed -t type:raw-dataset -t project:comparing-contours -n ./raw_videos_and_images/
```

## Step 4. Building the Pipeline

For Knitfab, "building a pipeline" means defining Plans.

In this project, the goal is to create a pipeline that takes a mixed dataset of images and videos as input and generates an HTML file comparing the originals with their contour-extracted versions. This involves determining the necessary tasks and defining the Plans for each task sequentially.

### Pipeline Outline

Before starting to build the pipeline, we outline its structure. This pipeline involves the following tasks:

1. Frame Extracter: A task to split videos in the dataset into frame images.
2. Contour Extracter: A task to extract contour lines from images.
3. Movie Composer: A task to recompose frame images into videos.
4. Collager: A task to generate a webpage for comparing original images (or videos) with their contour-line images (or videos).

By applying these tasks sequentially, the pipeline will transform a dataset containing videos and images into a Web page for comparison with contour-extracted visuals. To manage this, Plans will be defined for each task to construct the pipeline.

In Task 4, since original images/videos and contour-extracted visuals are treated as pairs, Tasks 2 and 3 also maintain these pairs within a single Data unit.

### Frame Extracter

This task extracts frames from MP4 videos in the Data as JPEG images.

Create a directory for this task:

```
mkdir -p plans/frame-extracter
```

Write the frame extraction program as `plans/frame-extracter/main.py`:

```python:plans/frame-extracter/main.py
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

```

The script copies files from the input (`--input`) directory to the output (`--output`) directory. For MP4 files, instead of copying them, it extracts each frame as a JPEG image named `${original_file_name}_frame_${frame_number}.jpg`, with the frame number zero-padded to 10 digits for proper sequential sorting.

Create a Dockerfile at `plans/frame-extracter/Dockerfile` to create an image:

```Dockerfile:plans/frame-extracter/Dockerfile
FROM python:3.12-bookworm

WORKDIR "/work"
COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "./main.py" ]
CMD ["--input", "/in", "--output", "/out"]

```

For the script to work well, make `plans/frame-extracter/requirements.txt` as below:

```plans/frame-extracter/requirements.txt
opencv-python-headless==4.11.0.86

```

Build, tag, and push the Docker image:

```sh
docker build -t frame-extracter:1.0 plans/frame-extracter
docker tag frame-extracter:1.0 ${REGISTRY}/frame-extracter:1.0
docker push ${REGISTRY}/frame-extracter:1.0
```

> [!NOTE]
>
> For reproduce this case study on your hand, replace ${REGISTRY} with your Docker registry host.

Define the Plan using this image:

```yaml:plans/frame-extracter/frame-extracter.plan.yaml
image: "${REGISTRY}/frame-extracter:1.0"

args:
  - --input
  - /in
  - --output
  - /out

inputs:
  - path: "/in"
    tags:
      - "format:mixed"
      - "type:raw-dataset"
      - "project:comparing-contours"

outputs:
  - path: "/out"
    tags:
      - "type:extracted-frames"
      - "format:jpeg"
      - "project:comparing-contours"

log:
  tags:
    - "type:log"
    - "project:comparing-contours"

active: true

resources:
  cpu: 1
  memory: 1Gi

```

> [!NOTE]
>
> If you use Image Registry built in Knitfab、replace `${REGISTRY}` in the Plan definition with `localhost:${PORT}`.
> (`${PORT}` is the port number of the Registry)

Register the Plan in Knitfab:

```sh
knit plan apply plans/frame-extracter/frame-extracter.plan.yaml
```

### Contour Extracter

This task extracts contour lines from images.

Create the working directory:

```sh
mkdir plans/contour-extracter
```

Write the script as `plans/contour-extracter/main.py`:

```python:plans/contour-extracter/main.py
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

```

The script creates `original` and `contour` subdirectories in the output, storing copies of original images in `original` and their contour-extracted versions in `contour`.

Create the Dockerfile at `plans/contour-extracter/Dockerfile`:

```Dockerfile:plans/contour-extracter/Dockerfile
FROM python:3.12-bookworm

COPY . .
RUN pip install -r requirements.txt

WORKDIR "/work"
ENTRYPOINT [ "python", "./main.py" ]
CMD ["--input", "/in", "--output", "/out"]

```

For the script to work well, make `plans/contour-extracter/requirements.txt` as below:

```plans/contour-extracter/requirements.txt
opencv-python-headless==4.11.0.86

```

Build, tag, and push the Docker image:

```sh
docker build -t contour-extracter:1.0 plans/contour-extracter
docker tag contour-extracter:1.0 ${REGISTRY}/contour-extracter:1.0
docker push ${REGISTRY}/contour-extracter:1.0
```

Define and register the Plan in Knitfab at `plans/contour-extracter/contour-extracter.plan.yaml`:

```yaml:plans/contour-extracter/contour-extracter.plan.yaml
image: "${REGISTRY}/contour-extracter:1.0"

args:
  - --input
  - /in
  - --output
  - /out

inputs:
  - path: "/in"
    tags:
      - "type:extracted-frames"
      - "format:jpeg"
      - "project:comparing-contours"

outputs:
  - path: "/out"
    tags:
      - "type:original-contour-pairs"
      - "format:jpeg"
      - "project:comparing-contours"

log:
  tags:
    - "type:log"
    - "project:comparing-contours"

active: true

resources:
  cpu: 1
  memory: 1Gi

```

Register the Plan in Knitfab.

```sh
knit plan apply plans/contour-extracter/contour-extracter.plan.yaml
```

### Movie Composer

This task reconstructs animations GIFs from frame images in the Data, identified by filenames containing `_frame_`. For other files, this task just copies them into output.

Create the working directory:

```sh
mkdir plans/movie-composer
```

Write the Python script at `plans/movie-composer/main.py`:

```python:plans/movie-composer/main.py
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

```

Create the Dockerfile at `plans/movie-composer/Dockerfile`:

```Dockerfile:plans/movie-composer/Dockerfile
FROM python:3.12-bookworm

WORKDIR "/work"
COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "./main.py" ]
CMD ["--input", "/in", "--output", "/out"]

```

For the script to work well, make `plans/contour-extracter/requirements.txt` as below:

```plans/contour-extracter/requirements.txt
opencv-python-headless==4.11.0.86
imageio==2.37.0

```

Build, tag, and push the image:

```sh
docker build -t movie-composer:1.0 plans/movie-composer
docker tag movie-composer:1.0 ${REGISTRY}/movie-composer:1.0
docker push ${REGISTRY}/movie-composer:1.0
```

Define the Plan using this image at `plans/movie-composer/movie-composer.plan.yaml`:

```yaml:plans/movie-composer/movie-composer.plan.yaml
image: "${REGISTRY}/movie-composer:1.0"

args:
  - --input
  - /in
  - --output
  - /out

inputs:
  - path: "/in"
    tags:
      - "type:original-contour-pairs"
      - "format:jpeg"
      - "project:comparing-contours"

outputs:
  - path: "/out"
    tags:
      - "type:recomposed-movie"
      - "format:mixed"
      - "project:comparing-contours"

log:
  tags:
    - "type:log"
    - "project:comparing-contours"

active: true

resources:
  cpu: 1
  memory: 5Gi

```

To generate movies, this Plan requires much memory.

Register the Plan in Knitfab.

```sh
knit plan apply plans/movie-composer/movie-composer.plan.yaml
```

### Collager

This task generates a webpage for comparing original and contour-extracted visuals.

Create the directory:

```sh
mkdir ./plans/collager
```

Write the Python script as `./plans/collager/main.py`:

```python:plans/collager/main.py
from argparse import ArgumentParser
import os
import pathlib
import shutil
import io

from bs4 import BeautifulSoup


html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Collager</title>
</head>
<body>
    <h1>Collager</h1>
    <table id="collage-container">
        <tr><th>Original</th><th>Contour</th></tr>
    </table>
</body>
</html>
"""


def main(input_dir: pathlib.Path, output_dir: pathlib.Path):
    if not input_dir.exists:
        raise FileNotFoundError(f"input file {input_dir} not found")
    orig_root = input_dir / "original"
    if not orig_root.exists:
        raise FileNotFoundError(f"input file {orig_root} not found")
    contour_root = input_dir / "contour"
    if not contour_root.exists:
        raise FileNotFoundError(f"input file {contour_root} not found")

    static = output_dir / "static"
    os.makedirs(static, exist_ok=True)

    orig_dest = static / "original"
    os.makedirs(orig_dest, exist_ok=True)
    contour_dest = static / "contour"
    os.makedirs(contour_dest, exist_ok=True)

    soup = BeautifulSoup(html_template, "html.parser")
    container = soup.find("table", id="collage-container")

    for d, _, files in os.walk(orig_root):
        dirpath = pathlib.Path(d)
        relpath = dirpath.relative_to(orig_root)

        for file in files:
            contour_file = contour_root / relpath / file
            if not contour_file.exists():
                print(f"Contour file not found for {file}")
                continue

            orig_file = orig_dest / relpath / file
            os.makedirs(orig_file.parent, exist_ok=True)
            print(f"Copying {dirpath / file} to {orig_file}")

            # animated gif cannot be copied with shutil.copy (not know why)
            with open(dirpath / file, "rb") as f:
                with open(orig_file, "xb") as f2:
                    f2.write(f.read())

            contour_file = contour_dest / relpath / file
            os.makedirs(contour_file.parent, exist_ok=True)
            print(f"Copying {contour_root / relpath / file} to {contour_file}")

            with open(contour_root / relpath / file, "rb") as f:
                with open(contour_file, "xb") as f2:
                    f2.write(f.read())

            row = soup.new_tag("tr")
            container.append(row)

            orig_cell = soup.new_tag("td")
            row.append(orig_cell)
            img_orig = soup.new_tag("img", src=str(orig_file.relative_to(output_dir)))
            orig_cell.append(img_orig)

            contour_cell = soup.new_tag("td")
            row.append(contour_cell)
            img_contour = soup.new_tag(
                "img", src=str(contour_file.relative_to(output_dir))
            )
            contour_cell.append(img_contour)

    with open(output_dir / "index.html", "w") as f:
        f.write(str(soup))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--input", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)

    args = parser.parse_args()
    main(input_dir=args.input, output_dir=args.output)

```

Create the Dockerfile at `./plans/collager/Dockerfile`:

```Dockerfile:plans/collager/Dockerfile
FROM python:3.12-bookworm

WORKDIR "/work"
COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "./main.py" ]
CMD ["--input", "/in", "--output", "/out"]

```

For the script to work well, make `plans/collager/requirements.txt` as below:

```plans/collager/requirements.txt
beautifulsoup4==4.13.3

```


Build, tag, and push the image:

```sh
docker build -t collager:1.0 plans/collager
docker tag collager:1.0 ${REGISTRY}/collager:1.0
docker push ${REGISTRY}/collager:1.0
```

Write the Plan Definition at `plans/collager/collager.plan.yaml`:

```yaml:plans/collager/collager.plan.yaml
image: "${REGISTRY}/collager:1.0"

args:
  - --input
  - /in
  - --output
  - /out

inputs:
  - path: "/in"
    tags:
      - "type:recomposed-movie"
      - "format:mixed"
      - "project:comparing-contours"

outputs:
  - path: "/out"
    tags:
      - "type:collage"
      - "format:web-site"
      - "project:comparing-contours"

log:
  tags:
    - "type:log"
    - "project:comparing-contours"

active: true

resources:
  cpu: 1
  memory: 1Gi

```

Register the Plan in Knitfab.

```sh
knit plan apply plans/collager/collager.plan.yaml
```

## Step 5. Confirming Results

### Output of the Pipeline

Verify the results generated by the pipeline,

To verify the results generated by the pipeline, search for the relevant Data tagged as follows:

- `format:web-site`
- `type:collage`
- `project:comparing-contours`

Run the following command:

```
knit data find -t "format:web-site" -t "type:collage" -t "project:comparing-contours"
```

Using the identified Knit ID, download the Data:

```
knit data pull -x ${Knit ID} ./out/collager
```

This saves the Data to `./out/collager/${Knit ID}`.

Within this folder, open index.html in a browser to see the webpage comparing original images (original) and their contour-extracted versions (contour), as shown below:

![](images/collager-screenshot.png)

### Verifying the Pipeline Structure

To visualize the structure of the entire pipeline, generate a Plan Graph:

```
knit plan graph -n all ${Plan ID of Collager Plan} | dot -Tpng > plan-graph.png
```

This will produce a Plan Graph like the one shown below, illustrating a pipeline composed of four interconnected Plans:

![](./images/plan-graph.png)

### Lineage

Finally, inspect the lineage graph created by the pipeline:

```
knit data linage -n all ${Knit ID of output of Collager}
```

The lineage graph mirrors the structure seen in the Plan Graph, detailing four Runs and their respective outputs.

![](./images/lineage-graph.png)

## Summary

- Using Knitfab, we successfully constructed a general-purpose task pipeline, not limited to machine learning.
- The pipeline processes data through a chain of multiple Plans, producing a cohesive output.

