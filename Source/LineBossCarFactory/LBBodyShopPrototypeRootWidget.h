#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "LBBodyShopPrototypeRuntime.h"
#include "LBBodyShopPrototypeRootWidget.generated.h"

class ALBBodyShopManagementPawn;
class ALBBodyShopPrototypeRuntime;
class UButton;
class UTextBlock;

/**
 * Native UMG operator surface for the isolated Body Shop vertical slice.
 *
 * This deliberately replaces the temporary Canvas banner. It exposes only the
 * bounded pilot controls already owned by ALBBodyShopPrototypeRuntime; it does
 * not import the Press Shop management widget or campaign/save authority.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ULBBodyShopPrototypeRootWidget : public UUserWidget
{
    GENERATED_BODY()

public:
    static TArray<FName> GetCanonicalControlIds();
    static FString GetPrimaryActionLabel(ELBBodyShopRuntimeStage Stage,
        bool bSimulationRunning);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Prototype|UI")
    void RefreshFromRuntime();

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|UI")
    bool HasRenderableShell() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|UI")
    FString GetLastActionText() const { return LastActionText; }

protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    virtual void NativeOnInitialized() override;
    virtual void NativeConstruct() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
    UPROPERTY(Transient) TObjectPtr<UTextBlock> StageLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> StatusLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> WIPLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> LastActionLabel;
    UPROPERTY(Transient) TObjectPtr<UTextBlock> PrimaryActionLabel;
    UPROPERTY(Transient) TObjectPtr<UButton> PrimaryActionButton;
    UPROPERTY(Transient) TObjectPtr<UButton> SaveButton;
    UPROPERTY(Transient) TObjectPtr<UButton> LoadButton;
    UPROPERTY(Transient) TObjectPtr<UButton> ClearHeldButton;
    UPROPERTY(Transient) TObjectPtr<UButton> RobotSlotsButton;

    FString LastActionText = TEXT("Ready for operator input");
    float RefreshAccumulatorSeconds = 0.0f;

    void BuildShell();
    void SetLastAction(const FString& Message, bool bError);
    ALBBodyShopPrototypeRuntime* ResolveRuntime() const;
    ALBBodyShopManagementPawn* ResolveManagementPawn() const;

    UFUNCTION() void HandlePrimaryActionClicked();
    UFUNCTION() void HandleSaveClicked();
    UFUNCTION() void HandleLoadClicked();
    UFUNCTION() void HandleClearHeldClicked();
    UFUNCTION() void HandleRobotSlotsClicked();
};
