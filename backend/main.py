from config import settings

from fastapi import FastAPI
import uvicorn

from routers.file_router import file_router
from routers.llm_router import llm_router


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
        description="""
        Retrival augemented generation for language model
        """,
        version="0.2"
        )

app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        )


app.include_router(file_router.router)
app.include_router(llm_router.router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        log_level="debug",
        reload=True,
    )
