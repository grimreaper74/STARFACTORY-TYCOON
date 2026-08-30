#include "LBBodyShopUnderbodyExpansionV2.h"

#include "LBBodyShopUnderbodyProcess.h"

const FName LBBodyShopUnderbodyExpansionStationIdsV2::ComponentKitPresentation(
    TEXT("BWU000_COMPONENT_KIT_PRESENTATION_V001"));
const FName LBBodyShopUnderbodyExpansionStationIdsV2::RailCrossmemberPreparation(
    TEXT("BWU001_RAIL_CROSSMEMBER_PREP_V001"));
const FName LBBodyShopUnderbodyExpansionStationIdsV2::MainUnderbodyJoining(
    TEXT("BWU002_MAIN_UNDERBODY_JOIN_V001"));
const FName LBBodyShopUnderbodyExpansionStationIdsV2::SideSillRockerJoining(
    TEXT("BWU003_SIDE_SILL_ROCKER_JOIN_V001"));
const FName LBBodyShopUnderbodyExpansionStationIdsV2::DeburrFinish(
    TEXT("BWU004_DEBURR_FINISH_V001"));
const FName LBBodyShopUnderbodyExpansionStationIdsV2::UnderbodyInspection(
    TEXT("BWU005_UNDERBODY_INSPECTION_V001"));
const FName LBBodyShopUnderbodyExpansionStationIdsV2::UnderbodyRework(
    TEXT("BWU006_UNDERBODY_REWORK_V001"));
const FName LBBodyShopUnderbodyExpansionStationIdsV2::PassBuffer(
    TEXT("BWU007_PASS_BUFFER_V001"));

const FName LBBodyShopUnderbodyExpansionMaterialIdsV2::RawPrimaryKit(
    TEXT("UBW_PRIMARY_KIT_RAW"));
const FName LBBodyShopUnderbodyExpansionMaterialIdsV2::PresentedPrimaryKit(
    TEXT("UBW_PRIMARY_KIT_PRESENTED"));
const FName LBBodyShopUnderbodyExpansionMaterialIdsV2::PreparedPrimaryStructure(
    TEXT("UBW_PRIMARY_STRUCTURE_PREPARED"));
const FName LBBodyShopUnderbodyExpansionMaterialIdsV2::PrimaryStructureJoined(
    TEXT("UBW_PRIMARY_STRUCTURE_JOINED"));
const FName LBBodyShopUnderbodyExpansionMaterialIdsV2::SideSillKit(
    TEXT("UBW_SIDE_SILL_KIT"));
const FName LBBodyShopUnderbodyExpansionMaterialIdsV2::SideSillsJoined(
    TEXT("UBW_SIDE_SILLS_JOINED"));
const FName LBBodyShopUnderbodyExpansionMaterialIdsV2::FinishChecked(
    TEXT("UBW_FINISH_CHECKED"));
const FName LBBodyShopUnderbodyExpansionMaterialIdsV2::ReworkHold(
    TEXT("UBW_REWORK_HOLD"));
const FName LBBodyShopUnderbodyExpansionMaterialIdsV2::ReinspectReady(
    TEXT("UBW_REINSPECT_READY"));

const FName LBBodyShopUnderbodyExpansionPortIdsV2::PrimaryKitIn(TEXT("PRIMARY_KIT_IN"));
const FName LBBodyShopUnderbodyExpansionPortIdsV2::BodyIn(TEXT("BODY_IN"));
const FName LBBodyShopUnderbodyExpansionPortIdsV2::BodyOut(TEXT("BODY_OUT"));
const FName LBBodyShopUnderbodyExpansionPortIdsV2::SideSillKitIn(TEXT("SILL_KIT_IN"));
const FName LBBodyShopUnderbodyExpansionPortIdsV2::PassOut(TEXT("PASS_OUT"));
const FName LBBodyShopUnderbodyExpansionPortIdsV2::ReworkOut(TEXT("REWORK_OUT"));
const FName LBBodyShopUnderbodyExpansionPortIdsV2::ReworkIn(TEXT("REWORK_IN"));
const FName LBBodyShopUnderbodyExpansionPortIdsV2::ReinspectOut(TEXT("REINSPECT_OUT"));
const FName LBBodyShopUnderbodyExpansionPortIdsV2::ReinspectIn(TEXT("REINSPECT_IN"));

const FName LBBodyShopUnderbodyExpansionConnectionIdsV2::KitToPreparation(
    TEXT("BWU_CONN_001"));
const FName LBBodyShopUnderbodyExpansionConnectionIdsV2::PreparationToMainJoin(
    TEXT("BWU_CONN_002"));
const FName LBBodyShopUnderbodyExpansionConnectionIdsV2::MainJoinToSideJoin(
    TEXT("BWU_CONN_003"));
const FName LBBodyShopUnderbodyExpansionConnectionIdsV2::SideJoinToFinish(
    TEXT("BWU_CONN_004"));
const FName LBBodyShopUnderbodyExpansionConnectionIdsV2::FinishToInspection(
    TEXT("BWU_CONN_005"));
const FName LBBodyShopUnderbodyExpansionConnectionIdsV2::InspectionToPassBuffer(
    TEXT("BWU_CONN_006"));
const FName LBBodyShopUnderbodyExpansionConnectionIdsV2::InspectionToRework(
    TEXT("BWU_CONN_007"));
const FName LBBodyShopUnderbodyExpansionConnectionIdsV2::ReworkToReinspection(
    TEXT("BWU_CONN_008"));

namespace LBBodyShopUnderbodyExpansionV2Private
{
    FLBBodyShopUnderbodyExpansionPortV2 Port(const FName PortId,
        const ELBBodyShopPortDirection Direction, const FName MaterialId,
        const FVector& Location, const FRotator& Rotation = FRotator::ZeroRotator,
        const ELBBodyShopTransportType Transport = ELBBodyShopTransportType::SkidConveyor)
    {
        FLBBodyShopUnderbodyExpansionPortV2 Result;
        Result.PortId = PortId;
        Result.Direction = Direction;
        Result.Transport = Transport;
        Result.MaterialId = MaterialId;
        Result.LocalTransform = FTransform(Rotation, Location);
        return Result;
    }

