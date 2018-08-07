"""
fuzzy_string_cmp.py

Copyright 2008 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import difflib

from w3af.core.controllers.misc.diff import split_by_sep


def fuzzy_equal(a_str, b_str, threshold=0.6):
    """
    Indicates if the strings to compare are similar enough. This (optimized)
    function is equivalent to the expression:

        relative_distance(x, y) > threshold

    :param a_str: A string instance
    :param b_str: A string instance
    :param threshold: Float value indicating the expected "similarity". Must be
                      0 <= threshold <= 1.0
    :return: A boolean value
    """
    optimization_result = _get_optimized_fuzzy_equal(a_str, b_str, threshold=threshold)

    if optimization_result is not None:
        return optimization_result

    # Bad, we can't optimize anything better, just calculate the relative distance
    distance = relative_distance(a_str, b_str)
    return distance > threshold


def fuzzy_equal_return_distance(a_str, b_str, threshold=0.6):
    """
    Similar to fuzzy_equal() but returns the distance between the strings

    :param a_str: A string instance
    :param b_str: A string instance
    :param threshold: Float value indicating the expected "similarity". Must be
                      0 <= threshold <= 1.0
    :return: A tuple containing:
                - A boolean indicating the fuzzy_equal result
                - The distance between the two strings, if it was calculated
    """
    optimization_result = _get_optimized_fuzzy_equal(a_str, b_str, threshold=threshold)

    if optimization_result is not None:
        return optimization_result, None

    # Bad, we can't optimize anything better, just calculate the relative distance
    distance = relative_distance(a_str, b_str)
    return distance > threshold, distance


def _get_optimized_fuzzy_equal(a_str, b_str, threshold=0.6):
    """
    Indicates if the strings to compare are similar enough. This (optimized)
    function is equivalent to the expression:

        relative_distance(x, y) > threshold

    The function shouldn't get called directly, only use it via fuzzy_equal.

    :param a_str: A string object
    :param b_str: A string object
    :param threshold: Float value indicating the expected "similarity". Must be
                      0 <= threshold <= 1.0
    :return: True means that both strings are fuzzy equal
             False means that both strings are NOT fuzzy equal
             None means the algorithm is unable to know
    """
    if threshold == 0:
        return True

    if threshold == 1.0:
        return a_str == b_str

    a_len = len(a_str)
    b_len = len(b_str)

    if b_len == 0 or a_len == 0:
        return a_len == b_len

    if b_len == a_len and a_str == b_str:
        return True

    if threshold > upper_bound_similarity(a_len, b_len):
        return False

    return None


def upper_bound_similarity(a_len, b_len):
    # First we need b_len to be the larger of both
    if b_len < a_len:
        a_len, b_len = b_len, a_len

    return (2.0 * a_len) / (a_len + b_len)


def fuzzy_not_equal(a_str, b_str, threshold=0.6):
    """
    Indicates if the 'similarity' index between strings
    is *less than* 'threshold'
    """
    return not fuzzy_equal(a_str, b_str, threshold)


def relative_distance(a_str, b_str):
    """
    Measures the "similarity" of two strings.

    Depends on the algorithm we finally implement, but usually a return value
    over 0.7 means the strings are very similar.

    :param a_str: A string object
    :param b_str: A string object
    :return: A float with the distance
    """
    return difflib.SequenceMatcher(None,
                                   split_by_sep(a_str),
                                   split_by_sep(b_str)).quick_ratio()

