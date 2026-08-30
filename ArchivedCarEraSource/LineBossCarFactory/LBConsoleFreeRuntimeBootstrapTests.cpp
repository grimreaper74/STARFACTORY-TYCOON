#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Engine/Engine.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBCoilAGVController.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryTransportLink.h"
#include "LBGameMode.h"
#include "LBInboundDeliveryController.h"
#include "LBPressShopSupportFleetController.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBStillageFLTFleetController.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressShopStorageZone.h"
#include "LBPressTrainAStation.h"
#include "LBSupportRobot.h"
#include "LBSupportRobotServiceDock.h"

namespace
{
template <typename TActorType>
int32 CountValidActors(UWorld* World)
{
    int32 Count = 0;
    if (!World) return Count;
    for (TActorIterator<TActorType> It(World); It; ++It)
        if (IsValid(*It)) ++Count;
    return Count;
}

template <typename TActorType>
TActorType* FindFirstValidActor(UWorld* World)
{
    if (!World) return nullptr;
    for (TActorIterator<TActorType> It(World); It; ++It)
        if (IsValid(*It)) return *It;
    return nullptr;
}

UWorld* CreateBootstrapWorld(const TCHAR* Name)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, FName(Name));
    if (!World) return nullptr;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    return World;
}

void DestroyBootstrapWorld(UWorld* World)
{
    if (!World) return;
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBConsoleFreeGameModeAuthoritiesTest,
    "LineBoss.FactoryBuilder.ConsoleFreeRuntime.GameModeAuthorities",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBConsoleFreeGameModeAuthoritiesTest::RunTest(const FString& Parameters)
{
    UWorld* CleanWorld = CreateBootstrapWorld(TEXT("LB_ConsoleFree_GameModeAuthorities"));
    TestNotNull(TEXT("Clean transient world exists"), CleanWorld);
    if (!CleanWorld) return false;

    CleanWorld->SpawnActor<ALBInboundDeliveryController>();
    CleanWorld->SpawnActor<ALBInboundDeliveryController>();
    ALBGameMode* CleanMode = CleanWorld->SpawnActor<ALBGameMode>();
    TestNotNull(TEXT("Clean factory GameMode spawns"), CleanMode);
    if (CleanMode) CleanMode->DispatchBeginPlay();

    TestEqual(TEXT("Clean GameMode deduplicates to exactly one inbound authority"),
        CountValidActors<ALBInboundDeliveryController>(CleanWorld), 1);
    TestEqual(TEXT("Clean GameMode ensures exactly one player flow authority"),
        CountValidActors<ALBPlayerBuiltPressFlowController>(CleanWorld), 1);
    TestEqual(TEXT("Clean GameMode installs exactly one stillage-FLT fleet authority"),
        CountValidActors<ALBStillageFLTFleetController>(CleanWorld), 1);
    ALBStillageFLTFleetController* StillageFleet =
        FindFirstValidActor<ALBStillageFLTFleetController>(CleanWorld);
    TestTrue(TEXT("A new factory receives exactly one starter compact stillage FLT"),
        StillageFleet && StillageFleet->GetFleetSize() == 1);
    TestEqual(TEXT("Clean GameMode ensures exactly one coil AGV authority"),
        CountValidActors<ALBCoilAGVController>(CleanWorld), 1);
    TestEqual(TEXT("Clean GameMode ensures exactly one build authority"),
        CountValidActors<ALBPressShopBuildAuthority>(CleanWorld), 1);
    TestEqual(TEXT("Clean GameMode installs exactly the retained four-unit support fleet"),
        CountValidActors<ALBSupportRobot>(CleanWorld), 4);
    TestEqual(TEXT("Clean GameMode installs four independent service docks"),
        CountValidActors<ALBSupportRobotServiceDock>(CleanWorld), 4);
    TestEqual(TEXT("Clean GameMode installs one support-fleet authority"),
        CountValidActors<ALBPressShopSupportFleetController>(CleanWorld), 1);
    TSet<FName> SupportUnitIds;
    for (TActorIterator<ALBSupportRobot> It(CleanWorld); It; ++It)
        if (IsValid(*It)) SupportUnitIds.Add(It->CaptureCommonSaveState().UnitId);
    TestTrue(TEXT("Starter support fleet has exact CR01/MR01 identities"),
        SupportUnitIds.Num() == 4 && SupportUnitIds.Contains(TEXT("LB-CR01-01"))
        && SupportUnitIds.Contains(TEXT("LB-CR01-02"))
        && SupportUnitIds.Contains(TEXT("LB-MR01-01"))
        && SupportUnitIds.Contains(TEXT("LB-MR01-02")));
    ALBPressShopSupportFleetController* SupportFleet =
        FindFirstValidActor<ALBPressShopSupportFleetController>(CleanWorld);
    TestTrue(TEXT("Support fleet derives routes from clean installed positions"),
        SupportFleet && SupportFleet->bUseInstalledActorTransforms);
    const TMap<FName, FVector> ExpectedRobotLocations = {
        {TEXT("LB-CR01-01"), FVector(-750.0f, -4050.0f, 56.0f)},
        {TEXT("LB-CR01-02"), FVector(-250.0f, -4050.0f, 56.0f)},
        {TEXT("LB-MR01-01"), FVector(250.0f, -4050.0f, 62.5f)},
        {TEXT("LB-MR01-02"), FVector(750.0f, -4050.0f, 62.5f)}};
    for (TActorIterator<ALBSupportRobot> It(CleanWorld); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FLBSupportRobotSaveState State = It->CaptureCommonSaveState();
        const FVector* Expected = ExpectedRobotLocations.Find(State.UnitId);
        TestTrue(*FString::Printf(TEXT("%s retains its accepted clean service-bank berth"), *State.UnitId.ToString()),
            Expected && It->GetActorLocation().Equals(*Expected, 0.01f));
    }
    const TMap<FName, FVector> ExpectedDockLocations = {
        {TEXT("LB-DOCK-CR01-01"), FVector(-750.0f, -4380.0f, 0.0f)},
        {TEXT("LB-DOCK-CR01-02"), FVector(-250.0f, -4380.0f, 0.0f)},
        {TEXT("LB-DOCK-MR01-01"), FVector(250.0f, -4380.0f, 0.0f)},
        {TEXT("LB-DOCK-MR01-02"), FVector(750.0f, -4380.0f, 0.0f)}};
    for (TActorIterator<ALBSupportRobotServiceDock> It(CleanWorld); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FVector* Expected = ExpectedDockLocations.Find(It->GetDockId());
        TestTrue(*FString::Printf(TEXT("%s retains its accepted independent dock position"), *It->GetDockId().ToString()),
            Expected && It->GetActorLocation().Equals(*Expected, 0.01f)
            && FMath::IsNearlyEqual(It->GetActorRotation().Yaw, 90.0f, 0.01f));
    }
    TestTrue(TEXT("Clean support fleet commissions against installed berths and independent docks"),
        SupportFleet && SupportFleet->InitialiseInstalledFleet() && SupportFleet->IsFleetReady());
    for (const TPair<FName, FVector>& Expected : ExpectedRobotLocations)
    {
        FLBSupportRobotSaveState State;
        TestTrue(*FString::Printf(TEXT("%s has a commissioned runtime snapshot"), *Expected.Key.ToString()),
            SupportFleet && SupportFleet->GetUnitSnapshot(Expected.Key, State));
        TestTrue(*FString::Printf(TEXT("%s is certified at its own dock"), *Expected.Key.ToString()),
            State.bCertified && State.bDocked
            && State.DockId == FName(*FString::Printf(TEXT("LB-DOCK-%s"), *Expected.Key.ToString().RightChop(3))));
    }
    ALBInboundDeliveryController* CleanInbound =
        FindFirstValidActor<ALBInboundDeliveryController>(CleanWorld);
    ALBPlayerBuiltPressFlowController* CleanFlow =
        FindFirstValidActor<ALBPlayerBuiltPressFlowController>(CleanWorld);
    TestTrue(TEXT("Clean inbound late bootstrap is explicitly enabled"),
        CleanInbound && CleanInbound->IsPlayerBuilderBootstrapEnabled());
    TestTrue(TEXT("Clean local train autostart is explicitly enabled"),
        CleanFlow && CleanFlow->IsConsoleFreeTrainAutostartEnabled());
    DestroyBootstrapWorld(CleanWorld);

    UWorld* LegacyWorld = CreateBootstrapWorld(TEXT("LB_LegacyConsole_GameModeAuthorities"));
    TestNotNull(TEXT("Legacy transient world exists"), LegacyWorld);
    if (!LegacyWorld) return false;
    TestNotNull(TEXT("Legacy operations console fixture exists"),
        LegacyWorld->SpawnActor<ALBControlRoomOperationsConsole>());
    ALBGameMode* LegacyMode = LegacyWorld->SpawnActor<ALBGameMode>();
    TestNotNull(TEXT("Legacy factory GameMode spawns"), LegacyMode);
    if (LegacyMode) LegacyMode->DispatchBeginPlay();

    TestEqual(TEXT("Legacy console map does not gain a clean inbound authority"),
        CountValidActors<ALBInboundDeliveryController>(LegacyWorld), 0);
    TestEqual(TEXT("Legacy console map does not gain a clean starter support fleet"),
        CountValidActors<ALBSupportRobot>(LegacyWorld), 0);
    ALBPlayerBuiltPressFlowController* LegacyFlow =
        FindFirstValidActor<ALBPlayerBuiltPressFlowController>(LegacyWorld);
    TestFalse(TEXT("Legacy console remains the train-start authority"),
        LegacyFlow && LegacyFlow->IsConsoleFreeTrainAutostartEnabled());
    DestroyBootstrapWorld(LegacyWorld);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBConsoleFreeLateBoundInboundTest,
    "LineBoss.FactoryBuilder.ConsoleFreeRuntime.LateBoundInboundToLateStorage",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBConsoleFreeLateBoundInboundTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_ConsoleFree_LateInbound"));
    TestNotNull(TEXT("Late-bound inbound world exists"), World);
    if (!World) return false;

    auto SpawnTagged = [World](const FVector& Location, const FName Tag)
    {
        AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(
            AStaticMeshActor::StaticClass(), Location, FRotator::ZeroRotator);
        if (Actor)
        {
            Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
            Actor->Tags.Add(Tag);
        }
        return Actor;
    };
    SpawnTagged(FVector(0, 0, 29), TEXT("LB.Vehicle.CoilAGV"));
    SpawnTagged(FVector(0, 0, 64), TEXT("LB.Vehicle.CoilAGV.LiftDeck"));
    SpawnTagged(FVector(0, 0, 156), TEXT("LB.Inventory.InTransfer"));

    ALBCoilAGVController* AGV = World->SpawnActor<ALBCoilAGVController>();
    ALBInboundDeliveryController* Delivery = World->SpawnActor<ALBInboundDeliveryController>();
    TestTrue(TEXT("Retained AGV presentation binds before player machines exist"),
        AGV && AGV->DiscoverAndBind());
    TestNotNull(TEXT("Inbound authority exists before player machines"), Delivery);
    if (!AGV || !Delivery)
    {
        World->DestroyWorld(false);
        return false;
    }
    Delivery->SetPlayerBuilderBootstrapEnabled(true);
    Delivery->Tick(0.6f);
    TestFalse(TEXT("No endpoints leaves inbound safely idle"),
        Delivery->IsPlayerBuilderBootstrapBound());

    ALBFactoryBuildMachine* Inbound = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(0, 0, 0)));
    TestTrue(TEXT("Player places only the inbound dock"), Inbound
        && Inbound->Configure(TEXT("INBOUND-PLAYER-001"),
            ELBFactoryBuildMachineType::InboundDeliveryDock));
    for (int32 Step = 0; Step < 2000
        && Delivery->GetPhase() != ELBInboundDeliveryPhase::WaitingForStorage; ++Step)
    {
        AGV->Tick(0.05f);
        Delivery->Tick(0.05f);
    }
    TestEqual(TEXT("The unloading dock immediately removes and holds the first coil"),
        Delivery->GetPhase(), ELBInboundDeliveryPhase::WaitingForStorage);
    TestEqual(TEXT("The held coil is not silently counted as delivered"),
        Delivery->GetCompletedDeliveries(), 0);

    ALBPlayerBuiltPressFlowController* Flow =
        World->SpawnActor<ALBPlayerBuiltPressFlowController>();
    ALBPressShopStorageZone* CoilStorage =
        World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FTransform(FVector(900, 1500, 0)));
    TestTrue(TEXT("Player places wrapped-coil storage while the first coil is held"),
        Flow && CoilStorage
        && CoilStorage->Configure(TEXT("SZ-COIL-LATE-001"),
            ELBPressShopStorageType::BareCoils, 4, FVector(300)));
    Delivery->Tick(0.6f);
    TestEqual(TEXT("Storage alone does not invent a missing inspection destination"),
        Delivery->GetPhase(), ELBInboundDeliveryPhase::WaitingForStorage);

    ALBFactoryBuildMachine* PR002 = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(900, 900, 0)));
    TestTrue(TEXT("Player then places PR002"), PR002
        && PR002->Configure(TEXT("PR002-PLAYER-001"),
            ELBFactoryBuildMachineType::CoilWeighInspectionCell)
        && PR002->ConfigureGameplayBuffers(2, 2));

    ULBFactoryConnectionSubsystem* Connections =
        NewObject<ULBFactoryConnectionSubsystem>(World);
    ALBFactoryTransportLink* InboundLink = nullptr;
    FString Reason;
    TestTrue(TEXT("Player-built inbound has one real dock-to-PR002 link"),
        Connections && Connections->Connect(
            Inbound->OutputPort, PR002->InputPort, InboundLink, Reason));
    Delivery->Tick(0.6f);
    TestEqual(TEXT("Incomplete AGV infrastructure keeps the physical coil safely held"),
        Delivery->GetPhase(), ELBInboundDeliveryPhase::WaitingForStorage);

    auto SpawnInfrastructure = [World](const FName Id,
        const ELBFactoryAGVInfrastructureType Type, const FVector& Location,
        const FRotator& Rotation = FRotator::ZeroRotator)
    {
        ALBFactoryAGVInfrastructure* Infrastructure =
            World->SpawnActor<ALBFactoryAGVInfrastructure>(
                ALBFactoryAGVInfrastructure::StaticClass(), FTransform(Rotation, Location));
        return Infrastructure && Infrastructure->Configure(Id, Type)
            ? Infrastructure : nullptr;
    };
    TestTrue(TEXT("Player places inbound wait and turn points"),
        SpawnInfrastructure(TEXT("AGV-WAIT-INBOUND"), ELBFactoryAGVInfrastructureType::WaitPoint,
            FVector(100, 0, 0))
        && SpawnInfrastructure(TEXT("AGV-WAYPOINT-PR002"), ELBFactoryAGVInfrastructureType::RouteWaypoint,
            FVector(900, 0, 0)));
    TestTrue(TEXT("Distant route tiles cannot authorize the inbound AGV"),
        SpawnInfrastructure(TEXT("AGV-ROUTE-DISCONNECTED-01"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(4000, 4000, 0))
        && SpawnInfrastructure(TEXT("AGV-ROUTE-DISCONNECTED-02"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(4500, 4000, 0)));
    Delivery->Tick(0.6f);
    TestFalse(TEXT("Disconnected route leaves inbound bootstrap safely unbound"),
        Delivery->IsPlayerBuilderBootstrapBound());
    TestEqual(TEXT("Disconnected route leaves the inbound coil held"),
        Delivery->GetPhase(), ELBInboundDeliveryPhase::WaitingForStorage);

    TestTrue(TEXT("Player places a continuously covered inbound AGV route"),
        SpawnInfrastructure(TEXT("AGV-ROUTE-INBOUND-01"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(350, 0, 0))
        && SpawnInfrastructure(TEXT("AGV-ROUTE-INBOUND-02"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(750, 0, 0))
        && SpawnInfrastructure(TEXT("AGV-ROUTE-INBOUND-03"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(900, 400, 0), FRotator(0, 90, 0)));

    Delivery->Tick(0.6f);
    TestTrue(TEXT("Late endpoints and route bind without restarting the world"),
        Delivery->IsPlayerBuilderBootstrapBound());
    TestTrue(TEXT("The already-held coil dispatches when the missing route becomes valid"),
        Delivery->GetPhase() == ELBInboundDeliveryPhase::AGVDispatch
        || Delivery->GetPhase() == ELBInboundDeliveryPhase::AGVHandoff);
    const FVector ExpectedDock = PR002->InputPort->GetComponentLocation();
    const FVector ConfiguredDock = AGV->GetConfiguredDockPoint();
    TestTrue(TEXT("AGV route terminates at the live PR002 input endpoint"),
        FVector2D(ConfiguredDock).Equals(FVector2D(ExpectedDock), 1.0f));

    for (int32 Step = 0; Step < 5000
        && (Delivery->GetCompletedDeliveries() < 1
            || Delivery->GetPhase() != ELBInboundDeliveryPhase::Idle); ++Step)
    {
        AGV->Tick(0.05f);
        Delivery->Tick(0.05f);
    }
    Delivery->SetPlayerBuilderBootstrapEnabled(false);
    TestEqual(TEXT("Exactly one deterministic inbound delivery completes"),
        Delivery->GetCompletedDeliveries(), 1);
    TestEqual(TEXT("Inbound authority returns idle after the AGV returns"),
        Delivery->GetPhase(), ELBInboundDeliveryPhase::Idle);
    TestEqual(TEXT("Exactly one physical inbound link transfer is recorded"),
        InboundLink ? InboundLink->GetTransferredUnits() : 0, 1);
    TestEqual(TEXT("One wrapped coil visibly leaves the four-coil lorry"),
        Inbound->GetVisibleTrailerCoilCount(), 3);
    const FLBFactoryBuildMachineSaveState PR002State = PR002->CaptureSaveState();
    TestEqual(TEXT("PR002 receives exactly one deterministic identity"),
        PR002State.InputUnitIds.Num(), 1);
    if (PR002State.InputUnitIds.Num() == 1)
    {
        TestEqual(TEXT("PR002 receives the deterministic exact identity"),
            PR002State.InputUnitIds[0], FName(TEXT("COIL-INBOUND-000001")));
    }

    ALBFactoryTransportLink* StorageLink = nullptr;
    TestTrue(TEXT("Late-placed storage connects to the existing PR002 output"),
        Connections && Connections->Connect(
            PR002->OutputPort, CoilStorage->IngressPoint, StorageLink, Reason));
    if (Flow) Flow->SetAutomaticFlowEnabled(false);
    FString Summary;
    for (int32 Step = 0; Flow && Step < 20 && CoilStorage->GetOccupancy() == 0; ++Step)
        Flow->ExecuteAutomaticStep(Summary);
    TestEqual(TEXT("Late storage receives the already-delivered coil without rebind"),
        CoilStorage ? CoilStorage->GetOccupancy() : 0, 1);
    TestTrue(TEXT("Late storage preserves the deterministic inbound identity"),
        CoilStorage && CoilStorage->CaptureSaveState().StoredUnitIds
            == TArray<FName>({TEXT("COIL-INBOUND-000001")}));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBConsoleFreeTrainAutostartSafetyTest,
    "LineBoss.FactoryBuilder.ConsoleFreeRuntime.TrainAutostartSafety",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBConsoleFreeTrainAutostartSafetyTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_ConsoleFree_TrainAutostart"));
    ULBFactoryConnectionSubsystem* Connections =
        World ? NewObject<ULBFactoryConnectionSubsystem>(World) : nullptr;
    ALBPlayerBuiltPressFlowController* Flow =
        World ? World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    TestNotNull(TEXT("Console-free train flow authority exists"), Flow);
    if (!World || !Connections || !Flow)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    Flow->SetAutomaticFlowEnabled(false);
    Flow->SetConsoleFreeTrainAutostartEnabled(true);

    auto SpawnBlankStore = [World](const FName Id, const FVector& Location)
    {
        ALBPressShopStorageZone* Store = World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FTransform(Location));
        return Store && Store->Configure(Id, ELBPressShopStorageType::PreparedBlanks,
            4, FVector(300)) ? Store : nullptr;
    };
    ALBPressShopStorageZone* SafeStore =
        SpawnBlankStore(TEXT("SZ-BLANK-SAFE"), FVector(0, 0, 0));
    ALBPressShopStorageZone* GuardOpenStore =
        SpawnBlankStore(TEXT("SZ-BLANK-GUARD"), FVector(1000, 0, 0));
    ALBPressShopStorageZone* RestartStore =
        SpawnBlankStore(TEXT("SZ-BLANK-RESTART"), FVector(2000, 0, 0));
    ALBPressTrainAStation* SafeTrain = World->SpawnActor<ALBPressTrainAStation>(
        ALBPressTrainAStation::StaticClass(), FTransform(FVector(0, 500, 0)));
    ALBPressTrainAStation* GuardOpenTrain = World->SpawnActor<ALBPressTrainAStation>(
        ALBPressTrainAStation::StaticClass(), FTransform(FVector(1000, 500, 0)));
    ALBPressTrainAStation* RestartTrain = World->SpawnActor<ALBPressTrainAStation>(
        ALBPressTrainAStation::StaticClass(), FTransform(FVector(2000, 500, 0)));
    TestTrue(TEXT("Three isolated player trains configure"),
        SafeTrain && GuardOpenTrain && RestartTrain
        && GuardOpenTrain->ConfigureTrainVariant(TEXT("TRAIN_B"), TEXT("TRAIN B"),
            TEXT("TEST GUARD"), FLinearColor::Blue)
        && RestartTrain->ConfigureTrainVariant(TEXT("TRAIN_C"), TEXT("TRAIN C"),
            TEXT("TEST RESTART"), FLinearColor::Red));
    if (!SafeStore || !GuardOpenStore || !RestartStore
        || !SafeTrain || !GuardOpenTrain || !RestartTrain)
    {
        World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("Every autostart fixture has an approved stamped-panel recipe and installed die"),
        SafeTrain->SetActiveProductionRecipe(
            TEXT("CAIRNWELL_2040"), TEXT("DOOR_FRONT_LEFT"), TEXT("DIE_DOOR_FRONT_LEFT_2040"))
        && GuardOpenTrain->SetActiveProductionRecipe(
            TEXT("CAIRNWELL_2040"), TEXT("DOOR_FRONT_LEFT"), TEXT("DIE_DOOR_FRONT_LEFT_2040"))
        && RestartTrain->SetActiveProductionRecipe(
            TEXT("CAIRNWELL_2040"), TEXT("DOOR_FRONT_LEFT"), TEXT("DIE_DOOR_FRONT_LEFT_2040")));

    GuardOpenTrain->SetAccessInterlocksClosed(false);
    FLBPressTrainASaveState RestartState = RestartTrain->CaptureSaveState();
    RestartState.bRestartRequiredAfterLoad = true;
    TestTrue(TEXT("Valid restored train fixture requires explicit restart"),
        RestartTrain->RestoreSaveState(RestartState));
    TestTrue(TEXT("Three exact prepared blanks enter player buffers"),
        SafeStore->TryStoreIdentifiedUnit(TEXT("BLANK-SAFE-001"))
        && GuardOpenStore->TryStoreIdentifiedUnit(TEXT("BLANK-GUARD-001"))
        && RestartStore->TryStoreIdentifiedUnit(TEXT("BLANK-RESTART-001")));

    auto ConnectTrain = [Connections](ALBPressShopStorageZone* Store,
        ALBPressTrainAStation* Train)
    {
        ALBFactoryTransportLink* Link = nullptr;
        FString Reason;
        return Connections->Connect(Store->EgressPoint, Train->FactoryInputPort,
            Link, Reason) && Link;
    };
    TestTrue(TEXT("Every player train has a real blank-buffer link"),
        ConnectTrain(SafeStore, SafeTrain)
        && ConnectTrain(GuardOpenStore, GuardOpenTrain)
        && ConnectTrain(RestartStore, RestartTrain));

    FString Summary;
    Flow->ExecuteAutomaticStep(Summary);
    const FLBPressTrainAHMIStatus SafeStatus = SafeTrain->GetHMIStatus();
    const FLBPressTrainAHMIStatus GuardStatus = GuardOpenTrain->GetHMIStatus();
    const FLBPressTrainAHMIStatus RestartStatus = RestartTrain->GetHMIStatus();
    TestEqual(TEXT("Healthy player train locally powers and starts after blank queue"),
        SafeStatus.State, ELBPressTrainAState::Cycling);
    TestTrue(TEXT("Healthy player train control power is on"), SafeStatus.bControlPowerOn);
    TestFalse(TEXT("Guard-open train remains isolated"),
        GuardStatus.bControlPowerOn);
    TestEqual(TEXT("Guard-open blank remains safely queued"),
        GuardStatus.PendingBlankCount, 1);
    TestFalse(TEXT("Autostart never closes or bypasses the open guard"),
        GuardStatus.bAccessInterlocksClosed);
    TestFalse(TEXT("Restart-required train remains isolated"),
        RestartStatus.bControlPowerOn);
    TestTrue(TEXT("Autostart never clears restart-required state"),
        RestartStatus.bRestartRequiredAfterLoad);
    TestEqual(TEXT("Restart-required blank remains safely queued"),
        RestartStatus.PendingBlankCount, 1);

    SafeTrain->Tick(6.1f);
    TestEqual(TEXT("Locally started healthy train completes a real panel"),
        SafeTrain->GetHMIStatus().PendingPanelCount, 1);

    World->DestroyWorld(false);
    return true;
}

#endif
