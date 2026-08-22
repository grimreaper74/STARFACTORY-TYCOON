#include "LBVehiclePanelCatalog.h"

namespace
{
    const FName Cairnwell2040Id(TEXT("CAIRNWELL_2040"));

    const TArray<FLBStampedPanelDefinition> Cairnwell2040Panels =
    {
        { TEXT("HOOD_PANEL"), TEXT("Hood outer"), ELBPanelHandedness::None,
            16, FVector(165.0f, 145.0f, 24.0f), NAME_None },
        { TEXT("ROOF_PANEL"), TEXT("Roof outer"), ELBPanelHandedness::None,
            12, FVector(205.0f, 150.0f, 20.0f), NAME_None },
        { TEXT("DOOR_FRONT_LEFT"), TEXT("Front door left"), ELBPanelHandedness::Left,
            20, FVector(125.0f, 18.0f, 115.0f), NAME_None },
        { TEXT("DOOR_FRONT_RIGHT"), TEXT("Front door right"), ELBPanelHandedness::Right,
            20, FVector(125.0f, 18.0f, 115.0f), TEXT("DOOR_FRONT_LEFT") },
        { TEXT("DOOR_REAR_LEFT"), TEXT("Rear door left"), ELBPanelHandedness::Left,
            20, FVector(110.0f, 18.0f, 112.0f), NAME_None },
        { TEXT("DOOR_REAR_RIGHT"), TEXT("Rear door right"), ELBPanelHandedness::Right,
            20, FVector(110.0f, 18.0f, 112.0f), NAME_None },
        { TEXT("FENDER_FRONT_LEFT"), TEXT("Front fender left"), ELBPanelHandedness::Left,
            24, FVector(118.0f, 42.0f, 92.0f), NAME_None },
        { TEXT("FENDER_FRONT_RIGHT"), TEXT("Front fender right"), ELBPanelHandedness::Right,
            24, FVector(118.0f, 42.0f, 92.0f), TEXT("FENDER_FRONT_LEFT") },
        { TEXT("QUARTER_PANEL_LEFT"), TEXT("Quarter panel left"), ELBPanelHandedness::Left,
            12, FVector(175.0f, 42.0f, 118.0f), NAME_None },
        { TEXT("QUARTER_PANEL_RIGHT"), TEXT("Quarter panel right"), ELBPanelHandedness::Right,
            12, FVector(175.0f, 42.0f, 118.0f), NAME_None },
        { TEXT("TAILGATE_PANEL"), TEXT("Tailgate outer"), ELBPanelHandedness::None,
            14, FVector(145.0f, 22.0f, 108.0f), NAME_None }
    };

    const TArray<FLBVehicleModelRecipe> BuiltInVehicleRecipes =
    {
        {
            Cairnwell2040Id,
            TEXT("Cairnwell 2040 / BEV development programme"),
            TEXT("CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001"),
            TEXT("PAINT_ROUTE_EDCOAT_VISIBLE_V001"),
            // The active development build deliberately renders the authored
            // native WIP layers. The retired imported runtime authority is
            // excluded from the cook and must not survive as recipe metadata.
            TEXT("Cairnwell2040NativeWIPVehicleRepresentation_v001"),
            TEXT("Cairnwell2040PanelModules_v001_CoordinateRecovery_v003"),
            true,
            true,
            3200000,
            Cairnwell2040Panels,
            TEXT("CAIRNWELL_2040_BIW_BASE_KIT")
        }
    };

    const TArray<FLBStampedPanelDefinition> EmptyPanels;

    TArray<FLBVehicleModelRecipe>& MutableVehicleRecipes()
    {
        static TArray<FLBVehicleModelRecipe> Recipes = BuiltInVehicleRecipes;
        return Recipes;
    }

