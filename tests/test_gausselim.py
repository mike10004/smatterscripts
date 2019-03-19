#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  testgausselim.py
#  
#
#  (c) 2015 Mike Chaberski
#  
#  MIT License
#  

from numpy import array
from calculation.gausselim import gauss
from unittest import TestCase


class GaussTest(TestCase):

    def test_something(self):
        a = array([[1.0, 2.0, 0.0],[-1.0, 2.0, 3.0],[1.0, 4.0, 1.0]])
        b = array([3.0, -1.0, 4.0])
        #a = array([[-1.414214, 2, 0],[1, -1.414214, 1], [0, 2, -1.414214]])
        #b = array([1.0,1.0,1.0])
        #a = array([[2.0, 2.0, 2.0],[1.0, 1.0, 5.0], [2.0, 5.0, 1.0]])
        #b = array([6.0, 7.0, 8.0])
        #a = array([[1.001, 2.001, 3.001],[0.999, 2.0, 2.999], [1.002, 1.999, 2.999]])
        #b = array([4.003, 4.001, 3.999])

        #a = numpy.array([[0.7, 8.0, 3.0],[-6.0, 0.45, -0.25], [8.0, -3.1, 1.05]])
        #b = numpy.array([2.3, 3.5, 10.3])

        print("A = ", a)
        print("b = ", b)

        x = gauss(a, b)
        print("Solution = ", x)

        #sol = linalg.solve(a, b)
        #print "linalg Solution = ", sol

        #y = residue(a, b, x)
        #print "Residue = ", y

        #u = gauss(a, y)
        #print "Residue destribution = ", u

        #z = gauss(a, b+y)
        #print "New Solution (with added residue) = ", z

        #y2 = residue(a, b+y, z)
        #print "Residule of new solution = ", y2


        #if linalg.norm(y2) < linalg.norm(y):
        #    print "New solution has a smaller residue."
        #else:
        #    print "Original solution has a smaller residue."

        #~ nx = disturb(a, b, 0.5, 0.5)
        #~ print "Disturbed Solution = ", nx
