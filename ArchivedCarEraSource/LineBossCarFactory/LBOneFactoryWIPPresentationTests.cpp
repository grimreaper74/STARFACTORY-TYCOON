#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryWIPPresentationActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/World.h"
#include "LBPressShopOverheadPresentationActor.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryWIPStageReadabilityTest,
    "LineBoss.OneFactory.Presentation.WIPStagesRemainVisuallyDistinct",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryWIPStageReadabilityTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const ELBOneFactoryWIPVisual Body =
        ALBOneFactoryWIPPresentationActor::VisualForStage(
            ELBOneFactoryVehicleStage::BodyInWhite);
    const ELBOneFactoryWIPVisual PressInspection =
        ALBOneFactoryWIPPresentationActor::VisualForStage(
            ELBOneFactoryVehicleStage::PressPanelInspection);
    const ELBOneFactoryWIPVisual ECoat =
        ALBOneFactoryWIPPresentationActor::VisualForStage(
            ELBOneFactoryVehicleStage::EDCoat);
    const ELBOneFactoryWIPVisual Paint =
        ALBOneFactoryWIPPresentationActor::VisualForStage(
            ELBOneFactoryVehicleStage::ColourCoat);
    const ELBOneFactoryWIPVisual Finished =
        ALBOneFactoryWIPPresentationActor::VisualForStage(
            ELBOneFactoryVehicleStage::GeneralAssemblyTrim);

    TestEqual(TEXT("body-in-white uses the open-body visual family"), Body,
        ELBOneFactoryWIPVisual::BodyInWhite);
    TestEqual(TEXT("Press inspection keeps the stamped-panel visual family"),
        PressInspection, ELBOneFactoryWIPVisual::PanelStack);
    TestEqual(TEXT("e-coat uses the primed visual family"), ECoat,
        ELBOneFactoryWIPVisual::PrimedBody);
    TestEqual(TEXT("colour coat uses the painted visual family"), Paint,
        ELBOneFactoryWIPVisual::PaintedBody);
    TestEqual(TEXT("final assembly uses the finished-car family"), Finished,
        ELBOneFactoryWIPVisual::FinishedCar);
    TestTrue(TEXT("body, e-coat, paint and final assembly must remain distinct"),
        Body != ECoat && ECoat != Paint && Paint != Finished);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryStampedPanelWIPPresentationTest,
    "LineBoss.OneFactory.Presentation.StampedPanelRackUsesValidatedElevenPanelModules",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryOverheadWIPFallbackTest,
    "LineBoss.OneFactory.Presentation.DisabledOverheadRestoresGenericPressWIP",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryStampedPanelWIPPresentationTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    TestTrue(TEXT("Cairnwell has an explicit WIP presentation authority"),
        ALBOneFactoryWIPPresentationActor::SupportsVehicleModel(TEXT("CAIRNWELL_2040")));
    TestFalse(TEXT("an unregistered development model is never shown using Cairnwell WIP"),
        ALBOneFactoryWIPPresentationActor::SupportsVehicleModel(TEXT("UNREGISTERED_DEVELOPMENT_MODEL")));

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBStampedPanelPresentationTestWorld"));
    if (!TestNotNull(TEXT("presentation test world created"), World)) return false;

    ALBOneFactoryWIPPresentationActor* Presentation =
        World->SpawnActor<ALBOneFactoryWIPPresentationActor>();
    if (!TestNotNull(TEXT("WIP presentation actor spawned"), Presentation))
    {
        World->DestroyWorld(false);
        return false;
    }

    TInlineComponentArray<UInstancedStaticMeshComponent*> Components(Presentation);
    int32 PanelCount = 0;
    for (UInstancedStaticMeshComponent* Component : Components)
    {
        if (!Component || !Component->GetName().StartsWith(TEXT("WIP_Stamped_")))
        {
            continue;
        }
        ++PanelCount;
        TestNotNull(*FString::Printf(TEXT("native panel archetype %s is hard-referenced"),
            *Component->GetName()), Component->GetStaticMesh().Get());
        TestTrue(*FString::Printf(TEXT("panel batch %s uses the clean-room native panel authority"),
            *Component->GetName()), Component->GetStaticMesh()
                && Component->GetStaticMesh()->GetPathName().Contains(
                    TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/")));
        TestEqual(*FString::Printf(TEXT("panel batch %s has no collision"),
            *Component->GetName()), Component->GetCollisionEnabled(),
            ECollisionEnabled::NoCollision);
        TestFalse(*FString::Printf(TEXT("panel batch %s cannot affect navigation"),
            *Component->GetName()), Component->CanEverAffectNavigation());
    }
    TestEqual(TEXT("exact 11 validated panel batches are present"), PanelCount, 11);

    World->DestroyWorld(false);
    return true;
}

bool FLBOneFactoryOverheadWIPFallbackTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryOverheadWIPFallbackTest"));
    ALBPressShopOverheadPresentationActor* Overhead = World
        ? World->SpawnActor<ALBPressShopOverheadPresentationActor>() : nullptr;
    if (!TestNotNull(TEXT("overhead presentation actor spawns"), Overhead))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("enabled visible overhead presentation owns Press WIP"),
        ALBOneFactoryWIPPresentationActor::
            IsOverheadPressPresentationAuthoritative(Overhead));
    Overhead->SetPresentationEnabled(false);
    TestFalse(TEXT("disabled overhead presentation restores generic Press WIP"),
        ALBOneFactoryWIPPresentationActor::
            IsOverheadPressPresentationAuthoritative(Overhead));
    Overhead->SetPresentationEnabled(true);
    Overhead->SetActorHiddenInGame(true);
    TestFalse(TEXT("hidden overhead presentation restores generic Press WIP"),
        ALBOneFactoryWIPPresentationActor::
            IsOverheadPressPresentationAuthoritative(Overhead));

    World->DestroyWorld(false);
    return true;
}

#endif
