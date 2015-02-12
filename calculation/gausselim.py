#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  gausselim.py
#  
#  http://208.91.135.51/posts/show/5645
#
# this requires numpy get it from http://numpy.sf.net

from copy import deepcopy
#from numpy import *
import numpy
import sys
# this function, swapRows, was adapted from
# Numerical Methods Engineering with Python, Jean Kiusalaas
def swapRows(v,i,j):
    """Swaps rows i and j of vector or matrix [v]."""
    if len(v) == 1:
        v[i],v[j] = v[j],v[i]
    else:
        temp = v[i].copy()
        v[i] = v[j]
        v[j] = temp
    
def pivoting(a, b, verbose=True):
    """changes matrix A by pivoting"""
    if isinstance(b[0], list):
        print >> sys.stderr, "unwrapping b =", b
        b = b[0]
    if verbose:
        print >> sys.stderr, "pivoting: a =", a
        print >> sys.stderr, "pivoting: b =", b
    n = len(b)
    for k in range(0, n-1):
        av = abs(a[k:n, k])
        arg = numpy.argmax(av)
        p = int(arg) + k
        if (p != k):
            swapRows(b, k, p)
            swapRows(a,k,p)

def gauss(a, b, t=1.0e-9, verbose=False):
    """ Solves [a|b] by gauss elimination"""
    
    n = len(b)
    
    # make copies of a and b so as not to change the values in the arguments
    tempa = deepcopy(a)
    tempb = deepcopy(b)
    
    # check if matrix is singular
    if abs(numpy.linalg.det(tempa)) < t:
        print "asn"
        return -1
    
    pivoting(tempa, tempb)

    for k in range(0,n-1):  
        for i in range(k+1, n):
            if tempa[i,k] != 0.0:
                m = tempa[i,k]/tempa[k,k]
                if verbose:
                    print "m =", m
                tempa[i,k+1:n] = tempa[i,k+1:n] - m * tempa[k,k+1:n]
                tempb[i] = tempb[i] - m * tempb[k]
    
    # Back substitution
    for k in range(n-1,-1,-1):
        tempb[k] = (tempb[k] - numpy.dot(tempa[k,k+1:n], tempb[k+1:n]))/tempa[k,k]

    return tempb

def residue(a, b, c):
    """Calculates the residue of a system solved by gauss elimination"""
    n = len(b)

    t = a * c # t is the A with the values of x replaced (an [n x n] matrix) 

    s = []
    for i in range(0, n):
        s.append(sum(t[i])) # s is the solution


    res = b - s # res is the residue

    return res

# 1) dA = Somar uma pequena quantidade a A
# 2) dB = Somar uma pequena quantidade a B
# 3) A.dX = dB - dA.x0

def disturb(a, b, ai, bi):
    """Calculates the extarnal disturbance cause by da and db"""
    
    x = gauss(a, b)
    
    n = len(b)
    
    da = numpy.array([1])
    da.resize(n, n)
    da.fill(ai)
    
    print "da = ", da
    
    db = numpy.array([1])
    db.resize(1, n)
    db.fill(bi)
    
    print "db = ", db
    
    t = db - da*x
    nx = gauss(a, t)

    return nx
    
def main():
    
    return 0

if __name__ == '__main__':
    main()

