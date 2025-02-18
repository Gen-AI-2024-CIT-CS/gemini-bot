import psycopg2
import json
from decimal import Decimal
from datetime import datetime
import os

# Database connection details
DB_NAME = "mydummydb"
DB_USER = "postgres"
DB_PASSWORD = "hemanth!21"
DB_HOST = "localhost"  # Change if using a remote server
DB_PORT = "5432"  # Default PostgreSQL port

# Function to convert Decimal to float for JSON serialization
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError("Type not serializable")

# Function to convert datetime to string for JSON serialization
def datetime_default(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # Convert to ISO format string
    raise TypeError("Type not serializable")

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()

    # Fetch all table names from the public schema
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = [table[0] for table in cursor.fetchall()]

    db_data = {}

    # Loop through each table and fetch its data
    for table in tables:
        cursor.execute(f"SELECT * FROM {table};")
        columns = [desc[0] for desc in cursor.description]  # Get column names
        rows = cursor.fetchall()

        # Convert rows into dictionary format
        table_data = []
        for row in rows:
            row_data = dict(zip(columns, row))
            # Convert Decimal and datetime values to serializable formats
            row_data = {key: (decimal_default(value) if isinstance(value, Decimal) else
                              datetime_default(value) if isinstance(value, datetime) else value)
                        for key, value in row_data.items()}
            table_data.append(row_data)

        db_data[table] = table_data

    # Create the data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)

    # Save the entire database data as JSON in the data directory
    output_file = os.path.join(data_dir, "database_dump.json")
    with open(output_file, "w") as json_file:
        json.dump(db_data, json_file, indent=4)

    print(f"✅ Database exported successfully to '{output_file}'")

except Exception as e:
    print("❌ Error:", e)

finally:
    # Close connection
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
