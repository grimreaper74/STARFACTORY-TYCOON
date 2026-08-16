#include "LBPaintShopPrototypeRuntime.h"

#include "LBBodyWeldLineActor.h"
#include "LBPaintShopBuildAuthority.h"
#include "LBPaintShopCellActor.h"

#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

namespace LBPaintShopPrototypeRuntimePrivate
{
    float LocalProgress(const float CycleProgress, const float Start, const float End)
    {
        return FMath::Clamp((CycleProgress - Start) / (End - Start), 0.0f, 1.0f);
    }

    bool IsApprovedCell(const FLBPaintShopPlacedCellSaveState& Cell)
    {
        const FLBPaintShopApprovedEDCoatLayoutItem Approved =
            ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
        return Cell.CellId == Approved.CellId && Cell.DefinitionId == Approved.DefinitionId
            && Cell.WorldTransform.Equals(Approved.WorldTransform);
    }
}

ALBPaintShopPrototypeRuntime::ALBPaintShopPrototypeRuntime()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    SetActorEnableCollision(false);
    Tags.AddUnique(TEXT("LB.PaintShop.Experimental.Runtime.v001"));
}

void ALBPaintShopPrototypeRuntime::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bInitialized && !bPaused && !bProcessFaulted)
    {
        AdvanceSimulation(DeltaSeconds);
    }
}

bool ALBPaintShopPrototypeRuntime::BindBuildAuthority(
    ALBPaintShopBuildAuthority* InAuthority, FString& OutReason)
{
    OutReason.Reset();
    if (!InAuthority || !IsValid(InAuthority))
    {
        OutReason = TEXT("PAINT RUNTIME REQUIRES A VALID BUILD AUTHORITY");
        return false;
    }
    if (BuildAuthority || bInitialized)
    {
        OutReason = TEXT("PAINT RUNTIME BUILD AUTHORITY IS ALREADY BOUND");
        return false;
    }
    if (InAuthority->GetWorld() != GetWorld())
    {
        OutReason = TEXT("PAINT RUNTIME AND BUILD AUTHORITY MUST SHARE ONE WORLD");
        return false;
    }
    BuildAuthority = InAuthority;
    return true;
}

bool ALBPaintShopPrototypeRuntime::InitializePrototype(FString& OutReason)
{
    OutReason.Reset();
    if (bInitialized)
    {
        const ALBPaintShopCellActor* Cell = GetEDCoatCell();
        if (BuildAuthority && IsValid(BuildAuthority) && Cell && Cell->IsConfigured())
        {
            return true;
        }
        OutReason = TEXT("PAINT RUNTIME INITIALIZED STATE IS INCOHERENT");
        return false;
    }

    if (!BuildAuthority || !IsValid(BuildAuthority) || BuildAuthority->GetWorld() != GetWorld())
    {
        OutReason = TEXT("PAINT RUNTIME REQUIRES ITS BOUND BUILD AUTHORITY");
        return false;
    }

    if (!BuildAuthority->BuildApprovedEDCoatDipLayout(OutReason))
    {
        return false;
    }

    const FLBPaintShopApprovedEDCoatLayoutItem Approved =
        ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
    ALBPaintShopCellActor* Cell = BuildAuthority->FindCell(Approved.CellId);
    FLBPaintShopCellPresentationState IdlePresentation =
        MakePresentationState(false, 0.0f, false);
    FString PresentationReason;
    if (!Cell || !Cell->IsConfigured()
        || !ALBPaintShopCellActor::ValidatePresentationState(
            IdlePresentation, PresentationReason)
        || !Cell->SetPresentationState(IdlePresentation, PresentationReason))
    {
        OutReason = PresentationReason.IsEmpty()
            ? TEXT("PAINT RUNTIME CELL INITIALIZATION FAILED") : PresentationReason;
        return false;
    }

    bInitialized = true;
    bHasActiveWIP = false;
    ActiveWIP = FLBPaintShopWIPSaveState();
    bPaused = false;
    bOutputBlocked = false;
    bProcessFaulted = false;
    ProcessFaultReason.Reset();
    Phase = ELBPaintShopPrototypePhase::Starved;
    PhaseProgress01 = 0.0f;
    CycleProgress01 = 0.0f;
    NextWIPSerial = 1;
    NextGenealogySequence = 1;
    return true;
}

