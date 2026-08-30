#include "LBFactoryMachineBuilderSubsystem.h"

#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "LBBodyWeldLineActor.h"
#include "LBCoilAGVController.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBFactoryTransportLink.h"
#include "LBPressTrainAStation.h"
#include "LBPressShopStorageZone.h"
#include "LBPressShopBuildAuthority.h"
#include "Misc/AutomationTest.h"
#include "Materials/MaterialInterface.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
struct FFactoryBuilderAutomationWorld
{
    explicit FFactoryBuilderAutomationWorld(const FName WorldName)
    {
        if (!GEngine) return;
        World = UWorld::CreateWorld(EWorldType::Game, false, WorldName);
        if (!World) return;
        FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);

        BuildAuthority = World->SpawnActor<ALBPressShopBuildAuthority>();
        if (!BuildAuthority) return;
        FLBPressShopBuildBay Bay;
        Bay.BayId = TEXT("FACTORY-BUILDER-AUTOMATION-FLOOR");
        Bay.Centre = FVector::ZeroVector;
        Bay.HalfExtent = FVector(25000.0f, 25000.0f, 2000.0f);
        BuildAuthority->BuildBays.Add(Bay);
    }

    ~FFactoryBuilderAutomationWorld()
    {
        if (!World) return;
        World->DestroyWorld(false);
        if (GEngine) GEngine->DestroyWorldContext(World);
    }

    UWorld* World = nullptr;
    ALBPressShopBuildAuthority* BuildAuthority = nullptr;
};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryAutomaticInboundAGVRouteTest,
    "LineBoss.FactoryBuilder.AGVInfrastructure.AutomaticInboundRoute",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryDemoAlignedInboundAGVRouteTest,
    "LineBoss.FactoryBuilder.AGVInfrastructure.DemoAlignedInboundRoute",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryMixedAGVRouteProfileRebindTest,
    "LineBoss.FactoryBuilder.AGVInfrastructure.MixedRouteProfileRebind",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryAutomaticInboundRouteProfileOwnershipTest,
    "LineBoss.FactoryBuilder.AGVInfrastructure.AutomaticInboundRouteProfileOwnership",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryECoatPlacementContractTest,
    "LineBoss.FactoryBuilder.ECoat.Authoritative189MetrePlacementContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryBodyWeldPlacementContractTest,
    "LineBoss.FactoryBuilder.BodyWeld.DedicatedPlacementPersistenceAndConnectionContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBCoilPreparationImportedCompositeAssetContractTest,
    "LineBoss.FactoryBuilder.Machines.CoilPreparationImportedCompositeAssetContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBCoilPreparationCookManifestContractTest,
    "LineBoss.FactoryBuilder.Machines.CoilPreparationCookManifestContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBCoilPreparationImportedCompositeAssetContractTest::RunTest(const FString& Parameters)
{
    const ALBFactoryBuildMachine* Defaults = GetDefault<ALBFactoryBuildMachine>();
    TestNotNull(TEXT("Factory-machine native defaults exist"), Defaults);
    if (!Defaults) return false;

    const TArray<TSoftObjectPtr<UStaticMesh>>& References =
        Defaults->GetCoilPreparationVisualAssetReferences();
    TestEqual(TEXT("Compact PR005-PR010 composite declares every intended visual entry"),
        References.Num(), 75);

    struct FExpectedRootCount
    {
        const TCHAR* Root;
        int32 Count;
    };
    const FExpectedRootCount ExpectedRoots[] =
    {
        {TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/"), 10},
        {TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001/"), 12},
        {TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001/"), 12},
        {TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001/"), 16},
        {TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/Static/"), 10},
        {TEXT("/Game/LineBoss/Candidates/PressShop/PR010/"), 15}
    };
    TArray<int32> RootCounts;
    RootCounts.Init(0, UE_ARRAY_COUNT(ExpectedRoots));
    bool bEveryReferenceResolved = true;
    bool bEveryReferenceHasAuthorizedRoot = true;
    bool bContainsUnsafeOrValidationOnlyAsset = false;
    for (const TSoftObjectPtr<UStaticMesh>& Reference : References)
    {
        const FString Path = Reference.ToSoftObjectPath().ToString();
        bool bFoundRoot = false;
        for (int32 RootIndex = 0; RootIndex < UE_ARRAY_COUNT(ExpectedRoots); ++RootIndex)
        {
            if (Path.StartsWith(ExpectedRoots[RootIndex].Root))
            {
                ++RootCounts[RootIndex];
                bFoundRoot = true;
                break;
            }
        }
        bEveryReferenceHasAuthorizedRoot &= bFoundRoot;
        bEveryReferenceResolved &= Reference.LoadSynchronous() != nullptr;
        bContainsUnsafeOrValidationOnlyAsset |= Path.Contains(TEXT("ReleaseDetail"))
            || Path.Contains(TEXT("ProEnvelope"));
    }
    TestTrue(TEXT("Every declared preparation mesh resolves from Content"),
        bEveryReferenceResolved);
    TestTrue(TEXT("Every preparation mesh stays in its audited station root"),
        bEveryReferenceHasAuthorizedRoot);
    TestFalse(TEXT("Validation overlays and raw high-poly imports are not runtime-bound"),
        bContainsUnsafeOrValidationOnlyAsset);
    for (int32 RootIndex = 0; RootIndex < UE_ARRAY_COUNT(ExpectedRoots); ++RootIndex)
    {
        const FString AssertionLabel = FString::Printf(
            TEXT("%s contributes its intended visual-entry count"), ExpectedRoots[RootIndex].Root);
        TestEqual(*AssertionLabel, RootCounts[RootIndex], ExpectedRoots[RootIndex].Count);
    }

    const TMap<FName, TSoftObjectPtr<UMaterialInterface>>& PaletteReferences =
        Defaults->GetCoilPreparationPaletteMaterialReferences();
    TestEqual(TEXT("Accepted component-level palettes remain explicit soft dependencies"),
        PaletteReferences.Num(), 58);
    bool bEveryPaletteReferenceResolved = true;
    for (const TPair<FName, TSoftObjectPtr<UMaterialInterface>>& Palette : PaletteReferences)
    {
        bEveryPaletteReferenceResolved &= Palette.Value.LoadSynchronous() != nullptr;
    }
    TestTrue(TEXT("Every component-level palette dependency resolves from Content"),
        bEveryPaletteReferenceResolved);
    const TSoftObjectPtr<UMaterialInterface>* PR009Frame = PaletteReferences.Find(FName(TEXT("PR009.Frame")));
    const TSoftObjectPtr<UMaterialInterface>* PR010Frame = PaletteReferences.Find(FName(TEXT("PR010.Frame")));
    TestTrue(TEXT("PR009 keeps its accepted v096/v086 presentation palette authority"),
        PR009Frame && PR009Frame->ToSoftObjectPath().ToString().Contains(TEXT("Presentation_v086")));
    TestTrue(TEXT("PR010 keeps its accepted-v103 v085 baseline palette authority"),
        PR010Frame && PR010Frame->ToSoftObjectPath().ToString().Contains(TEXT("Presentation_v085")));

    TestTrue(TEXT("Contract includes the corrected PR009 v087 static release group"),
        References.ContainsByPredicate([](const TSoftObjectPtr<UStaticMesh>& Reference)
        {
            return Reference.ToSoftObjectPath().ToString().Contains(
                TEXT("SM_CA_MW_PR009_VisionCentre_01_v087"));
        }));
    TestTrue(TEXT("Contract includes PR010 accepted-baseline release-art blank stacks"),
        References.ContainsByPredicate([](const TSoftObjectPtr<UStaticMesh>& Reference)
        {
            return Reference.ToSoftObjectPath().ToString().Contains(
                TEXT("SM_CA_MW_PR010_BlankStack_Layered_v101"));
        }));

    FFactoryBuilderAutomationWorld Fixture(TEXT("LB_CoilPreparationImportedComposite"));
    ALBFactoryBuildMachine* Machine = Fixture.World
        ? Fixture.World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    const bool bConfigured = Machine && Machine->Configure(
        TEXT("COIL-PREPARATION-ASSET-CONTRACT"), ELBFactoryBuildMachineType::DecoilerFeeder);
    TestTrue(TEXT("Coil preparation machine configures"), bConfigured);
    if (!bConfigured) return false;

    TestEqual(TEXT("All six stations resolved atomically"),
        Machine->GetResolvedCoilPreparationStationCount(), 6);
    TestEqual(TEXT("All 75 imported visual entries are visible"),
        Machine->GetVisibleCoilPreparationArtPartCount(), 75);
    TestEqual(TEXT("A fully resolved composite exposes no Engine BasicShapes fallback"),
        Machine->GetVisiblePlaceholderPartCount(), 0);

    int32 VisibleImportedCount = 0;
    int32 VisibleBasicShapeCount = 0;
    bool bPresentationOnlyContract = true;
    for (const UStaticMeshComponent* Part : Machine->GetCoilPreparationVisualComponents())
    {
        if (!Part || !Part->IsVisible() || !Part->GetStaticMesh()) continue;
        const FString Path = Part->GetStaticMesh()->GetPathName();
        if (Path.StartsWith(TEXT("/Engine/BasicShapes/"))) ++VisibleBasicShapeCount;
        else ++VisibleImportedCount;
        bPresentationOnlyContract &= Part->GetCollisionEnabled() == ECollisionEnabled::NoCollision
            && !Part->GetGenerateOverlapEvents()
            && !Part->CanEverAffectNavigation();
    }
    TestEqual(TEXT("Presentation-pool audit independently counts all imported station parts"),
        VisibleImportedCount, 75);
    TestEqual(TEXT("Presentation-pool audit independently finds zero primitive fallbacks"),
        VisibleBasicShapeCount, 0);
    TestTrue(TEXT("Preparation art cannot add donor collision, overlaps or nav geometry"),
        bPresentationOnlyContract);

    TestTrue(TEXT("Legacy gameplay envelope is unchanged"),
        Machine->GetMachineHalfExtent().Equals(FVector(750.0f, 1300.0f, 350.0f))
        && Machine->GetProtectedEnvelopeHalfExtent().Equals(FVector(750.0f, 1300.0f, 350.0f)));
    TestTrue(TEXT("Legacy process identity, material flow and transports are unchanged"),
        Machine->InputPort && Machine->OutputPort
        && Machine->InputPort->ProcessStage == LBFactoryProcessStage::DecoilerThreader
        && Machine->OutputPort->ProcessStage == LBFactoryProcessStage::DecoilerThreader
        && Machine->InputPort->MaterialClass == ELBFactoryMaterialClass::Coil
        && Machine->OutputPort->MaterialClass == ELBFactoryMaterialClass::Blank
        && Machine->InputPort->TransportKind == ELBFactoryTransportKind::AGVHandoff
        && Machine->OutputPort->TransportKind == ELBFactoryTransportKind::RollerConveyor
        && Machine->InputPort->MaximumConnections == 4
        && Machine->GetRequiredAutomaticProcessSteps() == 6);
    const FLBFactoryBuildMachineSaveState Saved = Machine->CaptureSaveState();
    TestTrue(TEXT("Save-state identity and six-step gameplay contract are unchanged"),
        Saved.MachineId == TEXT("COIL-PREPARATION-ASSET-CONTRACT")
        && Saved.MachineType == ELBFactoryBuildMachineType::DecoilerFeeder
        && Saved.RequiredAutomaticProcessSteps == 6);
    return true;
}

bool FLBCoilPreparationCookManifestContractTest::RunTest(const FString& Parameters)
{
    const FString ConfigPath = FPaths::ProjectConfigDir() / TEXT("DefaultGame.ini");
    FString ConfigContents;
    TestTrue(TEXT("Project packaging configuration is readable"),
        FFileHelper::LoadFileToString(ConfigContents, *ConfigPath));

    const TCHAR* RequiredCookRoots[] =
    {
        TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001"),
        TEXT("/Game/LineBoss/Stations/Press/PR006/Candidate_v001"),
        TEXT("/Game/LineBoss/Stations/Press/PR007/Candidate_v001"),
        TEXT("/Game/LineBoss/Stations/Press/PR008/Detailed_v001"),
        TEXT("/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision"),
        TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v086"),
        TEXT("/Game/LineBoss/Candidates/PressShop/PR010/Blockout_v001"),
        TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v100"),
        TEXT("/Game/LineBoss/Candidates/PressShop/PR010/ReleaseArt_v101"),
        TEXT("/Game/LineBoss/Stations/Press/PR009/Presentation_v085")
    };
    for (const TCHAR* Root : RequiredCookRoots)
    {
        TestTrue(FString::Printf(TEXT("Cook manifest includes runtime soft-reference root %s"), Root),
            ConfigContents.Contains(Root));
    }
    return true;
}

bool FLBFactoryAutomaticInboundAGVRouteTest::RunTest(const FString& Parameters)
{
    FFactoryBuilderAutomationWorld Fixture(TEXT("LB_AutomaticInboundAGVRoute"));
    UWorld* World = Fixture.World;
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(World) : nullptr;
    ALBCoilAGVController* AGV = World ? World->SpawnActor<ALBCoilAGVController>() : nullptr;
    const bool bFixtureReady = World && Fixture.BuildAuthority && Builder && AGV
        && AGV->DiscoverAndBind();
    TestTrue(TEXT("Automatic-route fixture has a registered world, build floor and bound AGV"),
        bFixtureReady);
    if (!bFixtureReady)
    {
        return false;
    }

    FString Reason;
    AActor* Inbound = nullptr;
    AActor* PR002 = nullptr;
    const bool bInboundPlaced = Builder->PlaceMachine(
        ELBFactoryBuildMachineType::InboundDeliveryDock, FTransform(FVector::ZeroVector),
        Inbound, Reason);
    TestTrue(FString::Printf(TEXT("Player places inbound without painting a route: %s"),
        *Reason), bInboundPlaced);
    ALBFactoryBuildMachine* InboundMachine = Cast<ALBFactoryBuildMachine>(Inbound);
    TestNotNull(TEXT("Placed inbound actor has the expected machine type"), InboundMachine);
    if (!bInboundPlaced || !InboundMachine) return false;

    ALBFactoryAGVInfrastructure* RejectedManualEndpoint = nullptr;
    TestFalse(TEXT("Ordinary player infrastructure cannot bypass a machine protected envelope"),
        Builder->PlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::WaitPoint,
            INDEX_NONE, InboundMachine->GetActorTransform(), RejectedManualEndpoint, Reason));
    TestNull(TEXT("Rejected player endpoint does not leave a hidden infrastructure actor"),
        RejectedManualEndpoint);
    TestTrue(TEXT("Protected-envelope rejection remains player-actionable"),
        Reason.Contains(TEXT("PROTECTED MACHINE ENVELOPE")));

    ALBPressShopStorageZone* SafeBuffer = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Player provides the required wrapped-coil buffer before PR002"), SafeBuffer
        && SafeBuffer->Configure(TEXT("SZ-COIL-AUTO-ROUTE"),
            ELBPressShopStorageType::BareCoils, 4, FVector(300.0f)));
    const bool bPR002Placed = Builder->PlaceMachine(
        ELBFactoryBuildMachineType::CoilWeighInspectionCell,
        // Keep the protected envelopes separate while leaving the compatible
        // Inbound-OUT -> PR002-IN ports inside their 25 m automatic-link reach.
        FTransform(FVector(1600.0f, 1600.0f, 0.0f)), PR002, Reason);
    TestTrue(FString::Printf(TEXT("Placing PR002 automatically builds and configures its AGV route: %s"),
        *Reason), bPR002Placed);
    ALBFactoryBuildMachine* PR002Machine = Cast<ALBFactoryBuildMachine>(PR002);
    TestNotNull(TEXT("Successful PR002 placement returns the expected machine actor"), PR002Machine);
    if (!bPR002Placed || !PR002Machine || !PR002Machine->InputPort) return false;

    int32 WaitCount = 0;
    int32 WaypointCount = 0;
    int32 RouteTileCount = 0;
    int32 AutomaticCount = 0;
    int32 AutomaticWalkwayCount = 0;
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It)
    {
        if (It->ActorHasTag(TEXT("LB.FactoryBuilder.AutomaticAGVRoute"))) ++AutomaticCount;
        if (It->ActorHasTag(TEXT("LB.FactoryBuilder.AutomaticServiceWalkway"))) ++AutomaticWalkwayCount;
        switch (It->GetInfrastructureType())
        {
        case ELBFactoryAGVInfrastructureType::WaitPoint: ++WaitCount; break;
        case ELBFactoryAGVInfrastructureType::RouteWaypoint: ++WaypointCount; break;
        case ELBFactoryAGVInfrastructureType::AGVRouteSegment: ++RouteTileCount; break;
        default: break;
        }
    }
    TestEqual(TEXT("Automatic route creates one lorry wait point"), WaitCount, 1);
    TestEqual(TEXT("Automatic route creates one readable corner"), WaypointCount, 1);
    TestTrue(TEXT("Automatic route continuously tiles both movement legs"), RouteTileCount >= 2);
    TestEqual(TEXT("Every generated route item is marked as automatic"),
        AutomaticCount, WaitCount + WaypointCount + RouteTileCount);
    TestTrue(TEXT("Automatic material route also creates its safe service walkway"),
        AutomaticWalkwayCount >= 2);
    TestTrue(TEXT("Coil AGV receives the generated PR002 route immediately"),
        FVector2D(AGV->GetConfiguredDockPoint()).Equals(
            FVector2D(PR002Machine->InputPort->GetComponentLocation()), 1.0f));
    TArray<FLBFactoryAGVInfrastructureSaveState> SavedRoute;
    TestTrue(TEXT("Automatic route is included in normal save data"),
        Builder->CaptureAGVInfrastructure(SavedRoute));
    TestEqual(TEXT("Saved automatic route and walkways retain every generated item"),
        SavedRoute.Num(), AutomaticCount + AutomaticWalkwayCount);
    return true;
}

bool FLBFactoryDemoAlignedInboundAGVRouteTest::RunTest(const FString& Parameters)
{
    FFactoryBuilderAutomationWorld Fixture(TEXT("LB_DemoAlignedInboundAGVRoute"));
    UWorld* World = Fixture.World;
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(World) : nullptr;
    ALBCoilAGVController* AGV = World ? World->SpawnActor<ALBCoilAGVController>() : nullptr;
    TestTrue(TEXT("Packaged-demo route fixture is available"),
        World && Fixture.BuildAuthority && Builder && AGV && AGV->DiscoverAndBind());
    if (!World || !Fixture.BuildAuthority || !Builder || !AGV)
    {
        return false;
    }

    // Reproduce the legacy serialized route that v1026 retained when its generated straight
    // route failed to configure. At 120 cm/s this first leg reaches the same 30-second
    // dock_timeout pose seen in the packaged bridge snapshot.
    TestTrue(TEXT("Legacy map route is seeded before player construction"), AGV->ConfigureRoute(
        FVector(-6200.0f, -2700.0f, 29.0f), FVector::ZeroVector, FVector(1000.0f, 0.0f, 0.0f)));

    FString Reason;
    AActor* InboundActor = nullptr;
    AActor* PR002Actor = nullptr;
    TestTrue(TEXT("Demo inbound dock places at its packaged transform"), Builder->PlaceMachine(
        ELBFactoryBuildMachineType::InboundDeliveryDock,
        FTransform(FRotator(0.0f, -90.0f, 0.0f), FVector(-10000.0f, -1000.0f, 0.0f)),
        InboundActor, Reason));
    ALBPressShopStorageZone* SafeBuffer = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Demo wrapped-coil buffer unlocks PR002"), SafeBuffer && SafeBuffer->Configure(
        TEXT("SZ-COIL-DEMO-ROUTE"), ELBPressShopStorageType::BareCoils, 12,
        FVector(710.0f, 650.0f, 125.0f)));
    const bool bPR002Placed = Builder->PlaceMachine(
        ELBFactoryBuildMachineType::CoilWeighInspectionCell,
        FTransform(FRotator(0.0f, -90.0f, 0.0f), FVector(-6800.0f, -1000.0f, 0.0f)),
        PR002Actor, Reason);
    TestTrue(FString::Printf(TEXT("Collinear demo PR002 placement configures the live AGV: %s"),
        *Reason), bPR002Placed);
    TestTrue(TEXT("Builder reports a live configured AGV instead of zero active AGVs"),
        Reason.Contains(TEXT("1 ACTIVE AGV")));

    ALBFactoryBuildMachine* Inbound = Cast<ALBFactoryBuildMachine>(InboundActor);
    ALBFactoryBuildMachine* PR002 = Cast<ALBFactoryBuildMachine>(PR002Actor);
    TestTrue(TEXT("Demo placement returns both endpoint machine actors"),
        Inbound && Inbound->OutputPort && PR002 && PR002->InputPort);
    if (!bPR002Placed || !Inbound || !Inbound->OutputPort || !PR002 || !PR002->InputPort)
        return false;
    const FVector ExpectedStart = Inbound && Inbound->OutputPort
        ? Inbound->OutputPort->GetComponentLocation() : FVector::ZeroVector;
    const FVector ExpectedDock = PR002 && PR002->InputPort
        ? PR002->InputPort->GetComponentLocation() : FVector::ZeroVector;
    TestTrue(TEXT("Generated straight route replaces the stale staged point"),
        AGV->GetVehicleLocation().Equals(FVector(ExpectedStart.X, ExpectedStart.Y, 29.0f), 0.1f));
    TestTrue(TEXT("Generated route targets the exact PR002 input"),
        FVector2D(AGV->GetConfiguredDockPoint()).Equals(FVector2D(ExpectedDock), 0.1f));
    TestTrue(TEXT("Demo coil dispatch starts on the generated route"),
        AGV->StartDispatch(TEXT("BRIDGE-COIL-001")));

    float ElapsedSeconds = 0.0f;
    bool bTravelHeightStayedConstant = true;
    bool bActorRootFollowedController = true;
    for (int32 Step = 0; Step < 350 && !AGV->IsHandoffReady()
        && AGV->GetPhase() != ELBCoilAGVPhase::Fault; ++Step)
    {
        AGV->Tick(0.1f);
        ElapsedSeconds += 0.1f;
        bTravelHeightStayedConstant &= FMath::IsNearlyEqual(AGV->GetVehicleLocation().Z, 29.0f, 0.01f);
        bActorRootFollowedController &= AGV->GetActorLocation().Equals(AGV->GetVehicleLocation(), 0.1f);
    }
    TestTrue(TEXT("Packaged-demo AGV reaches PR002 before the 35-second observation"),
        AGV->IsHandoffReady() && ElapsedSeconds < 35.0f);
    TestEqual(TEXT("Aligned route completes without dock_timeout"),
        AGV->GetFault(), ELBCoilAGVFault::None);
    TestTrue(TEXT("Generated route preserves the owned visual root travel height"),
        bTravelHeightStayedConstant);
    TestTrue(TEXT("Whole AGV actor follows the route authority"), bActorRootFollowedController);
    TestTrue(TEXT("AGV stops at the exact PR002 input"), AGV->GetVehicleLocation().Equals(
        FVector(ExpectedDock.X, ExpectedDock.Y, 29.0f), 0.1f));

    return true;
}

