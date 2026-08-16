#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBFactoryEnvelopeSideDressingActor.generated.h"

class UHierarchicalInstancedStaticMeshComponent;
class USceneComponent;
class UStaticMesh;

/**
 * Lightweight, visual-only rhythm for the north and south factory envelope.
 *
 * It uses existing approved project meshes rather than baking routes or altering the
 * clean-shell map.  All instances are deliberately non-colliding/non-navigation so
 * the player-built layout, AGV paths and save state remain the source of truth.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBFactoryEnvelopeSideDressingActor : public AActor
{
    GENERATED_BODY()

public:
    ALBFactoryEnvelopeSideDressingActor();

    /** Resolves every approved source mesh before creating any visible side dressing. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Envelope")
    bool ActivatePresentation();

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope")
    bool IsPresentationActive() const { return bPresentationActive; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope")
    int32 GetColumnInstanceCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope")
    int32 GetBeamInstanceCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope")
    int32 GetServiceCabinetInstanceCount() const;

    /** Non-interactive exterior apron that keeps the open-roof planning view site-readable. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Envelope")
    int32 GetExteriorApronInstanceCount() const;

    /** Stable evidence for packaged soft-reference/cook validation. */
    TArray<FSoftObjectPath> GetRuntimeAssetPaths() const;

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> ColumnInstances;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> BeamInstances;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> ServiceCabinetInstances;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Factory Envelope")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> ExteriorApronInstances;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Factory Envelope")
    bool bPresentationActive = false;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> ColumnMesh;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> BeamMesh;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> ServiceCabinetMesh;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> ExteriorApronMesh;

    void ClearPresentation();
    void ConfigureVisualInstances(UHierarchicalInstancedStaticMeshComponent* Component) const;
};
