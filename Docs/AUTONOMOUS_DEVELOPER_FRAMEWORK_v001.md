# Autonomous Local AI Developer — framework authority v001

**Date:** 2026-08-31. **Status:** Phase 1 in progress (diagnosis complete,
repair starting). **Owner grant:** full authority to fork/customise
AgentZet and the local Qwen/Ollama/TRELLIS stack; only base-model weight
modification is out of scope (adapters/fine-tunes deferred until the
framework approach demonstrably hits its ceiling).

## Objective

Turn this PC into a dedicated autonomous developer for STAR FACTORY
TYCOON:

    Owner → qwen3-coder:30b (Ollama) → customised AgentZet → TRELLIS → UE 5.8

The owner gives game-development instructions ("build the
engine-installation station for the Scout"), not coding instructions. The
agent plans, inspects, reuses, generates 3D via TRELLIS, imports,
implements, tests in PIE, reads logs, repairs and reports — and never
claims success without evidence.

## Environment (verified live, 2026-08-31)

| Piece | State |
|---|---|
| Ollama | Up on :11434. `qwen3-coder:30b` Q4_K_M, 262k max context, native `tools` capability. Also `qwen3.8:27b` (tools+vision — candidate for reference-image work) and `qwen2.5-coder:14b`. |
| AgentZet | Compiled into the project (5 modules); source committed at `8a09705`. Provider=Ollama, model=qwen3-coder:30b, OllamaContextSize=32768 (per-project editor settings). |
| TRELLIS | `trellis-server.exe` + `trellis-cli.exe` at `%LOCALAPPDATA%\trellis-studio\runtime\`, full Q8 model set (`models\q8`: shape/tex flows 512+1024, BiRefNet matting, DINOv3). Server only runs while Studio is open — the framework must manage its own instance or use the CLI. |

## The tool-hallucination bug — diagnosis (evidence-backed)

Reported symptom: Qwen invents nonexistent tools (`list_assets`,
`get_project_info`, `list_levels`); a prompt patch did not help.

### Live probes (reproduced outside AgentZet)

1. **3 clean tools, native API** → perfect `tool_calls`, correct name,
   valid JSON. The model is NOT inherently broken.
2. **Needed tool absent** → model emits a *spurious call to a real tool*
   with dummy args while saying it can't help. A legitimate
   "no tool fits" exit is required.
3. **All 105 plugin tools (~30k tokens) via `/v1/chat/completions`** →
   Ollama processed only **2,050 prompt tokens** (silent truncation; the
   `options.num_ctx` field is ignored on the OpenAI-compat endpoint).
   Model saw only the alphabetical tail (widget tools), said so, and
   called a hallucinated tool named `error`. **Bug reproduced.**
4. **Same 105 tools via native `/api/chat` with `options.num_ctx=40960`**
   → all 31,910 tokens processed (fix path confirmed), but the model
   emitted the call as pseudo-XML *text*, not `tool_calls` — and prefill
   cost 40 s. Even with full context, ~100 tools break call formatting.

Conclusion: **small task-scoped toolsets are the only regime where this
model reliably works**, and context size is only controllable on the
native endpoint.

### Code audit (six-reader workflow + adversarial verify over the plugin)

The compound causal chain, each link cited in the audit:

1. **Context silently tiny.** `num_ctx` is sent inside `options` on
   `/v1/chat/completions` (OpenAICompatClient.cpp:1184), where Ollama
   ignores it → the model runs at the small default; system prompt,
   tools and history get truncated top-first with no warning.
2. **The prompt teaches a phantom tool.** The local condensed system
   prompt advertises `search_files` (SAgentZetMainPanel.cpp:2024) which
   exists in **no** schema file; it also sits in the 23-name "essential"
   whitelist where the intersection silently drops it
   (ToolSchemaRegistry.cpp:741). The plugin itself models name-invention.
3. **Discovery is broken three ways.** Category filter matches a JSON
   field zero tools define (registry :331 → always empty); the fallback
   substring-loads a *different* set than the listing renders
   (ChatSession.cpp:624); the model is then told "All N tools loaded" and
   calls listed-but-unloaded names — indistinguishable from hallucination.
4. **No client-side name validation.** Any returned name is broadcast
   and routed (OpenAICompatClient.cpp:2014, ChatSession.cpp:784); unknown
   names fail only at executor lookup with
   `EXECUTION FAILED: No executor registered for tool: X` — no valid-tool
   list, no suggestion (ActionRouter.cpp:105). The existing fuzzy
   "did you mean" runs only inside `get_tool_info`.
5. **Invented read-looking names auto-execute.** Read-only classification
   is a name-prefix heuristic (`list_`, `get_`…) and auto-approval
   defaults on (ChatSession.cpp:880) — so `list_assets` runs unprompted,
   fails, and the failed call is **replayed in history as a legitimate
   tool_call** (OpenAICompatClient.cpp:1272), reinforcing the name.
6. **Loop pressure without exits.** No iteration cap ("Roo Code
   approach", ChatSession.cpp:60); a no-tool reply triggers a nudge
   demanding tool use (ChatSession.cpp:1023) — exactly the pressure that
   produced the spurious call in probe 2. The repetition detector shows a
   modal to the USER, never feedback to the model, and resets on any
   arg variation. `FAgentZetErrorFeedback` (retry budget) and
   `FAgentZetSafetyGate` are dead code.
7. **History/serialization defects.** Malformed tool-args JSON is coerced
   to `{}` and dispatched silently (OpenAICompatClient.cpp:2025);
   system-role notices are dropped in serialization (:1355); the
   condenser orphans tool results so summaries never see them; truncation
   is pairing-unaware. MCP tools are sent on the first request but not on
   continuations — the toolset shrinks mid-conversation.
8. **Qwen `<think>` content is unhandled** — streamed raw into chat and
   replayed in history (owner requirement: hidden CoT must not show).
9. **`pcg_tools.json` has a UTF-8 BOM** — strict JSON parsing can drop
   that whole toolset silently.
10. The hallucinated names appear nowhere in the plugin (except as
    negative examples inside the 2026-08-31 patch): they are **training
    priors** (generic Unreal-MCP tool names) filling the gaps the above
    defects create. The 78 KB `agentZet_system_prompt.txt` is cloud-only
    (local path returns early, MainPanel.cpp:2071) — a prompt patch there
    can never reach Qwen.

## Architecture decision

Fork-in-place: AgentZet's module layout, action router and UI are kept;
the LLM transport, tool routing, prompting, validation and recovery are
redesigned for a 30B local model. Naming: the customisation is tracked in
this doc series; stock source is preserved in git history (`8a09705`).

Principles (each backed by a probe above):
- **Native `/api/chat` transport** for Ollama with per-request
  `options.num_ctx`, and `prompt_eval_count` echoed into the log as a
  truncation tripwire.
- **Task-scoped toolsets** (~10–20 tools) selected per request by a
  deterministic router — never the full catalogue; the toolset a request
  carries is the *same* source of truth the prompt's tool list is
  generated from.
- **Client-side tool-name validation**: unknown names never execute;
  the model gets a corrective tool_result naming the valid set and the
  nearest match.
- **A legitimate no-tool exit** (`answer` / `report_blocked`) so the
  model is never cornered into inventing calls.
- **Bounded loops** with model-visible feedback on every failure class
  (unknown name, bad args, repetition, iteration budget).
- **Evidence discipline**: compile/PIE/log/asset checks as first-class
  tools; "done" requires their output.

## Phase plan (owner's ten steps, mapped)

| # | Step | State |
|---|---|---|
| 1 | Audit AgentZet | **Done** — six-reader workflow + adversarial verify |
| 2 | Diagnose tool-call failure | **Done** — reproduced live, root chain above |
| 3 | Repair tool discovery/execution | **Done first pass** — repair set below, proven by step-4 eval |
| 4 | Prove reliable project inspection | **PROVEN** (eval `step4e`, 2026-08-31, 57 s, 3 turns): `list_directory` + `read_file_snippet` executed with real results; `attempt_completion` named three files (all verified present) and the declared class `ALBSpacecraftGameMode : AGameModeBase` (verified at the header's line 30). No invented tools, no invented facts. Transcript `Saved/AgentZetEval/outbox/step4e.jsonl` + summary in the tab's `api_history.json`. |
| 5 | Prove small reversible change | **PROVEN** (eval `step5a`, 2026-08-31, 14 s): `create_blueprint_actor` + `compile_blueprint` both executed; `Content/AgentZetEval/BP_EvalProbe.uasset` (23,801 bytes) verified on disk; summary accurate and relayed the EventTick warning honestly. Probe asset deleted after the session (reversibility). |
| 6 | Prove compile/test + failure detection | **PROVEN** (eval `step6a`, 2026-08-31, 67 s): `compile_blueprint` on a nonexistent asset returned "EXECUTION FAILED: Blueprint not found"; the model's completion stated the failure and its cause verbatim — no fabricated success. Known roughness: the transcript's `is_error` flag stays false for EXECUTION FAILED results (the router returns them as plain content), so graders must read result text, not the flag. |
| 7 | TRELLIS integration | **CLI validated end-to-end** (52.8 s @512 → 139k-tri textured GLB, verified in Blender; unit-scale confirmed → explicit scale baking required, existing Blender lane covers it). Agent-facing tools pending. |
| 8 | Prove image→asset→Unreal automatically | Pending |
| 9 | Persistent project memory | Pending (design: files under `Plugins/AgentZet/Resources/ProjectMemory/` + injection budget) |
| 10 | Expand toward autonomous construction | Pending |

## Phase-3 repair set — IMPLEMENTED 2026-08-31 (first pass)

All items below are built (editor target compiles clean) with the game's
130/2 test baseline intact. Live in-editor Qwen validation is the next
gate — until that runs, these are code-complete, not proven.

R1 ✅ Ollama transport → native `/api/chat`: `bUseOllamaNativeApi` in
    OpenAICompatClient - URL swap (strips the forced `/v1`), temperature
    moved into `options`, replayed assistant `tool_calls.arguments` sent
    as OBJECTS (a string 400s on the native Go unmarshal), response
    parsed from top-level `message` with object-arguments, and
    `prompt_eval_count` logged with a warning tripwire when it presses
    against `num_ctx` (the silent-truncation signature).
R2 ✅ Unknown-tool guard in `ExecuteToolCall`: names with neither
    executor nor schema never execute; the model gets corrective
    feedback with word-overlap nearest matches ("list_assets" →
    search_assets, list_directory), the exact callable set, discovery
    pointers, and the no-tool exits. Real-but-unsent tools now execute
    AND self-pin into `DynamicallyLoadedTools`.
R3 ✅ Prompt truth: the local prompt's tool list is now GENERATED from
    `GetEssentialSchemas()` (single source of truth); `search_files`
    phantom removed from both the essential whitelist and the prompt;
    `list_assets` added to the deny examples.
R4 ✅ Discovery coherence: new `GetToolNamesInCategory()` sharing THE
    pattern map with `ListToolsInCategoryString`; ChatSession loads
    exactly what was listed and reports the loaded names verbatim
    (never "all tools loaded"); `get_tool_info`'s success banner is
    gated on real registration - it used to confirm hallucinated names
    as "loaded and available".
R5 ✅ Loop hygiene: 60-iteration hard cap (the no-limit design's $ cost
    gate is inert for a free local model); malformed argument JSON now
    short-circuits with the raw text quoted back instead of silently
    running the tool with `{}` args; router unknown-tool error enriched
    as defense-in-depth.
R6 ✅ `<think>` stripping at all three content sinks (native parse,
    OpenAI parse, FinalizeResponse) - UI, history and replay never see
    chain-of-thought; unterminated tags drop the tail.
R7 ✅ `pcg_tools.json` BOM stripped.
R10 ✅ Schema description truncation raised 200→600 / 80→200 chars -
    sized for the ~22-tool request reality, not the old 93-tool one.

Deliberately NOT done: `tool_choice:auto` for Ollama (field doesn't
exist on the native endpoint; changing the OpenAI path adds risk for
nothing) and history scrubbing of invented names (synthesis item 11 -
pairing-sensitive, deferred until the guard proves itself live).
Still open from the set: MCP schema consistency on continuations (R8),
repetition feedback to the model rather than only a user modal, and a
`report_blocked` explicit no-tool tool.

Evidence: build log `%TEMP%\build_azfix3.log` (Succeeded), game suite
`Saved/Automation/AgentZetRepairs_2026-08-31` (130 pass / 2 expected).

## Eval harness (built 2026-08-31)

Scripted, repeatable proof for Phase-1 steps 4-6 — evidence instead of
hand-testing:

- **In-editor**: `FAgentZetEvalBridge` (AgentZetUI), active only when the
  editor is launched with `-AgentZetEvalBridge`. File protocol under
  `Saved/AgentZetEval/`: drop `inbox/<id>.prompt.txt`, the bridge summons
  the AgentZet tab, submits through `SAgentZetMainPanel::OnPromptSubmitted`
  (the EXACT path a human takes), captures every message to
  `outbox/<id>.jsonl`, auto-approves tool batches (recorded in the
  transcript), and writes `outbox/<id>.done` when the agent finishes.
  Mirrors the game's `-LineBossAutomationBridge` safety pattern: opt-in
  flag, project-Saved files only, no sockets.
- **Driver**: `Scripts/run_agentzet_eval.ps1 -EvalId X -Prompt "..."` -
  atomic prompt drop, waits on the done marker, prints transcript.
- **TRELLIS lane**: `Scripts/trellis_generate_v001.ps1 -Image ref.png
  -Name part_name [-Res 512|1024]` - deterministic CLI generation with a
  sha256 manifest, refusing silent overwrite, per repo lane conventions.

First-run findings (all fixed the same day):
- The panel's `ActiveChatSession` member is declared but never assigned
  anywhere - dead state; the live session belongs to the active
  conversation tab (`GetActiveTabState()->ChatSession`). The bridge's
  session accessor now routes through the tab state.
- The panel restores prior task tabs at startup, so the first eval
  inherited a 35-message stale history - both a prefill tax and
  behavioral contamination from pre-repair conversations. The bridge
  now opens a FRESH tab per eval.
- The HTTP client's timeout does not fire OnAgentFinished, so a dead
  request left no `.done` marker. The bridge now has its own 660 s
  eval timeout finishing as `bridge_timeout`.
- UE's default JSON writer pretty-prints; transcripts are now condensed
  one-object-per-line as the .jsonl name promises.

Second-run finding - the greedy-decoding runaway (fixed 2026-08-31):
two consecutive evals died at the client's 600 s timeout with zero
messages. Ollama's server log showed both requests prefilled instantly
(prompt cache hit) and then GENERATED for 9m59s until the client hung
up. Cause was compound: upstream AgentZet forces `temperature 0.0`, and
the Qwen team explicitly warns that greedy decoding puts Qwen3 into
endless repetition loops; with no `num_predict` cap and llama.cpp
context shifting, such a loop never terminates (old tokens are shifted
out, so it never even hits the context wall). Measured generation speed
was healthy (43.5 tok/s at 49 % CPU offload — qwen3-coder is MoE, ~3B
active), ruling out starvation. Fix: the native path no longer sends a
temperature at all — the modelfile already carries the Qwen-recommended
sampling (temp 0.7, top_p 0.8, top_k 20, repeat_penalty 1.05) — and
sends `num_predict 2048`, so a runaway now returns a truncated,
readable response with `done_reason="length"` (logged as a warning)
instead of hanging silently. Tool-call determinism was never real
anyway: temp 0 traded imaginary determinism for real deadlocks.

Third-run finding - the boot-storm starvation (fixed 2026-08-31): a
first eval launched seconds after editor start ran the same request
that takes 20-57 s on a settled editor for 600+ s and died at the
client timeout, twice. The editor's startup burst (asset-registry
scan, DDC churn, map load - not only shaders; one failing run had an
empty shader queue throughout) starves the CPU-offloaded model half.
Fixes, verified together by eval `step4g`: the bridge holds prompts
until quiescence (shader queue empty AND asset registry idle AND 30 s
sustained quiet), the client's local-provider timeout floor rose to
1200 s, and the bridge's own eval timeout to 1260 s so it always
outlasts the client. step4g: prompt dropped the instant bridge.ready
appeared (worst case), held 34 s by the gate, then ran clean in
20.6 s. attempt_completion summaries are also recorded into the
transcript now (before the finish broadcast unbinds the bridge), so
transcripts grade without the api_history workaround.

Measured performance envelope (2026-08-31, this machine): generation
50.8 tok/s with the editor closed, 43.5 tok/s with it open and idle -
the 49/51 CPU/GPU split does NOT change when the editor frees VRAM
(the 20 GB model simply exceeds the 12 GB card), so ~50 tok/s is the
hardware ceiling for this model. Warm-cache turn startup 0.3 s;
contention pushes prefill to 16 s+ and boot storms collapse
generation ~12x. Speed strategy is therefore: protect the prompt
cache, never run during storms, and cut turn counts with high-level
tools - not chase tokens/sec.

Operational note - VRAM contention: with the editor resident, only
~10.4 GB of the model fits on the 12 GB card (and a 32k KV cache adds
~3.6 GB to the model's footprint), leaving heavy CPU offload and
multi-minute first turns. `OllamaContextSize` is set to 16384 for this
machine - roughly half the KV memory back as GPU weight layers; the
essential-toolset requests run ~4-6k tokens, and the prompt_eval
tripwire warns if anything ever approaches the window.

## Evidence ledger

- Probes 1–4: transcripts in session scratchpad (`qwen_tooltest_*.json`
  + outputs, 2026-08-31).
- TRELLIS run: `trellis_cli_test_drone.glb` (139,488 tris, 1.0×0.86×0.51
  normalized), from `assembly_drone_iso.png`, seed 42, res 512, 52.8 s.
- Audit workflow: run `wf_0b8d7464-1be` (six readers, verifier,
  synthesis), journal in session transcript dir.
