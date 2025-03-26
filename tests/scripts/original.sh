#!/bin/bash

export CUDA_HOME=/usr/local/cuda-12.1

#@submit
for dataset in imagenet cifar10 mnist; do
  for model in resnet50 vit transformer; do
    LOG_DIR=/path/to/logs/$dataset/$model

    #@task $dataset $model $LOG_DIR
    python train.py --dataset $dataset \
      --model $model \
      --cuda-home $CUDA_HOME \
      --log-dir $LOG_DIR
    #@end

  done
done
#@end

echo "done"
