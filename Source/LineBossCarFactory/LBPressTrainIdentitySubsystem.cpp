#include "LBPressTrainIdentitySubsystem.h"

#include "LBPressTrainAStation.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressShopSaveGame.h"
#include "EngineUtils.h"

namespace
{
bool IsFinitePressTrainSaveState(const FLBPressTrainASaveState& State)
{
    return FMath::IsFinite(State.RunningHours)
        && FMath::IsFinite(State.CycleElapsedSeconds)
        && FMath::IsFinite(State.TargetStrokesPerMinute)
        && FMath::IsFinite(State.HydraulicPressureBar)
        && FMath::IsFinite(State.PressLoadPercent);
}
}

bool ULBPressTrainIdentitySubsystem::IsValidTrainId(const FName TrainId)
{
    const FString Id = TrainId.ToString().ToUpper();
    return Id.Len() == 7 && Id.StartsWith(TEXT("TRAIN_"))
        && Id[6] >= TCHAR('A') && Id[6] <= TCHAR('D');
}

void ULBPressTrainIdentitySubsystem::PurgeInvalidEntries()
{
    for (auto It = TrainsByGuid.CreateIterator(); It; ++It)
        if (!It.Value().IsValid()) It.RemoveCurrent();
    for (auto It = TrainsById.CreateIterator(); It; ++It)
        if (!It.Value().IsValid()) It.RemoveCurrent();
    for (auto It = ManagedTrains.CreateIterator(); It; ++It)
        if (!It->IsValid()) It.RemoveCurrent();
}

FName ULBPressTrainIdentitySubsystem::FindNextAvailableTrainId() const
{
    for (TCHAR Letter = TCHAR('A'); Letter <= TCHAR('D'); ++Letter)
    {
        const FName Candidate(*FString::Printf(TEXT("TRAIN_%c"), Letter));
        if (!TrainsById.Contains(Candidate)) return Candidate;
    }
    return NAME_None;
}

bool ULBPressTrainIdentitySubsystem::RegisterTrain(ALBPressTrainAStation* Train)
{
    if (!IsValid(Train)) return false;
    PurgeInvalidEntries();

    FGuid Guid = Train->GetPersistentTrainGuid();
    const TWeakObjectPtr<ALBPressTrainAStation>* GuidOwner = Guid.IsValid() ? TrainsByGuid.Find(Guid) : nullptr;
    if (!Guid.IsValid() || (GuidOwner && GuidOwner->Get() != Train)) Guid = FGuid::NewGuid();

    FName Id = Train->GetTrainId();
    const TWeakObjectPtr<ALBPressTrainAStation>* IdOwner = IsValidTrainId(Id) ? TrainsById.Find(Id) : nullptr;
    if (!IsValidTrainId(Id) || (IdOwner && IdOwner->Get() != Train)) Id = FindNextAvailableTrainId();
    if (Id.IsNone()) return false;

    Train->ApplyPersistentIdentity(Guid, Id, Train->GetTrainDisplayName());
    TrainsByGuid.Add(Guid, Train);
    TrainsById.Add(Id, Train);
    return true;
}

void ULBPressTrainIdentitySubsystem::ReleaseTrain(ALBPressTrainAStation* Train)
{
    if (!Train) return;
    if (const TWeakObjectPtr<ALBPressTrainAStation>* Owner = TrainsByGuid.Find(Train->GetPersistentTrainGuid()))
        if (Owner->Get() == Train) TrainsByGuid.Remove(Train->GetPersistentTrainGuid());
    if (const TWeakObjectPtr<ALBPressTrainAStation>* Owner = TrainsById.Find(Train->GetTrainId()))
        if (Owner->Get() == Train) TrainsById.Remove(Train->GetTrainId());
    ManagedTrains.Remove(Train);
}

