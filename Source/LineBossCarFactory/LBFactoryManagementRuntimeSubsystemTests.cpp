#include "LBFactoryManagementRuntimeSubsystem.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "LBBodyWeldLineActor.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryManagementSubsystem.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBPressTrainAStation.h"
#include "LBVehiclePanelCatalog.h"
#include "Misc/AutomationTest.h"

namespace
{
    struct FLBRuntimeBridgeFixture
    {
        UWorld* World = nullptr;
        ULBFactoryManagementSubsystem* Management = nullptr;
        ULBFactoryManagementRuntimeSubsystem* Bridge = nullptr;
    };

    FLBRuntimeBridgeFixture CreateRuntimeBridgeFixture(const FName WorldName,
        const int64 OpeningCashPence = 1000000)
    {
        FLBRuntimeBridgeFixture Fixture;
        Fixture.World = UWorld::CreateWorld(EWorldType::Game, false, WorldName);
        if (!Fixture.World) return Fixture;
        FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(Fixture.World);
        Fixture.World->InitializeActorsForPlay(FURL());
        Fixture.Management = Fixture.World->GetSubsystem<ULBFactoryManagementSubsystem>();
        Fixture.Bridge = Fixture.World->GetSubsystem<
            ULBFactoryManagementRuntimeSubsystem>();
        if (Fixture.Management)
            Fixture.Management->InitialiseNewCampaign(OpeningCashPence, 0);
        return Fixture;
    }

    void DestroyRuntimeBridgeFixture(FLBRuntimeBridgeFixture& Fixture)
    {
        if (!Fixture.World) return;
        Fixture.World->DestroyWorld(false);
        GEngine->DestroyWorldContext(Fixture.World);
        Fixture.World = nullptr;
    }

    FLBPanelLineageRecord MakeDeliveredPanel(const FName OrderId,
        const FName PanelId, const FName BlankId, const FName StillageId)
    {
        FLBPanelLineageRecord Panel;
        Panel.PanelId = PanelId;
        Panel.BlankId = BlankId;
        Panel.OrderId = OrderId;
        Panel.VehicleModelId = TEXT("CAIRNWELL_2040");
        Panel.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
        Panel.SourceTrainId = TEXT("TRAIN_A");
        Panel.StillageId = StillageId;
        Panel.Disposition = ELBPanelDisposition::Good;
        Panel.Stage = ELBPanelFlowStage::WeldShopIntake;
        return Panel;
    }

    FLBPanelStillageLoad MakeDeliveredStillage(const FName OrderId,
        const FName StillageId, const FName PanelId, const int32 Capacity)
    {
        FLBPanelStillageLoad Load;
        Load.StillageId = StillageId;
        Load.OrderId = OrderId;
        Load.VehicleModelId = TEXT("CAIRNWELL_2040");
        Load.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
        Load.CapacityPanels = Capacity;
        Load.PanelIds.Add(PanelId);
        Load.bReadyForWeld = true;
        Load.bDeliveredToWeld = true;
        return Load;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBManagementRuntimeEvidenceBridgeTest,
    "LineBoss.Management.Runtime.RealStateQualityFaultAndWearBridge",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRuntimeEvidenceBridgeTest::RunTest(const FString& Parameters)
{
    FLBRuntimeBridgeFixture Fixture = CreateRuntimeBridgeFixture(
        TEXT("LB_ManagementRuntimeEvidence"));
    TestNotNull(TEXT("Runtime bridge world exists"), Fixture.World);
    TestNotNull(TEXT("Persistent management authority auto-creates"), Fixture.Management);
    TestNotNull(TEXT("Runtime evidence bridge auto-creates"), Fixture.Bridge);
    if (!Fixture.World || !Fixture.Management || !Fixture.Bridge)
    {
        DestroyRuntimeBridgeFixture(Fixture);
        return false;
    }
    TestTrue(TEXT("Cheap campaign guard reports the initialised authority"),
        Fixture.Management->IsCampaignInitialised());

    ALBFactoryBuildMachine* Machine =
        Fixture.World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Real generic machine configures with a persistent ID"), Machine
        && Machine->Configure(TEXT("RUNTIME-MACHINE-01"),
            ELBFactoryBuildMachineType::InspectionCell));
    TestTrue(TEXT("Machine accepts an actual identified unit"), Machine
        && Machine->AcceptInputUnit(TEXT("PANEL-RUNTIME-001")));
    TestTrue(TEXT("Long deterministic process fixture configures"), Machine
        && Machine->ConfigureGameplayProcessSteps(100));
    FName ProcessedUnit;
    bool bCompleted = false;
    TestTrue(TEXT("Machine enters its real Processing state"), Machine
        && Machine->AdvanceAutomaticProcess(ProcessedUnit, bCompleted));
    TestFalse(TEXT("Fixture has not fabricated process completion"), bCompleted);

    ALBPressTrainAStation* Train = Fixture.World->SpawnActor<ALBPressTrainAStation>();
    TestTrue(TEXT("Real press train variant configures"), Train
        && Train->ConfigureTrainVariant(TEXT("TRAIN_A"), TEXT("TRAIN A"),
            TEXT("OUTER PANELS"), FLinearColor::Green));
    FLBPressTrainASaveState FaultedTrain = Train
        ? Train->CaptureSaveState() : FLBPressTrainASaveState();
    FaultedTrain.State = ELBPressTrainAState::Fault;
    FaultedTrain.ActiveFault = ELBPressTrainAFault::TransferFault;
    FaultedTrain.bControlPowerOn = true;
    FaultedTrain.GoodPanels = 3;
    FaultedTrain.RejectedPanels = 1;
    TestTrue(TEXT("Press fixture restores a real explicit fault and counters"), Train
        && Train->RestoreSaveState(FaultedTrain));

    Fixture.World->BeginPlay();
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);

