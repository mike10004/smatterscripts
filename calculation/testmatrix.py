#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  testmatrix.py
#  

import matrix

def main():
    a = matrix.rand(3,3)
    print "a = "
    matrix.show(a)
    b = matrix.rand(3, 3)
    print "b = "
    matrix.show(b)
    c = matrix.mult(a, b)
    print "c = "
    matrix.show(c)
    return 0

if __name__ == '__main__':
    main()

