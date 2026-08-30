#include "LBPaintShopExperimentalSaveGame.h"

#include "LBVehiclePanelCatalog.h"

namespace LBPaintShopExperimentalSavePrivate
{
    constexpr int32 ExactCairnwellPanelFamilyCount = 11;

    bool IsFiniteTransform(const FTransform& Transform)
    {
        const FVector Location = Transform.GetLocation();
        const FVector Scale = Transform.GetScale3D();
        const FQuat Rotation = Transform.GetRotation();
        return !Location.ContainsNaN() && !Scale.ContainsNaN() && !Rotation.ContainsNaN()
            && Rotation.IsNormalized() && Scale.GetAbsMin() > KINDA_SMALL_NUMBER;
    }

    bool IsKnownCellState(const ELBPaintShopExperimentalCellState CellState)
    {
        const uint8 Value = static_cast<uint8>(CellState);
        return Value <= static_cast<uint8>(ELBPaintShopExperimentalCellState::Faulted);
    }

    bool IsKnownWIPId(const FName WIPId)
    {
        return WIPId == LBPaintShopWIPIds::BIWComplete
            || WIPId == LBPaintShopWIPIds::BIWEDCoated
            || WIPId == LBPaintShopWIPIds::BIWCuredEDCoat;
    }

    bool IsCompletelyDefaultLineage(const FLBBodyInWhiteRecord& Body)
    {
        const FLBBodyWeldQualityEvidence& Quality = Body.QualityEvidence;
        const FLBBodyWeldCycleEvidence& Cycle = Body.CycleEvidence;
        return Body.BodyId.IsNone() && Body.VehicleModelId.IsNone()
            && Body.OrderId.IsNone() && Body.BaseKitId.IsNone()
            && Body.ReservationId.IsNone() && Body.WeldLineId.IsNone()
            && Body.Panels.IsEmpty()
            && Body.QualityState == ELBBodyWeldQualityState::Pending
            && !Quality.bRecipeComplete && !Quality.bFixtureProgramCorrect
            && !Quality.bSpotOperationsComplete && !Quality.bMIGOperationsComplete
            && !Quality.bRobotCalibrationInTolerance
            && !Quality.bServiceConditionAcceptable && !Quality.bSafetyInterlockClear
            && Quality.ReasonCodes.IsEmpty()
            && Cycle.ClosurePreparationSeconds == 0.0f
            && Cycle.FramingSeconds == 0.0f && Cycle.WeldingSeconds == 0.0f
            && Cycle.GeometryCheckSeconds == 0.0f && Cycle.CompletionSequence == 0
            && !Body.bEDAccepted;
    }

    bool IsExactAcknowledgedGoodWeldLineage(const FLBBodyInWhiteRecord& Body)
    {
        const TArray<FName> RequiredFamilies =
            ALBBodyWeldLineActor::GetRequiredPanelFamilies();
        const FLBBodyWeldQualityEvidence& Quality = Body.QualityEvidence;
        const FLBBodyWeldCycleEvidence& Cycle = Body.CycleEvidence;
        if (RequiredFamilies.Num() != ExactCairnwellPanelFamilyCount
            || Body.BodyId.IsNone()
            || Body.VehicleModelId != ALBBodyWeldLineActor::GetVehicleModelId()
            || Body.OrderId.IsNone() || Body.BaseKitId.IsNone()
            || Body.ReservationId.IsNone() || Body.WeldLineId.IsNone()
            || Body.Panels.Num() != ExactCairnwellPanelFamilyCount
            || Body.QualityState != ELBBodyWeldQualityState::Good || !Body.bEDAccepted
            || !Quality.bRecipeComplete || !Quality.bFixtureProgramCorrect
            || !Quality.bSpotOperationsComplete || !Quality.bMIGOperationsComplete
            || !Quality.bRobotCalibrationInTolerance
            || !Quality.bServiceConditionAcceptable || !Quality.bSafetyInterlockClear
            || !Quality.ReasonCodes.IsEmpty()
            || !FMath::IsFinite(Cycle.ClosurePreparationSeconds)
            || Cycle.ClosurePreparationSeconds < 0.0f
            || !FMath::IsFinite(Cycle.FramingSeconds) || Cycle.FramingSeconds < 0.0f
            || !FMath::IsFinite(Cycle.WeldingSeconds) || Cycle.WeldingSeconds < 0.0f
            || !FMath::IsFinite(Cycle.GeometryCheckSeconds)
            || Cycle.GeometryCheckSeconds < 0.0f || Cycle.CompletionSequence <= 0)
        {
            return false;
        }

        TSet<FName> PanelIds;
        TSet<FName> PanelFamilies;
        for (const FLBBodyWeldPanelLineage& Panel : Body.Panels)
        {
            FName ParsedVehicle;
            FName ParsedFamily;
            if (Panel.PanelId.IsNone() || Panel.PanelTypeId.IsNone()
                || Panel.StillageId.IsNone() || PanelIds.Contains(Panel.PanelId)
                || PanelFamilies.Contains(Panel.PanelTypeId)
                || !LBCairnwell2040PanelCatalog::ParsePressedPanelUnitId(
                    Panel.PanelId, ParsedVehicle, ParsedFamily)
                || ParsedVehicle != Body.VehicleModelId || ParsedFamily != Panel.PanelTypeId
                || !RequiredFamilies.Contains(Panel.PanelTypeId))
            {
                return false;
            }
            PanelIds.Add(Panel.PanelId);
            PanelFamilies.Add(Panel.PanelTypeId);
        }
        return PanelFamilies.Num() == RequiredFamilies.Num();
    }

