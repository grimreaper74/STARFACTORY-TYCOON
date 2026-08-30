# Localization readiness — status and debt v001

Status: living checklist (owner reminder 2026-08-26: "don't forget
we're using credits and it's got to be translated"). The standing
decisions: the game ships translated into the main languages; the
currency is neutral Credits displayed "n cr" (locale-grouped digits),
internally integer hundredths ("pence" fields); never £/GBP in
player-facing text.

## Compliant today (audited 2026-08-26)

- All UI chrome authored this week is LOCTEXT (panel tabs, sections,
  buttons, orders, slots, top-bar readouts, objectives, pause menu).
- Money displays route through ULBSpacecraftTopBarWidget::
  FormatCurrency ("n cr"); the one refusal that prints amounts
  (INSUFFICIENT FUNDS) converts hundredths -> credits before display.
- "pence" appears player-visibly NOWHERE; the only remaining "pence"
  string is a UE_LOG diagnostic (deliberately greppable).
- Item badge icons are TEXTLESS as of today (category shapes +
  colours; the first cut had English words baked into the PNGs -
  regenerated, because texture text can never localize).

## Debt (ordered)

1. **Authority refusal strings** (the fail-closed toasts, DescribeLock
   and friends): English diagnostics shown verbatim. Standing plan:
   reason CODES from authorities, localized rendering at the UI layer,
   English kept in logs. Touches every authority - schedule as its own
   pass with tests pinning the codes.
2. **Catalogue display names**: station DisplayName, recipe
   DisplayName, research node DisplayName, item DisplayName are raw
   FStrings. Plan: string-table pass (FText::FromStringTable) keyed by
   the stable ids; the pure label builders keep their shape.
3. **Gather pipeline**: no Localization/Game target configured yet -
   the gather/PO/compile loop and CulturesToStage exist in config, but
   a first gather has never run. Schedule after (1) and (2) so the
   gather catches real keys.
4. Number/date formatting: FormatCurrency groups digits with ","
   hard-coded; swap to FText::AsNumber with culture grouping during
   the string-table pass (tests pin the en output).
