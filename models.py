import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load model and tokenizer (forces CPU usage)
model_name = "microsoft/phi-2"
device = torch.device("cpu")

model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Define schema for generating SQL queries
schema = """{
    "users": { "id": "integer", "name": "character varying", "email": "character varying", "password": "text", "role": "character varying" },
    "student": { "name": "character varying", "email": "character varying", "roll_no": "character varying", "gender": "character varying", "dept": "character varying", "year": "integer" },
    "course": { "course_name": "character varying", "course_id": "character varying" },
    "students_enrolled": { "course_name": "character varying", "course_id": "character varying", "email": "character varying" },
    "courses_enrolled": { "course_id": "character varying", "course_name": "character varying", "email": "character varying", "status": "character varying" },
    "assignments": { "courseid": "character varying", "name": "character varying", "email": "character varying", "roll_no": "character varying", "assignment0": "numeric", "created_at": "timestamp without time zone" },
    "mentee": { "name": "character varying", "email": "character varying", "roll_no": "character varying", "mentor_name": "character varying" }
}"""

def generate_sql(question):
    """Generate an accurate SQL query for a given question."""
    prompt = f"Schema: {schema}\nGenerate an accurate SQL query for: {question}\nSQL:"
    
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    output = model.generate(**inputs, max_new_tokens=100)

    sql_query = tokenizer.decode(output[0], skip_special_tokens=True)
    return sql_query

if __name__ == "__main__":
    while True:
        question = input("\nEnter your question (or type 'exit' to quit): ")
        if question.lower() == "exit":
            break
        print("\nGenerated SQL Query:\n", generate_sql(question))
