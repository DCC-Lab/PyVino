import unittest
import numpy as np
from dcclab import Database
import os
from ramandb import RamanDB
import requests
import re

class TestRamanDatabase(unittest.TestCase):
    def setUp(self):
        self.db = RamanDB()
        # self.db = RamanDB("mysql://127.0.0.1/root@raman")
        self.assertIsNotNone(self.db)

    @unittest.skip("Now in setUp")
    def test01Database(self):
        self.db = RamanDB()
        self.assertIsNotNone(self.db)

    def test02Wavelengths(self):
        self.assertIsNotNone(self.db.getWavelengths())

    def test03WavelengthsAreUniqueAndCommon(self):
        """
        Check that all RAW spectra have the same number of wavelengths.
        This is a complex SQL statement with a sub-select, but it returns 1 if true and 0 if false.
        """
        self.db.execute("""
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
        firstRecord = self.db.fetchOne()
        self.assertEqual(firstRecord["wavelengthsAreAllTheSame"], 1)

    def test04WavelengthsProperty(self):
        self.assertIsNotNone(self.db.wavelengths)

    def test05FileCount(self):
        self.assertIsNotNone(self.db.getFileCount())

    def test06FileCountShouldMatchRawSpectraTimesWavelength(self):
        """
        NUmber of points in the spectra database for 'raw' spectra should be #wavelengths x #files
        """
        rawSpectraCount = self.db.getFileCount()
        wavelengthsCount = len(self.db.getWavelengths())

        self.db.execute("select count(*) as count from spectra where dataType='raw'")
        valueRecord = self.db.fetchOne()
        self.assertEqual(valueRecord["count"], rawSpectraCount*wavelengthsCount)

    def test07FilePaths(self):
        self.assertIsNotNone(self.db.getSpectraPaths())
        self.assertEqual(self.db.getFileCount(), len(self.db.getSpectraPaths()))

    def test08GetWhiteSpectra(self):
        self.db.execute("select count(*) as count from files inner join wines on wines.wineId = files.wineId where wines.color = 'white'")
        firstRecord = self.db.fetchOne()
        whiteWineFileCount = firstRecord["count"]

        matrix, labels = self.db.getSpectraWithId(dataType='raw', color='white')
        self.assertIsNotNone(matrix)

        self.assertEqual(matrix.shape, (len(self.db.wavelengths), whiteWineFileCount))

    def test09GetRedSpectra(self):
        self.db.execute("select count(*) as count from files inner join wines on wines.wineId = files.wineId where wines.color = 'red'")
        firstRecord = self.db.fetchOne()
        redWineFileCount = firstRecord["count"]

        matrix, labels = self.db.getSpectraWithId(dataType='raw', color='red')
        self.assertIsNotNone(matrix)

        self.assertEqual(matrix.shape, (len(self.db.wavelengths), redWineFileCount))

    def test10ReadQEProFile(self):
        wavelengths, intensities = self.db.readQEProFile('originaldata/Q100.txt')
        self.assertEqual(len(intensities), 1044)

    def test11InsertAllSpectra(self):
        dataDir = 'originaldata'
        filenames = os.listdir(dataDir)
        filePaths = []
        for filename in filenames:
            filePaths.append(os.path.join(dataDir, filename))

        inserted = self.db.insertSpectralDataFromFiles(filePaths)
        if inserted == 0:
            self.skipTest("Nothing was inserted")

    def test12ExecuteCount(self):
        self.assertTrue(self.db.executeCount("select count(*) as count from spectra") > 0)

    def test13InsertAllCorrectedSpectra(self):
        self.db.execute("select distinct spectrumId from spectra where spectrumId not in (select spectrumId from spectra where dataType='fluorescence-corrected')")
        records = self.db.fetchAll()
        if len(records) == 0:
            self.skipTest("All corrected spectra exist in the database")

        for record in records:
            spectrumId = record["spectrumId"]
            spectrum, labels = self.db.getSpectrum(dataType='raw', spectrumId=spectrumId)
            if spectrum is None:
                continue
            degree = 100
            correctedSpectrum = self.db.subtractFluorescence(spectrum, polynomialDegree=degree)
            print(spectrumId)
            match = re.search(r"(\d+)-(\d+)", spectrumId)
            wineId = int(match.group(1))
            sampleId = int(match.group(2))
            self.db.insertSpectralData(self.db.wavelengths, correctedSpectrum[:,:], 'fluorescence-corrected', wineId, sampleId, 'BaselineRemoval-nomask-degree{0}'.format(degree))

    @unittest.skip("done")
    def test14BuildWineIdAndSampleId(self):
        self.db.execute('update files set sampleId=substr(path,18,2) where path like "%\_%" ESCAPE "\"')

    def test15WinesSummary(self):
        wineSummary = self.db.getWinesSummary()
        totalNumberOfSpectra = sum([ wine["nSamples"] for wine in wineSummary])

        self.db.execute("select count(*) as count from spectra where dataType='raw'")
        valueRecord = self.db.fetchOne()
        self.assertEqual(valueRecord["count"], totalNumberOfSpectra*len(self.db.getWavelengths()))

    def test16SingleSpectrum(self):
        self.db.execute("select wavelength, intensity from spectra where spectrumId = '0002-0001'")
        records = self.db.fetchAll()
        for record in records:
            print(record)

    def test17DataTypes(self):
        self.assertTrue('raw' in self.db.getDataTypes())

    def test18GetSpectraValidTypeFluorescence(self):
        if 'fluorescence-corrected' in self.db.getDataTypes():
            spectra, spectrumIds = self.db.getSpectraWithId(dataType='fluorescence-corrected')
            self.assertIsNotNone(spectra)
        else:
            self.skipTest("No background-corrected spectra in database")

    def test19GetSpectraInvalidType(self):
        with self.assertRaises(ValueError):
            spectra = self.db.getSpectraWithId(dataType='unknown')

    def test20DatabaseMySQLLocal(self):
        db = RamanDB("mysql://127.0.0.1/root@raman")
        self.assertIsNotNone(db)
        self.assertIsNotNone(db.getWavelengths())

    def test21Wavenumbers(self):
        print(self.db.wavenumbers)

    def test22Mask(self):
        print(sum(self.db.wavelengthMask))
        maskRange = []
        for i, mask in enumerate(self.db.wavelengthMask):
            if mask:
                maskRange.append(i)
        print(self.db.wavelengths[maskRange])

if __name__ == "__main__":
    unittest.main()