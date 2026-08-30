# Star Factory Tycoon — build notes for reviewers

**Parthenon Interactive · pre-alpha vertical slice · PC (Windows), keyboard and mouse**

This is an in-development build. It is a vertical slice: the core loop runs
end to end, and the content around it is deliberately thin. There is no
tutorial yet, so these notes stand in for one.

Run `LineBossCarFactory.exe`. It takes a few seconds to open.

---

## What you are looking at

You run a factory that builds small spacecraft to order. You take a
contract, lay out a production line, and the line builds the ship. Every
craft leaves in its customer's own colours and flies out of the building
under its own power.

## Controls

| | |
|---|---|
| Pan the camera | WASD, or drag with the right mouse button |
| Zoom | Mouse wheel |
| Select and place | Left mouse button |
| Site view / factory interior | **M** toggles between them |
| Console (see below) | `¬` or `~` |

## The first two minutes

1. You start on the **site**, an illustration of the whole plant seen
   from above. It is a picture you click, not a world you fly around.
2. Twelve places are drawn on it. Most wear a **padlock** — they are
   drawn so you can see what the site becomes, and they say plainly why
   they are shut if you click them. A **plus** means you can build that
   one now. The **ship factory has neither**: it is already standing and
   it is where you begin.
3. **Click the ship factory.** The camera drops inside onto the factory
   floor.
4. The panel on the left is the **build menu**. It shows only what you can
   afford and are allowed to build right now, so it is short at the start
   and grows.
5. Under **CONTRACTS**, take a Scout order. A hull appears at the head of
   the line and work begins.
6. Watch **THE LINE — WHO FITS WHAT** in the left panel. It tells you which
   components each station fits and how long it stops for. That readout is
   the game: a single station fits all six components in one long stop, and
   building more stations splits the work between them.
7. Follow a hull down the line. Drones fit parts from the kit dolly beside
   each station; a gantry crane lifts the hull between them. It ends at the
   spray booth, where it takes the customer's livery through the glass.
   A Scout is about seven minutes of fitting from end to end.

## Then the factory stops, and that is the game starting

**Your factory opens with parts for exactly one craft.** When the second
hull reaches the head of the line it will stop, and the panel will tell you
why in plain words:

> INSUFFICIENT RESOURCES: AssemblyRobot-002 NEEDS 1x Component.Hull — NONE
> IN THE FACTORY, AND NO DELIVERY DOCK TO ORDER THEM TO; BUILD ONE

That is not a fault. It is the second thing the game asks you to do, and
every refusal in it works this way — it names what is missing and what to do
about it. To get going again:

8. Build a **delivery dock**. Goods you buy arrive there.
9. Build a **storage rack**. Drone haulers stage through a rack, so without
   one nothing is ever collected from the dock — and the panel will say so
   if you skip it.
10. **Order components** at the dock. There is a **BUY QUANTITY**
   control that cycles x1 / x5 / x20, so stocking up for a long run is
   one click per item rather than twenty. Importing all six for a Scout costs
   about 119,600 cr against the 150,000 cr the craft sells for. That is a
   deliberately thin living: importing everything keeps you afloat and never
   makes you rich.

## Making the parts yourself

Importing is the starting position, not the destination. The margin is in
fabricating components rather than buying them, and getting there is the
game's main line of progression:

- Press **M** for the site and build a **Parts factory** — either from
  the build menu, or by clicking its place on the site picture when it
  is no longer padlocked. Fabrication machines do not stand on the floor — they go
  **inside** a parts factory, in its slots. Try to place a Smelter on the
  ship-factory floor and the game says so: *"Smelter GOES INSIDE A Parts
  factory — BUILD ONE AND INSTALL IT IN A SLOT."*
- Install machines into those slots and give each one a recipe.
- Some machines are **research-locked** — a CircuitFab answers *"IS LOCKED —
  RESEARCH IT FIRST."* Research is the third tab in the panel.

Drone haulers move finished parts from the parts factory to storage and on
to the line, so the two buildings work as one factory. Watching that supply
chain fill itself is the thing we would most like a fresh pair of eyes on.

## What to try if you have ten minutes

- **Place a second fitting station** and lay track to it. Watch the stop
  times in the panel split between stations. That is the central decision
  of the game.
- **Hire more drones** at a station. An understaffed station fits parts
  badly and produces defects.
- **Let a deadline get close.** Contracts have real deadlines and the
  penalty is real.

## Things we already know, so you needn't report them

- **No controller support.** This is the largest single piece of work
  between here and console, and we know it is a design problem rather than
  a remap. Flagged deliberately rather than glossed.
- **No tutorial or onboarding.** The design intent is that the simulation
  teaches by refusing clearly — every refusal names its reason — but that
  is not a substitute for onboarding and we know it.
- **No audio.** Sound design has not started.
- **Placeholder art in places.** Some machinery is still drawn from
  primitives. The line, the crane, the booth and the craft are real models.
- **Two craft classes only.** The Scout and the Cargo. Further classes are
  designed but not built.
- Some console log warnings reference archived assets from an earlier
  version of the project. They are noise, not faults.

## What we would most value your view on

1. **Is the core decision legible?** Does it become clear, without being
   told, that building more stations makes the line faster by splitting the
   fitting sequence?
2. **Is the delivery worth watching?** The craft starting itself and flying
   out is meant to be the reward the factory exists to produce.
3. **Does the factory read at a glance** — can you tell a working station
   from a starved one without opening a menu?

## Developer console

Press `¬`. Useful commands if you want to skip ahead:

| | |
|---|---|
| `LB.Spacecraft.Status` | Prints the state of the line |
| `LB.Spacecraft.Jump Assembly` | Fast-forwards until a craft reaches a stage |
| `LB.Spacecraft.Watch` | Frames one station close enough to see the drones work |
| `LB.Spacecraft.SiteMap` | Frames the whole site |

A Scout is about seven minutes of fitting in real time.
`LB.Spacecraft.Jump` is the quickest way to see the end of the line without
waiting for it.
