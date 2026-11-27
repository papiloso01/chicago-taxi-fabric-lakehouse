"""Offline structural checks for the Git-synced Fabric workspace items under fabric/."""
import json
from pathlib import Path

KINDS = {"Notebook", "DataPipeline", "Lakehouse", "Environment"}


def validate(root="fabric"):
    root = Path(root)
    items, logical_ids = {}, set()
    for folder in sorted(path for path in root.iterdir() if path.is_dir()):
        name, _, kind = folder.name.rpartition(".")
        platform = json.loads((folder / ".platform").read_text())
        meta = platform["metadata"]
        if kind not in KINDS or meta["type"] != kind or meta["displayName"] != name:
            raise ValueError("Item folder does not match its .platform: " + folder.name)
        logical_id = platform["config"]["logicalId"]
        if logical_id in logical_ids:
            raise ValueError("Duplicate logicalId: " + folder.name)
        logical_ids.add(logical_id)
        items[logical_id] = (kind, name)
        if kind == "Notebook":
            text = (folder / "notebook-content.py").read_text()
            if not text.startswith("# Fabric notebook source") or text.count("# PARAMETERS CELL") != 1:
                raise ValueError("Notebook needs the Fabric header and exactly one parameters cell: " + name)
            if "notebookutils.notebook.exit(" not in text:
                raise ValueError("Notebook must return a JSON exit value for the pipeline: " + name)
    for folder in root.glob("*.DataPipeline"):
        properties = json.loads((folder / "pipeline-content.json").read_text())["properties"]
        names = [activity["name"] for activity in properties["activities"]]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate pipeline activity")
        for activity in properties["activities"]:
            for dependency in activity.get("dependsOn", []):
                if dependency["activity"] not in names:
                    raise ValueError("Unknown activity dependency: " + dependency["activity"])
            if activity["type"] == "TridentNotebook":
                target = items.get(activity["typeProperties"]["notebookId"])
                if not target or target[0] != "Notebook":
                    raise ValueError("Pipeline references a notebook that is not in fabric/: " + activity["name"])
                for parameter in activity["typeProperties"].get("parameters", {}).values():
                    value = parameter["value"]
                    if isinstance(value, dict) and value.get("value", "").startswith("@pipeline().parameters."):
                        if value["value"].split(".")[-1] not in properties.get("parameters", {}):
                            raise ValueError("Undeclared pipeline parameter in " + activity["name"])
    return len(items)


if __name__ == "__main__":
    print(f"Validated {validate()} Fabric workspace items")
