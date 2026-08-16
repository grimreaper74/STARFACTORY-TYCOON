#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryAssemblyStarterPresentationActor.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryAssemblyPresentationContractTest,
    "LineBoss.OneFactory.AssemblyStarter.Presentation.ExactNativeNinetyFiveInstanceContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryAssemblyPresentationContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    const FLBOneFactoryAssemblyLayoutState Layout =
        ULBOneFactoryAssemblyStarterLayoutLibrary::MakeCanonicalStarterLayout();
    const TArray<FLBOneFactoryAssemblyPresentationItem> Items =
        ALBOneFactoryAssemblyStarterPresentationActor::
            BuildExpectedPresentationItems(Layout);
    FString Reason;
    TestTrue(TEXT("Exact Assembly presentation contract validates"),
        ALBOneFactoryAssemblyStarterPresentationActor::
            ValidatePresentationContract(Layout, Items, Reason));
    TestEqual(TEXT("Presentation has exactly 95 visual instances"),
        Items.Num(), 95);
    TestEqual(TEXT("Presentation has exactly ten HISM batches"),
        ALBOneFactoryAssemblyStarterPresentationActor::
            GetExpectedVisualBatchCount(), 10);

    int32 ExpectedTotal = 0;
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryAssemblyPresentationBatch::SkilletCarrier);
        Value <= static_cast<int32>(
            ELBOneFactoryAssemblyPresentationBatch::StatusCube); ++Value)
    {
        ExpectedTotal += ALBOneFactoryAssemblyStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                static_cast<ELBOneFactoryAssemblyPresentationBatch>(Value));
    }
    TestEqual(TEXT("Exact per-batch counts sum to 95"), ExpectedTotal, 95);

    const TArray<FSoftObjectPath> Assets =
        ALBOneFactoryAssemblyStarterPresentationActor::
            GetRequiredNativeAssetPaths();
    TestEqual(TEXT("Eight authored plus two Engine references are exact"),
        Assets.Num(), 10);
    TestTrue(TEXT("Exact native reference allowlist validates"),
        ALBOneFactoryAssemblyStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryAssemblyStarterPresentationActor::
                    GetPresentationClassPath(), Assets, Reason));
    if (Assets.Num() == 10)
    {
        for (int32 Index = 0; Index < 8; ++Index)
        {
            TestTrue(TEXT("Authored Assembly mesh stays in frozen kit v001"),
                Assets[Index].ToString().StartsWith(TEXT(
                    "/Game/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001/")));
            TestFalse(TEXT("No authored reference contains Meshy"),
                Assets[Index].ToString().Contains(
                    TEXT("Meshy"), ESearchCase::IgnoreCase));
        }
        TestTrue(TEXT("Route mesh is exact Engine Cube"),
            Assets[8] == FSoftObjectPath(TEXT(
                "/Engine/BasicShapes/Cube.Cube")));
        TestTrue(TEXT("Semantic material is exact Engine basic material"),
            Assets[9] == FSoftObjectPath(TEXT(
                "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")));
    }

    TArray<FSoftObjectPath> Drifted = Assets;
    if (!Drifted.IsEmpty()) Drifted[0] = FSoftObjectPath(TEXT(
        "/Game/Meshy/Assembly/SM_ExternalGenerated.SM_ExternalGenerated"));
    TestFalse(TEXT("Any authored-path drift fails closed"),
        ALBOneFactoryAssemblyStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryAssemblyStarterPresentationActor::
                    GetPresentationClassPath(), Drifted, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryAssemblyPresentationConfigureAndReassignTest,
    "LineBoss.OneFactory.AssemblyStarter.Presentation.AtomicConfigureAndOperationReassignment",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryAssemblyPresentationConfigureAndReassignTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryAssemblyPresentationTest"));
    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryAssemblyStarterLayoutAuthority>()
        : nullptr;
    ALBOneFactoryAssemblyStarterPresentationActor* Presentation = World
        ? World->SpawnActor<
            ALBOneFactoryAssemblyStarterPresentationActor>() : nullptr;
    if (!TestNotNull(TEXT("Assembly data authority exists"), Authority)
        || !TestNotNull(TEXT("Assembly presentation actor exists"),
            Presentation))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    TestTrue(TEXT("Canonical snapshot configures atomically"),
        Presentation->ConfigureFromLayout(
            Authority->CaptureLayout(), Reason));
    TestTrue(TEXT("Configured actor exposes all ten batches"),
        Presentation->IsPresentationConfigured()
        && Presentation->GetVisualBatchCount() == 10);
    TestEqual(TEXT("Configured actor exposes all 95 instances"),
        Presentation->GetVisibleInstanceCount(), 95);
    TestFalse(TEXT("Presentation can never represent process WIP"),
        Presentation->RepresentsProcessWIP());

    const TArray<FLBOneFactoryAssemblyPresentationItem> BeforeItems =
        Presentation->GetConfiguredItemsForOperation(
            ELBOneFactoryAssemblyOperation::UnderbodyTorque);
    TestEqual(TEXT("Underbody torque has one visual fixture before move"),
        BeforeItems.Num(), 1);
    if (BeforeItems.Num() == 1)
    {
        TestEqual(TEXT("Underbody torque begins at position 13"),
            BeforeItems[0].StationId,
            LBOneFactoryAssemblyStarterIds::Station(13));
    }

    TestTrue(TEXT("Compatible operation reassigns atomically in data"),
        Authority->AssignOperation(
            ELBOneFactoryAssemblyOperation::UnderbodyTorque,
            LBOneFactoryAssemblyStarterIds::Station(14), Reason));
    TestTrue(TEXT("Reassigned snapshot rematerialises atomically"),
        Presentation->ConfigureFromLayout(
            Authority->CaptureLayout(), Reason));
    const TArray<FLBOneFactoryAssemblyPresentationItem> AfterItems =
        Presentation->GetConfiguredItemsForOperation(
            ELBOneFactoryAssemblyOperation::UnderbodyTorque);
    TestEqual(TEXT("Underbody torque still has exactly one fixture"),
        AfterItems.Num(), 1);
    if (AfterItems.Num() == 1)
    {
        TestEqual(TEXT("Fixture follows its authoritative operation to 14"),
            AfterItems[0].StationId,
            LBOneFactoryAssemblyStarterIds::Station(14));
    }
    TestEqual(TEXT("Presentation revision follows data revision"),
        Presentation->GetConfiguredLayoutRevision(),
        Authority->CaptureLayout().Revision);
    TestEqual(TEXT("Reassignment preserves exact instance inventory"),
        Presentation->GetVisibleInstanceCount(), 95);

    FLBOneFactoryAssemblyLayoutState Invalid = Authority->CaptureLayout();
    Invalid.Stations.RemoveAt(0);
    TestFalse(TEXT("Incomplete layout clears and rejects presentation"),
        Presentation->ConfigureFromLayout(Invalid, Reason));
    TestFalse(TEXT("Failed configuration stays visibly empty"),
        Presentation->IsPresentationConfigured());
    TestEqual(TEXT("Failed configuration leaves zero instances"),
        Presentation->GetVisibleInstanceCount(), 0);

    World->DestroyWorld(false);
    return true;
}

#endif

