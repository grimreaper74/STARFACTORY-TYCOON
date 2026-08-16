#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryPlayerBuilderSubsystem.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBFactoryBuildMachine.h"
#include "LBOneFactoryAssemblyStarterLayout.h"
#include "LBOneFactoryAssemblyStarterPresentationActor.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryBodyWeldStarterPresentationActor.h"
#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryGameMode.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryPaintStarterPresentationActor.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "LBPressShopBuildAuthority.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryPlayerBuilderTestsPrivate
{
    template<typename ActorType>
    int32 CountLiveActors(UWorld* World)
    {
        int32 Count = 0;
        if (!World) return Count;
        for (TActorIterator<ActorType> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++Count;
        }
        return Count;
    }

    void ConfigureCanonicalAuthority(ALBPressShopBuildAuthority& Authority)
    {
        const FLBOneFactoryLayoutDefinition Layout =
            ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
        ULBOneFactoryLayoutLibrary::BuildExpectedPressAuthorityContract(Layout,
            Authority.BuildBays, Authority.ProtectedAreas,
            Authority.UtilitySpines, Authority.LogisticsSpines);
        Authority.StorageBays.Reset();
        Authority.SetActorTransform(FTransform::Identity);
        Authority.Tags.AddUnique(
            ALBOneFactoryBootstrap::GetPressBuildAuthorityTag());
        Authority.Tags.AddUnique(ALBOneFactoryBootstrap::GetNativeOnlyTag());
    }

    struct FReadyFixture
    {
        UWorld* World = nullptr;
        ALBOneFactoryBootstrap* Bootstrap = nullptr;
        ALBPressShopBuildAuthority* MapAuthority = nullptr;
        ALBOneFactoryGameMode* GameMode = nullptr;
        ULBOneFactoryPlayerBuilderSubsystem* Builder = nullptr;

        bool Create(const TCHAR* WorldName)
        {
            World = UWorld::CreateWorld(EWorldType::Game, false,
                FName(WorldName));
            Bootstrap = World
                ? World->SpawnActor<ALBOneFactoryBootstrap>() : nullptr;
            MapAuthority = World
                ? World->SpawnActor<ALBPressShopBuildAuthority>() : nullptr;
            if (!World || !Bootstrap || !MapAuthority) return false;
            ConfigureCanonicalAuthority(*MapAuthority);
            Bootstrap->DispatchBeginPlay();
            GameMode = World->SpawnActor<ALBOneFactoryGameMode>();
            if (!GameMode) return false;
            GameMode->DispatchBeginPlay();
            Builder = World->GetSubsystem<
                ULBOneFactoryPlayerBuilderSubsystem>();
            return Bootstrap->HasValidShell() && GameMode->HasValidRuntimeBackbone()
                && Builder;
        }

        void Destroy()
        {
            if (World) World->DestroyWorld(false);
            World = nullptr;
            Bootstrap = nullptr;
            MapAuthority = nullptr;
            GameMode = nullptr;
            Builder = nullptr;
        }
    };

    ALBOneFactoryPressStarterLayoutAuthority* FindLayoutAuthority(
        UWorld* World)
    {
        if (!World) return nullptr;
        for (TActorIterator<ALBOneFactoryPressStarterLayoutAuthority> It(World);
            It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
        }
        return nullptr;
    }

    ALBOneFactoryPressStarterPresentationActor* FindPresentation(UWorld* World)
    {
        if (!World) return nullptr;
        for (TActorIterator<ALBOneFactoryPressStarterPresentationActor> It(World);
            It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
        }
        return nullptr;
    }

    ALBOneFactoryAssemblyStarterLayoutAuthority* FindAssemblyAuthority(
        UWorld* World)
    {
        if (!World) return nullptr;
        for (TActorIterator<ALBOneFactoryAssemblyStarterLayoutAuthority>
            It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
        }
        return nullptr;
    }

    ALBOneFactoryAssemblyStarterPresentationActor* FindAssemblyPresentation(
        UWorld* World)
    {
        if (!World) return nullptr;
        for (TActorIterator<ALBOneFactoryAssemblyStarterPresentationActor>
            It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
        }
        return nullptr;
    }

    ALBOneFactoryPaintStarterLayoutAuthority* FindPaintAuthority(
        UWorld* World)
    {
        if (!World) return nullptr;
        for (TActorIterator<ALBOneFactoryPaintStarterLayoutAuthority>
            It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
        }
        return nullptr;
    }

    ALBOneFactoryBodyWeldStarterLayoutAuthority* FindBodyWeldAuthority(
        UWorld* World)
    {
        if (!World) return nullptr;
        for (TActorIterator<ALBOneFactoryBodyWeldStarterLayoutAuthority>
            It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
        }
        return nullptr;
    }

    ALBOneFactoryBodyWeldStarterPresentationActor*
        FindBodyWeldPresentation(UWorld* World)
    {
        if (!World) return nullptr;
        for (TActorIterator<ALBOneFactoryBodyWeldStarterPresentationActor>
            It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
        }
        return nullptr;
    }

    ALBOneFactoryPaintStarterPresentationActor* FindPaintPresentation(
        UWorld* World)
    {
        if (!World) return nullptr;
        for (TActorIterator<ALBOneFactoryPaintStarterPresentationActor>
            It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
        }
        return nullptr;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryNativeUMGReadyAndAtomicRollbackTest,
    "LineBoss.OneFactory.PlayerBuilder.NativeUMGReadyGateAndAtomicCreationRollback",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryNativeUMGReadyAndAtomicRollbackTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* UnreadyWorld = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPlayerBuilderUnreadyTest"));
    ALBOneFactoryBootstrap* UnreadyBootstrap = UnreadyWorld
        ? UnreadyWorld->SpawnActor<ALBOneFactoryBootstrap>() : nullptr;
    ULBOneFactoryPlayerBuilderSubsystem* UnreadyBuilder = UnreadyWorld
        ? UnreadyWorld->GetSubsystem<ULBOneFactoryPlayerBuilderSubsystem>()
        : nullptr;
    TestNotNull(TEXT("Unready fixture bootstrap exists"), UnreadyBootstrap);
    TestNotNull(TEXT("Native OneFactory builder subsystem exists"),
        UnreadyBuilder);
    if (UnreadyBuilder)
    {
        TestTrue(TEXT("Bootstrap identity opts into the OneFactory UMG seam"),
            UnreadyBuilder->IsOneFactoryBuilderWorld());
        const TArray<FLBOneFactoryBuilderUMGAction> Actions =
            UnreadyBuilder->GetUMGActions();
        TestEqual(TEXT("The native UMG seam has five stable actions"),
            Actions.Num(), ULBOneFactoryPlayerBuilderSubsystem::UMGActionCount);
        TestEqual(TEXT("First action is New Factory"), Actions[0].Title,
            FString(TEXT("New Factory")));
        TestFalse(TEXT("New Factory stays locked before bootstrap Ready"),
            Actions[0].bEnabled);
        TestTrue(TEXT("Ready rejection is visible in UMG details"),
            Actions[0].Detail.Contains(TEXT("READY")));
    }
    if (UnreadyWorld) UnreadyWorld->DestroyWorld(false);

    LBOneFactoryPlayerBuilderTestsPrivate::FReadyFixture Fixture;
    if (!TestTrue(TEXT("Ready OneFactory fixture validates"),
            Fixture.Create(TEXT("LBOneFactoryPlayerBuilderRollbackTest"))))
    {
        Fixture.Destroy();
        return false;
    }
    Fixture.Builder->SetForcePresentationFailureForTests(true);
    FString Reason;
    TestFalse(TEXT("Forced presentation failure rejects New Factory"),
        Fixture.Builder->CreateNewFactory(Reason));
    TestTrue(TEXT("The failure reason exposes the atomic rollback"),
        Reason.Contains(TEXT("ROLLED BACK DATA AND PRESENTATION ATOMICALLY")));
    TestEqual(TEXT("Failed materialisation leaves no data authority"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryPressStarterLayoutAuthority>(Fixture.World), 0);
    TestEqual(TEXT("Failed materialisation leaves no presentation actor"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryPressStarterPresentationActor>(Fixture.World), 0);
    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryProgrammeMoveCommissionWIPTest,
    "LineBoss.OneFactory.PlayerBuilder.ProgrammeMoveCommissionAndWIPReasons",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryProgrammeMoveCommissionWIPTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    LBOneFactoryPlayerBuilderTestsPrivate::FReadyFixture Fixture;
    if (!TestTrue(TEXT("Ready editing fixture validates"),
            Fixture.Create(TEXT("LBOneFactoryPlayerBuilderEditingTest"))))
    {
        Fixture.Destroy();
        return false;
    }
    FString Reason;
    TestTrue(TEXT("New Factory atomically creates data and presentation"),
        Fixture.Builder->CreateNewFactory(Reason));
    ALBOneFactoryPressStarterLayoutAuthority* Authority =
        LBOneFactoryPlayerBuilderTestsPrivate::FindLayoutAuthority(Fixture.World);
    ALBOneFactoryPressStarterPresentationActor* Presentation =
        LBOneFactoryPlayerBuilderTestsPrivate::FindPresentation(Fixture.World);
    if (!TestNotNull(TEXT("Canonical Press data authority exists"), Authority)
        || !TestNotNull(TEXT("Native Press presentation exists"), Presentation))
    {
        Fixture.Destroy();
        return false;
    }
    TestFalse(TEXT("New Factory does not silently commission"),
        Authority->IsCommissioned());
    TestEqual(TEXT("The useful configurable train is selected first"),
        Fixture.Builder->GetSelectedTargetId(),
        LBOneFactoryPressStarterIds::PressTrain());
    TestTrue(TEXT("Summary exposes the exact native provenance pass"),
        Fixture.Builder->GetUMGSummary().Contains(TEXT("NATIVE-ONLY PASS")));

    const FLBOneFactoryPressStarterLayoutState BeforeProgramme =
        Authority->CaptureLayout();
    TestTrue(TEXT("Programme action is enabled for the selected train"),
        Fixture.Builder->GetUMGActions()[2].bEnabled);
    TestTrue(TEXT("UMG programme action commits"),
        Fixture.Builder->ExecuteUMGAction(2, Reason));
    const FLBOneFactoryPressStarterLayoutState AfterProgramme =
        Authority->CaptureLayout();
    TestEqual(TEXT("Programme transaction advances one data revision"),
        AfterProgramme.Revision, BeforeProgramme.Revision + 1);
    TestEqual(TEXT("Presentation advances with the same revision"),
        Presentation->GetConfiguredLayoutRevision(), AfterProgramme.Revision);
    FName CoherentPanel = NAME_None;
    bool bAllRecipeResponsibilitiesMatch = true;
    for (const FLBOneFactoryPressStarterStationState& Station :
        AfterProgramme.Stations)
    {
        if (Station.PanelTypeId.IsNone()) continue;
        if (CoherentPanel.IsNone()) CoherentPanel = Station.PanelTypeId;
        else bAllRecipeResponsibilitiesMatch &= Station.PanelTypeId == CoherentPanel;
    }
    TestTrue(TEXT("All recipe-bound responsibilities change together"),
        bAllRecipeResponsibilitiesMatch
        && CoherentPanel != BeforeProgramme.Stations[4].PanelTypeId);

    const FLBOneFactoryPressStarterStationState* TrainBeforeMove =
        AfterProgramme.Stations.FindByPredicate([](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.StationId == LBOneFactoryPressStarterIds::PressTrain();
        });
    const FVector BeforeMoveLocation = TrainBeforeMove
        ? TrainBeforeMove->WorldTransform.GetLocation() : FVector::ZeroVector;
    TestTrue(TEXT("UMG move action commits"),
        Fixture.Builder->ExecuteUMGAction(3, Reason));
    const FLBOneFactoryPressStarterLayoutState AfterMove =
        Authority->CaptureLayout();
    const FLBOneFactoryPressStarterStationState* TrainAfterMove =
        AfterMove.Stations.FindByPredicate([](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.StationId == LBOneFactoryPressStarterIds::PressTrain();
        });
    TestTrue(TEXT("Selected station moves exactly one metre east"),
        TrainBeforeMove && TrainAfterMove
        && TrainAfterMove->WorldTransform.GetLocation().Equals(
            BeforeMoveLocation + FVector(100.0f, 0.0f, 0.0f), 0.01f));
    TestEqual(TEXT("Moved presentation stays on the data revision"),
        Presentation->GetConfiguredLayoutRevision(), AfterMove.Revision);

    TestTrue(TEXT("Lifecycle action commissions the coherent pair"),
        Fixture.Builder->ExecuteUMGAction(0, Reason));
    TestTrue(TEXT("Authority is explicitly commissioned"),
        Authority->IsCommissioned());
    TestTrue(TEXT("Commission reason remains visible"),
        Fixture.Builder->GetLastActionReason().Contains(TEXT("COMMISSIONED")));

    FLBOneFactoryPressStarterLayoutState WithWIP = Authority->CaptureLayout();
    FLBOneFactoryPressStarterStationState* WIPStation =
        WithWIP.Stations.FindByPredicate([](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.StationId == LBOneFactoryPressStarterIds::PressTrain();
        });
    if (WIPStation) WIPStation->ActiveOrReservedUnitIds.Add(TEXT("LB.WIP.TEST.001"));
    ++WithWIP.Revision;
    TestTrue(TEXT("Test WIP snapshot restores coherently"),
        WIPStation && Authority->RestoreLayout(WithWIP, Reason));
    TestTrue(TEXT("Presentation follows the coherent WIP data revision"),
        Presentation->ConfigureFromLayout(Authority->CaptureLayout(), Reason));
    const TArray<FLBOneFactoryBuilderUMGAction> WIPActions =
        Fixture.Builder->GetUMGActions();
    TestFalse(TEXT("WIP blocks programme changes"), WIPActions[2].bEnabled);
    TestTrue(TEXT("Programme card exposes its WIP rejection reason"),
        WIPActions[2].Detail.Contains(TEXT("WIP")));
    TestFalse(TEXT("WIP blocks station movement"), WIPActions[3].bEnabled);
    TestTrue(TEXT("Move card exposes its WIP rejection reason"),
        WIPActions[3].Detail.Contains(TEXT("WIP")));
    TestFalse(TEXT("Canonical station remove/disconnect remains protected"),
        WIPActions[4].bEnabled);
    TestTrue(TEXT("Protected edit reason names both package constraints"),
        WIPActions[4].Detail.Contains(TEXT("CANNOT BE REMOVED"))
        && WIPActions[4].Detail.Contains(TEXT("CANNOT BE DISCONNECTED")));

    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryExistingTransactionalMachineEditRoutingTest,
    "LineBoss.OneFactory.PlayerBuilder.ExistingTransactionalMachineDisconnectAndRemove",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryExistingTransactionalMachineEditRoutingTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    LBOneFactoryPlayerBuilderTestsPrivate::FReadyFixture Fixture;
    if (!TestTrue(TEXT("Ready transaction fixture validates"),
            Fixture.Create(TEXT("LBOneFactoryPlayerBuilderTransactionTest"))))
    {
        Fixture.Destroy();
        return false;
    }
    FString Reason;
    if (!TestTrue(TEXT("Canonical starter exists before player-machine editing"),
            Fixture.Builder->CreateNewFactory(Reason)))
    {
        Fixture.Destroy();
        return false;
    }
    ALBFactoryBuildMachine* PlayerMachine =
        Fixture.World->SpawnActor<ALBFactoryBuildMachine>();
    if (!TestNotNull(TEXT("Player-added transaction fixture machine exists"),
            PlayerMachine)
        || !TestTrue(TEXT("Player-added fixture machine has a stable identity"),
            PlayerMachine && PlayerMachine->Configure(TEXT("OF_PLAYER_INSPECTION_001"),
                ELBFactoryBuildMachineType::InspectionCell)))
    {
        Fixture.Destroy();
        return false;
    }

    for (int32 Index = 0;
        Index < 10 && Fixture.Builder->GetSelectedTargetKind()
            != ELBOneFactoryBuilderTargetKind::PlayerBuildMachine;
        ++Index)
    {
        Fixture.Builder->SelectNextTarget(Reason);
    }
    TestEqual(TEXT("UMG selection reaches the player-built machine"),
        Fixture.Builder->GetSelectedTargetKind(),
        ELBOneFactoryBuilderTargetKind::PlayerBuildMachine);
    TestEqual(TEXT("Selected player machine identity is stable"),
        Fixture.Builder->GetSelectedTargetId(),
        FName(TEXT("OF_PLAYER_INSPECTION_001")));

    TArray<FLBOneFactoryBuilderUMGAction> Actions =
        Fixture.Builder->GetUMGActions();
    TestTrue(TEXT("Existing CanEditMachine gate admits idle disconnect"),
        Actions[3].bEnabled);
    TestTrue(TEXT("Disconnect UMG action uses the existing connection authority"),
        Fixture.Builder->ExecuteUMGAction(3, Reason));
    TestTrue(TEXT("Idempotent no-link result is reported honestly"),
        Reason.Contains(TEXT("ALREADY DISCONNECTED")));

    Actions = Fixture.Builder->GetUMGActions();
    TestTrue(TEXT("Existing CanEditMachine gate admits idle removal"),
        Actions[4].bEnabled);
    TestTrue(TEXT("Remove UMG action uses the existing builder transaction"),
        Fixture.Builder->ExecuteUMGAction(4, Reason));
    TestEqual(TEXT("Removed player machine is no longer live"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBFactoryBuildMachine>(Fixture.World), 0);
    TestEqual(TEXT("Selection clears after transactional removal"),
        Fixture.Builder->GetSelectedTargetKind(),
        ELBOneFactoryBuilderTargetKind::None);

    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryBodyWeldLifecycleRobotProgrammeRollbackMoveWIPAndRemovalTest,
    "LineBoss.OneFactory.PlayerBuilder.BodyWeldLifecycleRobotProgrammeRollbackMoveWIPAndRemoval",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryBodyWeldLifecycleRobotProgrammeRollbackMoveWIPAndRemovalTest::
    RunTest(const FString& Parameters)
{
    (void)Parameters;
    LBOneFactoryPlayerBuilderTestsPrivate::FReadyFixture Fixture;
    if (!TestTrue(TEXT("Ready Body/Weld rollback fixture validates"),
            Fixture.Create(TEXT("LBOneFactoryBodyWeldBuilderRollbackTest"))))
    {
        Fixture.Destroy();
        return false;
    }
    FString Reason;
    if (!TestTrue(TEXT("Press exists before Body/Weld"),
            Fixture.Builder->CreateNewFactory(Reason))
        || !TestTrue(TEXT("Press commissions before Body/Weld"),
            Fixture.Builder->CommissionPressStarter(Reason)))
    {
        Fixture.Destroy();
        return false;
    }
    TestEqual(TEXT("Native lifecycle exposes Body/Weld after Press"),
        Fixture.Builder->GetUMGActions()[0].Title,
        FString(TEXT("Build Body/Weld starter")));
    Fixture.Builder->SetForceBodyWeldPresentationFailureForTests(true);
    TestFalse(TEXT("Forced Body/Weld art failure rejects construction"),
        Fixture.Builder->CreateBodyWeldStarter(Reason));
    TestTrue(TEXT("Body/Weld creation failure exposes atomic rollback"),
        Reason.Contains(TEXT(
            "ROLLED BACK DATA AND PRESENTATION ATOMICALLY")));
    TestEqual(TEXT("Failed Body/Weld creation leaves no data authority"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryBodyWeldStarterLayoutAuthority>(Fixture.World), 0);
    TestEqual(TEXT("Failed Body/Weld creation leaves no presentation"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryBodyWeldStarterPresentationActor>(Fixture.World), 0);

    Fixture.Destroy();
    if (!TestTrue(TEXT("Fresh Body/Weld lifecycle fixture validates"),
            Fixture.Create(TEXT("LBOneFactoryBodyWeldBuilderLifecycleTest")))
        || !TestTrue(TEXT("Fresh Press starter exists"),
            Fixture.Builder->CreateNewFactory(Reason))
        || !TestTrue(TEXT("Fresh Press starter commissions"),
            Fixture.Builder->CommissionPressStarter(Reason)))
    {
        Fixture.Destroy();
        return false;
    }
    Fixture.Builder->SetForceBodyWeldPresentationFailureForTests(false);
    TestTrue(TEXT("UMG lifecycle atomically creates Body/Weld pair"),
        Fixture.Builder->ExecuteUMGAction(0, Reason));
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority =
        LBOneFactoryPlayerBuilderTestsPrivate::FindBodyWeldAuthority(
            Fixture.World);
    ALBOneFactoryBodyWeldStarterPresentationActor* Presentation =
        LBOneFactoryPlayerBuilderTestsPrivate::FindBodyWeldPresentation(
            Fixture.World);
    if (!TestNotNull(TEXT("Body/Weld layout authority exists"), Authority)
        || !TestNotNull(TEXT("Body/Weld native presentation exists"),
            Presentation))
    {
        Fixture.Destroy();
        return false;
    }
    TestEqual(TEXT("Exactly one Body/Weld authority is live"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryBodyWeldStarterLayoutAuthority>(Fixture.World), 1);
    TestEqual(TEXT("Exactly one Body/Weld presentation is live"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryBodyWeldStarterPresentationActor>(Fixture.World), 1);
    TestFalse(TEXT("A second Body/Weld pair is refused"),
        Fixture.Builder->CreateBodyWeldStarter(Reason));
    TestFalse(TEXT("Body/Weld awaits explicit commission"),
        Authority->IsCommissioned());
    TestEqual(TEXT("Useful front-underbody position is selected"),
        Fixture.Builder->GetSelectedTargetId(),
        LBOneFactoryBodyWeldStarterIds::Station(2));
    TestEqual(TEXT("Front-underbody programme is initially chosen"),
        Fixture.Builder->GetSelectedBodyWeldProgramme(),
        ELBOneFactoryBodyWeldProgramme::FrontUnderbodyGeometry);
    TestEqual(TEXT("Body/Weld presentation commits all 24 HISM batches"),
        Presentation->GetVisualBatchCount(), 24);
    TestEqual(TEXT("Body/Weld presentation commits 469 native items"),
        Presentation->GetVisibleInstanceCount(), 469);
    TestFalse(TEXT("Body/Weld presentation never owns process WIP"),
        Presentation->RepresentsProcessWIP());

    const FLBOneFactoryBodyWeldLayoutState BeforeRobotDuties =
        Authority->CaptureLayout();
    TestTrue(TEXT("UMG applies programme plus mirrored robot duties"),
        Fixture.Builder->ExecuteUMGAction(3, Reason));
    const FLBOneFactoryBodyWeldLayoutState AfterRobotDuties =
        Authority->CaptureLayout();
    const FLBOneFactoryBodyWeldStationState& Position2AfterDuties =
        AfterRobotDuties.Stations[1];
    TestEqual(TEXT("Robot-duty transaction advances one revision"),
        AfterRobotDuties.Revision, BeforeRobotDuties.Revision + 1);
    TestEqual(TEXT("Left robot duty swaps to spot welding"),
        Position2AfterDuties.LeftRobotRole,
        ELBOneFactoryBodyWeldRobotRole::SpotWelding);
    TestEqual(TEXT("Right robot retains required geometry duty"),
        Position2AfterDuties.RightRobotRole,
        ELBOneFactoryBodyWeldRobotRole::GeometryClamp);
    const TArray<FLBOneFactoryBodyWeldPresentationItem> LeftRobotItems =
        Presentation->GetConfiguredRobotItems(
            LBOneFactoryBodyWeldStarterIds::Station(2),
            ELBOneFactoryBodyWeldRobotSide::Left);
    const TArray<FLBOneFactoryBodyWeldPresentationItem> RightRobotItems =
        Presentation->GetConfiguredRobotItems(
            LBOneFactoryBodyWeldStarterIds::Station(2),
            ELBOneFactoryBodyWeldRobotSide::Right);
    TestTrue(TEXT("Presentation rebuild exposes both complete robot sides"),
        !LeftRobotItems.IsEmpty() && !RightRobotItems.IsEmpty());
    TestTrue(TEXT("Presented robot duties follow the committed snapshot"),
        LeftRobotItems.ContainsByPredicate([](
            const FLBOneFactoryBodyWeldPresentationItem& Item)
        {
            return Item.RobotRole ==
                ELBOneFactoryBodyWeldRobotRole::SpotWelding;
        })
        && RightRobotItems.ContainsByPredicate([](
            const FLBOneFactoryBodyWeldPresentationItem& Item)
        {
            return Item.RobotRole ==
                ELBOneFactoryBodyWeldRobotRole::GeometryClamp;
        }));

    TestTrue(TEXT("UMG cycles to the next order-safe programme"),
        Fixture.Builder->ExecuteUMGAction(2, Reason));
    TestEqual(TEXT("Rear-underbody geometry is the next safe programme"),
        Fixture.Builder->GetSelectedBodyWeldProgramme(),
        ELBOneFactoryBodyWeldProgramme::RearUnderbodyGeometry);
    const int32 BeforeProgrammeRevision = Authority->CaptureLayout().Revision;
    TestTrue(TEXT("UMG moves programme and robot duties atomically"),
        Fixture.Builder->ExecuteUMGAction(3, Reason));
    const FLBOneFactoryBodyWeldLayoutState AfterProgramme =
        Authority->CaptureLayout();
    TestEqual(TEXT("Programme assignment advances one revision"),
        AfterProgramme.Revision, BeforeProgrammeRevision + 1);
    TestTrue(TEXT("Rear-underbody programme moved to selected position"),
        AfterProgramme.Stations[1].AssignedProgrammes.Contains(
            ELBOneFactoryBodyWeldProgramme::RearUnderbodyGeometry)
        && !AfterProgramme.Stations[2].AssignedProgrammes.Contains(
            ELBOneFactoryBodyWeldProgramme::RearUnderbodyGeometry));
    const TArray<FLBOneFactoryBodyWeldPresentationItem> RearItems =
        Presentation->GetConfiguredItemsForProgramme(
            ELBOneFactoryBodyWeldProgramme::RearUnderbodyGeometry);
    TestTrue(TEXT("Programme fixture follows the selected position"),
        RearItems.ContainsByPredicate([](
            const FLBOneFactoryBodyWeldPresentationItem& Item)
        {
            return Item.StationId ==
                LBOneFactoryBodyWeldStarterIds::Station(2);
        }));

    const FLBOneFactoryBodyWeldLayoutState BeforeForcedRollback =
        Authority->CaptureLayout();
    Fixture.Builder->SetForceBodyWeldPresentationFailureForTests(true);
    TestFalse(TEXT("Forced Body/Weld sync failure rejects configuration"),
        Fixture.Builder->ExecuteUMGAction(3, Reason));
    Fixture.Builder->SetForceBodyWeldPresentationFailureForTests(false);
    const FLBOneFactoryBodyWeldLayoutState AfterForcedRollback =
        Authority->CaptureLayout();
    TestEqual(TEXT("Failed sync restores exact Body/Weld data revision"),
        AfterForcedRollback.Revision, BeforeForcedRollback.Revision);
    TestEqual(TEXT("Failed sync restores exact presentation revision"),
        Presentation->GetConfiguredLayoutRevision(),
        BeforeForcedRollback.Revision);
    TestTrue(TEXT("Body/Weld rollback proves both restores"),
        Reason.Contains(TEXT("ROLLED BACK"))
        && Reason.Contains(TEXT("DATA RESTORE: PASS"))
        && Reason.Contains(TEXT("PRESENTATION RESTORE: PASS")));

    const FVector BeforeMove = AfterForcedRollback.Stations[1]
        .WorldTransform.GetLocation();
    TestTrue(TEXT("UMG moves selected Body/Weld position atomically"),
        Fixture.Builder->ExecuteUMGAction(4, Reason));
    const FLBOneFactoryBodyWeldLayoutState Moved =
        Authority->CaptureLayout();
    TestTrue(TEXT("Body/Weld position moves exactly one metre east"),
        Moved.Stations[1].WorldTransform.GetLocation().Equals(
            BeforeMove + FVector(100.0f, 0.0f, 0.0f), 0.01f));
    TestEqual(TEXT("Moved Body/Weld presentation follows data revision"),
        Presentation->GetConfiguredLayoutRevision(), Moved.Revision);

    FLBOneFactoryBodyWeldLayoutState WithWIP = Moved;
    WithWIP.Stations[1].ActiveOrReservedUnitIds.Add(
        TEXT("LB.BODYWELD.WIP.TEST.001"));
    TestTrue(TEXT("Committed Body/Weld state accepts coherent WIP"),
        Authority->RestoreLayout(WithWIP, Reason));
    TestTrue(TEXT("Presentation rebuilds only from committed layout"),
        Presentation->ConfigureFromLayout(
            Authority->CaptureLayout(), Reason));
    const TArray<FLBOneFactoryBuilderUMGAction> WIPActions =
        Fixture.Builder->GetUMGActions();
    TestFalse(TEXT("Body/Weld WIP blocks explicit commission"),
        WIPActions[0].bEnabled);
    TestFalse(TEXT("Body/Weld WIP blocks programme selection"),
        WIPActions[2].bEnabled);
    TestFalse(TEXT("Body/Weld WIP blocks programme and robot duties"),
        WIPActions[3].bEnabled);
    TestFalse(TEXT("Body/Weld WIP blocks movement"),
        WIPActions[4].bEnabled);
    TestFalse(TEXT("Body/Weld WIP blocks complete-pair removal"),
        Fixture.Builder->RemoveBodyWeldStarter(Reason));
    TestTrue(TEXT("All Body/Weld cards expose WIP rejection"),
        WIPActions[0].Detail.Contains(TEXT("WIP"))
        && WIPActions[2].Detail.Contains(TEXT("WIP"))
        && WIPActions[3].Detail.Contains(TEXT("WIP"))
        && WIPActions[4].Detail.Contains(TEXT("WIP"))
        && Reason.Contains(TEXT("WIP")));

    TestTrue(TEXT("Cleared Body/Weld snapshot restores atomically"),
        Authority->RestoreLayout(Moved, Reason));
    TestTrue(TEXT("Presentation follows cleared committed snapshot"),
        Presentation->ConfigureFromLayout(Moved, Reason));
    TestTrue(TEXT("Lifecycle explicitly commissions Body/Weld"),
        Fixture.Builder->ExecuteUMGAction(0, Reason));
    TestTrue(TEXT("Body/Weld authority is commissioned"),
        Authority->IsCommissioned());
    TestTrue(TEXT("Summary exposes commissioned Body/Weld provenance"),
        Fixture.Builder->GetUMGSummary().Contains(
            TEXT("BODY/WELD: COMMISSIONED"))
        && Fixture.Builder->GetUMGSummary().Contains(
            TEXT("NATIVE-ONLY PASS")));
    TestEqual(TEXT("Paint follows commissioned Body/Weld in lifecycle"),
        Fixture.Builder->GetUMGActions()[0].Title,
        FString(TEXT("Build Paint starter")));
    TestTrue(TEXT("Idle complete Body/Weld pair removes atomically"),
        Fixture.Builder->RemoveBodyWeldStarter(Reason));
    TestEqual(TEXT("Body/Weld authority is destroyed"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryBodyWeldStarterLayoutAuthority>(Fixture.World), 0);
    TestEqual(TEXT("Body/Weld presentation is destroyed"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryBodyWeldStarterPresentationActor>(Fixture.World), 0);
    TestEqual(TEXT("Lifecycle returns to Body/Weld construction"),
        Fixture.Builder->GetUMGActions()[0].Title,
        FString(TEXT("Build Body/Weld starter")));

    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryAssemblyLifecycleAssignmentRollbackAndWIPTest,
    "LineBoss.OneFactory.PlayerBuilder.AssemblyLifecycleAssignmentRollbackAndWIP",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryAssemblyLifecycleAssignmentRollbackAndWIPTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    LBOneFactoryPlayerBuilderTestsPrivate::FReadyFixture Fixture;
    if (!TestTrue(TEXT("Ready Assembly builder fixture validates"),
            Fixture.Create(TEXT("LBOneFactoryAssemblyBuilderTest"))))
    {
        Fixture.Destroy();
        return false;
    }
    FString Reason;
    if (!TestTrue(TEXT("Press starter exists before Assembly"),
            Fixture.Builder->CreateNewFactory(Reason))
        || !TestTrue(TEXT("Press commissions before Assembly construction"),
            Fixture.Builder->CommissionPressStarter(Reason))
        || !TestTrue(TEXT("Body/Weld exists before Assembly"),
            Fixture.Builder->CreateBodyWeldStarter(Reason))
        || !TestTrue(TEXT("Body/Weld commissions before Assembly"),
            Fixture.Builder->CommissionBodyWeldStarter(Reason))
        || !TestTrue(TEXT("Paint exists before Assembly"),
            Fixture.Builder->CreatePaintStarter(Reason))
        || !TestTrue(TEXT("Paint commissions before Assembly"),
            Fixture.Builder->CommissionPaintStarter(Reason)))
    {
        Fixture.Destroy();
        return false;
    }
    TestEqual(TEXT("Native UMG exposes Assembly as the next lifecycle step"),
        Fixture.Builder->GetUMGActions()[0].Title,
        FString(TEXT("Build Assembly starter")));

    Fixture.Builder->SetForceAssemblyPresentationFailureForTests(true);
    TestFalse(TEXT("Forced Assembly art failure rejects construction"),
        Fixture.Builder->CreateAssemblyStarter(Reason));
    TestTrue(TEXT("Assembly failure reason exposes atomic rollback"),
        Reason.Contains(TEXT(
            "ROLLED BACK DATA AND PRESENTATION ATOMICALLY")));
    TestEqual(TEXT("Failed Assembly construction leaves no data actor"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryAssemblyStarterLayoutAuthority>(Fixture.World), 0);
    TestEqual(TEXT("Failed Assembly construction leaves no presentation"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryAssemblyStarterPresentationActor>(Fixture.World), 0);

    Fixture.Destroy();
    if (!TestTrue(TEXT("Fresh lifecycle fixture validates after rollback proof"),
            Fixture.Create(TEXT("LBOneFactoryAssemblyLifecycleTest")))
        || !TestTrue(TEXT("Fresh lifecycle Press starter exists"),
            Fixture.Builder->CreateNewFactory(Reason))
        || !TestTrue(TEXT("Fresh lifecycle Press starter commissions"),
            Fixture.Builder->CommissionPressStarter(Reason))
        || !TestTrue(TEXT("Fresh lifecycle Body/Weld starter exists"),
            Fixture.Builder->CreateBodyWeldStarter(Reason))
        || !TestTrue(TEXT("Fresh lifecycle Body/Weld commissions"),
            Fixture.Builder->CommissionBodyWeldStarter(Reason))
        || !TestTrue(TEXT("Fresh lifecycle Paint starter exists"),
            Fixture.Builder->CreatePaintStarter(Reason))
        || !TestTrue(TEXT("Fresh lifecycle Paint commissions"),
            Fixture.Builder->CommissionPaintStarter(Reason)))
    {
        Fixture.Destroy();
        return false;
    }
    Fixture.Builder->SetForceAssemblyPresentationFailureForTests(false);
    TestTrue(TEXT("UMG lifecycle atomically creates Assembly pair"),
        Fixture.Builder->ExecuteUMGAction(0, Reason));
    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority =
        LBOneFactoryPlayerBuilderTestsPrivate::FindAssemblyAuthority(
            Fixture.World);
    ALBOneFactoryAssemblyStarterPresentationActor* Presentation =
        LBOneFactoryPlayerBuilderTestsPrivate::FindAssemblyPresentation(
            Fixture.World);
    if (!TestNotNull(TEXT("Assembly data authority exists"), Authority)
        || !TestNotNull(TEXT("Assembly native presentation exists"),
            Presentation))
    {
        Fixture.Destroy();
        return false;
    }
    TestFalse(TEXT("Assembly construction awaits explicit commission"),
        Authority->IsCommissioned());
    TestEqual(TEXT("Heavy marriage position is initially selected"),
        Fixture.Builder->GetSelectedTargetId(),
        LBOneFactoryAssemblyStarterIds::Station(12));
    TestEqual(TEXT("Assembly presentation is exact and complete"),
        Presentation->GetVisibleInstanceCount(), 95);

    TestTrue(TEXT("UMG cycles to the next compatible operation"),
        Fixture.Builder->ExecuteUMGAction(2, Reason));
    TestEqual(TEXT("Position 12 next compatible work is underbody torque"),
        Fixture.Builder->GetSelectedAssemblyOperation(),
        ELBOneFactoryAssemblyOperation::UnderbodyTorque);
    const int32 BeforeAssignmentRevision =
        Authority->CaptureLayout().Revision;
    TestTrue(TEXT("UMG assigns selected operation atomically"),
        Fixture.Builder->ExecuteUMGAction(3, Reason));
    TestEqual(TEXT("Assignment advances exactly one data revision"),
        Authority->CaptureLayout().Revision, BeforeAssignmentRevision + 1);
    const TArray<FLBOneFactoryAssemblyPresentationItem> UnderbodyItems =
        Presentation->GetConfiguredItemsForOperation(
            ELBOneFactoryAssemblyOperation::UnderbodyTorque);
    TestEqual(TEXT("Reassigned operation keeps one visual fixture"),
        UnderbodyItems.Num(), 1);
    if (UnderbodyItems.Num() == 1)
    {
        TestEqual(TEXT("Visual fixture follows assignment to position 12"),
            UnderbodyItems[0].StationId,
            LBOneFactoryAssemblyStarterIds::Station(12));
    }

    TestTrue(TEXT("UMG cycles to another compatible torque operation"),
        Fixture.Builder->ExecuteUMGAction(2, Reason));
    const FLBOneFactoryAssemblyLayoutState BeforeForcedRollback =
        Authority->CaptureLayout();
    Fixture.Builder->SetForceAssemblyPresentationFailureForTests(true);
    TestFalse(TEXT("Forced sync failure rejects an Assembly assignment"),
        Fixture.Builder->ExecuteUMGAction(3, Reason));
    Fixture.Builder->SetForceAssemblyPresentationFailureForTests(false);
    const FLBOneFactoryAssemblyLayoutState AfterForcedRollback =
        Authority->CaptureLayout();
    TestEqual(TEXT("Failed sync restores the exact data revision"),
        AfterForcedRollback.Revision, BeforeForcedRollback.Revision);
    TestEqual(TEXT("Failed sync restores the exact presentation revision"),
        Presentation->GetConfiguredLayoutRevision(),
        BeforeForcedRollback.Revision);
    TestTrue(TEXT("Rollback reason remains visible"),
        Reason.Contains(TEXT("ROLLED BACK"))
        && Reason.Contains(TEXT("DATA RESTORE: PASS"))
        && Reason.Contains(TEXT("PRESENTATION RESTORE: PASS")));

    const FVector BeforeMove = BeforeForcedRollback.Stations[11]
        .WorldTransform.GetLocation();
    TestTrue(TEXT("UMG moves selected Assembly position atomically"),
        Fixture.Builder->ExecuteUMGAction(4, Reason));
    TestTrue(TEXT("Assembly position moves exactly one metre east"),
        Authority->CaptureLayout().Stations[11].WorldTransform.GetLocation()
            .Equals(BeforeMove + FVector(100.0f, 0.0f, 0.0f), 0.01f));
    TestEqual(TEXT("Moved presentation follows the data revision"),
        Presentation->GetConfiguredLayoutRevision(),
        Authority->CaptureLayout().Revision);

    TestTrue(TEXT("Lifecycle action commissions Assembly explicitly"),
        Fixture.Builder->ExecuteUMGAction(0, Reason));
    TestTrue(TEXT("Assembly authority is commissioned"),
        Authority->IsCommissioned());
    TestTrue(TEXT("Summary exposes both native provenance passes"),
        Fixture.Builder->GetUMGSummary().Contains(TEXT("ASSEMBLY: COMMISSIONED"))
        && Fixture.Builder->GetUMGSummary().Contains(TEXT("NATIVE-ONLY PASS")));

    FLBOneFactoryAssemblyLayoutState WithWIP = Authority->CaptureLayout();
    WithWIP.Stations[11].ActiveOrReservedUnitIds.Add(
        TEXT("LB.ASSEMBLY.WIP.TEST.001"));
    TestTrue(TEXT("Coherent Assembly WIP snapshot restores"),
        Authority->RestoreLayout(WithWIP, Reason));
    TestTrue(TEXT("Presentation follows coherent WIP-bearing revision"),
        Presentation->ConfigureFromLayout(
            Authority->CaptureLayout(), Reason));
    const TArray<FLBOneFactoryBuilderUMGAction> WIPActions =
        Fixture.Builder->GetUMGActions();
    TestFalse(TEXT("WIP blocks operation selection"),
        WIPActions[2].bEnabled);
    TestFalse(TEXT("WIP blocks operation assignment"),
        WIPActions[3].bEnabled);
    TestFalse(TEXT("WIP blocks position movement"),
        WIPActions[4].bEnabled);
    TestTrue(TEXT("Every blocked card exposes its WIP reason"),
        WIPActions[2].Detail.Contains(TEXT("WIP"))
        && WIPActions[3].Detail.Contains(TEXT("WIP"))
        && WIPActions[4].Detail.Contains(TEXT("WIP")));

    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryPaintLifecycleProgrammeRollbackMoveAndWIPTest,
    "LineBoss.OneFactory.PlayerBuilder.PaintLifecycleProgrammeRollbackMoveAndWIP",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPaintLifecycleProgrammeRollbackMoveAndWIPTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    LBOneFactoryPlayerBuilderTestsPrivate::FReadyFixture Fixture;
    if (!TestTrue(TEXT("Ready Paint rollback fixture validates"),
            Fixture.Create(TEXT("LBOneFactoryPaintBuilderRollbackTest"))))
    {
        Fixture.Destroy();
        return false;
    }
    FString Reason;
    if (!TestTrue(TEXT("Press exists before Paint rollback proof"),
            Fixture.Builder->CreateNewFactory(Reason))
        || !TestTrue(TEXT("Press commissions before Body/Weld"),
            Fixture.Builder->CommissionPressStarter(Reason))
        || !TestTrue(TEXT("Body/Weld exists before Paint"),
            Fixture.Builder->CreateBodyWeldStarter(Reason))
        || !TestTrue(TEXT("Body/Weld commissions before Paint"),
            Fixture.Builder->CommissionBodyWeldStarter(Reason)))
    {
        Fixture.Destroy();
        return false;
    }
    TestEqual(TEXT("Native lifecycle exposes Paint after Body/Weld"),
        Fixture.Builder->GetUMGActions()[0].Title,
        FString(TEXT("Build Paint starter")));

    Fixture.Builder->SetForcePaintPresentationFailureForTests(true);
    TestFalse(TEXT("Forced Paint art failure rejects construction"),
        Fixture.Builder->CreatePaintStarter(Reason));
    TestTrue(TEXT("Paint failure exposes atomic pair rollback"),
        Reason.Contains(TEXT(
            "ROLLED BACK DATA AND PRESENTATION ATOMICALLY")));
    TestEqual(TEXT("Failed Paint creation leaves no layout authority"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryPaintStarterLayoutAuthority>(Fixture.World), 0);
    TestEqual(TEXT("Failed Paint creation leaves no presentation actor"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryPaintStarterPresentationActor>(Fixture.World), 0);

    Fixture.Destroy();
    if (!TestTrue(TEXT("Fresh Paint lifecycle fixture validates"),
            Fixture.Create(TEXT("LBOneFactoryPaintBuilderLifecycleTest")))
        || !TestTrue(TEXT("Fresh Press starter exists"),
            Fixture.Builder->CreateNewFactory(Reason))
        || !TestTrue(TEXT("Fresh Press starter commissions"),
            Fixture.Builder->CommissionPressStarter(Reason))
        || !TestTrue(TEXT("Fresh Body/Weld starter exists"),
            Fixture.Builder->CreateBodyWeldStarter(Reason))
        || !TestTrue(TEXT("Fresh Body/Weld starter commissions"),
            Fixture.Builder->CommissionBodyWeldStarter(Reason)))
    {
        Fixture.Destroy();
        return false;
    }
    Fixture.Builder->SetForcePaintPresentationFailureForTests(false);
    TestTrue(TEXT("UMG lifecycle atomically creates the Paint pair"),
        Fixture.Builder->ExecuteUMGAction(0, Reason));
    ALBOneFactoryPaintStarterLayoutAuthority* Authority =
        LBOneFactoryPlayerBuilderTestsPrivate::FindPaintAuthority(
            Fixture.World);
    ALBOneFactoryPaintStarterPresentationActor* Presentation =
        LBOneFactoryPlayerBuilderTestsPrivate::FindPaintPresentation(
            Fixture.World);
    if (!TestNotNull(TEXT("Paint layout authority exists"), Authority)
        || !TestNotNull(TEXT("Paint native presentation exists"),
            Presentation))
    {
        Fixture.Destroy();
        return false;
    }
    TestEqual(TEXT("Exactly one Paint layout authority is live"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryPaintStarterLayoutAuthority>(Fixture.World), 1);
    TestEqual(TEXT("Exactly one Paint presentation actor is live"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryPaintStarterPresentationActor>(Fixture.World), 1);
    TestFalse(TEXT("Downstream Paint blocks Body/Weld pair removal"),
        Fixture.Builder->RemoveBodyWeldStarter(Reason));
    TestTrue(TEXT("Body/Weld removal rejection names downstream order"),
        Reason.Contains(TEXT("DOWNSTREAM")));
    TestFalse(TEXT("A second Paint starter pair is refused"),
        Fixture.Builder->CreatePaintStarter(Reason));
    TestFalse(TEXT("Paint creation awaits explicit commission"),
        Authority->IsCommissioned());
    TestEqual(TEXT("Useful spray booth responsibility is selected"),
        Fixture.Builder->GetSelectedTargetId(),
        LBOneFactoryPaintStarterIds::Station(
            ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth));
    TestEqual(TEXT("Paint presentation commits its exact tracked-line items"),
        Presentation->GetVisibleInstanceCount(),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedVisibleInstanceCount());
    TestEqual(TEXT("Paint presentation commits its exact active HISM batches"),
        Presentation->GetVisualBatchCount(),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedVisualBatchCount());
    TestTrue(TEXT("Actual player path receives the visible tracked ED line"),
        Presentation->ActorHasTag(
            FName(TEXT("LB.Paint.TrackedEDLineVisible"))));
    TestEqual(TEXT("Actual player path includes the immersed C2040 BIW"),
        Presentation->GetInstanceCountForBatch(
            ELBOneFactoryPaintPresentationBatch::EDImmersedBody), 1);
    TestFalse(TEXT("Paint art never persists or owns process WIP"),
        Presentation->RepresentsProcessWIP());
    TestFalse(TEXT("Paint art never invents hidden booth internals"),
        Presentation->ClaimsHiddenProcessInternals());

    const FLBOneFactoryPaintStarterLayoutState BeforeProgramme =
        Authority->CaptureLayout();
    TestEqual(TEXT("Canonical Paint programme begins Cairnwell teal"),
        BeforeProgramme.SelectedBodyColour,
        ELBOneFactoryPaintColour::CairnwellTeal);
    TestTrue(TEXT("Native UMG chooses the next complete colour programme"),
        Fixture.Builder->ExecuteUMGAction(2, Reason));
    const FLBOneFactoryPaintStarterLayoutState Red = Authority->CaptureLayout();
    TestEqual(TEXT("Next launch colour is signal red"),
        Red.SelectedBodyColour, ELBOneFactoryPaintColour::SignalRed);
    TestEqual(TEXT("Programme commit advances exactly one revision"),
        Red.Revision, BeforeProgramme.Revision + 1);
    TestEqual(TEXT("Paint presentation follows the committed colour"),
        Presentation->GetConfiguredBodyColour(),
        ELBOneFactoryPaintColour::SignalRed);
    TestEqual(TEXT("Paint presentation follows the data revision"),
        Presentation->GetConfiguredLayoutRevision(), Red.Revision);
    bool bEveryBoundResponsibilityMatches = true;
    int32 BoundResponsibilityCount = 0;
    for (const FLBOneFactoryPaintStarterStationState& Station : Red.Stations)
    {
        if (Station.PaintProgrammeId.IsNone()) continue;
        ++BoundResponsibilityCount;
        bEveryBoundResponsibilityMatches &=
            Station.PaintProgrammeId == Red.PaintProgrammeId
            && Station.TargetBodyColour == Red.SelectedBodyColour;
    }
    TestTrue(TEXT("All five downstream responsibilities change together"),
        BoundResponsibilityCount == 5 && bEveryBoundResponsibilityMatches);

    Fixture.Builder->SetForcePaintPresentationFailureForTests(true);
    TestFalse(TEXT("Forced Paint sync failure rejects colour change"),
        Fixture.Builder->ExecuteUMGAction(2, Reason));
    Fixture.Builder->SetForcePaintPresentationFailureForTests(false);
    const FLBOneFactoryPaintStarterLayoutState AfterRollback =
        Authority->CaptureLayout();
    TestEqual(TEXT("Failed Paint sync restores exact revision"),
        AfterRollback.Revision, Red.Revision);
    TestEqual(TEXT("Failed Paint sync restores exact programme colour"),
        AfterRollback.SelectedBodyColour, Red.SelectedBodyColour);
    TestEqual(TEXT("Failed Paint sync restores presentation revision"),
        Presentation->GetConfiguredLayoutRevision(), Red.Revision);
    TestEqual(TEXT("Failed Paint sync restores presentation colour"),
        Presentation->GetConfiguredBodyColour(), Red.SelectedBodyColour);
    TestTrue(TEXT("Paint rollback reason proves both restores"),
        Reason.Contains(TEXT("ROLLED BACK"))
        && Reason.Contains(TEXT("DATA RESTORE: PASS"))
        && Reason.Contains(TEXT("PRESENTATION RESTORE: PASS")));

    const FLBOneFactoryPaintStarterStationState* SprayBeforeMove =
        AfterRollback.Stations.FindByPredicate([](
            const FLBOneFactoryPaintStarterStationState& Station)
        {
            return Station.Role ==
                ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth;
        });
    const FVector SprayLocation = SprayBeforeMove
        ? SprayBeforeMove->WorldTransform.GetLocation() : FVector::ZeroVector;
    TestTrue(TEXT("Native UMG moves selected Paint responsibility"),
        SprayBeforeMove && Fixture.Builder->ExecuteUMGAction(3, Reason));
    const FLBOneFactoryPaintStarterLayoutState Moved =
        Authority->CaptureLayout();
    const FLBOneFactoryPaintStarterStationState* SprayAfterMove =
        Moved.Stations.FindByPredicate([](
            const FLBOneFactoryPaintStarterStationState& Station)
        {
            return Station.Role ==
                ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth;
        });
    TestTrue(TEXT("Paint responsibility moves exactly one metre east"),
        SprayAfterMove
        && SprayAfterMove->WorldTransform.GetLocation().Equals(
            SprayLocation + FVector(100.0f, 0.0f, 0.0f), 0.01f));
    TestEqual(TEXT("Moved Paint presentation follows data revision"),
        Presentation->GetConfiguredLayoutRevision(), Moved.Revision);

    FLBOneFactoryPaintStarterLayoutState WithWIP = Moved;
    FLBOneFactoryPaintStarterStationState* WIPStation =
        WithWIP.Stations.FindByPredicate([](
            const FLBOneFactoryPaintStarterStationState& Station)
        {
            return Station.Role ==
                ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth;
        });
    if (WIPStation)
        WIPStation->ActiveOrReservedUnitIds.Add(
            TEXT("LB.PAINT.WIP.TEST.001"));
    TestTrue(TEXT("Committed Paint layout state accepts coherent WIP"),
        WIPStation && Authority->RestoreLayout(WithWIP, Reason));
    TestTrue(TEXT("Presentation rebuilds from committed layout only"),
        Presentation->ConfigureFromLayout(
            Authority->CaptureLayout(), Reason));
    const TArray<FLBOneFactoryBuilderUMGAction> WIPActions =
        Fixture.Builder->GetUMGActions();
    TestFalse(TEXT("Paint WIP blocks explicit commission"),
        WIPActions[0].bEnabled);
    TestFalse(TEXT("Paint WIP blocks programme changes"),
        WIPActions[2].bEnabled);
    TestFalse(TEXT("Paint WIP blocks responsibility movement"),
        WIPActions[3].bEnabled);
    TestFalse(TEXT("Paint WIP blocks complete pair removal"),
        WIPActions[4].bEnabled);
    TestTrue(TEXT("Every blocked Paint action exposes its WIP reason"),
        WIPActions[0].Detail.Contains(TEXT("WIP"))
        && WIPActions[2].Detail.Contains(TEXT("WIP"))
        && WIPActions[3].Detail.Contains(TEXT("WIP"))
        && WIPActions[4].Detail.Contains(TEXT("WIP")));

    TestTrue(TEXT("Cleared committed layout restores atomically"),
        Authority->RestoreLayout(Moved, Reason));
    TestTrue(TEXT("Presentation follows restored committed snapshot"),
        Presentation->ConfigureFromLayout(Moved, Reason));
    TestTrue(TEXT("Lifecycle explicitly commissions Paint"),
        Fixture.Builder->ExecuteUMGAction(0, Reason));
    TestTrue(TEXT("Paint authority is commissioned"),
        Authority->IsCommissioned());
    TestTrue(TEXT("Summary exposes commissioned Paint native provenance"),
        Fixture.Builder->GetUMGSummary().Contains(
            TEXT("PAINT: COMMISSIONED"))
        && Fixture.Builder->GetUMGSummary().Contains(
            TEXT("NATIVE-ONLY PASS")));
    TestTrue(TEXT("Idle complete Paint pair can be removed atomically"),
        Fixture.Builder->GetUMGActions()[4].bEnabled
        && Fixture.Builder->ExecuteUMGAction(4, Reason));
    TestEqual(TEXT("Atomic removal destroys the one Paint authority"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryPaintStarterLayoutAuthority>(Fixture.World), 0);
    TestEqual(TEXT("Atomic removal destroys the paired presentation"),
        LBOneFactoryPlayerBuilderTestsPrivate::CountLiveActors<
            ALBOneFactoryPaintStarterPresentationActor>(Fixture.World), 0);
    TestEqual(TEXT("Lifecycle returns to the Paint construction step"),
        Fixture.Builder->GetUMGActions()[0].Title,
        FString(TEXT("Build Paint starter")));

    Fixture.Destroy();
    return true;
}

#endif
