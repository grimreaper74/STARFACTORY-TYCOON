#include "LBFactoryManagementSubsystem.h"

namespace
{
    bool TryAddInt64(const int64 A, const int64 B, int64& OutValue)
    {
        if ((B > 0 && A > MAX_int64 - B) || (B < 0 && A < MIN_int64 - B))
            return false;
        OutValue = A + B;
        return true;
    }

    bool TryAddNonNegative(const int64 A, const int64 B, int64& OutValue)
    {
        return A >= 0 && B >= 0 && TryAddInt64(A, B, OutValue) && OutValue >= 0;
    }

    bool IsExpenseCategory(const ELBManagementLedgerCategory Category)
    {
        return Category == ELBManagementLedgerCategory::CapitalPurchase
            || Category == ELBManagementLedgerCategory::OperatingCost
            || Category == ELBManagementLedgerCategory::MaintenanceService
            || Category == ELBManagementLedgerCategory::MachineUpgrade;
    }

    bool IsKnownCategory(const ELBManagementLedgerCategory Category)
    {
        switch (Category)
        {
        case ELBManagementLedgerCategory::CapitalPurchase:
        case ELBManagementLedgerCategory::OperatingCost:
        case ELBManagementLedgerCategory::OrderRevenue:
        case ELBManagementLedgerCategory::MaintenanceService:
        case ELBManagementLedgerCategory::MachineUpgrade:
            return true;
        default:
            return false;
        }
    }

    const FLBManagementLedgerEntry* FindLedgerEntry(
        const TArray<FLBManagementLedgerEntry>& Ledger, const FName TransactionId)
    {
        return Ledger.FindByPredicate([TransactionId](const FLBManagementLedgerEntry& Entry)
        {
            return Entry.TransactionId == TransactionId;
        });
    }

    FString UpgradeKey(const FName MachineId, const FName UpgradeId)
    {
        return MachineId.ToString() + TEXT("|") + UpgradeId.ToString();
    }

    FString BucketKey(const FName BucketId, const FName AssetId)
    {
        return BucketId.ToString() + TEXT("|") + AssetId.ToString();
    }

    bool LexicalNameLess(const FName A, const FName B)
    {
        return A.LexicalLess(B);
    }

    bool CanAccumulateLedgerCategory(const TArray<FLBManagementLedgerEntry>& Ledger,
        const ELBManagementLedgerCategory Category, const int64 AdditionalAbsolutePence)
    {
        if (AdditionalAbsolutePence < 0) return false;
        int64 Total = 0;
        for (const FLBManagementLedgerEntry& Entry : Ledger)
        {
            if (Entry.Category != Category) continue;
            const int64 Absolute = Entry.SignedAmountPence < 0
                ? -Entry.SignedAmountPence : Entry.SignedAmountPence;
            if (!TryAddNonNegative(Total, Absolute, Total)) return false;
        }
        return TryAddNonNegative(Total, AdditionalAbsolutePence, Total);
    }
}

bool ULBFactoryManagementSubsystem::IsStrictId(const FName Id)
{
    if (Id.IsNone()) return false;
    const FString Text = Id.ToString();
    if (Text.IsEmpty() || Text.Len() > 96) return false;
    for (const TCHAR Character : Text)
    {
        const bool bAsciiAlphaNumeric = (Character >= TEXT('A') && Character <= TEXT('Z'))
            || (Character >= TEXT('a') && Character <= TEXT('z'))
            || (Character >= TEXT('0') && Character <= TEXT('9'));
        if (!bAsciiAlphaNumeric && Character != TEXT('-') && Character != TEXT('_')
            && Character != TEXT('.') && Character != TEXT(':') && Character != TEXT('/'))
            return false;
    }
    return true;
}

bool ULBFactoryManagementSubsystem::CanStartMutation(const FName EventId) const
{
    return IsStrictId(EventId) && !AppliedEventSet.Contains(EventId)
        && State.Revision < MAX_int64;
}

bool ULBFactoryManagementSubsystem::CanApplyMoneyDelta(const int64 SignedDeltaPence) const
{
    int64 NewBalance = 0;
    return TryAddInt64(State.CashBalancePence, SignedDeltaPence, NewBalance)
        && NewBalance >= 0;
}

void ULBFactoryManagementSubsystem::AddAppliedEventNoBroadcast(const FName EventId)
{
    AppliedEventSet.Add(EventId);
    State.AppliedEventIds.Add(EventId);
    State.AppliedEventIds.Sort([](const FName A, const FName B)
    {
        return LexicalNameLess(A, B);
    });
}

FLBManagementLedgerEntry ULBFactoryManagementSubsystem::AddLedgerEntryNoBroadcast(
    const FName TransactionId, const ELBManagementLedgerCategory Category,
    const FName SubjectId, const int64 SignedAmountPence, const FName LineItemId)
{
    FLBManagementLedgerEntry Entry;
    Entry.Sequence = State.NextLedgerSequence++;
    Entry.TransactionId = TransactionId;
    Entry.Category = Category;
    Entry.SubjectId = SubjectId;
    Entry.LineItemId = LineItemId;
    Entry.SignedAmountPence = SignedAmountPence;
    State.LedgerEntries.Add(Entry);
    State.CashBalancePence += SignedAmountPence;
    return Entry;
}

void ULBFactoryManagementSubsystem::CommitMutation(
    const FName CauseId, const FLBManagementLedgerEntry* LedgerEntry)
{
    State.Version = CurrentSaveVersion;
    State.bCampaignInitialised = true;
    ++State.Revision;
    bSnapshotDirty = true;
    const FLBFactoryManagementSnapshot Snapshot = GetSnapshot();
    if (LedgerEntry) FinancialTransactionCommitted.Broadcast(*LedgerEntry);
    ManagementChanged.Broadcast(Snapshot, CauseId);
}

bool ULBFactoryManagementSubsystem::InitialiseNewCampaign(
    const int64 OpeningCashPence, const int64 OpeningResearchPoints)
{
    if (State.bCampaignInitialised || State.Revision != 0
        || !State.AppliedEventIds.IsEmpty() || !State.LedgerEntries.IsEmpty()
        || !State.CapitalAssets.IsEmpty() || !State.ResearchGrants.IsEmpty()
        || !State.ResearchUnlocks.IsEmpty()
        || !State.MachineUpgrades.IsEmpty() || !State.QualityRecords.IsEmpty()
        || !State.MaintenanceRecords.IsEmpty() || !State.AnalyticsBuckets.IsEmpty()
        || OpeningCashPence < 0 || OpeningResearchPoints < 0)
        return false;

    State = FLBFactoryManagementSaveState();
    State.Version = CurrentSaveVersion;
    State.bCampaignInitialised = true;
    State.OpeningCashPence = OpeningCashPence;
    State.CashBalancePence = OpeningCashPence;
    State.OpeningResearchPoints = OpeningResearchPoints;
    State.AvailableResearchPoints = OpeningResearchPoints;
    State.Revision = 1;
    RebuildRuntimeCaches();
    bSnapshotDirty = true;
    const FLBFactoryManagementSnapshot Snapshot = GetSnapshot();
    ManagementChanged.Broadcast(Snapshot, TEXT("CAMPAIGN-INITIALISED"));
    return true;
}

