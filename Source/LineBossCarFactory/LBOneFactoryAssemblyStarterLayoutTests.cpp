#include "LBOneFactoryAssemblyStarterLayout.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryAssemblyStarterTestsPrivate
{
    bool SameStation(const FLBOneFactoryAssemblyStationState& Left,
        const FLBOneFactoryAssemblyStationState& Right)
    {
        return Left.Version == Right.Version
            && Left.StationId == Right.StationId
            && Left.LinePosition == Right.LinePosition
            && Left.WorldTransform.Equals(Right.WorldTransform, 0.001f)
            && Left.FootprintSizeCm.Equals(Right.FootprintSizeCm, 0.01f)
            && Left.Capabilities == Right.Capabilities
            && Left.AssignedOperations == Right.AssignedOperations
            && FMath::IsNearlyEqual(Left.NominalCycleSeconds,
                Right.NominalCycleSeconds, 0.001f)
            && Left.ActiveOrReservedUnitIds == Right.ActiveOrReservedUnitIds;
    }

    bool SameConnection(const FLBOneFactoryAssemblyConnectionState& Left,
        const FLBOneFactoryAssemblyConnectionState& Right)
    {
        return Left.Version == Right.Version
            && Left.ConnectionId == Right.ConnectionId
            && Left.SourceStationId == Right.SourceStationId
            && Left.TargetStationId == Right.TargetStationId
            && FMath::IsNearlyEqual(Left.MaximumRouteLengthCm,
                Right.MaximumRouteLengthCm, 0.001f);
    }

    bool SameState(const FLBOneFactoryAssemblyLayoutState& Left,
        const FLBOneFactoryAssemblyLayoutState& Right)
    {
        if (Left.Version != Right.Version || Left.LayoutId != Right.LayoutId
            || Left.VehicleModelId != Right.VehicleModelId
            || Left.Revision != Right.Revision
            || Left.bCommissioned != Right.bCommissioned
            || Left.InputState != Right.InputState
            || Left.OutputState != Right.OutputState
            || Left.Stations.Num() != Right.Stations.Num()
            || Left.Connections.Num() != Right.Connections.Num())
        {
            return false;
        }
        for (int32 Index = 0; Index < Left.Stations.Num(); ++Index)
        {
            if (!SameStation(Left.Stations[Index], Right.Stations[Index]))
                return false;
        }
        for (int32 Index = 0; Index < Left.Connections.Num(); ++Index)
        {
            if (!SameConnection(Left.Connections[Index],
                    Right.Connections[Index])) return false;
        }
        return true;
    }

    FLBOneFactoryAssemblyStationState* FindStation(
        FLBOneFactoryAssemblyLayoutState& State, const int32 LinePosition)
    {
        return State.Stations.FindByPredicate([LinePosition](
            const FLBOneFactoryAssemblyStationState& Station)
        {
            return Station.LinePosition == LinePosition;
        });
    }

    const FLBOneFactoryAssemblyStationState* FindStation(
        const FLBOneFactoryAssemblyLayoutState& State,
        const int32 LinePosition)
    {
        return State.Stations.FindByPredicate([LinePosition](
            const FLBOneFactoryAssemblyStationState& Station)
        {
            return Station.LinePosition == LinePosition;
        });
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryAssemblyCanonicalLayoutTest,
    "LineBoss.OneFactory.AssemblyStarter.ConfigurableTwentyFourPositionContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryAssemblyCanonicalLayoutTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    FString Reason;
    const FLBOneFactoryAssemblyLayoutState State =
        ULBOneFactoryAssemblyStarterLayoutLibrary::MakeCanonicalStarterLayout();
    TestTrue(TEXT("Canonical configurable Assembly line validates"),
        ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            State, Reason));
    TestEqual(TEXT("Assembly has exactly 24 installed positions"),
        State.Stations.Num(), 24);
    TestEqual(TEXT("Assembly has one exact 23-link carrier route"),
        State.Connections.Num(), 23);
    TestFalse(TEXT("Assembly starts uncommissioned"), State.bCommissioned);
    TestEqual(TEXT("Assembly accepts the painted body state"),
        State.InputState, ELBOneFactoryAssemblyMaterialState::PaintedBody);
    TestEqual(TEXT("Assembly produces a finished vehicle"),
        State.OutputState, ELBOneFactoryAssemblyMaterialState::FinishedVehicle);

    TSet<ELBOneFactoryAssemblyOperation> Operations;
    int32 ConfigurablePositions = 0;
    for (const FLBOneFactoryAssemblyStationState& Station : State.Stations)
    {
        if (Station.Capabilities.Num() > 1) ++ConfigurablePositions;
        TestTrue(TEXT("Canonical position has no decorative WIP"),
            Station.ActiveOrReservedUnitIds.IsEmpty());
        for (const ELBOneFactoryAssemblyOperation Operation :
            Station.AssignedOperations)
        {
            TestFalse(TEXT("No operation is duplicated"),
                Operations.Contains(Operation));
            Operations.Add(Operation);
            TestTrue(TEXT("Assigned position has the required capability"),
                ULBOneFactoryAssemblyStarterLayoutLibrary::
                    StationSupportsOperation(Station, Operation));
            TestFalse(TEXT("Player-facing operation name is never empty"),
                ULBOneFactoryAssemblyStarterLayoutLibrary::
                    GetOperationDisplayName(Operation).IsEmpty());
        }
    }
    TestEqual(TEXT("All 24 required operations exist exactly once"),
        Operations.Num(), 24);
    TestTrue(TEXT("Most installed positions expose multiple valid capabilities"),
        ConfigurablePositions >= 20);
    TestEqual(TEXT("Heavy marriage is at the line midpoint"),
        LBOneFactoryAssemblyStarterTestsPrivate::FindStation(State, 12)
            ->AssignedOperations[0],
        ELBOneFactoryAssemblyOperation::PowertrainMarriage);
    TestEqual(TEXT("Final position dispatches a complete car"),
        LBOneFactoryAssemblyStarterTestsPrivate::FindStation(State, 24)
            ->AssignedOperations[0],
        ELBOneFactoryAssemblyOperation::FinishedVehicleDispatch);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryAssemblyAssignmentTest,
    "LineBoss.OneFactory.AssemblyStarter.AtomicAssignmentCommissionAndRestore",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryAssemblyAssignmentTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryAssemblyAssignmentTest"));
    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryAssemblyStarterLayoutAuthority>()
        : nullptr;
    if (!TestNotNull(TEXT("Assembly starter authority spawns"), Authority))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    TestTrue(TEXT("Assembly authority has exact native identity"),
        Authority->ActorHasTag(
            ALBOneFactoryAssemblyStarterLayoutAuthority::GetAuthorityTag())
        && Authority->ActorHasTag(
            ALBOneFactoryAssemblyStarterLayoutAuthority::GetNativeOnlyTag()));
    TestFalse(TEXT("Assembly data authority never ticks"),
        Authority->PrimaryActorTick.bCanEverTick);

    FString Reason;
    const FLBOneFactoryAssemblyLayoutState Original =
        Authority->CaptureLayout();
    TestTrue(TEXT("Compatible adjacent position accepts consolidated torque work"),
        Authority->AssignOperation(
            ELBOneFactoryAssemblyOperation::UnderbodyTorque,
            LBOneFactoryAssemblyStarterIds::Station(14), Reason));
    const FLBOneFactoryAssemblyLayoutState Consolidated =
        Authority->CaptureLayout();
    TestEqual(TEXT("Assignment increments one revision"),
        Consolidated.Revision, Original.Revision + 1);
    const FLBOneFactoryAssemblyStationState* Position13 =
        LBOneFactoryAssemblyStarterTestsPrivate::FindStation(
            Consolidated, 13);
    const FLBOneFactoryAssemblyStationState* Position14 =
        LBOneFactoryAssemblyStarterTestsPrivate::FindStation(
            Consolidated, 14);
    if (TestNotNull(TEXT("Source position remains installed"), Position13)
        && TestNotNull(TEXT("Target position remains installed"), Position14))
    {
        TestTrue(TEXT("Source position can be temporarily unassigned"),
            Position13->AssignedOperations.IsEmpty());
        TestEqual(TEXT("Compatible position now owns two ordered operations"),
            Position14->AssignedOperations.Num(), 2);
        TestEqual(TEXT("First consolidated operation preserves process order"),
            Position14->AssignedOperations[0],
            ELBOneFactoryAssemblyOperation::UnderbodyTorque);
    }
    TestFalse(TEXT("Assignment change requires recommission"),
        Consolidated.bCommissioned);
    TestTrue(TEXT("Complete compatible assignment commissions"),
        Authority->Commission(Reason));
    TestTrue(TEXT("Commission state is captured"), Authority->IsCommissioned());

    const FLBOneFactoryAssemblyLayoutState Commissioned =
        Authority->CaptureLayout();
    FLBOneFactoryAssemblyLayoutState Duplicate = Commissioned;
    Duplicate.Stations[0].AssignedOperations.Add(
        ELBOneFactoryAssemblyOperation::FinishedVehicleDispatch);
    TestFalse(TEXT("Duplicate required operation rejects restore"),
        Authority->RestoreLayout(Duplicate, Reason));
    TestTrue(TEXT("Rejected restore leaves commissioned state unchanged"),
        LBOneFactoryAssemblyStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Commissioned));

    TestFalse(TEXT("Incompatible position rejects wheel installation"),
        Authority->AssignOperation(
            ELBOneFactoryAssemblyOperation::WheelsAndTires,
            LBOneFactoryAssemblyStarterIds::Station(19), Reason));
    TestTrue(TEXT("Rejected assignment is transactionally unchanged"),
        LBOneFactoryAssemblyStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Commissioned));
    TestTrue(TEXT("Original balanced layout restores exactly"),
        Authority->RestoreLayout(Original, Reason));
    TestTrue(TEXT("Capture and restore are lossless"),
        LBOneFactoryAssemblyStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Original));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryAssemblyMoveAndWIPGateTest,
    "LineBoss.OneFactory.AssemblyStarter.TransactionalMoveAndWIPFailClosed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryAssemblyMoveAndWIPGateTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryAssemblyMoveAndWIPGateTest"));
    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryAssemblyStarterLayoutAuthority>()
        : nullptr;
    if (!TestNotNull(TEXT("Assembly authority spawns"), Authority))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    FString Reason;
    const FLBOneFactoryAssemblyLayoutState Original =
        Authority->CaptureLayout();
    const FLBOneFactoryAssemblyStationState* Dispatch =
        LBOneFactoryAssemblyStarterTestsPrivate::FindStation(Original, 24);
    if (!TestNotNull(TEXT("Dispatch position exists"), Dispatch))
    {
        World->DestroyWorld(false);
        return false;
    }
    FTransform ValidMove = Dispatch->WorldTransform;
    ValidMove.AddToTranslation(FVector(100.0f, 0.0f, 0.0f));
    TestTrue(TEXT("Small in-bay station movement succeeds"),
        Authority->MoveStation(Dispatch->StationId, ValidMove, Reason));
    const FLBOneFactoryAssemblyLayoutState Moved = Authority->CaptureLayout();
    TestEqual(TEXT("Move increments one revision"),
        Moved.Revision, Original.Revision + 1);
    bool bConnectionsUnchanged =
        Moved.Connections.Num() == Original.Connections.Num();
    for (int32 Index = 0; bConnectionsUnchanged
        && Index < Moved.Connections.Num(); ++Index)
    {
        bConnectionsUnchanged =
            LBOneFactoryAssemblyStarterTestsPrivate::SameConnection(
                Moved.Connections[Index], Original.Connections[Index]);
    }
    TestTrue(TEXT("All 23 carrier routes survive movement"),
        bConnectionsUnchanged);

    const FLBOneFactoryAssemblyStationState* Position23 =
        LBOneFactoryAssemblyStarterTestsPrivate::FindStation(Moved, 23);
    if (TestNotNull(TEXT("Position 23 exists"), Position23))
    {
        TestFalse(TEXT("Overlapping move fails closed"),
            Authority->MoveStation(Dispatch->StationId,
                Position23->WorldTransform, Reason));
        TestTrue(TEXT("Failed overlapping move rolls back exactly"),
            LBOneFactoryAssemblyStarterTestsPrivate::SameState(
                Authority->CaptureLayout(), Moved));
    }

    FLBOneFactoryAssemblyLayoutState WithWIP = Moved;
    FLBOneFactoryAssemblyStationState* Marriage =
        LBOneFactoryAssemblyStarterTestsPrivate::FindStation(WithWIP, 12);
    if (TestNotNull(TEXT("Marriage position exists"), Marriage))
        Marriage->ActiveOrReservedUnitIds.Add(TEXT("C2040-WIP-0001"));
    TestTrue(TEXT("Coherent WIP-bearing snapshot restores"),
        Authority->RestoreLayout(WithWIP, Reason));
    const FLBOneFactoryAssemblyLayoutState BeforeBlocked =
        Authority->CaptureLayout();
    TestFalse(TEXT("WIP blocks operation reassignment"),
        Authority->AssignOperation(
            ELBOneFactoryAssemblyOperation::UnderbodyTorque,
            LBOneFactoryAssemblyStarterIds::Station(14), Reason));
    TestFalse(TEXT("WIP blocks station movement"),
        Authority->MoveStation(LBOneFactoryAssemblyStarterIds::Station(24),
            Dispatch->WorldTransform, Reason));
    TestFalse(TEXT("WIP blocks commission"), Authority->Commission(Reason));
    TestTrue(TEXT("Every WIP-rejected mutation preserves the exact state"),
        LBOneFactoryAssemblyStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), BeforeBlocked));

    FLBOneFactoryAssemblyLayoutState DuplicateWIP = WithWIP;
    DuplicateWIP.Stations[0].ActiveOrReservedUnitIds.Add(
        TEXT("C2040-WIP-0001"));
    TestFalse(TEXT("Duplicate WIP identity rejects before mutation"),
        Authority->RestoreLayout(DuplicateWIP, Reason));
    TestTrue(TEXT("Rejected duplicate WIP restore is unchanged"),
        LBOneFactoryAssemblyStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), BeforeBlocked));

    World->DestroyWorld(false);
    return true;
}

#endif