    FLBBodyShopUnderbodyExpansionStationV2 Station(const FName StationId,
        const ELBBodyShopUnderbodyArchitecture Architecture,
        const ELBBodyShopUnderbodyExpansionStageV2 Stage, const TCHAR* DisplayName,
        const FVector& Footprint, const FVector& MaintenanceEnvelope,
        const float CycleSeconds, const FName ProcessStepId)
    {
        FLBBodyShopUnderbodyExpansionStationV2 Result;
        Result.StationId = StationId;
        Result.Architecture = Architecture;
        Result.Stage = Stage;
        Result.DisplayName = FText::FromString(DisplayName);
        Result.FootprintCm = Footprint;
        Result.MaintenanceEnvelopeCm = MaintenanceEnvelope;
        Result.CycleSeconds = CycleSeconds;
        Result.ProcessStepIds = {ProcessStepId};
        return Result;
    }

    TArray<FName> StableProcessStepIds()
    {
        return FLBBodyShopUnderbodyProcessRegistry::GetStableProcessStepIds();
    }

    bool IsKnownArchitecture(const ELBBodyShopUnderbodyArchitecture Architecture)
    {
        return Architecture == ELBBodyShopUnderbodyArchitecture::CentreTunnel
            || Architecture == ELBBodyShopUnderbodyArchitecture::EVBatteryTray;
    }

    bool IsKnownDirection(const ELBBodyShopPortDirection Direction)
    {
        return Direction == ELBBodyShopPortDirection::Input
            || Direction == ELBBodyShopPortDirection::Output;
    }

    bool IsKnownTransport(const ELBBodyShopTransportType Transport)
    {
        return Transport == ELBBodyShopTransportType::StillageFLT
            || Transport == ELBBodyShopTransportType::RobotHandoff
            || Transport == ELBBodyShopTransportType::SkidConveyor;
    }

    bool IsFiniteUnitTransform(const FTransform& Transform)
    {
        const FVector Location = Transform.GetLocation();
        const FVector Scale = Transform.GetScale3D();
        const FQuat Rotation = Transform.GetRotation();
        return !Location.ContainsNaN() && !Scale.ContainsNaN() && !Rotation.ContainsNaN()
            && Rotation.IsNormalized() && Scale.Equals(FVector::OneVector, 0.001f);
    }

    bool IsUniqueKnownNames(const TArray<FName>& Values, const TArray<FName>& Known)
    {
        TSet<FName> Seen;
        for (const FName Value : Values)
        {
            if (Value.IsNone() || Seen.Contains(Value) || !Known.Contains(Value)) return false;
            Seen.Add(Value);
        }
        return true;
    }

