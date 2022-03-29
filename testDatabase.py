import unittest
import numpy as np
from dcclab import Database
import os
from ramandb import RamanDB
import requests
import re

class TestBuildDatabase(unittest.TestCase):
    def test01Database(self):
        db = RamanDB()
        self.assertIsNotNone(db)

    def test02Wavelengths(self):
        db = RamanDB()
        self.assertIsNotNone(db.getWavelengths())

    def test03WavelengthsAreUniqueAndCommon(self):
        """
        Check that all RAW spectra have the same number of wavelengths.
        This is a complex SQL statement with a sub-select, but it returns 1 if true and 0 if false.
        """
        db = RamanDB()
        db.execute("""
        SELECT 
        MAX(spectralPts) = MIN(spectralPts) as wavelengthsAreAllTheSame
        FROM
            (SELECT 
                COUNT(wavelength) AS spectralPts
            FROM
                spectra
            where dataType='raw'
            GROUP BY wavelength) AS something;
        """)
        firstRecord = db.fetchOne()
        self.assertEqual(firstRecord["wavelengthsAreAllTheSame"], 1)

    def test04WavelengthsProperty(self):
        db = RamanDB()
        self.assertIsNotNone(db.wavelengths)

    def test05FileCount(self):
        db = RamanDB()
        self.assertIsNotNone(db.getFileCount())

    def test06FileCountShouldMatchRawSpectraTimesWavelength(self):
        """
        NUmber of points in the spectra database for 'raw' spectra should be #wavelengths x #files
        """
        db = RamanDB()
        rawSpectraCount = db.getFileCount()
        wavelengthsCount = len(db.getWavelengths())

        db.execute("select count(*) as count from spectra where dataType='raw'")
        valueRecord = db.fetchOne()
        self.assertEqual(valueRecord["count"], rawSpectraCount*wavelengthsCount)

    def test07FilePaths(self):
        db = RamanDB()
        self.assertIsNotNone(db.getSpectraPaths())
        self.assertEqual(db.getFileCount(), len(db.getSpectraPaths()))

    def test08GetWhiteSpectra(self):
        db = RamanDB()
        db.execute("select count(*) as count from files inner join wines on wines.wineId = files.wineId where wines.color = 'white'")
        firstRecord = db.fetchOne()
        whiteWineFileCount = firstRecord["count"]

        matrix, labels = db.getSpectraWithId(dataType='raw', color='white')
        self.assertIsNotNone(matrix)

        self.assertEqual(matrix.shape, (len(db.wavelengths), whiteWineFileCount))

    def test09GetRedSpectra(self):
        db = RamanDB()
        db.execute("select count(*) as count from files inner join wines on wines.wineId = files.wineId where wines.color = 'red'")
        firstRecord = db.fetchOne()
        redWineFileCount = firstRecord["count"]

        matrix, labels = db.getSpectraWithId(dataType='raw', color='red')
        self.assertIsNotNone(matrix)

        self.assertEqual(matrix.shape, (len(db.wavelengths), redWineFileCount))

    def testReadQEProFile(self):
        db = RamanDB()
        wavelengths, intensities = db.readQEProFile('originaldata/Q100.txt')
        self.assertEqual(len(intensities), 1044)

    # @unittest.skip("Done to fix a bad import, no need to redo")
    def testInsertAllSpectra(self):
        db = RamanDB()
        dataDir = 'originaldata'
        filenames = os.listdir(dataDir)
        filePaths = []
        for filename in filenames:
            filePaths.append(os.path.join(dataDir, filename))

        db.insertSpectralDataFromFiles(filePaths)

    def testInsertAllCorrectedSpectra(self):
        db = RamanDB()
        spectra, labels = db.getSpectraWithId(dataType='raw')
        degree = 100
        correctedSpectra = db.subtractFluorescence(spectra, polynomialDegree=degree)

        for i, label in enumerate(labels):
            print("{0}/{1}".format(i, len(labels)))

            match = re.search(r"(\d+)-(\d+)", label)
            wineId = int(match.group(1))
            sampleId = int(match.group(2))
            db.insertSpectralData(db.wavelengths, correctedSpectra[:,i], 'fluorescence-corrected', wineId, sampleId, 'BaselineRemoval-nomask-degree{0}'.format(degree))

    @unittest.skip("done")
    def testBuildWineIdAndSampleId(self):
        db.execute('update files set sampleId=substr(path,18,2) where path like "%\_%" ESCAPE "\"')

    def testWinesSummary(self):
        db = RamanDB()
        wineSummary = db.getWinesSummary()
        totalNumberOfSpectra = sum([ wine["nSamples"] for wine in wineSummary])

        db.execute("select count(*) as count from spectra where dataType='raw'")
        valueRecord = db.fetchOne()
        self.assertEqual(valueRecord["count"], totalNumberOfSpectra*len(db.getWavelengths()))

    @unittest.skip("This function is not ready")
    def testStoreCorrectedSpectra(self):
        db = RamanDB()
        db.storeCorrectedSpectra()

    def testSingleSpectrum(self):
        db = RamanDB()
        db.execute("select wavelength, intensity from spectra where spectrumId = '0002-0001'")
        records = db.fetchAll()
        for record in records:
            print(record)

    def testDataTypes(self):
        db = RamanDB()
        self.assertTrue('raw' in db.getDataTypes())

    def testGetSpectraValidTypeFluorescence(self):
        db = RamanDB()
        if 'fluorescence-corrected' in db.getDataTypes():
            spectra, spectrumIds = db.getSpectraWithId(dataType='fluorescence-corrected')
            self.assertIsNotNone(spectra)
        else:
            self.skipTest("No background-corrected spectra in database")

    def testGetSpectraInvalidType(self):
        db = RamanDB()
        with self.assertRaises(ValueError):
            spectra = db.getSpectraWithId(dataType='unknown')

if __name__ == "__main__":
    unittest.main()