#include "LBBodyShopBuildAuthority.h"

#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "LBBodyShopCellActor.h"
#include "LBBodyShopPortComponent.h"

namespace LBBodyShopBuildPrivate
{
    constexpr float PositionToleranceCm = 20.0f;
    constexpr float YawToleranceDegrees = 2.0f;
    constexpr float FootprintInsetCm = 0.5f;

    void ConfigureExclusion(UBoxComponent* Component, const FVector& Location,
        const FVector& Extent, const TCHAR* Tag)
    {
        if (!Component) return;
        Component->SetRelativeLocation(Location);
        Component->SetBoxExtent(Extent);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCollisionResponseToAllChannels(ECR_Ignore);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetHiddenInGame(true);
        Component->ComponentTags.Add(FName(Tag));
    }

    float NormalizedYaw(const float Yaw)
    {
        return FRotator::NormalizeAxis(Yaw);
    }

    bool IsQuarterTurn(const float Yaw)
    {
        const float Remainder = FMath::Fmod(FMath::Abs(NormalizedYaw(Yaw)), 90.0f);
        return FMath::IsNearlyZero(Remainder, 0.01f)
            || FMath::IsNearlyEqual(Remainder, 90.0f, 0.01f);
    }
}

ALBBodyShopBuildAuthority::ALBBodyShopBuildAuthority()
{
    PrimaryActorTick.bCanEverTick = false;
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    BuildArea = CreateDefaultSubobject<UBoxComponent>(TEXT("BuildArea"));
    BuildArea->SetupAttachment(SceneRoot);
    BuildArea->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BuildArea->SetCollisionResponseToAllChannels(ECR_Ignore);
    BuildArea->SetGenerateOverlapEvents(false);
    BuildArea->SetCanEverAffectNavigation(false);
    BuildArea->SetHiddenInGame(true);

    PedestrianExclusion = CreateDefaultSubobject<UBoxComponent>(TEXT("PedestrianExclusion"));
    PedestrianExclusion->SetupAttachment(SceneRoot);
    FLTRouteExclusion = CreateDefaultSubobject<UBoxComponent>(TEXT("FLTRouteExclusion"));
    FLTRouteExclusion->SetupAttachment(SceneRoot);
    NorthServiceExclusion = CreateDefaultSubobject<UBoxComponent>(TEXT("NorthServiceExclusion"));
    NorthServiceExclusion->SetupAttachment(SceneRoot);
    SouthServiceExclusion = CreateDefaultSubobject<UBoxComponent>(TEXT("SouthServiceExclusion"));
    SouthServiceExclusion->SetupAttachment(SceneRoot);

    Tags.AddUnique(TEXT("LB.BodyShop.Experimental.BuildAuthority.v001"));
}

void ALBBodyShopBuildAuthority::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    BuildArea->SetBoxExtent(BuildAreaHalfExtentCm);
    LBBodyShopBuildPrivate::ConfigureExclusion(PedestrianExclusion,
        FVector(0.0f, 4000.0f, 25.0f), FVector(8200.0f, 90.0f, 25.0f),
        TEXT("LB.BodyShop.Exclusion.Pedestrian"));
    LBBodyShopBuildPrivate::ConfigureExclusion(FLTRouteExclusion,
        FVector(-250.0f, -3750.0f, 25.0f), FVector(8250.0f, 250.0f, 25.0f),
        TEXT("LB.BodyShop.Exclusion.FLT"));
    LBBodyShopBuildPrivate::ConfigureExclusion(NorthServiceExclusion,
        FVector(0.0f, 3400.0f, 25.0f), FVector(8000.0f, 200.0f, 25.0f),
        TEXT("LB.BodyShop.Exclusion.NorthService"));
    LBBodyShopBuildPrivate::ConfigureExclusion(SouthServiceExclusion,
        FVector(0.0f, -3175.0f, 25.0f), FVector(8000.0f, 125.0f, 25.0f),
        TEXT("LB.BodyShop.Exclusion.SouthService"));
}

bool ALBBodyShopBuildAuthority::IsTransformGridAligned(const FTransform& Transform) const
{
    const FVector Location = Transform.GetLocation();
    const FVector Scale = Transform.GetScale3D();
    const FRotator Rotation = Transform.Rotator();
    const auto IsGrid = [this](const float Value)
    {
        return FMath::IsNearlyEqual(Value, FMath::GridSnap(Value, PlacementGridCm), 0.01f);
    };
    return !Location.ContainsNaN() && !Scale.ContainsNaN()
        && Scale.Equals(FVector::OneVector, 0.001f)
        && IsGrid(Location.X) && IsGrid(Location.Y) && FMath::IsNearlyZero(Location.Z, 0.01f)
        && FMath::IsNearlyZero(Rotation.Pitch, 0.01f)
        && FMath::IsNearlyZero(Rotation.Roll, 0.01f)
        && LBBodyShopBuildPrivate::IsQuarterTurn(Rotation.Yaw);
}