    TArray<FLBBodyShopUnderbodyExpansionStationV2> BuildCanonicalStations(
        const ELBBodyShopUnderbodyArchitecture Architecture)
    {
        using namespace LBBodyShopUnderbodyComponentIds;
        using namespace LBBodyShopUnderbodyExpansionMaterialIdsV2;
        using namespace LBBodyShopUnderbodyExpansionPortIdsV2;
        using namespace LBBodyShopUnderbodyExpansionStationIdsV2;
        using namespace LBBodyShopUnderbodyProcessStepIds;

        if (!IsKnownArchitecture(Architecture)) return {};

        const FName CentreStructure =
            Architecture == ELBBodyShopUnderbodyArchitecture::EVBatteryTray
            ? EVBatteryTray : CentreTunnel;
        const TArray<FName> PrimaryKitComponents = {FloorPan, CentreStructure,
            LongitudinalRailLeft, LongitudinalRailRight, Crossmembers,
            FrontFloorPartition, RearFloorPartition};

        TArray<FLBBodyShopUnderbodyExpansionStationV2> Result;

        FLBBodyShopUnderbodyExpansionStationV2 Kit = Station(ComponentKitPresentation,
            Architecture,
            ELBBodyShopUnderbodyExpansionStageV2::ComponentKitPresentation,
            TEXT("Underbody component-kit presentation"), FVector(1000.0f, 800.0f, 420.0f),
            FVector(1200.0f, 1000.0f, 500.0f), 4.0f, PresentComponentKit);
        // Side sills have their own later material input and are deliberately not
        // owned by this primary-kit material state.
        Kit.ComponentIds = PrimaryKitComponents;
        Kit.Ports = {
            Port(PrimaryKitIn, ELBBodyShopPortDirection::Input, RawPrimaryKit,
                FVector(-500.0f, 0.0f, 35.0f), FRotator(0.0f, 180.0f, 0.0f)),
            Port(BodyOut, ELBBodyShopPortDirection::Output, PresentedPrimaryKit,
                FVector(500.0f, 0.0f, 35.0f))
        };
        Result.Add(Kit);

        FLBBodyShopUnderbodyExpansionStationV2 Preparation = Station(
            RailCrossmemberPreparation,
            Architecture,
            ELBBodyShopUnderbodyExpansionStageV2::RailCrossmemberPreparation,
            TEXT("Rail and crossmember preparation"), FVector(1200.0f, 800.0f, 420.0f),
            FVector(1400.0f, 1000.0f, 500.0f), 6.0f, LocateInFixture);
        Preparation.ComponentIds = {LongitudinalRailLeft, LongitudinalRailRight, Crossmembers};
        Preparation.Ports = {
            Port(BodyIn, ELBBodyShopPortDirection::Input, PresentedPrimaryKit,
                FVector(-600.0f, 0.0f, 35.0f), FRotator(0.0f, 180.0f, 0.0f)),
            Port(BodyOut, ELBBodyShopPortDirection::Output, PreparedPrimaryStructure,
                FVector(600.0f, 0.0f, 35.0f))
        };
        Result.Add(Preparation);

        FLBBodyShopUnderbodyExpansionStationV2 MainJoin = Station(MainUnderbodyJoining,
            Architecture,
            ELBBodyShopUnderbodyExpansionStageV2::MainUnderbodyJoining,
            TEXT("Main underbody geometry and joining"), FVector(1200.0f, 1000.0f, 500.0f),
            FVector(1400.0f, 1200.0f, 600.0f), 12.0f, JoinPrimaryStructure);
        // Front and rear partitions are joined here, rather than merely being
        // counted at presentation and then orphaned from the process.
        MainJoin.ComponentIds = PrimaryKitComponents;
        MainJoin.JoinOperationIds = {LBBodyShopUnderbodyJoinOperationIds::ResistanceSpotWeld};
        MainJoin.Ports = {
            Port(BodyIn, ELBBodyShopPortDirection::Input, PreparedPrimaryStructure,
                FVector(-600.0f, 0.0f, 35.0f), FRotator(0.0f, 180.0f, 0.0f)),
            Port(BodyOut, ELBBodyShopPortDirection::Output, PrimaryStructureJoined,
                FVector(600.0f, 0.0f, 35.0f))
        };
        Result.Add(MainJoin);

        FLBBodyShopUnderbodyExpansionStationV2 SideJoin = Station(SideSillRockerJoining,
            Architecture,
            ELBBodyShopUnderbodyExpansionStageV2::SideSillRockerJoining,
            TEXT("Side-sill and rocker joining"), FVector(1200.0f, 1000.0f, 500.0f),
            FVector(1400.0f, 1200.0f, 600.0f), 10.0f, JoinPrimaryStructure);
        SideJoin.ComponentIds = {SideSillLeft, SideSillRight};
        SideJoin.JoinOperationIds = {LBBodyShopUnderbodyJoinOperationIds::ResistanceSpotWeld,
            LBBodyShopUnderbodyJoinOperationIds::AdhesiveBond};
        SideJoin.Ports = {
            Port(BodyIn, ELBBodyShopPortDirection::Input, PrimaryStructureJoined,
                FVector(-600.0f, 0.0f, 35.0f), FRotator(0.0f, 180.0f, 0.0f)),
            Port(SideSillKitIn, ELBBodyShopPortDirection::Input, SideSillKit,
                FVector(0.0f, 500.0f, 80.0f), FRotator(0.0f, 90.0f, 0.0f),
                ELBBodyShopTransportType::RobotHandoff),
            Port(BodyOut, ELBBodyShopPortDirection::Output, SideSillsJoined,
                FVector(600.0f, 0.0f, 35.0f))
        };
        Result.Add(SideJoin);

        FLBBodyShopUnderbodyExpansionStationV2 Finish = Station(DeburrFinish,
            Architecture,
            ELBBodyShopUnderbodyExpansionStageV2::DeburrFinish,
            TEXT("Deburr and finish"), FVector(800.0f, 800.0f, 420.0f),
            FVector(1000.0f, 1000.0f, 500.0f), 5.0f, DeburrAndFinishCheck);
        Finish.QualityCheckIds = {LBBodyShopUnderbodyQualityCheckIds::DeburrAndFinish};
        Finish.Ports = {
            Port(BodyIn, ELBBodyShopPortDirection::Input, SideSillsJoined,
                FVector(-400.0f, 0.0f, 35.0f), FRotator(0.0f, 180.0f, 0.0f)),
            Port(BodyOut, ELBBodyShopPortDirection::Output, FinishChecked,
                FVector(400.0f, 0.0f, 35.0f))
        };
        Result.Add(Finish);

        FLBBodyShopUnderbodyExpansionStationV2 Inspection = Station(UnderbodyInspection,
            Architecture,
            ELBBodyShopUnderbodyExpansionStageV2::UnderbodyInspection,
            TEXT("Dimensional and weld-integrity inspection"), FVector(800.0f, 800.0f, 500.0f),
            FVector(1000.0f, 1000.0f, 600.0f), 5.0f, DimensionalCheck);
        Inspection.ProcessStepIds.Add(WeldIntegrityCheck);
        Inspection.QualityCheckIds = {LBBodyShopUnderbodyQualityCheckIds::DimensionalAlignment,
            LBBodyShopUnderbodyQualityCheckIds::WeldIntegrity};
        Inspection.Ports = {
            Port(BodyIn, ELBBodyShopPortDirection::Input, FinishChecked,
                FVector(-400.0f, 0.0f, 35.0f), FRotator(0.0f, 180.0f, 0.0f)),
            Port(ReinspectIn, ELBBodyShopPortDirection::Input, ReinspectReady,
                FVector(200.0f, -400.0f, 35.0f), FRotator(0.0f, -90.0f, 0.0f)),
            Port(PassOut, ELBBodyShopPortDirection::Output, LBBodyShopMaterialIds::Underbody,
                FVector(400.0f, 0.0f, 35.0f)),
            Port(ReworkOut, ELBBodyShopPortDirection::Output, ReworkHold,
                FVector(-200.0f, -400.0f, 35.0f), FRotator(0.0f, -90.0f, 0.0f))
        };
        Result.Add(Inspection);

        FLBBodyShopUnderbodyExpansionStationV2 Rework = Station(UnderbodyRework,
            Architecture,
            ELBBodyShopUnderbodyExpansionStageV2::UnderbodyRework,
            TEXT("Underbody rework"), FVector(800.0f, 800.0f, 500.0f),
            FVector(1000.0f, 1000.0f, 600.0f), 8.0f, JoinPrimaryStructure);
        Rework.ProcessStepIds.Add(DeburrAndFinishCheck);
        Rework.JoinOperationIds = {LBBodyShopUnderbodyJoinOperationIds::ResistanceSpotWeld};
        Rework.QualityCheckIds = {LBBodyShopUnderbodyQualityCheckIds::DeburrAndFinish};
        Rework.Ports = {
            Port(ReworkIn, ELBBodyShopPortDirection::Input, ReworkHold,
                FVector(-200.0f, 400.0f, 35.0f), FRotator(0.0f, 90.0f, 0.0f)),
            Port(ReinspectOut, ELBBodyShopPortDirection::Output, ReinspectReady,
                FVector(200.0f, 400.0f, 35.0f), FRotator(0.0f, 90.0f, 0.0f))
        };
        Result.Add(Rework);

        FLBBodyShopUnderbodyExpansionStationV2 Buffer = Station(PassBuffer,
            Architecture,
            ELBBodyShopUnderbodyExpansionStageV2::PassBuffer,
            TEXT("Passed underbody buffer"), FVector(1000.0f, 800.0f, 300.0f),
            FVector(1200.0f, 1000.0f, 400.0f), 1.0f, TransferOnSkid);
        Buffer.ProcessStepIds.Add(ReleaseUnderbody);
        Buffer.Ports = {
            Port(BodyIn, ELBBodyShopPortDirection::Input, LBBodyShopMaterialIds::Underbody,
                FVector(-500.0f, 0.0f, 35.0f), FRotator(0.0f, 180.0f, 0.0f))
        };
        Result.Add(Buffer);

        return Result;
    }

