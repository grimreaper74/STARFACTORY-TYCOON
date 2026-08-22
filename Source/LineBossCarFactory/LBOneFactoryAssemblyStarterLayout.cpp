#include "LBOneFactoryAssemblyStarterLayout.h"

#include "LBVehiclePanelCatalog.h"

namespace LBOneFactoryAssemblyStarterPrivate
{
    constexpr float TransformTolerance = 0.001f;
    constexpr float LayoutToleranceCm = 0.1f;
    constexpr float MaximumRouteLengthCm = 6500.0f;

    struct FStationContract
    {
        int32 LinePosition;
        ELBOneFactoryAssemblyOperation InitialOperation;
        TArray<ELBOneFactoryAssemblyCapability> Capabilities;
        float NominalCycleSeconds;
    };

    const TArray<FStationContract>& Contracts()
    {
        using C = ELBOneFactoryAssemblyCapability;
        using O = ELBOneFactoryAssemblyOperation;
        static const TArray<FStationContract> Result =
        {
            {1, O::PaintedBodyReceive, {C::MaterialHandling}, 24.0f},
            {2, O::DoorOff, {C::MaterialHandling, C::TrimInstall}, 32.0f},
            {3, O::MainWiringHarness, {C::ElectricalSoftware, C::TrimInstall}, 52.0f},
            {4, O::HVACModule, {C::TrimInstall, C::PrecisionTorque}, 48.0f},
            {5, O::InstrumentPanelCockpit, {C::HeavyLift, C::TrimInstall}, 58.0f},
            {6, O::InteriorTrim, {C::TrimInstall, C::PrecisionTorque}, 56.0f},
            {7, O::Glazing, {C::AdhesiveGlazing, C::MaterialHandling}, 46.0f},
            {8, O::Closures, {C::TrimInstall, C::PrecisionTorque}, 52.0f},
            {9, O::FrontRearCornerModules, {C::HeavyLift, C::PrecisionTorque}, 54.0f},
            {10, O::PowertrainPreparation, {C::Powertrain, C::HeavyLift}, 60.0f},
            {11, O::BatteryAndFuelSystem, {C::Powertrain, C::HeavyLift, C::ElectricalSoftware}, 62.0f},
            {12, O::PowertrainMarriage, {C::Powertrain, C::HeavyLift, C::PrecisionTorque}, 64.0f},
            {13, O::UnderbodyTorque, {C::Powertrain, C::PrecisionTorque}, 58.0f},
            {14, O::ExhaustAndThermal, {C::Powertrain, C::PrecisionTorque}, 52.0f},
            {15, O::Seats, {C::HeavyLift, C::TrimInstall}, 50.0f},
            {16, O::DoorRefit, {C::TrimInstall, C::PrecisionTorque}, 54.0f},
            {17, O::WheelsAndTires, {C::WheelTire, C::HeavyLift, C::PrecisionTorque}, 56.0f},
            {18, O::FluidsCharge, {C::Fluids, C::Inspection}, 48.0f},
            {19, O::SoftwareFlash, {C::ElectricalSoftware}, 45.0f},
            {20, O::ElectricalFunctionalTest, {C::ElectricalSoftware, C::Inspection}, 42.0f},
            {21, O::WheelAlignment, {C::WheelTire, C::DynamicTest}, 48.0f},
            {22, O::BrakeRollDyno, {C::DynamicTest, C::Inspection}, 52.0f},
            {23, O::FinalInspectionAndRework, {C::Inspection, C::Rework}, 60.0f},
            {24, O::FinishedVehicleDispatch, {C::Dispatch, C::MaterialHandling}, 24.0f}
        };
        return Result;
    }

    const FStationContract* FindContract(const int32 LinePosition)
    {
        return Contracts().FindByPredicate([LinePosition](
            const FStationContract& Contract)
        {
            return Contract.LinePosition == LinePosition;
        });
    }

