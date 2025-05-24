from fastapi import FastAPI
from pydantic import BaseModel
from src.chain import run_agent

app = FastAPI()

class QueryRequest(BaseModel):
    message: str

@app.post("/query")
async def query_endpoint(request: QueryRequest):
    response = run_agent(request.message)
    return { "response": response }




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),  # use PORT from env or default to 8000
        reload=True
    )