import argparse
import os
import pathlib
import pandas as pd
import joblib

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=pathlib.Path, required=True)
parser.add_argument("--model", type=pathlib.Path, required=True)
parser.add_argument("--save-to", type=pathlib.Path, required=True)
args = parser.parse_args()

os.makedirs(args.save_to.parent, exist_ok=True)

DATA_PATH = args.dataset / 'train_data.csv'
IN_MODEL_PATH = args.model / 'pipeline.pkl'
OUT_MODEL_PATH = args.save_to / 'pipeline.pkl'

def prepare_data(data):
    # Drop unnecessary columns if they exist
    data = data.drop(columns=[col for col in ['Unnamed: 0', 'label'] if col in data.columns], errors='ignore')
    
    # Remove NaN values
    data = data.dropna()
    
    # Keep only rows where label_num is 0 or 1
    data = data[data['label_num'].isin([0, 1])]

    x = data['text']
    y = data['label_num']

    return x, y

def train_and_export_model(x_train, y_train, in_model_path, out_model_path):
    try:
        print("Loading the existing model...")
        pipeline = joblib.load(in_model_path)

        # Update the model with new data
        pipeline.named_steps['classifier'].partial_fit(
            pipeline.named_steps['vectorizer'].transform(x_train),
            y_train,
            classes=[0, 1]
        )
        print("Model updated with new data.")

    except FileNotFoundError:
        raise FileNotFoundError(f"Model file not found at {in_model_path}. Please provide a valid pre-trained model path.")

    # Save the updated pipeline
    joblib.dump(pipeline, out_model_path)
    print(f"Model saved to {out_model_path}")

# Main script
if __name__ == "__main__":
    try:
        # Load the initial dataset
        data = pd.read_csv(DATA_PATH, encoding='latin-1')

        # Prepare the training data
        x_train, y_train = prepare_data(data)

        # Train and export the model
        train_and_export_model(x_train, y_train, IN_MODEL_PATH, OUT_MODEL_PATH)
    except Exception as e:
        print(f"Error: {e}")
