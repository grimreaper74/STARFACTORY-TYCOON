#include "LBPR005HMIWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Fonts/SlateFontInfo.h"
#include "Styling/CoreStyle.h"

namespace LBPR005HMIColours
{
    static const FLinearColor Background(0.007f, 0.012f, 0.014f, 1.0f);
    static const FLinearColor Header(0.014f, 0.070f, 0.058f, 1.0f);
    static const FLinearColor OffWhite(0.89f, 0.88f, 0.83f, 1.0f);
    static const FLinearColor Muted(0.43f, 0.50f, 0.51f, 1.0f);
    static const FLinearColor Yellow(0.89f, 0.65f, 0.0f, 1.0f);
    static const FLinearColor Green(0.06f, 0.72f, 0.44f, 1.0f);
    static const FLinearColor Red(0.78f, 0.08f, 0.04f, 1.0f);
}

void ULBPR005HMIWidget::NativeConstruct()
{
    Super::NativeConstruct();
    BuildScreen();
    RefreshFromStation();
}

void ULBPR005HMIWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshAccumulator += InDeltaTime;
    if (RefreshAccumulator >= RefreshPeriodSeconds)
    {
        RefreshAccumulator = 0.0f;
        RefreshFromStation();
    }
}

void ULBPR005HMIWidget::BindStation(ALBPR005Station* InStation)
{
    Station = InStation;
    RefreshFromStation();
}

void ULBPR005HMIWidget::HandlePhysicalControlPower(bool bEnabled)
{
    if (Station.IsValid()) Station->SetControlPower(bEnabled);
}

bool ULBPR005HMIWidget::HandlePhysicalModeSelection(ELBPR005ControlMode NewMode)
{
    return Station.IsValid() && Station->SetControlMode(NewMode);
}

bool ULBPR005HMIWidget::HandlePhysicalCycleStart()
{
    return Station.IsValid() && Station->PressCycleStart();
}

void ULBPR005HMIWidget::HandlePhysicalControlledStop()
{
    if (Station.IsValid()) Station->RequestControlledStop();
}

bool ULBPR005HMIWidget::HandlePhysicalFaultReset()
{
    return Station.IsValid() && Station->ResetFault();
}

UTextBlock* ULBPR005HMIWidget::AddText(UCanvasPanel* Canvas, FName Name, const FString& InitialText,
    FVector2D Position, FVector2D Size, int32 FontSize, FLinearColor Colour, bool bBold)
{
    UTextBlock* Text = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
    Text->SetText(FText::FromString(InitialText));
    Text->SetColorAndOpacity(FSlateColor(Colour));
    Text->SetFont(FSlateFontInfo(FCoreStyle::GetDefaultFontStyle(bBold ? TEXT("Bold") : TEXT("Regular"), FontSize)));
    UCanvasPanelSlot* CanvasSlot = Canvas->AddChildToCanvas(Text);
    CanvasSlot->SetPosition(Position);
    CanvasSlot->SetSize(Size);
    return Text;
}

UButton* ULBPR005HMIWidget::AddButton(UCanvasPanel* Canvas, FName Name, const FString& Label,
    FVector2D Position, FVector2D Size, FLinearColor Colour, UTextBlock*& OutLabel)
{
    UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), Name);
    Button->SetBackgroundColor(Colour);
    OutLabel = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), *(Name.ToString() + TEXT("_Label")));
    OutLabel->SetText(FText::FromString(Label));
    OutLabel->SetJustification(ETextJustify::Center);
    OutLabel->SetColorAndOpacity(FSlateColor(LBPR005HMIColours::OffWhite));
    OutLabel->SetFont(FSlateFontInfo(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), 19)));
    Button->AddChild(OutLabel);
    UCanvasPanelSlot* CanvasSlot = Canvas->AddChildToCanvas(Button);
    CanvasSlot->SetPosition(Position);
    CanvasSlot->SetSize(Size);
    return Button;
}

