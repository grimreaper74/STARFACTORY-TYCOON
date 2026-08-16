#include "LBOneFactoryProductionFlow.h"

#include "Algo/AnyOf.h"

namespace LBOneFactoryProductionFlowPrivate
{
    constexpr int32 LedgerVersion = 1;
    constexpr int32 UnitVersion = 1;

    bool HasDuplicates(const TArray<ELBOneFactoryDepartment>& Values)
    {
        TSet<ELBOneFactoryDepartment> Unique;
        for (const ELBOneFactoryDepartment Value : Values)
        {
            if (Unique.Contains(Value)) return true;
            Unique.Add(Value);
        }
        return false;
    }

    bool IsTerminal(const FLBOneFactoryVehicleUnitState& Unit)
    {
        return Unit.Stage == ELBOneFactoryVehicleStage::Dispatched
            || Unit.QualityState == ELBOneFactoryVehicleQualityState::Scrapped;
    }

    bool IsUsableId(const FName Value)
    {
        return !Value.IsNone() && !Value.ToString().TrimStartAndEnd().IsEmpty();
    }
}

FLBOneFactoryProductionLedgerState
ULBOneFactoryProductionFlowLibrary::MakeEmptyLedger()
{
    FLBOneFactoryProductionLedgerState State;
    State.Version = LBOneFactoryProductionFlowPrivate::LedgerVersion;
    State.LedgerId = TEXT("MOORCROSS_ONE_FACTORY_PRODUCTION_LEDGER_V001");
    State.Revision = 0;
    State.NextVehicleSerial = 1;
    State.MaximumConcurrentWIP = 8;
    return State;
}

ELBOneFactoryDepartment ULBOneFactoryProductionFlowLibrary::GetDepartmentForStage(
    const ELBOneFactoryVehicleStage InStage)
{
    switch (InStage)
    {
    case ELBOneFactoryVehicleStage::InboundCoil:
    case ELBOneFactoryVehicleStage::BlankPreparation:
    case ELBOneFactoryVehicleStage::Pressing:
    case ELBOneFactoryVehicleStage::PressedPanelStillage:
        return ELBOneFactoryDepartment::Press;
    case ELBOneFactoryVehicleStage::BodyFraming:
    case ELBOneFactoryVehicleStage::BodyInWhite:
    case ELBOneFactoryVehicleStage::BodyQualityInspection:
        return ELBOneFactoryDepartment::Body;
    case ELBOneFactoryVehicleStage::Pretreatment:
    case ELBOneFactoryVehicleStage::EDCoat:
    case ELBOneFactoryVehicleStage::ColourCoat:
    case ELBOneFactoryVehicleStage::Cure:
    case ELBOneFactoryVehicleStage::PaintQualityInspection:
        return ELBOneFactoryDepartment::Paint;
    default:
        return ELBOneFactoryDepartment::Assembly;
    }
}

bool ULBOneFactoryProductionFlowLibrary::GetNextStage(
    const ELBOneFactoryVehicleStage InStage, ELBOneFactoryVehicleStage& OutStage)
{
    switch (InStage)
    {
    case ELBOneFactoryVehicleStage::InboundCoil:
        OutStage = ELBOneFactoryVehicleStage::BlankPreparation; return true;
    case ELBOneFactoryVehicleStage::BlankPreparation:
        OutStage = ELBOneFactoryVehicleStage::Pressing; return true;
    case ELBOneFactoryVehicleStage::Pressing:
        OutStage = ELBOneFactoryVehicleStage::PressedPanelStillage; return true;
    case ELBOneFactoryVehicleStage::PressedPanelStillage:
        OutStage = ELBOneFactoryVehicleStage::BodyFraming; return true;
    case ELBOneFactoryVehicleStage::BodyFraming:
        OutStage = ELBOneFactoryVehicleStage::BodyInWhite; return true;
    case ELBOneFactoryVehicleStage::BodyInWhite:
        OutStage = ELBOneFactoryVehicleStage::BodyQualityInspection; return true;
    case ELBOneFactoryVehicleStage::BodyQualityInspection:
        OutStage = ELBOneFactoryVehicleStage::Pretreatment; return true;
    case ELBOneFactoryVehicleStage::Pretreatment:
        OutStage = ELBOneFactoryVehicleStage::EDCoat; return true;
    case ELBOneFactoryVehicleStage::EDCoat:
        OutStage = ELBOneFactoryVehicleStage::ColourCoat; return true;
    case ELBOneFactoryVehicleStage::ColourCoat:
        OutStage = ELBOneFactoryVehicleStage::Cure; return true;
    case ELBOneFactoryVehicleStage::Cure:
        OutStage = ELBOneFactoryVehicleStage::PaintQualityInspection; return true;
    case ELBOneFactoryVehicleStage::PaintQualityInspection:
        OutStage = ELBOneFactoryVehicleStage::GeneralAssemblyTrim; return true;
    case ELBOneFactoryVehicleStage::GeneralAssemblyTrim:
        OutStage = ELBOneFactoryVehicleStage::PowertrainMarriage; return true;
    case ELBOneFactoryVehicleStage::PowertrainMarriage:
        OutStage = ELBOneFactoryVehicleStage::RollingChassis; return true;
    case ELBOneFactoryVehicleStage::RollingChassis:
        OutStage = ELBOneFactoryVehicleStage::EndOfLineInspection; return true;
    case ELBOneFactoryVehicleStage::EndOfLineInspection:
        OutStage = ELBOneFactoryVehicleStage::FinishedVehicle; return true;
    case ELBOneFactoryVehicleStage::FinishedVehicle:
        OutStage = ELBOneFactoryVehicleStage::Dispatched; return true;
    default:
        OutStage = ELBOneFactoryVehicleStage::Dispatched; return false;
    }
}

