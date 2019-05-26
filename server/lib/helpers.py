#!/usr/bin/python3

import math


#https://gist.github.com/rochacbruno/2883505
def distance(origin, destination):
	lat1, lon1 = origin
	lat2, lon2 = destination
	radius = 6371 * 1000 # meters

	dlat = math.radians(lat2-lat1)
	dlon = math.radians(lon2-lon1)
	a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
	    * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
	d = radius * c
	return d

#http://pythonfiddle.com/python-triangulation-implementati/
def triangulate(points):
	""" Given points in (x,y, signal) format, approximate the position (x,y).
		Reading:
		* http://stackoverflow.com/questions/10329877/how-to-properly-triangulate-gsm-cell-towers-to-get-a-location
		* http://www.neilson.co.za/?p=364
		* http://gis.stackexchange.com/questions/40660/trilateration-algorithm-for-n-amount-of-points
		* http://gis.stackexchange.com/questions/2850/what-algorithm-should-i-use-for-wifi-geolocation
		"""
	# Weighted signal strength
	ws = sum(p[2] for p in points)
	points = tuple( (x,y,signal/ws) for (x,y,signal) in points )

	# Approximate
	return (
		sum(p[0]*p[2] for p in points), # x
		sum(p[1]*p[2] for p in points) # y
	)