void ULBPR005HMIWidget::BuildScreen()
{
    if (!WidgetTree || WidgetTree->RootWidget) return;

    UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("PR005_HMI_Root"));
    WidgetTree->RootWidget = Root;

    UBorder* Background = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("Background"));
    Background->SetBrushColor(LBPR005HMIColours::Background);
    UCanvasPanelSlot* BackgroundSlot = Root->AddChildToCanvas(Background);
    BackgroundSlot->SetPosition(FVector2D::ZeroVector);
    BackgroundSlot->SetSize(FVector2D(1024.0f, 768.0f));

    UBorder* Header = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("Header"));
    Header->SetBrushColor(LBPR005HMIColours::Header);
    UCanvasPanelSlot* HeaderSlot = Root->AddChildToCanvas(Header);
    HeaderSlot->SetPosition(FVector2D::ZeroVector);
    HeaderSlot->SetSize(FVector2D(1024.0f, 86.0f));

    AddText(Root, TEXT("CorporateTitle"), TEXT("CAIRNWELL AUTOMOTIVE · MOORCROSS WORKS"), FVector2D(28, 12), FVector2D(720, 34), 26, LBPR005HMIColours::OffWhite, true);
    AddText(Root, TEXT("StationTitle"), TEXT("PR005-DC01 · DECOILER / THREADER"), FVector2D(28, 47), FVector2D(620, 28), 18, LBPR005HMIColours::Muted);
    StateValue = AddText(Root, TEXT("StateValue"), TEXT("NO STATION"), FVector2D(760, 21), FVector2D(235, 42), 20, LBPR005HMIColours::Green, true);

    AddText(Root, TEXT("OverviewTitle"), TEXT("STATION OVERVIEW"), FVector2D(28, 112), FVector2D(280, 28), 19, LBPR005HMIColours::Yellow, true);
    ModeValue = AddText(Root, TEXT("ModeValue"), TEXT("MODE: OFF"), FVector2D(320, 112), FVector2D(300, 28), 18, LBPR005HMIColours::Muted, true);
    AddText(Root, TEXT("CoilLabel"), TEXT("COIL ID"), FVector2D(28, 168), FVector2D(190, 25), 16, LBPR005HMIColours::Muted);
    CoilValue = AddText(Root, TEXT("CoilValue"), TEXT("—"), FVector2D(218, 168), FVector2D(385, 25), 17, LBPR005HMIColours::OffWhite, true);
    AddText(Root, TEXT("RecipeLabel"), TEXT("RECIPE"), FVector2D(28, 207), FVector2D(190, 25), 16, LBPR005HMIColours::Muted);
    RecipeValue = AddText(Root, TEXT("RecipeValue"), TEXT("—"), FVector2D(218, 207), FVector2D(385, 25), 17, LBPR005HMIColours::OffWhite, true);
    AddText(Root, TEXT("WidthLabel"), TEXT("COIL / REQUIRED WIDTH"), FVector2D(28, 246), FVector2D(230, 25), 16, LBPR005HMIColours::Muted);
    WidthValue = AddText(Root, TEXT("WidthValue"), TEXT("—"), FVector2D(270, 246), FVector2D(333, 25), 17, LBPR005HMIColours::OffWhite, true);
    ProductionValue = AddText(Root, TEXT("ProductionValue"), TEXT("CYCLES 0 · STRIP 0.0 m · SCRAP 0"), FVector2D(28, 300), FVector2D(575, 28), 17, LBPR005HMIColours::OffWhite);

    AddText(Root, TEXT("ChecklistTitle"), TEXT("COMMISSIONING CHECKLIST"), FVector2D(28, 374), FVector2D(420, 28), 19, LBPR005HMIColours::Yellow, true);
    ChecklistValue = AddText(Root, TEXT("ChecklistValue"), TEXT("Waiting for station binding"), FVector2D(28, 416), FVector2D(590, 245), 17, LBPR005HMIColours::OffWhite);
    AddText(Root, TEXT("PermissiveTitle"), TEXT("SAFETY PERMISSIVES"), FVector2D(650, 112), FVector2D(345, 28), 19, LBPR005HMIColours::Yellow, true);
    PermissiveValue = AddText(Root, TEXT("PermissiveValue"), TEXT("No data"), FVector2D(650, 158), FVector2D(345, 218), 17, LBPR005HMIColours::OffWhite);
    AlarmValue = AddText(Root, TEXT("AlarmValue"), TEXT("ACTIVE ALARMS: —"), FVector2D(650, 405), FVector2D(345, 38), 18, LBPR005HMIColours::Red, true);

    UTextBlock* AuthoriseLabelRaw = nullptr;
    AuthoriseButton = AddButton(Root, TEXT("AuthoriseButton"), TEXT("AUTHORISE"), FVector2D(650, 475), FVector2D(345, 92), LBPR005HMIColours::Yellow, AuthoriseLabelRaw);
    AuthoriseLabel = AuthoriseLabelRaw;
    AuthoriseButton->OnClicked.AddDynamic(this, &ULBPR005HMIWidget::OnAuthoriseClicked);
    FooterValue = AddText(Root, TEXT("FooterValue"), TEXT("STATION NOT BOUND"), FVector2D(28, 719), FVector2D(968, 32), 16, LBPR005HMIColours::Muted);
}

