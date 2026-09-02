#include "LBSpacecraftWIPPresentationActor.h"
#include "LBSpacecraftPalette.h"

#include "LBSpacecraftCraftingAuthority.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftProductionTypes.h"
#include "LBSpacecraftDroneFleetAuthority.h"
#include "LBSpacecraftPlayerPawn.h"
#include "GameFramework/PlayerController.h"
#include "Components/AudioComponent.h"
#include "HAL/IConsoleManager.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Kismet/GameplayStatics.h"
#include "Components/TextRenderComponent.h"
#include "Sound/SoundBase.h"
#include "LBSpacecraftTransportAuthority.h"
#include "LBSpacecraftTrackAuthority.h"
#include "Components/DecalComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SplineComponent.h"
#include "Components/SplineMeshComponent.h"
#include "Components/RectLightComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "MaterialDomain.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

namespace LBSpacecraftWIPPresentationPrivate
{
	// TAKE OUT THE MESHY-SOURCED MODELS, BLOCKOUT UNTIL DESIGN REPLACES
	// THEM (owner, 2026-08-30). Every resolver below that loads content
	// from the Meshy intake pipeline (identified by folder against the
	// project's own SourceAssets/Candidate/Spacecraft/*_MeshyIntake_v001
	// manifests, not guessed) checks this FIRST and returns nullptr,
	// which is not new behaviour - every one of these call sites
	// already falls back to a logged placeholder block when its mesh
	// is unavailable, because that has always been this file's honest
	// answer to a missing asset. This just makes it unavailable on
	// purpose.
	//
	// NOT gated: the Scout01_v002 six-part craft (Claude Design,
	// 2026-08-30), the hall shell and gantry portal pieces (built
	// procedurally in Blender by this project, not commissioned), and
	// the bought background kit under /Game/Meshes/ (a different,
	// legitimate source kept deliberately apart from the site's own
	// art - see LoadKit below).
	//
	// FLIP THIS BACK to false once Design has replaced what the
	// punch-list in Docs/ names, and only then - this is a switch, not
	// a redesign, and it must not quietly become the permanent state.
	constexpr bool bBlockoutMeshyContent = true;

	// Unity-build safety: helpers qualified by subject.
	const TCHAR* SpacecraftCubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
	const TCHAR* SpacecraftShapeMaterialPath =
		TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
	// Spline mesh components need bUsedWithSplineMeshes on their
	// material, which the engine BasicShapeMaterial lacks - in the
	// first packaged run every belt segment cost a game-thread SMU
	// fixup, and a Shipping build would render default material.
	// Project-owned equivalent (same "Color" parameter), created by
	// Scripts/fix_cooked_material_usage_v001.py, flag baked in.
	const TCHAR* SpacecraftSplineShapeMaterialPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
		"/Materials/M_LB_ShapeSpline_v001.M_LB_ShapeSpline_v001");
	const TCHAR* SpacecraftCraftMeshPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
		"/Meshes/SM_LB_SC_Scout01_v001.SM_LB_SC_Scout01_v001");
	const TCHAR* SpacecraftChassisMeshPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
		"/Meshes/SM_LB_SC_Scout01_Chassis_v001_LOD0"
		".SM_LB_SC_Scout01_Chassis_v001_LOD0");
	const TCHAR* SpacecraftAirframeMeshPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
		"/Meshes/SM_LB_SC_Scout01_AirframeOpen_v001"
		".SM_LB_SC_Scout01_AirframeOpen_v001");
	const TCHAR* SpacecraftFittedMeshPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
		"/Meshes/SM_LB_SC_Scout01_Fitted_v001_LOD0"
		".SM_LB_SC_Scout01_Fitted_v001_LOD0");
	const TCHAR* SpacecraftHullMaterialPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
		"/Materials/M_LB_SC_Scout01_Hull.M_LB_SC_Scout01_Hull");
	// Cargo-01 build forms (owner's morning drop 2026-08-26).
	const TCHAR* SpacecraftCargoChassisMeshPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
		"/Meshes/SM_LB_SC_Cargo01_Chassis_v001_LOD0"
		".SM_LB_SC_Cargo01_Chassis_v001_LOD0");
	const TCHAR* SpacecraftCargoAirframeMeshPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
		"/Meshes/SM_LB_SC_Cargo01_AirframeOpen_v001"
		".SM_LB_SC_Cargo01_AirframeOpen_v001");
	const TCHAR* SpacecraftCargoFittedMeshPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
		"/Meshes/SM_LB_SC_Cargo01_Fitted_v001_LOD0"
		".SM_LB_SC_Cargo01_Fitted_v001_LOD0");
	const TCHAR* SpacecraftCargoCraftMeshPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
		"/Meshes/SM_LB_SC_Cargo01_v001_LOD0"
		".SM_LB_SC_Cargo01_v001_LOD0");
	const FName SpacecraftCargoRecipeId(TEXT("CARGO-01"));
	const FName SpacecraftScoutRecipeId(TEXT("SCOUT-01"));

	// THE SIX-ASSEMBLY SCOUT (v003, Claude Design latest 2026-08-30).
	// Interchange nests each import in <SourceBasename>/StaticMeshes/<ObjectName>
	// rather than laying it flat - this is the NESTED path, verified by importing
	// and listing the destination directory rather than guessed.
	const TCHAR* ScoutV2HullPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001/"
		"Meshes/Scout01_v003/scout01_v003/StaticMeshes/Hull.Hull");
	const TCHAR* ScoutV2PropulsionPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001/"
		"Meshes/Scout01_v003/scout01_v003/StaticMeshes/Propulsion"
		".Propulsion");
	const TCHAR* ScoutV2PowerPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001/"
		"Meshes/Scout01_v003/scout01_v003/StaticMeshes/Power.Power");
	const TCHAR* ScoutV2ElectronicsPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001/"
		"Meshes/Scout01_v003/scout01_v003/StaticMeshes/Electronics"
		".Electronics");
	const TCHAR* ScoutV2NavigationPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001/"
		"Meshes/Scout01_v003/scout01_v003/StaticMeshes/Navigation"
		".Navigation");
	const TCHAR* ScoutV2InteriorPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftFactory_v001/"
		"Meshes/Scout01_v003/scout01_v003/StaticMeshes/Interior"
		".Interior");

	const TCHAR* SpacecraftCargoHullMaterialPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
		"/Materials/MI_LB_SC_Cargo01_Hull.MI_LB_SC_Cargo01_Hull");
	const TCHAR* SpacecraftPaintMaterialPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
		"/Materials/M_LB_ShipPaint_v001.M_LB_ShipPaint_v001");
	const FLinearColor SpacecraftMistColour(0.7f, 0.75f, 0.82f);
	// The blue afterburner plume authored for the test bay; fallback is a
	// plain blue shape when the content is absent.
	const TCHAR* SpacecraftPlumeMaterialPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001"
		"/Materials/M_LB_SC_ThrustPlume.M_LB_SC_ThrustPlume");
	// Polish pass: a soft additive radial flame (script-built v005) that
	// stops the plumes reading as flat solid wedges at cinematic
	// distance. Preferred when present; the plume above is the fallback.
	const TCHAR* SpacecraftSoftFlameMaterialPath = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
		"/Materials/M_LB_Flame_v001.M_LB_Flame_v001");
	const TCHAR* SpacecraftConePath =
		TEXT("/Engine/BasicShapes/Cone.Cone");
	const FLinearColor SpacecraftFlameBlue(0.36f, 0.62f, 1.0f);

	constexpr float SpacecraftStationBlockHeightCm = 350.f;
	// Where the belly sits when the craft is DOWN on its own landing
	// gear - the gear is 110 cm, so this is the height its wheels give.
	constexpr float SpacecraftLandedBellyCm = 110.f;
	// How much of a station stop is spent rising, and the same again
	// lowering. 0.12 each end leaves three quarters of the stop with
	// the craft up and the crew working, which is what a stop is for.
	constexpr float SpacecraftLiftRiseFraction = 0.12f;
	constexpr float SpacecraftCrateHalfHeightCm = 100.f;

	const TCHAR* SpacecraftCylinderPath =
		TEXT("/Engine/BasicShapes/Cylinder.Cylinder");
	constexpr float SpacecraftAccentPulsePeriod = 2.4f;
	// Provisional indicator language only (blue/white) - no brand colours.
	const FLinearColor SpacecraftAccentBright(0.55f, 0.75f, 1.0f);
	const FLinearColor SpacecraftAccentDim(0.10f, 0.12f, 0.16f);

	// Runway language: white paint, red strobes (aviation warning red -
	// functional lighting, not a brand colour).
	const FLinearColor SpacecraftRunwayPaint(0.85f, 0.86f, 0.88f);
	const FLinearColor SpacecraftTubeRib(0.66f, 0.67f, 0.70f);
	const FLinearColor SpacecraftChaseDim(0.06f, 0.10f, 0.16f);
	const FLinearColor SpacecraftChaseBright(0.55f, 0.78f, 1.f);
	const FLinearColor SpacecraftDroneBody(0.13f, 0.14f, 0.16f);
	// v002: v001 was harmonic partials only, which loops cleanly but
	// sounds like an organ rather than moving air. v002 builds the
	// noise in the frequency domain so it loops too. v001 stays
	// imported as evidence; nothing points at it.
	const TCHAR* SpacecraftRotorSoundPath = TEXT(
		"/Game/LineBoss/Audio/SFX/S_LB_DroneRotor_v002"
		".S_LB_DroneRotor_v002");

	// One drone's rotor voice. Named for its subject because this
	// module builds with unity: an unqualified MakeRotorAudio would
	// eventually collide with another file's helper (as IsFiniteVector
	// already did once).
	UAudioComponent* SpacecraftMakeRotorAudio(AActor* Owner,
		USceneComponent* Parent, FName Key, USoundBase* Loop,
		float RadiusCm, float FalloffCm)
	{
		if (Owner == nullptr || Parent == nullptr || Loop == nullptr)
		{
			return nullptr;
		}
		UAudioComponent* Audio = NewObject<UAudioComponent>(
			Owner, UAudioComponent::StaticClass(), Key);
		Audio->SetSound(Loop);
		// Started explicitly once the rotors are actually turning, so a
		// factory of docked drones opens silent rather than humming.
		Audio->bAutoActivate = false;
		Audio->bAllowSpatialization = true;
		Audio->bOverrideAttenuation = true;
		Audio->AttenuationOverrides.bAttenuate = true;
		Audio->AttenuationOverrides.bSpatialize = true;
		Audio->AttenuationOverrides.DistanceAlgorithm =
			EAttenuationDistanceModel::NaturalSound;
		Audio->AttenuationOverrides.AttenuationShape =
			EAttenuationShape::Sphere;
		Audio->AttenuationOverrides.AttenuationShapeExtents =
			FVector(RadiusCm);
		Audio->AttenuationOverrides.FalloffDistance = FalloffCm;
		Audio->AttenuationOverrides.dBAttenuationAtMax = -60.f;
		Audio->SetupAttachment(Parent);
		Audio->RegisterComponent();
		return Audio;
	}
	const FLinearColor SpacecraftDockIdle = LBSpacecraftPalette::IndicatorIdle; // idle dock indicator
	// THE LANE, not a belt (owner: gantry crane plus rail). Pale
	// hardstand, so it reads as ground the craft is set down on rather
	// than a dark moving surface it rides.
	// DARK BED (owner 2026-09-01 "still not right" over a frame of
	// chalk-pale track on a pale floor). Both benchmarks make the
	// conveyor the darkest thing on the floor - that contrast IS how
	// it reads as the spine. Palette hazard backing #23211F in linear.
	const FLinearColor SpacecraftConveyorBed(0.017f, 0.016f, 0.014f);
	const FLinearColor SpacecraftCrateColour = LBSpacecraftPalette::CrateTan; // delivered crates - a second, different crate tone
	// PHASE A OF THE LOOK PLAN (Docs/LOOK_JUDGEMENT_AND_PLAN_v001.md,
	// owner "start on A", 2026-09-02): VALUE CONTRAST. Every frame
	// judged that day had floor, pad, pallet, hull and wall in one band
	// of pale grey. The interior floor drops to a dark concrete so the
	// pale machines, pallets and craft stand off it, the way both
	// reference games' floors work. Candidates, not palette tokens yet:
	// they become Floor.Concrete.Dark in the spec once a frame is judged.
	// Measured on the first phase A frame: a blue-leaning dark tone
	// (#65686E) read cool under a white sun and still cool under a warm
	// one, floor sampling 139/145/153. The concrete family is warm (hue
	// 38, like Floor.Concrete), so the dark floor is too.
	// Lifted a step after the first frame with the hall's own floor:
	// at #6D6A64 the interior sampled 82/82/83 and read as a void.
	const FLinearColor SpacecraftFloorDark(0.205f, 0.194f, 0.178f);   // ~#7C7972
	const FLinearColor SpacecraftFloorZone(0.262f, 0.250f, 0.230f);   // ~#8B887F
	const FLinearColor SpacecraftFloorLine(0.361f, 0.346f, 0.320f);   // ~#A19D96, lane grid
	const FLinearColor SpacecraftBeamColour(0.4f, 0.85f, 1.f);
	const FLinearColor SpacecraftWeldColour(1.f, 0.92f, 0.7f);
	const FLinearColor SpacecraftSparkColour(1.f, 0.6f, 0.15f);
	// SLEEPERS, which were chevrons. The chevrons slid down the lane
	// every frame - the visual grammar of a conveyor, asserting that
	// the surface carries things. It does not; the crane does. Dark
	// cross-ties keep the repeating rhythm that made the lane read as
	// the factory's spine, without the claim.
	// Pale on the now-dark bed (was dark-on-pale before the flip).
	const FLinearColor SpacecraftConveyorChevron(0.58f, 0.57f, 0.54f);
	const FLinearColor SpacecraftBeltRail(0.52f, 0.53f, 0.56f);
	const FLinearColor SpacecraftBeltAccent = LBSpacecraftPalette::MachineAmberTrim; // belt accent, running the length of the floor
	constexpr float SpacecraftBeltDeckZCm = 34.f;
	constexpr float SpacecraftConveyorSpeedCmPerS = 250.f;
	constexpr float SpacecraftConveyorSpacingCm = 400.f;
	const FLinearColor SpacecraftDockCharging(0.9f, 0.45f, 0.1f);
	const FLinearColor SpacecraftStrobeHot(1.0f, 0.05f, 0.02f);
	const FLinearColor SpacecraftStrobeDim(0.12f, 0.01f, 0.01f);
	constexpr float SpacecraftRunwayPaintZCm = 4.f;
	// The Meshy Scout's nose points LOCAL -X (canopy forward of the
	// wings in the segmentation): add 180 deg to any facing yaw.
	constexpr float SpacecraftCraftNoseYawOffsetDeg = 180.f;

	// Owner playtest (2026-08-26 morning): "parts rack was as big as
	// machines". A dressing-fit factor shrinks furniture-class models
	// WITHIN their catalogue footprint; machines stay at full fit.
	float SpacecraftStationDressFit(FName DefinitionId)
	{
		if (DefinitionId == FName(TEXT("StorageRack"))
			|| DefinitionId == FName(TEXT("StorageRackMk2")))
		{
			return 0.65f;
		}
		return 1.f;
	}

	FLinearColor SpacecraftStationColour(FName DefinitionId)
	{
		// Placeholder blocks: graphite stations; the test rig reads darker.
		return DefinitionId == FName(TEXT("TestingRig"))
			? FLinearColor(0.05f, 0.06f, 0.07f)
			: FLinearColor(0.16f, 0.17f, 0.18f);
	}
}

ALBSpacecraftWIPPresentationActor::ALBSpacecraftWIPPresentationActor()
{
	PrimaryActorTick.bCanEverTick = true;
	// THE RUNWAY LIVES ON RUNWAY LAND. Its X was a literal from the
	// 220 m factory floor; when the site grew to 600 m (owner
	// 2026-08-28) the strip stayed where it was and ended up INSIDE
	// the ship factory, which is where the first attempt to photograph
	// a launch found it. Derived from the site's own size now, and
	// placed beyond the buildable edge - the strip is permanent site
	// furniture that nothing may be built over.
	SiteRunwayXCm =
		ALBSpacecraftBuildAuthority::SiteHalfExtentCm() - 2500.f;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	CraftMesh = FSoftObjectPath(
		LBSpacecraftWIPPresentationPrivate::SpacecraftCraftMeshPath);
	ChassisMesh = FSoftObjectPath(
		LBSpacecraftWIPPresentationPrivate::SpacecraftChassisMeshPath);
	AirframeMesh = FSoftObjectPath(
		LBSpacecraftWIPPresentationPrivate::SpacecraftAirframeMeshPath);
	FittedMesh = FSoftObjectPath(
		LBSpacecraftWIPPresentationPrivate::SpacecraftFittedMeshPath);
	CargoChassisMesh = FSoftObjectPath(LBSpacecraftWIPPresentationPrivate
		::SpacecraftCargoChassisMeshPath);
	CargoAirframeMesh = FSoftObjectPath(LBSpacecraftWIPPresentationPrivate
		::SpacecraftCargoAirframeMeshPath);
	CargoFittedMesh = FSoftObjectPath(LBSpacecraftWIPPresentationPrivate
		::SpacecraftCargoFittedMeshPath);
	CargoCraftMesh = FSoftObjectPath(LBSpacecraftWIPPresentationPrivate
		::SpacecraftCargoCraftMeshPath);
	// The Meshy-derived station derivatives (intake manifest
	// StationModels_MeshyIntake_v001). Missing entries fall back to blocks.
	const TCHAR* StationMeshRoot =
		TEXT("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Meshes");
	StationMeshes.Add(FName(TEXT("RollingMill")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_RollingMill_LOD0.SM_LB_ST_RollingMill_LOD0"),
			StationMeshRoot))));
	// The futuristic reactor: domed cap over a glowing core column with
	// four buttress fins, 28.6 m tall in a 24 m square plot.
	StationMeshes.Add(FName(TEXT("PowerPlant")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_PowerPlant_v002")
			TEXT(".SM_LB_ST_PowerPlant_v002"), StationMeshRoot))));
	StationMeshes.Add(FName(TEXT("StorageRack")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_StorageRack_LOD0.SM_LB_ST_StorageRack_LOD0"),
			StationMeshRoot))));
	StationMeshes.Add(FName(TEXT("CircuitFab")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_CircuitFab_LOD0.SM_LB_ST_CircuitFab_LOD0"),
			StationMeshRoot))));
	StationMeshes.Add(FName(TEXT("PowerCellPlant")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_PowerCellPlant_LOD0.SM_LB_ST_PowerCellPlant_LOD0"),
			StationMeshRoot))));
	StationMeshes.Add(FName(TEXT("PropulsionStation")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_PropulsionStation_LOD0")
			TEXT(".SM_LB_ST_PropulsionStation_LOD0"),
			StationMeshRoot))));
	// Procedural slot buildings (owner approved 2026-08-26): open
	// compounds whose hosted units stay visible inside.
	StationMeshes.Add(FName(TEXT("PowerStation")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_PowerStation_LOD0")
			TEXT(".SM_LB_ST_PowerStation_LOD0"), StationMeshRoot))));
	// v003 (2026-08-27): the WHITE FUTURISTIC parts factory. The owner
	// chose this language over the grounded-industrial sawtooth hall of
	// v002 by comparing rendered options, so v002 is superseded rather
	// than kept alongside. Identity confirmed by rendering the drop and
	// looking at it, never by its filename.
	// THE LINE STATIONS, all four pointed at the SAME gantry. They are
	// collapsing into one repeated station type (owner: "one station
	// type like car manufacturer... but with our drones instead of
	// robots"), so sharing the mesh now previews the end state instead
	// of dressing four classes that are about to become one.
	//
	// The Mk1 opening must clear 900 x 450 cm and the Mk2 1400 x 700 -
	// the declared craft envelopes, checked fail-closed against every
	// recipe. Bounds suggest both clear, but a bounding box cannot
	// measure a gap; this wants an eyeball with a craft under it.
	{
		// NO PORTAL OVER THE LINE STATION (owner 2026-09-02: "do we
		// need the arches in the assembly stations as the drones are
		// doing the work"). No: the drones fit, the cranes move, and
		// the frame only hid the craft from the camera. The station is
		// its marked floor square and tool pillars; the three portal
		// dresses that used to stack here are gone together.
	}
	// The two fabrication machines that took the part recipes off the
	// line, the dock where bought goods arrive, and the storage silo.
	StationMeshes.Add(FName(TEXT("StructureFab")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_StructureFab_v001")
			TEXT(".SM_LB_ST_StructureFab_v001"), StationMeshRoot))));
	StationMeshes.Add(FName(TEXT("FitOutFab")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_FitOutFab_v001")
			TEXT(".SM_LB_ST_FitOutFab_v001"), StationMeshRoot))));
	StationMeshes.Add(FName(TEXT("DeliveryDock")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_DeliveryDock_v001")
			TEXT(".SM_LB_ST_DeliveryDock_v001"), StationMeshRoot))));
	// The storage rack wears the Meshy pallet rack (2026-09-02): the
	// silo mesh this pointed at never existed on disk, so the rack was a
	// blockout on the floor and a blank tile in the build menu.
	StationMeshes.Add(FName(TEXT("StorageRack")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
			TEXT("/Game/LineBoss/Candidates/Spacecraft/StationDress_v001")
			TEXT("/SM_LB_ST_WallRack_v001.SM_LB_ST_WallRack_v001"))));
	StationMeshes.Add(FName(TEXT("SubAssemblyHall")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_SubAssemblyHall_v003")
			TEXT(".SM_LB_ST_SubAssemblyHall_v003"), StationMeshRoot))));
	// STATION DRESS (look plan phases C and E, 2026-09-02): the four
	// Meshy models commissioned from the same day's blockout, imported
	// at declared sizes (Saved/Audits/Spacecraft/station_dress_import
	// _v001.json). Geometry only; the presenter tints per role.
	{
		const TCHAR* DressRoot =
			TEXT("/Game/LineBoss/Candidates/Spacecraft/StationDress_v001");
		const TPair<const TCHAR*, const TCHAR*> Dress[] = {
			{ TEXT("Station.ToolTower"), TEXT("SM_LB_ST_ToolTower_v001") },
			{ TEXT("Station.ToolCabinet"), TEXT("SM_LB_ST_ToolCabinet_v001") },
			{ TEXT("Hall.WallRack"), TEXT("SM_LB_ST_WallRack_v001") },
			{ TEXT("Hall.LightBar"), TEXT("SM_LB_ST_LightBar_v001") } };
		for (const auto& Entry : Dress)
		{
			StationMeshes.Add(FName(Entry.Key),
				TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
					FString::Printf(TEXT("%s/%s.%s"), DressRoot,
						Entry.Value, Entry.Value))));
		}
	}
	// The smelter that took the raw-to-stock recipes off the line.
	StationMeshes.Add(FName(TEXT("Smelter")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_Smelter")
			TEXT(".SM_LB_ST_Smelter"), StationMeshRoot))));
	StationMeshes.Add(FName(TEXT("ElectronicsStation")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_ElectronicsStation_LOD0")
			TEXT(".SM_LB_ST_ElectronicsStation_LOD0"),
			StationMeshRoot))));
	StationMeshes.Add(FName(TEXT("SubAssemblyRobot")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_ST_SubAssemblyRobot_LOD0")
			TEXT(".SM_LB_ST_SubAssemblyRobot_LOD0"),
			StationMeshRoot))));
	// Core line stations (and Mk2 marks) wear the closest crafting-
	// family model until each gets its own; min-fit scaling above keeps
	// them inside their footprints.
	const TPair<const TCHAR*, const TCHAR*> SharedDress[] = {
		{ TEXT("MaterialProcessor"), TEXT("SM_LB_ST_RollingMill_LOD0") },
		{ TEXT("MaterialProcessorMk2"),
			TEXT("SM_LB_ST_RollingMill_LOD0") },
		// Owner's morning drop (2026-08-26): the hull bay has its own
		// model; the Propulsion stand-in retires for this pair.
		{ TEXT("HullFabricator"), TEXT("SM_LB_ST_HullFabBay_LOD0") },
		{ TEXT("HullFabricatorMk2"), TEXT("SM_LB_ST_HullFabBay_LOD0") },
		{ TEXT("ComponentFabricator"), TEXT("SM_LB_ST_CircuitFab_LOD0") },
		{ TEXT("ComponentFabricatorMk2"),
			TEXT("SM_LB_ST_CircuitFab_LOD0") },
		// Owner's morning drop (2026-08-26): the assembly bay model
		// (height-capped under 8 m) takes the pair off the SubAssembly
		// stand-in.
		};
	for (const auto& Dress : SharedDress)
	{
		StationMeshes.Add(FName(Dress.Key),
			TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
				FString::Printf(TEXT("%s/%s.%s"), StationMeshRoot,
					Dress.Value, Dress.Value))));
	}
	// CONCEPT-DRIVEN BATCH (owner-approved concepts, 2026-08-31): the
	// TRELLIS pipeline's first production run. These re-Adds win over
	// the registrations above (TMap::Add replaces). Real-size imports,
	// size-verified at import (Saved/Audits/Spacecraft/
	// trellis_batch_import_v001.json); min-fit scaling still applies.
	// The portal-frame LINE STATION dresses all eight line marks - it
	// stands ON the owner's marked floor square, not instead of it.
	{
		const TPair<const TCHAR*, const TCHAR*> ConceptDress[] = {
			{ TEXT("Drone.CargoLift.Body"), TEXT("cargo_drone_v001") },
			{ TEXT("Drone.Assembly.Body"), TEXT("assembly_drone_v001") },
			{ TEXT("Drone.GroundLifter.Body"), TEXT("lifter_drone_v001") },
			// Batch 2 (2026-09-01): the site-furniture and crafting
			// stations. One approved fabricator-cell model dresses the
			// whole sub-assembly family until each earns its own - the
			// same shared-dress convention as the crafting stand-ins
			// above, but with owner-approved concept art.
			{ TEXT("DeliveryDock"), TEXT("delivery_dock_v001") },
			{ TEXT("PowerStation"), TEXT("power_station_v001") },
			{ TEXT("Dock.Charging"), TEXT("charging_dock_v002") },
			{ TEXT("StructureFab"), TEXT("fabricator_cell_v003") },
			{ TEXT("FitOutFab"), TEXT("fabricator_cell_v003") },
			{ TEXT("CircuitFab"), TEXT("fabricator_cell_v003") },
			{ TEXT("PowerCellPlant"), TEXT("fabricator_cell_v003") },
			{ TEXT("PropulsionStation"), TEXT("fabricator_cell_v003") },
			{ TEXT("ElectronicsStation"), TEXT("fabricator_cell_v003") },
			{ TEXT("SubAssemblyRobot"), TEXT("fabricator_cell_v003") },
			{ TEXT("Smelter"), TEXT("fabricator_cell_v003") },
			// The two machine ids the batch missed (2026-09-01, found
			// through the long-red StationAccents test): the plant and
			// mill still pointed at quarantined car-era meshes, so
			// they rendered as blocks and grew no accents. Same
			// shared fabricator dress as their whole family.
			{ TEXT("PowerPlant"), TEXT("fabricator_cell_v003") },
			{ TEXT("RollingMill"), TEXT("fabricator_cell_v003") } };
		for (const auto& Dress : ConceptDress)
		{
			StationMeshes.Add(FName(Dress.Key),
				TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
					FString::Printf(
						TEXT("/Game/Spacecraft/Props/%s/%s.%s"),
						Dress.Value, Dress.Value, Dress.Value))));
		}
	}
	// Runway site furniture: the hover-test pad (owner's evening drop
	// 2026-08-26, from the LaunchRunway_v001 blockout).
	StationMeshes.Add(FName(TEXT("Site.HoverPad")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_RW_HoverPad_LOD0.SM_LB_RW_HoverPad_LOD0"),
			StationMeshRoot))));
	// The canopy glass (owner 2026-08-26 night: "the glass will be
	// one of last things fitted") - per recipe, cut from the airframe.
	StationMeshes.Add(FName(TEXT("Canopy.Scout")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(TEXT(
			"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001")
			TEXT("/Meshes/SM_LB_SC_Scout01_Canopy_v001")
			TEXT(".SM_LB_SC_Scout01_Canopy_v001"))));
	StationMeshes.Add(FName(TEXT("Canopy.Cargo")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(TEXT(
			"/Game/LineBoss/Candidates/Spacecraft/SpacecraftTestBay_v001")
			TEXT("/Meshes/SM_LB_SC_Cargo01_Canopy_v001")
			TEXT(".SM_LB_SC_Cargo01_Canopy_v001"))));
	// The six ship COMPONENTS (owner's batch 2026-08-26, identities
	// assigned by gallery; sized to fit IN the ship). Keyed by their
	// ledger item ids so cargo visuals resolve straight from state.
	for (const TCHAR* ComponentKey : { TEXT("Hull"), TEXT("Electronics"),
		TEXT("Power"), TEXT("Propulsion"), TEXT("Navigation"),
		TEXT("Interior") })
	{
		StationMeshes.Add(
			FName(*FString::Printf(TEXT("Component.%s"), ComponentKey)),
			TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
				FString::Printf(
					TEXT("%s/SM_LB_CP_%s_LOD1.SM_LB_CP_%s_LOD1"),
					StationMeshRoot, ComponentKey, ComponentKey))));
	}
	// The procedural SITE KIT: floor tile, wall bay, wall pillar.
	for (const TCHAR* SitePiece : { TEXT("FloorTile"), TEXT("WallPanel"),
		TEXT("WallPillar") })
	{
		StationMeshes.Add(
			FName(*FString::Printf(TEXT("Site.%s"), SitePiece)),
			TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
				FString::Printf(TEXT("%s/SM_LB_Site_%s.SM_LB_Site_%s"),
					StationMeshRoot, SitePiece, SitePiece))));
	}
	StationMeshes.Add(FName(TEXT("Site.RunwayStrip")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_RW_RunwayStrip_LOD0.SM_LB_RW_RunwayStrip_LOD0"),
			StationMeshRoot))));
	StationMeshes.Add(FName(TEXT("Site.ChicanePylon")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
			TEXT("%s/SM_LB_RW_ChicanePylon_LOD0")
			TEXT(".SM_LB_RW_ChicanePylon_LOD0"), StationMeshRoot))));
	// THE TRACK IS A RAIL AND HARDSTAND LANE, NOT A CONVEYOR. The
	// straight used to bind SM_LB_TR_ConveyorSection - an actual belt -
	// which was right while a belt carried the craft and became wrong
	// the moment the gantry took that job (owner 2026-08-28). A cradle
	// now stands on this lane and a crane lifts from it; nothing about
	// it moves.
	//
	// EVERY PIECE IS EXACTLY 4.00 m on its travel axis, which is the
	// track authority's own GetPieceLengthCm. The turn is a SQUARE 4.00
	// x 4.00 m tile with the curve inside it, not a curved wedge - the
	// first attempt came back as a quarter-annulus at 3.30 m, which
	// cannot butt against a straight on either edge and would have left
	// a crescent gap at every corner a player laid. Measured, not
	// eyeballed: at a glance the wedge looked like a perfectly good
	// corner.
	//
	// The turn is authored single-handed and mirrors for the other way.
	const TPair<const TCHAR*, const TCHAR*> TrackPieceMeshes[] = {
		{ TEXT("Track.Straight"), TEXT("track_straight") },
		{ TEXT("Track.Turn"), TEXT("track_turn") },
		{ TEXT("Track.Cap"), TEXT("track_end_cap") } };
	for (const auto& TrackPiece : TrackPieceMeshes)
	{
		StationMeshes.Add(FName(TrackPiece.Key),
			TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
				FString::Printf(
					TEXT("/Game/LineBoss/Candidates/Spacecraft/")
					TEXT("TrackSet_v002/LB_Track_%s/StaticMeshes/")
					TEXT("LB_Track_%s.LB_Track_%s"),
					TrackPiece.Value, TrackPiece.Value,
					TrackPiece.Value))));
	}
	// Drones are CO-STARS (owner 2026-08-25): seven crew models
	// register, and stations pick their crew by role - Winch under the
	// assembly bays, CargoLift at storage and the dock, Assembly
	// elsewhere.
	// The drone charging dock registration lives in the ConceptDress
	// block ABOVE (charging_dock_v002). A v001 re-Add used to sit here
	// and silently won - TMap::Add replaces, and last writer wins - so
	// every dock on the floor wore the superseded model while the
	// approved v002 sat unused on disk (audit 2026-09-01).
	// The placeholder rotor loop. Soft-referenced so a build without
	// the imported wave still cooks and still runs - the rotors just
	// turn in silence.
	RotorLoopSound = TSoftObjectPtr<USoundBase>(FSoftObjectPath(
		LBSpacecraftWIPPresentationPrivate::SpacecraftRotorSoundPath));
	// THE LANDING GEAR LEG (owner 2026-08-28). One mesh for all three
	// legs: two attempts at a distinct nose leg came back as tripod
	// lander stands, the main leg was right first time, and real
	// tricycle legs do resemble each other. The nose is this mesh
	// scaled down; the nose/main difference lives in the parts.
	StationMeshes.Add(FName(TEXT("Gear.Leg")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
			TEXT("/Game/LineBoss/Candidates/Spacecraft/LandingGear_v001/")
			TEXT("SM_LB_GEAR_MainLeg.SM_LB_GEAR_MainLeg"))));
	// THE GROUND CREW (owner 2026-08-28): three wheeled drones that
	// work UNDER the craft, where a flier cannot reach. Registered by
	// the same key shape as the fliers so the crew lookup does not
	// care which kind it is asking for.
	//
	// DRONEBATCH_v001 (2026-08-30): all seven crew kinds - the two
	// already-remade fliers (CargoLift, Assembly) AND the five that were
	// still blockouts (Spray, Winch, GroundLifter, GroundAssembly,
	// GroundSprayer) - replaced together from one commissioned batch,
	// this time authored with moving parts (rotor spinners, wheels)
	// kept as separate named objects rather than carved from a whole
	// mesh, so they can genuinely animate instead of being modelled
	// mid-spin. GetDronePartsManifest() (below) knows which imported
	// part goes with which body. Body asset names are "<Stem>_Body"
	// for every multi-part import EXCEPT ChargingDock, whose single-
	// mesh GLB imported as bare "<Stem>" - Interchange names a
	// single-object import after the source file, not the internal
	// node, and only that one case has no second object to disambiguate
	// against.
	const TCHAR* DroneBatchRoot = TEXT(
		"/Game/LineBoss/Candidates/Spacecraft/DroneBatch_v001");
	const TCHAR* DroneBatchKeys[][2] = {
		{ TEXT("CargoLift"), TEXT("cargolift_v001") },
		{ TEXT("Assembly"), TEXT("assembly_v001") },
		{ TEXT("Spray"), TEXT("spray_v001") },
		{ TEXT("Winch"), TEXT("winch_v001") },
		{ TEXT("GroundLifter"), TEXT("ground_lifter_v001") },
		{ TEXT("GroundAssembly"), TEXT("ground_assembly_v001") },
		{ TEXT("GroundSprayer"), TEXT("ground_sprayer_v001") } };
	for (const auto& Batch : DroneBatchKeys)
	{
		StationMeshes.Add(
			FName(*FString::Printf(TEXT("Drone.%s.Body"), Batch[0])),
			TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
				TEXT("%s/%s/%s/StaticMeshes/%s_Body.%s_Body"),
				DroneBatchRoot, Batch[1], Batch[1], Batch[1], Batch[1]))));
	}
	// THE PAINT BOOTH, which had no model at all - twenty-six metres of
	// engine cubes on the biggest object on the floor after the hall.
	StationMeshes.Add(FName(TEXT("SprayBooth")),
		TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
			TEXT("/Game/LineBoss/Candidates/Spacecraft/PaintBooth_v001/")
			TEXT("LB_Booth_paint_booth/StaticMeshes/")
			TEXT("LB_Booth_paint_booth.LB_Booth_paint_booth"))));
	// THE FIVE PARTS CARRIERS that stand on a kit dolly. Registered
	// under their own keys so the dolly can pick a carrier per
	// component family rather than repeating one generic crate - the
	// five were measured distinct by silhouette at the 72 px they
	// actually occupy in frame.
	const TCHAR* Carriers[] = { TEXT("bundled_stock"), TEXT("cage_pallet"),
		TEXT("open_tray"), TEXT("pressure_canister"),
		TEXT("sealed_crate") };
	for (const TCHAR* Carrier : Carriers)
	{
		StationMeshes.Add(
			FName(*FString::Printf(TEXT("Carrier.%s"), Carrier)),
			TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
				TEXT("/Game/LineBoss/Candidates/Spacecraft/Carriers_v001/")
				TEXT("LB_Carrier_%s/StaticMeshes/")
				TEXT("LB_Carrier_%s.LB_Carrier_%s"),
				Carrier, Carrier, Carrier))));
	}
	// PALLETLOADS_v001 (2026-08-30): fourteen real ship assemblies cut
	// from the Scout model itself, stowed on factory pallets - the
	// per-COMPONENT kit dolly content the Meshy-era generic crate block
	// was always a stand-in for. Registered under "Pallet.<stem>" so
	// GetKitPalletCandidates() (below) can build each component's
	// variety pool by name rather than repeating the path here.
	const TCHAR* Pallets[] = {
		TEXT("pallet-hull_nose"), TEXT("pallet-hull_fwd"),
		TEXT("pallet-hull_mid"), TEXT("pallet-hull_aft"),
		TEXT("pallet-wing"), TEXT("pallet-wing_port"),
		TEXT("pallet-canopy"), TEXT("pallet-booster"),
		TEXT("pallet-booster_port"), TEXT("pallet-mainengine"),
		TEXT("pallet-cellbank"), TEXT("pallet-avionics"),
		TEXT("pallet-sensor"), TEXT("pallet-interior") };
	for (const TCHAR* Pallet : Pallets)
	{
		// The destination folder was written with underscores (Python
		// cannot use a hyphen in some path contexts this pipeline
		// touches), but Interchange named the single-object import
		// after the SOURCE FILE verbatim, hyphen included - the same
		// asset-naming quirk charging_dock_v001 hit. The two must not
		// be conflated: FolderStem for the two directory levels,
		// Pallet (unmodified) for the asset name.
		const FString FolderStem =
			FString(Pallet).Replace(TEXT("-"), TEXT("_"));
		StationMeshes.Add(
			FName(*FString::Printf(TEXT("Pallet.%s"), Pallet)),
			TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(FString::Printf(
				TEXT("/Game/LineBoss/Candidates/Spacecraft/")
				TEXT("PalletLoads_v001/%s/%s/StaticMeshes/%s.%s"),
				*FolderStem, Pallet, Pallet, Pallet))));
	}
}

UStaticMesh* ALBSpacecraftWIPPresentationActor::TryGetStationMesh(
	FName DefinitionId)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	// CORRECTED, 2026-08-30 (same day). The first version of this gate
	// blocked EVERYTHING that funnelled through this one function,
	// classified purely by its /Game/.../Candidates/Spacecraft/ path -
	// but "Candidates" is this project's naming for "not yet promoted",
	// not a synonym for Meshy, and the owner caught the paint booth
	// being wrongly blocked within the hour. Checked properly against
	// SourceAssets/Spacecraft/<Folder> (the PROMOTED source tree, as
	// opposed to SourceAssets/Candidate/Spacecraft/<Name>_MeshyIntake_
	// v001, the raw-intake tree with an actual Meshy manifest): the
	// booth, the two ALREADY-REMADE drones, the lift cradle, the parts
	// carriers and the ship-fitting components all have organised,
	// individually-named promoted sources - direct evidence they are
	// finished, non-Meshy work, not folder-name pattern-matching.
	// Excluded from the gate for that reason. Everything else here
	// (the core station machine bodies, ground drones, landing gear,
	// the two still-old flying drones, both craft canopies) has NO
	// promoted-tree counterpart at all, which is the same evidence
	// working the other way - keep those blocked.
	// "Components_v001" in the promoted tree LOOKED like a match for
	// these six (Component.Hull etc) by name alone - it is not. It
	// holds a different, unrelated part-name convention (LB_Part_*)
	// that this game never loads; the keys actually loaded here
	// (SM_LB_CP_*_LOD1) have no promoted counterpart anywhere. Nearly
	// excluded them on the strength of a second folder-name coincidence
	// before checking the real file prefix - exactly the mistake this
	// correction exists to stop making, so it is recorded rather than
	// quietly avoided. They stay gated.
	// DRONEBATCH_v001 (2026-08-30): all seven crew bodies plus the
	// charging dock now have a genuine promoted source too - this list
	// predates that batch and only named the two drones remade before
	// it (CargoLift, Assembly), so the other five plus the dock were
	// still being silently blocked here even after their StationMeshes
	// paths were repointed at real DroneBatch_v001 assets. That is the
	// actual cause of "drones don't render properly": every crew this
	// list missed fell through to the placeholder block/pod fallback,
	// which is what was on screen.
	const bool bHasPromotedSource =
		DefinitionId == FName(TEXT("SprayBooth"))
		|| DefinitionId == FName(TEXT("Drone.CargoLift.Body"))
		|| DefinitionId == FName(TEXT("Drone.Assembly.Body"))
		|| DefinitionId == FName(TEXT("Drone.Spray.Body"))
		|| DefinitionId == FName(TEXT("Drone.Winch.Body"))
		|| DefinitionId == FName(TEXT("Drone.GroundLifter.Body"))
		|| DefinitionId == FName(TEXT("Drone.GroundAssembly.Body"))
		|| DefinitionId == FName(TEXT("Drone.GroundSprayer.Body"))
		|| DefinitionId == FName(TEXT("Dock.Charging"))
		// CONCEPT-DRIVEN BATCH (2026-08-31): owner-approved concepts
		// through the TRELLIS pipeline, size-verified at import - the
		// promoted-source bar these keys had to clear is met.
		|| DefinitionId.ToString().StartsWith(TEXT("MaterialProcessor"))
		|| DefinitionId.ToString().StartsWith(TEXT("HullFabricator"))
		|| DefinitionId.ToString().StartsWith(TEXT("ComponentFabricator"))
		|| DefinitionId.ToString().StartsWith(TEXT("AssemblyRobot"))
		|| DefinitionId == FName(TEXT("DeliveryDock"))
		|| DefinitionId == FName(TEXT("PowerStation"))
		|| DefinitionId == FName(TEXT("StructureFab"))
		|| DefinitionId == FName(TEXT("FitOutFab"))
		|| DefinitionId == FName(TEXT("CircuitFab"))
		|| DefinitionId == FName(TEXT("PowerCellPlant"))
		|| DefinitionId == FName(TEXT("PropulsionStation"))
		|| DefinitionId == FName(TEXT("ElectronicsStation"))
		|| DefinitionId == FName(TEXT("SubAssemblyRobot"))
		|| DefinitionId == FName(TEXT("Smelter"))
		|| DefinitionId == FName(TEXT("PowerPlant"))
		|| DefinitionId == FName(TEXT("RollingMill"))
		|| DefinitionId.ToString().StartsWith(TEXT("Carrier."))
		|| DefinitionId.ToString().StartsWith(TEXT("Track."))
		// PALLETLOADS_v001 (2026-08-30): added at registration time,
		// not discovered as a second silent-block bug later.
		|| DefinitionId.ToString().StartsWith(TEXT("Pallet."))
		// SITE KIT (2026-09-01): import_site_kit_v002.py is explicit -
		// "Procedural, no Meshy, no third-party assets", owner-requested
		// floor/wall quality. The gate's default-deny had silently
		// killed RefreshSiteDressing in every build since it went up;
		// the packaged journey finally made the fallback visible.
		|| DefinitionId.ToString().StartsWith(TEXT("Site."))
		// The station dress and hall fill (look plan phases C and E,
		// 2026-09-02): imported with sizes verified, so promoted.
		|| DefinitionId.ToString().StartsWith(TEXT("Station."))
		|| DefinitionId.ToString().StartsWith(TEXT("Hall."))
		// The storage rack wears the same imported pallet rack (2026-09-02).
		|| DefinitionId.ToString().StartsWith(TEXT("StorageRack"));
	if (bBlockoutMeshyContent && !bHasPromotedSource)
	{
		return nullptr;
	}
	if (TObjectPtr<UStaticMesh>* Cached =
		LoadedStationMeshes.Find(DefinitionId))
	{
		return Cached->Get();
	}
	if (StationMeshLoadFailed.Contains(DefinitionId))
	{
		return nullptr;
	}
	const TSoftObjectPtr<UStaticMesh>* Soft =
		StationMeshes.Find(DefinitionId);
	UStaticMesh* Mesh =
		Soft != nullptr ? Soft->LoadSynchronous() : nullptr;
	if (Mesh == nullptr)
	{
		// Honest fallback, logged ONCE per definition: the block stands in.
		StationMeshLoadFailed.Add(DefinitionId);
		UE_LOG(LogTemp, Display,
			TEXT("SPACECRAFT PRESENTER: no station mesh for %s - ")
			TEXT("placeholder block in use"), *DefinitionId.ToString());
		return nullptr;
	}
	LoadedStationMeshes.Add(DefinitionId, Mesh);
	UE_LOG(LogTemp, Display,
		TEXT("SPACECRAFT PRESENTER: station mesh bound for %s"),
		*DefinitionId.ToString());
	return Mesh;
}

void ALBSpacecraftWIPPresentationActor::BindAuthorities(
	ALBSpacecraftBuildAuthority* InBuild,
	ALBSpacecraftRuntimeCoordinator* InCoordinator,
	ALBSpacecraftProductionAuthority* InProduction)
{
	BuildAuthority = InBuild;
	Coordinator = InCoordinator;
	ProductionAuthority = InProduction;
}

void ALBSpacecraftWIPPresentationActor::BindCrafting(
	ALBSpacecraftCraftingAuthority* InCrafting)
{
	CraftingAuthority = InCrafting;
}

void ALBSpacecraftWIPPresentationActor::BindInventory(
	ALBSpacecraftInventoryAuthority* InInventory)
{
	InventoryAuthority = InInventory;
}

void ALBSpacecraftWIPPresentationActor::BindDroneFleet(
	ALBSpacecraftDroneFleetAuthority* InFleet)
{
	DroneFleetAuthority = InFleet;
}

float ALBSpacecraftWIPPresentationActor::ComputeAccentPulse01(
	float ClockSeconds, float PeriodSeconds)
{
	if (PeriodSeconds <= 0.f)
	{
		return 0.5f;
	}
	return 0.5f + 0.5f * FMath::Sin(
		2.f * PI * ClockSeconds / PeriodSeconds);
}

float ALBSpacecraftWIPPresentationActor::ComputeRingYawDeg(
	float ClockSeconds)
{
	return FMath::Fmod(ClockSeconds * 24.f, 360.f);
}

int32 ALBSpacecraftWIPPresentationActor::GetRunwayPartCount(
	FName RigStationId) const
{
	const FLBSpacecraftRunwayVisual* Runway = Runways.Find(RigStationId);
	return Runway != nullptr ? Runway->Parts.Num() : 0;
}

float ALBSpacecraftWIPPresentationActor::ComputeStrobeArmClock(
	float DepartureElapsedSeconds, float InChicaneSeconds,
	float LeadSeconds)
{
	return DepartureElapsedSeconds
		- FMath::Max(InChicaneSeconds - LeadSeconds, 0.f);
}

void ALBSpacecraftWIPPresentationActor::ComputeThrusterMix(
	float ElapsedSeconds, float InChicaneSeconds, float InSprintSeconds,
	float& OutBelly01, float& OutMain01)
{
	const float T = FMath::Max(ElapsedSeconds, 0.f);
	const float SpoolSeconds = 0.4f;
	if (T <= InChicaneSeconds || InSprintSeconds <= 0.f)
	{
		// Hover and chicane ride on the belly RCS; the mains only start
		// spooling just before throttle-up.
		OutBelly01 = 1.f;
		OutMain01 = InChicaneSeconds > 0.f
			? 0.3f * FMath::Clamp(
				(T - (InChicaneSeconds - SpoolSeconds)) / SpoolSeconds,
				0.f, 1.f)
			: 0.f;
		return;
	}
	const float U = FMath::Clamp(
		(T - InChicaneSeconds) / InSprintSeconds, 0.f, 1.f);
	// As speed builds the belly cuts out and only the mains burn.
	OutBelly01 = 1.f - FMath::Clamp(U / 0.25f, 0.f, 1.f);
	OutMain01 = 0.3f + 0.7f * FMath::Clamp(U / 0.3f, 0.f, 1.f);
}

int32 ALBSpacecraftWIPPresentationActor::GetUnitFlameCount(
	FName UnitId) const
{
	const FLBSpacecraftFlameSet* Flames = UnitFlames.Find(UnitId);
	return Flames != nullptr
		? Flames->Belly.Num() + Flames->Main.Num() : 0;
}

int32 ALBSpacecraftWIPPresentationActor::GetDepartingFlameCount() const
{
	int32 Count = 0;
	for (const FLBSpacecraftDepartingVisual& Departure : Departing)
	{
		Count += Departure.BellyFlames.Num()
			+ Departure.MainFlames.Num();
	}
	return Count;
}

ALBSpacecraftWIPPresentationActor::FLBSpacecraftFlameSet
ALBSpacecraftWIPPresentationActor::MakeFlameSet(
	UStaticMeshComponent* CraftComponent, FName KeyBase)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	FLBSpacecraftFlameSet Flames;
	UStaticMesh* Cone = LoadObject<UStaticMesh>(nullptr,
		SpacecraftConePath);
	if (Cone == nullptr || CraftComponent == nullptr)
	{
		return Flames; // draws less, never more
	}
	UMaterialInterface* Plume = LoadObject<UMaterialInterface>(nullptr,
		SpacecraftSoftFlameMaterialPath);
	if (Plume == nullptr)
	{
		Plume = LoadObject<UMaterialInterface>(nullptr,
			SpacecraftPlumeMaterialPath);
	}
	auto MakeFlame = [&](const TCHAR* Part, int32 Index,
		const FVector& RelLocation, const FRotator& RelRotation,
		const FVector& RelScale) -> UStaticMeshComponent*
	{
		const FName Key(*FString::Printf(TEXT("%s_%s%d"),
			*KeyBase.ToString(), Part, Index));
		UStaticMeshComponent* Flame = NewObject<UStaticMeshComponent>(
			this, UStaticMeshComponent::StaticClass(), Key);
		Flame->SetStaticMesh(Cone);
		Flame->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Flame->SetCastShadow(false);
		Flame->SetupAttachment(CraftComponent);
		Flame->SetRelativeLocation(RelLocation);
		Flame->SetRelativeRotation(RelRotation);
		Flame->SetRelativeScale3D(RelScale);
		Flame->RegisterComponent();
		if (Plume != nullptr)
		{
			UMaterialInstanceDynamic* PlumeMID =
				UMaterialInstanceDynamic::Create(Plume, Flame);
			PlumeMID->SetVectorParameterValue(TEXT("Color"),
				SpacecraftFlameBlue);
			Flame->SetMaterial(0, PlumeMID);
		}
		else if (UMaterialInterface* ShapeMaterial =
			LoadObject<UMaterialInterface>(nullptr,
				SpacecraftShapeMaterialPath))
		{
			UMaterialInstanceDynamic* MID =
				UMaterialInstanceDynamic::Create(ShapeMaterial, Flame);
			MID->SetVectorParameterValue(TEXT("Color"),
				SpacecraftFlameBlue);
			Flame->SetMaterial(0, MID);
		}
		return Flame;
	};
	// Belly RCS: four cones under the hull, apex up at the nozzle so the
	// plume widens downward (the mesh is grounded at Z=0).
	const FVector2D BellySpots[] = { FVector2D(350.f, -150.f),
		FVector2D(350.f, 150.f), FVector2D(-350.f, -150.f),
		FVector2D(-350.f, 150.f) };
	for (int32 Index = 0; Index < 4; ++Index)
	{
		Flames.Belly.Add(MakeFlame(TEXT("Belly"), Index,
			FVector(BellySpots[Index].X, BellySpots[Index].Y, -110.f),
			FRotator::ZeroRotator, FVector(0.6f, 0.6f, 2.2f)));
	}
	// Mains: three cones at the tail (local -X), apex toward the nose so
	// the plume widens behind the craft.
	const float MainY[] = { -110.f, 0.f, 110.f };
	for (int32 Index = 0; Index < 3; ++Index)
	{
		Flames.Main.Add(MakeFlame(TEXT("Main"), Index,
			FVector(-660.f - 250.f, MainY[Index], 120.f),
			FRotator(-90.f, 0.f, 0.f), FVector(1.1f, 1.1f, 5.f)));
	}
	return Flames;
}

void ALBSpacecraftWIPPresentationActor::ComputeTricycleGearAnchorsCm(
	const FVector& HullOriginCm, const FVector& HullHalfExtentCm,
	FVector& OutNoseCm, FVector& OutLeftMainCm, FVector& OutRightMainCm)
{
	// TRICYCLE, in the aircraft sense: the nose leg carries little and
	// steers, the two mains carry the weight and sit just BEHIND the
	// hull centre so the craft rests nose-down rather than on its tail.
	// Mains forward of centre is the classic way to build a machine
	// that tips over backwards the moment it is loaded.
	const float BellyZ = HullOriginCm.Z - HullHalfExtentCm.Z;
	OutNoseCm = FVector(HullOriginCm.X + HullHalfExtentCm.X * 0.62f,
		HullOriginCm.Y, BellyZ);
	// Track wide enough to be stable, inboard enough that the wheels
	// stay under the hull rather than sticking out past it.
	const float TrackY = HullHalfExtentCm.Y * 0.55f;
	const float MainX = HullOriginCm.X - HullHalfExtentCm.X * 0.20f;
	OutLeftMainCm = FVector(MainX, HullOriginCm.Y - TrackY, BellyZ);
	OutRightMainCm = FVector(MainX, HullOriginCm.Y + TrackY, BellyZ);
}

float ALBSpacecraftWIPPresentationActor::ComputeGearRetraction01(
	float ElapsedSeconds, float InChicaneSeconds, float InRetractSeconds)
{
	if (ElapsedSeconds <= InChicaneSeconds)
	{
		return 0.f; // still taxiing the chicane: wheels stay down
	}
	if (InRetractSeconds <= 0.f)
	{
		return 1.f;
	}
	return FMath::SmoothStep(0.f, 1.f,
		(ElapsedSeconds - InChicaneSeconds) / InRetractSeconds);
}

void ALBSpacecraftWIPPresentationActor::ApplyGearRetraction(
	const TArray<TWeakObjectPtr<UStaticMeshComponent>>& Legs,
	const TArray<float>& AnchorZCm, float Retraction01,
	float RetractTravelCm)
{
	const float Folded = FMath::Clamp(Retraction01, 0.f, 1.f);
	for (int32 Index = 0; Index < Legs.Num(); ++Index)
	{
		UStaticMeshComponent* Leg = Legs[Index].Get();
		if (!IsValid(Leg))
		{
			continue;
		}
		if (Folded >= 0.999f)
		{
			// Fully away: hidden outright rather than left as a
			// zero-scale component the eye can still catch shimmering.
			Leg->SetVisibility(false, /*bPropagateToChildren=*/true);
			continue;
		}
		Leg->SetVisibility(true, /*bPropagateToChildren=*/true);
		FVector Where = Leg->GetRelativeLocation();
		// The leg CLIMBS INTO THE HULL and is occluded by it - which is
		// what a wheel well is. Deliberately not a shrink: the strut's
		// own scale is non-uniform (thin and long), so scaling it back
		// toward unity would visibly fatten the leg as it folded.
		// The travel is computed once, at build time, in the craft's
		// own local units - which is not centimetres when the hull is a
		// scaled blockout cube.
		Where.Z = (AnchorZCm.IsValidIndex(Index)
			? AnchorZCm[Index] : Where.Z) + RetractTravelCm * Folded;
		Leg->SetRelativeLocation(Where);
	}
}

int32 ALBSpacecraftWIPPresentationActor::GetLandingGearLegCount() const
{
	int32 Count = 0;
	for (const TPair<FName, FLBSpacecraftGearSet>& Pair : UnitGear)
	{
		Count += Pair.Value.Legs.Num();
	}
	return Count;
}

ALBSpacecraftWIPPresentationActor::FLBSpacecraftGearSet
ALBSpacecraftWIPPresentationActor::MakeGearSet(
	UStaticMeshComponent* CraftComponent, FName KeyBase)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	FLBSpacecraftGearSet Gear;
	if (CraftComponent == nullptr
		|| CraftComponent->GetStaticMesh() == nullptr)
	{
		return Gear; // draws less, never more
	}
	UStaticMesh* Cylinder = LoadObject<UStaticMesh>(nullptr,
		SpacecraftCylinderPath);
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr,
		SpacecraftCubePath);
	UMaterialInterface* Shape = LoadObject<UMaterialInterface>(nullptr,
		SpacecraftShapeMaterialPath);
	if (Cylinder == nullptr || Cube == nullptr)
	{
		return Gear;
	}
	// EVERYTHING BELOW IS IN THE CRAFT'S LOCAL SPACE, and that space is
	// not always centimetres: an unresolved hull is drawn as a SCALED
	// CUBE, so a leg placed naively under it comes out stretched by the
	// hull's own scale. Local bounds and local anchors line up by
	// themselves; only the leg's own dimensions need the scale undone.
	const FBoxSphereBounds Bounds =
		CraftComponent->GetStaticMesh()->GetBounds();
	const FVector CraftScale = CraftComponent->GetRelativeScale3D();
	const FVector InvCraft(
		1.f / FMath::Max(FMath::Abs(CraftScale.X), KINDA_SMALL_NUMBER),
		1.f / FMath::Max(FMath::Abs(CraftScale.Y), KINDA_SMALL_NUMBER),
		1.f / FMath::Max(FMath::Abs(CraftScale.Z), KINDA_SMALL_NUMBER));
	FVector NoseAt;
	FVector LeftAt;
	FVector RightAt;
	ComputeTricycleGearAnchorsCm(Bounds.Origin, Bounds.BoxExtent,
		NoseAt, LeftAt, RightAt);

	// Graphite struts and near-black tyres: structural steel reads dark
	// in the settled language, and a wheel that is not nearly black
	// stops reading as rubber.
	const FLinearColor StrutTone(0.24f, 0.25f, 0.28f);
	const FLinearColor TyreTone(0.06f, 0.06f, 0.07f);
	auto MakePiece = [&](USceneComponent* Parent, const FName& Key,
		UStaticMesh* Mesh, const FLinearColor& Colour,
		const FVector& RelLocation, const FRotator& RelRotation,
		const FVector& RelScale) -> UStaticMeshComponent*
	{
		UStaticMeshComponent* Piece = NewObject<UStaticMeshComponent>(
			this, UStaticMeshComponent::StaticClass(), Key);
		Piece->SetStaticMesh(Mesh);
		Piece->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Piece->SetCastShadow(true);
		Piece->SetReceivesDecals(false);
		Piece->SetupAttachment(Parent);
		Piece->SetRelativeLocation(RelLocation);
		Piece->SetRelativeRotation(RelRotation);
		Piece->SetRelativeScale3D(RelScale);
		Piece->RegisterComponent();
		if (Shape != nullptr)
		{
			UMaterialInstanceDynamic* MID =
				UMaterialInstanceDynamic::Create(Shape, Piece);
			MID->SetVectorParameterValue(TEXT("Color"), Colour);
			Piece->SetMaterial(0, MID);
		}
		return Piece;
	};

	// The nose leg is the small one and the mains carry the weight -
	// that asymmetry is what makes it read as tricycle gear rather than
	// three identical posts. Declared up here because the real-mesh
	// path sizes a leg by its wheel.
	const float MainWheelRadiusCm =
		FMath::Clamp(FMath::Max(GearHeightCm, 10.f) * 0.32f, 14.f, 90.f);

	// One leg: an oleo strut hanging from the belly, a drag brace
	// raking off it, and a wheel on an axle. The STRUT IS THE ROOT of
	// the leg, so retracting moves the whole assembly as one and the
	// children are never touched again. BLOCKOUT ONLY - used when the
	// modelled leg is unavailable.
	const float Height = FMath::Max(GearHeightCm, 10.f);
	// The real leg when it is available; the blockout below when it is
	// not. A whole modelled leg needs no strut, brace or wheel built
	// under it - carving those on would only disfigure it, the same
	// lesson the drone fan pods taught.
	UStaticMesh* LegMesh = TryGetStationMesh(FName(TEXT("Gear.Leg")));
	const float LegMeshHeightCm = LegMesh != nullptr
		? FMath::Max(LegMesh->GetBounds().BoxExtent.Z * 2.f, 1.f) : 1.f;
	auto MakeLeg = [&](const TCHAR* Part, const FVector& AnchorCm,
		float WheelRadiusCm, float StrutRadiusCm)
			-> UStaticMeshComponent*
	{
		const FName StrutKey(*FString::Printf(TEXT("%s_Gear%s_Strut"),
			*KeyBase.ToString(), Part));
		if (LegMesh != nullptr)
		{
			// The leg is modelled standing on the ground with its
			// trunnion at the top, so it hangs from the belly by its
			// own full height. Wheel size stands in for leg size: the
			// nose leg is the same part built smaller.
			const float Wanted = Height * (WheelRadiusCm
				/ FMath::Max(MainWheelRadiusCm, 1.f));
			const FVector Fit(
				Wanted / LegMeshHeightCm * InvCraft.X,
				Wanted / LegMeshHeightCm * InvCraft.Y,
				Wanted / LegMeshHeightCm * InvCraft.Z);
			return MakePiece(CraftComponent, StrutKey, LegMesh,
				StrutTone,
				AnchorCm - FVector(0.f, 0.f, Wanted * InvCraft.Z),
				FRotator::ZeroRotator, Fit);
		}
		// A 100 cm engine cylinder is centred on its own origin, so
		// hanging it half a leg below the belly puts its top at the
		// hull and its foot at the wheel.
		UStaticMeshComponent* Strut = MakePiece(CraftComponent, StrutKey,
			Cylinder, StrutTone,
			AnchorCm - FVector(0.f, 0.f,
				Height * 0.5f * InvCraft.Z),
			FRotator::ZeroRotator,
			FVector(StrutRadiusCm / 50.f * InvCraft.X,
				StrutRadiusCm / 50.f * InvCraft.Y,
				Height / 100.f * InvCraft.Z));
		if (Strut == nullptr)
		{
			return nullptr;
		}
		// Children live in the STRUT's space, which its own scale
		// distorts; undoing that scale is what keeps the wheel round
		// instead of squashed into an ellipse by the leg length.
		const FVector Undo(50.f / (StrutRadiusCm * InvCraft.X),
			50.f / (StrutRadiusCm * InvCraft.Y),
			100.f / (Height * InvCraft.Z));
		const FName WheelKey(*FString::Printf(TEXT("%s_Gear%s_Wheel"),
			*KeyBase.ToString(), Part));
		// Rolled 90 degrees, a standing cylinder becomes a wheel on an
		// axle running across the craft.
		MakePiece(Strut, WheelKey, Cylinder, TyreTone,
			FVector(0.f, 0.f, -0.5f), FRotator(0.f, 0.f, 90.f),
			FVector(WheelRadiusCm / 50.f * Undo.X,
				WheelRadiusCm * 0.5f / 50.f * Undo.Y,
				WheelRadiusCm / 50.f * Undo.Z));
		const FName BraceKey(*FString::Printf(TEXT("%s_Gear%s_Brace"),
			*KeyBase.ToString(), Part));
		MakePiece(Strut, BraceKey, Cube, StrutTone,
			FVector(0.3f, 0.f, -0.05f), FRotator(38.f, 0.f, 0.f),
			FVector(Height * 0.0055f * Undo.X, 0.14f * Undo.Y,
				Height * 0.011f * Undo.Z));
		return Strut;
	};

	const float MainWheel = MainWheelRadiusCm;
	const TCHAR* Parts[] = { TEXT("Nose"), TEXT("Left"), TEXT("Right") };
	const FVector Anchors[] = { NoseAt, LeftAt, RightAt };
	const float Wheels[] = { MainWheel * 0.72f, MainWheel, MainWheel };
	const float Struts[] = { 9.f, 12.f, 12.f };
	for (int32 Index = 0; Index < 3; ++Index)
	{
		if (UStaticMeshComponent* Leg = MakeLeg(Parts[Index],
			Anchors[Index], Wheels[Index], Struts[Index]))
		{
			Gear.Legs.Add(Leg);
			Gear.AnchorZCm.Add(Leg->GetRelativeLocation().Z);
		}
	}
	// 1.6 leg-lengths of travel puts the wheel comfortably above the
	// belly plane rather than grazing it, so the fold ends with the
	// whole leg swallowed by the hull that occludes it.
	Gear.RetractTravelCm = Height * 1.6f * InvCraft.Z;
	return Gear;
}

void ALBSpacecraftWIPPresentationActor::ApplyFlameIntensity(
	const TArray<TWeakObjectPtr<UStaticMeshComponent>>& Flames,
	float Intensity01, float FlickerSeed)
{
	for (int32 Index = 0; Index < Flames.Num(); ++Index)
	{
		UStaticMeshComponent* Flame = Flames[Index].Get();
		if (!IsValid(Flame))
		{
			continue;
		}
		if (Intensity01 <= 0.02f)
		{
			Flame->SetVisibility(false);
			continue;
		}
		const float Flicker = 0.85f + 0.15f * FMath::Sin(
			FlickerSeed * 23.f + Index * 1.7f);
		Flame->SetVisibility(true);
		FVector Scale = Flame->GetRelativeScale3D();
		Scale.Z = (Flame->GetRelativeRotation().Pitch < -45.f
			? 5.f : 2.2f) * Intensity01 * Flicker;
		Flame->SetRelativeScale3D(Scale);
	}
}

void ALBSpacecraftWIPPresentationActor::DestroyFlameSet(
	FLBSpacecraftFlameSet& Flames)
{
	for (const TWeakObjectPtr<UStaticMeshComponent>& Flame : Flames.Belly)
	{
		if (UStaticMeshComponent* Live = Flame.Get(); IsValid(Live))
		{
			Live->DestroyComponent();
		}
	}
	for (const TWeakObjectPtr<UStaticMeshComponent>& Flame : Flames.Main)
	{
		if (UStaticMeshComponent* Live = Flame.Get(); IsValid(Live))
		{
			Live->DestroyComponent();
		}
	}
	Flames.Belly.Reset();
	Flames.Main.Reset();
}

float ALBSpacecraftWIPPresentationActor::ComputeStrobeIntensity01(
	float ClockSeconds, int32 LightIndex, int32 LightCount,
	float ChasePeriodSeconds)
{
	if (LightCount <= 0 || ChasePeriodSeconds <= 0.f)
	{
		return 0.f;
	}
	const float Phase = FMath::Fmod(
		FMath::Max(ClockSeconds, 0.f) / ChasePeriodSeconds, 1.f);
	const int32 HotIndex = FMath::Clamp(
		static_cast<int32>(Phase * LightCount), 0, LightCount - 1);
	return LightIndex == HotIndex ? 1.f : 0.f;
}

void ALBSpacecraftWIPPresentationActor::BindTransport(
	ALBSpacecraftTransportAuthority* InTransport)
{
	TransportAuthority = InTransport;
	ConveyorRevision.Reset(); // rebuild against the new source
}

void ALBSpacecraftWIPPresentationActor::ComputeHoverWobbleDeg(
	float ClockSeconds, float& OutPitchDeg, float& OutRollDeg)
{
	// Incommensurate periods so the drift never visibly repeats.
	OutPitchDeg = 1.4f * FMath::Sin(ClockSeconds * 0.83f);
	OutRollDeg = 1.1f * FMath::Sin(ClockSeconds * 1.27f + 1.1f);
}

float ALBSpacecraftWIPPresentationActor::ComputeRCSCorrection01(
	float PitchDeg, float RollDeg, int32 CornerIndex)
{
	// Belly corner signs in flame order (see MakeFlameSet).
	static const float SignX[] = { 1.f, 1.f, -1.f, -1.f };
	static const float SignY[] = { -1.f, 1.f, -1.f, 1.f };
	const int32 Corner = FMath::Clamp(CornerIndex, 0, 3);
	// Positive pitch lifts the nose (+X corners rise, -X drop);
	// positive roll lifts +Y. A dropped corner fires to push back up.
	const float CornerHeight = PitchDeg * SignX[Corner] * 0.5f
		+ RollDeg * SignY[Corner] * 0.5f;
	const float Correction = FMath::Clamp(-CornerHeight * 0.85f,
		0.f, 0.94f);
	// A whisper of station-keeping so a level craft still breathes.
	return FMath::Clamp(Correction + 0.06f, 0.f, 1.f);
}

bool ALBSpacecraftWIPPresentationActor::GetActiveDeparture(
	FVector& OutShipCm, float& OutElapsedSeconds,
	float* OutCraftHalfLenCm) const
{
	for (const FLBSpacecraftDepartingVisual& Departure : Departing)
	{
		if (Departure.Component != nullptr)
		{
			OutShipCm = Departure.Component->GetComponentLocation();
			OutElapsedSeconds = Departure.ElapsedSeconds;
			if (OutCraftHalfLenCm != nullptr)
			{
				// The mesh knows its own size - the camera frames the
				// 18 m Cargo as honestly as the 14 m Scout.
				*OutCraftHalfLenCm =
					Departure.Component->Bounds.BoxExtent.X;
			}
			return true;
		}
	}
	return false;
}

void ALBSpacecraftWIPPresentationActor::ComputeLaunchCameraPose(
	float ElapsedSeconds, const FVector& ShipCm, float InChicaneSeconds,
	FVector& OutCameraCm, FVector& OutLookAtCm, float InCraftHalfLenCm)
{
	// Chicane: low side chase abeam the craft. Sprint: trailing crane
	// that deliberately loses ground so the ship pulls away. The two
	// poses blend across one second at the throttle-up boundary.
	// Offsets were framed for the 700 cm-half Scout; bigger craft push
	// the camera out proportionally so the hull never swallows it
	// (the Cargo-01 showcase caught the chase pose INSIDE the ship).
	const float Frame = FMath::Max(1.f, InCraftHalfLenCm / 700.f);
	const FVector ChasePose =
		ShipCm + FVector(1500.f, 350.f, 260.f) * Frame;
	const FVector CranePose =
		ShipCm + FVector(650.f, 2300.f, 820.f) * Frame;
	const float Blend = FMath::Clamp(
		(ElapsedSeconds - InChicaneSeconds) * 1.f + 0.5f, 0.f, 1.f);
	OutCameraCm = FMath::Lerp(ChasePose, CranePose,
		FMath::SmoothStep(0.f, 1.f, Blend));
	OutLookAtCm = ShipCm + FVector(0.f, 0.f, 160.f);
}

void ALBSpacecraftWIPPresentationActor::BindTrack(
	ALBSpacecraftTrackAuthority* InTrack)
{
	TrackAuthority = InTrack;
}

void ALBSpacecraftWIPPresentationActor::TickTrack(float DeltaSeconds)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	(void)DeltaSeconds;
	if (TrackAuthority == nullptr)
	{
		return;
	}
	// ONE CONTINUOUS BELT, not butted blocks (owner 2026-09-01: "think
	// you should make better track"). The benchmark conveyors read at
	// any zoom because they are one bold object; forty small pieces
	// with seams never will. The chain renders as a single smooth
	// spline - corners round themselves - with a pale sleeper rhythm
	// and the authored caps at the ends. Rebuilt only when the piece
	// set changes; the relayer rebuilds the chain wholesale anyway, so
	// piece-level diffing buys nothing.
	FString Signature;
	for (const FLBSpacecraftTrackPieceRecord& Piece :
		TrackAuthority->GetPieces())
	{
		Signature += Piece.PieceId.ToString();
		Signature += TEXT(";");
	}
	if (Signature == TrackRenderSignature)
	{
		return;
	}
	TrackRenderSignature = Signature;
	for (USplineMeshComponent* Segment : TrackSplineMeshes)
	{
		if (Segment != nullptr)
		{
			Segment->DestroyComponent();
		}
	}
	TrackSplineMeshes.Reset();
	for (UStaticMeshComponent* Cap : TrackCaps)
	{
		if (Cap != nullptr)
		{
			Cap->DestroyComponent();
		}
	}
	TrackCaps.Reset();
	if (TrackSleepers != nullptr)
	{
		TrackSleepers->ClearInstances();
	}
	const TArray<FLBSpacecraftTrackPieceRecord>& Pieces =
		TrackAuthority->GetPieces();
	if (Pieces.Num() < 2)
	{
		// A lone anchor piece has no run to draw yet.
		return;
	}
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr,
		SpacecraftCubePath);
	// Spline-flagged parent first; the engine shape material only as a
	// fallback so a missing asset degrades to the old SMU-fixup path
	// rather than an unrendered track.
	UMaterialInterface* ShapeMaterial = LoadObject<UMaterialInterface>(
		nullptr, SpacecraftSplineShapeMaterialPath);
	if (ShapeMaterial == nullptr)
	{
		ShapeMaterial = LoadObject<UMaterialInterface>(
			nullptr, SpacecraftShapeMaterialPath);
	}
	if (Cube == nullptr)
	{
		return;
	}
	if (TrackSpline == nullptr)
	{
		TrackSpline = NewObject<USplineComponent>(this,
			USplineComponent::StaticClass(), TEXT("TrackSpline"));
		TrackSpline->SetMobility(EComponentMobility::Movable);
		TrackSpline->SetupAttachment(RootComponent);
		TrackSpline->RegisterComponent();
	}
	TrackSpline->ClearSplinePoints(false);
	constexpr float BeltTopZCm = 22.f;
	for (const FLBSpacecraftTrackPieceRecord& Piece : Pieces)
	{
		TrackSpline->AddSplinePoint(
			Piece.WorldTransform.GetLocation()
				+ FVector(0.f, 0.f, BeltTopZCm),
			ESplineCoordinateSpace::World, false);
	}
	TrackSpline->UpdateSpline();
	const int32 SegmentCount = TrackSpline->GetNumberOfSplinePoints() - 1;
	for (int32 Index = 0; Index < SegmentCount; ++Index)
	{
		USplineMeshComponent* Belt = NewObject<USplineMeshComponent>(
			this, USplineMeshComponent::StaticClass());
		Belt->SetMobility(EComponentMobility::Movable);
		Belt->SetStaticMesh(Cube);
		Belt->SetForwardAxis(ESplineMeshAxis::X, false);
		Belt->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		// The dark albedo does the reading; a 40 cm slab's shadow is
		// z-band noise at management zoom.
		Belt->SetCastShadow(false);
		Belt->SetupAttachment(TrackSpline);
		Belt->RegisterComponent();
		if (ShapeMaterial != nullptr)
		{
			UMaterialInstanceDynamic* BeltMID =
				UMaterialInstanceDynamic::Create(ShapeMaterial, Belt);
			BeltMID->SetVectorParameterValue(TEXT("Color"),
				SpacecraftConveyorBed);
			Belt->SetMaterial(0, BeltMID);
		}
		Belt->SetStartAndEnd(
			TrackSpline->GetLocationAtSplinePoint(Index,
				ESplineCoordinateSpace::Local),
			TrackSpline->GetTangentAtSplinePoint(Index,
				ESplineCoordinateSpace::Local),
			TrackSpline->GetLocationAtSplinePoint(Index + 1,
				ESplineCoordinateSpace::Local),
			TrackSpline->GetTangentAtSplinePoint(Index + 1,
				ESplineCoordinateSpace::Local),
			false);
		// The engine cube is 100 cm: 6.5 across is a 650 cm belt, near
		// the craft's own width per the standing scale rule.
		Belt->SetStartScale(FVector2D(6.5f, 0.44f), false);
		Belt->SetEndScale(FVector2D(6.5f, 0.44f), false);
		Belt->UpdateMesh();
		TrackSplineMeshes.Add(Belt);
	}
	// Sleeper bars across the belt give it rhythm and scale - the
	// difference between a band of paint and a machine.
	if (TrackSleepers == nullptr)
	{
		TrackSleepers = NewObject<UInstancedStaticMeshComponent>(this,
			UInstancedStaticMeshComponent::StaticClass(),
			TEXT("TrackSleepers"));
		TrackSleepers->SetStaticMesh(Cube);
		TrackSleepers->SetMobility(EComponentMobility::Movable);
		TrackSleepers->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		TrackSleepers->SetCastShadow(false);
		TrackSleepers->SetupAttachment(RootComponent);
		TrackSleepers->RegisterComponent();
		if (ShapeMaterial != nullptr)
		{
			UMaterialInstanceDynamic* SleeperMID =
				UMaterialInstanceDynamic::Create(ShapeMaterial,
					TrackSleepers);
			SleeperMID->SetVectorParameterValue(TEXT("Color"),
				SpacecraftConveyorChevron);
			TrackSleepers->SetMaterial(0, SleeperMID);
		}
	}
	const float SplineLengthCm = TrackSpline->GetSplineLength();
	for (float Along = 150.f; Along < SplineLengthCm; Along += 260.f)
	{
		const FVector At = TrackSpline->GetLocationAtDistanceAlongSpline(
			Along, ESplineCoordinateSpace::World);
		const FRotator Facing =
			TrackSpline->GetRotationAtDistanceAlongSpline(Along,
				ESplineCoordinateSpace::World);
		TrackSleepers->AddInstance(FTransform(
			FRotator(0.f, Facing.Yaw, 0.f),
			FVector(At.X, At.Y, BeltTopZCm + 24.f),
			FVector(0.5f, 5.6f, 0.06f)), true);
	}
	// The authored terminators keep the ends honest: blue at the
	// anchor, warning orange at the cap.
	if (UStaticMesh* CapMesh = TryGetStationMesh(FName(TEXT("Track.Cap"))))
	{
		const float PieceLength =
			ALBSpacecraftTrackAuthority::GetPieceLengthCm();
		for (int32 End = 0; End < 2; ++End)
		{
			const bool bIsStart = End == 0;
			const FLBSpacecraftTrackPieceRecord& Piece =
				bIsStart ? Pieces[0] : Pieces.Last();
			if (UStaticMeshComponent* CapComp = MakeTrackPieceComponent(
				FName(*FString::Printf(TEXT("TrackCap_%d"), End)),
				CapMesh))
			{
				FTransform CapTransform = Piece.WorldTransform;
				const float CapOffset = PieceLength * 0.5f - 40.f;
				CapTransform.AddToTranslation(
					Piece.WorldTransform.GetRotation().RotateVector(
						FVector(bIsStart ? -CapOffset : CapOffset, 0.f,
							0.f)));
				if (bIsStart)
				{
					CapTransform.SetRotation((
						Piece.WorldTransform.Rotator()
							+ FRotator(0.f, 180.f, 0.f)).Quaternion());
					TintTrackCapForStart(CapComp);
				}
				CapComp->SetWorldTransform(CapTransform);
				TrackCaps.Add(CapComp);
			}
		}
	}
}

void ALBSpacecraftWIPPresentationActor::TickConveyors(
	float DeltaSeconds)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	(void)DeltaSeconds;
	if (BuildAuthority == nullptr)
	{
		return;
	}
	// Auto-connection (owner 2026-08-25): the belt path IS the stage
	// table. For each consecutive pair of route stages both present on
	// the floor, one belt runs first-placed station to first-placed
	// station. Placing or removing a station reroutes automatically.
	// Authority-owned belts win; the stage-table auto line is the
	// stand-in for a factory with no built belts yet.
	TArray<TPair<FName, FVector>> RouteStops;
	if (TransportAuthority != nullptr
		&& TransportAuthority->GetRoutes().Num() > 0)
	{
		for (const FLBSpacecraftBeltRoute& Route :
			TransportAuthority->GetRoutes())
		{
			for (const FVector& Point : Route.PathPointsCm)
			{
				RouteStops.Emplace(Route.RouteId, Point);
			}
		}
	}
	else
	for (const FLBSpacecraftStageDescriptor& Stage :
		FLBSpacecraftProductionCatalog::StageTable())
	{
		if (Stage.StationClassId.IsNone())
		{
			continue;
		}
		for (const FLBSpacecraftStationRecord& Record :
			BuildAuthority->GetStations())
		{
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			const FName StageClass = Definition != nullptr
				? (Definition->StageClassId.IsNone()
					? Definition->DefinitionId : Definition->StageClassId)
				: FName();
			if (StageClass == Stage.StationClassId)
			{
				RouteStops.Emplace(Record.StationId,
					Record.WorldTransform.GetLocation());
				break;
			}
		}
	}
	FString Revision;
	for (const TPair<FName, FVector>& Stop : RouteStops)
	{
		Revision += FString::Printf(TEXT("%s@%.0f,%.0f;"),
			*Stop.Key.ToString(), Stop.Value.X, Stop.Value.Y);
	}
	if (Revision != ConveyorRevision)
	{
		ConveyorRevision = Revision;
		for (FLBSpacecraftConveyorVisual& Belt : Conveyors)
		{
			if (Belt.Strip != nullptr) { Belt.Strip->DestroyComponent(); }
			for (UStaticMeshComponent* Part : Belt.Furniture)
			{
				if (Part != nullptr) { Part->DestroyComponent(); }
			}
			for (UStaticMeshComponent* Chevron : Belt.Chevrons)
			{
				if (Chevron != nullptr) { Chevron->DestroyComponent(); }
			}
		}
		Conveyors.Reset();
		for (int32 Index = 0; Index + 1 < RouteStops.Num(); ++Index)
		{
			// Review fix: never bridge two different routes - the
			// presenter draws only belts an authority owns.
			if (RouteStops[Index].Key != RouteStops[Index + 1].Key
				&& TransportAuthority != nullptr
				&& TransportAuthority->GetRoutes().Num() > 0)
			{
				continue;
			}
			const FVector Start = RouteStops[Index].Value;
			const FVector End = RouteStops[Index + 1].Value;
			const FVector Flat(End.X - Start.X, End.Y - Start.Y, 0.f);
			const float Span = Flat.Size();
			if (Span < 200.f)
			{
				continue; // stations touching: no belt to draw
			}
			FLBSpacecraftConveyorVisual Belt;
			Belt.StartCm = FVector(Start.X, Start.Y, 0.f);
			Belt.EndCm = FVector(End.X, End.Y, 0.f);
			// Premium furniture (owner 2026-08-25): elevated bed on
			// legs, steel side rails, drive units capping both ends.
			const FVector Mid = (Belt.StartCm + Belt.EndCm) * 0.5f;
			const FRotator Yaw = Flat.Rotation();
			const FVector Dir = Flat / Span;
			const FVector Side =
				FVector::CrossProduct(Dir, FVector::UpVector);
			const FName StripKey(*FString::Printf(TEXT("Belt_%d"), Index));
			Belt.Strip = MakeBlockComponent(StripKey, SpacecraftConveyorBed);
			if (Belt.Strip != nullptr)
			{
				Belt.Strip->SetWorldTransform(FTransform(Yaw,
					Mid + FVector(0.f, 0.f, SpacecraftBeltDeckZCm),
					FVector(Span / 100.f, 1.3f, 0.10f)));
			}
			for (int32 Rail = 0; Rail < 2; ++Rail)
			{
				const FName RailKey(*FString::Printf(
					TEXT("Belt_%d_Rail%d"), Index, Rail));
				if (UStaticMeshComponent* RailComp =
					MakeBlockComponent(RailKey, SpacecraftBeltRail))
				{
					RailComp->SetWorldTransform(FTransform(Yaw,
						Mid + Side * (Rail == 0 ? 72.f : -72.f)
							+ FVector(0.f, 0.f,
								SpacecraftBeltDeckZCm + 8.f),
						FVector(Span / 100.f, 0.14f, 0.22f)));
					Belt.Furniture.Add(RailComp);
				}
			}
			const int32 LegRows = FMath::Clamp(
				FMath::FloorToInt(Span / 500.f), 1, 30);
			for (int32 Leg = 0; Leg <= LegRows; ++Leg)
			{
				const FVector Along = Belt.StartCm
					+ Dir * (Span * Leg / FMath::Max(LegRows, 1));
				for (int32 LegSide = 0; LegSide < 2; ++LegSide)
				{
					const FName LegKey(*FString::Printf(
						TEXT("Belt_%d_Leg%d_%d"), Index, Leg, LegSide));
					if (UStaticMeshComponent* LegComp =
						MakeBlockComponent(LegKey, SpacecraftBeltRail))
					{
						LegComp->SetWorldTransform(FTransform(Yaw,
							Along + Side
								* (LegSide == 0 ? 60.f : -60.f)
								+ FVector(0.f, 0.f,
									SpacecraftBeltDeckZCm * 0.5f),
							FVector(0.12f, 0.12f,
								SpacecraftBeltDeckZCm / 100.f)));
						Belt.Furniture.Add(LegComp);
					}
				}
			}
			for (int32 Cap = 0; Cap < 2; ++Cap)
			{
				const FVector CapPos = (Cap == 0
					? Belt.StartCm : Belt.EndCm)
					+ FVector(0.f, 0.f, SpacecraftBeltDeckZCm + 6.f);
				const FName CapKey(*FString::Printf(
					TEXT("Belt_%d_Drive%d"), Index, Cap));
				if (UStaticMeshComponent* Drive =
					MakeBlockComponent(CapKey, SpacecraftDockIdle))
				{
					Drive->SetWorldTransform(FTransform(Yaw, CapPos,
						FVector(0.6f, 1.7f, 0.5f)));
					Belt.Furniture.Add(Drive);
				}
				const FName TrimKey(*FString::Printf(
					TEXT("Belt_%d_DriveTrim%d"), Index, Cap));
				if (UStaticMeshComponent* Trim =
					MakeBlockComponent(TrimKey, SpacecraftBeltAccent))
				{
					Trim->SetWorldTransform(FTransform(Yaw,
						CapPos + FVector(0.f, 0.f, 28.f),
						FVector(0.64f, 1.74f, 0.05f)));
					Belt.Furniture.Add(Trim);
				}
			}
			const int32 ChevronCount = FMath::Clamp(
				FMath::FloorToInt(Span / SpacecraftConveyorSpacingCm),
				1, 40);
			for (int32 Chevron = 0; Chevron < ChevronCount; ++Chevron)
			{
				const FName ChevronKey(*FString::Printf(
					TEXT("Belt_%d_Chev_%d"), Index, Chevron));
				UStaticMeshComponent* Stud = MakeBlockComponent(
					ChevronKey, SpacecraftConveyorChevron);
				if (Stud != nullptr)
				{
					// ACROSS the lane, like a sleeper under a rail -
					// the chevron was long-ways-on and pointed, which
					// is how a conveyor stud reads.
					Stud->SetWorldScale3D(FVector(0.22f, 1.5f, 0.06f));
					Belt.Chevrons.Add(Stud);
				}
			}
			Conveyors.Add(Belt);
		}
	}
	// THE SLEEPERS ARE LAID, NOT DRIVEN. This used to slide the whole
	// chevron train toward the next stage every frame, which is the one
	// thing a rail must not do - a moving surface says it is carrying
	// the craft, and the gantry is carrying the craft.
	//
	// ComputeConveyorChevronOffsetCm is still used, and still tested,
	// with its time term passed as ZERO: spacing down the lane was
	// always the useful half of that function, and the sleepers want
	// exactly the even spacing the chevrons had.
	for (FLBSpacecraftConveyorVisual& Belt : Conveyors)
	{
		const FVector Flat = Belt.EndCm - Belt.StartCm;
		const float Span = Flat.Size();
		if (Span < 1.f)
		{
			continue;
		}
		const FVector Direction = Flat / Span;
		const FRotator Yaw = Flat.Rotation();
		for (int32 Chevron = 0; Chevron < Belt.Chevrons.Num(); ++Chevron)
		{
			if (Belt.Chevrons[Chevron] == nullptr)
			{
				continue;
			}
			const float Offset = ComputeConveyorChevronOffsetCm(
				0.f, SpacecraftConveyorSpeedCmPerS, Span,
				Chevron, SpacecraftConveyorSpacingCm);
			Belt.Chevrons[Chevron]->SetWorldLocationAndRotation(
				Belt.StartCm + Direction * Offset
					+ FVector(0.f, 0.f, SpacecraftBeltDeckZCm + 8.f),
				Yaw.Quaternion());
		}
	}
}

void ALBSpacecraftWIPPresentationActor::TickRunways(float DeltaSeconds)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	(void)DeltaSeconds; // the shared accent clock drives the chase
	if (BuildAuthority == nullptr)
	{
		return;
	}
	// The runway is PERMANENT SITE FURNITURE (owner 2026-08-26): one
	// fixed strip the chicane swings every departing craft onto. It is
	// never player-built and never buildable over.
	TSet<FName> Live;
	{
		const FName SiteKey(TEXT("Site.Runway"));
		Live.Add(SiteKey);
		FLBSpacecraftRunwayVisual* Runway = Runways.Find(SiteKey);
		const FName RecordStationId = SiteKey;
		if (Runway == nullptr)
		{
			FLBSpacecraftRunwayVisual NewRunway;
			const FVector RigLocation(SiteRunwayXCm,
				SiteRunwayStartYCm, 0.f);
			const float StartY = SiteRunwayStartYCm;
			const float HalfW = RunwayWidthCm * 0.5f;
			auto MakePaint = [&](const TCHAR* Part, int32 Index,
				const FVector& Size, const FVector& Centre)
			{
				const FName Key(*FString::Printf(TEXT("%s_%s%d"),
					*RecordStationId.ToString(), Part, Index));
				UStaticMeshComponent* Component =
					MakeBlockComponent(Key, SpacecraftRunwayPaint);
				if (Component == nullptr)
				{
					return static_cast<UStaticMeshComponent*>(nullptr);
				}
				Component->SetWorldTransform(FTransform(
					FQuat::Identity, Centre,
					FVector(Size.X / 100.f, Size.Y / 100.f,
						Size.Z / 100.f)));
				NewRunway.Parts.Add(Component);
				return Component;
			};
			// The runway deck: five tileable strip sections (owner's
			// evening drop 2026-08-26) laid end to end; the painted
			// lines remain the honest fallback without the content.
			UStaticMesh* StripMesh =
				TryGetStationMesh(FName(TEXT("Site.RunwayStrip")));
			const float StripDeckTopCm = StripMesh != nullptr ? 90.f : 0.f;
			if (StripMesh != nullptr)
			{
				const float StripLen = 2000.f;
				const int32 Sections = FMath::Max(1,
					FMath::RoundToInt(RunwayLengthCm / StripLen));
				for (int32 Section = 0; Section < Sections; ++Section)
				{
					const FName StripKey(*FString::Printf(
						TEXT("%s_Strip%d"),
						*RecordStationId.ToString(), Section));
					if (UStaticMeshComponent* Strip =
						MakeTrackPieceComponent(StripKey, StripMesh))
					{
						// The mesh's long axis is X; the runway runs -Y.
						Strip->SetWorldTransform(FTransform(
							FRotator(0.f, 90.f, 0.f).Quaternion(),
							FVector(RigLocation.X,
								StartY - StripLen * Section
									- StripLen * 0.5f, 0.f),
							FVector::OneVector));
						NewRunway.Parts.Add(Strip);
					}
				}
			}
			else
			{
				// Edge lines, full length.
				for (int32 Side = 0; Side < 2; ++Side)
				{
					MakePaint(TEXT("Edge"), Side,
						FVector(20.f, RunwayLengthCm,
							SpacecraftRunwayPaintZCm),
						FVector(RigLocation.X
								+ (Side == 0 ? -HalfW : HalfW),
							StartY - RunwayLengthCm * 0.5f, 2.f));
				}
				// Centreline dashes.
				const float DashLen = 300.f;
				const float DashPitch = 450.f;
				const int32 DashCount =
					static_cast<int32>(RunwayLengthCm / DashPitch);
				for (int32 Dash = 0; Dash < DashCount; ++Dash)
				{
					MakePaint(TEXT("Dash"), Dash,
						FVector(30.f, DashLen, SpacecraftRunwayPaintZCm),
						FVector(RigLocation.X,
							StartY - DashPitch * Dash - DashLen * 0.5f,
							2.f));
				}
				// Threshold piano keys at the start.
				for (int32 KeyBar = 0; KeyBar < 6; ++KeyBar)
				{
					MakePaint(TEXT("Threshold"), KeyBar,
						FVector(90.f, 260.f, SpacecraftRunwayPaintZCm),
						FVector(RigLocation.X - HalfW + 110.f
								+ KeyBar * (RunwayWidthCm - 220.f) / 5.f,
							StartY - 150.f, 2.f));
				}
			}
			// The chicane gate: one pylon pair (owner's evening drop)
			// flanking the runway entry the craft swings through.
			if (UStaticMesh* PylonMesh =
				TryGetStationMesh(FName(TEXT("Site.ChicanePylon"))))
			{
				for (int32 Side = 0; Side < 2; ++Side)
				{
					const FName PylonKey(*FString::Printf(
						TEXT("%s_Pylon%d"),
						*RecordStationId.ToString(), Side));
					if (UStaticMeshComponent* Pylon =
						MakeTrackPieceComponent(PylonKey, PylonMesh))
					{
						Pylon->SetWorldTransform(FTransform(
							FQuat::Identity,
							FVector(RigLocation.X
									+ (Side == 0 ? -900.f : 900.f),
								StartY + 550.f, 0.f),
							FVector::OneVector));
						NewRunway.Parts.Add(Pylon);
					}
				}
			}
			// The hover-test pad sits at the threshold: the apron the
			// craft settles onto for its self-start before the sprint.
			if (UStaticMesh* PadMesh =
				TryGetStationMesh(FName(TEXT("Site.HoverPad"))))
			{
				const FName PadKey(*FString::Printf(
					TEXT("%s_HoverPad"),
					*RecordStationId.ToString()));
				if (UStaticMeshComponent* Pad =
					MakeTrackPieceComponent(PadKey, PadMesh))
				{
					Pad->SetWorldTransform(FTransform(FQuat::Identity,
						FVector(RigLocation.X, StartY + 1400.f, 2.f),
						FVector::OneVector));
					NewRunway.Parts.Add(Pad);
				}
			}
			// Red strobes down both edges, indexed toward the exit so the
			// chase runs the way the craft flies.
			const int32 Pairs = FMath::Max(RunwayStrobePairs, 2);
			for (int32 Pair = 0; Pair < Pairs; ++Pair)
			{
				for (int32 Side = 0; Side < 2; ++Side)
				{
					const FName Key(*FString::Printf(
						TEXT("%s_Strobe%d_%d"),
						*RecordStationId.ToString(), Pair, Side));
					UStaticMeshComponent* Strobe =
						MakeBlockComponent(Key, SpacecraftStrobeDim);
					if (Strobe == nullptr)
					{
						continue;
					}
					// On the authored deck the chase sits on the baked
					// pod line (strip half-width 720); painted runways
					// keep the old kerb offset.
					const float StrobeX = StripMesh != nullptr
						? 740.f : HalfW + 60.f;
					Strobe->SetWorldTransform(FTransform(
						FQuat::Identity,
						FVector(RigLocation.X
								+ (Side == 0 ? -StrobeX : StrobeX),
							StartY - (RunwayLengthCm / (Pairs - 0.5f))
								* Pair - 100.f,
							12.f + StripDeckTopCm),
						FVector(0.35f, 0.35f, 0.22f)));
					NewRunway.Parts.Add(Strobe);
					if (UMaterialInstanceDynamic* MID =
						Cast<UMaterialInstanceDynamic>(
							Strobe->GetMaterial(0)))
					{
						NewRunway.StrobeMIDs.Add(MID);
					}
				}
			}
			// LAUNCH TUBE (owner: "like Battlestar Galactica where the
			// Vipers launch"): rib frames march down the corridor with
			// overhead beams the craft flashes under, glowing guide
			// studs line the inside edges, one soft centre guide strip.
			const int32 RibCount = FMath::Max(2,
				static_cast<int32>(RunwayLengthCm / 2000.f));
			for (int32 Rib = 0; Rib < RibCount; ++Rib)
			{
				const float RibY = StartY - 900.f
					- (RunwayLengthCm - 1200.f)
						* Rib / FMath::Max(RibCount - 1, 1);
				for (int32 Side = 0; Side < 2; ++Side)
				{
					const FName PostKey(*FString::Printf(
						TEXT("%s_RibPost%d_%d"),
						*RecordStationId.ToString(), Rib, Side));
					if (UStaticMeshComponent* Post =
						MakeBlockComponent(PostKey, SpacecraftTubeRib))
					{
						Post->SetWorldTransform(FTransform(
							FQuat::Identity,
							FVector(RigLocation.X + (Side == 0
									? -HalfW - 160.f : HalfW + 160.f),
								RibY, 275.f),
							FVector(0.5f, 0.5f, 5.5f)));
						NewRunway.Parts.Add(Post);
					}
				}
				const FName BeamKey(*FString::Printf(TEXT("%s_RibBeam%d"),
					*RecordStationId.ToString(), Rib));
				if (UStaticMeshComponent* Beam =
					MakeBlockComponent(BeamKey, SpacecraftTubeRib))
				{
					Beam->SetWorldTransform(FTransform(FQuat::Identity,
						FVector(RigLocation.X, RibY, 570.f),
						FVector((2.f * (HalfW + 190.f)) / 100.f,
							0.5f, 0.4f)));
					NewRunway.Parts.Add(Beam);
				}
				const FName RibGlowKey(*FString::Printf(
					TEXT("%s_RibGlow%d"),
					*RecordStationId.ToString(), Rib));
				if (UStaticMeshComponent* RibGlow =
					MakeBlockComponent(RibGlowKey, SpacecraftChaseBright))
				{
					RibGlow->SetWorldTransform(FTransform(FQuat::Identity,
						FVector(RigLocation.X, RibY, 548.f),
						FVector((2.f * HalfW) / 100.f, 0.16f, 0.06f)));
					NewRunway.Parts.Add(RibGlow);
				}
			}
			// Guide studs inside both edges, indexed toward the exit.
			const int32 ChasePerSide = 20;
			for (int32 Stud = 0; Stud < ChasePerSide; ++Stud)
			{
				for (int32 Side = 0; Side < 2; ++Side)
				{
					const FName StudKey(*FString::Printf(
						TEXT("%s_Chase%d_%d"),
						*RecordStationId.ToString(), Stud, Side));
					UStaticMeshComponent* StudComp =
						MakeBlockComponent(StudKey, SpacecraftChaseDim);
					if (StudComp == nullptr)
					{
						continue;
					}
					StudComp->SetWorldTransform(FTransform(
						FQuat::Identity,
						FVector(RigLocation.X + (Side == 0
								? -HalfW + 90.f : HalfW - 90.f),
							StartY - (RunwayLengthCm / ChasePerSide)
								* Stud - 200.f, 10.f),
						FVector(0.24f, 0.24f, 0.14f)));
					NewRunway.Parts.Add(StudComp);
					if (UMaterialInstanceDynamic* MID =
						Cast<UMaterialInstanceDynamic>(
							StudComp->GetMaterial(0)))
					{
						NewRunway.ChaseMIDs.Add(MID);
					}
				}
			}
			// Centre guide strip, one soft piece full length.
			const FName GuideKey(*FString::Printf(TEXT("%s_Guide"),
				*RecordStationId.ToString()));
			if (UStaticMeshComponent* Guide =
				MakeBlockComponent(GuideKey, SpacecraftChaseDim))
			{
				Guide->SetWorldTransform(FTransform(FQuat::Identity,
					FVector(RigLocation.X,
						StartY - RunwayLengthCm * 0.5f, 1.f),
					FVector(0.5f, RunwayLengthCm / 100.f, 0.03f)));
				NewRunway.Parts.Add(Guide);
			}
			Runway = &Runways.Add(SiteKey, NewRunway);
		}
		// Strobes are an EVENT, not wallpaper: dark until a departing
		// craft is about to throttle up, then the chase runs from the rig
		// toward the exit for the rest of the flight.
		float ArmClock = -1.f;
		for (const FLBSpacecraftDepartingVisual& Departure : Departing)
		{
			ArmClock = FMath::Max(ArmClock, ComputeStrobeArmClock(
				Departure.ElapsedSeconds, ChicaneSeconds,
				RunwayStrobeLeadSeconds));
		}
		// MIDs are stored pair-major, both sides of a pair flash together.
		for (int32 Index = 0; Index < Runway->StrobeMIDs.Num(); ++Index)
		{
			const int32 Pairs = FMath::Max(RunwayStrobePairs, 2);
			const float Intensity = ArmClock >= 0.f
				? ComputeStrobeIntensity01(ArmClock, Index / 2, Pairs,
					RunwayStrobeChaseSeconds)
				: 0.f;
			if (Runway->StrobeMIDs[Index] != nullptr)
			{
				Runway->StrobeMIDs[Index]->SetVectorParameterValue(
					TEXT("Color"),
					FMath::Lerp(SpacecraftStrobeDim, SpacecraftStrobeHot,
						Intensity));
			}
		}
		// The launch tube breathes: guide studs crawl slowly at rest
		// and RACE toward the exit while a craft sprints (Viper-tube
		// chase, owner 2026-08-25).
		const bool bLaunching = ArmClock >= 0.f;
		const float StudsPerSecond = bLaunching ? 14.f : 2.f;
		for (int32 Index = 0; Index < Runway->ChaseMIDs.Num(); ++Index)
		{
			if (Runway->ChaseMIDs[Index] == nullptr)
			{
				continue;
			}
			// Stored side-major per stud pair; both sides pulse together.
			const float Intensity = ComputeChaseIntensity01(
				AccentClockSeconds, Index / 2,
				FMath::Max(Runway->ChaseMIDs.Num() / 2, 1),
				StudsPerSecond);
			const float Scaled = bLaunching
				? Intensity : Intensity * 0.35f;
			Runway->ChaseMIDs[Index]->SetVectorParameterValue(
				TEXT("Color"), FMath::Lerp(SpacecraftChaseDim,
					SpacecraftChaseBright, Scaled));
		}
	}
	// A removed rig takes its runway with it.
	for (auto It = Runways.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			for (UStaticMeshComponent* Part : It.Value().Parts)
			{
				if (Part != nullptr)
				{
					Part->DestroyComponent();
				}
			}
			It.RemoveCurrent();
		}
	}
}

float ALBSpacecraftWIPPresentationActor::GetDroneWorkAlpha(
	FName StationId) const
{
	const FLBSpacecraftDroneVisual* Visual = DroneVisuals.Find(StationId);
	return Visual != nullptr ? Visual->WorkAlpha : 0.f;
}

float ALBSpacecraftWIPPresentationActor::ComputeWeldFlicker01(
	float ClockSeconds, int32 Seed)
{
	// Three incommensurate sines beat against each other: bright arc
	// with irregular dips, fully deterministic.
	const float Phase = ClockSeconds * 31.7f + Seed * 2.3f;
	const float Value = 0.62f
		+ 0.22f * FMath::Sin(Phase)
		+ 0.11f * FMath::Sin(Phase * 2.63f + 1.4f)
		+ 0.05f * FMath::Sin(Phase * 7.19f + 0.6f);
	return FMath::Clamp(Value, 0.f, 1.f);
}

FVector ALBSpacecraftWIPPresentationActor::ComputeSparkOffsetCm(
	float ClockSeconds, int32 Index, float& OutAlive01)
{
	// Each spark loops a 0.45 s flight, staggered by index; heading is
	// a hash of (index, cycle) so bursts vary without RNG.
	const float Lifetime = 0.45f;
	const float Staggered = ClockSeconds + Index * 0.13f;
	const int32 Cycle = FMath::FloorToInt(Staggered / Lifetime);
	const float T = FMath::Fmod(Staggered, Lifetime) / Lifetime;
	OutAlive01 = 1.f - T;
	const uint32 Hash = ::GetTypeHash(Index * 7919 + Cycle * 104729);
	const float Yaw = (Hash % 360u) * PI / 180.f;
	const float Speed = 180.f + (Hash % 97u);
	const float Up = 120.f * T - 420.f * T * T; // droop under gravity
	return FVector(FMath::Cos(Yaw) * Speed * T,
		FMath::Sin(Yaw) * Speed * T, Up);
}

float ALBSpacecraftWIPPresentationActor::ComputeChaseIntensity01(
	float ClockSeconds, int32 Index, int32 Count, float StudsPerSecond)
{
	if (Count <= 0)
	{
		return 0.f;
	}
	const float Head = FMath::Fmod(ClockSeconds * StudsPerSecond,
		static_cast<float>(Count));
	float Distance = Head - static_cast<float>(Index);
	if (Distance < 0.f)
	{
		Distance += Count; // the pulse only trails, it never leads
	}
	// Bright head with a three-stud fading tail.
	return FMath::Clamp(1.f - Distance / 3.f, 0.12f, 1.f);
}

float ALBSpacecraftWIPPresentationActor::ComputeConveyorChevronOffsetCm(
	float ClockSeconds, float SpeedCmPerS, float SpanCm, int32 Index,
	float SpacingCm)
{
	if (SpanCm <= 1.f)
	{
		return 0.f;
	}
	const float Raw = ClockSeconds * SpeedCmPerS
		+ static_cast<float>(Index) * SpacingCm;
	return FMath::Fmod(Raw, SpanCm);
}

FRotator ALBSpacecraftWIPPresentationActor::ComputeFanTiltDeg(
	const FVector& VelocityCmPerS, float MaxTiltDeg)
{
	// Pods lean INTO the motion: forward (+X) velocity pitches the pod
	// nose-down, sideways (+Y) velocity rolls it. Full lean at 600 cm/s.
	const float FullLeanCmPerS = 600.f;
	const float Pitch = FMath::Clamp(
		-VelocityCmPerS.X / FullLeanCmPerS, -1.f, 1.f) * MaxTiltDeg;
	const float Roll = FMath::Clamp(
		VelocityCmPerS.Y / FullLeanCmPerS, -1.f, 1.f) * MaxTiltDeg;
	return FRotator(Pitch, 0.f, Roll);
}

float ALBSpacecraftWIPPresentationActor::ComputeSpinnerAngleDeg(
	float PriorAngleDeg, float DeltaSeconds, float Speed01,
	float DegPerSecondAtFullSpeed)
{
	const float Advance = FMath::Clamp(Speed01, 0.f, 1.f)
		* DegPerSecondAtFullSpeed * DeltaSeconds;
	return FMath::Fmod(PriorAngleDeg + Advance, 360.f);
}

float ALBSpacecraftWIPPresentationActor::ComputeWheelRollDeg(
	float PriorAngleDeg, float DeltaSeconds, float SpeedCmPerS,
	float WheelRadiusCm)
{
	if (WheelRadiusCm <= 0.f)
	{
		return PriorAngleDeg;
	}
	// angle = distance / radius (radians), converted to degrees. Signed
	// speed rolls the wheel backward for reverse travel rather than
	// always spinning forward.
	const float DistanceCm = SpeedCmPerS * DeltaSeconds;
	const float AdvanceDeg = FMath::RadiansToDegrees(DistanceCm
		/ WheelRadiusCm);
	return FMath::Fmod(PriorAngleDeg + AdvanceDeg, 360.f);
}

FVector ALBSpacecraftWIPPresentationActor::ComputeRotatedPartRelativeLocation(
	const FVector& PivotLocal, const FRotator& SpinRotation)
{
	// A component rendered with RelativeLocation L and RelativeRotation
	// R places mesh-local vertex V at L + R*V. Baked geometry already
	// sits at V (correct, unrotated); to make it read as spinning
	// AROUND its own pivot P rather than around the component's origin,
	// the rendered position for every vertex must become
	// P + R*(V-P) = (P - R*P) + R*V. Matching that to L + R*V gives
	// L = P - R*P, recomputed every tick since it depends on R.
	return PivotLocal - SpinRotation.RotateVector(PivotLocal);
}

float ALBSpacecraftWIPPresentationActor::ComputeRotorLoad01(
	bool bDocked, bool bCarrying, bool bFitting)
{
	// Docked wins over everything: a drone on its pad has its motors
	// off, whatever else it might be flagged as.
	if (bDocked)
	{
		return 0.f;
	}
	if (bCarrying)
	{
		// Carrying a part means lifting its mass as well as the drone's,
		// so the motors are working hardest here. This is the whole
		// point of driving sound from load rather than from motion: the
		// floor audibly gets busier when parts are actually moving.
		return 1.f;
	}
	if (bFitting)
	{
		// Station-keeping over the work, holding position precisely.
		return 0.85f;
	}
	// Empty transit: enough to fly, no payload.
	return 0.72f;
}

float ALBSpacecraftWIPPresentationActor::ComputeRotorSpeed01(
	float Current, float Target, float DeltaSeconds,
	float SpoolUpSeconds, float SpoolDownSeconds)
{
	Current = FMath::Clamp(Current, 0.f, 1.f);
	Target = FMath::Clamp(Target, 0.f, 1.f);
	if (DeltaSeconds <= 0.f)
	{
		return Current;
	}
	const float Tau = Target > Current ? SpoolUpSeconds : SpoolDownSeconds;
	if (Tau <= 0.f)
	{
		// No time constant given: snap. Refusing to divide beats
		// producing an infinity that would ride into the pitch.
		return Target;
	}
	// Exponential approach rather than a fixed step per frame, so the
	// spool takes the same wall-clock time at 30 fps and at 144.
	const float Alpha = 1.f - FMath::Exp(-DeltaSeconds / Tau);
	return FMath::Clamp(FMath::Lerp(Current, Target, Alpha), 0.f, 1.f);
}

float ALBSpacecraftWIPPresentationActor::ComputeRotorPitch(
	float Speed01, float MinPitch, float MaxPitch)
{
	return FMath::Lerp(MinPitch, MaxPitch,
		FMath::Clamp(Speed01, 0.f, 1.f));
}

float ALBSpacecraftWIPPresentationActor::ComputeRotorVolume01(
	float Speed01)
{
	const float Speed = FMath::Clamp(Speed01, 0.f, 1.f);
	// Quadratic: a half-speed rotor is a quarter as loud. Linear would
	// leave a floor of idling drones humming as one continuous drone.
	return Speed * Speed;
}

float ALBSpacecraftWIPPresentationActor::GetDroneRotorSpeed01(
	FName StationId, int32 DroneIndex) const
{
	const FLBSpacecraftDroneVisual* Visual = DroneVisuals.Find(StationId);
	if (Visual == nullptr || !Visual->RotorSpeeds.IsValidIndex(DroneIndex))
	{
		return 0.f;
	}
	return Visual->RotorSpeeds[DroneIndex];
}

int32 ALBSpacecraftWIPPresentationActor::GetRotorAudioCount() const
{
	int32 Count = 0;
	for (const TPair<FName, FLBSpacecraftDroneVisual>& Pair : DroneVisuals)
	{
		for (UAudioComponent* Audio : Pair.Value.RotorAudio)
		{
			if (Audio != nullptr)
			{
				++Count;
			}
		}
	}
	return Count;
}

FVector ALBSpacecraftWIPPresentationActor::ComputeDroneWorkOffsetCm(
	float ClockSeconds, int32 DroneIndex, float OrbitRadiusCm,
	float HoverHeightCm)
{
	const float Phase = DroneIndex * PI; // half a turn apart
	// The orbit breathes in toward the workpiece and back out - the
	// "fitting parts" motion - while the whole drone bobs gently.
	const float Radius = OrbitRadiusCm
		* (0.55f + 0.45f * FMath::Cos(ClockSeconds * 0.7f + Phase));
	const float Angle = ClockSeconds * 0.9f + Phase;
	return FVector(Radius * FMath::Cos(Angle),
		Radius * FMath::Sin(Angle),
		HoverHeightCm + 55.f * FMath::Sin(ClockSeconds * 1.7f + Phase));
}

float ALBSpacecraftWIPPresentationActor::ComputeCraneCarryCm(
	float Progress01, float SlideStart, float CarryCm)
{
	// Parked: the craft sits on its cradle and the crane is not on it.
	if (Progress01 <= SlideStart)
	{
		return 0.f;
	}
	// Remap the slide window onto 0..1 and reuse the station lift's
	// rise-hold-fall shape rather than writing a second one. They are
	// the same motion at different scales, and one of them is already
	// covered by tests.
	const float Alpha = (Progress01 - SlideStart)
		/ FMath::Max(1.f - SlideStart, 0.01f);
	return ComputeStationLiftCm(Alpha, CarryCm, 0.25f);
}

float ALBSpacecraftWIPPresentationActor::ComputeStationLiftCm(
	float Progress01, float RaisedCm, float RiseFraction)
{
	const float Rise = FMath::Clamp(RiseFraction, 0.01f, 0.49f);
	const float T = FMath::Clamp(Progress01, 0.f, 1.f);
	if (T < Rise)
	{
		return RaisedCm * FMath::SmoothStep(0.f, 1.f, T / Rise);
	}
	if (T > 1.f - Rise)
	{
		return RaisedCm * FMath::SmoothStep(0.f, 1.f, (1.f - T) / Rise);
	}
	return RaisedCm;   // held up, which is when the work happens
}

FVector ALBSpacecraftWIPPresentationActor::ComputeGroundDroneWorkOffsetCm(
	float ClockSeconds, int32 DroneIndex, float RunHalfLengthCm,
	float LaneOffsetCm)
{
	// A wheeled drone works UNDER the craft, so it does the one thing a
	// flier cannot: it drives the length of the belly. The run is a
	// slow shuttle along the line axis; the lane keeps two of them from
	// occupying the same strip of floor. Z is zero, always - wheels do
	// not leave the ground, and the caller must not lift it.
	const float Phase = DroneIndex * 1.3f;
	const float Along = RunHalfLengthCm
		* FMath::Sin(ClockSeconds * 0.35f + Phase);
	const float Lane = (DroneIndex % 2 == 0 ? 1.f : -1.f) * LaneOffsetCm;
	return FVector(Along, Lane, 0.f);
}

float ALBSpacecraftWIPPresentationActor::ComputeGroundDroneYawDeg(
	float ClockSeconds, int32 DroneIndex)
{
	// The run is a sine along X, so its velocity is the cosine: the
	// drone faces +X on the way out and -X on the way back. Taking the
	// yaw from the same expression that moves it means the wheels can
	// never point the wrong way.
	const float Phase = DroneIndex * 1.3f;
	return FMath::Cos(ClockSeconds * 0.35f + Phase) >= 0.f ? 0.f : 180.f;
}

FString ALBSpacecraftWIPPresentationActor::ComputeDroneCrewRevision(
	const TArray<FName>& InstalledKinds, int32 InstalledDrones)
{
	// The hired kinds in slot order identify the crew exactly. The
	// count is included so a station whose kinds were never recorded
	// (a save from before kinds existed) still rebuilds when it grows.
	FString Revision = FString::Printf(TEXT("n%d"), InstalledDrones);
	for (const FName& KindId : InstalledKinds)
	{
		Revision += TEXT("|") + KindId.ToString();
	}
	return Revision;
}

void ALBSpacecraftWIPPresentationActor::GetDronePartsManifest(FName Crew,
	TArray<FLBSpacecraftDronePartSpec>& OutParts)
{
	OutParts.Reset();
	// CONCEPT-DRIVEN BATCH (2026-08-31): CargoLift, Assembly and
	// GroundLifter now wear single JOINED meshes from the TRELLIS
	// pipeline (rotors and arms welded into the body). Their old
	// DroneBatch part manifests must return EMPTY or the spinners and
	// arms would be attached a second time over the welded copies. The
	// cost is rotor spin on these three crews until articulated
	// versions exist; the other four crews keep their moving parts.
	if (Crew == FName(TEXT("CargoLift"))
		|| Crew == FName(TEXT("Assembly"))
		|| Crew == FName(TEXT("GroundLifter")))
	{
		return;
	}
	FString Stem;
	if (Crew == FName(TEXT("CargoLift"))) { Stem = TEXT("cargolift_v001"); }
	else if (Crew == FName(TEXT("Assembly"))) { Stem = TEXT("assembly_v001"); }
	else if (Crew == FName(TEXT("Spray"))) { Stem = TEXT("spray_v001"); }
	else if (Crew == FName(TEXT("Winch"))) { Stem = TEXT("winch_v001"); }
	else if (Crew == FName(TEXT("GroundLifter"))) { Stem = TEXT("ground_lifter_v001"); }
	else if (Crew == FName(TEXT("GroundAssembly"))) { Stem = TEXT("ground_assembly_v001"); }
	else if (Crew == FName(TEXT("GroundSprayer"))) { Stem = TEXT("ground_sprayer_v001"); }
	else { return; }

	// Reproduces the Blender processing lane's rename convention
	// exactly (process_drone_batch_v001.py): the first occurrence of a
	// named part keeps its bare name, every repeat after it gets a
	// "_N" suffix counting from 1 - never Blender's own ".001" dedup
	// suffix, which does not survive the GLB round-trip into Unreal.
	auto AddNumbered = [&OutParts, &Stem](const TCHAR* BaseName,
		int32 Count, ELBSpacecraftDronePartKind Kind)
	{
		for (int32 Index = 0; Index < Count; ++Index)
		{
			const FString PartName = Index == 0
				? FString::Printf(TEXT("%s_%s"), *Stem, BaseName)
				: FString::Printf(TEXT("%s_%s_%d"), *Stem, BaseName, Index);
			FLBSpacecraftDronePartSpec Spec;
			Spec.AssetPath = FString::Printf(
				TEXT("/Game/LineBoss/Candidates/Spacecraft/DroneBatch_v001/")
				TEXT("%s/%s/StaticMeshes/%s.%s"),
				*Stem, *Stem, *PartName, *PartName);
			Spec.Kind = Kind;
			OutParts.Add(MoveTemp(Spec));
		}
	};

	using EKind = ELBSpacecraftDronePartKind;
	if (Crew == FName(TEXT("CargoLift")))
	{
		// Hexacopter: six rotor units, each a spinning blade on a
		// static housing/arm.
		AddNumbered(TEXT("rotor_unit_spinner_mesh"), 6, EKind::Spinner);
		AddNumbered(TEXT("rotor_unit_mesh"), 6, EKind::Static);
	}
	else if (Crew == FName(TEXT("Assembly")))
	{
		// Quadcopter plus a fitting arm (shoulder->elbow->wrist->
		// gripper). Only the rotors animate this pass; the arm is
		// spawned correctly but held static (see the struct comment on
		// StaticParts for why).
		AddNumbered(TEXT("rotor_unit_spinner_mesh"), 4, EKind::Spinner);
		AddNumbered(TEXT("rotor_unit_mesh"), 4, EKind::Static);
		AddNumbered(TEXT("elbow_joint_mesh"), 2, EKind::Static);
		AddNumbered(TEXT("gripper_mesh"), 2, EKind::Static);
		AddNumbered(TEXT("upper_arm_link_mesh"), 2, EKind::Static);
		AddNumbered(TEXT("wrist_joint_mesh"), 2, EKind::Static);
		AddNumbered(TEXT("manipulator_arm_left_mesh"), 1, EKind::Static);
		AddNumbered(TEXT("manipulator_arm_right_mesh"), 1, EKind::Static);
	}
	else if (Crew == FName(TEXT("Spray")))
	{
		// Quadcopter with a spinning blade per rotor (housing tilts
		// with ComputeFanTiltDeg the way the block fallback's Pods
		// already do - not yet wired for these named parts, deferred
		// alongside legs) and four retractable landing legs.
		AddNumbered(TEXT("rotor_spinner_mesh"), 4, EKind::Spinner);
		AddNumbered(TEXT("rotor_tilt_mesh"), 4, EKind::Static);
		AddNumbered(TEXT("landing_leg_swing_mesh"), 4, EKind::Static);
	}
	else if (Crew == FName(TEXT("Winch")))
	{
		AddNumbered(TEXT("rotor_spinner_mesh"), 4, EKind::Spinner);
		AddNumbered(TEXT("rotor_tilt_mesh"), 4, EKind::Static);
		AddNumbered(TEXT("landing_leg_swing_mesh"), 4, EKind::Static);
		AddNumbered(TEXT("hook_block_mesh"), 1, EKind::Static);
		AddNumbered(TEXT("winch_drum_mesh"), 1, EKind::Static);
	}
	else if (Crew == FName(TEXT("GroundLifter")))
	{
		// Four wheels (tyre + spinning hub, both rolled together) on a
		// bogie suspension, a scissor lift table on four rams.
		AddNumbered(TEXT("wheel_mesh"), 4, EKind::Wheel);
		AddNumbered(TEXT("wheel_hub_spin_mesh"), 4, EKind::Wheel);
		AddNumbered(TEXT("suspension_damper_travel_mesh"), 4, EKind::Static);
		AddNumbered(TEXT("lift_ram_travel_mesh"), 4, EKind::Static);
		AddNumbered(TEXT("lift_table_mesh"), 1, EKind::Static);
	}
	else if (Crew == FName(TEXT("GroundSprayer")))
	{
		AddNumbered(TEXT("wheel_mesh"), 4, EKind::Wheel);
		AddNumbered(TEXT("wheel_hub_spin_mesh"), 4, EKind::Wheel);
		AddNumbered(TEXT("suspension_damper_travel_mesh"), 4, EKind::Static);
		AddNumbered(TEXT("outrigger_jack_travel_mesh"), 4, EKind::Static);
		AddNumbered(TEXT("gantry_ram_travel_mesh"), 1, EKind::Static);
		AddNumbered(TEXT("spray_gantry_mesh"), 1, EKind::Static);
	}
	else if (Crew == FName(TEXT("GroundAssembly")))
	{
		// Six-wheeled bogie rover with a turret-mounted arm and a tool
		// carousel; the fastener spindle is the one part on this drone
		// that IS a genuine spinner (a chucked bit), not an arm joint.
		AddNumbered(TEXT("wheel_mesh"), 6, EKind::Wheel);
		AddNumbered(TEXT("wheel_hub_spin_mesh"), 6, EKind::Wheel);
		AddNumbered(TEXT("bogie_damper_travel_mesh"), 6, EKind::Static);
		AddNumbered(TEXT("elbow_joint_mesh"), 1, EKind::Static);
		AddNumbered(TEXT("elbow_ram_travel_mesh"), 1, EKind::Static);
		AddNumbered(TEXT("fastener_spindle_spinner_mesh"), 1, EKind::Spinner);
		AddNumbered(TEXT("shoulder_ram_travel_mesh"), 1, EKind::Static);
		AddNumbered(TEXT("tool_carousel_mesh"), 1, EKind::Static);
		AddNumbered(TEXT("turret_mesh"), 1, EKind::Static);
		AddNumbered(TEXT("upper_arm_link_mesh"), 1, EKind::Static);
		AddNumbered(TEXT("work_mast_mesh"), 1, EKind::Static);
		AddNumbered(TEXT("wrist_joint_mesh"), 1, EKind::Static);
	}
}

void ALBSpacecraftWIPPresentationActor::GetKitPalletCandidates(
	FName ComponentId, TArray<FName>& OutPalletKeys)
{
	OutPalletKeys.Reset();
	// The hull is cut into four real sections and Propulsion into
	// three - both get a variety pool. Everything else PalletLoads_v001
	// covers has exactly one pallet. Hull's four are the actual fuselage
	// SECTIONS (nose->fwd->mid->aft) - owner, 2026-08-30: "the hull
	// parts need to be put together", so ShouldAssembleKitPalletsTogether
	// (below) has these spawn as one nose-to-aft sequence rather than
	// standing in for each other. Wing/wing_port/canopy are deliberately
	// NOT in this list: they are separate ship parts, not sections of
	// the same fuselage run, and forcing them into the sequence would
	// misrepresent "put together" as "everything hull-adjacent".
	if (ComponentId == FName(TEXT("Component.Hull")))
	{
		OutPalletKeys = { FName(TEXT("Pallet.pallet-hull_nose")),
			FName(TEXT("Pallet.pallet-hull_fwd")),
			FName(TEXT("Pallet.pallet-hull_mid")),
			FName(TEXT("Pallet.pallet-hull_aft")) };
	}
	else if (ComponentId == FName(TEXT("Component.Propulsion")))
	{
		OutPalletKeys = { FName(TEXT("Pallet.pallet-booster")),
			FName(TEXT("Pallet.pallet-booster_port")),
			FName(TEXT("Pallet.pallet-mainengine")) };
	}
	else if (ComponentId == FName(TEXT("Component.Power")))
	{
		OutPalletKeys = { FName(TEXT("Pallet.pallet-cellbank")) };
	}
	else if (ComponentId == FName(TEXT("Component.Electronics")))
	{
		OutPalletKeys = { FName(TEXT("Pallet.pallet-avionics")) };
	}
	else if (ComponentId == FName(TEXT("Component.Navigation")))
	{
		OutPalletKeys = { FName(TEXT("Pallet.pallet-sensor")) };
	}
	else if (ComponentId == FName(TEXT("Component.Interior")))
	{
		OutPalletKeys = { FName(TEXT("Pallet.pallet-interior")) };
	}
}

int32 ALBSpacecraftWIPPresentationActor::ComputeKitPalletCandidateIndex(
	FName StationId, int32 BayIndex, int32 CandidateCount)
{
	if (CandidateCount <= 0)
	{
		return INDEX_NONE;
	}
	// GetTypeHash rather than a running counter: stable regardless of
	// build/load order, and two different stations fitting the same
	// component do not land on the same pallet just because they were
	// built in the same sequence.
	const uint32 Hash = HashCombine(GetTypeHash(StationId),
		GetTypeHash(BayIndex));
	return static_cast<int32>(Hash % static_cast<uint32>(CandidateCount));
}

bool ALBSpacecraftWIPPresentationActor::ShouldAssembleKitPalletsTogether(
	FName ComponentId)
{
	return ComponentId == FName(TEXT("Component.Hull"));
}

void ALBSpacecraftWIPPresentationActor::ComputeSequentialLayoutCentresCm(
	const TArray<float>& LengthsCm, TArray<float>& OutCentresCm)
{
	OutCentresCm.Reset();
	float TotalLengthCm = 0.f;
	for (const float LengthCm : LengthsCm)
	{
		TotalLengthCm += LengthCm;
	}
	float CursorY = -TotalLengthCm * 0.5f;
	for (const float LengthCm : LengthsCm)
	{
		OutCentresCm.Add(CursorY + LengthCm * 0.5f);
		CursorY += LengthCm;
	}
}

void ALBSpacecraftWIPPresentationActor::GetShipNodes(FName RecipeId,
	TArray<FLBSpacecraftShipNode>& OutNodes)
{
	OutNodes.Reset();
	// SCOUT-01: the six-assembly model's own modelling brief already
	// pre-aligns every part in one shared coordinate space (Hull is the
	// primary; the other five slot in at Identity), so every node here
	// is Identity too - this table does not change what gets rendered
	// today, it names the assumption so a future part that is NOT
	// pre-aligned can define a real offset without any attach call site
	// needing to change.
	if (RecipeId == LBSpacecraftWIPPresentationPrivate::SpacecraftScoutRecipeId)
	{
		OutNodes.Add({ FName(TEXT("Node.Hull")), FTransform::Identity });
		OutNodes.Add({ FName(TEXT("Node.Propulsion")), FTransform::Identity });
		OutNodes.Add({ FName(TEXT("Node.Power")), FTransform::Identity });
		OutNodes.Add({ FName(TEXT("Node.Electronics")),
			FTransform::Identity });
		OutNodes.Add({ FName(TEXT("Node.Navigation")),
			FTransform::Identity });
		OutNodes.Add({ FName(TEXT("Node.Interior")), FTransform::Identity });
	}
}

bool ALBSpacecraftWIPPresentationActor::FindShipNodeTransform(
	FName RecipeId, FName NodeId, FTransform& OutTransform)
{
	OutTransform = FTransform::Identity;
	TArray<FLBSpacecraftShipNode> Nodes;
	GetShipNodes(RecipeId, Nodes);
	for (const FLBSpacecraftShipNode& Node : Nodes)
	{
		if (Node.NodeId == NodeId)
		{
			OutTransform = Node.RelativeTransform;
			return true;
		}
	}
	return false;
}

void ALBSpacecraftWIPPresentationActor::DestroyDroneVisual(
	FLBSpacecraftDroneVisual& Visual)
{
	const TArray<UStaticMeshComponent*>* Groups[] = {
		&Visual.Drones, &Visual.Pods, &Visual.Crates, &Visual.NavLights,
		&Visual.WorkLights, &Visual.Beams, &Visual.Flashes,
		&Visual.Sparks, &Visual.Docks, &Visual.DockModels,
		&Visual.Spinners, &Visual.Wheels, &Visual.StaticParts };
	for (const TArray<UStaticMeshComponent*>* Group : Groups)
	{
		for (UStaticMeshComponent* Part : *Group)
		{
			if (Part != nullptr) { Part->DestroyComponent(); }
		}
	}
	// Rotor voices must be STOPPED as well as destroyed, and destroyed
	// explicitly: they hang off the drone body, and destroying a parent
	// component detaches its children rather than destroying them. Left
	// out, removing a station would leave its rotors buzzing on an
	// empty slab.
	for (UAudioComponent* Rotors : Visual.RotorAudio)
	{
		if (Rotors != nullptr)
		{
			Rotors->Stop();
			Rotors->DestroyComponent();
		}
	}
}

// The game mode's LogLBSpacecraft is file-static to that translation
// unit; the presenter needs its own, named for its subject so the unity
// build cannot collide it with another file's.
DEFINE_LOG_CATEGORY_STATIC(LogLBSpacecraftPresenter, Log, All);

void ALBSpacecraftWIPPresentationActor::LogDroneCrew() const
{
	if (BuildAuthority == nullptr)
	{
		UE_LOG(LogLBSpacecraftPresenter, Warning,
			TEXT("DRONES: no build authority bound"));
		return;
	}
	// The CRAFT and the STATIONS too: a drone is only legible against
	// what it is standing next to, and a framing that looked wrong is
	// answered by measuring, not by squinting at a screenshot.
	for (const TPair<FName, TObjectPtr<UStaticMeshComponent>>& Pair :
		UnitVisuals)
	{
		if (Pair.Value == nullptr) { continue; }
		const FVector Extent = Pair.Value->Bounds.BoxExtent;
		UE_LOG(LogLBSpacecraftPresenter, Display,
			TEXT("CRAFT %s at (%.0f,%.0f,%.0f) size=(%.0f x %.0f x %.0f) ")
			TEXT("cm mesh=%s scale=%s"),
			*Pair.Key.ToString(),
			Pair.Value->GetComponentLocation().X,
			Pair.Value->GetComponentLocation().Y,
			Pair.Value->GetComponentLocation().Z,
			Extent.X * 2.f, Extent.Y * 2.f, Extent.Z * 2.f,
			Pair.Value->GetStaticMesh() != nullptr
				? *Pair.Value->GetStaticMesh()->GetName() : TEXT("none"),
			*Pair.Value->GetComponentScale().ToString());
	}
	for (const TPair<FName, TObjectPtr<UStaticMeshComponent>>& Pair :
		StationVisuals)
	{
		if (Pair.Value == nullptr) { continue; }
		const FVector Extent = Pair.Value->Bounds.BoxExtent;
		UE_LOG(LogLBSpacecraftPresenter, Display,
			TEXT("STATION %s size=(%.0f x %.0f x %.0f) cm mesh=%s ")
			TEXT("scale=%s"),
			*Pair.Key.ToString(), Extent.X * 2.f, Extent.Y * 2.f,
			Extent.Z * 2.f,
			Pair.Value->GetStaticMesh() != nullptr
				? *Pair.Value->GetStaticMesh()->GetName() : TEXT("none"),
			*Pair.Value->GetComponentScale().ToString());
	}
	// THE UNDERCARRIAGE, per craft: where each leg actually is relative
	// to the hull it hangs from, and whether it is still being drawn.
	for (const TPair<FName, FLBSpacecraftGearSet>& Pair : UnitGear)
	{
		for (int32 Leg = 0; Leg < Pair.Value.Legs.Num(); ++Leg)
		{
			const UStaticMeshComponent* Strut = Pair.Value.Legs[Leg].Get();
			if (!IsValid(Strut)) { continue; }
			const FVector Local = Strut->GetRelativeLocation();
			UE_LOG(LogLBSpacecraftPresenter, Display,
				TEXT("GEAR %s leg%d local=(%.0f,%.0f,%.0f) anchorZ=%.0f ")
				TEXT("visible=%d"),
				*Pair.Key.ToString(), Leg, Local.X, Local.Y, Local.Z,
				Pair.Value.AnchorZCm.IsValidIndex(Leg)
					? Pair.Value.AnchorZCm[Leg] : 0.f,
				Strut->IsVisible() ? 1 : 0);
		}
	}
	for (const FLBSpacecraftDepartingVisual& Departure : Departing)
	{
		for (int32 Leg = 0; Leg < Departure.GearLegs.Num(); ++Leg)
		{
			const UStaticMeshComponent* Strut = Departure.GearLegs[Leg].Get();
			if (!IsValid(Strut)) { continue; }
			UE_LOG(LogLBSpacecraftPresenter, Display,
				TEXT("GEAR-INFLIGHT leg%d t=%.2f localZ=%.0f ")
				TEXT("anchorZ=%.0f visible=%d"),
				Leg, Departure.ElapsedSeconds,
				Strut->GetRelativeLocation().Z,
				Departure.GearAnchorZCm.IsValidIndex(Leg)
					? Departure.GearAnchorZCm[Leg] : 0.f,
				Strut->IsVisible() ? 1 : 0);
		}
	}
	for (const TPair<FName, FLBSpacecraftDroneVisual>& Pair : DroneVisuals)
	{
		const FLBSpacecraftStationRecord* Record =
			BuildAuthority->FindStation(Pair.Key);
		const FVector StationAt = Record != nullptr
			? Record->WorldTransform.GetLocation() : FVector::ZeroVector;
		for (int32 Drone = 0; Drone < Pair.Value.Drones.Num(); ++Drone)
		{
			const UStaticMeshComponent* Body = Pair.Value.Drones[Drone];
			if (Body == nullptr)
			{
				continue;
			}
			const FVector At = Body->GetComponentLocation();
			const FBoxSphereBounds Bounds = Body->Bounds;
			UE_LOG(LogLBSpacecraftPresenter, Display,
				TEXT("DRONE %s[%d] %s at (%.0f,%.0f,%.0f) ")
				TEXT("station(%.0f,%.0f,%.0f) dZ=%.0f size=%.0fcm ")
				TEXT("mesh=%s"),
				*Pair.Key.ToString(), Drone,
				Pair.Value.Ground.IsValidIndex(Drone)
					&& Pair.Value.Ground[Drone]
					? TEXT("GROUND") : TEXT("FLIER"),
				At.X, At.Y, At.Z, StationAt.X, StationAt.Y, StationAt.Z,
				At.Z - StationAt.Z,
				Bounds.BoxExtent.GetMax() * 2.f,
				Body->GetStaticMesh() != nullptr
					? *Body->GetStaticMesh()->GetName() : TEXT("none"));
		}
	}
}

void ALBSpacecraftWIPPresentationActor::TickDrones(float DeltaSeconds)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	if (BuildAuthority == nullptr)
	{
		return;
	}
	TSet<FName> Live;
	for (const FLBSpacecraftStationRecord& Record :
		BuildAuthority->GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(Record.DefinitionId);
		// One shared rule with the battery sim: crafting families plus
		// the fitting route stations of the core line.
		if (Definition == nullptr
			|| !ALBSpacecraftDroneFleetAuthority::StationHostsFittingDrones(
				*Definition))
		{
			continue;
		}
		Live.Add(Record.StationId);
		// WHAT THE PLAYER HIRED IS WHAT STANDS THERE (owner
		// 2026-08-28). The crew signature is the hired kinds in slot
		// order; when it changes, the visual is rebuilt rather than
		// left showing the crew they had before they chose.
		const FString CrewRevision = ComputeDroneCrewRevision(
			Record.InstalledDroneTypes, Record.InstalledDrones);
		if (FString* Built = DroneVisualCrewRevisions.Find(
			Record.StationId))
		{
			if (*Built != CrewRevision)
			{
				if (FLBSpacecraftDroneVisual* Stale =
					DroneVisuals.Find(Record.StationId))
				{
					DestroyDroneVisual(*Stale);
				}
				DroneVisuals.Remove(Record.StationId);
			}
		}
		DroneVisualCrewRevisions.Add(Record.StationId, CrewRevision);
		FLBSpacecraftDroneVisual* Visual =
			DroneVisuals.Find(Record.StationId);
		if (Visual == nullptr)
		{
			FLBSpacecraftDroneVisual NewVisual;
			const FTransform& Station = Record.WorldTransform;
			// Show the hired crew when there is one; otherwise the
			// ambient pair, which is what crafting machines (no slots)
			// have always had and what an unstaffed station keeps.
			const int32 DroneCount = Record.InstalledDroneTypes.Num() > 0
				? Record.InstalledDroneTypes.Num() : 2;
			for (int32 Drone = 0; Drone < DroneCount; ++Drone)
			{
				// SPREAD ALONG BOTH FLANKS. This used to be "drone 0 to
				// one corner, everyone else to the other", which was
				// fine while a station had two drones and became a bug
				// the moment the loadout hired seven: six of them
				// stacked on a single point, so a bay crewed with the
				// full set looked like a bay with three.
				//
				// Alternating sides and stepping down the flank keeps
				// them all visible and reads like a crew at their
				// stations - and drones are the co-stars, so a station
				// that hides most of its own is the wrong picture.
				// One row of docks along the NEAR flank, outside the
				// pad edge, spread along the line - never at the pad's
				// ends, which are the track (owner 2026-09-02).
				const float Along = DroneCount > 1
					? -0.36f + 0.72f * static_cast<float>(Drone)
						/ static_cast<float>(DroneCount - 1)
					: 0.f;
				const FVector DockLocal(
					Along * Definition->FootprintCm.X,
					Definition->FootprintCm.Y * 0.5f + 170.f,
					0.f);
				const FVector DockWorld =
					Station.TransformPosition(DockLocal);
				NewVisual.DockLocations.Add(DockWorld);
				const FName DockKey(*FString::Printf(TEXT("%s_Dock%d"),
					*Record.StationId.ToString(), Drone));
				if (UStaticMeshComponent* Dock =
					MakeBlockComponent(DockKey, SpacecraftDockIdle))
				{
					Dock->SetWorldTransform(FTransform(FQuat::Identity,
						DockWorld + FVector(0.f, 0.f, 8.f),
						FVector(1.4f, 1.4f, 0.16f)));
					NewVisual.Docks.Add(Dock);
					NewVisual.DockMIDs.Add(
						Cast<UMaterialInstanceDynamic>(
							Dock->GetMaterial(0)));
				}
				// The real dock model sits ON the status pad when its
				// mesh is available; the pad below keeps the
				// idle/charging tint readable around its rim.
				if (UStaticMesh* DockMesh = TryGetStationMesh(
					FName(TEXT("Dock.Charging"))))
				{
					const FName DockMeshKey(*FString::Printf(
						TEXT("%s_DockMesh%d"),
						*Record.StationId.ToString(), Drone));
					UStaticMeshComponent* DockModel =
						NewObject<UStaticMeshComponent>(this,
							UStaticMeshComponent::StaticClass(),
							DockMeshKey);
					DockModel->SetStaticMesh(DockMesh);
					DockModel->SetCollisionEnabled(
						ECollisionEnabled::NoCollision);
					DockModel->SetCastShadow(false);
					DockModel->SetupAttachment(RootComponent);
					DockModel->RegisterComponent();
					DockModel->SetWorldTransform(FTransform(
						FQuat::Identity,
						DockWorld + FVector(0.f, 0.f, 16.f),
						FVector(1.f)));
					NewVisual.DockModels.Add(DockModel);
				}
				const FName DroneKey(*FString::Printf(TEXT("%s_Drone%d"),
					*Record.StationId.ToString(), Drone));
				if (UStaticMeshComponent* DroneComp =
					MakeBlockComponent(DroneKey, SpacecraftDroneBody))
				{
					FVector BodyScale(0.9f, 0.9f, 0.26f);
					// Crew by role: Winch works under the assembly bays,
					// CargoLift hauls at storage, Assembly fits parts
					// everywhere else (drones are co-stars - owner).
					// THE KIND THE PLAYER HIRED comes first (owner
					// 2026-08-28: they pick what drones they want, so
					// what stands there has to be what they bought).
					// The station-role guesses below are the fallback
					// for crews installed before kinds existed.
					FString HiredKind;
					if (Record.InstalledDroneTypes.IsValidIndex(Drone))
					{
						HiredKind =
							Record.InstalledDroneTypes[Drone].ToString();
					}
					const TCHAR* Crew = TEXT("Assembly");
					if (!HiredKind.IsEmpty())
					{
						Crew = *HiredKind;
					}
					else if (Record.DefinitionId == FName(TEXT("StorageRack")))
					{
						Crew = TEXT("CargoLift");
					}
					else if (Record.DefinitionId
							== FName(TEXT("SubAssemblyRobot"))
						|| Record.DefinitionId
							== FName(TEXT("AssemblyRobot"))
						|| Record.DefinitionId
							== FName(TEXT("AssemblyRobotMk2"))
						|| Record.DefinitionId
							== FName(TEXT("HullFabricator"))
						|| Record.DefinitionId
							== FName(TEXT("HullFabricatorMk2")))
					{
						Crew = TEXT("Winch");
					}
					if (UStaticMesh* BodyMesh = TryGetStationMesh(
						FName(*FString::Printf(TEXT("Drone.%s.Body"),
							Crew))))
					{
						// Real derivative: game scale baked, grounded.
						DroneComp->SetStaticMesh(BodyMesh);
						DroneComp->EmptyOverrideMaterials();
						BodyScale = FVector::OneVector;
						// DRONEBATCH_v001 (2026-08-30): named moving parts
						// beyond the body - rotor spinners, ground-drone
						// wheels, and (for now, spawned but static)
						// everything else this batch's design briefed as
						// separately articulated: arm joints, rams, jacks,
						// the winch drum/hook, landing legs. Attached to
						// DroneComp at IDENTITY: processing baked every
						// part's full position in the drone's own shared
						// coordinate space into its vertex data - the
						// same space the body mesh above is baked into -
						// so no offset is needed to reassemble the drone.
						// Spinners/Wheels then get a per-tick pivot
						// correction (ComputeRotatedPartRelativeLocation)
						// so they rotate around their OWN hub/axle rather
						// than the drone's shared origin - superseding the
						// "fans are part of the body" era below for any
						// crew this manifest covers; the block fallback
						// (Pods) still applies to crews it does not.
						TArray<FLBSpacecraftDronePartSpec> PartSpecs;
						GetDronePartsManifest(FName(Crew), PartSpecs);
						for (int32 PartIndex = 0; PartIndex < PartSpecs.Num();
							++PartIndex)
						{
							const FLBSpacecraftDronePartSpec& Spec =
								PartSpecs[PartIndex];
							UStaticMesh* PartMesh =
								TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
									Spec.AssetPath)).LoadSynchronous();
							if (PartMesh == nullptr)
							{
								continue;
							}
							const FName PartKey(*FString::Printf(
								TEXT("%s_Part%d"), *DroneKey.ToString(),
								PartIndex));
							UStaticMeshComponent* PartComp =
								NewObject<UStaticMeshComponent>(this,
									UStaticMeshComponent::StaticClass(),
									PartKey);
							PartComp->SetStaticMesh(PartMesh);
							PartComp->SetCollisionEnabled(
								ECollisionEnabled::NoCollision);
							PartComp->SetCastShadow(false);
							PartComp->SetupAttachment(DroneComp);
							PartComp->RegisterComponent();
							PartComp->SetRelativeTransform(
								FTransform::Identity);
							switch (Spec.Kind)
							{
							case ELBSpacecraftDronePartKind::Spinner:
								NewVisual.Spinners.Add(PartComp);
								NewVisual.SpinnerOwnerDroneIndex.Add(Drone);
								NewVisual.SpinnerAngleDeg.Add(0.f);
								NewVisual.SpinnerPivotLocal.Add(
									PartMesh->GetBounds().Origin);
								break;
							case ELBSpacecraftDronePartKind::Wheel:
								NewVisual.Wheels.Add(PartComp);
								NewVisual.WheelOwnerDroneIndex.Add(Drone);
								NewVisual.WheelAngleDeg.Add(0.f);
								NewVisual.WheelPivotLocal.Add(
									PartMesh->GetBounds().Origin);
								break;
							default:
								NewVisual.StaticParts.Add(PartComp);
								break;
							}
						}
						// Whole-mesh drones without a DroneBatch_v001
						// manifest: fans are part of the body (the carved
						// pods disfigured them - owner).
						// Carried crate: the visible "I am working"
						// payload, shown only while the drone is out
						// (until the real part models arrive).
						const FName CrateKey(*FString::Printf(
							TEXT("%s_Crate"), *DroneKey.ToString()));
						if (UStaticMeshComponent* Crate =
							MakeBlockComponent(CrateKey,
								SpacecraftCrateColour))
						{
							// Already registered by MakeBlockComponent:
							// runtime attach, not SetupAttachment.
							Crate->AttachToComponent(DroneComp,
								FAttachmentTransformRules::
									KeepRelativeTransform);
							Crate->SetRelativeLocation(
								FVector(0.f, 0.f, -34.f));
							Crate->SetRelativeScale3D(
								FVector(0.42f, 0.42f, 0.3f));
							Crate->SetVisibility(false);
							NewVisual.Crates.Add(Crate);
						}
						// Work-effect rig: cutting beam, weld flash and
						// four spark streaks (owner: "sparks and
						// lasers"). All hidden until the drone works.
						const FName BeamKey(*FString::Printf(
							TEXT("%s_Beam"), *DroneKey.ToString()));
						if (UStaticMeshComponent* Beam =
							MakeBlockComponent(BeamKey,
								SpacecraftBeamColour))
						{
							Beam->SetVisibility(false);
							NewVisual.Beams.Add(Beam);
						}
						const FName FlashKey(*FString::Printf(
							TEXT("%s_Flash"), *DroneKey.ToString()));
						if (UStaticMeshComponent* Flash =
							MakeBlockComponent(FlashKey,
								SpacecraftWeldColour))
						{
							Flash->SetVisibility(false);
							NewVisual.Flashes.Add(Flash);
						}
						for (int32 Spark = 0; Spark < 4; ++Spark)
						{
							const FName SparkKey(*FString::Printf(
								TEXT("%s_Spark%d"),
								*DroneKey.ToString(), Spark));
							if (UStaticMeshComponent* SparkComp =
								MakeBlockComponent(SparkKey,
									SpacecraftSparkColour))
							{
								SparkComp->SetVisibility(false);
								NewVisual.Sparks.Add(SparkComp);
							}
						}
						// Lights (owner 2026-08-26): two blue-white
						// nav strobes on the shoulders, one warm work
						// light under the belly - soft additive glows
						// riding the drone body.
						for (int32 Nav = 0; Nav < 2; ++Nav)
						{
							UMaterialInstanceDynamic* NavMID = nullptr;
							if (UStaticMeshComponent* NavComp =
								MakeGlowSprite(FString::Printf(
									TEXT("%s_Nav%d"),
									*DroneKey.ToString(), Nav),
									DroneComp,
									FVector(0.f,
										Nav == 0 ? -30.f : 30.f, 14.f),
									10.f, SpacecraftAccentBright,
									NavMID))
							{
								NewVisual.NavLights.Add(NavComp);
								NewVisual.NavLightMIDs.Add(NavMID);
							}
						}
						{
							UMaterialInstanceDynamic* WorkMID = nullptr;
							if (UStaticMeshComponent* WorkComp =
								MakeGlowSprite(FString::Printf(
									TEXT("%s_WorkLight"),
									*DroneKey.ToString()), DroneComp,
									FVector(0.f, 0.f, -20.f), 46.f,
									SpacecraftWeldColour, WorkMID))
							{
								WorkComp->SetVisibility(false);
								NewVisual.WorkLights.Add(WorkComp);
								NewVisual.WorkLightMIDs.Add(WorkMID);
							}
						}
					}
					// Wheeled crew park ON the floor, not 40 cm above
					// it. The flag is read once here, from the kind the
					// player hired, and everything downstream - drive
					// path, rotor spin, rotor voice - reads the flag
					// rather than re-deciding.
					const FLBSpacecraftDroneKind* HiredDefinition =
						HiredKind.IsEmpty() ? nullptr
							: ALBSpacecraftBuildAuthority::FindDroneKind(
								FName(*HiredKind));
					const bool bGroundCrew = HiredDefinition != nullptr
						&& HiredDefinition->bGroundCrew;
					DroneComp->SetWorldTransform(FTransform(
						FQuat::Identity,
						DockWorld + FVector(0.f, 0.f,
							bGroundCrew ? 0.f : 40.f),
						BodyScale));
					NewVisual.Drones.Add(DroneComp);
					NewVisual.Ground.Add(bGroundCrew);
					// Rotor state rides one-per-drone alongside the
					// body, so every index lines up with Drones.
					NewVisual.RotorSpeeds.Add(0.f);
					NewVisual.RotorAngles.Add(0.f);
					NewVisual.RotorAudio.Add(
						LBSpacecraftWIPPresentationPrivate::
							SpacecraftMakeRotorAudio(this, DroneComp,
								FName(*FString::Printf(TEXT("%s_Rotors"),
									*DroneKey.ToString())),
								RotorLoopSound.LoadSynchronous(),
								RotorAudioRadiusCm,
								RotorAudioFalloffCm));
					NewVisual.LastLocations.Add(
						DockWorld + FVector(0.f, 0.f,
							bGroundCrew ? 0.f : 40.f));
				}
			}
			Visual = &DroneVisuals.Add(Record.StationId, NewVisual);
		}
		// Working state is READ, never invented: from the drone fleet
		// (battery-aware) when bound, else from the crafting selection.
		bool bWorking = CraftingAuthority != nullptr
			&& CraftingAuthority->GetSelectedRecipe(Record.StationId)
				!= nullptr;
		if (DroneFleetAuthority != nullptr)
		{
			const FLBSpacecraftDroneState* Drone0 =
				DroneFleetAuthority->FindDrone(Record.StationId, 0);
			bWorking = Drone0 != nullptr && Drone0->bFlying;
		}
		// FITTING IS WORK (owner 2026-09-01: "its building hull but
		// theres no activity"). Fleet sorties exist only for crafting
		// recipes, so a line crew sat docked through the very cycle
		// this game is about watching. The coordinator's assignment is
		// the truth of "this crew is working": while the station holds
		// a craft, the docked fleet state stands aside below and the
		// orbit-and-work choreography runs - crates, belly rovers,
		// weld rig and all.
		bool bStationFitting = false;
		if (Coordinator != nullptr)
		{
			for (const FLBSpacecraftRuntimeAssignment& Assignment :
				Coordinator->GetAssignments())
			{
				if (Assignment.StationId == Record.StationId)
				{
					bStationFitting = true;
					break;
				}
			}
		}
		bWorking = bWorking || bStationFitting;
		const float Rate = DroneTransitSeconds > 0.f
			? 1.f / DroneTransitSeconds : 100.f;
		Visual->WorkAlpha = FMath::Clamp(
			Visual->WorkAlpha + (bWorking ? 1.f : -1.f)
				* DeltaSeconds * Rate, 0.f, 1.f);
		const float Eased = FMath::SmoothStep(0.f, 1.f, Visual->WorkAlpha);
		const FVector StationCentre =
			Record.WorldTransform.GetLocation();
		const float OrbitRadius =
			FMath::Max(Definition->FootprintCm.X,
				Definition->FootprintCm.Y) * 0.45f;
		for (int32 Drone = 0; Drone < Visual->Drones.Num(); ++Drone)
		{
			if (Visual->Drones[Drone] == nullptr)
			{
				continue;
			}
			// GROUND CREW work underneath the craft (owner 2026-08-28:
			// "3 ground drones ... for working underneath the ship").
			// They shuttle the length of the belly at floor level; the
			// fliers keep the orbit-and-bob they have always had.
			const bool bGround = Visual->Ground.IsValidIndex(Drone)
				&& Visual->Ground[Drone];
			const FVector WorkSpot = bGround
				? StationCentre + ComputeGroundDroneWorkOffsetCm(
					AccentClockSeconds, Drone, OrbitRadius, 260.f)
				: StationCentre + ComputeDroneWorkOffsetCm(
					AccentClockSeconds, Drone, OrbitRadius,
					DroneHoverHeightCm);
			const FVector DockSpot = Visual->DockLocations.IsValidIndex(
				Drone) ? Visual->DockLocations[Drone]
					+ FVector(0.f, 0.f, bGround ? 0.f : 40.f)
				: StationCentre;
			// Autonomous sorties mirror the fleet authority's mission
			// state; without a fleet bound the old orbit lerp stands in.
			FVector NewSpot = FMath::Lerp(DockSpot, WorkSpot, Eased);
			bool bCarrying = false;
			bool bFitting = Eased > 0.9f;
			// GROUND CREW DO NOT RUN SUPPLY SORTIES. The fleet's
			// missions fly a drone 90 m to the delivery apron and back;
			// a rover whose whole job is the underside of the craft in
			// front of it has no business there, and clamping such a
			// sortie to the floor would just show it driving across the
			// hall. They stay at their station and work the belly.
			if (DroneFleetAuthority != nullptr && !bGround)
			{
				if (const FLBSpacecraftDroneState* State =
					DroneFleetAuthority->FindDrone(Record.StationId,
						Drone))
				{
					// Supply point: the delivery dock apron, staggered
					// per drone so sorties do not stack.
					// THE PARTS COME OFF THE STATION'S OWN PALLETS (owner
					// 2026-09-02: "the heavy drones are supposed to pick
					// the parts up from the pallets and put together").
					// The supply run used to go to a fixed point 99 m off
					// the line, so the crew flew away to nowhere; now it
					// is the pallet stack beside the station, and the
					// fallback is only for a station with no stock shown.
					FVector SupplySpot(-9900.f,
						((Drone * 2 + (Record.StationId.GetNumber() % 5))
							- 4) * 220.f,
						DroneHoverHeightCm);
					if (const TArray<TObjectPtr<UStaticMeshComponent>>*
						Stacks = StationStockStacks.Find(Record.StationId))
					{
						if (Stacks->Num() > 0)
						{
							const UStaticMeshComponent* Pallet =
								(*Stacks)[Drone % Stacks->Num()];
							if (Pallet != nullptr)
							{
								SupplySpot = Pallet->GetComponentLocation()
									+ FVector(0.f, 0.f,
										DroneHoverHeightCm * 0.55f);
							}
						}
					}
					const float Alpha = FMath::SmoothStep(0.f, 1.f,
						ALBSpacecraftDroneFleetAuthority::
							GetMissionAlpha01(*State,
								DroneFleetAuthority->TravelSeconds,
								DroneFleetAuthority->PickupSeconds,
								DroneFleetAuthority
									->FittingBurstSeconds));
					bCarrying = false;
					bFitting = false;
					switch (State->Mission)
					{
					case ELBSpacecraftDroneMission::ToSupply:
						NewSpot = FMath::Lerp(DockSpot, SupplySpot,
							Alpha);
						break;
					case ELBSpacecraftDroneMission::Pickup:
						NewSpot = SupplySpot + FVector(0.f, 0.f,
							18.f * FMath::Sin(
								AccentClockSeconds * 4.f + Drone));
						break;
					case ELBSpacecraftDroneMission::ToStation:
						NewSpot = FMath::Lerp(SupplySpot, WorkSpot,
							Alpha);
						bCarrying = true;
						break;
					case ELBSpacecraftDroneMission::Fitting:
						NewSpot = WorkSpot;
						bFitting = true;
						break;
					case ELBSpacecraftDroneMission::ToDock:
						NewSpot = FMath::Lerp(WorkSpot, DockSpot,
							Alpha);
						break;
					default:
						// While the station FITS, docked means "no
						// sortie running", not "stay parked": the
						// work-orbit lerp already in NewSpot owns the
						// drone, and the work rig lights at full
						// alpha, matching the fleetless idiom.
						if (bStationFitting)
						{
							bFitting = Eased > 0.9f;
						}
						else
						{
							NewSpot = DockSpot;
						}
						break;
					}
				}
			}
			if (bGround)
			{
				// The wheels are the contract: a mission lerp may aim
				// this drone anywhere, but its Z is clamped to the
				// station floor here so it can never be seen to fly.
				NewSpot.Z = StationCentre.Z;
				Visual->Drones[Drone]->SetWorldLocationAndRotation(
					NewSpot, FRotator(0.f,
						ComputeGroundDroneYawDeg(AccentClockSeconds,
							Drone), 0.f));
			}
			else
			{
				Visual->Drones[Drone]->SetWorldLocation(NewSpot);
			}
			// ROTORS. One speed value per drone feeds BOTH the blade
			// spin and the sound, so what you hear can never disagree
			// with what you see - the reason this is a model rather
			// than two independent effects.
			const bool bRotorsAirborne = !bGround
				&& (Eased > 0.02f || bCarrying || bFitting);
			float RotorSpeed01 = 0.f;
			if (!bGround && Visual->RotorSpeeds.IsValidIndex(Drone))
			{
				RotorSpeed01 = ComputeRotorSpeed01(
					Visual->RotorSpeeds[Drone],
					ComputeRotorLoad01(!bRotorsAirborne, bCarrying,
						bFitting),
					DeltaSeconds, RotorSpoolUpSeconds,
					RotorSpoolDownSeconds);
				Visual->RotorSpeeds[Drone] = RotorSpeed01;
			}
			if (Visual->RotorAngles.IsValidIndex(Drone))
			{
				// Wrapped to a turn so the angle cannot grow until
				// float precision makes the spin visibly stutter.
				Visual->RotorAngles[Drone] = FMath::Fmod(
					Visual->RotorAngles[Drone]
						+ RotorSpeed01 * RotorSpinDegPerSec
							* DeltaSeconds,
					360.f);
			}
			if (Visual->RotorAudio.IsValidIndex(Drone)
				&& Visual->RotorAudio[Drone] != nullptr)
			{
				UAudioComponent* Rotors = Visual->RotorAudio[Drone];
				const float Volume = ComputeRotorVolume01(RotorSpeed01);
				if (Volume <= KINDA_SMALL_NUMBER)
				{
					// Fully spooled down: stop rather than play silence,
					// so a floor of docked drones costs no voices.
					if (Rotors->IsPlaying())
					{
						Rotors->Stop();
					}
				}
				else
				{
					Rotors->SetPitchMultiplier(ComputeRotorPitch(
						RotorSpeed01, RotorMinPitch, RotorMaxPitch));
					Rotors->SetVolumeMultiplier(Volume);
					if (!Rotors->IsPlaying())
					{
						Rotors->Play();
					}
				}
			}
			// Fan pods lean into the motion (four pods per drone).
			if (Visual->LastLocations.IsValidIndex(Drone)
				&& DeltaSeconds > 0.f)
			{
				const FVector Velocity =
					(NewSpot - Visual->LastLocations[Drone])
						/ DeltaSeconds;
				Visual->LastLocations[Drone] = NewSpot;
				const FRotator Tilt =
					ComputeFanTiltDeg(Velocity, 18.f);
				// Review fix: pods per drone varies (CargoLift crews
				// carry six); split the pod array evenly across the
				// pair instead of assuming four.
				const int32 PodsPerDrone = Visual->Drones.Num() > 0
					? Visual->Pods.Num() / Visual->Drones.Num() : 0;
				for (int32 PodIndex = Drone * PodsPerDrone;
					PodIndex < (Drone + 1) * PodsPerDrone
						&& PodIndex < Visual->Pods.Num(); ++PodIndex)
				{
					if (Visual->Pods[PodIndex] != nullptr)
					{
						// ComputeFanTiltDeg leaves yaw free, so the
						// blade spin drops straight into it. Note this
						// reaches only the BLOCK fallback: the real
						// drone derivatives are one whole mesh with the
						// fans modelled in, so nothing separable is
						// left to turn. The sound is driven by the
						// rotor model either way, and separable rotor
						// sub-meshes would make this visible on them
						// too.
						Visual->Pods[PodIndex]->SetRelativeRotation(
							FRotator(Tilt.Pitch,
								Visual->RotorAngles.IsValidIndex(Drone)
									? Visual->RotorAngles[Drone] : 0.f,
								Tilt.Roll));
					}
				}
				// DRONEBATCH_v001 (2026-08-30): the named parts this
				// drone actually has, as opposed to Pods above (the
				// block-fallback-only substitute). Ground speed for
				// wheel roll comes from the SAME Velocity just computed
				// for the fan-pod tilt; a drone with zero Spinners/
				// Wheels here (nothing hired yet, or a crew the
				// manifest does not cover) simply does no extra work -
				// both loops are filtered by owner index, not sized to
				// this drone specifically.
				const float SpinSpeed01 =
					Visual->RotorSpeeds.IsValidIndex(Drone)
						? Visual->RotorSpeeds[Drone] : 0.f;
				const float GroundSpeedCmPerS = Velocity.Size2D();
				constexpr float SpinnerDegPerSecAtFullSpeed = 1400.f;
				constexpr float WheelRadiusCm = 22.f;
				for (int32 Spin = 0; Spin < Visual->Spinners.Num(); ++Spin)
				{
					if (Visual->SpinnerOwnerDroneIndex[Spin] != Drone
						|| Visual->Spinners[Spin] == nullptr)
					{
						continue;
					}
					Visual->SpinnerAngleDeg[Spin] = ComputeSpinnerAngleDeg(
						Visual->SpinnerAngleDeg[Spin], DeltaSeconds,
						SpinSpeed01, SpinnerDegPerSecAtFullSpeed);
					const FRotator SpinRot(0.f,
						Visual->SpinnerAngleDeg[Spin], 0.f);
					Visual->Spinners[Spin]->SetRelativeLocationAndRotation(
						ComputeRotatedPartRelativeLocation(
							Visual->SpinnerPivotLocal[Spin], SpinRot),
						SpinRot);
				}
				for (int32 Wheel = 0; Wheel < Visual->Wheels.Num(); ++Wheel)
				{
					if (Visual->WheelOwnerDroneIndex[Wheel] != Drone
						|| Visual->Wheels[Wheel] == nullptr)
					{
						continue;
					}
					Visual->WheelAngleDeg[Wheel] = ComputeWheelRollDeg(
						Visual->WheelAngleDeg[Wheel], DeltaSeconds,
						GroundSpeedCmPerS, WheelRadiusCm);
					// A wheel with its axle along local Y (forward
					// travel along local X, the standard actor-forward
					// convention this drone's own body yaw already
					// assumes via ComputeGroundDroneYawDeg) rolls in
					// the X-Z plane - rotation around Y, which FRotator
					// names Pitch, not Roll.
					const FRotator RollRot(Visual->WheelAngleDeg[Wheel],
						0.f, 0.f);
					Visual->Wheels[Wheel]->SetRelativeLocationAndRotation(
						ComputeRotatedPartRelativeLocation(
							Visual->WheelPivotLocal[Wheel], RollRot),
						RollRot);
				}
			}
			// The payload crate shows only while out working: docked
			// drones carry nothing (draws less, never more).
			if (Visual->Crates.IsValidIndex(Drone)
				&& Visual->Crates[Drone] != nullptr)
			{
				// PHASE D (look plan): the sortie carries the ACTUAL
				// PART - the mesh on the station's pallet - not a
				// generic crate, so what flies onto the craft is what
				// was lying beside it.
				UStaticMeshComponent* Carried = Visual->Crates[Drone];
				if (bCarrying)
				{
					UStaticMesh* PartMesh = nullptr;
					if (const TArray<TObjectPtr<UStaticMeshComponent>>*
						Stacks = StationStockStacks.Find(Record.StationId))
					{
						if (Stacks->Num() > 0 && (*Stacks)[0] != nullptr)
						{
							PartMesh = (*Stacks)[0]->GetStaticMesh();
						}
					}
					if (PartMesh != nullptr
						&& Carried->GetStaticMesh() != PartMesh)
					{
						Carried->SetStaticMesh(PartMesh);
						Carried->EmptyOverrideMaterials();
						// A pallet-sized section carried at a third of
						// its size reads as a part in a claw.
						Carried->SetRelativeScale3D(FVector(0.34f));
						Carried->SetRelativeLocation(FVector(0.f, 0.f, -60.f));
					}
				}
				Carried->SetVisibility(bCarrying);
			}
			// Sparks and lasers while working: beam from the drone
			// belly to the work point, flickering weld flash, spark
			// burst - all deterministic, all hidden when docked.
			const bool bWorkingEffects = bFitting;
			// Lights (owner 2026-08-26): the nav strobes blink on a
			// per-drone phase whenever the drone is off its dock; the
			// warm work light burns only while it works.
			const bool bAirborne = Eased > 0.02f
				|| bCarrying || bFitting;
			for (int32 Nav = 0; Nav < 2; ++Nav)
			{
				const int32 NavIndex = Drone * 2 + Nav;
				if (!Visual->NavLights.IsValidIndex(NavIndex)
					|| Visual->NavLights[NavIndex] == nullptr)
				{
					continue;
				}
				const float Phase = FMath::Frac(
					AccentClockSeconds * 1.4f
					+ Drone * 0.37f + Nav * 0.5f);
				const bool bBlink = Phase < 0.12f;
				Visual->NavLights[NavIndex]->SetVisibility(
					bAirborne && bBlink);
				if (Visual->NavLightMIDs.IsValidIndex(NavIndex)
					&& Visual->NavLightMIDs[NavIndex] != nullptr)
				{
					Visual->NavLightMIDs[NavIndex]
						->SetScalarParameterValue(TEXT("Strength"),
							9.f);
				}
			}
			if (Visual->WorkLights.IsValidIndex(Drone)
				&& Visual->WorkLights[Drone] != nullptr)
			{
				Visual->WorkLights[Drone]->SetVisibility(
					bWorkingEffects);
				if (bWorkingEffects
					&& Visual->WorkLightMIDs.IsValidIndex(Drone)
					&& Visual->WorkLightMIDs[Drone] != nullptr)
				{
					// The work light breathes with the weld flicker.
					Visual->WorkLightMIDs[Drone]
						->SetScalarParameterValue(TEXT("Strength"),
							3.f + 3.f * ComputeWeldFlicker01(
								AccentClockSeconds, Drone));
				}
			}
			const FVector WorkPoint(NewSpot.X, NewSpot.Y, 120.f);
			if (Visual->Beams.IsValidIndex(Drone)
				&& Visual->Beams[Drone] != nullptr)
			{
				Visual->Beams[Drone]->SetVisibility(bWorkingEffects);
				if (bWorkingEffects)
				{
					const FVector Belly = NewSpot
						+ FVector(0.f, 0.f, -20.f);
					const FVector Mid = (Belly + WorkPoint) * 0.5f;
					const float Length =
						FVector::Dist(Belly, WorkPoint);
					Visual->Beams[Drone]->SetWorldTransform(FTransform(
						FRotationMatrix::MakeFromZ(WorkPoint - Belly)
							.Rotator(),
						Mid, FVector(0.05f, 0.05f, Length / 100.f)));
				}
			}
			if (Visual->Flashes.IsValidIndex(Drone)
				&& Visual->Flashes[Drone] != nullptr)
			{
				Visual->Flashes[Drone]->SetVisibility(bWorkingEffects);
				if (bWorkingEffects)
				{
					const float Flicker = ComputeWeldFlicker01(
						AccentClockSeconds, Drone);
					Visual->Flashes[Drone]->SetWorldTransform(
						FTransform(FQuat::Identity, WorkPoint,
							FVector(0.25f + 0.35f * Flicker)));
				}
			}
			for (int32 Spark = Drone * 4; Spark < Drone * 4 + 4
				&& Spark < Visual->Sparks.Num(); ++Spark)
			{
				if (Visual->Sparks[Spark] == nullptr)
				{
					continue;
				}
				Visual->Sparks[Spark]->SetVisibility(bWorkingEffects);
				if (bWorkingEffects)
				{
					float Alive = 0.f;
					const FVector Offset = ComputeSparkOffsetCm(
						AccentClockSeconds, Spark, Alive);
					Visual->Sparks[Spark]->SetWorldTransform(
						FTransform(FQuat::Identity,
							WorkPoint + Offset,
							FVector(0.1f, 0.1f, 0.04f)
								* FMath::Max(Alive, 0.05f)));
				}
			}
			// A landed drone charges: its dock pulses warm.
			if (Visual->DockMIDs.IsValidIndex(Drone)
				&& Visual->DockMIDs[Drone] != nullptr)
			{
				// Review fix: the pulse mirrors the fleet's real
				// charging state - a full battery sits dark, honest.
				float ChargingNow = 1.f;
				if (DroneFleetAuthority != nullptr)
				{
					const FLBSpacecraftDroneState* DockState =
						DroneFleetAuthority->FindDrone(
							Record.StationId, Drone);
					ChargingNow = (DockState != nullptr
						&& DockState->Charge01 < 1.f) ? 1.f : 0.f;
				}
				const float Charge = (1.f - Eased) * ChargingNow
					* ComputeAccentPulse01(AccentClockSeconds, 1.8f);
				Visual->DockMIDs[Drone]->SetVectorParameterValue(
					TEXT("Color"),
					FMath::Lerp(SpacecraftDockIdle,
						SpacecraftDockCharging, Charge));
			}
		}
	}
	// Removed stations take their drones and docks with them.
	for (auto It = DroneVisuals.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			DestroyDroneVisual(It.Value());
			DroneVisualCrewRevisions.Remove(It.Key());
			It.RemoveCurrent();
		}
	}
}

void ALBSpacecraftWIPPresentationActor::TickStationAccents(
	float DeltaSeconds)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	AccentClockSeconds += FMath::Max(DeltaSeconds, 0.f);
	if (BuildAuthority == nullptr)
	{
		return;
	}
	TSet<FName> Live;
	ActiveAccents.Reset();
	for (const FLBSpacecraftStationRecord& Record :
		BuildAuthority->GetStations())
	{
		// Accents dress REAL meshes only; placeholder blocks stay plain.
		TObjectPtr<UStaticMesh>* Loaded =
			LoadedStationMeshes.Find(Record.DefinitionId);
		UStaticMesh* StationMesh =
			Loaded != nullptr ? Loaded->Get() : nullptr;
		if (StationMesh == nullptr)
		{
			continue;
		}
		Live.Add(Record.StationId);
		const bool bRing =
			Record.DefinitionId == FName(TEXT("PowerPlant"));
		// Working state is READ, never invented: an active recipe pulses
		// the beacon; the plant's ring always runs (it supplies).
		const bool bActive = bRing
			|| (CraftingAuthority != nullptr
				&& CraftingAuthority->GetSelectedRecipe(Record.StationId)
					!= nullptr);
		if (bActive)
		{
			ActiveAccents.Add(Record.StationId);
		}

		TObjectPtr<UStaticMeshComponent>* Existing =
			StationAccents.Find(Record.StationId);
		UStaticMeshComponent* Accent =
			Existing != nullptr ? Existing->Get() : nullptr;
		if (Accent == nullptr)
		{
			// The plant wears a compact GLOW ORB (owner 2026-08-26:
			// "the glow was a big disk" - the old bounds-sized ring
			// read as a landing pad); everything else keeps the small
			// status puck.
			UStaticMesh* AccentMesh = LoadObject<UStaticMesh>(nullptr,
				bRing ? TEXT("/Engine/BasicShapes/Sphere.Sphere")
					: SpacecraftCylinderPath);
			if (AccentMesh == nullptr)
			{
				continue; // draws less, never more
			}
			const FName AccentKey(*FString::Printf(TEXT("%s_Accent"),
				*Record.StationId.ToString()));
			Accent = NewObject<UStaticMeshComponent>(this,
				UStaticMeshComponent::StaticClass(), AccentKey);
			Accent->SetStaticMesh(AccentMesh);
			Accent->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Accent->SetCastShadow(false);
			Accent->SetupAttachment(RootComponent);
			Accent->RegisterComponent();
			UMaterialInterface* AccentMaterial = bRing
				? LoadObject<UMaterialInterface>(nullptr,
					SpacecraftSoftFlameMaterialPath)
				: nullptr;
			if (AccentMaterial == nullptr)
			{
				AccentMaterial = LoadObject<UMaterialInterface>(nullptr,
					SpacecraftShapeMaterialPath);
			}
			if (AccentMaterial != nullptr)
			{
				UMaterialInstanceDynamic* MID =
					UMaterialInstanceDynamic::Create(AccentMaterial,
						Accent);
				MID->SetVectorParameterValue(TEXT("Color"),
					SpacecraftAccentDim);
				Accent->SetMaterial(0, MID);
				StationAccentMIDs.Add(Record.StationId, MID);
			}
			StationAccents.Add(Record.StationId, Accent);
		}

		const FBoxSphereBounds MeshBounds = StationMesh->GetBounds();
		FTransform AccentTransform = Record.WorldTransform;
		if (bRing)
		{
			// Compact energy orb breathing above the reactor - the
			// old bounds-sized disk read as a landing pad (owner).
			const float Breathe = 1.6f + 0.25f * FMath::Sin(
				AccentClockSeconds * 1.7f);
			AccentTransform.SetScale3D(FVector(Breathe));
			AccentTransform.AddToTranslation(FVector(0.f, 0.f,
				MeshBounds.BoxExtent.Z * 2.f + 160.f
				+ 18.f * FMath::Sin(AccentClockSeconds * 0.9f)));
		}
		else
		{
			// Status beacon above the mesh.
			AccentTransform.SetScale3D(FVector(1.1f, 1.1f, 0.32f));
			AccentTransform.AddToTranslation(FVector(0.f, 0.f,
				MeshBounds.BoxExtent.Z * 2.f + 90.f));
		}
		Accent->SetWorldTransform(AccentTransform);
		if (TObjectPtr<UMaterialInstanceDynamic>* MID =
			StationAccentMIDs.Find(Record.StationId))
		{
			const float Pulse = bActive
				? ComputeAccentPulse01(AccentClockSeconds,
					SpacecraftAccentPulsePeriod)
				: 0.f;
			(*MID)->SetVectorParameterValue(TEXT("Color"),
				FMath::Lerp(SpacecraftAccentDim, SpacecraftAccentBright,
					Pulse));
		}
	}
	// Accents of removed (or mesh-less) stations disappear.
	for (auto It = StationAccents.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			if (It.Value() != nullptr)
			{
				It.Value()->DestroyComponent();
			}
			StationAccentMIDs.Remove(It.Key());
			It.RemoveCurrent();
		}
	}
}

UStaticMeshComponent* ALBSpacecraftWIPPresentationActor::MakeGlowSprite(
	const FString& Key, UStaticMeshComponent* AttachTo,
	const FVector& RelLocation, float SizeCm,
	const FLinearColor& Colour, UMaterialInstanceDynamic*& OutMID)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	OutMID = nullptr;
	UStaticMesh* Sphere = LoadObject<UStaticMesh>(nullptr,
		TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (Sphere == nullptr || AttachTo == nullptr)
	{
		return nullptr;
	}
	UStaticMeshComponent* Glow = NewObject<UStaticMeshComponent>(this,
		UStaticMeshComponent::StaticClass(), FName(*Key));
	Glow->SetStaticMesh(Sphere);
	Glow->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Glow->SetCastShadow(false);
	Glow->RegisterComponent();
	Glow->AttachToComponent(AttachTo,
		FAttachmentTransformRules::KeepRelativeTransform);
	Glow->SetRelativeLocation(RelLocation);
	Glow->SetRelativeScale3D(FVector(SizeCm / 100.f));
	// The soft additive flame material doubles as a light glow; the
	// engine-shape MID is the honest fallback when it is absent.
	if (UMaterialInterface* Soft = LoadObject<UMaterialInterface>(nullptr,
		SpacecraftSoftFlameMaterialPath))
	{
		OutMID = UMaterialInstanceDynamic::Create(Soft, Glow);
		OutMID->SetVectorParameterValue(TEXT("Color"), Colour);
		Glow->SetMaterial(0, OutMID);
	}
	else if (UMaterialInterface* Shape = LoadObject<UMaterialInterface>(
		nullptr, SpacecraftShapeMaterialPath))
	{
		OutMID = UMaterialInstanceDynamic::Create(Shape, Glow);
		OutMID->SetVectorParameterValue(TEXT("Color"), Colour);
		Glow->SetMaterial(0, OutMID);
	}
	return Glow;
}

UStaticMeshComponent* ALBSpacecraftWIPPresentationActor::MakeTrackPieceComponent(
	FName Key, UStaticMesh* Mesh)
{
	UStaticMeshComponent* Component = NewObject<UStaticMeshComponent>(
		this, UStaticMeshComponent::StaticClass(), Key);
	Component->SetStaticMesh(Mesh);
	Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	// Machinery CASTS. Without a shadow a station reads as a
	// sticker on the floor rather than an object standing on
	// it, and the whole floor looks flat under any lighting.
	Component->SetCastShadow(true);
	Component->SetReceivesDecals(false);
	Component->SetupAttachment(RootComponent);
	Component->RegisterComponent();
	return Component;
}

void ALBSpacecraftWIPPresentationActor::TintTrackCapForStart(
	UStaticMeshComponent* CapComponent)
{
	// The Start anchor wears the blue accent instead of the end cap's
	// warning orange; the import lane authored the material for this.
	if (CapComponent == nullptr || CapComponent->GetStaticMesh() == nullptr)
	{
		return;
	}
	UMaterialInterface* Blue = LoadObject<UMaterialInterface>(nullptr,
		TEXT("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001")
		TEXT("/Materials/M_LB_Track_AccentBlue.M_LB_Track_AccentBlue"));
	if (Blue == nullptr)
	{
		return;
	}
	const TArray<FStaticMaterial>& Slots =
		CapComponent->GetStaticMesh()->GetStaticMaterials();
	for (int32 Index = 0; Index < Slots.Num(); ++Index)
	{
		const FString SlotName =
			Slots[Index].MaterialSlotName.ToString();
		if (SlotName.Contains(TEXT("Track_Accent"))
			&& !SlotName.Contains(TEXT("Blue")))
		{
			CapComponent->SetMaterial(Index, Blue);
		}
	}
}

UStaticMeshComponent* ALBSpacecraftWIPPresentationActor::MakeBlockComponent(
	FName Key, const FLinearColor& Colour)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, SpacecraftCubePath);
	if (Cube == nullptr)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("SPACECRAFT PRESENTER: engine cube unavailable for %s"),
			*Key.ToString());
		return nullptr;
	}
	UStaticMeshComponent* Component = NewObject<UStaticMeshComponent>(
		this, UStaticMeshComponent::StaticClass(), Key);
	Component->SetStaticMesh(Cube);
	Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Component->SetCastShadow(true);
	// Blocks RECEIVE decals now. The line-station pad is a slab
	// sitting exactly where the bay paint projects: refusing
	// decals, it hid the markings under itself, which is why
	// the paint had never been seen despite registering and
	// cleaning up correctly. Emissive parts opt out below.
	Component->SetReceivesDecals(true);
	Component->SetupAttachment(RootComponent);
	Component->RegisterComponent();
	if (UMaterialInterface* ShapeMaterial = LoadObject<UMaterialInterface>(
		nullptr, SpacecraftShapeMaterialPath))
	{
		UMaterialInstanceDynamic* MID =
			UMaterialInstanceDynamic::Create(ShapeMaterial, Component);
		MID->SetVectorParameterValue(TEXT("Color"), Colour);
		Component->SetMaterial(0, MID);
	}
	return Component;
}

UStaticMesh* ALBSpacecraftWIPPresentationActor::ResolveChassisMesh()
{
	if (LBSpacecraftWIPPresentationPrivate::bBlockoutMeshyContent)
	{
		return nullptr;
	}
	if (!bChassisMeshLoadAttempted)
	{
		bChassisMeshLoadAttempted = true;
		LoadedChassisMesh = ChassisMesh.LoadSynchronous();
		if (LoadedChassisMesh != nullptr)
		{
			UE_LOG(LogTemp, Display,
				TEXT("SPACECRAFT PRESENTER: chassis mesh bound"));
		}
		else
		{
			UE_LOG(LogTemp, Display,
				TEXT("SPACECRAFT PRESENTER: no chassis mesh - crate stands in"));
		}
	}
	return LoadedChassisMesh;
}

UStaticMesh* ALBSpacecraftWIPPresentationActor::ResolveAirframeMesh()
{
	if (LBSpacecraftWIPPresentationPrivate::bBlockoutMeshyContent)
	{
		return nullptr;
	}
	if (!bAirframeMeshLoadAttempted)
	{
		bAirframeMeshLoadAttempted = true;
		LoadedAirframeMesh = AirframeMesh.LoadSynchronous();
		if (LoadedAirframeMesh != nullptr)
		{
			UE_LOG(LogTemp, Display,
				TEXT("SPACECRAFT PRESENTER: airframe mesh bound"));
		}
		else
		{
			UE_LOG(LogTemp, Display, TEXT(
				"SPACECRAFT PRESENTER: no airframe mesh - ladder falls"));
		}
	}
	return LoadedAirframeMesh;
}

UStaticMesh* ALBSpacecraftWIPPresentationActor::ResolveFittedMesh()
{
	if (LBSpacecraftWIPPresentationPrivate::bBlockoutMeshyContent)
	{
		return nullptr;
	}
	if (!bFittedMeshLoadAttempted)
	{
		bFittedMeshLoadAttempted = true;
		LoadedFittedMesh = FittedMesh.LoadSynchronous();
		if (LoadedFittedMesh != nullptr)
		{
			UE_LOG(LogTemp, Display,
				TEXT("SPACECRAFT PRESENTER: fitted mesh bound"));
		}
		else
		{
			UE_LOG(LogTemp, Display, TEXT(
				"SPACECRAFT PRESENTER: no fitted mesh - ladder falls"));
		}
	}
	return LoadedFittedMesh;
}

UStaticMesh* ALBSpacecraftWIPPresentationActor::ResolveCargoCraftMesh()
{
	if (LBSpacecraftWIPPresentationPrivate::bBlockoutMeshyContent)
	{
		return nullptr;
	}
	if (!bCargoCraftLoadAttempted)
	{
		bCargoCraftLoadAttempted = true;
		LoadedCargoCraftMesh = CargoCraftMesh.LoadSynchronous();
	}
	return LoadedCargoCraftMesh;
}

UStaticMesh* ALBSpacecraftWIPPresentationActor::ResolveCargoChassisMesh()
{
	if (LBSpacecraftWIPPresentationPrivate::bBlockoutMeshyContent)
	{
		return nullptr;
	}
	if (!bCargoChassisLoadAttempted)
	{
		bCargoChassisLoadAttempted = true;
		LoadedCargoChassisMesh = CargoChassisMesh.LoadSynchronous();
	}
	return LoadedCargoChassisMesh;
}

UStaticMesh* ALBSpacecraftWIPPresentationActor::ResolveCargoAirframeMesh()
{
	if (LBSpacecraftWIPPresentationPrivate::bBlockoutMeshyContent)
	{
		return nullptr;
	}
	if (!bCargoAirframeLoadAttempted)
	{
		bCargoAirframeLoadAttempted = true;
		LoadedCargoAirframeMesh = CargoAirframeMesh.LoadSynchronous();
	}
	return LoadedCargoAirframeMesh;
}

UStaticMesh* ALBSpacecraftWIPPresentationActor::ResolveCargoFittedMesh()
{
	if (LBSpacecraftWIPPresentationPrivate::bBlockoutMeshyContent)
	{
		return nullptr;
	}
	if (!bCargoFittedLoadAttempted)
	{
		bCargoFittedLoadAttempted = true;
		LoadedCargoFittedMesh = CargoFittedMesh.LoadSynchronous();
	}
	return LoadedCargoFittedMesh;
}

UStaticMesh* ALBSpacecraftWIPPresentationActor::ResolveBuildFormMesh(
	ELBSpacecraftStage Stage, FName RecipeId)
{
	// Fall DOWN the ladder honestly: a missing form shows the previous
	// one; below Hull Fabrication (or with nothing loadable) the caller
	// draws the crate. Cargo units try their own forms first and fall
	// back to the Scout's, so a missing cargo asset never draws less.
	using namespace LBSpacecraftWIPPresentationPrivate;
	const bool bCargo = RecipeId == SpacecraftCargoRecipeId;
	UStaticMesh* Mesh = nullptr;
	if (Stage >= ELBSpacecraftStage::AssemblyStaging)
	{
		Mesh = bCargo ? ResolveCargoFittedMesh() : nullptr;
		if (Mesh == nullptr)
		{
			Mesh = ResolveFittedMesh();
		}
	}
	if (Mesh == nullptr && Stage >= ELBSpacecraftStage::ComponentFabrication)
	{
		Mesh = bCargo ? ResolveCargoAirframeMesh() : nullptr;
		if (Mesh == nullptr)
		{
			Mesh = ResolveAirframeMesh();
		}
	}
	if (Mesh == nullptr && Stage >= ELBSpacecraftStage::HullFabrication)
	{
		Mesh = bCargo ? ResolveCargoChassisMesh() : nullptr;
		if (Mesh == nullptr)
		{
			Mesh = ResolveChassisMesh();
		}
	}
	return Mesh;
}

bool ALBSpacecraftWIPPresentationActor::ResolveScoutV2Parts(
	UStaticMesh*& OutHull, UStaticMesh*& OutPropulsion,
	UStaticMesh*& OutPower, UStaticMesh*& OutElectronics,
	UStaticMesh*& OutNavigation, UStaticMesh*& OutInterior)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	if (!bScoutV2LoadAttempted)
	{
		bScoutV2LoadAttempted = true;
		LoadedScoutV2Hull = LoadObject<UStaticMesh>(nullptr, ScoutV2HullPath);
		LoadedScoutV2Propulsion =
			LoadObject<UStaticMesh>(nullptr, ScoutV2PropulsionPath);
		LoadedScoutV2Power =
			LoadObject<UStaticMesh>(nullptr, ScoutV2PowerPath);
		LoadedScoutV2Electronics =
			LoadObject<UStaticMesh>(nullptr, ScoutV2ElectronicsPath);
		LoadedScoutV2Navigation =
			LoadObject<UStaticMesh>(nullptr, ScoutV2NavigationPath);
		LoadedScoutV2Interior =
			LoadObject<UStaticMesh>(nullptr, ScoutV2InteriorPath);
		if (LoadedScoutV2Hull == nullptr
			|| LoadedScoutV2Propulsion == nullptr
			|| LoadedScoutV2Power == nullptr
			|| LoadedScoutV2Electronics == nullptr
			|| LoadedScoutV2Navigation == nullptr
			|| LoadedScoutV2Interior == nullptr)
		{
			// SAY SO. A silent partial load would draw a hull with
			// missing engines and call it finished, which is worse
			// than the honest single-mesh fallback this file already
			// uses everywhere else.
			UE_LOG(LogTemp, Warning, TEXT(
				"SPACECRAFT PRESENTER: Scout v002 six-part model is "
				"incomplete - falling back to the single-mesh craft"));
		}
	}
	OutHull = LoadedScoutV2Hull;
	OutPropulsion = LoadedScoutV2Propulsion;
	OutPower = LoadedScoutV2Power;
	OutElectronics = LoadedScoutV2Electronics;
	OutNavigation = LoadedScoutV2Navigation;
	OutInterior = LoadedScoutV2Interior;
	return OutHull != nullptr && OutPropulsion != nullptr
		&& OutPower != nullptr && OutElectronics != nullptr
		&& OutNavigation != nullptr && OutInterior != nullptr;
}

UStaticMesh* ALBSpacecraftWIPPresentationActor::ResolveCraftMesh()
{
	if (LBSpacecraftWIPPresentationPrivate::bBlockoutMeshyContent)
	{
		return nullptr;
	}
	if (!bCraftMeshLoadAttempted)
	{
		bCraftMeshLoadAttempted = true;
		LoadedCraftMesh = CraftMesh.LoadSynchronous();
		if (LoadedCraftMesh == nullptr)
		{
			UE_LOG(LogTemp, Warning, TEXT(
				"SPACECRAFT PRESENTER: craft mesh unavailable (%s) - "
				"falling back to the crate block"),
				*CraftMesh.ToString());
		}
	}
	return LoadedCraftMesh;
}

void ALBSpacecraftWIPPresentationActor::RefreshStations()
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	if (BuildAuthority == nullptr)
	{
		return;
	}

	TSet<FName> Live;
	for (const FLBSpacecraftStationRecord& Record :
		BuildAuthority->GetStations())
	{
		Live.Add(Record.StationId);
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(Record.DefinitionId);
		if (Definition == nullptr)
		{
			continue; // draws less, never more
		}
		if (Definition->bSiteBuilding)
		{
			// A BUILDING is not a machine: the shell layer draws the
			// ship factory (roof up on the world map, lifted when you
			// enter it), so it must not also get a machine block on
			// the floor inside itself.
			Live.Remove(Record.StationId);
			continue;
		}
		TObjectPtr<UStaticMeshComponent>* Existing =
			StationVisuals.Find(Record.StationId);
		UStaticMeshComponent* Component =
			Existing != nullptr ? Existing->Get() : nullptr;
		if (Component == nullptr)
		{
			Component = MakeBlockComponent(Record.StationId,
				SpacecraftStationColour(Record.DefinitionId));
			if (Component == nullptr)
			{
				continue;
			}
			StationVisuals.Add(Record.StationId, Component);
		}
		RefreshStationFloorPaint(Record, *Definition);
		if (!Definition->StageClassId.IsNone())
		{
			// A LINE STATION IS A WORK STATION, NOT A MACHINE (owner
			// 2026-08-26 evening: "the stations dont have machinery
			// only drones", restated 2026-08-28: "its suposed to be
			// just a work station like car manufacture").
			//
			// This used to say: if a mesh exists for this definition,
			// draw it and DESTROY the frame. The comment justified it
			// by claiming the generated gantry honoured the no-
			// machinery rule - but the asset it actually picked up is
			// SM_LB_ST_AssemblyBay, a full enclosed machine bay. So
			// the rule was stated and then overridden by whatever art
			// happened to be on disk, and the marked square the owner
			// asked for only ever appeared when art was MISSING.
			//
			// Now the frame is not a fallback, it IS the station: a
			// marked floor square straddling the track, an accent
			// border, the dock pads and a work light. The drones are
			// the workforce and the craft is the thing you watch. The
			// bay meshes stay in the project - they are wanted for the
			// SUB-ASSEMBLY buildings off the line, which are machines.
			//
			// CONCEPT PORTAL (owner-approved 2026-08-31): the
			// portal-frame station model now stands ON that marked
			// square - an open arch the craft passes through, tool
			// arms on the inner frame. The square keeps the ground
			// identity; the portal gives the station a body. Min-fit
			// into the footprint like every dressed station.
			RefreshLineStationFrame(Record, *Definition);
			RefreshStationBadge(Record, *Definition);
			RefreshStationStockpile(Record, *Definition);
			// The SPRAY BOOTH is a line station by stage class but has
			// its own bespoke presentation (booth mesh + glass panes,
			// built elsewhere). Dressing it with the portal on top of
			// that produced the owner's "this bit's a mess" frame
			// (2026-09-01): two presentations occupying one station.
			if (Record.DefinitionId == FName(TEXT("SprayBooth")))
			{
				Component->SetVisibility(false);
				continue;
			}
			if (UStaticMesh* PortalMesh =
				TryGetStationMesh(Record.DefinitionId))
			{
				if (Component->GetStaticMesh() != PortalMesh)
				{
					Component->SetStaticMesh(PortalMesh);
					Component->EmptyOverrideMaterials();
				}
				const FVector PortalSize =
					PortalMesh->GetBounds().BoxExtent * 2.0;
				float PortalFit = 1.f;
				if (PortalSize.X > 1.f && PortalSize.Y > 1.f)
				{
					// NEVER ENLARGE (owner's live frame, 2026-09-01):
					// the portal is imported at its true 8 m; min-fit
					// blew it up 1.7x into a tower that dwarfed the
					// 17 m gantry ("need to make the cranes bigger" -
					// the cranes were fine, the stations were bloated).
					// Concept meshes carry real size; fit only shrinks.
					PortalFit = FMath::Min(1.f, FMath::Min(
						Definition->FootprintCm.X / PortalSize.X,
						Definition->FootprintCm.Y / PortalSize.Y));
				}
				FTransform PortalTransform = Record.WorldTransform;
				PortalTransform.SetScale3D(FVector(PortalFit));
				// NO EXTRA YAW (owner's second live frame, 2026-09-01):
				// with stations now taking their yaw from the track
				// piece they stand on, the mesh's own axes already put
				// the arch ACROSS the travel direction - the earlier
				// +90 (added against a free-placed station) turned the
				// arch ALONG the track so the craft would hit the
				// columns. The station wears the piece rotation as-is.
				Component->SetWorldTransform(PortalTransform);
				Component->SetVisibility(true);
			}
			else
			{
				Component->SetVisibility(false);
			}
			continue;
		}
		if (UStaticMesh* RealMesh = TryGetStationMesh(Record.DefinitionId))
		{
			// Real derivative: game scale is baked, grounded at Z=0.
			// One mesh can dress several definitions (core line stations
			// share the crafting-family models), so uniform min-fit the
			// mesh into THIS definition's footprint.
			if (Component->GetStaticMesh() != RealMesh)
			{
				Component->SetStaticMesh(RealMesh);
				Component->EmptyOverrideMaterials();
			}
			const FVector MeshSize =
				RealMesh->GetBounds().BoxExtent * 2.0;
			// A LONG mesh lies along the footprint's long side: the
			// pallet rack (6 m by 1 m) stood end-on across its bay
			// otherwise (frame, 2026-09-02). Quarter turn when the
			// footprint and the mesh disagree about which axis is long.
			const bool bQuarterTurn = Definition != nullptr
				&& ((Definition->FootprintCm.X >= Definition->FootprintCm.Y)
					!= (MeshSize.X >= MeshSize.Y));
			const float MeshAlongX = bQuarterTurn ? MeshSize.Y : MeshSize.X;
			const float MeshAlongY = bQuarterTurn ? MeshSize.X : MeshSize.Y;
			float Fit = 1.f;
			if (Definition != nullptr
				&& MeshAlongX > 1.f && MeshAlongY > 1.f)
			{
				Fit = FMath::Min(
					Definition->FootprintCm.X / MeshAlongX,
					Definition->FootprintCm.Y / MeshAlongY);
			}
			FTransform MeshTransform = Record.WorldTransform;
			if (bQuarterTurn)
			{
				MeshTransform.SetRotation(Record.WorldTransform.GetRotation()
					* FRotator(0.f, 90.f, 0.f).Quaternion());
			}
			MeshTransform.SetScale3D(FVector(
				Fit * SpacecraftStationDressFit(Record.DefinitionId)));
			Component->SetWorldTransform(MeshTransform);
			continue;
		}
		// Engine cube is 100 cm; scale to footprint x height, sit on floor.
		FTransform BlockTransform = Record.WorldTransform;
		BlockTransform.SetScale3D(FVector(
			Definition->FootprintCm.X / 100.f,
			Definition->FootprintCm.Y / 100.f,
			SpacecraftStationBlockHeightCm / 100.f));
		BlockTransform.AddToTranslation(
			FVector(0.f, 0.f, SpacecraftStationBlockHeightCm * 0.5f));
		Component->SetWorldTransform(BlockTransform);
	}

	// Removed stations disappear.
	for (auto It = StationVisuals.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			if (It.Value() != nullptr)
			{
				It.Value()->DestroyComponent();
			}
			It.RemoveCurrent();
		}
	}
	for (auto It = LineStationFrames.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			DestroyLineStationFrame(It.Value());
			It.RemoveCurrent();
		}
	}
	for (auto It = StationFloorPaint.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			for (UDecalComponent* Decal : It.Value().Decals)
			{
				if (Decal != nullptr)
				{
					Decal->DestroyComponent();
				}
			}
			It.RemoveCurrent();
		}
	}
	// Badges and stockpiles leaked past removal (audit 2026-09-01):
	// a demolished station left its floating READY text and pallet
	// stacks rendered at the vacated spot for the rest of the session.
	for (auto It = StationBadges.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			if (It.Value() != nullptr)
			{
				It.Value()->DestroyComponent();
			}
			It.RemoveCurrent();
		}
	}
	for (auto It = StationIndicatorBars.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			if (It.Value() != nullptr)
			{
				It.Value()->DestroyComponent();
			}
			It.RemoveCurrent();
		}
	}
	for (auto It = StationStockStacks.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			for (UStaticMeshComponent* Stack : It.Value())
			{
				if (Stack != nullptr)
				{
					Stack->DestroyComponent();
				}
			}
			It.RemoveCurrent();
		}
	}
}

void ALBSpacecraftWIPPresentationActor::DestroyLineStationFrame(
	FLBSpacecraftLineStationFrame& Frame)
{
	for (UStaticMeshComponent* Part : Frame.Parts)
	{
		if (Part != nullptr)
		{
			Part->DestroyComponent();
		}
	}
	Frame.Parts.Reset();
	for (ULightComponent* Light : Frame.Lights)
	{
		if (Light != nullptr)
		{
			Light->DestroyComponent();
		}
	}
	Frame.Lights.Reset();
}

void ALBSpacecraftWIPPresentationActor::RefreshStationBadge(
	const FLBSpacecraftStationRecord& Record,
	const FLBSpacecraftStationDefinition& Definition)
{
	// RATE BADGE - every fact on it is read, never invented: the split
	// from GetFixingSplit, the live state from the coordinator's real
	// assignments. Palette indicator colours: working #BFE4FF, idle
	// #6E7C86 (the interface carries no hue; indicators are the one
	// sanctioned exception, and they are desaturated blues).
	TObjectPtr<UTextRenderComponent>& Badge =
		StationBadges.FindOrAdd(Record.StationId);
	if (Badge == nullptr)
	{
		Badge = NewObject<UTextRenderComponent>(this,
			UTextRenderComponent::StaticClass());
		Badge->SetupAttachment(RootComponent);
		Badge->SetHorizontalAlignment(EHTA_Center);
		Badge->SetWorldSize(64.f);
		Badge->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Badge->RegisterComponent();
	}
	FString Line1;
	if (BuildAuthority != nullptr && ProductionAuthority != nullptr)
	{
		FName RecipeId = NAME_None;
		for (const FLBSpacecraftUnitState& Unit :
			ProductionAuthority->GetUnits())
		{
			if (Unit.Stage != ELBSpacecraftStage::Dispatched)
			{
				RecipeId = Unit.RecipeId;
				break;
			}
		}
		TArray<FName> SplitStations;
		TArray<int32> SplitCounts;
		FString SplitReason;
		if (!RecipeId.IsNone() && BuildAuthority->GetFixingSplit(
			RecipeId, SplitStations, SplitCounts, SplitReason))
		{
			const int32 Index = SplitStations.Find(Record.StationId);
			if (Index != INDEX_NONE && SplitCounts.IsValidIndex(Index))
			{
				Line1 = FString::Printf(TEXT("%d · FITS %d"),
					Index + 1, SplitCounts[Index]);
			}
		}
	}
	bool bWorking = false;
	FString Line2 = TEXT("READY");
	if (Coordinator != nullptr)
	{
		for (const FLBSpacecraftRuntimeAssignment& Assignment :
			Coordinator->GetAssignments())
		{
			if (Assignment.StationId != Record.StationId)
			{
				continue;
			}
			bWorking = true;
			float Progress01 = 0.f;
			if (Coordinator->GetUnitCycleProgress(
				Assignment.UnitId, Progress01))
			{
				Line2 = FString::Printf(TEXT("FITTING %d%%"),
					FMath::RoundToInt(Progress01 * 100.f));
			}
			else
			{
				Line2 = TEXT("FITTING");
			}
			break;
		}
	}
	const FString Text = Line1.IsEmpty()
		? Line2 : FString::Printf(TEXT("%s\n%s"), *Line1, *Line2);
	Badge->SetText(FText::FromString(Text));
	Badge->SetTextRenderColor(bWorking
		? FColor(0xBF, 0xE4, 0xFF) : FColor(0x6E, 0x7C, 0x86));
	const float BadgeZ = 60.f + FMath::Max(
		820.f, Definition.FootprintCm.Y * 0.55f);
	Badge->SetWorldLocation(
		Record.WorldTransform.GetLocation() + FVector(0.f, 0.f, BadgeZ));
	// FACE THE LIVE CAMERA (audit 2026-09-01): Q/E rotates the camera
	// azimuth, and a TextRender quad is one-sided - the fixed yaw went
	// edge-on or backwards the moment the player turned. The pawn's
	// yaw IS the azimuth, so the badge follows it.
	float BadgeYaw = 180.f;
	if (ShellViewPawn.IsValid())
	{
		BadgeYaw = ShellViewPawn->GetActorRotation().Yaw + 180.f;
	}
	Badge->SetWorldRotation(FRotator(0.f, BadgeYaw, 0.f));

	// ROLE LIGHT ON THE FLOOR (audit 2026-09-01: six anonymous clones
	// with no state readable at play zoom). A bar along the pad's
	// aisle flank burns working-blue while the station holds a craft
	// and idle-grey otherwise - the adopted indicator pair doing
	// exactly the job it was chosen for.
	TObjectPtr<UStaticMeshComponent>& IndicatorBar =
		StationIndicatorBars.FindOrAdd(Record.StationId);
	if (IndicatorBar == nullptr)
	{
		IndicatorBar = MakeBlockComponent(FName(*FString::Printf(
			TEXT("%s_Indicator"), *Record.StationId.ToString())),
			LBSpacecraftPalette::IndicatorIdle);
		if (IndicatorBar != nullptr)
		{
			IndicatorBar->SetCastShadow(false);
		}
	}
	if (IndicatorBar != nullptr)
	{
		const FQuat StationQuat = Record.WorldTransform.GetRotation();
		const FVector BarAt = Record.WorldTransform.GetLocation()
			+ StationQuat.RotateVector(FVector(0.f,
				Definition.FootprintCm.Y * 0.5f + 60.f, 0.f));
		IndicatorBar->SetWorldTransform(FTransform(StationQuat,
			FVector(BarAt.X, BarAt.Y, 26.f),
			FVector(Definition.FootprintCm.X / 100.f * 0.55f,
				0.4f, 0.34f)));
		if (UMaterialInstanceDynamic* BarMID =
			Cast<UMaterialInstanceDynamic>(IndicatorBar->GetMaterial(0)))
		{
			BarMID->SetVectorParameterValue(TEXT("Color"), bWorking
				? LBSpacecraftPalette::IndicatorWorking
				: LBSpacecraftPalette::IndicatorIdle);
		}
	}
}

void ALBSpacecraftWIPPresentationActor::RefreshStationStockpile(
	const FLBSpacecraftStationRecord& Record,
	const FLBSpacecraftStationDefinition& Definition)
{
	// VISIBLE STOCKPILE - the benchmark machines show their contents;
	// ours shows the station store's REAL fill as pallet stacks. Zero
	// pallets when the store is empty is the honest look, not a bug.
	TArray<TObjectPtr<UStaticMeshComponent>>& Stacks =
		StationStockStacks.FindOrAdd(Record.StationId);
	int32 Wanted = 0;
	if (InventoryAuthority != nullptr)
	{
		const FName StoreId(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		const int32 Used = InventoryAuthority->GetUsedUnits(StoreId);
		const int32 Cap = InventoryAuthority->GetCapacityUnits(StoreId);
		if (Used > 0 && Cap > 0)
		{
			// At most two stacks (owner 2026-09-02: "the first station
			// is a mess with all the parts on pallets"): the stockpile
			// says "stocked" or "nearly full", not "warehouse".
			Wanted = FMath::Clamp(
				FMath::RoundToInt(2.f * Used / (float)Cap), 1, 2);
		}
	}
	// THE STATION'S OWN COMPONENT, not always hull (audit 2026-09-01:
	// presentation contradicted the ledger it claims to mirror - every
	// stockpile drew hull sections even at an electronics station).
	// The first allocated component names the pallets; hull is only
	// the fallback for an unallocated station.
	FName StockComponent(TEXT("Component.Hull"));
	if (Record.AllocatedComponents.Num() > 0)
	{
		StockComponent = Record.AllocatedComponents[0];
	}
	TArray<FName> PalletKeys;
	GetKitPalletCandidates(StockComponent, PalletKeys);
	if (PalletKeys.Num() == 0)
	{
		GetKitPalletCandidates(FName(TEXT("Component.Hull")), PalletKeys);
	}
	while (Stacks.Num() > Wanted)
	{
		if (Stacks.Last() != nullptr)
		{
			Stacks.Last()->DestroyComponent();
		}
		Stacks.Pop();
	}
	for (int32 Index = 0; Index < Wanted; ++Index)
	{
		// One pallet type per station, the middle of the pool - a row
		// of nose, tube and tail sections read as scattered parts, not
		// stock.
		UStaticMesh* PalletMesh = PalletKeys.Num() > 0
			? TryGetStationMesh(PalletKeys[PalletKeys.Num() / 2])
			: nullptr;
		if (PalletMesh == nullptr)
		{
			return;
		}
		if (!Stacks.IsValidIndex(Index))
		{
			UStaticMeshComponent* Stack =
				NewObject<UStaticMeshComponent>(this,
					UStaticMeshComponent::StaticClass());
			Stack->SetupAttachment(RootComponent);
			Stack->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Stack->RegisterComponent();
			Stacks.Add(Stack);
		}
		UStaticMeshComponent* Stack = Stacks[Index];
		if (Stack->GetStaticMesh() != PalletMesh)
		{
			Stack->SetStaticMesh(PalletMesh);
			Stack->EmptyOverrideMaterials();
		}
		const FVector Base = Record.WorldTransform.GetLocation();
		// Beyond the far flank, never at the pad's ends (the track).
		const float OutY = -(Definition.FootprintCm.Y * 0.5f + 320.f);
		const float RowX = (Index - (Wanted - 1) * 0.5f) * 300.f;
		// IN THE STATION'S FRAME, not world axes (audit 2026-09-01):
		// stations take their yaw from the track now, and a world-axis
		// flank put the pallets ON the track for any rotated station.
		const FQuat StationYaw = Record.WorldTransform.GetRotation();
		Stack->SetWorldLocationAndRotation(
			Base + StationYaw.RotateVector(FVector(RowX, OutY, 0.f)),
			StationYaw);
	}
}

int32 ALBSpacecraftWIPPresentationActor::GetBayPaintDecalCount() const
{
	int32 Count = 0;
	for (const TPair<FName, FLBSpacecraftFloorPaint>& It : StationFloorPaint)
	{
		Count += It.Value.Decals.Num();
	}
	return Count;
}

int32 ALBSpacecraftWIPPresentationActor::GetBayPaintedDecalCount() const
{
	int32 Count = 0;
	for (const TPair<FName, FLBSpacecraftFloorPaint>& It : StationFloorPaint)
	{
		for (const UDecalComponent* Decal : It.Value.Decals)
		{
			if (Decal == nullptr)
			{
				continue;
			}
			const UMaterialInterface* Bound = Decal->GetDecalMaterial();
			const UMaterial* Base =
				Bound != nullptr ? Bound->GetMaterial() : nullptr;
			if (Base != nullptr
				&& Base->MaterialDomain == MD_DeferredDecal)
			{
				++Count;
			}
		}
	}
	return Count;
}

FLinearColor ALBSpacecraftWIPPresentationActor::InspectionSweepColour(
	int32 DefectsFound, int32 DefectsTotal)
{
	// Clean scan: the blue-white of every other working indicator on
	// this floor. Faults pull it toward warning orange - the owner's
	// settled palette, not a colour invented for the occasion.
	const FLinearColor Clean = LBSpacecraftPalette::IndicatorWorking; // clean/working indicator
	const FLinearColor Fault = LBSpacecraftPalette::IndicatorFault; // fault indicator
	if (DefectsFound <= 0 || DefectsTotal <= 0)
	{
		return Clean;
	}
	const float Alpha = FMath::Clamp(
		static_cast<float>(DefectsFound)
			/ static_cast<float>(FMath::Max(DefectsTotal, 1)), 0.f, 1.f);
	return FMath::Lerp(Clean, Fault, Alpha);
}

void ALBSpacecraftWIPPresentationActor::RefreshInspectionSweep()
{
	FName UnitId;
	FName StationId;
	float Progress = 0.f;
	int32 Found = 0;
	const bool bSweeping = Coordinator != nullptr
		&& Coordinator->GetInspectionSweep(UnitId, StationId, Progress,
			Found);
	TObjectPtr<UStaticMeshComponent>* UnitVisual =
		bSweeping ? UnitVisuals.Find(UnitId) : nullptr;
	UStaticMeshComponent* Craft =
		UnitVisual != nullptr ? UnitVisual->Get() : nullptr;
	if (!bSweeping || Craft == nullptr)
	{
		// Nothing under inspection: the bar goes away rather than
		// hanging in the air over an empty rig.
		if (InspectionSweepBar != nullptr)
		{
			InspectionSweepBar->DestroyComponent();
			InspectionSweepBar = nullptr;
			InspectionSweepMID = nullptr;
		}
		return;
	}
	if (InspectionSweepBar == nullptr)
	{
		InspectionSweepBar = MakeBlockComponent(
			FName(TEXT("LB_InspectionSweep")),
			InspectionSweepColour(0, 0));
		if (InspectionSweepBar == nullptr)
		{
			return;
		}
		// A beam is light, not machinery: it throws nothing and takes
		// no paint.
		InspectionSweepBar->SetCastShadow(false);
		InspectionSweepBar->SetReceivesDecals(false);
	}
	// Ride the craft's own bounds so the sweep fits whatever tier is
	// on the rig - a Cargo is half as long again as a Scout.
	const FVector Extent = Craft->Bounds.BoxExtent;
	const FVector Centre = Craft->Bounds.Origin;
	const float Length = FMath::Max(Extent.X * 2.f, 100.f);
	const float Travel = (FMath::Clamp(Progress, 0.f, 1.f) - 0.5f) * Length;
	FTransform Where = FTransform::Identity;
	Where.SetLocation(Centre + FVector(Travel, 0.f, 0.f));
	Where.SetScale3D(FVector(12.f, FMath::Max(Extent.Y * 2.2f, 100.f),
		FMath::Max(Extent.Z * 2.2f, 100.f)) / 100.f);
	InspectionSweepBar->SetWorldTransform(Where);
	const FLinearColor Colour = InspectionSweepColour(Found,
		FMath::Max(Found, 1));
	if (InspectionSweepMID == nullptr)
	{
		InspectionSweepMID = Cast<UMaterialInstanceDynamic>(
			InspectionSweepBar->GetMaterial(0));
	}
	if (InspectionSweepMID != nullptr)
	{
		InspectionSweepMID->SetVectorParameterValue(TEXT("Color"), Colour);
	}
}

void ALBSpacecraftWIPPresentationActor::RefreshStationFloorPaint(
	const FLBSpacecraftStationRecord& Record,
	const FLBSpacecraftStationDefinition& Definition)
{
	FLBSpacecraftFloorPaint& Paint =
		StationFloorPaint.FindOrAdd(Record.StationId);
	if (Paint.Decals.Num() > 0
		&& Paint.PaintedAt.Equals(Record.WorldTransform, 1.f))
	{
		return;   // already painted where it stands
	}
	for (UDecalComponent* Old : Paint.Decals)
	{
		if (Old != nullptr)
		{
			Old->DestroyComponent();
		}
	}
	Paint.Decals.Reset();
	Paint.PaintedAt = Record.WorldTransform;

	// The project's own decal materials, authored by
	// Scripts/build_bay_paint_decals_v001.py: procedural hazard
	// banding (no baked words, tunable colours) and a scuff patch
	// that fades at its edges. The Fab materials used here before
	// were decal-domain too and were NOT the reason the paint went
	// unseen - that is still open. Absent materials leave the floor
	// bare rather than blocking a placement.
	UMaterialInterface* HazardMaterial = LoadObject<UMaterialInterface>(
		nullptr,
		TEXT("/Game/LineBoss/Materials/Decals/MI_LB_BayHazard_v001")
		TEXT(".MI_LB_BayHazard_v001"));
	// v002, and the version matters. v001's wear decal drove OPACITY
	// from how DARK a texel was while using the texture's own RGB as
	// base colour, on the assumption the source was dark marks on a
	// pale plate. It is mostly dark, so the assumption inverted: the
	// darkest texels painted at FULL opacity in near-black and every
	// work-station bay rendered as a black pit in a bright hall. It
	// read as "the bay floor looks muddy" - a taste problem - for far
	// longer than it should have. v002 tints the grime itself and caps
	// its opacity at 0.30, so the pad tone still leads. Do not point
	// this back at v001; it is kept only as evidence of the fault.
	UMaterialInterface* WearMaterial = LoadObject<UMaterialInterface>(
		nullptr,
		TEXT("/Game/LineBoss/Materials/Decals/MI_LB_BayWear_v002")
		TEXT(".MI_LB_BayWear_v002"));
	if (HazardMaterial == nullptr && WearMaterial == nullptr)
	{
		return;
	}

	const FTransform& Where = Record.WorldTransform;
	const float HalfX = Definition.FootprintCm.X * 0.5f;
	const float HalfY = Definition.FootprintCm.Y * 0.5f;
	constexpr float StripCm = 90.f;    // painted band width
	constexpr float DepthCm = 60.f;    // shallow: the deck only

	auto AddDecal = [&](const TCHAR* Part, int32 Index,
		UMaterialInterface* Material, const FVector& LocalCentre,
		float HalfAlongX, float HalfAlongY, int32 SortOrder)
	{
		if (Material == nullptr)
		{
			return;
		}
		const FName Key(*FString::Printf(TEXT("%s_Paint_%s%d"),
			*Record.StationId.ToString(), Part, Index));
		UDecalComponent* Decal = NewObject<UDecalComponent>(this,
			UDecalComponent::StaticClass(), Key);
		Decal->SetupAttachment(RootComponent);
		// SIZE BEFORE TRANSFORM: the render proxy bakes the decal's
		// box from DecalSize at the moment the transform updates, so
		// assigning the field afterwards leaves the proxy at the
		// 128x256x256 default and the paint comes out the wrong size.
		Decal->DecalSize = FVector(DepthCm, HalfAlongY, HalfAlongX);
		Decal->RegisterComponent();
		Decal->SetDecalMaterial(Material);
		const UMaterial* Base = Material->GetMaterial();
		if (Base == nullptr || Base->MaterialDomain != MD_DeferredDecal)
		{
			// The engine ACCEPTS a wrong-domain material and quietly
			// renders the default decal instead (an editor toast is
			// its only complaint), so the bad paint is invisible
			// rather than absent. Say it out loud.
			UE_LOG(LogTemp, Error,
				TEXT("LB bay paint: %s is not a Deferred Decal material, "
					"so %s renders the engine default instead"),
				*Material->GetPathName(), *Key.ToString());
		}
		// A decal projects along its local -X: pitching -90 aims it at
		// the floor, and the station's yaw carries the paint round with
		// it. Local Y then spans world Y, local Z spans world X.
		FRotator Facing = Where.Rotator();
		Facing.Pitch -= 90.f;
		Decal->SetWorldRotation(Facing);
		Decal->SetWorldLocation(Where.GetLocation()
			+ Where.GetRotation().RotateVector(LocalCentre));
		Decal->SetSortOrder(SortOrder);
		Decal->SetFadeScreenSize(0.0005f);
		Decal->MarkRenderStateDirty();
		Paint.Decals.Add(Decal);
	};

	// Wear patch first (under the paint), then the hazard border: two
	// bands across the line and two along it.
	AddDecal(TEXT("Wear"), 0, WearMaterial, FVector(0.f, 0.f, 0.f),
		HalfX * 0.85f, HalfY * 0.85f, 0);
	for (int32 Side = 0; Side < 2; ++Side)
	{
		const float Sign = Side == 0 ? -1.f : 1.f;
		AddDecal(TEXT("EdgeX"), Side, HazardMaterial,
			FVector(Sign * (HalfX - StripCm * 0.5f), 0.f, 0.f),
			StripCm * 0.5f, HalfY, 1);
		AddDecal(TEXT("EdgeY"), Side, HazardMaterial,
			FVector(0.f, Sign * (HalfY - StripCm * 0.5f), 0.f),
			HalfX, StripCm * 0.5f, 1);
	}
}

void ALBSpacecraftWIPPresentationActor::RefreshLineStationFrame(
	const FLBSpacecraftStationRecord& Record,
	const FLBSpacecraftStationDefinition& Definition)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	// NO machinery on line stations (owner 2026-08-26 evening: "the
	// stations dont have machinery only drones") - the frame is pads,
	// columns, beams and the drone dock ring; the workforce is the
	// drones themselves.
	FLBSpacecraftLineStationFrame& Frame =
		LineStationFrames.FindOrAdd(Record.StationId);
	// Rebuild only when the visible state actually changed - the frame
	// is many components and must never churn per tick (the command
	// panel taught that lesson).
	// THE KIT DOLLY (owner 2026-08-28: "so all the parts for that
	// station for each ship has its own dolly of parts").
	//
	// Its signature is part of the rebuild guard. The frame must not
	// churn per tick, but the dolly is the one part of it that changes
	// as the station consumes stock - guard on drones alone and the
	// crates would freeze at whatever they were when a drone was last
	// hired.
	FString KitNow;
	for (const FName& Component : Record.AllocatedComponents)
	{
		const bool bHeld = HasKitComponent(Record.StationId, Component);
		KitNow += FString::Printf(TEXT("%s=%d;"),
			*Component.ToString(), bHeld ? 1 : 0);
	}
	if (Frame.Parts.Num() > 0
		&& Frame.InstalledDrones == Record.InstalledDrones
		&& Frame.KitSignature == KitNow)
	{
		return;
	}
	Frame.KitSignature = KitNow;
	DestroyLineStationFrame(Frame);
	Frame.InstalledDrones = Record.InstalledDrones;

	const FTransform& Where = Record.WorldTransform;
	const float FootX = Definition.FootprintCm.X;
	const float FootY = Definition.FootprintCm.Y;
	auto AddBlock = [&](const TCHAR* Part, int32 Index,
		const FLinearColor& Colour, const FVector& LocalCentre,
		const FVector& SizeCm)
	{
		const FName Key(*FString::Printf(TEXT("%s_LF_%s%d"),
			*Record.StationId.ToString(), Part, Index));
		UStaticMeshComponent* Block = MakeBlockComponent(Key, Colour);
		if (Block == nullptr)
		{
			return;
		}
		FTransform T = Where;
		T.AddToTranslation(
			Where.GetRotation().RotateVector(LocalCentre));
		T.SetScale3D(SizeCm / 100.f);
		Block->SetWorldTransform(T);
		Frame.Parts.Add(Block);
	};

	// PALLETLOADS_v001 (2026-08-30): the real per-component pallet(s)
	// for one kit bay, at LocalCentre (station-local, matching AddBlock's
	// convention). Single-candidate and pick-one-of-several components
	// spawn one mesh at LocalCentre; ShouldAssembleKitPalletsTogether
	// components (Hull) instead lay every candidate out nose-to-aft
	// along local Y, each touching the last, centred as a WHOLE on
	// LocalCentre - "the hull parts need to be put together" (owner).
	// Real per-part lengths, not a guessed spacing constant: a generic
	// spacing either overlaps the biggest section or leaves a gap after
	// the smallest.
	auto AddKitPallets = [&](FName ComponentId, int32 Bay,
		const FVector& LocalCentre)
	{
		TArray<FName> Candidates;
		GetKitPalletCandidates(ComponentId, Candidates);
		if (Candidates.Num() == 0)
		{
			return false;
		}
		if (!ShouldAssembleKitPalletsTogether(ComponentId))
		{
			const int32 PickIndex = ComputeKitPalletCandidateIndex(
				Record.StationId, Bay, Candidates.Num());
			UStaticMesh* PalletMesh =
				TryGetStationMesh(Candidates[PickIndex]);
			if (PalletMesh == nullptr)
			{
				return true;
			}
			const FName PalletKey(*FString::Printf(
				TEXT("%s_Pallet%d"), *Record.StationId.ToString(), Bay));
			UStaticMeshComponent* PalletComp =
				NewObject<UStaticMeshComponent>(this,
					UStaticMeshComponent::StaticClass(), PalletKey);
			PalletComp->SetStaticMesh(PalletMesh);
			PalletComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			PalletComp->SetCastShadow(true);
			PalletComp->SetupAttachment(RootComponent);
			PalletComp->RegisterComponent();
			FTransform T = Where;
			T.AddToTranslation(Where.GetRotation().RotateVector(
				LocalCentre));
			T.SetRotation(T.GetRotation()
				* FQuat(FRotator(0.f, 90.f, 0.f)));
			PalletComp->SetWorldTransform(T);
			Frame.Parts.Add(PalletComp);
			return true;
		}
		// ASSEMBLE TOGETHER: resolve every mesh first (need each one's
		// own length before any position can be placed), then lay them
		// end to end along local Y, centred on LocalCentre.
		TArray<UStaticMesh*> Meshes;
		TArray<float> LengthsCm;
		for (const FName& Key : Candidates)
		{
			UStaticMesh* Mesh = TryGetStationMesh(Key);
			Meshes.Add(Mesh);
			const float LengthCm = Mesh != nullptr
				? Mesh->GetBounds().BoxExtent.Y * 2.f : 0.f;
			LengthsCm.Add(LengthCm);
		}
		TArray<float> CentresCm;
		ComputeSequentialLayoutCentresCm(LengthsCm, CentresCm);
		for (int32 Index = 0; Index < Meshes.Num(); ++Index)
		{
			if (Meshes[Index] == nullptr)
			{
				continue;
			}
			const float PieceCentreY = CentresCm[Index];
			const FName PalletKey(*FString::Printf(
				TEXT("%s_Pallet%d_%d"), *Record.StationId.ToString(), Bay,
				Index));
			UStaticMeshComponent* PalletComp =
				NewObject<UStaticMeshComponent>(this,
					UStaticMeshComponent::StaticClass(), PalletKey);
			PalletComp->SetStaticMesh(Meshes[Index]);
			PalletComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			PalletComp->SetCastShadow(true);
			PalletComp->SetupAttachment(RootComponent);
			PalletComp->RegisterComponent();
			FTransform T = Where;
			T.AddToTranslation(Where.GetRotation().RotateVector(
				LocalCentre + FVector(PieceCentreY, 0.f, 0.f)));
			// The sections lie along the line on the far flank; the
			// pallet meshes were modelled lying along local Y.
			T.SetRotation(T.GetRotation()
				* FQuat(FRotator(0.f, 90.f, 0.f)));
			PalletComp->SetWorldTransform(T);
			Frame.Parts.Add(PalletComp);
		}
		return true;
	};

	// Lifted from 0.42: against the warm mid-grey floor and the warmer
	// sun the old pad read as a black hole rather than a marked bay.
	// THE BAY'S COLOUR (owner 2026-08-28: "we need some color on it").
	//
	// When line stations stopped being machine MESHES and became
	// procedural work stations, they quietly stopped using the palette:
	// every colour here is a literal, so the Machine Amber tuned to the
	// Car Manufacture reference applied to nothing on the line. The bay
	// came out a grey square with orange trim.
	//
	// These now carry the reference's own separation - amber machinery
	// as the most colourful thing on the floor, yellow-and-black hazard
	// banding, blue-white indicators, and a floor that stays out of
	// their way. Literals still, because MakeBlockComponent paints a
	// dynamic instance rather than taking a material - but literals
	// that MATCH the palette instead of ignoring it.
	// NOTHING SITS ON THE LINE (owner 2026-09-02: "make sure nothing
	// blocks the line like drone charging docks etc"). A station's long
	// side runs along the line, so its ±X ends ARE the track corridor.
	// Everything that serves the station lives on the FLANKS: the near
	// flank (+Y local, the camera side, low things only) takes the crew
	// docks, slot pads, cable runs and cabinet; the far flank (-Y) takes
	// the tool tower at its upstream corner and the kit dolly along the
	// rest; the stockpile stands beyond the far flank.
	const FLinearColor MachineAmber = LBSpacecraftPalette::MachineAmber; // machine accent, was V 0.94 against a 0.66 ceiling
	const FLinearColor PadTone(0.46f, 0.45f, 0.43f);
	// Safety yellow, not the old dull orange: the references use
	// yellow-and-black for floor hazard, and it separates from the
	// amber machinery instead of blurring into it.
	const FLinearColor BorderOrange = LBSpacecraftPalette::Hazard; // station border - a third near-identical yellow
	const FLinearColor SlotLit(0.42f, 0.76f, 1.00f);
	const FLinearColor SlotDark(0.09f, 0.09f, 0.11f);

	// The work-station shape (owner: "the stations are basically
	// squares", and 2026-08-28 pointing at BOTH Car Manufacture and
	// Production Line: "its suposed to be just a work station"): one
	// marked floor square straddling the track, a hazard border, and
	// the dock pads along the two outer edges. Nothing stands up - the
	// drones are the station.
	AddBlock(TEXT("Pad"), 0, PadTone,
		FVector(0.f, 0.f, 4.f), FVector(FootX, FootY, 8.f));
	// HAZARD BANDS, properly wide. Both references lean on floor
	// striping to break up open ground and say where a zone begins -
	// Production Line's yellow-and-black edging is doing as much work
	// as its robots. A 16 cm pinstripe read as nothing from the play
	// camera; these are 70 cm and alternate with the pad tone so they
	// carry the striped look at a distance rather than needing a
	// texture nobody has authored yet.
	// The bay outline, WIDER and a little higher off the pad (the
	// side-by-side against Car Manufacture, 2026-09-02: their yellow bay
	// tape is bright and wide, ours read dim under the locked exposure).
	// Same palette token - Hazard is exempt from the saturation ceiling
	// - just more of it, lifted clear of the pad's own shadow.
	const float BandCm = 100.f;
	for (int32 Side = 0; Side < 2; ++Side)
	{
		const float SideSign = Side == 0 ? -1.f : 1.f;
		AddBlock(TEXT("BorderX"), Side, BorderOrange,
			FVector(SideSign * (FootX * 0.5f - BandCm * 0.5f), 0.f, 12.f),
			FVector(BandCm, FootY, 4.f));
		AddBlock(TEXT("BorderY"), Side, BorderOrange,
			FVector(0.f, SideSign * (FootY * 0.5f - BandCm * 0.5f), 12.f),
			FVector(FootX, BandCm, 4.f));
		// The dark half of the stripe: five dashes along each band, so
		// the edge reads as hazard tape and not as a plain orange line.
		for (int32 Dash = 0; Dash < 5; ++Dash)
		{
			const float AlongY = -FootY * 0.5f
				+ FootY * (Dash * 2 + 1) / 10.f;
			AddBlock(TEXT("DashX"), Side * 5 + Dash, SlotDark,
				FVector(SideSign * (FootX * 0.5f - BandCm * 0.5f),
					AlongY, 10.f),
				FVector(BandCm, FootY / 12.f, 3.f));
			const float AlongX = -FootX * 0.5f
				+ FootX * (Dash * 2 + 1) / 10.f;
			AddBlock(TEXT("DashY"), Side * 5 + Dash, SlotDark,
				FVector(AlongX,
					SideSign * (FootY * 0.5f - BandCm * 0.5f), 10.f),
				FVector(FootX / 12.f, BandCm, 3.f));
		}
		// Four dock pads per outer edge: lit = a drone is installed in
		// that slot, dark = empty. The visible n/8 the panel counts.
		for (int32 Slot = 0; Slot < 4; ++Slot)
		{
			const int32 SlotIndex = Side * 4 + Slot;
			const bool bFilled = SlotIndex < Record.InstalledDrones;
			// Eight slot pads in ONE row along the near flank, not four
			// at each end of the pad (the ends are the track).
			(void)SideSign;
			const float SlotAlongX = -FootX * 0.5f + 120.f
				+ (FootX - 240.f) * (SlotIndex + 0.5f) / 8.f;
			AddBlock(TEXT("Dock"), SlotIndex,
				bFilled ? SlotLit : SlotDark,
				FVector(SlotAlongX, FootY * 0.5f - 110.f, 10.f),
				FVector(150.f, 150.f, 6.f));
		}
	}
	// THE LIFT: ONE RAM IN THE MIDDLE (owner 2026-08-28: "the station
	// will have to lift the ship up ... to be worked on", then "think
	// there should just be 1 in middle").
	//
	// A single central column is the right answer and not just the
	// simpler one: it holds the craft by its centre and leaves the
	// ENTIRE underside open. Four corner posts - which is what this
	// was first - fenced the ground crew out of exactly the space they
	// were hired to work in.
	//
	// Built here but DRIVEN in the tick, because it is the one part of
	// a work station that moves.
	{
		// PHASE C (Docs/LOOK_JUDGEMENT_AND_PLAN_v001.md): a station is a
		// machine, not a slab. ONE TOOL TOWER on the FAR flank across
		// the line - never between the camera and the craft (the first
		// blockout's near tower hid the hero) - and a LOW cabinet on
		// the near flank that hides nothing. The Meshy models
		// (StationDress_v001) dress both when they load; the code
		// blockout stands in when they do not. The camera sits at -X
		// looking +X; a yaw-90 station's local -Y is world +X, far.
		{
			const FLinearColor TowerTone = LBSpacecraftPalette::MachineHousingPale;
			const FLinearColor TowerCap = LBSpacecraftPalette::MachineAmber;
			const FLinearColor TowerFoot = LBSpacecraftPalette::StructureGraphite;
			const FLinearColor TowerLight = LBSpacecraftPalette::IndicatorWorking;
			const float FlankY = -(FootY * 0.5f - 130.f);
			// Upstream far corner, so the kit dolly can run along the
			// rest of the far flank without meeting it.
			const float TowerX = -(FootX * 0.5f - 230.f);
			auto PlaceDress = [&](const TCHAR* Part, UStaticMesh* Mesh,
				const FVector& LocalAt, float LocalYawDeg,
				const FLinearColor& Tint)
			{
				const FName Key(*FString::Printf(TEXT("%s_LF_%s"),
					*Record.StationId.ToString(), Part));
				UStaticMeshComponent* Piece = NewObject<UStaticMeshComponent>(
					this, UStaticMeshComponent::StaticClass(), Key);
				Piece->SetStaticMesh(Mesh);
				Piece->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Piece->SetCastShadow(true);
				Piece->SetupAttachment(RootComponent);
				Piece->RegisterComponent();
				// The surface family tints through BaseTint; a material
				// without the parameter simply stays graphite.
				if (UMaterialInterface* Base = Piece->GetMaterial(0))
				{
					UMaterialInstanceDynamic* Tinted =
						UMaterialInstanceDynamic::Create(Base, Piece);
					Tinted->SetVectorParameterValue(TEXT("BaseTint"), Tint);
					for (int32 Slot = 0; Slot < Piece->GetNumMaterials(); ++Slot)
					{
						Piece->SetMaterial(Slot, Tinted);
					}
				}
				FTransform T = Where;
				T.AddToTranslation(Where.GetRotation().RotateVector(LocalAt));
				T.SetRotation(Where.GetRotation()
					* FRotator(0.f, LocalYawDeg, 0.f).Quaternion());
				T.SetScale3D(FVector::OneVector);
				Piece->SetWorldTransform(T);
				Frame.Parts.Add(Piece);
			};
			if (UStaticMesh* TowerMesh =
				TryGetStationMesh(FName(TEXT("Station.ToolTower"))))
			{
				// Its arm face looks at the craft (local +Y).
				PlaceDress(TEXT("ToolTower"), TowerMesh,
					FVector(TowerX, FlankY, 0.f), 90.f, TowerTone);
				AddBlock(TEXT("TowerCap"), 0, TowerCap,
					FVector(TowerX, FlankY, 572.f), FVector(180.f, 150.f, 24.f));
				AddBlock(TEXT("TowerLight"), 0, TowerLight,
					FVector(TowerX, FlankY + 68.f, 330.f), FVector(90.f, 6.f, 360.f));
			}
			else
			{
				AddBlock(TEXT("TowerFoot"), 0, TowerFoot,
					FVector(TowerX, FlankY, 20.f), FVector(260.f, 220.f, 40.f));
				AddBlock(TEXT("Tower"), 0, TowerTone,
					FVector(TowerX, FlankY, 300.f), FVector(200.f, 170.f, 520.f));
				AddBlock(TEXT("TowerCap"), 0, TowerCap,
					FVector(TowerX, FlankY, 580.f), FVector(230.f, 200.f, 36.f));
				AddBlock(TEXT("TowerLight"), 0, TowerLight,
					FVector(TowerX, FlankY + 90.f, 330.f), FVector(140.f, 8.f, 380.f));
				AddBlock(TEXT("TowerArm"), 0, TowerCap,
					FVector(TowerX, FlankY + 250.f, 500.f), FVector(50.f, 330.f, 44.f));
				AddBlock(TEXT("TowerArmHead"), 0, TowerFoot,
					FVector(TowerX, FlankY + 420.f, 470.f), FVector(90.f, 60.f, 90.f));
			}
			if (UStaticMesh* CabinetMesh =
				TryGetStationMesh(FName(TEXT("Station.ToolCabinet"))))
			{
				// Near flank, off to one side of the crew docks, low.
				PlaceDress(TEXT("ToolCabinet"), CabinetMesh,
					FVector(FootX * 0.28f, FootY * 0.5f - 80.f, 0.f), -90.f,
					TowerTone);
			}
		}
		const FLinearColor RamTone = MachineAmber;
		// The saddle the craft rests on reads DARK against the amber
		// column, so the contact point is findable at a glance.
		const FLinearColor SaddleTone(0.16f, 0.16f, 0.18f);
		// A TELESCOPIC RAM: three nested stages, widest at the bottom.
		// Each stage runs from the floor to its own share of the
		// travel, so retracted they sit inside one another and
		// extended they step inward - which is what a telescopic ram
		// actually looks like. A single box being stretched reads as
		// neither a piston nor a scissor.
		// THE MODELLED LIFT, five separate meshes because the game
		// moves them independently. The saddle used to be the one block
		// on a station that never got a mesh - a 7.2 x 3.4 m untextured
		// slab lying on the concrete, which the owner spotted as "a
		// couple of cubes that need removing" (2026-08-29). It is a
		// beam frame with four contact pads now.
		// NOT GATED (corrected same day): all five LiftCradle pieces
		// have an organised, individually-named promoted source at
		// SourceAssets/Spacecraft/LiftCradle_v001/ - direct evidence
		// this is finished work, not a folder-name guess.
		auto LoadLift = [](const TCHAR* Piece) -> UStaticMesh*
		{
			return LoadObject<UStaticMesh>(nullptr, *FString::Printf(
				TEXT("/Game/LineBoss/Candidates/Spacecraft/")
				TEXT("LiftCradle_v001/LB_Lift_%s/StaticMeshes/")
				TEXT("LB_Lift_%s.LB_Lift_%s"), Piece, Piece, Piece));
		};
		// Authored heights, measured from the delivered model. The
		// stages sit at these Z when fully extended and slide down from
		// them; the tick needs the same numbers, so they live here
		// where the mesh they describe is placed.
		const TCHAR* StageNames[SpacecraftLiftStages] = {
			TEXT("lift_stage_1"), TEXT("lift_stage_2"),
			TEXT("lift_stage_3") };
		const float StageRestZCm[SpacecraftLiftStages] =
			{ 12.f, 52.f, 132.f };

		if (UStaticMesh* BaseMesh = LoadLift(TEXT("lift_base")))
		{
			const FName BaseKey(*FString::Printf(
				TEXT("%s_LF_LiftBase"), *Record.StationId.ToString()));
			if (UStaticMeshComponent* Base =
				MakeBlockComponent(BaseKey, RamTone))
			{
				Base->SetStaticMesh(BaseMesh);
				for (int32 Slot = 0;
					Slot < BaseMesh->GetStaticMaterials().Num(); ++Slot)
				{
					Base->SetMaterial(Slot, nullptr);
				}
				Base->SetWorldTransform(FTransform(Where.GetRotation(),
					Where.GetLocation(), FVector::OneVector));
				Frame.Parts.Add(Base);
			}
		}

		TArray<TObjectPtr<UStaticMeshComponent>> Stages;
		for (int32 Stage = 0; Stage < SpacecraftLiftStages; ++Stage)
		{
			const FName StageKey(*FString::Printf(
				TEXT("%s_LF_LiftRam%d"),
				*Record.StationId.ToString(), Stage));
			UStaticMeshComponent* Ram =
				MakeBlockComponent(StageKey, RamTone);
			if (Ram == nullptr)
			{
				continue;
			}
			UStaticMesh* StageMesh = LoadLift(StageNames[Stage]);
			if (StageMesh != nullptr)
			{
				Ram->SetStaticMesh(StageMesh);
				// The mesh carries its own palette slots; the flat
				// block tint would paint over the brushed sliding
				// faces that make it read as a ram.
				for (int32 Slot = 0;
					Slot < StageMesh->GetStaticMaterials().Num(); ++Slot)
				{
					Ram->SetMaterial(Slot, nullptr);
				}
			}
			const float RestZ = StageRestZCm[Stage];
			Ram->SetWorldTransform(FTransform(Where.GetRotation(),
				Where.GetLocation() + FVector(0.f, 0.f, RestZ),
				FVector::OneVector));
			StationLiftRamRestZ.Add(Ram,
				Where.GetLocation().Z + RestZ);
			Frame.Parts.Add(Ram);
			Stages.Add(Ram);
		}
		StationLiftRams.Add(Record.StationId, Stages);

		const FName SaddleKey(*FString::Printf(TEXT("%s_LF_LiftSaddle"),
			*Record.StationId.ToString()));
		if (UStaticMeshComponent* Saddle =
			MakeBlockComponent(SaddleKey, SaddleTone))
		{
			if (UStaticMesh* SaddleMesh = LoadLift(TEXT("lift_saddle")))
			{
				Saddle->SetStaticMesh(SaddleMesh);
				for (int32 Slot = 0;
					Slot < SaddleMesh->GetStaticMaterials().Num(); ++Slot)
				{
					Saddle->SetMaterial(Slot, nullptr);
				}
			}
			else
			{
				UE_LOG(LogTemp, Warning,
					TEXT("SPACECRAFT PRESENTER: the lift cradle did not "
						"load - the saddle falls back to a plain block. "
						"If this is a packaged build, LiftCradle_v001 is "
						"missing from DirectoriesToAlwaysCook."));
			}
			Saddle->SetWorldTransform(FTransform(Where.GetRotation(),
				Where.GetLocation() + FVector(0.f, 0.f, 220.f),
				FVector::OneVector));
			Frame.Parts.Add(Saddle);
			StationLiftSaddles.Add(Record.StationId, Saddle);
		}
	}

	// THE SMALL HARDWARE (owner 2026-08-28: "can you get them polished").
	// A marked square, a lift and some dock pads is the STRUCTURE of a
	// work station; what makes one read as a place where work happens
	// is the clutter around its edge. Both reference games are full of
	// it - cabinets, stands, cable runs, bins - and it costs nothing but
	// a handful of blocks placed off the line's own geometry.
	{
		// Machinery is the colourful thing; the cable run and the bin
		// lips stay dark so the amber has something to read against.
		const FLinearColor CabinetTone = MachineAmber;
		const FLinearColor PanelFace(0.42f, 0.76f, 1.00f);
		const FLinearColor CableTone(0.14f, 0.14f, 0.15f);
		const FLinearColor BinTone = MachineAmber;
		// NO CONTROL CABINET (owner 2026-08-29, pointing at a close-up
		// of a station: "need to remove these 2 from the station").
		// It earned removal on the project's own rules as well as on
		// looks: the comment that placed it sited it "on the near
		// corner where a person would stand at it", and nothing on
		// this floor is handled by a person - the same reasoning that
		// took handles, ladders and cabs off every other machine.
		// Cable runs from the cabinet along the bay edge - the thing
		// that ties a machine to its floor instead of leaving it
		// sitting on one.
		for (int32 Run = 0; Run < 2; ++Run)
		{
			// Along the near flank's edge, one each side of centre.
			AddBlock(TEXT("CableRun"), Run, CableTone,
				FVector(-FootX * 0.25f + FootX * 0.5f * Run,
					FootY * 0.5f - 30.f, 22.f),
				FVector(FootX * 0.42f, 70.f, 26.f));
		}
		// THE KIT DOLLY, in place of three bins that were the same
		// three bins whatever the station held. One bay per component
		// this station fits, one crate per input of that component's
		// sub-assembly recipe - so the dolly is sized by DATA and a
		// recipe change moves it instead of quietly disagreeing.
		//
		// A bay's crates are all present or all absent together,
		// because stock is tracked per COMPONENT and that is what is
		// genuinely known. It is not a claim about the individual
		// Sets. When the line is later pushed down to withdrawing
		// Sets, the picture does not change - only the fill test does.
		const FLinearColor DeckTone(0.30f, 0.30f, 0.32f);
		const FLinearColor WheelTone(0.10f, 0.10f, 0.11f);
		const FLinearColor CrateTone = LBSpacecraftPalette::CrateTan; // part crates, were nearly the same tone as the machines
		const FLinearColor CrateLid = LBSpacecraftPalette::CrateTanDark; // crate lids
		const FLinearColor EmptyCradle(0.12f, 0.12f, 0.13f);

		const TArray<FName>& Kit = Record.AllocatedComponents;
		bool bSkidPlaced = false;

		// ---- THE REAL SKID, WHEN IT IS THERE ----
		//
		// The blockout below is a deck on FOUR WHEELS WITH A DRAWBAR,
		// which is the wheeled-cart idiom the owner corrected on
		// 2026-08-28 - "its a drone dolly thing". Nothing on this floor
		// is handled by a person, so a tow bar is wrong twice over.
		//
		// The commissioned model is a proper drone skid: grapple
		// hardpoints, a lift eye and guide notches instead. One placed
		// per allocated component rather than one stretched to fit,
		// because non-uniform scaling on a detailed mesh distorts every
		// fastener on it - and one dolly per station per craft is the
		// settled model anyway.
		UStaticMesh* SkidMesh = LoadObject<UStaticMesh>(nullptr,
			TEXT("/Game/LineBoss/Candidates/Spacecraft/KitDolly_v003")
			TEXT("/LB_KitDolly_v003_joined/StaticMeshes")
			TEXT("/SM_LB_KitDolly_v003.SM_LB_KitDolly_v003"));
		if (SkidMesh == nullptr)
		{
			// Same trap as the crane above: a missing cook entry leaves
			// this null and the wheeled blockout draws instead, which
			// looks like a design that was never changed rather than an
			// asset that never shipped.
			UE_LOG(LogTemp, Warning,
				TEXT("SPACECRAFT PRESENTER: the kit skid did not load - "
					"falling back to the wheeled blockout. If this is a "
					"packaged build, KitDolly_v003 is missing from "
					"DirectoriesToAlwaysCook."));
		}
		if (SkidMesh != nullptr && Kit.Num() > 0)
		{
			// Along the FAR flank (inside the pad edge), bays spread
			// along the line, downstream of the tower's corner.
			const float SkidFlankY = -(FootY * 0.5f - 210.f);
			const float BaySpacing = 340.f;
			for (int32 Bay = 0; Bay < Kit.Num(); ++Bay)
			{
				const FName SkidKey(*FString::Printf(TEXT("%s_Skid%d"),
					*Record.StationId.ToString(), Bay));
				UStaticMeshComponent* Skid =
					NewObject<UStaticMeshComponent>(this,
						UStaticMeshComponent::StaticClass(), SkidKey);
				Skid->SetStaticMesh(SkidMesh);
				Skid->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Skid->SetupAttachment(RootComponent);
				Skid->RegisterComponent();
				FTransform T = Where;
				const float AlongX = 260.f
					+ (Bay - (Kit.Num() - 1) * 0.5f) * BaySpacing;
				T.AddToTranslation(Where.GetRotation().RotateVector(
					FVector(AlongX, SkidFlankY, 0.f)));
				// No yaw now: the model runs long on ITS x and the bay
				// runs along the station's x (the line) on the far flank.
				T.SetRotation(T.GetRotation());
				T.SetScale3D(FVector(1.f));
				Skid->SetWorldTransform(T);
				Frame.Parts.Add(Skid);
				// PALLETLOADS_v001 (2026-08-30): the skid mesh's OWN
				// baked crates are generic (the same lumps regardless
				// of what the bay actually holds) - this is what "the
				// signal is lost until the crates are split out of the
				// model or driven by per-instance data" (below) was
				// waiting on. A real per-component pallet rides on top
				// when this bay's component has one; the skid still
				// supplies the platform/hardpoints either way.
				if (HasKitComponent(Record.StationId, Kit[Bay]))
				{
					AddKitPallets(Kit[Bay], Bay,
						FVector(AlongX, SkidFlankY, 55.f));
				}
			}
			// The mesh carries its own crates, so the data-driven crate
			// blocks below are skipped rather than stacked on top of
			// them. THE COST IS REAL AND WORTH NAMING: the blockout
			// sized itself from the recipe, so a station fitting more
			// parts grew a longer dolly. That signal is lost until the
			// crates are either split out of the model or driven by
			// per-instance data - it is not a thing to forget.
			//
			// A FLAG RATHER THAN AN EARLY RETURN. Returning here would
			// have skipped the booth mullions and everything else this
			// function still has to draw - geometry silently missing
			// from every station, for a reason no screenshot would
			// explain.
			bSkidPlaced = true;
		}

		// A station with nothing allocated gets no dolly rather than an
		// empty one: there is no kit, so there is nothing to stand
		// there. An empty dolly would read as a shortage.
		if (!bSkidPlaced && Kit.Num() > 0)
		{
			// Along the far flank, downstream of the tower's corner.
			const float DollyY = -(FootY * 0.5f - 210.f);
			const float DollyX0 = 260.f;
			// Sized to its contents, so a one-component station gets a
			// short dolly and a two-component station a long one.
			const float BayLenY = 340.f;
			const float DeckLenY = BayLenY * static_cast<float>(Kit.Num());
			AddBlock(TEXT("DollyDeck"), 0, DeckTone,
				FVector(DollyX0, DollyY, 46.f),
				FVector(DeckLenY, 270.f, 18.f));
			// Four wheels and a drawbar, so it reads as a thing that
			// was WHEELED here rather than a box that lives there.
			for (int32 Wheel = 0; Wheel < 4; ++Wheel)
			{
				AddBlock(TEXT("DollyWheel"), Wheel, WheelTone,
					FVector(DollyX0 + ((Wheel / 2 == 0) ? -1.f : 1.f)
							* (DeckLenY * 0.5f - 60.f),
						DollyY + ((Wheel % 2 == 0) ? -110.f : 110.f), 20.f),
					FVector(52.f, 52.f, 40.f));
			}
			AddBlock(TEXT("DollyBar"), 0, WheelTone,
				FVector(DollyX0 + DeckLenY * 0.5f + 70.f, DollyY, 40.f),
				FVector(150.f, 40.f, 16.f));

			for (int32 Bay = 0; Bay < Kit.Num(); ++Bay)
			{
				const float BayX = DollyX0 - DeckLenY * 0.5f + BayLenY * 0.5f
					+ BayLenY * static_cast<float>(Bay);
				const bool bHeld =
					HasKitComponent(Record.StationId, Kit[Bay]);
				// PALLETLOADS_v001 (2026-08-30): a real ship-cut pallet
				// when this component has one, replacing the whole
				// generic crate-cradle grid below for this bay rather
				// than nesting inside it - the grid's slots (~1 m,
				// four per bay) were sized for a generic placeholder
				// crate and are too small for a wing panel or a hull
				// section (up to 3.19 m). One pallet reads as the
				// component; the crate grid's job (loaded vs empty)
				// is carried instead by whether the pallet is drawn.
				TArray<FName> PalletCandidates;
				GetKitPalletCandidates(Kit[Bay], PalletCandidates);
				if (PalletCandidates.Num() > 0)
				{
					// else (bHeld false): no pallet drawn is the
					// shortage, same language the empty cradle spoke.
					if (bHeld)
					{
						AddKitPallets(Kit[Bay], Bay,
							FVector(BayX, DollyY, 55.f));
					}
					continue;
				}
				const int32 Crates = KitCrateCount(Kit[Bay]);
				for (int32 Crate = 0; Crate < Crates; ++Crate)
				{
					// Two rows down the dolly, so eight crates read as
					// a loaded pallet rather than a queue.
					//
					// SPACING MUST EXCEED THE CRATE. The first cut put
					// 116 cm crates on 95 cm row spacing, so every pair
					// of rows overlapped and four crates rendered as
					// two slabs - the dolly looked loaded but could not
					// be counted.
					const float SlotX = BayX
						+ ((Crate / 2 == 0) ? -76.f : 76.f);
					const float SlotY = DollyY
						+ ((Crate % 2 == 0) ? -64.f : 64.f);
					const int32 Key = Bay * 8 + Crate;
					// THE CRADLE IS ALWAYS DRAWN, loaded or not. The
					// first cut drew a flat dark plate for an empty
					// slot and it read as a dark TILE, not as a gap -
					// because a hole only reads as a hole when there
					// is a frame it should be filling. Four rails
					// outline every slot, and the crate's presence
					// inside them is then the only difference.
					for (int32 Rail = 0; Rail < 4; ++Rail)
					{
						const bool bAlongY = Rail >= 2;
						const float Sign = (Rail % 2 == 0) ? -1.f : 1.f;
						AddBlock(TEXT("KitCradle"), Key * 4 + Rail,
							EmptyCradle,
							FVector(SlotX + (bAlongY ? 0.f : Sign * 54.f),
								SlotY + (bAlongY ? Sign * 54.f : 0.f),
								64.f),
							bAlongY ? FVector(118.f, 12.f, 22.f)
								: FVector(12.f, 118.f, 22.f));
					}
					if (bHeld)
					{
						// From the play camera a crate is its LID, so the
						// lid takes Crate.Tan and the body the dark; the
						// other way round the kit read as four black
						// blocks on the pad (frame, 2026-09-02).
						AddBlock(TEXT("KitCrate"), Key, CrateLid,
							FVector(SlotX, SlotY, 104.f),
							FVector(98.f, 98.f, 76.f));
						AddBlock(TEXT("KitCrateLid"), Key, CrateTone,
							FVector(SlotX, SlotY, 145.f),
							FVector(106.f, 106.f, 10.f));
					}
					// else: the empty cradle IS the shortage. No
					// number and no bar - the gap is the message, and
					// it is visible before the craft even arrives.
				}
			}
		}
	}

	// THE SPRAY BOOTH IS A WORK STATION WITH GLASS SIDES (owner
	// 2026-08-28: "and the spray booth to be same but with glass
	// sides"). It was a solid box of its own, which enclosed the
	// overspray and also hid the one thing worth watching - the craft
	// taking the customer's livery. Glass keeps the enclosure and gives
	// the paint back to the player.
	//
	// Everything above this point is the SAME work station every line
	// station gets: the marked square, the hazard bands, the dock pads
	// and the central lift. The booth only adds what makes it a booth.
	if (Definition.bProcessStation)
	{
		// THE REAL BOOTH IF IT LOADED, the block enclosure if it did not.
		// The ninety lines below were twenty-six metres of engine cubes
		// standing in for a model that did not exist. It does now, so they
		// become the FALLBACK rather than the plan - and the fallback says
		// so out loud, because a silent one shipped a build a revision
		// behind this morning.
		bool bBoothShellPlaced = false;
		if (UStaticMesh* BoothMesh =
			TryGetStationMesh(FName(TEXT("SprayBooth"))))
		{
			const FName BoothKey(*FString::Printf(
				TEXT("%s_LF_BoothShell"), *Record.StationId.ToString()));
			if (UStaticMeshComponent* Shell =
				MakeBlockComponent(BoothKey, FLinearColor::White))
			{
				Shell->SetStaticMesh(BoothMesh);
				// The mesh carries its own six palette slots, so the flat
				// block tint MakeBlockComponent applies must be cleared or
				// it would paint the glazing opaque.
				for (int32 Slot = 0;
					Slot < BoothMesh->GetStaticMaterials().Num(); ++Slot)
				{
					Shell->SetMaterial(Slot, nullptr);
				}
				// NANITE CANNOT DO TRANSLUCENCY, and the whole point of this
				// building is seeing the craft take its livery through the
				// glass. Left on, the engine warns and the glazing stops
				// being glass. Five thousand triangles gives up nothing by
				// opting out.
				Shell->bDisallowNanite = true;
				// A QUARTER TURN (owner 2026-08-29: "the booth wants turning
				// 90 degrees"). The line runs down +Y - stations step along
				// it - while the booth's 26 m through-axis is modelled on X,
				// so unrotated the craft would have to enter through a side
				// wall.
				FTransform ShellAt = Where;
				ShellAt.SetRotation(Where.GetRotation()
					* FRotator(0.f, 90.f, 0.f).Quaternion());
				Shell->SetWorldTransform(ShellAt);
				bBoothShellPlaced = true;
			}
		}
		if (!bBoothShellPlaced)
		{
			UE_LOG(LogTemp, Warning,
				TEXT("SPACECRAFT PRESENTER: the paint booth model did not "
					"load - falling back to the block enclosure. If this is "
					"a packaged build, PaintBooth_v001 is missing from "
					"DirectoriesToAlwaysCook."));
		}
		// Only when there is no model. Guarded rather than deleted: the
		// blockout is still the honest thing to draw if the asset is
		// absent, and drawing nothing would look like a bug in the line.
		if (!bBoothShellPlaced)
		{
			const FLinearColor FrameTone(0.24f, 0.23f, 0.22f);
			const float WallHeight = 780.f;
			UMaterialInterface* GlassMaterial =
				LoadObject<UMaterialInterface>(nullptr,
					TEXT("/Game/LineBoss/Materials/Surfaces/")
					TEXT("MI_LB_Surface_Glass.MI_LB_Surface_Glass"));
			for (int32 Side = 0; Side < 2; ++Side)
			{
				const float SideSign = Side == 0 ? -1.f : 1.f;
				// GLASS along the craft's path; the ends stay open so it
				// drives in one and out the other.
				const FName GlassKey(*FString::Printf(
					TEXT("%s_LF_BoothGlass%d"),
					*Record.StationId.ToString(), Side));
				if (UStaticMeshComponent* Pane =
					MakeBlockComponent(GlassKey,
						FLinearColor(0.62f, 0.74f, 0.80f)))
				{
					FTransform PaneAt = Where;
					PaneAt.AddToTranslation(Where.GetRotation().RotateVector(
						FVector(SideSign * (FootX * 0.5f - 14.f), 0.f,
							WallHeight * 0.5f)));
					PaneAt.SetScale3D(
						FVector(0.16f, FootY / 100.f, WallHeight / 100.f));
					Pane->SetWorldTransform(PaneAt);
					// Real glass when the translucent material exists; a
					// pale tinted pane when it does not. Draws less, never
					// more - and never a solid wall where glass was asked
					// for, which would hide the paint again.
					if (GlassMaterial != nullptr)
					{
						Pane->SetMaterial(0, GlassMaterial);
					}
					Pane->SetCastShadow(false);
					Frame.Parts.Add(Pane);
				}
				// A dark mullion at the top of each pane, so the glass
				// reads as glazing in a frame rather than a floating slab.
				AddBlock(TEXT("BoothMullion"), Side, FrameTone,
					FVector(SideSign * (FootX * 0.5f - 14.f), 0.f,
						WallHeight - 20.f),
					FVector(34.f, FootY, 60.f));
			}
			// THE ROOF IS GLASS TOO (owner 2026-08-28: "we cant see
			// anything with roor on booth"). Glass sides were pointless
			// with a solid lid on top - the camera looks DOWN at pitch -35,
			// so the roof is most of what it sees and the craft was hidden
			// again. A booth still needs a ceiling to hold the overspray,
			// so the answer is glazing rather than removing it.
			{
				const FName RoofKey(*FString::Printf(
					TEXT("%s_LF_BoothRoof"),
					*Record.StationId.ToString()));
				if (UStaticMeshComponent* Roof =
					MakeBlockComponent(RoofKey,
						FLinearColor(0.62f, 0.74f, 0.80f)))
				{
					FTransform RoofAt = Where;
					RoofAt.AddToTranslation(Where.GetRotation().RotateVector(
						FVector(0.f, 0.f, WallHeight + 20.f)));
					RoofAt.SetScale3D(FVector(FootX / 100.f,
						(FootY - 160.f) / 100.f, 0.22f));
					Roof->SetWorldTransform(RoofAt);
					if (GlassMaterial != nullptr)
					{
						Roof->SetMaterial(0, GlassMaterial);
					}
					Roof->SetCastShadow(false);
					Frame.Parts.Add(Roof);
				}
				// Two structural beams across it, so the glazing reads as a
				// roof rather than a sheet floating over the bay.
				for (int32 Beam = 0; Beam < 2; ++Beam)
				{
					AddBlock(TEXT("BoothBeam"), Beam, FrameTone,
						FVector(0.f,
							(Beam == 0 ? -1.f : 1.f) * FootY * 0.22f,
							WallHeight + 44.f),
						FVector(FootX, 70.f, 46.f));
				}
			}
			for (int32 Stack = 0; Stack < 2; ++Stack)
			{
				AddBlock(TEXT("BoothStack"), Stack, FrameTone,
					FVector((Stack == 0 ? -1.f : 1.f) * FootX * 0.22f, 0.f,
						WallHeight + 190.f),
					FVector(220.f, 220.f, 300.f));
			}
		}
	}

	// The work light: one cool-white rect light high over the square
	// (owner 2026-08-26 night: "full detail, lights, shadows").
	{
		const FName LampKey(*FString::Printf(TEXT("%s_LF_Lamp"),
			*Record.StationId.ToString()));
		URectLightComponent* Lamp = NewObject<URectLightComponent>(
			this, URectLightComponent::StaticClass(), LampKey);
		Lamp->SetupAttachment(RootComponent);
		Lamp->RegisterComponent();
		Lamp->SetWorldLocation(Where.GetLocation()
			+ Where.GetRotation().RotateVector(
				FVector(0.f, 0.f, 850.f)));
		Lamp->SetWorldRotation(FRotator(-90.f, 0.f, 0.f));
		// BRIGHT AND WARM (owner 2026-08-28, holding up Car
		// Manufacture: "want to look nice and bright like this").
		//
		// 18k lm once blew machines out to white/orange under Lumen, and
		// the fix then was to dim the lamp to 3.5k. That treated the
		// symptom: the blowout was METALLIC surfaces with no reflection
		// environment to reflect, not too much light. With the palette
		// taken to a matte painted finish the light can come up to
		// where the reference actually sits, and the cool blue-white
		// goes with it - that tint is most of why the floor read cold.
		// 9k was an overcorrection and the owner saw it before I did:
		// "the building looks like its coverd in snow". 3.5k was too
		// dim for a matte palette, 9k blew a 0.88-albedo panel to
		// white. 5k with the albedo brought down to 0.72 is the pair
		// that works - the two numbers only make sense together.
		Lamp->SetIntensity(5000.f);
		Lamp->SetLightColor(FColor(255, 247, 235));
		Lamp->SetSourceWidth(FootX * 0.75f);
		Lamp->SetSourceHeight(FootY * 0.75f);
		Lamp->SetAttenuationRadius(2600.f);
		Lamp->SetCastShadows(true);
		Frame.Lights.Add(Lamp);
	}
}

void ALBSpacecraftWIPPresentationActor::DestroySprayRig(
	FLBSpacecraftSprayRig& Rig)
{
	for (UStaticMeshComponent* Part : Rig.Bodies)
	{
		if (Part != nullptr) { Part->DestroyComponent(); }
	}
	for (UStaticMeshComponent* Part : Rig.Mists)
	{
		if (Part != nullptr) { Part->DestroyComponent(); }
	}
}

void ALBSpacecraftWIPPresentationActor::RefreshUnits()
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	// Cleared BEFORE the guard, not after: an unconfigured line has no
	// craft, and a stale carry would leave the gantry parked over a
	// ship that is no longer there.
	bCraftIsCarried = false;
	CarriedCraftsCm.Reset();
	if (Coordinator == nullptr || ProductionAuthority == nullptr
		|| !Coordinator->IsConfigured())
	{
		return;
	}
	const TArray<FLBSpacecraftRouteStep>& Route = Coordinator->GetRoute();

	TSet<FName> Live;
	for (const FLBSpacecraftRuntimeAssignment& Assignment :
		Coordinator->GetAssignments())
	{
		const FLBSpacecraftUnitState* Unit =
			ProductionAuthority->FindUnit(Assignment.UnitId);
		if (Unit == nullptr || !Route.IsValidIndex(Assignment.RouteIndex))
		{
			continue;
		}
		Live.Add(Assignment.UnitId);

		// SCOUT: gated on the real, per-component ground truth (owner,
		// 2026-08-30 - see ScoutV2AttachedComponents' header comment for
		// why Stage was wrong here) rather than the stage-threshold
		// ladder every other recipe still uses. Cargo is untouched:
		// no evidence yet that its single-mesh ladder has the same
		// fault, and this fix is scoped to the bug actually reported.
		const bool bScoutSixPart = Unit->RecipeId
			== LBSpacecraftWIPPresentationPrivate::SpacecraftScoutRecipeId
			&& Unit->ProducedComponents.Contains(ELBSpacecraftComponent::Hull);
		const bool bCraftForm = bScoutSixPart
			|| Unit->Stage >= ELBSpacecraftStage::Assembly;
		UStaticMesh* Craft = nullptr;
		if (bCraftForm)
		{
			// THE SIX-ASSEMBLY SCOUT tries first for its own recipe.
			// Hull becomes the primary component's mesh; the other
			// five attach as children once Component exists below.
			// Falls to the single-mesh ladder if incomplete - never a
			// hull with missing engines.
			UStaticMesh* V2Propulsion = nullptr;
			UStaticMesh* V2Power = nullptr;
			UStaticMesh* V2Electronics = nullptr;
			UStaticMesh* V2Navigation = nullptr;
			UStaticMesh* V2Interior = nullptr;
			if (Unit->RecipeId == LBSpacecraftWIPPresentationPrivate
					::SpacecraftScoutRecipeId
				&& ResolveScoutV2Parts(Craft, V2Propulsion, V2Power,
					V2Electronics, V2Navigation, V2Interior))
			{
				// Craft now holds Hull; the branches below are skipped
				// because Craft is no longer nullptr.
			}
			// Each recipe's finished craft is its TEXTURED derivative
			// (the segmentation forms carry no UVs); the ladder falls
			// to the fitted form, then the Scout craft, never to less.
			if (Craft == nullptr
				&& Unit->RecipeId
					== LBSpacecraftWIPPresentationPrivate
						::SpacecraftCargoRecipeId)
			{
				Craft = ResolveCargoCraftMesh();
				if (Craft == nullptr)
				{
					Craft = ResolveCargoFittedMesh();
				}
			}
			if (Craft == nullptr)
			{
				Craft = ResolveCraftMesh();
			}
		}
		UStaticMesh* BuildForm = !bCraftForm
			? ResolveBuildFormMesh(Unit->Stage, Unit->RecipeId) : nullptr;

		TObjectPtr<UStaticMeshComponent>* Existing =
			UnitVisuals.Find(Assignment.UnitId);
		UStaticMeshComponent* Component =
			Existing != nullptr ? Existing->Get() : nullptr;
		if (Component == nullptr)
		{
			Component = MakeBlockComponent(Assignment.UnitId,
				FLinearColor(0.78f, 0.76f, 0.70f)); // pale component crate
			if (Component == nullptr)
			{
				continue;
			}
			UnitVisuals.Add(Assignment.UnitId, Component);
			if (Assignment.RouteIndex == 0 && !bCraftForm
				&& !ShellDeliveredUnits.Contains(Assignment.UnitId))
			{
				BeginShellDelivery(Assignment.UnitId,
					Route.IsValidIndex(0) && BuildAuthority != nullptr
						? [this, &Route]()
						{
							const FLBSpacecraftStationRecord* First =
								BuildAuthority->FindStation(
									Route[0].StationId);
							return First != nullptr
								? First->WorldTransform.GetLocation()
								: FVector::ZeroVector;
						}()
						: FVector::ZeroVector,
					BuildForm);
			}
		}
		if (ShellDeliveries.Contains(Assignment.UnitId))
		{
			Component->SetVisibility(false);
		}
		// STRIPPED HULL, BUILT LIVE (owner, 2026-08-30: "the hull ship
		// needs to be striped down and built live"). Before Hull is
		// fitted, a Scout unit shows its own real hull SECTIONS - loose,
		// not yet joined - instead of a featureless crate, reusing the
		// PalletLoads_v001 sections already imported for the kit dolly
		// (ShouldAssembleKitPalletsTogether's ordering, so this reads as
		// the same nose-to-aft sequence a station's dolly shows). The
		// primary Component stays the transform anchor - crane-carry,
		// slide, everything already keys off it - but is hidden (not
		// destroyed: SetVisibility does not propagate to children by
		// default, so the sections attached to it keep rendering) while
		// the sections stand in for it. They are destroyed and Component
		// made visible again the instant bScoutSixPart turns true, at
		// which point the Form ladder below takes over with the real
		// assembled Hull.
		if (Unit->RecipeId == SpacecraftScoutRecipeId)
		{
			if (!bScoutSixPart)
			{
				if (!StrippedHullSections.Contains(Assignment.UnitId))
				{
					TArray<FName> HullSectionKeys;
					GetKitPalletCandidates(FName(TEXT("Component.Hull")),
						HullSectionKeys);
					TArray<UStaticMesh*> SectionMeshes;
					TArray<float> SectionLengthsCm;
					for (const FName& Key : HullSectionKeys)
					{
						UStaticMesh* Mesh = TryGetStationMesh(Key);
						SectionMeshes.Add(Mesh);
						SectionLengthsCm.Add(Mesh != nullptr
							? Mesh->GetBounds().BoxExtent.Y * 2.f : 0.f);
					}
					TArray<float> SectionCentresCm;
					ComputeSequentialLayoutCentresCm(SectionLengthsCm,
						SectionCentresCm);
					TArray<TObjectPtr<UStaticMeshComponent>> Sections;
					for (int32 Index = 0; Index < SectionMeshes.Num();
						++Index)
					{
						if (SectionMeshes[Index] == nullptr)
						{
							continue;
						}
						const FName SectionKey(*FString::Printf(
							TEXT("%s_HullSection%d"),
							*Assignment.UnitId.ToString(), Index));
						UStaticMeshComponent* Section =
							NewObject<UStaticMeshComponent>(this,
								UStaticMeshComponent::StaticClass(),
								SectionKey);
						Section->SetStaticMesh(SectionMeshes[Index]);
						Section->SetCollisionEnabled(
							ECollisionEnabled::NoCollision);
						Section->SetCastShadow(true);
						Section->AttachToComponent(Component,
							FAttachmentTransformRules::
								KeepRelativeTransform);
						// Along the craft's OWN axis (local X, nose at -X),
						// where the assembled hull will stand - not across
						// it, which put the loose hull across the line
						// (frame, 2026-09-02). The section meshes are
						// modelled lying along Y, hence the quarter turn.
						Section->SetRelativeLocationAndRotation(
							FVector(SectionCentresCm[Index], 0.f, 0.f),
							FRotator(0.f, 90.f, 0.f));
						Section->RegisterComponent();
						Sections.Add(Section);
					}
					StrippedHullSections.Add(Assignment.UnitId,
						MoveTemp(Sections));
				}
				Component->SetVisibility(false);
				// THE HULL COMES TOGETHER (look plan, 2026-09-02): the
				// loose sections start the stop spread apart along the
				// craft's axis and close up nose-to-aft as the stop
				// progresses, so the first station shows a hull being
				// built rather than parts lying still; the real hull
				// takes over the instant it is fitted.
				if (TArray<TObjectPtr<UStaticMeshComponent>>* Loose =
					StrippedHullSections.Find(Assignment.UnitId))
				{
					float StopProgress = 0.f;
					if (Coordinator != nullptr)
					{
						Coordinator->GetUnitCycleProgress(Assignment.UnitId,
							StopProgress);
					}
					TArray<float> LengthsCm;
					for (UStaticMeshComponent* Section : *Loose)
					{
						LengthsCm.Add(Section != nullptr
							&& Section->GetStaticMesh() != nullptr
							? Section->GetStaticMesh()->GetBounds().BoxExtent.Y
								* 2.f
							: 0.f);
					}
					TArray<float> CentresCm;
					ComputeSequentialLayoutCentresCm(LengthsCm, CentresCm);
					const int32 Count = Loose->Num();
					const float Closed = FMath::SmoothStep(0.f, 1.f,
						FMath::Clamp(StopProgress, 0.f, 1.f));
					for (int32 Index = 0; Index < Count; ++Index)
					{
						UStaticMeshComponent* Section = (*Loose)[Index];
						if (Section == nullptr || !CentresCm.IsValidIndex(Index))
						{
							continue;
						}
						const float Spread = (Index - (Count - 1) * 0.5f)
							* 260.f * (1.f - Closed);
						Section->SetRelativeLocation(
							FVector(CentresCm[Index] + Spread, 0.f, 0.f));
					}
				}
			}
			else if (TArray<TObjectPtr<UStaticMeshComponent>>* Sections =
				StrippedHullSections.Find(Assignment.UnitId))
			{
				for (UStaticMeshComponent* Section : *Sections)
				{
					if (Section != nullptr) { Section->DestroyComponent(); }
				}
				StrippedHullSections.Remove(Assignment.UnitId);
				Component->SetVisibility(true);
			}
		}
		if (!bCraftForm && BuildForm != nullptr)
		{
			RefreshUnitFittings(Assignment.UnitId, Component,
				Assignment.RouteIndex, Route.Num(),
				Unit->RecipeId == SpacecraftCargoRecipeId);
		}
		else
		{
			// The hull closes at assembly - the innards disappear
			// inside the finished craft.
			ClearUnitFittings(Assignment.UnitId);
		}

		// Form ladder: crate -> chassis -> airframe -> fitted -> craft.
		if (bCraftForm && Craft != nullptr
			&& Component->GetStaticMesh() != Craft)
		{
			Component->SetStaticMesh(Craft);
			Component->EmptyOverrideMaterials(); // craft keeps its own look
		}
		// THE FIVE ATTACHED ASSEMBLIES. Component now holds Hull; the
		// rest are separate meshes that never existed as a single
		// object, so they must be spawned and attached rather than
		// swapped in with SetStaticMesh. Created once per unit and left
		// alone after - identity relative transform, because all six
		// parts were authored already positioned in the same local
		// space (loading only Hull gives a bare airframe; loading all
		// six gives the finished craft, per the modelling brief).
		if (bCraftForm
			&& Unit->RecipeId == SpacecraftScoutRecipeId)
		{
			UStaticMesh* V2Hull = nullptr;
			UStaticMesh* V2Propulsion = nullptr;
			UStaticMesh* V2Power = nullptr;
			UStaticMesh* V2Electronics = nullptr;
			UStaticMesh* V2Navigation = nullptr;
			UStaticMesh* V2Interior = nullptr;
			if (ResolveScoutV2Parts(V2Hull, V2Propulsion, V2Power,
				V2Electronics, V2Navigation, V2Interior))
			{
				// INCREMENTAL, not created-once-and-left (owner,
				// 2026-08-30): each part now attaches the moment
				// Unit->ProducedComponents actually contains it, tracked
				// per-component in ScoutV2AttachedComponents so a part
				// already attached is never re-created - the craft
				// visibly gains its propulsion, power, etc. as the line
				// actually fits them, not all five at once whenever
				// bCraftForm first turns true.
				TSet<ELBSpacecraftComponent>& Attached =
					ScoutV2AttachedComponents.FindOrAdd(Assignment.UnitId);
				TArray<TObjectPtr<UStaticMeshComponent>>& Parts =
					ScoutV2Parts.FindOrAdd(Assignment.UnitId);
				// Unique key per UNIT, not just per part-name: with
				// attachment now gated on real per-component fitting
				// rather than the rare late Stage>=Assembly threshold,
				// several units can hold a Propulsion part concurrently,
				// and NewObject requires unique names under one Outer.
				// NODE SYSTEM (owner, 2026-08-30: "make the ship into a
				// node system where the parts snap on"): each part now
				// asks FindShipNodeTransform for its named point rather
				// than assuming Identity outright. Today that lookup
				// still resolves to Identity for every Scout part - the
				// six-assembly model IS pre-aligned - so this is a
				// mechanism change with no visible effect yet, not a
				// repositioning; a future part with different geometry
				// overrides GetShipNodes and every attach call site here
				// picks the new offset up for free.
				auto Attach = [this, Component, &Assignment, Unit](
					UStaticMesh* Mesh, FName NodeId,
					bool bDisallowNanite) -> UStaticMeshComponent*
				{
					const FName PartKey(*FString::Printf(TEXT("%s_%s"),
						*Assignment.UnitId.ToString(), *NodeId.ToString()));
					UStaticMeshComponent* Part =
						NewObject<UStaticMeshComponent>(this,
							UStaticMeshComponent::StaticClass(), PartKey);
					Part->SetStaticMesh(Mesh);
					Part->SetCollisionEnabled(
						ECollisionEnabled::NoCollision);
					Part->SetCastShadow(true);
					// Navigation carries the canopy_glass slot - Nanite
					// cannot render translucency, the exact fault the
					// spray booth's glazing already taught this file.
					// The asset is fixed at import time too; this is
					// belt-and-braces at the instance.
					Part->bDisallowNanite = bDisallowNanite;
					Part->AttachToComponent(Component,
						FAttachmentTransformRules::KeepRelativeTransform);
					FTransform NodeTransform;
					FindShipNodeTransform(Unit->RecipeId, NodeId,
						NodeTransform);
					Part->SetRelativeTransform(NodeTransform);
					Part->RegisterComponent();
					return Part;
				};
				auto AttachIfFitted = [&](ELBSpacecraftComponent Comp,
					UStaticMesh* Mesh, FName NodeId, bool bDisallowNanite)
				{
					if (Attached.Contains(Comp)
						|| !Unit->ProducedComponents.Contains(Comp))
					{
						return;
					}
					Parts.Add(Attach(Mesh, NodeId, bDisallowNanite));
					Attached.Add(Comp);
				};
				AttachIfFitted(ELBSpacecraftComponent::Propulsion,
					V2Propulsion, FName(TEXT("Node.Propulsion")), false);
				AttachIfFitted(ELBSpacecraftComponent::Power, V2Power,
					FName(TEXT("Node.Power")), false);
				AttachIfFitted(ELBSpacecraftComponent::Electronics,
					V2Electronics, FName(TEXT("Node.Electronics")), false);
				AttachIfFitted(ELBSpacecraftComponent::Navigation,
					V2Navigation, FName(TEXT("Node.Navigation")), true);
				AttachIfFitted(ELBSpacecraftComponent::Interior,
					V2Interior, FName(TEXT("Node.Interior")), false);
			}
		}
		else if (BuildForm != nullptr
			&& Component->GetStaticMesh() != BuildForm)
		{
			Component->SetStaticMesh(BuildForm);
			Component->EmptyOverrideMaterials();
			// Build-form FBX ships bare; it wears its craft's hull
			// material so it reads as the same airframe it becomes
			// (per recipe - the cargo is not painted as a Scout).
			const TCHAR* HullPath =
				Unit->RecipeId == SpacecraftCargoRecipeId
					? SpacecraftCargoHullMaterialPath
					: SpacecraftHullMaterialPath;
			if (UMaterialInterface* Hull = LoadObject<UMaterialInterface>(
				nullptr, HullPath))
			{
				Component->SetMaterial(0, Hull);
			}
		}

		// Position: at the station, CARRIED BY THE GANTRY to the next
		// late in a cycle (owner 2026-08-28: "if the gantry crane moves
		// the ship we don't need conveyer?", then choosing crane plus
		// rail).
		//
		// The belt never moved anything. This slid the craft along the
		// floor between station transforms while a conveyor animated
		// beside it - a CAR idiom inherited from the car game. A pulse
		// line moves airframes by crane, so the craft now RIDES: up off
		// its cradle, across, and set down at the next station.
		FVector Location =
			Route[Assignment.RouteIndex].WorldTransform.GetLocation();
		// THE PULSE (2026-09-02): the craft rides only while the line
		// is MOVING and only inside its own crane trip's window of
		// the move phase - with one crane the craft go one after
		// another, with a crane per gap they all rise together. A
		// finished station's craft sits on its cradle until then;
		// after its trip it waits at the next station for the phase
		// to end, where the sim will put it. Progress01 is remapped so
		// the carry arc (ComputeCraneCarryCm) spans the whole trip.
		float Progress01 = 0.f;
		float CarryStart01 = 0.f;
		float CarryEnd01 = 0.f;
		const bool bInCarryWindow = Coordinator->GetUnitCarryWindow(
			Assignment.UnitId, CarryStart01, CarryEnd01)
			&& Route.IsValidIndex(Assignment.RouteIndex + 1);
		if (bInCarryWindow)
		{
			const float Phase01 = Coordinator->GetPulseProgress01();
			const float Trip01 = FMath::Clamp(
				(Phase01 - CarryStart01)
					/ FMath::Max(CarryEnd01 - CarryStart01, 0.001f),
				0.f, 1.f);
			Progress01 = SlideStartFraction
				+ Trip01 * (1.f - SlideStartFraction);
		}
		if (bInCarryWindow && Progress01 > SlideStartFraction)
		{
			const FVector Next =
				Route[Assignment.RouteIndex + 1].WorldTransform.GetLocation();
			const float Alpha = FMath::SmoothStep(0.f, 1.f,
				(Progress01 - SlideStartFraction)
					/ FMath::Max(1.f - SlideStartFraction, 0.01f));
			// THE CRAFT RIDES THE LINE, NOT THE CHORD (2026-09-01): a
			// straight lerp cut every corner the free-form track lays.
			// The belt spline carries one point per track piece and
			// both stations ARE pieces, so the carry samples the
			// spline by distance and follows the geometry the player
			// actually built - bends, U-turns and all. The travel-
			// facing yaw below then leads the nose through corners
			// with no extra work. The chord lerp stays as the honest
			// fallback for a stale or absent spline.
			bool bRodeTrack = false;
			if (TrackSpline != nullptr && TrackAuthority != nullptr
				&& TrackSpline->GetNumberOfSplinePoints()
					== TrackAuthority->GetPieces().Num())
			{
				const FName FromStation =
					Route[Assignment.RouteIndex].StationId;
				const FName ToStation =
					Route[Assignment.RouteIndex + 1].StationId;
				int32 FromPoint = INDEX_NONE;
				int32 ToPoint = INDEX_NONE;
				const TArray<FLBSpacecraftTrackPieceRecord>& Pieces =
					TrackAuthority->GetPieces();
				for (int32 Piece = 0; Piece < Pieces.Num(); ++Piece)
				{
					if (Pieces[Piece].NodeStationId == FromStation)
					{
						FromPoint = Piece;
					}
					else if (Pieces[Piece].NodeStationId == ToStation)
					{
						ToPoint = Piece;
					}
				}
				if (FromPoint != INDEX_NONE && ToPoint != INDEX_NONE)
				{
					const float FromDistance = TrackSpline
						->GetDistanceAlongSplineAtSplinePoint(FromPoint);
					const float ToDistance = TrackSpline
						->GetDistanceAlongSplineAtSplinePoint(ToPoint);
					const FVector OnSpline =
						TrackSpline->GetLocationAtDistanceAlongSpline(
							FMath::Lerp(FromDistance, ToDistance, Alpha),
							ESplineCoordinateSpace::World);
					Location = FVector(OnSpline.X, OnSpline.Y, 0.f);
					bRodeTrack = true;
				}
			}
			if (!bRodeTrack)
			{
				Location = FMath::Lerp(Location, Next, Alpha);
			}
			Location.Z += ComputeCraneCarryCm(Progress01,
				SlideStartFraction, CraneCarryRiseCm);
			// Published for the crane tick. ONE writer, so the gantry
			// can never drift off the ship it is holding.
			CarriedCraftAtCm = Location;
			bCraftIsCarried = true;
			CarriedCraftsCm.Add(Location);
		}

		// Face along the line (owner playtest fix): moving units point
		// where they are going; parked units keep their last heading.
		float UnitYaw = Component->GetComponentRotation().Yaw;
		{
			const FVector Travel =
				Location - Component->GetComponentLocation();
			if (Travel.SizeSquared2D() > 1.f)
			{
				UnitYaw = FMath::RadiansToDegrees(
					FMath::Atan2(Travel.Y, Travel.X))
					+ SpacecraftCraftNoseYawOffsetDeg;
			}
		}
		// THE UNDERCARRIAGE (owner 2026-08-28: tricycle landing gear, on
		// the ship, gone once it takes off).
		//
		// It appears when THE HULL COMPONENT IS FITTED, and that is the
		// point rather than a convenience: the Landing Set - one nose
		// leg and two mains - is part of the hull's bill of materials,
		// so the gear on screen is the gear the craft was actually
		// built with (owner: "the gear parts can be wired into the
		// parts system"). No hull, nothing to bolt a leg to.
		//
		// Deliberately NOT gated on the hull ART resolving: an
		// unresolved hull is drawn as a blockout, and a blockout still
		// lands. Attached to the craft, so it rides every slide down
		// the line and the whole departure without being driven.
		const bool bHullFitted = Unit->ProducedComponents.Contains(
			ELBSpacecraftComponent::Hull);
		if (bHullFitted && !UnitGear.Contains(Assignment.UnitId))
		{
			UnitGear.Add(Assignment.UnitId,
				MakeGearSet(Component, Assignment.UnitId));
		}
		FTransform UnitTransform(FRotator(0.f, UnitYaw, 0.f), Location);
		if ((bCraftForm && Craft != nullptr) || BuildForm != nullptr)
		{
			// The pre-Hull sections branch may have hidden this
			// component's own mesh; a real form always shows.
			Component->SetVisibility(true, false);

			// THE STATION LIFTS THE SHIP (owner 2026-08-28: "the
			// station will have to lift the ship up ... to be worked
			// on"). The craft arrives on its landing gear, the
			// four-post lift raises it so the crew can get underneath,
			// and it comes down again before it moves on. It used to
			// float at one fixed height for its whole stop, which gave
			// the ground crew nothing to have been let under and left
			// the lift columns as decoration.
			const float ParkedCm =
				SpacecraftStationBlockHeightCm + 100.f;
			float Lift = ParkedCm;
			// ONLY WHILE IT IS BEING WORKED ON. A craft at the hover
			// test is flying on its own RCS and is not on anybody's
			// lift - putting it on one dropped it to the floor at the
			// start of its test, which the hover test caught.
			if (Unit->Stage < ELBSpacecraftStage::Testing)
			{
				float StopProgress = 1.f;
				Coordinator->GetUnitCycleProgress(Assignment.UnitId,
					StopProgress);
				Lift = SpacecraftLandedBellyCm
					+ ComputeStationLiftCm(StopProgress,
						ParkedCm - SpacecraftLandedBellyCm,
						SpacecraftLiftRiseFraction);
				// THE RAM CARRIES THE CRAFT, so it is driven from the
				// same number rather than its own copy of the curve -
				// a lift whose column disagreed with the thing standing
				// on it is the one fault this cannot have.
				if (TArray<TObjectPtr<UStaticMeshComponent>>* Stages =
					StationLiftRams.Find(Assignment.StationId))
				{
					// TELESCOPING STAGES SLIDE, THEY DO NOT STRETCH.
					// This used to SetScale3D each stage to reach its
					// height, which is fine for a featureless engine
					// cylinder and wrong for a real one - stretching a
					// modelled stage smears its wiper collar and its
					// seal lip up the column. Each stage now keeps its
					// shape and moves.
					//
					// The stages are authored EXTENDED, at the pose
					// they hold when the lift is fully up, because a
					// mesh cannot reveal surfaces it was modelled
					// without. Retracting slides them back DOWN from
					// there.
					//
					// TRAVEL IS BOUNDED BY THE GEOMETRY, not by the
					// brief. The delivered stages are 0.48 / 0.88 /
					// 0.90 m tall, so they cannot nest inside each
					// other far enough to reach the 0.60 m retracted
					// height that was asked for: stage two can drop
					// 0.40 m before its foot meets stage one's, and
					// stage three 0.80 m. That is 1.20 m of real
					// travel, and driving further would push a stage
					// through the floor.
					constexpr float SpacecraftLiftStageDropCm[
						SpacecraftLiftStages] = { 0.f, 40.f, 80.f };
					constexpr float SpacecraftLiftMaxTravelCm = 120.f;
					const float Extension = FMath::Clamp(
						Lift / FMath::Max(SpacecraftLiftMaxTravelCm, 1.f),
						0.f, 1.f);
					for (int32 Stage = 0; Stage < Stages->Num(); ++Stage)
					{
						UStaticMeshComponent* Ram = (*Stages)[Stage];
						if (Ram == nullptr
							|| !StationLiftRamRestZ.Contains(Ram))
						{
							continue;
						}
						const float Drop = SpacecraftLiftStageDropCm[
							FMath::Min(Stage, SpacecraftLiftStages - 1)];
						FTransform RamAt =
							Ram->GetComponentTransform();
						RamAt.SetLocation(FVector(
							RamAt.GetLocation().X,
							RamAt.GetLocation().Y,
							StationLiftRamRestZ[Ram]
								- Drop * (1.f - Extension)));
						Ram->SetWorldTransform(RamAt);
					}
				}
				if (TObjectPtr<UStaticMeshComponent>* Saddle =
					StationLiftSaddles.Find(Assignment.StationId))
				{
					if (*Saddle != nullptr)
					{
						FTransform SaddleAt =
							(*Saddle)->GetComponentTransform();
						SaddleAt.SetLocation(FVector(
							SaddleAt.GetLocation().X,
							SaddleAt.GetLocation().Y,
							FMath::Max(Lift, 10.f) + 14.f));
						(*Saddle)->SetWorldTransform(SaddleAt);
					}
				}
			}
			if (Unit->Stage == ELBSpacecraftStage::Testing)
			{
				// The hover test, visibly: rise off the rig and bob on
				// blue belly RCS flames (owner, 2026-08-25).
				const float BobPhase = HoverBobPeriodSeconds > 0.f
					? VisualTimeSeconds * 2.f * PI / HoverBobPeriodSeconds
					: 0.f;
				Lift += TestHoverLiftCm
					+ HoverBobAmplitudeCm * FMath::Sin(BobPhase);
				// Attitude drift the RCS visibly corrects (owner
				// 2026-08-25: thrusters fire to stabilise like
				// rockets do).
				float WobblePitch = 0.f;
				float WobbleRoll = 0.f;
				ComputeHoverWobbleDeg(VisualTimeSeconds, WobblePitch,
					WobbleRoll);
				UnitTransform.SetRotation(FRotator(WobblePitch,
					UnitYaw, WobbleRoll).Quaternion());
				if (!UnitFlames.Contains(Assignment.UnitId))
				{
					UnitFlames.Add(Assignment.UnitId,
						MakeFlameSet(Component, Assignment.UnitId));
				}
				if (FLBSpacecraftFlameSet* Flames =
					UnitFlames.Find(Assignment.UnitId))
				{
					// Each corner thruster fires only as ITS corner
					// drops - stabilisation, not a constant burn.
					for (int32 Corner = 0;
						Corner < Flames->Belly.Num(); ++Corner)
					{
						TArray<TWeakObjectPtr<UStaticMeshComponent>> Single;
						Single.Add(Flames->Belly[Corner]);
						ApplyFlameIntensity(Single,
							ComputeRCSCorrection01(WobblePitch,
								WobbleRoll, Corner),
							VisualTimeSeconds + Corner * 0.37f);
					}
					ApplyFlameIntensity(Flames->Main, 0.f,
						VisualTimeSeconds);
				}
			}
			else if (FLBSpacecraftFlameSet* Flames =
				UnitFlames.Find(Assignment.UnitId))
			{
				DestroyFlameSet(*Flames);
				UnitFlames.Remove(Assignment.UnitId);
			}
			// LIVE PAINTING IN THE SPRAY BOOTH (owner 2026-08-25 for
			// the paint front; owner 2026-08-28 for the booth). The
			// front sweeps with the craft's real progress through the
			// booth and the two spray drones fly it with mist puffs.
			//
			// Keyed on WHERE THE CRAFT IS, not on its stage. It used to
			// fire throughout Assembly, which meant the customer's
			// livery went on in the open air beside the parts being
			// fitted - the one process a factory always encloses,
			// happening in the one place it should not.
			const FLBSpacecraftStationRecord* PaintStation =
				BuildAuthority != nullptr
					? BuildAuthority->FindStation(Assignment.StationId)
					: nullptr;
			const FLBSpacecraftStationDefinition* PaintDefinition =
				PaintStation != nullptr
					? ALBSpacecraftBuildAuthority::FindDefinition(
						PaintStation->DefinitionId)
					: nullptr;
			const bool bInTheBooth = PaintDefinition != nullptr
				&& PaintDefinition->bProcessStation;
			// A PRIMER COAT FROM THE FIRST STATION (owner 2026-09-02:
			// "there's not much colour in the game yet"). The ships are
			// where the colour lives, and a craft used to be graphite
			// for most of its life on the line. Now the hull wears its
			// customer's colour, muted, from the moment it is set down,
			// and the booth sweeps the full livery over it. The paint
			// instance is made here once, whether or not the craft is
			// in the booth; the material's PrimerColor had never been
			// set by anything.
			// Applied to whatever form the unit wears - the build forms
			// during assembly reset their material when they change,
			// so the instance is re-set whenever it has been lost.
			if (Component->GetStaticMesh() != nullptr
				&& !UnitPaintMIDs.Contains(Assignment.UnitId))
			{
				if (UMaterialInterface* PaintBase =
					LoadObject<UMaterialInterface>(nullptr,
						SpacecraftPaintMaterialPath))
				{
					UMaterialInstanceDynamic* PrimerMID =
						UMaterialInstanceDynamic::Create(PaintBase, Component);
					const FLinearColor Livery =
						FLBSpacecraftCustomerCatalogue::LiveryForRecipe(
							ProductionAuthority->GetContracts(), Unit->RecipeId);
					PrimerMID->SetVectorParameterValue(TEXT("PaintColor"),
						Livery);
					PrimerMID->SetVectorParameterValue(TEXT("PrimerColor"),
						FMath::Lerp(Livery,
							FLinearColor(0.55f, 0.55f, 0.56f), 0.5f));
					// The front far behind the tail: nothing painted
					// yet, the whole hull in primer.
					PrimerMID->SetScalarParameterValue(TEXT("PaintFrontX"),
						-1.0e9f);
					Component->SetMaterial(0, PrimerMID);
					UnitPaintMIDs.Add(Assignment.UnitId, PrimerMID);
				}
			}
			if (TObjectPtr<UMaterialInstanceDynamic>* WornPaint =
				UnitPaintMIDs.Find(Assignment.UnitId))
			{
				if (*WornPaint != nullptr
					&& Component->GetMaterial(0) != *WornPaint)
				{
					Component->SetMaterial(0, *WornPaint);
				}
			}
			if (bInTheBooth && Craft != nullptr)
			{
				float PaintProgress = 0.f;
				Coordinator->GetUnitCycleProgress(Assignment.UnitId,
					PaintProgress);
				const FBoxSphereBounds CraftBounds = Craft->GetBounds();
				const float HalfLen = CraftBounds.BoxExtent.X;
				const float FrontX = Location.X - HalfLen
					+ PaintProgress * HalfLen * 2.f;
				TObjectPtr<UMaterialInstanceDynamic>* PaintMID =
					UnitPaintMIDs.Find(Assignment.UnitId);
				if (PaintMID == nullptr)
				{
					if (UMaterialInterface* PaintBase =
						LoadObject<UMaterialInterface>(nullptr,
							SpacecraftPaintMaterialPath))
					{
						UMaterialInstanceDynamic* NewMID =
							UMaterialInstanceDynamic::Create(PaintBase,
								Component);
						Component->SetMaterial(0, NewMID);
						PaintMID = &UnitPaintMIDs.Add(
							Assignment.UnitId, NewMID);
					}
					// No paint material: the hull look stands in
					// (honest fallback, the stage still runs).
				}
				if (PaintMID != nullptr && *PaintMID != nullptr)
				{
					(*PaintMID)->SetScalarParameterValue(
						TEXT("PaintFrontX"), FrontX);
					// THE CUSTOMER'S COLOURS (owner: colour belongs to
					// the ships, and each contract paints the craft in
					// its customer's livery). The material has carried
					// a PaintColor parameter since the day it was built
					// and nothing ever set it, so every craft came out
					// of the booth in the material's default.
					(*PaintMID)->SetVectorParameterValue(
						TEXT("PaintColor"),
						FLBSpacecraftCustomerCatalogue::LiveryForRecipe(
							ProductionAuthority->GetContracts(),
							Unit->RecipeId));
				}
				FLBSpacecraftSprayRig* Rig =
					UnitSprayRigs.Find(Assignment.UnitId);
				if (Rig == nullptr)
				{
					FLBSpacecraftSprayRig NewRig;
					for (int32 Side = 0; Side < 2; ++Side)
					{
						const FName BodyKey(*FString::Printf(
							TEXT("%s_Spray%d"),
							*Assignment.UnitId.ToString(), Side));
						UStaticMeshComponent* Body =
							MakeBlockComponent(BodyKey,
								SpacecraftMistColour);
						if (Body != nullptr)
						{
							if (UStaticMesh* SprayMesh =
								TryGetStationMesh(FName(
									TEXT("Drone.Spray.Body"))))
							{
								Body->SetStaticMesh(SprayMesh);
								Body->EmptyOverrideMaterials();
							}
							NewRig.Bodies.Add(Body);
						}
						for (int32 Puff = 0; Puff < 3; ++Puff)
						{
							const FName MistKey(*FString::Printf(
								TEXT("%s_Mist%d_%d"),
								*Assignment.UnitId.ToString(), Side,
								Puff));
							if (UStaticMeshComponent* Mist =
								MakeBlockComponent(MistKey,
									SpacecraftMistColour))
							{
								NewRig.Mists.Add(Mist);
							}
						}
					}
					Rig = &UnitSprayRigs.Add(Assignment.UnitId, NewRig);
				}
				const float HullHalfWidth =
					CraftBounds.BoxExtent.Y;
				for (int32 Side = 0;
					Side < Rig->Bodies.Num(); ++Side)
				{
					if (Rig->Bodies[Side] == nullptr)
					{
						continue;
					}
					const float SideSign = Side == 0 ? 1.f : -1.f;
					const FVector SprayPos(FrontX,
						Location.Y + SideSign * (HullHalfWidth + 160.f),
						Lift + 260.f
							+ 14.f * FMath::Sin(VisualTimeSeconds * 3.f
								+ Side * PI));
					Rig->Bodies[Side]->SetWorldLocationAndRotation(
						SprayPos,
						FRotator(0.f, Side == 0 ? -90.f : 90.f, 0.f));
					for (int32 Puff = 0; Puff < 3; ++Puff)
					{
						const int32 MistIndex = Side * 3 + Puff;
						if (!Rig->Mists.IsValidIndex(MistIndex)
							|| Rig->Mists[MistIndex] == nullptr)
						{
							continue;
						}
						const float T = FMath::Fmod(
							VisualTimeSeconds * 1.6f + Puff * 0.33f,
							1.f);
						const FVector MistPos = FMath::Lerp(SprayPos,
							FVector(FrontX, Location.Y
								+ SideSign * HullHalfWidth * 0.4f,
								Lift + 180.f), T);
						Rig->Mists[MistIndex]->SetWorldTransform(
							FTransform(FQuat::Identity, MistPos,
								FVector(0.16f, 0.16f, 0.12f)
									* (1.f - 0.6f * T)));
					}
				}
			}
			else if (FLBSpacecraftSprayRig* DoneRig =
				UnitSprayRigs.Find(Assignment.UnitId))
			{
				// Painting over: the crew leaves, the finish stays.
				DestroySprayRig(*DoneRig);
				UnitSprayRigs.Remove(Assignment.UnitId);
			}
			UnitTransform.AddToTranslation(FVector(0.f, 0.f, Lift));
		}
		else
		{
			// STRIPPED SECTIONS ARE REAL-SIZE CHILDREN (audit
			// 2026-09-01): scaling the parent to crate metres
			// stretched every section 4x3x2 and tripled their nose-
			// to-aft spread for the whole pre-Hull run. With sections
			// shown, the parent keeps unit scale and hides its own
			// crate box; the honest crate stands in only when there
			// are no sections to show.
			if (StrippedHullSections.Contains(Assignment.UnitId))
			{
				UnitTransform.AddToTranslation(FVector(0.f, 0.f,
					SpacecraftStationBlockHeightCm));
				Component->SetVisibility(false, false);
			}
			else
			{
				UnitTransform.SetScale3D(
					FVector(4.f, 3.f, 2.f)); // crate metres
				UnitTransform.AddToTranslation(FVector(0.f, 0.f,
					SpacecraftStationBlockHeightCm
						+ SpacecraftCrateHalfHeightCm));
				Component->SetVisibility(true, false);
			}
		}
		Component->SetWorldTransform(UnitTransform);

		// A PART LANDING IS A MOMENT (owner 2026-09-01: "its not
		// actualy fitting them"). Half the Scout's components are
		// interior assemblies that attach out of sight inside the
		// closed hull, so every fit after the first now blooms a
		// working-blue ring under the craft and lets it fade - the
		// eye is told even when the geometry cannot show it.
		{
			const float FlashDelta = GetWorld() != nullptr
				? GetWorld()->GetDeltaSeconds() : 0.016f;
			const int32 FittedNow = Unit->ProducedComponents.Num();
			int32& Seen = UnitFittedSeen.FindOrAdd(Assignment.UnitId);
			if (FittedNow > Seen && Seen > 0)
			{
				UnitFitFlash.Add(Assignment.UnitId, 1.f);
			}
			Seen = FittedNow;
			if (float* Flash = UnitFitFlash.Find(Assignment.UnitId))
			{
				*Flash -= FlashDelta / 1.2f;
				if (*Flash <= 0.f)
				{
					if (TObjectPtr<UStaticMeshComponent>* Done =
						UnitFitFlashComps.Find(Assignment.UnitId))
					{
						if (*Done != nullptr)
						{
							(*Done)->DestroyComponent();
						}
					}
					UnitFitFlashComps.Remove(Assignment.UnitId);
					UnitFitFlash.Remove(Assignment.UnitId);
				}
				else
				{
					TObjectPtr<UStaticMeshComponent>& FlashComp =
						UnitFitFlashComps.FindOrAdd(Assignment.UnitId);
					if (FlashComp == nullptr)
					{
						FlashComp = MakeBlockComponent(
							FName(*FString::Printf(TEXT("%s_FitFlash"),
								*Assignment.UnitId.ToString())),
							LBSpacecraftPalette::IndicatorWorking);
						if (FlashComp != nullptr)
						{
							FlashComp->SetCastShadow(false);
						}
					}
					if (FlashComp != nullptr)
					{
						// The basic shape material is opaque, so the
						// fade is a colour lerp toward the floor tone
						// while the ring blooms outward.
						const float Bloom = 1.f - *Flash;
						const float RingM = 8.f + 12.f * Bloom;
						FlashComp->SetWorldTransform(FTransform(
							FRotator::ZeroRotator,
							Location + FVector(0.f, 0.f, 34.f),
							FVector(RingM, RingM, 0.02f)));
						if (UMaterialInstanceDynamic* FlashMID =
							Cast<UMaterialInstanceDynamic>(
								FlashComp->GetMaterial(0)))
						{
							FlashMID->SetVectorParameterValue(
								TEXT("Color"), FMath::Lerp(
									FLinearColor(0.59f, 0.565f, 0.52f),
									LBSpacecraftPalette::IndicatorWorking,
									*Flash));
						}
					}
				}
			}
		}
	}

	// Units that left the line: dispatched craft FLY OUT of the building;
	// anything else (load rollback, ledger anomaly) is removed quietly -
	// the presenter mirrors the authorities, it never invents a story.
	for (auto It = UnitSprayRigs.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			DestroySprayRig(It.Value());
			It.RemoveCurrent();
		}
	}
	for (auto It = UnitPaintMIDs.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			It.RemoveCurrent(); // review fix: MIDs die with their units
		}
	}
	for (auto It = UnitFittings.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			for (UStaticMeshComponent* Part : It.Value().Parts)
			{
				if (Part != nullptr)
				{
					Part->DestroyComponent();
				}
			}
			It.RemoveCurrent();
		}
	}
	for (auto It = ShellDeliveries.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			if (It.Value().DroneComp != nullptr)
			{
				It.Value().DroneComp->DestroyComponent();
			}
			if (It.Value().ShellComp != nullptr)
			{
				It.Value().ShellComp->DestroyComponent();
			}
			It.RemoveCurrent();
		}
	}
	for (auto It = UnitVisuals.CreateIterator(); It; ++It)
	{
		if (Live.Contains(It.Key()))
		{
			continue;
		}
		UStaticMeshComponent* Component = It.Value();
		const FLBSpacecraftUnitState* Unit =
			ProductionAuthority->FindUnit(It.Key());
		const bool bDispatched = Unit != nullptr
			&& Unit->Stage == ELBSpacecraftStage::Dispatched;
		if (bDispatched && Component != nullptr)
		{
			FLBSpacecraftDepartingVisual Departure;
			Departure.Component = Component;
			Departure.StartLocation = Component->GetComponentLocation();
			// The hover flames ride along; a craft that never grew them
			// (mesh fallback) grows them for the flight.
			FLBSpacecraftFlameSet Flames;
			if (FLBSpacecraftFlameSet* Existing = UnitFlames.Find(It.Key()))
			{
				Flames = *Existing;
				UnitFlames.Remove(It.Key());
			}
			else
			{
				Flames = MakeFlameSet(Component, It.Key());
			}
			Departure.BellyFlames = Flames.Belly;
			Departure.MainFlames = Flames.Main;
			// The gear flies too, so it can be SEEN to fold: it comes
			// off the line on its wheels and retracts on the sprint.
			if (FLBSpacecraftGearSet* Gear = UnitGear.Find(It.Key()))
			{
				Departure.GearLegs = Gear->Legs;
				Departure.GearAnchorZCm = Gear->AnchorZCm;
				Departure.GearRetractTravelCm = Gear->RetractTravelCm;
				UnitGear.Remove(It.Key());
			}
			// The six-part Scout's five children ride the flight as
			// Component's attached children (no per-frame work needed -
			// they follow its transform automatically), but still need
			// explicit destruction at the end, so they move with the
			// departing visual the same way the gear legs do.
			if (TArray<TObjectPtr<UStaticMeshComponent>>* V2Parts =
				ScoutV2Parts.Find(It.Key()))
			{
				Departure.ScoutParts = *V2Parts;
				ScoutV2Parts.Remove(It.Key());
				ScoutV2AttachedComponents.Remove(It.Key());
			}
			// Should not normally exist at departure - Hull is always
			// fitted long before Testing/Dispatched - but destroyed
			// defensively rather than left to leak if a unit somehow
			// reaches here first.
			if (TArray<TObjectPtr<UStaticMeshComponent>>* Sections =
				StrippedHullSections.Find(It.Key()))
			{
				for (UStaticMeshComponent* Section : *Sections)
				{
					if (Section != nullptr) { Section->DestroyComponent(); }
				}
				StrippedHullSections.Remove(It.Key());
			}
			Departing.Add(Departure);
			PlayWorldCue(FName(TEXT("ShipDeparts")), Component != nullptr
				? Component->GetComponentLocation() : FVector::ZeroVector);
		}
		else if (Component != nullptr)
		{
			if (FLBSpacecraftFlameSet* Flames = UnitFlames.Find(It.Key()))
			{
				DestroyFlameSet(*Flames);
				UnitFlames.Remove(It.Key());
			}
			if (FLBSpacecraftGearSet* Gear = UnitGear.Find(It.Key()))
			{
				// Destroyed explicitly: the legs hang off the craft
				// component, and destroying a parent DETACHES its
				// children rather than destroying them - the same trap
				// the rotor voices taught.
				for (const TWeakObjectPtr<UStaticMeshComponent>& Leg :
					Gear->Legs)
				{
					if (UStaticMeshComponent* LiveLeg = Leg.Get();
						IsValid(LiveLeg))
					{
						LiveLeg->DestroyComponent();
					}
				}
				UnitGear.Remove(It.Key());
			}
			if (TArray<TObjectPtr<UStaticMeshComponent>>* V2Parts =
				ScoutV2Parts.Find(It.Key()))
			{
				// Same trap, same fix: the six-part Scout's five
				// children hang off Component too.
				for (UStaticMeshComponent* Part : *V2Parts)
				{
					if (Part != nullptr) { Part->DestroyComponent(); }
				}
				ScoutV2Parts.Remove(It.Key());
				ScoutV2AttachedComponents.Remove(It.Key());
			}
			if (TArray<TObjectPtr<UStaticMeshComponent>>* Sections =
				StrippedHullSections.Find(It.Key()))
			{
				// Same trap, same fix: the loose hull sections hang off
				// Component too.
				for (UStaticMeshComponent* Section : *Sections)
				{
					if (Section != nullptr) { Section->DestroyComponent(); }
				}
				StrippedHullSections.Remove(It.Key());
			}
			Component->DestroyComponent();
		}
		It.RemoveCurrent();
	}
}

FVector ALBSpacecraftWIPPresentationActor::ComputeDepartureOffsetCm(
	float ElapsedSeconds, float InChicaneSeconds, float InChicaneWidthCm,
	float InSprintSeconds, float InSprintDistanceCm, float InClimbCm,
	float InLateralTargetCm)
{
	const float Total = InChicaneSeconds + InSprintSeconds;
	const float T = FMath::Clamp(ElapsedSeconds, 0.f, Total);
	// Forward progress made while weaving (a taxi-out, not the sprint).
	const float ChicaneRunCm = InChicaneWidthCm * 2.5f;
	FVector Offset = FVector::ZeroVector;
	if (T <= InChicaneSeconds && InChicaneSeconds > 0.f)
	{
		const float A = T / InChicaneSeconds;
		// PLAIN TAXI, NOT A CINEMATIC WEAVE (owner, 2026-08-30: "want to
		// see it do it but not the cinematic"). This still has the same
		// JOB the S-weave had - slide off the line and onto the site
		// runway centreline before the sprint - it just does it as a
		// smooth, direct slide rather than a showy S-curve.
		Offset.X = InLateralTargetCm * FMath::SmoothStep(0.f, 1.f, A);
		Offset.Y = -ChicaneRunCm * A;
		Offset.Z = InClimbCm * 0.25f * A;
		return Offset;
	}
	// Full pelt down the length of the factory: quadratic acceleration.
	const float U = InSprintSeconds > 0.f
		? FMath::Clamp((T - InChicaneSeconds) / InSprintSeconds, 0.f, 1.f)
		: 1.f;
	Offset.X = InLateralTargetCm;
	Offset.Y = -(ChicaneRunCm + InSprintDistanceCm * U * U);
	Offset.Z = InClimbCm * (0.25f + 0.75f * U);
	return Offset;
}

void ALBSpacecraftWIPPresentationActor::TickDepartures(float DeltaSeconds)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	const float Total = ChicaneSeconds + SprintSeconds;
	for (int32 Index = Departing.Num() - 1; Index >= 0; --Index)
	{
		FLBSpacecraftDepartingVisual& Departure = Departing[Index];
		if (!IsValid(Departure.Component))
		{
			Departing.RemoveAt(Index);
			continue;
		}
		Departure.ElapsedSeconds += DeltaSeconds;
		const FVector Offset = ComputeDepartureOffsetCm(
			Departure.ElapsedSeconds, ChicaneSeconds, ChicaneWidthCm,
			SprintSeconds, SprintDistanceCm, DepartureClimbCm,
			SiteRunwayXCm - Departure.StartLocation.X);
		Departure.Component->SetWorldLocation(
			Departure.StartLocation + Offset);
		// NO BANKING (owner, 2026-08-30: lose the cinematic) - the taxi
		// is a plain slide now, so there is no weave to bank through.
		const float BankDeg = 0.f;
		// Face the TRUE direction of motion (owner playtest fix: the
		// -90 assumption flew the -X-nosed Scout backwards), sampling
		// the path a hair ahead so the chicane swing steers the nose.
		const FVector Ahead = Departure.StartLocation
			+ ComputeDepartureOffsetCm(
				Departure.ElapsedSeconds + 0.05f, ChicaneSeconds,
				ChicaneWidthCm, SprintSeconds, SprintDistanceCm,
				DepartureClimbCm,
				SiteRunwayXCm - Departure.StartLocation.X);
		const FVector Motion = Ahead
			- Departure.Component->GetComponentLocation();
		float FaceYaw = -90.f + SpacecraftCraftNoseYawOffsetDeg;
		if (Motion.SizeSquared2D() > 1.f)
		{
			FaceYaw = FMath::RadiansToDegrees(
				FMath::Atan2(Motion.Y, Motion.X))
				+ SpacecraftCraftNoseYawOffsetDeg;
		}
		Departure.Component->SetWorldRotation(
			FRotator(0.f, FaceYaw, BankDeg));
		// Belly RCS through the weave; mains take over with speed.
		float Belly01 = 0.f;
		float Main01 = 0.f;
		ComputeThrusterMix(Departure.ElapsedSeconds, ChicaneSeconds,
			SprintSeconds, Belly01, Main01);
		ApplyFlameIntensity(Departure.BellyFlames, Belly01,
			VisualTimeSeconds);
		ApplyFlameIntensity(Departure.MainFlames, Main01,
			VisualTimeSeconds);
		// GEAR UP as the sprint starts (owner: it disappears when it
		// takes off at the end). Down through the chicane, because that
		// leg is a taxi onto the runway.
		ApplyGearRetraction(Departure.GearLegs, Departure.GearAnchorZCm,
			ComputeGearRetraction01(Departure.ElapsedSeconds,
				ChicaneSeconds, GearRetractSeconds),
			Departure.GearRetractTravelCm);
		if (Departure.ElapsedSeconds >= Total)
		{
			for (const TWeakObjectPtr<UStaticMeshComponent>& Flame :
				Departure.BellyFlames)
			{
				if (UStaticMeshComponent* Live = Flame.Get(); IsValid(Live))
				{
					Live->DestroyComponent();
				}
			}
			for (const TWeakObjectPtr<UStaticMeshComponent>& Flame :
				Departure.MainFlames)
			{
				if (UStaticMeshComponent* Live = Flame.Get(); IsValid(Live))
				{
					Live->DestroyComponent();
				}
			}
			for (const TWeakObjectPtr<UStaticMeshComponent>& Leg :
				Departure.GearLegs)
			{
				if (UStaticMeshComponent* Live = Leg.Get(); IsValid(Live))
				{
					Live->DestroyComponent();
				}
			}
			for (UStaticMeshComponent* Part : Departure.ScoutParts)
			{
				if (IsValid(Part))
				{
					Part->DestroyComponent();
				}
			}
			Departure.Component->DestroyComponent();
			Departing.RemoveAt(Index);
		}
	}
}

void ALBSpacecraftWIPPresentationActor::OnRuntimeRestored()
{
	// A restore rebuilds units under their ORIGINAL UnitIds, so an
	// in-flight departure animation belongs to a craft that no longer
	// exists. Destroy whatever of it still lives and drop the lot -
	// RefreshUnits reconstructs parked craft from the restored state.
	for (FLBSpacecraftDepartingVisual& Departure : Departing)
	{
		for (const TWeakObjectPtr<UStaticMeshComponent>& Flame :
			Departure.BellyFlames)
		{
			if (UStaticMeshComponent* Live = Flame.Get(); IsValid(Live))
			{
				Live->DestroyComponent();
			}
		}
		for (const TWeakObjectPtr<UStaticMeshComponent>& Flame :
			Departure.MainFlames)
		{
			if (UStaticMeshComponent* Live = Flame.Get(); IsValid(Live))
			{
				Live->DestroyComponent();
			}
		}
		for (const TWeakObjectPtr<UStaticMeshComponent>& Leg :
			Departure.GearLegs)
		{
			if (UStaticMeshComponent* Live = Leg.Get(); IsValid(Live))
			{
				Live->DestroyComponent();
			}
		}
		for (UStaticMeshComponent* Part : Departure.ScoutParts)
		{
			if (IsValid(Part))
			{
				Part->DestroyComponent();
			}
		}
		if (IsValid(Departure.Component))
		{
			Departure.Component->DestroyComponent();
		}
	}
	Departing.Reset();
}

bool ALBSpacecraftWIPPresentationActor::GetUnitVisualLocation(FName UnitId,
	FVector& OutLocation) const
{
	const TObjectPtr<UStaticMeshComponent>* Found = UnitVisuals.Find(UnitId);
	if (Found == nullptr || Found->Get() == nullptr)
	{
		return false;
	}
	OutLocation = Found->Get()->GetComponentLocation();
	return true;
}

void ALBSpacecraftWIPPresentationActor::TickSubAssemblyLogistics(
	float DeltaSeconds)
{
	using namespace LBSpacecraftWIPPresentationPrivate;
	(void)DeltaSeconds;
	if (BuildAuthority == nullptr || CraftingAuthority == nullptr)
	{
		return;
	}
	// --- buffer crates beside each machine (owner 2026-08-26: the
	// hull is made and waits in a small buffer next to the machine) ---
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr,
		SpacecraftCubePath);
	UMaterialInterface* Shape = LoadObject<UMaterialInterface>(nullptr,
		SpacecraftShapeMaterialPath);
	TSet<FName> Live;
	for (const FLBSpacecraftStationRecord& Record :
		BuildAuthority->GetStations())
	{
		const int32 Count =
			CraftingAuthority->GetBufferCount(Record.StationId);
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record.DefinitionId);
		if (Count <= 0 || Definition == nullptr)
		{
			continue;
		}
		Live.Add(Record.StationId);
		// One crate per two buffered items, up to three - the stack
		// growing beside the machine IS the buffer gauge.
		const int32 Crates = FMath::Clamp((Count + 1) / 2, 1, 3);
		const FName OutputItem =
			CraftingAuthority->GetStationOutputItem(Record.StationId);
		UStaticMesh* OutputMesh = OutputItem.IsNone()
			? nullptr : TryGetStationMesh(OutputItem);
		TArray<TObjectPtr<UStaticMeshComponent>>& Stack =
			BufferCrates.FindOrAdd(Record.StationId);
		while (Stack.Num() < Crates && Cube != nullptr)
		{
			UStaticMeshComponent* Crate =
				NewObject<UStaticMeshComponent>(this,
					UStaticMeshComponent::StaticClass());
			Crate->SetStaticMesh(
				OutputMesh != nullptr ? OutputMesh : Cube);
			Crate->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Crate->SetCastShadow(false);
			Crate->SetReceivesDecals(false);
			Crate->SetupAttachment(RootComponent);
			Crate->RegisterComponent();
			if (Shape != nullptr && OutputMesh == nullptr)
			{
				UMaterialInstanceDynamic* MID =
					UMaterialInstanceDynamic::Create(Shape, Crate);
				MID->SetVectorParameterValue(TEXT("Color"),
					SpacecraftCrateColour);
				Crate->SetMaterial(0, MID);
			}
			Stack.Add(Crate);
		}
		while (Stack.Num() > Crates)
		{
			if (Stack.Last() != nullptr)
			{
				Stack.Last()->DestroyComponent();
			}
			Stack.Pop();
		}
		const FVector Base = Record.WorldTransform.TransformPosition(
			FVector(Definition->FootprintCm.X * 0.5f + 120.f, 0.f, 0.f));
		for (int32 Index = 0; Index < Stack.Num(); ++Index)
		{
			if (Stack[Index] != nullptr)
			{
				Stack[Index]->SetWorldTransform(FTransform(
					FQuat::Identity,
					Base + FVector(0.f, 0.f, 40.f + Index * 82.f),
					FVector(0.8f, 0.8f, 0.8f)));
			}
		}
	}
	for (auto It = BufferCrates.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			for (UStaticMeshComponent* Crate : It.Value())
			{
				if (Crate != nullptr)
				{
					Crate->DestroyComponent();
				}
			}
			It.RemoveCurrent();
		}
	}
	// --- the heavy hauler's flights (mirrors the fleet, never invents) ---
	if (DroneFleetAuthority == nullptr)
	{
		return;
	}
	TSet<FName> LiveHaulers;
	for (const FLBSpacecraftHaulState& Haul :
		DroneFleetAuthority->GetHauls())
	{
		if (Haul.Phase == ELBSpacecraftHaulPhase::Idle)
		{
			continue; // parked at the rack, the crew visuals cover it
		}
		const FLBSpacecraftStationRecord* Rack = nullptr;
		const FLBSpacecraftStationRecord* Machine = nullptr;
		for (const FLBSpacecraftStationRecord& Record :
			BuildAuthority->GetStations())
		{
			if (Record.StationId == Haul.RackStationId)
			{
				Rack = &Record;
			}
			if (Record.StationId == Haul.MachineStationId)
			{
				Machine = &Record;
			}
		}
		if (Rack == nullptr || Machine == nullptr)
		{
			continue;
		}
		LiveHaulers.Add(Haul.RackStationId);
		TObjectPtr<UStaticMeshComponent>& Body =
			HaulerBodies.FindOrAdd(Haul.RackStationId);
		if (Body == nullptr)
		{
			if (UStaticMesh* HaulerMesh = TryGetStationMesh(
				FName(TEXT("Drone.CargoLift.Body"))))
			{
				Body = NewObject<UStaticMeshComponent>(this,
					UStaticMeshComponent::StaticClass());
				Body->SetStaticMesh(HaulerMesh);
				Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Body->SetCastShadow(true);
				Body->SetReceivesDecals(false);
				Body->SetupAttachment(RootComponent);
				Body->RegisterComponent();
			}
		}
		if (Body == nullptr)
		{
			continue;
		}
		const float Alpha = DroneFleetAuthority->HaulTravelSeconds > 0.f
			? FMath::Clamp(Haul.PhaseSeconds
				/ DroneFleetAuthority->HaulTravelSeconds, 0.f, 1.f)
			: 1.f;
		const FVector RackCm =
			Rack->WorldTransform.GetLocation() + FVector(0.f, 0.f, 560.f);
		const FVector MachineCm = Machine->WorldTransform.GetLocation()
			+ FVector(0.f, 0.f, 560.f);
		const bool bOutbound =
			Haul.Phase == ELBSpacecraftHaulPhase::ToMachine;
		const FVector From = bOutbound ? RackCm : MachineCm;
		const FVector To = bOutbound ? MachineCm : RackCm;
		const FVector Where = FMath::Lerp(From, To,
			FMath::SmoothStep(0.f, 1.f, Alpha));
		// The hook: returning with cargo, the machine's component hangs
		// under the hauler (owner: the parts the drones carry are the
		// real models now). Fallback stays empty-hook, never invented.
		TObjectPtr<UStaticMeshComponent>& Cargo =
			HaulerCargos.FindOrAdd(Haul.RackStationId);
		const bool bCarrying =
			!bOutbound && Haul.CarryCount > 0;
		UStaticMesh* CargoMesh = nullptr;
		if (bCarrying && CraftingAuthority != nullptr)
		{
			const FName CarryItem = CraftingAuthority
				->GetStationOutputItem(Haul.MachineStationId);
			CargoMesh = CarryItem.IsNone()
				? nullptr : TryGetStationMesh(CarryItem);
		}
		if (CargoMesh != nullptr)
		{
			if (Cargo == nullptr)
			{
				Cargo = NewObject<UStaticMeshComponent>(this,
					UStaticMeshComponent::StaticClass());
				Cargo->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Cargo->SetCastShadow(true);
				Cargo->SetReceivesDecals(false);
				Cargo->SetupAttachment(RootComponent);
				Cargo->RegisterComponent();
			}
			if (Cargo->GetStaticMesh() != CargoMesh)
			{
				Cargo->SetStaticMesh(CargoMesh);
			}
			Cargo->SetVisibility(true);
			Cargo->SetWorldLocation(Where - FVector(0.f, 0.f, 300.f));
		}
		else if (Cargo != nullptr)
		{
			Cargo->SetVisibility(false);
		}
		FRotator Facing = (To - From).Rotation();
		Facing.Pitch = 0.f;
		Body->SetWorldTransform(FTransform(Facing, Where, FVector(1.f)));
		Body->SetVisibility(true);
		// The slung crate rides only on the loaded leg home.
		TObjectPtr<UStaticMeshComponent>& CarryCrate =
			HaulerCrates.FindOrAdd(Haul.RackStationId);
		const bool bLoaded =
			Haul.Phase == ELBSpacecraftHaulPhase::ToStore
			&& Haul.CarryCount > 0;
		if (CarryCrate == nullptr && bLoaded && Cube != nullptr)
		{
			CarryCrate = NewObject<UStaticMeshComponent>(this,
				UStaticMeshComponent::StaticClass());
			CarryCrate->SetStaticMesh(Cube);
			CarryCrate->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			CarryCrate->SetCastShadow(false);
			CarryCrate->AttachToComponent(Body,
				FAttachmentTransformRules::KeepRelativeTransform);
			CarryCrate->SetRelativeLocation(FVector(0.f, 0.f, -120.f));
			CarryCrate->SetRelativeScale3D(FVector(0.9f, 0.9f, 0.9f));
			if (Shape != nullptr)
			{
				UMaterialInstanceDynamic* MID =
					UMaterialInstanceDynamic::Create(Shape, CarryCrate);
				MID->SetVectorParameterValue(TEXT("Color"),
					SpacecraftCrateColour);
				CarryCrate->SetMaterial(0, MID);
			}
			CarryCrate->RegisterComponent();
		}
		if (CarryCrate != nullptr)
		{
			CarryCrate->SetVisibility(bLoaded);
		}
	}
	for (auto It = HaulerBodies.CreateIterator(); It; ++It)
	{
		if (!LiveHaulers.Contains(It.Key()) && It.Value() != nullptr)
		{
			It.Value()->SetVisibility(false);
		}
	}
	for (auto It = HaulerCargos.CreateIterator(); It; ++It)
	{
		if (!LiveHaulers.Contains(It.Key()) && It.Value() != nullptr)
		{
			It.Value()->SetVisibility(false);
		}
	}
	// The slung crate too (audit 2026-09-01): hiding the body does not
	// propagate, so every completed haul left a tan crate hanging in
	// mid-air at the rack until the next haul happened to reuse it.
	for (auto It = HaulerCrates.CreateIterator(); It; ++It)
	{
		if (!LiveHaulers.Contains(It.Key()) && It.Value() != nullptr)
		{
			It.Value()->SetVisibility(false);
		}
	}
}

void ALBSpacecraftWIPPresentationActor::ClearUnitFittings(FName UnitId)
{
	FLBSpacecraftUnitFittings* Fittings = UnitFittings.Find(UnitId);
	if (Fittings == nullptr)
	{
		return;
	}
	for (UStaticMeshComponent* Part : Fittings->Parts)
	{
		if (Part != nullptr)
		{
			Part->DestroyComponent();
		}
	}
	UnitFittings.Remove(UnitId);
}

void ALBSpacecraftWIPPresentationActor::RefreshUnitFittings(FName UnitId,
	UStaticMeshComponent* UnitComponent, int32 RouteIndex, int32 RouteCount,
	bool bCargoRecipe)
{
	if (UnitComponent == nullptr || UnitComponent->GetStaticMesh() == nullptr)
	{
		return;
	}
	// Route progress reveals the six components one by one; the pipe
	// and cable runs arrive with the fifth (the hull closes soon after).
	const float Progress = RouteCount > 1
		? static_cast<float>(RouteIndex) / (RouteCount - 1) : 0.f;
	// Seven reveals: the six components, then the canopy glass - the
	// last thing fitted before the hull closes (owner 2026-08-26).
	const int32 Reveal = FMath::Clamp(
		FMath::CeilToInt(Progress * 7.f), 0, 7);
	FLBSpacecraftUnitFittings& Fittings = UnitFittings.FindOrAdd(UnitId);
	if (Fittings.RevealedCount == Reveal)
	{
		return;
	}
	for (UStaticMeshComponent* Part : Fittings.Parts)
	{
		if (Part != nullptr)
		{
			Part->DestroyComponent();
		}
	}
	Fittings.Parts.Reset();
	Fittings.RevealedCount = Reveal;
	if (Reveal <= 0)
	{
		return;
	}

	const FBoxSphereBounds HullBounds =
		UnitComponent->GetStaticMesh()->GetBounds();
	const FVector E = HullBounds.BoxExtent;   // hull half-size, local
	const FVector O = HullBounds.Origin;
	// Sockets in hull-local space, nose +X: engine aft, power behind
	// the middle, hull stack amidships, electronics forward, nav at
	// the nose, cockpit interior front-top.
	const TPair<const TCHAR*, FVector> Sockets[] = {
		{ TEXT("Component.Propulsion"),
			FVector(-0.55f, 0.f, 0.18f) },
		{ TEXT("Component.Power"), FVector(-0.25f, 0.15f, 0.15f) },
		{ TEXT("Component.Hull"), FVector(-0.05f, -0.3f, 0.12f) },
		{ TEXT("Component.Electronics"),
			FVector(0.2f, 0.3f, 0.15f) },
		{ TEXT("Component.Navigation"), FVector(0.55f, 0.f, 0.2f) },
		{ TEXT("Component.Interior"), FVector(0.3f, -0.15f, 0.3f) } };

	auto SocketPoint = [&](const FVector& Fraction)
	{
		return O + FVector(Fraction.X * E.X * 2.f,
			Fraction.Y * E.Y * 2.f, Fraction.Z * E.Z * 2.f);
	};

	int32 Placed = 0;
	FVector Previous = FVector::ZeroVector;
	bool bHavePrevious = false;
	for (const auto& Socket : Sockets)
	{
		if (Placed >= Reveal)
		{
			break;
		}
		UStaticMesh* Mesh = TryGetStationMesh(FName(Socket.Key));
		const FVector Local = SocketPoint(Socket.Value);
		if (Mesh != nullptr)
		{
			const FName Key(*FString::Printf(TEXT("%s_Fit%d"),
				*UnitId.ToString(), Placed));
			UStaticMeshComponent* Part =
				NewObject<UStaticMeshComponent>(this,
					UStaticMeshComponent::StaticClass(), Key);
			Part->SetStaticMesh(Mesh);
			Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Part->SetCastShadow(true);
			Part->SetReceivesDecals(false);
			Part->SetupAttachment(UnitComponent);
			Part->RegisterComponent();
			Part->SetRelativeLocation(Local);
			Fittings.Parts.Add(Part);
		}
		// The pipe/cable dressing links the sockets once most parts
		// are in - thin dark runs plus one warning-orange line.
		if (bHavePrevious && Reveal >= 5)
		{
			const FVector Delta = Local - Previous;
			const float Length = Delta.Size();
			if (Length > 50.f)
			{
				const FName PipeKey(*FString::Printf(
					TEXT("%s_Pipe%d"), *UnitId.ToString(), Placed));
				UStaticMeshComponent* Pipe = MakeBlockComponent(PipeKey,
					Placed % 3 == 2
						? FLinearColor(0.72f, 0.30f, 0.05f)
						: FLinearColor(0.10f, 0.11f, 0.13f));
				if (Pipe != nullptr)
				{
					// MakeBlockComponent attaches to the actor root;
					// re-seat it on the unit so it rides along.
					Pipe->AttachToComponent(UnitComponent,
						FAttachmentTransformRules::KeepRelativeTransform);
					Pipe->SetRelativeLocation((Previous + Local) * 0.5f);
					Pipe->SetRelativeRotation(
						Delta.GetSafeNormal().Rotation());
					Pipe->SetRelativeScale3D(FVector(
						Length / 100.f, 0.14f, 0.14f));
					Fittings.Parts.Add(Pipe);
				}
			}
		}
		Previous = Local;
		bHavePrevious = true;
		++Placed;
	}
	if (Reveal >= 7)
	{
		// The canopy glass drops on at its authored position - the
		// forms share one baked transform, so zero offset aligns it.
		if (UStaticMesh* CanopyMesh = TryGetStationMesh(FName(
			bCargoRecipe ? TEXT("Canopy.Cargo") : TEXT("Canopy.Scout"))))
		{
			const FName CanopyKey(*FString::Printf(TEXT("%s_FitGlass"),
				*UnitId.ToString()));
			UStaticMeshComponent* Glass =
				NewObject<UStaticMeshComponent>(this,
					UStaticMeshComponent::StaticClass(), CanopyKey);
			Glass->SetStaticMesh(CanopyMesh);
			Glass->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Glass->SetCastShadow(false);
			Glass->SetReceivesDecals(false);
			Glass->SetupAttachment(UnitComponent);
			Glass->RegisterComponent();
			Glass->SetRelativeLocation(FVector::ZeroVector);
			Fittings.Parts.Add(Glass);
		}
	}
}

void ALBSpacecraftWIPPresentationActor::BeginShellDelivery(
	FName UnitId, const FVector& StationLocation, UStaticMesh* ShellMesh)
{
	// The heavy drone carries the shell in; without the drone mesh or a
	// shell form the unit simply appears - an honest fallback, never a
	// blocked line.
	UStaticMesh* DroneMesh =
		TryGetStationMesh(FName(TEXT("Drone.CargoLift.Body")));
	if (DroneMesh == nullptr || ShellMesh == nullptr)
	{
		ShellDeliveredUnits.Add(UnitId);
		return;
	}
	FLBSpacecraftShellDelivery Delivery;
	Delivery.StationLocation = StationLocation;
	const FName DroneKey(*FString::Printf(TEXT("%s_ShellDrone"),
		*UnitId.ToString()));
	Delivery.DroneComp = MakeTrackPieceComponent(DroneKey, DroneMesh);
	const FName ShellKey(*FString::Printf(TEXT("%s_ShellCargo"),
		*UnitId.ToString()));
	Delivery.ShellComp = MakeTrackPieceComponent(ShellKey, ShellMesh);
	if (Delivery.DroneComp == nullptr || Delivery.ShellComp == nullptr)
	{
		ShellDeliveredUnits.Add(UnitId);
		return;
	}
	ShellDeliveries.Add(UnitId, Delivery);
}

void ALBSpacecraftWIPPresentationActor::TickShellDeliveries(
	float DeltaSeconds)
{
	// Fly in high from the dock side, lower the shell to the deck,
	// release, climb away: FlyIn 3 s, Lower 1.5 s, Depart 1.5 s.
	constexpr float FlyInSeconds = 3.f;
	constexpr float LowerSeconds = 1.5f;
	constexpr float DepartSeconds = 1.5f;
	const FVector ApproachOffset(3500.f, 1500.f, 2600.f);
	for (auto It = ShellDeliveries.CreateIterator(); It; ++It)
	{
		FLBSpacecraftShellDelivery& Delivery = It.Value();
		Delivery.Elapsed += DeltaSeconds;
		const FVector Station = Delivery.StationLocation;
		FVector DronePos;
		bool bCarrying = true;
		if (Delivery.Elapsed < FlyInSeconds)
		{
			const float A = FMath::SmoothStep(0.f, 1.f,
				Delivery.Elapsed / FlyInSeconds);
			DronePos = Station + FMath::Lerp(ApproachOffset,
				FVector(0.f, 0.f, 1400.f), A);
		}
		else if (Delivery.Elapsed < FlyInSeconds + LowerSeconds)
		{
			const float A = (Delivery.Elapsed - FlyInSeconds)
				/ LowerSeconds;
			DronePos = Station
				+ FVector(0.f, 0.f, FMath::Lerp(1400.f, 620.f, A));
		}
		else if (Delivery.Elapsed
			< FlyInSeconds + LowerSeconds + DepartSeconds)
		{
			// Released: the real unit visual takes over on the deck.
			bCarrying = false;
			const float A = (Delivery.Elapsed - FlyInSeconds
				- LowerSeconds) / DepartSeconds;
			DronePos = Station + FMath::Lerp(
				FVector(0.f, 0.f, 620.f),
				FVector(-2500.f, -1200.f, 3000.f),
				FMath::SmoothStep(0.f, 1.f, A));
		}
		else
		{
			if (Delivery.DroneComp != nullptr)
			{
				Delivery.DroneComp->DestroyComponent();
			}
			if (Delivery.ShellComp != nullptr)
			{
				Delivery.ShellComp->DestroyComponent();
			}
			ShellDeliveredUnits.Add(It.Key());
			It.RemoveCurrent();
			continue;
		}
		if (Delivery.DroneComp != nullptr)
		{
			Delivery.DroneComp->SetWorldLocation(DronePos);
		}
		if (Delivery.ShellComp != nullptr)
		{
			Delivery.ShellComp->SetVisibility(bCarrying);
			if (bCarrying)
			{
				Delivery.ShellComp->SetWorldLocation(
					DronePos - FVector(0.f, 0.f, 420.f));
			}
		}
	}
}

void ALBSpacecraftWIPPresentationActor::RefreshSiteShells()
{
	// ONE SHELL PER PLACED SITE BUILDING (owner 2026-08-28: the ship
	// factory, parts factory and power plant stand on the world map at
	// one scale, and the player places each). Shells are the roofline
	// the map reads; entering a building lifts its own roof and leaves
	// the others standing, which is what makes the map a place.
	if (BuildAuthority == nullptr)
	{
		return;
	}
	if (ShellViewPawn.Get() == nullptr)
	{
		if (APlayerController* Controller =
			GetWorld()->GetFirstPlayerController())
		{
			ShellViewPawn = Cast<ALBSpacecraftPlayerPawn>(
				Controller->GetPawn());
		}
	}
	const bool bOnMap = ShellViewPawn.IsValid()
		&& ShellViewPawn->IsSiteMapView();
	const FName Entered = ShellViewPawn.IsValid()
		? ShellViewPawn->GetFocusedBuilding() : NAME_None;

	TSet<FName> Live;
	for (const FLBSpacecraftStationRecord& Record :
		BuildAuthority->GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record.DefinitionId);
		if (Definition == nullptr || !Definition->bSiteBuilding)
		{
			continue;
		}
		Live.Add(Record.StationId);
		TObjectPtr<UStaticMeshComponent>* Existing =
			SiteShells.Find(Record.StationId);
		UStaticMeshComponent* Shell =
			Existing != nullptr ? Existing->Get() : nullptr;
		if (Shell == nullptr)
		{
			UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr,
				TEXT("/Game/LineBoss/Candidates/Spacecraft/")
				TEXT("StationMeshes_v001/Meshes/")
				TEXT("SM_LB_ST_ShipFactoryHall_v002")
				TEXT(".SM_LB_ST_ShipFactoryHall_v002"));
			if (Mesh == nullptr)
			{
				continue; // draws less, never more
			}
			Shell = NewObject<UStaticMeshComponent>(this,
				UStaticMeshComponent::StaticClass(),
				FName(*FString::Printf(TEXT("SiteShell_%s"),
					*Record.StationId.ToString())));
			Shell->SetStaticMesh(Mesh);
			Shell->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Shell->SetCastShadow(true);
			Shell->SetReceivesDecals(false);
			Shell->SetupAttachment(RootComponent);
			Shell->RegisterComponent();
			// Scaled to the building's declared footprint - one site
			// scale means the same mesh serves all three until each
			// has its own model.
			const FVector MeshSize = Mesh->GetBounds().BoxExtent * 2.0;
			const FVector2D Span = Definition->FootprintCm;
			const float ScaleX = Span.X / FMath::Max(MeshSize.X, 1.0);
			const float ScaleY = Span.Y / FMath::Max(MeshSize.Y, 1.0);
			const float ScaleZ = FMath::Max(1.f,
				(ScaleX + ScaleY) * 0.35f);
			Shell->SetWorldTransform(FTransform(
				Record.WorldTransform.GetRotation(),
				Record.WorldTransform.GetLocation(),
				FVector(ScaleX, ScaleY, ScaleZ)));
			SiteShells.Add(Record.StationId, Shell);
		}
		// Standing on the map; a building you are INSIDE has its roof
		// off.
		//
		// This used to be "the one you ENTERED has its roof off", and
		// that was subtly wrong in a way that wasted most of a day of
		// captures: clicking or watching a LINE STATION sets the focus
		// to the station, so the hall stopped counting as entered and
		// its shell dropped straight back over the camera. Every
		// close-up came back as the inside of a roof, and the camera
		// diagnostics all read correct because the camera WAS correct.
		//
		// Asking whether the camera is inside the footprint answers it
		// for every case, including ones nobody has written yet: a
		// station selected, a drone followed, a launch tracked.
		bool bInside = false;
		if (!bOnMap && ShellViewPawn.IsValid()
			&& !Definition->InteriorFloorCm.IsNearlyZero())
		{
			const FVector Pivot = ShellViewPawn->GetActorLocation();
			const FVector Centre = Record.WorldTransform.GetLocation();
			bInside =
				FMath::Abs(Pivot.X - Centre.X)
					<= Definition->InteriorFloorCm.X * 0.5f
				&& FMath::Abs(Pivot.Y - Centre.Y)
					<= Definition->InteriorFloorCm.Y * 0.5f;
		}
		const bool bShow =
			bOnMap || (Record.StationId != Entered && !bInside);
		if (Shell->IsVisible() != bShow)
		{
			Shell->SetVisibility(bShow);
		}
	}
	for (auto It = SiteShells.CreateIterator(); It; ++It)
	{
		if (!Live.Contains(It.Key()))
		{
			if (It.Value() != nullptr)
			{
				It.Value()->DestroyComponent();
			}
			It.RemoveCurrent();
		}
	}
	RefreshSiteRoads();
	RefreshHallInterior();
	// The interior is INSIDE a building: on the site map its roof is on,
	// so the dressing under it must not show through.
	for (UStaticMeshComponent* Piece : HallInteriorPieces)
	{
		if (Piece != nullptr && Piece->IsVisible() == bOnMap)
		{
			Piece->SetVisibility(!bOnMap);
		}
	}
	// And the converse (owner 2026-09-01: "the walkways should go") -
	// the site roads are OUTSIDE furniture, and with the hall roofless
	// they showed through as grey walkway strips across the factory
	// floor. Nothing on this floor walks; roads live on the site view.
	// The 20 m survey grid is site furniture too: its painted bars sit
	// higher than the hall's floor paint and were striping the factory
	// floor from underneath (owner 2026-09-01 "and the yellow lines?").
	if (SiteGridLines != nullptr && SiteGridLines->IsVisible() != bOnMap)
	{
		SiteGridLines->SetVisibility(bOnMap);
	}
	for (UStaticMeshComponent* Road : RoadPieces)
	{
		if (Road != nullptr && Road->IsVisible() != bOnMap)
		{
			Road->SetVisibility(bOnMap);
		}
	}
}

UStaticMeshComponent* ALBSpacecraftWIPPresentationActor::MakeRoadSlab(
	FName SlabName, const FVector& CentreCm, const FVector2D& SizeCm)
{
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr,
		TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (Cube == nullptr)
	{
		return nullptr;
	}
	UStaticMeshComponent* Slab = NewObject<UStaticMeshComponent>(this,
		UStaticMeshComponent::StaticClass(), SlabName);
	Slab->SetStaticMesh(Cube);
	Slab->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Slab->SetCastShadow(false);
	Slab->SetupAttachment(RootComponent);
	Slab->RegisterComponent();
	// The engine cube is 100 cm; a road is a thin slab just above the
	// ground so it reads as surfacing rather than a wall.
	// Sat ON the floor tiles, not in them: the tile mesh has real
	// thickness, and a 6 cm slab vanished inside it - roads that only
	// showed where they overhung the tiles.
	Slab->SetWorldTransform(FTransform(FQuat::Identity,
		CentreCm + FVector(0.f, 0.f, 22.f),
		FVector(SizeCm.X / 100.f, SizeCm.Y / 100.f, 0.3f)));
	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr,
		TEXT("/Engine/BasicShapes/BasicShapeMaterial")
		TEXT(".BasicShapeMaterial")))
	{
		if (UMaterialInstanceDynamic* Road =
			UMaterialInstanceDynamic::Create(Base, this))
		{
			// Dark cold grey: road surfacing against the pale apron,
			// in the settled clean-industrial language.
			Road->SetVectorParameterValue(TEXT("Color"),
				FLinearColor(0.16f, 0.17f, 0.19f, 1.f));
			Slab->SetMaterial(0, Road);
		}
	}
	RoadPieces.Add(Slab);
	return Slab;
}

void ALBSpacecraftWIPPresentationActor::RefreshSiteRoads()
{
	// ROADS TO THE DOORS (owner 2026-08-28). A spine runs down the
	// site's west side; each placed building gets a spur from its own
	// DOOR to that spine. The door position is the definition's, so a
	// rotated building is served on the side its door actually faces
	// rather than wherever the road happened to be drawn.
	if (BuildAuthority == nullptr)
	{
		return;
	}
	TArray<const FLBSpacecraftStationRecord*> Buildings;
	for (const FLBSpacecraftStationRecord& Record :
		BuildAuthority->GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record.DefinitionId);
		if (Definition != nullptr && Definition->bSiteBuilding)
		{
			Buildings.Add(&Record);
		}
	}
	// Rebuilt only when the set changes - roads are static furniture,
	// and rebuilding every tick would be a component churn for nothing.
	if (Buildings.Num() == RoadBuildingCount)
	{
		return;
	}
	RoadBuildingCount = Buildings.Num();
	for (UStaticMeshComponent* Piece : RoadPieces)
	{
		if (Piece != nullptr)
		{
			Piece->DestroyComponent();
		}
	}
	RoadPieces.Reset();
	if (Buildings.Num() == 0)
	{
		return;
	}

	// 16 m: a two-lane industrial road. 9 m was invisible at map
	// distance, which for a feature whose whole job is to read on the
	// map is the same as not being there.
	// 16 m: a two-lane industrial road. 9 m was invisible at map
	// distance, which for a feature whose whole job is to read on the
	// map is the same as not being there.
	constexpr float RoadWidthCm = 1600.f;

	// A PERIMETER LOOP (owner 2026-08-28: "yeah do the perimeter
	// loop"). The ring runs around everything built, with a spur from
	// each building's DOOR to the nearest side - an estate road rather
	// than one spine with long branches off it. The ring is derived
	// from the buildings' own bounds so it grows with the site, with a
	// floor under it so a single building still gets a proper loop
	// rather than a collar.
	constexpr float RingMarginCm = 7000.f;
	constexpr float RingMinHalfCm = 15000.f;
	FVector2D Lo(FLT_MAX, FLT_MAX);
	FVector2D Hi(-FLT_MAX, -FLT_MAX);
	for (const FLBSpacecraftStationRecord* Record : Buildings)
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record->DefinitionId);
		if (Definition == nullptr)
		{
			continue;
		}
		const FVector Where = Record->WorldTransform.GetLocation();
		const FVector2D Half = Definition->FootprintCm * 0.5f;
		Lo.X = FMath::Min(Lo.X, static_cast<float>(Where.X) - Half.X);
		Lo.Y = FMath::Min(Lo.Y, static_cast<float>(Where.Y) - Half.Y);
		Hi.X = FMath::Max(Hi.X, static_cast<float>(Where.X) + Half.X);
		Hi.Y = FMath::Max(Hi.Y, static_cast<float>(Where.Y) + Half.Y);
	}
	if (Lo.X > Hi.X)
	{
		return;
	}
	const FVector2D Centre((Lo.X + Hi.X) * 0.5f, (Lo.Y + Hi.Y) * 0.5f);
	const float HalfX = FMath::Max(
		(Hi.X - Lo.X) * 0.5f + RingMarginCm, RingMinHalfCm);
	const float HalfY = FMath::Max(
		(Hi.Y - Lo.Y) * 0.5f + RingMarginCm, RingMinHalfCm);
	// Kept inside the ground it is drawn on.
	const float Bound =
		ALBSpacecraftBuildAuthority::SiteHalfExtentCm() - RoadWidthCm;
	const float WestX = FMath::Max(Centre.X - HalfX, -Bound);
	const float EastX = FMath::Min(Centre.X + HalfX, Bound);
	const float SouthY = FMath::Max(Centre.Y - HalfY, -Bound);
	const float NorthY = FMath::Min(Centre.Y + HalfY, Bound);
	const float SpanX = EastX - WestX + RoadWidthCm;
	const float SpanY = NorthY - SouthY + RoadWidthCm;
	MakeRoadSlab(FName(TEXT("RoadRingWest")),
		FVector(WestX, (SouthY + NorthY) * 0.5f, 0.f),
		FVector2D(RoadWidthCm, SpanY));
	MakeRoadSlab(FName(TEXT("RoadRingEast")),
		FVector(EastX, (SouthY + NorthY) * 0.5f, 0.f),
		FVector2D(RoadWidthCm, SpanY));
	MakeRoadSlab(FName(TEXT("RoadRingSouth")),
		FVector((WestX + EastX) * 0.5f, SouthY, 0.f),
		FVector2D(SpanX, RoadWidthCm));
	MakeRoadSlab(FName(TEXT("RoadRingNorth")),
		FVector((WestX + EastX) * 0.5f, NorthY, 0.f),
		FVector2D(SpanX, RoadWidthCm));

	// Spurs: each door to the NEAREST side of the ring, so the road a
	// building meets is the one its door faces.
	for (const FLBSpacecraftStationRecord* Record : Buildings)
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record->DefinitionId);
		if (Definition == nullptr || Definition->DoorOffsetCm.IsNearlyZero())
		{
			continue;
		}
		const FVector Door =
			Definition->DoorWorldCm(Record->WorldTransform);
		const float ToWest = FMath::Abs(Door.X - WestX);
		const float ToEast = FMath::Abs(Door.X - EastX);
		const float ToSouth = FMath::Abs(Door.Y - SouthY);
		const float ToNorth = FMath::Abs(Door.Y - NorthY);
		const float Nearest =
			FMath::Min(FMath::Min(ToWest, ToEast),
				FMath::Min(ToSouth, ToNorth));
		const FName SpurName(*FString::Printf(TEXT("RoadSpur_%s"),
			*Record->StationId.ToString()));
		if (Nearest < RoadWidthCm)
		{
			continue; // the door already meets the ring
		}
		if (Nearest == ToWest || Nearest == ToEast)
		{
			const float SideX = Nearest == ToWest ? WestX : EastX;
			MakeRoadSlab(SpurName,
				FVector((Door.X + SideX) * 0.5f, Door.Y, 0.f),
				FVector2D(FMath::Abs(Door.X - SideX), RoadWidthCm));
		}
		else
		{
			const float SideY = Nearest == ToSouth ? SouthY : NorthY;
			MakeRoadSlab(SpurName,
				FVector(Door.X, (Door.Y + SideY) * 0.5f, 0.f),
				FVector2D(RoadWidthCm, FMath::Abs(Door.Y - SideY)));
		}
	}
	UE_LOG(LogTemp, Display,
		TEXT("LBSiteRoads %d pieces for %d buildings (ring %.0f x %.0f)"),
		RoadPieces.Num(), Buildings.Num(), EastX - WestX,
		NorthY - SouthY);
}

void ALBSpacecraftWIPPresentationActor::RefreshHallInterior()
{
	// THE LIFE AROUND THE LINE (owner 2026-08-28). Four generated
	// pieces, placed from the line's OWN geometry rather than from
	// numbers typed here: a stockpile beside every line station (the
	// parts each one fits, waiting where the drones collect them - the
	// owner's Production Line model made visible), columns down both
	// flanks, a gantry crane over the middle of the line, and the
	// dispatch door at the runway end where a finished craft leaves.
	//
	// Rebuilt only when the number of line stations changes: it is
	// fixed dressing, and rebuilding per tick would churn components
	// for nothing.
	if (BuildAuthority == nullptr)
	{
		return;
	}
	const FLBSpacecraftStationRecord* Hall = nullptr;
	const FLBSpacecraftStationDefinition* HallDefinition = nullptr;
	TArray<const FLBSpacecraftStationRecord*> LineStations;
	for (const FLBSpacecraftStationRecord& Record :
		BuildAuthority->GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record.DefinitionId);
		if (Definition == nullptr)
		{
			continue;
		}
		if (Definition->bSiteBuilding
			&& !Definition->InteriorFloorCm.IsNearlyZero())
		{
			Hall = &Record;
			HallDefinition = Definition;
		}
		else if (!Definition->StageClassId.IsNone())
		{
			LineStations.Add(&Record);
		}
	}
	// Rebuilt when the LINE changes - or the CRANE COUNT: a bought
	// crane must appear on the rails at once, not at the next station
	// placement (PULSE_LINE_DESIGN_v001, 2026-09-02).
	const int32 CraneCountNow = BuildAuthority != nullptr
		? BuildAuthority->GetCraneCount() : 1;
	if (LineStations.Num() == HallInteriorStationCount
		&& CraneCountNow == HallInteriorCraneCount)
	{
		return;
	}
	HallInteriorStationCount = LineStations.Num();
	HallInteriorCraneCount = CraneCountNow;
	for (UStaticMeshComponent* Piece : HallInteriorPieces)
	{
		if (Piece != nullptr)
		{
			Piece->DestroyComponent();
		}
	}
	HallInteriorPieces.Reset();
	// HALL FIRST, LINE SECOND (owner 2026-09-01: "the screen is black
	// until you put the station in"). This used to bail with zero line
	// stations, so a brand-new player ENTERING their empty ship factory
	// saw a black void until the first station spawned the first
	// geometry. The ROOM - walls, door, the waiting crane - exists the
	// moment the hall does; every station-derived piece below already
	// falls back to hall-centre maths when the line is empty.
	if (Hall == nullptr)
	{
		return;
	}

	auto LoadInterior = [](const TCHAR* Name) -> UStaticMesh*
	{
		// Stockpile/Column/Crane/Door are pre-existing Candidate intake
		// content - blocked out with the rest of the Meshy pipeline
		// (owner, 2026-08-30) while LoadShell's own three pieces below
		// (walls, trusses, lights - built procedurally, not
		// commissioned) keep rendering.
		if (LBSpacecraftWIPPresentationPrivate::bBlockoutMeshyContent)
		{
			return nullptr;
		}
		return LoadObject<UStaticMesh>(nullptr,
			*FString::Printf(TEXT("/Game/LineBoss/Candidates/Spacecraft/")
				TEXT("ShipFactoryInterior_v001/%s.%s"), Name, Name));
	};
	UStaticMesh* Stockpile = LoadInterior(TEXT("SM_LB_IN_StockpileRack"));
	UStaticMesh* Column = LoadInterior(TEXT("SM_LB_IN_HallColumn"));
	// THE COMMISSIONED GANTRY, with the old block crane behind it.
	//
	// Drawn orthographic references were fed to image-to-3D after two
	// text-prompted attempts came back with handrails and a push handle
	// on machines nothing human ever touches. This one has rail bogies,
	// lattice-braced box girders, a trolley and a spreader - and no
	// walkways, ladders or cab.
	//
	// Scaled from the CLEAR SPAN rather than the overall width: what
	// has to fit under a portal is the craft plus its working room, and
	// that is the opening between the legs, not the outside of the
	// machine. 23 m of opening makes it 31.4 m wide and 17.0 m tall.
	// GENERATED v002, not commissioned. Three text briefs for this
	// machine produced three plausible wrong ones - two monorails and a
	// portal turned a quarter turn - because no adjective says which
	// axis the bridge crosses. Scripts/build_gantry_portal.py builds it
	// from GantryRailSpanCm() instead, in four pieces that move
	// separately.
	auto LoadGantry = [](const TCHAR* Piece) -> UStaticMesh*
	{
		// NESTED, because Interchange puts each imported asset in its
		// own <Name>/StaticMeshes/ folder rather than flat beside its
		// siblings. The flat path here loaded nothing, the fallback
		// quietly drew the old block crane, and only the warning added
		// this morning said so. Guessing an asset path is the same
		// mistake as guessing a cook entry.
		const FString Path = FString::Printf(
			TEXT("/Game/LineBoss/Candidates/Spacecraft/Gantry_v002/")
			TEXT("LB_Gantry_%s/StaticMeshes/LB_Gantry_%s.LB_Gantry_%s"),
			Piece, Piece, Piece);
		return LoadObject<UStaticMesh>(nullptr, *Path);
	};
	UStaticMesh* Crane = LoadGantry(TEXT("portal"));
	UStaticMesh* CraneTrolley = LoadGantry(TEXT("trolley"));
	UStaticMesh* CraneHoist = LoadGantry(TEXT("hoist"));
	if (Crane == nullptr)
	{
		// LOUDLY, because this exact silence shipped a build. The
		// commissioned crane is loaded by hard-coded path, which the
		// COOKER CANNOT SEE - nothing references it, so nothing
		// packaged it - and this fallback then quietly drew the old
		// block crane. The packaged game looked correct and was a
		// revision behind, with no error anywhere to find.
		//
		// The fix is Config/DefaultGame.ini's DirectoriesToAlwaysCook;
		// this warning is how anyone learns that it has been missed
		// again, since a graceful fallback is otherwise indistinguishable
		// from success.
		UE_LOG(LogTemp, Warning,
			TEXT("SPACECRAFT PRESENTER: the generated gantry portal did "
				"not load - falling back to the block crane. If this is "
				"a packaged build, Gantry_v002 is missing from "
				"DirectoriesToAlwaysCook."));
		Crane = LoadInterior(TEXT("SM_LB_IN_GantryCrane"));
	}
	// THE RAILS ARE NOT PART OF THE CRANE (owner 2026-08-29: "take the
	// rails off and use in the map"). The gantry travels and the track
	// does not - modelled as one object the rails would slide down the
	// hall with it, which is exactly backwards.
	UStaticMesh* CraneRails = LoadGantry(TEXT("rails"));
	UStaticMesh* Door = LoadInterior(TEXT("SM_LB_IN_DispatchDoor"));
	auto Place = [this](UStaticMesh* Mesh, const FName& Name,
		const FVector& Where, float Yaw)
	{
		if (Mesh == nullptr)
		{
			return;
		}
		UStaticMeshComponent* Piece = NewObject<UStaticMeshComponent>(
			this, UStaticMeshComponent::StaticClass(), Name);
		Piece->SetStaticMesh(Mesh);
		Piece->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Piece->SetCastShadow(true);
		Piece->SetupAttachment(RootComponent);
		Piece->RegisterComponent();
		Piece->SetWorldTransform(FTransform(FRotator(0.f, Yaw, 0.f),
			Where, FVector::OneVector));
		HallInteriorPieces.Add(Piece);
	};

	const FVector HallAt = Hall->WorldTransform.GetLocation();
	const FVector2D Floor = HallDefinition->InteriorFloorCm;
	// A stockpile stands beside each station, on the WEST flank, where
	// the delivery drones come in from the dock.
	for (int32 Index = 0; Index < LineStations.Num(); ++Index)
	{
		const FVector StationAt =
			LineStations[Index]->WorldTransform.GetLocation();
		// Hard against the station's west flank: the parts a station
		// fits wait AT that station (the owner's Production Line
		// model), so the rack has to read as belonging to it rather
		// than standing about on the floor nearby.
		// NO STOCKPILE RACK AT THE STATION (owner 2026-08-29, the
		// second of the two objects). The station still HAS a
		// stockpile store and the haulers still fill it - this removes
		// the prop that stood for it, not the supply chain.
		(void)StationAt;
		(void)Stockpile;
	}
	// ---- THE SHELL: walls, trusses, lights ----
	//
	// The hall had a door, a crane, a column and a rack in it and
	// nothing else, so the factory read as a line of machines standing
	// on an infinite plane - which is what a blockout looks like. Close
	// frames of the same factory look fine; it was the empty volume
	// around them that was wrong.
	//
	// NO ROOF DECK, deliberately. The camera is fixed near-isometric at
	// pitch -35, so a ceiling would fill the top of every frame and
	// hide the factory under it. Open trusses read as "indoors" from
	// below while the floor stays visible between the members.
	// NESTED PATH, and it says so when it fails. Interchange puts each
	// import in its own <Name>/StaticMeshes/ folder; the four meshes
	// that were here before predate that and sit flat. The first build
	// of this shell used the flat loader, got null for all three
	// pieces, and drew a hall with no walls - looking exactly like the
	// problem it was written to fix. A null mesh here is a silent
	// nothing, so it is now a warning.
	auto LoadShell = [](const TCHAR* Name) -> UStaticMesh*
	{
		UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr,
			*FString::Printf(TEXT("/Game/LineBoss/Candidates/Spacecraft/")
				TEXT("ShipFactoryInterior_v001/%s/StaticMeshes/%s.%s"),
				Name, Name, Name));
		if (Mesh == nullptr)
		{
			UE_LOG(LogLBSpacecraftPresenter, Warning,
				TEXT("SPACECRAFT PRESENTER: hall shell piece %s did not "
					"load - the hall draws without it"), Name);
		}
		return Mesh;
	};
	auto ShellInstances = [this](const TCHAR* Key, UStaticMesh* Mesh,
		UInstancedStaticMeshComponent*& Slot)
	{
		if (Slot != nullptr)
		{
			Slot->DestroyComponent();
			Slot = nullptr;
		}
		if (Mesh == nullptr)
		{
			return;
		}
		Slot = NewObject<UInstancedStaticMeshComponent>(this,
			UInstancedStaticMeshComponent::StaticClass(), FName(Key));
		Slot->SetStaticMesh(Mesh);
		Slot->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Slot->SetCastShadow(true);
		Slot->SetupAttachment(RootComponent);
		Slot->RegisterComponent();
	};
	UInstancedStaticMeshComponent* Walls = nullptr;
	UInstancedStaticMeshComponent* Trusses = nullptr;
	UInstancedStaticMeshComponent* Lights = nullptr;
	ShellInstances(TEXT("HallWalls"), LoadShell(TEXT("SM_LB_IN_WallBay")),
		Walls);
	ShellInstances(TEXT("HallTrusses"),
		LoadShell(TEXT("SM_LB_IN_RoofTruss")), Trusses);
	ShellInstances(TEXT("HallLights"),
		LoadShell(TEXT("SM_LB_IN_BayLight")), Lights);
	HallWallInstances = Walls;
	HallTrussInstances = Trusses;
	HallLightInstances = Lights;
	if (Walls != nullptr)
	{
		// A 6 m bay, laid round all four sides. The bay's origin is its
		// centre on the floor, so the walk is just a step of 600 cm.
		constexpr float BayCm = 600.f;
		const float HalfX = Floor.X * 0.5f;
		const float HalfY = Floor.Y * 0.5f;
		const int32 BaysX = FMath::Max(FMath::RoundToInt(Floor.X / BayCm), 1);
		const int32 BaysY = FMath::Max(FMath::RoundToInt(Floor.Y / BayCm), 1);
		for (int32 Index = 0; Index < BaysX; ++Index)
		{
			const float X = HallAt.X - HalfX + BayCm * (Index + 0.5f);
			Walls->AddInstance(FTransform(FRotator::ZeroRotator,
				FVector(X, HallAt.Y - HalfY, 0.f)), true);
			Walls->AddInstance(FTransform(FRotator(0.f, 180.f, 0.f),
				FVector(X, HallAt.Y + HalfY, 0.f)), true);
		}
		for (int32 Index = 0; Index < BaysY; ++Index)
		{
			const float Y = HallAt.Y - HalfY + BayCm * (Index + 0.5f);
			Walls->AddInstance(FTransform(FRotator(0.f, 90.f, 0.f),
				FVector(HallAt.X - HalfX, Y, 0.f)), true);
			Walls->AddInstance(FTransform(FRotator(0.f, -90.f, 0.f),
				FVector(HallAt.X + HalfX, Y, 0.f)), true);
		}
	}
	// Trusses cross the line rather than tiling the whole 180 m roof:
	// structure over the part of the floor the camera actually holds,
	// and none over the empty acreage nobody looks at.
	// DOLLHOUSE (owner + research, 2026-09-01): the benchmarks are
	// roofless - the camera looks straight into a lit interior, and the
	// truss/purlin lattice read as pure clutter over the line from the
	// management angle (owner's live frame confirmed it). The roof
	// structure is cut, not hidden: sun and sky light the floor. Walls
	// stay - they draw the room's boundary without blocking the view.
	Trusses = nullptr;
	Lights = nullptr;
	// PHASE E, FILL THE FRAME (look plan, 2026-09-02). The hall is 260 m
	// by 180 m and the entry frame covers the middle 120 m, so anything
	// on the walls is off screen; the fill has to live BESIDE THE LINE.
	// Behind each station (far side, past the tower) a run of PALLET
	// RACKS; in front, further out so a 3 m rack never covers the pad
	// from a camera pitched 35 degrees, a second run; and LIGHT BARS
	// hang in a row behind the line at 9 m, where they sit above the
	// craft on screen and never between the camera and it. All three
	// are Meshy models from the same day's commission; absent, the
	// hall draws without them.
	{
		UInstancedStaticMeshComponent* Racks = nullptr;
		ShellInstances(TEXT("HallRacks"),
			TryGetStationMesh(FName(TEXT("Hall.WallRack"))), Racks);
		UInstancedStaticMeshComponent* Bars = nullptr;
		ShellInstances(TEXT("HallLightBars"),
			TryGetStationMesh(FName(TEXT("Hall.LightBar"))), Bars);
		if (LineStations.Num() > 0 && (Racks != nullptr || Bars != nullptr))
		{
			float MinY = TNumericLimits<float>::Max();
			float MaxY = TNumericLimits<float>::Lowest();
			float AxisX = 0.f;
			for (const FLBSpacecraftStationRecord* Line : LineStations)
			{
				const FVector At = Line->WorldTransform.GetLocation();
				MinY = FMath::Min(MinY, At.Y);
				MaxY = FMath::Max(MaxY, At.Y);
				AxisX = At.X;
			}
			// Racks run along the line every 6.4 m, 6 m long each.
			for (float Y = MinY - 400.f; Y <= MaxY + 400.f; Y += 640.f)
			{
				if (Racks != nullptr)
				{
					Racks->AddInstance(FTransform(FRotator(0.f, 90.f, 0.f),
						FVector(AxisX + 2100.f, Y, 0.f)), true);
					Racks->AddInstance(FTransform(FRotator(0.f, -90.f, 0.f),
						FVector(AxisX - 2600.f, Y, 0.f)), true);
				}
			}
			// The light bars hang OVER THE LINE at 11.5 m, every 18 m.
			// From a camera pitched 35 degrees a bar that high projects
			// 16 m behind the line on screen, above the far racks, so
			// it never covers the craft; a bar over the far flank at 9 m
			// was the first thing in front of anything the player
			// looked at on that side (frame, 2026-09-02).
			for (float Y = MinY; Y <= MaxY + 200.f; Y += 1800.f)
			{
				if (Bars != nullptr)
				{
					Bars->AddInstance(FTransform(FRotator(0.f, 90.f, 0.f),
						FVector(AxisX, Y, 1150.f)), true);
				}
			}
		}
		// Graphite on a dark floor merges (frame, 2026-09-02): the racks
		// take Crate.Tan - they are crates on frames - and the light
		// bars the working-indicator white, the closest a non-emissive
		// surface gets to reading lit under the locked exposure.
		auto Tint = [](UInstancedStaticMeshComponent* Piece,
			const FLinearColor& Tone)
		{
			if (Piece == nullptr)
			{
				return;
			}
			if (UMaterialInterface* Base = Piece->GetMaterial(0))
			{
				UMaterialInstanceDynamic* Tinted =
					UMaterialInstanceDynamic::Create(Base, Piece);
				Tinted->SetVectorParameterValue(TEXT("BaseTint"), Tone);
				for (int32 Slot = 0; Slot < Piece->GetNumMaterials(); ++Slot)
				{
					Piece->SetMaterial(Slot, Tinted);
				}
			}
		};
		Tint(Racks, LBSpacecraftPalette::CrateTan);
		Tint(Bars, LBSpacecraftPalette::IndicatorWorking);
		if (Racks != nullptr)
		{
			HallInteriorPieces.Add(Racks);
		}
		if (Bars != nullptr)
		{
			HallInteriorPieces.Add(Bars);
		}
	}
	if (Trusses != nullptr && LineStations.Num() > 0)
	{
		constexpr float TrussHeightCm = 1240.f;
		constexpr float TrussStepCm = 1200.f;
		float MinY = TNumericLimits<float>::Max();
		float MaxY = TNumericLimits<float>::Lowest();
		for (const FLBSpacecraftStationRecord* Station : LineStations)
		{
			const float Y = Station->WorldTransform.GetLocation().Y;
			MinY = FMath::Min(MinY, Y);
			MaxY = FMath::Max(MaxY, Y);
		}
		MinY -= 2400.f;
		MaxY += 2400.f;
		const int32 Count = FMath::Max(
			FMath::RoundToInt((MaxY - MinY) / TrussStepCm), 1);
		for (int32 Index = 0; Index <= Count; ++Index)
		{
			const float Y = MinY + Index * TrussStepCm;
			Trusses->AddInstance(FTransform(FRotator::ZeroRotator,
				FVector(HallAt.X, Y, TrussHeightCm)), true);
			if (Lights != nullptr && (Index % 2) == 0)
			{
				Lights->AddInstance(FTransform(FRotator(0.f, 90.f, 0.f),
					FVector(HallAt.X, Y, TrussHeightCm - 180.f)), true);
			}
		}
		// AND THE RUNS THAT CROSS THEM. Trusses alone span X, which is
		// the axis running INTO this camera: a whole 18 m truss seen
		// end-on is a 28 cm stub behind a machine, and twelve of them
		// were invisible in the frame while the log happily reported
		// twelve placed. A roof reads as a GRID, so purlins run along
		// the line as well - honest structure, and the half of it that
		// the camera can actually see.
		constexpr float PurlinHeightCm = TrussHeightCm - 40.f;
		for (int32 Lane = -1; Lane <= 1; ++Lane)
		{
			const float X = HallAt.X + Lane * 600.f;
			for (float Y = MinY; Y <= MaxY; Y += 1800.f)
			{
				Trusses->AddInstance(FTransform(FRotator(0.f, 90.f, 0.f),
					FVector(X, Y + 900.f, PurlinHeightCm)), true);
			}
		}
	}
	UE_LOG(LogLBSpacecraftPresenter, Display,
		TEXT("SPACECRAFT PRESENTER: hall shell walls=%d trusses=%d "
			"lights=%d hallAt=%s floor=%.0fx%.0f stations=%d"),
		Walls != nullptr ? Walls->GetInstanceCount() : -1,
		Trusses != nullptr ? Trusses->GetInstanceCount() : -1,
		Lights != nullptr ? Lights->GetInstanceCount() : -1,
		*HallAt.ToCompactString(), Floor.X, Floor.Y, LineStations.Num());
	// ---- FILLING THE FLOOR ----
	//
	// The hall is 180 m square and the starting line uses about
	// 110 x 40 of it, so six sevenths of the frame is bare pale
	// concrete. The catalogue comment beside InteriorFloorCm already
	// diagnosed this and named the two cures: fill it, or start the
	// player somewhere smaller. SHRINKING IS NOT AVAILABLE - it is a
	// budgeted decision with both smaller sizes already tried and
	// recorded as failures (Y=14000 left the spray booth 300 cm short,
	// X=12000 refused every Mk2 station of a second parallel line). So
	// this fills it.
	//
	// It fills it with FLOOR, not furniture. Both reference games break
	// open ground with painted zones and lane markings rather than
	// clutter, and the site picture outside uses exactly this language
	// - marked bays, guide lines, hazard edging - so bringing it inside
	// makes the two screens read as one place.
	auto Flat = [this](const TCHAR* Key, int32 Index,
		const FLinearColor& Tone, const FVector& Centre,
		const FVector& Span)
	{
		if (UStaticMeshComponent* Block = MakeBlockComponent(
			FName(*FString::Printf(TEXT("HallFloor_%s_%d"), Key, Index)),
			Tone))
		{
			Block->SetWorldTransform(FTransform(FRotator::ZeroRotator,
				Centre, Span * 0.01f));
			HallInteriorPieces.Add(Block);
		}
	};
	{
		// ZONES, NOT PINSTRIPES. The first attempt drew dashed lane
		// lines and thin bay outlines, and from the play camera they
		// were invisible - the floor looked exactly as bare as before.
		// The same lesson the station markings already record, one
		// scale up: a 16 cm pinstripe reads as nothing, so the hazard
		// bands became 70 cm. Here the unit is not a line at all but a
		// painted AREA, because what is being fixed is acres of empty
		// tone rather than a missing edge.
		// LIFTED TWICE. At 4-6 cm nothing appeared at any contrast; at
		// 14-18 cm the thin hazard lines appeared but the big zone
		// slabs still did not, which put the hall floor's own surface
		// between the two - so the paint sits at 22-30 cm now. It is
		// still flush from a camera 40 m up, and the lesson is that
		// "invisible" was never a contrast problem: the blocks were
		// created, registered and transformed correctly throughout,
		// and simply buried.
		//
		// ORIGINALLY LIFTED CLEAR OF THE FLOOR. The first two attempts drew these
		// at z=4..6 cm and NOTHING appeared, at any contrast - the
		// diagnostic pass used near-black and the floor stayed pale.
		// The blocks were being created, registered and transformed
		// correctly the whole time; they were simply UNDER the hall
		// floor surface. Zone paint now sits at 14-18 cm, which is
		// still flush from the play camera and unambiguously above.
		// TONED BACK from the diagnostic near-black once the blocks were
		// proven to render. These sit a little under the floor's own
		// concrete so the zones read as swept, worked areas rather than
		// as grey paint - the governing palette rule still applies, and
		// no world surface may be both bright and saturated.
		// Phase A: the zones sit a step above the dark slab, and the
		// traffic lanes at the ends are PAINTED PALE - a walkway reads
		// as paint on dark concrete, never as a lighter grey on grey.
		const FLinearColor ZoneStorage =
			LBSpacecraftWIPPresentationPrivate::SpacecraftFloorZone;
		const FLinearColor ZoneStaging =
			LBSpacecraftWIPPresentationPrivate::SpacecraftFloorZone;
		const FLinearColor ZoneTraffic = LBSpacecraftPalette::FloorConcrete;
		const FLinearColor HazardTone(0.79f, 0.63f, 0.11f);
		const float HalfX = Floor.X * 0.5f;
		const float HalfY = Floor.Y * 0.5f;

		// A CLEAN SLAB OVER THE AUTHORED FLOOR (owner 2026-09-01 "and
		// the yellow lines?"): the kept hall interior mesh carries its
		// own baked lane markings, which cross under the free-laid
		// track meaning nothing and cannot be removed from code. One
		// palette-concrete slab masks all of it and gives the floor a
		// single controlled surface; the zone paint above (22-30 cm)
		// still reads.
		Flat(TEXT("CleanSlab"), 0,
			LBSpacecraftWIPPresentationPrivate::SpacecraftFloorDark,
			FVector(HallAt.X, HallAt.Y, 14.f),
			FVector(Floor.X - 80.f, Floor.Y - 80.f, 4.f));

		// The storage half of the hall, west of the line.
		// A LANE GRID every 10 m (Car Manufacture's floor language: dark
		// concrete with painted lines). Thin but not a pinstripe: 16 cm
		// at this camera reads; the earlier 4-6 cm attempts did not.
		{
			using namespace LBSpacecraftWIPPresentationPrivate;
			int32 Line = 0;
			for (float X = -HalfX + 1000.f; X < HalfX - 500.f; X += 1000.f)
			{
				Flat(TEXT("LaneX"), Line++, SpacecraftFloorLine,
					FVector(HallAt.X + X, HallAt.Y, 18.f),
					FVector(16.f, Floor.Y - 160.f, 2.f));
			}
			for (float Y = -HalfY + 1000.f; Y < HalfY - 500.f; Y += 1000.f)
			{
				Flat(TEXT("LaneY"), Line++, SpacecraftFloorLine,
					FVector(HallAt.X, HallAt.Y + Y, 18.f),
					FVector(Floor.X - 160.f, 16.f, 2.f));
			}
		}
		Flat(TEXT("ZoneStorage"), 0, ZoneStorage,
			FVector(HallAt.X - HalfX + 3600.f, HallAt.Y, 22.f),
			FVector(6400.f, Floor.Y - 2400.f, 6.f));
		// The staging strip east of the line, where finished work and
		// inbound kit stand.
		Flat(TEXT("ZoneStaging"), 0, ZoneStaging,
			FVector(HallAt.X + HalfX - 3600.f, HallAt.Y, 22.f),
			FVector(6400.f, Floor.Y - 2400.f, 6.f));
		// A traffic corridor across each end, joining the two.
		for (int32 End = 0; End < 2; ++End)
		{
			const float Sign = End == 0 ? -1.f : 1.f;
			Flat(TEXT("ZoneTraffic"), End, ZoneTraffic,
				FVector(HallAt.X, HallAt.Y + Sign * (HalfY - 2200.f), 22.f),
				FVector(Floor.X - 2400.f, 2600.f, 6.f));
		}
		// BAY DIVIDER LINES CUT (owner 2026-09-01 "and the yellow
		// lines?"): they were drawn for the fixed starter line, and
		// with free track laying they cross under whatever the player
		// builds - loud paint that means nothing. The rack rows mark
		// the bays by themselves; hazard paint now only appears where
		// it states a rule (wall perimeter, station pads, dock apron).
		// HAZARD EDGING where the floor meets the wall, which is what
		// stops the far corners reading as unfinished ground.
		for (int32 Side = 0; Side < 2; ++Side)
		{
			const float Sign = Side == 0 ? -1.f : 1.f;
			Flat(TEXT("EdgeX"), Side, HazardTone,
				FVector(HallAt.X + Sign * (HalfX - 260.f), HallAt.Y, 30.f),
				FVector(150.f, Floor.Y - 520.f, 3.f));
			Flat(TEXT("EdgeY"), Side, HazardTone,
				FVector(HallAt.X, HallAt.Y + Sign * (HalfY - 260.f), 30.f),
				FVector(Floor.X - 520.f, 150.f, 3.f));
		}
	}
	// STORAGE RACKS ALONG THE WEST WALL. They used to stand one per
	// station until the owner had them removed from the stations
	// (2026-08-29); the racks themselves were never the problem, their
	// place was. Storage belongs in a storage zone - dock, then
	// storage, then stations - so they stand in the marked bays.
	if (Stockpile != nullptr)
	{
		for (int32 Rank = 0; Rank < 2; ++Rank)
		{
			for (int32 Bay = 0; Bay < 7; ++Bay)
			{
				const float Y = HallAt.Y - Floor.Y * 0.5f + 1900.f
					+ Bay * ((Floor.Y - 3800.f) / 6.f);
				const float X = HallAt.X - Floor.X * 0.5f + 2200.f
					+ Rank * 2600.f;
				Place(Stockpile,
					FName(*FString::Printf(TEXT("HallStore_%d_%d"),
						Rank, Bay)),
					FVector(X, Y, 0.f), 0.f);
			}
		}
	}
	// Columns down both flanks, clear of the line itself.
	for (int32 Index = 0; Index < 6; ++Index)
	{
		const float Along = HallAt.Y - Floor.Y * 0.5f + 1800.f
			+ Index * ((Floor.Y - 3600.f) / 5.f);
		Place(Column, FName(*FString::Printf(TEXT("HallColumnW_%d"),
			Index)),
			FVector(HallAt.X - Floor.X * 0.5f + 1200.f, Along, 0.f), 0.f);
		Place(Column, FName(*FString::Printf(TEXT("HallColumnE_%d"),
			Index)),
			FVector(HallAt.X + Floor.X * 0.5f - 1200.f, Along, 0.f), 0.f);
	}
	// HOW MANY CRANES IS AN OPEN QUESTION (owner 2026-08-29). He asked
	// for "one gantry crane between each station", then handed the
	// choice back - "1 crane does all work, will have to test each" - so
	// this builds either and lets the two be compared in play rather
	// than argued about.
	//
	//   LB.Spacecraft.CranePerGap 1  - N stations, N-1 cranes, every
	//                                  station hands forward at once
	//   LB.Spacecraft.CranePerGap 0  - one crane, a queue of trips and
	//                                  therefore a real upgrade axis
	//
	// The RAILS are one continuous full-length pair either way. That
	// part he did specify, and it holds for both.
	//
	// NO STATIONS, NO CRANE (owner 2026-09-01: "and the crane is
	// already there" - a fresh empty hall was spawning one crane and a
	// 60 m rail at Y=0 because the empty StationYs degraded to MeanY=0
	// instead of skipping). The crane exists to move craft BETWEEN
	// stations; an empty floor has nothing to serve. The resets stay
	// outside the guard so TickHallCrane never drives a component the
	// skipped rebuild destroyed.
	HallCranes.Reset();
	HallCraneParkCm.Reset();
	HallCraneAxisAlongY.Reset();
	HallCrane = nullptr;
	// RAILS FOLLOW THE LINE (owner 2026-09-01: "if i place a station at
	// the top the crane isnt over it" - the old rig was one hall-centre
	// column, correct only for the fixed starter line). The laid track
	// is grouped into maximal straight LEGS; every leg that carries a
	// station gets its own tiled rail run and its own portal(s), yawed
	// to the leg's axis. No track or no stations means no cranes.
	if (LineStations.Num() > 0 && TrackAuthority != nullptr)
	{
		struct FLBHallCraneLeg
		{
			bool bAlongY = true;
			float CrossCm = 0.f;
			float MinAlongCm = 0.f;
			float MaxAlongCm = 0.f;
			TArray<float> StationAlongCm;
		};
		TArray<FLBHallCraneLeg> Legs;
		{
			FLBHallCraneLeg Current;
			bool bOpen = false;
			const auto CloseLeg = [&Legs, &Current, &bOpen]()
			{
				if (bOpen && Current.StationAlongCm.Num() > 0)
				{
					Legs.Add(Current);
				}
				bOpen = false;
			};
			for (const FLBSpacecraftTrackPieceRecord& Piece :
				TrackAuthority->GetPieces())
			{
				const bool bStraightKind = Piece.PieceType
						== ELBSpacecraftTrackPiece::Straight
					|| Piece.PieceType == ELBSpacecraftTrackPiece::Start
					|| Piece.PieceType == ELBSpacecraftTrackPiece::End;
				if (!bStraightKind)
				{
					// A corner ends its leg; collinear legs on either
					// side of a U stay separate runs, as their rails do.
					CloseLeg();
					continue;
				}
				const FVector At = Piece.WorldTransform.GetLocation();
				const float Yaw = Piece.WorldTransform.Rotator().Yaw;
				const bool bAlongY = FMath::Abs(FMath::Fmod(
					FMath::Abs(Yaw), 180.f) - 90.f) < 45.f;
				const float Cross = bAlongY ? At.X : At.Y;
				const float Along = bAlongY ? At.Y : At.X;
				if (!bOpen || Current.bAlongY != bAlongY
					|| !FMath::IsNearlyEqual(Current.CrossCm, Cross, 1.f))
				{
					CloseLeg();
					Current = FLBHallCraneLeg();
					Current.bAlongY = bAlongY;
					Current.CrossCm = Cross;
					Current.MinAlongCm = Along;
					Current.MaxAlongCm = Along;
					bOpen = true;
				}
				Current.MinAlongCm = FMath::Min(Current.MinAlongCm, Along);
				Current.MaxAlongCm = FMath::Max(Current.MaxAlongCm, Along);
				if (!Piece.NodeStationId.IsNone())
				{
					Current.StationAlongCm.Add(Along);
				}
			}
			CloseLeg();
		}
		// AS MANY CRANES AS THE PLAYER OWNS (PULSE_LINE_DESIGN_v001,
		// 2026-09-02). The hall comes with one; each bought crane
		// lets one more craft move per crane trip of a pulse, up to
		// one per gap. The count is the build authority's, so what is
		// drawn on the rails is exactly what the simulation is moving
		// craft with. The old LB.Spacecraft.CranePerGap cvar is gone:
		// the comparison the owner asked for (2026-08-29, "1 crane
		// does all work, will have to test each") is now made by
		// buying cranes in the BUILD tab.
		const int32 OwnedCranes = BuildAuthority != nullptr
			? BuildAuthority->GetCraneCount() : 1;
		int32 CraneIndex = 0;
		for (int32 LegIndex = 0; LegIndex < Legs.Num(); ++LegIndex)
		{
			const FLBHallCraneLeg& Leg = Legs[LegIndex];
			// The v002 gantry set is modelled with its run on X and its
			// gauge on Y, so a Y-running leg wears the quarter turn.
			const float LegYaw = Leg.bAlongY ? 90.f : 0.f;
			const auto LegPoint = [&Leg](float Along, float Z)
			{
				return Leg.bAlongY
					? FVector(Leg.CrossCm, Along, Z)
					: FVector(Along, Leg.CrossCm, Z);
			};
			// Rails TILED over the leg with clearance past each end so
			// a crane can stand clear while the next one works.
			{
				constexpr float RailPieceCm = 6000.f;
				constexpr float RailMarginCm = 1600.f;
				const float NeededCm =
					(Leg.MaxAlongCm - Leg.MinAlongCm) + RailMarginCm * 2.f;
				const float CentreAlong =
					(Leg.MinAlongCm + Leg.MaxAlongCm) * 0.5f;
				const int32 Pieces = FMath::Max(1,
					FMath::CeilToInt(NeededCm / RailPieceCm));
				const float FirstAlong = CentreAlong
					- (Pieces - 1) * RailPieceCm * 0.5f;
				for (int32 Piece = 0; Piece < Pieces; ++Piece)
				{
					const int32 BeforeRail = HallInteriorPieces.Num();
					Place(CraneRails, FName(*FString::Printf(
						TEXT("HallCraneRails_%d_%d"), LegIndex, Piece)),
						LegPoint(FirstAlong + Piece * RailPieceCm, 0.f),
						LegYaw);
					// The rail GAUGE narrows with the portal span (the
					// legs must land on their rails) - same native-Y
					// scale as the portal below.
					if (HallInteriorPieces.Num() > BeforeRail)
					{
						UStaticMeshComponent* Rail =
							HallInteriorPieces.Last();
						FVector RailScale = Rail->GetRelativeScale3D();
						RailScale.Y *= 0.42f;
						Rail->SetRelativeScale3D(RailScale);
					}
				}
			}
			// The owned cranes spread along the leg: one per gap when
			// there are enough, otherwise evenly over the gaps, and a
			// single crane parks at the leg's middle.
			TArray<float> Parks;
			TArray<float> Stations = Leg.StationAlongCm;
			Stations.Sort();
			TArray<float> GapParks;
			for (int32 Gap = 0; Gap + 1 < Stations.Num(); ++Gap)
			{
				GapParks.Add((Stations[Gap] + Stations[Gap + 1]) * 0.5f);
			}
			if (GapParks.Num() > 0 && OwnedCranes >= GapParks.Num())
			{
				Parks = GapParks;
			}
			else if (GapParks.Num() > 1 && OwnedCranes > 1)
			{
				for (int32 Index = 0; Index < OwnedCranes; ++Index)
				{
					Parks.Add(GapParks[FMath::Clamp(
						(Index * GapParks.Num() + GapParks.Num() / 2)
							/ OwnedCranes,
						0, GapParks.Num() - 1)]);
				}
			}
			else
			{
				float Mean = 0.f;
				for (const float Along : Stations)
				{
					Mean += Along;
				}
				Parks.Add(Mean / FMath::Max(Stations.Num(), 1));
			}
			for (const float Park : Parks)
			{
				// COUNTED BEFORE AND AFTER, not "take the last piece".
				// Place is a no-op on a missing mesh, so grabbing the
				// last entry blind would hand TickHallCrane whatever
				// went down previously - the rails.
				const int32 BeforeCrane = HallInteriorPieces.Num();
				Place(Crane, FName(*FString::Printf(TEXT("HallCrane_%d"),
					CraneIndex)), LegPoint(Park, 0.f), LegYaw);
				if (HallInteriorPieces.Num() <= BeforeCrane)
				{
					continue;
				}
				UStaticMeshComponent* Portal = HallInteriorPieces.Last();
				// HUG THE LINE (owner 2026-09-01 "cranes only go
				// across"): the authored portal spans 31.5 m - sized
				// for the old multi-line bay - so over a single leg it
				// reached twelve metres of empty floor each side and
				// read as a bridge across the hall, not a crane over
				// the line. Scaled on the mesh's native span axis (its
				// local Y; the yaw has already turned the component)
				// to shoulder the stations instead.
				constexpr float PortalSpanScale = 0.42f;
				{
					FVector PortalScale = Portal->GetRelativeScale3D();
					PortalScale.Y *= PortalSpanScale;
					Portal->SetRelativeScale3D(PortalScale);
				}
				HallCranes.Add(Portal);
				HallCraneParkCm.Add(LegPoint(Park, 0.f));
				HallCraneAxisAlongY.Add(Leg.bAlongY);
				if (HallCranes.Num() == 1)
				{
					// The first is the one TickHallCrane drives until a
					// craft picks a nearer one.
					HallCrane = Portal;
					HallCraneParkAtCm = LegPoint(Park, 0.f);
					bHallCraneAxisAlongY = Leg.bAlongY;
				}
				// THE TROLLEY AND HOIST RIDE THE PORTAL, so they are
				// ATTACHED rather than placed loose - anything merely
				// standing at the same coordinate is left behind the
				// moment the crane travels.
				const int32 BeforeRig = HallInteriorPieces.Num();
				Place(CraneTrolley, FName(*FString::Printf(
					TEXT("HallCraneTrolley_%d"), CraneIndex)),
					LegPoint(Park, 0.f), LegYaw);
				// IDLE POSITION IS RAISED (owner, 2026-09-01: "the
				// crane has something hanging from it that's always
				// there"): stowed hoist, dropped only when the carry
				// animation lands.
				const float HoistRaiseCm = CraneHoist != nullptr
					? CraneHoist->GetBounds().BoxExtent.Z * 2.f * 0.7f
					: 0.f;
				Place(CraneHoist, FName(*FString::Printf(
					TEXT("HallCraneHoist_%d"), CraneIndex)),
					LegPoint(Park, HoistRaiseCm), LegYaw);
				for (int32 Rig = BeforeRig;
					Rig < HallInteriorPieces.Num(); ++Rig)
				{
					HallInteriorPieces[Rig]->AttachToComponent(Portal,
						FAttachmentTransformRules::KeepWorldTransform);
				}
				++CraneIndex;
			}
		}
	}
	// The dispatch door at the runway (+X) end of the hall.
	Place(Door, FName(TEXT("HallDispatchDoor")),
		FVector(HallAt.X + Floor.X * 0.5f - 300.f, HallAt.Y, 0.f), 90.f);

	// ---- THE BUILDING BRINGS ITS OWN FLOOR ----
	//
	// The site is GROUND now, so a hall standing on it needs concrete of
	// its own or the player would be working on open dirt. This is the
	// indoor half of that split, and it belongs on the building for the
	// same reason its walls and door do: the hall brings its surfaces
	// with it. RefreshSiteDressing cannot do it - it runs once, behind a
	// latch, before any building exists.
	{
		const FLinearColor SlabTone =
			LBSpacecraftWIPPresentationPrivate::SpacecraftFloorDark; // interior slab, phase A
		const FName SlabKey(*FString::Printf(TEXT("HallSlab_%s"),
			*Hall->StationId.ToString()));
		if (UStaticMeshComponent* Slab =
			MakeBlockComponent(SlabKey, SlabTone))
		{
			// One slab rather than a tile grid: it is a single flat
			// surface under everything, and 3600 more instances to draw
			// the same rectangle would be waste.
			Slab->SetWorldTransform(FTransform(FRotator::ZeroRotator,
				FVector(HallAt.X, HallAt.Y, 6.f),
				FVector(Floor.X / 100.f, Floor.Y / 100.f, 0.10f)));
			HallInteriorPieces.Add(Slab);
		}
		// THE SITE'S PAVING STOPS AT THE HALL WALL. The site dressing
		// tiles the whole plot before any building exists, and its
		// tiles stand proud of this slab, so every phase A frame of the
		// interior was showing the OUTDOOR paving (the floor sample did
		// not move by one value when the slab's tone changed,
		// 2026-09-02). The tiles under the hall's footprint go, once;
		// the hall brings its own floor.
		if (SiteFloorTiles != nullptr)
		{
			TArray<int32> Under;
			const int32 Count = SiteFloorTiles->GetInstanceCount();
			for (int32 Index = 0; Index < Count; ++Index)
			{
				FTransform TileAt;
				if (SiteFloorTiles->GetInstanceTransform(Index, TileAt, true)
					&& FMath::Abs(TileAt.GetLocation().X - HallAt.X)
						< Floor.X * 0.5f
					&& FMath::Abs(TileAt.GetLocation().Y - HallAt.Y)
						< Floor.Y * 0.5f)
				{
					Under.Add(Index);
				}
			}
			if (Under.Num() > 0)
			{
				SiteFloorTiles->RemoveInstances(Under);
				UE_LOG(LogLBSpacecraftPresenter, Display,
					TEXT("SPACECRAFT PRESENTER: %d site tiles lifted from ")
					TEXT("under the hall"), Under.Num());
			}
		}
	}

	// ---- THE FLOOR IS MARKED OUT ----
	//
	// The hall is the right size (three attempts to shrink it were each
	// refused by a fixture defending something real), so its emptiness
	// is answered by FILLING. The camera looks down at 35 degrees, which
	// makes the floor most of the picture and marking it the highest
	// value thing that can go on it.
	//
	// ARCHITECTURE, NOT GAMEPLAY. No buildings are placed here. The site
	// opens empty and the player builds it; seeding objects to look busy
	// would fake the very thing the game is about. Markings belong to
	// the BUILDING, like its columns and its door.
	//
	// NO TEXT. A real floor carries bay numbers and lettering, and this
	// game can carry neither - it ships translated and bakes no words
	// into any texture.
	{
		// CONTRAST IS THE WHOLE JOB. The first pass painted the lanes
		// at 0.74 against a floor of almost exactly that value, and the
		// result was invisible - markings that cannot be seen are worse
		// than none, because they cost draw calls and buy nothing. The
		// lane now sits clearly DARKER than the floor and its edges are
		// full safety yellow.
		// CONTRAST IS THE WHOLE JOB. An earlier pass painted the lanes
		// at 0.74 against a floor of almost exactly that value; markings
		// that cannot be seen are worse than none, because they cost
		// draw calls and buy nothing.
		const FLinearColor KeepClear = LBSpacecraftPalette::Hazard; // keep-clear hatching

		auto Paint = [this](const TCHAR* Part, int32 Index,
			const FLinearColor& Tone, const FVector& Centre,
			const FVector2D& SizeCm, float HeightCm)
		{
			const FName Key(*FString::Printf(TEXT("HallPaint_%s_%d"),
				Part, Index));
			if (UStaticMeshComponent* Slab =
				MakeBlockComponent(Key, Tone))
			{
				// Proud of the floor by a couple of centimetres so it
				// never z-fights the floor tiles, and flat enough that
				// nothing can be walked into.
				// CLEAR OF THE FLOOR TILES. The first pass put these at
				// 3-5 cm and NOTHING RENDERED - not faint, absent. They
				// were under the floor. Tagging them magenta proved they
				// existed and were still invisible; lifting them 200 cm
				// made them blaze. The tiles' top sits above 5 cm, so
				// the paint starts at 12 - proud of the floor, and at
				// the game's zoom no height at all.
				//
				// 12 was still not enough - the paint came through in
				// broken dashes, which is z-fighting rather than
				// occlusion. 30 clears it outright. At a whole bay in
				// frame, 30 cm reads as flat paint.
				Slab->SetWorldTransform(FTransform(FRotator::ZeroRotator,
					Centre + FVector(0.f, 0.f, HeightCm + 30.f),
					FVector(SizeCm.X / 100.f, SizeCm.Y / 100.f, 0.04f)));
				HallInteriorPieces.Add(Slab);
			}
		};

		// WALKWAYS AND CROSS AISLES ARE GONE (owner 2026-09-01: "do we
		// need the walkways?" - no. NOTHING on this floor is handled
		// by people, so painted pedestrian lanes contradict the
		// fiction, and they were drawn for the old fixed line anyway:
		// with the free-form auto-connected track they crossed under
		// whatever the player built, which was the floor-clutter
		// complaint of the whole session. Paint survives only where it
		// states a machine rule: station pads, the dock apron, and the
		// dispatch keep-clear below.)

		// KEEP-CLEAR HATCHING at the dispatch door - the one patch of
		// floor a real plant always marks, because it is where something
		// large comes through.
		const float DoorX = HallAt.X + Floor.X * 0.5f - 300.f;
		for (int32 Bar = 0; Bar < 7; ++Bar)
		{
			const float Off = -1800.f + 600.f * static_cast<float>(Bar);
			Paint(TEXT("KeepClear"), Bar, KeepClear,
				FVector(DoorX - 900.f, HallAt.Y + Off, 0.f),
				FVector2D(1500.f, 180.f), 5.f);
		}
	}

	UE_LOG(LogTemp, Display,
		TEXT("LBHallInterior %d pieces for %d line stations"),
		HallInteriorPieces.Num(), LineStations.Num());
}

void ALBSpacecraftWIPPresentationActor::TickHallCrane(float DeltaSeconds)
{
	// EVERY CRANE HAS A JOB OR GOES HOME. A pulse with a crane per gap
	// lifts several craft in the same trip, so each craft in transit
	// claims the nearest crane nobody else has claimed; with a single
	// crane the craft go one after another and that crane does them
	// all. Before the pulse line one crane chased one carried craft
	// and the others stood still while their craft rose on nothing.
	const int32 CraneCount = HallCranes.Num();
	if (CraneCount == 0)
	{
		return;
	}
	TArray<int32> CraneJob;
	CraneJob.Init(INDEX_NONE, CraneCount);
	for (int32 Craft = 0; Craft < CarriedCraftsCm.Num(); ++Craft)
	{
		int32 Nearest = INDEX_NONE;
		float Best = TNumericLimits<float>::Max();
		for (int32 Index = 0; Index < CraneCount; ++Index)
		{
			if (CraneJob[Index] != INDEX_NONE || !HallCranes[Index].IsValid()
				|| !HallCraneParkCm.IsValidIndex(Index))
			{
				continue;
			}
			const float Distance = FVector::DistSquared2D(
				HallCraneParkCm[Index], CarriedCraftsCm[Craft]);
			if (Distance < Best)
			{
				Best = Distance;
				Nearest = Index;
			}
		}
		if (Nearest != INDEX_NONE)
		{
			CraneJob[Nearest] = Craft;
		}
	}

	// One hoist rig per crane, remade when the crane count changes
	// (the hall rebuild resets HallCranes; stale rigs would hang in
	// the air over cranes that no longer exist).
	if (HallCraneHoists.Num() != CraneCount * 3)
	{
		for (UStaticMeshComponent* Old : HallCraneHoists)
		{
			if (Old != nullptr)
			{
				Old->DestroyComponent();
			}
		}
		HallCraneHoists.Reset();
		// THE AMBER LIVES HERE, and only here on the crane: the hoist
		// is the one piece that moves, so it is the one piece that
		// earns the accent; the portal around it is structure and
		// stays graphite.
		const FLinearColor HoistTone = LBSpacecraftPalette::MachineAmber;
		const FLinearColor CableTone =
			LBSpacecraftPalette::StructureGraphiteDark;
		for (int32 Index = 0; Index < CraneCount; ++Index)
		{
			UStaticMeshComponent* Block = MakeBlockComponent(
				FName(*FString::Printf(TEXT("CraneHoistBlock_%d"), Index)),
				HoistTone);
			UStaticMeshComponent* CableA = MakeBlockComponent(
				FName(*FString::Printf(TEXT("CraneCable_%d_0"), Index)),
				CableTone);
			UStaticMeshComponent* CableB = MakeBlockComponent(
				FName(*FString::Printf(TEXT("CraneCable_%d_1"), Index)),
				CableTone);
			HallCraneHoists.Add(Block);
			HallCraneHoists.Add(CableA);
			HallCraneHoists.Add(CableB);
		}
	}

	if (HallCraneAudio.Num() != CraneCount)
	{
		for (UAudioComponent* Old : HallCraneAudio)
		{
			if (Old != nullptr)
			{
				Old->Stop();
				Old->DestroyComponent();
			}
		}
		HallCraneAudio.Init(nullptr, CraneCount);
		HallCraneWasBusy.Init(false, CraneCount);
	}
	for (int32 Index = 0; Index < CraneCount; ++Index)
	{
		UStaticMeshComponent* Crane = HallCranes[Index].Get();
		if (Crane == nullptr || !HallCraneParkCm.IsValidIndex(Index))
		{
			continue;
		}
		const bool bAlongY = HallCraneAxisAlongY.IsValidIndex(Index)
			? HallCraneAxisAlongY[Index] : true;
		const bool bBusy = CraneJob[Index] != INDEX_NONE;
		// THE CRANE IS HEARD: a travel loop while it has a job, a
		// set-down clunk when the job ends.
		if (bBusy && HallCraneAudio[Index] == nullptr)
		{
			if (USoundBase* Travel = SoundFor(FName(TEXT("CraneTravel"))))
			{
				HallCraneAudio[Index] =
					LBSpacecraftWIPPresentationPrivate::SpacecraftMakeRotorAudio(
						this, Crane, FName(*FString::Printf(
							TEXT("CraneTravelAudio_%d"), Index)),
						Travel, 2500.f, 6000.f);
			}
		}
		if (HallCraneAudio[Index] != nullptr)
		{
			if (bBusy && !HallCraneAudio[Index]->IsPlaying())
			{
				HallCraneAudio[Index]->Play();
			}
			else if (!bBusy && HallCraneAudio[Index]->IsPlaying())
			{
				HallCraneAudio[Index]->Stop();
			}
		}
		if (HallCraneWasBusy.IsValidIndex(Index)
			&& HallCraneWasBusy[Index] && !bBusy)
		{
			PlayWorldCue(FName(TEXT("CraneSetDown")),
				Crane->GetComponentLocation());
		}
		if (HallCraneWasBusy.IsValidIndex(Index))
		{
			HallCraneWasBusy[Index] = bBusy;
		}
		const FVector Load = bBusy
			? CarriedCraftsCm[CraneJob[Index]] : HallCraneParkCm[Index];
		// A GANTRY RUNS ON RAILS, so only the along-leg axis moves -
		// constant speed, not an ease: a gantry accelerates hard and
		// then runs flat, and an eased interp reads as floating.
		const FVector At = Crane->GetComponentLocation();
		FVector NewAt = At;
		if (bAlongY)
		{
			NewAt.Y = FMath::FInterpConstantTo(At.Y, Load.Y, DeltaSeconds,
				FMath::Max(CraneTravelSpeedCmS, 1.f));
		}
		else
		{
			NewAt.X = FMath::FInterpConstantTo(At.X, Load.X, DeltaSeconds,
				FMath::Max(CraneTravelSpeedCmS, 1.f));
		}
		Crane->SetWorldLocation(NewAt);
		if (Index == 0)
		{
			// Kept for anything that still reads the single-crane fields.
			HallCrane = HallCranes[Index];
			HallCraneParkAtCm = HallCraneParkCm[Index];
			bHallCraneAxisAlongY = bAlongY;
		}

		// The hoist: a block riding the beam with two cables down to
		// the load. The beam is near the top of the gantry's own bounds
		// rather than a hardcoded height, so a replacement crane mesh
		// does not leave the hoist hanging in mid-air. The trolley
		// slides ACROSS the beam toward the load, so the hook's
		// cross-axis coordinate is the craft's; the along-axis one is
		// the crane's own travel.
		const int32 Rig = Index * 3;
		if (!HallCraneHoists.IsValidIndex(Rig + 2)
			|| HallCraneHoists[Rig] == nullptr
			|| HallCraneHoists[Rig + 1] == nullptr
			|| HallCraneHoists[Rig + 2] == nullptr)
		{
			continue;
		}
		const float BeamZ = Crane->Bounds.Origin.Z
			+ Crane->Bounds.BoxExtent.Z * 0.62f;
		FVector Hook(NewAt.X, NewAt.Y, BeamZ - 220.f);
		if (bBusy)
		{
			Hook = bAlongY
				? FVector(Load.X, NewAt.Y, Load.Z + 210.f)
				: FVector(NewAt.X, Load.Y, Load.Z + 210.f);
		}
		HallCraneHoists[Rig]->SetWorldTransform(FTransform(
			FRotator::ZeroRotator, Hook, FVector(1.6f, 1.2f, 0.5f)));
		const float Drop = FMath::Max(BeamZ - Hook.Z, 10.f);
		for (int32 Cable = 0; Cable < 2; ++Cable)
		{
			const float Side = Cable == 0 ? -60.f : 60.f;
			HallCraneHoists[Rig + 1 + Cable]->SetWorldTransform(FTransform(
				FRotator::ZeroRotator,
				FVector(Hook.X + Side, Hook.Y, Hook.Z + Drop * 0.5f),
				FVector(0.08f, 0.08f, Drop / 100.f)));
		}
	}
}

USoundBase* ALBSpacecraftWIPPresentationActor::SoundFor(FName CueRole)
{
	if (TObjectPtr<USoundBase>* Known = SoundByRole.Find(CueRole))
	{
		return Known->Get();
	}
	// Loaded by path on first use. A missing wave is a silent cue, not
	// a crash, and it is logged once so the silence has a name.
	const FString Path = FString::Printf(
		TEXT("/Game/LineBoss/Audio/LB_%s_v001.LB_%s_v001"),
		*CueRole.ToString(), *CueRole.ToString());
	USoundBase* Sound = LoadObject<USoundBase>(nullptr, *Path);
	if (Sound == nullptr)
	{
		UE_LOG(LogTemp, Warning, TEXT("SOUND %s not found at %s"),
			*CueRole.ToString(), *Path);
	}
	SoundByRole.Add(CueRole, Sound);
	return Sound;
}

void ALBSpacecraftWIPPresentationActor::PlayWorldCue(FName CueRole,
	const FVector& AtCm)
{
	USoundBase* Sound = SoundFor(CueRole);
	if (Sound == nullptr)
	{
		return;
	}
	UGameplayStatics::PlaySoundAtLocation(this, Sound, AtCm);
	UE_LOG(LogTemp, Display, TEXT("SOUND %s at (%.0f, %.0f)"),
		*CueRole.ToString(), AtCm.X, AtCm.Y);
}

void ALBSpacecraftWIPPresentationActor::TickAudioCues(float DeltaSeconds)
{
	(void)DeltaSeconds;
	// ROOM TONE while the view is inside a building; the site map is
	// outdoors and quiet.
	const bool bInside = ShellViewPawn.IsValid()
		&& !ShellViewPawn->IsSiteMapView();
	if (bInside && HallAmbienceAudio == nullptr)
	{
		if (USoundBase* Ambience = SoundFor(FName(TEXT("HallAmbience"))))
		{
			HallAmbienceAudio = UGameplayStatics::CreateSound2D(this,
				Ambience, 0.6f, 1.f, 0.f, nullptr, /*bPersistAcrossLevelTransition=*/false,
				/*bAutoDestroy=*/false);
			if (HallAmbienceAudio != nullptr)
			{
				HallAmbienceAudio->Play();
				UE_LOG(LogTemp, Display, TEXT("SOUND HallAmbience on"));
			}
		}
	}
	else if (HallAmbienceAudio != nullptr)
	{
		if (bInside && !HallAmbienceAudio->IsPlaying())
		{
			HallAmbienceAudio->Play();
		}
		else if (!bInside && HallAmbienceAudio->IsPlaying())
		{
			HallAmbienceAudio->Stop();
			UE_LOG(LogTemp, Display, TEXT("SOUND HallAmbience off"));
		}
	}
	// A LORRY LANDS: the pending-order count dropped, so goods arrived
	// at the dock. The count is the authority's; the sound is ours.
	if (InventoryAuthority != nullptr)
	{
		const int32 Pending = InventoryAuthority->GetPendingOrders().Num();
		if (LastPendingOrderCount > Pending && BuildAuthority != nullptr)
		{
			FVector DockAt = FVector::ZeroVector;
			for (const FLBSpacecraftStationRecord& Record :
				BuildAuthority->GetStations())
			{
				if (Record.DefinitionId == FName(TEXT("DeliveryDock")))
				{
					DockAt = Record.WorldTransform.GetLocation();
					break;
				}
			}
			PlayWorldCue(FName(TEXT("LorryArrives")), DockAt);
		}
		LastPendingOrderCount = Pending;
	}
}

void ALBSpacecraftWIPPresentationActor::EnsureTileStudio()
{
	if (TileCapture != nullptr && TileSubject != nullptr)
	{
		return;
	}
	// Far below and beside the site: nothing else is drawn there, and
	// the capture uses a show-only list so nothing else could be.
	const FVector StudioAt(-600000.f, -600000.f, -80000.f);
	TileSubject = NewObject<UStaticMeshComponent>(this,
		UStaticMeshComponent::StaticClass(), TEXT("TileSubject"));
	TileSubject->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	TileSubject->SetCastShadow(false);
	TileSubject->SetupAttachment(RootComponent);
	TileSubject->SetRelativeLocation(StudioAt);
	TileSubject->RegisterComponent();
	// A GRAPHITE backdrop, not the panel tone: the pale housings and
	// white booth vanished against a pale ground (first tiles, same
	// day). Structure.Graphite #4A4D50 in linear.
	TileBackdrop = MakeBlockComponent(TEXT("TileBackdrop"),
		FLinearColor(0.068f, 0.075f, 0.082f));
	if (TileBackdrop != nullptr)
	{
		TileBackdrop->SetCastShadow(false);
		TileBackdrop->SetRelativeLocation(StudioAt + FVector(0.f, 0.f, -60.f));
		TileBackdrop->SetRelativeScale3D(FVector(400.f, 400.f, 1.f));
	}
	TileCapture = NewObject<USceneCaptureComponent2D>(this,
		USceneCaptureComponent2D::StaticClass(), TEXT("TileCapture"));
	TileCapture->SetupAttachment(RootComponent);
	TileCapture->RegisterComponent();
	TileCapture->bCaptureEveryFrame = false;
	TileCapture->bCaptureOnMovement = false;
	TileCapture->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
	TileCapture->PrimitiveRenderMode =
		ESceneCapturePrimitiveRenderMode::PRM_UseShowOnlyList;
	TileCapture->ShowOnlyComponents.Add(TileSubject);
	if (TileBackdrop != nullptr)
	{
		TileCapture->ShowOnlyComponents.Add(TileBackdrop);
	}
	TileCapture->FOVAngle = 28.f;
}

UTextureRenderTarget2D* ALBSpacecraftWIPPresentationActor::GetDefinitionTile(
	FName DefinitionId, const FLinearColor* Livery)
{
	const bool bPainted = Livery != nullptr
		&& DefinitionId == FName(TEXT("Craft.Chassis"));
	if (bPainted)
	{
		// One tile per livery, keyed by the colour.
		DefinitionId = FName(*FString::Printf(TEXT("Craft.Chassis#%s"),
			*Livery->ToFColor(true).ToHex()));
	}
	if (TObjectPtr<UTextureRenderTarget2D>* Known =
		DefinitionTiles.Find(DefinitionId))
	{
		return Known->Get();
	}
	// "Craft.Chassis" is the ship itself (the contract cards wear it);
	// everything else is a station definition.
	UStaticMesh* Mesh = nullptr;
	if (bPainted || DefinitionId == FName(TEXT("Craft.Chassis")))
	{
		// The Scout V2 hull - the mesh the line actually builds on -
		// not the gated placeholder chassis (blank card, 2026-09-02).
		UStaticMesh* Hull = nullptr; UStaticMesh* Propulsion = nullptr;
		UStaticMesh* Power = nullptr; UStaticMesh* Electronics = nullptr;
		UStaticMesh* Navigation = nullptr; UStaticMesh* Interior = nullptr;
		ResolveScoutV2Parts(Hull, Propulsion, Power, Electronics,
			Navigation, Interior);
		Mesh = Hull != nullptr ? Hull : ResolveChassisMesh();
	}
	else
	{
		Mesh = TryGetStationMesh(DefinitionId);
		if (Mesh == nullptr
			&& DefinitionId.ToString().StartsWith(TEXT("AssemblyRobot")))
		{
			// The fitting station's portal dress went by decision
			// (2026-09-02); its picture is the tool tower that stands
			// on it, so the build menu is not a blank tile.
			Mesh = TryGetStationMesh(FName(TEXT("Station.ToolTower")));
		}
	}
	if (Mesh == nullptr)
	{
		DefinitionTiles.Add(DefinitionId, nullptr);
		return nullptr;
	}
	EnsureTileStudio();
	if (TileCapture == nullptr || TileSubject == nullptr)
	{
		DefinitionTiles.Add(DefinitionId, nullptr);
		return nullptr;
	}
	UTextureRenderTarget2D* Target = NewObject<UTextureRenderTarget2D>(this);
	Target->RenderTargetFormat = ETextureRenderTargetFormat::RTF_RGBA8;
	Target->ClearColor = FLinearColor(0.068f, 0.075f, 0.082f, 1.f);
	Target->InitAutoFormat(352, 192);
	Target->UpdateResourceImmediate(true);
	// Handed back at once (the tile draws the backdrop until the shot
	// lands a couple of frames later), queued for the studio tick.
	DefinitionTiles.Add(DefinitionId, Target);
	FLBSpacecraftPendingTile Pending;
	Pending.DefinitionId = DefinitionId;
	Pending.Mesh = Mesh;
	Pending.Target = Target;
	Pending.bPainted = bPainted;
	if (bPainted)
	{
		Pending.Livery = *Livery;
	}
	PendingTiles.Add(Pending);
	return Target;
}

void ALBSpacecraftWIPPresentationActor::TickTileStudio()
{
	if (PendingTiles.Num() == 0 || TileCapture == nullptr
		|| TileSubject == nullptr)
	{
		return;
	}
	FLBSpacecraftPendingTile& Job = PendingTiles[0];
	if (Job.FramesPosed < 0)
	{
		// POSE. Sit the mesh on the backdrop, frame its bounds from a
		// three-quarter view slightly above: the same shot for every
		// tile so the menu reads as one set.
		TileSubject->SetStaticMesh(Job.Mesh);
		TileSubject->EmptyOverrideMaterials();
		if (Job.bPainted)
		{
			// The booth's own paint material, fully painted, in the
			// customer's colour - the same look the craft leaves in.
			if (UMaterialInterface* PaintBase =
				LoadObject<UMaterialInterface>(nullptr,
					LBSpacecraftWIPPresentationPrivate::SpacecraftPaintMaterialPath))
			{
				UMaterialInstanceDynamic* Paint =
					UMaterialInstanceDynamic::Create(PaintBase, TileSubject);
				Paint->SetVectorParameterValue(TEXT("PaintColor"), Job.Livery);
				Paint->SetScalarParameterValue(TEXT("PaintFrontX"), 1.0e9f);
				TileSubject->SetMaterial(0, Paint);
			}
		}
		TileSubject->SetRelativeScale3D(FVector(1.f));
		const FBoxSphereBounds Bounds = Job.Mesh->GetBounds();
		const FVector StudioAt(-600000.f, -600000.f, -80000.f);
		const FVector Centre = StudioAt + FVector(0.f, 0.f, Bounds.BoxExtent.Z);
		TileSubject->SetRelativeLocation(Centre - Bounds.Origin);
		const float Radius = FMath::Max(Bounds.SphereRadius, 100.f);
		// Framed tight: the sphere radius over-estimates a long low
		// machine, so 0.82 of the textbook distance fills the tile.
		const float Distance = Radius
			/ FMath::Tan(FMath::DegreesToRadians(TileCapture->FOVAngle * 0.5f))
			* 0.82f;
		const FRotator Look(-26.f, 38.f, 0.f);
		TileCapture->SetRelativeLocation(Centre - Look.Vector() * Distance);
		TileCapture->SetRelativeRotation(Look);
		TileCapture->TextureTarget = Job.Target;
		Job.FramesPosed = 0;
		return;
	}
	if (++Job.FramesPosed < 2)
	{
		return;
	}
	TileCapture->CaptureScene();
	UE_LOG(LogTemp, Display, TEXT("TILE %s captured from %s"),
		*Job.DefinitionId.ToString(), *Job.Mesh->GetName());
	PendingTiles.RemoveAt(0);
}

bool ALBSpacecraftWIPPresentationActor::HasKitComponent(
	FName StationId, FName ComponentId) const
{
	// No ledger bound is NOT "empty". An absent binding must not paint
	// every station as starving - that would be the static bins'
	// dishonesty again, just in the other direction. Show the kit as
	// present and let the real refusal text carry the truth.
	if (InventoryAuthority == nullptr)
	{
		return true;
	}
	const FName StoreId(*FString::Printf(TEXT("Store.%s"),
		*StationId.ToString()));
	return InventoryAuthority->GetQuantity(StoreId, ComponentId) > 0;
}

int32 ALBSpacecraftWIPPresentationActor::KitCrateCount(FName ComponentId)
{
	// Derived from the sub-assembly recipe, not a constant. Every
	// component is four Sets today; if that ever changes, the dolly
	// changes with it rather than quietly showing the old number.
	for (const FLBSpacecraftItemRecipe& Recipe :
		FLBSpacecraftRecipeCatalogue::GetRecipeTable())
	{
		for (const FLBSpacecraftItemStack& Output : Recipe.Outputs)
		{
			if (Output.ItemId == ComponentId)
			{
				return FMath::Clamp(Recipe.Inputs.Num(), 1, 8);
			}
		}
	}
	// Nothing makes it, so it is bought in whole: one crate.
	return 1;
}

void ALBSpacecraftWIPPresentationActor::RefreshSiteScenery()
{
	// A FULL SITE MAP (owner 2026-08-28: "see if there's any sceneries
	// or anything in fab or download... needs to be a full site map
	// like arms trade tycoon").
	//
	// The answer to "buy something?" was no: the project already owns a
	// 759-piece industrial environment kit under /Game/Meshes with real
	// dimensions - 1.4 m fence panels, 6 m shipping containers, a 46 m
	// tower, a 145 m hangar, refinery pipework. Measured before use
	// (Scripts/inspect_scenery_kit_v001.py), because a name tells you
	// nothing about whether a thing dresses a 600 m site.
	//
	// Three layers, all instanced, built once:
	//   BEYOND THE FENCE - towers, a hangar and pipework standing off
	//     the plot, so the site sits in an industrial district instead
	//     of a void.
	//   THE YARD - shipping containers in ranks near the west road.
	//   THE ROADSIDE - light masts down the approach.
	//
	// Deterministic layout: the variation comes from the index, never
	// from a random draw, so the site looks the same every launch and a
	// screenshot means something.
	if (bSiteSceneryBuilt)
	{
		return;
	}
	auto LoadKit = [](const TCHAR* Name) -> UStaticMesh*
	{
		return LoadObject<UStaticMesh>(nullptr,
			*FString::Printf(TEXT("/Game/Meshes/%s.%s"), Name, Name));
	};
	// OUR OWN SCENERY (owner 2026-08-28: "can you make your own stuff
	// with the meshy api please"). Generated in the game's white
	// futuristic language rather than bought, so the site stops mixing
	// two art directions: our props stand ON the plot where the player
	// looks, and the bought grey kit stays in the DISTRICT beyond the
	// fence where its present-day industrial look reads as background.
	auto LoadOurs = [](const TCHAR* Name) -> UStaticMesh*
	{
		// This IS Meshy content - the owner's own brief for it was
		// "make your own stuff with the meshy api please" (2026-08-28).
		// The 2026-08-30 blanket blockout swept it up, and because the
		// whole outdoor build gates on Container below, the first
		// screen of every session lost its fence, gate, yard and
		// masts. UNBLOCKED 2026-09-01: the owner explicitly re-opened
		// the Meshy lane that evening ("don't forget you have meshy
		// api"), and this set is his own commissioned site dressing,
		// not unreviewed intake. The blockout still stands for the
		// station bodies it was aimed at.
		return LoadObject<UStaticMesh>(nullptr,
			*FString::Printf(TEXT("/Game/LineBoss/Candidates/Spacecraft/")
				TEXT("SiteScenery_v001/%s.%s"), Name, Name));
	};
	UStaticMesh* TowerTall = LoadKit(TEXT("SM_Background1_Tower01"));
	UStaticMesh* TowerWide = LoadKit(TEXT("SM_Background1_Tower02"));
	UStaticMesh* Antenna = LoadKit(TEXT("SM_Background1_AntennaTower"));
	UStaticMesh* Hangar = LoadKit(TEXT("SM_Background2_Hangar"));
	UStaticMesh* Pipes = LoadKit(TEXT("SM_Background2_Pipe01"));
	UStaticMesh* Container = LoadOurs(TEXT("SM_LB_SC_CargoContainer"));
	UStaticMesh* LampArch = LoadOurs(TEXT("SM_LB_SC_LightMast"));
	UStaticMesh* FencePanel = LoadOurs(TEXT("SM_LB_SC_FencePanel"));
	UStaticMesh* Gate = LoadOurs(TEXT("SM_LB_SC_EntranceGate"));
	UStaticMesh* Tank = LoadOurs(TEXT("SM_LB_SC_StorageTank"));
	UStaticMesh* Substation = LoadOurs(TEXT("SM_LB_SC_Substation"));
	UStaticMesh* Hauler = LoadOurs(TEXT("SM_LB_SC_DeliveryHauler"));
	// GATED ON OUR OWN KIT ONLY. This used to require TowerTall too -
	// a DISTANT BACKDROP TOWER from the bought car-era kit - and that
	// kit was archived out of Content in 97503b1. So one missing
	// scenery mesh beyond the fence silently took the entire outdoor
	// build with it: fence, gate, containers, light masts, tanks,
	// substation and hauler, on the first screen of every session.
	//
	// The old comment said "draws less, never more", which is true and
	// is exactly why nobody noticed. Missing background is invisible;
	// missing foreground looks like a game that was never finished.
	if (Container == nullptr)
	{
		UE_LOG(LogTemp, Warning,
			TEXT("SPACECRAFT PRESENTER: site scenery skipped - our own "
				"kit did not load. If this is a packaged build, "
				"SiteScenery_v001 is missing from "
				"DirectoriesToAlwaysCook."));
		return;
	}
	if (TowerTall == nullptr)
	{
		// Said out loud rather than absorbed. The district is meant to
		// be replaced in the game's own white futuristic language; until
		// it is, the plot draws and the horizon is empty.
		UE_LOG(LogTemp, Warning,
			TEXT("SPACECRAFT PRESENTER: the district backdrop kit is "
				"absent (archived with the car content). The plot still "
				"draws; the horizon beyond the fence does not."));
	}
	bSiteSceneryBuilt = true;

	auto MakeSceneryInstances = [this](const TCHAR* Key,
		UStaticMesh* Mesh) -> UInstancedStaticMeshComponent*
	{
		if (Mesh == nullptr)
		{
			return nullptr;
		}
		UInstancedStaticMeshComponent* Component =
			NewObject<UInstancedStaticMeshComponent>(this,
				UInstancedStaticMeshComponent::StaticClass(), FName(Key));
		Component->SetStaticMesh(Mesh);
		Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Component->SetCastShadow(true);
		Component->SetupAttachment(RootComponent);
		Component->RegisterComponent();
		return Component;
	};

	const float Edge = ALBSpacecraftBuildAuthority::SiteHalfExtentCm();
	// ---- beyond the fence: the district (bought kit) ----
	UInstancedStaticMeshComponent* Towers =
		MakeSceneryInstances(TEXT("SceneryTowers"), TowerTall);
	UInstancedStaticMeshComponent* Wides =
		MakeSceneryInstances(TEXT("SceneryTowersWide"), TowerWide);
	UInstancedStaticMeshComponent* Masts =
		MakeSceneryInstances(TEXT("SceneryAntennae"), Antenna);
	UInstancedStaticMeshComponent* Hangars =
		MakeSceneryInstances(TEXT("SceneryHangars"), Hangar);
	UInstancedStaticMeshComponent* Refinery =
		MakeSceneryInstances(TEXT("SceneryPipes"), Pipes);
	// Ranks along each side, stepped out so nothing crowds the wall but
	// nothing strands in the distance either.
	for (int32 Index = 0; Index < 44; ++Index)
	{
		const int32 Side = Index % 4;
		const int32 Along = Index / 4;
		const float Offset = -Edge + 3000.f + Along * 5400.f;
		const float Out = Edge + 4500.f + (Index % 3) * 9000.f;
		FVector Where;
		switch (Side)
		{
		case 0: Where = FVector(Offset, Out, 0.f); break;
		case 1: Where = FVector(Offset, -Out, 0.f); break;
		case 2: Where = FVector(Out, Offset, 0.f); break;
		default: Where = FVector(-Out, Offset, 0.f); break;
		}
		const float Yaw = 90.f * (Index % 4) + (Index % 7) * 6.f;
		const FTransform Spot(FRotator(0.f, Yaw, 0.f), Where,
			FVector(1.f, 1.f, 0.75f + 0.15f * (Index % 4)));
		switch (Index % 5)
		{
		case 0:
			// Guarded like its four siblings. It was the ONLY unguarded
			// one, which is why the early return above had to promise
			// TowerTall was non-null - and that promise is what took
			// the whole plot down with the backdrop.
			if (Towers != nullptr) { Towers->AddInstance(Spot, true); }
			break;
		case 1:
			if (Wides != nullptr) { Wides->AddInstance(Spot, true); }
			break;
		case 2:
			if (Masts != nullptr) { Masts->AddInstance(Spot, true); }
			break;
		case 3:
			if (Hangars != nullptr) { Hangars->AddInstance(Spot, true); }
			break;
		default:
			if (Refinery != nullptr) { Refinery->AddInstance(Spot, true); }
			break;
		}
	}

	// ---- the yard: containers in ranks, west of the plot ----
	if (UInstancedStaticMeshComponent* Containers =
		MakeSceneryInstances(TEXT("SceneryContainers"), Container))
	{
		for (int32 Row = 0; Row < 4; ++Row)
		{
			for (int32 Slot = 0; Slot < 6; ++Slot)
			{
				const FVector Where(
					-Edge + 4000.f + Row * 900.f,
					-9000.f + Slot * 1400.f,
					(Slot % 3 == 0 && Row % 2 == 0) ? 301.f : 0.f);
				Containers->AddInstance(FTransform(
					FRotator(0.f, 90.f, 0.f), Where), true);
			}
		}
	}

	// ---- the roadside: light masts down the approach ----
	if (UInstancedStaticMeshComponent* Lamps =
		MakeSceneryInstances(TEXT("SceneryLampArches"), LampArch))
	{
		// Down the west approach, spaced like real yard lighting.
		for (int32 Index = 0; Index < 7; ++Index)
		{
			Lamps->AddInstance(FTransform(FRotator::ZeroRotator,
				FVector(-24000.f, -18000.f + Index * 6000.f, 0.f)),
				true);
		}
	}
	// ---- the fence line: OUR panels, right around the plot ----
	// A 7.6 m panel every 7.6 m, with the run BROKEN where the entrance
	// gate stands - a fence drawn through its own gateway is the kind
	// of detail that makes a site read as assembled rather than built.
	const float GateY = 0.f;
	const float GateHalfWidth = 800.f;
	if (UInstancedStaticMeshComponent* Fence =
		MakeSceneryInstances(TEXT("SceneryFence"), FencePanel))
	{
		constexpr float PanelCm = 759.f;
		const int32 PerSide = FMath::FloorToInt(Edge * 2.f / PanelCm);
		for (int32 Index = 0; Index < PerSide; ++Index)
		{
			const float Along = -Edge + PanelCm * (Index + 0.5f);
			// West side carries the gateway.
			if (FMath::Abs(Along - GateY) > GateHalfWidth)
			{
				Fence->AddInstance(FTransform(FRotator(0.f, 90.f, 0.f),
					FVector(-Edge, Along, 0.f)), true);
			}
			Fence->AddInstance(FTransform(FRotator(0.f, 90.f, 0.f),
				FVector(Edge, Along, 0.f)), true);
			Fence->AddInstance(FTransform(FRotator::ZeroRotator,
				FVector(Along, -Edge, 0.f)), true);
			Fence->AddInstance(FTransform(FRotator::ZeroRotator,
				FVector(Along, Edge, 0.f)), true);
		}
	}
	if (UInstancedStaticMeshComponent* Gates =
		MakeSceneryInstances(TEXT("SceneryGate"), Gate))
	{
		Gates->AddInstance(FTransform(FRotator(0.f, 90.f, 0.f),
			FVector(-Edge, GateY, 0.f)), true);
	}

	// ---- plant beside the power plant: tanks and a substation ----
	if (UInstancedStaticMeshComponent* Tanks =
		MakeSceneryInstances(TEXT("SceneryTanks"), Tank))
	{
		for (int32 Index = 0; Index < 3; ++Index)
		{
			Tanks->AddInstance(FTransform(FRotator::ZeroRotator,
				FVector(-9000.f + Index * 700.f, 14000.f, 0.f)), true);
		}
	}
	if (UInstancedStaticMeshComponent* Substations =
		MakeSceneryInstances(TEXT("ScenerySubstations"), Substation))
	{
		for (int32 Index = 0; Index < 4; ++Index)
		{
			Substations->AddInstance(FTransform(FRotator(0.f, 90.f, 0.f),
				FVector(-13000.f, 9000.f + Index * 500.f, 0.f)), true);
		}
	}

	// ---- a hauler standing at the gate, one at the yard ----
	if (UInstancedStaticMeshComponent* Haulers =
		MakeSceneryInstances(TEXT("SceneryHaulers"), Hauler))
	{
		Haulers->AddInstance(FTransform(FRotator(0.f, 90.f, 0.f),
			FVector(-Edge + 3500.f, GateY + 1800.f, 0.f)), true);
		Haulers->AddInstance(FTransform(FRotator::ZeroRotator,
			FVector(-20000.f, -6000.f, 0.f)), true);
	}
	UE_LOG(LogTemp, Display,
		TEXT("LBSiteScenery dressed: our props on the plot, the bought ")
		TEXT("kit in the district"));
}

void ALBSpacecraftWIPPresentationActor::ApplySceneLighting()
{
	// THE LIGHT IS A COLOUR DECISION, AND IT WAS THE ONE NOBODY OWNED.
	//
	// The site ground was set to the spec's Ground.Prepared - saturation
	// 8%, value 76% - and rendered back at saturation 14%, value 83%. A
	// rendered pixel is albedo times light and will never equal its
	// albedo, but neutral light preserves SATURATION, and ours nearly
	// doubled it. The sun was RGB(255, 246, 232): a warm white carrying
	// about nine points of warm saturation of its own, which is very
	// nearly the whole discrepancy.
	//
	// A warm key is the worst possible fault for this palette because
	// it pushes EVERY surface toward Machine.Amber's hue arc at once -
	// the same global failure the spec cites when it rules out a dusk
	// setting. No amount of correcting individual albedos can fix a
	// light that is tinting all of them.
	//
	// THIS DOES NOT MAKE THE WORLD COLD. The warmth belongs to the
	// albedo, where it can be measured: Ground.Prepared is 40 degrees,
	// Floor.Concrete 38, Machine.Housing.Pale 38. A neutral sun is what
	// lets those warm tones read at the saturation they were chosen
	// for instead of being pushed past it.
	//
	// Set from CODE rather than in the map because a value living in a
	// map package is invisible to the release gate, untestable, and
	// free to drift - and this one had. The map still owns the actors;
	// the palette owns their colour.
	for (TActorIterator<ADirectionalLight> It(GetWorld()); It; ++It)
	{
		if (UDirectionalLightComponent* Sun =
			Cast<UDirectionalLightComponent>(It->GetLightComponent()))
		{
			// THE WARM KEY IS THE OWNER'S DECISION (2026-09-02). Shown
			// the same view at warmth 0, 0.5 and 1 (LB.Look.Sun), he
			// chose 1: "yeah I agree with the car manufacturer feel".
			// That supersedes the neutral-sun argument above. The sky
			// fill stays cool so pale hull and pale ground still
			// separate; if the amber-arc problem shows on a frame it is
			// raised with him, not quietly reverted.
			Sun->SetLightColor(FLinearColor(1.0f, 0.86f, 0.70f));
			// Phase A: contact shadows, so a pallet, a drone and a hull
			// section sit ON the floor instead of floating in the same
			// value as it. Screen-space length, a small fraction.
			Sun->ContactShadowLength = 0.03f;
			Sun->MarkRenderStateDirty();
			// High overcast daylight, fixed. The spec puts the sun at
			// 62 degrees and never overhead: a 90-degree sun kills the
			// silhouette read from above, which is the only read this
			// camera has.
			It->SetActorRotation(FRotator(-62.f, -135.f, 0.f));
		}
	}
	for (TActorIterator<ASkyLight> It(GetWorld()); It; ++It)
	{
		if (USkyLightComponent* Sky = It->GetLightComponent())
		{
			// Cool fill against warm ground bounce. That pairing is
			// what keeps a pale hull separable from pale ground - the
			// two things most likely to merge in this game.
			Sky->SetLightColor(LBSpacecraftPalette::SkyAmbient);
		}
	}
}

void ALBSpacecraftWIPPresentationActor::RefreshSiteDressing()
{
	if (bSiteDressed)
	{
		return;
	}
	ApplySceneLighting();
	UStaticMesh* TileMesh = TryGetStationMesh(FName(TEXT("Site.FloorTile")));
	UStaticMesh* WallMesh = TryGetStationMesh(FName(TEXT("Site.WallPanel")));
	UStaticMesh* PillarMesh =
		TryGetStationMesh(FName(TEXT("Site.WallPillar")));
	if (TileMesh == nullptr || WallMesh == nullptr || PillarMesh == nullptr)
	{
		// Content absent: the map's own floor stands in - and that is
		// FINAL for the session, because these are synchronous loads.
		// Retrying meant three failed loads and a full relight EVERY
		// FRAME (the 2026-09-01 boot crawl and the per-frame mobility
		// warning storm in the log).
		bSiteDressed = true;
		UE_LOG(LogTemp, Warning, TEXT(
			"SPACECRAFT PRESENTER: site dress meshes absent - the "
			"map's own floor stands in"));
		return;
	}
	bSiteDressed = true;
	RefreshSiteScenery();

	auto MakeInstances = [this](const TCHAR* Key, UStaticMesh* Mesh)
	{
		UInstancedStaticMeshComponent* Component =
			NewObject<UInstancedStaticMeshComponent>(this,
				UInstancedStaticMeshComponent::StaticClass(), FName(Key));
		Component->SetStaticMesh(Mesh);
		Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Component->SetCastShadow(true);
		Component->SetupAttachment(RootComponent);
		Component->RegisterComponent();
		return Component;
	};
	// THE OUTSIDE (owner 2026-08-27, on seeing the first site shot:
	// "that's not the outside map"). Everything until now was the
	// interior floor seen from above; this apron is the first piece of
	// world beyond the walls, so the site view reads as a factory
	// standing on a plot rather than tiles floating in void. It is a
	// first pass for the owner's eyes - the building-shell exteriors
	// come once this reads right.
	if (UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr,
		LBSpacecraftWIPPresentationPrivate::SpacecraftCubePath))
	{
		UStaticMeshComponent* Apron = NewObject<UStaticMeshComponent>(
			this, UStaticMeshComponent::StaticClass(),
			FName(TEXT("SiteExteriorApron")));
		Apron->SetStaticMesh(Cube);
		Apron->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Apron->SetCastShadow(false);
		Apron->SetReceivesDecals(false);
		Apron->SetupAttachment(RootComponent);
		Apron->RegisterComponent();
		if (UMaterialInterface* Concrete = LoadObject<UMaterialInterface>(
			nullptr, TEXT("/Game/LineBoss/Materials/Environment/")
			TEXT("MI_LB_SealedFactoryConcrete_Neutral_v001")
			TEXT(".MI_LB_SealedFactoryConcrete_Neutral_v001")))
		{
			Apron->SetMaterial(0, Concrete);
		}
		// 1400 x 1400 m of exterior ground, top surface 12 cm below the
		// interior tiles so the plot sits proud of it. It has to reach
		// past the DISTRICT: background towers standing beyond the edge
		// of a 600 m apron float in blue void, which is worse than no
		// background at all.
		Apron->SetWorldTransform(FTransform(FQuat::Identity,
			FVector(0.f, 0.f, -62.f), FVector(1400.f, 1400.f, 1.f)));
	}

	SiteFloorTiles = MakeInstances(TEXT("SiteFloorTiles"), TileMesh);
	// THE SITE IS GROUND, NOT A FLOOR (owner: "thats still got the
	// inside concrete"). These tiles are the factory's INTERIOR floor
	// mesh laid across the whole 600 m plot, so an unbuilt site read as
	// a poured slab. A compacted hardstand tone is what a prepared
	// factory site actually looks like, and it lets the eye tell
	// outside from inside at a glance.
	//
	// The walls were retired for this exact reason already - "a black
	// palisade around open ground" - and the floor was left.
	if (UMaterialInterface* Apron = LoadObject<UMaterialInterface>(
		nullptr,
		TEXT("/Game/LineBoss/Materials/Surfaces/MI_LB_Surface_SiteApron")
		TEXT(".MI_LB_Surface_SiteApron")))
	{
		// THE GROUND TONE COMES FROM THE PALETTE, NOT FROM THE ASSET.
		//
		// The material instance carried a hardstand tone picked by hand,
		// and the opening screen read as a sand flat because of it. The
		// spec's Ground.Prepared is deliberately the same hue as the
		// interior slab and only three points below it in value, so
		// stepping inside a building is not a change of world.
		//
		// Driven through BaseTint rather than by editing the asset so
		// the value lives beside every other colour decision and is
		// covered by the palette tests.
		if (UMaterialInstanceDynamic* Ground =
			UMaterialInstanceDynamic::Create(Apron, this))
		{
			Ground->SetVectorParameterValue(TEXT("BaseTint"),
				LBSpacecraftPalette::GroundPrepared);
			SiteFloorTiles->SetMaterial(0, Ground);
		}
		else
		{
			SiteFloorTiles->SetMaterial(0, Apron);
		}
	}
	// ---- THE GROUND IS SURVEYED, NOT JUST COLOURED ----
	//
	// A 600 m plot with one building on it reads as an unfinished level
	// rather than as a business on its first day, and the owner has now
	// said as much twice about this screen. Colour alone does not fix
	// it: EMPTINESS READS AS CAPACITY ONLY IF THE GROUND IS ORGANISED.
	//
	// So the plot is surveyed - a boundary kerb and a painted grid on
	// the spec's 20 m pitch. It does two jobs at once. It makes the
	// site look prepared and owned, and it teaches where things can go
	// before the player has touched a placement tool, because the grid
	// IS the module buildings sit on.
	//
	// Deliberately hue-free line-work in Site.Kerb, so organising the
	// ground costs nothing against the saturation budget the ships are
	// owed.
	if (UStaticMesh* Cube = LoadObject<UStaticMesh>(
		nullptr, LBSpacecraftWIPPresentationPrivate::SpacecraftCubePath))
	{
		SiteGridLines = MakeInstances(TEXT("SiteGridLines"), Cube);
		if (SiteGridLines != nullptr)
		{
			// The SAME shape material every painted block uses, with
			// its "Color" parameter. Creating a dynamic instance from
			// the cube's own default material instead would silently
			// do nothing - the parameter would not exist, no error
			// would be raised, and the grid would render in engine
			// grey while looking like it had been coloured.
			if (UMaterialInterface* ShapeMaterial =
				LoadObject<UMaterialInterface>(nullptr,
					LBSpacecraftWIPPresentationPrivate
						::SpacecraftShapeMaterialPath))
			{
				UMaterialInstanceDynamic* Paint =
					UMaterialInstanceDynamic::Create(
						ShapeMaterial, SiteGridLines);
				Paint->SetVectorParameterValue(TEXT("Color"),
					LBSpacecraftPalette::SiteKerb);
				SiteGridLines->SetMaterial(0, Paint);
			}
			const float Half =
				ALBSpacecraftBuildAuthority::SiteHalfExtentCm();
			// 20 m survey pitch, from the spec and kept exactly.
			//
			// THE WIDTHS ARE NOT THE SPEC'S, AND THAT IS DELIBERATE.
			// It calls for a 0.10 m painted line and a 0.15 m kerb,
			// which are the right dimensions standing on the ground and
			// invisible from where this game is actually played. The
			// site camera covers roughly 200 m across about 836 px of
			// world, so a metre is 4.2 px and the spec's line is 0.42
			// PX WIDE - under one pixel, and it rendered as nothing at
			// all on the first attempt.
			//
			// Widened to the smallest sizes that survive that zoom:
			// 0.60 m reads at ~2.5 px and 1.00 m at ~4.2 px. A marking
			// nobody can see is not a subtler marking, it is an absent
			// one, and the whole purpose here is that the ground LOOKS
			// surveyed.
			//
			// Raised as an amendment rather than assumed: the honest
			// fix is a marking whose screen width has a floor, so it
			// stays legible at site zoom without becoming a runway at
			// ground zoom. Until that exists these are tuned for the
			// view that actually shows them.
			constexpr float GridPitchCm = 2000.f;
			constexpr float LineWidthCm = 60.f;
			constexpr float KerbWidthCm = 100.f;
			// LIFTED WELL CLEAR OF THE TILES, on precedent rather than
			// on taste. Ground markings have been lost on this project
			// three times now: too low reads as nothing at all, and the
			// hall's own markings needed 30 cm before they cleared - 12
			// still z-fought. The first attempt here used 8 cm, and 66
			// lines rendered as nothing.
			//
			// At site zoom the plot is 600 m across and a metre is
			// about four pixels, so a third of a metre of lift is
			// invisible. There is no cost to clearing properly and a
			// whole build cycle to clearing narrowly.
			constexpr float PaintZCm = 30.f;
			constexpr float KerbZCm = 40.f;

			auto AddBar = [this](const FVector& Centre,
				const FVector& SizeCm)
			{
				SiteGridLines->AddInstance(FTransform(
					FRotator::ZeroRotator, Centre,
					SizeCm / 100.f), true);
			};

			const int32 Lines = FMath::FloorToInt(Half / GridPitchCm);
			for (int32 Step = -Lines; Step <= Lines; ++Step)
			{
				const float At = Step * GridPitchCm;
				AddBar(FVector(At, 0.f, PaintZCm),
					FVector(LineWidthCm, Half * 2.f, 4.f));
				AddBar(FVector(0.f, At, PaintZCm),
					FVector(Half * 2.f, LineWidthCm, 4.f));
			}
			// The boundary kerb, standing slightly prouder than the
			// paint so the edge of the plot reads as a physical edge
			// without a wall. The walls were retired precisely because
			// they read as "a black palisade around open ground"; a
			// kerb states the same boundary and encloses nothing.
			for (int32 Side = 0; Side < 2; ++Side)
			{
				const float At = (Side == 0) ? -Half : Half;
				AddBar(FVector(At, 0.f, KerbZCm),
					FVector(KerbWidthCm, Half * 2.f, 16.f));
				AddBar(FVector(0.f, At, KerbZCm),
					FVector(Half * 2.f, KerbWidthCm, 16.f));
			}
		}
	}

	SiteWallPanels = MakeInstances(TEXT("SiteWallPanels"), WallMesh);
	SiteWallPillars = MakeInstances(TEXT("SiteWallPillars"), PillarMesh);
	// Only the FLOOR takes the bay paint.
	SiteWallPanels->SetReceivesDecals(false);
	SiteWallPillars->SetReceivesDecals(false);

	// The site is the buildable ground bound (SiteHalfExtentCm) on
	// a 1000 cm module: 22 x 22 tiles, walls on all four edges.
	constexpr float Module = 1000.f;
	const float HalfSite =
		ALBSpacecraftBuildAuthority::SiteHalfExtentCm();
	const int32 Span = FMath::RoundToInt(HalfSite * 2.f / Module);
	for (int32 IX = 0; IX < Span; ++IX)
	{
		for (int32 IY = 0; IY < Span; ++IY)
		{
			const FVector Where(
				-HalfSite + Module * (IX + 0.5f),
				-HalfSite + Module * (IY + 0.5f), 0.f);
			// Quarter-turn the tiles in a checker so the drain and
			// score lines do not stripe the whole floor one way.
			const float Yaw = ((IX + IY) % 2 == 0) ? 0.f : 90.f;
			SiteFloorTiles->AddInstance(FTransform(
				FRotator(0.f, Yaw, 0.f), Where), true);
		}
	}
	// Walls: RETIRED 2026-08-28. These interior wall bays were dressing
	// for a 220 m factory FLOOR; on a 600 m site with three buildings
	// on it they read as a black palisade around open ground, and they
	// stood in the same line as the generated perimeter fence, which is
	// what a site boundary actually looks like. The fence in
	// RefreshSiteScenery replaces them; the loop is kept, disabled, so
	// the module maths is here if an interior ever wants walls again.
	//
	// One bay per module along each edge, facing inward, with a pillar
	// at every joint. The +X edge is the RUNWAY side and stays OPEN -
	// the craft leaves that way (site furniture contract).
	constexpr bool bDressSiteWalls = false;
	for (int32 Index = 0; bDressSiteWalls && Index < Span; ++Index)
	{
		const float Along = -HalfSite + Module * (Index + 0.5f);
		const float Edge = HalfSite;
		// -X wall (behind the line).
		SiteWallPanels->AddInstance(FTransform(
			FRotator(0.f, 0.f, 0.f),
			FVector(-Edge, Along, 0.f)), true);
		// -Y and +Y walls run the other way.
		SiteWallPanels->AddInstance(FTransform(
			FRotator(0.f, 90.f, 0.f),
			FVector(Along, -Edge, 0.f)), true);
		SiteWallPanels->AddInstance(FTransform(
			FRotator(0.f, 90.f, 0.f),
			FVector(Along, Edge, 0.f)), true);
		// Pillars at the joints.
		const float Joint = -HalfSite + Module * Index;
		SiteWallPillars->AddInstance(FTransform(
			FRotator::ZeroRotator, FVector(-Edge, Joint, 0.f)), true);
		SiteWallPillars->AddInstance(FTransform(
			FRotator::ZeroRotator, FVector(Joint, -Edge, 0.f)), true);
		SiteWallPillars->AddInstance(FTransform(
			FRotator::ZeroRotator, FVector(Joint, Edge, 0.f)), true);
	}
	// Corner pillars close the three walled edges (retired with them).
	for (const FVector& Corner : bDressSiteWalls
		? TArray<FVector>{ FVector(-HalfSite, -HalfSite, 0.f),
			FVector(-HalfSite, HalfSite, 0.f) }
		: TArray<FVector>{})
	{
		SiteWallPillars->AddInstance(FTransform(
			FRotator::ZeroRotator, Corner), true);
	}
	UE_LOG(LogTemp, Display,
		TEXT("SPACECRAFT PRESENTER: site dressed - %d floor tiles, ")
		TEXT("%d survey lines, %d wall bays, %d pillars"),
		SiteFloorTiles->GetInstanceCount(),
		SiteGridLines != nullptr
			? SiteGridLines->GetInstanceCount() : 0,
		SiteWallPanels->GetInstanceCount(),
		SiteWallPillars->GetInstanceCount());
}

void ALBSpacecraftWIPPresentationActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	VisualTimeSeconds += DeltaSeconds;
	RefreshSiteDressing();
	RefreshStations();
	RefreshSiteShells();
	TickStationAccents(DeltaSeconds);
	TickRunways(DeltaSeconds);
	TickConveyors(DeltaSeconds);
	TickTrack(DeltaSeconds);
	TickDrones(DeltaSeconds);
	TickSubAssemblyLogistics(DeltaSeconds);
	RefreshUnits();
	// AFTER RefreshUnits: it publishes where the carried craft is, and
	// the gantry has nothing to follow until it has.
	TickHallCrane(DeltaSeconds);
	TickShellDeliveries(DeltaSeconds);
	TickDepartures(DeltaSeconds);
	TickAudioCues(DeltaSeconds);
	TickTileStudio();
	// LAST: the sweep rides whatever craft is under the scan, so it
	// reads the unit visuals only after RefreshUnits has placed them.
	RefreshInspectionSweep();
}

// LB.Look.Sun <warmth 0..1>: the A/B lever for the one look decision that
// is the owner's, not mine (2026-09-02). 0 is the palette adoption's
// neutral white sun; 1 is a frankly warm key. Presentation only, nothing
// saved, so two frames of the same view can be put in front of him.
static FAutoConsoleCommandWithWorldAndArgs LBLookSunCommand(
	TEXT("LB.Look.Sun"),
	TEXT("Sun warmth for A/B frames: 0 neutral white, 1 warm. Args: [warmth]"),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	if (World == nullptr)
	{
		return;
	}
	const float Warmth = FMath::Clamp(
		Args.Num() > 0 ? FCString::Atof(*Args[0]) : 0.5f, 0.f, 1.f);
	const FLinearColor Colour = FMath::Lerp(FLinearColor::White,
		FLinearColor(1.0f, 0.86f, 0.70f), Warmth);
	for (TActorIterator<ADirectionalLight> It(World); It; ++It)
	{
		if (UDirectionalLightComponent* Sun =
			Cast<UDirectionalLightComponent>(It->GetLightComponent()))
		{
			Sun->SetLightColor(Colour);
		}
	}
	UE_LOG(LogTemp, Display, TEXT("LB.Look.Sun warmth %.2f -> (%.2f %.2f %.2f)"),
		Warmth, Colour.R, Colour.G, Colour.B);
}));
