#include "LBSpacecraftSaveGame.h"

#include "Kismet/GameplayStatics.h"

namespace LBSpacecraftSavePipelinePrivate
{
	// Unity-build safety: helpers qualified by subject.
	constexpr int32 SpacecraftSaveUserIndex = 0;
}

bool FLBSpacecraftSavePipeline::SaveToSlot(
	const FLBSpacecraftSaveContext& Context, const FString& SlotName,
	FString& OutReason)
{
	using namespace LBSpacecraftSavePipelinePrivate;
	if (!Context.IsComplete())
	{
		OutReason = TEXT("SAVE NEEDS EVERY AUTHORITY");
		return false;
	}
	if (SlotName.IsEmpty())
	{
		OutReason = TEXT("SAVE NEEDS A SLOT NAME");
		return false;
	}
	ULBSpacecraftSaveGame* Save = Cast<ULBSpacecraftSaveGame>(
		UGameplayStatics::CreateSaveGameObject(
			ULBSpacecraftSaveGame::StaticClass()));
	if (Save == nullptr)
	{
		OutReason = TEXT("COULD NOT CREATE THE SAVE OBJECT");
		return false;
	}
	Save->FactoryLayout = Context.Build->CaptureState();
	Save->Ledger = Context.Production->CaptureLedger();
	Save->Runtime = Context.Coordinator->CaptureRuntime();
	Save->Inventory = Context.Inventory->CaptureSnapshot();
	Save->Crafting = Context.Crafting->CaptureSnapshot();
	Save->Power = Context.Power->CaptureSnapshot();
	Save->Research = Context.Research->CaptureSnapshot();
	Save->DroneFleet = Context.DroneFleet->CaptureSnapshot();
	Save->Reputation = Context.Reputation->CaptureSnapshot();
	Save->Transport = Context.Transport->CaptureSnapshot();
	Save->Progression = Context.Progression->CaptureSnapshot();
	Save->LineTrack = Context.Track->CaptureSnapshot();

	// Never write a snapshot that would refuse to load.
	if (!Context.Build->ValidateState(Save->FactoryLayout, OutReason)
		|| !Context.Production->ValidateLedger(Save->Ledger, OutReason)
		|| !ALBSpacecraftInventoryAuthority::ValidateSnapshot(
			Save->Inventory, OutReason)
		|| !ALBSpacecraftCraftingAuthority::ValidateSnapshot(
			Save->Crafting, OutReason)
		|| !ALBSpacecraftPowerAuthority::ValidateSnapshot(
			Save->Power, OutReason)
		|| !ALBSpacecraftResearchAuthority::ValidateSnapshot(
			Save->Research, OutReason)
		|| !ALBSpacecraftDroneFleetAuthority::ValidateSnapshot(
			Save->DroneFleet, OutReason)
		|| !ALBSpacecraftReputationAuthority::ValidateSnapshot(
			Save->Reputation, OutReason)
		|| !Context.Transport->ValidateSnapshot(
			Save->Transport, OutReason)
		|| !Context.Progression->ValidateSnapshot(
			Save->Progression, OutReason))
	{
		OutReason = FString::Printf(TEXT("REFUSING TO SAVE INVALID STATE: %s"),
			*OutReason);
		return false;
	}
	if (!UGameplayStatics::SaveGameToSlot(Save, SlotName,
		SpacecraftSaveUserIndex))
	{
		OutReason = TEXT("SAVE SLOT WRITE FAILED");
		return false;
	}
	OutReason.Reset();
	return true;
}

