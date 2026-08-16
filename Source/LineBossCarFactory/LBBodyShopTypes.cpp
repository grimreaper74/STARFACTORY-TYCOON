#include "LBBodyShopTypes.h"

const FName LBBodyShopMaterialIds::Underbody(TEXT("BIW_UNDERBODY"));
const FName LBBodyShopMaterialIds::SideLeft(TEXT("BIW_SIDE_LEFT"));
const FName LBBodyShopMaterialIds::SideRight(TEXT("BIW_SIDE_RIGHT"));
const FName LBBodyShopMaterialIds::UpperStructure(TEXT("BIW_UPPER_STRUCTURE"));
const FName LBBodyShopMaterialIds::RoofOuter(TEXT("BIW_ROOF_OUTER"));
const FName LBBodyShopMaterialIds::FramedBody(TEXT("BIW_FRAMED_BODY"));
const FName LBBodyShopMaterialIds::CompleteBody(TEXT("BIW_COMPLETE"));
const FName LBBodyShopMaterialIds::PressedPanelStillage(TEXT("PRESSED_PANEL_STILLAGE"));
const FName LBBodyShopMaterialIds::EmptyPanelStillage(TEXT("EMPTY_PANEL_STILLAGE"));

const FName LBBodyShopPrototypeIds::FullStillageDock(TEXT("BW001_FULL_STILLAGE_DOCK_BASIC"));
const FName LBBodyShopPrototypeIds::PanelPresentation(TEXT("BW002_PANEL_PRESENTATION_BASIC"));
const FName LBBodyShopPrototypeIds::UnderbodyFixture(TEXT("BW003_UNDERBODY_FIXTURE_BASIC"));
const FName LBBodyShopPrototypeIds::StraightSkidConveyor(TEXT("BW003_STRAIGHT_SKID_CONVEYOR_BASIC"));
const FName LBBodyShopPrototypeIds::BasicVisionGate(TEXT("BW012_VISION_GATE_BASIC"));
const FName LBBodyShopPrototypeIds::OutputBuffer(TEXT("BW014_OUTPUT_BUFFER_BASIC"));

const FName LBBodyShopPrototypeIds::StillageIn(TEXT("STILLAGE_IN"));
const FName LBBodyShopPrototypeIds::StillageOut(TEXT("STILLAGE_OUT"));
const FName LBBodyShopPrototypeIds::PanelOut(TEXT("PANEL_OUT"));
const FName LBBodyShopPrototypeIds::PanelIn(TEXT("PANEL_IN"));
const FName LBBodyShopPrototypeIds::SkidIn(TEXT("SKID_IN"));
const FName LBBodyShopPrototypeIds::SkidOut(TEXT("SKID_OUT"));
const FName LBBodyShopPrototypeIds::BodyIn(TEXT("BODY_IN"));
const FName LBBodyShopPrototypeIds::BodyOut(TEXT("BODY_OUT"));

namespace LBBodyShopTypesPrivate
{
    FLBBodyShopPortDefinition Port(const FName Id, const ELBBodyShopPortDirection Direction,
        const ELBBodyShopTransportType Transport, const FName Material,
        const FVector& Location, const FRotator& Rotation = FRotator::ZeroRotator,
        const int32 Capacity = 1)
    {
        FLBBodyShopPortDefinition Result;
        Result.PortId = Id;
        Result.Direction = Direction;
        Result.Transport = Transport;
        Result.MaterialId = Material;
        Result.LocalTransform = FTransform(Rotation, Location);
        Result.Capacity = Capacity;
        return Result;
    }

    FLBBodyShopRobotSlotDefinition Slot(const TCHAR* Id, const FVector& Location,
        const FRotator& Rotation, const ELBBodyShopRobotRole Role,
        const ELBBodyShopToolType Tool, const float ReachCm, const float SweepCm)
    {
        FLBBodyShopRobotSlotDefinition Result;
        Result.SlotId = FName(Id);
        Result.LocalMountTransform = FTransform(Rotation, Location);
        Result.AllowedRoles = {Role};
        Result.AllowedTools = {Tool};
        Result.ReachRadiusCm = ReachCm;
        Result.SweepRadiusCm = SweepCm;
        return Result;
    }

