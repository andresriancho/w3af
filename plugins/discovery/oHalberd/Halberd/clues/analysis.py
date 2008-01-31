# -*- coding: iso-8859-1 -*-

"""Utilities for clue analysis.
"""

# Copyright (C) 2004, 2005, 2006 Juan M. Bello Rivas <jmbr@superadditive.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import copy

import Halberd.logger


logger = Halberd.logger.getLogger()


# TODO - Test fuzzy clustering and k-means against this naive hierarchical
# clustering algorithm to see which one performs better (there's a k-means
# implementation in Scipy).
# Fuzzy clustering will probably be better as it can output a degree of
# confidence which might be helpful to halberd's users.

# XXX - In python 2.4 there's itertools.groupby() which replaces the idiomatic
# dictionary uses for grouping things together.

def diff_fields(clues):
    """Study differences between fields.

    @param clues: Clues to analyze.
    @type clues: C{list}

    @return: Fields which were found to be different among the analyzed clues.
    @rtype: C{list}
    """
    def pairs(num):
        for i in xrange(num):
            for j in xrange(num):
                if i == j:
                    continue
                yield (i, j)

    import difflib

    different = []
    for i, j in pairs(len(clues)):
        one, other = clues[i].headers, clues[j].headers
        matcher = difflib.SequenceMatcher(None, one, other)

        for tag, alo, ahi, blo, bhi in matcher.get_opcodes():
            if tag == 'equal':
                continue
                
            for name, value in one[alo:ahi] + other[blo:bhi]:
                different.append(name)

    different.sort()
    different.reverse()

    return different

def ignore_changing_fields(clues):
    """Tries to detect and ignore MIME fields with ever changing content.

    Some servers might include fields varying with time, randomly, etc. Those
    fields are likely to alter the clue's digest and interfer with L{analyze},
    producing many false positives and making the scan useless. This function
    detects those fields and recalculates each clue's digest so they can be
    safely analyzed again.

    @param clues: Sequence of clues.
    @type clues: C{list} or C{tuple}
    """
    from Halberd.clues.Clue import Clue

    different = diff_fields(clues)

    # First alter Clue to be able to cope with the varying fields.
    ignored = []
    for field in different:
        method = '_get_' + Clue.normalize(field)
        if not hasattr(Clue, method):
            logger.debug('ignoring %s', field)
            ignored.append(method)
            setattr(Clue, method, lambda s, f: None)

    for clue in clues:
        Clue.parse(clue, clue.headers)

    for method in ignored:
        # We want to leave the Clue class as before because a MIME field
        # causing trouble for the current scan might be the source of precious
        # information for another scan.
        delattr(Clue, method)

    return clues


def get_digest(clue):
    """Returns the specified clue's digest.

    This function is usually passed as a parameter for L{classify} so it can
    separate clues according to their digest (among other fields).

    @return: The digest of a clue's parsed headers.
    @rtype: C{str}
    """
    return clue.info['digest']

def clusters(clues, step=3):
    """Finds clusters of clues.

    A cluster is a group of at most C{step} clues which only differ in 1 seconds
    between each other.

    @param clues: A sequence of clues to analyze
    @type clues: C{list} or C{tuple}

    @param step: Maximum difference between the time differences of the
    cluster's clues.
    @type step: C{int}

    @return: A sequence with merged clusters.
    @rtype: C{tuple}
    """
    def iscluster(clues, num):
        """Determines if a list of clues form a cluster of the specified size.
        """
        assert len(clues) == num

        if abs(clues[0].diff - clues[-1].diff) <= num:
            return True
        return False

    def find_cluster(clues, num):
        if len(clues) >= num:
            if iscluster(clues[:num], num):
                return tuple(clues[:num])
        return ()

    clues = sort_clues(clues)

    invrange = lambda num: [(num - x) for x in range(num)]

    start = 0
    while True:
        clues = clues[start:]
        if not clues:
            break

        for i in invrange(step):
            cluster = find_cluster(clues, i)
            if cluster:
                yield cluster
                start = i
                break

def merge(clues):
    """Merges a sequence of clues into one.

    A new clue will store the total count of the clues.
    
    Note that each L{Clue} has a starting count of 1

    >>> a, b, c = Clue(), Clue(), Clue()
    >>> sum([x.getCount() for x in [a, b, c]])
    3
    >>> a.incCount(5), b.incCount(11), c.incCount(23)
    (None, None, None)
    >>> merged = merge((a, b, c))
    >>> merged.getCount()
    42
    >>> merged == a
    True

    @param clues: A sequence containing all the clues to merge into one.
    @type clues: C{list} or C{tuple}

    @return: The result of merging all the passed clues into one.
    @rtype: L{Clue}
    """
    merged = copy.copy(clues[0])
    for clue in clues[1:]:
        merged.incCount(clue.getCount())
    return merged

