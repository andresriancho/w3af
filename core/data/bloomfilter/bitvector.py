#!/usr/bin/env python

__version__ = '2.0.1'
__author__  = "Avinash Kak (kak@purdue.edu)"
__date__    = '2010-August-30'
__url__     = 'http://RVL4.ecn.purdue.edu/~kak/dist/BitVector-2.0.1.html'
__copyright__ = "(C) 2010 Avinash Kak. Python Software Foundation."

__doc__ = '''

    BitVector.py

    Version: ''' + __version__ + '''
   
    Author: Avinash Kak (kak@purdue.edu)

    Date: ''' + __date__ + '''

    @title
    CHANGE LOG:

       Version 2.0.1

           Fixed numerous typos and other errors in the documentation page
           for the module.  The implementation code remains unchanged.

       Version 2.0

           To address the needs of the folks who are using the BitVector
           class in data mining research, the new version of the class
           includes several additional methods.  Since the bit vectors used
           by these folks can be extremely long, possibly involving
           millions of bits, the new version of the class includes a much
           faster method for counting the total number of set bits when a
           bit vector is sparse.  [But note that this new bit counting
           method may perform poorly for dense bit vectors. So the old bit
           counting method has been retained.]  Also for data mining folks,
           the new version of the class is provided with similarity and
           distance calculation metrics such as the Jaccard similarity
           coefficient, the Jaccard distance, and the Hamming distance.
           Again for the same folks, the class now also has a
           next_set_bit(from_index) method.  Other enhancements to the
           class include methods for folks who do research in cryptography.
           Now you can directly calculate the greatest common divisor of
           two bit vectors, or find the multiplicative inverse of one bit
           vector modulo another bit vector.

       Version 1.5.1:

           Removed a bug from the implementation of the right circular
           shift operator.

       Version 1.5:

           This version should prove to be much more efficient for long bit
           vectors.  Efficiency in BitVector construction when only its
           size is specified was achieved by eliminating calls to
           _setbit().  The application of logical operators to two
           BitVectors of equal length was also made efficient by
           eliminating calls to the padding function.  Another feature of
           this version is the count_bits() method that returns the total
           number of bits set in a BitVector instance.  Yet another feature
           of this version is the setValue() method that alters the bit
           pattern associated with a previously constructed BitVector.
       
       Version 1.4.1:

           The reset() method now returns 'self' to allow for cascaded
           invocation with the slicing operator.  Also removed the
           discrepancy between the value of the __copyright__ variable in
           the module and the value of license variable in setup.py.

       Version 1.4:

           This version includes the following two upgrades: 1) code for
           slice assignment; and 2) A reset function to reinitialize a
           previously constructed BitVector.  Additionally, the code was
           cleaned up with the help of pychecker.

       Version 1.3.2:

           Fixed a potentially misleading documentation issue for the
           Windows users of the BitVector class.  If you are writing an
           internally generated BitVector to a disk file, you must open the
           file in the binary mode.  If you don't, the bit patterns that
           correspond to line breaks will be misinterpreted.  On a Windows
           machine in the text mode, the bit pattern 000001010 ('\\n') will
           be written out to the disk as 0000110100001010 ('\\r\\n').

       Version 1.3.1:

           Removed the inconsistency in the internal representation of bit
           vectors produced by logical bitwise operations vis-a-vis the bit
           vectors created by the constructor.  Previously, the logical
           bitwise operations resulted in bit vectors that had their bits
           packed into lists of ints, as opposed to arrays of unsigned
           shorts.

       Version 1.3:

           (a) One more constructor mode included: When initializing a new
           bit vector with an integer value, you can now also specify a
           size for the bit vector.  The constructor zero-pads the bit
           vector from the left with zeros. (b) The BitVector class now
           supports 'if x in y' syntax to test if the bit pattern 'x' is
           contained in the bit pattern 'y'.  (c) Improved syntax to
           conform to well-established Python idioms. (d) What used to be a
           comment before the beginning of each method definition is now a
           docstring.

       Version 1.2:

           (a) One more constructor mode included: You can now construct a
           bit vector directly from a string of 1's and 0's.  (b) The class
           now constructs a shortest possible bit vector from an integer
           value.  So the bit vector for the integer value 0 is just one
           bit of value 0, and so on. (c) All the rich comparison operators
           are now overloaded. (d) The class now includes a new method
           'intValue()' that returns the unsigned integer value of a bit
           vector.  This can also be done through '__int__'. (e) The
           package now includes a unittest based framework for testing out
           an installation.  This is in a separate directory called
           "TestBitVector".
       
       Version 1.1.1:

           The function that does block reads from a disk file now peeks
           ahead at the end of each block to see if there is anything
           remaining to be read in the file.  If nothing remains, the
           more_to_read attribute of the BitVector object is set to False.
           This simplifies reading loops. This version also allows
           BitVectors of size 0 to be constructed


       Version 1.1:

           I have changed the API significantly to provide more ways for
           constructing a bit vector.  As a result, it is now necessary to
           supply a keyword argument to the constructor.
       

    @title
    INSTALLATION:

       The BitVector class was packaged using Distutils.  For installation,
       execute the following command-line in the source directory (this is
       the directory that contains the setup.py file after you have
       downloaded and uncompressed the tar archive):
 
           python setup.py install

       You have to have root privileges for this to work.  On Linux
       distributions, this will install the module file at a location that
       looks like

            /usr/lib/python2.6/site-packages/

       If you do not have root access, you have the option of working
       directly off the directory in which you downloaded the software by
       simply placing the following statements at the top of your scripts
       that use the BitVector class

           import sys
           sys.path.append( "pathname_to_BitVector_directory" )

       To uninstall the module, simply delete the source directory, locate
       where BitVector was installed with "locate BitVector" and delete
       those files.  As mentioned above, the full pathname to the installed
       version is likely to look like
       /usr/lib/python2.6/site-packages/BitVector*

       If you want to carry out a non-standard install of BitVector, look
       up the on-line information on Disutils by pointing your browser to

              http://docs.python.org/dist/dist.html


    @title
    INTRODUCTION:
   
       The BitVector class for a memory-efficient packed representation of
       bit arrays and for logical operations on such arrays.  The core idea
       used in this Python script for bin packing is based on an internet
       posting by Josiah Carlson to the Pyrex mailing list.

       Operations supported on bit vectors:

              __getitem__
              __setitem__
              __len__
              __iter__
              __contains__
              __getslice__
              __str__
              __int__
              __add__
              __eq__, __ne__, __lt__, __le__, __gt__, __ge__
              |            for bitwise or
              &            for bitwise and              
              ^            for bitwise xor
              ~            for bitwise inversion
              <<           for circular rotation to the left
              >>           for circular rotation to the right
              +            for concatenation
              intValue()   for returning the integer value 
              divide_into_two
              permute
              unpermute
              pad_from_left
              pad_from_right
              read_bits_from_file
              write_to_file
              read_bits_from_fileobject
              write_bits_to_fileobject
              reset
              slice assignment
              setValue
              count_bits
              count_bit_sparse          
              jaccard_similarity
              jaccard_distance
              hamming_distance
              next_set_bit
              rank_of_bit_set_at_index
              isPowerOf2
              isPowerOf2_sparse
              reverse
              gcd
              multiplicative_inverse


    @title
    CONSTRUCTING BIT VECTORS:

        You can construct a bit vector in seven different ways.
   
        (1) You can construct a bit vector directly from
            either a tuple or a list of bits, as in

               bv =  BitVector( bitlist = [1,0,1,0,0,1,0,1,0,0,1,0,1,0,0,1] ) 
 
        (2) You can construct a bit vector from an integer by

               bv =  BitVector( intVal = 56789 )

            The bits stored now will correspond to the binary
            representation of the integer.  The resulting bit vector is the
            shortest possible bit vector for the integer value supplied.
            For example, when intVal is 0, the bit vector constructed will
            consist of just the bit 0.


        (3) When initializing a bit vector with an intVal as shown above,
            you can also specify a size for the bit vector:

               bv = BitVector( intVal = 0, size = 8 )

            will return the bit vector consisting of the bit pattern
            00000000.  The zero padding needed for meeting the size
            requirement is always on the left.  If the size supplied is
            smaller than what it takes to create the shortest possible bit
            vector for intVal, an exception is thrown.

                
        (4) You can create a zero-initialized bit vector of a given size by

               bv  = BitVector( size = 62 )

            This bit vector will hold exactly 62 bits, all initialized to
            the 0 bit value.

        (5) You can construct a bit vector from a disk file by a two-step
            procedure. First you construct an instance of bit vector by
   
               bv  =  BitVector( filename = 'somefile' )   

            This bit vector itself is incapable of holding the bits.  To
            now create bit vectors that actually hold the bits, you need to
            make the following sort of a call on the above variable bv:
 
               bv1 =  bv.read_bits_from_file( 64 )    

            bv1 will be a regular bit vector containing 64 bits from the
            disk file. If you want to re-read a file from the beginning for
            some reason, you must obviously first close the file object
            that was acquired with a call to the BitVector constructor with
            a filename argument.  This can be accomplished by

              bv.close_file_object()

        (6) You can construct a bit vector from a string of 1's and 0's by
 
               bv  =  BitVector( bitstring = '110011110000' )      
   
        (7) Yet another way to construct a bit vector is to read the bits
            directly from a file-like object, as in
  
               x = "111100001111"
               fileobj = StringIO.StringIO( x )
               bv = BitVector( fp = fileobj )


    @title   
    OPERATIONS SUPPORTED BY THE BITVECTOR CLASS:
    
    @title
    DISPLAYING BIT VECTORS:


        1) Since the BitVector class implements the __str__ method, a bit
           vector can be displayed on a terminal by

                  print bitvec

           Basically, you can always obtain the string representation of a
           bit vector by

                  str( bitvec )

           and integer value by

                  int( bitvec )


    @title
    ACCESSING AND SETTING INDIVIDUAL BITS AND SLICES:

   
        2) Any single bit of a bit vector bv can be set to 1 or 0 by
 
                  bv[M] = 1_or_0
                  print bv[M]

           for accessing (and setting) the bit at the position that is
           indexed M.  You can retrieve the bit at position M by bv[M].
           Note that the index 0 corresponds to the first bit at the left
           end of a bit pattern.

        3) A slice of a bit vector obtained by

                  bv[i:j]

            is a bit vector constructed from the bits at index positions
            from i through j-1.

        4) You can also carry out slice assignment:

                  bv1 = BitVector( size = 25 )
                  bv2 = BitVector( bitstring = '1010001' )
                  bv1[6:9]  = bv2[0:3]
                  bv3 = BitVector( bitstring = '101' )                 
                  bv1[0:3]  = bv3

           The first slice assignment will set the 6th, 7th, and the 8th
           bits of the bit vector bv1 according to the first three bits of
           bv2.  The second slice assignment will set the first three bits
           of bv1 according to the three bits in bv3.

        5) You can iterate over a bit vector, as illustrated by

                  for bit in bitvec:
                      print bit,   

           This is made possible by the override definition for the special
           __iter__() method.

        6) Negative subscripts for array-like indexing are supported.
           Therefore,

                  bitvec[ -i ]

           is legal assuming that the index range is not violated.  A
           negative index carries the usual Python interpretation: The last
           element of a bit vector is indexed -1 and the first element
           -(n+1) if n is the total number of bits in the bit vector.

        7) You can reset a previously constructed bit vector to either the
           all-zeros state or the all-ones state by

                  bv1 = BitVector( size = 25 )
                  ...
                  ...
                  bv1.reset( 1 )
                  ...
                  ...
                  bv1.reset( 0 )

           The first call to reset() will set all the bits of bv1 to 1's
           and the second call all the bits to 0's.


    @title
    LOGICAL OPERATIONS ON BIT VECTORS:

   
        8) Given two bit vectors bv1 and bv2, you can perform bitwise
           logical operations on them by

                  result_bv  =  bv1 ^ bv2           # for bitwise XOR
                  result_bv  =  bv1 & bv2           # for bitwise AND
                  result_bv  =  bv1 | bv2           # for bitwise OR
                  result_bv  =  ~bv1                # for bitwise negation


    @title
    COMPARING BIT VECTORS:

        9) Given two bit vectors bv1 and bv2, you can carry out the
           following comparisons that return Boolean values:

                  bv1 ==  bv2
                  bv1 !=  bv2
                  bv1 <   bv2
                  bv1 <=  bv2
                  bv1 >   bv2
                  bv1 >=  bv2

           The equalities and inequalities are determined by the integer
           values associated with the bit vectors.

   
    @title
    OTHER SUPPORTED OPERATIONS:

   
       10) You can permute and unpermute bit vectors:

                  bv_permuted   =  bv.permute( permutation_list )

                  bv_unpermuted =  bv.unpermute( permutation_list )


       11) Left and right circular rotations can be carried out by
 
                  bitvec  << N 

                  bitvec  >> N

           for circular rotations to the left and to the right by N bit
           positions.


       12) A bit vector containing an even number of bits can be divided
           into two equal parts by

                  [left_half, right_half] = bitvec.divide_into_two()

           where left_half and right_half hold references to the two
           returned bit vectors.


       13) You can find the integer value of a bit array by

                  bitvec.intValue()

           or by

                  int( bitvec )


       14) You can convert a bit vector into its string representation by

                  str( bitvec )


       15) Because __add__ is supplied, you can always join two bit vectors
           by

                  bitvec3  =  bitvec1  +  bitvec2

           bitvec3 is a new bit vector that contains all the bits of
           bitvec1 followed by all the bits of bitvec2.

             
       16) You can write a bit vector directly to a file, as illustrated by
           the following example that reads one bit vector from a file and
           then writes it to another file

                  bv = BitVector( filename = 'input.txt' )
                  bv1 = bv.read_bits_from_file(64)        
                  print bv1           
                  FILEOUT = open( 'output.bits', 'wb' )
                  bv1.write_to_file( FILEOUT )
                  FILEOUT.close()
                  bv = BitVector( filename = 'output.bits' )
                  bv2 = bv.read_bits_from_file( 64 )
                  print bv2

             IMPORTANT: The size of a bit vector must be a multiple of of 8
                         for this write function to work.  If this
                         condition is not met, the function will throw an
                         exception.

             IMPORTANT FOR WINDOWS USERS: When writing an internally
                         generated bit vector out to a disk file, it is
                         important to open the file in the binary mode as
                         shown.  Otherwise, the bit pattern 00001010
                         ('\\n') in your bitstring will be written out as
                         0000110100001010 ('\\r\\n'), which is the
                         linebreak on Windows machines.

       17) You can also write a bit vector directly to a stream object, as
           illustrated by

                  fp_write = StringIO.StringIO()
                  bitvec.write_bits_to_fileobject( fp_write )
                  print fp_write.getvalue()         # 111100001111 
             

       18) You can pad a bit vector from the left or from the right with a
           designated number of zeros

                  bitvec.pad_from_left( n )

                  bitvec.pad_from_right( n )

           In the first case, the new bit vector will be the same as the
           old bit vector except for the additional n zeros on the left.
           The same thing happens in the second case except that now the
           additional n zeros will be on the right.

       19) You can test if a bit vector x is contained in another bit
           vector y by using the syntax 'if x in y'.  This is made possible
           by the override definition for the special __contains__()
           method.

       20) You can change the bit pattern associated with a previously
           constructed BitVector instance:

              bv = BitVector( intVal = 7, size =16 )
              print bv                              # 0000000000000111
              bv.setValue( intVal = 45 )
              print bv                              # 101101

       21) You can count the number of bits set in a BitVector instance by

              bv = BitVector( bitstring = '100111' )
              print bv.count_bits()                     # 4


       22) For folks who use bit vectors with millions of bits in them but
           with only a few bits set, your bit counting will go much, much
           faster if you call count_bits_sparse() instead of count_bits():

              # a BitVector with 2 million bits:
              bv = BitVector( size = 2000000 )
              bv[345234] = 1
              bv[233]=1
              bv[243]=1
              bv[18]=1
              bv[785] =1
              print bv.count_bits_sparse()
              
       23) You can calculate the similarity and the distance between two
           bit vectors using the Jaccard similarity coefficient and the
           Jaccard distance.  Also, you can calculate the Hamming distance
           between two bit vectors:

              bv1 = BitVector( bitstring = '11111111' )
              bv2 = BitVector( bitstring = '00101011' )
              print bv1.jaccard_similarity( bv2 )
              print bv1.jaccard_distance( bv2 )
              print bv1.hamming_distance( bv2 )

       24) Starting from a given bit position, you can find the position
           index of the next set bit:

              bv = BitVector( bitstring = '00000000000001' )
              print bv.next_set_bit( 5 ) 

       25) You can measure the "rank" of a bit that is set at a given
           position.  Rank is the number of bits that are set up to the
           position of the bit you are interested in.

              bv = BitVector( bitstring = '01010101011100' )
              print bv.rank_of_bit_set_at_index( 10 )            # 6

       26) You can test whether the integer value of a bit vector is a
           power of two.  The sparse version of this method will work much
           faster for very long bit vectors.  However, the regular version
           may work faster for small bit vectors.

              bv = BitVector( bitstring = '10000000001110' )
              print bv.isPowerOf2()
              print bv.isPowerOf2_sparse()

       27) Given a bit vector, you can construct a bit vector with all the
           bits reversed, in the sense that what was left to right before
           now becomes right to left.

              bv = BitVector( bitstring = '0001100000000000001' )
              print bv.reverse()

       28) You can find the greatest common divisor of two bit vectors:

              bv1 = BitVector( bitstring = '01100110' )
              bv2 = BitVector( bitstring = '011' ) 
              bv = bv1.gcd( bv2 )
              print int(bv)

       29) You can find the multiplicative inverse of a bit vector
           vis-a-vis a given modulus:

              bv_modulus = BitVector( intVal = 32 )
              bv = BitVector( intVal = 17 ) 
              bv_result = bv.multiplicative_inverse( bv_modulus )
              if bv_result is not None:
                  print int(bv_result)
              else: print "No multiplicative inverse in this case"


    @title
    HOW THE BIT VECTORS ARE STORED:
   
        The bits of a bit array are stored in 16-bit unsigned ints.  After
        resolving the argument with which the constructor is called (which
        happens in lines (A2) through (A70) of the file BitVector.py), the
        very first thing that the constructor does is to figure out in line
        (A78) as to how many of those 2-byte ints it needs for the bits.
        For example, if you wanted to store a 64-bit array, the variable
        'two_byte_ints_needed' in line (A78) would be set to 4. (This does
        not mean that the size of a bit vector must be a multiple of 16.
        Any sized bit vectors can constructed using the required number of
        two-byte ints.) Line (A79) then creates an array of 2-byte ints and
        initializes it with the required number of zeros.  Lines (A80) then
        shifts the bits into the array of two-byte ints.

        As mentioned above, note that it is not necessary for the size of
        the vector to be a multiple of 16 even though we are using C's
        unsigned short as as a basic unit for storing the bit arrays.  The
        class BitVector keeps track of the actual number of bits in the bit
        vector through the "size" instance attribute.

        With regard to the code in lines (A2) through (A77) of the file
        BitVector.py, note that, except for one case, the constructor must
        be called with a single keyword argument, which determines how the
        bit vector will be constructed.  The single exception to this rule
        is for the keyword argument 'intVal' which can be used along with
        the 'size' keyword argument.  When 'intVal' is used with the 'size'
        option, the bit vector constructed for the integer is the shortest
        possible bit vector.  On the other hand, when 'size' is also
        specified, the bit vector is padded with zeroes from the left so
        that it has the specified size.

        Lines (A16) through (A22) are for the following sort of a call

               bv = BitVector( filename = 'myfilename' )

        This call returns a bit vector on which you must subsequently
        invoke the 'read_bits_from_file()' method to actually obtain a bit
        vector consisting of the bits that constitute the information
        stored in the file.

        Lines (A23) through (A28) are for the case when you want to
        construct a bit vector by reading the bits off a file-like object,
        as in

              x = "111100001111"
              fileobj = StringIO.StringIO( x )
              bv = BitVector( fp = fileobj )

        Lines (A29) through (A61) are for the case when you want to
        construct a bit vector from an integer, as in

              bv = BitVector( intVal = 123456 )

        The bits stored in the bit vector will correspond to the binary
        representation of the integer argument provided.  The bit vector
        constructed with the above call will be the shortest possible bit
        vector for the integer supplied.  As a case in point, when the
        intVal is 0, the bit vector will consist of a single bit which will
        be 0 also.  The code in lines (A29) through (A61) can also handle
        the following sort of a call

              bv = BitVector( intVal = 46, size = 16 )        

        which returns a bit vector of a specific size by padding the
        shortest possible bit vector the the intVal with zeros from the
        left.
        
        Lines (A62) through (A68) are for constructing a bit vector with
        just the size information, as in

              bv = BitVector( size = 61 )

        This returns a bit vector that will hold exactly 61 bits, all
        initialized to the zero value.

        Lines (A69) through (A73) are for constructing a bit vector from a
        bitstring, as in

              bv = BitVector( bitstring = '00110011111' )

        Finally, lines (A74) through (A77) are for constructing a bit
        vector from a list or a tuple of the individual bits:
          
              bv = BitVector( bitlist = (1, 0, 1, 1, 0, 0, 1) )

        The bit vector constructed is initialized with the supplied bits.

   
    @title
    ACKNOWLEDGMENTS:

        The author is grateful to Oleg Broytmann for suggesting many
        improvements that were incorporated in Version 1.1 of this package.
        The author would like to thank Kurt Schwehr whose email resulted in
        the creation of Version 1.2.  Kurt also caught an error in my
        earlier version of 'setup.py' and suggested a unittest based
        approach to the testing of the package.  Kurt also supplied the
        Makefile that is included in this distribution.  The author would
        also like to thank all (Scott Daniels, Blair Houghton, and Steven
        D'Aprano) for their responses to my comp.lang.python query
        concerning how to make a Python input stream peekable.  This
        feature was included in Version 1.1.1.

        With regard to the changes incorporated in Version 1.3, thanks are
        owed to Kurt Schwehr and Gabriel Ricardo for bringing to my
        attention the bug related to the intVal method of initializing a
        bit vector when the value of intVal exceeded sys.maxint. This
        problem is fixed in Version 1.3.  Version 1.3 also includes many
        other improvements that make the syntax better conform to the
        standard idioms of Python.  These changes and the addition of the
        new constructor mode (that allows a bit vector of a given size to
        be constructed from an integer value) are also owing to Kurt's
        suggestions.

        With regard to the changes incorporated in Version 1.3.1, I would
        like to thank Michael Haggerty for noticing that the bitwise
        logical operators resulted in bit vectors that had their bits
        packed into lists of ints, as opposed to arrays of unsigned shorts.
        This inconsistency in representation has been removed in version
        1.3.1.  Michael has also suggested that since BitVector is mutable,
        I should be overloading __iand__(), __ior__(), etc., for in-place
        modifications of bit vectors.  Michael certainly makes a good
        point. But I am afraid that this change will break the code for the
        existing users of the BitVector class.

        I thank Mathieu Roy for bringing to my attention the problem with
        writing bitstrings out to a disk files on Windows machines.  This
        turned out to be a problem more with the documentation than with
        the BitVector class itself.  On a Windows machine, it is
        particularly important that a file you are writing a bitstring into
        be opened in binary mode since otherwise the bit pattern 00001010
        ('\\n') will be written out as 0000110100001010 ('\\r\\n').  This
        documentation fix resulted in Version 1.3.2.

        With regard to Version 1.4, the suggestions/bug reports made by
        John Kominek, Bob Morse, and Steve Ward contributed to this
        version.  I wish to thank all three. John wanted me to equip the
        class with a reset() method so that a previously constructed class
        could be reset to either all 0's or all 1's. Bob spotted loose
        local variables in the implementation --- presumably left over from
        a debugging phase of the code.  Bob recommended that I clean up the
        code with pychecker. That has been done.  Steve noticed that slice
        assignment was not working.  It should work now.

        Version 1.4.1 was prompted by John Kominek suggesting that if
        reset() returned self, then the slice operation could be combined
        with the reset operation.  Thanks John!  Another reason for 1.4.1
        was to remove the discrepancy between the value of the
        __copyright__ variable in the module and the value of license
        variable in setup.py.  This discrepancy was brought to my attention
        by David Eyk.  Thanks David!

        Version 1.5 has benefited greatly by the suggestions made by Ryan
        Cox.  By examining the BitVector execution with cProfile, Ryan
        observed that my implementation was making unnecessary method calls
        to _setbit() when just the size option is used for constructing a
        BitVector instance.  Since Python allocates cleaned up memory, it
        is unnecessary to set the individual bits of a vector if it is
        known in advance that they are all zero. Ryan made a similar
        observation for the logical operations applied to two BitVector
        instances of equal length.  He noticed that I was making
        unnecessary calls to _resize_pad_from_left() for the case of equal
        arguments to logical operations.  Ryan also recommended that I
        include a method that returns the total number of bits set in a
        BitVector instance.  The new method count_bits() does exactly
        that. Thanks Ryan for all your suggestions.  Version 1.5 also
        includes the method setValue() that allows the internally stored
        bit pattern associated with a previously constructed BitVector to
        be changed.  A need for this method was expressed by Aleix
        Conchillo.  Thanks Aleix.
        
        Version 1.5.1 is a quick release to fix a bug in the right circular
        shift operator.  This bug was discovered by Jasper Spaans.  Thanks
        very much Jasper.

        Version 2.0 was prompted mostly by the needs of the folks who play
        with very long bit vectors that may contain of millions of bits.  I
        believe such bit vectors are encountered in data mining research
        and development.  Towards that end, among the new methods in
        Version 2, the count_bits_sparse() was provided by Rhiannon Weaver.
        She says when a bit vector contains over 2 million bits and only,
        say, five bits are set, her method is faster than the older
        count_bits() method by a factor of roughly 18.  Thanks
        Rhiannon. [The logic of the new implementation works best for very
        sparse bit vectors.  For very dense vectors, it may perform more
        slowly than the regular count_bits() method.  For that reason, I
        have retained the original method.]  Rhiannon's implementation is
        based on what has been called the Kernighan way at the web site
        http://graphics.stanford.edu/~seander/bithacks.html.  Version 2
        also includes a few additional functions posted at this web site
        for extracting information from bit fields.  Also included in this
        new version is the next_set_bit() method supplied by Jason Allum.
        I believe this method is also useful for data mining folks.  Thanks
        Jason.  Additional methods in Version 2 include the similarity and
        the distance metrics for comparing two bit vectors, method for
        finding the greatest common divisor of two bit vectors, and a
        method that determines the multiplicative inverse of a bit vector
        vis-a-vis a modulus.  The last two methods should prove useful to
        folks in cryptography.
        

    @title
    ABOUT THE AUTHOR:

        Avi Kak is the author of "Programming with Objects: A Comparative
        Presentation of Object-Oriented Programming with C++ and Java",
        published by John-Wiley in 2003. This book presents a new approach
        to the combined learning of two large object-oriented languages,
        C++ and Java.  It is being used as a text in a number of
        educational programs around the world.  This book has also been
        translated into Chinese.  Avi Kak is also the author of "Scripting
        with Objects: A Comparative Presentation of Object-Oriented
        Scripting with Perl and Python," published in 2008 by John-Wiley.


    @title
    SOME EXAMPLE CODE:

        #!/usr/bin/env python
        import BitVector

        # Construct a bit vector from a list or tuple of bits:
        bv = BitVector.BitVector( bitlist = (1, 0, 0, 1) )
        print bv                                # 1001

        # Construct a bit vector from an integer:
        bv = BitVector.BitVector( intVal = 5678 )
        print bv                                # 0001011000101110

        # Construct a bit vector of a given size from a given
        # integer:
        bv = BitVector( intVal = 45, size = 16 )
        print bv                                # 0000000000101101

        # Construct a zero-initialized bit vector of a given size:
        bv = BitVector.BitVector( size = 5 )
        print bv                                # 00000

        # Construct a bit vector from a bit string:
        bv = BitVector.BitVector( bitstring = '110001' )     
        print bv[0], bv[1], bv[2], bv[3], bv[4], bv[5]       # 1 1 0 0 0 1
        print bv[-1], bv[-2], bv[-3], bv[-4], bv[-5], bv[-6] # 1 0 0 0 1 1

        # Construct a bit vector from a file like object:
        import StringIO
        x = "111100001111"
        fp_read = StringIO.StringIO( x )
        bv = BitVector.BitVector( fp = fp_read )
        print bv                                    # 111100001111 

        # Experiments with bitwise logical operations:
        bv3 = bv1 | bv2                              
        bv3 = bv1 & bv2
        bv3 = bv1 ^ bv2
        bv6 = ~bv5

        # Find the length of a bit vector
        print len( bitvec )

        # Find the integer value of a bit vector
        print int( bitvec )

        # Open a file for reading bit vectors from
        bv = BitVector.BitVector( filename = 'TestBitVector/testinput1.txt' )
        print bv                                    # nothing yet
        bv1 = bv.read_bits_from_file(64)    
        print bv1                            # first 64 bits from the file

        # Divide a bit vector into two equal sub-vectors:
        [bv1, bv2] = bitvec.divide_into_two()

        # Permute and Un-Permute a bit vector:
        bv2 = bitvec.permute( permutation_list )
        bv2 = bitvec.unpermute( permutation_list )

        # Try circular shifts to the left and to the right
        bitvec << 7
        bitvec >> 7

        # Try 'if x in y' syntax for bit vectors:
        bv1 = BitVector( bitstring = '0011001100' )
        bv2 = BitVector( bitstring = '110011' )
        if bv2 in bv1:
            print "%s is in %s" % (bv2, bv1)
        else:
            print "%s is not in %s" % (bv2, bv1)

        .....
        .....

        (For a more complete working example, see the
         example code in the BitVectorDemo.py file in the
         Examples sub-directory.)

'''


