#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftCraftingAuthority.h"

#include "EngineUtils.h"
#include "LBSpacecraftCommandPanelWidget.h"
#include "Components/TextBlock.h"
#include "Blueprint/WidgetTree.h"
#include "LBSpacecraftPauseMenuWidget.h"
#include "LBSpacecraftSettingsWidget.h"
#include "LBSpacecraftObjectivesWidget.h"
#include "LBSpacecraftTransportAuthority.h"
#include "LBSpacecraftTrackAuthority.h"
#include "LBSpacecraftDifficulty.h"
#include "LBSpacecraftProgressionAuthority.h"
#include "Kismet/GameplayStatics.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "LBSpacecraftPlayerPawn.h"
#include "LBSpacecraftSiteHubWidget.h"
#include "TimerManager.h"
#include "UnrealClient.h"
#include "LBSpacecraftReputationAuthority.h"
#include "GameFramework/InputSettings.h"
#include "LBGameUserSettings.h"
#include "LBSpacecraftInputMap.h"
#include "LBSpacecraftSaveGame.h"
#include "LBSpacecraftTopBarWidget.h"
#include "LBSpacecraftWIPPresentationActor.h"
#include "Blueprint/UserWidget.h"

DEFINE_LOG_CATEGORY_STATIC(LogLBSpacecraft, Log, All);

namespace LBSpacecraftGameModePrivate
{
	// Unity-build safety: helpers qualified by subject.
	void SpacecraftLogStatus(ALBSpacecraftGameMode& GameMode)
	{
		ALBSpacecraftProductionAuthority* Production =
			GameMode.GetProductionAuthority();
		ALBSpacecraftRuntimeCoordinator* Coordinator =
			GameMode.GetCoordinator();
		ALBSpacecraftBuildAuthority* Build = GameMode.GetBuildAuthority();
		if (Production == nullptr || Coordinator == nullptr || Build == nullptr)
		{
			UE_LOG(LogLBSpacecraft, Warning,
				TEXT("LB.Spacecraft.Status: authorities missing"));
			return;
		}
		if (Production->GetStockedCraftCount() > 0)
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  FINISHED STOCK: %d craft built and unsold"),
				Production->GetStockedCraftCount());
		}
		if (!Coordinator->GetLastHoldReason().IsEmpty())
		{
			UE_LOG(LogLBSpacecraft, Display, TEXT("  LINE HELD: %s"),
				*Coordinator->GetLastHoldReason());
		}
		if (!Coordinator->GetLastStartRefusal().IsEmpty())
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  HEAD OF LINE: %s"),
				*Coordinator->GetLastStartRefusal());
		}
		// WHAT IS ACTUALLY ON THE LINE. Status reported stations,
		// commissioning and revenue but never the craft themselves, so
		// a line with a hull stuck at its head station looked exactly
		// like an idle one - every field read healthy while nothing
		// moved. Where a craft is and how far through its stop it has
		// got is the first thing anyone asks.
		if (Coordinator->GetAssignments().Num() == 0)
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  ON THE LINE: nothing"));
		}
		for (const FLBSpacecraftRuntimeAssignment& Assignment :
			Coordinator->GetAssignments())
		{
			const FLBSpacecraftUnitState* Unit =
				Production->FindUnit(Assignment.UnitId);
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  ON THE LINE: %s at %s (route step %d), "
					"%.1fs into its stop, stage %d"),
				*Assignment.UnitId.ToString(),
				*Assignment.StationId.ToString(),
				Assignment.RouteIndex,
				Assignment.CycleElapsedSeconds,
				Unit != nullptr ? static_cast<int32>(Unit->Stage) : -1);
		}
		UE_LOG(LogLBSpacecraft, Display,
			TEXT("SPACECRAFT STATUS sim=%.1fs stations=%d commissioned=%d ")
			TEXT("configured=%d revenue=%lld cash=%lld pence"),
			Production->GetSimSeconds(), Build->GetStations().Num(),
			Build->IsCommissioned() ? 1 : 0,
			Coordinator->IsConfigured() ? 1 : 0,
			Production->GetRevenuePence(), Production->GetCashPence());
		for (const FLBSpacecraftContract& Contract : Production->GetContracts())
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  CONTRACT %s %s x%d dispatched=%d state=%d"),
				*Contract.ContractId.ToString(),
				*Contract.RecipeId.ToString(), Contract.Quantity,
				Contract.DispatchedCount,
				static_cast<int32>(Contract.State));
		}
		for (const FLBSpacecraftUnitState& Unit : Production->GetUnits())
		{
			float Progress01 = 0.f;
			Coordinator->GetUnitCycleProgress(Unit.UnitId, Progress01);
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  UNIT %s stage=%d progress=%.0f%% components=%d"),
				*Unit.UnitId.ToString(), static_cast<int32>(Unit.Stage),
				Progress01 * 100.f, Unit.ProducedComponents.Num());
		}
		if (ALBSpacecraftPowerAuthority* Power = GameMode.GetPowerAuthority())
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  POWER supply=%dkW draw=%dkW headroom=%dkW"),
				Power->GetTotalSupplyKw(), Power->GetTotalDrawKw(),
				Power->GetHeadroomKw());
		}
		if (ALBSpacecraftResearchAuthority* Research =
			GameMode.GetResearchAuthority())
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  RESEARCH points=%d unlocked=%d/%d"),
				Research->GetPoints(), Research->GetUnlockedNodeCount(),
				FLBSpacecraftResearchCatalogue::GetNodeTable().Num());
		}
		if (ALBSpacecraftInventoryAuthority* Inventory =
			GameMode.GetInventoryAuthority())
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  INVENTORY stores=%d"), Inventory->GetStoreCount());
		}
		if (ALBSpacecraftDroneFleetAuthority* Fleet =
			GameMode.GetDroneFleet())
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  DRONES total=%d flying=%d charging=%d"),
				Fleet->GetDroneCount(), Fleet->GetFlyingCount(),
				Fleet->GetChargingCount());
			// LOGISTICS: what the heavy haulers are doing right now.
			// A factory that has stalled for want of a delivery is
			// almost always explained by this line.
			for (const FLBSpacecraftHaulState& Haul : Fleet->GetHauls())
			{
				UE_LOG(LogLBSpacecraft, Display,
					TEXT("  HAUL %s job=%s phase=%d to=%s item=%s x%d"),
					*Haul.RackStationId.ToString(),
					Haul.Job == ELBSpacecraftHaulJob::DeliverInput
						? TEXT("DELIVER") : TEXT("COLLECT"),
					static_cast<int32>(Haul.Phase),
					*Haul.MachineStationId.ToString(),
					*Haul.CarryItemId.ToString(), Haul.CarryCount);
			}
		}
		if (ALBSpacecraftInventoryAuthority* Inv =
			GameMode.GetInventoryAuthority())
		{
			// Where the goods actually are, store by store.
			for (const FName& StoreId : Inv->GetStoreIds())
			{
				UE_LOG(LogLBSpacecraft, Display,
					TEXT("  STORE %s holds %d/%d units"),
					*StoreId.ToString(), Inv->GetUsedUnits(StoreId),
					Inv->GetCapacityUnits(StoreId));
			}
		}
		// WHO FITS WHAT, as the panel shows it. A fitting station
		// with an empty allocation is the silent version of a stalled
		// line: the route sends a craft to it, the craft waits for a
		// part, and no hauler ever flies because the station never
		// asked for anything. Printing the allocation is the only way
		// a headless run can tell that apart from a slow delivery.
		for (const FLBSpacecraftStationRecord& Record :
			Build->GetStations())
		{
			if (!Build->IsFittingStation(Record.StationId))
			{
				continue;
			}
			FString Fits;
			for (const FName& Component : Record.AllocatedComponents)
			{
				Fits += (Fits.IsEmpty() ? TEXT("") : TEXT(", "));
				Fits += Component.ToString();
			}
			UE_LOG(LogLBSpacecraft, Display, TEXT("  FITS %s: %s"),
				*Record.StationId.ToString(),
				Fits.IsEmpty() ? TEXT("NOTHING ALLOCATED") : *Fits);
		}
		if (ALBSpacecraftReputationAuthority* Rep =
			GameMode.GetReputation())
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("  REPUTATION tier=%d points=%d"),
				Rep->GetTier(), Rep->GetPoints());
		}
	}

	// The dev floor store the LB.Spacecraft.Deposit/Craft commands use; the
	// real game registers stores through storage buildings.
	bool SpacecraftEnsureDevFloorStore(
		ALBSpacecraftInventoryAuthority& Inventory, FString& OutReason)
	{
		const FName Floor(TEXT("Store.Floor"));
		if (Inventory.HasStore(Floor))
		{
			return true;
		}
		return Inventory.RegisterStore(Floor, 5000, OutReason);
	}
}

ALBSpacecraftGameMode::ALBSpacecraftGameMode()
{
	// The live session ticks production on real time; headless journeys
	// keep using LB.Spacecraft.Run on top (both drive the same sim).
	PrimaryActorTick.bCanEverTick = true;
	DefaultPawnClass = ALBSpacecraftPlayerPawn::StaticClass();
}

void ALBSpacecraftGameMode::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (DeltaSeconds <= 0.f)
	{
		return;
	}
	// The factory time control scales every economy tick from ONE place
	// so money, power, crafting, hauls and the line can never drift
	// apart; 0 freezes the sim while the world keeps rendering.
	const float SimDelta = DeltaSeconds * SimTimeScale;
	// The line runs only once commissioned AND configured - before that
	// the coordinator would just refuse every tick.
	FString Reason;
	if (SimDelta > 0.f && Coordinator != nullptr
		&& Coordinator->IsConfigured())
	{
		Coordinator->TickProduction(SimDelta, Reason);
		// A line that stops must SAY so. Every hold reason used to be
		// computed and dropped, so the factory could sit frozen with
		// nothing on screen to explain it.
		RaiseSimAlert(Coordinator->GetLastHoldReason());
	}
	if (BuildAuthority != nullptr && CraftingAuthority != nullptr
		&& InventoryAuthority != nullptr)
	{
		if (Transport != nullptr)
		{
			Transport->SyncFromBuild(BuildAuthority);
		}
		SyncStationStores(*BuildAuthority, *InventoryAuthority,
			CraftingAuthority);
		TickLaunchCamera();
		if (SimDelta > 0.f)
		{
			TickCraftingStations(*BuildAuthority, *CraftingAuthority,
				*InventoryAuthority, SimDelta, Transport, this);
		}
	}
	if (DroneFleet != nullptr && SimDelta > 0.f)
	{
		DroneFleet->SyncFromBuild(BuildAuthority, PowerAuthority);
		DroneFleet->TickFleet(SimDelta, CraftingAuthority,
			PowerAuthority, Coordinator);
		DroneFleet->TickHauls(SimDelta, CraftingAuthority,
			InventoryAuthority, BuildAuthority);
	}
	if (PowerAuthority != nullptr && SimDelta > 0.f)
	{
		// The mains meter runs on the same clock as everything else
		// (owner 2026-08-26: electricity is bought until generation).
		PowerAuthority->TickGridMeter(SimDelta, ProductionAuthority);
	}
	SyncLedgerDerivedAuthorities();
	if (InventoryAuthority != nullptr && SimDelta > 0.f)
	{
		InventoryAuthority->TickOrders(SimDelta);
	}
}

void ALBSpacecraftGameMode::BeginPlay()
{
	Super::BeginPlay();
	// The player's saved difficulty takes hold before anything reads a
	// rule from it. Absent settings leave Standard in force rather than
	// guessing.
	if (const ULBGameUserSettings* Settings =
		ULBGameUserSettings::GetLineBossGameUserSettings())
	{
		FLBSpacecraftDifficulty::SetCurrent(
			Settings->GetSpacecraftDifficulty());
	}
	UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return;
	}
	// Empty authorities only - the premade-factory contract. Stations arrive
	// through the build authority, never seeded into the map.
	BuildAuthority = World->SpawnActor<ALBSpacecraftBuildAuthority>();
	ProductionAuthority =
		World->SpawnActor<ALBSpacecraftProductionAuthority>();
	Coordinator = World->SpawnActor<ALBSpacecraftRuntimeCoordinator>();
	InventoryAuthority = World->SpawnActor<ALBSpacecraftInventoryAuthority>();
	CraftingAuthority = World->SpawnActor<ALBSpacecraftCraftingAuthority>();
	PowerAuthority = World->SpawnActor<ALBSpacecraftPowerAuthority>();
	ResearchAuthority = World->SpawnActor<ALBSpacecraftResearchAuthority>();
	DroneFleet = World->SpawnActor<ALBSpacecraftDroneFleetAuthority>();
	Reputation = World->SpawnActor<ALBSpacecraftReputationAuthority>();
	Transport = World->SpawnActor<ALBSpacecraftTransportAuthority>();
	Progression = World->SpawnActor<ALBSpacecraftProgressionAuthority>();
	TrackAuthority = World->SpawnActor<ALBSpacecraftTrackAuthority>();
	// The player's saved preferences apply at the door: any spacecraft
	// mapping a stale Saved/Input.ini predates is backfilled, and the
	// saved master volume reaches the audio device (transient by
	// engine design, so it must be pushed every session).
	if (UInputSettings* InputSettings = UInputSettings::GetInputSettings())
	{
		FLBSpacecraftInputMap::EnsureSpacecraftBindings(*InputSettings);
	}
	if (ULBGameUserSettings* UserSettings =
		ULBGameUserSettings::GetLineBossGameUserSettings())
	{
		UserSettings->ApplyMasterVolumeToWorld(World);
	}
	// Research gates placement: a locked family is refused at the build
	// authority itself, before geometry. The slice families are free.
	if (BuildAuthority != nullptr && ResearchAuthority != nullptr)
	{
		TWeakObjectPtr<ALBSpacecraftResearchAuthority> WeakResearch =
			ResearchAuthority;
		BuildAuthority->SetPlacementGate(
			[WeakResearch](FName DefinitionId, FString& GateReason)
		{
			if (!WeakResearch.IsValid())
			{
				GateReason = TEXT("RESEARCH AUTHORITY IS GONE");
				return false;
			}
			if (!WeakResearch->IsStationClassUnlocked(DefinitionId))
			{
				GateReason = FString::Printf(
					TEXT("%s IS LOCKED - RESEARCH IT FIRST"),
					*DefinitionId.ToString());
				return false;
			}
			return true;
		});
		// Dedicated slot buildings open only after the FIRST unit of
		// their kind is owned (owner 2026-08-26: buy the power plant,
		// and it opens the dedicated building with more slots).
		TWeakObjectPtr<ALBSpacecraftBuildAuthority> WeakBuild =
			BuildAuthority;
		auto PriorGate = [WeakResearch](FName DefinitionId,
			FString& GateReason)
		{
			if (!WeakResearch.IsValid())
			{
				GateReason = TEXT("RESEARCH AUTHORITY IS GONE");
				return false;
			}
			if (!WeakResearch->IsStationClassUnlocked(DefinitionId))
			{
				GateReason = FString::Printf(
					TEXT("%s IS LOCKED - RESEARCH IT FIRST"),
					*DefinitionId.ToString());
				return false;
			}
			return true;
		};
		BuildAuthority->SetPlacementGate(
			[WeakBuild, PriorGate](FName DefinitionId,
				FString& GateReason)
		{
			if (!PriorGate(DefinitionId, GateReason))
			{
				return false;
			}
			if (!WeakBuild.IsValid())
			{
				return true;
			}
			// The POWER STATION has no prior-ownership gate any more:
			// generators live only inside it (owner 2026-08-26, "its
			// supposed to be in its own building"), so requiring a
			// plant first would deadlock the progression. The hall is
			// the purchase; plants install into its slots.
			// The SUB-ASSEMBLY HALL loses its prior-ownership gate for
			// the same reason the power station did: parts machines
			// live only inside it, so requiring one first would
			// deadlock. The hall is the purchase; machines fill it.
			return true;
		});
		// ON-SITE FABRICATION is a DELIVERY MILESTONE, and the hall is
		// what it opens. The objectives ladder had been promising this
		// unlock to the player since the slice shipped while gating
		// nothing at all - the ladder was telling them something that
		// was not true.
		//
		// Binding it to the hall makes the make-vs-buy arc read: your
		// first craft are assembled from components you IMPORT, and
		// once you have delivered a couple you earn the right to make
		// your own. (My design call; one line to re-bind if you would
		// rather it opened something else.)
		TWeakObjectPtr<ALBSpacecraftProgressionAuthority> WeakProgress =
			Progression;
		auto ResearchAndPriorGate = BuildAuthority->GetPlacementGate();
		BuildAuthority->SetPlacementGate(
			[WeakProgress, ResearchAndPriorGate](FName DefinitionId,
				FString& GateReason)
		{
			if (ResearchAndPriorGate
				&& !ResearchAndPriorGate(DefinitionId, GateReason))
			{
				return false;
			}
			if (DefinitionId == FName(TEXT("SubAssemblyHall"))
				&& WeakProgress.IsValid()
				&& !WeakProgress->IsUnlocked(
					ELBSpacecraftUnlock::Fabrication))
			{
				GateReason = WeakProgress->DescribeLock(
					ELBSpacecraftUnlock::Fabrication);
				return false;
			}
			return true;
		});
	}
	Presenter = World->SpawnActor<ALBSpacecraftWIPPresentationActor>();
	if (Presenter != nullptr)
	{
		Presenter->BindAuthorities(BuildAuthority, Coordinator,
			ProductionAuthority);
		Presenter->BindCrafting(CraftingAuthority);
		// The presenter never had the ledger. That is why the parts
		// visuals were static: not an oversight in the drawing code,
		// an absent binding - it could not see stock to draw it.
		Presenter->BindInventory(InventoryAuthority);
		Presenter->BindDroneFleet(DroneFleet);
		Presenter->BindTransport(Transport);
		Presenter->BindTrack(TrackAuthority);
		Coordinator->BindInventory(InventoryAuthority);
	}
	// The HUD is a read-only projection; it exists only where a player
	// viewport does (headless -NullRHI journeys run without it).
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("SPACECRAFT UI GATE: GameViewport=%d FirstPlayerController=%d"),
		World->GetGameViewport() != nullptr ? 1 : 0,
		World->GetFirstPlayerController() != nullptr ? 1 : 0);
	if (World->GetGameViewport() != nullptr)
	{
		if (APlayerController* PlayerController =
			World->GetFirstPlayerController())
		{
			TopBar = CreateWidget<ULBSpacecraftTopBarWidget>(
				PlayerController, ULBSpacecraftTopBarWidget::StaticClass());
			if (TopBar != nullptr)
			{
				TopBar->BindAuthorities(BuildAuthority, ProductionAuthority,
					Coordinator, PowerAuthority, ResearchAuthority,
					Reputation);
				TopBar->AddToViewport(100);
			}
			CommandPanel = CreateWidget<ULBSpacecraftCommandPanelWidget>(
				PlayerController,
				ULBSpacecraftCommandPanelWidget::StaticClass());
			if (CommandPanel != nullptr)
			{
				CommandPanel->BindGame(this, nullptr);
				CommandPanel->AddToViewport(90);
			}
			// THE SHIP FACTORY STANDS ON THE SITE FROM THE START (owner
			// 2026-08-29, superseding the empty plot). It was only ever
			// placed by the dev BuildLine command, so a real new game
			// opened on a bare site with every place on the hub
			// padlocked - including the one building the player is
			// supposed to walk into first.
			//
			// Placed through the normal build authority, not seeded into
			// the map package, which is the premade-factory contract:
			// what the player starts with must be built the way a player
			// builds it. Everything INSIDE it is still theirs to build.
			if (BuildAuthority != nullptr)
			{
				bool bHasHall = false;
				for (const FLBSpacecraftStationRecord& Record :
					BuildAuthority->GetStations())
				{
					bHasHall |= Record.DefinitionId
						== FName(TEXT("ShipFactoryHall"));
				}
				if (!bHasHall)
				{
					FName HallId;
					FString HallReason;
					if (!BuildAuthority->PlaceStarterHall(HallId, HallReason))
					{
						UE_LOG(LogLBSpacecraft, Warning,
							TEXT("SPACECRAFT: the starting ship factory "
								"could not be placed: %s"), *HallReason);
					}
				}
			}
			// THE SITE HUB - the outer screen, one painted picture of
			// the plant that the player clicks into. Below the panel
			// and top bar in Z so the interface still sits over it.
			SiteHub = CreateWidget<ULBSpacecraftSiteHubWidget>(
				PlayerController,
				ULBSpacecraftSiteHubWidget::StaticClass());
			if (SiteHub != nullptr)
			{
				SiteHub->BindGame(this);
				SiteHub->AddToViewport(20);
			}
			ULBSpacecraftObjectivesWidget* Objectives =
				CreateWidget<ULBSpacecraftObjectivesWidget>(
					PlayerController,
					ULBSpacecraftObjectivesWidget::StaticClass());
			if (Objectives != nullptr)
			{
				Objectives->BindGame(this);
				Objectives->AddToViewport(85);
			}
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("SPACECRAFT UI WIDGETS: TopBar=%d CommandPanel=%d SiteHub=%d Objectives=%d ViewportSize=%s"),
				TopBar != nullptr ? 1 : 0, CommandPanel != nullptr ? 1 : 0,
				SiteHub != nullptr ? 1 : 0, Objectives != nullptr ? 1 : 0,
				*World->GetGameViewport()->Viewport->GetSizeXY().ToString());
			// UI clicks and world clicks coexist: capture stays with the
			// game so the pawn keeps its camera and placement input.
			FInputModeGameAndUI InputMode;
			InputMode.SetHideCursorDuringCapture(false);
			PlayerController->SetInputMode(InputMode);
		}
	}
