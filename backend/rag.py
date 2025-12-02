from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI
import logging

from database import WebPage
from embeddings import get_embedding
from config import OPENAI_API_KEY, CHAT_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


def search_similar_content(db: Session, query: str, top_k: int = 5) -> List[Tuple[WebPage, float]]:
    """Search for content similar to the query using vector similarity"""
    try:
        # Generate embedding for the query
        query_embedding = get_embedding(query)
        
        # Search using cosine similarity with pgvector
        # Using raw SQL for pgvector distance operator
        sql = text("""
            SELECT id, url, title, content, embedding,
                   1 - (embedding <=> :query_embedding) as similarity
            FROM web_pages
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_embedding
            LIMIT :top_k
        """)
        
        result = db.execute(sql, {
            "query_embedding": str(query_embedding),
            "top_k": top_k
        })
        
        results = []
        for row in result:
            page = WebPage(
                id=row.id,
                url=row.url,
                title=row.title,
                content=row.content
            )
            results.append((page, row.similarity))
        
        return results
    except Exception as e:
        logger.error(f"Error searching similar content: {e}")
        raise


def generate_answer(query: str, context_pages: List[Tuple[WebPage, float]]) -> Dict:
    """Generate an answer using RAG with the retrieved context"""
    try:
        # Build context from retrieved pages
        context_parts = []
        sources = []
        
        for page, similarity in context_pages:
            # Truncate content for context window
            content_preview = page.content[:2000] if len(page.content) > 2000 else page.content
            context_parts.append(f"Source: {page.url}\nTitle: {page.title}\nContent: {content_preview}")
            sources.append({
                "url": page.url,
                "title": page.title,
                "similarity": round(similarity, 4)
            })
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Generate response using OpenAI
        system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
        Always cite the sources you use to answer the question.
        If the context doesn't contain enough information to answer the question, say so clearly.
        Be concise but thorough in your answers."""
        
        user_prompt = f"""Context information from web pages:

{context}

---

Based on the above context, please answer the following question:
{query}

Please provide a clear answer and mention which source(s) you used."""

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        
        return {
            "answer": answer,
            "sources": sources,
            "query": query
        }
    except Exception as e:
        logger.error(f"Error generating answer: {e}")
        raise


def query_rag(db: Session, query: str, top_k: int = 5) -> Dict:
    """Main RAG pipeline: search and generate answer"""
    # Search for relevant content
    similar_pages = search_similar_content(db, query, top_k)
    
    if not similar_pages:
        return {
            "answer": "I couldn't find any relevant information in the database to answer your question.",
            "sources": [],
            "query": query
        }
    
    # Generate answer
    return generate_answer(query, similar_pages)
