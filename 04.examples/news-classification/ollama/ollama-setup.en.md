### Instruction
# Configuring a Local LLM with Ollama for LLM-as-a-Judge Evaluation
This guide demonstrates how to set up a local Large Language Model (LLM) using Ollama for LLM-as-a-Judge evaluation. By running the LLM locally within Ollama, you can use it as the evaluator in your LLM-as-a-Judge process. This setup facilitates both local testing and seamless integration into a Knitfab evaluation pipeline.

### Overview
#### What is LLM-as-a-Judge?
LLM-as-a-Judge utilizes the power of Large Language Models (LLMs) to assess the performance of other AI models. This innovative approach provides near human-level evaluation while offering substantial cost and time savings compared to traditional methods.

For example, in our news classification case study, LLM-as-a-Judge was used to evaluate a fine-tuned GPT-2 model. Instead of relying solely on traditional metrics, the LLM was prompted to assess the model's performance by evaluating the relevance of the predicted news category to the actual category, expressed in natural language. This allowed for a more nuanced and qualitative assessment of the model's accuracy.

#### Setting up Ollama
This guide covers configuring a local LLM as the evaluator using Ollama. We will walk through deploying Ollama using Docker for local testing and Kubernetes for integration within Knitfab. This allows you to validate the LLM-as-a-Judge evaluation locally before deploying it to your production environment.

We'll cover two deployment scenarios:

- **Docker (Local Testing)**: This option allows you to quickly set up and test the LLM-as-a-Judge functionality on your local machine.
- **Kubernetes (Knitfab Integration)**: This option enables seamless integration of the LLM-as-a-Judge into your Knitfab processing pipeline.

### Prerequisites
To successfully complete this instruction, ensure you have met the following prerequisites:

- **GPU:** Ollama relies on GPUs for efficient operation. CPU-only operation is extremely slow and impractical for real-world use.
- **`Docker`**: Essential for local setup and testing of the LLM-as-a-Judge functionality.
- **Knitfab Kubenetes cluster access**: You'll need appropriate permissions to deploy Ollama to the Knitfab Kubernetes cluster. Contact your administrator for assistance.
- **`kubectl`**: This command-line tool is necessary for deploying Ollama to your Knitfab Kubernetes cluster.

### Repository
To access the files and directories used in this instruction, clone the `knitfab-docs` repository from GitHub:
```bash
git clone https://github.com/opst/knitfab-docs.git
```
Once cloned, navigate to the `04.examples/news-classification/ollama` directory. You will find the following:
- **`ollama.yaml`:** This YAML file provides the template for deploying Ollama to Kubernetes.

### Task
- [Task 1: Deploy Ollama to a Docker Container.](#step-1-deploy-ollama-app-to-docker-container)
- [Task 2: Deploy Ollama to Kubenetes.](#step-2-deploy-ollama-app-to-kubenetes)

## Task 1: Deploy Ollama to a Docker Container.
This section involves setting up Ollama in a Docker container to verify the LLM-as-a-judge evaluation image ( e.g., `news-classification-evaluate:v1.0` for the news classification case study) before deploying it to Knitfab. This allows for local testing and validation of the LLM-as-a-Judge functionality.

### 1. Create a Docker Network:
```bash
docker network create ollama-net
```
This command creates a Docker network named `ollama-net`, which will allow the Ollama container to communicate with other containers on the same network.

### 2. Run the Ollama Docker Container:
```bash
docker run -d --gpus all --network ollama-net \ 
           -v ollama:/root/.ollama -p 11434:11434 \
           --name ollama ollama/ollama
```
This command runs the Ollama Docker image in detached mode (`-d`).

- `--gpus all`: This option makes all available GPUs accessible to the container. If you want to specify particular GPUs, consult the Docker documentation.
- `--network ollama-net`: This connects the container to the `ollama-net` network.
- `-v ollama:/root/.ollama`: This mounts a Docker volume named `ollama` to the `/root/.ollama` directory inside the container. This ensures that your Ollama models and data are persisted even if the container is stopped or removed.
- `-p 11434:11434`: This maps port `11434` on the host machine to port `11434` in the container, which is the default port Ollama uses.
- `--name ollama`: This assigns the name ollama to the container, making it easier to manage.
- `ollama/ollama`: This specifies the Docker image to use.

### 3. Pull the Llama 3.2 Model:
```bash
docker exec -it ollama ollama pull llama3.2
```
This command executes the `ollama pull llama3.2` command inside the running ollama container to download the Llama 3.2 model.  The `-it` flags provide an interactive terminal session within the container.

## Task 2: Deploy Ollama to Kubernetes
This section deploys and configures Ollama within your Kubernetes cluster. This deployment enables evaluation tasks running on Knitfab to access the local LLM and utilize it as the evaluator for LLM-as-a-Judge evaluations.

### 1. Define Deployment and Service resources:
> [!Note]
>
> For simplicity, this example deploys the Ollama Deployment and Service into the same namespace as Knitfab.
> For enhanced security, consider deploying Ollama to a separate namespace. If you choose this approach, ensure your DNS query pointing to correct namespace and confirm evaluation runs can access the Ollama service.

Create a YAML file defines an Ollama application deployment and service for a Kubernetes cluster.  Save this content as `ollama.yaml`. Each section reponsible for:
- **Deploys Ollama:** Creates a single Ollama pod using the `ollama/ollama` Docker image in the `knitfab` namespace.  It allocates 4 CPU cores, 5GB of memory, and 1 GPU to the pod.  Crucially, it downloads the `llama3.2` model on startup.

- **Creates a Service:** Exposes the Ollama application internally within the Kubernetes cluster on port `11434`, allowing other applications within the cluster to access it.

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

### 2. Deploy Ollama application:
> [!Note]
> 
> **Important Note Regarding GPU Access:** If you have only one GPU available in your Kubernetes cluster, you may need to enable GPU sharing features like Time-Slicing or Multi-Instance GPU (MIG) to allow multiple Pods, including your Ollama Pod, to access it concurrently.  Without these features, your Ollama Deployment might fail or be unable to utilize the GPU.
>
> For detailed instructions on configuring GPU sharing, please consult the official NVIDIA documentation:
>
> - [Time-Slicing](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)
> - [Multi-Instance GPU (MIG)](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-operator-mig.html)
>
> Once you've addressed any GPU sharing requirements (if applicable), you can proceed with deploying the Ollama application.

To deploy the Ollama application, execute the following commands:
```bash
kubectl apply -f ollama/ollama.yaml
```