bool ALBPaintShopPrototypeRuntime::AcceptAndAcknowledgeBodyInWhite(
    ALBBodyWeldLineActor* SourceLine, const FName BodyId, const FName CarrierId,
    FString& OutReason)
{
    OutReason.Reset();
    if (!bInitialized || !IsValid(BuildAuthority) || !GetEDCoatCell())
    {
        OutReason = TEXT("PAINT RUNTIME IS NOT INITIALIZED");
        return false;
    }
    if (bProcessFaulted)
    {
        OutReason = TEXT("PAINT RUNTIME IS FAULTED");
        return false;
    }
    if (!IsValid(SourceLine) || SourceLine->GetWorld() != GetWorld()
        || BodyId.IsNone() || CarrierId.IsNone())
    {
        OutReason = TEXT("WELD SOURCE, BODY ID, AND CARRIER ID ARE REQUIRED");
        return false;
    }
    if (bHasActiveWIP)
    {
        OutReason = ActiveWIP.CarrierId == CarrierId
            || ActiveWIP.SourceBodyInWhite.BodyId == BodyId
            ? TEXT("PAINT RUNTIME REJECTED DUPLICATE ACTIVE IDENTITY")
            : TEXT("PAINT RUNTIME ONE-WIP CAPACITY IS FULL");
        return false;
    }
    if (NextWIPSerial < 1 || NextWIPSerial == MAX_int32
        || NextGenealogySequence < 1 || NextGenealogySequence == MAX_int64)
    {
        OutReason = TEXT("PAINT RUNTIME IDENTITY COUNTER IS EXHAUSTED");
        return false;
    }

    FLBBodyInWhiteRecord Candidate;
    if (!SourceLine->IsEDAvailable() || !SourceLine->GetOutputBody(Candidate)
        || Candidate.BodyId != BodyId || Candidate.bEDAccepted)
    {
        OutReason = TEXT("REQUESTED BODY IS NOT AVAILABLE AT THE WELD ED BOUNDARY");
        return false;
    }

    FLBPaintShopExperimentalSaveState TentativeState;
    if (!BuildTentativeAcceptedSave(Candidate, CarrierId, TentativeState, OutReason))
    {
        return false;
    }

    FLBBodyInWhiteRecord TransferredBody;
    if (!SourceLine->AcknowledgeEDTransfer(BodyId, TransferredBody))
    {
        OutReason = TEXT("WELD ED ACKNOWLEDGEMENT FAILED WITHOUT PAINT MUTATION");
        return false;
    }

    // Every fallible Paint-side operation completed above. These assignments are the
    // transaction commit, and the exact record returned by Weld replaces the preflight copy.
    ActiveWIP = MoveTemp(TentativeState.WIP[0]);
    ActiveWIP.SourceBodyInWhite = MoveTemp(TransferredBody);
    bHasActiveWIP = true;
    NextWIPSerial = TentativeState.NextWIPSerial;
    NextGenealogySequence = TentativeState.NextGenealogySequence;
    bPaused = false;
    bProcessFaulted = false;
    ProcessFaultReason.Reset();
    CycleProgress01 = 0.0f;
    Phase = ELBPaintShopPrototypePhase::Loading;
    PhaseProgress01 = 0.0f;
    return true;
}

void ALBPaintShopPrototypeRuntime::AdvanceSimulation(const float DeltaSeconds)
{
    if (!bInitialized)
    {
        return;
    }
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds < 0.0f)
    {
        EnterProcessFault(TEXT("PAINT PROCESS RECEIVED INVALID DELTA SECONDS"));
        return;
    }
    if (bProcessFaulted || bPaused)
    {
        return;
    }
    if (!bHasActiveWIP)
    {
        UpdatePhaseFromCycleProgress();
    }
    else if (CycleProgress01 < DrainEndProgress01)
    {
        CycleProgress01 = FMath::Clamp(CycleProgress01
            + DeltaSeconds / GetTotalCycleDurationSeconds(), 0.0f, DrainEndProgress01);
        if (CycleProgress01 >= DrainEndProgress01)
        {
            ActiveWIP.MaterialId = LBPaintShopWIPIds::BIWEDCoated;
        }
        UpdatePhaseFromCycleProgress();
    }

    FString PresentationReason;
    if (!ApplyPresentation(PresentationReason))
    {
        EnterProcessFault(PresentationReason.IsEmpty()
            ? TEXT("PAINT CELL PRESENTATION UPDATE FAILED") : PresentationReason);
    }
}

