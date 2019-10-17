######################## BEGIN LICENSE BLOCK ########################
# The Original Code is Mozilla Communicator client code.
#
# The Initial Developer of the Original Code is
# Netscape Communications Corporation.
# Portions created by the Initial Developer are Copyright (C) 1998
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#   Mark Pilgrim - port to Python
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
# 02110-1301  USA
######################### END LICENSE BLOCK #########################

from .compat import wrap_ord

NUM_OF_CATEGORY = 6
DONT_KNOW = -1
ENOUGH_REL_THRESHOLD = 100
MAX_REL_THRESHOLD = 1000
MINIMUM_DATA_THRESHOLD = 4

# This is hiragana 2-char sequence table, the number in each cell
# represents its frequency category
jp2CharContext = (
    (0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1),
    (2, 4, 0, 4, 0, 3, 0, 4, 0, 3, 4, 4, 4, 2, 4, 3, 3, 4, 3, 2, 3, 3, 4, 2, 3, 3, 3, 2, 4, 1, 4, 3, 3, 1, 5, 4, 3, 4, 3, 4, 3, 5, 3, 0, 3, 5, 4, 2, 0, 3, 1, 0, 3, 3, 0, 3, 3, 0, 1, 1, 0, 4, 3, 0, 3, 3, 0, 4, 0, 2, 0, 3, 5, 5, 5, 5, 4, 0, 4, 1, 0, 3, 4),
    (0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2),
    (0, 4, 0, 5, 0, 5, 0, 4, 0, 4, 5, 4, 4, 3, 5, 3, 5, 1, 5, 3, 4, 3, 4, 4, 3, 4, 3, 3, 4, 3, 5, 4, 4, 3, 5, 5, 3, 5, 5, 5, 3, 5, 5, 3, 4, 5, 5, 3, 1, 3, 2, 0, 3, 4, 0, 4, 2, 0, 4, 2, 1, 5, 3, 2, 3, 5, 0, 4, 0, 2, 0, 5, 4, 4, 5, 4, 5, 0, 4, 0, 0, 4, 4),
    (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 3, 0, 4, 0, 3, 0, 3, 0, 4, 5, 4, 3, 3, 3, 3, 4, 3, 5, 4, 4, 3, 5, 4, 4, 3, 4, 3, 4, 4, 4, 4, 5, 3, 4, 4, 3, 4, 5, 5, 4, 5, 5, 1, 4, 5, 4, 3, 0, 3, 3, 1, 3, 3, 0, 4, 4, 0, 3, 3, 1, 5, 3, 3, 3, 5, 0, 4, 0, 3, 0, 4, 4, 3, 4, 3, 3, 0, 4, 1, 1, 3, 4),
    (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 4, 0, 3, 0, 3, 0, 4, 0, 3, 4, 4, 3, 2, 2, 1, 2, 1, 3, 1, 3, 3, 3, 3, 3, 4, 3, 1, 3, 3, 5, 3, 3, 0, 4, 3, 0, 5, 4, 3, 3, 5, 4, 4, 3, 4, 4, 5, 0, 1, 2, 0, 1, 2, 0, 2, 2, 0, 1, 0, 0, 5, 2, 2, 1, 4, 0, 3, 0, 1, 0, 4, 4, 3, 5, 4, 3, 0, 2, 1, 0, 4, 3),
    (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 3, 0, 5, 0, 4, 0, 2, 1, 4, 4, 2, 4, 1, 4, 2, 4, 2, 4, 3, 3, 3, 4, 3, 3, 3, 3, 1, 4, 2, 3, 3, 3, 1, 4, 4, 1, 1, 1, 4, 3, 3, 2, 0, 2, 4, 3, 2, 0, 3, 3, 0, 3, 1, 1, 0, 0, 0, 3, 3, 0, 4, 2, 2, 3, 4, 0, 4, 0, 3, 0, 4, 4, 5, 3, 4, 4, 0, 3, 0, 0, 1, 4),
    (1, 4, 0, 4, 0, 4, 0, 4, 0, 3, 5, 4, 4, 3, 4, 3, 5, 4, 3, 3, 4, 3, 5, 4, 4, 4, 4, 3, 4, 2, 4, 3, 3, 1, 5, 4, 3, 2, 4, 5, 4, 5, 5, 4, 4, 5, 4, 4, 0, 3, 2, 2, 3, 3, 0, 4, 3, 1, 3, 2, 1, 4, 3, 3, 4, 5, 0, 3, 0, 2, 0, 4, 5, 5, 4, 5, 4, 0, 4, 0, 0, 5, 4),
    (0, 5, 0, 5, 0, 4, 0, 3, 0, 4, 4, 3, 4, 3, 3, 3, 4, 0, 4, 4, 4, 3, 4, 3, 4, 3, 3, 1, 4, 2, 4, 3, 4, 0, 5, 4, 1, 4, 5, 4, 4, 5, 3, 2, 4, 3, 4, 3, 2, 4, 1, 3, 3, 3, 2, 3, 2, 0, 4, 3, 3, 4, 3, 3, 3, 4, 0, 4, 0, 3, 0, 4, 5, 4, 4, 4, 3, 0, 4, 1, 0, 1, 3),
    (0, 3, 1, 4, 0, 3, 0, 2, 0, 3, 4, 4, 3, 1, 4, 2, 3, 3, 4, 3, 4, 3, 4, 3, 4, 4, 3, 2, 3, 1, 5, 4, 4, 1, 4, 4, 3, 5, 4, 4, 3, 5, 5, 4, 3, 4, 4, 3, 1, 2, 3, 1, 2, 2, 0, 3, 2, 0, 3, 1, 0, 5, 3, 3, 3, 4, 3, 3, 3, 3, 4, 4, 4, 4, 5, 4, 2, 0, 3, 3, 2, 4, 3),
    (0, 2, 0, 3, 0, 1, 0, 1, 0, 0, 3, 2, 0, 0, 2, 0, 1, 0, 2, 1, 3, 3, 3, 1, 2, 3, 1, 0, 1, 0, 4, 2, 1, 1, 3, 3, 0, 4, 3, 3, 1, 4, 3, 3, 0, 3, 3, 2, 0, 0, 0, 0, 1, 0, 0, 2, 0, 0, 0, 0, 0, 4, 1, 0, 2, 3, 2, 2, 2, 1, 3, 3, 3, 4, 4, 3, 2, 0, 3, 1, 0, 3, 3),
    (0, 4, 0, 4, 0, 3, 0, 3, 0, 4, 4, 4, 3, 3, 3, 3, 3, 3, 4, 3, 4, 2, 4, 3, 4, 3, 3, 2, 4, 3, 4, 5, 4, 1, 4, 5, 3, 5, 4, 5, 3, 5, 4, 0, 3, 5, 5, 3, 1, 3, 3, 2, 2, 3, 0, 3, 4, 1, 3, 3, 2, 4, 3, 3, 3, 4, 0, 4, 0, 3, 0, 4, 5, 4, 4, 5, 3, 0, 4, 1, 0, 3, 4),
    (0, 2, 0, 3, 0, 3, 0, 0, 0, 2, 2, 2, 1, 0, 1, 0, 0, 0, 3, 0, 3, 0, 3, 0, 1, 3, 1, 0, 3, 1, 3, 3, 3, 1, 3, 3, 3, 0, 1, 3, 1, 3, 4, 0, 0, 3, 1, 1, 0, 3, 2, 0, 0, 0, 0, 1, 3, 0, 1, 0, 0, 3, 3, 2, 0, 3, 0, 0, 0, 0, 0, 3, 4, 3, 4, 3, 3, 0, 3, 0, 0, 2, 3),
    (2, 3, 0, 3, 0, 2, 0, 1, 0, 3, 3, 4, 3, 1, 3, 1, 1, 1, 3, 1, 4, 3, 4, 3, 3, 3, 0, 0, 3, 1, 5, 4, 3, 1, 4, 3, 2, 5, 5, 4, 4, 4, 4, 3, 3, 4, 4, 4, 0, 2, 1, 1, 3, 2, 0, 1, 2, 0, 0, 1, 0, 4, 1, 3, 3, 3, 0, 3, 0, 1, 0, 4, 4, 4, 5, 5, 3, 0, 2, 0, 0, 4, 4),
    (0, 2, 0, 1, 0, 3, 1, 3, 0, 2, 3, 3, 3, 0, 3, 1, 0, 0, 3, 0, 3, 2, 3, 1, 3, 2, 1, 1, 0, 0, 4, 2, 1, 0, 2, 3, 1, 4, 3, 2, 0, 4, 4, 3, 1, 3, 1, 3, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 4, 1, 1, 1, 2, 0, 3, 0, 0, 0, 3, 4, 2, 4, 3, 2, 0, 1, 0, 0, 3, 3),
    (0, 1, 0, 4, 0, 5, 0, 4, 0, 2, 4, 4, 2, 3, 3, 2, 3, 3, 5, 3, 3, 3, 4, 3, 4, 2, 3, 0, 4, 3, 3, 3, 4, 1, 4, 3, 2, 1, 5, 5, 3, 4, 5, 1, 3, 5, 4, 2, 0, 3, 3, 0, 1, 3, 0, 4, 2, 0, 1, 3, 1, 4, 3, 3, 3, 3, 0, 3, 0, 1, 0, 3, 4, 4, 4, 5, 5, 0, 3, 0, 1, 4, 5),
    (0, 2, 0, 3, 0, 3, 0, 0, 0, 2, 3, 1, 3, 0, 4, 0, 1, 1, 3, 0, 3, 4, 3, 2, 3, 1, 0, 3, 3, 2, 3, 1, 3, 0, 2, 3, 0, 2, 1, 4, 1, 2, 2, 0, 0, 3, 3, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0, 2, 2, 0, 3, 2, 1, 3, 3, 0, 2, 0, 2, 0, 0, 3, 3, 1, 2, 4, 0, 3, 0, 2, 2, 3),
    (2, 4, 0, 5, 0, 4, 0, 4, 0, 2, 4, 4, 4, 3, 4, 3, 3, 3, 1, 2, 4, 3, 4, 3, 4, 4, 5, 0, 3, 3, 3, 3, 2, 0, 4, 3, 1, 4, 3, 4, 1, 4, 4, 3, 3, 4, 4, 3, 1, 2, 3, 0, 4, 2, 0, 4, 1, 0, 3, 3, 0, 4, 3, 3, 3, 4, 0, 4, 0, 2, 0, 3, 5, 3, 4, 5, 2, 0, 3, 0, 0, 4, 5),
    (0, 3, 0, 4, 0, 1, 0, 1, 0, 1, 3, 2, 2, 1, 3, 0, 3, 0, 2, 0, 2, 0, 3, 0, 2, 0, 0, 0, 1, 0, 1, 1, 0, 0, 3, 1, 0, 0, 0, 4, 0, 3, 1, 0, 2, 1, 3, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 4, 2, 2, 3, 1, 0, 3, 0, 0, 0, 1, 4, 4, 4, 3, 0, 0, 4, 0, 0, 1, 4),
    (1, 4, 1, 5, 0, 3, 0, 3, 0, 4, 5, 4, 4, 3, 5, 3, 3, 4, 4, 3, 4, 1, 3, 3, 3, 3, 2, 1, 4, 1, 5, 4, 3, 1, 4, 4, 3, 5, 4, 4, 3, 5, 4, 3, 3, 4, 4, 4, 0, 3, 3, 1, 2, 3, 0, 3, 1, 0, 3, 3, 0, 5, 4, 4, 4, 4, 4, 4, 3, 3, 5, 4, 4, 3, 3, 5, 4, 0, 3, 2, 0, 4, 4),
    (0, 2, 0, 3, 0, 1, 0, 0, 0, 1, 3, 3, 3, 2, 4, 1, 3, 0, 3, 1, 3, 0, 2, 2, 1, 1, 0, 0, 2, 0, 4, 3, 1, 0, 4, 3, 0, 4, 4, 4, 1, 4, 3, 1, 1, 3, 3, 1, 0, 2, 0, 0, 1, 3, 0, 0, 0, 0, 2, 0, 0, 4, 3, 2, 4, 3, 5, 4, 3, 3, 3, 4, 3, 3, 4, 3, 3, 0, 2, 1, 0, 3, 3),
    (0, 2, 0, 4, 0, 3, 0, 2, 0, 2, 5, 5, 3, 4, 4, 4, 4, 1, 4, 3, 3, 0, 4, 3, 4, 3, 1, 3, 3, 2, 4, 3, 0, 3, 4, 3, 0, 3, 4, 4, 2, 4, 4, 0, 4, 5, 3, 3, 2, 2, 1, 1, 1, 2, 0, 1, 5, 0, 3, 3, 2, 4, 3, 3, 3, 4, 0, 3, 0, 2, 0, 4, 4, 3, 5, 5, 0, 0, 3, 0, 2, 3, 3),
    (0, 3, 0, 4, 0, 3, 0, 1, 0, 3, 4, 3, 3, 1, 3, 3, 3, 0, 3, 1, 3, 0, 4, 3, 3, 1, 1, 0, 3, 0, 3, 3, 0, 0, 4, 4, 0, 1, 5, 4, 3, 3, 5, 0, 3, 3, 4, 3, 0, 2, 0, 1, 1, 1, 0, 1, 3, 0, 1, 2, 1, 3, 3, 2, 3, 3, 0, 3, 0, 1, 0, 1, 3, 3, 4, 4, 1, 0, 1, 2, 2, 1, 3),
    (0, 1, 0, 4, 0, 4, 0, 3, 0, 1, 3, 3, 3, 2, 3, 1, 1, 0, 3, 0, 3, 3, 4, 3, 2, 4, 2, 0, 1, 0, 4, 3, 2, 0, 4, 3, 0, 5, 3, 3, 2, 4, 4, 4, 3, 3, 3, 4, 0, 1, 3, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 4, 2, 3, 3, 3, 0, 3, 0, 0, 0, 4, 4, 4, 5, 3, 2, 0, 3, 3, 0, 3, 5),
    (0, 2, 0, 3, 0, 0, 0, 3, 0, 1, 3, 0, 2, 0, 0, 0, 1, 0, 3, 1, 1, 3, 3, 0, 0, 3, 0, 0, 3, 0, 2, 3, 1, 0, 3, 1, 0, 3, 3, 2, 0, 4, 2, 2, 0, 2, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, 2, 0, 1, 0, 1, 0, 0, 0, 1, 3, 1, 2, 0, 0, 0, 1, 0, 0, 1, 4),
    (0, 3, 0, 3, 0, 5, 0, 1, 0, 2, 4, 3, 1, 3, 3, 2, 1, 1, 5, 2, 1, 0, 5, 1, 2, 0, 0, 0, 3, 3, 2, 2, 3, 2, 4, 3, 0, 0, 3, 3, 1, 3, 3, 0, 2, 5, 3, 4, 0, 3, 3, 0, 1, 2, 0, 2, 2, 0, 3, 2, 0, 2, 2, 3, 3, 3, 0, 2, 0, 1, 0, 3, 4, 4, 2, 5, 4, 0, 3, 0, 0, 3, 5),
    (0, 3, 0, 3, 0, 3, 0, 1, 0, 3, 3, 3, 3, 0, 3, 0, 2, 0, 2, 1, 1, 0, 2, 0, 1, 0, 0, 0, 2, 1, 0, 0, 1, 0, 3, 2, 0, 0, 3, 3, 1, 2, 3, 1, 0, 3, 3, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 2, 3, 1, 2, 3, 0, 3, 0, 1, 0, 3, 2, 1, 0, 4, 3, 0, 1, 1, 0, 3, 3),
    (0, 4, 0, 5, 0, 3, 0, 3, 0, 4, 5, 5, 4, 3, 5, 3, 4, 3, 5, 3, 3, 2, 5, 3, 4, 4, 4, 3, 4, 3, 4, 5, 5, 3, 4, 4, 3, 4, 4, 5, 4, 4, 4, 3, 4, 5, 5, 4, 2, 3, 4, 2, 3, 4, 0, 3, 3, 1, 4, 3, 2, 4, 3, 3, 5, 5, 0, 3, 0, 3, 0, 5, 5, 5, 5, 4, 4, 0, 4, 0, 1, 4, 4),
    (0, 4, 0, 4, 0, 3, 0, 3, 0, 3, 5, 4, 4, 2, 3, 2, 5, 1, 3, 2, 5, 1, 4, 2, 3, 2, 3, 3, 4, 3, 3, 3, 3, 2, 5, 4, 1, 3, 3, 5, 3, 4, 4, 0, 4, 4, 3, 1, 1, 3, 1, 0, 2, 3, 0, 2, 3, 0, 3, 0, 0, 4, 3, 1, 3, 4, 0, 3, 0, 2, 0, 4, 4, 4, 3, 4, 5, 0, 4, 0, 0, 3, 4),
    (0, 3, 0, 3, 0, 3, 1, 2, 0, 3, 4, 4, 3, 3, 3, 0, 2, 2, 4, 3, 3, 1, 3, 3, 3, 1, 1, 0, 3, 1, 4, 3, 2, 3, 4, 4, 2, 4, 4, 4, 3, 4, 4, 3, 2, 4, 4, 3, 1, 3, 3, 1, 3, 3, 0, 4, 1, 0, 2, 2, 1, 4, 3, 2, 3, 3, 5, 4, 3, 3, 5, 4, 4, 3, 3, 0, 4, 0, 3, 2, 2, 4, 4),
    (0, 2, 0, 1, 0, 0, 0, 0, 0, 1, 2, 1, 3, 0, 0, 0, 0, 0, 2, 0, 1, 2, 1, 0, 0, 1, 0, 0, 0, 0, 3, 0, 0, 1, 0, 1, 1, 3, 1, 0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 0, 3, 4, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1),
    (0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 4, 0, 4, 1, 4, 0, 3, 0, 4, 0, 3, 0, 4, 0, 3, 0, 3, 0, 4, 1, 5, 1, 4, 0, 0, 3, 0, 5, 0, 5, 2, 0, 1, 0, 0, 0, 2, 1, 4, 0, 1, 3, 0, 0, 3, 0, 0, 3, 1, 1, 4, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0),
    (1, 4, 0, 5, 0, 3, 0, 2, 0, 3, 5, 4, 4, 3, 4, 3, 5, 3, 4, 3, 3, 0, 4, 3, 3, 3, 3, 3, 3, 2, 4, 4, 3, 1, 3, 4, 4, 5, 4, 4, 3, 4, 4, 1, 3, 5, 4, 3, 3, 3, 1, 2, 2, 3, 3, 1, 3, 1, 3, 3, 3, 5, 3, 3, 4, 5, 0, 3, 0, 3, 0, 3, 4, 3, 4, 4, 3, 0, 3, 0, 2, 4, 3),
    (0, 1, 0, 4, 0, 0, 0, 0, 0, 1, 4, 0, 4, 1, 4, 2, 4, 0, 3, 0, 1, 0, 1, 0, 0, 0, 0, 0, 2, 0, 3, 1, 1, 1, 0, 3, 0, 0, 0, 1, 2, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 3, 0, 0, 0, 0, 3, 2, 0, 2, 2, 0, 1, 0, 0, 0, 2, 3, 2, 3, 3, 0, 0, 0, 0, 2, 1, 0),
    (0, 5, 1, 5, 0, 3, 0, 3, 0, 5, 4, 4, 5, 1, 5, 3, 3, 0, 4, 3, 4, 3, 5, 3, 4, 3, 3, 2, 4, 3, 4, 3, 3, 0, 3, 3, 1, 4, 4, 3, 4, 4, 4, 3, 4, 5, 5, 3, 2, 3, 1, 1, 3, 3, 1, 3, 1, 1, 3, 3, 2, 4, 5, 3, 3, 5, 0, 4, 0, 3, 0, 4, 4, 3, 5, 3, 3, 0, 3, 4, 0, 4, 3),
    (0, 5, 0, 5, 0, 3, 0, 2, 0, 4, 4, 3, 5, 2, 4, 3, 3, 3, 4, 4, 4, 3, 5, 3, 5, 3, 3, 1, 4, 0, 4, 3, 3, 0, 3, 3, 0, 4, 4, 4, 4, 5, 4, 3, 3, 5, 5, 3, 2, 3, 1, 2, 3, 2, 0, 1, 0, 0, 3, 2, 2, 4, 4, 3, 1, 5, 0, 4, 0, 3, 0, 4, 3, 1, 3, 2, 1, 0, 3, 3, 0, 3, 3),
    (0, 4, 0, 5, 0, 5, 0, 4, 0, 4, 5, 5, 5, 3, 4, 3, 3, 2, 5, 4, 4, 3, 5, 3, 5, 3, 4, 0, 4, 3, 4, 4, 3, 2, 4, 4, 3, 4, 5, 4, 4, 5, 5, 0, 3, 5, 5, 4, 1, 3, 3, 2, 3, 3, 1, 3, 1, 0, 4, 3, 1, 4, 4, 3, 4, 5, 0, 4, 0, 2, 0, 4, 3, 4, 4, 3, 3, 0, 4, 0, 0, 5, 5),
    (0, 4, 0, 4, 0, 5, 0, 1, 1, 3, 3, 4, 4, 3, 4, 1, 3, 0, 5, 1, 3, 0, 3, 1, 3, 1, 1, 0, 3, 0, 3, 3, 4, 0, 4, 3, 0, 4, 4, 4, 3, 4, 4, 0, 3, 5, 4, 1, 0, 3, 0, 0, 2, 3, 0, 3, 1, 0, 3, 1, 0, 3, 2, 1, 3, 5, 0, 3, 0, 1, 0, 3, 2, 3, 3, 4, 4, 0, 2, 2, 0, 4, 4),
    (2, 4, 0, 5, 0, 4, 0, 3, 0, 4, 5, 5, 4, 3, 5, 3, 5, 3, 5, 3, 5, 2, 5, 3, 4, 3, 3, 4, 3, 4, 5, 3, 2, 1, 5, 4, 3, 2, 3, 4, 5, 3, 4, 1, 2, 5, 4, 3, 0, 3, 3, 0, 3, 2, 0, 2, 3, 0, 4, 1, 0, 3, 4, 3, 3, 5, 0, 3, 0, 1, 0, 4, 5, 5, 5, 4, 3, 0, 4, 2, 0, 3, 5),
    (0, 5, 0, 4, 0, 4, 0, 2, 0, 5, 4, 3, 4, 3, 4, 3, 3, 3, 4, 3, 4, 2, 5, 3, 5, 3, 4, 1, 4, 3, 4, 4, 4, 0, 3, 5, 0, 4, 4, 4, 4, 5, 3, 1, 3, 4, 5, 3, 3, 3, 3, 3, 3, 3, 0, 2, 2, 0, 3, 3, 2, 4, 3, 3, 3, 5, 3, 4, 1, 3, 3, 5, 3, 2, 0, 0, 0, 0, 4, 3, 1, 3, 3),
    (0, 1, 0, 3, 0, 3, 0, 1, 0, 1, 3, 3, 3, 2, 3, 3, 3, 0, 3, 0, 0, 0, 3, 1, 3, 0, 0, 0, 2, 2, 2, 3, 0, 0, 3, 2, 0, 1, 2, 4, 1, 3, 3, 0, 0, 3, 3, 3, 0, 1, 0, 0, 2, 1, 0, 0, 3, 0, 3, 1, 0, 3, 0, 0, 1, 3, 0, 2, 0, 1, 0, 3, 3, 1, 3, 3, 0, 0, 1, 1, 0, 3, 3),
    (0, 2, 0, 3, 0, 2, 1, 4, 0, 2, 2, 3, 1, 1, 3, 1, 1, 0, 2, 0, 3, 1, 2, 3, 1, 3, 0, 0, 1, 0, 4, 3, 2, 3, 3, 3, 1, 4, 2, 3, 3, 3, 3, 1, 0, 3, 1, 4, 0, 1, 1, 0, 1, 2, 0, 1, 1, 0, 1, 1, 0, 3, 1, 3, 2, 2, 0, 1, 0, 0, 0, 2, 3, 3, 3, 1, 0, 0, 0, 0, 0, 2, 3),
    (0, 5, 0, 4, 0, 5, 0, 2, 0, 4, 5, 5, 3, 3, 4, 3, 3, 1, 5, 4, 4, 2, 4, 4, 4, 3, 4, 2, 4, 3, 5, 5, 4, 3, 3, 4, 3, 3, 5, 5, 4, 5, 5, 1, 3, 4, 5, 3, 1, 4, 3, 1, 3, 3, 0, 3, 3, 1, 4, 3, 1, 4, 5, 3, 3, 5, 0, 4, 0, 3, 0, 5, 3, 3, 1, 4, 3, 0, 4, 0, 1, 5, 3),
    (0, 5, 0, 5, 0, 4, 0, 2, 0, 4, 4, 3, 4, 3, 3, 3, 3, 3, 5, 4, 4, 4, 4, 4, 4, 5, 3, 3, 5, 2, 4, 4, 4, 3, 4, 4, 3, 3, 4, 4, 5, 5, 3, 3, 4, 3, 4, 3, 3, 4, 3, 3, 3, 3, 1, 2, 2, 1, 4, 3, 3, 5, 4, 4, 3, 4, 0, 4, 0, 3, 0, 4, 4, 4, 4, 4, 1, 0, 4, 2, 0, 2, 4),
    (0, 4, 0, 4, 0, 3, 0, 1, 0, 3, 5, 2, 3, 0, 3, 0, 2, 1, 4, 2, 3, 3, 4, 1, 4, 3, 3, 2, 4, 1, 3, 3, 3, 0, 3, 3, 0, 0, 3, 3, 3, 5, 3, 3, 3, 3, 3, 2, 0, 2, 0, 0, 2, 0, 0, 2, 0, 0, 1, 0, 0, 3, 1, 2, 2, 3, 0, 3, 0, 2, 0, 4, 4, 3, 3, 4, 1, 0, 3, 0, 0, 2, 4),
    (0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 2, 0, 0, 0, 0, 0, 1, 0, 2, 0, 1, 0, 0, 0, 0, 0, 3, 1, 3, 0, 3, 2, 0, 0, 0, 1, 0, 3, 2, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 4, 0, 2, 0, 0, 0, 0, 0, 0, 2),
    (0, 2, 1, 3, 0, 2, 0, 2, 0, 3, 3, 3, 3, 1, 3, 1, 3, 3, 3, 3, 3, 3, 4, 2, 2, 1, 2, 1, 4, 0, 4, 3, 1, 3, 3, 3, 2, 4, 3, 5, 4, 3, 3, 3, 3, 3, 3, 3, 0, 1, 3, 0, 2, 0, 0, 1, 0, 0, 1, 0, 0, 4, 2, 0, 2, 3, 0, 3, 3, 0, 3, 3, 4, 2, 3, 1, 4, 0, 1, 2, 0, 2, 3),
    (0, 3, 0, 3, 0, 1, 0, 3, 0, 2, 3, 3, 3, 0, 3, 1, 2, 0, 3, 3, 2, 3, 3, 2, 3, 2, 3, 1, 3, 0, 4, 3, 2, 0, 3, 3, 1, 4, 3, 3, 2, 3, 4, 3, 1, 3, 3, 1, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 4, 1, 1, 0, 3, 0, 3, 1, 0, 2, 3, 3, 3, 3, 3, 1, 0, 0, 2, 0, 3, 3),
    (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 2, 0, 3, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 3, 0, 3, 0, 3, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 2, 0, 2, 3, 0, 0, 0, 0, 0, 0, 0, 0, 3),
    (0, 2, 0, 3, 1, 3, 0, 3, 0, 2, 3, 3, 3, 1, 3, 1, 3, 1, 3, 1, 3, 3, 3, 1, 3, 0, 2, 3, 1, 1, 4, 3, 3, 2, 3, 3, 1, 2, 2, 4, 1, 3, 3, 0, 1, 4, 2, 3, 0, 1, 3, 0, 3, 0, 0, 1, 3, 0, 2, 0, 0, 3, 3, 2, 1, 3, 0, 3, 0, 2, 0, 3, 4, 4, 4, 3, 1, 0, 3, 0, 0, 3, 3),
    (0, 2, 0, 1, 0, 2, 0, 0, 0, 1, 3, 2, 2, 1, 3, 0, 1, 1, 3, 0, 3, 2, 3, 1, 2, 0, 2, 0, 1, 1, 3, 3, 3, 0, 3, 3, 1, 1, 2, 3, 2, 3, 3, 1, 2, 3, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 3, 0, 1, 0, 0, 2, 1, 2, 1, 3, 0, 3, 0, 0, 0, 3, 4, 4, 4, 3, 2, 0, 2, 0, 0, 2, 4),
    (0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 3, 1, 0, 0, 0, 0, 0, 0, 0, 3),
    (0, 3, 0, 3, 0, 2, 0, 3, 0, 3, 3, 3, 2, 3, 2, 2, 2, 0, 3, 1, 3, 3, 3, 2, 3, 3, 0, 0, 3, 0, 3, 2, 2, 0, 2, 3, 1, 4, 3, 4, 3, 3, 2, 3, 1, 5, 4, 4, 0, 3, 1, 2, 1, 3, 0, 3, 1, 1, 2, 0, 2, 3, 1, 3, 1, 3, 0, 3, 0, 1, 0, 3, 3, 4, 4, 2, 1, 0, 2, 1, 0, 2, 4),
    (0, 1, 0, 3, 0, 1, 0, 2, 0, 1, 4, 2, 5, 1, 4, 0, 2, 0, 2, 1, 3, 1, 4, 0, 2, 1, 0, 0, 2, 1, 4, 1, 1, 0, 3, 3, 0, 5, 1, 3, 2, 3, 3, 1, 0, 3, 2, 3, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 4, 0, 1, 0, 3, 0, 2, 0, 1, 0, 3, 3, 3, 4, 3, 3, 0, 0, 0, 0, 2, 3),
    (0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, 0, 0, 1, 0, 0, 0, 0, 0, 3),
    (0, 1, 0, 3, 0, 4, 0, 3, 0, 2, 4, 3, 1, 0, 3, 2, 2, 1, 3, 1, 2, 2, 3, 1, 1, 1, 2, 1, 3, 0, 1, 2, 0, 1, 3, 2, 1, 3, 0, 5, 5, 1, 0, 0, 1, 3, 2, 1, 0, 3, 0, 0, 1, 0, 0, 0, 0, 0, 3, 4, 0, 1, 1, 1, 3, 2, 0, 2, 0, 1, 0, 2, 3, 3, 1, 2, 3, 0, 1, 0, 1, 0, 4),
    (0, 0, 0, 1, 0, 3, 0, 3, 0, 2, 2, 1, 0, 0, 4, 0, 3, 0, 3, 1, 3, 0, 3, 0, 3, 0, 1, 0, 3, 0, 3, 1, 3, 0, 3, 3, 0, 0, 1, 2, 1, 1, 1, 0, 1, 2, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 3, 3, 3, 3, 0, 0, 0, 0, 1, 4),
    (0, 0, 0, 3, 0, 3, 0, 0, 0, 0, 3, 1, 1, 0, 3, 0, 1, 0, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 3, 0, 2, 0, 2, 3, 0, 0, 2, 2, 3, 1, 2, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 2, 0, 0, 0, 0, 2, 3),
    (2, 4, 0, 5, 0, 5, 0, 4, 0, 3, 4, 3, 3, 3, 4, 3, 3, 3, 4, 3, 4, 4, 5, 4, 5, 5, 5, 2, 3, 0, 5, 5, 4, 1, 5, 4, 3, 1, 5, 4, 3, 4, 4, 3, 3, 4, 3, 3, 0, 3, 2, 0, 2, 3, 0, 3, 0, 0, 3, 3, 0, 5, 3, 2, 3, 3, 0, 3, 0, 3, 0, 3, 4, 5, 4, 5, 3, 0, 4, 3, 0, 3, 4),
    (0, 3, 0, 3, 0, 3, 0, 3, 0, 3, 3, 4, 3, 2, 3, 2, 3, 0, 4, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 2, 4, 3, 3, 1, 3, 4, 3, 4, 4, 4, 3, 4, 4, 3, 2, 4, 4, 1, 0, 2, 0, 0, 1, 1, 0, 2, 0, 0, 3, 1, 0, 5, 3, 2, 1, 3, 0, 3, 0, 1, 2, 4, 3, 2, 4, 3, 3, 0, 3, 2, 0, 4, 4),
    (0, 3, 0, 3, 0, 1, 0, 0, 0, 1, 4, 3, 3, 2, 3, 1, 3, 1, 4, 2, 3, 2, 4, 2, 3, 4, 3, 0, 2, 2, 3, 3, 3, 0, 3, 3, 3, 0, 3, 4, 1, 3, 3, 0, 3, 4, 3, 3, 0, 1, 1, 0, 1, 0, 0, 0, 4, 0, 3, 0, 0, 3, 1, 2, 1, 3, 0, 4, 0, 1, 0, 4, 3, 3, 4, 3, 3, 0, 2, 0, 0, 3, 3),
    (0, 3, 0, 4, 0, 1, 0, 3, 0, 3, 4, 3, 3, 0, 3, 3, 3, 1, 3, 1, 3, 3, 4, 3, 3, 3, 0, 0, 3, 1, 5, 3, 3, 1, 3, 3, 2, 5, 4, 3, 3, 4, 5, 3, 2, 5, 3, 4, 0, 1, 0, 0, 0, 0, 0, 2, 0, 0, 1, 1, 0, 4, 2, 2, 1, 3, 0, 3, 0, 2, 0, 4, 4, 3, 5, 3, 2, 0, 1, 1, 0, 3, 4),
    (0, 5, 0, 4, 0, 5, 0, 2, 0, 4, 4, 3, 3, 2, 3, 3, 3, 1, 4, 3, 4, 1, 5, 3, 4, 3, 4, 0, 4, 2, 4, 3, 4, 1, 5, 4, 0, 4, 4, 4, 4, 5, 4, 1, 3, 5, 4, 2, 1, 4, 1, 1, 3, 2, 0, 3, 1, 0, 3, 2, 1, 4, 3, 3, 3, 4, 0, 4, 0, 3, 0, 4, 4, 4, 3, 3, 3, 0, 4, 2, 0, 3, 4),
    (1, 4, 0, 4, 0, 3, 0, 1, 0, 3, 3, 3, 1, 1, 3, 3, 2, 2, 3, 3, 1, 0, 3, 2, 2, 1, 2, 0, 3, 1, 2, 1, 2, 0, 3, 2, 0, 2, 2, 3, 3, 4, 3, 0, 3, 3, 1, 2, 0, 1, 1, 3, 1, 2, 0, 0, 3, 0, 1, 1, 0, 3, 2, 2, 3, 3, 0, 3, 0, 0, 0, 2, 3, 3, 4, 3, 3, 0, 1, 0, 0, 1, 4),
    (0, 4, 0, 4, 0, 4, 0, 0, 0, 3, 4, 4, 3, 1, 4, 2, 3, 2, 3, 3, 3, 1, 4, 3, 4, 0, 3, 0, 4, 2, 3, 3, 2, 2, 5, 4, 2, 1, 3, 4, 3, 4, 3, 1, 3, 3, 4, 2, 0, 2, 1, 0, 3, 3, 0, 0, 2, 0, 3, 1, 0, 4, 4, 3, 4, 3, 0, 4, 0, 1, 0, 2, 4, 4, 4, 4, 4, 0, 3, 2, 0, 3, 3),
    (0, 0, 0, 1, 0, 4, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 3, 2, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 2),
    (0, 2, 0, 3, 0, 4, 0, 4, 0, 1, 3, 3, 3, 0, 4, 0, 2, 1, 2, 1, 1, 1, 2, 0, 3, 1, 1, 0, 1, 0, 3, 1, 0, 0, 3, 3, 2, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 2, 0, 2, 2, 0, 3, 1, 0, 0, 1, 0, 1, 1, 0, 1, 2, 0, 3, 0, 0, 0, 0, 1, 0, 0, 3, 3, 4, 3, 1, 0, 1, 0, 3, 0, 2),
    (0, 0, 0, 3, 0, 5, 0, 0, 0, 0, 1, 0, 2, 0, 3, 1, 0, 1, 3, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 4, 0, 0, 0, 2, 3, 0, 1, 4, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 3, 0, 0, 0, 0, 0, 3),
    (0, 2, 0, 5, 0, 5, 0, 1, 0, 2, 4, 3, 3, 2, 5, 1, 3, 2, 3, 3, 3, 0, 4, 1, 2, 0, 3, 0, 4, 0, 2, 2, 1, 1, 5, 3, 0, 0, 1, 4, 2, 3, 2, 0, 3, 3, 3, 2, 0, 2, 4, 1, 1, 2, 0, 1, 1, 0, 3, 1, 0, 1, 3, 1, 2, 3, 0, 2, 0, 0, 0, 1, 3, 5, 4, 4, 4, 0, 3, 0, 0, 1, 3),
    (0, 4, 0, 5, 0, 4, 0, 4, 0, 4, 5, 4, 3, 3, 4, 3, 3, 3, 4, 3, 4, 4, 5, 3, 4, 5, 4, 2, 4, 2, 3, 4, 3, 1, 4, 4, 1, 3, 5, 4, 4, 5, 5, 4, 4, 5, 5, 5, 2, 3, 3, 1, 4, 3, 1, 3, 3, 0, 3, 3, 1, 4, 3, 4, 4, 4, 0, 3, 0, 4, 0, 3, 3, 4, 4, 5, 0, 0, 4, 3, 0, 4, 5),
    (0, 4, 0, 4, 0, 3, 0, 3, 0, 3, 4, 4, 4, 3, 3, 2, 4, 3, 4, 3, 4, 3, 5, 3, 4, 3, 2, 1, 4, 2, 4, 4, 3, 1, 3, 4, 2, 4, 5, 5, 3, 4, 5, 4, 1, 5, 4, 3, 0, 3, 2, 2, 3, 2, 1, 3, 1, 0, 3, 3, 3, 5, 3, 3, 3, 5, 4, 4, 2, 3, 3, 4, 3, 3, 3, 2, 1, 0, 3, 2, 1, 4, 3),
    (0, 4, 0, 5, 0, 4, 0, 3, 0, 3, 5, 5, 3, 2, 4, 3, 4, 0, 5, 4, 4, 1, 4, 4, 4, 3, 3, 3, 4, 3, 5, 5, 2, 3, 3, 4, 1, 2, 5, 5, 3, 5, 5, 2, 3, 5, 5, 4, 0, 3, 2, 0, 3, 3, 1, 1, 5, 1, 4, 1, 0, 4, 3, 2, 3, 5, 0, 4, 0, 3, 0, 5, 4, 3, 4, 3, 0, 0, 4, 1, 0, 4, 4),
    (1, 3, 0, 4, 0, 2, 0, 2, 0, 2, 5, 5, 3, 3, 3, 3, 3, 0, 4, 2, 3, 4, 4, 4, 3, 4, 0, 0, 3, 4, 5, 4, 3, 3, 3, 3, 2, 5, 5, 4, 5, 5, 5, 4, 3, 5, 5, 5, 1, 3, 1, 0, 1, 0, 0, 3, 2, 0, 4, 2, 0, 5, 2, 3, 2, 4, 1, 3, 0, 3, 0, 4, 5, 4, 5, 4, 3, 0, 4, 2, 0, 5, 4),
    (0, 3, 0, 4, 0, 5, 0, 3, 0, 3, 4, 4, 3, 2, 3, 2, 3, 3, 3, 3, 3, 2, 4, 3, 3, 2, 2, 0, 3, 3, 3, 3, 3, 1, 3, 3, 3, 0, 4, 4, 3, 4, 4, 1, 1, 4, 4, 2, 0, 3, 1, 0, 1, 1, 0, 4, 1, 0, 2, 3, 1, 3, 3, 1, 3, 4, 0, 3, 0, 1, 0, 3, 1, 3, 0, 0, 1, 0, 2, 0, 0, 4, 4),
    (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 3, 0, 3, 0, 2, 0, 3, 0, 1, 5, 4, 3, 3, 3, 1, 4, 2, 1, 2, 3, 4, 4, 2, 4, 4, 5, 0, 3, 1, 4, 3, 4, 0, 4, 3, 3, 3, 2, 3, 2, 5, 3, 4, 3, 2, 2, 3, 0, 0, 3, 0, 2, 1, 0, 1, 2, 0, 0, 0, 0, 2, 1, 1, 3, 1, 0, 2, 0, 4, 0, 3, 4, 4, 4, 5, 2, 0, 2, 0, 0, 1, 3),
    (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 4, 2, 1, 1, 0, 1, 0, 3, 2, 0, 0, 3, 1, 1, 1, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 1, 0, 0, 0, 2, 0, 0, 0, 1, 4, 0, 4, 2, 1, 0, 0, 0, 0, 0, 1),
    (0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 3, 1, 0, 0, 0, 2, 0, 2, 1, 0, 0, 1, 2, 1, 0, 1, 1, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 1, 0, 0, 0, 0, 0, 1, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 2),
    (0, 4, 0, 4, 0, 4, 0, 3, 0, 4, 4, 3, 4, 2, 4, 3, 2, 0, 4, 4, 4, 3, 5, 3, 5, 3, 3, 2, 4, 2, 4, 3, 4, 3, 1, 4, 0, 2, 3, 4, 4, 4, 3, 3, 3, 4, 4, 4, 3, 4, 1, 3, 4, 3, 2, 1, 2, 1, 3, 3, 3, 4, 4, 3, 3, 5, 0, 4, 0, 3, 0, 4, 3, 3, 3, 2, 1, 0, 3, 0, 0, 3, 3),
    (0, 4, 0, 3, 0, 3, 0, 3, 0, 3, 5, 5, 3, 3, 3, 3, 4, 3, 4, 3, 3, 3, 4, 4, 4, 3, 3, 3, 3, 4, 3, 5, 3, 3, 1, 3, 2, 4, 5, 5, 5, 5, 4, 3, 4, 5, 5, 3, 2, 2, 3, 3, 3, 3, 2, 3, 3, 1, 2, 3, 2, 4, 3, 3, 3, 4, 0, 4, 0, 2, 0, 4, 3, 2, 2, 1, 2, 0, 3, 0, 0, 4, 1),
)


