#include "LBBodyShopUnderbodyProcess.h"

const FName LBBodyShopUnderbodyRecipeIds::TunnelPilotV1(
    TEXT("UBR_UNDERBODY_TUNNEL_PILOT_V001"));
const FName LBBodyShopUnderbodyRecipeIds::EVPilotV1(
    TEXT("UBR_UNDERBODY_EV_TRAY_PILOT_V001"));

const FName LBBodyShopUnderbodyChoiceGroupIds::CentreStructure(
    TEXT("UB_ALT_CENTRE_STRUCTURE"));

const FName LBBodyShopUnderbodyComponentIds::FloorPan(TEXT("UBC_FLOOR_PAN"));
const FName LBBodyShopUnderbodyComponentIds::CentreTunnel(TEXT("UBC_CENTRE_TUNNEL"));
const FName LBBodyShopUnderbodyComponentIds::EVBatteryTray(TEXT("UBC_EV_BATTERY_TRAY"));
const FName LBBodyShopUnderbodyComponentIds::LongitudinalRailLeft(
    TEXT("UBC_LONGITUDINAL_RAIL_LEFT"));
const FName LBBodyShopUnderbodyComponentIds::LongitudinalRailRight(
    TEXT("UBC_LONGITUDINAL_RAIL_RIGHT"));
const FName LBBodyShopUnderbodyComponentIds::Crossmembers(TEXT("UBC_CROSSMEMBERS"));
const FName LBBodyShopUnderbodyComponentIds::SideSillLeft(TEXT("UBC_SIDE_SILL_LEFT"));
const FName LBBodyShopUnderbodyComponentIds::SideSillRight(TEXT("UBC_SIDE_SILL_RIGHT"));
const FName LBBodyShopUnderbodyComponentIds::FrontFloorPartition(
    TEXT("UBC_FRONT_FLOOR_PARTITION"));
const FName LBBodyShopUnderbodyComponentIds::RearFloorPartition(
    TEXT("UBC_REAR_FLOOR_PARTITION"));

const FName LBBodyShopUnderbodyJoinOperationIds::ResistanceSpotWeld(
    TEXT("UBJ_RESISTANCE_SPOT_WELD"));
const FName LBBodyShopUnderbodyJoinOperationIds::LaserWeldOrBraze(
    TEXT("UBJ_LASER_WELD_OR_BRAZE"));
const FName LBBodyShopUnderbodyJoinOperationIds::MigMagWeld(
    TEXT("UBJ_MIG_MAG_WELD"));
const FName LBBodyShopUnderbodyJoinOperationIds::AdhesiveBond(
    TEXT("UBJ_ADHESIVE_BOND"));
const FName LBBodyShopUnderbodyJoinOperationIds::SelfPiercingRivet(
    TEXT("UBJ_SELF_PIERCING_RIVET"));

const FName LBBodyShopUnderbodyQualityCheckIds::DeburrAndFinish(
    TEXT("UBQ_DEBURR_AND_FINISH"));
const FName LBBodyShopUnderbodyQualityCheckIds::DimensionalAlignment(
    TEXT("UBQ_DIMENSIONAL_ALIGNMENT"));
const FName LBBodyShopUnderbodyQualityCheckIds::WeldIntegrity(
    TEXT("UBQ_WELD_INTEGRITY"));

const FName LBBodyShopUnderbodyProcessStepIds::PresentComponentKit(
    TEXT("UB_STEP_PRESENT_COMPONENT_KIT"));
const FName LBBodyShopUnderbodyProcessStepIds::LocateInFixture(
    TEXT("UB_STEP_LOCATE_IN_FIXTURE"));
const FName LBBodyShopUnderbodyProcessStepIds::JoinPrimaryStructure(
    TEXT("UB_STEP_JOIN_PRIMARY_STRUCTURE"));
const FName LBBodyShopUnderbodyProcessStepIds::TransferOnSkid(
    TEXT("UB_STEP_TRANSFER_ON_SKID"));
const FName LBBodyShopUnderbodyProcessStepIds::DeburrAndFinishCheck(
    TEXT("UB_STEP_DEBURR_AND_FINISH_CHECK"));
const FName LBBodyShopUnderbodyProcessStepIds::DimensionalCheck(
    TEXT("UB_STEP_DIMENSIONAL_CHECK"));
const FName LBBodyShopUnderbodyProcessStepIds::WeldIntegrityCheck(
    TEXT("UB_STEP_WELD_INTEGRITY_CHECK"));
const FName LBBodyShopUnderbodyProcessStepIds::ReleaseUnderbody(
    TEXT("UB_STEP_RELEASE_BIW_UNDERBODY"));

