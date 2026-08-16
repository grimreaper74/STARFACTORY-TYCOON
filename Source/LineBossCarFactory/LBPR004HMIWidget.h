#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Input/Reply.h"
#include "LBPR004HMIWidget.generated.h"

class ALBPR004Station;
class SButton;
class STextBlock;

/** Compact Cairnwell operator touchscreen for the simplified PR-004 workflow. */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ULBPR004HMIWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-004|HMI")
    void BindStation(ALBPR004Station* InStation);

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
    UPROPERTY(Transient) TWeakObjectPtr<ALBPR004Station> Station;
    TSharedPtr<STextBlock> StateValue;
    TSharedPtr<STextBlock> CoilValue;
    TSharedPtr<STextBlock> RecipeValue;
    TSharedPtr<STextBlock> ChecklistValue;
    TSharedPtr<STextBlock> FooterValue;
    TSharedPtr<SButton> UnpackageButton;
    TSharedPtr<STextBlock> UnpackageLabel;
    float RefreshAccumulator = 0.0f;

    void RefreshFromStation();
    FReply OnUnpackageClicked();
};
