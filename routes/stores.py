from flask import Blueprint, request, jsonify
import os
import openai
import base64
import re
import pandas as pd
from supabase import create_client

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Create Flask Blueprint
stores_bp = Blueprint("stores", __name__)

@stores_bp.route("/api/cv", methods=["GET"])
def main():
    """Handles grocery list extraction and processing."""
    food_img = request.args.get("food_img")
    location = request.args.get("location")

    if not food_img:
        return jsonify({"error": "Missing food image"}), 400

    grocery_list = image_to_grocery_list(food_img)

    if not grocery_list:
        return jsonify({"error": "No grocery items detected"}), 400

    grocery_set = frozenset(grocery_list)
    result = get_path(grocery_set=grocery_set)  # Assuming this function exists

    return jsonify({"grocery_list": list(grocery_set), "result": result})


def image_to_grocery_list(image_path):
    """Extracts grocery items from an image using GPT-4o."""
    try:
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract items from this grocery list image."},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_data}},
                    ],
                }
            ],
        )

        return [item.strip() for item in response.choices[0].message.content.lower().split(",")]

    except Exception as e:
        return []


def find_best_match(item_name, market_items):
    """Finds the best match for a grocery item in a store's inventory."""
    def is_valid_match(item, match):
        """Checks if every word in the item appears in the match."""
        return all(word in match.lower() for word in item.lower().split())

    for match in market_items:
        if is_valid_match(item_name, match):
            return match

    return None  # No match found


def find_item_in_market(item_name, market_id):
    """Finds an item in a specific market."""
    market_items_query = supabase.table("items").select("item_name", "price", "unit_of_measurement").eq("market_id", market_id).execute()
    
    if not market_items_query.data:
        return None

    market_items = [item["item_name"] for item in market_items_query.data]
    best_match = find_best_match(item_name, market_items)

    if best_match:
        return next(item for item in market_items_query.data if item["item_name"] == best_match)

    return None


def build_grocery_price_dataset(grocery_list):
    """Builds a dataset of grocery prices across different markets."""
    markets_query = supabase.table("market").select("id", "market_name", "address_name").execute()

    if not markets_query.data:
        return pd.DataFrame()

    markets = markets_query.data
    data = []

    for item in grocery_list:
        for market in markets:
            market_id = market["id"]
            market_name = market["market_name"]
            address = market["address_name"]

            item_data = find_item_in_market(item, market_id)

            data.append({
                "Item": item_data["item_name"] if item_data else item,
                "Market": market_name,
                "Market ID": market_id,
                "Address": address,
                "Price": item_data["price"] if item_data else None,
                "Unit": item_data["unit_of_measurement"] if item_data else None,
            })

    return pd.DataFrame(data)


@stores_bp.route("/api/markets", methods=["GET"])
def get_market_items():
    """Returns a list of market addresses."""
    market_items_query = supabase.table("market").select("address_name").execute()
    
    if not market_items_query.data:
        return jsonify({"markets": []})

    return jsonify({"markets": [m["address_name"] for m in market_items_query.data]})
