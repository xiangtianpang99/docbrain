import os
import shutil
from sentence_transformers import SentenceTransformer

def download_model():
    model_name = "all-MiniLM-L6-v2"
    # Define local path relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(project_root, "models")
    model_path = os.path.join(models_dir, model_name)

    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

    print(f"Downloading {model_name} to {model_path}...")
    
    # This will download the model and save it to the specified path
    model = SentenceTransformer(model_name)
    model.save(model_path)
    
    print(f"Model saved to: {model_path}")
    print("Download complete.")

if __name__ == "__main__":
    download_model()