    FBox AssemblyBayBounds()
    {
        const FLBOneFactoryLayoutDefinition Layout =
            ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
        const FLBOneFactoryDepartmentBay* Bay =
            Layout.DepartmentBays.FindByPredicate([](
                const FLBOneFactoryDepartmentBay& Candidate)
            {
                return Candidate.BayId == LBOneFactoryIds::AssemblyBay()
                    && Candidate.Department ==
                        ELBOneFactoryDepartment::Assembly;
            });
        return Bay ? Bay->GetWorldBounds() : FBox(ForceInit);
    }

    FBox StationBounds(const FLBOneFactoryAssemblyStationState& Station)
    {
        const FVector Half(Station.FootprintSizeCm.X * 0.5f,
            Station.FootprintSizeCm.Y * 0.5f, 0.0f);
        return FBox(FVector(-Half.X, -Half.Y, 0.0f),
            FVector(Half.X, Half.Y, Station.FootprintSizeCm.Z))
            .TransformBy(Station.WorldTransform);
    }

    bool IsTransformUsable(const FTransform& Transform)
    {
        const FRotator Rotation = Transform.Rotator();
        return Transform.IsValid() && !Transform.ContainsNaN()
            && Transform.GetScale3D().Equals(FVector::OneVector,
                TransformTolerance)
            && FMath::IsNearlyZero(Transform.GetLocation().Z,
                LayoutToleranceCm)
            && FMath::IsNearlyZero(Rotation.Roll, TransformTolerance)
            && FMath::IsNearlyZero(Rotation.Pitch, TransformTolerance);
    }

    bool IsFinitePositiveVector(const FVector& Value)
    {
        return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y)
            && FMath::IsFinite(Value.Z) && Value.X > 0.0f
            && Value.Y > 0.0f && Value.Z > 0.0f;
    }

    FLBOneFactoryAssemblyStationState* FindStation(
        FLBOneFactoryAssemblyLayoutState& State, const FName StationId)
    {
        return State.Stations.FindByPredicate([StationId](
            const FLBOneFactoryAssemblyStationState& Station)
        {
            return Station.StationId == StationId;
        });
    }

    const FLBOneFactoryAssemblyStationState* FindStation(
        const FLBOneFactoryAssemblyLayoutState& State, const FName StationId)
    {
        return State.Stations.FindByPredicate([StationId](
            const FLBOneFactoryAssemblyStationState& Station)
        {
            return Station.StationId == StationId;
        });
    }

    bool HasUniqueCapabilities(
        const TArray<ELBOneFactoryAssemblyCapability>& Capabilities)
    {
        TSet<ELBOneFactoryAssemblyCapability> Seen;
        for (const ELBOneFactoryAssemblyCapability Capability : Capabilities)
        {
            if (static_cast<uint8>(Capability)
                    > static_cast<uint8>(
                        ELBOneFactoryAssemblyCapability::Dispatch)
                || Seen.Contains(Capability))
            {
                return false;
            }
            Seen.Add(Capability);
        }
        return !Capabilities.IsEmpty();
    }

    FVector CanonicalLocation(const int32 LinePosition)
    {
        if (LinePosition <= 12)
        {
            return FVector(4000.0f + (LinePosition - 1) * 2200.0f,
                5500.0f, 0.0f);
        }
        return FVector(28200.0f - (LinePosition - 13) * 2200.0f,
            11500.0f, 0.0f);
    }
}

FName LBOneFactoryAssemblyStarterIds::Layout()
{
    static const FName Id(TEXT("MOORCROSS_ASSEMBLY_STARTER_NATIVE_V001"));
    return Id;
}

FName LBOneFactoryAssemblyStarterIds::Station(const int32 LinePosition)
{
    return LinePosition >= 1
            && LinePosition <=
                ULBOneFactoryAssemblyStarterLayoutLibrary::RequiredStationCount
        ? FName(*FString::Printf(TEXT("OF_ASSEMBLY_POS_%02d"), LinePosition))
        : NAME_None;
}

