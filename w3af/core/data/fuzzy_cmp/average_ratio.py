"""
average_ratio.py

Copyright 2015 Andres Riancho

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
from w3af.core.data.fuzzy_cmp.fuzzy_string_cmp import relative_distance


MIN_INPUT_REQUIREMENT = 5
MIN_SIMILARITY = 0.85


def average_ratio(inputs):
    """
    This function will return the average similarity ratio between all the
    input strings

    The function is useful for cases where you have a set of known bad results
    and then you want to know if a new string is similar to the known bad or
    not. It was initially written for comparing login test results for #799 but
    it can be used for anything.

    For example, you can send 10 known bad / failed login attempts to a site,
    call average_ratio with the response bodies and get a similarity ratio of
    0.95. After that you send your real login tests and compare them with
    relative_distance and 0.95 (or maybe 0.95 - 0.1 or some other delta).

    The improvement with other strategies is that before we just used a fixed
    value instead of the 0.95 (from the example above) which triggered some
    false negatives in the login brute force process.
    
    The function implements these safeguards:
    
        * At least MIN_INPUT_REQUIREMENT input strings need to be sent as args
        
        * If one of the inputs is very different then we raise an exception.
          This is a protection against sites which change a lot, where we won't
          be able to effectively compare responses.
          
        * If the similarity average between all inputs is low (less than
          MIN_SIMILARITY) then we raise an exception. This is to protect against
          sets of pages which are similar but not enough to compare.

    :param inputs: A list containing at least MIN_INPUT_REQUIREMENT strings
    :return: The average similarity ratio between all input strings
    :see: https://github.com/andresriancho/w3af/issues/799
    """
    if len(inputs) < MIN_INPUT_REQUIREMENT:
        msg = 'Need at least %s inputs to calculate an average.'
        raise ValueError(msg % MIN_INPUT_REQUIREMENT)

    ratios = []

    for i, input_a in enumerate(inputs):
        for j, input_b in enumerate(inputs):
            if i == j:
                continue

            ratio = relative_distance(input_a, input_b)
            if ratio < MIN_SIMILARITY:
                msg = 'Inputs are very different (%s) and can not be averaged'
                raise ValueError(msg % ratio)

            ratios.append(ratio)

    return sum(ratios) / len(ratios)