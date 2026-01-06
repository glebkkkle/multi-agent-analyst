# src/multi_agent_analyst/tools/analysis_tools.py
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import STL
from langchain_core.tools import StructuredTool
from src.multi_agent_analyst.schemas.analysis_agent_schema import (
    CorrelationSchema,
    AnomalySchema,
    SummarySchema,
    GroupBySchema,
    DifferenceSchema,
    FilterSchema, 
    SortSchema,
    DistributionSchema
)
from src.multi_agent_analyst.utils.utils import object_store
from scipy import stats

def sanitize_for_json(obj):
    import numpy as np
    import pandas as pd
    import math
    from datetime import datetime

    if isinstance(obj, pd.DataFrame):
        raise TypeError("sanitize_for_json must NOT be called on DataFrames")

    if obj is pd.NA:
        return None

    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return None if math.isnan(obj) or math.isinf(obj) else float(obj)

    if isinstance(obj, float):
        return None if math.isnan(obj) or math.isinf(obj) else obj

    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    if isinstance(obj, datetime):
        return obj.isoformat()

    if obj is None:
        return None

    return obj

def make_correlation_tool(df):
    def correlation():
        try:
            mat = df.corr(numeric_only=True)


            table_shape=mat.shape
        #format exception flag properly for the controller
        except Exception as e:
            return {
                'exception': str(e)
            }        
        obj_id=object_store.save(mat)
        
        payload={'object_id':obj_id, 
                'details':{'table_shape':table_shape},
                "operation_type":"Correlation"
                }

        return sanitize_for_json(payload)
    
    return StructuredTool.from_function(
        func=correlation,
        name="correlation_analysis",
        description="Compute correlation matrix for numeric columns.",
        args_schema=CorrelationSchema,
    )

def make_anomaly_tool(df):
    def anomaly():
        try:
            numeric = df.select_dtypes(include=["int", "float"])
            print('DETECTING')

            q1 = numeric.quantile(0.25)
            q3 = numeric.quantile(0.75)
            iqr = q3 - q1

            mask = (numeric < (q1 - 1.5 * iqr)) | (numeric > (q3 + 1.5 * iqr))

            lower = (q1 - 1.5 * iqr).to_dict()
            upper = (q3 + 1.5 * iqr).to_dict()

            iqr_bounds = {
                f"{col}_lower": round(lower[col], 2)
                for col in numeric.columns
            } | {
                f"{col}_upper": round(upper[col], 2)
                for col in numeric.columns
            }

            outlier_rows = numeric[mask.any(axis=1)]
            outlier_rows_display = outlier_rows.to_dict(orient="records")
            outlier_count = len(outlier_rows)

            annotated_df = df.copy()
            annotated_df["outlier"] = mask.any(axis=1)


            table_shape=annotated_df.shape

            obj_id = object_store.save(annotated_df)

            details = {
                "outlier_count": outlier_count,
                "outlier_rows": sanitize_for_json(outlier_rows_display) if len(outlier_rows_display) > 0 else 'No outliers detected',
                "columns_checked": list(numeric.columns),
                "iqr_bounds": ", ".join(f"{k}: {v}" for k, v in iqr_bounds.items()),
                'table_shape':table_shape
                }            

            result = {
                'object_id':obj_id,
                'details':details,
                "operation_type":"Anomaly detection"
                }
            
            print(result)

        except Exception as e:
            return {
                'exception': str(e)
            }
        
        return sanitize_for_json(result)

    return StructuredTool.from_function(
        func=anomaly,
        name="anomaly_detection",
        description="Detect outliers using IQR rule.",
        args_schema=AnomalySchema,
    )

def make_summary_tool(df):
    def summary():
        try:
            stats = df.describe(include="all")
        except Exception as e:
            return {
                'exception': str(e)
            }
        obj_id=object_store.save(stats)
        
        result={'object_id':obj_id, 
                'details':{'summary_table_shape':stats.shape}, 
                "operation_type":"Summary statistics"
                }
        
        return sanitize_for_json(result)

    return StructuredTool.from_function(
        func=summary,
        name="summary_statistics",
        description="Compute descriptive statistics.",
        args_schema=SummarySchema,
    )


