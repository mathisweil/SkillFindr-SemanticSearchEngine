import pandas as pd
from datetime import datetime

from utils.config import load_config

config = load_config()
current_date = datetime.now().strftime("%Y-%m-%d")

df = pd.read_json(f"../{config['raw_output_path']}/{config['output_filename']}_{current_date}.json")
print(df.shape)

df = df.drop_duplicates(subset=["course_url"])

print(df.shape)
