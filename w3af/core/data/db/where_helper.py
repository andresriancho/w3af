"""
Copyright 2009 Andres Riancho

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


class WhereHelper(object):
    """Simple WHERE condition maker."""
    conditions = {}
    _values = []

    def __init__(self, conditions={}):
        """Construct object."""
        self.conditions = conditions

    def values(self):
        """Return values for prep.statements."""
        if not self._values:
            self.sql()
        return self._values

    def _makePair(self, field, value, oper='=', conjunction='AND'):
        """Auxiliary method."""
        result = ' ' + conjunction + ' ' + field + ' ' + oper + ' ?'
        return (result, value)

    def sql(self, whereStr=True):
        """
        :return: SQL string.

        >>> w = WhereHelper( [ ('field', '3', '=') ] )
        >>> w.sql()
        ' WHERE field = ?'

        >>> w = WhereHelper( [ ('field', '3', '='), ('foo', '4', '=') ] )
        >>> w.sql()
        ' WHERE field = ? AND foo = ?'
        >>>
        """
        result = ''
        self._values = []

        for cond in self.conditions:
            if isinstance(cond[0], list):
                item, oper = cond
                tmpWhere = ''
                for tmpField in item:
                    tmpName, tmpValue, tmpOper = tmpField
                    sql, value = self._makePair(
                        tmpName, tmpValue, tmpOper, oper)
                    self._values.append(value)
                    tmpWhere += sql
                if tmpWhere:
                    result += " AND (" + tmpWhere[len(oper) + 1:] + ")"
            else:
                sql, value = self._makePair(cond[0], cond[1], cond[2])
                self._values.append(value)
                result += sql
        result = result[5:]

        if whereStr and result:
            result = ' WHERE ' + result

        return result

    def __str__(self):
        return self.sql() + ' | ' + str(self.values())
