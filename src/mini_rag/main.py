from fastapi import FastAPI

app = FastAPI(title="mini-RAG", version="0.1")

@app.get("/welcome")
def welcome_message():
    return {"message": "Welcome to mini-RAG! This is a simple FastAPI application."}