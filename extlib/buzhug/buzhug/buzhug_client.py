import urllib,urllib2
import cPickle
import cStringIO

from buzhug import *

class ProxyBase(Base):

    NB_RECORDS = 100
    
    def request(self,method,*args,**kw):
        arg_str = cPickle.dumps(args and args or [])
        kw_str = cPickle.dumps(kw and kw or {})
        r = urllib2.urlopen('http://%s:%s' % (self.host, self.port),
                urllib.urlencode({'method':method,'basename':self.name,
                                                'args':arg_str,'kw':kw_str}))
        return r.read()
    
    def __init__(self,basename,host='localhost',port=3456):
        Base.__init__(self,basename)
        self.host = host
        self.port = port
        self.request('__init__')
        self._iterating = None

    def open(self):
        info = cStringIO.StringIO(self.request('open'))
        self._update_info(info)

    def create(self,*fields,**kw):
        info = self.request('create',*fields,**kw)
        self._update_info(info)

    def _update_info(self,info):
        info = cStringIO.StringIO(info)
        info.seek(0)
        self._open(info)

    def delete(self,records):
        if issubclass(records.__class__,Record):
            # individual record
            records = [records]
        _ids = [r.__id__ for r in records]
        self.request('delete',*_ids)            

    def cleanup(self):
        self.request('cleanup')
        
    def __getitem__(self,_id):
        res = cPickle.loads(self.request('__getitem__',_id))
        if res is IndexError:
            raise IndexError,'No record at index %s' %_id
        else:
            return self._full_rec(res)

    def insert(self,*args,**kw):
        return cPickle.loads(self.request('insert',*args,**kw))

    def select(self,names=None,request=None,**kw):
        names,res = cPickle.loads(self.request('select',names,request,**kw))
        Record = makeRecordClass(self,self.record_class,names)
        recs = [ Record(r) for r in res ]
        return ResultSet(names,recs)

    def select_for_update(self,names=None,request=None,**kw):
        if not names:
            names = self.field_names
        else:
            names += [ f for f in ['__id__','__version__'] if not f in names ]
        return self.select(names,request,**kw)

    def update(self,record,**kw):
        self.request('update',record.__id__,**kw)

    def add_field(self,field_name,field_type,after=None,default=None):
        info = self.request('add_field',field_name,field_type,after,default)
        self._update_info(info)
        
    def drop_field(self,field_name):
        info = self.request('drop_field',field_name)
        self._update_info(info)

    def __delitem__(self,num):
        """Delete the item at id num"""
        self.request('delete',num)

    def __len__(self):
        return cPickle.loads(self.request('__len__'))

    def has_key(self,num):
        p_block = self._pos.get_block_at(num)
        if not p_block or p_block[0] == '#':
            return False
        return True

    def keys(self):
        return [ r.__id__ for r in self.select(['__id__']) ]

    def has_key(self,num):
        return cPickle.loads(self.request('has_key',num))

    def keys(self):
        return cPickle.loads(self.request('keys'))

    def __iter__(self):
        """Iterate on all records"""
        if self._iterating is None:
            self._iterating = 0
        
        while True:
            recs = self.select(None,
                __id__=[self._iterating,self._iterating+self.NB_RECORDS-1])
            if not recs:
                self._iterating = None
                raise StopIteration
            else:
                for rec in recs:
                    yield rec
                self._iterating += self.NB_RECORDS

if __name__ == "__main__":        
    p = ProxyBase('dummyProxy',8080)
    p.create(('name',str),('age',int),mode='override')
    p.insert('pierre',47)
    p.insert(name='claire',age=24)
    p.insert(name='camille',age=19)

    print 'first iteration'
    print sum([1 for r in p]),'records'
    print 'second iteration'
    print sum([1 for r in p]),'records'


    print len(p),'records'
    print p.keys()
    print p[0]
    print p[1]
    p.delete(p[0])
    try:
        print p[0]
    except IndexError:
        print 'record 0 deleted'
    p.cleanup()
    print len(p),'records'
    print p[1]
    print p.select(['name'],name='claire')
    print p.select_for_update(['name'],name='claire')
    p.update(p[1],name='florence')
    print p[1]
    p.update(p[1],name='marie-anne')
    print p[1]
    p.add_field('birth',date)
    print p[1]
    p.drop_field('birth')
    print p[1]
    print p[2]
    del p[2]
    try:
        print p[2]
    except IndexError:
        print 'record 2 deleted'
    print len(p),'records'
    print p.has_key(0)
    print p.has_key(1)
    print p.keys()
    #print p[3]
    