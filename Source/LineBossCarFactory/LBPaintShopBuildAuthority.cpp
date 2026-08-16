#include "LBPaintShopBuildAuthority.h"

#include "Components/BoxComponent.h"
#include "Engine/World.h"
#include "LBPaintShopCellActor.h"

namespace LBPaintShopBuildAuthorityPrivate
{
    constexpr float PlacementTolerance = 0.01f;
    constexpr float TransformTolerance = 0.01f;
    const FVector FootprintHalfExtentCm(900.0f, 500.0f, 426.5f);
    const FVector ProtectedEnvelopeHalfExtentCm(950.0f, 650.0f, 475.0f);

    FBox GetExpectedLocalBounds(const FVector& HalfExtent)
    {
        return FBox(FVector(-HalfExtent.X, -HalfExtent.Y, 0.0f),
            FVector(HalfExtent.X, HalfExtent.Y, HalfExtent.Z * 2.0f));
    }

    bool IsGridValue(const double Value, const double GridCm)
    {
        return FMath::IsFinite(Value)
            && FMath::IsNearlyEqual(Value, FMath::GridSnap(Value, GridCm),
                PlacementTolerance);
    }
}

ALBPaintShopBuildAuthority::ALBPaintShopBuildAuthority()
{
    PrimaryActorTick.bCanEverTick = false;
    PrimaryActorTick.bStartWithTickEnabled = false;
    SetActorEnableCollision(false);
    Tags.AddUnique(TEXT("LB.PaintShop.Experimental.BuildAuthority.v001"));
}

FLBPaintShopApprovedEDCoatLayoutItem
ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout()
{
    FLBPaintShopApprovedEDCoatLayoutItem Result;
    Result.CellId = TEXT("PAINT_EDCOAT_CELL_001");
    Result.DefinitionId = LBPaintShopCellIds::EDCoatDipCell;
    Result.WorldTransform = FTransform::Identity;
    return Result;
}

bool ALBPaintShopBuildAuthority::GetLocalBounds(
    const UBoxComponent* Component, FBox& OutBounds)
{
    OutBounds = FBox(ForceInit);
    if (!Component)
    {
        return false;
    }

    const FVector Extent = Component->GetUnscaledBoxExtent();
    const FTransform RelativeTransform = Component->GetRelativeTransform();
    if (Extent.ContainsNaN() || Extent.GetMin() <= UE_SMALL_NUMBER
        || !RelativeTransform.IsValid()
        || !RelativeTransform.GetScale3D().Equals(FVector::OneVector,
            LBPaintShopBuildAuthorityPrivate::PlacementTolerance))
    {
        return false;
    }

    OutBounds = FBox(-Extent, Extent).TransformBy(RelativeTransform);
    return !OutBounds.Min.ContainsNaN() && !OutBounds.Max.ContainsNaN()
        && OutBounds.GetSize().GetMin() > UE_SMALL_NUMBER;
}

