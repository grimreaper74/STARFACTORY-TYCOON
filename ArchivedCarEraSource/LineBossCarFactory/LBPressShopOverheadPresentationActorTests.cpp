#if WITH_DEV_AUTOMATION_TESTS

#include "LBPressShopOverheadPresentationActor.h"

#include "Components/ActorComponent.h"
#include "Components/RectLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "LBPressShopOverheadVisualLayerActor.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/App.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPressShopOverheadNativePresentationContractTest,
    "LineBoss.PressShop.Overhead.NativePresentationContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPressShopOverheadStateMappingTest,
    "LineBoss.PressShop.Overhead.StateMapping",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPressShopOverheadVisualLayerContractTest,
    "LineBoss.PressShop.Overhead.VisualLayerContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPressShopOverheadCoilFeedMotionContractTest,
    "LineBoss.PressShop.Overhead.CoilFeedMotionContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPressShopOverheadNativePresentationContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_PressShop_Overhead_NativePresentation"));
    ALBPressShopOverheadPresentationActor* Presentation = World
        ? World->SpawnActor<ALBPressShopOverheadPresentationActor>() : nullptr;
    if (!TestNotNull(TEXT("overhead presentation actor spawns"), Presentation))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestFalse(TEXT("presentation never owns production state"),
        Presentation->OwnsProductionState());
    TestTrue(TEXT("stable presentation tag is present"),
        Presentation->ActorHasTag(
            ALBPressShopOverheadPresentationActor::GetPresentationTag()));
    TestEqual(TEXT("one native beacon exists for every placed machine"),
        Presentation->GetStatusBeaconCount(), 14);
    TestEqual(TEXT("four inspection/depack task lights are native components"),
        Presentation->GetTaskLightCount(), 4);

    const FName MachineIds[] = {
        TEXT("IN01_ARTICULATED_CARRIER"), TEXT("IN02_COIL_HANDLER_AGV"),
        TEXT("IN03_COIL_STORAGE"), TEXT("IN04_DEPACK"),
        TEXT("IN05_COIL_PREP"), TEXT("S01_DESTACK_LOAD"),
        TEXT("S02_DEEP_DRAW"), TEXT("S03_FORM"), TEXT("S04_TRIM"),
        TEXT("S05_PIERCE"), TEXT("S06_FLANGE"), TEXT("S07_INSPECTION"),
        TEXT("S07_PALLETISER"), TEXT("SUPPORT_FLEET")
    };
    for (const FName MachineId : MachineIds)
    {
        ULBStatusBeaconComponent* Beacon =
            Presentation->GetStatusBeacon(MachineId);
        TestNotNull(*FString::Printf(TEXT("%s owns native status beacon"),
            *MachineId.ToString()), Beacon);
        TestTrue(*FString::Printf(TEXT("%s beacon begins off safely"),
            *MachineId.ToString()), Beacon
                && Beacon->GetStatus() == ELBStatusBeaconState::Off);
        TestTrue(*FString::Printf(TEXT("%s beacon has real point lights"),
            *MachineId.ToString()), Beacon && Beacon->GetGreenLight()
                && Beacon->GetAmberLight() && Beacon->GetRedLight());
    }

    const FName TaskIds[] = {
        TEXT("IN04_DEPACK_TASK"), TEXT("S07_INSPECTION_TASK_A"),
        TEXT("S07_INSPECTION_TASK_B"), TEXT("S07_PALLETISER_TASK")
    };
    for (const FName TaskId : TaskIds)
    {
        URectLightComponent* Light = Presentation->GetTaskLight(TaskId);
        TestNotNull(*FString::Printf(TEXT("%s uses a native rect light"),
            *TaskId.ToString()), Light);
        TestTrue(*FString::Printf(TEXT("%s starts dark until commissioned"),
            *TaskId.ToString()), Light && Light->Intensity == 0.0f);
    }

    World->DestroyWorld(false);
    return true;
}

bool FLBPressShopOverheadStateMappingTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    TestEqual(TEXT("uncommissioned is dark"),
        ALBPressShopOverheadPresentationActor::ResolveBeaconState(
            false, false, false, false, false, false, false),
        ELBStatusBeaconState::Off);
    TestEqual(TEXT("commissioned idle machine is green ready"),
        ALBPressShopOverheadPresentationActor::ResolveBeaconState(
            true, false, false, false, false, false, false),
        ELBStatusBeaconState::Ready);
    TestEqual(TEXT("active processing is green running"),
        ALBPressShopOverheadPresentationActor::ResolveBeaconState(
            true, false, false, false, true, false, false),
        ELBStatusBeaconState::Running);
    TestEqual(TEXT("moving presentation uses flashing amber"),
        ALBPressShopOverheadPresentationActor::ResolveBeaconState(
            true, false, false, false, true, true, false),
        ELBStatusBeaconState::Moving);
    TestEqual(TEXT("quality hold is amber waiting"),
        ALBPressShopOverheadPresentationActor::ResolveBeaconState(
            true, false, false, false, true, false, true),
        ELBStatusBeaconState::Waiting);
    TestEqual(TEXT("pause is red stopped"),
        ALBPressShopOverheadPresentationActor::ResolveBeaconState(
            true, true, false, false, true, false, false),
        ELBStatusBeaconState::Stopped);
    TestEqual(TEXT("press fault is red fault"),
        ALBPressShopOverheadPresentationActor::ResolveBeaconState(
            true, false, true, false, true, false, false),
        ELBStatusBeaconState::Fault);

    FName Machine;
    ELBPressShopOverheadPressFrame Frame;
    float LocalProgress = 0.0f;
    bool bTransfer = false;
    ALBPressShopOverheadPresentationActor::ComputePressVisualState(
        0.01f, Machine, Frame, LocalProgress, bTransfer);
    TestEqual(TEXT("press cycle begins at S02"), Machine,
        FName(TEXT("S02_DEEP_DRAW")));
    TestEqual(TEXT("press cycle begins open"), Frame,
        ELBPressShopOverheadPressFrame::Open);

    ALBPressShopOverheadPresentationActor::ComputePressVisualState(
        0.30f, Machine, Frame, LocalProgress, bTransfer);
    TestEqual(TEXT("second fifth drives S03"), Machine,
        FName(TEXT("S03_FORM")));
    TestEqual(TEXT("mid-downstroke uses descending frame"), Frame,
        ELBPressShopOverheadPressFrame::Descending);

    ALBPressShopOverheadPresentationActor::ComputePressVisualState(
        0.71f, Machine, Frame, LocalProgress, bTransfer);
    TestEqual(TEXT("fourth fifth drives S05"), Machine,
        FName(TEXT("S05_PIERCE")));
    TestEqual(TEXT("contact interval is explicit"), Frame,
        ELBPressShopOverheadPressFrame::Contact);

    ALBPressShopOverheadPresentationActor::ComputePressVisualState(
        0.99f, Machine, Frame, LocalProgress, bTransfer);
    TestEqual(TEXT("final fifth drives S06"), Machine,
        FName(TEXT("S06_FLANGE")));
    TestTrue(TEXT("tail of each press step exposes transfer state"), bTransfer);
    TestEqual(TEXT("transfer returns to open silhouette"), Frame,
        ELBPressShopOverheadPressFrame::Open);

    FName DepackPose;
    float DepackProgress = 0.0f;
    ALBPressShopOverheadPresentationActor::ComputeDepackVisualState(
        0.10f, DepackPose, DepackProgress);
    TestEqual(TEXT("depack begins on drive rollers"), DepackPose,
        FName(TEXT("ROLLERS")));
    TestTrue(TEXT("roller subphase has local progress"),
        FMath::IsNearlyEqual(DepackProgress, 0.40f));
    ALBPressShopOverheadPresentationActor::ComputeDepackVisualState(
        0.45f, DepackPose, DepackProgress);
    TestEqual(TEXT("depack middle removes wrap"), DepackPose,
        FName(TEXT("WRAP_REMOVE")));
    TestTrue(TEXT("wrap-removal subphase has local progress"),
        FMath::IsNearlyEqual(DepackProgress, 0.50f, KINDA_SMALL_NUMBER));
    ALBPressShopOverheadPresentationActor::ComputeDepackVisualState(
        0.825f, DepackPose, DepackProgress);
    TestEqual(TEXT("depack finishes with vision inspection"), DepackPose,
        FName(TEXT("VISION_INSPECT")));
    TestTrue(TEXT("vision subphase has local progress"),
        FMath::IsNearlyEqual(DepackProgress, 0.50f, KINDA_SMALL_NUMBER));
    return true;
}

bool FLBPressShopOverheadVisualLayerContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_PressShop_Overhead_VisualLayer"));
    ALBPressShopOverheadVisualLayerActor* Layer = World
        ? World->SpawnActor<ALBPressShopOverheadVisualLayerActor>() : nullptr;
    if (!TestNotNull(TEXT("visual layer actor spawns"), Layer))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    TestTrue(TEXT("visual layer has stable packaged-runtime tag"),
        Layer->ActorHasTag(
            ALBPressShopOverheadVisualLayerActor::GetLayerTag()));
    TestFalse(TEXT("visual layer has no actor collision"),
        Layer->GetActorEnableCollision());
    TestEqual(TEXT("visual layer mesh has no collision"),
        Layer->GetStaticMeshComponent()->GetCollisionEnabled(),
        ECollisionEnabled::NoCollision);
    TestFalse(TEXT("visual layer cannot cast a flat card shadow"),
        Layer->GetStaticMeshComponent()->CastShadow);

    UStaticMeshComponent* LayerMesh = Layer->GetStaticMeshComponent();
    UStaticMesh* UnitPlane = LoadObject<UStaticMesh>(nullptr,
        TEXT("/Engine/BasicShapes/Plane.Plane"));
    UMaterialInstanceDynamic* SpriteMaterial =
        UMaterialInstanceDynamic::Create(
            UMaterial::GetDefaultMaterial(MD_Surface), Layer);
    if (!TestNotNull(TEXT("engine unit plane is available"), UnitPlane)
        || !TestNotNull(TEXT("test sprite material instance is available"),
            SpriteMaterial))
    {
        World->DestroyWorld(false);
        return false;
    }

    // Model a loaded layer: its UObject references exist before registration.
    // The native hook must retain that exact MI and schedule a proxy rebuild on
    // both initial registration and later component re-registration.
    Layer->UnregisterAllComponents();
    LayerMesh->SetStaticMesh(UnitPlane);
    LayerMesh->SetMaterial(0, SpriteMaterial);
    int32 MaterialProxyRefreshCount = 0;
    const FDelegateHandle RenderDirtyHandle =
        UActorComponent::MarkRenderStateDirtyEvent.AddLambda(
            [LayerMesh, &MaterialProxyRefreshCount](UActorComponent& Component)
            {
                if (&Component == LayerMesh)
                {
                    ++MaterialProxyRefreshCount;
                }
            });

    Layer->RegisterAllComponents();
    TestTrue(TEXT("slot zero retains its exact MI after registration"),
        LayerMesh->GetMaterial(0) == SpriteMaterial);
    TestTrue(TEXT("slot zero remains an explicit component override"),
        LayerMesh->GetNumOverrideMaterials() > 0);
    if (FApp::CanEverRender())
    {
        TestTrue(TEXT("registered sprite schedules a scene-proxy refresh"),
            LayerMesh->IsRenderStateDirty());
        TestEqual(TEXT("initial registration requests one material refresh"),
            MaterialProxyRefreshCount, 1);
    }

    World->SendAllEndOfFrameUpdates();
    Layer->ReregisterAllComponents();
    TestTrue(TEXT("slot zero retains its exact MI after re-registration"),
        LayerMesh->GetMaterial(0) == SpriteMaterial);
    TestTrue(TEXT("re-registration retains the explicit override"),
        LayerMesh->GetNumOverrideMaterials() > 0);
    if (FApp::CanEverRender())
    {
        TestTrue(TEXT("re-registered sprite schedules a scene-proxy refresh"),
            LayerMesh->IsRenderStateDirty());
        TestEqual(TEXT("re-registration requests another material refresh"),
            MaterialProxyRefreshCount, 2);
    }
    UActorComponent::MarkRenderStateDirtyEvent.Remove(RenderDirtyHandle);

    Layer->bHasMotionRange = true;
    Layer->MotionStart = FTransform(FVector(100.0, 200.0, 10.0));
    Layer->MotionEnd = FTransform(FVector(500.0, 600.0, 10.0));
    Layer->ApplyPresentationState(true, 0.5f);
    TestTrue(TEXT("motion range interpolates deterministically"),
        Layer->GetActorLocation().Equals(FVector(300.0, 400.0, 10.0), 0.01));
    TestFalse(TEXT("visible layer is not hidden"), Layer->IsHidden());
    Layer->ApplyPresentationState(false, 0.5f);
    TestTrue(TEXT("disabled layer hides without changing collision"),
        Layer->IsHidden() && !Layer->GetActorEnableCollision());

    Layer->SequenceFrameIndex = 3;
    Layer->SequenceFrameCount = 8;
    Layer->bSequenceLoops = false;
    TestTrue(TEXT("one-shot sequence selects its exact frame"),
        Layer->IsSequenceFrameVisible(0.45f));
    TestFalse(TEXT("one-shot sequence hides non-current frame"),
        Layer->IsSequenceFrameVisible(0.10f));
    TestFalse(TEXT("one-shot sequence clamps to the final frame"),
        Layer->IsSequenceFrameVisible(1.0f));
    Layer->SequenceFrameIndex = 7;
    TestTrue(TEXT("one-shot final progress selects the final frame"),
        Layer->IsSequenceFrameVisible(1.0f));
    Layer->SequenceFrameIndex = 3;
    Layer->bSequenceLoops = true;
    TestTrue(TEXT("looping sequence repeats deterministically"),
        Layer->IsSequenceFrameVisible(1.45f));
    Layer->SequenceFrameIndex = 8;
    TestFalse(TEXT("invalid sequence metadata fails closed"),
        Layer->IsSequenceFrameVisible(0.95f));

    World->DestroyWorld(false);
    return true;
}

