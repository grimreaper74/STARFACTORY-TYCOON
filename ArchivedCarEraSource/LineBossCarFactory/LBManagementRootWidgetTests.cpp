#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "InputCoreTypes.h"
#include "LBControlRoomHUD.h"
#include "LBFactoryBrandSubsystem.h"
#include "LBManagementRootWidget.h"

namespace
{
class FScopedModernManagementTestWorld
{
public:
    explicit FScopedModernManagementTestWorld(const TCHAR* WorldName)
    {
        if (!GEngine) return;
        World = UWorld::CreateWorld(EWorldType::Game, false, WorldName);
        if (!World) return;
        FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        World->InitializeActorsForPlay(FURL());
    }

    ~FScopedModernManagementTestWorld()
    {
        if (!World || !GEngine) return;
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
    }

    UWorld* Get() const { return World; }

private:
    UWorld* World = nullptr;
};

bool CompleteDefaultFactoryIdentity(UWorld* World)
{
    ULBFactoryBrandSubsystem* Brand = World
        ? World->GetSubsystem<ULBFactoryBrandSubsystem>() : nullptr;
    return Brand && Brand->CompleteInitialSetup();
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementRootWidgetCanonicalStagesTest,
    "LineBoss.Management.UMG.CanonicalSixStageContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRootWidgetCanonicalStagesTest::RunTest(const FString& Parameters)
{
    const TArray<FName> Ids = ULBManagementRootWidget::GetCanonicalProductionStageIds();
    TestEqual(TEXT("The shell exposes exactly six stable production stages"),
        Ids.Num(), ULBManagementRootWidget::ProductionStageCount);
    const FName Expected[] = {
        TEXT("COIL_INTAKE"), TEXT("BLANK_BUFFER"), TEXT("TRANSFER_PRESS"),
        TEXT("PANEL_STILLAGES"), TEXT("BODY_WELD"), TEXT("ED_COAT")};
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Expected); ++Index)
        TestEqual(FString::Printf(TEXT("Stage %d retains its canonical ID"), Index),
            Ids[Index], Expected[Index]);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementRootWidgetCanonicalDestinationsTest,
    "LineBoss.Management.UMG.CanonicalSevenDestinationContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRootWidgetCanonicalDestinationsTest::RunTest(
    const FString& Parameters)
{
    const TArray<FName> Destinations =
        ULBManagementRootWidget::GetCanonicalManagementDestinationIds();
    const FName Expected[] = {
        TEXT("FACTORY"), TEXT("BUILD"), TEXT("ORDERS"), TEXT("ASSETS"),
        TEXT("MAINTENANCE"), TEXT("RESEARCH"), TEXT("ANALYTICS")};
    TestEqual(TEXT("The compact shell exposes every management destination"),
        Destinations.Num(), ULBManagementRootWidget::ManagementDestinationCount);
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Expected); ++Index)
        TestEqual(FString::Printf(TEXT("Destination %d retains its canonical ID"),
            Index), Destinations[Index], Expected[Index]);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementRootWidgetGameplayKeysStayOutsideUITest,
    "LineBoss.Management.UMG.GameplayKeysStayOutsideUI",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRootWidgetGameplayKeysStayOutsideUITest::RunTest(
    const FString& Parameters)
{
    const FKey GameplayKeys[] = { EKeys::W, EKeys::A, EKeys::S, EKeys::D,
        EKeys::Q, EKeys::E, EKeys::SpaceBar, EKeys::Home };
    for (const FKey& Key : GameplayKeys)
        TestTrue(FString::Printf(TEXT("%s remains owned by gameplay"),
            *Key.GetDisplayName().ToString()),
            ULBManagementRootWidget::IsReservedGameplayKey(Key));

    TestFalse(TEXT("Arrow navigation remains available to the HUD"),
        ULBManagementRootWidget::IsReservedGameplayKey(EKeys::Left));
    TestFalse(TEXT("Enter remains available to the HUD"),
        ULBManagementRootWidget::IsReservedGameplayKey(EKeys::Enter));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementRootWidgetCairnwellLogoTest,
    "LineBoss.Management.UMG.CairnwellV002LogoAsset",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRootWidgetCairnwellLogoTest::RunTest(const FString& Parameters)
{
    const FSoftObjectPath LogoPath =
        ULBManagementRootWidget::GetBrandLogoPath();
    TestEqual(TEXT("The HUD uses the approved Cairnwell v002 logo path"),
        LogoPath.ToString(), FString(TEXT("/Game/LineBoss/Brand/Cairnwell/Candidate_v002/T_Cairnwell_PrimaryLogo_v002.T_Cairnwell_PrimaryLogo_v002")));
    UTexture2D* Logo = Cast<UTexture2D>(LogoPath.TryLoad());
    TestNotNull(TEXT("The approved Cairnwell v002 logo loads"), Logo);
    if (Logo)
    {
        const FIntPoint ImportedSize = Logo->GetImportedSize();
        TestEqual(TEXT("The approved logo retains its source width"),
            ImportedSize.X, 2400);
        TestEqual(TEXT("The approved logo retains its source height"),
            ImportedSize.Y, 640);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementRootWidgetTruthfulTelemetryTest,
    "LineBoss.Management.UMG.TruthfulStatusConnectorAndThroughputPolicy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRootWidgetTruthfulTelemetryTest::RunTest(
    const FString& Parameters)
{
    FLBManagementStagePresentation Upstream;
    FLBManagementStagePresentation Downstream;
    TestFalse(TEXT("An uninstalled process has no status telemetry dot"),
        ULBManagementRootWidget::ShouldShowStageStatusDot(Upstream));
    TestFalse(TEXT("A planned connection is not highlighted as live"),
        ULBManagementRootWidget::ShouldHighlightStageConnector(
            Upstream, Downstream));

    Upstream.bInstalled = true;
    TestTrue(TEXT("An installed process exposes its live status dot"),
        ULBManagementRootWidget::ShouldShowStageStatusDot(Upstream));
    TestFalse(TEXT("One installed endpoint cannot imply a live connection"),
        ULBManagementRootWidget::ShouldHighlightStageConnector(
            Upstream, Downstream));
    Downstream.bInstalled = true;
    TestTrue(TEXT("Both installed endpoints make the connector live"),
        ULBManagementRootWidget::ShouldHighlightStageConnector(
            Upstream, Downstream));

    TestFalse(TEXT("Zero is not invented as a measured throughput value"),
        ULBManagementRootWidget::HasTruthfulThroughput(0.0));
    TestFalse(TEXT("Negative throughput is invalid telemetry"),
        ULBManagementRootWidget::HasTruthfulThroughput(-1.0));
    TestTrue(TEXT("A positive measured throughput is presentable"),
        ULBManagementRootWidget::HasTruthfulThroughput(14.2));
    TestEqual(TEXT("Six stages own exactly five canonical connectors"),
        ULBManagementRootWidget::ProductionConnectorCount, 5);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementRootWidgetNativeProductionSchematicPolicyTest,
    "LineBoss.Management.UMG.NativeProductionSchematicPolicy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRootWidgetNativeProductionSchematicPolicyTest::RunTest(const FString& Parameters)
{
    const TArray<FName> Ids = ULBManagementRootWidget::GetCanonicalProductionStageIds();
    for (const FName Id : Ids)
    {
        TestTrue(FString::Printf(TEXT("%s deliberately uses a native schematic"),
            *Id.ToString()), ULBManagementRootWidget::GetStageThumbnailPath(Id).IsNull());
    }
    TestTrue(TEXT("Unknown stages remain visibly unresolved"),
        ULBManagementRootWidget::GetStageThumbnailPath(TEXT("INVENTED_STAGE")).IsNull());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementRootWidgetResponsiveMetricsTest,
    "LineBoss.Management.UMG.ResponsiveMetrics720p1080p",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRootWidgetResponsiveMetricsTest::RunTest(const FString& Parameters)
{
    const FLBManagementShellLayoutMetrics At720 =
        ULBManagementRootWidget::CalculateLayoutMetrics(FVector2D(1280.0f, 720.0f));
    const FLBManagementShellLayoutMetrics At1080 =
        ULBManagementRootWidget::CalculateLayoutMetrics(FVector2D(1920.0f, 1080.0f));
    TestTrue(TEXT("720p uses compact presentation"), At720.bCompact);
    TestFalse(TEXT("1080p uses full presentation"), At1080.bCompact);
    TestTrue(TEXT("720p scale remains readable"), At720.UIScale >= 2.0f / 3.0f);
    TestTrue(TEXT("1080p retains the one-to-one visual target"),
        FMath::IsNearlyEqual(At1080.UIScale, 1.0f));
    TestTrue(TEXT("The 720p tray leaves the factory view visible"),
        At720.FlowTrayHeight < At720.ViewportSize.Y * 0.40f);
    TestTrue(TEXT("The 1080p tray leaves the factory view visible"),
        At1080.FlowTrayHeight < At1080.ViewportSize.Y * 0.40f);
    TestTrue(TEXT("The full layout has a larger inspector"),
        At1080.DetailWidth > At720.DetailWidth);
    TestTrue(TEXT("The tray keeps the measured 40 px mock-up bottom margin at 1080p"),
        FMath::IsNearlyEqual(At1080.FlowTrayBottomMargin,
            ULBManagementRootWidget::DesignFlowTrayBottomMargin));
    TestTrue(TEXT("The tray bottom margin scales uniformly at 720p"),
        FMath::IsNearlyEqual(At720.FlowTrayBottomMargin,
            ULBManagementRootWidget::DesignFlowTrayBottomMargin * (2.0f / 3.0f)));
    TestTrue(TEXT("The measured surface radius scales uniformly at 720p"),
        FMath::IsNearlyEqual(At720.SurfaceCornerRadius,
            ULBManagementRootWidget::DesignSurfaceCornerRadius * (2.0f / 3.0f)));
    TestTrue(TEXT("The detail separator remains a crisp one-pixel design divider"),
        FMath::IsNearlyEqual(ULBManagementRootWidget::DesignDetailDividerWidth, 1.0f));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementRootWidgetNativeTopStripReachabilityTest,
    "LineBoss.Management.UMG.NativeTopStripPointerAndControllerReachability",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRootWidgetNativeTopStripReachabilityTest::RunTest(
    const FString& Parameters)
{
    ULBManagementRootWidget* Widget = NewObject<ULBManagementRootWidget>();
    TestNotNull(TEXT("The native management widget can be instantiated"), Widget);
    if (!Widget) return false;
    TestTrue(TEXT("The native management widget initializes its authored tree"),
        Widget->Initialize());
    // Keep the Slate owner alive while testing the real UObject/Slate hierarchy.
    const TSharedRef<SWidget> SlateShell = Widget->TakeWidget();
    TestTrue(TEXT("The native management shell has a renderable Slate tree"),
        Widget->HasRenderableShell());

    const FName DestinationButtons[] = {
        TEXT("Destination_BUILD"), TEXT("Destination_ORDERS"),
        TEXT("Destination_ANALYTICS"), TEXT("Destination_SETTINGS")};
    for (const FName ButtonName : DestinationButtons)
    {
        UButton* Button = Cast<UButton>(Widget->GetWidgetFromName(ButtonName));
        TestNotNull(FString::Printf(TEXT("%s is a real native UMG destination button"),
            *ButtonName.ToString()), Button);
        if (!Button) continue;
        TestEqual(FString::Printf(TEXT("%s is visibly pointer reachable"),
            *ButtonName.ToString()), Button->GetVisibility(),
            ESlateVisibility::Visible);
        TestTrue(FString::Printf(TEXT("%s accepts keyboard/controller focus"),
            *ButtonName.ToString()), Button->GetIsFocusable());
        TestTrue(FString::Printf(TEXT("%s is wired to its destination delegate"),
            *ButtonName.ToString()), Button->OnClicked.IsBound());
    }

    const FName SimulationButtons[] = {
        TEXT("Simulation_PAUSE"), TEXT("Simulation_PLAY"),
        TEXT("Simulation_FAST_FORWARD")};
    for (const FName ButtonName : SimulationButtons)
    {
        UButton* Button = Cast<UButton>(Widget->GetWidgetFromName(ButtonName));
        TestNotNull(FString::Printf(TEXT("%s is a real native UMG rate button"),
            *ButtonName.ToString()), Button);
        if (!Button) continue;
        TestEqual(FString::Printf(TEXT("%s is visibly pointer reachable"),
            *ButtonName.ToString()), Button->GetVisibility(),
            ESlateVisibility::Visible);
        TestTrue(FString::Printf(TEXT("%s accepts keyboard/controller focus"),
            *ButtonName.ToString()), Button->GetIsFocusable());
        TestTrue(FString::Printf(TEXT("%s is wired to its simulation-rate delegate"),
            *ButtonName.ToString()), Button->OnClicked.IsBound());
    }

    for (int32 Index = 0; Index < 5; ++Index)
    {
        const FName ButtonName(*FString::Printf(
            TEXT("ManagementContextAction_%d"), Index));
        UButton* Button = Cast<UButton>(Widget->GetWidgetFromName(ButtonName));
        TestNotNull(FString::Printf(TEXT("Five-action context retains slot %d"), Index),
            Button);
        if (Button)
            TestTrue(FString::Printf(TEXT("Context slot %d retains its delegate"), Index),
                Button->OnClicked.IsBound());
    }
    TestNull(TEXT("The bounded context does not grow a sixth action slot"),
        Widget->GetWidgetFromName(TEXT("ManagementContextAction_5")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementRootWidgetNoImportedProductionThumbnailLoadsTest,
    "LineBoss.Management.UMG.NoImportedProductionThumbnailLoads",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRootWidgetNoImportedProductionThumbnailLoadsTest::RunTest(
    const FString& Parameters)
{
    const TArray<FName> Ids = ULBManagementRootWidget::GetCanonicalProductionStageIds();
    for (const FName StageId : Ids)
    {
        const FSoftObjectPath SoftPath =
            ULBManagementRootWidget::GetStageThumbnailPath(StageId);
        TestTrue(FString::Printf(TEXT("%s does not load an imported thumbnail"),
            *StageId.ToString()), SoftPath.IsNull());
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDModernOverviewVisibilityPolicyTest,
    "LineBoss.Management.UMG.ModernOverviewVisibilityPolicy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDModernOverviewVisibilityPolicyTest::RunTest(
    const FString& Parameters)
{
    FScopedModernManagementTestWorld TestWorld(TEXT("LBModernOverviewPolicyWorld"));
    UWorld* World = TestWorld.Get();
    TestNotNull(TEXT("Modern-overview policy world exists"), World);
    if (!World) return false;
    TestTrue(TEXT("Visibility policy starts past mandatory factory identity"),
        CompleteDefaultFactoryIdentity(World));

    ALBControlRoomHUD* HUD = World->SpawnActor<ALBControlRoomHUD>();
    TestNotNull(TEXT("Modern-overview policy HUD exists"), HUD);
    if (!HUD) return false;

    TestFalse(TEXT("Modern Overview is hidden while management is closed"),
        HUD->IsModernOverviewActive());
    HUD->OpenManagementPage(ELBManagementPage::Overview);
    TestTrue(TEXT("Modern Overview is active only on the open Overview page"),
        HUD->IsModernOverviewActive());

    const ELBManagementPage NonOverviewPages[] = {
        ELBManagementPage::FactoryBuild,
        ELBManagementPage::PressTrains,
        ELBManagementPage::Analytics};
    for (const ELBManagementPage Page : NonOverviewPages)
    {
        HUD->OpenManagementPage(Page);
        TestFalse(FString::Printf(TEXT("Modern Overview is hidden on page %d"),
            static_cast<int32>(Page)), HUD->IsModernOverviewActive());
    }

    HUD->OpenManagementPage(ELBManagementPage::Overview);
    HUD->OpenFactoryAppearanceSettings();
    TestTrue(TEXT("Factory appearance remains inside native Settings above Modern Overview"),
        HUD->IsModernOverviewActive());
    HUD->ToggleManagement();
    TestFalse(TEXT("Toggling management closes the modern factory view"),
        HUD->IsModernOverviewActive());
    HUD->OpenManagementPage(ELBManagementPage::Overview);
    TestTrue(TEXT("Reopening Overview restores its native surface"),
        HUD->IsModernOverviewActive());

    UTextureRenderTarget2D* CCTVFeed = NewObject<UTextureRenderTarget2D>(HUD);
    HUD->ShowCCTVFeed(CCTVFeed);
    TestTrue(TEXT("Synthetic CCTV feed is valid for policy testing"),
        HUD->IsCCTVFeedVisible());
    TestFalse(TEXT("CCTV owns the viewport above Modern Overview"),
        HUD->IsModernOverviewActive());
    HUD->HideCCTVFeed();
    TestTrue(TEXT("Leaving CCTV restores the still-open Modern Overview"),
        HUD->IsModernOverviewActive());

    HUD->CloseManagement();
    TestFalse(TEXT("Closing management hides Modern Overview again"),
        HUD->IsModernOverviewActive());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDModernDestinationRoutingTest,
    "LineBoss.Management.UMG.ModernDestinationRouting",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDModernDestinationRoutingTest::RunTest(
    const FString& Parameters)
{
    FScopedModernManagementTestWorld TestWorld(TEXT("LBModernDestinationWorld"));
    UWorld* World = TestWorld.Get();
    TestNotNull(TEXT("Modern-destination world exists"), World);
    if (!World) return false;
    TestTrue(TEXT("Destination routing starts past mandatory factory identity"),
        CompleteDefaultFactoryIdentity(World));

    ALBControlRoomHUD* HUD = World->SpawnActor<ALBControlRoomHUD>();
    TestNotNull(TEXT("Modern-destination HUD exists"), HUD);
    if (!HUD) return false;

    struct FDestinationCase
    {
        FName Id;
        ELBManagementPage ExpectedPage;
    };
    const FDestinationCase Cases[] = {
        {TEXT("FACTORY"), ELBManagementPage::Overview},
        {TEXT("BUILD"), ELBManagementPage::FactoryBuild},
        {TEXT("ORDERS"), ELBManagementPage::Production},
        {TEXT("ASSETS"), ELBManagementPage::PressTrains},
        {TEXT("MAINTENANCE"), ELBManagementPage::SupportFleet},
        {TEXT("RESEARCH"), ELBManagementPage::Research},
        {TEXT("ANALYTICS"), ELBManagementPage::Analytics}};

    for (const FDestinationCase& Case : Cases)
    {
        TestTrue(FString::Printf(TEXT("%s is a recognized modern destination"),
            *Case.Id.ToString()), HUD->HandleModernManagementDestination(Case.Id));
        TestTrue(FString::Printf(TEXT("%s opens management"),
            *Case.Id.ToString()), HUD->IsManagementVisible());
        TestEqual(FString::Printf(TEXT("%s routes to its canonical page"),
            *Case.Id.ToString()), HUD->GetManagementPage(), Case.ExpectedPage);
    }

    const ELBManagementPage PageBeforeUnknown = HUD->GetManagementPage();
    TestFalse(TEXT("Unknown modern destinations are rejected"),
        HUD->HandleModernManagementDestination(TEXT("INVENTED_DESTINATION")));
    TestEqual(TEXT("Rejected destination cannot mutate the current page"),
        HUD->GetManagementPage(), PageBeforeUnknown);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDModernStageActionCanonicalMappingTest,
    "LineBoss.Management.UMG.ModernStageActionCanonicalMapping",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDModernStageActionCanonicalMappingTest::RunTest(
    const FString& Parameters)
{
    FScopedModernManagementTestWorld TestWorld(TEXT("LBModernStageActionWorld"));
    UWorld* World = TestWorld.Get();
    TestNotNull(TEXT("Modern-stage bridge world exists"), World);
    if (!World) return false;
    TestTrue(TEXT("Stage bridge starts past mandatory factory identity"),
        CompleteDefaultFactoryIdentity(World));

    ALBControlRoomHUD* HUD = World->SpawnActor<ALBControlRoomHUD>();
    TestNotNull(TEXT("Modern-stage bridge HUD exists"), HUD);
    if (!HUD) return false;
    HUD->OpenManagementPage(ELBManagementPage::Overview);

    const TArray<FName> StageIds =
        ULBManagementRootWidget::GetCanonicalProductionStageIds();
    for (int32 Index = 0; Index < StageIds.Num(); ++Index)
    {
        TestTrue(FString::Printf(TEXT("%s is consumed by the real stage-action bridge"),
            *StageIds[Index].ToString()),
            HUD->HandleModernProductionStageAction(StageIds[Index]));
        TestEqual(FString::Printf(TEXT("%s maps to canonical flow index %d"),
            *StageIds[Index].ToString(), Index),
            HUD->GetSelectedProductionFlowStage(), Index);
        TestEqual(FString::Printf(TEXT("%s shares the existing action selection authority"),
            *StageIds[Index].ToString()),
            HUD->GetSelectedManagementAction(), Index);
    }

    const int32 StageBeforeUnknown = HUD->GetSelectedProductionFlowStage();
    const int32 ActionBeforeUnknown = HUD->GetSelectedManagementAction();
    TestFalse(TEXT("Unknown modern stage IDs are rejected"),
        HUD->HandleModernProductionStageAction(TEXT("INVENTED_STAGE")));
    TestEqual(TEXT("Rejected stage cannot mutate the selected flow index"),
        HUD->GetSelectedProductionFlowStage(), StageBeforeUnknown);
    TestEqual(TEXT("Rejected stage cannot mutate the action authority"),
        HUD->GetSelectedManagementAction(), ActionBeforeUnknown);
    return true;
}

#endif
