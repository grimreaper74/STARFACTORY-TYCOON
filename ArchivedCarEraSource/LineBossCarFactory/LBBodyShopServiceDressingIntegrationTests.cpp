#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopServiceDressingActor.h"

#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Misc/AutomationTest.h"

namespace LBBodyShopPrototypeGameModePrivate
{
    FName GetServiceDressingActorName();
    ALBBodyShopServiceDressingActor* TrySpawnServiceDressing(
        UWorld* World, AActor* Owner, FString& OutReason);
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopServiceDressingIntegrationTest,
    "LineBoss.BodyShop.Experimental.ServiceDressing.UnconditionalNativeV002SpawnContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopServiceDressingIntegrationTest::RunTest(const FString& Parameters)
{
    (void)Parameters;

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBBodyShopServiceDressingIntegrationTest")));
    if (!TestNotNull(TEXT("Synthetic service-dressing integration world exists"), World))
        return false;

    FActorSpawnParameters OwnerSpawnParameters;
    OwnerSpawnParameters.ObjectFlags |= RF_Transient;
    AActor* Owner = World->SpawnActor<AActor>(AActor::StaticClass(),
        FTransform::Identity, OwnerSpawnParameters);
    if (!TestNotNull(TEXT("Synthetic same-world owner exists"), Owner))
    {
        World->DestroyWorld(false);
        return false;
    }

    FString Reason = TEXT("STALE");
    ALBBodyShopServiceDressingActor* Dressing =
        LBBodyShopPrototypeGameModePrivate::TrySpawnServiceDressing(
            World, Owner, Reason);
    if (TestNotNull(TEXT("The valid same-world owner unconditionally spawns native dressing"),
        Dressing))
    {
        TestTrue(TEXT("A successful dressing spawn has no failure reason"), Reason.IsEmpty());
        TestEqual(TEXT("Native v002 dressing identity is stable and screenshot-addressable"),
            Dressing->GetFName(),
            LBBodyShopPrototypeGameModePrivate::GetServiceDressingActorName());
        TestEqual(TEXT("The GameMode-provided owner remains explicit"),
            Dressing->GetOwner(), Owner);
        TestTrue(TEXT("Dressing placement is the identity-aligned frozen layout"),
            Dressing->GetActorTransform().Equals(FTransform::Identity));
        TestTrue(TEXT("Dressing can never be serialized into the prototype map"),
            Dressing->HasAnyFlags(RF_Transient));
        TestTrue(TEXT("All twelve empty service props are active"),
            Dressing->IsPresentationActive()
                && Dressing->HasValidPresentationContract()
                && Dressing->GetVisibleInstanceCount() == 12);
        TestFalse(TEXT("Service dressing never becomes process WIP"),
            Dressing->RepresentsProcessWIP());
        TestTrue(TEXT("The actor carries the promoted native v002 service tag"),
            Dressing->ActorHasTag(TEXT("LB.BodyShop.ServiceDressing.v002")));
    }

    FString InvalidOwnerReason;
    TestNull(TEXT("Dressing cannot spawn without the explicit GameMode owner"),
        LBBodyShopPrototypeGameModePrivate::TrySpawnServiceDressing(
            World, nullptr, InvalidOwnerReason));
    TestTrue(TEXT("Invalid ownership fails with a diagnostic contract reason"),
        !InvalidOwnerReason.IsEmpty());

    World->DestroyWorld(false);
    return true;
}

#endif
