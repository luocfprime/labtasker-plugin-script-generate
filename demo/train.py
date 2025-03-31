import argparse


def main():
    parser = argparse.ArgumentParser(description="Dummy training script")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset name")
    parser.add_argument("--model", type=str, required=True, help="Model type")
    parser.add_argument(
        "--cuda-home", type=str, required=True, help="CUDA installation path"
    )
    parser.add_argument("--log-dir", type=str, required=True, help="Log directory path")

    args = parser.parse_args()

    print("Training Configuration:")
    print(f"  Dataset: {args.dataset}")
    print(f"  Model: {args.model}")
    print(f"  CUDA Home: {args.cuda_home}")
    print(f"  Log Directory: {args.log_dir}")


if __name__ == "__main__":
    main()
