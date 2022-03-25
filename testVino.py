import unittest
import numpy as np
from dcclab import Database
import os
from ramandb import RamanDB
import requests
from vino import vinoPCA

class TestVInoClass(unittest.TestCase):
    def testInit(self):
        vinoPCA()


if __name__ == "__main__":
    unittest.main()