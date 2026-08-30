#include "LBPressShopBuildAuthority.h"
#include "LBPressShopStorageZone.h"
#include "LBManagementPawn.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBFactoryTransportLink.h"
#include "Misc/AutomationTest.h"
#include "Engine/World.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPressShopStorageAuthorityTest,
    "LineBoss.PressShop.Builder.StorageAuthority",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPressShopStorageAuthorityTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_StorageBuilder"));
    ALBPressShopBuildAuthority* Authority = World
        ? World->SpawnActor<ALBPressShopBuildAuthority>() : nullptr;
    TestNotNull(TEXT("Storage authority spawns"), Authority);
    if (!Authority)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FLBPressShopStorageBay Bay;
    Bay.BayId = TEXT("PR003_COIL_STORAGE");
    Bay.Centre = FVector(0.0f, 0.0f, 250.0f);
    Bay.HalfExtent = FVector(1200.0f, 900.0f, 300.0f);
    Bay.AcceptedTypes = {ELBPressShopStorageType::BareCoils,
        ELBPressShopStorageType::Quarantine};
    Bay.DefaultZoneHalfExtent = FVector(700.0f, 650.0f, 200.0f);
    Bay.DefaultCapacity = 12;
    Bay.StorageUnitPitchCm = FVector2D(220.0f, 600.0f);
    Authority->StorageBays.Add(Bay);

    FLBPressShopStorageBay PartsBay;
    PartsBay.BayId = TEXT("PR_MRO_PARTS_STORAGE");
    PartsBay.Centre = FVector(2500.0f, 0.0f, 150.0f);
    PartsBay.HalfExtent = FVector(500.0f, 500.0f, 200.0f);
    PartsBay.AcceptedTypes = {ELBPressShopStorageType::MaintenanceParts};
    PartsBay.DefaultZoneHalfExtent = FVector(250.0f, 250.0f, 150.0f);
    PartsBay.DefaultCapacity = 4;
    PartsBay.StorageUnitPitchCm = FVector2D(200.0f, 200.0f);
    PartsBay.BoundaryClearanceCm = 25.0f;
    Authority->StorageBays.Add(PartsBay);

    FLBPressShopLogisticsSpine Route;
    Route.SpineId = TEXT("AGV_PRIMARY");
    Route.Start = FVector(-1500.0f, -700.0f, 0.0f);
    Route.End = FVector(3500.0f, -700.0f, 0.0f);
    Route.MaximumAccessDistanceCm = 800.0f;
    Authority->LogisticsSpines.Add(Route);

    FString Reason;
    const FVector ZoneExtent(700.0f, 650.0f, 200.0f);
    FVector AuthoredExtent;
    int32 AuthoredCapacity = 0;
    TestTrue(TEXT("Placement preview uses authored storage defaults"),
        Authority->GetStoragePlacementDefaults(ELBPressShopStorageType::BareCoils,
            AuthoredExtent, AuthoredCapacity, Reason));
    TestEqual(TEXT("Authored capacity is preserved"), AuthoredCapacity, 12);
    TestTrue(TEXT("Authored footprint is preserved"), AuthoredExtent.Equals(ZoneExtent));
    int32 Columns = 0;
    int32 Rows = 0;
    int32 CalculatedCapacity = 0;
    TestTrue(TEXT("Dragged coil area generates an authored stand layout"),
        Authority->CalculateStorageLayout(ELBPressShopStorageType::BareCoils,
            FTransform(FVector(0.0f, 0.0f, 200.0f)), ZoneExtent,
            Columns, Rows, CalculatedCapacity, Reason));
    TestEqual(TEXT("Coil area fits six stands per row"), Columns, 6);
    TestEqual(TEXT("Coil area fits two rows"), Rows, 2);
    TestEqual(TEXT("Coil area automatically yields twelve positions"), CalculatedCapacity, 12);
    TestTrue(TEXT("Authorised coil zone with AGV access passes"),
        Authority->EvaluateStorageTransform(ELBPressShopStorageType::BareCoils,
            FTransform(FVector(0.0f, 0.0f, 200.0f)), ZoneExtent, Reason));
    TestTrue(TEXT("Pass reason identifies logistics authority"), Reason.Contains(TEXT("AGV_PRIMARY")));

    ALBPressShopStorageZone* BuiltZone = nullptr;
    TestTrue(TEXT("Authority places a functional deterministic coil zone"),
        Authority->PlaceStorageZone(ELBPressShopStorageType::BareCoils,
            FTransform(FVector(0.0f, 0.0f, 200.0f)), ZoneExtent, 12, BuiltZone, Reason));
    TestNotNull(TEXT("Placed storage actor exists"), BuiltZone);
    TestEqual(TEXT("First storage identity is deterministic"),
        BuiltZone ? BuiltZone->GetZoneId() : NAME_None, FName(TEXT("SZ-COIL-001")));
    TestEqual(TEXT("Dragged area generates twelve physical coil stands"),
        BuiltZone ? BuiltZone->GetGeneratedStandCount() : -1, 12);
    if (BuiltZone) AddInfo(FString::Printf(TEXT("Measured first stand bottom Z: %.3f"), BuiltZone->GetFirstStandBottomWorldZ()));
    TestTrue(TEXT("Approved storage stand is grounded on the factory floor"), BuiltZone
        && FMath::IsNearlyEqual(BuiltZone->GetFirstStandBottomWorldZ(), 0.0f, 0.25f));
    TestEqual(TEXT("Generated stand layout preserves six columns"),
        BuiltZone ? BuiltZone->GetLayoutColumns() : -1, 6);
    TestEqual(TEXT("Generated stand layout preserves two rows"),
        BuiltZone ? BuiltZone->GetLayoutRows() : -1, 2);
    TestEqual(TEXT("Empty storage starts with no visible coils"),
        BuiltZone ? BuiltZone->GetVisibleStoredUnitCount() : -1, 0);
    TestEqual(TEXT("Coil storage exposes the ordered stage-two ingress after PR002"),
        BuiltZone && BuiltZone->IngressPoint ? BuiltZone->IngressPoint->ProcessStage : -1,
        LBFactoryProcessStage::CoilStorage);
    TestEqual(TEXT("Coil storage ingress carries coil material"),
        BuiltZone && BuiltZone->IngressPoint ? BuiltZone->IngressPoint->MaterialClass
            : ELBFactoryMaterialClass::GeneralParts, ELBFactoryMaterialClass::Coil);
    TestTrue(TEXT("Coil storage process-port identities derive from its stable zone identity"),
        BuiltZone && BuiltZone->IngressPoint && BuiltZone->EgressPoint
        && BuiltZone->IngressPoint->PortId == TEXT("SZ-COIL-001-IN")
        && BuiltZone->EgressPoint->PortId == TEXT("SZ-COIL-001-OUT"));

    AActor* PR002Cell = World->SpawnActor<AActor>();
    ULBFactoryProcessPortComponent* PR002Output = NewObject<ULBFactoryProcessPortComponent>(
        PR002Cell, TEXT("PR002_COIL_OUT"));
    PR002Output->PortId = TEXT("PR002-COIL-OUT");
    PR002Output->Direction = ELBFactoryPortDirection::Output;
    PR002Output->ProcessStage = LBFactoryProcessStage::PR002WeighInspection;
    PR002Output->MaterialClass = ELBFactoryMaterialClass::Coil;
    PR002Output->TransportKind = ELBFactoryTransportKind::AGVHandoff;
    PR002Output->MaximumAutomaticLinkDistanceCm = 2000.0f;
    PR002Cell->AddInstanceComponent(PR002Output);
    PR002Output->RegisterComponent();
    PR002Output->SetWorldLocation(FVector(0.0f, -1000.0f, 250.0f));
    ULBFactoryConnectionSubsystem* Connections = NewObject<ULBFactoryConnectionSubsystem>(World);
    TArray<ALBFactoryTransportLink*> StorageLinks;
    TestTrue(TEXT("Placed coil storage automatically joins the ordered graph after PR002"),
        Connections && Connections->AutoConnectNewMachine(BuiltZone, StorageLinks, Reason));
    TestEqual(TEXT("PR002 creates one automatic AGV handoff to coil storage"),
        StorageLinks.Num(), 1);
    TestTrue(TEXT("Storage accepts available capacity"), BuiltZone && BuiltZone->TryStore(7));
    TestEqual(TEXT("Occupancy records stored material"), BuiltZone ? BuiltZone->GetOccupancy() : -1, 7);
    TestEqual(TEXT("Occupancy drives visible cylindrical coils"),
        BuiltZone ? BuiltZone->GetVisibleStoredUnitCount() : -1, 7);
    if (BuiltZone) AddInfo(FString::Printf(TEXT("Measured first wrapped-coil bottom Z: %.3f"), BuiltZone->GetFirstStoredUnitBottomWorldZ()));
    TestTrue(TEXT("Repaired wrapped coil sits on the measured 41 cm complete-saddle top"), BuiltZone
        && FMath::IsNearlyEqual(BuiltZone->GetFirstStoredUnitBottomWorldZ(), 41.0f, 0.25f));
    TestFalse(TEXT("Storage rejects over-capacity delivery"), BuiltZone && BuiltZone->TryStore(6));
    TestTrue(TEXT("Storage permits a valid withdrawal"), BuiltZone && BuiltZone->TryWithdraw(2));
    TestFalse(TEXT("Storage rejects over-withdrawal"), BuiltZone && BuiltZone->TryWithdraw(6));
    TestTrue(TEXT("Player buffer accepts an automatic replenishment policy"),
        BuiltZone && BuiltZone->ConfigureReplenishment(3, 4, 2));
    TestTrue(TEXT("Consumption below reorder level succeeds"), BuiltZone && BuiltZone->TryWithdraw(3));
    TestEqual(TEXT("Low buffer raises pull demand to its target level"),
        BuiltZone ? BuiltZone->GetRequestedReplenishmentUnits() : -1, 5);
    TestEqual(TEXT("Demand is represented by two replenishment loads"),
        BuiltZone ? BuiltZone->GetOutstandingReplenishmentLoads() : -1, 2);
    TestTrue(TEXT("Received delivery closes outstanding replenishment demand"),
        BuiltZone && BuiltZone->TryStore(5));
    TestEqual(TEXT("Replenished buffer has no open cards"),
        BuiltZone ? BuiltZone->GetOutstandingReplenishmentLoads() : -1, 0);
    const FLBPressShopStorageZoneSaveState BufferSave = BuiltZone->CaptureSaveState();
    ALBPressShopStorageZone* ReloadedBuffer = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Player buffer state restores by stable zone identity"),
        ReloadedBuffer && ReloadedBuffer->RestoreSaveState(BufferSave));
    TestEqual(TEXT("Buffer occupancy round trips"),
        ReloadedBuffer ? ReloadedBuffer->GetOccupancy() : -1, BuiltZone->GetOccupancy());
    TestEqual(TEXT("Generated stands round trip through campaign storage state"),
        ReloadedBuffer ? ReloadedBuffer->GetGeneratedStandCount() : -1, 12);
    TestEqual(TEXT("Visible coil occupancy round trips"),
        ReloadedBuffer ? ReloadedBuffer->GetVisibleStoredUnitCount() : -1,
        BuiltZone->GetVisibleStoredUnitCount());

    ALBPressShopStorageZone* PartsZone = nullptr;
    TestTrue(TEXT("Shared dragged-area authority places a maintenance-parts zone"),
        Authority->PlaceStorageZone(ELBPressShopStorageType::MaintenanceParts,
            FTransform(FVector(2500.0f, 0.0f, 150.0f)), FVector(250.0f, 250.0f, 150.0f),
            4, PartsZone, Reason));
    TestEqual(TEXT("Parts area automatically generates four pallet/rack positions"),
        PartsZone ? PartsZone->GetGeneratedStandCount() : -1, 4);
    TestTrue(TEXT("Parts inventory can occupy generated positions"),
        PartsZone && PartsZone->TryStore(3));
    TestEqual(TEXT("Parts occupancy drives three visible stored loads"),
        PartsZone ? PartsZone->GetVisibleStoredUnitCount() : -1, 3);
    TestEqual(TEXT("Automatic replenishment state round trips"),
        ReloadedBuffer ? ReloadedBuffer->GetRequestedReplenishmentUnits() : -1,
        BuiltZone->GetRequestedReplenishmentUnits());
    TestFalse(TEXT("Preview rejects overlap with an existing functional zone"),
        Authority->EvaluateStorageTransform(ELBPressShopStorageType::BareCoils,
            FTransform(FVector(0.0f, 0.0f, 250.0f)), ZoneExtent, Reason));
    TestTrue(TEXT("Overlap reason identifies the occupied zone"), Reason.Contains(TEXT("SZ-COIL-001")));

    ALBManagementPawn* ManagementPawn = World->SpawnActor<ALBManagementPawn>();
    TestTrue(TEXT("Management mode can enter authored storage placement"),
        ManagementPawn && ManagementPawn->StartStoragePlacement(ELBPressShopStorageType::BareCoils));
    TestTrue(TEXT("Management storage placement becomes active"),
        ManagementPawn && ManagementPawn->IsStoragePlacementActive());

    TestFalse(TEXT("Wrong storage type fails closed"),
        Authority->EvaluateStorageTransform(ELBPressShopStorageType::Scrap,
            FTransform(FVector(0.0f, 0.0f, 250.0f)), ZoneExtent, Reason));
    TestFalse(TEXT("Incomplete footprint outside bay fails"),
        Authority->EvaluateStorageTransform(ELBPressShopStorageType::BareCoils,
            FTransform(FVector(1150.0f, 0.0f, 250.0f)), ZoneExtent, Reason));

    FLBPressShopProtectedArea Aisle;
    Aisle.AreaId = TEXT("PEDESTRIAN_AISLE");
    Aisle.Centre = FVector(0.0f, 0.0f, 250.0f);
    Aisle.HalfExtent = FVector(100.0f, 900.0f, 300.0f);
    Authority->ProtectedAreas.Add(Aisle);
    TestFalse(TEXT("Protected pedestrian aisle blocks storage"),
        Authority->EvaluateStorageTransform(ELBPressShopStorageType::BareCoils,
            FTransform(FVector(0.0f, 0.0f, 250.0f)), ZoneExtent, Reason));

    Authority->ProtectedAreas.Reset();
    Authority->LogisticsSpines[0].MaximumAccessDistanceCm = 100.0f;
    TestFalse(TEXT("Storage without verified logistics reach fails closed"),
        Authority->EvaluateStorageTransform(ELBPressShopStorageType::BareCoils,
            FTransform(FVector(0.0f, 0.0f, 250.0f)), ZoneExtent, Reason));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPanelStillageThreeHighStorageTest,
    "LineBoss.PressShop.Builder.PanelStillageThreeHighStorage",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPanelStillageThreeHighStorageTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_PanelStillageThreeHighStorage"));
    ALBPressShopBuildAuthority* Authority = World
        ? World->SpawnActor<ALBPressShopBuildAuthority>() : nullptr;
    if (!World || !Authority)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    auto AddStillageBay = [Authority](const FName BayId, const FVector& Centre,
        const ELBPressShopStorageType StorageType)
    {
        FLBPressShopStorageBay Bay;
        Bay.BayId = BayId;
        Bay.Centre = Centre;
        Bay.HalfExtent = FVector(700.0f, 700.0f, 300.0f);
        Bay.AcceptedTypes = {StorageType};
        Bay.DefaultZoneHalfExtent = FVector(550.0f, 550.0f,
            ALBPressShopStorageZone::PanelStillageMinimumZoneHalfHeightCm);
        Bay.DefaultCapacity = 48;
        Bay.StorageUnitPitchCm = FVector2D(250.0f, 250.0f);
        Bay.BoundaryClearanceCm = 50.0f;
        Authority->StorageBays.Add(Bay);
    };
    AddStillageBay(TEXT("FULL_STILLAGE_TEST_BAY"), FVector(0.0f, 0.0f, 235.0f),
        ELBPressShopStorageType::FinishedPanelStillages);
    AddStillageBay(TEXT("EMPTY_STILLAGE_TEST_BAY"), FVector(2000.0f, 0.0f, 235.0f),
        ELBPressShopStorageType::EmptyPanelStillages);

    FLBPressShopLogisticsSpine Route;
    Route.SpineId = TEXT("STILLAGE_FLT_ROUTE");
    Route.Start = FVector(-1000.0f, -700.0f, 0.0f);
    Route.End = FVector(3000.0f, -700.0f, 0.0f);
    Route.MaximumAccessDistanceCm = 800.0f;
    Authority->LogisticsSpines.Add(Route);

    const FVector ThreeHighExtent(550.0f, 550.0f,
        ALBPressShopStorageZone::PanelStillageMinimumZoneHalfHeightCm);
    const FTransform FullTransform(FVector(0.0f, 0.0f, ThreeHighExtent.Z));
    const FTransform EmptyTransform(FVector(2000.0f, 0.0f, ThreeHighExtent.Z));
    FString Reason;
    int32 Columns = 0;
    int32 Rows = 0;
    int32 FullCapacity = 0;
    TestTrue(TEXT("A 4x4 full-stillage floor computes three-high capacity"),
        Authority->CalculateStorageLayout(ELBPressShopStorageType::FinishedPanelStillages,
            FullTransform, ThreeHighExtent, Columns, Rows, FullCapacity, Reason));
    TestEqual(TEXT("Full store has four columns"), Columns, 4);
    TestEqual(TEXT("Full store has four rows"), Rows, 4);
    TestEqual(TEXT("Full store capacity is 16 floor bays x 3 high"), FullCapacity, 48);
    int32 EmptyCapacity = 0;
    TestTrue(TEXT("Empty-stillage store uses the identical calculation"),
        Authority->CalculateStorageLayout(ELBPressShopStorageType::EmptyPanelStillages,
            EmptyTransform, ThreeHighExtent, Columns, Rows, EmptyCapacity, Reason));
    TestEqual(TEXT("Empty and full stillage capacities match"), EmptyCapacity, FullCapacity);
    TestFalse(TEXT("Three-high store rejects the old one-high protected height"),
        Authority->EvaluateStorageTransform(ELBPressShopStorageType::FinishedPanelStillages,
            FTransform(FVector(0.0f, 0.0f, 150.0f)), FVector(550.0f, 550.0f, 150.0f), Reason));
    TestTrue(TEXT("Height rejection explains the protected envelope"),
        Reason.Contains(TEXT("4.7 m")));

    ALBPressShopStorageZone* FullStore = nullptr;
    ALBPressShopStorageZone* EmptyStore = nullptr;
    TestTrue(TEXT("Full stillage store places with three-high authority"),
        Authority->PlaceStorageZone(ELBPressShopStorageType::FinishedPanelStillages,
            FullTransform, ThreeHighExtent, 48, FullStore, Reason));
    TestTrue(TEXT("Empty stillage store places with the same authority"),
        Authority->PlaceStorageZone(ELBPressShopStorageType::EmptyPanelStillages,
            EmptyTransform, ThreeHighExtent, 48, EmptyStore, Reason));
    TestEqual(TEXT("Full store retains sixteen painted floor stands"),
        FullStore ? FullStore->GetGeneratedStandCount() : -1, 16);
    TestEqual(TEXT("Empty store retains sixteen painted floor stands"),
        EmptyStore ? EmptyStore->GetGeneratedStandCount() : -1, 16);
    TestEqual(TEXT("Empty starter inventory fills all three tiers"),
        EmptyStore ? EmptyStore->GetOccupancy() : -1, 48);
    TestEqual(TEXT("Every empty starter stillage has an exact identity"),
        EmptyStore ? EmptyStore->GetIdentifiedUnitCount() : -1, 48);
    TestTrue(TEXT("Last starter identity is deterministic and persistent"), EmptyStore
        && EmptyStore->ContainsIdentifiedUnit(TEXT("SZ-EMPTY-STL-002-STL-048")));

    TestFalse(TEXT("Stillage stores reject multi-unit handling"),
        FullStore && FullStore->TryStore(2));
    for (int32 StillageIndex = 0; FullStore && StillageIndex < 48; ++StillageIndex)
    {
        const FName StillageId(*FString::Printf(TEXT("FULL-WIP-%03d"), StillageIndex + 1));
        TestTrue(FString::Printf(TEXT("Full stillage %d enters one at a time"), StillageIndex + 1),
            FullStore->TryStoreIdentifiedUnit(StillageId));
    }
    TestFalse(TEXT("The forty-ninth stillage is rejected"), FullStore
        && FullStore->TryStoreIdentifiedUnit(TEXT("FULL-WIP-049")));
    TestFalse(TEXT("Stillage stores reject multi-unit withdrawal"),
        FullStore && FullStore->TryWithdraw(2));
    TestEqual(TEXT("All 48 full stillages are visible"),
        FullStore ? FullStore->GetVisibleStoredUnitCount() : -1, 48);
    TestTrue(TEXT("Tier one is grounded"), FullStore
        && FMath::IsNearlyEqual(FullStore->GetVisibleStoredUnitBottomWorldZ(0), 0.0f, 0.25f)
        && FMath::IsNearlyEqual(FullStore->GetVisibleStoredUnitBottomWorldZ(15), 0.0f, 0.25f));
    TestTrue(TEXT("Tier two starts at 145 cm"), FullStore
        && FMath::IsNearlyEqual(FullStore->GetVisibleStoredUnitBottomWorldZ(16), 145.0f, 0.25f));
    TestTrue(TEXT("Tier three starts at 290 cm"), FullStore
        && FMath::IsNearlyEqual(FullStore->GetVisibleStoredUnitBottomWorldZ(32), 290.0f, 0.25f));
    TestTrue(TEXT("Tier three remains inside the raised 4.7 m envelope"), FullStore
        && FullStore->GetVisibleStoredUnitBottomWorldZ(47) + 145.0f
            <= FullStore->GetActorLocation().Z + FullStore->GetZoneHalfExtent().Z + 0.25f);

    const FLBPressShopStorageZoneSaveState FullSave = FullStore->CaptureSaveState();
    TestEqual(TEXT("New storage state writes version four"), FullSave.Version, 4);
    TestEqual(TEXT("Save records all occupied stack levels"),
        FullSave.OccupiedStackLevels.Num(), 48);
    TestTrue(TEXT("Save records deterministic tier transitions"),
        FullSave.OccupiedStackLevels.Num() == 48
        && FullSave.OccupiedStackLevels[0] == 1
        && FullSave.OccupiedStackLevels[16] == 2
        && FullSave.OccupiedStackLevels[32] == 3);
    ALBPressShopStorageZone* ReloadedFull = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Three-high full store round trips"),
        ReloadedFull && ReloadedFull->RestoreSaveState(FullSave));
    TestTrue(TEXT("Round trip preserves capacity, IDs, stands and tier three"), ReloadedFull
        && ReloadedFull->GetCapacity() == 48
        && ReloadedFull->GetMaximumStackLevels() == 3
        && ReloadedFull->GetGeneratedStandCount() == 16
        && ReloadedFull->ContainsIdentifiedUnit(TEXT("FULL-WIP-048"))
        && FMath::IsNearlyEqual(ReloadedFull->GetVisibleStoredUnitBottomWorldZ(32), 290.0f, 0.25f));

    FLBPressShopStorageZoneSaveState InvalidStackSave = FullSave;
    InvalidStackSave.OccupiedStackLevels[16] = 3;
    TArray<FLBPressShopStorageZoneSaveState> InvalidSet = {InvalidStackSave};
    TestFalse(TEXT("Build authority rejects corrupted saved stack levels"),
        Authority->RestoreStorageZones(InvalidSet, Reason));

    FLBPressShopStorageZoneSaveState LegacyState;
    LegacyState.Version = 3;
    LegacyState.ZoneId = TEXT("SZ-PANEL-LEGACY-003");
    LegacyState.StorageType = ELBPressShopStorageType::FinishedPanelStillages;
    LegacyState.WorldTransform = FTransform(FVector(0.0f, 0.0f, 150.0f));
    LegacyState.ZoneHalfExtent = FVector(550.0f, 550.0f, 150.0f);
    LegacyState.Capacity = 16;
    LegacyState.Occupancy = 2;
    LegacyState.ReorderPoint = 4;
    LegacyState.ReplenishmentBatchSize = 8;
    LegacyState.MaximumOutstandingReplenishmentLoads = 2;
    LegacyState.LayoutColumns = 4;
    LegacyState.LayoutRows = 4;
    LegacyState.StorageUnitPitchCm = FVector2D(250.0f, 250.0f);
    LegacyState.BoundaryClearanceCm = 50.0f;
    LegacyState.StoredUnitIds = {TEXT("LEGACY-WIP-001"), TEXT("LEGACY-WIP-002")};
    ALBPressShopStorageZone* LegacyStore = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Version-three one-high stillage state remains loadable"),
        LegacyStore && LegacyStore->RestoreSaveState(LegacyState));
    TestTrue(TEXT("Legacy restore remains one-high with exact identities"), LegacyStore
        && LegacyStore->GetMaximumStackLevels() == 1
        && LegacyStore->GetCapacity() == 16
        && LegacyStore->GetGeneratedStandCount() == 16
        && LegacyStore->ContainsIdentifiedUnit(TEXT("LEGACY-WIP-002")));

    if (ReloadedFull) ReloadedFull->Destroy();
    if (LegacyStore) LegacyStore->Destroy();
    TArray<FLBPressShopStorageZoneSaveState> LegacySet = {LegacyState};
    TestTrue(TEXT("Build-authority save validation also accepts legacy one-high state"),
        Authority->RestoreStorageZones(LegacySet, Reason));

    World->DestroyWorld(false);
    return true;
}

#endif
