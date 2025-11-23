
import sys
import os
import yaml

# Add the 'src' directory to the Python path to allow importing project modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from quantization_pipeline import QuantizationPipeline, QuantizationConfig
except ImportError as e:
    print(f"Error: Failed to import quantization modules. Make sure you have run setup.", file=sys.stderr)
    print(f"Details: {e}", file=sys.stderr)
    sys.exit(1)

def main():
    """
    Runs the quantization pipeline for all models defined in models.yaml,
    or for a specific model if provided as a command-line argument.
    """
    # Construct the path to the config file
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'models.yaml')
    try:
        with open(config_path, 'r') as f:
            models_config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: {config_path} not found.", file=sys.stderr)
        sys.exit(1)

    pipeline = QuantizationPipeline()
    models_to_quantize = []

    if len(sys.argv) > 1:
        # User specified a model to quantize
        model_name = sys.argv[1]
        print(f"Quantizing specific model: {model_name}...")
        # Verify the model exists in the config
        found = False
        for category in models_config.get('models', {}).values():
            if model_name in category:
                models_to_quantize.append(model_name)
                found = True
                break
        if not found:
            print(f"Error: Model '{model_name}' not found in config/models.yaml", file=sys.stderr)
            sys.exit(1)
    else:
        # If no model is specified, quantize all models from the config
        print("Quantizing all models from config/models.yaml...")
        for category in models_config.get('models', {}).values():
            for model_name in category.keys():
                models_to_quantize.append(model_name)

    print("-" * 50)
    for model_name in models_to_quantize:
        print(f"Processing: {model_name}")
        try:
            # Default to 'amx' as the target hardware since it supports most models.
            # This could be made more sophisticated by reading the target from the config.
            config = QuantizationConfig(target_hardware="amx")
            result = pipeline.quantize(model_name, None, config)

            if result and result.quantized_size_mb > 0:
                print(f"  └── SUCCESS")
                print(f"      Method: {result.quantization_method}, Target: {result.target_hardware}")
                print(f"      Size: {result.original_size_mb:.1f} MB -> {result.quantized_size_mb:.1f} MB (Compression: {result.compression_ratio:.2f}x)")
            else:
                print(f"  └── SKIPPED or FAILED (model may not be suitable or downloaded).")

        except Exception as e:
            print(f"  └── ERROR: Could not quantize {model_name}. Reason: {e}")
        print("-" * 50)

if __name__ == "__main__":
    main()
