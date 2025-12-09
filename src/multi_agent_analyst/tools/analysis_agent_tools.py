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
)
from src.multi_agent_analyst.utils.utils import object_store

#no improvisations, strict execution of the plan 

def make_correlation_tool(df):
    def correlation():
        try:
            result = df.corr(numeric_only=True)
            saved_id = object_store.save(result)

            # Metadata for controller
            strongest = None
            if result.size > 1:
                abs_vals = result.abs()
                upper = abs_vals.where(np.triu(np.ones(abs_vals.shape), k=1).astype(bool))
                strongest_pair = upper.unstack().idxmax()
                strongest_val = upper.max().max()
                strongest = {
                    "col_pair": strongest_pair,
                    "correlation": float(strongest_val)
                }

            return {
                "object_id": saved_id,
                "observation": {
                    "agent": "AnalysisAgent",
                    "tools_used": ["correlation_analysis"],
                    "summary": f"Computed correlation matrix for {result.shape[0]} numeric columns.",
                    "details": {
                        "shape": result.shape,
                        "strongest_correlation": strongest,
                        "columns": list(result.columns)
                    },
                    "relevance_to_query": "Correlation helps identify relationships between numeric variables."
                },
                "exception": None
            }

        except Exception as e:
            return {
                "object_id": None,
                "observation": {
                    "agent": "AnalysisAgent",
                    "tools_used": ["correlation_analysis"],
                    "summary": "Correlation computation failed.",
                    "details": {},
                    "relevance_to_query": ""
                },
                "exception": str(e)
            }

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

            q1 = numeric.quantile(0.25)
            q3 = numeric.quantile(0.75)
            iqr = q3 - q1

            mask = (numeric < (q1 - 1.5 * iqr)) | (numeric > (q3 + 1.5 * iqr))
            outlier_rows = numeric[mask.any(axis=1)]
            outlier_count = len(outlier_rows)

            iqr_bounds = {
                f"{col}_lower": float(q1[col] - 1.5 * iqr[col])
                for col in numeric.columns
            } | {
                f"{col}_upper": float(q3[col] + 1.5 * iqr[col])
                for col in numeric.columns
            }

            result = {
                "outlier_count": outlier_count,
                "columns_checked": list(numeric.columns),
                "iqr_bounds": iqr_bounds,
                "outlier_rows_preview": outlier_rows.head(5).to_dict(orient="records")
            }

            saved_id = object_store.save(result)

            return {
                "object_id": saved_id,
                "observation": {
                    "agent": "AnalysisAgent",
                    "tools_used": ["anomaly_detection"],
                    "summary": f"Detected {outlier_count} outliers using IQR.",
                    "details": {
                        "outlier_count": outlier_count,
                        "columns_checked": list(numeric.columns),
                        "iqr_bounds": iqr_bounds
                    },
                    "relevance_to_query": "Outlier detection highlights abnormal points that may skew analysis."
                },
                "exception": None
            }

        except Exception as e:
            return {
                "object_id": None,
                "observation": {
                    "agent": "AnalysisAgent",
                    "tools_used": ["anomaly_detection"],
                    "summary": "Anomaly detection failed.",
                    "details": {},
                    "relevance_to_query": ""
                },
                "exception": str(e)
            }

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

            numeric_cols = dfc.select_dtypes(include=["float", "int"]).columns
            if len(numeric_cols) == 0:
                raise ValueError("No numeric columns available for periodic analysis.")

            col = numeric_cols[0]
            series = dfc[col].astype(float).values
            series = series - np.mean(series)

            stl = STL(series, period=frequency, robust=True).fit()

            trend = stl.trend.tolist()
            seasonal = stl.seasonal.tolist()
            resid = stl.resid.tolist()

            result = {
                "column_used": col,
                "trend_preview": trend[:10],
                "seasonal_preview": seasonal[:10],
                "residual_stats": {
                    "std": float(np.std(resid)),
                    "max": float(np.max(resid)),
                    "min": float(np.min(resid)),
                }
            }

            saved_id = object_store.save(result)

            return {
                "object_id": saved_id,
                "observation": {
                    "agent": "AnalysisAgent",
                    "tools_used": ["periodic_analysis"],
                    "summary": f"Performed STL decomposition on '{col}' with frequency={frequency}.",
                    "details": result,
                    "relevance_to_query": "Seasonal decomposition identifies repeating patterns and trend direction."
                },
                "exception": None
            }

        except Exception as e:
            return {
                "object_id": None,
                "observation": {
                    "agent": "AnalysisAgent",
                    "tools_used": ["periodic_analysis"],
                    "summary": "Periodic analysis failed.",
                    "details": {},
                    "relevance_to_query": ""
                },
                "exception": str(e)
            }

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
            saved_id = object_store.save(stats)

            return {
                "object_id": saved_id,
                "observation": {
                    "agent": "AnalysisAgent",
                    "tools_used": ["summary_statistics"],
                    "summary": "Computed descriptive statistics.",
                    "details": {
                        "columns": list(stats.keys()),
                        "stats_preview": {k: list(v.values())[:3] for k, v in stats.items()}
                    },
                    "relevance_to_query": "Basic statistics provide a global understanding of distribution and scale."
                },
                "exception": None
            }

        except Exception as e:
            return {
                "object_id": None,
                "observation": {
                    "agent": "AnalysisAgent",
                    "tools_used": ["summary_statistics"],
                    "summary": "Summary statistics failed.",
                    "details": {},
                    "relevance_to_query": ""
                },
                "exception": str(e)
            }

    return StructuredTool.from_function(
        func=summary,
        name="summary_statistics",
        description="Compute descriptive statistics.",
        args_schema=SummarySchema,
    )


#might need more complexity (tool, planning wise) to answer and reason through complex questions that user might have

#probably wouldnt be hard to fully get rid of the planner if its non viable and better approach is needed

#agents should reason independently, only on their piece of the puzzle. They should return the observations that they have made to the controller, and the controller to make the desicion based on the observations returned by the agents.

#with each agent working on their problem and returning their independent observations, the controller has to reason of what to do next. If its confident that the query has been answered - return, if not - think and act about the problem futher
