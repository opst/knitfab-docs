import configargparse
import json
import pathlib
import os
import pandas as pd
from typing import Any
from sklearn.datasets import fetch_20newsgroups
import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoProcessor,
    TrainingArguments,
    BitsAndBytesConfig,
    DataCollatorWithPadding,
)
from datasets import Dataset
from peft import LoraConfig
from trl import SFTTrainer

def parse_arguments() -> configargparse.Namespace:
    parser = configargparse.ArgumentParser(
        description="Fine-tune model for news classification"
    )
    parser.add_argument(
        "--config-file",
        type=pathlib.Path,
        help="Path to configuration JSON file.",
    )
    parser.add_argument(
        "--save-to",
        type=pathlib.Path,
        default=NewsClassifierFineTuner.DEFAULT_SAVE_DIRECTORY,
        help="Directory to save model and logs.",
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default=NewsClassifierFineTuner.DEFAULT_BASE_MODEL,
        help="Base model name.",
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default=NewsClassifierFineTuner.DEFAULT_DEVICE,
        help="Device to run inference on (cuda/cpu)"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=NewsClassifierFineTuner.DEFAULT_EPOCHS,
        help="Number of training epochs.",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=NewsClassifierFineTuner.DEFAULT_LEARNING_RATE,
        help="Learning rate.",
    )
    
    args = parser.parse_args()

    if args.config_file:
        with open(args.config_file, "r") as f:
            config = json.load(f)
        for key, value in config.items():
            setattr(args, key.replace("-", "_"), value)

    return args

class NewsClassifierFineTuner:
    DEFAULT_BASE_MODEL: str = "openai-community/gpt2"
    DEFAULT_SAVE_DIRECTORY: str = "./out"
    DEFAULT_DEVICE: str = "auto"
    DEFAULT_EPOCHS: int = 1
    DEFAULT_LEARNING_RATE: float = 2e-5

    def __init__(self, args: configargparse.Namespace) -> None:
        self.args: configargparse.Namespace = args
        self.tokenizer: Any = None
        self.model: Any = None
        self.train_dataset: Dataset | None = None
        self.eval_dataset: Dataset | None = None
        self.trainer: SFTTrainer | None = None
        self.eval_results: dict[str, Any] = {}
        self.num_labels: int = 20

    def setup_environment(self) -> None:        
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.args.base_model,
            num_labels=self.num_labels,
            quantization_config=quant_config,
            device_map=args.device,
        )
        self.tokenizer = AutoProcessor.from_pretrained(self.args.base_model)
        self.tokenizer.pad_token = self.tokenizer.eos_token

    def prepare_datasets(self, dataset: Any) -> Dataset:
        def tokenize(examples):
            return self.tokenizer(examples["text"], truncation=True)
        df: pd.DataFrame = pd.DataFrame(
            {
                "text": dataset.data,
                "label": dataset.target,
            }
        )

        df_cleaned: pd.DataFrame = df.dropna(subset=["text"])
        df_cleaned = df_cleaned[df_cleaned["text"].str.strip() != ""]

        dataset = Dataset.from_pandas(df_cleaned)
        tokenized_dataset = dataset.map(tokenize, batched=True)
        
        return tokenized_dataset

    def load_train_datasets(self) -> None:
        raw_train_dataset = fetch_20newsgroups(subset="train")
        self.train_dataset = self.prepare_datasets(raw_train_dataset)

    def load_eval_datasets(self) -> None:
        raw_eval_dataset = fetch_20newsgroups(subset="test")
        self.eval_dataset = self.prepare_datasets(raw_eval_dataset)

    def setup_trainer(self) -> None:
        training_args = TrainingArguments(
            output_dir=self.args.save_to,
            logging_dir=f"{self.args.save_to}/logs",
            num_train_epochs=self.args.epochs,
            per_device_train_batch_size=1,
            per_device_eval_batch_size=1,
            gradient_accumulation_steps=2,
            learning_rate=self.args.learning_rate,
            weight_decay=0.05,
            max_grad_norm=0.3,
            fp16=True,
            bf16=False,
            warmup_ratio=0.1,
            lr_scheduler_type="cosine",
            logging_strategy="steps",
        )

        peft_config = LoraConfig(
            lora_alpha=16,
            lora_dropout=0.1,
            r=64,
            bias="none",
            task_type="SEQ_CLS",
        )

        collator = DataCollatorWithPadding(tokenizer=self.tokenizer, padding="max_length")

        self.trainer = SFTTrainer(
            model=self.model,
            args=training_args,
            peft_config=peft_config,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            tokenizer=self.tokenizer,
            data_collator=collator,
        )

    def save_results(self) -> None:
        model_dir = os.path.join(self.args.save_to, "model")
        metrics_dir = os.path.join(self.args.save_to, "metrics")
        os.makedirs(model_dir, exist_ok=True)
        os.makedirs(metrics_dir, exist_ok=True)

        self.trainer.model.save_pretrained(model_dir)
        self.trainer.model.config.save_pretrained(model_dir)
        self.trainer.tokenizer.save_pretrained(model_dir)

        metrics_path = os.path.join(metrics_dir, f"metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(self.eval_results, f, indent=4)

        print(f"Model and evaluation results saved to {model_dir}")
        print(f"Evaluation metrics saved to {metrics_path}")

    def run(self) -> None:
        try:
            self.setup_environment()
            self.load_train_datasets()
            self.load_eval_datasets()
            self.setup_trainer()
            self.trainer.train()
            self.eval_results = self.trainer.evaluate()
            self.save_results()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    args = parse_arguments()
    os.makedirs(args.save_to, exist_ok=True)
    fine_tuner = NewsClassifierFineTuner(args)
    fine_tuner.run()