    const TArray<FLBBodyShopUnderbodyExpansionStationV2>& CanonicalStations(
        const ELBBodyShopUnderbodyArchitecture Architecture)
    {
        static const TArray<FLBBodyShopUnderbodyExpansionStationV2> TunnelStations =
            BuildCanonicalStations(ELBBodyShopUnderbodyArchitecture::CentreTunnel);
        static const TArray<FLBBodyShopUnderbodyExpansionStationV2> EVStations =
            BuildCanonicalStations(ELBBodyShopUnderbodyArchitecture::EVBatteryTray);
        static const TArray<FLBBodyShopUnderbodyExpansionStationV2> Empty;
        if (Architecture == ELBBodyShopUnderbodyArchitecture::CentreTunnel)
            return TunnelStations;
        if (Architecture == ELBBodyShopUnderbodyArchitecture::EVBatteryTray)
            return EVStations;
        return Empty;
    }

    const FLBBodyShopUnderbodyExpansionPortV2* FindPort(
        const FLBBodyShopUnderbodyExpansionStationV2& Station, const FName PortId)
    {
        return Station.Ports.FindByPredicate([PortId](
            const FLBBodyShopUnderbodyExpansionPortV2& Candidate)
        {
            return Candidate.PortId == PortId;
        });
    }

    const FLBBodyShopUnderbodyExpansionLayoutItemV2* FindLayout(
        const TArray<FLBBodyShopUnderbodyExpansionLayoutItemV2>& Layout, const FName StationId)
    {
        return Layout.FindByPredicate([StationId](
            const FLBBodyShopUnderbodyExpansionLayoutItemV2& Candidate)
        {
            return Candidate.StationId == StationId;
        });
    }

    const FLBBodyShopUnderbodyExpansionStationV2* FindStation(
        const TArray<FLBBodyShopUnderbodyExpansionStationV2>& Stations,
        const FName StationId)
    {
        return Stations.FindByPredicate([StationId](
            const FLBBodyShopUnderbodyExpansionStationV2& Candidate)
        {
            return Candidate.StationId == StationId;
        });
    }

    bool PortsMatch(const FLBBodyShopUnderbodyExpansionPortV2& Actual,
        const FLBBodyShopUnderbodyExpansionPortV2& Expected)
    {
        return Actual.PortId == Expected.PortId
            && Actual.Direction == Expected.Direction
            && Actual.Transport == Expected.Transport
            && Actual.MaterialId == Expected.MaterialId
            && Actual.LocalTransform.Equals(Expected.LocalTransform, 0.01f);
    }

    bool StationsMatch(const FLBBodyShopUnderbodyExpansionStationV2& Actual,
        const FLBBodyShopUnderbodyExpansionStationV2& Expected)
    {
        if (Actual.ContractVersion != Expected.ContractVersion
            || Actual.StationId != Expected.StationId
            || Actual.Architecture != Expected.Architecture
            || Actual.Stage != Expected.Stage
            || Actual.DisplayName.ToString() != Expected.DisplayName.ToString()
            || !Actual.FootprintCm.Equals(Expected.FootprintCm, 0.01f)
            || !Actual.MaintenanceEnvelopeCm.Equals(Expected.MaintenanceEnvelopeCm, 0.01f)
            || !FMath::IsNearlyEqual(Actual.CycleSeconds, Expected.CycleSeconds, 0.001f)
            || Actual.ProcessStepIds != Expected.ProcessStepIds
            || Actual.ComponentIds != Expected.ComponentIds
            || Actual.JoinOperationIds != Expected.JoinOperationIds
            || Actual.QualityCheckIds != Expected.QualityCheckIds
            || Actual.Ports.Num() != Expected.Ports.Num())
        {
            return false;
        }
        for (int32 Index = 0; Index < Actual.Ports.Num(); ++Index)
        {
            if (!PortsMatch(Actual.Ports[Index], Expected.Ports[Index])) return false;
        }
        return true;
    }

    bool LayoutItemsMatch(const FLBBodyShopUnderbodyExpansionLayoutItemV2& Actual,
        const FLBBodyShopUnderbodyExpansionLayoutItemV2& Expected)
    {
        return Actual.StationId == Expected.StationId
            && Actual.WorldTransform.Equals(Expected.WorldTransform, 0.01f);
    }

    bool ConnectionsMatch(const FLBBodyShopUnderbodyExpansionConnectionV2& Actual,
        const FLBBodyShopUnderbodyExpansionConnectionV2& Expected)
    {
        return Actual.ConnectionId == Expected.ConnectionId
            && Actual.Source.StationId == Expected.Source.StationId
            && Actual.Source.PortId == Expected.Source.PortId
            && Actual.Target.StationId == Expected.Target.StationId
            && Actual.Target.PortId == Expected.Target.PortId;
    }

