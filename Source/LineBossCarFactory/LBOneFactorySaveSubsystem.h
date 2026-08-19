#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBOneFactorySaveGame.h"
#include "LBOneFactorySaveSubsystem.generated.h"

/**
 * Transaction boundary for the unified factory.
 *
 * It requires one data authority and one visual-only presentation actor per
 * department plus one production-ledger authority. Incoming and rollback
 * snapshots are fully preflighted before any live authority is mutated.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactorySaveSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    /** Fixed slot intentionally unrelated to every historic campaign slot. */
    static FString GetIsolatedSlotName();
    static int32 GetIsolatedUserIndex();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Save")
    FString GetSaveSlotName() const { return GetIsolatedSlotName(); }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Save")
    bool DoesOneFactorySaveExist() const;

    /** In-memory capture used by disk save and deterministic automation. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Save")
    bool CaptureCurrentFactory(FLBOneFactorySaveState& OutState,
        FString& OutReason) const;

    /** In-memory transactional restore with full authority/presentation rollback. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Save")
    bool RestoreFactoryState(const FLBOneFactorySaveState& State,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Save")
    bool SaveOneFactory(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Save")
    bool LoadOneFactory(FString& OutReason);

#if WITH_DEV_AUTOMATION_TESTS
    /** Forces failure after data commit so automation can prove full rollback. */
    void SetForcePresentationFailureForTests(const bool bForce)
    {
        bForcePresentationFailureForTests = bForce;
    }
#endif

private:
    /** Applies the saved management economy after a committed restore. */
    void RestoreManagementState(const FLBOneFactorySaveState& State) const;

#if WITH_DEV_AUTOMATION_TESTS
    bool bForcePresentationFailureForTests = false;
#endif
};

