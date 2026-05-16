from dotenv import load_dotenv
from fastapi import FastAPI
from api.routes import router

load_dotenv()

app = FastAPI(
    title="Database MCP — REST API",
    description="Data quality checks and RCA reports over a DuckDB database.",
    version="1.0.0",
)

app.include_router(router)
