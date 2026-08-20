#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "LBOneFactoryProductionHUD.h"
#include "LBOneFactoryDetailPanelWidget.generated.h"

class UBorder;
class UButton;
class UTextBlock;

/**
 * UI v2 detail panel (U4): one template for every process group, opened by
 * a flow-strip card click. Cause first (why the group is in its state),
 * then the numbers, then a single honest primary action - the panel only
 * offers actions the runtime actually has.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryDetailPanelWidget
    : public UUserWidget
{
    GENERATED_BODY()

public:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry,
        float InDeltaTime) override;

    /** Shows the panel pinned to the given group index. */
    void ShowGroup(int32 GroupIndex);
    void Hide();
    bool IsShowing() const { return ShownGroupIndex != INDEX_NONE; }
    int32 GetShownGroupIndex() const { return ShownGroupIndex; }

private:
    /** What the one action button currently does. */
    enum class EPrimaryAction : uint8
    {
        Close,
        ResumeLine,
        ServiceFleet
    };

    void BuildTree();
    void Refresh();

    UFUNCTION() void OnPrimaryActionClicked();
    UFUNCTION() void OnCloseClicked();

    UPROPERTY() TObjectPtr<UBorder> PanelBorder;
    UPROPERTY() TObjectPtr<UTextBlock> TitleText;
    UPROPERTY() TObjectPtr<UTextBlock> DepartmentText;
    UPROPERTY() TObjectPtr<UTextBlock> CauseText;
    UPROPERTY() TObjectPtr<UTextBlock> StationsText;
    UPROPERTY() TObjectPtr<UTextBlock> UnitsText;
    UPROPERTY() TObjectPtr<UTextBlock> RateText;
    UPROPERTY() TObjectPtr<UTextBlock> ProgressText;
    UPROPERTY() TObjectPtr<UButton> PrimaryButton;
    UPROPERTY() TObjectPtr<UTextBlock> PrimaryLabel;
    UPROPERTY() TObjectPtr<UButton> CloseButton;

    int32 ShownGroupIndex = INDEX_NONE;
    EPrimaryAction PrimaryAction = EPrimaryAction::Close;
    float RefreshAccumulator = 0.0f;
};
