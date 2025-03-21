import json
import re
from collections import Counter
from datetime import datetime

from utils.config import load_config
import pandas as pd


config = load_config()
current_date = datetime.now().strftime("%Y-%m-%d")

df = pd.read_json(f"../{config['raw_output_path']}/{config['output_filename']}_2025-03-12.json")


def extract_boilerplate_and_languages(filenames):
    all_lines = []

    # Load each JSON file and split each course description into lines
    for file in filenames:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            # each data item is a course description string
            for item in data:
                lines = item.split("\n")
                for line in lines:
                    line = line.strip()
                    if line:  # ignore empty lines
                        all_lines.append(line)

    # Count how often each line appears
    line_counts = Counter(all_lines)

    # We'll define boilerplate lines as those that appear more than once
    # We'll also collect any line mentioning 'language(s)' separately
    boilerplate = []
    languages = []

    for line, count in line_counts.items():
        # If repeated multiple times, consider it boilerplate
        if count > 1:
            boilerplate.append(line)

        # If the line mentions 'language(s)' or 'Language(s):' treat it as a "languages" line
        # This is just a simple regex check; adjust as needed
        if re.search(r"\blanguage(s)?\b", line, re.IGNORECASE):
            languages.append(line)

    return boilerplate, languages


# Example usage:
files = [
    "../description_temp/cybersecurity_desc.json",
    "../description_temp/data_science_desc.json",
    "../description_temp/web_development_desc.json"
]

boilerplate_lines, language_lines = extract_boilerplate_and_languages(files)

print("BOILERPLATE = [")
for b in sorted(boilerplate_lines):
    print(f"    {repr(b)},")
print("]\n")

print("LANGUAGES = [")
for l in sorted(language_lines):
    print(f"    {repr(l)},")
print("]")
