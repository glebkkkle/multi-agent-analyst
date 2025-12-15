CHAT_INTENT_PROMPT="""
    You are an intent classifier for an AI system that supports both:
    1) normal conversational chat
    2) analytical queries requiring planning, tool use, or multi-step reasoning.

    Your task:
    Given ONLY the latest user message, determine whether the user wants:
    - **"plan"** → when the message requires analytics, data processing, SQL operations,
                plots, visualizations, segmentation, forecasting,
                or any task that requires agents or tools.
    - **"chat"** → when the user is talking casually, asking general questions,
    making comments, or anything not requiring tools.

    IMPORTANT RULES:
    - DO NOT classify "clarification". Clarification is NOT your responsibility.
    The critic/revision system will explicitly request clarification separately.
    - You NEVER decide if the system is missing information.
    - You NEVER route to clarification.
    - Your ONLY outputs are "chat" or "plan".

    Classification logic:
    - If the message references data, columns, tables, trends, correlations,
    filtering, merging, visualizing, forecasting → label **"plan"**.
    - If the message describes an action (“segment X”, “visualize Y”, “retrieve Z”) → **"plan"**.
    - If the user is discussing feelings, thinking aloud, joking, or chatting → **"chat"**.
    - Ambiguous messages default to **"chat"**.

    Respond ONLY with JSON:
        intent: Literal["plan", "chat"]
        reason: str
    
    Latest user message:
    {user_query}
"""

#let the intent classifier node check if the query from user is complete. Provide neccessary args definitions for it to evalutate whether we have enough info from the user.

#line-plot (target column)
#correlation-analysis (dataset/df)
#scatter plot (x column, y column)
#pie chart (dataset/df/columns)
#anomaly_detection (dataset/df/columns)
#table_visualization (dataset/df/columns)


#fitting the dataset schemas as well perhaps. So the classifier could check whether we have what the user intents.

#could be done. Nothing to worry about for the DataAgent. Need to only check if there is enough data for the analysis/visualization.

INTENT_CLASSIFIER_PROMPT = """
You are the Intent Classifier and Feasibility Guardrail for a Multi Agent System.

Your Task:
1. Analyze the `User Message`.
2. Determine if the request is "chat" (casual) or "plan" (analytical).
3. If "plan", determine if the request is **Executable** based on the data and tool logic.
---

### 1. AVAILABLE DATA SCHEMAS
(These are the tables and columns the user actually possesses)
{data_schemas}

### 2. TOOL LOGIC
Use these rules to judge if a "plan" is executable (`is_sufficient: true`):

* **General Visualization (Bar, Line, Pie):** * Needs: Requires 1 recognizable column from the schemas.
    * *Logic:* If the user says "Plot sales", 'sales' is a table or column, this is SUFFICIENT.
* **Scatter Plot:** * Needs: 2 distinct numeric columns (X and Y)!. 
    * *Logic:* "Scatter plot of profit" is INSUFFICIENT (missing 2nd variable). "Scatter plot of profit vs revenue" is SUFFICIENT (if both columns exist).
* **Correlation:** * Needs: A dataset name OR at least 2 specific columns from provided schemas
* **Anomaly detection ** * Needs : a dataset name OR at least one column from the provided schemas

### 3. CLASSIFICATION RULES

**Target: "chat"**
* Greetings, emotional statements, general questions unrelated to the data.
* Example: "Hello", "That's cool", "Write a poem about stocks."

**Target: "plan"**
* Any request to view, analyze, plot, calculate, or retrieve data.

### 4. SUFFICIENCY CHECK (The "Feasibility" Flag)
If intent is "plan", check `is_sufficient`:
* **TRUE:** The user mentioned specific columns/tables present in the Schema, AND the tool requirements (from section 2) are met.
    * *Note:* Fuzzy matching is allowed (e.g., User says "finance plan" matches table finance, or fuzzy column names).
* **FALSE:** (set intent==clarification)
1. The mentioned data does not exist in the schema.
    2. The tool logic is violated (e.g., Scatter plot requested with only 1 column).

---

If intent is chatting, set is_sufficient True and do not specify any missing info.

### OUTPUT FORMAT (JSON ONLY). Output nothing else!
Respond with valid JSON.
    "intent": "plan" | "chat"| 'clarification' ,
    "is_sufficient": boolean (only for plan or clarification)
    "missing_info": string | null, // If false, briefly state what is missing (e.g., "Missing 2nd variable for scatter plot" or "Column 'happiness' not found")

### USER MESSAGE:
{user_query}
"""

# schemas="""
# {'бізнес план_фін': {'description': "User table 'бізнес план_фін'", 'columns': {'january': 'text'}, 'row_count': 11}, 'sales': {'description': "User table 'sales'", 'columns': {'date': 'text', 'revenue': 'double precision', 'units_sold': 'integer', 'profit': 'double precision'}, 'row_count': 28}, 'customer_feedback': {'description': "User table 'customer_feedback'", 'columns': {'date': 'text', 'stock_level': 'integer', 'restock_units': 'integer', 'stockouts': 'integer'}, 'row_count': 14}, 'radial_data': {'description': "User table 'radial_data'", 'columns': {'col_06310127810182615': 'double precision', 'col_06084932788567511': 'double precision', 'col_1': 'integer'}, 'row_count': 399}}
# """

# from langchain_openai import ChatOpenAI
# from pydantic import BaseModel 
# from typing import List

# openai_llm = ChatOpenAI(model="gpt-5-mini")
# class Output(BaseModel):
#     intent:str
#     is_sufficient:bool
#     missing_info:str

# user_query='correlation '

# sl=openai_llm.with_structured_output(Output).invoke(INTENT_CLASSIFIER_PROMPT.format(data_schemas=schemas, user_query=user_query))

# print(sl)

# print(sl.is_sufficient)
# print(type(sl.is_sufficient))

#or maybe let the intent classifier check if enough data is provided along with the types and so on. While the critic is focused on correcting the created plan 