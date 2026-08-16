#include "LBPaintShopPrototypeRootWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/ButtonSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Fonts/SlateFontInfo.h"
#include "GameFramework/PlayerController.h"
#include "LBPaintShopBuildAuthority.h"
#include "LBPaintShopCellActor.h"
#include "LBPaintShopManagementPawn.h"
#include "LBPaintShopPrototypeGameMode.h"
#include "LBPaintShopPrototypeHUD.h"
#include "LBPaintShopPrototypeRuntime.h"
#include "LBPaintShopPrototypeWorldBootstrap.h"
#include "Styling/CoreStyle.h"

namespace LBPaintShopPrototypeUI
{
    const FLinearColor Ink(0.0065f, 0.0140f, 0.0170f, 0.96f);
    const FLinearColor Card(0.0180f, 0.0350f, 0.0400f, 0.98f);
    const FLinearColor CardHover(0.0300f, 0.0600f, 0.0660f, 1.0f);
    const FLinearColor Stroke(0.075f, 0.30f, 0.32f, 0.95f);
    const FLinearColor OffWhite(0.92f, 0.94f, 0.91f, 1.0f);
    const FLinearColor Muted(0.62f, 0.70f, 0.70f, 1.0f);
    const FLinearColor Cyan(0.10f, 0.78f, 0.82f, 1.0f);
    const FLinearColor Amber(1.0f, 0.65f, 0.14f, 1.0f);
    const FLinearColor Green(0.08f, 0.72f, 0.30f, 1.0f);
    const FLinearColor Red(0.92f, 0.20f, 0.16f, 1.0f);

    FSlateFontInfo Font(const int32 Size, const bool bBold = false)
    {
        return FSlateFontInfo(FCoreStyle::GetDefaultFontStyle(
            bBold ? TEXT("Bold") : TEXT("Regular"), Size));
    }

    FSlateBrush RoundedBrush(const FLinearColor Fill, const FLinearColor Outline,
        const float OutlineWidth = 1.0f, const float Radius = 8.0f)
    {
        return FSlateRoundedBoxBrush(Fill,
            FVector4(Radius, Radius, Radius, Radius), Outline, OutlineWidth);
    }

    FButtonStyle ButtonStyle(const bool bPrimary)
    {
        FButtonStyle Style;
        const FLinearColor Normal = bPrimary
            ? FLinearColor(0.02f, 0.38f, 0.19f, 1.0f) : Card;
        const FLinearColor Hover = bPrimary
            ? FLinearColor(0.03f, 0.55f, 0.26f, 1.0f) : CardHover;
        Style.SetNormal(RoundedBrush(Normal, bPrimary ? Green : Stroke));
        Style.SetHovered(RoundedBrush(Hover, Cyan, 1.5f));
        Style.SetPressed(RoundedBrush(FLinearColor(0.01f, 0.16f, 0.09f, 1.0f),
            Cyan, 2.0f));
        Style.SetDisabled(RoundedBrush(Card.CopyWithNewOpacity(0.42f), Stroke));
        Style.SetNormalPadding(FMargin(1.0f));
        Style.SetPressedPadding(FMargin(2.0f, 3.0f, 0.0f, 0.0f));
        return Style;
    }

    UTextBlock* Text(UWidgetTree* Tree, const FName Name, const FString& Value,
        const int32 Size, const FLinearColor Colour, const bool bBold = false)
    {
        UTextBlock* Label = Tree->ConstructWidget<UTextBlock>(
            UTextBlock::StaticClass(), Name);
        Label->SetText(FText::FromString(Value));
        Label->SetFont(Font(Size, bBold));
        Label->SetColorAndOpacity(FSlateColor(Colour));
        Label->SetAutoWrapText(false);
        return Label;
    }

    UButton* Button(UWidgetTree* Tree, const FName Name, UTextBlock*& OutLabel,
        const FString& Value, const bool bPrimary)
    {
        UButton* Result = Tree->ConstructWidget<UButton>(UButton::StaticClass(), Name);
        Result->SetStyle(ButtonStyle(bPrimary));
        OutLabel = Text(Tree, FName(*(Name.ToString() + TEXT("Label"))),
            Value, 13, OffWhite, true);
        if (UButtonSlot* Slot = Cast<UButtonSlot>(Result->AddChild(OutLabel)))
        {
            Slot->SetPadding(FMargin(12.0f, 8.0f));
            Slot->SetHorizontalAlignment(HAlign_Center);
            Slot->SetVerticalAlignment(VAlign_Center);
        }
        return Result;
    }