    bool AreFullyOpposed(const FTransform& SourceWorld, const FTransform& TargetWorld)
    {
        if (FVector::Dist(SourceWorld.GetLocation(), TargetWorld.GetLocation()) > 0.01f)
            return false;
        const FVector SourceForward = SourceWorld.GetUnitAxis(EAxis::X);
        const FVector TargetForward = TargetWorld.GetUnitAxis(EAxis::X);
        const FVector SourceRight = SourceWorld.GetUnitAxis(EAxis::Y);
        const FVector TargetRight = TargetWorld.GetUnitAxis(EAxis::Y);
        const FVector SourceUp = SourceWorld.GetUnitAxis(EAxis::Z);
        const FVector TargetUp = TargetWorld.GetUnitAxis(EAxis::Z);
        return FMath::IsNearlyEqual(FVector::DotProduct(SourceForward, TargetForward), -1.0f,
                0.0001f)
            && FMath::IsNearlyEqual(FVector::DotProduct(SourceRight, TargetRight), -1.0f,
                0.0001f)
            && FMath::IsNearlyEqual(FVector::DotProduct(SourceUp, TargetUp), 1.0f,
                0.0001f);
    }
}

TArray<FName> FLBBodyShopUnderbodyExpansionRegistryV2::GetStableStationIds()
{
    return {
        LBBodyShopUnderbodyExpansionStationIdsV2::ComponentKitPresentation,
        LBBodyShopUnderbodyExpansionStationIdsV2::RailCrossmemberPreparation,
        LBBodyShopUnderbodyExpansionStationIdsV2::MainUnderbodyJoining,
        LBBodyShopUnderbodyExpansionStationIdsV2::SideSillRockerJoining,
        LBBodyShopUnderbodyExpansionStationIdsV2::DeburrFinish,
        LBBodyShopUnderbodyExpansionStationIdsV2::UnderbodyInspection,
        LBBodyShopUnderbodyExpansionStationIdsV2::UnderbodyRework,
        LBBodyShopUnderbodyExpansionStationIdsV2::PassBuffer
    };
}

TArray<FName> FLBBodyShopUnderbodyExpansionRegistryV2::GetStableMaterialIds()
{
    return {
        LBBodyShopUnderbodyExpansionMaterialIdsV2::RawPrimaryKit,
        LBBodyShopUnderbodyExpansionMaterialIdsV2::PresentedPrimaryKit,
        LBBodyShopUnderbodyExpansionMaterialIdsV2::PreparedPrimaryStructure,
        LBBodyShopUnderbodyExpansionMaterialIdsV2::PrimaryStructureJoined,
        LBBodyShopUnderbodyExpansionMaterialIdsV2::SideSillKit,
        LBBodyShopUnderbodyExpansionMaterialIdsV2::SideSillsJoined,
        LBBodyShopUnderbodyExpansionMaterialIdsV2::FinishChecked,
        LBBodyShopUnderbodyExpansionMaterialIdsV2::ReworkHold,
        LBBodyShopUnderbodyExpansionMaterialIdsV2::ReinspectReady,
        LBBodyShopMaterialIds::Underbody
    };
}

TArray<FName> FLBBodyShopUnderbodyExpansionRegistryV2::GetStablePortIds()
{
    return {
        LBBodyShopUnderbodyExpansionPortIdsV2::PrimaryKitIn,
        LBBodyShopUnderbodyExpansionPortIdsV2::BodyIn,
        LBBodyShopUnderbodyExpansionPortIdsV2::BodyOut,
        LBBodyShopUnderbodyExpansionPortIdsV2::SideSillKitIn,
        LBBodyShopUnderbodyExpansionPortIdsV2::PassOut,
        LBBodyShopUnderbodyExpansionPortIdsV2::ReworkOut,
        LBBodyShopUnderbodyExpansionPortIdsV2::ReworkIn,
        LBBodyShopUnderbodyExpansionPortIdsV2::ReinspectOut,
        LBBodyShopUnderbodyExpansionPortIdsV2::ReinspectIn
    };
}

TArray<FName> FLBBodyShopUnderbodyExpansionRegistryV2::GetStableConnectionIds()
{
    return {
        LBBodyShopUnderbodyExpansionConnectionIdsV2::KitToPreparation,
        LBBodyShopUnderbodyExpansionConnectionIdsV2::PreparationToMainJoin,
        LBBodyShopUnderbodyExpansionConnectionIdsV2::MainJoinToSideJoin,
        LBBodyShopUnderbodyExpansionConnectionIdsV2::SideJoinToFinish,
        LBBodyShopUnderbodyExpansionConnectionIdsV2::FinishToInspection,
        LBBodyShopUnderbodyExpansionConnectionIdsV2::InspectionToPassBuffer,
        LBBodyShopUnderbodyExpansionConnectionIdsV2::InspectionToRework,
        LBBodyShopUnderbodyExpansionConnectionIdsV2::ReworkToReinspection
    };
}

TArray<FLBBodyShopUnderbodyExpansionStationV2>
FLBBodyShopUnderbodyExpansionRegistryV2::GetCanonicalStations(
    const ELBBodyShopUnderbodyArchitecture Architecture)
{
    return LBBodyShopUnderbodyExpansionV2Private::CanonicalStations(Architecture);
}

bool FLBBodyShopUnderbodyExpansionRegistryV2::FindCanonicalStation(
    const FName StationId, FLBBodyShopUnderbodyExpansionStationV2& OutStation,
    const ELBBodyShopUnderbodyArchitecture Architecture)
{
    const FLBBodyShopUnderbodyExpansionStationV2* Found =
        LBBodyShopUnderbodyExpansionV2Private::CanonicalStations(Architecture).FindByPredicate(
            [StationId](const FLBBodyShopUnderbodyExpansionStationV2& Candidate)
            {
                return Candidate.StationId == StationId;
            });
    if (!Found) return false;
    OutStation = *Found;
    return true;
}

