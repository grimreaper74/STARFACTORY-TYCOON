#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Engine/Engine.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/InputSettings.h"
#include "InputCoreTypes.h"
#include "LBControlRoomHUD.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBFactoryBrandSubsystem.h"
#include "LBFactoryMachineBuilderSubsystem.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBFactoryBuildMachine.h"
#include "LBBodyWeldLineActor.h"
#include "LBGameMode.h"
#include "LBManagementPawn.h"
#include "LBOneFactoryTypes.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressShopCampaignController.h"
#include "LBPressShopStorageZone.h"
#include "LBPressTrainAStation.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "EngineUtils.h"

namespace
{
bool CompleteDefaultFactoryIdentityForUnrelatedHUDTest(UWorld* World)
{
    ULBFactoryBrandSubsystem* Brand = World
        ? World->GetSubsystem<ULBFactoryBrandSubsystem>() : nullptr;
    return Brand && Brand->CompleteInitialSetup();
}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDBrandFillTextContrastTest,
    "LineBoss.Management.HUD.BrandFillTextContrast",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDBrandFillTextContrastTest::RunTest(const FString& Parameters)
{
    struct FBrandContrastCase
    {
        const TCHAR* Name;
        FLinearColor Fill;
        bool bExpectDarkInk;
    };
    const FBrandContrastCase Cases[] = {
        {TEXT("green"), FLinearColor(0.035f, 0.36f, 0.16f), true},
        {TEXT("blue"), FLinearColor(0.025f, 0.22f, 0.55f), true},
        {TEXT("red"), FLinearColor(0.55f, 0.055f, 0.045f), false},
        {TEXT("orange"), FLinearColor(0.80f, 0.24f, 0.025f), true},
        {TEXT("purple"), FLinearColor(0.30f, 0.075f, 0.48f), false},
        {TEXT("grey"), FLinearColor(0.38f, 0.43f, 0.46f), true}
    };
    const auto ContrastRatio = [](const FLinearColor& A, const FLinearColor& B)
    {
        const float Bright = FMath::Max(A.GetLuminance(), B.GetLuminance());
        const float Dark = FMath::Min(A.GetLuminance(), B.GetLuminance());
        return (Bright + 0.05f) / (Dark + 0.05f);
    };

    for (const FBrandContrastCase& Case : Cases)
    {
        const FLinearColor Ink = ALBControlRoomHUD::ChooseReadableTextColour(Case.Fill);
        TestEqual(FString::Printf(TEXT("%s brand fill chooses the expected ink polarity"), Case.Name),
            Ink.GetLuminance() < 0.1f, Case.bExpectDarkInk);
        TestTrue(FString::Printf(TEXT("%s brand fill text reaches normal-text contrast"), Case.Name),
            ContrastRatio(Case.Fill, Ink) >= 4.5f);
    }

    const FLinearColor DarkCard(0.055f, 0.075f, 0.080f);
    TestTrue(TEXT("Dark inactive cards retain light ink"),
        ALBControlRoomHUD::ChooseReadableTextColour(DarkCard).GetLuminance() > 0.9f);
    const FLinearColor ManagementSelected(0.09f, 0.48f, 0.30f);
    TestTrue(TEXT("Bright management selection uses dark ink"),
        ALBControlRoomHUD::ChooseReadableTextColour(ManagementSelected).GetLuminance() < 0.1f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDFactoryAppearanceSettingsFlowTest,
    "LineBoss.Management.HUD.OptionalFactoryAppearanceSettingsFlow",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDFactoryAppearanceSettingsFlowTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBFactoryAppearanceSettingsHUDTestWorld"));
    TestNotNull(TEXT("Factory appearance settings test world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ULBFactoryBrandSubsystem* Brand = World->GetSubsystem<ULBFactoryBrandSubsystem>();
    ALBControlRoomHUD* HUD = World->SpawnActor<ALBControlRoomHUD>();
    TestNotNull(TEXT("Factory brand authority exists"), Brand);
    TestNotNull(TEXT("Factory profile HUD exists"), HUD);
    if (!Brand || !HUD)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }

    TestTrue(TEXT("A new campaign starts with a valid built-in factory identity"),
        Brand->IsInitialSetupComplete());
    HUD->ToggleManagement();
    TestTrue(TEXT("Normal management opens immediately on a new campaign"),
        HUD->IsManagementVisible());
    TestFalse(TEXT("Factory appearance does not interrupt normal startup or management"),
        HUD->IsFactoryBrandEditorVisible());
    TestFalse(TEXT("Factory appearance is never mandatory"),
        HUD->IsMandatoryFactorySetupActive());
    HUD->CloseManagement();
    TestFalse(TEXT("Management closes normally without an onboarding gate"),
        HUD->IsManagementVisible());

    HUD->OpenFactoryAppearanceSettings();
    TestFalse(TEXT("Factory appearance never revives the retired Canvas editor"),
        HUD->IsFactoryBrandEditorVisible());
    TestFalse(TEXT("Factory appearance remains optional"),
        HUD->IsMandatoryFactorySetupActive());
    TestTrue(TEXT("Native appearance routing never invalidates the live profile"),
        Brand->IsInitialSetupComplete());

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDControllerWorkflowTest,
    "LineBoss.Management.AnywhereHUD.ControllerWorkflow",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDControllerWorkflowTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LBManagementHUDTestWorld"));
    TestNotNull(TEXT("Transient management world created"), World);
    if (!World) return false;

    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    TestTrue(TEXT("Unrelated controller workflow starts past first-run identity setup"),
        CompleteDefaultFactoryIdentityForUnrelatedHUDTest(World));
    ALBControlRoomOperationsConsole* Operations = World->SpawnActor<ALBControlRoomOperationsConsole>();
    ALBControlRoomHUD* HUD = World->SpawnActor<ALBControlRoomHUD>();
    TestNotNull(TEXT("Authoritative operations console spawned"), Operations);
    TestNotNull(TEXT("Anywhere management HUD spawned"), HUD);
    World->BeginPlay();
    if (Operations && !Operations->HasActorBegunPlay()) Operations->DispatchBeginPlay();

    if (HUD && Operations)
    {
        TestFalse(TEXT("Management overlay starts closed"), HUD->IsManagementVisible());
        HUD->ToggleManagement();
        TestTrue(TEXT("Management overlay opens without visiting control room"), HUD->IsManagementVisible());
        HUD->NextManagementPage();
        TestEqual(TEXT("First right navigation selects progression-aware build page"),
            HUD->GetManagementPage(), ELBManagementPage::FactoryBuild);
        HUD->NextManagementPage();
        TestEqual(TEXT("Second right navigation selects production page"), HUD->GetManagementPage(), ELBManagementPage::Production);

        HUD->NextManagementAction();
        HUD->NextManagementAction();
        TestEqual(TEXT("Down navigation selects quantity increase"), HUD->GetSelectedManagementAction(), 2);
        TestTrue(TEXT("Confirm routes through authoritative console action"), HUD->ConfirmManagementAction());
        TestEqual(TEXT("Quantity changed once through management overlay"),
            Operations->CaptureSaveState().RequestedQuantity, 100);

        HUD->PreviousManagementPage();
        TestEqual(TEXT("Left navigation returns to build page"), HUD->GetManagementPage(), ELBManagementPage::FactoryBuild);
        HUD->PreviousManagementPage();
        TestEqual(TEXT("Second left navigation returns to overview"), HUD->GetManagementPage(), ELBManagementPage::Overview);
        HUD->ToggleManagement();
        TestFalse(TEXT("Management overlay closes cleanly"), HUD->IsManagementVisible());
    }

    const UInputSettings* Input = GetDefault<UInputSettings>();
    TestNotNull(TEXT("Input settings available"), Input);
    if (Input)
    {
        TArray<FInputActionKeyMapping> ToggleMappings;
        Input->GetActionMappingByName(TEXT("LB_ToggleManagement"), ToggleMappings);
        TestTrue(TEXT("PlayStation touchpad-equivalent opens management"),
            ToggleMappings.ContainsByPredicate([](const FInputActionKeyMapping& Mapping)
            {
                return Mapping.Key == EKeys::Gamepad_Special_Left;
            }));
        TArray<FInputActionKeyMapping> ConfirmMappings;
        Input->GetActionMappingByName(TEXT("LB_ManagementConfirm"), ConfirmMappings);
        TestTrue(TEXT("Cross/A confirms management action"),
            ConfirmMappings.ContainsByPredicate([](const FInputActionKeyMapping& Mapping)
            {
                return Mapping.Key == EKeys::Gamepad_FaceButton_Bottom;
            }));
        TArray<FInputAxisKeyMapping> ZoomMappings;
        Input->GetAxisMappingByName(TEXT("LB_Zoom"), ZoomMappings);
        TestTrue(TEXT("Mouse wheel provides variable management zoom"),
            ZoomMappings.ContainsByPredicate([](const FInputAxisKeyMapping& Mapping)
            {
                return Mapping.Key == EKeys::MouseWheelAxis;
            }));
        TestTrue(TEXT("Right trigger zooms management camera in"),
            ZoomMappings.ContainsByPredicate([](const FInputAxisKeyMapping& Mapping)
            {
                return Mapping.Key == EKeys::Gamepad_RightTriggerAxis && Mapping.Scale > 0.0f;
            }));
        TestTrue(TEXT("Left trigger zooms management camera out"),
            ZoomMappings.ContainsByPredicate([](const FInputAxisKeyMapping& Mapping)
            {
                return Mapping.Key == EKeys::Gamepad_LeftTriggerAxis && Mapping.Scale < 0.0f;
            }));
    }

    const ALBGameMode* GameMode = GetDefault<ALBGameMode>();
    TestNotNull(TEXT("Primary factory game mode defaults exist"), GameMode);
    if (GameMode)
    {
        TestTrue(TEXT("Primary factory view uses the overhead management pawn"),
            GameMode->DefaultPawnClass.Get() == ALBManagementPawn::StaticClass());
        TestTrue(TEXT("Primary factory view owns the anywhere management HUD"),
            GameMode->HUDClass.Get() == ALBControlRoomHUD::StaticClass());
    }
    const ALBManagementPawn* ManagementDefaults = GetDefault<ALBManagementPawn>();
    TestTrue(TEXT("Normal camera can reach close machine inspection range"),
        ManagementDefaults && ManagementDefaults->GetMinimumManagementZoomDistance() <= 1000.0f);
    TestTrue(TEXT("Placement camera preserves the complete train framing range"),
        ManagementDefaults && ManagementDefaults->GetMinimumPlacementZoomDistance() >= 6500.0f);
    TestTrue(TEXT("Management camera can frame the complete 189 m ED line"),
        ManagementDefaults && ManagementDefaults->GetMaximumManagementZoomDistance() >= 30000.0f);
    // The 30,000 cm floor above is satisfied by a camera that still cannot frame
    // a single shop, which is how the cap sat below the size of its own subject
    // unnoticed. Tie the requirement to the authored layout instead of a magic
    // number: the department bays span 31,000 cm north-south, which needs roughly
    // 35,000 cm of standoff at this pawn's field of view, and the full 62,000 cm
    // envelope needs about 70,000.
    {
        const FLBOneFactoryLayoutDefinition Layout =
            ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
        const float BayDepthCm =
            static_cast<float>(Layout.FactoryEnvelopeSizeCm.Y);
        const float HalfFovRadians = FMath::DegreesToRadians(48.0f * 0.5f);
        const float StandoffForBayDepthCm =
            (BayDepthCm * 0.5f) / FMath::Tan(HalfFovRadians);
        TestTrue(
            TEXT("Management camera can frame the authored department bay depth"),
            ManagementDefaults
                && ManagementDefaults->GetMaximumManagementZoomDistance()
                    >= StandoffForBayDepthCm);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBConsoleFreePlayerBuilderHUDTest,
    "LineBoss.Management.ConsoleFreeBuilder.BootCatalogueAndConfirm",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBConsoleFreePlayerBuilderHUDTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LBConsoleFreeBuilderHUDTestWorld"));
    TestNotNull(TEXT("Console-free player-builder world created"), World);
    if (!World) return false;

    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    TestTrue(TEXT("Unrelated clean-builder workflow starts past first-run identity setup"),
        CompleteDefaultFactoryIdentityForUnrelatedHUDTest(World));

    ALBPressShopBuildAuthority* BuildAuthority = World->SpawnActor<ALBPressShopBuildAuthority>();
    ALBPlayerBuiltPressFlowController* PlayerFlow = World->SpawnActor<ALBPlayerBuiltPressFlowController>();
    APlayerController* PlayerController = World->SpawnActor<APlayerController>();
    TestNotNull(TEXT("Clean-map build authority fixture exists"), BuildAuthority);
    TestNotNull(TEXT("Clean-map production-order authority exists"), PlayerFlow);
    TestNotNull(TEXT("Console-free player controller spawned"), PlayerController);
    if (PlayerController)
    {
        PlayerController->ClientSetHUD(ALBControlRoomHUD::StaticClass());
    }
    ALBManagementPawn* ManagementPawn = World->SpawnActor<ALBManagementPawn>();
    TestNotNull(TEXT("Primary overhead builder pawn spawned"), ManagementPawn);
    if (PlayerController && ManagementPawn)
    {
        PlayerController->Possess(ManagementPawn);
    }

    World->BeginPlay();
    if (ManagementPawn && !ManagementPawn->HasActorBegunPlay()) ManagementPawn->DispatchBeginPlay();
    ALBControlRoomHUD* HUD = PlayerController
        ? Cast<ALBControlRoomHUD>(PlayerController->GetHUD()) : nullptr;
    TestNotNull(TEXT("Console-free builder owns the management HUD"), HUD);

    int32 ConsoleCount = 0;
    for (TActorIterator<ALBControlRoomOperationsConsole> It(World); It; ++It)
    {
        if (IsValid(*It)) ++ConsoleCount;
    }
    TestEqual(TEXT("Clean player-builder boots with no operations console"), ConsoleCount, 0);

    if (HUD && ManagementPawn)
    {
        TestFalse(TEXT("HUD reports no legacy operations authority"), HUD->HasOperationsAuthority());
        TestTrue(TEXT("Clean player-builder opens its catalogue on boot"), HUD->IsManagementVisible());
        TestEqual(TEXT("Factory Build is the clean-map landing page"),
            HUD->GetManagementPage(), ELBManagementPage::FactoryBuild);
        TestTrue(TEXT("Console-free machine category renders its ordered next action"),
            HUD->GetManagementActionCount() >= 1);

        TestTrue(TEXT("Mouse-selectable first catalogue row activates without a console"),
            HUD->ActivateManagementAction(0));
        TestTrue(TEXT("Confirmation starts inbound-delivery placement"),
            ManagementPawn->IsPressTrainPlacementActive()
            && ManagementPawn->GetSelectedMachineType() == ELBFactoryBuildMachineType::InboundDeliveryDock);
        TestFalse(TEXT("Catalogue closes for practical floor placement"), HUD->IsManagementVisible());
        ManagementPawn->UseContextualConfirm();
        TestTrue(TEXT("Cross/A routes to active placement instead of reopening or advancing the catalogue"),
            ManagementPawn->IsPressTrainPlacementActive() && !HUD->IsManagementVisible());

        ManagementPawn->CancelPressTrainPlacement();
        ManagementPawn->UseContextualBuilderShortcut();
        TestTrue(TEXT("Clean-mode shortcut returns directly to Factory Build"),
            HUD->IsManagementVisible() && HUD->GetManagementPage() == ELBManagementPage::FactoryBuild);
        HUD->NextManagementPage();
        TestEqual(TEXT("Clean player reaches production orders without a control room"),
            HUD->GetManagementPage(), ELBManagementPage::Production);
        TestEqual(TEXT("Production order editor exposes five simple mouse actions"),
            HUD->GetManagementActionCount(), 5);
        TestEqual(TEXT("First playable vehicle uses the approved Cairnwell 2040 model identity"),
            HUD->GetSelectedVehicleModelId(), FName(TEXT("CAIRNWELL_2040")));
        TestEqual(TEXT("Order editor truthfully labels the 2040 as a pre-production BEV"),
            HUD->GetSelectedVehicleDisplayName(),
            FString(TEXT("CAIRNWELL 2040 / BEV PRE-PRODUCTION")));
        TestTrue(TEXT("Existing controller programme control remains reachable"),
            HUD->ActivateManagementAction(0));
        TestEqual(TEXT("Programme control cannot leave the approved first vehicle"),
            HUD->GetSelectedVehicleModelId(), FName(TEXT("CAIRNWELL_2040")));
        TestTrue(TEXT("Player queues the default ten-panel batch"), HUD->ActivateManagementAction(4));
        TestEqual(TEXT("Queued order reaches the live automatic scheduler"),
            PlayerFlow ? PlayerFlow->GetPanelBatches().Num() : 0, 1);
        if (PlayerFlow && !PlayerFlow->GetPanelBatches().IsEmpty())
        {
            TestEqual(TEXT("Default order is a batch of ten"),
                PlayerFlow->GetPanelBatches()[0].RequestedQuantity, 10);
            TestEqual(TEXT("Default order retains the Cairnwell 2040 model identity"),
                PlayerFlow->GetPanelBatches()[0].VehicleModelId,
                FName(TEXT("CAIRNWELL_2040")));
        }
        ManagementPawn->UseContextualBuilderShortcut();
        TestFalse(TEXT("Clean-mode shortcut no longer dead-ends on a missing return pawn"),
            HUD->IsManagementVisible());
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDECoatMilestoneCardMappingTest,
    "LineBoss.Management.ConsoleFreeBuilder.ECoatMilestoneCardMapping",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDECoatMilestoneCardMappingTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBManagementHUDECoatMilestoneTestWorld"));
    TestNotNull(TEXT("ED-line milestone HUD world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    TestTrue(TEXT("Unrelated ED-card workflow starts past first-run identity setup"),
        CompleteDefaultFactoryIdentityForUnrelatedHUDTest(World));

    APlayerController* PlayerController = World->SpawnActor<APlayerController>();
    ALBManagementPawn* ManagementPawn = World->SpawnActor<ALBManagementPawn>();
    if (PlayerController) PlayerController->ClientSetHUD(ALBControlRoomHUD::StaticClass());
    if (PlayerController && ManagementPawn) PlayerController->Possess(ManagementPawn);

    const auto AddMachine = [World, this](const TCHAR* Id,
        const ELBFactoryBuildMachineType Type)
    {
        ALBFactoryBuildMachine* Machine = World
            ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
        TestTrue(FString::Printf(TEXT("%s prerequisite machine configured"), Id),
            Machine && Machine->Configure(FName(Id), Type));
        return Machine;
    };
    const auto AddStorage = [World, this](const TCHAR* Id,
        const ELBPressShopStorageType Type)
    {
        ALBPressShopStorageZone* Zone = World
            ? World->SpawnActor<ALBPressShopStorageZone>() : nullptr;
        TestTrue(FString::Printf(TEXT("%s prerequisite storage configured"), Id),
            Zone && Zone->Configure(FName(Id), Type, 8, FVector(400.0f, 400.0f, 100.0f)));
        return Zone;
    };

    AddMachine(TEXT("ECOAT-CARD-INBOUND"), ELBFactoryBuildMachineType::InboundDeliveryDock);
    AddMachine(TEXT("ECOAT-CARD-PR002"), ELBFactoryBuildMachineType::CoilWeighInspectionCell);
    AddStorage(TEXT("ECOAT-CARD-COILS"), ELBPressShopStorageType::BareCoils);
    AddMachine(TEXT("ECOAT-CARD-DEPACK"), ELBFactoryBuildMachineType::DepackagingRobot);
    AddMachine(TEXT("ECOAT-CARD-DECOILER"), ELBFactoryBuildMachineType::DecoilerFeeder);
    AddStorage(TEXT("ECOAT-CARD-BLANKS"), ELBPressShopStorageType::PreparedBlanks);
    ALBPressTrainAStation* Train = World->SpawnActor<ALBPressTrainAStation>();
    TestNotNull(TEXT("ED-line milestone fixture has one press train"), Train);
    AddMachine(TEXT("ECOAT-CARD-INSPECTION"), ELBFactoryBuildMachineType::InspectionCell);

    World->BeginPlay();
    ALBControlRoomHUD* HUD = PlayerController
        ? Cast<ALBControlRoomHUD>(PlayerController->GetHUD()) : nullptr;
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    TestNotNull(TEXT("ED-line milestone HUD exists"), HUD);
    TestNotNull(TEXT("ED-line milestone builder exists"), Builder);
    if (!HUD || !Builder || !ManagementPawn)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }
    HUD->OpenFactoryBuild();

    const TArray<ELBFactoryBuildMachineType> LockedAvailable =
        Builder->GetAvailableMachineTypes();
    TestEqual(TEXT("Fixture exposes four ordinary machine actions before weld unlock"),
        LockedAvailable.Num(), 4);
    TestFalse(TEXT("ED line is not yet an actionable machine"),
        LockedAvailable.Contains(ELBFactoryBuildMachineType::ECoatLine));
    TestEqual(TEXT("Ordered weld and ED milestones remain visible on page one"),
        HUD->GetVisibleFactoryMachineCardCount(), 5);
    TestTrue(TEXT("Fourth card is the locked body-weld milestone"),
        HUD->IsFactoryMachineCardLocked(3));
    TestTrue(TEXT("Fifth card is explicitly marked locked"),
        HUD->IsFactoryMachineCardLocked(4));
    TestEqual(TEXT("Locked milestone has no action index"),
        HUD->GetFactoryMachineCardActionIndex(4), INDEX_NONE);
    TestFalse(TEXT("Locked milestone cannot activate placement"),
        HUD->ActivateFactoryMachineCard(4));
    TestFalse(TEXT("Locked milestone leaves the pawn out of placement mode"),
        ManagementPawn->IsPressTrainPlacementActive());

    AddStorage(TEXT("ECOAT-CARD-EMPTY"),
        ELBPressShopStorageType::EmptyPanelStillages);
    AddStorage(TEXT("ECOAT-CARD-FINISHED"),
        ELBPressShopStorageType::FinishedPanelStillages);
    AddMachine(TEXT("ECOAT-CARD-OUTBOUND"),
        ELBFactoryBuildMachineType::OutboundPanelDock);
    HUD->OpenFactoryBuild();
    const TArray<ELBFactoryBuildMachineType> UnlockedAvailable =
        Builder->GetAvailableMachineTypes();
    TestTrue(TEXT("Completing press-shop dispatch unlocks the body-weld action"),
        UnlockedAvailable.Contains(ELBFactoryBuildMachineType::BodyWeldLine));
    TestFalse(TEXT("Unlocked body-weld milestone card is no longer disabled"),
        HUD->IsFactoryMachineCardLocked(3));
    TestTrue(TEXT("Click-card activation starts real body-weld placement after unlock"),
        HUD->ActivateFactoryMachineCard(3));
    TestTrue(TEXT("Pawn receives the body-weld machine type from the unlocked card"),
        ManagementPawn->IsPressTrainPlacementActive()
        && ManagementPawn->GetSelectedMachineType() == ELBFactoryBuildMachineType::BodyWeldLine);

    ManagementPawn->CancelPressTrainPlacement();
    ALBBodyWeldLineActor* Weld = World->SpawnActor<ALBBodyWeldLineActor>();
    TestTrue(TEXT("Placed body-weld milestone fixture configures"),
        Weld && Weld->Configure(TEXT("HUD-WELD-MILESTONE")));
    HUD->OpenFactoryBuild();
    const TArray<ELBFactoryBuildMachineType> ECoatAvailable = Builder->GetAvailableMachineTypes();
    TestTrue(TEXT("Body weld unlocks ED as the next ordered milestone"),
        ECoatAvailable.Contains(ELBFactoryBuildMachineType::ECoatLine));
    TestTrue(TEXT("Keyboard/controller action zero starts the unlocked ED milestone"),
        HUD->ActivateManagementAction(0));
    TestEqual(TEXT("Keyboard/controller selects the ED-line type"),
        ManagementPawn->GetSelectedMachineType(), ELBFactoryBuildMachineType::ECoatLine);

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDSevenPageLayoutParityTest,
    "LineBoss.Management.HUD.SevenPageLayoutMouseControllerParity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDSevenPageLayoutParityTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("Overview ordinal remains save/input compatible"),
        static_cast<int32>(ELBManagementPage::Overview), 0);
    TestEqual(TEXT("Build ordinal remains save/input compatible"),
        static_cast<int32>(ELBManagementPage::FactoryBuild), 1);
    TestEqual(TEXT("Orders ordinal remains save/input compatible"),
        static_cast<int32>(ELBManagementPage::Production), 2);
    TestEqual(TEXT("Assets ordinal remains save/input compatible"),
        static_cast<int32>(ELBManagementPage::PressTrains), 3);
    TestEqual(TEXT("Maintenance ordinal remains save/input compatible"),
        static_cast<int32>(ELBManagementPage::SupportFleet), 4);
    TestEqual(TEXT("Seven-page constant includes Research and Analytics"),
        static_cast<int32>(ELBManagementPage::PageCount), 7);

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBManagementSevenPageHUDWorld"));
    TestNotNull(TEXT("Seven-page HUD world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    TestTrue(TEXT("Seven-page workflow starts past identity setup"),
        CompleteDefaultFactoryIdentityForUnrelatedHUDTest(World));
    ALBControlRoomOperationsConsole* Operations =
        World->SpawnActor<ALBControlRoomOperationsConsole>();
    ALBControlRoomHUD* HUD = World->SpawnActor<ALBControlRoomHUD>();
    TestNotNull(TEXT("Seven-page operations fixture exists"), Operations);
    TestNotNull(TEXT("Seven-page HUD exists"), HUD);
    World->BeginPlay();
    if (Operations && !Operations->HasActorBegunPlay()) Operations->DispatchBeginPlay();

    if (HUD && Operations)
    {
        HUD->ToggleManagement();
        constexpr float ViewW = 1920.0f;
        constexpr float ViewH = 1080.0f;
        for (int32 Index = 0;
            Index < static_cast<int32>(ELBManagementPage::PageCount); ++Index)
        {
            const ELBManagementPage Page = static_cast<ELBManagementPage>(Index);
            FVector2D Target;
            TestTrue(FString::Printf(TEXT("Page %d exposes a generated tab target"), Index),
                HUD->GetManagementTabHitTarget(Page, ViewW, ViewH, Target));
            TestTrue(FString::Printf(TEXT("Page %d generated tab is mouse actionable"), Index),
                HUD->HandleManagementClickForViewport(Target.X, Target.Y, ViewW, ViewH));
            TestEqual(FString::Printf(TEXT("Mouse selects exact page %d"), Index),
                HUD->GetManagementPage(), Page);
        }

        HUD->OpenManagementPage(ELBManagementPage::Analytics);
        HUD->NextManagementPage();
        TestEqual(TEXT("Right/controller navigation wraps Analytics to Overview"),
            HUD->GetManagementPage(), ELBManagementPage::Overview);
        HUD->PreviousManagementPage();
        TestEqual(TEXT("Left/controller navigation wraps Overview to Analytics"),
            HUD->GetManagementPage(), ELBManagementPage::Analytics);
        HUD->OpenManagementPage(ELBManagementPage::Research);
        TestEqual(TEXT("Research is a truthful read-only page until unlock actions exist"),
            HUD->GetManagementActionCount(), 0);
        HUD->OpenManagementPage(ELBManagementPage::Analytics);
        TestEqual(TEXT("Analytics is a truthful read-only page"),
            HUD->GetManagementActionCount(), 0);

        HUD->OpenManagementPage(ELBManagementPage::Production);
        const int32 QuantityBefore = Operations->CaptureSaveState().RequestedQuantity;
        FVector2D ActionTarget;
        TestTrue(TEXT("Quantity-plus action exposes its generated row centre"),
            HUD->GetManagementActionHitTarget(2, ViewW, ViewH, ActionTarget));
        TestTrue(TEXT("Mouse click resolves through that exact generated row"),
            HUD->HandleManagementClickForViewport(
                ActionTarget.X, ActionTarget.Y, ViewW, ViewH));
        TestTrue(TEXT("Mouse and controller share the same quantity-plus authority"),
            Operations->CaptureSaveState().RequestedQuantity > QuantityBefore
            && HUD->GetSelectedManagementAction() == 2);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDRichCatalogueDecisionAndPagingTest,
    "LineBoss.Management.HUD.RichCatalogueDecisionFactsPagingAndParity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDRichCatalogueDecisionAndPagingTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBRichCatalogueHUDWorld"));
    TestNotNull(TEXT("Rich catalogue world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    TestTrue(TEXT("Rich catalogue fixture starts past identity setup"),
        CompleteDefaultFactoryIdentityForUnrelatedHUDTest(World));

    ALBPressShopBuildAuthority* Authority = World->SpawnActor<ALBPressShopBuildAuthority>();
    if (Authority)
    {
        FLBPressShopBuildBay Bay;
        Bay.BayId = TEXT("RICH-CATALOGUE-BAY");
        Bay.Centre = FVector::ZeroVector;
        Bay.HalfExtent = FVector(12000.0f, 12000.0f, 500.0f);
        Authority->BuildBays.Add(Bay);

        // Page-two action five is the empty-stillage store. Its click must pass
        // through the same authored storage-default gate as live play; a generic
        // build bay alone is intentionally insufficient for storage placement.
        FLBPressShopStorageBay EmptyStillageBay;
        EmptyStillageBay.BayId = TEXT("RICH-CATALOGUE-EMPTY-STILLAGE-BAY");
        EmptyStillageBay.Centre = FVector(4000.0f, 0.0f, 0.0f);
        EmptyStillageBay.HalfExtent = FVector(1200.0f, 1200.0f, 600.0f);
        EmptyStillageBay.AcceptedTypes.Add(
            ELBPressShopStorageType::EmptyPanelStillages);
        EmptyStillageBay.DefaultZoneHalfExtent = FVector(1000.0f, 1000.0f, 500.0f);
        EmptyStillageBay.DefaultCapacity = 12;
        EmptyStillageBay.StorageUnitPitchCm = FVector2D(250.0f, 250.0f);
        EmptyStillageBay.BoundaryClearanceCm = 100.0f;
        Authority->StorageBays.Add(EmptyStillageBay);
    }
    APlayerController* PlayerController = World->SpawnActor<APlayerController>();
    ALBManagementPawn* ManagementPawn = World->SpawnActor<ALBManagementPawn>();
    if (PlayerController) PlayerController->ClientSetHUD(ALBControlRoomHUD::StaticClass());
    if (PlayerController && ManagementPawn) PlayerController->Possess(ManagementPawn);
    ALBFactoryBuildMachine* Inbound = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Storage paging fixture owns inbound authority"), Inbound
        && Inbound->Configure(TEXT("RICH-CATALOGUE-INBOUND"),
            ELBFactoryBuildMachineType::InboundDeliveryDock));
    ALBFactoryBuildMachine* Decoiler = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Storage paging fixture owns preparation line"), Decoiler
        && Decoiler->Configure(TEXT("RICH-CATALOGUE-DECOILER"),
            ELBFactoryBuildMachineType::DecoilerFeeder));
    ALBFactoryBuildMachine* Inspection = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Storage paging fixture owns panel inspection"), Inspection
        && Inspection->Configure(TEXT("RICH-CATALOGUE-INSPECTION"),
            ELBFactoryBuildMachineType::InspectionCell));
    TestNotNull(TEXT("Storage paging fixture owns press train"),
        World->SpawnActor<ALBPressTrainAStation>());

    World->BeginPlay();
    ALBControlRoomHUD* HUD = PlayerController
        ? Cast<ALBControlRoomHUD>(PlayerController->GetHUD()) : nullptr;
    TestNotNull(TEXT("Rich catalogue HUD exists"), HUD);
    if (!HUD)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }
    HUD->OpenFactoryBuild();
    const int32 MachineCardCount = HUD->GetVisibleFactoryMachineCardCount();
    int32 LockedWeldCardIndex = INDEX_NONE;
    int32 LockedECoatCardIndex = INDEX_NONE;
    for (int32 CardIndex = 0; CardIndex < MachineCardCount; ++CardIndex)
    {
        FLBFactoryCatalogueDecisionFacts CandidateFacts;
        if (!HUD->IsFactoryMachineCardLocked(CardIndex)
            || !HUD->GetFactoryMachineCardDecisionFacts(CardIndex, CandidateFacts)) continue;
        if (CandidateFacts.DisplayName.Contains(TEXT("BODY WELD"))) LockedWeldCardIndex = CardIndex;
        if (CandidateFacts.DisplayName.Contains(TEXT("ED / E-COAT"))) LockedECoatCardIndex = CardIndex;
    }
    TestTrue(TEXT("Machine catalogue retains both ordered locked area milestones"),
        LockedWeldCardIndex != INDEX_NONE && LockedECoatCardIndex != INDEX_NONE
        && LockedWeldCardIndex < LockedECoatCardIndex);
    FLBFactoryCatalogueDecisionFacts LockedFacts;
    TestTrue(TEXT("Locked milestone exposes decision facts"),
        HUD->GetFactoryMachineCardDecisionFacts(LockedECoatCardIndex, LockedFacts));
    TestEqual(TEXT("Locked milestone keeps its complete untruncated name"),
        LockedFacts.DisplayName, FString(TEXT("COMPLETE 189 m ED / E-COAT LINE")));
    TestEqual(TEXT("Locked milestone identifies its production stage"),
        LockedFacts.ProcessStage, FString(TEXT("PAINT / ED E-COAT")));
    TestTrue(TEXT("Locked milestone explains its truthful prerequisite"),
        LockedFacts.bLocked
        && LockedFacts.LockReason.Contains(TEXT("BODY WELD")));
    TestEqual(TEXT("Locked milestone exposes input material"),
        LockedFacts.InputFlow, FString(TEXT("IN  BODY-IN-WHITE")));
    TestEqual(TEXT("Locked milestone exposes output material"),
        LockedFacts.OutputFlow, FString(TEXT("OUT E-COATED BODY")));
    TestEqual(TEXT("Locked milestone exposes its 189 m clearance contract"),
        LockedFacts.FootprintAndServiceEnvelope, FString(TEXT("ENVELOPE 189 m LINE")));
    TestTrue(TEXT("Catalogue preview API is ready for real authored thumbnails"),
        LockedFacts.ThumbnailAsset.IsNull() && !LockedFacts.PreviewKind.IsEmpty());
    FLBFactoryCatalogueDecisionFacts WeldFacts;
    TestTrue(TEXT("Locked body-weld milestone exposes decision facts"),
        HUD->GetFactoryMachineCardDecisionFacts(LockedWeldCardIndex, WeldFacts));
    TestTrue(TEXT("Body-weld facts expose stillage intake, BIW output and full envelope"),
        WeldFacts.InputFlow.Contains(TEXT("PANEL STILLAGES"))
        && WeldFacts.OutputFlow.Contains(TEXT("BODY-IN-WHITE"))
        && WeldFacts.FootprintAndServiceEnvelope.Contains(TEXT("60.0 x 30.0")));

    const struct { float W; float H; const TCHAR* Label; } Viewports[] = {
        {1280.0f, 720.0f, TEXT("1280x720")},
        {1920.0f, 1080.0f, TEXT("1920x1080")}
    };
    TestTrue(TEXT("Storage filter is accessible through the shared category API"),
        HUD->SelectFactoryBuildCategory(1));
    TestTrue(TEXT("Seven available storage types remain discoverable"),
        HUD->GetManagementActionCount() >= 7);
    TestEqual(TEXT("Storage catalogue uses two pages instead of hiding items"),
        HUD->GetFactoryCataloguePageCount(), 2);
    for (const auto& Viewport : Viewports)
    {
        FBox2D PreviousCard(ForceInit);
        for (int32 CardIndex = 0; CardIndex < 5; ++CardIndex)
        {
            FBox2D Card(ForceInit);
            TestTrue(FString::Printf(TEXT("%s card %d has responsive geometry"),
                Viewport.Label, CardIndex), HUD->GetFactoryCatalogueCardHitRect(
                    CardIndex, Viewport.W, Viewport.H, Card));
            TestTrue(FString::Printf(TEXT("%s card %d stays inside viewport"),
                Viewport.Label, CardIndex), Card.Min.X >= 0.0f && Card.Min.Y >= 0.0f
                    && Card.Max.X <= Viewport.W && Card.Max.Y <= Viewport.H);
            TestTrue(FString::Printf(TEXT("%s card %d has decision-fact height"),
                Viewport.Label, CardIndex), Card.GetSize().Y >= 220.0f);
            if (CardIndex > 0)
                TestTrue(FString::Printf(TEXT("%s cards do not overlap"), Viewport.Label),
                    PreviousCard.Max.X < Card.Min.X);
            PreviousCard = Card;
        }
        FBox2D NextButton(ForceInit);
        TestTrue(FString::Printf(TEXT("%s paging control has shared geometry"),
            Viewport.Label), HUD->GetFactoryCataloguePageButtonHitRect(
                true, Viewport.W, Viewport.H, NextButton));
        TestTrue(FString::Printf(TEXT("%s paging control keeps 44 px target"),
            Viewport.Label), NextButton.GetSize().Y
                >= ALBControlRoomHUD::GetReadabilityContract(
                    Viewport.W, Viewport.H).MinimumInteractiveHeight);
    }

    HUD->NextFactoryCataloguePage();
    TestEqual(TEXT("Controller/API paging reaches the second page"),
        HUD->GetFactoryCataloguePage(), 1);
    FBox2D SecondPageFirstCard(ForceInit);
    TestTrue(TEXT("Second-page first card has a mouse hit target"),
        HUD->GetFactoryCatalogueCardHitRect(0, 1280.0f, 720.0f,
            SecondPageFirstCard));
    TestEqual(TEXT("Second-page first card retains absolute action five"),
        HUD->GetSelectedManagementAction(), 5);
    TestTrue(TEXT("Mouse activation on page two shares action five authority"),
        HUD->HandleManagementClickForViewport(SecondPageFirstCard.GetCenter().X,
            SecondPageFirstCard.GetCenter().Y, 1280.0f, 720.0f));
    TestTrue(TEXT("Mouse/controller parity starts storage placement from page two"),
        ManagementPawn && ManagementPawn->IsStoragePlacementActive());

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDResponsiveReadabilityContractTest,
    "LineBoss.Management.HUD.ResponsiveReadability720p1080p",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDResponsiveReadabilityContractTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBManagementResponsiveHUDWorld"));
    TestNotNull(TEXT("Responsive HUD world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    TestTrue(TEXT("Responsive HUD workflow starts past identity setup"),
        CompleteDefaultFactoryIdentityForUnrelatedHUDTest(World));
    ALBControlRoomOperationsConsole* Operations =
        World->SpawnActor<ALBControlRoomOperationsConsole>();
    ALBControlRoomHUD* HUD = World->SpawnActor<ALBControlRoomHUD>();
    TestNotNull(TEXT("Responsive HUD operations fixture exists"), Operations);
    TestNotNull(TEXT("Responsive HUD exists"), HUD);
    World->BeginPlay();
    if (Operations && !Operations->HasActorBegunPlay()) Operations->DispatchBeginPlay();

    struct FViewportCase
    {
        const TCHAR* Label;
        float W;
        float H;
    };
    const FViewportCase Viewports[] = {
        {TEXT("1280x720"), 1280.0f, 720.0f},
        {TEXT("1920x1080"), 1920.0f, 1080.0f}
    };
    const auto IsInsideViewport = [](const FBox2D& Rect, const float W, const float H)
    {
        return Rect.Min.X >= 0.0 && Rect.Min.Y >= 0.0
            && Rect.Max.X <= static_cast<double>(W)
            && Rect.Max.Y <= static_cast<double>(H)
            && Rect.GetSize().X > 0.0 && Rect.GetSize().Y > 0.0;
    };

    if (HUD && Operations)
    {
        for (const FViewportCase& Viewport : Viewports)
        {
            const FLBHUDReadabilityContract Contract =
                ALBControlRoomHUD::GetReadabilityContract(Viewport.W, Viewport.H);
            const float ExpectedReferenceScale = Viewport.H / 720.0f;
            TestTrue(FString::Printf(TEXT("%s complete HUD contract scales from the 720p reference"),
                Viewport.Label), FMath::IsNearlyEqual(
                    Contract.LayoutScale, ExpectedReferenceScale, 0.01f));
            TestTrue(FString::Printf(TEXT("%s normal copy budgets at least 16 physical pixels"),
                Viewport.Label), Contract.ExpectedNormalTextPixelHeight
                    >= 16.0f * ExpectedReferenceScale);
            TestTrue(FString::Printf(TEXT("%s secondary copy budgets at least 14 physical pixels"),
                Viewport.Label), Contract.ExpectedDetailTextPixelHeight
                    >= 14.0f * ExpectedReferenceScale);
            TestTrue(FString::Printf(TEXT("%s headings budget at least 24 physical pixels"),
                Viewport.Label), Contract.ExpectedHeadingTextPixelHeight
                    >= 24.0f * ExpectedReferenceScale);
            TestTrue(FString::Printf(TEXT("%s normal SmallFont scale matches its pixel budget"),
                Viewport.Label), Contract.NormalTextScale
                    >= 1.34f * ExpectedReferenceScale);
            TestTrue(FString::Printf(TEXT("%s detail SmallFont scale matches its pixel budget"),
                Viewport.Label), Contract.DetailTextScale
                    >= 1.16f * ExpectedReferenceScale);
            TestTrue(FString::Printf(TEXT("%s LargeFont heading scale matches its pixel budget"),
                Viewport.Label), Contract.HeadingTextScale
                    >= 0.92f * ExpectedReferenceScale);
            TestTrue(FString::Printf(TEXT("%s interaction contract keeps a scaled 44 px target"),
                Viewport.Label), Contract.MinimumInteractiveHeight
                    >= 44.0f * ExpectedReferenceScale);
            TestTrue(FString::Printf(TEXT("%s persistent strip keeps its 720p visual proportion"),
                Viewport.Label), Contract.PersistentHUDHeight
                    >= 65.0f * ExpectedReferenceScale);
            TestTrue(FString::Printf(TEXT("%s persistent strip remains on screen"), Viewport.Label),
                IsInsideViewport(Contract.PersistentBounds, Viewport.W, Viewport.H));
            TestTrue(FString::Printf(TEXT("%s management panel does not clip"), Viewport.Label),
                IsInsideViewport(Contract.ManagementBounds, Viewport.W, Viewport.H));
            TestTrue(FString::Printf(TEXT("%s build catalogue does not clip"), Viewport.Label),
                IsInsideViewport(Contract.FactoryBuildBounds, Viewport.W, Viewport.H));
            TestTrue(FString::Printf(TEXT("%s brand modal does not clip"), Viewport.Label),
                IsInsideViewport(Contract.FactoryBrandBounds, Viewport.W, Viewport.H));
            TestTrue(FString::Printf(TEXT("%s build catalogue preserves most factory context"),
                Viewport.Label), Contract.FactoryBuildBounds.Min.Y >= Viewport.H * 0.40f);

            for (int32 ControlIndex = 0; ControlIndex < 4; ++ControlIndex)
            {
                FBox2D ControlRect(ForceInit);
                TestTrue(FString::Printf(TEXT("%s profile control %d has a generated rectangle"),
                    Viewport.Label, ControlIndex), HUD->GetFactoryBrandControlHitRect(
                        ControlIndex, Viewport.W, Viewport.H, ControlRect));
                TestTrue(FString::Printf(TEXT("%s profile control %d stays on screen"),
                    Viewport.Label, ControlIndex), IsInsideViewport(
                        ControlRect, Viewport.W, Viewport.H));
                TestTrue(FString::Printf(TEXT("%s profile control %d keeps the minimum target"),
                    Viewport.Label, ControlIndex),
                    ControlRect.GetSize().Y >= Contract.MinimumInteractiveHeight);
            }

            for (int32 PageIndex = 0;
                PageIndex < static_cast<int32>(ELBManagementPage::PageCount); ++PageIndex)
            {
                const ELBManagementPage Page = static_cast<ELBManagementPage>(PageIndex);
                HUD->OpenManagementPage(Page);
                FBox2D TabRect(ForceInit);
                TestTrue(FString::Printf(TEXT("%s page %d has a generated tab rectangle"),
                    Viewport.Label, PageIndex), HUD->GetManagementTabHitRect(
                        Page, Viewport.W, Viewport.H, TabRect));
                TestTrue(FString::Printf(TEXT("%s page %d tab stays on screen"),
                    Viewport.Label, PageIndex), IsInsideViewport(
                        TabRect, Viewport.W, Viewport.H));
                TestTrue(FString::Printf(TEXT("%s page %d tab keeps the minimum target"),
                    Viewport.Label, PageIndex),
                    TabRect.GetSize().Y >= Contract.MinimumInteractiveHeight);
                const FVector2D TabTarget = TabRect.GetCenter();
                TestTrue(FString::Printf(TEXT("%s page %d generated tab remains mouse actionable"),
                    Viewport.Label, PageIndex), HUD->HandleManagementClickForViewport(
                        TabTarget.X, TabTarget.Y, Viewport.W, Viewport.H));
                TestEqual(FString::Printf(TEXT("%s mouse/controller page authority remains exact"),
                    Viewport.Label), HUD->GetManagementPage(), Page);
            }

            HUD->OpenManagementPage(ELBManagementPage::Production);
            TestEqual(FString::Printf(TEXT("%s operations page retains all nine actions"),
                Viewport.Label), HUD->GetManagementActionCount(), 9);
            for (int32 ActionIndex = 0; ActionIndex < 9; ++ActionIndex)
            {
                FBox2D ActionRect(ForceInit);
                TestTrue(FString::Printf(TEXT("%s action %d has a generated rectangle"),
                    Viewport.Label, ActionIndex), HUD->GetManagementActionHitRect(
                        ActionIndex, Viewport.W, Viewport.H, ActionRect));
                TestTrue(FString::Printf(TEXT("%s action %d stays on screen"),
                    Viewport.Label, ActionIndex), IsInsideViewport(
                        ActionRect, Viewport.W, Viewport.H));
                TestTrue(FString::Printf(TEXT("%s action %d keeps the minimum target"),
                    Viewport.Label, ActionIndex),
                    ActionRect.GetSize().Y >= Contract.MinimumInteractiveHeight);
            }
            const int32 QuantityBefore = Operations->CaptureSaveState().RequestedQuantity;
            FVector2D QuantityTarget;
            TestTrue(FString::Printf(TEXT("%s quantity action exposes its shared centre"),
                Viewport.Label), HUD->GetManagementActionHitTarget(
                    2, Viewport.W, Viewport.H, QuantityTarget));
            TestTrue(FString::Printf(TEXT("%s quantity action remains mouse actionable"),
                Viewport.Label), HUD->HandleManagementClickForViewport(
                    QuantityTarget.X, QuantityTarget.Y, Viewport.W, Viewport.H));
            TestTrue(FString::Printf(TEXT("%s mouse and controller retain exact action parity"),
                Viewport.Label), HUD->GetSelectedManagementAction() == 2
                && Operations->CaptureSaveState().RequestedQuantity > QuantityBefore);
        }
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDProductionFlowResponsiveGeometryTest,
    "LineBoss.Management.HUD.ProductionFlowResponsiveGeometry720p1080p",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDProductionFlowResponsiveGeometryTest::RunTest(
    const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBProductionFlowGeometryWorld"));
    TestNotNull(TEXT("Production-flow geometry world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    ALBControlRoomHUD* HUD = World->SpawnActor<ALBControlRoomHUD>();
    TestNotNull(TEXT("Production-flow geometry HUD exists"), HUD);
    if (!HUD)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }

    struct FViewportCase
    {
        const TCHAR* Label;
        float W;
        float H;
    };
    const FViewportCase Viewports[] = {
        {TEXT("1280x720"), 1280.0f, 720.0f},
        {TEXT("1920x1080"), 1920.0f, 1080.0f}
    };
    const auto IsInsideViewport = [](const FBox2D& Rect,
        const float W, const float H)
    {
        return Rect.bIsValid
            && Rect.Min.X >= 0.0 && Rect.Min.Y >= 0.0
            && Rect.Max.X <= static_cast<double>(W)
            && Rect.Max.Y <= static_cast<double>(H)
            && Rect.GetSize().X > 0.0 && Rect.GetSize().Y > 0.0;
    };
    const auto BoxNearlyEquals = [](const FBox2D& A, const FBox2D& B)
    {
        return A.Min.Equals(B.Min, 0.01f) && A.Max.Equals(B.Max, 0.01f);
    };

    FLBProductionFlowHUDLayout Layout720;
    for (const FViewportCase& Viewport : Viewports)
    {
        const FLBHUDReadabilityContract Readability =
            ALBControlRoomHUD::GetReadabilityContract(Viewport.W, Viewport.H);
        const FLBProductionFlowHUDLayout Layout =
            ALBControlRoomHUD::GetProductionFlowLayout(Viewport.W, Viewport.H);
        TestEqual(FString::Printf(TEXT("%s production flow has exactly six cards"),
            Viewport.Label), Layout.StageCardBounds.Num(), 6);
        TestTrue(FString::Printf(TEXT("%s top bar stays inside the viewport"),
            Viewport.Label), IsInsideViewport(Layout.TopBarBounds,
                Viewport.W, Viewport.H));
        TestTrue(FString::Printf(TEXT("%s flow canvas stays inside the viewport"),
            Viewport.Label), IsInsideViewport(Layout.FlowCanvasBounds,
                Viewport.W, Viewport.H));
        TestTrue(FString::Printf(TEXT("%s stage lane stays inside the flow canvas"),
            Viewport.Label), Layout.FlowCanvasBounds.IsInside(
                Layout.StageLaneBounds.Min)
            && Layout.FlowCanvasBounds.IsInside(Layout.StageLaneBounds.Max));
        TestTrue(FString::Printf(TEXT("%s detail panel stays inside the flow canvas"),
            Viewport.Label), Layout.FlowCanvasBounds.IsInside(Layout.DetailBounds.Min)
            && Layout.FlowCanvasBounds.IsInside(Layout.DetailBounds.Max));
        TestTrue(FString::Printf(TEXT("%s stage lane and detail panel never overlap"),
            Viewport.Label), Layout.StageLaneBounds.Max.X < Layout.DetailBounds.Min.X);
        TestTrue(FString::Printf(TEXT("%s primary action stays inside detail panel"),
            Viewport.Label), Layout.DetailBounds.IsInside(Layout.PrimaryActionBounds.Min)
            && Layout.DetailBounds.IsInside(Layout.PrimaryActionBounds.Max));
        TestTrue(FString::Printf(TEXT("%s primary action keeps the 44 px interaction contract"),
            Viewport.Label), Layout.PrimaryActionBounds.GetSize().Y
                >= Readability.MinimumInteractiveHeight);

        FBox2D PublicPrimary(ForceInit);
        TestTrue(FString::Printf(TEXT("%s exposes the primary-action hit rectangle"),
            Viewport.Label), HUD->GetProductionFlowPrimaryActionHitRect(
                Viewport.W, Viewport.H, PublicPrimary));
        TestTrue(FString::Printf(TEXT("%s primary-action getter shares draw geometry"),
            Viewport.Label), BoxNearlyEquals(PublicPrimary,
                Layout.PrimaryActionBounds));

        float PreviousMaxX = -1.0f;
        for (int32 StageIndex = 0; StageIndex < 6; ++StageIndex)
        {
            const FBox2D& Card = Layout.StageCardBounds[StageIndex];
            TestTrue(FString::Printf(TEXT("%s stage %d stays inside its lane"),
                Viewport.Label, StageIndex), Layout.StageLaneBounds.IsInside(Card.Min)
                && Layout.StageLaneBounds.IsInside(Card.Max));
            TestTrue(FString::Printf(TEXT("%s stage %d keeps a controller-sized target"),
                Viewport.Label, StageIndex), Card.GetSize().Y
                    >= Readability.MinimumInteractiveHeight);
            TestTrue(FString::Printf(TEXT("%s stage %d retains left-to-right order"),
                Viewport.Label, StageIndex), Card.Min.X > PreviousMaxX);
            PreviousMaxX = Card.Max.X;

            FBox2D PublicCard(ForceInit);
            TestTrue(FString::Printf(TEXT("%s exposes stage %d hit geometry"),
                Viewport.Label, StageIndex), HUD->GetProductionFlowStageHitRect(
                    StageIndex, Viewport.W, Viewport.H, PublicCard));
            TestTrue(FString::Printf(TEXT("%s stage %d hit geometry matches drawing"),
                Viewport.Label, StageIndex), BoxNearlyEquals(PublicCard, Card));
        }
        FBox2D InvalidCard(ForceInit);
        TestFalse(FString::Printf(TEXT("%s rejects stage index below zero"),
            Viewport.Label), HUD->GetProductionFlowStageHitRect(
                INDEX_NONE, Viewport.W, Viewport.H, InvalidCard));
        TestFalse(FString::Printf(TEXT("%s rejects stage index six"),
            Viewport.Label), HUD->GetProductionFlowStageHitRect(
                6, Viewport.W, Viewport.H, InvalidCard));

        if (Viewport.W == 1280.0f) Layout720 = Layout;
        else
        {
            TestTrue(TEXT("1080p top bar scales exactly from the 720p reference"),
                FMath::IsNearlyEqual(Layout.TopBarBounds.GetSize().Y,
                    Layout720.TopBarBounds.GetSize().Y * 1.5f, 0.01f));
            TestTrue(TEXT("1080p flow canvas height scales exactly from 720p"),
                FMath::IsNearlyEqual(Layout.FlowCanvasBounds.GetSize().Y,
                    Layout720.FlowCanvasBounds.GetSize().Y * 1.5f, 0.01f));
            TestTrue(TEXT("1080p stage-card height scales exactly from 720p"),
                FMath::IsNearlyEqual(Layout.StageCardBounds[0].GetSize().Y,
                    Layout720.StageCardBounds[0].GetSize().Y * 1.5f, 0.01f));
        }
    }
    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDProductionFlowMouseControllerParityTest,
    "LineBoss.Management.HUD.ProductionFlowMouseControllerSelectionParity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDProductionFlowMouseControllerParityTest::RunTest(
    const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBProductionFlowInputParityWorld"));
    TestNotNull(TEXT("Production-flow input world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    TestTrue(TEXT("Production-flow input test starts past identity setup"),
        CompleteDefaultFactoryIdentityForUnrelatedHUDTest(World));
    ALBControlRoomHUD* HUD = World->SpawnActor<ALBControlRoomHUD>();
    TestNotNull(TEXT("Production-flow input HUD exists"), HUD);
    World->BeginPlay();

    if (HUD)
    {
        constexpr float ViewW = 1280.0f;
        constexpr float ViewH = 720.0f;
        HUD->OpenManagementPage(ELBManagementPage::Overview);
        TestEqual(TEXT("Overview opens on the approved transfer-press stage"),
            HUD->GetSelectedProductionFlowStage(), 2);
        TestEqual(TEXT("Overview exposes exactly the six stage selections"),
            HUD->GetManagementActionCount(), 6);

        for (int32 ExpectedStage = 0; ExpectedStage < 6; ++ExpectedStage)
        {
            FBox2D StageRect(ForceInit);
            TestTrue(FString::Printf(TEXT("Stage %d exposes shared mouse geometry"),
                ExpectedStage), HUD->GetProductionFlowStageHitRect(
                    ExpectedStage, ViewW, ViewH, StageRect));
            TestTrue(FString::Printf(TEXT("Mouse selects exact stage %d"),
                ExpectedStage), HUD->HandleManagementClickForViewport(
                    StageRect.GetCenter().X, StageRect.GetCenter().Y,
                    ViewW, ViewH));
            TestEqual(FString::Printf(TEXT("Mouse retains absolute stage %d"),
                ExpectedStage), HUD->GetSelectedProductionFlowStage(),
                ExpectedStage);
        }

        TestFalse(TEXT("A miss above the flow panel is not consumed as a stage"),
            HUD->HandleManagementClickForViewport(640.0f, 120.0f,
                ViewW, ViewH));
        TestEqual(TEXT("Mouse miss leaves stage selection unchanged"),
            HUD->GetSelectedProductionFlowStage(), 5);

        HUD->NextManagementAction();
        TestEqual(TEXT("Controller Next wraps stage five directly to stage zero"),
            HUD->GetSelectedProductionFlowStage(), 0);
        TestEqual(TEXT("Controller stage navigation never changes management page"),
            HUD->GetManagementPage(), ELBManagementPage::Overview);
        HUD->PreviousManagementAction();
        TestEqual(TEXT("Controller Previous wraps stage zero directly to stage five"),
            HUD->GetSelectedProductionFlowStage(), 5);
        TestEqual(TEXT("Controller selection remains within six absolute stage indices"),
            HUD->GetManagementActionCount(), 6);

        FBox2D StageTwoRect(ForceInit);
        TestTrue(TEXT("Transfer-press stage exposes its shared rectangle"),
            HUD->GetProductionFlowStageHitRect(2, ViewW, ViewH, StageTwoRect));
        TestTrue(TEXT("Mouse can restore the approved transfer-press selection"),
            HUD->HandleManagementClickForViewport(StageTwoRect.GetCenter().X,
                StageTwoRect.GetCenter().Y, ViewW, ViewH));
        TestEqual(TEXT("Mouse/controller authority agrees on transfer-press index two"),
            HUD->GetSelectedProductionFlowStage(), 2);

        FBox2D PrimaryRect(ForceInit);
        TestTrue(TEXT("Primary stage action exposes one shared input rectangle"),
            HUD->GetProductionFlowPrimaryActionHitRect(
                ViewW, ViewH, PrimaryRect));
        TestTrue(TEXT("Uninstalled locked transfer press consumes its action click truthfully"),
            HUD->HandleManagementClickForViewport(PrimaryRect.GetCenter().X,
                PrimaryRect.GetCenter().Y, ViewW, ViewH));
        TestEqual(TEXT("Unavailable transfer-press action cannot mutate stage selection"),
            HUD->GetSelectedProductionFlowStage(), 2);
        TestTrue(TEXT("Controller confirm uses the same unavailable-stage action seam"),
            HUD->ConfirmManagementAction());
        TestEqual(TEXT("Unavailable controller confirm cannot escape the flow stage"),
            HUD->GetSelectedProductionFlowStage(), 2);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBManagementHUDManualCampaignSaveLoadBridgeTest,
    "LineBoss.Management.HUD.ManualCampaignSaveLoadDoubleConfirm",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementHUDManualCampaignSaveLoadBridgeTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBManagementCampaignBridgeHUDWorld"));
    TestNotNull(TEXT("Manual campaign bridge world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    TestTrue(TEXT("Manual campaign bridge starts past identity setup"),
        CompleteDefaultFactoryIdentityForUnrelatedHUDTest(World));
    ALBPressShopCampaignController* Campaign =
        World->SpawnActor<ALBPressShopCampaignController>();
    ALBControlRoomHUD* HUD = World->SpawnActor<ALBControlRoomHUD>();
    TestNotNull(TEXT("Whole-campaign save authority exists"), Campaign);
    TestNotNull(TEXT("Manual campaign bridge HUD exists"), HUD);
    World->BeginPlay();

    if (HUD && Campaign)
    {
        constexpr float ViewW = 1280.0f;
        constexpr float ViewH = 720.0f;
        HUD->OpenManagementPage(ELBManagementPage::Analytics);
        TestEqual(TEXT("Analytics owns explicit manual Save and Load actions"),
            HUD->GetManagementActionCount(), 2);

        FVector2D SaveTarget;
        TestTrue(TEXT("Save action exposes the same generated mouse/controller target"),
            HUD->GetManagementActionHitTarget(0, ViewW, ViewH, SaveTarget));
        FVector2D LoadTarget;
        TestTrue(TEXT("Load action exposes the same generated mouse/controller target"),
            HUD->GetManagementActionHitTarget(1, ViewW, ViewH, LoadTarget));
        TestTrue(TEXT("Mouse can arm, but cannot one-click execute, whole-campaign Load"),
            HUD->HandleManagementClickForViewport(
                LoadTarget.X, LoadTarget.Y, ViewW, ViewH));
        TestTrue(TEXT("First Load activation enters explicit confirmation state"),
            HUD->IsCampaignLoadConfirmationArmed());
        TestEqual(TEXT("Armed Load displays the required unsaved-change warning"),
            HUD->GetCampaignPersistenceFeedback(),
            FString(TEXT("CONFIRM LOAD - UNSAVED CHANGES WILL BE LOST")));

        HUD->PreviousManagementAction();
        TestFalse(TEXT("Moving away from Load safely cancels its armed state"),
            HUD->IsCampaignLoadConfirmationArmed());
        HUD->NextManagementAction();
        TestTrue(TEXT("Controller can arm the same guarded Load action"),
            HUD->ConfirmManagementAction());
        TestTrue(TEXT("Controller path reaches the identical guarded state"),
            HUD->IsCampaignLoadConfirmationArmed());
        HUD->OpenManagementPage(ELBManagementPage::Overview);
        TestFalse(TEXT("Leaving Analytics cancels a pending destructive Load"),
            HUD->IsCampaignLoadConfirmationArmed());

        // This is intentionally a pure action-state test: it never calls either
        // slot API and therefore cannot overwrite or load a user's campaign.
        HUD->OpenManagementPage(ELBManagementPage::Analytics);
        HUD->NextManagementAction();
        TestTrue(TEXT("Returning to Load requires a fresh first confirmation"),
            HUD->ConfirmManagementAction());
        TestTrue(TEXT("Fresh first confirmation is armed rather than executed"),
            HUD->IsCampaignLoadConfirmationArmed());
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBInfrastructureSelectionAndSafeEditTest,
    "LineBoss.Management.InfrastructureEditor.SelectValidateCancelAndPersist",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBInfrastructureSelectionAndSafeEditTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LBInfrastructureEditorTestWorld"));
    TestNotNull(TEXT("Infrastructure editor world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ALBPressShopBuildAuthority* Authority = World->SpawnActor<ALBPressShopBuildAuthority>();
    if (Authority)
    {
        FLBPressShopBuildBay Bay;
        Bay.BayId = TEXT("INFRASTRUCTURE_EDIT_TEST_FLOOR");
        Bay.Centre = FVector::ZeroVector;
        Bay.HalfExtent = FVector(3000.0f, 3000.0f, 500.0f);
        Authority->BuildBays.Add(Bay);
    }
    ULBFactoryMachineBuilderSubsystem* Builder = World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
    AStaticMeshActor* BlockingFloor = World->SpawnActor<AStaticMeshActor>(
        AStaticMeshActor::StaticClass(), FTransform(FVector(0.0f, 0.0f, -50.0f)));
    if (BlockingFloor && BlockingFloor->GetStaticMeshComponent())
    {
        BlockingFloor->GetStaticMeshComponent()->SetStaticMesh(Cube);
        BlockingFloor->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        BlockingFloor->GetStaticMeshComponent()->SetCollisionProfileName(TEXT("BlockAll"));
        BlockingFloor->GetStaticMeshComponent()->SetCollisionObjectType(ECC_WorldStatic);
        BlockingFloor->SetActorScale3D(FVector(60.0f, 60.0f, 1.0f));
    }
    TestTrue(TEXT("Editor fixture has an actual blocking floor at Z=0"), BlockingFloor && Cube
        && BlockingFloor->GetComponentsBoundingBox(true).Max.Z <= 0.1f);
    ALBFactoryAGVInfrastructure* Walkway = nullptr;
    FString Reason;
    TestTrue(TEXT("Editable walkway is placed through the normal builder"), Authority && Builder
        && Builder->PlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::PedestrianWalkway,
            INDEX_NONE, FTransform(FVector(0.0f, 0.0f, 0.0f)), Walkway, Reason));
    if (!Authority || !Builder || !Walkway)
    {
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
        return false;
    }
    Walkway->MarkAutomaticallyGenerated();
    const FVector WalkwayHalfExtent = Walkway->GetPlacementHalfExtentCm();
    TestEqual(TEXT("Placement collision centre is one half-height above its floor root"),
        Walkway->GetPlacementEnvelope()->GetRelativeLocation().Z, WalkwayHalfExtent.Z);
    TestTrue(TEXT("Dedicated selection proxy is query-only and mouse-visible"),
        Walkway->GetSelectionProxy()
        && Walkway->GetSelectionProxy()->GetCollisionEnabled() == ECollisionEnabled::QueryOnly
        && Walkway->GetSelectionProxy()->GetCollisionResponseToChannel(ECC_Visibility) == ECR_Block);

    ALBManagementPawn* Pawn = World->SpawnActor<ALBManagementPawn>();
    TestTrue(TEXT("Management pawn selects infrastructure by actor identity"),
        Pawn && Pawn->SelectInfrastructure(Walkway));
    TestEqual(TEXT("Inspector exposes stable id"),
        Pawn ? Pawn->GetInspectedInfrastructureId() : NAME_None, Walkway->GetInfrastructureId());
    const FTransform Original = Walkway->GetActorTransform();
    TestTrue(TEXT("Idle automatic infrastructure enters guarded edit mode"),
        Pawn && Pawn->StartSelectedInfrastructureEdit());
    if (Pawn) Pawn->CancelInfrastructureEdit(false);
    TestFalse(TEXT("Cancel exits edit mode"), Pawn && Pawn->IsInfrastructureEditActive());
    TestTrue(TEXT("Cancel retains the exact original transform"),
        Walkway->GetActorTransform().Equals(Original, 0.01f));

    const FTransform ValidEdit(FRotator(0.0f, 90.0f, 0.0f), FVector(600.0f, 0.0f, 0.0f));
    TestFalse(TEXT("Floor-root preview ignores the traced blocking support floor"),
        ALBManagementPawn::IsInfrastructurePreviewEnvelopeObstructed(
            World, ValidEdit, WalkwayHalfExtent, BlockingFloor->GetStaticMeshComponent(),
            FVector::UpVector, Pawn));
    TestTrue(TEXT("Builder accepts a clear edit inside the factory floor"),
        Builder->UpdateAGVInfrastructureTransform(Walkway->GetInfrastructureId(), ValidEdit, Reason));
    TestEqual(TEXT("Edited automatic provenance remains explicit"), Walkway->GetProvenance(),
        ELBFactoryInfrastructureProvenance::PlayerEditedAutomatic);
    if (Pawn) Pawn->ClearInfrastructureSelection();
    TestTrue(TEXT("Controller-style centre view ray selects the query-only floor asset"), Pawn
        && Pawn->SelectInfrastructureAlongViewRay(
            FVector(600.0f, 0.0f, 1000.0f), FVector::DownVector)
        && Pawn->GetInspectedInfrastructureId() == Walkway->GetInfrastructureId());
    const FVector SnappedFloorRoot = ALBManagementPawn::SnapInfrastructureRootToFloor(
        FVector(123.0f, 276.0f, 42.0f));
    TestEqual(TEXT("Infrastructure root retains exact floor height instead of adding half-height"),
        SnappedFloorRoot.Z, 42.0);
    TestEqual(TEXT("Infrastructure root still uses the 0.5 m floor grid"),
        FVector2D(SnappedFloorRoot.X, SnappedFloorRoot.Y), FVector2D(100.0f, 300.0f));
    TestFalse(TEXT("Complete footprint outside the build bay is rejected"),
        Builder->ValidateAGVInfrastructureTransform(Walkway->GetInfrastructureId(),
            FTransform(FVector(4000.0f, 0.0f, 0.0f)), Reason));

    AStaticMeshActor* RaisedObstruction = World->SpawnActor<AStaticMeshActor>(
        AStaticMeshActor::StaticClass(), FTransform(FVector(-1200.0f, 0.0f, 50.0f)));
    if (RaisedObstruction && RaisedObstruction->GetStaticMeshComponent())
    {
        RaisedObstruction->GetStaticMeshComponent()->SetStaticMesh(Cube);
        RaisedObstruction->GetStaticMeshComponent()->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        RaisedObstruction->GetStaticMeshComponent()->SetCollisionProfileName(TEXT("BlockAll"));
        RaisedObstruction->GetStaticMeshComponent()->SetCollisionObjectType(ECC_WorldStatic);
        RaisedObstruction->SetActorScale3D(FVector(4.0f, 4.0f, 1.0f));
    }
    const FTransform ObstructedEdit(FVector(-1200.0f, 0.0f, 0.0f));
    TestTrue(TEXT("Floor-root preview still rejects a true raised obstruction"), RaisedObstruction
        && ALBManagementPawn::IsInfrastructurePreviewEnvelopeObstructed(
            World, ObstructedEdit, WalkwayHalfExtent, BlockingFloor->GetStaticMeshComponent(),
            FVector::UpVector, Pawn));
    TestTrue(TEXT("A raised visibility hit is never trusted as the support floor"), RaisedObstruction
        && ALBManagementPawn::IsInfrastructurePreviewEnvelopeObstructed(
            World, ObstructedEdit, WalkwayHalfExtent,
            RaisedObstruction->GetStaticMeshComponent(), FVector::UpVector, Pawn));
    const FTransform RaisedTopEdit(FVector(-1200.0f, 0.0f, 100.0f));
    TestTrue(TEXT("An upward WorldStatic top above the authored floor datum is never accepted"),
        ALBManagementPawn::IsInfrastructurePreviewEnvelopeObstructed(
            World, RaisedTopEdit, WalkwayHalfExtent,
            RaisedObstruction->GetStaticMeshComponent(), FVector::UpVector, Pawn));
    TestFalse(TEXT("Builder also rejects a root lifted onto a raised WorldStatic top"),
        Builder->ValidateAGVInfrastructureTransform(
            Walkway->GetInfrastructureId(), RaisedTopEdit, Reason));
    TestTrue(TEXT("Raised-top rejection identifies the authorised floor datum"),
        Reason.Contains(TEXT("FLOOR DATUM")));
    TestFalse(TEXT("Builder rejects the same true raised obstruction"),
        Builder->ValidateAGVInfrastructureTransform(
            Walkway->GetInfrastructureId(), ObstructedEdit, Reason));
    TestTrue(TEXT("Raised-obstruction rejection reports its physical cause"),
        Reason.Contains(TEXT("RAISED WORLD OBSTRUCTION")));

    ALBFactoryBuildMachine* Machine = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(1500.0f, 0.0f, 0.0f)));
    TestTrue(TEXT("Protected machine fixture configures"), Machine
        && Machine->Configure(TEXT("EDIT-BLOCKER-001"), ELBFactoryBuildMachineType::InspectionCell));
    TestFalse(TEXT("Edit cannot enter a machine protected envelope"),
        Builder->ValidateAGVInfrastructureTransform(Walkway->GetInfrastructureId(),
            FTransform(FVector(1500.0f, 0.0f, 0.0f)), Reason));

    const FTransform EndpointTransform(FVector(0.0f, 1200.0f, 0.0f));
    ALBFactoryAGVInfrastructure* WaitPoint = World->SpawnActor<ALBFactoryAGVInfrastructure>(
        ALBFactoryAGVInfrastructure::StaticClass(), EndpointTransform);
    ALBFactoryAGVInfrastructure* RoutePaint = World->SpawnActor<ALBFactoryAGVInfrastructure>(
        ALBFactoryAGVInfrastructure::StaticClass(), EndpointTransform);
    TestTrue(TEXT("Automatic endpoint overlap fixtures configure"), WaitPoint && RoutePaint
        && WaitPoint->Configure(TEXT("EDIT-WAIT-001"), ELBFactoryAGVInfrastructureType::WaitPoint)
        && RoutePaint->Configure(TEXT("EDIT-ROUTE-001"), ELBFactoryAGVInfrastructureType::AGVRouteSegment));
    TestTrue(TEXT("Wait/handoff endpoints may retain their intentional overlap with route paint"),
        WaitPoint && Builder->ValidateAGVInfrastructureTransform(
            WaitPoint->GetInfrastructureId(), EndpointTransform, Reason));

    TArray<FLBFactoryAGVInfrastructureSaveState> Saved;
    TestTrue(TEXT("Edited infrastructure enters campaign save"), Builder->CaptureAGVInfrastructure(Saved));
    const FLBFactoryAGVInfrastructureSaveState* SavedWalkway = Saved.FindByPredicate(
        [Walkway](const FLBFactoryAGVInfrastructureSaveState& State)
        { return State.InfrastructureId == Walkway->GetInfrastructureId(); });
    TestTrue(TEXT("Save v2 retains stable id and automatic-to-manual provenance"), SavedWalkway
        && SavedWalkway->Version == 2
        && SavedWalkway->Provenance == ELBFactoryInfrastructureProvenance::PlayerEditedAutomatic);

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
