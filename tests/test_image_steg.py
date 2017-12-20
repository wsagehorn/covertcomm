# allow realtive imports
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import os
from steg import get_arg_parser, steg
from unittest import TestCase
import filecmp

#removes files if they exists
def clean(*files):
    for f in files:
        if os.path.exists(f):
            os.remove(f)

TXT_FILE = "tests/data/m.txt"
TXT_OUT = "tests/data/m2.txt"

PNG_FILE = "tests/data/image.png"
PNG_OUT = "tests/data/out.png"

JPG_FILE = "tests/data/image.jpg"
JPG_OUT = "tests/data/out.jpg"

BMP_FILE = "tests/data/image.bmp"
BMP_OUT = "tests/data/out.bmp"

TMP_FILES = [TXT_OUT, PNG_OUT, JPG_OUT, BMP_OUT]

class CommandLineTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        parser = get_arg_parser()
        cls.parser = parser


class ImageTestCase(CommandLineTestCase):

    def tearDown(self):
        clean(*TMP_FILES)

    def test_with_empty_args(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args([])

    def CLI_embed(self, img, data, out):
        args = self.parser.parse_args(
            [img, "-i", data, "-o", out]
        )
        steg(args)

    def CLI_extract(self, img, out):
        args = self.parser.parse_args(
            [img, "-e", "-o", out]
        )
        steg(args)

    def image_helper(self, in_file, out_file):
        self.CLI_embed(in_file, TXT_FILE, out_file)
        self.assertTrue(os.path.exists(out_file))
        self.CLI_extract(out_file, TXT_OUT)
        self.assertTrue(filecmp.cmp(TXT_FILE, TXT_OUT))

    def test_PNG(self):
        self.image_helper(PNG_FILE, PNG_OUT)

    def test_JPG(self):
        self.image_helper(JPG_FILE, JPG_OUT)

    def test_BMP(self):
        self.image_helper(BMP_FILE, BMP_OUT)