FName LBOneFactoryAssemblyStarterIds::Connection(
    const int32 SourceLinePosition)
{
    return SourceLinePosition >= 1
            && SourceLinePosition <=
                ULBOneFactoryAssemblyStarterLayoutLibrary::RequiredConnectionCount
        ? FName(*FString::Printf(TEXT("OF_ASSEMBLY_ROUTE_%02d_%02d"),
            SourceLinePosition, SourceLinePosition + 1))
        : NAME_None;
}

ELBOneFactoryAssemblyCapability
ULBOneFactoryAssemblyStarterLayoutLibrary::GetRequiredCapability(
    const ELBOneFactoryAssemblyOperation InOperation)
{
    using C = ELBOneFactoryAssemblyCapability;
    using O = ELBOneFactoryAssemblyOperation;
    switch (InOperation)
    {
    case O::PaintedBodyReceive: return C::MaterialHandling;
    case O::DoorOff: return C::TrimInstall;
    case O::MainWiringHarness: return C::ElectricalSoftware;
    case O::HVACModule: return C::TrimInstall;
    case O::InstrumentPanelCockpit: return C::HeavyLift;
    case O::InteriorTrim: return C::TrimInstall;
    case O::Glazing: return C::AdhesiveGlazing;
    case O::Closures: return C::PrecisionTorque;
    case O::FrontRearCornerModules: return C::HeavyLift;
    case O::PowertrainPreparation: return C::Powertrain;
    case O::BatteryAndFuelSystem: return C::Powertrain;
    case O::PowertrainMarriage: return C::HeavyLift;
    case O::UnderbodyTorque: return C::PrecisionTorque;
    case O::ExhaustAndThermal: return C::PrecisionTorque;
    case O::Seats: return C::HeavyLift;
    case O::DoorRefit: return C::PrecisionTorque;
    case O::WheelsAndTires: return C::WheelTire;
    case O::FluidsCharge: return C::Fluids;
    case O::SoftwareFlash: return C::ElectricalSoftware;
    case O::ElectricalFunctionalTest: return C::Inspection;
    case O::WheelAlignment: return C::WheelTire;
    case O::BrakeRollDyno: return C::DynamicTest;
    case O::FinalInspectionAndRework: return C::Rework;
    case O::FinishedVehicleDispatch: return C::Dispatch;
    default: return C::MaterialHandling;
    }
}

FString ULBOneFactoryAssemblyStarterLayoutLibrary::GetOperationDisplayName(
    const ELBOneFactoryAssemblyOperation InOperation)
{
    using O = ELBOneFactoryAssemblyOperation;
    switch (InOperation)
    {
    case O::PaintedBodyReceive: return TEXT("Painted body receive");
    case O::DoorOff: return TEXT("Door-off transfer");
    case O::MainWiringHarness: return TEXT("Main wiring harness");
    case O::HVACModule: return TEXT("HVAC module");
    case O::InstrumentPanelCockpit: return TEXT("Instrument-panel cockpit");
    case O::InteriorTrim: return TEXT("Interior trim");
    case O::Glazing: return TEXT("Glazing");
    case O::Closures: return TEXT("Closures");
    case O::FrontRearCornerModules: return TEXT("Front and rear corner modules");
    case O::PowertrainPreparation: return TEXT("Powertrain preparation");
    case O::BatteryAndFuelSystem: return TEXT("Battery and fuel system");
    case O::PowertrainMarriage: return TEXT("Powertrain marriage");
    case O::UnderbodyTorque: return TEXT("Underbody torque");
    case O::ExhaustAndThermal: return TEXT("Exhaust and thermal");
    case O::Seats: return TEXT("Seat installation");
    case O::DoorRefit: return TEXT("Door refit");
    case O::WheelsAndTires: return TEXT("Wheels and tires");
    case O::FluidsCharge: return TEXT("Fluids charge");
    case O::SoftwareFlash: return TEXT("Software flash");
    case O::ElectricalFunctionalTest: return TEXT("Electrical functional test");
    case O::WheelAlignment: return TEXT("Wheel alignment");
    case O::BrakeRollDyno: return TEXT("Brake and roll test");
    case O::FinalInspectionAndRework: return TEXT("Final inspection and rework");
    case O::FinishedVehicleDispatch: return TEXT("Finished vehicle dispatch");
    default: return TEXT("Unknown assembly operation");
    }
}

