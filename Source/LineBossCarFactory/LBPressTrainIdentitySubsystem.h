#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBPressTrainIdentitySubsystem.generated.h"

class ALBPressTrainAStation;
class ULBPressShopSaveGame;

/** Runtime authority for stable player-placed press-train identities. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBPressTrainIdentitySubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Trains|Identity")
    bool RegisterTrain(ALBPressTrainAStation* Train);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Trains|Identity")
    void ReleaseTrain(ALBPressTrainAStation* Train);

    /** Replaces a provisional spawn identity with an exact persisted identity. */
    bool RestoreTrainIdentity(ALBPressTrainAStation* Train, const FGuid& PersistentGuid,
        FName TrainId, const FString& DisplayName);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Identity")
    ALBPressTrainAStation* FindTrainByPersistentGuid(const FGuid& PersistentGuid) const;

    /** Captures the managed train set in deterministic designation order into the campaign root. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Trains|Save")
    bool CaptureAllTrains(ULBPressShopSaveGame* SaveRoot);

    /** Restores an exact identity-matched set; missing or duplicate authority fails closed. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Trains|Save")
    bool RestoreAllTrains(const ULBPressShopSaveGame* SaveRoot);

    /** Authoritative factory-builder placement using the retained Train A protected envelope. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Trains|Factory Builder")
    bool PlaceTrain(const FTransform& WorldTransform, const FString& DisplayName,
        const FString& PartFamily, ALBPressTrainAStation*& OutTrain);

    /** Read-only placement preflight for the player preview; allocates no actor or identity. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Trains|Factory Builder")
    bool CanPlaceTrain(const FTransform& WorldTransform, FString& OutReason) const;

    /** Removes only an isolated, empty train; survivors keep their designations. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Trains|Factory Builder")
    bool RemoveTrain(ALBPressTrainAStation* Train);

private:
    TMap<FGuid, TWeakObjectPtr<ALBPressTrainAStation>> TrainsByGuid;
    TMap<FName, TWeakObjectPtr<ALBPressTrainAStation>> TrainsById;
    /**
     * Actors owned by the player/campaign train set. Merely registering an authored
     * map actor does not make it disposable during a campaign restore.
     */
    TSet<TWeakObjectPtr<ALBPressTrainAStation>> ManagedTrains;
    bool bManagedSetEstablished = false;

    void PurgeInvalidEntries();
    FName FindNextAvailableTrainId() const;
    static bool IsValidTrainId(FName TrainId);
    static FBox BuildProtectedEnvelope(const FTransform& WorldTransform);
};
