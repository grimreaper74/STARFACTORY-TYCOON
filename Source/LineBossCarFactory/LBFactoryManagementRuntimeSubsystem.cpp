#include "LBFactoryManagementRuntimeSubsystem.h"

#include "EngineUtils.h"
#include "LBBodyWeldLineActor.h"
#include "LBCompactStillageFLT.h"
#include "LBECoatLineActor.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryManagementSubsystem.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBPressTrainAStation.h"
#include "LBSupportRobot.h"

namespace
{
    enum class ELBRuntimeTimeState : uint8
    {
        Running,
        Starved,
        Blocked,
        Fault
    };

    struct FLBRuntimeAssetEvidence
    {
        FName AssetId = NAME_None;
        AActor* Actor = nullptr;
        ELBRuntimeTimeState TimeState = ELBRuntimeTimeState::Blocked;
        FName FaultCode = NAME_None;
        double ServiceIntervalHours = 250.0;
        double IdealUnitsPerSecond = 0.0;
        int64 ProducedCount = 0;
        int64 GoodCount = 0;
        int64 RejectedCount = 0;
        bool bHasOutputCounter = false;
        bool bHasQualityCounter = false;

        bool IsFaulted() const
        {
            return TimeState == ELBRuntimeTimeState::Fault;
        }
    };

    FString EventToken(const FName SourceId)
    {
        const FString Source = SourceId.ToString();
        if (Source.Len() <= 36) return Source;
        return FString::Printf(TEXT("%s-%08X"), *Source.Left(26), GetTypeHash(Source));
    }

    FName StableEventId(const TCHAR* Operation, const FName SourceId)
    {
        return FName(*FString::Printf(TEXT("RT.%s.%s"), Operation,
            *EventToken(SourceId)));
    }

    FName RevisionEventId(const TCHAR* Operation, const FName SourceId,
        const int64 Revision)
    {
        return FName(*FString::Printf(TEXT("RT.%s.%s.R%lld"), Operation,
            *EventToken(SourceId), Revision));
    }

    FName CounterEventId(const FName AssetId, const int64 DurableGoodCount,
        const int64 DurableRejectedCount)
    {
        return FName(*FString::Printf(TEXT("RT.QLT.%s.G%lld.X%lld"),
            *EventToken(AssetId), DurableGoodCount, DurableRejectedCount));
    }

    FName BucketOrdinalEventId(const TCHAR* Operation, const FName SourceId,
        const int64 Ordinal)
    {
        return FName(*FString::Printf(TEXT("RT.%s.%s.B%lld"), Operation,
            *EventToken(SourceId), Ordinal));
    }

    FName OrderEventId(const TCHAR* Operation, const FName OrderId,
        const int32 RequestedQuantity)
    {
        return FName(*FString::Printf(TEXT("RT.%s.%s.Q%d"), Operation,
            *EventToken(OrderId), RequestedQuantity));
    }

    FName EnumFaultCode(const TCHAR* Domain, const UEnum* Enum, const int64 Value)
    {
        if (!Enum) return FName(*FString::Printf(TEXT("%s-FAULT"), Domain));
        const FString Name = Enum->GetNameStringByValue(Value);
        return Name.IsEmpty()
            ? FName(*FString::Printf(TEXT("%s-FAULT"), Domain))
            : FName(*FString::Printf(TEXT("%s-%s"), Domain, *Name));
    }

    bool IsUsableAssetId(const FName Id)
    {
        return ULBFactoryManagementSubsystem::IsStrictId(Id);
    }

    ELBRuntimeTimeState MachineTimeState(const ELBFactoryMachineOperatingState State)
    {
        switch (State)
        {
        case ELBFactoryMachineOperatingState::Processing:
            return ELBRuntimeTimeState::Running;
        case ELBFactoryMachineOperatingState::Idle:
        case ELBFactoryMachineOperatingState::Starved:
            return ELBRuntimeTimeState::Starved;
        case ELBFactoryMachineOperatingState::Fault:
            return ELBRuntimeTimeState::Fault;
        case ELBFactoryMachineOperatingState::Ready:
        case ELBFactoryMachineOperatingState::Blocked:
        default:
            return ELBRuntimeTimeState::Blocked;
        }
    }

    ELBRuntimeTimeState PressTimeState(const FLBPressTrainAHMIStatus& Status)
    {
        if (Status.ActiveFault != ELBPressTrainAFault::None
            || Status.State == ELBPressTrainAState::Fault)
            return ELBRuntimeTimeState::Fault;
        if (Status.State == ELBPressTrainAState::Cycling)
            return ELBRuntimeTimeState::Running;
        if (Status.State == ELBPressTrainAState::Ready
            && Status.PendingBlankCount == 0 && Status.InProcessBlankId.IsNone())
            return ELBRuntimeTimeState::Starved;
        return ELBRuntimeTimeState::Blocked;
    }

