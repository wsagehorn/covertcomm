

from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from steg import get_arg_parser
from unittest import TestCase

class CommandLineTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        parser = get_arg_parser
        cls.parser = parser


class PNGTestCase(CommandLineTestCase):
    def test_with_empty_args(self):
        self.assertEqual(1+1, 2)
