#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "LBBodyShopTypes.generated.h"

/** Approved prototype cells. The first implementation is fixture-cell based, not free robot CAD. */
UENUM(BlueprintType)
enum class ELBBodyShopCellType : uint8
{
    FullStillageDock,
    PanelPresentation,
    UnderbodyFixture,
    StraightSkidConveyor,
    BasicVisionGate,
    OutputBuffer
};

UENUM(BlueprintType)
enum class ELBBodyShopRobotRole : uint8
{
    None,
    PanelHandling,
    SpotWelding
};

UENUM(BlueprintType)
enum class ELBBodyShopToolType : uint8
{
    None,
    VacuumEightCup,
    SpotCGun,
    SprayApplicator
};

UENUM(BlueprintType)
enum class ELBBodyShopPortDirection : uint8
{
    Input,
    Output
};

UENUM(BlueprintType)
enum class ELBBodyShopTransportType : uint8
{
    StillageFLT,
    RobotHandoff,
    SkidConveyor
};

UENUM(BlueprintType)
enum class ELBBodyShopCellState : uint8
{
    Planned,
    Constructed,
    Commissioning,
    Idle,
    Starved,
    Running,
    Blocked,
    Faulted
};

UENUM(BlueprintType)
enum class ELBBodyShopQualityResult : uint8
{
    Pending,
    Pass,
    Fail
};

/** Limited authored process poses for fixture-mounted robots; this is not free robot programming. */
UENUM(BlueprintType)
enum class ELBBodyShopRobotPose : uint8
{
    Home,
    Acquire,
    Process,
    Retract,
    FaultSafe
};

/** Stable provisional material IDs approved for the modular Body Shop prototype. */
namespace LBBodyShopMaterialIds
{
    LINEBOSSCARFACTORY_API extern const FName Underbody;
    LINEBOSSCARFACTORY_API extern const FName SideLeft;
    LINEBOSSCARFACTORY_API extern const FName SideRight;
    LINEBOSSCARFACTORY_API extern const FName UpperStructure;
    LINEBOSSCARFACTORY_API extern const FName RoofOuter;
    LINEBOSSCARFACTORY_API extern const FName FramedBody;
    LINEBOSSCARFACTORY_API extern const FName CompleteBody;
    LINEBOSSCARFACTORY_API extern const FName PressedPanelStillage;
    LINEBOSSCARFACTORY_API extern const FName EmptyPanelStillage;
}

/** Stable cell and port IDs used by definitions, saves, tests and UI. */
namespace LBBodyShopPrototypeIds
{
    LINEBOSSCARFACTORY_API extern const FName FullStillageDock;
    LINEBOSSCARFACTORY_API extern const FName PanelPresentation;
    LINEBOSSCARFACTORY_API extern const FName UnderbodyFixture;
    LINEBOSSCARFACTORY_API extern const FName StraightSkidConveyor;
    LINEBOSSCARFACTORY_API extern const FName BasicVisionGate;
    LINEBOSSCARFACTORY_API extern const FName OutputBuffer;

    LINEBOSSCARFACTORY_API extern const FName StillageIn;
    LINEBOSSCARFACTORY_API extern const FName StillageOut;
    LINEBOSSCARFACTORY_API extern const FName PanelOut;
    LINEBOSSCARFACTORY_API extern const FName PanelIn;
    LINEBOSSCARFACTORY_API extern const FName SkidIn;
    LINEBOSSCARFACTORY_API extern const FName SkidOut;
    LINEBOSSCARFACTORY_API extern const FName BodyIn;
    LINEBOSSCARFACTORY_API extern const FName BodyOut;
}

USTRUCT(BlueprintType)
struct FLBBodyShopPortDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName PortId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) ELBBodyShopPortDirection Direction = ELBBodyShopPortDirection::Input;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) ELBBodyShopTransportType Transport = ELBBodyShopTransportType::RobotHandoff;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName MaterialId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FTransform LocalTransform = FTransform::Identity;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="1")) int32 Capacity = 1;
};

