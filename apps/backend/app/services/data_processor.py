import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pandas as pd
from dotenv import load_dotenv
from fastapi import HTTPException


load_dotenv()


def _parse_raw_payload(raw_data: Any) -> Dict[str, Any]:
    if raw_data is None:
        return {}

    if isinstance(raw_data, dict):
        return raw_data

    if isinstance(raw_data, str):
        try:
            return json.loads(raw_data)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="Received non-JSON payload from OpenAI") from exc

    raise HTTPException(status_code=502, detail="Unsupported data format returned by OpenAI")


def _resolve_data_source() -> Path:
    path_value = os.getenv("DATA_SOURCE_PATH")
    if not path_value:
        raise HTTPException(status_code=500, detail="Data source path is not configured")

    source_path = Path(path_value).expanduser()
    if not source_path.exists():
        raise HTTPException(status_code=500, detail=f"Data source file not found: {source_path}")

    if not source_path.is_file():
        raise HTTPException(status_code=500, detail="Configured data source is not a file")

    return source_path


@lru_cache(maxsize=1)
def _load_dataset() -> pd.DataFrame:
    source_path = _resolve_data_source()
    try:
        dataframe = pd.read_excel(source_path)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=f"Unable to read data source: {exc}") from exc

    if dataframe.empty:
        raise HTTPException(status_code=500, detail="Data source is empty")

    return dataframe


def _validate_columns(columns: Iterable[str], dataframe: pd.DataFrame) -> List[str]:
    if columns is None:
        return []

    if not isinstance(columns, list) or not all(isinstance(col, str) for col in columns):
        raise HTTPException(status_code=422, detail="'columns' must be a list of column names")

    normalized: List[str] = []
    missing: List[str] = []
    for column in columns:
        if column in dataframe.columns:
            normalized.append(column)
        else:
            missing.append(column)

    if missing and not normalized:
        raise HTTPException(
            status_code=422,
            detail=f"Requested columns not found in data source: {missing}",
        )

    return normalized


def _aggregate_raw_records(dataframe: pd.DataFrame, columns: List[str]) -> List[Dict[str, Any]]:
    if not columns:
        return dataframe.to_dict(orient="records")

    filtered_df = dataframe[columns]
    return filtered_df.to_dict(orient="records")


def _aggregate_non_zero_count(
    dataframe: pd.DataFrame,
    columns: List[str],
    value_field: str,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for column in columns:
        numeric_series = pd.to_numeric(dataframe[column], errors="coerce").fillna(0)
        count = int(numeric_series.ne(0).sum())
        results.append({"column": column, value_field: count})

    return results


def _aggregate_zero_count(
    dataframe: pd.DataFrame,
    columns: List[str],
    value_field: str,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for column in columns:
        numeric_series = pd.to_numeric(dataframe[column], errors="coerce").fillna(0)
        count = int((numeric_series == 0).sum())
        results.append({"column": column, value_field: count})

    return results


def _get_default_numeric_columns(dataframe: pd.DataFrame, exclude: Iterable[str] | None = None) -> List[str]:
    exclude_set = set(exclude or [])
    configured = os.getenv("EXCEPTION_COLUMNS")

    if configured:
        configured_columns = [col.strip() for col in configured.split(",") if col.strip()]
        valid_configured = [col for col in configured_columns if col in dataframe.columns and col not in exclude_set]
        if valid_configured:
            return valid_configured

    numeric_columns = [
        column
        for column in dataframe.columns
        if column not in exclude_set and pd.api.types.is_numeric_dtype(dataframe[column])
    ]

    if not numeric_columns:
        raise HTTPException(status_code=422, detail="No numeric columns available for aggregation")

    return numeric_columns


def _resolve_numeric_columns(
    columns: Iterable[str] | None,
    dataframe: pd.DataFrame,
    exclude: Iterable[str] | None = None,
) -> List[str]:
    exclude_set = set(exclude or [])
    validated = _validate_columns(columns, dataframe)

    numeric_columns: List[str] = []
    non_numeric: List[str] = []
    for column in validated:
        if column in exclude_set:
            continue
        if pd.api.types.is_numeric_dtype(dataframe[column]):
            numeric_columns.append(column)
        else:
            non_numeric.append(column)

    if non_numeric:
        raise HTTPException(
            status_code=422,
            detail=f"Columns must be numeric for aggregation: {non_numeric}",
        )

    if numeric_columns:
        return numeric_columns

    return _get_default_numeric_columns(dataframe, exclude)


def _aggregate_non_zero_count_by_group(
    dataframe: pd.DataFrame,
    columns: List[str],
    group_by: str,
    value_field: str,
) -> List[Dict[str, Any]]:
    if not group_by:
        raise HTTPException(status_code=422, detail="'group_by' is required for grouped aggregations")

    if group_by not in dataframe.columns:
        raise HTTPException(status_code=422, detail=f"Group by column not found in data source: {group_by}")

    numeric_df = dataframe[columns].apply(pd.to_numeric, errors="coerce").fillna(0)
    exception_counts = (numeric_df != 0).sum(axis=1)

    grouping_df = pd.DataFrame({group_by: dataframe[group_by], value_field: exception_counts})
    result_df = grouping_df.groupby(group_by, dropna=False, as_index=False)[value_field].sum()

    if pd.api.types.is_datetime64_any_dtype(result_df[group_by]):
        result_df[group_by] = result_df[group_by].dt.strftime("%Y-%m-%d")
    else:
        result_df[group_by] = result_df[group_by].astype(str)

    result_df[value_field] = result_df[value_field].astype(int)

    return result_df.to_dict(orient="records")


def process_data(raw_data: Any) -> Tuple[list[dict[str, Any]], str]:
    payload = _parse_raw_payload(raw_data)

    chart_payload = payload.get("chart")
    if not isinstance(chart_payload, dict):
        raise HTTPException(status_code=422, detail="Response is missing 'chart' metadata")

    plot_name = payload.get("plot_name") or chart_payload.get("title") or "Generated Plot"

    aggregation = chart_payload.get("aggregation") or "raw_records"
    columns = chart_payload.get("columns")
    value_field = chart_payload.get("value_field") or "count"
    group_by = chart_payload.get("group_by")

    dataframe = _load_dataset().copy()

    if aggregation == "raw_records":
        selected_columns = _validate_columns(columns, dataframe)
        if not selected_columns:
            selected_columns = list(dataframe.columns)
        processed_data = _aggregate_raw_records(dataframe, selected_columns)
    elif aggregation == "non_zero_count":
        selected_columns = _resolve_numeric_columns(columns, dataframe)
        processed_data = _aggregate_non_zero_count(dataframe, selected_columns, value_field)
    elif aggregation == "zero_count":
        selected_columns = _resolve_numeric_columns(columns, dataframe)
        processed_data = _aggregate_zero_count(dataframe, selected_columns, value_field)
    elif aggregation == "non_zero_count_by_group":
        selected_columns = _resolve_numeric_columns(columns, dataframe, exclude=[group_by] if group_by else None)
        processed_data = _aggregate_non_zero_count_by_group(dataframe, selected_columns, group_by, value_field)
    else:
        raise HTTPException(status_code=422, detail=f"Unsupported aggregation: {aggregation}")

    if not processed_data:
        raise HTTPException(status_code=422, detail="No data produced for the requested chart")

    return processed_data, plot_name
