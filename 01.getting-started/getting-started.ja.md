はじめに
=======

Knitfab にようこそ！

本書では、簡易的な Knitfab のインストールと、単純な機械学習タスクを題材にした Knitfab のチュートリアルを扱います。

> [!Caution]
>
> 本チュートリアルは、Apple Silicon や ARM 系の CPU を搭載しているコンピュータではうまく機能しない可能性があります。

他言語版/Translations
---------------------

- en: [./getting-started.en.md](./getting-started.en.md)

Knitfab とは
------

Kntifab とは、

- タグベースワークフローエンジンと
- 自動リネージ管理システム

をもった MLOps ツールです。

ユーザが実験を *"プラン"* (後述)し、必要なデータをそろえれば、 Knitfab は自動的にその実験を実行します。
またその際に、実験ごとに入力と出力を記録して、履歴を遡れるようにします。

これによって、全実験の全履歴が有機的に関連付けられるようになるのです。

### コンセプト

#### Knitfab における「機械学習タスク」

Knitfab では、機械学習タスク (あるいは、プログラム) を「入力をとって、出力を与える何らかの処理」として一般化して捉えます。
（以下では、この意味で「機械学習タスク」という表現を用いることにします）

その実体は、kubernetes 上で実行されるコンテナです。

#### タグ

Knitfab が扱うリソースには、*"タグ"* というキー：バリュー型のメタデータをつけることができます。

タグ付けできるリソースには、"タグ" を任意の数設定できます。

#### データ

機械学習タスクに入力されたり出力されたりするものは、すべて *"データ"* です。

Knitfabでは、"データ" は「"タグ" のついたディレクトリ」だと考えます。

ユーザは Knitfab に対して "データ" をアップロードしたり、既存の "データ" に "タグ" を再設定したりできます。

データの実体は、kubernetes の Persistent Volume Claim および Persistent Volume です。

#### プラン

*"プラン"* は、「どういう入力を、どういう機械学習タスクに与えて、どういう出力を得るのか」を定義したものです。

機械学習タスクは、コンテナイメージとして設定します。

入力と出力は "データ" をマウントするファイルパスであり、それぞれ "タグ" を設定できます。

入力のタグは「その入力にセットしていい "データ" 」を決めるものです。Kntifabは、そのプランの入力の "タグ" をすべて持っている "データ" を、その入力としてセットします。

出力のタグは、その出力 "データ" に自動セットされる "タグ" です。Knitfabは、そのプランを"ラン"として実行し、出力が得られたら出力タグをただちにセットします。
（出力データに別のタグを手動でセットすることはもちろんできます）

#### ラン

*"ラン"* は、Knitfab 内で実行する具体的な機械学習タスクです。

"ラン" は、"プラン"の定義に従って生成されます。

Knitfabは、プランの各入力（入力タグ）をチェックし、そこにセットできる "データ" が全て揃ったらランを実行します。ユーザが "ラン" を直接実行することはできません。

ランの実体は kubernetes の Job です。


Knitfab（簡易版） をローカル環境にインストールする
------

本章では、Knitfab をローカルPCなどに簡易的にインストールして、「ちょっと試してみる」ための手順を説明します。

> [!Warning]
>
> ここで紹介する方法でインストールされた Knitfab は簡易版であり、データ保存場所を kubernetes に頼っています。
> したがって、それを構成する kubernetes pod が再起動しただけで情報（ "データ" やリネージなど）を喪失する可能性があります。
>
> 正式に運用することを目的とするのであれば、 admin-guide に従って Kntifab を構築してください。

### インストールに必要な環境とツール

必要な環境は次のものです。

- 読者が自由にしてよい kubernetes クラスタ

必要なツールは次のものです。

- bash
- helm
- curl
- wget

インストーラスクリプトは bash のシェルスクリプトとして書かれています。
curl と helm はインストーラが内部的に利用します。

#### 一時的な kubernetes クラスタを作成する

実験用に、自由に作って壊せる kubernetes クラスタを構築する方法を紹介します。

