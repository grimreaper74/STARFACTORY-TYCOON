#if WITH_DEV_AUTOMATION_TESTS

#include "LBPaintShopPrototypeWorldBootstrap.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBPaintShopBuildAuthority.h"
#include "LBPaintShopCellActor.h"
#include "LBPaintShopPrototypeRuntime.h"
#include "Misc/AutomationTest.h"

namespace LBPaintShopPrototypeWorldBootstrapTests
{
    template<typename ActorType>
    int32 CountLiveActors(UWorld* World)
    {
        int32 Count = 0;
        if (!World) return Count;
        for (TActorIterator<ActorType> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++Count;
        }
        return Count;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopBootstrapPreconditionTest,
    "LineBoss.PaintShop.Experimental.WorldBootstrap.SpawnPreconditions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopBootstrapPreconditionTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    FString Reason;
    TestTrue(TEXT("An empty Paint authority world is accepted"),
        ALBPaintShopPrototypeWorldBootstrap::ValidateSpawnPreconditions(0, 0, Reason));
    TestTrue(TEXT("Accepted preconditions have no failure reason"), Reason.IsEmpty());
    TestFalse(TEXT("A pre-existing Paint build authority fails closed"),
        ALBPaintShopPrototypeWorldBootstrap::ValidateSpawnPreconditions(1, 0, Reason));
    TestFalse(TEXT("A pre-existing Paint runtime fails closed"),
        ALBPaintShopPrototypeWorldBootstrap::ValidateSpawnPreconditions(0, 1, Reason));
    TestFalse(TEXT("A complete pre-existing Paint pair still fails closed"),
        ALBPaintShopPrototypeWorldBootstrap::ValidateSpawnPreconditions(1, 1, Reason));
    TestFalse(TEXT("Malformed negative authority counts fail closed"),
        ALBPaintShopPrototypeWorldBootstrap::ValidateSpawnPreconditions(-1, 0, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopBootstrapInitializationTest,
    "LineBoss.PaintShop.Experimental.WorldBootstrap.InitializeExactlyOnePair",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopBootstrapInitializationTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPaintShopBootstrapInitializationTest"));
    ALBPaintShopPrototypeWorldBootstrap* Bootstrap = World
        ? World->SpawnActor<ALBPaintShopPrototypeWorldBootstrap>() : nullptr;
    if (!TestNotNull(TEXT("Paint prototype bootstrap spawns"), Bootstrap))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestFalse(TEXT("Paint bootstrap never ticks"),
        Bootstrap->PrimaryActorTick.bCanEverTick);
    FString Reason;
    TestTrue(TEXT("Bootstrap creates and initializes the isolated Paint pair"),
        Bootstrap->InitializePrototypeWorld(Reason));
    TestTrue(TEXT("Successful bootstrap reports Ready"), Bootstrap->IsReady());
    TestEqual(TEXT("Successful bootstrap state is exact"), Bootstrap->GetBootstrapState(),
        ELBPaintShopPrototypeBootstrapState::Ready);
    TestTrue(TEXT("Successful bootstrap exposes a status reason"),
        !Bootstrap->GetBootstrapReason().IsEmpty());

    ALBPaintShopBuildAuthority* Authority = Bootstrap->GetBuildAuthority();
    ALBPaintShopPrototypeRuntime* Runtime = Bootstrap->GetRuntime();
    TestNotNull(TEXT("Bootstrap owns one Paint build authority"), Authority);
    TestNotNull(TEXT("Bootstrap owns one Paint prototype runtime"), Runtime);
    TestTrue(TEXT("Both Paint authorities are owned by the bootstrap"),
        Authority && Runtime && Authority->GetOwner() == Bootstrap
        && Runtime->GetOwner() == Bootstrap);
    TestEqual(TEXT("World contains exactly one Paint build authority"),
        LBPaintShopPrototypeWorldBootstrapTests::CountLiveActors<
            ALBPaintShopBuildAuthority>(World), 1);
    TestEqual(TEXT("World contains exactly one Paint runtime"),
        LBPaintShopPrototypeWorldBootstrapTests::CountLiveActors<
            ALBPaintShopPrototypeRuntime>(World), 1);

    const FLBPaintShopApprovedEDCoatLayoutItem Approved =
        ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
    ALBPaintShopCellActor* Cell = Authority ? Authority->FindCell(Approved.CellId) : nullptr;
    TestNotNull(TEXT("Bootstrap builds exactly the approved ED-coat cell"), Cell);
    FString PlacementReason;
    TestTrue(TEXT("Bootstrap cell retains the canonical definition and placement"),
        Authority && Cell && Cell->GetCellId() == Approved.CellId
        && Cell->GetDefinitionId() == Approved.DefinitionId
        && Authority->ValidateApprovedCellPlacement(
            Cell->GetDefinitionId(), Cell->GetActorTransform(), PlacementReason));
    TestTrue(TEXT("Runtime is bound to the bootstrap-owned build authority"),
        Runtime && Runtime->IsInitialized() && Runtime->GetBuildAuthority() == Authority);
    TestTrue(TEXT("Runtime resolves the same bootstrap-owned ED-coat cell"),
        Runtime && Cell && Runtime->GetEDCoatCell() == Cell
        && Cell->GetOwner() == Authority);
    TestTrue(TEXT("Fresh isolated runtime is safely starved without synthesized WIP"),
        Runtime && Runtime->IsStarved() && !Runtime->HasActiveWIP());

    TestTrue(TEXT("Repeated bootstrap initialization is idempotent"),
        Bootstrap->InitializePrototypeWorld(Reason));
    TestTrue(TEXT("Idempotent initialization preserves the exact authority pointers"),
        Bootstrap->GetBuildAuthority() == Authority && Bootstrap->GetRuntime() == Runtime);
    TestEqual(TEXT("Idempotent initialization does not duplicate build authority"),
        LBPaintShopPrototypeWorldBootstrapTests::CountLiveActors<
            ALBPaintShopBuildAuthority>(World), 1);
    TestEqual(TEXT("Idempotent initialization does not duplicate runtime"),
        LBPaintShopPrototypeWorldBootstrapTests::CountLiveActors<
            ALBPaintShopPrototypeRuntime>(World), 1);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopBootstrapExistingAuthorityFailureTest,
    "LineBoss.PaintShop.Experimental.WorldBootstrap.PreExistingPaintAuthorityFailsClosed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopBootstrapExistingAuthorityFailureTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPaintShopBootstrapExistingAuthorityFailureTest"));
    ALBPaintShopBuildAuthority* ExternalAuthority = World
        ? World->SpawnActor<ALBPaintShopBuildAuthority>() : nullptr;
    ALBPaintShopPrototypeWorldBootstrap* Bootstrap = World
        ? World->SpawnActor<ALBPaintShopPrototypeWorldBootstrap>() : nullptr;
    if (!World || !ExternalAuthority || !Bootstrap)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    TestFalse(TEXT("Bootstrap refuses a world with a pre-existing Paint authority"),
        Bootstrap->InitializePrototypeWorld(Reason));
    TestTrue(TEXT("Rejected bootstrap records a terminal failure"),
        Bootstrap->HasFailed()
        && Bootstrap->GetBootstrapState() == ELBPaintShopPrototypeBootstrapState::Failed);
    TestTrue(TEXT("Rejected bootstrap exposes its exact failure reason"),
        !Reason.IsEmpty() && Bootstrap->GetBootstrapReason() == Reason);
    TestTrue(TEXT("Failure publishes no partially owned authority pointers"),
        Bootstrap->GetBuildAuthority() == nullptr && Bootstrap->GetRuntime() == nullptr);
    TestTrue(TEXT("Failure leaves the unrelated pre-existing Paint authority untouched"),
        IsValid(ExternalAuthority) && !ExternalAuthority->IsActorBeingDestroyed());
    TestEqual(TEXT("Failure creates no additional Paint build authority"),
        LBPaintShopPrototypeWorldBootstrapTests::CountLiveActors<
            ALBPaintShopBuildAuthority>(World), 1);
    TestEqual(TEXT("Failure creates no Paint runtime"),
        LBPaintShopPrototypeWorldBootstrapTests::CountLiveActors<
            ALBPaintShopPrototypeRuntime>(World), 0);

    TestFalse(TEXT("Repeated failed initialization remains fail-closed"),
        Bootstrap->InitializePrototypeWorld(Reason));
    TestEqual(TEXT("Repeated failure still creates no Paint runtime"),
        LBPaintShopPrototypeWorldBootstrapTests::CountLiveActors<
            ALBPaintShopPrototypeRuntime>(World), 0);

    World->DestroyWorld(false);
    return true;
}

#endif
