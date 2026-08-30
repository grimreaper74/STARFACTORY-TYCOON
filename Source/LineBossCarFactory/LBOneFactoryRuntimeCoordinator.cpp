#include "LBOneFactoryRuntimeCoordinator.h"

#include "LBVehiclePanelCatalog.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBFactoryManagementSubsystem.h"
#include "Misc/Crc.h"

namespace LBOneFactoryRuntimeCoordinatorPrivate
{
    constexpr float CycleToleranceSeconds = 0.001f;
    constexpr int32 PressPanelInspectionRouteIndex = 5;

    /**
     * Runtime route versions are deliberately independent of the save schema.
     * Routed units persist an exact topology id; manual units persist the
     * additive route-profile field. Pre-V002 zero/default manual genealogy is
     * conservatively V001, so all active V001 work drains before V002 admits.
     */
    enum class ERouteProfile : uint8
    {
        LegacyV001,
        PressInspectionV002
    };

    /**
     * Exact topology written by the released pre-relocation V001 route.
     * This is an input-only migration alias: MakeTopologyId still computes
     * the identity of the current physical route and never emits this value.
     */
    const FName& FrozenPersistedV001TopologyAlias()
    {
        static const FName Alias(
            TEXT("OF_RUNTIME_TOPOLOGY_V001_C9F61F4B"));
        return Alias;
    }

    bool IsFrozenPersistedV001TopologyAlias(const FName TopologyId)
    {
        return TopologyId == FrozenPersistedV001TopologyAlias();
    }

    struct FAuthorities
    {
        ALBOneFactoryPressStarterLayoutAuthority* Press = nullptr;
        ALBOneFactoryBodyWeldStarterLayoutAuthority* Body = nullptr;
        ALBOneFactoryPaintStarterLayoutAuthority* Paint = nullptr;
        ALBOneFactoryAssemblyStarterLayoutAuthority* Assembly = nullptr;
        ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    };

    struct FSnapshots
    {
        FLBOneFactoryPressStarterLayoutState Press;
        FLBOneFactoryBodyWeldLayoutState Body;
        FLBOneFactoryPaintStarterLayoutState Paint;
        FLBOneFactoryAssemblyLayoutState Assembly;
        FLBOneFactoryProductionLedgerState Ledger;
    };

    template<typename ActorType>
    bool ResolveExactlyOne(UWorld* World, const TCHAR* Label,
        ActorType*& OutActor, FString& OutReason)
    {
        OutActor = nullptr;
        int32 Count = 0;
        if (World)
        {
            for (TActorIterator<ActorType> It(World); It; ++It)
            {
                if (IsValid(*It) && !It->IsActorBeingDestroyed())
                {
                    OutActor = *It;
                    ++Count;
                }
            }
        }
        if (Count != 1)
        {
            OutActor = nullptr;
            OutReason = FString::Printf(
                TEXT("ONEFACTORY RUNTIME REQUIRES EXACTLY ONE %s AUTHORITY; FOUND %d"),
                Label, Count);
            return false;
        }
        return true;
    }

    bool ResolveAuthorities(const ALBOneFactoryRuntimeCoordinator& Coordinator,
        FAuthorities& Out, FString& OutReason)
    {
        UWorld* World = Coordinator.GetWorld();
        if (!ResolveExactlyOne(World, TEXT("PRESS"), Out.Press, OutReason)
            || !ResolveExactlyOne(World, TEXT("BODY/WELD"), Out.Body,
                OutReason)
            || !ResolveExactlyOne(World, TEXT("PAINT"), Out.Paint,
                OutReason)
            || !ResolveExactlyOne(World, TEXT("ASSEMBLY"), Out.Assembly,
                OutReason)
            || !ResolveExactlyOne(World, TEXT("PRODUCTION"), Out.Production,
                OutReason))
        {
            return false;
        }
        if (!Out.Press->ActorHasTag(
                ALBOneFactoryPressStarterLayoutAuthority::GetAuthorityTag())
            || !Out.Body->ActorHasTag(
                ALBOneFactoryBodyWeldStarterLayoutAuthority::GetAuthorityTag())
            || !Out.Paint->ActorHasTag(
                ALBOneFactoryPaintStarterLayoutAuthority::GetAuthorityTag())
            || !Out.Assembly->ActorHasTag(
                ALBOneFactoryAssemblyStarterLayoutAuthority::GetAuthorityTag())
            || !Out.Production->ActorHasTag(
                ALBOneFactoryProductionFlowAuthority::GetAuthorityTag()))
        {
            OutReason = TEXT("ONEFACTORY RUNTIME AUTHORITY TAG CONTRACT FAILED");
            return false;
        }
        return true;
    }

    FSnapshots Capture(const FAuthorities& Actors)
    {
        FSnapshots State;
        State.Press = Actors.Press->CaptureLayout();
        State.Body = Actors.Body->CaptureLayout();
        State.Paint = Actors.Paint->CaptureLayout();
        State.Assembly = Actors.Assembly->CaptureLayout();
        State.Ledger = Actors.Production->CaptureLedger();
        return State;
    }

    bool IsTerminal(const FLBOneFactoryVehicleUnitState& Unit)
    {
        return Unit.Stage == ELBOneFactoryVehicleStage::Dispatched
            || Unit.QualityState == ELBOneFactoryVehicleQualityState::Scrapped;
    }

    bool HasActiveManualWIP(
        const FLBOneFactoryProductionLedgerState& Ledger)
    {
        return Ledger.Units.ContainsByPredicate([](
            const FLBOneFactoryVehicleUnitState& Unit)
            {
                return !IsTerminal(Unit) && Unit.RuntimeStationCursor < 0;
            });
    }

    FName PaintColourId(const ELBOneFactoryPaintColour Colour)
    {
        switch (Colour)
        {
        case ELBOneFactoryPaintColour::BodyInWhite: return TEXT("BODY_IN_WHITE");
        case ELBOneFactoryPaintColour::EDPrimerGrey: return TEXT("ED_PRIMER_GREY");
        case ELBOneFactoryPaintColour::ArcticWhite: return TEXT("ARCTIC_WHITE");
        case ELBOneFactoryPaintColour::FoundryGraphite:
            return TEXT("FOUNDRY_GRAPHITE");
        case ELBOneFactoryPaintColour::CairnwellTeal:
            return TEXT("CAIRNWELL_TEAL");
        case ELBOneFactoryPaintColour::SignalRed: return TEXT("SIGNAL_RED");
        case ELBOneFactoryPaintColour::AuroraBlue: return TEXT("AURORA_BLUE");
        default: return NAME_None;
        }
    }

    bool LedgerDepartmentCommissioned(
        const FLBOneFactoryProductionLedgerState& Ledger,
        const ELBOneFactoryDepartment Department)
    {
        switch (Department)
        {
        case ELBOneFactoryDepartment::Press:
            return Ledger.Commissioning.bPressCommissioned;
        case ELBOneFactoryDepartment::Body:
            return Ledger.Commissioning.bBodyCommissioned;
        case ELBOneFactoryDepartment::Paint:
            return Ledger.Commissioning.bPaintCommissioned;
        default:
            return Ledger.Commissioning.bAssemblyCommissioned;
        }
    }

    bool LayoutDepartmentCommissioned(const FSnapshots& State,
        const ELBOneFactoryDepartment Department)
    {
        switch (Department)
        {
        case ELBOneFactoryDepartment::Press: return State.Press.bCommissioned;
        case ELBOneFactoryDepartment::Body: return State.Body.bCommissioned;
        case ELBOneFactoryDepartment::Paint: return State.Paint.bCommissioned;
        default: return State.Assembly.bCommissioned;
        }
    }

    FName MakeWorkId(const TCHAR* Prefix, const int32 Value)
    {
        return FName(*FString::Printf(TEXT("%s_%02d"), Prefix, Value));
    }

    FName MakeAssignmentId(const TCHAR* Prefix,
        const TArray<FName>& WorkIds)
    {
        FString Value(Prefix);
        if (WorkIds.IsEmpty())
        {
            Value += TEXT("_PASS_THROUGH");
        }
        else
        {
            for (const FName WorkId : WorkIds)
            {
                Value += TEXT("_");
                Value += WorkId.ToString();
            }
        }
        return FName(*Value);
    }

    void AddStep(TArray<FLBOneFactoryRuntimeStationStep>& Route,
        const ELBOneFactoryDepartment Department, const FName StationId,
        const FTransform& WorldTransform, const TArray<FName>& WorkIds,
        const TCHAR* AssignmentPrefix, const float CycleSeconds,
        const ELBOneFactoryVehicleStage Stage, const bool bQualityGate)
    {
        FLBOneFactoryRuntimeStationStep& Step = Route.AddDefaulted_GetRef();
        Step.RouteIndex = Route.Num() - 1;
        Step.Department = Department;
        Step.StationId = StationId;
        Step.WorldTransform = WorldTransform;
        Step.ConfiguredWorkIds = WorkIds;
        Step.AssignmentId = MakeAssignmentId(AssignmentPrefix, WorkIds);
        Step.NominalCycleSeconds = CycleSeconds;
        Step.SemanticStage = Stage;
        Step.bQualityGate = bQualityGate;
    }

    int32 FindBodyProgrammePosition(
        const FLBOneFactoryBodyWeldLayoutState& State,
        const ELBOneFactoryBodyWeldProgramme Programme)
    {
        for (const FLBOneFactoryBodyWeldStationState& Station : State.Stations)
        {
            if (Station.AssignedProgrammes.Contains(Programme))
                return Station.LinePosition;
        }
        return INDEX_NONE;
    }

    int32 FindAssemblyOperationPosition(
        const FLBOneFactoryAssemblyLayoutState& State,
        const ELBOneFactoryAssemblyOperation Operation)
    {
        for (const FLBOneFactoryAssemblyStationState& Station : State.Stations)
        {
            if (Station.AssignedOperations.Contains(Operation))
                return Station.LinePosition;
        }
        return INDEX_NONE;
    }

    void ApplyPressRouteProfile(
        TArray<FLBOneFactoryRuntimeStationStep>& Route,
        const ERouteProfile Profile)
    {
        check(Route.IsValidIndex(PressPanelInspectionRouteIndex));
        FLBOneFactoryRuntimeStationStep& Inspection =
            Route[PressPanelInspectionRouteIndex];
        Inspection.SemanticStage = Profile == ERouteProfile::LegacyV001
            ? ELBOneFactoryVehicleStage::Pressing
            : ELBOneFactoryVehicleStage::PressPanelInspection;
        Inspection.bQualityGate = Profile ==
            ERouteProfile::PressInspectionV002;
    }

