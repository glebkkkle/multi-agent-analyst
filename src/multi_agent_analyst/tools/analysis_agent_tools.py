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
        except Exception as e:
            print(e)
            return {

                'exception': e
            }
        return object_store.save(mask)

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

            series = dfc.select_dtypes(include=["float", "int"]).values
            series -= np.mean(series)

            stl = STL(series, period=frequency, robust=True).fit()

            decomposition = {
                "trend": stl.trend.tolist(),
                "seasonal": stl.seasonal.tolist(),
                "residual": stl.resid.tolist(),
            }

        except Exception as e:
            return {
                'exception': e
            }

        return object_store.save(decomposition)

    return StructuredTool.from_function(
        func=periodic,
        name="periodic_analysis",
        description="Perform STL periodic decomposition.",
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