FBox ALBBodyShopBuildAuthority::GetWorldFootprint(const FLBBodyShopCellDefinition& Definition,
    const FTransform& Transform)
{
    const FVector Half(Definition.FootprintCm.X * 0.5f, Definition.FootprintCm.Y * 0.5f,
        Definition.FootprintCm.Z * 0.5f);
    FBox Local(-Half, Half);
    return Local.TransformBy(Transform);
}

bool ALBBodyShopBuildAuthority::IsWithinBuildArea(const FLBBodyShopCellDefinition& Definition,
    const FTransform& Transform) const
{
    const FBox WorldFootprint = GetWorldFootprint(Definition, Transform);
    const FVector Centre = GetActorTransform().TransformPosition(BuildArea->GetRelativeLocation());
    const FBox WorldBuild(Centre - BuildAreaHalfExtentCm, Centre + BuildAreaHalfExtentCm);
    return WorldBuild.IsInsideOrOn(WorldFootprint.Min) && WorldBuild.IsInsideOrOn(WorldFootprint.Max);
}

bool ALBBodyShopBuildAuthority::IntersectsProtectedZone(const FBox& FootprintWorld) const
{
    for (const UBoxComponent* Zone : {PedestrianExclusion.Get(), FLTRouteExclusion.Get(),
        NorthServiceExclusion.Get(), SouthServiceExclusion.Get()})
    {
        if (!Zone) continue;
        if (FootprintWorld.Intersect(Zone->Bounds.GetBox())) return true;
    }
    return false;
}

bool ALBBodyShopBuildAuthority::IntersectsOtherCell(const FLBBodyShopCellDefinition& Definition,
    const FTransform& Transform, const ALBBodyShopCellActor* IgnoredCell) const
{
    FBox Candidate = GetWorldFootprint(Definition, Transform);
    Candidate = Candidate.ExpandBy(-LBBodyShopBuildPrivate::FootprintInsetCm);
    for (const ALBBodyShopCellActor* Cell : PlacedCells)
    {
        if (!IsValid(Cell) || Cell == IgnoredCell) continue;
        FBox Existing = GetWorldFootprint(Cell->GetDefinition(), Cell->GetActorTransform());
        Existing = Existing.ExpandBy(-LBBodyShopBuildPrivate::FootprintInsetCm);
        if (Candidate.Intersect(Existing)) return true;
    }
    return false;
}

bool ALBBodyShopBuildAuthority::ValidateModulePlacement(const FName DefinitionId,
    const FTransform& Transform, FString& OutReason, const ALBBodyShopCellActor* IgnoredCell) const
{
    OutReason.Reset();
    FLBBodyShopCellDefinition Definition;
    if (!FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(DefinitionId, Definition))
    {
        OutReason = TEXT("BODY SHOP MODULE DEFINITION IS NOT APPROVED");
        return false;
    }
    if (!IsTransformGridAligned(Transform))
    {
        OutReason = TEXT("BODY SHOP MODULE MUST USE 100 CM SNAP, FLOOR DATUM AND 90 DEGREE ROTATION");
        return false;
    }
    if (!IsWithinBuildArea(Definition, Transform))
    {
        OutReason = TEXT("BODY SHOP MODULE FOOTPRINT EXCEEDS THE BUILDABLE AREA");
        return false;
    }
    const FBox FootprintWorld = GetWorldFootprint(Definition, Transform);
    if (IntersectsProtectedZone(FootprintWorld))
    {
        OutReason = TEXT("BODY SHOP MODULE ENTERS A PROTECTED PEDESTRIAN, FLT OR SERVICE ZONE");
        return false;
    }
    if (IntersectsOtherCell(Definition, Transform, IgnoredCell))
    {
        OutReason = TEXT("BODY SHOP MODULE FOOTPRINT OVERLAPS ANOTHER CELL");
        return false;
    }
    return true;
}

void ALBBodyShopBuildAuthority::ValidateModulePlacementForValidation(const FName DefinitionId,
    const FTransform& Transform, bool& bOutValid, FString& OutReason) const
{
    bOutValid = ValidateModulePlacement(DefinitionId, Transform, OutReason);
}

