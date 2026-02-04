# Prompting Guide

Best practices for prompting Sarvam-M effectively.

## System Prompts

### Persona Setting

```python
messages = [
    {
        "role": "system",
        "content": """You are Priya, a friendly customer service agent for an Indian e-commerce company.
- Always greet customers warmly
- Respond in the same language as the customer
- Be helpful and patient
- Escalate complex issues to human agents"""
    },
    {"role": "user", "content": "मेरा ऑर्डर कहाँ है?"}
]
```

### Domain Expert

```python
messages = [
    {
        "role": "system",
        "content": """You are an expert in Indian constitutional law.
- Cite relevant articles when applicable
- Explain complex legal concepts simply
- Distinguish between Supreme Court and High Court jurisdictions
- Note when professional legal advice should be sought"""
    },
    {"role": "user", "content": "What is Article 21?"}
]
```

### Language Control

```python
messages = [
    {
        "role": "system",
        "content": """Respond in Hindi using Devanagari script.
Include English transliteration in parentheses after each sentence.
Example: नमस्ते। (Namaste.)"""
    },
    {"role": "user", "content": "How do I introduce myself?"}
]
```

## Hybrid Thinking

### When to Use

Enable `thinking=True` for:
- Math problems
- Logic puzzles
- Multi-step reasoning
- Analysis tasks

### Example

```python
response = client.chat.completions.create(
    model="sarvam-m",
    messages=[
        {
            "role": "user",
            "content": """A shopkeeper sells an item at 20% profit. 
If the cost price is ₹500, what is the selling price?"""
        }
    ],
    thinking=True
)

# The model will show its reasoning:
# Thinking: "Cost price = ₹500, Profit = 20%, 
#           Profit amount = 500 × 0.20 = ₹100,
#           Selling price = 500 + 100 = ₹600"
# Answer: "The selling price is ₹600."
```

## Few-Shot Prompting

Provide examples for consistent formatting:

```python
messages = [
    {
        "role": "system",
        "content": "You translate English sentences to Hindi."
    },
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "नमस्ते"},
    {"role": "user", "content": "Thank you"},
    {"role": "assistant", "content": "धन्यवाद"},
    {"role": "user", "content": "Good morning"}
]
```

## Chain of Thought

For complex reasoning without thinking mode:

```python
messages = [
    {
        "role": "user",
        "content": """Solve step by step:
        
A train leaves Delhi at 8:00 AM traveling at 60 km/h.
Another train leaves from the same station at 9:00 AM traveling at 80 km/h in the same direction.
At what time will the second train catch up with the first?

Think through this step by step."""
    }
]
```

## Structured Output

Request specific formats:

### JSON Output

```python
messages = [
    {
        "role": "system",
        "content": """Extract information and return as JSON.
Format: {"name": "...", "age": ..., "city": "..."}"""
    },
    {
        "role": "user",
        "content": "Rahul is 25 years old and lives in Mumbai."
    }
]
```

### Table Output

```python
messages = [
    {
        "role": "user",
        "content": """List the top 5 populated cities in India.
Format as a markdown table with columns: Rank, City, State, Population"""
    }
]
```

## Temperature Guidelines

| Use Case | Temperature | Reason |
|----------|-------------|--------|
| Factual Q&A | 0.1-0.3 | Consistent, accurate |
| Translation | 0.2-0.4 | Balanced accuracy |
| Conversation | 0.5-0.7 | Natural flow |
| Creative writing | 0.8-1.0 | More variety |
| Brainstorming | 1.0-1.5 | Maximum creativity |

## Common Patterns

### Q&A Bot

```python
system_prompt = """You are a Q&A assistant.
- Answer questions directly and concisely
- Say "I don't know" if uncertain
- Cite sources when possible
- Ask for clarification if the question is ambiguous"""
```

### Summarizer

```python
system_prompt = """You summarize text.
- Keep summaries under 100 words
- Preserve key facts and figures
- Maintain neutral tone
- Highlight the most important points first"""
```

### Code Assistant

```python
system_prompt = """You are a Python coding assistant.
- Write clean, readable code
- Include comments explaining logic
- Handle edge cases
- Follow PEP 8 style guidelines"""
```

## Error Handling

Handle common issues:

```python
try:
    response = client.chat.completions.create(
        model="sarvam-m",
        messages=messages,
        timeout=30
    )
except Exception as e:
    # Retry with simpler prompt or fallback
    pass
```

