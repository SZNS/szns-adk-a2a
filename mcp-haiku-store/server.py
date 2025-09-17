import asyncio
import logging
import os

import httpx
from typing import Any, Dict, List, Optional

from sqlmodel import Field, Session, SQLModel, create_engine, select, func
from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

# Define the database file name
DATABASE_FILE = "haikus.db"
# Define the database URL. For Cloud Run, we'll use an in-memory database for simplicity,
# but you could easily switch to a persistent solution like Cloud SQL.
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Create the engine. The `connect_args` are needed for SQLite.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Define the Haiku data model
class Haiku(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    score: int = Field(ge=1, le=100) # Score must be between 1 and 100

def create_db_and_tables():
    # If the database file exists, delete it to start fresh on each run
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
    SQLModel.metadata.create_all(engine)
    # Add some sample data
    with Session(engine) as session:
        haiku_1 = Haiku(text="Old silent pond...\nA frog jumps into the pond,\nsplash! Silence again.", score=85)
        haiku_2 = Haiku(text="An old silent pond...\nA frog jumps into the pond,\nsplash! Silence again.", score=92)
        haiku_3 = Haiku(text="Light of a candle\nis transferred to another candle—\nspring twilight.", score=78)
        session.add(haiku_1)
        session.add(haiku_2)
        session.add(haiku_3)
        session.commit()

mcp = FastMCP("Haiku Store")

@mcp.tool
def create_haiku(text: str, score: int) -> Dict[str, Any]:
    """
    Create a new haiku, determine its ID, and add it to the database.
    Returns a dictionary representing the new haiku.
    """
    with Session(engine) as session:
        # Determine the next primary ID
        max_id = session.exec(select(func.max(Haiku.id))).one_or_none()
        next_id = (max_id or 0) + 1
        
        haiku = Haiku(id=next_id, text=text, score=score)
        session.add(haiku)
        session.commit()
        session.refresh(haiku)
        return {"id": haiku.id, "text": haiku.text, "score": haiku.score}

@mcp.tool
def read_haikus(offset: int = 0, limit: int = 10) -> List[Haiku]:
    """
    Get a list of all haikus, with pagination.
    """
    with Session(engine) as session:
        haikus = session.exec(select(Haiku).offset(offset).limit(limit)).all()
        return haikus

@mcp.tool
def search_haikus(query: Optional[str] = None, min_score: Optional[int] = None) -> List[Haiku]:
    """
    Search for haikus by text query or a minimum score.
    """
    with Session(engine) as session:
        statement = select(Haiku)
        if query:
            statement = statement.where(Haiku.text.contains(query))
        if min_score is not None:
            statement = statement.where(Haiku.score >= min_score)
        
        results = session.exec(statement).all()
        return results

@mcp.tool
def read_haiku(haiku_id: int) -> Optional[Haiku]:
    """
    Get a single haiku by its unique ID.
    """
    with Session(engine) as session:
        haiku = session.get(Haiku, haiku_id)
        return haiku

@mcp.tool
def delete_haiku(haiku_id: int) -> Dict[str, Any]:
    """
    Delete a haiku by its unique ID.
    """
    with Session(engine) as session:
        haiku = session.get(Haiku, haiku_id)
        if not haiku:
            return {"ok": False, "message": "Haiku not found"}
        session.delete(haiku)
        session.commit()
        return {"ok": True, "message": "Haiku deleted successfully"}

if __name__ == "__main__":
    logger.info(f" MCP server started on port {os.getenv('PORT', 8075)}")
    # Host="0.0.0.0" required for Cloud Run.
    create_db_and_tables()
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=os.getenv("PORT", 8075),
        )
    )