import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schema.action_schema import SanitizedContextPayload, StructuredAction
from app.vlm_agent import RemoteVLMAgent

app = FastAPI(
    title="Privacy-Preserving Remote VLM Reasoning Server",
    description="SIH PS 26171 Backend Server. Accepts ONLY sanitized context payloads.",
    version="1.0.0"
)

# Enable CORS for browser extension requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = RemoteVLMAgent()

@app.get("/health")
def health_check():
    return {"status": "healthy", "server_time": time.time()}

@app.post("/api/v1/reason", response_model=StructuredAction)
def reason_over_sanitized_context(payload: SanitizedContextPayload):
    # Verify that Privacy Boundary Report is attached and zero raw PII is verified
    if not payload.boundaryReport.zeroRawPIIVerified:
        raise HTTPException(
            status_code=400,
            detail="Security Violation: Egress payload failed independent zero-raw-PII boundary verification."
        )

    action = agent.plan_next_action(payload)
    return action

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
