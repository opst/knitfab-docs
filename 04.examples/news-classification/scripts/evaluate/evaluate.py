import configargparse
import json
import os
import pathlib
from typing import List
import torch
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval import evaluate
from deepeval.evaluate import EvaluationResult
from sklearn.datasets import fetch_20newsgroups
from transformers import pipeline, AutoModelForSequenceClassification, AutoProcessor

def parse_arguments():
    parser = configargparse.ArgumentParser(
        description="Evaluate fine-tuned model on news classification"
    )
    parser.add_argument(
        "--config-file",
        type=pathlib.Path,
        help="Path to configuration JSON file.",
    )
    parser.add_argument(
        "--model-path", 
        type=pathlib.Path, 
        default=TestGPT2Model.DEFAULT_MODEL_PATH,
        help="Path to the fine-tuned model"
    )
    parser.add_argument(
        "--save-to",
        type=pathlib.Path,
        default=TestGPT2Model.DEFAULT_SAVE_DIRECTORY,
        help="Directory to save model and logs.",
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default=TestGPT2Model.DEFAULT_DEVICE,
        help="Device to run inference on (cuda/cpu)"
    )
    parser.add_argument(
        "--num-samples", 
        type=int, 
        default=TestGPT2Model.DEFAULT_NUMBER_TEST_SAMPLES,
        help="Number of test samples to evaluate"
    )
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=TestGPT2Model.DEFAULT_TEST_PASS_THRESHOLD,
        help="Deepeval test threshold"
    )

    args = parser.parse_args()

    if args.config_file:
        with open(args.config_file, "r") as f:
            config = json.load(f)
        for key, value in config.items():
            setattr(args, key.replace("-", "_"), value)

    return args

def create_classifier(model_path: str, num_labels: int, device: str):
    try:
        model = AutoModelForSequenceClassification.from_pretrained(model_path, num_labels=num_labels)
        tokenizer = AutoProcessor.from_pretrained(model_path)

        return pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            device=device,
            max_length=970
        )
    except Exception as e:
        raise RuntimeError(f"Failed to create classifier: {e}")

def map_category(label: str, categories: List[str]) -> str:
    try:
        num = int(label.replace("LABEL_", ""))
        return categories[num] if 0 <= num < len(categories) else "Unknown"
    except (ValueError, IndexError):
        return "Unknown"
    
def get_test_cases(model_path: str, device: str, num_samples: int, num_labels:int) -> List[LLMTestCase]:
    raw_eval_dataset = fetch_20newsgroups(subset='test')
    categories = raw_eval_dataset.target_names
    
    data = raw_eval_dataset.data[:num_samples]
    target = raw_eval_dataset.target[:num_samples]

    classifier = create_classifier(model_path, num_labels, device)
    
    test_cases = []
    for text, category_idx in zip(data, target):
        try:
            expected_category = categories[category_idx]
            prompt = f"### [HUMAN] Classify this news article: '{text}'\n"
            
            actual_output = classifier(prompt)[0]["label"]
            actual_output = map_category(actual_output, categories)

            test_case = LLMTestCase(
                input=text,
                actual_output=actual_output,
                expected_output=expected_category,
            )
            test_cases.append(test_case)
        except Exception as e:
            print(f"Error processing test case: {e}")
            continue
    
    return test_cases

class TestGPT2Model:
    DEFAULT_MODEL_PATH: str = "./in/model"
    DEFAULT_SAVE_DIRECTORY: str = "./out"
    DEFAULT_DEVICE: str = "auto"
    DEFAULT_NUMBER_TEST_SAMPLES: int = 100
    DEFAULT_TEST_PASS_THRESHOLD: float = 0.8

    def __init__(self, args: configargparse.Namespace) -> None:
        self.args: configargparse.Namespace = args
        self.test_cases: LLMTestCase | None = None
        self.num_labels: int = 20
        self.eval_result: EvaluationResult | None = None

    @property
    def output_precision(self):
        return GEval(
            name="CategoryPrecision",
            threshold=self.args.threshold,
            criteria="Category classifier precision - determine if the actual output matched the provided expected output",
            evaluation_steps=[
                "Award 1.0 points for exact match between actual and expected category",
                "Award 0.5 points for semantically related categories (e.g., 'finance' for 'business')",
                "Award 0.0 points if categories are unrelated",
                "In case of multiple categories, evaluate only the most prominently stated category",
                "Deduct 0.5 points if category is ambiguously stated",
                "Deduct 0.2 points for each additional category present",
                "Multiple categories cannot result in a score higher than a single correct category",
                "Minimum score after penalties is 0.0",
            ],
            evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
        )

    def setup_class(self):
        self.test_cases = get_test_cases(
            self.args.model_path,
            self.args.device,
            self.args.num_samples,
            self.num_labels
        )

    def test_category_prediction(self):
        return evaluate(
            test_cases=self.test_cases,
            metrics=[self.output_precision],
            use_cache=True
        )
    
    def save_evaluate_result(self):
        os.makedirs(self.args.save_to, exist_ok=True)
        result_path = os.path.join(self.args.save_to, "deepeval-result.json")
        with open(result_path, "w") as f:
            json.dump(self.eval_result.model_dump(), f, indent=4)

    def run_test(self):
        self.setup_class()
        self.eval_result = self.test_category_prediction()
        self.save_evaluate_result()

if __name__ == "__main__":
    test_GPT2_instacne = TestGPT2Model(parse_arguments())
    test_GPT2_instacne.run_test()