    bool ResolveCoherentPrototype(const UWorld* World,
        int32& OutBootstrapCount,
        ALBPaintShopPrototypeWorldBootstrap*& OutBootstrap,
        ALBPaintShopPrototypeRuntime*& OutRuntime,
        FString& OutReason)
    {
        OutBootstrapCount = 0;
        int32 AuthorityCount = 0;
        int32 RuntimeCount = 0;
        OutBootstrap = nullptr;
        OutRuntime = nullptr;
        if (!World)
        {
            OutReason = TEXT("PAINT SHOP WORLD IS UNAVAILABLE");
            return false;
        }
        for (TActorIterator<ALBPaintShopPrototypeWorldBootstrap> It(World); It; ++It)
        {
            if (!IsValid(*It) || It->IsActorBeingDestroyed()) continue;
            ++OutBootstrapCount;
            OutBootstrap = *It;
        }
        for (TActorIterator<ALBPaintShopBuildAuthority> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++AuthorityCount;
        }
        for (TActorIterator<ALBPaintShopPrototypeRuntime> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++RuntimeCount;
        }

        ALBPaintShopBuildAuthority* Authority = OutBootstrapCount == 1
            ? OutBootstrap->GetBuildAuthority() : nullptr;
        OutRuntime = OutBootstrapCount == 1 ? OutBootstrap->GetRuntime() : nullptr;
        ALBPaintShopCellActor* Cell = OutRuntime ? OutRuntime->GetEDCoatCell() : nullptr;
        const FLBPaintShopApprovedEDCoatLayoutItem Approved =
            ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
        FString PlacementReason;
        const bool bRuntimeBound = Authority && OutRuntime
            && Authority->GetOwner() == OutBootstrap
            && OutRuntime->GetOwner() == OutBootstrap
            && OutRuntime->GetBuildAuthority() == Authority;
        const bool bApprovedCell = Authority && Cell
            && Cell->GetOwner() == Authority
            && Authority->FindCell(Approved.CellId) == Cell
            && Cell->GetCellId() == Approved.CellId
            && Cell->GetDefinitionId() == Approved.DefinitionId
            && Cell->GetActorTransform().Equals(Approved.WorldTransform, 0.01f)
            && Authority->ValidateApprovedCellPlacement(
                Cell->GetDefinitionId(), Cell->GetActorTransform(), PlacementReason);
        return ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(
            OutBootstrapCount, AuthorityCount, RuntimeCount,
            OutBootstrapCount == 1 ? OutBootstrap->GetBootstrapState()
                : ELBPaintShopPrototypeBootstrapState::Uninitialized,
            IsValid(Authority), IsValid(OutRuntime),
            OutRuntime && OutRuntime->IsInitialized(), bRuntimeBound,
            bApprovedCell, OutReason);
    }
}

TArray<FName> ULBPaintShopPrototypeRootWidget::GetCanonicalControlIds()
{
    return {TEXT("START_WELD_HANDOFF"), TEXT("PAUSE_RESUME"),
        TEXT("OUTPUT_BLOCK"), TEXT("RELEASE_OUTPUT"), TEXT("SAVE"), TEXT("LOAD")};
}

TSharedRef<SWidget> ULBPaintShopPrototypeRootWidget::RebuildWidget()
{
    BuildShell();
    return Super::RebuildWidget();
}

void ULBPaintShopPrototypeRootWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    BuildShell();
}

void ULBPaintShopPrototypeRootWidget::NativeConstruct()
{
    Super::NativeConstruct();
    RefreshFromRuntime();
}

void ULBPaintShopPrototypeRootWidget::NativeTick(
    const FGeometry& MyGeometry, const float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshAccumulatorSeconds += InDeltaTime;
    if (RefreshAccumulatorSeconds >= 0.20f)
    {
        RefreshAccumulatorSeconds = 0.0f;
        RefreshFromRuntime();
    }
}