import array
import operator

_hexdict = { '0' : '0000', '1' : '0001', '2' : '0010', '3' : '0011',
             '4' : '0100', '5' : '0101', '6' : '0110', '7' : '0111',
             '8' : '1000', '9' : '1001', 'a' : '1010', 'b' : '1011',
             'c' : '1100', 'd' : '1101', 'e' : '1110', 'f' : '1111' }

def _readblock( blocksize, bitvector ):                              #(R1)
    ''' 
    If this function can read all blocksize bits, it peeks ahead to see
    if there is anything more to be read in the file. It uses
    tell-read-seek mechanism for this in lines (R18) through (R21).  If
    there is nothing further to be read, it sets the more_to_read attribute
    of the bitvector object to False.  Obviously, this can only be done for
    seekable streams such as those connected with disk files.  According to
    Blair Houghton, a similar feature could presumably be implemented for
    socket streams by using recv() or recvfrom() if you set the flags
    argument to MSG_PEEK.
    '''
    global hexdict                                                   #(R2)
    bitstring = ''                                                   #(R3)
    i = 0                                                            #(R4)
    while ( i < blocksize / 8 ):                                     #(R5)
        i += 1                                                       #(R6)
        byte = bitvector.FILEIN.read(1)                              #(R7)
        if byte == '':                                               #(R8)
            if len(bitstring) < blocksize:                           #(R9)
                bitvector.more_to_read = False                      #(R10)
            return bitstring                                        #(R11)
        hexvalue = hex( ord( byte ) )                               #(R12)
        hexvalue = hexvalue[2:]                                     #(R13)
        if len( hexvalue ) == 1:                                    #(R14)
            hexvalue = '0' + hexvalue                               #(R15)
        bitstring += _hexdict[ hexvalue[0] ]                        #(R16)
        bitstring += _hexdict[ hexvalue[1] ]                        #(R17)
    file_pos = bitvector.FILEIN.tell()                              #(R18)
    # peek at the next byte; moves file position only if a
    # byte is read
    next_byte = bitvector.FILEIN.read(1)                            #(R19)
    if next_byte:                                                   #(R20)
        # pretend we never read the byte                   
        bitvector.FILEIN.seek( file_pos )                           #(R21)
    else:                                                           #(R22)
        bitvector.more_to_read = False                              #(R23)
    return bitstring                                                #(R24)