    FName MakeTopologyId(
        const TArray<FLBOneFactoryRuntimeStationStep>& Route,
        const ERouteProfile Profile)
    {
        const bool bLegacy = Profile == ERouteProfile::LegacyV001;
        FString Contract(bLegacy
            ? TEXT("ONEFACTORY_RUNTIME_ROUTE_V001")
            : TEXT("ONEFACTORY_RUNTIME_ROUTE_V002"));
        for (const FLBOneFactoryRuntimeStationStep& Step : Route)
        {
            const FVector Location = Step.WorldTransform.GetLocation();
            const FRotator Rotation = Step.WorldTransform.Rotator();
            Contract += FString::Printf(
                TEXT("|%02d|%d|%s|%s|%.3f|%d|%d|%.3f,%.3f,%.3f|%.3f"),
                Step.RouteIndex, static_cast<int32>(Step.Department),
                *Step.StationId.ToString(), *Step.AssignmentId.ToString(),
                Step.NominalCycleSeconds,
                static_cast<int32>(Step.SemanticStage),
                Step.bQualityGate ? 1 : 0, Location.X, Location.Y, Location.Z,
                Rotation.Yaw);
        }
        const uint32 ContractCrc = FCrc::StrCrc32(*Contract);
        if (bLegacy)
        {
            return FName(*FString::Printf(
                TEXT("OF_RUNTIME_TOPOLOGY_V001_%08X"), ContractCrc));
        }
        return FName(*FString::Printf(
            TEXT("OF_RUNTIME_TOPOLOGY_V002_%08X"), ContractCrc));
    }

    bool IsLegacyRouteTopology(const FName TopologyId)
    {
        return TopologyId.ToString().StartsWith(
            TEXT("OF_RUNTIME_TOPOLOGY_V001_"));
    }

    bool IsAllowedLegacyRoutedTopology(const FName SavedTopologyId,
        const FName ComputedLegacyTopologyId)
    {
        return SavedTopologyId == ComputedLegacyTopologyId
            || IsFrozenPersistedV001TopologyAlias(SavedTopologyId);
    }

    void NormalizeFrozenV001TopologyAliasForMutation(
        FLBOneFactoryProductionLedgerState& Ledger,
        const FName MutatedUnitId,
        const FName ComputedSelectedTopologyId)
    {
        if (!IsLegacyRouteTopology(ComputedSelectedTopologyId)) return;
        FLBOneFactoryVehicleUnitState* Unit = Ledger.Units.FindByPredicate(
            [MutatedUnitId](const FLBOneFactoryVehicleUnitState& Candidate)
            { return Candidate.UnitId == MutatedUnitId; });
        if (!Unit || Unit->RuntimeStationCursor < 0
            || ULBOneFactoryProductionFlowLibrary::
                ResolveRouteProfileVersion(*Unit)
                != ULBOneFactoryProductionFlowLibrary::
                    LegacyRouteProfileV001)
        {
            return;
        }
        if (IsFrozenPersistedV001TopologyAlias(Unit->RuntimeTopologyId))
        {
            Unit->RuntimeTopologyId = ComputedSelectedTopologyId;
        }
        if (Unit->RouteProfileVersion ==
            ULBOneFactoryProductionFlowLibrary::UnversionedRouteProfile)
        {
            Unit->RouteProfileVersion = ULBOneFactoryProductionFlowLibrary::
                LegacyRouteProfileV001;
        }
    }