    bool IsRobotRunningState(const ELBSupportRobotState State)
    {
        switch (State)
        {
        case ELBSupportRobotState::Dispatched:
        case ELBSupportRobotState::Navigating:
        case ELBSupportRobotState::Cleaning:
        case ELBSupportRobotState::Inspecting:
        case ELBSupportRobotState::Diagnosing:
        case ELBSupportRobotState::LightService:
        case ELBSupportRobotState::Lubricating:
        case ELBSupportRobotState::DeliveringParts:
        case ELBSupportRobotState::ModuleExchange:
        case ELBSupportRobotState::Verifying:
        case ELBSupportRobotState::Returning:
        case ELBSupportRobotState::Servicing:
            return true;
        default:
            return false;
        }
    }

    bool IsRobotFaultState(const ELBSupportRobotState State)
    {
        switch (State)
        {
        case ELBSupportRobotState::Lost:
        case ELBSupportRobotState::LeakDetected:
        case ELBSupportRobotState::PartMismatch:
        case ELBSupportRobotState::ArmOverload:
        case ELBSupportRobotState::SafetyStop:
        case ELBSupportRobotState::Fault:
            return true;
        default:
            return false;
        }
    }

    ELBRuntimeTimeState RobotTimeState(const FLBSupportRobotSaveState& State)
    {
        if (State.ActiveFault != ELBSupportRobotFault::None || IsRobotFaultState(State.State))
            return ELBRuntimeTimeState::Fault;
        if (IsRobotRunningState(State.State)) return ELBRuntimeTimeState::Running;
        if (State.State == ELBSupportRobotState::Certified
            || State.State == ELBSupportRobotState::Docked)
            return ELBRuntimeTimeState::Starved;
        return ELBRuntimeTimeState::Blocked;
    }

    ELBRuntimeTimeState FLTTimeState(const ALBCompactStillageFLT* FLT)
    {
        if (!FLT) return ELBRuntimeTimeState::Blocked;
        if (FLT->GetFault() != ELBCompactStillageFLTFault::None
            || FLT->GetPhase() == ELBCompactStillageFLTPhase::Fault)
            return ELBRuntimeTimeState::Fault;
        return FLT->GetPhase() == ELBCompactStillageFLTPhase::Parked
            ? ELBRuntimeTimeState::Starved : ELBRuntimeTimeState::Running;
    }

    void AddMachineEvidence(UWorld* World, TArray<FLBRuntimeAssetEvidence>& OutAssets)
    {
        for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
        {
            ALBFactoryBuildMachine* Machine = *It;
            if (!IsValid(Machine) || !IsUsableAssetId(Machine->GetMachineId())) continue;
            FLBRuntimeAssetEvidence Evidence;
            Evidence.AssetId = Machine->GetMachineId();
            Evidence.Actor = Machine;
            Evidence.TimeState = MachineTimeState(Machine->GetOperatingState());
            Evidence.FaultCode = Evidence.IsFaulted() ? FName(TEXT("MACHINE-FAULT")) : NAME_None;
            Evidence.ServiceIntervalHours = 250.0;
            Evidence.IdealUnitsPerSecond = 0.25;
            Evidence.ProducedCount = FMath::Max(0, Machine->GetCompletedUnitCount());
            Evidence.GoodCount = Evidence.ProducedCount;
            Evidence.bHasOutputCounter = true;
            OutAssets.Add(Evidence);
        }
    }

    void AddPressEvidence(UWorld* World, TArray<FLBRuntimeAssetEvidence>& OutAssets)
    {
        for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
        {
            ALBPressTrainAStation* Train = *It;
            if (!IsValid(Train) || !IsUsableAssetId(Train->GetTrainId())) continue;
            const FLBPressTrainAHMIStatus Status = Train->GetHMIStatus();
            FLBRuntimeAssetEvidence Evidence;
            Evidence.AssetId = Train->GetTrainId();
            Evidence.Actor = Train;
            Evidence.TimeState = PressTimeState(Status);
            Evidence.FaultCode = Evidence.IsFaulted()
                ? (Status.ActiveFault == ELBPressTrainAFault::None
                    ? FName(TEXT("PRESS-STATE-FAULT"))
                    : EnumFaultCode(TEXT("PRESS"), StaticEnum<ELBPressTrainAFault>(),
                        static_cast<int64>(Status.ActiveFault)))
                : NAME_None;
            Evidence.ServiceIntervalHours = 500.0;
            Evidence.IdealUnitsPerSecond = FMath::Max(0.0,
                static_cast<double>(Status.TargetStrokesPerMinute) / 60.0);
            Evidence.GoodCount = FMath::Max(0, Status.GoodPanels);
            Evidence.RejectedCount = FMath::Max(0, Status.RejectedPanels);
            Evidence.ProducedCount = Evidence.GoodCount + Evidence.RejectedCount;
            Evidence.bHasOutputCounter = true;
            Evidence.bHasQualityCounter = true;
            OutAssets.Add(Evidence);
        }
    }

