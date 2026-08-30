<!-- COMMISSIONED BRAND SPEC, PRESERVED VERBATIM.
     Extracted from the owner's design-tool export on 2026-08-29.
     The source zip keeps ONE filename and has already been
     overwritten three times, so the only durable copy is this one.
     This is the AUTHORITY for colour, layout and motion; it
     supersedes the 'brand is OPEN' note in CLAUDE.md. Text is the
     tool's own wording - do not edit it to fit the code; if the
     code disagrees, the code is what changes, or the disagreement
     goes back to the next revision as an amendment. -->

Implementation spec · rev A

 1g palette · 1i type · wordmark pending

 Star Factory Tycoon — UI, refusal and world spec

 Transcribable values for native UMG. Hexes are sRGB — in C++ build them with FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("1B1B1BFF"))) so they land in linear space correctly; assigning a raw 0–1 triple from these numbers will read visibly darker. Nothing in this document depends on which wordmark you pick: the wordmark never appears in the HUD, only on the splash, the main menu and the capsule.

 01

 UI tokens — the dark panel

 TOKEN
 HEX
 USE

 Panel.Bg

 #1B1B1B

 Side panel fill. Flat, fully opaque — no translucency over the floor, so text contrast never depends on what is behind it.

 Panel.BgRaised

 #232322

 Nested blocks inside the panel: list headers, tab strip, the contract card.

 Panel.Rule

 #363433

 1px internal dividers between rows and sections. Never softened below 1px, never replaced by spacing alone.

 Panel.Edge

 #0E0E0E

 2px outer border where the panel meets the bright floor. Does the work a drop shadow would; there are no shadows in this UI.

 Text.Heading

 #A8A4A1

 Section headings — tracked caps in Saira Condensed. Deliberately quieter than body text; the heading is a locator, not content.

 Text.Body

 #EDEDEC

 Primary text: station names, part names, row labels, refusal detail lines.

 Text.Value

 #FFFFFF

 Numerals only — credits, counts, kW, timers, percentages. Pure white gives numbers weight without a hue.

 Text.Dim

 #918D8B

 Secondary information that is true but not urgent: units, QUEUED, timestamps, part codes.

 Text.Disabled

 #5E5B59

 Unbuildable / locked rows. ~2.7:1 on Panel.Bg, below the readable threshold on purpose — pair it with a struck rule or a disabled icon so colour is never the only signal.

 State.Positive.Fill
 + Text.OnPositive 

 #EDEDEC
#1B1B1B

 Affordable / ready / complete. A solid light chip with dark text — inverted weight, not a green. Also the fill of an enabled primary button.

 State.Warning.Hatch

 #918D8B
on #1B1B1B

 Warning / low stock / degrading. A 1px dashed border or 8px 45° hatch, text stays Text.Body. Carries no hue at all — this is what removes your amber-vs-orange collision (see §4).

 State.Refusal
 + Text.OnRefusal 

 #EC3013
#FFFFFF

 The only hue in the interface. Refusal banner fill, and a 2px left marker on the row or entity the refusal names. White text on it measures ~4.2:1, so set it at 13px SemiBold or larger and never in black.

 Row.Selected
 + Row.Selected.Marker 

 #2E2C2B
