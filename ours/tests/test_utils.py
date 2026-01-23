import unittest
from cbct.utils import safe_get

class TestUtils(unittest.TestCase):
    def test_safe_get(self):
        class Dummy:
            def __init__(self):
                self.a = 1
        
        d = Dummy()
        self.assertEqual(safe_get(d, 'a'), 1)
        self.assertIsNone(safe_get(d, 'b'))
        self.assertEqual(safe_get(d, 'b', default=2), 2)

if __name__ == '__main__':
    unittest.main()
