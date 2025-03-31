#!/bin/bash

export CUDA_HOME=/usr/local/cuda-12.1

BASE_LOG_DIR=/path/to/logs

DATASETS=("imagenet" "cifar10" "mnist" "custom_dataset")
MODELS=("resnet50" "vit" "transformer" "alexnet")

#@submit
for idx in "${!DATASETS[@]}"; do  
  for model_idx in "${!MODELS[@]}"; do    

    DATASET=${DATASETS[$idx]}
    MODEL=${MODELS[$model_idx]}
    LOG_DIR="$BASE_LOG_DIR/$(echo "$DATASET" | tr '[:upper:]' '[:lower:]')/$MODEL"
    
    #@task
    echo "Processing Dataset: $(echo "$DATASET" | tr '[:lower:]' '[:upper:]')"  # Uppercase the dataset name
    echo "Model (short): ${MODEL:0:3}"        # First three letters of model name
    echo "Log Directory: ${LOG_DIR}"

    # Execute training command
    python train.py --dataset "$DATASET" \
                    --model "$MODEL" \
                    --cuda-home "$CUDA_HOME" \
                    --log-dir "$LOG_DIR"
    #@end
  done
done
#@end

echo "All tasks completed successfully."
