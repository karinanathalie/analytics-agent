from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qpython import qconnection
from langchain_ollama import ChatOllama
import numpy as np

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

q = qconnection.QConnection(host="localhost", port=6000)
q.open()
llm = ChatOllama(model="llama3.2")

class QueryRequest(BaseModel):
    user_query: str

def get_q_query_from_llm(user_query: str) -> str:
    prompt = (
        "You are an expert in KDB+/Q for financial analytics.\n"
        "The table is named `trade` and has columns: time, sym, algo, volume, price, date, slippage.\n"
        "Given the user's request in English, respond with ONLY a valid Q query, nothing else.\n"
        "Never use '*' in select. Use: select from trade where ...\n"
        "If the user wants all columns, use: select from trade where ...\n"
        "If user asks for columns, use: select col1, col2 from trade where ...\n"
        f"User: {user_query}\nQ:"
    )
    response = llm.invoke(prompt)
    content = response.content.strip().splitlines()[0].strip()
    print("LLM Q query:", content)
    return content


def log_query_to_file(q_query: str, path: str = "trade.q"):
    """Append the Q query to trade.q for auditing"""
    with open(path, "a") as f:
        f.write(q_query + "\n")

def qtable_to_json(qtable):
    import numpy as np
    # Handle dict (typical table)
    if isinstance(qtable, dict) and qtable:
        columns = list(qtable.keys())
        n = len(qtable[columns[0]])
        rows = []
        for i in range(n):
            row = []
            for col in columns:
                val = qtable[col][i]
                if isinstance(val, np.generic):
                    val = val.item()
                row.append(val)
            rows.append(row)
        return {"columns": columns, "rows": rows}
    # Handle numpy structured arrays (list of tuples)
    elif hasattr(qtable, "dtype") and hasattr(qtable, "tolist"):
        # Convert structured numpy array to list of rows and columns
        try:
            arr = qtable
            columns = arr.dtype.names
            rows = arr.tolist()
            # Clean bytes to strings for display
            rows_clean = []
            for row in rows:
                new_row = [x.decode() if isinstance(x, bytes) else x for x in row]
                rows_clean.append(new_row)
            return {"columns": list(columns), "rows": rows_clean}
        except Exception as e:
            return {"text": str(qtable)}
    # Otherwise, fallback to text
    else:
        return {"text": str(qtable)}


@app.post("/ask")
async def ask(request: QueryRequest):
    user_query = request.user_query
    q_query = get_q_query_from_llm(user_query)
    print("query:", q_query)
    
    # Log the LLM-generated Q query
    log_query_to_file(q_query)

    try:
        result = q.sendSync(q_query)
        json_result = qtable_to_json(result)
        print("result:", result)
        return {"query": q_query, "result": json_result}
    except Exception as e:
        return {"error": str(e)}
