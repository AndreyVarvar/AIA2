import matplotlib.pyplot as plt
import json
import random


with open("benchmark.txt", "r") as file:
    data = json.loads(file.read())



def plot(data, compression_algo, x_axis, y_axis, file_type, color="blue"):
    """
    data: benchmark.txt
    compression_algo: 'jpeg', 'rle', or 'huffman'
    x_axis: 'ratio', 'time', 'efficiency', and 'file size'
    y_axis: same as x_axis
    file_type: 'random', 'words', or 'repeating'. Does not do anything if compression_algo == 'jpeg'
    """
    if compression_algo not in ["jpeg", "rle", "huffman"]:
        print("Invalid compression algorithm:", compression_algo)
        return

    for axis in [x_axis, y_axis]:
        if axis not in ['ratio', 'time', 'efficiency', 'file size']:
            print("Invalid axis type:", axis)
            return

    if file_type not in ['random', 'words', 'repeating'] and compression_algo != 'jpeg':
        print("Invalid file type:", file_type)
        return

    axes = [[], []]  # not to ve confused with axes, tools for chopping trees

    for file in data[compression_algo].keys():
        # ignore files of incorrect file type
        if compression_algo != 'jpeg':
            if file_type == 'random' and 'random' not in file:
                continue
            if file_type == 'words' and ('words' not in file and 'bee' not in file):
                continue
            if file_type == 'repeating' and file_type not in file:
                continue
 
        for i in range(2):
            axis = [x_axis, y_axis][i]
            if axis == 'efficiency':
                axes[i].append(data[compression_algo][file]['ratio'] / data[compression_algo][file]['time'])
            else:
                axes[i].append(data[compression_algo][file][axis])


    plt.scatter(axes[0], axes[1], c=color)
    
    plt.xscale('log')
    plt.yscale('log')

    plt.title(f"{compression_algo} - {file_type}")

    plt.xlabel(x_axis)
    plt.ylabel(y_axis)


    plt.show()


colors = [
    "#4287f5",
    "#09a9e3",
    "#09e309",
    "#3f9605",
    "#f2e602",
    "#f29a02",
    "#f25202",
    "#f20202",
    "#f2027e",
    "#f202f2",
    "#9202f2",
    "#3a02f2",
    "#8a8a8a",
    "#212121",
    "#6e3a00",
    "#6e1200",
]


plots_to_plot = [
    ['rle', 'file size', 'time', 'random'],
    ['rle', 'file size', 'ratio', 'random'],
    ['rle', 'file size', 'efficiency', 'random'],

    ['rle', 'file size', 'time', 'words'],
    ['rle', 'file size', 'ratio', 'words'],
    ['rle', 'file size', 'efficiency', 'words'],
    
    ['rle', 'file size', 'time', 'repeating'],
    ['rle', 'file size', 'ratio', 'repeating'],
    ['rle', 'file size', 'efficiency', 'repeating'],
    

    ['huffman', 'file size', 'time', 'random'],
    ['huffman', 'file size', 'ratio', 'random'],
    ['huffman', 'file size', 'efficiency', 'random'],
    
    ['huffman', 'file size', 'time', 'words'],
    ['huffman', 'file size', 'ratio', 'words'],
    ['huffman', 'file size', 'efficiency', 'words'],

    ['huffman', 'file size', 'time', 'repeating'],
    ['huffman', 'file size', 'ratio', 'repeating'],
    ['huffman', 'file size', 'efficiency', 'repeating'],


    ['jpeg', 'file size', 'time', ''],
    ['jpeg', 'file size', 'ratio', ''],
    ['jpeg', 'file size', 'efficiency', ''],
]

for p in plots_to_plot:
    plot(data, compression_algo=p[0], x_axis=p[1], y_axis=p[2], file_type=p[3], color=random.choice(colors))