bool ULBOneFactoryAssemblyStarterLayoutLibrary::StationSupportsOperation(
    const FLBOneFactoryAssemblyStationState& Station,
    const ELBOneFactoryAssemblyOperation InOperation)
{
    return Station.Capabilities.Contains(GetRequiredCapability(InOperation));
}

FLBOneFactoryAssemblyLayoutState
ULBOneFactoryAssemblyStarterLayoutLibrary::MakeCanonicalStarterLayout()
{
    FLBOneFactoryAssemblyLayoutState State;
    State.LayoutId = LBOneFactoryAssemblyStarterIds::Layout();
    State.VehicleModelId = LBCairnwell2040PanelCatalog::GetVehicleModelId();
    State.InputState = ELBOneFactoryAssemblyMaterialState::PaintedBody;
    State.OutputState = ELBOneFactoryAssemblyMaterialState::FinishedVehicle;
    for (const LBOneFactoryAssemblyStarterPrivate::FStationContract& Contract :
        LBOneFactoryAssemblyStarterPrivate::Contracts())
    {
        FLBOneFactoryAssemblyStationState& Station =
            State.Stations.AddDefaulted_GetRef();
        Station.StationId =
            LBOneFactoryAssemblyStarterIds::Station(Contract.LinePosition);
        Station.LinePosition = Contract.LinePosition;
        Station.WorldTransform = FTransform(FRotator::ZeroRotator,
            LBOneFactoryAssemblyStarterPrivate::CanonicalLocation(
                Contract.LinePosition), FVector::OneVector);
        Station.FootprintSizeCm = FVector(1800.0f, 3300.0f, 450.0f);
        Station.Capabilities = Contract.Capabilities;
        Station.AssignedOperations = {Contract.InitialOperation};
        Station.NominalCycleSeconds = Contract.NominalCycleSeconds;
    }
    for (int32 Position = 1; Position <= RequiredConnectionCount; ++Position)
    {
        FLBOneFactoryAssemblyConnectionState& Connection =
            State.Connections.AddDefaulted_GetRef();
        Connection.ConnectionId =
            LBOneFactoryAssemblyStarterIds::Connection(Position);
        Connection.SourceStationId =
            LBOneFactoryAssemblyStarterIds::Station(Position);
        Connection.TargetStationId =
            LBOneFactoryAssemblyStarterIds::Station(Position + 1);
        Connection.MaximumRouteLengthCm =
            LBOneFactoryAssemblyStarterPrivate::MaximumRouteLengthCm;
    }
    return State;
}

