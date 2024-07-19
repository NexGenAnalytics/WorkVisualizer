import os
import unittest

from ..api.cali2events import convert_cali_to_json

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(self.test_dir, "data", "cali")
        self.data_files = [os.path.join(self.data_dir, filename) for filename in os.listdir(self.data_dir) if filename.endswith(".cali")]

    def test_reader(self):
        convert_cali_to_json(self.data_files, self.data_dir, maximum_depth_limit=2, write=False)
        assert 1

if __name__ == "__main__":
    unittest.main()