    FLBBodyShopCellDefinition Base(const FName Id, const ELBBodyShopCellType Type,
        const TCHAR* Name, const FVector& Footprint, const FVector& Maintenance,
        const float Cycle, const int32 Capacity)
    {
        FLBBodyShopCellDefinition Result;
        Result.DefinitionId = Id;
        Result.CellType = Type;
        Result.DisplayName = FText::FromString(Name);
        Result.FootprintCm = Footprint;
        Result.MaintenanceEnvelopeCm = Maintenance;
        Result.CycleSeconds = Cycle;
        Result.WIPCapacity = Capacity;
        return Result;
    }

    TArray<FLBBodyShopCellDefinition> BuildCanonicalDefinitions()
    {
        TArray<FLBBodyShopCellDefinition> Result;

        FLBBodyShopCellDefinition Dock = Base(LBBodyShopPrototypeIds::FullStillageDock,
            ELBBodyShopCellType::FullStillageDock, TEXT("Full stillage dock"),
            FVector(400.0f, 400.0f, 220.0f), FVector(600.0f, 600.0f, 260.0f), 2.0f, 2);
        Dock.Ports.Add(Port(LBBodyShopPrototypeIds::StillageIn, ELBBodyShopPortDirection::Input,
            ELBBodyShopTransportType::StillageFLT, LBBodyShopMaterialIds::PressedPanelStillage,
            FVector(-400.0f, 0.0f, 0.0f), FRotator(0.0f, 180.0f, 0.0f), 2));
        Dock.Ports.Add(Port(LBBodyShopPrototypeIds::StillageOut, ELBBodyShopPortDirection::Output,
            ELBBodyShopTransportType::RobotHandoff, LBBodyShopMaterialIds::PressedPanelStillage,
            FVector(400.0f, 0.0f, 0.0f), FRotator::ZeroRotator, 2));
        Result.Add(Dock);

        FLBBodyShopCellDefinition Presentation = Base(LBBodyShopPrototypeIds::PanelPresentation,
            ELBBodyShopCellType::PanelPresentation, TEXT("Panel presentation / destacking"),
            FVector(800.0f, 700.0f, 340.0f), FVector(1000.0f, 900.0f, 400.0f), 5.0f, 1);
        Presentation.Ports.Add(Port(LBBodyShopPrototypeIds::StillageIn,
            ELBBodyShopPortDirection::Input, ELBBodyShopTransportType::RobotHandoff,
            LBBodyShopMaterialIds::PressedPanelStillage, FVector(-600.0f, 0.0f, 0.0f),
            FRotator(0.0f, 180.0f, 0.0f)));
        Presentation.Ports.Add(Port(LBBodyShopPrototypeIds::PanelOut,
            ELBBodyShopPortDirection::Output, ELBBodyShopTransportType::RobotHandoff,
            LBBodyShopMaterialIds::Underbody, FVector(600.0f, 0.0f, 80.0f)));
        Presentation.RobotSlots.Add(Slot(TEXT("ROBOT_HND_01"), FVector(0.0f, -180.0f, 0.0f),
            FRotator(0.0f, 35.0f, 0.0f), ELBBodyShopRobotRole::PanelHandling,
            ELBBodyShopToolType::VacuumEightCup, 360.0f, 250.0f));
        Result.Add(Presentation);

        FLBBodyShopCellDefinition Underbody = Base(LBBodyShopPrototypeIds::UnderbodyFixture,
            ELBBodyShopCellType::UnderbodyFixture, TEXT("Underbody fixture cell"),
            FVector(1000.0f, 800.0f, 420.0f), FVector(1200.0f, 1000.0f, 480.0f), 8.0f, 1);
        Underbody.Ports.Add(Port(LBBodyShopPrototypeIds::PanelIn,
            ELBBodyShopPortDirection::Input, ELBBodyShopTransportType::RobotHandoff,
            LBBodyShopMaterialIds::Underbody, FVector(-400.0f, 0.0f, 80.0f),
            FRotator(0.0f, 180.0f, 0.0f)));
        Underbody.Ports.Add(Port(LBBodyShopPrototypeIds::SkidIn,
            ELBBodyShopPortDirection::Input, ELBBodyShopTransportType::SkidConveyor,
            LBBodyShopMaterialIds::Underbody, FVector(-500.0f, 200.0f, 35.0f),
            FRotator(0.0f, 180.0f, 0.0f)));
        Underbody.Ports.Add(Port(LBBodyShopPrototypeIds::SkidOut,
            ELBBodyShopPortDirection::Output, ELBBodyShopTransportType::SkidConveyor,
            LBBodyShopMaterialIds::Underbody, FVector(600.0f, 0.0f, 35.0f)));
        Underbody.RobotSlots.Add(Slot(TEXT("ROBOT_WELD_LEFT"), FVector(0.0f, -300.0f, 0.0f),
            FRotator(0.0f, 35.0f, 0.0f), ELBBodyShopRobotRole::SpotWelding,
            ELBBodyShopToolType::SpotCGun, 390.0f, 260.0f));
        Underbody.RobotSlots.Add(Slot(TEXT("ROBOT_WELD_RIGHT"), FVector(0.0f, 300.0f, 0.0f),
            FRotator(0.0f, -35.0f, 0.0f), ELBBodyShopRobotRole::SpotWelding,
            ELBBodyShopToolType::SpotCGun, 390.0f, 260.0f));
        Result.Add(Underbody);

        FLBBodyShopCellDefinition Conveyor = Base(LBBodyShopPrototypeIds::StraightSkidConveyor,
            ELBBodyShopCellType::StraightSkidConveyor, TEXT("Straight skid conveyor"),
            FVector(800.0f, 300.0f, 110.0f), FVector(900.0f, 400.0f, 180.0f), 4.0f, 1);
        Conveyor.Ports.Add(Port(LBBodyShopPrototypeIds::SkidIn, ELBBodyShopPortDirection::Input,
            ELBBodyShopTransportType::SkidConveyor, LBBodyShopMaterialIds::Underbody,
            FVector(-500.0f, 0.0f, 35.0f), FRotator(0.0f, 180.0f, 0.0f)));
        Conveyor.Ports.Add(Port(LBBodyShopPrototypeIds::SkidOut, ELBBodyShopPortDirection::Output,
            ELBBodyShopTransportType::SkidConveyor, LBBodyShopMaterialIds::Underbody,
            FVector(500.0f, 0.0f, 35.0f)));
        Result.Add(Conveyor);

        FLBBodyShopCellDefinition Vision = Base(LBBodyShopPrototypeIds::BasicVisionGate,
            ELBBodyShopCellType::BasicVisionGate, TEXT("Basic BIW vision gate"),
            FVector(600.0f, 400.0f, 420.0f), FVector(700.0f, 500.0f, 460.0f), 3.0f, 1);
        Vision.Ports.Add(Port(LBBodyShopPrototypeIds::BodyIn, ELBBodyShopPortDirection::Input,
            ELBBodyShopTransportType::SkidConveyor, LBBodyShopMaterialIds::Underbody,
            FVector(-400.0f, 0.0f, 35.0f), FRotator(0.0f, 180.0f, 0.0f)));
        Vision.Ports.Add(Port(LBBodyShopPrototypeIds::BodyOut, ELBBodyShopPortDirection::Output,
            ELBBodyShopTransportType::SkidConveyor, LBBodyShopMaterialIds::Underbody,
            FVector(400.0f, 0.0f, 35.0f)));
        Result.Add(Vision);

        FLBBodyShopCellDefinition Buffer = Base(LBBodyShopPrototypeIds::OutputBuffer,
            ELBBodyShopCellType::OutputBuffer, TEXT("Underbody output buffer"),
            FVector(800.0f, 400.0f, 160.0f), FVector(900.0f, 500.0f, 220.0f), 1.0f, 2);
        Buffer.Ports.Add(Port(LBBodyShopPrototypeIds::BodyIn, ELBBodyShopPortDirection::Input,
            ELBBodyShopTransportType::SkidConveyor, LBBodyShopMaterialIds::Underbody,
            FVector(-500.0f, 0.0f, 35.0f), FRotator(0.0f, 180.0f, 0.0f), 2));
        Result.Add(Buffer);

        return Result;
    }

