#if WITH_DEV_AUTOMATION_TESTS

#include "LBControlRoomHUD.h"
#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryAssemblyStarterLayout.h"
#include "LBOneFactoryAssemblyStarterPresentationActor.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryBodyWeldStarterPresentationActor.h"
#include "LBOneFactoryGameMode.h"
#include "LBOneFactoryOperationsSubsystem.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryPaintStarterPresentationActor.h"
#include "LBOneFactoryPlayerBuilderSubsystem.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactorySaveSubsystem.h"
#include "LBPressShopBuildAuthority.h"
#include "LBVehiclePanelCatalog.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryActualPlayerIntegrationTestsPrivate
{
    template<typename ActorType>
    int32 CountLiveActors(UWorld* World)
    {
        int32 Count = 0;
        if (!World) return Count;
        for (TActorIterator<ActorType> It(World); It; ++It)
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++Count;
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

    FLBVehicleModelRecipe MakeNorthstarDevelopmentRecipe()
    {
        FLBVehicleModelRecipe Recipe;
        Recipe.ModelId = TEXT("NORTHSTAR_DEVELOPMENT");
        Recipe.DisplayName = TEXT("Northstar development programme");
        Recipe.RecipeRevisionId = TEXT("NORTHSTAR_DEVELOPMENT_RECIPE_V001");
        Recipe.PaintRouteProfileId = TEXT("PAINT_ROUTE_EDCOAT_VISIBLE_V001");
        Recipe.GeometryAuthorityId = TEXT("NorthstarDevelopmentGeometry_V001");
        Recipe.PanelGeometryAuthorityId = TEXT("NorthstarDevelopmentPanels_V001");
        Recipe.BaseKitTypeId = TEXT("NORTHSTAR_DEVELOPMENT_BIW_BASE_KIT");
        Recipe.bDevelopmentVisual = true;
        Recipe.bPanelGeometryValidated = true;
        Recipe.DefaultRevenuePence = 2800000;
        Recipe.RequiredPanels = {
            { TEXT("NORTHSTAR_HOOD"), TEXT("Northstar hood"), ELBPanelHandedness::None,
                12, FVector(160.0f, 140.0f, 20.0f), NAME_None },
            { TEXT("NORTHSTAR_DOOR_LEFT"), TEXT("Northstar door left"), ELBPanelHandedness::Left,
                16, FVector(120.0f, 18.0f, 110.0f), NAME_None }
        };
        return Recipe;
    }

    struct FActualPlayerWorld
    {
        UWorld* World = nullptr;
        ALBOneFactoryBootstrap* Bootstrap = nullptr;
        ALBPressShopBuildAuthority* MapBuildAuthority = nullptr;
        ALBOneFactoryGameMode* GameMode = nullptr;
        ULBOneFactoryPlayerBuilderSubsystem* Builder = nullptr;
        ULBOneFactoryOperationsSubsystem* Operations = nullptr;
        ULBOneFactorySaveSubsystem* Save = nullptr;

        bool CreateShell(const TCHAR* WorldName, FString& OutReason)
        {
            World = UWorld::CreateWorld(EWorldType::Game, false,
                FName(WorldName));
            Bootstrap = World
                ? World->SpawnActor<ALBOneFactoryBootstrap>() : nullptr;
            MapBuildAuthority = World
                ? World->SpawnActor<ALBPressShopBuildAuthority>() : nullptr;
            if (!World || !Bootstrap || !MapBuildAuthority)
            {
                OutReason = TEXT("ACTUAL-PLAYER TEST SHELL CREATION FAILED");
                return false;
            }
            ConfigureCanonicalAuthority(*MapBuildAuthority);
            Bootstrap->DispatchBeginPlay();
            GameMode = World->SpawnActor<ALBOneFactoryGameMode>();
            if (!GameMode)
            {
                OutReason = TEXT("ACTUAL-PLAYER TEST GAMEMODE CREATION FAILED");
                return false;
            }
            GameMode->DispatchBeginPlay();
            Builder = World->GetSubsystem<
                ULBOneFactoryPlayerBuilderSubsystem>();
            Operations = World->GetSubsystem<
                ULBOneFactoryOperationsSubsystem>();
            Save = World->GetSubsystem<ULBOneFactorySaveSubsystem>();
            if (!Bootstrap->HasValidShell()
                || !GameMode->HasValidOneFactoryShell()
                || !GameMode->HasValidRuntimeBackbone()
                || !Builder || !Operations || !Save)
            {
                OutReason = GameMode->GetOneFactoryStartupStatus();
                return false;
            }
            GameMode->GetOneFactoryRuntimeCoordinator()
                ->bAdvanceStartedVehiclesOnActorTick = false;
            OutReason = TEXT("ACTUAL-PLAYER ONEFACTORY SHELL READY");
            return true;
        }

        bool BuildAndCommissionThroughUMGModel(FString& OutReason)
        {
            if (!Builder)
            {
                OutReason = TEXT("ACTUAL-PLAYER BUILDER IS UNAVAILABLE");
                return false;
            }
            // One stable native-UMG lifecycle button: create/commission each of
            // Press, Body/Weld, Paint and Assembly in dependency order.
            for (int32 Transition = 0; Transition < 8; ++Transition)
                if (!Builder->ExecuteUMGAction(0, OutReason)) return false;
            return GameMode->GetOneFactoryRuntimeCoordinator()
                ->ValidateRuntimeFactory(OutReason);
        }

        ALBControlRoomHUD* CreateHUD()
        {
            return World ? World->SpawnActor<ALBControlRoomHUD>() : nullptr;
        }

        void Destroy()
        {
            if (World) World->DestroyWorld(false);
            *this = FActualPlayerWorld();
        }
    };
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryActualPlayerHUDVehicleLoopTest,
    "LineBoss.OneFactory.ActualPlayer.NativeUMGFull57StationQualityReworkLoop",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryActualPlayerHUDVehicleLoopTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryActualPlayerIntegrationTestsPrivate;
    FString Reason;
    FActualPlayerWorld Fixture;
    if (!TestTrue(TEXT("Real GameMode creates the actual-player shell/backbone"),
            Fixture.CreateShell(TEXT("LBOneFactoryActualPlayerHUDLoop"), Reason))
        || !TestTrue(TEXT("The public builder UMG model commissions all 57 positions"),
            Fixture.BuildAndCommissionThroughUMGModel(Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }

    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    TestTrue(TEXT("Configured physical route resolves after the player lifecycle"),
        Fixture.GameMode->GetOneFactoryRuntimeCoordinator()
            ->GetConfiguredStationRoute(Route, TopologyId, Reason));
    TestEqual(TEXT("The player-built factory exposes exactly 57 positions"),
        Route.Num(), ALBOneFactoryRuntimeCoordinator::RequiredPhysicalStationCount);

    ALBControlRoomHUD* HUD = Fixture.CreateHUD();
    if (!TestNotNull(TEXT("Actual-player native management HUD exists"), HUD))
    {
        Fixture.Destroy();
        return false;
    }
    HUD->OpenManagementPage(ELBManagementPage::Production);
    TestEqual(TEXT("OneFactory Production keeps the existing five UMG slots"),
        HUD->GetManagementActionCount(),
        ULBOneFactoryOperationsSubsystem::UMGActionCount);
    TestTrue(TEXT("HUD action creates one configured logical vehicle"),
        HUD->ActivateManagementAction(0));
    const FName UnitId = Fixture.Operations->GetSelectedUnitId();
    TestFalse(TEXT("Create action selects a stable UnitId"), UnitId.IsNone());
    TestTrue(TEXT("HUD action explicitly starts the selected vehicle"),
        HUD->ActivateManagementAction(2));

    bool bExercisedRework = false;
    bool bDispatched = false;
    for (int32 Guard = 0; Guard < 180 && !bDispatched; ++Guard)
    {
        FLBOneFactoryRuntimeVehicleStatus Status;
        if (!Fixture.GameMode->GetOneFactoryRuntimeCoordinator()
                ->GetVehicleRuntimeStatus(UnitId, Status, Reason))
        {
            AddError(Reason);
            break;
        }
        if (Status.bDispatched)
        {
            bDispatched = true;
            break;
        }
        if (Status.bAwaitingQualityResult)
        {
            if (!bExercisedRework)
            {
                TestTrue(TEXT("HUD requests rework at a completed quality gate"),
                    HUD->ActivateManagementAction(4));
                TestTrue(TEXT("The same HUD slot records completion of rework"),
                    HUD->ActivateManagementAction(4));
                TestTrue(TEXT("HUD reruns the reset inspection cycle"),
                    HUD->ActivateManagementAction(2));
                bExercisedRework = true;
            }
            TestTrue(TEXT("HUD records a passing quality decision"),
                HUD->ActivateManagementAction(3));
        }
        else
        {
            TestTrue(TEXT("HUD advances one deterministic station cycle"),
                HUD->ActivateManagementAction(2));
        }
    }

    TestTrue(TEXT("The actual-player path exercises quality rework"),
        bExercisedRework);
    TestTrue(TEXT("The same UnitId completes and dispatches all 57 positions"),
        bDispatched);
    const FLBOneFactoryProductionLedgerState Ledger =
        Fixture.GameMode->GetOneFactoryProductionFlow()->CaptureLedger();
    TestEqual(TEXT("Exactly one vehicle is completed"),
        Ledger.CompletedVehicleCount, 1);
    TestEqual(TEXT("Exactly one vehicle is dispatched"),
        Ledger.DispatchedVehicleCount, 1);
    Fixture.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryTwoWorldFreshRestoreTest,
    "LineBoss.OneFactory.ActualPlayer.TwoWorldFreshSessionRestoreAndHUDContinue",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryTwoWorldFreshRestoreTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryActualPlayerIntegrationTestsPrivate;
    FString Reason;
    FLBOneFactorySaveState SavedState;
    FName UnitId = NAME_None;
    FLBOneFactoryRuntimeVehicleStatus Before;

    FActualPlayerWorld SessionA;
    if (!TestTrue(TEXT("Session A starts through the real GameMode"),
            SessionA.CreateShell(TEXT("LBOneFactoryTwoWorldSessionA"), Reason))
        || !TestTrue(TEXT("Session A builds through the public UMG lifecycle"),
            SessionA.BuildAndCommissionThroughUMGModel(Reason)))
    {
        AddError(Reason);
        SessionA.Destroy();
        return false;
    }
    ALBControlRoomHUD* HUDA = SessionA.CreateHUD();
    if (!TestNotNull(TEXT("Session A public HUD exists"), HUDA))
    {
        SessionA.Destroy();
        return false;
    }
    HUDA->OpenManagementPage(ELBManagementPage::Production);
    TestTrue(TEXT("Session A creates a vehicle through HUD"),
        HUDA->ActivateManagementAction(0));
    UnitId = SessionA.Operations->GetSelectedUnitId();
    TestTrue(TEXT("Session A starts through HUD"),
        HUDA->ActivateManagementAction(2));
    TestTrue(TEXT("Session A advances through HUD"),
        HUDA->ActivateManagementAction(2));
    TestTrue(TEXT("Session A status is readable before save"),
        SessionA.GameMode->GetOneFactoryRuntimeCoordinator()
            ->GetVehicleRuntimeStatus(UnitId, Before, Reason));
    TestTrue(TEXT("Session A captures the complete save payload"),
        SessionA.Save->CaptureCurrentFactory(SavedState, Reason));
    SessionA.Destroy();

    FActualPlayerWorld SessionB;
    if (!TestTrue(TEXT("Session B starts as a genuinely empty shell"),
            SessionB.CreateShell(TEXT("LBOneFactoryTwoWorldSessionB"), Reason)))
    {
        AddError(Reason);
        SessionB.Destroy();
        return false;
    }
    TestEqual(TEXT("Fresh Session B initially has no starter actors"),
        CountLiveActors<ALBOneFactoryPressStarterLayoutAuthority>(
            SessionB.World), 0);
    if (!TestTrue(TEXT("Fresh restore materialises saved actors transactionally"),
            SessionB.Save->RestoreFactoryState(SavedState, Reason)))
    {
        AddError(Reason);
        SessionB.Destroy();
        return false;
    }
    TestEqual(TEXT("Fresh restore creates exactly one Press data authority"),
        CountLiveActors<ALBOneFactoryPressStarterLayoutAuthority>(
            SessionB.World), 1);
    TestEqual(TEXT("Fresh restore creates exactly one Body data authority"),
        CountLiveActors<ALBOneFactoryBodyWeldStarterLayoutAuthority>(
            SessionB.World), 1);
    TestEqual(TEXT("Fresh restore creates exactly one Paint data authority"),
        CountLiveActors<ALBOneFactoryPaintStarterLayoutAuthority>(
            SessionB.World), 1);
    TestEqual(TEXT("Fresh restore creates exactly one Assembly data authority"),
        CountLiveActors<ALBOneFactoryAssemblyStarterLayoutAuthority>(
            SessionB.World), 1);

    FLBOneFactoryRuntimeVehicleStatus After;
    TestTrue(TEXT("Session B restores the same UnitId into the coordinator"),
        SessionB.GameMode->GetOneFactoryRuntimeCoordinator()
            ->GetVehicleRuntimeStatus(UnitId, After, Reason));
    TestEqual(TEXT("Fresh restore preserves the physical station cursor"),
        After.StationCursor, Before.StationCursor);
    TestEqual(TEXT("Fresh restore preserves completed-station progress"),
        After.CompletedStationCount, Before.CompletedStationCount);
    TestEqual(TEXT("Fresh restore preserves explicit started state"),
        After.bStarted, Before.bStarted);

    ALBControlRoomHUD* HUDB = SessionB.CreateHUD();
    if (!TestNotNull(TEXT("Session B public HUD exists"), HUDB))
    {
        SessionB.Destroy();
        return false;
    }
    HUDB->OpenManagementPage(ELBManagementPage::Production);
    TestEqual(TEXT("Restored session remains on the five-action OneFactory route"),
        HUDB->GetManagementActionCount(),
        ULBOneFactoryOperationsSubsystem::UMGActionCount);
    TestTrue(TEXT("Restored WIP continues through the public HUD action"),
        HUDB->ActivateManagementAction(2));
    FLBOneFactoryRuntimeVehicleStatus Continued;
    TestTrue(TEXT("Continued restored WIP remains coherent"),
        SessionB.GameMode->GetOneFactoryRuntimeCoordinator()
            ->GetVehicleRuntimeStatus(UnitId, Continued, Reason));
    TestTrue(TEXT("Continuation advances beyond the saved cursor"),
        Continued.StationCursor > After.StationCursor
            || Continued.CycleElapsedSeconds > After.CycleElapsedSeconds);
    HUDB->OpenManagementPage(ELBManagementPage::Analytics);
    TestEqual(TEXT("Restored OneFactory routes Analytics to isolated save/load"),
        HUDB->GetManagementActionCount(), 2);
    SessionB.Destroy();
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryProgrammeChangeoverTest,
    "LineBoss.OneFactory.ActualPlayer.EmptyLineProgrammeChangeoverUsesRegisteredRecipe",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryProgrammeChangeoverTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryActualPlayerIntegrationTestsPrivate;
    const FName ModelId(TEXT("NORTHSTAR_DEVELOPMENT"));
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);
    const FLBVehicleModelRecipe Recipe = MakeNorthstarDevelopmentRecipe();
    FString Reason;
    if (!TestTrue(TEXT("second development recipe registers"),
            LBVehicleModelCatalog::RegisterDevelopmentRecipe(Recipe, Reason)))
        return false;

    FActualPlayerWorld Fixture;
    const bool bReady = Fixture.CreateShell(TEXT("LBOneFactoryProgrammeChangeover"), Reason)
        && Fixture.BuildAndCommissionThroughUMGModel(Reason);
    if (!TestTrue(TEXT("empty player-built line is ready for a programme changeover"), bReady))
    {
        AddError(Reason);
        Fixture.Destroy();
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);
        return false;
    }
    const TArray<FLBOneFactoryBuilderUMGAction> Actions =
        Fixture.Operations->GetUMGActions();
    TestEqual(TEXT("empty multi-model line exposes player-facing changeover"),
        Actions[1].Title, FString(TEXT("Change factory programme")));
    TestTrue(TEXT("all four layouts retool atomically through player UMG while zero WIP exists"),
        Fixture.Operations->ExecuteUMGAction(1, Reason));
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Body = nullptr;
    ALBOneFactoryPaintStarterLayoutAuthority* Paint = nullptr;
    ALBOneFactoryAssemblyStarterLayoutAuthority* Assembly = nullptr;
    for (TActorIterator<ALBOneFactoryBodyWeldStarterLayoutAuthority> It(Fixture.World); It; ++It) Body = *It;
    for (TActorIterator<ALBOneFactoryPaintStarterLayoutAuthority> It(Fixture.World); It; ++It) Paint = *It;
    for (TActorIterator<ALBOneFactoryAssemblyStarterLayoutAuthority> It(Fixture.World); It; ++It) Assembly = *It;
    if (!TestNotNull(TEXT("body layout exists after player build"), Body)
        || !TestNotNull(TEXT("paint layout exists after player build"), Paint)
        || !TestNotNull(TEXT("assembly layout exists after player build"), Assembly))
    {
        Fixture.Destroy();
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);
        return false;
    }
    TestEqual(TEXT("body layout carries selected programme"),
        Body->CaptureLayout().VehicleModelId, ModelId);
    TestEqual(TEXT("paint layout carries selected programme"),
        Paint->CaptureLayout().VehicleModelId, ModelId);
    TestEqual(TEXT("assembly layout carries selected programme"),
        Assembly->CaptureLayout().VehicleModelId, ModelId);
    TestTrue(TEXT("public operation action creates the selected programme, not Cairnwell"),
        Fixture.Operations->ExecuteUMGAction(0, Reason));
    const FLBOneFactoryProductionLedgerState Ledger =
        Fixture.GameMode->GetOneFactoryProductionFlow()->CaptureLedger();
    TestEqual(TEXT("the new unit captures Northstar as its immutable model identity"),
        Ledger.Units.Last().VehicleModelId, ModelId);
    TestEqual(TEXT("the new unit captures Northstar's immutable recipe revision"),
        Ledger.Units.Last().VehicleRecipeRevisionId, Recipe.RecipeRevisionId);
    TestEqual(TEXT("the new unit captures Northstar's own panel BOM"),
        Ledger.Units.Last().RequiredPanelTypeIds.Num(), Recipe.RequiredPanels.Num());
    TestFalse(TEXT("active WIP prevents a mixed-model retool"),
        Fixture.Operations->ChangeFactoryProgramme(TEXT("CAIRNWELL_2040"), Reason));
    Fixture.Destroy();
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactorySecondModelFullRouteTest,
    "LineBoss.OneFactory.ActualPlayer.RegisteredDevelopmentModelCompletesFullRoute",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactorySecondModelFullRouteTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryActualPlayerIntegrationTestsPrivate;
    const FName ModelId(TEXT("NORTHSTAR_DEVELOPMENT"));
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);
    const FLBVehicleModelRecipe Recipe = MakeNorthstarDevelopmentRecipe();
    FString Reason;
    if (!TestTrue(TEXT("second route recipe registers"),
            LBVehicleModelCatalog::RegisterDevelopmentRecipe(Recipe, Reason)))
        return false;

    FActualPlayerWorld Fixture;
    const bool bReady = Fixture.CreateShell(TEXT("LBOneFactorySecondModelFullRoute"), Reason)
        && Fixture.BuildAndCommissionThroughUMGModel(Reason)
        && Fixture.Operations->ChangeFactoryProgramme(ModelId, Reason);
    if (!TestTrue(TEXT("second model factory retargets before production"), bReady))
    {
        AddError(Reason);
        Fixture.Destroy();
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);
        return false;
    }

    FName UnitId;
    if (!TestTrue(TEXT("second model order is created by the runtime coordinator"),
            Fixture.GameMode->GetOneFactoryRuntimeCoordinator()->CreateRuntimeVehicleOrder(
                TEXT("NORTHSTAR_FULL_ROUTE_001"), ModelId,
                ULBOneFactoryPaintStarterLayoutLibrary::MakePaintProgrammeIdForModel(
                    ModelId, ELBOneFactoryPaintColour::CairnwellTeal),
                TEXT("NORTHSTAR_TEAL"), TEXT("NORTHSTAR_COIL_001"), UnitId, Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);
        return false;
    }
    if (!TestTrue(TEXT("second model order starts from the configured Press inbound"),
            Fixture.GameMode->GetOneFactoryRuntimeCoordinator()->StartVehicle(UnitId, Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);
        return false;
    }

    bool bDispatched = false;
    for (int32 Guard = 0; Guard < 180 && !bDispatched; ++Guard)
    {
        FLBOneFactoryRuntimeVehicleStatus Status;
        if (!Fixture.GameMode->GetOneFactoryRuntimeCoordinator()->GetVehicleRuntimeStatus(
                UnitId, Status, Reason))
        {
            AddError(Reason);
            break;
        }
        if (Status.bDispatched)
        {
            bDispatched = true;
            break;
        }
        if (Status.bAwaitingQualityResult)
        {
            if (!Fixture.GameMode->GetOneFactoryRuntimeCoordinator()->
                    SubmitRuntimeQualityResult(UnitId,
                        ELBOneFactoryVehicleQualityState::Passed,
                        FName(*FString::Printf(TEXT("NORTHSTAR_QA_%03d"), Guard)),
                        Reason))
            {
                AddError(Reason);
                break;
            }
        }
        else if (!Fixture.GameMode->GetOneFactoryRuntimeCoordinator()->
                TickVehicle(UnitId, 1000.0f, Reason))
        {
            AddError(Reason);
            break;
        }
    }

    TestTrue(TEXT("the registered development model dispatches through all factory stages"),
        bDispatched);
    const FLBOneFactoryProductionLedgerState Ledger =
        Fixture.GameMode->GetOneFactoryProductionFlow()->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* Unit = Ledger.Units.FindByPredicate(
        [UnitId](const FLBOneFactoryVehicleUnitState& Candidate)
        {
            return Candidate.UnitId == UnitId;
        });
    TestTrue(TEXT("the dispatched unit retains the selected model identity"),
        Unit && Unit->VehicleModelId == ModelId && Unit->bCompleted && Unit->bDispatched);
    TestTrue(TEXT("the dispatched unit retains the selected recipe revision"),
        Unit && Unit->VehicleRecipeRevisionId == Recipe.RecipeRevisionId);
    Fixture.Destroy();
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ModelId);
    return !HasAnyErrors();
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryFreshRestoreRollbackTest,
    "LineBoss.OneFactory.ActualPlayer.FreshRestoreFailureDestroysOnlyMaterialisedActors",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryFreshRestoreRollbackTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactoryActualPlayerIntegrationTestsPrivate;
    FString Reason;
    FLBOneFactorySaveState SavedState;

    FActualPlayerWorld SourceSession;
    if (!TestTrue(TEXT("Rollback source session starts"),
            SourceSession.CreateShell(
                TEXT("LBOneFactoryFreshRollbackSource"), Reason))
        || !TestTrue(TEXT("Rollback source session builds through UMG"),
            SourceSession.BuildAndCommissionThroughUMGModel(Reason))
        || !TestTrue(TEXT("Rollback source state captures"),
            SourceSession.Save->CaptureCurrentFactory(SavedState, Reason)))
    {
        AddError(Reason);
        SourceSession.Destroy();
        return false;
    }
    SourceSession.Destroy();

    FActualPlayerWorld FreshSession;
    if (!TestTrue(TEXT("Rollback target starts as a fresh GameMode shell"),
            FreshSession.CreateShell(
                TEXT("LBOneFactoryFreshRollbackTarget"), Reason)))
    {
        AddError(Reason);
        FreshSession.Destroy();
        return false;
    }
    FreshSession.Save->SetForcePresentationFailureForTests(true);
    TestFalse(TEXT("Injected post-materialisation failure rejects restore"),
        FreshSession.Save->RestoreFactoryState(SavedState, Reason));
    FreshSession.Save->SetForcePresentationFailureForTests(false);
    TestTrue(TEXT("Failure reports fresh-shell transactional rollback"),
        Reason.Contains(TEXT("FRESH RESTORE ROLLED BACK")));
    TestEqual(TEXT("Rollback removes the newly materialised Press data actor"),
        CountLiveActors<ALBOneFactoryPressStarterLayoutAuthority>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Press presentation"),
        CountLiveActors<ALBOneFactoryPressStarterPresentationActor>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Body data actor"),
        CountLiveActors<ALBOneFactoryBodyWeldStarterLayoutAuthority>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Body presentation"),
        CountLiveActors<ALBOneFactoryBodyWeldStarterPresentationActor>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Paint data actor"),
        CountLiveActors<ALBOneFactoryPaintStarterLayoutAuthority>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Paint presentation"),
        CountLiveActors<ALBOneFactoryPaintStarterPresentationActor>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Assembly data actor"),
        CountLiveActors<ALBOneFactoryAssemblyStarterLayoutAuthority>(
            FreshSession.World), 0);
    TestEqual(TEXT("Rollback removes the newly materialised Assembly presentation"),
        CountLiveActors<ALBOneFactoryAssemblyStarterPresentationActor>(
            FreshSession.World), 0);
    const FLBOneFactoryProductionLedgerState RolledBackLedger =
        FreshSession.GameMode->GetOneFactoryProductionFlow()->CaptureLedger();
    TestTrue(TEXT("Rollback restores the fresh empty production ledger"),
        RolledBackLedger.Units.IsEmpty()
            && !RolledBackLedger.Commissioning.bPressCommissioned
            && !RolledBackLedger.Commissioning.bBodyCommissioned
            && !RolledBackLedger.Commissioning.bPaintCommissioned
            && !RolledBackLedger.Commissioning.bAssemblyCommissioned);
    TestEqual(TEXT("Rollback leaves no stale player-builder selection"),
        FreshSession.Builder->GetSelectedTargetKind(),
        ELBOneFactoryBuilderTargetKind::None);
    FreshSession.Destroy();
    return true;
}

#endif
