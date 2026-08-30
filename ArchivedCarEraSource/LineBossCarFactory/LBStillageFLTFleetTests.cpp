#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBBodyWeldLineActor.h"
#include "LBCompactStillageFLT.h"
#include "LBMachineLiveryComponent.h"
#include "LBPressShopStorageZone.h"
#include "LBStatusBeaconComponent.h"
#include "LBStillageFLTFleetController.h"

#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Components/SpotLightComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStillageFLTStarterPurchaseContractTest,
    "LineBoss.WeldShop.StillageFLT.StarterPurchaseAndLivery",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStillageFLTExactOnceNaturalFlowTest,
    "LineBoss.WeldShop.StillageFLT.ExactOnceNaturalFullAndEmptyFlow",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStillageFLTFleetSaveRestoreTest,
    "LineBoss.WeldShop.StillageFLT.FleetSaveRestore",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStillageFLTTriplexStackingContractTest,
    "LineBoss.WeldShop.StillageFLT.TriplexThreeHighStackingContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStillageFLTBodyWeldAuthorityEnvelopeTest,
    "LineBoss.WeldShop.StillageFLT.BodyWeldStableAuthorityAndEnvelope",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStillageFLTAutomaticThreeHighParityTest,
    "LineBoss.WeldShop.StillageFLT.AutomaticThreeHighFullEmptyParity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStillageFLTAutomaticStackCapacityAndReservationTest,
    "LineBoss.WeldShop.StillageFLT.AutomaticStackCapacityAndReservationIntegrity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStillageFLTAutomaticAllReservationsCapacityTest,
    "LineBoss.WeldShop.StillageFLT.AutomaticAll48ReservationsFailClosed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBStillageFLTAutomaticStackRestartTest,
    "LineBoss.WeldShop.StillageFLT.AutomaticStackRestartAndNoTeleport",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    UWorld* MakeWorld(const FName Name)
    {
        UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, Name);
        if (!World) return nullptr;
        FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        World->InitializeActorsForPlay(FURL());
        World->BeginPlay();
        return World;
    }

    void DestroyWorld(UWorld* World)
    {
        if (!World) return;
        World->DestroyWorld(false);
        GEngine->DestroyWorldContext(World);
    }

    bool TickUntilJobTerminal(ALBStillageFLTFleetController* Fleet,
        const FName JobId, const int32 MaximumSteps = 4000)
    {
        for (int32 Step = 0; Fleet && Step < MaximumSteps; ++Step)
        {
            Fleet->Tick(0.05f);
            for (int32 UnitIndex = 1; UnitIndex <= Fleet->GetFleetSize(); ++UnitIndex)
            {
                const FName UnitId(*FString::Printf(TEXT("LB-FLT-AGV-%02d"), UnitIndex));
                if (ALBCompactStillageFLT* Unit = Fleet->GetUnitById(UnitId))
                {
                    Unit->Tick(0.05f);
                }
            }
            FLBStillageFLTJob Job;
            if (Fleet->GetJobSnapshot(JobId, Job)
                && (Job.State == ELBStillageFLTJobState::Completed
                    || Job.State == ELBStillageFLTJobState::Failed))
            {
                return Job.State == ELBStillageFLTJobState::Completed;
            }
        }
        return false;
    }

    bool IsFleetTestTravelPhase(const ELBCompactStillageFLTPhase Phase)
    {
        return Phase == ELBCompactStillageFLTPhase::TravelToPickup
            || Phase == ELBCompactStillageFLTPhase::TravelToDropoff
            || Phase == ELBCompactStillageFLTPhase::ReturningToBerth;
    }

    bool ConfigureThreeHighStillageStore(ALBPressShopStorageZone* Store,
        const FName ZoneId, const ELBPressShopStorageType StorageType)
    {
        return Store
            && ALBPressShopStorageZone::IsPanelStillageStorageType(StorageType)
            && Store->Configure(ZoneId, StorageType, 48,
                FVector(550.0f, 550.0f,
                    ALBPressShopStorageZone::PanelStillageMinimumZoneHalfHeightCm))
            && Store->ConfigureStacking(
                ALBPressShopStorageZone::PanelStillageMaximumStackLevels,
                ALBPressShopStorageZone::PanelStillageStackPitchCm)
            && Store->ConfigureLayout(4, 4, FVector2D(250.0f, 250.0f), 50.0f);
    }

    bool SeedIdentifiedStillages(ALBPressShopStorageZone* Store,
        const FString& Prefix, const int32 Count)
    {
        for (int32 Index = 0; Store && Index < Count; ++Index)
        {
            if (!Store->TryStoreIdentifiedUnit(FName(*FString::Printf(
                    TEXT("%s-%03d"), *Prefix, Index + 1))))
            {
                return false;
            }
        }
        return Store && Store->GetOccupancy() == Count;
    }

    bool MarkSavedJobPending(FLBStillageFLTFleetSaveState& State,
        const FName JobId)
    {
        FLBStillageFLTJob* Job = State.Jobs.FindByPredicate(
            [JobId](const FLBStillageFLTJob& Candidate)
            { return Candidate.JobId == JobId; });
        if (!Job) return false;
        if (Job->State == ELBStillageFLTJobState::Pending
            && Job->ClaimedUnitId.IsNone())
        {
            return true;
        }
        if (Job->ClaimedUnitId.IsNone()) return false;
        FLBCompactStillageFLTSaveState* Unit = State.Units.FindByPredicate(
            [Job](const FLBCompactStillageFLTSaveState& Candidate)
            { return Candidate.UnitId == Job->ClaimedUnitId; });
        if (!Unit) return false;
        Job->State = ELBStillageFLTJobState::Pending;
        Job->ClaimedUnitId = NAME_None;
        Unit->Phase = ELBCompactStillageFLTPhase::Parked;
        Unit->Fault = ELBCompactStillageFLTFault::None;
        Unit->ActiveJobId = NAME_None;
        Unit->VehicleTransform.SetLocation(Unit->HomeBerth);
        Unit->CurrentSpeedCmPerSecond = 0.0f;
        Unit->CarriageLiftCm = 3.0f;
        Unit->RearSteerAngleDegrees = 0.0f;
        Unit->bCarryingStillage = false;
        Unit->bCarriedStillageFull = false;
        Unit->CarriedStillageId = NAME_None;
        Unit->bDeliveryEventEmitted = false;
        return true;
    }
}