    const TArray<FLBBodyShopCellDefinition>& CanonicalDefinitions()
    {
        static const TArray<FLBBodyShopCellDefinition> Definitions = BuildCanonicalDefinitions();
        return Definitions;
    }

    bool IsFiniteTransform(const FTransform& Transform)
    {
        const FVector Location = Transform.GetLocation();
        const FVector Scale = Transform.GetScale3D();
        const FQuat Rotation = Transform.GetRotation();
        return !Location.ContainsNaN() && !Scale.ContainsNaN() && !Rotation.ContainsNaN()
            && Rotation.IsNormalized()
            && Scale.GetAbsMin() > KINDA_SMALL_NUMBER;
    }
}

FPrimaryAssetId ULBBodyShopCellDefinitionAsset::GetPrimaryAssetId() const
{
    return Definition.DefinitionId.IsNone()
        ? Super::GetPrimaryAssetId()
        : FPrimaryAssetId(TEXT("BodyShopCell"), Definition.DefinitionId);
}

TArray<FName> FLBBodyShopDefinitionRegistry::GetApprovedUnderbodySliceDefinitionIds()
{
    return {
        LBBodyShopPrototypeIds::FullStillageDock,
        LBBodyShopPrototypeIds::PanelPresentation,
        LBBodyShopPrototypeIds::UnderbodyFixture,
        LBBodyShopPrototypeIds::StraightSkidConveyor,
        LBBodyShopPrototypeIds::BasicVisionGate,
        LBBodyShopPrototypeIds::OutputBuffer
    };
}

