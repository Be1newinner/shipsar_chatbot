import torch
from transformers import pipeline
from datetime import datetime
from db import chat_history_collection

pipe = pipeline(
    "text-generation",
    model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

def clean_response(response_text):
    """Removes unwanted system, user, and assistant tags from the response."""
    response_text = response_text.split("<|assistant|>")[-1]
    return response_text 

def chatter(user_id: str, session_id: str, msg: str):
    """Generate a chatbot response with context from previous messages."""

    # Fetch last 10 messages
    past_chats = list(chat_history_collection.find(
        {"session_id": session_id}).sort("timestamp", -1).limit(10)
    )

    messages = [{"role": "system", "content": "You are a friendly chatbot."}]
    
    # Add past messages to maintain context
    for chat in reversed(past_chats):
        messages.append({"role": "user", "content": chat["message"]})
        messages.append({"role": "assistant", "content": chat["response"]})

    # Append the new user message
    messages.append({"role": "user", "content": msg})

    # Generate prompt for model
    prompt = pipe.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

    # Generate response
    outputs = pipe(prompt, max_new_tokens=150, do_sample=True, temperature=0.7, top_k=50, top_p=0.95)
    raw_response = outputs[0]["generated_text"]
    
    # Clean the response
    cleaned_response = clean_response(raw_response)

    # Save to database
    chat_data = {
        "session_id": session_id,
        "user_id": user_id,
        "message": msg,
        "response": cleaned_response,
        "timestamp": datetime.utcnow()
    }
    chat_history_collection.insert_one(chat_data)

    return {"assistant": cleaned_response}
