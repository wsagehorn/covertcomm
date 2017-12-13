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

class CommandLineTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        parser = get_arg_parser()
        cls.parser = parser


class PNGTestCase(CommandLineTestCase):

    def tearDown(self):
        clean(PNG_OUT)
        clean(TXT_OUT)

    def test_with_empty_args(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args([])

    def test_PNG(self):
        args = self.parser.parse_args(
            [PNG_FILE, "-i", TXT_FILE, "-o", PNG_OUT]
        )

        steg(args)

        args = self.parser.parse_args(
            [PNG_OUT, "-e", "-o", TXT_OUT]
        )

        steg(args)

        self.assertTrue(filecmp.cmp(TXT_FILE, TXT_OUT))