    void AddECoatEvidence(UWorld* World, TArray<FLBRuntimeAssetEvidence>& OutAssets)
    {
        for (TActorIterator<ALBECoatLineActor> It(World); It; ++It)
        {
            ALBECoatLineActor* Line = *It;
            if (!IsValid(Line) || !IsUsableAssetId(Line->GetLineId())) continue;
            bool bBayFaulted = false;
            bool bBayStarved = false;
            int32 FirstFaultedBay = INDEX_NONE;
            for (int32 BayIndex = 0; BayIndex < Line->GetBayCount(); ++BayIndex)
            {
                FLBECoatBayOperatingState Bay;
                if (!Line->GetBayOperatingState(BayIndex, Bay)) continue;
                if (Bay.bFaulted && FirstFaultedBay == INDEX_NONE) FirstFaultedBay = BayIndex;
                bBayFaulted |= Bay.bFaulted;
                bBayStarved |= Bay.bStarved;
            }

            FLBRuntimeAssetEvidence Evidence;
            Evidence.AssetId = Line->GetLineId();
            Evidence.Actor = Line;
            Evidence.ServiceIntervalHours = 1000.0;
            switch (Line->GetOperatingState())
            {
            case ELBECoatOperatingState::Running:
                Evidence.TimeState = bBayFaulted ? ELBRuntimeTimeState::Fault
                    : (bBayStarved ? ELBRuntimeTimeState::Starved
                        : ELBRuntimeTimeState::Running);
                break;
            case ELBECoatOperatingState::Starved:
                Evidence.TimeState = ELBRuntimeTimeState::Starved;
                break;
            case ELBECoatOperatingState::Faulted:
            case ELBECoatOperatingState::EmergencyStop:
                Evidence.TimeState = ELBRuntimeTimeState::Fault;
                break;
            default:
                Evidence.TimeState = bBayFaulted
                    ? ELBRuntimeTimeState::Fault : ELBRuntimeTimeState::Blocked;
                break;
            }
            if (Evidence.IsFaulted())
            {
                if (FirstFaultedBay != INDEX_NONE)
                    Evidence.FaultCode = FName(*FString::Printf(TEXT("ECOAT-BAY-%02d-FAULT"),
                        FirstFaultedBay + 1));
                else if (IsUsableAssetId(Line->GetStateReason()))
                    Evidence.FaultCode = Line->GetStateReason();
                else
                    Evidence.FaultCode = TEXT("ECOAT-FAULT");
            }
            // The line currently exposes carrier position, not a saved lifetime
            // completion counter. Deliberately leave output at zero rather than
            // reporting a looping/current carrier as a newly completed vehicle.
            OutAssets.Add(Evidence);
        }
    }

    void AddBodyWeldEvidence(UWorld* World, TArray<FLBRuntimeAssetEvidence>& OutAssets)
    {
        for (TActorIterator<ALBBodyWeldLineActor> It(World); It; ++It)
        {
            ALBBodyWeldLineActor* Line = *It;
            if (!IsValid(Line) || !IsUsableAssetId(Line->GetLineId())) continue;

            FLBRuntimeAssetEvidence Evidence;
            Evidence.AssetId = Line->GetLineId();
            Evidence.Actor = Line;
            Evidence.TimeState = MachineTimeState(Line->GetOperatingState());
            Evidence.ServiceIntervalHours = 1000.0;
            if (Evidence.IsFaulted())
            {
                const FName SourceFault = Line->CaptureSaveState().FaultReason;
                Evidence.FaultCode = IsUsableAssetId(SourceFault)
                    ? SourceFault : FName(TEXT("BODY-WELD-FAULT"));
            }
            // Completed BIWs are a durable lineage history, not a commercial delivery
            // counter. The geometry gate also exposes per-body evidence rather than
            // lifetime pass/reject totals. Deliberately leave both counter flags false:
            // management may track time, wear and faults, but must not invent revenue or
            // quality events from the current body/rework/output slots.
            OutAssets.Add(Evidence);
        }
    }