bool ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
    const FLBOneFactoryAssemblyLayoutState& State, FString& OutReason)
{
    if (State.Version != 1
        || State.LayoutId != LBOneFactoryAssemblyStarterIds::Layout()
        || !LBVehicleModelCatalog::IsKnownModel(State.VehicleModelId)
        || State.Revision < 0
        || State.InputState != ELBOneFactoryAssemblyMaterialState::PaintedBody
        || State.OutputState !=
            ELBOneFactoryAssemblyMaterialState::FinishedVehicle
        || State.Stations.Num() != RequiredStationCount
        || State.Connections.Num() != RequiredConnectionCount)
    {
        OutReason = TEXT("ASSEMBLY LAYOUT IDENTITY, VERSION OR CARDINALITY IS INVALID");
        return false;
    }

    const FBox Bay = LBOneFactoryAssemblyStarterPrivate::AssemblyBayBounds();
    if (!Bay.IsValid)
    {
        OutReason = TEXT("ASSEMBLY BAY CONTRACT IS UNAVAILABLE");
        return false;
    }
    TSet<FName> StationIds;
    TSet<int32> Positions;
    TSet<FName> UnitIds;
    TMap<ELBOneFactoryAssemblyOperation, int32> OperationPositions;
    TArray<FBox> Envelopes;
    for (const FLBOneFactoryAssemblyStationState& Station : State.Stations)
    {
        const LBOneFactoryAssemblyStarterPrivate::FStationContract* Contract =
            LBOneFactoryAssemblyStarterPrivate::FindContract(
                Station.LinePosition);
        if (Station.Version != 1 || !Contract
            || Station.StationId
                != LBOneFactoryAssemblyStarterIds::Station(
                    Station.LinePosition)
            || StationIds.Contains(Station.StationId)
            || Positions.Contains(Station.LinePosition)
            || !LBOneFactoryAssemblyStarterPrivate::IsTransformUsable(
                Station.WorldTransform)
            || !LBOneFactoryAssemblyStarterPrivate::IsFinitePositiveVector(
                Station.FootprintSizeCm)
            || !FMath::IsFinite(Station.NominalCycleSeconds)
            || Station.NominalCycleSeconds <= 0.0f
            || Station.Capabilities != Contract->Capabilities
            || !LBOneFactoryAssemblyStarterPrivate::HasUniqueCapabilities(
                Station.Capabilities))
        {
            OutReason = FString::Printf(
                TEXT("ASSEMBLY STATION CONTRACT FAILED AT POSITION %d"),
                Station.LinePosition);
            return false;
        }
        StationIds.Add(Station.StationId);
        Positions.Add(Station.LinePosition);
        const FBox Envelope =
            LBOneFactoryAssemblyStarterPrivate::StationBounds(Station);
        if (!Bay.IsInsideOrOn(Envelope.Min) || !Bay.IsInsideOrOn(Envelope.Max))
        {
            OutReason = FString::Printf(TEXT("ASSEMBLY STATION %s LEFT ITS BAY"),
                *Station.StationId.ToString());
            return false;
        }
        for (const FBox& Existing : Envelopes)
        {
            if (Envelope.Intersect(Existing))
            {
                OutReason = FString::Printf(
                    TEXT("ASSEMBLY STATION %s OVERLAPS ANOTHER POSITION"),
                    *Station.StationId.ToString());
                return false;
            }
        }
        Envelopes.Add(Envelope);
        for (const FName UnitId : Station.ActiveOrReservedUnitIds)
        {
            if (UnitId.IsNone() || UnitIds.Contains(UnitId))
            {
                OutReason = TEXT("ASSEMBLY ACTIVE OR RESERVED UNIT IDS ARE INVALID OR DUPLICATED");
                return false;
            }
            UnitIds.Add(UnitId);
        }
        TSet<ELBOneFactoryAssemblyOperation> LocalOperations;
        for (const ELBOneFactoryAssemblyOperation Operation :
            Station.AssignedOperations)
        {
            if (static_cast<uint8>(Operation)
                    >= static_cast<uint8>(RequiredOperationCount)
                || LocalOperations.Contains(Operation)
                || OperationPositions.Contains(Operation)
                || !StationSupportsOperation(Station, Operation))
            {
                OutReason = FString::Printf(
                    TEXT("ASSEMBLY OPERATION ASSIGNMENT IS INVALID AT %s"),
                    *Station.StationId.ToString());
                return false;
            }
            LocalOperations.Add(Operation);
            OperationPositions.Add(Operation, Station.LinePosition);
        }
    }
    if (OperationPositions.Num() != RequiredOperationCount)
    {
        OutReason = TEXT("ASSEMBLY BILL OF PROCESS MUST CONTAIN ALL 24 OPERATIONS EXACTLY ONCE");
        return false;
    }
    int32 PreviousPosition = 0;
    for (int32 Index = 0; Index < RequiredOperationCount; ++Index)
    {
        const ELBOneFactoryAssemblyOperation Operation =
            static_cast<ELBOneFactoryAssemblyOperation>(Index);
        const int32* Position = OperationPositions.Find(Operation);
        if (!Position || *Position < PreviousPosition)
        {
            OutReason = TEXT("ASSEMBLY OPERATION ORDER WOULD BYPASS A REQUIRED PROCESS");
            return false;
        }
        PreviousPosition = *Position;
    }

    TSet<FName> ConnectionIds;
    for (int32 Index = 0; Index < State.Connections.Num(); ++Index)
    {
        const int32 SourcePosition = Index + 1;
        const FLBOneFactoryAssemblyConnectionState& Connection =
            State.Connections[Index];
        const FLBOneFactoryAssemblyStationState* Source =
            LBOneFactoryAssemblyStarterPrivate::FindStation(
                State, Connection.SourceStationId);
        const FLBOneFactoryAssemblyStationState* Target =
            LBOneFactoryAssemblyStarterPrivate::FindStation(
                State, Connection.TargetStationId);
        if (Connection.Version != 1
            || Connection.ConnectionId
                != LBOneFactoryAssemblyStarterIds::Connection(SourcePosition)
            || Connection.SourceStationId
                != LBOneFactoryAssemblyStarterIds::Station(SourcePosition)
            || Connection.TargetStationId
                != LBOneFactoryAssemblyStarterIds::Station(SourcePosition + 1)
            || ConnectionIds.Contains(Connection.ConnectionId)
            || !Source || !Target
            || !FMath::IsNearlyEqual(Connection.MaximumRouteLengthCm,
                LBOneFactoryAssemblyStarterPrivate::MaximumRouteLengthCm,
                LBOneFactoryAssemblyStarterPrivate::LayoutToleranceCm)
            || FVector::Dist2D(Source->WorldTransform.GetLocation(),
                Target->WorldTransform.GetLocation())
                > Connection.MaximumRouteLengthCm
                    + LBOneFactoryAssemblyStarterPrivate::LayoutToleranceCm)
        {
            OutReason = FString::Printf(
                TEXT("ASSEMBLY ROUTE CONTRACT FAILED AT LINK %d"),
                SourcePosition);
            return false;
        }
        ConnectionIds.Add(Connection.ConnectionId);
    }
    OutReason = State.bCommissioned
        ? TEXT("CONFIGURABLE 24-POSITION ASSEMBLY LINE IS COMMISSIONED")
        : TEXT("CONFIGURABLE 24-POSITION ASSEMBLY LINE IS VALID AND UNCOMMISSIONED");
    return true;
}

