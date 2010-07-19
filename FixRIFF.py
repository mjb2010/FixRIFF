#!/usr/local/bin/python
"""
FixRIFF.py
Copyright 2010 Mike J. Brown <mike@skew.org>

This software is released under the terms of whichever license your project
requires: The MIT License (see MIT-License.txt), or the GNU Public License
(Version 3 or any later version; see GPL-License.txt for Version 3).

Python 2.x required.
"""
__version__ = '2010-07-19'

import os, struct, sys

#
# This initial version is very crude, doing almost no sanity checks.
# It assumes the presence of a simple 44-byte RIFF header followed by nothing but
# valid subchunk data (i.e., no metadata tags tacked onto the end!)
#
# It was written to solve a problem where some 16-bit, 44.1 kHz PCM-containing
# WAVs had undercounted ChunkSize and SubChunkSize values.
# Software reading such WAVs will typically honor the stated values, discarding
# any incomplete samples if necessary. This is good, because you don't want to
# treat tags (e.g. ID3 tags) as if they were audio data, but it's bad if the
# values are wrong and you really do have audio data beyond where the chunks
# supposedly end.
#

# make a list of wav files to read
wavs = filter(lambda s: s.endswith(".wav") and not s.endswith("-fixed.wav"), os.listdir(os.getcwd()))
if not wavs:
    print "No candidate .wav files found in current folder."
    sys.exit(99)

# for each file...
for wav in wavs:
    # open an input file and output file
    infile = open(wav, 'rb')
    print "Processing file: %s" % wav
    fixedwav = wav[:-4] + '-fixed.wav'
    # read the first 44 bytes of the input file
    header = infile.read(44)
    if len(header) < 44:
        print "Header too small (%d bytes)" % len(header)
        continue

    # get chunksize by unpacking bytes 5-8
    chunksizedata = header[4:8]
    chunksize = struct.unpack('<L', chunksizedata)[0]
    # get subchunksize by unpacking bytes 41-44
    subchunksizedata = header[40:44]
    subchunksize = struct.unpack('<L', subchunksizedata)[0]
    # get filesize
    filesize = os.fstat(infile.fileno()).st_size

    # see if there's anything to do
    outfileneeded = False
    probablechunksize = filesize - 8
    probablesubchunksize = filesize - 44
    if chunksize == probablechunksize:
        print "Current ChunkSize seems to be correct."
    else:
        print "Current ChunkSize %d doesn't match probable size %d." % (chunksize, probablechunksize)
        chunksizedata = struct.pack('<L', probablechunksize)
        outfileneeded = True

    if subchunksize == probablesubchunksize:
        print "Current SubChunkSize seems to be correct."
    else:
        print "Current SubChunkSize %d doesn't match probable size %d." % (subchunksize, probablesubchunksize)
        subchunksizedata = struct.pack('<L', probablesubchunksize)
        outfileneeded = True

    if outfileneeded:
        print "Writing %s..." % fixedwav
        outfile = open(fixedwav, 'wb')
        # copy the first 4 bytes to the output file
        outfile.write(header[:4])
        # write the chunksize data to the output file
        outfile.write(chunksizedata)
        # copy bytes 9-40 to the output file
        outfile.write(header[8:40])
        # write the chunksize data to the output file
        outfile.write(subchunksizedata)
        # read & write the rest of the file
        outfile.write(infile.read())
        outfile.close()

    # tidy up
    infile.close()
    print "Done.\n"
