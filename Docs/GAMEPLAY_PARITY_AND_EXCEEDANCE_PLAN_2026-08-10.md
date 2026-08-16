# Line Boss — gameplay parity and exceedance plan

## Product promise

Line Boss should retain the readable build-and-bottleneck appeal of Production Line and Car Manufacture while exceeding them through a fully 3D, player-authored future car factory. The player is the line boss: they lay out equipment, storage, walkways and AGV routes; choose capacity and redundancy; diagnose flow, quality and maintenance; and decide which future vehicles to manufacture.

No proprietary code, data or art from installed reference games is used. They are interaction and pacing references only.

## What is already stronger in playable v978

- Continuous material identity from inbound wrapped coil through PR002 and the production chain.
- Player-placed, process-ordered machinery with automatic physical transport links and legitimate parallel branches.
- Player-painted AGV routes that now fail closed unless the actual travel path continuously reaches PR002.
- Four placeable wider Press Trains A-D, each a single saveable/removable unit with visibly moving transfer and press modules.
- Independent storage capacity, empty/occupied visuals and visible starvation/blockage states.
- Cleaning and maintenance fleets with separate docks, resources, wear, safety and faults.
- Approved high-detail 3D equipment pipeline using separate visual, motion and collision authority.

## Gaps before the game can honestly claim parity

1. **First-session onboarding:** guided camera, catalogue, placement, rotation, connection, route and first-coil objectives without a manual.
2. **Economic loop:** starting capital, purchase/running costs, energy, labour/service cost, sales income, penalties and bankruptcy/recovery rules.
3. **Order and demand system:** vehicle orders with volume, deadline, body variant, colour/trim and quality requirements.
4. **Vehicle/BOM system:** future Cairnwell models, shared platforms, panels/components, variant changeovers and finished vehicle identity.
5. **Progression:** research, supplier quality, machine upgrades, faster robots, storage/AGV expansion and new shops unlocked through proved production.
6. **Quality/rework:** dimensional checks, quarantine, scrap, rework routing and traceability consequences visible to the player.
7. **People and shifts:** staffing/skills only where they create decisions; no decorative workers that do not affect operation.
8. **Usability:** clear throughput overlays, bottleneck explanation, profitability breakdown, alerts, undo/replace, route editing and full gamepad placement.
9. **Content:** complete Press Shop first, then Body Shop, Paint Shop, General Assembly and outbound vehicle logistics using the same data-driven contracts.
10. **Release polish:** performance budgets, scalable detail, audio, accessibility, reliable save migration and repeated packaged playtests.

## Press Shop release milestone

The Press Shop is the proving ground and must be complete before cloning systems into other shops.

- New player can build lorry unloading -> PR002 -> storage -> PR004 -> PR005 -> blank buffer -> Train A -> inspection -> finished storage -> outbound.
- The catalogue reveals machinery in production order and explains the missing prerequisite.
- Conveyor/AGV links are physically continuous; unsafe or disconnected routes fail closed with a readable reason.
- Adding a second compatible machine or robot measurably increases capacity only when it addresses the current bottleneck.
- Storage has finite capacity and visible occupancy; blocked/starved states propagate without losing unit identity.
- At least one complete vehicle panel order can be produced, inspected, sold and included in profit/loss.
- Cleaning/maintenance neglect causes recoverable deterioration; adding support capacity has a measurable benefit.
- Save/load preserves machines, links, routes, units, orders, finances and in-flight operations.
- A first-time player can reach the first accepted panel in 15 minutes without developer intervention.

## Sequenced implementation

1. Finish/gate Press Shop appearances while retaining v978 gameplay placeholders.
2. Add the order/economy/BOM authority around the existing physical flow.
3. Add guided first-coil and first-panel objectives plus bottleneck explanations.
4. Complete one 2042 M1 vehicle family and connect stamped-panel output to its BOM.
5. Package and user-test the Press Shop milestone; fix comprehension and pacing before building other shops.
6. Reuse the proven contracts for Body, Paint and Assembly rather than creating separate one-off simulations.

## Definition of “better”

The claim is earned only when packaged playtests prove all of the following:

- players understand how to build and repair a line without outside help;
- layout, capacity, routing, maintenance and product choices produce different measurable outcomes;
- the full order-to-profit loop survives save/load;
- the factory remains readable and performant at intended scale;
- the 3D machinery and future vehicles improve immersion without obscuring the management decisions.

Until then, describe Line Boss as a deeper physical factory-building prototype—not as a finished superior game.