void ALBPaintShopPrototypeRuntime::SetPaused(const bool bInPaused)
{
    bPaused = bInitialized && bHasActiveWIP && !bProcessFaulted
        && Phase != ELBPaintShopPrototypePhase::OutputReady && bInPaused;
}

void ALBPaintShopPrototypeRuntime::SetOutputBlocked(const bool bInBlocked)
{
    bOutputBlocked = bInBlocked;
}

bool ALBPaintShopPrototypeRuntime::ReleaseOutput(FLBPaintShopWIPSaveState& OutReleasedWIP,
    FString& OutReason)
{
    OutReleasedWIP = FLBPaintShopWIPSaveState();
    OutReason.Reset();
    if (!bInitialized || bProcessFaulted || !bHasActiveWIP
        || Phase != ELBPaintShopPrototypePhase::OutputReady
        || ActiveWIP.MaterialId != LBPaintShopWIPIds::BIWEDCoated)
    {
        OutReason = TEXT("NO VALID ED-COATED OUTPUT IS READY");
        return false;
    }
    if (bOutputBlocked)
    {
        OutReason = TEXT("PAINT OUTPUT IS BLOCKED; COATED WIP IS RETAINED");
        return false;
    }

    ALBPaintShopCellActor* Cell = GetEDCoatCell();
    FLBPaintShopCellPresentationState IdlePresentation =
        MakePresentationState(false, 0.0f, false);
    FString PresentationReason;
    if (!Cell || !ALBPaintShopCellActor::ValidatePresentationState(
            IdlePresentation, PresentationReason)
        || !Cell->SetPresentationState(IdlePresentation, PresentationReason))
    {
        EnterProcessFault(PresentationReason.IsEmpty()
            ? TEXT("PAINT OUTPUT RELEASE PRESENTATION PREFLIGHT FAILED") : PresentationReason);
        OutReason = ProcessFaultReason;
        return false;
    }

    OutReleasedWIP = ActiveWIP;
    ActiveWIP = FLBPaintShopWIPSaveState();
    bHasActiveWIP = false;
    bPaused = false;
    CycleProgress01 = 0.0f;
    Phase = ELBPaintShopPrototypePhase::Starved;
    PhaseProgress01 = 0.0f;
    return true;
}

bool ALBPaintShopPrototypeRuntime::CaptureSaveState(
    FLBPaintShopExperimentalSaveState& OutState, FString& OutReason) const
{
    OutState = FLBPaintShopExperimentalSaveState();
    OutReason.Reset();
    if (!bInitialized || !IsValid(BuildAuthority)
        || !BuildAuthority->CaptureTopologySaveState(OutState, OutReason)
        || OutState.Cells.Num() != 1)
    {
        if (OutReason.IsEmpty())
        {
            OutReason = TEXT("PAINT RUNTIME CANNOT CAPTURE ITS TOPOLOGY");
        }
        return false;
    }

    FLBPaintShopPlacedCellSaveState& Cell = OutState.Cells[0];
    Cell.bCommissioned = true;
    Cell.ProcessProgress01 = CycleProgress01;
    Cell.bProcessPaused = bPaused;
    Cell.bOutputBlocked = bOutputBlocked;
    Cell.QueuedWIPIds.Reset();
    Cell.ActiveWIPId = NAME_None;
    if (bProcessFaulted)
    {
        Cell.State = ELBPaintShopExperimentalCellState::Faulted;
    }
    else if (!bHasActiveWIP)
    {
        Cell.State = ELBPaintShopExperimentalCellState::Starved;
    }
    else if (Phase == ELBPaintShopPrototypePhase::OutputReady)
    {
        Cell.State = bOutputBlocked ? ELBPaintShopExperimentalCellState::Blocked
                                    : ELBPaintShopExperimentalCellState::Idle;
    }
    else
    {
        Cell.State = ELBPaintShopExperimentalCellState::Processing;
    }

    OutState.WIP.Reset();
    if (bHasActiveWIP)
    {
        FLBPaintShopWIPSaveState SavedWIP = ActiveWIP;
        OutState.WIP.Add(SavedWIP);
        Cell.ActiveWIPId = SavedWIP.UnitId;
    }
    OutState.NextWIPSerial = NextWIPSerial;
    OutState.NextGenealogySequence = NextGenealogySequence;
    if (!ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(OutState, OutReason)
        || !ValidateRuntimeSaveShape(OutState, OutReason))
    {
        OutState = FLBPaintShopExperimentalSaveState();
        return false;
    }
    return true;
}