    void AddSupportRobotEvidence(UWorld* World, TArray<FLBRuntimeAssetEvidence>& OutAssets)
    {
        for (TActorIterator<ALBSupportRobot> It(World); It; ++It)
        {
            ALBSupportRobot* Robot = *It;
            if (!IsValid(Robot)) continue;
            const FLBSupportRobotSaveState State = Robot->CaptureCommonSaveState();
            if (!IsUsableAssetId(State.UnitId)) continue;
            FLBRuntimeAssetEvidence Evidence;
            Evidence.AssetId = State.UnitId;
            Evidence.Actor = Robot;
            Evidence.TimeState = RobotTimeState(State);
            Evidence.FaultCode = Evidence.IsFaulted()
                ? (State.ActiveFault == ELBSupportRobotFault::None
                    ? FName(TEXT("ROBOT-STATE-FAULT"))
                    : EnumFaultCode(TEXT("ROBOT"), StaticEnum<ELBSupportRobotFault>(),
                        static_cast<int64>(State.ActiveFault)))
                : NAME_None;
            Evidence.ServiceIntervalHours = 250.0;
            OutAssets.Add(Evidence);
        }
    }

    void AddFLTEvidence(UWorld* World, TArray<FLBRuntimeAssetEvidence>& OutAssets)
    {
        for (TActorIterator<ALBCompactStillageFLT> It(World); It; ++It)
        {
            ALBCompactStillageFLT* FLT = *It;
            if (!IsValid(FLT) || !IsUsableAssetId(FLT->GetUnitId())) continue;
            FLBRuntimeAssetEvidence Evidence;
            Evidence.AssetId = FLT->GetUnitId();
            Evidence.Actor = FLT;
            Evidence.TimeState = FLTTimeState(FLT);
            Evidence.FaultCode = Evidence.IsFaulted()
                ? (FLT->GetFault() == ELBCompactStillageFLTFault::None
                    ? FName(TEXT("FLT-STATE-FAULT"))
                    : EnumFaultCode(TEXT("FLT"), StaticEnum<ELBCompactStillageFLTFault>(),
                        static_cast<int64>(FLT->GetFault())))
                : NAME_None;
            Evidence.ServiceIntervalHours = 500.0;
            OutAssets.Add(Evidence);
        }
    }

    TArray<FLBRuntimeAssetEvidence> DiscoverAssets(UWorld* World)
    {
        TArray<FLBRuntimeAssetEvidence> Candidates;
        if (!World) return Candidates;
        AddMachineEvidence(World, Candidates);
        AddPressEvidence(World, Candidates);
        AddBodyWeldEvidence(World, Candidates);
        AddECoatEvidence(World, Candidates);
        AddSupportRobotEvidence(World, Candidates);
        AddFLTEvidence(World, Candidates);
        Candidates.Sort([](const FLBRuntimeAssetEvidence& A,
            const FLBRuntimeAssetEvidence& B)
        {
            if (A.AssetId != B.AssetId) return A.AssetId.LexicalLess(B.AssetId);
            const FString APath = A.Actor ? A.Actor->GetPathName() : FString();
            const FString BPath = B.Actor ? B.Actor->GetPathName() : FString();
            return APath < BPath;
        });

        TArray<FLBRuntimeAssetEvidence> Unique;
        for (const FLBRuntimeAssetEvidence& Candidate : Candidates)
        {
            if (!Unique.IsEmpty() && Unique.Last().AssetId == Candidate.AssetId) continue;
            Unique.Add(Candidate);
        }
        return Unique;
    }

    void EnsureRegistered(ULBFactoryManagementSubsystem* Management,
        const FLBRuntimeAssetEvidence& Asset)
    {
        FLBManagementMaintenanceRecord Existing;
        if (Management->GetMaintenanceRecord(Asset.AssetId, Existing)) return;
        Management->RegisterMaintainableAsset(
            StableEventId(TEXT("REG"), Asset.AssetId), Asset.AssetId,
            Asset.ServiceIntervalHours);
    }

    void MirrorFault(ULBFactoryManagementSubsystem* Management,
        const FLBRuntimeAssetEvidence& Asset)
    {
        FLBManagementMaintenanceRecord Existing;
        if (!Management->GetMaintenanceRecord(Asset.AssetId, Existing)) return;
        const int64 Revision = Management->GetSnapshot().Revision;
        if (Asset.IsFaulted())
        {
            if (!Existing.bFaulted || Existing.FaultCode != Asset.FaultCode)
                Management->SetAssetFault(
                    RevisionEventId(TEXT("FAULT"), Asset.AssetId, Revision),
                    Asset.AssetId, Asset.FaultCode);
        }
        else if (Existing.bFaulted)
        {
            Management->ClearAssetFault(
                RevisionEventId(TEXT("CLEAR"), Asset.AssetId, Revision),
                Asset.AssetId);
        }
    }