def classify(seq, *classifiers):
    """Classify a sequence according to one or several criteria.

    We store each item into a nested dictionary using the classifiers as key
    generators (all of them must be callable objects).

    In the following example we classify a list of clues according to their
    digest and their time difference.

    >>> a, b, c = Clue(), Clue(), Clue()
    >>> a.diff, b.diff, c.diff = 1, 2, 2
    >>> a.info['digest'] = 'x'
    >>> b.info['digest'] = c.info['digest'] = 'y'
    >>> get_diff = lambda x: x.diff
    >>> classified = classify([a, b, c], get_digest, get_diff)
    >>> digests = classified.keys()
    >>> digests.sort()  # We sort these so doctest won't fail.
    >>> for digest in digests:
    ...     print digest
    ...     for diff in classified[digest].keys():
    ...         print ' ', diff
    ...         for clue in classified[digest][diff]:
    ...             if clue is a: print '    a'
    ...             elif clue is b: print '    b'
    ...             elif clue is c: print '    c'
    ...
    x
      1
        a
    y
      2
        b
        c

    @param seq: A sequence to classify.
    @type seq: C{list} or C{tuple}

    @param classifiers: A sequence of callables which return specific fields of
    the items contained in L{seq}
    @type classifiers: C{list} or C{tuple}

    @return: A nested dictionary in which the keys are the fields obtained by
    applying the classifiers to the items in the specified sequence.
    @rtype: C{dict}
    """
    # XXX - Printing a dictionary in a doctest string is a very bad idea.
    classified = {}

    for item in seq:
        section = classified
        for classifier in classifiers[:-1]:
            assert callable(classifier)
            section = section.setdefault(classifier(item), {})

        # At the end no more dict nesting is needed. We simply store the items.
        last = classifiers[-1]
        section.setdefault(last(item), []).append(item)

    return classified

def sections(classified, sects=None):
    """Returns sections (and their items) from a nested dict.

    See also: L{classify}

    @param classified: Nested dictionary.
    @type classified: C{dict}

    @param sects: List of results. It should not be specified by the user.
    @type sects: C{list}

    @return: A list of lists in where each item is a subsection of a nested dictionary.
    @rtype: C{list}
    """
    if sects is None:
        sects = []

    if isinstance(classified, dict):
        for key in classified.keys():
            sections(classified[key], sects)
    elif isinstance(classified, list):
        sects.append(classified)

    return sects

def deltas(xs):
    """Computes the differences between the elements of a sequence of integers.

    >>> deltas([-1, 0, 1])
    [1, 1]
    >>> deltas([1, 1, 2, 3, 5, 8, 13])
    [0, 1, 1, 2, 3, 5]

    @param xs: A sequence of integers.
    @type xs: C{list}

    @return: A list of differences between consecutive elements of L{xs}.
    @rtype: C{list}
    """
    if len(xs) < 2:
        return []
    else:
        return [xs[1] - xs[0]] + deltas(xs[1:])

def slices(start, xs):
    """Returns slices of a given sequence separated by the specified indices.

    If we wanted to get the slices necessary to split range(20) in
    sub-sequences of 5 items each we'd do:

    >>> seq = range(20) 
    >>> indices = [5, 10, 15]
    >>> for piece in slices(0, indices):
    ...     print seq[piece]
    [0, 1, 2, 3, 4]
    [5, 6, 7, 8, 9]
    [10, 11, 12, 13, 14]
    [15, 16, 17, 18, 19]

    @param start: Index of the first element of the sequence we want to
    partition.
    @type start: C{int}.

    @param xs: Sequence of indexes where 'cuts' must be made.
    @type xs: C{list}

    @return: A sequence of C{slice} objects suitable for splitting a list as
    specified.
    @rtype: C{list} of C{slice}
    """
    if xs == []:
        # The last slice includes all the remaining items in the sequence.
        return [slice(start, None)]
    return [slice(start, xs[0])] + slices(xs[0], xs[1:])

def sort_clues(clues):
    """Sorts clues according to their time difference.
    """
    # This can be accomplished in newer (>= 2.4) Python versions using:
    #  clues.sort(key=lambda x: x.diff)
    tmps = [(x.diff, x) for x in clues]
    tmps.sort()
    return [x[1] for x in tmps]


