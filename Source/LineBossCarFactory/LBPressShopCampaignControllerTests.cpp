#include "LBPressShopCampaignController.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBPR004Station.h"
#include "LBPR005Station.h"
#include "LBPR006Station.h"
#include "LBPR007Station.h"
#include "LBPR008Station.h"
#include "LBPR009Station.h"
#include "LBPR010Station.h"
#include "LBPressShopSaveGame.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressTrainAStation.h"
#include "LBPressTrainIdentitySubsystem.h"
#include "LBStillageFLTFleetController.h"
#include "LBFactoryManagementSubsystem.h"
#include "LBFactoryBrandSubsystem.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBFactoryTransportLink.h"
#include "LBBodyWeldLineActor.h"
#include "LBECoatLineActor.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBPressShopStorageZone.h"
#include "LBInboundDeliveryController.h"
#include "LBCoilAGVController.h"
#include "LBPressShopSupportFleetController.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPressShopCampaignRoundTripTest,
    "LineBoss.PressShop.Save.WholeShopCampaignRoundTrip",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltCampaignRoundTripTest,
    "LineBoss.PressShop.Save.PlayerBuiltV18ManagementAndBodyWeldRoundTrip",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
template <typename T>
int32 CountLiveActors(UWorld* World)
{
    int32 Count = 0;
    if (!World) return Count;
    for (TActorIterator<T> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++Count;
    }
    return Count;
}

struct FLBCampaignTestFixture
{
    UWorld* World = nullptr;
    ALBPR004Station* PR004 = nullptr;
    ALBPR005Station* PR005 = nullptr;
    ALBPR006Station* PR006 = nullptr;
    ALBPR007Station* PR007 = nullptr;
    ALBPR008Station* PR008 = nullptr;
    ALBPR009Station* PR009 = nullptr;
    ALBPR010Station* PR010 = nullptr;
    ALBPressTrainAStation* Train = nullptr;
    ALBControlRoomOperationsConsole* Console = nullptr;
    ALBPressShopCampaignController* Campaign = nullptr;
    ALBPressShopBuildAuthority* BuildAuthority = nullptr;
    ALBStillageFLTFleetController* StillageFleet = nullptr;
    ULBFactoryManagementSubsystem* Management = nullptr;

    bool IsValid(const bool bRequireTrain = true) const
    {
        return World && PR004 && PR005 && PR006 && PR007 && PR008 && PR009 && PR010
            && (!bRequireTrain || Train) && Console && Campaign && BuildAuthority
            && StillageFleet && Management;
    }
};

FLBCampaignTestFixture CreateCampaignFixture(const FName WorldName, const bool bSpawnTrain = true)
{
    FLBCampaignTestFixture Fixture;
    Fixture.World = UWorld::CreateWorld(EWorldType::Game, false, WorldName);
    if (!Fixture.World) return Fixture;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(Fixture.World);
    Fixture.World->InitializeActorsForPlay(FURL());
    Fixture.PR004 = Fixture.World->SpawnActor<ALBPR004Station>();
    Fixture.PR005 = Fixture.World->SpawnActor<ALBPR005Station>();
    Fixture.PR006 = Fixture.World->SpawnActor<ALBPR006Station>();
    Fixture.PR007 = Fixture.World->SpawnActor<ALBPR007Station>();
    Fixture.PR008 = Fixture.World->SpawnActor<ALBPR008Station>();
    Fixture.PR009 = Fixture.World->SpawnActor<ALBPR009Station>();
    Fixture.PR010 = Fixture.World->SpawnActor<ALBPR010Station>();
    if (bSpawnTrain) Fixture.Train = Fixture.World->SpawnActor<ALBPressTrainAStation>();
    Fixture.Console = Fixture.World->SpawnActor<ALBControlRoomOperationsConsole>();
    Fixture.Campaign = Fixture.World->SpawnActor<ALBPressShopCampaignController>();
    Fixture.BuildAuthority = Fixture.World->SpawnActor<ALBPressShopBuildAuthority>();
    if (Fixture.BuildAuthority)
    {
        FLBPressShopBuildBay Bay;
        Bay.BayId = TEXT("CAMPAIGN-AUTOMATION-FLOOR");
        Bay.Centre = FVector::ZeroVector;
        Bay.HalfExtent = FVector(25000.0f, 25000.0f, 2000.0f);
        Fixture.BuildAuthority->BuildBays.Add(Bay);
        FLBPressShopUtilitySpine Utility;
        Utility.SpineId = TEXT("CAMPAIGN-AUTOMATION-UTILITY");
        Utility.Start = FVector(-25000.0f, 0.0f, 0.0f);
        Utility.End = FVector(25000.0f, 0.0f, 0.0f);
        Utility.MaximumConnectionDistanceCm = 25000.0f;
        Fixture.BuildAuthority->UtilitySpines.Add(Utility);
    }
    Fixture.StillageFleet = Fixture.World->SpawnActor<ALBStillageFLTFleetController>();
    Fixture.World->BeginPlay();
    // The real GameMode commissions the starter explicitly. Synthetic automation
    // worlds do not own that GameMode, so establish the same one-starter contract.
    if (Fixture.StillageFleet) Fixture.StillageFleet->InitialiseFreshFleet();
    Fixture.Management = Fixture.World->GetSubsystem<ULBFactoryManagementSubsystem>();
    if (Fixture.Management)
    {
        Fixture.Management->InitialiseNewCampaign(
            ULBFactoryManagementSubsystem::DefaultStartingCashPence, 0);
    }
    return Fixture;
}