/** One authored and validated robot mounting position supplied by a fixture cell. */
USTRUCT(BlueprintType)
struct FLBBodyShopRobotSlotDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName SlotId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FTransform LocalMountTransform = FTransform::Identity;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TArray<ELBBodyShopRobotRole> AllowedRoles;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TArray<ELBBodyShopToolType> AllowedTools;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="1.0")) float ReachRadiusCm = 260.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="1.0")) float SweepRadiusCm = 190.0f;
};

USTRUCT(BlueprintType)
struct FLBBodyShopCellDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FName DefinitionId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) ELBBodyShopCellType CellType = ELBBodyShopCellType::FullStillageDock;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FText DisplayName;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FVector FootprintCm = FVector(400.0f, 300.0f, 250.0f);
    UPROPERTY(EditAnywhere, BlueprintReadOnly) FVector MaintenanceEnvelopeCm = FVector(500.0f, 400.0f, 300.0f);
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="0.0")) float CycleSeconds = 1.0f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, meta=(ClampMin="1")) int32 WIPCapacity = 1;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) bool bAutoAssembleSafetyAndServices = true;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TArray<FLBBodyShopPortDefinition> Ports;
    UPROPERTY(EditAnywhere, BlueprintReadOnly) TArray<FLBBodyShopRobotSlotDefinition> RobotSlots;
};

USTRUCT(BlueprintType)
struct FLBBodyShopRobotAssignment
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName SlotId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBBodyShopRobotRole Role = ELBBodyShopRobotRole::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBBodyShopToolType Tool = ELBBodyShopToolType::None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bEnabled = true;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float Condition01 = 1.0f;
};

USTRUCT(BlueprintType)
struct FLBBodyShopPlacedCellSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName CellId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName DefinitionId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FTransform WorldTransform = FTransform::Identity;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBBodyShopCellState State = ELBBodyShopCellState::Planned;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) bool bCommissioned = false;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyShopRobotAssignment> RobotAssignments;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FName> QueuedWIPIds;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ActiveWIPId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float ProcessProgress01 = 0.0f;
};

USTRUCT(BlueprintType)
struct FLBBodyShopConnectionSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ConnectionId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName SourceCellId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName SourcePortId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName TargetCellId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName TargetPortId = NAME_None;
};

USTRUCT(BlueprintType)
struct FLBBodyShopWIPSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName UnitId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName MaterialId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName CurrentCellId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName SourceStillageId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName SkidId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 GenealogySequence = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBBodyShopQualityResult Quality = ELBBodyShopQualityResult::Pending;
};

/** Standalone experimental persistence. It is deliberately not part of campaign save format 18. */
USTRUCT(BlueprintType)
struct FLBBodyShopExperimentalSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyShopPlacedCellSaveState> Cells;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyShopConnectionSaveState> Connections;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) TArray<FLBBodyShopWIPSaveState> WIP;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextCellSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextConnectionSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextWIPSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int64 NextGenealogySequence = 1;
};

/** Optional authoring asset. Runtime validation never trusts asset age or filename alone. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ULBBodyShopCellDefinitionAsset : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category="Line Boss|Body Shop")
    FLBBodyShopCellDefinition Definition;

    virtual FPrimaryAssetId GetPrimaryAssetId() const override;
};

/** Canonical prototype definitions and mutation-free contract validation. */
class LINEBOSSCARFACTORY_API FLBBodyShopDefinitionRegistry
{
public:
    static TArray<FName> GetApprovedUnderbodySliceDefinitionIds();
    static bool FindCanonicalDefinition(FName DefinitionId, FLBBodyShopCellDefinition& OutDefinition);
    static bool ValidateDefinition(const FLBBodyShopCellDefinition& Definition, FString& OutReason);
    static bool ValidateRobotAssignments(const FLBBodyShopCellDefinition& Definition,
        const TArray<FLBBodyShopRobotAssignment>& Assignments, FString& OutReason);
    static bool ValidateExperimentalSaveState(const FLBBodyShopExperimentalSaveState& State,
        FString& OutReason);
};
