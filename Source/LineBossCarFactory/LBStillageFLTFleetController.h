#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBCompactStillageFLT.h"
#include "LBStillageFLTFleetController.generated.h"

class ALBCompactStillageFLT;
class ALBPressShopStorageZone;
class USceneComponent;

USTRUCT(BlueprintType)
struct FLBStillageFLTFleetSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextUnitSerial = 2;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 NextJobSequence = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBCompactStillageFLTSaveState> Units;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBStillageFLTJob> Jobs;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_FiveParams(FOnLBStillageFLTFleetDelivery,
    FName, JobId, FName, StillageId, ELBStillageFLTJobType, JobType,
    FName, SourceAuthorityId, FName, TargetAuthorityId);

/**
 * Exact-once dispatcher and ownership authority for compact stillage FLTs.
 * A fresh placed controller commissions exactly one starter vehicle. Extra
 * units exist only after a successful paid purchase or campaign restore.
 */
UCLASS(BlueprintType, Blueprintable)
class LINEBOSSCARFACTORY_API ALBStillageFLTFleetController : public AActor
{
    GENERATED_BODY()

public:
    ALBStillageFLTFleetController();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** Idempotent fresh-campaign commissioning. Never creates more than the one starter entitlement. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Commissioning")
    bool InitialiseFreshFleet();

