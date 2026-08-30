#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "LBBodyWeldLineActor.h"
#include "LBPaintShopTypes.h"
#include "LBPaintShopExperimentalSaveGame.generated.h"

/** Runtime state persisted for one placed experimental Paint Shop cell. */
UENUM(BlueprintType)
enum class ELBPaintShopExperimentalCellState : uint8
{
    Planned,
    Commissioning,
    Idle,
    Processing,
    Starved,
    Blocked,
    Faulted
};

USTRUCT(BlueprintType)
struct FLBPaintShopPlacedCellSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName CellId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName DefinitionId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FTransform WorldTransform = FTransform::Identity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBPaintShopExperimentalCellState State = ELBPaintShopExperimentalCellState::Planned;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCommissioned = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FName> QueuedWIPIds;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ActiveWIPId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float ProcessProgress01 = 0.0f;

    /** Exact operator hold state for this cell; a paused process never advances on reload. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bProcessPaused = false;

    /** Exact downstream hold state, including a pre-block applied before output is ready. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bOutputBlocked = false;
};

USTRUCT(BlueprintType)
struct FLBPaintShopConnectionSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ConnectionId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName SourceCellId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName SourcePortId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName TargetCellId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName TargetPortId = NAME_None;
};

USTRUCT(BlueprintType)
struct FLBPaintShopWIPSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName UnitId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName MaterialId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName CurrentCellId = NAME_None;

    /** One carrier has at most one experimental WIP unit in v001. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName CarrierId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 GenealogySequence = 0;

    /**
     * Exact acknowledged Weld output. Version 1 WIP must leave this completely
     * default; version 2 WIP must carry one validated Good BIW without identity drift.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLBBodyInWhiteRecord SourceBodyInWhite;
};

/**
 * Isolated, versioned Paint Shop state. It deliberately owns no campaign data
 * and must validate completely before a runtime applies any part of it.
 */
USTRUCT(BlueprintType)
struct FLBPaintShopExperimentalSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBPaintShopPlacedCellSaveState> Cells;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBPaintShopConnectionSaveState> Connections;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBPaintShopWIPSaveState> WIP;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 NextCellSerial = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 NextConnectionSerial = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 NextWIPSerial = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int64 NextGenealogySequence = 1;
};

/**
 * Experimental Paint Shop persistence only. This class is intentionally
 * independent from every legacy line and production save contract.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ULBPaintShopExperimentalSaveGame : public USaveGame
{
    GENERATED_BODY()

public:
    static constexpr int32 SchemaVersion = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Line Boss|Paint Shop|Save")
    FLBPaintShopExperimentalSaveState State;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Line Boss|Paint Shop|Save")
    FString PrototypeMapId = TEXT("LB_PaintShop_Prototype_v001");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category="Line Boss|Paint Shop|Save")
    int32 SaveSchemaVersion = SchemaVersion;

    static FName GetSlotName();
    static int32 GetUserIndex() { return 0; }

    /** Mutation-free, fail-closed validation for an all-or-nothing runtime restore. */
    static bool ValidateExperimentalSaveState(const FLBPaintShopExperimentalSaveState& InState,
        FString& OutReason);
    bool ValidateForLoad(FString& OutReason) const;
};