// (Car-era automation bridge removed with the 2026-09-01 cull;
	// spacecraft dev driving runs through LB.Spacecraft.* -ExecCmds.)

	// The STARTING LAND is not the starter spine's. It used to be
	// seeded inside SeedStarterSpine, so switching the spine off left
	// a player with ZERO bays and a "BUY THE BAY FIRST" refusal as
	// their first interaction - found by the sighted v008 first-launch
	// capture. An empty floor still comes with a starting plot;
	// SeedStartingBays refuses politely when land already exists
	// (loaded saves keep theirs).
	if (Progression != nullptr)
	{
		FString LandReason;
		if (Progression->SeedStartingBays(LandReason))
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("SPACECRAFT STARTING LAND: %s"), *LandReason);
		}
	}
	// The game opens EMPTY (owner, 2026-08-28: "already stuff in map"
	// was the first thing they rejected in a packaged launch). The
	// spine survives as a dev fixture behind LB.Spacecraft.SeedSpine.
	if (bSeedStarterSpine && World->GetGameViewport() != nullptr)
	{
		FString SpineReason;
		if (SeedStarterSpine(SpineReason))
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("SPACECRAFT STARTER SPINE: %s"), *SpineReason);
		}
		else
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("SPACECRAFT STARTER SPINE SKIPPED: %s"),
				*SpineReason);
		}
	}
	// -LineBossAutoShow: the scripted showcase (dev only). ExecCmds do
	// not reach the console in -game builds, so the flag drives the
	// same authority calls directly after the spine: canonical line,
	// commission, one Scout contract - then realtime does the rest.
	if (FParse::Param(FCommandLine::Get(), TEXT("LineBossAutoShow"))
		&& BuildAuthority != nullptr && Coordinator != nullptr
		&& ProductionAuthority != nullptr)
	{
		FString ShowReason;
		// -LineBossAutoShowRecipe=CARGO-01 overrides the showcase
		// contract (default Scout) so any recipe can run unattended.
		FString ShowRecipe = TEXT("SCOUT-01");
		FParse::Value(FCommandLine::Get(),
			TEXT("LineBossAutoShowRecipe="), ShowRecipe);
		const bool bMk2Show = ShowRecipe != TEXT("SCOUT-01");
		// A big-craft showcase walks the research tree the same way a
		// player would - banked points spent through UnlockNode, never
		// around the gate - so the Mk2 marks place legitimately.
		if (bMk2Show && ResearchAuthority != nullptr)
		{
			FString ResearchReason;
			ResearchAuthority->AddPoints(95, ResearchReason);
			for (const TCHAR* NodeId : { TEXT("Research.Mfg.T1"),
				TEXT("Research.Mfg.T2"), TEXT("Research.Mfg.Mk2") })
			{
				ResearchAuthority->UnlockNode(FName(NodeId),
					ResearchReason);
			}
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("AUTOSHOW RESEARCH: %s"), *ResearchReason);
		}
		// The showcase lays a demo track through the same authority the
		// player uses: start, straights, one turn EACH WAY, the cap -
		// every authored piece variant on screen (turn-mirroring proof).
		auto LayShowTrack = [this](FString& TrackReason)
		{
			// One implementation, called from here and from
			// LB.Spacecraft.BuildLine, so the console path cannot
			// silently drift away from the showcase again.
			return LayLineTrack(TrackReason);
		};
		auto StaffLine = [this](FString& StaffReason)
		{
			for (const FLBSpacecraftStationRecord& Record :
				BuildAuthority->GetStations())
			{
				const FLBSpacecraftStationDefinition* Definition =
					ALBSpacecraftBuildAuthority::FindDefinition(
						Record.DefinitionId);
				if (Definition == nullptr
					|| Definition->DroneSlotCount <= 0)
				{
					continue;
				}
				for (int32 Slot = 0; Slot < 2; ++Slot)
				{
					if (!InstallStationDronePowered(*BuildAuthority,
						Record.StationId, StaffReason,
						ProductionAuthority))
					{
						return false;
					}
				}
			}
			return true;
		};
		const bool bShow =
			SetupCanonicalLine(*BuildAuthority, ShowReason, bMk2Show)
			&& StockShowComponents(ShowReason)
			&& StaffLine(ShowReason)
			&& Coordinator->ConfigureFromAuthorities(BuildAuthority,
				ProductionAuthority, ShowReason)
			&& LayShowTrack(ShowReason)
			&& Coordinator->ConfigureFromAuthorities(BuildAuthority,
				ProductionAuthority, ShowReason, TrackAuthority)
			&& StartRecipeContract(*ProductionAuthority,
				FName(*ShowRecipe), 1, ShowReason);
		UE_LOG(LogLBSpacecraft, Display, TEXT("AUTOSHOW %s: %s"),
			bShow ? TEXT("RUNNING") : TEXT("REFUSED"), *ShowReason);
	}
	// ---- THE SHIP FACTORY IS ALREADY STANDING ----
	//
	// Owner 2026-08-29: the site opens with the ship factory placed, and
	// everything else is still the player's to build. He asked for this
	// after opening a packaged build and finding he could not play -
	// "cant play as theres no building on the site and cant select it".
	//
	// Only the ship factory. Power, storage, the dock, sub-assembly and
	// further factories stay player-built, so the land and expansion
	// systems keep their purpose.
	if (BuildAuthority != nullptr && PowerAuthority != nullptr
		&& InventoryAuthority != nullptr
		&& BuildAuthority->GetStations().Num() == 0)
	{
		// EMPTY SITE ONLY, so a loaded save is never overwritten, and
		// the autoshow is left alone because it lays its own line.
		FName HallId;
		FString PlaceReason;
		// NULL LEDGER = free. The starting building is a given, not a
		// purchase - but it still goes through the same authority,
		// power wiring and progression gate the player's own placements
		// use, so the opening state can never drift from what a player
		// could legally build.
		const bool bPlaced = PlaceStationPowered(
			*BuildAuthority, *PowerAuthority, *InventoryAuthority,
			FName(TEXT("ShipFactoryHall")),
			FTransform(FRotator::ZeroRotator, FVector::ZeroVector),
			HallId, PlaceReason, /*InLedger=*/nullptr, Progression);
		if (bPlaced)
		{
			FString LoadoutReason;
			const bool bLoadout = SeedShipFactoryLoadout(
				*BuildAuthority, *PowerAuthority, *InventoryAuthority,
				HallId, LoadoutReason, Progression, Coordinator,
				ProductionAuthority, TrackAuthority);
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("SPACECRAFT OPENING FACTORY %s: %s (%s)"),
				bLoadout ? TEXT("READY") : TEXT("LOADOUT SKIPPED"),
				*HallId.ToString(), *LoadoutReason);
		}
		else
		{
			// Logged as loudly as the success. A silent fail-closed
			// opening would leave the player on the bare plot this
			// change exists to remove, with nothing saying why.
			UE_LOG(LogLBSpacecraft, Warning,
				TEXT("SPACECRAFT OPENING FACTORY REFUSED: %s"),
				*PlaceReason);
		}
	}

	UE_LOG(LogLBSpacecraft, Display,
		TEXT("SPACECRAFT GAME MODE READY"));
}

bool ALBSpacecraftGameMode::StockShowComponents(FString& OutReason)
{
	// The showcase demonstrates the WHOLE loop unattended, and a craft
	// costs the six assembled components it is made of. A player buys
	// or fabricates them; the dev showcase is handed them.
	//
	// STOCKED AT THE STATIONS THAT FIT THEM, not on a floor store. The
	// showcase used to fill "Store.Floor" and worked - until stations
	// started eating from their OWN stockpiles (the owner's Production
	// Line model, 2026-08-27). After that the demo held mid-line
	// reading INSUFFICIENT RESOURCES forever: correct behaviour by the
	// line, a stale fixture underneath it. Found by finally watching
	// the showcase run rather than trusting that it still did.
	if (InventoryAuthority == nullptr || BuildAuthority == nullptr)
	{
		OutReason = TEXT("AUTOSHOW NEEDS THE INVENTORY AUTHORITY");
		return false;
	}
	const FName Floor = SiteOverflowStoreId();
	if (!InventoryAuthority->HasStore(Floor)
		&& !InventoryAuthority->RegisterStore(Floor, 5000, OutReason))
	{
		return false;
	}
	SyncStationStores(*BuildAuthority, *InventoryAuthority,
		CraftingAuthority);
	int32 Stocked = 0;
	for (const FLBSpacecraftStationRecord& Record :
		BuildAuthority->GetStations())
	{
		const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		if (!InventoryAuthority->HasStore(Stockpile))
		{
			continue;
		}
		for (const FName& Component : Record.AllocatedComponents)
		{
			if (InventoryAuthority->Deposit(Stockpile, Component, 4,
				OutReason))
			{
				++Stocked;
			}
		}
	}
	// The overflow yard keeps a set too, so the haulers have something
	// to top the shelves up with when the first craft has eaten theirs.
	for (uint8 Index = 0; Index < 6; ++Index)
	{
		const FName ItemId =
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(Index);
		if (!ItemId.IsNone())
		{
			InventoryAuthority->Deposit(Floor, ItemId, 4, OutReason);
		}
	}
	if (Stocked == 0)
	{
		OutReason = TEXT("AUTOSHOW STOCKED NOTHING - NO LINE STATION "
			"HAS A COMPONENT ALLOCATED");
		return false;
	}
	OutReason = FString::Printf(
		TEXT("AUTOSHOW STOCKED %d STATION SHELVES"), Stocked);
	return true;
}

double ALBSpacecraftGameMode::ContractAllowanceSeconds(
	const FLBSpacecraftRecipe& Recipe, int32 Quantity)
{
	double CycleSeconds = 0.0;
	double BottleneckSeconds = 0.0;
	for (const TPair<ELBSpacecraftStage, float>& Stage :
		Recipe.NominalCycleSeconds)
	{
		const double Seconds = FMath::Max(Stage.Value, 0.f);
		CycleSeconds += Seconds;
		BottleneckSeconds = FMath::Max(BottleneckSeconds, Seconds);
	}

	// THE GAME HAD NO CLOCK. Measured against this recipe, the old
	// formula - 1800 s plus ten times the craft's own work per unit -
	// gave 6200 s for a single Scout against a 440 s build. Fourteen
	// times the time needed, and eleven times even on a four-craft
	// order. Nothing the player did on the line had any time pressure
	// attached to it, which is a large hole in a factory game quite
	// apart from what it did to the quality-disposition choice: with
	// that much slack a rework costs nothing, so "put it right" is
	// always the answer and the decision is decorative.
	//
	// PIPELINED WALL-CLOCK, NOT WORK. The first craft takes a whole
	// build; every one after it emerges a single bottleneck cycle
	// later, because the line is a pipeline and not a queue of
	// sequential builds. Multiplying per-unit work by quantity - what
	// the old formula did - overstates a multi-craft order enormously
	// and is why the allowance ballooned with size.
	const int32 Units = FMath::Max(Quantity, 1);
	const double PipelinedSeconds =
		CycleSeconds + BottleneckSeconds * static_cast<double>(Units - 1);

	// A CONSTANT SLACK at every order size, so the disposition choice
	// behaves identically on one Scout and on an eight-craft run, and
	// the rework that threatens a deadline is always the same one.
	//
	// 300 s is a tight corridor and deliberately so: the largest rework
	// a craft can owe is 540 s, so slack has to sit near enough to that
	// for a bad craft to genuinely threaten delivery. Much more and
	// nothing ever threatens it; much less and ordinary variance makes
	// the player late through no fault of their own.
	constexpr double SlackSeconds = 300.0;
	const double Allowance = SlackSeconds + PipelinedSeconds;
	// How patient the customer is, is a difficulty dial.
	return Allowance * FMath::Max(
		FLBSpacecraftDifficulty::Current().DeadlineScale, 0.05f);
}

int32 ALBSpacecraftGameMode::OfferQuantityForSlot(int32 Slot)
{
	// A single, a pair and a run of four: enough spread that the choice
	// is about what the line can actually carry (PROVISIONAL).
	static const int32 Quantities[] = { 1, 2, 4 };
	return Quantities[FMath::Abs(Slot) % UE_ARRAY_COUNT(Quantities)];
}

int64 ALBSpacecraftGameMode::OfferUnitPricePence(int64 BasePence,
	int32 Quantity, int32 ReputationTier)
{
	if (BasePence <= 0)
	{
		return BasePence;
	}
	// Bulk pays less per craft, a one-off pays more: quantity is a
	// trade against what the line can carry, not a free multiplier.
	// PROVISIONAL: +8% for a single, -6% for four or more.
	int64 Price = BasePence;
	if (Quantity <= 1)
	{
		Price = Price * 108 / 100;
	}
	else if (Quantity >= 4)
	{
		Price = Price * 94 / 100;
	}
	// The reputation premium rides on top - the same one a directly
	// started contract gets - and what the work pays at all is a
	// difficulty dial.
	Price = static_cast<int64>(Price
		* FMath::Max(FLBSpacecraftDifficulty::Current().ContractPriceScale,
			0.05f));
	return ALBSpacecraftReputationAuthority::ApplyTierPremiumPence(Price,
		ReputationTier);
}

void ALBSpacecraftGameMode::RefreshOfferBoard()
{
	RefreshOfferBoard(MakeSaveContext());
}

void ALBSpacecraftGameMode::RefreshOfferBoard(
	const FLBSpacecraftSaveContext& InContext)
{
	ALBSpacecraftProductionAuthority* const ProductionAuthority =
		InContext.Production;
	ALBSpacecraftReputationAuthority* const Reputation =
		InContext.Reputation;
	if (ProductionAuthority == nullptr)
	{
		return;
	}
	int32 Standing = 0;
	for (const FLBSpacecraftContract& Contract :
		ProductionAuthority->GetContracts())
	{
		if (Contract.State == ELBSpacecraftContractState::Offered)
		{
			++Standing;
		}
	}
	if (Standing >= OfferBoardSize)
	{
		return;
	}
	const int32 Tier = Reputation != nullptr ? Reputation->GetTier() : 1;
	// Offer only what the customer would trust this yard with. The
	// reputation gate stays exactly where it was - this just stops the
	// board dangling work that would be refused on click.
	TArray<FName> Offerable;
	for (const FLBSpacecraftRecipe& Recipe :
		FLBSpacecraftProductionCatalog::CanonicalRecipes())
	{
		if (Tier >= Recipe.MinReputationTier)
		{
			Offerable.Add(Recipe.RecipeId);
		}
	}
	if (Offerable.Num() == 0)
	{
		return;
	}
	// Vary the terms by how many contracts the yard has ever seen, not
	// by how many offers happen to be standing. Using the standing
	// count meant a refill always landed on the same high slot, so the
	// board drifted to nothing but four-craft orders and the choice
	// went away.
	const int32 Seen = ProductionAuthority->GetContracts().Num();
	for (int32 Slot = Standing; Slot < OfferBoardSize; ++Slot)
	{
		const int32 Variant = Seen + Slot;
		const FName RecipeId = Offerable[Variant % Offerable.Num()];
		FLBSpacecraftRecipe Recipe;
		if (!FLBSpacecraftProductionCatalog::FindRecipe(RecipeId, Recipe))
		{
			continue;
		}
		FLBSpacecraftContract Offer;
		Offer.ContractId = ProductionAuthority->MintContractId();
		Offer.RecipeId = RecipeId;
		Offer.Quantity = OfferQuantityForSlot(Variant);
		Offer.PricePerUnitPence = OfferUnitPricePence(Recipe.RevenuePence,
			Offer.Quantity, Tier);
		// Customers want their craft BY a date. An offer nobody takes
		// rots off the board on the same clock, which keeps the board
		// turning over.
		Offer.DeadlineSimSeconds = ProductionAuthority->GetSimSeconds()
			+ ContractAllowanceSeconds(Recipe, Offer.Quantity);
		// Somebody actually wants this craft, and wants it in their
		// colours. Deterministic per offer so a reload rebuilds the
		// same board.
		const FLBSpacecraftCustomer& Customer =
			FLBSpacecraftCustomerCatalogue::CustomerForIndex(Variant);
		Offer.CustomerId = Customer.CustomerId;
		Offer.LiveryColour = Customer.LiveryColour;
		FString OfferReason;
		ProductionAuthority->OfferContract(Offer, OfferReason);
	}
}

void ALBSpacecraftGameMode::RaiseSimAlert(const FString& Alert)
{
	// Ignore repeats: this is raised from a per-tick path, and a
	// stalled machine complains every single tick.
	if (Alert.IsEmpty() || Alert == SimAlertText)
	{
		return;
	}
	SimAlertText = Alert;
	// Display, not Warning: this is the factory telling the PLAYER
	// something, not the engine reporting a fault, and a warning here
	// makes every suite that trips it "succeeded with warnings".
	UE_LOG(LogLBSpacecraft, Display, TEXT("SPACECRAFT ALERT: %s"), *Alert);
}

FString ALBSpacecraftGameMode::BuildBufferStallAlert(FName StationId,
	bool bAnyStorageRack)
{
	if (bAnyStorageRack)
	{
		return FString::Printf(
			TEXT("%s IS FULL AND WAITING FOR A HAULER DRONE"),
			*StationId.ToString());
	}
	// The honest version: nothing is coming, and here is why.
	return FString::Printf(
		TEXT("%s HAS STOPPED - ITS OUTPUT BUFFER IS FULL AND THERE IS NO ")
		TEXT("STORAGE RACK FOR A HAULER TO EMPTY IT INTO. BUILD A ")
		TEXT("STORAGE RACK"), *StationId.ToString());
}

int32 ALBSpacecraftGameMode::StockpileUnitsForItems(
	const TArray<FName>& Items, int32 TopUpUnits, int32 BaseUnits)
{
	int32 Needed = 0;
	for (const FName& ItemId : Items)
	{
		const FLBSpacecraftItemDefinition* Item =
			FLBSpacecraftItemCatalogue::FindItem(ItemId);
		Needed += FMath::Max(Item != nullptr ? Item->UnitVolume : 1, 1);
	}
	return FMath::Max(BaseUnits, Needed * FMath::Max(TopUpUnits, 1));
}

