#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopPrototypeGameMode.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPackagedPerformanceCommandLineTest,
    "LineBoss.BodyShop.Experimental.PackagedPerformance.CommandLineGate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPackagedPerformanceCommandLineTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    FLBBodyShopPackagedPerformanceRequest Request;
    FString Reason;
    const FString Token(TEXT("0123456789abcdef0123456789abcdef"));

    TestTrue(TEXT("No request leaves packaged performance disabled"),
        ALBBodyShopPrototypeGameMode::ParsePackagedPerformanceRequest(
            TEXT(""), Request, Reason));
    TestEqual(TEXT("No request selects no view"), Request.View,
        ELBBodyShopPackagedPerformanceView::None);

    TestTrue(TEXT("Management request and safe token parse"),
        ALBBodyShopPrototypeGameMode::ParsePackagedPerformanceRequest(
            *FString::Printf(TEXT("-LineBossBodyShopPerformanceValidation=Management -LineBossBodyShopValidationToken=%s"),
                *Token), Request, Reason));
    TestEqual(TEXT("Management request selects management"), Request.View,
        ELBBodyShopPackagedPerformanceView::Management);
    TestEqual(TEXT("Performance token is retained exactly"), Request.Token, Token);

    TestTrue(TEXT("Focus request parses case-insensitively"),
        ALBBodyShopPrototypeGameMode::ParsePackagedPerformanceRequest(
            *FString::Printf(TEXT("-LineBossBodyShopPerformanceValidation=focus -LineBossBodyShopValidationToken=%s"),
                *Token), Request, Reason));
    TestEqual(TEXT("Focus request selects focus"), Request.View,
        ELBBodyShopPackagedPerformanceView::Focus);

    TestFalse(TEXT("Unknown view fails closed"),
        ALBBodyShopPrototypeGameMode::ParsePackagedPerformanceRequest(
            *FString::Printf(TEXT("-LineBossBodyShopPerformanceValidation=Wide -LineBossBodyShopValidationToken=%s"),
                *Token), Request, Reason));
    TestFalse(TEXT("Missing token fails closed"),
        ALBBodyShopPrototypeGameMode::ParsePackagedPerformanceRequest(
            TEXT("-LineBossBodyShopPerformanceValidation=Focus"), Request, Reason));
    TestFalse(TEXT("Unsafe token fails closed"),
        ALBBodyShopPrototypeGameMode::ParsePackagedPerformanceRequest(
            TEXT("-LineBossBodyShopPerformanceValidation=Focus -LineBossBodyShopValidationToken=unsafe/token/value"),
            Request, Reason));
    TestFalse(TEXT("Save/load and performance modes cannot share a process"),
        ALBBodyShopPrototypeGameMode::ParsePackagedPerformanceRequest(
            *FString::Printf(TEXT("-LineBossBodyShopPerformanceValidation=Focus -LineBossBodyShopPackageValidation=Save -LineBossBodyShopValidationToken=%s"),
                *Token), Request, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPackagedPerformanceMarkerTest,
    "LineBoss.BodyShop.Experimental.PackagedPerformance.ExactTokenedMarkers",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPackagedPerformanceMarkerTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const FString Token(TEXT("0123456789abcdef0123456789abcdef"));
    const FString Marker = ALBBodyShopPrototypeGameMode::BuildPackagedPerformanceMarker(
        ELBBodyShopPackagedPerformanceView::Focus, Token, true, TEXT("D3D12"),
        1920, 1080, 300, 25, 10, TEXT("focus_runtime_capture_v002.json"));
    TestEqual(TEXT("Packaged performance PASS marker is exact and token-bound"), Marker,
        FString::Printf(TEXT("LINE_BOSS_BODY_SHOP_PACKAGED_PERFORMANCE_LOD_V002 view=FOCUS token=%s result=PASS viewport=1920x1080 frames=300 components=25 meshes=10 rhi=D3D12 receipt=focus_runtime_capture_v002.json"),
            *Token));

    const FString FailedMarker = ALBBodyShopPrototypeGameMode::BuildPackagedPerformanceMarker(
        ELBBodyShopPackagedPerformanceView::Management, Token, false, TEXT("Null RHI"),
        1280, 720, 0, 0, 0, TEXT("none"), TEXT("bad\nreason=unsafe"));
    TestFalse(TEXT("Failed performance marker cannot contain the accepted PASS sequence"),
        FailedMarker.Contains(TEXT("result=PASS")));
    TestFalse(TEXT("Failure text cannot inject a second marker or key"),
        FailedMarker.Contains(TEXT("\n")) || FailedMarker.Contains(TEXT("reason=unsafe")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPackagedPerformanceTargetCountsTest,
    "LineBoss.BodyShop.Experimental.PackagedPerformance.TargetCounts",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPackagedPerformanceTargetCountsTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    FString Reason;
    TestTrue(TEXT("Exact three-robot 25-component ten-mesh automatic-LOD contract passes"),
        ALBBodyShopPrototypeGameMode::ValidatePackagedPerformanceTargetCounts(
            3, 25, 10, false, Reason));
    TestFalse(TEXT("A missing robot fails closed"),
        ALBBodyShopPrototypeGameMode::ValidatePackagedPerformanceTargetCounts(
            2, 25, 10, false, Reason));
    TestFalse(TEXT("A missing target component fails closed"),
        ALBBodyShopPrototypeGameMode::ValidatePackagedPerformanceTargetCounts(
            3, 24, 10, false, Reason));
    TestFalse(TEXT("A mesh-family drift fails closed"),
        ALBBodyShopPrototypeGameMode::ValidatePackagedPerformanceTargetCounts(
            3, 25, 9, false, Reason));
    TestFalse(TEXT("Any forced LOD fails closed"),
        ALBBodyShopPrototypeGameMode::ValidatePackagedPerformanceTargetCounts(
            3, 25, 10, true, Reason));
    return true;
}

#endif
