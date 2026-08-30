#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopTypes.h"

#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopStableIdsAndCanonicalDefinitionsTest,
    "LineBoss.BodyShop.Experimental.StableIdsAndCanonicalDefinitions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopStableIdsAndCanonicalDefinitionsTest::RunTest(const FString& Parameters)
{
    const TArray<FName> MaterialIds = {
        LBBodyShopMaterialIds::Underbody,
        LBBodyShopMaterialIds::SideLeft,
        LBBodyShopMaterialIds::SideRight,
        LBBodyShopMaterialIds::UpperStructure,
        LBBodyShopMaterialIds::RoofOuter,
        LBBodyShopMaterialIds::FramedBody,
        LBBodyShopMaterialIds::CompleteBody
    };
    const TArray<FName> ExpectedMaterialIds = {
        TEXT("BIW_UNDERBODY"),
        TEXT("BIW_SIDE_LEFT"),
        TEXT("BIW_SIDE_RIGHT"),
        TEXT("BIW_UPPER_STRUCTURE"),
        TEXT("BIW_ROOF_OUTER"),
        TEXT("BIW_FRAMED_BODY"),
        TEXT("BIW_COMPLETE")
    };
    TestEqual(TEXT("Seven approved provisional BIW IDs exist"), MaterialIds.Num(), 7);
    TestEqual(TEXT("Stable provisional IDs remain exact"), MaterialIds, ExpectedMaterialIds);

    const TArray<FName> DefinitionIds =
        FLBBodyShopDefinitionRegistry::GetApprovedUnderbodySliceDefinitionIds();
    TestEqual(TEXT("Approved underbody slice has exactly six cells"), DefinitionIds.Num(), 6);

    TSet<FName> UniqueIds;
    int32 TotalRobotSlots = 0;
    for (const FName DefinitionId : DefinitionIds)
    {
        FLBBodyShopCellDefinition Definition;
        FString Reason;
        TestTrue(FString::Printf(TEXT("Canonical definition %s resolves"),
            *DefinitionId.ToString()),
            FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(DefinitionId, Definition));
        TestTrue(FString::Printf(TEXT("Canonical definition %s validates"),
            *DefinitionId.ToString()),
            FLBBodyShopDefinitionRegistry::ValidateDefinition(Definition, Reason));
        TestFalse(TEXT("Definition IDs remain unique"), UniqueIds.Contains(DefinitionId));
        UniqueIds.Add(DefinitionId);
        TotalRobotSlots += Definition.RobotSlots.Num();
        TestTrue(TEXT("Every cell auto-assembles safety and services"),
            Definition.bAutoAssembleSafetyAndServices);
    }
    TestEqual(TEXT("Slice exposes one handling and two weld slots"), TotalRobotSlots, 3);

    FLBBodyShopCellDefinition Presentation;
    TestTrue(TEXT("Presentation definition resolves"),
        FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(
            LBBodyShopPrototypeIds::PanelPresentation, Presentation));
    TestEqual(TEXT("Presentation cell has one authored slot"),
        Presentation.RobotSlots.Num(), 1);
    if (Presentation.RobotSlots.Num() == 1)
    {
        TestTrue(TEXT("Presentation slot accepts handling robot"),
            Presentation.RobotSlots[0].AllowedRoles.Contains(
                ELBBodyShopRobotRole::PanelHandling));
        TestTrue(TEXT("Presentation slot requires eight-cup EOAT"),
            Presentation.RobotSlots[0].AllowedTools.Contains(
                ELBBodyShopToolType::VacuumEightCup));
    }

    FLBBodyShopCellDefinition Underbody;
    TestTrue(TEXT("Underbody definition resolves"),
        FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(
            LBBodyShopPrototypeIds::UnderbodyFixture, Underbody));
    TestEqual(TEXT("Underbody cell has exactly two authored weld slots"),
        Underbody.RobotSlots.Num(), 2);
    if (Underbody.RobotSlots.Num() == 2)
    {
        const FLBBodyShopRobotSlotDefinition& Left = Underbody.RobotSlots[0];
        const FLBBodyShopRobotSlotDefinition& Right = Underbody.RobotSlots[1];
        const FVector LeftForward = Left.LocalMountTransform.GetUnitAxis(EAxis::X);
        const FVector RightForward = Right.LocalMountTransform.GetUnitAxis(EAxis::X);
        TestTrue(TEXT("Weld mounts retain exact mirrored lateral locations"),
            Left.LocalMountTransform.GetLocation().Equals(FVector(0.0f, -300.0f, 0.0f), 0.01f)
            && Right.LocalMountTransform.GetLocation().Equals(FVector(0.0f, 300.0f, 0.0f), 0.01f));
        TestTrue(TEXT("Robot bodies retain exact readable diagonal mount yaws"),
            FMath::IsNearlyEqual(Left.LocalMountTransform.Rotator().Yaw, 35.0f, 0.01f)
            && FMath::IsNearlyEqual(Right.LocalMountTransform.Rotator().Yaw, -35.0f, 0.01f));
        TestTrue(TEXT("Both robot bases primarily face along positive production flow"),
            LeftForward.X > 0.8f && RightForward.X > 0.8f);
        TestTrue(TEXT("Robot bodies form a readable mirror without facing away from the line"),
            FMath::IsNearlyEqual(LeftForward.X, RightForward.X, 0.01f)
            && FMath::IsNearlyEqual(LeftForward.Y, -RightForward.Y, 0.01f)
            && FMath::IsNearlyEqual(
                Left.LocalMountTransform.Rotator().Yaw,
                -Right.LocalMountTransform.Rotator().Yaw, 0.01f));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopRobotSlotValidationTest,
    "LineBoss.BodyShop.Experimental.FixtureRobotSlotValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopRobotSlotValidationTest::RunTest(const FString& Parameters)
{
    FLBBodyShopCellDefinition Underbody;
    TestTrue(TEXT("Underbody definition resolves"),
        FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(
            LBBodyShopPrototypeIds::UnderbodyFixture, Underbody));

    FLBBodyShopRobotAssignment Left;
    Left.SlotId = TEXT("ROBOT_WELD_LEFT");
    Left.Role = ELBBodyShopRobotRole::SpotWelding;
    Left.Tool = ELBBodyShopToolType::SpotCGun;
    FLBBodyShopRobotAssignment Right = Left;
    Right.SlotId = TEXT("ROBOT_WELD_RIGHT");

    FString Reason;
    TestTrue(TEXT("Exact authored two-robot configuration validates"),
        FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(
            Underbody, {Left, Right}, Reason));

    FLBBodyShopRobotAssignment FreePlacement = Left;
    FreePlacement.SlotId = TEXT("PLAYER_FREE_PLACEMENT");
    TestFalse(TEXT("Unrestricted robot placement is rejected"),
        FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(
            Underbody, {FreePlacement}, Reason));

    FLBBodyShopRobotAssignment WrongTool = Left;
    WrongTool.Tool = ELBBodyShopToolType::VacuumEightCup;
    TestFalse(TEXT("Wrong tool is rejected by authored slot"),
        FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(
            Underbody, {WrongTool}, Reason));

    TestFalse(TEXT("Duplicate slot assignment is rejected"),
        FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(
            Underbody, {Left, Left}, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopExperimentalSaveContractTest,
    "LineBoss.BodyShop.Experimental.SaveV1AtomicContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopExperimentalSaveContractTest::RunTest(const FString& Parameters)
{
    FLBBodyShopExperimentalSaveState State;
    const TArray<FName> DefinitionIds =
        FLBBodyShopDefinitionRegistry::GetApprovedUnderbodySliceDefinitionIds();
    int32 Serial = 1;
    for (const FName DefinitionId : DefinitionIds)
    {
        FLBBodyShopPlacedCellSaveState& Cell = State.Cells.AddDefaulted_GetRef();
        Cell.CellId = FName(*FString::Printf(TEXT("BODYSHOP-CELL-%03d"), Serial++));
        Cell.DefinitionId = DefinitionId;
        Cell.WorldTransform = FTransform(FRotator::ZeroRotator,
            FVector(static_cast<float>(Serial) * 1000.0f, 0.0f, 0.0f));
        Cell.State = ELBBodyShopCellState::Idle;
        Cell.bCommissioned = true;
        FLBBodyShopCellDefinition Definition;
        FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(DefinitionId, Definition);
        for (const FLBBodyShopRobotSlotDefinition& Slot : Definition.RobotSlots)
        {
            FLBBodyShopRobotAssignment& Assignment = Cell.RobotAssignments.AddDefaulted_GetRef();
            Assignment.SlotId = Slot.SlotId;
            Assignment.Role = Slot.AllowedRoles[0];
            Assignment.Tool = Slot.AllowedTools[0];
        }
    }
    State.NextCellSerial = Serial;

    FLBBodyShopWIPSaveState Unit;
    Unit.UnitId = TEXT("BODYSHOP-WIP-001");
    Unit.MaterialId = LBBodyShopMaterialIds::Underbody;
    Unit.CurrentCellId = State.Cells[0].CellId;
    Unit.SourceStillageId = TEXT("STILLAGE-001");
    Unit.GenealogySequence = 1;
    State.WIP.Add(Unit);
    State.Cells[0].QueuedWIPIds.Add(Unit.UnitId);
    State.NextWIPSerial = 2;
    State.NextGenealogySequence = 2;

    FString Reason;
    TestTrue(TEXT("Standalone experimental save validates"),
        FLBBodyShopDefinitionRegistry::ValidateExperimentalSaveState(State, Reason));

    const FLBBodyShopExperimentalSaveState Before = State;
    FLBBodyShopExperimentalSaveState DuplicateWIP = State;
    DuplicateWIP.WIP.Add(Unit);
    TestFalse(TEXT("Duplicate WIP is rejected"),
        FLBBodyShopDefinitionRegistry::ValidateExperimentalSaveState(DuplicateWIP, Reason));
    TestEqual(TEXT("Failed validation does not mutate authoritative state"),
        State.WIP.Num(), Before.WIP.Num());
    TestEqual(TEXT("Experimental schema version remains independent v1"), State.Version, 1);
    return true;
}

#endif
