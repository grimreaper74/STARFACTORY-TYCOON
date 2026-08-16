#include "LBFactoryFloorMarkingComponent.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryMachineBuilderSubsystem.h"
#include "LBPressShopStorageZone.h"
#include "LBPressShopBuildAuthority.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBMachineFloorMarkingHierarchyTest,
    "LineBoss.FactoryBuilder.FloorMarkings.MachineSafetyHierarchy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBMachineFloorMarkingHierarchyTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_MachineFloorMarkings"));
    ALBFactoryBuildMachine* Inbound = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    ALBFactoryBuildMachine* Inspection = World ? World->SpawnActor<ALBFactoryBuildMachine>() : nullptr;
    TestTrue(TEXT("Floor-marking fixtures configure"), Inbound && Inspection
        && Inbound->Configure(TEXT("INBOUND-MARK-001"), ELBFactoryBuildMachineType::InboundDeliveryDock)
        && Inspection->Configure(TEXT("INSPECT-MARK-001"), ELBFactoryBuildMachineType::InspectionCell));
    if (!World || !Inbound || !Inspection)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    ULBFactoryFloorMarkingComponent* DockPaint = Inbound->GetFloorMarkings();
    ULBFactoryFloorMarkingComponent* MachinePaint = Inspection->GetFloorMarkings();
    TestTrue(TEXT("Inbound unloading bay owns non-colliding placement paint"),
        DockPaint && DockPaint->HasNonCollidingPresentation());
    TestEqual(TEXT("Every machine has a four-sided yellow service envelope"),
        MachinePaint ? MachinePaint->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::ServiceEnvelope) : 0, 4);
    TestEqual(TEXT("Ordinary machine does not claim red keep-clear semantics"),
        MachinePaint ? MachinePaint->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::KeepClearHatch) : -1, 0);
    TestTrue(TEXT("Unload dock receives clipped red diagonal hatching"), DockPaint
        && DockPaint->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::KeepClearHatch) >= 8);
    TestTrue(TEXT("Unload dock receives dashed vehicle approach guides"), DockPaint
        && DockPaint->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::VehicleLane) >= 4);
    TestEqual(TEXT("Unload hierarchy keeps yellow boundary above the red work zone"),
        DockPaint ? DockPaint->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::ServiceEnvelope) : 0, 4);

    const FTransform EditedTransform(FRotator(0.0f, 37.0f, 0.0f), FVector(1240.0f, -830.0f, 0.0f));
    Inbound->SetActorTransform(EditedTransform);
    const FLBFactoryBuildMachineSaveState Saved = Inbound->CaptureSaveState();
    ALBFactoryBuildMachine* Restored = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Machine placement edit restores through normal save state"),
        Restored && Restored->RestoreSaveState(Saved));
    TestTrue(TEXT("Restored machine paint follows the saved transform"), Restored
        && Restored->GetActorTransform().Equals(EditedTransform, 0.01f)
        && Restored->GetFloorMarkings()
        && Restored->GetFloorMarkings()->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::KeepClearHatch)
            == DockPaint->GetMarkingCountBySemantic(ELBFactoryFloorMarkingSemantic::KeepClearHatch));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBStorageFloorPaintingTest,
    "LineBoss.FactoryBuilder.FloorMarkings.StoragePaintAndPersistence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBStorageFloorPaintingTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_StorageFloorMarkings"));
    ALBPressShopStorageZone* FinishedPanels = World ? World->SpawnActor<ALBPressShopStorageZone>() : nullptr;
    ALBPressShopStorageZone* Quarantine = World ? World->SpawnActor<ALBPressShopStorageZone>() : nullptr;
    TestTrue(TEXT("Storage paint fixtures configure"), FinishedPanels && Quarantine
        && FinishedPanels->Configure(TEXT("SZ-PANEL-MARK-001"),
            ELBPressShopStorageType::FinishedPanelStillages, 8, FVector(500.0f, 300.0f, 100.0f))
        && FinishedPanels->ConfigureLayout(4, 2, FVector2D(200.0f, 200.0f), 50.0f)
        && Quarantine->Configure(TEXT("SZ-QUAR-MARK-001"),
            ELBPressShopStorageType::Quarantine, 4, FVector(300.0f, 250.0f, 100.0f)));
    if (!World || !FinishedPanels || !Quarantine)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    ULBFactoryFloorMarkingComponent* SafePaint = FinishedPanels->GetFloorMarkings();
    ULBFactoryFloorMarkingComponent* QuarantinePaint = Quarantine->GetFloorMarkings();
    TestTrue(TEXT("Finished-panel store is painted as one green owned floor area"), SafePaint
        && SafePaint->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::StorageFill) == 1);
    TestEqual(TEXT("Storage boundary plus slot divisions are white and deterministic"),
        SafePaint ? SafePaint->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::StorageBoundary) : 0, 8);
    TestEqual(TEXT("Safe storage never receives hazard hatch"), SafePaint
        ? SafePaint->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::KeepClearHatch) : -1, 0);
    TestTrue(TEXT("Storage paint preserves gameplay collision and navigation"),
        SafePaint && SafePaint->HasNonCollidingPresentation());
    TestTrue(TEXT("Quarantine storage replaces green fill with red hatch"), QuarantinePaint
        && QuarantinePaint->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::StorageFill) == 0
        && QuarantinePaint->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::KeepClearHatch) > 0);

    const FTransform EditedTransform(FRotator(0.0f, -25.0f, 0.0f), FVector(-600.0f, 925.0f, 100.0f));
    FinishedPanels->SetActorTransform(EditedTransform);
    const FLBPressShopStorageZoneSaveState Saved = FinishedPanels->CaptureSaveState();
    ALBPressShopStorageZone* Restored = World->SpawnActor<ALBPressShopStorageZone>();
    TestTrue(TEXT("Storage placement edit restores through normal save state"),
        Restored && Restored->RestoreSaveState(Saved));
    TestTrue(TEXT("Restored store rebuilds green fill, white border and slot grid"), Restored
        && Restored->GetActorTransform().Equals(EditedTransform, 0.01f)
        && Restored->GetFloorMarkings()
        && Restored->GetFloorMarkings()->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::StorageBoundary) == 8);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBEditableInfrastructureMarkingTest,
    "LineBoss.FactoryBuilder.FloorMarkings.EditableRoutesAndCrossings",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBEditableInfrastructureMarkingTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_EditableRoutePaint"));
    ULBFactoryMachineBuilderSubsystem* Builder = World
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(World) : nullptr;
    ALBPressShopBuildAuthority* FloorAuthority = World
        ? World->SpawnActor<ALBPressShopBuildAuthority>() : nullptr;
    if (FloorAuthority)
    {
        FLBPressShopBuildBay Bay;
        Bay.BayId = TEXT("EDITABLE_INFRASTRUCTURE_TEST_FLOOR");
        Bay.Centre = FVector::ZeroVector;
        Bay.HalfExtent = FVector(5000.0f, 5000.0f, 500.0f);
        FloorAuthority->BuildBays.Add(Bay);
    }
    ALBFactoryAGVInfrastructure* Walkway = nullptr;
    FString Reason;
    TestTrue(TEXT("Player can place an editable walkway with automatic paint"), Builder
        && Builder->PlaceAGVInfrastructure(ELBFactoryAGVInfrastructureType::PedestrianWalkway,
            INDEX_NONE, FTransform(FVector(100.0f, 200.0f, 0.0f)), Walkway, Reason));
    if (!World || !Builder || !Walkway)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    TestTrue(TEXT("Walkway adds a white pedestrian boundary over its green base"),
        Walkway->GetSafetyMarkings()
        && Walkway->GetSafetyMarkings()->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::PedestrianCrossing) == 4);

    const FTransform EditedTransform(FRotator(0.0f, 90.0f, 0.0f), FVector(850.0f, -450.0f, 0.0f));
    TestTrue(TEXT("Post-placement route/walkway edit is accepted by stable identity"), FloorAuthority &&
        Builder->UpdateAGVInfrastructureTransform(Walkway->GetInfrastructureId(),
            EditedTransform, Reason));
    TArray<FLBFactoryAGVInfrastructureSaveState> Saved;
    TestTrue(TEXT("Edited player marking transform enters normal save data"),
        Builder->CaptureAGVInfrastructure(Saved));
    TestEqual(TEXT("One edited walkway was captured"), Saved.Num(), 1);
    TestTrue(TEXT("Saved walkway retains edited position and rotation"), Saved.Num() == 1
        && Saved[0].WorldTransform.Equals(EditedTransform, 0.01f));

    UWorld* RestoreWorld = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_RestoredRoutePaint"));
    ULBFactoryMachineBuilderSubsystem* RestoreBuilder = RestoreWorld
        ? NewObject<ULBFactoryMachineBuilderSubsystem>(RestoreWorld) : nullptr;
    TestTrue(TEXT("Edited walkway restores in a fresh world"), RestoreBuilder
        && RestoreBuilder->RestoreAGVInfrastructure(Saved, Reason));
    ALBFactoryAGVInfrastructure* Reloaded = nullptr;
    if (RestoreWorld)
        for (TActorIterator<ALBFactoryAGVInfrastructure> It(RestoreWorld); It; ++It)
            Reloaded = *It;
    TestTrue(TEXT("Restored walkway keeps automatic safe paint at edited transform"), Reloaded
        && Reloaded->GetActorTransform().Equals(EditedTransform, 0.01f)
        && Reloaded->GetSafetyMarkings()
        && Reloaded->GetSafetyMarkings()->HasNonCollidingPresentation());

    ALBFactoryAGVInfrastructure* Route = World->SpawnActor<ALBFactoryAGVInfrastructure>();
    ALBFactoryAGVInfrastructure* Crossing = World->SpawnActor<ALBFactoryAGVInfrastructure>();
    TestTrue(TEXT("Route and crossing fixtures configure"), Route && Crossing
        && Route->Configure(TEXT("AGV-ROUTE-MARK-001"),
            ELBFactoryAGVInfrastructureType::AGVRouteSegment)
        && Crossing->Configure(TEXT("PED-XING-MARK-001"),
            ELBFactoryAGVInfrastructureType::PedestrianCrossing));
    TestTrue(TEXT("AGV lane paints both dashed blue edges"), Route && Route->GetSafetyMarkings()
        && Route->HasFloorMarkingPresentation()
        && Route->GetSafetyMarkings()->HasNonCollidingPresentation()
        && FMath::IsNearlyEqual(Route->GetFloorMarkingDimensionsCm().Y, 30.0f, 0.01f)
        && Route->GetSafetyMarkings()->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::VehicleLane) >= 6);
    TestTrue(TEXT("Pedestrian crossing paints repeated white zebra bars"), Crossing
        && Crossing->GetSafetyMarkings()
        && Crossing->GetSafetyMarkings()->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::PedestrianCrossing) >= 4);

    if (RestoreWorld) RestoreWorld->DestroyWorld(false);
    World->DestroyWorld(false);
    return true;
}

#endif