FLBCampaignTestFixture CreatePlayerBuiltCampaignFixture(const FName WorldName)
{
    FLBCampaignTestFixture Fixture;
    Fixture.World = UWorld::CreateWorld(EWorldType::Game, false, WorldName);
    if (!Fixture.World) return Fixture;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(Fixture.World);
    Fixture.World->InitializeActorsForPlay(FURL());
    Fixture.Campaign = Fixture.World->SpawnActor<ALBPressShopCampaignController>();
    Fixture.BuildAuthority = Fixture.World->SpawnActor<ALBPressShopBuildAuthority>();
    if (Fixture.BuildAuthority)
    {
        FLBPressShopBuildBay Bay;
        Bay.BayId = TEXT("PLAYER-BUILT-CAMPAIGN-AUTOMATION-FLOOR");
        Bay.Centre = FVector::ZeroVector;
        Bay.HalfExtent = FVector(25000.0f, 25000.0f, 2000.0f);
        Fixture.BuildAuthority->BuildBays.Add(Bay);
        FLBPressShopUtilitySpine Utility;
        Utility.SpineId = TEXT("PLAYER-BUILT-CAMPAIGN-AUTOMATION-UTILITY");
        Utility.Start = FVector(-25000.0f, 0.0f, 0.0f);
        Utility.End = FVector(25000.0f, 0.0f, 0.0f);
        Utility.MaximumConnectionDistanceCm = 25000.0f;
        Fixture.BuildAuthority->UtilitySpines.Add(Utility);
    }
    Fixture.StillageFleet = Fixture.World->SpawnActor<ALBStillageFLTFleetController>();
    Fixture.World->BeginPlay();
    if (Fixture.StillageFleet) Fixture.StillageFleet->InitialiseFreshFleet();
    Fixture.Management = Fixture.World->GetSubsystem<ULBFactoryManagementSubsystem>();
    if (Fixture.Management)
    {
        Fixture.Management->InitialiseNewCampaign(
            ULBFactoryManagementSubsystem::DefaultStartingCashPence, 0);
    }
    return Fixture;
}

bool IsPlayerBuiltFixtureValid(const FLBCampaignTestFixture& Fixture)
{
    return Fixture.World && Fixture.Campaign && Fixture.BuildAuthority
        && Fixture.StillageFleet && Fixture.Management && !Fixture.Console
        && !Fixture.PR004 && !Fixture.PR005 && !Fixture.PR006 && !Fixture.PR007
        && !Fixture.PR008 && !Fixture.PR009 && !Fixture.PR010;
}

void DestroyCampaignFixture(FLBCampaignTestFixture& Fixture)
{
    if (!Fixture.World) return;
    Fixture.World->DestroyWorld(false);
    GEngine->DestroyWorldContext(Fixture.World);
    Fixture.World = nullptr;
}
}

