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

---

### 🔒 Notes on Authentication and Environment

- The `.env` file must be present and correctly configured before launching the server.
- API endpoints are currently unauthenticated but designed to be secured via a token-based system (e.g., FastAPI’s OAuth2 or header-based auth).

---

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
