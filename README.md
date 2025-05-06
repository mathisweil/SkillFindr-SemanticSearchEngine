# 🧠 SkillFindr — Semantic Search for IBM SkillsBuild

## 📚 Overview

**SkillFindr** is a full-stack Python application developed to enhance content discoverability on the [IBM SkillsBuild](https://skillsbuild.org) platform. It combines automated data scraping, semantic search, a hybrid PostgreSQL database (including vector storage), and a FastAPI-based API. The project was built as part of a final-year dissertation to demonstrate how AI-powered search can improve access to educational content.

---

## 🚀 Features

### 🔎 Semantic Search Engine
- Embedding-based retrieval using Sentence-BERT (`all-MiniLM-L6-v2`)
- Vector similarity ranking using cosine distance
- Real-time query execution via FastAPI

### 🕸 Web Scraper
- Extracts 1,200+ courses and programs from IBM SkillsBuild
- Captures metadata: title, description, duration, tags, ratings
- Built with Selenium + BeautifulSoup and supports dynamic DOM rendering

### 🗃 Hybrid Database (PostgreSQL + pgvector)
- Stores structured metadata and vector embeddings
- Leverages `pgvector` for fast semantic similarity search

### ⚙️ FastAPI Backend
- Exposes RESTful API for semantic and keyword-based search
- Supports filterable JSON responses for integration and analysis

---

## 📦 Prerequisites

### System Requirements
- Python 3.12
- OS: Windows / macOS / Linux

### Python Dependencies
Install via:
```bash
pip install -r requirements.txt
```
Key libraries:
- `selenium`, `beautifulsoup4`, `pandas`, `lxml`
- `sentence-transformers`, `pgvector`
- `fastapi`, `uvicorn`, `sqlalchemy`

## 🐍 Conda Environment Setup

To ensure compatibility and reproducibility, it is recommended to use a dedicated conda environment.

### ✅ Create and Activate Environment

```bash
# Create a new environment with Python 3.12
conda create -n skillfindr python=3.12

# Activate the environment
conda activate skillfindr

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

### 💡 Notes
- Make sure `conda` is installed (via [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/)).

### Additional Tools
- Chrome WebDriver (for Selenium)
- PostgreSQL 15+ with `pgvector` extension

---

## 🛠 Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/skillfindr.git
cd skillfindr
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables in `.env`:
```env
USERNAME=YOUR_USERNAME
PASSWORD=YOUR_PASSWORD

# Project environment configuration
LOGIN_URL=https://sb-auth.skillsbuild.org/login
BASE_URL=https://skills.yourlearning.ibm.com
SCRAPE_DELAY=2

# Model & database settings
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
LLM_MODEL_NAME=ibm-granite/granite-3.0-1b-a400m-instruct
DATABASE_URL=postgresql+psycopg2://mathisweil@localhost:5432/postgres
```

---

## ▶️ Usage

### 🔍 Run Scraper
```bash
python scraper/IBM_scraper.py
```

If you wish to run it in **headless mode**, modify the `config.json` file by adding the following key-value pair under `"webdriver_args"`:

```json
"webdriver_args": {
  "incognito": "incognito",
  "headless": "--headless"
}
```

This will allow the browser to operate without opening a visible window, which is useful for background execution or deployment environments.

### 🧹 Process Raw Data
```bash
python parsers/process_courses.py
```

### 🗃 Load Data into PostgreSQL
```bash
python database/load_data.py
```

### ✅ Run Evaluation of Semantic Search Engine
```bash
python evaluation/semantic_search_evaluation.py
```

## 📡 Running and Testing the API

### 🌐 Launch FastAPI Server

To start the API locally, run the following command from the project root:

```bash
fastapi dev api/main.py
```

This will start a development server using `fastapi`’s CLI (make sure it's installed via `pip install fastapi[all]` if not already).

The server will initialize all core resources during startup, including:

- Sentence-BERT embedding model (`all-MiniLM-L6-v2`)
- IBM Granite LLM and tokenizer
- PostgreSQL vector database connection

---

### 🧪 Interactive API Testing via Swagger UI

Once the server is running, open your browser and navigate to:

```
http://127.0.0.1:8000/docs
```

This brings up **Swagger UI**, an auto-generated API documentation and test interface.

You can simulate calls to:

- **`POST /api/v1/courses/search/semantic`**  
  Input a search query (e.g., *"beginner cybersecurity path"*) and add filters like `duration`, `category`, or `star_rating`. Click "Execute" to view results with real-time similarity search.

- **`POST /api/v1/chat`**  
  This endpoint implements **Retrieval-Augmented Generation (RAG)**.  
  Provide a `chat_history` array with `"role": "user"` and `"role": "assistant"` messages. The system will search for semantically similar courses, feed them to a language model, and return a contextual answer.

### 📁 Example Request Payloads

#### `/api/v1/courses/search/semantic`

```json
{
  "query": "data analysis beginner course",
  "threshold": 0.5,
  "limit": 5,
  "filters": {
    "duration": { "min": 30, "max": 120 },
    "category": ["data_science"]
  }
}
```

#### `/api/v1/chat`

```json
{
  "chat_history": [
    { "role": "user", "content": "I'm interested in learning web development from scratch" }
  ],
  "threshold": 0.5,
  "limit": 5
}
```

---

Both endpoints return rich metadata and ranked courses, helping users navigate educational content more intelligently.

---

## 📁 Project Structure

```plaintext
skillfindr/
├── scraper/           # Web scraping (Selenium + BeautifulSoup)
├── embedding/         # Embedding logic and retrieval methods
├── database/          # PostgreSQL loaders and vector storage
├── api/               # FastAPI server and endpoints
├── output/            # Scraped and processed data
├── logs/              # Logs for debugging and monitoring
├── config/            # configuration folder
└── requirements.txt   # Python package list
```

---

## 🔄 Customisation

- **Add fields**: Extend `config.json` and scraping logic
- **Swap models**: Replace Sentence-BERT with other embedding models
- **Advanced filtering**: Extend API to filter by rating, duration, category
- **Frontend integration**: Consume FastAPI with React, Flask, etc.

---

## ⚠️ Error Handling

- Handles:
  - DOM structure changes
  - Timeout or network issues
  - Duplicate entries
- Logs saved in `logs/` for debugging

---

## 🙏 Acknowledgements

- Final-year BSc Computer Science project at Queen Mary University of London.
- Thanks to IBM for platform access and support.

---

## 📬 Contact

**Mathis Weil**  
📧 [ec22995@qmul.ac.uk](mailto:ec22995@qmul.ac.uk)