ここでは [minikube](https://minikube.sigs.k8s.io/docs/) を利用する例を示します。

minikube は、ローカルな kubernetes クラスタを構築するためのツールです。
すなわち、あなたが作業に使っているコンピュータ内に、kubernetes クラスタを構築できるのです。
また、その kubernetes クラスタはあなた専用のものなので、不要になれば簡単に削除できます。

minikube を使ってクラスタを起動するには、

```
minikube start --memory 4G --container-runtime=containerd
```

のようにすします。 **メモリは 4GB 程度は必要** です。それ以外は、必要に応じてオプションを調整してください。
オプションの詳細は minikube のドキュメントを参照してください。

### インストールする

1. インストーラを手に入れる
2. インストーラから、デフォルトの設定ファイルを生成させる
3. インストールする

#### インストーラを入手する

インストーラは https://github.com/opst/knitfab/installer/installer.sh です。

これを適当なディレクトリにダウンロードします。

```
mkdir -p ~/devel/knitfab-install
cd ~/devel/knitfab-install

wget -O installer.sh https://raw.githubusercontent.com/opst/knitfab/main/installer/installer.sh
chmod +x ./installer.sh
```

#### デフォルトの設定ファイルを生成させる

ダウンロードしたインストーラについて、

```
./installer.sh --prepare -n ${NAMESPACE}
```

`${NAMESPACE}` には、これから Knitfab をインストールしようとする kubernetes のネームスペースを任意に（ユーザの好みの名前を）指定します。
なお、この `${NAMESPACE}` は kubernetes の名前空間となるものなので、kubernetesの仕様により、
使える文字は半角英小文字と数字、ハイフン '-' のみであり、英・数字ではじまり、英・数字で終わる文字列である必要があります。

を実行すると、 `./knitfab_install_settings` ディレクトリに Knitfab のインストール設定が生成されます。
**この設定は「 Knitfab が管理している情報を永続化しない」ように記述されています。**
したがって、 Knitfab を構成する pod を削除・再起動すると、情報の不整合が生じたり情報が喪失したりする場合があります。
あくまで一時的な利用に留めることをおすすめします。

> [!Note]
>
> もし、デフォルトの kubeconfig 以外の kubeconfig が使いたいなら、`--kubeconfig` フラグで与えることができる。
>
> ```
> ./installer.sh --prepare --kubeconfig ${KUBECONFIG} -n ${NAMESPACE}
> ```

#### インストールする

作成したインストール設定を利用して、実際に Knitfab をインストールします。

```
./installer.sh --install -s ./knitfab_install_settings
```

スクリプトは順次必要なコンポーネントのインストールを進行します。
あわせて、この Knitfab に対する接続設定を含むディレクトリが `./knitfab_install_settings/handouts` に生成されます。

以上がエラーなく終了すれば、インストールは完了です。

### アンインストールする

インストーラは `./knitfab_install_settings` 内にアンインストーラ (`uninstaller.sh`) も生成します。
これを実行することで、Knitfab はクラスタからアンインストールされます。

```
./knitfab_install_settings/uninstaller.sh --hard
```

オプション `--hard` は、データベースやイメージレジストリも含めて、すべての Knitfab リソースを破棄することを意味します。


CLI ツール: knit
-----------------

Knitfab に対する操作は CLI コマンド `knit` を介して行います。
以降のチュートリアルに先立ち、 `knit` コマンドを入手してください。

ツールは https://github.com/opst/knitfab/releases から入手できます。
使用する環境にあったバイナリをダウンロードしてください。

たとえば、

```
mkdir -p ~/.local/bin

VERSION=v1.5.1  # or release which you desired
OS=linux        # or windows, darwin
ARCH=arm64      # or amd64

wget -O ~/.local/bin/knit https://github.com/opst/knitfab/releases/download/${VERSION}/knit-${OS}-${ARCH}
chmod -x ~/.local/bin/knit

# and prepend ~/.local/bin to ${PATH}
```

チュートリアル1: Knitfab でモデルを訓練する
-------

チュートリアルとして、ごく簡単な実験についてウォークスルーしながら、Knitfab の動きを紹介します。

詳細な利用法については、 user-guide をご参照ください。

### 前提

このウォークスルーはインストール済の Knitfab にアクセスできることに加え、次のツールがあることを前提としています。適宜インストールしておいてください。

- docker
- graphviz の dot コマンド

#### docker の設定

docker の設定をおこないます。

Knitfab はクラスタ内にコンテナイメージのレジストリをデプロイします。
このレジストリはプライベートなものです。このため、ユーザ独自のカスタムなイメージを利用した実験を行う場合でも dockerhub などに公開することなく実験を進める事ができます。

ただし、そのためには、docker コマンドに対してこのレジストリの CA 証明書を信頼させる必要があります。
詳細は docker のドキュメントをご参照ください。: https://docs.docker.com/engine/security/certificates/#understand-the-configuration

次のようにすることで、Knitfab が使っている TLS 証明書を docker が信頼するようになります。

```
cp -r /path/to/handout/docker/certs.d /etc/docker/certs.d
```

> [!Caution]
>
> この操作は、お使いのシステム上の docker の挙動に対してグローバルな影響があります。
> もしコンピュータを複数のユーザで共有しているのならば、あらかじめ他のユーザの同意を得るようにしてください。

> [!Note]
>
> もし dockerd を colima や minikube のような仮想環境上で実行しているなら、
> このあとの操作はその仮想環境において実施する必要があります。

### 作業ディレクトリを作成する

これから始める機械学習タスクプロジェクトのファイルを格納するディレクトリを作成して、そこに移動します。

任意のディレクトリでよいが、ここでは `first-knitfab-project` とします。
他の名前のディレクトリを使う場合は、これ以降の説明では適宜読み替えてください。

```
mkdir -p ~/devel/first-knitfab-project
cd ~/devel/first-knitfab-project
```

### knit コマンドの初期化

最初に、Knitfab への接続情報を knit cli の設定として取り込む必要があります。

> [!Note]
>
> もしあなた以外に管理者のいる kntifab に接続しようとしているなら、管理者からハンドアウトを受け取ってください。

Knitfab をインストールしたときに生成されたハンドアウト(`handout`)に `knitprofile` というファイルが含まれているので、これを取り込みます。
次のようにします。

```
knit init /path/to/handout/knitprofile
```

これで、このディレクトリでの knit を使った作業は、このハンドアウトを生成した Knitfab に接続して実施されるようになりました。

これで、Knitfab を使い始める準備ができました。

### "データ" を投入する

今回は [QMNIST](https://github.com/facebookresearch/qmnist) を利用して、ディープラーニングによる手書き数字の分類器をつくってみましょう。

QMNIST は、facebookresearch による手書き数字データセットです。同様のものに MNIST という有名なデータセットがありますが、 QMNIST はそれを拡張・整理したものです。

QMNIST を Knitfab に投入するために、まずは上記 QMNIST データセットをダウンロードし、画像とラベルが組になるようにディレクトリに格納しましょう。以下のように、訓練用・テスト用をそれぞれダウンロードします。

```
mkdir -p data/qmnist-train data/qmnist-test

wget -O data/qmnist-train/images.gz https://raw.githubusercontent.com/facebookresearch/qmnist/master/qmnist-train-images-idx3-ubyte.gz
wget -O data/qmnist-train/labels.gz https://raw.githubusercontent.com/facebookresearch/qmnist/master/qmnist-train-labels-idx2-int.gz

wget -O data/qmnist-test/images.gz https://raw.githubusercontent.com/facebookresearch/qmnist/master/qmnist-test-images-idx3-ubyte.gz
wget -O data/qmnist-test/labels.gz https://raw.githubusercontent.com/facebookresearch/qmnist/master/qmnist-test-labels-idx2-int.gz
```

続いて、訓練用データセットを "データ" として Knitfab にアップロードします。

```
knit data push -t format:mnist -t mode:training -t type:dataset -t project:first-knitfab -n ./data/qmnist-train
```

各オプションの意味は次の通りです。

- `-t`: "データ" に "タグ" を設定する
- `-n`: ディレクトリ名を `name:...` というキーをもった "タグ" として登録する

これによって、訓練用データセット "データ" として Knitfab に登録されました。
このときコンソールに表示されるのは、登録された "データ" のメタデータです。

```json
{
    "knitId": "63685b22-f04b-478b-9fa0-9c0a4fd7314f",
    "tags": [
        "format:mnist",
        "knit#id:63685b22-f04b-478b-9fa0-9c0a4fd7314f",
        "knit#timestamp:2024-11-19T05:24:36.964+00:00",
        "mode:training",
        "name:qmnist-train",
        "project:first-knitfab",
        "type:dataset"
    ],
    "upstream": {
        "mountpoint": {
            "path": "/upload",
            "tags": []
        },
        "run": {
            "runId": "4079754d-cf73-4529-9a17-c4aad942d6cd",
            "status": "done",
            "updatedAt": "2024-11-19T05:24:36.964+00:00",
            "plan": {
                "planId": "f9631291-31c1-4d94-aa14-dbc17dc25464",
                "name": "knit#uploaded"
            }
        }
    },
    "downstreams": [],
    "nomination": []
}
```

キー `"knitId"` の値が、この "データ" を識別する ID です。また、同じ値が "タグ" `knit#id` の値としても登録されています。

### 機械学習タスクを実行するプログラムを書く

QMNIST を訓練するサンプルスクリプトが `./scripts/train.py` に用意してあるので、これを使います。

これは、pytorch を使って書かれていて、次に示す深層学習モデルを QMNIST の訓練用 "データ" で訓練するスクリプトです。

```python
class MyMnistModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = torch.nn.Sequential(
            torch.nn.Conv2d(1, 16, kernel_size=3, padding=1),  # 1x28x28 -> 16x28x28
            torch.nn.ReLU(),
            torch.nn.Conv2d(16, 32, kernel_size=3, padding=1),  # 16x28x28 -> 32x28x28
            torch.nn.ReLU(),
            torch.nn.Flatten(),
            torch.nn.Linear(32 * 28 * 28, 1024),
            torch.nn.ReLU(),
            torch.nn.Linear(1024, 10),
        )

    def forward(self, x):
        logit = self.layers(x)
        return logit
```

これを最初の機械学習タスクとして、Knitfab 上で動かすことを目指します。

なお、この訓練スクリプトは次のような設定となっているいます。

- 乱数シードは `0` に固定してあります。
    - 標準ライブラリ, numpy, pytorch のいずれも同様です。
- 訓練用データには 6 万件の画像:ラベル組が含まれていますが、このうちランダムな 5 万件を訓練用、残りをバリデーション用に分割しています。
- ミニバッチ訓練をしていて、バッチサイズは 64 です。
- また、全体で 3 エポック訓練するように設定してあります。

#### ローカルで動作検証する

Knitfab で動かす前に、まずはこれを Knitfab の外で動かして、何が起きるか確認しておきましょう。

このチュートリアルには、この訓練スクリプトを Docker イメージとしてビルドするための Dockerfile もバンドルされています。
Docker コンテナとして動作を検証しましょう。訓練スクリプト用のイメージは、次のコマンドでビルドできます。

```
docker build -t knitfab-first-train:v1.0 -f scripts/train/Dockerfile ./scripts
```

このコマンドでは、`./scripts/train.py` を実行できる Docker イメージをビルドして、それに `knitfab-first-train:v1.0` という別名 (タグ) をつけています。

Dockerfile の内容は次のとおりです。

```Dockerfile
FROM python:3.11

WORKDIR /work

RUN pip install numpy==1.26.4 && \
    pip install torch==2.2.1 --index-url https://download.pytorch.org/whl/cpu

COPY . .

ENTRYPOINT [ "python", "-u", "train.py" ]
CMD [ "--dataset", "/in/dataset", "--save-to", "/out/model" ]
```

上記では依存ライブラリをインストールし、`./train.py` を実行しています。GPU 環境を想定していないので、pytorch は CPU 版を指定しました。
`train.py` は 2 つのコマンドラインフラグをとっています。

- `--dataset /in/dataset` : 訓練用データセットの所在は (コンテナ内の) `/in/dataset` である
- `--save-to /out/model` : モデルパラメータを保存する先は (コンテナ内の)  `/out/model` である

したがって、この 2 つのファイルパスに対してデータセットとモデルの書き出し先とをマウントしながら起動すればよいです。

```
mkdir -p ./out/model

docker run --rm -it \
    -v "$(pwd)/data/qmnist-train:/in/dataset" \
    -v "$(pwd)/out/model:/out/model" \
    knitfab-first-train:v1.0
```

ホストマシン側では `./out/model` にモデルが書き出されるように設定しました。
また、コンテナ側の `/in/dataset` には、先程 QMNIST の訓練用データセットをダウンロードしたディレクトリを指定しました。
次のようなログが得られれば成功です。

```
data shape:(60000, 28, 28), type: uint8
label shape:(60000,), type: uint8
**TRAINING START** Epoch: #1
Epoch: #1, Batch: #0 -- Loss: 2.3024802207946777, Accuracy: 0.046875
Epoch: #1, Batch: #100 -- Loss: 2.154975175857544, Accuracy: 0.29842202970297027
Epoch: #1, Batch: #200 -- Loss: 0.667496919631958, Accuracy: 0.5030317164179104
Epoch: #1, Batch: #300 -- Loss: 0.3974001109600067, Accuracy: 0.6195494186046512
Epoch: #1, Batch: #400 -- Loss: 0.2097681164741516, Accuracy: 0.6856296758104738
Epoch: #1, Batch: #500 -- Loss: 0.3507159948348999, Accuracy: 0.7278255988023952
Epoch: #1, Batch: #600 -- Loss: 0.18445907533168793, Accuracy: 0.7567595673876872
Epoch: #1, Batch: #700 -- Loss: 0.31259363889694214, Accuracy: 0.7791993580599144
**TRAINING RESULT** Epoch: #1 -- total Loss: 597.214958243072, Accuracy: 0.79342
**VALIDATION START** Epoch: #1
**VALIDATION RESULT** Epoch: #1 -- total Loss: 44.73237031698227, Accuracy: 0.9127
**SAVING MODEL** at Epoch: #1
**TRAINING START** Epoch: #2
...(snip)...
```

動作確認としては 1 エポックも見れば十分なので、中断(`Ctrl+C`)してしまいましょう。

> [!Note]
>
> ログの最初に OpenBLAS に由来する警告メッセージが表示されるかもしれませんが、無視してかまいません。

### Knitfab に機械学習タスクを登録する

動作が確認できたら、これを使って Knitfab に機械学習タスクを任せてみましょう。

これには 2 つのステップを踏みます。

1. Docker イメージを Knitfab のクラスタ内イメージレジストリに登録する
2. "プラン" の定義をイメージから作成して、Knitfab に登録する

#### Docker イメージを Knitfab に登録する

先程作成した Docker イメージに、新しくタグをセットしましょう。

```
docker tag knitfab-first-train:v1.0 ${YOUR_KNITFAB_NODE}:${PORT}/knitfab-first-train:v1.0
```

`${YOUR_KNITFAB_NODE}` には、使っている Knitfab クラスタを構成するノード (どれでもよい) の IP アドレスを指定してください。

> ノードの IP は
>
> ```
> kubectl get node -o wide
> ```
>
> などとすることで調べられます。
>

`${PORT}` はイメージレジストリのポート番号です。デフォルトでは `30503` になっているはずです。

イメージにタグがついたなら、続いてこれをレジストリに送信します。

```
docker push ${YOUR_KNITFAB_NODE}:${PORT}/knitfab-first-train:v1.0
```

#### プラン定義をイメージから作成して、Knitfab に登録する

さて、Knitfab に対して、いま `docker push` したイメージをどう使いたいのか、ということを伝える必要があります。
このために、"プラン" の定義を作成して、それを Knitfab に送信しましょう。

"プラン" 定義のひな型は `knit` コマンドを使って生成できます。

```
docker save ${YOUR_KNITFAB_NODE}:${PORT}/knitfab-first-train:v1.0 | \
    knit plan template > ./knitfab-first-train.v1.0.plan.yaml
```

> [!Note]
>
> イメージが少々大きい (1GB+) ので、しばらく時間がかかります。

`knit plan template` コマンドが Docker イメージを解析して、"プラン" 定義のひな型を書き出します。
次のようなファイルが `./knitfab-first-train.v1.0.plan.yaml` として書き出されているはずです。

```yaml


# annotations (optional, mutable):
#   Set Annotations of this Plan in list of "key=value" format string.
#   You can use this for your own purpose, for example documentation. This does not affect lineage tracking.
#   Knitfab Extensions may refer this.
annotations: []
#   - "key=value"
#   - "description=This is a Plan for ..."


# image:
#   Container image to be executed as this Plan.
#   This image-tag should be accessible from your knitfab cluster.
image: "${YOUR_KNITFAB_NODE}:${PORT}/knitfab-first-train:v1.0"

# entrypoint:
#   Command to be executed as this Plan image.
#   This array overrides the ENTRYPOINT of the image.
entrypoint: ["python", "-u", "train.py"]

# args:
#   Arguments to be passed to this Plan image.
#   This array overrides the CMD of the image.
args: ["--dataset", "/in/dataset", "--save-to", "/out/model"]

# inputs:
#   List of filepath and Tags as Input of this Plans.
#   1 or more Inputs are needed.
#   Each filepath should be absolute. Tags should be formatted in "key:value"-style.
inputs:
  - path: "/in/dataset"
    tags:
      - "type:dataset"

# outputs:
#   List of filepathes and Tags as Output of this Plans.
#   See "inputs" for detail.
outputs:
  - path: "/out/model"
    tags:
      - "type:model"

# log (optional):
#   Set Tags stored log (STDOUT+STDERR of runs of this Plan) as Data.
#   If missing or null, log would not be stored.
log:
  tags:
    - "type:log"

# active (optional, mutable):
#   To suspend executing Runs by this Plan, set false explicitly.
#   If missing or null, it is assumed as true.
active: true

# resource (optional, mutable):
# Specify the resource , cpu or memory for example, requirements for this Plan.
# This value can be changed after the Plan is applied.

# There can be other resources. For them, ask your administrator.

# (advanced note: These values are passed to container.resource.limits in kubernetes.)
resources:

  # cpu (optional; default = 1):
  #   Specify the CPU resource requirements for this Plan.
  #   This value means "how many cores" the plan will use.
  #   This can be a fraction, like "0.5" or "500m" (= 500 millicore) for a half of a core.
  cpu: 1

  # memory (optional; default = 1Gi):
  #   Specify the memory resource requirements for this Plan.
  #   This value means "how many bytes" the plan will use.
  #   You can use suffixes like "Ki", "Mi", "Gi" for kibi-(1024), mebi-(1024^2), gibi-(1024^3) bytes, case sensitive.
  #   For example, "1Gi" means 1 gibibyte.
  #   If you omit the suffix, it is assumed as bytes.
  memory: 1Gi


# # on_node (optional):
# #   Specify the node where this Plan is executed.
# #
# #   For each level (may, prefer and must), you can put node labels or taints in "key=value" format.
# #   Labels show a node characteristic, and taints show a node restriction.
# #   Ask your administrator for the available labels/taints.
# #
# #   By default (= empty), this plan is executed on any node, if the node does not taint.
# on_node:
#   # may: (optional)
#   #   Allow to execute this plan on nodes with these taints, put here.
#   may:
#     - "label-a=value1"
#     - "label-b=value2"
#
#   # prefer: (optional)
#   #   Execute this plan on nodes with these labels & taints, if possible.
#   prefer:
#     - "vram=large"
#
#   # must: (optional)
#   #   Always execute this plan on nodes with these labels & taints
#   #   (taints on node can be subset of this list).
#   #
#   #   If no node matches, runs of the plan will be scheduled but not started.
#   must:
#     - "accelarator=gpu"
#
# # service_account (optional, mutable):
# #   Specify the service account to run this Plan.
# #   If missing or null, the service account is not used.
# service_account: "default"
```

一部、うまくない部分があるから、訂正しましょう。

- イメージ名の `${YOUR_KNITFAB_NODE}` の部分を `localhost` に書き換えます。
  - これで、あなたのコンテナを実行する Knitfab にとっての `localhost` にあるイメージ、という意味合いになります。
- 入力 `/in/dataset` に次の "タグ" を追加します。
    - `"project:first-knitfab"`
    - `"mode:training"`
- 出力 `/out/model` に次の "タグ" を追加します。
    - `"project:first-knitfab"`
    - `"description:2 layer CNN + 2 layer Affine"`
- ログに次の "タグ" を追加します。
    - `"project:first-knitfab"`

入力側の "タグ" は、先程 `knit data push` したデータを使うように、 "データ" と同じ "タグ" をここにも指定しました。
出力側には「何が書き出されているか」ということを記録するために、プロジェクトの名前 (`project`) とモデルの概略 (`description`) を書きました。

全体としては、次のような "プラン" 定義が得られます。今回は関係ないコメントアウト部分は削除しました。

```yaml
# image:
#   Container image to be executed as this Plan.
#   This image-tag should be accessible from your knitfab cluster.
image: "localhost:${PORT}/knitfab-first-train:v1.0"

# entrypoint:
#   Command to be executed as this Plan image.
#   This array overrides the ENTRYPOINT of the image.
entrypoint: ["python", "-u", "train.py"]

# args:
#   Arguments to be passed to this Plan image.
#   This array overrides the CMD of the image.
args: ["--dataset", "/in/dataset", "--save-to", "/out/model"]

# inputs:
#   List of filepath and Tags as Input of this Plans.
#   1 or more Inputs are needed.
#   Each filepath should be absolute. Tags should be formatted in "key:value"-style.
inputs:
  - path: "/in/dataset"
    tags:
      - "project:first-knitfab"
      - "type:dataset"
      - "mode:training"

# outputs:
#   List of filepathes and Tags as Output of this Plans.
#   See "inputs" for detail.
outputs:
  - path: "/out/model"
    tags:
      - "project:first-knitfab"
      - "type:model"
      - "description: 2 layer CNN + 2 layer Affine"

# log (optional):
#   Set Tags stored log (STDOUT+STDERR of runs of this Plan) as Data.
#   If missing or null, log would not be stored.
log:
  tags:
    - "project:first-knitfab"
    - "type:log"

# active (optional, mutable):
#   To suspend executing Runs by this Plan, set false explicitly.
#   If missing or null, it is assumed as true.
active: true

# resource (optional, mutable):
# Specify the resource , cpu or memory for example, requirements for this Plan.
# This value can be changed after the Plan is applied.

# There can be other resources. For them, ask your administrator.

# (advanced note: These values are passed to container.resource.limits in kubernetes.)
resources:

  # cpu (optional; default = 1):
  #   Specify the CPU resource requirements for this Plan.
  #   This value means "how many cores" the plan will use.
  #   This can be a fraction, like "0.5" or "500m" (= 500 millicore) for a half of a core.
  cpu: 1

  # memory (optional; default = 1Gi):
  #   Specify the memory resource requirements for this Plan.
  #   This value means "how many bytes" the plan will use.
  #   You can use suffixes like "Ki", "Mi", "Gi" for kibi-(1024), mebi-(1024^2), gibi-(1024^3) bytes, case sensitive.
  #   For example, "1Gi" means 1 gibibyte.
  #   If you omit the suffix, it is assumed as bytes.
  memory: 1Gi
```

これを、次のコマンドで Knitfab に送信します。

```
knit plan apply ./knitfab-first-train.v1.0.plan.yaml
```

すると、登録された "プラン" の情報が表示されます。次のような内容であるはずです。

```json
{
    "planId": "da6c4451-4886-4d78-9c20-aede6b288d22",
    "image": "localhost:30503/knitfab-first-train:v1.0",
    "entrypoint": [
        "python",
        "-u",
        "train.py"
    ],
    "args": [
        "--dataset",
        "/in/dataset",
        "--save-to",
        "/out/model"
    ],
    "inputs": [
        {
            "path": "/in/dataset",
            "tags": [
                "mode:training",
                "project:first-knitfab",
                "type:dataset"
            ],
            "upstreams": []
        }
    ],
    "outputs": [
        {
            "path": "/out/model",
            "tags": [
                "description:2 layer CNN + 2 layer Affine",
                "project:first-knitfab",
                "type:model"
            ],
            "downstreams": []
        }
    ],
    "log": {
        "tags": [
            "project:first-knitfab",
            "type:log"
        ],
        "downstreams": []
    },
    "active": true,
    "resources": {
        "cpu": "1",
        "memory": "1Gi"
    }
}
```

キー `planId` がこの "プラン" を一意に特定する ID です。

### 待つ

ここまできたら、あとは待つだけです。

時々 `knit run find -p ${PLAN_ID}` を実行して、"ラン" が生成されていること、状態が変化してゆくことを監視しておきましょう。
`${PLAN_ID}` には、`knit plan apply` の結果に含まれている planId を指定してください。

次のようなコンソール出力が得られるでしょう。

```json
[
    {
        "runId": "c9441be1-438a-42bd-ab45-61763ea09c1d",
        "status": "running",
        "updatedAt": "2024-11-19T05:25:23.911+00:00",
        "plan": {
            "planId": "da6c4451-4886-4d78-9c20-aede6b288d22",
            "image": "localhost:30503/knitfab-first-train:v1.0",
            "entrypoint": [
                "python",
                "-u",
                "train.py"
            ],
            "args": [
                "--dataset",
                "/in/dataset",
                "--save-to",
                "/out/model"
            ]
        },
        "inputs": [
            {
                "path": "/in/dataset",
                "tags": [
                    "mode:training",
                    "project:first-knitfab",
                    "type:dataset"
                ],
                "knitId": "63685b22-f04b-478b-9fa0-9c0a4fd7314f"
            }
        ],
        "outputs": [
            {
                "path": "/out/model",
                "tags": [
                    "description:2 layer CNN + 2 layer Affine",
                    "project:first-knitfab",
                    "type:model"
                ],
                "knitId": "5dfd676c-9932-42c8-8b49-7c24929200c9"
            }
        ],
        "log": {
            "tags": [
                "project:first-knitfab",
                "type:log"
            ],
            "knitId": "8e35f658-3328-44ae-9905-92983e1d5869"
        }
    }
]
```

このうちキー `runId` がこの "ラン" を一意に特定します。

`status` が上例のように `running` になっていれば、この "ラン" は計算を始めています。

訓練のログは

```
knit run show --log ${RUN_ID}
```

で読むことができます。値 `${RUN_ID}` は、 `knit run find` で見つかった runId です。指定した ID の "ラン" についてログを表示できます。

### モデルをダウンロードする

訓練されたモデルを手元にダウンロードしましょう。

改めて "ラン" の状態を調べて、 `"status": "done"` になっていることを確認してください。

```
knit run show ${RUN_ID}
```

さて、次のような内容がコンソールに書き出されているはずです。

```json
{
    "runId": "c9441be1-438a-42bd-ab45-61763ea09c1d",
    "status": "done",
    "updatedAt": "2024-11-19T05:49:20.525+00:00",
    "exit": {
        "code": 0,
        "message": ""
    },
    "plan": {
        "planId": "da6c4451-4886-4d78-9c20-aede6b288d22",
        "image": "localhost:30503/knitfab-first-train:v1.0",
        "entrypoint": [
            "python",
            "-u",
            "train.py"
        ],
        "args": [
            "--dataset",
            "/in/dataset",
            "--save-to",
            "/out/model"
        ]
    },
    "inputs": [
        {
            "path": "/in/dataset",
            "tags": [
                "mode:training",
                "project:first-knitfab",
                "type:dataset"
            ],
            "knitId": "63685b22-f04b-478b-9fa0-9c0a4fd7314f"
        }
    ],
    "outputs": [
        {
            "path": "/out/model",
            "tags": [
                "description:2 layer CNN + 2 layer Affine",
                "project:first-knitfab",
                "type:model"
            ],
            "knitId": "5dfd676c-9932-42c8-8b49-7c24929200c9"
        }
    ],
    "log": {
        "tags": [
            "project:first-knitfab",
            "type:log"
        ],
        "knitId": "8e35f658-3328-44ae-9905-92983e1d5869"
    }
}
```

このうち `outputs` にかかれている内容が、この "ラン" が実際に出力した "データ" です。
`knitId` が Knitfab 内の "データ" を一意に特定する ID を示しています。

モデルを書き出したのは `"path": "/out/model"` である出力でした。
その `knitId` を指定して、 "データ" としてモデルをダウンロードします。

```
mkdir -p ./knitfab/out/model
knit data pull -x ${KNIT_ID} ./knitfab/out/model
```

こうすると、ディレクトリ `./knitfab/out/model/${KNIT_ID}` に、出力された "データ" の内容が書き出されることになります。

チュートリアル2: モデルの性能を評価する
------------------

### 評価スクリプトの動作確認

`./scripts/validation.py` を使うと、モデルを使った推論ができます。
これも `validation/Dockerfile` を使ってコマンド起動用のイメージをビルドできます。

```
docker build -t knitfab-first-validation:v1.0 -f ./scripts/validation/Dockerfile ./scripts
```

この Dockerfile の内容は次の通りです。

```Dockerfile
FROM python:3.11

WORKDIR /work

RUN pip install numpy==1.26.4 && \
    pip install torch==2.2.1 --index-url https://download.pytorch.org/whl/cpu

COPY . .

ENTRYPOINT [ "python", "-u", "validation.py", "--dataset", "/in/dataset", "--model", "/in/model/model.pth" ]
```

訓練側とよく似ています。違う点は

- 実行するスクリプトファイル名が `validation.py` であること。
  - これが評価用スクリプトです。
- コマンドラインフラグから `--save-to` がなくなり、代わりに `--model` が増えていること。
  - このファイルパスからモデルを読み込みます。

さらに、`validation.py` は `--id` という引数を渡すとその画像番号の画像についてのみ推論するようにできています。

まずはこのイメージを使って、本当に推論がうまくいっているのか様子を見てみましょう。
評価用データセットとモデルをマウントして動作を見ればよいので...

```
docker run -it --rm -v "$(pwd)/data/qmnist-test:/in/dataset" -v "$(pwd)/knitfab/out/model/${KNIT_ID}:/in/model" knitfab-first-validation:v1.0 --id IMAGE_ID
```

としたらよいですね。(`${KNIT_ID}`の部分は自分の環境に合わせて適宜書き換えてください)

たとえば `--id 1` とすると、

```
img shape torch.Size([60000, 28, 28])
label shape torch.Size([60000])
=== image ===



            ####
         ########
        #########
        ###    ###
        ##     ##
              ###
              ###
             ###
            ####
           ####
           ###
          ####
          ###
         ####
        ####
        ###
        ###           ####
        ##################
        ################
             #####





=== ===== ===
Prediction: tensor([2]), Ground Truth: 2
```

このような結果が得られるでしょう。指定した ID の画像がアスキーアートとして表示され、続いて予測(Prediction)と正解(Ground Truth)が示されています。

上記の例では画像内容も、モデルの予測と正解も"2"で一致しているので、正しく推論できている、といえます。

では次に、このモデルをテスト用データセットで評価するタスクを Knitfab で実施してみましょう。

やるべきことは訓練時とかわりません。

- データセットを Knitfab に登録する (`knit data push`)
- イメージを `docker push` する
- "プラン" 定義を作成して、Knitfab に登録する (`knit plan apply`)

### データセットを登録する

今回はテスト用データセットを "データ" として登録ましょう。

既にダウンロードまでは済んでいるので、あとは登録するだけです。

```
knit data push -t format:mnist -t mode:test -t type:dataset -t project:first-knitfab -n ./data/qmnist-test
```

### 評価用イメージを push する

ビルドは先程したので、これに Knitfab のクラスタ内レジストリ用にタグをセットして `docker push` したらよいです。

```
docker tag knitfab-first-validation:v1.0 ${YOUR_KNITFAB_NODE}:${PORT}/knitfab-first-validation:v1.0

docker push ${YOUR_KNITFAB_NODE}:${PORT}/knitfab-first-validation:v1.0
```

### プランを作成して登録する

作成したイメージに基づいて、"プラン" のひな型を得ましょう。

```
docker save ${YOUR_KNITFAB_NODE}:${PORT}/knitfab-first-validation:v1.0 | knit plan template > ./knitfab-first-validation.v1.0.plan.yaml
```

次のような内容のファイルが得られるはずです。

```yaml


# annotations (optional, mutable):
#   Set Annotations of this Plan in list of "key=value" format string.
#   You can use this for your own purpose, for example documentation. This does not affect lineage tracking.
#   Knitfab Extensions may refer this.
annotations: []
#   - "key=value"
#   - "description=This is a Plan for ..."


# image:
#   Container image to be executed as this Plan.
#   This image-tag should be accessible from your knitfab cluster.
image: "${YOUR_KNITFAB_NODE}:${PORT}/knitfab-first-validation:v1.0"

# entrypoint:
#   Command to be executed as this Plan image.
#   This array overrides the ENTRYPOINT of the image.
entrypoint: ["python", "-u", "validation.py", "--dataset", "/in/dataset", "--model", "/in/model/model.pth"]

# args:
#   Arguments to be passed to this Plan image.
#   This array overrides the CMD of the image.
args: []

# inputs:
#   List of filepath and Tags as Input of this Plans.
#   1 or more Inputs are needed.
#   Each filepath should be absolute. Tags should be formatted in "key:value"-style.
inputs:
  - path: "/in/dataset"
    tags:
      - "type:dataset"
  - path: "/in/model/model.pth"
    tags:
      - "type:model.pth"

# outputs:
#   List of filepathes and Tags as Output of this Plans.
#   See "inputs" for detail.
outputs: []

# log (optional):
#   Set Tags stored log (STDOUT+STDERR of runs of this Plan) as Data.
#   If missing or null, log would not be stored.
log:
  tags:
    - "type:log"

# active (optional, mutable):
#   To suspend executing Runs by this Plan, set false explicitly.
#   If missing or null, it is assumed as true.
active: true

# resource (optional, mutable):
# Specify the resource , cpu or memory for example, requirements for this Plan.
# This value can be changed after the Plan is applied.

# There can be other resources. For them, ask your administrator.

# (advanced note: These values are passed to container.resource.limits in kubernetes.)
resources:

  # cpu (optional; default = 1):
  #   Specify the CPU resource requirements for this Plan.
  #   This value means "how many cores" the plan will use.
  #   This can be a fraction, like "0.5" or "500m" (= 500 millicore) for a half of a core.
  cpu: 1

  # memory (optional; default = 1Gi):
  #   Specify the memory resource requirements for this Plan.
  #   This value means "how many bytes" the plan will use.
  #   You can use suffixes like "Ki", "Mi", "Gi" for kibi-(1024), mebi-(1024^2), gibi-(1024^3) bytes, case sensitive.
  #   For example, "1Gi" means 1 gibibyte.
  #   If you omit the suffix, it is assumed as bytes.
  memory: 1Gi


# # on_node (optional):
# #   Specify the node where this Plan is executed.
# #
# #   For each level (may, prefer and must), you can put node labels or taints in "key=value" format.
# #   Labels show a node characteristic, and taints show a node restriction.
# #   Ask your administrator for the available labels/taints.
# #
# #   By default (= empty), this plan is executed on any node, if the node does not taint.
# on_node:
#   # may: (optional)
#   #   Allow to execute this plan on nodes with these taints, put here.
#   may:
#     - "label-a=value1"
#     - "label-b=value2"
#
#   # prefer: (optional)
#   #   Execute this plan on nodes with these labels & taints, if possible.
#   prefer:
#     - "vram=large"
#
#   # must: (optional)
#   #   Always execute this plan on nodes with these labels & taints
#   #   (taints on node can be subset of this list).
#   #
#   #   If no node matches, runs of the plan will be scheduled but not started.
#   must:
#     - "accelarator=gpu"
#
# # service_account (optional, mutable):
# #   Specify the service account to run this Plan.
# #   If missing or null, the service account is not used.
# service_account: "default"
```

これを訂正して、意味のあるものにしましょう。

- イメージ名の `${YOUR_KNITFAB_NODE}` を `localhost` に書き換えます。
- 1 番目の入力について
  - タグを追加します。
    - `"mode:test"`
    - `"project:first-knitfab"`
- 2 番目の入力が誤っているので、訂正します。
  - `path` にはディレクトリを指定する必要があります。ファイル名を除去します。(`"/in/model/model.pth"` -> `"/in/model"`)
  - タグを追加/訂正して、訓練で生成されたモデルパラメータを含む "データ" を取り込むようにします。
    - `"type:model.pth"` -> `"type:model"`
    - `"project:first-knitfab"`
- ログについて:
  - タグを追加します。
    - `"project:first-knitfab"`
    - `"type:validation"`

全体として、次のようになります。

```yaml
# image:
#   Container image to be executed as this plan.
#   This image-tag should be accessible from your Knitfab cluster.
image: "localhost:${PORT}/knitfab-first-validation:v1.0"

# inputs:
#   List of filepath and tags as input of this plans.
#   1 or more inputs are needed.
#   Each filepath should be absolute. Tags should be formatted in "key:value"-style.
inputs:
  - path: "/in/dataset"
    tags:
      - "type:dataset"
      - "mode:test"
      - "project:first-knitfab"
  - path: "/in/model"
    tags:
      - "type:model"
      - "project:first-knitfab"

# outputs:
#   List of filepathes and tags as output of this plans.
#   See "inputs" for detail.
outputs: []

# log (optional):
#   Set tags stored log (STDOUT+STDERR of runs of this plan) as data.
#   If missing or null, log would not be stored.
log:
  tags:
    - "type:log"
    - "type:validation"
    - "project:first-knitfab"

# active (optional):
#   To suspend executing runs by this plan, set false explicitly.
#   If missing or null, it is assumed as true.
active: true

# resource (optional):
# Specify the resource , cpu or memory for example, requirements for this plan.
# This value can be changed after the plan is applied.

# There can be other resources. For them, ask your administrator.

# (advanced note: These values are passed to container.resource.limits in kubernetes.)
resources:
  # cpu (optional; default = 1):
  #   Specify the CPU resource requirements for this plan.
  #   This value means "how many cores" the plan will use.
  #   This can be a fraction, like "0.5" or "500m" (= 500 millicore) for half a core.
  cpu: 1

  # memory (optional; default = 1Gi):
  #   Specify the memory resource requirements for this plan.
  #   This value means "how many bytes" the plan will use.
  #   You can use suffixes like "Ki", "Mi", "Gi" for kibi-(1024), mebi-(1024^2), gibi-(1024^3) bytes, case sensitive.
  #   For example, "1Gi" means 1 gibibyte.
  #   If you omit the suffix, it is assumed as bytes.
  memory: 1Gi
```

この内容で Knitfab に登録します。

```
knit plan apply ./knitfab-first-validation.v1.0.plan.yaml
```

すると、Knitfab は先程生成したモデルパラメータと、新しく指定したデータセットの組み合わせから "ラン" を生成して実行します。

- `knit run find -p ${PLAN_ID}` で監視してみましょう。
- `knit run show --log ${RUN_ID}` でログを見てみましょう。

そのうちに、評価を実施している "ラン" が `"status": "done"` になるでしょう。
改めてログを読んで、訓練がうまくいったことを確認しましょう。

```
Accuracy (at 10000 images): 0.9629
Accuracy (at 20000 images): 0.96095
Accuracy (at 30000 images): 0.9602
Accuracy (at 40000 images): 0.9604
Accuracy (at 50000 images): 0.95974
Accuracy (at 60000 images): 0.95985

=== Validation Result ===
Accuracy: 0.95985
```

チュートリアル3: 全体を見渡す
---------------

最後に、ここまでの実験によって生成してきたリネージや、"プラン" によって構築されたパイプラインを確認しましょう。

### 必要なツール

このセクションでは、新しく `dot` (graphviz) を利用します。
必要に応じインストールしてください。

### リネージを見渡す

リネージを確認しましょう。

ある "データ" に関するリネージ全体は

```
knit data lineage -n all ${KNIT_ID} | dot -T png -o ./lineage-graph.png
```

で調べることができます。

`knit data lineage` は、指定した `${KNIT_ID}` を起点にして dot フォーマットでリネージグラフを書き出すコマンドです。

これを graphviz の `dot` コマンドに通して、PNG ファイルとして書き出させると、次のような画像としてリネージグラフを観察できます。

![lineage graph](images/lineage-graph.png)

"ラン" に対する "データ" の入出力の流れが見て取れるでしょう。

### パイプラインを見渡す

これまでのチュートリアルで見てきた通り、Knitfab では、複数の "プラン" の間の依存関係から機械学習タスクパイプラインが構成されます。

ある "プラン" に関わるパイプライン全体は

```
knit plan graph -n all ${PLAN_ID} | dot -T png -o ./plan-graph.png
```

で調べることができます。

`knit plan graph` は指定した `${PLAN_ID}` を起点にして、dot フォーマットで "プラン" のつながりを示した図である "プラングラフ" を書き出すコマンドです。

これを graphviz の `dot` コマンドに通して、PNG ファイルとして書き出させると、次のような画像としてプラングラフを観察できます。

![plan-graph](images/plan-graph.png)

リネージグラフが *実施された* 機械学習タスクの流れを "データ" と "ラン" の関係として表現しているのに対して、このプラングラフは今後新しく "データ" が増えた際に *実施されるであろう* 機械学習タスクの流れを、"プラン" の関係として示しています。

まとめ
-----

これで本書の内容は終了です。

> [!Note]
>
> 必要に応じ、Knitfab や kubernetes クラスタをアンインストール/破棄してください。

本書で扱った内容は:

- Knitfab の簡易的なインストールを実施しました。
- Knitfab を使ってモデルの訓練をしました。
- Knitfab を使ってモデルの評価をしました。
- Knitfab では、モデルの訓練も評価も、「 "データ" と "プラン" を登録するだけ」で自動的に実施されることを確認しました。

さらなる詳細については、ユーザガイドならびに運用ガイドを参照してください。
