#include "LBPR004HMIWidget.h"

#include "LBPR004Station.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace LBPR004HMIColours
{
    static const FLinearColor Background(0.007f, 0.012f, 0.014f, 1.0f);
    static const FLinearColor Header(0.014f, 0.070f, 0.058f, 1.0f);
    static const FLinearColor OffWhite(0.89f, 0.88f, 0.83f, 1.0f);
    static const FLinearColor Muted(0.43f, 0.50f, 0.51f, 1.0f);
    static const FLinearColor Yellow(0.89f, 0.65f, 0.0f, 1.0f);
    static const FLinearColor Green(0.06f, 0.72f, 0.44f, 1.0f);
    static const FLinearColor Red(0.78f, 0.08f, 0.04f, 1.0f);
}

namespace
{
    FSlateFontInfo HMIFont(const int32 Size, const bool bBold = false)
    {
        return FCoreStyle::GetDefaultFontStyle(bBold ? TEXT("Bold") : TEXT("Regular"), Size);
    }

    TSharedRef<SWidget> MakeCaption(const TCHAR* Text)
    {
        return SNew(STextBlock)
            .Text(FText::FromString(Text))
            .Font(HMIFont(18, true))
            .ColorAndOpacity(LBPR004HMIColours::Yellow);
    }
}

TSharedRef<SWidget> ULBPR004HMIWidget::RebuildWidget()
{
    return SNew(SBorder)
        .BorderBackgroundColor(LBPR004HMIColours::Background)
        .Padding(0.0f)
        [
            SNew(SVerticalBox)
            + SVerticalBox::Slot()
            .AutoHeight()
            [
                SNew(SBox)
                .HeightOverride(108.0f)
                [
                    SNew(SBorder)
                    .BorderBackgroundColor(LBPR004HMIColours::Header)
                    .Padding(FMargin(28.0f, 14.0f))
                    [
                        SNew(SHorizontalBox)
                        + SHorizontalBox::Slot()
                        .FillWidth(1.0f)
                        [
                            SNew(SVerticalBox)
                            + SVerticalBox::Slot()
                            .AutoHeight()
                            [
                                SNew(STextBlock)
                                .Text(FText::FromString(TEXT("CAIRNWELL AUTOMOTIVE / MOORCROSS WORKS")))
                                .Font(HMIFont(27, true))
                                .ColorAndOpacity(LBPR004HMIColours::OffWhite)
                            ]
                            + SVerticalBox::Slot()
                            .AutoHeight()
                            .Padding(0.0f, 8.0f, 0.0f, 0.0f)
                            [
                                SNew(STextBlock)
                                .Text(FText::FromString(TEXT("PR-004 / COIL PREPARATION")))
                                .Font(HMIFont(20, true))
                                .ColorAndOpacity(LBPR004HMIColours::Muted)
                            ]
                        ]
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        .VAlign(VAlign_Center)
                        [
                            SAssignNew(StateValue, STextBlock)
                            .Text(FText::FromString(TEXT("NO STATION")))
                            .Font(HMIFont(21, true))
                            .ColorAndOpacity(LBPR004HMIColours::Green)
                        ]
                    ]
                ]
            ]
            + SVerticalBox::Slot()
            .FillHeight(1.0f)
            .Padding(FMargin(42.0f, 42.0f, 42.0f, 20.0f))
            [
                SNew(SHorizontalBox)
                + SHorizontalBox::Slot()
                .FillWidth(0.62f)
                .Padding(0.0f, 0.0f, 28.0f, 0.0f)
                [
                    SNew(SVerticalBox)
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    [MakeCaption(TEXT("SELECTED COIL"))]
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 10.0f, 0.0f, 30.0f)
                    [
                        SAssignNew(CoilValue, STextBlock)
                        .Text(FText::FromString(TEXT("-")))
                        .Font(HMIFont(24, true))
                        .ColorAndOpacity(LBPR004HMIColours::OffWhite)
                    ]
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    [MakeCaption(TEXT("PREPARATION RECORD"))]
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 10.0f, 0.0f, 30.0f)
                    [
                        SAssignNew(RecipeValue, STextBlock)
                        .Text(FText::FromString(TEXT("-")))
                        .Font(HMIFont(22, true))
                        .ColorAndOpacity(LBPR004HMIColours::OffWhite)
                    ]
                    + SVerticalBox::Slot()
                    .FillHeight(1.0f)
                    [
                        SAssignNew(ChecklistValue, STextBlock)
                        .Text(FText::FromString(TEXT("Waiting for station binding")))
                        .Font(HMIFont(18))
                        .ColorAndOpacity(LBPR004HMIColours::OffWhite)
                    ]
                ]
                + SHorizontalBox::Slot()
                .FillWidth(0.38f)
                .VAlign(VAlign_Top)
                .Padding(10.0f, 40.0f, 0.0f, 0.0f)
                [
                    SNew(SBox)
                    .HeightOverride(138.0f)
                    [
                        SAssignNew(UnpackageButton, SButton)
                        .ButtonColorAndOpacity(LBPR004HMIColours::Yellow)
                        .HAlign(HAlign_Center)
                        .VAlign(VAlign_Center)
                        .OnClicked(FOnClicked::CreateUObject(this, &ULBPR004HMIWidget::OnUnpackageClicked))
                        [
                            SAssignNew(UnpackageLabel, STextBlock)
                            .Text(FText::FromString(TEXT("UNPACKAGE COIL")))
                            .Font(HMIFont(24, true))
                            .ColorAndOpacity(LBPR004HMIColours::Background)
                        ]
                    ]
                ]
            ]
            + SVerticalBox::Slot()
            .AutoHeight()
            .Padding(FMargin(42.0f, 0.0f, 42.0f, 24.0f))
            [
                SAssignNew(FooterValue, STextBlock)
                .Text(FText::FromString(TEXT("STATION NOT BOUND")))
                .Font(HMIFont(18, true))
                .ColorAndOpacity(LBPR004HMIColours::Muted)
            ]
        ];
}