bool FLBPressShopOverheadCoilFeedMotionContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    float CartTravel = -1.0f;
    float PayoffProgress = -1.0f;
    bool bCartMoving = true;
    bool bPayoffActive = true;

    ALBPressShopOverheadPresentationActor::ComputeCoilFeedVisualState(
        0.0f, CartTravel, PayoffProgress, bCartMoving, bPayoffActive);
    TestTrue(TEXT("S01 cycle begins at the authored cart start"),
        FMath::IsNearlyZero(CartTravel));
    TestFalse(TEXT("station cursor zero does not claim cart motion"),
        bCartMoving);
    TestFalse(TEXT("payoff is interlocked until cart transfer completes"),
        bPayoffActive);
    TestTrue(TEXT("payoff progress remains zero before its interlock"),
        FMath::IsNearlyZero(PayoffProgress));

    ALBPressShopOverheadPresentationActor::ComputeCoilFeedVisualState(
        0.18f, CartTravel, PayoffProgress, bCartMoving, bPayoffActive);
    TestTrue(TEXT("half transfer reaches half the eased 3.2m range"),
        FMath::IsNearlyEqual(CartTravel, 0.5f, KINDA_SMALL_NUMBER));
    TestTrue(TEXT("cart is moving during its authored transfer"),
        bCartMoving);
    TestFalse(TEXT("payoff remains stopped while cart moves"),
        bPayoffActive);

    ALBPressShopOverheadPresentationActor::ComputeCoilFeedVisualState(
        0.36f, CartTravel, PayoffProgress, bCartMoving, bPayoffActive);
    TestTrue(TEXT("phase boundary seats cart at exact authored endpoint"),
        FMath::IsNearlyEqual(CartTravel, 1.0f));
    TestFalse(TEXT("seated cart is no longer moving"), bCartMoving);
    TestTrue(TEXT("seated cart releases payoff interlock"), bPayoffActive);
    TestTrue(TEXT("payoff begins at frame progress zero"),
        FMath::IsNearlyZero(PayoffProgress));

    ALBPressShopOverheadPresentationActor::ComputeCoilFeedVisualState(
        0.68f, CartTravel, PayoffProgress, bCartMoving, bPayoffActive);
    TestTrue(TEXT("mid-payoff keeps cart seated"),
        FMath::IsNearlyEqual(CartTravel, 1.0f));
    TestTrue(TEXT("mid-payoff selects the middle of non-looping frames"),
        FMath::IsNearlyEqual(PayoffProgress, 0.5f,
            KINDA_SMALL_NUMBER));

    ALBPressShopOverheadPresentationActor::ComputeCoilFeedVisualState(
        1.0f, CartTravel, PayoffProgress, bCartMoving, bPayoffActive);
    TestTrue(TEXT("completed station retains exact cart endpoint"),
        FMath::IsNearlyEqual(CartTravel, 1.0f));
    TestTrue(TEXT("completed station reaches final feed frame"),
        FMath::IsNearlyEqual(PayoffProgress, 1.0f));

    const FTransform Placed(FRotator(0.0f, 23.0f, 0.0f),
        FVector(1200.0f, -340.0f, 17.0f), FVector(1.4f, 0.8f, 1.0f));
    FTransform Start;
    FTransform End;
    TestTrue(TEXT("approved coil-transfer channel resolves a native range"),
        ALBPressShopOverheadPresentationActor::BuildAuthoredMotionRange(
            TEXT("CoilTransferToDecoiler"), Placed, Start, End));
    TestTrue(TEXT("native range preserves the exact placed anchor"),
        Start.Equals(Placed, 0.001f));
    TestTrue(TEXT("native range uses documented +X 3.2m endpoint"),
        End.GetLocation().Equals(
            Placed.GetLocation() + FVector(320.0f, 0.0f, 0.0f), 0.001f));
    TestTrue(TEXT("native range preserves authored rotation and scale"),
        End.GetRotation().Equals(Placed.GetRotation(), 0.0001f)
        && End.GetScale3D().Equals(Placed.GetScale3D(), 0.0001f));

    FTransform RejectedStart = FTransform::Identity;
    FTransform RejectedEnd = FTransform::Identity;
    TestFalse(TEXT("unknown channels cannot invent transform endpoints"),
        ALBPressShopOverheadPresentationActor::BuildAuthoredMotionRange(
            TEXT("UNAUTHORISED_RANGE"), Placed,
            RejectedStart, RejectedEnd));

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_PressShop_Overhead_CoilFeedMotion"));
    ALBPressShopOverheadPresentationActor* Presentation = World
        ? World->SpawnActor<ALBPressShopOverheadPresentationActor>() : nullptr;
    ALBPressShopOverheadVisualLayerActor* CartLayer = World
        ? World->SpawnActor<ALBPressShopOverheadVisualLayerActor>() : nullptr;
    if (TestNotNull(TEXT("motion integration presentation spawns"),
            Presentation)
        && TestNotNull(TEXT("motion integration cart layer spawns"),
            CartLayer))
    {
        const FTransform WorldAnchor(FRotator::ZeroRotator,
            FVector(-3779.0f, 280.0f, 4.0f));
        CartLayer->SetActorTransform(WorldAnchor);
        CartLayer->MachineId = TEXT("S01_DESTACK_LOAD");
        CartLayer->MotionChannel = TEXT("CoilTransferToDecoiler");
        TestFalse(TEXT("spawn registry retains a placed anchor, not endpoints"),
            CartLayer->bHasMotionRange);

        // The first native binding refresh is the complete integration seam:
        // it derives runtime-only endpoints and then safely waits for the
        // canonical OneFactory backbone in this isolated test world.
        Presentation->Tick(0.0f);
        TestTrue(TEXT("native binding installs the approved cart range"),
            CartLayer->bHasMotionRange);
        TestTrue(TEXT("binding keeps the exact placed start anchor"),
            CartLayer->MotionStart.Equals(WorldAnchor, 0.001f));
        TestTrue(TEXT("binding installs the exact +X 320cm endpoint"),
            CartLayer->MotionEnd.GetLocation().Equals(
                WorldAnchor.GetLocation() + FVector(320.0f, 0.0f, 0.0f),
                0.001f));
    }
    if (World) World->DestroyWorld(false);
    return true;
}

#endif
