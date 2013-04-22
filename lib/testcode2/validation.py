'''
testcode2.validation
--------------------

Classes and functions for comparing data.

:copyright: (c) 2012 James Spencer.
:license: modified BSD; see LICENSE for more details.
'''

import testcode2.compatibility as compat
import sys

class Status:
    '''Enum-esque object for storing whether an object passed a comparison.

bools: iterable of boolean objects.  If all booleans are True (False) then the
       status is set to pass (fail) and if only some booleans are True, the
       status is set to warning (partial pass).
status: existing status to use.  bools is ignored if status is supplied.'''
    def __init__(self, bools=None, status=None):
        (self._pass, self._partial, self._fail) = (0, 1, 2)
        if status is not None:
            self.status = status
        else:
            if compat.compat_all(bools):
                self.status = self._pass
            elif compat.compat_any(bools):
                self.status = self._partial
            else:
                self.status = self._fail
    def passed(self):
        '''Return true if stored status is passed.'''
        return self.status == self._pass
    def warning(self):
        '''Return true if stored status is a partial pass.'''
        return self.status == self._partial
    def failed(self):
        '''Return true if stored status is failed.'''
        return self.status == self._fail
    def print_status(self, msg=None, verbose=True, vspace=True):
        '''Print status.

msg: optional message to print out after status.
verbose: suppress all output except for . (for pass), W (for warning/partial
         pass) and F (for fail).
vspace: print out extra new line afterwards.
'''
        if verbose:
            if self.status == self._pass:
                print('Passed.')
            elif self.status == self._partial:
                print('WARNING.')
            else:
                print('**FAILED**.')
            if msg:
                print(msg)
            if vspace:
                print('')
        else:
            if self.status == self._pass:
                sys.stdout.write('.')
            elif self.status == self._partial:
                sys.stdout.write('W')
            else:
                sys.stdout.write('F')
            sys.stdout.flush()
    def __add__(self, other):
        '''Add two status objects.

Return the maximum level (ie most "failed") status.'''
        return Status(status=max(self.status, other.status))

class Tolerance:
    '''Store absolute and relative tolerances

Given floats are regarded as equal if they are within these tolerances.'''
    def __init__(self, absolute=None, relative=None):
        self.absolute = absolute
        self.relative = relative
    def validate(self, test_val, benchmark_val, key=''):
        '''Compare test and benchmark values to within the tolerances.'''
        status = Status([True])
        msg = 'values are within tolerance.'
        try:
            # Check float is not NaN (which we can't compare).
            if compat.isnan(test_val) or compat.isnan(benchmark_val):
                status = Status([False])
                msg = 'cannot compare NaNs.'
            else:
                # Check if values are within tolerances.
                diff = test_val - benchmark_val
                if self.absolute:
                    err = abs(diff)
                    abs_passed = err < self.absolute
                    if not abs_passed:
                        msg = ('absolute error %.2e greater than %.2e.' %
                                (err, self.absolute))
                    status += Status([abs_passed])
                if self.relative:
                    if benchmark_val == 0 and diff == 0:
                        err = 0
                    elif benchmark_val == 0:
                        err = float("Inf")
                    else:
                        err = abs(diff/benchmark_val)
                    rel_passed = err < self.relative
                    if not rel_passed:
                        msg = ('relative error %.2e greater than %.2e.' %
                                (err, self.relative))
                    status += Status([rel_passed])
        except TypeError:
            if test_val != benchmark_val:
                # require test and benchmark values to be equal (within python's
                # definition of equality).
                status = Status([False])
                msg = 'values are different.'
        if key:
            msg = '%s: %s' % (key, msg)
        return (status, msg)

def compare_data(benchmark, test, default_tolerance, tolerances,
        ignore_fields=None):
    '''Compare two data dictionaries.'''
    if ignore_fields:
        for field in ignore_fields:
            benchmark.pop([field])
            test.pop([field])
    nitems = lambda data_dict: [len(val) for (key, val)
                                                in sorted(data_dict.items())]
    if sorted(benchmark.keys()) != sorted(test.keys()) or \
            nitems(benchmark) != nitems(test):
        comparable = False
        status = Status([False])
        msg = 'Different sets of data extracted from benchmark and test.'
    else:
        comparable = True
        status = Status([True])
        msg = []
        # Test keys are same.
        # Compare each field (unless we're ignoring it).
        for key in benchmark.keys():
            if key in tolerances.keys():
                tol = tolerances[key]
            else:
                tol = default_tolerance
            for ind in range(len(benchmark[key])):
                (key_status, err) = tol.validate(
                        test[key][ind], benchmark[key][ind], key)
                status += key_status
                if not key_status.passed() and err:
                    msg.append(err)
        msg = '\n'.join(msg)
    return (comparable, status, msg)
