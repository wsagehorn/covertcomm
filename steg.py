#!/usr/bin/env python3

import sys, os, argparse
import numpy as np
from PIL import Image
from itertools import chain

def get_args():
    parser = argparse.ArgumentParser()

    general_options = parser.add_argument_group("General Options")
    general_options.add_argument("-e", "--extract", dest="is_extract", action="store_true", default=False, help="Extract data from a vessel image")
    general_options.add_argument("-v", "--verbose", dest="is_verbose", action="store_true", default=False, help="Print more about what's going on")
    general_options.add_argument("-b", "--bits", dest="b", type=int, default=2, help="The number of bits to use per byte")

    io_options = parser.add_argument_group("I/O 0ptions")
    io_options.add_argument('vessel_image')
    io_options.add_argument("-i", "--input", dest="input_file", help="File to embed into the image")
    io_options.add_argument("-o", "--output", dest="output_file", help="File to output to. If left blank, \
    save as <inputfile>.vsl or <inputimage>.uvsl for enbedding and extracting, respectively")

    return parser.parse_args()


def embed2(vessel_image, input_file, b):
    vessel_array = np.array(vessel_image)
    flat_vessel = vessel_array.flatten() # 2d -> 1D array
    bits = get_bits(input_file, b)
    for pixel in flat_vessel:
        for j in [0,1,2]: # for the R, G, and B values of each pixel
            #replace the last b bits with b bits from input_file
            try:
                pixel[j] = (pixel[j] & ~b) | next(bits)
            except StopIteration:
                #unsquash the image
                new_vessel = np.reshape(vessel_image)
                new_vessel = np.rot90(new_vessel, 3)
                return Image.fromarray(new_vessel)

def embed(vessel_image_path, input_file_path, b):

    input_generator = get_bits_from_file(input_file_path, b)
    #store the size of the input file in the first 8 bytes so we know how much
    # to read when we extract
    # we still want to conform to our "use b bits from each byte" rule
    # so we need to chain the generators
    size_in_bytes = (os.path.getsize(input_file_path)).to_bytes(8, "big")
    print("".join([ format(x, "0{}b".format(b)) for x in get_bits(bytearray(size_in_bytes), b) ]))
#"".join([ format(x, "0{}b".format(b)) for x in get_bits((2).to_bytes(1,"big"), b) ])
    size_generator = get_bits(bytearray(size_in_bytes), b)
    bits = chain(size_generator, input_generator)

    vessel_image = Image.open(vessel_image_path)
    vessel_bytes = bytearray(vessel_image.tobytes())
    # stores b in the last 3 bits of the first byte in the image.
    # since b can't be 0, 000 means 8
    vessel_bytes[0] = (vessel_bytes[0] & 0) | (b % 8)
    #print(vessel_bytes[:10], len(vessel_bytes))

    for i, byte in enumerate(vessel_bytes[1:]):
        try:
            #print("before: " + str(vessel_bytes[i + 1]))
            q = next(bits)

            #if i < 50:
                #print(i, format(q, "0{}b".format(b)))


            vessel_bytes[i + 1] = (byte & ~((2**b)-1)) | q
            #if i < 50:
                #print(i, format(vessel_bytes[i + 1] & ((2**b)-1), "0{}b".format(b)))

            #print("after: " + str(vessel_bytes[i + 1]))

        except StopIteration:

            #print([format(r & ((2**b)-1), "0{}b".format(b)) for r in vessel_bytes[:50]], len(vessel_bytes))

            return Image.frombytes("RGB", vessel_image.size, bytes(vessel_bytes))


# generator that fetches b bits at a time from bytearray b
#   0 > b >= 8
#   keep b as factor of 8 for best results ([1,2,4,8])
def get_bits(ba, b):
    for byte in ba:
        for i in range(0,8,b):
            #print(i)
            mask = ((2**b) - 1) << i
            yield (byte & mask) >> i

# feeds a file into get_bits
def get_bits_from_file(input_file_path, b):
    with open(input_file_path, "rb") as input_file:
        return get_bits(bytearray(input_file.read()), b)

def extract(vessel_image_path):
    vessel_image = Image.open(vessel_image_path)
    vessel_bytes = vessel_image.tobytes()
    #print(vessel_bytes[:10])
    #print(vessel_bytes[0], len(vessel_bytes))


    b = (vessel_bytes[0] & 7)
    print("b = " + str(b))
    data = bytearray()
    bytestring = ""
    #print([r for r in vessel_bytes[1:9]])
    file_size = int.from_bytes(vessel_bytes[1:9], "big")
    i = 0
    #print([format(r & ((2**b)-1), "0{}b".format(b)) for r in vessel_bytes[:50]], len(vessel_bytes))

    for byte in vessel_bytes[1:]:


        bytestring = bytestring + format(byte & ((2**b)-1), "0{}b".format(b))
        if i < 100:
            print(i, format(byte & ((2**b)-1), "0{}b".format(b)))

        if len(bytestring) >= 8:
            if i < 100:
                print("adding to data: " + str(int(bytestring[:8], 2)))
                print(i, data, bytestring)
            data.append(int(bytestring[:8], 2))
            bytestring = bytestring[8:]


        i += 1
    print(data[1:9], "big if true")

    print(int.from_bytes(data[1:9], "big"))
    #quit()
    return data

def main():
    args = get_args()

    vessel_image_path = args.vessel_image
    b = args.b

    vessel_image = Image.open(vessel_image_path)

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
        if (vessel_size * b/8 < input_size):
            print("Error: input is larger than what can be stored")
            print("input size:  " + str(input_size))
            print("vessel size: " + str(vessel_size * b/8))
            quit()

        img = embed(vessel_image_path, input_file_path, b)
        output_file_path = args.output_file if args.output_file else vessel_image_path
        #must be saved as BMP, otherwise it will be scrambled by other storage schemas
        img.save(output_file_path, format="BMP")

    else:
        output_file_path = args.output_file if args.output_file else vessel_image_path + ".uvsl"
        with open(output_file_path, "wb") as output_file:
            output_file.write(extract(vessel_image_path))

if __name__ == "__main__":
    main()