int32 ALBSpacecraftGameMode::SyncStationStores(
	const ALBSpacecraftBuildAuthority& InBuild,
	ALBSpacecraftInventoryAuthority& InInventory,
	const ALBSpacecraftCraftingAuthority* InCrafting)
{
	int32 Registered = 0;
	for (const FLBSpacecraftStationRecord& Record : InBuild.GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(Record.DefinitionId);
		if (Definition == nullptr)
		{
			continue;
		}
		const int32 Units = Definition->StorageCapacityUnits > 0
			? Definition->StorageCapacityUnits
			: Definition->InputStockpileUnits;
		if (Units <= 0)
		{
			continue;
		}
		const FName StoreId(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		if (InInventory.HasStore(StoreId))
		{
			continue;
		}
		FString Reason;
		if (InInventory.RegisterStore(StoreId, Units, Reason))
		{
			++Registered;
		}
	}
	// Then size every stockpile to the work it is actually doing. A
	// station's requirements change - components are allocated at
	// commissioning, a machine's recipe is chosen and re-chosen - so
	// the shelf is re-derived rather than fixed at placement.
	for (const FLBSpacecraftStationRecord& Record : InBuild.GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(Record.DefinitionId);
		if (Definition == nullptr || Definition->InputStockpileUnits <= 0)
		{
			continue;
		}
		TArray<FName> Needs = Record.AllocatedComponents;
		if (InCrafting != nullptr)
		{
			if (const FLBSpacecraftItemRecipe* Recipe =
				InCrafting->GetSelectedRecipe(Record.StationId))
			{
				for (const FLBSpacecraftItemStack& Input : Recipe->Inputs)
				{
					Needs.AddUnique(Input.ItemId);
				}
			}
		}
		if (Needs.Num() == 0)
		{
			continue;
		}
		const FName StoreId(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		const int32 Wanted = StockpileUnitsForItems(Needs,
			ALBSpacecraftDroneFleetAuthority::DefaultStockpileTopUpUnits(),
			Definition->InputStockpileUnits);
		if (InInventory.GetCapacityUnits(StoreId) < Wanted)
		{
			FString ResizeReason;
			InInventory.SetStoreCapacity(StoreId, Wanted, ResizeReason);
		}
	}
	return Registered;
}

void ALBSpacecraftGameMode::SyncLedgerDerivedAuthorities()
{
	SyncLedgerDerivedAuthorities(MakeSaveContext());
}

void ALBSpacecraftGameMode::SyncLedgerDerivedAuthorities(
	const FLBSpacecraftSaveContext& InContext)
{
	if (InContext.Reputation != nullptr)
	{
		InContext.Reputation->SyncFromLedger(InContext.Production);
	}
	if (InContext.Progression != nullptr)
	{
		InContext.Progression->SyncFromLedger(InContext.Production);
	}
	if (InContext.Research != nullptr)
	{
		// Delivering craft is how the factory learns. Without this the
		// only source of research points was a dev console command,
		// which left the whole tree - the crafting chain, the Mk2
		// marks and with them the second craft tier - unreachable
		// content the player could see costed and never afford.
		InContext.Research->SyncFromLedger(InContext.Production);
	}
	// The board is ledger-derived too, and it belongs INSIDE this one
	// call for the same reason everything else does: hung outside it,
	// the console journey never refreshed the board and it stayed
	// empty. One path, no drift.
	RefreshOfferBoard(InContext);
}

bool ALBSpacecraftGameMode::LayLineTrack(FString& TrackReason)
{
	if (TrackAuthority == nullptr || Coordinator == nullptr)
	{
		return true;
	}
	// RELAY WHEN THE TRACK NO LONGER COVERS THE LINE. This used to bail
	// out the moment ANY track existed, which is right for "do not lay
	// it twice" and wrong for "the line just grew". The autoshow lays a
	// short track at startup for the one station the player begins
	// with; LB.Spacecraft.BuildLine then adds five more, found track
	// already present, and returned success having done nothing. The
	// stations were attached to nothing, which runs fine and refuses to
	// LOAD.
	{
		TArray<FName> RouteStations;
		for (const FLBSpacecraftRouteStep& Step : Coordinator->GetRoute())
		{
			RouteStations.AddUnique(Step.StationId);
		}
		const TArray<FName> Attached =
			TrackAuthority->GetNodeStationsInOrder();
		bool bCovered = true;
		for (const FName& StationId : RouteStations)
		{
			if (!Attached.Contains(StationId))
			{
				bCovered = false;
				break;
			}
		}
		if (TrackAuthority->GetPieces().Num() > 0)
		{
			if (bCovered)
			{
				return true;
			}
			// Tear it down and lay it again to fit. Detach first: a
			// piece removed while a station still points at it would
			// leave a node referencing track that no longer exists,
			// which is the same broken shape by another route.
			for (const FName& StationId : Attached)
			{
				FString DetachReason;
				TrackAuthority->DetachStationNode(StationId,
					DetachReason);
			}
			while (TrackAuthority->GetPieces().Num() > 0)
			{
				if (!TrackAuthority->RemoveOpenEnd(TrackReason))
				{
					TrackReason = FString::Printf(
						TEXT("COULD NOT CLEAR THE OLD TRACK: %s"),
						*TrackReason);
					return false;
				}
			}
		}
	}
		// THE STATIONS FIRST, THEN TRACK SIZED TO THEM. This used
		// to lay a fixed seven-piece list holding four straights
		// and attach one station per straight - which silently
		// removed the ENTIRE track the moment the line grew past
		// four stations. Going to six (owner, 2026-08-29) tripped
		// exactly that, and the symptom was not a missing track: it
		// was LOAD REFUSED, because a saved line whose stations are
		// attached to nothing fails restore validation. A save you
		// cannot load is worse than no save button at all.
		//
		// The route is the ground truth here. The canonical build
		// carries MORE line-class stations than the route uses
		// (base plus Mk2 marks), and the coordinator was configured
		// without the track just before this, so its route says
		// which stations actually need a node.
		TArray<FName> LineStations;
		for (const FLBSpacecraftRouteStep& Step :
		Coordinator->GetRoute())
		{
		if (LineStations.Num() == 0
			|| LineStations.Last() != Step.StationId)
		{
			LineStations.AddUnique(Step.StationId);
		}
		}

		FName PieceId;
		if (!TrackAuthority->StartLine(
		FTransform(FRotator(0.f, 90.f, 0.f),
			FVector(2400.f, -7000.f, 0.f)), PieceId, TrackReason))
		{
		return false;
		}
		// One straight per station that needs a node, then a turn
		// each way and the cap - the turns are kept because they
		// put every authored piece variant on screen and prove the
		// turn mirrors, which was the point of the demo track.
		TArray<ELBSpacecraftTrackPiece> ShowPieces;
		for (int32 Node = 0; Node < LineStations.Num(); ++Node)
		{
		ShowPieces.Add(ELBSpacecraftTrackPiece::Straight);
		}
		ShowPieces.Add(ELBSpacecraftTrackPiece::TurnLeft);
		ShowPieces.Add(ELBSpacecraftTrackPiece::Straight);
		ShowPieces.Add(ELBSpacecraftTrackPiece::TurnRight);
		ShowPieces.Add(ELBSpacecraftTrackPiece::End);
		TArray<FName> StraightPieces;
		for (ELBSpacecraftTrackPiece ShowPiece : ShowPieces)
		{
		if (!TrackAuthority->ExtendLine(ShowPiece, PieceId,
			TrackReason))
		{
			// Out of track nodes or off the floor. Say which,
			// and leave the partial track rather than silently
			// binning it - a short track is visible and
			// diagnosable; a vanished one is neither.
			TrackReason = FString::Printf(
				TEXT("SHOW TRACK STOPPED AT %d/%d PIECES: %s"),
				StraightPieces.Num(), ShowPieces.Num(),
				*TrackReason);
			return false;
		}
		if (ShowPiece == ELBSpacecraftTrackPiece::Straight)
		{
			StraightPieces.Add(PieceId);
		}
		}
		for (int32 Node = 0; Node < LineStations.Num(); ++Node)
		{
		if (!TrackAuthority->AttachStationNode(
			LineStations[Node], StraightPieces[Node],
			BuildAuthority, TrackReason))
		{
			return false;
		}
		}
		return true;
}

bool ALBSpacecraftGameMode::SetupCanonicalLine(
	ALBSpacecraftBuildAuthority& InBuild, FString& OutReason,
	bool bMk2Line)
{
	// One of each class in a row down +Y, gaps sized to the footprints.
	// No test bay: the craft self-starts at the end of the line
	// (owner 2026-08-26).
	// Mk1 line for the Scout; the Mk2 marks (wider footprints, bigger
	// craft envelopes) when the showcase runs a craft the Mk1 stations
	// would refuse fail-closed - e.g. the 21 m Cargo-01.
	// ONE repeated station type (owner 2026-08-27): four assembly
	// stations in a row ARE the canonical line. The count is taste -
	// the route takes however many stand.
	// SIX STATIONS INCLUDING THE BOOTH (owner 2026-08-29): five fitting
	// stations and the spray booth that closes the line. Six is also
	// where the current craft stops paying - the fixing order is six
	// components, so a seventh station would pass through fitting
	// nothing until the parts catalogue splits finer.
	const TCHAR* Mk1Classes[] = {
		TEXT("AssemblyRobot"), TEXT("AssemblyRobot"),
		TEXT("AssemblyRobot"), TEXT("AssemblyRobot"),
		TEXT("AssemblyRobot") };
	const TCHAR* Mk2Classes[] = {
		TEXT("AssemblyRobotMk2"), TEXT("AssemblyRobotMk2"),
		TEXT("AssemblyRobotMk2"), TEXT("AssemblyRobotMk2"),
		TEXT("AssemblyRobotMk2") };
	// THE HALL FIRST. Interior buildings are legal only inside a placed
	// site building (owner 2026-08-28), so the canonical line begins by
	// placing the ship factory the player would place on the world map
	// - the fixture builds what a player builds, in the same order.
	{
		FName HallId;
		if (!InBuild.PlaceStarterHall(HallId, OutReason))
		{
			return false;
		}
	}
	// CLEAR THE FLOOR FIRST (owner 2026-08-29: "clear the map").
	// A ship factory now opens with a STARTING LOADOUT already standing
	// in it, so this command - written before that existed - was laying
	// its line on top and being refused by the overlap gate for
	// colliding with the station the game had just given the player.
	// Removing the interior stations first makes it idempotent: run it
	// twice and you get one line, not a refusal.
	{
		TArray<FName> ToClear;
		for (const FLBSpacecraftStationRecord& Record :
			InBuild.GetStations())
		{
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			// Site buildings stay - the hall is the floor this line
			// stands on, and demolishing it would take the line with it.
			if (Definition != nullptr && !Definition->bSiteBuilding)
			{
				ToClear.Add(Record.StationId);
			}
		}
		for (const FName& StationId : ToClear)
		{
			FString ClearReason;
			InBuild.RemoveStation(StationId, ClearReason);
		}
	}
	// CENTRED IN THE HALL: the line has to fit the ship factory's
	// interior floor now that the building is a real 120 m footprint
	// rather than the whole plot.
	// Centred on the hall for six nodes rather than five.
	float Y = -4000.f;
	// Tightened to the Car Manufacture density (owner 2026-08-26
	// evening, "more like this"): gaps of ~4-6 m between stations
	// instead of ~9-11. The build authority's overlap gate still rules.
	const float Step = bMk2Line ? 2200.f : 1600.f;
	for (int32 Index = 0; Index < 5; ++Index)
	{
		const TCHAR* ClassId =
			bMk2Line ? Mk2Classes[Index] : Mk1Classes[Index];
		FName StationId;
		if (!InBuild.PlaceStation(FName(ClassId),
			FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
			StationId, OutReason))
		{
			return false;
		}
		// The canonical line is a WORKING factory, so it is crewed to
		// nominal. Two drones is the work-bonus curve's 1.0x point and
		// the point at which a station fits parts cleanly - an
		// uncrewed line builds defective craft by design, and this
		// demo/showcase line is not what that lesson is for. No ledger
		// is threaded here, so the demo crew is uncharged; the
		// player's own stations buy their drones.
		for (int32 Crew = 0; Crew < 2; ++Crew)
		{
			FString CrewReason;
			if (!InBuild.InstallStationDrone(StationId, CrewReason))
			{
				OutReason = CrewReason;
				return false;
			}
		}
		Y += Step;
	}
	// THE SPRAY BOOTH closes the line (owner 2026-08-28: required).
	// At the END, downstream of every fitting station, because a craft
	// painted before its parts go on would have them bolted onto a wet
	// finish. The canonical line is what a player would build, so it
	// gets the booth a player cannot commission without.
	{
		FName BoothId;
		// The booth is 18 m across its own Y where a fitting station is
		// 14, so the last gap needs more than the station pitch or the
		// two land exactly edge to edge - legal, but with no room for
		// the crane that has to work between them.
		Y += 400.f;
		if (!InBuild.PlaceStation(FName(TEXT("SprayBooth")),
			FTransform(FRotator::ZeroRotator, FVector(0.f, Y, 0.f)),
			BoothId, OutReason))
		{
			return false;
		}
		for (int32 Crew = 0; Crew < 2; ++Crew)
		{
			FString CrewReason;
			InBuild.InstallStationDrone(BoothId, CrewReason,
				FName(TEXT("Spray")));
		}
	}
	return InBuild.CommissionFactory(OutReason);
}

bool ALBSpacecraftGameMode::SetupEconomy(ALBSpacecraftBuildAuthority& InBuild,
	ALBSpacecraftPowerAuthority& InPower,
	ALBSpacecraftInventoryAuthority& InInventory,
	ALBSpacecraftCraftingAuthority& InCrafting,
	ALBSpacecraftResearchAuthority& InResearch,
	ALBSpacecraftProductionAuthority& InLedger,
	ALBSpacecraftProgressionAuthority* InProgression,
	int32 CraftTarget, FString& OutReason)
{
	if (!InBuild.IsCommissioned())
	{
		OutReason = TEXT("BUILD AND COMMISSION THE LINE FIRST ")
			TEXT("(LB.Spacecraft.BuildLine)");
		return false;
	}
	CraftTarget = FMath::Clamp(CraftTarget, 1, 20);

	// Research: the whole tree, through the normal spend. The chain's
	// machine families sit at several tiers and this fixture exists to
	// run the chain, not to prove the tree's pacing (which has its own
	// tests).
	{
		FString GrantReason;
		InResearch.AddPoints(100000, GrantReason);
		bool bProgress = true;
		while (bProgress)
		{
			bProgress = false;
			for (const FLBSpacecraftResearchNode& Node :
				FLBSpacecraftResearchCatalogue::GetNodeTable())
			{
				FString NodeReason;
				if (!InResearch.IsNodeUnlocked(Node.NodeId)
					&& InResearch.UnlockNode(Node.NodeId, NodeReason))
				{
					bProgress = true;
				}
			}
		}
	}

	// Land: every purchasable bay. The floor is CENTRED - bays index
	// -2..1 on each axis - and purchases must touch owned land, so the
	// sweep repeats until a pass buys nothing. PurchaseBay refuses
	// runway land and already-owned bays on its own; those refusals
	// are expected, not errors. Uncharged like the construction below.
	if (InProgression != nullptr)
	{
		bool bBought = true;
		while (bBought)
		{
			bBought = false;
			// The starting plot the game seeds (SeedStartingBays), plus
			// whatever else is buyable - fixtures run without the game
			// mode's BeginPlay, so they buy their own ground.
			for (int32 BayX = -4; BayX <= 3; ++BayX)
			{
				for (int32 BayY = -4; BayY <= 3; ++BayY)
				{
					FString BayReason;
					if (InProgression->PurchaseBay(FIntPoint(BayX, BayY),
						nullptr, BayReason))
					{
						bBought = true;
					}
				}
			}
		}
	}

	// Placement scans the RIGHT GROUND for the kind of thing being
	// placed (owner 2026-08-28, the world map): a site building goes on
	// open ground across the plot, an interior building goes on the
	// ship factory's own floor. Deterministic order; the refusal tally
	// separates "the ground is full" from "a gate said no".
	FVector HallCentre = FVector::ZeroVector;
	FVector2D HallFloor = FVector2D::ZeroVector;
	for (const FLBSpacecraftStationRecord& Record : InBuild.GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record.DefinitionId);
		if (Definition != nullptr && Definition->bSiteBuilding
			&& !Definition->InteriorFloorCm.IsNearlyZero())
		{
			HallCentre = Record.WorldTransform.GetLocation();
			HallFloor = Definition->InteriorFloorCm;
			break;
		}
	}
	auto TryPlace = [&InBuild, &InPower, &InInventory, InProgression,
		HallCentre, HallFloor](
		FName DefinitionId, FName& OutStationId, FString& OutPlaceReason)
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(DefinitionId);
		const bool bSite = Definition != nullptr
			&& Definition->bSiteBuilding;
		const FVector Centre = bSite ? FVector::ZeroVector : HallCentre;
		const FVector2D Span = bSite
			? FVector2D(42000.f, 42000.f) : HallFloor;
		if (Span.IsNearlyZero())
		{
			OutPlaceReason = TEXT("NO SHIP FACTORY STANDS - NOTHING ")
				TEXT("CAN BE BUILT INSIDE ONE");
			return false;
		}
		TMap<FString, int32> RefusalTally;
		FString LastRefusal;
		const float StepCm = bSite ? 2000.f : 1000.f;
		// INSET by the building's own half footprint: a scan that
		// offers centres right up to the edge spends most of its
		// attempts on spots where the building would hang off the
		// ground it is allowed to stand on.
		const FVector2D Inset = Definition != nullptr
			? Definition->FootprintCm * 0.5f : FVector2D::ZeroVector;
		for (float X = Centre.X - Span.X * 0.5f + Inset.X;
			X <= Centre.X + Span.X * 0.5f - Inset.X; X += StepCm)
		{
			for (float Y = Centre.Y - Span.Y * 0.5f + Inset.Y;
				Y <= Centre.Y + Span.Y * 0.5f - Inset.Y; Y += StepCm)
			{
				if (PlaceStationPowered(InBuild, InPower, InInventory,
					DefinitionId,
					FTransform(FRotator::ZeroRotator, FVector(X, Y, 0.f)),
					OutStationId, LastRefusal, nullptr, InProgression))
				{
					return true;
				}
				++RefusalTally.FindOrAdd(LastRefusal.Left(18));
			}
		}
		FString Tally;
		for (const TPair<FString, int32>& Kind : RefusalTally)
		{
			Tally += FString::Printf(TEXT(" [%s]x%d"), *Kind.Key,
				Kind.Value);
		}
		OutPlaceReason = FString::Printf(
			TEXT("NO LEGAL SPOT LEFT FOR %s (%d STATIONS STAND;")
			TEXT("%s; LAST: %s)"), *DefinitionId.ToString(),
			InBuild.GetStations().Num(), *Tally, *LastRefusal);
		return false;
	};

	// MAKE-VS-BUY, forced by the floor. Fabricating all six components
	// from ore needs a machine per distinct recipe - measured at
	// upwards of ninety machines for one craft, which does not fit the
	// 220 m floor at Mk1 sizes. That is not a fixture bug, it is the
	// economy's real shape: the import price list exists precisely so
	// a yard fabricates SOME chains and buys the rest. This fixture
	// fabricates the HULL's whole chain from raw ore (the deepest,
	// heaviest chain) and imports the other five components through
	// the same dock the raws arrive at.
	// ON-SITE FABRICATION is a delivery milestone: a young yard
	// assembles from imported components, and earns its parts factory
	// after a couple of deliveries. When the milestone is still locked
	// this builds the IMPORT ECONOMY (all six components ordered, no
	// machines) - which is exactly the intended early game, not a
	// degraded fixture. Run the command again after the unlock and it
	// adds the hull fabrication chain.
	if (InProgression != nullptr)
	{
		// Normally the game-mode tick keeps the credit count synced;
		// inside a single-frame -ExecCmds chain that tick never runs,
		// so a delivery earned two commands ago would still read as
		// locked here. The check reads fresh state on purpose.
		InProgression->SyncFromLedger(&InLedger);
	}
	const bool bFabricationOpen = InProgression == nullptr
		|| InProgression->IsUnlocked(ELBSpacecraftUnlock::Fabrication);
	TArray<FLBSpacecraftPlannedRun> Plan;
	TMap<FName, int32> RawNeed;
	if (bFabricationOpen)
	{
		TMap<FName, int32> Targets;
		Targets.Add(
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(0),
			CraftTarget);
		if (!FLBSpacecraftRecipeCatalogue::PlanBuild(Targets, Plan,
			RawNeed, OutReason))
		{
			return false;
		}
	}
	else
	{
		RawNeed.Add(
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(0),
			CraftTarget);
	}
	// The bought half of the bill of materials rides the same order
	// pipeline as the ore.
	for (uint8 Index = 1; Index < 6; ++Index)
	{
		RawNeed.Add(
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(Index),
			CraftTarget);
	}
	// One MACHINE per distinct recipe, its standing order the summed
	// cycles. The sim's own scheduling replaces the plan's ordering -
	// a machine whose inputs are not made yet simply stalls with a
	// named reason until the haulers bring them, which is the honest
	// behaviour this fixture exists to soak.
	struct FLBSpacecraftMachineWant
	{
		FName StationClassId;
		int32 Cycles = 0;
	};
	TMap<FName, FLBSpacecraftMachineWant> Machines;
	for (const FLBSpacecraftPlannedRun& Run : Plan)
	{
		FLBSpacecraftMachineWant& Want = Machines.FindOrAdd(Run.RecipeId);
		Want.StationClassId = Run.StationClassId;
		Want.Cycles += Run.Cycles;
	}

	// Power BEFORE machines: installs are power-wired and fail closed.
	int32 DrawKw = 0;
	for (const TPair<FName, FLBSpacecraftMachineWant>& Machine : Machines)
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Machine.Value.StationClassId);
		if (Definition == nullptr)
		{
			OutReason = FString::Printf(
				TEXT("RECIPE %s NAMES UNKNOWN MACHINE CLASS %s"),
				*Machine.Key.ToString(),
				*Machine.Value.StationClassId.ToString());
			return false;
		}
		DrawKw += Definition->PowerDrawKw;
	}
	while (InPower.GetHeadroomKw() < DrawKw)
	{
		FName PowerHallId;
		if (!TryPlace(FName(TEXT("PowerStation")), PowerHallId, OutReason))
		{
			return false;
		}
		const FLBSpacecraftStationDefinition* PowerDefinition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				FName(TEXT("PowerStation")));
		const int32 PowerSlots = PowerDefinition != nullptr
			&& PowerDefinition->SlotCount > 0
				? PowerDefinition->SlotCount : 4;
		for (int32 Slot = 0; Slot < PowerSlots
			&& InPower.GetHeadroomKw() < DrawKw; ++Slot)
		{
			FName PlantId;
			if (!InstallInSlotPowered(InBuild, InPower, PowerHallId,
				FName(TEXT("PowerPlant")), PlantId, OutReason, nullptr,
				&InInventory))
			{
				return false;
			}
		}
	}

	// Halls, sized by what a parts factory actually holds rather than
	// by a number copied here.
	const FLBSpacecraftStationDefinition* HallDefinition =
		ALBSpacecraftBuildAuthority::FindDefinition(
			FName(TEXT("SubAssemblyHall")));
	const int32 SlotsPerHall = HallDefinition != nullptr
		&& HallDefinition->SlotCount > 0 ? HallDefinition->SlotCount : 4;
	const int32 HallCount =
		FMath::DivideAndRoundUp(Machines.Num(), SlotsPerHall);
	TArray<FName> HallIds;
	for (int32 Hall = 0; Hall < HallCount; ++Hall)
	{
		FName HallId;
		if (!TryPlace(FName(TEXT("SubAssemblyHall")), HallId, OutReason))
		{
			return false;
		}
		HallIds.Add(HallId);
	}
	int32 MachineIndex = 0;
	for (const TPair<FName, FLBSpacecraftMachineWant>& Machine : Machines)
	{
		const FName HallId = HallIds[MachineIndex / SlotsPerHall];
		++MachineIndex;
		FName StationId;
		if (!InstallInSlotPowered(InBuild, InPower, HallId,
			Machine.Value.StationClassId, StationId, OutReason, nullptr,
			&InInventory))
		{
			return false;
		}
		if (!SelectStationRecipe(InBuild, InCrafting, InResearch,
			StationId, Machine.Key, OutReason))
		{
			return false;
		}
		// Cycles DOUBLED, matching the raw headroom below - and not as
		// polish. With exact one-shot orders the site deadlocks: the
		// FrameStock mill starves on LightAlloy while every unit of
		// LightAlloy sits hoarded on shelves of machines that are
		// themselves waiting for FrameStock, and nothing reclaims from
		// a shelf. Float is what breaks the cycle. A future demand
		// scheduler could do it with less waste; the finding is
		// recorded in the self-feeding test's starvation dumps.
		if (!InCrafting.AddOrder(StationId, Machine.Value.Cycles * 2,
			OutReason))
		{
			return false;
		}
	}

	// Storage between the two factories, and a dock for the inbound
	// raws if the site does not already have one.
	for (int32 Rack = 0; Rack < 2; ++Rack)
	{
		FName RackId;
		if (!TryPlace(FName(TEXT("StorageRack")), RackId, OutReason))
		{
			return false;
		}
	}
	FName DockId = NAME_None;
	for (const FLBSpacecraftStationRecord& Record : InBuild.GetStations())
	{
		if (Record.DefinitionId == FName(TEXT("DeliveryDock")))
		{
			DockId = Record.StationId;
			break;
		}
	}
	if (DockId.IsNone())
	{
		if (!TryPlace(FName(TEXT("DeliveryDock")), DockId, OutReason))
		{
			return false;
		}
	}
	SyncStationStores(InBuild, InInventory, &InCrafting);

	// The feedstock is CHARGED: raw spend against contract income is
	// half of what a soak of this economy is for. RAWS are bought with
	// headroom, deliberately: the haulers top stockpiles up without
	// knowing the whole plan, so a shared input (Silicon feeds several
	// smelting recipes) can strand in the wrong machine's stockpile -
	// and with exact quantities a stranded unit starves the real
	// consumer forever. A real yard over-buys cheap feedstock for the
	// same reason. The imported components stay exact: each is wanted
	// by exactly one line station, so nothing can strand.
	const FName DockStore(*FString::Printf(TEXT("Store.%s"),
		*DockId.ToString()));
	for (const TPair<FName, int32>& Raw : RawNeed)
	{
		const bool bComponent =
			Raw.Key.ToString().StartsWith(TEXT("Component."));
		int32 Count = bComponent ? Raw.Value : Raw.Value * 2 + 8;
		// TRUCKLOADS, not one bulk order. Deliveries land whole into
		// the dock's finite hold, so a single order bigger than the
		// room the dock ever has simply retries forever - a three-
		// craft ore order (~370 units against a 400-unit dock shared
		// with everything else) starved the whole fabrication phase
		// with "pending orders 1". Chunks of 40 trickle through as
		// the haulers drain the dock.
		while (Count > 0)
		{
			const int32 Chunk = FMath::Min(Count, 40);
			if (!PlaceResourceOrder(InInventory, InLedger, Raw.Key,
				Chunk, DockStore, OutReason))
			{
				return false;
			}
			Count -= Chunk;
		}
	}

	OutReason = FString::Printf(
		TEXT("ECONOMY READY (%s): %d machines in %d halls, %d recipes ")
		TEXT("ordered, %d order kinds inbound at the dock, headroom ")
		TEXT("%d kW"),
		bFabricationOpen ? TEXT("HULL FABRICATED, REST IMPORTED")
			: TEXT("ALL IMPORTED - FABRICATION STILL LOCKED"),
		Machines.Num(), HallIds.Num(), Machines.Num(), RawNeed.Num(),
		InPower.GetHeadroomKw());
	return true;
}

bool ALBSpacecraftGameMode::StartScoutContract(
	ALBSpacecraftProductionAuthority& InProduction, int32 Quantity,
	FString& OutReason)
{
	return StartRecipeContract(InProduction, FName(TEXT("SCOUT-01")),
		Quantity, OutReason);
}

