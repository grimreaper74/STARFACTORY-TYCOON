#include "LBControlRoomPR004Console.h"

#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/WidgetComponent.h"
#include "EngineUtils.h"
#include "LBPR004HMIWidget.h"
#include "LBPR004Station.h"

ALBControlRoomPR004Console::ALBControlRoomPR004Console()
{
    PrimaryActorTick.bCanEverTick = true;

    ConsoleRoot = CreateDefaultSubobject<USceneComponent>(TEXT("ConsoleRoot"));
    SetRootComponent(ConsoleRoot);

    OperatorScreen = CreateDefaultSubobject<UWidgetComponent>(TEXT("PR004ControlRoomScreen"));
    OperatorScreen->SetupAttachment(ConsoleRoot);
    OperatorScreen->SetWidgetSpace(EWidgetSpace::World);
    OperatorScreen->SetWidgetClass(ULBPR004HMIWidget::StaticClass());
    OperatorScreen->SetEditTimeUsable(true);
    OperatorScreen->SetDrawSize(FVector2D(1280.0f, 720.0f));
    OperatorScreen->SetPivot(FVector2D(0.5f, 0.5f));
    OperatorScreen->SetBlendMode(EWidgetBlendMode::Opaque);
    OperatorScreen->SetBackgroundColor(FLinearColor(0.007f, 0.012f, 0.014f, 1.0f));
    OperatorScreen->SetTwoSided(true);
    OperatorScreen->SetTickWhenOffscreen(true);
    OperatorScreen->SetManuallyRedraw(false);
    OperatorScreen->SetRedrawTime(0.0f);
    OperatorScreen->SetGeometryMode(EWidgetGeometryMode::Plane);
    OperatorScreen->SetCollisionProfileName(TEXT("UI"));
    OperatorScreen->SetRelativeScale3D(FVector(0.05625f));

    // UE's off-screen WidgetComponent renderer can expose its checkerboard
    // fallback in command-line and packaged rendering. Keep the real widget
    // as the authoritative interaction host, but use a deterministic live
    // TextRender layer for the visible diegetic monitor, matching PR-004's
    // proven station-side HMI presentation.
    OperatorScreen->SetVisibility(false, false);
    OperatorScreen->SetHiddenInGame(true, false);

    ScreenInteractionSurface = CreateDefaultSubobject<UBoxComponent>(TEXT("PR004ScreenInteractionSurface"));
    ScreenInteractionSurface->SetupAttachment(ConsoleRoot);
    ScreenInteractionSurface->SetBoxExtent(FVector(2.0f, 36.0f, 20.0f));
    ScreenInteractionSurface->SetRelativeLocation(FVector(1.0f, 0.0f, 0.0f));
    ScreenInteractionSurface->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    ScreenInteractionSurface->SetCollisionResponseToAllChannels(ECR_Ignore);
    ScreenInteractionSurface->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    ScreenInteractionSurface->SetCanEverAffectNavigation(false);
    ScreenInteractionSurface->SetHiddenInGame(true);

    const auto CreateHMIText = [this](const TCHAR* Name, const FText& Text, const FColor Colour, const float WorldSize)
    {
        UTextRenderComponent* Component = CreateDefaultSubobject<UTextRenderComponent>(Name);
        Component->SetupAttachment(ConsoleRoot);
        Component->SetText(Text);
        Component->SetTextRenderColor(Colour);
        Component->SetHorizontalAlignment(EHTA_Center);
        Component->SetVerticalAlignment(EVRTA_TextCenter);
        Component->SetWorldSize(WorldSize);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCastShadow(false);
        return Component;
    };

    HMIBrandText = CreateHMIText(TEXT("MCR_PR004_HMI_BrandText"),
        FText::FromString(TEXT("CAIRNWELL AUTOMOTIVE / MOORCROSS WORKS")), FColor(226, 224, 212), 1.45f);
    HMIStationText = CreateHMIText(TEXT("MCR_PR004_HMI_StationText"),
        FText::FromString(TEXT("PR-004  /  COIL PREPARATION")), FColor(110, 128, 130), 1.55f);
    HMIStateText = CreateHMIText(TEXT("MCR_PR004_HMI_StateText"),
        FText::FromString(TEXT("NO STATION")), FColor(15, 184, 112), 1.8f);
    HMICoilText = CreateHMIText(TEXT("MCR_PR004_HMI_CoilText"),
        FText::FromString(TEXT("COIL  -")), FColor(226, 224, 212), 1.35f);
    HMIRecipeText = CreateHMIText(TEXT("MCR_PR004_HMI_RecipeText"),
        FText::FromString(TEXT("RECORD  -")), FColor(226, 224, 212), 1.25f);
    HMIChecklistText = CreateHMIText(TEXT("MCR_PR004_HMI_ChecklistText"),
        FText::FromString(TEXT("WAITING FOR STATION BINDING")), FColor(226, 224, 212), 1.15f);
    HMIActionText = CreateHMIText(TEXT("MCR_PR004_HMI_ActionText"),
        FText::FromString(TEXT("[  UNPACKAGE COIL  ]")), FColor(227, 166, 0), 1.75f);

    const auto PlaceHMIText = [](UTextRenderComponent* Component, const float LocalZ)
    {
        Component->SetRelativeLocation(FVector(1.0f, 0.0f, LocalZ));
        Component->SetRelativeRotation(FRotator::ZeroRotator);
    };
    PlaceHMIText(HMIBrandText, 13.0f);
    PlaceHMIText(HMIStationText, 9.5f);
    PlaceHMIText(HMIStateText, 5.0f);
    PlaceHMIText(HMICoilText, 0.8f);
    PlaceHMIText(HMIRecipeText, -2.5f);
    PlaceHMIText(HMIChecklistText, -6.2f);
    PlaceHMIText(HMIActionText, -12.0f);
}

