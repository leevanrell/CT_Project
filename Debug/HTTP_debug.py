HTTP_SERVER = 'http://localhost:80'

import json
import urllib2
import requests

document = {'time': 194509.000, 
 'arfcn': '0181',
 'rxl': 12, 
 'bsic': '12', 
 'Cell_ID': '10a1',
 'MCC': 310,
 'MNC': 410,
 'LAC': '7935',
 'lat': 12.912,
 'lon': -34.021, 
 'satellites': 5,
 'GPS_quality': 2,
 'altitude': 230.2,
 'altitude_units': 'M'
}


try:
	json_object = json.loads(json.dumps(document))
except ValueError,e :
	print 'JSON: False'
print 'JSON: True'
print 'Sending JSON to %s' % HTTP_SERVER

r = requests.post(HTTP_SERVER, data = json.dumps(document))
print 'Status Code: %s' % r.status_code
print r.status_code == 200