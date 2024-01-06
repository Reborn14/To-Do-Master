from fastapi import FastAPI, Request, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from notion_client import Client
from pydantic import BaseModel, Field
import os
import httpx

app = FastAPI()

# Load environment variables
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
DATABASE_ID = os.getenv('DATABASE_ID')

# API Key for authentication
API_SECRET_KEY = os.getenv("API_SECRET_KEY")  # Your API secret key

# API Key Header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == API_SECRET_KEY:
        return api_key_header
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")

@app.get("/", dependencies=[Depends(get_api_key)])
async def read_root():
    return {"Hello": "World"}


# Define the request model for querying the database
class NotionDatabaseQueryRequest(BaseModel):
    filter: dict = Field(default_factory=dict)
    sorts: list = Field(default_factory=list)
    start_cursor: str = None
    page_size: int = None

@app.post("/query-database", dependencies=[Depends(get_api_key)])
async def query_database(request_body: NotionDatabaseQueryRequest):
    try:
        response = httpx.post(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}/query",
            headers={"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
            json=request_body.dict(exclude_none=True)
        )
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


# Define the request model for creating a page
class NotionPageCreateRequest(BaseModel):
    parent: dict = Field(default_factory=dict)
    properties: dict
    children: list = Field(default_factory=list)
    icon: dict = None
    cover: dict = None

@app.post("/create-page", dependencies=[Depends(get_api_key)])
async def create_page(request_body: NotionPageCreateRequest):
    page_data = request_body.dict(exclude_none=True)
    page_data["parent"] = {"database_id": DATABASE_ID}

    try:
        response = httpx.post(
            "https://api.notion.com/v1/pages",
            headers={"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
            json=page_data
        )
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


# Define the request model for updating a page
class NotionPageUpdateRequest(BaseModel):
    page_id: str
    properties: dict
    archived: bool = None
    icon: dict = None
    cover: dict = None

@app.patch("/update-page", dependencies=[Depends(get_api_key)])
async def update_page(request_body: NotionPageUpdateRequest):
    update_data = request_body.dict(exclude_unset=True)
    page_id = update_data.pop('page_id')  # Extract page_id and remove it from the update data

    try:
        response = httpx.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers={"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"},
            json=update_data
        )
        return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
        

