import requests
import json
import os
import random
import time
import schedule
import logging
from database_operations import (
    create_database_connection,
    create_air_quality_table,
    insert_air_quality_data,
    update_location_in_database,
    check_if_location_exists,
)

API_KEY = "f5fbf7aa-06a3-403a-8e34-906a773a4d8a" # Replace with your api key.
LOCATIONS_FILE = "locations.json"  # Configuration file for locations

# Logging setup (moved to here to avoid multiple setups)
logging.basicConfig(
    filename="air_quality_retrieval.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
def load_locations():
    """Loads locations from the locations.json file."""
    try:
        with open(LOCATIONS_FILE, "r") as f:
            locations = json.load(f)
        return locations
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading locations: {e}")
        return []

def get_air_quality_data(latitude, longitude, max_retries=5, backoff_factor=1):
    """Retrieves air quality data from the AirVisual API with retry and exponential backoff"""
    url = f"https://api.airvisual.com/v2/nearest_city?lat={latitude}&lon={longitude}&key={API_KEY}"
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            return data
        except requests.exceptions.RequestException as e:
            if response.status_code == 429:
                print(f"API request failed (429): {e}, retrying...")
            else:
                print(f"API request failed: {e}, retrying...")
            retries += 1
            delay = (backoff_factor * (2 ** retries)) + random.random()  # Exponential backoff + jitter
            time.sleep(delay)
    print("Max retries exceeded. API request failed.")
    return None

def process_air_quality_data(api_data, location_data):
    """Processes the API response into a dictionary."""
    if not api_data or api_data.get("status") != "success":
        logging.warning(f"Invalid API data: {api_data}")
        return None

    try:
        pollution_data = api_data["data"]["current"]["pollution"]
        weather_data = api_data["data"]["current"]["weather"]
        location_coords = api_data["data"]["location"]["coordinates"]
        city_name = api_data["data"]["city"]
        state_name = api_data["data"].get("state", "Unknown")
        country_name = api_data["data"].get("country", "Unknown")
        station_name = api_data["data"].get("location", {}).get("name", "Unknown")

        processed_data = {
            "timestamp": pollution_data["ts"],
            "latitude": location_coords[1],
            "longitude": location_coords[0],
            "city": city_name,
            "state": state_name,
            "country": country_name,
            "aqi": pollution_data["aqius"],
            "main_pollutant": pollution_data["mainus"],
            "pm25": pollution_data.get("pm25", None),  # Handle missing pollutants
            "pm10": pollution_data.get("pm10", None),
            "o3": pollution_data.get("o3", None),
            "no2": pollution_data.get("no2", None),
            "so2": pollution_data.get("so2", None),
            "co": pollution_data.get("co", None),
            "temperature": weather_data["tp"],
            "humidity": weather_data["hu"],
            "wind_speed": weather_data["ws"],
            "wind_direction": weather_data["wd"],
            "pressure": weather_data["pr"],
            "station_name": station_name,
        }
        print("Processed Data:", processed_data)
        return processed_data
    except KeyError as e:
        logging.error(f"KeyError processing data: {e}, Data: {api_data}")
        return None
def fetch_and_store_data():
    """Fetches air quality data for all locations and stores it in the database."""
    conn = create_database_connection("data/raw/air_quality_data.db")
    if conn:
        create_air_quality_table(conn)
        locations = load_locations()  # Load locations from JSON file

        for location_data in locations:
            latitude = location_data["latitude"]
            longitude = location_data["longitude"]
            location_name = location_data["name"]
            original_location_name = location_data.get("original_name", location_name) #gets original name

            api_data = get_air_quality_data(latitude, longitude)
            if api_data:
                processed_data = process_air_quality_data(api_data, location_name)
                if processed_data:
                    #check if location exists.
                    if check_if_location_exists(conn, original_location_name):
                        #update location.
                        update_location_in_database(conn, {"latitude": latitude, "longitude": longitude, "name": location_name, "original_name": original_location_name})
                    insert_air_quality_data(conn, processed_data)
                else:
                    logging.warning(
                        f"Failed to process data for {location_name} (Lat: {latitude}, Lon: {longitude})"
                    )
            else:
                logging.warning(
                    f"Failed to retrieve data for {location_name} (Lat: {latitude}, Lon: {longitude})"
                )
        conn.close()
    else:
        logging.error("Failed to connect to the database.")

def run_scheduler():
    """Runs the scheduler to fetch and store data hourly."""
    schedule.every().hour.do(fetch_and_store_data)
    logging.info("Scheduler started. Running hourly.")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    db_path = os.path.join("data", "raw", "air_quality_data.db")
    conn = create_database_connection(db_path)
    fetch_and_store_data() # For testing, run once
    run_scheduler()  # Start the scheduler