bool ULBFactoryManagementSubsystem::TryPurchaseCapitalAsset(
    const FName TransactionId, const FName AssetId, const int64 CostPence)
{
    if (!CanStartMutation(TransactionId) || !IsStrictId(AssetId) || CostPence <= 0
        || State.NextLedgerSequence >= MAX_int64 || !CanApplyMoneyDelta(-CostPence)
        || !CanAccumulateLedgerCategory(State.LedgerEntries,
            ELBManagementLedgerCategory::CapitalPurchase, CostPence)
        || State.CapitalAssets.ContainsByPredicate([AssetId](const FLBManagementCapitalAsset& Asset)
        {
            return Asset.AssetId == AssetId;
        }))
        return false;

    FLBManagementCapitalAsset Asset;
    Asset.AssetId = AssetId;
    Asset.PurchaseTransactionId = TransactionId;
    Asset.PurchaseCostPence = CostPence;
    State.CapitalAssets.Add(Asset);
    State.CapitalAssets.Sort([](const FLBManagementCapitalAsset& A,
        const FLBManagementCapitalAsset& B) { return A.AssetId.LexicalLess(B.AssetId); });
    AddAppliedEventNoBroadcast(TransactionId);
    const FLBManagementLedgerEntry Ledger = AddLedgerEntryNoBroadcast(TransactionId,
        ELBManagementLedgerCategory::CapitalPurchase, AssetId, -CostPence);
    CommitMutation(TransactionId, &Ledger);
    return true;
}

bool ULBFactoryManagementSubsystem::TryChargeOperatingCost(
    const FName TransactionId, const FName CostCentreId, const int64 CostPence)
{
    if (!CanStartMutation(TransactionId) || !IsStrictId(CostCentreId) || CostPence <= 0
        || State.NextLedgerSequence >= MAX_int64 || !CanApplyMoneyDelta(-CostPence)
        || !CanAccumulateLedgerCategory(State.LedgerEntries,
            ELBManagementLedgerCategory::OperatingCost, CostPence))
        return false;
    AddAppliedEventNoBroadcast(TransactionId);
    const FLBManagementLedgerEntry Ledger = AddLedgerEntryNoBroadcast(TransactionId,
        ELBManagementLedgerCategory::OperatingCost, CostCentreId, -CostPence);
    CommitMutation(TransactionId, &Ledger);
    return true;
}

bool ULBFactoryManagementSubsystem::TryRecordOrderRevenue(
    const FName TransactionId, const FName OrderId, const int64 RevenuePence)
{
    if (!CanStartMutation(TransactionId) || !IsStrictId(OrderId) || RevenuePence <= 0
        || State.NextLedgerSequence >= MAX_int64 || !CanApplyMoneyDelta(RevenuePence)
        || !CanAccumulateLedgerCategory(State.LedgerEntries,
            ELBManagementLedgerCategory::OrderRevenue, RevenuePence))
        return false;
    AddAppliedEventNoBroadcast(TransactionId);
    const FLBManagementLedgerEntry Ledger = AddLedgerEntryNoBroadcast(TransactionId,
        ELBManagementLedgerCategory::OrderRevenue, OrderId, RevenuePence);
    CommitMutation(TransactionId, &Ledger);
    return true;
}

bool ULBFactoryManagementSubsystem::GrantResearchPoints(
    const FName EventId, const FName SourceId, const int64 Points)
{
    int64 NewAvailable = 0;
    int64 NewEarned = 0;
    if (!CanStartMutation(EventId) || !IsStrictId(SourceId) || Points <= 0
        || !TryAddNonNegative(State.AvailableResearchPoints, Points, NewAvailable)
        || !TryAddNonNegative(State.TotalResearchEarnedPoints, Points, NewEarned))
        return false;
    State.AvailableResearchPoints = NewAvailable;
    State.TotalResearchEarnedPoints = NewEarned;
    FLBManagementResearchGrant Grant;
    Grant.EventId = EventId;
    Grant.SourceId = SourceId;
    Grant.Points = Points;
    State.ResearchGrants.Add(Grant);
    State.ResearchGrants.Sort([](const FLBManagementResearchGrant& A,
        const FLBManagementResearchGrant& B) { return A.EventId.LexicalLess(B.EventId); });
    AddAppliedEventNoBroadcast(EventId);
    CommitMutation(EventId);
    return true;
}

bool ULBFactoryManagementSubsystem::TryUnlockResearch(
    const FName EventId, const FName UnlockId, const int64 PointCost)
{
    int64 NewSpent = 0;
    if (!CanStartMutation(EventId) || !IsStrictId(UnlockId) || PointCost < 0
        || State.AvailableResearchPoints < PointCost
        || !TryAddNonNegative(State.TotalResearchSpentPoints, PointCost, NewSpent)
        || State.ResearchUnlocks.ContainsByPredicate([UnlockId](const FLBManagementResearchUnlock& Unlock)
        {
            return Unlock.UnlockId == UnlockId;
        }))
        return false;

    FLBManagementResearchUnlock Unlock;
    Unlock.UnlockId = UnlockId;
    Unlock.EventId = EventId;
    Unlock.ResearchPointCost = PointCost;
    State.ResearchUnlocks.Add(Unlock);
    State.ResearchUnlocks.Sort([](const FLBManagementResearchUnlock& A,
        const FLBManagementResearchUnlock& B) { return A.UnlockId.LexicalLess(B.UnlockId); });
    State.AvailableResearchPoints -= PointCost;
    State.TotalResearchSpentPoints = NewSpent;
    AddAppliedEventNoBroadcast(EventId);
    CommitMutation(EventId);
    return true;
}

bool ULBFactoryManagementSubsystem::TryPurchaseMachineUpgrade(
    const FName TransactionId, const FName MachineId, const FName UpgradeId,
    const int32 TargetLevel, const int64 CostPence, const FName RequiredUnlockId)
{
    if (!CanStartMutation(TransactionId) || !IsStrictId(MachineId)
        || !IsStrictId(UpgradeId) || CostPence <= 0 || TargetLevel <= 0
        || State.NextLedgerSequence >= MAX_int64 || !CanApplyMoneyDelta(-CostPence)
        || !CanAccumulateLedgerCategory(State.LedgerEntries,
            ELBManagementLedgerCategory::MachineUpgrade, CostPence)
        || (!RequiredUnlockId.IsNone() && (!IsStrictId(RequiredUnlockId)
            || !HasResearchUnlock(RequiredUnlockId))))
        return false;

    FLBManagementMachineUpgrade* Existing = State.MachineUpgrades.FindByPredicate(
        [MachineId, UpgradeId](const FLBManagementMachineUpgrade& Upgrade)
        {
            return Upgrade.MachineId == MachineId && Upgrade.UpgradeId == UpgradeId;
        });
    if (Existing && Existing->RequiredUnlockId != RequiredUnlockId) return false;
    if (TargetLevel != (Existing ? Existing->Level + 1 : 1)) return false;
    int64 NewInvestment = CostPence;
    if (Existing && !TryAddNonNegative(Existing->TotalInvestedPence,
        CostPence, NewInvestment)) return false;

    if (Existing)
    {
        Existing->Level = TargetLevel;
        Existing->TotalInvestedPence = NewInvestment;
        Existing->LastTransactionId = TransactionId;
    }
    else
    {
        FLBManagementMachineUpgrade Upgrade;
        Upgrade.MachineId = MachineId;
        Upgrade.UpgradeId = UpgradeId;
        Upgrade.RequiredUnlockId = RequiredUnlockId;
        Upgrade.Level = 1;
        Upgrade.TotalInvestedPence = CostPence;
        Upgrade.LastTransactionId = TransactionId;
        State.MachineUpgrades.Add(Upgrade);
    }
    State.MachineUpgrades.Sort([](const FLBManagementMachineUpgrade& A,
        const FLBManagementMachineUpgrade& B)
    {
        if (A.MachineId != B.MachineId) return A.MachineId.LexicalLess(B.MachineId);
        return A.UpgradeId.LexicalLess(B.UpgradeId);
    });
    AddAppliedEventNoBroadcast(TransactionId);
    const FLBManagementLedgerEntry Ledger = AddLedgerEntryNoBroadcast(TransactionId,
        ELBManagementLedgerCategory::MachineUpgrade, MachineId, -CostPence, UpgradeId);
    CommitMutation(TransactionId, &Ledger);
    return true;
}

