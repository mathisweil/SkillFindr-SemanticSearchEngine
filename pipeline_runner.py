import subprocess

# subprocess.run(["python", "scrapers/IBM_scraper.py"])
subprocess.run(["python", "parsers/data_cleaner.py"])
subprocess.run(["python", "database/insert_into_db.py"])