FName ALBBodyShopBuildAuthority::AllocateCellId()
{
    return FName(*FString::Printf(TEXT("BODYSHOP-CELL-%03d"), NextCellSerial++));
}

FName ALBBodyShopBuildAuthority::AllocateConnectionId()
{
    return FName(*FString::Printf(TEXT("BODYSHOP-CONNECTION-%03d"), NextConnectionSerial++));
}

bool ALBBodyShopBuildAuthority::PlaceModule(const FName DefinitionId, const FTransform& Transform,
    ALBBodyShopCellActor*& OutCell, FString& OutReason)
{
    OutCell = nullptr;
    if (!ValidateModulePlacement(DefinitionId, Transform, OutReason)) return false;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("BODY SHOP BUILD WORLD IS OFFLINE");
        return false;
    }
    FActorSpawnParameters SpawnParams;
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    const FName ProposedCellId(*FString::Printf(TEXT("BODYSHOP-CELL-%03d"), NextCellSerial));
    ALBBodyShopCellActor* Candidate = World->SpawnActor<ALBBodyShopCellActor>(
        ALBBodyShopCellActor::StaticClass(), Transform, SpawnParams);
    if (!Candidate || !Candidate->ConfigureCell(ProposedCellId, DefinitionId, OutReason))
    {
        if (Candidate) Candidate->Destroy();
        if (OutReason.IsEmpty()) OutReason = TEXT("BODY SHOP MODULE SPAWN FAILED");
        return false;
    }
    OwnedCells.Add(Candidate);
    PlacedCells.Add(Candidate);
    ++NextCellSerial;
    OutCell = Candidate;
    return true;
}

bool ALBBodyShopBuildAuthority::MoveModule(const FName CellId, const FTransform& Transform,
    FString& OutReason)
{
    ALBBodyShopCellActor* Cell = FindCell(CellId);
    if (!Cell)
    {
        OutReason = TEXT("BODY SHOP CELL DOES NOT EXIST");
        return false;
    }
    if (!Cell->GetQueuedWIPIds().IsEmpty() || !Cell->GetActiveWIPId().IsNone())
    {
        OutReason = TEXT("BODY SHOP CELL WITH WIP CANNOT BE MOVED");
        return false;
    }
    if (Connections.ContainsByPredicate([CellId](const FLBBodyShopConnectionSaveState& Connection)
        { return Connection.SourceCellId == CellId || Connection.TargetCellId == CellId; }))
    {
        OutReason = TEXT("DISCONNECT BODY SHOP PORTS BEFORE MOVING A CELL");
        return false;
    }
    if (!ValidateModulePlacement(Cell->GetDefinitionId(), Transform, OutReason, Cell)) return false;
    Cell->SetActorTransform(Transform, false, nullptr, ETeleportType::TeleportPhysics);
    return true;
}

bool ALBBodyShopBuildAuthority::RemoveModule(const FName CellId, FString& OutReason)
{
    ALBBodyShopCellActor* Cell = FindCell(CellId);
    if (!Cell)
    {
        OutReason = TEXT("BODY SHOP CELL DOES NOT EXIST");
        return false;
    }
    if (!Cell->GetQueuedWIPIds().IsEmpty() || !Cell->GetActiveWIPId().IsNone()
        || Connections.ContainsByPredicate([CellId](const FLBBodyShopConnectionSaveState& Connection)
            { return Connection.SourceCellId == CellId || Connection.TargetCellId == CellId; }))
    {
        OutReason = TEXT("DISCONNECT AND EMPTY BODY SHOP CELL BEFORE REMOVING IT");
        return false;
    }
    PlacedCells.Remove(Cell);
    OwnedCells.Remove(Cell);
    Cell->Destroy();
    return true;
}

ALBBodyShopCellActor* ALBBodyShopBuildAuthority::FindCell(const FName CellId) const
{
    ALBBodyShopCellActor* const* Found = PlacedCells.FindByPredicate([CellId](const ALBBodyShopCellActor* Cell)
    {
        return IsValid(Cell) && Cell->GetCellId() == CellId;
    });
    return Found ? *Found : nullptr;
}

