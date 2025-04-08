# scripts/automation.py
import subprocess
import schedule
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_api_retrieval():
    logging.info("Running api_retrieval.py...")
    subprocess.run(['python', 'scripts/api_retrieval.py'])

def run_data_cleaning():
    logging.info("Running data_cleaning.py...")
    subprocess.run(['python', 'scripts/data_cleaning.py'])

def run_feature_engineering():
    logging.info("Running feature_engineering.py...")
    subprocess.run(['python', 'scripts/feature_engineering.py'])

def run_model():
    logging.info("Running model.py...")
    subprocess.run(['python', 'scripts/model.py'])

def run_pipeline():
    run_api_retrieval()
    run_data_cleaning()
    run_feature_engineering()
    # run_model()  # Uncomment when ready

# Schedule the pipeline to run hourly (or as needed)
schedule.every().hour.at(":00").do(run_pipeline)

while True:
    schedule.run_pending()
    time.sleep(1)