namespace LBBodyShopUnderbodyProcessPrivate
{
    FLBBodyShopUnderbodyComponentDefinition Component(
        const FName Id, const ELBBodyShopUnderbodyComponentRule Rule,
        const FName ChoiceGroupId = NAME_None)
    {
        FLBBodyShopUnderbodyComponentDefinition Result;
        Result.ComponentId = Id;
        Result.Rule = Rule;
        Result.ChoiceGroupId = ChoiceGroupId;
        return Result;
    }

    bool HasDuplicates(const TArray<FName>& Ids)
    {
        TSet<FName> UniqueIds;
        for (const FName Id : Ids)
        {
            if (Id.IsNone() || UniqueIds.Contains(Id))
            {
                return true;
            }
            UniqueIds.Add(Id);
        }
        return false;
    }

    bool HasExactOrder(const TArray<FName>& Actual, const TArray<FName>& Expected)
    {
        return Actual == Expected;
    }

    bool ContainsOnlyKnownIds(const TArray<FName>& Actual, const TArray<FName>& Known)
    {
        for (const FName Id : Actual)
        {
            if (!Known.Contains(Id))
            {
                return false;
            }
        }
        return true;
    }
}

TArray<FName> FLBBodyShopUnderbodyProcessRegistry::GetStableComponentIds()
{
    return {
        LBBodyShopUnderbodyComponentIds::FloorPan,
        LBBodyShopUnderbodyComponentIds::CentreTunnel,
        LBBodyShopUnderbodyComponentIds::EVBatteryTray,
        LBBodyShopUnderbodyComponentIds::LongitudinalRailLeft,
        LBBodyShopUnderbodyComponentIds::LongitudinalRailRight,
        LBBodyShopUnderbodyComponentIds::Crossmembers,
        LBBodyShopUnderbodyComponentIds::SideSillLeft,
        LBBodyShopUnderbodyComponentIds::SideSillRight,
        LBBodyShopUnderbodyComponentIds::FrontFloorPartition,
        LBBodyShopUnderbodyComponentIds::RearFloorPartition
    };
}

TArray<FName> FLBBodyShopUnderbodyProcessRegistry::GetStableJoinOperationIds()
{
    return {
        LBBodyShopUnderbodyJoinOperationIds::ResistanceSpotWeld,
        LBBodyShopUnderbodyJoinOperationIds::LaserWeldOrBraze,
        LBBodyShopUnderbodyJoinOperationIds::MigMagWeld,
        LBBodyShopUnderbodyJoinOperationIds::AdhesiveBond,
        LBBodyShopUnderbodyJoinOperationIds::SelfPiercingRivet
    };
}

TArray<FName> FLBBodyShopUnderbodyProcessRegistry::GetStableQualityCheckIds()
{
    return {
        LBBodyShopUnderbodyQualityCheckIds::DeburrAndFinish,
        LBBodyShopUnderbodyQualityCheckIds::DimensionalAlignment,
        LBBodyShopUnderbodyQualityCheckIds::WeldIntegrity
    };
}

TArray<FName> FLBBodyShopUnderbodyProcessRegistry::GetStableProcessStepIds()
{
    return {
        LBBodyShopUnderbodyProcessStepIds::PresentComponentKit,
        LBBodyShopUnderbodyProcessStepIds::LocateInFixture,
        LBBodyShopUnderbodyProcessStepIds::JoinPrimaryStructure,
        LBBodyShopUnderbodyProcessStepIds::TransferOnSkid,
        LBBodyShopUnderbodyProcessStepIds::DeburrAndFinishCheck,
        LBBodyShopUnderbodyProcessStepIds::DimensionalCheck,
        LBBodyShopUnderbodyProcessStepIds::WeldIntegrityCheck,
        LBBodyShopUnderbodyProcessStepIds::ReleaseUnderbody
    };
}

