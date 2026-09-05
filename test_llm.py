import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv("backend/.env")
api_key = os.environ.get("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0, google_api_key=api_key)
prompt = PromptTemplate.from_template("Hello")
chain = prompt | llm
print(chain.invoke({}))
