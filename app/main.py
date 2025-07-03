from fastapi import FastAPI

app = FastAPI(title="MyndReader API", version="1.0.0")

@app.get("/")
def root():
    return {"message": "Welcome to MyndReader API"}