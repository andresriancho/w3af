#
# This is part of "python-cluster". A library to group similar items together.
# Copyright (C) 2006   Michel Albert
#
# This library is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

from types import TupleType

class ClusteringError(Exception):
   pass

def flatten(L):
   """
   Flattens a list.
   Example:
   flatten([a,b,[c,d,[e,f]]]) = [a,b,c,d,e,f]
   """
   if type(L) != type([]): return [L]
   if L == []: return L
   return flatten(L[0]) + flatten(L[1:])

def median(numbers):
   """Return the median of the list of numbers.
   found at: http://mail.python.org/pipermail/python-list/2004-December/294990.html"""

   # Sort the list and take the middle element.
   n = len(numbers)
   copy = numbers[:] # So that "numbers" keeps its original order
   copy.sort()
   if n & 1:         # There is an odd number of elements
      return copy[n // 2]
   else:
      return (copy[n // 2 - 1] + copy[n // 2]) / 2.0

def mean(numbers):
   """Returns the arithmetic mean of a numeric list.
   found at: http://mail.python.org/pipermail/python-list/2004-December/294990.html"""
   return float(sum(numbers)) / float(len(numbers))

def minkowski_distance(x, y, p=2):
   """
   Calculates the minkowski distance between two points.

   PARAMETERS
      x - the first point
      y - the second point
      p - the order of the minkowski algorithm.
          Default = 2. This is equal to the euclidian distance.
                       If the order is 1, it is equal to the manhatten
                       distance.
                       The higher the order, the closer it converges to the
                       Chebyshev distance, which has p=infinity
   """
   from math import pow
   assert(len(y)==len(x))
   assert(x>=1)
   sum = 0
   for i in range(len(x)):
      sum += abs(x[i]-y[i]) ** p
   return pow(sum, 1.0/float(p))

def genmatrix(list, combinfunc, symmetric=False, diagonal=None):
   """
   Takes a list and generates a 2D-matrix using the supplied combination
   function to calculate the values.

   PARAMETERS
      list        - the list of items
      combinfunc  - the function that is used to calculate teh value in a cell.
                    It has to cope with two arguments.
      symmetric   - Whether it will be a symmetric matrix along the diagonal.
                    For example, it the list contains integers, and the
                    combination function is abs(x-y), then the matrix will be
                    symmetric.
                    Default: False
      diagonal    - The value to be put into the diagonal. For some functions,
                    the diagonal will stay constant. An example could be the
                    function "x-y". Then each diagonal cell will be "0".
                    If this value is set to None, then the diagonal will be
                    calculated.
                    Default: None
   """
   matrix = []
   row_index = 0
   for item in list:
      row = []
      col_index = 0
      for item2 in list:
         if diagonal is not None and col_index == row_index:
            # if this is a cell on the diagonal
            row.append(diagonal)
         elif symmetric and col_index < row_index:
            # if the matrix is symmetric and we are "in the lower left triangle"
            row.append( matrix[col_index][row_index] )
         else:
            # if this cell is not on the diagonal
            row.append(combinfunc(item, item2))
         col_index += 1
      matrix.append(row)
      row_index += 1
   return matrix

def printmatrix(list):
   """
   Prints out a 2-dimensional list cleanly.
   This is useful for debugging.

   PARAMETERS
      list  -  the 2D-list to display
   """
   # determine maximum length
   maxlen = 0
   colcount = len(list[0])
   for col in list:
      for cell in col:
         maxlen = max(len(str(cell)), maxlen)
   # print data
   format =  " %%%is |" % maxlen
   format = "|" + format*colcount
   for row in list:
      print format % tuple(row)

def magnitude(a):
   "calculates the magnitude of a vecor"
   from math import sqrt
   sum = 0
   for coord in a:
      sum += coord ** 2
   return sqrt(sum)

def dotproduct(a, b):
   "Calculates the dotproduct between two vecors"
   assert(len(a) == len(b))
   out = 0
   for i in range(len(a)):
      out += a[i]*b[i]
   return out

def centroid(list, method=median):
   "returns the central vector of a list of vectors"
   out = []
   for i in range(len(list[0])):
      out.append( method( [x[i] for x in list] ) )
   return tuple(out)

class Cluster:
   """
   A collection of items. This is internally used to detect clustered items in
   the data so we could distinguish other collection types (lists, dicts, ...)
   from the actual clusters. This means that you could also create clusters of
   lists with this class.
   """

   def __str__(self):
      return "<Cluster@%s(%s)>" % (self.__level, self.__items)

   def __repr__(self):
      return self.__str__()

   def __init__(self, level, *args):
      """
      Constructor

      PARAMETERS
         level - The level of this cluster. This is used in hierarchical
                 clustering to retrieve a specific set of clusters. The higher
                 the level, the smaller the count of clusters returned. The
                 level depends on the difference function used.
         *args - every additional argument passed following the level value
                 will get added as item to the cluster. You could also pass a
                 list as second parameter to initialise the cluster with that
                 list as content
      """
      self.__level = level
      if len(args) == 0: self.__items = []
      else:              self.__items = list(args)

   def append(self, item):
      """
      Appends a new item to the cluster

      PARAMETERS
         item  -  The item that is to be appended
      """
      self.__items.append(item)

   def items(self, newItems = None):
      """
      Sets or gets the items of the cluster

      PARAMETERS
         newItems (optional) - if set, the items of the cluster will be
                               replaced with that argument.
      """
      if newItems is None: return self.__items
      else:                self.__items = newItems

   def fullyflatten(self, *args):
      """
      Completely flattens out this cluster and returns a one-dimensional list
      containing the cluster's items. This is useful in cases where some items
      of the cluster are clusters in their own right and you only want the
      items.

      PARAMETERS
         *args - only used for recursion.
      """
      flattened_items = []
      if len(args) == 0: collection = self.__items
      else:              collection = args[0].items()

      for item in collection:
         if isinstance(item, Cluster):
            flattened_items = flattened_items + self.fullyflatten(item)
         else:
            flattened_items.append(item)

      return flattened_items

   def level(self):
      """
      Returns the level associated with this cluster
      """
      return self.__level

   def display(self, depth=0):
      """
      Pretty-prints this cluster. Useful for debuging
      """
      print depth*"   " + "[level %s]" % self.__level
      for item in self.__items:
         if isinstance(item, Cluster):
            item.display(depth+1)
         else:
            print depth*"   "+"%s" % item

   def topology(self):
      """
      Returns the structure (topology) of the cluster as tuples.

      Output from cl.data:
          [<Cluster@0.833333333333(['CVS', <Cluster@0.818181818182(['34.xls',
          <Cluster@0.789473684211([<Cluster@0.555555555556(['0.txt',
          <Cluster@0.181818181818(['ChangeLog', 'ChangeLog.txt'])>])>,
          <Cluster@0.684210526316(['20060730.py',
          <Cluster@0.684210526316(['.cvsignore',
          <Cluster@0.647058823529(['About.py',
          <Cluster@0.625(['.idlerc', '.pylint.d'])>])>])>])>])>])>])>]

      Corresponding output from cl.topo():
          ('CVS', ('34.xls', (('0.txt', ('ChangeLog', 'ChangeLog.txt')),
          ('20060730.py', ('.cvsignore', ('About.py',
          ('.idlerc', '.pylint.d')))))))
      """

      left  = self.__items[0]
      right = self.__items[1]
      if isinstance(left, Cluster):
          first = left.topology()
      else:
          first = left
      if isinstance(right, Cluster):
          second = right.topology()
      else:
          second = right
      return first, second

   def getlevel(self, threshold):
      """
      Retrieve all clusters up to a specific level threshold. This
      level-threshold represents the maximum distance between two clusters. So
      the lower you set this threshold, the more clusters you will receive and
      the higher you set it, you will receive less but bigger clusters.

      PARAMETERS
         threshold - The level threshold

      NOTE
         It is debatable whether the value passed into this method should
         really be as strongly linked to the real cluster-levels as it is right
         now. The end-user will not know the range of this value unless s/he
         first inspects the top-level cluster. So instead you might argue that
         a value ranging from 0 to 1 might be a more useful approach.
      """

      left  = self.__items[0]
      right = self.__items[1]

      # if this object itself is below the threshold value we only need to
      # return it's contents as a list
      if self.level() <= threshold:
         return [self.fullyflatten()]

      # if this cluster's level is higher than the threshold we will investgate
      # it's left and right part. Their level could be below the threshold
      if isinstance(left, Cluster) and left.level() <= threshold:
         if isinstance(right, Cluster):
            return [left.fullyflatten()] + right.getlevel(threshold)
         else:
            return [left.fullyflatten()] + [[right]]
      elif isinstance(right, Cluster) and right.level() <= threshold:
         if isinstance(left, Cluster):
            return left.getlevel(threshold) + [right.fullyflatten()]
         else:
            return [[left]] + [right.fullyflatten()]

      # Alright. We covered the cases where one of the clusters was below the
      # threshold value. Now we'll deal with the clusters that are above by
      # recursively applying the previous cases.
      if isinstance(left, Cluster) and isinstance(right, Cluster):
         return left.getlevel(threshold) + right.getlevel(threshold)
      elif isinstance(left, Cluster):
         return left.getlevel(threshold) + [[right]]
      elif isinstance(right, Cluster):
         return [[left]] + right.getlevel(threshold)
      else:
         return [[left], [right]]

class BaseClusterMethod:
   """
   The base class of all clustering methods.
   """

   def __init__(self, input, distance_function):
      """
      Constructs the object and starts clustering

      PARAMETERS
         input             - a list of objects
         distance_function - a function returning the distance - or opposite of
                             similarity ( distance = -similarity ) - of two
                             items from the input. In other words, the closer
                             the two items are related, the smaller this value
                             needs to be. With 0 meaning they are exactly the
                             same.

      NOTES
         The distance function should always return the absolute distance
         between two given items of the list. Say,

         distance(input[1], input[4]) = distance(input[4], input[1])

         This is very important for the clustering algorithm to work!
         Naturally, the data returned by the distance function MUST be a
         comparable datatype, so you can perform arithmetic comparisons on
         them (< or >)! The simplest examples would be floats or ints. But as
         long as they are comparable, it's ok.
      """
      self.distance = distance_function
      self._input = input    # the original input
      self._data  = input[:] # clone the input so we can work with it

   def topo(self):
      """
      Returns the structure (topology) of the cluster.

      See Cluster.topology() for information.
      """
      return self.data[0].topology()

   def __get_data(self):
      """
      Returns the data that is currently in process.
      """
      return self._data
   data = property(__get_data)

   def __get_raw_data(self):
      """
      Returns the raw data (data without being clustered).
      """
      return self._input
   raw_data = property(__get_raw_data)

class HierarchicalClustering(BaseClusterMethod):
   """
   Implementation of the hierarchical clustering method as explained in
   http://www.elet.polimi.it/upload/matteucc/Clustering/tutorial_html/hierarchical.html

   USAGE
      >>> from cluster import HierarchicalClustering
      >>> # or: from cluster import *
      >>> cl = HierarchicalClustering([123,334,345,242,234,1,3], lambda x,y: float(abs(x-y)))
      >>> cl.getlevel(90)
      [[345, 334], [234, 242], [123], [3, 1]]

      Note that all of the returned clusters are more that 90 apart

   """

   def __init__(self, data, distance_function, linkage='single'):
      """
      Constructor

      See BaseClusterMethod.__init__ for more details.
      """
      BaseClusterMethod.__init__(self, data, distance_function)

      # set the linkage type to single
      self.setLinkageMethod(linkage)
      self.__clusterCreated = False

   def setLinkageMethod(self, method):
      """
      Sets the method to determine the distance between two clusters.

      PARAMETERS:
         method - The name of the method to use. It must be one of 'single',
                  'complete', 'average' or 'uclus'
      """
      if method == 'single':
         self.linkage = self.singleLinkageDistance
      elif method == 'complete':
         self.linkage = self.completeLinkageDistance
      elif method == 'average':
         self.linkage = self.averageLinkageDistance
      elif method == 'uclus':
         self.linkage = self.uclusDistance
      else:
         raise ValueError, 'distance method must be one of single, complete, average of uclus'

   def uclusDistance(self, x, y):
      """
      The method to determine the distance between one cluster an another
      item/cluster. The distance equals to the *average* (median) distance from
      any member of one cluster to any member of the other cluster.

      PARAMETERS
         x  -  first cluster/item
         y  -  second cluster/item
      """
      # create a flat list of all the items in <x>
      if not isinstance(x, Cluster): x = [x]
      else: x = x.fullyflatten()

      # create a flat list of all the items in <y>
      if not isinstance(y, Cluster): y = [y]
      else: y = y.fullyflatten()

      distances = []
      for k in x:
         for l in y:
            distances.append(self.distance(k,l))
      return median(distances)

   def averageLinkageDistance(self, x, y):
      """
      The method to determine the distance between one cluster an another
      item/cluster. The distance equals to the *average* (mean) distance from
      any member of one cluster to any member of the other cluster.

      PARAMETERS
         x  -  first cluster/item
         y  -  second cluster/item
      """
      # create a flat list of all the items in <x>
      if not isinstance(x, Cluster): x = [x]
      else: x = x.fullyflatten()

      # create a flat list of all the items in <y>
      if not isinstance(y, Cluster): y = [y]
      else: y = y.fullyflatten()

      distances = []
      for k in x:
         for l in y:
            distances.append(self.distance(k,l))
      return mean(distances)

   def completeLinkageDistance(self, x, y):
      """
      The method to determine the distance between one cluster an another
      item/cluster. The distance equals to the *longest* distance from any
      member of one cluster to any member of the other cluster.

      PARAMETERS
         x  -  first cluster/item
         y  -  second cluster/item
      """

      # create a flat list of all the items in <x>
      if not isinstance(x, Cluster): x = [x]
      else: x = x.fullyflatten()

      # create a flat list of all the items in <y>
      if not isinstance(y, Cluster): y = [y]
      else: y = y.fullyflatten()

      # retrieve the minimum distance (single-linkage)
      maxdist = self.distance(x[0], y[0])
      for k in x:
         for l in y:
            maxdist = max(maxdist, self.distance(k,l))

      return maxdist

   def singleLinkageDistance(self, x, y):
      """
      The method to determine the distance between one cluster an another
      item/cluster. The distance equals to the *shortest* distance from any
      member of one cluster to any member of the other cluster.

      PARAMETERS
         x  -  first cluster/item
         y  -  second cluster/item
      """

      # create a flat list of all the items in <x>
      if not isinstance(x, Cluster): x = [x]
      else: x = x.fullyflatten()

      # create a flat list of all the items in <y>
      if not isinstance(y, Cluster): y = [y]
      else: y = y.fullyflatten()

      # retrieve the minimum distance (single-linkage)
      mindist = self.distance(x[0], y[0])
      for k in x:
         for l in y:
            mindist = min(mindist, self.distance(k,l))

      return mindist

   def cluster(self, matrix=None, level=None, sequence=None):
      """
      Perform hierarchical clustering. This method is automatically called by
      the constructor so you should not need to call it explicitly.

      PARAMETERS
         matrix   -  The 2D list that is currently under processing. The matrix
                     contains the distances of each item with each other
         level    -  The current level of clustering
         sequence -  The sequence number of the clustering
      """

      if matrix is None:
         # create level 0, first iteration (sequence)
         level    = 0
         sequence = 0
         matrix   = []

      # if the matrix only has two rows left, we are done
      while len(matrix) > 2 or matrix == []:

         matrix = genmatrix(self._data, self.linkage, True, 0)

         smallestpair = None
         mindistance  = None
         rowindex = 0   # keep track of where we are in the matrix
         # find the minimum distance
         for row in matrix:
            cellindex = 0 # keep track of where we are in the matrix
            for cell in row:
               # if we are not on the diagonal (which is always 0)
               # and if this cell represents a new minimum...
               if (rowindex != cellindex) and ( cell < mindistance or smallestpair is None ):
                  smallestpair = ( rowindex, cellindex )
                  mindistance  = cell
               cellindex += 1
            rowindex += 1

         sequence += 1
         level     = matrix[smallestpair[1]][smallestpair[0]]
         cluster   = Cluster(level, self._data[smallestpair[0]], self._data[smallestpair[1]])

         # maintain the data, by combining the the two most similar items in the list
         # we use the min and max functions to ensure the integrity of the data.
         # imagine: if we first remove the item with the smaller index, all the
         # rest of the items shift down by one. So the next index will be
         # wrong. We could simply adjust the value of the second "remove" call,
         # but we don't know the order in which they come. The max and min
         # approach clarifies that
         self._data.remove(self._data[max(smallestpair[0], smallestpair[1])]) # remove item 1
         self._data.remove(self._data[min(smallestpair[0], smallestpair[1])]) # remove item 2
         self._data.append(cluster)               # append item 1 and 2 combined

      # all the data is in one single cluster. We return that and stop
      self.__clusterCreated = True
      return

   def getlevel(self, threshold):
      """
      Returns all clusters with a maximum distance of <threshold> in between
      each other

      PARAMETERS
         threshold - the maximum distance between clusters

      SEE-ALSO
         Cluster.getlevel(threshold)
      """

      # if it's not worth clustering, just return the data
      if len(self._input) <= 1: return self._input

      # initialize the cluster if not yet done
      if not self.__clusterCreated: self.cluster()

      return self._data[0].getlevel(threshold)

class KMeansClustering:
   """
   Implementation of the kmeans clustering method as explained in
   http://www.elet.polimi.it/upload/matteucc/Clustering/tutorial_html/kmeans.html

   USAGE
   =====

     >>> from cluster import KMeansClustering
     >>> cl = KMeansClustering([(1,1), (2,1), (5,3), ...])
     >>> clusters = cl.getclusters(2)
   """

   def __init__(self, data, distance=None):
      """
      Constructor

      PARAMETERS
         data     - A list of tuples or integers.
         distance - A function determining the distance between two items.
                    Default: It assumes the tuples contain numeric values and
                             appiles a generalised form of the
                             euclidian-distance algorithm on them.
      """
      self.__data = data
      self.distance = distance
      self.__initial_length = len(data)

      # test if each item is of same dimensions
      if len(data) > 1 and isinstance(data[0], TupleType):
         control_length = len(data[0])
         for item in data[1:]:
            if len(item) != control_length:
               raise ValueError("Each item in the data list must have the same amount of dimensions. Item", item, "was out of line!")
      # now check if we need and have a distance function
      if len(data) > 1 and not isinstance(data[0], TupleType) and distance is None:
         raise ValueError("You supplied non-standard items but no distance function! We cannot continue!")
      # we now know that we have tuples, and assume therefore that it's items are numeric
      elif distance is None:
         self.distance = minkowski_distance

   def getclusters(self, n):
      """
      Generates <n> clusters

      PARAMETERS
         n - The amount of clusters that should be generated.
             n must be greater than 1
      """

      # only proceed if we got sensible input
      if n <= 1:
         raise ClusteringError("When clustering, you need to ask for at least two clusters! You asked for %d" % n)

      # return the data straight away if there is nothing to cluster
      if self.__data == [] or len(self.__data) == 1 or n == self.__initial_length:
         return self.__data

      # It makes no sense to ask for more clusters than data-items available
      if n > self.__initial_length:
         raise ClusteringError( """Unable to generate more clusters than items 
available. You supplied %d items, and asked for %d clusters.""" %
               (self.__initial_length, n) )

      self.initialiseClusters(self.__data, n)

      items_moved = True     # tells us if any item moved between the clusters,
                             # as we initialised the clusters, we assume that
                             # is the case
      while items_moved is True:
         items_moved = False
         for cluster in self.__clusters:
            for item in cluster:
               res = self.assign_item(item, cluster)
               if items_moved is False: items_moved = res
      return self.__clusters

   def assign_item(self, item, origin):
      """
      Assigns an item from a given cluster to the closest located cluster

      PARAMETERS
         item   - the item to be moved
         origin - the originating cluster
      """
      closest_cluster = origin
      for cluster in self.__clusters:
         if self.distance(item, centroid(cluster)) < self.distance(item, centroid(closest_cluster)):
            closest_cluster = cluster

      if closest_cluster != origin:
         self.move_item(item, origin, closest_cluster)
         return True
      else:
         return False

   def move_item(self, item, origin, destination):
      """
      Moves an item from one cluster to anoter cluster

      PARAMETERS

         item        - the item to be moved
         origin      - the originating cluster
         destination - the target cluster
      """
      destination.append( origin.pop( origin.index(item) ) )

   def initialiseClusters(self, input, clustercount):
      """
      Initialises the clusters by distributing the items from the data evenly
      across n clusters

      PARAMETERS
         input        - the data set (a list of tuples)
         clustercount - the amount of clusters (n)
      """
      # initialise the clusters with empty lists
      self.__clusters = []
      for x in xrange(clustercount): self.__clusters.append([])

      # distribute the items into the clusters
      count = 0
      for item in input:
         self.__clusters[ count % clustercount ].append(item)
         count += 1