void ALBControlRoomPR004Console::BeginPlay()
{
    Super::BeginPlay();
    BindAvailableStation();
    UpdateHMITextPresentation();
}

void ALBControlRoomPR004Console::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!BoundStation.IsValid())
    {
        BindAvailableStation();
    }
    HMIRefreshAccumulator += FMath::Max(0.0f, DeltaSeconds);
    if (HMIRefreshAccumulator >= 0.1f)
    {
        HMIRefreshAccumulator = 0.0f;
        UpdateHMITextPresentation();
    }
}

bool ALBControlRoomPR004Console::BindAvailableStation()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return false;
    }

    ALBPR004Station* Station = nullptr;
    for (TActorIterator<ALBPR004Station> It(World); It; ++It)
    {
        Station = *It;
        break;
    }

    if (!Station && bSpawnAuthorityIfMissing)
    {
        FActorSpawnParameters Parameters;
        Parameters.Name = TEXT("LB_MCR_Runtime_PR004_Authority");
        Parameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        Station = World->SpawnActor<ALBPR004Station>(
            ALBPR004Station::StaticClass(),
            FVector(0.0f, 0.0f, -100000.0f),
            FRotator::ZeroRotator,
            Parameters);
        if (Station)
        {
            Station->SetActorHiddenInGame(true);
            Station->SetActorEnableCollision(false);
        }
    }

    if (!Station)
    {
        return false;
    }

    if (bBootstrapReadyPackagedCoil && !ConfigureCandidateAuthority(Station))
    {
        return false;
    }

    BoundStation = Station;
    OperatorScreen->InitWidget();
    if (ULBPR004HMIWidget* Widget = Cast<ULBPR004HMIWidget>(OperatorScreen->GetUserWidgetObject()))
    {
        Widget->BindStation(Station);
        OperatorScreen->RequestRedraw();
        return true;
    }
    BoundStation.Reset();
    return false;
}

bool ALBControlRoomPR004Console::ConfigureCandidateAuthority(ALBPR004Station* Station) const
{
    if (!Station)
    {
        return false;
    }

    if (!Station->SetControlPower(true) || !Station->SetCellCommissioned(true))
    {
        return false;
    }

    FString CoilId = Station->GetCurrentCoilId();
    if (CoilId.IsEmpty())
    {
        CoilId = TEXT("MCX-U-MCR-PR004-001");
        if (!Station->LoadPackagedCoil(CoilId))
        {
            return false;
        }
    }

    return Station->SelectDepackRecipe(TEXT("PR004_DEPACK_STANDARD"), CoilId)
        && Station->SetCradleLocked(true)
        && Station->SetCHookWithdrawn(true);
}

bool ALBControlRoomPR004Console::TriggerPrimaryAction(FName EvidenceId)
{
    ALBPR004Station* Station = BoundStation.Get();
    if (!Station || EvidenceId.IsNone())
    {
        return false;
    }

    const bool bSucceeded = Station->UnpackageCoil(EvidenceId);
    UpdateHMITextPresentation();
    return bSucceeded;
}

bool ALBControlRoomPR004Console::ExecutePrimaryAction()
{
    return TriggerPrimaryAction(TEXT("CONTROL_ROOM_PR004_SCREEN"));
}

void ALBControlRoomPR004Console::UpdateHMITextPresentation()
{
    ALBPR004Station* Station = BoundStation.Get();
    if (!Station || !HMIStateText || !HMICoilText || !HMIRecipeText || !HMIChecklistText || !HMIActionText)
    {
        return;
    }

    const UEnum* StateEnum = StaticEnum<ELBPR004State>();
    const FString StateName = StateEnum
        ? FName::NameToDisplayString(StateEnum->GetNameStringByValue(static_cast<int64>(Station->GetProcessState())), false).ToUpper()
        : TEXT("UNKNOWN");
    TArray<FText> BlockingReasons;
    const bool bCanUnpackage = Station->CanUnpackageCoil(BlockingReasons);
    HMIStateText->SetText(FText::FromString(Station->IsCoilUnpackaged()
        ? TEXT("COIL UNPACKAGED")
        : bCanUnpackage ? TEXT("READY TO UNPACKAGE") : StateName));
    HMIStateText->SetTextRenderColor(Station->GetActiveFault() == ELBPR004Fault::None
        ? FColor(15, 184, 112) : FColor(199, 20, 10));
    HMICoilText->SetText(FText::FromString(FString::Printf(TEXT("COIL  %s"),
        Station->GetCurrentCoilId().IsEmpty() ? TEXT("NO COIL LOADED") : *Station->GetCurrentCoilId())));
    HMIRecipeText->SetText(FText::FromString(FString::Printf(TEXT("RECORD  %s"),
        Station->GetActiveRecipeId().IsNone() ? TEXT("-") : *Station->GetActiveRecipeId().ToString())));

    FString Checklist = TEXT("CRADLE LOCKED  /  HOOK CLEAR\nCOIL ID + RECIPE VERIFIED");
    if (!BlockingReasons.IsEmpty())
    {
        Checklist = BlockingReasons[0].ToString();
        if (BlockingReasons.Num() > 1)
        {
            Checklist += TEXT("\n") + BlockingReasons[1].ToString();
        }
    }
    HMIChecklistText->SetText(FText::FromString(Checklist));
    HMIActionText->SetText(FText::FromString(Station->IsCoilUnpackaged()
        ? TEXT("[  COIL UNPACKAGED  ]")
        : bCanUnpackage ? TEXT("[  UNPACKAGE COIL  ]") : TEXT("[  ACTION BLOCKED  ]")));
}
