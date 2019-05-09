# BioPython Debugging

This is a debugging repository to test [TomHarrop](https://github.com/TomHarrop/biopython-index-test)
container that is having issues running on different systems. Specifically, I will
do the following:

## Integrate BioPython
The [base container](https://github.com/TomHarrop/singularity-containers/blob/master/tools/Singularity.biopython_1.73) installs biopython from pip, and I need to get the same version and install from this folder. Specifically, I need to have a custom version that I can edit with print statements, etc. I will modify the recipe here to account for that. To download this original codebase:

```bash
$ wget http://biopython.org/DIST/biopython-1.73.tar.gz
$ tar -xzvf biopython-1.73.tar.gz 
```

I then combined the original recipe with the base image, and changed the biopython install to be from the local folder.

## Build Testing Container
For the first test, I'd just want to build the container, and run it as specified by @TomHarrop
to generate a result. To build:

```bash
$ sudo singularity build biopython.sif Singularity.biopython_index_test
```

And then to run, create another TMPDIR

```bash
mkdir -p /tmp/pancakes
SINGULARITYENV_TMPDIR=/tmp/pancakes
SINGULARITYENV_PYTHONNOUSERSITE=Iamset
export SINGULARITYENV_PYTHONNOUSERSITE SINGULARITYENV_TMPDIR
```

And then run. This should work on a host. Note that the original command had `--nv`, and I had to remove it because my computer is a slow dinosaur.

```bash
$ singularity run -B ${PWD},/tmp -H $(mktemp -d) --pwd ${PWD} --containall  --cleanenv biopython.sif
```

I (think) a successful run just finishes without error? Here is what happened. Note that I added print
statements after the `index_db` command to ensure we finished the function call without triggering
the except:

```bash
$ singularity run -B ${PWD},/tmp -H $(mktemp -d) --pwd ${PWD} --containall  --cleanenv biopython.sif
DEBUG:root:sys.version
DEBUG:root:3.7.3 (default, May  8 2019, 05:28:42) 
[GCC 6.3.0 20170516]
DEBUG:root:sqlite3.version
DEBUG:root:2.6.0
DEBUG:root:platform.python_implementation()
DEBUG:root:CPython
DEBUG:root:platform.platform()
DEBUG:root:Linux-4.15.0-48-generic-x86_64-with-debian-9.9
DEBUG:root:Bio.__version__
DEBUG:root:1.73
DEBUG:root:os.environ
DEBUG:root:environ({'PYTHON_PIP_VERSION': '19.1.1', 'LD_LIBRARY_PATH': '/.singularity.d/libs', 'HOME': '/tmp/tmp.vsWj4fD9OC', 'GPG_KEY': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx', 'PS1': 'Singularity> ', 'PYTHONNOUSERSITE': 'Iamset', 'TMPDIR': '/tmp/pancakes', 'TERM': 'xterm-256color', 'PATH': '/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin', 'LANG': 'C.UTF-8', 'SINGULARITY_APPNAME': '', 'PYTHON_VERSION': '3.7.3', 'SINGULARITY_CONTAINER': '/home/vanessa/Documents/Dropbox/Code/researchapps/biopython-index-test/biopython.sif', 'PWD': '/home/vanessa/Documents/Dropbox/Code/researchapps/biopython-index-test', 'SINGULARITY_NAME': 'biopython.sif'})
```

There is a little temporary folder with an index file, so this is also evidence of working.

```bash
├── tmpjnl64dm_
│   └── r1.idx
```

## Create Debugging BioPython
Now that I have a base case that works, although I am fairly certain I won't reproduce the error (it was done on RHEL),
what I can do is generate a container with enough debugging statements that trace the indexing through and through.
To maintain the original biopython and to separate my customizations, I copied the biopython folder,
and created a  [new Singularity recipe](Singularity.biopython_custom) to use it.

```bash
cp Singularity.biopython_index_test Singularity.biopython_custom
cp -R biopython-1.73 biopython-1.73-custom
```

Next, I inspected the user error:

```bash
ERROR:root:
Traceback (most recent call last):
  File "/usr/local/lib/python3.7/dist-packages/Bio/File.py", line 732, in _build_index
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS "
sqlite3.IntegrityError: UNIQUE constraint failed: offset_data.key

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/path/to/.snakemake/scripts/tmppgoypljn.index_reads.py", line 38, in <module>
    'fastq')
  File "/usr/local/lib/python3.7/dist-packages/Bio/SeqIO/__init__.py", line 1032, in index_db
    key_function, repr)
  File "/usr/local/lib/python3.7/dist-packages/Bio/File.py", line 563, in __init__
    self._build_index()
  File "/usr/local/lib/python3.7/dist-packages/Bio/File.py", line 738, in _build_index
    raise ValueError("Duplicate key? %s" % err)
ValueError: Duplicate key? UNIQUE constraint failed: offset_data.key
```

The error tells us that we are trying to define the same (should be unique) key twice for 
the sqlite3 database:

```
sqlite3.IntegrityError: UNIQUE constraint failed: offset_data.key
```

It also re-affirms our entrypoint is the `init_db` function, which is
used like this in the file:

```python
read_index = SeqIO.index_db(db_file,
                            read_file,
                            'fastq')
```

## Dockerfile

Singularity can't cache builds, so testing a container (and needing to consistently
rebuild) is really hard. Thus, I created a quick [Dockerfile](Dockerfile) to get
the print statements right, and it would be easy to rebuild.

```bash
$ docker build -t vanessa/biopython .
```

To rebuild it took only 27 seconds:

```bash
...
Successfully tagged vanessa/biopython:latest

real	0m27.667s
user	0m0.537s
sys	0m0.800s
```

I could find the entry point fairly easily based on the original import, and the
function name (it's in __init__.py).

```bash
cd biopython-1.73-custom/Bio/SeqIO
$ grep -R index_db
_index.py:is all handled internally by the Bio.SeqIO.index(...) and index_db(...)
_index.py:sequencing. If memory is an issue, the index_db(...) interface stores the
__init__.py:    See Also: Bio.SeqIO.index_db() and Bio.SeqIO.to_dict()
__init__.py:def index_db(index_filename, filenames=None, format=None, alphabet=None,
__init__.py:    >>> records = SeqIO.index_db(idx_name, files, "fasta", generic_protein, get_gi)
__init__.py:    repr = ("SeqIO.index_db(%r, filenames=%r, format=%r, alphabet=%r, key_function=%r)"
```

And then I just traced the whole thing. I added sections surrounded by a header and 
footer so they would be easily found:

```python
    #### DEBUGGING #############
    print("START of call to index_db in biopython.Bio.SeqIO")
    print("index_filename is %s" % index_filename)
    print("filenames are %s" % filenames)
    print("format is %s" % format)
    print("alphabet is %s" % alphabet)
    print("key_function is %s" % key_function)
    #### DEBUGGING #############
```

I tested it once quickly to ensure that the prints would be seen. Note that we don't have to
worry about local binds and the Python user site because it's completely isolated.

```
$ docker run vanessa/biopython
...

DEBUG:root:Read index finished successfully.
START of call to index_db in biopython.Bio.SeqIO
index_filename is /tmp/tmp9jjr16_w/r1.idx
filenames are /r1.fq
format is fastq
alphabet is None
key_function is None
```

Woot! Okay then I added a LOT more of that. One interesting thing I noticed is
that there is one (final?) call to insert *after* we hit end of file (EOF) in
the end of the FastqRandomAccess function. That seems strange to me.

```bash
Inserting batch of 100 offsets, K00171:456:HKGMHBBXX:5:2228:18862:48808 ... K00171:456:HKGMHBBXX:5:2228:29934:49212
EOF
END of of FastqRandomAccess __iter__
Inserting batch of 1 offsets, K00171:456:HKGMHBBXX:5:2228:31517:49247 ... K00171:456:HKGMHBBXX:5:2228:31517:49247
length of random_access_proxies is less than max_open 10
```

## Back to Singularity

When I was content with my print statements, I build the same container again with Singularity. This
is the step you'd want to start at to build my image on your own, and then test it:

```bash
$ git clone https://www.github.com/researchapps/biopython-index-test
$ cd biopython-index-test
$ sudo singularity build biopython-debug.sif Singularity.biopython_custom
```

And if you haven't, do the same as before:

```bash
mkdir -p /tmp/pancakes
SINGULARITYENV_TMPDIR=/tmp/pancakes
SINGULARITYENV_PYTHONNOUSERSITE=Iamset
export SINGULARITYENV_PYTHONNOUSERSITE SINGULARITYENV_TMPDIR
```

And then run.

```bash
$ singularity run -B ${PWD},/tmp -H $(mktemp -d) --pwd ${PWD} --containall  --cleanenv biopython-debug.sif
```

I'm hoping there is enough printing so that we can run this container where the error is being generated,
and trace what is happening better than now. We can adjust the debug statements (more or less)
depending on what we find.
