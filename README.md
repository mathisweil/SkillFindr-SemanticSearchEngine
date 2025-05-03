
# 🧠 SkillFindr — Semantic Search for IBM SkillsBuild

## 📚 Overview

**SkillFindr** is a full-stack Python application developed to enhance content discoverability on the [IBM SkillsBuild](https://skillsbuild.org) platform. It combines automated data scraping, semantic search, a hybrid PostgreSQL database (including vector storage), and a FastAPI-based API. The project was built as part of a final-year dissertation to demonstrate how AI-powered search can improve access to educational content.

---

## 🚀 Features

### 🔎 Semantic Search Engine
- Embedding-based retrieval using Sentence-BERT (`all-MiniLM-L6-v2`)
- Vector similarity ranking using cosine distance
- Real-time response via FastAPI

### 🕸 Web Scraper
- Extracts over 1,200+ courses and programs from IBM SkillsBuild
- Captures metadata: title, description, duration, tags, rating
- Built using Selenium and BeautifulSoup with dynamic content support

### 🗃 Hybrid Database
- PostgreSQL used for structured metadata (e.g., duration, title, tags)
- `pgvector` extension stores and indexes 384-dimensional course embeddings

### ⚙️ FastAPI Backend
- RESTful API to serve course search queries and metadata filtering
- JSON responses suitable for frontend integration or data analysis

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

### Additional Tools
- Chrome WebDriver (required for Selenium)
- PostgreSQL 14+ with the `pgvector` extension

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

3. (Optional) Set environment variables in `.env`:
```
DB_URL=postgresql://user:password@localhost:5432/skillsbuild
```

4. Configure `config.json` for scraping parameters (e.g., URLs, language filters).

---

## ▶️ Usage

### 🔍 Run Scraper
```bash
python scraper/IBM_scraper.py
```

### 🗂 Ingest Data into PostgreSQL
```bash
python database/load_data.py
```

### 🌐 Launch FastAPI Server
```bash
fastapi dev api/main.py
```

---

## 📁 Project Structure

```plaintext
skillfindr/
├── scraper/           # Web scraping logic (Selenium + BeautifulSoup)
├── embedding/         # Embedding generation and semantic indexing
├── database/          # PostgreSQL + pgvector integration and loaders
├── api/               # FastAPI backend for course search
├── output/            # Scraped data
├── logs/              # Logging info
├── config.json        # Scraper configuration
└── requirements.txt   # Python dependencies
```

---

## 🔄 Customisation

- **Add new fields**: Extend `config.json` and `scraper/main.py` to extract additional metadata.
- **Use other models**: Swap Sentence-BERT with OpenAI/GTE embeddings.
- **Expand filters**: Modify the API to support advanced filtering (e.g., duration, language).
- **Connect frontend**: Consume FastAPI endpoints in a React or Flask interface.

---

## ❗ Error Handling

- Built-in exception handling for:
  - DOM structure changes
  - Timeouts and connection failures
  - Course duplication
- Logs stored in `/logs/` for debugging

---

## 🙏 Acknowledgements

- Developed as part of a BSc Computer Science final-year project at Queen Mary University of London.
- Special thanks to IBM for platform access and technical support.

---

## 📬 Contact

**Mathis Weil**  
📧 [ec22995@qmul.ac.uk](mailto:ec22995@qmul.ac.uk)