#EDEDEC

 Selected row: raised fill plus a 3px light left marker. Selection is a light accent, never red — red must only ever mean refusal.

 Row.Hover

 #262524

 Mouse-over fill on any interactive row or button. One step below Row.Selected so the two never read the same.

 Focus.Ring

 #EDEDEC

 2px gamepad/keyboard focus outline, 2px offset. Light, not red, for the same reason as selection.

 HUE DISCIPLINE — CONFIRMED

 Exactly one token owns a hue: State.Refusal #EC3013 . Every other UI value above is a neutral gray or white by construction (R≈G≈B). Red is forbidden on: selection, focus, hover, buttons, progress bars, timers, low-stock, hull integrity, minimap markers and tooltips. If a second hue is ever proposed for the panel, it takes the meaning away from refusal — the reason refusals read instantly is that nothing else on the interface is coloured.

 02

 The refusal rule — 2b, headline plus detail

 Your three real strings are all the same shape: a fixed reason, then variable entities and quantities. That is what decides it. Split every refusal into a translated headline and a wrapping detail line. The headline is the only part with a length budget, and it holds because it contains no entity names; the detail line takes the names, IDs and counts and is allowed to wrap freely. 2a's unbounded single block would put an 8-word Russian sentence in tracked caps, which is the least readable setting you have; 2c takes floor space for the state players see most.

 YOUR STRINGS, SPLIT

 INSUFFICIENT RESOURCES

 AssemblyRobot-002 needs 1× Component.Hull

 HEADLINE 22 · DETAIL 41

 NOT MOVE-READY

 Station 3 — 2 of 3 fits complete, propulsion outstanding

 HEADLINE 14 · DETAIL 55

 NO STORAGE RACK BUILT

 6 waiting at DeliveryDock-004

 HEADLINE 21 · DETAIL 29

 THE RULE

 HEADLINE Loc budget 28 characters. Caps, no entity names, no numbers. Wraps to 2 lines; if a locale still exceeds 2 lines it wraps to 3 and logs a loc warning — it is never clipped. 

 DETAIL Sentence case, no tracking, unbounded line count, target ≤ 4 lines at 390px. Entity IDs stay verbatim and untranslated. 

 OVERFLOW Word wrap first, per-character wrap as fallback for unbroken compounds. No ellipsis, no clip, no auto-shrink. Beyond 40% of panel content height the banner scrolls internally with the first line pinned. 

 WHO GROWS The banner grows, the panel does not. Panel outer rect is fixed; the part-list region above the banner is the flex loser and scrolls. Banner is anchored above the action bar and grows downward from a fixed top edge , so the first line never moves between the 1-line and 4-line cases. 

 COUNT One refusal per panel. A new refusal replaces the old one; it does not stack or queue. The banner persists while the condition holds — these are states, not toasts, so no auto-dismiss timer. 

 WORLD LINK While a refusal shows, the entity it names carries a 2px State.Refusal outline in the world and in the list. Same red, same meaning, no text in the world. 

 GEOMETRY Banner padding 10px 12px, headline-to-detail gap 0, line-height 1.35, 3px red left marker on the detail block. Content width 390px at 1920 (panel 422px), 250px at 1280 (panel 282px) — validate both. 

 UMG NOTES

 Both text blocks: AutoWrapText = true , WrappingPolicy = AllowPerCharacterWrapping , ClippingMode = Inherit (never ClipToBounds on a refusal), and no TextOverflowPolicy::Ellipsis . Banner is a Vertical Box with SizeToContent inside a Size Box with MaxDesiredHeight = 0.4 × panel content height , wrapped in a Scroll Box for the beyond-max case. The part list is the only Fill slot in the panel's root vertical box, so it absorbs every height change. Build the string with FText::Format and named arguments — never concatenate, or the detail line cannot be reordered in translation.

 03

 Type spec — authored at 1920×1080

 Sizes are px at 1080p and scale with your DPI curve; floor every role at 12px, below which the condensed faces lose their counters. Tracking is given in em — multiply by size for Slate's px letter-spacing.

 ROLE
 FACE
 SIZE
 WEIGHT
 TRACK
 LINE
 FIGURES

 Top-bar readout
 IBM Plex Sans Cd
 20px
 SemiBold 600
 0.02em
 24px
 Tabular + lining

 Section heading
 Saira Condensed
 13px
 SemiBold 600
 0.18em
 16px
 Caps, no numerals

 List row label
 IBM Plex Sans Cd
 15px
 Regular 400
 0em
 20px
 Sentence case

 Numeric value
 IBM Plex Sans Cd
 15px
 Medium 500
 0.01em
 20px
 Tabular + lining, right

 Button label
 Saira Condensed
 14px
 SemiBold 600
 0.10em
 16px
 Caps, flush left

 Refusal headline
 IBM Plex Sans Cd
 13px
 SemiBold 600
 0.08em
 18px
 Caps

 Refusal detail
 IBM Plex Sans Cd
 13px
 Regular 400
 0em
 18px
 Tabular + lining

 TABULAR FIGURES — THE UMG CATCH

 Slate exposes no OpenType feature switches, so you cannot turn on tnum at runtime. Bake it: run pyftfeatfreeze -f tnum,lnum over IBM Plex Sans Condensed Regular / Medium / SemiBold, rename the family (the OFL requires it — see §5), and import that as a separate typeface used for every live number. Verify by holding a credits value at 1,111,111 and 8,888,888 in consecutive frames: the string width must not change. Saira Condensed carries proportional figures and is never used for numerals — headings and button labels only.

 SCRIPT COVERAGE

 IBM Plex Sans Condensed covers Latin, Greek and Cyrillic, so the whole UI face is safe for RU/UK/PL/TR. Saira Condensed's released masters are Latin + Vietnamese with only partial Greek and no Cyrillic — check the build you ship, and for Cyrillic and Greek locales fall back headings and button labels to IBM Plex Sans Condensed SemiBold at the same size and tracking. For CJK, fall back to Noto Sans SC / JP / KR (also OFL) with tracking set to 0 and caps disabled. No text in any texture or icon, as specified.

 04

 The factory floor — world albedo tokens

 These are base-colour / albedo values, not final pixels — your lighting will lift them. Judge them the way the player does: whole-bay zoom, fixed near-isometric, lights on. HSV is given because that is what the governing rule is written in, and because your amber collision was a saturation problem, not a hue problem.

 TOKEN
 HEX
 HSV
 USE

 Floor.Concrete
 #C9C5BE
 40° · 5% · 79%
 The bright ground the whole game reads against. Warm-neutral, never blue-gray.

 Floor.Concrete.Wear
 #B2AEA7
 40° · 6% · 70%
 Slab joints, drone-lane wear, stains. The only floor variation — no tinted patches.

 Floor.Line.Lane
 #9E9A93
 40° · 7% · 62%
 Painted layout lines, bay numbers, footprint outlines. Gray paint, not white — white belongs to indicators.

 Structure.Graphite
 #4A4D50
 206° · 6% · 31%
 Frames, gantries, station chassis, conveyor beds. The mass of the factory.

 Structure.Graphite.Dark
 #33363A
 212° · 12% · 23%
 Recesses, undersides, cable trays, rubber. Reads as shadow without being lit as shadow.

 Machine.Housing.Pale
 #D6D2CB
 38° · 5% · 84%
 Large machine bodies, robot chassis and panelling — the "lights on" surface. Every machine surface over 0.5 m² is this, not amber.

 Machine.Amber
 #A87334
 33° · 69% · 66%
 Moving parts only, and only on surfaces under 0.5 m²: arm segments, fitting heads, lift carriages. Robot and machine bodies take Machine.Housing.Pale — amber marks what moves , never a whole chassis and never a static frame.

 Machine.Amber.Trim
 #C08A3C
 35° · 69% · 75%
 Edge strips and end caps under 0.5 m² only. The brightest non-ship, non-emissive surface allowed.

 Crate.Tan
 #B39468
 35° · 42% · 70%
 Crates, pallets, part bins. Same hue family as amber but 27 saturation points below it — that gap is what stops the floor reading as one orange mass from above.

 Crate.Tan.Dark
 #8E7350
 33° · 44% · 56%
 Crate banding, straps, stencilled panels (never stencilled text — no baked strings).

 Hazard.Yellow
