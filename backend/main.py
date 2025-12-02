from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging

from database import get_db, init_db, WebPage
from scraper import read_urls_from_file, scrape_urls
from embeddings import get_embedding
from rag import query_rag
from config import HOST, PORT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    yield
    # Shutdown (nothing to do)


app = FastAPI(
    title="Web RAG API",
    description="API for web scraping and RAG-based question answering",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class SourceInfo(BaseModel):
    url: str
    title: str
    similarity: float


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    query: str


class ScrapeRequest(BaseModel):
    urls: Optional[List[str]] = None
    file_path: Optional[str] = None


class ScrapeStatus(BaseModel):
    message: str
    urls_processed: int
    urls_stored: int


class WebPageInfo(BaseModel):
    id: int
    url: str
    title: Optional[str]
    content_preview: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Web RAG API is running", "docs": "/docs"}


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest, db: Session = Depends(get_db)):
    """Query the RAG system with a question"""
    try:
        result = query_rag(db, request.query, request.top_k)
        return QueryResponse(**result)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape", response_model=ScrapeStatus)
async def scrape_endpoint(request: ScrapeRequest, db: Session = Depends(get_db)):
    """Scrape URLs and store them in the database"""
    urls = []
    
    # Get URLs from request or file
    if request.urls:
        urls = request.urls
    elif request.file_path:
        urls = read_urls_from_file(request.file_path)
    else:
        raise HTTPException(status_code=400, detail="Either urls or file_path must be provided")
    
    if not urls:
        raise HTTPException(status_code=400, detail="No valid URLs provided")
    
    # Scrape URLs
    scraped_data = scrape_urls(urls)
    
    # Store in database with embeddings
    stored_count = 0
    for data in scraped_data:
        try:
            # Check if URL already exists
            existing = db.query(WebPage).filter(WebPage.url == data["url"]).first()
            if existing:
                logger.info(f"URL already exists, updating: {data['url']}")
                existing.title = data["title"]
                existing.content = data["content"]
                existing.embedding = get_embedding(data["content"])
            else:
                # Create new entry
                embedding = get_embedding(data["content"])
                page = WebPage(
                    url=data["url"],
                    title=data["title"],
                    content=data["content"],
                    embedding=embedding
                )
                db.add(page)
            
            db.commit()
            stored_count += 1
        except Exception as e:
            logger.error(f"Error storing {data['url']}: {e}")
            db.rollback()
    
    return ScrapeStatus(
        message="Scraping completed",
        urls_processed=len(urls),
        urls_stored=stored_count
    )


@app.get("/pages", response_model=List[WebPageInfo])
async def list_pages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all stored web pages"""
    pages = db.query(WebPage).offset(skip).limit(limit).all()
    return [
        WebPageInfo(
            id=page.id,
            url=page.url,
            title=page.title or "",
            content_preview=page.content[:200] + "..." if len(page.content) > 200 else page.content
        )
        for page in pages
    ]


@app.delete("/pages/{page_id}")
async def delete_page(page_id: int, db: Session = Depends(get_db)):
    """Delete a web page from the database"""
    page = db.query(WebPage).filter(WebPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    db.delete(page)
    db.commit()
    return {"message": "Page deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