bool FLBSpacecraftSavePipeline::LoadFromSlot(
	const FLBSpacecraftSaveContext& Context, const FString& SlotName,
	FString& OutReason)
{
	using namespace LBSpacecraftSavePipelinePrivate;
	if (!Context.IsComplete())
	{
		OutReason = TEXT("LOAD NEEDS EVERY AUTHORITY");
		return false;
	}
	if (!UGameplayStatics::DoesSaveGameExist(SlotName, SpacecraftSaveUserIndex))
	{
		OutReason = FString::Printf(TEXT("NO SAVE IN SLOT %s"), *SlotName);
		return false;
	}
	ULBSpacecraftSaveGame* Save = Cast<ULBSpacecraftSaveGame>(
		UGameplayStatics::LoadGameFromSlot(SlotName, SpacecraftSaveUserIndex));
	if (Save == nullptr)
	{
		OutReason = TEXT("SLOT DID NOT CONTAIN A SPACECRAFT SAVE");
		return false;
	}
	if (Save->SchemaVersion != ULBSpacecraftSaveGame::CurrentSchemaVersion)
	{
		OutReason = FString::Printf(
			TEXT("SAVE SCHEMA %d DOES NOT MATCH CURRENT %d"),
			Save->SchemaVersion, ULBSpacecraftSaveGame::CurrentSchemaVersion);
		return false;
	}

	// Capture the pre-load state so ANY failure rolls everything back and
	// invalid data never partly applies.
	const FLBSpacecraftFactoryLayoutState PreLayout =
		Context.Build->CaptureState();
	const FLBSpacecraftProductionLedgerState PreLedger =
		Context.Production->CaptureLedger();
	const FLBSpacecraftRuntimeState PreRuntime =
		Context.Coordinator->CaptureRuntime();
	const FLBSpacecraftInventorySnapshot PreInventory =
		Context.Inventory->CaptureSnapshot();
	const FLBSpacecraftCraftingSnapshot PreCrafting =
		Context.Crafting->CaptureSnapshot();
	const FLBSpacecraftPowerSnapshot PrePower =
		Context.Power->CaptureSnapshot();
	const FLBSpacecraftResearchSnapshot PreResearch =
		Context.Research->CaptureSnapshot();
	const FLBSpacecraftDroneFleetSnapshot PreDroneFleet =
		Context.DroneFleet->CaptureSnapshot();
	const FLBSpacecraftReputationSnapshot PreReputation =
		Context.Reputation->CaptureSnapshot();
	const FLBSpacecraftTransportSnapshot PreTransport =
		Context.Transport->CaptureSnapshot();
	const FLBSpacecraftProgressionSnapshot PreProgression =
		Context.Progression->CaptureSnapshot();
	const FLBSpacecraftTrackSnapshot PreTrack =
		Context.Track->CaptureSnapshot();
	const bool bWasConfigured = Context.Coordinator->IsConfigured();

	auto RollBack = [&]()
	{
		FString Ignored;
		Context.Build->RestoreState(PreLayout, Ignored);
		Context.Production->RestoreLedger(PreLedger, Ignored);
		Context.Inventory->RestoreSnapshot(PreInventory, Ignored);
		Context.Crafting->RestoreSnapshot(PreCrafting, Ignored);
		Context.Power->RestoreSnapshot(PrePower, Ignored);
		Context.Research->RestoreSnapshot(PreResearch, Ignored);
		Context.DroneFleet->RestoreSnapshot(PreDroneFleet, Context.Power,
			Ignored);
		Context.Reputation->RestoreSnapshot(PreReputation, Ignored);
		Context.Transport->RestoreSnapshot(PreTransport, Ignored);
		Context.Progression->RestoreSnapshot(PreProgression, Ignored);
		Context.Track->RestoreSnapshot(PreTrack, Ignored);
		if (bWasConfigured)
		{
			Context.Coordinator->ConfigureFromAuthorities(Context.Build,
				Context.Production, Ignored);
			Context.Coordinator->RestoreRuntime(PreRuntime, Ignored);
		}
	};

	if (!Context.Build->RestoreState(Save->FactoryLayout, OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD LAYOUT REFUSED: %s"),
			*OutReason);
		return false; // nothing applied yet
	}
	if (!Context.Production->RestoreLedger(Save->Ledger, OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD LEDGER REFUSED: %s"),
			*OutReason);
		RollBack();
		return false;
	}
	if (!Context.Inventory->RestoreSnapshot(Save->Inventory, OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD INVENTORY REFUSED: %s"),
			*OutReason);
		RollBack();
		return false;
	}
	if (!Context.Crafting->RestoreSnapshot(Save->Crafting, OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD CRAFTING REFUSED: %s"),
			*OutReason);
		RollBack();
		return false;
	}
	if (!Context.Power->RestoreSnapshot(Save->Power, OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD POWER REFUSED: %s"),
			*OutReason);
		RollBack();
		return false;
	}
	if (!Context.Research->RestoreSnapshot(Save->Research, OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD RESEARCH REFUSED: %s"),
			*OutReason);
		RollBack();
		return false;
	}
	if (!Context.DroneFleet->RestoreSnapshot(Save->DroneFleet,
		Context.Power, OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD DRONE FLEET REFUSED: %s"),
			*OutReason);
		RollBack();
		return false;
	}
	if (!Context.Reputation->RestoreSnapshot(Save->Reputation, OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD REPUTATION REFUSED: %s"),
			*OutReason);
		RollBack();
		return false;
	}
	if (!Context.Transport->RestoreSnapshot(Save->Transport, OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD TRANSPORT REFUSED: %s"),
			*OutReason);
		RollBack();
		return false;
	}
	if (!Context.Progression->RestoreSnapshot(Save->Progression,
		OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD PROGRESSION REFUSED: %s"),
			*OutReason);
		RollBack();
		return false;
	}

	if (!Context.Track->RestoreSnapshot(Save->LineTrack, OutReason))
	{
		OutReason = FString::Printf(TEXT("LOAD TRACK REFUSED: %s"),
			*OutReason);
		RollBack();
		return false;
	}

	if (Save->FactoryLayout.bCommissioned)
	{
		FString ConfigureReason;
		if (!Context.Coordinator->ConfigureFromAuthorities(Context.Build,
			Context.Production, ConfigureReason, Context.Track))
		{
			OutReason = FString::Printf(TEXT("LOAD RECONFIGURE REFUSED: %s"),
				*ConfigureReason);
			RollBack();
			return false;
		}
		if (!Context.Coordinator->RestoreRuntime(Save->Runtime, OutReason))
		{
			OutReason = FString::Printf(TEXT("LOAD RUNTIME REFUSED: %s"),
				*OutReason);
			RollBack();
			return false;
		}
	}
	else if (Save->Runtime.Assignments.Num() > 0)
	{
		OutReason = TEXT(
			"SAVE HAS RUNTIME ASSIGNMENTS WITHOUT A COMMISSIONED FACTORY");
		RollBack();
		return false;
	}
	else
	{
		// Review fix: an uncommissioned save loaded over a running
		// session must clear the live route and assignments too.
		Context.Coordinator->ResetConfiguration();
	}

	OutReason.Reset();
	return true;
}