TArray<FLBBodyShopUnderbodyExpansionLayoutItemV2>
FLBBodyShopUnderbodyExpansionRegistryV2::GetApprovedLayout()
{
    const auto Item = [](const FName StationId, const FVector& Location)
    {
        FLBBodyShopUnderbodyExpansionLayoutItemV2 Result;
        Result.StationId = StationId;
        Result.WorldTransform = FTransform(Location);
        return Result;
    };
    using namespace LBBodyShopUnderbodyExpansionStationIdsV2;
    return {
        Item(ComponentKitPresentation, FVector(-1100.0f, 0.0f, 0.0f)),
        Item(RailCrossmemberPreparation, FVector(0.0f, 0.0f, 0.0f)),
        Item(MainUnderbodyJoining, FVector(1200.0f, 0.0f, 0.0f)),
        Item(SideSillRockerJoining, FVector(2400.0f, 0.0f, 0.0f)),
        Item(DeburrFinish, FVector(3400.0f, 0.0f, 0.0f)),
        Item(UnderbodyInspection, FVector(4200.0f, 0.0f, 0.0f)),
        Item(UnderbodyRework, FVector(4200.0f, -800.0f, 0.0f)),
        Item(PassBuffer, FVector(5100.0f, 0.0f, 0.0f))
    };
}

TArray<FLBBodyShopUnderbodyExpansionConnectionV2>
FLBBodyShopUnderbodyExpansionRegistryV2::GetApprovedConnections()
{
    const auto Link = [](const FName Id, const FName SourceStation, const FName SourcePort,
        const FName TargetStation, const FName TargetPort)
    {
        FLBBodyShopUnderbodyExpansionConnectionV2 Result;
        Result.ConnectionId = Id;
        Result.Source.StationId = SourceStation;
        Result.Source.PortId = SourcePort;
        Result.Target.StationId = TargetStation;
        Result.Target.PortId = TargetPort;
        return Result;
    };
    using namespace LBBodyShopUnderbodyExpansionConnectionIdsV2;
    using namespace LBBodyShopUnderbodyExpansionPortIdsV2;
    using namespace LBBodyShopUnderbodyExpansionStationIdsV2;
    return {
        Link(KitToPreparation, ComponentKitPresentation, BodyOut,
            RailCrossmemberPreparation, BodyIn),
        Link(PreparationToMainJoin, RailCrossmemberPreparation, BodyOut,
            MainUnderbodyJoining, BodyIn),
        Link(MainJoinToSideJoin, MainUnderbodyJoining, BodyOut,
            SideSillRockerJoining, BodyIn),
        Link(SideJoinToFinish, SideSillRockerJoining, BodyOut,
            DeburrFinish, BodyIn),
        Link(FinishToInspection, DeburrFinish, BodyOut,
            UnderbodyInspection, BodyIn),
        Link(InspectionToPassBuffer, UnderbodyInspection, PassOut,
            PassBuffer, BodyIn),
        Link(InspectionToRework, UnderbodyInspection, ReworkOut,
            UnderbodyRework, ReworkIn),
        Link(ReworkToReinspection, UnderbodyRework, ReinspectOut,
            UnderbodyInspection, ReinspectIn)
    };
}

bool FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(
    const FLBBodyShopUnderbodyExpansionStationV2& Station, FString& OutReason)
{
    using namespace LBBodyShopUnderbodyExpansionV2Private;
    OutReason.Reset();
    if (Station.ContractVersion != 2 || Station.StationId.IsNone()
        || !IsKnownArchitecture(Station.Architecture)
        || !GetStableStationIds().Contains(Station.StationId) || Station.DisplayName.IsEmpty()
        || Station.FootprintCm.ContainsNaN() || Station.MaintenanceEnvelopeCm.ContainsNaN()
        || Station.FootprintCm.GetMin() <= 0.0f
        || Station.MaintenanceEnvelopeCm.GetMin() <= 0.0f
        || Station.MaintenanceEnvelopeCm.X < Station.FootprintCm.X
        || Station.MaintenanceEnvelopeCm.Y < Station.FootprintCm.Y
        || Station.MaintenanceEnvelopeCm.Z < Station.FootprintCm.Z
        || !FMath::IsFinite(Station.CycleSeconds) || Station.CycleSeconds <= 0.0f
        || Station.Ports.IsEmpty())
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION STATION HEADER IS INVALID");
        return false;
    }
    const int32 ExpectedStageIndex = GetStableStationIds().IndexOfByKey(Station.StationId);
    if (ExpectedStageIndex == INDEX_NONE
        || static_cast<int32>(Station.Stage) != ExpectedStageIndex)
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION STAGE DOES NOT MATCH ITS STABLE ID");
        return false;
    }
    if (!IsUniqueKnownNames(Station.ProcessStepIds, StableProcessStepIds())
        || Station.ProcessStepIds.IsEmpty()
        || !IsUniqueKnownNames(Station.ComponentIds,
            FLBBodyShopUnderbodyProcessRegistry::GetStableComponentIds())
        || !IsUniqueKnownNames(Station.JoinOperationIds,
            FLBBodyShopUnderbodyProcessRegistry::GetStableJoinOperationIds())
        || !IsUniqueKnownNames(Station.QualityCheckIds,
            FLBBodyShopUnderbodyProcessRegistry::GetStableQualityCheckIds()))
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION STATION USES INVALID PROCESS IDS");
        return false;
    }

    TSet<FName> PortIds;
    for (const FLBBodyShopUnderbodyExpansionPortV2& PortDefinition : Station.Ports)
    {
        if (PortDefinition.PortId.IsNone() || PortIds.Contains(PortDefinition.PortId)
            || !GetStablePortIds().Contains(PortDefinition.PortId)
            || !GetStableMaterialIds().Contains(PortDefinition.MaterialId)
            || !IsKnownDirection(PortDefinition.Direction)
            || !IsKnownTransport(PortDefinition.Transport)
            || !IsFiniteUnitTransform(PortDefinition.LocalTransform))
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION STATION HAS AN INVALID PORT");
            return false;
        }
        PortIds.Add(PortDefinition.PortId);
    }

    FLBBodyShopUnderbodyExpansionStationV2 Expected;
    if (!FindCanonicalStation(Station.StationId, Expected, Station.Architecture)
        || !StationsMatch(Station, Expected))
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION STATION DIFFERS FROM ITS EXACT CANONICAL CONTRACT");
        return false;
    }
    return true;
}

