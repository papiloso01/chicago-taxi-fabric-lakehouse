"""Fabric lakehouse identifiers and OneLake path helpers."""
import re

IDENTIFIER = r"[A-Za-z_][A-Za-z_0-9]*"
DEFAULT_LAKEHOUSE = "lh_chicago_taxi"
# Inside a Fabric notebook the attached default lakehouse is mounted here for file APIs.
DEFAULT_MOUNT = "/lakehouse/default/"


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(IDENTIFIER, value):
        raise ValueError("Invalid identifier")
    return value


def table_name(value):
    """Schema-enabled lakehouses accept lakehouse.schema.table within the same workspace."""
    if not isinstance(value, str) or not re.fullmatch(rf"{IDENTIFIER}\.{IDENTIFIER}\.{IDENTIFIER}", value):
        raise ValueError("Expected lakehouse.schema.table identifier")
    return value


def qualified(lakehouse, schema, table):
    return table_name(f"{identifier(lakehouse)}.{identifier(schema)}.{identifier(table)}")


def spark_path(local_path):
    """Map the notebook file mount to the Spark-relative Files/ path; keep other paths as file URIs."""
    text = str(local_path).replace("\\", "/")
    if text.startswith(DEFAULT_MOUNT):
        return text[len(DEFAULT_MOUNT):]
    if text.startswith("abfss://"):
        return text
    if not text.startswith("/"):
        raise ValueError("Expected an absolute local, mounted or abfss path")
    return "file://" + text
