from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qpython import qconnection
from langchain_community.llms import Ollama

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
q = qconnection.Qconnection(host="localhost", port=6000)
q.open()