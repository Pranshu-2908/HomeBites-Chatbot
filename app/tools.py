from langchain.tools import Tool
from app.db import db
import os
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import PromptTemplate

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.7
)

homebites_keywords = [
    "homebites", "meal", "chef", "customer", "order", "cart",
    "menu", "dashboard", "delivery", "homemade", "food", "kitchen",
    "profile", "notification", "review", "rating", "payment",
]

def is_homebites_query(query: str) -> bool:
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in homebites_keywords)

def homebites_tool_func(query: str) -> str:
    """
    Takes a natural language query and returns relevant information about HomeBites.
    """
    parser = StrOutputParser()
    prompt = PromptTemplate(
    input_variables=["question"],
    template="""
You are an AI assistant for a platform called HomeBites. You must only answer questions specifically about the HomeBites system.

System Description:
HomeBites is a platform that connects home chefs with customers looking for homemade food. 
Chefs can create profiles, list their meals, and manage orders. 
Customers can browse meals, place orders, and leave reviews.
The platform includes dashboards for chefs and customers, a cart for managing orders, and a notification system for updates.
It uses a secure card payment system, and only registered users who are logged in can add items to the cart and place orders.

Instructions:
- Only answer questions **directly related to the HomeBites system**.
- If the question is **not related to HomeBites**, respond with:
  "I can only answer questions about the HomeBites system."
- If the question **is** related to HomeBites, give a **detailed and factual answer** based only on the system description above.
- you can answer creatively and bit descriptive.
- Do **not** explain your reasoning.
- Do **not** show any thinking process.
- Do **not** use formatting like `<think>`, `Thought:`, `Action:`, or `Observation:`.
- Do **not** hallucinate or invent details.
- If you know the answer based on the description above, respond with:
  Final Answer: <your brief answer here>
- If you need to use a tool, respond with ONLY:
  Action: <tool name>
  Action Input: <input for the tool>
- Do not provide both Action and Final Answer at the same time.
- Do not output any "Thought", "Observation", or `<think>` statements.

Question: {question}
Answer:
"""
)
    chain = prompt | llm | parser
    result = chain.invoke({"question": query})
    print(f"*************************************{result}***********************************")
    return f"{result}"

# Create the tool
homebites_tool = Tool(
    name="HomeBitesAssistant",
    description="Answers questions about the HomeBites system. It does not answer general knowledge or web questions.",
    func=homebites_tool_func
)


def search_database(query: str) -> str:
    """
    Takes a natural language query and returns relevant information from MongoDB.
    """
    # Define the prompt to convert natural language to MongoDB query
    prompt = PromptTemplate(
        input_variables=["question"],
        template="""
You are an assistant that helps convert user questions into MongoDB queries.

Database: HomeBites
Collections: users (fields: role, name), orders (fields: chefId, customerId, status), meals (fields: name, chefId, quantity)

Question: {question}
When answering:
    Always resolve referenced fields first (e.g., if a question is find meals by "chef_name" or orders for "Customer_name" find the id from users schema and then use this id to find the main result).
    if user asks for something and that is not a field in the collection, try to resolve reference to the field in the collection. maybe it is a field in another collection.
    Example: if user asks for orders by "chef_name" or meals for "Customer_name", find the id from users schema and then use this id to find the main result.
    Don't assume that if meals of a chef are asked then there would be a field called chef_name in meals collection. The id of the chef is stored in the meals collection as chefId.
    Don't assume that if orders of a customer are asked then there would be a field called customer_name in orders collection. The id of the customer is stored in the orders collection as customerId.
Write the MongoDB query that returns the answer.
Use this format ONLY. Don't use any other format. I want this to be the only output format:
db.<collection>.method({{...}})
Do NOT use any placeholders. Respond with only the MongoDB query, no explanation.
"""
    )

    chain = prompt | llm

    result = chain.invoke({"question": query})
    print(f"*************************************{result.content}***********************************")
    return f"{result.content}"

search_tool = Tool(
    name="SearchDatabase",
    func=search_database,
    description="Use this to answer an questions about users, chefs, orders, or meals from the database."
)

def execute_query(query: str) -> str:
    """
    Executes a MongoDB query string like: db.collection.method({...})
    and returns the result.
    WARNING: This executes arbitrary MongoDB commands on your db!
    """

    if not query.startswith("db."):
        return "Invalid query format. Must start with 'db.'"

    try:
        # Define the limited globals for eval to access only 'db'
        allowed_globals = {"db": db}

        # Evaluate the query string safely in this limited context
        result = eval(query, allowed_globals, {})

        # If result is a cursor or iterable, convert to list
        if hasattr(result, "next") or hasattr(result, "__iter__"):
            try:
                return list(result)
            except Exception:
                # If cannot convert to list, just return str
                return str(result)

        return result

    except Exception as e:
        return f"Error executing query: {e}"
    

execute_tool = Tool(
    name="ExecuteQuery",
    func=execute_query,
    description="Executes a MongoDB query string like db.users.count_documents({{...}}) and returns the result."
)
