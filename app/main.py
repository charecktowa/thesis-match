from fastapi import FastAPI
import uvicorn

from app.api.routes import professor
from app.api.routes import student

app = FastAPI()

# Include routers
app.include_router(professor.router, prefix="/api/v1")
app.include_router(student.router, prefix="/api/v1")


@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}


def main() -> None:
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
