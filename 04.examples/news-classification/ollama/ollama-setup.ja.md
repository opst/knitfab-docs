### Instruction
# LLM-as-a-Judge 評価器として Ollama を使用したローカル LLM の構成
本書では、LLM-as-a-Judge 評価器として Ollama を使用したローカル大規模言語モデル (LLM) を設定する方法について説明します。ローカル LLM を評価器として設定することで、ニュース分類微調整済みの GPT-2 モデルをローカルで動作確認でき、更に Knitfab 評価 Plan への関連付けが可能になります。

### 概要
#### LLM-as-a-Judgeとは？
LLM-as-a-Judge は、LLM を活用して他のAIモデルを評価するし手法です。人間に近い品質で評価ができながらコストと時間を大幅に削減できるのは本手法と特徴となります。実際にニュース分類の事例では、LLM-as-a-Judge を使用して、微調整済みの GPT-2 モデルがニュース記事を分類能力を短時間に評価することができました。

#### Ollamaの構成
本書では、Ollamaを使用してローカル LLM 評価器を構築します。ローカルテストのために Ollama を Docker にデプロイし、その後、Knitfab Kubernetes に展開し Knitfab 上の評価 Plan と関連付けます。これにより、LLM-as-a-Judge 評価をローカルで検証から本番環境の実装までの一連の流れを確認できるようになります。

以下の 2 つの構成方法について説明します。

- **Docker（ローカルテスト）**: Ollama を Docker コンテナーに展開しローカルマシンで LLM-as-a-Judge 機能を用いて微調整済み LLM の性能評価ができます。
- **Kubernetes（Knitfab統合）**: Knitfab 上の評価 Plan と関連付け、評価タスクを自動化しながら、指標レポートなどの成果物を自動的に管理します。

### 前提条件
本手順を正常に完了するために、次の前提条件を満たしているかを確認してください。

- **GPU:** Ollama を効率に評価結果を生成するために GPU での実行が求められています。CPU で実行した場合、非効率で処理時間が大幅に長くなります。
- **`Docker`**: LLM-as-a-Judge のローカル構成とテストに必要です。
- **Knitfab Kubenetes クラスタへのアクセス**: Ollama を Knitfab Kubernetes クラスタに展開するには、適切な権限が必要です。事前に Knitfab 管理者に問い合わせしてください。
- **`kubectl`**: Ollama を Knitfab Kubernetes クラスタに展開するために必要なツールです。

### リポジトリ
本書で使用されるファイルとディレクトリは、GitHub の `knitfab-docs` リポジトリからをクローンできます。
```bash
git clone https://github.com/opst/knitfab-docs.git
```
クローンが完了したら、`04.examples/news-classification/ollama`ディレクトリ内にあるファイルを確認してください。
- **`ollama.yaml`:** Ollama を Kubernetes に展開するためのひな型を提供する YAML ファイル。

