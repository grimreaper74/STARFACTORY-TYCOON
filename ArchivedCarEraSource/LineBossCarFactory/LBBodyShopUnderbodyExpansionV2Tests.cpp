#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopUnderbodyExpansionV2.h"

#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopUnderbodyExpansionCatalogV2Test,
    "LineBoss.BodyShop.Experimental.UnderbodyExpansionV2.StableCatalog",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopUnderbodyExpansionCatalogV2Test::RunTest(const FString& Parameters)
{
    const TArray<FName> ExpectedStations = {
        TEXT("BWU000_COMPONENT_KIT_PRESENTATION_V001"),
        TEXT("BWU001_RAIL_CROSSMEMBER_PREP_V001"),
        TEXT("BWU002_MAIN_UNDERBODY_JOIN_V001"),
        TEXT("BWU003_SIDE_SILL_ROCKER_JOIN_V001"),
        TEXT("BWU004_DEBURR_FINISH_V001"),
        TEXT("BWU005_UNDERBODY_INSPECTION_V001"),
        TEXT("BWU006_UNDERBODY_REWORK_V001"),
        TEXT("BWU007_PASS_BUFFER_V001")
    };
    const TArray<FName> ExpectedMaterials = {
        TEXT("UBW_PRIMARY_KIT_RAW"),
        TEXT("UBW_PRIMARY_KIT_PRESENTED"),
        TEXT("UBW_PRIMARY_STRUCTURE_PREPARED"),
        TEXT("UBW_PRIMARY_STRUCTURE_JOINED"),
        TEXT("UBW_SIDE_SILL_KIT"),
        TEXT("UBW_SIDE_SILLS_JOINED"),
        TEXT("UBW_FINISH_CHECKED"),
        TEXT("UBW_REWORK_HOLD"),
        TEXT("UBW_REINSPECT_READY"),
        TEXT("BIW_UNDERBODY")
    };
    const TArray<FName> ExpectedPorts = {
        TEXT("PRIMARY_KIT_IN"), TEXT("BODY_IN"), TEXT("BODY_OUT"), TEXT("SILL_KIT_IN"),
        TEXT("PASS_OUT"), TEXT("REWORK_OUT"), TEXT("REWORK_IN"),
        TEXT("REINSPECT_OUT"), TEXT("REINSPECT_IN")
    };
    const TArray<FName> ExpectedConnections = {
        TEXT("BWU_CONN_001"), TEXT("BWU_CONN_002"), TEXT("BWU_CONN_003"),
        TEXT("BWU_CONN_004"), TEXT("BWU_CONN_005"), TEXT("BWU_CONN_006"),
        TEXT("BWU_CONN_007"), TEXT("BWU_CONN_008")
    };
    TestEqual(TEXT("Eight expanded underbody station IDs remain exact and ordered"),
        FLBBodyShopUnderbodyExpansionRegistryV2::GetStableStationIds(), ExpectedStations);
    TestEqual(TEXT("Every material state transition remains exact and final output stays BIW_UNDERBODY"),
        FLBBodyShopUnderbodyExpansionRegistryV2::GetStableMaterialIds(), ExpectedMaterials);
    TestEqual(TEXT("Main, inbound and rework-loop port IDs remain exact"),
        FLBBodyShopUnderbodyExpansionRegistryV2::GetStablePortIds(), ExpectedPorts);
    TestEqual(TEXT("Connection IDs remain exact and ordered"),
        FLBBodyShopUnderbodyExpansionRegistryV2::GetStableConnectionIds(),
        ExpectedConnections);

    const TArray<FName> V1Ids = FLBBodyShopDefinitionRegistry::GetApprovedUnderbodySliceDefinitionIds();
    for (const FName V2Id : ExpectedStations)
    {
        TestFalse(TEXT("Expanded station IDs never replace a verified v1 cell ID"),
            V1Ids.Contains(V2Id));
    }

    const TArray<FLBBodyShopUnderbodyExpansionStationV2> TunnelStations =
        FLBBodyShopUnderbodyExpansionRegistryV2::GetCanonicalStations(
            ELBBodyShopUnderbodyArchitecture::CentreTunnel);
    const TArray<FLBBodyShopUnderbodyExpansionStationV2> EVStations =
        FLBBodyShopUnderbodyExpansionRegistryV2::GetCanonicalStations(
            ELBBodyShopUnderbodyArchitecture::EVBatteryTray);
    TestEqual(TEXT("Tunnel architecture has eight canonical definitions"),
        TunnelStations.Num(), 8);
    TestEqual(TEXT("EV architecture has eight canonical definitions"), EVStations.Num(), 8);
    if (TunnelStations.Num() != 8 || EVStations.Num() != 8)
    {
        AddError(TEXT("Canonical architecture inventory is unsafe to index."));
        return false;
    }
    const int32 ExpectedProcessStepCounts[] = {1, 1, 1, 1, 1, 2, 2, 2};
    FString Reason;
    for (int32 Index = 0; Index < TunnelStations.Num(); ++Index)
    {
        TestTrue(TEXT("Every tunnel-architecture station validates"),
            FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(
                TunnelStations[Index], Reason));
        TestTrue(TEXT("Every EV-architecture station validates"),
            FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(EVStations[Index], Reason));
        TestEqual(TEXT("Stable ID order and stage order are identical"),
            TunnelStations[Index].StationId, ExpectedStations[Index]);
        TestEqual(TEXT("Each station owns its exact stable process-step count"),
            TunnelStations[Index].ProcessStepIds.Num(), ExpectedProcessStepCounts[Index]);
        TestEqual(TEXT("Architecture is explicit on every tunnel station"),
            TunnelStations[Index].Architecture,
            ELBBodyShopUnderbodyArchitecture::CentreTunnel);
        TestEqual(TEXT("Architecture is explicit on every EV station"),
            EVStations[Index].Architecture,
            ELBBodyShopUnderbodyArchitecture::EVBatteryTray);
    }
    TestTrue(TEXT("Tunnel primary kit selects the tunnel"),
        TunnelStations[0].ComponentIds.Contains(LBBodyShopUnderbodyComponentIds::CentreTunnel));
    TestFalse(TEXT("Tunnel primary kit excludes the EV tray"),
        TunnelStations[0].ComponentIds.Contains(LBBodyShopUnderbodyComponentIds::EVBatteryTray));
    TestTrue(TEXT("EV primary kit selects the EV tray"),
        EVStations[0].ComponentIds.Contains(LBBodyShopUnderbodyComponentIds::EVBatteryTray));
    TestFalse(TEXT("EV primary kit excludes the tunnel"),
        EVStations[0].ComponentIds.Contains(LBBodyShopUnderbodyComponentIds::CentreTunnel));
    TestFalse(TEXT("Primary-kit ownership excludes separately supplied side sills"),
        TunnelStations[0].ComponentIds.Contains(LBBodyShopUnderbodyComponentIds::SideSillLeft));
    TestTrue(TEXT("Front partition is processed by main joining"),
        TunnelStations[2].ComponentIds.Contains(
            LBBodyShopUnderbodyComponentIds::FrontFloorPartition));
    TestTrue(TEXT("Rear partition is processed by main joining"),
        TunnelStations[2].ComponentIds.Contains(
            LBBodyShopUnderbodyComponentIds::RearFloorPartition));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopUnderbodyExpansionTopologyV2Test,
    "LineBoss.BodyShop.Experimental.UnderbodyExpansionV2.ApprovedTopology",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopUnderbodyExpansionTopologyV2Test::RunTest(const FString& Parameters)
{
    FString Reason;
    TestTrue(TEXT("The approved eight-station line and rework loop validate"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateApprovedExpansion(Reason));
    TestTrue(TEXT("The EV-tray architecture validates on the same exact topology"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateApprovedExpansion(
            ELBBodyShopUnderbodyArchitecture::EVBatteryTray, Reason));

    const TArray<FLBBodyShopUnderbodyExpansionLayoutItemV2> Layout =
        FLBBodyShopUnderbodyExpansionRegistryV2::GetApprovedLayout();
    TestEqual(TEXT("Expanded layout has eight unique station placements"), Layout.Num(), 8);
    if (Layout.Num() != 8)
    {
        AddError(TEXT("Approved layout inventory is unsafe to index."));
        return false;
    }
    const FVector ExpectedLocations[] = {
        FVector(-1100.0f, 0.0f, 0.0f), FVector(0.0f, 0.0f, 0.0f),
        FVector(1200.0f, 0.0f, 0.0f), FVector(2400.0f, 0.0f, 0.0f),
        FVector(3400.0f, 0.0f, 0.0f), FVector(4200.0f, 0.0f, 0.0f),
        FVector(4200.0f, -800.0f, 0.0f), FVector(5100.0f, 0.0f, 0.0f)
    };
    for (int32 Index = 0; Index < Layout.Num(); ++Index)
    {
        TestTrue(TEXT("Every approved placement remains on the exact 100 cm layout"),
            Layout[Index].WorldTransform.GetLocation().Equals(ExpectedLocations[Index], 0.01f));
    }

    const TArray<FLBBodyShopUnderbodyExpansionConnectionV2> Connections =
        FLBBodyShopUnderbodyExpansionRegistryV2::GetApprovedConnections();
    TestEqual(TEXT("Six main-line links and two rework-loop links are explicit"),
        Connections.Num(), 8);
    if (Connections.Num() != 8)
    {
        AddError(TEXT("Approved connection inventory is unsafe to index."));
        return false;
    }
    const TArray<FName> StableConnectionIds =
        FLBBodyShopUnderbodyExpansionRegistryV2::GetStableConnectionIds();
    if (StableConnectionIds.Num() != Connections.Num())
    {
        AddError(TEXT("Stable connection inventory is unsafe to index."));
        return false;
    }
    for (int32 Index = 0; Index < Connections.Num(); ++Index)
    {
        TestEqual(TEXT("Approved connection identity matches its exact stable order"),
            Connections[Index].ConnectionId,
            StableConnectionIds[Index]);
    }
    TestEqual(TEXT("Inspection sends failed work to the dedicated rework station"),
        Connections[6].Source.PortId, FName(TEXT("REWORK_OUT")));
    TestEqual(TEXT("Rework returns through a distinct reinspect endpoint"),
        Connections[7].Target.PortId, FName(TEXT("REINSPECT_IN")));

    const TArray<FLBBodyShopUnderbodyExpansionStationV2> Stations =
        FLBBodyShopUnderbodyExpansionRegistryV2::GetCanonicalStations();
    const FLBBodyShopUnderbodyExpansionStationV2* Inspection = Stations.FindByPredicate(
        [](const FLBBodyShopUnderbodyExpansionStationV2& Candidate)
        {
            return Candidate.Stage == ELBBodyShopUnderbodyExpansionStageV2::UnderbodyInspection;
        });
    TestNotNull(TEXT("Expanded topology has a real inspection station"), Inspection);
    if (Inspection)
    {
        const FLBBodyShopUnderbodyExpansionPortV2* Pass = Inspection->Ports.FindByPredicate(
            [](const FLBBodyShopUnderbodyExpansionPortV2& Port)
            {
                return Port.PortId == LBBodyShopUnderbodyExpansionPortIdsV2::PassOut;
            });
        TestNotNull(TEXT("Inspection has an explicit pass output"), Pass);
        if (Pass)
        {
            TestEqual(TEXT("Only passed inspection releases the existing underbody material"),
                Pass->MaterialId, LBBodyShopMaterialIds::Underbody);
        }
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopUnderbodyExpansionFailClosedV2Test,
    "LineBoss.BodyShop.Experimental.UnderbodyExpansionV2.FailClosed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopUnderbodyExpansionFailClosedV2Test::RunTest(const FString& Parameters)
{
    FString Reason;
    const TArray<FLBBodyShopUnderbodyExpansionStationV2> CanonicalStations =
        FLBBodyShopUnderbodyExpansionRegistryV2::GetCanonicalStations();
    const TArray<FLBBodyShopUnderbodyExpansionLayoutItemV2> CanonicalLayout =
        FLBBodyShopUnderbodyExpansionRegistryV2::GetApprovedLayout();
    const TArray<FLBBodyShopUnderbodyExpansionConnectionV2> CanonicalConnections =
        FLBBodyShopUnderbodyExpansionRegistryV2::GetApprovedConnections();
    const TArray<FLBBodyShopUnderbodyExpansionStationV2> EVCanonicalStations =
        FLBBodyShopUnderbodyExpansionRegistryV2::GetCanonicalStations(
            ELBBodyShopUnderbodyArchitecture::EVBatteryTray);
    if (CanonicalStations.Num() != 8 || CanonicalLayout.Num() != 8
        || CanonicalConnections.Num() != 8 || EVCanonicalStations.Num() != 8
        || CanonicalStations[0].Ports.IsEmpty()
        || CanonicalStations[1].Ports.IsEmpty())
    {
        AddError(TEXT("Canonical fail-closed fixtures are unsafe to index."));
        return false;
    }

    FLBBodyShopUnderbodyExpansionStationV2 WrongVersion = CanonicalStations[0];
    WrongVersion.ContractVersion = 1;
    TestFalse(TEXT("An expanded station cannot masquerade as v1"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(WrongVersion, Reason));

    FLBBodyShopUnderbodyExpansionStationV2 WrongStage = CanonicalStations[0];
    WrongStage.Stage = ELBBodyShopUnderbodyExpansionStageV2::PassBuffer;
    TestFalse(TEXT("A stable station ID cannot claim a different process role"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(WrongStage, Reason));

    FLBBodyShopUnderbodyExpansionStationV2 InvalidArchitecture = CanonicalStations[0];
    InvalidArchitecture.Architecture = static_cast<ELBBodyShopUnderbodyArchitecture>(255);
    TestFalse(TEXT("An unknown architecture fails closed"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(
            InvalidArchitecture, Reason));

    FLBBodyShopUnderbodyExpansionStationV2 InvalidDirection = CanonicalStations[0];
    InvalidDirection.Ports[0].Direction = static_cast<ELBBodyShopPortDirection>(255);
    TestFalse(TEXT("An unknown port direction fails closed"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(InvalidDirection, Reason));

    FLBBodyShopUnderbodyExpansionStationV2 InvalidTransport = CanonicalStations[0];
    InvalidTransport.Ports[0].Transport = static_cast<ELBBodyShopTransportType>(255);
    TestFalse(TEXT("An unknown transport type fails closed"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(InvalidTransport, Reason));

    FLBBodyShopUnderbodyExpansionStationV2 DuplicatePort = CanonicalStations[0];
    const FLBBodyShopUnderbodyExpansionPortV2 CopiedPort = DuplicatePort.Ports[0];
    DuplicatePort.Ports.Add(CopiedPort);
    TestFalse(TEXT("Duplicate station endpoints are rejected"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(DuplicatePort, Reason));

    FLBBodyShopUnderbodyExpansionStationV2 WrongProcess = CanonicalStations[0];
    WrongProcess.ProcessStepIds = CanonicalStations[1].ProcessStepIds;
    TestFalse(TEXT("A station cannot borrow another stage's process responsibility"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(WrongProcess, Reason));

    FLBBodyShopUnderbodyExpansionStationV2 DuplicateSillOwnership = CanonicalStations[0];
    DuplicateSillOwnership.ComponentIds.Add(LBBodyShopUnderbodyComponentIds::SideSillLeft);
    TestFalse(TEXT("The primary kit cannot duplicate side-sill material ownership"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(
            DuplicateSillOwnership, Reason));

    FLBBodyShopUnderbodyExpansionStationV2 OrphanedPartition = CanonicalStations[2];
    OrphanedPartition.ComponentIds.Remove(LBBodyShopUnderbodyComponentIds::RearFloorPartition);
    TestFalse(TEXT("Main joining cannot orphan a presented floor partition"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateStation(OrphanedPartition, Reason));

    TArray<FLBBodyShopUnderbodyExpansionConnectionV2> MissingLink = CanonicalConnections;
    MissingLink.RemoveAt(0);
    TestFalse(TEXT("Removing a main-line connection invalidates the expanded topology"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateExpansion(
            CanonicalStations, CanonicalLayout, MissingLink, Reason));

    TArray<FLBBodyShopUnderbodyExpansionConnectionV2> ReorderedLinks = CanonicalConnections;
    ReorderedLinks.Swap(0, 1);
    TestFalse(TEXT("Approved connection order is part of the stable contract"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateExpansion(
            CanonicalStations, CanonicalLayout, ReorderedLinks, Reason));

    TArray<FLBBodyShopUnderbodyExpansionConnectionV2> RenamedLink = CanonicalConnections;
    RenamedLink[0].ConnectionId = FName(TEXT("BWU_CONN_RENAMED"));
    TestFalse(TEXT("Approved connection identity cannot be renamed"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateExpansion(
            CanonicalStations, CanonicalLayout, RenamedLink, Reason));

    TArray<FLBBodyShopUnderbodyExpansionLayoutItemV2> OverlappingLayout = CanonicalLayout;
    OverlappingLayout[6].WorldTransform.SetLocation(FVector(4200.0f, -700.0f, 0.0f));
    TestFalse(TEXT("The rework cell cannot overlap inspection"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateExpansion(
            CanonicalStations, OverlappingLayout, CanonicalConnections, Reason));

    TArray<FLBBodyShopUnderbodyExpansionLayoutItemV2> BrokenLoop = CanonicalLayout;
    BrokenLoop[6].WorldTransform.AddToTranslation(FVector(100.0f, 0.0f, 0.0f));
    TestFalse(TEXT("The rework loop ports must remain exactly coincident"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateExpansion(
            CanonicalStations, BrokenLoop, CanonicalConnections, Reason));

    TArray<FLBBodyShopUnderbodyExpansionStationV2> TwistedPort = CanonicalStations;
    TwistedPort[1].Ports[0].LocalTransform.SetRotation(
        FRotator(15.0f, 180.0f, 0.0f).Quaternion());
    TestFalse(TEXT("Connected ports must have fully opposed three-axis transforms"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateExpansion(
            TwistedPort, CanonicalLayout, CanonicalConnections, Reason));

    TArray<FLBBodyShopUnderbodyExpansionStationV2> MaterialMismatch = CanonicalStations;
    MaterialMismatch[1].Ports[0].MaterialId =
        LBBodyShopUnderbodyExpansionMaterialIdsV2::FinishChecked;
    TestFalse(TEXT("A connection cannot silently change material identity"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateExpansion(
            MaterialMismatch, CanonicalLayout, CanonicalConnections, Reason));

    TArray<FLBBodyShopUnderbodyExpansionStationV2> MixedArchitecture = CanonicalStations;
    MixedArchitecture[1] = EVCanonicalStations[1];
    TestFalse(TEXT("One topology cannot mix tunnel and EV architecture stations"),
        FLBBodyShopUnderbodyExpansionRegistryV2::ValidateExpansion(
            MixedArchitecture, CanonicalLayout, CanonicalConnections, Reason));
    return true;
}

#endif
