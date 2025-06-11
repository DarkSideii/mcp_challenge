import os
import logging
from dotenv import load_dotenv
from langchain_ollama import OllamaLLM
from langchain.tools import StructuredTool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.prompts import MessagesPlaceholder

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
chat_history = MessagesPlaceholder(variable_name="chat_history")
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

# Register each MCP tool the agent is allowed to call
tools = [
    StructuredTool.from_function(
        get_weather_client,
        name="get_weather",
        description="Get current weather for a city.",
        return_direct=True
    ),
    StructuredTool.from_function(
        get_forecast_client,
        name="get_forecast",
        description="Get an N-day weather forecast for a city.",
        return_direct=True
    ),
    StructuredTool.from_function(
        get_news_headlines_client,
        name="get_news_headlines",
        description=(
            "Retrieve the latest news headlines for one of the following categories: "
            "business, entertainment, general, health, science, sports, or technology. "
            "Optionally filter results by country using a two-letter ISO code."
        ),
        return_direct=True
    ),
    StructuredTool.from_function(
        search_web_client,
        name="search_web",
        description="Run a web search for the given query and return the top results.",
        return_direct=True
    ),
]

# Build the agent that orchestrates the tools and language model
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory,
    verbose=False,
    handle_parsing_errors=True,
    early_stopping_method="generate",
    agent_kwargs={
            # tells the prompt to inject your chat history here:
            "memory_prompts": [chat_history],
            # ensure the prompt template knows about this variable:
            "input_variables": ["input", "agent_scratchpad", "chat_history"],
        },
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