class JapaneseContextAnalysis:
    def __init__(self):
        self.reset()

    def reset(self):
        self._mTotalRel = 0  # total sequence received
        # category counters, each interger counts sequence in its category
        self._mRelSample = [0] * NUM_OF_CATEGORY
        # if last byte in current buffer is not the last byte of a character,
        # we need to know how many bytes to skip in next buffer
        self._mNeedToSkipCharNum = 0
        self._mLastCharOrder = -1  # The order of previous char
        # If this flag is set to True, detection is done and conclusion has
        # been made
        self._mDone = False

    def feed(self, aBuf, aLen):
        if self._mDone:
            return

        # The buffer we got is byte oriented, and a character may span in more than one
        # buffers. In case the last one or two byte in last buffer is not
        # complete, we record how many byte needed to complete that character
        # and skip these bytes here.  We can choose to record those bytes as
        # well and analyse the character once it is complete, but since a
        # character will not make much difference, by simply skipping
        # this character will simply our logic and improve performance.
        i = self._mNeedToSkipCharNum
        while i < aLen:
            order, charLen = self.get_order(aBuf[i:i + 2])
            i += charLen
            if i > aLen:
                self._mNeedToSkipCharNum = i - aLen
                self._mLastCharOrder = -1
            else:
                if (order != -1) and (self._mLastCharOrder != -1):
                    self._mTotalRel += 1
                    if self._mTotalRel > MAX_REL_THRESHOLD:
                        self._mDone = True
                        break
                    self._mRelSample[jp2CharContext[self._mLastCharOrder][order]] += 1
                self._mLastCharOrder = order

    def got_enough_data(self):
        return self._mTotalRel > ENOUGH_REL_THRESHOLD

    def get_confidence(self):
        # This is just one way to calculate confidence. It works well for me.
        if self._mTotalRel > MINIMUM_DATA_THRESHOLD:
            return (self._mTotalRel - self._mRelSample[0]) / self._mTotalRel
        else:
            return DONT_KNOW

    def get_order(self, aBuf):
        return -1, 1


