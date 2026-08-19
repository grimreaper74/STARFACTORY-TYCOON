# UI research digest

## 1. The ten rules for Line Boss UI v2

**1. One status model drives every surface.**
Define a single C++ `EStationStatus` enum (Working / Starved / Blocked / QualityHold / WearCritical / Offline / Paused) with one severity-to-colour-and-shape map, and derive the card-strip dot, the detail-panel status line, and the world-toast trigger from it. Factorio's `EntityStatus` enum is the model — and Factorio's own failure (its HUD alerts run on a *separate* enum, producing panel/world disagreements players file as bugs) is the warning: Line Boss must run alerts off the same enum, not a parallel system.

**2. Name the cause, never just the magnitude.**
Satisfactory's bare uptime % and Production Line's time-usage pie both left players unable to tell starved from blocked from congested — documented complaint threads in both games. Anno 1800 enumerates the exact stop reason (input empty, output full, no workforce, incident, no electricity) in the building panel. Every Line Boss status is a named cause in localised FText ("Starved — no bodies from Weld"), and the panel's one primary action targets that cause.

**3. Alerts are stateful conditions with a data-driven severity table, not fire-and-forget events.**
A toast exists only while its condition is true on a live actor (auto-clears on fix/sell/demolish), retriggers update the existing toast, and each alert type declares severity (toast+bell / inbox-only / suppressed) in config. Captain of Industry patched toast spam, lingering dead-entity toasts, and per-tier muting across three separate releases; Two Point Museum patched thief-message spam post-launch. Every alert type also needs a concrete clearing player action — CS2's "High Rent" icon, which fired with no available fix, had to be re-specified twice and set the review tone for the whole game.

**4. No state is encoded by colour, sound, or a single surface alone.**
Two Point Hospital's audio-only staff alerts forced a deaf reviewer to play fully zoomed out; CS2 shipped hue-only infoviews colourblind players cannot read; 8-10% of males are red-green deficient. Every status pairs colour with a fixed shape glyph, every sound has a visual sibling, and every world toast has a camera-independent sibling (bell badge + card dot), so the bottleneck is findable from the strip with the camera anywhere.

**5. One canonical rate unit, and arithmetic that visibly reconciles.**
Satisfactory normalised everything to per-minute and previews the resulting rate before a change commits; CS2's Economy tab "not adding up" destroyed trust in the whole screen; Production Line players maintained external spreadsheets because the game never surfaced "this line supports N cars/hour". Pick cars/hour, use it on cards, panel and contract maths from the same counters and window, show required-vs-measured on every card, and make the reconciliation (press out = weld in ± buffer delta) an automated test.

**6. Transport controls are visible, hotkeyed, and honest.**
Anno 1800 PC ships speed control with zero HUD presence — a documented discoverability failure the Console Edition had to fix. CS2's 2x/3x buttons silently stop working on big cities with no UI acknowledgement. The mockup's visible pause/1x/2x/4x is right: lit active segment, hotkey shown in tooltip, and requested-vs-achieved speed as separate states (effective-rate badge on the button, day clock advances at achieved rate) so deadlines stay honest.

**7. Every panel is a navigation surface, never a dead end.**
Factoriopedia exists because tooltips couldn't be clicked; Production Line's 1.03 route-highlight was the patch Harris said "solves a lot of issues"; CoI's most popular mod exists to add "Show me" camera jumps. Upstream/downstream chips select-and-jump, bell entries pan the camera, selecting a card lights the actual feeding route in world, and off-screen alerts get screen-edge direction arrows on hover.

**8. One template, one grammar, one level deep.**
Factorio's FFF-318 enforces one canonical tooltip reused identically everywhere; Satisfactory uses one machine-window skeleton for every building; Anno 117's nested submenus and Two Point Museum's per-mechanic button mappings were both publicly punished. Build ONE station-panel UMG template with fixed slot positions, one verb set (confirm / cancel / cycle-tab / contextual-action) across build, inspection, contracts and inbox, and an acceptance test: every core stat reachable in one click or hover from the default view.

