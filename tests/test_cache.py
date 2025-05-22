# tests/test_cache.py

import unittest
from dsca_explorer.cache import detect_new_or_updated_layers

class TestCache(unittest.TestCase):
    def test_detect_new_or_updated_layers(self):
        layers = [{"name": "Test", "type": "TestType", "endpoint": "http://example.com", "formats": "JSON", "properties": {}, "source": "Test", "series": "Test"}]
        new, updated = detect_new_or_updated_layers(layers)
        self.assertIsInstance(new, list)
        self.assertIsInstance(updated, list)

if __name__ == "__main__":
    unittest.main()
