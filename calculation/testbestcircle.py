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
from bestcircle import Point
from bestcircle import fit_circle


def create_random_points(delta=0.8):
    #~ Random points are constructed which lie roughly on a circle
    #~ of radius 4 having the origin as center.
    #~ delta*0.5 is the maximal distance in x- and y- direction of the random
    #~ points from the circle line.
    p = []
    for i in xrange(0, 100):
        angle = random()*2*math.pi;
        co = 4*math.cos(angle)+delta*(random()-0.5);
        si = 4*math.sin(angle)+delta*(random()-0.5);
        p.append(Point(co, si));
    return p

def main():
    p = create_random_points()
    print "points:"
    print p
    x, y, r = fit_circle(p)
    print "circle = ", (x, y, r)
    return 0

if __name__ == '__main__':
    main()

