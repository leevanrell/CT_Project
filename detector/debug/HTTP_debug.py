HTTP_SERVER = 'http://127.0.0.1:3000/data'

import json
import urllib2
import requests

document = {'time': '194168.000', 
 'MCC': '310',
 'MNC': '410',
 'LAC': '7935',
 'Cell_ID': '9821',
 'rxl': 20, 
 'arfcn': '0181',
 'bsic': '12', 
 'lat': 32.617306,
 'lon': -85.456558, 
 'satellites': 5,
 'GPS_quality': 2,
 'altitude': 230.2,
 'altitude_units': 'M'
}
print document
headers = {'content-type': 'application/json'}
r = requests.post(HTTP_SERVER, data=json.dumps(document), headers=headers)
print 'Status Code: %s' % r.status_code