
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import asyncio
from .custom_server import webhook
from .custom_server import specify_place
import requests
import math
import urllib
import requests
import urllib
from typing import List, Tuple, Dict

import os
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('API_KEY')


def haversine_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate the great-circle distance between two points on the Earth's surface.
    :param coord1: Tuple of latitude and longitude for the first point (lat, lon)
    :param coord2: Tuple of latitude and longitude for the second point (lat, lon)
    :return: Distance in kilometers
    """
    R = 6371  # Radius of the Earth in kilometers

    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

# A* sorting algorithm

def a_star_sort(
    current_location: Tuple[float, float],
    destinations: List[Dict[str, Tuple[float, float]]]
) -> List[Dict[str, Tuple[float, float]]]:
    """
    Sort destinations by their distance to the current location using A* algorithm.
    :param current_location: Current location as (latitude, longitude)
    :param destinations: List of destinations with their coordinates, e.g.,
                         [{'name': 'Restaurant A', 'coords': (lat, lon)}, ...]
    :return: Sorted list of destinations by distance
    """
    def heuristic(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Heuristic function to estimate cost (distance)."""
        return haversine_distance(coord1, coord2)

    # Compute distances using the heuristic and sort by distance
    for destination in destinations:
        destination["distance"] = heuristic(current_location, destination["coords"])

    # Sort destinations by computed distance
    sorted_destinations = sorted(destinations, key=lambda x: x["distance"])
    return sorted_destinations


def get_lat_long(location: str) -> Tuple[float, float]:
    geocode_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?inputtype=textquery&input={location}&key={api_key}"
    response = requests.get(geocode_url)
    data = response.json()
    place_id = data['candidates'][0]['place_id']
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name%2Cformatted_address%2Cgeometry&key={api_key}"
    response = requests.get(url)
    retrieved = response.json()

    if data['status'] == 'OK':
        lat = retrieved['result']['geometry']['location']['lat']
        lng = retrieved['result']['geometry']['location']['lng']
        return lat, lng
    else:
        return None, None

class ActionReturnName(Action):

    def name(self) -> Text:
        return "action_return_feed"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        location = tracker.get_slot("city")
        user_id = tracker.sender_id
        user_metadata = tracker.latest_message
        text_location = user_metadata.get('text')

        lat_lng = get_lat_long(text_location)

        # print(get_lat_long(location))
        coordinate = str(str(lat_lng[0]) + ", " + str(lat_lng[1]))

        if not location:
            dispatcher.utter_message(text="Please provide a location.")
            return []

        # try:
        #     current_loc = geocode_location(location)
        # except ValueError as e:
        #     dispatcher.utter_message(text=str(e))
        #     return []
                
        #temp = str(str(location[0]) + ",%20" + str(location[1]))
        res = webhook(coordinate, text_location)
        if not res or res == "Place not Found":
            dispatcher.utter_message(text="Place not found. Please try a different location.")
            return  []
        restaurant_data = []
        # current_loc = tuple(map(float, specify_place(location).split(',')))
        current_loc = lat_lng

        for i in res:
            restaurant_data.append({
                "name": i["name"],
                "coords": (i["lat"], i["lng"]),  # Correctly assign coords here
                "latitude": i["lat"],
                "longitude": i["lng"]
            })
        sorted_data = a_star_sort(current_loc, restaurant_data)
        # print(sorted_data)
        strn = "Here is the restaurants that are close to you:\n"
        cntr = 1
        for i in sorted_data:
            distance_in_km = i["distance"]
            # st = str('' + str(i['name']) + " \n" + str(i['user_ratings_total']) + " users rated " + str(i['rating']) + '\n' + ' The place is located in ' + i['vicinity']+'\n')
            # st = str('Name: ' + str(i["name"]) + " Distance:" + str(i['distance']) + "\n")
            if distance_in_km < 1:
                distance_in_meters = distance_in_km * 1000
                st = str(str(cntr) + ". " + str(i['name']) + " is " + str(round(distance_in_meters)) + " meters away.\n")

            else:
                st = str(str(cntr) + ". " + str(i['name']) + " is " + str(round(distance_in_km)) + " km away.\n")
            cntr = cntr + 1
            strn = strn + st

        dispatcher.utter_message(text=strn)

        return []

actions = {
        "action_return_feed": ActionReturnName()
        }