    void ReconcilePressQuality(ULBFactoryManagementSubsystem* Management,
        const FLBRuntimeAssetEvidence& Asset,
        FLBFactoryManagementRuntimeAccumulator& Accumulator)
    {
        if (!Asset.bHasQualityCounter) return;

        FLBManagementQualityRecord Existing;
        if (!Management->GetQualityRecord(Asset.AssetId, Existing))
            Existing.AssetId = Asset.AssetId;

        const auto EstablishBaseline = [&Accumulator, &Asset]()
        {
            Accumulator.LastObservedQualityActor = Asset.Actor;
            Accumulator.LastObservedQualityProduced = Asset.ProducedCount;
            Accumulator.LastObservedQualityGood = Asset.GoodCount;
            Accumulator.LastObservedQualityRejected = Asset.RejectedCount;
            Accumulator.bQualityBaselineEstablished = true;
        };

        int64 ProducedDelta = 0;
        int64 InspectedDelta = 0;
        int64 PassedDelta = 0;
        int64 RejectedDelta = 0;
        if (!Accumulator.bQualityBaselineEstablished)
        {
            // A fresh bridge can safely reconcile a continuing actor against durable
            // totals. Lower source counters indicate a new/reset epoch and are only
            // baselined, never subtracted from lifetime management evidence.
            if (Asset.ProducedCount >= Existing.ProducedCount
                && Asset.GoodCount >= Existing.PassedCount
                && Asset.RejectedCount >= Existing.RejectedCount)
            {
                ProducedDelta = Asset.ProducedCount - Existing.ProducedCount;
                InspectedDelta = Asset.ProducedCount - Existing.InspectedCount;
                PassedDelta = Asset.GoodCount - Existing.PassedCount;
                RejectedDelta = Asset.RejectedCount - Existing.RejectedCount;
            }
            else
            {
                EstablishBaseline();
                return;
            }
        }
        else
        {
            const bool bActorReplaced = Accumulator.LastObservedQualityActor.Get()
                != Asset.Actor;
            const bool bCounterReset = Asset.ProducedCount
                    < Accumulator.LastObservedQualityProduced
                || Asset.GoodCount < Accumulator.LastObservedQualityGood
                || Asset.RejectedCount < Accumulator.LastObservedQualityRejected;
            if (bActorReplaced || bCounterReset)
            {
                EstablishBaseline();
                return;
            }
            ProducedDelta = Asset.ProducedCount
                - Accumulator.LastObservedQualityProduced;
            InspectedDelta = ProducedDelta;
            PassedDelta = Asset.GoodCount - Accumulator.LastObservedQualityGood;
            RejectedDelta = Asset.RejectedCount
                - Accumulator.LastObservedQualityRejected;
        }

        if ((ProducedDelta | InspectedDelta | PassedDelta | RejectedDelta) == 0)
        {
            EstablishBaseline();
            return;
        }
        if (PassedDelta > MAX_int64 - Existing.PassedCount
            || RejectedDelta > MAX_int64 - Existing.RejectedCount)
            return;
        const int64 DurableGoodTarget = Existing.PassedCount + PassedDelta;
        const int64 DurableRejectedTarget = Existing.RejectedCount + RejectedDelta;
        if (Management->RecordQualityCounts(
            CounterEventId(Asset.AssetId, DurableGoodTarget, DurableRejectedTarget),
            Asset.AssetId, ProducedDelta, InspectedDelta, PassedDelta,
            RejectedDelta, 0, 0))
        {
            EstablishBaseline();
        }
    }

    struct FLBAnalyticsPosition
    {
        double StartSeconds = 0.0;
        int64 Ordinal = 0;
    };

    FLBAnalyticsPosition AnalyticsPositionForAsset(
        const ULBFactoryManagementSubsystem* Management, const FName AssetId)
    {
        FLBAnalyticsPosition Position;
        // Remaining scale issue: analytics history is intentionally append-only and
        // this scan is linear. Add save-compatible rollups/retention before claiming
        // unattended multi-year sessions; do not silently discard audit evidence here.
        for (const FLBManagementAnalyticsSnapshot& Bucket
            : Management->GetSnapshot().AnalyticsBuckets)
        {
            if (Bucket.AssetId != AssetId) continue;
            Position.StartSeconds += Bucket.Raw.BucketDurationSeconds;
            ++Position.Ordinal;
        }
        return Position;
    }