bool FLBFactoryMixedAGVRouteProfileRebindTest::RunTest(const FString& Parameters)
{
    FFactoryBuilderAutomationWorld Fixture(TEXT("LB_MixedAGVRouteProfiles"));
    UWorld* World = Fixture.World;
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(World) : nullptr;
    ALBPressShopBuildAuthority* Authority = Fixture.BuildAuthority;
    TestTrue(TEXT("Mixed-profile edit fixture exists"), World && Builder && Authority);
    if (!World || !Builder || !Authority)
    {
        return false;
    }

    auto SpawnInfrastructure = [World](const TCHAR* Id,
        const ELBFactoryAGVInfrastructureType Type, const FVector& Location,
        const FRotator& Rotation = FRotator::ZeroRotator, const int32 TrainIndex = INDEX_NONE)
    {
        ALBFactoryAGVInfrastructure* Item = World->SpawnActor<ALBFactoryAGVInfrastructure>(
            ALBFactoryAGVInfrastructure::StaticClass(), FTransform(Rotation, Location));
        return Item && Item->Configure(FName(Id), Type, TrainIndex) ? Item : nullptr;
    };

    // Build the train-owned route first so its legacy first-wait/first-waypoint lookup remains
    // deterministic while this test proves the new per-vehicle ownership at edit time.
    ALBFactoryAGVInfrastructure* TrainWait = SpawnInfrastructure(TEXT("TRAIN-WAIT-0"),
        ELBFactoryAGVInfrastructureType::WaitPoint, FVector(-3000.0f, 2500.0f, 0.0f));
    ALBFactoryAGVInfrastructure* TrainTurn = SpawnInfrastructure(TEXT("TRAIN-TURN-0"),
        ELBFactoryAGVInfrastructureType::RouteWaypoint, FVector(-2000.0f, 2500.0f, 0.0f));
    ALBFactoryAGVInfrastructure* TrainHandoff = SpawnInfrastructure(TEXT("S01-HANDOFF-A"),
        ELBFactoryAGVInfrastructureType::PressTrainHandoff,
        FVector(-2000.0f, 3500.0f, 0.0f), FRotator::ZeroRotator, 0);
    ALBFactoryAGVInfrastructure* TrainRoute1 = SpawnInfrastructure(TEXT("TRAIN-ROUTE-1"),
        ELBFactoryAGVInfrastructureType::AGVRouteSegment,
        FVector(-2750.0f, 2500.0f, 0.0f));
    TestTrue(TEXT("Train-owned route endpoints configure"), TrainWait && TrainTurn && TrainHandoff
        && TrainRoute1
        && SpawnInfrastructure(TEXT("TRAIN-ROUTE-2"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(-2250.0f, 2500.0f, 0.0f))
        && SpawnInfrastructure(TEXT("TRAIN-ROUTE-3"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(-2000.0f, 2750.0f, 0.0f), FRotator(0.0f, 90.0f, 0.0f))
        && SpawnInfrastructure(TEXT("TRAIN-ROUTE-4"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(-2000.0f, 3250.0f, 0.0f), FRotator(0.0f, 90.0f, 0.0f)));
    ALBCoilAGVController* TrainAGV = World->SpawnActor<ALBCoilAGVController>();
    TestTrue(TEXT("Train AGV records Train A route ownership"), TrainAGV
        && TrainAGV->ConfigureFromPlayerBuiltInfrastructure(0)
        && TrainAGV->GetRouteProfile() == ELBCoilAGVRouteProfile::PressTrainHandoff
        && TrainAGV->GetAssignedRouteTrainIndex() == 0);

    ALBFactoryBuildMachine* Inbound = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(0.0f, -3000.0f, 0.0f)));
    ALBFactoryBuildMachine* PR002 = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(2500.0f, -3000.0f, 0.0f)));
    TestTrue(TEXT("Inbound route machine endpoints configure"), Inbound && PR002
        && Inbound->Configure(TEXT("INBOUND-MIXED-PROFILE"), ELBFactoryBuildMachineType::InboundDeliveryDock)
        && PR002->Configure(TEXT("PR002-MIXED-PROFILE"), ELBFactoryBuildMachineType::CoilWeighInspectionCell)
        && Inbound->OutputPort && PR002->InputPort);
    if (!Inbound || !PR002 || !Inbound->OutputPort || !PR002->InputPort)
    {
        return false;
    }
    const FVector InboundStart = Inbound->OutputPort->GetComponentLocation();
    const FVector InboundDock = PR002->InputPort->GetComponentLocation();
    const FVector InboundTurn((InboundStart.X + InboundDock.X) * 0.5f,
        InboundStart.Y - 600.0f, 0.0f);
    TestTrue(TEXT("Inbound-owned route endpoints configure"),
        SpawnInfrastructure(TEXT("INBOUND-WAIT-MIXED"), ELBFactoryAGVInfrastructureType::WaitPoint,
            FVector(InboundStart.X, InboundStart.Y, 0.0f))
        && SpawnInfrastructure(TEXT("INBOUND-TURN-MIXED"), ELBFactoryAGVInfrastructureType::RouteWaypoint,
            InboundTurn));
    int32 InboundRouteSerial = 1;
    const auto PaintLeg = [&](const FVector& A, const FVector& B)
    {
        const float Length = FVector::Dist2D(A, B);
        const int32 TileCount = FMath::Max(1, FMath::CeilToInt(Length / 350.0f));
        const float Yaw = (B - A).Rotation().Yaw;
        for (int32 Index = 0; Index < TileCount; ++Index)
        {
            const float Alpha = (static_cast<float>(Index) + 0.5f) / static_cast<float>(TileCount);
            const FString Id = FString::Printf(TEXT("INBOUND-MIXED-ROUTE-%02d"), InboundRouteSerial++);
            if (!SpawnInfrastructure(*Id, ELBFactoryAGVInfrastructureType::AGVRouteSegment,
                FMath::Lerp(A, B, Alpha), FRotator(0.0f, Yaw, 0.0f))) return false;
        }
        return true;
    };
    TestTrue(TEXT("Inbound route has continuous painted coverage"),
        PaintLeg(InboundStart, InboundTurn) && PaintLeg(InboundTurn, InboundDock));
    ALBCoilAGVController* InboundAGV = World->SpawnActor<ALBCoilAGVController>();
    TestTrue(TEXT("Inbound AGV records PR002 route ownership"), InboundAGV
        && InboundAGV->ConfigureInboundRouteFromPlayerBuiltInfrastructure(Inbound, PR002)
        && InboundAGV->GetRouteProfile() == ELBCoilAGVRouteProfile::InboundPR002);
    const FVector InboundDockBeforeEdit = InboundAGV ? InboundAGV->GetConfiguredDockPoint() : FVector::ZeroVector;
    const FTransform EditedHandoff(FVector(-1950.0f, 3500.0f, 0.0f));
    FString Reason;
    TestTrue(TEXT("Train A handoff edit commits through the normal builder transaction"),
        Builder->UpdateAGVInfrastructureTransform(
            TrainHandoff ? TrainHandoff->GetInfrastructureId() : NAME_None, EditedHandoff, Reason));
    TestTrue(TEXT("Train A AGV alone receives the edited handoff"), TrainAGV
        && TrainAGV->GetConfiguredDockPoint().Equals(FVector(-1950.0f, 3500.0f, 29.0f), 0.1f));
    TestTrue(TEXT("Inbound PR002 AGV is never rerouted by a train handoff edit"), InboundAGV
        && InboundAGV->GetConfiguredDockPoint().Equals(InboundDockBeforeEdit, 0.1f)
        && InboundAGV->GetRouteProfile() == ELBCoilAGVRouteProfile::InboundPR002);
    const FTransform TrainRoute1BeforeBrokenEdit = TrainRoute1
        ? TrainRoute1->GetActorTransform() : FTransform::Identity;
    TestFalse(TEXT("Moving one train route tile away cannot falsely certify disconnected paint"),
        Builder->UpdateAGVInfrastructureTransform(
            TrainRoute1 ? TrainRoute1->GetInfrastructureId() : NAME_None,
            FTransform(FVector(-5000.0f, 4000.0f, 0.0f)), Reason));
    TestTrue(TEXT("Disconnected route edit reports its transactional rollback"),
        Reason.Contains(TEXT("EDIT ROLLED BACK")));
    TestTrue(TEXT("Disconnected train-route tile is restored to its exact prior transform"),
        TrainRoute1 && TrainRoute1->GetActorTransform().Equals(TrainRoute1BeforeBrokenEdit, 0.01f));

    ALBCoilAGVController* ManualAGV = World->SpawnActor<ALBCoilAGVController>();
    TestTrue(TEXT("Manual AGV remains explicitly unassigned"), ManualAGV
        && ManualAGV->ConfigureRoute(FVector(4000.0f, 3000.0f, 29.0f),
            FVector(4500.0f, 3000.0f, 29.0f), FVector(4500.0f, 3500.0f, 29.0f))
        && ManualAGV->GetRouteProfile() == ELBCoilAGVRouteProfile::ManualOrUnassigned);
    const FTransform HandoffBeforeAmbiguousEdit = TrainHandoff
        ? TrainHandoff->GetActorTransform() : FTransform::Identity;
    TestFalse(TEXT("Any ambiguous manual controller blocks route-authority edits"),
        Builder->UpdateAGVInfrastructureTransform(
            TrainHandoff ? TrainHandoff->GetInfrastructureId() : NAME_None,
            FTransform(FVector(-1900.0f, 3500.0f, 0.0f)), Reason));
    TestTrue(TEXT("Manual-controller rejection tells the player to assign its route"),
        Reason.Contains(TEXT("ASSIGN OR CONFIGURE")));
    TestTrue(TEXT("Rejected ambiguous edit leaves the handoff unchanged"), TrainHandoff
        && TrainHandoff->GetActorTransform().Equals(HandoffBeforeAmbiguousEdit, 0.01f));

    return true;
}