bool FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(const FName DefinitionId,
    FLBBodyShopCellDefinition& OutDefinition)
{
    const FLBBodyShopCellDefinition* Found =
        LBBodyShopTypesPrivate::CanonicalDefinitions().FindByPredicate(
            [DefinitionId](const FLBBodyShopCellDefinition& Candidate)
            {
                return Candidate.DefinitionId == DefinitionId;
            });
    if (!Found) return false;
    OutDefinition = *Found;
    return true;
}

bool FLBBodyShopDefinitionRegistry::ValidateDefinition(
    const FLBBodyShopCellDefinition& Definition, FString& OutReason)
{
    OutReason.Reset();
    if (Definition.Version != 1 || Definition.DefinitionId.IsNone()
        || Definition.DisplayName.IsEmpty() || Definition.FootprintCm.ContainsNaN()
        || Definition.MaintenanceEnvelopeCm.ContainsNaN()
        || Definition.FootprintCm.GetMin() <= 0.0f
        || Definition.MaintenanceEnvelopeCm.GetMin() <= 0.0f
        || !FMath::IsFinite(Definition.CycleSeconds) || Definition.CycleSeconds < 0.0f
        || Definition.WIPCapacity < 1)
    {
        OutReason = TEXT("BODY SHOP CELL DEFINITION HAS INVALID CORE FIELDS");
        return false;
    }

    TSet<FName> PortIds;
    for (const FLBBodyShopPortDefinition& PortDef : Definition.Ports)
    {
        if (PortDef.PortId.IsNone() || PortDef.MaterialId.IsNone() || PortDef.Capacity < 1
            || !LBBodyShopTypesPrivate::IsFiniteTransform(PortDef.LocalTransform)
            || PortIds.Contains(PortDef.PortId))
        {
            OutReason = TEXT("BODY SHOP CELL DEFINITION HAS INVALID OR DUPLICATE PORTS");
            return false;
        }
        PortIds.Add(PortDef.PortId);
    }

    TSet<FName> SlotIds;
    for (const FLBBodyShopRobotSlotDefinition& SlotDef : Definition.RobotSlots)
    {
        if (SlotDef.SlotId.IsNone() || SlotIds.Contains(SlotDef.SlotId)
            || SlotDef.AllowedRoles.IsEmpty() || SlotDef.AllowedTools.IsEmpty()
            || !LBBodyShopTypesPrivate::IsFiniteTransform(SlotDef.LocalMountTransform)
            || !FMath::IsFinite(SlotDef.ReachRadiusCm) || SlotDef.ReachRadiusCm <= 0.0f
            || !FMath::IsFinite(SlotDef.SweepRadiusCm) || SlotDef.SweepRadiusCm <= 0.0f
            || SlotDef.SweepRadiusCm > SlotDef.ReachRadiusCm)
        {
            OutReason = TEXT("BODY SHOP CELL DEFINITION HAS INVALID OR DUPLICATE ROBOT SLOTS");
            return false;
        }
        SlotIds.Add(SlotDef.SlotId);
    }
    return true;
}

