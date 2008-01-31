import os
import random
import re

from datetime import date, datetime, time as dtime
from buzhug import Base, Record

try:
    from buzhug import ProxyBase, buzhug_files
except:
    from buzhug_client import ProxyBase
    import buzhug_files

names = ['pierre','claire','simon','camille','jean',
    'florence','marie-anne']
fr_names = [ 'andr\x82','fran\x87ois','h\x82l\x8ane' ] # latin-1 encoding

remote = False

if not remote:
    db = Base(r'dummy') 
else:
    db = ProxyBase('dummy')

db.create(('name',str), ('fr_name',unicode),
    ('age',int),('size',int),('birth',date),('afloat',float), ('birth_hour', dtime),
    mode='override')

for i in range(100):
    db.insert(name=random.choice(names),
         fr_name = unicode(random.choice(fr_names),'latin-1'),
         age=random.randint(7,47),size=random.randint(110,175),
         birth=date(random.randint(1958,1999),random.randint(1,12),10),
         afloat = random.uniform(-10**random.randint(-307,307),
            10**random.randint(-307,307)),
         birth_hour = dtime(random.randint(0, 23), random.randint(0, 59), random.randint(0, 59)))

#db.add_field('fr_name',unicode,after='name',
#    default=unicode('andr\x82','latin-1'))

for i in range(5):
    # insert a list
    db.insert(random.choice(names),
         unicode(random.choice(fr_names),'latin-1'),
         random.randint(7,47),random.randint(110,175),
         date(random.randint(1958,1999),random.randint(1,12),10),
         random.uniform(-10**random.randint(-307,307),
            10**random.randint(-307,307)),
         dtime(random.randint(0, 23), random.randint(0, 59), random.randint(0, 59)))
    db.insert(name=random.choice(names)) # missing fields

# insert as string
db.set_string_format(unicode,'latin-1')
db.set_string_format(date,'%d-%m-%y')
db.set_string_format(dtime,'%H-%M-%S')
db.insert_as_strings(name="testname",fr_name=random.choice(fr_names),
    age=10,size=123,birth="07-10-95", birth_hour="20-53-3")
print db[len(db)-1].birth
db.insert_as_strings("testname",random.choice(fr_names),
    11,134,"09-12-94",1.0, "5-6-13")
print db[len(db)-1].birth

for i in range(10):
    print db[i].birth
# search between 2 dates
print '\nBirth between 1960 and 1970'
for r in db.select(None,birth=[date(1960,1,1),date(1970,12,13)]):
    print r.name,r.birth

print "sorted"
for r in db.select(None,birth=[date(1960,1,1),date(1970,12,13)]).sort_by('+name-birth'):
    print r.name,r.birth

f = buzhug_files.FloatFile().to_block
def all(v):
    print v,[ord(c) for c in f(v)]
# search between 2 floats
print '\nFloat between 0 and 1e50'
print len(db.select(None,afloat=[0.0,1e50]))
all(0.0)
all(1e50)
print 'lc'
for r in [ r for r in db if 0.0 <= r.afloat <= 1e50 ]:
    all(r.afloat)
print '\n select'
for r in db.select(None,'x<=afloat<=y',x=0.0,y=1e50):
    all(r.afloat)

raw_input()

fr=random.choice(fr_names)
print fr
db.select(['name','fr_name'],age=30).pp()
db.select(['name','fr_name'],age=30,fr_name = unicode(fr,'latin-1')).pp()
db.select(['name','fr_name'],fr_name = unicode(fr,'latin-1')).pp()

for r in [ r for r in db if r.age == 30 and r.fr_name == unicode(fr,'latin-1')]:
    print r.name,r.fr_name.encode('latin-1')

raw_input()

# different ways to count the number of items
print len(db)
print sum([1 for r in db])
print len(db)
print len(db.select(['name']))
print len(db)

recs = db.select_for_update(['name'],'True')
print 'before update',recs[0].__version__,len(db)
for i in range(5):
    recs = db.select_for_update(['name'],'True')
    #db.update(recs[0])
    recs[0].update()
    print 'after update',db[0].__version__

print len(db)
db.cleanup()
print len(db)

recs = db.select([],'__id__ == c',c=20)
recs.pp()
print db[20]
print '\n has key 1000 ?',db.has_key(1000)
#print db[1000]

#db.drop_field('name')

print '\nRecord at position 10'
print db[10]
db.delete([db[10]])
try:
    print db[10]
    raise Exception,"Row 10 should have been deleted"
except IndexError:
    print 'Record 10 successfully deleted'
raw_input()

# selections    
print '\nage between 30 et 32'
for r in db.select(['__id__','fr_name','age','birth'],'c1 > age >= c2',c1=33,c2=30):
    print r
print '-------------'

# selection by generator expression
print 'age between 30 et 32'
d_ids = []
for r in [r for r in db if 33> r.age >= 30]:
    print r.name,r.age
    d_ids.append(r.__id__)
print '-------------'
print "deleted ids",d_ids

# remove these items
db.delete([r for r in db if 33> r.age >= 30])
print 'after remove',db._pos.deleted_lines,db._del_rows.deleted_rows

i = 0
for i,r in enumerate(db._pos):
    pass
print 'enumerate on _pos',i

