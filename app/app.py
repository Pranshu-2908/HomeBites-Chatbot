from fastapi import FastAPI
from pydantic import BaseModel
from chain import run_agent

app = FastAPI()

class QueryRequest(BaseModel):
    message: str

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    response = run_agent(request.message)
    return { "response": response }
