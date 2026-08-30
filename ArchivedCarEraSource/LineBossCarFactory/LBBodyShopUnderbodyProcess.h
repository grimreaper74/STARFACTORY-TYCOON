#pragma once

#include "CoreMinimal.h"
#include "LBBodyShopTypes.h"
#include "LBBodyShopUnderbodyProcess.generated.h"

/** Product architecture choice for the centre of the pilot underbody kit. */
UENUM(BlueprintType)
enum class ELBBodyShopUnderbodyArchitecture : uint8
{
    CentreTunnel,
    EVBatteryTray
};

/** How a component participates in the stable underbody component catalogue. */
UENUM(BlueprintType)
enum class ELBBodyShopUnderbodyComponentRule : uint8
{
    Required,
    ExactlyOneFromChoiceGroup,
    Optional
};

namespace LBBodyShopUnderbodyRecipeIds
{
    LINEBOSSCARFACTORY_API extern const FName TunnelPilotV1;
    LINEBOSSCARFACTORY_API extern const FName EVPilotV1;
}

namespace LBBodyShopUnderbodyChoiceGroupIds
{
    LINEBOSSCARFACTORY_API extern const FName CentreStructure;
}

namespace LBBodyShopUnderbodyComponentIds
{
    LINEBOSSCARFACTORY_API extern const FName FloorPan;
    LINEBOSSCARFACTORY_API extern const FName CentreTunnel;
    LINEBOSSCARFACTORY_API extern const FName EVBatteryTray;
    LINEBOSSCARFACTORY_API extern const FName LongitudinalRailLeft;
    LINEBOSSCARFACTORY_API extern const FName LongitudinalRailRight;
    LINEBOSSCARFACTORY_API extern const FName Crossmembers;
    LINEBOSSCARFACTORY_API extern const FName SideSillLeft;
    LINEBOSSCARFACTORY_API extern const FName SideSillRight;
    LINEBOSSCARFACTORY_API extern const FName FrontFloorPartition;
    LINEBOSSCARFACTORY_API extern const FName RearFloorPartition;
}

namespace LBBodyShopUnderbodyJoinOperationIds
{
    LINEBOSSCARFACTORY_API extern const FName ResistanceSpotWeld;
    LINEBOSSCARFACTORY_API extern const FName LaserWeldOrBraze;
    LINEBOSSCARFACTORY_API extern const FName MigMagWeld;
    LINEBOSSCARFACTORY_API extern const FName AdhesiveBond;
    LINEBOSSCARFACTORY_API extern const FName SelfPiercingRivet;
}

namespace LBBodyShopUnderbodyQualityCheckIds
{
    LINEBOSSCARFACTORY_API extern const FName DeburrAndFinish;
    LINEBOSSCARFACTORY_API extern const FName DimensionalAlignment;
    LINEBOSSCARFACTORY_API extern const FName WeldIntegrity;
}

namespace LBBodyShopUnderbodyProcessStepIds
{
    LINEBOSSCARFACTORY_API extern const FName PresentComponentKit;
    LINEBOSSCARFACTORY_API extern const FName LocateInFixture;
    LINEBOSSCARFACTORY_API extern const FName JoinPrimaryStructure;
    LINEBOSSCARFACTORY_API extern const FName TransferOnSkid;
    LINEBOSSCARFACTORY_API extern const FName DeburrAndFinishCheck;
    LINEBOSSCARFACTORY_API extern const FName DimensionalCheck;
    LINEBOSSCARFACTORY_API extern const FName WeldIntegrityCheck;
    LINEBOSSCARFACTORY_API extern const FName ReleaseUnderbody;
}

USTRUCT(BlueprintType)
struct FLBBodyShopUnderbodyComponentDefinition
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName ComponentId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ELBBodyShopUnderbodyComponentRule Rule = ELBBodyShopUnderbodyComponentRule::Required;

    /** Non-empty only for ExactlyOneFromChoiceGroup components. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName ChoiceGroupId = NAME_None;
};

/**
 * Non-persistent manufacturing recipe for one BIW_UNDERBODY genealogy unit.
 * It deliberately adds no fields to experimental save v1 or campaign v18.
 */
USTRUCT(BlueprintType)
struct FLBBodyShopUnderbodyProcessRecipe
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int32 ContractVersion = 1;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName RecipeId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName OutputMaterialId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ELBBodyShopUnderbodyArchitecture Architecture =
        ELBBodyShopUnderbodyArchitecture::CentreTunnel;

    /** One entry per physical kit item; front and rear partitions are optional. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> SelectedComponentIds;

    /** The current two-C-gun pilot cell must execute these operations. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> RequiredJoinOperationIds;

    /** Stable supported alternatives for future authored fixture variants. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> SupportedVariantJoinOperationIds;

    /** Material-specific optional operation; not fitted to the current pilot cell. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> OptionalJoinOperationIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> RequiredQualityCheckIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> OrderedProcessStepIds;

    /** Player configures authored fixture cells, robot slots and tools. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    bool bUsesAuthoredFixtureCells = true;

    /** The first implementation is intentionally not six-axis robot CAD. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    bool bAllowsUnrestrictedRobotPlacement = false;
};

/** Stable, Body-Shop-only underbody process definitions and pure validation. */
class LINEBOSSCARFACTORY_API FLBBodyShopUnderbodyProcessRegistry
{
public:
    static TArray<FName> GetStableComponentIds();
    static TArray<FName> GetStableJoinOperationIds();
    static TArray<FName> GetStableQualityCheckIds();
    static TArray<FName> GetStableProcessStepIds();
    static TArray<FLBBodyShopUnderbodyComponentDefinition> GetComponentDefinitions();

    /** Builds the canonical first-slice kit. Optional partitions are excluded by default. */
    static FLBBodyShopUnderbodyProcessRecipe BuildPilotRecipe(
        ELBBodyShopUnderbodyArchitecture Architecture);

    /** Validates stable IDs, kit completeness, joining/quality gates and fixture-cell UX. */
    static bool ValidateRecipe(const FLBBodyShopUnderbodyProcessRecipe& Recipe,
        FString& OutReason);
};

