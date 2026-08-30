#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopUnderbodyProcess.h"

#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopUnderbodyStableCatalogV1Test,
    "LineBoss.BodyShop.Experimental.UnderbodyProcess.StableCatalogV1",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopUnderbodyStableCatalogV1Test::RunTest(const FString& Parameters)
{
    const TArray<FName> ExpectedComponents = {
        TEXT("UBC_FLOOR_PAN"),
        TEXT("UBC_CENTRE_TUNNEL"),
        TEXT("UBC_EV_BATTERY_TRAY"),
        TEXT("UBC_LONGITUDINAL_RAIL_LEFT"),
        TEXT("UBC_LONGITUDINAL_RAIL_RIGHT"),
        TEXT("UBC_CROSSMEMBERS"),
        TEXT("UBC_SIDE_SILL_LEFT"),
        TEXT("UBC_SIDE_SILL_RIGHT"),
        TEXT("UBC_FRONT_FLOOR_PARTITION"),
        TEXT("UBC_REAR_FLOOR_PARTITION")
    };
    const TArray<FName> ExpectedJoins = {
        TEXT("UBJ_RESISTANCE_SPOT_WELD"),
        TEXT("UBJ_LASER_WELD_OR_BRAZE"),
        TEXT("UBJ_MIG_MAG_WELD"),
        TEXT("UBJ_ADHESIVE_BOND"),
        TEXT("UBJ_SELF_PIERCING_RIVET")
    };
    const TArray<FName> ExpectedQuality = {
        TEXT("UBQ_DEBURR_AND_FINISH"),
        TEXT("UBQ_DIMENSIONAL_ALIGNMENT"),
        TEXT("UBQ_WELD_INTEGRITY")
    };
    const TArray<FName> ExpectedSteps = {
        TEXT("UB_STEP_PRESENT_COMPONENT_KIT"),
        TEXT("UB_STEP_LOCATE_IN_FIXTURE"),
        TEXT("UB_STEP_JOIN_PRIMARY_STRUCTURE"),
        TEXT("UB_STEP_TRANSFER_ON_SKID"),
        TEXT("UB_STEP_DEBURR_AND_FINISH_CHECK"),
        TEXT("UB_STEP_DIMENSIONAL_CHECK"),
        TEXT("UB_STEP_WELD_INTEGRITY_CHECK"),
        TEXT("UB_STEP_RELEASE_BIW_UNDERBODY")
    };

    TestEqual(TEXT("Ten stable underbody component IDs remain exact"),
        FLBBodyShopUnderbodyProcessRegistry::GetStableComponentIds(), ExpectedComponents);
    TestEqual(TEXT("Five stable joining-operation IDs remain exact"),
        FLBBodyShopUnderbodyProcessRegistry::GetStableJoinOperationIds(), ExpectedJoins);
    TestEqual(TEXT("Three stable quality-check IDs remain exact"),
        FLBBodyShopUnderbodyProcessRegistry::GetStableQualityCheckIds(), ExpectedQuality);
    TestEqual(TEXT("Eight stable process-step IDs remain exact and ordered"),
        FLBBodyShopUnderbodyProcessRegistry::GetStableProcessStepIds(), ExpectedSteps);

    const TArray<FLBBodyShopUnderbodyComponentDefinition> Definitions =
        FLBBodyShopUnderbodyProcessRegistry::GetComponentDefinitions();
    TestEqual(TEXT("Every stable component has one definition"), Definitions.Num(), 10);
    int32 RequiredCount = 0;
    int32 CentreChoiceCount = 0;
    int32 OptionalCount = 0;
    for (const FLBBodyShopUnderbodyComponentDefinition& Definition : Definitions)
    {
        if (Definition.Rule == ELBBodyShopUnderbodyComponentRule::Required)
        {
            ++RequiredCount;
        }
        else if (Definition.Rule ==
            ELBBodyShopUnderbodyComponentRule::ExactlyOneFromChoiceGroup)
        {
            ++CentreChoiceCount;
            TestEqual(TEXT("Centre alternatives share one stable choice group"),
                Definition.ChoiceGroupId,
                FName(TEXT("UB_ALT_CENTRE_STRUCTURE")));
        }
        else if (Definition.Rule == ELBBodyShopUnderbodyComponentRule::Optional)
        {
            ++OptionalCount;
        }
    }
    TestEqual(TEXT("Six components are mandatory in every underbody kit"), RequiredCount, 6);
    TestEqual(TEXT("Tunnel and EV tray form one exact choice"), CentreChoiceCount, 2);
    TestEqual(TEXT("Front and rear partitions remain optional"), OptionalCount, 2);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopUnderbodyKitSelectionV1Test,
    "LineBoss.BodyShop.Experimental.UnderbodyProcess.KitSelectionV1",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopUnderbodyKitSelectionV1Test::RunTest(const FString& Parameters)
{
    FString Reason;
    FLBBodyShopUnderbodyProcessRecipe TunnelRecipe =
        FLBBodyShopUnderbodyProcessRegistry::BuildPilotRecipe(
            ELBBodyShopUnderbodyArchitecture::CentreTunnel);
    TestTrue(TEXT("Canonical tunnel recipe validates"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(TunnelRecipe, Reason));
    TestEqual(TEXT("Tunnel recipe ID remains exact"), TunnelRecipe.RecipeId,
        FName(TEXT("UBR_UNDERBODY_TUNNEL_PILOT_V001")));
    TestEqual(TEXT("Tunnel recipe releases one stable WIP material"),
        TunnelRecipe.OutputMaterialId, FName(TEXT("BIW_UNDERBODY")));

    FLBBodyShopUnderbodyProcessRecipe EVRecipe =
        FLBBodyShopUnderbodyProcessRegistry::BuildPilotRecipe(
            ELBBodyShopUnderbodyArchitecture::EVBatteryTray);
    TestTrue(TEXT("Canonical EV tray recipe validates"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(EVRecipe, Reason));
    TestEqual(TEXT("EV recipe ID remains exact"), EVRecipe.RecipeId,
        FName(TEXT("UBR_UNDERBODY_EV_TRAY_PILOT_V001")));
    TestEqual(TEXT("EV recipe releases the same stable WIP material"),
        EVRecipe.OutputMaterialId, FName(TEXT("BIW_UNDERBODY")));

    FLBBodyShopUnderbodyProcessRecipe WithPartitions = TunnelRecipe;
    WithPartitions.SelectedComponentIds.Add(
        LBBodyShopUnderbodyComponentIds::FrontFloorPartition);
    WithPartitions.SelectedComponentIds.Add(
        LBBodyShopUnderbodyComponentIds::RearFloorPartition);
    TestTrue(TEXT("Optional front and rear partitions validate"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(WithPartitions, Reason));

    FLBBodyShopUnderbodyProcessRecipe MissingLeftRail = TunnelRecipe;
    MissingLeftRail.SelectedComponentIds.Remove(
        LBBodyShopUnderbodyComponentIds::LongitudinalRailLeft);
    TestFalse(TEXT("Missing a required rail is rejected"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(MissingLeftRail, Reason));

    FLBBodyShopUnderbodyProcessRecipe BothCentreStructures = TunnelRecipe;
    BothCentreStructures.SelectedComponentIds.Add(
        LBBodyShopUnderbodyComponentIds::EVBatteryTray);
    TestFalse(TEXT("Tunnel and EV tray together are rejected"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(BothCentreStructures, Reason));

    FLBBodyShopUnderbodyProcessRecipe DuplicateFloorPan = TunnelRecipe;
    DuplicateFloorPan.SelectedComponentIds.Add(LBBodyShopUnderbodyComponentIds::FloorPan);
    TestFalse(TEXT("Duplicate physical kit item is rejected"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(DuplicateFloorPan, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopUnderbodyFixtureProcessV1Test,
    "LineBoss.BodyShop.Experimental.UnderbodyProcess.FixtureProcessV1",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopUnderbodyFixtureProcessV1Test::RunTest(const FString& Parameters)
{
    FString Reason;
    const FLBBodyShopUnderbodyProcessRecipe Canonical =
        FLBBodyShopUnderbodyProcessRegistry::BuildPilotRecipe(
            ELBBodyShopUnderbodyArchitecture::CentreTunnel);
    TestTrue(TEXT("Canonical process validates"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(Canonical, Reason));
    TestTrue(TEXT("Player UX remains authored fixture-cell based"),
        Canonical.bUsesAuthoredFixtureCells);
    TestFalse(TEXT("Unrestricted robot CAD remains disabled"),
        Canonical.bAllowsUnrestrictedRobotPlacement);
    const TArray<FName> ExpectedRequiredJoins = {
        FName(TEXT("UBJ_RESISTANCE_SPOT_WELD"))
    };
    const TArray<FName> ExpectedVariantJoins = {
        FName(TEXT("UBJ_LASER_WELD_OR_BRAZE")),
        FName(TEXT("UBJ_MIG_MAG_WELD")),
        FName(TEXT("UBJ_ADHESIVE_BOND"))
    };
    const TArray<FName> ExpectedOptionalJoins = {
        FName(TEXT("UBJ_SELF_PIERCING_RIVET"))
    };
    const TArray<FName> ExpectedQualityChecks = {
        FName(TEXT("UBQ_DEBURR_AND_FINISH")),
        FName(TEXT("UBQ_DIMENSIONAL_ALIGNMENT")),
        FName(TEXT("UBQ_WELD_INTEGRITY"))
    };
    TestEqual(TEXT("Current pilot requires resistance spot welding only"),
        Canonical.RequiredJoinOperationIds, ExpectedRequiredJoins);
    TestEqual(TEXT("Laser, MIG/MAG and adhesive remain supported fixture variants"),
        Canonical.SupportedVariantJoinOperationIds, ExpectedVariantJoins);
    TestEqual(TEXT("Self-piercing riveting remains optional"),
        Canonical.OptionalJoinOperationIds, ExpectedOptionalJoins);
    TestEqual(TEXT("All three first-slice quality checks are required"),
        Canonical.RequiredQualityCheckIds, ExpectedQualityChecks);

    FLBBodyShopUnderbodyProcessRecipe FreeRobotCAD = Canonical;
    FreeRobotCAD.bAllowsUnrestrictedRobotPlacement = true;
    TestFalse(TEXT("Free robot CAD is rejected"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(FreeRobotCAD, Reason));

    FLBBodyShopUnderbodyProcessRecipe MissingSpotWeld = Canonical;
    MissingSpotWeld.RequiredJoinOperationIds.Reset();
    TestFalse(TEXT("Removing the two-C-gun pilot operation is rejected"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(MissingSpotWeld, Reason));

    FLBBodyShopUnderbodyProcessRecipe MissingWeldIntegrity = Canonical;
    MissingWeldIntegrity.RequiredQualityCheckIds.Remove(
        LBBodyShopUnderbodyQualityCheckIds::WeldIntegrity);
    TestFalse(TEXT("Removing weld-integrity inspection is rejected"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(
            MissingWeldIntegrity, Reason));

    FLBBodyShopUnderbodyProcessRecipe Reordered = Canonical;
    Reordered.OrderedProcessStepIds.Swap(1, 2);
    TestFalse(TEXT("Reordering fixture location after joining is rejected"),
        FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(Reordered, Reason));
    return true;
}

#endif