bool ULBPressTrainIdentitySubsystem::RestoreTrainIdentity(ALBPressTrainAStation* Train,
    const FGuid& PersistentGuid, const FName TrainId, const FString& DisplayName)
{
    if (!IsValid(Train) || !PersistentGuid.IsValid() || !IsValidTrainId(TrainId)) return false;
    PurgeInvalidEntries();
    if (const TWeakObjectPtr<ALBPressTrainAStation>* Owner = TrainsByGuid.Find(PersistentGuid))
        if (Owner->Get() != Train) return false;
    if (const TWeakObjectPtr<ALBPressTrainAStation>* Owner = TrainsById.Find(TrainId))
        if (Owner->Get() != Train) return false;

    const bool bWasManaged = ManagedTrains.Contains(Train);
    ReleaseTrain(Train);
    Train->ApplyPersistentIdentity(PersistentGuid, TrainId, DisplayName);
    TrainsByGuid.Add(PersistentGuid, Train);
    TrainsById.Add(TrainId, Train);
    if (bWasManaged) ManagedTrains.Add(Train);
    return true;
}

ALBPressTrainAStation* ULBPressTrainIdentitySubsystem::FindTrainByPersistentGuid(const FGuid& PersistentGuid) const
{
    if (const TWeakObjectPtr<ALBPressTrainAStation>* Found = TrainsByGuid.Find(PersistentGuid)) return Found->Get();
    return nullptr;
}

bool ULBPressTrainIdentitySubsystem::CaptureAllTrains(ULBPressShopSaveGame* SaveRoot)
{
    UWorld* World = GetWorld();
    if (!SaveRoot || !World) return false;
    PurgeInvalidEntries();
    TArray<ALBPressTrainAStation*> Trains;
    if (bManagedSetEstablished)
    {
        for (const TWeakObjectPtr<ALBPressTrainAStation>& Managed : ManagedTrains)
            if (Managed.IsValid()) Trains.Add(Managed.Get());
    }
    else
    {
        // Migration path for pre-managed-set worlds: the first capture adopts the
        // currently authored train set. Subsequent captures remain campaign-owned.
        for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
            if (IsValid(*It)) Trains.Add(*It);
    }
    Trains.Sort([](const ALBPressTrainAStation& Left, const ALBPressTrainAStation& Right)
        { return Left.GetTrainId().LexicalLess(Right.GetTrainId()); });
    SaveRoot->PressTrains.Reset();
    TSet<FGuid> Guids;
    TSet<FName> Ids;
    for (ALBPressTrainAStation* Train : Trains)
    {
        if (!RegisterTrain(Train) || Guids.Contains(Train->GetPersistentTrainGuid()) || Ids.Contains(Train->GetTrainId()))
            return false;
        Guids.Add(Train->GetPersistentTrainGuid());
        Ids.Add(Train->GetTrainId());
        SaveRoot->PressTrains.Add(Train->CaptureSaveState());
        ManagedTrains.Add(Train);
    }
    if (const FLBPressTrainASaveState* TrainA = SaveRoot->PressTrains.FindByPredicate(
        [](const FLBPressTrainASaveState& State) { return State.TrainId == TEXT("TRAIN_A"); }))
        SaveRoot->PressTrainA = *TrainA;
    else
        SaveRoot->PressTrainA = FLBPressTrainASaveState();
    SaveRoot->SavedAtUtc = FDateTime::UtcNow();
    bManagedSetEstablished = true;
    return true;
}

