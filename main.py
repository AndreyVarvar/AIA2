from src.jpeg import jpeg, ijpeg
from src.huffman import huffman, ihuffman
from src.rle import rle_file, irle_file

import os
import time
import filecmp
import pprint


# we need to take track of time and compression ratio
# The lists will have tuples of the following format: (time it took)
compression_stats = {
    "jpeg": {},
    "hauffman": {},
    "rle": {},
}


TEST_DIR = "./tests/"
RESULT_DIR = "./results/"
COMPARE_DIR = "./compare/"

TIME_TESTS = 3  # how many times to run the same compression algorithm on the same file to measure time



def rle_test(file_name):
    stats = {
        "ratio": 0.0,
        "time": 0.0,
        "lossless": False
    }

    # get compression ratio
    test_path = f"{TEST_DIR}{file_name}.txt"
    result_path = f"{RESULT_DIR}{file_name}.txt"
    rle_file(test_path, result_path)

    stats["ratio"] = os.path.getsize(test_path) / os.path.getsize(result_path)  # > 1 - good, < 1 - what are you even doing bro?

    times = []

    # get average time
    for _ in range(TIME_TESTS):
        start = time.perf_counter()

        rle_file(test_path, result_path)

        end = time.perf_counter()

        elapsed = end - start

        times.append(elapsed)

        stats["time"] =  sum(times) / len(times)


    compression_stats["rle"].update(
        {file_name+".txt": stats}
    )

    # test for loss of data
    # since RLE is supposed to be lossless, we check if no data is loss
    
    compare_path = f"{COMPARE_DIR}{file_name}.txt"
    irle_file(result_path, compare_path)
    
    stats["lossless"] = filecmp.cmp(test_path, compare_path)



files = os.listdir("./tests/")  # get all test files

for file in files:
    extension = file.split(".")[-1]
    file_name = '.'.join(file.split(".")[:-1])  # remove extension from file name   
    # determine compression algorithm type
    if extension == "png":  # jpeg compression
        pass
    elif extension == "txt":  # huffman and rle compressions
        rle_test(file_name)

pprint.pprint(compression_stats, indent=4)

