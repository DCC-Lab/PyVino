import unittest
import numpy as np
from dcclab import Database
import os
from ramandb import RamanDB
import requests
import matplotlib.pyplot as plt
from vino import vinoPCA

class TestVInoClass(unittest.TestCase):
    @unittest.skip("NOt now")
    def testInit(self):
        iterable = [31, 30, 30, 30, 80, 31, 33, 31, 30, 30, 30, 30, 30, 30, 30, 30, 104, 30, 30] # sans vin blanc parceque ça shit le aspect ratio
        total = sum(iterable)

        # Data = np.genfromtxt('/Users/Shooshoo/PycharmProjects/PCA_DCCLab/DataVino_Sorted.csv', delimiter=',')
        db = RamanDB()
        data, labels = db.getIntensities()
        wavelengths = db.getWavelengths()
        data = np.cat(wavelengths, wavelengths, data[:,0:total])
        self.assertEqual(data.shape[1], total)
        my_Spectrums = vinoPCA(data, iterable)

        self.assertIsNotNone(my_Spectrums)

    def testRemoveFluo(self):
        iterable = [31, 30, 30, 30, 80, 31, 33, 31, 30, 30, 30, 30, 30, 30, 30, 30, 104, 30, 30] # sans vin blanc parceque ça shit le aspect ratio
        total = sum(iterable)

        # I need to remove this function, I don't have access to the csv file.
        # Data = np.genfromtxt('/Users/Shooshoo/PycharmProjects/PCA_DCCLab/DataVino_Sorted.csv', delimiter=',')
        # After a bit of playing around: column 0 is not used, column 1 is the wavelengths, then its
        # the data
        db = RamanDB()
        data, labels = db.getIntensities()
        wavelengths = db.getWavelengths()
        wavelengths = np.expand_dims(wavelengths, 1)

        data = np.concatenate( (wavelengths, wavelengths, data[:,0:total]), axis=1 )
        # self.assertEqual(data.shape[1], total)
        my_Spectrums = vinoPCA(data, iterable)

        self.assertIsNotNone(my_Spectrums)

        my_Spectrums.removeFLuo(my_Spectrums.Data)


    def testDoPCA(self):
        iterable = [31, 30, 30, 30, 80, 31, 33, 31, 30, 30, 30, 30, 30, 30, 30, 30, 104, 30, 30] # sans vin blanc parceque ça shit le aspect ratio
        total = sum(iterable)

        # Data = np.genfromtxt('/Users/Shooshoo/PycharmProjects/PCA_DCCLab/DataVino_Sorted.csv', delimiter=',')
        db = RamanDB()
        data, labels = db.getIntensities()
        wavelengths = db.getWavelengths()
        wavelengths = np.expand_dims(wavelengths, 1)

        data = np.concatenate( (wavelengths, wavelengths, data[:,0:total]), axis=1 )
        # self.assertEqual(data.shape[1], total)
        my_Spectrums = vinoPCA(data, iterable)

        self.assertIsNotNone(my_Spectrums)

        my_Spectrums.doPCA(10)
        my_Spectrums.showTransformedData3D()
        my_Spectrums.showTransformedData2D()
        my_Spectrums.showEigenvectors()

    def testvinoPCANoArgument(self):
        my_Spectrums = vinoPCA()
        self.assertIsNotNone(my_Spectrums)

        my_Spectrums.doPCA(10)
        my_Spectrums.showTransformedData3D()
        my_Spectrums.showTransformedData2D()
        my_Spectrums.showEigenvectors()

    # def testInitDB(self):
    #     self.assertIsNotNone(vinoPCA().db)

    def testColormap(self):
        vino = vinoPCA()
        cm = vino.getColorMap()
        self.assertIsNotNone(cm)
        spectra, labels = vino.db.getIntensities()
        self.assertEqual(len(cm), len(labels))

    # def testOneSpectrum(self):
    #     vino = vinoPCA()
    #     spectra, labels = vino.db.getIntensities()
    #     plt.plot(spectra[:,1])
    #     newSpectra = vino.removeFLuo(spectra)
    #     print(newSpectra)
    #     # plt.plot(newSpectra)
    #     # plt.show()


if __name__ == "__main__":
    unittest.main()