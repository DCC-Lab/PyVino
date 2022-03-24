import unittest
import numpy as np
from dcclab import Database
import os
from ramandb import RamanDB
import requests

class TestBuildDatabase(unittest.TestCase):
    def testDatabase(self):
        db = RamanDB()
        self.assertIsNotNone(db)
        self.assertTrue(os.path.exists(db.databasePath))

    def testWavelengths(self):
        db = RamanDB()
        self.assertIsNotNone(db.getWavelengths())
        self.assertEqual(len(db.getWavelengths()), 1044)

    def testWavelengthsProperty(self):
        db = RamanDB()
        self.assertIsNotNone(db.wavelengths)
        self.assertEqual(len(db.wavelengths), 1044)

    def testFileCount(self):
        db = RamanDB()
        self.assertIsNotNone(db.getCountFiles())
        self.assertEqual(db.getCountFiles(), 709)

    def testFilePaths(self):
        db = RamanDB()
        self.assertIsNotNone(db.getSpectraPaths())
        self.assertEqual(db.getCountFiles(), len(db.getSpectraPaths()))

    def testGetIntensity(self):
        db = RamanDB()
        matrix = db.getIntensities()
        self.assertIsNotNone(matrix)
        self.assertEqual(matrix.shape, (len(db.wavelengths), db.getCountFiles()))
        
    def testDownload(self):
        url = 'https://www.dropbox.com/s/2st0sv7jpii6dz8/raman.db?dl=1'
        r = requests.get(url, allow_redirects=True)
        with open('test.db', 'wb') as file:
            file.write(r.content)

    def testDownload(self):
        db = RamanDB()
        db.downloadDatabase()
        self.assertTrue(os.path.exists('raman-download.db'))
        
if __name__ == "__main__":
    unittest.main()