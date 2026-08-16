#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "LBBodyShopPrototypeHUD.generated.h"

class ALBBodyShopPrototypeWorldBootstrap;
class ULBBodyShopPrototypeRootWidget;

/**
 * Isolated UMG-only HUD host for the Body Shop prototype map.
 * It intentionally does not load, modify or overlay the Press Shop widget.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBBodyShopPrototypeHUD : public AHUD
{
    GENERATED_BODY()

public:
    ALBBodyShopPrototypeHUD();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

    static FString BuildIsolationReadout(bool bHasBootstrap, bool bFlagsValid,
        bool bWorldIsolationValid, bool bHasLegacyAuthority,
        bool bAuthoritiesBound);

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|UI")
    bool IsPrototypeWidgetActive() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype|UI")
    ULBBodyShopPrototypeRootWidget* GetPrototypeRootWidget() const
    {
        return PrototypeRootWidget.Get();
    }

private:
    UPROPERTY(Transient)
    TObjectPtr<ULBBodyShopPrototypeRootWidget> PrototypeRootWidget;

    bool EnsurePrototypeWidget();
    ALBBodyShopPrototypeWorldBootstrap* FindPrototypeBootstrap() const;
};
