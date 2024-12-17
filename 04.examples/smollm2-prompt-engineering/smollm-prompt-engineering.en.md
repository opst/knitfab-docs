EXAMPLE: Prompt Engneering with SmolLM2
==================================

This document demonstrates examples of prompt engineering using the small language model "SmolLM2".

> [!NOTE]
>
> It is highly recommended to use a GPU when reproducing the examples in this document. Running on a CPU is not practical.

## Step 1. Outline

This example investigates how prompt engineering impacts the performance of the SmolLM2-135M model.
The experiment uses [TriviaQA](https://nlp.cs.washington.edu/triviaqa/), a dataset of trivia quizzes in English, as the benchmark dataset.
For evaluation, the [HuggingFace/lighteval](https://github.com/huggingface/lighteval) tool is utilized.

The experiment will proceed as follows:

1. Outline
2. Environment setup
3. Create a plan for model evaluation
4. Prepare and evaluate multiple prompts
5. Compare the results

### What is SmolLM2?

[SmolLM2](https://github.com/huggingface/smollm) is a compact natural language model capable of solving diverse tasks. It is publicly available on HuggingFace and can be easily accessed.

In this example, we use SmolLM2-135M, the smallest model in the SmolLM2 series, to keep the experiment lightweight.

### Overview of the TriviaQA Dataset

You can view the contents of the TriviaQA dataset at https://huggingface.co/datasets/lighteval/trivia_qa.

TriviaQA is a dataset consisting of trivia quiz *questions*, corresponding correct *answers*, and their source information.
The correct answers are not sentences but rather (proper) nouns or a few words, with multiple options listed to account for variations in expression.

A language model answering TriviaQA is expected to output one of these correct answers.

## Step 2. Environment Setup

First, create a directory for this series of experiments:

```
mkdir smollm2-prompt-engineering
cd smollm2-prompt-engineering
```

Next, configure this directory as a Knitfab project directory.

Run `knit init` to set up Knitfab for use in this directory:

```
knit init PATH/TO/handout/knitprofile
```

Additionally, define common tags for the project in the `knitenv` file:

```
tag:
  - "project:smollm2-prompt-engineering"
```

This configuration ensures that subsequent commands like `knit data push` and `knit plan template` will always set `project:smollm2-prompt-engineering` as the default Tag.

## Step 3. Define the Evaluation Plan

Define a Plan to evaluate the language model SmolLM2-135M.

According to the [SmolLM2 のドキュメント](https://github.com/huggingface/smollm/blob/main/evaluation/README.md), the evaluation is conducted using [lighteval](https://github.com/huggingface/lighteval/). Therefore, this experiment will follow the same approach.Since this experiment focuses on the performance differences caused by varying prompts, the evaluation Plan to be created must be able to accept *any prompt as Data in a Knitfab manner*.

### Define the Container Image

Create a container image that runs lighteval.

To do that, create a working directory and a Dockerfile:

```
mkdir evaluator
touch evaluator/Dockerfile
```

Set the contents of the Dockerfile as follows:

```Dockerfile:evaluator/Dockerfile
FROM python:3.12.7-bookworm

WORKDIR "/work"
RUN git clone https://github.com/huggingface/smollm.git .
RUN pip install -r evaluation/requirements.txt
ENTRYPOINT ["lighteval", "accelerate", "--model_args", "pretrained=HuggingFaceTB/SmolLM2-135M,revision=main,dtype=float16,vllm,gpu_memory_utilisation=0.8,max_model_length=2048", "--save_details"]
CMD ["--custom_tasks", "/in/tasks.py", "--tasks", "custom|trivia_qa|0|1", "--output_dir", "/out"]
```

> [!NOTE]
>
> The value of `btype` in `--model_args` has been changed from the value (`bfloat16`) specified in the SmolLM2 README.
> This change is due to the hardware limitations of the GPU (NVIDIA TITAN V) used in our experiment.

`lighteval` operates by reading the evaluation tasks from the Python module specified by the `--custom_tasks` argument for the model defined in the `--model_args` argument.
This container image is designed to allow replacing the contents of `/in/tasks.py` with different Data as needed to investigate performance differences between prompts.

Next, build and push the container image.

```
docker build -t smollm2-evaluation:1.0 ./evaluator/
docker tag smollm2-evaluation:1.0 ${REPOSITORY}/smollm2-evaluation:1.0
docker push ${REPOSITORY}/smollm2-evaluation:1.0
```

### Writing the Plan Definition

Define the plan using the image created in the previous step.

```yaml:smollm2-evaluation.plan.yaml
image: ${REPOSITORY}/smollm2-evaluation:1.0
annotations:
  - name=smollm2-evaluation
  - target-model=HuggingFaceTB/SmolLM2-135M
  - benchmark-dataset=trivia_qa

inputs:
  - path: /in
    tags:
      - "type:lighteval-task"
      - "project:smollm2-prompt-engineering"
outputs:
  - path: /out
    tags:
      - "type:lighteval-output"
      - "project:smollm2-prompt-engineering"
log:
  tags:
    - "type:log"
    - "type:lighteval-output"

resources:
    memory: 10Gi
    cpu: "1"
    nvidia.com/gpu: "1"
```

> [!TIPS]
>
> If you are reproducing this example, adjust the Plan definition as needed for your cluster configuration:
>
> - The `resources` section for GPUs may need to reference different resource names depending on your cluster.
> - If your Kubernetes cluster contains a mix of GPU and non-GPU nodes, you might need to specify `on_node` to ensure the task runs on GPU-equipped nodes.
>
> For more details, consult your Knitfab admin.
>

`/in` is specified as the input directory to allow injecting `/in/tasks.py` as a data source.
The evaluation results are written to `/out`, which is defined as the output directory.

Register the Plan.

```
knit plan apply smollm2-evaluation.plan.yaml
```

## Step 4. Prompt Engineering

To examine how performance changes with different prompts, you will register multiple prompts as Data.

With lighteval, custom prompts are written as Python modules.

### Task with Standard Prompt

Create a working directory:

```
mkdir standard-prompt
```

Create a file named ./standard-prompt/tasks.py with the following content:

```python:./standard-prompt/tasks.py
from lighteval.tasks.lighteval_task import LightevalTaskConfig
from lighteval.metrics.metrics import Metrics
import lighteval.tasks.default_prompts as prompt

TASKS_TABLE=[
    LightevalTaskConfig(
        name="trivia_qa",
        prompt_function=prompt.triviaqa,
        suite=["custom"],
        hf_repo="mandarjoshi/trivia_qa",
        hf_subset="rc.nocontext",
        hf_revision="0f7faf33a3908546c6fd5b73a660e0f8ff173c2f",
        hf_avail_splits=["train", "validation"],
        evaluation_splits=["validation"],
        metric=[Metrics.quasi_exact_match_triviaqa],
        generation_size=20,
        trust_dataset=True,
        stop_sequence=["Question:", "Question"],
        few_shots_select="random_sampling_from_train",
    ),
]
```

This script defines a task to evaluate TriviaQA performance using the SmolLM2 model.
It is a simplified version of https://github.com/huggingface/smollm/blob/main/evaluation/tasks.py specifically designed for this experiment.

The prompt content is determined by the `prompt.triviaqa` function provided by lighteval. The function can be viewed here:

https://github.com/huggingface/lighteval/blob/392982542dfb0b90ee2e589d9d59c2012e232eaa/src/lighteval/tasks/default_prompts.py#L2193-L2215

The key element is the `query` argument of the returned `Doc`.
This value defines the input text passed to the language model. In this setup, the model receives a prompt in the following format:

```
Question: <TriviaQA question>
Answer:
```

This will serve as the baseline for comparison.
Register this module as Data in Knitfab:

```
knit data push -t type:lighteval-task -n ./standard-prompt
```

### "Trivia Master" Prompt

Since TriviaQA is a collection of trivia questions, let's transform SmolLM2 into a "trivia master" with a prompt like this:

```
You are the Trivia Master. Answer a following trivia quiz concisely.
Question: <TriviaQA question>
Answer:
```

This prompt encourages the model to embody a trivia expert, answering questions succinctly and directly.

Create `./trivia-master` directory.

```
mkdir trivia-master
```

Then save the following content as `./trivia-master/tasks.py`:

```python:./trivia-master/tasks.py
import string

from lighteval.tasks.lighteval_task import LightevalTaskConfig
from lighteval.tasks.requests import Doc
from lighteval.metrics.metrics import Metrics


def prompter(line, task_name: str = None):
    def _remove_prefixes(aliases):
        aliases.sort()
        ret = [aliases[0]]
        for alias in aliases[1:]:
            if not alias.startswith(ret[-1]):
                ret.append(alias)
        return ret

    list_of_candidates = [
        alias.lower().translate(str.maketrans("", "", string.punctuation))
        for alias in _remove_prefixes(line["answer"]["aliases"])
    ]

    return Doc(
        task_name=task_name,
        query=f"You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: {line['question']}\nAnswer:",
        gold_index=0,
        choices=[list_of_candidates],
    )

TASKS_TABLE=[
    LightevalTaskConfig(
        name="trivia_qa",
        prompt_function=prompter,
        suite=["custom"],
        hf_repo="mandarjoshi/trivia_qa",
        hf_subset="rc.nocontext",
        hf_revision="0f7faf33a3908546c6fd5b73a660e0f8ff173c2f",
        hf_avail_splits=["train", "validation"],
        evaluation_splits=["validation"],
        metric=[Metrics.quasi_exact_match_triviaqa],
        generation_size=20,
        trust_dataset=True,
        stop_sequence=["Question:", "Question"],
        few_shots_select="random_sampling_from_train",
    ),
]
```

I defined a function `prompter`. Note that the `prompt_function` parameter of `TASKS_TABLE` refers to the `prompter` function, ensuring the custom "Trivia Master" prompt is used during evaluation.

Register the new task definition as Data in Knitfab:

```
knit data push -t type:lighteval-task -n ./trivia-master
```

### Strict and Precise Answerer Prompt

To improve the TriviaQA score, let's ensure the model answers trivia questions with strict precision and accuracy. We'll use the following prompt:

```
You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.
Question: <TriviaQA question>
Answer:
```

Create `./precise-answerer` directory

```
mkdir precise-answerer
```

Save the following content as `./precise-answerer/tasks.py`:

```python:./precise-answerer/tasks.py
import string

from lighteval.tasks.lighteval_task import LightevalTaskConfig
from lighteval.tasks.requests import Doc
from lighteval.metrics.metrics import Metrics

def prompter(line, task_name: str = None):
    def _remove_prefixes(aliases):
        aliases.sort()
        ret = [aliases[0]]
        for alias in aliases[1:]:
            if not alias.startswith(ret[-1]):
                ret.append(alias)
        return ret

    list_of_candidates = [
        alias.lower().translate(str.maketrans("", "", string.punctuation))
        for alias in _remove_prefixes(line["answer"]["aliases"])
    ]

    return Doc(
        task_name=task_name,
        query=f"You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: {line['question']}\nAnswer:",
        gold_index=0,
        choices=[list_of_candidates],
    )

TASKS_TABLE=[
    LightevalTaskConfig(
        name="trivia_qa",
        prompt_function=prompter,
        suite=["custom"],
        hf_repo="mandarjoshi/trivia_qa",
        hf_subset="rc.nocontext",
        hf_revision="0f7faf33a3908546c6fd5b73a660e0f8ff173c2f",
        hf_avail_splits=["train", "validation"],
        evaluation_splits=["validation"],
        metric=[Metrics.quasi_exact_match_triviaqa],
        generation_size=20,
        trust_dataset=True,
        stop_sequence=["Question:", "Question"],
        few_shots_select="random_sampling_from_train",
    ),
]
```

Register this as a Data:

```
knit data push -t type:lighteval-task -n ./precise-answerer/tasks.py
```

### 待つ

After pushing the above Data using `knit data push ...`, simply wait for all the results to be generated. Knitfab will detect that each prompt can be applied to the "smollm2-evaluation" plan and will automatically execute the corresponding Runs with these prompts as inputs.

Let’s check the status of each run.

To do this, first identify the Runs and their outputs corresponding to the three prompts. Since all of these are related to runs based on the "smollm2-evaluation" plan, it is needed to determine the ID of that plan.

```
knit plan find --image ${REPOSITORY}/smollm2-evaluation:1.0 | jq '.[].planId'
```

Next, list the runs based on the plan with the identified ID.

```
knit run find -p "${Plan ID}"
```

Three runs corresponding to the three prompts should be found.
Check the status of each run. Typically, the status will transition in the following order:

- `waiting`: The initial state right after the Run is created.
- `ready`: The state where the destination for output Data has been secured and the run is ready to start.
- `starting`: The state immediately after the computation begins.
- `running`: The state where the computation is in progress.
- `completing`: The state where it is detected that the computation has successfully completed.
- `done`: The state where the computation has completed successfully and unnecessary resources have been released.

If a Run is in the `starting` state, it might be waiting for computational resources (especially GPUs), and it may not immediately transition to the `running` state.

Wait until each run reaches the `done` state.

## Step 5: Compare the Results

Once the three runs corresponding to the three prompts are in the `done` state, download their outputs and compare the results.

```
knit data pull -x ${output Knit ID} ./out/${appropriate directory name}
```

> [!TIPS]
>
> When naming the output directory, choose a clear and easy-to-understand name.
>
> However, if you are unsure which one is which, don’t worry. Knitfab remembers it for you. If needed, you can re-download the files later.

各ディレクトリ内の `results/HuggingFaceTB/SmolLM2-135M/results*.json` が結果のサマリーです。
この中の `"results"` というエントリに正解率（`"qem"`; quasi exact match の略で、出力の前後にある空白を取り除いた状態で、期待する回答と完全一致した率です）が記録されています。

The `results/HuggingFaceTB/SmolLM2-135M/results*.json` files within each directory contain the summary of the results.
In these files, the `"results"` entry contains the accuracy rate (`"qem"`; quasi exact match, which is the percentage of the output that exactly matches the expected answer after removing any surrounding whitespace).

When comparing the results, you should see approximate values as shown in the table below:

| prompt | qem (approx.) |
|:-----|------:|
| standard-prompt | 0.022 |
| trivia-master | 0.103 |
| precise-answerer | 0.079 |

As you can see, the performance differs depending on the prompt. The "trivia-master" prompt has a nearly 5 times higher accuracy than the "standard" prompt.

### Digging Deeper

Let's examine how the model made mistakes for each prompt.

The model's answers for each question are stored in the detail directory within the output data. The relevant Parquet files are named in the format `detail/HuggingFaceTB/SmolLM2-135M/${timestamp}/details_custom|trivia_qa_0${timestamp}.parquet`.

The column structure for these Parquet files is described in detail here: https://github.com/huggingface/lighteval/blob/main/docs/source/saving-and-reading-results.mdx#load-from-the-huggingface-hub
Pay particular attention to the following columns:

- `full_prompt` (the full prompt passed to the model)
- `predictions` (the model’s answer)
- `metrics` (whether the answer was correct)

You can query this data using [duckdb](https://duckdb.org/) to view it.

Run the following query to convert these three columns into a JSON format and view the first 10 records:

```sql
copy (select full_prompt, predictions, metrics from './out/standard-prompt/c9cfc4ca-5b3e-420b-83e0-0f901ee19b63/details/HuggingFaceTB/SmolLM2-135M/2024-12-10T01-47-04.505270/details_custom|trivia_qa|0_2024-12-10T01-47-04.505270.parquet' limit 10) to 'detail.json' (array);
```

(This is an example query for the "standard" prompt. Make sure to adjust the file path as necessary.)

The formatted result of the above query is as follows:

```json
[
    {
        "full_prompt": "Question: In April 1963, Lester Bowles Pearson became Prime Minister of which country?\nAnswer:",
        "predictions": "[([' Canada\\n\\n'], [-1.933692216873169, -0.2442161738872528, -0.6466554403305054, -2.003248691558838])]",
        "metrics": "{'qem': 1}"
    },
    {
        "full_prompt": "Question: Which US President was born Lesley Lynch King Jr?\nAnswer:",
        "predictions": "[([' Barack Obama\\n\\n'], [-2.628418207168579, -0.04262186586856842, -1.2610938549041748, -0.4659770131111145, -2.5769600868225098])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "Question: Rapidly boiling a liquid to make it thicker and more concentrated is called what?\nAnswer:",
        "predictions": "[([' Distillation\\n\\nQ: What is the difference between distillation and filtration?\\nAnswer: Distillation'], [-2.6942663192749023, -0.2995268404483795, -0.4160449504852295, -0.8358938694000244, -1.6305314302444458, -0.7395981550216675, -1.0752604007720947, -0.4633537530899048, -0.6777204275131226, -1.8828260898590088, -0.026748549193143845, -1.688951015472412, -0.0831923857331276, -1.577526330947876, -0.042983125895261765, -0.09957873821258545, -0.172224223613739, -0.0024808840826153755, -0.2556929886341095, -0.007029563654214144])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "Question: 8Â  Fort Ville-Marie was the original name of which Canadian city?\nAnswer:",
        "predictions": "[([' Fort Ville-Marie was the original name of which Canadian city?\\n\\n'], [-1.878208041191101, -0.28804850578308105, -0.001043133088387549, -0.0338585264980793, -0.006291819736361504, -0.8661340475082397, -0.28548896312713623, -0.28110817074775696, -0.031884584575891495, -0.023567086085677147, -0.09190956503152847, -0.07609765231609344, -0.02219853177666664, -0.16486409306526184, -0.23043379187583923, -0.9985241293907166, -2.9562790393829346])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "Question: \"What year did Jean-Francois Champollion publish the first correct translation of Egyptian hieroglyphs from the Rosetta Stone, the Roman Catholic Church take Galileo Galilei's \"\"Dialogue\"\" off their list of banned books, and Britain repeal the death penalty for over 100 crimes?\"\nAnswer:",
        "predictions": "[([' \"The Rosetta Stone was discovered in 1799 by French archaeologist Jean-Francois Champ'], [-0.549147367477417, -1.9164979457855225, -1.6489514112472534, -0.08574049174785614, -0.9531553983688354, -0.7687571048736572, -0.38980409502983093, -0.3014388680458069, -0.0005479741375893354, -0.023860685527324677, -0.0002649671514518559, -0.002856224775314331, -0.9774541258811951, -1.2453804016113281, -1.4208648204803467, -1.2441296577453613, -0.22031410038471222, -0.4270954728126526, -0.008720765821635723, -0.013052971102297306])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "Question: What is Marge Simpson's maiden name ?\nAnswer:",
        "predictions": "[([' Marge Simpson\\n\\nMarge Simpson is a fictional character from the 1940s'], [-1.7412254810333252, -0.12547612190246582, -0.280891090631485, -1.2609928846359253, -0.8938041925430298, -1.551526665687561, -0.4702300429344177, -0.3315695822238922, -1.6883487701416016, -0.824028491973877, -1.8885860443115234, -0.25895094871520996, -1.232683539390564, -0.3505438268184662, -1.2885715961456299, -0.1765313595533371, -0.008800766430795193, -1.4907751083374023, -0.7015455365180969, -0.25724366307258606])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "Question: What percentage of the earth's surface is covered by Europe?\nAnswer:",
        "predictions": "[([' 10%\\n\\n'], [-0.7567840218544006, -1.4727146625518799, -1.5819077491760254, -1.138973355293274, -0.476298987865448, -0.536645233631134, -1.3072094917297363])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "Question: Which artist has a daughter and two sons with Jane Asher, whom he married in 1981?\nAnswer:",
        "predictions": "[([' The artist is a painter, and the son is a sculptor.\\n\\n'], [-3.2958333492279053, -2.751289129257202, -1.2942497730255127, -3.30837345123291, -3.34598445892334, -1.5228177309036255, -2.188628673553467, -1.4657254219055176, -0.9899106025695801, -0.4008978009223938, -0.3648073971271515, -1.5260484218597412, -0.1996256411075592, -0.434756338596344, -0.4937499761581421, -2.031771421432495])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "Question: Which famous fishing town of east Scotland lies roughly half-way between Montrose and Dundee?\nAnswer:",
        "predictions": "[([' The town of Dundee lies in the north-east of the county of Argyll.\\n'], [-2.884977340698242, -2.0717034339904785, -0.21515531837940216, -2.3171334266662598, -0.05150463059544563, -0.9717702865600586, -2.226348638534546, -0.38932931423187256, -2.6928539276123047, -0.7956702709197998, -0.7509791254997253, -0.37150490283966064, -0.6873122453689575, -0.9606336355209351, -0.8567963242530823, -2.1453421115875244, -0.028062909841537476, -0.04036317020654678, -1.1038148403167725, -1.268834114074707])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "Question: Which was the first commercial jet airliner to go into service in the UK?\nAnswer:",
        "predictions": "[([' The first commercial jet airliner to go into service in the UK was the Boeing 707'], [-0.7208071947097778, -1.3049670457839966, -0.21477110683918, -0.553572416305542, -0.385793536901474, -0.014289788901805878, -0.5369077920913696, -0.2938914895057678, -0.025309380143880844, -0.03929346054792404, -0.148825004696846, -0.09589296579360962, -0.030028093606233597, -0.1491509974002838, -0.29845666885375977, -2.284789562225342, -0.13670581579208374, -0.14492401480674744, -0.6095356345176697, -0.01700183004140854])]",
        "metrics": "{'qem': 0}"
    }
]
```

The `"predictions"` column contains pairs of English text and some kind of vector. It appears that this vector represents the sequence of tokens returned by the model, while the English text is a transformed version of that sequence.

Upon analysis, the standard-prompt frequently produces answers in sentence form. However, TriviaQA expects answers to be words rather than full sentences. This behavior likely negatively impacts the accuracy rate.

Executing a similar query for the trivia-master outputs shows the following result:

```json
[
    {
        "full_prompt": "You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: In April 1963, Lester Bowles Pearson became Prime Minister of which country?\nAnswer:",
        "predictions": "[([' Canada\\n'], [-1.7264893054962158, -0.10874428600072861, -0.03504376485943794])]",
        "metrics": "{'qem': 1}"
    },
    {
        "full_prompt": "You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: Which US President was born Lesley Lynch King Jr?\nAnswer:",
        "predictions": "[([' George W. Bush\\n'], [-1.991175889968872, -0.9096693992614746, -0.14089666306972504, -0.012946479953825474, -0.37657949328422546, -0.08454815298318863])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: Rapidly boiling a liquid to make it thicker and more concentrated is called what?\nAnswer:",
        "predictions": "[([' Distillation\\n'], [-2.124079704284668, -0.29639899730682373, -0.29767075181007385, -0.054986342787742615])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: 8Â  Fort Ville-Marie was the original name of which Canadian city?\nAnswer:",
        "predictions": "[([' Ottawa\\n'], [-2.354099750518799, -0.1746305227279663, -0.02430429868400097])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: \"What year did Jean-Francois Champollion publish the first correct translation of Egyptian hieroglyphs from the Rosetta Stone, the Roman Catholic Church take Galileo Galilei's \"\"Dialogue\"\" off their list of banned books, and Britain repeal the death penalty for over 100 crimes?\"\nAnswer:",
        "predictions": "[([' 1799\\n'], [-0.4178844690322876, -0.06488373875617981, -0.5906904935836792, -0.5367541313171387, -0.4430837333202362, -0.5318288803100586, -0.3247792720794678])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: What is Marge Simpson's maiden name ?\nAnswer:",
        "predictions": "[([' Marge Simpson\\n'], [-1.641848087310791, -0.17814792692661285, -0.3750501871109009, -0.6823999285697937, -0.19204102456569672])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: What percentage of the earth's surface is covered by Europe?\nAnswer:",
        "predictions": "[([' 10%\\n'], [-0.2702411115169525, -1.418449878692627, -1.3690186738967896, -0.8845666646957397, -0.1479579359292984, -0.06396888941526413])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: Which artist has a daughter and two sons with Jane Asher, whom he married in 1981?\nAnswer:",
        "predictions": "[([' The Beatles\\n'], [-3.043836832046509, -2.7513725757598877, -0.02069312520325184, -0.5961008667945862, -0.05239078775048256])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: Which famous fishing town of east Scotland lies roughly half-way between Montrose and Dundee?\nAnswer:",
        "predictions": "[([' Aberdeen\\n'], [-2.838249444961548, -0.14105363190174103, -0.40612778067588806, -0.06407790631055832])]",
        "metrics": "{'qem': 0}"
    },
    {
        "full_prompt": "You are the Trivia Master. Answer a following trivia quiz concisely.\nQuestion: Which was the first commercial jet airliner to go into service in the UK?\nAnswer:",
        "predictions": "[([' The Boeing 707\\n'], [-0.9868261218070984, -2.411531448364258, -0.1350013166666031, -0.321322500705719, -0.3810722529888153, -0.010170303285121918, -0.7277032732963562, -0.05908128246665001])]",
        "metrics": "{'qem': 0}"
    }
]
```

Here, the answers are more concise. While there’s no difference in accuracy within this query's scope, the prompt instructing the model to "answer concisely" seems to have been effective for TriviaQA.

Next, let’s consider the "precise-answerer" prompt, which achieved a mid-range accuracy rate:

```json
[
	{
		"full_prompt": "You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: In April 1963, Lester Bowles Pearson became Prime Minister of which country?\nAnswer:",
		"predictions": "[([' Canada\\n'], [-1.9378408193588257, -0.17201809585094452, -0.09478380531072617])]",
		"metrics": "{'qem': 1}"
	},
	{
		"full_prompt": "You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: Which US President was born Lesley Lynch King Jr?\nAnswer:",
		"predictions": "[([' George W. Bush\\n'], [-2.506396770477295, -0.9977110624313354, -0.2693701386451721, -0.011972473002970219, -0.6038808822631836, -0.19966167211532593])]",
		"metrics": "{'qem': 0}"
	},
	{
		"full_prompt": "You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: Rapidly boiling a liquid to make it thicker and more concentrated is called what?\nAnswer:",
		"predictions": "[([' Boiling\\n'], [-2.7497341632843018, -0.024180497974157333, -1.7518264055252075, -0.21447332203388214])]",
		"metrics": "{'qem': 0}"
	},
	{
		"full_prompt": "You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: 8Â  Fort Ville-Marie was the original name of which Canadian city?\nAnswer:",
		"predictions": "[([' Fort Ville-Marie was the original name of which Canadian city?\\n'], [-2.094404697418213, -0.49479907751083374, -0.001684914343059063, -0.03708053007721901, -0.010029279626905918, -1.2236144542694092, -0.30421075224876404, -0.33396637439727783, -0.046404339373111725, -0.02139255404472351, -0.24684664607048035, -0.05905049294233322, -0.02144366130232811, -0.33441945910453796, -0.23572731018066406, -0.22757479548454285])]",
		"metrics": "{'qem': 0}"
	},
	{
		"full_prompt": "You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: \"What year did Jean-Francois Champollion publish the first correct translation of Egyptian hieroglyphs from the Rosetta Stone, the Roman Catholic Church take Galileo Galilei's \"\"Dialogue\"\" off their list of banned books, and Britain repeal the death penalty for over 100 crimes?\"\nAnswer:",
		"predictions": "[([' 1799\\n'], [-1.0891914367675781, -0.09142391383647919, -0.5811132788658142, -0.585858941078186, -0.4127100110054016, -0.8970917463302612, -0.7140992879867554])]",
		"metrics": "{'qem': 0}"
	},
	{
		"full_prompt": "You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: What is Marge Simpson's maiden name ?\nAnswer:",
		"predictions": "[([' Marge Simpson\\n'], [-1.653944969177246, -0.12940935790538788, -0.21645332872867584, -1.1405993700027466, -0.6379312872886658])]",
		"metrics": "{'qem': 0}"
	},
	{
		"full_prompt": "You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: What percentage of the earth's surface is covered by Europe?\nAnswer:",
		"predictions": "[([' 10%\\n'], [-0.37803971767425537, -1.4268310070037842, -1.3617628812789917, -0.9976868629455566, -0.26003915071487427, -0.22752352058887482])]",
		"metrics": "{'qem': 0}"
	},
	{
		"full_prompt": "You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: Which artist has a daughter and two sons with Jane Asher, whom he married in 1981?\nAnswer:",
		"predictions": "[([' The answer is: The Beatles.\\n'], [-3.151826858520508, -2.6840031147003174, -0.22725562751293182, -2.0870089530944824, -3.6007559299468994, -2.5920186042785645, -0.02511734887957573, -0.4749943017959595, -0.3350891172885895, -0.20437978208065033])]",
		"metrics": "{'qem': 0}"
	},
	{
		"full_prompt": "You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: Which famous fishing town of east Scotland lies roughly half-way between Montrose and Dundee?\nAnswer:",
		"predictions": "[([' Dundee\\n'], [-3.0182785987854004, -0.0828484371304512, -0.8448668718338013, -0.4432024359703064])]",
		"metrics": "{'qem': 0}"
	},
	{
		"full_prompt": "You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.\nQuestion: Which was the first commercial jet airliner to go into service in the UK?\nAnswer:",
		"predictions": "[([' The first commercial jet airliner to go into service in the UK was the Boeing 707'], [-0.9244765043258667, -1.8300584554672241, -0.19787319004535675, -0.4966600239276886, -0.6826395392417908, -0.021142464131116867, -0.5793478488922119, -0.1932220757007599, -0.019743353128433228, -0.029880009591579437, -0.1301271915435791, -0.07407835870981216, -0.02199738845229149, -0.14878585934638977, -0.2913905084133148, -2.2714085578918457, -0.12212035804986954, -0.34001803398132324, -0.5835666060447693, -0.024602102115750313])]",
		"metrics": "{'qem': 0}"
	}
]
```

The brevity of the answers falls somewhere between that of "standard-prompt" and "trivia-master".

The meaning of the responses appears consistent across all prompts, suggesting that performance differences arise from how well the model’s behavior aligns with the task requirements.

## Summary

Using Knitfab, we accomplished the following:

- Practiced prompt engineering for natural language models.
- Conducted performance evaluations and comparisons of models published on Hugging Face.
- Automated the execution of multiple experiments under a single Plan.
    - Aside from defining the plan, the only additional requirement was providing experimental conditions as data.