Hazard.Black
 #C9A21C
#23211F
 46° · 86% · 79%
34° · 9% · 14%
 45° striping at a fixed 200mm pitch in world space, always paired with black. Exempt from the saturation ceiling because it is factory-native, but bound by the footprint rule below.

 Indicator.Working
 #BFE4FF
 205° · 25% · 100%
 Emissive. Means powered and working . Steady while running, slow 0.8s pulse while waiting on input.

 Indicator.Idle
 #6E7C86
 203° · 18% · 53%
 Unlit lamp: built but unpowered or unassigned. Reads as "off", not as a state.

 Indicator.Complete
 #EDEDEC
 60° · 1% · 93%
 Single white flash on a completed fit or handoff. Matches State.Positive.Fill in the UI, so "done" is white in both world and panel.

 Indicator.Fault
 #E33A1C
 9° · 87% · 89%
 Blocked, starved or faulted — the world half of State.Refusal, deliberately the same red. This is the only red in the world.

 THE SATURATION CEILING — SATURATION × FOOTPRINT

 SURFACE AREA
 MAX S
 EXAMPLES

 > 2 m²
 22%
 Floor, walls, structure, machine housings

 0.5 – 2 m²
 45%
 Crates, bins, conveyor sides. Robot and machine bodies sit here, so they take Machine.Housing.Pale, not amber

 < 0.5 m²
 70%
 Machine.Amber and Amber.Trim (arm segments, fitting heads, edge strips), hazard striping, decals

 < 0.05 m², emissive
 exempt
 Indicator lamps only

 Ship liveries
 60–100%
 Any area, any hue — the only surfaces allowed both S > 70% and V > 80%

 THE AMBER / WARNING COLLISION — RESOLVED TWICE

 First, in the UI: warning is State.Warning.Hatch , a gray dashed treatment with no hue, so there is no warning orange left to collide with. Second, in the world: Machine.Amber is capped at V 66% and S 69%, and no world surface may be both bright and saturated. A UI element and a machine can therefore never land on the same colour, because only one of them is allowed to have a hue at all.

 SAFETY YELLOW — WHERE IT MAY AND MAY NOT GO

 May: drone-lane edges, launch-chicane boundary, under-gantry exclusion zones, dock lips, step and pit edges, moving-machine swept-area outlines. Always painted on the floor or on a static structure edge, always striped with black, always at the fixed world pitch so it reads as one system from the fixed camera.
 May not: machine bodies, robot arms, crates, ship hulls or anything a livery touches; the UI; icons; the wordmark or any marketing surface. It is floor infrastructure, not a brand colour — the moment it appears on a machine it starts competing with amber, and the moment it appears in the panel it competes with the ships.

 THE SHIP-DOMINANCE CHECK

 Once per bay, screenshot at whole-bay zoom and run a chroma pass. Non-ship pixels above 60% saturation should stay under 8% of the frame, and the single most saturated pixel in frame should always belong to a hull. If a livery ever loses that test, lower the machinery — never raise the livery, because the customer chose that colour.

 05

 Font licensing — both faces clear to embed

 FACE
 LICENCE
 AUTHOR
 SHIPPING OBLIGATION

 Saira Condensed

 SIL Open Font License 1.1

 Omnibus-Type (Héctor Gatti)

 Reserved Font Name "Saira". Ship OFL.txt and the copyright line in your third-party notices.

 IBM Plex Sans Condensed

 SIL Open Font License 1.1

 IBM

 Reserved Font Name "IBM Plex". Same notice requirement; no royalty, no per-title fee.

 WHAT OFL 1.1 PERMITS HERE

 The OFL allows the fonts to be used, modified and redistributed freely as long as they are not sold on their own, and lets the fonts and their derivatives be bundled, embedded, redistributed and sold with any software provided reserved names are not reused. Embedding the .ttf in a shipped Unreal .pak is exactly this case, so no separate licence is needed. Confirm the OFL.txt in the specific release you download — it travels with the font files.

 TWO THINGS THAT WILL CATCH YOU

 The tabular-figures instance in §3 is a modified font, so under the Reserved Font Name clause it must not ship as "IBM Plex …" — rename the family (e.g. SFT Readout Condensed ) and keep the original copyright and licence notice inside the file. Same applies to any subset you generate to cut package size. And derivatives stay under OFL — you cannot relicense them, though that has no bearing on the game itself.

 METRIC-COMPATIBLE SUBSTITUTES, IF YOU EVER NEED THEM

 Neither face needs replacing, but if legal wants alternatives: Archivo Narrow (OFL 1.1, Omnibus-Type) for headings and button labels — same manufacturing tone, wider than Saira Condensed so re-check button widths; Barlow Semi Condensed (OFL 1.1, Jeremy Tribby) for the UI face, with lining figures and near-identical x-height to IBM Plex Sans Condensed at the same px size. Neither is metrically identical, so any swap needs one pass over the panel at 1280×720 to confirm no row wraps that did not wrap before.