    bool BuildRoute(const FSnapshots& State,
        TArray<FLBOneFactoryRuntimeStationStep>& OutRoute,
        FName& OutTopologyId, FString& OutReason)
    {
        OutRoute.Reset();
        OutTopologyId = NAME_None;
        FString Detail;
        if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
                State.Press, Detail)
            || !ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
                State.Body, Detail)
            || !ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
                State.Paint, Detail)
            || !ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
                State.Assembly, Detail))
        {
            OutReason = FString(TEXT("ONEFACTORY RUNTIME LAYOUT PREFLIGHT FAILED: "))
                + Detail;
            return false;
        }

        static const float PressCycles[] =
            {8.0f, 12.0f, 18.0f, 8.0f, 45.0f, 12.0f, 8.0f};
        static const ELBOneFactoryVehicleStage PressStages[] =
        {
            ELBOneFactoryVehicleStage::InboundCoil,
            ELBOneFactoryVehicleStage::InboundCoil,
            ELBOneFactoryVehicleStage::BlankPreparation,
            ELBOneFactoryVehicleStage::BlankPreparation,
            ELBOneFactoryVehicleStage::Pressing,
            ELBOneFactoryVehicleStage::PressPanelInspection,
            ELBOneFactoryVehicleStage::PressedPanelStillage
        };
        for (int32 Index = 0; Index < 7; ++Index)
        {
            const ELBOneFactoryPressStarterRole Role =
                static_cast<ELBOneFactoryPressStarterRole>(Index);
            const FLBOneFactoryPressStarterStationState* Station =
                State.Press.Stations.FindByPredicate([Role](
                    const FLBOneFactoryPressStarterStationState& Candidate)
                { return Candidate.Role == Role; });
            if (!Station)
            {
                OutReason = TEXT("ONEFACTORY PRESS PHYSICAL ROUTE IS INCOMPLETE");
                return false;
            }
            TArray<FName> WorkIds = {MakeWorkId(TEXT("PRESS_ROLE"), Index)};
            if (!Station->PanelTypeId.IsNone())
            {
                WorkIds.Add(Station->PanelTypeId);
                WorkIds.Add(Station->DieId);
            }
            AddStep(OutRoute, ELBOneFactoryDepartment::Press,
                Station->StationId, Station->WorldTransform, WorkIds,
                TEXT("PRESS_ASSIGNMENT"), PressCycles[Index],
                PressStages[Index], Index == PressPanelInspectionRouteIndex);
        }

        const int32 BodyMarriagePosition = FindBodyProgrammePosition(State.Body,
            ELBOneFactoryBodyWeldProgramme::BodyFramingAndMarriage);
        const int32 BodyQualityPosition = FindBodyProgrammePosition(State.Body,
            ELBOneFactoryBodyWeldProgramme::WeldQualityInspection);
        for (int32 Position = 1;
            Position <= ULBOneFactoryBodyWeldStarterLayoutLibrary::RequiredStationCount;
            ++Position)
        {
            const FLBOneFactoryBodyWeldStationState* Station =
                State.Body.Stations.FindByPredicate([Position](
                    const FLBOneFactoryBodyWeldStationState& Candidate)
                { return Candidate.LinePosition == Position; });
            if (!Station)
            {
                OutReason = TEXT("ONEFACTORY BODY/WELD PHYSICAL ROUTE IS INCOMPLETE");
                return false;
            }
            TArray<FName> WorkIds;
            for (const ELBOneFactoryBodyWeldProgramme Programme :
                Station->AssignedProgrammes)
            {
                WorkIds.Add(MakeWorkId(TEXT("BODY_PROGRAMME"),
                    static_cast<int32>(Programme)));
            }
            if (WorkIds.IsEmpty()) WorkIds.Add(TEXT("BODY_PASS_THROUGH"));
            const bool bQuality = Station->AssignedProgrammes.Contains(
                ELBOneFactoryBodyWeldProgramme::WeldQualityInspection);
            const ELBOneFactoryVehicleStage Stage = Position <= BodyMarriagePosition
                ? ELBOneFactoryVehicleStage::BodyFraming
                : Position < BodyQualityPosition
                    ? ELBOneFactoryVehicleStage::BodyInWhite
                    : ELBOneFactoryVehicleStage::BodyQualityInspection;
            AddStep(OutRoute, ELBOneFactoryDepartment::Body,
                Station->StationId, Station->WorldTransform, WorkIds,
                TEXT("BODY_ASSIGNMENT"), Station->NominalCycleSeconds,
                Stage, bQuality);
        }

        static const float PaintCycles[] =
            {8.0f, 25.0f, 35.0f, 12.0f, 30.0f, 40.0f, 18.0f, 8.0f};
        for (int32 Index = 0; Index < 8; ++Index)
        {
            const ELBOneFactoryPaintStarterRole Role =
                static_cast<ELBOneFactoryPaintStarterRole>(Index);
            const FLBOneFactoryPaintStarterStationState* Station =
                State.Paint.Stations.FindByPredicate([Role](
                    const FLBOneFactoryPaintStarterStationState& Candidate)
                { return Candidate.Role == Role; });
            if (!Station)
            {
                OutReason = TEXT("ONEFACTORY PAINT PHYSICAL ROUTE IS INCOMPLETE");
                return false;
            }
            TArray<FName> WorkIds = {MakeWorkId(TEXT("PAINT_ROLE"), Index)};
            if (!Station->PaintProgrammeId.IsNone())
                WorkIds.Add(Station->PaintProgrammeId);
            ELBOneFactoryVehicleStage Stage =
                ELBOneFactoryVehicleStage::Pretreatment;
            if (Role == ELBOneFactoryPaintStarterRole::EDCoatLogicalProcess
                || Role == ELBOneFactoryPaintStarterRole::FlashOff)
                Stage = ELBOneFactoryVehicleStage::EDCoat;
            else if (Role == ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth)
                Stage = ELBOneFactoryVehicleStage::ColourCoat;
            else if (Role == ELBOneFactoryPaintStarterRole::CuringOven)
                Stage = ELBOneFactoryVehicleStage::Cure;
            else if (Role ==
                    ELBOneFactoryPaintStarterRole::QualityLightInspection
                || Role ==
                    ELBOneFactoryPaintStarterRole::PaintedBodyDispatch)
                Stage = ELBOneFactoryVehicleStage::PaintQualityInspection;
            const bool bQuality = Role ==
                ELBOneFactoryPaintStarterRole::QualityLightInspection;
            AddStep(OutRoute, ELBOneFactoryDepartment::Paint,
                Station->StationId, Station->WorldTransform, WorkIds,
                TEXT("PAINT_ASSIGNMENT"), PaintCycles[Index], Stage, bQuality);
        }

        const int32 MarriagePosition = FindAssemblyOperationPosition(
            State.Assembly, ELBOneFactoryAssemblyOperation::PowertrainMarriage);
        const int32 FinalQualityPosition = FindAssemblyOperationPosition(
            State.Assembly,
            ELBOneFactoryAssemblyOperation::FinalInspectionAndRework);
        for (int32 Position = 1;
            Position <= ULBOneFactoryAssemblyStarterLayoutLibrary::RequiredStationCount;
            ++Position)
        {
            const FLBOneFactoryAssemblyStationState* Station =
                State.Assembly.Stations.FindByPredicate([Position](
                    const FLBOneFactoryAssemblyStationState& Candidate)
                { return Candidate.LinePosition == Position; });
            if (!Station)
            {
                OutReason = TEXT("ONEFACTORY ASSEMBLY PHYSICAL ROUTE IS INCOMPLETE");
                return false;
            }
            TArray<FName> WorkIds;
            for (const ELBOneFactoryAssemblyOperation Operation :
                Station->AssignedOperations)
            {
                WorkIds.Add(MakeWorkId(TEXT("ASSEMBLY_OPERATION"),
                    static_cast<int32>(Operation)));
            }
            if (WorkIds.IsEmpty()) WorkIds.Add(TEXT("ASSEMBLY_PASS_THROUGH"));
            const bool bQuality = Station->AssignedOperations.Contains(
                ELBOneFactoryAssemblyOperation::FinalInspectionAndRework);
            ELBOneFactoryVehicleStage Stage =
                ELBOneFactoryVehicleStage::GeneralAssemblyTrim;
            if (Position == MarriagePosition)
                Stage = ELBOneFactoryVehicleStage::PowertrainMarriage;
            else if (Position > MarriagePosition
                && Position < FinalQualityPosition)
                Stage = ELBOneFactoryVehicleStage::RollingChassis;
            else if (Position ==
                ULBOneFactoryAssemblyStarterLayoutLibrary::RequiredStationCount)
                Stage = ELBOneFactoryVehicleStage::FinishedVehicle;
            else if (Position >= FinalQualityPosition)
                Stage = ELBOneFactoryVehicleStage::EndOfLineInspection;
            AddStep(OutRoute, ELBOneFactoryDepartment::Assembly,
                Station->StationId, Station->WorldTransform, WorkIds,
                TEXT("ASSEMBLY_ASSIGNMENT"), Station->NominalCycleSeconds,
                Stage, bQuality);
        }

        if (OutRoute.Num()
            != ALBOneFactoryRuntimeCoordinator::RequiredPhysicalStationCount)
        {
            OutReason = FString::Printf(
                TEXT("ONEFACTORY RUNTIME ROUTE REQUIRES 57 STATIONS; FOUND %d"),
                OutRoute.Num());
            OutRoute.Reset();
            return false;
        }
        const FName CurrentTopologyId = MakeTopologyId(OutRoute,
            ERouteProfile::PressInspectionV002);
        TArray<FLBOneFactoryRuntimeStationStep> LegacyRoute = OutRoute;
        ApplyPressRouteProfile(LegacyRoute, ERouteProfile::LegacyV001);
        const FName LegacyTopologyId = MakeTopologyId(LegacyRoute,
            ERouteProfile::LegacyV001);

        ERouteProfile SelectedProfile = ERouteProfile::PressInspectionV002;
        bool bActiveProfileSelected = false;
        bool bHasActiveManualMode = false;
        bool bHasActiveRoutedMode = false;
        for (const FLBOneFactoryVehicleUnitState& Unit : State.Ledger.Units)
        {
            if (IsTerminal(Unit)) continue;

            bHasActiveManualMode |= Unit.RuntimeStationCursor < 0;
            bHasActiveRoutedMode |= Unit.RuntimeStationCursor >= 0;
            if (bHasActiveManualMode && bHasActiveRoutedMode)
            {
                OutReason = TEXT(
                    "ONEFACTORY RUNTIME CANNOT MIX ACTIVE MANUAL AND ROUTED WIP");
                OutRoute.Reset();
                return false;
            }

            ERouteProfile UnitProfile;
            const int32 PersistedProfile =
                ULBOneFactoryProductionFlowLibrary::
                    ResolveRouteProfileVersion(Unit);
            if (PersistedProfile == ULBOneFactoryProductionFlowLibrary::
                    LegacyRouteProfileV001)
            {
                UnitProfile = ERouteProfile::LegacyV001;
            }
            else if (PersistedProfile == ULBOneFactoryProductionFlowLibrary::
                    PressInspectionRouteProfileV002)
            {
                UnitProfile = ERouteProfile::PressInspectionV002;
            }
            else
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY RUNTIME ROUTE PROFILE IS INVALID FOR ACTIVE UNIT %s"),
                    *Unit.UnitId.ToString());
                OutRoute.Reset();
                return false;
            }

            // Manual genealogy has no physical topology. Routed WIP must
            // still prove the exact topology for the profile inferred above.
            if (Unit.RuntimeStationCursor >= 0
                && ((UnitProfile == ERouteProfile::LegacyV001
                        && !IsAllowedLegacyRoutedTopology(
                            Unit.RuntimeTopologyId, LegacyTopologyId))
                    || (UnitProfile == ERouteProfile::PressInspectionV002
                        && Unit.RuntimeTopologyId != CurrentTopologyId)))
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY RUNTIME TOPOLOGY DRIFTED FOR ACTIVE UNIT %s"),
                    *Unit.UnitId.ToString());
                OutRoute.Reset();
                return false;
            }
            if (bActiveProfileSelected && UnitProfile != SelectedProfile)
            {
                OutReason = TEXT(
                    "ONEFACTORY RUNTIME CANNOT MIX ACTIVE V001 AND V002 ROUTE PROFILES");
                OutRoute.Reset();
                return false;
            }
            SelectedProfile = UnitProfile;
            bActiveProfileSelected = true;
        }

        if (SelectedProfile == ERouteProfile::LegacyV001)
        {
            OutRoute = MoveTemp(LegacyRoute);
            OutTopologyId = LegacyTopologyId;
            OutReason = TEXT(
                "ONEFACTORY LEGACY V001 ROUTE VALID; ACTIVE ROUTED OR MANUAL WIP MUST DRAIN BEFORE V002 ADMISSION");
        }
        else
        {
            OutTopologyId = CurrentTopologyId;
            OutReason = TEXT(
                "ONEFACTORY CONFIGURED 57-STATION V002 ROUTE WITH PRESS QUALITY GATE VALID");
        }
        return true;
    }

    const FLBOneFactoryVehicleUnitState* FindUnit(
        const FLBOneFactoryProductionLedgerState& Ledger, const FName UnitId)
    {
        return Ledger.Units.FindByPredicate([UnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
        { return Unit.UnitId == UnitId; });
    }

    FLBOneFactoryVehicleUnitState* FindUnit(
        FLBOneFactoryProductionLedgerState& Ledger, const FName UnitId)
    {
        return Ledger.Units.FindByPredicate([UnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
        { return Unit.UnitId == UnitId; });
    }

    bool AddReservationSet(const TArray<FName>& UnitIds,
        const FName StationId, const ELBOneFactoryDepartment Department,
        const FLBOneFactoryProductionLedgerState& Ledger,
        TMap<FName, FName>& OutStationByUnit,
        TMap<FName, ELBOneFactoryDepartment>& OutDepartmentByUnit,
        FString& OutReason)
    {
        if (UnitIds.Num() > 1)
        {
            OutReason = FString::Printf(
                TEXT("ONEFACTORY RUNTIME STATION %s HAS MORE THAN ONE WIP RESERVATION"),
                *StationId.ToString());
            return false;
        }
        for (const FName UnitId : UnitIds)
        {
            if (OutStationByUnit.Contains(UnitId))
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY RUNTIME UNIT %s IS RESERVED MORE THAN ONCE"),
                    *UnitId.ToString());
                return false;
            }
            const FLBOneFactoryVehicleUnitState* Unit = FindUnit(Ledger, UnitId);
            if (!Unit || IsTerminal(*Unit) || Unit->Department != Department
                || Unit->CurrentStationId != StationId)
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY RUNTIME RESERVATION %s DISAGREES WITH ITS LEDGER UNIT"),
                    *UnitId.ToString());
                return false;
            }
            OutStationByUnit.Add(UnitId, StationId);
            OutDepartmentByUnit.Add(UnitId, Department);
        }
        return true;
    }

    bool ValidateComposite(const FSnapshots& State,
        const TArray<FLBOneFactoryRuntimeStationStep>& Route,
        const FName TopologyId, FString& OutReason)
    {
        FString Detail;
        if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
                State.Press, Detail)
            || !ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
                State.Body, Detail)
            || !ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
                State.Paint, Detail)
            || !ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
                State.Assembly, Detail)
            || !ULBOneFactoryProductionFlowLibrary::ValidateLedger(
                State.Ledger, Detail))
        {
            OutReason = FString(TEXT("ONEFACTORY RUNTIME COMPOSITE PREFLIGHT FAILED: "))
                + Detail;
            return false;
        }
        const FLBOneFactoryDepartmentCommissioningState& Commissioning =
            State.Ledger.Commissioning;
        if (State.Press.bCommissioned != Commissioning.bPressCommissioned
            || State.Body.bCommissioned != Commissioning.bBodyCommissioned
            || State.Paint.bCommissioned != Commissioning.bPaintCommissioned
            || State.Assembly.bCommissioned
                != Commissioning.bAssemblyCommissioned)
        {
            OutReason = TEXT("ONEFACTORY RUNTIME LAYOUT AND LEDGER COMMISSIONING DISAGREE");
            return false;
        }
        if (State.Body.VehicleModelId.IsNone()
            || State.Paint.VehicleModelId != State.Body.VehicleModelId
            || State.Assembly.VehicleModelId != State.Body.VehicleModelId)
        {
            OutReason = TEXT("ONEFACTORY RUNTIME VEHICLE-MODEL AUTHORITIES DISAGREE");
            return false;
        }

        TMap<FName, FName> StationByUnit;
        TMap<FName, ELBOneFactoryDepartment> DepartmentByUnit;
        for (const FLBOneFactoryPressStarterStationState& Station :
            State.Press.Stations)
            if (!AddReservationSet(Station.ActiveOrReservedUnitIds,
                    Station.StationId, ELBOneFactoryDepartment::Press,
                    State.Ledger, StationByUnit, DepartmentByUnit, OutReason))
                return false;
        for (const FLBOneFactoryBodyWeldStationState& Station :
            State.Body.Stations)
            if (!AddReservationSet(Station.ActiveOrReservedUnitIds,
                    Station.StationId, ELBOneFactoryDepartment::Body,
                    State.Ledger, StationByUnit, DepartmentByUnit, OutReason))
                return false;
        for (const FLBOneFactoryPaintStarterStationState& Station :
            State.Paint.Stations)
            if (!AddReservationSet(Station.ActiveOrReservedUnitIds,
                    Station.StationId, ELBOneFactoryDepartment::Paint,
                    State.Ledger, StationByUnit, DepartmentByUnit, OutReason))
                return false;
        for (const FLBOneFactoryAssemblyStationState& Station :
            State.Assembly.Stations)
            if (!AddReservationSet(Station.ActiveOrReservedUnitIds,
                    Station.StationId, ELBOneFactoryDepartment::Assembly,
                    State.Ledger, StationByUnit, DepartmentByUnit, OutReason))
                return false;

        // A terminal unit is durable genealogy, not live WIP. After the last
        // V001 unit drains, the line selects V002, but the dispatched/scrapped
        // record must remain valid under the unchanged physical layout. The
        // computed companion and the single frozen pre-relocation V001 alias
        // are accepted; every other claimed topology remains fail-closed.
        TArray<FLBOneFactoryRuntimeStationStep> CompanionRoute = Route;
        const ERouteProfile CompanionProfile = IsLegacyRouteTopology(TopologyId)
            ? ERouteProfile::PressInspectionV002
            : ERouteProfile::LegacyV001;
        ApplyPressRouteProfile(CompanionRoute, CompanionProfile);
        const FName CompanionTopologyId = MakeTopologyId(
            CompanionRoute, CompanionProfile);

        const bool bSelectedLegacy = IsLegacyRouteTopology(TopologyId);
        const FName ComputedLegacyTopologyId = bSelectedLegacy
            ? TopologyId : CompanionTopologyId;
        const FName ComputedCurrentTopologyId = bSelectedLegacy
            ? CompanionTopologyId : TopologyId;

        for (const FLBOneFactoryVehicleUnitState& Unit : State.Ledger.Units)
        {
            if (Unit.RuntimeStationCursor < 0) continue;
            const bool bTerminal = IsTerminal(Unit);
            const int32 ResolvedProfile =
                ULBOneFactoryProductionFlowLibrary::
                    ResolveRouteProfileVersion(Unit);
            const bool bLegacyProfile = ResolvedProfile ==
                ULBOneFactoryProductionFlowLibrary::LegacyRouteProfileV001;
            const bool bCurrentProfile = ResolvedProfile ==
                ULBOneFactoryProductionFlowLibrary::
                    PressInspectionRouteProfileV002;
            const bool bTopologyAllowed = bLegacyProfile
                ? IsAllowedLegacyRoutedTopology(Unit.RuntimeTopologyId,
                    ComputedLegacyTopologyId)
                : bCurrentProfile
                    && Unit.RuntimeTopologyId == ComputedCurrentTopologyId;
            if (!bTopologyAllowed
                || (!bTerminal && bLegacyProfile != bSelectedLegacy))
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY RUNTIME TOPOLOGY DRIFTED FOR UNIT %s"),
                    *Unit.UnitId.ToString());
                return false;
            }
            if (bTerminal)
            {
                if (StationByUnit.Contains(Unit.UnitId))
                {
                    OutReason = TEXT("ONEFACTORY TERMINAL RUNTIME UNIT RETAINS A WIP RESERVATION");
                    return false;
                }
                continue;
            }
            if (!Route.IsValidIndex(Unit.RuntimeStationCursor))
            {
                OutReason = TEXT("ONEFACTORY ACTIVE RUNTIME CURSOR LEFT THE 57-STATION ROUTE");
                return false;
            }
            const FLBOneFactoryRuntimeStationStep& Step =
                Route[Unit.RuntimeStationCursor];
            if (!StationByUnit.Contains(Unit.UnitId)
                || StationByUnit[Unit.UnitId] != Step.StationId
                || Unit.CurrentStationId != Step.StationId
                || Unit.Department != Step.Department
                || Unit.Stage != Step.SemanticStage
                || Unit.RuntimeCurrentAssignmentId != Step.AssignmentId
                || !FMath::IsNearlyEqual(Unit.RuntimeCycleDurationSeconds,
                    Step.NominalCycleSeconds, CycleToleranceSeconds)
                || (Unit.QualityState ==
                        ELBOneFactoryVehicleQualityState::Pending
                    && !Step.bQualityGate)
                || Unit.PaintProgrammeId != State.Paint.PaintProgrammeId)
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY RUNTIME CURSOR, RESERVATION OR CONFIGURATION DRIFTED FOR %s"),
                    *Unit.UnitId.ToString());
                return false;
            }
        }
        OutReason = TEXT("ONEFACTORY RUNTIME COMPOSITE STATE VALID");
        return true;
    }

    TArray<FName>* FindReservationArray(FSnapshots& State,
        const ELBOneFactoryDepartment Department, const FName StationId)
    {
        switch (Department)
        {
        case ELBOneFactoryDepartment::Press:
            if (FLBOneFactoryPressStarterStationState* Station =
                State.Press.Stations.FindByPredicate([StationId](
                    const FLBOneFactoryPressStarterStationState& Candidate)
                { return Candidate.StationId == StationId; }))
                return &Station->ActiveOrReservedUnitIds;
            break;
        case ELBOneFactoryDepartment::Body:
            if (FLBOneFactoryBodyWeldStationState* Station =
                State.Body.Stations.FindByPredicate([StationId](
                    const FLBOneFactoryBodyWeldStationState& Candidate)
                { return Candidate.StationId == StationId; }))
                return &Station->ActiveOrReservedUnitIds;
            break;
        case ELBOneFactoryDepartment::Paint:
            if (FLBOneFactoryPaintStarterStationState* Station =
                State.Paint.Stations.FindByPredicate([StationId](
                    const FLBOneFactoryPaintStarterStationState& Candidate)
                { return Candidate.StationId == StationId; }))
                return &Station->ActiveOrReservedUnitIds;
            break;
        default:
            if (FLBOneFactoryAssemblyStationState* Station =
                State.Assembly.Stations.FindByPredicate([StationId](
                    const FLBOneFactoryAssemblyStationState& Candidate)
                { return Candidate.StationId == StationId; }))
                return &Station->ActiveOrReservedUnitIds;
            break;
        }
        return nullptr;
    }

    bool AddReservation(FSnapshots& State,
        const FLBOneFactoryRuntimeStationStep& Target, const FName UnitId,
        FString& OutReason)
    {
        TArray<FName>* TargetIds = FindReservationArray(State,
            Target.Department, Target.StationId);
        if (!TargetIds || !TargetIds->IsEmpty())
        {
            OutReason = TEXT("ONEFACTORY RUNTIME TARGET STATION IS MISSING OR OCCUPIED");
            return false;
        }
        TargetIds->Add(UnitId);
        return true;
    }

    bool RemoveReservation(FSnapshots& State,
        const FLBOneFactoryRuntimeStationStep& Source, const FName UnitId,
        FString& OutReason)
    {
        TArray<FName>* SourceIds = FindReservationArray(State,
            Source.Department, Source.StationId);
        if (!SourceIds || SourceIds->Num() != 1 || (*SourceIds)[0] != UnitId)
        {
            OutReason = TEXT("ONEFACTORY RUNTIME SOURCE RESERVATION IS NOT EXACT");
            return false;
        }
        SourceIds->Reset();
        return true;
    }

    void Rollback(const FAuthorities& Actors, const FSnapshots& State)
    {
        FString Ignored;
        Actors.Press->RestoreLayout(State.Press, Ignored);
        Actors.Body->RestoreLayout(State.Body, Ignored);
        Actors.Paint->RestoreLayout(State.Paint, Ignored);
        Actors.Assembly->RestoreLayout(State.Assembly, Ignored);
        Actors.Production->RestoreLedger(State.Ledger, Ignored);
    }

    bool ApplyComposite(const FAuthorities& Actors,
        const FSnapshots& Candidate, const FSnapshots& RollbackState,
        const TArray<FLBOneFactoryRuntimeStationStep>& Route,
        const FName TopologyId, FString& OutReason)
    {
        if (!ValidateComposite(Candidate, Route, TopologyId, OutReason))
            return false;
        FString Detail;
        if (!Actors.Press->RestoreLayout(Candidate.Press, Detail)
            || !Actors.Body->RestoreLayout(Candidate.Body, Detail)
            || !Actors.Paint->RestoreLayout(Candidate.Paint, Detail)
            || !Actors.Assembly->RestoreLayout(Candidate.Assembly, Detail)
            || !Actors.Production->RestoreLedger(Candidate.Ledger, Detail))
        {
            Rollback(Actors, RollbackState);
            OutReason = FString(TEXT("ONEFACTORY RUNTIME TRANSACTION ROLLED BACK: "))
                + Detail;
            return false;
        }
        return true;
    }

    bool ApplyLedgerOnly(const FAuthorities& Actors,
        const FSnapshots& Current, const FLBOneFactoryProductionLedgerState& Ledger,
        const TArray<FLBOneFactoryRuntimeStationStep>& Route,
        const FName TopologyId, FString& OutReason)
    {
        FSnapshots Candidate = Current;
        Candidate.Ledger = Ledger;
        if (!ValidateComposite(Candidate, Route, TopologyId, OutReason))
            return false;
        FString Detail;
        if (!Actors.Production->RestoreLedger(Ledger, Detail))
        {
            FString Ignored;
            Actors.Production->RestoreLedger(Current.Ledger, Ignored);
            OutReason = FString(TEXT("ONEFACTORY RUNTIME LEDGER COMMIT ROLLED BACK: "))
                + Detail;
            return false;
        }
        return true;
    }

    bool CurrentOperationalGateAllowsCycle(const FSnapshots& State,
        const ELBOneFactoryDepartment Department, FString& OutReason)
    {
        if (State.Ledger.bLinePaused)
        {
            OutReason = TEXT("ONEFACTORY RUNTIME HOLD: LINE PAUSED");
            return false;
        }
        if (!LedgerDepartmentCommissioned(State.Ledger, Department)
            || !LayoutDepartmentCommissioned(State, Department))
        {
            OutReason = TEXT("ONEFACTORY RUNTIME HOLD: CURRENT DEPARTMENT UNCOMMISSIONED");
            return false;
        }
        if (State.Ledger.FaultedDepartments.Contains(Department))
        {
            OutReason = TEXT("ONEFACTORY RUNTIME HOLD: CURRENT DEPARTMENT FAULTED");
            return false;
        }
        return true;
    }

    bool TargetGateAllowsTransfer(const FSnapshots& State,
        const ELBOneFactoryDepartment Department, FString& OutReason)
    {
        if (!LedgerDepartmentCommissioned(State.Ledger, Department)
            || !LayoutDepartmentCommissioned(State, Department))
        {
            OutReason = TEXT("ONEFACTORY RUNTIME HOLD: TARGET DEPARTMENT UNCOMMISSIONED");
            return false;
        }
        if (State.Ledger.FaultedDepartments.Contains(Department))
        {
            OutReason = TEXT("ONEFACTORY RUNTIME HOLD: TARGET DEPARTMENT FAULTED");
            return false;
        }
        return true;
    }

    bool EvidenceExists(const FLBOneFactoryProductionLedgerState& Ledger,
        const FName EvidenceId)
    {
        for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
            if (Unit.EvidenceIds.Contains(EvidenceId)) return true;
        return false;
    }

    FName MakeStationEvidence(const FLBOneFactoryVehicleUnitState& Unit,
        const FLBOneFactoryRuntimeStationStep& Step)
    {
        return FName(*FString::Printf(TEXT("OF_%s_STATION_%02d_A%08X"),
            *Unit.UnitId.ToString(), Step.RouteIndex + 1,
            FCrc::StrCrc32(*Step.AssignmentId.ToString())));
    }

    bool AddEvidence(FLBOneFactoryProductionLedgerState& Ledger,
        FLBOneFactoryVehicleUnitState& Unit, const FName EvidenceId,
        FString& OutReason)
    {
        if (EvidenceId.IsNone() || EvidenceExists(Ledger, EvidenceId))
        {
            OutReason = TEXT("ONEFACTORY RUNTIME EVIDENCE ID IS EMPTY OR DUPLICATED");
            return false;
        }
        Unit.EvidenceIds.Add(EvidenceId);
        return true;
    }

    bool StampRequiredPanelBOM(FLBOneFactoryProductionLedgerState& Ledger,
        FLBOneFactoryVehicleUnitState& Unit, FString& OutReason)
    {
        if (Unit.RequiredPanelTypeIds.IsEmpty()
            || Unit.RequiredPanelTypeIds.Contains(NAME_None)
            || !Unit.PressedPanelTypeIds.IsEmpty())
        {
            OutReason = TEXT("ONEFACTORY PRESS CANNOT STAMP A MISSING OR ALREADY-STAMPED ORDER PANEL BOM");
            return false;
        }
        TSet<FName> UniquePanels;
        for (const FName PanelId : Unit.RequiredPanelTypeIds)
        {
            if (UniquePanels.Contains(PanelId)
                || Unit.PressedPanelTypeIds.Contains(PanelId)
                || !AddEvidence(Ledger, Unit,
                    FName(*FString::Printf(TEXT("OF_%s_PANEL_%s_STAMPED"),
                        *Unit.UnitId.ToString(), *PanelId.ToString())),
                    OutReason))
            {
                OutReason = TEXT("ONEFACTORY PRESS PANEL BOM STAMP EVIDENCE IS INVALID");
                return false;
            }
            UniquePanels.Add(PanelId);
            Unit.PressedPanelTypeIds.Add(PanelId);
        }
        return true;
    }

    bool HasCompleteStampedPanelBOM(const FLBOneFactoryVehicleUnitState& Unit)
    {
        if (Unit.RequiredPanelTypeIds.IsEmpty()
            || Unit.RequiredPanelTypeIds.Num() != Unit.PressedPanelTypeIds.Num())
        {
            return false;
        }
        for (const FName PanelId : Unit.RequiredPanelTypeIds)
        {
            if (PanelId.IsNone() || !Unit.PressedPanelTypeIds.Contains(PanelId))
            {
                return false;
            }
        }
        return true;
    }
}

