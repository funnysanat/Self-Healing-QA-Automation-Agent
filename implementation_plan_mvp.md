# Full MVP Implementation Plan

Now that we have the core "Self-Healing" hackathon demo working flawlessly, we need to build out the rest of the **MVP features** mentioned in your PRD so you can present a complete "Autonomous Quality Engineering Platform."

## Goal
Expand our current backend and frontend to include Change Detection, AI Test Generation, Multi-Dimensional Testing (Accessibility, Security, API), and Quality Intelligence.

## User Review Required
> [!WARNING]
> Building a true integration with Git PRs, OWASP, and Load Testing tools is usually a multi-week project. For the hackathon, we need to balance **real execution** with **smart simulation**. Please review the proposed approach below.

## Open Questions
> [!IMPORTANT]
> 1. Are you okay with simulating the "Git PR webhook" using a manual button on the dashboard to trigger the pipeline?
> 2. For multi-dimensional testing, I propose adding Axe (Accessibility) into our existing Playwright test. For Security and Performance, we can mock the test results. Does this sound like a good balance for the demo?

## Proposed Changes

### 1. Multi-Dimensional Testing Integration
We will extend our Playwright setup to do more than just UI testing.
- **[MODIFY] `backend/tests/test_checkout.py`**: 
  - Add `axe-playwright-python` (or similar library) to run an accessibility scan during the UI test.
  - Add a simple REST API ping to verify the backend (API Testing).
- **[MODIFY] `backend/requirements.txt`**: Add dependencies for accessibility testing.

### 2. Quality Intelligence & Release Risk
- **[MODIFY] `backend/main.py`**: 
  - Enhance the `/run-test` endpoint to return multi-dimensional results (UI: Pass, A11y: Warn, Security: Pass, Perf: Pass).
  - Implement the Risk Calculation: `Risk = Business Criticality × Change Impact × Test Failure Severity`
  - Update the Release Decision logic to output `🟢 PASS`, `🟡 WARN`, or `🔴 BLOCK`.

### 3. AI Test Generation & Change Detection (Simulation)
- **[MODIFY] `backend/main.py`**: Add a new endpoint `/generate-tests` that accepts a "Developer Change Description" (e.g., "Checkout button changed") and uses Gemini to output a list of generated test scenarios.
- **[MODIFY] `frontend/src/App.tsx`**: 
  - Add a "Pipeline Trigger" section mimicking a CI/CD or PR trigger.
  - Build a visually impressive dashboard section for **Multi-Dimensional Testing** showing badges for UI, API, Security, Accessibility, and Performance.
  - Build a section displaying the newly generated test cases by the AI.

## Verification Plan
1. **Trigger Pipeline**: User inputs a simulated developer commit in the UI.
2. **AI Generation**: Dashboard shows test cases generated dynamically by Gemini.
3. **Execution**: Multi-dimensional test runs (UI + API + A11y).
4. **Dashboard**: All metrics populate, calculating a final business-aware release decision.