bool ALBSpacecraftGameMode::StartRecipeContract(
	ALBSpacecraftProductionAuthority& InProduction, FName RecipeId,
	int32 Quantity, FString& OutReason,
	ALBSpacecraftReputationAuthority* InReputation)
{
	FLBSpacecraftRecipe Recipe;
	if (!FLBSpacecraftProductionCatalog::FindRecipe(RecipeId, Recipe))
	{
		OutReason = FString::Printf(TEXT("UNKNOWN RECIPE %s"),
			*RecipeId.ToString());
		return false;
	}
	if (InReputation != nullptr
		&& InReputation->GetTier() < Recipe.MinReputationTier)
	{
		OutReason = FString::Printf(
			TEXT("REPUTATION TIER %d REQUIRED FOR %s - YOU ARE TIER %d. ")
			TEXT("DELIVER CONTRACTS TO BUILD YOUR NAME"),
			Recipe.MinReputationTier, *RecipeId.ToString(),
			InReputation->GetTier());
		return false;
	}

	FLBSpacecraftContract Contract;
	// Review fix: the ledger mints ids (a static counter was process
	// state and reused ids after load).
	Contract.ContractId = InProduction.MintContractId();
	Contract.RecipeId = RecipeId;
	Contract.Quantity = FMath::Max(Quantity, 1);
	// A NAME IS WORTH MONEY. Customers pay a trusted builder more, so
	// the price is set when the contract is taken, at the tier you hold
	// then. Without this a reputation tier bought nothing except
	// permission to click the Cargo button.
	Contract.DeadlineSimSeconds = InProduction.GetSimSeconds()
		+ ContractAllowanceSeconds(Recipe, Contract.Quantity);
	Contract.PricePerUnitPence = InReputation != nullptr
		? ALBSpacecraftReputationAuthority::ApplyTierPremiumPence(
			Recipe.RevenuePence, InReputation->GetTier())
		: Recipe.RevenuePence;
	if (!InProduction.OfferContract(Contract, OutReason))
	{
		return false;
	}
	return InProduction.AcceptContract(Contract.ContractId, OutReason);
}

ALBSpacecraftGameMode* ALBSpacecraftGameMode::FindInWorld(UWorld* World)
{
	return World != nullptr
		? Cast<ALBSpacecraftGameMode>(World->GetAuthGameMode()) : nullptr;
}

bool ALBSpacecraftGameMode::IsKnownSimSpeed(const float Scale)
{
	return Scale == 0.f || Scale == 1.f || Scale == 2.f || Scale == 4.f;
}

bool ALBSpacecraftGameMode::SetSimSpeed(const float NewScale,
	FString& OutReason)
{
	if (!IsKnownSimSpeed(NewScale))
	{
		OutReason = FString::Printf(
			TEXT("%.1fx IS NOT A FACTORY SPEED (0 / 1 / 2 / 4)"), NewScale);
		return false;
	}
	SimTimeScale = NewScale;
	OutReason = FString::Printf(TEXT("FACTORY SPEED %s"),
		NewScale == 0.f ? TEXT("PAUSED")
			: *FString::Printf(TEXT("%.0fx"), NewScale));
	return true;
}

FText ALBSpacecraftGameMode::DescribeSimSpeed() const
{
	if (SimTimeScale == 0.f)
	{
		return NSLOCTEXT("LBSpacecraftGameMode", "SpeedPaused", "PAUSED");
	}
	if (SimTimeScale == 2.f)
	{
		return NSLOCTEXT("LBSpacecraftGameMode", "Speed2x", "2x");
	}
	if (SimTimeScale == 4.f)
	{
		return NSLOCTEXT("LBSpacecraftGameMode", "Speed4x", "4x");
	}
	return NSLOCTEXT("LBSpacecraftGameMode", "Speed1x", "1x");
}

bool ALBSpacecraftGameMode::QuickSave(FString& OutReason)
{
	if (!FLBSpacecraftSavePipeline::SaveToSlot(MakeSaveContext(),
		TEXT("SpacecraftSlot1"), OutReason))
	{
		return false;
	}
	OutReason = TEXT("SAVED - SLOT 1");
	return true;
}

bool ALBSpacecraftGameMode::QuickLoad(FString& OutReason)
{
	if (!FLBSpacecraftSavePipeline::LoadFromSlot(MakeSaveContext(),
		TEXT("SpacecraftSlot1"), OutReason))
	{
		return false;
	}
	OutReason = TEXT("LOADED - SLOT 1");
	return true;
}

void ALBSpacecraftGameMode::OpenSettingsMenu()
{
	APlayerController* PlayerController =
		GetWorld() != nullptr
			? GetWorld()->GetFirstPlayerController() : nullptr;
	if (PlayerController == nullptr)
	{
		return;
	}
	if (SettingsMenu == nullptr)
	{
		SettingsMenu = CreateWidget<ULBSpacecraftSettingsWidget>(
			PlayerController, ULBSpacecraftSettingsWidget::StaticClass());
		if (SettingsMenu == nullptr)
		{
			return;
		}
		SettingsMenu->OnCloseRequested.BindWeakLambda(this, [this]()
		{
			if (SettingsMenu != nullptr)
			{
				SettingsMenu->RemoveFromParent();
			}
		});
	}
	if (!SettingsMenu->IsInViewport())
	{
		SettingsMenu->AddToViewport(210);
	}
}

void ALBSpacecraftGameMode::CyclePanelTab(const int32 Direction)
{
	if (CommandPanel != nullptr)
	{
		CommandPanel->CycleTab(Direction);
	}
}

FLBSpacecraftSaveContext ALBSpacecraftGameMode::MakeSaveContext() const
{
	FLBSpacecraftSaveContext Context;
	Context.Build = BuildAuthority;
	Context.Production = ProductionAuthority;
	Context.Coordinator = Coordinator;
	Context.Inventory = InventoryAuthority;
	Context.Crafting = CraftingAuthority;
	Context.Power = PowerAuthority;
	Context.Research = ResearchAuthority;
	// Schema v4 regression fix: these two were never set, so the LIVE
	// Save command failed closed while the suite's full rigs passed.
	Context.DroneFleet = DroneFleet;
	Context.Reputation = Reputation;
	Context.Transport = Transport;
	Context.Progression = Progression;
	Context.Track = TrackAuthority;
	return Context;
}

bool ALBSpacecraftGameMode::PlaceStationPowered(
	ALBSpacecraftBuildAuthority& InBuild, ALBSpacecraftPowerAuthority& InPower,
	ALBSpacecraftInventoryAuthority& InInventory, FName DefinitionId,
	const FTransform& Transform, FName& OutStationId, FString& OutReason,
	ALBSpacecraftProductionAuthority* InLedger,
	ALBSpacecraftProgressionAuthority* InProgression)
{
	OutStationId = NAME_None;
	const FLBSpacecraftStationDefinition* Definition =
		ALBSpacecraftBuildAuthority::FindDefinition(DefinitionId);
	if (Definition == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STATION FAMILY %s"),
			*DefinitionId.ToString());
		return false;
	}
	// Land gate (research: bays are bought): the footprint must lie in
	// owned bays. Rigs without a progression authority are ungated.
	if (InProgression != nullptr
		&& !InProgression->IsFootprintOwned(Transform.GetLocation(),
			Definition->FootprintCm, OutReason))
	{
		return false;
	}
	// Money first (owner-endorsed vision: the loop has stakes): with a
	// ledger, the station's price is charged fail-closed BEFORE anything
	// is placed; every later wiring failure refunds it in the unwind.
	if (InLedger != nullptr
		&& !InLedger->SpendPence(Definition->CostPence, OutReason))
	{
		return false;
	}
	// The research gate runs inside PlaceStation.
	if (!InBuild.PlaceStation(DefinitionId, Transform, OutStationId,
		OutReason))
	{
		if (InLedger != nullptr)
		{
			FString Ignored;
			InLedger->EarnPence(Definition->CostPence, Ignored);
		}
		return false;
	}
	// Wiring order: supply first, store second, draw last - and any
	// failure unwinds EVERYTHING done so far. A station is never left
	// half-connected.
	bool bSupplyRegistered = false;
	bool bStoreRegistered = false;
	const FName StoreId(*FString::Printf(TEXT("Store.%s"),
		*OutStationId.ToString()));
	auto Unwind = [&](const FString& WhyRefused)
	{
		FString Ignored;
		if (bStoreRegistered)
		{
			InInventory.RemoveStore(StoreId, Ignored);
		}
		if (bSupplyRegistered)
		{
			InPower.RemoveSupply(OutStationId, Ignored);
		}
		InBuild.RemoveStation(OutStationId, Ignored);
		if (InLedger != nullptr)
		{
			InLedger->EarnPence(Definition->CostPence, Ignored);
		}
		OutStationId = NAME_None;
		OutReason = WhyRefused;
	};
	if (Definition->PowerSupplyKw > 0)
	{
		FString SupplyReason;
		if (!InPower.RegisterSupply(OutStationId,
			Definition->PowerSupplyKw, SupplyReason))
		{
			Unwind(SupplyReason);
			return false;
		}
		bSupplyRegistered = true;
	}
	// A station's store is either BULK (a storage rack) or a local
	// STOCKPILE beside a machine that consumes materials. Both are
	// ordinary inventory stores, which is what lets a delivery drone
	// move goods between them with a plain Transfer.
	const int32 StoreUnits = Definition->StorageCapacityUnits > 0
		? Definition->StorageCapacityUnits
		: Definition->InputStockpileUnits;
	if (StoreUnits > 0)
	{
		FString StoreReason;
		if (!InInventory.RegisterStore(StoreId, StoreUnits, StoreReason))
		{
			Unwind(StoreReason);
			return false;
		}
		bStoreRegistered = true;
	}
	if (Definition->PowerDrawKw > 0)
	{
		FString PowerReason;
		if (!InPower.ConnectLoad(OutStationId,
			Definition->PowerDrawKw, PowerReason))
		{
			Unwind(PowerReason);
			return false;
		}
	}
	return true;
}

bool ALBSpacecraftGameMode::InstallInSlotPowered(
	ALBSpacecraftBuildAuthority& InBuild,
	ALBSpacecraftPowerAuthority& InPower, FName HostStationId,
	FName UnitDefinitionId, FName& OutStationId, FString& OutReason,
	ALBSpacecraftProductionAuthority* InLedger,
	ALBSpacecraftInventoryAuthority* InInventory)
{
	OutStationId = NAME_None;
	const FLBSpacecraftStationDefinition* Definition =
		ALBSpacecraftBuildAuthority::FindDefinition(UnitDefinitionId);
	if (Definition == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN UNIT FAMILY %s"),
			*UnitDefinitionId.ToString());
		return false;
	}
	if (InLedger != nullptr
		&& !InLedger->SpendPence(Definition->CostPence, OutReason))
	{
		return false;
	}
	if (!InBuild.InstallInSlot(HostStationId, UnitDefinitionId,
		OutStationId, OutReason))
	{
		if (InLedger != nullptr)
		{
			FString Ignored;
			InLedger->EarnPence(Definition->CostPence, Ignored);
		}
		return false;
	}
	auto Unwind = [&](const FString& WhyRefused)
	{
		FString Ignored;
		InBuild.RemoveStation(OutStationId, Ignored);
		if (InLedger != nullptr)
		{
			InLedger->EarnPence(Definition->CostPence, Ignored);
		}
		OutStationId = NAME_None;
		OutReason = WhyRefused;
	};
	if (Definition->PowerSupplyKw > 0)
	{
		FString SupplyReason;
		if (!InPower.RegisterSupply(OutStationId,
			Definition->PowerSupplyKw, SupplyReason))
		{
			Unwind(SupplyReason);
			return false;
		}
	}
	// A housed machine gets its LOCAL STOCKPILE exactly as a freely
	// placed one does - without it the delivery drones have nowhere to
	// put its feedstock and it can never craft.
	if (InInventory != nullptr && Definition->InputStockpileUnits > 0)
	{
		const FName StoreId(*FString::Printf(TEXT("Store.%s"),
			*OutStationId.ToString()));
		FString StoreReason;
		if (!InInventory->HasStore(StoreId)
			&& !InInventory->RegisterStore(StoreId,
				Definition->InputStockpileUnits, StoreReason))
		{
			Unwind(StoreReason);
			return false;
		}
	}
	if (Definition->PowerDrawKw > 0)
	{
		FString PowerReason;
		if (!InPower.ConnectLoad(OutStationId, Definition->PowerDrawKw,
			PowerReason))
		{
			Unwind(PowerReason);
			return false;
		}
	}
	return true;
}

bool ALBSpacecraftGameMode::InstallStationDronePowered(
	ALBSpacecraftBuildAuthority& InBuild, FName StationId,
	FString& OutReason, ALBSpacecraftProductionAuthority* InLedger,
	const ALBSpacecraftProgressionAuthority* InProgression, FName KindId)
{
	// QUALITY CONTROL is a delivery milestone, and crew is what quality
	// MEANS here - an under-crewed station fits parts badly. Everyone
	// can crew to nominal from the first minute, so nobody is forced to
	// build defective craft; crewing BEYOND nominal, for speed, is what
	// the milestone opens. Like the fabrication binding this is my
	// design call, made because the objectives ladder was advertising
	// an unlock that gated nothing at all.
	if (InProgression != nullptr
		&& !InProgression->IsUnlocked(ELBSpacecraftUnlock::QualityControl))
	{
		const FLBSpacecraftStationRecord* Record =
			InBuild.FindStation(StationId);
		if (Record != nullptr
			&& Record->InstalledDrones >= NominalStationCrew())
		{
			OutReason = FString::Printf(TEXT("%s (%s IS AT ITS NOMINAL ")
				TEXT("CREW OF %d)"),
				*InProgression->DescribeLock(
					ELBSpacecraftUnlock::QualityControl),
				*StationId.ToString(), NominalStationCrew());
			return false;
		}
	}
	// Each KIND has its own price (owner 2026-08-28: the player picks
	// what drones they want, so the choice has to cost something
	// different). An unnamed kind falls back to the flat drone price,
	// which is what every existing caller passes.
	const FLBSpacecraftDroneKind* Kind =
		ALBSpacecraftBuildAuthority::FindDroneKind(KindId);
	const int64 PricePence = Kind != nullptr
		? Kind->CostPence : InBuild.DroneUnitCostPence;
	if (InLedger != nullptr && !InLedger->SpendPence(PricePence, OutReason))
	{
		return false;
	}
	if (!InBuild.InstallStationDrone(StationId, OutReason, KindId))
	{
		if (InLedger != nullptr)
		{
			FString Ignored;
			InLedger->EarnPence(PricePence, Ignored);
		}
		return false;
	}
	return true;
}

bool ALBSpacecraftGameMode::DismissStationDronePowered(
	ALBSpacecraftBuildAuthority& InBuild, FName StationId, int32 SlotIndex,
	FString& OutReason, ALBSpacecraftProductionAuthority* InLedger)
{
	// A dismissed drone refunds HALF, the same provisional rule
	// station removal uses - selling back at full price would make the
	// crew a free experiment.
	const FLBSpacecraftStationRecord* Record = InBuild.FindStation(StationId);
	int64 Refund = InBuild.DroneUnitCostPence / 2;
	if (Record != nullptr
		&& Record->InstalledDroneTypes.IsValidIndex(SlotIndex))
	{
		if (const FLBSpacecraftDroneKind* Kind =
			ALBSpacecraftBuildAuthority::FindDroneKind(
				Record->InstalledDroneTypes[SlotIndex]))
		{
			Refund = Kind->CostPence / 2;
		}
	}
	if (!InBuild.RemoveStationDrone(StationId, SlotIndex, OutReason))
	{
		return false;
	}
	if (InLedger != nullptr)
	{
		FString Ignored;
		InLedger->EarnPence(Refund, Ignored);
	}
	return true;
}

bool ALBSpacecraftGameMode::RemoveStationPowered(
	ALBSpacecraftBuildAuthority& InBuild, ALBSpacecraftPowerAuthority& InPower,
	ALBSpacecraftInventoryAuthority& InInventory,
	ALBSpacecraftCraftingAuthority* InCrafting, FName StationId,
	FString& OutReason, ALBSpacecraftProductionAuthority* InLedger)
{
	// A slot building removes its hosted units FIRST through this same
	// powered path, so their supplies, loads and refunds unwind
	// exactly like free-standing stations.
	{
		TArray<FName> Hosted;
		for (const FLBSpacecraftStationRecord& Record :
			InBuild.GetStations())
		{
			if (Record.HostStationId == StationId)
			{
				Hosted.Add(Record.StationId);
			}
		}
		for (const FName& HostedId : Hosted)
		{
			FString HostedReason;
			RemoveStationPowered(InBuild, InPower, InInventory,
				InCrafting, HostedId, HostedReason, InLedger);
		}
	}
	const FLBSpacecraftStationDefinition* Definition = nullptr;
	for (const FLBSpacecraftStationRecord& Record :
		InBuild.GetStations())
	{
		if (Record.StationId == StationId)
		{
			Definition = ALBSpacecraftBuildAuthority::FindDefinition(
				Record.DefinitionId);
			break;
		}
	}
	if (Definition == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STATION %s"),
			*StationId.ToString());
		return false;
	}
	// Fail-closed checks FIRST, in an order where each refusal leaves
	// everything untouched: a stranding supply or a stocked rack blocks
	// the whole removal.
	if (Definition->PowerSupplyKw > 0
		&& !InPower.RemoveSupply(StationId, OutReason))
	{
		return false;
	}
	// Symmetric with placement: bulk store or local stockpile, both
	// ordinary stores. A stocked one refuses removal - you empty it
	// first, which is the same rule racks always had.
	if (Definition->StorageCapacityUnits > 0
		|| Definition->InputStockpileUnits > 0)
	{
		const FName StoreId(*FString::Printf(TEXT("Store.%s"),
			*StationId.ToString()));
		// A station wired before stockpiles existed - or installed
		// without an inventory to hand - simply has no store, and
		// that must not block its removal.
		if (InInventory.HasStore(StoreId)
			&& !InInventory.RemoveStore(StoreId, OutReason))
		{
			// The supply (if any) was already removed above; a station is
			// never both a plant and a rack, so no re-registration case
			// exists in the catalogue. Assert that stays true.
			checkf(Definition->PowerSupplyKw == 0,
				TEXT("catalogue must not combine supply and storage"));
			return false;
		}
	}
	if (Definition->PowerDrawKw > 0)
	{
		FString Ignored;
		InPower.DisconnectLoad(StationId, Ignored);
	}
	FString CraftIgnored;
	if (InCrafting != nullptr)
	{
		InCrafting->ClearSelection(StationId, CraftIgnored);
	}
	if (!InBuild.RemoveStation(StationId, OutReason))
	{
		return false;
	}
	// Sell-back (PROVISIONAL 50% pending the owner's economy tuning).
	if (InLedger != nullptr)
	{
		FString Ignored;
		InLedger->EarnPence(
			Definition->CostPence * RemovalRefundPercent / 100, Ignored);
	}
	return true;
}

bool ALBSpacecraftGameMode::SelectStationRecipe(
	ALBSpacecraftBuildAuthority& InBuild,
	ALBSpacecraftCraftingAuthority& InCrafting,
	ALBSpacecraftResearchAuthority& InResearch, FName StationId,
	FName RecipeId, FString& OutReason)
{
	for (const FLBSpacecraftStationRecord& Record : InBuild.GetStations())
	{
		if (Record.StationId != StationId)
		{
			continue;
		}
		if (!InResearch.IsStationClassUnlocked(Record.DefinitionId))
		{
			OutReason = FString::Printf(
				TEXT("%s IS LOCKED - RESEARCH IT FIRST"),
				*Record.DefinitionId.ToString());
			return false;
		}
		// A bigger mark runs the SAME recipes as the mark below it.
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(Record.DefinitionId);
		return InCrafting.SelectRecipe(StationId,
			Definition != nullptr ? Definition->GetRecipeClassId()
				: Record.DefinitionId,
			RecipeId, OutReason);
	}
	OutReason = FString::Printf(TEXT("UNKNOWN STATION %s"),
		*StationId.ToString());
	return false;
}

