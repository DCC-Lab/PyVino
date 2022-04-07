import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.decomposition import PCA
from scipy import interpolate
from BaselineRemoval import BaselineRemoval
from ramandb import RamanDB

class vinoPCA:

    def __init__(self):
        self.db = RamanDB()
        self.constraints = []
        self.data, self.labels = self.db.getSpectraWithId(dataType='raw')
        self.correctedData, correctedLabel = self.db.getSpectraWithId(dataType='fluorescence-corrected')
        self.averageSpectra, self.spectraID = self.db.getAverageSpectra()
        if self.labels != correctedLabel:
            raise ValueError('Not all spectra are corrected')

        self.wavelengths = self.db.getWavelengths()
        self.fullWaveLengths = self.wavelengths

        self.wavelengthMask = range(200, 1000)
        self.data = self.data[self.wavelengthMask, :]
        self.wavelengths = self.wavelengths[self.wavelengthMask]

    def getColorMap(self):

        """
        Creats a colormap to differentiate the samples in the transformed plot
        :return: Return a colormap to visualise different samples on the plot.
        """

        splitId = []
        for i in range(0, len(self.labels)):
            splitId.append(self.labels[i].split("-"))
        colormap = list(map(int, list(zip(*splitId))[0]))

        return np.array(colormap)

    def subtractFluorescence(self):

        """
        Remove fluorescence background from the data.
        :return: A corrected data without the background.
        """

        polynomial_degree = 5
        correctedSpectra = np.empty_like(self.data)
        for i in range(self.data.shape[1]):
            spectre = self.data[:, i]
            correctedSpectra[:, i] = BaselineRemoval(spectre).IModPoly(polynomial_degree)

        return correctedSpectra

    def doPCA(self, n:int):

        """
        Apply PCA on the data given. Redimentionalize in n value of eigenvectors
        :param n: number of componants to get from the PCA
        :return: Returns nothing. Just creats an array of the transformed datas into the new vector space
        """
        self.pca = PCA(n_components=n)
        correctedData = self.subtractFluorescence()
        self.X_reduced = self.pca.fit_transform(correctedData.T)

    def showTransformedData3D(self):

        """
        Plots the data transformed in the new vector space with the three firsts eigenvectors
        :return: None
        """

        plt.clf()
        fig = plt.figure(1, figsize=(8, 6))
        ax = Axes3D(fig, elev=-150, azim=110)
        ax.scatter(
            self.X_reduced[:, 0],
            self.X_reduced[:, 1],
            self.X_reduced[:, 2],
            c=self.getColorMap(),
            cmap='nipy_spectral',
            s=10)
        ax.set_title("First three PCA directions")
        ax.set_xlabel("1st eigenvector")
        ax.w_xaxis.set_ticklabels([])
        ax.set_ylabel("2nd eigenvector")
        ax.w_yaxis.set_ticklabels([])
        ax.set_zlabel("3rd eigenvector")
        ax.w_zaxis.set_ticklabels([])
        plt.show()

    def showTransformedData2D(self):

        """
        Plots the data transformed in the new vector space with the two firsts eigenvectors
        :return: None
        """

        plt.clf()
        plt.figure(2)
        plt.scatter(self.X_reduced[:, 0], self.X_reduced[:, 1], c=self.getColorMap(), cmap='nipy_spectral', s=10)
        plt.title('First two PCA directions')
        plt.xlabel('1st eigenvector')
        plt.ylabel('2nd eigenvector')
        plt.show()

    def showTransformedData1D(self):

        """
        :return: Plots the data transformed in the new vector space along the first eigenvector
        """
        plt.clf()
        plt.figure(3)
        plt.scatter(self.X_reduced[:, 0], np.zeros_like(self.X_reduced[:, 0]), c=self.getColorMap(), cmap='nipy_spectral', s=10)
        ax = plt.gca()
        ax.axes.yaxis.set_visible(False)
        plt.title('First PCA direction')
        plt.xlabel('1st eigenvector')
        plt.show()

    def showAverageInputSpectrums(self):

        """
        Creats a plot of the average spretrums of each independant bottles.
        :return: A plot
        """

        plt.clf()
        plt.figure(4)
        plt.plot(self.fullWaveLengths, self.averageSpectra)
        plt.title('Average spectras')
        plt.xlabel('Wavelength [nm]')
        plt.ylabel('Counts [-]')
        plt.show()


    def getAllEigenvectors(self):

        """
        Function to get all of the eigenvectors created
        :return: an array of n eigenvector
        """

        return self.pca.components_.transpose()

    def showEigenvectors(self):

        """
        Function to visualise eigenvectors
        :return: None
        """
        plt.figure(5)
        plt.title('1st eigenvector')
        plt.plot(self.pca.components_.transpose()[:, 0])
        plt.figure(6)
        plt.title('2nd eigenvector')
        plt.plot(self.pca.components_.transpose()[:, 1])
        plt.figure(7)
        plt.title('3rd eigenvector')
        plt.plot(self.pca.components_.transpose()[:, 2])
        plt.show()

    def getTransformedDatas(self):

        """
        Gives the transformed datas as an array.
        :return: transformed datas
        """

        return self.X_reduced

    def getScreeValues(self):

        """
        Gives the percentage of representation for each new eigenvectors
        :return: array of the scree values, from most important to least
        """

        return self.pca.explained_variance_ratio_

    def plotScreeValues(self):

        """
        Creat a scree plot with the eigenvectors
        :return: None
        """
        varianceRatio = self.pca.explained_variance_ratio_
        numberOfPC = list(range(1, len(self.pca.explained_variance_ratio_)+1))

        fig, ax = plt.subplots()
        ax.bar(numberOfPC, varianceRatio)
        ax.set_xlabel('PC number')
        ax.set_ylabel('Explained variance ratio')
        ax.set_title('Scree plot')
        plt.xticks(numberOfPC)
        for bars in ax.containers:
            ax.bar_label(bars, fmt='%.4f', fontsize=8)
        plt.show()

    def getSingularValues(self):

        """
        Function to get all of the singular values
        :return: an array of n eigenvalues
        """

        return self.pca.singular_values_

    def plotMeanDeviationSpectrum(self):

        """
        Function that plots the mean spectrum with the standard deviation (in grey)
        :return: None
        """

        meanData = np.mean(self.data, axis=1)
        stdData = np.std(self.data)

        plt.figure(8)
        plt.plot(self.wavelengths, meanData)
        plt.fill_between(self.wavelengths, meanData - stdData, meanData + stdData, color='#CCCCCC')
        plt.title('Mean spectrum and standard deviation')
        plt.xlabel('Wavelength (nm)')
        plt.ylabel('Intensity (arb. un.)')
        plt.show()

if __name__ == "__main__":

    my_Spectrums = vinoPCA()
    my_Spectrums.doPCA(10)
    my_Spectrums.showTransformedData3D()
    my_Spectrums.showTransformedData2D()
    my_Spectrums.showEigenvectors()
    my_Spectrums.showAverageInputSpectrums()