    void StageAssetBucket(ULBFactoryManagementSubsystem* Management,
        const FLBRuntimeAssetEvidence& Asset,
        FLBFactoryManagementRuntimeAccumulator& Accumulator)
    {
        if (Accumulator.bHasPendingBucket || Accumulator.ElapsedSeconds <= 0.0) return;
        const FLBAnalyticsPosition Position = AnalyticsPositionForAsset(Management,
            Asset.AssetId);
        FLBFactoryManagementRuntimePendingBucket& Pending = Accumulator.PendingBucket;
        Pending.BucketStartSimulationSeconds = Position.StartSeconds;
        Pending.ElapsedSeconds = Accumulator.ElapsedSeconds;
        Pending.RunningSeconds = Accumulator.RunningSeconds;
        Pending.StarvedSeconds = Accumulator.StarvedSeconds;
        Pending.BlockedSeconds = Accumulator.BlockedSeconds;
        Pending.FaultSeconds = Accumulator.FaultSeconds;
        Pending.ProducedCount = Accumulator.ProducedInBucket;
        Pending.GoodCount = FMath::Min(Accumulator.GoodInBucket,
            Accumulator.ProducedInBucket);
        Pending.MaintenanceEventId = BucketOrdinalEventId(TEXT("USE"),
            Asset.AssetId, Position.Ordinal);
        Pending.AnalyticsEventId = BucketOrdinalEventId(TEXT("KPI"),
            Asset.AssetId, Position.Ordinal);
        Pending.BucketId = BucketOrdinalEventId(TEXT("BUCKET"),
            Asset.AssetId, Position.Ordinal);
        Pending.bMaintenanceRequired = Pending.RunningSeconds > 0.0
            || Pending.FaultSeconds > 0.0;
        Accumulator.bHasPendingBucket = true;

        Accumulator.ElapsedSeconds = 0.0;
        Accumulator.RunningSeconds = 0.0;
        Accumulator.StarvedSeconds = 0.0;
        Accumulator.BlockedSeconds = 0.0;
        Accumulator.FaultSeconds = 0.0;
        Accumulator.ProducedInBucket = 0;
        Accumulator.GoodInBucket = 0;
    }

    bool FlushAssetBucket(ULBFactoryManagementSubsystem* Management,
        const FLBRuntimeAssetEvidence& Asset,
        FLBFactoryManagementRuntimeAccumulator& Accumulator)
    {
        if (!Accumulator.bHasPendingBucket) return true;
        FLBFactoryManagementRuntimePendingBucket& Pending = Accumulator.PendingBucket;

        if (Pending.bMaintenanceRequired && !Pending.bMaintenanceCommitted)
        {
            FLBManagementMaintenanceRecord Maintenance;
            if (!Management->GetMaintenanceRecord(Asset.AssetId, Maintenance))
                return false;
            const double WearIncrease = Pending.RunningSeconds
                / FMath::Max(1.0, Maintenance.ServiceIntervalOperatingHours * 3600.0);
            Pending.bMaintenanceCommitted = Management->RecordMaintenanceUsage(
                Pending.MaintenanceEventId, Asset.AssetId, Pending.RunningSeconds,
                Pending.FaultSeconds, FMath::Clamp(WearIncrease, 0.0, 1.0))
                || Management->IsEventApplied(Pending.MaintenanceEventId);
            if (!Pending.bMaintenanceCommitted) return false;
        }

        FLBManagementTimeBucketSample Sample;
        Sample.BucketStartSimulationSeconds = Pending.BucketStartSimulationSeconds;
        Sample.BucketDurationSeconds = Pending.ElapsedSeconds;
        Sample.PlannedProductionSeconds = Pending.ElapsedSeconds;
        Sample.RunningSeconds = Pending.RunningSeconds;
        Sample.StarvedSeconds = Pending.StarvedSeconds;
        Sample.BlockedSeconds = Pending.BlockedSeconds;
        Sample.FaultDowntimeSeconds = Pending.FaultSeconds;
        Sample.ProducedCount = Pending.ProducedCount;
        Sample.GoodCount = Pending.GoodCount;
        Sample.IdealUnitCapacity = FMath::Max(
            static_cast<double>(Sample.ProducedCount),
            Pending.RunningSeconds * Asset.IdealUnitsPerSecond);
        const bool bAnalyticsCommitted = Management->RecordTimeBucket(
            Pending.AnalyticsEventId, Pending.BucketId, Asset.AssetId, Sample)
            || Management->IsEventApplied(Pending.AnalyticsEventId);
        if (!bAnalyticsCommitted) return false;

        Pending = FLBFactoryManagementRuntimePendingBucket();
        Accumulator.bHasPendingBucket = false;
        return true;
    }

