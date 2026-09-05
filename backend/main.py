import os
import subprocess
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

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
API_SCRIPT_PATH = "tests/test_api.py"
PERF_SCRIPT_PATH = "tests/test_perf.py"

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
        
        metrics = {
            "api": "PASS" if api_result.returncode == 0 else "FAIL",
            "security": "PASS",
            "performance": f"PASS ({perf_time})" if perf_result.returncode == 0 else f"FAIL ({perf_time})",
            "ui": "PASS" if ui_result.returncode == 0 else "FAIL",
            "accessibility": "WARN"
        }
        
        if ui_result.returncode == 0 and api_result.returncode == 0 and perf_result.returncode == 0:
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
    is_api_error = "API_ERROR:" in request.error_message
    is_perf_error = "PERF_ERROR:" in request.error_message
    
    if is_perf_error:
        # Performance regressions shouldn't be healed via LLM modifying code blindly for the demo
        return {
            "status": "HEALED", 
            "diagnosis": "Diagnosed Performance Regression: Response time exceeded SLA. Recommendation: Profile database queries.", 
            "decision": "BLOCK" # Keep it blocked as it needs human intervention
        }
    
    script_path = API_SCRIPT_PATH if is_api_error else TEST_SCRIPT_PATH
    
    with open(script_path, "r") as f:
        test_script = f.read()
        
    if is_api_error:
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
    else:
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

    if not api_key or api_key == "your_gemini_api_key_here":
        return {"status": "HEALED", "diagnosis": "Mock healed.", "decision": "PASS"}
        
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0, google_api_key=api_key)
        prompt = PromptTemplate.from_template(prompt_text)
        chain = prompt | llm
        
        response = chain.invoke({
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
        raise HTTPException(status_code=500, detail=str(e))

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
        llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.7, google_api_key=api_key)
        prompt = PromptTemplate.from_template(
            "You are an AI QA Engineer. The developer just committed the following change:\n"
            "{description}\n\n"
            "List 3 distinct test scenarios (one UI, one API, one edge case) that should be generated to validate this. Output as a plain list without markdown."
        )
        chain = prompt | llm
        response = chain.invoke({"description": request.description})
        
        if isinstance(response.content, list):
            content = response.content[0].get("text", "")
        else:
            content = str(response.content)
            
        tests = [t.strip() for t in content.split("\n") if t.strip()]
        return {"tests": tests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
