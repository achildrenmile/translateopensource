import os
import shutil
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer

def download_model(model_name="facebook/m2m100_418M", save_path="api/models/m2m100"):
    """Download and save the model files locally"""
    print(f"Downloading model and tokenizer from {model_name}...")
    
    # Remove existing model directory if it exists
    if os.path.exists(save_path):
        print(f"Removing existing model directory: {save_path}")
        shutil.rmtree(save_path)
    
    # Create directory
    os.makedirs(save_path, exist_ok=True)
    
    try:
        # Download and save tokenizer
        print("Downloading tokenizer...")
        tokenizer = M2M100Tokenizer.from_pretrained(model_name, force_download=True)
        tokenizer.save_pretrained(save_path)
        print("✓ Tokenizer saved successfully!")
        
        # Download and save model
        print("Downloading model (this might take a while)...")
        model = M2M100ForConditionalGeneration.from_pretrained(model_name, force_download=True)
        model.save_pretrained(save_path)
        print("✓ Model saved successfully!")
        
        # Verify the download
        print("\nVerifying downloaded files...")
        test_tokenizer = M2M100Tokenizer.from_pretrained(save_path)
        test_model = M2M100ForConditionalGeneration.from_pretrained(save_path)
        print("✓ Model verification successful!")
        
        print(f"\nModel and tokenizer saved to: {save_path}")
        return True
        
    except Exception as e:
        print(f"\nError occurred during download: {str(e)}")
        if os.path.exists(save_path):
            print(f"Cleaning up {save_path}")
            shutil.rmtree(save_path)
        return False

if __name__ == "__main__":
    success = download_model()
    if not success:
        print("\nDownload failed. Please try again.")
    else:
        print("\nDownload completed successfully!")