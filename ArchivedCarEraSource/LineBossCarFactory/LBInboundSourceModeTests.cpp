#if WITH_DEV_AUTOMATION_TESTS

#include "LBInboundDeliveryController.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "LBCoilAGVController.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryTransportLink.h"
#include "LBPressShopStorageZone.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBNativeAGVInboundSourceModeTest,
    "LineBoss.OneFactory.Inbound.NativeAGVArrivalExactProvenanceAndSave",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBNativeAGVInboundSourceModeTest::RunTest(const FString& Parameters)
{
    const FString NativeChassisPath = TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_Chassis_Candidate_v001.SM_LB_CoilAGV_Chassis_Candidate_v001");
    const FString NativeDeckPath = TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/CoilAGV/Candidate_v001/SM_LB_CoilAGV_LiftDeck_Candidate_v001.SM_LB_CoilAGV_LiftDeck_Candidate_v001");
    const FString NativeLoadPath = TEXT("/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005.SM_LB_MasterCoil_Candidate_v005");
    TestTrue(TEXT("Procedural chassis is on the exact native allowlist"),
        ALBCoilAGVController::IsNativeOneFactoryPresentationAssetPathAllowed(NativeChassisPath));
    TestTrue(TEXT("Procedural lift deck is on the exact native allowlist"),
        ALBCoilAGVController::IsNativeOneFactoryPresentationAssetPathAllowed(NativeDeckPath));
    TestTrue(TEXT("Retained native master coil is on the exact native allowlist"),
        ALBCoilAGVController::IsNativeOneFactoryPresentationAssetPathAllowed(NativeLoadPath));
    TestFalse(TEXT("A non-allowlisted path is rejected even when it names an AGV"),
        ALBCoilAGVController::IsNativeOneFactoryPresentationAssetPathAllowed(
            TEXT("/Game/LineBoss/Meshy/SM_CoilAGV.SM_CoilAGV")));
    TestFalse(TEXT("The retained lorry-era AGV path is not native One Factory provenance"),
        ALBCoilAGVController::IsNativeOneFactoryPresentationAssetPathAllowed(
            TEXT("/Game/LineBoss/Runtime/PressShop/CoilAGV/UntouchedControlled_v20260810/SM_Cairnwell_CoilAGV_UntouchedControlled_v20260810.SM_Cairnwell_CoilAGV_UntouchedControlled_v20260810")));

    UWorld* ContaminatedWorld = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_NativeAGVContaminationGate"));
    AActor* RetainedTaggedVehicle = ContaminatedWorld
        ? ContaminatedWorld->SpawnActor<AActor>() : nullptr;
    if (RetainedTaggedVehicle) RetainedTaggedVehicle->Tags.Add(TEXT("LB.Vehicle.CoilAGV"));
    ALBCoilAGVController* ContaminatedAGV = ContaminatedWorld
        ? ContaminatedWorld->SpawnActor<ALBCoilAGVController>() : nullptr;
    FString ContaminationReason;
    TestFalse(TEXT("Native presentation rejects a tag-bound retained vehicle"),
        ContaminatedAGV && ContaminatedAGV->ConfigureNativeOneFactoryPresentation(
            ContaminationReason));
    TestTrue(TEXT("Native provenance failure names tag-bound contamination"),
        ContaminationReason.Contains(TEXT("TAG-BOUND LEGACY PRESENTATION")));
    if (ContaminatedWorld) ContaminatedWorld->DestroyWorld(false);

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_NativeAGVInboundSourceMode"));
    TestNotNull(TEXT("Transient native inbound world exists"), World);
    if (!World) return false;

    ALBCoilAGVController* AGV = World->SpawnActor<ALBCoilAGVController>();
    ALBFactoryBuildMachine* Inbound = World->SpawnActor<ALBFactoryBuildMachine>();
    ALBFactoryBuildMachine* PR002 = World->SpawnActor<ALBFactoryBuildMachine>();
    ALBInboundDeliveryController* Delivery = World->SpawnActor<ALBInboundDeliveryController>();
    ALBPressShopStorageZone* Storage = World->SpawnActor<ALBPressShopStorageZone>();
    ULBFactoryConnectionSubsystem* Connections = NewObject<ULBFactoryConnectionSubsystem>(World);
    TestTrue(TEXT("Native inbound dock configures"), Inbound && Inbound->Configure(
        TEXT("ONEFACTORY-INBOUND-001"), ELBFactoryBuildMachineType::InboundDeliveryDock));
    TestTrue(TEXT("Native PR002 configures"), PR002 && PR002->Configure(
        TEXT("ONEFACTORY-PR002-001"), ELBFactoryBuildMachineType::CoilWeighInspectionCell)
        && PR002->ConfigureGameplayBuffers(2, 2));
    TestTrue(TEXT("Native inbound retains a real wrapped-coil buffer"), Storage && Storage->Configure(
        TEXT("ONEFACTORY-COIL-STORAGE-001"), ELBPressShopStorageType::BareCoils,
        8, FVector(600.0f, 600.0f, 100.0f)));
    ALBFactoryTransportLink* Link = nullptr;
    FString Reason;
    TestTrue(TEXT("Native dock-to-PR002 link connects"), Connections && Connections->Connect(
        Inbound->OutputPort, PR002->InputPort, Link, Reason));
    TestTrue(TEXT("Native AGV source mode binds atomically"), Delivery
        && Delivery->ConfigureForSourceMode(Inbound, PR002, AGV,
            ELBInboundDeliverySourceMode::NativeAGVArrival, Reason));
    TestEqual(TEXT("Inbound authority records native AGV arrival"),
        Delivery ? Delivery->GetSourceMode() : ELBInboundDeliverySourceMode::LegacyLorry,
        ELBInboundDeliverySourceMode::NativeAGVArrival);
    TestTrue(TEXT("AGV proves the exact owned native presentation"),
        AGV && AGV->IsUsingNativeOneFactoryPresentation());
    TestFalse(TEXT("Native inbound never binds a lorry/coil-handler visual sequence"),
        Delivery && Delivery->IsVisualSequenceBound());
    TestTrue(TEXT("Native dock presentation retires the lorry and coil-handler package"),
        Inbound && Inbound->IsUsingNativeAGVArrivalPresentation());
    TestEqual(TEXT("Native dock exposes no trailer-source coils"),
        Inbound ? Inbound->GetVisibleTrailerCoilCount() : -1, 0);
    TestFalse(TEXT("Native dock hides the retained lorry visual"),
        Inbound && Inbound->GetApprovedVisualComponent()
            && Inbound->GetApprovedVisualComponent()->IsVisible());
    TestTrue(TEXT("Native chassis component uses the exact allowlisted asset"),
        AGV && AGV->GetApprovedChassisVisual()
        && AGV->GetApprovedChassisVisual()->GetStaticMesh()
        && AGV->GetApprovedChassisVisual()->GetStaticMesh()->GetPathName() == NativeChassisPath);
    TestTrue(TEXT("Native lift deck remains a separate visible articulation"),
        AGV && AGV->GetApprovedLiftDeckVisual()
        && AGV->GetApprovedLiftDeckVisual()->GetStaticMesh()
        && AGV->GetApprovedLiftDeckVisual()->GetStaticMesh()->GetPathName() == NativeDeckPath
        && AGV->GetApprovedLiftDeckVisual()->IsVisible());
    TestTrue(TEXT("Native loaded coil uses the exact allowlisted asset"),
        AGV && AGV->GetApprovedLoadVisual() && AGV->GetApprovedLoadVisual()->GetStaticMesh()
        && AGV->GetApprovedLoadVisual()->GetStaticMesh()->GetPathName() == NativeLoadPath);
    TestTrue(TEXT("Native AGV route configures"), AGV && AGV->ConfigureRoute(
        FVector(0.0f, 0.0f, 29.0f), FVector(300.0f, 0.0f, 29.0f),
        FVector(300.0f, 300.0f, 29.0f)));

    if (!AGV || !Inbound || !PR002 || !Delivery || !Link)
    {
        World->DestroyWorld(false);
        return false;
    }
    TestTrue(TEXT("Native identified coil starts without a lorry unload phase"),
        Delivery->StartDelivery(TEXT("COIL-NATIVE-0001"), Reason));
    TestEqual(TEXT("Native arrival dispatches directly by AGV"),
        Delivery->GetPhase(), ELBInboundDeliveryPhase::AGVDispatch);
    for (int32 Step = 0; Step < 500
        && Delivery->GetPhase() != ELBInboundDeliveryPhase::Idle
        && Delivery->GetPhase() != ELBInboundDeliveryPhase::Fault; ++Step)
    {
        AGV->Tick(0.1f);
        Delivery->Tick(0.1f);
    }
    TestEqual(*FString::Printf(TEXT("Native delivery completes (%s)"),
        *Delivery->GetLastReason()), Delivery->GetPhase(), ELBInboundDeliveryPhase::Idle);
    TestEqual(TEXT("Native delivery reaches PR002 exactly once"),
        PR002->GetInputUnitCount(), 1);
    TestEqual(TEXT("Native physical handoff crosses the real link exactly once"),
        Link->GetTransferredUnits(), 1);

    const FLBInboundDeliverySaveState NativeSave = Delivery->CaptureSaveState();
    TestEqual(TEXT("Source-aware inbound save schema is v7"), NativeSave.SaveVersion, 7);
    TestEqual(TEXT("Native source mode persists"), NativeSave.SourceMode,
        ELBInboundDeliverySourceMode::NativeAGVArrival);
    TestTrue(TEXT("Native v7 save restores into the same proved source mode"),
        Delivery->RestoreSaveState(NativeSave));
    FLBInboundDeliverySaveState LegacyV5 = NativeSave;
    LegacyV5.SaveVersion = 5;
    LegacyV5.SourceMode = ELBInboundDeliverySourceMode::NativeAGVArrival;
    TestFalse(TEXT("A pre-v6 legacy save cannot cross into native One Factory"),
        Delivery->RestoreSaveState(LegacyV5));

    World->DestroyWorld(false);
    return true;
}

#endif
