from distutils.core import setup
import py2exe
import pymunk
import sys
import os

pymunk_dir = os.path.dirname(pymunk.__file__)

sys.argv.append("py2exe")

setup(windows = [{"script":"src/xenoNaturalist.pyw", "icon_resources":[(1,"extranaut.ico")]}],
      options = {'py2exe': {'optimize': 2, 'bundle_files':1} },
      data_files = [os.path.join(pymunk_dir, 'chipmunk.dll') ], 
      zipfile = None, )
