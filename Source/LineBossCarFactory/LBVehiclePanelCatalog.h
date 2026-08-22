#pragma once

#include "CoreMinimal.h"

enum class ELBPanelHandedness : uint8
{
    None,
    Left,
    Right
};

/** Stable gameplay definition for one stamped closure/body-side panel family. */
struct FLBStampedPanelDefinition
{
    FName PanelTypeId = NAME_None;
    FString DisplayName;
    ELBPanelHandedness Handedness = ELBPanelHandedness::None;
    /** Number of like panels carried by one production WIP stillage. */
    int32 StillageCapacity = 1;
    /** Honest placeholder envelope until the registered geometry authority is available. */
    FVector NominalSizeCm = FVector::ZeroVector;
    /** Optional opposite-hand authority used to build a controlled mirrored derivative. */
    FName MirrorAuthorityPanelTypeId = NAME_None;
};

/**
 * Gameplay-facing vehicle recipe.  Geometry and presentation authorities are
 * deliberately referenced by revision IDs instead of asset paths, so an art
 * replacement cannot change contract, save or production identities.
 */
struct FLBVehicleModelRecipe
{
    FName ModelId = NAME_None;
    FString DisplayName;
    FName RecipeRevisionId = NAME_None;
    FName PaintRouteProfileId = NAME_None;
    FName GeometryAuthorityId = NAME_None;
    /** Independently validated stamped-panel authority for WIP/body presentation. */
    FName PanelGeometryAuthorityId = NAME_None;
    bool bDevelopmentVisual = true;
    bool bPanelGeometryValidated = false;
    /** Fallback sale price for an uncontracted dispatched unit, in pence. */
    int64 DefaultRevenuePence = 0;
    TArray<FLBStampedPanelDefinition> RequiredPanels;
    /** Exact BIW carrier/base-kit family consumed by the body-weld recipe. */
    FName BaseKitTypeId = NAME_None;
};

/**
 * The model registry is the sole gameplay catalogue for vehicle identity,
 * panel BOM and presentation revision.  Adding a programme means registering
 * a new recipe here (or, later, loading one through the same interface), not
 * introducing another CAIRNWELL-specific branch in production code.
 */
namespace LBVehicleModelCatalog
{
    LINEBOSSCARFACTORY_API const TArray<FLBVehicleModelRecipe>& GetRecipes();
    LINEBOSSCARFACTORY_API const FLBVehicleModelRecipe* Find(FName ModelId);
    /** True only when a recipe is safe to manufacture or use for a shop changeover. */
    LINEBOSSCARFACTORY_API bool IsProductionReady(const FLBVehicleModelRecipe& Recipe);
    LINEBOSSCARFACTORY_API FName GetDefaultModelId();
    LINEBOSSCARFACTORY_API bool IsKnownModel(FName ModelId);
    LINEBOSSCARFACTORY_API const TArray<FLBStampedPanelDefinition>& GetPanels(FName ModelId);
    /** Returns one model-scoped panel definition without exposing a vehicle-specific facade. */
    LINEBOSSCARFACTORY_API const FLBStampedPanelDefinition* FindPanelDefinition(
        FName ModelId, FName PanelTypeId);
    /** Validates a panel family against the selected model's registered BOM. */
    LINEBOSSCARFACTORY_API bool IsApprovedStampedPanelRecipe(
        FName ModelId, FName PanelTypeId);
    /**
     * Parses the transport-neutral press identity
     * `PT?-PANEL-<model>-<panel>-<serial>` and validates it against the
     * model registry. It is intentionally not tied to Cairnwell.
     */
    LINEBOSSCARFACTORY_API bool ParsePressedPanelUnitId(FName UnitId,
        FName& OutVehicleModelId, FName& OutPanelTypeId);
    /**
     * Returns the complete body-weld BOM for a registered model.  Production
     * code uses this instead of maintaining a model-specific panel list.
     */
    LINEBOSSCARFACTORY_API bool GetBodyWeldContract(FName ModelId,
        TArray<FName>& OutPanelFamilies, FName& OutBaseKitTypeId);
    /** Adds a non-shipping programme recipe without altering existing save identities. */
    LINEBOSSCARFACTORY_API bool RegisterDevelopmentRecipe(const FLBVehicleModelRecipe& Recipe, FString& OutReason);
    /** Removes a dynamically registered development recipe; built-in programmes cannot be removed. */
    LINEBOSSCARFACTORY_API bool UnregisterDevelopmentRecipe(FName ModelId);
}

namespace LBCairnwell2040PanelCatalog
{
    LINEBOSSCARFACTORY_API FName GetVehicleModelId();
    LINEBOSSCARFACTORY_API const TArray<FLBStampedPanelDefinition>& GetDefinitions();
    LINEBOSSCARFACTORY_API const FLBStampedPanelDefinition* Find(FName VehicleModelId, FName PanelTypeId);
    LINEBOSSCARFACTORY_API bool IsApprovedStampedRecipe(FName VehicleModelId, FName PanelTypeId);

    /** Parses the press authority ID: PT?-PANEL-<vehicle>-<panel>-<serial>. */
    LINEBOSSCARFACTORY_API bool ParsePressedPanelUnitId(FName UnitId,
        FName& OutVehicleModelId, FName& OutPanelTypeId);
}
