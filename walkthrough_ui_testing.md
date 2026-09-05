# Autonomous QA Agent - Demo Walkthrough

We have successfully built the core hackathon demo flow as outlined in your PRD!

## What was built
1. **Demo Target Application**:
   - `v1` (Working App) with `#checkout` button.
   - `v2` (Broken App) simulating a developer change to `#proceed-payment`.
2. **AI Healing Backend**:
   - A FastAPI service that executes Playwright tests.
   - Intercepts test failures, diagnoses DOM changes (mocked by default, can use OpenAI), and automatically rewrites the test script.
3. **Frontend Dashboard**:
   - A React/Tailwind UI to run the tests and visualize the real-time healing process and release decisions.

## How to Run the Demo

To show off your hackathon project, you will need to start three things (the demo static files, the backend, and the frontend).

### 1. Start the Backend API
The backend acts as the brain and runs the tests.
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```
*(If you have an OpenAI key, you can run `export OPENAI_API_KEY="sk-..."` before starting the server to use real GPT-4o for self-healing).*

### 2. Start the Frontend Dashboard
```bash
cd frontend
npm run dev
```
Open the provided `localhost` URL in your browser.

## Presenting the Demo
1. **Click "Target: App v1 (Original)"** and hit **Run Automated Test**.
   - You will see it successfully pass because the script works for `v1`.
2. **Click "Target: App v2 (Changed ID)"** and hit **Run Automated Test**.
   - The test will **FAIL**.
   - The UI will immediately switch to **"AI Healing..."** as the backend diagnoses the failure.
   - It will update the status to **"HEALED"**, show the root cause (`#checkout -> #proceed-payment`), give a "PASS" release decision, and **automatically rerun the test**.
   - The second test run will pass successfully.

This clearly demonstrates the "Detect → Understand → Heal → Validate → Explain → Decide" lifecycle perfectly!