ALBOneFactoryRuntimeCoordinator::ALBOneFactoryRuntimeCoordinator()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    SetReplicates(false);
    SetActorEnableCollision(false);
    Tags.AddUnique(GetCoordinatorTag());
    Tags.AddUnique(TEXT("LB.Provenance.NativeOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
}

FName ALBOneFactoryRuntimeCoordinator::GetCoordinatorTag()
{
    return TEXT("LB.OneFactory.RuntimeCoordinator.Authority.v001");
}

void ALBOneFactoryRuntimeCoordinator::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bAdvanceStartedVehiclesOnActorTick || DeltaSeconds <= 0.0f) return;
    int32 Processed = 0;
    FString Ignored;
    TickAutomaticFlow(DeltaSeconds * RuntimeTimeScale, Processed, Ignored);
}

bool ALBOneFactoryRuntimeCoordinator::SetRuntimeTimeScale(
    const float InTimeScale, FString& OutReason)
{
    if (!FMath::IsFinite(InTimeScale) || InTimeScale < 0.25f
        || InTimeScale > 4.0f)
    {
        OutReason = TEXT(
            "ONEFACTORY RUNTIME TIME SCALE MUST BE FINITE AND BETWEEN 0.25 AND 4.0");
        return false;
    }
    RuntimeTimeScale = InTimeScale;
    OutReason = FString::Printf(TEXT("ONEFACTORY RUNTIME TIME SCALE SET TO %.2f"),
        RuntimeTimeScale);
    return true;
}

