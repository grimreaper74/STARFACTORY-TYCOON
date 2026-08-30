#if WITH_DEV_AUTOMATION_TESTS

#include "LBPaintShopManagementPawn.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "LBPaintShopBuildAuthority.h"
#include "LBPaintShopPrototypeGameMode.h"
#include "LBPaintShopPrototypeHUD.h"
#include "LBPaintShopPrototypeRuntime.h"
#include "LBPaintShopPrototypeWorldBootstrap.h"
#include "Misc/AutomationTest.h"
#include <limits>

namespace LBPaintShopPlayerShellTests
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
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPlayerShellCameraContractTest,
    "LineBoss.PaintShop.Experimental.PlayerShell.Camera.FixedEDCoatFocusContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPlayerShellCameraContractTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const FLBPaintShopCameraFocusContract Identity =
        ALBPaintShopManagementPawn::BuildEDCoatFocusContract(FTransform::Identity);
    TestTrue(TEXT("Camera targets the exact vertical centre of the approved cell"),
        Identity.Target.Equals(FVector(0.0f, 0.0f, 426.5f), KINDA_SMALL_NUMBER));
    TestTrue(TEXT("Camera contract declares the exact 1800 x 1000 x 853 cm cell"),
        Identity.CellDimensionsCm.Equals(FVector(1800.0f, 1000.0f, 853.0f),
            KINDA_SMALL_NUMBER));
    TestEqual(TEXT("Camera comparison zoom is deterministic"),
        Identity.ZoomDistanceCm, 2700.0f);
    TestTrue(TEXT("Camera comparison rotation is deterministic"),
        Identity.Rotation.Equals(FRotator(-32.0f, 45.0f, 0.0f),
            KINDA_SMALL_NUMBER));
    TestEqual(TEXT("Camera comparison FOV is deterministic"),
        Identity.FieldOfViewDegrees, 55.0f);

    const FTransform Translated(FRotator::ZeroRotator,
        FVector(1200.0f, -300.0f, 100.0f));
    const FLBPaintShopCameraFocusContract Moved =
        ALBPaintShopManagementPawn::BuildEDCoatFocusContract(Translated);
    TestTrue(TEXT("Camera target follows a finite supplied cell transform exactly"),
        Moved.Target.Equals(FVector(1200.0f, -300.0f, 526.5f),
            KINDA_SMALL_NUMBER));
    TestEqual(TEXT("Zoom clamps to its management minimum"),
        ALBPaintShopManagementPawn::ClampPrototypeZoomDistance(-1.0f), 1400.0f);
    TestEqual(TEXT("Zoom clamps to its management maximum"),
        ALBPaintShopManagementPawn::ClampPrototypeZoomDistance(50000.0f), 9000.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPlayerShellGameModeContractTest,
    "LineBoss.PaintShop.Experimental.PlayerShell.GameMode.DefaultClassesAndBootstrapGate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPlayerShellGameModeContractTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const ALBPaintShopPrototypeGameMode* Defaults =
        GetDefault<ALBPaintShopPrototypeGameMode>();
    TestNotNull(TEXT("Paint player-shell game mode defaults exist"), Defaults);
    if (Defaults)
    {
        TestEqual(TEXT("Game mode selects only the Paint management pawn"),
            Defaults->DefaultPawnClass.Get(), ALBPaintShopManagementPawn::StaticClass());
        TestEqual(TEXT("Game mode selects only the Paint prototype HUD"),
            Defaults->HUDClass.Get(), ALBPaintShopPrototypeHUD::StaticClass());
        TestFalse(TEXT("Game mode never ticks"), Defaults->PrimaryActorTick.bCanEverTick);
    }

    FString Reason;
    TestTrue(TEXT("One coherent already-Ready bootstrap passes"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(1, 1, 1,
            ELBPaintShopPrototypeBootstrapState::Ready,
            true, true, true, true, true, Reason));
    TestEqual(TEXT("Passing bootstrap contract has stable status"), Reason,
        FString(TEXT("PAINT SHOP PROTOTYPE ISOLATED - ED-COAT READY")));
    TestFalse(TEXT("Missing bootstrap fails closed"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(0, 1, 1,
            ELBPaintShopPrototypeBootstrapState::Ready,
            true, true, true, true, true, Reason));
    TestFalse(TEXT("Duplicate bootstraps fail closed"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(2, 1, 1,
            ELBPaintShopPrototypeBootstrapState::Ready,
            true, true, true, true, true, Reason));
    TestFalse(TEXT("A duplicate build authority fails closed"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(1, 2, 1,
            ELBPaintShopPrototypeBootstrapState::Ready,
            true, true, true, true, true, Reason));
    TestFalse(TEXT("A duplicate runtime fails closed"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(1, 1, 2,
            ELBPaintShopPrototypeBootstrapState::Ready,
            true, true, true, true, true, Reason));
    TestFalse(TEXT("An initializing bootstrap is not treated as Ready"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(1, 1, 1,
            ELBPaintShopPrototypeBootstrapState::Initializing,
            true, true, true, true, true, Reason));
    TestFalse(TEXT("A failed bootstrap remains failed"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(1, 1, 1,
            ELBPaintShopPrototypeBootstrapState::Failed,
            true, true, true, true, true, Reason));
    TestFalse(TEXT("A Ready label cannot hide a missing runtime"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(1, 1, 0,
            ELBPaintShopPrototypeBootstrapState::Ready,
            true, false, false, false, false, Reason));
    TestFalse(TEXT("A Ready label cannot hide a missing build authority"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(1, 0, 1,
            ELBPaintShopPrototypeBootstrapState::Ready,
            false, true, true, false, false, Reason));
    TestFalse(TEXT("An uninitialized runtime fails closed"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(1, 1, 1,
            ELBPaintShopPrototypeBootstrapState::Ready,
            true, true, false, true, true, Reason));
    TestFalse(TEXT("An unbound runtime fails closed"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(1, 1, 1,
            ELBPaintShopPrototypeBootstrapState::Ready,
            true, true, true, false, true, Reason));
    TestFalse(TEXT("A missing approved ED-coat cell fails closed"),
        ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(1, 1, 1,
            ELBPaintShopPrototypeBootstrapState::Ready,
            true, true, true, true, false, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPlayerShellHUDContractTest,
    "LineBoss.PaintShop.Experimental.PlayerShell.HUD.IsolationStageAndControls",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPlayerShellHUDContractTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    TestEqual(TEXT("Ready isolation readout is explicit"),
        ALBPaintShopPrototypeHUD::BuildIsolationReadout(1,
            ELBPaintShopPrototypeBootstrapState::Ready, true, FString()),
        FString(TEXT("ISOLATION: PASS - EXACTLY ONE COHERENT PAINT AUTHORITY PAIR")));
    TestTrue(TEXT("A Ready label cannot conceal incoherent live authorities"),
        ALBPaintShopPrototypeHUD::BuildIsolationReadout(1,
            ELBPaintShopPrototypeBootstrapState::Ready, false,
            TEXT("AUTHORITY COUNT INVALID")).Contains(TEXT("FAIL")));
    TestTrue(TEXT("Missing bootstrap is visibly failed"),
        ALBPaintShopPrototypeHUD::BuildIsolationReadout(0,
            ELBPaintShopPrototypeBootstrapState::Uninitialized, false, FString())
            .Contains(TEXT("FAIL")));
    TestTrue(TEXT("Duplicate bootstrap count is visible"),
        ALBPaintShopPrototypeHUD::BuildIsolationReadout(2,
            ELBPaintShopPrototypeBootstrapState::Ready, false, FString())
            .Contains(TEXT("FOUND 2")));

    const FString Active = ALBPaintShopPrototypeHUD::BuildRuntimeStageReadout(
        ELBPaintShopPrototypePhase::Immersing, 0.375f, true, true, false, FString());
    TestTrue(TEXT("HUD reports the exact live process stage"),
        Active.Contains(TEXT("IMMERSING")));
    TestTrue(TEXT("HUD reports rounded phase progress"),
        Active.Contains(TEXT("38%")));
    TestTrue(TEXT("HUD exposes pause and blocked output independently"),
        Active.Contains(TEXT("PAUSED")) && Active.Contains(TEXT("OUTPUT BLOCKED")));

    const FString Fault = ALBPaintShopPrototypeHUD::BuildRuntimeStageReadout(
        ELBPaintShopPrototypePhase::Faulted, 2.0f, false, false, true,
        TEXT("TEST FAULT"));
    TestTrue(TEXT("HUD clamps malformed progress and preserves the fault reason"),
        Fault.Contains(TEXT("100%")) && Fault.Contains(TEXT("TEST FAULT")));
    const FString NonFinite = ALBPaintShopPrototypeHUD::BuildRuntimeStageReadout(
        ELBPaintShopPrototypePhase::Loading,
        std::numeric_limits<float>::quiet_NaN(), false, false, false, FString());
    TestTrue(TEXT("HUD fails non-finite progress closed to zero"),
        NonFinite.Contains(TEXT("0%")));
    const FString Infinite = ALBPaintShopPrototypeHUD::BuildRuntimeStageReadout(
        ELBPaintShopPrototypePhase::Loading,
        std::numeric_limits<float>::infinity(), false, false, false, FString());
    TestTrue(TEXT("HUD also fails infinite progress closed to zero"),
        Infinite.Contains(TEXT("0%")));
    const FString Controls = ALBPaintShopPrototypeHUD::GetCameraControlsReadout();
    TestTrue(TEXT("HUD names pan, orbit, zoom and reset controls"),
        Controls.Contains(TEXT("PAN")) && Controls.Contains(TEXT("ORBIT"))
        && Controls.Contains(TEXT("ZOOM")) && Controls.Contains(TEXT("RESET")));
    const FString OperatorControls =
        ALBPaintShopPrototypeHUD::GetOperatorControlsReadout();
    TestTrue(TEXT("HUD names bounded Paint process, output and save controls"),
        OperatorControls.Contains(TEXT("START"))
        && OperatorControls.Contains(TEXT("PAUSE/RESUME"))
        && OperatorControls.Contains(TEXT("BLOCK OUTPUT"))
        && OperatorControls.Contains(TEXT("RELEASE"))
        && OperatorControls.Contains(TEXT("SAVE"))
        && OperatorControls.Contains(TEXT("LOAD")));
    TestFalse(TEXT("Paint HUD contract explicitly forbids Canvas rendering"),
        ALBPaintShopPrototypeHUD::UsesCanvasRendering());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPlayerShellLiveWorldTest,
    "LineBoss.PaintShop.Experimental.PlayerShell.World.LiveCardinalityOwnershipAndFocus",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPlayerShellLiveWorldTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPaintShopPlayerShellLiveWorldTest"));
    ALBPaintShopPrototypeWorldBootstrap* Bootstrap = World
        ? World->SpawnActor<ALBPaintShopPrototypeWorldBootstrap>() : nullptr;
    FString Reason;
    if (!TestNotNull(TEXT("Transient Paint shell world and bootstrap exist"), Bootstrap)
        || !TestTrue(TEXT("Only the bootstrap creates its Paint authority pair"),
            Bootstrap && Bootstrap->InitializePrototypeWorld(Reason)))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestEqual(TEXT("Bootstrap starts with exactly one Paint build authority"),
        LBPaintShopPlayerShellTests::CountLiveActors<ALBPaintShopBuildAuthority>(World), 1);
    TestEqual(TEXT("Bootstrap starts with exactly one Paint runtime"),
        LBPaintShopPlayerShellTests::CountLiveActors<ALBPaintShopPrototypeRuntime>(World), 1);

    ALBPaintShopPrototypeGameMode* Mode =
        World->SpawnActor<ALBPaintShopPrototypeGameMode>();
    APlayerController* Controller = World->SpawnActor<APlayerController>();
    ALBPaintShopManagementPawn* Pawn = World->SpawnActor<ALBPaintShopManagementPawn>();
    if (!TestNotNull(TEXT("Paint prototype game mode exists"), Mode)
        || !TestNotNull(TEXT("Transient player controller exists"), Controller)
        || !TestNotNull(TEXT("Paint management pawn exists"), Pawn))
    {
        World->DestroyWorld(false);
        return false;
    }

    Controller->Possess(Pawn);
    TestTrue(TEXT("Controller possesses only the Paint management pawn"),
        Controller->GetPawn() == Pawn);
    TestTrue(TEXT("Live shell validation accepts and focuses the coherent bootstrap"),
        Mode->ValidatePrototypeShellNow(Controller));
    TestTrue(TEXT("Live game mode exposes the exact bootstrap and focused state"),
        Mode->HasValidPrototypeBootstrap()
        && Mode->GetPrototypeBootstrap() == Bootstrap
        && Mode->HasFocusedManagementCamera());
    TestTrue(TEXT("Live pawn is bound to the exact same-world bootstrap"),
        Pawn->IsBoundToPrototypeBootstrap(Bootstrap));
    TestTrue(TEXT("Live pawn receives the deterministic ED-cell focus target"),
        Pawn->GetActorLocation().Equals(FVector(0.0f, 0.0f, 426.5f),
            KINDA_SMALL_NUMBER));
    TestEqual(TEXT("Live pawn receives the deterministic ED-cell zoom"),
        Pawn->GetPrototypeZoomDistance(), 2700.0f);
    TestTrue(TEXT("Repeated shell validation stays idempotent"),
        Mode->ValidatePrototypeShellNow(Controller));
    TestEqual(TEXT("Shell validation never creates another Paint build authority"),
        LBPaintShopPlayerShellTests::CountLiveActors<ALBPaintShopBuildAuthority>(World), 1);
    TestEqual(TEXT("Shell validation never creates another Paint runtime"),
        LBPaintShopPlayerShellTests::CountLiveActors<ALBPaintShopPrototypeRuntime>(World), 1);

    TestNotNull(TEXT("A test-only stray authority can be introduced"),
        World->SpawnActor<ALBPaintShopBuildAuthority>());
    AddExpectedError(
        TEXT("REQUIRES EXACTLY ONE BUILD AUTHORITY AND ONE RUNTIME; FOUND 2 AND 1"),
        EAutomationExpectedErrorFlags::Contains, 1);
    TestFalse(TEXT("Live shell revokes validity when global cardinality drifts"),
        Mode->ValidatePrototypeShellNow(Controller));
    TestFalse(TEXT("Cardinality failure revokes both bootstrap and camera claims"),
        Mode->HasValidPrototypeBootstrap() || Mode->HasFocusedManagementCamera());

    World->DestroyWorld(false);
    return true;
}

#endif
