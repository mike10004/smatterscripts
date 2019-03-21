#!/usr/bin/python
#
# combinadic
# 
# factorial copied from Python documentation
#
# other parts (c) 2015 Mike Chaberski
#  
# MIT License

from math import factorial
import random


def get_num_combos(n, k) -> int:
    if n < 0 or k < 0:
        raise ValueError('n and k values must be nonnegative')
    if n < k:
        raise ValueError('Must have n >= k')
    return factorial(n) // (factorial(k) * factorial(n - k))


def get_combo(n, k, index):
    num_combos = get_num_combos(n, k)
    if not (0 <= index < num_combos):
        raise ValueError("invalid index: must be in interval [%d, %d)" %
                            (0, num_combos))
    values = list()
    for slot in range(0, n):
        if k == 0:
            break
        threshold = get_num_combos(n - (slot + 1), k - 1)
        if index < threshold:
            values.append(slot)
            k = k - 1
        else: # if index >= threshold
            index = index - threshold
    return values


def get_random_subset(n, k):
    """Get a subset of k integers from the interval [0, n). Set is returned
    as a list object.
    """
    return get_random_subsets(n, k, 1).pop()

def get_random_subsets(n, k, m=1):
    """Get a list of m sets of size k, where each set is a subset of [0, n). 
    Sets are randomly selected from all possible subsets of [0, n).
    Sets are returned in the form of list objects.
    """
    n_C_k = get_num_combos(n, k)
    nCk_C_m = get_num_combos(n_C_k, m)
    r = random.randint(0, nCk_C_m - 1)
    subset_indices = get_combo(n_C_k, m, r)
    combos = [get_combo(n, k, i) for i in subset_indices]
    return combos

REQUIRED_NUM_ARGS = 2

def _parse_args():
    from optparse import OptionParser
    parser = OptionParser(usage="""
    %prog [options] n k
Prints combinations of k elements out of n, or a single combination as 
specified by the options flagged. In precise terms,
    n   is the size of the set;
    k   is the size of the subset;
and by default all unique subsets of k elements out of an n-element set
are printed to standard output. 

Examples

    %prog 4 2
    %prog -i147 10 5
    %prog -r20 10 5
    """)
    parser.add_option("-i", "--index", 
                    help="Print the subset at index INTEGER in the list"+
                    " of unique subsets.",
                    metavar="INTEGER",
                    action="store",
                    type="int")
    parser.add_option("-r", "--random", 
                    metavar="INTEGER",
                    help="Print INTEGER randomly selected subsets.",
                    action="store",
                    type="int")
    options, args = parser.parse_args()
    if len(args) != REQUIRED_NUM_ARGS:
        parser.error("Must have %d arguments" % REQUIRED_NUM_ARGS)
    return options, args

def print_combo(combo):
    #print ' '.join([str(x) for x in get_combo(n, k, i)])
    print(' '.join([str(x) for x in combo]))


def main():
    options, args = _parse_args()
    n, k = int(args[0]), int(args[1])
    if options.index is not None:
        print_combo(get_combo(n, k, options.index))
    elif options.random is not None:
        combos = get_random_subsets(n, k, options.random)
        for i in range(len(combos)):
            print_combo(combos[i])
    else:
        for i in range(get_num_combos(n, k)):
            print_combo(get_combo(n, k, i))
    return 0