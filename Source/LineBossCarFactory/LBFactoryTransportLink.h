#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBFactoryTransportLink.generated.h"

class USplineComponent;
class UHierarchicalInstancedStaticMeshComponent;
class ULBFactoryProcessPortComponent;

/** Runtime authority for an automatically generated inter-machine transport path. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBFactoryTransportLink : public AActor
{
    GENERATED_BODY()

public:
    ALBFactoryTransportLink();

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Transport")
    bool Configure(ULBFactoryProcessPortComponent* Source, ULBFactoryProcessPortComponent* Target);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Transport")
    bool TryTransferUnits(int32 Quantity);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Transport")
    int32 GetTransferredUnits() const { return TransferredUnits; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Transport")
    ELBFactoryTransportKind GetTransportKind() const { return TransportKind; }

    ULBFactoryProcessPortComponent* GetSourcePort() const { return SourcePort.Get(); }
    ULBFactoryProcessPortComponent* GetTargetPort() const { return TargetPort.Get(); }

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Factory Builder|Transport")
    TObjectPtr<USplineComponent> RouteSpline;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Factory Builder|Transport")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SideRails;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Factory Builder|Transport")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> RollerOrBeltDeck;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Cairnwell|Factory Builder|Transport")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SupportLegs;

private:
    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Transport")
    TObjectPtr<ULBFactoryProcessPortComponent> SourcePort;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Transport")
    TObjectPtr<ULBFactoryProcessPortComponent> TargetPort;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Transport")
    ELBFactoryTransportKind TransportKind = ELBFactoryTransportKind::RollerConveyor;

    UPROPERTY(VisibleInstanceOnly, Category="Cairnwell|Factory Builder|Transport")
    int32 TransferredUnits = 0;

    void RebuildVisuals();
    void AddStraightVisualSection(const FVector& Start, const FVector& End);
};
