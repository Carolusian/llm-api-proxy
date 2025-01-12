import os
import uvicorn
import httpx  # <--- Added this line
import collections
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse


load_dotenv()

app = FastAPI()
client = httpx.AsyncClient(proxy=os.environ.get("HTTP_PROXY", ""))

gemini_api_key = os.environ.get("GEMINI_API_KEY", "")

providers = {
    "groq": "https://api.groq.com/",
    "cerebras": "https://api.cerebras.ai/",
    "gemini": "https://generativelanguage.googleapis.com/",
}

@app.post("/{path:path}")
async def reverse_proxy(request: Request, path: str):
    for p, base_url in providers.items():
        if path.startswith(f"{p}/"):
            url = base_url + path[len(p) + 1:]
            target_url = httpx.URL(url, query=request.url.query.encode("utf-8"))
            if p == "gemini" and gemini_api_key:
                params = target_url.params.merge({"key": gemini_api_key})
                target_url = target_url.copy_merge_params(params=params)
            break
    else:
        sub_path = path.split("/")[0]
        url = "https://api.openai.com/" + path[len(sub_path) + 1 :]
        target_url = httpx.URL(url, query=request.url.query.encode("utf-8"))

    print(f"target_url: {target_url}")

    new_headers = collections.defaultdict(str)
    if auth := request.headers.get("authorization"):
        new_headers = {"Authorization": auth}
    body = await request.json() if request.method in ["POST"] else None
    stream = body.get("stream", False) or "streamGenerateContent" in path
    req = client.build_request(
        request.method, target_url, headers=new_headers, content=await request.body()
    )

    if stream:
        response = await client.send(req, stream=True)
        return StreamingResponse(
            response.aiter_bytes(),
            status_code=response.status_code,
            headers=response.headers,
        )
    response = await client.send(req)
    return response.json()


@app.get("/{path:path}")
async def reverse_proxy_get(request: Request, path: str):
    return await reverse_proxy(request, path)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