    bool IsRecipeWellFormed(const FLBVehicleModelRecipe& Recipe, FString& OutReason)
    {
        if (Recipe.ModelId.IsNone() || Recipe.DisplayName.IsEmpty() || Recipe.RecipeRevisionId.IsNone())
        {
            OutReason = TEXT("Vehicle recipes require a stable model ID, display name and recipe revision.");
            return false;
        }
        if (Recipe.PaintRouteProfileId.IsNone() || Recipe.GeometryAuthorityId.IsNone())
        {
            OutReason = TEXT("Vehicle recipes require paint-route and geometry authority IDs.");
            return false;
        }
        if (Recipe.DefaultRevenuePence <= 0 || Recipe.RequiredPanels.IsEmpty() || Recipe.BaseKitTypeId.IsNone())
        {
            OutReason = TEXT("Vehicle recipes require a positive revenue, base-kit family and at least one stamped panel.");
            return false;
        }

        TSet<FName> SeenPanels;
        for (const FLBStampedPanelDefinition& Panel : Recipe.RequiredPanels)
        {
            if (Panel.PanelTypeId.IsNone() || Panel.DisplayName.IsEmpty() || Panel.StillageCapacity <= 0
                || SeenPanels.Contains(Panel.PanelTypeId))
            {
                OutReason = TEXT("Vehicle recipe panel IDs must be named, unique and have positive stillage capacity.");
                return false;
            }
            SeenPanels.Add(Panel.PanelTypeId);
        }
        return true;
    }
}

const TArray<FLBVehicleModelRecipe>& LBVehicleModelCatalog::GetRecipes()
{
    return MutableVehicleRecipes();
}

const FLBVehicleModelRecipe* LBVehicleModelCatalog::Find(const FName ModelId)
{
    if (ModelId.IsNone()) return nullptr;
    return MutableVehicleRecipes().FindByPredicate([ModelId](const FLBVehicleModelRecipe& Recipe)
    {
        return Recipe.ModelId == ModelId;
    });
}

bool LBVehicleModelCatalog::IsProductionReady(const FLBVehicleModelRecipe& Recipe)
{
    return !Recipe.RecipeRevisionId.IsNone()
        && !Recipe.PanelGeometryAuthorityId.IsNone()
        && Recipe.bPanelGeometryValidated
        && !Recipe.RequiredPanels.IsEmpty();
}

FName LBVehicleModelCatalog::GetDefaultModelId()
{
    return Cairnwell2040Id;
}

bool LBVehicleModelCatalog::IsKnownModel(const FName ModelId)
{
    return Find(ModelId) != nullptr;
}

const TArray<FLBStampedPanelDefinition>& LBVehicleModelCatalog::GetPanels(const FName ModelId)
{
    if (const FLBVehicleModelRecipe* Recipe = Find(ModelId))
    {
        return Recipe->RequiredPanels;
    }
    return EmptyPanels;
}

const FLBStampedPanelDefinition* LBVehicleModelCatalog::FindPanelDefinition(
    const FName ModelId, const FName PanelTypeId)
{
    if (PanelTypeId.IsNone()) return nullptr;
    return GetPanels(ModelId).FindByPredicate([PanelTypeId](
        const FLBStampedPanelDefinition& Definition)
    {
        return Definition.PanelTypeId == PanelTypeId;
    });
}

bool LBVehicleModelCatalog::IsApprovedStampedPanelRecipe(
    const FName ModelId, const FName PanelTypeId)
{
    if (PanelTypeId.IsNone()) return false;
    return GetPanels(ModelId).ContainsByPredicate([PanelTypeId](
        const FLBStampedPanelDefinition& Definition)
    {
        return Definition.PanelTypeId == PanelTypeId;
    });
}

bool LBVehicleModelCatalog::ParsePressedPanelUnitId(const FName UnitId,
    FName& OutVehicleModelId, FName& OutPanelTypeId)
{
    OutVehicleModelId = NAME_None;
    OutPanelTypeId = NAME_None;
    if (UnitId.IsNone()) return false;

    FString Payload;
    if (!UnitId.ToString().Split(TEXT("-PANEL-"), nullptr, &Payload)
        || Payload.IsEmpty()) return false;

    FString WithoutSerial;
    FString Serial;
    if (!Payload.Split(TEXT("-"), &WithoutSerial, &Serial, ESearchCase::CaseSensitive,
        ESearchDir::FromEnd) || WithoutSerial.IsEmpty() || !Serial.IsNumeric()) return false;

    FString Vehicle;
    FString Panel;
    if (!WithoutSerial.Split(TEXT("-"), &Vehicle, &Panel) || Vehicle.IsEmpty() || Panel.IsEmpty())
        return false;

    OutVehicleModelId = FName(*Vehicle);
    OutPanelTypeId = FName(*Panel);
    return IsApprovedStampedPanelRecipe(OutVehicleModelId, OutPanelTypeId);
}

