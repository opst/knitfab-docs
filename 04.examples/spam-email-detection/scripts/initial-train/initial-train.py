import argparse
import os
import pathlib
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument("--dataset", type=pathlib.Path, required=True)
parser.add_argument("--save-to", type=pathlib.Path, required=True)
args = parser.parse_args()

os.makedirs(args.save_to, exist_ok=True)

MODEL_PATH = args.save_to / 'pipeline.pkl'
DATA_PATH = args.dataset / 'train_data.csv'

def prepare_data(data):
    data = data.drop(columns=['Unnamed: 0', 'label'], axis=1)
    
    # Remove NaN values
    data = data.dropna()

    # Keep only rows where label_num is 0 or 1
    data = data[data['label_num'].isin([0, 1])]

    x = data['text']
    y = data['label_num']

    return x, y

# Function to load or train the model
def train_and_export_model(x_train, y_train, model_path):  
    print("Training a new model...")
    # Create a new pipeline
    pipeline = Pipeline([
        ('vectorizer', CountVectorizer()),
        ('classifier', MultinomialNB())
    ])

    # Train the pipeline
    pipeline.fit(x_train, y_train)
    
    # Save the updated pipeline
    joblib.dump(pipeline, model_path)
    print("Model updated with new data and saved.")

# Main script
if __name__ == "__main__":
    # Load the initial dataset
    data = pd.read_csv(DATA_PATH, encoding='latin-1')

    # Prepare the training and testing data
    x_train, y_train = prepare_data(data)

    # Train and export the model
    train_and_export_model(x_train, y_train, MODEL_PATH)