bool ALBOneFactoryRuntimeCoordinator::GetConfiguredStationRoute(
    TArray<FLBOneFactoryRuntimeStationStep>& OutRoute, FName& OutTopologyId,
    FString& OutReason) const
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    FAuthorities Actors;
    if (!ResolveAuthorities(*this, Actors, OutReason)) return false;
    return BuildRoute(Capture(Actors), OutRoute, OutTopologyId, OutReason);
}

bool ALBOneFactoryRuntimeCoordinator::ValidateRuntimeFactory(
    FString& OutReason) const
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    FAuthorities Actors;
    if (!ResolveAuthorities(*this, Actors, OutReason)) return false;
    const FSnapshots State = Capture(Actors);
    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    return BuildRoute(State, Route, TopologyId, OutReason)
        && ValidateComposite(State, Route, TopologyId, OutReason);
}

bool ALBOneFactoryRuntimeCoordinator::CreateRuntimeVehicleOrder(
    const FName BuildOrderId, const FName VehicleModelId,
    const FName PaintProgrammeId, const FName PaintColourId,
    const FName SourceCoilLotId, FName& OutUnitId, FString& OutReason)
{
    return CreateRuntimeVehicleOrderInternal(BuildOrderId, VehicleModelId,
        PaintProgrammeId, PaintColourId, SourceCoilLotId, false, OutUnitId,
        OutReason);
}

bool ALBOneFactoryRuntimeCoordinator::CreateRuntimeVehicleOrderInternal(
    const FName BuildOrderId, const FName VehicleModelId,
    const FName PaintProgrammeId, const FName PaintColourId,
    const FName SourceCoilLotId, const bool bStartImmediately,
    FName& OutUnitId, FString& OutReason)
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    OutUnitId = NAME_None;
    FAuthorities Actors;
    if (!ResolveAuthorities(*this, Actors, OutReason)) return false;
    const FSnapshots RollbackState = Capture(Actors);
    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    if (!BuildRoute(RollbackState, Route, TopologyId, OutReason)
        || !ValidateComposite(RollbackState, Route, TopologyId, OutReason))
        return false;
    if (IsLegacyRouteTopology(TopologyId))
    {
        OutReason = TEXT(
            "ONEFACTORY V002 ADMISSION HOLD: ACTIVE V001 ROUTE WIP MUST DRAIN FIRST (INCLUDING UNVERSIONED MANUAL GENEALOGY)");
        return false;
    }
    if (HasActiveManualWIP(RollbackState.Ledger))
    {
        OutReason = TEXT(
            "ONEFACTORY V002 ROUTED ADMISSION HOLD: ACTIVE MANUAL WIP MUST DRAIN FIRST");
        return false;
    }
    if (VehicleModelId != RollbackState.Body.VehicleModelId
        || PaintProgrammeId != RollbackState.Paint.PaintProgrammeId)
    {
        OutReason = TEXT("ONEFACTORY VEHICLE ORDER DISAGREES WITH CONFIGURED MODEL OR PAINT PROGRAMME");
        return false;
    }
    for (int32 DepartmentIndex = 0; DepartmentIndex < 4; ++DepartmentIndex)
    {
        const ELBOneFactoryDepartment Department =
            static_cast<ELBOneFactoryDepartment>(DepartmentIndex);
        if (!LedgerDepartmentCommissioned(RollbackState.Ledger, Department)
            || !LayoutDepartmentCommissioned(RollbackState, Department))
        {
            OutReason = TEXT("ONEFACTORY ALL FOUR DEPARTMENTS MUST BE COMMISSIONED BEFORE STARTING A CAR");
            return false;
        }
    }
    const FLBOneFactoryPressStarterStationState* InboundStation =
        RollbackState.Press.Stations.FindByPredicate([&Route](
            const FLBOneFactoryPressStarterStationState& Station)
        { return Station.StationId == Route[0].StationId; });
    if (!InboundStation || !InboundStation->ActiveOrReservedUnitIds.IsEmpty())
    {
        OutReason = TEXT("ONEFACTORY PRESS INBOUND IS ALREADY RESERVED");
        return false;
    }

    if (!Actors.Production->CreateRoutedVehicleOrder(
            BuildOrderId, VehicleModelId,
            PaintProgrammeId, PaintColourId, SourceCoilLotId,
            Route[0].StationId, OutUnitId, OutReason))
        return false;

    FSnapshots Candidate = RollbackState;
    Candidate.Ledger = Actors.Production->CaptureLedger();
    FLBOneFactoryVehicleUnitState* Unit = FindUnit(Candidate.Ledger, OutUnitId);
    if (!Unit || !AddReservation(Candidate, Route[0], OutUnitId, OutReason))
    {
        Rollback(Actors, RollbackState);
        OutUnitId = NAME_None;
        return false;
    }
    Unit->RuntimeStationCursor = 0;
    Unit->RuntimeCompletedStationCount = 0;
    Unit->RuntimeTotalStationCount = RequiredPhysicalStationCount;
    Unit->RuntimeCycleElapsedSeconds = 0.0f;
    Unit->RuntimeCycleDurationSeconds = Route[0].NominalCycleSeconds;
    Unit->RuntimeTopologyId = TopologyId;
    Unit->RuntimeCurrentAssignmentId = Route[0].AssignmentId;
    Unit->bRuntimeStarted = bStartImmediately;
    Unit->Stage = Route[0].SemanticStage;
    Unit->Department = Route[0].Department;
    Unit->CurrentStationId = Route[0].StationId;
    if (!ApplyComposite(Actors, Candidate, RollbackState, Route, TopologyId,
            OutReason))
    {
        Rollback(Actors, RollbackState);
        OutUnitId = NAME_None;
        return false;
    }
    OutReason = bStartImmediately
        ? TEXT("ONEFACTORY AUTOMATION CREATED AND STARTED ONE CONTRACT VEHICLE")
        : TEXT("ONEFACTORY VEHICLE CREATED WITH EXACTLY ONE PRESS-INBOUND RESERVATION");
    return true;
}

