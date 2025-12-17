
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



# we check in the intent classfier (this is actually where we have the dataset schemas and row count).
# We check - if the desired by user dataset contains less then 200 rows - then we dont care, and allow future execution
# if however, the dataset contains more than 200 rows and the user hasnt specified - we reprompt asking for specification 
# same goes for unbigues specifications like "retrive full dataset".
#  We are not allowing that for the moment, so just clarify from the user and then implement some safety meassures outside the prompts later 
# like in sql queries or smth