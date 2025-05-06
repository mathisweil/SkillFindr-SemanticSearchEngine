import os
import json
import csv
from pathlib import Path

from dotenv import load_dotenv

from embedding.retrieve_courses import semantic_search, keyword_search
from embedding.model_loader import load_embedding_model
from config.config import get_database_engine


def annotate_courses(query_set: list[str], model, engine) -> dict:
    test_dataset = {}

    for query in query_set:
        print(f"\n=== Query: '{query}' ===\n")

        courses_semantic = semantic_search(query, model, engine, threshold=0.5, limit=20)
        courses_bm25 = keyword_search(query, engine, threshold=0.05, limit=20)

        combined_courses = courses_semantic + courses_bm25
        seen_ids = set()
        unique_courses = []

        for course in combined_courses:
            course_id = course['course_id']
            if course_id and course_id not in seen_ids:
                seen_ids.add(course_id)
                unique_courses.append(course)

        annotations = []
        for idx, course in enumerate(unique_courses, 1):
            print(f"{idx}. Title: {course['title']}")
            print(f"   URL: {course['course_url']}")
            while True:
                try:
                    relevance = int(input("   Relevance (0=Not relevant, 1=Relevant, 2=Highly Relevant): "))
                    if relevance in {0, 1, 2}:
                        break
                    else:
                        print("Please enter 0, 1, or 2.")
                except ValueError:
                    print("Invalid input. Please enter an integer 0, 1, or 2.")

            annotations.append({
                "course_id": course['course_id'],
                "relevance": relevance
            })

        if query in test_dataset:
            test_dataset[query].extend(annotations)
        else:
            test_dataset[query] = annotations

    return test_dataset


if __name__ == "__main__":
    load_dotenv()
    BASE_DIR = Path(__file__).resolve().parent.parent
    model = load_embedding_model(os.getenv("EMBEDDING_MODEL_NAME"))
    engine = get_database_engine(os.getenv("DATABASE_URL"))

    TEST_QUERIES_PATH = BASE_DIR / os.getenv("TEST_QUERIES_PATH", "datasets/ir_test_queries.csv")
    with open(TEST_QUERIES_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        query_set = [row["query"] for row in reader]

    test_dataset = annotate_courses(query_set, model, engine)

    OUTPUT_PATH = BASE_DIR / os.getenv("TEST_DATASET_PATH", "datasets/test_dataset.json")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(test_dataset, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Test dataset saved successfully to: {OUTPUT_PATH}")
