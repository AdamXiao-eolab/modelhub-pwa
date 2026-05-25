# ModelHub API

One API, 200+ Models. Affordable AI for everyone.

ModelHub provides unified access to 200+ AI models including DeepSeek V4, Claude 4, GPT-5, Gemini 2.5 Pro, and more through a single OpenAI-compatible API. No Chinese phone number required. Pay with credit card.

## Quick Start

```python
from openai import OpenAI
client = OpenAI(base_url="https://modelhub-api.com/v1", api_key="your-key")
response = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":"Hello!"}])
print(response.choices[0].message.content)
```

## Pricing

DeepSeek V4: $0.50/M tokens input - Save 95% vs OpenAI
Full pricing at modelhub-api.com/pricing

## Referral

Earn $50 per referral - no cap. modelhub-api.com/referral
