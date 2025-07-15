# backend/app.py

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pandas as pd
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    df = df.sort_values("Instance F1 Score", ascending=False).reset_index(drop=True)

    podium = ""
    for i in range(min(3, len(df))):
        podium += f"<div class='podium rank{i+1}'>🥇🥈🥉"[i] + f" {df.iloc[i]['Name']} – {df.iloc[i]['Instance F1 Score']}" + "</div>"

    html = f"""
    <html>
    <head>
        <title>Live Segmentation Leaderboard</title>
        <meta http-equiv="refresh" content="15">
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #fafafa; }}
            h1 {{ color: #333; }}
            .podium {{ font-size: 1.5em; font-weight: bold; padding: 10px; margin-bottom: 10px; }}
            .rank1 {{ color: gold; }}
            .rank2 {{ color: silver; }}
            .rank3 {{ color: #cd7f32; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 30px; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
            th {{ background-color: #f2f2f2; cursor: pointer; }}
            tr:hover {{ background-color: #f1f1f1; }}
        </style>
        <script>
            function sortTable(n) {{
                var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                table = document.getElementById("leaderboard");
                switching = true;
                dir = "desc";
                while (switching) {{
                    switching = false;
                    rows = table.rows;
                    for (i = 1; i < (rows.length - 1); i++) {{
                        shouldSwitch = false;
                        x = rows[i].getElementsByTagName("TD")[n];
                        y = rows[i + 1].getElementsByTagName("TD")[n];
                        if (dir == "asc") {{
                            if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {{
                                shouldSwitch = true;
                                break;
                            }}
                        }} else if (dir == "desc") {{
                            if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {{
                                shouldSwitch = true;
                                break;
                            }}
                        }}
                    }}
                    if (shouldSwitch) {{
                        rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                        switching = true;
                        switchcount++;
                    }} else {{
                        if (switchcount == 0 && dir == "desc") {{
                            dir = "asc";
                            switching = true;
                        }}
                    }}
                }}
            }}
        </script>
    </head>
    <body>
        <h1>🧠 Live Segmentation Leaderboard</h1>
        {podium}
        <p>Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        {df.to_html(index=False, table_id="leaderboard", escape=False)}
        <script>
            var headers = document.querySelectorAll("#leaderboard th");
            headers.forEach((th, i) => th.addEventListener("click", () => sortTable(i)));
        </script>
    </body>
    </html>
    """

    return HTMLResponse(content=html)