bool ULBOneFactoryProductionFlowLibrary::IsQualityGate(
    const ELBOneFactoryVehicleStage InStage)
{
    return InStage == ELBOneFactoryVehicleStage::BodyQualityInspection
        || InStage == ELBOneFactoryVehicleStage::PaintQualityInspection
        || InStage == ELBOneFactoryVehicleStage::EndOfLineInspection;
}

bool ULBOneFactoryProductionFlowLibrary::ValidateLedger(
    const FLBOneFactoryProductionLedgerState& State, FString& OutReason)
{
    using namespace LBOneFactoryProductionFlowPrivate;
    OutReason.Reset();
    if (State.Version != LedgerVersion
        || State.LedgerId != TEXT("MOORCROSS_ONE_FACTORY_PRODUCTION_LEDGER_V001"))
    {
        OutReason = TEXT("ONEFACTORY PRODUCTION LEDGER ID OR VERSION IS INVALID");
        return false;
    }
    if (State.Revision < 0 || State.NextVehicleSerial < 1
        || State.MaximumConcurrentWIP < 1 || State.MaximumConcurrentWIP > 64
        || State.CompletedVehicleCount < 0 || State.DispatchedVehicleCount < 0
        || State.DispatchedVehicleCount > State.CompletedVehicleCount)
    {
        OutReason = TEXT("ONEFACTORY PRODUCTION LEDGER COUNTERS ARE INVALID");
        return false;
    }
    if (HasDuplicates(State.FaultedDepartments)
        || HasDuplicates(State.OutputBlockedDepartments))
    {
        OutReason = TEXT("ONEFACTORY PRODUCTION RUNTIME GATES CONTAIN DUPLICATES");
        return false;
    }

    TSet<FName> UnitIds;
    TSet<FName> BuildOrderIds;
    TSet<FName> EvidenceIds;
    int32 ActiveCount = 0;
    int32 CompletedCount = 0;
    int32 DispatchedCount = 0;
    int32 MaximumObservedSerial = 0;
    for (const FLBOneFactoryVehicleUnitState& Unit : State.Units)
    {
        if (Unit.Version != UnitVersion || !IsUsableId(Unit.UnitId)
            || !IsUsableId(Unit.BuildOrderId) || !IsUsableId(Unit.VehicleModelId)
            || !IsUsableId(Unit.PaintProgrammeId) || !IsUsableId(Unit.PaintColourId)
            || !IsUsableId(Unit.CurrentStationId) || Unit.StageRevision < 0
            || Unit.SourceMaterialUnitIds.IsEmpty())
        {
            OutReason = TEXT("ONEFACTORY VEHICLE UNIT CORE CONTRACT IS INVALID");
            return false;
        }

        const bool bUsesAutomaticRuntime = Unit.RuntimeStationCursor >= 0;
        if (Unit.RuntimeStationCursor < -1
            || Unit.RuntimeCompletedStationCount < 0
            || Unit.RuntimeTotalStationCount < 0
            || !FMath::IsFinite(Unit.RuntimeCycleElapsedSeconds)
            || !FMath::IsFinite(Unit.RuntimeCycleDurationSeconds)
            || Unit.RuntimeCycleElapsedSeconds < 0.0f
            || Unit.RuntimeCycleDurationSeconds < 0.0f)
        {
            OutReason = TEXT("ONEFACTORY VEHICLE RUNTIME CURSOR OR CYCLE IS INVALID");
            return false;
        }
        if (!bUsesAutomaticRuntime)
        {
            if (Unit.RuntimeCompletedStationCount != 0
                || Unit.RuntimeTotalStationCount != 0
                || !FMath::IsNearlyZero(Unit.RuntimeCycleElapsedSeconds)
                || !FMath::IsNearlyZero(Unit.RuntimeCycleDurationSeconds)
                || !Unit.RuntimeTopologyId.IsNone()
                || !Unit.RuntimeCurrentAssignmentId.IsNone()
                || Unit.bRuntimeStarted)
            {
                OutReason = TEXT("ONEFACTORY LEGACY VEHICLE CLAIMS PARTIAL AUTOMATIC RUNTIME STATE");
                return false;
            }
        }
        else
        {
            const bool bAtRouteEnd =
                Unit.RuntimeStationCursor == Unit.RuntimeTotalStationCount;
            if (Unit.RuntimeTotalStationCount != 57
                || Unit.RuntimeStationCursor > Unit.RuntimeTotalStationCount
                || Unit.RuntimeCompletedStationCount
                    != Unit.RuntimeStationCursor
                || Unit.RuntimeTopologyId.IsNone()
                || (!bAtRouteEnd
                    && (Unit.RuntimeCurrentAssignmentId.IsNone()
                        || Unit.RuntimeCycleDurationSeconds <= 0.0f
                        || Unit.RuntimeCycleElapsedSeconds
                            > Unit.RuntimeCycleDurationSeconds + KINDA_SMALL_NUMBER))
                || (bAtRouteEnd
                    && (!FMath::IsNearlyZero(Unit.RuntimeCycleElapsedSeconds)
                        || !FMath::IsNearlyZero(Unit.RuntimeCycleDurationSeconds)
                        || Unit.bRuntimeStarted
                        || !Unit.bDispatched)))
            {
                OutReason = TEXT("ONEFACTORY AUTOMATIC RUNTIME STATE IS INCOHERENT");
                return false;
            }
            if (Unit.QualityState ==
                    ELBOneFactoryVehicleQualityState::Scrapped
                && Unit.bRuntimeStarted)
            {
                OutReason = TEXT("ONEFACTORY SCRAPPED VEHICLE CANNOT KEEP RUNNING");
                return false;
            }
        }
        if (UnitIds.Contains(Unit.UnitId) || BuildOrderIds.Contains(Unit.BuildOrderId))
        {
            OutReason = TEXT("ONEFACTORY VEHICLE OR BUILD-ORDER ID IS DUPLICATED");
            return false;
        }
        UnitIds.Add(Unit.UnitId);
        BuildOrderIds.Add(Unit.BuildOrderId);
        if (Unit.Department != GetDepartmentForStage(Unit.Stage))
        {
            OutReason = TEXT("ONEFACTORY VEHICLE STAGE AND DEPARTMENT DISAGREE");
            return false;
        }
        if (Unit.bDispatched != (Unit.Stage == ELBOneFactoryVehicleStage::Dispatched)
            || Unit.bDispatched && !Unit.bCompleted
            || Unit.bCompleted != (Unit.Stage == ELBOneFactoryVehicleStage::FinishedVehicle
                || Unit.Stage == ELBOneFactoryVehicleStage::Dispatched))
        {
            OutReason = TEXT("ONEFACTORY VEHICLE COMPLETION FLAGS DISAGREE WITH STAGE");
            return false;
        }
        if (Unit.QualityState == ELBOneFactoryVehicleQualityState::Pending
            && !IsQualityGate(Unit.Stage))
        {
            OutReason = TEXT("ONEFACTORY PENDING QUALITY EXISTS OUTSIDE AN INSPECTION GATE");
            return false;
        }
        TSet<FName> SourceIds;
        for (const FName SourceId : Unit.SourceMaterialUnitIds)
        {
            if (!IsUsableId(SourceId) || SourceIds.Contains(SourceId))
            {
                OutReason = TEXT("ONEFACTORY SOURCE MATERIAL ID IS INVALID OR DUPLICATED");
                return false;
            }
            SourceIds.Add(SourceId);
        }
        for (const FName EvidenceId : Unit.EvidenceIds)
        {
            if (!IsUsableId(EvidenceId) || EvidenceIds.Contains(EvidenceId))
            {
                OutReason = TEXT("ONEFACTORY PROCESS EVIDENCE ID IS INVALID OR DUPLICATED");
                return false;
            }
            EvidenceIds.Add(EvidenceId);
        }
        if (!IsTerminal(Unit)) ++ActiveCount;
        if (Unit.bCompleted) ++CompletedCount;
        if (Unit.bDispatched) ++DispatchedCount;

        FString Prefix;
        FString SerialText;
        if (Unit.UnitId.ToString().Split(TEXT("-"), &Prefix, &SerialText,
            ESearchCase::IgnoreCase, ESearchDir::FromEnd))
        {
            MaximumObservedSerial = FMath::Max(MaximumObservedSerial,
                FCString::Atoi(*SerialText));
        }
    }
    if (ActiveCount > State.MaximumConcurrentWIP
        || CompletedCount != State.CompletedVehicleCount
        || DispatchedCount != State.DispatchedVehicleCount
        || State.NextVehicleSerial <= MaximumObservedSerial)
    {
        OutReason = TEXT("ONEFACTORY PRODUCTION COUNTERS DISAGREE WITH VEHICLE RECORDS");
        return false;
    }
    OutReason = TEXT("ONEFACTORY PRODUCTION LEDGER VALID");
    return true;
}

