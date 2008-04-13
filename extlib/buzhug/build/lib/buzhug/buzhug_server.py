import cPickle
from buzhug import *

from SimpleAsyncHTTPServer import Server,DialogManager

class BuzhugServer(DialogManager):

    open_bases = {}

    def handle_data(self):
        self.send_response(200)
        self.end_headers()
        method = self.body['method'].value
        basename = self.body['basename'].value
        args = self.body['args'].value
        kw = self.body['kw'].value
        if args:
            args = cPickle.loads(args)
        else:
            args = []
        if kw:
            kw = cPickle.loads(kw)
        else:
            kw = {}
        if method == "__init__":
            self.open_bases[basename] = Base(basename)
        else:
            if not self.open_bases.has_key(basename):
                self.wfile.write('no base named %s' %basename)
            else:
                if hasattr(self,method):
                    self.db = self.open_bases[basename]
                    getattr(self,method)(*args,**kw)

        self.finish()    

    def __getitem__(self,rec_id):
        try:
            res = self.db[rec_id]
            res = [ res[i] for i,k in enumerate(self.db.field_names) ]
        except IndexError,msg:
            res = IndexError
        self.wfile.write(cPickle.dumps(res))

    def open(self):
        self.db.open()
        self.wfile.write(open(self.db.info_name,'rb').read())

    def create(self,*args,**kw):
        self.db.create(*args,**kw)
        self.wfile.write(open(self.db.info_name,'rb').read())

    def insert(self,*args,**kw):
        self.wfile.write(cPickle.dumps(self.db.insert(*args,**kw)))

    def delete(self,*args):
        # the server receives ids
        records = [ self.db[_id] for _id in args ]
        self.db.delete(records)

    def cleanup(self):
        self.db.cleanup()

    def select(self,*args,**kw):
        res0 = self.db.select(*args,**kw)
        names = res0.names
        res = []
        for r in res0:
            res.append([r[i] for i in range(len(names))])
        self.wfile.write(cPickle.dumps((names,res)))

    def update(self,*args,**kw):
        self.db.update(self.db[args[0]],**kw)

    def add_field(self,*args):
        self.db.add_field(*args)
        self.wfile.write(open(self.db.info_name,'rb').read())

    def drop_field(self,*args):
        self.db.drop_field(*args)
        self.wfile.write(open(self.db.info_name,'rb').read())

    def __len__(self):
        self.wfile.write(cPickle.dumps(len(self.db)))

    def has_key(self,*args):
        self.wfile.write(cPickle.dumps(self.db.has_key(*args)))

    def keys(self):
        self.wfile.write(cPickle.dumps(self.db.keys()))

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-P","--port",dest="port",default=3456,
        help = "port number")
    parser.add_option("-H","--host",dest="host",default="localhost",
        help = "host name")
    (options,args) = parser.parse_args()
    
    httpd = Server((options.host,options.port),BuzhugServer)
    print 'buzhug server on port %s' %options.port
    print 'Press CTRL+C to stop'
    try:
        httpd.loop()
    except KeyboardInterrupt:
        print 'CTRL+C pressed, shutting down'
        sys.exit()