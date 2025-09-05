# ADK Agent

This sample uses FastMCP to create a simple REST API to manage haikus in-memory with a SQLite database.

## Prerequisites

- Python 3.10 or higher

## Running the Sample

1. Navigate to the samples directory:

    ```bash
    cd mcp-haiku-store
    ```

4. Run the MCP server agent:

    ```bash
    # Runs at port 8075 locally
    
    uv run server.py
    ```

5. Test the MCP server

    ```bash
    # In a separate terminal, cd back into the mcp-haiku-store directory
    
    uv run test_client.py
    ```

## Deploy to Google Cloud Run

```sh
gcloud run deploy mcp-haiku-store \
    --port=8080 \
    --source=. \
    --allow-unauthenticated \
    --region="us-central1" \
    --project=$GOOGLE_CLOUD_PROJECT
```
