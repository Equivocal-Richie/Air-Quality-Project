import subprocess
import schedule
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_script(script_name):
    try:
        logging.info(f"Running {script_name}...")
        subprocess.run(['python', script_name], check=True)
        logging.info(f"{script_name} executed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {script_name}: {e}")

def run_all_scripts():
    run_script('api_retrieval.py')
    run_script('data_cleaning.py')
    run_script('feature_engineering.py')
    run_script('model.py')
    logging.info("All scripts executed.")

# Schedule the pipeline to run hourly
schedule.every().hour.at(":00").do(run_all_scripts)

while True:
    schedule.run_pending()
    time.sleep(1)