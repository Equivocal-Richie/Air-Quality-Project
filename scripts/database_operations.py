import sqlite3
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
            );
        """)
        conn.commit()
        print("Air Quality Table Created")
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")


def insert_air_quality_data(conn, data):
    """Inserts air quality data into the database."""
    try:
        df = pd.DataFrame([data])
        df.to_sql('air_quality', conn, if_exists='append', index=False)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error inserting data: {e}")
