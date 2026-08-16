#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "LBPR005Station.h"
#include "LBPR005HMIWidget.generated.h"

class UButton;
class UCanvasPanel;
class UTextBlock;

/**
 * Runtime 4:3 touchscreen for the shared Cairnwell operator cabinet.
 * It consumes only FLBPR005HMIStatus and invokes guarded controller commands;
 * it never writes a safety permissive or protected station field directly.
 */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ULBPR005HMIWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005|HMI")
    void BindStation(ALBPR005Station* InStation);

    UFUNCTION(BlueprintPure, Category = "Line Boss|PR-005|HMI")
    ALBPR005Station* GetBoundStation() const { return Station.Get(); }

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005|HMI|Physical Controls")
    void HandlePhysicalControlPower(bool bEnabled);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005|HMI|Physical Controls")
    bool HandlePhysicalModeSelection(ELBPR005ControlMode NewMode);

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005|HMI|Physical Controls")
    bool HandlePhysicalCycleStart();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005|HMI|Physical Controls")
    void HandlePhysicalControlledStop();

    UFUNCTION(BlueprintCallable, Category = "Line Boss|PR-005|HMI|Physical Controls")
    bool HandlePhysicalFaultReset();

protected:
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
    UPROPERTY(Transient) TWeakObjectPtr<ALBPR005Station> Station;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> StateValue;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ModeValue;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> CoilValue;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> RecipeValue;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> WidthValue;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ProductionValue;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> ChecklistValue;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> PermissiveValue;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> AlarmValue;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> FooterValue;
    UPROPERTY(Transient) TObjectPtr<UButton> AuthoriseButton;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> AuthoriseLabel;

    float RefreshAccumulator = 0.0f;
    static constexpr float RefreshPeriodSeconds = 0.1f;

    void BuildScreen();
    void RefreshFromStation();
    UTextBlock* AddText(UCanvasPanel* Canvas, FName Name, const FString& InitialText,
        FVector2D Position, FVector2D Size, int32 FontSize, FLinearColor Colour, bool bBold = false);
    UButton* AddButton(UCanvasPanel* Canvas, FName Name, const FString& Label,
        FVector2D Position, FVector2D Size, FLinearColor Colour, UTextBlock*& OutLabel);

    UFUNCTION() void OnAuthoriseClicked();
};
