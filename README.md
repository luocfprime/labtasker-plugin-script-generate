# labtasker-plugin-script-generate

> [!WARNING]
> This plugin does not cover all possible scenarios and does not guarantee the correctness of the generated scripts. 
> **It is strongly advised to double-check and manually adjust the generated scripts to your need.**

This is a plugin for [Labtasker](https://github.com/luocfprime/labtasker) that
helps you to automatically split your bash script into submit script and job script.

## Install

```bash
pip install labtasker-plugin-script-generate
```

## Example

You can find the code in the [demo](./demo) directory.

Imagine you have a bash wrapper script for your machine learning experiment. To divide the script into a submit script
and a job script, simply add a few special comments (e.g., `#@submit`, `#@task`, `#@end`).

```diff
#!/bin/bash

export CUDA_HOME=/usr/local/cuda-12.1

+#@submit
for dataset in imagenet cifar10 mnist; do
  for model in resnet50 vit transformer; do
    LOG_DIR=/path/to/logs/$dataset/$model

+    #@task
    python train.py --dataset $dataset \
      --model $model \
      --cuda-home $CUDA_HOME \
      --log-dir $LOG_DIR
+    #@end

  done
done
+#@end

echo "done"
```

Run:

```bash
labtasker generate original.sh
```

You will see `original_submit.sh` and `original_run.sh` generated at the same directory, with
the following content:

### `original_submit.sh`:

```bash
#!/bin/bash
# This script is generated by Labtasker from original.sh

export CUDA_HOME=/usr/local/cuda-12.1

for dataset in imagenet cifar10 mnist; do
  for model in resnet50 vit transformer; do
    LOG_DIR=/path/to/logs/$dataset/$model

    labtasker task submit -- --CUDA_HOME "$CUDA_HOME" --LOG_DIR "$LOG_DIR" --dataset "$dataset" --model "$model"

  done
done

echo "done"
```

### `original_run.sh`:

```bash
#!/bin/bash
# This script is generated by Labtasker from original.sh

export CUDA_HOME=/usr/local/cuda-12.1

LABTASKER_TASK_SCRIPT=$(mktemp)
cat <<'LABTASKER_LOOP_EOF' > "$LABTASKER_TASK_SCRIPT"
CUDA_HOME=%(CUDA_HOME)
LOG_DIR=%(LOG_DIR)
dataset=%(dataset)
model=%(model)
    python train.py --dataset $dataset \
      --model $model \
      --cuda-home $CUDA_HOME \
      --log-dir $LOG_DIR
LABTASKER_LOOP_EOF
labtasker loop --executable /bin/bash --script-path $LABTASKER_TASK_SCRIPT

echo "done"
```