bool FLBStillageFLTStarterPurchaseContractTest::RunTest(const FString& Parameters)
{
    UWorld* World = MakeWorld(TEXT("LB_StillageFLT_StarterPurchase"));
    TestNotNull(TEXT("Transient runtime world created"), World);
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>() : nullptr;
    TestNotNull(TEXT("Stillage FLT fleet controller spawns"), Fleet);
    TestTrue(TEXT("Fresh fleet follows the same explicit GameMode initialisation seam"),
        Fleet && Fleet->InitialiseFreshFleet());
    TestEqual(TEXT("Fresh weld start has exactly one included FLT"),
        Fleet ? Fleet->GetFleetSize() : 0, 1);
    TestEqual(TEXT("Starter entitlement is fixed at one"),
        Fleet ? Fleet->GetStarterEntitlementCount() : 0, 1);

    ALBCompactStillageFLT* Starter = Fleet
        ? Fleet->GetUnitById(TEXT("LB-FLT-AGV-01")) : nullptr;
    TestNotNull(TEXT("Starter receives deterministic identity"), Starter);
    TestEqual(TEXT("Only explicit body/frame fallback slots receive player livery"),
        Starter && Starter->GetMachineLiveryComponent()
            ? Starter->GetMachineLiveryComponent()->GetMaterialBindingCount() : -1, 2);
    TestTrue(TEXT("Parked starter has a live amber status beacon"), Starter
        && Starter->GetStatusBeacon()
        && Starter->GetStatusBeacon()->GetStatus() == ELBStatusBeaconState::Idle
        && Starter->GetStatusBeacon()->IsAmberLampLit());

    int32 Funds = Fleet ? Fleet->GetAdditionalFLTPurchaseCost() - 1 : 0;
    TestFalse(TEXT("Insufficient funds cannot create a free second FLT"),
        Fleet && Fleet->TryPurchaseAdditionalFLT(Funds));
    TestEqual(TEXT("Rejected purchase preserves the one-unit fleet"),
        Fleet ? Fleet->GetFleetSize() : 0, 1);
    const int32 Price = Fleet ? Fleet->GetAdditionalFLTPurchaseCost() : 0;
    Funds = Price;
    TestTrue(TEXT("Player can buy the second FLT when throughput is insufficient"),
        Fleet && Fleet->TryPurchaseAdditionalFLT(Funds));
    TestEqual(TEXT("Successful purchase deducts the exact price"), Funds, 0);
    TestEqual(TEXT("Successful purchase adds exactly one unit"),
        Fleet ? Fleet->GetFleetSize() : 0, 2);
    TestNotNull(TEXT("Purchased unit has a distinct deterministic identity"),
        Fleet ? Fleet->GetUnitById(TEXT("LB-FLT-AGV-02")) : nullptr);

    ALBPressShopStorageZone* FullStore = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(650.0f, -1200.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    // The two protected envelopes plus the loaded rear-steer swept stand-offs
    // must leave at least the fleet authority's certified 650 cm service lane.
    ALBPressShopStorageZone* WeldIntake = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(2550.0f, -1200.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("Full WIP storage configures"), FullStore && FullStore->Configure(
        TEXT("PRESS-FULL-WIP-A"), ELBPressShopStorageType::FinishedPanelStillages,
        4, FVector(220.0f, 260.0f, 100.0f)));
    TestTrue(TEXT("Weld intake storage configures"), WeldIntake && WeldIntake->Configure(
        TEXT("WELD-STILLAGE-INTAKE-A"), ELBPressShopStorageType::MaintenanceParts,
        4, FVector(220.0f, 260.0f, 100.0f)));
    TestTrue(TEXT("Full store owns the exact stillage before dispatch"),
        FullStore && FullStore->TryStoreIdentifiedUnit(TEXT("WIP-STL-AUTH-0001")));
    FName ActorJobId;
    TestTrue(TEXT("Actor-based enqueue derives safe service points without inventing an ID"),
        Fleet && Fleet->EnqueueFullStillageTransfer(TEXT("WIP-STL-AUTH-0001"),
            FullStore, WeldIntake, FVector2D(85.0f, 155.0f), ActorJobId));
    TestTrue(TEXT("Enqueue does not withdraw source inventory before physical delivery"),
        FullStore && FullStore->ContainsIdentifiedUnit(TEXT("WIP-STL-AUTH-0001")));
    FLBStillageFLTJob ActorJob;
    TestTrue(TEXT("Actor job remains traceable"),
        Fleet && Fleet->GetJobSnapshot(ActorJobId, ActorJob));
    TestEqual(TEXT("Actor job records exact source authority"),
        ActorJob.SourceAuthorityId, FName(TEXT("PRESS-FULL-WIP-A")));
    TestEqual(TEXT("Actor job records exact target authority"),
        ActorJob.TargetAuthorityId, FName(TEXT("WELD-STILLAGE-INTAKE-A")));
    TestTrue(TEXT("Actor-derived locator points retain the certified 650 cm service lane"),
        FVector::Dist2D(ActorJob.PickupServicePoint, ActorJob.DropoffServicePoint)
            >= 650.0f);
    TestEqual(TEXT("Non-storage weld intake remains an explicit floor-tier placement"),
        ActorJob.TargetStackTier, 1);
    TestFalse(TEXT("Compatibility enqueue records a concrete target pad locator"),
        ActorJob.TargetStackPadId.IsNone());

    DestroyWorld(World);
    return true;
}

bool FLBStillageFLTTriplexStackingContractTest::RunTest(const FString& Parameters)
{
    UWorld* World = MakeWorld(TEXT("LB_StillageFLT_TriplexStacking"));
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>() : nullptr;
    TestTrue(TEXT("Fresh triplex fleet initialises"), Fleet && Fleet->InitialiseFreshFleet());
    ALBCompactStillageFLT* Unit = Fleet
        ? Fleet->GetUnitById(TEXT("LB-FLT-AGV-01")) : nullptr;
    TestNotNull(TEXT("Starter triplex FLT exists"), Unit);
    TestEqual(TEXT("Empty and full stillages share the three-high limit"),
        Unit ? Unit->GetMaximumStackTier() : 0, 3);
    TestEqual(TEXT("FLT carries one stillage at a time"),
        Unit ? Unit->GetCarryingCapacityStillages() : 0, 1);
    TestTrue(TEXT("Tier one is the floor fork-entry height"), Unit
        && FMath::IsNearlyEqual(Unit->GetForkPlacementHeightForTier(1), 3.0f, 0.1f));
    TestTrue(TEXT("Tier two target is approximately 1.50 metres"), Unit
        && FMath::IsNearlyEqual(Unit->GetForkPlacementHeightForTier(2), 150.0f, 0.1f));
    TestTrue(TEXT("Tier three target is approximately 2.90 metres"), Unit
        && FMath::IsNearlyEqual(Unit->GetForkPlacementHeightForTier(3), 290.0f, 0.1f)
        && Unit->CanReachStackTier(3));

    FName RejectedJobId;
    TestFalse(TEXT("Full stillage tier four is rejected"), Fleet
        && Fleet->EnqueueExactJobToStackTier(TEXT("STACK-FULL-INVALID"),
            ELBStillageFLTJobType::FullStillageToWeld,
            TEXT("STACK-PRESS"), TEXT("STACK-WELD"),
            FVector(500.0f, 0.0f, 0.0f), FVector(1400.0f, 0.0f, 0.0f),
            4, TEXT("WELD-PAD-A"), 0.0f, FVector2D(85.0f, 155.0f), RejectedJobId));
    TestFalse(TEXT("Empty stillage tier four is rejected by the same limit"), Fleet
        && Fleet->EnqueueExactJobToStackTier(TEXT("STACK-EMPTY-INVALID"),
            ELBStillageFLTJobType::EmptyStillageToPress,
            TEXT("STACK-WELD"), TEXT("STACK-PRESS"),
            FVector(1400.0f, 0.0f, 0.0f), FVector(500.0f, 0.0f, 0.0f),
            4, TEXT("PRESS-PAD-A"), 180.0f, FVector2D(85.0f, 155.0f), RejectedJobId));
    TestFalse(TEXT("A stacked job without a pad/corner-locator identity is rejected"), Fleet
        && Fleet->EnqueueExactJobToStackTier(TEXT("STACK-NO-PAD"),
            ELBStillageFLTJobType::FullStillageToWeld,
            TEXT("STACK-PRESS"), TEXT("STACK-WELD"),
            FVector(500.0f, 0.0f, 0.0f), FVector(1400.0f, 0.0f, 0.0f),
            3, NAME_None, 0.0f, FVector2D(85.0f, 155.0f), RejectedJobId));

    FName TierThreeJobId;
    TestTrue(TEXT("Full stillage accepts a tier-three authored stacking pad"), Fleet
        && Fleet->EnqueueExactJobToStackTier(TEXT("STACK-FULL-003"),
            ELBStillageFLTJobType::FullStillageToWeld,
            TEXT("STACK-PRESS"), TEXT("STACK-WELD"),
            FVector(500.0f, 0.0f, 0.0f), FVector(1400.0f, 0.0f, 0.0f),
            3, TEXT("WELD-PAD-A"), 0.0f, FVector2D(85.0f, 155.0f), TierThreeJobId));

    bool bObservedLocatorProve = false;
    bool bObservedRaisedTravel = false;
    float MaximumLiftCm = 0.0f;
    float MaximumFirstStageExtensionCm = 0.0f;
    float MaximumSecondStageExtensionCm = 0.0f;
    float MaximumFreeCarriageZCm = 0.0f;
    for (int32 Step = 0; Fleet && Unit && Step < 6000; ++Step)
    {
        Fleet->Tick(0.05f);
        Unit->Tick(0.05f);
        MaximumLiftCm = FMath::Max(MaximumLiftCm, Unit->GetCarriageLiftCm());
        if (Unit->GetInnerMastMover())
        {
            MaximumFirstStageExtensionCm = FMath::Max(MaximumFirstStageExtensionCm,
                Unit->GetInnerMastMover()->GetRelativeLocation().Z);
        }
        if (Unit->GetSecondMastMover())
        {
            MaximumSecondStageExtensionCm = FMath::Max(MaximumSecondStageExtensionCm,
                Unit->GetSecondMastMover()->GetRelativeLocation().Z);
        }
        if (Unit->GetCarriageMover())
        {
            MaximumFreeCarriageZCm = FMath::Max(MaximumFreeCarriageZCm,
                Unit->GetCarriageMover()->GetRelativeLocation().Z);
        }
        if (IsFleetTestTravelPhase(Unit->GetPhase())
            && Unit->GetCarriageLiftCm() > Unit->GetTransportLiftHeightCm() + 0.05f)
        {
            bObservedRaisedTravel = true;
        }
        if (Unit->GetPhase() == ELBCompactStillageFLTPhase::StackLocatorProving)
        {
            bObservedLocatorProve |= Unit->IsAlignedWithTargetStackPad();
        }
        FLBStillageFLTJob Snapshot;
        if (Fleet->GetJobSnapshot(TierThreeJobId, Snapshot)
            && (Snapshot.State == ELBStillageFLTJobState::Completed
                || Snapshot.State == ELBStillageFLTJobState::Failed))
        {
            break;
        }
    }
    FLBStillageFLTJob CompletedTierThree;
    TestTrue(TEXT("Tier-three job remains traceable"), Fleet
        && Fleet->GetJobSnapshot(TierThreeJobId, CompletedTierThree));
    TestEqual(TEXT("Tier-three full stillage completes"),
        CompletedTierThree.State, ELBStillageFLTJobState::Completed);
    TestTrue(TEXT("Tier-three lift reaches the 2.90 metre placement target"),
        MaximumLiftCm >= 289.5f);
    TestTrue(TEXT("First nested mast stage extends independently"),
        MaximumFirstStageExtensionCm >= 99.5f);
    TestTrue(TEXT("Second nested mast stage extends independently"),
        MaximumSecondStageExtensionCm >= 99.5f);
    TestTrue(TEXT("Finite free-lift carriage supplies the third motion component"),
        MaximumFreeCarriageZCm >= 117.5f);
    TestTrue(TEXT("Four-corner pad alignment is proven before release"),
        bObservedLocatorProve);
    TestFalse(TEXT("Route travel is prohibited above low transport height"),
        bObservedRaisedTravel);

    FName EmptyTierThreeJobId;
    TestTrue(TEXT("Empty stillage also accepts the same tier-three contract"), Fleet
        && Fleet->EnqueueExactJobToStackTier(TEXT("STACK-EMPTY-003"),
            ELBStillageFLTJobType::EmptyStillageToPress,
            TEXT("STACK-WELD"), TEXT("STACK-PRESS"),
            FVector(1400.0f, 0.0f, 0.0f), FVector(500.0f, 0.0f, 0.0f),
            3, TEXT("PRESS-PAD-A"), 180.0f, FVector2D(85.0f, 155.0f),
            EmptyTierThreeJobId));
    FLBStillageFLTJob EmptyTierThree;
    TestTrue(TEXT("Empty tier-three job persists the requested tier and pad"), Fleet
        && Fleet->GetJobSnapshot(EmptyTierThreeJobId, EmptyTierThree)
        && EmptyTierThree.TargetStackTier == 3
        && EmptyTierThree.TargetStackPadId == FName(TEXT("PRESS-PAD-A")));

    DestroyWorld(World);
    return true;
}

bool FLBStillageFLTExactOnceNaturalFlowTest::RunTest(const FString& Parameters)
{
    UWorld* World = MakeWorld(TEXT("LB_StillageFLT_ExactOnceFlow"));
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>() : nullptr;
    TestTrue(TEXT("Fresh material-flow fleet initialises"),
        Fleet && Fleet->InitialiseFreshFleet());
    ALBCompactStillageFLT* Unit = Fleet
        ? Fleet->GetUnitById(TEXT("LB-FLT-AGV-01")) : nullptr;
    TestNotNull(TEXT("Starter FLT exists"), Unit);

    FName FullJobId;
    TestTrue(TEXT("Exact full stillage queues from press WIP to weld intake"), Fleet
        && Fleet->EnqueueExactJob(TEXT("WIP-STL-2040-000001"),
            ELBStillageFLTJobType::FullStillageToWeld,
            TEXT("PRESS-FULL-WIP"), TEXT("WELD-STILLAGE-INTAKE"),
            FVector(600.0f, 0.0f, 0.0f), FVector(1450.0f, 650.0f, 0.0f),
            FVector2D(85.0f, 155.0f), FullJobId));
    TestTrue(TEXT("First job is outstanding for the exact physical stillage"),
        Fleet && Fleet->HasOutstandingJobForStillage(TEXT("WIP-STL-2040-000001")));
    FName DuplicateJobId;
    TestFalse(TEXT("Same physical stillage cannot receive a second outstanding claim"),
        Fleet && Fleet->EnqueueExactJob(TEXT("WIP-STL-2040-000001"),
            ELBStillageFLTJobType::FullStillageToWeld,
            TEXT("PRESS-FULL-WIP"), TEXT("WELD-STILLAGE-INTAKE"),
            FVector(600.0f, 0.0f, 0.0f), FVector(1450.0f, 650.0f, 0.0f),
            FVector2D(85.0f, 155.0f), DuplicateJobId));
    TestEqual(TEXT("One starter claims exactly one job"),
        Fleet ? Fleet->GetActiveJobCount() : 0, 1);
    TestTrue(TEXT("Moving FLT flashes its amber beacon"), Unit
        && Unit->GetStatusBeacon()
        && Unit->GetStatusBeacon()->GetStatus() == ELBStatusBeaconState::Moving
        && Unit->GetStatusBeacon()->IsFlashing());
    TestTrue(TEXT("Both real mast work lights operate during the mission"), Unit
        && Unit->GetLeftMastWorkLight() && Unit->GetLeftMastWorkLight()->IsVisible()
        && Unit->GetLeftMastWorkLight()->Intensity > 0.0f
        && Unit->GetRightMastWorkLight() && Unit->GetRightMastWorkLight()->IsVisible()
        && Unit->GetRightMastWorkLight()->Intensity > 0.0f);
    TestTrue(TEXT("Rear-steer tail and fork sweep are included in the collision envelope"),
        Unit && Unit->GetOutwardSweepAllowanceCm() > 40.0f
        && Unit->GetCollisionRoot()->GetUnscaledBoxExtent().Y
            >= 42.0f + Unit->GetOutwardSweepAllowanceCm() - 0.1f);
    TestTrue(TEXT("Reverse travel reverses the rear-wheel command for the same body yaw"),
        Unit && Unit->CalculateRearSteerAngleDegrees(100.0f, 20.0f)
            * Unit->CalculateRearSteerAngleDegrees(-100.0f, 20.0f) < 0.0f);

    bool bObservedCarrying = false;
    bool bObservedRaisedCarriage = false;
    bool bObservedRearSteering = false;
    bool bFrontWheelsStayedFixed = true;
    float MaximumYawStep = 0.0f;
    float MaximumAccelerationStep = 0.0f;
    float MaximumDecelerationStep = 0.0f;
    float MaximumTranslationStepCm = 0.0f;
    float PreviousYaw = Unit ? Unit->GetActorRotation().Yaw : 0.0f;
    float PreviousSpeed = Unit ? Unit->GetCurrentSpeedMetresPerSecond() : 0.0f;
    FVector PreviousLocation = Unit ? Unit->GetActorLocation() : FVector::ZeroVector;
    for (int32 Step = 0; Fleet && Unit && Step < 4000; ++Step)
    {
        Fleet->Tick(0.05f);
        Unit->Tick(0.05f);
        bObservedCarrying |= Unit->IsCarryingFullStillage();
        bObservedRaisedCarriage |= Unit->GetCarriageLiftCm() >= 11.5f;
        bObservedRearSteering |= FMath::Abs(Unit->GetRearSteerAngleDegrees()) > 1.0f;
        bFrontWheelsStayedFixed &= FMath::IsNearlyZero(
            Unit->GetFrontWheelSteerAngleDegrees(), KINDA_SMALL_NUMBER);
        const float Yaw = Unit->GetActorRotation().Yaw;
        const float Speed = Unit->GetCurrentSpeedMetresPerSecond();
        MaximumYawStep = FMath::Max(MaximumYawStep,
            FMath::Abs(FMath::FindDeltaAngleDegrees(PreviousYaw, Yaw)));
        MaximumAccelerationStep = FMath::Max(MaximumAccelerationStep, Speed - PreviousSpeed);
        MaximumDecelerationStep = FMath::Max(MaximumDecelerationStep, PreviousSpeed - Speed);
        MaximumTranslationStepCm = FMath::Max(MaximumTranslationStepCm,
            FVector::Dist2D(PreviousLocation, Unit->GetActorLocation()));
        PreviousYaw = Yaw;
        PreviousSpeed = Speed;
        PreviousLocation = Unit->GetActorLocation();
        FLBStillageFLTJob Job;
        if (Fleet->GetJobSnapshot(FullJobId, Job)
            && Job.State == ELBStillageFLTJobState::Completed)
        {
            break;
        }
    }
    FLBStillageFLTJob CompletedFull;
    TestTrue(TEXT("Full transfer remains traceable"),
        Fleet && Fleet->GetJobSnapshot(FullJobId, CompletedFull));
    TestEqual(TEXT("Full transfer completes exactly once"),
        CompletedFull.State, ELBStillageFLTJobState::Completed);
    TestTrue(TEXT("FLT physically carries the full stillage"), bObservedCarrying);
    TestTrue(TEXT("Approved modular carriage lifts during pickup"), bObservedRaisedCarriage);
    TestTrue(TEXT("Rear steering pivot visibly turns through the curved mission"),
        bObservedRearSteering && Unit && Unit->GetRearSteeringPivot());
    TestTrue(TEXT("Front drive wheels remain fixed while the rear axle steers"),
        bFrontWheelsStayedFixed);
    TestTrue(TEXT("Steering is rate limited instead of a 90-degree snap"), MaximumYawStep <= 2.76f);
    TestTrue(TEXT("Acceleration is smooth"), MaximumAccelerationStep <= 0.046f);
    TestTrue(TEXT("Deceleration is smooth"), MaximumDecelerationStep <= 0.069f);
    TestTrue(TEXT("No travel tick teleports the FLT"), MaximumTranslationStepCm <= 8.6f);
    TestTrue(TEXT("Completed FLT returns parked and available"), Unit && Unit->IsAvailableForJob());

    FName EmptyJobId;
    TestTrue(TEXT("The same exact ID may return only after its full job is terminal"), Fleet
        && Fleet->EnqueueExactJob(TEXT("WIP-STL-2040-000001"),
            ELBStillageFLTJobType::EmptyStillageToPress,
            TEXT("WELD-EMPTY-STILLAGES"), TEXT("PRESS-EMPTY-STILLAGES"),
            FVector(1450.0f, 650.0f, 0.0f), FVector(600.0f, 0.0f, 0.0f),
            FVector2D(85.0f, 155.0f), EmptyJobId));
    TestTrue(TEXT("Empty stillage physically returns to press storage"),
        TickUntilJobTerminal(Fleet, EmptyJobId));
    FLBStillageFLTJob CompletedEmpty;
    TestTrue(TEXT("Empty return remains traceable"),
        Fleet && Fleet->GetJobSnapshot(EmptyJobId, CompletedEmpty));
    TestEqual(TEXT("Empty return completes"),
        CompletedEmpty.State, ELBStillageFLTJobState::Completed);

    DestroyWorld(World);
    return true;
}

bool FLBStillageFLTFleetSaveRestoreTest::RunTest(const FString& Parameters)
{
    UWorld* World = MakeWorld(TEXT("LB_StillageFLT_SaveRestore"));
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>() : nullptr;
    int32 Funds = Fleet ? Fleet->GetAdditionalFLTPurchaseCost() : 0;
    TestTrue(TEXT("Second FLT purchase succeeds before save"),
        Fleet && Fleet->TryPurchaseAdditionalFLT(Funds));

    FName JobA;
    FName JobB;
    TestTrue(TEXT("First full job queues"), Fleet && Fleet->EnqueueExactJob(
        TEXT("SAVE-STL-001"), ELBStillageFLTJobType::FullStillageToWeld,
        TEXT("SAVE-PRESS-FULL"), TEXT("SAVE-WELD-IN"),
        FVector(800.0f, -300.0f, 0.0f), FVector(1700.0f, -300.0f, 0.0f),
        FVector2D(85.0f, 155.0f), JobA));
    TestTrue(TEXT("Second full job queues and uses purchased capacity"), Fleet
        && Fleet->EnqueueExactJob(TEXT("SAVE-STL-002"),
            ELBStillageFLTJobType::FullStillageToWeld,
            TEXT("SAVE-PRESS-FULL"), TEXT("SAVE-WELD-IN"),
            FVector(800.0f, 300.0f, 0.0f), FVector(1700.0f, 300.0f, 0.0f),
            FVector2D(85.0f, 155.0f), JobB));
    TestEqual(TEXT("Both purchased vehicles claim one unique job"),
        Fleet ? Fleet->GetActiveJobCount() : 0, 2);

    for (int32 Step = 0; Fleet && Step < 25; ++Step)
    {
        Fleet->Tick(0.05f);
        if (ALBCompactStillageFLT* One = Fleet->GetUnitById(TEXT("LB-FLT-AGV-01"))) One->Tick(0.05f);
        if (ALBCompactStillageFLT* Two = Fleet->GetUnitById(TEXT("LB-FLT-AGV-02"))) Two->Tick(0.05f);
    }
    FLBStillageFLTFleetSaveState Saved;
    TestTrue(TEXT("In-flight fleet snapshot captures"), Fleet && Fleet->CaptureSaveState(Saved));
    TestEqual(TEXT("Purchased capacity persists in snapshot"), Saved.Units.Num(), 2);
    TestEqual(TEXT("Both exact claims persist in snapshot"), Saved.Jobs.Num(), 2);

    if (Fleet)
    {
        if (ALBCompactStillageFLT* One = Fleet->GetUnitById(TEXT("LB-FLT-AGV-01"))) One->Destroy();
        if (ALBCompactStillageFLT* Two = Fleet->GetUnitById(TEXT("LB-FLT-AGV-02"))) Two->Destroy();
        Fleet->Destroy();
    }
    ALBStillageFLTFleetController* Reloaded = World
        ? World->SpawnActor<ALBStillageFLTFleetController>(
            ALBStillageFLTFleetController::StaticClass(), FVector(0.0f, 2500.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("Validated in-flight fleet restores"),
        Reloaded && Reloaded->RestoreSaveState(Saved));
    TestEqual(TEXT("Restore does not grant an extra starter FLT"),
        Reloaded ? Reloaded->GetFleetSize() : 0, 2);
    TestEqual(TEXT("Restored jobs retain exact-once claims"),
        Reloaded ? Reloaded->GetActiveJobCount() : 0, 2);
    FLBStillageFLTJob RestoredA;
    FLBStillageFLTJob RestoredB;
    TestTrue(TEXT("First exact job restores"), Reloaded
        && Reloaded->GetJobSnapshot(JobA, RestoredA));
    TestTrue(TEXT("Second exact job restores"), Reloaded
        && Reloaded->GetJobSnapshot(JobB, RestoredB));
    TestTrue(TEXT("Restored claims remain on distinct vehicles"),
        !RestoredA.ClaimedUnitId.IsNone() && !RestoredB.ClaimedUnitId.IsNone()
        && RestoredA.ClaimedUnitId != RestoredB.ClaimedUnitId);

    DestroyWorld(World);
    return true;
}

bool FLBStillageFLTBodyWeldAuthorityEnvelopeTest::RunTest(const FString& Parameters)
{
    UWorld* World = MakeWorld(TEXT("LB_StillageFLT_WeldAuthority"));
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>(
            ALBStillageFLTFleetController::StaticClass(), FVector(-6500.0f, 1200.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* Source = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(-5000.0f, 0.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    ALBBodyWeldLineActor* Weld = World
        ? World->SpawnActor<ALBBodyWeldLineActor>(
            ALBBodyWeldLineActor::StaticClass(), FVector(2000.0f, 0.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    const FName StillageId(TEXT("WIP-STL-WELD-AUTH-000001"));
    const FName WeldLineId(TEXT("BODY-WELD-STABLE-LINE-001"));
    TestTrue(TEXT("Physical source, fleet and weld authority configure"), Fleet && Source && Weld
        && Source->Configure(TEXT("PRESS-STAGE9-STABLE-001"),
            ELBPressShopStorageType::FinishedPanelStillages, 4, FVector(200.0f))
        && Source->TryStoreIdentifiedUnit(StillageId)
        && Weld->Configure(WeldLineId));
    if (!Fleet || !Source || !Weld)
    {
        DestroyWorld(World);
        return false;
    }

    FName JobId;
    TestTrue(TEXT("Actor-level route resolves the composite weld protected envelope"),
        Fleet->EnqueueFullStillageTransfer(StillageId, Source, Weld,
            FVector2D(85.0f, 155.0f), JobId));
    FLBStillageFLTJob Job;
    TestTrue(TEXT("Exact route remains inspectable by deterministic job ID"),
        Fleet->GetJobSnapshot(JobId, Job));
    TestEqual(TEXT("Target authority is stable LineId, never transient actor FName"),
        Job.TargetAuthorityId, WeldLineId);
    TestEqual(TEXT("Source authority remains the exact stage-9 storage ID"),
        Job.SourceAuthorityId, Source->GetZoneId());
    TestEqual(TEXT("Physical route retains the exact stillage ID"),
        Job.StillageId, StillageId);
    const UBoxComponent* Envelope = Weld->GetProtectedEnvelope();
    const FVector LocalDrop = Envelope
        ? Envelope->GetComponentTransform().InverseTransformPosition(Job.DropoffServicePoint)
        : FVector::ZeroVector;
    const FVector Extent = Envelope ? Envelope->GetUnscaledBoxExtent() : FVector::ZeroVector;
    TestTrue(TEXT("Drop locator clears the protected weld envelope"), Envelope
        && (FMath::Abs(LocalDrop.X) > Extent.X || FMath::Abs(LocalDrop.Y) > Extent.Y));
    const TArray<FLBStillageFLTJob> Snapshots = Fleet->GetJobSnapshots();
    TestTrue(TEXT("Read-only ledger is deterministic and returns an independent snapshot"),
        Snapshots.Num() == 1 && Snapshots[0].JobId == JobId);

    DestroyWorld(World);
    return true;
}

bool FLBStillageFLTAutomaticThreeHighParityTest::RunTest(const FString& Parameters)
{
    UWorld* World = MakeWorld(TEXT("LB_StillageFLT_AutomaticThreeHighParity"));
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>(
            ALBStillageFLTFleetController::StaticClass(),
            FVector(-7000.0f, 0.0f, 0.0f), FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* FullSource = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(-3000.0f, -1800.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* EmptySource = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(-3000.0f, 1800.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* FullStore = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(3000.0f, -1800.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* EmptyStore = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(3000.0f, 1800.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("Automatic parity fixture configures"), Fleet && FullSource && EmptySource
        && FullSource->Configure(TEXT("AUTO-FULL-SOURCE"),
            ELBPressShopStorageType::FinishedPanelStillages, 4, FVector(200.0f))
        && EmptySource->Configure(TEXT("AUTO-EMPTY-SOURCE"),
            ELBPressShopStorageType::EmptyPanelStillages, 4, FVector(200.0f))
        && FullSource->TryStoreIdentifiedUnit(TEXT("AUTO-FULL-INCOMING"))
        && EmptySource->TryStoreIdentifiedUnit(TEXT("AUTO-EMPTY-INCOMING"))
        && ConfigureThreeHighStillageStore(FullStore, TEXT("AUTO-FULL-STORE"),
            ELBPressShopStorageType::FinishedPanelStillages)
        && ConfigureThreeHighStillageStore(EmptyStore, TEXT("AUTO-EMPTY-STORE"),
            ELBPressShopStorageType::EmptyPanelStillages)
        && SeedIdentifiedStillages(FullStore, TEXT("AUTO-FULL-OCC"), 16)
        && SeedIdentifiedStillages(EmptyStore, TEXT("AUTO-EMPTY-OCC"), 16));

    FName FullJobId;
    FName EmptyJobId;
    TestTrue(TEXT("Automatic full store job selects first free address"), Fleet
        && Fleet->EnqueueFullStillageTransfer(TEXT("AUTO-FULL-INCOMING"),
            FullSource, FullStore, FVector2D(85.0f, 155.0f), FullJobId));
    TestTrue(TEXT("Automatic empty store job selects the same first free address"), Fleet
        && Fleet->EnqueueEmptyStillageReturn(TEXT("AUTO-EMPTY-INCOMING"),
            EmptySource, EmptyStore, FVector2D(85.0f, 155.0f), EmptyJobId));
    FLBStillageFLTJob FullJob;
    FLBStillageFLTJob EmptyJob;
    TestTrue(TEXT("Automatic full/empty jobs remain traceable"), Fleet
        && Fleet->GetJobSnapshot(FullJobId, FullJob)
        && Fleet->GetJobSnapshot(EmptyJobId, EmptyJob));
    TestTrue(TEXT("Both stores progress from sixteen floor bays to tier two"),
        FullJob.TargetStackTier == 2 && EmptyJob.TargetStackTier == 2);
    TestTrue(TEXT("Full and empty stores use the identical deterministic bay ordinal"),
        FullJob.TargetStackPadId == FName(TEXT("AUTO-FULL-STORE-STACK-PAD-001"))
        && EmptyJob.TargetStackPadId == FName(TEXT("AUTO-EMPTY-STORE-STACK-PAD-001")));
    int32 FullAddressIndex = INDEX_NONE;
    int32 EmptyAddressIndex = INDEX_NONE;
    TestTrue(TEXT("Full and empty automatic addresses map to the same tier-major index"),
        FullStore && EmptyStore
        && FullStore->GetStorageIndexForStackAddress(
            FullJob.TargetStackPadId, FullJob.TargetStackTier, FullAddressIndex)
        && EmptyStore->GetStorageIndexForStackAddress(
            EmptyJob.TargetStackPadId, EmptyJob.TargetStackTier, EmptyAddressIndex)
        && FullAddressIndex == 16 && EmptyAddressIndex == 16);
    TestEqual(TEXT("Automatic enqueue does not teleport inventory into the full store"),
        FullStore ? FullStore->GetOccupancy() : -1, 16);
    TestEqual(TEXT("Automatic enqueue does not teleport inventory into the empty store"),
        EmptyStore ? EmptyStore->GetOccupancy() : -1, 16);
    TestFalse(TEXT("Incoming full ID remains physically in transit"),
        FullStore && FullStore->ContainsIdentifiedUnit(TEXT("AUTO-FULL-INCOMING")));
    TestFalse(TEXT("Incoming empty ID remains physically in transit"),
        EmptyStore && EmptyStore->ContainsIdentifiedUnit(TEXT("AUTO-EMPTY-INCOMING")));
    TestTrue(TEXT("Automatic enqueue preserves exact full source ownership"),
        FullSource && FullSource->ContainsIdentifiedUnit(TEXT("AUTO-FULL-INCOMING")));
    TestTrue(TEXT("Automatic enqueue preserves exact empty source ownership"),
        EmptySource && EmptySource->ContainsIdentifiedUnit(TEXT("AUTO-EMPTY-INCOMING")));

    DestroyWorld(World);
    return true;
}

bool FLBStillageFLTAutomaticStackCapacityAndReservationTest::RunTest(
    const FString& Parameters)
{
    UWorld* World = MakeWorld(TEXT("LB_StillageFLT_AutomaticStackCapacity"));
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>(
            ALBStillageFLTFleetController::StaticClass(),
            FVector(-7000.0f, 0.0f, 0.0f), FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* Source = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(-3000.0f, 0.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* Store = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(3000.0f, 0.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("Automatic reservation fixture configures"), Fleet && Source
        && Source->Configure(TEXT("AUTO-RESERVE-SOURCE"),
            ELBPressShopStorageType::EmptyPanelStillages, 4, FVector(200.0f))
        && Source->TryStoreIdentifiedUnit(TEXT("AUTO-RESERVE-A"))
        && Source->TryStoreIdentifiedUnit(TEXT("AUTO-RESERVE-B"))
        && Source->TryStoreIdentifiedUnit(TEXT("AUTO-FULL-49"))
        && ConfigureThreeHighStillageStore(Store, TEXT("AUTO-RESERVE-STORE"),
            ELBPressShopStorageType::EmptyPanelStillages)
        && SeedIdentifiedStillages(Store, TEXT("AUTO-RESERVE-OCC"), 31));

    FName FirstJobId;
    FName SecondJobId;
    TestTrue(TEXT("First automatic reservation selects the final tier-two address"), Fleet
        && Fleet->EnqueueEmptyStillageReturn(TEXT("AUTO-RESERVE-A"), Source, Store,
            FVector2D(85.0f, 155.0f), FirstJobId));
    TestTrue(TEXT("Second automatic reservation advances without duplicating occupancy"), Fleet
        && Fleet->EnqueueEmptyStillageReturn(TEXT("AUTO-RESERVE-B"), Source, Store,
            FVector2D(85.0f, 155.0f), SecondJobId));
    FLBStillageFLTJob FirstJob;
    FLBStillageFLTJob SecondJob;
    TestTrue(TEXT("Reserved jobs have unique first-free addresses"), Fleet
        && Fleet->GetJobSnapshot(FirstJobId, FirstJob)
        && Fleet->GetJobSnapshot(SecondJobId, SecondJob)
        && FirstJob.TargetStackTier == 2
        && FirstJob.TargetStackPadId == FName(TEXT("AUTO-RESERVE-STORE-STACK-PAD-016"))
        && SecondJob.TargetStackTier == 3
        && SecondJob.TargetStackPadId == FName(TEXT("AUTO-RESERVE-STORE-STACK-PAD-001")));
    FName DuplicateAddressJob;
    TestFalse(TEXT("Exact low-level enqueue cannot duplicate a live storage reservation"),
        Fleet && Fleet->EnqueueExactJobToStackTier(TEXT("AUTO-RESERVE-DUP"),
            ELBStillageFLTJobType::EmptyStillageToPress,
            Source->GetZoneId(), Store->GetZoneId(),
            FVector(-3500.0f, 0.0f, 0.0f), FVector(2500.0f, 0.0f, 0.0f),
            FirstJob.TargetStackTier, FirstJob.TargetStackPadId, 0.0f,
            FVector2D(85.0f, 155.0f), DuplicateAddressJob));
    FName ForeignPadJob;
    TestTrue(TEXT("Low-level authored fixture can expose a foreign live storage pad"),
        Fleet && Fleet->EnqueueExactJobToStackTier(TEXT("AUTO-RESERVE-FOREIGN"),
            ELBStillageFLTJobType::EmptyStillageToPress,
            Source->GetZoneId(), Store->GetZoneId(),
            FVector(-3500.0f, 500.0f, 0.0f), FVector(2500.0f, 500.0f, 0.0f),
            3, TEXT("FOREIGN-STACK-PAD-001"), 0.0f,
            FVector2D(85.0f, 155.0f), ForeignPadJob));
    FName RejectedAroundForeignPad;
    TestFalse(TEXT("Automatic resolver fails closed around a foreign live storage pad"),
        Fleet && Fleet->EnqueueEmptyStillageReturn(TEXT("AUTO-FULL-49"), Source, Store,
            FVector2D(85.0f, 155.0f), RejectedAroundForeignPad));
    TestTrue(TEXT("Foreign-reservation rejection creates no automatic job identity"),
        RejectedAroundForeignPad.IsNone());
    TestEqual(TEXT("Reservations do not increase physical storage occupancy"),
        Store ? Store->GetOccupancy() : -1, 31);

    FLBStillageFLTFleetSaveState ValidState;
    TestTrue(TEXT("Reservation ledger captures"), Fleet && Fleet->CaptureSaveState(ValidState));
    FLBStillageFLTFleetSaveState DuplicateState = ValidState;
    TestTrue(TEXT("Reservation corruption fixture safely parks both jobs"),
        MarkSavedJobPending(DuplicateState, FirstJobId)
        && MarkSavedJobPending(DuplicateState, SecondJobId));
    if (DuplicateState.Jobs.Num() >= 2)
    {
        DuplicateState.Jobs[1].TargetStackPadId =
            DuplicateState.Jobs[0].TargetStackPadId;
        DuplicateState.Jobs[1].TargetStackTier =
            DuplicateState.Jobs[0].TargetStackTier;
    }
    ALBStillageFLTFleetController* RejectingFleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>(
            ALBStillageFLTFleetController::StaticClass(),
            FVector(-7000.0f, 3000.0f, 0.0f), FRotator::ZeroRotator) : nullptr;
    TestFalse(TEXT("Restore rejects duplicate outstanding storage addresses"),
        RejectingFleet && RejectingFleet->RestoreSaveState(DuplicateState));

    ALBPressShopStorageZone* FullStore = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(3000.0f, 3500.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("All-48 capacity fixture fills exactly"),
        ConfigureThreeHighStillageStore(FullStore, TEXT("AUTO-FULL-48"),
            ELBPressShopStorageType::FinishedPanelStillages)
        && SeedIdentifiedStillages(FullStore, TEXT("AUTO-FULL-48-OCC"), 48));
    FName RejectedFullJob;
    ALBPressShopStorageZone* FullSource = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(-3000.0f, 3500.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("Full capacity fixture preserves a correctly typed source stillage"),
        FullSource && FullSource->Configure(TEXT("AUTO-FULL-48-SOURCE"),
            ELBPressShopStorageType::FinishedPanelStillages, 4, FVector(200.0f))
        && FullSource->TryStoreIdentifiedUnit(TEXT("AUTO-FULL-49")));
    TestFalse(TEXT("Automatic full-store enqueue fails closed when all 48 are occupied"),
        Fleet && Fleet->EnqueueFullStillageTransfer(TEXT("AUTO-FULL-49"), FullSource, FullStore,
            FVector2D(85.0f, 155.0f), RejectedFullJob));
    TestTrue(TEXT("Capacity rejection creates no job identity"), RejectedFullJob.IsNone());

    DestroyWorld(World);
    return true;
}

bool FLBStillageFLTAutomaticAllReservationsCapacityTest::RunTest(
    const FString& Parameters)
{
    UWorld* World = MakeWorld(TEXT("LB_StillageFLT_AutomaticAllReservations"));
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>(
            ALBStillageFLTFleetController::StaticClass(),
            FVector(-7000.0f, 0.0f, 0.0f), FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* Source = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(-3000.0f, 0.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* Store = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(3000.0f, 0.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("All-reservation fixture configures"), Fleet && Source
        && Source->Configure(TEXT("AUTO-ALL-RESERVE-SOURCE"),
            ELBPressShopStorageType::EmptyPanelStillages, 49, FVector(200.0f))
        && ConfigureThreeHighStillageStore(Store, TEXT("AUTO-ALL-RESERVE-STORE"),
            ELBPressShopStorageType::EmptyPanelStillages));
    int32 ReservedCount = 0;
    for (int32 Index = 0; Fleet && Source && Store && Index < 48; ++Index)
    {
        const FName StillageId(*FString::Printf(TEXT("AUTO-ALL-RESERVE-%03d"), Index + 1));
        if (!Source->TryStoreIdentifiedUnit(StillageId)) break;
        FName JobId;
        if (!Fleet->EnqueueEmptyStillageReturn(StillageId, Source, Store,
                FVector2D(85.0f, 155.0f), JobId)) break;
        ++ReservedCount;
    }
    TestEqual(TEXT("All 48 deterministic storage positions can be reserved once"),
        ReservedCount, 48);
    TestEqual(TEXT("Forty-eight reservations still do not teleport occupancy"),
        Store ? Store->GetOccupancy() : -1, 0);
    if (ReservedCount == 48)
    {
        const TArray<FLBStillageFLTJob> ReservedJobs = Fleet->GetJobSnapshots();
        TestTrue(TEXT("Automatic fill order progresses tier one, tier two, then tier three"),
            ReservedJobs.Num() == 48
            && ReservedJobs[0].TargetStackTier == 1
            && ReservedJobs[0].TargetStackPadId
                == FName(TEXT("AUTO-ALL-RESERVE-STORE-STACK-PAD-001"))
            && ReservedJobs[15].TargetStackTier == 1
            && ReservedJobs[15].TargetStackPadId
                == FName(TEXT("AUTO-ALL-RESERVE-STORE-STACK-PAD-016"))
            && ReservedJobs[16].TargetStackTier == 2
            && ReservedJobs[16].TargetStackPadId
                == FName(TEXT("AUTO-ALL-RESERVE-STORE-STACK-PAD-001"))
            && ReservedJobs[31].TargetStackTier == 2
            && ReservedJobs[31].TargetStackPadId
                == FName(TEXT("AUTO-ALL-RESERVE-STORE-STACK-PAD-016"))
            && ReservedJobs[32].TargetStackTier == 3
            && ReservedJobs[32].TargetStackPadId
                == FName(TEXT("AUTO-ALL-RESERVE-STORE-STACK-PAD-001"))
            && ReservedJobs[47].TargetStackTier == 3
            && ReservedJobs[47].TargetStackPadId
                == FName(TEXT("AUTO-ALL-RESERVE-STORE-STACK-PAD-016")));
        TSet<FString> Addresses;
        bool bAllAddressesValid = ReservedJobs.Num() == 48;
        for (const FLBStillageFLTJob& Job : ReservedJobs)
        {
            int32 AddressIndex = INDEX_NONE;
            bAllAddressesValid &= Store->GetStorageIndexForStackAddress(
                Job.TargetStackPadId, Job.TargetStackTier, AddressIndex)
                && AddressIndex >= 0 && AddressIndex < 48
                && !Addresses.Contains(FString::Printf(TEXT("%s|%d"),
                    *Job.TargetStackPadId.ToString(), Job.TargetStackTier));
            Addresses.Add(FString::Printf(TEXT("%s|%d"),
                *Job.TargetStackPadId.ToString(), Job.TargetStackTier));
        }
        TestTrue(TEXT("Every automatic reservation maps to one unique physical address"),
            bAllAddressesValid && Addresses.Num() == 48);
        TestTrue(TEXT("Overflow source identity stores"), Source
            && Source->TryStoreIdentifiedUnit(TEXT("AUTO-ALL-RESERVE-049")));
        FName OverflowJobId;
        TestFalse(TEXT("Automatic enqueue fails closed when all 48 are reserved"), Fleet
            && Fleet->EnqueueEmptyStillageReturn(TEXT("AUTO-ALL-RESERVE-049"), Source, Store,
                FVector2D(85.0f, 155.0f), OverflowJobId));
        TestTrue(TEXT("Reservation overflow creates no job identity"), OverflowJobId.IsNone());
    }

    DestroyWorld(World);
    return true;
}

bool FLBStillageFLTAutomaticStackRestartTest::RunTest(const FString& Parameters)
{
    UWorld* World = MakeWorld(TEXT("LB_StillageFLT_AutomaticStackRestart"));
    ALBStillageFLTFleetController* Fleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>(
            ALBStillageFLTFleetController::StaticClass(),
            FVector(-7000.0f, 0.0f, 0.0f), FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* Source = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(-3000.0f, 0.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    ALBPressShopStorageZone* Store = World
        ? World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(), FVector(3000.0f, 0.0f, 0.0f),
            FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("Restart fixture configures"), Fleet && Source
        && Source->Configure(TEXT("AUTO-RESTART-SOURCE"),
            ELBPressShopStorageType::EmptyPanelStillages, 4, FVector(200.0f))
        && Source->TryStoreIdentifiedUnit(TEXT("AUTO-RESTART-INCOMING"))
        && Source->TryStoreIdentifiedUnit(TEXT("AUTO-RESTART-NEXT"))
        && ConfigureThreeHighStillageStore(Store, TEXT("AUTO-RESTART-STORE"),
            ELBPressShopStorageType::EmptyPanelStillages)
        && SeedIdentifiedStillages(Store, TEXT("AUTO-RESTART-OCC"), 32));

    const FTransform StoreTransformBefore = Store ? Store->GetActorTransform() : FTransform();
    const FLBPressShopStorageZoneSaveState StoreStateBefore =
        Store ? Store->CaptureSaveState() : FLBPressShopStorageZoneSaveState();
    FName JobId;
    TestTrue(TEXT("Automatic tier-three job queues before restart"), Fleet
        && Fleet->EnqueueEmptyStillageReturn(TEXT("AUTO-RESTART-INCOMING"), Source, Store,
            FVector2D(85.0f, 155.0f), JobId));
    FLBStillageFLTJob BeforeRestart;
    TestTrue(TEXT("Tier-three reservation is exact before restart"), Fleet
        && Fleet->GetJobSnapshot(JobId, BeforeRestart)
        && BeforeRestart.TargetStackTier == 3
        && BeforeRestart.TargetStackPadId
            == FName(TEXT("AUTO-RESTART-STORE-STACK-PAD-001")));
    TestEqual(TEXT("Queued job leaves storage occupancy unchanged"),
        Store ? Store->GetOccupancy() : -1, 32);
    TestTrue(TEXT("Queued job leaves destination transform unchanged"), Store
        && Store->GetActorTransform().Equals(StoreTransformBefore, 0.001f));

    FLBStillageFLTFleetSaveState FleetState;
    TestTrue(TEXT("In-flight tier-three reservation captures"),
        Fleet && Fleet->CaptureSaveState(FleetState));
    TestTrue(TEXT("Restart fixture saves the address as an outstanding pending job"),
        MarkSavedJobPending(FleetState, JobId));
    ALBStillageFLTFleetController* ReloadedFleet = World
        ? World->SpawnActor<ALBStillageFLTFleetController>(
            ALBStillageFLTFleetController::StaticClass(),
            FVector(-7000.0f, 3000.0f, 0.0f), FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("In-flight tier-three reservation restores"),
        ReloadedFleet && ReloadedFleet->RestoreSaveState(FleetState));
    TestTrue(TEXT("Storage authority independently restores the same physical layout"),
        Store && Store->RestoreSaveState(StoreStateBefore));
    FLBStillageFLTJob AfterRestart;
    TestTrue(TEXT("Restart preserves exact pad, tier and stillage IDs"), ReloadedFleet
        && ReloadedFleet->GetJobSnapshot(JobId, AfterRestart)
        && AfterRestart.StillageId == BeforeRestart.StillageId
        && AfterRestart.TargetAuthorityId == BeforeRestart.TargetAuthorityId
        && AfterRestart.TargetStackPadId == BeforeRestart.TargetStackPadId
        && AfterRestart.TargetStackTier == BeforeRestart.TargetStackTier);
    TestEqual(TEXT("Restart leaves saved physical occupancy unchanged"),
        Store ? Store->CaptureSaveState().Occupancy : -1, StoreStateBefore.Occupancy);
    TestTrue(TEXT("Restart does not materialise the in-flight stillage"),
        Store && !Store->ContainsIdentifiedUnit(TEXT("AUTO-RESTART-INCOMING")));

    FName NextJobId;
    TestTrue(TEXT("Restored reservation advances the next automatic address"), ReloadedFleet
        && ReloadedFleet->EnqueueEmptyStillageReturn(TEXT("AUTO-RESTART-NEXT"), Source, Store,
            FVector2D(85.0f, 155.0f), NextJobId));
    FLBStillageFLTJob NextJob;
    TestTrue(TEXT("Post-restart enqueue cannot duplicate the saved address"), ReloadedFleet
        && ReloadedFleet->GetJobSnapshot(NextJobId, NextJob)
        && NextJob.TargetStackTier == 3
        && NextJob.TargetStackPadId
            == FName(TEXT("AUTO-RESTART-STORE-STACK-PAD-002")));

    DestroyWorld(World);
    return true;
}

#endif
