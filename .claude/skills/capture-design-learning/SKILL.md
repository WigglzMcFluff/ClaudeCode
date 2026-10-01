---
name: capture-design-learning
description: Extract durable, evidence-backed design knowledge from the current Claude Code session, save it as clean local RAG source material, and re-index the selected CAD knowledge store. Use only when the user deliberately wants to retain a lesson from the current design session.
argument-hint: "<fusion360|blender> [focus]"
arguments: [store, focus]
disable-model-invocation: true
---

Capture durable design knowledge from the current conversation into the local design-memory RAG.

Store: `$store`
Optional focus: `$focus`

The design-memory project lives at `C:\Users\ronbu\OneDrive\Documents\ClaudeCode\design-memory`. Always use the absolute paths below, regardless of which folder this session was started in.

## Validate the destination

`$store` must be exactly `fusion360` or `blender`. If it is not, stop and tell the user to invoke the skill as:

`/capture-design-learning fusion360 [optional focus]`

or:

`/capture-design-learning blender [optional focus]`

Do not infer a different store when the argument is invalid or missing.

## What qualifies

Review the active conversation itself. Retain only knowledge that will be useful in a future design session and is supported by evidence in this session.

A candidate qualifies when at least one of these is true:

- the user reported a physical print, fit, assembly, measurement, or test result;
- a tool produced a concrete measurement or result;
- the user explicitly established a design requirement or durable decision;
- a failure and a corrective change were observed, with the outcome stated in the session;
- a tool-specific procedure was actually demonstrated to work in this session.

Do not retain:

- your own unsupported guesses or explanations;
- hypotheses that were never checked;
- approaches later shown to be wrong;
- intermediate values superseded by later measurements;
- conversational filler;
- generic knowledge that is readily available in ordinary documentation;
- a causal claim when the session only established correlation.

If nothing meets the bar, write nothing and say that the session did not produce durable evidence-backed knowledge.

## Produce standalone retrieval records

Create one Markdown file for each distinct reusable lesson under:

`C:/Users/ronbu/OneDrive/Documents/ClaudeCode/design-memory/knowledge/$store/captured/`

Use a short semantic filename such as `rear-tab-flex-under-four-spools.md`, not a timestamp or session number. Before creating a new record, inspect existing files under `C:/Users/ronbu/OneDrive/Documents/ClaudeCode/design-memory/knowledge/$store/` for the same lesson. Update an existing record when the new session materially strengthens or corrects that same knowledge instead of creating a duplicate.

Write the files as UTF-8 text.

Each record must make sense when retrieved months later with no access to this conversation. Use this structure:

```markdown
# <specific standalone lesson>

**Topic:** <concise subject>
**Evidence type:** <physical result reported by user | tool measurement | explicit requirement | demonstrated procedure>

## Reusable knowledge
<The smallest complete statement that should influence a future design decision. Include actual dimensions, materials, geometry, or conditions when they matter.>

## Conditions
<The product, geometry, material, printer/process, tool state, or other boundaries required to interpret the finding correctly. Omit irrelevant details.>

## Evidence
<What actually happened or was measured in this session. Separate observation from interpretation.>

## Boundaries
<What this session did not establish, especially where a future Claude session could otherwise over-generalize the result.>
```

Prefer one precise lesson over a session summary. If the session contains several independent durable lessons, write several small records rather than one broad record.

## Re-index

After writing or updating the records, run:

`"C:\Users\ronbu\.venvs\design-memory\Scripts\python.exe" "C:\Users\ronbu\OneDrive\Documents\ClaudeCode\design-memory\seed.py" --store $store`

(In PowerShell, prefix the command with `&`.) If it fails with a connection error, tell the user to start Docker Desktop and wait for the database container to become healthy, then retry.

Do not edit the PostgreSQL database directly. The Markdown files are the source of truth; the vector database is a rebuildable index.

## Finish

Report only:

- the files created or updated;
- one sentence per retained lesson;
- whether re-indexing succeeded.
