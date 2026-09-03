import pathlib
import sys
sys.path.insert(0, str(pathlib.Path('packages/ktools-core/src')))
sys.path.insert(0, str(pathlib.Path('packages/ktools-media/src')))

import unittest
from packages.ktools_media.tests.test_media_split_engine import MediaSplitEngineTests

if __name__ == '__main__':
    unittest.main(module='packages.ktools_media.tests.test_media_split_engine')