bool LBVehicleModelCatalog::GetBodyWeldContract(const FName ModelId,
    TArray<FName>& OutPanelFamilies, FName& OutBaseKitTypeId)
{
    OutPanelFamilies.Reset();
    OutBaseKitTypeId = NAME_None;
    const FLBVehicleModelRecipe* Recipe = Find(ModelId);
    if (!Recipe || Recipe->BaseKitTypeId.IsNone()) return false;

    TSet<FName> SeenFamilies;
    for (const FLBStampedPanelDefinition& Panel : Recipe->RequiredPanels)
    {
        if (Panel.PanelTypeId.IsNone() || SeenFamilies.Contains(Panel.PanelTypeId))
        {
            OutPanelFamilies.Reset();
            return false;
        }
        SeenFamilies.Add(Panel.PanelTypeId);
        OutPanelFamilies.Add(Panel.PanelTypeId);
    }
    if (OutPanelFamilies.IsEmpty()) return false;
    OutBaseKitTypeId = Recipe->BaseKitTypeId;
    return true;
}

bool LBVehicleModelCatalog::RegisterDevelopmentRecipe(const FLBVehicleModelRecipe& Recipe, FString& OutReason)
{
    OutReason.Reset();
    if (!Recipe.bDevelopmentVisual)
    {
        OutReason = TEXT("Only explicitly development visual programmes may be registered at runtime.");
        return false;
    }
    if (!IsRecipeWellFormed(Recipe, OutReason)) return false;
    TArray<FLBVehicleModelRecipe>& Recipes = MutableVehicleRecipes();
    if (Recipes.ContainsByPredicate([&Recipe](const FLBVehicleModelRecipe& Existing)
        { return Existing.ModelId == Recipe.ModelId; }))
    {
        OutReason = TEXT("Vehicle model ID is already registered.");
        return false;
    }
    Recipes.Add(Recipe);
    return true;
}

bool LBVehicleModelCatalog::UnregisterDevelopmentRecipe(const FName ModelId)
{
    if (ModelId.IsNone() || ModelId == Cairnwell2040Id) return false;
    TArray<FLBVehicleModelRecipe>& Recipes = MutableVehicleRecipes();
    const int32 Removed = Recipes.RemoveAll([ModelId](const FLBVehicleModelRecipe& Recipe)
        { return Recipe.ModelId == ModelId && Recipe.bDevelopmentVisual; });
    return Removed == 1;
}

FName LBCairnwell2040PanelCatalog::GetVehicleModelId()
{
    return Cairnwell2040Id;
}

const TArray<FLBStampedPanelDefinition>& LBCairnwell2040PanelCatalog::GetDefinitions()
{
    return LBVehicleModelCatalog::GetPanels(Cairnwell2040Id);
}

const FLBStampedPanelDefinition* LBCairnwell2040PanelCatalog::Find(
    const FName VehicleModelId, const FName PanelTypeId)
{
    return LBVehicleModelCatalog::FindPanelDefinition(VehicleModelId,
        PanelTypeId);
}

bool LBCairnwell2040PanelCatalog::IsApprovedStampedRecipe(
    const FName VehicleModelId, const FName PanelTypeId)
{
    return LBVehicleModelCatalog::IsApprovedStampedPanelRecipe(
        VehicleModelId, PanelTypeId);
}

bool LBCairnwell2040PanelCatalog::ParsePressedPanelUnitId(const FName UnitId,
    FName& OutVehicleModelId, FName& OutPanelTypeId)
{
    return LBVehicleModelCatalog::ParsePressedPanelUnitId(
        UnitId, OutVehicleModelId, OutPanelTypeId);
}