bool ALBPaintShopPrototypeRuntime::RestoreSaveState(
    const FLBPaintShopExperimentalSaveState& State, FString& OutReason)
{
    OutReason.Reset();
    if (!bInitialized || !IsValid(BuildAuthority))
    {
        OutReason = TEXT("PAINT RUNTIME MUST BE INITIALIZED BEFORE RESTORE");
        return false;
    }
    if (!ValidateRuntimeSaveShape(State, OutReason))
    {
        return false;
    }

    FLBPaintShopExperimentalSaveState PreviousState;
    FString PreviousCaptureReason;
    if (!CaptureSaveState(PreviousState, PreviousCaptureReason))
    {
        OutReason = PreviousCaptureReason.IsEmpty()
            ? TEXT("PAINT RESTORE COULD NOT CAPTURE ITS ROLLBACK STATE")
            : PreviousCaptureReason;
        return false;
    }

    const FLBPaintShopPlacedCellSaveState& SavedCell = State.Cells[0];
    const bool bRestoredHasWIP = State.WIP.Num() == 1;
    const bool bRestoredFault = SavedCell.State == ELBPaintShopExperimentalCellState::Faulted;
    const bool bRestoredOutputBlocked =
        SavedCell.bOutputBlocked
        || SavedCell.State == ELBPaintShopExperimentalCellState::Blocked;
    const FLBPaintShopCellPresentationState RestoredPresentation = MakePresentationState(
        bRestoredHasWIP, SavedCell.ProcessProgress01, bRestoredFault);
    FString PresentationReason;
    if (!ALBPaintShopCellActor::ValidatePresentationState(
        RestoredPresentation, PresentationReason))
    {
        OutReason = PresentationReason;
        return false;
    }

    FLBPaintShopExperimentalSaveState StrippedTopology = State;
    StrippedTopology.WIP.Reset();
    for (FLBPaintShopPlacedCellSaveState& Cell : StrippedTopology.Cells)
    {
        Cell.QueuedWIPIds.Reset();
        Cell.ActiveWIPId = NAME_None;
        Cell.bProcessPaused = false;
        Cell.bOutputBlocked = false;
    }
    if (!BuildAuthority->RestoreTopologySaveState(StrippedTopology, OutReason))
    {
        return false;
    }

    ALBPaintShopCellActor* RestoredCell = GetEDCoatCell();
    if (!RestoredCell
        || !RestoredCell->SetPresentationState(RestoredPresentation, PresentationReason))
    {
        const FString RestoreFailure = PresentationReason.IsEmpty()
            ? TEXT("RESTORED PAINT CELL PRESENTATION COULD NOT BE APPLIED")
            : PresentationReason;

        FLBPaintShopExperimentalSaveState PreviousTopology = PreviousState;
        PreviousTopology.WIP.Reset();
        for (FLBPaintShopPlacedCellSaveState& Cell : PreviousTopology.Cells)
        {
            Cell.QueuedWIPIds.Reset();
            Cell.ActiveWIPId = NAME_None;
            Cell.bProcessPaused = false;
            Cell.bOutputBlocked = false;
        }
        FString RollbackReason;
        bool bRolledBack = BuildAuthority->RestoreTopologySaveState(
            PreviousTopology, RollbackReason);
        if (bRolledBack && PreviousState.Cells.Num() == 1)
        {
            const FLBPaintShopPlacedCellSaveState& PreviousCell = PreviousState.Cells[0];
            const FLBPaintShopCellPresentationState PreviousPresentation =
                MakePresentationState(PreviousState.WIP.Num() == 1,
                    PreviousCell.ProcessProgress01,
                    PreviousCell.State == ELBPaintShopExperimentalCellState::Faulted);
            ALBPaintShopCellActor* RolledBackCell = GetEDCoatCell();
            bRolledBack = RolledBackCell
                && RolledBackCell->SetPresentationState(
                    PreviousPresentation, RollbackReason);
        }
        if (bRolledBack)
        {
            OutReason = RestoreFailure;
            return false;
        }

        EnterProcessFault(FString::Printf(
            TEXT("%s; ROLLBACK FAILED: %s"), *RestoreFailure,
            RollbackReason.IsEmpty() ? TEXT("UNKNOWN ROLLBACK FAILURE")
                                     : *RollbackReason));
        OutReason = ProcessFaultReason;
        return false;
    }

    bHasActiveWIP = bRestoredHasWIP;
    ActiveWIP = bRestoredHasWIP ? State.WIP[0] : FLBPaintShopWIPSaveState();
    bPaused = SavedCell.bProcessPaused;
    bOutputBlocked = bRestoredOutputBlocked;
    bProcessFaulted = bRestoredFault;
    if (bRestoredFault)
    {
        ProcessFaultReason = TEXT("RESTORED_PAINT_PROCESS_FAULT");
    }
    else
    {
        ProcessFaultReason.Reset();
    }
    CycleProgress01 = SavedCell.ProcessProgress01;
    NextWIPSerial = State.NextWIPSerial;
    NextGenealogySequence = State.NextGenealogySequence;
    UpdatePhaseFromCycleProgress();
    return true;
}

