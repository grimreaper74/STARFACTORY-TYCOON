#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBBodyShopTypes.h"
#include "LBBodyShopRobotSlotConfigurationLibrary.generated.h"

class ALBBodyShopBuildAuthority;
class ALBBodyShopCellActor;

/** Explicit configuration operations; none of them permit free robot placement. */
UENUM(BlueprintType)
enum class ELBBodyShopRobotSlotMutation : uint8
{
    AddToVacantSlot,
    ReplaceOccupiedSlot,
    RemoveFromOccupiedSlot
};

/** One role/tool pairing authorised by an authored fixture slot. */
USTRUCT(BlueprintType)
struct FLBBodyShopRobotSelection
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ELBBodyShopRobotRole Role = ELBBodyShopRobotRole::None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ELBBodyShopToolType Tool = ELBBodyShopToolType::None;

    bool operator==(const FLBBodyShopRobotSelection& Other) const
    {
        return Role == Other.Role && Tool == Other.Tool;
    }
};

/** Read-only player-facing view of one fixture-owned robot slot. */
USTRUCT(BlueprintType)
struct FLBBodyShopRobotSlotView
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName SlotId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FTransform LocalMountTransform = FTransform::Identity;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FTransform WorldMountTransform = FTransform::Identity;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    float ReachRadiusCm = 0.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    float SweepRadiusCm = 0.0f;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FLBBodyShopRobotSelection> CompatibleSelections;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    bool bOccupied = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FLBBodyShopRobotAssignment CurrentAssignment;
};

/**
 * Body-Shop-only player configuration seam for authored robot mounts.
 *
 * Mutations delegate to ALBBodyShopBuildAuthority, so a slot must belong to a
 * placed Body Shop cell and the role/tool pairing must pass the canonical
 * definition contract. This library does not place robots freely, alter the
 * campaign save, or change the approved three-robot pilot baseline.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBBodyShopRobotSlotConfigurationLibrary
    : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot Configuration")
    static bool GetRobotSlotInventory(ALBBodyShopCellActor* Cell,
        TArray<FLBBodyShopRobotSlotView>& OutSlots, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot Configuration")
    static bool GetRobotSlot(ALBBodyShopCellActor* Cell, FName SlotId,
        FLBBodyShopRobotSlotView& OutSlot, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot Configuration")
    static bool IsRobotSelectionCompatible(ALBBodyShopCellActor* Cell, FName SlotId,
        ELBBodyShopRobotRole RobotRole, ELBBodyShopToolType Tool, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Robot Configuration")
    static bool CanApplyRobotSlotMutation(ALBBodyShopCellActor* Cell, FName SlotId,
        ELBBodyShopRobotSlotMutation Mutation, ELBBodyShopRobotRole RobotRole,
        ELBBodyShopToolType Tool, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Robot Configuration")
    static bool AddRobotToVacantSlot(ALBBodyShopBuildAuthority* BuildAuthority,
        FName CellId, FName SlotId, ELBBodyShopRobotRole RobotRole,
        ELBBodyShopToolType Tool, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Robot Configuration")
    static bool ReplaceRobotInOccupiedSlot(ALBBodyShopBuildAuthority* BuildAuthority,
        FName CellId, FName SlotId, ELBBodyShopRobotRole RobotRole,
        ELBBodyShopToolType Tool, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Robot Configuration")
    static bool RemoveRobotFromOccupiedSlot(ALBBodyShopBuildAuthority* BuildAuthority,
        FName CellId, FName SlotId, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Robot Configuration|Overlay")
    static bool SetCellRobotSlotOverlayVisible(ALBBodyShopBuildAuthority* BuildAuthority,
        FName CellId, bool bVisible, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Body Shop|Robot Configuration|Overlay")
    static bool SetAllRobotSlotOverlaysVisible(ALBBodyShopBuildAuthority* BuildAuthority,
        bool bVisible, int32& OutAffectedCellCount, FString& OutReason);

    /** Pure helpers kept public so the contract can be tested without launching a world. */
    static bool BuildSlotInventory(const FLBBodyShopCellDefinition& Definition,
        const TArray<FLBBodyShopRobotAssignment>& Assignments,
        const FTransform& CellWorldTransform, TArray<FLBBodyShopRobotSlotView>& OutSlots,
        FString& OutReason);

    static bool ValidateRobotSlotMutation(const FLBBodyShopCellDefinition& Definition,
        const TArray<FLBBodyShopRobotAssignment>& Assignments, FName SlotId,
        ELBBodyShopRobotSlotMutation Mutation, ELBBodyShopRobotRole RobotRole,
        ELBBodyShopToolType Tool, FString& OutReason);
};
