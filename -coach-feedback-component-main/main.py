#!/opt/anaconda3/bin/python
"""
Main FastAPI application for the 32-hour integration sprint
Includes Parth's coach_feedback endpoint
"""

from fastapi import FastAPI
from pi.api.coach_feedback import router as coach_feedback_router

app = FastAPI(title="Assistant Demo API", version="1.0.0")

# Include the coach feedback router
app.include_router(coach_feedback_router)

@app.get("/")
def root():
    return {"message": "Assistant Demo API - 32-Hour Integration Sprint", "status": "active"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "component": "coach_feedback"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)