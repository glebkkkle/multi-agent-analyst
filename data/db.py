import pandas as pd
import sqlite3
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Create connection (in-memory)
conn = sqlite3.connect('company_data.db')
cursor = conn.cursor()

# -----------------------------
# Create the sales table
# -----------------------------
cursor.execute('''
CREATE TABLE sales (
    date TEXT PRIMARY KEY,
    revenue REAL,
    units_sold INTEGER,
    profit REAL
)
''')

# Generate two weeks of continuous dates
start_date = datetime(2025, 4, 12)
dates = [start_date + timedelta(days=i) for i in range(14)]

# Randomized but realistic daily sales
sales_data = [
    (
        d.strftime('%Y-%m-%d'),
        np.random.uniform(5000, 15000),    # revenue
        np.random.randint(80, 200),        # units_sold
        np.random.uniform(1000, 4000)      # profit
    )
    for d in dates
]

cursor.executemany('INSERT INTO sales VALUES (?, ?, ?, ?)', sales_data)

# -----------------------------
# Create the campaign_analysis table
# -----------------------------
cursor.execute('''
CREATE TABLE campaign_analysis (
    date TEXT PRIMARY KEY,
    impressions INTEGER,
    clicks INTEGER,
    conversions INTEGER,
    ad_spend REAL
)
''')

# Random but consistent metrics aligned with same dates
campaign_data = [
    (
        d.strftime('%Y-%m-%d'),
        np.random.randint(10000, 50000),     # impressions
        np.random.randint(500, 2500),        # clicks
        np.random.randint(20, 200),          # conversions
        np.random.uniform(500, 2500)         # ad_spend
    )
    for d in dates
]

cursor.executemany('INSERT INTO campaign_analysis VALUES (?, ?, ?, ?, ?)', campaign_data)

cursor.execute('''
CREATE TABLE customer_feedback (
    date TEXT PRIMARY KEY,
    satisfaction_score REAL,
    support_tickets INTEGER,
    response_time REAL
)
''')

feedback_data = [
    (
        d.strftime('%Y-%m-%d'),
        np.random.uniform(3.0, 5.0),          # satisfaction_score (1–5 scale)
        np.random.randint(5, 50),             # support_tickets
        np.random.uniform(0.5, 3.0)           # avg response_time in hours
    )
    for d in dates
]

cursor.executemany('INSERT INTO customer_feedback VALUES (?, ?, ?, ?)', feedback_data)

# -----------------------------
# Create the inventory table
# -----------------------------
cursor.execute('''
CREATE TABLE inventory (
    date TEXT PRIMARY KEY,
    stock_level INTEGER,
    restock_units INTEGER,
    stockouts INTEGER
)
''')

inventory_data = [
    (
        d.strftime('%Y-%m-%d'),
        np.random.randint(500, 1000),          # stock_level
        np.random.randint(50, 200),            # restock_units
        np.random.randint(0, 5)                # stockouts (number of items out of stock)
    )
    for d in dates
]

cursor.executemany('INSERT INTO inventory VALUES (?, ?, ?, ?)', inventory_data)

# -----------------------------
# Create the website_traffic table
# -----------------------------
cursor.execute('''
CREATE TABLE website_traffic (
    date TEXT PRIMARY KEY,
    visitors INTEGER,
    bounce_rate REAL,
    avg_session_duration REAL,
    pages_per_session REAL
)
''')

traffic_data = [
    (
        d.strftime('%Y-%m-%d'),
        np.random.randint(2000, 10000),        # visitors
        np.random.uniform(30.0, 70.0),         # bounce_rate in %
        np.random.uniform(1.0, 4.0),           # avg_session_duration in minutes
        np.random.uniform(1.5, 5.0)            # pages_per_session
    )
    for d in dates
]

cursor.executemany('INSERT INTO website_traffic VALUES (?, ?, ?, ?, ?)', traffic_data)


conn.commit()