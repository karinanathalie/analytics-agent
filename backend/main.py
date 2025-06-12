import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qpython import qconnection
from dotenv import load_dotenv
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
import pandas as pd
import smtplib
from email.message import EmailMessage
import tempfile

# Load .env variables
load_dotenv()

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

# Load OpenAI LLM via LangChain
llm = ChatOpenAI(openai_api_key=os.environ["OPENAI_API_KEY"], model="gpt-4o")

# Converts q table to JSON with columns/rows
def qtable_to_json(qtable):
    columns = qtable.keys()
    rows = list(zip(*qtable.values()))
    # decode bytes to string if necessary
    rows = [[cell.decode() if isinstance(cell, bytes) else cell for cell in row] for row in rows]
    return {"columns": columns, "rows": rows}

# Tool 1: Run Q Query
def run_q_query(q_query: str) -> dict:
    try:
        result = q.sendSync(q_query)
        return qtable_to_json(result)
    except Exception as e:
        return {"error": str(e)}

# Tool 2: Explain Q Query
def explain_q_query(q_query: str) -> str:
    prompt = f"Explain in simple English what this Q query does:\n{q_query}"
    return llm.invoke(prompt).content.strip()

# Tool 3: Table to CSV
def table_to_csv(table_json: dict) -> str:
    df = pd.DataFrame(table_json["rows"], columns=table_json["columns"])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", encoding='utf-8') as tmp:
        df.to_csv(tmp.name, index=False)
        tmp.flush()
        tmp.seek(0)
        return tmp.read()

# Tool 4: Summarize Table
def summarize_table(table_json: dict) -> str:
    prompt = f"Summarize this trade table:\nColumns: {table_json['columns']}\nRows: {table_json['rows']}"
    return llm.invoke(prompt).content.strip()

# Tool 5: Send Email with Attachment
def send_email_with_attachment(to_email: str, subject: str, body: str, csv_content: str) -> str:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = os.environ["EMAIL_USER"]
    msg["To"] = to_email
    msg.set_content(body)

    # Attach CSV
    msg.add_attachment(csv_content, filename="trade_results.csv", subtype="csv", maintype="text")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
            smtp.send_message(msg)
        return f"Email sent to {to_email}"
    except Exception as e:
        return f"Failed to send email: {str(e)}"

# Agent Tools 
tools = [
    Tool(
        name="run_q_query",
        func=run_q_query,
        description="Run a KDB+/Q query and return results as a table (JSON: columns/rows). Input: Q code string"
    ),
    Tool(
        name="explain_q_query",
        func=explain_q_query,
        description="Explain what a KDB+/Q query does in simple English. Input: Q code string"
    ),
    Tool(
        name="table_to_csv",
        func=table_to_csv,
        description="Convert a Q table (JSON format) to CSV format. Input: Table as JSON"
    ),
    Tool(
        name="summarize_table",
        func=summarize_table,
        description="Summarize a trade table (columns/rows JSON) in English. Input: Table as JSON"
    ),
    Tool(
        name="send_email_with_attachment",
        func=send_email_with_attachment,
        description="Send table (CSV string) to an email address. Input: email, subject, body, csv_content"
    )
]

# LangChain Agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent="openai-functions",
    verbose=True,
)

# API INput Model
class QueryRequest(BaseModel):
    user_query: str

@app.post("/agent")
async def agentic_query(request: QueryRequest):
    user_query = request.user_query
    result = agent.run(user_query)
    return {"result": result}