void ULBPaintShopPrototypeRootWidget::BuildShell()
{
    if (!WidgetTree || WidgetTree->RootWidget) return;

    UOverlay* Root = WidgetTree->ConstructWidget<UOverlay>(
        UOverlay::StaticClass(), TEXT("PaintShopPrototypeRoot"));
    WidgetTree->RootWidget = Root;

    USizeBox* PanelSize = WidgetTree->ConstructWidget<USizeBox>(
        USizeBox::StaticClass(), TEXT("PaintShopOperatorPanelSize"));
    PanelSize->SetWidthOverride(780.0f);
    UOverlaySlot* PanelOverlaySlot = Root->AddChildToOverlay(PanelSize);
    PanelOverlaySlot->SetHorizontalAlignment(HAlign_Left);
    PanelOverlaySlot->SetVerticalAlignment(VAlign_Top);
    PanelOverlaySlot->SetPadding(FMargin(24.0f));

    UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(
        UBorder::StaticClass(), TEXT("PaintShopOperatorPanel"));
    Panel->SetBrush(LBPaintShopPrototypeUI::RoundedBrush(
        LBPaintShopPrototypeUI::Ink, LBPaintShopPrototypeUI::Stroke, 1.0f, 10.0f));
    Panel->SetPadding(FMargin(18.0f));
    PanelSize->AddChild(Panel);

    UVerticalBox* Stack = WidgetTree->ConstructWidget<UVerticalBox>(
        UVerticalBox::StaticClass(), TEXT("PaintShopOperatorStack"));
    Panel->AddChild(Stack);
    Stack->AddChildToVerticalBox(LBPaintShopPrototypeUI::Text(WidgetTree,
        TEXT("PaintShopTitle"), TEXT("CAIRNWELL 2040  /  PAINT SHOP  /  ED-COAT"),
        20, LBPaintShopPrototypeUI::OffWhite, true));
    IsolationLabel = LBPaintShopPrototypeUI::Text(WidgetTree,
        TEXT("PaintShopIsolationStatus"), TEXT("ISOLATION: WAIT"), 13,
        LBPaintShopPrototypeUI::Cyan, true);
    Stack->AddChildToVerticalBox(IsolationLabel)->SetPadding(
        FMargin(0.0f, 7.0f, 0.0f, 0.0f));
    RuntimeLabel = LBPaintShopPrototypeUI::Text(WidgetTree,
        TEXT("PaintShopRuntimeStatus"), TEXT("PROCESS: LOCKED"), 14,
        LBPaintShopPrototypeUI::Amber, true);
    Stack->AddChildToVerticalBox(RuntimeLabel)->SetPadding(
        FMargin(0.0f, 4.0f, 0.0f, 0.0f));
    OperatorLabel = LBPaintShopPrototypeUI::Text(WidgetTree,
        TEXT("PaintShopOperatorStatus"), TEXT("OPERATOR: READY"), 13,
        LBPaintShopPrototypeUI::Green);
    Stack->AddChildToVerticalBox(OperatorLabel)->SetPadding(
        FMargin(0.0f, 4.0f, 0.0f, 0.0f));
    CameraLabel = LBPaintShopPrototypeUI::Text(WidgetTree,
        TEXT("PaintShopCameraStatus"), TEXT("CAMERA: WAITING"), 12,
        LBPaintShopPrototypeUI::Muted);
    Stack->AddChildToVerticalBox(CameraLabel)->SetPadding(
        FMargin(0.0f, 4.0f, 0.0f, 12.0f));

    UHorizontalBox* PrimaryActions = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("PaintShopPrimaryActions"));
    Stack->AddChildToVerticalBox(PrimaryActions);
    UTextBlock* StartLabel = nullptr;
    UTextBlock* PauseLabel = nullptr;
    UTextBlock* BlockLabel = nullptr;
    StartButton = LBPaintShopPrototypeUI::Button(WidgetTree,
        TEXT("PaintShopStart"), StartLabel, TEXT("Start Weld handoff"), true);
    PauseButton = LBPaintShopPrototypeUI::Button(WidgetTree,
        TEXT("PaintShopPause"), PauseLabel, TEXT("Pause process"), false);
    BlockButton = LBPaintShopPrototypeUI::Button(WidgetTree,
        TEXT("PaintShopBlock"), BlockLabel, TEXT("Block output"), false);
    PauseButtonLabel = PauseLabel;
    BlockButtonLabel = BlockLabel;
    UTextBlock* ReleaseLabel = nullptr;
    ReleaseButton = LBPaintShopPrototypeUI::Button(WidgetTree,
        TEXT("PaintShopRelease"), ReleaseLabel, TEXT("Release output"), false);
    for (UButton* Button : {StartButton.Get(), PauseButton.Get(),
        BlockButton.Get(), ReleaseButton.Get()})
    {
        PrimaryActions->AddChildToHorizontalBox(Button)->SetPadding(
            FMargin(0.0f, 0.0f, 8.0f, 0.0f));
    }

    UHorizontalBox* SaveActions = WidgetTree->ConstructWidget<UHorizontalBox>(
        UHorizontalBox::StaticClass(), TEXT("PaintShopSaveActions"));
    Stack->AddChildToVerticalBox(SaveActions)->SetPadding(
        FMargin(0.0f, 8.0f, 0.0f, 10.0f));
    UTextBlock* SaveLabel = nullptr;
    UTextBlock* LoadLabel = nullptr;
    SaveButton = LBPaintShopPrototypeUI::Button(WidgetTree,
        TEXT("PaintShopSave"), SaveLabel, TEXT("Save Paint state"), false);
    LoadButton = LBPaintShopPrototypeUI::Button(WidgetTree,
        TEXT("PaintShopLoad"), LoadLabel, TEXT("Load Paint state"), false);
    SaveActions->AddChildToHorizontalBox(SaveButton)->SetPadding(
        FMargin(0.0f, 0.0f, 8.0f, 0.0f));
    SaveActions->AddChildToHorizontalBox(LoadButton);

    Stack->AddChildToVerticalBox(LBPaintShopPrototypeUI::Text(WidgetTree,
        TEXT("PaintShopOperatorControls"),
        ALBPaintShopPrototypeHUD::GetOperatorControlsReadout(), 11,
        LBPaintShopPrototypeUI::Muted));
    Stack->AddChildToVerticalBox(LBPaintShopPrototypeUI::Text(WidgetTree,
        TEXT("PaintShopCameraControls"),
        ALBPaintShopPrototypeHUD::GetCameraControlsReadout(), 11,
        LBPaintShopPrototypeUI::Muted))->SetPadding(
            FMargin(0.0f, 3.0f, 0.0f, 0.0f));

    StartButton->OnClicked.AddDynamic(this,
        &ULBPaintShopPrototypeRootWidget::HandleStartClicked);
    PauseButton->OnClicked.AddDynamic(this,
        &ULBPaintShopPrototypeRootWidget::HandlePauseClicked);
    BlockButton->OnClicked.AddDynamic(this,
        &ULBPaintShopPrototypeRootWidget::HandleBlockClicked);
    ReleaseButton->OnClicked.AddDynamic(this,
        &ULBPaintShopPrototypeRootWidget::HandleReleaseClicked);
    SaveButton->OnClicked.AddDynamic(this,
        &ULBPaintShopPrototypeRootWidget::HandleSaveClicked);
    LoadButton->OnClicked.AddDynamic(this,
        &ULBPaintShopPrototypeRootWidget::HandleLoadClicked);
}