**9. Lock the interaction grammar now and treat it as a contract.**
Wube documents that "any major changes are hard to make" once habits form — the objectively-better 0.17 quickbar still generated a backlash. Space = pause, 1/2/3 = 1x/2x/4x (the CS2/RimWorld genre standard; deviating reads as broken), keys 1-4 or Q/E cycle shops, one-primary-action-per-panel. Document it in the repo; later rebinding is a breaking change requiring legacy options.

**10. Localisation, text size, and scale are structural, not polish.**
Short UI strings — exactly what the top bar, cards and action button are made of — expand 200-300% in German (W3C); every number must route through FText::AsNumber/AsCurrency (German writes 1.234,56); one project-wide Composite Font with Noto Sans SC covers zh-Hans. Floor: nothing under 12px at 1280x800 (Deck), 18px body height at 1080p (XAG), UI scale slider from build one. Two Point Museum got demoted to "Playable" on Deck for small text and had to patch scaling in — small text is the single most common management-game demotion.

## 2. Deltas to the current UI v2 design

### Top bar — keep the shape, upgrade every element
Anno validates the minimal bar; keep it strictly read-only global state (Two Point's Information Panel pattern). Changes:

- **Contract counter → always-visible progress widget**, not a count: `14/40 · 2d 4h`, Satisfactory-milestone style. Hover opens a mini contract dashboard (FFF-423 pattern): completion-rate sparkline over the last N game-minutes, projected finish vs deadline coloured green/red, and the blocking shop if behind. The player verifies "is the plant on pace" without opening anything.
- **Cash gains a net-rate delta** coloured green/red (Anno's global scope convention); hover breaks down income vs upkeep; click opens the finance view with time-window selector (today / 7 days / contract-to-date — Production Line's lesson that cumulative totals hide trends).
- **Transport control**: active speed segment lit; each button's tooltip shows the *live* hotkey binding via Enhanced Input lookup (never hardcoded "Space" in a localised string); a visible effective-rate state when 4x cannot be sustained (CoI's adaptive-sim decoupling, the fix for CS2's lying buttons).
- **Alert bell aggregates by category with a count** — never one entry per event. It opens a persistent inbox (below).
- All numeric fields in auto-size slots; all through ICU-aware FText formatters.

### Flow cards — promote the strip from dashboard to instrument
The strip is Line Boss's Statistics screen (the tool Anno had to retrofit in patch 6.0) and its region-switcher. Changes:

- **Each card shows measured vs required rate** (`9/hr / 12 needed`), so the strip answers "where is the bottleneck" with zero clicks. Grey out last-known throughput on stall rather than blanking (Production Line's blank-pie bug).
- **Status dot = colour + fixed shape**, one meaning per state, documented in one legend: filled circle running, triangle starved, square stopped, diamond quality hold, wrench wear. Same glyphs on toasts and bell entries — learned once.
- **Cards are camera navigation**: click selects the shop AND flies the camera; keys 1-4 bound to Press/Body/Paint/Assembly. Selection is bidirectional and spatial: the selected card's outline plus the in-world feeding route lit (Production Line 1.03's highest-leverage feature).
- **Buffer/WIP as pips** (filled vs hollow for in-transit), never bracketed numerals like "12 (4)".
- **Cards slide in with progression** — first contract shows Press only; the strip itself is the complexity ramp (CS2's milestone lesson).

### Detail panel — one template, cause-first, remote-capable
- One reusable UMG template, fixed slot order top to bottom: identity header → status lamp + named cause (FText) → throughput + short sparkline (last shift) → per-input/output buffer fill (`needs 2 · 38 buffered`, CoI's diagnosability standard) → named property groups (FFF-318 structure: unnamed root, then Inputs / Power & Wear / Contract impact) → **one primary action, icon + label, always anchored in the same spot**.
- The primary action maps 1:1 to the named cause: Starved → "Jump to Weld"; Quality hold → "Release / Scrap" with a quantified pass-chance % next to the button (TPH's cure-chance pattern — a number turns a binary click into a decision).
- Any rate-changing action **previews the resulting rate before commit** (Satisfactory overclock pattern); any numeric control accepts typed values, and where the player thinks in outcomes, the outcome is the input (set cars/day, derive line speed).
- Per-station stop is **"Hold station" with distinct iconography — never the word "pause"** (CoI's two-pause confusion), and the panel shows which of global-pause / station-hold applies.
- Panel is edge-anchored, collapsible, and never occludes the selected station (Two Point Museum's shipped failure). Station/part chips are clickable select-and-jump; reserve a "?" affordance in the input scheme for a post-v1 encyclopedia.
- The panel works remotely: resolving an alert never requires camera travel first (Factorio remote view / Satisfactory priority-switch lesson).

### Alerts — build the full stack now, it is the game's voice
CS2's reviews prove the notification layer sets the emotional tone of a management game. Ship day one:

- **Three layers, one enum**: card dot (passive), world toast at the station (per-instance, persistent until resolved or dismissed — never auto-timeout, Big Pharma's auto-cycling text is the anti-pattern), bell inbox (persistent, typed, re-readable — Two Point's letter inbox).
- **Bell inbox grouped by shop first, category second** (FFF-400's by-planet grouping — the mental model is spatial), with per-category filter, per-tier mute, dismiss-all, and a pin affordance for watch items. Every consequential toast also lands as an inbox entry.
- **Every alert type is a two-stage ladder**: wear-warning (amber, inbox) before breakdown (red toast, line stops); contract-at-risk before contract-failed. The warning stage is what makes the watch-and-fix loop fair.
- **Audio budget**: sound only for line-fully-stopped and imminent contract breach, one distinct plant-wide cue each (Satisfactory's fuse pattern); ongoing conditions never retrigger sound. Factorio had to delete its continuous attack sound; don't ship one.
- **Coalescing**: one toast per station per condition with a counter; shop-level badge when several stations share a condition — no icon confetti during a cascading stoppage (CS2's unmet mod demand).
- Later polish, reserve the hooks now: hover camera thumbnail (SceneCapture2D) on bell entries, screen-edge arrows for off-screen stations.

### Phases U1–U5 — re-scope so foundations precede surfaces
- **U1 (foundations) must absorb**: Common UI adoption, the `EStationStatus` enum + severity/shape/colour token map (Okabe-Ito derived), the canonical cars/hour rate system with windowed ring-buffer counters, one Composite Font asset + base text-style set, the type ramp with 12px@800p floor, and the UI scale slider. Every one of these is a documented expensive retrofit.
- **U2 (top bar)**: add the contract mini-dashboard hover, net-cash delta, honest-speed state, live-binding tooltips.
- **U3 (card strip)**: add required-vs-measured rates, shape-coded dots, camera-fly on click, bidirectional route highlight, progressive card unlock.
- **U4 (detail panel)**: the single template with cause line, buffer fills, rate preview, Hold verb, collapsibility.
- **U5 (alerts + onboarding)**: the severity table, ladders, inbox, coalescing — plus the tutorial, which reuses U2-U4 surfaces exclusively: a temporary objective checklist (retires permanently after contract 1, Satisfactory's ADA shape), a staged genuine press-starves-body bottleneck the player finds and fixes themselves (Factorio's FFF-329 verdict: the helper must never act for the player), skippable from new-game to the identical post-tutorial state, one analytics event per objective step, systems gated by contract completions not time. No modal screens, no bespoke tutorial level, no narrator system.
- **Per-screen definition of done, all phases**: run `-leet` (hardcoded-string check), preview German for overflow, `culture=zh-Hans` for font coverage, greyscale screenshot of the strip (states must read by shape+luminance), screenshot at 1280x800.

## 3. Traps to avoid

- **Anno 1800**: speed controls with no HUD presence — invisible transport state is a discoverability failure.
- **Anno 1800**: shipped without a production-overview screen; had to retrofit the Statistics menu under player pressure.
- **Anno 117**: nested build submenus and "fighting the UI to find your buttons" — one-level depth or reviewers punish it.
- **Anno 117**: minimal-to-sparse UI that hid management-relevant numbers scored as badly as clutter.
- **CS2**: speed buttons that silently stop honouring the multiplier.
- **CS2**: an alert ("High Rent") with no clearing player action — re-specified twice post-launch.
- **CS2**: hue-only overlays, no colourblind mode, continuing an unresolved complaint lineage from CS1.
- **CS2**: force-swapping the viewport into an overlay on selection — players begged for mods to stop it.
- **CS2**: per-building problem icons with no visibility controls — icon confetti with only debug-mode escape hatches.
- **Satisfactory**: bare efficiency % that never says why a machine idles.
- **Satisfactory**: no notification at all for starved/blocked machines — players installed webhook mods to fill the gap.
- **Factorio**: continuous alert audio for an ongoing condition — deleted as too annoying.
- **Factorio**: a year of polished guided-campaign work deleted; over-produced onboarding diverges from the game and gets cut.
- **Factorio**: tips shown once at start and never retrievable again — wasted content until rebuilt as trigger-unlocked and browsable.
- **Factorio**: alerts and entity status on two separate enums — panel and HUD can disagree.
- **Production Line**: a full stall visible only as small text inside a detail window, and a pie chart that blanked to nothing.
- **Production Line**: a mandatory action hidden behind a plain "Change" text button players never found.
- **Production Line**: one yellow encoding covering two different causes — players couldn't tell error from history.
- **Production Line**: missing ratio math forcing players into external spreadsheets.
- **Two Point Hospital**: audio-only alerts (unplayable for deaf players without max zoom-out) and tutorial pop-ups with no global mute, generating complaint threads across every game in the series.
- **Two Point Museum**: uncollapsible panels occluding the inspected object; inconsistent button verbs per mechanic; notification spam patched post-launch.
- **Big Pharma**: auto-cycling info pages that skip before the player finishes reading; console text too small to read.
- **Captain of Industry**: two things called "pause" in one window — players file "pause not working" bugs.
- **Factorio 0.17 quickbar**: even an objectively better rework of an established grammar generates a revolt — lock the grammar before habits form.

## 4. Deferred-but-design-for

**Controller / Steam Deck (target: 1.1-style pass that is a binding job, not a rebuild).**
Build every widget on Common UI now: CommonActivatableWidget stacks, a UI input-action data table, cardinal navigation, device-aware glyphs. Define a complete focus-traversal order across top bar → card strip → detail panel → toasts → settings from the start; no hover-only reveals, no drag-only controls, no mouse/controller lockouts. Track controller reachability per surface as an explicit checklist — Verified is all-or-nothing on content access (Dorfromantik was held at Playable over menus alone). Wire every EditableTextBox (save name, company name) to the Steam OSK call; it must handle IME for zh-Hans. Screenshot-test everything at 1280x800; nothing under 12px there; Factorio's verdict stands — don't plan to "fix Deck later with a Steam Input layout." Line Boss's small interaction set (no free placement in v1) makes native gamepad focus navigation the cheap path if the foundation is Common UI.

**Build mode slot.**
Pause-as-build-mode gets visibly modal chrome: HUD frame tint + mode label beside the transport controls so every screenshot is unambiguous about mode, single-key enter/exit, Escape restores the plain management view in one press. All panel actions, inbox triage and contract acceptance must be fully operable at 0x — make that an acceptance test. Reserve now: an "Edit"-style deep link from the detail panel into build mode scoped to the selected station (TPH's room panel), a "copy settings to like stations" affordance (Satisfactory's sampled-config pattern), and the placement-validity colour grammar for when free placement arrives post-v1. Global pause and station Hold remain separate verbs with separate icons forever.

**Accessibility toggles (ship the cheap ones in v1; the rest are pre-wired).**
Day one: UI scale slider (75-200% via `UUserInterfaceSettings::ApplicationScale` — one line at the root, but only if every widget is anchored/auto-sized, so that authoring rule is enforced from U1); full key remapping on Enhanced Input player-mappable keys with hints composed from live bindings; per-category alert mute and severity toggles; the Okabe-Ito-derived status palette (vermilion/bluish-green replacing red/green) with shape-paired glyphs — validated under deuteranopia simulation and greyscale before palette lock; no italics or decorative faces for data text. Design-for-later: 200% text scaling without content loss (detail panel gets a vertical ScrollBox as standard equipment; card strip picks its 200% degradation mode — horizontal scroll or two-row wrap — now), toast text budgeted at the subtitle tier or made click-persistent so the reading-speed constraint disappears, and world-toast visibility controls (category toggles, severity threshold) as shipping settings, not debug flags.
