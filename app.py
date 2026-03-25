from flask import Flask, request, jsonify
import sqlite3
import os
import requests
import datetime
import platform
from together import Together

app = Flask(__name__)

# ================== TOGETHER AI ==================
client = Together()  # uses TOGETHER_API_KEY

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
    cursor.execute("SELECT user, ai FROM memory ORDER BY id DESC LIMIT 10")
    return cursor.fetchall()

# ================== MODE ==================
mode = "normal"

# ================== AI ==================
def ask_ai(prompt):
    global mode

    memory = get_memory()
    messages = []

    # Personality
    if mode == "study":
        system_msg = "You are a strict study assistant. Give short, clear answers."
    else:
        system_msg = "You are NeuroWeave AI, a smart, friendly futuristic assistant."

    messages.append({"role": "system", "content": system_msg})

    # Memory context
    for u, a in memory:
        messages.append({"role": "user", "content": u})
        messages.append({"role": "assistant", "content": a})

    # Current input
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=messages
    )

    return response.choices[0].message.content

# ================== INTERNET ==================
def search_web(query):
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    data = requests.get(url).json()

    if data.get("AbstractText"):
        return data["AbstractText"]
    elif data.get("RelatedTopics"):
        return str(data["RelatedTopics"][:2])

    return "No result found."

# ================== ACTIONS ==================
def perform_action(text):
    global mode
    text = text.lower()

    # APPS
    if "open chrome" in text:
        os.system("start chrome")
        return "Opening Chrome"

    elif "open notepad" in text:
        os.system("start notepad")
        return "Opening Notepad"

    elif "open youtube" in text:
        os.system("start https://www.youtube.com")
        return "Opening YouTube"

    elif "open google" in text:
        os.system("start https://www.google.com")
        return "Opening Google"

    # SYSTEM
    elif "shutdown" in text:
        os.system("shutdown /s /t 5")
        return "Shutting down system"

    elif "system info" in text:
        return platform.system() + " " + platform.release()

    # TIME / DATE
    elif "time" in text:
        return "Time: " + datetime.datetime.now().strftime("%H:%M")

    elif "date" in text:
        return "Date: " + str(datetime.date.today())

    # FILE
    elif "create file" in text:
        with open("new_file.txt", "w") as f:
            f.write("Created by NeuroWeave AI")
        return "File created"

    # MODES
    elif "study mode" in text:
        mode = "study"
        return "Study mode activated"

    elif "normal mode" in text:
        mode = "normal"
        return "Normal mode activated"

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

<h2>🧠 NeuroWeave AI (FREE CLOUD)</h2>

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