bool ULBPaintShopPrototypeRootWidget::HasRenderableShell() const
{
    return WidgetTree && WidgetTree->RootWidget && IsolationLabel && RuntimeLabel
        && OperatorLabel && CameraLabel && PauseButtonLabel && BlockButtonLabel
        && StartButton && PauseButton && BlockButton && ReleaseButton
        && SaveButton && LoadButton;
}

void ULBPaintShopPrototypeRootWidget::RefreshFromRuntime()
{
    if (!HasRenderableShell()) return;

    int32 BootstrapCount = 0;
    ALBPaintShopPrototypeWorldBootstrap* Bootstrap = nullptr;
    ALBPaintShopPrototypeRuntime* Runtime = nullptr;
    FString ValidationReason;
    const bool bCoherent = LBPaintShopPrototypeUI::ResolveCoherentPrototype(
        GetWorld(), BootstrapCount, Bootstrap, Runtime, ValidationReason);
    IsolationLabel->SetText(FText::FromString(
        ALBPaintShopPrototypeHUD::BuildIsolationReadout(BootstrapCount,
            Bootstrap ? Bootstrap->GetBootstrapState()
                : ELBPaintShopPrototypeBootstrapState::Uninitialized,
            bCoherent,
            Bootstrap && Bootstrap->HasFailed()
                ? Bootstrap->GetBootstrapReason() : ValidationReason)));

    if (bCoherent && IsValid(Runtime))
    {
        RuntimeLabel->SetText(FText::FromString(
            ALBPaintShopPrototypeHUD::BuildRuntimeStageReadout(
                Runtime->GetPhase(), Runtime->GetPhaseProgress01(),
                Runtime->IsPaused(), Runtime->IsOutputBlocked(),
                Runtime->IsProcessFaulted(), Runtime->GetProcessFaultReason())));
        PauseButtonLabel->SetText(FText::FromString(
            Runtime->IsPaused() ? TEXT("Resume process") : TEXT("Pause process")));
        BlockButtonLabel->SetText(FText::FromString(
            Runtime->IsOutputBlocked() ? TEXT("Unblock output") : TEXT("Block output")));
    }
    else
    {
        RuntimeLabel->SetText(FText::FromString(FString::Printf(
            TEXT("PROCESS: LOCKED - %s"),
            ValidationReason.IsEmpty() ? TEXT("RUNTIME NOT DISCOVERABLE")
                : *ValidationReason)));
    }

    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
    {
        OperatorLabel->SetText(FText::FromString(Mode->GetLastOperatorActionStatus()));
        OperatorLabel->SetColorAndOpacity(FSlateColor(
            Mode->WasLastOperatorActionSuccessful()
                ? LBPaintShopPrototypeUI::Green : LBPaintShopPrototypeUI::Red));
    }
    else
    {
        OperatorLabel->SetText(FText::FromString(
            TEXT("OPERATOR: LOCKED - PAINT GAME MODE NOT DISCOVERABLE")));
        OperatorLabel->SetColorAndOpacity(FSlateColor(LBPaintShopPrototypeUI::Red));
    }

    FString CameraText(TEXT("CAMERA: MANAGEMENT PAWN NOT DISCOVERABLE"));
    if (const APlayerController* Controller = GetOwningPlayer())
    {
        if (const ALBPaintShopManagementPawn* Pawn =
            Cast<ALBPaintShopManagementPawn>(Controller->GetPawn()))
        {
            CameraText = FString::Printf(TEXT("CAMERA: %s  |  ZOOM %.0f CM"),
                *Pawn->GetCameraStatus(), Pawn->GetPrototypeZoomDistance());
        }
    }
    CameraLabel->SetText(FText::FromString(CameraText));
}

