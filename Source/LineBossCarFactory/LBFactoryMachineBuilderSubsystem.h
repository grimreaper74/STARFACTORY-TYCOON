#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBFactoryBuildMachine.h"
#include "LBPressShopStorageZone.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBECoatLineActor.h"
#include "LBBodyWeldLineActor.h"
#include "LBFactoryMachineBuilderSubsystem.generated.h"

class ALBPressTrainAStation;
class ALBFactoryTransportLink;

/** Ordered player-build catalogue and placement authority for the Press Shop process chain. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBFactoryMachineBuilderSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machines")
    bool CanPlaceMachine(ELBFactoryBuildMachineType MachineType, FString& OutReason) const;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machines")
    bool PlaceMachine(ELBFactoryBuildMachineType MachineType, const FTransform& WorldTransform,
        AActor*& OutMachine, FString& OutReason);

#if !UE_BUILD_SHIPPING
    /** Development-only deterministic QA fixture seam; never exposed to player placement. */
    AActor* PlaceMachineForVisualQA(ELBFactoryBuildMachineType MachineType,
        const FTransform& WorldTransform, FString& OutReason);
#endif

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machines")
    TArray<ELBFactoryBuildMachineType> GetAvailableMachineTypes() const;

    /** Stable placement contract used by previews and the final authoritative spawn. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machines")
    bool GetMachinePlacementEnvelope(ELBFactoryBuildMachineType MachineType,
        FVector& OutHalfExtent, FVector& OutRelativeCentre, float& OutRootHeightCm,
        FString& OutReason) const;

    /** Validates the complete protected footprint against floor, utilities and live assets. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machines")
    bool ValidateMachineTransform(ELBFactoryBuildMachineType MachineType,
        const FTransform& WorldTransform, FString& OutReason) const;

    /** C++ edit preflight; the selected actor is excluded from catalogue and overlap checks. */
    bool ValidateMachineTransform(ELBFactoryBuildMachineType MachineType,
        const FTransform& WorldTransform, const ALBFactoryBuildMachine* IgnoredMachine,
        FString& OutReason) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machines|Editing")
    bool ValidateMachineTransformForEdit(FName MachineId,
        const FTransform& WorldTransform, FString& OutReason) const;

    /** Fail-closed WIP, reservation, controller and ownership gate shared by move/remove. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Machines|Editing")
    bool CanEditMachine(FName MachineId, FString& OutReason) const;

    /** Transactional move preserving identity, process ports, exact links and transfer counters. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machines|Editing")
    bool MoveMachine(FName MachineId, const FTransform& WorldTransform, FString& OutReason);

    /** Idempotent removal; live WIP, reservations and external ownership always reject. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|Machines|Editing")
    bool RemoveMachine(FName MachineId, FString& OutReason);

    /** Storage choices compatible with the process chain already built in this world. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Storage")
    TArray<ELBPressShopStorageType> GetAvailableStorageTypes() const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV")
    bool CanPlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType Type, int32 TrainIndex, FString& OutReason) const;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|AGV")
    bool PlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType Type, int32 TrainIndex,
        const FTransform& WorldTransform, ALBFactoryAGVInfrastructure*& OutInfrastructure, FString& OutReason);

    /** Full floor, protected-envelope and editable-layout preflight used by preview and final placement. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV")
    bool ValidateAGVInfrastructurePlacement(ELBFactoryAGVInfrastructureType Type, int32 TrainIndex,
        const FTransform& WorldTransform, FString& OutReason) const;

    /** Post-placement edit authority used by the route/walkway move tool; save captures the result. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder|AGV")
    bool UpdateAGVInfrastructureTransform(FName InfrastructureId,
        const FTransform& WorldTransform, FString& OutReason);

    /** Read-only transform preflight for the post-placement route/walkway editor. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV")
    bool ValidateAGVInfrastructureTransform(FName InfrastructureId,
        const FTransform& WorldTransform, FString& OutReason) const;

    /** Moving-route safety gate. Route geometry may only change while every bound coil AGV is idle. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV")
    bool CanEditAGVInfrastructure(FName InfrastructureId, FString& OutReason) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Infrastructure")
    TArray<ELBFactoryAGVInfrastructureType> GetAvailableInfrastructureTypes() const;

    /** First press train A-D without an S01 handoff, or INDEX_NONE when all four are assigned. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|AGV")
    int32 GetNextAvailablePressTrainHandoffIndex() const;

    bool CaptureAGVInfrastructure(TArray<FLBFactoryAGVInfrastructureSaveState>& OutStates) const;
    bool RestoreAGVInfrastructure(const TArray<FLBFactoryAGVInfrastructureSaveState>& States, FString& OutReason);

    bool CaptureMachines(TArray<FLBFactoryBuildMachineSaveState>& OutStates) const;
    bool ValidateMachineSaveSet(const TArray<FLBFactoryBuildMachineSaveState>& States,
        FString& OutReason) const;
    bool RestoreMachines(const TArray<FLBFactoryBuildMachineSaveState>& States, FString& OutReason);

    bool CaptureBodyWeldLines(TArray<FLBBodyWeldLineSaveState>& OutStates) const;
    bool ValidateBodyWeldLineSaveSet(const TArray<FLBBodyWeldLineSaveState>& States,
        FString& OutReason) const;
    bool RestoreBodyWeldLines(const TArray<FLBBodyWeldLineSaveState>& States, FString& OutReason);

    bool CaptureECoatLines(TArray<FLBECoatLineSaveState>& OutStates) const;
    bool ValidateECoatLineSaveSet(const TArray<FLBECoatLineSaveState>& States,
        FString& OutReason) const;
    bool RestoreECoatLines(const TArray<FLBECoatLineSaveState>& States, FString& OutReason);

private:
    /** Automatic inbound paint may enter its two connected machine handoff envelopes only. */
    bool PlaceAGVInfrastructureAllowingConnectedMachines(
        ELBFactoryAGVInfrastructureType Type, int32 TrainIndex,
        const FTransform& WorldTransform, const ALBFactoryBuildMachine* AllowedStartMachine,
        const ALBFactoryBuildMachine* AllowedDockMachine,
        ALBFactoryAGVInfrastructure*& OutInfrastructure, FString& OutReason);
    bool CreateAutomaticInboundAGVRoute(ALBFactoryBuildMachine* InboundDock,
        ALBFactoryBuildMachine* PR002Cell, FString& OutReason);
    int32 CreateAutomaticServiceWalkways(const TArray<ALBFactoryTransportLink*>& Links);
    bool HasGenericMachine(ELBFactoryBuildMachineType Type) const;
    bool HasBodyWeldLine() const;
    bool HasECoatLine() const;
    bool HasStorageType(uint8 StorageTypeValue) const;
    FName AllocateMachineId(ELBFactoryBuildMachineType Type) const;
    FName AllocateBodyWeldLineId() const;
    FName AllocateECoatLineId() const;
    FName AllocateAGVInfrastructureId(ELBFactoryAGVInfrastructureType Type, int32 TrainIndex) const;
    bool RebindIdleCoilAGVsAfterInfrastructureEdit(ALBFactoryAGVInfrastructure* Edited,
        FString& OutReason) const;
};
