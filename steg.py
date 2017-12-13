#!/usr/bin/env python3

import sys, os, argparse
from PIL import Image
from itertools import chain


def get_args():
    parser = argparse.ArgumentParser()

    general_options = parser.add_argument_group("General Options")
    general_options.add_argument("-e", "--extract", dest="is_extract", action="store_true", default=False, help="Extract data from a vessel image")

    io_options = parser.add_argument_group("I/O Options")
    io_options.add_argument('vessel_image')
    io_options.add_argument("-i", "--input", dest="input_file", help="File to embed into the image")
    io_options.add_argument("-o", "--output", dest="output_file", help="File to output to. If left blank, \
    overwrite or save to <inputimage>.uvsl for embedding and extracting, respectively")

    return parser.parse_args()



def embed(vessel_image, input_file):

    # create a 1-bit-at-a-time generator for the size of the input
    size_in_bytes = (os.path.getsize(input_file.name)).to_bytes(8, "big")
    size_generator = get_bits(bytearray(size_in_bytes))

    # do the same for the input itself
    input_generator = get_bits_from_file(input_file)

    #chain them together
    bits = chain(size_generator, input_generator)

    # The output of this generator is what will be embedded in the file.
    # - The first 8 bytes are the size of the file so that the extractor will know
    #   when it has the full file and stop extracting.
    # - The rest is the data of the input file itself.

    vessel_bytes = bytearray(vessel_image.tobytes())
    for i, byte in enumerate(vessel_bytes):
        try:
            vessel_bytes[i] = (byte & ~1) | next(bits)
        except StopIteration:
            return Image.frombytes(vessel_image.mode, vessel_image.size, bytes(vessel_bytes))

def extract(vessel_image):
    vessel_bytes = vessel_image.tobytes()

    # retreive the size of the input file from the first 8 bytes
    size_in_bytes = build_from_bits(8, vessel_bytes[:64])
    size = int.from_bytes(size_in_bytes, "big")

    # edge case where an arbitrary file is being read from
    if size > sys.maxsize:
        message = "Error: target file size too large. \n (Are you sure you're extracting from the right file?)"
        raise OverflowError(message)

    return build_from_bits(size, vessel_bytes[64:])

# generator that yields 1 bit at a time from bytearray
def get_bits(ba):
    for byte in ba:
        for i in range(8)[::-1]:
            yield (byte & 2**i) >> i

# yields 1 bit at a time from a file
def get_bits_from_file(input_file):
    assert input_file.mode == "rb", "file must be opened in mode rb"
    return get_bits(bytearray(input_file.read()))

# constructs target from the last bit from each byte in source
def build_from_bits(size_of_target, source):
    target = bytearray(size_of_target)
    for i, _ in enumerate(target):
        for byte in source[i * 8: (i+1) * 8]:
            target[i] <<= 1
            target[i] |= (byte & 1)
    return target


def main():
    args = get_args()

    vessel_image_path = args.vessel_image
    vessel_image = Image.open(vessel_image_path)

    ### Embedding ###
    if not args.is_extract:
        if not args.input_file:
            print("Error: No input file provided.")
            quit()
        input_file_path = args.input_file

        if not args.output_file:
            print("an output file wasn't provided, the image file will be overwritten. \
            Continue? (y/n)")
            if (input().upper() != "Y"):
                quit()

        input_size = os.path.getsize(input_file_path)
        vessel_size = len(vessel_image.tobytes())
        if (vessel_size / 8 < input_size):
            print("Error: input is larger than what can be stored")
            print("input size:  " + str(input_size))
            print("vessel size: " + str(int(vessel_size / 8)))
            quit()

        with open(input_file_path, "rb") as input_file:
            img = embed(vessel_image, input_file)
        output_file_path = args.output_file if args.output_file else vessel_image_path
        #JPEG must be saved as BMP, otherwise it will be scrambled by compression
        f = vessel_image.format if vessel_image.format != "JPEG" else "BMP"
        try:
            img.save(output_file_path, format=f)
        except Exception as e:
            print(e)

    ### Extracting ###
    else:
        output_file_path = args.output_file if args.output_file else vessel_image_path + ".uvsl"
        with open(output_file_path, "wb") as output_file:
            try:
                output_file.write(extract(vessel_image))
            except Exception as e:
                print(e)
                os.remove(output_file_path)



if __name__ == '__main__':
    main()