ALBOneFactoryAssemblyStarterLayoutAuthority::
ALBOneFactoryAssemblyStarterLayoutAuthority()
{
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    Tags.AddUnique(GetAuthorityTag());
    Tags.AddUnique(GetNativeOnlyTag());
    CurrentState =
        ULBOneFactoryAssemblyStarterLayoutLibrary::MakeCanonicalStarterLayout();
}

FName ALBOneFactoryAssemblyStarterLayoutAuthority::GetAuthorityTag()
{
    static const FName Tag(TEXT("LB.OneFactory.AssemblyStarter.Authority"));
    return Tag;
}

FName ALBOneFactoryAssemblyStarterLayoutAuthority::GetNativeOnlyTag()
{
    static const FName Tag(TEXT("LB.OneFactory.Provenance.NativeOnly"));
    return Tag;
}

bool ALBOneFactoryAssemblyStarterLayoutAuthority::HasActiveOrReservedWIP(
    const FLBOneFactoryAssemblyLayoutState& State)
{
    return State.Stations.ContainsByPredicate([](
        const FLBOneFactoryAssemblyStationState& Station)
    {
        return !Station.ActiveOrReservedUnitIds.IsEmpty();
    });
}

bool ALBOneFactoryAssemblyStarterLayoutAuthority::RestoreLayout(
    const FLBOneFactoryAssemblyLayoutState& State, FString& OutReason)
{
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            State, OutReason))
    {
        return false;
    }
    CurrentState = State;
    OutReason = TEXT("ASSEMBLY LAYOUT RESTORED AFTER COMPLETE PREFLIGHT");
    return true;
}