bool ULBFactoryManagementSubsystem::ValidateQualityRecord(
    const FLBManagementQualityRecord& Record)
{
    return IsStrictId(Record.AssetId) && Record.ProducedCount >= 0
        && Record.InspectedCount >= 0 && Record.PassedCount >= 0
        && Record.RejectedCount >= 0 && Record.ReworkedCount >= 0
        && Record.ScrappedCount >= 0
        && Record.InspectedCount <= Record.ProducedCount
        && Record.PassedCount <= Record.InspectedCount
        && Record.RejectedCount <= Record.InspectedCount - Record.PassedCount
        && Record.ReworkedCount <= Record.RejectedCount
        && Record.ScrappedCount <= Record.RejectedCount - Record.ReworkedCount;
}

bool ULBFactoryManagementSubsystem::RecordQualityCounts(
    const FName EventId, const FName AssetId, const int64 ProducedDelta,
    const int64 InspectedDelta, const int64 PassedDelta, const int64 RejectedDelta,
    const int64 ReworkedDelta, const int64 ScrappedDelta)
{
    if (!CanStartMutation(EventId) || !IsStrictId(AssetId)
        || ProducedDelta < 0 || InspectedDelta < 0 || PassedDelta < 0
        || RejectedDelta < 0 || ReworkedDelta < 0 || ScrappedDelta < 0
        || (ProducedDelta | InspectedDelta | PassedDelta | RejectedDelta
            | ReworkedDelta | ScrappedDelta) == 0)
        return false;

    FLBManagementQualityRecord Updated;
    if (const FLBManagementQualityRecord* Existing = State.QualityRecords.FindByPredicate(
        [AssetId](const FLBManagementQualityRecord& Record) { return Record.AssetId == AssetId; }))
        Updated = *Existing;
    else
        Updated.AssetId = AssetId;

    if (!TryAddNonNegative(Updated.ProducedCount, ProducedDelta, Updated.ProducedCount)
        || !TryAddNonNegative(Updated.InspectedCount, InspectedDelta, Updated.InspectedCount)
        || !TryAddNonNegative(Updated.PassedCount, PassedDelta, Updated.PassedCount)
        || !TryAddNonNegative(Updated.RejectedCount, RejectedDelta, Updated.RejectedCount)
        || !TryAddNonNegative(Updated.ReworkedCount, ReworkedDelta, Updated.ReworkedCount)
        || !TryAddNonNegative(Updated.ScrappedCount, ScrappedDelta, Updated.ScrappedCount)
        || !ValidateQualityRecord(Updated))
        return false;

    FLBManagementQualityRecord FactoryTotals;
    FactoryTotals.AssetId = TEXT("FACTORY");
    for (const FLBManagementQualityRecord& Record : State.QualityRecords)
    {
        if (!TryAddNonNegative(FactoryTotals.ProducedCount, Record.ProducedCount,
                FactoryTotals.ProducedCount)
            || !TryAddNonNegative(FactoryTotals.InspectedCount, Record.InspectedCount,
                FactoryTotals.InspectedCount)
            || !TryAddNonNegative(FactoryTotals.PassedCount, Record.PassedCount,
                FactoryTotals.PassedCount)
            || !TryAddNonNegative(FactoryTotals.RejectedCount, Record.RejectedCount,
                FactoryTotals.RejectedCount)
            || !TryAddNonNegative(FactoryTotals.ReworkedCount, Record.ReworkedCount,
                FactoryTotals.ReworkedCount)
            || !TryAddNonNegative(FactoryTotals.ScrappedCount, Record.ScrappedCount,
                FactoryTotals.ScrappedCount))
            return false;
    }
    const FLBManagementQualityRecord* Previous = State.QualityRecords.FindByPredicate(
        [AssetId](const FLBManagementQualityRecord& Record) { return Record.AssetId == AssetId; });
    if (Previous)
    {
        FactoryTotals.ProducedCount -= Previous->ProducedCount;
        FactoryTotals.InspectedCount -= Previous->InspectedCount;
        FactoryTotals.PassedCount -= Previous->PassedCount;
        FactoryTotals.RejectedCount -= Previous->RejectedCount;
        FactoryTotals.ReworkedCount -= Previous->ReworkedCount;
        FactoryTotals.ScrappedCount -= Previous->ScrappedCount;
    }
    if (!TryAddNonNegative(FactoryTotals.ProducedCount, Updated.ProducedCount,
            FactoryTotals.ProducedCount)
        || !TryAddNonNegative(FactoryTotals.InspectedCount, Updated.InspectedCount,
            FactoryTotals.InspectedCount)
        || !TryAddNonNegative(FactoryTotals.PassedCount, Updated.PassedCount,
            FactoryTotals.PassedCount)
        || !TryAddNonNegative(FactoryTotals.RejectedCount, Updated.RejectedCount,
            FactoryTotals.RejectedCount)
        || !TryAddNonNegative(FactoryTotals.ReworkedCount, Updated.ReworkedCount,
            FactoryTotals.ReworkedCount)
        || !TryAddNonNegative(FactoryTotals.ScrappedCount, Updated.ScrappedCount,
            FactoryTotals.ScrappedCount))
        return false;

    if (FLBManagementQualityRecord* Existing = State.QualityRecords.FindByPredicate(
        [AssetId](const FLBManagementQualityRecord& Record) { return Record.AssetId == AssetId; }))
        *Existing = Updated;
    else
        State.QualityRecords.Add(Updated);
    State.QualityRecords.Sort([](const FLBManagementQualityRecord& A,
        const FLBManagementQualityRecord& B) { return A.AssetId.LexicalLess(B.AssetId); });
    AddAppliedEventNoBroadcast(EventId);
    CommitMutation(EventId);
    return true;
}

bool ULBFactoryManagementSubsystem::ValidateMaintenanceRecord(
    const FLBManagementMaintenanceRecord& Record)
{
    return IsStrictId(Record.AssetId) && FMath::IsFinite(Record.WearFraction)
        && Record.WearFraction >= 0.0 && Record.WearFraction <= 1.0
        && FMath::IsFinite(Record.OperatingSecondsSinceService)
        && Record.OperatingSecondsSinceService >= 0.0
        && FMath::IsFinite(Record.ServiceIntervalOperatingHours)
        && Record.ServiceIntervalOperatingHours > 0.0
        && FMath::IsFinite(Record.CumulativeDowntimeSeconds)
        && Record.CumulativeDowntimeSeconds >= 0.0
        && Record.CompletedServiceCount >= 0
        && (Record.bFaulted ? IsStrictId(Record.FaultCode) : Record.FaultCode.IsNone());
}

