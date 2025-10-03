# Haiku Utilities A2A Agent

This sample uses the Agent Development Kit (ADK) to create a haiku utility agent which communicates using A2A.

## Prerequisites

- Python 3.10+
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- `make`
    - The build automation tool to run a `Makefile`
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
    - Python package management system
    - More tightly coupled with ADK libraries and offers quicker development than `pip` alone

## Running the Sample

1. Navigate to the samples directory:

    ```bash
    cd a2a_utilities
    ```

2. Create a virtual environment and install requirements:

    ```bash
    uv venv
    source .venv/bin/activate
    uv pip install -r requirements.txt
    ```

3. Create a `.env` file by copying the `.sample-env` and filling out the correct values:

    ```bash
    GOOGLE_API_KEY=<your_key>
    GOOGLE_CLOUD_PROJECT=<your_project>
    GOOGLE_PROJECT_NUMBER=<your_project_number>
    GOOGLE_CLOUD_LOCATION=<your_region>
    GOOGLE_CLOUD_REGION=${GOOGLE_CLOUD_LOCATION}
    GEMINI_API_KEY=${GOOGLE_API_KEY}
    ```

4. Run the A2A agent:

    ```bash
    uv run uvicorn agent:a2a_app --host localhost --port 8002
    ```

5. Run the ADK Web Server

    ```bash
    # In a separate terminal, run the adk web server at the project root
    adk web
    ```

  In the Web UI, select the `a2a_utilities` agent.

## Deploy to Google Cloud Run

```sh
# Set the environment variables from your .env file into the terminal session
source .env

# Run deployment command in a2a_utilities directory
gcloud run deploy a2a-utilities \
    --port=8080 \
    --source=. \
    --allow-unauthenticated \
    --min-instances=1 \
    --region="us-central1" \
    --project=$GOOGLE_CLOUD_PROJECT \
    --set-env-vars=GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_PROJECT_NUMBER=$GOOGLE_PROJECT_NUMBER
```