bool FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(
    const FLBBodyShopCellDefinition& Definition,
    const TArray<FLBBodyShopRobotAssignment>& Assignments, FString& OutReason)
{
    OutReason.Reset();
    TSet<FName> AssignedSlots;
    for (const FLBBodyShopRobotAssignment& Assignment : Assignments)
    {
        const FLBBodyShopRobotSlotDefinition* SlotDef = Definition.RobotSlots.FindByPredicate(
            [&Assignment](const FLBBodyShopRobotSlotDefinition& Candidate)
            {
                return Candidate.SlotId == Assignment.SlotId;
            });
        if (!SlotDef || AssignedSlots.Contains(Assignment.SlotId)
            || Assignment.Role == ELBBodyShopRobotRole::None
            || Assignment.Tool == ELBBodyShopToolType::None
            || !SlotDef->AllowedRoles.Contains(Assignment.Role)
            || !SlotDef->AllowedTools.Contains(Assignment.Tool)
            || !FMath::IsFinite(Assignment.Condition01)
            || !FMath::IsWithinInclusive(Assignment.Condition01, 0.0f, 1.0f))
        {
            OutReason = TEXT("BODY SHOP ROBOT ASSIGNMENT DOES NOT MATCH AN AUTHORED SLOT");
            return false;
        }
        AssignedSlots.Add(Assignment.SlotId);
    }
    return true;
}

