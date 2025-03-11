import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Load base model with low memory settings
base_model = AutoModelForCausalLM.from_pretrained(
    "defog/sqlcoder-7b-2",  
    device_map="auto",
    load_in_4bit=True,
    torch_dtype=torch.float16
)
tokenizer = AutoTokenizer.from_pretrained("defog/sqlcoder-7b-2")

# Ensure padding token is set
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

# Load LoRA adapters
model = PeftModel.from_pretrained(base_model, "./lora_adapters")

# Generate SQL query
def generate_sql(prompt, max_length=512):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            inputs.input_ids,
            max_length=max_length,
            num_beams=1,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id
        )
    
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Test with your specific database schema
prompt = """
### Instructions:
Convert the following natural language query into a SQL query.

### Database Schema:
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL
);

### Query:
Find all users who signed up in February 2024.

### SQL Query:
"""

sql = generate_sql(prompt)
print(sql)