EXAMPLE: Pachyderm's Beginner Tutorial with Knitfab
================================================

In this document, we introduce an example of reproducing tasks equivalent to those in [Pachyderm](https://www.pachyderm.com/)'s Beginner Tutorial using Knitfab.

## What is Pachyderm?

Pachyderm is a data science platform characterized by data-driven pipelines and data versioning.

It supports container image-based data science tasks and parallelization of data science workflows through data partitioning.

Reference: https://docs.pachyderm.com/products/mldm/latest/learn/

### Comparison with Knitfab

Both Knitfab and Pachyderm are data-driven task pipeline systems.
These systems are designed under the paradigm of monitoring data generation and triggering container image-based tasks when new data is created. By running machine learning tasks as part of these pipelines, machine learning workflows can be automated.

**Pachyderm** employs a data management approach where each *pipeline* definition is associated with a *repository* that stores the output data of the tasks (*Job*s).
Repositories are versioned, and each time a pipeline's Job runs, its output is recorded as a new commit on a specific branch of the repository. Repositories can also support multiple branches.
Pipelines are triggered by commits to specific branches in input repositories. When triggered, the defined container image is executed as a Job, which processes input data. The entire repository or just a subset of it can be used as input data. Additionally, multiple repositories can be combined to create a single input.
Once a Job completes and a new commit is registered in the repository, other pipelines referencing that repository can generate new Jobs based on the updated data.

In Pachyderm, workflows are built by having pipelines reference other repositories as inputs.

On the other hand, **Knitfab** represents *Data* as the output of executed tasks (*Run*s). Data is not versioned but can have metadata (*Tag*s) that describe its properties.
Task definitions (*Plan*s) can be specified the conditions for input Data using a set of Tags and declared Tags to be automatically applied to output Data.
Plans create Runs for each Data matching their input conditions, and these Runs execute tasks based on the Plan's definition.
When a Run completes and generates output Data, other Plans that can use this output as input similarly trigger new Runs.

In Knitfab, machine learning workflows are expressed as a chain reaction of Runs triggered by Data generation.

## Reproduction Experiment: Pachyderm's Beginner Tutorial

### Step1. Overview

The [Pachyderm's Begginer Tutorial](https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/) demonstrates a workflow for extracting contours from videos and images and generating HTML files that compare the original images with their contour images.

This tutorial defines the following pipelines:

- Video Converter Pipeline: Converts videos to MP4 format
- Image Flattener Pipeline: Extracts frames from videos as images
- Image Tracing Pipeline: Extracts contours from each image
- Gif Pipeline: Creates GIFs from video frames and their corresponding contour images
- Content Shuffler Pipeline: Sorts contour images, contour GIFs, and their original counterparts
- Content Collager Pipeline: Generates HTML files for comparison

To replicate this tutorial using Knitfab, each of these pipelines will be mapped to a corresponding Plan. However, due to differences between Knitfab and Pachyderm features, some parts did not have a one-to-one correspondence. These gaps were addressed by defining additional Plans to supplement functionality.

### Step 2. Preparing the Knitfab Project

First, create a directory for this tutorial.

```
mkdir -p pachyderm-beginner-tutorial
cd pachyderm-beginner-tutorial
```

Next, initialize the directory as a working directory for Knitfab using the `knit init` command.

```
knit init PATH/TO/handout/knitprofile
```

Then, define a common project tag for the tutorial in a `knitenv` file.

```yaml:knitenv
tag:
    - "project:pachyderm-beginner-tutorial"
```

With this setup, subsequent `knit data push` and `knit plan template` commands will automatically include the `project:pachyderm-beginner-tutorial` Tag.

### Step3. Collect and Upload Data

Download the files used in the tutorial.

```
mkdir ./raw_videos_and_images
wget -O ./raw_videos_and_images/liberty.jpg https://raw.githubusercontent.com/pachyderm/docs-content/main/images/opencv/liberty.jpg
wget -O ./raw_videos_and_images/cat-sleeping.mov https://storage.googleapis.com/docs-tutorial-resoruces/cat-sleeping.MOV
wget -O ./raw_videos_and_images/robot.jpg https://raw.githubusercontent.com/pachyderm/docs-content/main/images/opencv/robot.jpg
wget -O ./raw_videos_and_images/highway.mov https://storage.googleapis.com/docs-tutorial-resoruces/highway.MOV
```

After downloading, upload the `./raw_videos_and_images` folder as a Data object in Knitfab.

```
knit data push -t format:mixed -t type:raw-dataset -n ./raw_videos_and_images/
```

Upon execution, the following output was obtained in the console:

```
[knit data push] 2024/11/29 14:05:29 [[1/1]] sending... ./raw_videos_and_images/
22.12 MiB / 22.12 MiB [-------------------------------------] 100.00% 6.29 MiB p/s
[knit data push] 2024/11/29 14:05:32 registered: ./raw_videos_and_images/ -> knit#id:50bcbd12-2524-410d-bb46-d43b5e602111
[knit data push] 2024/11/29 14:05:32 tagging...
[knit data push] 2024/11/29 14:05:33 [[1/1]] [OK] done: ./raw_videos_and_images/ -> knit#id:50bcbd12-2524-410d-bb46-d43b5e602111
{
    "knitId": "50bcbd12-2524-410d-bb46-d43b5e602111",
    "tags": [
        "format:mixed",
        "knit#id:50bcbd12-2524-410d-bb46-d43b5e602111",
        "knit#timestamp:2024-11-29T05:05:34.804+00:00",
        "name:raw_videos_and_images",
        "project:pachyderm-beginner-tutorial",
        "type:raw-dataset"
    ],
    "upstream": {
        "mountpoint": {
            "path": "/upload",
            "tags": []
        },
        "run": {
            "runId": "ab1f52fd-c7fb-4f81-8c1a-61adc9c5b88d",
            "status": "done",
            "updatedAt": "2024-11-29T05:05:34.804+00:00",
            "plan": {
                "planId": "088172e7-aac6-442d-8866-ea232ab04fc6",
                "name": "knit#uploaded"
            }
        }
    },
    "downstreams": [],
    "nomination": []
}
```

### Step 4. Building the Pipelines
。
In Knitfab, constructing a workflow essentially involves defining Plans. Each pipeline in Pachyderm's tutorial will be mapped to a corresponding Plan in Knitfab.

Since Pachyderm provides publicly available container images for the tutorial, these same images will be used in the Knitfab Plans as well.

After defining each Plan, you can register it with Knitfab by executing the following command for each Plan definition file:

```
knit plan apply ${plan-definition-yaml-file}
```

#### Video Converter Pipeline

First, define a Plan to perform the task of converting video formats in the dataset to mp4.

```yaml:video_converter.plan.yaml
annotations:
  - "based-on=https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/3/#create-pipelines-video-converter-pipeline"

image: "lbliii/video_mp4_converter:1.0.14"

entrypoint: []
args:
  - python3
  - /video_mp4_converter.py
  - --input
  - /pfs/raw_videos_and_images/
  - --output
  - /pfs/out/

inputs:
  - path: "/pfs/raw_videos_and_images/"
    tags:
      - "type:raw-dataset"
      - "name:raw_videos_and_images"
      - "project:pachyderm-beginner-tutorial"

outputs:
  - path: "/pfs/out/"
    tags:
      - "type:dataset"
      - "content:movies"
      - "format:mp4"
      - "project:pachyderm-beginner-tutorial"
      - "name:video_mp4_converter"

log:
  tags:
    - "type:log"
    - "project:pachyderm-beginner-tutorial"

active: true

resouces:
  cpu: 1
  memory: 1Gi

```

The `args` follow those specified in the Pachyderm Beginner Tutorial pipeline.

Additionally, `inputs` and `outputs` are provided to correspond to the Pachyderm definitions.

- `inputs`: In Knitfab, tags are specified so that the previously uploaded data can be referenced.
- `outputs`: Tags are used to indicate the nature of the data, and the `name` tag simulates a repository in Pachyderm.

#### Image Flattener Pipeline

This task involves extracting frames from mp4 videos and saving them as jpeg images.

Following a similar approach to the previous example, the following Plan definition is created:

```yaml:image_flattener.plan.yaml
annotations:
  - "based-on=https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/3/#create-pipelines-image-flattener-pipeline"

image: "lbliii/image_flattener:1.0.0"

entrypoint: []
args:
  - python3
  - /image_flattener.py
  - --input
  - /pfs/video_mp4_converter
  - --output
  - /pfs/out/

inputs:
  - path: "/pfs/video_mp4_converter/"
    tags:
      - "type:dataset"
      - "content:movies"
      - "format:mp4"
      - "project:pachyderm-beginner-tutorial"
      - "name:video_mp4_converter"

outputs:
  - path: "/pfs/out/"
    tags:
      - "type:dataset"
      - "content:images"
      - "format:jpeg"
      - "project:pachyderm-beginner-tutorial"
      - "name:image_flattener"

log:
  tags:
    - "type:log"
    - "project:pachyderm-beginner-tutorial"

active: true

resouces:
  cpu: 1
  memory: 1Gi

```

#### Image Tracing Pipeline

This pipeline performs the task of extracting contour images from image files, which are taken from multiple repositories in Pachyderm. It collects the image files as a single input and processes them to extract contours.
While Knitfab does not have a feature to combine multiple data sources into a single input, it does support the ability to handle multiple inputs. The missing part is the ability to "extract only image files." Therefore, we will create a Plan to address this issue.

Next, we will define the core Plan of the pipeline, which corresponds to the main processing logic in Pachyderm.

##### Image Extraction Plan

To create a custom image extraction Plan, we first need to set up a working directory for it.

```
mkdir -p ./image_extracter
cd ./image_extracter
```

The first step is to write a program that extracts images from the specified folder and copies them to another folder.

```python:image_extracter.py
import argparse
import os
import pathlib
import shutil

parser = argparse.ArgumentParser(
    description="extract images from specified directories"
)

parser.add_argument(
    "-i",
    "--input",
    type=pathlib.Path,
    required=True,
    help="directories to extract images from",
)

parser.add_argument(
    "-o",
    "--output",
    type=pathlib.Path,
    required=True,
    help="directory to store the extracted images",
)

args = parser.parse_args()

# Create the output directory if it doesn't exist
output_dir = args.output
os.makedirs(output_dir, exist_ok=True)

input_dir = args.input

# allows only image file extensions
allowed_extensions = (".png", ".jpg", ".jpeg")

# Loop through input directories and copy files to the output directory
for filename in os.listdir(input_dir):
    file_path = os.path.join(input_dir, filename)
    if os.path.isfile(file_path) and filename.lower().endswith(allowed_extensions):
        shutil.copy(file_path, output_dir)

print(f"All files merged into {output_dir}")
```

The following Dockerfile corresponds to the container image that will execute the image extraction program:

```Dockerfile
FROM python:3.12.7-slim

WORKDIR /work
COPY . .

ENTRYPOINT ["python", "image_extracter.py"]
CMD ["--input", "/in/mix", "--output", "/out/images"]
```

After writing the Dockerfile, you can build, tag, and push the image as follows:

```
cd ../
docker build -t image_extracter:1.0 ./image_extracter/
docker tag "${REPOSITORY}/image_extracter:1.0" image_extracter:1.0
docker push ${REPOSITORY}/image_extracter:1.0
```

Next, create the Plan definition to use this image and extract only the image files from the previously uploaded data.

```yaml:image_extracter.plan.yaml
image: "975050250135.dkr.ecr.ap-northeast-1.amazonaws.com/image_extracter:1.0"
entrypoint: ["python", "image_extracter.py"]

args: ["--input", "/in/mix", "--output", "/out/images"]

inputs:
  - path: "/in/mix"
    tags:
      - "project:pachyderm-beginner-tutorial"
      - "format:mixed"
      - "type:raw-dataset"

outputs:
  - path: "/out/images"
    tags:
      - "project:pachyderm-beginner-tutorial"
      - "type:images"
      - "name:image_extracter"

log:
  tags:
    - "type:log"
    - "project:pachyderm-beginner-tutorial"

active: true

resouces:
  cpu: 1
  memory: 1Gi
```

##### Main Pipeline

The Plan to extract contours from images will be defined here. The inputs for this task will be the dataset containing only the extracted images (created earlier) and the dataset containing the frames extracted from the videos.

The following Plan definition is created to perform the contour extraction:

```yaml:image_tracer.plan.yaml
annotations:
  - "based-on=https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/3/#create-pipelines-image-tracing-pipeline"

image: "lbliii/image_tracer:1.0.8"

entrypoint: []
args:
  - python3
  - /image_tracer.py
  - --input
  - /pfs/raw_videos_and_images
  - /pfs/image_flattener
  - --output
  - /pfs/out/

inputs:
  - path: "/pfs/raw_videos_and_images/"
    tags:
      - "type:images"
      - "name:image_extracter"
      - "project:pachyderm-beginner-tutorial"
  - path: "/pfs/image_flattener/"
    tags:
      - "name:image_flattener"
      - "project:pachyderm-beginner-tutorial"

outputs:
  - path: "/pfs/out/"
    tags:
      - "project:pachyderm-beginner-tutorial"
      - "name:image_tracer"

log:
  tags:
    - "type:log"
    - "project:pachyderm-beginner-tutorial"

active: true

resouces:
  cpu: 1
  memory: 1Gi
```

#### Gif Pipeline

This pipeline defines the task of converting a set of image files in a directory into a gif video.
The inputs are a set of video frame images and a set of contour images.

The following Plan definition is created for this task:

```yaml:gif.plan.yaml
annotations:
  - "based-on=https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/3/#create-pipelines-gif-pipeline"

image: "lbliii/movie_gifer:1.0.5"

entrypoint: []
args:
  - python3
  - /movie_gifer.py
  - --input
  - /pfs/image_flattener
  - /pfs/image_tracer
  - --output
  - /pfs/out/

inputs:
  - path: "/pfs/image_flattener/"
    tags:
      - "name:image_flattener"
      - "project:pachyderm-beginner-tutorial"
  - path: "/pfs/image_tracer/"
    tags:
      - "name:image_tracer"
      - "project:pachyderm-beginner-tutorial"

outputs:
  - path: "/pfs/out/"
    tags:
      - "project:pachyderm-beginner-tutorial"
      - "name:movie_gifer"

log:
  tags:
    - "type:log"
    - "project:pachyderm-beginner-tutorial"

active: true

resouces:
  cpu: 1
  memory: 5Gi
```
This task requires more memory, so note that `resources.memory` is increased.

#### Content Shuffler Pipeline

This pipeline defines a task that sorts images and videos into contour versions and original versions based on the naming convention of the file names.
However, files that contain extracted frames from videos will be ignored.

Create following Plan definition:

```yaml:content_shuffler.plan.yaml
annotations:
  - "based-on=https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/3/#create-pipelines-content-shuffler-pipeline"

image: "lbliii/content_shuffler:1.0.0"

entrypoint: []
args:
  - python3
  - /content_shuffler.py
  - --input
  - /pfs/movie_gifer
  - /pfs/raw_videos_and_images
  - /pfs/image_tracer
  - --output
  - /pfs/out/

inputs:
  - path: "/pfs/movie_gifer/"
    tags:
      - "name:movie_gifer"
      - "project:pachyderm-beginner-tutorial"
  - path: "/pfs/raw_videos_and_images/"
    tags:
      - "name:image_extracter"
      - "project:pachyderm-beginner-tutorial"
  - path: "/pfs/image_tracer/"
    tags:
      - "name:image_tracer"
      - "project:pachyderm-beginner-tutorial"

outputs:
  - path: "/pfs/out/"
    tags:
      - "project:pachyderm-beginner-tutorial"
      - "name:content_shuffler"

log:
  tags:
    - "type:log"
    - "project:pachyderm-beginner-tutorial"

active: true

resouces:
  cpu: 1
  memory: 1Gi
```

#### Content Collager Pipeline

This pipeline defines a task that generates a comparison viewer in HTML file format using the results from the Image Shuffler.

Create following Plan definition:

```yaml:content_collager.plan.yaml
annotations:
  - "based-on=https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/3/#create-pipelines-content-collager-pipeline"

image: "lbliii/content_collager:1.0.64"

entrypoint: []
args:
  - python3
  - /content_collager.py
  - --input
  - /pfs/content_shuffler
  - --output
  - /pfs/out/

inputs:
  - path: "/pfs/content_shuffler/"
    tags:
      - "name:content_shuffler"
      - "project:pachyderm-beginner-tutorial"

outputs:
  - path: "/pfs/out/"
    tags:
      - "project:pachyderm-beginner-tutorial"
      - "name:content_collager"

log:
  tags:
    - "type:log"
    - "project:pachyderm-beginner-tutorial"

active: true

resouces:
  cpu: 1
  memory: 1Gi
```

### Step 4. Check the Results

Download thethe final output, `content_collager`, and verify its contents.

First, identify the Run of the Plan corresponding to the Content Collage Pipeline and check the Knit ID of its output.

```
knit run find -p ${Plan ID of Content Collage Pipeline}
```

> [!TIP]
>
> You can find the Plan ID corresponding to the Content Collage Pipeline using the following command:
>
> ```
> knit plan find --image lbliii/content_collager:1.0.64 | jq '.[].planId'
> ```
>
> `knit plan find` is a command used to search for Plans registered in Knitfab.
> The `--image` flag filters based on the container image specified in the Plan.
>
> The result is then passed to [jq](https://jqlang.github.io/jq/) to extract the planId key.

You should see console output similar to the following:

```json
[
    {
        "runId": "068f8f2e-234c-4b24-ad0a-e5e844fe4e76",
        "status": "done",
        "updatedAt": "2024-11-29T09:33:48.058+00:00",
        "exit": {
            "code": 0,
            "message": ""
        },
        "plan": {
            "planId": "0ee77ac0-98bc-4f66-9baf-d02e3e38a368",
            "image": "lbliii/content_collager:1.0.64",
            "args": [
                "python3",
                "/content_collager.py",
                "--input",
                "/pfs/content_shuffler",
                "--output",
                "/pfs/out/"
            ],
            "annotations": [
                "based-on=https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/3/#create-pipelines-content-collager-pipeline"
            ]
        },
        "inputs": [
            {
                "path": "/pfs/content_shuffler",
                "tags": [
                    "name:content_shuffler",
                    "project:pachyderm-beginner-tutorial"
                ],
                "knitId": "c6b02405-d67e-4baa-9b3d-f80a88d2d8de"
            }
        ],
        "outputs": [
            {
                "path": "/pfs/out",
                "tags": [
                    "name:content_collager",
                    "project:pachyderm-beginner-tutorial"
                ],
                "knitId": "4ea5ccf8-91f7-4622-8964-e3ee40e3ccea"
            }
        ],
        "log": {
            "tags": [
                "project:pachyderm-beginner-tutorial",
                "type:log"
            ],
            "knitId": "fa7d3cba-15a1-485f-8171-7af3b77453cc"
        }
    }
]
```

`.outputs` がこの Run の出力ですから、その Knit ID を指定して `knit data pull` すればよいです。
The `.outputs` is the output of this Run, so by specifying its Knit ID, you can use knit data pull to download it.

```
knit data pull -x 4ea5ccf8-91f7-4622-8964-e3ee40e3ccea ./outputs/content_collager
```

This will create a directory named `./outputs/content_collager/4ea5ccf8-91f7-4622-8964-e3ee40e3ccea`, and the data will be downloaded into it.

Inside this directory, you will find a file named `index.html`. Opening this file in a browser will allow you to check the results.

### Step 5. Inspect the Created Resources

Now, let's check the workflow and the lineage graph created so far.

#### View the Workflow in a Plan Graph

We will examine the Plan Graph, which shows the connections between Plans, starting from the last Plan corresponding to the Content Collage Pipeline.

```
knit plan graph -n all ${Plan ID of Content Collage Pipeline} | dot -T png > plan-graph.png
```

You should see a Plan Graph image similar to this:

![](./images/plan-graph.png)

This image illustrates the relationships between Plans, showing the expected data flow based on which Plan’s output can be used by others. The pipeline is built with Plans reacting to each other in a chain, following the direction of the arrows.

When comparing this with the diagram shown in the [Pachyderm Beginner Tutorial's Overview](https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/0/#overview-part-1-beginner-overview), you will notice that Plan Graph has same structure with the diagram, except:

- An additional Plan `image_extracter` exists.
- There is no repository corresponding to the raw data, "raw_videos_and_images."

> [!NOTE]
>
> The repository for the image_extracter is masked because it uses a custom image.

#### View Data Lineage

Next, we will examine the Data Lineage Graph to confirm the history of the generated data.

```
knit data lineage -n all ${content_collager output Knit ID} | dot -T png > lineage-graph.png
```

You should see a Lineage Graph similar to the following:


![](./images/lineage-graph.png)

This diagram shows the relationships between which Data (green boxes) was output by which Run (yellow boxes) and which Run the Data was input to. The direction of the arrows represents the data flow.

When comparing this with the diagram shown in the [Pachyderm Beginner Tutorial の Overview](https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/0/#overview-part-1-beginner-overview), you will notice:

- There is a Run for the additional Plan `image_extracter`.
- The logs of each run (`(log)`) are also recorded as data.

Apart from these differences, the structure is the same.

## Summary

By using Knitfab, we were able to replicate tasks equivalent to those in the [Pachyderm](https://www.pachyderm.com/) [Beginner Tutorial](https://docs.pachyderm.com/products/mldm/latest/get-started/beginner-tutorial/) .

While additional Plans were needed for filtering Data, we confirmed that by defining Plans corresponding to the Pachyderm pipeline, we could build an equivalent workflow.

Furthermore, the expressiveness of workflows supported by Knitfab includes:

- General workflows, not limited to machine learning
- Complex workflows involving branching and merging
- Workflows that reuse Data generated in previous runs across multiple Runs

Additionally, by visualizing the overall workflow (Plan Graph) and Data Lineage, we were able to easily gain an overview of the tasks at hand.
