import subprocess

# subprocess.run(["python", "scrapers/IBM_scraper.py"])
subprocess.run(["python", "parsers/data_cleaner.py"])
subprocess.run(["python", "embedding/embed_courses.py"])
subprocess.run(["python", "database/store_to_pgvector.py"])
