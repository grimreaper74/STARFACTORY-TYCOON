#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryScanBeamActor.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryScanBeamRuntimeTest,
    "LineBoss.OneFactory.Presentation.InspectionScannerOwnsBeamAndSweeps",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryScanBeamRuntimeTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryScanBeamTestWorld"));
    if (!TestNotNull(TEXT("scanner test world created"), World)) return false;

    ALBOneFactoryScanBeamActor* Scanner = World->SpawnActor<ALBOneFactoryScanBeamActor>();
    if (!TestNotNull(TEXT("scanner actor spawned"), Scanner))
    {
        World->DestroyWorld(false);
        return false;
    }

    UStaticMeshComponent* Beam = Scanner->GetBeamComponent();
    UPointLightComponent* ScanLight = Scanner->GetScanLightComponent();
    TestNotNull(TEXT("scanner has a beam component"), Beam);
    TestNotNull(TEXT("scanner has a travelling scan glow"), ScanLight);
    TestTrue(TEXT("scan glow is cyan inspection light"), ScanLight
        && ScanLight->GetLightColor().G > ScanLight->GetLightColor().R);
    TestFalse(TEXT("scan glow does not cast distracting shadows"), ScanLight
        && ScanLight->CastShadows);
    TestTrue(TEXT("scanner owns the authored scan-beam asset"), Beam && Beam->GetStaticMesh()
        && Beam->GetStaticMesh()->GetPathName().Contains(
            TEXT("/Game/LineBoss/ScanKit_v001/Meshes/SM_LB_Inspect_ScanBeam_v001")));
    TestEqual(TEXT("scanner beam has no collision"), Beam ? Beam->GetCollisionEnabled()
        : ECollisionEnabled::QueryAndPhysics, ECollisionEnabled::NoCollision);
    TestFalse(TEXT("scanner beam cannot affect navigation"), Beam && Beam->CanEverAffectNavigation());

    Scanner->Tick(Scanner->SecondsPerPass);
    TestTrue(TEXT("scanner reaches the positive sweep end"), Beam
        && FMath::IsNearlyEqual(Beam->GetRelativeLocation().X, Scanner->SweepHalfRangeCm, 0.1f));
    Scanner->Tick(Scanner->DwellSeconds * 0.5f);
    TestTrue(TEXT("scanner dwells at the positive sweep end"), Beam
        && FMath::IsNearlyEqual(Beam->GetRelativeLocation().X, Scanner->SweepHalfRangeCm, 0.1f));
    // Finish the remaining half dwell, then advance halfway through the return pass.
    Scanner->Tick(Scanner->DwellSeconds * 0.5f + Scanner->SecondsPerPass * 0.5f);
    TestTrue(TEXT("scanner returns smoothly from the positive end"), Beam
        && FMath::IsNearlyEqual(Beam->GetRelativeLocation().X, 0.0f, 0.1f));

    World->DestroyWorld(false);
    return true;
}

#endif
