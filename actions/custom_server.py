from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Tracker
#from actions import actions
import requests
import json
import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('API_KEY')

def specify_place(location):

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json?"
    #location = "Azəriqaz Metrologiya Departamenti"
    params = {
            'query': location,
            'radius': '1000',
            'key': api_key
            }

    respons = requests.get(url, params=params)
    res = respons.json()['results']
    # print(respons.json())
    if not res:
        print("Place not found")
        return "Place not found"
    coordinate = str(res[0]['geometry']['location']['lat']) + ", " + str(res[0]['geometry']['location']['lng'])
    return coordinate

    

def webhook(coordinate, loc_name):
    api_endpt = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?address={loc_name}"
#    location = location.resplace(" ", "%20")
    # location = specify_place(place)
    # print(location)
    radius="1000"
    keyword="restaurant"
    key = api_key
    params = {
            "location": coordinate,
            "radius": radius,
            "keyword": keyword,
            "key": key
            }
    response = requests.get(api_endpt, params=params)
    res = response.json()
    final = []

    for i in res["results"]:
        items = {}
        items['lat'] = i['geometry']['location']['lat']
        items['lng'] = i['geometry']['location']['lng']
        items['location'] = i['geometry']['location']
        items['name'] = i['name']
        items['business_status'] = i['business_status']
        items['place_id'] = i['place_id']
        items['rating'] = i['rating']
        items['user_ratings_total'] = i['user_ratings_total']
        items['vicinity'] = i['vicinity']
        final.append(items)
    #print(final)
    return final

#print(webhook("Azəriqaz Metrologiya Departamenti"))

