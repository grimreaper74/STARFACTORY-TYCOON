#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "LBBodyShopTypes.h"
#include "LBBodyShopPortComponent.generated.h"

/** Typed internal Body Shop connection point; independent of the legacy global stage chain. */
UCLASS(ClassGroup=(LineBoss), meta=(BlueprintSpawnableComponent))
class LINEBOSSCARFACTORY_API ULBBodyShopPortComponent : public USceneComponent
{
    GENERATED_BODY()

public:
    ULBBodyShopPortComponent();

    void Configure(const FLBBodyShopPortDefinition& InDefinition);

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Port")
    FName GetPortId() const { return Definition.PortId; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Port")
    ELBBodyShopPortDirection GetDirection() const { return Definition.Direction; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Port")
    ELBBodyShopTransportType GetTransport() const { return Definition.Transport; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Port")
    FName GetMaterialId() const { return Definition.MaterialId; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Port")
    int32 GetCapacity() const { return Definition.Capacity; }

    const FLBBodyShopPortDefinition& GetDefinition() const { return Definition; }

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Body Shop|Port")
    FLBBodyShopPortDefinition Definition;
};

