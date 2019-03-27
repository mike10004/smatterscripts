from unittest import TestCase
from _common import predicates

class AlwaysTest(TestCase):

    # noinspection PyArgumentList
    def test_true(self):
        f = predicates.always_true()
        self.assertTrue(f())
        self.assertTrue(f(1))
        self.assertTrue(f('a'))
        self.assertTrue(f(1, 2))
        self.assertTrue(f(foo='bar'))

    # noinspection PyArgumentList
    def test_false(self):
        f = predicates.always_false()
        self.assertFalse(f())
        self.assertFalse(f(1))
        self.assertFalse(f('a'))
        self.assertFalse(f(1, 2))
        self.assertFalse(f(foo='bar'))


class AndTest(TestCase):

    def test_stuff(self):
        t = predicates.always_true()
        f = predicates.always_false()
        test_cases = [
            (t, t, True),
            (t, f, False),
            (f, t, False),
            (f, f, False),
        ]
        for a, b, expected in test_cases:
            with self.subTest():
                c = predicates.And(a, b)
                actual = c()
                self.assertEqual(expected, actual, "no args")
            with self.subTest():
                c = predicates.And(a, b)
                self.assertEqual(expected, c(1), "one string arg")
            with self.subTest():
                c = predicates.And(a, b)
                self.assertEqual(expected, c('a'), "one int arg")
            with self.subTest():
                c = predicates.And(a, b)
                self.assertEqual(expected, c(1, 2), "two args")
            with self.subTest():
                c = predicates.And(a, b)
                self.assertEqual(expected, c(foo='bar'), "kw arg")