void ULBPR005HMIWidget::RefreshFromStation()
{
    if (!StateValue || !Station.IsValid()) return;
    const FLBPR005HMIStatus Status = Station->GetHMIStatus();
    const UEnum* StateEnum = StaticEnum<ELBStationState>();
    const UEnum* ModeEnum = StaticEnum<ELBPR005ControlMode>();
    const UEnum* FaultEnum = StaticEnum<ELBPR005Fault>();
    const FString StateName = StateEnum ? StateEnum->GetNameStringByValue(static_cast<int64>(Status.MachineState)) : TEXT("UNKNOWN");
    const FString ModeName = ModeEnum ? ModeEnum->GetNameStringByValue(static_cast<int64>(Status.ControlMode)) : TEXT("UNKNOWN");
    const FString FaultName = FaultEnum ? FaultEnum->GetNameStringByValue(static_cast<int64>(Status.ActiveFault)) : TEXT("UNKNOWN");

    StateValue->SetText(FText::FromString(StateName.ToUpper()));
    StateValue->SetColorAndOpacity(FSlateColor(Status.ActiveFault == ELBPR005Fault::None ? LBPR005HMIColours::Green : LBPR005HMIColours::Red));
    ModeValue->SetText(FText::FromString(FString::Printf(TEXT("MODE: %s"), *ModeName.ToUpper())));
    CoilValue->SetText(FText::FromString(Status.CoilId.IsEmpty() ? TEXT("NO COIL") : Status.CoilId));
    RecipeValue->SetText(FText::FromName(Status.RecipeId));
    WidthValue->SetText(FText::FromString(FString::Printf(TEXT("%.0f / %.0f mm"), Status.CoilWidthMillimetres, Status.RequiredWidthMillimetres)));
    ProductionValue->SetText(FText::FromString(FString::Printf(TEXT("CYCLES %d · STRIP %.1f m · SCRAP %d · TARGET %.1f m/min"), Status.CycleCount, Status.StripLengthMetres, Status.ScrapCount, Status.TargetSpeedMetresPerMinute)));

    const TCHAR* Mark = TEXT("●");
    ChecklistValue->SetText(FText::FromString(FString::Printf(
        TEXT("%s CONTROL POWER\n%s UTILITIES AVAILABLE\n%s CORRECT COIL & RECIPE\n%s GUARDING CLOSED\n%s SAFETY CIRCUIT HEALTHY\n%s DRY CYCLE COMPLETE\n%s QUALITY APPROVED"),
        Status.bControlPowerOn ? Mark : TEXT("○"), Status.bUtilitiesAvailable ? Mark : TEXT("○"),
        Status.bCorrectCoilAndRecipe ? Mark : TEXT("○"), Status.bGuardsClosed ? Mark : TEXT("○"),
        Status.bSafetyCircuitHealthy ? Mark : TEXT("○"), Status.bDryCycleComplete ? Mark : TEXT("○"),
        Status.bQualityApproved ? Mark : TEXT("○"))));
    PermissiveValue->SetText(FText::FromString(Status.BlockingReasons.IsEmpty()
        ? TEXT("● ALL REQUIRED PERMISSIVES TRUE")
        : FString::JoinBy(Status.BlockingReasons, TEXT("\n"), [](const FText& Reason) { return FString(TEXT("○ ")) + Reason.ToString(); })));
    AlarmValue->SetText(FText::FromString(FString::Printf(TEXT("ACTIVE ALARM: %s"), *FaultName.ToUpper())));

    const bool bDryCycleAction = !Status.bCertifiedForProduction;
    const bool bEnabled = bDryCycleAction ? Status.bCanAuthoriseDryCycle : Status.bCanStartAutomatic;
    AuthoriseButton->SetIsEnabled(bEnabled);
    AuthoriseLabel->SetText(FText::FromString(bDryCycleAction ? TEXT("AUTHORISE DRY CYCLE") : TEXT("START AUTOMATIC")));
    FooterValue->SetText(FText::FromString(bEnabled ? TEXT("READY FOR PLAYER AUTHORISATION") : TEXT("ACTION BLOCKED · REVIEW PERMISSIVES")));
}

void ULBPR005HMIWidget::OnAuthoriseClicked()
{
    HandlePhysicalCycleStart();
    RefreshFromStation();
}