bool FLBPressShopCampaignRoundTripTest::RunTest(const FString& Parameters)
{
    constexpr const TCHAR* Slot = TEXT("LB_AUTOMATION_WHOLE_PRESS_SHOP_V018");
    FLBCampaignTestFixture Source = CreateCampaignFixture(TEXT("LB_WholeShopCampaign_Source"));
    TestTrue(TEXT("Every source campaign authority spawns, including one stillage fleet"),
        Source.IsValid());
    if (!Source.IsValid())
    {
        DestroyCampaignFixture(Source);
        return false;
    }

    Source.Console->IncreaseQuantity();
    TestTrue(TEXT("Legacy source records one deterministic operating cost"),
        Source.Management->TryChargeOperatingCost(
            TEXT("LEGACY-CAMPAIGN-ENERGY-001"), TEXT("PRESS-SHOP"), 12500));
    TestTrue(TEXT("Legacy source earns deterministic research"),
        Source.Management->GrantResearchPoints(
            TEXT("LEGACY-CAMPAIGN-RP-001"), TEXT("PRESS-SHOP"), 7));
    Source.Train->SetActorLocation(FVector(2200.0f, 300.0f, 0.0f));
    int32 FleetFunds = Source.StillageFleet->GetAdditionalFLTPurchaseCost();
    TestTrue(TEXT("Source campaign buys one additional stillage FLT"),
        Source.StillageFleet->TryPurchaseAdditionalFLT(FleetFunds));
    TestEqual(TEXT("Purchase creates exactly two source FLTs"),
        Source.StillageFleet->GetFleetSize(), 2);

    FName ActiveJobA;
    FName ActiveJobB;
    FName PendingJob;
    TestTrue(TEXT("First exact full-stillage job queues"),
        Source.StillageFleet->EnqueueExactJob(TEXT("CAMPAIGN-STL-001"),
            ELBStillageFLTJobType::FullStillageToWeld,
            TEXT("PRESS-FULL-A"), TEXT("WELD-IN-A"),
            FVector(700.0f, -800.0f, 0.0f), FVector(1800.0f, -800.0f, 0.0f),
            FVector2D(85.0f, 155.0f), ActiveJobA));
    TestTrue(TEXT("Second purchased FLT claims a second exact job"),
        Source.StillageFleet->EnqueueExactJob(TEXT("CAMPAIGN-STL-002"),
            ELBStillageFLTJobType::FullStillageToWeld,
            TEXT("PRESS-FULL-A"), TEXT("WELD-IN-A"),
            FVector(700.0f, 800.0f, 0.0f), FVector(1800.0f, 800.0f, 0.0f),
            FVector2D(85.0f, 155.0f), ActiveJobB));
    TestTrue(TEXT("Third exact job remains pending at current fleet capacity"),
        Source.StillageFleet->EnqueueExactJob(TEXT("CAMPAIGN-STL-003"),
            ELBStillageFLTJobType::FullStillageToWeld,
            TEXT("PRESS-FULL-A"), TEXT("WELD-IN-A"),
            FVector(700.0f, 0.0f, 0.0f), FVector(1800.0f, 0.0f, 0.0f),
            FVector2D(85.0f, 155.0f), PendingJob));
    TestEqual(TEXT("Two exact jobs are active before capture"),
        Source.StillageFleet->GetActiveJobCount(), 2);
    TestEqual(TEXT("One exact job is pending before capture"),
        Source.StillageFleet->GetPendingJobCount(), 1);

    ULBPressShopSaveGame* Saved = NewObject<ULBPressShopSaveGame>();
    TestTrue(TEXT("One coordinator captures the complete core Press Shop"),
        Source.Campaign->CaptureCampaign(Saved));
    TestEqual(TEXT("Campaign root is format eighteen"), Saved->SaveFormatVersion, 18);
    TestEqual(TEXT("Authored shop capture has explicit legacy topology"),
        Saved->TopologyMode, ELBCampaignTopologyMode::LegacyAuthoredPressShop);
    TestEqual(TEXT("Campaign captures exact management cash"),
        Saved->FactoryManagement.CashBalancePence,
        ULBFactoryManagementSubsystem::DefaultStartingCashPence - 12500);
    TestEqual(TEXT("Campaign captures exact management research"),
        Saved->FactoryManagement.AvailableResearchPoints, static_cast<int64>(7));
    TestEqual(TEXT("Campaign captures one exact train authority"), Saved->PressTrains.Num(), 1);
    TestEqual(TEXT("Campaign captures starter plus one purchased stillage FLT"),
        Saved->StillageFLTFleet.Units.Num(), 2);
    TestEqual(TEXT("Campaign captures active and pending exact stillage jobs"),
        Saved->StillageFLTFleet.Jobs.Num(), 3);
    TArray<uint8> Bytes;
    TestTrue(TEXT("Whole-shop campaign serializes"), UGameplayStatics::SaveGameToMemory(Saved, Bytes));
    ULBPressShopSaveGame* Loaded = Cast<ULBPressShopSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes));
    TestNotNull(TEXT("Whole-shop campaign deserializes"), Loaded);
    DestroyCampaignFixture(Source);

    // A cold campaign world intentionally has no player-built press actor. The
    // identity subsystem must recreate the saved managed set transactionally.
    FLBCampaignTestFixture Fresh = CreateCampaignFixture(TEXT("LB_WholeShopCampaign_Fresh"), false);
    TestTrue(TEXT("Fresh restore world has every required campaign authority"), Fresh.IsValid(false));
    if (!Loaded || !Fresh.IsValid(false))
    {
        DestroyCampaignFixture(Fresh);
        return false;
    }

    Fresh.Console->IncreaseQuantity();
    const int32 QuantityBeforeRejectedLoad = Fresh.Console->CaptureSaveState().RequestedQuantity;
    const int64 CashBeforeRejectedLoad = Fresh.Management->GetCashBalancePence();
    ULBPressShopSaveGame* Invalid = DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    Invalid->PR006.StationId = TEXT("WRONG-STATION");
    TestFalse(TEXT("Preflight rejects a mismatched station identity"),
        Fresh.Campaign->RestoreCampaign(Invalid));
    TestEqual(TEXT("Rejected preflight changes no control-room authority"),
        Fresh.Console->CaptureSaveState().RequestedQuantity, QuantityBeforeRejectedLoad);

    ULBPressShopSaveGame* InvalidManagement = DuplicateObject<ULBPressShopSaveGame>(
        Loaded, GetTransientPackage());
    InvalidManagement->FactoryManagement.CashBalancePence += 1;
    TestFalse(TEXT("Preflight rejects unreconciled management cash before mutation"),
        Fresh.Campaign->RestoreCampaign(InvalidManagement));
    TestEqual(TEXT("Rejected management payload changes no management authority"),
        Fresh.Management->GetCashBalancePence(), CashBeforeRejectedLoad);
    TestEqual(TEXT("Rejected management payload changes no control-room authority"),
        Fresh.Console->CaptureSaveState().RequestedQuantity, QuantityBeforeRejectedLoad);

    ULBPressShopSaveGame* MissingFleet = DuplicateObject<ULBPressShopSaveGame>(
        Loaded, GetTransientPackage());
    MissingFleet->StillageFLTFleet = FLBStillageFLTFleetSaveState();
    TestFalse(TEXT("V18 preflight rejects a missing stillage-fleet payload"),
        Fresh.Campaign->RestoreCampaign(MissingFleet));
    TestEqual(TEXT("Rejected V18 payload leaves the fresh starter untouched"),
        Fresh.StillageFleet->GetFleetSize(), 1);

    ULBPressShopSaveGame* SmuggledLegacyFleet = DuplicateObject<ULBPressShopSaveGame>(
        Loaded, GetTransientPackage());
    SmuggledLegacyFleet->SaveFormatVersion = 15;
    SmuggledLegacyFleet->TopologyMode = ELBCampaignTopologyMode::LegacyAuthoredPressShop;
    SmuggledLegacyFleet->FactoryManagement = FLBFactoryManagementSaveState();
    TestFalse(TEXT("V15 preflight rejects non-default future stillage-fleet data"),
        Fresh.Campaign->RestoreCampaign(SmuggledLegacyFleet));
    TestEqual(TEXT("Rejected legacy payload leaves the fresh starter untouched"),
        Fresh.StillageFleet->GetFleetSize(), 1);

    ULBPressShopSaveGame* SmuggledLegacyManagement =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    SmuggledLegacyManagement->SaveFormatVersion = 15;
    SmuggledLegacyManagement->TopologyMode =
        ELBCampaignTopologyMode::LegacyAuthoredPressShop;
    SmuggledLegacyManagement->StillageFLTFleet = FLBStillageFLTFleetSaveState();
    TestFalse(TEXT("V15 preflight rejects a smuggled v17 management payload"),
        Fresh.Campaign->RestoreCampaign(SmuggledLegacyManagement));
    TestEqual(TEXT("Rejected legacy management smuggle leaves cash untouched"),
        Fresh.Management->GetCashBalancePence(), CashBeforeRejectedLoad);

    TestTrue(TEXT("Valid whole-shop campaign restores into a fresh world"),
        Fresh.Campaign->RestoreCampaign(Loaded));
    if (ULBPressTrainIdentitySubsystem* TrainIdentity =
        Fresh.World->GetSubsystem<ULBPressTrainIdentitySubsystem>())
    {
        Fresh.Train = TrainIdentity->FindTrainByPersistentGuid(
            Loaded->PressTrains[0].PersistentTrainGuid);
    }
    TestEqual(TEXT("Control-room planning state restores through the coordinator"),
        Fresh.Console->CaptureSaveState().RequestedQuantity, 100);
    TestTrue(TEXT("Train placement restores through the same coordinator"),
        Fresh.Train && Fresh.Train->GetActorTransform().Equals(
            Loaded->PressTrains[0].WorldTransform, 0.01f));
    TestEqual(TEXT("Fresh world restores the purchased second FLT"),
        Fresh.StillageFleet->GetFleetSize(), 2);
    TestEqual(TEXT("Fresh world restores both exact active claims"),
        Fresh.StillageFleet->GetActiveJobCount(), 2);
    TestEqual(TEXT("Fresh world restores the capacity-limited pending job"),
        Fresh.StillageFleet->GetPendingJobCount(), 1);
    TestEqual(TEXT("Fresh world restores exact saved management cash"),
        Fresh.Management->GetCashBalancePence(),
        ULBFactoryManagementSubsystem::DefaultStartingCashPence - 12500);
    TestEqual(TEXT("Fresh world restores exact saved research"),
        Fresh.Management->GetAvailableResearchPoints(), static_cast<int64>(7));
    FLBStillageFLTJob RestoredActive;
    FLBStillageFLTJob RestoredPending;
    TestTrue(TEXT("Exact active job identity survives the fresh-world round trip"),
        Fresh.StillageFleet->GetJobSnapshot(ActiveJobA, RestoredActive)
        && RestoredActive.StillageId == TEXT("CAMPAIGN-STL-001")
        && RestoredActive.State == ELBStillageFLTJobState::Claimed);
    TestTrue(TEXT("Exact pending job identity survives the fresh-world round trip"),
        Fresh.StillageFleet->GetJobSnapshot(PendingJob, RestoredPending)
        && RestoredPending.StillageId == TEXT("CAMPAIGN-STL-003")
        && RestoredPending.State == ELBStillageFLTJobState::Pending);

    Fresh.Campaign->CampaignSlotName = Slot;
    TestTrue(TEXT("Coordinator writes the complete campaign to disk"),
        Fresh.Campaign->SaveCampaignToSlot());
    Fresh.Console->IncreaseQuantity();
    TestTrue(TEXT("Coordinator reloads the complete campaign from disk"),
        Fresh.Campaign->LoadCampaignFromSlot());
    TestEqual(TEXT("Disk load restores control-room planning state"),
        Fresh.Console->CaptureSaveState().RequestedQuantity, 100);
    TestEqual(TEXT("Disk load retains purchased stillage-FLT capacity"),
        Fresh.StillageFleet->GetFleetSize(), 2);
    TestTrue(TEXT("Automation campaign slot is removed"), UGameplayStatics::DeleteGameInSlot(Slot, 0));

    for (const int32 LegacyVersion : {13, 14, 15})
    {
        ULBPressShopSaveGame* Legacy = DuplicateObject<ULBPressShopSaveGame>(
            Loaded, GetTransientPackage());
        Legacy->SaveFormatVersion = LegacyVersion;
        Legacy->TopologyMode = ELBCampaignTopologyMode::LegacyAuthoredPressShop;
        Legacy->FactoryManagement = FLBFactoryManagementSaveState();
        Legacy->StillageFLTFleet = FLBStillageFLTFleetSaveState();
        Legacy->PlayerProductionOrders.Version = 3;
        Legacy->PlayerProductionOrders.PendingBaseKitDeliveries.Reset();
        Legacy->PlayerProductionOrders.TransferredBaseKitDeliveries.Reset();
        TestTrue(*FString::Printf(TEXT("Legacy V%d campaign restores through explicit migration"),
            LegacyVersion), Fresh.Campaign->RestoreCampaign(Legacy));
        TestEqual(*FString::Printf(TEXT("Legacy V%d receives one fresh starter FLT"),
            LegacyVersion), Fresh.StillageFleet->GetFleetSize(), 1);
        TestEqual(*FString::Printf(TEXT("Legacy V%d cannot inherit future active jobs"),
            LegacyVersion), Fresh.StillageFleet->GetActiveJobCount(), 0);
        TestEqual(*FString::Printf(TEXT("Legacy V%d cannot inherit future pending jobs"),
            LegacyVersion), Fresh.StillageFleet->GetPendingJobCount(), 0);
        TestEqual(*FString::Printf(TEXT("Legacy V%d receives fresh management cash"),
            LegacyVersion), Fresh.Management->GetCashBalancePence(),
            ULBFactoryManagementSubsystem::DefaultStartingCashPence);
        TestEqual(*FString::Printf(TEXT("Legacy V%d cannot inherit v17 research"),
            LegacyVersion), Fresh.Management->GetAvailableResearchPoints(),
            static_cast<int64>(0));
    }

    ULBPressShopSaveGame* LegacyV16 = DuplicateObject<ULBPressShopSaveGame>(
        Loaded, GetTransientPackage());
    LegacyV16->SaveFormatVersion = 16;
    LegacyV16->TopologyMode = ELBCampaignTopologyMode::LegacyAuthoredPressShop;
    LegacyV16->FactoryManagement = FLBFactoryManagementSaveState();
    LegacyV16->PlayerProductionOrders.Version = 3;
    LegacyV16->PlayerProductionOrders.PendingBaseKitDeliveries.Reset();
    LegacyV16->PlayerProductionOrders.TransferredBaseKitDeliveries.Reset();
    TestTrue(TEXT("Legacy V16 restores its native stillage payload and migrates management"),
        Fresh.Campaign->RestoreCampaign(LegacyV16));
    TestEqual(TEXT("Legacy V16 retains purchased stillage capacity"),
        Fresh.StillageFleet->GetFleetSize(), 2);
    TestEqual(TEXT("Legacy V16 retains active stillage work"),
        Fresh.StillageFleet->GetActiveJobCount(), 2);
    TestEqual(TEXT("Legacy V16 receives fresh management cash"),
        Fresh.Management->GetCashBalancePence(),
        ULBFactoryManagementSubsystem::DefaultStartingCashPence);
    TestEqual(TEXT("Legacy V16 cannot inherit v17 research"),
        Fresh.Management->GetAvailableResearchPoints(), static_cast<int64>(0));

    DestroyCampaignFixture(Fresh);
    return true;
}