def make_groupby_tool(df):
    def groupby_aggregate(group_column: str, agg_column: str, agg_function: str):
        try:
            if group_column not in df.columns:
                raise ValueError(f"Group column '{group_column}' does not exist in the dataframe.")

            # Validate aggregation column
            if agg_column not in df.columns:
                raise ValueError(f"Aggregation column '{agg_column}' does not exist in the dataframe.")

            # Validate aggregation function
            allowed = ["mean", "sum", "count", "min", "max"]
            if agg_function not in allowed:
                raise ValueError(
                    f"Aggregation function '{agg_function}' is not supported. "
                    f"Allowed: {allowed}"
                )

            # Perform grouping
            grouped = (
                df.groupby(group_column)[agg_column]
                .agg(agg_function)
                .reset_index()
            )

            table_shape=grouped.shape

            obj_id = object_store.save(grouped)

            # Build details
            details = {
                "group_column": group_column,
                "agg_column": agg_column,
                "agg_function": agg_function,
                "row_count": len(grouped),
                "table_shape":table_shape
            }

            result = {
                "object_id": obj_id,
                "details": details, 
                "operation_type":"Grouping"
            }

        except Exception as e:
            return {"exception": str(e)}

        return sanitize_for_json(result)

    return StructuredTool.from_function(
        func=groupby_aggregate,
        name="groupby_aggregate",
        description=(
            "Group the table by `group_column` and compute an aggregation on `agg_column` "
            "using one of the supported functions: mean, sum, count, min, max."
        ),
        args_schema=GroupBySchema,
    )

def make_difference_tool(df):
    print('CALLING DIFF TOOL')
    def difference_analysis(column: str, method: str = "absolute"):
        try:
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found in dataframe.")

            if method not in ["absolute", "percent"]:
                raise ValueError("method must be either 'absolute' or 'percent'.")

            if not pd.api.types.is_numeric_dtype(df[column]):
                raise ValueError(f"Column '{column}' must be numeric.")

            dfx = df.copy()

            if method == "absolute":
                dfx["difference"] = dfx[column].diff()
                dfx = dfx.replace({np.nan: None, np.inf: None, -np.inf: None})
            else:
                dfx["difference"] = dfx[column].pct_change() * 100.0
                dfx = dfx.replace({np.nan: None, np.inf: None, -np.inf: None})

            table_shape=dfx.shape
            obj_id = object_store.save(dfx)

            details = {
                "column": column,
                "method": method,
                "difference_stats": {
                    "max": float(dfx["difference"].max(skipna=True)),
                    "min": float(dfx["difference"].min(skipna=True)),
                    "mean": float(dfx["difference"].mean(skipna=True)),
                }, 
                "table_shape":table_shape
            }
            payload={
                "object_id": obj_id,
                "details": details, 
                "operation_type":"Difference Analysis"
            }

        except Exception as e:
            return {"exception": str(e)}

        return sanitize_for_json(payload)

    return StructuredTool.from_function(
        func=difference_analysis,
        name="difference_analysis",
        description=(
            "Calculate changes in a numeric column over the row index (time or order). "
            "Supports absolute differences or percent changes. Optionally sort by the difference."
        ),
        args_schema=DifferenceSchema,
    )

