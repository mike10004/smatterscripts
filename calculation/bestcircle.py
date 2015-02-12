#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  bestcircle.py
#  
#  (c) 2015 Mike Chaberski
#  
#  MIT License

from random import random
import math
from gausselim import *
from matrix import mult
import matrix


class Point:
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def X(self):
        return self.x
    
    def Y(self):
        return self.y
        
        
    def __repr__(self):
        return "Point(%.3f, %.3f)" % (self.x, self.y)
    
    def __str__(self):
        return "(%.3f, %.3f)" % (self.x, self.y)


#~ // we can fit a circle 
#~ // through the point set, consisting of n points.
#~ // The (n times 3) matrix consists of
#~ //   x_1, y_1, 1
#~ //   x_2, y_2, 1
#~ //      ...
#~ //   x_n, y_n, 1
#~ // where x_i, y_i is the position of point p_i
#~ // The vector y of length n consists of
#~ //    x_i*x_i+y_i*y_i 
#~ // for i=1,...n.

def fit_circle(p):
    M = []
    y = []
    n = len(p)
    for i in xrange(0, n):
        M.append([p[i].X(), p[i].Y(), 1.0]);
        y.append(p[i].X() * p[i].X() + p[i].Y() * p[i].Y());
    #~ // Now, the general linear least-square fitting problem
    #~ //    min_z || M*z - y||_2^2
    #~ // is solved by solving the system of linear equations
    #~ //    (M^T*M) * z = (M^T*y)
    #~ // with Gauss elimination.
    #MT = JXG.Math.transpose(M);
    MT = zip(*M)
    #~ B = JXG.Math.matMatMult(MT, M);
    #~ c = JXG.Math.matVecMult(MT, y);
    B = mult(MT, M)
    c = mult(MT, matrix.transpose([y]))
    z = gauss(B, c);
     
    #~ Finally, we can read from the solution vector z the coordinates [xm, ym] of the center
    #~ and the radius r and draw the circle.
    xm = z[0]*0.5;
    ym = z[1]*0.5;
    r = math.sqrt(z[2]+xm*xm+ym*ym);
    return (xm, ym, r)

def main():
    
    return 0

if __name__ == '__main__':
    main()

