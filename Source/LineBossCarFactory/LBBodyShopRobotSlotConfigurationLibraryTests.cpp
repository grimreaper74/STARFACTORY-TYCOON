#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopRobotSlotConfigurationLibrary.h"

#include "Misc/AutomationTest.h"

namespace LBBodyShopRobotSlotConfigurationLibraryTestsPrivate
{
    const FLBBodyShopRobotSlotView* FindSlot(
        const TArray<FLBBodyShopRobotSlotView>& Slots, const FName SlotId)
    {
        return Slots.FindByPredicate([SlotId](const FLBBodyShopRobotSlotView& Candidate)
        {
            return Candidate.SlotId == SlotId;
        });
    }

    FLBBodyShopRobotAssignment MakeLeftWeldAssignment()
    {
        FLBBodyShopRobotAssignment Assignment;
        Assignment.SlotId = TEXT("ROBOT_WELD_LEFT");
        Assignment.Role = ELBBodyShopRobotRole::SpotWelding;
        Assignment.Tool = ELBBodyShopToolType::SpotCGun;
        Assignment.bEnabled = true;
        Assignment.Condition01 = 1.0f;
        return Assignment;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopRobotSlotInventoryContractTest,
    "LineBoss.BodyShop.Experimental.RobotConfiguration.AuthoredInventoryAndEnvelopes",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopRobotSlotInventoryContractTest::RunTest(const FString& Parameters)
{
    FLBBodyShopCellDefinition Underbody;
    TestTrue(TEXT("Underbody fixture definition resolves"),
        FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(
            LBBodyShopPrototypeIds::UnderbodyFixture, Underbody));

    const FLBBodyShopRobotAssignment LeftAssignment =
        LBBodyShopRobotSlotConfigurationLibraryTestsPrivate::MakeLeftWeldAssignment();
    const FTransform CellWorldTransform(FRotator(0.0f, 90.0f, 0.0f),
        FVector(1000.0f, 2000.0f, 0.0f));
    TArray<FLBBodyShopRobotSlotView> Slots;
    FString Reason;
    TestTrue(TEXT("Authored slot inventory builds without a world"),
        ULBBodyShopRobotSlotConfigurationLibrary::BuildSlotInventory(
            Underbody, {LeftAssignment}, CellWorldTransform, Slots, Reason));
    TestEqual(TEXT("Inventory preserves exactly the two authored weld slots"), Slots.Num(), 2);

    const FLBBodyShopRobotSlotView* Left =
        LBBodyShopRobotSlotConfigurationLibraryTestsPrivate::FindSlot(
            Slots, TEXT("ROBOT_WELD_LEFT"));
    const FLBBodyShopRobotSlotView* Right =
        LBBodyShopRobotSlotConfigurationLibraryTestsPrivate::FindSlot(
            Slots, TEXT("ROBOT_WELD_RIGHT"));
    TestNotNull(TEXT("Left authored slot is exposed"), Left);
    TestNotNull(TEXT("Right authored slot is exposed"), Right);
    if (Left)
    {
        TestTrue(TEXT("Assigned left slot reports occupied"), Left->bOccupied);
        TestEqual(TEXT("Occupied slot exposes its compatible weld robot role"),
            Left->CurrentAssignment.Role, ELBBodyShopRobotRole::SpotWelding);
        TestEqual(TEXT("Left slot has one compatible role/tool pairing"),
            Left->CompatibleSelections.Num(), 1);
        if (Left->CompatibleSelections.Num() == 1)
        {
            TestEqual(TEXT("Compatible pairing requires the C-gun"),
                Left->CompatibleSelections[0].Tool, ELBBodyShopToolType::SpotCGun);
        }
        TestTrue(TEXT("World mount follows the owning cell transform"),
            Left->WorldMountTransform.GetLocation().Equals(
                CellWorldTransform.TransformPosition(
                    Left->LocalMountTransform.GetLocation()), 0.01f));
        TestTrue(TEXT("Reach radius remains greater than the protected sweep radius"),
            Left->ReachRadiusCm > Left->SweepRadiusCm);
    }
    if (Right)
    {
        TestFalse(TEXT("Unassigned right authored slot reports vacant"), Right->bOccupied);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopRobotSlotMutationContractTest,
    "LineBoss.BodyShop.Experimental.RobotConfiguration.ValidatedAddReplaceRemove",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopRobotSlotMutationContractTest::RunTest(const FString& Parameters)
{
    FLBBodyShopCellDefinition Underbody;
    TestTrue(TEXT("Underbody fixture definition resolves"),
        FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(
            LBBodyShopPrototypeIds::UnderbodyFixture, Underbody));

    FString Reason;
    TArray<FLBBodyShopRobotAssignment> Assignments;
    TestTrue(TEXT("A compatible robot can be added to a vacant authored slot"),
        ULBBodyShopRobotSlotConfigurationLibrary::ValidateRobotSlotMutation(
            Underbody, Assignments, TEXT("ROBOT_WELD_LEFT"),
            ELBBodyShopRobotSlotMutation::AddToVacantSlot,
            ELBBodyShopRobotRole::SpotWelding, ELBBodyShopToolType::SpotCGun, Reason));
    TestFalse(TEXT("A vacant slot cannot use replace semantics"),
        ULBBodyShopRobotSlotConfigurationLibrary::ValidateRobotSlotMutation(
            Underbody, Assignments, TEXT("ROBOT_WELD_LEFT"),
            ELBBodyShopRobotSlotMutation::ReplaceOccupiedSlot,
            ELBBodyShopRobotRole::SpotWelding, ELBBodyShopToolType::SpotCGun, Reason));
    TestFalse(TEXT("A vacant slot cannot use remove semantics"),
        ULBBodyShopRobotSlotConfigurationLibrary::ValidateRobotSlotMutation(
            Underbody, Assignments, TEXT("ROBOT_WELD_LEFT"),
            ELBBodyShopRobotSlotMutation::RemoveFromOccupiedSlot,
            ELBBodyShopRobotRole::None, ELBBodyShopToolType::None, Reason));

    Assignments.Add(LBBodyShopRobotSlotConfigurationLibraryTestsPrivate::MakeLeftWeldAssignment());
    TestFalse(TEXT("Add semantics cannot overwrite an occupied slot"),
        ULBBodyShopRobotSlotConfigurationLibrary::ValidateRobotSlotMutation(
            Underbody, Assignments, TEXT("ROBOT_WELD_LEFT"),
            ELBBodyShopRobotSlotMutation::AddToVacantSlot,
            ELBBodyShopRobotRole::SpotWelding, ELBBodyShopToolType::SpotCGun, Reason));
    TestTrue(TEXT("A compatible selection can replace an occupied authored slot"),
        ULBBodyShopRobotSlotConfigurationLibrary::ValidateRobotSlotMutation(
            Underbody, Assignments, TEXT("ROBOT_WELD_LEFT"),
            ELBBodyShopRobotSlotMutation::ReplaceOccupiedSlot,
            ELBBodyShopRobotRole::SpotWelding, ELBBodyShopToolType::SpotCGun, Reason));
    TestTrue(TEXT("An occupied authored slot can be removed"),
        ULBBodyShopRobotSlotConfigurationLibrary::ValidateRobotSlotMutation(
            Underbody, Assignments, TEXT("ROBOT_WELD_LEFT"),
            ELBBodyShopRobotSlotMutation::RemoveFromOccupiedSlot,
            ELBBodyShopRobotRole::None, ELBBodyShopToolType::None, Reason));
    TestFalse(TEXT("The wrong tool remains rejected during replacement"),
        ULBBodyShopRobotSlotConfigurationLibrary::ValidateRobotSlotMutation(
            Underbody, Assignments, TEXT("ROBOT_WELD_LEFT"),
            ELBBodyShopRobotSlotMutation::ReplaceOccupiedSlot,
            ELBBodyShopRobotRole::SpotWelding, ELBBodyShopToolType::VacuumEightCup, Reason));
    TestFalse(TEXT("Free robot placement remains impossible"),
        ULBBodyShopRobotSlotConfigurationLibrary::ValidateRobotSlotMutation(
            Underbody, Assignments, TEXT("PLAYER_FREE_PLACEMENT"),
            ELBBodyShopRobotSlotMutation::AddToVacantSlot,
            ELBBodyShopRobotRole::SpotWelding, ELBBodyShopToolType::SpotCGun, Reason));
    TestFalse(TEXT("An invalid mutation enum fails closed"),
        ULBBodyShopRobotSlotConfigurationLibrary::ValidateRobotSlotMutation(
            Underbody, Assignments, TEXT("ROBOT_WELD_LEFT"),
            static_cast<ELBBodyShopRobotSlotMutation>(255),
            ELBBodyShopRobotRole::SpotWelding, ELBBodyShopToolType::SpotCGun, Reason));
    return true;
}

#endif