bool ULBFactoryManagementSubsystem::RegisterMaintainableAsset(
    const FName EventId, const FName AssetId, const double ServiceIntervalOperatingHours)
{
    if (!CanStartMutation(EventId) || !IsStrictId(AssetId)
        || !FMath::IsFinite(ServiceIntervalOperatingHours)
        || ServiceIntervalOperatingHours <= 0.0 || ServiceIntervalOperatingHours > 1000000.0
        || State.MaintenanceRecords.ContainsByPredicate([AssetId](
            const FLBManagementMaintenanceRecord& Record) { return Record.AssetId == AssetId; }))
        return false;
    FLBManagementMaintenanceRecord Record;
    Record.AssetId = AssetId;
    Record.ServiceIntervalOperatingHours = ServiceIntervalOperatingHours;
    State.MaintenanceRecords.Add(Record);
    State.MaintenanceRecords.Sort([](const FLBManagementMaintenanceRecord& A,
        const FLBManagementMaintenanceRecord& B) { return A.AssetId.LexicalLess(B.AssetId); });
    AddAppliedEventNoBroadcast(EventId);
    CommitMutation(EventId);
    return true;
}

bool ULBFactoryManagementSubsystem::RecordMaintenanceUsage(
    const FName EventId, const FName AssetId, const double OperatingSeconds,
    const double FaultDowntimeSeconds, const double WearIncrease)
{
    FLBManagementMaintenanceRecord* Record = State.MaintenanceRecords.FindByPredicate(
        [AssetId](const FLBManagementMaintenanceRecord& Candidate)
        {
            return Candidate.AssetId == AssetId;
        });
    if (!CanStartMutation(EventId) || !Record || !FMath::IsFinite(OperatingSeconds)
        || !FMath::IsFinite(FaultDowntimeSeconds) || !FMath::IsFinite(WearIncrease)
        || OperatingSeconds < 0.0 || FaultDowntimeSeconds < 0.0
        || WearIncrease < 0.0 || WearIncrease > 1.0
        || (OperatingSeconds == 0.0 && FaultDowntimeSeconds == 0.0 && WearIncrease == 0.0)
        || !FMath::IsFinite(Record->OperatingSecondsSinceService + OperatingSeconds)
        || !FMath::IsFinite(Record->CumulativeDowntimeSeconds + FaultDowntimeSeconds))
        return false;
    Record->OperatingSecondsSinceService += OperatingSeconds;
    Record->CumulativeDowntimeSeconds += FaultDowntimeSeconds;
    Record->WearFraction = FMath::Min(1.0, Record->WearFraction + WearIncrease);
    AddAppliedEventNoBroadcast(EventId);
    CommitMutation(EventId);
    return true;
}

bool ULBFactoryManagementSubsystem::SetMaintenancePlanned(
    const FName EventId, const FName AssetId, const bool bPlanned)
{
    FLBManagementMaintenanceRecord* Record = State.MaintenanceRecords.FindByPredicate(
        [AssetId](const FLBManagementMaintenanceRecord& Candidate)
        {
            return Candidate.AssetId == AssetId;
        });
    if (!CanStartMutation(EventId) || !Record || Record->bPlannedService == bPlanned)
        return false;
    Record->bPlannedService = bPlanned;
    AddAppliedEventNoBroadcast(EventId);
    CommitMutation(EventId);
    return true;
}

bool ULBFactoryManagementSubsystem::SetAssetFault(
    const FName EventId, const FName AssetId, const FName FaultCode)
{
    FLBManagementMaintenanceRecord* Record = State.MaintenanceRecords.FindByPredicate(
        [AssetId](const FLBManagementMaintenanceRecord& Candidate)
        {
            return Candidate.AssetId == AssetId;
        });
    if (!CanStartMutation(EventId) || !Record || !IsStrictId(FaultCode)
        || (Record->bFaulted && Record->FaultCode == FaultCode))
        return false;
    Record->bFaulted = true;
    Record->FaultCode = FaultCode;
    AddAppliedEventNoBroadcast(EventId);
    CommitMutation(EventId);
    return true;
}

bool ULBFactoryManagementSubsystem::ClearAssetFault(
    const FName EventId, const FName AssetId)
{
    FLBManagementMaintenanceRecord* Record = State.MaintenanceRecords.FindByPredicate(
        [AssetId](const FLBManagementMaintenanceRecord& Candidate)
        {
            return Candidate.AssetId == AssetId;
        });
    if (!CanStartMutation(EventId) || !Record || !Record->bFaulted) return false;
    Record->bFaulted = false;
    Record->FaultCode = NAME_None;
    AddAppliedEventNoBroadcast(EventId);
    CommitMutation(EventId);
    return true;
}

bool ULBFactoryManagementSubsystem::TryCompleteMaintenanceService(
    const FName TransactionId, const FName AssetId, const int64 CostPence)
{
    FLBManagementMaintenanceRecord* Record = State.MaintenanceRecords.FindByPredicate(
        [AssetId](const FLBManagementMaintenanceRecord& Candidate)
        {
            return Candidate.AssetId == AssetId;
        });
    if (!CanStartMutation(TransactionId) || !Record || CostPence < 0
        || (!Record->bPlannedService && !Record->bFaulted && !Record->IsServiceDue())
        || Record->CompletedServiceCount == MAX_int32
        || (CostPence > 0 && (State.NextLedgerSequence >= MAX_int64
            || !CanApplyMoneyDelta(-CostPence)
            || !CanAccumulateLedgerCategory(State.LedgerEntries,
                ELBManagementLedgerCategory::MaintenanceService, CostPence))))
        return false;

    Record->WearFraction = 0.0;
    Record->OperatingSecondsSinceService = 0.0;
    Record->bPlannedService = false;
    Record->bFaulted = false;
    Record->FaultCode = NAME_None;
    ++Record->CompletedServiceCount;
    AddAppliedEventNoBroadcast(TransactionId);
    if (CostPence > 0)
    {
        const FLBManagementLedgerEntry Ledger = AddLedgerEntryNoBroadcast(TransactionId,
            ELBManagementLedgerCategory::MaintenanceService, AssetId, -CostPence);
        CommitMutation(TransactionId, &Ledger);
    }
    else
    {
        CommitMutation(TransactionId);
    }
    return true;
}

