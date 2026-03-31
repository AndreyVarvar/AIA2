import random


alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-=+_/?><,.~!@#$%^&*()[]{}"

def generate_tests_random_txt(count: int, size_type: str):
    # generate tests for RLE and huffman
    test_path = "./tests/"

    size = 0
    if size_type == "small":
        size = random.randrange(5, 50)
    if size_type == "medium":
        size = random.randrange(50, 500)
    if size_type == "large":
        size = random.randrange(500, 5_000)
    if size_type == "HUMONGOUS":
        size = random.randrange(5_000, 50_000)

    if size == 0:
        print(f"Invalid size: {size_type}")
        return
    if count < 0 or count > 100:
        print("Invalid count:", count)
        print("Count should be greater than 0 and smaller than 100 (to not bomb your computer)")
        return

    for i in range(count):
        path = test_path + f"{size_type}-{i}.txt"

        with open(path, "w") as file:
            for i in range(size):
                file.write(random.choice(alphabet))


if __name__ == "__main__":
    print("What do you want to do: ")
    print(" 1. Generate txt tests (random);")

    i = int(input("answer: "))
    if i == 1:
        count = int(input("How many tests do you want (<100): "))
        size_type = input("Enter size type (small, medium, large, HUMONGOUS): ")
        generate_tests_random_txt(count, size_type)
    else:
        print("Invalid option.")

