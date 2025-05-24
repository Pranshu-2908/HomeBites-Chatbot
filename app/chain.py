from langchain.agents import initialize_agent, AgentType
from langchain_google_genai import ChatGoogleGenerativeAI
from app.tools import search_tool,execute_tool,homebites_tool
import os
from langchain_groq import ChatGroq

from dotenv import load_dotenv

load_dotenv()

# llm = ChatGroq(
#     groq_api_key=os.getenv("GROQ_API_KEY"),
#     model_name="deepseek-r1-distill-llama-70b",
#     temperature=0.3,
# )
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7
)

agent = initialize_agent(
    tools=[search_tool,execute_tool,homebites_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True 
)

def run_agent(query: str) -> str:
    return agent.run(query)
