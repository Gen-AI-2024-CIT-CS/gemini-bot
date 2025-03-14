import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Path to your downloaded and unzipped LoRA adapters
lora_path = "./lora_adapters"  # Update this path to where you extracted the zip file

# Load the base model
base_model_name = "defog/sqlcoder-7b-2"
tokenizer = AutoTokenizer.from_pretrained(base_model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Load the base model with the LoRA adapters
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    device_map="auto",
    load_in_4bit=True,
    torch_dtype=torch.float16
)
model = PeftModel.from_pretrained(base_model, lora_path)
print("Model loaded successfully")

# Function to generate SQL from natural language
def generate_sql(query):
    # Your schema is already embedded in the training, so we don't need to pass it again
    prompt = f"""
### Instructions:
Convert the following natural language query into a SQL query.
### Query:
{query}
### SQL Query:
"""
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_length=256,
        temperature=0.1,
        top_p=0.95,
        do_sample=True
    )
    
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Example usage
query = "filter students based on the department"
sql_result = generate_sql(query)
print(f"Natural language: {query}")
print(f"SQL query: {sql_result}")