bool ALBBodyShopBuildAuthority::AssignRobotToSlot(const FName CellId, const FName SlotId,
    const ELBBodyShopRobotRole InRobotRole, const ELBBodyShopToolType InTool, FString& OutReason)
{
    ALBBodyShopCellActor* Cell = FindCell(CellId);
    if (!Cell || SlotId.IsNone())
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT DOES NOT EXIST");
        return false;
    }
    TArray<FLBBodyShopRobotAssignment> Assignments = Cell->GetRobotAssignments();
    Assignments.RemoveAll([SlotId](const FLBBodyShopRobotAssignment& Assignment)
        { return Assignment.SlotId == SlotId; });
    FLBBodyShopRobotAssignment& Assignment = Assignments.AddDefaulted_GetRef();
    Assignment.SlotId = SlotId;
    Assignment.Role = InRobotRole;
    Assignment.Tool = InTool;
    Assignment.bEnabled = true;
    Assignment.Condition01 = 1.0f;
    return Cell->ApplyRobotAssignments(Assignments, OutReason);
}

bool ALBBodyShopBuildAuthority::ClearRobotSlot(const FName CellId, const FName SlotId,
    FString& OutReason)
{
    ALBBodyShopCellActor* Cell = FindCell(CellId);
    if (!Cell || SlotId.IsNone())
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT DOES NOT EXIST");
        return false;
    }
    TArray<FLBBodyShopRobotAssignment> Assignments = Cell->GetRobotAssignments();
    const int32 Removed = Assignments.RemoveAll([SlotId](const FLBBodyShopRobotAssignment& Assignment)
        { return Assignment.SlotId == SlotId; });
    if (Removed != 1)
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT IS NOT ASSIGNED");
        return false;
    }
    return Cell->ApplyRobotAssignments(Assignments, OutReason);
}

bool ALBBodyShopBuildAuthority::IsEndpointConnected(const FLBBodyShopPortAddress& Address) const
{
    return Connections.ContainsByPredicate([&Address](const FLBBodyShopConnectionSaveState& Connection)
    {
        return (Connection.SourceCellId == Address.CellId && Connection.SourcePortId == Address.PortId)
            || (Connection.TargetCellId == Address.CellId && Connection.TargetPortId == Address.PortId);
    });
}

bool ALBBodyShopBuildAuthority::CanConnect(const FLBBodyShopPortAddress& Source,
    const FLBBodyShopPortAddress& Target, FString& OutReason) const
{
    OutReason.Reset();
    ALBBodyShopCellActor* SourceCell = FindCell(Source.CellId);
    ALBBodyShopCellActor* TargetCell = FindCell(Target.CellId);
    ULBBodyShopPortComponent* SourcePort = SourceCell ? SourceCell->FindPort(Source.PortId) : nullptr;
    ULBBodyShopPortComponent* TargetPort = TargetCell ? TargetCell->FindPort(Target.PortId) : nullptr;
    if (!Source.IsValid() || !Target.IsValid() || Source == Target || !SourcePort || !TargetPort
        || SourcePort->GetDirection() != ELBBodyShopPortDirection::Output
        || TargetPort->GetDirection() != ELBBodyShopPortDirection::Input
        || SourcePort->GetMaterialId() != TargetPort->GetMaterialId()
        || SourcePort->GetTransport() != TargetPort->GetTransport())
    {
        OutReason = TEXT("BODY SHOP PORTS HAVE INCOMPATIBLE DIRECTION, MATERIAL OR TRANSPORT");
        return false;
    }
    if (IsEndpointConnected(Source) || IsEndpointConnected(Target))
    {
        OutReason = TEXT("BODY SHOP PORT IS ALREADY CONNECTED");
        return false;
    }
    if (FVector::Dist(SourcePort->GetComponentLocation(), TargetPort->GetComponentLocation())
        > LBBodyShopBuildPrivate::PositionToleranceCm)
    {
        OutReason = TEXT("BODY SHOP PORTS MUST SNAP WITHIN 20 CM");
        return false;
    }
    const float Facing = FMath::Abs(FRotator::NormalizeAxis(
        SourcePort->GetComponentRotation().Yaw - TargetPort->GetComponentRotation().Yaw));
    if (!FMath::IsNearlyEqual(Facing, 180.0f, LBBodyShopBuildPrivate::YawToleranceDegrees))
    {
        OutReason = TEXT("BODY SHOP PORTS MUST FACE EACH OTHER");
        return false;
    }
    return true;
}

bool ALBBodyShopBuildAuthority::Connect(const FLBBodyShopPortAddress& Source,
    const FLBBodyShopPortAddress& Target, FName& OutConnectionId, FString& OutReason)
{
    OutConnectionId = NAME_None;
    if (!CanConnect(Source, Target, OutReason)) return false;
    FLBBodyShopConnectionSaveState& Connection = Connections.AddDefaulted_GetRef();
    Connection.ConnectionId = AllocateConnectionId();
    Connection.SourceCellId = Source.CellId;
    Connection.SourcePortId = Source.PortId;
    Connection.TargetCellId = Target.CellId;
    Connection.TargetPortId = Target.PortId;
    OutConnectionId = Connection.ConnectionId;
    return true;
}

