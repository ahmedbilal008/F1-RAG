# F1 RAG Assistant

A production-quality Retrieval-Augmented Generation (RAG) chatbot for Formula 1, featuring multi-source ingestion, hybrid retrieval, evaluation metrics, and a modern glassmorphic UI.

## Architecture

```
┌─────────────┐        ┌──────────────────────────────────────────┐
│  Next.js     │  REST  │  FastAPI Backend                         │
│  Frontend    │◄──────►│                                          │
│  (port 3000) │        │  /api/v1/chat    ─► RAG Chain            │
│              │        │  /api/v1/compare ─► RAG vs Direct        │
│              │        │  /api/v1/ingest  ─► Ingestion Pipeline   │
│              │        │  /api/v1/status  ─► Health Check         │
│              │        │  /api/v1/evaluate─► Evaluation Suite     │
└─────────────┘        └──────┬─────────────────┬─────────────────┘
                              │                 │
                    ┌─────────▼──────┐ ┌────────▼────────┐
                    │  Pinecone      │ │  Gemini 2.5     │
                    │  Vector DB     │ │  Flash LLM      │
                    │  (namespaces)  │ │  + Embeddings   │
                    └────────────────┘ └─────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, Tailwind CSS 4, shadcn/ui, Lucide icons |
| Backend | FastAPI, Pydantic, Loguru |
| Vector DB | Pinecone (serverless, cosine similarity) |
| LLM | Google Gemini 2.5 Flash |
| Embeddings | Google embedding-001 (768d) |
| Scraping | Trafilatura + BeautifulSoup fallback |
| Data APIs | Jolpica (Ergast replacement), OpenF1 |

## Features

- **Multi-source ingestion**: Wikipedia articles, Ergast F1 API data (results, standings, drivers, constructors)
- **Semantic chunking**: F1-aware metadata tagging (driver, team, season detection)
- **Namespace strategy**: Each data source in its own Pinecone namespace for selective retrieval
- **RAG vs Direct comparison**: Side-by-side mode with latency and quality metrics
- **Live data augmentation**: OpenF1 API for current session data
- **Evaluation suite**: 10-question test set with keyword scoring
- **Provider abstraction**: LLM and embedding providers are swappable

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Google AI API key ([Google AI Studio](https://aistudio.google.com/app/apikey))
- Pinecone API key ([Pinecone](https://www.pinecone.io/))

### 1. Configure Environment

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Ingest Data

Use the sidebar "Ingestion" buttons in the UI, or call the API directly:

```bash
curl -X POST http://localhost:8000/api/v1/ingest -H "Content-Type: application/json" -d '{"source": "all"}'
```

## Project Structure

```
f1-rag-chatbot/
├── backend/
│   ├── main.py                  # FastAPI app factory
│   ├── requirements.txt
│   ├── Dockerfile               # Backend container build
│   ├── .dockerignore
│   ├── .env.example             # Environment template
│   └── app/
│       ├── api/routes.py        # REST endpoints
│       ├── core/config.py       # Pydantic settings
│       ├── core/logging.py      # Structured logging
│       ├── evaluation/          # RAG evaluation suite
│       ├── ingestion/           # Wikipedia scraper, Jolpica client, chunker, pipeline
│       ├── models/schemas.py    # Request/response schemas
│       ├── retrieval/           # RAG chain, OpenF1 live data
│       └── services/            # Embeddings, LLM, vector store providers
├── frontend/
│   ├── src/app/                 # Next.js pages
│   ├── src/components/          # Chat UI, sidebar, metrics
│   └── src/lib/                 # API client, types
└── README.md
```