ALBOneFactoryProductionFlowAuthority::ALBOneFactoryProductionFlowAuthority()
{
    PrimaryActorTick.bCanEverTick = false;
    bReplicates = false;
    CurrentState = ULBOneFactoryProductionFlowLibrary::MakeEmptyLedger();
    Tags.AddUnique(GetAuthorityTag());
    Tags.AddUnique(TEXT("LB.Provenance.NativeOnly"));
}

FName ALBOneFactoryProductionFlowAuthority::GetAuthorityTag()
{
    return TEXT("LB.OneFactory.ProductionFlow.Authority.v001");
}

FLBOneFactoryVehicleUnitState* ALBOneFactoryProductionFlowAuthority::FindUnit(
    const FName UnitId)
{
    return CurrentState.Units.FindByPredicate(
        [UnitId](const FLBOneFactoryVehicleUnitState& Unit)
        { return Unit.UnitId == UnitId; });
}

const FLBOneFactoryVehicleUnitState* ALBOneFactoryProductionFlowAuthority::FindUnit(
    const FName UnitId) const
{
    return CurrentState.Units.FindByPredicate(
        [UnitId](const FLBOneFactoryVehicleUnitState& Unit)
        { return Unit.UnitId == UnitId; });
}

bool ALBOneFactoryProductionFlowAuthority::RestoreLedger(
    const FLBOneFactoryProductionLedgerState& State, FString& OutReason)
{
    if (!ULBOneFactoryProductionFlowLibrary::ValidateLedger(State, OutReason))
        return false;
    CurrentState = State;
    OutReason = TEXT("ONEFACTORY PRODUCTION LEDGER RESTORED");
    return true;
}

