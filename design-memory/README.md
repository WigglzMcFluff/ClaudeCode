# Design Memory

Long-term, searchable memory for Claude Code across Fusion 360 and Blender design sessions.
Lessons proven in one session (print results, measurements, fixes that worked) are saved as
Markdown notes and can be found by meaning in any later session.

Built from the *Build a Local Design Memory for Claude Code* tutorial, adapted for this PC.

```
READ:   Claude -> MCP server -> Python -> pgvector database -> matching notes -> Claude
LEARN:  design session -> /capture-design-learning -> Markdown note -> seed.py -> database
```

**The Markdown notes are the real copy. The database is just an index you can rebuild at any time.**

---

## Where everything lives

| What | Where |
|---|---|
| Project code | `C:\Users\ronbu\OneDrive\Documents\ClaudeCode\design-memory\` |
| Fusion notes | `design-memory\knowledge\fusion360\` (captured lessons go in `captured\`) |
| Blender notes | `design-memory\knowledge\blender\` (captured lessons go in `captured\`) |
| Python environment | `C:\Users\ronbu\.venvs\design-memory\` (outside OneDrive on purpose, ~1 GB) |
| Embedding model cache | `C:\Users\ronbu\.cache\huggingface\` (~90 MB) |
| Database | Docker container `design-memory-postgres`, databases `fusion360_rag` and `blender_rag` |
| Claude MCP config | `ClaudeCode\.mcp.json` **and** `design-memory\.mcp.json` (identical) |
| Capture Skill | `ClaudeCode\.claude\skills\capture-design-learning\SKILL.md` (one copy, works in both folders) |

---

## Daily use

**Requirement:** Docker Desktop must be running (whale icon in the system tray). The database restarts
automatically with Docker.

Start Claude Code sessions in the **desktop app, Code tab, local folder** `ClaudeCode` (or
`design-memory`). The web version at claude.ai/code cannot reach this PC.

### 1. Before or during a design task

Claude can search on its own, but asking explicitly is more reliable:

> Before changing this support geometry, search the Fusion design memory for relevant prior print
> failures, measurements, or constraints.

Use "Fusion design memory" or "Blender design memory" so it searches the right store.

### 2. When a session proves something

Finish the real work first. Once the result is backed by a print, a measurement, an explicit
requirement, or a procedure that actually worked, run:

```
/capture-design-learning fusion360 "short focus"
/capture-design-learning blender "short focus"
```

- Store name first (`fusion360` or `blender`), then an optional focus in quotes.
- Approve the file write and the `seed.py` command when asked.
- **Skim the note it reports.** Claude sometimes adds its own explanation as if it were proven. If
  something reads too strong, edit the `.md` file and re-sync (see below).

### 3. In a later session

Ask a related question in any wording. The earlier conversation is gone, but the lesson is found by
meaning.

---

## What makes a good note

**Good:**
- specific to your projects, printers, or materials
- a real physical result (fit, sag, warp, snap, tolerance)
- a measurement or constraint you don't want to rediscover
- why a lasting design decision was made
- a failure **and** the change that actually fixed it
- a Fusion or Blender procedure you've proven works

**Bad:**
- Claude's guesses or explanations that were never tested
- whole chat transcripts
- abandoned in-between measurements
- generic tutorials you could just search for again
- CAD files (`.f3d`, `.blend`, `.stl`); the model only understands text
- Fusion and Blender knowledge mixed in one store

---

## Adding your own notes

Any UTF-8 `.md` or `.txt` file anywhere under `knowledge\fusion360\` or `knowledge\blender\` gets
indexed. Organise subfolders however you like, for example:

```
knowledge\fusion360\
  captured\
  products\filament-basket.md
  printer-observations\overhang-tests.md