bool ULBPressTrainIdentitySubsystem::RestoreAllTrains(const ULBPressShopSaveGame* SaveRoot)
{
    UWorld* World = GetWorld();
    if (!SaveRoot || !World || (SaveRoot->SaveFormatVersion != 13 && SaveRoot->SaveFormatVersion != 14
        && SaveRoot->SaveFormatVersion != 15 && SaveRoot->SaveFormatVersion != 16
        && SaveRoot->SaveFormatVersion != 17 && SaveRoot->SaveFormatVersion != 18)) return false;

    // Validate and order the complete requested set before touching a live actor.
    // TRAIN_A..TRAIN_D are unique, so designation order is deterministic on every load.
    TArray<FLBPressTrainASaveState> Records = SaveRoot->PressTrains;
    TSet<FGuid> SavedGuids;
    TSet<FName> SavedIds;
    for (const FLBPressTrainASaveState& State : Records)
    {
        const FVector Scale = State.WorldTransform.GetScale3D();
        if ((State.Version != 2 && State.Version != 3 && State.Version != 4)
            || !State.PersistentTrainGuid.IsValid() || !IsValidTrainId(State.TrainId)
            || State.WorldTransform.ContainsNaN() || Scale.GetAbsMax() > 100.0f
            || Scale.GetAbsMin() < 0.01f || !IsFinitePressTrainSaveState(State)
            || !StaticEnum<ELBPressTrainAState>()->IsValidEnumValue(static_cast<int64>(State.State))
            || !StaticEnum<ELBPressTrainAPhase>()->IsValidEnumValue(static_cast<int64>(State.Phase))
            || !StaticEnum<ELBPressTrainAFault>()->IsValidEnumValue(static_cast<int64>(State.ActiveFault))
            || SavedGuids.Contains(State.PersistentTrainGuid) || SavedIds.Contains(State.TrainId))
        {
            return false;
        }
        SavedGuids.Add(State.PersistentTrainGuid);
        SavedIds.Add(State.TrainId);
    }
    Records.Sort([](const FLBPressTrainASaveState& Left, const FLBPressTrainASaveState& Right)
        { return Left.TrainId.LexicalLess(Right.TrainId); });

    PurgeInvalidEntries();
    TArray<ALBPressTrainAStation*> LiveActors;
    TMap<FGuid, ALBPressTrainAStation*> LiveByGuid;
    TSet<FName> LiveIds;
    for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
    {
        ALBPressTrainAStation* Train = *It;
        if (!IsValid(Train)) continue;
        if (!Train->GetPersistentTrainGuid().IsValid()
            || LiveByGuid.Contains(Train->GetPersistentTrainGuid())
            || LiveIds.Contains(Train->GetTrainId())) return false;
        LiveActors.Add(Train);
        LiveByGuid.Add(Train->GetPersistentTrainGuid(), Train);
        LiveIds.Add(Train->GetTrainId());
    }

    TSet<ALBPressTrainAStation*> CurrentManagedSet;
    for (const TWeakObjectPtr<ALBPressTrainAStation>& Managed : ManagedTrains)
        if (Managed.IsValid()) CurrentManagedSet.Add(Managed.Get());
    // Backward-compatible same-world restore: an exact saved GUID remains managed
    // even if it predates the explicit managed-set bookkeeping.
    for (const FGuid& Guid : SavedGuids)
        if (ALBPressTrainAStation* const* Match = LiveByGuid.Find(Guid)) CurrentManagedSet.Add(*Match);

    // An unrelated authored actor is never destroyed or silently reassigned. It may
    // coexist when its identity is outside the save set; a conflicting designation
    // fails before the managed set or registry is changed.
    for (ALBPressTrainAStation* Train : LiveActors)
    {
        if (!CurrentManagedSet.Contains(Train) && SavedIds.Contains(Train->GetTrainId())) return false;
    }

    TArray<ALBPressTrainAStation*> CurrentManaged = CurrentManagedSet.Array();
    CurrentManaged.Sort([](const ALBPressTrainAStation& Left, const ALBPressTrainAStation& Right)
        { return Left.GetTrainId().LexicalLess(Right.GetTrainId()); });
    TArray<FLBPressTrainASaveState> PreviousStates;
    PreviousStates.Reserve(CurrentManaged.Num());
    for (ALBPressTrainAStation* Train : CurrentManaged) PreviousStates.Add(Train->CaptureSaveState());

    const auto RestorePreviousRegistry = [this, &CurrentManaged, &PreviousStates]()
    {
        bool bRestored = CurrentManaged.Num() == PreviousStates.Num();
        for (int32 Index = 0; Index < CurrentManaged.Num(); ++Index)
        {
            ALBPressTrainAStation* Train = CurrentManaged[Index];
            if (!IsValid(Train))
            {
                bRestored = false;
                continue;
            }
            const FLBPressTrainASaveState& Previous = PreviousStates[Index];
            bRestored = RestoreTrainIdentity(Train, Previous.PersistentTrainGuid,
                Previous.TrainId, Previous.TrainDisplayName) && bRestored;
            ManagedTrains.Add(Train);
        }
        return bRestored;
    };

    // Keep the old managed actors alive and unchanged while replacement actors prove
    // that every record, identity and complete presentation can be restored.
    for (ALBPressTrainAStation* Train : CurrentManaged) ReleaseTrain(Train);

    TArray<ALBPressTrainAStation*> Staged;
    Staged.Reserve(Records.Num());
    FActorSpawnParameters SpawnParameters;
    SpawnParameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    bool bStageSucceeded = true;
    for (const FLBPressTrainASaveState& State : Records)
    {
        ALBPressTrainAStation* Train = World->SpawnActor<ALBPressTrainAStation>(
            ALBPressTrainAStation::StaticClass(), State.WorldTransform, SpawnParameters);
        if (!Train)
        {
            bStageSucceeded = false;
            break;
        }
        Staged.Add(Train);
        if (!RestoreTrainIdentity(Train, State.PersistentTrainGuid, State.TrainId, State.TrainDisplayName)
            || !Train->RestoreSaveState(State) || !Train->EnableCompletedRuntimeVisual()
            || !Train->HasCompletedRuntimeVisual() || Train->GetApprovedModularVisualCount() != 105)
        {
            bStageSucceeded = false;
            break;
        }
    }
    if (!bStageSucceeded)
    {
        for (ALBPressTrainAStation* Train : Staged)
            if (IsValid(Train)) Train->Destroy();
        RestorePreviousRegistry();
        return false;
    }

    bool bReuseExisting = CurrentManaged.Num() == Records.Num();
    TMap<FGuid, ALBPressTrainAStation*> ExistingByGuid;
    for (ALBPressTrainAStation* Train : CurrentManaged)
        ExistingByGuid.Add(Train->GetPersistentTrainGuid(), Train);
    for (const FLBPressTrainASaveState& State : Records)
        if (!ExistingByGuid.Contains(State.PersistentTrainGuid)) bReuseExisting = false;

    if (bReuseExisting)
    {
        // Preserve live references on the traditional same-world load path. The
        // staged set has already proved each record and presentation can restore.
        for (ALBPressTrainAStation* Train : Staged)
            if (IsValid(Train)) Train->Destroy();
        bool bCommitted = true;
        for (const FLBPressTrainASaveState& State : Records)
        {
            ALBPressTrainAStation* Train = ExistingByGuid.FindChecked(State.PersistentTrainGuid);
            bCommitted = RestoreTrainIdentity(Train, State.PersistentTrainGuid,
                State.TrainId, State.TrainDisplayName) && Train->RestoreSaveState(State)
                && Train->EnableCompletedRuntimeVisual() && Train->HasCompletedRuntimeVisual()
                && Train->GetApprovedModularVisualCount() == 105 && bCommitted;
            ManagedTrains.Add(Train);
        }
        if (bCommitted)
        {
            bManagedSetEstablished = true;
            return true;
        }

        // This path is defensive: deterministic staging makes a commit failure
        // unreachable under normal play, but restore the previous snapshots if an
        // actor was invalidated by external code during the synchronous transaction.
        for (ALBPressTrainAStation* Train : CurrentManaged) ReleaseTrain(Train);
        bool bRolledBack = true;
        for (int32 Index = 0; Index < CurrentManaged.Num(); ++Index)
        {
            ALBPressTrainAStation* Train = CurrentManaged[Index];
            const FLBPressTrainASaveState& Previous = PreviousStates[Index];
            bRolledBack = IsValid(Train)
                && RestoreTrainIdentity(Train, Previous.PersistentTrainGuid,
                    Previous.TrainId, Previous.TrainDisplayName)
                && Train->RestoreSaveState(Previous) && bRolledBack;
            if (IsValid(Train)) ManagedTrains.Add(Train);
        }
        ensureMsgf(bRolledBack, TEXT("Press-train restore rollback could not recreate the previous managed set"));
        return false;
    }

    // Cold-world/set-replacement commit. Staged actors now are the managed set; only
    // prior managed actors are removed. Owner-checked ReleaseTrain keeps staged map
    // entries intact while superseded actors receive EndPlay.
    for (ALBPressTrainAStation* Train : Staged) ManagedTrains.Add(Train);
    for (ALBPressTrainAStation* Train : CurrentManaged)
        if (IsValid(Train)) Train->Destroy();
    bManagedSetEstablished = true;
    return true;
}