bool ALBOneFactoryProductionFlowAuthority::IsDepartmentCommissioned(
    const ELBOneFactoryDepartment InDepartment) const
{
    switch (InDepartment)
    {
    case ELBOneFactoryDepartment::Press:
        return CurrentState.Commissioning.bPressCommissioned;
    case ELBOneFactoryDepartment::Body:
        return CurrentState.Commissioning.bBodyCommissioned;
    case ELBOneFactoryDepartment::Paint:
        return CurrentState.Commissioning.bPaintCommissioned;
    default:
        return CurrentState.Commissioning.bAssemblyCommissioned;
    }
}

bool ALBOneFactoryProductionFlowAuthority::HasActiveWIPInDepartment(
    const ELBOneFactoryDepartment InDepartment) const
{
    return Algo::AnyOf(CurrentState.Units,
        [InDepartment](const FLBOneFactoryVehicleUnitState& Unit)
        {
            return Unit.Department == InDepartment
                && Unit.Stage != ELBOneFactoryVehicleStage::Dispatched
                && Unit.QualityState != ELBOneFactoryVehicleQualityState::Scrapped;
        });
}

bool ALBOneFactoryProductionFlowAuthority::SetDepartmentCommissioned(
    const ELBOneFactoryDepartment InDepartment, const bool bCommissioned,
    FString& OutReason)
{
    if (!bCommissioned && HasActiveWIPInDepartment(InDepartment))
    {
        OutReason = TEXT("ONEFACTORY DEPARTMENT CANNOT DECOMMISSION WITH ACTIVE WIP");
        return false;
    }
    bool* Target = nullptr;
    switch (InDepartment)
    {
    case ELBOneFactoryDepartment::Press:
        Target = &CurrentState.Commissioning.bPressCommissioned; break;
    case ELBOneFactoryDepartment::Body:
        Target = &CurrentState.Commissioning.bBodyCommissioned; break;
    case ELBOneFactoryDepartment::Paint:
        Target = &CurrentState.Commissioning.bPaintCommissioned; break;
    default:
        Target = &CurrentState.Commissioning.bAssemblyCommissioned; break;
    }
    if (*Target != bCommissioned)
    {
        *Target = bCommissioned;
        ++CurrentState.Revision;
    }
    OutReason = bCommissioned
        ? TEXT("ONEFACTORY DEPARTMENT COMMISSIONED")
        : TEXT("ONEFACTORY DEPARTMENT DECOMMISSIONED");
    return true;
}