def make_filter_tool(df):
    def filter_rows(column: str, operator: str, value):
        try:
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found")

            series = df[column]

            if operator == "==":
                mask = series == value
            elif operator == "!=":
                mask = series != value
            elif operator == ">":
                mask = series > value
            elif operator == ">=":
                mask = series >= value
            elif operator == "<":
                mask = series < value
            elif operator == "<=":
                mask = series <= value
            elif operator == "in":
                if not isinstance(value, list):
                    raise ValueError("Value must be a list for 'in'")
                mask = series.isin(value)
            elif operator == "not_in":
                if not isinstance(value, list):
                    raise ValueError("Value must be a list for 'not_in'")
                mask = ~series.isin(value)
            else:
                raise ValueError(f"Unsupported operator '{operator}'")

            filtered = df[mask]

            obj_id = object_store.save(filtered)
            table_shape=filtered.shape
        except Exception as e:
            return {"exception":str(e)}
        
        payload={
                "object_id": obj_id,
                "details": {
                    "column": column,
                    "operator": operator,
                    "value": value,
                    "rows_after": len(filtered), 
                    "table_shape":table_shape
                }, 
                "operation_type":"Filtering"
            }

        return sanitize_for_json(payload)

    return StructuredTool.from_function(
        func=filter_rows,
        name="filter_rows",
        description="Filter rows based on a column condition.",
        args_schema=FilterSchema,
    )

def make_sort_tool(df):
    def sort_rows(column: str, order: str = "desc", limit: int = 10):
        try:
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found")

            if not pd.api.types.is_numeric_dtype(df[column]):
                raise ValueError(f"Column '{column}' must be numeric")

            ascending = order == "asc"

            sorted_df = (
                df.sort_values(column, ascending=ascending)
                  .head(limit)
            )


            obj_id = object_store.save(sorted_df)

            table_shape=sorted_df.shape
            payload={
                "object_id": obj_id,
                "details": {
                    "column": column,
                    "order": order,
                    "limit": limit, 
                    "table_shape":table_shape
                }, 
                "operation_type":"Sorting"
            }

        except Exception as e:
            return {"exception": str(e)}

        return sanitize_for_json(payload)
    return StructuredTool.from_function(
        func=sort_rows,
        name="sort_rows",
        description="Sort rows by a numeric column and return top results.",
        args_schema=SortSchema,
    )



def make_distribution_tool(df):
    def analyze_distribution(column: str):
        try:
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found")

            series = df[column].dropna()
            if not pd.api.types.is_numeric_dtype(series):
                raise ValueError(f"Column '{column}' must be numeric for distribution analysis")

            if len(series) < 3:
                raise ValueError("Not enough data points to determine distribution")

            # Basic Statistics
            mean_val = float(series.mean())
            median_val = float(series.median())
            std_val = float(series.std())
            
            # Shape Statistics
            skewness = float(stats.skew(series))
            kurtosis = float(stats.kurtosis(series))

            # Normality Testing (D'Agostino's K^2 test)
            # p < 0.05 usually means the data is NOT normally distributed
            stat, p_val = stats.normaltest(series)
            is_normal = p_val > 0.05

            # Identify Shape for the Summary
            if skewness > 1:
                shape = "highly right-skewed"
            elif skewness < -1:
                shape = "highly left-skewed"
            elif -0.5 < skewness < 0.5:
                shape = "approximately symmetric"
            else:
                shape = "moderately skewed"

            counts, bin_edges = np.histogram(series, bins='auto')
            dist_df = pd.DataFrame({
                "bin_start": bin_edges[:-1],
                "bin_end": bin_edges[1:],
                "count": counts
            })
            
            obj_id = object_store.save(dist_df)

            payload={
                "object_id": obj_id,
                "details": {
                    "column": column,
                    "mean": round(mean_val, 2),
                    "median": round(median_val, 2),
                    "std_dev": round(std_val, 2),
                    "skewness": round(skewness, 2),
                    "is_normal": bool(is_normal),
                    "normality_p_value": round(p_val, 4),
                    "distribution_shape": shape,
                    "table_shape": dist_df.shape
                }, 
                "operation_type":"Distribution Analysis"
            }

        except Exception as e:
            return {"exception": str(e)}

        return sanitize_for_json(payload)
    
    return StructuredTool.from_function(
        func=analyze_distribution,
        name="distribution_analysis",
        description="Calculate statistical distribution metrics (mean, skew, normality) for a numeric column.",
        args_schema=DistributionSchema,
    )


#might wanna add the previous exceptions/repairs along to the resolver agent, so he doesnt try the same fix twice but rethink its approach if failing, along with limits 

#making consistent format for tool outputs (always returning dataframe, but modified for example)
