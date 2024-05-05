from fastapi import FastAPI, Request, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from weaviate.classes.query import MetadataQuery
import weaviate
import asyncio  # import asyncio for the sleep function
import os
from visualizeData import prepare_graph_data
from chatCompletions import get_results


# Load environment variables
load_dotenv()

def connect_to_weaviate():
    return weaviate.connect_to_wcs(
        cluster_url=os.getenv("WCS_URL"),
        auth_credentials=weaviate.auth.AuthApiKey(os.getenv("WCS_API_KEY")),
        headers={"X-OpenAI-Api-Key": os.environ["OPENAI_API_KEY"]}
    )

def show_collection(client, collection_name):
    collection = client.collections.get(collection_name)
    response = collection.query.fetch_objects(include_vector=True)
    return response

def format_output(objects):
    data = [{"properties": o.properties, "vector": o.vector} for o in objects]
    return data


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

chat_contexts = {}

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/graph-data")
async def graph_data():
    with connect_to_weaviate() as client:
        collection = show_collection(client, "GithubIssues")
        collection_output = format_output(collection.objects)
        graph_json = prepare_graph_data(collection_output)
        return JSONResponse(content=graph_json)

@app.get("/issue/{issue_id}")
async def issue_detail(request: Request, issue_id: str):
    try:
        with connect_to_weaviate() as client:
            # Query for the specific issue_id using BM25 or another query method
            github_issues = client.collections.get("GithubIssues")
            response = github_issues.query.bm25(
                query=issue_id,
                query_properties=["issue_id"],
                return_metadata=MetadataQuery(score=True),
                limit=1  # Limit to only the best match
            )

            # Check if any results were found
            if not response.objects:
                raise HTTPException(status_code=404, detail="Issue not found")

            # Extract issue properties
            issue_details = response.objects[0].properties
            return templates.TemplateResponse("issue_detail.html", {"request": request, "issue": issue_details})

    except Exception as e:
        print(f"Error querying issue: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
@app.websocket("/ws/{issue_id}")
async def websocket_endpoint(websocket: WebSocket, issue_id: str):
    await websocket.accept()
    try:
        # Retrieve issue details for the given issue_id
        with connect_to_weaviate() as client:
            github_issues = client.collections.get("GithubIssues")
            response = github_issues.query.bm25(
                query=issue_id,
                query_properties=["issue_id"],
                return_metadata=MetadataQuery(score=True),
                limit=1
            )
            if not response.objects:
                await websocket.send_text("No details found for this issue.")
                await websocket.close()
                return
            issue_details = response.objects[0].properties
        
        # Start conversation with the issue context
        issue_context_message = (
            f"You are discussing an issue with the following details: {issue_details}"
        )
        await websocket.send_text(issue_context_message)

        # Pass issue context into the chatbot
        conversation = [{"role": "system", "content": issue_context_message}]
        
        # Receive user messages and send responses from the chatbot
        while True:
            data = await websocket.receive_text()
            async for result in get_results(data, conversation):
                await websocket.send_text(result)
                await asyncio.sleep(0)
    finally:
        await websocket.close()


@app.get("/chat-history/{chat_id}")
async def get_chat_history(chat_id: str):
    return {"history": chat_contexts.get(chat_id, [])}