#--------------------  BitVector Class Definition   ----------------------

class BitVector( object ):                                           #(A1)

    def __init__( self, *args, **kwargs ):                           #(A2)
        if args:                                                     #(A3)
               raise ValueError(                                     #(A4)
                      '''BitVector constructor can only be called with
                         keyword arguments for the following keywords:
                         filename, fp (for fileobject), size, intValue,
                         bitlist (for a list or tuple of bits, or
                         bitstring)''')
        filename = fp = intVal = size = bitlist = bitstring = None   #(A5)
        if kwargs.has_key('filename'):filename=kwargs.pop('filename')#(A6)
        if kwargs.has_key('fp'):           fp = kwargs.pop('fp')     #(A7)
        if kwargs.has_key('size'):       size = kwargs.pop('size')   #(A8)
        if kwargs.has_key('intVal'):   intVal = kwargs.pop('intVal') #(A9)
        if kwargs.has_key('bitlist'):
                               bitlist = kwargs.pop('bitlist')      #(A10)
        if kwargs.has_key('bitstring') :
                               bitstring = kwargs.pop('bitstring')  #(A11)
        self.filename = None                                        #(A12)
        self.size = 0                                               #(A13)
        self.FILEIN = None                                          #(A14)
        self.FILEOUT = None                                         #(A15)
        
        if filename:                                                #(A16)
            if fp or size or intVal or bitlist or bitstring:        #(A17)
                raise ValueError(                                   #(A18)
                  '''When filename is specified, you cannot
                     give values to any other constructor args''')
            self.filename = filename                                #(A19)
            self.FILEIN = open( filename, 'rb' )                    #(A20)
            self.more_to_read = True                                #(A21)
            return                                                  #(A22)
        elif fp:                                                    #(A23)
            if filename or size or intVal or bitlist or bitstring:  #(A24)
                raise ValueError(                                   #(A25)
                  '''When fileobject is specified, you cannot      
                     give values to any other constructor args''')
            bits = self.read_bits_from_fileobject( fp )             #(A26)
            bitlist =  map( int, bits )                             #(A27)
            self.size = len( bitlist )                              #(A28)
        elif intVal or intVal == 0:                                 #(A29)
            if filename or fp or bitlist or bitstring:              #(A30)
                raise ValueError(                                   #(A31)
                  '''When intVal is specified, you can only give
                     a value to the 'size' constructor arg''')
            if intVal == 0:                                         #(A32)
                bitlist = [0]                                       #(A33)
                if not size:                                        #(A34)
                    self.size = 1                                   #(A35)
                else:                                               #(A36)
                    if size < len(bitlist):                         #(A37)
                        raise ValueError(                           #(A38)
                          '''The value specified for size must be at least
                             as large as for the smallest bit vector
                             possible for intVal''')
                    n = size - len(bitlist)                         #(A39)
                    bitlist = [0]*n + bitlist                       #(A40)
                    self.size = len( bitlist )                      #(A41)
            else:                                                   #(A42)
                hexVal = hex( intVal ).lower().rstrip('l')          #(A43)
                hexVal = hexVal[2:]                                 #(A44)
                if len( hexVal ) == 1:                              #(A45)
                    hexVal = '0' + hexVal                           #(A46)
                bitlist = ''.join(map(lambda x: _hexdict[x],hexVal))#(A47)
                bitlist =  map( int, bitlist )                      #(A48)
                i = 0                                               #(A49)
                while ( i < len( bitlist ) ):                       #(A50)
                    if bitlist[i] == 1: break                       #(A51)
                    i += 1                                          #(A52)
                del bitlist[0:i]                                    #(A53)
                if not size:                                        #(A54)
                    self.size = len( bitlist )                      #(A55)
                else:                                               #(A56)
                    if size < len(bitlist):                         #(A57)
                        raise ValueError(                           #(A58)
                          '''The value specified for size must be at least
                             as large as for the smallest bit vector
                             possible for intVal''')
                    n = size - len(bitlist)                         #(A59)
                    bitlist = [0]*n + bitlist                       #(A60)
                    self.size = len( bitlist )                      #(A61)
        elif size >= 0:                                             #(A62)
            if filename or fp or intVal or bitlist or bitstring:    #(A63)
                raise ValueError(                                   #(A64)
                  '''When size is specified (without an intVal), you cannot
                     give values to any other constructor args''')
            self.size = size                                        #(A65)
            two_byte_ints_needed = (size + 15) // 16                #(A66)
            self.vector = array.array('H', [0]*two_byte_ints_needed)#(A67)
            return                                                  #(A68)
        elif bitstring or bitstring == '':                          #(A69)
            if filename or fp or size or intVal or bitlist:         #(A70)
                raise ValueError(                                   #(A71)
                  '''When a bitstring is specified, you cannot
                     give values to any other constructor args''')
            bitlist =  map( int, list(bitstring) )                  #(A72)
            self.size = len( bitlist )                              #(A73)
        elif bitlist:                                               #(A74)
            if filename or fp or size or intVal or bitstring:       #(A75)
                raise ValueError(                                   #(A76)
                  '''When bits are specified, you cannot give values to any
                     other constructor args''')
            self.size = len( bitlist )                              #(A77)
        else:                                                       #(A78)
            raise ValueError("wrong arg(s) for constructor")        #(A79) 
        two_byte_ints_needed = (len(bitlist) + 15) // 16            #(A80)
        self.vector = array.array( 'H', [0]*two_byte_ints_needed )  #(A81)
        map( self._setbit, enumerate(bitlist), bitlist)             #(A82)


    def _setbit( self, posn, val ):                                  #(B1)
        'Set the bit at the designated position to the value shown'
        if val not in (0, 1):                                        #(B2)
            raise ValueError( "incorrect value for a bit" )          #(B3)
        if isinstance( posn, (tuple) ):                              #(B4)
            posn = posn[0]                                           #(B5)
        if  posn >= self.size or posn < -self.size:                  #(B6)
            raise ValueError( "index range error" )                  #(B7)   
        if posn < 0: posn = self.size + posn                         #(B8)
        block_index = posn // 16                                     #(B9)
        shift = posn & 15                                           #(B10)
        cv = self.vector[block_index]                               #(B11)
        if ( cv >> shift ) & 1 != val:                              #(B12)
            self.vector[block_index] = cv ^ (1 << shift)            #(B13)


    def _getbit( self, posn ):                                       #(C1)
        'Get the bit from the designated position'
        if  posn >= self.size or posn < -self.size:                  #(C2)
            raise ValueError( "index range error" )                  #(C3)   
        if posn < 0: posn = self.size + posn                         #(C4)
        return ( self.vector[posn//16] >> (posn&15) ) & 1            #(C5)


    def __xor__(self, other):                                        #(E1)
        '''
        Take a bitwise 'xor' of the bit vector on which the method is
        invoked with the argument bit vector.  Return the result as a new
        bit vector.  If the two bit vectors are not of the same size, pad
        the shorter one with zeros from the left.
        '''
        if self.size < other.size:                                   #(E2)
            bv1 = self._resize_pad_from_left(other.size - self.size) #(E3)
            bv2 = other                                              #(E4)
        elif self.size > other.size:                                 #(E5)
            bv1 = self                                               #(E6)
            bv2 = other._resize_pad_from_left(self.size - other.size)#(E7)
        else:                                                        #(E8)
            bv1 = self                                               #(E9)
            bv2 = other                                             #(E10)
        res = BitVector( size = bv1.size )                          #(E11)
        lpb = map(operator.__xor__, bv1.vector, bv2.vector)         #(E12) 
        res.vector = array.array( 'H', lpb )                        #(E13)
        return res                                                  #(E14)


    def __and__(self, other):                                        #(F1)
        '''
        Take a bitwise 'and' of the bit vector on which the method is
        invoked with the argument bit vector.  Return the result as a new
        bit vector.  If the two bit vectors are not of the same size, pad
        the shorter one with zeros from the left.
        '''      
        if self.size < other.size:                                   #(F2)
            bv1 = self._resize_pad_from_left(other.size - self.size) #(F3)
            bv2 = other                                              #(F4)
        elif self.size > other.size:                                 #(F5)
            bv1 = self                                               #(F6)
            bv2 = other._resize_pad_from_left(self.size - other.size)#(F7)
        else:                                                        #(F8)
            bv1 = self                                               #(F9)
            bv2 = other                                             #(F10)
        res = BitVector( size = bv1.size )                          #(F11)
        lpb = map(operator.__and__, bv1.vector, bv2.vector)         #(F12) 
        res.vector = array.array( 'H', lpb )                        #(F13)
        return res                                                  #(F14)


    def __or__(self, other):                                         #(G1)
        '''
        Take a bitwise 'or' of the bit vector on which the method is
        invoked with the argument bit vector.  Return the result as a new
        bit vector.  If the two bit vectors are not of the same size, pad
        the shorter one with zero's from the left.
        '''
        if self.size < other.size:                                   #(G2)
            bv1 = self._resize_pad_from_left(other.size - self.size) #(G3)
            bv2 = other                                              #(G4)
        elif self.size > other.size:                                 #(G5)
            bv1 = self                                               #(G6)
            bv2 = other._resize_pad_from_left(self.size - other.size)#(G7)
        else:                                                        #(G8)
            bv1 = self                                               #(G9)
            bv2 = other                                             #(G10)
        res = BitVector( size = bv1.size )                          #(G11)
        lpb = map(operator.__or__, bv1.vector, bv2.vector)          #(G12) 
        res.vector = array.array( 'H', lpb )                        #(G13)
        return res                                                  #(G14)


    def __invert__(self):                                            #(H1)
        '''
        Invert the bits in the bit vector on which the method is invoked
        and return the result as a new bit vector.
        '''
        res = BitVector( size = self.size )                          #(H2)
        lpb = map( operator.__inv__, self.vector )                   #(H3) 
        res.vector = array.array( 'H' )                              #(H3)
        for i in range(len(lpb)):                                    #(H4)
            res.vector.append( lpb[i] & 0x0000FFFF )                 #(H5)
        return res                                                   #(H6)


    def __add__(self, other):                                        #(J1)
        '''
        Concatenate the argument bit vector with the bit vector on which
        the method is invoked.  Return the concatenated bit vector as a new
        BitVector object.
        '''
        i = 0                                                        #(J2)
        outlist = []                                                 #(J3)
        while ( i < self.size ):                                     #(J4)
            outlist.append( self[i] )                                #(J5)
            i += 1                                                   #(J6)
        i = 0                                                        #(J7)
        while ( i < other.size ):                                    #(J8)
            outlist.append( other[i] )                               #(J9)
            i += 1                                                  #(J10)
        return BitVector( bitlist = outlist )                       #(J11)


    def _getsize(self):                                              #(K1)
        'Return the number of bits in a bit vector.'
        return self.size                                             #(K2)


    def read_bits_from_file(self, blocksize):                        #(L1)
        '''
        Read blocksize bits from a disk file and return a BitVector object
        containing the bits.  If the file contains fewer bits than
        blocksize, construct the BitVector object from however many bits
        there are in the file.  If the file contains zero bits, return a
        BitVector object of size attribute set to 0.
        '''
        error_str = '''You need to first construct a BitVector
        object with a filename as  argument'''                       #(L2)
        if not self.filename:                                        #(L3)
            raise SyntaxError( error_str )                           #(L4)
        if blocksize % 8 != 0:                                       #(L5)
            raise ValueError( "block size must be a multiple of 8" ) #(L6)
        bitstr = _readblock( blocksize, self )                       #(L7)
        if len( bitstr ) == 0:                                       #(L8)
            return BitVector( size = 0 )                             #(L9)
        else:                                                       #(L10)
            return BitVector( bitstring = bitstr )                  #(L11)



    def read_bits_from_fileobject( self, fp ):                       #(M1)
        '''
        This function is meant to read a bit string from a file like
        object.
        '''
        bitlist = []                                                 #(M2)
        while 1:                                                     #(M3)
            bit = fp.read()                                          #(M4)
            if bit == '': return bitlist                             #(M5)
            bitlist += bit                                           #(M6)


    def write_bits_to_fileobject( self, fp ):                        #(N1)
        '''
        This function is meant to write a bit vector directly to a file
        like object.  Note that whereas 'write_to_file' method creates a
        memory footprint that corresponds exactly to the bit vector, the
        'write_bits_to_fileobject' actually writes out the 1's and 0's as
        individual items to the file object.  That makes this method
        convenient for creating a string representation of a bit vector,
        especially if you use the StringIO class, as shown in the test
        code.
        '''
        for bit_index in range(self.size):                           #(N2)
            if self[bit_index] == 0:                                 #(N3)
                fp.write( '0' )                                      #(N4)
            else:                                                    #(N5)
                fp.write( '1' )                                      #(N6)


    def divide_into_two(self):                                       #(P1)
        '''
        Divides an even-sized bit vector into two and returns the two
        halves as a list of two bit vectors.
        '''
        if self.size % 2 != 0:                                       #(P2)
            raise ValueError( "must have even num bits" )            #(P3)
        i = 0                                                        #(P4)
        outlist1 = []                                                #(P5)
        while ( i < self.size /2 ):                                  #(P6)
            outlist1.append( self[i] )                               #(P7)
            i += 1                                                   #(P8)
        outlist2 = []                                                #(P9)
        while ( i < self.size ):                                    #(P10)
            outlist2.append( self[i] )                              #(P11)
            i += 1                                                  #(P12)
        return [ BitVector( bitlist = outlist1 ),
                 BitVector( bitlist = outlist2 ) ]                  #(P13)


    def permute(self, permute_list):                                 #(Q1)
        '''
        Permute a bit vector according to the indices shown in the second
        argument list.  Return the permuted bit vector as a new bit vector.
        '''
        if max(permute_list) > self.size -1:                         #(Q2)
            raise ValueError( "Bad permutation index" )              #(Q3)
        outlist = []                                                 #(Q4)
        i = 0                                                        #(Q5)
        while ( i < len( permute_list ) ):                           #(Q6)
            outlist.append( self[ permute_list[i] ] )                #(Q7)
            i += 1                                                   #(Q8)
        return BitVector( bitlist = outlist )                        #(Q9)


    def unpermute(self, permute_list):                               #(S1)
        '''
        Unpermute the bit vector according to the permutation list supplied
        as the second argument.  If you first permute a bit vector by using
        permute() and then unpermute() it using the same permutation list,
        you will get back the original bit vector.
        '''
        if max(permute_list) > self.size -1:                         #(S2)
            raise ValueError( "Bad permutation index" )              #(S3)
        if self.size != len( permute_list ):                         #(S4)
            raise ValueError( "Bad size for permute list" )          #(S5)
        out_bv = BitVector( size = self.size )                       #(S6)
        i = 0                                                        #(S7)
        while ( i < len(permute_list) ):                             #(S8)
            out_bv[ permute_list[i] ] = self[i]                      #(S9)
            i += 1                                                  #(S10)
        return out_bv                                               #(S11)


    def write_to_file(self, file_out):                               #(T1)
        '''
        (Contributed by Joe Davidson) Write the bitvector to the file
        object file_out.  (A file object is returned by a call to
        open()). Since all file I/O is byte oriented, the bitvector must be
        multiple of 8 bits. Each byte treated as MSB first (0th index).
        '''
        err_str = '''Only a bit vector whose length is a multiple of 8 can
            be written to a file.  Use the padding functions to satisfy
            this constraint.'''                                      #(T2)
        if not self.FILEOUT: 
            self.FILEOUT = file_out
        if self.size % 8:                                            #(T3)
            raise ValueError( err_str )                              #(T4)
        for byte in range(self.size/8 ):                             #(T5)
            value = 0                                                #(T6)
            for bit in range(8):                                     #(T7)
                value += (self._getbit( byte*8 + (7 - bit) ) << bit )#(T8)
            file_out.write( chr(value) )                             #(T9)


    def close_file_object(self):                                     #(U1)
        '''
        For closing a file object that was used for reading the bits into
        one or more BitVector objects.
        '''
        if not self.FILEIN:                                          #(U2)
            raise SyntaxError( "No associated open file" )           #(U3)
        self.FILEIN.close()                                          #(U4)


    def intValue(self):                                              #(V1)
        'Return the integer value of a bitvector'
        intVal = 0                                                   #(V2)
        for i in range(self.size):                                   #(V3)
            intVal += self[i] * (2 ** (self.size - i - 1))           #(V4)
        return intVal                                                #(V5)

            
    def __lshift__( self, n ):                                       #(W1)
        'For an in-place left circular shift by n bit positions'
        for i in range(n):                                           #(W2)
            self.circular_rotate_left_by_one()                       #(W3)


    def __rshift__( self, n ):                                       #(W4)
        'For an in-place right circular shift by n bit positions.'
        for i in range(n):                                           #(W5)
            self.circular_rotate_right_by_one()                      #(W6)


    def circular_rotate_left_by_one(self):                           #(X1)
        'For a one-bit in-place left circular shift'
        size = len(self.vector)                                      #(X2)
        bitstring_leftmost_bit = self.vector[0] & 1                  #(X3)
        left_most_bits = map(operator.__and__, self.vector, [1]*size)#(X4)
        left_most_bits.append(left_most_bits[0])                     #(X5)
        del(left_most_bits[0])                                       #(X6)
        self.vector = map(operator.__rshift__, self.vector, [1]*size)#(X7)
        self.vector = map( operator.__or__, self.vector, \
             map(operator.__lshift__, left_most_bits, [15]*size) )   #(X8)
        self._setbit(self.size -1, bitstring_leftmost_bit)           #(X9)


    def circular_rotate_right_by_one(self):                          #(Y1)
        'For a one-bit in-place right circular shift'
        size = len(self.vector)                                      #(Y2)
        bitstring_rightmost_bit = self[self.size - 1]                #(Y3)
        right_most_bits = map( operator.__and__,
                               self.vector, [0x8000]*size )          #(Y4)
        self.vector = \
             map( operator.__and__, self.vector, [~0x8000]*size )    #(Y5)
        right_most_bits.insert(0, bitstring_rightmost_bit)           #(Y6)
        right_most_bits.pop()                                        #(Y7)
        self.vector = map(operator.__lshift__, self.vector, [1]*size)#(Y8)
        self.vector = map( operator.__or__, self.vector, \
             map(operator.__rshift__, right_most_bits, [15]*size) )  #(Y9)
        self._setbit(0, bitstring_rightmost_bit)                    #(Y10)


    def circular_rot_left(self):                                     #(Z1)
        '''
        This is merely another implementation of the method
        circular_rotate_left_by_one() shown above.  This one does NOT use
        map functions.  This method carries out a one-bit left circular
        shift of a bit vector.
        '''
        max_index = (self.size -1)  // 16                            #(Z2)
        left_most_bit = self.vector[0] & 1                           #(Z3)
        self.vector[0] = self.vector[0] >> 1                         #(Z4)
        for i in range(1, max_index + 1):                            #(Z5)
            left_bit = self.vector[i] & 1                            #(Z6)
            self.vector[i] = self.vector[i] >> 1                     #(Z7)
            self.vector[i-1] |= left_bit << 15                       #(Z8)
        self._setbit(self.size -1, left_most_bit)                    #(Z9)


    def circular_rot_right(self):                                    #(a1)
        '''
        This is merely another implementation of the method
        circular_rotate_right_by_one() shown above.  This one does NOT use
        map functions.  This method does a one-bit right circular shift of
        a bit vector.
        '''
        max_index = (self.size -1)  // 16                            #(a2)
        right_most_bit = self[self.size - 1]                         #(a3)
        self.vector[max_index] &= ~0x8000                            #(a4)
        self.vector[max_index] = self.vector[max_index] << 1         #(a5)
        for i in range(max_index-1, -1, -1):                         #(a6)
            right_bit = self.vector[i] & 0x8000                      #(a7)
            self.vector[i] &= ~0x8000                                #(a8)
            self.vector[i] = self.vector[i] << 1                     #(a9)
            self.vector[i+1] |= right_bit >> 15                     #(a10)
        self._setbit(0, right_most_bit)                             #(a11)


    # Allow array like subscripting for getting and setting:
    __getitem__ = _getbit                                            #(b1)

    def __setitem__(self, pos, item):                                #(b2)
        '''
        This is needed for both slice assignments and for index
        assignments.  It checks the types of pos and item to see if the
        call is for slice assignment.  For slice assignment, pos must be of
        type 'slice' and item of type BitVector.  For index assignment, the
        argument types are checked in the _setbit() method.
        '''      
        # The following section is for slice assignment:
        if isinstance( pos, slice ):                                 #(b3)
            if (not isinstance( item, BitVector )):                  #(b4)
                raise TypeError('For slice assignment, \
                        the right hand side must be a BitVector')    #(b5)
            if ( (pos.stop - pos.start) != len(item) ):              #(b6)
                raise ValueError('incompatible lengths for \
                                               slice assignment')    #(b7)
            for i in range( pos.start, pos.stop ):                   #(b8)
                self[i] = item[ i - pos.start ]                      #(b9)
            return                                                  #(b10)
        # For index assignment use _setbit()
        self._setbit( pos, item )                                   #(b11)


    def __getslice__(self, i, j):                                    #(c1)
        'Allow slicing with [i:j], [:], etc.'
        slicebits = []                                               #(c2)
        if j > self.size: j = self.size                              #(c3)
        for x in range(i,j):                                         #(c4)
            slicebits.append( self[x] )                              #(c5)
        return BitVector( bitlist = slicebits )                      #(c6)


    # Allow len() to work:
    __len__ = _getsize                                               #(d1)
    # Allow int() to work:
    __int__ = intValue                                               #(d2)

    def __iter__( self ):                                            #(d3)
        '''
        To allow iterations over a bit vector by supporting the 'for bit in
        bit_vector' syntax:
        '''
        return BitVectorIterator( self )                             #(d4)


    def __str__( self ):                                             #(e1)
        'To create a print representation'
        if self.size == 0:                                           #(e2)
            return ''                                                #(e3)
        return ''.join( map( str, self ) )                           #(e4)


    # Compare two bit vectors:

    def __eq__(self, other):                                         #(f1)
        if self.size != other.size:                                  #(f2)
            return False                                             #(f3)
        i = 0                                                        #(f4)
        while ( i < self.size ):                                     #(f5)
            if (self[i] != other[i]): return False                   #(f6)
            i += 1                                                   #(f7)
        return True                                                  #(f8)
    def __ne__(self, other):                                         #(f9)
        return not self == other                                    #(f10)
    def __lt__(self, other):                                        #(f11)
        return self.intValue() < other.intValue()                   #(f12)
    def __le__(self, other):                                        #(f13)
        return self.intValue() <= other.intValue()                  #(f14)
    def __gt__(self, other):                                        #(f15)
        return self.intValue() > other.intValue()                   #(f16)
    def __ge__(self, other):                                        #(f17)
        return self.intValue() >= other.intValue()                  #(f18)

    # Some additional utility functions:

    def _make_deep_copy( self ):                                     #(g1)
        'Make a deep copy of a bit vector'
        copy = str( self )                                           #(g2)
        return BitVector( bitstring = copy )                         #(g3)


    def _resize_pad_from_left( self, n ):                            #(g4)
        '''
        Resize a bit vector by padding with n 0's from the left. Return the
        result as a new bit vector.
        '''
        new_str = '0'*n + str( self )                                #(g5)
        return BitVector( bitstring = new_str )                      #(g6)


    def _resize_pad_from_right( self, n ):                           #(g7)
        '''
        Resize a bit vector by padding with n 0's from the right. Return
        the result as a new bit vector.
        '''
        new_str = str( self ) + '0'*n                                #(g8)
        return BitVector( bitstring = new_str )                      #(g9)


    def pad_from_left( self, n ):                                   #(g10)
        'Pad a bit vector with n zeros from the left'
        new_str = '0'*n + str( self )                               #(g11)
        bitlist =  map( int, list(new_str) )                        #(g12)
        self.size = len( bitlist )                                  #(g13)
        two_byte_ints_needed = (len(bitlist) + 15) // 16            #(g14)
        self.vector = array.array( 'H', [0]*two_byte_ints_needed )  #(g15)
        map( self._setbit, enumerate(bitlist), bitlist)             #(g16)


    def pad_from_right( self, n ):                                  #(g17)
        'Pad a bit vector with n zeros from the right'
        new_str = str( self ) + '0'*n                               #(g18)
        bitlist =  map( int, list(new_str) )                        #(g19)
        self.size = len( bitlist )                                  #(g20)
        two_byte_ints_needed = (len(bitlist) + 15) // 16            #(g21)
        self.vector = array.array( 'H', [0]*two_byte_ints_needed )  #(g22)
        map( self._setbit, enumerate(bitlist), bitlist)             #(g23)


    def __contains__( self, otherBitVec ):                           #(h1)
        '''
        This supports 'if x in y' and 'if x not in y' syntax for bit
        vectors.
        '''
        if self.size == 0:                                           #(h2)
              raise ValueError, "First arg bitvec has no bits"       #(h3)
        elif self.size < otherBitVec.size:                           #(h4)
              raise ValueError, "First arg bitvec too short"         #(h5)
        max_index = self.size - otherBitVec.size + 1                 #(h6)
        for i in range(max_index):                                   #(h7)
              if self[i:i+otherBitVec.size] == otherBitVec:          #(h8)
                    return True                                      #(h9)
        return False                                                #(h10)


    def reset( self, val ):                                          #(j1)
        '''
        Resets a previously created BitVector to either all zeros or all
        ones depending on the argument val.  Returns self to allow for
        syntax like
               bv = bv1[3:6].reset(1)
        or
               bv = bv1[:].reset(1)
        '''
        if val not in (0,1):                                         #(j2)
            raise ValueError( "Incorrect reset argument" )           #(j3)
        bitlist = [val for i in range( self.size )]                  #(j4)
        map( self._setbit, enumerate(bitlist), bitlist )             #(j5)
        return self                                                  #(j6)

    def count_bits( self ):                                          #(k1)
        '''
        Return the number of bits set in a BitVector instance.
        '''
        return reduce( lambda x, y: int(x)+int(y), self )            #(k2)

    def setValue(self, *args, **kwargs ):                            #(m1)
        '''
        Changes the bit pattern associated with a previously constructed
        BitVector instance.  The allowable modes for chaning the internally
        stored bit patten are the same as for the constructor.
        '''
        self.__init__( *args, **kwargs )                             #(m2)

    def count_bits_sparse( self ):                                   #(n1)
        '''
        For sparse bit vectors, this method, contributed by Rhiannon, will
        be much faster.  She estimates that if a bit vector with over 2
        millions bits has only five bits set, this will return the answer
        in 1/18 of the time taken by the count_bits() method.  Note
        however, that count_bits() may work much faster for dense-packed
        bit vectors.  Rhianon's implementation is based on an algorithm
        generally known as the Brian Kernighan's way, although its
        antecedents predate its mention by Kernighan and Ritchie.
        '''
        num = 0                                                      #(n2)
        for intval in self.vector:                                   #(n3)
            if intval == 0: continue                                 #(n4)
            c = 0; iv = intval                                       #(n5)
            while iv > 0:                                            #(n6)
                iv = iv & (iv -1)                                    #(n7)
                c = c + 1                                            #(n8)
            num = num + c                                            #(n9)
        return num                                                  #(n10)

    def jaccard_similarity( self, other ):                           #(p1)
        ''' 
        Computes the Jaccard similarity coefficient between two bit vectors
        '''
        assert self.size == other.size, 'vectors of unequal length'  #(p2)
        intersect = self & other                                     #(p4)
        union = self | other                                         #(p5)
        return ( intersect.count_bits_sparse()\
                  / float( union.count_bits_sparse() ) )             #(p6)

    def jaccard_distance( self, other ):                             #(q1)
        ''' 
        Computes the Jaccard distance between two bit vectors
        '''
        assert self.size == other.size, 'vectors of unequal length'  #(q2)
        return 1 - self.jaccard_similarity( other )                  #(q3)

    def hamming_distance( self, other ):                             #(r1)
        '''
        Computes the Hamming distance between two bit vectors
        '''
        assert self.size == other.size, 'vectors of unequal length'  #(r2)
        diff = self ^ other                                          #(r3)
        return diff.count_bits_sparse()                              #(r4)

    def next_set_bit(self, from_index=0):                            #(s1)
        '''
        This method, contributed by Jason Allum, calculates the number of
        bit positions from the current position index to the next set bit.
        '''
        assert from_index >= 0, 'from_index must be nonnegative'     #(s2)
        i = from_index                                               #(s3)
        v = self.vector                                              #(s4)
        l = len(v)                                                   #(s5)
        o = i >> 4                                                   #(s6)
        m = 1 << (i & 0x0F)                                          #(s7)
        while o < l:                                                 #(s8)
            h = v[o]                                                 #(s9)
            if h:                                                   #(s10)
                while m != (1 << 0x10):                             #(s11)
                    if h & m: return i                              #(s12)
                    m <<= 1                                         #(s13)
                    i += 1                                          #(s14)
            else:                                                   #(s15)
                i += 0x10                                           #(s16)
            m = 1                                                   #(s17)
            o += 1                                                  #(s18)
        return -1                                                   #(s19)

    def rank_of_bit_set_at_index( self, position ):                  #(t1)
        '''
        For a bit that is set at the argument 'position', this method
        returns how many bits are set to the left of that bit.  For
        example, in the bit pattern 000101100100, a call to this method
        with position set to 9 will return 4.
        '''
        assert self[position] == 1, 'the arg bit not set'
        bv = self[0:position+1]                                      #(t2)
        return bv.count_bits()                                       #(t3)

    def isPowerOf2( self ):                                          #(t1)
        '''
        Determines whether the integer value of a bit vector is a power of
        2.
        '''
        if self.intValue() == 0: return False                        #(u2)
        bv = self & BitVector( intVal = self.intValue() - 1 )        #(u3)
        if bv.intValue() == 0: return True                           #(u4)
        return False                                                 #(u5)

    def isPowerOf2_sparse( self ):                                   #(v1)
        '''
        Faster version of isPowerOf2() for sparse bit vectors
        '''
        if self.count_bits_sparse() == 1: return True                #(v2)
        return False                                                 #(v3)

    def reverse( self ):                                             #(w1)
        '''
        Returns a new bit vector by reversing the bits in the bit vector on
        which the method is invoked.
        '''
        reverseList = []                                             #(w2)
        i = 1                                                        #(w3)
        while ( i < self.size + 1 ):                                 #(w4)
            reverseList.append( self[ -i ] )                         #(w5)
            i += 1                                                   #(w6)
        return BitVector( bitlist = reverseList )                    #(w7)

    def gcd( self, other ):                                          #(x1)
        ''' 
        Using Euclid's Algorithm, returns the greatest common divisor of
        the integer value of the bit vector on which the method is invoked
        and the integer value of the argument bit vector.
        '''
        a = self.intValue(); b = other.intValue()                    #(x2)
        if a < b: a,b = b,a                                          #(x3)
        while b != 0:                                                #(x4)
            a, b = b, a % b                                          #(x5)
        return BitVector( intVal = a )                               #(x6)

    def multiplicative_inverse( self, modulus ):                     #(y1)
        '''
        Calculates the multiplicative inverse of a bit vector modulo the
        bit vector that is supplied as the argument. Code based on the
        Extended Euclid's Algorithm.
        '''
        MOD = mod = modulus.intValue(); num = self.intValue()        #(y2)
        x, x_old = 0L, 1L                                            #(y3)
        y, y_old = 1L, 0L                                            #(y4)
        while mod:                                                   #(y5)
            quotient = num // mod                                    #(y6)
            num, mod = mod, num % mod                                #(y7)
            x, x_old = x_old - x * quotient, x                       #(y8)
            y, y_old = y_old - y * quotient, y                       #(y9)
        if num != 1:                                                #(y10)
            return None                                             #(y11)
        else:                                                       #(y12)
            MI = (x_old + MOD) % MOD                                #(y13)
            return BitVector( intVal = MI )                         #(y14)


#-----------------------  BitVectorIterator Class -----------------------

class BitVectorIterator:                                            #(IT1)
    def __init__( self, bitvec ):                                   #(IT2)
        self.items = []                                             #(IT3)
        for i in range( bitvec.size ):                              #(IT4)
            self.items.append( bitvec._getbit(i) )                  #(IT5)
        self.index = -1                                             #(IT6)
    def __iter__( self ):                                           #(IT7)
        return self                                                 #(IT8)
    def next( self ):                                               #(IT9)
        self.index += 1                                            #(IT10)
        if self.index < len( self.items ):                         #(IT11)
            return self.items[ self.index ]                        #(IT12)
        else:                                                      #(IT13)
            raise StopIteration                                    #(IT14)

       
#------------------------  End of Class Definition -----------------------


#------------------------     Test Code Follows    -----------------------

if __name__ == '__main__':

    # Construct a bit vector of size 0
    print "\nConstructing a bit vector of size 0:"
    bv1 = BitVector( size = 0 )
    print bv1                                   # no output

    # Construct a bit vector of size 2:
    print "\nConstructing a bit vector of size 2:"
    bv2 = BitVector( size = 2 )
    print bv2                                   # 00

    # Joining two bit vectors:
    print "\nOutput concatenation of two previous bit vectors:"
    print bv1 + bv2                             # 00

    # Construct a bit vector with a tuple of bits:
    print "\nThis is a bit vector from a tuple of bits:"
    bv = BitVector( bitlist = (1, 0, 0, 1) )
    print bv                                    # 1001

    # Construct a bit vector with a list of bits:    
    print "\nThis is a bit vector from a list of bits:"
    bv = BitVector( bitlist = [1, 1, 0, 1] )
    print bv                                    # 1101
    
    # Construct a bit vector from an integer
    bv = BitVector( intVal = 5678 )
    print "\nBit vector constructed from integer 5678:"
    print bv                                    # 1011000101110
    print "\nBit vector constructed from integer 0:"
    bv = BitVector( intVal = 0 )
    print bv                                    # 0
    print "\nBit vector constructed from integer 2:"
    bv = BitVector( intVal = 2 )
    print bv                                    # 10
    print "\nBit vector constructed from integer 3:"
    bv = BitVector( intVal = 3 )
    print bv                                    # 11
    print "\nBit vector constructed from integer 123456:"
    bv = BitVector( intVal = 123456 )
    print bv                                    # 11110001001000000
    print "\nInt value of the previous bit vector as computed by intVal():"
    print bv.intValue()                         # 123456
    print "\nInt value of the previous bit vector as computed by int():"
    print int( bv )                             # 123456

    # Construct a bit vector directly from a file-like object:
    import StringIO
    x = "111100001111"
    fp_read = StringIO.StringIO( x )
    bv = BitVector( fp = fp_read )
    print "\nBit vector constructed directed from a file like object:"
    print bv                                    # 111100001111 

    # Construct a bit vector directly from a bit string:
    bv = BitVector( bitstring = '00110011' )
    print "\nBit Vector constructed directly from a string:"
    print bv                                    # 00110011

    bv = BitVector( bitstring = '' )
    print "\nBit Vector constructed directly from an empty string:"
    print bv                                    # nothing

    print "\nInteger value of the previous bit vector:"
    print bv.intValue()                         # 0

    # Test array-like indexing for a bit vector:
    bv = BitVector( bitstring = '110001' )
    print "\nPrints out bits individually from bitstring 110001:"
    print bv[0], bv[1], bv[2], bv[3], bv[4], bv[5]       # 1 1 0 0 0 1
    print "\nSame as above but using negative array indexing:"
    print bv[-1], bv[-2], bv[-3], bv[-4], bv[-5], bv[-6] # 1 0 0 0 1 1

    # Test setting bit values with positive and negative
    # accessors:
    bv = BitVector( bitstring = '1111' )
    print "\nBitstring for 1111:"
    print bv                                    # 1111

    print "\nReset individual bits of above vector:"
    bv[0]=0;bv[1]=0;bv[2]=0;bv[3]=0        
    print bv                                    # 0000
    print "\nDo the same as above with negative indices:"
    bv[-1]=1;bv[-2]=1;bv[-4]=1
    print bv                                    # 1011

    print "\nCheck equality and inequality ops:"
    bv1 = BitVector( bitstring = '00110011' )
    bv2 = BitVector( bitlist = [0,0,1,1,0,0,1,1] )
    print bv1 == bv2                            # True
    print bv1 != bv2                            # False
    print bv1 < bv2                             # False
    print bv1 <= bv2                            # True
    bv3 = BitVector( intVal = 5678 )
    print bv3.intValue()                        # 5678
    print bv3                                   # 10110000101110
    print bv1 == bv3                            # False
    print bv3 > bv1                             # True
    print bv3 >= bv1                            # True


    # Create a string representation of a bit vector:
    fp_write = StringIO.StringIO()
    bv.write_bits_to_fileobject( fp_write )
    print "\nGet bit vector written out to a file-like object:"
    print fp_write.getvalue()                   # 1011 

    print "\nExperiments with bitwise logical operations:"
    bv3 = bv1 | bv2                              
    print bv3                                   # 00110011
    bv3 = bv1 & bv2
    print bv3                                   # 00110011
    bv3 = bv1 + bv2
    print bv3                                   # 0011001100110011
    bv4 = BitVector( size = 3 )
    print bv4                                   # 000
    bv5 = bv3 + bv4
    print bv5                                   # 0011001100110011000
    bv6 = ~bv5
    print bv6                                   # 1100110011001100111
    bv7 = bv5 & bv6
    print bv7                                   # 0000000000000000000
    bv7 = bv5 | bv6
    print bv7                                   # 1111111111111111111

    print "\nTry logical operations on bit vectors of different sizes:"
    print BitVector( intVal = 6 ) ^ BitVector( intVal = 13 )   # 1011
    print BitVector( intVal = 6 ) & BitVector( intVal = 13 )   # 0100
    print BitVector( intVal = 6 ) | BitVector( intVal = 13 )   # 1111

    print BitVector( intVal = 1 ) ^ BitVector( intVal = 13 )   # 1100
    print BitVector( intVal = 1 ) & BitVector( intVal = 13 )   # 0001
    print BitVector( intVal = 1 ) | BitVector( intVal = 13 )   # 1101

    print "\nExperiments with setbit() and getsize():"
    bv7[7] = 0
    print bv7                                   # 1111111011111111111
    print len( bv7 )                            # 19
    bv8 = (bv5 & bv6) ^ bv7
    print bv8                                   # 1111111011111111111
    

    print "\nConstruct a bit vector from what is in the file testinput1.txt:"
    bv = BitVector( filename = 'TestBitVector/testinput1.txt' )
    #print bv                                    # nothing to show
    bv1 = bv.read_bits_from_file(64)    
    print "\nPrint out the first 64 bits read from the file:"
    print bv1
         # 0100000100100000011010000111010101101110011001110111001001111001
    print "\nRead the next 64 bits from the same file:"
    bv2 = bv.read_bits_from_file(64)    
    print bv2
         # 0010000001100010011100100110111101110111011011100010000001100110
    print "\nTake xor of the previous two bit vectors:"
    bv3 = bv1 ^ (bv2)
    print bv3
         # 0110000101000010000110100001101000011001000010010101001000011111

    print "\nExperiment with dividing an even-sized vector into two:"
    [bv4, bv5] = bv3.divide_into_two()
    print bv4                            # 01100001010000100001101000011010
    print bv5                            # 00011001000010010101001000011111

    # Permute a bit vector:
    print "\nWe will use this bit vector for experiments with permute()"
    bv1 = BitVector( bitlist = [1, 0, 0, 1, 1, 0, 1] )
    print bv1                                    # 1001101
    
    bv2 = bv1.permute( [6, 2, 0, 1] )
    print "\nPermuted and contracted form of the previous bit vector:"
    print bv2                                    # 1010

    print "\nExperiment with writing an internally generated bit vector out to a disk file:"
    bv1 = BitVector( bitstring = '00001010' ) 
    FILEOUT = open( 'TestBitVector/test.txt', 'wb' )
    bv1.write_to_file( FILEOUT )
    FILEOUT.close()
    bv2 = BitVector( filename = 'TestBitVector/test.txt' )
    bv3 = bv2.read_bits_from_file( 32 )
    print "\nDisplay bit vectors written out to file and read back from the file and their respective lengths:"
    print bv1, bv3
    print len(bv1), len(bv3)


    print "\nExperiments with reading a file from the beginning to end:"
    bv = BitVector( filename = 'TestBitVector/testinput4.txt' )
    print "\nHere are all the bits read from the file:"
    while (bv.more_to_read):
        bv_read = bv.read_bits_from_file( 64 )
        print bv_read
    print

    print "\nExperiment with closing a file object and start extracting bit vectors from the file from the beginning again:"
    bv.close_file_object()
    bv = BitVector( filename = 'TestBitVector/testinput4.txt' )
    bv1 = bv.read_bits_from_file(64)        
    print "\nHere are all the first 64 bits read from the file again after the file object was closed and opened again:"
    print bv1           
    FILEOUT = open( 'TestBitVector/testinput5.txt', 'wb' )
    bv1.write_to_file( FILEOUT )
    FILEOUT.close()

    print "\nExperiment in 64-bit permutation and unpermutation of the previous 64-bit bitvector:"
    print "The permutation array was generated separately by the Fisher-Yates shuffle algorithm:"
    bv2 = bv1.permute( [22, 47, 33, 36, 18, 6, 32, 29, 54, 62, 4,
                        9, 42, 39, 45, 59, 8, 50, 35, 20, 25, 49,
                        15, 61, 55, 60, 0, 14, 38, 40, 23, 17, 41,
                        10, 57, 12, 30, 3, 52, 11, 26, 43, 21, 13,
                        58, 37, 48, 28, 1, 63, 2, 31, 53, 56, 44, 24,
                        51, 19, 7, 5, 34, 27, 16, 46] )
    print "Permuted bit vector:"
    print bv2

    bv3 = bv2.unpermute( [22, 47, 33, 36, 18, 6, 32, 29, 54, 62, 4,
                          9, 42, 39, 45, 59, 8, 50, 35, 20, 25, 49,
                          15, 61, 55, 60, 0, 14, 38, 40, 23, 17, 41,
                          10, 57, 12, 30, 3, 52, 11, 26, 43, 21, 13,
                          58, 37, 48, 28, 1, 63, 2, 31, 53, 56, 44, 24,
                          51, 19, 7, 5, 34, 27, 16, 46] )    
    print "Unpurmute the bit vector:"
    print bv3
    print
    print

    print "\nTry circular shifts to the left and to the right for the following bit vector:"
    print bv3   # 0100000100100000011010000111010101101110011001110111001001111001
    print "\nCircular shift to the left by 7 positions:"
    bv3 << 7
    print bv3   # 1001000000110100001110101011011100110011101110010011110010100000

    print "\nCircular shift to the right by 7 positions:"
    bv3 >> 7
    print bv3   # 0100000100100000011010000111010101101110011001110111001001111001

    print "Test len() on the above bit vector:"
    print len( bv3 )                      # 64

    print "\nTest forming a [5:22] slice of the above bit vector:"
    bv4 = bv3[5:22]
    print bv4                             # 00100100000011010

    print "\nTest the iterator:"
    for bit in bv4:
        print bit,                        # 0 0 1 0 0 1 0 0 0 0 0 0 1 1 0 1 0
    print
    
    print "\nDemonstrate padding a bit vector from left:"
    bv = BitVector( bitstring = '101010' )
    bv.pad_from_left( 4 )
    print bv                              # 0000101010
    print "\nDemonstrate padding a bit vector from right:"
    bv.pad_from_right( 4 )
    print bv                              # 00001010100000

    print "\nTest the syntax 'if bit_vector_1 in bit_vector_2' syntax:"
    try:
        bv1 = BitVector( bitstring = '0011001100' )
        bv2 = BitVector( bitstring = '110011' )
        if bv2 in bv1:
            print "%s is in %s" % (bv2, bv1)
        else:
            print "%s is not in %s" % (bv2, bv1)
    except ValueError, arg:
        print "Error Message: " + str(arg)

    print "\nTest the size modifier when a bit vector is initialized with the intVal method:"
    bv = BitVector( intVal = 45, size = 16 )
    print bv                              # 0000000000101101
    bv = BitVector( intVal = 0, size = 8 )    
    print bv                              # 00000000
    bv = BitVector( intVal = 1, size = 8 )    
    print bv                              # 00000001

    print "\nTesting slice assignment:"
    bv1 = BitVector( size = 25 )
    print "bv1= ", bv1                    # 0000000000000000000000000
    bv2 = BitVector( bitstring = '1010001' )
    print "bv2= ", bv2                    # 1010001
    bv1[6:9]  = bv2[0:3]
    print "bv1= ", bv1                    # 0000001010000000000000000

    print "\nTesting reset function:"
    bv1.reset( 1 )             
    print "bv1= ", bv1                    # 1111111111111111111111111
    print bv1[3:9].reset(0)               # 000000
    print bv1[:].reset(0)                 # 0000000000000000000000000

    print "\nTesting count_bit():"
    bv = BitVector( intVal = 45, size = 16 )
    y = bv.count_bits()
    print y
    bv = BitVector( bitstring = '100111' )
    print bv.count_bits()
    bv = BitVector( bitstring = '00111000' )
    print bv.count_bits()
    bv = BitVector( bitstring = '001' )
    print bv.count_bits()
    bv = BitVector( bitstring = '00000000000000' )
    print bv.count_bits()

    print "\nTest setValue idea:"
    bv = BitVector( intVal = 7, size =16 )
    print bv                              # 0000000000000111
    bv.setValue( intVal = 45 )
    print bv                              # 101101

    print "\nTesting count_bits_sparse():"
    bv = BitVector( size = 2000000 )
    bv[345234] = 1
    bv[233]=1
    bv[243]=1
    bv[18]=1
    bv[785] =1
    print "The number of bits set: ", bv.count_bits_sparse()     # 5

    print "\nTesting Jaccard similarity and distance and Hamming distance:"
    bv1 = BitVector( bitstring = '11111111' )
    bv2 = BitVector( bitstring = '00101011' )
    print "Jaccard similarity: ", bv1.jaccard_similarity( bv2 )  # 0.5
    print "Jaccard distance: ", bv1.jaccard_distance( bv2 )      # 0.5
    print "Jaccard distance: ", bv1.hamming_distance( bv2 )      # 4

    print "\nTesting next_set_bit():"
    bv = BitVector( bitstring = '00000000000001' )
    print bv.next_set_bit( 5 )                                   # 13

    print "\nTesting rank_of_bit_set_at_index():"
    bv = BitVector( bitstring = '01010101011100' )
    print bv.rank_of_bit_set_at_index( 10 )                      # 6

    print "\nTesting isPowerOf2():"
    bv = BitVector( bitstring = '10000000001110' )
    print "int value: ", int( bv )                               # 826
    print bv.isPowerOf2()                                        # False
    print "\nTesting isPowerOf2_sparse():"              
    print bv.isPowerOf2_sparse()                                 # False

    print "\nTesting reverse():"
    bv = BitVector( bitstring = '0001100000000000001' )
    print "original bv: ", bv                    # 0001100000000000001
    print "reversed bv: ", bv.reverse()          # 1000000000000011000

    print "\nTesting Greatest Common Divisor (gcd):"
    bv1 = BitVector( bitstring = '01100110' )
    print "first arg bv: ", bv1, "   of int value: ", int(bv1)    # 102
    bv2 = BitVector( bitstring = '011010' ) 
    print "second arg bv: ", bv2, "   of int value: ", int(bv2)   # 26
    bv = bv1.gcd( bv2 )
    print "gcd is: ", bv, "   of int value: ", int(bv)            # 2

    print "\nTesting multiplicative_inverse:"
    bv_modulus = BitVector( intVal = 32 )
    print "modulus is bv: ", bv_modulus, "   of int value: ", int(bv_modulus)
    bv = BitVector( intVal = 17 ) 
    print "bv: ", bv, "   of int value: ", int(bv)
    result = bv.multiplicative_inverse( bv_modulus )
    if result is not None:
        print "MI is: ", result, "   of int value: ", int(result)
    else: print "No multiplicative inverse in this case"

