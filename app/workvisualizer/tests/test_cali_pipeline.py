import os
import sys
import shutil
import unittest

from cali2events import convert_cali_to_json
from logical_hierarchy import generate_logical_hierarchy_from_root



class TestConfig(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.data_dir = os.path.join(self.test_dir, "data")
        self.cali_dir = os.path.join(self.data_dir, "cali")

        # Clear any non-cali directories
        for dir_name in os.listdir(self.data_dir):
            dir_path = os.path.join(self.data_dir, dir_name)
            if dir_name != "cali" and os.path.isdir(dir_path):
                shutil.rmtree(dir_path)

    def test_data_generation(self):
        # Check that we start with only the cali directory
        assert len(os.listdir(self.data_dir)) == 1 and "cali" in os.listdir(self.data_dir)

        # Then read in the cali files
        cali_files = [os.path.join(self.cali_dir, filename) for filename in os.listdir(self.cali_dir) if
                      filename.endswith(".cali")]
        convert_cali_to_json(cali_files, self.data_dir, maximum_depth_limit=2)

        # Now we should have three new directories (so four total)
        updated_data_dir_contents = os.listdir(self.data_dir)
        assert len(updated_data_dir_contents) == 4 and \
               "cali" in updated_data_dir_contents and \
               "events" in updated_data_dir_contents and \
               "unique-events" in updated_data_dir_contents and \
               "metadata" in updated_data_dir_contents

        # Now test that the logical hierarchy is created correctly
        unique_events_dir = os.path.join(self.data_dir, "unique-events")
        unique_events_file = os.path.join(unique_events_dir, os.listdir(unique_events_dir)[0])
        logical_hierarchy_dir = os.path.join(self.data_dir, "logical_hierarchy")
        output_file = os.path.join(logical_hierarchy_dir, "test_logical_hierarchy.json")

        # Run generation script
        generate_logical_hierarchy_from_root(unique_events_file, output_file)

        # Now we should have five total data directories
        updated_data_dir_contents = os.listdir(self.data_dir)
        assert len(updated_data_dir_contents) == 5 and \
               "logical_hierarchy" in updated_data_dir_contents


if __name__ == "__main__":
    unittest.main()
