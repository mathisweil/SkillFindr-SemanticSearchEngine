import pandas as pd
import logging

def process_with_pandas(courses, output_file):
    """
    Cleans scraped course data using Pandas:
    - Removes duplicates
    - Fills missing values
    - Converts data types
    - Standardizes formatting
    - Filters low-quality courses (optional)
    - Saves final dataset as CSV & JSON

    :param courses: List of dictionaries containing course data.
    :param output_file: Filename for CSV output.
    :return: Cleaned list of course dictionaries.
    """
    if not courses:
        logging.warning("No courses to process.")
        return []

    df = pd.DataFrame(courses)

    # 1️⃣ Remove duplicate courses based on unique course URL
    df = df.drop_duplicates(subset=["course_url"])

    # 2️⃣ Handle missing values
    df.fillna({"description": "No description available", "duration": 0}, inplace=True)

    # 3️⃣ Convert numerical fields safely
    df["learners_amount"] = pd.to_numeric(df["learners_amount"], errors="coerce").fillna(0).astype(int)
    df["star_rating"] = pd.to_numeric(df["star_rating"], errors="coerce").fillna(0.0)

    # 4️⃣ Standardize text formatting
    df["title"] = df["title"].str.strip().str.title()
    df["description"] = df["description"].str.replace(r'\s+', ' ', regex=True).str.strip()

    # 5️⃣ Ensure tags are stored as lists
    df["tags"] = df["tags"].apply(lambda x: x if isinstance(x, list) else [])

    # 7️⃣ Sort by popularity (learners first, then rating)
    df = df.sort_values(by=["learners_amount", "star_rating"], ascending=[False, False])

    # Save cleaned dataset
    df.to_csv(f"{output_file}.csv", index=False)
    df.to_json(f"{output_file}.json", orient="records", indent=4)
    logging.info(f"Data successfully saved")

    return df.to_dict(orient="records")
