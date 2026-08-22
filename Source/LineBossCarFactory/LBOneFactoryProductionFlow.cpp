#include "LBOneFactoryProductionFlow.h"

#include "LBVehiclePanelCatalog.h"

#include "Algo/AnyOf.h"
#include "Misc/Crc.h"

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

    bool HasDuplicatePanelIds(const TArray<FName>& Values)
    {
        TSet<FName> Unique;
        for (const FName Value : Values)
        {
            if (Value.IsNone() || Unique.Contains(Value)) return true;
            Unique.Add(Value);
        }
        return false;
    }

    bool IsProductionReadyRecipe(const FLBVehicleModelRecipe* Recipe)
    {
        return Recipe && LBVehicleModelCatalog::IsProductionReady(*Recipe);
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

    bool HasExactPanelSet(const TArray<FName>& Expected, const TArray<FName>& Actual)
    {
        if (Expected.Num() != Actual.Num() || Expected.IsEmpty()) return false;
        TSet<FName> ExpectedSet;
        TSet<FName> ActualSet;
        for (const FName Id : Expected)
        {
            if (!IsUsableId(Id) || ExpectedSet.Contains(Id)) return false;
            ExpectedSet.Add(Id);
        }
        for (const FName Id : Actual)
        {
            if (!IsUsableId(Id) || ActualSet.Contains(Id) || !ExpectedSet.Contains(Id)) return false;
            ActualSet.Add(Id);
        }
        return ActualSet.Num() == ExpectedSet.Num();
    }

    bool StageRequiresStampedPanelBOM(const ELBOneFactoryVehicleStage Stage)
    {
        return static_cast<uint8>(Stage)
            >= static_cast<uint8>(ELBOneFactoryVehicleStage::BodyFraming);
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

    TMap<FName, const FLBOneFactoryVehicleContract*> ContractsById;
    for (const FLBOneFactoryVehicleContract& Contract : State.Contracts)
    {
        if (!IsUsableId(Contract.ContractId)
            || !IsUsableId(Contract.VehicleModelId)
            || Contract.Quantity <= 0 || Contract.PricePerVehiclePence <= 0
            || Contract.DispatchedCount < 0
            || Contract.DispatchedCount > Contract.Quantity
            || !FMath::IsFinite(Contract.DeadlineSimSeconds)
            || ContractsById.Contains(Contract.ContractId))
        {
            OutReason = TEXT("ONEFACTORY CONTRACT IDENTITY OR QUANTITY IS INVALID");
            return false;
        }
        const FLBVehicleModelRecipe* Recipe =
            LBVehicleModelCatalog::Find(Contract.VehicleModelId);
        if (!LBOneFactoryProductionFlowPrivate::IsProductionReadyRecipe(Recipe))
        {
            OutReason = TEXT("ONEFACTORY CONTRACT REFERENCES AN UNKNOWN OR UNVALIDATED VEHICLE PROGRAMME");
            return false;
        }
        const bool bStateIsCoherent =
            (Contract.State == ELBOneFactoryContractState::Open
                && Contract.DispatchedCount < Contract.Quantity)
            || (Contract.State == ELBOneFactoryContractState::Complete
                && Contract.DispatchedCount == Contract.Quantity)
            || (Contract.State == ELBOneFactoryContractState::Expired
                && Contract.DispatchedCount < Contract.Quantity);
        if (!bStateIsCoherent)
        {
            OutReason = TEXT("ONEFACTORY CONTRACT STATE AND DISPATCH COUNT DISAGREE");
            return false;
        }
        ContractsById.Add(Contract.ContractId, &Contract);
    }

    TMap<FName, int32> FulfilledContractCounts;
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

        if (!Unit.RequiredPanelTypeIds.IsEmpty())
        {
            // The order owns its BOM. Looking it up from the mutable catalogue
            // here would rewrite historic WIP when a future recipe is revised.
            if (Unit.RequiredPanelTypeIds.Contains(NAME_None)
                || HasDuplicatePanelIds(Unit.RequiredPanelTypeIds)
                || (!HasExactPanelSet(Unit.RequiredPanelTypeIds,
                    Unit.PressedPanelTypeIds)
                    && StageRequiresStampedPanelBOM(Unit.Stage)))
            {
                OutReason = TEXT("ONEFACTORY VEHICLE PANEL BOM IS MISSING OR DUPLICATED");
                return false;
            }
        }
        else if (!Unit.PressedPanelTypeIds.IsEmpty())
        {
            OutReason = TEXT("ONEFACTORY VEHICLE HAS STAMPED PANELS WITHOUT A MODEL BOM");
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
        if (!Unit.FulfilledContractId.IsNone())
        {
            const FLBOneFactoryVehicleContract* const* Contract =
                ContractsById.Find(Unit.FulfilledContractId);
            if (!Unit.bDispatched || !Contract || !*Contract
                || (*Contract)->VehicleModelId != Unit.VehicleModelId
                || (*Contract)->State == ELBOneFactoryContractState::Expired)
            {
                OutReason = TEXT("ONEFACTORY UNIT CONTRACT SETTLEMENT IS INVALID");
                return false;
            }
            ++FulfilledContractCounts.FindOrAdd(Unit.FulfilledContractId);
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
    for (const FLBOneFactoryVehicleContract& Contract : State.Contracts)
    {
        if (FulfilledContractCounts.FindRef(Contract.ContractId)
            != Contract.DispatchedCount)
        {
            OutReason = TEXT("ONEFACTORY CONTRACT DISPATCH COUNT DOES NOT MATCH UNIT SETTLEMENTS");
            return false;
        }
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

bool ALBOneFactoryProductionFlowAuthority::AdvanceSimulationClock(
    const float DeltaSeconds, FString& OutReason)
{
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.0f)
    {
        OutReason = TEXT("ONEFACTORY CLOCK DELTA MUST BE FINITE AND POSITIVE");
        return false;
    }
    if (CurrentState.bLinePaused)
    {
        OutReason = TEXT("ONEFACTORY CLOCK HELD: LINE PAUSED");
        return true;
    }
    CurrentState.SimClockSeconds += DeltaSeconds;
    ++CurrentState.Revision;
    OutReason = TEXT("ONEFACTORY CLOCK ADVANCED");
    return true;
}

bool ULBOneFactoryProductionFlowLibrary::IsDefectSuspected(
    const FName UnitId, const double FleetWear01)
{
    if (UnitId.IsNone() || FleetWear01 <= 0.0)
    {
        return false;
    }
    const double Clamped = FMath::Clamp(FleetWear01, 0.0, 1.0);
    const int32 Threshold = FMath::RoundToInt(Clamped * 40.0);
    const uint32 Hash = FCrc::StrCrc32(*UnitId.ToString());
    return static_cast<int32>(Hash % 100u) < Threshold;
}

bool ALBOneFactoryProductionFlowAuthority::PerformPlantMaintenance(
    FString& OutReason)
{
    CurrentState.FleetWear01 = 0.0;
    ++CurrentState.MaintenanceSerial;
    ++CurrentState.Revision;
    OutReason = FString::Printf(
        TEXT("ONEFACTORY PLANT MAINTENANCE %d COMPLETE; FLEET WEAR RESET"),
        CurrentState.MaintenanceSerial);
    return true;
}

bool ALBOneFactoryProductionFlowAuthority::AddVehicleContract(
    const FLBOneFactoryVehicleContract& Contract, FString& OutReason)
{
    if (Contract.ContractId.IsNone() || Contract.VehicleModelId.IsNone()
        || Contract.Quantity <= 0 || Contract.PricePerVehiclePence <= 0)
    {
        OutReason = TEXT("ONEFACTORY CONTRACT REQUIRES ID, MODEL, QUANTITY AND PRICE");
        return false;
    }
    const FLBVehicleModelRecipe* Recipe =
        LBVehicleModelCatalog::Find(Contract.VehicleModelId);
    if (!LBOneFactoryProductionFlowPrivate::IsProductionReadyRecipe(Recipe))
    {
        OutReason = TEXT("ONEFACTORY CONTRACT REQUIRES A REGISTERED VEHICLE PROGRAMME WITH VALIDATED PANEL GEOMETRY");
        return false;
    }
    if (CurrentState.Contracts.ContainsByPredicate(
        [&Contract](const FLBOneFactoryVehicleContract& Existing)
        { return Existing.ContractId == Contract.ContractId; }))
    {
        OutReason = TEXT("ONEFACTORY CONTRACT ALREADY EXISTS");
        return true;
    }
    FLBOneFactoryVehicleContract Added = Contract;
    Added.DispatchedCount = 0;
    Added.State = ELBOneFactoryContractState::Open;
    CurrentState.Contracts.Add(Added);
    ++CurrentState.Revision;
    OutReason = TEXT("ONEFACTORY CONTRACT ADDED");
    return true;
}

int32 ALBOneFactoryProductionFlowAuthority::SweepContractDeadlines(
    FString& OutReason)
{
    int32 Expired = 0;
    for (FLBOneFactoryVehicleContract& Contract : CurrentState.Contracts)
    {
        if (Contract.State == ELBOneFactoryContractState::Open
            && Contract.DeadlineSimSeconds > 0.0
            && CurrentState.SimClockSeconds > Contract.DeadlineSimSeconds)
        {
            Contract.State = ELBOneFactoryContractState::Expired;
            ++Expired;
        }
    }
    if (Expired > 0)
    {
        // Soft failure: a missed deadline costs standing, never the game.
        CurrentState.ReputationScore =
            FMath::Max(0, CurrentState.ReputationScore - 5 * Expired);
        ++CurrentState.Revision;
    }
    OutReason = FString::Printf(
        TEXT("ONEFACTORY CONTRACT SWEEP EXPIRED %d"), Expired);
    return Expired;
}

bool ALBOneFactoryProductionFlowAuthority::ApplyFinancialPolicy(
    const int64 CashBalancePence, FString& OutReason)
{
    // GBP 250k floor gives the player warning room before the crisis.
    constexpr int64 WarningFloorPence = 25000000;
    const ELBOneFactoryFinancialState NewState =
        CashBalancePence < 0 ? ELBOneFactoryFinancialState::Emergency
        : CashBalancePence < WarningFloorPence
            ? ELBOneFactoryFinancialState::Warning
            : ELBOneFactoryFinancialState::Healthy;
    if (NewState != CurrentState.FinancialState)
    {
        CurrentState.FinancialState = NewState;
        ++CurrentState.Revision;
    }
    if (NewState != ELBOneFactoryFinancialState::Emergency)
    {
        OutReason = TEXT("ONEFACTORY FINANCES INSIDE POLICY");
        return true;
    }
    // One open rescue offer at a time: premium price, short deadline,
    // and a real reputation cost.
    const bool bRescueOpen = CurrentState.Contracts.ContainsByPredicate(
        [](const FLBOneFactoryVehicleContract& Contract)
        { return Contract.bEmergency
              && Contract.State == ELBOneFactoryContractState::Open; });
    if (bRescueOpen)
    {
        OutReason = TEXT("ONEFACTORY EMERGENCY RESCUE ALREADY OPEN");
        return true;
    }
    const TArray<FLBVehicleModelRecipe>& Recipes = LBVehicleModelCatalog::GetRecipes();
    TArray<const FLBVehicleModelRecipe*> EligibleRecipes;
    for (const FLBVehicleModelRecipe& Recipe : Recipes)
    {
        if (LBOneFactoryProductionFlowPrivate::IsProductionReadyRecipe(&Recipe))
        {
            EligibleRecipes.Add(&Recipe);
        }
    }
    if (EligibleRecipes.IsEmpty())
    {
        OutReason = TEXT("ONEFACTORY EMERGENCY RESCUE REQUIRES A REGISTERED VEHICLE PROGRAMME");
        return false;
    }
    const int32 RescueProgrammeIndex = CurrentState.EmergencyContractSerial
        % EligibleRecipes.Num();
    const FLBVehicleModelRecipe& RescueRecipe = *EligibleRecipes[RescueProgrammeIndex];
    FLBOneFactoryVehicleContract Rescue;
    Rescue.ContractId = FName(*FString::Printf(TEXT("CON_EMERGENCY_%d"),
        ++CurrentState.EmergencyContractSerial));
    // Emergency work must come from the same catalogue as normal contracts.
    // This keeps additional programmes economically real instead of relegating
    // them to a UI-only selection.
    Rescue.VehicleModelId = RescueRecipe.ModelId;
    Rescue.Quantity = 6;
    Rescue.PricePerVehiclePence = 4200000;
    Rescue.DeadlineSimSeconds = CurrentState.SimClockSeconds + 6.0 * 3600.0;
    Rescue.bEmergency = true;
    FString AddReason;
    if (!AddVehicleContract(Rescue, AddReason))
    {
        OutReason = AddReason;
        return false;
    }
    CurrentState.ReputationScore =
        FMath::Max(0, CurrentState.ReputationScore - 10);
    ++CurrentState.Revision;
    OutReason = TEXT("ONEFACTORY EMERGENCY RESCUE CONTRACT OFFERED");
    return true;
}

bool ALBOneFactoryProductionFlowAuthority::SeedStarterContracts(
    FString& OutReason)
{
    // The sandbox's opening chain: volumes and prices escalate, and every
    // deadline is generous at 1x speed - soft pressure, not a fail wall.
    struct FSeed
    {
        const TCHAR* Id;
        int32 Quantity;
        int64 PricePence;
        double DeadlineSeconds;
    };
    static const FSeed Seeds[] = {
        { TEXT("CON_STARTER_1"), 3, 3000000, 4.0 * 3600.0 },
        { TEXT("CON_STARTER_2"), 5, 3300000, 10.0 * 3600.0 },
        { TEXT("CON_STARTER_3"), 8, 3600000, 20.0 * 3600.0 },
    };
    const TArray<FLBVehicleModelRecipe>& Recipes = LBVehicleModelCatalog::GetRecipes();
    TArray<const FLBVehicleModelRecipe*> EligibleRecipes;
    for (const FLBVehicleModelRecipe& Recipe : Recipes)
    {
        if (LBOneFactoryProductionFlowPrivate::IsProductionReadyRecipe(&Recipe))
        {
            EligibleRecipes.Add(&Recipe);
        }
    }
    if (EligibleRecipes.IsEmpty())
    {
        OutReason = TEXT("ONEFACTORY STARTER CONTRACTS REQUIRE A REGISTERED VEHICLE PROGRAMME");
        return false;
    }
    for (int32 SeedIndex = 0; SeedIndex < UE_ARRAY_COUNT(Seeds); ++SeedIndex)
    {
        const FSeed& Seed = Seeds[SeedIndex];
        const FLBVehicleModelRecipe& Recipe =
            *EligibleRecipes[SeedIndex % EligibleRecipes.Num()];
        FLBOneFactoryVehicleContract Contract;
        Contract.ContractId = FName(Seed.Id);
        // A factory-management game needs contracts to expose the programmes
        // the plant can actually retool for.  The starter ladder therefore
        // rotates deterministically through the registered catalogue instead
        // of silently keeping every order on the original development car.
        Contract.VehicleModelId = Recipe.ModelId;
        Contract.Quantity = Seed.Quantity;
        Contract.PricePerVehiclePence = Seed.PricePence;
        Contract.DeadlineSimSeconds =
            CurrentState.SimClockSeconds + Seed.DeadlineSeconds;
        FString AddReason;
        if (!AddVehicleContract(Contract, AddReason))
        {
            OutReason = AddReason;
            return false;
        }
    }
    OutReason = TEXT("ONEFACTORY STARTER CONTRACTS SEEDED");
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
    const FLBVehicleModelRecipe* Recipe = LBVehicleModelCatalog::Find(VehicleModelId);
    if (!LBOneFactoryProductionFlowPrivate::IsProductionReadyRecipe(Recipe))
    {
        OutReason = TEXT("ONEFACTORY VEHICLE MODEL REQUIRES VALIDATED PANEL GEOMETRY AND A REGISTERED RECIPE REVISION");
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
    Unit.VehicleRecipeRevisionId = Recipe->RecipeRevisionId;
    Unit.PaintProgrammeId = PaintProgrammeId;
    Unit.PaintColourId = PaintColourId;
    Unit.Stage = ELBOneFactoryVehicleStage::InboundCoil;
    Unit.Department = ELBOneFactoryDepartment::Press;
    Unit.CurrentStationId = InboundStationId;
    Unit.CreatedAtSimSeconds = CurrentState.SimClockSeconds;
    Unit.SourceMaterialUnitIds.Add(SourceCoilLotId);
    const TArray<FLBStampedPanelDefinition>& RequiredPanels = Recipe->RequiredPanels;
    Unit.RequiredPanelTypeIds.Reserve(RequiredPanels.Num());
    for (const FLBStampedPanelDefinition& Panel : RequiredPanels)
    {
        Unit.RequiredPanelTypeIds.Add(Panel.PanelTypeId);
    }
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

    TArray<FName> PanelEvidenceIds;
    if (Unit->Stage == ELBOneFactoryVehicleStage::Pressing
        && NextStage == ELBOneFactoryVehicleStage::PressedPanelStillage
        && !Unit->RequiredPanelTypeIds.IsEmpty())
    {
        if (!Unit->PressedPanelTypeIds.IsEmpty()
            || Unit->RequiredPanelTypeIds.Contains(NAME_None)
            || LBOneFactoryProductionFlowPrivate::HasDuplicatePanelIds(
                Unit->RequiredPanelTypeIds))
        {
            OutReason = TEXT("ONEFACTORY PRESS CANNOT STAMP AN INVALID OR ALREADY-STAMPED ORDER PANEL BOM");
            return false;
        }
        for (const FName PanelId : Unit->RequiredPanelTypeIds)
        {
            const FName PanelEvidence(*FString::Printf(
                TEXT("OF_%s_PANEL_%s_STAMPED"), *Unit->UnitId.ToString(),
                *PanelId.ToString()));
            if (EvidenceIdExists(PanelEvidence))
            {
                OutReason = TEXT("ONEFACTORY PRESS PANEL BOM EVIDENCE IS DUPLICATED");
                return false;
            }
            PanelEvidenceIds.Add(PanelEvidence);
        }
    }

    Unit->Stage = NextStage;
    Unit->Department = TargetDepartment;
    Unit->CurrentStationId = TargetStationId;
    Unit->EvidenceIds.Add(EvidenceId);
    if (!PanelEvidenceIds.IsEmpty())
    {
        Unit->PressedPanelTypeIds = Unit->RequiredPanelTypeIds;
        Unit->EvidenceIds.Append(PanelEvidenceIds);
    }
    if (ULBOneFactoryProductionFlowLibrary::IsQualityGate(NextStage))
    {
        Unit->QualityState = ELBOneFactoryVehicleQualityState::Pending;
        Unit->bDefectSuspected =
            ULBOneFactoryProductionFlowLibrary::IsDefectSuspected(
                Unit->UnitId, CurrentState.FleetWear01);
    }
    // Every completed station cycle wears the fleet a little; maintenance
    // is the counter-pressure.
    CurrentState.FleetWear01 =
        FMath::Min(1.0, CurrentState.FleetWear01 + 0.0004);
    ++Unit->StageRevision;
    if (NextStage == ELBOneFactoryVehicleStage::FinishedVehicle)
    {
        Unit->bCompleted = true;
        ++CurrentState.CompletedVehicleCount;
    }
    else if (NextStage == ELBOneFactoryVehicleStage::Dispatched)
    {
        Unit->bDispatched = true;
        Unit->DispatchedAtSimSeconds = CurrentState.SimClockSeconds;
        ++CurrentState.DispatchedVehicleCount;
        // Settle against the oldest open contract for this model; creation
        // order makes the array's first open match the oldest.
        for (FLBOneFactoryVehicleContract& Contract : CurrentState.Contracts)
        {
            if (Contract.State != ELBOneFactoryContractState::Open
                || Contract.VehicleModelId != Unit->VehicleModelId)
            {
                continue;
            }
            ++Contract.DispatchedCount;
            Unit->FulfilledContractId = Contract.ContractId;
            if (Contract.DispatchedCount >= Contract.Quantity)
            {
                Contract.State = ELBOneFactoryContractState::Complete;
            }
            break;
        }
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
