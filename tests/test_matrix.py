from unittest import TestCase
from calculation import matrix

class MatrixTest(TestCase):

    def test_printing(self):
        a = matrix.rand(3,3)
        print("a = ")
        matrix.show(a)
        b = matrix.rand(3, 3)
        print("b = ")
        matrix.show(b)
        c = matrix.mult(a, b)
        print("c = ")
        matrix.show(c)