bool FLBBodyShopDefinitionRegistry::ValidateExperimentalSaveState(
    const FLBBodyShopExperimentalSaveState& State, FString& OutReason)
{
    OutReason.Reset();
    if (State.Version != 1 || State.NextCellSerial < 1 || State.NextConnectionSerial < 1
        || State.NextWIPSerial < 1 || State.NextGenealogySequence < 1)
    {
        OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE HEADER IS INVALID");
        return false;
    }

    TSet<FName> CellIds;
    TMap<FName, FLBBodyShopCellDefinition> DefinitionsByCell;
    for (const FLBBodyShopPlacedCellSaveState& Cell : State.Cells)
    {
        FLBBodyShopCellDefinition Definition;
        if (Cell.Version != 1 || Cell.CellId.IsNone() || CellIds.Contains(Cell.CellId)
            || !LBBodyShopTypesPrivate::IsFiniteTransform(Cell.WorldTransform)
            || !FMath::IsFinite(Cell.ProcessProgress01)
            || !FMath::IsWithinInclusive(Cell.ProcessProgress01, 0.0f, 1.0f)
            || !FindCanonicalDefinition(Cell.DefinitionId, Definition)
            || !ValidateRobotAssignments(Definition, Cell.RobotAssignments, OutReason))
        {
            if (OutReason.IsEmpty()) OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE HAS INVALID CELLS");
            return false;
        }
        CellIds.Add(Cell.CellId);
        DefinitionsByCell.Add(Cell.CellId, Definition);
    }

    TSet<FName> ConnectionIds;
    TSet<FString> UsedEndpoints;
    for (const FLBBodyShopConnectionSaveState& Connection : State.Connections)
    {
        const FLBBodyShopCellDefinition* SourceDef = DefinitionsByCell.Find(Connection.SourceCellId);
        const FLBBodyShopCellDefinition* TargetDef = DefinitionsByCell.Find(Connection.TargetCellId);
        const FLBBodyShopPortDefinition* SourcePort = SourceDef
            ? SourceDef->Ports.FindByPredicate([&Connection](const FLBBodyShopPortDefinition& P)
                { return P.PortId == Connection.SourcePortId; }) : nullptr;
        const FLBBodyShopPortDefinition* TargetPort = TargetDef
            ? TargetDef->Ports.FindByPredicate([&Connection](const FLBBodyShopPortDefinition& P)
                { return P.PortId == Connection.TargetPortId; }) : nullptr;
        const FString SourceEndpoint = Connection.SourceCellId.ToString() + TEXT("/")
            + Connection.SourcePortId.ToString();
        const FString TargetEndpoint = Connection.TargetCellId.ToString() + TEXT("/")
            + Connection.TargetPortId.ToString();
        if (Connection.Version != 1 || Connection.ConnectionId.IsNone()
            || ConnectionIds.Contains(Connection.ConnectionId) || !SourcePort || !TargetPort
            || SourcePort->Direction != ELBBodyShopPortDirection::Output
            || TargetPort->Direction != ELBBodyShopPortDirection::Input
            || SourcePort->Transport != TargetPort->Transport
            || SourcePort->MaterialId != TargetPort->MaterialId
            || UsedEndpoints.Contains(SourceEndpoint) || UsedEndpoints.Contains(TargetEndpoint))
        {
            OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE HAS INVALID CONNECTIONS");
            return false;
        }
        ConnectionIds.Add(Connection.ConnectionId);
        UsedEndpoints.Add(SourceEndpoint);
        UsedEndpoints.Add(TargetEndpoint);
    }

    TSet<FName> WIPIds;
    TSet<int64> GenealogySequences;
    for (const FLBBodyShopWIPSaveState& Unit : State.WIP)
    {
        if (Unit.Version != 1 || Unit.UnitId.IsNone() || WIPIds.Contains(Unit.UnitId)
            || Unit.MaterialId.IsNone() || !CellIds.Contains(Unit.CurrentCellId)
            || Unit.GenealogySequence < 1 || GenealogySequences.Contains(Unit.GenealogySequence))
        {
            OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE HAS INVALID OR DUPLICATE WIP");
            return false;
        }
        WIPIds.Add(Unit.UnitId);
        GenealogySequences.Add(Unit.GenealogySequence);
    }

    TSet<FName> OwnedWIPIds;
    for (const FLBBodyShopPlacedCellSaveState& Cell : State.Cells)
    {
        TArray<FName> References = Cell.QueuedWIPIds;
        if (!Cell.ActiveWIPId.IsNone()) References.Add(Cell.ActiveWIPId);
        for (const FName WIPId : References)
        {
            if (!WIPIds.Contains(WIPId) || OwnedWIPIds.Contains(WIPId))
            {
                OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE HAS INVALID WIP OWNERSHIP");
                return false;
            }
            const FLBBodyShopWIPSaveState* Unit = State.WIP.FindByPredicate(
                [WIPId](const FLBBodyShopWIPSaveState& Candidate)
                {
                    return Candidate.UnitId == WIPId;
                });
            if (!Unit || Unit->CurrentCellId != Cell.CellId)
            {
                OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE HAS CONTRADICTORY WIP OWNERSHIP");
                return false;
            }
            OwnedWIPIds.Add(WIPId);
        }
    }
    if (OwnedWIPIds.Num() != WIPIds.Num())
    {
        OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE HAS UNOWNED WIP");
        return false;
    }
    return true;
}