bool FLBFactoryAutomaticInboundRouteProfileOwnershipTest::RunTest(const FString& Parameters)
{
    FFactoryBuilderAutomationWorld Fixture(TEXT("LB_AutomaticInboundRouteProfileOwnership"));
    UWorld* World = Fixture.World;
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(World) : nullptr;
    TestTrue(TEXT("Automatic-route ownership fixture exists"),
        World && Fixture.BuildAuthority && Builder);
    if (!World || !Fixture.BuildAuthority || !Builder)
    {
        return false;
    }

    const auto SpawnInfrastructure = [World](const TCHAR* Id,
        const ELBFactoryAGVInfrastructureType Type, const FVector& Location,
        const FRotator& Rotation = FRotator::ZeroRotator, const int32 TrainIndex = INDEX_NONE)
    {
        ALBFactoryAGVInfrastructure* Item = World->SpawnActor<ALBFactoryAGVInfrastructure>(
            ALBFactoryAGVInfrastructure::StaticClass(), FTransform(Rotation, Location));
        return Item && Item->Configure(FName(Id), Type, TrainIndex);
    };
    TestTrue(TEXT("Unrelated Train A route configures before automatic inbound placement"),
        SpawnInfrastructure(TEXT("OWNERSHIP-TRAIN-WAIT"), ELBFactoryAGVInfrastructureType::WaitPoint,
            FVector(-4000.0f, 4000.0f, 0.0f))
        && SpawnInfrastructure(TEXT("OWNERSHIP-TRAIN-TURN"), ELBFactoryAGVInfrastructureType::RouteWaypoint,
            FVector(-3000.0f, 4000.0f, 0.0f))
        && SpawnInfrastructure(TEXT("OWNERSHIP-TRAIN-HANDOFF"), ELBFactoryAGVInfrastructureType::PressTrainHandoff,
            FVector(-3000.0f, 5000.0f, 0.0f), FRotator::ZeroRotator, 0)
        && SpawnInfrastructure(TEXT("OWNERSHIP-TRAIN-ROUTE-1"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(-3750.0f, 4000.0f, 0.0f))
        && SpawnInfrastructure(TEXT("OWNERSHIP-TRAIN-ROUTE-2"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(-3250.0f, 4000.0f, 0.0f))
        && SpawnInfrastructure(TEXT("OWNERSHIP-TRAIN-ROUTE-3"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(-3000.0f, 4250.0f, 0.0f), FRotator(0.0f, 90.0f, 0.0f))
        && SpawnInfrastructure(TEXT("OWNERSHIP-TRAIN-ROUTE-4"), ELBFactoryAGVInfrastructureType::AGVRouteSegment,
            FVector(-3000.0f, 4750.0f, 0.0f), FRotator(0.0f, 90.0f, 0.0f)));
    ALBCoilAGVController* TrainAGV = World->SpawnActor<ALBCoilAGVController>();
    ALBCoilAGVController* ManualAGV = World->SpawnActor<ALBCoilAGVController>();
    TestTrue(TEXT("Mixed pre-existing fleet has train-owned and manual profiles"), TrainAGV && ManualAGV
        && TrainAGV->ConfigureFromPlayerBuiltInfrastructure(0)
        && ManualAGV->ConfigureRoute(FVector(3000.0f, 4000.0f, 29.0f),
            FVector(3500.0f, 4000.0f, 29.0f), FVector(3500.0f, 4500.0f, 29.0f)));
    const FVector TrainDockBefore = TrainAGV ? TrainAGV->GetConfiguredDockPoint() : FVector::ZeroVector;
    const FVector ManualDockBefore = ManualAGV ? ManualAGV->GetConfiguredDockPoint() : FVector::ZeroVector;

    FString Reason;
    AActor* InboundActor = nullptr;
    AActor* PR002Actor = nullptr;
    TestTrue(TEXT("Inbound dock places beside the mixed fleet"), Builder->PlaceMachine(
        ELBFactoryBuildMachineType::InboundDeliveryDock, FTransform(FVector::ZeroVector),
        InboundActor, Reason));
    ALBPressShopStorageZone* SafeBuffer = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Required inbound buffer exists"), SafeBuffer && SafeBuffer->Configure(
        TEXT("SZ-OWNERSHIP-INBOUND"), ELBPressShopStorageType::BareCoils, 4, FVector(300.0f)));
    const bool bPR002Placed = Builder->PlaceMachine(
        ELBFactoryBuildMachineType::CoilWeighInspectionCell,
        FTransform(FVector(1600.0f, 1600.0f, 0.0f)), PR002Actor, Reason);
    TestTrue(FString::Printf(TEXT("PR002 placement creates its route without stealing a mixed-profile AGV: %s"),
        *Reason), bPR002Placed);
    TestNotNull(TEXT("Successful ownership placement returns its PR002 actor"), PR002Actor);
    TestTrue(TEXT("Automatic inbound placement never overwrites the train-owned controller"), TrainAGV
        && TrainAGV->GetRouteProfile() == ELBCoilAGVRouteProfile::PressTrainHandoff
        && TrainAGV->GetAssignedRouteTrainIndex() == 0
        && TrainAGV->GetConfiguredDockPoint().Equals(TrainDockBefore, 0.1f));
    TestTrue(TEXT("Ambiguous manual controller is not silently claimed as inbound"), ManualAGV
        && ManualAGV->GetRouteProfile() == ELBCoilAGVRouteProfile::ManualOrUnassigned
        && ManualAGV->GetConfiguredDockPoint().Equals(ManualDockBefore, 0.1f));

    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryOrderedMachineCatalogueTest,
    "LineBoss.FactoryBuilder.Machines.OrderedCatalogueAndPersistence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryTransactionalMachineEditingTest,
    "LineBoss.FactoryBuilder.Machines.TransactionalMoveRemoveAndPersistence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBFactoryOrderedMachineCatalogueTest::RunTest(const FString& Parameters)
{
    FFactoryBuilderAutomationWorld Fixture(TEXT("LB_OrderedMachineBuilder"));
    UWorld* World = Fixture.World;
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(World) : nullptr;
    TestNotNull(TEXT("Ordered machine builder exists"), Builder);
    TestNotNull(TEXT("Ordered machine builder has an authorised factory floor"),
        Fixture.BuildAuthority);
    if (!Builder || !World || !Fixture.BuildAuthority)
    {
        return false;
    }

    FString Reason;
    const TArray<ELBFactoryAGVInfrastructureType> EmptyShopInfrastructure = Builder->GetAvailableInfrastructureTypes();
    TestTrue(TEXT("Walkways are available in an empty player-built shop"),
        EmptyShopInfrastructure.Contains(ELBFactoryAGVInfrastructureType::PedestrianWalkway));
    TestTrue(TEXT("Crossings are available in an empty player-built shop"),
        EmptyShopInfrastructure.Contains(ELBFactoryAGVInfrastructureType::PedestrianCrossing));
    TestTrue(TEXT("Safety fence is available in an empty player-built shop"),
        EmptyShopInfrastructure.Contains(ELBFactoryAGVInfrastructureType::SafetyFence));
    TestFalse(TEXT("AGV route remains locked until inbound delivery exists"),
        EmptyShopInfrastructure.Contains(ELBFactoryAGVInfrastructureType::AGVRouteSegment));
    ALBFactoryAGVInfrastructure* Walkway = nullptr;
    ALBFactoryAGVInfrastructure* Crossing = nullptr;
    ALBFactoryAGVInfrastructure* Fence = nullptr;
    TestTrue(TEXT("Player can place a walkway before machinery"), Builder->PlaceAGVInfrastructure(
        ELBFactoryAGVInfrastructureType::PedestrianWalkway, INDEX_NONE,
        FTransform(FVector(0, -1000, 0)), Walkway, Reason));
    TestTrue(TEXT("Player can place a protected pedestrian crossing"), Builder->PlaceAGVInfrastructure(
        ELBFactoryAGVInfrastructureType::PedestrianCrossing, INDEX_NONE,
        FTransform(FVector(500, -1000, 0)), Crossing, Reason));
    TestTrue(TEXT("Player can place safety fencing"), Builder->PlaceAGVInfrastructure(
        ELBFactoryAGVInfrastructureType::SafetyFence, INDEX_NONE,
        FTransform(FVector(1000, -1000, 0)), Fence, Reason));
    TestTrue(TEXT("Walkway uses green player floor marking"), Walkway
        && Walkway->GetFloorMarkingColour().G > Walkway->GetFloorMarkingColour().B);
    TestTrue(TEXT("Crossing uses yellow player floor marking"), Crossing
        && Crossing->GetFloorMarkingColour().R > Crossing->GetFloorMarkingColour().B);
    TestTrue(TEXT("Inbound delivery is available at an empty factory"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::InboundDeliveryDock, Reason));
    TestFalse(TEXT("Depackaging is withheld until bare-coil storage exists"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::DepackagingRobot, Reason));
    TestTrue(TEXT("Missing predecessor reason is player-actionable"),
        Reason.Contains(TEXT("INBOUND DELIVERY")));
    TestEqual(TEXT("No storage is offered before inbound authority"),
        Builder->GetAvailableStorageTypes().Num(), 0);

    ALBFactoryBuildMachine* Inbound = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Inbound fixture receives deterministic identity"), Inbound && Inbound->Configure(
        TEXT("INBOUND-001"), ELBFactoryBuildMachineType::InboundDeliveryDock));
    const UStaticMeshComponent* LorryVisual = Inbound ? Inbound->GetApprovedVisualComponent() : nullptr;
    TestTrue(TEXT("Inbound player asset uses the native development lorry proxy"),
        LorryVisual && LorryVisual->IsVisible() && LorryVisual->GetStaticMesh()
        && LorryVisual->GetStaticMesh()->GetPathName().Contains(TEXT("/Engine/BasicShapes/Cube")));
    TestTrue(TEXT("Loaded lorry keeps its full 16.5 m flow-axis envelope"), Inbound
        && FMath::IsNearlyEqual(Inbound->GetMachineHalfExtent().Y * 2.0f, 1700.0f));
    TestTrue(TEXT("Loaded lorry rotates source X length onto player flow Y"), LorryVisual
        && FMath::IsNearlyEqual(LorryVisual->GetRelativeRotation().Yaw, 90.0f));
    TestTrue(TEXT("Inbound actor pivot remains on the factory floor instead of floating the lorry"),
        Inbound && FMath::IsNearlyZero(Inbound->GetPlacementRootHeightCm()));
    TestTrue(TEXT("Inbound protected envelope includes the full offset lorry and coil-handler footprint"), Inbound
        && Inbound->GetProtectedEnvelopeRelativeCentre().Equals(FVector(64.0f, -59.75f, 398.5f), 0.01f)
        && Inbound->GetProtectedEnvelopeHalfExtent().Equals(FVector(716.0f, 909.75f, 398.5f), 0.01f));
    if (Inbound)
    {
        FBox VisiblePackageBounds(EForceInit::ForceInit);
        TInlineComponentArray<UStaticMeshComponent*> MeshComponents(Inbound);
        for (UStaticMeshComponent* Component : MeshComponents)
        {
            if (!Component || !Component->IsVisible() || !Component->GetStaticMesh()) continue;
            Component->UpdateBounds();
            VisiblePackageBounds += Component->Bounds.GetBox();
        }
        const FVector EnvelopeCentre = Inbound->GetActorTransform().TransformPosition(
            Inbound->GetProtectedEnvelopeRelativeCentre());
        const FVector EnvelopeExtent = Inbound->GetProtectedEnvelopeHalfExtent();
        const FBox EnvelopeBounds(EnvelopeCentre - EnvelopeExtent, EnvelopeCentre + EnvelopeExtent);
        AddInfo(FString::Printf(TEXT("Inbound visible bounds min=%s max=%s; envelope min=%s max=%s"),
            *VisiblePackageBounds.Min.ToString(), *VisiblePackageBounds.Max.ToString(),
            *EnvelopeBounds.Min.ToString(), *EnvelopeBounds.Max.ToString()));
        TestTrue(TEXT("Measured lorry, coil handler, coils and saddle all fit the protected envelope"),
            VisiblePackageBounds.IsValid
            && VisiblePackageBounds.Min.X >= EnvelopeBounds.Min.X - 0.1f
            && VisiblePackageBounds.Min.Y >= EnvelopeBounds.Min.Y - 0.1f
            && VisiblePackageBounds.Min.Z >= EnvelopeBounds.Min.Z - 0.1f
            && VisiblePackageBounds.Max.X <= EnvelopeBounds.Max.X + 0.1f
            && VisiblePackageBounds.Max.Y <= EnvelopeBounds.Max.Y + 0.1f
            && VisiblePackageBounds.Max.Z <= EnvelopeBounds.Max.Z + 0.1f);
        TestTrue(TEXT("Development lorry proxy is seated at the actor floor datum"), LorryVisual
            && FMath::IsNearlyZero(LorryVisual->Bounds.GetBox().Min.Z, 0.1f));
    }
    TestEqual(TEXT("Player-built delivery arrives with four separate wrapped coils"),
        Inbound ? Inbound->GetVisibleTrailerCoilCount() : 0, 4);
    if (Inbound)
    {
        for (int32 CoilIndex = 0; CoilIndex < 4; ++CoilIndex)
        {
            const UStaticMeshComponent* Coil = Inbound->GetTrailerCoilComponent(CoilIndex);
            TestTrue(*FString::Printf(TEXT("Trailer coil %d bore axis runs across the trailer"), CoilIndex + 1),
                Coil && FMath::IsNearlyEqual(FMath::Abs(Coil->GetRelativeRotation().Yaw), 90.0f, 0.01f));
        }
    }
    TestTrue(TEXT("An unloading step can remove one trailer coil without replacing the lorry"),
        Inbound && Inbound->SetTrailerCoilVisible(0, false));
    TestEqual(TEXT("Only the unloaded coil disappears"),
        Inbound ? Inbound->GetVisibleTrailerCoilCount() : 0, 3);
    TestTrue(TEXT("Delivery fixture can restore its first load for later assertions"),
        Inbound && Inbound->SetTrailerCoilVisible(0, true));
    TestTrue(TEXT("Inbound package uses a visible native primitive coil-handler body"), Inbound
        && Inbound->GetInboundCoilHandlerChassisComponent()
        && Inbound->GetInboundCoilHandlerChassisComponent()->IsVisible()
        && Inbound->GetInboundCoilHandlerChassisComponent()->GetStaticMesh());
    TestTrue(TEXT("Inbound package uses a separate bore-entry coil ram instead of forks"), Inbound
        && Inbound->GetInboundCoilHandlerRamComponent()
        && Inbound->GetInboundCoilHandlerRamComponent()->IsVisible()
        && Inbound->GetInboundCoilHandlerRamComponent()->GetStaticMesh());
    TestFalse(TEXT("A second inbound delivery authority is withheld"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::InboundDeliveryDock, Reason));
    const TArray<ELBPressShopStorageType> AfterInbound = Builder->GetAvailableStorageTypes();
    TestTrue(TEXT("Wrapped coil storage unlocks as soon as unloading exists"),
        AfterInbound.Contains(ELBPressShopStorageType::BareCoils));
    TestFalse(TEXT("Prepared blanks remain hidden before decoiling"),
        AfterInbound.Contains(ELBPressShopStorageType::PreparedBlanks));
    TestFalse(TEXT("Finished panels remain hidden before inspection"),
        AfterInbound.Contains(ELBPressShopStorageType::FinishedPanelStillages));
    TestFalse(TEXT("Depackaging cannot bypass the missing PR002 cell"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::DepackagingRobot, Reason));
    TestTrue(TEXT("Ordered catalogue names PR002 as the next missing dependency"),
        Reason.Contains(TEXT("PR002")));
    TestFalse(TEXT("PR002 waits until a safe wrapped-coil buffer exists"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::CoilWeighInspectionCell, Reason));

    ALBPressShopStorageZone* Coils = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Wrapped-coil buffer fixture configures"), Coils && Coils->Configure(
        TEXT("SZ-COIL-001"), ELBPressShopStorageType::BareCoils, 12, FVector(700.0f, 650.0f, 200.0f)));
    TestTrue(TEXT("PR002 becomes available after inbound delivery and storage"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::CoilWeighInspectionCell, Reason));

    ALBFactoryBuildMachine* PR002 = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("PR002 fixture configures"), PR002 && PR002->Configure(
        TEXT("PR002-001"), ELBFactoryBuildMachineType::CoilWeighInspectionCell));
    const UStaticMeshComponent* PR002Visual = PR002 ? PR002->GetPR002StationVisualComponent() : nullptr;
    TestTrue(TEXT("PR002 uses its approved scanner and weigh-cell visual"), PR002Visual
        && PR002Visual->IsVisible() && PR002Visual->GetStaticMesh()
        && PR002Visual->GetStaticMesh()->GetPathName().Contains(TEXT("SM_CA_MW_PR002_ScannerWeighCell_v922")));
    TestFalse(TEXT("Empty PR002 does not display a phantom coil"),
        PR002 && PR002->IsPR002PayloadVisible());
    TestTrue(TEXT("PR002 accepts a wrapped coil"),
        PR002 && PR002->AcceptInputUnit(TEXT("COIL-PR002-TEST")));
    TestTrue(TEXT("Loaded PR002 displays its removable wrapped coil"),
        PR002 && PR002->IsPR002PayloadVisible());
    FName PR002Output;
    TestTrue(TEXT("PR002 completes weigh and inspection"),
        PR002 && PR002->ProcessNextUnit(PR002Output));
    TestFalse(TEXT("PR002 clears the visual payload after inspection"),
        PR002 && PR002->IsPR002PayloadVisible());
    const TArray<ELBPressShopStorageType> AfterPR002 = Builder->GetAvailableStorageTypes();
    TestTrue(TEXT("Additional wrapped-coil storage remains available for bottleneck capacity"),
        AfterPR002.Contains(ELBPressShopStorageType::BareCoils));
    TestTrue(TEXT("Depackaging unlocks when the already-placed storage and PR002 both exist"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::DepackagingRobot, Reason));
    TestTrue(TEXT("Ordered catalogue reports the next machine is available"),
        Reason.Contains(TEXT("AVAILABLE")));

    TestTrue(TEXT("Depackaging becomes available after storage and PR002"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::DepackagingRobot, Reason));
    TestFalse(TEXT("Decoiler remains withheld until depackaging exists"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::DecoilerFeeder, Reason));

    ALBFactoryBuildMachine* Depack = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Depackaging fixture configures"), Depack && Depack->Configure(
        TEXT("DEPACK-001"), ELBFactoryBuildMachineType::DepackagingRobot));
    TestTrue(TEXT("PR004 uses the complete approved A-E runtime assembly"),
        Depack && !Depack->IsUsingModularPlaceholder()
        && Depack->GetApprovedVisualComponent()
        && Depack->GetApprovedVisualComponent()->IsVisible()
        && Depack->GetApprovedVisualComponent()->GetStaticMesh()
        && Depack->GetApprovedVisualComponent()->GetStaticMesh()->GetPathName().Contains(
            TEXT("SM_Cairnwell_PR004_CompleteCell_Runtime_v997")));
    TestTrue(TEXT("Decoiler becomes the next available machine"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::DecoilerFeeder, Reason));
    TestFalse(TEXT("Prepared-blank storage is still hidden before a decoiler is installed"),
        Builder->GetAvailableStorageTypes().Contains(ELBPressShopStorageType::PreparedBlanks));
    TestFalse(TEXT("Press train remains withheld until prepared-blank storage exists"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::PressTrain, Reason));

    ALBFactoryBuildMachine* Decoiler = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Decoiler fixture configures"), Decoiler && Decoiler->Configure(
        TEXT("DECOILER-001"), ELBFactoryBuildMachineType::DecoilerFeeder));
    TestTrue(TEXT("PR005-PR010 imported presentation exposes the complete preparation line"),
        Decoiler && !Decoiler->IsUsingModularPlaceholder()
        && Decoiler->GetResolvedCoilPreparationStationCount() == 6
        && Decoiler->GetVisibleCoilPreparationArtPartCount() == 75
        && Decoiler->GetVisiblePlaceholderPartCount() == 0
        && Decoiler->GetMachineHalfExtent().Y >= 1300.0f
        && Decoiler->GetRequiredAutomaticProcessSteps() == 6
        && (!Decoiler->GetApprovedVisualComponent() || !Decoiler->GetApprovedVisualComponent()->IsVisible()));
    TestTrue(TEXT("Prepared-blank storage unlocks after decoiling"),
        Builder->GetAvailableStorageTypes().Contains(ELBPressShopStorageType::PreparedBlanks));

    ALBPressShopStorageZone* Blanks = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Prepared-blank buffer fixture configures"), Blanks && Blanks->Configure(
        TEXT("SZ-BLANK-001"), ELBPressShopStorageType::PreparedBlanks, 8, FVector(500.0f, 400.0f, 150.0f)));
    TestTrue(TEXT("Press train becomes available after prepared-blank storage"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::PressTrain, Reason));
    TestFalse(TEXT("Inspection remains withheld until a native press train exists"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::InspectionCell, Reason));
    TArray<ALBPressTrainAStation*> CapacityTrains;
    for (int32 Index = 0; Index < 4; ++Index)
        CapacityTrains.Add(World->SpawnActor<ALBPressTrainAStation>());
    TestTrue(TEXT("Four-train capacity fixtures spawn"),
        CapacityTrains.Num() == 4 && !CapacityTrains.Contains(nullptr));
    TestFalse(TEXT("Catalogue refuses a fifth press train beyond A-D"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::PressTrain, Reason));
    TestTrue(TEXT("Capacity rejection explicitly names the four authored trains"),
        Reason.Contains(TEXT("FOUR")) && Reason.Contains(TEXT("A-D")));
    for (ALBPressTrainAStation* CapacityTrain : CapacityTrains)
        if (CapacityTrain) CapacityTrain->Destroy();

    ALBPressShopStorageZone* Finished = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Premature finished-panel buffer fixture configures"), Finished && Finished->Configure(
        TEXT("SZ-PANEL-001"), ELBPressShopStorageType::FinishedPanelStillages, 4,
        FVector(400.0f, 400.0f, 150.0f)));
    TestFalse(TEXT("Finished storage alone cannot bypass inspection and unlock outbound"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::OutboundPanelDock, Reason));
    TestTrue(TEXT("Outbound rejection names the missing inspection dependency"),
        Reason.Contains(TEXT("INSPECTION")));

    ALBFactoryBuildMachine* InspectionVisual = World->SpawnActor<ALBFactoryBuildMachine>();
    ALBFactoryBuildMachine* OutboundVisual = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Panel inspection placeholder configures"), InspectionVisual
        && InspectionVisual->Configure(TEXT("INSPECT-VISUAL-001"), ELBFactoryBuildMachineType::InspectionCell));
    TestTrue(TEXT("Panel inspection placeholder is an open portal with continuous bed"),
        InspectionVisual && InspectionVisual->GetVisiblePlaceholderPartCount() >= 14);
    TestFalse(TEXT("A full WIP store and inspection still require an empty-stillage return store"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::OutboundPanelDock, Reason));
    TestTrue(TEXT("Outbound rejection explicitly names the missing empty-stillage dependency"),
        Reason.Contains(TEXT("EMPTY")) && Reason.Contains(TEXT("STILLAGE")));
    ALBPressShopStorageZone* EmptyStillages = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Empty-stillage return store fixture configures"), EmptyStillages
        && EmptyStillages->Configure(TEXT("SZ-EMPTY-STILLAGE-001"),
            ELBPressShopStorageType::EmptyPanelStillages, 4, FVector(400.0f, 400.0f, 150.0f)));
    TestTrue(TEXT("Inspection plus full and empty stillage stores unlock the weld intake dock"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::OutboundPanelDock, Reason));
    TestTrue(TEXT("Outbound dock placeholder configures"), OutboundVisual
        && OutboundVisual->Configure(TEXT("OUTBOUND-VISUAL-001"), ELBFactoryBuildMachineType::OutboundPanelDock));
    TestTrue(TEXT("Outbound placeholder is a modular stillage dock"),
        OutboundVisual && OutboundVisual->GetVisiblePlaceholderPartCount() >= 10);
    if (OutboundVisual)
    {
        UStaticMeshComponent* InactiveCrane = nullptr;
        for (UActorComponent* Component : OutboundVisual->GetComponents())
        {
            if (Component && Component->GetFName() == FName(TEXT("InboundCraneRunwayVisual")))
            {
                InactiveCrane = Cast<UStaticMeshComponent>(Component);
                break;
            }
        }
        TestNotNull(TEXT("Reusable machine actor retains its named inbound-crane presentation slot"),
            InactiveCrane);
        TestTrue(TEXT("Inactive alternative presentation is both hidden and non-physical"),
            InactiveCrane && !InactiveCrane->IsVisible()
                && InactiveCrane->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
    }
    if (InspectionVisual) InspectionVisual->Destroy();
    if (OutboundVisual) OutboundVisual->Destroy();

    TArray<FLBFactoryBuildMachineSaveState> Saved;
    TestTrue(TEXT("Generic player-built machines capture"), Builder->CaptureMachines(Saved));
    TestEqual(TEXT("Four generic machines are captured"), Saved.Num(), 4);
    TestTrue(TEXT("Captured IDs are deterministic and sorted"), Saved.Num() == 4
        && Saved[0].MachineId == TEXT("DECOILER-001")
        && Saved[1].MachineId == TEXT("DEPACK-001") && Saved[2].MachineId == TEXT("INBOUND-001")
        && Saved[3].MachineId == TEXT("PR002-001"));
    if (Inbound) Inbound->SetActorLocation(FVector(999.0f, 999.0f, 0.0f));
    TestTrue(TEXT("Exact generic machine set restores"), Builder->RestoreMachines(Saved, Reason));
    TArray<FLBFactoryBuildMachineSaveState> RoundTrip;
    TestTrue(TEXT("Restored generic machines recapture"), Builder->CaptureMachines(RoundTrip));
    TestEqual(TEXT("Machine round-trip count remains exact"), RoundTrip.Num(), Saved.Num());

    return true;
}