bool ALBPaintShopPrototypeRuntime::SaveToExperimentalSlot(FString& OutReason) const
{
    return SaveToSlot(ULBPaintShopExperimentalSaveGame::GetSlotName().ToString(),
        ULBPaintShopExperimentalSaveGame::GetUserIndex(), OutReason);
}

bool ALBPaintShopPrototypeRuntime::LoadFromExperimentalSlot(FString& OutReason)
{
    return LoadFromSlot(ULBPaintShopExperimentalSaveGame::GetSlotName().ToString(),
        ULBPaintShopExperimentalSaveGame::GetUserIndex(), OutReason);
}

#if WITH_DEV_AUTOMATION_TESTS
bool ALBPaintShopPrototypeRuntime::SaveToAutomationSlot(
    const FString& SlotName, FString& OutReason) const
{
    if (!SlotName.StartsWith(TEXT("LineBossPaintShopExperimental_Automation_")))
    {
        OutReason = TEXT("PAINT AUTOMATION SAVE REJECTED A NON-AUTOMATION SLOT");
        return false;
    }
    return SaveToSlot(SlotName, ULBPaintShopExperimentalSaveGame::GetUserIndex(), OutReason);
}

bool ALBPaintShopPrototypeRuntime::LoadFromAutomationSlot(
    const FString& SlotName, FString& OutReason)
{
    if (!SlotName.StartsWith(TEXT("LineBossPaintShopExperimental_Automation_")))
    {
        OutReason = TEXT("PAINT AUTOMATION LOAD REJECTED A NON-AUTOMATION SLOT");
        return false;
    }
    return LoadFromSlot(SlotName, ULBPaintShopExperimentalSaveGame::GetUserIndex(), OutReason);
}
#endif

bool ALBPaintShopPrototypeRuntime::SaveToSlot(
    const FString& SlotName, const int32 UserIndex, FString& OutReason) const
{
    OutReason.Reset();
    if (SlotName.IsEmpty() || UserIndex < 0)
    {
        OutReason = TEXT("PAINT SAVE SLOT IDENTITY IS INVALID");
        return false;
    }

    FLBPaintShopExperimentalSaveState CapturedState;
    if (!CaptureSaveState(CapturedState, OutReason))
    {
        return false;
    }

    ULBPaintShopExperimentalSaveGame* Save = Cast<ULBPaintShopExperimentalSaveGame>(
        UGameplayStatics::CreateSaveGameObject(
            ULBPaintShopExperimentalSaveGame::StaticClass()));
    if (!Save)
    {
        OutReason = TEXT("PAINT SAVE OBJECT COULD NOT BE CREATED");
        return false;
    }
    Save->SaveSchemaVersion = ULBPaintShopExperimentalSaveGame::SchemaVersion;
    Save->PrototypeMapId = TEXT("LB_PaintShop_Prototype_v001");
    Save->State = MoveTemp(CapturedState);
    if (!Save->ValidateForLoad(OutReason))
    {
        return false;
    }
    if (!UGameplayStatics::SaveGameToSlot(Save, SlotName, UserIndex))
    {
        OutReason = TEXT("PAINT ISOLATED SAVE COULD NOT BE WRITTEN");
        return false;
    }
    OutReason = TEXT("PAINT ISOLATED STATE SAVED");
    return true;
}

