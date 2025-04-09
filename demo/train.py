import argparse
import time

from rich.console import Console

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None


def main():
    console = Console()

    parser = argparse.ArgumentParser(description="Dummy training script")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset name")
    parser.add_argument(
        "--dataset-description", type=str, required=True, help="Dataset description"
    )
    parser.add_argument("--model", type=str, required=True, help="Model type")
    parser.add_argument(
        "--cuda-home", type=str, required=True, help="CUDA installation path"
    )
    parser.add_argument("--log-dir", type=str, required=True, help="Log directory path")

    args = parser.parse_args()

    console.print("Training Configuration:", style="bold blue")
    console.print(f"  {'Dataset:':<22} {args.dataset}", style="green")
    console.print(
        f"  {'Dataset Description:':<22} {args.dataset_description}", style="green"
    )
    console.print(f"  {'Model:':<22} {args.model}", style="green")
    console.print(f"  {'CUDA Home:':<22} {args.cuda_home}", style="green")
    console.print(f"  {'Log Directory:':<22} {args.log_dir}", style="green")

    # Demo tqdm util
    if tqdm is not None:
        for _ in tqdm(range(5), desc="Training"):
            time.sleep(1)


if __name__ == "__main__":
    main()