bool ALBBodyShopBuildAuthority::Disconnect(const FName ConnectionId, FString& OutReason)
{
    const int32 Removed = Connections.RemoveAll([ConnectionId](const FLBBodyShopConnectionSaveState& Connection)
        { return Connection.ConnectionId == ConnectionId; });
    if (Removed != 1)
    {
        OutReason = TEXT("BODY SHOP CONNECTION DOES NOT EXIST");
        return false;
    }
    return true;
}

bool ALBBodyShopBuildAuthority::ValidateCommissioning(const FName CellId,
    FLBBodyShopValidationReport& OutReport) const
{
    OutReport = FLBBodyShopValidationReport();
    ALBBodyShopCellActor* Cell = FindCell(CellId);
    if (!Cell)
    {
        OutReport.Errors.Add(TEXT("CELL DOES NOT EXIST"));
        return false;
    }
    FString Reason;
    if (!FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(Cell->GetDefinition(),
        Cell->GetRobotAssignments(), Reason)) OutReport.Errors.Add(Reason);
    if (Cell->GetConfiguredRobotCount() != Cell->GetAuthoredRobotSlotCount())
        OutReport.Errors.Add(TEXT("EVERY AUTHORED ROBOT SLOT MUST BE ASSIGNED"));
    for (const FLBBodyShopRobotAssignment& Assignment : Cell->GetRobotAssignments())
    {
        if (!Assignment.bEnabled || Assignment.Condition01 <= 0.0f)
            OutReport.Errors.Add(TEXT("ROBOT ASSIGNMENT IS NOT AVAILABLE"));
    }
    OutReport.bValid = OutReport.Errors.IsEmpty();
    return OutReport.bValid;
}

bool ALBBodyShopBuildAuthority::CommissionModule(const FName CellId, FString& OutReason)
{
    FLBBodyShopValidationReport Report;
    if (!ValidateCommissioning(CellId, Report))
    {
        OutReason = FString::Join(Report.Errors, TEXT(" | "));
        return false;
    }
    ALBBodyShopCellActor* Cell = FindCell(CellId);
    return Cell && Cell->SetCommissioned(true, OutReason);
}

bool ALBBodyShopBuildAuthority::HasExactConnection(const FName SourceDefinition,
    const FName SourcePort, const FName TargetDefinition, const FName TargetPort) const
{
    return Connections.ContainsByPredicate([this, SourceDefinition, SourcePort, TargetDefinition, TargetPort]
        (const FLBBodyShopConnectionSaveState& Connection)
    {
        const ALBBodyShopCellActor* Source = FindCell(Connection.SourceCellId);
        const ALBBodyShopCellActor* Target = FindCell(Connection.TargetCellId);
        return Source && Target && Source->GetDefinitionId() == SourceDefinition
            && Connection.SourcePortId == SourcePort && Target->GetDefinitionId() == TargetDefinition
            && Connection.TargetPortId == TargetPort;
    });
}