bool ULBFactoryManagementSubsystem::ValidateTimeBucketSample(
    const FLBManagementTimeBucketSample& Sample)
{
    const bool bFinite = FMath::IsFinite(Sample.BucketStartSimulationSeconds)
        && FMath::IsFinite(Sample.BucketDurationSeconds)
        && FMath::IsFinite(Sample.PlannedProductionSeconds)
        && FMath::IsFinite(Sample.RunningSeconds)
        && FMath::IsFinite(Sample.StarvedSeconds)
        && FMath::IsFinite(Sample.BlockedSeconds)
        && FMath::IsFinite(Sample.FaultDowntimeSeconds)
        && FMath::IsFinite(Sample.IdealUnitCapacity);
    if (!bFinite || Sample.BucketStartSimulationSeconds < 0.0
        || Sample.BucketDurationSeconds <= 0.0
        || Sample.PlannedProductionSeconds < 0.0
        || Sample.PlannedProductionSeconds > Sample.BucketDurationSeconds
        || Sample.RunningSeconds < 0.0 || Sample.StarvedSeconds < 0.0
        || Sample.BlockedSeconds < 0.0 || Sample.FaultDowntimeSeconds < 0.0
        || Sample.IdealUnitCapacity < 0.0 || Sample.ProducedCount < 0
        || Sample.GoodCount < 0 || Sample.GoodCount > Sample.ProducedCount)
        return false;
    const double Accounted = Sample.RunningSeconds + Sample.StarvedSeconds
        + Sample.BlockedSeconds + Sample.FaultDowntimeSeconds;
    if (!FMath::IsFinite(Accounted)
        || Accounted > Sample.PlannedProductionSeconds + 0.0001)
        return false;
    if ((Sample.IdealUnitCapacity == 0.0 && Sample.ProducedCount != 0)
        || static_cast<double>(Sample.ProducedCount) > Sample.IdealUnitCapacity + 0.0001)
        return false;
    return true;
}

bool ULBFactoryManagementSubsystem::RecordTimeBucket(
    const FName EventId, const FName BucketId, const FName AssetId,
    const FLBManagementTimeBucketSample& Sample)
{
    if (!CanStartMutation(EventId) || !IsStrictId(BucketId) || !IsStrictId(AssetId)
        || !ValidateTimeBucketSample(Sample)
        || State.AnalyticsBuckets.ContainsByPredicate([BucketId, AssetId](
            const FLBManagementTimeBucketRecord& Record)
        {
            return Record.BucketId == BucketId && Record.AssetId == AssetId;
        }))
        return false;
    double TotalDuration = Sample.BucketDurationSeconds;
    double TotalPlanned = Sample.PlannedProductionSeconds;
    double TotalRunning = Sample.RunningSeconds;
    double TotalIdeal = Sample.IdealUnitCapacity;
    double TotalProduced = static_cast<double>(Sample.ProducedCount);
    double TotalGood = static_cast<double>(Sample.GoodCount);
    for (const FLBManagementTimeBucketRecord& Existing : State.AnalyticsBuckets)
    {
        TotalDuration += Existing.Sample.BucketDurationSeconds;
        TotalPlanned += Existing.Sample.PlannedProductionSeconds;
        TotalRunning += Existing.Sample.RunningSeconds;
        TotalIdeal += Existing.Sample.IdealUnitCapacity;
        TotalProduced += static_cast<double>(Existing.Sample.ProducedCount);
        TotalGood += static_cast<double>(Existing.Sample.GoodCount);
        if (!FMath::IsFinite(TotalDuration) || !FMath::IsFinite(TotalPlanned)
            || !FMath::IsFinite(TotalRunning) || !FMath::IsFinite(TotalIdeal)
            || !FMath::IsFinite(TotalProduced) || !FMath::IsFinite(TotalGood))
            return false;
    }
    FLBManagementTimeBucketRecord Record;
    Record.EventId = EventId;
    Record.BucketId = BucketId;
    Record.AssetId = AssetId;
    Record.Sample = Sample;
    State.AnalyticsBuckets.Add(Record);
    State.AnalyticsBuckets.Sort([](const FLBManagementTimeBucketRecord& A,
        const FLBManagementTimeBucketRecord& B)
    {
        if (A.Sample.BucketStartSimulationSeconds != B.Sample.BucketStartSimulationSeconds)
            return A.Sample.BucketStartSimulationSeconds < B.Sample.BucketStartSimulationSeconds;
        if (A.BucketId != B.BucketId) return A.BucketId.LexicalLess(B.BucketId);
        return A.AssetId.LexicalLess(B.AssetId);
    });
    AddAppliedEventNoBroadcast(EventId);
    CommitMutation(EventId);
    return true;
}

bool ULBFactoryManagementSubsystem::HasResearchUnlock(const FName UnlockId) const
{
    return State.ResearchUnlocks.ContainsByPredicate([UnlockId](
        const FLBManagementResearchUnlock& Unlock) { return Unlock.UnlockId == UnlockId; });
}

int32 ULBFactoryManagementSubsystem::GetMachineUpgradeLevel(
    const FName MachineId, const FName UpgradeId) const
{
    const FLBManagementMachineUpgrade* Upgrade = State.MachineUpgrades.FindByPredicate(
        [MachineId, UpgradeId](const FLBManagementMachineUpgrade& Candidate)
        {
            return Candidate.MachineId == MachineId && Candidate.UpgradeId == UpgradeId;
        });
    return Upgrade ? Upgrade->Level : 0;
}

bool ULBFactoryManagementSubsystem::GetMaintenanceRecord(
    const FName AssetId, FLBManagementMaintenanceRecord& OutRecord) const
{
    const FLBManagementMaintenanceRecord* Record = State.MaintenanceRecords.FindByPredicate(
        [AssetId](const FLBManagementMaintenanceRecord& Candidate)
        {
            return Candidate.AssetId == AssetId;
        });
    if (!Record) return false;
    OutRecord = *Record;
    return true;
}

bool ULBFactoryManagementSubsystem::GetQualityRecord(
    const FName AssetId, FLBManagementQualityRecord& OutRecord) const
{
    const FLBManagementQualityRecord* Record = State.QualityRecords.FindByPredicate(
        [AssetId](const FLBManagementQualityRecord& Candidate)
        {
            return Candidate.AssetId == AssetId;
        });
    if (!Record) return false;
    OutRecord = *Record;
    return true;
}

bool ULBFactoryManagementSubsystem::IsEventApplied(const FName EventId) const
{
    return AppliedEventSet.Contains(EventId);
}

FLBManagementKPIValues ULBFactoryManagementSubsystem::CalculateKPIs(
    const TArray<FLBManagementTimeBucketRecord>& Records)
{
    double Duration = 0.0;
    double Planned = 0.0;
    double Running = 0.0;
    double Starved = 0.0;
    double Blocked = 0.0;
    double FaultDowntime = 0.0;
    double Ideal = 0.0;
    double Produced = 0.0;
    double Good = 0.0;
    for (const FLBManagementTimeBucketRecord& Record : Records)
    {
        Duration += Record.Sample.BucketDurationSeconds;
        Planned += Record.Sample.PlannedProductionSeconds;
        Running += Record.Sample.RunningSeconds;
        Starved += Record.Sample.StarvedSeconds;
        Blocked += Record.Sample.BlockedSeconds;
        FaultDowntime += Record.Sample.FaultDowntimeSeconds;
        Ideal += Record.Sample.IdealUnitCapacity;
        Produced += static_cast<double>(Record.Sample.ProducedCount);
        Good += static_cast<double>(Record.Sample.GoodCount);
    }
    FLBManagementKPIValues Result;
    if (Duration > 0.0)
    {
        Result.ThroughputGoodUnitsPerHour = Good * 3600.0 / Duration;
        Result.StarvationRatio = FMath::Clamp(Starved / Duration, 0.0, 1.0);
        Result.BlockingRatio = FMath::Clamp(Blocked / Duration, 0.0, 1.0);
        Result.FaultDowntimeRatio = FMath::Clamp(FaultDowntime / Duration, 0.0, 1.0);
        Result.UtilisationRatio = FMath::Clamp(Running / Duration, 0.0, 1.0);
    }
    if (Planned > 0.0)
        Result.AvailabilityRatio = FMath::Clamp(Running / Planned, 0.0, 1.0);
    if (Ideal > 0.0)
        Result.PerformanceRatio = FMath::Clamp(Produced / Ideal, 0.0, 1.0);
    if (Produced > 0.0)
        Result.QualityRatio = FMath::Clamp(Good / Produced, 0.0, 1.0);
    Result.OEE = Result.AvailabilityRatio * Result.PerformanceRatio * Result.QualityRatio;
    return Result;
}