```

Then re-sync that store (next section). Files you **edit** are re-processed, files you **delete** are
removed from the database, and unchanged files are skipped.

---

## Commands

Run these in PowerShell. They use full paths, so you don't need to activate anything.

```powershell
cd C:\Users\ronbu\OneDrive\Documents\ClaudeCode\design-memory
```

**Health check** (run this first if anything seems broken):
```powershell
& C:\Users\ronbu\.venvs\design-memory\Scripts\python.exe check_setup.py
```

**Re-sync a store** after adding, editing, or deleting notes:
```powershell
& C:\Users\ronbu\.venvs\design-memory\Scripts\python.exe seed.py --store fusion360
& C:\Users\ronbu\.venvs\design-memory\Scripts\python.exe seed.py --store blender
```

**Search without Claude:**
```powershell
& C:\Users\ronbu\.venvs\design-memory\Scripts\python.exe search.py --store fusion360 "your question"
```

**Unit tests:**
```powershell
& C:\Users\ronbu\.venvs\design-memory\Scripts\python.exe -m unittest discover -s tests -v
```

**Database status:**
```powershell
docker compose ps
```

> **Avoid `seed.py --directory`** unless you mean it. It makes the store match *only* that folder and
> deletes everything else from that store's database. Your files are safe, but run a normal re-sync to
> restore them.

---

## Rebuilding from scratch

Because the notes are the real copy, the database can be thrown away at any time. If the Docker volume
is deleted or PostgreSQL is recreated:

```powershell
docker compose up -d
& C:\Users\ronbu\.venvs\design-memory\Scripts\python.exe seed.py --store fusion360
& C:\Users\ronbu\.venvs\design-memory\Scripts\python.exe seed.py --store blender
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `connection refused` / health check fails on the database | Docker Desktop isn't running. Open it, wait for **Engine running**, check `docker compose ps` shows **healthy**. |
| Claude says a design-memory server failed to connect | Check Docker first. Then start a **new** session (servers start with the session). Run the health check. |
| Memory tools missing in a session | That session was started in a different folder, in the web version, or before the servers were approved. Start a new local session in `ClaudeCode`. |
| `/capture-design-learning` not in the `/` list | Session started outside `ClaudeCode` or `design-memory`. Start a new session there. |
| First search in a session takes ~20 s | Normal: the model loads once per session. Later searches are fast. |
| Server fails with an offline/model-not-found error | The model cache was deleted. Run `check_setup.py` once in a PowerShell window **without** `HF_HUB_OFFLINE` set to download it again. |
| A deleted note still shows up | Re-sync that store. |
| Unrelated notes are coming back | Raise the store's cutoff in `rag_config.py` (e.g. 0.30 → 0.35). |
| A note you know exists isn't found | Lower the cutoff a little, or ask with wording closer to the note. |
| Claude saved a guess as fact | Edit or delete the `.md` file, then re-sync. **Never edit the database directly.** |
| Port 5432 already in use | Another PostgreSQL is running. Stop it, or change the port in `docker-compose.yml` **and** set `RAG_DB_PORT`. |

---

## Changes from the tutorial

| Change | Why |
|---|---|
| Python environment at `C:\Users\ronbu\.venvs\design-memory` | Keeps ~1 GB of packages out of OneDrive sync. |
| `.mcp.json` uses full paths to Python and `mcp_server.py` | The tutorial's plain `python` only works if Claude is started from an activated terminal. The desktop app isn't. |
| `.mcp.json` in both `ClaudeCode` and `design-memory` | Memory is available in your normal project folder too. |
| `HF_HUB_OFFLINE=1` in `.mcp.json` | Servers never contact the internet once the model is downloaded, and start faster. |
| `restart: unless-stopped` in `docker-compose.yml` | Database comes back by itself whenever Docker starts. |
| Similarity cutoff **0.30** (tutorial: 0.50) | Tested 2026-09-30: related questions scored 0.33-0.63 against a captured note, unrelated ones 0.06-0.26. At 0.50, 5 of 6 related questions were missed. Re-check once there are ~10 real notes. |
| Skill uses full paths with forward slashes | `${CLAUDE_PROJECT_DIR}` would point to the wrong folder from `ClaudeCode`. Also, `\$store` is treated as an escaped literal by Claude Code, so backslashes can't come right before `$store`. |
| Skill lives only in `ClaudeCode\.claude\skills\` | Claude Code also loads skills from parent folders, so one copy covers both. |

## Deliberately left out (from the tutorial)

No LangChain, LlamaIndex, ORM, web API, queue, reranker, approximate index, agent framework, or separate
vector-database product. Add the smallest thing that solves a real problem only if one shows up.
