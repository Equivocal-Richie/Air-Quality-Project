import sqlite3
import logging
import pandas as pd
import os

def create_database_connection(db_file):
    """Creates a database connection to the SQLite database."""
    print(f"Attempting to connect to: {db_file}")
    conn = None
    try:
        # Get the directory of the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the full path to the database file
        full_path = os.path.join(script_dir,"..", db_file)
        print(f"Attempting to connect to: {full_path}")
        conn = sqlite3.connect(full_path)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    return conn

def create_air_quality_table(conn):
    """Creates the air quality data table in the database."""
    try:
        print("Creating table...")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS air_quality (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                latitude REAL,
                longitude REAL,
                city TEXT,
                state TEXT,
                country TEXT,
                aqi REAL,
                main_pollutant TEXT,
                pm25 REAL,
                pm10 REAL,
                o3 REAL,
                no2 REAL,
                so2 REAL,
                co REAL,
                temperature REAL,
                humidity REAL,
                wind_speed REAL,
                wind_direction REAL,
                pressure REAL
                station_name TEXT
            );
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON air_quality (timestamp);")
        conn.commit()
        logging.info("Air Quality Table Created")
    except sqlite3.Error as e:
        logging.error(f"Error creating table: {e}")


def insert_air_quality_data(conn, data):
    """Inserts air quality data into the database, checking for duplicates."""
    try:
        df = pd.DataFrame([data])
        df.to_sql('air_quality', conn, if_exists='append', index=False)
        conn.commit()
        logging.info(f"Inserted data for timestamp: {data['timestamp']}")
    except sqlite3.Error as e:
        logging.error(f"Error inserting data: {e}")
        logging.error(f"Data that caused error: {data}")
def update_location_in_database(conn, location_data):
    """
    Updates location information (name, coordinates) in the database.
    This function is crucial for handling changes in station names or coordinates.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE air_quality
            SET latitude = ?, longitude = ?, city = ?
            WHERE station_name = ?;
            """,
            (
                location_data["latitude"],
                location_data["longitude"],
                location_data["name"],
                location_data["original_name"],  # Use original name to find the record
            ),
        )
        conn.commit()
        if cursor.rowcount > 0:
            logging.info(
                f"Updated location for station: {location_data['original_name']} to {location_data['name']}"
            )
        else:
            logging.info(
                f"Location not found for station: {location_data['original_name']}.  No update performed."
            )
    except sqlite3.Error as e:
        logging.error(f"Error updating location: {e}")

def check_if_location_exists(conn, station_name):
    """Checks if a location exists in the database."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM air_quality WHERE station_name = ?;
            """,
            (station_name,),
        )
        count = cursor.fetchone()[0]
        return count > 0
    except sqlite3.Error as e:
        logging.error(f"Error checking location existence: {e}")
        return False