bool ALBPaintShopBuildAuthority::ValidateCellBounds(const ALBPaintShopCellActor* Cell,
    const FTransform& WorldTransform, FString& OutReason)
{
    FBox LocalFootprint;
    FBox LocalEnvelope;
    if (!Cell || !GetLocalBounds(Cell->GetFootprint(), LocalFootprint)
        || !GetLocalBounds(Cell->GetProtectedEnvelope(), LocalEnvelope))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT CELL HAS INVALID AUTHORED BOUNDS");
        return false;
    }

    const FBox ExpectedFootprint =
        LBPaintShopBuildAuthorityPrivate::GetExpectedLocalBounds(
            LBPaintShopBuildAuthorityPrivate::FootprintHalfExtentCm);
    const FBox ExpectedEnvelope =
        LBPaintShopBuildAuthorityPrivate::GetExpectedLocalBounds(
            LBPaintShopBuildAuthorityPrivate::ProtectedEnvelopeHalfExtentCm);
    if (!LocalFootprint.Min.Equals(ExpectedFootprint.Min,
            LBPaintShopBuildAuthorityPrivate::PlacementTolerance)
        || !LocalFootprint.Max.Equals(ExpectedFootprint.Max,
            LBPaintShopBuildAuthorityPrivate::PlacementTolerance)
        || !LocalEnvelope.Min.Equals(ExpectedEnvelope.Min,
            LBPaintShopBuildAuthorityPrivate::PlacementTolerance)
        || !LocalEnvelope.Max.Equals(ExpectedEnvelope.Max,
            LBPaintShopBuildAuthorityPrivate::PlacementTolerance))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT CELL BOUNDS DO NOT MATCH THE APPROVED 1800 CM BAY");
        return false;
    }

    const FBox CandidateFootprint = LocalFootprint.TransformBy(WorldTransform);
    const FBox ApprovedEnvelope = ExpectedEnvelope.TransformBy(
        GetApprovedEDCoatDipLayout().WorldTransform).ExpandBy(
            LBPaintShopBuildAuthorityPrivate::PlacementTolerance);
    if (!ApprovedEnvelope.IsInsideOrOn(CandidateFootprint.Min)
        || !ApprovedEnvelope.IsInsideOrOn(CandidateFootprint.Max))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT CELL FOOTPRINT EXCEEDS ITS APPROVED BAY");
        return false;
    }
    return true;
}

bool ALBPaintShopBuildAuthority::ValidateApprovedCellPlacement(const FName DefinitionId,
    const FTransform& WorldTransform, FString& OutReason) const
{
    OutReason.Reset();
    FLBPaintShopCellDefinition Definition;
    if (DefinitionId != LBPaintShopCellIds::EDCoatDipCell
        || !FLBPaintShopDefinitionRegistry::FindCanonicalDefinition(DefinitionId, Definition)
        || Definition.CellType != ELBPaintShopCellType::EDCoatDip
        || !FLBPaintShopDefinitionRegistry::ValidateDefinition(Definition, OutReason))
    {
        if (OutReason.IsEmpty())
        {
            OutReason = TEXT("PAINT SHOP BUILD AUTHORITY ACCEPTS ONLY THE CANONICAL ED-COAT DIP CELL");
        }
        return false;
    }

    const FVector Location = WorldTransform.GetLocation();
    const FVector Scale = WorldTransform.GetScale3D();
    const FRotator Rotation = WorldTransform.Rotator();
    if (!WorldTransform.IsValid() || WorldTransform.ContainsNaN()
        || !Scale.Equals(FVector::OneVector,
            LBPaintShopBuildAuthorityPrivate::PlacementTolerance))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT PLACEMENT REQUIRES A FINITE UNSCALED TRANSFORM");
        return false;
    }
    if (!LBPaintShopBuildAuthorityPrivate::IsGridValue(Location.X, GetPlacementGridCm())
        || !LBPaintShopBuildAuthorityPrivate::IsGridValue(Location.Y, GetPlacementGridCm())
        || !FMath::IsNearlyZero(Location.Z,
            LBPaintShopBuildAuthorityPrivate::PlacementTolerance)
        || !FMath::IsNearlyZero(Rotation.Pitch,
            LBPaintShopBuildAuthorityPrivate::PlacementTolerance)
        || !FMath::IsNearlyZero(Rotation.Roll,
            LBPaintShopBuildAuthorityPrivate::PlacementTolerance))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT PLACEMENT REQUIRES 100 CM GRID SNAP AND FLOOR DATUM");
        return false;
    }

    const FLBPaintShopApprovedEDCoatLayoutItem Approved = GetApprovedEDCoatDipLayout();
    const FBox CandidateFootprint =
        LBPaintShopBuildAuthorityPrivate::GetExpectedLocalBounds(
            LBPaintShopBuildAuthorityPrivate::FootprintHalfExtentCm).TransformBy(WorldTransform);
    const FBox ApprovedEnvelope =
        LBPaintShopBuildAuthorityPrivate::GetExpectedLocalBounds(
            LBPaintShopBuildAuthorityPrivate::ProtectedEnvelopeHalfExtentCm).TransformBy(
                Approved.WorldTransform).ExpandBy(
                    LBPaintShopBuildAuthorityPrivate::PlacementTolerance);
    if (!ApprovedEnvelope.IsInsideOrOn(CandidateFootprint.Min)
        || !ApprovedEnvelope.IsInsideOrOn(CandidateFootprint.Max))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT CELL FOOTPRINT EXCEEDS ITS APPROVED BAY");
        return false;
    }
    if (!WorldTransform.Equals(Approved.WorldTransform,
        LBPaintShopBuildAuthorityPrivate::TransformTolerance))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT PLACEMENT IS OUTSIDE THE ONE APPROVED BAY");
        return false;
    }
    return true;
}