FName ALBSpacecraftGameMode::FindDeliveryStore(
	const ALBSpacecraftBuildAuthority& InBuild,
	const ALBSpacecraftInventoryAuthority& InInventory, FName ItemId,
	int32 Count, FString& OutReason)
{
	bool bAnyDock = false;
	for (const FLBSpacecraftStationRecord& Record : InBuild.GetStations())
	{
		if (Record.DefinitionId != FName(TEXT("DeliveryDock")))
		{
			continue;
		}
		bAnyDock = true;
		const FName StoreId(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		// ROOM FOR SOME, not room for all. This asked for room for the
		// WHOLE order, which made a big order strictly harder to place
		// than the same goods bought in dribs: 900 Silicon against a
		// 400-unit dock was refused outright, and "buy parts for
		// twenty ships in one click" was impossible by construction.
		// Deliveries now land as much as fits and keep the rest on the
		// lorry, so a dock with ANY room can take the order; a dock
		// with none is genuinely backed up and still says so.
		if (InInventory.GetRoomForItems(StoreId, ItemId) >= 1)
		{
			OutReason.Reset();
			return StoreId;
		}
	}
	OutReason = bAnyDock
		? FString::Printf(
			TEXT("EVERY DELIVERY DOCK IS BACKED UP - CLEAR ONE BEFORE ")
			TEXT("ORDERING %d MORE %s"), Count, *ItemId.ToString())
		: FString(TEXT("NO DELIVERY DOCK - BUILD ONE FOR GOODS TO ")
			TEXT("ARRIVE AT"));
	return NAME_None;
}

bool ALBSpacecraftGameMode::PlaceResourceOrder(
	ALBSpacecraftInventoryAuthority& InInventory,
	ALBSpacecraftProductionAuthority& InLedger, FName ItemId, int32 Count,
	FName StoreId, FString& OutReason)
{
	const int64 UnitPrice =
		FLBSpacecraftItemCatalogue::GetOrderablePricePence(ItemId);
	if (UnitPrice <= 0 || Count <= 0)
	{
		OutReason = FString::Printf(
			TEXT("%s IS NOT A PURCHASABLE RAW MATERIAL"),
			*ItemId.ToString());
		return false;
	}
	// Money first, refund on any later refusal - never a free order and
	// never a paid-for nothing.
	if (!InLedger.SpendPence(UnitPrice * Count, OutReason))
	{
		return false;
	}
	FName OrderId;
	if (!InInventory.PlaceOrder(ItemId, Count, StoreId, OrderId,
		OutReason))
	{
		FString Ignored;
		InLedger.EarnPence(UnitPrice * Count, Ignored);
		return false;
	}
	OutReason = FString::Printf(TEXT("ORDER %s PLACED - ARRIVING SOON"),
		*OrderId.ToString());
	return true;
}

int32 ALBSpacecraftGameMode::TickCraftingStations(
	ALBSpacecraftBuildAuthority& InBuild,
	ALBSpacecraftCraftingAuthority& InCrafting,
	ALBSpacecraftInventoryAuthority& InInventory, double DeltaSeconds,
	const ALBSpacecraftTransportAuthority* InTransport,
	ALBSpacecraftGameMode* InAlertSink)
{
	// Is there anywhere for a full buffer to go? Haulers exist only per
	// storage rack, so with no rack the "awaiting drone pickup" the
	// crafting authority reports can never come true.
	bool bAnyStorageRack = false;
	for (const FLBSpacecraftStationRecord& RackRecord : InBuild.GetStations())
	{
		if (RackRecord.DefinitionId == FName(TEXT("StorageRack")))
		{
			bAnyStorageRack = true;
			break;
		}
	}
	using namespace LBSpacecraftGameModePrivate;
	if (DeltaSeconds <= 0.0)
	{
		return 0;
	}
	FString Reason;
	if (!SpacecraftEnsureDevFloorStore(InInventory, Reason))
	{
		return 0;
	}
	const FName Floor(TEXT("Store.Floor"));
	int32 TotalCycles = 0;
	for (const FLBSpacecraftStationRecord& Record : InBuild.GetStations())
	{
		if (InCrafting.GetSelectedRecipe(Record.StationId) == nullptr)
		{
			continue;
		}
		int32 Cycles = 0;
		// A belted station crafts faster; an unbelted one falls back to
		// drone ferrying - slower, never broken (research doc v001).
		// Belting speeds a station; so does a bigger MARK. Both are
		// multipliers on the same clock.
		const FLBSpacecraftStationDefinition* MarkDefinition =
			ALBSpacecraftBuildAuthority::FindDefinition(Record.DefinitionId);
		const float MarkSpeed = MarkDefinition != nullptr
			? FMath::Max(MarkDefinition->CraftSpeedMultiplier, 0.01f)
			: 1.f;
		const double StationSeconds = DeltaSeconds * MarkSpeed
			* (InTransport != nullptr
				? InTransport->GetStationSpeedMultiplier(Record.StationId)
				: 1.f);
		// A machine draws its feedstock from ITS OWN stockpile, the
		// one the delivery drones keep fed (owner 2026-08-27, the
		// Production Line model). Outputs go to the machine's buffer
		// and are collected from there by the same haulers.
		const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		const FName InputStore =
			InInventory.HasStore(Stockpile) ? Stockpile : Floor;
		InCrafting.TickCrafting(Record.StationId, StationSeconds,
			InInventory, InputStore, InputStore, Cycles, Reason);
		// A machine that refused its cycle used to say so into a local
		// that was thrown away. Tell the player.
		if (Cycles == 0 && InAlertSink != nullptr && !Reason.IsEmpty())
		{
			if (Reason.Contains(TEXT("OUTPUT BUFFER FULL")))
			{
				InAlertSink->RaiseSimAlert(BuildBufferStallAlert(
					Record.StationId, bAnyStorageRack));
			}
			else if (Reason.Contains(TEXT("HOLDS"))
				|| Reason.Contains(TEXT("LACKS")))
			{
				// Starved of feedstock: the drones have not brought
				// it yet, or there is none on site to bring.
				InAlertSink->RaiseSimAlert(FString::Printf(
					TEXT("INSUFFICIENT RESOURCES AT %s - ITS STOCKPILE ")
					TEXT("IS WAITING ON A DELIVERY"),
					*Record.StationId.ToString()));
			}
		}
		TotalCycles += Cycles;
	}
	return TotalCycles;
}

// ---------------------------------------------------------------------------
// LB.Spacecraft.* developer console commands
// ---------------------------------------------------------------------------

// DEV COMMAND - COMPILED OUT OF SHIPPING.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftAutoPlayCommand(
	TEXT("LB.Spacecraft.AutoPlay"),
	TEXT("Dev: plays the game under a stated POLICY and reports what it ")
	TEXT("achieved, so a design question can be answered by measurement ")
	TEXT("instead of argument. Args: [simMinutes=60] [greedy|minimal]. ")
	TEXT("GREEDY buys a fitting station whenever it can afford one; ")
	TEXT("MINIMAL never buys another. If greedy wins with no downside ")
	TEXT("then the game's central decision has a dominant answer and is ")
	TEXT("not a decision."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode =
		ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.AutoPlay: no spacecraft game mode"));
		return;
	}
	const double Minutes = Args.Num() > 0
		? FCString::Atod(*Args[0]) : 60.0;
	const FString Policy = (Args.Num() > 1 && Args[1].Equals(
		TEXT("minimal"), ESearchCase::IgnoreCase))
		? TEXT("MINIMAL") : TEXT("GREEDY");

	ALBSpacecraftBuildAuthority* Build = GameMode->GetBuildAuthority();
	ALBSpacecraftProductionAuthority* Production =
		GameMode->GetProductionAuthority();
	const int64 StartCash = Production->GetCashPence();

	// SIX IS THE CEILING because the fixing order is six components; a
	// seventh station passes through fitting nothing, so buying one
	// would be strictly wasteful and no sane policy does it.
	constexpr int32 ComponentCount = 6;
	constexpr double StepSeconds = 1.0;
	const int32 Steps = FMath::Max(1,
		FMath::RoundToInt(Minutes * 60.0 / StepSeconds));

	int32 Bought = 0;
	int32 Cycles = 0;
	int32 ContractsTaken = 0;
	FString Reason;

	// SUPPLY BEFORE SCALE - what a competent player does first, and
	// what the policy used to skip entirely. Buying fitting stations
	// while nothing can reach them is the beginner's mistake: the
	// starting loadout builds one craft, then the line holds forever
	// on a hull with no dock to order one to and no rack for a hauler
	// to stage through. The first honest AutoPlay run made 72,941 cr
	// in sixty simulated hours and failed ten contracts doing it.
	// Fails soft: a policy that cannot buy its supply chain is still
	// worth measuring, and the refusal is named rather than swallowed.
	bool bSupplyReady = false;
	if (GameMode->GetPowerAuthority() != nullptr
		&& GameMode->GetInventoryAuthority() != nullptr
		&& GameMode->GetCraftingAuthority() != nullptr
		&& GameMode->GetResearchAuthority() != nullptr)
	{
		bSupplyReady = ALBSpacecraftGameMode::SetupEconomy(*Build,
			*GameMode->GetPowerAuthority(),
			*GameMode->GetInventoryAuthority(),
			*GameMode->GetCraftingAuthority(),
			*GameMode->GetResearchAuthority(), *Production,
			GameMode->GetProgression(), 4, Reason);
	}
	if (!bSupplyReady)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("AUTOPLAY could not build its supply chain: %s"),
			Reason.IsEmpty() ? TEXT("MISSING AUTHORITY") : *Reason);
	}
	for (int32 Step = 0; Step < Steps; ++Step)
	{
		// RESTOCK. Supply is not a thing you do once. The opening
		// SetupEconomy buys raw materials and books crafting orders
		// for a handful of craft; when those run out the machines go
		// idle, the components stop arriving and the line holds on a
		// hull forever - which is what "5 craft in sixty hours"
		// actually was. A player watching the panel would simply
		// order more, so the policy does too, on a half-hour of sim
		// time. SetupEconomy skips what already stands, so this tops
		// up orders rather than rebuilding the factory.
		// Top up the ORDERS only. Re-running SetupEconomy did restock
		// the line - revenue tripled - but it also placed a fresh set
		// of machines every time it was called, and the factory grew
		// from 9 stations to 75. That is the policy cheating, and a
		// measurement taken against it is worthless. SetupEconomy is
		// idempotent about the dock and the racks, NOT about the
		// machines.
		if (bSupplyReady && Step > 0 && (Step % 1800) == 0
			&& GameMode->GetCraftingAuthority() != nullptr)
		{
			ALBSpacecraftCraftingAuthority* Crafting =
				GameMode->GetCraftingAuthority();
			for (const FLBSpacecraftStationRecord& Record :
				Build->GetStations())
			{
				if (Crafting->GetSelectedRecipe(Record.StationId)
						!= nullptr
					&& Crafting->GetOrderRemaining(Record.StationId) <= 0)
				{
					Crafting->AddOrder(Record.StationId, 8, Reason);
				}
			}
		}
		// RE-ORDER THE COMPONENTS. This is what the line actually
		// lives on. No crafting machine gets placed at the opening -
		// they are gated - so every component the stations fit is
		// IMPORTED, and SetupEconomy imports exactly enough for the
		// craft target it was given. When that runs out the line
		// holds on a hull and never moves again, which is what "5
		// craft, then nothing, for fifty more hours" was. A player
		// reads "ORDER MORE AT THE DELIVERY DOCK" and orders more.
		if (bSupplyReady && Step > 0 && (Step % 1800) == 0
			&& GameMode->GetInventoryAuthority() != nullptr)
		{
			ALBSpacecraftInventoryAuthority* Inv =
				GameMode->GetInventoryAuthority();
			FName DockStore;
			for (const FLBSpacecraftStationRecord& Record :
				Build->GetStations())
			{
				if (Record.DefinitionId == FName(TEXT("DeliveryDock")))
				{
					DockStore = FName(*FString::Printf(TEXT("Store.%s"),
						*Record.StationId.ToString()));
					break;
				}
			}
			if (!DockStore.IsNone())
			{
				for (const FLBSpacecraftStationRecord& Record :
					Build->GetStations())
				{
					for (const FName& Component :
						Record.AllocatedComponents)
					{
						// Keep a few in hand, no more. Ordering a
						// hoard would fill the dock's finite hold and
						// block every other component behind it.
						if (Inv->GetQuantity(DockStore, Component) < 4)
						{
							ALBSpacecraftGameMode::PlaceResourceOrder(
								*Inv, *Production, Component, 4,
								DockStore, Reason);
						}
					}
				}
			}
		}
		// Keep work on the line. A policy that never takes a contract
		// measures nothing - and the first version of this test was
		// "is the contract list empty", which the OFFER BOARD makes
		// false forever after the first tick. The policy took ONE
		// contract in sixty simulated hours and idled through 704
		// lapsed offers, which read like a deliberate strategy and was
		// a mis-asked question. What matters is whether any contract
		// is OUTSTANDING - accepted and not yet finished.
		int32 Outstanding = 0;
		for (const FLBSpacecraftContract& Contract :
			Production->GetContracts())
		{
			if (Contract.State == ELBSpacecraftContractState::Accepted)
			{
				++Outstanding;
			}
		}
		if (Outstanding == 0)
		{
			if (ALBSpacecraftGameMode::StartScoutContract(*Production, 2,
				Reason))
			{
				++ContractsTaken;
			}
		}
		if (Policy == TEXT("GREEDY"))
		{
			int32 LineStations = 0;
			for (const FLBSpacecraftStationRecord& Record :
				Build->GetStations())
			{
				const FLBSpacecraftStationDefinition* Definition =
					ALBSpacecraftBuildAuthority::FindDefinition(
						Record.DefinitionId);
				if (Definition != nullptr
					&& Definition->StageClassId
						== FName(TEXT("LineStation")))
				{
					++LineStations;
				}
			}
			const FLBSpacecraftStationDefinition* Mk1 =
				ALBSpacecraftBuildAuthority::FindDefinition(
					FName(TEXT("AssemblyRobot")));
			if (Mk1 != nullptr && LineStations < ComponentCount
				&& Production->GetCashPence() >= Mk1->CostPence)
			{
				FName NewId;
				// PLACE BEYOND WHAT IS ALREADY THERE. A fixed grid
				// collided with the station the game starts you with -
				// "ENVELOPE OVERLAPS STATION AssemblyRobot-002" - so
				// the policy appeared to decline rather than fail.
				float FurthestY = -4000.f;
				bool bAnyLine = false;
				for (const FLBSpacecraftStationRecord& Record :
					Build->GetStations())
				{
					const FLBSpacecraftStationDefinition* Existing =
						ALBSpacecraftBuildAuthority::FindDefinition(
							Record.DefinitionId);
					if (Existing == nullptr
						|| Existing->StageClassId
							!= FName(TEXT("LineStation")))
					{
						continue;
					}
					const float Y = static_cast<float>(
						Record.WorldTransform.GetLocation().Y);
					FurthestY = bAnyLine ? FMath::Max(FurthestY, Y) : Y;
					bAnyLine = true;
				}
				const float PlaceY = bAnyLine
					? FurthestY + 1600.f : -4000.f;
				const bool bPlaced = Build->PlaceStation(
					FName(TEXT("AssemblyRobot")),
					FTransform(FRotator::ZeroRotator,
						FVector(0.f, PlaceY, 0.f)), NewId, Reason);
				if (!bPlaced)
				{
					// SAY WHY, ONCE. The first version of this threw the
					// refusal away and reported "bought 0 stations",
					// which looks like a policy decision and is actually
					// a silent failure - the exact bug this command was
					// written to hunt.
					static bool bSaidOnce = false;
					if (!bSaidOnce)
					{
						bSaidOnce = true;
						UE_LOG(LogLBSpacecraft, Warning,
							TEXT("AUTOPLAY could not place a station at "
								"Y=%.0f: %s"), PlaceY, *Reason);
					}
				}
				if (bPlaced)
				{
					++Bought;
					Build->CommissionFactory(Reason);
					GameMode->LayLineTrack(Reason);
					if (GameMode->GetCoordinator() != nullptr)
					{
						GameMode->GetCoordinator()
							->ConfigureFromAuthorities(Build, Production,
								Reason, GameMode->GetTrackAuthority());
					}
				}
			}
		}
		int32 StepCycles = 0;
		ALBSpacecraftGameMode::TickWholeSimStep(*GameMode, StepSeconds,
			Reason, StepCycles);
		Cycles += StepCycles;
	}

	const int64 EndCash = Production->GetCashPence();
	const int32 Points = GameMode->GetReputation() != nullptr
		? GameMode->GetReputation()->GetPoints() : 0;
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("AUTOPLAY last step said: %s"), *Reason);
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("AUTOPLAY %s over %.0f sim-minutes: bought %d stations, "
			"%d craft cycles, %d contracts, cash %lld -> %lld pence "
			"(profit %lld), reputation %d"),
		*Policy, Minutes, Bought, Cycles, ContractsTaken,
		StartCash, EndCash, EndCash - StartCash, Points);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftPanelCommand(
	TEXT("LB.Spacecraft.Panel"),
	TEXT("Dev: prints every row the command panel is currently showing - ")
	TEXT("labels and button tags - so an unattended run can ASSERT what ")
	TEXT("is on screen instead of photographing it and needing eyes. The ")
	TEXT("SESSION section was verified from a screenshot before this ")
	TEXT("existed, which proves a picture exists, not that a button works."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>&, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode =
		ALBSpacecraftGameMode::FindInWorld(World);
	ULBSpacecraftCommandPanelWidget* Panel =
		GameMode != nullptr ? GameMode->GetCommandPanel() : nullptr;
	if (Panel == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Panel: no command panel"));
		return;
	}
	int32 Rows = 0;
	int32 Buttons = 0;
	UE_LOG(LogLBSpacecraft, Display, TEXT("PANEL TAB=%s"),
		*Panel->GetActiveTabName());
	TArray<UWidget*> Walk;
	Panel->WidgetTree->GetAllWidgets(Walk);
	for (UWidget* Widget : Walk)
	{
		if (const UTextBlock* Text = Cast<UTextBlock>(Widget))
		{
			const FString Line = Text->GetText().ToString();
			if (!Line.IsEmpty())
			{
				++Rows;
				UE_LOG(LogLBSpacecraft, Display, TEXT("PANEL ROW %s"),
					*Line.Replace(LINE_TERMINATOR, TEXT(" / ")));
			}
		}
		else if (const ULBSpacecraftTaggedButton* Button =
			Cast<ULBSpacecraftTaggedButton>(Widget))
		{
			++Buttons;
			UE_LOG(LogLBSpacecraft, Display, TEXT("PANEL BUTTON %s"),
				*Button->Tag.ToString());
		}
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("PANEL TOTAL rows=%d buttons=%d"), Rows, Buttons);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftPressCommand(
	TEXT("LB.Spacecraft.Press"),
	TEXT("Dev: presses a command-panel button BY ITS TAG, running the same ")
	TEXT("handler a mouse click would. Arg: tag (see LB.Spacecraft.Panel). ")
	TEXT("Without this a headless run can only call the code BEHIND a ")
	TEXT("button, which proves the pipeline works and says nothing about ")
	TEXT("whether the button is wired to it."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	if (Args.Num() < 1)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Press: needs a tag"));
		return;
	}
	ALBSpacecraftGameMode* GameMode =
		ALBSpacecraftGameMode::FindInWorld(World);
	ULBSpacecraftCommandPanelWidget* Panel =
		GameMode != nullptr ? GameMode->GetCommandPanel() : nullptr;
	if (Panel == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Press: no command panel"));
		return;
	}
	const FName Wanted(*Args[0]);
	TArray<UWidget*> Walk;
	Panel->WidgetTree->GetAllWidgets(Walk);
	for (UWidget* Widget : Walk)
	{
		ULBSpacecraftTaggedButton* Button =
			Cast<ULBSpacecraftTaggedButton>(Widget);
		if (Button == nullptr || Button->Tag != Wanted)
		{
			continue;
		}
		if (!Button->OnTagClicked)
		{
			UE_LOG(LogLBSpacecraft, Warning,
				TEXT("LB.Spacecraft.Press REFUSED: %s has no handler - ")
				TEXT("the button exists and is wired to nothing"),
				*Wanted.ToString());
			return;
		}
		Button->OnTagClicked(Button->Tag);
		UE_LOG(LogLBSpacecraft, Display,
			TEXT("LB.Spacecraft.Press OK: %s"), *Wanted.ToString());
		return;
	}
	UE_LOG(LogLBSpacecraft, Warning,
		TEXT("LB.Spacecraft.Press REFUSED: no button tagged %s on the %s ")
		TEXT("tab"), *Wanted.ToString(), *Panel->GetActiveTabName());
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftBuildLineCommand(
	TEXT("LB.Spacecraft.BuildLine"),
	TEXT("Places one station of every class through the build authority and ")
	TEXT("commissions the factory."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>&, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.BuildLine: no spacecraft game mode"));
		return;
	}
	FString Reason;
	if (!ALBSpacecraftGameMode::SetupCanonicalLine(
		*GameMode->GetBuildAuthority(), Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.BuildLine REFUSED: %s"), *Reason);
		return;
	}
	if (!GameMode->GetCoordinator()->ConfigureFromAuthorities(
		GameMode->GetBuildAuthority(), GameMode->GetProductionAuthority(),
		Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.BuildLine CONFIGURE REFUSED: %s"), *Reason);
		return;
	}
	// AND LAY THE TRACK. Without this the command produced a line whose
	// stations were attached to nothing, which runs perfectly well and
	// then refuses to LOAD - restore validates the whole snapshot and
	// rejects a route with no nodes. It configures once above to get a
	// route (the track needs to know which stations it must serve), then
	// again below with the track bound.
	if (!GameMode->LayLineTrack(Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.BuildLine TRACK REFUSED: %s"), *Reason);
		return;
	}
	if (!GameMode->GetCoordinator()->ConfigureFromAuthorities(
		GameMode->GetBuildAuthority(), GameMode->GetProductionAuthority(),
		Reason, GameMode->GetTrackAuthority()))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.BuildLine RECONFIGURE REFUSED: %s"),
			*Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display, TEXT(
		"LB.Spacecraft.BuildLine OK: %d stations, commissioned, route %d"),
		GameMode->GetBuildAuthority()->GetStations().Num(),
		GameMode->GetCoordinator()->GetRoute().Num());
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - stocks components into fitting stations for immediate production.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftStockComponentsCommand(
	TEXT("LB.Spacecraft.StockComponents"),
	TEXT("Stocks 4 units of each component into the fitting station ")
	TEXT("stockpiles. Use after LB.Spacecraft.BuildLine to make production ")
	TEXT("immediately runnable."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>&, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetInventoryAuthority() == nullptr
		|| GameMode->GetBuildAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.StockComponents: no game mode"));
		return;
	}
	FString Reason;
	int32 Stocked = 0;
	const FName Floor = FName(TEXT("Store.Floor"));
	if (!GameMode->GetInventoryAuthority()->HasStore(Floor))
	{
		GameMode->GetInventoryAuthority()->RegisterStore(Floor, 5000, Reason);
	}
	GameMode->SyncStationStores(*GameMode->GetBuildAuthority(),
		*GameMode->GetInventoryAuthority(),
		GameMode->GetCraftingAuthority());
	for (const FLBSpacecraftStationRecord& Record :
		GameMode->GetBuildAuthority()->GetStations())
	{
		const FName Stockpile(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		if (!GameMode->GetInventoryAuthority()->HasStore(Stockpile))
		{
			continue;
		}
		for (const FName& Component : Record.AllocatedComponents)
		{
			if (GameMode->GetInventoryAuthority()->Deposit(Stockpile,
				Component, 4, Reason))
			{
				++Stocked;
			}
		}
	}
	for (uint8 Index = 0; Index < 6; ++Index)
	{
		const FName ItemId =
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(Index);
		if (!ItemId.IsNone())
		{
			GameMode->GetInventoryAuthority()->Deposit(Floor, ItemId, 4, Reason);
		}
	}
	if (Stocked == 0)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.StockComponents: no stations or allocations"));
		return;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.StockComponents OK: %d shelves"), Stocked);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftBuildEconomyCommand(
	TEXT("LB.Spacecraft.BuildEconomy"),
	TEXT("Dev: builds the whole parts factory for the commissioned line - ")
	TEXT("plans the fabrication chain, places power/halls/machines with ")
	TEXT("recipes and standing orders, and orders the raw materials. ")
	TEXT("Args: [craftTarget=1]. Run LB.Spacecraft.BuildLine first; the ")
	TEXT("line then feeds itself with no Deposit commands."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetPowerAuthority() == nullptr
		|| GameMode->GetInventoryAuthority() == nullptr
		|| GameMode->GetCraftingAuthority() == nullptr
		|| GameMode->GetResearchAuthority() == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.BuildEconomy: no spacecraft game mode"));
		return;
	}
	const int32 CraftTarget = Args.Num() > 0
		? FCString::Atoi(*Args[0]) : 1;
	FString Reason;
	if (!ALBSpacecraftGameMode::SetupEconomy(
		*GameMode->GetBuildAuthority(), *GameMode->GetPowerAuthority(),
		*GameMode->GetInventoryAuthority(),
		*GameMode->GetCraftingAuthority(),
		*GameMode->GetResearchAuthority(),
		*GameMode->GetProductionAuthority(), GameMode->GetProgression(),
		CraftTarget, Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.BuildEconomy REFUSED: %s"), *Reason);
		return;
	}
	if (GameMode->GetDroneFleet() != nullptr)
	{
		GameMode->GetDroneFleet()->SyncFromBuild(
			GameMode->GetBuildAuthority(), GameMode->GetPowerAuthority());
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.BuildEconomy OK: %s"), *Reason);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftWatchCommand(
	TEXT("LB.Spacecraft.WatchRunway"),
	TEXT("Dev: points the camera at the runway, where a finished craft ")
	TEXT("self-starts, takes the chicane and sprints out. The launch is ")
	TEXT("the game's signature moment, and every capture until now was ")
	TEXT("taken from the factory floor where it cannot be seen."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>&, UWorld* World)
{
	APlayerController* Controller =
		World != nullptr ? World->GetFirstPlayerController() : nullptr;
	ALBSpacecraftPlayerPawn* Pawn = Controller != nullptr
		? Cast<ALBSpacecraftPlayerPawn>(Controller->GetPawn()) : nullptr;
	if (Pawn == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.WatchRunway: no spacecraft pawn"));
		return;
	}
	Pawn->FocusRunway();
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.WatchRunway OK"));
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftSpeedCommand(
	TEXT("LB.Spacecraft.Speed"),
	TEXT("Dev: sets the FACTORY SPEED the 1/2/3/4 keys set (0 pauses ")
	TEXT("the simulation, 1/2/4 scale it). Exists so a sighted run can ")
	TEXT("watch a whole craft get built and launched inside a capture, ")
	TEXT("which at 1x takes over seven minutes of real time. Arg: ")
	TEXT("[scale=4]."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Speed: no spacecraft game mode"));
		return;
	}
	const float Scale = Args.Num() > 0 ? FCString::Atof(*Args[0]) : 4.f;
	FString Reason;
	if (!GameMode->SetSimSpeed(Scale, Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Speed REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.Speed OK: %s"),
		*Reason);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftClickCommand(
	TEXT("LB.Spacecraft.Click"),
	TEXT("Dev: selects a placed station exactly as clicking it does, so ")
	TEXT("the panel shows that station's own page - its drone slots, its ")
	TEXT("crew and its fitting allocation. Arg: [stationId]; with none, ")
	TEXT("the first LINE station. (LB.Spacecraft.Select is the recipe ")
	TEXT("command and is a different thing.)"),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	APlayerController* Controller =
		World != nullptr ? World->GetFirstPlayerController() : nullptr;
	ALBSpacecraftPlayerPawn* Pawn = Controller != nullptr
		? Cast<ALBSpacecraftPlayerPawn>(Controller->GetPawn()) : nullptr;
	if (GameMode == nullptr || Pawn == nullptr
		|| GameMode->GetBuildAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Click: no spacecraft pawn"));
		return;
	}
	FName Target = Args.Num() > 0 ? FName(*Args[0]) : NAME_None;
	if (Target.IsNone())
	{
		for (const FLBSpacecraftStationRecord& Record :
			GameMode->GetBuildAuthority()->GetStations())
		{
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			if (Definition != nullptr && Definition->DroneSlotCount > 0)
			{
				Target = Record.StationId;
				break;
			}
		}
	}
	if (GameMode->GetBuildAuthority()->FindStation(Target) == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Click: no such station %s"),
			*Target.ToString());
		return;
	}
	Pawn->SetSelectedStation(Target);
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.Click OK: %s"),
		*Target.ToString());
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftEnterCommand(
	TEXT("LB.Spacecraft.Enter"),
	TEXT("Dev: enters a building - the camera drops inside and its roof ")
	TEXT("lifts, exactly as clicking it does. Arg: [stationId]; with no ")
	TEXT("argument it enters the first SITE BUILDING that stands. The ")
	TEXT("counterpart of LB.Spacecraft.SiteMap, so a sighted run can ")
	TEXT("photograph the inside of the factory as well as the outside."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	APlayerController* Controller =
		World != nullptr ? World->GetFirstPlayerController() : nullptr;
	ALBSpacecraftPlayerPawn* Pawn = Controller != nullptr
		? Cast<ALBSpacecraftPlayerPawn>(Controller->GetPawn()) : nullptr;
	if (GameMode == nullptr || Pawn == nullptr
		|| GameMode->GetBuildAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Enter: no spacecraft pawn"));
		return;
	}
	FName Target = Args.Num() > 0 ? FName(*Args[0]) : NAME_None;
	if (Target.IsNone())
	{
		for (const FLBSpacecraftStationRecord& Record :
			GameMode->GetBuildAuthority()->GetStations())
		{
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			if (Definition != nullptr && Definition->bSiteBuilding)
			{
				Target = Record.StationId;
				break;
			}
		}
	}
	if (Target.IsNone())
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Enter: nothing to enter - no building "
				"stands on the site"));
		return;
	}
	Pawn->SetSelectedStation(Target);
	Pawn->FocusStation(Target);
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.Enter OK: %s"),
		*Target.ToString());
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftSeedSpineCommand(
	TEXT("LB.Spacecraft.SeedSpine"),
	TEXT("Dev: seeds the starter spine (power, processor, rack, dock) ")
	TEXT("on an empty floor. Was the default first-launch state until ")
	TEXT("the owner rejected pre-seeded stations (2026-08-28); the game ")
	TEXT("opens empty now and fixtures ask for the spine explicitly."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>&, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.SeedSpine: no spacecraft game mode"));
		return;
	}
	FString Reason;
	if (!GameMode->SeedStarterSpine(Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.SeedSpine REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.SeedSpine OK: %s"), *Reason);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftChainCommand(
	TEXT("LB.Spacecraft.Chain"),
	TEXT("Dev: names what the fabrication chain is stuck on - every ")
	TEXT("machine still owing cycles with its shelf against its recipe, ")
	TEXT("and the line's hold reason. The self-feeding test's starvation ")
	TEXT("dump, promoted: a frozen factory must say WHY in one command."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>&, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetCraftingAuthority() == nullptr
		|| GameMode->GetInventoryAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Chain: no spacecraft game mode"));
		return;
	}
	ALBSpacecraftCraftingAuthority* Crafting =
		GameMode->GetCraftingAuthority();
	ALBSpacecraftInventoryAuthority* Inventory =
		GameMode->GetInventoryAuthority();
	int32 Stuck = 0;
	for (const FLBSpacecraftStationRecord& Record :
		GameMode->GetBuildAuthority()->GetStations())
	{
		const FLBSpacecraftItemRecipe* Recipe =
			Crafting->GetSelectedRecipe(Record.StationId);
		const int32 Remaining =
			Crafting->GetOrderRemaining(Record.StationId);
		if (Recipe == nullptr || Remaining <= 0)
		{
			continue;
		}
		const FName Shelf(*FString::Printf(TEXT("Store.%s"),
			*Record.StationId.ToString()));
		FString Inputs;
		for (const FLBSpacecraftItemStack& Input : Recipe->Inputs)
		{
			Inputs += FString::Printf(TEXT(" %s %d/%d"),
				*Input.ItemId.ToString(),
				Inventory->GetQuantity(Shelf, Input.ItemId),
				Input.Count);
		}
		UE_LOG(LogLBSpacecraft, Display,
			TEXT("CHAIN STUCK %s %s owes %d, buffer %d, shelf:%s"),
			*Record.StationId.ToString(), *Recipe->RecipeId.ToString(),
			Remaining, Crafting->GetBufferCount(Record.StationId),
			*Inputs);
		++Stuck;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("CHAIN %d machines still owe cycles; line hold: %s; ")
		TEXT("pending orders %d"),
		Stuck,
		GameMode->GetCoordinator() != nullptr
			? *GameMode->GetCoordinator()->GetLastHoldReason()
			: TEXT("-"),
		Inventory->GetPendingOrders().Num());
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftStartCommand(
	TEXT("LB.Spacecraft.Start"),
	TEXT("Offers and accepts a contract. Args: [quantity=1] [recipeId=SCOUT-01]."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetProductionAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Start: no spacecraft game mode"));
		return;
	}
	const int32 Quantity =
		Args.Num() > 0 ? FCString::Atoi(*Args[0]) : 1;
	const FName RecipeId =
		Args.Num() > 1 ? FName(*Args[1]) : FName(TEXT("SCOUT-01"));
	FString Reason;
	if (!ALBSpacecraftGameMode::StartRecipeContract(
		*GameMode->GetProductionAuthority(), RecipeId, Quantity, Reason,
		GameMode->GetReputation()))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Start REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Start OK: %s x%d accepted"),
		*RecipeId.ToString(), FMath::Max(Quantity, 1));
}));
#endif // !UE_BUILD_SHIPPING

bool ALBSpacecraftGameMode::TickWholeSimStep(
	ALBSpacecraftGameMode& InGameMode, double StepSeconds,
	FString& OutReason, int32& OutCraftCycles)
{
	// Gather once, step once. See the header for why the list lives in
	// exactly one place.
	return TickWholeSimStep(InGameMode.MakeSaveContext(), StepSeconds,
		OutReason, OutCraftCycles);
}

bool ALBSpacecraftGameMode::TickWholeSimStep(
	const FLBSpacecraftSaveContext& InContext, double StepSeconds,
	FString& OutReason, int32& OutCraftCycles)
{
	if (InContext.Coordinator == nullptr)
	{
		OutReason = TEXT("NO COORDINATOR");
		return false;
	}
	if (!InContext.Coordinator->TickProduction(StepSeconds, OutReason))
	{
		return false;
	}
	// Crafting stations run on the same sim clock as the craft line.
	if (InContext.Crafting != nullptr && InContext.Inventory != nullptr
		&& InContext.Build != nullptr)
	{
		// GIVE NEW STATIONS THEIR STOCKPILES. The same omission as the
		// haulers, found the same way. A station placed during a
		// console-driven run never got a store, because only the actor
		// tick created them - so it carried a fitting allocation it had
		// nowhere to hold parts for. In a soak that bought three
		// stations, ONE had a stockpile: the four components allocated
		// to the other three were fitted out of nothing, and never paid
		// for.
		SyncStationStores(*InContext.Build, *InContext.Inventory,
			InContext.Crafting);
		if (InContext.Transport != nullptr)
		{
			InContext.Transport->SyncFromBuild(InContext.Build);
		}
		OutCraftCycles += TickCraftingStations(*InContext.Build,
			*InContext.Crafting, *InContext.Inventory, StepSeconds,
			InContext.Transport);
	}
	// So does the drone fleet - flight drains, docks draw the grid.
	if (InContext.DroneFleet != nullptr)
	{
		InContext.DroneFleet->SyncFromBuild(InContext.Build,
			InContext.Power);
		InContext.DroneFleet->TickFleet(StepSeconds, InContext.Crafting,
			InContext.Power, InContext.Coordinator);
		// AND THE HAULERS. Missing this made the whole game unplayable
		// from the console while looking perfect in a headed session:
		// Run advances thousands of SIM seconds inside two or three
		// REAL frames, so an authority ticked only from the actor tick
		// receives a few hundredths of a second in total - far short of
		// one haul's travel time. Anything on the sim clock belongs
		// HERE; the actor tick is only the real-time path to this step.
		InContext.DroneFleet->TickHauls(StepSeconds, InContext.Crafting,
			InContext.Inventory, InContext.Build);
	}
	if (InContext.Power != nullptr)
	{
		InContext.Power->TickGridMeter(StepSeconds, InContext.Production);
	}
	// The SAME credit the actor tick applies - reputation, milestones
	// and research together.
	SyncLedgerDerivedAuthorities(InContext);
	if (InContext.Inventory != nullptr)
	{
		InContext.Inventory->TickOrders(StepSeconds);
	}
	return true;
}

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftJumpCommand(
	TEXT("LB.Spacecraft.Jump"),
	TEXT("Dev: fast-forwards the simulation until a craft REACHES A NAMED ")
	TEXT("STAGE, then stops. A Scout takes over seven minutes of real ")
	TEXT("time to build, so photographing it mid-assembly meant guessing ")
	TEXT("a delay and running the whole thing again when the guess was ")
	TEXT("wrong - which was the single biggest time sink in a day of ")
	TEXT("visual work. Args: <stage> [guardSimSeconds=2000] ")
	TEXT("[stepSeconds=2]. Stage is a NAME (intake, processing, hull, ")
	TEXT("component, staging, assembly, testing, dispatched) or an index."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	using namespace LBSpacecraftGameModePrivate;
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetCoordinator() == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Jump: no spacecraft game mode"));
		return;
	}
	if (Args.Num() < 1)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Jump: args are <stage> [guard] [step]"));
		return;
	}
	// Names first, index as the fallback: "Jump assembly" is what
	// anyone actually wants to type, and an index is unreadable in a
	// capture script six months later.
	const TCHAR* StageNames[] = { TEXT("intake"), TEXT("processing"),
		TEXT("hull"), TEXT("component"), TEXT("staging"),
		TEXT("assembly"), TEXT("testing"), TEXT("dispatched") };
	int32 Target = INDEX_NONE;
	for (int32 Index = 0; Index < UE_ARRAY_COUNT(StageNames); ++Index)
	{
		if (Args[0].StartsWith(StageNames[Index], ESearchCase::IgnoreCase))
		{
			Target = Index;
			break;
		}
	}
	if (Target == INDEX_NONE && Args[0].IsNumeric())
	{
		Target = FCString::Atoi(*Args[0]);
	}
	if (Target < 0 || Target > static_cast<int32>(
		ELBSpacecraftStage::Dispatched))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Jump: no stage called %s"), *Args[0]);
		return;
	}
	const double Guard = Args.Num() > 1
		? FCString::Atod(*Args[1]) : 2000.0;
	const double Step = Args.Num() > 2
		? FMath::Max(FCString::Atod(*Args[2]), 0.1) : 2.0;

	FString Reason;
	double Elapsed = 0.0;
	int32 CraftCycles = 0;
	auto AnyUnitReached = [GameMode, Target]()
	{
		for (const FLBSpacecraftUnitState& Unit :
			GameMode->GetProductionAuthority()->GetUnits())
		{
			if (static_cast<int32>(Unit.Stage) >= Target)
			{
				return true;
			}
		}
		return false;
	};
	// Already there: say so rather than silently doing nothing.
	if (AnyUnitReached())
	{
		UE_LOG(LogLBSpacecraft, Display,
			TEXT("LB.Spacecraft.Jump: a craft is already at %s"),
			*Args[0]);
		SpacecraftLogStatus(*GameMode);
		return;
	}
	while (Elapsed < Guard)
	{
		if (!ALBSpacecraftGameMode::TickWholeSimStep(*GameMode, Step,
			Reason, CraftCycles))
		{
			// A HOLD IS NOT A BUG, it is the line telling you why it
			// cannot proceed - so it is reported verbatim rather than
			// swallowed, and the guard is what stops an infinite wait.
			UE_LOG(LogLBSpacecraft, Warning,
				TEXT("LB.Spacecraft.Jump STOPPED at %.0fs: %s"),
				Elapsed, *Reason);
			return;
		}
		Elapsed += Step;
		if (AnyUnitReached())
		{
			UE_LOG(LogLBSpacecraft, Display,
				TEXT("LB.Spacecraft.Jump OK: reached %s after %.0f sim ")
				TEXT("seconds (%d craft cycles)"),
				*Args[0], Elapsed, CraftCycles);
			SpacecraftLogStatus(*GameMode);
			return;
		}
	}
	UE_LOG(LogLBSpacecraft, Warning,
		TEXT("LB.Spacecraft.Jump GAVE UP: %s not reached in %.0f sim ")
		TEXT("seconds. Last line state: %s"),
		*Args[0], Guard,
		GameMode->GetCoordinator() != nullptr
			? *GameMode->GetCoordinator()->GetLastHoldReason()
			: TEXT("-"));
	SpacecraftLogStatus(*GameMode);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftRunCommand(
	TEXT("LB.Spacecraft.Run"),
	TEXT("Ticks production. Args: [totalSimSeconds] [stepSeconds] ")
	TEXT("(defaults 600 5)."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	using namespace LBSpacecraftGameModePrivate;
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetCoordinator() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Run: no spacecraft game mode"));
		return;
	}
	const double Total =
		Args.Num() > 0 ? FCString::Atod(*Args[0]) : 600.0;
	const double Step =
		Args.Num() > 1 ? FMath::Max(FCString::Atod(*Args[1]), 0.1) : 5.0;
	FString Reason;
	double Elapsed = 0.0;
	int32 CraftCycles = 0;
	while (Elapsed < Total)
	{
		// One shared step with LB.Spacecraft.Jump - see
		// TickWholeSimStep for why they must not drift.
		if (!ALBSpacecraftGameMode::TickWholeSimStep(*GameMode, Step,
			Reason, CraftCycles))
		{
			UE_LOG(LogLBSpacecraft, Warning,
				TEXT("LB.Spacecraft.Run STOPPED at %.1fs: %s"),
				Elapsed, *Reason);
			return;
		}
		Elapsed += Step;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Run OK: advanced %.1f sim seconds ")
		TEXT("(%d craft cycles)"), Elapsed, CraftCycles);
	SpacecraftLogStatus(*GameMode);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftHubCommand(
	TEXT("LB.Spacecraft.Hub"),
	TEXT("Dev: clicks a place on the site hub, as the mouse would. ")
	TEXT("Args: placeId (ShipFactory, PartsFactory, PowerPlant, ")
	TEXT("ReceivingDock, StorageWarehouse, DroneDepot, ParkingApron, ")
	TEXT("ResearchLab, TestHall, Operations, MaterialsRefinery, ")
	TEXT("HeavyShipFactory). No argument lists every place and its ")
	TEXT("state."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	ULBSpacecraftSiteHubWidget* Hub = GameMode != nullptr
		? GameMode->GetSiteHub() : nullptr;
	if (Hub == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Hub: no site hub - it is only built "
				"with a player controller, so this needs a real game "
				"session rather than a headless -NullRHI one"));
		return;
	}
	if (Args.Num() == 0)
	{
		for (const FLBSpacecraftHubPlace& Place :
			ULBSpacecraftSiteHubWidget::Places())
		{
			const ULBSpacecraftSiteHubWidget::EState State =
				Hub->StateOf(Place.PlaceId);
			UE_LOG(LogLBSpacecraft, Display, TEXT("  HUB %-18s %s"),
				*Place.PlaceId.ToString(),
				State == ULBSpacecraftSiteHubWidget::EState::Open
					? TEXT("OPEN")
					: (State
						== ULBSpacecraftSiteHubWidget::EState::Buildable
						? TEXT("BUILDABLE") : TEXT("LOCKED")));
		}
		return;
	}
	const FString Said = Hub->EnterPlace(FName(*Args[0]));
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.Hub: %s"), *Said);
}));
#endif // !UE_BUILD_SHIPPING

#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftSiteMapCommand(
	TEXT("LB.Spacecraft.SiteMap"),
	TEXT("Frames the whole site (the M key's site map), for headed dev ")
	TEXT("runs and screenshots."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	(void)Args;
	APlayerController* Controller =
		World != nullptr ? World->GetFirstPlayerController() : nullptr;
	ALBSpacecraftPlayerPawn* Pawn = Controller != nullptr
		? Cast<ALBSpacecraftPlayerPawn>(Controller->GetPawn()) : nullptr;
	if (Pawn == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.SiteMap: no spacecraft pawn"));
		return;
	}
	Pawn->FocusSite();
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.SiteMap OK"));
}));
#endif // !UE_BUILD_SHIPPING

namespace LBSpacecraftBillOfMaterialsPrivate
{
	/**
	 * What one item costs to obtain, by the CHEAPER of the two routes
	 * the player actually has: buy it in, or make it from its inputs.
	 *
	 * Make-vs-buy is a real choice in this game - imports carry a
	 * deliberately thin ~1.3x premium so fabrication pays for itself
	 * once volume arrives - so a bill of materials that only counted
	 * import prices would overstate what a craft costs a player who
	 * fabricates, and one that only counted fabrication would
	 * understate the early game where nothing is built yet.
	 *
	 * Visited guards against a cycle in the recipe table. A cycle would
	 * otherwise recurse until the stack gave out, and a crash is a much
	 * worse way to learn the data is wrong than a named refusal.
	 */
	int64 CostOfItem(FName ItemId, TSet<FName>& Visited, int32 Depth,
		TMap<FName, int64>& OutLeafSpend)
	{
		const int64 Orderable =
			FLBSpacecraftItemCatalogue::GetOrderablePricePence(ItemId);
		if (Visited.Contains(ItemId) || Depth > 12)
		{
			return Orderable;   // cycle or runaway: fall back to buying
		}
		Visited.Add(ItemId);

		int64 Best = Orderable > 0 ? Orderable : MAX_int64;
		for (const FLBSpacecraftItemRecipe& Recipe :
			FLBSpacecraftRecipeCatalogue::GetRecipeTable())
		{
			int32 MadeHere = 0;
			for (const FLBSpacecraftItemStack& Output : Recipe.Outputs)
			{
				if (Output.ItemId == ItemId)
				{
					MadeHere = FMath::Max(Output.Count, 1);
					break;
				}
			}
			if (MadeHere <= 0)
			{
				continue;
			}
			int64 Inputs = 0;
			for (const FLBSpacecraftItemStack& Input : Recipe.Inputs)
			{
				TSet<FName> Branch = Visited;
				Inputs += CostOfItem(Input.ItemId, Branch, Depth + 1,
					OutLeafSpend) * FMath::Max(Input.Count, 1);
			}
			// Per unit produced, so a recipe yielding two costs half as
			// much each - otherwise a batch recipe reads as twice the
			// price of the thing it makes.
			Best = FMath::Min(Best, Inputs / MadeHere);
		}
		if (Best == MAX_int64)
		{
			// Neither orderable nor makeable. Recorded rather than
			// silently zero: an item with no price and no recipe is a
			// hole in the catalogue, and a bill of materials that
			// quietly treats it as free is worse than one that says so.
			OutLeafSpend.FindOrAdd(ItemId) += 0;
			return 0;
		}
		return Best;
	}
}

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftScrollCommand(
	TEXT("LB.Spacecraft.Scroll"),
	TEXT("Dev: scrolls the command panel, 0 top to 1 bottom, so a ")
	TEXT("capture can reach a section below the fold. Args: [fraction=1]."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode =
		ALBSpacecraftGameMode::FindInWorld(World);
	ULBSpacecraftCommandPanelWidget* Panel =
		GameMode != nullptr ? GameMode->GetCommandPanel() : nullptr;
	if (Panel == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Scroll: no command panel"));
		return;
	}
	const float Fraction = Args.Num() > 0
		? FCString::Atof(*Args[0]) : 1.f;
	Panel->ScrollContentToFraction(Fraction);
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Scroll -> %.2f"), Fraction);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftTabCommand(
	TEXT("LB.Spacecraft.Tab"),
	TEXT("Dev: switches the command panel to BUILD, CONTRACTS or ")
	TEXT("RESEARCH so an unattended capture can photograph a tab other ")
	TEXT("than the one it opens on. Args: [BUILD|CONTRACTS|RESEARCH]."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode =
		ALBSpacecraftGameMode::FindInWorld(World);
	ULBSpacecraftCommandPanelWidget* Panel =
		GameMode != nullptr ? GameMode->GetCommandPanel() : nullptr;
	if (Panel == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Tab: no command panel"));
		return;
	}
	const FString Wanted = Args.Num() > 0
		? Args[0].ToUpper() : TEXT("CONTRACTS");
	// CycleTab is the public way in, so step it until it lands rather
	// than reaching past the widget's own interface. Bounded, because a
	// loop that trusts a match it might never get is a hang.
	for (int32 Step = 0; Step < 3; ++Step)
	{
		if (Panel->GetActiveTabName() == Wanted)
		{
			break;
		}
		Panel->CycleTab(1);
	}
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.Tab -> %s"),
		*Panel->GetActiveTabName());
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftBillOfMaterialsCommand(
	TEXT("LB.Spacecraft.BillOfMaterials"),
	TEXT("Dev: totals what ONE craft costs in materials, by the cheaper ")
	TEXT("of make-or-buy at every step. Args: [recipeId=SCOUT-01]. The ")
	TEXT("economy model's weakest assumption is the material share of a ")
	TEXT("contract price - it moves the whole quality-disposition ")
	TEXT("break-even - and it had never been measured, only guessed."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	(void)World;
	using namespace LBSpacecraftBillOfMaterialsPrivate;
	const FName RecipeId = Args.Num() > 0
		? FName(*Args[0]) : FName(TEXT("SCOUT-01"));
	FLBSpacecraftRecipe Recipe;
	if (!FLBSpacecraftProductionCatalog::FindRecipe(RecipeId, Recipe))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("BOM: unknown recipe %s"), *RecipeId.ToString());
		return;
	}

	UE_LOG(LogLBSpacecraft, Display, TEXT("=== BILL OF MATERIALS: %s ==="),
		*RecipeId.ToString());
	int64 Total = 0;
	TMap<FName, int64> Unpriced;
	for (ELBSpacecraftComponent Component : Recipe.RequiredComponents)
	{
		const FName ItemId =
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(
				static_cast<uint8>(Component));
		TSet<FName> Visited;
		const int64 Each = CostOfItem(ItemId, Visited, 0, Unpriced);
		// TIMES HOW MANY THE CRAFT CARRIES. Counting one of each is
		// what made a Cargo cost the same as a Scout.
		const int32 Count =
			FLBSpacecraftProductionCatalog::ComponentCountFor(
				Recipe, Component);
		const int64 Cost = Each * Count;
		Total += Cost;
		UE_LOG(LogLBSpacecraft, Display, TEXT("  %-28s %2d x %8lld = %10lld cr"),
			*ItemId.ToString(), Count, Each / 100, Cost / 100);
	}
	UE_LOG(LogLBSpacecraft, Display, TEXT("  %-28s %10lld cr"),
		TEXT("TOTAL MATERIALS"), Total / 100);
	UE_LOG(LogLBSpacecraft, Display, TEXT("  %-28s %10lld cr"),
		TEXT("CONTRACT REVENUE"), Recipe.RevenuePence / 100);
	if (Recipe.RevenuePence > 0)
	{
		UE_LOG(LogLBSpacecraft, Display,
			TEXT("  MATERIAL SHARE OF PRICE: %.1f%%  (the model assumed 40%%)"),
			100.0 * static_cast<double>(Total)
				/ static_cast<double>(Recipe.RevenuePence));
	}
	for (const TPair<FName, int64>& Hole : Unpriced)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("  BOM HOLE: %s has neither a price nor a recipe"),
			*Hole.Key.ToString());
	}
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftScreenshotCommand(
	TEXT("LB.Spacecraft.Screenshot"),
	TEXT("Dev: waits, captures a screenshot, optionally quits. Args: ")
	TEXT("[name=LBShot] [delaySeconds=10] [quitAfter=1]. The delay is ")
	TEXT("WALL time so Nanite and streaming settle before the capture - ")
	TEXT("a frame-1 screenshot of a fresh world is grey mush. This is ")
	TEXT("the first tool that gives an unattended run EYES; every visual ")
	TEXT("claim so far has been made blind."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	if (World == nullptr)
	{
		return;
	}
	const FString Name = Args.Num() > 0 ? Args[0] : TEXT("LBShot");
	const float Delay = Args.Num() > 1
		? FMath::Max(FCString::Atof(*Args[1]), 0.1f) : 10.f;
	const bool bQuit = Args.Num() > 2 ? FCString::Atoi(*Args[2]) != 0 : true;
	FTimerHandle ShotTimer;
	World->GetTimerManager().SetTimer(ShotTimer,
		FTimerDelegate::CreateLambda([World, Name, bQuit]()
	{
		// UI IN the shot: the first split-panel capture came back
		// showing floor and no panel, because this flag said so. A
		// screenshot tool for checking UI that excludes UI is a trap.
		FScreenshotRequest::RequestScreenshot(Name,
			/*bInShowUI=*/true, /*bAddFilenameSuffix=*/false);
		UE_LOG(LogLBSpacecraft, Display,
			TEXT("LB.Spacecraft.Screenshot CAPTURING %s"), *Name);
		if (bQuit && GEngine != nullptr)
		{
			// A grace frame or two for the write, then out.
			FTimerHandle QuitTimer;
			World->GetTimerManager().SetTimer(QuitTimer,
				FTimerDelegate::CreateLambda([World]()
			{
				GEngine->Exec(World, TEXT("QUIT"));
			}), 3.f, false);
		}
	}), Delay, false);
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Screenshot ARMED: %s in %.1f s"),
		*Name, Delay);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftStatusCommand(
	TEXT("LB.Spacecraft.Status"),
	TEXT("Logs the factory, contract, unit and revenue state."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>&, UWorld* World)
{
	using namespace LBSpacecraftGameModePrivate;
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Status: no spacecraft game mode"));
		return;
	}
	SpacecraftLogStatus(*GameMode);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftSaveCommand(
	TEXT("LB.Spacecraft.Save"),
	TEXT("Saves layout+ledger+runtime. Arg: slot (default SpacecraftSlot1)."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Save: no spacecraft game mode"));
		return;
	}
	const FString Slot =
		Args.Num() > 0 ? Args[0] : TEXT("SpacecraftSlot1");
	FString Reason;
	if (!FLBSpacecraftSavePipeline::SaveToSlot(
		GameMode->MakeSaveContext(), Slot, Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Save REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Save OK -> slot %s"), *Slot);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftLoadCommand(
	TEXT("LB.Spacecraft.Load"),
	TEXT("Loads layout+ledger+runtime, rollback-safe. Arg: slot ")
	TEXT("(default SpacecraftSlot1)."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Load: no spacecraft game mode"));
		return;
	}
	const FString Slot =
		Args.Num() > 0 ? Args[0] : TEXT("SpacecraftSlot1");
	FString Reason;
	if (!FLBSpacecraftSavePipeline::LoadFromSlot(
		GameMode->MakeSaveContext(), Slot, Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Load REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Load OK <- slot %s"), *Slot);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftPowerCommand(
	TEXT("LB.Spacecraft.Power"),
	TEXT("Registers a dev power supply. Arg: capacityKw (default 2000)."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetPowerAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Power: no spacecraft game mode"));
		return;
	}
	const int32 CapacityKw =
		Args.Num() > 0 ? FCString::Atoi(*Args[0]) : 2000;
	static int32 SupplyCounter = 1;
	FString Reason;
	const FName SourceId(*FString::Printf(TEXT("Plant.Dev-%02d"),
		SupplyCounter));
	if (!GameMode->GetPowerAuthority()->RegisterSupply(SourceId, CapacityKw,
		Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Power REFUSED: %s"), *Reason);
		return;
	}
	++SupplyCounter;
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Power OK: %s (+%d kW, headroom %d kW)"),
		*SourceId.ToString(), CapacityKw,
		GameMode->GetPowerAuthority()->GetHeadroomKw());
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftGrantCommand(
	TEXT("LB.Spacecraft.Grant"),
	TEXT("Banks dev research points. Arg: points (default 100)."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetResearchAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Grant: no spacecraft game mode"));
		return;
	}
	const int32 Points = Args.Num() > 0 ? FCString::Atoi(*Args[0]) : 100;
	FString Reason;
	if (!GameMode->GetResearchAuthority()->AddPoints(Points, Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Grant REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.Grant OK: %s"),
		*Reason);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftResearchCommand(
	TEXT("LB.Spacecraft.Research"),
	TEXT("Unlocks a research node. Arg: nodeId (e.g. Research.Mfg.T1)."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetResearchAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Research: no spacecraft game mode"));
		return;
	}
	if (Args.Num() == 0)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Research: pass a node id"));
		return;
	}
	FString Reason;
	if (!GameMode->GetResearchAuthority()->UnlockNode(FName(*Args[0]),
		Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Research REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Research OK: %s"), *Reason);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftDepositCommand(
	TEXT("LB.Spacecraft.Deposit"),
	TEXT("Deposits items into the dev floor store. Args: itemId count."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	using namespace LBSpacecraftGameModePrivate;
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetInventoryAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Deposit: no spacecraft game mode"));
		return;
	}
	if (Args.Num() < 2)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Deposit: args are <itemId> <count>"));
		return;
	}
	ALBSpacecraftInventoryAuthority& Inventory =
		*GameMode->GetInventoryAuthority();
	FString Reason;
	if (!SpacecraftEnsureDevFloorStore(Inventory, Reason)
		|| !Inventory.Deposit(FName(TEXT("Store.Floor")), FName(*Args[0]),
			FCString::Atoi(*Args[1]), Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Deposit REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Deposit OK: %s x%s (floor now %d units)"),
		*Args[0], *Args[1],
		Inventory.GetUsedUnits(FName(TEXT("Store.Floor"))));
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftCraftCommand(
	TEXT("LB.Spacecraft.Craft"),
	TEXT("Crafts on the dev floor store. Args: stationClassId recipeId ")
	TEXT("[cycles=1]. The family must be researched."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	using namespace LBSpacecraftGameModePrivate;
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetCraftingAuthority() == nullptr
		|| GameMode->GetInventoryAuthority() == nullptr
		|| GameMode->GetResearchAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Craft: no spacecraft game mode"));
		return;
	}
	if (Args.Num() < 2)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Craft: args are <stationClassId> <recipeId> ")
			TEXT("[cycles]"));
		return;
	}
	const FName StationClassId(*Args[0]);
	FString Reason;
	// The dev shortcut honours the SAME research gate the builder does.
	if (!GameMode->GetResearchAuthority()->IsStationClassUnlocked(
		StationClassId))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Craft REFUSED: %s IS LOCKED - RESEARCH IT"),
			*StationClassId.ToString());
		return;
	}
	ALBSpacecraftInventoryAuthority& Inventory =
		*GameMode->GetInventoryAuthority();
	ALBSpacecraftCraftingAuthority& Crafting =
		*GameMode->GetCraftingAuthority();
	const FName DevStationId(*FString::Printf(TEXT("Dev.%s"), *Args[0]));
	const int32 Cycles =
		Args.Num() > 2 ? FMath::Max(FCString::Atoi(*Args[2]), 1) : 1;
	if (!SpacecraftEnsureDevFloorStore(Inventory, Reason)
		|| !Crafting.SelectRecipe(DevStationId, StationClassId,
			FName(*Args[1]), Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Craft REFUSED: %s"), *Reason);
		return;
	}
	for (int32 Cycle = 0; Cycle < Cycles; ++Cycle)
	{
		if (!Crafting.ExecuteCraftCycle(DevStationId, Inventory,
			FName(TEXT("Store.Floor")), FName(TEXT("Store.Floor")), Reason))
		{
			UE_LOG(LogLBSpacecraft, Warning,
				TEXT("LB.Spacecraft.Craft STOPPED AT CYCLE %d: %s"),
				Cycle, *Reason);
			return;
		}
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Craft OK: %s x%d on %s"),
		*Args[1], Cycles, *Args[0]);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftPlaceCommand(
	TEXT("LB.Spacecraft.Place"),
	TEXT("Places a station with full Phase-2 wiring (research gate, supply/")
	TEXT("store registration, power draw). Args: definitionId x y [yaw]."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Place: no spacecraft game mode"));
		return;
	}
	if (Args.Num() < 3)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Place: args are <definitionId> <x> <y> [yaw]"));
		return;
	}
	const float Yaw = Args.Num() > 3 ? FCString::Atof(*Args[3]) : 0.f;
	FName StationId;
	FString Reason;
	if (GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetPowerAuthority() == nullptr
		|| GameMode->GetInventoryAuthority() == nullptr
		|| !ALBSpacecraftGameMode::PlaceStationPowered(
			*GameMode->GetBuildAuthority(), *GameMode->GetPowerAuthority(),
			*GameMode->GetInventoryAuthority(), FName(*Args[0]),
			FTransform(FRotator(0.f, Yaw, 0.f),
				FVector(FCString::Atof(*Args[1]),
					FCString::Atof(*Args[2]), 0.f)),
			StationId, Reason, GameMode->GetProductionAuthority(),
			GameMode->GetProgression()))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Place REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Place OK: %s"), *StationId.ToString());
	// A new ship factory comes with its STARTING LOADOUT, by this route
	// as well as by the player's click - a dev command that places a
	// hall and gets a different factory than the player would is a
	// fixture that proves the wrong thing.
	FString LoadoutReason;
	const bool bLoadout = ALBSpacecraftGameMode::SeedShipFactoryLoadout(
		*GameMode->GetBuildAuthority(), *GameMode->GetPowerAuthority(),
		*GameMode->GetInventoryAuthority(), StationId, LoadoutReason,
		GameMode->GetProgression(), GameMode->GetCoordinator(),
		GameMode->GetProductionAuthority(),
		GameMode->GetTrackAuthority());
	// The REFUSAL IS LOGGED TOO. Logging only the success made a
	// fail-closed loadout completely silent, which is the one thing
	// every refusal in this project is built not to be.
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.Place %s: %s"),
		bLoadout ? TEXT("LOADOUT") : TEXT("LOADOUT SKIPPED"),
		*LoadoutReason);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftInstallCommand(
	TEXT("LB.Spacecraft.Install"),
	TEXT("Installs a unit into a slot building - the only route in for a ")
	TEXT("generator or a parts machine (owner 2026-08-26). Charged and ")
	TEXT("power-wired like the player's own install. ")
	TEXT("Args: hostStationId unitDefinitionId."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Install: no spacecraft game mode"));
		return;
	}
	if (Args.Num() < 2)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Install: args are <hostStationId> ")
			TEXT("<unitDefinitionId>"));
		return;
	}
	FName StationId;
	FString Reason;
	if (GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetPowerAuthority() == nullptr
		|| !ALBSpacecraftGameMode::InstallInSlotPowered(
			*GameMode->GetBuildAuthority(), *GameMode->GetPowerAuthority(),
			FName(*Args[0]), FName(*Args[1]), StationId, Reason,
			GameMode->GetProductionAuthority(),
			GameMode->GetInventoryAuthority()))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Install REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Install OK: %s in %s"), *StationId.ToString(),
		*Args[0]);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftDronesCommand(
	TEXT("LB.Spacecraft.Drones"),
	TEXT("Dev: logs every drone the presenter is drawing - kind, ")
	TEXT("ground or flier, position relative to its station, and mesh ")
	TEXT("size. Reads the components rather than a screenshot. The ")
	TEXT("delay is WALL time: from -ExecCmds this runs at frame zero, ")
	TEXT("when the presenter has built nothing and the dump is empty. ")
	TEXT("Args: [delaySeconds=0]."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	if (World == nullptr)
	{
		return;
	}
	const float Delay = Args.Num() > 0
		? FMath::Max(FCString::Atof(*Args[0]), 0.f) : 0.f;
	auto Dump = [World]()
	{
		ALBSpacecraftGameMode* GameMode =
			ALBSpacecraftGameMode::FindInWorld(World);
		if (GameMode == nullptr || GameMode->GetPresenter() == nullptr)
		{
			UE_LOG(LogLBSpacecraft, Warning,
				TEXT("LB.Spacecraft.Drones: no presenter"));
			return;
		}
		GameMode->GetPresenter()->LogDroneCrew();
		// The CAMERA too: every framing complaint so far has been an
		// argument about a screenshot. This says where the camera
		// actually is, so "the zoom I asked for was not the zoom I
		// got" becomes a fact rather than a suspicion.
		if (const APlayerController* Controller =
			World->GetFirstPlayerController())
		{
			if (const ALBSpacecraftPlayerPawn* Pawn =
				Cast<ALBSpacecraftPlayerPawn>(Controller->GetPawn()))
			{
				UE_LOG(LogLBSpacecraft, Display,
					TEXT("CAMERA pivot=(%.0f,%.0f,%.0f) arm=%.0f ")
					TEXT("desired=%.0f fov=%.1f siteMap=%d"),
					Pawn->GetActorLocation().X,
					Pawn->GetActorLocation().Y,
					Pawn->GetActorLocation().Z,
					Pawn->GetCameraArmLengthCm(),
					Pawn->GetDesiredZoomCm(),
					Pawn->GetCameraFovDeg(),
					Pawn->IsSiteMapView() ? 1 : 0);
			}
		}
	};
	if (Delay <= 0.f)
	{
		Dump();
		return;
	}
	FTimerHandle DumpTimer;
	World->GetTimerManager().SetTimer(DumpTimer,
		FTimerDelegate::CreateLambda(Dump), Delay, false);
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Drones ARMED in %.1f s"), Delay);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftWatchStationCommand(
	TEXT("LB.Spacecraft.Watch"),
	TEXT("Dev: frames ONE station close enough to see its drones work. ")
	TEXT("LB.Spacecraft.Enter frames a whole 160 m hall, at which range ")
	TEXT("a 3 m drone is a speck - a capture taken from there proves ")
	TEXT("nothing about what the crew is doing. Args: [stationId] ")
	TEXT("[zoomCm]; with no station, the first LINE station."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	APlayerController* Controller =
		World != nullptr ? World->GetFirstPlayerController() : nullptr;
	ALBSpacecraftPlayerPawn* Pawn = Controller != nullptr
		? Cast<ALBSpacecraftPlayerPawn>(Controller->GetPawn()) : nullptr;
	if (GameMode == nullptr || Pawn == nullptr
		|| GameMode->GetBuildAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Watch: no spacecraft pawn"));
		return;
	}
	FName Target = Args.Num() > 0 ? FName(*Args[0]) : NAME_None;
	if (Target.IsNone())
	{
		for (const FLBSpacecraftStationRecord& Record :
			GameMode->GetBuildAuthority()->GetStations())
		{
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			if (Definition != nullptr && Definition->DroneSlotCount > 0)
			{
				Target = Record.StationId;
				break;
			}
		}
	}
	if (Target.IsNone())
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Watch: no crewed station to watch"));
		return;
	}
	const float ZoomCm = Args.Num() > 1
		? FMath::Max(FCString::Atof(*Args[1]), 500.f) : 4200.f;
	Pawn->WatchStation(Target, ZoomCm);
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Watch OK: %s at %.0f cm"),
		*Target.ToString(), ZoomCm);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftDismissCommand(
	TEXT("LB.Spacecraft.Dismiss"),
	TEXT("Dismisses drones from a station's slots - the symmetric half ")
	TEXT("of LB.Spacecraft.Hire, and the only way to SWAP a crew for a ")
	TEXT("different kind while at nominal strength. ALL empties every ")
	TEXT("station that has slots. Args: <stationId|ALL> [count=1]."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr
		|| Args.Num() < 1)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Dismiss: args are <stationId|ALL> ")
			TEXT("[count]"));
		return;
	}
	const int32 Count = Args.Num() > 1
		? FMath::Max(1, FCString::Atoi(*Args[1])) : 1;
	ALBSpacecraftBuildAuthority& Build = *GameMode->GetBuildAuthority();
	TArray<FName> Targets;
	if (Args[0].Equals(TEXT("ALL"), ESearchCase::IgnoreCase))
	{
		for (const FLBSpacecraftStationRecord& Record : Build.GetStations())
		{
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			if (Definition != nullptr && Definition->DroneSlotCount > 0)
			{
				Targets.Add(Record.StationId);
			}
		}
	}
	else
	{
		Targets.Add(FName(*Args[0]));
	}
	int32 Dismissed = 0;
	FString Reason;
	for (const FName& StationId : Targets)
	{
		for (int32 Slot = 0; Slot < Count; ++Slot)
		{
			// Always the LAST slot: dismissing from the front would
			// renumber the rest under the caller's feet.
			const FLBSpacecraftStationRecord* Record =
				Build.FindStation(StationId);
			if (Record == nullptr || Record->InstalledDrones <= 0)
			{
				break;
			}
			if (!ALBSpacecraftGameMode::DismissStationDronePowered(
				Build, StationId, Record->InstalledDrones - 1, Reason,
				GameMode->GetProductionAuthority()))
			{
				UE_LOG(LogLBSpacecraft, Warning,
					TEXT("LB.Spacecraft.Dismiss REFUSED at %s: %s"),
					*StationId.ToString(), *Reason);
				break;
			}
			++Dismissed;
		}
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Dismiss OK: %d across %d station(s)"),
		Dismissed, Targets.Num());
}));
#endif // !UE_BUILD_SHIPPING

// HOW MANY CRANES - open, and meant to be COMPARED rather than argued
// about (owner 2026-08-29: "1 crane does all work, will have to test
// each"). Default is one per gap, which is what he asked for first; set
// it to 0 for a single crane serving the whole line and rebuild the
// hall to see the other model.
static TAutoConsoleVariable<int32> GLBSpacecraftCranePerGap(
	TEXT("LB.Spacecraft.CranePerGap"),
	1,
	TEXT("1 = a gantry between every pair of stations (N-1 cranes). ")
	TEXT("0 = one gantry serving the whole line. ")
	TEXT("Takes effect when the hall interior is next built."),
	ECVF_Default);

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftHireCommand(
	TEXT("LB.Spacecraft.Hire"),
	TEXT("Hires drones of a named kind onto a station's slots - the same ")
	TEXT("route as the panel's HIRE buttons, charged and progression-")
	TEXT("gated identically. ALL crews every station that has slots. ")
	TEXT("Args: <stationId|ALL> <kindId> [count=1]."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Hire: no spacecraft game mode"));
		return;
	}
	if (Args.Num() < 2)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Hire: args are <stationId|ALL> ")
			TEXT("<kindId> [count]"));
		return;
	}
	const FName KindId(*Args[1]);
	if (ALBSpacecraftBuildAuthority::FindDroneKind(KindId) == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Hire REFUSED: no drone kind named %s"),
			*Args[1]);
		return;
	}
	const int32 Count = Args.Num() > 2
		? FMath::Max(1, FCString::Atoi(*Args[2])) : 1;
	ALBSpacecraftBuildAuthority& Build = *GameMode->GetBuildAuthority();
	TArray<FName> Targets;
	if (Args[0].Equals(TEXT("ALL"), ESearchCase::IgnoreCase))
	{
		for (const FLBSpacecraftStationRecord& Record : Build.GetStations())
		{
			const FLBSpacecraftStationDefinition* Definition =
				ALBSpacecraftBuildAuthority::FindDefinition(
					Record.DefinitionId);
			if (Definition != nullptr && Definition->DroneSlotCount > 0)
			{
				Targets.Add(Record.StationId);
			}
		}
	}
	else
	{
		Targets.Add(FName(*Args[0]));
	}
	int32 Hired = 0;
	FString Reason;
	for (const FName& StationId : Targets)
	{
		for (int32 Slot = 0; Slot < Count; ++Slot)
		{
			if (!ALBSpacecraftGameMode::InstallStationDronePowered(
				Build, StationId, Reason,
				GameMode->GetProductionAuthority(),
				GameMode->GetProgression(), KindId))
			{
				// Fail-closed and SAY WHY: a refusal here is the
				// player's own refusal string, not a silent no-op.
				UE_LOG(LogLBSpacecraft, Warning,
					TEXT("LB.Spacecraft.Hire REFUSED at %s: %s"),
					*StationId.ToString(), *Reason);
				break;
			}
			++Hired;
		}
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Hire OK: %d x %s across %d station(s)"),
		Hired, *Args[1], Targets.Num());
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftSelectCommand(
	TEXT("LB.Spacecraft.Select"),
	TEXT("Selects a recipe on a placed station. Args: stationId recipeId."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Select: no spacecraft game mode"));
		return;
	}
	if (Args.Num() < 2)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Select: args are <stationId> <recipeId>"));
		return;
	}
	FString Reason;
	if (GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetCraftingAuthority() == nullptr
		|| GameMode->GetResearchAuthority() == nullptr
		|| !ALBSpacecraftGameMode::SelectStationRecipe(
			*GameMode->GetBuildAuthority(), *GameMode->GetCraftingAuthority(),
			*GameMode->GetResearchAuthority(), FName(*Args[0]),
			FName(*Args[1]), Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Select REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display,
		TEXT("LB.Spacecraft.Select OK: %s on %s"), *Args[1], *Args[0]);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftCommissionCommand(
	TEXT("LB.Spacecraft.Commission"),
	TEXT("Commissions the placed stations and configures the coordinator - ")
	TEXT("the player-built counterpart of BuildLine's canonical shortcut."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>&, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetCoordinator() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Commission: no spacecraft game mode"));
		return;
	}
	FString Reason;
	if (!GameMode->GetBuildAuthority()->CommissionFactory(Reason)
		|| !GameMode->GetCoordinator()->ConfigureFromAuthorities(
			GameMode->GetBuildAuthority(), GameMode->GetProductionAuthority(),
			Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Commission REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display, TEXT(
		"LB.Spacecraft.Commission OK: %d stations, route %d"),
		GameMode->GetBuildAuthority()->GetStations().Num(),
		GameMode->GetCoordinator()->GetRoute().Num());
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftBuyBayCommand(
	TEXT("LB.Spacecraft.BuyBay"),
	TEXT("LB.Spacecraft.BuyBay <BayX> <BayY> - buy one expansion bay ")
	TEXT("with credits (adjacent to owned land, never runway)."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetProgression() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.BuyBay: no spacecraft game mode"));
		return;
	}
	if (Args.Num() < 2)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.BuyBay <BayX> <BayY>"));
		return;
	}
	FString Reason;
	const bool bOk = GameMode->GetProgression()->PurchaseBay(
		FIntPoint(FCString::Atoi(*Args[0]), FCString::Atoi(*Args[1])),
		GameMode->GetProductionAuthority(), Reason);
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.BuyBay %s: %s"),
		bOk ? TEXT("OK") : TEXT("REFUSED"), *Reason);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftBeltCommand(
	TEXT("LB.Spacecraft.Belt"),
	TEXT("LB.Spacecraft.Belt <StationId> - connect a supply belt from the ")
	TEXT("station to the floor store (auto-routed, charged, fail-closed)."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetTransportAuthority() == nullptr
		|| GameMode->GetBuildAuthority() == nullptr
		|| GameMode->GetInventoryAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Belt: no spacecraft game mode"));
		return;
	}
	if (Args.Num() < 1)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Belt <StationId>"));
		return;
	}
	FName RouteId;
	FString Reason;
	const bool bOk = GameMode->GetTransportAuthority()->ConnectSupplyBelt(
		*GameMode->GetBuildAuthority(), *GameMode->GetInventoryAuthority(),
		GameMode->GetProductionAuthority(), FName(*Args[0]),
		FName(TEXT("Store.Floor")), RouteId, Reason,
		GameMode->GetProgression());
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.Belt %s: %s"),
		bOk ? TEXT("OK") : TEXT("REFUSED"), *Reason);
}));
#endif // !UE_BUILD_SHIPPING

// DEV COMMAND - COMPILED OUT OF SHIPPING. These drive and cheat the
// game freely (grant points, bank materials, build the whole
// factory, skip a craft to any stage), which is exactly right for
// headless verification and a reviewer build, and exactly wrong in
// a retail one.
#if !UE_BUILD_SHIPPING
static FAutoConsoleCommandWithWorldAndArgs GLBSpacecraftOrderCommand(
	TEXT("LB.Spacecraft.Order"),
	TEXT("Buys raw materials with cash; they arrive at the floor store on ")
	TEXT("the sim clock. Args: itemId count."),
	FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
		[](const TArray<FString>& Args, UWorld* World)
{
	using namespace LBSpacecraftGameModePrivate;
	ALBSpacecraftGameMode* GameMode = ALBSpacecraftGameMode::FindInWorld(World);
	if (GameMode == nullptr || GameMode->GetInventoryAuthority() == nullptr
		|| GameMode->GetProductionAuthority() == nullptr)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Order: no spacecraft game mode"));
		return;
	}
	if (Args.Num() < 2)
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Order: args are <itemId> <count>"));
		return;
	}
	FString Reason;
	const int32 OrderCount = FCString::Atoi(*Args[1]);
	const FName DeliveryStore = ALBSpacecraftGameMode::FindDeliveryStore(
		*GameMode->GetBuildAuthority(), *GameMode->GetInventoryAuthority(),
		FName(*Args[0]), OrderCount, Reason);
	if (DeliveryStore.IsNone()
		|| !ALBSpacecraftGameMode::PlaceResourceOrder(
			*GameMode->GetInventoryAuthority(),
			*GameMode->GetProductionAuthority(), FName(*Args[0]),
			OrderCount, DeliveryStore, Reason))
	{
		UE_LOG(LogLBSpacecraft, Warning,
			TEXT("LB.Spacecraft.Order REFUSED: %s"), *Reason);
		return;
	}
	UE_LOG(LogLBSpacecraft, Display, TEXT("LB.Spacecraft.Order OK: %s"),
		*Reason);
}));
#endif // !UE_BUILD_SHIPPING

bool ALBSpacecraftGameMode::SeedStarterSpine(FString& OutReason)
{
	if (BuildAuthority == nullptr || PowerAuthority == nullptr
		|| InventoryAuthority == nullptr)
	{
		OutReason = TEXT("STARTER SPINE NEEDS THE AUTHORITIES");
		return false;
	}
	if (BuildAuthority->GetStations().Num() > 0)
	{
		OutReason = TEXT("FLOOR IS NOT EMPTY - SPINE NOT SEEDED");
		return false;
	}
	if (Progression != nullptr)
	{
		FString LandReason;
		Progression->SeedStartingBays(LandReason);
	}
	// The same placement path the player uses, charged against starting
	// capital - the spine is bought, not conjured (honest economy).
	struct FLBSpacecraftSpineEntry
	{
		const TCHAR* DefinitionId;
		FVector LocationCm;
	};
	// The generator goes in its HALL, never loose on the floor (owner
	// 2026-08-26: "its supposed to be in its own building"), so the
	// spine builds the power station and installs a plant in a slot.
	const FLBSpacecraftSpineEntry Spine[] = {
		{ TEXT("PowerStation"), FVector(-6000.f, -4500.f, 0.f) },
		{ TEXT("MaterialProcessor"), FVector(-6000.f, 0.f, 0.f) },
		{ TEXT("StorageRack"), FVector(-8500.f, 0.f, 0.f) },
		// Somewhere for bought goods to arrive. Without a dock the
		// starting factory could order nothing at all, which is a
		// harsh way to meet a new mechanic.
		{ TEXT("DeliveryDock"), FVector(-8500.f, 3000.f, 0.f) },
	};
	for (const FLBSpacecraftSpineEntry& Entry : Spine)
	{
		FName StationId;
		if (!PlaceStationPowered(*BuildAuthority, *PowerAuthority,
			*InventoryAuthority, FName(Entry.DefinitionId),
			FTransform(FRotator::ZeroRotator, Entry.LocationCm),
			StationId, OutReason, ProductionAuthority, Progression))
		{
			return false; // fail closed - an empty floor stays empty
		}
		if (FName(Entry.DefinitionId) == FName(TEXT("PowerStation")))
		{
			FName PlantId;
			if (!InstallInSlotPowered(*BuildAuthority, *PowerAuthority,
				StationId, FName(TEXT("PowerPlant")), PlantId,
				OutReason, ProductionAuthority, InventoryAuthority))
			{
				return false; // no generator, no factory
			}
		}
	}
	OutReason = TEXT("STARTER SPINE READY - COMPLETE THE LINE");
	return true;
}

bool ALBSpacecraftGameMode::SeedShipFactoryLoadout(
	ALBSpacecraftBuildAuthority& InBuild,
	ALBSpacecraftPowerAuthority& InPower,
	ALBSpacecraftInventoryAuthority& InInventory,
	FName HallId, FString& OutReason,
	ALBSpacecraftProgressionAuthority* InProgression,
	ALBSpacecraftRuntimeCoordinator* InCoordinator,
	ALBSpacecraftProductionAuthority* InProduction,
	ALBSpacecraftTrackAuthority* InTrack)
{
	const FLBSpacecraftStationRecord* Hall = InBuild.FindStation(HallId);
	const FLBSpacecraftStationDefinition* HallDefinition = Hall != nullptr
		? ALBSpacecraftBuildAuthority::FindDefinition(Hall->DefinitionId)
		: nullptr;
	if (HallDefinition == nullptr || !HallDefinition->bSiteBuilding
		|| HallDefinition->InteriorFloorCm.IsNearlyZero())
	{
		OutReason = TEXT("THE STARTING LOADOUT NEEDS A HALL WITH A FLOOR");
		return false;
	}
	// ONCE, EVER. A second hall, a reload, a restored save - none of
	// them gets another free station and crew.
	for (const FLBSpacecraftStationRecord& Record : InBuild.GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				Record.DefinitionId);
		if (Definition != nullptr && !Definition->StageClassId.IsNone())
		{
			OutReason =
				TEXT("THE LINE ALREADY HAS A STATION - LOADOUT SKIPPED");
			return false;
		}
	}
	// The station goes at the HALL'S OWN CENTRE. Offsetting it up the
	// track looked tidier and was wrong: land is owned bay by bay, and
	// a station placed 45 m off the hall's centre can land on a bay the
	// player does not own - "BAY (0,-1) IS NOT YOURS - BUY THE BAY
	// FIRST" is what a loadout must never say. The hall's own footprint
	// is land they have just paid for, by definition.
	const FVector HallAt = Hall->WorldTransform.GetLocation();
	const FVector StationAt(HallAt.X, HallAt.Y, 0.f);
	FName StationId;
	// Placed through THE PLAYER'S OWN PATH so the store, the power
	// supply and the power draw are all wired exactly as they would be
	// for a station they bought - but with a NULL LEDGER, which is what
	// makes it free. A loadout is a gift, like starting capital; it is
	// not a purchase the player did not authorise.
	if (!PlaceStationPowered(InBuild, InPower, InInventory,
		FName(TEXT("AssemblyRobot")),
		FTransform(FRotator::ZeroRotator, StationAt), StationId,
		OutReason, /*InLedger=*/nullptr, InProgression))
	{
		return false; // fail closed - a hall with no station is honest
	}
	// Parts arrive beside the line and are fitted from the station's own
	// local stockpile - never a global pool - so this shelf is where the
	// starting kit has to land.
	const FName StoreId(*FString::Printf(TEXT("Store.%s"),
		*StationId.ToString()));

	// ONE OF EACH DRONE, as asked. The kinds are read from the
	// catalogue rather than listed here, so a kind added later joins
	// the loadout automatically and this cannot drift out of date.
	int32 Hired = 0;
	FString HireReason;
	for (const FLBSpacecraftDroneKind& Kind :
		ALBSpacecraftBuildAuthority::DroneKinds())
	{
		// Straight onto the authority, deliberately: the panel's hire
		// route charges the player and is gated on QUALITY CONTROL
		// after three deliveries, and a starting crew is neither bought
		// nor earned. A refusal here is not fatal - a station with
		// fewer drones still runs, just slower.
		if (InBuild.InstallStationDrone(StationId, HireReason,
			Kind.KindId))
		{
			++Hired;
		}
	}

	// THE PARTS FOR THE FIRST CRAFT, on the station's own shelf.
	//
	// Without this the loadout is a dead end rather than a slow start,
	// and it was measured rather than guessed: place the hall, take the
	// station and its crew, accept a contract, and the craft sits at
	// stage 0 for nine hundred simulated seconds holding on
	// "INSUFFICIENT RESOURCES" with an empty shelf, no dock to order
	// from and no storage to order into. A starting loadout that cannot
	// build the thing it is for is not a loadout.
	//
	// ONE set, not two: enough to build, test and launch the first
	// craft, so the player sees the whole loop once. After that,
	// supply is the game and they sort it out themselves.
	int32 Stocked = 0;
	for (uint8 Component = 0;
		Component <= static_cast<uint8>(ELBSpacecraftComponent::Interior);
		++Component)
	{
		const FName ItemId =
			FLBSpacecraftItemCatalogue::GetAssembledComponentItemId(
				Component);
		FString StockReason;
		if (!ItemId.IsNone()
			&& InInventory.Deposit(StoreId, ItemId, 1, StockReason))
		{
			++Stocked;
		}
	}

	// THE SPRAY BOOTH, downstream of the fitting station (owner
	// 2026-08-28: required, and in the starting loadout). Placed at a
	// GREATER Y so it sorts after the assembly station in line order -
	// the craft is built, then painted, then goes out the door. A booth
	// upstream of the fitting would paint a craft and then bolt parts
	// onto the wet finish.
	FName BoothId;
	FString BoothReason;
	if (!PlaceStationPowered(InBuild, InPower, InInventory,
		FName(TEXT("SprayBooth")),
		FTransform(FRotator::ZeroRotator,
			StationAt + FVector(0.f, 2800.f, 0.f)), BoothId,
		BoothReason, /*InLedger=*/nullptr, InProgression))
	{
		// Fail closed: the line REQUIRES a booth, so a loadout without
		// one would hand the player a factory that cannot commission.
		OutReason = BoothReason;
		return false;
	}
	// The booth's own crew: spray drones, which is the job they were
	// named for and had nowhere to do until now.
	for (int32 Slot = 0; Slot < 2; ++Slot)
	{
		FString BoothCrewReason;
		InBuild.InstallStationDrone(BoothId, BoothCrewReason,
			FName(TEXT("Spray")));
	}

	// LAY THE TRACK THROUGH BOTH (owner 2026-08-28: "have you got
	// convayer?" then "lay the track as part of the starting loadout -
	// station, booth and a line running through both").
	//
	// The line track is the conveyor the CRAFT rides. The system has
	// existed all along and the loadout never used it, so a new player
	// got stations with nothing running between them - which is why the
	// floor read as objects on concrete rather than a production line.
	// In both reference games the conveyor is the most prominent thing
	// in frame.
	//
	// Pieces are 400 cm, so the geometry has to land on that grid: the
	// start sits 2000 cm before the fitting station, which puts the
	// station on the fifth straight and the booth - 2800 cm further -
	// on the twelfth. That is also why the booth moved from 2600 to
	// 2800: a station between two pieces cannot take a node.
	if (InTrack != nullptr)
	{
		const float PieceCm =
			ALBSpacecraftTrackAuthority::GetPieceLengthCm();
		const int32 StationPiece = 5;
		const int32 BoothPiece = 12;
		const int32 Straights = 14;
		FName PieceId;
		FString TrackReason;
		TArray<FName> Straight;
		// Yaw 90: the line runs up +Y, which is the axis every line
		// this game has ever laid runs along and the order BuildRoute
		// sorts by.
		const bool bStarted = InTrack->StartLine(
			FTransform(FRotator(0.f, 90.f, 0.f),
				StationAt - FVector(0.f, PieceCm * StationPiece, 0.f)),
			PieceId, TrackReason);
		if (bStarted)
		{
			for (int32 Piece = 0; Piece < Straights; ++Piece)
			{
				if (!InTrack->ExtendLine(
					ELBSpacecraftTrackPiece::Straight, PieceId,
					TrackReason))
				{
					break;
				}
				Straight.Add(PieceId);
			}
			InTrack->ExtendLine(ELBSpacecraftTrackPiece::End, PieceId,
				TrackReason);
			// EVERY line station takes a node or the coordinator
			// refuses to route from the track at all - it counts nodes
			// against route steps. A half-attached line would be worse
			// than no line.
			const bool bAttached =
				Straight.IsValidIndex(StationPiece - 1)
				&& Straight.IsValidIndex(BoothPiece - 1)
				&& InTrack->AttachStationNode(StationId,
					Straight[StationPiece - 1], &InBuild, TrackReason)
				&& InTrack->AttachStationNode(BoothId,
					Straight[BoothPiece - 1], &InBuild, TrackReason);
			if (!bAttached)
			{
				// Fail closed by taking the track back out: a laid but
				// unattached track stops the factory routing entirely,
				// and a loadout must never hand the player that.
				FString Ignored;
				while (InTrack->GetPieces().Num() > 0
					&& InTrack->RemoveOpenEnd(Ignored))
				{
				}
			}
		}
	}

	// COMMISSION IT, so the test and the departure are there from the
	// first minute (owner: "and the test and departure"). An
	// uncommissioned factory refuses to route, and a player whose first
	// craft cannot leave has not seen the game.
	FString CommissionReason;
	if (!InBuild.CommissionFactory(CommissionReason))
	{
		OutReason = CommissionReason;
		return false;
	}
	// COMMISSIONED IS NOT ENOUGH. Commissioning and configuring are one
	// act everywhere else in the game - the panel's own COMMISSION
	// button does both - and a factory that is commissioned but not
	// configured answers "COORDINATOR IS NOT CONFIGURED" the first time
	// the player starts production. Splitting them here would ship that
	// as the opening experience.
	if (InCoordinator != nullptr && InProduction != nullptr)
	{
		FString ConfigureReason;
		if (!InCoordinator->ConfigureFromAuthorities(&InBuild,
			InProduction, ConfigureReason, InTrack))
		{
			OutReason = ConfigureReason;
			return false;
		}
	}
	OutReason = FString::Printf(
		TEXT("STARTING LOADOUT READY - %s CREWED BY %d DRONES WITH ")
		TEXT("PARTS FOR %d COMPONENTS; THE WHOLE BUILD HAPPENS HERE"),
		*StationId.ToString(), Hired, Stocked);
	return true;
}

