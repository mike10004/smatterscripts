from random import random
import math
from unittest import TestCase
from calculation.bestcircle import Point
from calculation.bestcircle import fit_circle


class FitCircleTest(TestCase):

    def test_fit_circle(self):
        p = self._create_random_points()
        x, y, r = fit_circle(p)
        self.assertEqual((0, 0, 1), (x, y, r))

    def _create_random_points(self, delta=0.8):
        #~ Random points are constructed which lie roughly on a circle
        #~ of radius 4 having the origin as center.
        #~ delta*0.5 is the maximal distance in x- and y- direction of the random
        #~ points from the circle line.
        p = []
        for i in range(0, 100):
            angle = random()*2*math.pi
            co = 4*math.cos(angle)+delta*(random()-0.5)
            si = 4*math.sin(angle)+delta*(random()-0.5)
            p.append(Point(co, si))
        return p

