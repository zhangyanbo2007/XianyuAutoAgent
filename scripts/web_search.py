import anthropic

client = anthropic.Anthropic(
    api_key="tp-c1kaznnjsvndkjgih8no34aj4530rk5u9ay61pma0eh3qjhb",
    base_url="https://token-plan-cn.xiaomimimo.com/anthropic"
)

message = client.messages.create(
    model="mimo-v2.5-pro",
    max_tokens=1024,
    tools=[
        {
            "type": "web_search_20250305",
            "user_location": {
                "type": "approximate",
                "country": "CN",
                "region": "Hubei",
                "city": "Wuhan"
            }
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "武汉明天天气怎么样？"
        }
    ]
)

print(message.content)
