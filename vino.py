import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sklearn.decomposition import PCA
from scipy import interpolate
from BaselineRemoval import BaselineRemoval


class vinoPCA:

    def __init__(self, Data, numberOfEachSamples):

        """
        :param Data: The data on wich PCA should be done.
        :param colormap: An iterable that contains how many of each samples there is in Data, in the good order.
        """

        self.Data = Data
        self.numberOfEachSamples = numberOfEachSamples

    def getColorMap(self):

        """
        Creats a colormap to differentiate the samples in the transformed plot
        :return: Return a colormap to visualise different samples on the plot.
        """

        for i in range(0, len(self.numberOfEachSamples)):
            if i == 0:
                colormap = np.zeros(self.numberOfEachSamples[0])
            else:
                colormap = np.append(colormap, np.ones(self.numberOfEachSamples[i]) *5*i)

        return colormap

    def removeFLuo(self, Data):

        """
        Remove fluorescence background from the data given.
        :param Data: The Data from witch you wish to remove fluo background.
        :return: A new set of Data without the background.
        """

        nm = Data[:, 1]
        cm = 1 / (632.8e-9) - 1 / (nm * 1e-9)
        size = np.ma.size(Data, 1)
        polynomial_degree = 100
        filtered_datas = np.zeros(shape=(800, size - 1))

        # for column in range(2, size):
        #     y = Data[:, column]
        #     d = 25
        #     f2 = interpolate.interp1d(cm[199:][::d], y[199:][::d], kind='quadratic')
        #     y = y[200:1000] - f2(cm[200:1000])
        #     y = (y - min(y)) / max(y - min(y))
        #     filt_datas[:, column - 1] = y
        # filt_datas[:, 0] = cm[200:1000]

        for column in range(2, size):
            spectre = Data[200:1000, column]
            baseObj = BaselineRemoval(spectre)
            values = baseObj.IModPoly(polynomial_degree)
            # values = values - min(values) # Si tu normalises, tu perds les composants communs (Alcool particulèrement)
            # values = values/max(values)   # tu perds aussi le degrés de présence (Plus ou moins bouchonné ?)
                                            # Si tu normalises pas, tu favorises les composants communs présents à
                                            # différents degrés (Plus ou moins d'alcool). Donc tester avec et sans?
            filtered_datas[:, column - 1] = values

        filtered_datas[:, 0] = Data[200:1000, 1]

        return filtered_datas

    def doPCA(self, n:int):

        """
        Apply PCA on the data given. Redimentionalize in n value of eigenvectors
        :param n: number of componants to get from the PCA
        :return: Returns nothing. Just creats an array of the transformed datas into the new vector space
        """

        new_Datas = self.removeFLuo(self.Data)
        new_Datas = np.transpose(new_Datas)
        self.X_PCA = PCA(n_components=n)
        self.X_reduced = self.X_PCA.fit_transform(new_Datas[1:, :])

    def showTransformedData3D(self):

        """
        Plots the data transformed in the new vector space with the three firsts eigenvectors
        :return: None
        """

        plt.clf()
        fig = plt.figure(1, figsize=(8, 6))
        ax = Axes3D(fig, elev=-150, azim=110)
        ax.scatter(
            self.X_reduced[:700, 0],
            self.X_reduced[:700, 1],
            self.X_reduced[:700, 2],
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
        plt.scatter(self.X_reduced[:700, 0], self.X_reduced[:700, 1], c=self.getColorMap(), cmap='nipy_spectral', s=10)
        plt.title('First two PCA directions')
        plt.xlabel('1st eigenvector')
        plt.ylabel('2nd eigenvector')
        plt.show()

    def showTransformData1D(self):

        """
        :return: Plots the data transformed in the new vector space along the first eigenvector
        """
        pass

    def getAllEigenvectors(self):

        """
        Function to get all of the eigenvectors created
        :return: an array of n eigenvector
        """

        return self.X_PCA.components_.transpose()

    def showEigenvectors(self):

        """
        Function to visualise eigenvectors
        :return: None
        """
        plt.figure(3)
        plt.title('1st eigenvector')
        plt.plot(self.X_PCA.components_.transpose()[:, 0])
        plt.figure(4)
        plt.title('2nd eigenvector')
        plt.plot(self.X_PCA.components_.transpose()[:, 1])
        plt.figure(5)
        plt.title('3rd eigenvector')
        plt.plot(self.X_PCA.components_.transpose()[:, 2])
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

        return self.X_PCA.explained_variance_ratio_

    def plotScreeValues(self):

        """
        Creat a scree plot with the eigenvectors
        :return: None
        """

        pass


if __name__ == "__main__":

    iterable = [31, 30, 30, 30, 80, 31, 33, 31, 30, 30, 30, 30, 30, 30, 30, 30, 104, 30, 30] # sans vin blanc parceque ça shit le aspect ratio
    Data = np.genfromtxt('/Users/Shooshoo/PycharmProjects/PCA_DCCLab/DataVino_Sorted.csv', delimiter=',')

    my_Spectrums = vinoPCA(Data, iterable)
    my_Spectrums.doPCA(10)
    my_Spectrums.showTransformedData3D()
    my_Spectrums.showTransformedData2D()
    my_Spectrums.showEigenvectors()
