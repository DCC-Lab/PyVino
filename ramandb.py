from dcclab.database import *
import numpy as np
import requests
from BaselineRemoval import BaselineRemoval

class RamanDB(Database):
    def __init__(self):
        """
        The Database is a MySQL database on cafeine called `raman`.
        """
        url = "mysql://dcclab@cafeine2.crulrg.ulaval.ca/dcclab@raman"

        self._wavelengths = None
        self.progressStart = None
        self.constraints = []
        super().__init__(url)

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

    @property
    def wavelengths(self):
        if self._wavelengths is None:
            self._wavelengths = self.getWavelengths()

        return self._wavelengths

    def readQEProFile(self, filePath):
        # text_file = open(filePath, "br")
        # hash = hashlib.md5(text_file.read()).hexdigest()
        # text_file.close()

        text_file = open(filePath, "r")
        lines = text_file.read().splitlines()

        wavelengths = []
        intensities = []
        for line in lines:
            match = re.match(r'^\s*(\d+\.?\d+)\s+(-?\d*\.?\d*)', line)
            if match is not None:
                intensity = match.group(2)
                wavelength = match.group(1)
                wavelengths.append(wavelength)
                intensities.append(intensity)
            else:
                pass
                # print("Line does not match: {0}".format(line))
        return wavelengths, intensities

    def insertSpectralDataFromFiles(self, filePaths):
        for filePath in filePaths:
            match = re.search(r'([A-Z]{1,2})_?(\d{1,3})\.', filePath)
            if match is None:
                raise ValueError("The file does not appear to have a valid name: {0}".format(filePath))

            wineId = int(ord(match.group(1))-ord('A'))
            sampleId = int(match.group(2))
            spectrumId = "{0:04}-{1:04d}".format(wineId, sampleId)

            print("Inserting {0}".format( filePath ))
            wavelengths, intensities = self.readQEProFile(filePath)
            self.insertSpectralData(wavelengths, intensities, 'test', wineId, sampleId)

    def insertSpectralData(self, wavelengths, intensities, dataType, wineId, sampleId, algorithm=None):
        spectrumId = "{0:04}-{1:04d}".format(wineId, sampleId)

        values = []
        for x,y in zip(wavelengths, intensities):
            values.append("({0}, {1}, '{2}', {3}, {4}, '{5}', now(), '{6}') ".format(x,y, dataType, wineId, sampleId, spectrumId, algorithm))

        bigStatement = "insert into spectra (wavelength, intensity, dataType, wineId, sampleId, spectrumId, dateAdded, algorithm) values" + ','.join(values)
        self.execute( bigStatement)

    def getWavelengths(self):
        self.execute(r"select distinct(wavelength) from spectra where dataType='raw' order by wavelength")
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

    def getWineIds(self):
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

    def getSpectraWithId(self, dataType=None, color=None, limit=None):
        whereConstraints = []
        possibleDataTypes = self.getDataTypes()

        if dataType is None:
            dataType = 'raw'
        if dataType not in possibleDataTypes:
            raise ValueError('Possible dataTypes are {0}'.format(possibleDataTypes))
        whereConstraints.append("dataType = '{0}'".format(dataType))

        if color is not None:
            whereConstraints.append("color = '{0}'".format(color))

        if len(whereConstraints) != 0:
            whereClause = "where " + " and ".join(whereConstraints)
        else:
            whereClause = ""

        stmnt = """
        select wavelength, intensity, spectra.spectrumId, wines.* from spectra 
        inner join files on files.spectrumId = spectra.spectrumId
        inner join wines on wines.wineId = spectra.wineId
        {0}
        order by spectra.spectrumId, spectra.wavelength """.format(whereClause )

        wavelengths = self.getWavelengths()
        nWavelengths = len(wavelengths)

        if limit is not None:
            stmnt += " limit {0}".format(limit*nWavelengths)

        self.execute(stmnt)

        rows = []
        row = self.fetchOne()
        while row is not None:
            rows.append(row)
            if len(rows) % 100 == 0:
                print(".", end='')
            row = self.fetchOne()

        nSamples = len(rows)//nWavelengths
        if nSamples == 0:
            return None

        spectra = np.zeros(shape=(nWavelengths, nSamples))
        spectrumIdentifiers = [""]*nSamples
        for i,row in enumerate(rows):
            spectra[i%nWavelengths, i//nWavelengths] = float(row['intensity'])
            spectrumIdentifiers[i//nWavelengths] = row['spectrumId']

        return spectra, spectrumIdentifiers

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
