#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryBodyWeldStarterPresentationActor.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryBodyWeldPresentationContractTest,
    "LineBoss.OneFactory.BodyWeldStarter.Presentation.ExactNativeFourHundredSixtyNineInstanceContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryBodyWeldPresentationContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    const FLBOneFactoryBodyWeldLayoutState Layout =
        ULBOneFactoryBodyWeldStarterLayoutLibrary::
            MakeCanonicalStarterLayout();
    const TArray<FLBOneFactoryBodyWeldPresentationItem> Items =
        ALBOneFactoryBodyWeldStarterPresentationActor::
            BuildExpectedPresentationItems(Layout);
    FString Reason;
    TestTrue(TEXT("Exact Body/Weld presentation contract validates"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            ValidatePresentationContract(Layout, Items, Reason));
    TestEqual(TEXT("Canonical presentation has exactly 469 instances"),
        Items.Num(), 469);
    TestEqual(TEXT("Canonical count helper remains frozen at 469"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetCanonicalVisibleInstanceCount(), 469);
    TestEqual(TEXT("Presentation has exactly 24 HISM batches"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedVisualBatchCount(), 24);
    TestEqual(TEXT("All 36 large robots have a native base"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedInstanceCountForBatch(Layout,
                ELBOneFactoryBodyWeldPresentationBatch::RobotBase), 36);
    TestEqual(TEXT("Canonical duty assignment exposes 16 native C-guns"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedInstanceCountForBatch(Layout,
                ELBOneFactoryBodyWeldPresentationBatch::RobotOpenCGun),
        16);
    TestEqual(TEXT("All 18 programmes have a visual fixture"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedInstanceCountForBatch(Layout,
                ELBOneFactoryBodyWeldPresentationBatch::
                    ProgrammeFixtureCube), 18);
    TestEqual(TEXT("All 17 links have one exact floor route"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedInstanceCountForBatch(Layout,
                ELBOneFactoryBodyWeldPresentationBatch::FloorRouteCube),
        17);

    int32 ExpectedTotal = 0;
    for (int32 Value = 0;
        Value < ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedVisualBatchCount(); ++Value)
    {
        ExpectedTotal += ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedInstanceCountForBatch(Layout,
                static_cast<ELBOneFactoryBodyWeldPresentationBatch>(Value));
    }
    TestEqual(TEXT("Exact per-batch counts sum to 469"),
        ExpectedTotal, 469);

    const TArray<FSoftObjectPath> Assets =
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetRequiredNativeAssetPaths();
    TestEqual(TEXT("24 mesh bindings plus one material are exact"),
        Assets.Num(), 25);
    TestTrue(TEXT("Exact Body/Weld native allowlist validates"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryBodyWeldStarterPresentationActor::
                    GetPresentationClassPath(), Assets, Reason));
    if (Assets.Num() == 25)
    {
        for (int32 Index = 0; Index < 8; ++Index)
        {
            TestTrue(TEXT("Robot reference stays in native robot kit v001"),
                Assets[Index].ToString().StartsWith(TEXT(
                    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/")));
        }
        for (int32 Index = 8; Index < 20; ++Index)
        {
            TestTrue(TEXT("Support reference stays in native support kit v002"),
                Assets[Index].ToString().StartsWith(TEXT(
                    "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/")));
        }
        for (int32 Index = 20; Index < 25; ++Index)
        {
            TestTrue(TEXT("Semantic dependency stays in Engine BasicShapes"),
                Assets[Index].ToString().StartsWith(
                    TEXT("/Engine/BasicShapes/")));
        }
        for (const FSoftObjectPath& Asset : Assets)
        {
            TestFalse(TEXT("No Body/Weld reference contains Meshy"),
                Asset.ToString().Contains(
                    TEXT("Meshy"), ESearchCase::IgnoreCase));
            TestFalse(TEXT("No legacy underbody-slice art is referenced"),
                Asset.ToString().Contains(
                    TEXT("BodyShopUnderbodySlice"),
                    ESearchCase::IgnoreCase));
        }
    }

    TArray<FSoftObjectPath> Drifted = Assets;
    if (!Drifted.IsEmpty()) Drifted[0] = FSoftObjectPath(TEXT(
        "/Game/Meshy/Weld/SM_ExternalGenerated.SM_ExternalGenerated"));
    TestFalse(TEXT("Any Body/Weld authored-path drift fails closed"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryBodyWeldStarterPresentationActor::
                    GetPresentationClassPath(), Drifted, Reason));

    TArray<FLBOneFactoryBodyWeldPresentationItem> WIPClaim = Items;
    if (!WIPClaim.IsEmpty()) WIPClaim[0].bRepresentsProcessWIP = true;
    TestFalse(TEXT("Any presentation WIP claim fails closed"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            ValidatePresentationContract(Layout, WIPClaim, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryBodyWeldPresentationConfigureAndReassignTest,
    "LineBoss.OneFactory.BodyWeldStarter.Presentation.AtomicConfigureProgrammeAndRobotRoleReassignment",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryBodyWeldPresentationConfigureAndReassignTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryBodyWeldPresentationTest"));
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryBodyWeldStarterLayoutAuthority>()
        : nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* Presentation = World
        ? World->SpawnActor<
            ALBOneFactoryBodyWeldStarterPresentationActor>() : nullptr;
    if (!TestNotNull(TEXT("Body/Weld data authority exists"), Authority)
        || !TestNotNull(TEXT("Body/Weld presentation actor exists"),
            Presentation))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    TestTrue(TEXT("Canonical Body/Weld snapshot configures atomically"),
        Presentation->ConfigureFromLayout(
            Authority->CaptureLayout(), Reason));
    TestTrue(TEXT("Configured actor exposes all 24 batches"),
        Presentation->IsPresentationConfigured()
        && Presentation->GetVisualBatchCount() == 24);
    TestEqual(TEXT("Configured actor exposes all 469 canonical instances"),
        Presentation->GetVisibleInstanceCount(), 469);
    TestFalse(TEXT("Presentation can never represent process WIP"),
        Presentation->RepresentsProcessWIP());

    const FName Position2 =
        LBOneFactoryBodyWeldStarterIds::Station(2);
    TArray<FLBOneFactoryBodyWeldPresentationItem> LeftRobot =
        Presentation->GetConfiguredRobotItems(Position2,
            ELBOneFactoryBodyWeldRobotSide::Left);
    TArray<FLBOneFactoryBodyWeldPresentationItem> RightRobot =
        Presentation->GetConfiguredRobotItems(Position2,
            ELBOneFactoryBodyWeldRobotSide::Right);
    TestEqual(TEXT("Geometry robot has seven links plus role marker"),
        LeftRobot.Num(), 8);
    TestEqual(TEXT("Spot robot also has one C-gun"),
        RightRobot.Num(), 9);
    for (const FLBOneFactoryBodyWeldPresentationItem& Item : LeftRobot)
    {
        TestEqual(TEXT("Left robot items expose geometry-clamp duty"),
            Item.RobotRole,
            ELBOneFactoryBodyWeldRobotRole::GeometryClamp);
    }
    for (const FLBOneFactoryBodyWeldPresentationItem& Item : RightRobot)
    {
        TestEqual(TEXT("Right robot items expose spot-weld duty"),
            Item.RobotRole,
            ELBOneFactoryBodyWeldRobotRole::SpotWelding);
    }

    TestTrue(TEXT("Mirrored robot duties swap atomically in data"),
        Authority->AssignRobotPairRoles(Position2,
            ELBOneFactoryBodyWeldRobotRole::SpotWelding,
            ELBOneFactoryBodyWeldRobotRole::GeometryClamp, Reason));
    TestTrue(TEXT("Role-swapped snapshot rematerialises atomically"),
        Presentation->ConfigureFromLayout(
            Authority->CaptureLayout(), Reason));
    LeftRobot = Presentation->GetConfiguredRobotItems(Position2,
        ELBOneFactoryBodyWeldRobotSide::Left);
    RightRobot = Presentation->GetConfiguredRobotItems(Position2,
        ELBOneFactoryBodyWeldRobotSide::Right);
    TestEqual(TEXT("C-gun follows spot duty to the left side"),
        LeftRobot.Num(), 9);
    TestEqual(TEXT("Geometry duty moves to the right side without a tool"),
        RightRobot.Num(), 8);
    TestEqual(TEXT("Role swap preserves exact canonical inventory"),
        Presentation->GetVisibleInstanceCount(), 469);

    const TArray<FLBOneFactoryBodyWeldPresentationItem> BeforeProgramme =
        Presentation->GetConfiguredItemsForProgramme(
            ELBOneFactoryBodyWeldProgramme::FrontUnderbodyGeometry);
    TestEqual(TEXT("Front underbody starts with one fixture"),
        BeforeProgramme.Num(), 1);
    if (BeforeProgramme.Num() == 1)
    {
        TestEqual(TEXT("Front underbody fixture begins at position 2"),
            BeforeProgramme[0].StationId, Position2);
    }
    TestTrue(TEXT("Compatible Body/Weld programme reassigns in data"),
        Authority->AssignProgramme(
            ELBOneFactoryBodyWeldProgramme::FrontUnderbodyGeometry,
            LBOneFactoryBodyWeldStarterIds::Station(3), Reason));
    TestTrue(TEXT("Programme-reassigned snapshot rematerialises"),
        Presentation->ConfigureFromLayout(
            Authority->CaptureLayout(), Reason));
    const TArray<FLBOneFactoryBodyWeldPresentationItem> AfterProgramme =
        Presentation->GetConfiguredItemsForProgramme(
            ELBOneFactoryBodyWeldProgramme::FrontUnderbodyGeometry);
    TestEqual(TEXT("Reassigned programme still has one fixture"),
        AfterProgramme.Num(), 1);
    if (AfterProgramme.Num() == 1)
    {
        TestEqual(TEXT("Fixture follows authority to position 3"),
            AfterProgramme[0].StationId,
            LBOneFactoryBodyWeldStarterIds::Station(3));
    }
    TestEqual(TEXT("Presentation revision follows Body/Weld data"),
        Presentation->GetConfiguredLayoutRevision(),
        Authority->CaptureLayout().Revision);

    FLBOneFactoryBodyWeldLayoutState Invalid = Authority->CaptureLayout();
    Invalid.Stations.RemoveAt(0);
    TestFalse(TEXT("Incomplete Body/Weld layout clears presentation"),
        Presentation->ConfigureFromLayout(Invalid, Reason));
    TestFalse(TEXT("Failed Body/Weld configuration stays empty"),
        Presentation->IsPresentationConfigured());
    TestEqual(TEXT("Failed configuration leaves zero instances"),
        Presentation->GetVisibleInstanceCount(), 0);

    World->DestroyWorld(false);
    return true;
}

#endif