class SJISContextAnalysis(JapaneseContextAnalysis):
    def __init__(self):
        self.charset_name = "SHIFT_JIS"

    def get_charset_name(self):
        return self.charset_name

    def get_order(self, aBuf):
        if not aBuf:
            return -1, 1
        # find out current char's byte length
        first_char = wrap_ord(aBuf[0])
        if ((0x81 <= first_char <= 0x9F) or (0xE0 <= first_char <= 0xFC)):
            charLen = 2
            if (first_char == 0x87) or (0xFA <= first_char <= 0xFC):
                self.charset_name = "CP932"
        else:
            charLen = 1

        # return its order if it is hiragana
        if len(aBuf) > 1:
            second_char = wrap_ord(aBuf[1])
            if (first_char == 202) and (0x9F <= second_char <= 0xF1):
                return second_char - 0x9F, charLen

        return -1, charLen


class EUCJPContextAnalysis(JapaneseContextAnalysis):
    def get_order(self, aBuf):
        if not aBuf:
            return -1, 1
        # find out current char's byte length
        first_char = wrap_ord(aBuf[0])
        if (first_char == 0x8E) or (0xA1 <= first_char <= 0xFE):
            charLen = 2
        elif first_char == 0x8F:
            charLen = 3
        else:
            charLen = 1

        # return its order if it is hiragana
        if len(aBuf) > 1:
            second_char = wrap_ord(aBuf[1])
            if (first_char == 0xA4) and (0xA1 <= second_char <= 0xF3):
                return second_char - 0xA1, charLen

        return -1, charLen

# flake8: noqa