void ULBFactoryManagementSubsystem::RebuildSnapshot() const
{
    CachedSnapshot = FLBFactoryManagementSnapshot();
    CachedSnapshot.Revision = State.Revision;
    CachedSnapshot.CashBalancePence = State.CashBalancePence;
    CachedSnapshot.AvailableResearchPoints = State.AvailableResearchPoints;
    CachedSnapshot.TotalResearchEarnedPoints = State.TotalResearchEarnedPoints;
    CachedSnapshot.TotalResearchSpentPoints = State.TotalResearchSpentPoints;
    CachedSnapshot.LedgerEntries = State.LedgerEntries;
    CachedSnapshot.CapitalAssets = State.CapitalAssets;
    for (const FLBManagementLedgerEntry& Entry : State.LedgerEntries)
    {
        const int64 Absolute = Entry.SignedAmountPence < 0
            ? -Entry.SignedAmountPence : Entry.SignedAmountPence;
        switch (Entry.Category)
        {
        case ELBManagementLedgerCategory::CapitalPurchase:
            CachedSnapshot.CapitalSpendPence += Absolute; break;
        case ELBManagementLedgerCategory::OperatingCost:
            CachedSnapshot.OperatingSpendPence += Absolute; break;
        case ELBManagementLedgerCategory::MaintenanceService:
            CachedSnapshot.MaintenanceSpendPence += Absolute; break;
        case ELBManagementLedgerCategory::MachineUpgrade:
            CachedSnapshot.UpgradeSpendPence += Absolute; break;
        case ELBManagementLedgerCategory::OrderRevenue:
            CachedSnapshot.OrderRevenuePence += Absolute; break;
        default: break;
        }
    }
    for (const FLBManagementResearchUnlock& Unlock : State.ResearchUnlocks)
        CachedSnapshot.ResearchUnlockIds.Add(Unlock.UnlockId);
    CachedSnapshot.MachineUpgrades = State.MachineUpgrades;
    CachedSnapshot.QualityByAsset = State.QualityRecords;
    CachedSnapshot.MaintenanceByAsset = State.MaintenanceRecords;
    CachedSnapshot.FactoryQualityTotals.AssetId = TEXT("FACTORY");
    for (const FLBManagementQualityRecord& Record : State.QualityRecords)
    {
        CachedSnapshot.FactoryQualityTotals.ProducedCount += Record.ProducedCount;
        CachedSnapshot.FactoryQualityTotals.InspectedCount += Record.InspectedCount;
        CachedSnapshot.FactoryQualityTotals.PassedCount += Record.PassedCount;
        CachedSnapshot.FactoryQualityTotals.RejectedCount += Record.RejectedCount;
        CachedSnapshot.FactoryQualityTotals.ReworkedCount += Record.ReworkedCount;
        CachedSnapshot.FactoryQualityTotals.ScrappedCount += Record.ScrappedCount;
    }
    for (const FLBManagementTimeBucketRecord& Record : State.AnalyticsBuckets)
    {
        FLBManagementAnalyticsSnapshot Bucket;
        Bucket.BucketId = Record.BucketId;
        Bucket.AssetId = Record.AssetId;
        Bucket.Raw = Record.Sample;
        TArray<FLBManagementTimeBucketRecord> Single;
        Single.Add(Record);
        Bucket.KPIs = CalculateKPIs(Single);
        CachedSnapshot.AnalyticsBuckets.Add(Bucket);
    }
    CachedSnapshot.LifetimeKPIs = CalculateKPIs(State.AnalyticsBuckets);
    bSnapshotDirty = false;
}

const FLBFactoryManagementSnapshot& ULBFactoryManagementSubsystem::GetSnapshot() const
{
    if (bSnapshotDirty) RebuildSnapshot();
    return CachedSnapshot;
}

void ULBFactoryManagementSubsystem::RebuildRuntimeCaches()
{
    AppliedEventSet.Reset();
    for (const FName EventId : State.AppliedEventIds) AppliedEventSet.Add(EventId);
}

