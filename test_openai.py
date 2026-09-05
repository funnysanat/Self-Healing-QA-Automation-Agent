import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

load_dotenv("backend/.env")
openai_key = os.environ.get("OPENAI_API_KEY")
print("Key starts with:", openai_key[:10])

try:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=openai_key, max_retries=0)
    prompt = PromptTemplate.from_template("Say hello")
    chain = prompt | llm
    response = chain.invoke({})
    print("Success:", response.content)
except Exception as e:
    print("Error:", e)
