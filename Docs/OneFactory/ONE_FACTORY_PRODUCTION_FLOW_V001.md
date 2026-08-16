# OneFactory production flow v001

Status: source candidate; combined Editor build and automation pending.

`ALBOneFactoryProductionFlowAuthority` is the single presentation-free owner of
vehicle WIP and genealogy in the unified Moorcross Works map. It does not own
machines, station layouts, meshes or visual actors.

Each car receives one immutable logical identity when a commissioned Press line
allocates a coil lot. That same identity moves through the exact sequence:

1. inbound coil;
2. blank preparation;
3. pressing;
4. pressed-panel stillage;
5. body framing;
6. body-in-white;
7. body quality inspection;
8. pretreatment;
9. ED coat;
10. colour coat;
11. cure;
12. paint quality inspection;
13. general-assembly trim;
14. powertrain marriage;
15. rolling chassis;
16. end-of-line inspection;
17. finished vehicle; and
18. dispatch.

Every transition records a globally unique evidence ID. The record also keeps
its build order, vehicle model, paint programme/colour, allocated material lots,
current station, current department and stage revision. Presentation will later
reconstruct from `UnitId + Stage + PaintColourId`; it must never create a second
logical record.

The authority fails closed when a department is uncommissioned, paused,
faulted or output-blocked. Body, Paint and end-of-line inspection are explicit
quality gates. A pass is required to continue; rework resets the same unit to a
pending inspection without creating another unit. Rejected or scrapped units
cannot advance.

`FLBOneFactoryProductionLedgerState` is a complete `SaveGame` snapshot. Restore
validates every counter, stage/department pairing, unique vehicle/build-order
identity, material genealogy, globally unique evidence, completion flag and WIP
limit before a single assignment commit. Invalid or duplicated WIP therefore
cannot partly mutate the live factory.

Integration order after the four starter authorities are compiled:

- The player builder creates one production authority only after the required
  department starters exist.
- Starter commission actions synchronise the four commission flags.
- Runtime station completion calls `AdvanceVehicle`; inspection calls
  `SubmitQualityResult`.
- The OneFactory campaign save embeds the captured ledger beside the four
  presentation-free starter-layout snapshots.
- A later native WIP presentation actor reads the ledger and binds the clean-room
  `VehicleWIPNativeKit_v001` layers. It owns no genealogy and is never saved.

