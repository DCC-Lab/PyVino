import unittest
import numpy as np
from dcclab import Database
import os
from ramandb import RamanDB
import requests

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

    @unittest.skip("Ok, tested")
    def testGetIntensity(self):
        db = RamanDB()
        matrix, labels = db.getIntensities()
        self.assertIsNotNone(matrix)
        self.assertEqual(matrix.shape, (len(db.wavelengths), db.getFileCount()))


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
        totalNumberOfSpectra = sum([ wine["nSamples"] for wine in wineSummary])

        db.execute("select count(*) as count from spectra where dataType='raw'")
        valueRecord = db.fetchOne()
        self.assertEqual(valueRecord["count"], totalNumberOfSpectra*len(db.getWavelengths()))

    def testStoreCorrectedSpectra(self):
        db = RamanDB()
        db.storeCorrectedSpectra()

    def testSingleSpectrum(self):
        db = RamanDB()
        db.execute("select wavelength, intensity from spectra where spectrumId = '0002-0001'")
        records = db.fetchAll()
        for record in records:
            print(record)

    # def testStoreSingleSpectrum(self):
    #     spectra, spectrumIds = self.getSpectraWithId(dataType='raw')
    #     correctedSpectra = self.subtractFluorescence(spectra)
    #     for i in range( correctedSpectra.shape[1]):
    #         spectrumId = spectrumIds[i]
    #         print("Running for spectrum {0}".format(spectrumId))
    #         for x,y in zip(self.wavelengths, correctedSpectra[:,i]):
    #             # self.execute("insert into spectra (wavelength, intensity, spectrumId, dataType, algorithm, dateAdded) values(?, ?, ?, 'fluorescence-corrected', 'BaselineRemoval-degree5', datetime())", (x,y, spectrumId))
    #             self.execute("insert into spectra (wavelength, intensity, spectrumId, dataType, algorithm, dateAdded) values(%s, %s, %s, 'fluorescence-corrected', 'BaselineRemoval-degree5', datetime())",(x, y, spectrumId))

    def testDataTypes(self):
        db = RamanDB()
        self.assertTrue('raw' in db.getDataTypes())

    def testGetSpectraValidType(self):
        db = RamanDB()
        spectra, spectrumIds = db.getSpectraWithId(dataType='raw')
        self.assertIsNotNone(spectra)

    def testGetSpectraValidTypeFluorescence(self):
        db = RamanDB()
        spectra, spectrumIds = db.getSpectraWithId(dataType='fluorescence-corrected')
        self.assertIsNotNone(spectra)

    def testGetSpectraInvalidType(self):
        db = RamanDB()
        with self.assertRaises(ValueError):
            spectra = db.getSpectraWithId(dataType='unknown')

if __name__ == "__main__":
    unittest.main()