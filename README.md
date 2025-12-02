# heelp-ay

Personal hobby project to make UNC Cobweb more accessible using AI.

## Overview

A web scraping and RAG (Retrieval Augmented Generation) application that:
1. Scrapes text content from a list of URLs provided in a text file
2. Stores the scraped content with embeddings in a PostgreSQL database with pgvector
3. Provides a React UI where users can ask questions
4. Returns AI-generated answers based on the scraped content, along with source URLs

## Project Structure

```
├── backend/                 # Python FastAPI backend
│   ├── main.py             # FastAPI application entry point
│   ├── config.py           # Configuration settings
│   ├── database.py         # Database models and connection
│   ├── scraper.py          # Web scraping utilities
│   ├── embeddings.py       # OpenAI embeddings generation
│   ├── rag.py              # RAG pipeline for Q&A
│   ├── requirements.txt    # Python dependencies
│   ├── urls.txt            # Sample URLs to scrape
│   └── .env.example        # Environment variables template
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.jsx        # Main React component
│   │   ├── main.jsx       # React entry point
│   │   └── index.css      # Styles
│   ├── index.html         # HTML template
│   ├── vite.config.js     # Vite configuration
│   └── package.json       # Node.js dependencies
└── docker-compose.yml      # Docker compose for PostgreSQL + pgvector
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- Docker and Docker Compose
- OpenAI API key

## Setup

### 1. Start the Database

```bash
docker-compose up -d
```

This starts PostgreSQL with the pgvector extension enabled.

### 2. Configure the Backend

```bash
cd backend
cp .env.example .env
# Edit .env and add your OpenAI API key
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

### 3. Add URLs to Scrape

Edit `backend/urls.txt` and add the URLs you want to scrape (one per line):

```
https://example.com/page1
https://example.com/page2
```

### 4. Start the Backend

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

### 5. Scrape URLs

Use the API to scrape and store URLs:

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "urls.txt"}'
```

Or provide URLs directly:

```bash
curl -X POST "http://localhost:8000/scrape" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/page1", "https://example.com/page2"]}'
```

### 6. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:3000`.

## Usage

1. Open the UI at `http://localhost:3000`
2. Enter your question in the search box
3. The system will:
   - Search for relevant content using vector similarity
   - Generate an answer using GPT
   - Display the answer with source URLs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/query` | Query the RAG system |
| POST | `/scrape` | Scrape URLs and store in database |
| GET | `/pages` | List all stored web pages |
| DELETE | `/pages/{id}` | Delete a web page |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://postgres:postgres@localhost:5432/webrag` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings and chat | Required |
| `HOST` | API server host | `0.0.0.0` |
| `PORT` | API server port | `8000` |

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, BeautifulSoup4
- **Database**: PostgreSQL with pgvector extension
- **Embeddings**: OpenAI text-embedding-ada-002
- **Chat**: OpenAI GPT-3.5-turbo
- **Frontend**: React, Vite

## License

ISC
