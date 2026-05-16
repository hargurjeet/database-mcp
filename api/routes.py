import os
import shutil
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from mcp_server.connectors.duckdb_connector import DuckDBConnector
from mcp_server.tools.schema_tools import get_schema
from mcp_server.tools.null_tools import check_null_rates
from mcp_server.tools.volume_tools import get_row_count
from mcp_server.tools.distribution_tools import get_distribution_stats
from mcp_server.tools.cardinality_tools import get_cardinality
from mcp_server.tools.timestamp_tools import detect_timestamp_gaps
from agent.dispatcher import run_rca, save_report

router = APIRouter()

REPORTS_PATH = os.getenv("REPORTS_PATH", "./data/reports/")

_NUMERIC_TYPES = {"INTEGER", "FLOAT", "DOUBLE", "BIGINT", "DECIMAL"}
_STRING_TYPES  = {"VARCHAR", "TEXT", "STRING"}
_TIME_TYPES    = {"TIMESTAMP", "DATE"}


class DBConfig(BaseModel):
    db_type: str = "duckdb"
    db_path: str


def _make_connector(config: DBConfig) -> DuckDBConnector:
    if config.db_type != "duckdb":
        raise HTTPException(status_code=400, detail=f"Unsupported db_type: {config.db_type}")
    return DuckDBConnector(config.model_dump())


def _run_full_check(connector, table: str) -> dict:
    schema = get_schema(connector, table)
    result = {
        "schema": schema,
        "null_rates": check_null_rates(connector, table),
        "row_count": get_row_count(connector, table),
        "distribution_stats": {},
        "cardinality": {},
        "timestamp_gaps": {},
    }
    for col in schema:
        name = col["column"]
        col_type = col["type"].upper()
        if any(t in col_type for t in _NUMERIC_TYPES):
            result["distribution_stats"][name] = get_distribution_stats(connector, table, name)
        if any(t in col_type for t in _STRING_TYPES):
            result["cardinality"][name] = get_cardinality(connector, table, name)
        if any(t in col_type for t in _TIME_TYPES):
            result["timestamp_gaps"][name] = detect_timestamp_gaps(connector, table, name)
    return result


@router.post("/upload")
async def upload_db_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Only .db files are supported")
    upload_dir = os.path.join(os.getcwd(), "data", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    dest = os.path.join(upload_dir, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"db_path": dest, "filename": file.filename}


@router.get("/tables")
def list_tables(db_path: str, db_type: str = "duckdb"):
    config = DBConfig(db_type=db_type, db_path=db_path)
    connector = _make_connector(config)
    try:
        return {"tables": connector.list_tables()}
    finally:
        connector.close()


@router.post("/check/{table}")
def run_check(table: str, config: DBConfig):
    connector = _make_connector(config)
    try:
        return _run_full_check(connector, table)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connector.close()


@router.post("/rca/{table}")
def run_rca_endpoint(table: str, config: DBConfig):
    config_dict = {**config.model_dump(), "table": table}
    try:
        report = run_rca(config_dict)
        save_report(table, report)
        return {"table": table, "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{table}")
def get_report(table: str):
    path = os.path.join(REPORTS_PATH, f"{table}_rca.md")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"No report found for table '{table}'")
    with open(path) as f:
        return {"table": table, "report": f.read()}
