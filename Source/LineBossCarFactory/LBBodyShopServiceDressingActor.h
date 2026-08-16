#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBBodyShopServiceDressingActor.generated.h"

class UHierarchicalInstancedStaticMeshComponent;
class USceneComponent;
class UStaticMesh;

/**
 * One explicitly empty service-apron prop beside the verified Body Shop line.
 *
 * These records are presentation contracts, not production inventory.  A dressing
 * item can never carry a process WIP identity or participate in line topology.
 */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBBodyShopServiceDressingItem
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Body Shop|Service Dressing")
    int32 Version = 1;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Body Shop|Service Dressing")
    FName PresentationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Body Shop|Service Dressing")
    FName Role = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Body Shop|Service Dressing")
    FSoftObjectPath AssetPath;

    /** Transform relative to the identity-aligned verified six-cell Body Shop root. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Body Shop|Service Dressing")
    FTransform RelativeTransform = FTransform::Identity;

    /** Conservative validation footprint; it does not create collision. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Body Shop|Service Dressing")
    FVector FootprintCm = FVector::ZeroVector;

    /** Frozen false: service dressing is never authoritative production WIP. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category="Line Boss|Body Shop|Service Dressing")
    bool bRepresentsProcessWIP = false;
};

/**
 * Deterministic, visual-only empty-container dressing for the Body Shop service aprons.
 *
 * The actor resolves all three clean-room native v002 presentation meshes before exposing
 * any instance. Missing art therefore produces an empty, failed-closed actor rather than
 * a misleading partial inventory. Source mesh materials are intentionally untouched.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBBodyShopServiceDressingActor : public AActor
{
    GENERATED_BODY()

public:
    ALBBodyShopServiceDressingActor();

    /** Atomically resolves and presents the complete approved empty-container layout. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Service Dressing")
    bool ActivatePresentation();

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Service Dressing")
    bool IsPresentationActive() const { return bPresentationActive; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Service Dressing")
    bool HasValidPresentationContract() const { return bPresentationContractValid; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Service Dressing")
    FString GetPresentationContractFailureReason() const
    {
        return PresentationContractFailureReason;
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Service Dressing")
    bool RepresentsProcessWIP() const { return bRepresentsProcessWIP; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Service Dressing")
    TArray<FLBBodyShopServiceDressingItem> GetPresentationLayout() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Service Dressing")
    int32 GetApprovedRoleCount(FName InRole) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Service Dressing")
    int32 GetVisibleInstanceCount() const;

    /** Stable validation/cook evidence in empty-return cart, pallet, crate order. */
    TArray<FSoftObjectPath> GetRuntimeAssetPaths() const;

    static FName GetEmptyReturnStillageRole();
    static FName GetComponentServicePalletRole();
    static FName GetEmptySmallPartsCrateRole();

    /** Exact immutable inventory, identities, roles, asset paths and relative transforms. */
    static TArray<FLBBodyShopServiceDressingItem> GetApprovedPresentationLayout();

    /** Exact clean-room native v002 presentation assets; none represents process WIP. */
    static TArray<FSoftObjectPath> GetApprovedNativeAssetPaths();

    /** Current six-cell v1 maintenance footprints, derived from the frozen definitions. */
    static TArray<FBox> GetVerifiedSixCellMaintenanceFootprints();

    /** Protected full-length, 260 cm-wide central skid-conveyor corridor. */
    static FBox GetCentralConveyorProtectedFootprint();

    /** Conservative plan footprint used only by deterministic validation and tests. */
    static FBox GetItemValidationFootprint(const FLBBodyShopServiceDressingItem& Item);

    /** Pure, exact validation seam. Any drift or WIP claim fails closed. */
    static bool ValidatePresentationContract(
        const TArray<FLBBodyShopServiceDressingItem>& Layout, FString& OutReason);

    /** Pure asset-resolution seam used by ActivatePresentation before any instance is made. */
    static bool ValidateResolvedAssetPaths(const TArray<FSoftObjectPath>& ResolvedAssetPaths,
        FString& OutReason);

private:
    UPROPERTY(VisibleAnywhere, Category="Line Boss|Body Shop|Service Dressing")
    TObjectPtr<USceneComponent> SceneRoot;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Body Shop|Service Dressing")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> EmptyReturnCartInstances;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Body Shop|Service Dressing")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> ComponentServicePalletInstances;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Body Shop|Service Dressing")
    TObjectPtr<UHierarchicalInstancedStaticMeshComponent> SmallPartsCrateInstances;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> EmptyReturnCartMesh;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> ComponentServicePalletMesh;

    UPROPERTY()
    TSoftObjectPtr<UStaticMesh> SmallPartsCrateMesh;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Service Dressing")
    bool bPresentationActive = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Service Dressing")
    bool bPresentationContractValid = false;

    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Service Dressing")
    FString PresentationContractFailureReason;

    /** Actor-level mirror of the per-item invariant; deliberately not editable. */
    UPROPERTY(VisibleInstanceOnly, Category="Line Boss|Body Shop|Service Dressing")
    bool bRepresentsProcessWIP = false;

    void ConfigureVisualInstances(UHierarchicalInstancedStaticMeshComponent* Component) const;
    void ClearPresentation();
    UHierarchicalInstancedStaticMeshComponent* FindComponentForAssetPath(
        const FSoftObjectPath& AssetPath) const;
};
