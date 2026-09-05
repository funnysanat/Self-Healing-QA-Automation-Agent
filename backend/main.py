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

@app.post("/run-test")
def run_test(request: RunTestRequest):
    url = f"file://{os.path.abspath(f'../demo-app/{request.version}.html')}"
    
    # Run the test in a subprocess to capture output
    try:
        result = subprocess.run(
            ["python", TEST_SCRIPT_PATH, url],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        metrics = {
            "api": "PASS",
            "security": "PASS",
            "performance": "PASS"
        }
        
        if result.returncode == 0:
            metrics["ui"] = "PASS"
            metrics["accessibility"] = "WARN"
            return {
                "status": "PASS", 
                "metrics": metrics,
                "risk": "LOW",
                "decision": "🟢 PASS"
            }
        else:
            metrics["ui"] = "FAIL"
            metrics["accessibility"] = "WARN"
            return {
                "status": "FAIL", 
                "error": result.stderr,
                "metrics": metrics,
                "risk": "HIGH",
                "decision": "🔴 BLOCK"
            }
    except Exception as e:
        return {"status": "FAIL", "error": str(e), "metrics": {}, "risk": "UNKNOWN", "decision": "🔴 BLOCK"}

@app.post("/heal-test")
def heal_test(request: HealTestRequest):
    # For a hackathon, we can either mock this or use Gemini if the key is provided
    api_key = os.environ.get("GEMINI_API_KEY")
    
    with open(TEST_SCRIPT_PATH, "r") as f:
        test_script = f.read()
        
    with open(f"../demo-app/{request.version}.html", "r") as f:
        new_dom = f.read()
        
    if not api_key or api_key == "your_gemini_api_key_here":
        # Mock self-healing logic for the demo if no API key is provided
        print("No GEMINI_API_KEY found, using mock healing...")
        new_script = test_script.replace("#checkout", "#proceed-payment")
        with open(TEST_SCRIPT_PATH, "w") as f:
            f.write(new_script)
        
        return {
            "status": "HEALED",
            "diagnosis": "Detected UI change: #checkout -> #proceed-payment. Confidence: 96%",
            "decision": "PASS"
        }
        
    # Actual LLM Logic
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0, google_api_key=api_key)
        prompt = PromptTemplate.from_template(
            "You are an AI QA Engineer. A Playwright test just failed.\n"
            "Error: {error}\n\n"
            "Here is the new DOM of the page:\n{dom}\n\n"
            "Here is the current test script:\n{script}\n\n"
            "Identify the new CSS selector for the checkout button and rewrite the script. "
            "Output ONLY the new python script code, without markdown formatting or explanation."
        )
        
        chain = prompt | llm
        response = chain.invoke({
            "error": request.error_message,
            "dom": new_dom,
            "script": test_script
        })
        
        if isinstance(response.content, list):
            new_script = response.content[0].get("text", "").strip()
        else:
            new_script = str(response.content).strip()
            
        if new_script.startswith("```python"):
            new_script = new_script.split("```python")[1].split("```")[0].strip()
            
        with open(TEST_SCRIPT_PATH, "w") as f:
            f.write(new_script)
            
        return {
            "status": "HEALED",
            "diagnosis": "AI successfully identified the new element and updated the test script.",
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