bool ALBOneFactoryRuntimeCoordinator::DispatchNextOpenContract(
    FName& OutUnitId, FString& OutReason)
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    OutUnitId = NAME_None;
    FAuthorities Actors;
    if (!ResolveAuthorities(*this, Actors, OutReason)) return false;
    const FSnapshots State = Capture(Actors);
    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    if (!BuildRoute(State, Route, TopologyId, OutReason)
        || !ValidateComposite(State, Route, TopologyId, OutReason))
        return false;
    if (IsLegacyRouteTopology(TopologyId))
    {
        // This is an expected soft hold, not corruption: existing V001 work
        // keeps advancing, while automatic dispatch cannot prolong the legacy
        // profile by admitting another V001 unit.
        OutReason = TEXT(
            "ONEFACTORY AUTOMATION HOLDS NEW ADMISSION WHILE V001 ROUTE WIP DRAINS");
        return true;
    }
    if (HasActiveManualWIP(State.Ledger))
    {
        OutReason = TEXT(
            "ONEFACTORY AUTOMATION HOLDS NEW ROUTED ADMISSION WHILE MANUAL WIP DRAINS");
        return true;
    }

    const FName ConfiguredModelId = State.Paint.VehicleModelId;
    const FName ConfiguredPaintProgrammeId = State.Paint.PaintProgrammeId;
    const FName ConfiguredPaintColourId = PaintColourId(
        State.Paint.SelectedBodyColour);
    if (ConfiguredModelId.IsNone() || ConfiguredPaintProgrammeId.IsNone()
        || ConfiguredPaintColourId.IsNone())
    {
        OutReason = TEXT("ONEFACTORY AUTOMATION REQUIRES A COMPLETE PAINT PROGRAMME CONFIGURATION");
        return false;
    }

    int32 RemainingContractVehicles = 0;
    for (const FLBOneFactoryVehicleContract& Contract : State.Ledger.Contracts)
    {
        if (Contract.State == ELBOneFactoryContractState::Open
            && Contract.VehicleModelId == ConfiguredModelId)
        {
            RemainingContractVehicles += Contract.Quantity
                - Contract.DispatchedCount;
        }
    }
    int32 ActiveVehiclesForModel = 0;
    for (const FLBOneFactoryVehicleUnitState& Unit : State.Ledger.Units)
    {
        if (Unit.VehicleModelId == ConfiguredModelId && !IsTerminal(Unit))
            ++ActiveVehiclesForModel;
    }
    if (RemainingContractVehicles <= ActiveVehiclesForModel)
    {
        OutReason = TEXT("ONEFACTORY AUTOMATION HAS NO UNSCHEDULED COMPATIBLE CONTRACT WORK");
        return true;
    }
    if (ActiveVehiclesForModel >= State.Ledger.MaximumConcurrentWIP)
    {
        OutReason = TEXT("ONEFACTORY AUTOMATION IS HOLDING AT THE CONFIGURED WIP LIMIT");
        return true;
    }

    const int32 Serial = State.Ledger.NextVehicleSerial;
    const FName BuildOrderId(*FString::Printf(TEXT("OF_AUTO_BUILD_%06d"),
        Serial));
    const FName CoilLotId(*FString::Printf(TEXT("OF_AUTO_COIL_LOT_%06d"),
        Serial));
    if (!CreateRuntimeVehicleOrderInternal(BuildOrderId, ConfiguredModelId,
            ConfiguredPaintProgrammeId, ConfiguredPaintColourId, CoilLotId,
            true, OutUnitId, OutReason))
    {
        OutUnitId = NAME_None;
        return false;
    }
    OutReason = FString::Printf(
        TEXT("ONEFACTORY AUTOMATION STARTED %s FOR THE OLDEST COMPATIBLE OPEN CONTRACT"),
        *OutUnitId.ToString());
    return true;
}

bool ALBOneFactoryRuntimeCoordinator::StartVehicle(const FName UnitId,
    FString& OutReason)
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    FAuthorities Actors;
    if (!ResolveAuthorities(*this, Actors, OutReason)) return false;
    const FSnapshots Current = Capture(Actors);
    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    if (!BuildRoute(Current, Route, TopologyId, OutReason)
        || !ValidateComposite(Current, Route, TopologyId, OutReason))
        return false;
    FLBOneFactoryProductionLedgerState Candidate = Current.Ledger;
    FLBOneFactoryVehicleUnitState* Unit = FindUnit(Candidate, UnitId);
    if (!Unit || Unit->RuntimeStationCursor < 0 || IsTerminal(*Unit))
    {
        OutReason = TEXT("ONEFACTORY RUNTIME START REQUIRES AN ACTIVE RESERVED UNIT");
        return false;
    }
    if (Unit->bRuntimeStarted)
    {
        OutReason = TEXT("ONEFACTORY RUNTIME UNIT IS ALREADY STARTED");
        return true;
    }
    FString GateReason;
    if (!CurrentOperationalGateAllowsCycle(Current, Unit->Department, GateReason))
    {
        OutReason = GateReason;
        return false;
    }
    Unit->bRuntimeStarted = true;
    NormalizeFrozenV001TopologyAliasForMutation(
        Candidate, UnitId, TopologyId);
    ++Candidate.Revision;
    if (!ApplyLedgerOnly(Actors, Current, Candidate, Route, TopologyId,
            OutReason))
        return false;
    OutReason = TEXT("ONEFACTORY RUNTIME UNIT STARTED");
    return true;
}

bool ALBOneFactoryRuntimeCoordinator::TickVehicle(const FName UnitId,
    const float DeltaSeconds, FString& OutReason)
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.0f)
    {
        OutReason = TEXT("ONEFACTORY RUNTIME DELTA MUST BE FINITE AND POSITIVE");
        return false;
    }
    FAuthorities Actors;
    if (!ResolveAuthorities(*this, Actors, OutReason)) return false;
    const FSnapshots Current = Capture(Actors);
    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    if (!BuildRoute(Current, Route, TopologyId, OutReason)
        || !ValidateComposite(Current, Route, TopologyId, OutReason))
        return false;
    const FLBOneFactoryVehicleUnitState* Existing =
        FindUnit(Current.Ledger, UnitId);
    if (!Existing || IsTerminal(*Existing)
        || !Route.IsValidIndex(Existing->RuntimeStationCursor))
    {
        OutReason = TEXT("ONEFACTORY RUNTIME TICK REQUIRES ACTIVE ROUTED WIP");
        return false;
    }
    if (!Existing->bRuntimeStarted)
    {
        OutReason = TEXT("ONEFACTORY RUNTIME UNIT HAS NOT BEEN STARTED");
        return false;
    }
    if (!CurrentOperationalGateAllowsCycle(Current, Existing->Department,
            OutReason))
        return true;

    const FLBOneFactoryRuntimeStationStep& SourceStep =
        Route[Existing->RuntimeStationCursor];
    FLBOneFactoryProductionLedgerState CandidateLedger = Current.Ledger;
    // Normalize only the transactional candidate. A failed/no-op hold leaves
    // the loaded alias byte-identical; the first actual commit restamps it.
    NormalizeFrozenV001TopologyAliasForMutation(
        CandidateLedger, UnitId, TopologyId);
    FLBOneFactoryVehicleUnitState* Unit = FindUnit(CandidateLedger, UnitId);
    check(Unit);
    const float NewElapsed = FMath::Min(Unit->RuntimeCycleDurationSeconds,
        Unit->RuntimeCycleElapsedSeconds + DeltaSeconds);
    const bool bElapsedChanged = !FMath::IsNearlyEqual(NewElapsed,
        Unit->RuntimeCycleElapsedSeconds, CycleToleranceSeconds);
    Unit->RuntimeCycleElapsedSeconds = NewElapsed;

    auto CommitElapsedHold = [&](const TCHAR* Reason) -> bool
    {
        if (bElapsedChanged)
        {
            ++CandidateLedger.Revision;
            if (!ApplyLedgerOnly(Actors, Current, CandidateLedger, Route,
                    TopologyId, OutReason))
                return false;
        }
        OutReason = Reason;
        return true;
    };

    if (NewElapsed + CycleToleranceSeconds
        < Unit->RuntimeCycleDurationSeconds)
    {
        ++CandidateLedger.Revision;
        if (!ApplyLedgerOnly(Actors, Current, CandidateLedger, Route,
                TopologyId, OutReason))
            return false;
        OutReason = TEXT("ONEFACTORY RUNTIME CYCLE PROGRESSED");
        return true;
    }

    if (SourceStep.bQualityGate
        && Unit->QualityState != ELBOneFactoryVehicleQualityState::Passed)
    {
        switch (Unit->QualityState)
        {
        case ELBOneFactoryVehicleQualityState::Pending:
            return CommitElapsedHold(
                TEXT("ONEFACTORY RUNTIME QUALITY HOLD: RESULT REQUIRED"));
        case ELBOneFactoryVehicleQualityState::ReworkRequired:
            return CommitElapsedHold(
                TEXT("ONEFACTORY RUNTIME QUALITY HOLD: REWORK REQUIRED"));
        case ELBOneFactoryVehicleQualityState::Rejected:
            return CommitElapsedHold(
                TEXT("ONEFACTORY RUNTIME QUALITY HOLD: UNIT REJECTED"));
        default:
            OutReason = TEXT("ONEFACTORY RUNTIME QUALITY STATE CANNOT LEAVE INSPECTION");
            return false;
        }
    }
    if (Current.Ledger.OutputBlockedDepartments.Contains(Unit->Department))
        return CommitElapsedHold(
            TEXT("ONEFACTORY RUNTIME OUTPUT HOLD: CURRENT DEPARTMENT BLOCKED"));

    FSnapshots Candidate = Current;
    Candidate.Ledger = CandidateLedger;
    Unit = FindUnit(Candidate.Ledger, UnitId);
    check(Unit);
    if (!RemoveReservation(Candidate, SourceStep, UnitId, OutReason))
        return false;
    const FName StationEvidence = MakeStationEvidence(*Unit, SourceStep);
    if (!AddEvidence(Candidate.Ledger, *Unit, StationEvidence, OutReason))
        return false;
    if (SourceStep.StationId == LBOneFactoryPressStarterIds::PressTrain())
    {
        if (!StampRequiredPanelBOM(Candidate.Ledger, *Unit, OutReason))
        {
            return false;
        }
    }
    if (Unit->RouteProfileVersion ==
        ULBOneFactoryProductionFlowLibrary::UnversionedRouteProfile)
    {
        // Persist the conservative inference on the first committed runtime
        // mutation. Merely validating/loading an old save remains read-only.
        Unit->RouteProfileVersion = IsLegacyRouteTopology(TopologyId)
            ? ULBOneFactoryProductionFlowLibrary::LegacyRouteProfileV001
            : ULBOneFactoryProductionFlowLibrary::
                PressInspectionRouteProfileV002;
    }
    ++Unit->StageRevision;
    ++Unit->RuntimeCompletedStationCount;

    const int32 NextCursor = Unit->RuntimeStationCursor + 1;
    if (Route.IsValidIndex(NextCursor))
    {
        const FLBOneFactoryRuntimeStationStep& TargetStep = Route[NextCursor];
        if (TargetStep.SemanticStage == ELBOneFactoryVehicleStage::BodyFraming
            && !HasCompleteStampedPanelBOM(*Unit))
        {
            OutReason = TEXT("ONEFACTORY BODY FRAMING REQUIRES THE COMPLETE MODEL-MATCHED PRESSED PANEL BOM");
            return false;
        }
        if (!TargetGateAllowsTransfer(Current, TargetStep.Department, OutReason))
        {
            const FString HoldReason = OutReason;
            return CommitElapsedHold(*HoldReason);
        }
        if (!AddReservation(Candidate, TargetStep, UnitId, OutReason))
            return CommitElapsedHold(
                TEXT("ONEFACTORY RUNTIME TRANSFER HOLD: TARGET STATION OCCUPIED"));
        // Measured cars/hour: the leaving station's department completed
        // one cycle at this sim time.
        RecordStationCompletion(SourceStep.Department,
            CandidateLedger.SimClockSeconds);
        // The physical route is the live production path.  Keep its wear and
        // deterministic quality-risk state in step with the logical ledger
        // path so maintenance and inspection decisions have real gameplay
        // consequences rather than remaining test-only bookkeeping.
        Candidate.Ledger.FleetWear01 = FMath::Min(1.0,
            Candidate.Ledger.FleetWear01 + 0.0004);
        Unit->RuntimeStationCursor = NextCursor;
        Unit->RuntimeCycleElapsedSeconds = 0.0f;
        Unit->RuntimeCycleDurationSeconds = TargetStep.NominalCycleSeconds;
        Unit->RuntimeCurrentAssignmentId = TargetStep.AssignmentId;
        Unit->CurrentStationId = TargetStep.StationId;
        Unit->Department = TargetStep.Department;
        Unit->Stage = TargetStep.SemanticStage;
        if (TargetStep.bQualityGate)
        {
            Unit->QualityState = ELBOneFactoryVehicleQualityState::Pending;
            Unit->bDefectSuspected =
                ULBOneFactoryProductionFlowLibrary::IsDefectSuspected(
                    Unit->UnitId, Candidate.Ledger.FleetWear01);
        }
        if (TargetStep.SemanticStage
            == ELBOneFactoryVehicleStage::FinishedVehicle)
        {
            if (!AddEvidence(Candidate.Ledger, *Unit,
                    FName(*FString::Printf(TEXT("OF_%s_FINISHED"),
                        *Unit->UnitId.ToString())), OutReason))
                return false;
            Unit->bCompleted = true;
            ++Unit->StageRevision;
            ++Candidate.Ledger.CompletedVehicleCount;
        }
        ++Candidate.Ledger.Revision;
        if (!ApplyComposite(Actors, Candidate, Current, Route, TopologyId,
                OutReason))
            return false;
        OutReason = FString::Printf(
            TEXT("ONEFACTORY RUNTIME TRANSFERRED UNIT TO STATION %d OF 57"),
            NextCursor + 1);
        return true;
    }

    if (Unit->Stage != ELBOneFactoryVehicleStage::FinishedVehicle
        || !Unit->bCompleted
        || Unit->QualityState != ELBOneFactoryVehicleQualityState::Passed)
    {
        OutReason = TEXT("ONEFACTORY RUNTIME FINAL DISPATCH REQUIRES PASSED EOL QUALITY");
        return false;
    }
    if (!AddEvidence(Candidate.Ledger, *Unit,
            FName(*FString::Printf(TEXT("OF_%s_DISPATCHED"),
                *Unit->UnitId.ToString())), OutReason))
        return false;
    RecordStationCompletion(ELBOneFactoryDepartment::Assembly,
        Candidate.Ledger.SimClockSeconds);
    Unit->RuntimeStationCursor = RequiredPhysicalStationCount;
    Unit->RuntimeCycleElapsedSeconds = 0.0f;
    Unit->RuntimeCycleDurationSeconds = 0.0f;
    Unit->bRuntimeStarted = false;
    Unit->Stage = ELBOneFactoryVehicleStage::Dispatched;
    Unit->Department = ELBOneFactoryDepartment::Assembly;
    Unit->bDispatched = true;
    // The automatic physical route is the authoritative production path.
    // Settle its dispatch against the oldest matching open contract just as
    // the legacy logical advance path does, so revenue and order state
    // describe the same finished vehicle.
    for (FLBOneFactoryVehicleContract& Contract : Candidate.Ledger.Contracts)
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
    ++Unit->StageRevision;
    ++Candidate.Ledger.DispatchedVehicleCount;
    ++Candidate.Ledger.Revision;
    if (!ApplyComposite(Actors, Candidate, Current, Route, TopologyId,
            OutReason))
        return false;
    OutReason = TEXT("ONEFACTORY RUNTIME COMPLETED AND DISPATCHED ONE LOGICAL VEHICLE");
    return true;
}