bool ULBFactoryManagementSubsystem::ValidateSaveState(
    const FLBFactoryManagementSaveState& SavedState, FString& OutReason)
{
    OutReason.Reset();
    if (SavedState.Version == 1)
    {
        if (SavedState.CashBalancePence < 0 || SavedState.AvailableResearchPoints < 0
            || SavedState.Revision < 0)
        {
            OutReason = TEXT("LEGACY CASH OR RESEARCH STATE IS INVALID");
            return false;
        }
        return true;
    }
    if (SavedState.Version != CurrentSaveVersion)
    {
        OutReason = TEXT("UNSUPPORTED MANAGEMENT SAVE VERSION");
        return false;
    }
    if (SavedState.Revision < 0 || SavedState.OpeningCashPence < 0
        || SavedState.CashBalancePence < 0 || SavedState.OpeningResearchPoints < 0
        || SavedState.AvailableResearchPoints < 0
        || SavedState.TotalResearchEarnedPoints < 0
        || SavedState.TotalResearchSpentPoints < 0 || SavedState.NextLedgerSequence < 1)
    {
        OutReason = TEXT("NEGATIVE MANAGEMENT TOTAL");
        return false;
    }
    const bool bHasPersistentEvents = !SavedState.AppliedEventIds.IsEmpty()
        || !SavedState.LedgerEntries.IsEmpty() || !SavedState.CapitalAssets.IsEmpty()
        || !SavedState.ResearchGrants.IsEmpty() || !SavedState.ResearchUnlocks.IsEmpty()
        || !SavedState.MachineUpgrades.IsEmpty() || !SavedState.QualityRecords.IsEmpty()
        || !SavedState.MaintenanceRecords.IsEmpty() || !SavedState.AnalyticsBuckets.IsEmpty();
    if ((!SavedState.bCampaignInitialised && (SavedState.Revision != 0 || bHasPersistentEvents))
        || (SavedState.bCampaignInitialised && SavedState.Revision < 1))
    {
        OutReason = TEXT("CAMPAIGN INITIALISATION STATE IS INCONSISTENT");
        return false;
    }

    TSet<FName> Applied;
    for (const FName EventId : SavedState.AppliedEventIds)
    {
        if (!IsStrictId(EventId) || Applied.Contains(EventId))
        {
            OutReason = TEXT("INVALID OR DUPLICATE EVENT ID");
            return false;
        }
        Applied.Add(EventId);
    }

    int64 ExpectedCash = SavedState.OpeningCashPence;
    int64 CapitalSpend = 0;
    int64 OperatingSpend = 0;
    int64 Revenue = 0;
    int64 MaintenanceSpend = 0;
    int64 UpgradeSpend = 0;
    TSet<FName> LedgerTransactions;
    TSet<FName> ClaimedPersistentEvents;
    for (int32 Index = 0; Index < SavedState.LedgerEntries.Num(); ++Index)
    {
        const FLBManagementLedgerEntry& Entry = SavedState.LedgerEntries[Index];
        if (Entry.Sequence != static_cast<int64>(Index) + 1
            || !IsStrictId(Entry.TransactionId) || !IsStrictId(Entry.SubjectId)
            || (!Entry.LineItemId.IsNone() && !IsStrictId(Entry.LineItemId))
            || !IsKnownCategory(Entry.Category) || Entry.SignedAmountPence == 0
            || LedgerTransactions.Contains(Entry.TransactionId)
            || !Applied.Contains(Entry.TransactionId)
            || (IsExpenseCategory(Entry.Category) && Entry.SignedAmountPence >= 0)
            || (Entry.Category == ELBManagementLedgerCategory::OrderRevenue
                && Entry.SignedAmountPence <= 0)
            || !TryAddInt64(ExpectedCash, Entry.SignedAmountPence, ExpectedCash)
            || ExpectedCash < 0)
        {
            OutReason = TEXT("INVALID LEDGER ENTRY OR RUNNING BALANCE");
            return false;
        }
        if ((Entry.Category == ELBManagementLedgerCategory::MachineUpgrade
                && Entry.LineItemId.IsNone())
            || (Entry.Category != ELBManagementLedgerCategory::MachineUpgrade
                && !Entry.LineItemId.IsNone()))
        {
            OutReason = TEXT("INVALID LEDGER LINE ITEM");
            return false;
        }
        const int64 Absolute = Entry.SignedAmountPence < 0
            ? -Entry.SignedAmountPence : Entry.SignedAmountPence;
        int64* CategoryTotal = nullptr;
        switch (Entry.Category)
        {
        case ELBManagementLedgerCategory::CapitalPurchase: CategoryTotal = &CapitalSpend; break;
        case ELBManagementLedgerCategory::OperatingCost: CategoryTotal = &OperatingSpend; break;
        case ELBManagementLedgerCategory::OrderRevenue: CategoryTotal = &Revenue; break;
        case ELBManagementLedgerCategory::MaintenanceService: CategoryTotal = &MaintenanceSpend; break;
        case ELBManagementLedgerCategory::MachineUpgrade: CategoryTotal = &UpgradeSpend; break;
        default: break;
        }
        if (!CategoryTotal || !TryAddNonNegative(*CategoryTotal, Absolute, *CategoryTotal))
        {
            OutReason = TEXT("LEDGER CATEGORY TOTAL OVERFLOW");
            return false;
        }
        LedgerTransactions.Add(Entry.TransactionId);
        ClaimedPersistentEvents.Add(Entry.TransactionId);
    }
    if (ExpectedCash != SavedState.CashBalancePence
        || SavedState.NextLedgerSequence != static_cast<int64>(SavedState.LedgerEntries.Num()) + 1)
    {
        OutReason = TEXT("LEDGER TOTAL DOES NOT MATCH CASH BALANCE");
        return false;
    }

    TSet<FName> CapitalIds;
    for (const FLBManagementCapitalAsset& Asset : SavedState.CapitalAssets)
    {
        const FLBManagementLedgerEntry* Entry = FindLedgerEntry(
            SavedState.LedgerEntries, Asset.PurchaseTransactionId);
        if (!IsStrictId(Asset.AssetId) || CapitalIds.Contains(Asset.AssetId)
            || Asset.PurchaseCostPence <= 0 || !Entry
            || Entry->Category != ELBManagementLedgerCategory::CapitalPurchase
            || Entry->SubjectId != Asset.AssetId
            || Entry->SignedAmountPence != -Asset.PurchaseCostPence)
        {
            OutReason = TEXT("INVALID CAPITAL ASSET RECORD");
            return false;
        }
        CapitalIds.Add(Asset.AssetId);
    }

    int64 ResearchGrantTotal = 0;
    TSet<FName> ResearchGrantEvents;
    for (const FLBManagementResearchGrant& Grant : SavedState.ResearchGrants)
    {
        if (!IsStrictId(Grant.EventId) || !IsStrictId(Grant.SourceId)
            || Grant.Points <= 0 || ResearchGrantEvents.Contains(Grant.EventId)
            || !Applied.Contains(Grant.EventId)
            || ClaimedPersistentEvents.Contains(Grant.EventId)
            || !TryAddNonNegative(ResearchGrantTotal, Grant.Points, ResearchGrantTotal))
        {
            OutReason = TEXT("INVALID RESEARCH GRANT");
            return false;
        }
        ResearchGrantEvents.Add(Grant.EventId);
        ClaimedPersistentEvents.Add(Grant.EventId);
    }
    if (ResearchGrantTotal != SavedState.TotalResearchEarnedPoints)
    {
        OutReason = TEXT("RESEARCH EARNINGS DO NOT MATCH GRANTS");
        return false;
    }

    int64 ExpectedResearch = 0;
    if (!TryAddNonNegative(SavedState.OpeningResearchPoints,
        SavedState.TotalResearchEarnedPoints, ExpectedResearch)
        || ExpectedResearch < SavedState.TotalResearchSpentPoints)
    {
        OutReason = TEXT("RESEARCH TOTAL OVERFLOW");
        return false;
    }
    ExpectedResearch -= SavedState.TotalResearchSpentPoints;
    if (ExpectedResearch != SavedState.AvailableResearchPoints)
    {
        OutReason = TEXT("RESEARCH BALANCE DOES NOT RECONCILE");
        return false;
    }
    TSet<FName> UnlockIds;
    int64 UnlockSpend = 0;
    for (const FLBManagementResearchUnlock& Unlock : SavedState.ResearchUnlocks)
    {
        if (!IsStrictId(Unlock.UnlockId) || !IsStrictId(Unlock.EventId)
            || Unlock.ResearchPointCost < 0 || UnlockIds.Contains(Unlock.UnlockId)
            || !Applied.Contains(Unlock.EventId)
            || ClaimedPersistentEvents.Contains(Unlock.EventId)
            || !TryAddNonNegative(UnlockSpend, Unlock.ResearchPointCost, UnlockSpend))
        {
            OutReason = TEXT("INVALID RESEARCH UNLOCK");
            return false;
        }
        UnlockIds.Add(Unlock.UnlockId);
        ClaimedPersistentEvents.Add(Unlock.EventId);
    }
    if (UnlockSpend != SavedState.TotalResearchSpentPoints)
    {
        OutReason = TEXT("RESEARCH SPEND DOES NOT MATCH UNLOCKS");
        return false;
    }

    TSet<FString> UpgradeIds;
    for (const FLBManagementMachineUpgrade& Upgrade : SavedState.MachineUpgrades)
    {
        const FString Key = UpgradeKey(Upgrade.MachineId, Upgrade.UpgradeId);
        if (!IsStrictId(Upgrade.MachineId) || !IsStrictId(Upgrade.UpgradeId)
            || (!Upgrade.RequiredUnlockId.IsNone()
                && (!IsStrictId(Upgrade.RequiredUnlockId)
                    || !UnlockIds.Contains(Upgrade.RequiredUnlockId)))
            || UpgradeIds.Contains(Key) || Upgrade.Level <= 0
            || Upgrade.TotalInvestedPence <= 0)
        {
            OutReason = TEXT("INVALID MACHINE UPGRADE");
            return false;
        }
        int32 MatchingTransactions = 0;
        int64 MatchingInvestment = 0;
        int64 LastSequence = 0;
        FName LastTransactionId = NAME_None;
        for (const FLBManagementLedgerEntry& Entry : SavedState.LedgerEntries)
        {
            if (Entry.Category != ELBManagementLedgerCategory::MachineUpgrade
                || Entry.SubjectId != Upgrade.MachineId
                || Entry.LineItemId != Upgrade.UpgradeId)
                continue;
            if (MatchingTransactions == MAX_int32
                || !TryAddNonNegative(MatchingInvestment, -Entry.SignedAmountPence,
                    MatchingInvestment))
            {
                OutReason = TEXT("MACHINE UPGRADE INVESTMENT OVERFLOW");
                return false;
            }
            ++MatchingTransactions;
            if (Entry.Sequence > LastSequence)
            {
                LastSequence = Entry.Sequence;
                LastTransactionId = Entry.TransactionId;
            }
        }
        if (MatchingTransactions != Upgrade.Level
            || MatchingInvestment != Upgrade.TotalInvestedPence
            || LastTransactionId != Upgrade.LastTransactionId)
        {
            OutReason = TEXT("MACHINE UPGRADE LEDGER DOES NOT RECONCILE");
            return false;
        }
        UpgradeIds.Add(Key);
    }

    TSet<FName> QualityIds;
    FLBManagementQualityRecord QualityTotals;
    QualityTotals.AssetId = TEXT("FACTORY");
    for (const FLBManagementQualityRecord& Record : SavedState.QualityRecords)
    {
        if (!ValidateQualityRecord(Record) || QualityIds.Contains(Record.AssetId)
            || !TryAddNonNegative(QualityTotals.ProducedCount, Record.ProducedCount,
                QualityTotals.ProducedCount)
            || !TryAddNonNegative(QualityTotals.InspectedCount, Record.InspectedCount,
                QualityTotals.InspectedCount)
            || !TryAddNonNegative(QualityTotals.PassedCount, Record.PassedCount,
                QualityTotals.PassedCount)
            || !TryAddNonNegative(QualityTotals.RejectedCount, Record.RejectedCount,
                QualityTotals.RejectedCount)
            || !TryAddNonNegative(QualityTotals.ReworkedCount, Record.ReworkedCount,
                QualityTotals.ReworkedCount)
            || !TryAddNonNegative(QualityTotals.ScrappedCount, Record.ScrappedCount,
                QualityTotals.ScrappedCount))
        {
            OutReason = TEXT("INVALID QUALITY RECORD");
            return false;
        }
        QualityIds.Add(Record.AssetId);
    }

    TSet<FName> MaintenanceIds;
    for (const FLBManagementMaintenanceRecord& Record : SavedState.MaintenanceRecords)
    {
        if (!ValidateMaintenanceRecord(Record) || MaintenanceIds.Contains(Record.AssetId))
        {
            OutReason = TEXT("INVALID MAINTENANCE RECORD");
            return false;
        }
        MaintenanceIds.Add(Record.AssetId);
    }

    for (const FLBManagementLedgerEntry& Entry : SavedState.LedgerEntries)
    {
        if (Entry.Category == ELBManagementLedgerCategory::CapitalPurchase
            && !SavedState.CapitalAssets.ContainsByPredicate([&Entry](
                const FLBManagementCapitalAsset& Asset)
            {
                return Asset.PurchaseTransactionId == Entry.TransactionId;
            }))
        {
            OutReason = TEXT("CAPITAL LEDGER HAS NO ASSET RECORD");
            return false;
        }
        if (Entry.Category == ELBManagementLedgerCategory::MachineUpgrade
            && !UpgradeIds.Contains(UpgradeKey(Entry.SubjectId, Entry.LineItemId)))
        {
            OutReason = TEXT("UPGRADE LEDGER HAS NO UPGRADE RECORD");
            return false;
        }
        if (Entry.Category == ELBManagementLedgerCategory::MaintenanceService
            && !MaintenanceIds.Contains(Entry.SubjectId))
        {
            OutReason = TEXT("SERVICE LEDGER HAS NO MAINTENANCE ASSET");
            return false;
        }
    }

    TSet<FString> BucketIds;
    double TotalDuration = 0.0;
    double TotalPlanned = 0.0;
    double TotalRunning = 0.0;
    double TotalIdeal = 0.0;
    double TotalProduced = 0.0;
    double TotalGood = 0.0;
    for (const FLBManagementTimeBucketRecord& Record : SavedState.AnalyticsBuckets)
    {
        const FString Key = BucketKey(Record.BucketId, Record.AssetId);
        if (!IsStrictId(Record.EventId) || !IsStrictId(Record.BucketId)
            || !IsStrictId(Record.AssetId) || !Applied.Contains(Record.EventId)
            || ClaimedPersistentEvents.Contains(Record.EventId)
            || BucketIds.Contains(Key) || !ValidateTimeBucketSample(Record.Sample))
        {
            OutReason = TEXT("INVALID ANALYTICS BUCKET");
            return false;
        }
        ClaimedPersistentEvents.Add(Record.EventId);
        TotalDuration += Record.Sample.BucketDurationSeconds;
        TotalPlanned += Record.Sample.PlannedProductionSeconds;
        TotalRunning += Record.Sample.RunningSeconds;
        TotalIdeal += Record.Sample.IdealUnitCapacity;
        TotalProduced += static_cast<double>(Record.Sample.ProducedCount);
        TotalGood += static_cast<double>(Record.Sample.GoodCount);
        if (!FMath::IsFinite(TotalDuration) || !FMath::IsFinite(TotalPlanned)
            || !FMath::IsFinite(TotalRunning) || !FMath::IsFinite(TotalIdeal)
            || !FMath::IsFinite(TotalProduced) || !FMath::IsFinite(TotalGood))
        {
            OutReason = TEXT("ANALYTICS TOTAL OVERFLOW");
            return false;
        }
        BucketIds.Add(Key);
    }
    return true;
}

bool ULBFactoryManagementSubsystem::RestoreSaveState(
    const FLBFactoryManagementSaveState& SavedState)
{
    FString Reason;
    if (!ValidateSaveState(SavedState, Reason)) return false;

    if (SavedState.Version == 1)
    {
        FLBFactoryManagementSaveState Migrated;
        Migrated.Version = CurrentSaveVersion;
        Migrated.bCampaignInitialised = true;
        Migrated.Revision = FMath::Max<int64>(1, SavedState.Revision);
        Migrated.OpeningCashPence = SavedState.CashBalancePence;
        Migrated.CashBalancePence = SavedState.CashBalancePence;
        Migrated.OpeningResearchPoints = SavedState.AvailableResearchPoints;
        Migrated.AvailableResearchPoints = SavedState.AvailableResearchPoints;
        State = MoveTemp(Migrated);
    }
    else
    {
        State = SavedState;
    }
    RebuildRuntimeCaches();
    bSnapshotDirty = true;
    const FLBFactoryManagementSnapshot Snapshot = GetSnapshot();
    ManagementChanged.Broadcast(Snapshot, TEXT("SAVE-RESTORED"));
    return true;
}