print "after delete"
for r in [r for r in db if 33> r.age >= 30]:
    print r.name,r.age
print '-------------'

print '\nname = pierre'
for r in db.select(['__id__','name','age','birth'],name='pierre'):
    print r
print '-------------'

# make 'pierre' uppercase
print '\nmake pierre uppercase'
for record in db.select_for_update(None,'name == x',x='pierre'):
    db.update(record,name = record.name.upper())
    print db[record.__id__]

# increment ages
print '\nincrement ages'
for record in db.select_for_update([],'True'):
    if not record.age is None:
        db.update(record,age = record.age+1)
print db[5]

for record in [r for r in db]:
    if not record.age is None:
        db.update(record,age = record.age+1)
print db[5]

print "\nChange dates"
for record in db.select_for_update([],'age>v',v=35):
    db.update(record,birth = date(random.randint(1958,1999),
                            random.randint(1,12),10))

# select by id
try:
    print db[20]
    recs = db.select([],'__id__ == c',c=20)
    recs.pp()
except IndexError:
    print "No record at index 20 - must have been deleted"

raw_input()

db.commit()

print 'Number of records',sum([1 for r in db])
print 'By count',len(db)

for i in range(50):
    db.insert(name=random.choice(names),
         age=random.randint(7,47),size=random.randint(110,175))

print "\nafter insert"
try:
    print db[10]
    raise Exception,"Row 10 should have been deleted"
except IndexError:
    print 'Record 10 successfully deleted'

print db._pos.deleted_lines
print db._del_rows.deleted_rows
print 'by iter',sum([ 1 for r in db])

# physically remove the deleted items    
db.cleanup()
print "\nafter cleanup"
print db._pos.deleted_lines
print db._del_rows.deleted_rows

raw_input()

try:
    print db[10]
    raise Exception,"Row 10 should have been deleted"
except IndexError:
    print 'Record 10 successfully deleted'


print 'New count',len(db)
print 'by iter',len([ r for r in db])
print "age > 30"
for r in db.select(['__id__','name','age'],
    'name == c1 and age > c2',
    c1 = 'pierre',c2 = 30):
    print r.__id__,r.name,r.age

print '\nname =="PIERRE" and age > 30'
for r in db.select(['__id__','name','age','birth'],
            'name == c1 and age > c2',
            c1 = 'PIERRE',c2 = 30):
    print r.__id__,r.name,r.age,r.birth

# test with !=
print '\nname != claire'
print len(db.select(['__id__'],'name != c1',c1='claire'))

# uninitialized birth date
print "\nbirth = None"
res_set = db.select(['__id__','age'],birth = None,name='pierre')
res_set.pp()

# age > id
print "\nage > __id__ with select"
for r in db.select(['name','__id__','age'],'age > __id__'):
    print r.__id__,r.name,r.age

# age > id
print "\nage > __id__ with iter"
for r in [ r for r in db if r.age > r.__id__ ]:
    print r.__id__,r.name,r.age

# birth > date(1978,1,1)
print "\nbirth > date with select"
print len(db.select(['name','__id__','age'],'birth > v',v=date(1978,1,1)))

print "\nbirth > date with iter"
print len([ r for r in db if r.birth and r.birth > date(1978,1,1) ])

# age > 2*id
print "\nage > 2*__id__"
for r in [ r for r in db if r.age > 2*r.__id__ ]:
    print r.__id__,r.name,r.age

# regular expression
print "\nsearch names with ie"
for r in [ r for r in db if re.search("IE",r.name) ]:
    print r.name

# records with version != 0
print '\nversion > 0'
for r in db:
    if not r.__version__ == 0:
        print r.__version__,
print

# test with floats
print "\nSelection by float",
for i in range(10):
    x = random.uniform(-10**random.randint(-307,307),
            10**random.randint(-307,307))
    r1 = [ r for r in db if r.afloat > x ]
    r2 = db.select(['name'],'afloat > v',v=x)
    print len(r1)==len(r2)

houses = Base('houses')

try:
    houses.create(('address',str),('resident',db))
except IOError:
    houses.destroy()
    houses.create(('address',str),('resident',db))

addresses = ['Giono','Proust','Mauriac','Gide','Bernanos','Racine',
    'La Fontaine']
ks = db.keys()
for i in range(50):
    x = random.choice(ks)
    print x,
    houses.insert(address=random.choice(addresses),resident=db[x])
print
print houses[0]
print houses[0].resident.name

print '\nhouses with jean'
for h in houses:
    if h.resident.name == 'jean':
        print h.address,
        print h.resident.age

print '\n select with resident.name = jean'
recs = houses.select([],'resident == v',v='jean')
print recs

h1 = Base('houses')
h1.open()
print '\nh1[0]'
print h1[0]

class DictRecord(Record):
    def __getitem__(self, k):
        item = self
        names = k.split('.')
        for name in names:
            item = getattr(item, name)
        return item

h1.set_record_class(DictRecord)
print '\nrecord_class = DictRecord, h1[0]'
print h1[0]
print "\nResident name: %(resident.name)s\nAddress: %(address)s" % h1[0]

try:
    print db[10]
    raise Exception,"Row 10 should have been deleted"
except IndexError:
    print 'Record 10 successfully deleted'