bool ALBOneFactoryRuntimeCoordinator::TickAutomaticFlow(
    const float DeltaSeconds, int32& OutProcessedUnitCount,
    FString& OutReason)
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    OutProcessedUnitCount = 0;
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.0f)
    {
        OutReason = TEXT("ONEFACTORY AUTOMATIC FLOW DELTA MUST BE FINITE AND POSITIVE");
        return false;
    }
    FAuthorities Actors;
    if (!ResolveAuthorities(*this, Actors, OutReason)) return false;
    // Factory time flows whenever the line is unpaused, even with no started
    // units - deadlines and running costs do not wait for orders.
    FString ClockReason;
    Actors.Production->AdvanceSimulationClock(DeltaSeconds, ClockReason);
    FString SweepReason;
    Actors.Production->SweepContractDeadlines(SweepReason);
    TArray<FName> StartedUnits;
    for (const FLBOneFactoryVehicleUnitState& Unit :
        Actors.Production->CaptureLedger().Units)
    {
        if (Unit.bRuntimeStarted && !IsTerminal(Unit))
            StartedUnits.Add(Unit.UnitId);
    }
    StartedUnits.Sort([](const FName Left, const FName Right)
    { return Left.ToString() < Right.ToString(); });
    for (const FName UnitId : StartedUnits)
    {
        if (!TickVehicle(UnitId, DeltaSeconds, OutReason)) return false;
        ++OutProcessedUnitCount;
    }
    if (bAutoDispatchOpenContracts)
    {
        FName AutoStartedUnitId = NAME_None;
        FString AutomationReason;
        if (!DispatchNextOpenContract(AutoStartedUnitId, AutomationReason))
        {
            OutReason = AutomationReason;
            return false;
        }
        if (!AutoStartedUnitId.IsNone())
        {
            ++OutProcessedUnitCount;
            OutReason = AutomationReason;
        }
    }
    // Non-fatal: the economy reconciles from deterministic ids, so a missing
    // management subsystem (some validation worlds) must not stop the line.
    FString EconomyReason;
    ReconcileEconomy(EconomyReason);
    OutReason = StartedUnits.IsEmpty()
        ? TEXT("ONEFACTORY AUTOMATIC FLOW IDLE")
        : TEXT("ONEFACTORY AUTOMATIC FLOW TICKED STARTED UNITS DETERMINISTICALLY");
    return true;
}

void ALBOneFactoryRuntimeCoordinator::RecordStationCompletion(
    const ELBOneFactoryDepartment Department, const double SimSeconds)
{
    constexpr int32 RingCap = 4096;
    CompletionStamps.Emplace(Department, SimSeconds);
    if (CompletionStamps.Num() > RingCap)
    {
        CompletionStamps.RemoveAt(0, CompletionStamps.Num() - RingCap,
            EAllowShrinking::No);
    }
}

float ALBOneFactoryRuntimeCoordinator::MeasuredRatePerHour(
    const ELBOneFactoryDepartment Department, const double NowSimSeconds,
    const float WindowSimSeconds) const
{
    if (WindowSimSeconds <= 0.0f)
    {
        return 0.0f;
    }
    const double WindowStart = NowSimSeconds - WindowSimSeconds;
    int32 Count = 0;
    for (const TPair<ELBOneFactoryDepartment, double>& Stamp :
        CompletionStamps)
    {
        if (Stamp.Key == Department && Stamp.Value > WindowStart
            && Stamp.Value <= NowSimSeconds)
        {
            ++Count;
        }
    }
    return static_cast<float>(Count) * 3600.0f / WindowSimSeconds;
}

bool ALBOneFactoryRuntimeCoordinator::ReconcileEconomy(FString& OutReason)
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    // The plant operating cost remains a site policy. Vehicle spot value is
    // deliberately held by the model recipe so future programmes can have
    // their own economics without another coordinator branch.
    constexpr int64 PlantOperatingCostPencePerHour = 150000;
    // Completing a sale is also the programme's evidence-backed progression
    // event. Keep it tied to the same idempotent unit identity as revenue so
    // reloading or repeatedly reconciling cannot farm research points.
    constexpr int64 VehicleDispatchResearchPoints = 5;

    UWorld* World = GetWorld();
    ULBFactoryManagementSubsystem* Management =
        World ? World->GetSubsystem<ULBFactoryManagementSubsystem>() : nullptr;
    FAuthorities Actors;
    if (!Management || !ResolveAuthorities(*this, Actors, OutReason))
    {
        OutReason = TEXT("ONEFACTORY ECONOMY REQUIRES MANAGEMENT AND PRODUCTION AUTHORITIES");
        return false;
    }
    if (!Management->IsCampaignInitialised()
        && !Management->InitialiseNewCampaign(
            ULBFactoryManagementSubsystem::DefaultStartingCashPence, 0))
    {
        OutReason = TEXT("ONEFACTORY ECONOMY COULD NOT INITIALISE THE CAMPAIGN");
        return false;
    }
    const FLBOneFactoryProductionLedgerState Ledger =
        Actors.Production->CaptureLedger();
    int32 RevenuePosted = 0;
    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        if (!Unit.bDispatched)
        {
            continue;
        }
        const FLBVehicleModelRecipe* Recipe =
            LBVehicleModelCatalog::Find(Unit.VehicleModelId);
        if (!Recipe || Recipe->DefaultRevenuePence <= 0)
        {
            OutReason = FString::Printf(
                TEXT("ONEFACTORY ECONOMY REJECTED UNPRICED VEHICLE PROGRAMME: %s"),
                *Unit.VehicleModelId.ToString());
            return false;
        }
        // Contract price when the unit settled one; its registered programme
        // spot price otherwise.
        int64 UnitPrice = Recipe->DefaultRevenuePence;
        if (!Unit.FulfilledContractId.IsNone())
        {
            for (const FLBOneFactoryVehicleContract& Contract :
                Ledger.Contracts)
            {
                if (Contract.ContractId == Unit.FulfilledContractId)
                {
                    UnitPrice = Contract.PricePerVehiclePence;
                    break;
                }
            }
        }
        const FName TransactionId(*FString::Printf(TEXT("OF_REV_%s"),
            *Unit.UnitId.ToString()));
        if (Management->TryRecordOrderRevenue(TransactionId, Unit.UnitId,
                UnitPrice))
        {
            const FName ResearchEventId(*FString::Printf(TEXT("OF_RP_%s"),
                *Unit.UnitId.ToString()));
            Management->GrantResearchPoints(ResearchEventId, Unit.UnitId,
                VehicleDispatchResearchPoints);
            ++RevenuePosted;
        }
    }
    int32 HoursCharged = 0;
    const int64 CompletedHours =
        static_cast<int64>(Ledger.SimClockSeconds / 3600.0);
    // Hour h completes when the clock passes h*3600, so charging starts at
    // hour 1 - there is no hour zero to pay for.
    for (int64 Hour = FMath::Max<int64>(LastChargedOpexHour + 1, 1);
         Hour <= CompletedHours; ++Hour)
    {
        const FName TransactionId(*FString::Printf(TEXT("OF_OPEX_H%lld"),
            Hour));
        if (Management->TryChargeOperatingCost(TransactionId,
                FName(TEXT("OF_PLANT")), PlantOperatingCostPencePerHour))
        {
            ++HoursCharged;
        }
    }
    LastChargedOpexHour = FMath::Max(LastChargedOpexHour, CompletedHours);
    FString PolicyReason;
    Actors.Production->ApplyFinancialPolicy(
        Management->GetCashBalancePence(), PolicyReason);
    OutReason = FString::Printf(
        TEXT("ONEFACTORY ECONOMY RECONCILED: %d revenue, %d opex hour(s)"),
        RevenuePosted, HoursCharged);
    return true;
}

