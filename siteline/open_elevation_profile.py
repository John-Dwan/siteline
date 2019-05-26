"""
Created on 7 Apr 2018

@author: john.dwan

ELEVATION PROFILE APP GENERATOR
ideagora geomatics-2018
http://geodose.com
"""

import json
from math import asin, cos, radians, sin, sqrt
import urllib.request

import matplotlib.pyplot as plt
from shapely.geometry import LineString

from siteline import config


def haversine(lat1, lon1, lat2, lon2):
	"""
	Given the coordinates of two points as floats

	Returns the distance between these two point in km
	"""
	lat1_rad = radians(lat1)
	lat2_rad = radians(lat2)
	lon1_rad = radians(lon1)
	lon2_rad = radians(lon2)
	delta_lat = lat2_rad - lat1_rad
	delta_lon = lon2_rad - lon1_rad
	a = sqrt((sin(delta_lat / 2)) ** 2 + cos(lat1_rad) * cos(lat2_rad) * (sin(delta_lon / 2)) ** 2)
	d = 2 * 6371000 * asin(a)
	return d


def plot_profile(
		a_end_name, a_end_lat, a_end_lon, b_end_name, b_end_lat, b_end_lon, a_end_agl=10, b_end_agl=20, num_points=1000):
	"""
	Takes a customer site (a_end_name=str), it's coordinates (a_end_lat=Float, a_end_lon=Float) and a
	Highsite (b_end_name=str) and it's coordinates (b_end_lat=Float, b_end_lon=Float)
	and optionally number of points along a line (num_points=Integer) which is max 1000 on open-elevation.com API,
	Note: no limit if running open-elevation locally.

	Saves a elevation profile between these two points as a .png
	"""

	# NUMBER OF POINTS
	interval_lat = (b_end_lat - a_end_lat) / num_points  # interval for latitude
	interval_lon = (b_end_lon - a_end_lon) / num_points  # interval for longitude

	# LATITUDE AND LONGITUDE LIST
	lat_list = [a_end_lat]
	lon_list = [a_end_lon]

	# GENERATING POINTS
	for i in range(num_points):
		lat_step = a_end_lat + interval_lat
		lon_step = a_end_lon + interval_lon
		a_end_lon = lon_step
		a_end_lat = lat_step
		lat_list.append(lat_step)
		lon_list.append(lon_step)

	# DISTANCE CALCULATION
	d_list = []
	for j in range(len(lat_list)):
		lat_p = lat_list[j]
		lon_p = lon_list[j]
		dp = haversine(a_end_lat, a_end_lon, lat_p, lon_p) / 1000  # km
		d_list.append(dp)
	d_list_rev = d_list[::-1]  # reverse list

	# CONSTRUCT JSON
	location = {}
	d_ar = [{}] * len(lat_list)
	for i in range(len(lat_list)):
		d_ar[i] = {"latitude": lat_list[i], "longitude": lon_list[i]}
	location['locations'] = d_ar
	json_data = json.dumps(location, skipkeys=int).encode('utf8')

	# SEND REQUEST
	response = urllib.request.Request(config.URL, json_data, headers={'Content-Type': 'application/json'})
	fp = urllib.request.urlopen(response)

	# RESPONSE PROCESSING
	res_byte = fp.read()
	res_str = res_byte.decode("utf8")
	js_str = json.loads(res_str)
	fp.close()

	# GETTING ELEVATION
	response_len = len(js_str['results'])
	elev_list = []
	for j in range(response_len):
		elev_list.append(js_str['results'][j]['elevation'])

	# BASIC STAT INFORMATION
	# mean_elev = round((sum(elev_list) / len(elev_list)), 3)
	# min_elev = min(elev_list)
	# max_elev = max(elev_list)
	distance = d_list_rev[-1]

	# LoS
	a_list = []
	for i in range(0, len(d_list_rev) - 1):
		a_tuple = (d_list_rev[i], elev_list[i])
		a_list.append(a_tuple)
	terrain = LineString(a_list)
	los_path = LineString(
		[(d_list_rev[0], elev_list[0] + a_end_agl), (d_list_rev[-1], elev_list[-1] + b_end_agl)])

	path_colour = '--g'
	print(terrain.intersection(los_path))
	if terrain.intersection(los_path):
		print('No LoS')
		path_colour = '--r'

	# PLOT ELEVATION PROFILE
	# with context('fivethirtyeight'):
	base_reg = 0
	plt.figure(figsize=(10, 4))
	plt.plot(d_list_rev, elev_list)
	plt.plot(
		[d_list_rev[0],
		d_list_rev[-1]],
		[elev_list[0] + a_end_agl,
		elev_list[-1] + b_end_agl],
		path_colour,
		label='LoS 10m AGL customer site to 20m highsite'
	)
	plt.fill_between(d_list_rev, elev_list, base_reg, alpha=0.1)
	plt.text(d_list_rev[0], elev_list[0], a_end_name)
	plt.text(d_list_rev[-1], elev_list[-1], b_end_name)
	plt.xlabel('Distance(km)    ' + str(round(distance)) + 'km')
	plt.ylabel('Elevation(m)    ' + str(elev_list[-1] - elev_list[0]) + 'm')
	plt.grid()
	plt.legend(fontsize='small')
	fname = a_end_name + '__to__' + b_end_name + '.png'
	plt.savefig(config.OUT_PATH.joinpath(fname))
	plt.close()