bool ALBPaintShopPrototypeRuntime::LoadFromSlot(
    const FString& SlotName, const int32 UserIndex, FString& OutReason)
{
    OutReason.Reset();
    if (SlotName.IsEmpty() || UserIndex < 0)
    {
        OutReason = TEXT("PAINT LOAD SLOT IDENTITY IS INVALID");
        return false;
    }
    if (!UGameplayStatics::DoesSaveGameExist(SlotName, UserIndex))
    {
        OutReason = TEXT("PAINT ISOLATED SAVE DOES NOT EXIST");
        return false;
    }

    const ULBPaintShopExperimentalSaveGame* Save =
        Cast<ULBPaintShopExperimentalSaveGame>(
            UGameplayStatics::LoadGameFromSlot(SlotName, UserIndex));
    if (!Save)
    {
        OutReason = TEXT("PAINT ISOLATED SAVE HAS THE WRONG ROOT TYPE");
        return false;
    }
    if (!Save->ValidateForLoad(OutReason))
    {
        return false;
    }

    // RestoreSaveState validates the stricter one-cell runtime shape before its
    // topology transaction. Disk/type/schema failures above leave live state untouched.
    if (!RestoreSaveState(Save->State, OutReason))
    {
        return false;
    }
    OutReason = TEXT("PAINT ISOLATED STATE LOADED");
    return true;
}

bool ALBPaintShopPrototypeRuntime::GetActiveWIP(FLBPaintShopWIPSaveState& OutWIP) const
{
    OutWIP = ActiveWIP;
    return bHasActiveWIP;
}

ALBPaintShopCellActor* ALBPaintShopPrototypeRuntime::GetEDCoatCell() const
{
    if (!IsValid(BuildAuthority))
    {
        return nullptr;
    }
    return BuildAuthority->FindCell(
        ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout().CellId);
}

void ALBPaintShopPrototypeRuntime::UpdatePhaseFromCycleProgress()
{
    if (!bInitialized)
    {
        Phase = ELBPaintShopPrototypePhase::Uninitialized;
        PhaseProgress01 = 0.0f;
        return;
    }
    if (bProcessFaulted)
    {
        Phase = ELBPaintShopPrototypePhase::Faulted;
        PhaseProgress01 = 0.0f;
        return;
    }
    if (!bHasActiveWIP)
    {
        Phase = ELBPaintShopPrototypePhase::Starved;
        PhaseProgress01 = 0.0f;
        CycleProgress01 = 0.0f;
        return;
    }
    if (CycleProgress01 >= DrainEndProgress01)
    {
        Phase = ELBPaintShopPrototypePhase::OutputReady;
        PhaseProgress01 = 1.0f;
        return;
    }
    if (CycleProgress01 < LoadEndProgress01)
    {
        Phase = ELBPaintShopPrototypePhase::Loading;
        PhaseProgress01 = LBPaintShopPrototypeRuntimePrivate::LocalProgress(
            CycleProgress01, 0.0f, LoadEndProgress01);
    }
    else if (CycleProgress01 < DescendEndProgress01)
    {
        Phase = ELBPaintShopPrototypePhase::Descending;
        PhaseProgress01 = LBPaintShopPrototypeRuntimePrivate::LocalProgress(
            CycleProgress01, LoadEndProgress01, DescendEndProgress01);
    }
    else if (CycleProgress01 < ImmerseEndProgress01)
    {
        Phase = ELBPaintShopPrototypePhase::Immersing;
        PhaseProgress01 = LBPaintShopPrototypeRuntimePrivate::LocalProgress(
            CycleProgress01, DescendEndProgress01, ImmerseEndProgress01);
    }
    else if (CycleProgress01 < RiseEndProgress01)
    {
        Phase = ELBPaintShopPrototypePhase::Rising;
        PhaseProgress01 = LBPaintShopPrototypeRuntimePrivate::LocalProgress(
            CycleProgress01, ImmerseEndProgress01, RiseEndProgress01);
    }
    else
    {
        Phase = ELBPaintShopPrototypePhase::Draining;
        PhaseProgress01 = LBPaintShopPrototypeRuntimePrivate::LocalProgress(
            CycleProgress01, RiseEndProgress01, DrainEndProgress01);
    }
}

