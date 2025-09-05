# ADK Agent

This sample uses the Agent Development Kit (ADK) to create a simple fun facts generator which communicates using A2A.

## Prerequisites

- Python 3.10 or higher
- Access to an LLM and API Key

## Running the Sample

1. Navigate to the samples directory:

    ```bash
    cd a2a_validator
    ```

2. Install Requirements

    ```bash
    pip install -r requirements.txt
    ```

3. Create a `.env` file by coping the `.sample-env` and filling out the correct values:

    ```bash
    GOOGLE_API_KEY=<your_key>
    GOOGLE_CLOUD_PROJECT=<your_project>
    GOOGLE_CLOUD_LOCATION=<your_region>
    GOOGLE_CLOUD_REGION=${GOOGLE_CLOUD_LOCATION}
    GEMINI_API_KEY=${GOOGLE_API_KEY}
    ```

4. Run the A2A agent:

    ```bash
    uvicorn agent:a2a_app --host localhost --port 8001
    ```

5. Run the ADK Web Server

    ```bash
    # In a separate terminal, run the adk web server at the project root
    adk web
    ```

  In the Web UI, select the `a2a_validator` agent.

## Deploy to Google Cloud Run

```sh
gcloud run deploy a2a-validator \
    --port=8080 \
    --source=. \
    --allow-unauthenticated \
    --region="us-central1" \
    --project=$GOOGLE_CLOUD_PROJECT \
    --set-env-vars=GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=us-central1,GOOGLE_GENAI_USE_VERTEXAI=true
```