bool ALBOneFactoryAssemblyStarterLayoutAuthority::AssignOperation(
    const ELBOneFactoryAssemblyOperation InOperation,
    const FName TargetStationId, FString& OutReason)
{
    if (HasActiveOrReservedWIP(CurrentState))
    {
        OutReason = TEXT("ASSEMBLY ASSIGNMENT IS BLOCKED BY ACTIVE OR RESERVED WIP");
        return false;
    }
    FLBOneFactoryAssemblyLayoutState Candidate = CurrentState;
    FLBOneFactoryAssemblyStationState* Source = nullptr;
    FLBOneFactoryAssemblyStationState* Target =
        LBOneFactoryAssemblyStarterPrivate::FindStation(
            Candidate, TargetStationId);
    for (FLBOneFactoryAssemblyStationState& Station : Candidate.Stations)
    {
        if (Station.AssignedOperations.Contains(InOperation))
        {
            Source = &Station;
            break;
        }
    }
    if (!Source || !Target || Source == Target
        || !ULBOneFactoryAssemblyStarterLayoutLibrary::StationSupportsOperation(
            *Target, InOperation))
    {
        OutReason = TEXT("ASSEMBLY TARGET CANNOT ACCEPT THE REQUESTED OPERATION");
        return false;
    }
    Source->AssignedOperations.RemoveSingle(InOperation);
    Target->AssignedOperations.Add(InOperation);
    Target->AssignedOperations.Sort([](
        const ELBOneFactoryAssemblyOperation Left,
        const ELBOneFactoryAssemblyOperation Right)
    {
        return static_cast<uint8>(Left) < static_cast<uint8>(Right);
    });
    Candidate.bCommissioned = false;
    ++Candidate.Revision;
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, OutReason))
    {
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = TEXT("ASSEMBLY OPERATION REASSIGNED ATOMICALLY; RECOMMISSION REQUIRED");
    return true;
}

bool ALBOneFactoryAssemblyStarterLayoutAuthority::MoveStation(
    const FName StationId, const FTransform& WorldTransform,
    FString& OutReason)
{
    if (HasActiveOrReservedWIP(CurrentState))
    {
        OutReason = TEXT("ASSEMBLY MOVEMENT IS BLOCKED BY ACTIVE OR RESERVED WIP");
        return false;
    }
    FLBOneFactoryAssemblyLayoutState Candidate = CurrentState;
    FLBOneFactoryAssemblyStationState* Station =
        LBOneFactoryAssemblyStarterPrivate::FindStation(Candidate, StationId);
    if (!Station
        || !LBOneFactoryAssemblyStarterPrivate::IsTransformUsable(
            WorldTransform))
    {
        OutReason = TEXT("ASSEMBLY MOVE TARGET OR TRANSFORM IS INVALID");
        return false;
    }
    Station->WorldTransform = WorldTransform;
    Candidate.bCommissioned = false;
    ++Candidate.Revision;
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, OutReason))
    {
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = TEXT("ASSEMBLY POSITION MOVED ATOMICALLY; RECOMMISSION REQUIRED");
    return true;
}

bool ALBOneFactoryAssemblyStarterLayoutAuthority::Commission(FString& OutReason)
{
    if (CurrentState.bCommissioned)
    {
        OutReason = TEXT("ASSEMBLY LINE IS ALREADY COMMISSIONED");
        return false;
    }
    if (HasActiveOrReservedWIP(CurrentState)
        || !ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            CurrentState, OutReason))
    {
        if (HasActiveOrReservedWIP(CurrentState))
            OutReason = TEXT("ASSEMBLY COMMISSION IS BLOCKED BY ACTIVE OR RESERVED WIP");
        return false;
    }
    FLBOneFactoryAssemblyLayoutState Candidate = CurrentState;
    Candidate.bCommissioned = true;
    ++Candidate.Revision;
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, OutReason))
    {
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = TEXT("CONFIGURABLE 24-POSITION ASSEMBLY LINE COMMISSIONED");
    return true;
}
