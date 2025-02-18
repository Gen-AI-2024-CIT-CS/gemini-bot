import psycopg2
import json
import os

# Database connection details
DB_NAME = "mydummydb"
DB_USER = "postgres"
DB_PASSWORD = "hemanth!21"
DB_HOST = "localhost"  # Change if using a remote server
DB_PORT = "5432"  # Default PostgreSQL port

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

    schema_data = {}

    # Loop through each table and fetch its schema information
    for table in tables:
        cursor.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}' AND table_schema = 'public';
        """)
        columns = cursor.fetchall()

        # Store table schema (columns and their data types)
        table_schema = {column[0]: column[1] for column in columns}
        schema_data[table] = table_schema

    # Create the data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)

    # Save the entire database data as JSON in the data directory
    output_file = os.path.join(data_dir, "database_schema.json")
    with open(output_file, "w") as json_file:
        json.dump(schema_data, json_file, indent=4)

    print(f"✅ Database exported successfully to '{output_file}'")

except Exception as e:
    print("❌ Error:", e)

finally:
    # Close connection
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
