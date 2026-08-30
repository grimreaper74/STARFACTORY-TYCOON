#include "LBOneFactoryPressFeedController.h"

#include "Engine/World.h"
#include "LBPR008Station.h"
#include "LBPR009Station.h"
#include "LBPR010Station.h"

#if WITH_DEV_AUTOMATION_TESTS
#include "EngineUtils.h"
#include "Misc/AutomationTest.h"
#endif

namespace LBOneFactoryPressFeedPrivate
{
    const FName CommandSource(TEXT("LB.ONEFACTORY.PRESSFEED"));
    const FName Authority(TEXT("CW.MW.CONTROL_ROOM"));
}

ALBOneFactoryPressFeedController::ALBOneFactoryPressFeedController()
{
    PrimaryActorTick.bCanEverTick = true;
    SetActorEnableCollision(false);
    Tags.AddUnique(GetFeedTag());
    Tags.AddUnique(TEXT("LB.Provenance.NativeCode"));
}

bool ALBOneFactoryPressFeedController::ConfigureAutomaticRoute(FString& OutReason)
{
    OutReason.Reset();
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("PRESS FEED ROUTE REQUIRES A WORLD");
        return false;
    }
    FActorSpawnParameters Params;
    Params.Owner = this;
    Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    PR008 = World->SpawnActor<ALBPR008Station>(ALBPR008Station::StaticClass(),
        GetActorTransform(), Params);
    PR009 = World->SpawnActor<ALBPR009Station>(ALBPR009Station::StaticClass(),
        GetActorTransform(), Params);
    PR010 = World->SpawnActor<ALBPR010Station>(ALBPR010Station::StaticClass(),
        GetActorTransform(), Params);
    if (!PR008 || !PR009 || !PR010)
    {
        OutReason = TEXT("PRESS FEED ROUTE COULD NOT CREATE ALL THREE MACHINE AUTHORITIES");
        return false;
    }

    PR008->SetGuardsClosed(true); PR008->SetStripAvailable(true);
    PR008->SetStripLoopPercent(50.0f); PR008->SetEdgeTrackingDeviation(0.0f);
    PR008->SetFeedPositionError(0.0f); PR008->SetFeedServoHealthy(true);
    PR008->SetPrePunchToolHealthy(true); PR008->SetPressShearLoad(45.0f);
    PR008->SetHydraulicPressure(215.0f); PR008->SetSlugChuteFill(0.0f);
    PR008->SetScrapBinFill(0.0f); PR008->SetBlankOutfeedClear(true);
    PR008->SetSafetyCircuitHealthy(true); PR008->SetEmergencyStopActive(false);
    PR008->SetBlankRecipe(1450.0f, 6.0f); PR008->SetMeasuredCutLength(1450.0f);
    PR009->ConfigureHealthyInputs(false); PR009->SetStackRecipe(5, 5, 1.2f);
    PR010->ConfigureHealthyInputs();

    const bool bStarted =
        PR008->ExecuteRemoteCommand(ELBPR008Command::PowerOn,
            LBOneFactoryPressFeedPrivate::CommandSource, LBOneFactoryPressFeedPrivate::Authority)
        && PR008->ExecuteRemoteCommand(ELBPR008Command::Start,
            LBOneFactoryPressFeedPrivate::CommandSource, LBOneFactoryPressFeedPrivate::Authority)
        && PR009->ExecuteRemoteCommand(ELBPR009Command::PowerOn,
            LBOneFactoryPressFeedPrivate::CommandSource, LBOneFactoryPressFeedPrivate::Authority)
        && PR009->ExecuteRemoteCommand(ELBPR009Command::Start,
            LBOneFactoryPressFeedPrivate::CommandSource, LBOneFactoryPressFeedPrivate::Authority)
        && PR010->ExecuteRemoteCommand(ELBPR010Command::PowerOn,
            LBOneFactoryPressFeedPrivate::CommandSource, LBOneFactoryPressFeedPrivate::Authority)
        && PR010->ExecuteRemoteCommand(ELBPR010Command::Start,
            LBOneFactoryPressFeedPrivate::CommandSource, LBOneFactoryPressFeedPrivate::Authority);
    if (!bStarted)
    {
        OutReason = TEXT("PRESS FEED ROUTE INTERLOCKS REJECTED AUTOMATIC START");
        return false;
    }
    bConfigured = true;
    OutReason = TEXT("PR008→PR009→PR010 NATIVE AUTOMATIC FEED ROUTE ACTIVE");
    return true;
}

