import os
import json

def load_json_file(file_path):
    """Load a JSON file and return its contents."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def load_text_file(file_path):
    """Load a text file and return its contents."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def load_dataset(dataset_name):
    """Load a dataset based on its name."""
    datasets_dir = os.path.join(os.path.dirname(__file__), '../resources/datasets')
    dataset_path = os.path.join(datasets_dir, dataset_name)
    
    if dataset_name.endswith('.json'):
        return load_json_file(dataset_path)
    else:
        return load_text_file(dataset_path)