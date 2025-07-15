# backend/app.py

from fastapi import FastAPI, Request, StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import pandas as pd
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

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

    df = pd.DataFrame(submissions)
    df = df.sort_values("Instance F1 Score", ascending=False)
    
    # Get top 3 for podium
    podium = df.head(3) if len(df) >= 3 else df

    html = """
    <html>
    <head>
        <title>Segmentation Leaderboard</title>
        <meta http-equiv="refresh" content="15">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen p-8">
        <div class="max-w-7xl mx-auto">
            <div class="flex flex-col items-center mb-12">
                <img src="/static/bobiac_logos_svgexport-03.svg" alt="BoBIAC Logo" class="w-64 mb-4">
                <h1 class="text-4xl font-bold text-center text-gray-800">Segmentation Leaderboard</h1>
                <p class="text-center text-gray-600 mt-4">Last updated: {}</p>
            </div>
    """

    # Add podium section if we have submissions
    if not podium.empty:
        html += """
            <div class="flex justify-center items-end space-x-4 mb-16 h-[400px]">
        """
        
        # Second place (if exists)
        if len(podium) > 1:
            html += f"""
                <div class="w-64 flex flex-col items-center">
                    <div class="bg-gradient-to-br from-gray-200 to-gray-300 rounded-t-lg w-full h-[250px] flex flex-col items-center justify-center p-4 transform hover:scale-105 transition-transform duration-200">
                        <div class="text-6xl mb-4">🥈</div>
                        <div class="text-xl font-bold text-gray-800 text-center mb-2">{podium.iloc[1]['Name']}</div>
                        <div class="text-gray-700">F1: {podium.iloc[1]['Instance F1 Score']:.3f}</div>
                    </div>
                </div>
            """
        
        # First place
        html += f"""
                <div class="w-64 flex flex-col items-center">
                    <div class="bg-gradient-to-br from-yellow-100 to-yellow-200 rounded-t-lg w-full h-[300px] flex flex-col items-center justify-center p-4 transform hover:scale-105 transition-transform duration-200 shadow-lg">
                        <div class="text-7xl mb-4">🥇</div>
                        <div class="text-2xl font-bold text-gray-800 text-center mb-2">{podium.iloc[0]['Name']}</div>
                        <div class="text-gray-700 text-lg">F1: {podium.iloc[0]['Instance F1 Score']:.3f}</div>
                    </div>
                </div>
        """
        
        # Third place (if exists)
        if len(podium) > 2:
            html += f"""
                <div class="w-64 flex flex-col items-center">
                    <div class="bg-gradient-to-br from-orange-100 to-orange-200 rounded-t-lg w-full h-[200px] flex flex-col items-center justify-center p-4 transform hover:scale-105 transition-transform duration-200">
                        <div class="text-5xl mb-4">🥉</div>
                        <div class="text-lg font-bold text-gray-800 text-center mb-2">{podium.iloc[2]['Name']}</div>
                        <div class="text-gray-700">F1: {podium.iloc[2]['Instance F1 Score']:.3f}</div>
                    </div>
                </div>
            """
        
        html += """
            </div>
        """

    # Add complete submissions table with all entries
    html += """
        <div class="bg-white rounded-lg shadow-lg overflow-hidden mb-8">
            <h2 class="text-2xl font-bold text-gray-800 p-6 border-b border-gray-200">Complete Submission Log</h2>
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead>
                        <tr class="bg-gray-800 text-white">
    """
    
    # Add headers
    for col in df.columns:
        html += f"""
                            <th class="px-6 py-4 text-left">{col}</th>
        """
        
    html += """
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Add all rows
    for idx, row in df.iterrows():
        # Highlight top 3 with different background colors
        bg_color = ""
        if idx == 0:
            bg_color = "bg-yellow-50"
        elif idx == 1:
            bg_color = "bg-gray-50"
        elif idx == 2:
            bg_color = "bg-orange-50"
            
        html += f"""
                        <tr class="border-b border-gray-200 hover:bg-gray-50 {bg_color}">
        """
        for col in df.columns:
            value = row[col]
            if col == "Instance F1 Score":
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
        </div>
    """

    html += """
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
