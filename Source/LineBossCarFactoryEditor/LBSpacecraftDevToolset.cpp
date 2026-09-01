#include "LBSpacecraftDevToolset.h"

#include "Dom/JsonObject.h"
#include "Editor.h"
#include "Engine/World.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftPowerAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftProgressionAuthority.h"
#include "LBSpacecraftRuntimeCoordinator.h"
#include "LBSpacecraftTrackAuthority.h"
#include "Modules/ModuleManager.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "ToolsetRegistry/UToolsetRegistry.h"

namespace LBSpacecraftDevToolsetPrivate
{
	FString WriteJson(const TSharedRef<FJsonObject>& Root)
	{
		FString Out;
		const TSharedRef<TJsonWriter<TCHAR,
			TCondensedJsonPrintPolicy<TCHAR>>> Writer =
			TJsonWriterFactory<TCHAR,
				TCondensedJsonPrintPolicy<TCHAR>>::Create(&Out);
		FJsonSerializer::Serialize(Root, Writer);
		return Out;
	}

	FString FailJson(const FString& Error)
	{
		const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
		Root->SetBoolField(TEXT("success"), false);
		Root->SetStringField(TEXT("error"), Error);
		return WriteJson(Root);
	}

	/** The live PIE/game world, or null. The authorities only exist in
	 *  a playing world - the edited level has none. */
	UWorld* FindPlayWorld()
	{
		return GEditor != nullptr ? GEditor->PlayWorld : nullptr;
	}

	FString EnumName(const UEnum* Enum, int64 Value)
	{
		return Enum != nullptr
			? Enum->GetNameStringByValue(Value) : FString::FromInt(Value);
	}
}

FString ULBSpacecraftDevToolset::GetSpacecraftFactoryStatus()
{
	using namespace LBSpacecraftDevToolsetPrivate;
	UWorld* World = FindPlayWorld();
	if (World == nullptr)
	{
		return FailJson(TEXT("No PIE session is running - the factory "
			"authorities only exist in a playing world. Start PIE first."));
	}
	ALBSpacecraftGameMode* GameMode =
		ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr)
	{
		return FailJson(TEXT("The PIE world has no spacecraft game mode "
			"(wrong map?)."));
	}
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);

	if (ALBSpacecraftProductionAuthority* Production =
		GameMode->GetProductionAuthority())
	{
		Root->SetNumberField(TEXT("cashPence"),
			static_cast<double>(Production->GetCashPence()));
		Root->SetNumberField(TEXT("stockedCraft"),
			Production->GetStockedCraftCount());
		const UEnum* StageEnum = StaticEnum<ELBSpacecraftStage>();
		TArray<TSharedPtr<FJsonValue>> Units;
		for (const FLBSpacecraftUnitState& Unit : Production->GetUnits())
		{
			const TSharedRef<FJsonObject> U = MakeShared<FJsonObject>();
			U->SetStringField(TEXT("unitId"), Unit.UnitId.ToString());
			U->SetStringField(TEXT("recipeId"), Unit.RecipeId.ToString());
			U->SetStringField(TEXT("stage"),
				EnumName(StageEnum, static_cast<int64>(Unit.Stage)));
			U->SetNumberField(TEXT("producedComponents"),
				Unit.ProducedComponents.Num());
			U->SetNumberField(TEXT("defectPoints"), Unit.DefectPoints);
			U->SetNumberField(TEXT("reworkSecondsRemaining"),
				Unit.ReworkSecondsRemaining);
			U->SetBoolField(TEXT("completed"), Unit.bCompleted);
			U->SetBoolField(TEXT("awaitingSale"), Unit.bAwaitingSale);
			Units.Add(MakeShared<FJsonValueObject>(U));
		}
		Root->SetArrayField(TEXT("units"), Units);
		const UEnum* ContractEnum = StaticEnum<ELBSpacecraftContractState>();
		TArray<TSharedPtr<FJsonValue>> Contracts;
		for (const FLBSpacecraftContract& Contract :
			Production->GetContracts())
		{
			const TSharedRef<FJsonObject> C = MakeShared<FJsonObject>();
			C->SetStringField(TEXT("contractId"),
				Contract.ContractId.ToString());
			C->SetStringField(TEXT("recipeId"),
				Contract.RecipeId.ToString());
			C->SetStringField(TEXT("state"), EnumName(ContractEnum,
				static_cast<int64>(Contract.State)));
			C->SetNumberField(TEXT("quantity"), Contract.Quantity);
			C->SetNumberField(TEXT("dispatched"), Contract.DispatchedCount);
			C->SetNumberField(TEXT("pricePerUnitPence"),
				static_cast<double>(Contract.PricePerUnitPence));
			Contracts.Add(MakeShared<FJsonValueObject>(C));
		}
		Root->SetArrayField(TEXT("contracts"), Contracts);
	}
	if (ALBSpacecraftBuildAuthority* Build = GameMode->GetBuildAuthority())
	{
		Root->SetBoolField(TEXT("commissioned"), Build->IsCommissioned());
		TArray<TSharedPtr<FJsonValue>> Stations;
		for (const FLBSpacecraftStationRecord& Record :
			Build->GetStations())
		{
			const TSharedRef<FJsonObject> S = MakeShared<FJsonObject>();
			S->SetStringField(TEXT("stationId"),
				Record.StationId.ToString());
			S->SetStringField(TEXT("definitionId"),
				Record.DefinitionId.ToString());
			S->SetNumberField(TEXT("drones"),
				Record.InstalledDroneTypes.Num());
			Stations.Add(MakeShared<FJsonValueObject>(S));
		}
		Root->SetArrayField(TEXT("stations"), Stations);
	}
	if (ALBSpacecraftRuntimeCoordinator* Coordinator =
		GameMode->GetCoordinator())
	{
		Root->SetBoolField(TEXT("configured"), Coordinator->IsConfigured());
		Root->SetStringField(TEXT("lastStartRefusal"),
			Coordinator->GetLastStartRefusal());
		TArray<TSharedPtr<FJsonValue>> Route;
		for (const FLBSpacecraftRouteStep& Step : Coordinator->GetRoute())
		{
			Route.Add(MakeShared<FJsonValueString>(
				Step.StationId.ToString()));
		}
		Root->SetArrayField(TEXT("route"), Route);
	}
	if (ALBSpacecraftTrackAuthority* Track = GameMode->GetTrackAuthority())
	{
		Root->SetNumberField(TEXT("trackPieces"),
			Track->GetPieces().Num());
	}
	if (ALBSpacecraftPowerAuthority* Power = GameMode->GetPowerAuthority())
	{
		Root->SetNumberField(TEXT("powerDrawKw"), Power->GetTotalDrawKw());
		Root->SetNumberField(TEXT("powerSupplyKw"),
			Power->GetTotalSupplyKw());
	}
	if (ALBSpacecraftProgressionAuthority* Progress =
		GameMode->GetProgression())
	{
		Root->SetNumberField(TEXT("creditedDeliveries"),
			Progress->GetCreditedDeliveries());
		Root->SetNumberField(TEXT("ownedBays"),
			Progress->GetOwnedBayCount());
	}
	return WriteJson(Root);
}

