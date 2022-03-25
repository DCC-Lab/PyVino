import unittest
import numpy as np
from dcclab import Database
import os
from ramandb import RamanDB
import requests
from vino import vinoPCA

class TestVInoClass(unittest.TestCase):
    def testInit(self):
        self.assertIsNotNone(vinoPCA())

    def testInitDB(self):
        self.assertIsNotNone(vinoPCA().db)

    def testColormap(self):
        vino = vinoPCA()
        cm = vino.getColorMap()
        self.assertIsNotNone(cm)
        spectra, labels = vino.db.getIntensities()
        self.assertEqual(len(cm), len(labels))

if __name__ == "__main__":
    unittest.main()