FBox ULBPressTrainIdentitySubsystem::BuildProtectedEnvelope(const FTransform& WorldTransform)
{
    return ALBPressTrainAStation::GetProtectedLocalEnvelope().TransformBy(WorldTransform);
}

bool ULBPressTrainIdentitySubsystem::PlaceTrain(const FTransform& WorldTransform,
    const FString& DisplayName, const FString& PartFamily, ALBPressTrainAStation*& OutTrain)
{
    OutTrain = nullptr;
    UWorld* World = GetWorld();
    FString PlacementReason;
    if (!World || DisplayName.TrimStartAndEnd().IsEmpty() || PartFamily.TrimStartAndEnd().IsEmpty()
        || !CanPlaceTrain(WorldTransform, PlacementReason)) return false;

    ALBPressTrainAStation* Train = World->SpawnActor<ALBPressTrainAStation>(
        ALBPressTrainAStation::StaticClass(), WorldTransform);
    if (!Train || !RegisterTrain(Train)
        || !Train->ConfigureTrainVariant(Train->GetTrainId(), DisplayName, PartFamily, FLinearColor(0.231f, 0.510f, 0.769f))
        || !Train->EnableCompletedRuntimeVisual())
    {
        if (Train) Train->Destroy();
        return false;
    }
    ManagedTrains.Add(Train);
    bManagedSetEstablished = true;
    OutTrain = Train;
    return true;
}