    void RewardFulfilledPanelOrders(UWorld* World,
        ULBFactoryManagementSubsystem* Management)
    {
        TArray<ALBPlayerBuiltPressFlowController*> Controllers;
        for (TActorIterator<ALBPlayerBuiltPressFlowController> It(World); It; ++It)
            if (IsValid(*It)) Controllers.Add(*It);
        Controllers.Sort([](const ALBPlayerBuiltPressFlowController& A,
            const ALBPlayerBuiltPressFlowController& B)
        {
            return A.GetPathName() < B.GetPathName();
        });

        for (const ALBPlayerBuiltPressFlowController* Controller : Controllers)
        {
            TArray<FLBVehiclePanelBatch> Batches = Controller->GetPanelBatches();
            const TArray<FLBPanelLineageRecord> Lineage = Controller->GetPanelLineage();
            const TArray<FLBPanelStillageLoad> Stillages = Controller->GetPanelStillages();
            Batches.Sort([](const FLBVehiclePanelBatch& A,
                const FLBVehiclePanelBatch& B)
            {
                return A.OrderId.LexicalLess(B.OrderId);
            });
            for (const FLBVehiclePanelBatch& Batch : Batches)
            {
                if (!IsUsableAssetId(Batch.OrderId) || Batch.RequestedQuantity <= 0
                    || !IsUsableAssetId(Batch.VehicleModelId)
                    || !IsUsableAssetId(Batch.PanelTypeId)
                    || Batch.DispatchedQuantity < Batch.RequestedQuantity)
                    continue;
                int32 DeliveredGoodPanels = 0;
                TSet<FName> CountedPanelIds;
                for (const FLBPanelLineageRecord& Panel : Lineage)
                {
                    const bool bAtWeldIntake =
                        Panel.Stage == ELBPanelFlowStage::WeldShopIntake;
                    const bool bAcceptedIntoBodyWeld =
                        Panel.Stage == ELBPanelFlowStage::BodyWeldInventory;
                    if (Panel.OrderId != Batch.OrderId
                        || Panel.VehicleModelId != Batch.VehicleModelId
                        || Panel.PanelTypeId != Batch.PanelTypeId
                        || !IsUsableAssetId(Panel.PanelId)
                        || !IsUsableAssetId(Panel.StillageId)
                        || CountedPanelIds.Contains(Panel.PanelId)
                        || Panel.Disposition != ELBPanelDisposition::Good
                        || (!bAtWeldIntake && !bAcceptedIntoBodyWeld))
                        continue;
                    const FLBPanelStillageLoad* DeliveredLoad = Stillages.FindByPredicate(
                        [&Batch, &Panel, bAtWeldIntake,
                            bAcceptedIntoBodyWeld](const FLBPanelStillageLoad& Load)
                    {
                        return Load.StillageId == Panel.StillageId
                            && Load.OrderId == Batch.OrderId
                            && Load.VehicleModelId == Batch.VehicleModelId
                            && Load.PanelTypeId == Batch.PanelTypeId
                            && Load.bReadyForWeld && Load.bDeliveredToWeld
                            && ((bAtWeldIntake && !Load.bAcceptedByBodyWeld)
                                || (bAcceptedIntoBodyWeld
                                    && Load.bAcceptedByBodyWeld
                                    && IsUsableAssetId(Load.WeldLineId)
                                    && Load.WeldDeliverySequence > 0))
                            && Load.PanelIds.Contains(Panel.PanelId);
                    });
                    if (!DeliveredLoad) continue;
                    CountedPanelIds.Add(Panel.PanelId);
                    ++DeliveredGoodPanels;
                }
                // This is deliberately a pressed-panel delivery contract. It does
                // not claim that a vehicle, weld body or painted body exists.
                if (DeliveredGoodPanels < Batch.RequestedQuantity) continue;
                if (static_cast<int64>(Batch.RequestedQuantity)
                    > MAX_int64 / ULBFactoryManagementRuntimeSubsystem::DefaultPanelRevenuePence)
                    continue;
                const int64 Revenue = static_cast<int64>(Batch.RequestedQuantity)
                    * ULBFactoryManagementRuntimeSubsystem::DefaultPanelRevenuePence;
                Management->TryRecordOrderRevenue(
                    OrderEventId(TEXT("REV"), Batch.OrderId, Batch.RequestedQuantity),
                    Batch.OrderId, Revenue);
                Management->GrantResearchPoints(
                    OrderEventId(TEXT("RP"), Batch.OrderId, Batch.RequestedQuantity),
                    Batch.OrderId,
                    ULBFactoryManagementRuntimeSubsystem::DefaultFulfilmentResearchPoints);
            }
        }
    }
}

bool ULBFactoryManagementRuntimeSubsystem::DoesSupportWorldType(
    const EWorldType::Type WorldType) const
{
    return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void ULBFactoryManagementRuntimeSubsystem::Tick(const float DeltaTime)
{
    AdvanceRuntimeBridge(DeltaTime);
}

TStatId ULBFactoryManagementRuntimeSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(ULBFactoryManagementRuntimeSubsystem,
        STATGROUP_Tickables);
}

