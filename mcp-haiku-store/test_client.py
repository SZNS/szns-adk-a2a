import asyncio
from fastmcp import Client

client = Client("http://localhost:8075/mcp")

async def call_create_haiku(text: str, score: int):
    """Calls the create_haiku tool."""
    async with client:
        result = await client.call_tool("create_haiku", {"text": text, "score": score})
        print("--- Create Haiku ---")
        print(result)
        # Access the 'data' attribute which holds the dictionary response
        return result.data.get("id")

async def call_search_haikus(query: str = None, min_score: int = None):
    """Calls the search_haikus tool."""
    params = {}
    if query:
        params["query"] = query
    if min_score:
        params["min_score"] = min_score
    
    async with client:
        print(f"\n--- Searching Haikus (query='{query}', min_score={min_score}) ---")
        result = await client.call_tool("search_haikus", params)
        print(result)

async def call_read_haiku(haiku_id: int):
    """Calls the read_haiku tool."""
    async with client:
        print(f"\n--- Reading Haiku (id={haiku_id}) ---")
        result = await client.call_tool("read_haiku", {"haiku_id": haiku_id})
        print(result)

async def call_delete_haiku(haiku_id: int):
    """Calls the delete_haiku tool."""
    async with client:
        print(f"\n--- Deleting Haiku (id={haiku_id}) ---")
        result = await client.call_tool("delete_haiku", {"haiku_id": haiku_id})
        print(result)

async def call_read_haikus(offset: int = 0, limit: int = 10):
    """Calls the read_haikus tool to see all haikus."""
    async with client:
        print("\n--- Reading All Haikus ---")
        result = await client.call_tool("read_haikus", {"offset": offset, "limit": limit})
        print(result)

async def main():
    # Create a new haiku
    new_id = await call_create_haiku(
        text="A world of dew,\nAnd within every dewdrop\nA world of struggle.",
        score=95
    )

    # Read the haiku we just created
    if new_id:
        await call_read_haiku(new_id)

    # Search for haikus
    await call_search_haikus(query="pond")
    await call_search_haikus(min_score=90)
    await call_search_haikus(query="frog", min_score=90)

    # Delete the haiku we created
    if new_id:
        await call_delete_haiku(new_id)

    # Read all haikus to see the final state
    await call_read_haikus()

if __name__ == "__main__":
    asyncio.run(main())
