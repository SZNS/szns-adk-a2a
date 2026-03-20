import httpx
from google.adk.agents import Agent

POETRYDB_BASE_URL = "https://poetrydb.org"
MAX_POEMS_DISPLAY = 5


def _format_poems(poems: list[dict]) -> str:
    """Format a list of poem dicts into readable text."""
    if not poems:
        return "No poems found."
    results = []
    for poem in poems[:MAX_POEMS_DISPLAY]:
        text = "\n".join(poem.get("lines", []))
        results.append(
            f"Title: {poem.get('title', 'Unknown')}\n"
            f"Author: {poem.get('author', 'Unknown')}\n"
            f"Lines: {poem.get('linecount', '?')}\n\n{text}"
        )
    total = len(poems)
    header = f"Showing {min(total, MAX_POEMS_DISPLAY)} of {total} poems:\n\n"
    return header + "\n\n---\n\n".join(results)


async def get_random_poems(count: int = 3) -> str:
    """Get random poems from PoetryDB. Count should be between 1 and 10."""
    count = max(1, min(count, 10))
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{POETRYDB_BASE_URL}/random/{count}")
            response.raise_for_status()
            return _format_poems(response.json())
    except httpx.HTTPError as e:
        return f"Failed to fetch random poems from PoetryDB: {e}"


async def search_poems_by_author(author_name: str) -> str:
    """Search for poems by author name. Supports partial matching."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{POETRYDB_BASE_URL}/author/{author_name}"
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "status" in data:
                return f"No poems found for author '{author_name}'."
            return _format_poems(data)
    except httpx.HTTPError as e:
        return f"Failed to search PoetryDB by author: {e}"


async def search_poems_by_title(title: str) -> str:
    """Search for poems by title. Supports partial matching."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{POETRYDB_BASE_URL}/title/{title}"
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "status" in data:
                return f"No poems found matching title '{title}'."
            return _format_poems(data)
    except httpx.HTTPError as e:
        return f"Failed to search PoetryDB by title: {e}"


PROMPT = """
You are a poetry lookup assistant. You have access to PoetryDB, a database of classic poetry.
You can:
- Get random poems for inspiration
- Search for poems by author name (partial matches work)
- Search for poems by title (partial matches work)

When the user asks about poems, poetry, or wants inspiration from classic poets, use these tools.
Present the results in a readable format. If the user asks for a specific poet, use search_poems_by_author.
"""

poetry_lookup_agent = Agent(
    name="poetry_lookup_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    tools=[get_random_poems, search_poems_by_author, search_poems_by_title],
    output_key="poetry_lookup_agent_output",
)
