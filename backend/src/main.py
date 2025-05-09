from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Cyber-Med-Agent Backend is running"}
