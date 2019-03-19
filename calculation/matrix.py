# matrix.py
#
# -*- coding: utf-8 -*-
#
#  http://www.syntagmatic.net/matrix-multiplication-in-python/
#

from __future__ import print_function
import random


def transpose(a):
    return list(zip(*a))

def zero(m,n):
    # Create zero matrix
    new_matrix = [[0 for row in range(n)] for col in range(m)]
    return new_matrix
 
def rand(m,n):
    # Create random matrix
    new_matrix = [[random.random() for row in range(n)] for col in range(m)]
    return new_matrix
 
def show(matrix):
    # Print out matrix
    for col in matrix:
        print(col)


def mult(matrix1,matrix2):
    assert isinstance(matrix1, list)
    assert isinstance(matrix2, list)
    # Matrix multiplication
    if len(matrix1[0]) != len(matrix2):
        # Check matrix dimensions
        raise ValueError('Matrices must be MxN and NxP to multiply!')
    else:
        # Multiply if correct dimensions
        new_matrix = zero(len(matrix1),len(matrix2[0]))
        for i in range(len(matrix1)):
            for j in range(len(matrix2[0])):
                for k in range(len(matrix2)):
                    new_matrix[i][j] += matrix1[i][k]*matrix2[k][j]
        return new_matrix
 