bool ALBPaintShopPrototypeRuntime::ApplyPresentation(FString& OutReason)
{
    OutReason.Reset();
    ALBPaintShopCellActor* Cell = GetEDCoatCell();
    if (!Cell || !Cell->IsConfigured())
    {
        OutReason = TEXT("PAINT RUNTIME HAS NO CONFIGURED ED-COAT CELL");
        return false;
    }
    const FLBPaintShopCellPresentationState Presentation = MakePresentationState(
        bHasActiveWIP, CycleProgress01, bProcessFaulted);
    return Cell->SetPresentationState(Presentation, OutReason);
}

void ALBPaintShopPrototypeRuntime::EnterProcessFault(const FString& Reason)
{
    bProcessFaulted = true;
    bPaused = false;
    ProcessFaultReason = Reason.IsEmpty() ? TEXT("PAINT_PROCESS_FAULT") : Reason;
    Phase = ELBPaintShopPrototypePhase::Faulted;
    PhaseProgress01 = 0.0f;

    if (ALBPaintShopCellActor* Cell = GetEDCoatCell())
    {
        const FLBPaintShopCellPresentationState FaultPresentation =
            MakePresentationState(bHasActiveWIP, CycleProgress01, true);
        FString IgnoredReason;
        Cell->SetPresentationState(FaultPresentation, IgnoredReason);
    }
}

bool ALBPaintShopPrototypeRuntime::BuildTentativeAcceptedSave(
    const FLBBodyInWhiteRecord& Candidate, const FName CarrierId,
    FLBPaintShopExperimentalSaveState& OutState, FString& OutReason) const
{
    OutState = FLBPaintShopExperimentalSaveState();
    OutReason.Reset();
    ALBPaintShopCellActor* CellActor = GetEDCoatCell();
    if (!IsValid(BuildAuthority) || !CellActor || !CellActor->IsConfigured()
        || !BuildAuthority->CaptureTopologySaveState(OutState, OutReason)
        || OutState.Cells.Num() != 1)
    {
        if (OutReason.IsEmpty())
        {
            OutReason = TEXT("PAINT ACCEPT PREFLIGHT COULD NOT CAPTURE EXACT TOPOLOGY");
        }
        return false;
    }

    FLBBodyInWhiteRecord AcknowledgedCandidate = Candidate;
    AcknowledgedCandidate.bEDAccepted = true;
    FLBPaintShopWIPSaveState Unit;
    Unit.Version = 2;
    Unit.UnitId = FName(*FString::Printf(TEXT("PAINT_WIP_%06d"), NextWIPSerial));
    Unit.MaterialId = LBPaintShopWIPIds::BIWComplete;
    Unit.CurrentCellId = OutState.Cells[0].CellId;
    Unit.CarrierId = CarrierId;
    Unit.GenealogySequence = NextGenealogySequence;
    Unit.SourceBodyInWhite = MoveTemp(AcknowledgedCandidate);

    FLBPaintShopPlacedCellSaveState& Cell = OutState.Cells[0];
    Cell.State = ELBPaintShopExperimentalCellState::Processing;
    Cell.bCommissioned = true;
    Cell.QueuedWIPIds.Reset();
    Cell.ActiveWIPId = Unit.UnitId;
    Cell.ProcessProgress01 = 0.0f;
    OutState.WIP = {Unit};
    OutState.NextWIPSerial = NextWIPSerial + 1;
    OutState.NextGenealogySequence = NextGenealogySequence + 1;
    if (!ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(OutState, OutReason)
        || !ValidateRuntimeSaveShape(OutState, OutReason))
    {
        OutState = FLBPaintShopExperimentalSaveState();
        return false;
    }

    const FLBPaintShopCellPresentationState Presentation =
        MakePresentationState(true, 0.0f, false);
    if (!ALBPaintShopCellActor::ValidatePresentationState(Presentation, OutReason))
    {
        OutState = FLBPaintShopExperimentalSaveState();
        return false;
    }
    return true;
}