bool FLBFactoryTransactionalMachineEditingTest::RunTest(const FString& Parameters)
{
    FFactoryBuilderAutomationWorld Fixture(TEXT("LB_TransactionalMachineEditing"));
    UWorld* World = Fixture.World;
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(World) : nullptr;
    ULBFactoryConnectionSubsystem* Connections = World
        ? World->GetSubsystem<ULBFactoryConnectionSubsystem>() : nullptr;
    TestTrue(TEXT("Transactional edit fixture has builder, graph and floor authority"),
        World && Builder && Connections && Fixture.BuildAuthority);
    if (!World || !Builder || !Connections || !Fixture.BuildAuthority) return false;

    ALBFactoryBuildMachine* Source = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FTransform(FVector::ZeroVector));
    ALBFactoryBuildMachine* Edited = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(0.0f, 1800.0f, 0.0f)));
    TestTrue(TEXT("Transactional source configures with stable identity"), Source
        && Source->Configure(TEXT("TX-DEPACK-001"),
            ELBFactoryBuildMachineType::DepackagingRobot));
    TestTrue(TEXT("Transactional edited machine configures with stable identity"), Edited
        && Edited->Configure(TEXT("TX-COIL-PREP-001"),
            ELBFactoryBuildMachineType::DecoilerFeeder));
    if (!Source || !Edited) return false;

    ALBFactoryTransportLink* OriginalLink = nullptr;
    FString Reason;
    TestTrue(TEXT("Legacy exact stage+1 route connects before editing"),
        Connections->Connect(Source->OutputPort, Edited->InputPort, OriginalLink, Reason));
    TestTrue(TEXT("Route transfer history exists before editing"),
        OriginalLink && OriginalLink->TryTransferUnits(7));
    TArray<FLBFactoryTransportLinkSaveState> OriginalEdges;
    TestTrue(TEXT("Exact edited-machine edge snapshot captures"),
        Connections->CaptureConnectionsForActor(Edited, OriginalEdges, Reason));
    TestTrue(TEXT("Snapshot preserves port identities and transfer history"),
        OriginalEdges.Num() == 1
        && OriginalEdges[0].SourcePortId == TEXT("TX-DEPACK-001-OUT")
        && OriginalEdges[0].TargetPortId == TEXT("TX-COIL-PREP-001-IN")
        && OriginalEdges[0].TransferredUnits == 7);
    TestTrue(TEXT("Public edit gate accepts the idle, unreserved connected machine"),
        Builder->CanEditMachine(TEXT("TX-COIL-PREP-001"), Reason));

    const FTransform SuccessfulTransform(FVector(100.0f, 2100.0f, 0.0f));
    TestTrue(TEXT("Selected actor is ignored by its own transform preflight"),
        Builder->ValidateMachineTransformForEdit(
            TEXT("TX-COIL-PREP-001"), SuccessfulTransform, Reason));
    TestTrue(FString::Printf(TEXT("Idle connected machine moves transactionally: %s"), *Reason),
        Builder->MoveMachine(TEXT("TX-COIL-PREP-001"), SuccessfulTransform, Reason));
    TestTrue(TEXT("Successful move applies the exact requested transform"),
        Edited->GetActorTransform().Equals(SuccessfulTransform, 0.001f));
    TestEqual(TEXT("Machine identity is preserved through move"),
        Edited->GetMachineId(), FName(TEXT("TX-COIL-PREP-001")));
    TestEqual(TEXT("Input port identity is preserved through move"),
        Edited->InputPort->PortId, FName(TEXT("TX-COIL-PREP-001-IN")));
    TArray<FLBFactoryTransportLinkSaveState> SuccessfulEdges;
    TestTrue(TEXT("Successful move recaptures its rebuilt edge"),
        Connections->CaptureConnectionsForActor(Edited, SuccessfulEdges, Reason));
    TestTrue(TEXT("Successful move preserves the exact logical link and transfer counter"),
        SuccessfulEdges.Num() == 1
        && SuccessfulEdges[0].SourcePortId == OriginalEdges[0].SourcePortId
        && SuccessfulEdges[0].TargetPortId == OriginalEdges[0].TargetPortId
        && SuccessfulEdges[0].TransferredUnits == OriginalEdges[0].TransferredUnits);

    TArray<FLBFactoryBuildMachineSaveState> SavedAfterSuccess;
    TestTrue(TEXT("Machine inventory captures after a successful edit"),
        Builder->CaptureMachines(SavedAfterSuccess));
    const FLBFactoryBuildMachineSaveState* SavedEdited = SavedAfterSuccess.FindByPredicate(
        [](const FLBFactoryBuildMachineSaveState& State)
        { return State.MachineId == TEXT("TX-COIL-PREP-001"); });
    TestTrue(TEXT("Campaign machine capture contains the edited transform and unchanged WIP"),
        SavedEdited && SavedEdited->WorldTransform.Equals(SuccessfulTransform, 0.001f)
        && SavedEdited->InputUnitIds.IsEmpty() && SavedEdited->OutputUnitIds.IsEmpty()
        && SavedEdited->CompletedUnitIds.IsEmpty());

    const FTransform BeforeRejectedEdit = Edited->GetActorTransform();
    TestFalse(TEXT("Move into another protected machine envelope is rejected"),
        Builder->MoveMachine(TEXT("TX-COIL-PREP-001"),
            FTransform(FVector(0.0f, 300.0f, 0.0f)), Reason));
    TestTrue(TEXT("Invalid-overlap failure leaves the actor transform unchanged"),
        Edited->GetActorTransform().Equals(BeforeRejectedEdit, 0.001f));
    TArray<FLBFactoryTransportLinkSaveState> EdgesAfterOverlapFailure;
    TestTrue(TEXT("Invalid-overlap failure leaves the live graph capturable"),
        Connections->CaptureConnectionsForActor(Edited, EdgesAfterOverlapFailure, Reason));
    TestTrue(TEXT("Invalid-overlap failure leaves link identity and counter unchanged"),
        EdgesAfterOverlapFailure.Num() == 1
        && EdgesAfterOverlapFailure[0].SourcePortId == SuccessfulEdges[0].SourcePortId
        && EdgesAfterOverlapFailure[0].TargetPortId == SuccessfulEdges[0].TargetPortId
        && EdgesAfterOverlapFailure[0].TransferredUnits == SuccessfulEdges[0].TransferredUnits);

    const FTransform OutOfRangeTransform(FVector(100.0f, 5000.0f, 0.0f));
    TestTrue(TEXT("Out-of-range proposal passes physical envelope validation"),
        Builder->ValidateMachineTransformForEdit(
            TEXT("TX-COIL-PREP-001"), OutOfRangeTransform, Reason));
    TestFalse(TEXT("Reconnect failure rejects the move"),
        Builder->MoveMachine(TEXT("TX-COIL-PREP-001"), OutOfRangeTransform, Reason));
    TestTrue(TEXT("Reconnect failure reports an explicit rollback"),
        Reason.Contains(TEXT("ROLLED BACK")));
    TestTrue(TEXT("Reconnect failure restores the exact actor transform"),
        Edited->GetActorTransform().Equals(BeforeRejectedEdit, 0.001f));
    TArray<FLBFactoryTransportLinkSaveState> EdgesAfterReconnectFailure;
    TestTrue(TEXT("Reconnect rollback leaves the graph coherent"),
        Connections->CaptureConnectionsForActor(
            Edited, EdgesAfterReconnectFailure, Reason));
    TestTrue(TEXT("Reconnect rollback leaves the exact edge set and transfer counter unchanged"),
        EdgesAfterReconnectFailure.Num() == 1
        && EdgesAfterReconnectFailure[0].SourcePortId == SuccessfulEdges[0].SourcePortId
        && EdgesAfterReconnectFailure[0].TargetPortId == SuccessfulEdges[0].TargetPortId
        && EdgesAfterReconnectFailure[0].TransferredUnits == SuccessfulEdges[0].TransferredUnits);

    TestTrue(TEXT("Machine accepts active WIP for removal rejection coverage"),
        Edited->AcceptInputUnit(TEXT("TX-ACTIVE-WIP-001")));
    const FLBFactoryBuildMachineSaveState WIPBeforeRejectedRemoval = Edited->CaptureSaveState();
    TestFalse(TEXT("Removal rejects a machine with active WIP"),
        Builder->RemoveMachine(TEXT("TX-COIL-PREP-001"), Reason));
    const FLBFactoryBuildMachineSaveState WIPAfterRejectedRemoval = Edited->CaptureSaveState();
    TestTrue(TEXT("Rejected removal leaves WIP and transform unchanged"),
        WIPAfterRejectedRemoval.InputUnitIds == WIPBeforeRejectedRemoval.InputUnitIds
        && WIPAfterRejectedRemoval.OutputUnitIds == WIPBeforeRejectedRemoval.OutputUnitIds
        && WIPAfterRejectedRemoval.CompletedUnitIds == WIPBeforeRejectedRemoval.CompletedUnitIds
        && WIPAfterRejectedRemoval.WorldTransform.Equals(
            WIPBeforeRejectedRemoval.WorldTransform, 0.001f));

    ALBFactoryBuildMachine* Removable = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(),
        FTransform(FVector(8000.0f, 0.0f, 0.0f)));
    AActor* DependentOwner = World->SpawnActor<AActor>();
    TestTrue(TEXT("Idle removal fixture configures"), Removable
        && Removable->Configure(TEXT("TX-REMOVE-001"),
            ELBFactoryBuildMachineType::InspectionCell));
    if (Removable) Removable->SetOwner(DependentOwner);
    TestFalse(TEXT("Unsafe external ownership rejects removal without mutation"),
        Builder->RemoveMachine(TEXT("TX-REMOVE-001"), Reason));
    TestTrue(TEXT("Ownership rejection leaves the machine alive"), IsValid(Removable));
    if (Removable) Removable->SetOwner(nullptr);
    TestTrue(TEXT("Unowned idle machine removes cleanly"),
        Builder->RemoveMachine(TEXT("TX-REMOVE-001"), Reason));
    TestTrue(TEXT("Repeated machine removal is idempotent"),
        Builder->RemoveMachine(TEXT("TX-REMOVE-001"), Reason));

    TArray<FLBFactoryBuildMachineSaveState> FinalMachines;
    TArray<FLBFactoryTransportLinkSaveState> FinalConnections;
    TestTrue(TEXT("Machine capture remains coherent after successful and rejected edits"),
        Builder->CaptureMachines(FinalMachines));
    TestTrue(TEXT("Connection capture remains coherent after successful and rejected edits"),
        Connections->CaptureConnections(FinalConnections));
    TestFalse(TEXT("Removed identity is absent from campaign capture"),
        FinalMachines.ContainsByPredicate([](const FLBFactoryBuildMachineSaveState& State)
        { return State.MachineId == TEXT("TX-REMOVE-001"); }));
    TestTrue(TEXT("Surviving WIP machine and exact link remain in campaign capture"),
        FinalMachines.ContainsByPredicate([](const FLBFactoryBuildMachineSaveState& State)
        {
            return State.MachineId == TEXT("TX-COIL-PREP-001")
                && State.InputUnitIds.Num() == 1
                && State.InputUnitIds[0] == TEXT("TX-ACTIVE-WIP-001");
        })
        && FinalConnections.Num() == 1
        && FinalConnections[0].TransferredUnits == 7);

    return true;
}

bool FLBFactoryECoatPlacementContractTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_ECoat189MetrePlacementContract"));
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(World) : nullptr;
    TestNotNull(TEXT("Factory builder exposes the ED-line placement contract"), Builder);
    if (!World || !Builder)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FVector HalfExtent = FVector::ZeroVector;
    FVector RelativeCentre = FVector::ZeroVector;
    float RootHeightCm = -1.0f;
    FString Reason;
    TestTrue(TEXT("ED-line placement envelope resolves"), Builder->GetMachinePlacementEnvelope(
        ELBFactoryBuildMachineType::ECoatLine, HalfExtent, RelativeCentre,
        RootHeightCm, Reason));
    TestTrue(TEXT("Placement half extent reserves the complete 195 x 15 x 10 m safety box"),
        HalfExtent.Equals(FVector(9750.0f, 750.0f, 500.0f), 0.01f));
    TestTrue(TEXT("Placement centre preserves the asymmetric entry and output clearances"),
        RelativeCentre.Equals(FVector(9650.0f, 0.0f, 500.0f), 0.01f));
    TestTrue(TEXT("Protected local bounds are exactly -100 to 19400 cm along the line"),
        FMath::IsNearlyEqual(RelativeCentre.X - HalfExtent.X, -100.0f, 0.01f)
        && FMath::IsNearlyEqual(RelativeCentre.X + HalfExtent.X, 19400.0f, 0.01f));
    TestEqual(TEXT("ED-line origin remains on the factory floor datum"), RootHeightCm, 0.0f);
    TestTrue(TEXT("Player-facing placement authority names the true 189 m footprint"),
        Reason.Contains(TEXT("189 m")));

    const ALBECoatLineActor* Defaults = GetDefault<ALBECoatLineActor>();
    TestTrue(TEXT("Default ED-line process ports retain the complete-line endpoints"),
        Defaults && Defaults->GetInputPort() && Defaults->GetOutputPort()
        && Defaults->GetInputPort()->GetRelativeLocation().Equals(FVector(0.0f, 0.0f, 430.0f), 0.01f)
        && Defaults->GetOutputPort()->GetRelativeLocation().Equals(FVector(18900.0f, 0.0f, 430.0f), 0.01f));

    ALBPressShopBuildAuthority* Authority = World->SpawnActor<ALBPressShopBuildAuthority>();
    TestNotNull(TEXT("ED-line save fixture has a factory-floor authority"), Authority);
    if (Authority)
    {
        FLBPressShopBuildBay Bay;
        Bay.BayId = TEXT("ED-LINE-189M-BAY");
        Bay.Centre = FVector::ZeroVector;
        Bay.HalfExtent = FVector(10000.0f, 1000.0f, 1000.0f);
        Authority->BuildBays.Add(Bay);
        FLBPressShopUtilitySpine Utility;
        Utility.SpineId = TEXT("ED-LINE-189M-UTILITY");
        Utility.Start = FVector(-10000.0f, 0.0f, 0.0f);
        Utility.End = FVector(10000.0f, 0.0f, 0.0f);
        Utility.MaximumConnectionDistanceCm = 1000.0f;
        Authority->UtilitySpines.Add(Utility);
    }

    ALBECoatLineActor* Line = World->SpawnActor<ALBECoatLineActor>(
        ALBECoatLineActor::StaticClass(), FTransform(FVector(-9450.0f, 0.0f, 0.0f)));
    TestTrue(TEXT("Centred 189 m save fixture configures"),
        Line && Line->Configure(TEXT("ED-LINE-SAVE-189M"))
        && Line->AddCarrier(TEXT("ED-CARRIER-EXIT"), 18450.0f));
    if (Line && Authority)
    {
        TArray<FLBECoatLineSaveState> SaveSet;
        SaveSet.Add(Line->CaptureSaveState());
        TestTrue(TEXT("Captured dependent fixture uses ED-line save v3 and the 184.5 m exit centre"),
            SaveSet[0].Version == 3 && SaveSet[0].Carriers.Num() == 1
            && FMath::IsNearlyEqual(SaveSet[0].Carriers[0].DistanceCm, 18450.0f, 0.01f));
        TestTrue(TEXT("Builder preflight accepts the complete v3 footprint on one floor datum"),
            Builder->ValidateECoatLineSaveSet(SaveSet, Reason));
        Line->SetActorLocation(FVector(-9000.0f, 250.0f, 0.0f));
        TestTrue(TEXT("Builder restores the v3 ED-line fixture transactionally"),
            Builder->RestoreECoatLines(SaveSet, Reason));
        TestTrue(TEXT("Restored fixture returns to the centred 0-to-189 m world placement"),
            Line->GetActorLocation().Equals(FVector(-9450.0f, 0.0f, 0.0f), 0.01f));
    }

    World->DestroyWorld(false);
    return true;
}

