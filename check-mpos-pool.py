#!/usr/bin/env python

import requests
import sys
import argparse

# Argument Parsing
parser = argparse.ArgumentParser(description="Query a MPOS mining pool API to get current mining hashrate for a given account.  Default is total hasrate for the user.  May also specify a worker name to query only for the hashrate of that worker.")
parser.add_argument("-w", metavar="HASHRATE", type=int, dest="warnThresh", help="Warning threshold", required=True)
parser.add_argument("-c", metavar="HASHRATE", type=int, dest="critThresh", help="Critical threshold", required=True)
parser.add_argument("-u", metavar="URL", dest="url", help="URL to pool's API (include port)", required=True)
parser.add_argument("-i", metavar="USERID", dest="userID", help="User ID (number).  Find this on the my account page.", required=True)
parser.add_argument("-k", metavar="APIKEY", dest="apiKey", help="API Key.  Find this on the my account page.", required=True)
parser.add_argument("-s", metavar="SCALE", type=int, dest="hashScale", help="Scaling factor for rashrate.  Default=1000 e.g. API returns hasherate in KH/s", default=1000)
parser.add_argument("--worker", metavar="WORKERNAME", dest="workerName", help="Query the hashrate for a single worker named WORKERNAME", default=None)



args = parser.parse_args()

# Verify parameters passed in

warnThresh = args.warnThresh
critThresh = args.critThresh
url = args.url.rstrip("/") + "/index.php"
userID = args.userID
apiKey = args.apiKey
hashScale = args.hashScale
workerName = args.workerName

if warnThresh < critThresh:
	print "Error: Warning threshold must be greater than critical threshold"
	sys.exit(3)


# Variables
exitCode=3
headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}



urlParams = dict (
	page="api",
	api_key=apiKey,
	id=userID,
	action="getdashboarddata"
)

if workerName!=None:
	urlParams['action']="getuserworkers"


# Get the data & parse it

response = requests.get(url=url, params=urlParams)

if response.status_code == requests.codes.ok:
	apiData = response.json()
	
	# Extract the relevant hashrate data	
	if urlParams['action']=="getuserworkers":
		workerData = filter(lambda worker: worker['username']==workerName, apiData["getuserworkers"]["data"])
		if not workerData:
			exitCode=3
			print "Error - Worker name not found"
			sys.exit(exitCode)
		
		hashRate=workerData[0]["hashrate"]
		

	elif urlParams['action']=="getdashboarddata":
		hashRate = apiData["getdashboarddata"]["data"]["personal"]["hashrate"]
	else:
		print "Error - Invalid API action requested"
		exitCode=3
		sys.exit(exitCode)

	
	# Evaluate the returned data to determine our monitor state & ouput
	hashRate = round(hashRate * hashScale)

	# TODO add scaling for the textual output into Kh/s, MH/s.  Leave actual perfdata as H/s for proper graphing
	if hashRate < critThresh:
		exitCode=2
		output="Critical - Hash rate: {} H/s".format(hashRate)
	elif hashRate < warnThresh:
		exitCode=1
		output="Warning - Hash rate: {} H/s".format(hashRate)
	else:
		exitCode=0
		output="OK - Hash rate: {} H/s".format(hashRate)

	output += " | Hashrate={};{};{};;".format(hashRate, warnThresh, critThresh)
	print output

else:
	exitCode=3
	print "HTTP Error: {}".format(response.status_code)

sys.exit(exitCode)
