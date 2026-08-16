#if WITH_DEV_AUTOMATION_TESTS

#include "LBInboundDeliveryController.h"

#include "Engine/Engine.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "LBCoilAGVController.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryTransportLink.h"
#include "LBPressShopStorageZone.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBInboundDeliveryContinuousCycleTest,
    "LineBoss.FactoryBuilder.MaterialFlow.InboundDeliveryContinuousCycle",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBInboundDeliveryContinuousCycleTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_InboundDeliveryCycle"));
    TestNotNull(TEXT("Transient inbound world exists"), World);
    if (!World) return false;

    auto SpawnTagged = [World](const FVector& Location, std::initializer_list<FName> Tags)
    {
        AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), Location, FRotator::ZeroRotator);
        if (Actor)
        {
            Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
            for (const FName Tag : Tags) Actor->Tags.Add(Tag);
        }
        return Actor;
    };
    SpawnTagged(FVector(0,0,29), {TEXT("LB.Vehicle.CoilAGV")});
    SpawnTagged(FVector(0,0,64), {TEXT("LB.Vehicle.CoilAGV.LiftDeck")});
    SpawnTagged(FVector(0,0,156), {TEXT("LB.Inventory.InTransfer")});

    ALBCoilAGVController* AGV = World->SpawnActor<ALBCoilAGVController>();
    ALBFactoryBuildMachine* Inbound = World->SpawnActor<ALBFactoryBuildMachine>();
    ALBFactoryBuildMachine* PR002 = World->SpawnActor<ALBFactoryBuildMachine>();
    ALBInboundDeliveryController* Delivery = World->SpawnActor<ALBInboundDeliveryController>();
    ALBPressShopStorageZone* Storage = World->SpawnActor<ALBPressShopStorageZone>();
    ULBFactoryConnectionSubsystem* Connections = NewObject<ULBFactoryConnectionSubsystem>(World);
    TestTrue(TEXT("Retained coil AGV binds"), AGV && AGV->DiscoverAndBind());
    TestTrue(TEXT("Short inbound route configures"), AGV && AGV->ConfigureRoute(
        FVector(0,0,29), FVector(300,0,29), FVector(300,300,29)));
    TestTrue(TEXT("Inbound dock configures"), Inbound && Inbound->Configure(
        TEXT("INBOUND-001"), ELBFactoryBuildMachineType::InboundDeliveryDock));
    TestTrue(TEXT("Two-place PR002 input configures"), PR002 && PR002->Configure(
        TEXT("PR002-001"), ELBFactoryBuildMachineType::CoilWeighInspectionCell)
        && PR002->ConfigureGameplayBuffers(2, 2));
    TestTrue(TEXT("Wrapped-coil storage permits onward handling"), Storage && Storage->Configure(
        TEXT("COIL-STORAGE-001"), ELBPressShopStorageType::BareCoils, 8, FVector(600, 600, 100)));

    ALBFactoryTransportLink* Link = nullptr;
    FString Reason;
    TestTrue(TEXT("Real AGV handoff link connects dock to PR002"), Connections && Connections->Connect(
        Inbound->OutputPort, PR002->InputPort, Link, Reason));
    TestTrue(TEXT("Delivery authority binds retained endpoints"), Delivery && Delivery->Configure(Inbound, PR002, AGV));
    if (!AGV || !Inbound || !PR002 || !Delivery || !Link)
    {
        World->DestroyWorld(false);
        return false;
    }

    auto RunDelivery = [this, AGV, Delivery](const FName CoilId)
    {
        FString StartReason;
        TestTrue(*FString::Printf(TEXT("%s starts at inbound dock"), *CoilId.ToString()),
            Delivery->StartDelivery(CoilId, StartReason));
        for (int32 Step = 0; Step < 500 && Delivery->GetPhase() != ELBInboundDeliveryPhase::Idle
            && Delivery->GetPhase() != ELBInboundDeliveryPhase::Fault; ++Step)
        {
            AGV->Tick(0.1f);
            Delivery->Tick(0.1f);
        }
        TestEqual(*FString::Printf(TEXT("%s completes and AGV returns"), *CoilId.ToString()),
            Delivery->GetPhase(), ELBInboundDeliveryPhase::Idle);
    };

    RunDelivery(TEXT("COIL-HEAT-0001"));
    TestEqual(TEXT("First identified coil is accepted by PR002 once"), PR002->GetInputUnitCount(), 1);
    TestEqual(TEXT("PR002 retains the first exact coil identity"),
        PR002->CaptureSaveState().InputUnitIds[0], FName(TEXT("COIL-HEAT-0001")));
    TestEqual(TEXT("First physical handoff counted once"), Link->GetTransferredUnits(), 1);
    RunDelivery(TEXT("COIL-HEAT-0002"));
    TestEqual(TEXT("Second identified coil is accepted by PR002 once"), PR002->GetInputUnitCount(), 2);
    TestEqual(TEXT("Two completed deliveries retained"), Delivery->GetCompletedDeliveries(), 2);
    TestEqual(TEXT("Two physical handoffs counted"), Link->GetTransferredUnits(), 2);

    FLBInboundDeliverySaveState Saved = Delivery->CaptureSaveState();
    TestTrue(TEXT("Idle delivery coordinator round-trips"), Delivery->RestoreSaveState(Saved));
    TestTrue(TEXT("Occupied PR002 still allows the third coil to be unloaded and held"),
        Delivery->StartDelivery(TEXT("COIL-HEAT-0003"), Reason));
    TestEqual(TEXT("Third coil waits safely instead of dispatching into full PR002"),
        Delivery->GetPhase(), ELBInboundDeliveryPhase::WaitingForStorage);
    TestEqual(TEXT("No third handoff crosses the process link"), Link->GetTransferredUnits(), 2);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBInboundDeliveryVisibleFourCoilUnloadTest,
    "LineBoss.FactoryBuilder.MaterialFlow.InboundDeliveryVisibleFourCoilUnload",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBInboundDeliveryVisibleFourCoilUnloadTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_InboundVisibleFourCoilUnload"));
    TestNotNull(TEXT("Transient visible inbound world exists"), World);
    if (!World) return false;

    auto SpawnMovable = [World](const FVector& Location)
    {
        AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), Location, FRotator::ZeroRotator);
        if (Actor) Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
        return Actor;
    };
    AStaticMeshActor* AGVBody = SpawnMovable(FVector(0, 0, 29));
    AStaticMeshActor* AGVDeck = SpawnMovable(FVector(0, 0, 64));
    AStaticMeshActor* AGVLoad = SpawnMovable(FVector(0, 0, 156));
    AGVBody->Tags.Add(TEXT("LB.Vehicle.CoilAGV"));
    AGVDeck->Tags.Add(TEXT("LB.Vehicle.CoilAGV.LiftDeck"));
    AGVLoad->Tags.Add(TEXT("LB.Inventory.InTransfer"));

    ALBCoilAGVController* AGV = World->SpawnActor<ALBCoilAGVController>();
    ALBFactoryBuildMachine* Inbound = World->SpawnActor<ALBFactoryBuildMachine>();
    ALBFactoryBuildMachine* PR002 = World->SpawnActor<ALBFactoryBuildMachine>();
    ALBInboundDeliveryController* Delivery = World->SpawnActor<ALBInboundDeliveryController>();
    ALBPressShopStorageZone* Storage = World->SpawnActor<ALBPressShopStorageZone>();
    ULBFactoryConnectionSubsystem* Connections = NewObject<ULBFactoryConnectionSubsystem>(World);
    TestTrue(TEXT("Visible sequence AGV binds"), AGV && AGV->DiscoverAndBind());
    TestTrue(TEXT("Visible sequence AGV route configures"), AGV && AGV->ConfigureRoute(
        FVector(0, 0, 29), FVector(200, 0, 29), FVector(200, 200, 29)));
    TestTrue(TEXT("Visible inbound dock configures"), Inbound && Inbound->Configure(
        TEXT("INBOUND-VISIBLE-001"), ELBFactoryBuildMachineType::InboundDeliveryDock));
    TestTrue(TEXT("Four-place visible PR002 input configures"), PR002 && PR002->Configure(
        TEXT("PR002-VISIBLE-001"), ELBFactoryBuildMachineType::CoilWeighInspectionCell)
        && PR002->ConfigureGameplayBuffers(4, 4));
    TestTrue(TEXT("Visible sequence has wrapped-coil storage"), Storage && Storage->Configure(
        TEXT("COIL-STORAGE-VISIBLE-001"), ELBPressShopStorageType::BareCoils, 8, FVector(600, 600, 100)));
    ALBFactoryTransportLink* Link = nullptr;
    FString Reason;
    TestTrue(TEXT("Visible sequence transport link connects"), Connections && Connections->Connect(
        Inbound->OutputPort, PR002->InputPort, Link, Reason));
    TestTrue(TEXT("Visible delivery authority binds endpoints"), Delivery && Delivery->Configure(Inbound, PR002, AGV));

    AStaticMeshActor* Lorry = SpawnMovable(FVector(-300, 0, 0));
    AStaticMeshActor* Bridge = SpawnMovable(FVector(0, 0, 600));
    AStaticMeshActor* Trolley = SpawnMovable(FVector(0, 0, 560));
    AStaticMeshActor* Hoist = SpawnMovable(FVector(0, 0, 500));
    AStaticMeshActor* Hook = SpawnMovable(FVector(0, 0, 450));
    AStaticMeshActor* Saddle = SpawnMovable(FVector(300, 300, 100));
    TArray<AActor*> TrailerCoils;
    for (int32 Index = 0; Index < 4; ++Index)
        TrailerCoils.Add(SpawnMovable(FVector(-300, Index * 60.0f, 100)));
    TestTrue(TEXT("Exactly four trailer coils bind to visible sequence"), Delivery && Delivery->ConfigureVisualSequence(
        Lorry, Bridge, Trolley, Hoist, Hook, Saddle, TrailerCoils, FVector(-300, 0, 0), FVector(0, 0, 0)));
    TestFalse(TEXT("Authored unload sequence does not opt into player-builder rediscovery"),
        Delivery && Delivery->IsPlayerBuilderBootstrapEnabled());

    if (!AGV || !Inbound || !PR002 || !Delivery || !Link)
    {
        World->DestroyWorld(false);
        return false;
    }
    for (int32 DeliveryIndex = 0; DeliveryIndex < 4; ++DeliveryIndex)
    {
        const FName CoilId(*FString::Printf(TEXT("COIL-VISIBLE-%04d"), DeliveryIndex + 1));
        TestTrue(*FString::Printf(TEXT("Visible coil %d starts"), DeliveryIndex + 1), Delivery->StartDelivery(CoilId, Reason));
        TestEqual(TEXT("Visible unloading reserves identity before AGV dispatch"),
            AGV->GetActiveCoilId(), FString());
        bool bSaveChecked = false;
        bool bObservedProvedHandoff = false;
        for (int32 Step = 0; Step < 2500 && Delivery->GetPhase() != ELBInboundDeliveryPhase::Idle
            && Delivery->GetPhase() != ELBInboundDeliveryPhase::Fault; ++Step)
        {
            AGV->Tick(0.05f);
            Delivery->Tick(0.05f);
            bObservedProvedHandoff |= Delivery->GetPhase() == ELBInboundDeliveryPhase::AGVHandoff;
            if (!bSaveChecked && Delivery->GetPhase() == ELBInboundDeliveryPhase::CoilLift)
            {
                const FLBInboundDeliverySaveState MidUnload = Delivery->CaptureSaveState();
                TestEqual(TEXT("Visible unload save schema is v6"), MidUnload.SaveVersion, 6);
                TestEqual(TEXT("Retained visible unload persists the legacy source mode"),
                    MidUnload.SourceMode, ELBInboundDeliverySourceMode::LegacyLorry);
                TestEqual(TEXT("Visible unload save targets PR002"),
                    MidUnload.PR002MachineId, FName(TEXT("PR002-VISIBLE-001")));
                TestTrue(TEXT("Mid-unload state restores without losing identity"), Delivery->RestoreSaveState(MidUnload));
                bSaveChecked = true;
            }
        }
        TestEqual(*FString::Printf(TEXT("Visible coil %d completes (phase reason: %s)"),
                DeliveryIndex + 1, *Delivery->GetLastReason()),
            Delivery->GetPhase(), ELBInboundDeliveryPhase::Idle);
        TestTrue(TEXT("Mid-unload persistence was exercised"), bSaveChecked);
        TestTrue(TEXT("Proved AGV handoff remains observable"), bObservedProvedHandoff);
        TestTrue(TEXT("Unloaded trailer coil is no longer duplicated on trailer"), TrailerCoils[DeliveryIndex]->IsHidden());
    }
    TestEqual(TEXT("Exactly four visible deliveries complete"), Delivery->GetCompletedDeliveries(), 4);
    TestEqual(TEXT("Exactly four identified coils reach PR002"), PR002->GetInputUnitCount(), 4);
    const FLBFactoryBuildMachineSaveState PR002State = PR002->CaptureSaveState();
    TestTrue(TEXT("PR002 preserves all four exact inbound identities"),
        PR002State.InputUnitIds == TArray<FName>({TEXT("COIL-VISIBLE-0001"), TEXT("COIL-VISIBLE-0002"),
            TEXT("COIL-VISIBLE-0003"), TEXT("COIL-VISIBLE-0004")}));
    TestEqual(TEXT("Exactly four physical handoffs cross the process link"), Link->GetTransferredUnits(), 4);
    TestFalse(TEXT("Empty four-coil trailer cannot originate a fifth coil"),
        Delivery->StartDelivery(TEXT("COIL-VISIBLE-0005"), Reason));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPlayerBuiltModularInboundUnloadTest,
    "LineBoss.FactoryBuilder.MaterialFlow.PlayerBuiltModularInboundUnload",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlayerBuiltModularInboundUnloadTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PlayerBuiltModularInbound"));
    if (!World) return false;
    auto SpawnTagged = [World](const FVector& Location, const FName Tag)
    {
        AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), Location, FRotator::ZeroRotator);
        if (Actor) { Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable); Actor->Tags.Add(Tag); }
        return Actor;
    };
    SpawnTagged(FVector(0,0,29), TEXT("LB.Vehicle.CoilAGV"));
    SpawnTagged(FVector(0,0,64), TEXT("LB.Vehicle.CoilAGV.LiftDeck"));
    SpawnTagged(FVector(0,0,156), TEXT("LB.Inventory.InTransfer"));
    ALBCoilAGVController* AGV = World->SpawnActor<ALBCoilAGVController>();
    ALBFactoryBuildMachine* Inbound = World->SpawnActor<ALBFactoryBuildMachine>();
    ALBFactoryBuildMachine* PR002 = World->SpawnActor<ALBFactoryBuildMachine>();
    ALBInboundDeliveryController* Delivery = World->SpawnActor<ALBInboundDeliveryController>();
    ALBPressShopStorageZone* Storage = World->SpawnActor<ALBPressShopStorageZone>();
    ULBFactoryConnectionSubsystem* Connections = NewObject<ULBFactoryConnectionSubsystem>(World);
    TestTrue(TEXT("Modular AGV binds"), AGV && AGV->DiscoverAndBind());
    TestTrue(TEXT("Modular AGV route configures"), AGV && AGV->ConfigureRoute(
        FVector(0,0,29), FVector(250,0,29), FVector(250,250,29)));
    TestTrue(TEXT("Approved modular inbound package configures"), Inbound && Inbound->Configure(
        TEXT("INBOUND-MODULAR-001"), ELBFactoryBuildMachineType::InboundDeliveryDock));
    TestTrue(TEXT("Modular PR002 endpoint configures"), PR002 && PR002->Configure(
        TEXT("PR002-MODULAR-001"), ELBFactoryBuildMachineType::CoilWeighInspectionCell));
    TestTrue(TEXT("Modular sequence has wrapped-coil storage"), Storage && Storage->Configure(
        TEXT("COIL-STORAGE-MODULAR-001"), ELBPressShopStorageType::BareCoils, 8, FVector(600, 600, 100)));
    ALBFactoryTransportLink* Link = nullptr;
    FString Reason;
    TestTrue(TEXT("Modular handoff link connects"), Connections && Connections->Connect(
        Inbound->OutputPort, PR002->InputPort, Link, Reason));
    TestTrue(TEXT("Modular authority binds process endpoints"), Delivery && Delivery->Configure(Inbound, PR002, AGV));
    TestTrue(TEXT("Modular authority binds the player-built coil-handler and load components"),
        Delivery && Delivery->ConfigurePlayerBuiltVisualSequence(Inbound));
    USceneComponent* HandlerChassis = Inbound->GetInboundCoilHandlerChassisComponent();
    USceneComponent* HandlerLift = Inbound->GetInboundCoilHandlerRamComponent();
    const FTransform HandlerChassisHome = HandlerChassis
        ? HandlerChassis->GetComponentTransform() : FTransform::Identity;
    const FVector LiftToChassisHomeLocal = HandlerChassis && HandlerLift
        ? HandlerChassisHome.InverseTransformVectorNoScale(
            HandlerLift->GetComponentLocation() - HandlerChassis->GetComponentLocation())
        : FVector::ZeroVector;
    USceneComponent* FixedFrontAxle = Inbound
        ? Inbound->GetInboundCoilHandlerFixedFrontAxleRoot() : nullptr;
    USceneComponent* RearSteeringRoot = Inbound
        ? Inbound->GetInboundCoilHandlerRearSteeringRoot() : nullptr;
    TestNotNull(TEXT("Coil-handler exposes its fixed front/load axle root"), FixedFrontAxle);
    TestNotNull(TEXT("Coil-handler exposes its rear steering pivot"), RearSteeringRoot);
    TestTrue(TEXT("Equal body-yaw demand reverses the rear-wheel command while backing"),
        Delivery && Delivery->CalculateCoilHandlerRearSteerAngleDegrees(100.0f, 18.0f)
            * Delivery->CalculateCoilHandlerRearSteerAngleDegrees(-100.0f, 18.0f) < 0.0f);
    TestTrue(TEXT("Loaded coil-handler sweep includes body diagonal and counterweight swing"),
        Delivery && Delivery->GetCoilHandlerSweptClearanceRadiusCm()
            > FVector2D(320.0f, 110.0f).Size());
    TestTrue(TEXT("First modular delivery starts"), Delivery && Delivery->StartDelivery(TEXT("COIL-MODULAR-0001"), Reason));
    bool bObservedBoreEngagement = false;
    bool bObservedSaddleSeat = false;
    bool bVerifiedMidUnloadRestore = false;
    bool bObservedWholeVehicleTravel = false;
    bool bObservedLocalLiftArticulation = false;
    for (int32 Step = 0; Step < 3000 && Delivery->GetPhase() != ELBInboundDeliveryPhase::Idle
        && Delivery->GetPhase() != ELBInboundDeliveryPhase::Fault; ++Step)
    {
        AGV->Tick(0.05f);
        Delivery->Tick(0.05f);
        UStaticMeshComponent* Hook = Inbound->GetInboundCHookComponent();
        UStaticMeshComponent* Coil = Inbound->GetTrailerCoilComponent(0);
        if (HandlerChassis && Hook)
        {
            bObservedWholeVehicleTravel |= FVector::Dist2D(
                HandlerChassis->GetComponentLocation(), HandlerChassisHome.GetLocation()) > 5.0f;
            const FVector LiftToChassisLocal = HandlerChassis->GetComponentTransform()
                .InverseTransformVectorNoScale(
                    Hook->GetComponentLocation() - HandlerChassis->GetComponentLocation());
            bObservedLocalLiftArticulation |= FMath::Abs(
                LiftToChassisLocal.Z - LiftToChassisHomeLocal.Z) > 5.0f;
            TestTrue(TEXT("Coil-handler body and lift assembly stay registered in the floor plane"),
                FVector2D(LiftToChassisLocal.X, LiftToChassisLocal.Y).Equals(
                    FVector2D(LiftToChassisHomeLocal.X, LiftToChassisHomeLocal.Y), 0.1f));
            TestTrue(TEXT("Coil-handler chassis never lifts with the mast"),
                FMath::IsNearlyEqual(HandlerChassis->GetComponentLocation().Z,
                    HandlerChassisHome.GetLocation().Z, 0.1f));
        }
        if (!bVerifiedMidUnloadRestore && Delivery->GetPhase() == ELBInboundDeliveryPhase::CoilLift)
        {
            USceneComponent* Bridge = Inbound->GetInboundCraneBridgeComponent();
            USceneComponent* Trolley = Cast<USceneComponent>(Inbound->GetDefaultSubobjectByName(TEXT("InboundCraneTrolleyVisual")));
            USceneComponent* Hoist = Cast<USceneComponent>(Inbound->GetDefaultSubobjectByName(TEXT("InboundCraneHoistVisual")));
            const FLBInboundDeliverySaveState MidUnload = Delivery->CaptureSaveState();
            USceneComponent* Chassis = Inbound->GetInboundCoilHandlerChassisComponent();
            TestEqual(TEXT("Player-built unload save schema is v6"), MidUnload.SaveVersion, 6);
            TestEqual(TEXT("Retained modular unload persists the legacy source mode"),
                MidUnload.SourceMode, ELBInboundDeliverySourceMode::LegacyLorry);
            TestTrue(TEXT("Player-built handler components are available for persistence"),
                Chassis && Bridge && Trolley && Hoist && Hook);
            if (Chassis && Bridge && Trolley && Hoist && Hook)
            {
                Chassis->AddWorldOffset(FVector(15, 25, 35), false, nullptr, ETeleportType::TeleportPhysics);
                Bridge->AddWorldOffset(FVector(111, 222, 333), false, nullptr, ETeleportType::TeleportPhysics);
                Trolley->AddWorldOffset(FVector(-77, 88, 99), false, nullptr, ETeleportType::TeleportPhysics);
                Hoist->AddWorldOffset(FVector(44, -55, 66), false, nullptr, ETeleportType::TeleportPhysics);
                Hook->AddWorldOffset(FVector(-12, -23, -34), false, nullptr, ETeleportType::TeleportPhysics);
                TestTrue(TEXT("Mid-unload v6 handler state restores"), Delivery->RestoreSaveState(MidUnload));
                TestTrue(TEXT("Coil-handler chassis pose restores exactly"),
                    Chassis->GetComponentTransform().Equals(MidUnload.CoilHandlerChassisTransform, 0.01f));
                TestTrue(TEXT("Bridge pose restores exactly"), Bridge->GetComponentTransform().Equals(MidUnload.CraneBridgeTransform, 0.01f));
                TestTrue(TEXT("Trolley pose restores exactly"), Trolley->GetComponentTransform().Equals(MidUnload.CraneTrolleyTransform, 0.01f));
                TestTrue(TEXT("Hoist pose restores exactly"), Hoist->GetComponentTransform().Equals(MidUnload.CraneHoistTransform, 0.01f));
                TestTrue(TEXT("C-hook pose restores exactly"), Hook->GetComponentTransform().Equals(MidUnload.CraneHookTransform, 0.01f));
                TestEqual(TEXT("Mid-unload phase survives restore"), Delivery->GetPhase(), ELBInboundDeliveryPhase::CoilLift);
                TestEqual(TEXT("Mid-unload coil identity survives restore"), Delivery->GetActiveCoilId(), FName(TEXT("COIL-MODULAR-0001")));
                bVerifiedMidUnloadRestore = true;
            }
        }
        if (Hook && Coil && Coil->GetStaticMesh()
            && Delivery->GetPhase() == ELBInboundDeliveryPhase::HookEngage)
        {
            const FVector HookLoadCentre = Hook->GetComponentLocation()
                + Hook->GetComponentQuat().RotateVector(FVector(-301.5f, 0.0f, 110.0f));
            const FVector CoilBoreCentre = Coil->GetComponentLocation()
                + Coil->GetComponentQuat().RotateVector(Coil->GetStaticMesh()->GetBounds().Origin);
            bObservedBoreEngagement |= HookLoadCentre.Equals(CoilBoreCentre, 1.0f);
        }
        if (Coil && Delivery->GetPhase() == ELBInboundDeliveryPhase::SaddleRelease)
            bObservedSaddleSeat |= Coil->GetComponentLocation().Equals(
                Inbound->GetReceivingSaddleLoadPoint(), 1.0f);
    }
    TestTrue(TEXT("Coil-handler ram engages the wrapped-coil bore datum"), bObservedBoreEngagement);
    TestTrue(TEXT("Coil-handler chassis travels with the lift assembly"), bObservedWholeVehicleTravel);
    TestTrue(TEXT("Coil-handler mast remains a local vertical articulation"), bObservedLocalLiftArticulation);
    TestFalse(TEXT("Coil-handler does not finish with its chassis frozen at the spawn pose"),
        HandlerChassis && HandlerChassis->GetComponentTransform().Equals(HandlerChassisHome, 0.01f));
    TestTrue(TEXT("Wrapped-coil bottom pivot seats on the receiving saddle top"), bObservedSaddleSeat);
    TestTrue(TEXT("Mid-unload handler and carried-coil pose restores before completing"), bVerifiedMidUnloadRestore);
    TestEqual(TEXT("Player-built modular unload completes"), Delivery->GetPhase(), ELBInboundDeliveryPhase::Idle);
    TestEqual(TEXT("One wrapped coil leaves the modular trailer"), Inbound->GetVisibleTrailerCoilCount(), 3);
    TestEqual(TEXT("One identified coil reaches player-built PR002"), PR002->GetInputUnitCount(), 1);
    const FLBFactoryBuildMachineSaveState PR002AfterFirstDelivery =
        PR002->CaptureSaveState();
    TestTrue(TEXT("Player-built PR002 exposes a delivered identity before it is inspected"),
        !PR002AfterFirstDelivery.InputUnitIds.IsEmpty());
    if (!PR002AfterFirstDelivery.InputUnitIds.IsEmpty())
    {
        TestEqual(TEXT("Player-built PR002 retains the exact delivered identity"),
            PR002AfterFirstDelivery.InputUnitIds[0], FName(TEXT("COIL-MODULAR-0001")));
    }
    TestEqual(TEXT("One physical modular handoff is counted"), Link ? Link->GetTransferredUnits() : 0, 1);

    // The second trailer position adds a lateral component, exercising real rear-steer
    // kinematics rather than proving only the first straight fore/aft shuttle.
    TestTrue(TEXT("Second modular coil starts the steering exercise"), Delivery
        && Delivery->StartDelivery(TEXT("COIL-MODULAR-0002"), Reason));
    bool bObservedRearWheelSteer = false;
    bool bObservedYawWhileTranslating = false;
    bool bObservedStationaryPivot = false;
    float MaximumHandlerYawStepDegrees = 0.0f;
    FVector PreviousHandlerLocation = HandlerChassis
        ? HandlerChassis->GetComponentLocation() : FVector::ZeroVector;
    float PreviousHandlerYawDegrees = HandlerChassis
        ? HandlerChassis->GetComponentRotation().Yaw : 0.0f;
    for (int32 Step = 0; Step < 3500 && Delivery
        && Delivery->GetPhase() != ELBInboundDeliveryPhase::Idle
        && Delivery->GetPhase() != ELBInboundDeliveryPhase::Fault; ++Step)
    {
        AGV->Tick(0.05f);
        Delivery->Tick(0.05f);
        if (!HandlerChassis) continue;
        const FVector CurrentHandlerLocation = HandlerChassis->GetComponentLocation();
        const float CurrentHandlerYawDegrees = HandlerChassis->GetComponentRotation().Yaw;
        const float TranslationCm = FVector::Dist2D(
            PreviousHandlerLocation, CurrentHandlerLocation);
        const float YawStepDegrees = FMath::Abs(FMath::FindDeltaAngleDegrees(
            PreviousHandlerYawDegrees, CurrentHandlerYawDegrees));
        MaximumHandlerYawStepDegrees = FMath::Max(
            MaximumHandlerYawStepDegrees, YawStepDegrees);
        if (YawStepDegrees > 0.01f)
        {
            bObservedYawWhileTranslating |= TranslationCm > 0.01f;
            bObservedStationaryPivot |= TranslationCm <= 0.01f;
        }
        bObservedRearWheelSteer |= FMath::Abs(
            Delivery->GetCoilHandlerRearSteerAngleDegrees()) > 0.5f;
        TestTrue(TEXT("Front/load axle remains fixed while CHF01 moves"),
            !FixedFrontAxle || FMath::IsNearlyZero(
                FixedFrontAxle->GetRelativeRotation().Yaw, 0.01f));
        TestTrue(TEXT("Visible rear pivot follows the kinematic steering command"),
            !RearSteeringRoot || FMath::IsNearlyEqual(
                RearSteeringRoot->GetRelativeRotation().Yaw,
                Delivery->GetCoilHandlerRearSteerAngleDegrees(), 0.05f));
        PreviousHandlerLocation = CurrentHandlerLocation;
        PreviousHandlerYawDegrees = CurrentHandlerYawDegrees;
    }
    TestEqual(TEXT("Second rear-steer delivery completes"),
        Delivery ? Delivery->GetPhase() : ELBInboundDeliveryPhase::Fault,
        ELBInboundDeliveryPhase::Idle);
    TestTrue(TEXT("Rear axle visibly steers on the offset trailer position"),
        bObservedRearWheelSteer);
    TestTrue(TEXT("CHF01 changes heading only while its full chassis translates"),
        bObservedYawWhileTranslating && !bObservedStationaryPivot);
    TestTrue(TEXT("Rear-steer body yaw is limited to a smooth frame-sized step"),
        MaximumHandlerYawStepDegrees <= 1.8f);
    TestTrue(TEXT("Front/load wheels finish straight"), Delivery
        && FMath::IsNearlyZero(Delivery->GetCoilHandlerFrontWheelSteerAngleDegrees(), 0.01f));
    TestTrue(TEXT("Rear wheels straighten after the handler stops"), Delivery
        && FMath::IsNearlyZero(Delivery->GetCoilHandlerRearSteerAngleDegrees(), 0.01f));

    ALBFactoryBuildMachine* SweepObstacle = World->SpawnActor<ALBFactoryBuildMachine>(
        ALBFactoryBuildMachine::StaticClass(), FTransform(FVector(0.0f, 620.0f, 0.0f)));
    TestTrue(TEXT("Counterweight sweep obstacle configures"), SweepObstacle
        && SweepObstacle->Configure(TEXT("CHF01-SWEEP-OBSTACLE"),
            ELBFactoryBuildMachineType::DepackagingRobot));
    TestFalse(TEXT("Loaded swept envelope rejects clearance missed by a chassis-only trace"),
        Delivery && Delivery->IsCoilHandlerSweptPathClear(
            FVector::ZeroVector, FVector(100.0f, 0.0f, 0.0f)));
    if (SweepObstacle) SweepObstacle->SetActorLocation(FVector(0.0f, 1400.0f, 0.0f));
    TestTrue(TEXT("The same path is accepted once the full loaded sweep is clear"),
        Delivery && Delivery->IsCoilHandlerSweptPathClear(
            FVector::ZeroVector, FVector(100.0f, 0.0f, 0.0f)));
    World->DestroyWorld(false);
    return true;
}

#endif
