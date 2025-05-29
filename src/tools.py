from langchain.tools import Tool
from src.db import db
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
    prompt = PromptTemplate(
        input_variables=["question"],
        template='''You are an assistant that converts user questions into MongoDB queries for the HomeBites database.

Collections:
    1) users: role, name, email
    2) orders: chefId, customerId, status
    3) meals: name, chefId, quantity, cuisine, price, category, description
    4) carts: customerId, mealId

Instructions:
    * Only use the following collections and their fields: users("role","name","email"), orders("chefId","customerId","status"), meals("name", "chefId", "quantity", "cuisine", "price", "category", "description"), carts("customerId", "mealId"). Do not query any other collection or use any other fields.
    * If the user asks to delete, update, or drop any document or collection, respond with:
    * I cannot delete or update anything in the database.

    * Always resolve references properly:
        - If a question involves names (e.g., chef name or customer name), first query the users collection to get the corresponding _id.
        - Then use that ID to query the relevant collection field (e.g., chefId, customerId).
        - Chefs and Customers are both stored in the users collection, so always resolve names through this collection.
    * Do not assume names exist in other collections—always resolve them through the users collection.
    * Use only MongoDB shell-compatible methods (e.g., find, countDocuments, aggregate) that do not modify or delete data.
Output Format:
Always return only the MongoDB query in this format as a string:
db.<collection>.<method>({{"<Field>":"<value>"}})
No explanations, no placeholders, and no extra text.'''
    )

    chain = prompt | llm

    result = chain.invoke({"question": query})
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
    forbidden_keywords = [
        "deleteOne", "deleteMany", "remove",
        "findOneAndDelete", "findByIdAndDelete",
        "findOneAndRemove", "findByIdAndRemove",
        "updateOne", "updateMany", "update", "replaceOne",
        "findOneAndUpdate", "findByIdAndUpdate", "findAndModify",
        "save", "drop", "dropCollection", "db.dropDatabase"
    ]

    for forbidden in forbidden_keywords:
        if forbidden in query:
            return "Dangerous operation detected: delete, update, or drop operations are not allowed."
    try:
        allowed_globals = {"db": db}
        result = eval(query, allowed_globals, {})

        if hasattr(result, "next") or hasattr(result, "__iter__"):
            try:
                return list(result)
            except Exception:
                return str(result)

        return result

    except Exception as e:
        return f"Error executing query: {e}"
    

execute_tool = Tool(
    name="ExecuteQuery",
    func=execute_query,
    description="Executes a MongoDB query string like db.users.count_documents({{...}}) and returns the result."
)
