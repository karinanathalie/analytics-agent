from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qpython import qconnection
from langchain_ollama import ChatOllama


app = FastAPI()

# CORS for Frontend Connections
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# Connect to Q server
q = qconnection.QConnection(host="localhost", port=6000)
q.open()

# Load Ollama Model
llm = ChatOllama(model="llama3.2")

# Request Model
class QueryRequest(BaseModel):
    user_query: str

# LLM Prompt
def get_q_query_from_llm(user_query: str) -> str:
    prompt = ("""You are an expert in KDB+/Q for financial analytics.
              The table is named `trade` and has columns: time, sym, algo, volume, price, date, slippage.
              Given the user's English request, respond with only a valid KDB+/Q query.
              Always start with `select from trade` and use the columns provided.
              User: {user_query}
              QL select from trade where volume > 1000\n"""
              f"User: {user_query} Q:")
    response = llm.invoke(prompt)
    content = response.content.strip()
    return content

# Fast API Route
@app.post("/ask")
async def ask(request: QueryRequest):
    user_query = request.user_query
    q_query = get_q_query_from_llm(user_query)
    
    # Execute Q query
    try:
        result = q.sendSync(q_query)
        print(result)
        return {"query": q_query, "result": result}
    except Exception as e:
        return {"error": str(e)}