bool ULBPressTrainIdentitySubsystem::CanPlaceTrain(const FTransform& WorldTransform, FString& OutReason) const
{
    OutReason.Reset();
    UWorld* World = GetWorld();
    const FVector Scale = WorldTransform.GetScale3D();
    if (!World || WorldTransform.ContainsNaN() || !Scale.Equals(FVector::OneVector, 0.001f))
    {
        OutReason = TEXT("INVALID TRANSFORM OR SCALE");
        return false;
    }

    const FBox Candidate = BuildProtectedEnvelope(WorldTransform);

    ALBPressShopBuildAuthority* BuildAuthority = nullptr;
    for (TActorIterator<ALBPressShopBuildAuthority> It(World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        if (BuildAuthority)
        {
            OutReason = TEXT("MULTIPLE PRESS SHOP BUILD AUTHORITIES");
            return false;
        }
        BuildAuthority = *It;
    }
    if (!BuildAuthority)
    {
        OutReason = TEXT("PRESS SHOP BUILD AUTHORITY MISSING");
        return false;
    }
    if (!BuildAuthority->EvaluateTrainEnvelope(Candidate, OutReason)) return false;

    for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
    {
        if (IsValid(*It) && Candidate.Intersect(BuildProtectedEnvelope(It->GetActorTransform())))
        {
            OutReason = FString::Printf(TEXT("PROTECTED ENVELOPE OVERLAPS %s"), *It->GetTrainId().ToString());
            return false;
        }
    }
    const FString AuthorityReason = OutReason;
    OutReason = FString::Printf(TEXT("TRAIN ENVELOPE CLEAR; %s"), *AuthorityReason);
    return true;
}

bool ULBPressTrainIdentitySubsystem::RemoveTrain(ALBPressTrainAStation* Train)
{
    if (!IsValid(Train)) return false;
    const FLBPressTrainAHMIStatus Status = Train->GetHMIStatus();
    if (Status.State != ELBPressTrainAState::Isolated || Status.PendingBlankCount != 0
        || !Status.InProcessBlankId.IsNone() || Status.PendingPanelCount != 0) return false;
    ReleaseTrain(Train);
    return Train->Destroy();
}