void ALBSpacecraftGameMode::CancelLaunchCamera()
{
	if (!bLaunchCameraLive)
	{
		return;
	}
	bLaunchCameraSuppressed = true;
	bLaunchCameraLive = false;
	UWorld* World = GetWorld();
	APlayerController* PlayerController = World != nullptr
		? World->GetFirstPlayerController() : nullptr;
	if (PlayerController != nullptr
		&& PlayerController->GetPawn() != nullptr)
	{
		PlayerController->SetViewTargetWithBlend(
			PlayerController->GetPawn(), 0.5f);
	}
}

void ALBSpacecraftGameMode::TickLaunchCamera()
{
	UWorld* World = GetWorld();
	if (World == nullptr || World->GetGameViewport() == nullptr
		|| Presenter == nullptr || !bLaunchCameraEnabled)
	{
		return;
	}
	APlayerController* PlayerController =
		World->GetFirstPlayerController();
	if (PlayerController == nullptr)
	{
		return;
	}
	FVector ShipCm;
	float Elapsed = 0.f;
	float CraftHalfLenCm = 700.f;
	const bool bDeparting =
		Presenter->GetActiveDeparture(ShipCm, Elapsed, &CraftHalfLenCm);
	if (!bDeparting)
	{
		// The show is over: hand the view back and re-arm for next time.
		if (bLaunchCameraLive)
		{
			bLaunchCameraLive = false;
			if (PlayerController->GetPawn() != nullptr)
			{
				PlayerController->SetViewTargetWithBlend(
					PlayerController->GetPawn(), 0.8f);
			}
		}
		bLaunchCameraSuppressed = false;
		return;
	}
	if (bLaunchCameraSuppressed)
	{
		return; // the player waved the director off this launch
	}
	if (LaunchCamera == nullptr)
	{
		LaunchCamera = World->SpawnActor<ACameraActor>();
		if (LaunchCamera != nullptr
			&& LaunchCamera->GetCameraComponent() != nullptr)
		{
			// Long lens: the sprint shot compresses like film.
			LaunchCamera->GetCameraComponent()->SetFieldOfView(35.f);
		}
	}
	if (LaunchCamera == nullptr)
	{
		return;
	}
	FVector CameraCm;
	FVector LookAtCm;
	ALBSpacecraftWIPPresentationActor::ComputeLaunchCameraPose(
		Elapsed, ShipCm,
		Presenter->ChicaneSeconds, CameraCm, LookAtCm, CraftHalfLenCm);
	LaunchCamera->SetActorLocationAndRotation(CameraCm,
		(LookAtCm - CameraCm).Rotation());
	if (!bLaunchCameraLive)
	{
		bLaunchCameraLive = true;
		PlayerController->SetViewTargetWithBlend(LaunchCamera, 0.7f);
	}
}

void ALBSpacecraftGameMode::TogglePauseMenu()
{
	UWorld* World = GetWorld();
	if (World == nullptr || World->GetGameViewport() == nullptr)
	{
		return; // headless journeys have no menu and never pause
	}
	APlayerController* PlayerController =
		World->GetFirstPlayerController();
	if (PlayerController == nullptr)
	{
		return;
	}
	if (PauseMenu != nullptr && PauseMenu->IsInViewport())
	{
		PauseMenu->RemoveFromParent();
		UGameplayStatics::SetGamePaused(World, false);
		return;
	}
	if (PauseMenu == nullptr)
	{
		PauseMenu = CreateWidget<ULBSpacecraftPauseMenuWidget>(
			PlayerController, ULBSpacecraftPauseMenuWidget::StaticClass());
		if (PauseMenu == nullptr)
		{
			return;
		}
		PauseMenu->BindGame(this);
	}
	PauseMenu->AddToViewport(200);
	UGameplayStatics::SetGamePaused(World, true);
}
