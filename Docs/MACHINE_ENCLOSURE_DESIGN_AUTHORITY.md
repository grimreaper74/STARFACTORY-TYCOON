# Cairnwell enclosed automated-machine design authority

Status: active project direction from the user, 2026-08-04.

## Player-facing rule

Normal production is presented as a connected sequence of enclosed automated
machine cells. Material enters through a controlled opening, the named process
occurs inside a Cairnwell enclosure, and the correct intermediate or finished
part leaves through the next controlled opening. The remote control room and
fixed CCTV network are the primary player viewpoint; inspection drones are the
secondary close-view tool.

This is not permission to replace process simulation with featureless boxes.
The validated feed, gantry, lift, press, die, transfer, sensor, buffer and
traceability mechanisms remain authoritative and animated inside their shells.
They become visible through inspection glazing, dedicated internal cameras,
maintenance-open states and removable service panels.

## Process-specific outputs

- PR-006 to PR-008 receive strip and output cut blanks.
- PR-009 receives individual blanks and outputs identified blank stacks or
  carriers to PR-010; it does not output a formed body panel.
- PR-010 stores and routes blank stacks to the four press trains.
- Each press train receives the scheduled blank and outputs the correctly
  formed panel stage toward the next press or finished-panel buffer.

## Press-train simulation depth

User authority: the four press trains only need to look and sound convincingly
operational at the management-game viewing distance. Do not attempt full sheet
metal deformation, finite-element behaviour or simulation of every internal
pump, gear and valve.

Each train uses one authoritative gameplay cycle shared by visuals, audio, HMI,
throughput, energy, wear, buffers, faults and save state. The observable cycle
is: scheduled blank arrival, guarded feed/position, press-ready indication,
ram/die stroke, synchronized impact and hydraulic/servo response, replacement
of the input blank with the correct formed-panel stage, retract and downstream
transfer. Selected flywheels, feed rolls, clamps, slide/ram, conveyors and
service indicators animate where cameras can see them. Layered spatial idle,
feed, charge, impact, retract, conveyor and alarm audio plus restrained structure
vibration, dust/oil-mist and status lighting sell the hidden machinery.

Internal close views may show representative mechanisms but are never required
to reproduce every real working component. The state and material genealogy
must remain truthful even when the physical transformation is presented as a
timed mesh/state swap.

## Reusable enclosure system

- Dimensioned modular structural frame, opaque sheet-metal skins, removable
  service doors, laminated inspection windows, roof/utility modules and sealed
  cable/air/hydraulic penetrations.
- Cairnwell foundry-charcoal structure, Cairnwell green service panels,
  restrained safety-yellow edges and hardware, readable station identity and
  local service/status HMI.
- Closed and interlocked during normal production. Doors, panels or windows may
  expose the already validated machinery only in authorised inspection,
  commissioning or isolated-maintenance states.
- No pedestrian player route is required. Certified MR-01/CR-01 access,
  material collision, crane clearance, service envelopes, zero-energy proof,
  E-stops, light curtains and controlled transfer openings remain mandatory.
- Approved open-mesh guarding remains at exposed conveyors, transfer apertures,
  gates and unavoidable external hazards. Do not wrap a fully enclosed machine
  in redundant fencing.

## Unreal and promotion requirements

Enclosures must be reusable CAD/Blender-authored modular assets with native
centimetre import scale and identity actor scale. Shell collision must not block
validated material or robot paths. Closed/open/maintenance states, interlocks,
save/load state and CCTV readability must be proved in PIE. A shell is not
promoted merely because import or collision tests pass: every station still
requires fresh fixed-camera Unreal screenshots inspected against its Pro
reference and its exposed internal mechanisms must remain believable when the
game reveals them.

## First implementation

PR-009 is the pilot because its v089 machinery, process authority, collision,
navigation and save state are already technically proven. Preserve v089 and the
retained v092 service-identity direction. Build the first shell as an isolated
successor, keep the infeed/outfeed paths open, keep the south HMI and electrical
cabinet externally accessible, and provide deliberate windows/camera views of
the gantry, blank stack and carrier handoff. PR-010 remains on hold until the
PR-009 enclosure pattern has passed its visual and runtime gates.
