import re

with open("backend/main.py", "r") as f:
    content = f.read()

# Add OpenAI import
if "from langchain_openai import ChatOpenAI" not in content:
    content = content.replace("from langchain_google_genai import ChatGoogleGenerativeAI", "from langchain_google_genai import ChatGoogleGenerativeAI\nfrom langchain_openai import ChatOpenAI")

# Create a helper function
helper_func = """
def invoke_llm(prompt_text, inputs, temperature=0):
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    last_exception = None
    
    # Try Gemini first
    if gemini_key and gemini_key != "your_gemini_api_key_here":
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=temperature, google_api_key=gemini_key, max_retries=0)
            prompt = PromptTemplate.from_template(prompt_text)
            chain = prompt | llm
            response = chain.invoke(inputs)
            return response
        except Exception as e:
            last_exception = e
            print(f"Gemini failed: {e}. Falling back to OpenAI...")
            
    # Try OpenAI next
    if openai_key and openai_key != "your_openai_api_key_here":
        try:
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=temperature, openai_api_key=openai_key, max_retries=0)
            prompt = PromptTemplate.from_template(prompt_text)
            chain = prompt | llm
            response = chain.invoke(inputs)
            return response
        except Exception as e:
            last_exception = e
            print(f"OpenAI failed: {e}.")
            
    if last_exception:
        raise last_exception
    else:
        raise Exception("No valid API keys found for LLM invocation.")
"""

if "def invoke_llm(" not in content:
    content = content.replace("app = FastAPI()", helper_func + "\napp = FastAPI()")

# Replace manual LLM invocation in logs diagnosis
logs_old = """            llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0, google_api_key=api_key, max_retries=0)
            prompt = PromptTemplate.from_template(
                "You are an AI SRE. A backend application log has thrown an error.\\n"
                "Logs:\\n{logs}\\n\\n"
                "Analyze the stack trace and provide a concise, 1-sentence explanation of the root cause. "
                "Output ONLY the explanation."
            )
            chain = prompt | llm
            response = chain.invoke({"logs": log_data})"""

logs_new = """            prompt_text = (
                "You are an AI SRE. A backend application log has thrown an error.\\n"
                "Logs:\\n{logs}\\n\\n"
                "Analyze the stack trace and provide a concise, 1-sentence explanation of the root cause. "
                "Output ONLY the explanation."
            )
            response = invoke_llm(prompt_text, {"logs": log_data})"""
content = content.replace(logs_old, logs_new)

# Replace manual LLM invocation in API/UI healing
api_ui_old = """        llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0, google_api_key=api_key, max_retries=0)
        prompt = PromptTemplate.from_template(prompt_text)
        chain = prompt | llm
        
        response = chain.invoke({
            "error": request.error_message,
            "context": context_data,
            "script": test_script
        })"""

api_ui_new = """        response = invoke_llm(prompt_text, {
            "error": request.error_message,
            "context": context_data,
            "script": test_script
        })"""
content = content.replace(api_ui_old, api_ui_new)

# Replace manual LLM invocation in generate-tests
gen_old = """        llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.7, google_api_key=api_key)
        prompt = PromptTemplate.from_template(
            "You are an AI QA Engineer. The developer just committed the following change:\\n"
            "{description}\\n\\n"
            "List 3 distinct test scenarios (one UI, one API, one edge case) that should be generated to validate this. Output as a plain list without markdown."
        )
        chain = prompt | llm
        response = chain.invoke({"description": request.description})"""

gen_new = """        prompt_text = (
            "You are an AI QA Engineer. The developer just committed the following change:\\n"
            "{description}\\n\\n"
            "List 3 distinct test scenarios (one UI, one API, one edge case) that should be generated to validate this. Output as a plain list without markdown."
        )
        response = invoke_llm(prompt_text, {"description": request.description}, temperature=0.7)"""
content = content.replace(gen_old, gen_new)


with open("backend/main.py", "w") as f:
    f.write(content)

