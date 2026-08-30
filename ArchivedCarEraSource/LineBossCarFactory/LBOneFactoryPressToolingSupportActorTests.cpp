#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryPressToolingSupportActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryPressToolingSupportTest,
    "LineBoss.OneFactory.PressStarter.Tooling.NativeDieStore",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPressToolingSupportTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPressToolingSupportTest"));
    ALBOneFactoryPressStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryPressStarterLayoutAuthority>() : nullptr;
    ALBOneFactoryPressToolingSupportActor* Tooling = World
        ? World->SpawnActor<ALBOneFactoryPressToolingSupportActor>() : nullptr;
    if (!TestNotNull(TEXT("Press layout authority fixture exists"), Authority)
        || !TestNotNull(TEXT("Native tooling fixture exists"), Tooling))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    TestTrue(TEXT("Tooling store materialises from the press layout"),
        Tooling->ConfigureFromPressLayout(Authority->CaptureLayout(), Reason));
    TestTrue(TEXT("Tooling actor exposes its native identity"),
        Tooling->ActorHasTag(ALBOneFactoryPressToolingSupportActor::GetToolingTag()));
    TestTrue(TEXT("Tooling store is configured"), Tooling->IsConfigured());
    TestEqual(TEXT("The store keeps one die set for S02-S06"),
        Tooling->GetStoredDieSetCount(), 5);

    TArray<UInstancedStaticMeshComponent*> Components;
    Tooling->GetComponents<UInstancedStaticMeshComponent>(Components);
    TestEqual(TEXT("Die store includes racks, access, bolster interfaces and staging"),
        Components.Num(), 5);
    for (const UInstancedStaticMeshComponent* Component : Components)
    {
        TestNotNull(TEXT("Every tooling visual component exists"), Component);
        if (!Component) continue;
        TestEqual(TEXT("Tooling is visual-only and cannot block production"),
            Component->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
        TestFalse(TEXT("Tooling visuals do not affect navigation"),
            Component->CanEverAffectNavigation());
        TestTrue(TEXT("Tooling visual has a native cube mesh"),
            Component->GetStaticMesh() != nullptr);
    }

    const UInstancedStaticMeshComponent* const* Bolster = Components.FindByPredicate([](
        const UInstancedStaticMeshComponent* Component)
    {
        return Component && Component->GetFName() == TEXT("PressBolsterInterfaces");
    });
    const UInstancedStaticMeshComponent* const* Staging = Components.FindByPredicate([](
        const UInstancedStaticMeshComponent* Component)
    {
        return Component && Component->GetFName() == TEXT("DieChangeStagingPads");
    });
    TestNotNull(TEXT("S02-S06 have native bolster interfaces"), Bolster ? *Bolster : nullptr);
    TestNotNull(TEXT("S02-S06 have protected die-change staging pads"), Staging ? *Staging : nullptr);
    if (Bolster) TestEqual(TEXT("One bolster interface is present per press"), (*Bolster)->GetInstanceCount(), 5);
    if (Staging) TestEqual(TEXT("One staging pad is present per press"), (*Staging)->GetInstanceCount(), 5);

    Tooling->Destroy();
    Authority->Destroy();
    World->DestroyWorld(false);
    return true;
}

#endif
