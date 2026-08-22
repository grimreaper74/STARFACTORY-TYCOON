#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryBodyWeldStarterPresentationActor.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryBodyWeldPresentationContractTest,
    "LineBoss.OneFactory.BodyWeldStarter.Presentation.ClosureSubassemblyInstanceContract",
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
    TestEqual(TEXT("Canonical presentation has exactly 600 instances"),
        Items.Num(), 600);
    TestEqual(TEXT("Canonical count helper remains frozen at 600"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetCanonicalVisibleInstanceCount(), 600);
    TestEqual(TEXT("Presentation has exactly 29 HISM batches"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedVisualBatchCount(), 29);
    TestEqual(TEXT("All 36 large robots have a native base"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedInstanceCountForBatch(Layout,
                ELBOneFactoryBodyWeldPresentationBatch::RobotBase), 36);
    TestEqual(TEXT("Canonical duty assignment exposes 16 native C-guns"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedInstanceCountForBatch(Layout,
                ELBOneFactoryBodyWeldPresentationBatch::RobotOpenCGun),
        16);
    TestEqual(TEXT("All 20 non-welding robots carry the panel-pick tool"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedInstanceCountForBatch(Layout,
                ELBOneFactoryBodyWeldPresentationBatch::RobotPanelPickTool),
        20);
    TestEqual(TEXT("Fifteen framing programmes use the framing fixture"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedInstanceCountForBatch(Layout,
                ELBOneFactoryBodyWeldPresentationBatch::
                    ProgrammeFixtureFraming), 15);
    TestEqual(TEXT("Three underbody programmes use the underbody fixture"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetExpectedInstanceCountForBatch(Layout,
                ELBOneFactoryBodyWeldPresentationBatch::
                    ProgrammeFixtureUnderbody), 3);
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
    TestEqual(TEXT("Exact per-batch counts sum to 600"),
        ExpectedTotal, 600);

    const auto HasNamedSubassemblyRack = [&Items](const TCHAR* Suffix)
    {
        return Items.ContainsByPredicate([Suffix](
            const FLBOneFactoryBodyWeldPresentationItem& Item)
        {
            return Item.PresentationId.ToString().EndsWith(Suffix,
                ESearchCase::CaseSensitive)
                && Item.Batch == ELBOneFactoryBodyWeldPresentationBatch::
                    PanelStillageFull;
        });
    };
    TestTrue(TEXT("Door-left sub-assembly rack is visible"),
        HasNamedSubassemblyRack(TEXT("DOOR_SUBASSEMBLY_LEFT")));
    TestTrue(TEXT("Door-right sub-assembly rack is visible"),
        HasNamedSubassemblyRack(TEXT("DOOR_SUBASSEMBLY_RIGHT")));
    TestTrue(TEXT("Bonnet sub-assembly rack is visible"),
        HasNamedSubassemblyRack(TEXT("BONNET_SUBASSEMBLY")));
    TestTrue(TEXT("Tailgate sub-assembly rack is visible"),
        HasNamedSubassemblyRack(TEXT("TAILGATE_SUBASSEMBLY")));

    const TArray<FSoftObjectPath> Assets =
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetRequiredNativeAssetPaths();
    TestEqual(TEXT("29 mesh bindings plus one material are exact"),
        Assets.Num(), 30);
    TestTrue(TEXT("Exact Body/Weld native allowlist validates"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryBodyWeldStarterPresentationActor::
                    GetPresentationClassPath(), Assets, Reason));
    if (Assets.Num() == 30)
    {
        for (int32 Index = 0; Index < 8; ++Index)
        {
            TestTrue(TEXT("Robot reference stays in native robot kit v001"),
                Assets[Index].ToString().StartsWith(TEXT(
                    "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/")));
        }
        TestEqual(TEXT("The panel-pick tool binds the exact slice asset"),
            Assets[8].ToString(), FString(TEXT(
                "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001.SM_LB_BodyShopTool_PanelPick8Cup_v001")));
        for (int32 Index = 9; Index < 12; ++Index)
        {
            TestTrue(TEXT("Dress reference stays in the modular robot kit v020"),
                Assets[Index].ToString().StartsWith(TEXT(
                    "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/")));
        }
        for (int32 Index = 12; Index < 24; ++Index)
        {
            TestTrue(TEXT("Support reference stays in native support kit v002"),
                Assets[Index].ToString().StartsWith(TEXT(
                    "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/")));
        }
        TestEqual(TEXT("The framing fixture binds the exact runtime asset"),
            Assets[24].ToString(), FString(TEXT(
                "/Game/LineBoss/Candidates/WeldShop/BodyWeldLine/Runtime_v001/Fixture/SM_LB_BodyWeld_FramingFixture_v001.SM_LB_BodyWeld_FramingFixture_v001")));
        TestEqual(TEXT("The underbody fixture binds the exact slice asset"),
            Assets[25].ToString(), FString(TEXT(
                "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Fixture/SM_LB_BodyShop_UnderbodyFixture_v001.SM_LB_BodyShop_UnderbodyFixture_v001")));
        for (int32 Index = 26; Index < 30; ++Index)
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
            TestFalse(TEXT("No superseded weld-robot runtime art is referenced"),
                Asset.ToString().Contains(
                    TEXT("Robots/WeldRobotRuntime"),
                    ESearchCase::IgnoreCase));
        }
    }

    // The FK pose seam matches the pack's own contact validation values.
    TArray<float> LeftPose;
    TestTrue(TEXT("Left contact pose resolves for target 1"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetContactProcessPoseJointAngles(
                ELBOneFactoryBodyWeldRobotSide::Left, 1, LeftPose));
    if (LeftPose.Num() == 6)
    {
        const float Expected[6] = { 55.0f, -55.947736f, 70.469811f,
            0.000001f, 61.000413f, -0.000005f };
        for (int32 JointIndex = 0; JointIndex < 6; ++JointIndex)
        {
            TestTrue(TEXT("Left pose matches contact_fk_validation_v001"),
                FMath::IsNearlyEqual(LeftPose[JointIndex],
                    Expected[JointIndex], 1.e-4f));
        }
    }
    TArray<float> RightPose;
    TestTrue(TEXT("Right contact pose resolves for target 1"),
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetContactProcessPoseJointAngles(
                ELBOneFactoryBodyWeldRobotSide::Right, 1, RightPose));
    if (LeftPose.Num() == 6 && RightPose.Num() == 6)
    {
        for (int32 JointIndex = 0; JointIndex < 6; ++JointIndex)
        {
            const float Mirror =
                (JointIndex == 0 || JointIndex == 3 || JointIndex == 5)
                    ? -LeftPose[JointIndex] : LeftPose[JointIndex];
            TestTrue(TEXT("Right pose mirrors J1/J4/J6"),
                FMath::IsNearlyEqual(RightPose[JointIndex], Mirror, 1.e-4f));
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
    TestTrue(TEXT("Presentation spawns hidden until a snapshot commits"),
        Presentation->IsHidden());
    TestTrue(TEXT("Canonical Body/Weld snapshot configures atomically"),
        Presentation->ConfigureFromLayout(
            Authority->CaptureLayout(), Reason));
    TestTrue(TEXT("Configured actor exposes all 29 batches"),
        Presentation->IsPresentationConfigured()
        && Presentation->GetVisualBatchCount() == 29);
    TestEqual(TEXT("Configured actor exposes all 600 canonical instances"),
        Presentation->GetVisibleInstanceCount(), 600);
    TestFalse(TEXT("Configured presentation is unhidden"),
        Presentation->IsHidden());
    {
        TArray<UHierarchicalInstancedStaticMeshComponent*> BatchComponents;
        Presentation->GetComponents<UHierarchicalInstancedStaticMeshComponent>(
            BatchComponents);
        for (const UHierarchicalInstancedStaticMeshComponent* Component :
            BatchComponents)
        {
            if (Component && Component->GetInstanceCount() > 0)
            {
                TestTrue(TEXT("Populated batch is visible"),
                    Component->IsVisible() && !Component->bHiddenInGame);
            }
        }
    }
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
    TestEqual(TEXT("Geometry robot has seven links, tool, dress trio and role marker"),
        LeftRobot.Num(), 12);
    TestEqual(TEXT("Spot robot has seven links, C-gun, dress trio and role marker"),
        RightRobot.Num(), 12);
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
    TestEqual(TEXT("Spot duty on the left still shows twelve items"),
        LeftRobot.Num(), 12);
    TestEqual(TEXT("Geometry duty on the right still shows twelve items"),
        RightRobot.Num(), 12);
    auto CountBatch = [](
        const TArray<FLBOneFactoryBodyWeldPresentationItem>& RobotItems,
        const ELBOneFactoryBodyWeldPresentationBatch Batch)
    {
        int32 Count = 0;
        for (const FLBOneFactoryBodyWeldPresentationItem& Item : RobotItems)
        {
            if (Item.Batch == Batch) ++Count;
        }
        return Count;
    };
    TestEqual(TEXT("C-gun follows spot duty to the left side"),
        CountBatch(LeftRobot,
            ELBOneFactoryBodyWeldPresentationBatch::RobotOpenCGun), 1);
    TestEqual(TEXT("Left side carries no panel-pick tool"),
        CountBatch(LeftRobot,
            ELBOneFactoryBodyWeldPresentationBatch::RobotPanelPickTool), 0);
    TestEqual(TEXT("Panel-pick follows geometry duty to the right side"),
        CountBatch(RightRobot,
            ELBOneFactoryBodyWeldPresentationBatch::RobotPanelPickTool), 1);
    TestEqual(TEXT("Right side carries no C-gun"),
        CountBatch(RightRobot,
            ELBOneFactoryBodyWeldPresentationBatch::RobotOpenCGun), 0);
    TestEqual(TEXT("Role swap preserves exact canonical inventory"),
        Presentation->GetVisibleInstanceCount(), 600);

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
    TestTrue(TEXT("Failed configuration re-hides the actor"),
        Presentation->IsHidden());

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryBodyWeldCookManifestContractTest,
    "LineBoss.OneFactory.BodyWeldStarter.Presentation.CookManifestCoversEveryFrozenRoot",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryBodyWeldCookManifestContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    // The frozen presentation resolves everything by path string, which the
    // cooker cannot see: only these always-cook roots keep the weld shop
    // alive in a package. Mirrors FLBCoilPreparationCookManifestContractTest.
    const FString ConfigPath =
        FPaths::ProjectConfigDir() / TEXT("DefaultGame.ini");
    FString ConfigContents;
    TestTrue(TEXT("Project packaging configuration is readable"),
        FFileHelper::LoadFileToString(ConfigContents, *ConfigPath));

    const TCHAR* RequiredCookRoots[] =
    {
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyWeldLine/Runtime_v001"),
        TEXT("/Engine/BasicShapes")
    };
    for (const TCHAR* Root : RequiredCookRoots)
    {
        TestTrue(FString::Printf(
            TEXT("Cook manifest includes frozen weld root %s"), Root),
            ConfigContents.Contains(Root));
    }

    // Every frozen binding must also exist as a real asset on disk, so a
    // deleted or moved asset fails here rather than in a packaged run.
    for (const FSoftObjectPath& Asset :
        ALBOneFactoryBodyWeldStarterPresentationActor::
            GetRequiredNativeAssetPaths())
    {
        const FString Path = Asset.ToString();
        if (!Path.StartsWith(TEXT("/Game/")))
        {
            continue;
        }
        FString PackagePath = Path;
        int32 DotIndex = INDEX_NONE;
        if (PackagePath.FindChar(TEXT('.'), DotIndex))
        {
            PackagePath.LeftInline(DotIndex);
        }
        const FString FilePath = FPaths::ProjectContentDir()
            / PackagePath.RightChop(6) + TEXT(".uasset");
        TestTrue(FString::Printf(
            TEXT("Frozen weld binding exists on disk: %s"), *Path),
            FPaths::FileExists(FilePath));
    }
    return true;
}

#endif
