#include "LBOneFactoryPressStarterLayout.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryPressStarterTestsPrivate
{
    bool SameStation(const FLBOneFactoryPressStarterStationState& Left,
        const FLBOneFactoryPressStarterStationState& Right)
    {
        return Left.Version == Right.Version
            && Left.StationId == Right.StationId
            && Left.Role == Right.Role
            && Left.WorldTransform.Equals(Right.WorldTransform, 0.001f)
            && Left.FootprintSizeCm.Equals(Right.FootprintSizeCm, 0.01f)
            && Left.bPlayerReconfigurable == Right.bPlayerReconfigurable
            && Left.VehicleModelId == Right.VehicleModelId
            && Left.PanelTypeId == Right.PanelTypeId
            && Left.DieId == Right.DieId
            && Left.ActiveOrReservedUnitIds == Right.ActiveOrReservedUnitIds;
    }

    bool SameConnection(const FLBOneFactoryPressStarterConnectionState& Left,
        const FLBOneFactoryPressStarterConnectionState& Right)
    {
        return Left.Version == Right.Version
            && Left.ConnectionId == Right.ConnectionId
            && Left.SourceStationId == Right.SourceStationId
            && Left.TargetStationId == Right.TargetStationId
            && Left.MaterialClass == Right.MaterialClass
            && FMath::IsNearlyEqual(Left.MaximumRouteLengthCm,
                Right.MaximumRouteLengthCm, 0.01f);
    }

    bool SameState(const FLBOneFactoryPressStarterLayoutState& Left,
        const FLBOneFactoryPressStarterLayoutState& Right)
    {
        if (Left.Version != Right.Version || Left.LayoutId != Right.LayoutId
            || Left.Revision != Right.Revision
            || Left.bCommissioned != Right.bCommissioned
            || Left.Stations.Num() != Right.Stations.Num()
            || Left.Connections.Num() != Right.Connections.Num())
        {
            return false;
        }
        for (int32 Index = 0; Index < Left.Stations.Num(); ++Index)
            if (!SameStation(Left.Stations[Index], Right.Stations[Index]))
                return false;
        for (int32 Index = 0; Index < Left.Connections.Num(); ++Index)
            if (!SameConnection(Left.Connections[Index],
                    Right.Connections[Index])) return false;
        return true;
    }

    FLBOneFactoryPressStarterStationState* FindStation(
        FLBOneFactoryPressStarterLayoutState& State, const FName StationId)
    {
        return State.Stations.FindByPredicate([StationId](
            const FLBOneFactoryPressStarterStationState& Station)
        { return Station.StationId == StationId; });
    }

    const FLBOneFactoryPressStarterStationState* FindStation(
        const FLBOneFactoryPressStarterLayoutState& State, const FName StationId)
    {
        return State.Stations.FindByPredicate([StationId](
            const FLBOneFactoryPressStarterStationState& Station)
        { return Station.StationId == StationId; });
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPressStarterNativeProfileTest,
    "LineBoss.OneFactory.PressStarter.NativeOnlyProfileAndCanonicalTopology",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPressStarterNativeProfileTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    FString Reason;
    const FLBOneFactoryPressNativeOnlyProfile Profile =
        ULBOneFactoryPressStarterLayoutLibrary::MakeNativeOnlyProfile();
    TestTrue(TEXT("Exact Press native-only profile validates"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeOnlyProfile(
            Profile, Reason));
    TestEqual(TEXT("Only four audited runtime classes are allowlisted"),
        Profile.AllowedClassPaths.Num(), 4);
    TestTrue(TEXT("Data authority class and native code reference are accepted"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
            ELBOneFactoryAssetProvenance::NativeCode, Reason));
    TestTrue(TEXT("Engine-shape AGV route presentation is accepted"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBFactoryAGVInfrastructure"),
            TEXT("/Engine/BasicShapes/Cube.Cube"),
            ELBOneFactoryAssetProvenance::NativeProcedural, Reason));
    TestTrue(TEXT("Exact native Press starter presentation is accepted"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterPresentationActor"),
            TEXT("/Engine/BasicShapes/Cube.Cube"),
            ELBOneFactoryAssetProvenance::NativeProcedural, Reason));
    TestTrue(TEXT("Isolated native Press art-direction layer is accepted"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressArtDirectionActor"),
            TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001/Materials/MI_CA_MW_PT_AD_WarmWhite_v001.MI_CA_MW_PT_AD_WarmWhite_v001"),
            ELBOneFactoryAssetProvenance::NativeAuthored, Reason));
    TestTrue(TEXT("Dedicated future OneFactory native Press root is accepted"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
            TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SM_Test.SM_Test"),
            ELBOneFactoryAssetProvenance::NativeAuthored, Reason));
    TestFalse(TEXT("Generic build machine is excluded because its presentation is mixed"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBFactoryBuildMachine"),
            TEXT("/Engine/BasicShapes/Cube.Cube"),
            ELBOneFactoryAssetProvenance::NativeProcedural, Reason));
    TestFalse(TEXT("Current Press train class is excluded from the native starter"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBPressTrainAStation"),
            TEXT("/Engine/BasicShapes/Cube.Cube"),
            ELBOneFactoryAssetProvenance::NativeProcedural, Reason));
    TestFalse(TEXT("A validation-only token fails even under the native root"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
            TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/Developer/Validation/Fixture"),
            ELBOneFactoryAssetProvenance::NativeAuthored, Reason));
    TestTrue(TEXT("The reversal freed generator-named art under the native root"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
            TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MeshyFixture"),
            ELBOneFactoryAssetProvenance::NativeAuthored, Reason));
    TestFalse(TEXT("Historic Candidate roots receive no implicit trust"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
            TEXT("/Game/LineBoss/Candidates/PressShop/UnknownFixture"),
            ELBOneFactoryAssetProvenance::VerifiedPreMeshyNative, Reason));

    const FLBOneFactoryPressStarterLayoutState Canonical =
        ULBOneFactoryPressStarterLayoutLibrary::MakeCanonicalStarterLayout();
    TestTrue(TEXT("Canonical seven-station Press starter validates"),
        ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            Canonical, Reason));
    TestEqual(TEXT("Starter has seven stable responsibilities"),
        Canonical.Stations.Num(), 7);
    TestEqual(TEXT("Starter has one contiguous six-route graph"),
        Canonical.Connections.Num(), 6);
    const FLBOneFactoryPressStarterStationState* CanonicalPress =
        LBOneFactoryPressStarterTestsPrivate::FindStation(Canonical,
            LBOneFactoryPressStarterIds::PressTrain());
    if (TestNotNull(TEXT("Canonical Press train responsibility exists"),
        CanonicalPress))
    {
        TestEqual(TEXT("Starter initially produces the visible hood programme"),
            CanonicalPress->PanelTypeId, FName(TEXT("HOOD_PANEL")));
    }
    TestFalse(TEXT("Starter definition contains no WIP"),
        Canonical.Stations.ContainsByPredicate([](
            const FLBOneFactoryPressStarterStationState& Station)
        { return !Station.ActiveOrReservedUnitIds.IsEmpty(); }));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPressStarterAtomicRestoreTest,
    "LineBoss.OneFactory.PressStarter.AtomicProgrammeCaptureRestoreAndWIPGate",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPressStarterAtomicRestoreTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPressStarterAtomicRestoreTest"));
    ALBOneFactoryPressStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryPressStarterLayoutAuthority>() : nullptr;
    if (!TestNotNull(TEXT("Press starter authority spawns"), Authority))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    TestTrue(TEXT("Authority carries stable native-only identity"),
        Authority->ActorHasTag(
            ALBOneFactoryPressStarterLayoutAuthority::GetAuthorityTag())
        && Authority->ActorHasTag(
            ALBOneFactoryPressStarterLayoutAuthority::GetNativeOnlyTag()));
    TestFalse(TEXT("Authority never ticks"),
        Authority->PrimaryActorTick.bCanEverTick);

    FString Reason;
    const FLBOneFactoryPressStarterLayoutState Original =
        Authority->CaptureLayout();
    TestTrue(TEXT("Press station accepts a different approved job"),
        Authority->SetStationPanelProgramme(
            LBOneFactoryPressStarterIds::PressTrain(),
            TEXT("ROOF_PANEL"), Reason));
    const FLBOneFactoryPressStarterLayoutState RoofProgramme =
        Authority->CaptureLayout();
    TestEqual(TEXT("Atomic programme change increments one revision"),
        RoofProgramme.Revision, Original.Revision + 1);
    int32 MatchingRecipeStations = 0;
    for (const FLBOneFactoryPressStarterStationState& Station :
        RoofProgramme.Stations)
    {
        if (!Station.PanelTypeId.IsNone())
        {
            ++MatchingRecipeStations;
            TestEqual(TEXT("Every recipe-bound station changed together"),
                Station.PanelTypeId, FName(TEXT("ROOF_PANEL")));
            TestEqual(TEXT("Every recipe-bound die changed together"),
                Station.DieId, FName(TEXT("DIE_ROOF_PANEL_V1")));
        }
    }
    TestEqual(TEXT("Five responsibilities share the selected programme"),
        MatchingRecipeStations, 5);

    FLBOneFactoryPressStarterLayoutState Invalid = RoofProgramme;
    Invalid.Stations[1].StationId = Invalid.Stations[0].StationId;
    TestFalse(TEXT("Duplicate station identity rejects restore"),
        Authority->RestoreLayout(Invalid, Reason));
    TestTrue(TEXT("Rejected restore leaves the full captured state unchanged"),
        LBOneFactoryPressStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), RoofProgramme));
    TestFalse(TEXT("Unknown panel programme rejects without mutation"),
        Authority->SetStationPanelProgramme(
            LBOneFactoryPressStarterIds::PressTrain(),
            TEXT("UNKNOWN_PANEL"), Reason));
    TestTrue(TEXT("Rejected panel job leaves the full state unchanged"),
        LBOneFactoryPressStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), RoofProgramme));

    TestTrue(TEXT("Exact original capture restores atomically"),
        Authority->RestoreLayout(Original, Reason));
    TestTrue(TEXT("Exact capture/restore round trip is lossless"),
        LBOneFactoryPressStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Original));

    FLBOneFactoryPressStarterLayoutState WithWIP = Original;
    FLBOneFactoryPressStarterStationState* Press =
        LBOneFactoryPressStarterTestsPrivate::FindStation(WithWIP,
            LBOneFactoryPressStarterIds::PressTrain());
    if (TestNotNull(TEXT("Press train record exists"), Press))
        Press->ActiveOrReservedUnitIds.Add(TEXT("BLANK-RESERVATION-001"));
    TestTrue(TEXT("A coherent active-WIP snapshot restores"),
        Authority->RestoreLayout(WithWIP, Reason));
    const FLBOneFactoryPressStarterLayoutState BeforeBlockedChange =
        Authority->CaptureLayout();
    TestFalse(TEXT("Active or reserved WIP blocks a programme change"),
        Authority->SetStationPanelProgramme(
            LBOneFactoryPressStarterIds::BlankPreparation(),
            TEXT("TAILGATE_PANEL"), Reason));
    TestTrue(TEXT("WIP-rejected change is transactionally unchanged"),
        LBOneFactoryPressStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), BeforeBlockedChange));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPressStarterMoveRollbackTest,
    "LineBoss.OneFactory.PressStarter.TransactionalMovePreservesGraphAndRollsBack",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPressStarterMoveRollbackTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPressStarterMoveRollbackTest"));
    ALBOneFactoryPressStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryPressStarterLayoutAuthority>() : nullptr;
    if (!TestNotNull(TEXT("Move fixture authority exists"), Authority))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    const FLBOneFactoryPressStarterLayoutState Before =
        Authority->CaptureLayout();
    FLBOneFactoryPressStarterLayoutState Proposed = Before;
    FLBOneFactoryPressStarterStationState* Inspection =
        LBOneFactoryPressStarterTestsPrivate::FindStation(Proposed,
            LBOneFactoryPressStarterIds::PanelInspection());
    if (!TestNotNull(TEXT("Inspection station exists"), Inspection))
    {
        World->DestroyWorld(false);
        return false;
    }
    FTransform SmallMove = Inspection->WorldTransform;
    SmallMove.AddToTranslation(FVector(100.0f, 0.0f, 0.0f));
    TestTrue(TEXT("Idle station can move inside its bay and route reach"),
        Authority->MoveStation(
            LBOneFactoryPressStarterIds::PanelInspection(), SmallMove, Reason));
    const FLBOneFactoryPressStarterLayoutState AfterMove =
        Authority->CaptureLayout();
    TestEqual(TEXT("Successful move increments one revision"),
        AfterMove.Revision, Before.Revision + 1);
    TestEqual(TEXT("Successful move preserves all six route identities"),
        AfterMove.Connections.Num(), Before.Connections.Num());
    for (int32 Index = 0; Index < Before.Connections.Num(); ++Index)
        TestTrue(TEXT("Exact material graph survived the move"),
            LBOneFactoryPressStarterTestsPrivate::SameConnection(
                AfterMove.Connections[Index], Before.Connections[Index]));

    FTransform Outside = SmallMove;
    Outside.SetLocation(FVector(5000.0f, 12000.0f, 0.0f));
    TestFalse(TEXT("Move outside the Press bay fails"),
        Authority->MoveStation(
            LBOneFactoryPressStarterIds::PanelInspection(), Outside, Reason));
    TestTrue(TEXT("Out-of-bay move rolls back the entire state"),
        LBOneFactoryPressStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), AfterMove));

    const FLBOneFactoryPressStarterStationState* Dispatch =
        AfterMove.Stations.FindByPredicate([](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.StationId ==
                LBOneFactoryPressStarterIds::PanelDispatch();
        });
    if (TestNotNull(TEXT("Dispatch station exists"), Dispatch))
    {
        TestFalse(TEXT("Overlapping another station fails"),
            Authority->MoveStation(
                LBOneFactoryPressStarterIds::PanelInspection(),
                Dispatch->WorldTransform, Reason));
        TestTrue(TEXT("Overlap rejection rolls back the entire state"),
            LBOneFactoryPressStarterTestsPrivate::SameState(
                Authority->CaptureLayout(), AfterMove));
    }

    TestTrue(TEXT("Idle complete layout commissions"),
        Authority->Commission(Reason));
    TestTrue(TEXT("Commissioning flips the explicit gate"),
        Authority->IsCommissioned());
    const FLBOneFactoryPressStarterLayoutState Commissioned =
        Authority->CaptureLayout();
    TestTrue(TEXT("Repeated commission is idempotent"),
        Authority->Commission(Reason));
    TestTrue(TEXT("Repeated commission does not increment revision"),
        LBOneFactoryPressStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Commissioned));

    World->DestroyWorld(false);
    return true;
}

#endif
