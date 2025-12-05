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
        #format exception flag properly for the controller
        except Exception as e:
            return {
                'exception': e
            }
        return object_store.save(result)

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
            # if column:
            #     numeric = numeric[[column]]
            print(numeric)
            q1 = numeric.quantile(0.25)
            q3 = numeric.quantile(0.75)
            iqr = q3 - q1

            mask = (numeric < (q1 - 1.5 * iqr)) | (numeric > (q3 + 1.5 * iqr))
            print(mask)
            outliers = numeric[mask]
            print(outliers)
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
            result = {
                "outlier_count": outlier_count,
                "outlier_rows": outlier_rows_display if len(outlier_rows_display) > 0 else 'No outliers detected',
                "columns_checked": list(numeric.columns),
                "iqr_bounds": ", ".join(f"{k}: {v}" for k, v in iqr_bounds.items())
                },
        
        except Exception as e:
            print(e)
            return {

                'exception': e
            }
        return object_store.save(result)

    return StructuredTool.from_function(
        func=anomaly,
        name="anomaly_detection",
        description="Detect outliers using IQR rule.",
        args_schema=AnomalySchema,
    )

#perhaps make the resolver agent-specific helper 


def make_periodic_tool(df):
    print('PERFORMING PERIODIC ANALYSIS')

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
            
            result = {
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
            
        except Exception as e:
            return {
                'exception': str(e)
            }

        return object_store.save(result)

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
        return object_store.save(stats)

    return StructuredTool.from_function(
        func=summary,
        name="summary_statistics",
        description="Compute descriptive statistics.",
        args_schema=SummarySchema,
    )
