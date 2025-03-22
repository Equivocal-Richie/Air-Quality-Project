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
    insert_air_quality_data
)

API_KEY = "f5fbf7aa-06a3-403a-8e34-906a773a4d8a" # Replace with your api key.

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

        processed_data = {
            'timestamp': measurements['ts'],
            'latitude': location['coordinates'][1],
            'longitude': location['coordinates'][0],
            'city': location.get('city', 'Unknown'),  # Use .get() with a default value
            'state': location.get('state', 'Unknown'),#added .get()
            'country': location.get('country', 'Unknown'), #added .get()
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
        print("Processed Data:", processed_data) # Add this line
        return processed_data
    else:
        print("process_air_quality_data: data was invalid")
        return None


if __name__ == "__main__":
    db_path = os.path.join("data", "raw", "air_quality_data.db")
    conn = create_database_connection(db_path)
    if conn:
        create_air_quality_table(conn)
        locations = [
            {"latitude": 34.0522, "longitude": -118.2437},  # Los Angeles
            {"latitude": 35.6895, "longitude": 139.6917},  # Tokyo
            {"latitude": 51.5074, "longitude": -0.1278},  # London
            {"latitude": 19.4326, "longitude": -99.1332},  # Mexico City
            {"latitude": -1.2921, "longitude": 36.8219},  # Nairobi
        ]

        for location in locations:
            latitude = location["latitude"]
            longitude = location["longitude"]
            api_data = get_air_quality_data(latitude, longitude)
            if api_data:
                processed_data = process_air_quality_data(api_data)
                if processed_data:
                    insert_air_quality_data(conn, processed_data)
            time.sleep(1)  # add a 1-second delay to avoid rate limiting.
        conn.close()