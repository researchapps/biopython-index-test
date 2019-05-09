#!/usr/bin/env python3

import Bio
from Bio import SeqIO
import logging
import os
import platform
import sqlite3
import sys
import tempfile

# set up log
logging.basicConfig(level=logging.DEBUG)

# debug biopython issue
logging.debug('sys.version')
logging.debug(sys.version)
logging.debug('sqlite3.version')
logging.debug(sqlite3.version)
logging.debug('platform.python_implementation()')
logging.debug(platform.python_implementation())
logging.debug('platform.platform()')
logging.debug(platform.platform())
logging.debug('Bio.__version__')
logging.debug(Bio.__version__)
logging.debug('os.environ')
logging.debug(os.environ)


read_file = '/r1.fq'

outdir = tempfile.mkdtemp(dir=os.environ.get('PWD'))
db_file = os.path.join(outdir, 'r1.idx')

try:
    read_index = SeqIO.index_db(db_file,
                                read_file,
                                'fastq')

    logging.debug("Read index finished successfully.")

except Exception as e:
    logging.exception('')
    raise e