def filter_proxies(clues, maxdelta=3):
    """Detect and merge clues pointing to a proxy cache on the remote end.

    @param clues: Sequence of clues to analyze
    @type clues: C{list}

    @param maxdelta: Maximum difference allowed between a clue's time
    difference and the previous one.
    @type maxdelta: C{int}

    @return: Sequence where all irrelevant clues pointing out to proxy caches
    have been filtered out.
    @rtype: C{list}
    """
    results = []

    # Classify clues by remote time and digest.
    get_rtime = lambda c: c._remote
    classified = classify(clues, get_rtime, get_digest)

    subsections = sections(classified)
    for cur_clues in subsections:
        if len(cur_clues) == 1:
            results.append(cur_clues[0])
            continue

        cur_clues = sort_clues(cur_clues)

        diffs = [c.diff for c in cur_clues]

        # We find the indices of those clues which differ from the rest in
        # more than maxdelta seconds.
        indices = [idx for idx, delta in enumerate(deltas(diffs))
                       if abs(delta) > maxdelta]

        for piece in slices(0, indices):
            if cur_clues[piece] == []:
                break
            results.append(merge(cur_clues[piece]))

    return results

def uniq(clues):
    """Return a list of unique clues.

    This is needed when merging clues coming from different sources. Clues with
    the same time diff and digest are not discarded, they are merged into one
    clue with the aggregated number of hits.

    @param clues: A sequence containing the clues to analyze.
    @type clues: C{list}

    @return: Filtered sequence of clues where no clue has the same digest and
    time difference.
    @rtype: C{list}
    """
    results = []

    get_diff = lambda c: c.diff
    classified = classify(clues, get_digest, get_diff)

    for section in sections(classified):
        results.append(merge(section))

    return results

def hits(clues):
    """Compute the total number of hits in a sequence of clues.

    @param clues: Sequence of clues.
    @type clues: C{list}

    @return: Total hits.
    @rtype: C{int}
    """
    return sum([clue.getCount() for clue in clues])

def analyze(clues):
    """Draw conclusions from the clues obtained during the scanning phase.

    @param clues: Unprocessed clues obtained during the scanning stage.
    @type clues: C{list}

    @return: Coherent list of clues identifying real web servers.
    @rtype: C{list}
    """
    results = []

    clues = uniq(clues)

    clues = filter_proxies(clues)

    cluesbydigest = classify(clues, get_digest)

    for key in cluesbydigest.keys():
        for cluster in clusters(cluesbydigest[key]):
            results.append(merge(cluster))

    return results

# TODO - reanalyze should be called from this module and not from Halberd.shell.
def reanalyze(clues, analyzed, threshold):
    """Identify and ignore changing header fields.

    After initial analysis one must check that there aren't as many realservers
    as obtained clues. If there were it could be a sign of something wrong
    happening: each clue is different from the others due to one or more MIME
    header fields which change unexpectedly.

    @param clues: Raw sequence of clues.
    @type clues: C{list}

    @param analyzed: Result from the first analysis phase.
    @type analyzed: C{list}

    @param threshold: Minimum clue-to-realserver ratio in order to trigger
    field inspection.
    @type threshold: C{float}
    """
    def ratio():
        return len(analyzed) / float(len(clues))

    assert len(clues) > 0

    r = ratio()
    if r >= threshold:
        logger.debug('clue-to-realserver ratio is high (%.3f)', r)
        logger.debug('reanalyzing clues...')

        ignore_changing_fields(clues)
        analyzed = analyze(clues)

        logger.debug('clue reanalysis done.')

    # Check again to see if we solved the problem but only warn the user if
    # there's a significant amount of evidence.
    if ratio() >= threshold and len(clues) > 10:
        logger.warn(
'''The following results might be incorrect.  It could be because the remote
host keeps changing its server version string or because halberd didn't have
enough samples.''')

    return analyzed


def _test():
    import doctest

    import Halberd.clues.Clue
    import Halberd.clues.analysis

    # Due to the above imports, this test must be executed from the top level
    # source directory:
    #     python Halberd/clues/analysis.py -v

    globs = Halberd.clues.analysis.__dict__
    globs.update(Halberd.clues.Clue.__dict__)

    return doctest.testmod(m=Halberd.clues.analysis, name='analysis', globs=globs)

if __name__ == '__main__':
    _test()


# vim: ts=4 sw=4 et