    FLBManagementMaintenanceRecord MachineMaintenance;
    FLBManagementMaintenanceRecord TrainMaintenance;
    TestTrue(TEXT("Generic machine is registered exactly under its gameplay ID"),
        Fixture.Management->GetMaintenanceRecord(TEXT("RUNTIME-MACHINE-01"),
            MachineMaintenance));
    TestTrue(TEXT("Press train is registered exactly under its gameplay ID"),
        Fixture.Management->GetMaintenanceRecord(TEXT("TRAIN_A"),
            TrainMaintenance));
    TestTrue(TEXT("Only the press train's actual fault is mirrored"),
        TrainMaintenance.bFaulted
            && TrainMaintenance.FaultCode == TEXT("PRESS-TransferFault"));
    TestFalse(TEXT("Deterministic wear never invents a generic-machine fault"),
        MachineMaintenance.bFaulted);

    FLBManagementQualityRecord Quality;
    TestTrue(TEXT("Press integrated inspection counters enter management quality"),
        Fixture.Management->GetQualityRecord(TEXT("TRAIN_A"), Quality));
    TestEqual(TEXT("Actual press good count is exact"), Quality.PassedCount, int64(3));
    TestEqual(TEXT("Actual press reject count is exact"), Quality.RejectedCount, int64(1));
    const int64 RevisionAfterFirstQuality = Fixture.Management->GetSnapshot().Revision;
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestTrue(TEXT("Unchanged source counters do not create a duplicate quality event"),
        Fixture.Management->GetSnapshot().Revision == RevisionAfterFirstQuality);

    for (int32 Second = 2; Second < 10; ++Second)
        Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestTrue(TEXT("Running generic machine retains maintenance evidence"),
        Fixture.Management->GetMaintenanceRecord(TEXT("RUNTIME-MACHINE-01"),
            MachineMaintenance));
    TestTrue(TEXT("Ten bounded samples become ten operating seconds"),
        FMath::IsNearlyEqual(MachineMaintenance.OperatingSecondsSinceService,
            10.0, 0.001));
    TestTrue(TEXT("Operating use increases deterministic wear"),
        MachineMaintenance.WearFraction > 0.0 && MachineMaintenance.WearFraction < 1.0);
    TestTrue(TEXT("Faulted press records exact downtime rather than operating wear"),
        Fixture.Management->GetMaintenanceRecord(TEXT("TRAIN_A"), TrainMaintenance)
            && FMath::IsNearlyEqual(TrainMaintenance.CumulativeDowntimeSeconds,
                10.0, 0.001));
    TestTrue(TEXT("Fixed buckets cover both real discovered assets"),
        Fixture.Management->GetSnapshot().AnalyticsBuckets.Num() >= 2);

    FLBPressTrainASaveState HealthyTrain = Train->CaptureSaveState();
    HealthyTrain.State = ELBPressTrainAState::Ready;
    HealthyTrain.ActiveFault = ELBPressTrainAFault::None;
    TestTrue(TEXT("Gameplay authority clears its actual fault"),
        Train->RestoreSaveState(HealthyTrain));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestTrue(TEXT("Runtime bridge observes the real clear state"),
        Fixture.Management->GetMaintenanceRecord(TEXT("TRAIN_A"), TrainMaintenance));
    TestFalse(TEXT("Management fault clears only after gameplay fault clears"),
        TrainMaintenance.bFaulted);

