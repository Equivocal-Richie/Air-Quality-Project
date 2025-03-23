import sqlite3
import logging
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
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO air_quality (
                timestamp, latitude, longitude, city, state, country,
                aqi, main_pollutant, pm25, pm10, o3, no2, so2, co,
                temperature, humidity, wind_speed, wind_direction, pressure
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["timestamp"],
                data["latitude"],
                data["longitude"],
                data["city"],
                data["state"],
                data["country"],
                data["aqi"],
                data["main_pollutant"],
                data["pm25"],
                data["pm10"],
                data["o3"],
                data["no2"],
                data["so2"],
                data["co"],
                data["temperature"],
                data["humidity"],
                data["wind_speed"],
                data["wind_direction"],
                data["pressure"],
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise e
    except Exception as e:
        logging.error(f"Database Error: {e}")
        raise e

def remove_duplicate_data(conn): #added function
    """Removes duplicate air quality data from the database."""
    try:
        sql_delete_duplicates = """
            DELETE FROM air_quality
            WHERE rowid NOT IN (
                SELECT MIN(rowid)
                FROM air_quality
                GROUP BY timestamp, latitude, longitude, city, state, country, aqi, main_pollutant, pm25, pm10, o3, no2, so2, co, temperature, humidity, wind_speed, wind_direction, pressure
            );
        """
        cur = conn.cursor()
        cur.execute(sql_delete_duplicates)
        conn.commit()
        logging.info("Duplicate data removed.")
    except sqlite3.Error as e:
        logging.error(f"Error removing duplicate data: {e}")