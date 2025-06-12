from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller.book import router as book_router

app = FastAPI(title="Library Management System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(book_router, tags=["books"])

@app.get("/")
def read_root():
    return {"message": "Library Management System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)