bool ALBPaintShopPrototypeRuntime::ValidateRuntimeSaveShape(
    const FLBPaintShopExperimentalSaveState& State, FString& OutReason)
{
    OutReason.Reset();
    if (!ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(State, OutReason))
    {
        return false;
    }
    if (State.Cells.Num() != 1 || !State.Connections.IsEmpty() || State.WIP.Num() > 1
        || !LBPaintShopPrototypeRuntimePrivate::IsApprovedCell(State.Cells[0]))
    {
        OutReason = TEXT("PAINT RUNTIME SAVE MUST CONTAIN EXACTLY ONE APPROVED ED-COAT CELL");
        return false;
    }

    const FLBPaintShopPlacedCellSaveState& Cell = State.Cells[0];
    if (Cell.bProcessPaused
        && (State.WIP.Num() != 1
            || Cell.State != ELBPaintShopExperimentalCellState::Processing
            || Cell.ProcessProgress01 >= DrainEndProgress01))
    {
        OutReason = TEXT("PAINT RUNTIME SAVE HAS AN INVALID PAUSED PROCESS");
        return false;
    }
    if (!Cell.bCommissioned || !Cell.QueuedWIPIds.IsEmpty())
    {
        OutReason = TEXT("PAINT RUNTIME SAVE HAS INVALID CELL COMMISSIONING OR QUEUE OWNERSHIP");
        return false;
    }
    if (State.WIP.IsEmpty())
    {
        if (!Cell.ActiveWIPId.IsNone() || Cell.ProcessProgress01 != 0.0f
            || Cell.bProcessPaused
            || (Cell.State != ELBPaintShopExperimentalCellState::Starved
                && Cell.State != ELBPaintShopExperimentalCellState::Faulted))
        {
            OutReason = TEXT("PAINT RUNTIME EMPTY SAVE MUST BE STARVED OR FAULTED AT ZERO PROGRESS");
            return false;
        }
        return true;
    }

    const FLBPaintShopWIPSaveState& Unit = State.WIP[0];
    if (Unit.Version != 2 || Unit.CurrentCellId != Cell.CellId
        || Cell.ActiveWIPId != Unit.UnitId)
    {
        OutReason = TEXT("PAINT RUNTIME SAVE HAS CONTRADICTORY EXACT WIP OWNERSHIP");
        return false;
    }
    const bool bAtOutput = Cell.ProcessProgress01 >= DrainEndProgress01;
    if ((Cell.State == ELBPaintShopExperimentalCellState::Blocked && !bAtOutput)
        || (bAtOutput && Cell.bOutputBlocked
            && Cell.State != ELBPaintShopExperimentalCellState::Blocked))
    {
        OutReason = TEXT("PAINT RUNTIME SAVE OUTPUT BLOCK FLAG AND CELL STATE DISAGREE");
        return false;
    }
    if ((!bAtOutput && (Unit.MaterialId != LBPaintShopWIPIds::BIWComplete
            || (Cell.State != ELBPaintShopExperimentalCellState::Processing
                && Cell.State != ELBPaintShopExperimentalCellState::Faulted)))
        || (bAtOutput && (Unit.MaterialId != LBPaintShopWIPIds::BIWEDCoated
            || (Cell.State != ELBPaintShopExperimentalCellState::Idle
                && Cell.State != ELBPaintShopExperimentalCellState::Blocked
                && Cell.State != ELBPaintShopExperimentalCellState::Faulted))))
    {
        OutReason = TEXT("PAINT RUNTIME SAVE MATERIAL, PROGRESS, AND CELL STATE DISAGREE");
        return false;
    }
    return true;
}

FLBPaintShopCellPresentationState ALBPaintShopPrototypeRuntime::MakePresentationState(
    const bool bHasWIP, const float InCycleProgress01, const bool bFaulted)
{
    FLBPaintShopCellPresentationState Result;
    Result.bCarrierVisible = bHasWIP;
    Result.CycleProgress01 = InCycleProgress01;
    Result.LiquidLevel01 = 1.0f;
    Result.bFaulted = bFaulted;
    return Result;
}