    DestroyRuntimeBridgeFixture(Fixture);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBManagementRuntimePressQualityEpochTest,
    "LineBoss.Management.Runtime.PressQualityCounterEpochAcrossReplacement",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRuntimePressQualityEpochTest::RunTest(const FString& Parameters)
{
    FLBRuntimeBridgeFixture Fixture = CreateRuntimeBridgeFixture(
        TEXT("LB_ManagementRuntimeQualityEpoch"));
    ALBPressTrainAStation* Original = Fixture.World
        ? Fixture.World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    TestTrue(TEXT("Original press configures under its persistent ID"), Original
        && Original->ConfigureTrainVariant(TEXT("TRAIN_A"), TEXT("TRAIN A"),
            TEXT("OUTER PANELS"), FLinearColor::Green));
    if (!Fixture.World || !Fixture.Management || !Fixture.Bridge || !Original)
    {
        DestroyRuntimeBridgeFixture(Fixture);
        return false;
    }

    FLBPressTrainASaveState OriginalState = Original->CaptureSaveState();
    OriginalState.GoodPanels = 3;
    OriginalState.RejectedPanels = 1;
    TestTrue(TEXT("Original lifetime counters restore"),
        Original->RestoreSaveState(OriginalState));
    Fixture.World->BeginPlay();
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);

    FLBManagementQualityRecord Quality;
    TestTrue(TEXT("Original counters reach durable quality"),
        Fixture.Management->GetQualityRecord(TEXT("TRAIN_A"), Quality));
    TestEqual(TEXT("Original good total"), Quality.PassedCount, int64(3));
    TestEqual(TEXT("Original reject total"), Quality.RejectedCount, int64(1));