bool ALBOneFactoryRuntimeCoordinator::PerformPlantMaintenance(
    FString& OutReason)
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    constexpr int64 MaintenanceFeePence = 2500000;

    UWorld* World = GetWorld();
    ULBFactoryManagementSubsystem* Management =
        World ? World->GetSubsystem<ULBFactoryManagementSubsystem>() : nullptr;
    FAuthorities Actors;
    if (!Management || !ResolveAuthorities(*this, Actors, OutReason))
    {
        OutReason = TEXT("ONEFACTORY MAINTENANCE REQUIRES MANAGEMENT AND PRODUCTION");
        return false;
    }
    const FLBOneFactoryProductionLedgerState Ledger =
        Actors.Production->CaptureLedger();
    if (Ledger.FleetWear01 <= 0.0)
    {
        OutReason = TEXT("ONEFACTORY FLEET HAS NO WEAR TO SERVICE");
        return true;
    }
    const FName TransactionId(*FString::Printf(TEXT("OF_MAINT_%d"),
        Ledger.MaintenanceSerial + 1));
    if (!Management->TryChargeOperatingCost(TransactionId,
            FName(TEXT("OF_PLANT_MAINTENANCE")), MaintenanceFeePence))
    {
        OutReason = TEXT("ONEFACTORY MAINTENANCE FEE COULD NOT BE CHARGED");
        return false;
    }
    return Actors.Production->PerformPlantMaintenance(OutReason);
}

bool ALBOneFactoryRuntimeCoordinator::SubmitRuntimeQualityResult(
    const FName UnitId,
    const ELBOneFactoryVehicleQualityState QualityState,
    const FName EvidenceId, FString& OutReason)
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    FAuthorities Actors;
    if (!ResolveAuthorities(*this, Actors, OutReason)) return false;
    const FSnapshots Current = Capture(Actors);
    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    if (!BuildRoute(Current, Route, TopologyId, OutReason)
        || !ValidateComposite(Current, Route, TopologyId, OutReason))
        return false;
    const FLBOneFactoryVehicleUnitState* Unit = FindUnit(Current.Ledger, UnitId);
    if (!Unit || !Route.IsValidIndex(Unit->RuntimeStationCursor)
        || !Route[Unit->RuntimeStationCursor].bQualityGate
        || Unit->RuntimeCycleElapsedSeconds + CycleToleranceSeconds
            < Unit->RuntimeCycleDurationSeconds)
    {
        OutReason = TEXT("ONEFACTORY RUNTIME QUALITY RESULT REQUIRES A COMPLETED INSPECTION CYCLE");
        return false;
    }
    if (!CurrentOperationalGateAllowsCycle(Current, Unit->Department,
            OutReason))
        return false;

    if (!Actors.Production->SubmitQualityResult(UnitId, QualityState,
            EvidenceId, OutReason))
        return false;
    FSnapshots Candidate = Current;
    Candidate.Ledger = Actors.Production->CaptureLedger();
    FLBOneFactoryVehicleUnitState* CandidateUnit =
        FindUnit(Candidate.Ledger, UnitId);
    check(CandidateUnit);
    NormalizeFrozenV001TopologyAliasForMutation(
        Candidate.Ledger, UnitId, TopologyId);
    if (QualityState == ELBOneFactoryVehicleQualityState::Scrapped)
    {
        if (!RemoveReservation(Candidate,
                Route[CandidateUnit->RuntimeStationCursor], UnitId, OutReason))
        {
            Rollback(Actors, Current);
            return false;
        }
        CandidateUnit->bRuntimeStarted = false;
        if (!ApplyComposite(Actors, Candidate, Current, Route, TopologyId,
                OutReason))
        {
            Rollback(Actors, Current);
            return false;
        }
    }
    else if (!ApplyLedgerOnly(Actors, Current, Candidate.Ledger, Route,
            TopologyId, OutReason))
    {
        FString Ignored;
        Actors.Production->RestoreLedger(Current.Ledger, Ignored);
        return false;
    }
    OutReason = TEXT("ONEFACTORY RUNTIME QUALITY RESULT RECORDED WITHOUT DUPLICATING WIP");
    return true;
}

bool ALBOneFactoryRuntimeCoordinator::CompleteRuntimeRework(
    const FName UnitId, const FName EvidenceId, FString& OutReason)
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    FAuthorities Actors;
    if (!ResolveAuthorities(*this, Actors, OutReason)) return false;
    const FSnapshots Current = Capture(Actors);
    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    if (!BuildRoute(Current, Route, TopologyId, OutReason)
        || !ValidateComposite(Current, Route, TopologyId, OutReason))
        return false;
    const FLBOneFactoryVehicleUnitState* Existing =
        FindUnit(Current.Ledger, UnitId);
    if (!Existing || !Route.IsValidIndex(Existing->RuntimeStationCursor)
        || !Route[Existing->RuntimeStationCursor].bQualityGate)
    {
        OutReason = TEXT("ONEFACTORY RUNTIME REWORK REQUIRES CURRENT INSPECTION WIP");
        return false;
    }
    if (!CurrentOperationalGateAllowsCycle(Current, Existing->Department,
            OutReason))
        return false;
    if (!Actors.Production->ResetQualityAfterRework(UnitId, EvidenceId,
            OutReason))
        return false;
    FLBOneFactoryProductionLedgerState Candidate =
        Actors.Production->CaptureLedger();
    FLBOneFactoryVehicleUnitState* Unit = FindUnit(Candidate, UnitId);
    check(Unit);
    Unit->RuntimeCycleElapsedSeconds = 0.0f;
    NormalizeFrozenV001TopologyAliasForMutation(
        Candidate, UnitId, TopologyId);
    ++Candidate.Revision;
    if (!ApplyLedgerOnly(Actors, Current, Candidate, Route, TopologyId,
            OutReason))
    {
        FString Ignored;
        Actors.Production->RestoreLedger(Current.Ledger, Ignored);
        return false;
    }
    OutReason = TEXT("ONEFACTORY RUNTIME REWORK COMPLETE; INSPECTION CYCLE RESET");
    return true;
}

bool ALBOneFactoryRuntimeCoordinator::GetVehicleRuntimeStatus(
    const FName UnitId, FLBOneFactoryRuntimeVehicleStatus& OutStatus,
    FString& OutReason) const
{
    using namespace LBOneFactoryRuntimeCoordinatorPrivate;
    OutStatus = FLBOneFactoryRuntimeVehicleStatus();
    FAuthorities Actors;
    if (!ResolveAuthorities(*this, Actors, OutReason)) return false;
    const FSnapshots State = Capture(Actors);
    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId;
    if (!BuildRoute(State, Route, TopologyId, OutReason)
        || !ValidateComposite(State, Route, TopologyId, OutReason))
        return false;
    const FLBOneFactoryVehicleUnitState* Unit = FindUnit(State.Ledger, UnitId);
    if (!Unit || Unit->RuntimeStationCursor < 0)
    {
        OutReason = TEXT("ONEFACTORY RUNTIME STATUS REQUIRES A ROUTED UNIT");
        return false;
    }
    OutStatus.UnitId = Unit->UnitId;
    OutStatus.CurrentStationId = Unit->CurrentStationId;
    OutStatus.CurrentAssignmentId = Unit->RuntimeCurrentAssignmentId;
    OutStatus.Department = Unit->Department;
    OutStatus.Stage = Unit->Stage;
    OutStatus.QualityState = Unit->QualityState;
    OutStatus.StationCursor = Unit->RuntimeStationCursor;
    OutStatus.CompletedStationCount = Unit->RuntimeCompletedStationCount;
    OutStatus.StageRevision = Unit->StageRevision;
    OutStatus.TotalStationCount = Unit->RuntimeTotalStationCount;
    OutStatus.CycleElapsedSeconds = Unit->RuntimeCycleElapsedSeconds;
    OutStatus.CycleDurationSeconds = Unit->RuntimeCycleDurationSeconds;
    OutStatus.NormalizedCycleProgress = Unit->RuntimeCycleDurationSeconds > 0.0f
        ? FMath::Clamp(Unit->RuntimeCycleElapsedSeconds
            / Unit->RuntimeCycleDurationSeconds, 0.0f, 1.0f)
        : Unit->bDispatched ? 1.0f : 0.0f;
    OutStatus.bStarted = Unit->bRuntimeStarted;
    if (Route.IsValidIndex(Unit->RuntimeStationCursor))
    {
        OutStatus.bAtQualityGate =
            Route[Unit->RuntimeStationCursor].bQualityGate;
        OutStatus.bAwaitingQualityResult = OutStatus.bAtQualityGate
            && Unit->QualityState == ELBOneFactoryVehicleQualityState::Pending
            && OutStatus.NormalizedCycleProgress >= 1.0f;
    }
    OutStatus.bCompleted = Unit->bCompleted;
    OutStatus.bDispatched = Unit->bDispatched;
    OutReason = TEXT("ONEFACTORY RUNTIME VEHICLE STATUS VALID");
    return true;
}
