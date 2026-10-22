# hypr-daemon

> Lightweight Linux background automation daemon providing an IPC bridge between local LLMs (via Ollama) and desktop management workflows on Hyprland.

---

## 1. Overview & Context

`hypr-daemon` is an experimental proof-of-concept created to explore local, privacy-first artificial intelligence integration into Linux desktop workflows. Instead of relying on cloud APIs or heavy Python web frameworks, this daemon runs locally on Fedora/Hyprland and exposes a native POSIX socket interface to process natural language desktop commands via a local instance of Ollama.

Key technologies utilized:
- **Language & Runtime:** Python 3 (pure standard library)
- **IPC Mechanism:** POSIX UNIX Domain Sockets (`AF_UNIX`)
- **Local LLM Backend:** Ollama API (`llama3.2:3b` model)
- **Data Exchange:** HTTP / REST JSON streaming

---

## 2. Architecture & Design

- **Core Components:**
  - `AF_UNIX` Socket Server: Binds to `$XDG_RUNTIME_DIR/malcom.sock` (or `/tmp`) to accept local client connections.
  - LLM Request Adapter: Translates raw text queries into constrained JSON payloads targeting the Ollama `/api/chat` endpoint.
  - JSON Intent Classifier: Enforces a strict system prompt instructing the model to output a deterministic JSON enum action.
- **IPC / Protocols / Data Flow:**
  - Local clients connect over standard UNIX domain stream sockets.
  - The daemon issues an HTTP POST request to Ollama running on `localhost:11434`.
  - Ollama evaluates the query using `llama3.2:3b` in JSON mode and returns a structured action payload.
- **Constraints / Design Decisions:**
  - **Zero External Dependencies:** Built solely on Python's standard library (`socket`, `urllib.request`, `json`, `os`) to avoid bloated virtual environments for background system daemons.
  - **Offline & Private:** Zero external internet network calls; all inference occurs strictly on local hardware.

```
[CLI / Keybind Client]
          │ (Raw text via UNIX Socket)
          ▼
[hypr-daemon (AF_UNIX Server)]
          │ (HTTP POST JSON payload)
          ▼
[Local Ollama Service (:11434)]  ──►  Intent Classification (llama3.2:3b)
          │ (Structured JSON response)
          ▼
[hypr-daemon]  ──►  Action Dispatcher (Hyprland / Scripts)
```

---

## 3. Directory Structure

```text
.
├── .gitignore          # Git exclusion rules
├── LICENSE             # License terms
├── main.py             # Daemon entry point, socket loop, and Ollama integration
└── README.md           # Documentation
```

---

## 4. Technical Deep-Dive / Key Features

### UNIX Domain Socket Server
- **Path:** `main.py`
- **Domain & Tech:** Systems programming, POSIX IPC, `socket.AF_UNIX`
- **Implementation Details:** Binds a stream socket to `$XDG_RUNTIME_DIR/malcom.sock` (with a `/tmp` fallback). Handles pre-startup cleanup by removing stale socket nodes and listens for inbound client connections in an iterative loop.

### Constrained Intent Classification via Ollama
- **Path:** `main.py`
- **Domain & Tech:** LLM integration, JSON schema enforcement, `urllib.request`
- **Implementation Details:** Constructs an HTTP POST request targeting `http://localhost:11434/api/chat`. Utilizes Ollama's `format: "json"` configuration along with a targeted system prompt:
  ```json
  {"action": "mode_work" | "backup_dotfiles" | "unknown"}
  ```
  This eliminates conversational filler and forces the LLM to output a machine-parseable decision in milliseconds.

---

## 5. Prerequisites & Environment

- **OS / Platform:** Linux (Fedora, Ubuntu, or Arch running Hyprland or any desktop environment)
- **Compilers / Runtimes:** Python 3.10+
- **System Dependencies / Daemons:** Ollama service running locally with model pulled:
  ```bash
  systemctl start ollama
  ollama pull llama3.2:3b
  ```

---

## 6. Build & Installation

```bash
# Clone the repository
git clone git@github.com:xLumar00/hypr-daemon.git
cd hypr-daemon

# Ensure local Ollama model is available
ollama pull llama3.2:3b
```

---

## 7. Usage & Examples

```bash
# Start the background daemon
python3 main.py

# Send natural language requests from any terminal client (using netcat or socat)
echo "Set up my coding workspace" | nc -U "${XDG_RUNTIME_DIR:-/tmp}/malcom.sock"

# Trigger backup workflow
echo "Backup all my dotfiles" | nc -U "${XDG_RUNTIME_DIR:-/tmp}/malcom.sock"
```

---

## 8. Engineering Post-Mortem & Known Issues

- **Missing Bi-Directional Socket Communication:** The server reads incoming client requests and logs parsed inference data to its stdout, but closes the client connection without writing a response payload back over the socket (`conn.sendall()`).
- **Unhandled Network & Parse Exceptions:** If the Ollama daemon is stopped or unreachable, `urllib.request.urlopen` raises an uncaught `urllib.error.URLError`, terminating the daemon process.
- **Single-Threaded Blocking I/O Loop:** The main loop executes synchronously. If an LLM inference call stalls or takes multiple seconds, incoming client connections on the socket backlog are blocked.
- **Missing Signal Cleanup:** The socket file is removed upon startup, but no `SIGINT` or `SIGTERM` signal handlers exist to cleanly unlink the socket node upon shutdown.

---

## 9. Roadmap & Future Improvements

- [ ] Implement socket response write-back to inform clients of execution results.
- [ ] Connect classified actions directly to system execution via Python's `subprocess` module (`mode_work.sh`, `backup_dotfiles.sh`).
- [ ] Refactor the blocking synchronous accept loop to non-blocking asynchronous I/O using `asyncio` or `selectors`.
- [ ] Implement signal handlers (`signal.signal`) for graceful cleanup of socket nodes on termination.

---

## 10. Notes / Attribution

- **Author:** Marek Lupták (`xLumar00`)
- **License:** MIT License (see `LICENSE`)
