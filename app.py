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
        return """
        <html>
        <head>
            <title>Live Segmentation Leaderboard</title>
            <meta http-equiv="refresh" content="15">
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-50">
            <div class="min-h-screen flex items-center justify-center">
                <h2 class="text-3xl font-bold text-gray-800">No submissions yet!</h2>
            </div>
        </body>
        </html>
        """

    df = pd.DataFrame(submissions)
    df = df.sort_values("Instance F1 Score", ascending=False)
    
    # Get top 3 for podium
    podium = df.head(3) if len(df) >= 3 else df
    # Rest of the leaderboard
    rest_of_board = df.iloc[3:] if len(df) > 3 else pd.DataFrame()

    html = """
    <html>
    <head>
        <title>Live Segmentation Leaderboard</title>
        <meta http-equiv="refresh" content="15">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen p-8">
        <div class="max-w-7xl mx-auto">
            <h1 class="text-4xl font-bold text-center text-gray-800 mb-2">🧠 Live Segmentation Leaderboard</h1>
            <p class="text-center text-gray-600 mb-12">Last updated: {}</p>
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

    # Add full leaderboard table
    if not rest_of_board.empty:
        html += """
            <div class="bg-white rounded-lg shadow-lg overflow-hidden">
                <table class="min-w-full">
                    <thead>
                        <tr class="bg-gray-800 text-white">
        """
        
        # Add headers
        for col in rest_of_board.columns:
            html += f"""
                            <th class="px-6 py-4 text-left">{col}</th>
            """
            
        html += """
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add rows
        for idx, row in rest_of_board.iterrows():
            html += """
                        <tr class="border-b border-gray-200 hover:bg-gray-50">
            """
            for col in rest_of_board.columns:
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
        """

    html += """
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
