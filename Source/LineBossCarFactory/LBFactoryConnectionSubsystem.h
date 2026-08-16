#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBFactoryConnectionSubsystem.generated.h"

class AActor;
class ALBFactoryTransportLink;
class ULBFactoryProcessPortComponent;

USTRUCT(BlueprintType)
struct FLBFactoryTransportLinkSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName SourcePortId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName TargetPortId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 TransferredUnits = 0;
};

/** Strict process-order authority for automatically connecting newly placed machinery. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBFactoryConnectionSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Connections")
    bool CanConnect(const ULBFactoryProcessPortComponent* Source,
        const ULBFactoryProcessPortComponent* Target, FString& OutReason) const;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Connections")
    bool Connect(ULBFactoryProcessPortComponent* Source, ULBFactoryProcessPortComponent* Target,
        ALBFactoryTransportLink*& OutLink, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Connections")
    bool AutoConnectNewMachine(AActor* NewlyPlacedMachine,
        TArray<ALBFactoryTransportLink*>& OutLinks, FString& OutReason);

    /** Removes one route from both endpoint caches and from the world link inventory. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Connections")
    bool Disconnect(ALBFactoryTransportLink* Link, FString& OutReason);

    /** Idempotently removes every route touching Actor and clears both sides of stale caches. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Connections")
    bool DisconnectActor(AActor* Actor, FString& OutReason);

    bool CaptureConnections(TArray<FLBFactoryTransportLinkSaveState>& OutStates) const;
    bool CaptureConnectionsForActor(const AActor* Actor,
        TArray<FLBFactoryTransportLinkSaveState>& OutStates, FString& OutReason) const;

    /**
     * Atomically replaces Actor's exact edge set after a proposed transform. Replacement
     * links are fully staged before the live port caches or old link actors are touched.
     */
    bool RebuildActorConnections(AActor* Actor,
        const TArray<FLBFactoryTransportLinkSaveState>& ExactStates, FString& OutReason);

    bool RestoreConnections(const TArray<FLBFactoryTransportLinkSaveState>& States, FString& OutReason);
};
