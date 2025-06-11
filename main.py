import os
import logging
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain.tools import Tool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

# Import project‑specific tool clients
from clients import (
    get_weather_client,
    get_forecast_client,
    get_news_headlines_client,
    search_web_client,  # DuckDuckGo wrapper
)

# Load environment variables and set up logging
load_dotenv()
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# Silence overly chatty network libraries
for noisy in ("httpcore.http11", "httpcore.connection", "httpx", "urllib3"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

# Create the Ollama LLM and stream tokens to the console as they arrive
llm = OllamaLLM(
    model=os.getenv("OLLAMA_MODEL_NAME"),
    base_url=os.getenv("OLLAMA_API_URL"),
    temperature=0.1,
)

# Keep the full conversation so the agent remembers what was said
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
)

# Register each MCP tool the agent is allowed to call
tools = [
    Tool(
        name="get_weather",
        func=get_weather_client,
        description="Get current weather for a city. Input: city name.",
    ),
    Tool(
        name="get_forecast",
        func=get_forecast_client,
        description="Get an N‑day weather forecast. Input: 'city|days'.",
    ),
    Tool(
        name="get_news_headlines",
        func=get_news_headlines_client,
        description="Get top news headlines. Input: optional 'category|country'.",
    ),
    Tool(
        name="search_web",
        func=search_web_client,
        description="Run a web search for the given query.",
    ),
]

# Build the agent that orchestrates the tools and language model
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, #AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=False,
    handle_parsing_errors=True,
    early_stopping_method="generate",
)


def chat() -> None:
    """Run a simple REPL so you can chat with the agent."""
    print("🗣  Chat with your agent – type 'exit' to quit.")
    while True:
        try:
            user_input = input("\n🙂 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("Exiting...")
            break
        if not user_input:
            continue
        try:
            result = agent.invoke({"input": user_input})["output"]
            print(f"\n🤖 Agent: {result}")
        except Exception as exc:
            logging.exception("LLM/agent error")
            print(f"⚠️  {exc}")


if __name__ == "__main__":
    chat()
