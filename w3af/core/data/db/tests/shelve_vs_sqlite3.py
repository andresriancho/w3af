import time
import shelve
import sqlite3
 
def _sqlite3_inserts():
    conn = sqlite3.connect("debug.s3db")
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS [mydict] ("
                "[key] VARCHAR(255) PRIMARY KEY NOT NULL, "
                "[value] VARCHAR(255) NOT NULL)")
    for i in xrange(0, 1000000):
        cur.execute("INSERT INTO [mydict] (key, value) VALUES (?, ?)",
                    (str(i), str(i*2)))
    conn.commit()
    cur.close()
    conn.close()
    
def _shelve_inserts():
    d = shelve.open("debug.shelf")
    for i in xrange(0, 1000000):
        d[str(i)] = str(i*2)
    d.close()


def measure(what, func):
    
    start = time.time()
    func()
    end = time.time()

    print '%s took %s seconds' % (what, end-start)

if __name__ == '__main__':
    measure('sqlite3', _sqlite3_inserts) # sqlite3 took 9.87409496307 seconds
    measure('shelve', _shelve_inserts) # shelve took 63.4450500011 seconds
    
