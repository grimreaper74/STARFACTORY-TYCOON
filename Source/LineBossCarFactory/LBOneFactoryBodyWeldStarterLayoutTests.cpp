#include "LBOneFactoryBodyWeldStarterLayout.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryBodyWeldStarterTestsPrivate
{
    bool SameStation(const FLBOneFactoryBodyWeldStationState& Left,
        const FLBOneFactoryBodyWeldStationState& Right)
    {
        return Left.Version == Right.Version
            && Left.StationId == Right.StationId
            && Left.LinePosition == Right.LinePosition
            && Left.WorldTransform.Equals(Right.WorldTransform, 0.001f)
            && Left.FootprintSizeCm.Equals(Right.FootprintSizeCm, 0.01f)
            && Left.Capabilities == Right.Capabilities
            && Left.AssignedProgrammes == Right.AssignedProgrammes
            && Left.SupportedRobotRoles == Right.SupportedRobotRoles
            && Left.LeftRobotRole == Right.LeftRobotRole
            && Left.RightRobotRole == Right.RightRobotRole
            && Left.bMirroredLargeSixAxisPair
                == Right.bMirroredLargeSixAxisPair
            && FMath::IsNearlyEqual(Left.NominalCycleSeconds,
                Right.NominalCycleSeconds, 0.001f)
            && Left.ActiveOrReservedUnitIds
                == Right.ActiveOrReservedUnitIds;
    }

    bool SameConnection(const FLBOneFactoryBodyWeldConnectionState& Left,
        const FLBOneFactoryBodyWeldConnectionState& Right)
    {
        return Left.Version == Right.Version
            && Left.ConnectionId == Right.ConnectionId
            && Left.SourceStationId == Right.SourceStationId
            && Left.TargetStationId == Right.TargetStationId
            && FMath::IsNearlyEqual(Left.MaximumRouteLengthCm,
                Right.MaximumRouteLengthCm, 0.001f);
    }

    bool SameState(const FLBOneFactoryBodyWeldLayoutState& Left,
        const FLBOneFactoryBodyWeldLayoutState& Right)
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

    FLBOneFactoryBodyWeldStationState* FindStation(
        FLBOneFactoryBodyWeldLayoutState& State, const int32 LinePosition)
    {
        return State.Stations.FindByPredicate([LinePosition](
            const FLBOneFactoryBodyWeldStationState& Station)
        {
            return Station.LinePosition == LinePosition;
        });
    }

    const FLBOneFactoryBodyWeldStationState* FindStation(
        const FLBOneFactoryBodyWeldLayoutState& State,
        const int32 LinePosition)
    {
        return State.Stations.FindByPredicate([LinePosition](
            const FLBOneFactoryBodyWeldStationState& Station)
        {
            return Station.LinePosition == LinePosition;
        });
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryBodyWeldCanonicalLayoutTest,
    "LineBoss.OneFactory.BodyWeldStarter.ConfigurableEighteenPositionContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryBodyWeldCanonicalLayoutTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    FString Reason;
    const FLBOneFactoryBodyWeldLayoutState State =
        ULBOneFactoryBodyWeldStarterLayoutLibrary::
            MakeCanonicalStarterLayout();
    TestTrue(TEXT("Canonical configurable Body/Weld line validates"),
        ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            State, Reason));
    TestEqual(TEXT("Body/Weld has exactly 18 installed positions"),
        State.Stations.Num(), 18);
    TestEqual(TEXT("Body/Weld has one exact 17-link skid route"),
        State.Connections.Num(), 17);
    TestFalse(TEXT("Body/Weld starts uncommissioned"),
        State.bCommissioned);
    TestEqual(TEXT("Body/Weld accepts pressed panel sets"), State.InputState,
        ELBOneFactoryBodyWeldMaterialState::PressedPanelSet);
    TestEqual(TEXT("Body/Weld produces a body in white"), State.OutputState,
        ELBOneFactoryBodyWeldMaterialState::BodyInWhite);

    TSet<ELBOneFactoryBodyWeldProgramme> Programmes;
    int32 MirroredRobotCount = 0;
    int32 MultiCapabilityPositions = 0;
    for (const FLBOneFactoryBodyWeldStationState& Station : State.Stations)
    {
        if (Station.Capabilities.Num() > 1) ++MultiCapabilityPositions;
        if (Station.bMirroredLargeSixAxisPair) MirroredRobotCount += 2;
        TestTrue(TEXT("Canonical Body/Weld position has no logical WIP"),
            Station.ActiveOrReservedUnitIds.IsEmpty());
        TestTrue(TEXT("Left large robot has a supported explicit duty"),
            ULBOneFactoryBodyWeldStarterLayoutLibrary::
                StationSupportsRobotRole(Station, Station.LeftRobotRole));
        TestTrue(TEXT("Right large robot has a supported explicit duty"),
            ULBOneFactoryBodyWeldStarterLayoutLibrary::
                StationSupportsRobotRole(Station, Station.RightRobotRole));
        for (const ELBOneFactoryBodyWeldProgramme Programme :
            Station.AssignedProgrammes)
        {
            TestFalse(TEXT("No Body/Weld programme is duplicated"),
                Programmes.Contains(Programme));
            Programmes.Add(Programme);
            TestTrue(TEXT("Assigned position has the required capability"),
                ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    StationSupportsProgramme(Station, Programme));
            const ELBOneFactoryBodyWeldRobotRole RequiredRole =
                ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    GetRequiredRobotRole(Programme);
            TestTrue(TEXT("Assigned programme has its required robot duty"),
                Station.LeftRobotRole == RequiredRole
                    || Station.RightRobotRole == RequiredRole);
            TestFalse(TEXT("Programme display name is never empty"),
                ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    GetProgrammeDisplayName(Programme).IsEmpty());
        }
    }
    TestEqual(TEXT("All 18 required programmes exist exactly once"),
        Programmes.Num(), 18);
    TestEqual(TEXT("Every position has a mirrored pair of large robots"),
        MirroredRobotCount, 36);
    TestEqual(TEXT("Every installed position exposes multiple capabilities"),
        MultiCapabilityPositions, 18);
    TestEqual(TEXT("First position receives pressed panels"),
        LBOneFactoryBodyWeldStarterTestsPrivate::FindStation(State, 1)
            ->AssignedProgrammes[0],
        ELBOneFactoryBodyWeldProgramme::PressedPanelReceive);
    TestEqual(TEXT("Final position hands off the body in white"),
        LBOneFactoryBodyWeldStarterTestsPrivate::FindStation(State, 18)
            ->AssignedProgrammes[0],
        ELBOneFactoryBodyWeldProgramme::BIWHandoff);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryBodyWeldAssignmentAndRobotRoleTest,
    "LineBoss.OneFactory.BodyWeldStarter.AtomicProgrammeRobotRoleCommissionAndRestore",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryBodyWeldAssignmentAndRobotRoleTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryBodyWeldAssignmentTest"));
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryBodyWeldStarterLayoutAuthority>()
        : nullptr;
    if (!TestNotNull(TEXT("Body/Weld starter authority spawns"), Authority))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    TestTrue(TEXT("Body/Weld authority has exact native identity"),
        Authority->ActorHasTag(
            ALBOneFactoryBodyWeldStarterLayoutAuthority::GetAuthorityTag())
        && Authority->ActorHasTag(
            ALBOneFactoryBodyWeldStarterLayoutAuthority::
                GetNativeOnlyTag()));
    TestFalse(TEXT("Body/Weld data authority never ticks"),
        Authority->PrimaryActorTick.bCanEverTick);

    FString Reason;
    const FLBOneFactoryBodyWeldLayoutState Original =
        Authority->CaptureLayout();
    TestTrue(TEXT("Mirrored underbody robot duties swap atomically"),
        Authority->AssignRobotPairRoles(
            LBOneFactoryBodyWeldStarterIds::Station(2),
            ELBOneFactoryBodyWeldRobotRole::SpotWelding,
            ELBOneFactoryBodyWeldRobotRole::GeometryClamp, Reason));
    const FLBOneFactoryBodyWeldLayoutState RoleSwapped =
        Authority->CaptureLayout();
    TestEqual(TEXT("Robot role assignment increments one revision"),
        RoleSwapped.Revision, Original.Revision + 1);

    TestTrue(TEXT("Compatible position accepts consolidated geometry work"),
        Authority->AssignProgramme(
            ELBOneFactoryBodyWeldProgramme::FrontUnderbodyGeometry,
            LBOneFactoryBodyWeldStarterIds::Station(3), Reason));
    const FLBOneFactoryBodyWeldLayoutState Consolidated =
        Authority->CaptureLayout();
    TestEqual(TEXT("Programme assignment increments one more revision"),
        Consolidated.Revision, RoleSwapped.Revision + 1);
    const FLBOneFactoryBodyWeldStationState* Position2 =
        LBOneFactoryBodyWeldStarterTestsPrivate::FindStation(
            Consolidated, 2);
    const FLBOneFactoryBodyWeldStationState* Position3 =
        LBOneFactoryBodyWeldStarterTestsPrivate::FindStation(
            Consolidated, 3);
    if (TestNotNull(TEXT("Source Body/Weld position remains installed"),
            Position2)
        && TestNotNull(TEXT("Target Body/Weld position remains installed"),
            Position3))
    {
        TestTrue(TEXT("Source position can be temporarily unassigned"),
            Position2->AssignedProgrammes.IsEmpty());
        TestEqual(TEXT("Compatible target owns two ordered programmes"),
            Position3->AssignedProgrammes.Num(), 2);
        TestEqual(TEXT("Consolidated process order is preserved"),
            Position3->AssignedProgrammes[0],
            ELBOneFactoryBodyWeldProgramme::FrontUnderbodyGeometry);
    }
    TestTrue(TEXT("Complete compatible Body/Weld layout commissions"),
        Authority->Commission(Reason));
    const FLBOneFactoryBodyWeldLayoutState Commissioned =
        Authority->CaptureLayout();

    TestFalse(TEXT("Incompatible robot pair cannot remove a required duty"),
        Authority->AssignRobotPairRoles(
            LBOneFactoryBodyWeldStarterIds::Station(4),
            ELBOneFactoryBodyWeldRobotRole::GeometryClamp,
            ELBOneFactoryBodyWeldRobotRole::GeometryClamp, Reason));
    TestTrue(TEXT("Rejected role assignment is transactionally unchanged"),
        LBOneFactoryBodyWeldStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Commissioned));
    TestFalse(TEXT("Incompatible position rejects main-body spot weld"),
        Authority->AssignProgramme(
            ELBOneFactoryBodyWeldProgramme::MainBodySpotWeld,
            LBOneFactoryBodyWeldStarterIds::Station(13), Reason));
    TestTrue(TEXT("Rejected programme assignment preserves commission"),
        LBOneFactoryBodyWeldStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Commissioned));

    FLBOneFactoryBodyWeldLayoutState Duplicate = Commissioned;
    Duplicate.Stations[0].AssignedProgrammes.Add(
        ELBOneFactoryBodyWeldProgramme::BIWHandoff);
    TestFalse(TEXT("Duplicate required programme rejects restore"),
        Authority->RestoreLayout(Duplicate, Reason));
    TestTrue(TEXT("Rejected restore leaves commissioned state unchanged"),
        LBOneFactoryBodyWeldStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Commissioned));
    TestTrue(TEXT("Original balanced layout restores exactly"),
        Authority->RestoreLayout(Original, Reason));
    TestTrue(TEXT("Body/Weld capture and restore are lossless"),
        LBOneFactoryBodyWeldStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Original));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryBodyWeldMoveAndWIPGateTest,
    "LineBoss.OneFactory.BodyWeldStarter.TransactionalMoveAndWIPFailClosed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryBodyWeldMoveAndWIPGateTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryBodyWeldMoveAndWIPTest"));
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryBodyWeldStarterLayoutAuthority>()
        : nullptr;
    if (!TestNotNull(TEXT("Body/Weld authority spawns"), Authority))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    const FLBOneFactoryBodyWeldLayoutState Original =
        Authority->CaptureLayout();
    const FLBOneFactoryBodyWeldStationState* Handoff =
        LBOneFactoryBodyWeldStarterTestsPrivate::FindStation(Original, 18);
    if (!TestNotNull(TEXT("BIW handoff position exists"), Handoff))
    {
        World->DestroyWorld(false);
        return false;
    }
    FTransform ValidMove = Handoff->WorldTransform;
    ValidMove.AddToTranslation(FVector(100.0f, 0.0f, 0.0f));
    TestTrue(TEXT("Small in-bay Body/Weld movement succeeds"),
        Authority->MoveStation(Handoff->StationId, ValidMove, Reason));
    const FLBOneFactoryBodyWeldLayoutState Moved =
        Authority->CaptureLayout();
    TestEqual(TEXT("Body/Weld move increments one revision"),
        Moved.Revision, Original.Revision + 1);

    const FLBOneFactoryBodyWeldStationState* Position17 =
        LBOneFactoryBodyWeldStarterTestsPrivate::FindStation(Moved, 17);
    if (TestNotNull(TEXT("Body/Weld position 17 exists"), Position17))
    {
        TestFalse(TEXT("Overlapping Body/Weld move fails closed"),
            Authority->MoveStation(Handoff->StationId,
                Position17->WorldTransform, Reason));
        TestTrue(TEXT("Failed overlapping move rolls back exactly"),
            LBOneFactoryBodyWeldStarterTestsPrivate::SameState(
                Authority->CaptureLayout(), Moved));
    }

    FLBOneFactoryBodyWeldLayoutState WithWIP = Moved;
    FLBOneFactoryBodyWeldStationState* Framing =
        LBOneFactoryBodyWeldStarterTestsPrivate::FindStation(WithWIP, 7);
    if (TestNotNull(TEXT("Body framing position exists"), Framing))
        Framing->ActiveOrReservedUnitIds.Add(TEXT("C2040-BIW-0001"));
    TestTrue(TEXT("Coherent WIP-bearing Body/Weld snapshot restores"),
        Authority->RestoreLayout(WithWIP, Reason));
    const FLBOneFactoryBodyWeldLayoutState BeforeBlocked =
        Authority->CaptureLayout();
    TestFalse(TEXT("WIP blocks Body/Weld programme reassignment"),
        Authority->AssignProgramme(
            ELBOneFactoryBodyWeldProgramme::FrontUnderbodyGeometry,
            LBOneFactoryBodyWeldStarterIds::Station(3), Reason));
    TestFalse(TEXT("WIP blocks mirrored robot role reassignment"),
        Authority->AssignRobotPairRoles(
            LBOneFactoryBodyWeldStarterIds::Station(2),
            ELBOneFactoryBodyWeldRobotRole::SpotWelding,
            ELBOneFactoryBodyWeldRobotRole::GeometryClamp, Reason));
    TestFalse(TEXT("WIP blocks Body/Weld station movement"),
        Authority->MoveStation(Handoff->StationId,
            Handoff->WorldTransform, Reason));
    TestFalse(TEXT("WIP blocks Body/Weld commission"),
        Authority->Commission(Reason));
    TestTrue(TEXT("Every WIP-rejected mutation preserves exact state"),
        LBOneFactoryBodyWeldStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), BeforeBlocked));

    FLBOneFactoryBodyWeldLayoutState DuplicateWIP = WithWIP;
    DuplicateWIP.Stations[0].ActiveOrReservedUnitIds.Add(
        TEXT("C2040-BIW-0001"));
    TestFalse(TEXT("Duplicate Body/Weld WIP identity rejects restore"),
        Authority->RestoreLayout(DuplicateWIP, Reason));
    TestTrue(TEXT("Rejected duplicate WIP restore is unchanged"),
        LBOneFactoryBodyWeldStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), BeforeBlocked));

    World->DestroyWorld(false);
    return true;
}

#endif
