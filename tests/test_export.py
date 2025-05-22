# tests/test_export.py

import unittest
from dsca_explorer.export import export_layers
import os

class TestExport(unittest.TestCase):
    def test_export_csv(self):
        layers = [{"name": "Test", "type": "TestType", "endpoint": "http://example.com", "formats": "JSON", "properties": {}, "source": "Test", "series": "Test"}]
        export_layers(layers, "test_export.csv")
        self.assertTrue(os.path.exists("test_export.csv"))
        os.remove("test_export.csv")

if __name__ == "__main__":
    unittest.main()
