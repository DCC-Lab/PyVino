# PyVino

Projet d'identification et caracterisation des vins avec la spectroscopie Raman.

Le plan est d'utiliser une analyse par composantes principales (PCA) avec le module SKlearn.

## Context

To be written.







## Database

### Usage

You can do :

```python
import ramandb

db = RamanDB()
matrix = db.getIntensities() 
```

to get th spectra.  You should run the tests `testDatabase.py` to confirm everything is working. The database will be downloaded if needed.



### Building the database

You do not need to do that. This is for reference.

It is easier to use a database to get all the spectra easily, with all their metadata. The first step is to create the database.

The database used is currently `sqlite3`, available on macOS by default, and downloadable for Windows. We open the (empty) database:

```shell
sqlite3 raman.db
```

We create the first table that will contain the name of the spectral files.

```sqlite
CREATE TABLE spectralfiles (path text, md5 text, fileId integer primary key autoincrement, date text);
```

Using a quick Unix command, we can get all files with their "hash"  (a unique identifier). We format and then write to a csv file for import:

```shell
find . -name "*.txt" -exec md5 {} \; > files+md5.txt
perl formatmd5.pl < files+md5.txt > files.csv
```

Then, back into `sqlite3 raman.db`, we actually import:

```sqlite
.mode csv
.sep "|"
.import files.csv spectralfiles
```

Then we import all spectra. From the Terminal, we get the files and format them:

```shell
find . -name "*csv" -exec python3 formatspectroforimport.py {} \; > importall.csv
```

then import the files.

```sqlite
.mode csv
.sep "|"
.import files.csv importall.csv
```



### Database schema

```sqlite
CREATE TABLE files (path text, md5 text primary key, date text );
CREATE TABLE spectra (wavelength real, intensity real, md5 text);
CREATE INDEX md5Idx on spectra(md5);
CREATE INDEX md5Idx2 on files(md5);
CREATE INDEX waveIdx on spectra(wavelength);
CREATE TABLE samples (name text, identifier text, type text, grape text, alcohol number, url text);

```

