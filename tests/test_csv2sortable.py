from unittest import TestCase
from shelltools import csv2sortable
import io
import csv

class ModuleTest(TestCase):

    def test_transform(self):
        text_input = io.StringIO("""\
a,b,c,d
1,2,3,4
apples,"peaches, pumpkin",pie,holler
""")
        buffer = io.StringIO()
        csv2sortable.transform(',', "\t", text_input, buffer)
        rows = [row for row in csv.reader(io.StringIO(buffer.getvalue()), delimiter="\t")]
        expected = [
            ["a", "b", "c", "d"],
            ["1", "2", "3", "4"],
            ["apples", "peaches, pumpkin", "pie", "holler"]
        ]
        self.assertListEqual(expected, rows)
