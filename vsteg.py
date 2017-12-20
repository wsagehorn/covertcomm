#!/usr/bin/env python3

import sys, os, argparse
from PIL import Image
from itertools import chain

from steg import get_bits, get_bits_from_file
import skvideo.io
import numpy as np

def get_arg_parser():
    parser = argparse.ArgumentParser(
        description='Steganographically embed or \
        extract information using vessel video files.'
    )

    general_options = parser.add_argument_group("General Options")
    general_options.add_argument(
        "-e", "--extract", dest="is_extract",
        action="store_true", default=False,
        help="Extract data from a vessel video"
    )

    io_options = parser.add_argument_group("I/O Options")
    io_options.add_argument('vessel_video')
    io_options.add_argument(
        "-i", "--input", dest="input_file",
        help="File to embed into the video"
    )
    io_options.add_argument(
        "-o", "--output", dest="output_file",
        help="File to output to. If left blank, \
        overwrite or save to <inputimage>.uvsl for \
        embedding and extracting, respectively"
    )

    return parser

def get_fake_bits():
    ba = [1]*200
    for byte in ba:
        for i in range(8)[::-1]:
            yield (byte & 2**i) >> i

def embed(vessel_video, input_file):

    # create a 1-bit-at-a-time generator for the size of the input
    size_in_bytes = (os.path.getsize(input_file.name)).to_bytes(8, "big")
    size_generator = get_bits(bytearray(size_in_bytes))

    # do the same for the input itself
    input_generator = get_bits_from_file(input_file)

    #chain them together
    bits = chain(size_generator, input_generator)
    #bits = get_fake_bits()

    video_shape = vessel_video.shape
    vessel_bytes = bytearray(vessel_video.tobytes())
    for i, byte in enumerate(vessel_bytes):
        try:
            vessel_bytes[i] = (byte & ~4) | (next(bits) << 2)
            if i < 64:
                print((vessel_bytes[i] & 4)>>2,end="")
            # create buffer bits - last two bits must be different
            # if 1 is added or subtracted, the 3rd bit won't change
            if vessel_bytes[i] & 3 == 0:
                vessel_bytes[i] = (byte & ~3) | 1
            if vessel_bytes[i] & 3 == 3:
                vessel_bytes[i] = (byte & ~3) | 2

        except StopIteration:
            #print("\t".join(str(b) for b in vessel_bytes[:64]))
            size = int.from_bytes(size_in_bytes, "big")
            #print(bin(size))
            video_array = np.frombuffer(vessel_bytes, np.dtype(np.uint8))
            return video_array.reshape(video_shape)

def extract(vessel_video):
    vessel_bytes = vessel_video.tobytes()

    # retreive the size of the input file from the first 8 bytes
    print(type(vessel_bytes[:64]))
    #print("\t".join(str(b) for b in vessel_bytes[:64]))
    source = vessel_bytes[:64]
    target = bytearray(8)
    for i, _ in enumerate(target):
        for byte in source[i * 8 : (i+1) * 8]:
            print(bin(byte), end="\t")
    print("\n\n")
    size_in_bytes = build_from_bits(8, vessel_bytes[:64])
    #print("\t".join(str(b) for b in size_in_bytes[:64]))
    size = int.from_bytes(size_in_bytes, "big")
    #print(bin(size))

    # edge case where an arbitrary file is being read from
    if size > sys.maxsize:
        message = "Error: target file size too large. \n (Are you sure you're extracting from the right file?)"
        raise OverflowError(message)
    return 0
    #return build_from_bits(size, vessel_bytes[64:])

# constructs target from the 3rd to last bit from each byte in source
def build_from_bits(size_of_target, source):
    target = bytearray(size_of_target)
    for i, _ in enumerate(target):
        for byte in source[i * 8 : (i+1) * 8]:
            print(bin(byte), end="\t")
            target[i] <<= 1
            #if i<64:
                #print(bin((byte & 4) >> 2), end="")
            target[i] |= (byte & 4) >> 2
            #print(" ", bin(target[i]))
        #print(" &&&& ", bin(target[i]))

    return target


def steg(args):
    vessel_video_path = args.vessel_video
    vessel_video = skvideo.io.vread(vessel_video_path)

    ### Embedding ###
    if not args.is_extract:
        if not args.input_file:
            print("Error: No input file provided.")
            quit()
        input_file_path = args.input_file

        if not args.output_file:
            print("an output file wasn't provided, the file will be overwritten. \
            Continue? (y/n)")
            if (input().upper() != "Y"):
                quit()

        input_size = os.path.getsize(input_file_path)
        vessel_size = len(vessel_video.tobytes())
        if (vessel_size / 8 < input_size):
            print("Error: input is larger than what can be stored")
            print("input size:  " + str(input_size))
            print("vessel size: " + str(int(vessel_size / 8)))
            quit()

        with open(input_file_path, "rb") as input_file:
            vid = embed(vessel_video, input_file)
        output_file_path = args.output_file if args.output_file else vessel_video_path
        try:
            outputdict = dict()
            outputdict["-c:v"] = "libx264"
            outputdict["-crf"] = "7"
            skvideo.io.vwrite(output_file_path, vid, outputdict=outputdict)
        except Exception as e:
            print(e)

    ### Extracting ###
    else:
        output_file_path = args.output_file if args.output_file else vessel_video_path + ".uvsl"
        with open(output_file_path, "wb") as output_file:
            try:
                output_file.write(extract(vessel_video))
            except Exception as e:
                print(e)
                os.remove(output_file_path)


def main():
    args = get_arg_parser().parse_args()
    steg(args)

if __name__ == '__main__':
    main()
