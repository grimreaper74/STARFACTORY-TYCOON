#include "LBSpacecraftInventoryAuthority.h"

#include "LBSpacecraftProductionTypes.h"

namespace LBSpacecraftInventoryPrivate
{
	// Unity-build safety: helpers qualified by subject.
	FLBSpacecraftItemDefinition MakeInventoryItemRow(const TCHAR* Id,
		const TCHAR* Display, ELBSpacecraftItemCategory Category,
		int32 UnitVolume)
	{
		FLBSpacecraftItemDefinition Row;
		Row.ItemId = FName(Id);
		Row.DisplayName = Display;
		Row.Category = Category;
		Row.UnitVolume = UnitVolume;
		return Row;
	}

	TArray<FLBSpacecraftItemDefinition> BuildPhase2ItemTable()
	{
		using EC = ELBSpacecraftItemCategory;
		TArray<FLBSpacecraftItemDefinition> Table;
		// Raw intake (6). Catalogue section 2, Phase-2 subset.
		Table.Add(MakeInventoryItemRow(TEXT("Raw.IronOre"),
			TEXT("Iron Ore"), EC::Raw, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Raw.TitaniumOre"),
			TEXT("Titanium Ore"), EC::Raw, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Raw.CopperOre"),
			TEXT("Copper Ore"), EC::Raw, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Raw.Silicon"),
			TEXT("Silicon"), EC::Raw, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Raw.Polymers"),
			TEXT("Polymers"), EC::Raw, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Raw.Chemicals"),
			TEXT("Chemicals"), EC::Raw, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Raw.ExoticAlloy"),
			TEXT("Exotic Alloy"), EC::Raw, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Raw.FusionCellPrecursor"),
			TEXT("Fusion Cell Precursor"), EC::Raw, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Raw.Carbon"),
			TEXT("Carbon"), EC::Raw, 1));
		// Processed stock (8).
		Table.Add(MakeInventoryItemRow(TEXT("Proc.Steel"),
			TEXT("Steel"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.TitaniumAlloy"),
			TEXT("Titanium Alloy"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.LightAlloy"),
			TEXT("Light Alloy"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.CopperWire"),
			TEXT("Copper Wire"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.Composites"),
			TEXT("Composites"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.PlateStock"),
			TEXT("Plate Stock"), EC::Processed, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.FrameStock"),
			TEXT("Frame Stock"), EC::Processed, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.FuelMix"),
			TEXT("Fuel Mix"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.CarbonPanel"),
			TEXT("Carbon Panel"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.Fasteners"),
			TEXT("Fasteners"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.Sealant"),
			TEXT("Sealant"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.Coolant"),
			TEXT("Coolant"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.CeramicTile"),
			TEXT("Ceramic Tile"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.CanopyGlass"),
			TEXT("Canopy Glass"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.InsulationFelt"),
			TEXT("Insulation Felt"), EC::Processed, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Proc.CircuitSubstrate"),
			TEXT("Circuit Substrate"), EC::Processed, 1));
		// Sub-parts (100 - owner 2026-08-27: "around the same number of
		// parts as car manufacturer", measured at 117 categories / 99
		// concrete parts). 76 BASE parts feed 24 SETS which feed the six
		// components. Two levels, not one: a component recipe taking all
		// ~17 of its parts would need 17 item types in a stockpile that
		// caps at 48 units, and the hauler tops up 4 per item - 68 units
		// of demand into 48 of capacity is a starvation deadlock.
		// Hull (17 base + 4 sets - the two skid parts became six gear
		// parts when the undercarriage became tricycle gear).
		Table.Add(MakeInventoryItemRow(TEXT("Part.KeelSpar"),
			TEXT("Keel Spar"), EC::SubPart, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Part.FrameRib"),
			TEXT("Frame Rib"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.BulkheadPanel"),
			TEXT("Bulkhead Panel"), EC::SubPart, 3));
		Table.Add(MakeInventoryItemRow(TEXT("Part.FloorPan"),
			TEXT("Floor Pan"), EC::SubPart, 3));
		Table.Add(MakeInventoryItemRow(TEXT("Part.HullSection"),
			TEXT("Hull Section"), EC::SubPart, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Part.NoseCone"),
			TEXT("Nose Cone"), EC::SubPart, 3));
		Table.Add(MakeInventoryItemRow(TEXT("Part.TailCone"),
			TEXT("Tail Cone"), EC::SubPart, 3));
		Table.Add(MakeInventoryItemRow(TEXT("Part.AccessHatch"),
			TEXT("Access Hatch"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CanopyFrame"),
			TEXT("Canopy Frame"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.Canopy"),
			TEXT("Canopy"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.HeatShieldTile"),
			TEXT("Heat-Shield Tile"), EC::SubPart, 1));
		// THE UNDERCARRIAGE (owner 2026-08-28: tricycle landing gear,
		// and "the gear parts can be wired into the parts system").
		// Skids are superseded: the craft rolls on a nose leg and two
		// mains. Counted PER FITTED INSTANCE, as the owner asked -
		// three oleo struts and three wheels because there are three
		// legs, and only TWO brake units because a nose wheel does not
		// brake. The legs themselves are sub-assemblies, so the set
		// recipe stays three items wide and cannot starve a stockpile.
		Table.Add(MakeInventoryItemRow(TEXT("Part.GearOleoStrut"),
			TEXT("Oleo Strut"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.GearWheel"),
			TEXT("Gear Wheel"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.GearBrakeUnit"),
			TEXT("Brake Unit"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.GearRetractActuator"),
			TEXT("Retract Actuator"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.NoseGearLeg"),
			TEXT("Nose Gear Leg"), EC::SubPart, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Part.MainGearLeg"),
			TEXT("Main Gear Leg"), EC::SubPart, 5));
		Table.Add(MakeInventoryItemRow(TEXT("Part.HullFrameSet"),
			TEXT("Hull Frame Set"), EC::SubPart, 8));
		Table.Add(MakeInventoryItemRow(TEXT("Part.HullSkinSet"),
			TEXT("Hull Skin Set"), EC::SubPart, 8));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CanopySet"),
			TEXT("Canopy Set"), EC::SubPart, 5));
		Table.Add(MakeInventoryItemRow(TEXT("Part.LandingSet"),
			TEXT("Landing Set"), EC::SubPart, 6));
		// Electronics (13 base + 4 sets).
		Table.Add(MakeInventoryItemRow(TEXT("Part.CircuitBoard"),
			TEXT("Circuit Board"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.ControlComputer"),
			TEXT("Control Computer"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.MemoryBank"),
			TEXT("Memory Bank"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.WiringLoom"),
			TEXT("Wiring Loom"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.PowerBusBar"),
			TEXT("Power Bus Bar"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.ConnectorBlock"),
			TEXT("Connector Block"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.SensorArray"),
			TEXT("Sensor Array"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.ProximitySensor"),
			TEXT("Proximity Sensor"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.ThermalSensor"),
			TEXT("Thermal Sensor"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.DisplayCluster"),
			TEXT("Display Cluster"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.SwitchPanel"),
			TEXT("Switch Panel"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.AntennaMast"),
			TEXT("Antenna Mast"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.Transceiver"),
			TEXT("Transceiver"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.AvionicsCoreSet"),
			TEXT("Avionics Core Set"), EC::SubPart, 5));
		Table.Add(MakeInventoryItemRow(TEXT("Part.HarnessLoomSet"),
			TEXT("Harness Loom Set"), EC::SubPart, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Part.SensorSet"),
			TEXT("Sensor Set"), EC::SubPart, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CockpitPanelSet"),
			TEXT("Cockpit Panel Set"), EC::SubPart, 5));
		// Power (12 base + 4 sets).
		Table.Add(MakeInventoryItemRow(TEXT("Part.BatteryCell"),
			TEXT("Battery Cell"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.BatteryHousing"),
			TEXT("Battery Housing"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.PowerRegulator"),
			TEXT("Power Regulator"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CapacitorBank"),
			TEXT("Capacitor Bank"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.ReactorCore"),
			TEXT("Reactor Core"), EC::SubPart, 3));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CoreShielding"),
			TEXT("Core Shielding"), EC::SubPart, 3));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CoolantPump"),
			TEXT("Coolant Pump"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CoolantLine"),
			TEXT("Coolant Line"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.RadiatorPanel"),
			TEXT("Radiator Panel"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.InverterUnit"),
			TEXT("Inverter Unit"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.DistributionNode"),
			TEXT("Distribution Node"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.ChargePort"),
			TEXT("Charge Port"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.BatteryPackSet"),
			TEXT("Battery Pack Set"), EC::SubPart, 5));
		Table.Add(MakeInventoryItemRow(TEXT("Part.ReactorSet"),
			TEXT("Reactor Set"), EC::SubPart, 6));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CoolingSet"),
			TEXT("Cooling Set"), EC::SubPart, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Part.PowerBusSet"),
			TEXT("Power Bus Set"), EC::SubPart, 5));
		// Propulsion (13 base + 4 sets).
		Table.Add(MakeInventoryItemRow(TEXT("Part.ThrusterNozzle"),
			TEXT("Thruster Nozzle"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CombustionChamber"),
			TEXT("Combustion Chamber"), EC::SubPart, 3));
		Table.Add(MakeInventoryItemRow(TEXT("Part.InjectorHead"),
			TEXT("Injector Head"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.Turbopump"),
			TEXT("Turbopump"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.FuelPump"),
			TEXT("Fuel Pump"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.FuelLine"),
			TEXT("Fuel Line"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.FuelTank"),
			TEXT("Fuel Tank"), EC::SubPart, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Part.TankBaffle"),
			TEXT("Tank Baffle"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.GimbalMount"),
			TEXT("Gimbal Mount"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.GimbalActuator"),
			TEXT("Gimbal Actuator"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.IgnitionUnit"),
			TEXT("Ignition Unit"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.RcsThruster"),
			TEXT("RCS Thruster"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.ValveBlock"),
			TEXT("Valve Block"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.EngineCoreSet"),
			TEXT("Engine Core Set"), EC::SubPart, 7));
		Table.Add(MakeInventoryItemRow(TEXT("Part.FuelFeedSet"),
			TEXT("Fuel Feed Set"), EC::SubPart, 5));
		Table.Add(MakeInventoryItemRow(TEXT("Part.TankSet"),
			TEXT("Tank Set"), EC::SubPart, 6));
		Table.Add(MakeInventoryItemRow(TEXT("Part.GimbalSet"),
			TEXT("Gimbal Set"), EC::SubPart, 5));
		// Navigation (12 base + 4 sets).
		Table.Add(MakeInventoryItemRow(TEXT("Part.Gyroscope"),
			TEXT("Gyroscope"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.AccelerometerPack"),
			TEXT("Accelerometer Pack"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.StarTracker"),
			TEXT("Star Tracker"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.NavDish"),
			TEXT("Nav Dish"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.DishActuator"),
			TEXT("Dish Actuator"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.RangingLaser"),
			TEXT("Ranging Laser"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.BeaconLight"),
			TEXT("Beacon Light"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.AttitudeComputer"),
			TEXT("Attitude Computer"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.FlightRecorder"),
			TEXT("Flight Recorder"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.HorizonSensor"),
			TEXT("Horizon Sensor"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.Magnetometer"),
			TEXT("Magnetometer"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.Transponder"),
			TEXT("Transponder"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.InertialSet"),
			TEXT("Inertial Set"), EC::SubPart, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Part.SkyTrackSet"),
			TEXT("Sky-Track Set"), EC::SubPart, 5));
		Table.Add(MakeInventoryItemRow(TEXT("Part.DishSet"),
			TEXT("Dish Set"), EC::SubPart, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Part.FlightComputerSet"),
			TEXT("Flight Computer Set"), EC::SubPart, 4));
		// Interior (13 base + 4 sets).
		Table.Add(MakeInventoryItemRow(TEXT("Part.SeatFrame"),
			TEXT("Seat Frame"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.SeatKit"),
			TEXT("Seat Kit"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.HarnessSet"),
			TEXT("Harness Set"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.FloorMat"),
			TEXT("Floor Mat"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.WallLiner"),
			TEXT("Wall Liner"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CeilingPanel"),
			TEXT("Ceiling Panel"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.StorageLocker"),
			TEXT("Storage Locker"), EC::SubPart, 3));
		Table.Add(MakeInventoryItemRow(TEXT("Part.LifeSupportUnit"),
			TEXT("Life-Support Unit"), EC::SubPart, 3));
		Table.Add(MakeInventoryItemRow(TEXT("Part.AirScrubber"),
			TEXT("Air Scrubber"), EC::SubPart, 2));
		Table.Add(MakeInventoryItemRow(TEXT("Part.OxygenTank"),
			TEXT("Oxygen Tank"), EC::SubPart, 3));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CabinLight"),
			TEXT("Cabin Light"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.FireSuppressor"),
			TEXT("Fire Suppressor"), EC::SubPart, 1));
		Table.Add(MakeInventoryItemRow(TEXT("Part.PressureDoor"),
			TEXT("Pressure Door"), EC::SubPart, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Part.SeatingSet"),
			TEXT("Seating Set"), EC::SubPart, 5));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CabinTrimSet"),
			TEXT("Cabin Trim Set"), EC::SubPart, 5));
		Table.Add(MakeInventoryItemRow(TEXT("Part.LifeSupportSet"),
			TEXT("Life-Support Set"), EC::SubPart, 6));
		Table.Add(MakeInventoryItemRow(TEXT("Part.CabinFitSet"),
			TEXT("Cabin Fit Set"), EC::SubPart, 6));
		// The six assembled components mirror ELBSpacecraftComponent - the
		// existing BOM becomes ITEMS so component lines can build ahead.
		Table.Add(MakeInventoryItemRow(TEXT("Component.Hull"),
			TEXT("Hull Component"), EC::AssembledComponent, 8));
		Table.Add(MakeInventoryItemRow(TEXT("Component.Electronics"),
			TEXT("Electronics Component"), EC::AssembledComponent, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Component.Power"),
			TEXT("Power Component"), EC::AssembledComponent, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Component.Propulsion"),
			TEXT("Propulsion Component"), EC::AssembledComponent, 6));
		Table.Add(MakeInventoryItemRow(TEXT("Component.Navigation"),
			TEXT("Navigation Component"), EC::AssembledComponent, 4));
		Table.Add(MakeInventoryItemRow(TEXT("Component.Interior"),
			TEXT("Interior Component"), EC::AssembledComponent, 6));
		return Table;
	}
}

const TArray<FLBSpacecraftItemDefinition>&
FLBSpacecraftItemCatalogue::GetItemTable()
{
	static const TArray<FLBSpacecraftItemDefinition> Table =
		LBSpacecraftInventoryPrivate::BuildPhase2ItemTable();
	return Table;
}

const FLBSpacecraftItemDefinition* FLBSpacecraftItemCatalogue::FindItem(
	FName ItemId)
{
	for (const FLBSpacecraftItemDefinition& Row : GetItemTable())
	{
		if (Row.ItemId == ItemId)
		{
			return &Row;
		}
	}
	return nullptr;
}

int64 FLBSpacecraftItemCatalogue::GetRawItemPricePence(FName ItemId)
{
	// PROVISIONAL prices pending the owner's economy tuning.
	static const TMap<FName, int64> Prices = {
		{ FName(TEXT("Raw.IronOre")), 4000 },
		{ FName(TEXT("Raw.TitaniumOre")), 12000 },
		{ FName(TEXT("Raw.CopperOre")), 6000 },
		{ FName(TEXT("Raw.Silicon")), 8000 },
		{ FName(TEXT("Raw.Polymers")), 5000 },
		{ FName(TEXT("Raw.Carbon")), 9000 },
		{ FName(TEXT("Raw.Chemicals")), 7000 },
		// Premium tail (Production Line calibration: raws are not a
		// price tier - exotics legitimately out-price cheap parts).
		{ FName(TEXT("Raw.ExoticAlloy")), 120000 },
		{ FName(TEXT("Raw.FusionCellPrecursor")), 180000 } };
	const int64* Price = Prices.Find(ItemId);
	return Price != nullptr ? *Price : 0;
}

int64 FLBSpacecraftItemCatalogue::GetItemImportPricePence(FName ItemId)
{
	// PROVISIONAL import premiums - ~1.3x the on-site cost (Production Line calibration: thin
	// arbitrage keeps importing a REAL choice), so
	// fabrication pays for itself once volume arrives (make-vs-buy).
	static const TMap<FName, int64> Prices = {
		// Hull.
		{ FName(TEXT("Part.KeelSpar")), 72000 },
		{ FName(TEXT("Part.FrameRib")), 38000 },
		{ FName(TEXT("Part.BulkheadPanel")), 54000 },
		{ FName(TEXT("Part.FloorPan")), 49000 },
		{ FName(TEXT("Part.HullSection")), 126000 },
		{ FName(TEXT("Part.NoseCone")), 88000 },
		{ FName(TEXT("Part.TailCone")), 74000 },
		{ FName(TEXT("Part.AccessHatch")), 41000 },
		{ FName(TEXT("Part.CanopyFrame")), 44000 },
		{ FName(TEXT("Part.Canopy")), 105000 },
		{ FName(TEXT("Part.HeatShieldTile")), 36000 },
		{ FName(TEXT("Part.GearOleoStrut")), 61000 },
		{ FName(TEXT("Part.GearWheel")), 44000 },
		{ FName(TEXT("Part.GearBrakeUnit")), 52000 },
		{ FName(TEXT("Part.GearRetractActuator")), 68000 },
		// Legs are assemblies, so they carry their contents' cost plus
		// the usual import premium over building them here.
		{ FName(TEXT("Part.NoseGearLeg")), 231000 },
		{ FName(TEXT("Part.MainGearLeg")), 299000 },
		{ FName(TEXT("Part.HullFrameSet")), 572000 },
		{ FName(TEXT("Part.HullSkinSet")), 1028000 },
		{ FName(TEXT("Part.CanopySet")), 259000 },
		{ FName(TEXT("Part.LandingSet")), 659000 },
		// Electronics.
		{ FName(TEXT("Part.CircuitBoard")), 31000 },
		{ FName(TEXT("Part.ControlComputer")), 95000 },
		{ FName(TEXT("Part.MemoryBank")), 52000 },
		{ FName(TEXT("Part.WiringLoom")), 23000 },
		{ FName(TEXT("Part.PowerBusBar")), 34000 },
		{ FName(TEXT("Part.ConnectorBlock")), 19000 },
		{ FName(TEXT("Part.SensorArray")), 63000 },
		{ FName(TEXT("Part.ProximitySensor")), 28000 },
		{ FName(TEXT("Part.ThermalSensor")), 30000 },
		{ FName(TEXT("Part.DisplayCluster")), 66000 },
		{ FName(TEXT("Part.SwitchPanel")), 37000 },
		{ FName(TEXT("Part.AntennaMast")), 33000 },
		{ FName(TEXT("Part.Transceiver")), 58000 },
		{ FName(TEXT("Part.AvionicsCoreSet")), 362000 },
		{ FName(TEXT("Part.HarnessLoomSet")), 307000 },
		{ FName(TEXT("Part.SensorSet")), 401000 },
		{ FName(TEXT("Part.CockpitPanelSet")), 370000 },
		// Power.
		{ FName(TEXT("Part.BatteryCell")), 29000 },
		{ FName(TEXT("Part.BatteryHousing")), 35000 },
		{ FName(TEXT("Part.PowerRegulator")), 37000 },
		{ FName(TEXT("Part.CapacitorBank")), 54000 },
		{ FName(TEXT("Part.ReactorCore")), 240000 },
		{ FName(TEXT("Part.CoreShielding")), 96000 },
		{ FName(TEXT("Part.CoolantPump")), 46000 },
		{ FName(TEXT("Part.CoolantLine")), 21000 },
		{ FName(TEXT("Part.RadiatorPanel")), 44000 },
		{ FName(TEXT("Part.InverterUnit")), 68000 },
		{ FName(TEXT("Part.DistributionNode")), 52000 },
		{ FName(TEXT("Part.ChargePort")), 26000 },
		{ FName(TEXT("Part.BatteryPackSet")), 367000 },
		{ FName(TEXT("Part.ReactorSet")), 484000 },
		{ FName(TEXT("Part.CoolingSet")), 296000 },
		{ FName(TEXT("Part.PowerBusSet")), 396000 },
		// Propulsion.
		{ FName(TEXT("Part.ThrusterNozzle")), 115000 },
		{ FName(TEXT("Part.CombustionChamber")), 137000 },
		{ FName(TEXT("Part.InjectorHead")), 89000 },
		{ FName(TEXT("Part.Turbopump")), 124000 },
		{ FName(TEXT("Part.FuelPump")), 47000 },
		{ FName(TEXT("Part.FuelLine")), 22000 },
		{ FName(TEXT("Part.FuelTank")), 78000 },
		{ FName(TEXT("Part.TankBaffle")), 24000 },
		{ FName(TEXT("Part.GimbalMount")), 56000 },
		{ FName(TEXT("Part.GimbalActuator")), 72000 },
		{ FName(TEXT("Part.IgnitionUnit")), 49000 },
		{ FName(TEXT("Part.RcsThruster")), 67000 },
		{ FName(TEXT("Part.ValveBlock")), 43000 },
		{ FName(TEXT("Part.EngineCoreSet")), 764000 },
		{ FName(TEXT("Part.FuelFeedSet")), 724000 },
		{ FName(TEXT("Part.TankSet")), 282000 },
		{ FName(TEXT("Part.GimbalSet")), 697000 },
		// Navigation.
		{ FName(TEXT("Part.Gyroscope")), 50000 },
		{ FName(TEXT("Part.AccelerometerPack")), 45000 },
		{ FName(TEXT("Part.StarTracker")), 98000 },
		{ FName(TEXT("Part.NavDish")), 68000 },
		{ FName(TEXT("Part.DishActuator")), 38000 },
		{ FName(TEXT("Part.RangingLaser")), 76000 },
		{ FName(TEXT("Part.BeaconLight")), 25000 },
		{ FName(TEXT("Part.AttitudeComputer")), 165000 },
		{ FName(TEXT("Part.FlightRecorder")), 86000 },
		{ FName(TEXT("Part.HorizonSensor")), 71000 },
		{ FName(TEXT("Part.Magnetometer")), 40000 },
		{ FName(TEXT("Part.Transponder")), 92000 },
		{ FName(TEXT("Part.InertialSet")), 364000 },
		{ FName(TEXT("Part.SkyTrackSet")), 354000 },
		{ FName(TEXT("Part.DishSet")), 231000 },
		{ FName(TEXT("Part.FlightComputerSet")), 384000 },
		// Interior.
		{ FName(TEXT("Part.SeatFrame")), 32000 },
		{ FName(TEXT("Part.SeatKit")), 45000 },
		{ FName(TEXT("Part.HarnessSet")), 23000 },
		{ FName(TEXT("Part.FloorMat")), 17000 },
		{ FName(TEXT("Part.WallLiner")), 28000 },
		{ FName(TEXT("Part.CeilingPanel")), 34000 },
		{ FName(TEXT("Part.StorageLocker")), 39000 },
		{ FName(TEXT("Part.LifeSupportUnit")), 84000 },
		{ FName(TEXT("Part.AirScrubber")), 57000 },
		{ FName(TEXT("Part.OxygenTank")), 61000 },
		{ FName(TEXT("Part.CabinLight")), 18000 },
		{ FName(TEXT("Part.FireSuppressor")), 44000 },
		{ FName(TEXT("Part.PressureDoor")), 92000 },
		{ FName(TEXT("Part.SeatingSet")), 224000 },
		{ FName(TEXT("Part.CabinTrimSet")), 240000 },
		{ FName(TEXT("Part.LifeSupportSet")), 358000 },
		{ FName(TEXT("Part.CabinFitSet")), 277000 },
		// Assembled components import too (owner 2026-08-26: parts are
		// BOUGHT until the machines are unlocked and bought - the whole
		// chain must run on imports; machines buy margin, not access).
		// PROVISIONAL: ~their part basket at import prices +15%.
		{ FName(TEXT("Component.Hull")), 2896000 },
		{ FName(TEXT("Component.Electronics")), 1656000 },
		{ FName(TEXT("Component.Power")), 1774000 },
		{ FName(TEXT("Component.Propulsion")), 2837000 },
		{ FName(TEXT("Component.Navigation")), 1533000 },
		{ FName(TEXT("Component.Interior")), 1264000 } };
		const int64* Price = Prices.Find(ItemId);
	return Price != nullptr ? *Price : 0;
}

int64 FLBSpacecraftItemCatalogue::GetOrderablePricePence(FName ItemId)
{
	const int64 Raw = GetRawItemPricePence(ItemId);
	return Raw > 0 ? Raw : GetItemImportPricePence(ItemId);
}

double FLBSpacecraftItemCatalogue::GetOrderLeadSeconds(int32 Count)
{
	return 30.0 + 2.0 * (FMath::Max(Count, 0) / 10);
}

FName FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(
	uint8 ComponentIndex)
{
	switch (static_cast<ELBSpacecraftComponent>(ComponentIndex))
	{
	case ELBSpacecraftComponent::Hull:
		return FName(TEXT("Component.Hull"));
	case ELBSpacecraftComponent::Electronics:
		return FName(TEXT("Component.Electronics"));
	case ELBSpacecraftComponent::Power:
		return FName(TEXT("Component.Power"));
	case ELBSpacecraftComponent::Propulsion:
		return FName(TEXT("Component.Propulsion"));
	case ELBSpacecraftComponent::Navigation:
		return FName(TEXT("Component.Navigation"));
	case ELBSpacecraftComponent::Interior:
		return FName(TEXT("Component.Interior"));
	default:
		return NAME_None;
	}
}

bool FLBSpacecraftItemCatalogue::ValidateItemTable(FString& OutReason)
{
	const TArray<FLBSpacecraftItemDefinition>& Table = GetItemTable();
	if (Table.Num() == 0)
	{
		OutReason = TEXT("ITEM TABLE IS EMPTY");
		return false;
	}
	TSet<FName> SeenIds;
	int32 CategoryCounts[4] = {0, 0, 0, 0};
	for (const FLBSpacecraftItemDefinition& Row : Table)
	{
		if (Row.ItemId.IsNone())
		{
			OutReason = TEXT("ITEM TABLE ROW HAS NO ID");
			return false;
		}
		if (SeenIds.Contains(Row.ItemId))
		{
			OutReason = FString::Printf(TEXT("DUPLICATE ITEM ID %s"),
				*Row.ItemId.ToString());
			return false;
		}
		SeenIds.Add(Row.ItemId);
		if (Row.DisplayName.IsEmpty())
		{
			OutReason = FString::Printf(TEXT("ITEM %s HAS NO DISPLAY NAME"),
				*Row.ItemId.ToString());
			return false;
		}
		if (Row.UnitVolume <= 0)
		{
			OutReason = FString::Printf(TEXT("ITEM %s HAS NON-POSITIVE VOLUME"),
				*Row.ItemId.ToString());
			return false;
		}
		CategoryCounts[static_cast<uint8>(Row.Category)]++;
	}
	for (int32 Category = 0; Category < 4; ++Category)
	{
		if (CategoryCounts[Category] == 0)
		{
			OutReason = TEXT("ITEM TABLE MISSING A CHAIN CATEGORY");
			return false;
		}
	}
	// The assembled-component rows must mirror the six-slot BOM exactly.
	for (uint8 Component = 0; Component < 6; ++Component)
	{
		const FLBSpacecraftItemDefinition* Row =
			FindItem(GetAssembledComponentItemId(Component));
		if (Row == nullptr
			|| Row->Category != ELBSpacecraftItemCategory::AssembledComponent)
		{
			OutReason = TEXT("ASSEMBLED COMPONENT ITEMS DO NOT MIRROR THE BOM");
			return false;
		}
	}
	if (CategoryCounts[static_cast<uint8>(
		ELBSpacecraftItemCategory::AssembledComponent)] != 6)
	{
		OutReason = TEXT("ASSEMBLED COMPONENT COUNT MUST BE EXACTLY SIX");
		return false;
	}
	return true;
}

ALBSpacecraftInventoryAuthority::ALBSpacecraftInventoryAuthority()
{
	PrimaryActorTick.bCanEverTick = false;
}

FLBSpacecraftInventoryStoreState* ALBSpacecraftInventoryAuthority::FindStore(
	FName StoreId)
{
	for (FLBSpacecraftInventoryStoreState& Store : Stores)
	{
		if (Store.StoreId == StoreId)
		{
			return &Store;
		}
	}
	return nullptr;
}

const FLBSpacecraftInventoryStoreState*
ALBSpacecraftInventoryAuthority::FindStore(FName StoreId) const
{
	for (const FLBSpacecraftInventoryStoreState& Store : Stores)
	{
		if (Store.StoreId == StoreId)
		{
			return &Store;
		}
	}
	return nullptr;
}

int32 ALBSpacecraftInventoryAuthority::UsedUnitsOf(
	const FLBSpacecraftInventoryStoreState& Store)
{
	int32 Used = 0;
	for (const FLBSpacecraftItemStack& Stack : Store.Stacks)
	{
		const FLBSpacecraftItemDefinition* Item =
			FLBSpacecraftItemCatalogue::FindItem(Stack.ItemId);
		Used += Stack.Count * (Item != nullptr ? Item->UnitVolume : 1);
	}
	return Used;
}

bool ALBSpacecraftInventoryAuthority::RegisterStore(FName StoreId,
	int32 CapacityUnits, FString& OutReason)
{
	if (StoreId.IsNone())
	{
		OutReason = TEXT("STORE REGISTRATION REQUIRES AN ID");
		return false;
	}
	if (CapacityUnits <= 0)
	{
		OutReason = TEXT("STORE CAPACITY MUST BE POSITIVE");
		return false;
	}
	if (FindStore(StoreId) != nullptr)
	{
		OutReason = FString::Printf(TEXT("STORE %s ALREADY EXISTS"),
			*StoreId.ToString());
		return false;
	}
	FLBSpacecraftInventoryStoreState Store;
	Store.StoreId = StoreId;
	Store.CapacityUnits = CapacityUnits;
	Stores.Add(Store);
	OutReason = FString::Printf(TEXT("STORE %s REGISTERED"),
		*StoreId.ToString());
	return true;
}

bool ALBSpacecraftInventoryAuthority::RemoveStore(FName StoreId,
	FString& OutReason)
{
	for (int32 Index = 0; Index < Stores.Num(); ++Index)
	{
		if (Stores[Index].StoreId != StoreId)
		{
			continue;
		}
		if (Stores[Index].Stacks.Num() > 0)
		{
			OutReason = FString::Printf(
				TEXT("STORE %s STILL HOLDS ITEMS - EMPTY IT FIRST"),
				*StoreId.ToString());
			return false;
		}
		Stores.RemoveAt(Index);
		OutReason = TEXT("STORE REMOVED");
		return true;
	}
	OutReason = FString::Printf(TEXT("UNKNOWN STORE %s"),
		*StoreId.ToString());
	return false;
}

bool ALBSpacecraftInventoryAuthority::Deposit(FName StoreId, FName ItemId,
	int32 Count, FString& OutReason)
{
	if (Count <= 0)
	{
		OutReason = TEXT("DEPOSIT COUNT MUST BE POSITIVE");
		return false;
	}
	FLBSpacecraftInventoryStoreState* Store = FindStore(StoreId);
	if (Store == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STORE %s"),
			*StoreId.ToString());
		return false;
	}
	const FLBSpacecraftItemDefinition* Item =
		FLBSpacecraftItemCatalogue::FindItem(ItemId);
	if (Item == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN ITEM %s"),
			*ItemId.ToString());
		return false;
	}
	const int32 NeededUnits = Count * Item->UnitVolume;
	if (UsedUnitsOf(*Store) + NeededUnits > Store->CapacityUnits)
	{
		OutReason = FString::Printf(
			TEXT("STORE %s CANNOT FIT %d x %s - DEPOSIT REFUSED WHOLE"),
			*StoreId.ToString(), Count, *ItemId.ToString());
		return false;
	}
	for (FLBSpacecraftItemStack& Stack : Store->Stacks)
	{
		if (Stack.ItemId == ItemId)
		{
			Stack.Count += Count;
			OutReason = TEXT("DEPOSITED");
			return true;
		}
	}
	FLBSpacecraftItemStack Stack;
	Stack.ItemId = ItemId;
	Stack.Count = Count;
	Store->Stacks.Add(Stack);
	OutReason = TEXT("DEPOSITED");
	return true;
}

bool ALBSpacecraftInventoryAuthority::Withdraw(FName StoreId, FName ItemId,
	int32 Count, FString& OutReason)
{
	if (Count <= 0)
	{
		OutReason = TEXT("WITHDRAW COUNT MUST BE POSITIVE");
		return false;
	}
	FLBSpacecraftInventoryStoreState* Store = FindStore(StoreId);
	if (Store == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STORE %s"),
			*StoreId.ToString());
		return false;
	}
	for (int32 Index = 0; Index < Store->Stacks.Num(); ++Index)
	{
		if (Store->Stacks[Index].ItemId != ItemId)
		{
			continue;
		}
		if (Store->Stacks[Index].Count < Count)
		{
			OutReason = FString::Printf(
				TEXT("STORE %s HOLDS %d x %s, NOT %d - WITHDRAW REFUSED"),
				*StoreId.ToString(), Store->Stacks[Index].Count,
				*ItemId.ToString(), Count);
			return false;
		}
		Store->Stacks[Index].Count -= Count;
		if (Store->Stacks[Index].Count == 0)
		{
			Store->Stacks.RemoveAt(Index);
		}
		OutReason = TEXT("WITHDRAWN");
		return true;
	}
	OutReason = FString::Printf(TEXT("STORE %s HOLDS NO %s"),
		*StoreId.ToString(), *ItemId.ToString());
	return false;
}

bool ALBSpacecraftInventoryAuthority::Transfer(FName FromStoreId,
	FName ToStoreId, FName ItemId, int32 Count, FString& OutReason)
{
	if (FromStoreId == ToStoreId)
	{
		OutReason = TEXT("TRANSFER REQUIRES TWO DIFFERENT STORES");
		return false;
	}
	// Validate BOTH sides before either mutates - the move is atomic.
	const FLBSpacecraftInventoryStoreState* From = FindStore(FromStoreId);
	const FLBSpacecraftInventoryStoreState* To = FindStore(ToStoreId);
	const FLBSpacecraftItemDefinition* Item =
		FLBSpacecraftItemCatalogue::FindItem(ItemId);
	if (From == nullptr || To == nullptr || Item == nullptr || Count <= 0)
	{
		OutReason = TEXT("TRANSFER PRECONDITIONS FAILED - NOTHING MOVED");
		return false;
	}
	int32 Held = 0;
	for (const FLBSpacecraftItemStack& Stack : From->Stacks)
	{
		if (Stack.ItemId == ItemId)
		{
			Held = Stack.Count;
		}
	}
	if (Held < Count)
	{
		OutReason = FString::Printf(
			TEXT("SOURCE HOLDS %d x %s, NOT %d - NOTHING MOVED"),
			Held, *ItemId.ToString(), Count);
		return false;
	}
	if (UsedUnitsOf(*To) + Count * Item->UnitVolume > To->CapacityUnits)
	{
		OutReason = FString::Printf(
			TEXT("DESTINATION %s CANNOT FIT %d x %s - NOTHING MOVED"),
			*ToStoreId.ToString(), Count, *ItemId.ToString());
		return false;
	}
	FString Inner;
	const bool bOut = Withdraw(FromStoreId, ItemId, Count, Inner);
	const bool bIn = bOut && Deposit(ToStoreId, ItemId, Count, Inner);
	checkf(bOut && bIn, TEXT("validated transfer must not fail"));
	OutReason = TEXT("TRANSFERRED");
	return true;
}

bool ALBSpacecraftInventoryAuthority::HasAnyStock() const
{
	for (const FLBSpacecraftInventoryStoreState& Store : Stores)
	{
		if (GetUsedUnits(Store.StoreId) > 0)
		{
			return true;
		}
	}
	return false;
}

int32 ALBSpacecraftInventoryAuthority::GetQuantity(FName StoreId,
	FName ItemId) const
{
	const FLBSpacecraftInventoryStoreState* Store = FindStore(StoreId);
	if (Store == nullptr)
	{
		return 0;
	}
	for (const FLBSpacecraftItemStack& Stack : Store->Stacks)
	{
		if (Stack.ItemId == ItemId)
		{
			return Stack.Count;
		}
	}
	return 0;
}

int32 ALBSpacecraftInventoryAuthority::GetUsedUnits(FName StoreId) const
{
	const FLBSpacecraftInventoryStoreState* Store = FindStore(StoreId);
	return Store != nullptr ? UsedUnitsOf(*Store) : 0;
}

int32 ALBSpacecraftInventoryAuthority::GetCapacityUnits(FName StoreId) const
{
	const FLBSpacecraftInventoryStoreState* Store = FindStore(StoreId);
	return Store != nullptr ? Store->CapacityUnits : 0;
}

TArray<FName> ALBSpacecraftInventoryAuthority::GetStoreIds() const
{
	TArray<FName> Ids;
	Ids.Reserve(Stores.Num());
	for (const FLBSpacecraftInventoryStoreState& Store : Stores)
	{
		Ids.Add(Store.StoreId);
	}
	return Ids;
}

int32 ALBSpacecraftInventoryAuthority::GetRoomForItems(FName StoreId,
	FName ItemId) const
{
	const FLBSpacecraftInventoryStoreState* Store = FindStore(StoreId);
	const FLBSpacecraftItemDefinition* Item =
		FLBSpacecraftItemCatalogue::FindItem(ItemId);
	if (Store == nullptr || Item == nullptr || Item->UnitVolume <= 0)
	{
		return 0;
	}
	const int32 FreeUnits = Store->CapacityUnits - UsedUnitsOf(*Store);
	return FMath::Max(FreeUnits, 0) / Item->UnitVolume;
}

bool ALBSpacecraftInventoryAuthority::SetStoreCapacity(FName StoreId,
	int32 CapacityUnits, FString& OutReason)
{
	if (CapacityUnits <= 0)
	{
		OutReason = TEXT("STORE CAPACITY MUST BE POSITIVE");
		return false;
	}
	FLBSpacecraftInventoryStoreState* Store = FindStore(StoreId);
	if (Store == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STORE %s"),
			*StoreId.ToString());
		return false;
	}
	const int32 Used = UsedUnitsOf(*Store);
	if (CapacityUnits < Used)
	{
		OutReason = FString::Printf(
			TEXT("STORE %s HOLDS %d UNITS - CANNOT SHRINK TO %d"),
			*StoreId.ToString(), Used, CapacityUnits);
		return false;
	}
	Store->CapacityUnits = CapacityUnits;
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftInventoryAuthority::HasStore(FName StoreId) const
{
	return FindStore(StoreId) != nullptr;
}

bool ALBSpacecraftInventoryAuthority::PlaceOrder(FName ItemId,
	int32 Count, FName StoreId, FName& OutOrderId, FString& OutReason)
{
	OutOrderId = NAME_None;
	if (Count <= 0)
	{
		OutReason = TEXT("ORDER COUNT MUST BE POSITIVE");
		return false;
	}
	if (FLBSpacecraftItemCatalogue::GetOrderablePricePence(ItemId) <= 0)
	{
		OutReason = FString::Printf(
			TEXT("%s IS NOT PURCHASABLE - NEITHER RAW NOR IMPORTABLE"),
			*ItemId.ToString());
		return false;
	}
	if (!HasStore(StoreId))
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STORE %s"),
			*StoreId.ToString());
		return false;
	}
	FLBSpacecraftResourceOrder Order;
	Order.OrderId = FName(*FString::Printf(TEXT("ORD-%04d"),
		NextOrderSequence++));
	Order.ItemId = ItemId;
	Order.Count = Count;
	Order.StoreId = StoreId;
	Order.ArrivesAtSeconds = OrderClockSeconds
		+ FLBSpacecraftItemCatalogue::GetOrderLeadSeconds(Count);
	Orders.Add(Order);
	OutOrderId = Order.OrderId;
	OutReason.Reset();
	return true;
}

void ALBSpacecraftInventoryAuthority::TickOrders(double DeltaSeconds)
{
	if (DeltaSeconds <= 0.0)
	{
		return;
	}
	OrderClockSeconds += DeltaSeconds;
	for (int32 Index = Orders.Num() - 1; Index >= 0; --Index)
	{
		if (Orders[Index].ArrivesAtSeconds > OrderClockSeconds)
		{
			continue;
		}
		FString Reason;
		// A delivery LANDS AS MUCH AS FITS and keeps the rest on the
		// lorry. It used to be all-or-nothing: a store without room for
		// the WHOLE order took none of it and retried forever, with the
		// player's money already spent. That made a big order strictly
		// worse than the same goods ordered in dribs - buying twenty
		// craft's worth of parts in one go delivered NOTHING and looked
		// like the game had eaten 579,200 cr. Every caller had to know
		// the dock's capacity and chunk by hand, and the one that did
		// not silently starved the line it was stocking.
		//
		// Bought goods still never vanish and never overfill a store:
		// what does not fit stays on the order and arrives as the
		// haulers drain the dock.
		const int32 Room = GetRoomForItems(Orders[Index].StoreId,
			Orders[Index].ItemId);
		if (Room <= 0)
		{
			continue;
		}
		const int32 Landing = FMath::Min(Room, Orders[Index].Count);
		if (!Deposit(Orders[Index].StoreId, Orders[Index].ItemId,
			Landing, Reason))
		{
			continue;
		}
		Orders[Index].Count -= Landing;
		if (Orders[Index].Count <= 0)
		{
			Orders.RemoveAt(Index);
		}
	}
}

FLBSpacecraftInventorySnapshot
ALBSpacecraftInventoryAuthority::CaptureSnapshot() const
{
	FLBSpacecraftInventorySnapshot Snapshot;
	Snapshot.Stores = Stores;
	Snapshot.Orders = Orders;
	Snapshot.OrderClockSeconds = OrderClockSeconds;
	return Snapshot;
}

bool ALBSpacecraftInventoryAuthority::ValidateSnapshot(
	const FLBSpacecraftInventorySnapshot& Snapshot, FString& OutReason)
{
	TSet<FName> SeenStores;
	for (const FLBSpacecraftInventoryStoreState& Store : Snapshot.Stores)
	{
		if (Store.StoreId.IsNone() || Store.CapacityUnits <= 0)
		{
			OutReason = TEXT("SNAPSHOT STORE IS MALFORMED");
			return false;
		}
		if (SeenStores.Contains(Store.StoreId))
		{
			OutReason = FString::Printf(TEXT("SNAPSHOT DUPLICATES STORE %s"),
				*Store.StoreId.ToString());
			return false;
		}
		SeenStores.Add(Store.StoreId);
		TSet<FName> SeenItems;
		int32 Used = 0;
		for (const FLBSpacecraftItemStack& Stack : Store.Stacks)
		{
			const FLBSpacecraftItemDefinition* Item =
				FLBSpacecraftItemCatalogue::FindItem(Stack.ItemId);
			if (Item == nullptr)
			{
				OutReason = FString::Printf(
					TEXT("SNAPSHOT STORE %s HOLDS UNKNOWN ITEM %s"),
					*Store.StoreId.ToString(), *Stack.ItemId.ToString());
				return false;
			}
			if (Stack.Count <= 0)
			{
				OutReason = FString::Printf(
					TEXT("SNAPSHOT STORE %s HAS A NON-POSITIVE STACK"),
					*Store.StoreId.ToString());
				return false;
			}
			if (SeenItems.Contains(Stack.ItemId))
			{
				OutReason = FString::Printf(
					TEXT("SNAPSHOT STORE %s DUPLICATES ITEM %s"),
					*Store.StoreId.ToString(), *Stack.ItemId.ToString());
				return false;
			}
			SeenItems.Add(Stack.ItemId);
			Used += Stack.Count * Item->UnitVolume;
		}
		if (Used > Store.CapacityUnits)
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT STORE %s EXCEEDS ITS CAPACITY"),
				*Store.StoreId.ToString());
			return false;
		}
	}
	if (Snapshot.OrderClockSeconds < 0.0)
	{
		OutReason = TEXT("SNAPSHOT ORDER CLOCK RUNS BACKWARDS");
		return false;
	}
	TSet<FName> OrderIds;
	for (const FLBSpacecraftResourceOrder& Order : Snapshot.Orders)
	{
		if (Order.OrderId.IsNone() || Order.Count <= 0
			|| FLBSpacecraftItemCatalogue::GetOrderablePricePence(
				Order.ItemId) <= 0)
		{
			OutReason = TEXT("SNAPSHOT ORDER IS MALFORMED");
			return false;
		}
		if (OrderIds.Contains(Order.OrderId))
		{
			OutReason = TEXT("SNAPSHOT DUPLICATES AN ORDER");
			return false;
		}
		OrderIds.Add(Order.OrderId);
	}
	OutReason = TEXT("SNAPSHOT VALID");
	return true;
}

bool ALBSpacecraftInventoryAuthority::RestoreSnapshot(
	const FLBSpacecraftInventorySnapshot& Snapshot, FString& OutReason)
{
	// Whole-snapshot validation BEFORE a single mutation - invalid data can
	// never partly apply (repo-wide save-restore law).
	if (!ValidateSnapshot(Snapshot, OutReason))
	{
		return false;
	}
	Stores = Snapshot.Stores;
	Orders = Snapshot.Orders;
	OrderClockSeconds = Snapshot.OrderClockSeconds;
	int32 MaxSequence = 0;
	for (const FLBSpacecraftResourceOrder& Order : Orders)
	{
		FString Suffix = Order.OrderId.ToString();
		int32 DashIndex = INDEX_NONE;
		if (Suffix.FindLastChar(TEXT('-'), DashIndex))
		{
			MaxSequence = FMath::Max(MaxSequence,
				FCString::Atoi(*Suffix.Mid(DashIndex + 1)));
		}
	}
	NextOrderSequence = MaxSequence + 1;
	OutReason = TEXT("INVENTORY RESTORED");
	return true;
}