bool ALBBodyShopBuildAuthority::ValidateUnderbodySlice(FLBBodyShopValidationReport& OutReport) const
{
    OutReport = FLBBodyShopValidationReport();
    const TArray<FName> Required = FLBBodyShopDefinitionRegistry::GetApprovedUnderbodySliceDefinitionIds();
    for (const FName DefinitionId : Required)
    {
        int32 Count = 0;
        for (const ALBBodyShopCellActor* Cell : PlacedCells)
        {
            if (IsValid(Cell) && Cell->GetDefinitionId() == DefinitionId) ++Count;
        }
        if (Count != 1)
            OutReport.Errors.Add(FString::Printf(TEXT("SLICE REQUIRES EXACTLY ONE %s"),
                *DefinitionId.ToString()));
    }
    if (!HasExactConnection(LBBodyShopPrototypeIds::FullStillageDock,
            LBBodyShopPrototypeIds::StillageOut, LBBodyShopPrototypeIds::PanelPresentation,
            LBBodyShopPrototypeIds::StillageIn))
        OutReport.Errors.Add(TEXT("MISSING FULL STILLAGE TO PRESENTATION CONNECTION"));
    if (!HasExactConnection(LBBodyShopPrototypeIds::PanelPresentation,
            LBBodyShopPrototypeIds::PanelOut, LBBodyShopPrototypeIds::UnderbodyFixture,
            LBBodyShopPrototypeIds::PanelIn))
        OutReport.Errors.Add(TEXT("MISSING PRESENTATION TO UNDERBODY CONNECTION"));
    if (!HasExactConnection(LBBodyShopPrototypeIds::UnderbodyFixture,
            LBBodyShopPrototypeIds::SkidOut, LBBodyShopPrototypeIds::StraightSkidConveyor,
            LBBodyShopPrototypeIds::SkidIn))
        OutReport.Errors.Add(TEXT("MISSING UNDERBODY TO CONVEYOR CONNECTION"));
    if (!HasExactConnection(LBBodyShopPrototypeIds::StraightSkidConveyor,
            LBBodyShopPrototypeIds::SkidOut, LBBodyShopPrototypeIds::BasicVisionGate,
            LBBodyShopPrototypeIds::BodyIn))
        OutReport.Errors.Add(TEXT("MISSING CONVEYOR TO VISION CONNECTION"));
    if (!HasExactConnection(LBBodyShopPrototypeIds::BasicVisionGate,
            LBBodyShopPrototypeIds::BodyOut, LBBodyShopPrototypeIds::OutputBuffer,
            LBBodyShopPrototypeIds::BodyIn))
        OutReport.Errors.Add(TEXT("MISSING VISION TO OUTPUT BUFFER CONNECTION"));
    for (const ALBBodyShopCellActor* Cell : PlacedCells)
    {
        if (!Cell || !Required.Contains(Cell->GetDefinitionId())) continue;
        if (!Cell->IsCommissioned())
            OutReport.Errors.Add(FString::Printf(TEXT("CELL %s IS NOT COMMISSIONED"),
                *Cell->GetCellId().ToString()));
    }
    OutReport.bValid = OutReport.Errors.IsEmpty();
    return OutReport.bValid;
}

FLBBodyShopExperimentalSaveState ALBBodyShopBuildAuthority::CaptureTopologySaveState() const
{
    FLBBodyShopExperimentalSaveState State;
    State.NextCellSerial = NextCellSerial;
    State.NextConnectionSerial = NextConnectionSerial;
    State.Cells.Reserve(PlacedCells.Num());
    for (const ALBBodyShopCellActor* Cell : PlacedCells)
    {
        if (Cell) State.Cells.Add(Cell->CaptureSaveState());
    }
    State.Cells.Sort([](const FLBBodyShopPlacedCellSaveState& A,
        const FLBBodyShopPlacedCellSaveState& B) { return A.CellId.LexicalLess(B.CellId); });
    State.Connections = Connections;
    State.Connections.Sort([](const FLBBodyShopConnectionSaveState& A,
        const FLBBodyShopConnectionSaveState& B)
        { return A.ConnectionId.LexicalLess(B.ConnectionId); });
    return State;
}

