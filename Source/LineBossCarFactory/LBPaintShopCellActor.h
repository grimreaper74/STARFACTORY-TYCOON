#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPaintShopTypes.h"
#include "LBPaintShopCellActor.generated.h"

class UBoxComponent;
class UHierarchicalInstancedStaticMeshComponent;
class ULBPaintShopPortComponent;
class UMaterialInterface;
class USceneComponent;
class UStaticMesh;
class UStaticMeshComponent;

/**
 * Runtime display state for the isolated ED-coat cell. This deliberately remains
 * separate from the experimental Paint Shop SaveGame schema until runtime owns it.
 */
USTRUCT(BlueprintType)
struct FLBPaintShopCellPresentationState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bCarrierVisible = false;

    /** Progress from the carrier input to output along one complete dip bay. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0.0", ClampMax="1.0"))
    float CycleProgress01 = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, meta=(ClampMin="0.0", ClampMax="1.0"))
    float LiquidLevel01 = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    bool bFaulted = false;
};

/**
 * One fail-closed modular Paint Shop cell. The first tranche supports only the
 * canonical ED-coat dip definition and cannot mutate the legacy ED line.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPaintShopCellActor : public AActor
{
    GENERATED_BODY()

public:
    ALBPaintShopCellActor();

    virtual void OnConstruction(const FTransform& Transform) override;

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Cell")
    bool ConfigureCell(FName InCellId, FName InDefinitionId, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell")
    bool IsConfigured() const { return bConfigured; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell")
    FName GetCellId() const { return bConfigured ? CellId : NAME_None; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell")
    FName GetDefinitionId() const { return bConfigured ? DefinitionId : NAME_None; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell")
    FString GetConfigurationFailureReason() const { return ConfigurationFailureReason; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell")
    ULBPaintShopPortComponent* GetInputPort() const { return InputPort; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell")
    ULBPaintShopPortComponent* GetOutputPort() const { return OutputPort; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell")
    ULBPaintShopPortComponent* FindPort(FName PortId) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell")
    UBoxComponent* GetFootprint() const { return Footprint; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell")
    UBoxComponent* GetProtectedEnvelope() const { return ProtectedEnvelope; }

    const FLBPaintShopCellDefinition& GetDefinition() const { return Definition; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    bool HasCompletePresentationAssetSet() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    TArray<FString> GetRequiredPresentationAssetPaths() const;

    /** Every imported candidate mesh is visual-only; boxes own gameplay collision. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    bool AreCandidateMeshesVisualOnly() const;

    /** Two exact generated rail profiles required by the validated v002 NoRail modules. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    int32 GetProfiledRailSegmentCount() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    bool IsProfiledRailVisualOnly() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    UStaticMeshComponent* GetTreatmentStartPresentation() const { return TreatmentStartPresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    UStaticMeshComponent* GetTreatmentEndPresentation() const { return TreatmentEndPresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    UStaticMeshComponent* GetLiquidSurfacePresentation() const { return LiquidSurfacePresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    UStaticMeshComponent* GetCarrierTrolleyPresentation() const { return CarrierTrolleyPresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    UStaticMeshComponent* GetCarrierHoistPresentation() const { return CarrierHoistPresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    UStaticMeshComponent* GetCarrierHangerPresentation() const { return CarrierHangerPresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    UStaticMeshComponent* GetProxyBIWPresentation() const { return ProxyBIWPresentation; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Paint Shop|Cell|Presentation")
    FLBPaintShopCellPresentationState CapturePresentationState() const;

    static bool ValidatePresentationState(const FLBPaintShopCellPresentationState& State,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Cell|Presentation")
    bool RestorePresentationState(const FLBPaintShopCellPresentationState& State,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Paint Shop|Cell|Presentation")
    bool SetPresentationState(const FLBPaintShopCellPresentationState& State,
        FString& OutReason);

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> Footprint;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> ProtectedEnvelope;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBPaintShopPortComponent> InputPort;
    UPROPERTY(VisibleAnywhere) TObjectPtr<ULBPaintShopPortComponent> OutputPort;

    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> TreatmentStartPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> TreatmentEndPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> LiquidSurfacePresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UHierarchicalInstancedStaticMeshComponent> ProfiledRailPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> CarrierPresentationRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> CarrierTrolleyPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> CarrierHoistPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> CarrierHangerPresentation;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> ProxyBIWPresentation;

    UPROPERTY(VisibleInstanceOnly) bool bConfigured = false;
    UPROPERTY(VisibleInstanceOnly) FName CellId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) FName DefinitionId = NAME_None;
    UPROPERTY(VisibleInstanceOnly) FLBPaintShopCellDefinition Definition;
    UPROPERTY(VisibleInstanceOnly) FString ConfigurationFailureReason;
    UPROPERTY(VisibleInstanceOnly) FLBPaintShopCellPresentationState PresentationState;

    UPROPERTY() TSoftObjectPtr<UStaticMesh> TreatmentStartMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> TreatmentEndMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> LiquidSurfaceMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> CarrierTrolleyMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> CarrierHoistMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> CarrierHangerMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> ProxyBIWMesh;
    UPROPERTY() TSoftObjectPtr<UStaticMesh> ProfiledRailSegmentMesh;
    UPROPERTY() TSoftObjectPtr<UMaterialInterface> EDCoatLiquidMaterial;

    bool RebuildConfiguredPresentation(FString& OutReason);
    void RebuildProfiledRail(UStaticMesh* RailMesh);
    bool ConfigurePorts(FString& OutReason);
    void ApplyPresentationState();
    void ClearConfiguration(const FString& FailureReason);
    void ClearPresentationMeshes();
};
