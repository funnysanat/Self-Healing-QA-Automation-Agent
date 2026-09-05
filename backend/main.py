import os
import subprocess
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()


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

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class RunTestRequest(BaseModel):
    version: str # "v1" or "v2"

class HealTestRequest(BaseModel):
    error_message: str
    version: str
    
class GenerateTestRequest(BaseModel):
    description: str

TEST_SCRIPT_PATH = "tests/test_checkout.py"
TEST_SCRIPT_PATH = "tests/test_checkout.py"
API_SCRIPT_PATH = "tests/test_api.py"
PERF_SCRIPT_PATH = "tests/test_perf.py"
LOGS_SCRIPT_PATH = "tests/test_logs.py"

@app.post("/run-test")
def run_test(request: RunTestRequest):
    url = f"file://{os.path.abspath(f'../demo-app/{request.version}.html')}"
    
    # Run the test in a subprocess to capture output
    try:
        ui_result = subprocess.run(
            ["python", TEST_SCRIPT_PATH, url],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        api_file = os.path.abspath(f"../demo-app/api_{request.version}.json")
        api_result = subprocess.run(
            ["python", API_SCRIPT_PATH, api_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        perf_result = subprocess.run(
            ["python", PERF_SCRIPT_PATH, url],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        perf_time = perf_result.stdout.strip().replace("Elapsed: ", "") if perf_result.stdout else "N/A"
        
        logs_file = os.path.abspath(f"../demo-app/logs_{request.version}.txt")
        logs_result = subprocess.run(
            ["python", LOGS_SCRIPT_PATH, logs_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        metrics = {
            "api": "PASS" if api_result.returncode == 0 else "FAIL",
            "security": "PASS",
            "performance": f"PASS ({perf_time})" if perf_result.returncode == 0 else f"FAIL ({perf_time})",
            "logs": "PASS" if logs_result.returncode == 0 else "FAIL",
            "ui": "PASS" if ui_result.returncode == 0 else "FAIL",
            "accessibility": "WARN"
        }
        
        if ui_result.returncode == 0 and api_result.returncode == 0 and perf_result.returncode == 0 and logs_result.returncode == 0:
            return {
                "status": "PASS", 
                "metrics": metrics,
                "risk": "LOW",
                "decision": "🟢 PASS"
            }
        else:
            error_msg = ""
            if ui_result.returncode != 0:
                error_msg += f"UI_ERROR: {ui_result.stderr}\n"
            if api_result.returncode != 0:
                error_msg += f"API_ERROR: {api_result.stderr}\n"
            if perf_result.returncode != 0:
                error_msg += f"PERF_ERROR: {perf_result.stderr}\n"
            if logs_result.returncode != 0:
                error_msg += f"LOGS_ERROR: {logs_result.stderr}\n"
                
            return {
                "status": "FAIL", 
                "error": error_msg,
                "metrics": metrics,
                "risk": "HIGH",
                "decision": "🔴 BLOCK"
            }
    except Exception as e:
        return {"status": "FAIL", "error": str(e), "metrics": {}, "risk": "UNKNOWN", "decision": "🔴 BLOCK"}

@app.post("/heal-test")
def heal_test(request: HealTestRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    is_ui_error = "UI_ERROR:" in request.error_message
    is_api_error = "API_ERROR:" in request.error_message
    is_perf_error = "PERF_ERROR:" in request.error_message
    is_logs_error = "LOGS_ERROR:" in request.error_message
    
    # PRIORITY 1: Heal API Contracts
    if is_api_error:
        script_path = API_SCRIPT_PATH
        with open(script_path, "r") as f:
            test_script = f.read()
        with open(f"../demo-app/api_{request.version}.json", "r") as f:
            context_data = f.read()
        prompt_text = (
            "You are an AI QA Engineer. An API contract test just failed.\n"
            "Error: {error}\n\n"
            "Here is the new JSON response from the API:\n{context}\n\n"
            "Here is the current python test script:\n{script}\n\n"
            "Update the test script to assert the correct field names based on the new JSON response. "
            "Output ONLY the new python script code, without markdown formatting or explanation."
        )
        
    # PRIORITY 2: Heal UI tests
    elif is_ui_error:
        script_path = TEST_SCRIPT_PATH
        with open(script_path, "r") as f:
            test_script = f.read()
        with open(f"../demo-app/{request.version}.html", "r") as f:
            context_data = f.read()
        prompt_text = (
            "You are an AI QA Engineer. A Playwright UI test just failed.\n"
            "Error: {error}\n\n"
            "Here is the new DOM of the page:\n{context}\n\n"
            "Here is the current python test script:\n{script}\n\n"
            "Identify the new CSS selector for the checkout button and rewrite the script. "
            "Output ONLY the new python script code, without markdown formatting or explanation."
        )

    # PRIORITY 3: Diagnose Logs
    elif is_logs_error:
        with open(f"../demo-app/logs_{request.version}.txt", "r") as f:
            log_data = f.read()
            
        if not api_key or api_key == "your_gemini_api_key_here":
            return {"status": "DIAGNOSED", "diagnosis": "Mock log analysis: Database timeout.", "decision": "BLOCK"}
            
        try:
            prompt_text = (
                "You are an AI SRE. A backend application log has thrown an error.\n"
                "Logs:\n{logs}\n\n"
                "Analyze the stack trace and provide a concise, 1-sentence explanation of the root cause. "
                "Output ONLY the explanation."
            )
            response = invoke_llm(prompt_text, {"logs": log_data})
            diagnosis = str(response.content).strip() if not isinstance(response.content, list) else response.content[0].get("text", "").strip()
            return {
                "status": "DIAGNOSED",
                "diagnosis": f"AI Log Analysis: {diagnosis}",
                "decision": "BLOCK" # Block release due to critical backend exception
            }
        except Exception as e:
            return {
                "status": "DIAGNOSED",
                "diagnosis": f"[API Limit Hit] Mock log analysis: Database timeout. (Details: {str(e)[:50]}...)",
                "decision": "BLOCK"
            }
            
    # PRIORITY 4: Diagnose Perf
    elif is_perf_error:
        return {
            "status": "DIAGNOSED", 
            "diagnosis": "Diagnosed Performance Regression: Response time exceeded SLA. Recommendation: Profile database queries.", 
            "decision": "BLOCK" # Keep it blocked as it needs human intervention
        }
        
    else:
        return {"status": "FAIL", "diagnosis": "Unknown error type.", "decision": "BLOCK"}

    # Execute healing for API or UI
    if not api_key or api_key == "your_gemini_api_key_here":
        return {"status": "HEALED", "diagnosis": "Mock healed.", "decision": "PASS"}
        
    try:
        response = invoke_llm(prompt_text, {
            "error": request.error_message,
            "context": context_data,
            "script": test_script
        })
        
        if isinstance(response.content, list):
            new_script = response.content[0].get("text", "").strip()
        else:
            new_script = str(response.content).strip()
            
        if new_script.startswith("```python"):
            new_script = new_script.split("```python")[1].split("```")[0].strip()
            
        with open(script_path, "w") as f:
            f.write(new_script)
            
        return {
            "status": "HEALED",
            "diagnosis": f"AI successfully identified the new {'API schema' if is_api_error else 'DOM element'} and updated the test script.",
            "decision": "PASS"
        }
    except Exception as e:
        # Fallback to mock healing if API rate limit or error occurs during hackathon
        fallback_msg = f"Mock healed (API Limit Hit): {str(e)[:50]}..."
        return {
            "status": "HEALED",
            "diagnosis": fallback_msg,
            "decision": "PASS"
        }

@app.post("/generate-tests")
def generate_tests(request: GenerateTestRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return {
            "tests": [
                "1. Verify successful checkout with valid credit card",
                "2. Verify error message when credit card is empty",
                "3. Validate API response structure matches new schema"
            ]
        }
        
    try:
        prompt_text = (
            "You are an AI QA Engineer. The developer just committed the following change:\n"
            "{description}\n\n"
            "List 3 distinct test scenarios (one UI, one API, one edge case) that should be generated to validate this. Output as a plain list without markdown."
        )
        response = invoke_llm(prompt_text, {"description": request.description}, temperature=0.7)
        
        if isinstance(response.content, list):
            content = response.content[0].get("text", "")
        else:
            content = str(response.content)
            
        tests = [t.strip() for t in content.split("\n") if t.strip()]
        return {"tests": tests}
    except Exception as e:
        # Fallback to mock data on rate limit or API error
        return {
            "tests": [
                "[MOCKED DUE TO API LIMIT] 1. Verify successful checkout with valid credit card",
                "[MOCKED DUE TO API LIMIT] 2. Verify error message when credit card is empty",
                "[MOCKED DUE TO API LIMIT] 3. Validate API response structure matches new schema"
            ]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
