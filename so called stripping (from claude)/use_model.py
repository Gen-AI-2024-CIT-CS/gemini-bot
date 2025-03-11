
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# For merged model
def load_merged_model():
    model = AutoModelForCausalLM.from_pretrained(
        "./merged_stripped_model",
        device_map="auto",
        torch_dtype=torch.float16
    )
    tokenizer = AutoTokenizer.from_pretrained("./merged_stripped_model")

    # Ensure padding token is set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return model, tokenizer

# For LoRA adapters only (if you couldn't merge)
def load_lora_model():
    from peft import PeftModel

    # Load base model - you'll need this installed
    base_model = AutoModelForCausalLM.from_pretrained(
        "defog/sqlcoder-7b-2",  # Replace with your base model
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
    return model, tokenizer

# Generate SQL query
def generate_sql(model, tokenizer, prompt, max_length=512):
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

# Example usage
if __name__ == "__main__":
    # Try loading merged model first, fall back to LoRA if needed
    try:
        model, tokenizer = load_merged_model()
        print("Loaded merged model")
    except:
        model, tokenizer = load_lora_model()
        print("Loaded base model with LoRA adapters")

    # Example prompt
    prompt = '''
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
Find all users who signed up in January 2024.

### SQL Query:
'''

    sql = generate_sql(model, tokenizer, prompt)
    print(sql)
