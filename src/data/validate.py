from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera import DataFrameSchema
from pandera.errors import SchemaErrors, SchemaError
import yaml

BASE_DIR = Path(__file__).resolve().parents[2]
PROC_DIR = BASE_DIR / "data" / "processed"
CONFIG_PATH = BASE_DIR / "configs" / "schema.yaml"


def _load_schema() -> DataFrameSchema:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Schema config not found: {CONFIG_PATH}")

    cfg = yaml.safe_load(CONFIG_PATH.read_text())
    columns_cfg = cfg.get("columns", [])
    if not columns_cfg:
        raise ValueError("schema.yaml contains no column definitions.")

    dtype_map: dict[str, pa.dtypes.DataType] = {
        "string": pa.String(),
        "float": pa.Float(),
        "float64": pa.Float(),
        "int": pa.Int(),
        "int64": pa.Int(),
        "bool": pa.Bool(),
        "boolean": pa.Bool(),
    }

    schema_columns: dict[str, pa.Column] = {}
    for col in columns_cfg:
        name = col["name"]
        dtype_key = str(col.get("dtype", "")).lower()
        dtype = dtype_map.get(dtype_key)
        if dtype is None:
            raise ValueError(f"Unsupported dtype '{dtype_key}' for column '{name}'.")
        nullable = bool(col.get("nullable", False))
        schema_columns[name] = pa.Column(dtype, nullable=nullable)

    return pa.DataFrameSchema(schema_columns, strict=True)


def main() -> int:
    dataset = PROC_DIR / "lca_labeled.csv"
    if not dataset.exists():
        print(f"[Validate] Missing processed dataset: {dataset}")
        print("[Validate] Run `python -m src.data.ingest` first.")
        return 1

    df = pd.read_csv(dataset)
    try:
        schema = _load_schema()
        schema.validate(df, lazy=True)
        print(f"[Validate] Dataset {dataset} passed schema validation.")
        return 0
    except SchemaErrors as err:
        print("[Validate] Schema validation failed:")
        print(err.failure_cases.to_string(index=False))
        return 2
    except SchemaError as err:
        print(f"[Validate] Schema validation failed: {err}")
        return 2
    except Exception as exc:  # defensive catch-all for configuration/runtime issues
        print(f"[Validate] Unexpected error: {exc}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