bool ALBOneFactoryProductionFlowAuthority::SetLinePaused(
    const bool bPaused, FString& OutReason)
{
    if (CurrentState.bLinePaused != bPaused)
    {
        CurrentState.bLinePaused = bPaused;
        ++CurrentState.Revision;
    }
    OutReason = bPaused ? TEXT("ONEFACTORY PRODUCTION PAUSED")
                        : TEXT("ONEFACTORY PRODUCTION RESUMED");
    return true;
}

bool ALBOneFactoryProductionFlowAuthority::SetDepartmentFaulted(
    const ELBOneFactoryDepartment InDepartment, const bool bFaulted,
    FString& OutReason)
{
    const bool bContains = CurrentState.FaultedDepartments.Contains(InDepartment);
    if (bFaulted && !bContains)
    {
        CurrentState.FaultedDepartments.Add(InDepartment);
        ++CurrentState.Revision;
    }
    else if (!bFaulted && bContains)
    {
        CurrentState.FaultedDepartments.Remove(InDepartment);
        ++CurrentState.Revision;
    }
    OutReason = bFaulted ? TEXT("ONEFACTORY DEPARTMENT FAULTED")
                         : TEXT("ONEFACTORY DEPARTMENT FAULT CLEARED");
    return true;
}

bool ALBOneFactoryProductionFlowAuthority::SetDepartmentOutputBlocked(
    const ELBOneFactoryDepartment InDepartment, const bool bBlocked,
    FString& OutReason)
{
    const bool bContains = CurrentState.OutputBlockedDepartments.Contains(InDepartment);
    if (bBlocked && !bContains)
    {
        CurrentState.OutputBlockedDepartments.Add(InDepartment);
        ++CurrentState.Revision;
    }
    else if (!bBlocked && bContains)
    {
        CurrentState.OutputBlockedDepartments.Remove(InDepartment);
        ++CurrentState.Revision;
    }
    OutReason = bBlocked ? TEXT("ONEFACTORY DEPARTMENT OUTPUT BLOCKED")
                         : TEXT("ONEFACTORY DEPARTMENT OUTPUT RELEASED");
    return true;
}

int32 ALBOneFactoryProductionFlowAuthority::GetActiveWIPCount() const
{
    int32 Count = 0;
    for (const FLBOneFactoryVehicleUnitState& Unit : CurrentState.Units)
    {
        if (Unit.Stage != ELBOneFactoryVehicleStage::Dispatched
            && Unit.QualityState != ELBOneFactoryVehicleQualityState::Scrapped)
            ++Count;
    }
    return Count;
}

bool ALBOneFactoryProductionFlowAuthority::EvidenceIdExists(
    const FName EvidenceId) const
{
    return Algo::AnyOf(CurrentState.Units,
        [EvidenceId](const FLBOneFactoryVehicleUnitState& Unit)
        { return Unit.EvidenceIds.Contains(EvidenceId); });
}

