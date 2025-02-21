### マニュアル
# LLM-as-a-Judge 評価器として Ollama を使用したローカル LLM の構成
本書では、LLM-as-a-Judge 評価器として Ollama を用いたローカル大規模言語モデル (LLM) の構築方法について解説します。Ollama を導入することで、ファインチューニング済みモデルの LLM-as-a-judge 評価プロセスをローカル LLM で実行できるようになり、ローカル環境での試行と Knitfab 上での実装をスムーズに連携させることができます。

### 概要
#### LLM-as-a-Judgeとは？
LLM-as-a-Judge は、大規模言語モデル (LLM) を評価者として活用する AI モデルの評価手法です。従来の人間による評価と比較して、評価の品質を維持しながらコストと時間を大幅に削減できる点が大きな特徴です。

LLM-as-a-Judge を用いたニュース分類の事例では、ファインチューニング済みの GPT-2 モデルがニュース記事を分類する性能を、自然言語で構成された指標を用いて評価します。具体的には、LLM-as-a-Judge は予測されたカテゴリと正解の関連性を判断し、その結果に基づいてモデルの分類精度を評価します。

#### Ollamaの構成
本書では、Ollama を使用してローカル LLM 評価器を構築する方法を解説します。具体的にローカルでの試行と Knitfab への統合という 2 つの場面を想定し、それぞれに最適な Ollama の構成方法を紹介します。

- **Docker（ローカル試行）**: LLM-as-a-Judge の評価プロセスをローカルマシンで試行する際には、Ollama を Docker コンテナにデプロイします。これにより、手軽に環境を構築し、評価タスクがローカル LLM を評価器として利用できるようになります。
- **Kubernetes（Knitfab統合）**: Knitfab 上で LLM-as-a-Judge を実行する場合は、Kubernetes を使用して Ollama をデプロイします。Knitfab の評価 Plan と Ollama を連携させることで、評価 Plan が生成した Run が Ollama に接続し、ローカル LLM を用いてファインチューニング済みモデルを評価できるようになります。

### 前提条件
本マニュアルを正常に完了するために、次の前提条件を満たしているかを確認してください。

- **GPU:** Ollama は、特に大規模なモデルや複雑なタスクを扱う場合、GPU での実行を推奨します。CPU で実行した場合、処理速度が大幅に低下し、評価に時間がかかる可能性があります。
- **`Docker`**: LLM-as-a-Judge のローカル構成と試行に必要です。
- **Knitfab Kubenetes クラスタへのアクセス**: Ollama を Knitfab Kubernetes クラスタにデプロイするには、適切な権限が必要です。事前に Knitfab 管理者に問い合わせ、必要な権限を取得してください。
- **`kubectl`**: Ollama を Knitfab Kubernetes クラスタにデプロイするために必要なツールです。

### リポジトリ
本書で使用するファイルとディレクトリは、GitHub の `knitfab-docs` リポジトリからをクローンできます。
```bash
git clone https://github.com/opst/knitfab-docs.git
```
クローンが完了したら、`04.examples/news-classification/ollama`ディレクトリ内にあるファイルを確認してください。
- **`ollama.yaml`:** Ollama を Kubernetes にデプロイするためのひな型を提供する YAML ファイル。

### タスク
- [タスク 1: Ollama を Docker コンテナにデプロイする](#タスク-1-Ollama-を-Docker-コンテナにデプロイする)
- [タスク 2: Ollama を Kubenetes にデプロイする](#タスク-2-Ollama-を-Kubenetes-にデプロイする)

## タスク 1: Ollama を Docker コンテナにデプロイする
本章では、LLM-as-a-judge 評価イメージ (ニュース分類の事例では `news-classification-evaluate:v1.0` イメージに該当します) を Knitfab に登録する前の段階として、Ollama を Docker コンテナにデプロイし、ローカル環境での試行を準備します。

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

## タスク 2: Ollama を Kubenetes にデプロイする
本章ではでは、Kubernetes クラスタに Ollama をデプロイます。これにより、Knitfab で実行されている LLM-as-a-judge 評価タスクが Ollama に接続し、ローカル LLM を評価器として使用できるようになります。

### 1. デプロイメントとサービスリソースの定義:
> [!Note]
>
> 本例では、わかりやすくするために Ollama デプロイメントとサービスをKnitfabと同じ名前空間に配置しています。
> セキュリティを強化するために、Ollama を別の名前空間に配置することを検討してください。その場合、DNS クエリーを正しい名前空間に変更し、評価タスクが Ollama に接続できることを確認してください。

Ollama の Kubernetes デプロイメントとサービスを定義し、`ollama.yaml` として保存します。各セクションは、次の役割を担います。
- **Ollama のデプロイメント**: knitfab 名前空間で `ollama/ollama` Dockerイメージを使用して、単一のOllama ポッドを作成します。ポッドには、4 つの CPU コア、5GB のメモリ、1 つの GPU が割り当てられます。起動時に `llama3.2` モデルをダウンロードします。

- **Ollama のサービス**: Kubernetes クラスタ内で Ollama をポート `11434` で公開し、クラスタ内の他のアプリケーションが接続できるようにします。

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

### 2. Ollama のデプロイ:
> [!Note]
> 
> **GPU に関する重要な注意事項**: Kubernetes クラスタで使用可能な GPU が 1 つしかない場合は、Ollama ポッドを含む複数のポッドが同時に利用できるように、タイムスライシングやマルチインスタンス GPU（MIG）などの GPU 共有機能を有効にする必要がある場合があります。これらの機能が欠けていると、Ollama デプロイが失敗したり、GPU を使用できなかったりする可能性があります。
>
> GPU 共有機能の構成については、NVIDIA の公式ドキュメントを参照してください。
>
> - [タイムスライシング](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)
> - [マルチインスタンス GPU（MIG）](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-operator-mig.html)
>
> GPU共有の要件（該当する場合）満たしたら、Ollama のデプロイに進んでください。

Ollama をデプロイするには、次のコマンドを実行します。
```bash
kubectl apply -f ollama/ollama.yaml
```