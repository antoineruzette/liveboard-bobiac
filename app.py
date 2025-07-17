# backend/app.py

from fastapi import FastAPI, Request
from starlette.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
import pandas as pd
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict

app = FastAPI()

# Mount the current directory as static files to serve the logo
app.mount("/static", StaticFiles(directory="."), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store submissions by task
submissions = defaultdict(list)

class Submission(BaseModel):
    name: str
    task: str
    host: str
    results: dict

@app.post("/update")
async def update(sub: Submission):
    sub_entry = {
        "Name": sub.name,
        "Task": sub.task,
        "Host": sub.host,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    sub_entry.update(sub.results)
    submissions[sub.task].append(sub_entry)
    return {"status": "ok"}

@app.post("/reset/{task}")
async def reset_task(task: str):
    if task in submissions:
        submissions[task].clear()
    return RedirectResponse(url="/", status_code=303)

@app.post("/reset")
async def reset_all():
    submissions.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def show_leaderboard():
    if not submissions:
        return """
        <html>
        <head>
            <title>Segmentation Leaderboard</title>
            <meta http-equiv="refresh" content="15">
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-50">
            <div class="min-h-screen flex flex-col items-center justify-center">
                <img src="/static/bobiac_logos_svgexport-03.svg" alt="BoBIAC Logo" class="w-64 mb-8">
                <h2 class="text-3xl font-bold text-gray-800">No submissions yet!</h2>
            </div>
        </body>
        </html>
        """

    html = """
    <html>
    <head>
        <title>BoBIAC Leaderboard</title>
        <meta http-equiv="refresh" content="15">
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            .podium-container {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 2rem;
                padding: 2rem;
            }}
            .podium-wrapper {{
                flex: 1;
                min-width: 300px;
                max-width: 600px;
            }}
        </style>
    </head>
    <body class="bg-gray-50 min-h-screen p-8">
        <div class="max-w-7xl mx-auto">
            <div class="flex flex-col items-center mb-12">
                <img src="/static/bobiac_logos_svgexport-03.svg" alt="BoBIAC Logo" class="w-64 mb-4">
                <h1 class="text-4xl font-bold text-center text-gray-800">BoBIAC Leaderboard</h1>
                <p class="text-center text-gray-600 mt-4">Last updated: {timestamp}</p>
            </div>
    """

    # Create podium layout
    html += '<div class="podium-container">'
    
    # Sort tasks to ensure consistent layout
    sorted_tasks = sorted(submissions.keys())
    
    for task in sorted_tasks:
        task_submissions = submissions[task]
        if not task_submissions:
            continue
            
        # Create DataFrame and get best score for each team
        df = pd.DataFrame(task_submissions)
        df = df.sort_values("Mean AP", ascending=False)
        
        # Get best score for each team
        best_per_team = df.loc[df.groupby('Name')['Mean AP'].idxmax()]
        best_per_team = best_per_team.sort_values("Mean AP", ascending=False)
        
        # Get top 3 unique teams for podium
        podium = best_per_team.head(3) if len(best_per_team) >= 3 else best_per_team

        html += f"""
            <div class="podium-wrapper bg-white rounded-lg shadow-lg p-6 mb-8">
                <div class="flex justify-between items-center mb-6">
                    <h2 class="text-2xl font-bold text-gray-800">{task}</h2>
                    <form action="/reset/{task}" method="post" class="inline" onsubmit="return confirm('Are you sure you want to reset the {task} leaderboard?');">
                        <button type="submit" class="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-200 text-sm">
                            Reset {task}
                        </button>
                    </form>
                </div>
        """

        if not podium.empty:
            html += """
                <div class="flex justify-center items-end space-x-4 mb-8 h-[300px]">
            """
            
            # Second place (if exists)
            if len(podium) > 1:
                html += f"""
                    <div class="w-1/3 flex flex-col items-center">
                        <div class="bg-gradient-to-br from-gray-200 to-gray-300 rounded-t-lg w-full h-[200px] flex flex-col items-center justify-center p-4 transform hover:scale-105 transition-transform duration-200">
                            <div class="text-4xl mb-4">🥈</div>
                            <div class="text-lg font-bold text-gray-800 text-center mb-2">{podium.iloc[1]['Name']}</div>
                            <div class="text-gray-700">Mean AP: {podium.iloc[1]['Mean AP']:.3f}</div>
                        </div>
                    </div>
                """
            
            # First place
            html += f"""
                    <div class="w-1/3 flex flex-col items-center">
                        <div class="bg-gradient-to-br from-yellow-100 to-yellow-200 rounded-t-lg w-full h-[250px] flex flex-col items-center justify-center p-4 transform hover:scale-105 transition-transform duration-200 shadow-lg">
                            <div class="text-5xl mb-4">🥇</div>
                            <div class="text-xl font-bold text-gray-800 text-center mb-2">{podium.iloc[0]['Name']}</div>
                            <div class="text-gray-700 text-lg">Mean AP: {podium.iloc[0]['Mean AP']:.3f}</div>
                        </div>
                    </div>
            """
            
            # Third place (if exists)
            if len(podium) > 2:
                html += f"""
                    <div class="w-1/3 flex flex-col items-center">
                        <div class="bg-gradient-to-br from-orange-100 to-orange-200 rounded-t-lg w-full h-[150px] flex flex-col items-center justify-center p-4 transform hover:scale-105 transition-transform duration-200">
                            <div class="text-3xl mb-4">🥉</div>
                            <div class="text-base font-bold text-gray-800 text-center mb-2">{podium.iloc[2]['Name']}</div>
                            <div class="text-gray-700">Mean AP: {podium.iloc[2]['Mean AP']:.3f}</div>
                        </div>
                    </div>
                """
            
            html += """
                </div>
            """
            
        html += "</div>"  # Close podium-wrapper

    html += "</div>"  # Close podium-container

    # Add complete submissions table with all entries
    html += """
        <div class="bg-white rounded-lg shadow-lg overflow-hidden mb-8">
            <div class="flex justify-between items-center p-6 border-b border-gray-200">
                <h2 class="text-2xl font-bold text-gray-800">Complete Submission Log</h2>
                <form action="/reset" method="post" class="inline" onsubmit="return confirm('Are you sure you want to reset ALL leaderboards? This will delete all submissions.');">
                    <button type="submit" class="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded-lg transition-colors duration-200 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
                        </svg>
                        Reset All
                    </button>
                </form>
            </div>
    """

    # Combine all submissions for the log table
    all_submissions = []
    for task_submissions in submissions.values():
        all_submissions.extend(task_submissions)
    
    if all_submissions:
        df_all = pd.DataFrame(all_submissions)
        df_all = df_all.sort_values("Timestamp", ascending=False)

        html += """
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead>
                        <tr class="bg-gray-800 text-white">
        """
        
        # Add headers
        for col in df_all.columns:
            html += f"""
                                <th class="px-6 py-4 text-left">{col}</th>
            """
            
        html += """
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add all rows
        for idx, row in df_all.iterrows():
            html += """
                            <tr class="border-b border-gray-200 hover:bg-gray-50">
            """
            for col in df_all.columns:
                value = row[col]
                if col == "Mean AP":
                    value = f"{value:.3f}"
                html += f"""
                                <td class="px-6 py-4">{value}</td>
                """
            html += """
                            </tr>
            """
            
        html += """
                    </tbody>
                </table>
            </div>
        """

    html += """
        </div>
    </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html.format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
