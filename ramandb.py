from dcclab.database import *
import numpy as np
import matplotlib.pyplot as plt
import requests

class RamanDB(Database):
    url = 'https://www.dropbox.com/s/peowchyj7xyib4w/raman.db?dl=1'
    def __init__(self, writePermission=False):  
        """
        Creates the database object for Raman spectra.
        """

        self.databasePath = "raman.db"
        if not os.path.exists(self.databasePath):
            print("The raman.db file is not available. Atttempting to download from {0}".format(self.url))
            filename = self.downloadDatabase()
            if os.path.exists(filename) and not os.path.exists(self.databasePath):
                os.rename(filename, self.databasePath)
                print("Success. File has been renamed raman.db")                

        self._wavelengths = None
        self.progressStart = None
        super().__init__(self.databasePath, writePermission=writePermission)

    def downloadDatabase(self):
        r = requests.get(self.url, allow_redirects=True)
        filename = "raman-download.db"
        with open(filename, 'wb') as file:
            file.write(r.content)
        return filename

    @property
    def wavelengths(self):
        if self._wavelengths is None:
            self._wavelengths = self.getWavelengths()

        return self._wavelengths

    def getWavelengths(self):
        self.execute(r"select distinct(wavelength) from spectra order by wavelength")
        rows = self.fetchAll()
        nTotal = len(rows)

        wavelengths = np.zeros(shape=(nTotal))
        for i,row in enumerate(rows):
            wavelengths[i] = row['wavelength']

        return wavelengths

    def getWineIdentifiers(self):
        
        self.execute(r"select path from spectra inner join files on files.fid = spectra.fid group by spectra.fid")
        rows = self.fetchAll()

        wineIdentifiers = set()
        for row in rows:
            match = re.search(r"([A-Z]+)_?\d+.txt", row["path"])
            if match is not None:
                wineIdentifiers.add(match.group(1))

        return sorted(wineIdentifiers)


    def getCountFiles(self):
        self.execute(r"select count(*) as count from files")
        rows = self.fetchAll()
        if rows is None:
            return 0
        return rows[0]["count"]


    def getSpectraPaths(self):
        self.execute("select path from files order by path")
        rows = self.fetchAll()
        paths = []
        for row in rows:
            paths.append(row['path'])
        return paths

    def getIntensities(self, limit=None):
        stmnt = """
        select wavelength, intensity, files.path from spectra 
        inner join files on files.fid = spectra.fid
        order by files.path, wavelength """

        wavelengths = self.getWavelengths()
        nWavelengths = len(wavelengths)

        if limit is not None:
            stmnt += " limit {0}".format(limit*nWavelengths)

        self.execute(stmnt)
        rows = list(self.fetchAll())

        if rows is None:
            return None
            
        nSamples = len(rows)//nWavelengths
        if nSamples == 0:
            return None

        spectra = np.zeros(shape=(nWavelengths, nSamples))
        wineIdentifiers = [""]*nSamples
        for i,row in enumerate(rows):
            spectra[i%nWavelengths, i//nWavelengths] = float(row['intensity'])
            match = re.search(r"([A-Z]+)_?\d+.txt", row["path"])
            if match is not None:
                wineIdentifiers[i//nWavelengths] = match.group(1)

        return spectra, wineIdentifiers

    def showProgressBar(self, iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
        """
        From: https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console

        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """

        if self.progressStart is None:
            self.progressStart = time.time()

        if time.time() > self.progressStart + 3:
            percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
            filledLength = int(length * iteration // total)
            bar = fill * filledLength + '-' * (length - filledLength)
            print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)

            if iteration == total: 
                print()
        
        if iteration == total: 
            self.progressStart = None

if __name__ == "__main__":
    db = RamanDB()
    spectra, labels = db.getIntensities()
    plt.plot(spectra[:,0:2])
    plt.show()
