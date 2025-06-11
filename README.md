# MCP Agent code

This project is a modular agent framework that communicates with a local language model (Phi-4 via Ollama) running inside a Docker container.
It exposes an mcp:// URI-based tool protocol and provides both CLI and HTTP interfaces for interacting with tools like weather lookup, news headlines, and web search — all orchestrated by a LangChain-powered agent.

## What It Does

The application runs an interactive agent backed by LangChain and a locally hosted **Phi-4 model from Ollama**. It enables users to:

- Ask for **current weather** and **multi-day forecasts**
- Retrieve **top news headlines**
- Run **web search queries**
- Get responses via a **conversational CLI interface** or via a **FastAPI-based HTTP server**
  
All tools are invoked through a centralized **MCP JSON-RPC endpoint**, using custom URIs

## Project Structure

| File         | Purpose                                                                 |
|--------------|-------------------------------------------------------------------------|
| `main.py`    | Initializes the LangChain agent, registers tools, and runs the CLI chat loop. |
| `clients.py` | Sends `mcp://` URI-based requests to the backend server using JSON-RPC. |
| `tools.py`   | Implements tool logic: weather, forecasts, headlines, and web search.   |
| `server.py`  | Hosts a FastAPI app that routes MCP URI requests to the right tool.     |

## How to Use
### 1. Pull the LLM model via Ollama
```bash
ollama pull <model_name>
```
### 2. Run the Ollama container with full GPU access
```bash
docker pull ollama/ollama
docker run --gpus all -d -p 11434:11434 --name ollama -v path\to
your\dir\.ollama:/root/.ollama ollama/ollama
```
### 3. Create a `.env` file

<details>
<summary>📄 Example .env file (click to expand)</summary>
  
```env
OLLAMA_MODEL_NAME=phi-4
OLLAMA_API_URL=http://localhost:11434
OPENWEATHER_API_KEY=your_api_key
NEWS_API_KEY=your_api_key
MCP_SERVER_URL=http://localhost:8000/mcp
```
</details> 

### 4. Start the MCP JSON-RPC server

Run this to start the backend API:
```bash
python server.py
```
### 5. Start the CLI agent
In a separate terminal:
```bash
python main.py
```
Now you can interact with the agent via natural language:
<img width="1215" alt="image" src="https://github.com/user-attachments/assets/51925185-12de-4b06-9ebe-225fee757394" />
<img width="1216" alt="image" src="https://github.com/user-attachments/assets/e69c357b-4722-4674-a374-824ec5290c40" />
<img width="1220" alt="image" src="https://github.com/user-attachments/assets/09590018-af19-4c87-8b6b-6f06b8991842" />




   