    /** Deducts the configured price only after the additional FLT has spawned successfully. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Purchase")
    bool TryPurchaseAdditionalFLT(UPARAM(ref) int32& InOutAvailableFunds);

    /**
     * High-level press-to-weld seam. The source still owns this exact full
     * StillageId until OnStillageDelivered fires. A panel-stillage storage
     * destination receives its deterministic first-free bay/tier (1..3).
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Jobs")
    bool EnqueueFullStillageTransfer(FName StillageId, AActor* FullPressWipStorage,
        AActor* WeldIntake, FVector2D StillageHalfExtentCm, FName& OutJobId);

    /** Explicit stacked destination. Pad ID and tier are persisted with the exact stillage job. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Jobs")
    bool EnqueueFullStillageTransferToStackTier(FName StillageId,
        AActor* FullPressWipStorage, AActor* WeldIntake, int32 TargetStackTier,
        FName TargetStackPadId, FVector2D StillageHalfExtentCm, FName& OutJobId);

    /**
     * High-level weld-to-press seam. Call only after weld has consumed the
     * panels and placed this exact StillageId in its empty-stillage store. A
     * panel-stillage destination receives its deterministic first-free bay/tier.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Jobs")
    bool EnqueueEmptyStillageReturn(FName StillageId, AActor* WeldEmptyStillageStorage,
        AActor* PressEmptyStillageStorage, FVector2D StillageHalfExtentCm, FName& OutJobId);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Jobs")
    bool EnqueueEmptyStillageReturnToStackTier(FName StillageId,
        AActor* WeldEmptyStillageStorage, AActor* PressEmptyStillageStorage,
        int32 TargetStackTier, FName TargetStackPadId,
        FVector2D StillageHalfExtentCm, FName& OutJobId);

    /** Low-level deterministic seam for tests or authored service-point actors. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Jobs")
    bool EnqueueExactJob(FName StillageId, ELBStillageFLTJobType JobType,
        FName SourceAuthorityId, FName TargetAuthorityId,
        FVector PickupServicePoint, FVector DropoffServicePoint,
        FVector2D StillageHalfExtentCm, FName& OutJobId);

    /** Low-level authored-pad seam. Rejects missing locators and tiers outside the common 1..3 limit. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Jobs")
    bool EnqueueExactJobToStackTier(FName StillageId, ELBStillageFLTJobType JobType,
        FName SourceAuthorityId, FName TargetAuthorityId,
        FVector PickupServicePoint, FVector DropoffServicePoint,
        int32 TargetStackTier, FName TargetStackPadId,
        float TargetStackPadYawDegrees, FVector2D StillageHalfExtentCm,
        FName& OutJobId);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Jobs")
    int32 DispatchPendingJobs();

    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT Fleet|Jobs")
    bool GetJobSnapshot(FName JobId, FLBStillageFLTJob& OutJob) const;
    /** Read-only deterministic ledger used to reconcile delivery events after restore/bind order changes. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT Fleet|Jobs")
    TArray<FLBStillageFLTJob> GetJobSnapshots() const;
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT Fleet|Jobs")
    bool HasOutstandingJobForStillage(FName StillageId) const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT Fleet|State")
    int32 GetFleetSize() const { return InstalledUnits.Num(); }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT Fleet|State")
    int32 GetStarterEntitlementCount() const { return FreshCampaignStarterUnitCount; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT Fleet|Purchase")
    int32 GetAdditionalFLTPurchaseCost() const { return AdditionalFLTPurchaseCost; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT Fleet|State")
    int32 GetPendingJobCount() const;
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT Fleet|State")
    int32 GetActiveJobCount() const;
    UFUNCTION(BlueprintPure, Category="Line Boss|Stillage FLT Fleet|State")
    ALBCompactStillageFLT* GetUnitById(FName UnitId) const;

    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Save")
    bool CaptureSaveState(FLBStillageFLTFleetSaveState& OutState) const;
    UFUNCTION(BlueprintCallable, Category="Line Boss|Stillage FLT Fleet|Save")
    bool RestoreSaveState(const FLBStillageFLTFleetSaveState& InState);

    UPROPERTY(BlueprintAssignable, Category="Line Boss|Stillage FLT Fleet|Events")
    FOnLBStillageFLTFleetDelivery OnStillageDelivered;

protected:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT Fleet|Commissioning")
    TSubclassOf<ALBCompactStillageFLT> UnitClass;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT Fleet|Commissioning")
    bool bAutoInitialiseFreshFleet = true;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT Fleet|Jobs")
    bool bAutoDispatchJobs = true;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT Fleet|Purchase", meta=(ClampMin="1"))
    int32 AdditionalFLTPurchaseCost = 45000;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT Fleet|Purchase", meta=(ClampMin="1", ClampMax="12"))
    int32 MaximumFleetSize = 8;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT Fleet|Layout", meta=(ClampMin="200.0"))
    float BerthSpacingCm = 320.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT Fleet|Layout", meta=(ClampMin="50.0"))
    float VehicleRootHeightCm = 83.0f;
    /** Clears loaded FLT planning expansion around source/target envelopes. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT Fleet|Layout", meta=(ClampMin="250.0"))
    float ServicePointStandOffCm = 375.0f;
    /** Minimum clear operating lane between actor-derived pickup/drop-off points. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Stillage FLT Fleet|Layout", meta=(ClampMin="500.0"))
    float MinimumServiceLaneLengthCm = 650.0f;

private:
    static constexpr int32 FreshCampaignStarterUnitCount = 1;

    UPROPERTY(VisibleAnywhere, Category="Line Boss|Stillage FLT Fleet|Layout") TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(Transient) TArray<TObjectPtr<ALBCompactStillageFLT>> InstalledUnits;
    UPROPERTY(VisibleInstanceOnly, SaveGame, Category="Line Boss|Stillage FLT Fleet|Jobs")
    TArray<FLBStillageFLTJob> Jobs;
    int32 NextUnitSerial = 1;
    int64 NextJobSequence = 1;
    bool bInitialised = false;

    ALBCompactStillageFLT* SpawnUnit(FName UnitId, const FVector& HomeBerth,
        const FRotator& Rotation);
    bool SpawnNextPurchasedUnit();
    bool BuildActorJob(AActor* SourceActor, AActor* TargetActor, FName StillageId,
        ELBStillageFLTJobType JobType, int32 TargetStackTier,
        FName TargetStackPadId, const FVector2D& StillageHalfExtentCm, FName& OutJobId);
    bool ResolveFirstFreeStorageStackAddress(
        const ALBPressShopStorageZone* TargetStorage,
        int32& OutTargetStackTier, FName& OutTargetStackPadId) const;
    bool ResolveAuthorityEnvelope(AActor* Actor, FName& OutAuthorityId,
        FVector& OutCentre, FVector2D& OutHalfExtent, FVector& OutAxisX,
        FVector& OutAxisY) const;
    bool CanDispatchDirection(const FLBStillageFLTJob& Candidate) const;
    bool ValidateSaveState(const FLBStillageFLTFleetSaveState& InState) const;

    UFUNCTION()
    void HandleUnitDelivered(FName UnitId, FName JobId, FName StillageId,
        bool bStillageWasFull);
    UFUNCTION()
    void HandleUnitFinished(FName UnitId, FName JobId, bool bSucceeded);
};
