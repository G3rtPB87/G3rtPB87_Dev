import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

class SmargeAgent:
    def __init__(self):
        if not GOOGLE_API_KEY:
            print("Warning: GOOGLE_API_KEY not found in environment variables.")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.7
        )

    async def chat_stream(self, messages: list) -> AsyncGenerator[str, None]:
        langchain_messages = []
        
        # Add a system prompt
        langchain_messages.append(SystemMessage(content="You are SmargeAI, a helpful and intelligent AI assistant."))

        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
        
        async for chunk in self.llm.astream(langchain_messages):
            yield chunk.content
