import argparse
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str)
    parser.add_argument("--model", type=str)
    parser.add_argument("--cuda-home", type=str)
    parser.add_argument("--log-dir", type=str)

    args = parser.parse_args()
    print(args)
    time.sleep(1)
