import random
import os
import sys

# use this to generate deterministic tests. Useful for when you want to copy what someone else has
# random.seed()

def filter(words):
    filtered = []
    for word in words:
        try:
            word.encode("ascii")
            filtered.append(word)
        except:
            pass
    return filtered


alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-=+_/?><,.~!@#$%^&*()[]{}"

with open("./top_english_words_mixed_1000000.txt", "r") as file:
    words = file.readlines()
words = filter(words)  # remove words that contain non-ascii characters


def generate_tests_random_txt(count: int, size_type: str):
    # generate tests for RLE and huffman
    test_path = "./tests/"


    if size_type not in ['small', 'medium', 'large', 'HUMONGOUS']:
        print(f"Invalid size: {size_type}")
        return
    if count < 0 or count > 100:
        print("Invalid count:", count)
        print("Count should be greater than 0 and smaller than 100 (to not bomb your computer)")
        return

    for i in range(count):
        size = 0
        if size_type == "small":
            size = random.randrange(5, 50)
        if size_type == "medium":
            size = random.randrange(50, 500)
        if size_type == "large":
            size = random.randrange(500, 5_000)
        if size_type == "HUMONGOUS":
            size = random.randrange(5_000, 50_000)

        path = test_path + f"random-{size_type}-{i}.txt"

        with open(path, "w") as file:
            for i in range(size):
                file.write(random.choice(alphabet))

    print(f"Successfully generated {count} random tests of size type: {size_type}")



def generate_tests_words_txt(count: int, size_type: str):
    # generate tests for RLE and huffman
    test_path = "./tests/"



    if size_type not in ['small', 'medium', 'large', 'HUMONGOUS']:
        print(f"Invalid size: {size_type}")
        return
    if count < 0 or count > 100:
        print("Invalid count:", count)
        print("Count should be greater than 0 and smaller than 100 (to not bomb your computer)")
        return


    for i in range(count):
        if size_type == "small":
            word_count = random.randrange(1, 10)
        if size_type == "medium":
            word_count = random.randrange(10, 100)
        if size_type == "large":
            word_count = random.randrange(100, 1_000)
        if size_type == "HUMONGOUS":
            word_count = random.randrange(1_000, 10_000)
        
        path = test_path + f"words-{size_type}-{i}.txt"

        with open(path, "w") as file:
            for i in range(word_count):
                file.write(random.choice(words))
    
    print(f"Successfully generated {count} word tests of size type: {size_type}")


def clean_testing_dir(type_to_remove):
    test_path = "./tests/"
    files = os.listdir(test_path)
    deleted_files_count = 0
    for file in files:
        if type_to_remove == file.split(".")[-1]:
            os.remove(test_path+file)
            deleted_files_count += 1
    print(f"Successfully deleted {deleted_files_count} files.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        seed = sys.argv[1]
    else:
        seed = random.randrange(sys.maxsize)
    random.seed(seed)

    print("Randomizer seed:", seed)

    print("What do you want to do: ")
    print(" 1. Generate txt tests (random gibberish);")
    print(" 2. Generate txt tests (enlgish words);")
    print(" 3. Default preset, that includes:")
    print("     a. 100 small random;")
    print("     b. 80 medium random;")
    print("     c. 40 large random;")
    print("     d. 20 HUMONGOUS random;")
    print("     e. 100 small words;")
    print("     f. 80 medium words;")
    print("     g. 40 large words;")
    print("     h. 20 HUMONGOUS words;")
    print(" 4. Clear current test directory.")
    print(" 5. Do nothing.")

    i = int(input("answer: "))
    if i == 1:
        count = int(input("How many tests do you want (<100): "))
        size_type = input("Enter size type (small, medium, large, HUMONGOUS): ")
        generate_tests_random_txt(count, size_type)
    elif i == 2:
        count = int(input("How many tests do you want (<100): "))
        size_type =  input("Enter size type (small, medium, large, HUMONGOUS): ")
        generate_tests_words_txt(count, size_type)
    elif i == 3:
        generate_tests_random_txt(100, "small")
        generate_tests_random_txt(80, "medium")
        generate_tests_random_txt(40, "large")
        generate_tests_random_txt(20, "HUMONGOUS")
        generate_tests_words_txt(100, "small")
        generate_tests_words_txt(80, "medium")
        generate_tests_words_txt(40, "large")
        generate_tests_words_txt(20, "HUMONGOUS")
    elif i == 4:
        type_to_remove = input("Enter file type to remove (png or txt): ")
        clean_testing_dir(type_to_remove)
    elif i == 5:
        print("bruh")
    else:
        print("Invalid option.")