bool ALBOneFactoryProductionFlowAuthority::CreateVehicleOrder(
    const FName BuildOrderId, const FName VehicleModelId,
    const FName PaintProgrammeId, const FName PaintColourId,
    const FName SourceCoilLotId, const FName InboundStationId,
    FName& OutUnitId, FString& OutReason)
{
    OutUnitId = NAME_None;
    if (!IsDepartmentCommissioned(ELBOneFactoryDepartment::Press))
    {
        OutReason = TEXT("ONEFACTORY PRESS MUST BE COMMISSIONED BEFORE A VEHICLE ORDER");
        return false;
    }
    if (CurrentState.bLinePaused
        || CurrentState.FaultedDepartments.Contains(ELBOneFactoryDepartment::Press)
        || CurrentState.OutputBlockedDepartments.Contains(ELBOneFactoryDepartment::Press))
    {
        OutReason = TEXT("ONEFACTORY PRESS RUNTIME GATE BLOCKS A NEW VEHICLE ORDER");
        return false;
    }
    if (BuildOrderId.IsNone() || VehicleModelId.IsNone() || PaintProgrammeId.IsNone()
        || PaintColourId.IsNone() || SourceCoilLotId.IsNone()
        || InboundStationId.IsNone())
    {
        OutReason = TEXT("ONEFACTORY VEHICLE ORDER REQUIRES COMPLETE IDENTITY");
        return false;
    }
    if (CurrentState.Units.ContainsByPredicate(
        [BuildOrderId](const FLBOneFactoryVehicleUnitState& Unit)
        { return Unit.BuildOrderId == BuildOrderId; }))
    {
        OutReason = TEXT("ONEFACTORY BUILD ORDER ID ALREADY EXISTS");
        return false;
    }
    if (GetActiveWIPCount() >= CurrentState.MaximumConcurrentWIP)
    {
        OutReason = TEXT("ONEFACTORY MAXIMUM CONCURRENT WIP REACHED");
        return false;
    }

    FLBOneFactoryVehicleUnitState Unit;
    Unit.Version = LBOneFactoryProductionFlowPrivate::UnitVersion;
    Unit.UnitId = FName(*FString::Printf(TEXT("%s-%06d"),
        *VehicleModelId.ToString(), CurrentState.NextVehicleSerial));
    Unit.BuildOrderId = BuildOrderId;
    Unit.VehicleModelId = VehicleModelId;
    Unit.PaintProgrammeId = PaintProgrammeId;
    Unit.PaintColourId = PaintColourId;
    Unit.Stage = ELBOneFactoryVehicleStage::InboundCoil;
    Unit.Department = ELBOneFactoryDepartment::Press;
    Unit.CurrentStationId = InboundStationId;
    Unit.SourceMaterialUnitIds.Add(SourceCoilLotId);
    CurrentState.Units.Add(Unit);
    OutUnitId = Unit.UnitId;
    ++CurrentState.NextVehicleSerial;
    ++CurrentState.Revision;
    OutReason = TEXT("ONEFACTORY VEHICLE ORDER CREATED");
    return true;
}

