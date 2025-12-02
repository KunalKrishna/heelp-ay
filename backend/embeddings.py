from openai import OpenAI
from typing import List
import logging
from config import OPENAI_API_KEY, EMBEDDING_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)


def get_embedding(text: str) -> List[float]:
    """Generate embedding for a single text"""
    try:
        # Truncate text if too long (max ~8000 tokens for ada-002)
        if len(text) > 30000:
            text = text[:30000]
        
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for multiple texts"""
    embeddings = []
    for text in texts:
        embedding = get_embedding(text)
        embeddings.append(embedding)
    return embeddings
