import pandas as pd
import sqlite3
import os
import numpy as np
import logging
import smtplib
from email.mime.text import MIMEText
import datetime

from dotenv import load_dotenv

load_dotenv() # Load the env file with the email logins

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_data_from_sqlite(db_path):
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM air_quality"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

script_dir = os.path.dirname(os.path.abspath(__file__)) #Get the script Directory
db_path = os.path.join(script_dir, "..", "data", "raw", "air_quality_data.db")

df = load_data_from_sqlite(db_path)



# ... (Data Cleaning Logic) ...

# 1. Outlier Handling and Data Cleaning Logic

# Drop empty columns
df = df.drop(['o3', 'no2', 'so2', 'co'], axis=1)

# Timestamp conversion
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Remove redundant ID column
df = df.drop('id', axis=1)

# Handle Duplicates
df = df.drop_duplicates()

# Handle Inconsistencies
df['city'] = df['city'].str.strip()

# Outlier Handling
def robust_cap_floor(series, cap_multiplier=3, floor_multiplier=3):
    median = series.median()
    mad = np.median(np.abs(series - median))
    cap = median + cap_multiplier * mad
    floor = median - floor_multiplier * mad
    return series.apply(lambda x: min(max(x, floor), cap))

# Apply robust capping/flooring to numerical columns
numerical_cols = df.select_dtypes(include=['number']).columns
for col in numerical_cols:
    df[col] = robust_cap_floor(df[col])

# Conditional Outlier Handling
# AQI, PM25, PM10 (High-end outliers are valid pollution events)
for col in ['aqi', 'pm25', 'pm10']:
    df[col] = df[col].apply(lambda x: x if x <= df[col].quantile(0.99) else df[col].quantile(0.99))

# Humidity (Low end is valid)
df['humidity'] = df['humidity'].apply(lambda x: x if x >= 0 else 0)

# Wind Speed (High end is valid)
df['wind_speed'] = df['wind_speed'].apply(lambda x: x if x <= df['wind_speed'].quantile(0.99) else df['wind_speed'].quantile(0.99))

# Pressure (Low end is valid)
df['pressure'] = df['pressure'].apply(lambda x: x if x >= df['pressure'].quantile(0.01) else df['pressure'].quantile(0.01))

# Store the cleaned data as a csv file
df.to_csv('data/processed/cleaned_data.csv', index=False)



# 2. Data Validation and Alerting
def validate_data(df):
    checks = {
        'timestamp': df['timestamp'].isnull().sum() == 0,
        'aqi_range': df['aqi'].min() >= 0,
        'pm25_range': df['pm25'].min() >= 0,
        'pm10_range': df['pm10'].min() >= 0,
        'humidity_range': df['humidity'].between(0, 100).all(),
        'wind_direction_range': df['wind_direction'].between(0, 360).all(),
        'pressure_range': df['pressure'].min() > 900, # A logical minimum
    }
    return checks

def send_alert_email(message):
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    receiver_email = os.getenv("RECEIVER_EMAIL")

    msg = MIMEText(message)
    msg['Subject'] = "Data Inconsistency Alert"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        logging.info("Alert email sent successfully.")
    except Exception as e:
        logging.error(f"Failed to send alert email: {e}")

def check_for_inconsistencies(df):
    validation_results = validate_data(df)
    error_messages = []
    for check, result in validation_results.items():
        if not result:
            error_messages.append(f"Data validation failed: {check} ({get_error_details(df, check)})")
            logging.error(f"Data validation failed: {check} ({get_error_details(df, check)})")
    if error_messages:
        alert_message = "Wagwan Data Scientist,\n\n"
        alert_message += "This is an automated alert from the Air Quality Project data pipeline.\n\n"
        alert_message += "The following data inconsistencies have been detected during the validation process:\n\n"
        alert_message += "\n".join([f"- {msg}" for msg in error_messages])
        alert_message += f"\n\nTimestamp of alert: {datetime.datetime.utcnow()} (UTC)\n\n"
        alert_message += "Sincerely,\n\nThe Air Quality Project Automated Alert System"
        alert_message += "\n\nYour buoy Richie🐣"
        send_alert_email(alert_message)

def get_error_details(df, check):
    if check == 'timestamp':
        return f"Null timestamps found: {df['timestamp'].isnull().sum()}"
    elif check == 'aqi_range':
        return f"Min AQI: {df['aqi'].min()}"
    elif check == 'pm25_range':
        return f"Min PM25: {df['pm25'].min()}"
    elif check == 'pm10_range':
        return f"Min PM10: {df['pm10'].min()}"
    elif check == 'humidity_range':
        return f"Humidity values outside 0-100 range: {df[~df['humidity'].between(0, 100)].shape[0]} rows"
    elif check == 'wind_direction_range':
        return f"Wind direction values outside 0-360 range: {df[~df['wind_direction'].between(0, 360)].shape[0]} rows"
    elif check == 'pressure_range':
        return f"Min Pressure: {df['pressure'].min()}"
    return "Details not available"

check_for_inconsistencies(df)