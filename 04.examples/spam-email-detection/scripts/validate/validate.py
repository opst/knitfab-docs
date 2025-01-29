import argparse
from datetime import datetime
import json
import os
import pathlib
import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=pathlib.Path, required=True)
parser.add_argument("--save-to", type=pathlib.Path, required=True)
parser.add_argument("--model", type=pathlib.Path, required=True)
args = parser.parse_args()

os.makedirs(args.save_to, exist_ok=True)

DATA_PATH = args.dataset / 'validation_data.csv'
MODEL_PATH = args.model / 'pipeline.plk'
METRICS_PATH = args.save_to / 'metrics.json'

def prepare_data(data):
    data = data.drop(columns=['Unnamed: 0', 'label'], axis=1)
    
    # Remove NaN values
    data = data.dropna()

    # Keep only rows where label_num is 0 or 1
    data = data[data['label_num'].isin([0, 1])]

    x = data['text']
    y = data['label_num']

    return x, y
    
def load_model(model_path):
    if os.path.exists(model_path):
        return joblib.load(model_path)
    else:
        raise ValueError("Model not found at the specified path.")

def evaluate_model(pipeline, x_test, y_test, metrics_path):
    # Evaluate the new model
    y_pred = pipeline.predict(x_test)
    accuracy = accuracy_score(y_test, y_pred)
    conf_matrix = confusion_matrix(y_test, y_pred)
    class_report = classification_report(y_test, y_pred, output_dict=True)

    # Get the current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    metrics = {
        'timestamp': timestamp,
        'accuracy': accuracy,
        'confusion_matrix': conf_matrix.tolist(),
        'classification_report': class_report
    }

    # Write the updated data back to the file
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=4)

    print("Model evaluated and metrics saved.")

if __name__ == "__main__":
    # Load the initial dataset
    data = pd.read_csv(DATA_PATH, encoding='latin-1')

    x_test, y_test = prepare_data(data)
    # Load the model
    try:
        pipeline = load_model(MODEL_PATH)
    except ValueError as e:
        print(e)
        exit(1)
    
    # Evaluate the model
    evaluate_model(pipeline, x_test, y_test, METRICS_PATH)