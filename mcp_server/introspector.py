from mcp_server.connectors.base import BaseConnector

NUMERIC_TYPES = {"INTEGER", "FLOAT", "DOUBLE", "BIGINT", "DECIMAL"}
STRING_TYPES  = {"VARCHAR", "TEXT", "STRING"}
TIME_TYPES    = {"TIMESTAMP", "DATE"}


def select_checks(column: str, col_type: str) -> list[str]:
    checks = ["null_rate"]

    if col_type.upper() in NUMERIC_TYPES:
        checks += ["distribution_stats", "z_score"]

    if col_type.upper() in STRING_TYPES:
        checks += ["cardinality", "unexpected_values"]

    if col_type.upper() in TIME_TYPES:
        checks += ["gap_detection", "ordering_check"]

    return checks


def introspect(connector: BaseConnector, table: str) -> dict[str, list[str]]:
    schema = connector.get_schema(table)
    return {col["column"]: select_checks(col["column"], col["type"]) for col in schema}
