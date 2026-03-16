from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_NAME = "distilgpt2"

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.to("cpu")
model.eval()

if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

prompt = "Vector databases are"
print("Tokenizing...")
inputs = tokenizer(prompt, return_tensors="pt")

input_ids = inputs["input_ids"].to("cpu")
attention_mask = inputs["attention_mask"].to("cpu")

print("Running forward pass...")
with torch.no_grad():
    outputs = model(input_ids=input_ids, attention_mask=attention_mask)

print("Forward pass OK")
print("Logits shape:", outputs.logits.shape)

print("Running generate...")
with torch.no_grad():
    generated = model.generate(
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=10,
        do_sample=False,
        num_beams=1,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

print("Generate OK")
print(tokenizer.decode(generated[0], skip_special_tokens=True))