void ALBOneFactoryPressFeedController::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bConfigured || !PR008 || !PR009 || !PR010) return;
    TransferBlank();
    TransferStack();
}

bool ALBOneFactoryPressFeedController::TransferBlank()
{
    if (PR008->GetPendingBlankCount() == 0) return false;
    TArray<FText> Reasons;
    if (!PR009->CanAcceptUpstreamBlank(Reasons)) return false;
    const FName Transaction(*FString::Printf(TEXT("PR008-PR009-%d"),
        PR008->GetHMIStatus().BlanksProduced));
    FName BlankId;
    if (!PR008->RequestBlankHandoff(Transaction, BlankId)
        || !PR009->AcceptUpstreamBlank(BlankId))
    {
        PR008->CancelBlankHandoff(Transaction);
        return false;
    }
    return PR008->ConfirmBlankHandoff(Transaction);
}

bool ALBOneFactoryPressFeedController::TransferStack()
{
    TArray<FText> Reasons;
    if (!PR009->CanReleaseCompletedStack(Reasons)
        || !PR010->CanAcceptUpstreamStack(Reasons)) return false;
    const FName Transaction(*FString::Printf(TEXT("PR009-PR010-%d"),
        PR009->GetHMIStatus().CarriersReleased));
    FName StackId;
    TArray<FName> BlankIds;
    if (!PR009->RequestStackHandoff(Transaction, StackId, BlankIds)
        || !PR010->OfferUpstreamStackWithManifest(StackId, BlankIds))
    {
        PR009->CancelStackHandoff(Transaction);
        return false;
    }
    if (!PR009->ConfirmStackHandoff(Transaction)) return false;
    ++DeliveredStackCount;
    return true;
}

FName ALBOneFactoryPressFeedController::GetFeedTag()
{
    return FName(TEXT("LB.OneFactory.PressFeed.Native"));
}

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryPressFeedControllerTest,
    "LineBoss.OneFactory.PressStarter.Feed.NativePR008ToPR010",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPressFeedControllerTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPressFeedControllerTest"));
    ALBOneFactoryPressFeedController* Feed = World
        ? World->SpawnActor<ALBOneFactoryPressFeedController>() : nullptr;
    if (!TestNotNull(TEXT("Native feed controller fixture exists"), Feed))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    FString Reason;
    if (!TestTrue(TEXT("PR008 through PR010 route configures"),
        Feed->ConfigureAutomaticRoute(Reason)))
    {
        World->DestroyWorld(false);
        return false;
    }

    ALBPR008Station* PR008 = nullptr;
    ALBPR009Station* PR009 = nullptr;
    ALBPR010Station* PR010 = nullptr;
    for (TActorIterator<ALBPR008Station> It(World); It; ++It) PR008 = *It;
    for (TActorIterator<ALBPR009Station> It(World); It; ++It) PR009 = *It;
    for (TActorIterator<ALBPR010Station> It(World); It; ++It) PR010 = *It;
    if (!TestNotNull(TEXT("PR008 authority was created"), PR008)
        || !TestNotNull(TEXT("PR009 authority was created"), PR009)
        || !TestNotNull(TEXT("PR010 authority was created"), PR010))
    {
        World->DestroyWorld(false);
        return false;
    }
    for (int32 Index = 0; Index < 80; ++Index)
    {
        PR008->Tick(3.0f);
        Feed->Tick(0.5f);
        PR009->Tick(1.1f);
        Feed->Tick(0.5f);
        PR010->Tick(0.5f);
    }
    TestTrue(TEXT("PR008 has created traceable blanks"),
        PR008->GetHMIStatus().BlanksProduced >= 5);
    TestTrue(TEXT("PR009 has released a traceable stack"),
        PR009->GetHMIStatus().CarriersReleased >= 1);
    TestTrue(TEXT("PR010 has stored the stack in its supermarket"),
        PR010->GetHMIStatus().TotalStacksStored >= 1);
    TestTrue(TEXT("Controller records a committed stack delivery"),
        Feed->GetDeliveredStackCount() >= 1);
    Feed->Destroy();
    World->DestroyWorld(false);
    return true;
}

#endif
