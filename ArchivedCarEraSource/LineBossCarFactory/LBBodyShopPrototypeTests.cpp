#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopManagementPawn.h"
#include "LBBodyShopPrototypeGameMode.h"
#include "LBBodyShopPrototypeHUD.h"
#include "LBBodyShopPrototypeWorldBootstrap.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPrototypeIsolationContractTest,
    "LineBoss.BodyShop.Experimental.Isolation.Contract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPrototypeIsolationContractTest::RunTest(const FString& Parameters)
{
    const ALBBodyShopPrototypeGameMode* PrototypeMode =
        GetDefault<ALBBodyShopPrototypeGameMode>();
    TestNotNull(TEXT("Prototype game mode default object exists"), PrototypeMode);
    if (PrototypeMode)
    {
        TestEqual(TEXT("Prototype game mode uses only its management pawn"),
            PrototypeMode->DefaultPawnClass.Get(),
            ALBBodyShopManagementPawn::StaticClass());
        TestEqual(TEXT("Prototype game mode uses only its UMG HUD host"),
            PrototypeMode->HUDClass.Get(), ALBBodyShopPrototypeHUD::StaticClass());
    }

    FString Reason;
    TestTrue(TEXT("One isolated bootstrap with runtime-only commissioned authorities passes"),
        ALBBodyShopPrototypeGameMode::ValidatePrototypeWorldContract(
            true, true, true, false, true, true, Reason));
    TestEqual(TEXT("Passing isolation contract has stable status"), Reason,
        FString(TEXT("BODY SHOP PROTOTYPE IS ISOLATED")));

    TestFalse(TEXT("Missing map bootstrap is rejected"),
        ALBBodyShopPrototypeGameMode::ValidatePrototypeWorldContract(
            false, true, true, false, true, true, Reason));
    TestTrue(TEXT("Missing bootstrap explains required map actor"),
        Reason.Contains(TEXT("REQUIRES EXACTLY ONE MAP BOOTSTRAP")));

    TestFalse(TEXT("Invalid map flags are rejected"),
        ALBBodyShopPrototypeGameMode::ValidatePrototypeWorldContract(
            true, false, true, false, true, true, Reason));
    TestFalse(TEXT("Wrong game mode or non-isolated map is rejected"),
        ALBBodyShopPrototypeGameMode::ValidatePrototypeWorldContract(
            true, true, false, false, true, true, Reason));
    TestTrue(TEXT("Non-isolated map has stable language"),
        Reason.Contains(TEXT("MAP IS NOT ISOLATED")));
    TestFalse(TEXT("Legacy authority is rejected"),
        ALBBodyShopPrototypeGameMode::ValidatePrototypeWorldContract(
            true, true, false, true, true, true, Reason));
    TestTrue(TEXT("Legacy rejection has stable language"),
        Reason.Contains(TEXT("LEGACY FACTORY AUTHORITY")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPrototypeRuntimeBootstrapContractTest,
    "LineBoss.BodyShop.Experimental.Isolation.RuntimeBootstrapOnly",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPrototypeRuntimeBootstrapContractTest::RunTest(const FString& Parameters)
{
    const ALBBodyShopPrototypeWorldBootstrap* Bootstrap =
        GetDefault<ALBBodyShopPrototypeWorldBootstrap>();
    TestNotNull(TEXT("Prototype bootstrap default object exists"), Bootstrap);
    if (Bootstrap)
    {
        TestTrue(TEXT("Prototype runtime is expressly a BeginPlay-only spawn"),
            Bootstrap->ShouldSpawnRuntimeOnBeginPlay());
        TestTrue(TEXT("Prototype default requests the approved initial underbody slice"),
            Bootstrap->ShouldRequestInitialUnderbodySlice());
    }

    FString Reason;
    TestTrue(TEXT("An empty saved map passes runtime-only spawn preflight"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateRuntimeSpawnPreconditions(
            true, true, 0, 0, Reason));
    TestEqual(TEXT("Valid preflight has stable status"), Reason,
        FString(TEXT("BODY SHOP PROTOTYPE RUNTIME SPAWN PREFLIGHT VALID")));
    TestFalse(TEXT("A map cannot disable BeginPlay runtime spawning"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateRuntimeSpawnPreconditions(
            false, true, 0, 0, Reason));
    TestTrue(TEXT("Disabled BeginPlay spawning explains the isolation rule"),
        Reason.Contains(TEXT("BEGIN PLAY")));
    TestFalse(TEXT("A baked build authority is rejected before runtime wiring"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateRuntimeSpawnPreconditions(
            true, true, 1, 0, Reason));
    TestTrue(TEXT("Baked authority rejection names the map contract"),
        Reason.Contains(TEXT("MUST NOT BAKE RUNTIME AUTHORITIES")));
    TestFalse(TEXT("A baked runtime is rejected before runtime wiring"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateRuntimeSpawnPreconditions(
            true, true, 0, 1, Reason));
    TestFalse(TEXT("The approved underbody slice cannot be skipped"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateRuntimeSpawnPreconditions(
            true, false, 0, 0, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPrototypeRuntimeCompletionContractTest,
    "LineBoss.BodyShop.Experimental.Isolation.RuntimeCommissioningRequired",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPrototypeRuntimeCompletionContractTest::RunTest(const FString& Parameters)
{
    FString Reason;
    TestFalse(TEXT("An isolated map is not considered ready before authority binding"),
        ALBBodyShopPrototypeGameMode::ValidatePrototypeWorldContract(
            true, true, true, false, false, false, Reason));
    TestTrue(TEXT("Missing bound authorities has stable diagnostics"),
        Reason.Contains(TEXT("RUNTIME AUTHORITIES ARE NOT BOUND")));
    TestFalse(TEXT("A bound runtime must still commission the first slice"),
        ALBBodyShopPrototypeGameMode::ValidatePrototypeWorldContract(
            true, true, true, false, true, false, Reason));
    TestTrue(TEXT("Missing commission has stable diagnostics"),
        Reason.Contains(TEXT("UNDERBODY SLICE IS NOT COMMISSIONED")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPrototypeBootstrapFlagsTest,
    "LineBoss.BodyShop.Experimental.Isolation.BootstrapFlags",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPrototypeBootstrapFlagsTest::RunTest(const FString& Parameters)
{
    FString Reason;
    TestTrue(TEXT("Exact isolated experimental flags validate"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateBootstrapFlags(
            true, true, true, true, 100.0f, Reason));
    TestFalse(TEXT("Prototype opt-in cannot be disabled"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateBootstrapFlags(
            false, true, true, true, 100.0f, Reason));
    TestFalse(TEXT("Legacy authority rejection cannot be disabled"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateBootstrapFlags(
            true, false, true, true, 100.0f, Reason));
    TestFalse(TEXT("Campaign v18 persistence cannot be enabled"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateBootstrapFlags(
            true, true, false, true, 100.0f, Reason));
    TestFalse(TEXT("Prototype game mode requirement cannot be disabled"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateBootstrapFlags(
            true, true, true, false, 100.0f, Reason));
    TestFalse(TEXT("Non-100 cm prototype grid is rejected"),
        ALBBodyShopPrototypeWorldBootstrap::ValidateBootstrapFlags(
            true, true, true, true, 50.0f, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPrototypeLegacyNameGateTest,
    "LineBoss.BodyShop.Experimental.Isolation.LegacyNameGate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPrototypeLegacyNameGateTest::RunTest(const FString& Parameters)
{
    TestTrue(TEXT("Legacy composite Body Weld actor is forbidden"),
        ALBBodyShopPrototypeWorldBootstrap::IsForbiddenLegacyAuthorityClassName(
            TEXT("LBBodyWeldLineActor")));
    TestTrue(TEXT("Press campaign authority is forbidden"),
        ALBBodyShopPrototypeWorldBootstrap::IsForbiddenLegacyAuthorityClassName(
            TEXT("BP_LBPressShopCampaignController_C")));
    TestTrue(TEXT("Legacy general game mode is forbidden"),
        ALBBodyShopPrototypeWorldBootstrap::IsForbiddenLegacyAuthorityClassName(
            TEXT("LBGameMode")));
    TestFalse(TEXT("Prototype runtime remains permitted"),
        ALBBodyShopPrototypeWorldBootstrap::IsForbiddenLegacyAuthorityClassName(
            TEXT("LBBodyShopPrototypeRuntime")));
    TestFalse(TEXT("Fixture cell actor remains permitted"),
        ALBBodyShopPrototypeWorldBootstrap::IsForbiddenLegacyAuthorityClassName(
            TEXT("LBBodyShopCellActor")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPrototypePresentationContractTest,
    "LineBoss.BodyShop.Experimental.Isolation.CameraAndHUD",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPrototypePresentationContractTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("Prototype camera clamps close zoom"),
        ALBBodyShopManagementPawn::ClampPrototypeZoomDistance(1.0f), 1800.0f);
    TestEqual(TEXT("Prototype camera clamps distant zoom"),
        ALBBodyShopManagementPawn::ClampPrototypeZoomDistance(99999.0f), 16000.0f);
    TestEqual(TEXT("Prototype camera retains valid zoom"),
        ALBBodyShopManagementPawn::ClampPrototypeZoomDistance(7600.0f), 7600.0f);

    const FBox ApprovedSliceBounds(
        FVector(-6700.0f, -2200.0f, -210.0f),
        FVector(-1200.0f, -1400.0f, 210.0f));
    const FLBBodyShopCameraFocusContract ProcessFocus =
        ALBBodyShopManagementPawn::BuildFocusContract(
            ApprovedSliceBounds, FVector::ZeroVector);
    TestTrue(TEXT("Commissioned process bounds are selected"),
        ProcessFocus.bUsedProcessBounds);
    TestEqual(TEXT("Approved cells target the process centre"),
        ProcessFocus.Target, FVector(-4050.0f, -1800.0f, 180.0f));
    TestEqual(TEXT("Approved cells use the release-comparison boom"),
        ProcessFocus.ZoomDistanceCm, 3400.0f);
    TestEqual(TEXT("Release-comparison pitch is stable"),
        ProcessFocus.Rotation.Pitch, -30.0);
    TestEqual(TEXT("Release-comparison yaw is stable"),
        ProcessFocus.Rotation.Yaw, 55.0);
    TestEqual(TEXT("Release-comparison roll remains level"),
        ProcessFocus.Rotation.Roll, 0.0);
    TestEqual(TEXT("Release-comparison field of view is stable"),
        ProcessFocus.FieldOfViewDegrees, 60.0f);

    const FVector FallbackOrigin(300.0f, -700.0f, 25.0f);
    const FLBBodyShopCameraFocusContract FallbackFocus =
        ALBBodyShopManagementPawn::BuildFocusContract(
            FBox(EForceInit::ForceInit), FallbackOrigin);
    TestFalse(TEXT("An empty slice reports fallback framing"),
        FallbackFocus.bUsedProcessBounds);
    TestEqual(TEXT("An empty slice retains the bootstrap build origin"),
        FallbackFocus.Target, FallbackOrigin);
    TestEqual(TEXT("Fallback framing retains the release-comparison boom"),
        FallbackFocus.ZoomDistanceCm, 3400.0f);
    TestEqual(TEXT("Fallback framing retains release-comparison pitch"),
        FallbackFocus.Rotation.Pitch, -30.0);
    TestEqual(TEXT("Fallback framing retains release-comparison yaw"),
        FallbackFocus.Rotation.Yaw, 55.0);
    TestEqual(TEXT("Fallback framing retains release-comparison field of view"),
        FallbackFocus.FieldOfViewDegrees, 60.0f);
    TestTrue(TEXT("HUD names missing bootstrap without creating authority"),
        ALBBodyShopPrototypeHUD::BuildIsolationReadout(false, false, false, false, false)
            .Contains(TEXT("NO FACTORY AUTHORITY CREATED")));
    TestTrue(TEXT("HUD names experimental-only persistence once ready"),
        ALBBodyShopPrototypeHUD::BuildIsolationReadout(true, true, true, false, true)
            .Contains(TEXT("EXPERIMENTAL SAVE V1 ONLY")));
    return true;
}

#endif