bool FLBPlayerBuiltCampaignRoundTripTest::RunTest(const FString& Parameters)
{
    FLBCampaignTestFixture Source = CreatePlayerBuiltCampaignFixture(
        TEXT("LB_PlayerBuiltCampaign_Source"));
    TestTrue(TEXT("Console-free player-built source needs no authored PR actors"),
        IsPlayerBuiltFixtureValid(Source));
    if (!IsPlayerBuiltFixtureValid(Source))
    {
        DestroyCampaignFixture(Source);
        return false;
    }

    ALBFactoryBuildMachine* Inspection =
        Source.World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Player-built source owns one dynamic inspection machine"),
        Inspection && Inspection->Configure(
            TEXT("PLAYER-INSPECTION-001"), ELBFactoryBuildMachineType::InspectionCell));
    if (Inspection)
    {
        Inspection->SetActorLocation(FVector(2400.0f, -900.0f, 0.0f));
    }
    ALBBodyWeldLineActor* BodyWeld = Source.World->SpawnActor<ALBBodyWeldLineActor>();
    TestTrue(TEXT("Player-built source owns one composite body-weld line"),
        BodyWeld && BodyWeld->Configure(TEXT("WELD-LINE-01")));
    if (BodyWeld)
    {
        BodyWeld->SetActorLocation(FVector(6000.0f, 3000.0f, 0.0f));
    }
    ALBECoatLineActor* ECoat = Source.World->SpawnActor<ALBECoatLineActor>();
    TestTrue(TEXT("Player-built source owns one complete ED / e-coat line"),
        ECoat && ECoat->Configure(TEXT("ED-LINE-01")));
    if (ECoat)
    {
        ECoat->SetActorLocation(FVector(-22000.0f, 10000.0f, 0.0f));
    }
    TestTrue(TEXT("Player-built source records an exact capital purchase"),
        Source.Management->TryPurchaseCapitalAsset(
            TEXT("PLAYER-CAPEX-INSPECTION-001"), TEXT("PLAYER-INSPECTION-001"), 400000));
    TestTrue(TEXT("Player-built source records earned research"),
        Source.Management->GrantResearchPoints(
            TEXT("PLAYER-RP-QUALITY-001"), TEXT("PLAYER-INSPECTION-001"), 11));

    ULBPressShopSaveGame* Saved = NewObject<ULBPressShopSaveGame>();
    TestTrue(TEXT("Console-free player-built campaign captures without PR-004..PR-010"),
        Source.Campaign->CaptureCampaign(Saved));
    TestEqual(TEXT("Player-built campaign is format eighteen"),
        Saved->SaveFormatVersion, 18);
    TestEqual(TEXT("Player-built campaign records explicit topology"),
        Saved->TopologyMode, ELBCampaignTopologyMode::PlayerBuiltFactory);
    TestEqual(TEXT("Player-built campaign captures one dynamic machine"),
        Saved->PlayerBuiltMachines.Num(), 1);
    TestEqual(TEXT("Player-built campaign captures one dedicated body-weld line"),
        Saved->PlayerBuiltBodyWeldLines.Num(), 1);
    TestEqual(TEXT("Player-built campaign captures one complete ED line"),
        Saved->PlayerBuiltECoatLines.Num(), 1);
    TestTrue(TEXT("Captured body-weld line preserves stable identity and transform"),
        Saved->PlayerBuiltBodyWeldLines.Num() == 1
        && Saved->PlayerBuiltBodyWeldLines[0].LineId == TEXT("WELD-LINE-01")
        && Saved->PlayerBuiltBodyWeldLines[0].WorldTransform.GetLocation().Equals(
            FVector(6000.0f, 3000.0f, 0.0f), 0.01f));
    TestEqual(TEXT("Player-built campaign captures exact post-purchase cash"),
        Saved->FactoryManagement.CashBalancePence,
        ULBFactoryManagementSubsystem::DefaultStartingCashPence - 400000);
    TestEqual(TEXT("Player-built campaign captures exact research"),
        Saved->FactoryManagement.AvailableResearchPoints, static_cast<int64>(11));

    TArray<uint8> Bytes;
    TestTrue(TEXT("Player-built v18 campaign serializes"),
        UGameplayStatics::SaveGameToMemory(Saved, Bytes));
    ULBPressShopSaveGame* Loaded = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromMemory(Bytes));
    TestNotNull(TEXT("Player-built v18 campaign deserializes"), Loaded);
    DestroyCampaignFixture(Source);

    FLBCampaignTestFixture Fresh = CreatePlayerBuiltCampaignFixture(
        TEXT("LB_PlayerBuiltCampaign_Fresh"));
    TestTrue(TEXT("Fresh console-free target needs no authored PR actors"),
        IsPlayerBuiltFixtureValid(Fresh));
    if (!Loaded || !IsPlayerBuiltFixtureValid(Fresh))
    {
        DestroyCampaignFixture(Fresh);
        return false;
    }

    const int64 CashBeforeRejectedLoad = Fresh.Management->GetCashBalancePence();
    ULBPressShopSaveGame* InvalidManagement =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    InvalidManagement->FactoryManagement.CashBalancePence -= 1;
    TestFalse(TEXT("Player-built preflight rejects invalid management before spawning assets"),
        Fresh.Campaign->RestoreCampaign(InvalidManagement));
    TestEqual(TEXT("Rejected player-built load leaves cash untouched"),
        Fresh.Management->GetCashBalancePence(), CashBeforeRejectedLoad);
    int32 MachineCountAfterRejectedLoad = 0;
    for (TActorIterator<ALBFactoryBuildMachine> It(Fresh.World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++MachineCountAfterRejectedLoad;
    }
    TestEqual(TEXT("Rejected player-built load spawns no machine"),
        MachineCountAfterRejectedLoad, 0);

    ULBPressShopSaveGame* DuplicateWeld =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    const FLBBodyWeldLineSaveState DuplicateWeldState =
        DuplicateWeld->PlayerBuiltBodyWeldLines[0];
    DuplicateWeld->PlayerBuiltBodyWeldLines.Add(DuplicateWeldState);
    TestFalse(TEXT("V18 preflight rejects duplicate body-weld identities before mutation"),
        Fresh.Campaign->RestoreCampaign(DuplicateWeld));
    TestEqual(TEXT("Duplicate body-weld rejection leaves no composite actor"),
        CountLiveActors<ALBBodyWeldLineActor>(Fresh.World), 0);

    ULBPressShopSaveGame* OverlappingWeld =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    OverlappingWeld->PlayerBuiltBodyWeldLines[0].WorldTransform =
        OverlappingWeld->PlayerBuiltMachines[0].WorldTransform;
    TestFalse(TEXT("V18 saved-layout preflight rejects weld over a generic machine"),
        Fresh.Campaign->RestoreCampaign(OverlappingWeld));
    TestEqual(TEXT("Saved-layout rejection leaves generic and weld actor sets untouched"),
        CountLiveActors<ALBFactoryBuildMachine>(Fresh.World)
            + CountLiveActors<ALBBodyWeldLineActor>(Fresh.World), 0);

    ULBPressShopSaveGame* WrongDirectionLink =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    FLBFactoryTransportLinkSaveState& Reversed =
        WrongDirectionLink->FactoryTransportLinks.AddDefaulted_GetRef();
    Reversed.SourcePortId = TEXT("PLAYER-INSPECTION-001-IN");
    Reversed.TargetPortId = TEXT("WELD-LINE-01-STILLAGE-IN");
    TestFalse(TEXT("V18 preflight rejects a saved input-to-input transport link"),
        Fresh.Campaign->RestoreCampaign(WrongDirectionLink));
    TestEqual(TEXT("Rejected link direction leaves link and endpoint actors untouched"),
        CountLiveActors<ALBFactoryTransportLink>(Fresh.World)
            + CountLiveActors<ALBFactoryBuildMachine>(Fresh.World)
            + CountLiveActors<ALBBodyWeldLineActor>(Fresh.World), 0);

    ULBPressShopSaveGame* UnownedEDBody =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    FLBECoatCarrierSaveState& ForeignCarrier =
        UnownedEDBody->PlayerBuiltECoatLines[0].Carriers.AddDefaulted_GetRef();
    ForeignCarrier.CarrierId = TEXT("ED-CARRIER-FOREIGN-001");
    ForeignCarrier.bEnabled = true;
    ForeignCarrier.bHasBodyInWhite = true;
    ForeignCarrier.BodyInWhite.BodyId = TEXT("BIW-FOREIGN-001");
    ForeignCarrier.BodyInWhite.VehicleModelId = TEXT("CAIRNWELL_2040");
    ForeignCarrier.BodyInWhite.OrderId = TEXT("ORDER-FOREIGN-001");
    ForeignCarrier.BodyInWhite.BaseKitId = TEXT("KIT-FOREIGN-001");
    ForeignCarrier.BodyInWhite.ReservationId = TEXT("RES-FOREIGN-001");
    ForeignCarrier.BodyInWhite.WeldLineId = TEXT("WELD-LINE-01");
    ForeignCarrier.BodyInWhite.bEDAccepted = true;
    ForeignCarrier.BodyInWhite.QualityState = ELBBodyWeldQualityState::Good;
    ForeignCarrier.BodyInWhite.CycleEvidence.CompletionSequence = 1;
    int32 ForeignPanelSerial = 1;
    for (const FName PanelFamily : ALBBodyWeldLineActor::GetRequiredPanelFamilies())
    {
        FLBBodyWeldPanelLineage& Panel =
            ForeignCarrier.BodyInWhite.Panels.AddDefaulted_GetRef();
        Panel.PanelTypeId = PanelFamily;
        Panel.PanelId = *FString::Printf(TEXT("PTA-PANEL-CAIRNWELL_2040-%s-%06d"),
            *PanelFamily.ToString(), ForeignPanelSerial++);
        Panel.StillageId = *FString::Printf(TEXT("STILLAGE-FOREIGN-%02d"),
            ForeignPanelSerial);
    }
    TestFalse(TEXT("V18 preflight rejects an ED BIW absent from weld completion ownership"),
        Fresh.Campaign->RestoreCampaign(UnownedEDBody));
    TestEqual(TEXT("Rejected ED ownership leaves weld and ED actor sets untouched"),
        CountLiveActors<ALBBodyWeldLineActor>(Fresh.World)
            + CountLiveActors<ALBECoatLineActor>(Fresh.World), 0);

    ULBPressShopSaveGame* OrphanFleetJob =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    FLBStillageFLTJob& OrphanJob =
        OrphanFleetJob->StillageFLTFleet.Jobs.AddDefaulted_GetRef();
    OrphanJob.JobId = TEXT("FLT-JOB-ORPHAN-000001");
    OrphanJob.StillageId = TEXT("STILLAGE-ORPHAN-001");
    OrphanJob.JobType = ELBStillageFLTJobType::FullStillageToWeld;
    OrphanJob.SourceAuthorityId = TEXT("PLAYER-INSPECTION-001");
    OrphanJob.TargetAuthorityId = TEXT("WELD-LINE-01");
    OrphanJob.TargetStackPadId = TEXT("WELD-PAD-ORPHAN-001");
    OrphanJob.PickupServicePoint = FVector(0.0f, 0.0f, 0.0f);
    OrphanJob.DropoffServicePoint = FVector(500.0f, 0.0f, 0.0f);
    OrphanJob.CreatedSequence = OrphanFleetJob->StillageFLTFleet.NextJobSequence++;
    TestFalse(TEXT("V18 preflight rejects a fleet job absent from flow authority"),
        Fresh.Campaign->RestoreCampaign(OrphanFleetJob));
    TestEqual(TEXT("Rejected fleet/flow mapping leaves the starter fleet unchanged"),
        Fresh.StillageFleet->GetFleetSize(), 1);
    TestEqual(TEXT("Rejected fleet/flow mapping queues no live job"),
        Fresh.StillageFleet->GetActiveJobCount(), 0);

    ULBPressShopSaveGame* InvalidBaseKitAdapter =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    FLBBodyWeldBaseKitDeliveryRecord& PendingKit =
        InvalidBaseKitAdapter->PlayerProductionOrders.PendingBaseKitDeliveries
            .AddDefaulted_GetRef();
    PendingKit.BaseKit.KitId = TEXT("BIW-BASE-KIT-PENDING-001");
    PendingKit.BaseKit.OrderId = TEXT("ORDER-PENDING-001");
    PendingKit.BaseKit.DeliverySequence =
        InvalidBaseKitAdapter->PlayerProductionOrders.NextBodyWeldDeliverySequence++;
    PendingKit.DeliveryAuthorityId = TEXT("PLAYER-INSPECTION-001");
    PendingKit.TargetWeldLineId = TEXT("WELD-LINE-01");
    TestFalse(TEXT("V18 preflight rejects a pending base kit without its adapter topology"),
        Fresh.Campaign->RestoreCampaign(InvalidBaseKitAdapter));
    TestEqual(TEXT("Rejected base-kit topology leaves machine, weld and link sets untouched"),
        CountLiveActors<ALBFactoryBuildMachine>(Fresh.World)
            + CountLiveActors<ALBBodyWeldLineActor>(Fresh.World)
            + CountLiveActors<ALBFactoryTransportLink>(Fresh.World), 0);

    // Inject a world-only obstruction which is intentionally invisible to the
    // pure saved-layout preflight. The incoming machine and brand have already
    // committed by the time body-weld placement rejects this ED envelope, so
    // this exercises the bounded full-root rollback rather than another early
    // malformed-payload rejection.
    ALBECoatLineActor* LateFailureBlocker =
        Fresh.World->SpawnActor<ALBECoatLineActor>();
    TestTrue(TEXT("Late-failure fixture owns one pre-existing ED obstruction"),
        LateFailureBlocker
            && LateFailureBlocker->Configure(TEXT("ED-ROLLBACK-BLOCKER-01")));
    if (LateFailureBlocker)
        LateFailureBlocker->SetActorLocation(FVector(6000.0f, 3000.0f, 0.0f));
    ULBFactoryBrandSubsystem* FreshBrand =
        Fresh.World->GetSubsystem<ULBFactoryBrandSubsystem>();
    const FLBFactoryBrandSaveState BrandBeforeLateFailure =
        FreshBrand ? FreshBrand->CaptureSaveState() : FLBFactoryBrandSaveState();
    const int64 CashBeforeLateFailure = Fresh.Management->GetCashBalancePence();
    const int64 ResearchBeforeLateFailure = Fresh.Management->GetAvailableResearchPoints();
    const int32 MachinesBeforeLateFailure =
        CountLiveActors<ALBFactoryBuildMachine>(Fresh.World);
    const int32 WeldBeforeLateFailure =
        CountLiveActors<ALBBodyWeldLineActor>(Fresh.World);
    const int32 EDBeforeLateFailure = CountLiveActors<ALBECoatLineActor>(Fresh.World);
    const int32 StorageBeforeLateFailure =
        CountLiveActors<ALBPressShopStorageZone>(Fresh.World);
    const int32 InfrastructureBeforeLateFailure =
        CountLiveActors<ALBFactoryAGVInfrastructure>(Fresh.World);
    const int32 LinksBeforeLateFailure =
        CountLiveActors<ALBFactoryTransportLink>(Fresh.World);
    const int32 FlowBeforeLateFailure =
        CountLiveActors<ALBPlayerBuiltPressFlowController>(Fresh.World);
    const int32 InboundBeforeLateFailure =
        CountLiveActors<ALBInboundDeliveryController>(Fresh.World)
        + CountLiveActors<ALBCoilAGVController>(Fresh.World);
    const int32 SupportBeforeLateFailure =
        CountLiveActors<ALBPressShopSupportFleetController>(Fresh.World);
    const int32 FLTActorsBeforeLateFailure =
        CountLiveActors<ALBCompactStillageFLT>(Fresh.World);
    ULBPressShopSaveGame* RootBeforeLateFailure =
        NewObject<ULBPressShopSaveGame>(GetTransientPackage());
    TestTrue(TEXT("Late-failure fixture captures the complete prior campaign root"),
        RootBeforeLateFailure
            && Fresh.Campaign->CaptureCampaign(RootBeforeLateFailure));
    ULBPressShopSaveGame* InjectedLateFailure =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    InjectedLateFailure->FactoryBrand.FactoryName = TEXT("ROLLBACK TARGET FACTORY");
    TestFalse(TEXT("A late body-weld placement rejection fails the campaign commit"),
        Fresh.Campaign->RestoreCampaign(InjectedLateFailure));
    const FLBFactoryBrandSaveState BrandAfterLateFailure =
        FreshBrand ? FreshBrand->CaptureSaveState() : FLBFactoryBrandSaveState();
    TestTrue(TEXT("Late failure restores the complete prior factory brand"),
        BrandAfterLateFailure.FactoryName == BrandBeforeLateFailure.FactoryName
        && BrandAfterLateFailure.PrimaryColour.Equals(
            BrandBeforeLateFailure.PrimaryColour, 0.0001f)
        && BrandAfterLateFailure.SecondaryColour.Equals(
            BrandBeforeLateFailure.SecondaryColour, 0.0001f)
        && BrandAfterLateFailure.bInitialSetupComplete
            == BrandBeforeLateFailure.bInitialSetupComplete
        && BrandAfterLateFailure.LogoAssetPath == BrandBeforeLateFailure.LogoAssetPath);
    TestEqual(TEXT("Late failure restores exact management cash"),
        Fresh.Management->GetCashBalancePence(), CashBeforeLateFailure);
    TestEqual(TEXT("Late failure restores exact management research"),
        Fresh.Management->GetAvailableResearchPoints(), ResearchBeforeLateFailure);
    TestEqual(TEXT("Late failure restores the generic-machine actor count"),
        CountLiveActors<ALBFactoryBuildMachine>(Fresh.World), MachinesBeforeLateFailure);
    TestEqual(TEXT("Late failure restores the weld actor count"),
        CountLiveActors<ALBBodyWeldLineActor>(Fresh.World), WeldBeforeLateFailure);
    TestEqual(TEXT("Late failure restores the ED actor count"),
        CountLiveActors<ALBECoatLineActor>(Fresh.World), EDBeforeLateFailure);
    TestEqual(TEXT("Late failure restores the storage actor count"),
        CountLiveActors<ALBPressShopStorageZone>(Fresh.World), StorageBeforeLateFailure);
    TestEqual(TEXT("Late failure restores the infrastructure actor count"),
        CountLiveActors<ALBFactoryAGVInfrastructure>(Fresh.World),
        InfrastructureBeforeLateFailure);
    TestEqual(TEXT("Late failure restores the transport-link actor count"),
        CountLiveActors<ALBFactoryTransportLink>(Fresh.World), LinksBeforeLateFailure);
    TestEqual(TEXT("Late failure preserves absence of a player flow controller"),
        CountLiveActors<ALBPlayerBuiltPressFlowController>(Fresh.World),
        FlowBeforeLateFailure);
    TestEqual(TEXT("Late failure restores inbound authority actor counts"),
        CountLiveActors<ALBInboundDeliveryController>(Fresh.World)
            + CountLiveActors<ALBCoilAGVController>(Fresh.World),
        InboundBeforeLateFailure);
    TestEqual(TEXT("Late failure restores support authority actor counts"),
        CountLiveActors<ALBPressShopSupportFleetController>(Fresh.World),
        SupportBeforeLateFailure);
    TestEqual(TEXT("Late failure restores stillage FLT actor count"),
        CountLiveActors<ALBCompactStillageFLT>(Fresh.World),
        FLTActorsBeforeLateFailure);
    TestEqual(TEXT("Late failure restores stillage fleet size"),
        Fresh.StillageFleet->GetFleetSize(), 1);
    TestEqual(TEXT("Late failure restores stillage fleet jobs"),
        Fresh.StillageFleet->GetActiveJobCount(), 0);
    ULBPressShopSaveGame* RootAfterLateFailure =
        NewObject<ULBPressShopSaveGame>(GetTransientPackage());
    TArray<uint8> RootBeforeBytes;
    TArray<uint8> RootAfterBytes;
    const bool bCapturedAfterLateFailure = RootAfterLateFailure
        && Fresh.Campaign->CaptureCampaign(RootAfterLateFailure);
    TestTrue(TEXT("Late failure leaves a capturable complete campaign root"),
        bCapturedAfterLateFailure);
    if (RootBeforeLateFailure && bCapturedAfterLateFailure)
    {
        RootBeforeLateFailure->SavedAtUtc = FDateTime();
        RootAfterLateFailure->SavedAtUtc = FDateTime();
        const bool bSerializedBefore = UGameplayStatics::SaveGameToMemory(
            RootBeforeLateFailure, RootBeforeBytes);
        const bool bSerializedAfter = UGameplayStatics::SaveGameToMemory(
            RootAfterLateFailure, RootAfterBytes);
        TestTrue(TEXT("Late failure serializes both campaign-root snapshots"),
            bSerializedBefore && bSerializedAfter);
        TestTrue(TEXT("Late failure restores every serialized campaign authority exactly"),
            bSerializedBefore && bSerializedAfter
                && RootBeforeBytes == RootAfterBytes);
    }
    if (LateFailureBlocker) LateFailureBlocker->Destroy();

    ULBPressShopSaveGame* SmuggledV17Weld =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    SmuggledV17Weld->SaveFormatVersion = 17;
    TestFalse(TEXT("V17 preflight rejects a smuggled future body-weld line"),
        Fresh.Campaign->RestoreCampaign(SmuggledV17Weld));
    TestEqual(TEXT("Rejected v17 weld smuggle leaves no body-weld actor"),
        CountLiveActors<ALBBodyWeldLineActor>(Fresh.World), 0);

    ULBPressShopSaveGame* MigratedV17 =
        DuplicateObject<ULBPressShopSaveGame>(Loaded, GetTransientPackage());
    MigratedV17->SaveFormatVersion = 17;
    MigratedV17->PlayerBuiltBodyWeldLines.Reset();
    MigratedV17->PlayerProductionOrders.Version = 3;
    MigratedV17->PlayerProductionOrders.PendingBaseKitDeliveries.Reset();
    MigratedV17->PlayerProductionOrders.TransferredBaseKitDeliveries.Reset();
    TestTrue(TEXT("A genuine v17 player-built save migrates with no invented weld line"),
        Fresh.Campaign->RestoreCampaign(MigratedV17));
    TestEqual(TEXT("V17 migration leaves the new body-weld set empty"),
        CountLiveActors<ALBBodyWeldLineActor>(Fresh.World), 0);

    TestTrue(TEXT("Valid player-built v18 restores into a genuinely fresh shell"),
        Fresh.Campaign->RestoreCampaign(Loaded));
    ALBFactoryBuildMachine* RestoredInspection = nullptr;
    int32 RestoredMachineCount = 0;
    for (TActorIterator<ALBFactoryBuildMachine> It(Fresh.World); It; ++It)
    {
        if (!IsValid(*It) || It->IsActorBeingDestroyed()) continue;
        ++RestoredMachineCount;
        if (It->GetMachineId() == TEXT("PLAYER-INSPECTION-001"))
        {
            RestoredInspection = *It;
        }
    }
    TestEqual(TEXT("Fresh player-built restore creates one exact machine"),
        RestoredMachineCount, 1);
    ALBBodyWeldLineActor* RestoredBodyWeld = nullptr;
    for (TActorIterator<ALBBodyWeldLineActor> It(Fresh.World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()
            && It->GetLineId() == TEXT("WELD-LINE-01"))
        {
            RestoredBodyWeld = *It;
        }
    }
    TestTrue(TEXT("Fresh player-built restore recreates the exact body-weld line"),
        RestoredBodyWeld && RestoredBodyWeld->GetActorLocation().Equals(
            FVector(6000.0f, 3000.0f, 0.0f), 0.01f));
    TestTrue(TEXT("Restored dynamic machine keeps identity, type and transform"),
        RestoredInspection
        && RestoredInspection->GetMachineType() == ELBFactoryBuildMachineType::InspectionCell
        && RestoredInspection->GetActorLocation().Equals(
            FVector(2400.0f, -900.0f, 0.0f), 0.01f));
    ALBECoatLineActor* RestoredECoat = nullptr;
    for (TActorIterator<ALBECoatLineActor> It(Fresh.World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()
            && It->GetLineId() == TEXT("ED-LINE-01"))
        {
            RestoredECoat = *It;
        }
    }
    TestTrue(TEXT("Fresh player-built restore recreates the exact ED line"),
        RestoredECoat && RestoredECoat->GetActorLocation().Equals(
            FVector(-22000.0f, 10000.0f, 0.0f), 0.01f));
    TestEqual(TEXT("Structural restore does not double-charge the saved capital purchase"),
        Fresh.Management->GetCashBalancePence(),
        ULBFactoryManagementSubsystem::DefaultStartingCashPence - 400000);
    TestEqual(TEXT("Player-built restore preserves exact research"),
        Fresh.Management->GetAvailableResearchPoints(), static_cast<int64>(11));
    TestEqual(TEXT("Player-built restore still has no operations console"),
        CountLiveActors<ALBControlRoomOperationsConsole>(Fresh.World), 0);

    DestroyCampaignFixture(Fresh);
    return true;
}

#endif
