from flask import Blueprint, jsonify, request
import random
import requests
import os

# Load API Key from environment variable

API_KEY = os.getenv("GOOGLE_MAPS_KEY")

script_bp = Blueprint('script', __name__)

@script_bp.route('/api/cv', methods=['GET'])
# Helper Functions
def get_user_address():
    response = requests.get("https://ipinfo.io/json")
    data = response.json()
    if "loc" in data:
        lat, lng = map(float, data["loc"].split(","))
        return f"{lng},{lat}"
    
def get_coordinates(address):
	base_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={API_KEY}"
	response = requests.get(base_url)
	if response.status_code == 200: 
		data = response.json()
		if data["status"] == "OK" and "results" in data and len(data["results"]) > 0:
			location = data["results"][0]["geometry"]["location"]
			latitude = location["lat"]
			longitude = location["lng"]
			return f"{longitude},{latitude}"

def get_route(start, end, mode):
	base_url = f"http://router.project-osrm.org/route/v1/{mode}/{start};{end}?overview=false"

	response = requests.get(base_url)

	if response.status_code == 200:
		data = response.json()
		if "routes" in data and data["routes"]:
			distance = data["routes"][0]["distance"] / 1609
			duration = data["routes"][0]["duration"] / 60
			print(f"Distance: {distance:.2f} miles")
			print(f"Estimated Time: {duration:.2f} minutes")
			return data["routes"][0]["distance"] / 1609
		else:
			print("No routes found.")
	else:
		print("Error fetching route:", response.status_code)
  
  
def addresses_to_dist(address1, address2):
    ptA = get_coordinates(address1)
    ptB = get_coordinates(address2)
    return get_route(ptA, ptB, "driving")

def from_start_dist(start, address2):
    ptB = get_coordinates(address2)
    return get_route(start, ptB, "driving")
    
def find_costs(start, stores):
    n = len(stores)
    costs = {}
    for i in range(n):
        d = from_start_dist(start, stores[i])
        costs[frozenset([start, stores[i]])] = d
    
    for i in range(n):
        for j in range(i + 1, n): 
            d = addresses_to_dist(stores[i], stores[j])
            costs[frozenset([stores[i], stores[j]])] = d       
    return costs

def greedy_set_cover(start, stores_inventory, costs, grocery_set):
	path = []
	bought_groceries = set()
	cur_loc = start
	
	# keep iterating if we haven't bought all the groceries yet
	while frozenset(bought_groceries) != grocery_set:
     
		# find which things has the minimum cost per new grocery item
		min_groc_cost = float("inf")
		min_cost_store = random.choice(list(stores_inventory.keys()))
		needed_groceries = grocery_set.difference(bought_groceries)

		for store in stores_inventory.keys():
			# calculate cost per new grocery item
			new_groceries = needed_groceries.intersection(stores_inventory[store])
			if len(new_groceries) == 0:
				continue

			cur_cost = costs[frozenset([cur_loc, store])]
			new_groc_cost = cur_cost / len(new_groceries)

			if min_groc_cost > new_groc_cost:
				min_groc_cost = new_groc_cost
				min_cost_store = store

		# By now, we should have picked our new
		new_groceries = frozenset(needed_groceries.intersection(stores_inventory[min_cost_store]))
		bought_groceries = bought_groceries.union(new_groceries)
		path.append(min_cost_store)
   
		# delete store from stores
		del stores_inventory[min_cost_store]
	# return the final path of what stores to reach
	return path

def get_path(addresses, stores_inventory, grocery_set):
    start = get_user_address()
    costs = find_costs(start, addresses)
    path = greedy_set_cover(start, stores_inventory, costs, grocery_set)
    return path



# stores_lst = [
#     "49 White St, Cambridge, MA 02140", 
#     "47 Mount Auburn St, Cambridge, MA 02140",
#     "6 John F. Kennedy St, Cambridge, MA 02140"
# ] 

# coords = [get_coordinates(store) for store in stores_lst]

# start = get_user_address()

# inventory = [
# 	frozenset(["apple", "egg"]),
#  	frozenset(["milk"]),
#   	frozenset(["fish", "avocado", "apple", "yams", "banana"])
# ]

# stores_inventory = {}
# for i in range(len(coords)):
#     stores_inventory[stores_lst[i]] = inventory[i] 

# grocery_set = frozenset(
#     ["apple", "yams", "milk"]
# )

# costs = find_costs(start, stores_lst)
# path = greedy_set_cover(start, stores_inventory, costs, grocery_set)
# print(path)