void ALBPaintShopBuildAuthority::ValidateApprovedCellPlacementForValidation(
    const FName DefinitionId, const FTransform& WorldTransform, bool& bOutValid,
    FString& OutReason) const
{
    bOutValid = ValidateApprovedCellPlacement(DefinitionId, WorldTransform, OutReason);
}

ALBPaintShopCellActor* ALBPaintShopBuildAuthority::FindCell(const FName CellId) const
{
    return IsValid(OwnedCell) && OwnedCell->IsConfigured()
        && OwnedCell->GetCellId() == CellId ? OwnedCell.Get() : nullptr;
}

bool ALBPaintShopBuildAuthority::ValidateTopologyState(
    const FLBPaintShopExperimentalSaveState& State, FString& OutReason) const
{
    OutReason.Reset();
    if (!State.WIP.IsEmpty())
    {
        OutReason = TEXT("PAINT SHOP TOPOLOGY RESTORE REQUIRES WIP AND LINEAGE TO REMAIN WITH THE RUNTIME");
        return false;
    }
    if (!State.Connections.IsEmpty())
    {
        OutReason = TEXT("THE FIRST PAINT SHOP ED-COAT SLICE HAS NO GENERIC CONNECTION GRAPH");
        return false;
    }
    if (State.Cells.Num() != 1)
    {
        OutReason = TEXT("THE FIRST PAINT SHOP SLICE REQUIRES EXACTLY ONE ED-COAT CELL");
        return false;
    }

    const FLBPaintShopPlacedCellSaveState& CellState = State.Cells[0];
    const FLBPaintShopApprovedEDCoatLayoutItem Approved = GetApprovedEDCoatDipLayout();
    const uint8 CellStateValue = static_cast<uint8>(CellState.State);
    if (CellState.CellId != Approved.CellId
        || CellState.DefinitionId != Approved.DefinitionId
        || !CellState.QueuedWIPIds.IsEmpty() || !CellState.ActiveWIPId.IsNone()
        || CellStateValue > static_cast<uint8>(ELBPaintShopExperimentalCellState::Faulted)
        || (CellState.State == ELBPaintShopExperimentalCellState::Processing
            && !CellState.bCommissioned))
    {
        OutReason = TEXT("PAINT SHOP TOPOLOGY DOES NOT MATCH THE APPROVED EMPTY ED-COAT CELL");
        return false;
    }

    // A runtime intentionally strips WIP ownership from its topology copy. Preserve the
    // exact runtime state in State, but normalize only this private validation probe so a
    // legitimate Processing record is not rejected merely because ActiveWIPId was stripped.
    FLBPaintShopExperimentalSaveState ValidationProbe = State;
    ValidationProbe.Cells[0].State = ELBPaintShopExperimentalCellState::Idle;
    if (!ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
        ValidationProbe, OutReason))
    {
        return false;
    }
    return ValidateApprovedCellPlacement(CellState.DefinitionId,
        CellState.WorldTransform, OutReason);
}