TArray<FLBBodyShopUnderbodyComponentDefinition>
FLBBodyShopUnderbodyProcessRegistry::GetComponentDefinitions()
{
    using namespace LBBodyShopUnderbodyProcessPrivate;
    return {
        Component(LBBodyShopUnderbodyComponentIds::FloorPan,
            ELBBodyShopUnderbodyComponentRule::Required),
        Component(LBBodyShopUnderbodyComponentIds::CentreTunnel,
            ELBBodyShopUnderbodyComponentRule::ExactlyOneFromChoiceGroup,
            LBBodyShopUnderbodyChoiceGroupIds::CentreStructure),
        Component(LBBodyShopUnderbodyComponentIds::EVBatteryTray,
            ELBBodyShopUnderbodyComponentRule::ExactlyOneFromChoiceGroup,
            LBBodyShopUnderbodyChoiceGroupIds::CentreStructure),
        Component(LBBodyShopUnderbodyComponentIds::LongitudinalRailLeft,
            ELBBodyShopUnderbodyComponentRule::Required),
        Component(LBBodyShopUnderbodyComponentIds::LongitudinalRailRight,
            ELBBodyShopUnderbodyComponentRule::Required),
        Component(LBBodyShopUnderbodyComponentIds::Crossmembers,
            ELBBodyShopUnderbodyComponentRule::Required),
        Component(LBBodyShopUnderbodyComponentIds::SideSillLeft,
            ELBBodyShopUnderbodyComponentRule::Required),
        Component(LBBodyShopUnderbodyComponentIds::SideSillRight,
            ELBBodyShopUnderbodyComponentRule::Required),
        Component(LBBodyShopUnderbodyComponentIds::FrontFloorPartition,
            ELBBodyShopUnderbodyComponentRule::Optional),
        Component(LBBodyShopUnderbodyComponentIds::RearFloorPartition,
            ELBBodyShopUnderbodyComponentRule::Optional)
    };
}

FLBBodyShopUnderbodyProcessRecipe
FLBBodyShopUnderbodyProcessRegistry::BuildPilotRecipe(
    const ELBBodyShopUnderbodyArchitecture Architecture)
{
    FLBBodyShopUnderbodyProcessRecipe Recipe;
    Recipe.RecipeId = Architecture == ELBBodyShopUnderbodyArchitecture::EVBatteryTray
        ? LBBodyShopUnderbodyRecipeIds::EVPilotV1
        : LBBodyShopUnderbodyRecipeIds::TunnelPilotV1;
    Recipe.OutputMaterialId = LBBodyShopMaterialIds::Underbody;
    Recipe.Architecture = Architecture;
    Recipe.SelectedComponentIds = {
        LBBodyShopUnderbodyComponentIds::FloorPan,
        Architecture == ELBBodyShopUnderbodyArchitecture::EVBatteryTray
            ? LBBodyShopUnderbodyComponentIds::EVBatteryTray
            : LBBodyShopUnderbodyComponentIds::CentreTunnel,
        LBBodyShopUnderbodyComponentIds::LongitudinalRailLeft,
        LBBodyShopUnderbodyComponentIds::LongitudinalRailRight,
        LBBodyShopUnderbodyComponentIds::Crossmembers,
        LBBodyShopUnderbodyComponentIds::SideSillLeft,
        LBBodyShopUnderbodyComponentIds::SideSillRight
    };
    Recipe.RequiredJoinOperationIds = {
        LBBodyShopUnderbodyJoinOperationIds::ResistanceSpotWeld
    };
    Recipe.SupportedVariantJoinOperationIds = {
        LBBodyShopUnderbodyJoinOperationIds::LaserWeldOrBraze,
        LBBodyShopUnderbodyJoinOperationIds::MigMagWeld,
        LBBodyShopUnderbodyJoinOperationIds::AdhesiveBond
    };
    Recipe.OptionalJoinOperationIds = {
        LBBodyShopUnderbodyJoinOperationIds::SelfPiercingRivet
    };
    Recipe.RequiredQualityCheckIds = GetStableQualityCheckIds();
    Recipe.OrderedProcessStepIds = GetStableProcessStepIds();
    return Recipe;
}

