import requests
import json
import os
import sqlite3
import time
import schedule
import logging
from database_operations import (
    create_database_connection,
    create_air_quality_table,
    insert_air_quality_data,
    remove_duplicate_data
)
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("API_KEY")
LOCATIONS_FILE = "locations.json" # Configuration file for locations

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_locations():
    """Loads locations from the locations.json file."""
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the full path to the locations.json file
        full_path = os.path.join(script_dir, "..", LOCATIONS_FILE)
        logging.info(f"Loading locations from: {full_path}")
        with open(full_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading locations: {e}")
        return []

def get_air_quality_data(latitude, longitude):
    """Retrieves air quality data from the AirVisual API."""
    url = f"https://api.airvisual.com/v2/nearest_city?lat={latitude}&lon={longitude}&key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None


def process_air_quality_data(data):
    """Processes the API response into a dictionary."""
    if data and data['status'] == 'success':
        city_data = data['data']
        measurements = city_data['current']['pollution']
        weather = city_data['current']['weather']
        location = city_data['location']

        # Extract city, state, and country from the root of the data
        city = city_data.get('city', 'Unknown')
        state = city_data.get('state', 'Unknown')
        country = city_data.get('country', 'Unknown')

        processed_data = {
            'timestamp': measurements['ts'],
            'latitude': location['coordinates'][1],
            'longitude': location['coordinates'][0],
            'city': city,
            'state': state,
            'country': country,
            'aqi': measurements['aqius'],
            'main_pollutant': measurements['mainus'],
            'pm25': measurements.get('aqicn', None),
            'pm10': measurements.get('aqius', None),
            'o3': measurements.get('o3', None),
            'no2': measurements.get('no2', None),
            'so2': measurements.get('so2', None),
            'co': measurements.get('co', None),
            'temperature': weather['tp'],
            'humidity': weather['hu'],
            'wind_speed': weather['ws'],
            'wind_direction': weather['wd'],
            'pressure': weather['pr']
        }
        print("Processed Data:", processed_data) # Print the processed batch
        return processed_data
    else:
        print("process_air_quality_data: data was invalid")
        return None

def fetch_and_store_data(location): #modified to accept one location
    """Fetches air quality data for the provided location and stores it in the database."""
    conn = create_database_connection("data/raw/air_quality_data.db")
    if conn:
        latitude = location["latitude"]
        longitude = location["longitude"]
        api_data = get_air_quality_data(latitude, longitude)
        if api_data:
            processed_data = process_air_quality_data(api_data)
            if processed_data:
                try:
                    insert_air_quality_data(conn, processed_data)
                except sqlite3.IntegrityError as e:
                    logging.warning(f"Database Integrity Error: {e}. Data not inserted: {processed_data}")
                except Exception as e:
                    logging.error(f"Database Error: {e}. Data not inserted: {processed_data}")
        remove_duplicate_data(conn)  # call to remove duplicates
        conn.close()
    else:
        logging.error("Failed to connect to the database.")


def run_scheduler():
    """Runs the scheduler to fetch and store data hourly."""
    all_locations = load_locations()
    if not all_locations:
        return

    interval_minutes = 60 / len(all_locations)  # Calculate interval.
    logging.info(f"Scheduling requests every {interval_minutes} minutes.")

    def schedule_requests():
        for i, location in enumerate(all_locations):
            minute_offset = i * interval_minutes
            schedule.every().hour.at(f":{int(minute_offset):02}") \
                .do(fetch_and_store_data, location)

    schedule_requests() # Schedule for the current hour.

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    conn = create_database_connection("data/raw/air_quality_data.db")
    if conn:
        create_air_quality_table(conn)
        conn.close()
        run_scheduler()
    else:
        logging.error("Failed to connect to the database.")