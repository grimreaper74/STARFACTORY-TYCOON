#include "LBSpacecraftCraftingAuthority.h"

namespace LBSpacecraftCraftingPrivate
{
	// Unity-build safety: helpers qualified by subject.
	FLBSpacecraftItemStack MakeCraftingStack(const TCHAR* ItemId, int32 Count)
	{
		FLBSpacecraftItemStack Stack;
		Stack.ItemId = FName(ItemId);
		Stack.Count = Count;
		return Stack;
	}

	FLBSpacecraftItemRecipe MakeCraftingRecipe(const TCHAR* Id,
		const TCHAR* Display, const TCHAR* StationClass,
		std::initializer_list<FLBSpacecraftItemStack> Inputs,
		std::initializer_list<FLBSpacecraftItemStack> Outputs,
		double CycleSeconds)
	{
		FLBSpacecraftItemRecipe Recipe;
		Recipe.RecipeId = FName(Id);
		Recipe.DisplayName = Display;
		Recipe.StationClassId = FName(StationClass);
		Recipe.Inputs = Inputs;
		Recipe.Outputs = Outputs;
		Recipe.CycleSeconds = CycleSeconds;
		return Recipe;
	}

	TArray<FLBSpacecraftItemRecipe> BuildPhase2RecipeTable()
	{
		auto S = &MakeCraftingStack;
		TArray<FLBSpacecraftItemRecipe> Table;
		// Material Processor: ores and feedstock into processed stock.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Steel"), TEXT("Smelt Steel"),
			TEXT("Smelter"),
			{S(TEXT("Raw.IronOre"), 2)}, {S(TEXT("Proc.Steel"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.TitaniumAlloy"),
			TEXT("Refine Titanium Alloy"), TEXT("Smelter"),
			{S(TEXT("Raw.TitaniumOre"), 2), S(TEXT("Raw.Chemicals"), 1)},
			{S(TEXT("Proc.TitaniumAlloy"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.LightAlloy"),
			TEXT("Blend Light Alloy"), TEXT("Smelter"),
			{S(TEXT("Raw.IronOre"), 1), S(TEXT("Raw.TitaniumOre"), 1)},
			{S(TEXT("Proc.LightAlloy"), 2)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CopperWire"),
			TEXT("Draw Copper Wire"), TEXT("Smelter"),
			{S(TEXT("Raw.CopperOre"), 1)},
			{S(TEXT("Proc.CopperWire"), 3)}, 6.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Composites"),
			TEXT("Cure Composites"), TEXT("Smelter"),
			{S(TEXT("Raw.Polymers"), 2), S(TEXT("Raw.Chemicals"), 1)},
			{S(TEXT("Proc.Composites"), 2)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FuelMix"),
			TEXT("Blend Fuel Mix"), TEXT("Smelter"),
			{S(TEXT("Raw.Chemicals"), 2)},
			{S(TEXT("Proc.FuelMix"), 2)}, 8.0));
		// Rolling Mill: stock shapes.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.PlateStock"),
			TEXT("Roll Plate Stock"), TEXT("RollingMill"),
			{S(TEXT("Proc.Steel"), 2)},
			{S(TEXT("Proc.PlateStock"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FrameStock"),
			TEXT("Roll Frame Stock"), TEXT("RollingMill"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Proc.FrameStock"), 1)}, 10.0));
		// Extra processed stock the hundred parts need.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CarbonPanel"),
			TEXT("Process Carbon Panel"), TEXT("Smelter"),
			{S(TEXT("Raw.Carbon"), 2)},
			{S(TEXT("Proc.CarbonPanel"), 2)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Fasteners"),
			TEXT("Roll Fasteners"), TEXT("RollingMill"),
			{S(TEXT("Proc.Steel"), 1)},
			{S(TEXT("Proc.Fasteners"), 1)}, 6.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Sealant"),
			TEXT("Process Sealant"), TEXT("Smelter"),
			{S(TEXT("Raw.Polymers"), 1), S(TEXT("Raw.Chemicals"), 1)},
			{S(TEXT("Proc.Sealant"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Coolant"),
			TEXT("Process Coolant"), TEXT("Smelter"),
			{S(TEXT("Raw.Chemicals"), 2)},
			{S(TEXT("Proc.Coolant"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CeramicTile"),
			TEXT("Process Ceramic Tile"), TEXT("Smelter"),
			{S(TEXT("Raw.Silicon"), 1), S(TEXT("Raw.Chemicals"), 1)},
			{S(TEXT("Proc.CeramicTile"), 2)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CanopyGlass"),
			TEXT("Process Canopy Glass"), TEXT("Smelter"),
			{S(TEXT("Raw.Silicon"), 2)},
			{S(TEXT("Proc.CanopyGlass"), 2)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.InsulationFelt"),
			TEXT("Process Insulation Felt"), TEXT("Smelter"),
			{S(TEXT("Raw.Polymers"), 2)},
			{S(TEXT("Proc.InsulationFelt"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CircuitSubstrate"),
			TEXT("Print Circuit Substrate"), TEXT("CircuitFab"),
			{S(TEXT("Raw.Silicon"), 1), S(TEXT("Proc.Composites"), 1)},
			{S(TEXT("Proc.CircuitSubstrate"), 1)}, 10.0));
		// Hull: 13 base parts, then 4 sets.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.KeelSpar"),
			TEXT("Fabricate Keel Spar"), TEXT("StructureFab"),
			{S(TEXT("Proc.FrameStock"), 2)},
			{S(TEXT("Part.KeelSpar"), 1)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FrameRib"),
			TEXT("Fabricate Frame Rib"), TEXT("StructureFab"),
			{S(TEXT("Proc.FrameStock"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.FrameRib"), 2)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.BulkheadPanel"),
			TEXT("Fabricate Bulkhead Panel"), TEXT("StructureFab"),
			{S(TEXT("Proc.PlateStock"), 1), S(TEXT("Proc.Composites"), 1)},
			{S(TEXT("Part.BulkheadPanel"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FloorPan"),
			TEXT("Fabricate Floor Pan"), TEXT("StructureFab"),
			{S(TEXT("Proc.PlateStock"), 2)},
			{S(TEXT("Part.FloorPan"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.HullSection"),
			TEXT("Fabricate Hull Section"), TEXT("StructureFab"),
			{S(TEXT("Proc.PlateStock"), 2), S(TEXT("Proc.FrameStock"), 1)},
			{S(TEXT("Part.HullSection"), 1)}, 18.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.NoseCone"),
			TEXT("Fabricate Nose Cone"), TEXT("StructureFab"),
			{S(TEXT("Proc.Composites"), 2), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.NoseCone"), 1)}, 16.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.TailCone"),
			TEXT("Fabricate Tail Cone"), TEXT("StructureFab"),
			{S(TEXT("Proc.Composites"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.TailCone"), 1)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.AccessHatch"),
			TEXT("Fabricate Access Hatch"), TEXT("StructureFab"),
			{S(TEXT("Proc.PlateStock"), 1), S(TEXT("Proc.Fasteners"), 1)},
			{S(TEXT("Part.AccessHatch"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CanopyFrame"),
			TEXT("Fabricate Canopy Frame"), TEXT("StructureFab"),
			{S(TEXT("Proc.LightAlloy"), 1), S(TEXT("Proc.Fasteners"), 1)},
			{S(TEXT("Part.CanopyFrame"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Canopy"),
			TEXT("Fabricate Canopy"), TEXT("StructureFab"),
			{S(TEXT("Proc.CanopyGlass"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.Canopy"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.HeatShieldTile"),
			TEXT("Fabricate Heat-Shield Tile"), TEXT("StructureFab"),
			{S(TEXT("Proc.CeramicTile"), 2)},
			{S(TEXT("Part.HeatShieldTile"), 2)}, 12.0));
		// THE UNDERCARRIAGE, made rather than imagined (owner
		// 2026-08-28). Four fabricated parts, then the two leg types
		// assembled from them - which is how an undercarriage is
		// actually built, and what keeps the landing set narrow.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.GearOleoStrut"),
			TEXT("Fabricate Oleo Strut"), TEXT("StructureFab"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Proc.Sealant"), 1)},
			{S(TEXT("Part.GearOleoStrut"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.GearWheel"),
			TEXT("Fabricate Gear Wheel"), TEXT("StructureFab"),
			{S(TEXT("Proc.Composites"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.GearWheel"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.GearBrakeUnit"),
			TEXT("Fabricate Brake Unit"), TEXT("StructureFab"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Proc.TitaniumAlloy"), 1)},
			{S(TEXT("Part.GearBrakeUnit"), 1)}, 11.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.GearRetractActuator"),
			TEXT("Fabricate Retract Actuator"), TEXT("StructureFab"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Proc.CopperWire"), 1)},
			{S(TEXT("Part.GearRetractActuator"), 1)}, 11.0));
		// The nose leg carries no brake: a nose wheel steers, it does
		// not stop the craft. That asymmetry is the whole reason these
		// are two part types rather than one repeated three times.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.NoseGearLeg"),
			TEXT("Build Nose Gear Leg"), TEXT("StructureFab"),
			{S(TEXT("Part.GearOleoStrut"), 1), S(TEXT("Part.GearWheel"), 1),
				S(TEXT("Part.GearRetractActuator"), 1)},
			{S(TEXT("Part.NoseGearLeg"), 1)}, 16.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.MainGearLeg"),
			TEXT("Build Main Gear Leg"), TEXT("StructureFab"),
			{S(TEXT("Part.GearOleoStrut"), 1), S(TEXT("Part.GearWheel"), 1),
				S(TEXT("Part.GearBrakeUnit"), 1),
				S(TEXT("Part.GearRetractActuator"), 1)},
			{S(TEXT("Part.MainGearLeg"), 1)}, 18.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.HullFrameSet"),
			TEXT("Build Hull Frame Set"), TEXT("StructureFab"),
			{S(TEXT("Part.KeelSpar"), 1), S(TEXT("Part.FrameRib"), 6),
				S(TEXT("Part.BulkheadPanel"), 3), S(TEXT("Part.FloorPan"), 1)},
			{S(TEXT("Part.HullFrameSet"), 1)}, 26.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.HullSkinSet"),
			TEXT("Build Hull Skin Set"), TEXT("StructureFab"),
			{S(TEXT("Part.HullSection"), 6), S(TEXT("Part.NoseCone"), 1),
				S(TEXT("Part.TailCone"), 1)},
			{S(TEXT("Part.HullSkinSet"), 1)}, 26.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CanopySet"),
			TEXT("Build Canopy Set"), TEXT("StructureFab"),
			{S(TEXT("Part.CanopyFrame"), 1), S(TEXT("Part.Canopy"), 1),
				S(TEXT("Part.AccessHatch"), 2)},
			{S(TEXT("Part.CanopySet"), 1)}, 20.0));
		// ONE nose leg and TWO mains - the tricycle, in the bill of
		// materials as well as on the ship.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.LandingSet"),
			TEXT("Build Landing Set"), TEXT("StructureFab"),
			{S(TEXT("Part.NoseGearLeg"), 1), S(TEXT("Part.MainGearLeg"), 2),
				S(TEXT("Part.HeatShieldTile"), 8)},
			{S(TEXT("Part.LandingSet"), 1)}, 22.0));
		// Electronics: 13 base parts, then 4 sets.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CircuitBoard"),
			TEXT("Print Circuit Board"), TEXT("CircuitFab"),
			{S(TEXT("Proc.CircuitSubstrate"), 1),
				S(TEXT("Proc.CopperWire"), 1)},
			{S(TEXT("Part.CircuitBoard"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.ControlComputer"),
			TEXT("Assemble Control Computer"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.CircuitBoard"), 2), S(TEXT("Part.WiringLoom"), 1)},
			{S(TEXT("Part.ControlComputer"), 1)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.MemoryBank"),
			TEXT("Print Memory Bank"), TEXT("CircuitFab"),
			{S(TEXT("Proc.CircuitSubstrate"), 1), S(TEXT("Raw.Silicon"), 1)},
			{S(TEXT("Part.MemoryBank"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.WiringLoom"),
			TEXT("Print Wiring Loom"), TEXT("CircuitFab"),
			{S(TEXT("Proc.CopperWire"), 2)},
			{S(TEXT("Part.WiringLoom"), 1)}, 6.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.PowerBusBar"),
			TEXT("Print Power Bus Bar"), TEXT("CircuitFab"),
			{S(TEXT("Proc.CopperWire"), 2), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.PowerBusBar"), 1)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.ConnectorBlock"),
			TEXT("Print Connector Block"), TEXT("CircuitFab"),
			{S(TEXT("Proc.CopperWire"), 1), S(TEXT("Raw.Polymers"), 1)},
			{S(TEXT("Part.ConnectorBlock"), 2)}, 6.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.SensorArray"),
			TEXT("Assemble Sensor Array"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.SensorArray"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.ProximitySensor"),
			TEXT("Assemble Proximity Sensor"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Proc.CopperWire"), 1)},
			{S(TEXT("Part.ProximitySensor"), 2)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.ThermalSensor"),
			TEXT("Assemble Thermal Sensor"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Proc.CeramicTile"), 1)},
			{S(TEXT("Part.ThermalSensor"), 2)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.DisplayCluster"),
			TEXT("Assemble Display Cluster"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Proc.CanopyGlass"), 1)},
			{S(TEXT("Part.DisplayCluster"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.SwitchPanel"),
			TEXT("Assemble Switch Panel"), TEXT("ElectronicsStation"),
			{S(TEXT("Proc.LightAlloy"), 1), S(TEXT("Part.ConnectorBlock"), 1)},
			{S(TEXT("Part.SwitchPanel"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.AntennaMast"),
			TEXT("Assemble Antenna Mast"), TEXT("ElectronicsStation"),
			{S(TEXT("Proc.LightAlloy"), 1), S(TEXT("Proc.CopperWire"), 1)},
			{S(TEXT("Part.AntennaMast"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Transceiver"),
			TEXT("Assemble Transceiver"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Part.WiringLoom"), 1)},
			{S(TEXT("Part.Transceiver"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.AvionicsCoreSet"),
			TEXT("Build Avionics Core Set"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.ControlComputer"), 1), S(TEXT("Part.MemoryBank"), 2),
				S(TEXT("Part.CircuitBoard"), 4)},
			{S(TEXT("Part.AvionicsCoreSet"), 1)}, 24.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.HarnessLoomSet"),
			TEXT("Build Harness Loom Set"), TEXT("CircuitFab"),
			{S(TEXT("Part.WiringLoom"), 4), S(TEXT("Part.PowerBusBar"), 2),
				S(TEXT("Part.ConnectorBlock"), 6)},
			{S(TEXT("Part.HarnessLoomSet"), 1)}, 20.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.SensorSet"),
			TEXT("Build Sensor Set"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.SensorArray"), 2),
				S(TEXT("Part.ProximitySensor"), 4),
				S(TEXT("Part.ThermalSensor"), 4)},
			{S(TEXT("Part.SensorSet"), 1)}, 22.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CockpitPanelSet"),
			TEXT("Build Cockpit Panel Set"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.DisplayCluster"), 2), S(TEXT("Part.SwitchPanel"), 2),
				S(TEXT("Part.Transceiver"), 1), S(TEXT("Part.AntennaMast"), 2)},
			{S(TEXT("Part.CockpitPanelSet"), 1)}, 24.0));
		// Power: 12 base parts, then 4 sets.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.BatteryCell"),
			TEXT("Build Battery Cell"), TEXT("PowerCellPlant"),
			{S(TEXT("Raw.Chemicals"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.BatteryCell"), 2)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.BatteryHousing"),
			TEXT("Build Battery Housing"), TEXT("PowerCellPlant"),
			{S(TEXT("Proc.PlateStock"), 1), S(TEXT("Proc.InsulationFelt"), 1)},
			{S(TEXT("Part.BatteryHousing"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.PowerRegulator"),
			TEXT("Build Power Regulator"), TEXT("PowerCellPlant"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Proc.CopperWire"), 1)},
			{S(TEXT("Part.PowerRegulator"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CapacitorBank"),
			TEXT("Build Capacitor Bank"), TEXT("PowerCellPlant"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Proc.CopperWire"), 2)},
			{S(TEXT("Part.CapacitorBank"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.ReactorCore"),
			TEXT("Build Reactor Core"), TEXT("PowerCellPlant"),
			{S(TEXT("Raw.FusionCellPrecursor"), 1),
				S(TEXT("Proc.TitaniumAlloy"), 1)},
			{S(TEXT("Part.ReactorCore"), 1)}, 24.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CoreShielding"),
			TEXT("Build Core Shielding"), TEXT("PowerCellPlant"),
			{S(TEXT("Proc.CeramicTile"), 2), S(TEXT("Proc.TitaniumAlloy"), 1)},
			{S(TEXT("Part.CoreShielding"), 1)}, 18.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CoolantPump"),
			TEXT("Build Coolant Pump"), TEXT("PowerCellPlant"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Proc.Coolant"), 1)},
			{S(TEXT("Part.CoolantPump"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CoolantLine"),
			TEXT("Build Coolant Line"), TEXT("PowerCellPlant"),
			{S(TEXT("Proc.Coolant"), 1), S(TEXT("Raw.Polymers"), 1)},
			{S(TEXT("Part.CoolantLine"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.RadiatorPanel"),
			TEXT("Build Radiator Panel"), TEXT("PowerCellPlant"),
			{S(TEXT("Proc.LightAlloy"), 2)},
			{S(TEXT("Part.RadiatorPanel"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.InverterUnit"),
			TEXT("Build Inverter Unit"), TEXT("PowerCellPlant"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Part.PowerBusBar"), 1)},
			{S(TEXT("Part.InverterUnit"), 1)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.DistributionNode"),
			TEXT("Build Distribution Node"), TEXT("PowerCellPlant"),
			{S(TEXT("Part.PowerBusBar"), 1), S(TEXT("Part.ConnectorBlock"), 2)},
			{S(TEXT("Part.DistributionNode"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.ChargePort"),
			TEXT("Build Charge Port"), TEXT("PowerCellPlant"),
			{S(TEXT("Proc.CopperWire"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.ChargePort"), 1)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.BatteryPackSet"),
			TEXT("Build Battery Pack Set"), TEXT("PowerCellPlant"),
			{S(TEXT("Part.BatteryCell"), 8), S(TEXT("Part.BatteryHousing"), 2),
				S(TEXT("Part.ChargePort"), 1)},
			{S(TEXT("Part.BatteryPackSet"), 1)}, 24.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.ReactorSet"),
			TEXT("Build Reactor Set"), TEXT("PowerCellPlant"),
			{S(TEXT("Part.ReactorCore"), 1), S(TEXT("Part.CoreShielding"), 2)},
			{S(TEXT("Part.ReactorSet"), 1)}, 28.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CoolingSet"),
			TEXT("Build Cooling Set"), TEXT("PowerCellPlant"),
			{S(TEXT("Part.CoolantPump"), 2), S(TEXT("Part.CoolantLine"), 4),
				S(TEXT("Part.RadiatorPanel"), 2)},
			{S(TEXT("Part.CoolingSet"), 1)}, 20.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.PowerBusSet"),
			TEXT("Build Power Bus Set"), TEXT("PowerCellPlant"),
			{S(TEXT("Part.PowerRegulator"), 2),
				S(TEXT("Part.CapacitorBank"), 2), S(TEXT("Part.InverterUnit"), 1),
				S(TEXT("Part.DistributionNode"), 2)},
			{S(TEXT("Part.PowerBusSet"), 1)}, 24.0));
		// Propulsion: 13 base parts, then 4 sets.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.ThrusterNozzle"),
			TEXT("Machine Thruster Nozzle"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.TitaniumAlloy"), 2)},
			{S(TEXT("Part.ThrusterNozzle"), 1)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CombustionChamber"),
			TEXT("Machine Combustion Chamber"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.TitaniumAlloy"), 1), S(TEXT("Proc.Steel"), 1)},
			{S(TEXT("Part.CombustionChamber"), 1)}, 16.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.InjectorHead"),
			TEXT("Machine Injector Head"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.TitaniumAlloy"), 1), S(TEXT("Proc.Fasteners"), 1)},
			{S(TEXT("Part.InjectorHead"), 1)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Turbopump"),
			TEXT("Machine Turbopump"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.TitaniumAlloy"), 1), S(TEXT("Proc.Steel"), 2)},
			{S(TEXT("Part.Turbopump"), 1)}, 18.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FuelPump"),
			TEXT("Machine Fuel Pump"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.FuelPump"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FuelLine"),
			TEXT("Machine Fuel Line"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Proc.Sealant"), 1)},
			{S(TEXT("Part.FuelLine"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FuelTank"),
			TEXT("Machine Fuel Tank"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.PlateStock"), 2), S(TEXT("Proc.Sealant"), 1)},
			{S(TEXT("Part.FuelTank"), 1)}, 16.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.TankBaffle"),
			TEXT("Machine Tank Baffle"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.PlateStock"), 1)},
			{S(TEXT("Part.TankBaffle"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.GimbalMount"),
			TEXT("Machine Gimbal Mount"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.Steel"), 2)},
			{S(TEXT("Part.GimbalMount"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.GimbalActuator"),
			TEXT("Machine Gimbal Actuator"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Part.CircuitBoard"), 1)},
			{S(TEXT("Part.GimbalActuator"), 1)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.IgnitionUnit"),
			TEXT("Machine Ignition Unit"), TEXT("PropulsionStation"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Proc.CopperWire"), 1)},
			{S(TEXT("Part.IgnitionUnit"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.RcsThruster"),
			TEXT("Machine RCS Thruster"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.LightAlloy"), 1), S(TEXT("Proc.TitaniumAlloy"), 1)},
			{S(TEXT("Part.RcsThruster"), 2)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.ValveBlock"),
			TEXT("Machine Valve Block"), TEXT("PropulsionStation"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Proc.Sealant"), 1)},
			{S(TEXT("Part.ValveBlock"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.EngineCoreSet"),
			TEXT("Build Engine Core Set"), TEXT("PropulsionStation"),
			{S(TEXT("Part.CombustionChamber"), 2),
				S(TEXT("Part.InjectorHead"), 2),
				S(TEXT("Part.ThrusterNozzle"), 2)},
			{S(TEXT("Part.EngineCoreSet"), 1)}, 30.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FuelFeedSet"),
			TEXT("Build Fuel Feed Set"), TEXT("PropulsionStation"),
			{S(TEXT("Part.Turbopump"), 2), S(TEXT("Part.FuelPump"), 2),
				S(TEXT("Part.FuelLine"), 6), S(TEXT("Part.ValveBlock"), 4)},
			{S(TEXT("Part.FuelFeedSet"), 1)}, 26.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.TankSet"),
			TEXT("Build Tank Set"), TEXT("PropulsionStation"),
			{S(TEXT("Part.FuelTank"), 2), S(TEXT("Part.TankBaffle"), 4)},
			{S(TEXT("Part.TankSet"), 1)}, 22.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.GimbalSet"),
			TEXT("Build Gimbal Set"), TEXT("PropulsionStation"),
			{S(TEXT("Part.GimbalMount"), 2), S(TEXT("Part.GimbalActuator"), 2),
				S(TEXT("Part.IgnitionUnit"), 2), S(TEXT("Part.RcsThruster"), 4)},
			{S(TEXT("Part.GimbalSet"), 1)}, 26.0));
		// Navigation: 12 base parts, then 4 sets.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Gyroscope"),
			TEXT("Assemble Gyroscope"), TEXT("ElectronicsStation"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Part.CircuitBoard"), 1)},
			{S(TEXT("Part.Gyroscope"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.AccelerometerPack"),
			TEXT("Assemble Accelerometer Pack"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.AccelerometerPack"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.StarTracker"),
			TEXT("Assemble Star Tracker"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.SensorArray"), 1), S(TEXT("Proc.CanopyGlass"), 1)},
			{S(TEXT("Part.StarTracker"), 1)}, 16.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.NavDish"),
			TEXT("Assemble Nav Dish"), TEXT("ElectronicsStation"),
			{S(TEXT("Proc.LightAlloy"), 1), S(TEXT("Part.CircuitBoard"), 1)},
			{S(TEXT("Part.NavDish"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.DishActuator"),
			TEXT("Assemble Dish Actuator"), TEXT("ElectronicsStation"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Part.ConnectorBlock"), 1)},
			{S(TEXT("Part.DishActuator"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.RangingLaser"),
			TEXT("Assemble Ranging Laser"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Proc.CanopyGlass"), 1)},
			{S(TEXT("Part.RangingLaser"), 1)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.BeaconLight"),
			TEXT("Assemble Beacon Light"), TEXT("ElectronicsStation"),
			{S(TEXT("Proc.CanopyGlass"), 1), S(TEXT("Proc.CopperWire"), 1)},
			{S(TEXT("Part.BeaconLight"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.AttitudeComputer"),
			TEXT("Assemble Attitude Computer"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.ControlComputer"), 1), S(TEXT("Part.Gyroscope"), 1)},
			{S(TEXT("Part.AttitudeComputer"), 1)}, 18.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FlightRecorder"),
			TEXT("Assemble Flight Recorder"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.MemoryBank"), 1), S(TEXT("Proc.TitaniumAlloy"), 1)},
			{S(TEXT("Part.FlightRecorder"), 1)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.HorizonSensor"),
			TEXT("Assemble Horizon Sensor"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.SensorArray"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.HorizonSensor"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Magnetometer"),
			TEXT("Assemble Magnetometer"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.CircuitBoard"), 1), S(TEXT("Proc.CopperWire"), 1)},
			{S(TEXT("Part.Magnetometer"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Transponder"),
			TEXT("Assemble Transponder"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.Transceiver"), 1), S(TEXT("Part.CircuitBoard"), 1)},
			{S(TEXT("Part.Transponder"), 1)}, 14.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.InertialSet"),
			TEXT("Build Inertial Set"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.Gyroscope"), 3),
				S(TEXT("Part.AccelerometerPack"), 3),
				S(TEXT("Part.Magnetometer"), 1)},
			{S(TEXT("Part.InertialSet"), 1)}, 22.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.SkyTrackSet"),
			TEXT("Build Sky-Track Set"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.StarTracker"), 1), S(TEXT("Part.HorizonSensor"), 2),
				S(TEXT("Part.RangingLaser"), 1)},
			{S(TEXT("Part.SkyTrackSet"), 1)}, 26.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.DishSet"),
			TEXT("Build Dish Set"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.NavDish"), 1), S(TEXT("Part.DishActuator"), 1),
				S(TEXT("Part.BeaconLight"), 4)},
			{S(TEXT("Part.DishSet"), 1)}, 20.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FlightComputerSet"),
			TEXT("Build Flight Computer Set"), TEXT("ElectronicsStation"),
			{S(TEXT("Part.AttitudeComputer"), 1),
				S(TEXT("Part.FlightRecorder"), 1), S(TEXT("Part.Transponder"), 1)},
			{S(TEXT("Part.FlightComputerSet"), 1)}, 28.0));
		// Interior: 13 base parts, then 4 sets.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.SeatFrame"),
			TEXT("Fit Seat Frame"), TEXT("FitOutFab"),
			{S(TEXT("Proc.LightAlloy"), 1), S(TEXT("Proc.Fasteners"), 1)},
			{S(TEXT("Part.SeatFrame"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.SeatKit"),
			TEXT("Fit Seat Kit"), TEXT("FitOutFab"),
			{S(TEXT("Raw.Polymers"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.SeatKit"), 1)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.HarnessSet"),
			TEXT("Fit Harness Set"), TEXT("FitOutFab"),
			{S(TEXT("Raw.Polymers"), 2)},
			{S(TEXT("Part.HarnessSet"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FloorMat"),
			TEXT("Fit Floor Mat"), TEXT("FitOutFab"),
			{S(TEXT("Proc.InsulationFelt"), 1), S(TEXT("Raw.Polymers"), 1)},
			{S(TEXT("Part.FloorMat"), 2)}, 6.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.WallLiner"),
			TEXT("Fit Wall Liner"), TEXT("FitOutFab"),
			{S(TEXT("Proc.InsulationFelt"), 1), S(TEXT("Proc.CarbonPanel"), 1)},
			{S(TEXT("Part.WallLiner"), 2)}, 8.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CeilingPanel"),
			TEXT("Fit Ceiling Panel"), TEXT("FitOutFab"),
			{S(TEXT("Proc.CarbonPanel"), 1), S(TEXT("Proc.LightAlloy"), 1)},
			{S(TEXT("Part.CeilingPanel"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.StorageLocker"),
			TEXT("Fit Storage Locker"), TEXT("FitOutFab"),
			{S(TEXT("Proc.PlateStock"), 1), S(TEXT("Proc.Fasteners"), 1)},
			{S(TEXT("Part.StorageLocker"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.LifeSupportUnit"),
			TEXT("Fit Life-Support Unit"), TEXT("FitOutFab"),
			{S(TEXT("Proc.Composites"), 1), S(TEXT("Part.CircuitBoard"), 1),
				S(TEXT("Raw.Chemicals"), 1)},
			{S(TEXT("Part.LifeSupportUnit"), 1)}, 16.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.AirScrubber"),
			TEXT("Fit Air Scrubber"), TEXT("FitOutFab"),
			{S(TEXT("Proc.Composites"), 1), S(TEXT("Raw.Chemicals"), 1)},
			{S(TEXT("Part.AirScrubber"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.OxygenTank"),
			TEXT("Fit Oxygen Tank"), TEXT("FitOutFab"),
			{S(TEXT("Proc.PlateStock"), 1), S(TEXT("Proc.Sealant"), 1)},
			{S(TEXT("Part.OxygenTank"), 1)}, 12.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CabinLight"),
			TEXT("Fit Cabin Light"), TEXT("FitOutFab"),
			{S(TEXT("Proc.CanopyGlass"), 1), S(TEXT("Proc.CopperWire"), 1)},
			{S(TEXT("Part.CabinLight"), 2)}, 6.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.FireSuppressor"),
			TEXT("Fit Fire Suppressor"), TEXT("FitOutFab"),
			{S(TEXT("Proc.Steel"), 1), S(TEXT("Raw.Chemicals"), 1)},
			{S(TEXT("Part.FireSuppressor"), 1)}, 10.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.PressureDoor"),
			TEXT("Fit Pressure Door"), TEXT("FitOutFab"),
			{S(TEXT("Proc.PlateStock"), 2), S(TEXT("Proc.Sealant"), 1)},
			{S(TEXT("Part.PressureDoor"), 1)}, 16.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.SeatingSet"),
			TEXT("Build Seating Set"), TEXT("FitOutFab"),
			{S(TEXT("Part.SeatFrame"), 2), S(TEXT("Part.SeatKit"), 2),
				S(TEXT("Part.HarnessSet"), 2)},
			{S(TEXT("Part.SeatingSet"), 1)}, 20.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CabinTrimSet"),
			TEXT("Build Cabin Trim Set"), TEXT("FitOutFab"),
			{S(TEXT("Part.FloorMat"), 2), S(TEXT("Part.WallLiner"), 4),
				S(TEXT("Part.CeilingPanel"), 2)},
			{S(TEXT("Part.CabinTrimSet"), 1)}, 20.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.LifeSupportSet"),
			TEXT("Build Life-Support Set"), TEXT("FitOutFab"),
			{S(TEXT("Part.LifeSupportUnit"), 1),
				S(TEXT("Part.AirScrubber"), 2), S(TEXT("Part.OxygenTank"), 2)},
			{S(TEXT("Part.LifeSupportSet"), 1)}, 26.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.CabinFitSet"),
			TEXT("Build Cabin Fit Set"), TEXT("FitOutFab"),
			{S(TEXT("Part.StorageLocker"), 1), S(TEXT("Part.CabinLight"), 4),
				S(TEXT("Part.FireSuppressor"), 1),
				S(TEXT("Part.PressureDoor"), 1)},
			{S(TEXT("Part.CabinFitSet"), 1)}, 24.0));
		// Sub-Assembly Robot: four sets into each component.
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Component.Hull"),
			TEXT("Join Hull Component"), TEXT("SubAssemblyRobot"),
			{S(TEXT("Part.HullFrameSet"), 1), S(TEXT("Part.HullSkinSet"), 1),
				S(TEXT("Part.CanopySet"), 1), S(TEXT("Part.LandingSet"), 1)},
			{S(TEXT("Component.Hull"), 1)}, 24.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Component.Electronics"),
			TEXT("Join Electronics Component"), TEXT("SubAssemblyRobot"),
			{S(TEXT("Part.AvionicsCoreSet"), 1),
				S(TEXT("Part.HarnessLoomSet"), 1), S(TEXT("Part.SensorSet"), 1),
				S(TEXT("Part.CockpitPanelSet"), 1)},
			{S(TEXT("Component.Electronics"), 1)}, 20.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Component.Power"),
			TEXT("Join Power Component"), TEXT("SubAssemblyRobot"),
			{S(TEXT("Part.BatteryPackSet"), 1), S(TEXT("Part.ReactorSet"), 1),
				S(TEXT("Part.CoolingSet"), 1), S(TEXT("Part.PowerBusSet"), 1)},
			{S(TEXT("Component.Power"), 1)}, 20.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Component.Propulsion"),
			TEXT("Join Propulsion Component"), TEXT("SubAssemblyRobot"),
			{S(TEXT("Part.EngineCoreSet"), 1), S(TEXT("Part.FuelFeedSet"), 1),
				S(TEXT("Part.TankSet"), 1), S(TEXT("Part.GimbalSet"), 1)},
			{S(TEXT("Component.Propulsion"), 1)}, 24.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Component.Navigation"),
			TEXT("Join Navigation Component"), TEXT("SubAssemblyRobot"),
			{S(TEXT("Part.InertialSet"), 1), S(TEXT("Part.SkyTrackSet"), 1),
				S(TEXT("Part.DishSet"), 1), S(TEXT("Part.FlightComputerSet"), 1)},
			{S(TEXT("Component.Navigation"), 1)}, 20.0));
		Table.Add(MakeCraftingRecipe(TEXT("Recipe.Component.Interior"),
			TEXT("Join Interior Component"), TEXT("SubAssemblyRobot"),
			{S(TEXT("Part.SeatingSet"), 1), S(TEXT("Part.CabinTrimSet"), 1),
				S(TEXT("Part.LifeSupportSet"), 1), S(TEXT("Part.CabinFitSet"), 1)},
			{S(TEXT("Component.Interior"), 1)}, 20.0));
		return Table;
	}
}

const TArray<FLBSpacecraftItemRecipe>&
FLBSpacecraftRecipeCatalogue::GetRecipeTable()
{
	static const TArray<FLBSpacecraftItemRecipe> Table =
		LBSpacecraftCraftingPrivate::BuildPhase2RecipeTable();
	return Table;
}

const FLBSpacecraftItemRecipe* FLBSpacecraftRecipeCatalogue::FindRecipe(
	FName RecipeId)
{
	for (const FLBSpacecraftItemRecipe& Recipe : GetRecipeTable())
	{
		if (Recipe.RecipeId == RecipeId)
		{
			return &Recipe;
		}
	}
	return nullptr;
}

TArray<FName> FLBSpacecraftRecipeCatalogue::GetRecipesForStationClass(
	FName StationClassId)
{
	TArray<FName> Result;
	for (const FLBSpacecraftItemRecipe& Recipe : GetRecipeTable())
	{
		if (Recipe.StationClassId == StationClassId)
		{
			Result.Add(Recipe.RecipeId);
		}
	}
	return Result;
}

bool FLBSpacecraftRecipeCatalogue::ValidateRecipeTable(FString& OutReason)
{
	const TArray<FLBSpacecraftItemRecipe>& Table = GetRecipeTable();
	if (Table.Num() == 0)
	{
		OutReason = TEXT("RECIPE TABLE IS EMPTY");
		return false;
	}
	TSet<FName> SeenIds;
	TSet<FName> ProducedItems;
	for (const FLBSpacecraftItemRecipe& Recipe : Table)
	{
		if (Recipe.RecipeId.IsNone() || Recipe.DisplayName.IsEmpty()
			|| Recipe.StationClassId.IsNone())
		{
			OutReason = TEXT("RECIPE ROW IS MALFORMED");
			return false;
		}
		if (SeenIds.Contains(Recipe.RecipeId))
		{
			OutReason = FString::Printf(TEXT("DUPLICATE RECIPE ID %s"),
				*Recipe.RecipeId.ToString());
			return false;
		}
		SeenIds.Add(Recipe.RecipeId);
		if (Recipe.CycleSeconds <= 0.0)
		{
			OutReason = FString::Printf(
				TEXT("RECIPE %s HAS A NON-POSITIVE CYCLE"),
				*Recipe.RecipeId.ToString());
			return false;
		}
		if (Recipe.Inputs.Num() == 0 || Recipe.Outputs.Num() == 0)
		{
			OutReason = FString::Printf(
				TEXT("RECIPE %s MUST CONSUME AND PRODUCE"),
				*Recipe.RecipeId.ToString());
			return false;
		}
		TSet<FName> InputIds;
		for (const FLBSpacecraftItemStack& Input : Recipe.Inputs)
		{
			if (FLBSpacecraftItemCatalogue::FindItem(Input.ItemId) == nullptr
				|| Input.Count <= 0)
			{
				OutReason = FString::Printf(
					TEXT("RECIPE %s HAS AN INVALID INPUT"),
					*Recipe.RecipeId.ToString());
				return false;
			}
			InputIds.Add(Input.ItemId);
		}
		for (const FLBSpacecraftItemStack& Output : Recipe.Outputs)
		{
			const FLBSpacecraftItemDefinition* Item =
				FLBSpacecraftItemCatalogue::FindItem(Output.ItemId);
			if (Item == nullptr || Output.Count <= 0)
			{
				OutReason = FString::Printf(
					TEXT("RECIPE %s HAS AN INVALID OUTPUT"),
					*Recipe.RecipeId.ToString());
				return false;
			}
			if (Item->Category == ELBSpacecraftItemCategory::Raw)
			{
				OutReason = FString::Printf(
					TEXT("RECIPE %s CRAFTS A RAW ITEM - RAW ARRIVES BY INTAKE"),
					*Recipe.RecipeId.ToString());
				return false;
			}
			if (InputIds.Contains(Output.ItemId))
			{
				OutReason = FString::Printf(
					TEXT("RECIPE %s USES AN ITEM AS INPUT AND OUTPUT"),
					*Recipe.RecipeId.ToString());
				return false;
			}
			ProducedItems.Add(Output.ItemId);
		}
	}
	// Chain completeness: every non-raw item in the catalogue is producible.
	for (const FLBSpacecraftItemDefinition& Item :
		FLBSpacecraftItemCatalogue::GetItemTable())
	{
		if (Item.Category != ELBSpacecraftItemCategory::Raw
			&& !ProducedItems.Contains(Item.ItemId))
		{
			OutReason = FString::Printf(
				TEXT("ITEM %s HAS NO PRODUCING RECIPE - CHAIN IS BROKEN"),
				*Item.ItemId.ToString());
			return false;
		}
	}
	OutReason = TEXT("RECIPE TABLE VALID");
	return true;
}

bool FLBSpacecraftRecipeCatalogue::PlanBuild(
	const TMap<FName, int32>& Targets,
	TArray<FLBSpacecraftPlannedRun>& OutRuns,
	TMap<FName, int32>& OutRawNeeds, FString& OutReason)
{
	OutRuns.Reset();
	OutRawNeeds.Reset();
	TMap<FName, int32> Need = Targets;
	// Expansion: pick any outstanding non-raw need, plan the recipe that
	// makes it (cycles rounded up to whole runs), zero that need and add
	// the recipe's inputs as new needs. An item a LATER-planned recipe
	// consumes gets planned again deeper down; reverse execution runs
	// the deeper copy first, so its output exists for the shallow one.
	int32 Guard = 0;
	bool bExpanded = true;
	while (bExpanded && Guard++ < 2000)
	{
		bExpanded = false;
		for (const TPair<FName, int32>& Want : Need)
		{
			if (Want.Value <= 0)
			{
				continue;
			}
			const FLBSpacecraftItemDefinition* Item =
				FLBSpacecraftItemCatalogue::FindItem(Want.Key);
			if (Item != nullptr
				&& Item->Category == ELBSpacecraftItemCategory::Raw)
			{
				continue; // raws are bought, not planned
			}
			const FLBSpacecraftItemRecipe* Maker = nullptr;
			int32 PerCycle = 0;
			for (const FLBSpacecraftItemRecipe& Recipe : GetRecipeTable())
			{
				for (const FLBSpacecraftItemStack& Out : Recipe.Outputs)
				{
					if (Out.ItemId == Want.Key && Out.Count > 0)
					{
						Maker = &Recipe;
						PerCycle = Out.Count;
					}
				}
			}
			if (Maker == nullptr)
			{
				OutReason = FString::Printf(
					TEXT("NOTHING MAKES %s AND IT IS NOT RAW - ")
					TEXT("THE CHAIN IS OPEN"), *Want.Key.ToString());
				return false;
			}
			FLBSpacecraftPlannedRun Run;
			Run.RecipeId = Maker->RecipeId;
			Run.StationClassId = Maker->StationClassId;
			Run.Cycles = FMath::DivideAndRoundUp(Want.Value, PerCycle);
			OutRuns.Add(Run);
			Need[Want.Key] = 0;
			for (const FLBSpacecraftItemStack& In : Maker->Inputs)
			{
				Need.FindOrAdd(In.ItemId) += In.Count * Run.Cycles;
			}
			bExpanded = true;
			break; // Need was mutated; restart the scan.
		}
	}
	if (Guard >= 2000)
	{
		OutReason = TEXT("BUILD PLAN DID NOT TERMINATE - THE RECIPE ")
			TEXT("CHAIN IS CYCLIC OR ABSURDLY DEEP");
		return false;
	}
	for (const TPair<FName, int32>& Want : Need)
	{
		const FLBSpacecraftItemDefinition* Item =
			FLBSpacecraftItemCatalogue::FindItem(Want.Key);
		if (Item != nullptr
			&& Item->Category == ELBSpacecraftItemCategory::Raw
			&& Want.Value > 0)
		{
			OutRawNeeds.Add(Want.Key, Want.Value);
		}
	}
	OutReason = FString::Printf(TEXT("PLANNED %d RUNS, %d RAW KINDS"),
		OutRuns.Num(), OutRawNeeds.Num());
	return true;
}

ALBSpacecraftCraftingAuthority::ALBSpacecraftCraftingAuthority()
{
	PrimaryActorTick.bCanEverTick = false;
}

const FLBSpacecraftStationRecipeSelection*
ALBSpacecraftCraftingAuthority::FindSelection(FName StationId) const
{
	for (const FLBSpacecraftStationRecipeSelection& Selection : Selections)
	{
		if (Selection.StationId == StationId)
		{
			return &Selection;
		}
	}
	return nullptr;
}

FLBSpacecraftStationRecipeSelection*
ALBSpacecraftCraftingAuthority::FindSelectionMutable(FName StationId)
{
	for (FLBSpacecraftStationRecipeSelection& Selection : Selections)
	{
		if (Selection.StationId == StationId)
		{
			return &Selection;
		}
	}
	return nullptr;
}

bool ALBSpacecraftCraftingAuthority::SelectRecipe(FName StationId,
	FName StationClassId, FName RecipeId, FString& OutReason)
{
	if (StationId.IsNone())
	{
		OutReason = TEXT("RECIPE SELECTION REQUIRES A STATION ID");
		return false;
	}
	const FLBSpacecraftItemRecipe* Recipe =
		FLBSpacecraftRecipeCatalogue::FindRecipe(RecipeId);
	if (Recipe == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN RECIPE %s"),
			*RecipeId.ToString());
		return false;
	}
	if (Recipe->StationClassId != StationClassId)
	{
		OutReason = FString::Printf(
			TEXT("RECIPE %s BELONGS TO %s, NOT %s - SELECTION REFUSED"),
			*RecipeId.ToString(), *Recipe->StationClassId.ToString(),
			*StationClassId.ToString());
		return false;
	}
	for (FLBSpacecraftStationRecipeSelection& Selection : Selections)
	{
		if (Selection.StationId == StationId)
		{
			Selection.StationClassId = StationClassId;
			Selection.RecipeId = RecipeId;
			// A different recipe starts from zero - no smuggled progress.
			Selection.CycleElapsedSeconds = 0.0;
			OutReason = TEXT("RECIPE RESELECTED");
			return true;
		}
	}
	FLBSpacecraftStationRecipeSelection Selection;
	Selection.StationId = StationId;
	Selection.StationClassId = StationClassId;
	Selection.RecipeId = RecipeId;
	Selections.Add(Selection);
	OutReason = TEXT("RECIPE SELECTED");
	return true;
}

bool ALBSpacecraftCraftingAuthority::ClearSelection(FName StationId,
	FString& OutReason)
{
	for (int32 Index = 0; Index < Selections.Num(); ++Index)
	{
		if (Selections[Index].StationId == StationId)
		{
			Selections.RemoveAt(Index);
			OutReason = TEXT("SELECTION CLEARED");
			return true;
		}
	}
	OutReason = FString::Printf(TEXT("STATION %s HAS NO SELECTION"),
		*StationId.ToString());
	return false;
}

const FLBSpacecraftItemRecipe*
ALBSpacecraftCraftingAuthority::GetSelectedRecipe(FName StationId) const
{
	const FLBSpacecraftStationRecipeSelection* Selection =
		FindSelection(StationId);
	return Selection != nullptr
		? FLBSpacecraftRecipeCatalogue::FindRecipe(Selection->RecipeId)
		: nullptr;
}

bool ALBSpacecraftCraftingAuthority::ExecuteCraftCycle(FName StationId,
	ALBSpacecraftInventoryAuthority& Inventory, FName InputStoreId,
	FName OutputStoreId, FString& OutReason)
{
	const FLBSpacecraftItemRecipe* Recipe = GetSelectedRecipe(StationId);
	if (Recipe == nullptr)
	{
		OutReason = FString::Printf(
			TEXT("STATION %s HAS NO ACTIVE RECIPE"), *StationId.ToString());
		return false;
	}
	// Sub-assembly rule (owner 2026-08-26): outputs land in the
	// machine's OWN buffer, not a store - the heavy drone does the
	// hauling. A full buffer stalls the machine, in plain words.
	FLBSpacecraftStationRecipeSelection* Selection =
		FindSelectionMutable(StationId);
	checkf(Selection != nullptr, TEXT("recipe implies selection"));
	// Made to order (owner 2026-08-26): no open order, no cycle.
	if (Selection->OrderRemaining <= 0)
	{
		OutReason = FString::Printf(
			TEXT("STATION %s HAS NO OPEN ORDER - PLACE AN ORDER"),
			*StationId.ToString());
		return false;
	}
	int32 OutputCount = 0;
	for (const FLBSpacecraftItemStack& Output : Recipe->Outputs)
	{
		OutputCount += Output.Count;
	}
	if (Selection->BufferItems.Num() + OutputCount > BufferCapacity)
	{
		OutReason = FString::Printf(
			TEXT("STATION %s OUTPUT BUFFER FULL (%d/%d) - AWAITING ")
			TEXT("DRONE PICKUP - CRAFT REFUSED WHOLE"),
			*StationId.ToString(), Selection->BufferItems.Num(),
			BufferCapacity);
		return false;
	}
	if (!ExchangeWouldValidate(*Recipe, Inventory, InputStoreId,
		OutputStoreId, OutReason, /*bOutputsToBuffer=*/true))
	{
		return false;
	}
	FString Inner;
	for (const FLBSpacecraftItemStack& Input : Recipe->Inputs)
	{
		const bool bWithdrawn = Inventory.Withdraw(InputStoreId,
			Input.ItemId, Input.Count, Inner);
		checkf(bWithdrawn, TEXT("validated craft input must withdraw"));
	}
	for (const FLBSpacecraftItemStack& Output : Recipe->Outputs)
	{
		for (int32 Unit = 0; Unit < Output.Count; ++Unit)
		{
			Selection->BufferItems.Add(Output.ItemId);
		}
	}
	--Selection->OrderRemaining;
	OutReason = FString::Printf(TEXT("CRAFTED %s (%d TO GO)"),
		*Recipe->RecipeId.ToString(), Selection->OrderRemaining);
	return true;
}

bool ALBSpacecraftCraftingAuthority::ExchangeWouldValidate(
	const FLBSpacecraftItemRecipe& Recipe,
	const ALBSpacecraftInventoryAuthority& Inventory, FName InputStoreId,
	FName OutputStoreId, FString& OutReason, bool bOutputsToBuffer)
{
	if (!Inventory.HasStore(InputStoreId)
		|| (!bOutputsToBuffer && !Inventory.HasStore(OutputStoreId)))
	{
		OutReason = TEXT("CRAFT CYCLE NEEDS REGISTERED STORES");
		return false;
	}
	// Validate the WHOLE exchange before anything moves.
	int32 FreedUnits = 0;
	for (const FLBSpacecraftItemStack& Input : Recipe.Inputs)
	{
		if (Inventory.GetQuantity(InputStoreId, Input.ItemId) < Input.Count)
		{
			OutReason = FString::Printf(
				TEXT("STORE %s LACKS %d x %s - CRAFT REFUSED WHOLE"),
				*InputStoreId.ToString(), Input.Count,
				*Input.ItemId.ToString());
			return false;
		}
		const FLBSpacecraftItemDefinition* Item =
			FLBSpacecraftItemCatalogue::FindItem(Input.ItemId);
		FreedUnits += Input.Count * (Item != nullptr ? Item->UnitVolume : 1);
	}
	int32 NeededUnits = 0;
	for (const FLBSpacecraftItemStack& Output : Recipe.Outputs)
	{
		const FLBSpacecraftItemDefinition* Item =
			FLBSpacecraftItemCatalogue::FindItem(Output.ItemId);
		NeededUnits += Output.Count * (Item != nullptr ? Item->UnitVolume : 1);
	}
	// Buffered outputs skip the store-capacity gate (the machine's
	// own buffer gate ran first); store crafting keeps it.
	if (!bOutputsToBuffer)
	{
		// Same-store crafting credits the volume the inputs free up.
		const int32 AvailableUnits =
			Inventory.GetCapacityUnits(OutputStoreId)
			- Inventory.GetUsedUnits(OutputStoreId)
			+ (InputStoreId == OutputStoreId ? FreedUnits : 0);
		if (NeededUnits > AvailableUnits)
		{
			OutReason = FString::Printf(
				TEXT("STORE %s CANNOT HOLD THE OUTPUTS - ")
				TEXT("CRAFT REFUSED WHOLE"),
				*OutputStoreId.ToString());
			return false;
		}
	}
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftCraftingAuthority::TickCrafting(FName StationId,
	double DeltaSeconds, ALBSpacecraftInventoryAuthority& Inventory,
	FName InputStoreId, FName OutputStoreId, int32& OutCompletedCycles,
	FString& OutReason)
{
	OutCompletedCycles = 0;
	if (DeltaSeconds <= 0.0)
	{
		OutReason = TEXT("TICK NEEDS POSITIVE SIM TIME");
		return false;
	}
	FLBSpacecraftStationRecipeSelection* Selection =
		FindSelectionMutable(StationId);
	const FLBSpacecraftItemRecipe* Recipe =
		Selection != nullptr
			? FLBSpacecraftRecipeCatalogue::FindRecipe(Selection->RecipeId)
			: nullptr;
	if (Selection == nullptr || Recipe == nullptr)
	{
		OutReason = FString::Printf(
			TEXT("STATION %s HAS NO ACTIVE RECIPE"), *StationId.ToString());
		return false;
	}
	if (!Inventory.HasStore(InputStoreId)
		|| !Inventory.HasStore(OutputStoreId))
	{
		OutReason = TEXT("CRAFT CYCLE NEEDS REGISTERED STORES");
		return false;
	}
	// Made to order (owner 2026-08-26): no open order, no accrual -
	// the machine idles with a named state, banking nothing.
	if (Selection->OrderRemaining <= 0)
	{
		OutReason = FString::Printf(
			TEXT("IDLE: STATION %s HAS NO OPEN ORDER"),
			*StationId.ToString());
		return true;
	}
	// Time accrues only while the exchange would validate: a starved or
	// blocked station stalls honestly instead of banking progress.
	FString StallReason;
	if (!ExchangeWouldValidate(*Recipe, Inventory, InputStoreId,
		OutputStoreId, StallReason, /*bOutputsToBuffer=*/true))
	{
		OutReason = FString::Printf(TEXT("STALLED: %s"), *StallReason);
		return true;
	}
	Selection->CycleElapsedSeconds += DeltaSeconds;
	while (Selection->CycleElapsedSeconds >= Recipe->CycleSeconds)
	{
		FString CraftReason;
		if (!ExecuteCraftCycle(StationId, Inventory, InputStoreId,
			OutputStoreId, CraftReason))
		{
			// The next cycle cannot pay: hold at the boundary and stall.
			Selection->CycleElapsedSeconds = Recipe->CycleSeconds;
			OutReason = FString::Printf(TEXT("STALLED: %s"), *CraftReason);
			return true;
		}
		Selection->CycleElapsedSeconds -= Recipe->CycleSeconds;
		++OutCompletedCycles;
	}
	OutReason = OutCompletedCycles > 0
		? FString::Printf(TEXT("COMPLETED %d CYCLES"), OutCompletedCycles)
		: TEXT("IN CYCLE");
	return true;
}

double ALBSpacecraftCraftingAuthority::GetCycleElapsedSeconds(
	FName StationId) const
{
	const FLBSpacecraftStationRecipeSelection* Selection =
		FindSelection(StationId);
	return Selection != nullptr ? Selection->CycleElapsedSeconds : 0.0;
}

FLBSpacecraftCraftingSnapshot
ALBSpacecraftCraftingAuthority::CaptureSnapshot() const
{
	FLBSpacecraftCraftingSnapshot Snapshot;
	Snapshot.Selections = Selections;
	return Snapshot;
}

bool ALBSpacecraftCraftingAuthority::AddOrder(FName StationId,
	int32 Count, FString& OutReason)
{
	if (Count <= 0)
	{
		OutReason = TEXT("ORDER COUNT MUST BE POSITIVE");
		return false;
	}
	FLBSpacecraftStationRecipeSelection* Selection =
		FindSelectionMutable(StationId);
	if (Selection == nullptr)
	{
		OutReason = FString::Printf(
			TEXT("STATION %s HAS NO ACTIVE RECIPE - PICK ONE FIRST"),
			*StationId.ToString());
		return false;
	}
	Selection->OrderRemaining += Count;
	OutReason = FString::Printf(TEXT("ORDER OPEN: %d CYCLES"),
		Selection->OrderRemaining);
	return true;
}

int32 ALBSpacecraftCraftingAuthority::GetOrderRemaining(
	FName StationId) const
{
	for (const FLBSpacecraftStationRecipeSelection& Selection : Selections)
	{
		if (Selection.StationId == StationId)
		{
			return Selection.OrderRemaining;
		}
	}
	return 0;
}

FName ALBSpacecraftCraftingAuthority::GetStationOutputItem(
	FName StationId) const
{
	// Display seam: what this machine MAKES (first buffered item when
	// one waits, else the selected recipe's first output). Never
	// invents - no selection means no item.
	const FLBSpacecraftStationRecipeSelection* Selection =
		FindSelection(StationId);
	if (Selection == nullptr)
	{
		return NAME_None;
	}
	if (Selection->BufferItems.Num() > 0)
	{
		return Selection->BufferItems[0];
	}
	const FLBSpacecraftItemRecipe* Recipe =
		FLBSpacecraftRecipeCatalogue::FindRecipe(Selection->RecipeId);
	if (Recipe != nullptr && Recipe->Outputs.Num() > 0)
	{
		return Recipe->Outputs[0].ItemId;
	}
	return NAME_None;
}

int32 ALBSpacecraftCraftingAuthority::GetBufferCount(FName StationId) const
{
	for (const FLBSpacecraftStationRecipeSelection& Selection : Selections)
	{
		if (Selection.StationId == StationId)
		{
			return Selection.BufferItems.Num();
		}
	}
	return 0;
}

FName ALBSpacecraftCraftingAuthority::FindStationWithBufferedOutput() const
{
	FName Fullest = NAME_None;
	int32 Best = 0;
	for (const FLBSpacecraftStationRecipeSelection& Selection : Selections)
	{
		if (Selection.BufferItems.Num() > Best)
		{
			Best = Selection.BufferItems.Num();
			Fullest = Selection.StationId;
		}
	}
	return Fullest;
}

bool ALBSpacecraftCraftingAuthority::TransferBufferToStore(FName StationId,
	ALBSpacecraftInventoryAuthority& Inventory, FName StoreId,
	int32 MaxCount, int32& OutMoved, FString& OutReason)
{
	OutMoved = 0;
	FLBSpacecraftStationRecipeSelection* Selection =
		FindSelectionMutable(StationId);
	if (Selection == nullptr)
	{
		OutReason = FString::Printf(
			TEXT("STATION %s HAS NO SUB-ASSEMBLY BUFFER"),
			*StationId.ToString());
		return false;
	}
	if (!Inventory.HasStore(StoreId))
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STORE %s"),
			*StoreId.ToString());
		return false;
	}
	// Front-of-queue order; an item the store cannot take stays put
	// (partial haul is physically honest - the drone leaves the rest).
	while (OutMoved < MaxCount && Selection->BufferItems.Num() > 0)
	{
		FString Inner;
		if (!Inventory.Deposit(StoreId, Selection->BufferItems[0], 1,
			Inner))
		{
			OutReason = FString::Printf(
				TEXT("STORE %s FULL - %d HAULED, BUFFER KEEPS THE REST"),
				*StoreId.ToString(), OutMoved);
			return OutMoved > 0;
		}
		Selection->BufferItems.RemoveAt(0);
		++OutMoved;
	}
	OutReason = FString::Printf(TEXT("HAULED %d FROM %s"), OutMoved,
		*StationId.ToString());
	return true;
}

bool ALBSpacecraftCraftingAuthority::ValidateSnapshot(
	const FLBSpacecraftCraftingSnapshot& Snapshot, FString& OutReason)
{
	TSet<FName> SeenStations;
	for (const FLBSpacecraftStationRecipeSelection& Selection :
		Snapshot.Selections)
	{
		if (Selection.StationId.IsNone())
		{
			OutReason = TEXT("SNAPSHOT SELECTION HAS NO STATION");
			return false;
		}
		if (SeenStations.Contains(Selection.StationId))
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT DUPLICATES STATION %s"),
				*Selection.StationId.ToString());
			return false;
		}
		SeenStations.Add(Selection.StationId);
		const FLBSpacecraftItemRecipe* Recipe =
			FLBSpacecraftRecipeCatalogue::FindRecipe(Selection.RecipeId);
		if (Recipe == nullptr
			|| Recipe->StationClassId != Selection.StationClassId)
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT SELECTION %s NAMES AN INVALID RECIPE"),
				*Selection.StationId.ToString());
			return false;
		}
		if (Selection.CycleElapsedSeconds < 0.0
			|| Selection.CycleElapsedSeconds > Recipe->CycleSeconds)
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT SELECTION %s HAS AN IMPOSSIBLE CYCLE CLOCK"),
				*Selection.StationId.ToString());
			return false;
		}
		if (Selection.OrderRemaining < 0)
		{
			OutReason = FString::Printf(
				TEXT("SNAPSHOT ORDER AT %s IS NEGATIVE"),
				*Selection.StationId.ToString());
			return false;
		}
		for (const FName& Buffered : Selection.BufferItems)
		{
			if (FLBSpacecraftItemCatalogue::FindItem(Buffered) == nullptr)
			{
				OutReason = FString::Printf(
					TEXT("SNAPSHOT BUFFER AT %s HOLDS UNKNOWN ITEM %s"),
					*Selection.StationId.ToString(),
					*Buffered.ToString());
				return false;
			}
		}
	}
	OutReason = TEXT("SNAPSHOT VALID");
	return true;
}

bool ALBSpacecraftCraftingAuthority::RestoreSnapshot(
	const FLBSpacecraftCraftingSnapshot& Snapshot, FString& OutReason)
{
	// Whole-snapshot validation BEFORE a single mutation (repo law).
	if (!ValidateSnapshot(Snapshot, OutReason))
	{
		return false;
	}
	Selections = Snapshot.Selections;
	OutReason = TEXT("CRAFTING RESTORED");
	return true;
}
