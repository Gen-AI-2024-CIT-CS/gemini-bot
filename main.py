import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
import re

# Load environment variables (API key)
load_dotenv()

# Configure API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/visualize": {"origins": "*"}})  # Modify as needed for CORS

# Load the database data and schema
def load_database_files():
    try:
        with open("./data/database_dump.json", "r") as file:
            db_data = json.load(file)
        
        with open("./data/database_schema.json", "r") as file:
            db_schema = json.load(file)
            
        return db_data, db_schema
    except Exception as e:
        print(f"Error loading database files: {e}")
        return None, None

# Function to build the context for Gemini with limited data samples
def build_context(db_data, db_schema):
    context = "Database Schema:\n"
    
    # Add schema information
    for table_name, columns in db_schema.items():
        context += f"Table: {table_name}\n"
        context += "Columns:\n"
        for column_name, data_type in columns.items():
            context += f"  - {column_name} ({data_type})\n"
        context += "\n"
    
    # Add limited data samples
    context += "Sample Data:\n"
    for table_name, data in db_data.items():
        context += f"Table: {table_name}, Total Row Count: {len(data)}\n"
        
        # Add just 3 sample rows
        sample_data = data[:5] if len(data) > 5 else data
        for row in sample_data:
            context += f"  {row}\n"
        
        context += "\n"
    
    return context

# Function to detect query type
def detect_query_type(query):
    # Convert query to lowercase for easier matching
    query_lower = query.lower()
    
    # Check for yes/no questions
    if re.search(r'\b(is|are|does|do|has|have|can|will|should|would|could)\b', query_lower) and query_lower.endswith('?'):
        return "yes_no"
    
    # Check for data type questions
    if re.search(r'\b(what type|what kind|data type|type of data|what is the type)\b', query_lower):
        return "data_type"
    
    # Check for table visualization requests (assuming these typically include words like "show", "display", "visualize", "table")
    if re.search(r'\b(show|display|visualize|table|graph|chart|plot)\b', query_lower):
        return "table"
    
    # Default to general question
    return "general"

# Function to query Gemini with database context and get the appropriate representation
def query_database_with_gemini(query, db_data, db_schema):
    # Detect query type
    query_type = detect_query_type(query)
    
    # Build context with schema and limited data
    context = build_context(db_data, db_schema)
    
    if query_type == "table":
        # For table visualization requests
        prompt = f"""
        You are a database visualization assistant. Your task is to generate a **JSON table** representation of the data based on the user's query.
        
        Below is the database schema and sample data information:
        
        {context}
        
        User Query: {query}
        
        **Instructions:**
        - Analyze the query and generate a **JSON table** representation of the results.
        - Provide a brief **explanation** before the table data.
        
        **Response Format Example:**
        The output should be in the following format:
        
        "type": "table",
        "columns": ["column1", "column2", "column3"],  # List of column names
        "rows": [  # List of rows, where each row is an array of values
            ["value1", "value2", "value3"],
            ["value4", "value5", "value6"]
        ],
        "explanation": "brief explanation of the representation"
        """
    elif query_type == "yes_no":
        # For yes/no questions
        prompt = f"""
        You are a database question answering assistant. Your task is to answer a yes/no question based on the database data.
        
        Below is the database schema and sample data information:
        
        {context}
        
        User Query: {query}
        
        **Instructions:**
        - Analyze the query and determine if the answer is yes, no, or cannot be determined from the data.
        - Provide a brief explanation for your answer.
        
        **Response Format Example:**
        The output should be in the following format:
        
        "type": "yes_no",
        "answer": "yes", # or "no" or "undetermined"
        "explanation": "brief explanation of the answer"
        """
    elif query_type == "data_type":
        # For data type questions
        prompt = f"""
        You are a database schema assistant. Your task is to answer questions about data types in the database.
        
        Below is the database schema and sample data information:
        
        {context}
        
        User Query: {query}
        
        **Instructions:**
        - Analyze the query and provide information about the data types being asked about.
        - Reference the schema information to give accurate data type details.
        
        **Response Format Example:**
        The output should be in the following format:
        
        "type": "data_type",
        "information": "detailed information about the data types",
        "explanation": "brief explanation of the data types"
        """
    else:
        # For general questions
        prompt = f"""
        You are a database question answering assistant. Your task is to answer a general question about the database data.
        
        Below is the database schema and sample data information:
        
        {context}
        
        User Query: {query}
        
        **Instructions:**
        - Analyze the query and provide a thoughtful answer based on the database information.
        - If the question cannot be answered with the available data, explain why.
        
        **Response Format Example:**
        The output should be in the following format:
        
        "type": "general",
        "answer": "detailed answer to the question",
        "explanation": "brief explanation if needed"
        """
    
    # Generate content from Gemini
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content(prompt)
    
    # Extract the JSON part of the response
    response_text = response.text
    json_match = re.search(r'\{[\s\S]*\}', response_text)
        
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return {"error": "Failed to parse response", "raw": response_text}
    else:
        return {"error": "No JSON found in response", "raw": response_text}

# API route to process queries and return appropriate representation
@app.route('/visualize', methods=['POST'])
def visualize():
    data = request.get_json()
    query = data.get('query')
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400

    db_data, db_schema = load_database_files()
    if not db_data or not db_schema:
        return jsonify({'error': 'Failed to load database files'}), 500

    # Process query through Gemini
    response = query_database_with_gemini(query, db_data, db_schema)
    
    # Log response for debugging
    print("Gemini Raw Response:\n", response)

    # Return response based on type
    if "type" in response:
        if response["type"] == "table":
            return jsonify({
                "type": "table",
                "columns": response["columns"],
                "rows": response["rows"],
                "explanation": response["explanation"]
            })
        elif response["type"] == "yes_no":
            return jsonify({
                "type": "yes_no",
                "answer": response["answer"],
                "explanation": response["explanation"]
            })
        elif response["type"] == "data_type":
            return jsonify({
                "type": "data_type",
                "information": response["information"],
                "explanation": response["explanation"]
            })
        elif response["type"] == "general":
            return jsonify({
                "type": "general",
                "answer": response["answer"],
                "explanation": response["explanation"]
            })
        else:
            return jsonify({
                "error": "Invalid response type",
                "response": response
            })
    else:
        return jsonify({
            "error": "Response missing type field",
            "response": response
        })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)