void ULBPR004HMIWidget::NativeConstruct()
{
    Super::NativeConstruct();
    RefreshFromStation();
}

void ULBPR004HMIWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    RefreshAccumulator += InDeltaTime;
    if (RefreshAccumulator >= 0.1f)
    {
        RefreshAccumulator = 0.0f;
        RefreshFromStation();
    }
}

void ULBPR004HMIWidget::BindStation(ALBPR004Station* InStation)
{
    Station = InStation;
    RefreshFromStation();
}

void ULBPR004HMIWidget::RefreshFromStation()
{
    if (!StateValue.IsValid() || !Station.IsValid()) return;
    const UEnum* StateEnum = StaticEnum<ELBPR004State>();
    const FString StateName = StateEnum ? StateEnum->GetNameStringByValue(static_cast<int64>(Station->GetProcessState())) : TEXT("UNKNOWN");
    StateValue->SetText(FText::FromString(StateName.ToUpper()));
    StateValue->SetColorAndOpacity(Station->GetActiveFault() == ELBPR004Fault::None ? LBPR004HMIColours::Green : LBPR004HMIColours::Red);
    CoilValue->SetText(FText::FromString(Station->GetCurrentCoilId().IsEmpty() ? TEXT("NO COIL LOADED") : Station->GetCurrentCoilId()));
    RecipeValue->SetText(FText::FromName(Station->GetActiveRecipeId()));
    TArray<FText> BlockingReasons;
    const bool bCanUnpackage = Station->CanUnpackageCoil(BlockingReasons);
    ChecklistValue->SetText(FText::FromString(BlockingReasons.IsEmpty()
        ? TEXT("READY\nCradle locked\nC-hook withdrawn\nIdentity and recipe matched")
        : FString::JoinBy(BlockingReasons, TEXT("\n"), [](const FText& Reason) { return FString(TEXT("- ")) + Reason.ToString(); })));
    UnpackageButton->SetEnabled(bCanUnpackage);
    UnpackageLabel->SetText(FText::FromString(Station->IsCoilUnpackaged() ? TEXT("COIL UNPACKAGED") : TEXT("UNPACKAGE COIL")));
    FooterValue->SetText(FText::FromString(bCanUnpackage ? TEXT("READY FOR PLAYER ACTION") : TEXT("ACTION BLOCKED / REVIEW CHECKLIST")));
}

FReply ULBPR004HMIWidget::OnUnpackageClicked()
{
    if (Station.IsValid()) Station->UnpackageCoil(TEXT("HMI_UNPACKAGE_BUTTON"));
    RefreshFromStation();
    return FReply::Handled();
}