ALBPaintShopPrototypeGameMode*
ULBPaintShopPrototypeRootWidget::ResolveOperatorGameMode() const
{
    return GetWorld() ? GetWorld()->GetAuthGameMode<ALBPaintShopPrototypeGameMode>()
                      : nullptr;
}

void ULBPaintShopPrototypeRootWidget::HandleStartClicked()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
        Mode->StartCanonicalWeldHandoff(Reason);
    RefreshFromRuntime();
}

void ULBPaintShopPrototypeRootWidget::HandlePauseClicked()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
        Mode->ToggleProcessPause(Reason);
    RefreshFromRuntime();
}

void ULBPaintShopPrototypeRootWidget::HandleBlockClicked()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
        Mode->ToggleOutputBlock(Reason);
    RefreshFromRuntime();
}

void ULBPaintShopPrototypeRootWidget::HandleReleaseClicked()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
        Mode->ReleasePaintOutput(Reason);
    RefreshFromRuntime();
}

void ULBPaintShopPrototypeRootWidget::HandleSaveClicked()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
        Mode->SavePaintState(Reason);
    RefreshFromRuntime();
}

void ULBPaintShopPrototypeRootWidget::HandleLoadClicked()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
        Mode->LoadPaintState(Reason);
    RefreshFromRuntime();
}