bool FLBFactoryBodyWeldPlacementContractTest::RunTest(const FString& Parameters)
{
    FFactoryBuilderAutomationWorld Fixture(TEXT("LB_BodyWeldPlacementContract"));
    UWorld* World = Fixture.World;
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(World) : nullptr;
    TestTrue(TEXT("Body-weld fixture has builder and authorised factory floor"),
        World && Builder && Fixture.BuildAuthority);
    if (!World || !Builder || !Fixture.BuildAuthority) return false;

    FLBPressShopUtilitySpine Utility;
    Utility.SpineId = TEXT("BODY-WELD-TEST-UTILITY");
    Utility.Start = FVector(-25000.0f, 0.0f, 0.0f);
    Utility.End = FVector(25000.0f, 0.0f, 0.0f);
    Utility.MaximumConnectionDistanceCm = 10000.0f;
    Fixture.BuildAuthority->UtilitySpines.Add(Utility);

    TestEqual(TEXT("ED enum ordinal remains save compatible"),
        static_cast<uint8>(ELBFactoryBuildMachineType::ECoatLine), static_cast<uint8>(7));
    TestEqual(TEXT("Body-weld enum is appended after ED"),
        static_cast<uint8>(ELBFactoryBuildMachineType::BodyWeldLine), static_cast<uint8>(8));

    FVector HalfExtent;
    FVector RelativeCentre;
    float RootHeight = -1.0f;
    FString Reason;
    TestTrue(TEXT("Dedicated body-weld placement envelope resolves"),
        Builder->GetMachinePlacementEnvelope(ELBFactoryBuildMachineType::BodyWeldLine,
            HalfExtent, RelativeCentre, RootHeight, Reason));
    const ALBBodyWeldLineActor* Defaults = GetDefault<ALBBodyWeldLineActor>();
    const UBoxComponent* DefaultsEnvelope = Defaults ? Defaults->GetProtectedEnvelope() : nullptr;
    TestTrue(TEXT("Builder envelope exactly mirrors the composite actor's protected box"),
        DefaultsEnvelope && HalfExtent.Equals(DefaultsEnvelope->GetUnscaledBoxExtent(), 0.01f)
        && RelativeCentre.Equals(DefaultsEnvelope->GetRelativeLocation(), 0.01f)
        && FMath::IsNearlyZero(RootHeight));

    FString CanPlaceReason;
    TestFalse(TEXT("Body weld is gated until outbound panel dispatch exists"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::BodyWeldLine, CanPlaceReason));
    TestTrue(TEXT("Gate explains the missing outbound intake"),
        CanPlaceReason.Contains(TEXT("OUTBOUND")) || CanPlaceReason.Contains(TEXT("WELD SHOP INTAKE")));

    ALBFactoryBuildMachine* Outbound = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(-1000.0f, -900.0f, 0.0f)));
    TestTrue(TEXT("Test outbound stillage handoff configures"), Outbound
        && Outbound->Configure(TEXT("OUTBOUND-WELD-TEST"),
            ELBFactoryBuildMachineType::OutboundPanelDock));
    TestTrue(TEXT("Outbound unlocks body weld"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::BodyWeldLine, CanPlaceReason));
    TestFalse(TEXT("Overlapping body-weld transform is rejected by its full envelope"),
        Builder->ValidateMachineTransform(ELBFactoryBuildMachineType::BodyWeldLine,
            FTransform(FVector(-1000.0f, -900.0f, 0.0f)), Reason));

    AActor* PlacedActor = nullptr;
    TestTrue(FString::Printf(TEXT("Clear body-weld line places: %s"), *Reason),
        Builder->PlaceMachine(ELBFactoryBuildMachineType::BodyWeldLine,
            FTransform::Identity, PlacedActor, Reason));
    ALBBodyWeldLineActor* Weld = Cast<ALBBodyWeldLineActor>(PlacedActor);
    TestTrue(TEXT("Dedicated body-weld actor owns exact mandatory and optional ports"), Weld
        && Weld->GetStillageInputPort() && Weld->GetStillageInputPort()->IsConnected()
        && Weld->GetBaseKitInputPort() && !Weld->GetBaseKitInputPort()->IsConnected()
        && Weld->GetBIWOutputPort() && !Weld->GetBIWOutputPort()->IsConnected());
    TestFalse(TEXT("Only one complete body-weld line is allowed"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::BodyWeldLine, CanPlaceReason));
    TestTrue(TEXT("Body weld unlocks ED progression"),
        Builder->CanPlaceMachine(ELBFactoryBuildMachineType::ECoatLine, CanPlaceReason));
    Fixture.BuildAuthority->BuildBays[0].HalfExtent.X = 30000.0f;
    AActor* ECoatActor = nullptr;
    TestTrue(TEXT("ED placement connects the exact body-in-white output to its exact input"),
        Builder->PlaceMachine(ELBFactoryBuildMachineType::ECoatLine,
            FTransform(FVector(5901.0f, 0.0f, 0.0f)), ECoatActor, Reason));
    ALBECoatLineActor* ECoat = Cast<ALBECoatLineActor>(ECoatActor);
    TestTrue(TEXT("Body-weld BIW output and ED input share one authoritative link"),
        Weld && ECoat && Weld->GetBIWOutputPort()->IsConnected()
        && ECoat->GetInputPort()->IsConnected()
        && Weld->GetBIWOutputPort()->GetConnectedPort() == ECoat->GetInputPort());

    TArray<FLBBodyWeldLineSaveState> Saved;
    TestTrue(TEXT("Dedicated body-weld save captures"), Builder->CaptureBodyWeldLines(Saved));
    TestTrue(TEXT("Dedicated body-weld save validates"),
        Builder->ValidateBodyWeldLineSaveSet(Saved, Reason));
    TestEqual(TEXT("At most one complete line is captured"), Saved.Num(), 1);
    if (Weld) Weld->SetActorLocation(FVector(1000.0f, 1000.0f, 0.0f));
    TestTrue(TEXT("Dedicated body-weld save restores transactionally"),
        Builder->RestoreBodyWeldLines(Saved, Reason));
    TestTrue(TEXT("Restored body-weld transform is exact"), Weld && Saved.Num() == 1
        && Weld->GetActorTransform().Equals(Saved[0].WorldTransform, 0.01f));

    FLBFactoryBuildMachineSaveState Smuggled;
    Smuggled.MachineId = TEXT("SMUGGLED-WELD");
    Smuggled.MachineType = ELBFactoryBuildMachineType::BodyWeldLine;
    Smuggled.WorldTransform = FTransform::Identity;
    const TArray<FLBFactoryBuildMachineSaveState> SmuggledSet = {Smuggled};
    TestFalse(TEXT("Generic machine save cannot smuggle a composite body-weld actor"),
        Builder->ValidateMachineSaveSet(SmuggledSet, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryPlayerBuiltAGVInfrastructureTest,
    "LineBoss.FactoryBuilder.AGVInfrastructure.PlayerPlacementAndPersistence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBFactoryPlayerBuiltAGVInfrastructureTest::RunTest(const FString& Parameters)
{
    FFactoryBuilderAutomationWorld Fixture(TEXT("LB_PlayerBuiltAGVInfrastructure"));
    UWorld* World = Fixture.World;
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(World) : nullptr;
    TestNotNull(TEXT("Factory builder exists"), Builder);
    TestNotNull(TEXT("Player infrastructure fixture has an authorised factory floor"),
        Fixture.BuildAuthority);
    if (!Builder || !World || !Fixture.BuildAuthority)
    {
        return false;
    }

    FString Reason;
    ALBFactoryAGVInfrastructure* SavedWalkway = nullptr;
    ALBFactoryAGVInfrastructure* SavedCrossing = nullptr;
    ALBFactoryAGVInfrastructure* SavedFence = nullptr;
    TestTrue(TEXT("Walkway placement is part of the persisted infrastructure set"),
        Builder->PlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::PedestrianWalkway,
            INDEX_NONE, FTransform(FVector(0, -1000, 0)), SavedWalkway, Reason));
    TestTrue(TEXT("Crossing placement is part of the persisted infrastructure set"),
        Builder->PlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::PedestrianCrossing,
            INDEX_NONE, FTransform(FVector(500, -1000, 0)), SavedCrossing, Reason));
    TestTrue(TEXT("Fence placement is part of the persisted infrastructure set"),
        Builder->PlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::SafetyFence,
            INDEX_NONE, FTransform(FVector(1000, -1000, 0)), SavedFence, Reason));
    TestFalse(TEXT("AGV infrastructure stays locked before inbound delivery"),
        Builder->CanPlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::ChargingStation, INDEX_NONE, Reason));

    ALBFactoryBuildMachine* Inbound = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Inbound fixture configures"), Inbound && Inbound->Configure(
        TEXT("INBOUND-001"), ELBFactoryBuildMachineType::InboundDeliveryDock));

    for (int32 ChargerIndex = 0; ChargerIndex < 4; ++ChargerIndex)
    {
        ALBFactoryAGVInfrastructure* Charger = nullptr;
        TestTrue(FString::Printf(TEXT("Charger CS%d places"), ChargerIndex + 1),
            Builder->PlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::ChargingStation, INDEX_NONE,
                FTransform(FVector(-5000.0f + ChargerIndex * 500.0f, 0.0f, 0.0f)), Charger, Reason));
        TestTrue(TEXT("Charger gets sequential identity"), Charger
            && Charger->GetInfrastructureId() == FName(*FString::Printf(TEXT("CS-%02d"), ChargerIndex + 1)));
        TestTrue(TEXT("Charger carries saved no-collision floor paint"), Charger
            && Charger->HasFloorMarkingPresentation()
            && Charger->GetFloorMarkingDimensionsCm().X > 300.0f
            && Charger->GetFloorMarkingColour().B > Charger->GetFloorMarkingColour().R);
    }
    TestFalse(TEXT("A fifth charger is rejected"),
        Builder->CanPlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::ChargingStation, INDEX_NONE, Reason));

    for (int32 TrainIndex = 0; TrainIndex < 4; ++TrainIndex)
    {
        TestEqual(FString::Printf(TEXT("Next available handoff is Train %c"), TCHAR('A' + TrainIndex)),
            Builder->GetNextAvailablePressTrainHandoffIndex(), TrainIndex);
        ALBFactoryAGVInfrastructure* Handoff = nullptr;
        TestTrue(FString::Printf(TEXT("S01 handoff for Train %c places"), TCHAR('A' + TrainIndex)),
            Builder->PlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::PressTrainHandoff, TrainIndex,
                FTransform(FVector(-5000.0f + TrainIndex * 500.0f, 1000.0f, 0.0f)), Handoff, Reason));
        TestTrue(TEXT("Handoff retains exact A-D association"), Handoff
            && Handoff->GetTrainIndex() == TrainIndex
            && Handoff->GetInfrastructureId() == FName(*FString::Printf(TEXT("S01-HANDOFF-%c"), TCHAR('A' + TrainIndex))));
    }
    TestEqual(TEXT("All four train handoffs exhaust the player allocator"),
        Builder->GetNextAvailablePressTrainHandoffIndex(), INDEX_NONE);
    TestFalse(TEXT("Duplicate Train A handoff is rejected"),
        Builder->CanPlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::PressTrainHandoff, 0, Reason));

    ALBFactoryAGVInfrastructure* WaitPoint = nullptr;
    ALBFactoryAGVInfrastructure* RoutePoint = nullptr;
    ALBFactoryAGVInfrastructure* RouteSegment = nullptr;
    TestTrue(TEXT("Player can place an AGV waiting point"), Builder->PlaceAGVInfrastructure(
        ELBFactoryAGVInfrastructureType::WaitPoint, INDEX_NONE, FTransform(FVector(0, 2000, 0)), WaitPoint, Reason));
    TestTrue(TEXT("Player can place an AGV route waypoint"), Builder->PlaceAGVInfrastructure(
        ELBFactoryAGVInfrastructureType::RouteWaypoint, INDEX_NONE, FTransform(FVector(500, 2000, 0)), RoutePoint, Reason));
    TestTrue(TEXT("Player can place a continuous AGV route segment"), Builder->PlaceAGVInfrastructure(
        ELBFactoryAGVInfrastructureType::AGVRouteSegment, INDEX_NONE,
        FTransform(FVector(1000, 2000, 0)), RouteSegment, Reason));
    TestTrue(TEXT("Route paint follows the saved player waypoint without navigation collision"), RoutePoint
        && RoutePoint->HasFloorMarkingPresentation()
        && RoutePoint->GetFloorMarkingDimensionsCm().Z <= 1.01f);
    TestTrue(TEXT("AGV route has overview-readable paint without widening its navigation authority"),
        RouteSegment
        && RouteSegment->HasFloorMarkingPresentation()
        && FMath::IsNearlyEqual(RouteSegment->GetFloorMarkingDimensionsCm().Y, 30.0f, 0.01f)
        && RouteSegment->GetFloorMarkingDimensionsCm().Z <= 1.01f
        && FMath::IsNearlyEqual(RouteSegment->GetPlacementHalfExtentCm().Y, 115.0f, 0.01f));

    TArray<FLBFactoryAGVInfrastructureSaveState> Saved;
    TestTrue(TEXT("AGV infrastructure captures"), Builder->CaptureAGVInfrastructure(Saved));
    TestEqual(TEXT("All floor infrastructure, chargers, handoffs and routes are captured"), Saved.Num(), 14);
    TestTrue(TEXT("AGV infrastructure restores"), Builder->RestoreAGVInfrastructure(Saved, Reason));
    TArray<FLBFactoryAGVInfrastructureSaveState> RoundTrip;
    TestTrue(TEXT("Restored AGV infrastructure recaptures"), Builder->CaptureAGVInfrastructure(RoundTrip));
    TestEqual(TEXT("AGV infrastructure round-trip is exact"), RoundTrip.Num(), Saved.Num());

    return true;
}

#endif