void ULBFactoryManagementRuntimeSubsystem::AdvanceRuntimeBridge(
    const float DeltaSeconds)
{
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.0f) return;
    // A single frame can contribute at most ten fixed samples. This bounds hitch
    // recovery without allowing a paused/load frame to manufacture hours of wear.
    FixedStepAccumulatorSeconds += FMath::Min<double>(DeltaSeconds, 10.0);
    int32 Steps = 0;
    while (FixedStepAccumulatorSeconds + UE_DOUBLE_SMALL_NUMBER >= FixedSampleSeconds
        && Steps < 10)
    {
        FixedStepAccumulatorSeconds -= FixedSampleSeconds;
        SampleFixedInterval(FixedSampleSeconds);
        ++Steps;
    }
}

void ULBFactoryManagementRuntimeSubsystem::SampleFixedInterval(
    const double SampleSeconds)
{
    UWorld* World = GetWorld();
    if (!World) return;
    ULBFactoryManagementSubsystem* Management =
        World->GetSubsystem<ULBFactoryManagementSubsystem>();
    if (!Management || !Management->IsCampaignInitialised()) return;

    const TArray<FLBRuntimeAssetEvidence> Assets = DiscoverAssets(World);
    TSet<FName> SeenAssets;
    for (const FLBRuntimeAssetEvidence& Asset : Assets)
    {
        SeenAssets.Add(Asset.AssetId);
        EnsureRegistered(Management, Asset);
        MirrorFault(Management, Asset);

        FLBFactoryManagementRuntimeAccumulator& Accumulator =
            AssetAccumulators.FindOrAdd(Asset.AssetId);
        ReconcilePressQuality(Management, Asset, Accumulator);
        // Retry a frozen partial commit before adding this second to the live bucket.
        // New evidence remains separate and is never cleared with the pending bucket.
        FlushAssetBucket(Management, Asset, Accumulator);
        if (Asset.bHasOutputCounter)
        {
            if (!Accumulator.bOutputBaselineEstablished)
            {
                Accumulator.LastObservedOutputActor = Asset.Actor;
                Accumulator.LastObservedProduced = Asset.ProducedCount;
                Accumulator.LastObservedGood = Asset.GoodCount;
                Accumulator.bOutputBaselineEstablished = true;
            }
            else if (Accumulator.LastObservedOutputActor.Get() != Asset.Actor
                || Asset.ProducedCount < Accumulator.LastObservedProduced
                || Asset.GoodCount < Accumulator.LastObservedGood)
            {
                // A replacement actor reused the persistent asset identity. Establish
                // a new runtime baseline; the durable management totals remain intact.
                Accumulator.LastObservedOutputActor = Asset.Actor;
                Accumulator.LastObservedProduced = Asset.ProducedCount;
                Accumulator.LastObservedGood = Asset.GoodCount;
            }
            else
            {
                const int64 ProducedDelta = Asset.ProducedCount
                    - Accumulator.LastObservedProduced;
                const int64 GoodDelta = FMath::Min(ProducedDelta,
                    Asset.GoodCount - Accumulator.LastObservedGood);
                Accumulator.ProducedInBucket += ProducedDelta;
                Accumulator.GoodInBucket += FMath::Max<int64>(0, GoodDelta);
                Accumulator.LastObservedProduced = Asset.ProducedCount;
                Accumulator.LastObservedGood = Asset.GoodCount;
            }
        }

        Accumulator.ElapsedSeconds += SampleSeconds;
        switch (Asset.TimeState)
        {
        case ELBRuntimeTimeState::Running:
            Accumulator.RunningSeconds += SampleSeconds;
            break;
        case ELBRuntimeTimeState::Starved:
            Accumulator.StarvedSeconds += SampleSeconds;
            break;
        case ELBRuntimeTimeState::Fault:
            Accumulator.FaultSeconds += SampleSeconds;
            break;
        case ELBRuntimeTimeState::Blocked:
        default:
            Accumulator.BlockedSeconds += SampleSeconds;
            break;
        }
        if (Accumulator.ElapsedSeconds + UE_DOUBLE_SMALL_NUMBER >= AnalyticsBucketSeconds)
        {
            StageAssetBucket(Management, Asset, Accumulator);
            FlushAssetBucket(Management, Asset, Accumulator);
        }
    }

    for (auto It = AssetAccumulators.CreateIterator(); It; ++It)
        if (!SeenAssets.Contains(It.Key())) It.RemoveCurrent();

    RewardFulfilledPanelOrders(World, Management);
}
