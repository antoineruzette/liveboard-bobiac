# backend/app.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pandas as pd
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow access from any origin (adjust if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for leaderboard
submissions = []

class Submission(BaseModel):
    name: str
    host: str
    results: dict

@app.post("/update")
async def update(sub: Submission):
    sub_entry = {
        "Name": sub.name,
        "Host": sub.host,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    sub_entry.update(sub.results)
    submissions.append(sub_entry)
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def show_leaderboard():
    if not submissions:
        return "<h2>No submissions yet!</h2>"

    df = pd.DataFrame(submissions)
    df = df.sort_values("Instance F1 Score", ascending=False)

    html = """
    <html>
    <head>
        <title>Live Segmentation Leaderboard</title>
        <meta http-equiv="refresh" content="15">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            h1 {{ color: #333; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>🧠 Live Segmentation Leaderboard</h1>
        <p>Last updated: {}</p>
        {}
    </body>
    </html>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), df.to_html(index=False))

    return HTMLResponse(content=html)
