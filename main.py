# IMPORTS

import json
import os
import socket
import urllib.request

# DEFINE
SOCKET_PATH = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "malcom.sock")

# Condition if already exists removes
if os.path.exists(SOCKET_PATH):
    os.remove(SOCKET_PATH)

# Define and bind socket object to path
server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(SOCKET_PATH)
server.listen()


# Translate massage into json llm request
####################################################################################################
def handle_request(user_prompt):

    # Create python text payload
    payload = {
        "model": "llama3.2:3b",
        "messages": [
            {
                "role": "system",
                "content": 'You are a Linux system assistant. Output ONLY JSON: {"action": "mode_work" | "backup_dotfiles" | "unknown"}. Do not explain.',
            },
            {"role": "user", "content": user_prompt},
        ],
        "format": "json",
        "stream": False,
    }

    # Create json message by importing payload
    json_message = json.dumps(payload).encode("utf-8")
    # Create request
    llm_request = urllib.request.Request(
        "http://localhost:11434/api/chat",
        json_message,
        {"Content-Type": "application/json"},
    )
    return llm_request


# Sends request and handles response
####################################################################################################
def handle_response(llm_request):
    with urllib.request.urlopen(llm_request) as response:
        raw_response = response.read().decode("utf-8")
        response_data = json.loads(raw_response)
    return response_data


# Main loop
####################################################################################################
while True:
    conn, adress = server.accept()

    raw_data = conn.recv(1024)
    # Condition if no data was sent (blank request)
    if not raw_data:
        conn.close()
        continue
    # Decode raw bytes into utf-8 and strip of \n
    massage = raw_data.decode("utf-8").strip()

    # print(f"Request: {massage}")
    request = handle_request(massage)
    respond = handle_response(request)
    print(respond)

    conn.close()
