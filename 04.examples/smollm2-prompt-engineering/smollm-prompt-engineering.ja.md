EXAMPLE: Prompt Engneering with SmolLM2
==================================

本書では、小型言語モデル SmolLM2 を題材に、プロンプトエンジニアリングを行う事例を示します。

> [!NOTE]
>
> 本書の事例を手元で再現する際には GPU を利用することを強くおすすめします。CPU では現実的ではありません。

## ステップ1. アウトライン

本事例は、 SmolLM2-135M についてプロンプトエンジニアリングをすることで、性能にどのような影響があるか調べる実験を題材とします。
この実験では、ベンチマークデータセットとして、英語圏の雑学クイズを集めたデータセットである [TriviaQA](https://nlp.cs.washington.edu/triviaqa/) を利用します。
また、評価用のツールとして [HuggingFace/lighteval](https://github.com/huggingface/lighteval) を利用します。

次の手順で実験を進めてゆきます。

1. アウトライン
2. 環境構築
3. モデル評価用 Plan を作成する
4. プロンプトを複数用意して、評価する
5. 結果を比較する

### SmolLM2 とは

[SmolLM2](https://github.com/huggingface/smollm) とは、多様なタスクを解くことができるコンパクトな自然言語モデルです。
HuggingFace で公開されていて、簡単にアクセスすることができます。

本事例では、実験を手軽なものにするために、SmolLM2 シリーズのうち最小のモデルである SmolLM2-135M を使用します。

### TriviaQA のデータ概観

https://huggingface.co/datasets/lighteval/trivia_qa で、TriviaQA のデータ内容を見ることができます。

雑学クイズの問題文 (question) と、それに対する正答 (answer) 、およびその由来情報としたデータセットであることがわかります。
正答は文章ではなく、一語から数語の (固有) 名詞であり、その表現の揺れに応じて複数のオプションが列挙されています。

TriviaQA に答える言語モデルは、この正解のうちのいずれかを出力することを求められます。

## ステップ2. 環境構築

まず、この一連の実験を行うディレクトリを作成します。

```
mkdir smollm2-prompt-engineering
cd smollm2-prompt-engineering
```

続いて、このディレクトリを Knitfab のプロジェクト用ディレクトリにします。

`knit init` して、このディレクトリでの作業で使う Knitfab を設定します。

```
knit init PATH/TO/handout/knitprofile
```

さらに、このディレクトリでのプロジェクト用の共通タグを `knitenv` ファイルに記述します。

```
tag:
  - "project:smollm2-prompt-engineering"
```

これによって、以後の `knit data push` や `knit plan template` が、常にこの `project:smollm2-prompt-engineering` を Tag としてセットするようになります。

## ステップ3. 評価用 Plan を定義する

言語モデル SmolLM2-135M の評価を行う Plan を定義します。

[SmolLM2 のドキュメント](https://github.com/huggingface/smollm/blob/main/evaluation/README.md) によれば、評価は [lighteval](https://github.com/huggingface/lighteval/) を使って行う、とのことなので、本実験でもそれに従うことにします。

この実験では、プロンプトの違いによる性能の差異に関心がありますから、作成する評価用 Plan は、*任意のプロンプトを、 Knitfab 的な Data として受け入れることができる*ものである必要があります。

### コンテナイメージを定義する

`lighteval` を実行するコンテナイメージを作ります。

作業用ディレクトリ と Dockerfile を作成します。

```
mkdir evaluator
touch evaluator/Dockerfile
```

Dockerfile の内容を次のようにします。

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
> `--model-args` 中の `btype` の値が、SmolLM2 の README にある値(`bfloat16`)から変更されています。
> これは、我々が実験に使った GPU (NVIDIA TITAN V) の機能制約によるものです。

`lighteval` は、引数 `--model_args` に指定されたモデルに対し、 引数 `--custom_tasks` の指す python モジュールから評価対象のタスクを読み取る、という振る舞いをします。このコンテナイメージの設計は、適宜 `/in/tasks.py` の内容を Data として取り替えて、プロンプト同士の性能差を調べよう、というものです。

続いて、これをビルドして、適宜プッシュします。

```
docker build -t smollm2-evaluation:1.0 ./evaluator/
docker tag smollm2-evaluation:1.0 ${REPOSITORY}/smollm2-evaluation:1.0
docker push ${REPOSITORY}/smollm2-evaluation:1.0
```

### Plan 定義を記述する

前節で定義したイメージを利用する Plan を定義します。

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
> この事例をお手元で再現する場合には、お使いのクラスタに合わせて Plan 定義を適宜調整してください。
>
> - GPU にあたる `resource` は、クラスタによっては異なるリソース名を参照する必要があるかもしれません。
> - Kubernetes クラスタ内に GPU が搭載されている Node とそうでない Node が混在している場合、GPU 搭載 Node 上でのみタスクを実行するためには、 `on_node` の指定が必要である場合があります。
>
> 詳細は、お使いの Knitfab の運用管理担当者にご相談ください。
>

`/in/tasks.py` を Data として注入できるようにするために、`/in` を入力に指定しています。
また、評価結果は `/out` に書き出されるので、このディレクトリを出力に指定しています。

この Plan 定義を登録します。

```
knit plan apply smollm2-evaluation.plan.yaml
```

## ステップ4. プロンプトエンジニアリング

プロンプトを変えたときに性能がどう変化するか調べるため、複数のプロンプトを Data として登録します。

lighteval においては、カスタムプロンプトは Python のモジュールとして記述します。

### 標準的なプロンプトを指定したタスク

作業ディレクトリを作ります。

```
mkdir standard-prompt
```

ファイル `./standard-prompt/tasks.py` として、次の内容のファイルを作成します。

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

このファイルは、 https://github.com/huggingface/smollm/blob/main/evaluation/tasks.py の抜粋版であり、言語モデルに対して TriviaQA の評価を行うタスクを実行させるものです。

ここで使われているプロンプトの内容は、lighteval が提供する関数 `prompt.trivia_qa` で決まっています。次の内容となっています。

https://github.com/huggingface/lighteval/blob/392982542dfb0b90ee2e589d9d59c2012e232eaa/src/lighteval/tasks/default_prompts.py#L2193-L2215

要点は、返り値の `Doc` の引数 `query` です。この値が言語モデルに渡される入力テキストです。すなわち、この条件では

```
Question: <TriviaQA の問題文>
Answer:
```

というプロンプトがモデルに与えられることになる、というわけです。

このプロンプトに基づく性能をべースラインとします。Data としてこのモジュールを登録します。

```
knit data push -t type:lighteval-task -n ./standard-prompt
```

### "雑学クイズマスター"のプロンプト

TriviaQA は雑学クイズを収集したものですから、SmolLM2 にも雑学クイズマスターになってもらいましょう。
こういうプロンプトを与えてみることにします。

```
You are the Trivia Master. Answer a following trivia quiz concisely.
Question: <TrivaiQA の問題文>
Answer:
```

ついでに、クイズの達人らしく、ズバッと簡潔に答えてもらうことにしましょう。

フォルダ `./trivia-master` を作成します。

```
mkdir trivia-master
```

続いて、ファイル `./trivia-master/tasks.py` として、上記プロンプトを与えるようなタスク定義ファイルを作成します。

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

プロンプトを与える関数 `prompter` を定義しました。`TASKS_TABLE` の要素は、関数 `prompter` を `prompt_function` に指定していることに注意してください。

では、これを Data として登録しましょう。

```
knit data push -t type:lighteval-task -n ./trivia-master
```

### 厳密な回答者

雑学クイズに間違わないことが、TriviaQA のスコアを向上させるはずですから、厳密・正確に答えるようなプロンプトを与えてみましょう。
次のプロンプトを与えることにします。

```
You are an answerer of trivia quizzes. You should answer them precisely with accuracy after reading a question cautiously.
Question: <TriviaQA の問題文>
Answer:
```

フォルダ `./precise-answerer` を作成します。

```
mkdir precise-answerer
```

続いて、ファイル `./precise-answerer/tasks.py` として、次のファイルを作成します。

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

これも Data として登録しましょう。

```
knit data push -t type:lighteval-task -n ./precise-answerer/tasks.py
```

### 待つ

以上の Data を `knit data push ...` したら、あとは全ての結果が出揃うまで待ちます。
Knitfab が "smollm2-evaluation" Plan に対して各プロンプトが適用できる、ということを検出し、自動的にそれぞれを入力とした Run を遂行しています。

各 Run の状況を調べましょう。

このためにまず、3 つのプロンプトに対応する Run とその出力を特定します。
いずれも "smollm2-evaluation" Plan に基づく Run に関するものですから、その Plan の ID を特定すればよいです。

```
knit plan find --image ${REPOSITORY}/smollm2-evaluation:1.0 | jq '.[].planId'
```

次に、その ID の Plan に基づく Run を列挙します。

```
knit run find -p "${Plan ID}"
```

3 つのプロンプトに対応した、3 つの Run が見つかるはずです。
それぞれ、Run の状態 (status) を確認します。通常は、次の順序で状態が変わっていきます。

- `waiting`: Run が作成された直後の状態
- `ready`: 出力 Data の保存先を確保して、実行できるようになった状態
- `starting`: Run の計算を開始した直後の状態
- `running`: 計算が進行中である状態
- `completing`: 計算が正常に完了したことを検出した状態
- `done`: 計算が正常に完了し、不要になったリソースを解放し終わった状態

`starting` である Run は、計算機リソース (特に GPU) の順番待ちをしていることがあり、その場合にはすぐに `running` になるとは限りません。

各 Run が `done` になるまで待ちます。

## ステップ5. 結果を比較する

3 つのプロンプトに対応する 3 つの Run が `done` 状態になったら、その出力をダウンロードして、結果を比較しましょう。

```
knit data pull -x ${出力の Knit ID} ./out/${適切なディレクトリ名}
```

> [!TIPS]
>
> 出力ディレクトリ名は、適宜わかりやすいものをつけてください。
>
> とはいえ、どれだどれだかわからなくなってしまっても大丈夫です。 Knitfab が覚えています。
> いざとなれば、改めてダウンロードしなおしましょう。

各ディレクトリ内の `results/HuggingFaceTB/SmolLM2-135M/results*.json` が結果のサマリーです。
この中の `"results"` というエントリに正解率（`"qem"`; quasi exact match の略で、出力の前後にある空白を取り除いた状態で、期待する回答と完全一致した率です）が記録されています。

比較表にすると、およそ次の値になっているはずです。

| prompt | qem (approx.) |
|:-----|------:|
| standard-prompt | 0.022 |
| trivia-master | 0.103 |
| precise-answerer | 0.079 |

この通り、プロンプトによって性能は異なることがわかります。標準のプロンプト（standard-prompt）に比べて、雑学クイズマスター (trivia-master) は 5 倍近い正解率となりました。

### さらに深堀りする

各プロンプトで、モデルがどう間違ったのか、ということを見ておきましょう。

各問題に対するモデルの回答は、出力 Data のうち `detail` ディレクトリ内に格納されています。
`detail/HuggingFaceTB/SmolLM2-135M/${timestamp}/details_custom|trivia_qa_0${timestamp}.parquet` という形式の名前をした parquet ファイルがそれです。

この parquet の列構成は、 https://github.com/huggingface/lighteval/blob/main/docs/source/saving-and-reading-results.mdx#load-from-the-huggingface-hub に示されている通りです。
特に、次の列に注目してみていきましょう。

- `full_prompt` (モデルにわたすプロンプト全体)
- `predictions` (モデルからの回答)
- `metrics` (回答が正しかったか)

この中身を [duckdb](https://duckdb.org/) をつかって見ていくことにします。

次のようなクエリを実行して、上記三列を json に変換したものを、先頭 10 レコードについて見ていきます。

```sql
copy (select full_prompt, predictions, metrics from './out/standard-prompt/c9cfc4ca-5b3e-420b-83e0-0f901ee19b63/details/HuggingFaceTB/SmolLM2-135M/2024-12-10T01-47-04.505270/details_custom|trivia_qa|0_2024-12-10T01-47-04.505270.parquet' limit 10) to 'detail.json' (array);
```

(これは、 standard-prompt についてのクエリ例です。ファイルパスは適宜変更してください)

上記クエリの結果（を整形したもの）は、次の内容でした。

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

`"predictions"` には、英文と、何らかのベクトルの組が格納されていることがわかります。おそらく、このベクトルがモデルが返したトークン列であり、それを変換したものが英文なのでしょう。

そうしてみたとき、 standard-prompt は少なくない割合で文章で答えを返してしまっていることが見て取れます。一方、　TriviaQA では、答えは文章ではなくて語であることを期待していたのでした。
この挙動は正答率に良くない影響を与えていそうです。

これに対して、"trivia-master" の出力について同様のクエリを実行した結果は、次のとおりでした。

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

こちらは、より簡潔に答えを返している事がわかります。このクエリの範囲では正答率に違いはないものの、TriviaQA に答えるは「簡潔に答えよ」というプロンプトが有効だった可能性があります。

正解率が中間の性能だった precise answerer プロンプトはどうでしょう？

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

回答の簡潔さも中間程度に見えます。

回答の意味はどのモデルでも似たようなものですから、タスクに対する挙動のアラインメントが性能を分けた、と言えそうです。

## まとめ

Knitfab を利用して、

- 自然言語モデル(LM)に対するプロンプトエンジニアリングを実践しました。
- HuggingFace に公開されているモデルの性能評価とその比較を実践しました。
- 単一の Plan に対する複数の実験実施を自動化しました。
    - Plan 定義のほかに必要だったのは、実験条件を Data として与えることだけでした。
