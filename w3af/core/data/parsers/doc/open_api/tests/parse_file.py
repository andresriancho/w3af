import json
from bravado_core.spec import Spec

config = {'use_models': False}
url = 'http://w3af.org/api/'
_file = 'data/simple.json'

spec_dict = json.loads(file(_file).read())

spec = Spec.from_dict(spec_dict,
                      origin_url=url,
                      config=config)