bool ALBPaintShopBuildAuthority::BuildApprovedEDCoatDipLayout(FString& OutReason)
{
    OutReason.Reset();
    if (IsValid(OwnedCell))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT LAYOUT IS ALREADY BUILT");
        return false;
    }

    const FLBPaintShopApprovedEDCoatLayoutItem Approved = GetApprovedEDCoatDipLayout();
    FLBPaintShopExperimentalSaveState InitialState;
    FLBPaintShopPlacedCellSaveState& CellState = InitialState.Cells.AddDefaulted_GetRef();
    CellState.CellId = Approved.CellId;
    CellState.DefinitionId = Approved.DefinitionId;
    CellState.WorldTransform = Approved.WorldTransform;
    CellState.State = ELBPaintShopExperimentalCellState::Planned;
    CellState.bCommissioned = false;
    CellState.ProcessProgress01 = 0.0f;
    InitialState.NextCellSerial = 2;
    return RestoreTopologySaveState(InitialState, OutReason);
}

bool ALBPaintShopBuildAuthority::CaptureTopologySaveState(
    FLBPaintShopExperimentalSaveState& OutState, FString& OutReason) const
{
    OutState = FLBPaintShopExperimentalSaveState();
    OutReason.Reset();
    if (!IsValid(OwnedCell) || !OwnedCell->IsConfigured()
        || TopologyState.Cells.Num() != 1)
    {
        OutReason = TEXT("PAINT SHOP ED-COAT TOPOLOGY IS NOT BUILT");
        return false;
    }
    if (!ValidateTopologyState(TopologyState, OutReason))
    {
        return false;
    }

    const FLBPaintShopPlacedCellSaveState& CellState = TopologyState.Cells[0];
    if (OwnedCell->GetCellId() != CellState.CellId
        || OwnedCell->GetDefinitionId() != CellState.DefinitionId
        || !OwnedCell->GetActorTransform().Equals(CellState.WorldTransform,
            LBPaintShopBuildAuthorityPrivate::TransformTolerance)
        || !ValidateCellBounds(OwnedCell, CellState.WorldTransform, OutReason))
    {
        if (OutReason.IsEmpty())
        {
            OutReason = TEXT("PAINT SHOP ED-COAT ACTOR NO LONGER MATCHES ITS TOPOLOGY RECORD");
        }
        return false;
    }

    OutState = TopologyState;
    return true;
}

bool ALBPaintShopBuildAuthority::RestoreTopologySaveState(
    const FLBPaintShopExperimentalSaveState& State, FString& OutReason)
{
    OutReason.Reset();
    if (!ValidateTopologyState(State, OutReason))
    {
        return false;
    }
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("PAINT SHOP BUILD AUTHORITY WORLD IS OFFLINE");
        return false;
    }

    const FLBPaintShopPlacedCellSaveState& CellState = State.Cells[0];
    FActorSpawnParameters SpawnParams;
    SpawnParams.Owner = this;
    SpawnParams.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ALBPaintShopCellActor* Candidate = World->SpawnActor<ALBPaintShopCellActor>(
        ALBPaintShopCellActor::StaticClass(), CellState.WorldTransform, SpawnParams);
    FString StageReason;
    if (!Candidate
        || !Candidate->ConfigureCell(CellState.CellId, CellState.DefinitionId, StageReason)
        || !Candidate->IsConfigured()
        || Candidate->GetCellId() != CellState.CellId
        || Candidate->GetDefinitionId() != CellState.DefinitionId
        || !Candidate->GetActorTransform().Equals(CellState.WorldTransform,
            LBPaintShopBuildAuthorityPrivate::TransformTolerance)
        || !ValidateCellBounds(Candidate, CellState.WorldTransform, StageReason))
    {
        if (Candidate)
        {
            Candidate->Destroy();
        }
        OutReason = StageReason.IsEmpty()
            ? TEXT("PAINT SHOP ED-COAT TOPOLOGY STAGING FAILED") : StageReason;
        return false;
    }

    ALBPaintShopCellActor* Previous = OwnedCell.Get();
    OwnedCell = Candidate;
    TopologyState = State;
    if (IsValid(Previous))
    {
        Previous->Destroy();
    }
    return true;
}
