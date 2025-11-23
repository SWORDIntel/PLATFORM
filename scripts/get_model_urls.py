
import yaml
import sys
import os

def main():
    """
    Parses the models.yaml file and prints Hugging Face URLs for download.
    Skips any models marked as 'custom'.
    """
    # Construct the path to the config file relative to the script location
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'models.yaml')
    
    try:
        with open(config_path, 'r') as f:
            models_config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found.", file=sys.stderr)
        sys.exit(1)

    # Base URL for Hugging Face model repositories
    base_url = "https://huggingface.co"

    for category in models_config.get('models', {}).values():
        for model_details in category.values():
            canonical_name = model_details.get('canonical')
            # Ensure a canonical name exists and it's not a custom/local model
            if canonical_name and not canonical_name.startswith("custom/"):
                print(f"{base_url}/{canonical_name}")

if __name__ == "__main__":
    main()
