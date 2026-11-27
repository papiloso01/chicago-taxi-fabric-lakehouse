"""Validate source definitions, reporting rules and silver/gold table contracts."""
from pathlib import Path
import re
import yaml

TABLE = r"[A-Za-z_][A-Za-z_0-9]*\.[A-Za-z_][A-Za-z_0-9]*\.[A-Za-z_][A-Za-z_0-9]*"


def has_column(schema_sql, column):
    return re.search(r"(?:^|,)\s*" + re.escape(column) + r"\s+", schema_sql) is not None


def validate(root="metadata"):
    root = Path(root)
    sources = yaml.safe_load((root / "sources.yml").read_text())
    names = [source["name"] for source in sources["sources"]]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate source names")
    for source in sources["sources"]:
        for required in ["endpoint", "natural_key", "status"]:
            if not source.get(required):
                raise ValueError("Missing source metadata: " + required)
        if not source["endpoint"].startswith("https://"):
            raise ValueError("Source must use HTTPS")
    reporting = yaml.safe_load((root / "reporting.yml").read_text())
    if not reporting.get("rules"):
        raise ValueError("Missing metric rules")
    for layer in ("silver", "gold"):
        warehouse = yaml.safe_load((root / (layer + "_tables.yml")).read_text())
        tables = warehouse.get("tables", [])
        identifiers = [table["name"] for table in tables]
        if not tables or len(identifiers) != len(set(identifiers)):
            raise ValueError("Missing or duplicate warehouse table metadata")
        by_short_name = {}
        for table in tables:
            if not re.fullmatch(TABLE, table["name"]) or table["name"].split(".")[1] != layer:
                raise ValueError("Invalid lakehouse.schema.table identifier")
            for required in ["key", "grain", "schema_sql", "format"]:
                if not table.get(required):
                    raise ValueError("Missing warehouse contract: " + required)
            keys = [table["key"]] if isinstance(table["key"], str) else table["key"]
            if not isinstance(keys, list) or not all(isinstance(key, str) for key in keys):
                raise ValueError("Invalid warehouse key")
            for key in keys:
                if not has_column(table["schema_sql"], key):
                    raise ValueError("Warehouse key absent from schema")
            by_short_name[table["name"].split(".")[-1]] = table
        for reference in warehouse.get("foreign_keys", []):
            for end in ["source", "target"]:
                table, column = reference[end].split(".")
                contract = by_short_name.get(table)
                if not contract or not has_column(contract["schema_sql"], column):
                    raise ValueError("Invalid warehouse foreign key")
    return len(names)


if __name__ == "__main__":
    print(f"Validated {validate()} source definitions, reporting rules and table contracts")