bool ALBOneFactoryProductionFlowAuthority::AdvanceVehicle(
    const FName UnitId, const FName TargetStationId, const FName EvidenceId,
    FString& OutReason)
{
    FLBOneFactoryVehicleUnitState* Unit = FindUnit(UnitId);
    if (!Unit || TargetStationId.IsNone() || EvidenceId.IsNone())
    {
        OutReason = TEXT("ONEFACTORY VEHICLE ADVANCE IDENTITY IS INVALID");
        return false;
    }
    ELBOneFactoryVehicleStage NextStage;
    if (!ULBOneFactoryProductionFlowLibrary::GetNextStage(Unit->Stage, NextStage))
    {
        OutReason = TEXT("ONEFACTORY VEHICLE IS ALREADY DISPATCHED");
        return false;
    }
    if (ULBOneFactoryProductionFlowLibrary::IsQualityGate(Unit->Stage)
        && Unit->QualityState != ELBOneFactoryVehicleQualityState::Passed)
    {
        OutReason = TEXT("ONEFACTORY VEHICLE CANNOT LEAVE AN UNPASSED QUALITY GATE");
        return false;
    }
    if (Unit->QualityState == ELBOneFactoryVehicleQualityState::Rejected
        || Unit->QualityState == ELBOneFactoryVehicleQualityState::Scrapped
        || Unit->QualityState == ELBOneFactoryVehicleQualityState::ReworkRequired)
    {
        OutReason = TEXT("ONEFACTORY VEHICLE QUALITY STATE BLOCKS ADVANCE");
        return false;
    }
    const ELBOneFactoryDepartment TargetDepartment =
        ULBOneFactoryProductionFlowLibrary::GetDepartmentForStage(NextStage);
    if (CurrentState.bLinePaused
        || !IsDepartmentCommissioned(Unit->Department)
        || !IsDepartmentCommissioned(TargetDepartment)
        || CurrentState.FaultedDepartments.Contains(Unit->Department)
        || CurrentState.FaultedDepartments.Contains(TargetDepartment)
        || CurrentState.OutputBlockedDepartments.Contains(Unit->Department))
    {
        OutReason = TEXT("ONEFACTORY COMMISSION, PAUSE, FAULT OR OUTPUT GATE BLOCKS ADVANCE");
        return false;
    }
    if (EvidenceIdExists(EvidenceId))
    {
        OutReason = TEXT("ONEFACTORY PROCESS EVIDENCE ID ALREADY EXISTS");
        return false;
    }

    Unit->Stage = NextStage;
    Unit->Department = TargetDepartment;
    Unit->CurrentStationId = TargetStationId;
    Unit->EvidenceIds.Add(EvidenceId);
    Unit->QualityState = ULBOneFactoryProductionFlowLibrary::IsQualityGate(NextStage)
        ? ELBOneFactoryVehicleQualityState::Pending
        : Unit->QualityState;
    ++Unit->StageRevision;
    if (NextStage == ELBOneFactoryVehicleStage::FinishedVehicle)
    {
        Unit->bCompleted = true;
        ++CurrentState.CompletedVehicleCount;
    }
    else if (NextStage == ELBOneFactoryVehicleStage::Dispatched)
    {
        Unit->bDispatched = true;
        ++CurrentState.DispatchedVehicleCount;
    }
    ++CurrentState.Revision;
    OutReason = TEXT("ONEFACTORY VEHICLE ADVANCED");
    return true;
}

bool ALBOneFactoryProductionFlowAuthority::SubmitQualityResult(
    const FName UnitId, const ELBOneFactoryVehicleQualityState InQualityState,
    const FName EvidenceId, FString& OutReason)
{
    FLBOneFactoryVehicleUnitState* Unit = FindUnit(UnitId);
    if (!Unit || !ULBOneFactoryProductionFlowLibrary::IsQualityGate(Unit->Stage)
        || Unit->QualityState != ELBOneFactoryVehicleQualityState::Pending
        || EvidenceId.IsNone() || EvidenceIdExists(EvidenceId)
        || (InQualityState != ELBOneFactoryVehicleQualityState::Passed
            && InQualityState != ELBOneFactoryVehicleQualityState::ReworkRequired
            && InQualityState != ELBOneFactoryVehicleQualityState::Rejected
            && InQualityState != ELBOneFactoryVehicleQualityState::Scrapped))
    {
        OutReason = TEXT("ONEFACTORY QUALITY RESULT IS INVALID FOR THE CURRENT GATE");
        return false;
    }
    Unit->QualityState = InQualityState;
    Unit->EvidenceIds.Add(EvidenceId);
    ++Unit->StageRevision;
    ++CurrentState.Revision;
    OutReason = TEXT("ONEFACTORY QUALITY RESULT RECORDED");
    return true;
}

bool ALBOneFactoryProductionFlowAuthority::ResetQualityAfterRework(
    const FName UnitId, const FName EvidenceId, FString& OutReason)
{
    FLBOneFactoryVehicleUnitState* Unit = FindUnit(UnitId);
    if (!Unit || !ULBOneFactoryProductionFlowLibrary::IsQualityGate(Unit->Stage)
        || Unit->QualityState != ELBOneFactoryVehicleQualityState::ReworkRequired
        || EvidenceId.IsNone() || EvidenceIdExists(EvidenceId))
    {
        OutReason = TEXT("ONEFACTORY REWORK RESET IS INVALID FOR THE CURRENT UNIT");
        return false;
    }
    Unit->QualityState = ELBOneFactoryVehicleQualityState::Pending;
    Unit->EvidenceIds.Add(EvidenceId);
    ++Unit->StageRevision;
    ++CurrentState.Revision;
    OutReason = TEXT("ONEFACTORY QUALITY RESET AFTER REWORK");
    return true;
}
