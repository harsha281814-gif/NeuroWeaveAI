from flask import Flask, request, jsonify
import sqlite3
import requests
import datetime
import platform
from together import Together

app = Flask(__name__)

# ================== TOGETHER AI ==================
client = Together()

# ================== MEMORY ==================
conn = sqlite3.connect("memory.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    ai TEXT
)
""")
conn.commit()

def save_memory(user, ai):
    cursor.execute("INSERT INTO memory (user, ai) VALUES (?, ?)", (user, ai))
    conn.commit()

def get_memory():
    cursor.execute("SELECT user, ai FROM memory ORDER BY id DESC LIMIT 5")
    return cursor.fetchall()

# ================== MODE ==================
mode = "normal"

# ================== AI (SAFE VERSION) ==================
def ask_ai(prompt):
    try:
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        return "AI Error: " + str(e)

# ================== INTERNET ==================
def search_web(query):
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        data = requests.get(url).json()

        if data.get("AbstractText"):
            return data["AbstractText"]
        return "No result found."
    except:
        return "Search error"

# ================== ACTIONS ==================
def perform_action(text):
    text = text.lower()

    if "time" in text:
        return "Time: " + datetime.datetime.now().strftime("%H:%M")

    elif "date" in text:
        return "Date: " + str(datetime.date.today())

    elif "system info" in text:
        return platform.system() + " " + platform.release()

    return None

# ================== API ==================
@app.route("/ask", methods=["POST"])
def ask():
    user_input = request.json["message"]

    if "search" in user_input.lower():
        response = search_web(user_input)
    else:
        action = perform_action(user_input)

        if action:
            response = action
        else:
            response = ask_ai(user_input)

    save_memory(user_input, response)

    return jsonify({"response": response})

# ================== UI ==================
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
<title>NeuroWeave AI</title>

<style>
body {
    background: #0d0d0d;
    color: white;
    font-family: Arial;
}

#chat {
    height: 400px;
    overflow-y: auto;
    background: #1a1a1a;
    padding: 10px;
    border-radius: 10px;
}

.user { color: #00ffcc; }
.ai { color: #00ff00; }

input {
    width: 75%;
    padding: 10px;
    border-radius: 5px;
    border: none;
}

button {
    padding: 10px;
    background: #00ffcc;
    border: none;
    border-radius: 5px;
}
</style>
</head>

<body>

<h2>🧠 NeuroWeave AI v3 🚀</h2>

<div id="chat"></div>

<br>

<input id="msg" placeholder="Type your message..." />
<button onclick="sendMessage()">Send</button>

<script>
async function sendMessage() {
    let msg = document.getElementById("msg").value;

    document.getElementById("chat").innerHTML += 
        "<p class='user'>You: " + msg + "</p>";

    let res = await fetch("/ask", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: msg})
    });

    let data = await res.json();

    document.getElementById("chat").innerHTML += 
        "<p class='ai'>AI: " + data.response + "</p>";

    document.getElementById("chat").scrollTop =
        document.getElementById("chat").scrollHeight;
}
</script>

</body>
</html>
"""

# ================== RUN ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