bool ALBBodyShopBuildAuthority::RestoreTopologySaveState(const FLBBodyShopExperimentalSaveState& State,
    FString& OutReason)
{
    OutReason.Reset();
    if (!State.WIP.IsEmpty())
    {
        OutReason = TEXT("BODY SHOP TOPOLOGY RESTORE REQUIRES THE EXPERIMENTAL RUNTIME WIP PHASE");
        return false;
    }
    if (!FLBBodyShopDefinitionRegistry::ValidateExperimentalSaveState(State, OutReason)) return false;
    if (!GetWorld())
    {
        OutReason = TEXT("BODY SHOP TOPOLOGY RESTORE WORLD IS OFFLINE");
        return false;
    }

    TArray<FLBBodyShopCellDefinition> Definitions;
    Definitions.Reserve(State.Cells.Num());
    for (const FLBBodyShopPlacedCellSaveState& CellState : State.Cells)
    {
        FLBBodyShopCellDefinition Definition;
        if (!FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(CellState.DefinitionId, Definition)
            || !IsTransformGridAligned(CellState.WorldTransform)
            || !IsWithinBuildArea(Definition, CellState.WorldTransform)
            || IntersectsProtectedZone(GetWorldFootprint(Definition, CellState.WorldTransform)))
        {
            OutReason = TEXT("BODY SHOP TOPOLOGY RESTORE HAS AN INVALID CELL PLACEMENT");
            return false;
        }
        Definitions.Add(Definition);
    }
    for (int32 Left = 0; Left < State.Cells.Num(); ++Left)
    {
        for (int32 Right = Left + 1; Right < State.Cells.Num(); ++Right)
        {
            const FBox LeftFootprint = GetWorldFootprint(Definitions[Left],
                State.Cells[Left].WorldTransform).ExpandBy(-LBBodyShopBuildPrivate::FootprintInsetCm);
            const FBox RightFootprint = GetWorldFootprint(Definitions[Right],
                State.Cells[Right].WorldTransform).ExpandBy(-LBBodyShopBuildPrivate::FootprintInsetCm);
            if (LeftFootprint.Intersect(RightFootprint))
            {
                OutReason = TEXT("BODY SHOP TOPOLOGY RESTORE HAS OVERLAPPING CELL FOOTPRINTS");
                return false;
            }
        }
    }

    const auto FindCellIndex = [&State](const FName CellId)
    {
        return State.Cells.IndexOfByPredicate([CellId](const FLBBodyShopPlacedCellSaveState& CellState)
        {
            return CellState.CellId == CellId;
        });
    };
    for (const FLBBodyShopConnectionSaveState& Connection : State.Connections)
    {
        const int32 SourceIndex = FindCellIndex(Connection.SourceCellId);
        const int32 TargetIndex = FindCellIndex(Connection.TargetCellId);
        const FLBBodyShopPortDefinition* SourcePort = SourceIndex != INDEX_NONE
            ? Definitions[SourceIndex].Ports.FindByPredicate([&Connection](const FLBBodyShopPortDefinition& Port)
                { return Port.PortId == Connection.SourcePortId; }) : nullptr;
        const FLBBodyShopPortDefinition* TargetPort = TargetIndex != INDEX_NONE
            ? Definitions[TargetIndex].Ports.FindByPredicate([&Connection](const FLBBodyShopPortDefinition& Port)
                { return Port.PortId == Connection.TargetPortId; }) : nullptr;
        if (!SourcePort || !TargetPort)
        {
            OutReason = TEXT("BODY SHOP TOPOLOGY RESTORE HAS AN UNKNOWN PORT");
            return false;
        }
        const FTransform SourceWorld = SourcePort->LocalTransform * State.Cells[SourceIndex].WorldTransform;
        const FTransform TargetWorld = TargetPort->LocalTransform * State.Cells[TargetIndex].WorldTransform;
        const float Facing = FMath::Abs(FRotator::NormalizeAxis(
            SourceWorld.Rotator().Yaw - TargetWorld.Rotator().Yaw));
        if (FVector::Dist(SourceWorld.GetLocation(), TargetWorld.GetLocation())
                > LBBodyShopBuildPrivate::PositionToleranceCm
            || !FMath::IsNearlyEqual(Facing, 180.0f, LBBodyShopBuildPrivate::YawToleranceDegrees))
        {
            OutReason = TEXT("BODY SHOP TOPOLOGY RESTORE HAS NONCOINCIDENT PORTS");
            return false;
        }
    }

    TArray<TObjectPtr<ALBBodyShopCellActor>> StagedOwned;
    TArray<ALBBodyShopCellActor*> StagedCells;
    for (const FLBBodyShopPlacedCellSaveState& CellState : State.Cells)
    {
        FActorSpawnParameters SpawnParams;
        SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        ALBBodyShopCellActor* Cell = GetWorld() ? GetWorld()->SpawnActor<ALBBodyShopCellActor>(
            ALBBodyShopCellActor::StaticClass(), CellState.WorldTransform, SpawnParams) : nullptr;
        if (!Cell || !Cell->RestoreSaveState(CellState, OutReason))
        {
            if (Cell) Cell->Destroy();
            for (ALBBodyShopCellActor* Staged : StagedCells) if (Staged) Staged->Destroy();
            if (OutReason.IsEmpty()) OutReason = TEXT("BODY SHOP TOPOLOGY RESTORE STAGING FAILED");
            return false;
        }
        StagedOwned.Add(Cell);
        StagedCells.Add(Cell);
    }
    for (ALBBodyShopCellActor* Existing : PlacedCells) if (Existing) Existing->Destroy();
    OwnedCells = MoveTemp(StagedOwned);
    PlacedCells = MoveTemp(StagedCells);
    Connections = State.Connections;
    NextCellSerial = State.NextCellSerial;
    NextConnectionSerial = State.NextConnectionSerial;
    return true;
}

