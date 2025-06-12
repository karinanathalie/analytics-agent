from langchain_ollama import ChatOllama

# Load local Ollama LLM
llm = ChatOllama(model="llama3.2")

# Create a robust prompt
prompt = """You are an expert in KDB+/Q.
The table is named `trade` and has columns: time, sym, algo, volume, price, date, slippage.
Given the user's English request, respond with only a valid KDB+/Q query.
Always start with `select from trade` and use the columns provided.
User: Show trades above 1000 shares.
Q:"""

# Run inference
response = llm.invoke(prompt)

# Print output
result = response.content
print(result)