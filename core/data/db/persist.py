'''
persist.py

Copyright 2008 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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

'''

import sqlite3

try:
    from cPickle import Pickler, Unpickler
except ImportError:
    from pickle import Pickler, Unpickler
    
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

if __name__ != '__main__':
    from core.controllers.w3afException import w3afException

class persist:
    '''
    A class that persists objects to a file using sqlite3 and pickle.
    
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    def __init__(self):
        self._filename = None
        self._db = None
        self._primary_key_columns = None
        
        self._insertion_count = 0
    
    def open( self, filename ):
        '''
        Open an already existing database.
        
        @parameter filename: The filename where the database is.
        '''
        try:
            ### FIXME: check_same_thread=False
            self._db = sqlite3.connect(filename, check_same_thread=False)
        except Exception, e:
            raise w3afException('Failed to create the database in file "' + primary_key_columns +'". Exception: ' + str(e) )
        else:
            # Read the column names to recreate self._primary_key_columns
            pk_getters = []
            
            c = self._db.cursor()
            try:
                c.execute('PRAGMA table_info(data_table)')
                table_info = c.fetchall()
            except Exception, e:
                raise w3afException('Exception found while opening database: ' + str(e) )
            else:
                col_names = [ r[1] for r in table_info ]
                pk_getters = [ c for c in col_names if c != 'raw_pickled_data']
                    
                # Now we save the data to the attributes
                self._filename = filename
                self._primary_key_columns = pk_getters
    
    def create( self, filename, primary_key_columns ):
        '''
        @parameter primary_key_columns: A list of getters that we use to get the values for the primary key.
        @parameter filename: The file name where to save the data.
        '''
        self._create_db( filename, primary_key_columns)
        
    def persist( self, primary_key_values, obj ):
        '''
        Save an object to a file; if this is the first object to persist, we are going to create the database.
        
        @parameter primary_key_values: A tuple that contains the values of the primary key.
        @parameter obj: The object to persist.
        @return: None
        '''
        if not self._db:
            raise w3afException('You have to call open or create first.')
            
        insert_stm = "insert into data_table values ("
        
        # The primary key data
        bindings = []
        for column_number, column_name in enumerate(self._primary_key_columns):
            # Create the stm
            insert_stm += "(?) ,"
            # Get the value
            value = primary_key_values[column_number]
            bindings.append( str(value) )
            
        # And the pickled data
        f = StringIO()
        p = Pickler( f )
        p.dump(obj)
        insert_stm = insert_stm[:-1] + ", (?))"
        bindings.append( f.getvalue() )
        
        # Save the object
        self._db.execute( insert_stm, bindings )
        self._commit_if_needed()
        
    def commit( self ):
        '''
        Force a commit of the changes to disk.
        '''
        self._db.commit()
        
    def _commit_if_needed( self ):
        '''
        Once every 50 calls to this method, the data is commited to disk.
        '''
        self._insertion_count += 1
        if self._insertion_count > 50:
            self._db.commit()
            self._insertion_count = 0
            
    def _create_db( self, filename, primary_key_columns):
        '''
        Create the database; the columns of the database are going to be the primary_key_columns.
        
        @parameter filename: The filename where the object database is.
        @parameter primary_key_columns: The primary key getters.
        @return: None
        '''
        try:
            ### FIXME: check_same_thread=False
            self._db = sqlite3.connect(filename, check_same_thread=False)
        except Exception, e:
            raise w3afException('Failed to create the database in file "' + primary_key_columns +'". Exception: ' + str(e) )
        else:
            # Create the table for the data
            database_creation = 'create table data_table'
            database_creation += '('
            for column_name in primary_key_columns:
                attr_type = 'text'
                database_creation += column_name + ' ' + attr_type +' ,'
            
            # And now we add the column for the pickle
            database_creation = database_creation[:-1] + ', raw_pickled_data blob, '
            # Finally the PK
            database_creation += 'PRIMARY KEY ('+','.join(primary_key_columns)+'))'
            
            try:
                self._db.execute(database_creation)
            except Exception, e:
                raise e
            else:
                self._filename = filename
                self._primary_key_columns = primary_key_columns
    
    def retrieve( self, primary_key ):
        '''
        This method returns *only one* (if found) object. If the user want's to retrieve more than one object, he can do it easily
        with retrieve_all().
        
        @parameter primary_key: The user specifies here the primary key values which he wants to use in the retrieve process.
        @return: An object of the type that was persisted; None if the PK isn't in the database.
        '''
        if not self._db:
            raise w3afException('No database has been initialized.')
        
        if len(primary_key) != len(self._primary_key_columns):
            raise w3afException('The length of the primary_key should be equal to the length of the primary_key_columns.')
        
        # Get the row
        c = self._db.cursor()
        select_stm = "select * from data_table"
        select_stm += " where "
        bindings = []
        for column_number, column_name in enumerate(self._primary_key_columns):
            select_stm += column_name + '= (?)'
            bindings.append( primary_key[column_number] )
        
        try:
            c.execute( select_stm, bindings )
            row = c.fetchone()
        except Exception, e:
            return None
        else:
            # unpickle
            f = StringIO( str(row[-1]) )
            obj = Unpickler(f).load()
            return obj
    
    def retrieve_all( self, search_string ):
        '''
        This method returns a list of objects (if any is found).
        
        Examples:
            if search_string is 
                id='1' and url='abc'
            you'll get all object that match:
                SELECT * FROM DATA_TABLE WHERE id=1 AND url ='abc'
        
        @parameter search_string: The user specifies here the search parameters to use in the retrieve process.
        @return: An object of the type that was persisted; None if the PK isn't in the database.
        '''
        if not self._db:
            raise w3afException('No database has been initialized.')
        
        # Get the row(s)
        c = self._db.cursor()
        select_stm = "select * from data_table"
        # This is a SQL injection! =)
        select_stm += " where " + search_string
        try:
            c.execute( select_stm )
            rows = c.fetchall()
        except Exception, e:
            return []
        else:
            res = []
            
            # unpickle
            for row in rows:
                f = StringIO( str(row[-1]) )
                obj = Unpickler(f).load()
                res.append(obj)
                
            return res
            
    def raw_stm( self, stm ):
        '''
        Executes a select to the underlaying database. Only used for debugging.
        
        @parameter stm: The statement to execute.
        '''
        c = self._db.cursor()
        c.execute( stm )
        return c.fetchall()
        
    def close(self):
        '''
        Commits changes and closes the connection to the underlaying db.
        '''
        self._db.close()
        self._db.close()
        self._primary_key_columns = None
        self._filename = None
        
        
class test_class:
    def __init__( self ):
        self._spam =  'abc'
        self._eggs = 1
        self._foobar = 1.0
        self._id = 1
        
    def getSpam( self ):
        return self._spam
        
    def setSpam( self, s ):
        self._spam = s
        
    def getEggs( self ):
        return self._eggs
    
    def setEggs( self, e ):
        self._eggs = e
        
    def getFooBar( self ):
        return self._foobar
    
    def setFooBar( self, s ):
        self._foobar = s

    def getId( self ):
        return self._id
    
    def setId( self, i ):
        self._id = i
        
    def __eq__( self, other ):
        if self.getId() == other.getId():
            return True
        else:
            return False
            
        
if __name__ == '__main__':
    p = persist()
    p.create('/tmp/a.sqlite', primary_key_columns=['id',] )
    
    print '1- Loading...'
    tc = test_class()
    for i in xrange(10000):
        tc.setId( i )
        p.persist( (i,), tc )
    
    print '1- Retrieving...'
    for i in xrange(10000):
        p.retrieve( (i,) )
    p.close()
    
    p = persist()
    p.open('/tmp/a.sqlite')
    print '2- Loading...'
    tc = test_class()
    for i in xrange(10000, 20000):
        tc.setId( i )
        p.persist( (i,) , tc )
    
    print '2- Retrieving...'
    for i in xrange(10000, 20000):
        tc2 = p.retrieve( [i,] )
    
    
    if tc2.getId() == 19999:
        print 'Success!'
        
    if len(p.retrieve_all('id = 5 or id = 6')) == 2:
        print 'Success!'
        
    p.close()
 