FString ULBSpacecraftDevToolset::RunSpacecraftConsoleCommand(
	const FString& Command)
{
	using namespace LBSpacecraftDevToolsetPrivate;
	UWorld* World = FindPlayWorld();
	if (World == nullptr)
	{
		return FailJson(TEXT("No PIE session is running. Start PIE, then "
			"drive it with the LB.* commands."));
	}
	if (Command.TrimStartAndEnd().IsEmpty())
	{
		return FailJson(TEXT("Empty command."));
	}
	const bool bHandled = GEngine != nullptr
		&& GEngine->Exec(World, *Command);
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetBoolField(TEXT("success"), true);
	Root->SetStringField(TEXT("command"), Command);
	Root->SetBoolField(TEXT("handled"), bHandled);
	return WriteJson(Root);
}

/** Module: registers the toolset once the registry is up. Mirrors
 *  VibeUE's own deferral - GEditor may not exist yet at module load. */
class FLineBossCarFactoryEditorModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		if (IsRunningCommandlet())
		{
			// Cooks and commandlets need no MCP surface, and the
			// registry can stall clean exits.
			return;
		}
		if (GEditor != nullptr)
		{
			RegisterToolset();
		}
		else
		{
			FCoreDelegates::OnPostEngineInit.AddRaw(this,
				&FLineBossCarFactoryEditorModule::RegisterToolset);
		}
	}

	virtual void ShutdownModule() override
	{
		FCoreDelegates::OnPostEngineInit.RemoveAll(this);
		if (UToolsetRegistry::IsAvailable())
		{
			UToolsetRegistry::UnregisterToolsetClass(
				ULBSpacecraftDevToolset::StaticClass());
		}
	}

private:
	void RegisterToolset()
	{
		if (UToolsetRegistry::IsAvailable())
		{
			UToolsetRegistry::RegisterToolsetClass(
				ULBSpacecraftDevToolset::StaticClass());
			UE_LOG(LogTemp, Display, TEXT(
				"LINEBOSS MCP: LBSpacecraftDevToolset registered"));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT(
				"LINEBOSS MCP: ToolsetRegistry unavailable - the dev "
				"toolset is not exposed this session"));
		}
	}
};

IMPLEMENT_MODULE(FLineBossCarFactoryEditorModule, LineBossCarFactoryEditor)