TArray<FLBBodyShopApprovedLayoutItem> ALBBodyShopBuildAuthority::GetApprovedUnderbodySliceLayout()
{
    TArray<FLBBodyShopApprovedLayoutItem> Layout;
    const auto Add = [&Layout](const FName DefinitionId, const FVector& Location)
    {
        FLBBodyShopApprovedLayoutItem& Item = Layout.AddDefaulted_GetRef();
        Item.DefinitionId = DefinitionId;
        Item.WorldTransform = FTransform(Location);
    };
    Add(LBBodyShopPrototypeIds::FullStillageDock, FVector(-6500.0f, -1800.0f, 0.0f));
    Add(LBBodyShopPrototypeIds::PanelPresentation, FVector(-5500.0f, -1800.0f, 0.0f));
    Add(LBBodyShopPrototypeIds::UnderbodyFixture, FVector(-4500.0f, -1800.0f, 0.0f));
    Add(LBBodyShopPrototypeIds::StraightSkidConveyor, FVector(-3400.0f, -1800.0f, 0.0f));
    Add(LBBodyShopPrototypeIds::BasicVisionGate, FVector(-2500.0f, -1800.0f, 0.0f));
    Add(LBBodyShopPrototypeIds::OutputBuffer, FVector(-1600.0f, -1800.0f, 0.0f));
    return Layout;
}

bool ALBBodyShopBuildAuthority::BuildApprovedUnderbodySliceLayout(FString& OutReason)
{
    if (!PlacedCells.IsEmpty() || !Connections.IsEmpty())
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE LAYOUT IS NOT EMPTY");
        return false;
    }
    const int32 InitialCellSerial = NextCellSerial;
    const int32 InitialConnectionSerial = NextConnectionSerial;
    const TArray<FLBBodyShopApprovedLayoutItem> Layout = GetApprovedUnderbodySliceLayout();
    TArray<ALBBodyShopCellActor*> Built;
    const auto Rollback = [this, &Built, InitialCellSerial, InitialConnectionSerial]()
    {
        for (ALBBodyShopCellActor* BuiltCell : Built) if (BuiltCell) BuiltCell->Destroy();
        PlacedCells.Reset();
        OwnedCells.Reset();
        Connections.Reset();
        NextCellSerial = InitialCellSerial;
        NextConnectionSerial = InitialConnectionSerial;
    };
    for (const FLBBodyShopApprovedLayoutItem& Item : Layout)
    {
        ALBBodyShopCellActor* Cell = nullptr;
        if (!PlaceModule(Item.DefinitionId, Item.WorldTransform, Cell, OutReason))
        {
            Rollback();
            return false;
        }
        Built.Add(Cell);
    }
    const auto Assign = [this, &OutReason](ALBBodyShopCellActor* Cell, const FName Slot,
        const ELBBodyShopRobotRole InRobotRole, const ELBBodyShopToolType InTool)
    {
        return Cell && AssignRobotToSlot(Cell->GetCellId(), Slot, InRobotRole, InTool, OutReason);
    };
    if (!Assign(Built[1], TEXT("ROBOT_HND_01"), ELBBodyShopRobotRole::PanelHandling,
            ELBBodyShopToolType::VacuumEightCup)
        || !Assign(Built[2], TEXT("ROBOT_WELD_LEFT"), ELBBodyShopRobotRole::SpotWelding,
            ELBBodyShopToolType::SpotCGun)
        || !Assign(Built[2], TEXT("ROBOT_WELD_RIGHT"), ELBBodyShopRobotRole::SpotWelding,
            ELBBodyShopToolType::SpotCGun))
    {
        Rollback();
        return false;
    }
    for (ALBBodyShopCellActor* Cell : Built)
    {
        if (!CommissionModule(Cell->GetCellId(), OutReason))
        {
            Rollback();
            return false;
        }
    }
    const FLBBodyShopPortAddress Links[][2] = {
        {{Built[0]->GetCellId(), LBBodyShopPrototypeIds::StillageOut}, {Built[1]->GetCellId(), LBBodyShopPrototypeIds::StillageIn}},
        {{Built[1]->GetCellId(), LBBodyShopPrototypeIds::PanelOut}, {Built[2]->GetCellId(), LBBodyShopPrototypeIds::PanelIn}},
        {{Built[2]->GetCellId(), LBBodyShopPrototypeIds::SkidOut}, {Built[3]->GetCellId(), LBBodyShopPrototypeIds::SkidIn}},
        {{Built[3]->GetCellId(), LBBodyShopPrototypeIds::SkidOut}, {Built[4]->GetCellId(), LBBodyShopPrototypeIds::BodyIn}},
        {{Built[4]->GetCellId(), LBBodyShopPrototypeIds::BodyOut}, {Built[5]->GetCellId(), LBBodyShopPrototypeIds::BodyIn}}
    };
    for (const auto& Link : Links)
    {
        FName ConnectionId;
        if (!Connect(Link[0], Link[1], ConnectionId, OutReason))
        {
            Rollback();
            return false;
        }
    }
    return true;
}
