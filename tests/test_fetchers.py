# tests/test_fetchers.py

import unittest
from dsca_explorer.fetchers.fema import fetch_arcgis_layers_all, fetch_openfema_layers

class TestFEMAFetchers(unittest.TestCase):
    def test_fetch_arcgis_layers_all(self):
        result = fetch_arcgis_layers_all()
        self.assertIsInstance(result, dict)
        self.assertIn('layers', result)
        self.assertIsInstance(result['layers'], list)

    def test_fetch_openfema_layers(self):
        layers = fetch_openfema_layers()
        self.assertIsInstance(layers, list)
        if layers:
            self.assertIn('name', layers[0])

if __name__ == "__main__":
    unittest.main()