    FString MakeWeldCompletionKey(const FLBBodyInWhiteRecord& Body)
    {
        return FString::Printf(TEXT("%s/%lld"),
            *Body.WeldLineId.ToString().ToUpper(), Body.CycleEvidence.CompletionSequence);
    }

    const FLBPaintShopPortDefinition* FindPort(const FLBPaintShopCellDefinition& Definition,
        const FName PortId)
    {
        return Definition.Ports.FindByPredicate([PortId](const FLBPaintShopPortDefinition& Port)
        {
            return Port.PortId == PortId;
        });
    }
}

FName ULBPaintShopExperimentalSaveGame::GetSlotName()
{
    return TEXT("LineBossPaintShopExperimental_v001");
}

bool ULBPaintShopExperimentalSaveGame::ValidateExperimentalSaveState(
    const FLBPaintShopExperimentalSaveState& InState, FString& OutReason)
{
    OutReason.Reset();
    if (InState.Version != 1 || InState.NextCellSerial < 1
        || InState.NextConnectionSerial < 1 || InState.NextWIPSerial < 1
        || InState.NextGenealogySequence < 1)
    {
        OutReason = TEXT("PAINT SHOP EXPERIMENTAL SAVE HEADER IS INVALID");
        return false;
    }

    const TArray<FName> CanonicalDefinitionIds =
        FLBPaintShopDefinitionRegistry::GetCanonicalDefinitionIds();
    TSet<FName> CellIds;
    TSet<FName> DefinitionIds;
    TMap<FName, FLBPaintShopCellDefinition> DefinitionsByCell;
    TMap<FName, int32> CanonicalOrderByCell;
    for (const FLBPaintShopPlacedCellSaveState& Cell : InState.Cells)
    {
        FLBPaintShopCellDefinition Definition;
        const int32 CanonicalOrder = CanonicalDefinitionIds.IndexOfByKey(Cell.DefinitionId);
        if (Cell.Version != 1 || Cell.CellId.IsNone() || CellIds.Contains(Cell.CellId)
            || DefinitionIds.Contains(Cell.DefinitionId)
            || !LBPaintShopExperimentalSavePrivate::IsFiniteTransform(Cell.WorldTransform)
            || !LBPaintShopExperimentalSavePrivate::IsKnownCellState(Cell.State)
            || !FMath::IsFinite(Cell.ProcessProgress01)
            || !FMath::IsWithinInclusive(Cell.ProcessProgress01, 0.0f, 1.0f)
            || !FLBPaintShopDefinitionRegistry::FindCanonicalDefinition(Cell.DefinitionId, Definition)
            || CanonicalOrder == INDEX_NONE)
        {
            OutReason = TEXT("PAINT SHOP EXPERIMENTAL SAVE HAS INVALID CELLS");
            return false;
        }
        if (Cell.State == ELBPaintShopExperimentalCellState::Processing
            && (!Cell.bCommissioned || Cell.ActiveWIPId.IsNone()))
        {
            OutReason = TEXT("PAINT SHOP EXPERIMENTAL PROCESSING CELL IS NOT COMMISSIONED OR HAS NO ACTIVE WIP");
            return false;
        }
        if (Cell.bProcessPaused
            && (!Cell.bCommissioned || Cell.ActiveWIPId.IsNone()
                || Cell.State != ELBPaintShopExperimentalCellState::Processing
                || Cell.ProcessProgress01 >= 1.0f))
        {
            OutReason = TEXT("PAINT SHOP EXPERIMENTAL PAUSE STATE HAS NO IN-FLIGHT PROCESS");
            return false;
        }

        CellIds.Add(Cell.CellId);
        DefinitionIds.Add(Cell.DefinitionId);
        DefinitionsByCell.Add(Cell.CellId, Definition);
        CanonicalOrderByCell.Add(Cell.CellId, CanonicalOrder);
    }

    TSet<FName> ConnectionIds;
    TSet<FString> UsedEndpoints;
    for (const FLBPaintShopConnectionSaveState& Connection : InState.Connections)
    {
        const FLBPaintShopCellDefinition* SourceDefinition =
            DefinitionsByCell.Find(Connection.SourceCellId);
        const FLBPaintShopCellDefinition* TargetDefinition =
            DefinitionsByCell.Find(Connection.TargetCellId);
        const FLBPaintShopPortDefinition* SourcePort = SourceDefinition
            ? LBPaintShopExperimentalSavePrivate::FindPort(*SourceDefinition, Connection.SourcePortId)
            : nullptr;
        const FLBPaintShopPortDefinition* TargetPort = TargetDefinition
            ? LBPaintShopExperimentalSavePrivate::FindPort(*TargetDefinition, Connection.TargetPortId)
            : nullptr;
        const FString SourceEndpoint = Connection.SourceCellId.ToString() + TEXT("/")
            + Connection.SourcePortId.ToString();
        const FString TargetEndpoint = Connection.TargetCellId.ToString() + TEXT("/")
            + Connection.TargetPortId.ToString();
        const int32* SourceOrder = CanonicalOrderByCell.Find(Connection.SourceCellId);
        const int32* TargetOrder = CanonicalOrderByCell.Find(Connection.TargetCellId);
        if (Connection.Version != 1 || Connection.ConnectionId.IsNone()
            || ConnectionIds.Contains(Connection.ConnectionId)
            || Connection.SourceCellId == Connection.TargetCellId || !SourcePort || !TargetPort
            || SourcePort->Direction != ELBPaintShopPortDirection::Output
            || TargetPort->Direction != ELBPaintShopPortDirection::Input
            || SourcePort->WIPId != TargetPort->WIPId || !SourceOrder || !TargetOrder
            || *TargetOrder != *SourceOrder + 1 || UsedEndpoints.Contains(SourceEndpoint)
            || UsedEndpoints.Contains(TargetEndpoint))
        {
            OutReason = TEXT("PAINT SHOP EXPERIMENTAL SAVE HAS INVALID TOPOLOGY");
            return false;
        }
        ConnectionIds.Add(Connection.ConnectionId);
        UsedEndpoints.Add(SourceEndpoint);
        UsedEndpoints.Add(TargetEndpoint);
    }

    TSet<FName> WIPIds;
    TSet<FName> CarrierIds;
    TSet<int64> GenealogySequences;
    TSet<FName> SourceBodyIds;
    TSet<FName> SourceBaseKitIds;
    TSet<FName> SourceReservationIds;
    TSet<FName> SourcePanelIds;
    TSet<FString> SourceWeldCompletionKeys;
    for (const FLBPaintShopWIPSaveState& Unit : InState.WIP)
    {
        const FLBPaintShopCellDefinition* CurrentDefinition =
            DefinitionsByCell.Find(Unit.CurrentCellId);
        if ((Unit.Version != 1 && Unit.Version != 2)
            || Unit.UnitId.IsNone() || WIPIds.Contains(Unit.UnitId)
            || !LBPaintShopExperimentalSavePrivate::IsKnownWIPId(Unit.MaterialId)
            || !CurrentDefinition || Unit.CarrierId.IsNone() || CarrierIds.Contains(Unit.CarrierId)
            || Unit.GenealogySequence < 1 || GenealogySequences.Contains(Unit.GenealogySequence)
            || (Unit.MaterialId != CurrentDefinition->InputWIPId
                && Unit.MaterialId != CurrentDefinition->OutputWIPId))
        {
            OutReason = TEXT("PAINT SHOP EXPERIMENTAL SAVE HAS INVALID OR DUPLICATE WIP");
            return false;
        }
        if (Unit.Version == 1)
        {
            if (!LBPaintShopExperimentalSavePrivate::IsCompletelyDefaultLineage(
                Unit.SourceBodyInWhite))
            {
                OutReason = TEXT("PAINT SHOP EXPERIMENTAL VERSION 1 WIP HAS NON-DEFAULT WELD LINEAGE");
                return false;
            }
        }
        else
        {
            const FLBBodyInWhiteRecord& Body = Unit.SourceBodyInWhite;
            const FString WeldCompletionKey =
                LBPaintShopExperimentalSavePrivate::MakeWeldCompletionKey(Body);
            if (Unit.GenealogySequence >= InState.NextGenealogySequence
                || !LBPaintShopExperimentalSavePrivate::IsExactAcknowledgedGoodWeldLineage(Body)
                || SourceBodyIds.Contains(Body.BodyId)
                || SourceBaseKitIds.Contains(Body.BaseKitId)
                || SourceReservationIds.Contains(Body.ReservationId)
                || SourceWeldCompletionKeys.Contains(WeldCompletionKey))
            {
                OutReason = TEXT("PAINT SHOP EXPERIMENTAL VERSION 2 WIP HAS INVALID OR DUPLICATE WELD LINEAGE");
                return false;
            }
            for (const FLBBodyWeldPanelLineage& Panel : Body.Panels)
            {
                if (SourcePanelIds.Contains(Panel.PanelId))
                {
                    OutReason = TEXT("PAINT SHOP EXPERIMENTAL VERSION 2 WIP REUSES A SOURCE PANEL ID");
                    return false;
                }
            }
            SourceBodyIds.Add(Body.BodyId);
            SourceBaseKitIds.Add(Body.BaseKitId);
            SourceReservationIds.Add(Body.ReservationId);
            SourceWeldCompletionKeys.Add(WeldCompletionKey);
            for (const FLBBodyWeldPanelLineage& Panel : Body.Panels)
            {
                SourcePanelIds.Add(Panel.PanelId);
            }
        }
        WIPIds.Add(Unit.UnitId);
        CarrierIds.Add(Unit.CarrierId);
        GenealogySequences.Add(Unit.GenealogySequence);
    }

    TSet<FName> OwnedWIPIds;
    for (const FLBPaintShopPlacedCellSaveState& Cell : InState.Cells)
    {
        TArray<FName> References = Cell.QueuedWIPIds;
        if (!Cell.ActiveWIPId.IsNone())
        {
            References.Add(Cell.ActiveWIPId);
        }
        for (const FName WIPId : References)
        {
            if (WIPId.IsNone() || !WIPIds.Contains(WIPId) || OwnedWIPIds.Contains(WIPId))
            {
                OutReason = TEXT("PAINT SHOP EXPERIMENTAL SAVE HAS INVALID WIP OWNERSHIP");
                return false;
            }
            const FLBPaintShopWIPSaveState* Unit = InState.WIP.FindByPredicate(
                [WIPId](const FLBPaintShopWIPSaveState& Candidate)
                {
                    return Candidate.UnitId == WIPId;
                });
            if (!Unit || Unit->CurrentCellId != Cell.CellId)
            {
                OutReason = TEXT("PAINT SHOP EXPERIMENTAL SAVE HAS CONTRADICTORY WIP OWNERSHIP");
                return false;
            }
            OwnedWIPIds.Add(WIPId);
        }
    }
    if (OwnedWIPIds.Num() != WIPIds.Num())
    {
        OutReason = TEXT("PAINT SHOP EXPERIMENTAL SAVE HAS UNOWNED WIP");
        return false;
    }
    return true;
}

bool ULBPaintShopExperimentalSaveGame::ValidateForLoad(FString& OutReason) const
{
    OutReason.Reset();
    if (SaveSchemaVersion != SchemaVersion)
    {
        OutReason = TEXT("PAINT SHOP EXPERIMENTAL SAVE SCHEMA IS NOT VERSION 1");
        return false;
    }
    if (PrototypeMapId != TEXT("LB_PaintShop_Prototype_v001"))
    {
        OutReason = TEXT("PAINT SHOP EXPERIMENTAL SAVE TARGETS A DIFFERENT PROTOTYPE MAP");
        return false;
    }
    return ValidateExperimentalSaveState(State, OutReason);
}
