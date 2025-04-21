import subprocess
import sys

def run_pipeline():
    # subprocess.run([sys.executable, "scrapers/IBM_scraper.py"], check=True)
    subprocess.run([sys.executable, "parsers/process_courses.py"], check=True)
    subprocess.run([sys.executable, "database/insert_into_db.py"], check=True)

if __name__ == "__main__":
    run_pipeline()