### タスク
- [タスク 1: Ollama を Docker コンテナに展開する](#タスク-1-Ollama-を-Docker-コンテナに展開する)
- [タスク 2: Ollama を Kubenetes に展開する](#タスク-2-Ollama-を-Kubenetes-に展開する)

## タスク 1: Ollama を Docker コンテナに展開する
この手順では、`news-classification-evaluate:v1.0` イメージを Knitfab に上げる前の検証として Ollama を Docker コンテナに展開し、ローカルテスト環境を設定します。

### 1. Dockerネットワークの作成:
```bash
docker network create ollama-net
```
このコマンドは、`ollama-net` という Docker ネットワークを作成します。これにより、Ollama コンテナは同じネットワーク上の他のコンテナと通信できます。

### 2. Ollama Docker コンテナの実行:
```bash
docker run -d --gpus all --network ollama-net \ 
           -v ollama:/root/.ollama -p 11434:11434 \
           --name ollama ollama/ollama
```
このコマンドは、Ollama Dockerイメージをデタッチモード（`-d`）で実行します。

- `--gpus all`: 利用可能なすべての GPU をコンテナにアクセス権を与えます。特定の GPU を指定したい場合は、Docker のドキュメントを参照してください。
- `--network ollama-net`: コンテナを `ollama-net` ネットワークに接続します。
- `-v ollama:/root/.ollama`: `ollama` のボリュームをコンテナ内の `/root/.ollama` ディレクトリに結びつけます。これにより、コンテナが停止または削除されても、Ollama モデルとデータが保持されます。
- `-p 11434:11434`: ホストマシンのポート `11434` をコンテナのポート `11434` に結びつけます。
- `--name ollama`: コンテナにollamaという名前を割り当てます。
- `ollama/ollama`: Dockerイメージを指定します。

### 3. Pull the Llama 3.2 Model:
```bash
docker exec -it ollama ollama pull llama3.2
```
このコマンドは、実行中の `ollama` コンテナ内で `ollama pull llama3.2` コマンドを実行して、Llama 3.2 モデルをダウンロードします。

## タスク 2: Ollama を Kubenetes に展開する
この手順では、Kubernetes クラスタに Ollama を展開ます。これにより、Knitfab で実行されている評価タスクがローカル LLM に接続し、LLM-as-a-Judge の評価器として使用できるようになります。

### 1. デプロイメントとサービスリソースの定義:
> [!Note]
>
> 本例では、わかりやすくするために Ollama デプロイメントとサービスをKnitfabと同じ名前空間に展開しています。
> セキュリティを強化するために、Ollama を別の名前空間に展開することを検討してください。その場合、ネットワーク接続と権限を適切に構成して、他名前空間にある評価タスクが Ollama に接続できるように確認してください。

Ollama アプリケーションの Kubernetes デプロイとサービスを定義し、`ollama.yaml` として保存します。各セクションは、次の役割を担います。
- **Ollama のデプロイ**: knitfab 名前空間で `ollama/ollama` Dockerイメージを使用して、単一のOllama ポッドを作成します。ポッドには、4 つの CPU コア、5GB のメモリ、1 つの GPU が割り当てられます。起動時に llama3.2 モデルをダウンロードします。

- **サービスの作成**: Kubernetes クラスタ内で Ollamaアプリケーションをポート `11434` で公開し、クラスタ内の他のアプリケーションが接続できるようにします。

`ollama.yaml`

```YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama
  namespace: knitfab
  labels:
    app: ollama
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ollama
  template:
    metadata:
      labels:
        app: ollama
    spec:
      containers:
        - name: ollama
          image: ollama/ollama
          resources:
            requests:
              cpu: "4"
              memory: "5Gi"
              nvidia.com/gpu: 1
            limits:
              cpu: "4"
              memory: "5Gi"
              nvidia.com/gpu: 1
          ports:
            - containerPort: 11434
          lifecycle:
            postStart:
              exec:
                command: ["sh", "-c", "ollama pull llama3.2"]
---
apiVersion: v1
kind: Service
metadata:
  name: ollama
  namespace: knitfab
spec:
  selector:
    app: ollama
  ports:
    - protocol: TCP
      port: 11434
      targetPort: 11434
  type: ClusterIP
```

### 2. Ollamaアプリケーションの展開:
> [!Note]
> 
> **GPU に関する重要な注意事項**: Kubernetes クラスタで使用可能な GPU が 1 つしかない場合は、Ollama ポッドを含む複数のポッドが同時に利用できるように、タイムスライシングやマルチインスタンス GPU（MIG）などの GPU 共有機能を有効にする必要がある場合があります。これらの機能が欠けていると、Ollama 展開が失敗したり、GPU を使用できなかったりする可能性があります。
>
> GPU 共有機能の構成については、NVIDIA の公式ドキュメントを参照してください。
>
> - [タイムスライシング](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)
> - [マルチインスタンス GPU（MIG）](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-operator-mig.html)
>
> GPU共有の要件（該当する場合）満たしたら、Ollama アプリケーションの展開に進んでください。

Ollama アプリケーションを展開するには、次のコマンドを実行します。
```bash
kubectl apply -f ollama/ollama.yaml
```