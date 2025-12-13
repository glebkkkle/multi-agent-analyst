# src/multi_agent_analyst/tools/analysis_tools.py
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import STL
from langchain_core.tools import StructuredTool
from src.multi_agent_analyst.schemas.analysis_agent_schema import (
    CorrelationSchema,
    AnomalySchema,
    PeriodicSchema,
    SummarySchema,
    GroupBySchema,
    DifferenceSchema
)
from src.multi_agent_analyst.utils.utils import object_store

def make_correlation_tool(df):
    def correlation():
        try:
            result = df.corr(numeric_only=True)
            print(type(result))
        #format exception flag properly for the controller
        except Exception as e:
            return {
                'exception': e
            }        
        obj_id=object_store.save(result)
        
        return {'object_id':obj_id, 
                'details':'correlation matrix is executed'}

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

            obj_id = object_store.save(annotated_df)

            details = {
                "outlier_count": outlier_count,
                "outlier_rows": outlier_rows_display if len(outlier_rows_display) > 0 else 'No outliers detected',
                "columns_checked": list(numeric.columns),
                "iqr_bounds": ", ".join(f"{k}: {v}" for k, v in iqr_bounds.items())
                }            
            # object_id=object_store.save(details)

            result = {
                'object_id':obj_id,
                'details':details
                }
            
            print(result)

        except Exception as e:
            return {
                'exception': e
            }
        
        return result

    return StructuredTool.from_function(
        func=anomaly,
        name="anomaly_detection",
        description="Detect outliers using IQR rule.",
        args_schema=AnomalySchema,
    )

#perhaps make the resolver agent-specific helper 

def make_periodic_tool(df):
    def periodic(frequency: int):
        try:
            dfc = df.copy()
            dfc["date"] = pd.to_datetime(dfc["date"])
            dfc = dfc.sort_values("date")

            # Ensure exactly one numeric column is used
            numeric_cols = dfc.select_dtypes(include=["float", "int"]).columns

            if len(numeric_cols) == 0:
                raise ValueError("No numeric columns available for periodic analysis.")

            if len(numeric_cols) > 1:
                print(f"[WARNING] Multiple numeric columns found. Using: {numeric_cols[0]}")

            series = dfc[numeric_cols[0]].values.astype(float)  # 1D array
            series = series - np.mean(series)

            stl = STL(series, period=frequency, robust=True).fit()

            decomposition = {
                "trend": stl.trend.tolist(),
                "seasonal": stl.seasonal.tolist(),
                "residual": stl.resid.tolist(),
                "column_used": numeric_cols[0]
            }
            trend = stl.trend.tolist()
            seasonal = stl.seasonal.tolist()
            resid = stl.resid.tolist()
            
            details = {
                "trend_preview": trend[:10],
                "seasonal_preview": seasonal[:10],
                "residual_stats": {
                    "std": float(np.std(resid)),
                    "max": float(np.max(resid)),
                    "min": float(np.min(resid)),
                },
                "full_decomposition":{
                    "trend": trend,
                    "seasonal": seasonal,
                    "residual": resid,
                }}
            obj_id=object_store.save(details)

            result={'object_id': obj_id,
                    'details':details
                }

        except Exception as e:
            return {
                'exception': str(e)
            }

        return result

    return StructuredTool.from_function(
        func=periodic,
        name="periodic_analysis",
        description="Perform STL periodic decomposition on a single numeric time-series.",
        args_schema=PeriodicSchema,
    )

def make_summary_tool(df):
    def summary():
        try:
            stats = df.describe(include="all").to_dict()
        except Exception as e:
            return {
                'exception': e
            }
        obj_id=object_store.save(stats)
        
        result={'object_id':obj_id, 
                'details':stats}
        
        return result

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

            # Save result
            obj_id = object_store.save(grouped)

            # Build details
            details = {
                "group_column": group_column,
                "agg_column": agg_column,
                "agg_function": agg_function,
                "row_count": len(grouped)
            }

            result = {
                "object_id": obj_id,
                "details": details
            }
            print(result)
        except Exception as e:
            return {"exception": str(e)}

        return result

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

            obj_id = object_store.save(dfx)

            details = {
                "column": column,
                "method": method,
                "difference_stats": {
                    "max": float(dfx["difference"].max(skipna=True)),
                    "min": float(dfx["difference"].min(skipna=True)),
                    "mean": float(dfx["difference"].mean(skipna=True)),
                }
            }
            print(obj_id)
            print(details)
            return {
                "object_id": obj_id,
                "details": details
            }

        except Exception as e:
            return {"exception": str(e)}

    return StructuredTool.from_function(
        func=difference_analysis,
        name="difference_analysis",
        description=(
            "Calculate changes in a numeric column over the row index (time or order). "
            "Supports absolute differences or percent changes. Optionally sort by the difference."
        ),
        args_schema=DifferenceSchema,
    )

#might wanna add the previous exceptions/repairs along to the resolver agent, so he doesnt try the same fix twice but rethink its approach if failing, along with limits 

#making consistent format for tool outputs (always returning dataframe, but modified for example)
