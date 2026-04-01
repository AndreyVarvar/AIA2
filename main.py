from src.jpeg import jpeg, ijpeg
from src.huffman import huffman_file, ihuffman_file
from src.rle import rle_file, irle_file

import os
import time
import filecmp
import pprint
import json

# we need to take track of time and compression ratio
# The lists will have tuples of the following format: (time it took)
compression_stats = {
    "jpeg": {},
    "huffman": {},
    "rle": {},
}


TEST_DIR = "./tests/"
RESULT_DIR = "./results/"
COMPARE_DIR = "./compare/"

TIME_TESTS = 3  # how many times to run the same compression algorithm on the same file to measure time



def match_compression(compression_type: str, ipath, opath):
    if compression_type == "rle":
        rle_file(ipath, opath)
    elif compression_type == "jpeg":
        jpeg(ipath, opath)
    elif compression_type == "huffman":
        huffman_file(ipath, opath)

def match_decompression(compression_type: str, ipath, opath):
    if compression_type == "rle":
        irle_file(ipath, opath)
    elif compression_type == "jpeg":
        ijpeg(ipath, opath)
    elif compression_type == "huffman":
        ihuffman_file(ipath, opath)

def test(file_name, compression_type):
    stats = {
        "ratio": 0.0,
        "time": 0.0,
        "lossless": False,
        "file size": 0.0
    }

    if compression_type == "jpeg":
        comp_ext, decomp_ext = "jpeg", "png"
    elif compression_type == "rle" or compression_type == "huffman":
        comp_ext, decomp_ext = "txt", "txt"
    else:
        comp_ext, decomp_ext = "txt", "txt"

    # get comression ratio
    test_path = f"{TEST_DIR}{file_name}.{decomp_ext}"
    result_path = f"{RESULT_DIR}{file_name}-{compression_type}.{comp_ext}"
    try:
        match_compression(compression_type, test_path, result_path)
    except:
        print(f"\nError compressing file {file_name}")
        return -1

    stats["ratio"] = os.path.getsize(test_path) / os.path.getsize(result_path)  # > 1 - good, < 1 - what are you even doing bro?
    stats["file size"] = os.path.getsize(test_path)

    times = []

    # get average time
    for _ in range(TIME_TESTS):
        start = time.perf_counter()

        match_compression(compression_type, test_path, result_path)

        end = time.perf_counter()

        elapsed = end - start

        times.append(elapsed)

        stats["time"] =  sum(times) / len(times)


    # test for loss of data
    
    compare_path = f"{COMPARE_DIR}{file_name}-{compression_type}.{decomp_ext}"
    try:
        match_decompression(compression_type, result_path, compare_path)
    except:
        print(f"\nError decompressing file after compressing this one: {file_name}")
        return -1

    stats["lossless"] = filecmp.cmp(test_path, compare_path)


    compression_stats[compression_type].update(
        {file_name+f".{decomp_ext}": stats}
    )

    return 0


def run_tests(test_type, file_name=None):
    all_files = os.listdir("./tests/")  # get all test files

    files = []
    for file in all_files:
        if test_type == "all":
            files.append(file)
        elif test_type == "txt" and file.split(".")[-1] == "txt":
            files.append(file)
        elif test_type == "jpeg" and file.split(".")[-1] == "png":
            files.append(file)
        elif test_type == "specific" and file == file_name:
            files.append(file)

    file_count = len(files)
    failed_tests = []
    compression_types = ["jpeg", "rle", "huffman"]
    
    if file_count < 20:
        print("You can run `python generate.py` to generate .txt tests")

    start = time.perf_counter()

    for i, file in enumerate(files):
        print(f"\r\033[K{i}/{file_count} done, current file: {file}", end="")
        extension = file.split(".")[-1]
        file_name = '.'.join(file.split(".")[:-1])  # remove extension from file name   
        
        # determine compression algorithm type
        for comp in compression_types:
            if (comp == "jpeg" and extension == "png") or (comp != "jpeg" and extension == "txt"):
                r = test(file_name, comp)
                if r == -1:
                    failed_tests.append(file_name)

    end = time.perf_counter()
    elapsed = end - start

    print()
    print(f"Ran all tests in {elapsed:.4f} seconds.")
    with open("benchmark.txt", "w") as file:
        json.dump(compression_stats, file)

    print(f"Successfuly dumped benchmark to benchmark.txt (wow, so creative)")
    
    if len(failed_tests) > 0:
        print(f"{len(failed_tests)} failed tests. These include: {failed_tests}")

    # after running all the tests, cleanup the results and compare folders
    results_files = os.listdir(RESULT_DIR)
    for file in results_files:
        os.remove(RESULT_DIR + file)

    compare_files = os.listdir(COMPARE_DIR)
    for file in compare_files:
        os.remove(COMPARE_DIR + file)


def testing():
    print("Choose what you want to do: ")
    print(" 1. Run all tests")
    print(" 2. Run specific test")
    print(" 3. Run specific type of test (txt or jpeg)")
    choice = int(input("answer: "))

    if choice == 1:
        run_tests("all")
    elif choice == 2:
        file_name = input("Enter file name of the test: ")
        run_tests("specific", file_name)
    elif choice == 3:
        file_type = input("Enter file type (txt or jpeg): ")
        if file_type not in ["txt", "jpeg"]:
            print(f"Invalid type: {file_type}")
        else:
            run_tests(file_type)

def compressing():
    print("Enter compression algorithm you want to use:")
    print(" 1. JPEG")
    print(" 2. RLE")
    print(" 3. Huffman")
    compression_algo = int(input("answer: "))
    
    if compression_algo not in [1, 2, 3]:
        print("Invalid choice")
        return

    algo = ["jpeg", "rle", "huffman"][compression_algo-1]

    print("Enter what you want to do with it: ")
    print(" 1. Compress")
    print(" 2. Decompress")
    choice = int(input("answer: "))

    if choice not in [1, 2]:
        print("Invalid choice")
        return

    ipath = input("Enter input file path: ")
    opath = input("Enter output file path: ")

    if choice == 1:
        match_compression(algo, ipath, opath)
    else:
        match_decompression(algo, ipath, opath)


if __name__ == "__main__":
    print("Enter what you want to do: ")
    print(" 1. Compress something")
    print(" 2. Run benchmark")

    choice = int(input("answer: "))
    if choice == "1":
        compressing()
    elif choice == "2":
        testing()
    else:
        print("Invalid choice.")
