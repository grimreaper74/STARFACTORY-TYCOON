#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopPrototypeGameMode.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPackagedValidationCommandLineTest,
    "LineBoss.BodyShop.Experimental.PackageValidation.CommandLineGate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPackagedValidationCommandLineTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    FLBBodyShopPackagedValidationRequest Request;
    FString Reason;
    TestTrue(TEXT("No command-line request leaves the bridge disabled"),
        ALBBodyShopPrototypeGameMode::ParsePackagedValidationRequest(TEXT(""), Request, Reason));
    TestEqual(TEXT("No request selects no packaged mode"), Request.Mode,
        ELBBodyShopPackagedValidationMode::None);

    const FString Token(TEXT("0123456789abcdef0123456789abcdef"));
    TestTrue(TEXT("Exact save request and safe token parse"),
        ALBBodyShopPrototypeGameMode::ParsePackagedValidationRequest(
            *FString::Printf(TEXT("-LineBossBodyShopPackageValidation=Save -LineBossBodyShopValidationToken=%s"), *Token),
            Request, Reason));
    TestEqual(TEXT("Save request selects save mode"), Request.Mode,
        ELBBodyShopPackagedValidationMode::Save);
    TestEqual(TEXT("Safe token is retained exactly"), Request.Token, Token);

    TestTrue(TEXT("Exact load request parses case-insensitively"),
        ALBBodyShopPrototypeGameMode::ParsePackagedValidationRequest(
            *FString::Printf(TEXT("-LineBossBodyShopPackageValidation=load -LineBossBodyShopValidationToken=%s"), *Token),
            Request, Reason));
    TestEqual(TEXT("Load request selects load mode"), Request.Mode,
        ELBBodyShopPackagedValidationMode::Load);

    TestFalse(TEXT("Unknown packaged mode fails closed"),
        ALBBodyShopPrototypeGameMode::ParsePackagedValidationRequest(
            *FString::Printf(TEXT("-LineBossBodyShopPackageValidation=Smoke -LineBossBodyShopValidationToken=%s"), *Token),
            Request, Reason));
    TestFalse(TEXT("A missing token fails closed"),
        ALBBodyShopPrototypeGameMode::ParsePackagedValidationRequest(
            TEXT("-LineBossBodyShopPackageValidation=Save"), Request, Reason));
    TestFalse(TEXT("Unsafe token characters fail closed"),
        ALBBodyShopPrototypeGameMode::ParsePackagedValidationRequest(
            TEXT("-LineBossBodyShopPackageValidation=Load -LineBossBodyShopValidationToken=unsafe/token/value"),
            Request, Reason));
    TestFalse(TEXT("A short token fails closed"),
        ALBBodyShopPrototypeGameMode::ParsePackagedValidationRequest(
            TEXT("-LineBossBodyShopPackageValidation=Load -LineBossBodyShopValidationToken=short"),
            Request, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPackagedValidationMarkerTest,
    "LineBoss.BodyShop.Experimental.PackageValidation.ExactTokenedMarkers",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPackagedValidationMarkerTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const FString Token(TEXT("0123456789abcdef0123456789abcdef"));
    const FString SaveMarker = ALBBodyShopPrototypeGameMode::BuildPackagedValidationMarker(
        ELBBodyShopPackagedValidationMode::Save, Token, true, TEXT("WELDING_UNDERBODY"), 1, 1);
    const FString LoadMarker = ALBBodyShopPrototypeGameMode::BuildPackagedValidationMarker(
        ELBBodyShopPackagedValidationMode::Load, Token, true, TEXT("WELDING_UNDERBODY"), 1, 1);
    const FString FailedMarker = ALBBodyShopPrototypeGameMode::BuildPackagedValidationMarker(
        ELBBodyShopPackagedValidationMode::Load, Token, false, TEXT("FAULTED"), 0, 0,
        TEXT("bad\nreason=unsafe"));

    TestEqual(TEXT("Save marker is exact and token-bound"), SaveMarker,
        FString::Printf(TEXT("LINE_BOSS_BODY_SHOP_PACKAGE_VALIDATION_V001 phase=SAVE token=%s result=PASS stage=WELDING_UNDERBODY logical_wip=1 visible_wip=1 save_slot=LineBoss_BodyShopExperimental_v001"), *Token));
    TestEqual(TEXT("Load marker is exact and token-bound"), LoadMarker,
        FString::Printf(TEXT("LINE_BOSS_BODY_SHOP_PACKAGE_VALIDATION_V001 phase=LOAD token=%s result=PASS stage=WELDING_UNDERBODY logical_wip=1 visible_wip=1 save_slot=LineBoss_BodyShopExperimental_v001"), *Token));
    TestFalse(TEXT("A failed marker can never contain the accepted PASS sequence"),
        FailedMarker.Contains(TEXT("result=PASS")));
    TestFalse(TEXT("Failure diagnostics cannot inject another marker line"),
        FailedMarker.Contains(TEXT("\n")) || FailedMarker.Contains(TEXT("reason=unsafe")));
    return true;
}

#endif