bool FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(
    const FLBBodyShopUnderbodyProcessRecipe& Recipe, FString& OutReason)
{
    using namespace LBBodyShopUnderbodyProcessPrivate;
    OutReason.Reset();

    if (Recipe.ContractVersion != 1)
    {
        OutReason = TEXT("Underbody process contract must remain version 1.");
        return false;
    }
    if (Recipe.Architecture != ELBBodyShopUnderbodyArchitecture::CentreTunnel &&
        Recipe.Architecture != ELBBodyShopUnderbodyArchitecture::EVBatteryTray)
    {
        OutReason = TEXT("Underbody architecture is not recognised by contract v1.");
        return false;
    }

    const FName ExpectedRecipeId =
        Recipe.Architecture == ELBBodyShopUnderbodyArchitecture::EVBatteryTray
        ? LBBodyShopUnderbodyRecipeIds::EVPilotV1
        : LBBodyShopUnderbodyRecipeIds::TunnelPilotV1;
    if (Recipe.RecipeId != ExpectedRecipeId)
    {
        OutReason = TEXT("Recipe ID does not match the selected underbody architecture.");
        return false;
    }
    if (Recipe.OutputMaterialId != LBBodyShopMaterialIds::Underbody)
    {
        OutReason = TEXT("The first slice must release exactly one BIW_UNDERBODY material ID.");
        return false;
    }
    if (!Recipe.bUsesAuthoredFixtureCells || Recipe.bAllowsUnrestrictedRobotPlacement)
    {
        OutReason = TEXT("Underbody production must use authored fixture cells and robot slots.");
        return false;
    }

    const TArray<FName> KnownComponents = GetStableComponentIds();
    if (HasDuplicates(Recipe.SelectedComponentIds) ||
        !ContainsOnlyKnownIds(Recipe.SelectedComponentIds, KnownComponents))
    {
        OutReason = TEXT("Selected underbody components contain an empty, duplicate or unknown ID.");
        return false;
    }

    for (const FLBBodyShopUnderbodyComponentDefinition& Definition : GetComponentDefinitions())
    {
        if (Definition.Rule == ELBBodyShopUnderbodyComponentRule::Required &&
            !Recipe.SelectedComponentIds.Contains(Definition.ComponentId))
        {
            OutReason = FString::Printf(TEXT("Required underbody component %s is missing."),
                *Definition.ComponentId.ToString());
            return false;
        }
    }

    const bool bHasTunnel =
        Recipe.SelectedComponentIds.Contains(LBBodyShopUnderbodyComponentIds::CentreTunnel);
    const bool bHasBatteryTray =
        Recipe.SelectedComponentIds.Contains(LBBodyShopUnderbodyComponentIds::EVBatteryTray);
    if (bHasTunnel == bHasBatteryTray)
    {
        OutReason = TEXT("Select exactly one centre structure: tunnel or EV battery tray.");
        return false;
    }
    if ((Recipe.Architecture == ELBBodyShopUnderbodyArchitecture::CentreTunnel) != bHasTunnel)
    {
        OutReason = TEXT("Selected centre structure does not match the recipe architecture.");
        return false;
    }

    if (HasDuplicates(Recipe.RequiredJoinOperationIds) ||
        HasDuplicates(Recipe.SupportedVariantJoinOperationIds) ||
        HasDuplicates(Recipe.OptionalJoinOperationIds))
    {
        OutReason = TEXT("Joining operation lists contain an empty or duplicate ID.");
        return false;
    }
    TArray<FName> AllSelectedJoinOperations = Recipe.RequiredJoinOperationIds;
    AllSelectedJoinOperations.Append(Recipe.SupportedVariantJoinOperationIds);
    AllSelectedJoinOperations.Append(Recipe.OptionalJoinOperationIds);
    if (HasDuplicates(AllSelectedJoinOperations) ||
        !ContainsOnlyKnownIds(AllSelectedJoinOperations, GetStableJoinOperationIds()))
    {
        OutReason = TEXT("Joining operation classifications overlap or contain an unknown ID.");
        return false;
    }
    const TArray<FName> ExpectedRequiredJoins = {
        LBBodyShopUnderbodyJoinOperationIds::ResistanceSpotWeld
    };
    const TArray<FName> ExpectedSupportedVariantJoins = {
        LBBodyShopUnderbodyJoinOperationIds::LaserWeldOrBraze,
        LBBodyShopUnderbodyJoinOperationIds::MigMagWeld,
        LBBodyShopUnderbodyJoinOperationIds::AdhesiveBond
    };
    const TArray<FName> ExpectedOptionalJoins = {
        LBBodyShopUnderbodyJoinOperationIds::SelfPiercingRivet
    };
    if (!HasExactOrder(Recipe.RequiredJoinOperationIds, ExpectedRequiredJoins) ||
        !HasExactOrder(Recipe.SupportedVariantJoinOperationIds,
            ExpectedSupportedVariantJoins) ||
        !HasExactOrder(Recipe.OptionalJoinOperationIds, ExpectedOptionalJoins))
    {
        OutReason = TEXT("Joining operation classifications do not match pilot contract v1.");
        return false;
    }

    if (HasDuplicates(Recipe.RequiredQualityCheckIds) ||
        !HasExactOrder(Recipe.RequiredQualityCheckIds, GetStableQualityCheckIds()))
    {
        OutReason = TEXT("Deburr, dimensional and weld-integrity checks are all required.");
        return false;
    }
    if (HasDuplicates(Recipe.OrderedProcessStepIds) ||
        !HasExactOrder(Recipe.OrderedProcessStepIds, GetStableProcessStepIds()))
    {
        OutReason = TEXT("Underbody process steps do not match the stable first-slice order.");
        return false;
    }

    return true;
}
