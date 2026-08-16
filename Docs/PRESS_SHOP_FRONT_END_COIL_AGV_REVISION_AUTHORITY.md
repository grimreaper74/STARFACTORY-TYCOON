# Press Shop front-end coil AGV revision authority

Status: OWNER-DIRECTED ISOLATED DESIGN REVISION — NOT PROMOTED  
Date: 2026-08-05

## Decision

The owner has requested a purpose-built AGV for routine PR-003 to PR-004 coil transport. The overhead crane and C-hook remain available for coil-store replenishment, recovery and maintenance.

This is a deliberate revision to the existing front-end automation concept. The authoritative Sheet 2 layout and Sheet 4 automation sequence currently describe crane retrieval as the normal transfer method. They do not authorize an AGV. Therefore:

- retained map `/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124` remains unchanged;
- AGV work must start as an isolated direct child of v124;
- existing crane runtime authority must remain functional in that candidate as fallback/recovery;
- no map or asset may be promoted until the revised visual, runtime, safety, collision/navigation, save and authority gates pass;
- any layout dimension not present in an approved source is marked `TBC`.

## Reused verified inputs

- Packaged master-coil nominal envelope: 1,500 mm axial width × 1,900 mm outside diameter.
- Existing PR-004 coil interface: 25–30 tonne coils, 1,800–2,100 mm OD, maximum width 1,550 mm.
- PR-003 storage: exactly 12 positions, two rows of six, 2,200 mm pitch within a row and 6,000 mm between row centrelines.
- Existing pedestrian, guarding, emergency-access and crane-clearance provisions remain protected.

## Candidate AGV design contract

| Property | Candidate value | Authority |
|---|---:|---|
| Source vehicle envelope | 3,610 × 2,220 × approximately 1,180 mm, empty assembled vehicle | Independently measured Candidate v001 FBX; operational approval TBC |
| Loaded envelope | 3,610 × 2,220 × approximately 2,510 mm | Derived from verified 1,900 mm OD coil and source assembly; TBC |
| Payload design target | 40 tonnes | Owner-selected nominal target; certification TBC |
| Routine carried coil | 25–30 tonnes | Existing PR-004 interface |
| Coil axis on vehicle | X/local longitudinal | Matches existing master-coil asset |
| Lift stroke | 80 mm | Candidate gameplay/readability target; TBC |
| Steering | Four steer-drive modules / zero-turn capable | Candidate concept; TBC |
| Route clear width | 3,000 mm candidate minimum | Unapproved generated-sheet value; TBC |
| Travel speed and stopping distance | TBC | Must not be fabricated |

The coil must be physically supported by two replaceable rubber-lined V shoes on the lift deck. The vehicle must show four steer-drive cassettes, front and rear safety scanners, corner lidar housings, emergency stops, bumpers, amber beacon, blue direction lights, status lamps, lift/dock sensors and positive docking locators. Cairnwell Automotive is the only vehicle branding.

## Operating and safety contract

Normal sequence: request coil → reserve source slot → verify PR-004 ready → close/guard transfer route → dispatch empty AGV → dock at selected transfer interface → receive and positively locate coil → verify load → travel to PR-004 → dock and transfer → verify coil accepted → clear route.

Movement is inhibited when any of the following is false: route reserved, pedestrian gates proved, scanner zone clear, load secured, destination ready, dock handshake valid, emergency circuit healthy and no conflicting crane motion in the shared envelope.

On scanner trip, gate loss, load-loss indication, docking timeout or authority loss, the AGV performs a controlled stop and requires the defined recovery flow. The crane may recover a stranded load only after AGV isolation and maintenance authority are proved.

## Promotion hold

This document authorizes isolated candidate work only. It does not certify machinery, dimensions, routes, speeds, stopping distances or safety performance.
