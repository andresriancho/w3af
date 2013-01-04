import time
import shelve
import sqlite3
 
def test_sqlite3():
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
    
def test_shelve():
    d = shelve.open("debug.shelf")
    for i in xrange(0, 1000000):
        d[str(i)] = str(i*2)
    d.close()


def measure(what, func):
    
    start = time.time()
    func()
    end = time.time()

    print '%s took %s seconds' % (what, end-start)

measure('sqlite3', test_sqlite3) # sqlite3 took 9.87409496307 seconds
measure('shelve', test_shelve) # shelve took 63.4450500011 seconds
