#!/usr/bin/python3
# Copyright (c) 2018 Po Huit
# [This program is licensed under the "MIT License"]
# Please see the file LICENSE in the source
# distribution of this software for license terms.


# Measure skill injector, skill extractor and PLEX prices
# on a regular basis.

# Measurement interval (hours, minimum 1).
measurement_interval = 1
# Region for market history.
market_region = "The Forge"

import http.client as client
import json
from sys import stdout, stderr
import time
import urllib.parse

# Where to fetch the maps from.
esi_endpoint = "esi.tech.ccp.is"
# What version to fetch.
esi_version = "latest"
# Number of retries before giving up.
max_retries = 5
# How long to wait between retries (secs).
retry_timeout = 5.0
# How long to wait before reopening the connection (secs).
reopen_timeout = 5.0
# Maximum request rate (reqs/sec).
request_rate = 10.0

connection = None

def open_connection():
    global connection
    if connection != None:
        connection.close()
    connection = client.HTTPSConnection(esi_endpoint)

def close_connection():
    global connection
    if connection != None:
        connection.close()
    connection = None

def ccp_request(path, **kwargs):
    "Make an ESI request."
    global connection
    if connection == None:
        open_connection()
    url = "/" + esi_version + "/" + path + "/"
    if kwargs != None:
        url += "?" + urllib.parse.urlencode(kwargs)
    for retries in range(max_retries):
        try:
            if retries == 1:
                time.sleep(reopen_timeout)
                open_connection()
            else:
                time.sleep(1.0/request_rate)
            connection.request('GET', url)
            response = connection.getresponse()
            if response.status == 200:
                try:
                    return json.load(response)
                except json.decoder.JSONDecodeError as e:
                    print("json error: ", e, file=stderr)
            else:
                print("bad response status: ", response.status, file=stderr)
        except client.ResponseNotReady as e:
            print("http error: ", e, file=stderr)
            open_connection()
        except client.HTTPException as e:
            print("http error: ", e.code, file=stderr)
        if retries < max_retries - 1:
            time.sleep(retry_timeout)
    print("fetch failed for", url, file=stderr)
    return None


# Find the typeIDs we need.

print("Fetching region ID", file=stderr)
regionID = ccp_request("search",
                       categories="region",
                       strict="true",
                       search=market_region)
if regionID == None:
    print("Failed to communicate with server: giving up", file=stderr)
    exit(1)
if len(regionID) == 0:
    print("Bad region name: giving up", file=stderr)
    exit(1)
regionID = regionID['region'][0]

print("Fetching type IDs", file=stderr)
typeIDs = dict()
items = (
    "PLEX",
    "Large Skill Injector",
    "Skill Extractor",
)
for name in items:
    typeID = ccp_request("search",
                         categories="inventory_type",
                         strict="true",
                         search=name)
    if typeID == None:
        print("Failed to communicate with server: giving up", file=stderr)
        exit(1)
    typeIDs[name] = typeID['inventory_type'][0]


# Hit the market history endpoint, then sleep for a while.
print("Starting service", file=stderr)
while True:
    for name in typeIDs:
        market_history = ccp_request("markets/{}/history".format(regionID),
                                     type_id = typeIDs[name])
        if market_history == None:
            print("Could not retrieve market history, retrying in 1h",
                  file=stderr)
            close_connection()
            time.sleep(60*60)
            continue
        latest = market_history[-1]
        print("market history:", name, latest['date'], latest['average'])
    close_connection()
    time.sleep(measurement_interval * 60 * 60)
