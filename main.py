from src.jpeg import jpeg, ijpeg
from src.huffman import huffman_file, ihuffman_file
from src.rle import rle_file, irle_file

import os
import time
import filecmp
import pprint


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

with open("./tests/1.txt", "r") as file:
    print(set(file.read()), end="")


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

    # get compression ratio
    test_path = f"{TEST_DIR}{file_name}.{decomp_ext}"
    result_path = f"{RESULT_DIR}{file_name}-{compression_type}.{comp_ext}"
    match_compression(compression_type, test_path, result_path)

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


    compression_stats[compression_type].update(
        {file_name+f".{decomp_ext}": stats}
    )

    # test for loss of data
    # since RLE is supposed to be lossless, we check if no data is loss
    
    compare_path = f"{COMPARE_DIR}{file_name}-{compression_type}.{decomp_ext}"
    match_decompression(compression_type, result_path, compare_path)
    
    stats["lossless"] = filecmp.cmp(test_path, compare_path)

files = os.listdir("./tests/")  # get all test files

for file in files:
    extension = file.split(".")[-1]
    file_name = '.'.join(file.split(".")[:-1])  # remove extension from file name   
    # determine compression algorithm type
    if extension == "png":  # jpeg compression
        test(file_name, "jpeg")
    elif extension == "txt":  # huffman and rle compressions
        test(file_name, "rle")
        test(file_name, "huffman")

pprint.pprint(compression_stats, indent=4)

