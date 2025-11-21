import pandas as pd
import sqlite3

conn = sqlite3.connect('company_data.db', check_same_thread=False)


def load_sample_tables():
    website_traffic_samples = pd.read_sql_query('SELECT * FROM website_traffic', conn).head()
    sales_samples = pd.read_sql_query('SELECT * FROM sales', conn).head()
    customer_feedback_samples = pd.read_sql_query('SELECT * FROM customer_feedback', conn).head()
    inventory_samples = pd.read_sql_query('SELECT * FROM inventory', conn).head()
    campaign_analysis_samples = pd.read_sql_query('SELECT * FROM campaign_analysis', conn).head()

    return {
        'website_traffic': {
            'description':'SQL table with information about website traffic',
            'columns': website_traffic_samples
        },
        'sales': {
            'description':'SQL table with information about sales',
            'columns': sales_samples
        },
        'customer_feedback': {
            'description':'SQL table with information about customer feedback',
            'columns': customer_feedback_samples
        },
        'inventory': {
            'description':'SQL table with information about inventory',
            'columns': inventory_samples
        },
        'campaign_analysis': {
            'description':'SQL table with information about campaign analysis',
            'columns': campaign_analysis_samples
        }
    }