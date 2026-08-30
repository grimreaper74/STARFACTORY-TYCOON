#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopBuildAuthority.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBBodyShopBuildAuthorityTestsPrivate
{
    const FLBBodyShopPortDefinition* FindPort(const FLBBodyShopCellDefinition& Definition,
        const FName PortId)
    {
        return Definition.Ports.FindByPredicate([PortId](const FLBBodyShopPortDefinition& Port)
        {
            return Port.PortId == PortId;
        });
    }

    FBox GetFootprint(const FLBBodyShopCellDefinition& Definition, const FTransform& Transform)
    {
        const FVector Half = Definition.FootprintCm * 0.5f;
        return FBox(-Half, Half).TransformBy(Transform);
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopApprovedLayoutContractTest,
    "LineBoss.BodyShop.Experimental.ApprovedUnderbodyLayoutGridAndPorts",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopApprovedLayoutContractTest::RunTest(const FString& Parameters)
{
    const TArray<FLBBodyShopApprovedLayoutItem> Layout =
        ALBBodyShopBuildAuthority::GetApprovedUnderbodySliceLayout();
    TestEqual(TEXT("Approved vertical slice has six placeable cells"), Layout.Num(), 6);

    TArray<FLBBodyShopCellDefinition> Definitions;
    Definitions.Reserve(Layout.Num());
    for (const FLBBodyShopApprovedLayoutItem& Item : Layout)
    {
        FLBBodyShopCellDefinition Definition;
        TestTrue(FString::Printf(TEXT("Approved cell %s resolves"),
            *Item.DefinitionId.ToString()),
            FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(Item.DefinitionId, Definition));
        const FVector Location = Item.WorldTransform.GetLocation();
        TestTrue(TEXT("Approved location is on the 100 cm build grid"),
            FMath::IsNearlyEqual(Location.X, FMath::GridSnap(Location.X, 100.0f), 0.01f)
            && FMath::IsNearlyEqual(Location.Y, FMath::GridSnap(Location.Y, 100.0f), 0.01f)
            && FMath::IsNearlyZero(Location.Z, 0.01f));
        Definitions.Add(Definition);
    }

    for (int32 Left = 0; Left < Layout.Num(); ++Left)
    {
        for (int32 Right = Left + 1; Right < Layout.Num(); ++Right)
        {
            const FBox LeftBox = LBBodyShopBuildAuthorityTestsPrivate::GetFootprint(
                Definitions[Left], Layout[Left].WorldTransform).ExpandBy(-0.5f);
            const FBox RightBox = LBBodyShopBuildAuthorityTestsPrivate::GetFootprint(
                Definitions[Right], Layout[Right].WorldTransform).ExpandBy(-0.5f);
            TestFalse(TEXT("Approved cell footprints do not overlap"), LeftBox.Intersect(RightBox));
        }
    }

    struct FExpectedLink
    {
        int32 SourceIndex;
        FName SourcePortId;
        int32 TargetIndex;
        FName TargetPortId;
    };
    const FExpectedLink Links[] = {
        {0, LBBodyShopPrototypeIds::StillageOut, 1, LBBodyShopPrototypeIds::StillageIn},
        {1, LBBodyShopPrototypeIds::PanelOut, 2, LBBodyShopPrototypeIds::PanelIn},
        {2, LBBodyShopPrototypeIds::SkidOut, 3, LBBodyShopPrototypeIds::SkidIn},
        {3, LBBodyShopPrototypeIds::SkidOut, 4, LBBodyShopPrototypeIds::BodyIn},
        {4, LBBodyShopPrototypeIds::BodyOut, 5, LBBodyShopPrototypeIds::BodyIn}
    };
    for (const FExpectedLink& Link : Links)
    {
        const FLBBodyShopPortDefinition* Source =
            LBBodyShopBuildAuthorityTestsPrivate::FindPort(Definitions[Link.SourceIndex],
                Link.SourcePortId);
        const FLBBodyShopPortDefinition* Target =
            LBBodyShopBuildAuthorityTestsPrivate::FindPort(Definitions[Link.TargetIndex],
                Link.TargetPortId);
        TestNotNull(TEXT("Approved link has a source port"), Source);
        TestNotNull(TEXT("Approved link has a target port"), Target);
        if (!Source || !Target) continue;

        const FTransform SourceWorld = Source->LocalTransform * Layout[Link.SourceIndex].WorldTransform;
        const FTransform TargetWorld = Target->LocalTransform * Layout[Link.TargetIndex].WorldTransform;
        TestTrue(TEXT("Approved link port locations are coincident"),
            FVector::Dist(SourceWorld.GetLocation(), TargetWorld.GetLocation()) <= 0.01f);
        const float Facing = FMath::Abs(FRotator::NormalizeAxis(
            SourceWorld.Rotator().Yaw - TargetWorld.Rotator().Yaw));
        TestTrue(TEXT("Approved link ports face each other"),
            FMath::IsNearlyEqual(Facing, 180.0f, 0.01f));
        TestEqual(TEXT("Approved link transport matches"), Source->Transport, Target->Transport);
        TestEqual(TEXT("Approved link material matches"), Source->MaterialId, Target->MaterialId);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPilotSkidSourceContractTest,
    "LineBoss.BodyShop.Experimental.PilotSkidSourceContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPilotSkidSourceContractTest::RunTest(const FString& Parameters)
{
    FLBBodyShopCellDefinition Underbody;
    TestTrue(TEXT("Underbody fixture definition resolves"),
        FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(
            LBBodyShopPrototypeIds::UnderbodyFixture, Underbody));
    const FLBBodyShopPortDefinition* SkidIn =
        LBBodyShopBuildAuthorityTestsPrivate::FindPort(Underbody, LBBodyShopPrototypeIds::SkidIn);
    TestNotNull(TEXT("Underbody has an authored skid input"), SkidIn);
    if (SkidIn)
    {
        TestEqual(TEXT("Pilot source uses the skid transport contract"),
            SkidIn->Transport, ELBBodyShopTransportType::SkidConveyor);
        TestEqual(TEXT("Pilot source feeds the provisional underbody material"),
            SkidIn->MaterialId, LBBodyShopMaterialIds::Underbody);
    }
    TestEqual(TEXT("The first slice stays at the approved six placeable cells"),
        ALBBodyShopBuildAuthority::GetApprovedUnderbodySliceLayout().Num(), 6);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPlacementGridAndQuarterTurnPreviewTest,
    "LineBoss.BodyShop.Experimental.Placement.GridAndQuarterTurnPreview",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPlacementGridAndQuarterTurnPreviewTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBBodyShopPlacementGridAndQuarterTurnPreviewTest")));
    if (!TestNotNull(TEXT("Synthetic Body Shop placement world exists"), World))
        return false;

    ALBBodyShopBuildAuthority* Authority = World->SpawnActor<ALBBodyShopBuildAuthority>();
    if (TestNotNull(TEXT("Body Shop placement authority spawns"), Authority))
    {
        bool bValid = false;
        FString Reason;
        const FTransform ValidQuarterTurn(FRotator(0.0f, 90.0f, 0.0f),
            FVector(0.0f, 1000.0f, 0.0f), FVector::OneVector);
        Authority->ValidateModulePlacementForValidation(
            LBBodyShopPrototypeIds::OutputBuffer, ValidQuarterTurn, bValid, Reason);
        TestTrue(TEXT("A 100 cm-grid, 90-degree player preview is accepted"), bValid);
        TestTrue(TEXT("Accepted placement has no rejection reason"), Reason.IsEmpty());

        Reason.Reset();
        const FTransform InvalidRotation(FRotator(0.0f, 45.0f, 0.0f),
            FVector(0.0f, 1000.0f, 0.0f), FVector::OneVector);
        Authority->ValidateModulePlacementForValidation(
            LBBodyShopPrototypeIds::OutputBuffer, InvalidRotation, bValid, Reason);
        TestFalse(TEXT("An on-grid 45-degree player preview is rejected"), bValid);
        TestTrue(TEXT("Invalid rotation supplies a player-facing reason"), !Reason.IsEmpty());

        Reason.Reset();
        const FTransform InvalidGrid(FRotator(0.0f, 90.0f, 0.0f),
            FVector(50.0f, 1050.0f, 0.0f), FVector::OneVector);
        Authority->ValidateModulePlacementForValidation(
            LBBodyShopPrototypeIds::OutputBuffer, InvalidGrid, bValid, Reason);
        TestFalse(TEXT("An off-grid 90-degree player preview is rejected"), bValid);
        TestTrue(TEXT("Invalid grid position supplies a player-facing reason"), !Reason.IsEmpty());
        TestEqual(TEXT("Placement preview does not mutate the cell graph"),
            Authority->GetPlacedCells().Num(), 0);
    }

    World->DestroyWorld(false);
    return true;
}

#endif
