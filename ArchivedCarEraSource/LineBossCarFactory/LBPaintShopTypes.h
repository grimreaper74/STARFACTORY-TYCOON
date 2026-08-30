#pragma once

#include "CoreMinimal.h"
#include "LBPaintShopTypes.generated.h"

/** Stable semantic cell types for the isolated first Paint Shop process chain. */
UENUM(BlueprintType)
enum class ELBPaintShopCellType : uint8
{
    BIWLoadDock,
    PhosphateDip,
    EDCoatDip,
    DrainInspection,
    EDCureOven,
    EDOutputBuffer
};

UENUM(BlueprintType)
enum class ELBPaintShopPortDirection : uint8
{
    Input,
    Output
};

/** Stable identifiers owned only by the isolated experimental Paint Shop foundation. */
namespace LBPaintShopCellIds
{
    LINEBOSSCARFACTORY_API extern const FName BIWLoadDock;
    LINEBOSSCARFACTORY_API extern const FName PhosphateDipCell;
    LINEBOSSCARFACTORY_API extern const FName EDCoatDipCell;
    LINEBOSSCARFACTORY_API extern const FName DrainInspectionCell;
    LINEBOSSCARFACTORY_API extern const FName EDCureOvenCell;
    LINEBOSSCARFACTORY_API extern const FName EDOutputBuffer;
}

namespace LBPaintShopWIPIds
{
    LINEBOSSCARFACTORY_API extern const FName BIWComplete;
    LINEBOSSCARFACTORY_API extern const FName BIWEDCoated;
    LINEBOSSCARFACTORY_API extern const FName BIWCuredEDCoat;
}

namespace LBPaintShopRecipeIds
{
    LINEBOSSCARFACTORY_API extern const FName PhosphateV001;
    LINEBOSSCARFACTORY_API extern const FName EDCoatV001;
    LINEBOSSCARFACTORY_API extern const FName EDCureV001;
}

namespace LBPaintShopQualityIds
{
    LINEBOSSCARFACTORY_API extern const FName PhosphateCoverage;
    LINEBOSSCARFACTORY_API extern const FName EDFilmBuild;
    LINEBOSSCARFACTORY_API extern const FName EDCure;
}

namespace LBPaintShopPortIds
{
    LINEBOSSCARFACTORY_API extern const FName CarrierIn;
    LINEBOSSCARFACTORY_API extern const FName CarrierOut;
}

/** Semantic carrier hand-off. Geometry and physical carrier limits remain deliberately TBC. */
USTRUCT(BlueprintType)
struct FLBPaintShopPortDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName PortId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    ELBPaintShopPortDirection Direction = ELBPaintShopPortDirection::Input;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName WIPId = NAME_None;
};

/**
 * Version-one semantic process definition only. It intentionally carries no
 * map placement, art, physical dimensions, runtime state, or campaign data.
 */
USTRUCT(BlueprintType)
struct FLBPaintShopCellDefinition
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName DefinitionId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    ELBPaintShopCellType CellType = ELBPaintShopCellType::BIWLoadDock;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FText DisplayName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName InputWIPId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName OutputWIPId = NAME_None;

    /** NAME_None is valid for transfer, inspection, and buffer cells. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName RecipeId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    TArray<FName> QualityCheckIds;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    TArray<FLBPaintShopPortDefinition> Ports;
};

/** Canonical isolated Paint Shop v1 definitions and mutation-free validation. */
class LINEBOSSCARFACTORY_API FLBPaintShopDefinitionRegistry
{
public:
    static TArray<FName> GetCanonicalDefinitionIds();
    static TArray<FLBPaintShopCellDefinition> GetCanonicalDefinitions();
    static bool FindCanonicalDefinition(FName DefinitionId,
        FLBPaintShopCellDefinition& OutDefinition);
    static bool ValidateDefinition(const FLBPaintShopCellDefinition& Definition,
        FString& OutReason);
    static bool ValidateCanonicalDefinitionSet(
        const TArray<FLBPaintShopCellDefinition>& Definitions, FString& OutReason);
};