    TestTrue(TEXT("Original actor is removed before identity reuse"), Original->Destroy());
    ALBPressTrainAStation* Replacement =
        Fixture.World->SpawnActor<ALBPressTrainAStation>();
    TestTrue(TEXT("Replacement may reuse the same persistent train ID"), Replacement
        && Replacement->ConfigureTrainVariant(TEXT("TRAIN_A"), TEXT("TRAIN A"),
            TEXT("OUTER PANELS"), FLinearColor::Green));
    if (!Replacement)
    {
        DestroyRuntimeBridgeFixture(Fixture);
        return false;
    }
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);

    FLBPressTrainASaveState ReplacementState = Replacement
        ? Replacement->CaptureSaveState() : FLBPressTrainASaveState();
    ReplacementState.GoodPanels = 2;
    ReplacementState.RejectedPanels = 1;
    TestTrue(TEXT("Replacement produces in its new counter epoch"), Replacement
        && Replacement->RestoreSaveState(ReplacementState));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestTrue(TEXT("Replacement quality remains attached to the durable train ID"),
        Fixture.Management->GetQualityRecord(TEXT("TRAIN_A"), Quality));
    TestEqual(TEXT("New-epoch good panels add to lifetime total"),
        Quality.PassedCount, int64(5));
    TestEqual(TEXT("New-epoch rejects add to lifetime total"),
        Quality.RejectedCount, int64(2));

    ReplacementState = Replacement->CaptureSaveState();
    ReplacementState.GoodPanels = 0;
    ReplacementState.RejectedPanels = 0;
    TestTrue(TEXT("Same actor can reset its local service counters"),
        Replacement->RestoreSaveState(ReplacementState));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    ReplacementState.GoodPanels = 1;
    TestTrue(TEXT("Reset actor produces after the new baseline"),
        Replacement->RestoreSaveState(ReplacementState));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestTrue(TEXT("Reset-epoch quality remains queryable"),
        Fixture.Management->GetQualityRecord(TEXT("TRAIN_A"), Quality));
    TestEqual(TEXT("Same-actor reset does not stall or double count quality"),
        Quality.PassedCount, int64(6));
    TestEqual(TEXT("Reset does not invent rejects"),
        Quality.RejectedCount, int64(2));

    DestroyRuntimeBridgeFixture(Fixture);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBManagementRuntimeBucketRetryTest,
    "LineBoss.Management.Runtime.FailedBucketCommitRetainsEvidence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRuntimeBucketRetryTest::RunTest(const FString& Parameters)
{
    FLBRuntimeBridgeFixture Fixture = CreateRuntimeBridgeFixture(
        TEXT("LB_ManagementRuntimeBucketRetry"));
    ALBFactoryBuildMachine* Machine = Fixture.World
        ? Fixture.World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    TestTrue(TEXT("Retry fixture machine configures"), Machine
        && Machine->Configure(TEXT("RETRY-MACHINE-01"),
            ELBFactoryBuildMachineType::InspectionCell));
    TestTrue(TEXT("Retry fixture accepts identified work"), Machine
        && Machine->AcceptInputUnit(TEXT("PANEL-RETRY-001")));
    TestTrue(TEXT("Retry fixture uses a long real process"), Machine
        && Machine->ConfigureGameplayProcessSteps(100));
    FName ProcessedUnit;
    bool bCompleted = false;
    TestTrue(TEXT("Retry fixture enters Processing"), Machine
        && Machine->AdvanceAutomaticProcess(ProcessedUnit, bCompleted));
    if (!Fixture.World || !Fixture.Management || !Fixture.Bridge || !Machine)
    {
        DestroyRuntimeBridgeFixture(Fixture);
        return false;
    }

    Fixture.World->BeginPlay();
    for (int32 Second = 0; Second < 9; ++Second)
        Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    const int64 RevisionBeforeSaturation =
        Fixture.Management->GetSnapshot().Revision;
    FLBFactoryManagementSaveState Saturated = Fixture.Management->CaptureSaveState();
    Saturated.Revision = MAX_int64 - 1;
    TestTrue(TEXT("Near-saturated revision is a valid deterministic failure fixture"),
        Fixture.Management->RestoreSaveState(Saturated));

    // Maintenance consumes the final revision; analytics must fail and remain pending.
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    FLBManagementMaintenanceRecord Maintenance;
    TestTrue(TEXT("Maintenance half of the bucket committed exactly once"),
        Fixture.Management->GetMaintenanceRecord(TEXT("RETRY-MACHINE-01"),
            Maintenance));
    TestTrue(TEXT("Ten seconds of maintenance evidence survived staging"),
        FMath::IsNearlyEqual(Maintenance.OperatingSecondsSinceService, 10.0, 0.001));
    TestEqual(TEXT("Analytics half could not commit at maximum revision"),
        Fixture.Management->GetSnapshot().AnalyticsBuckets.Num(), 0);

    FLBFactoryManagementSaveState Retryable = Fixture.Management->CaptureSaveState();
    Retryable.Revision = RevisionBeforeSaturation + 1;
    TestTrue(TEXT("Failure fixture is reopened without discarding committed usage"),
        Fixture.Management->RestoreSaveState(Retryable));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);

    TestTrue(TEXT("Maintenance retry is idempotent"),
        Fixture.Management->GetMaintenanceRecord(TEXT("RETRY-MACHINE-01"),
            Maintenance));
    TestTrue(TEXT("Maintenance evidence was not duplicated on analytics retry"),
        FMath::IsNearlyEqual(Maintenance.OperatingSecondsSinceService, 10.0, 0.001));
    const TArray<FLBManagementAnalyticsSnapshot>& Buckets =
        Fixture.Management->GetSnapshot().AnalyticsBuckets;
    TestEqual(TEXT("Frozen analytics evidence commits on the next valid sample"),
        Buckets.Num(), 1);
    if (Buckets.Num() == 1)
    {
        TestTrue(TEXT("Retried bucket retains the original ten-second duration"),
            FMath::IsNearlyEqual(Buckets[0].Raw.BucketDurationSeconds, 10.0, 0.001));
        TestTrue(TEXT("Retried bucket retains all running evidence"),
            FMath::IsNearlyEqual(Buckets[0].Raw.RunningSeconds, 10.0, 0.001));
    }

    // The successful retry already opened the next live bucket with one second.
    for (int32 Second = 1; Second < 9; ++Second)
        Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    const int64 RevisionBeforeMaintenanceFailure =
        Fixture.Management->GetSnapshot().Revision;
    FLBFactoryManagementSaveState MaintenanceBlocked =
        Fixture.Management->CaptureSaveState();
    MaintenanceBlocked.Revision = MAX_int64;
    TestTrue(TEXT("Maximum revision blocks the maintenance half itself"),
        Fixture.Management->RestoreSaveState(MaintenanceBlocked));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestTrue(TEXT("Failed maintenance commit does not alter durable usage"),
        Fixture.Management->GetMaintenanceRecord(TEXT("RETRY-MACHINE-01"),
            Maintenance)
            && FMath::IsNearlyEqual(Maintenance.OperatingSecondsSinceService,
                10.0, 0.001));
    TestEqual(TEXT("Failed maintenance prevents its paired analytics commit"),
        Fixture.Management->GetSnapshot().AnalyticsBuckets.Num(), 1);

    FLBFactoryManagementSaveState MaintenanceRetryable =
        Fixture.Management->CaptureSaveState();
    MaintenanceRetryable.Revision = RevisionBeforeMaintenanceFailure;
    TestTrue(TEXT("Maintenance failure fixture is reopened"),
        Fixture.Management->RestoreSaveState(MaintenanceRetryable));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestTrue(TEXT("Retried maintenance commits the retained second bucket once"),
        Fixture.Management->GetMaintenanceRecord(TEXT("RETRY-MACHINE-01"),
            Maintenance)
            && FMath::IsNearlyEqual(Maintenance.OperatingSecondsSinceService,
                20.0, 0.001));
    TestEqual(TEXT("Retried analytics commits the retained second bucket"),
        Fixture.Management->GetSnapshot().AnalyticsBuckets.Num(), 2);
    if (Fixture.Management->GetSnapshot().AnalyticsBuckets.Num() == 2)
    {
        TestTrue(TEXT("Maintenance-failure retry preserves bucket duration"),
            FMath::IsNearlyEqual(
                Fixture.Management->GetSnapshot().AnalyticsBuckets[1]
                    .Raw.BucketDurationSeconds,
                10.0, 0.001));
    }

    DestroyRuntimeBridgeFixture(Fixture);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBManagementRuntimeDeliveredOrderTest,
    "LineBoss.Management.Runtime.DeliveredPanelOrderExactOnceAcrossRestore",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRuntimeDeliveredOrderTest::RunTest(const FString& Parameters)
{
    constexpr int64 OpeningCash = 1000000;
    FLBRuntimeBridgeFixture Fixture = CreateRuntimeBridgeFixture(
        TEXT("LB_ManagementRuntimeOrder"), OpeningCash);
    TestNotNull(TEXT("Delivered-order bridge exists"), Fixture.Bridge);
    ALBPlayerBuiltPressFlowController* Flow = Fixture.World
        ? Fixture.World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    TestNotNull(TEXT("Existing player-built production-order authority exists"), Flow);
    if (!Fixture.World || !Fixture.Management || !Fixture.Bridge || !Flow)
    {
        DestroyRuntimeBridgeFixture(Fixture);
        return false;
    }

    const FName OrderId(TEXT("ORDER-RUNTIME-001"));
    const FLBStampedPanelDefinition* Definition = LBCairnwell2040PanelCatalog::Find(
        TEXT("CAIRNWELL_2040"), TEXT("DOOR_FRONT_LEFT"));
    TestNotNull(TEXT("Approved stamped-panel definition exists"), Definition);
    if (!Definition)
    {
        DestroyRuntimeBridgeFixture(Fixture);
        return false;
    }

    FLBPlayerBuiltPressFlowSaveState Incomplete;
    FLBVehiclePanelBatch Batch;
    Batch.OrderId = OrderId;
    Batch.VehicleModelId = TEXT("CAIRNWELL_2040");
    Batch.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
    Batch.RequestedQuantity = 2;
    Batch.DispatchedQuantity = 2;
    Incomplete.PanelBatches.Add(Batch);
    FLBPanelLineageRecord WaitingPanel = MakeDeliveredPanel(OrderId,
        TEXT("PANEL-ORDER-001"), TEXT("BLANK-ORDER-001"), TEXT("STILLAGE-ORDER-001"));
    WaitingPanel.Stage = ELBPanelFlowStage::WIPStillage;
    Incomplete.PanelLineage.Add(WaitingPanel);
    FLBPanelLineageRecord RejectedPanel;
    RejectedPanel.PanelId = TEXT("PANEL-ORDER-002");
    RejectedPanel.BlankId = TEXT("BLANK-ORDER-002");
    RejectedPanel.OrderId = OrderId;
    RejectedPanel.VehicleModelId = TEXT("CAIRNWELL_2040");
    RejectedPanel.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
    RejectedPanel.SourceTrainId = TEXT("TRAIN_A");
    RejectedPanel.Disposition = ELBPanelDisposition::Rejected;
    RejectedPanel.Stage = ELBPanelFlowStage::Rejected;
    Incomplete.PanelLineage.Add(RejectedPanel);
    FLBPanelStillageLoad WaitingLoad = MakeDeliveredStillage(OrderId,
        TEXT("STILLAGE-ORDER-001"), TEXT("PANEL-ORDER-001"),
        Definition->StillageCapacity);
    WaitingLoad.bReadyForWeld = false;
    WaitingLoad.bDeliveredToWeld = false;
    Incomplete.PanelStillages.Add(WaitingLoad);
    Incomplete.NextStillageSerial = 2;
    TestTrue(TEXT("Incomplete/rejected source order is a valid real flow state"),
        Flow->RestoreSaveState(Incomplete));
    Fixture.World->BeginPlay();
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestEqual(TEXT("Rejected or undelivered order earns no cash"),
        Fixture.Management->GetCashBalancePence(), OpeningCash);
    TestEqual(TEXT("Rejected or undelivered order earns no research"),
        Fixture.Management->GetAvailableResearchPoints(), int64(0));

    FLBPlayerBuiltPressFlowSaveState Uncorroborated;
    Uncorroborated.PanelBatches.Add(Batch);
    FLBPanelLineageRecord UncorroboratedPanelA = MakeDeliveredPanel(OrderId,
        TEXT("PANEL-ORDER-001"), TEXT("BLANK-ORDER-001"), TEXT("STILLAGE-ORDER-001"));
    FLBPanelLineageRecord UncorroboratedPanelB = MakeDeliveredPanel(OrderId,
        TEXT("PANEL-ORDER-002"), TEXT("BLANK-ORDER-002"), TEXT("STILLAGE-ORDER-002"));
    UncorroboratedPanelA.Stage = ELBPanelFlowStage::WIPStillage;
    UncorroboratedPanelB.Stage = ELBPanelFlowStage::WIPStillage;
    Uncorroborated.PanelLineage.Add(UncorroboratedPanelA);
    Uncorroborated.PanelLineage.Add(UncorroboratedPanelB);
    FLBPanelStillageLoad UncorroboratedLoadA = MakeDeliveredStillage(OrderId,
        TEXT("STILLAGE-ORDER-001"), TEXT("PANEL-ORDER-001"),
        Definition->StillageCapacity);
    FLBPanelStillageLoad UncorroboratedLoadB = MakeDeliveredStillage(OrderId,
        TEXT("STILLAGE-ORDER-002"), TEXT("PANEL-ORDER-002"),
        Definition->StillageCapacity);
    UncorroboratedLoadA.bDeliveredToWeld = false;
    UncorroboratedLoadB.bDeliveredToWeld = false;
    Uncorroborated.PanelStillages.Add(UncorroboratedLoadA);
    Uncorroborated.PanelStillages.Add(UncorroboratedLoadB);
    Uncorroborated.NextStillageSerial = 3;
    TestTrue(TEXT("Lineage alone can restore but is not delivery proof"),
        Flow->RestoreSaveState(Uncorroborated));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestEqual(TEXT("Weld-intake lineage without delivered stillages earns no cash"),
        Fixture.Management->GetCashBalancePence(), OpeningCash);

    const FLBStampedPanelDefinition* WrongDefinition =
        LBCairnwell2040PanelCatalog::Find(TEXT("CAIRNWELL_2040"),
            TEXT("DOOR_FRONT_RIGHT"));
    TestNotNull(TEXT("A second approved recipe exists for mismatch coverage"),
        WrongDefinition);
    if (!WrongDefinition)
    {
        DestroyRuntimeBridgeFixture(Fixture);
        return false;
    }
    FLBPlayerBuiltPressFlowSaveState WrongProduct;
    WrongProduct.PanelBatches.Add(Batch);
    FLBVehiclePanelBatch WrongProductBatch = Batch;
    WrongProductBatch.PanelTypeId = TEXT("DOOR_FRONT_RIGHT");
    WrongProductBatch.DispatchedQuantity = 0;
    WrongProduct.PanelBatches.Add(WrongProductBatch);
    FLBPanelLineageRecord WrongPanelA = MakeDeliveredPanel(OrderId,
        TEXT("PANEL-WRONG-001"), TEXT("BLANK-WRONG-001"), TEXT("STILLAGE-WRONG-001"));
    FLBPanelLineageRecord WrongPanelB = MakeDeliveredPanel(OrderId,
        TEXT("PANEL-WRONG-002"), TEXT("BLANK-WRONG-002"), TEXT("STILLAGE-WRONG-002"));
    WrongPanelA.PanelTypeId = TEXT("DOOR_FRONT_RIGHT");
    WrongPanelB.PanelTypeId = TEXT("DOOR_FRONT_RIGHT");
    WrongProduct.PanelLineage.Add(WrongPanelA);
    WrongProduct.PanelLineage.Add(WrongPanelB);
    FLBPanelStillageLoad WrongLoadA = MakeDeliveredStillage(OrderId,
        TEXT("STILLAGE-WRONG-001"), TEXT("PANEL-WRONG-001"),
        WrongDefinition->StillageCapacity);
    FLBPanelStillageLoad WrongLoadB = MakeDeliveredStillage(OrderId,
        TEXT("STILLAGE-WRONG-002"), TEXT("PANEL-WRONG-002"),
        WrongDefinition->StillageCapacity);
    WrongLoadA.PanelTypeId = TEXT("DOOR_FRONT_RIGHT");
    WrongLoadB.PanelTypeId = TEXT("DOOR_FRONT_RIGHT");
    WrongProduct.PanelStillages.Add(WrongLoadA);
    WrongProduct.PanelStillages.Add(WrongLoadB);
    WrongProduct.NextStillageSerial = 3;
    TestTrue(TEXT("Different product under the same order can restore as source data"),
        Flow->RestoreSaveState(WrongProduct));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestEqual(TEXT("Order ID alone cannot fulfil a different panel contract"),
        Fixture.Management->GetCashBalancePence(), OpeningCash);
    TestEqual(TEXT("Mismatched product delivery earns no research"),
        Fixture.Management->GetAvailableResearchPoints(), int64(0));

    FLBPlayerBuiltPressFlowSaveState Delivered;
    Delivered.PanelBatches.Add(Batch);
    Delivered.PanelLineage.Add(MakeDeliveredPanel(OrderId,
        TEXT("PANEL-ORDER-001"), TEXT("BLANK-ORDER-001"), TEXT("STILLAGE-ORDER-001")));
    Delivered.PanelLineage.Add(MakeDeliveredPanel(OrderId,
        TEXT("PANEL-ORDER-002"), TEXT("BLANK-ORDER-002"), TEXT("STILLAGE-ORDER-002")));
    Delivered.PanelStillages.Add(MakeDeliveredStillage(OrderId,
        TEXT("STILLAGE-ORDER-001"), TEXT("PANEL-ORDER-001"),
        Definition->StillageCapacity));
    Delivered.PanelStillages.Add(MakeDeliveredStillage(OrderId,
        TEXT("STILLAGE-ORDER-002"), TEXT("PANEL-ORDER-002"),
        Definition->StillageCapacity));
    Delivered.NextStillageSerial = 3;
    TestTrue(TEXT("Fulfilled state contains two actual weld-intake deliveries"),
        Flow->RestoreSaveState(Delivered));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    const int64 ExpectedRevenue = 2
        * ULBFactoryManagementRuntimeSubsystem::DefaultPanelRevenuePence;
    TestEqual(TEXT("One fulfilled pressed-panel contract earns exact revenue"),
        Fixture.Management->GetCashBalancePence(), OpeningCash + ExpectedRevenue);
    TestEqual(TEXT("One fulfilled pressed-panel contract earns one research grant"),
        Fixture.Management->GetAvailableResearchPoints(),
        ULBFactoryManagementRuntimeSubsystem::DefaultFulfilmentResearchPoints);
    TestEqual(TEXT("Ledger labels the income as order revenue"),
        Fixture.Management->GetSnapshot().OrderRevenuePence, ExpectedRevenue);

    const FName AcceptedOrderId(TEXT("ORDER-RUNTIME-ACCEPTED-001"));
    FLBPlayerBuiltPressFlowSaveState Accepted;
    FLBVehiclePanelBatch AcceptedBatch = Batch;
    AcceptedBatch.OrderId = AcceptedOrderId;
    Accepted.PanelBatches.Add(AcceptedBatch);
    FLBPanelLineageRecord AcceptedPanelA = MakeDeliveredPanel(AcceptedOrderId,
        TEXT("PANEL-ACCEPTED-001"), TEXT("BLANK-ACCEPTED-001"),
        TEXT("STILLAGE-ACCEPTED-001"));
    FLBPanelLineageRecord AcceptedPanelB = MakeDeliveredPanel(AcceptedOrderId,
        TEXT("PANEL-ACCEPTED-002"), TEXT("BLANK-ACCEPTED-002"),
        TEXT("STILLAGE-ACCEPTED-002"));
    AcceptedPanelA.Stage = ELBPanelFlowStage::BodyWeldInventory;
    AcceptedPanelB.Stage = ELBPanelFlowStage::BodyWeldInventory;
    Accepted.PanelLineage.Add(AcceptedPanelA);
    Accepted.PanelLineage.Add(AcceptedPanelB);
    FLBPanelStillageLoad AcceptedLoadA = MakeDeliveredStillage(AcceptedOrderId,
        TEXT("STILLAGE-ACCEPTED-001"), TEXT("PANEL-ACCEPTED-001"),
        Definition->StillageCapacity);
    FLBPanelStillageLoad AcceptedLoadB = MakeDeliveredStillage(AcceptedOrderId,
        TEXT("STILLAGE-ACCEPTED-002"), TEXT("PANEL-ACCEPTED-002"),
        Definition->StillageCapacity);
    AcceptedLoadA.WeldLineId = TEXT("BODY-WELD-RUNTIME-01");
    AcceptedLoadB.WeldLineId = TEXT("BODY-WELD-RUNTIME-01");
    AcceptedLoadA.WeldDeliverySequence = 1;
    AcceptedLoadB.WeldDeliverySequence = 2;
    AcceptedLoadA.bAcceptedByBodyWeld = true;
    AcceptedLoadB.bAcceptedByBodyWeld = true;
    Accepted.PanelStillages.Add(AcceptedLoadA);
    Accepted.PanelStillages.Add(AcceptedLoadB);
    Accepted.NextStillageSerial = 3;
    Accepted.NextBodyWeldDeliverySequence = 3;
    TestTrue(TEXT("Body-weld-owned panels retain exact delivered/accepted proof"),
        Flow->RestoreSaveState(Accepted));
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestEqual(TEXT("Accepted panels earn only their pressed-panel contract revenue"),
        Fixture.Management->GetCashBalancePence(),
        OpeningCash + (2 * ExpectedRevenue));
    TestEqual(TEXT("Accepted pressed-panel contract earns one further research grant"),
        Fixture.Management->GetAvailableResearchPoints(),
        2 * ULBFactoryManagementRuntimeSubsystem::DefaultFulfilmentResearchPoints);
    TestEqual(TEXT("Accepted ownership does not invent separate weld-body revenue"),
        Fixture.Management->GetSnapshot().OrderRevenuePence,
        2 * ExpectedRevenue);

    const FLBFactoryManagementSaveState SavedManagement =
        Fixture.Management->CaptureSaveState();
    TestTrue(TEXT("Management state round-trips before a bridge restart"),
        Fixture.Management->RestoreSaveState(SavedManagement));
    ULBFactoryManagementRuntimeSubsystem* RestartedBridge =
        NewObject<ULBFactoryManagementRuntimeSubsystem>(Fixture.World);
    TestNotNull(TEXT("Fresh transient bridge represents a reload"), RestartedBridge);
    RestartedBridge->AdvanceRuntimeBridge(1.0f);
    TestEqual(TEXT("Reload cannot duplicate delivered or accepted panel revenue"),
        Fixture.Management->GetCashBalancePence(),
        OpeningCash + (2 * ExpectedRevenue));
    TestEqual(TEXT("Reload cannot duplicate delivered or accepted panel research"),
        Fixture.Management->GetAvailableResearchPoints(),
        2 * ULBFactoryManagementRuntimeSubsystem::DefaultFulfilmentResearchPoints);

    DestroyRuntimeBridgeFixture(Fixture);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBManagementRuntimeBodyWeldEvidenceTest,
    "LineBoss.Management.Runtime.BodyWeldMaintenanceWithoutFabricatedCommercialCounters",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBManagementRuntimeBodyWeldEvidenceTest::RunTest(const FString& Parameters)
{
    constexpr int64 OpeningCash = 2000000;
    FLBRuntimeBridgeFixture Fixture = CreateRuntimeBridgeFixture(
        TEXT("LB_ManagementRuntimeBodyWeld"), OpeningCash);
    ALBBodyWeldLineActor* Line = Fixture.World
        ? Fixture.World->SpawnActor<ALBBodyWeldLineActor>() : nullptr;
    TestTrue(TEXT("Composite Body Weld fixture has one stable management identity"), Line
        && Line->Configure(TEXT("BODY-WELD-MGMT-01"))
        && Line->SetAssignedOrder(TEXT("ORDER-BODY-WELD-MGMT-01")));
    if (!Fixture.World || !Fixture.Management || !Fixture.Bridge || !Line)
    {
        DestroyRuntimeBridgeFixture(Fixture);
        return false;
    }

    Fixture.World->BeginPlay();
    Fixture.Bridge->AdvanceRuntimeBridge(1.0f);

    FLBManagementMaintenanceRecord Maintenance;
    TestTrue(TEXT("Body Weld is discovered under LineId rather than actor name"),
        Fixture.Management->GetMaintenanceRecord(TEXT("BODY-WELD-MGMT-01"), Maintenance));
    TestFalse(TEXT("Normal material starvation is not misreported as a machine fault"),
        Maintenance.bFaulted);
    FLBManagementQualityRecord Quality;
    TestFalse(TEXT("Current BIW slots do not fabricate a lifetime quality record"),
        Fixture.Management->GetQualityRecord(TEXT("BODY-WELD-MGMT-01"), Quality));
    TestEqual(TEXT("Discovering or sampling Body Weld cannot create extra revenue"),
        Fixture.Management->GetCashBalancePence(), OpeningCash);
    TestEqual(TEXT("Body Weld sampling leaves order revenue at zero"),
        Fixture.Management->GetSnapshot().OrderRevenuePence, int64(0));

    for (int32 Second = 1; Second < 10; ++Second)
        Fixture.Bridge->AdvanceRuntimeBridge(1.0f);
    TestTrue(TEXT("Starved Body Weld contributes exact tracked downtime evidence"),
        Fixture.Management->GetMaintenanceRecord(TEXT("BODY-WELD-MGMT-01"), Maintenance)
        && FMath::IsNearlyEqual(Maintenance.OperatingSecondsSinceService, 0.0, 0.001));
    TestEqual(TEXT("A full analytics bucket still cannot manufacture BIW revenue"),
        Fixture.Management->GetCashBalancePence(), OpeningCash);
    TestFalse(TEXT("A full analytics bucket still cannot manufacture quality totals"),
        Fixture.Management->GetQualityRecord(TEXT("BODY-WELD-MGMT-01"), Quality));
    const FLBManagementAnalyticsSnapshot* WeldBucket =
        Fixture.Management->GetSnapshot().AnalyticsBuckets.FindByPredicate(
            [](const FLBManagementAnalyticsSnapshot& Bucket)
            {
                return Bucket.AssetId == TEXT("BODY-WELD-MGMT-01");
            });
    TestNotNull(TEXT("Body Weld contributes a real time bucket under its LineId"), WeldBucket);
    if (WeldBucket)
    {
        TestEqual(TEXT("Body Weld time evidence has no fabricated produced BIWs"),
            WeldBucket->Raw.ProducedCount, int64(0));
        TestEqual(TEXT("Body Weld time evidence has no fabricated good BIWs"),
            WeldBucket->Raw.GoodCount, int64(0));
        TestTrue(TEXT("Body Weld time evidence records actual material starvation"),
            FMath::IsNearlyEqual(WeldBucket->Raw.StarvedSeconds, 10.0, 0.001));
    }

    DestroyRuntimeBridgeFixture(Fixture);
    return true;
}

#endif
