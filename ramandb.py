from dcclab.database import *
import numpy as np
import requests
from BaselineRemoval import BaselineRemoval

class RamanDB(Database):
    url = 'https://www.dropbox.com/s/peowchyj7xyib4w/raman.db?dl=1'
    def __init__(self, writePermission=False):  
        """
        Creates the database object for Raman spectra.

        The information as entered by people is here: https://docs.google.com/spreadsheets/d/1CgXRyIr7q3P26GP8Km4r9LuLH5o2APFj-4B72niTI1g/edit#gid=0
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
        self.constraints = []
        super().__init__(self.databasePath, writePermission=writePermission)

    def showHelp(self):
        print("""
        All wines obtained from the group are in this database. Things to know:
        * Wines are identified with a "wineId" that is A,B,C, .... AA, AB, AC, .... etc.
        * Each wine has a number a spectrum acquisitions associated with it (typically 30, 60, etc...)
        * When a Raman spectrum is acquired
        
        """)

    def execute(self, statement, bindings=None):
        """
        This function with "bindings" is necessary to handle binary data: it cannot be inserted with a string statement.
        The bindings are explained here: https://zetcode.com/db/sqlitepythontutorial/ and are similar to .format()
        but are handled properly by the sqlite3 module instead of a python string. Without it, binary data
        is inserted as a string, which is not good.

        See insertFileContentIntoSources() for an example.

        """
        if bindings is None:
            super().execute(statement) # Call the original function from dcclab.database
        else:
            self.cursor.execute(statement, bindings)

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

    def getDataTypes(self):
        self.execute('select dataType from spectra group by dataType')
        rows = self.fetchAll()
        dataTypes = []
        for row in rows:
            dataTypes.append(row["dataType"])

        return dataTypes

    def getIdentifiers(self):
        self.execute(r"select count(*) as count, wineId as id from files group by wineId order by wineId;")
        rows = self.fetchAll()
        identifiers = {}
        for row in rows:
            id = row["id"]
            nSamples = row["count"]
            identifiers[id] = nSamples
        return identifiers

    def getWinesSummary(self):
        self.execute(r"select files.wineId,  count(*) as nSamples, wines.* from files inner join wines on wines.wineId = files.wineId group by files.wineId order by files.wineId")
        rows = self.fetchAll()
        wines = []
        for row in rows:
            wines.append(dict(row))
        return wines

    def getFileCount(self):
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
        return self.getSpectraWithWineId(limit=limit)

    def getSpectraWithId(self, dataType=None, limit=None):
        possibleDataTypes = self.getDataTypes()

        if dataType is None:
            dataType = 'raw'

        if dataType not in possibleDataTypes:
            raise ValueError('Possible dataTypes are {0}'.format(possibleDataTypes))

        stmnt = """
        select wavelength, intensity, spectra.spectrumId, wines.* from spectra 
        inner join files on files.spectrumId = spectra.spectrumId
        inner join wines on wines.wineId = files.wineId
        where dataType = '{0}'
        order by files.path, wavelength """.format(dataType)

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
        spectrumIdentifiers = [""]*nSamples
        for i,row in enumerate(rows):
            spectra[i%nWavelengths, i//nWavelengths] = float(row['intensity'])
            spectrumIdentifiers[i//nWavelengths] = row['spectrumId']

        return spectra, spectrumIdentifiers

    def storeCorrectedSpectra(self):
        spectra, spectrumIds = self.getSpectraWithId()
        correctedSpectra = self.subtractFluorescence(spectra)
        for i in range( correctedSpectra.shape[1]):
            spectrumId = spectrumIds[i]
            print("Running for spectrum {0}".format(spectrumId))
            for x,y in zip(self.wavelengths, correctedSpectra[:,i]):
                self.execute("insert into spectra (wavelength, intensity, spectrumId, dataType, algorithm, dateAdded) values(?, ?, ?, 'fluorescence-corrected', 'BaselineRemoval-degree5', datetime())", (x,y, spectrumId))

    def subtractFluorescence(self, rawSpectra, polynomialDegree=5):

        """
        Remove fluorescence background from the data.
        :return: A corrected data without the background.
        """

        correctedSpectra = np.empty_like(rawSpectra)
        for i in range(rawSpectra.shape[1]):
            spectrum = rawSpectra[:, i]
            correctedSpectra[:, i] = BaselineRemoval(spectrum).IModPoly(polynomialDegree)

        return correctedSpectra

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
