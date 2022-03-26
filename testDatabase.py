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
        self.assertIsNotNone(db.getFileCount())
        self.assertEqual(db.getFileCount(), 709)

    def testFilePaths(self):
        db = RamanDB()
        self.assertIsNotNone(db.getSpectraPaths())
        self.assertEqual(db.getFileCount(), len(db.getSpectraPaths()))

    def testGetIntensity(self):
        db = RamanDB()
        matrix, labels = db.getIntensities()
        self.assertIsNotNone(matrix)
        self.assertEqual(matrix.shape, (len(db.wavelengths), db.getFileCount()))

    @unittest.skip("Ok, tested")
    def testDownload(self):
        url = 'https://www.dropbox.com/s/2st0sv7jpii6dz8/raman.db?dl=1'
        r = requests.get(url, allow_redirects=True)
        with open('test.db', 'wb') as file:
            file.write(r.content)

    @unittest.skip("Ok, tested")
    def testDownload(self):
        db = RamanDB()
        filename = db.downloadDatabase()
        self.assertTrue(os.path.exists(filename))
        os.remove(filename)

    @unittest.skip("Done, no need to redo.")
    def testAddFileIdToDatabase(self):
        db = RamanDB(writePermission=True)
        db.execute("select * from files order by path")
        records = db.fetchAll()
        for i, record in enumerate(records):
            db.execute("update files set fid={0} where md5='{1}'".format(i, record["md5"]))

        db.execute("select spectra.md5, files.fid from spectra inner join files on files.md5 = spectra.md5")
        records = db.fetchAll()
        for i, record in enumerate(records):
            statement = "update spectra set fid={0} where md5='{1}'".format(record["fid"], record["md5"])
            db.execute(statement)

    @unittest.skip("done")
    def testBuildWineIdAndSampleId(self):
        db.execute('update files set sampleId=substr(path,18,2) where path like "%\_%" ESCAPE "\"')

    def testWineIdentifiers(self):
        db = RamanDB()
        print(db.getIdentifiers())

    def testWinesSummary(self):
        db = RamanDB()
        wineSummary = db.getWinesSummary()
        print(wineSummary)

    def testStoreCorrectedSpectra(self):
        db = RamanDB(writePermission=False)
        db.storeCorrectedSpectra()

    def testDataTypes(self):
        db = RamanDB(writePermission=False)
        print(db.getDataTypes())

    def testGetSpectraValidType(self):
        db = RamanDB(writePermission=False)
        spectra, spectrumIds = db.getSpectraWithId(dataType='raw')
        self.assertIsNotNone(spectra)

    def testGetSpectraValidTypeFluorescence(self):
        db = RamanDB(writePermission=False)
        spectra, spectrumIds = db.getSpectraWithId(dataType='fluorescence-corrected')
        self.assertIsNotNone(spectra)

    def testGetSpectraInvalidType(self):
        db = RamanDB(writePermission=False)
        with self.assertRaises(ValueError):
            spectra = db.getSpectraWithId(dataType='unknown')

if __name__ == "__main__":
    unittest.main()