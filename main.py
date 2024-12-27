from fastapi import FastAPI
import httpx

app = FastAPI()

@app.get("/openai/{text}")
async def openai_proxy(text: str):
    api_url = "https://api.openai.com/v1/engines/davinci/completions"
    headers = {"Authorization": "Bearer YOUR_OPENAI_API_KEY"}
    params = {"prompt": text, "max_tokens": 2048}
    response = await httpx.post(api_url, headers=headers, json=params)
    return response.json()