bool FLBBodyShopUnderbodyExpansionRegistryV2::ValidateExpansion(
    const TArray<FLBBodyShopUnderbodyExpansionStationV2>& Stations,
    const TArray<FLBBodyShopUnderbodyExpansionLayoutItemV2>& Layout,
    const TArray<FLBBodyShopUnderbodyExpansionConnectionV2>& Connections,
    FString& OutReason)
{
    using namespace LBBodyShopUnderbodyExpansionV2Private;
    OutReason.Reset();
    const TArray<FName> StableStations = GetStableStationIds();
    if (Stations.Num() != StableStations.Num() || Layout.Num() != StableStations.Num()
        || Connections.Num() != GetStableConnectionIds().Num())
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION INVENTORY IS INCOMPLETE");
        return false;
    }

    const ELBBodyShopUnderbodyArchitecture Architecture = Stations[0].Architecture;
    if (!IsKnownArchitecture(Architecture))
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION ARCHITECTURE IS INVALID");
        return false;
    }
    const TArray<FLBBodyShopUnderbodyExpansionStationV2> ExpectedStations =
        GetCanonicalStations(Architecture);
    const TArray<FLBBodyShopUnderbodyExpansionLayoutItemV2> ExpectedLayout =
        GetApprovedLayout();
    const TArray<FLBBodyShopUnderbodyExpansionConnectionV2> ExpectedConnections =
        GetApprovedConnections();
    if (ExpectedStations.Num() != Stations.Num() || ExpectedLayout.Num() != Layout.Num()
        || ExpectedConnections.Num() != Connections.Num())
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION CANONICAL INVENTORY IS INCOMPLETE");
        return false;
    }

    for (int32 Index = 0; Index < Stations.Num(); ++Index)
    {
        if (!ValidateStation(Stations[Index], OutReason)) return false;
        if (!StationsMatch(Stations[Index], ExpectedStations[Index]))
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION STATION ORDER OR CONTRACT IS NOT EXACT");
            return false;
        }
    }

    TSet<FName> SeenLayout;
    for (int32 Index = 0; Index < Layout.Num(); ++Index)
    {
        const FLBBodyShopUnderbodyExpansionLayoutItemV2& Item = Layout[Index];
        const FVector Location = Item.WorldTransform.GetLocation();
        if (Item.StationId.IsNone() || SeenLayout.Contains(Item.StationId)
            || !StableStations.Contains(Item.StationId)
            || !LayoutItemsMatch(Item, ExpectedLayout[Index])
            || !IsFiniteUnitTransform(Item.WorldTransform)
            || !FMath::IsNearlyZero(Item.WorldTransform.Rotator().Pitch, 0.01f)
            || !FMath::IsNearlyZero(Item.WorldTransform.Rotator().Yaw, 0.01f)
            || !FMath::IsNearlyZero(Item.WorldTransform.Rotator().Roll, 0.01f)
            || !FMath::IsNearlyEqual(Location.X, FMath::GridSnap(Location.X, 100.0f), 0.01f)
            || !FMath::IsNearlyEqual(Location.Y, FMath::GridSnap(Location.Y, 100.0f), 0.01f)
            || !FMath::IsNearlyZero(Location.Z, 0.01f))
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION LAYOUT IS INVALID");
            return false;
        }
        SeenLayout.Add(Item.StationId);
    }
    if (SeenLayout.Num() != StableStations.Num())
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION HAS A MISSING STATION");
        return false;
    }

    for (int32 LeftIndex = 0; LeftIndex < Stations.Num(); ++LeftIndex)
    {
        const FLBBodyShopUnderbodyExpansionLayoutItemV2* LeftLayout =
            FindLayout(Layout, Stations[LeftIndex].StationId);
        if (!LeftLayout)
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION STATION HAS NO LAYOUT ITEM");
            return false;
        }
        const FVector LeftHalf = Stations[LeftIndex].FootprintCm * 0.5f - FVector(0.5f);
        const FBox LeftBox(LeftLayout->WorldTransform.GetLocation() - LeftHalf,
            LeftLayout->WorldTransform.GetLocation() + LeftHalf);
        for (int32 RightIndex = LeftIndex + 1; RightIndex < Stations.Num(); ++RightIndex)
        {
            const FLBBodyShopUnderbodyExpansionLayoutItemV2* RightLayout =
                FindLayout(Layout, Stations[RightIndex].StationId);
            if (!RightLayout)
            {
                OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION STATION HAS NO LAYOUT ITEM");
                return false;
            }
            const FVector RightHalf = Stations[RightIndex].FootprintCm * 0.5f - FVector(0.5f);
            const FBox RightBox(RightLayout->WorldTransform.GetLocation() - RightHalf,
                RightLayout->WorldTransform.GetLocation() + RightHalf);
            if (LeftBox.Intersect(RightBox))
            {
                OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION STATION FOOTPRINTS OVERLAP");
                return false;
            }
        }
    }

    TSet<FName> ConnectionIds;
    TSet<FString> UsedEndpoints;
    for (int32 Index = 0; Index < Connections.Num(); ++Index)
    {
        const FLBBodyShopUnderbodyExpansionConnectionV2& Connection = Connections[Index];
        if (!ConnectionsMatch(Connection, ExpectedConnections[Index]))
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION CONNECTION ORDER OR FIELDS ARE NOT EXACT");
            return false;
        }
        const FLBBodyShopUnderbodyExpansionStationV2* SourceStation =
            FindStation(Stations, Connection.Source.StationId);
        const FLBBodyShopUnderbodyExpansionStationV2* TargetStation =
            FindStation(Stations, Connection.Target.StationId);
        const FLBBodyShopUnderbodyExpansionLayoutItemV2* SourceLayout =
            FindLayout(Layout, Connection.Source.StationId);
        const FLBBodyShopUnderbodyExpansionLayoutItemV2* TargetLayout =
            FindLayout(Layout, Connection.Target.StationId);
        if (Connection.ConnectionId.IsNone() || ConnectionIds.Contains(Connection.ConnectionId)
            || !SourceStation || !TargetStation
            || !SourceLayout || !TargetLayout)
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION CONNECTION IDENTITY IS INVALID");
            return false;
        }
        const FLBBodyShopUnderbodyExpansionPortV2* SourcePort =
            FindPort(*SourceStation, Connection.Source.PortId);
        const FLBBodyShopUnderbodyExpansionPortV2* TargetPort =
            FindPort(*TargetStation, Connection.Target.PortId);
        const FString SourceEndpoint = Connection.Source.StationId.ToString() + TEXT("/")
            + Connection.Source.PortId.ToString();
        const FString TargetEndpoint = Connection.Target.StationId.ToString() + TEXT("/")
            + Connection.Target.PortId.ToString();
        if (!SourcePort || !TargetPort || SourcePort->Direction != ELBBodyShopPortDirection::Output
            || TargetPort->Direction != ELBBodyShopPortDirection::Input
            || SourcePort->Transport != TargetPort->Transport
            || SourcePort->MaterialId != TargetPort->MaterialId
            || UsedEndpoints.Contains(SourceEndpoint) || UsedEndpoints.Contains(TargetEndpoint))
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION CONNECTION CONTRACT IS INVALID");
            return false;
        }
        const FTransform SourceWorld = SourcePort->LocalTransform * SourceLayout->WorldTransform;
        const FTransform TargetWorld = TargetPort->LocalTransform * TargetLayout->WorldTransform;
        if (!AreFullyOpposed(SourceWorld, TargetWorld))
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION PORTS ARE NOT COINCIDENT AND OPPOSED");
            return false;
        }
        ConnectionIds.Add(Connection.ConnectionId);
        UsedEndpoints.Add(SourceEndpoint);
        UsedEndpoints.Add(TargetEndpoint);
    }

    TSet<FName> CoveredComponents;
    TSet<FName> CoveredProcessSteps;
    TSet<FName> CoveredJoinOperations;
    TSet<FName> CoveredQualityChecks;
    for (const FLBBodyShopUnderbodyExpansionStationV2& Station : Stations)
    {
        for (const FName Id : Station.ProcessStepIds) CoveredProcessSteps.Add(Id);
        for (const FName Id : Station.ComponentIds) CoveredComponents.Add(Id);
        for (const FName Id : Station.JoinOperationIds) CoveredJoinOperations.Add(Id);
        for (const FName Id : Station.QualityCheckIds) CoveredQualityChecks.Add(Id);
    }
    FLBBodyShopUnderbodyProcessRecipe Recipe =
        FLBBodyShopUnderbodyProcessRegistry::BuildPilotRecipe(Architecture);
    Recipe.SelectedComponentIds.Add(LBBodyShopUnderbodyComponentIds::FrontFloorPartition);
    Recipe.SelectedComponentIds.Add(LBBodyShopUnderbodyComponentIds::RearFloorPartition);
    FString RecipeReason;
    if (!FLBBodyShopUnderbodyProcessRegistry::ValidateRecipe(Recipe, RecipeReason))
    {
        OutReason = FString::Printf(
            TEXT("BODY SHOP UNDERBODY EXPANSION ARCHITECTURE RECIPE IS INVALID: %s"),
            *RecipeReason);
        return false;
    }
    if (CoveredComponents.Num() != Recipe.SelectedComponentIds.Num())
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION COMPONENT RESPONSIBILITIES ARE NOT EXACT");
        return false;
    }
    for (const FName RequiredComponent : Recipe.SelectedComponentIds)
    {
        if (!CoveredComponents.Contains(RequiredComponent))
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION DOES NOT COVER ITS SELECTED RECIPE");
            return false;
        }
    }
    if (CoveredProcessSteps.Num() != Recipe.OrderedProcessStepIds.Num())
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION PROCESS RESPONSIBILITIES ARE NOT EXACT");
        return false;
    }
    for (const FName RequiredStep : Recipe.OrderedProcessStepIds)
    {
        if (!CoveredProcessSteps.Contains(RequiredStep))
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION DOES NOT COVER ITS RECIPE STEPS");
            return false;
        }
    }
    if (!CoveredJoinOperations.Contains(LBBodyShopUnderbodyJoinOperationIds::ResistanceSpotWeld))
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION HAS NO PRIMARY JOINING AUTHORITY");
        return false;
    }
    if (CoveredQualityChecks.Num() != Recipe.RequiredQualityCheckIds.Num())
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION QUALITY RESPONSIBILITIES ARE NOT EXACT");
        return false;
    }
    for (const FName RequiredCheck : Recipe.RequiredQualityCheckIds)
    {
        if (!CoveredQualityChecks.Contains(RequiredCheck))
        {
            OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION DOES NOT COVER REQUIRED QUALITY CHECKS");
            return false;
        }
    }

    return true;
}

bool FLBBodyShopUnderbodyExpansionRegistryV2::ValidateApprovedExpansion(FString& OutReason)
{
    return ValidateApprovedExpansion(ELBBodyShopUnderbodyArchitecture::CentreTunnel,
        OutReason);
}

bool FLBBodyShopUnderbodyExpansionRegistryV2::ValidateApprovedExpansion(
    const ELBBodyShopUnderbodyArchitecture Architecture, FString& OutReason)
{
    if (!LBBodyShopUnderbodyExpansionV2Private::IsKnownArchitecture(Architecture))
    {
        OutReason = TEXT("BODY SHOP UNDERBODY EXPANSION ARCHITECTURE IS INVALID");
        return false;
    }
    return ValidateExpansion(GetCanonicalStations(Architecture), GetApprovedLayout(),
        GetApprovedConnections(), OutReason);
}
