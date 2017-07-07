HTTP_SERVER = 'http://localhost:80'

import json
import urllib2
import requests

document = {'time': '194558.000', 
 'MCC': 310,
 'MNC': 410,
 'LAC': '7935',
 'Cell_ID': '9821',
 'rxl': 5, 
 'arfcn': '0181',
 'bsic': '12', 
 'lat': 32.609306,
 'lon': -85.481558, 
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