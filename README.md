# F1 RAG Chat

A Retrieval-Augmented Generation (RAG) chatbot for Formula 1 information using Pinecone vector database and Google Gemini AI.

## Features

- RAG and Direct AI response modes with comparison capability
- Persistent vector storage using Pinecone
- Real-time F1 data scraping from Wikipedia sources
- Professional chat interface with analytics
- Source citations with relevance scores
- Comprehensive error handling and logging

## Architecture

```
User Query → RAG Mode Toggle → If RAG:
    ├── Pinecone Vector Search
    ├── Context Retrieval  
    ├── Gemini AI Generation
    └── Response + Sources

If Direct:
    └── Direct Gemini AI → Response
```

## Tech Stack

- **Frontend**: Streamlit with custom CSS
- **Vector DB**: Pinecone
- **LLM**: Google Gemini 1.5 Flash
- **Embeddings**: Google Embedding-001
- **Web Scraping**: BeautifulSoup + Requests

## Prerequisites

- Python 3.8+
- Google AI API Key
- Pinecone API Key

## Quick Setup

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/f1-rag-chatbot.git
cd f1-rag-chatbot
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Create .env file
GOOGLE_API_KEY=your_google_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment
```

### 3. Initialize Vector Database

```bash
python main.py
```

The application will automatically scrape F1 data and populate the vector database on first run.

### 4. Run Application

```bash
streamlit run main.py
```

## Configuration

All settings are managed in `src/utils/config.py`:

- Vector dimensions and similarity thresholds
- Scraping targets and refresh intervals  
- Model parameters and temperature settings
- Logging levels and output formats

## Project Structure

```
f1-rag-chatbot/
├── main.py                 # Main application entry point
├── src/
│   ├── components/         # UI components
│   ├── core/              # Core RAG functionality
│   ├── data/              # Data storage and metadata
│   └── utils/             # Configuration and utilities
├── static/                # CSS and assets
└── requirements.txt       # Dependencies
```

## Usage

1. **RAG Mode**: Uses vector search to find relevant F1 information and generate contextual responses
2. **Direct Mode**: Bypasses vector search for immediate AI responses
3. **Comparison**: Toggle between modes to compare response quality and sources

## API Keys

- **Google AI**: Generate at [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Pinecone**: Create account at [Pinecone](https://www.pinecone.io/)

