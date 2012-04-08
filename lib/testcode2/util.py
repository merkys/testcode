'''Utility functions.'''

import os.path
import re
import sys

import testcode2.compatibility as compat
import testcode2.exceptions as exceptions

def testcode_filename(stem, file_id, inp, args):
    '''Construct filename in testcode format.'''
    filename = '%s.%s' % (stem, file_id)
    if inp:
        filename = '%s.inp=%s' % (filename, inp)
    if args:
        args_string = args.replace(' ','_')
        filename = '%s.args=%s' % (filename, args_string)
    return filename

def testcode_file_id(filename, stem):
    '''Extract the file_id from a filename in the testcode format.'''
    filename = filename.replace('%s.' % (stem), '')
    filename = re.sub('\.inp=.*', '', filename)
    filename = re.sub('\.args=.*', '', filename)
    return filename


def try_floatify(val):
    '''Convert val to a float if possible.'''
    try:
        return float(val)
    except ValueError:
        return val

def extract_tagged_data(data_tag, filename):
    '''Extract data from lines marked by the data_tag in filename.'''
    if not os.path.exists(filename):
        err = 'Cannot extract data: file %s does not exist.' % (filename)
        raise exceptions.RunError(err)
    data_file = open(filename)
    # Data tag is the first non-space character in the line.
    # e.g. extract data from lines:
    # data_tag      Energy:    1.256743 a.u.
    data_tag_regex = re.compile('^ *%s' % (re.escape(data_tag)))
    data = {}
    for line in data_file.readlines():
        if data_tag_regex.match(line):
            # This is a line containing info to be tested.
            words = line.split()
            key = []
            # name of data is string after the data_tag and preceeding the
            # (numerical) data.  only use the first number in the line, with
            # the key taken from all proceeding information.
            for word in words[1:]:
                val = try_floatify(word)
                if val != word:
                    break
                else:
                    key.append(word)
            if key[-1] in ("=",':'):
                key.pop()
            key = '_'.join(key)
            if key[-1] in ("=",':'):
                key = key[:-1]
            if not key:
                key = 'data'
            if key in data:
                data[key].append(val)
            else:
                data[key] = [val]
    # We shouldn't change the data from this point: convert entries to tuples.
    for (key, val) in data.items():
        data[key] = tuple(val)
    return data

def dict_table_string(table_string):
    '''Read a data table from a string into a dictionary.

The first row and any subsequent rows containing no numbers are assumed to form
headers of a subtable, and so form the keys for the subsequent subtable.

Values, where possible, are converted to floats.

e.g. a  b  c  a  ->   {'a':(1,4,7,8), 'b':(2,5), 'c':(3,6)}
     1  2  3  7
     4  5  6  8
and
     a  b  c   ->   {'a':(1,4,7), 'b':(2,5,8), 'c':(3,6), 'd':(9), 'e':(6)}
     1  2  3
     4  5  6
     a  b  d  e
     7  8  9  6
'''
    data = [i.split() for i in table_string.splitlines()]
    # Convert to numbers where appropriate
    data = [[try_floatify(val) for val in dline] for dline in data]
    data_dict = {}
    for dline in data:
        # Test if all items are strings; if so start a new subtable.
        # We actually test if all items are not floats, as python 3 can return
        # a bytes variable from subprocess whereas (e.g.) python 2.4 returns a
        # str.  Testing for this is problematic as the bytes type does not
        # exist in python 2.4.  Fortunately we have converted all items to
        # floats if possible, so can just test for the inverse condition...
        if compat.compat_all(type(val) is not float for val in dline):
            # header of new subtable
            head = dline
            for val in head:
                if val not in data_dict:
                    data_dict[val] = []
        else:
            for (ind, val) in enumerate(dline):
                # Add data to appropriate key.
                # Note that this handles the case where the same column heading
                # occurs multiple times in the same subtable and does not
                # overwrite the previous column with the same heading.
                data_dict[head[ind]].append(val)
    # We shouldn't change the data from this point: convert entries to tuples.
    for (key, val) in data_dict.items():
        data_dict[key] = tuple(val)
    return data_dict

def pretty_print_table(labels, dicts):
    '''Print data in dictionaries of identical size in a tabular format.'''
    # Loop through all elements in order to calculate the field width.
    label_width = max(len(str(label)) for label in labels)
    field_width = {}
    fmt = dict(label='%%-%is' % (label_width))
    header = [fmt['label'] % ('')]
    for key in sorted(dicts[0].keys()):
        field_width[key] = len(str(key))
        nitems = 1
        if type(dicts[0][key]) is tuple or type(dicts[0][key]) is list:
            nitems = len(dicts[0][key])
            for dval in dicts:
                for item in dval[key]:
                    field_width[key] = max(field_width[key], len(str(item)))
        else:
            field_width[key] = max(len(str(dval[key])) for dval in dicts)
            field_width[key] = max(field_width[key], len(str(key)))
        fmt[key] = '%%-%is' % (field_width[key])
        for item in range(nitems):
            header.append(fmt[key] % (key))
    # printing without a new line is different in python 2 and python 3, so for
    # ease we construct the formatting for the line and then print it.
    lines = [ header ]
    for (ind, label) in enumerate(labels):
        line = [fmt['label'] % (label)]
        dval = dicts[ind]
        for key in sorted(dval.keys()):
            if type(dval[key]) is tuple or type(dval[key]) is list:
                for item in range(len(dval[key])):
                    line.append(fmt[key] % (dval[key][item]))
            else:
                line.append(fmt[key] % (dval[key]))
        lines.extend([line])
    # Now actually form table.
    lines = ['  '.join(line) for line in lines]
    table = '\n'.join(lines)
    return table

def print_success(passed, msg, verbose):
    '''Print output from comparing test job to benchmark.'''
    if verbose:
        if passed:
            print('Passed.')
        else:
            print('**FAILED**.')
        if msg:
            print(msg)
    else:
        if passed:
            sys.stdout.write('.')
        else:
            sys.stdout.write('F')
        sys.stdout.flush()
