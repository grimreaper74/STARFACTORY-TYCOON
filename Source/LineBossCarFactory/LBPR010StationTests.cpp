#include "LBPR010Station.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Components/SceneComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/World.h"
#include "Engine/TextRenderActor.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "LBPressShopSaveGame.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPR010RuntimeAndSaveTest,
    "LineBoss.PressShop.PR010.RuntimeAndSave",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPR010RuntimeAndSaveTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PR010_RuntimeTest"));
    ALBPR010Station* Station = World ? World->SpawnActor<ALBPR010Station>() : nullptr;
    ALBPR010Station* Reloaded = World ? World->SpawnActor<ALBPR010Station>() : nullptr;
    TestNotNull(TEXT("PR-010 station spawns"), Station);
    TestNotNull(TEXT("PR-010 reload target spawns"), Reloaded);
    if (!Station || !Reloaded)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    const FName Authority(TEXT("CW.MW.CONTROL_ROOM"));
    const FName Source(TEXT("MW.MCR.PR010.CONSOLE"));
    Station->ConfigureHealthyInputs();
    TestFalse(TEXT("Untrusted authority cannot power PR-010"),
        Station->ExecuteRemoteCommand(ELBPR010Command::PowerOn, Source, TEXT("UNTRUSTED")));
    TestTrue(TEXT("Control room powers PR-010"),
        Station->ExecuteRemoteCommand(ELBPR010Command::PowerOn, Source, Authority));
    TestTrue(TEXT("Control room starts PR-010"),
        Station->ExecuteRemoteCommand(ELBPR010Command::Start, Source, Authority));

    TInlineComponentArray<USceneComponent*> Components;
    Station->GetComponents(Components);
    TestTrue(TEXT("PR-010 exposes modular motion contracts"), Components.Num() >= 15);
    AActor* ShuttleProbe = World->SpawnActor<AActor>();
    USceneComponent* ProbeRoot = NewObject<USceneComponent>(ShuttleProbe, TEXT("PR010_ShuttleProbe"));
    ProbeRoot->RegisterComponent(); ShuttleProbe->SetRootComponent(ProbeRoot);
    TestTrue(TEXT("PR-010 semantic shuttle binds to native mover"), Station->BindPresentationActor(
        TEXT("PR010_M01_InfeedShuttle"), TEXT("moving_infeed_shuttle"), ShuttleProbe));
    TestEqual(TEXT("Shuttle probe attaches to native shuttle mover"),
        ShuttleProbe->GetRootComponent()->GetAttachParent()->GetFName(), FName(TEXT("PR010_ShuttleMover")));
    ATextRenderActor* StateText = World->SpawnActor<ATextRenderActor>();
    ATextRenderActor* CapacityText = World->SpawnActor<ATextRenderActor>();
    TestTrue(TEXT("PR-010 binds live state HMI text"), Station->BindHMITextActor(TEXT("State"), StateText));
    TestTrue(TEXT("PR-010 binds live capacity HMI text"), Station->BindHMITextActor(TEXT("Capacity"), CapacityText));
    TestFalse(TEXT("PR-010 rejects unsupported HMI fields"), Station->BindHMITextActor(TEXT("WorkingTitle"), CapacityText));
    Station->Tick(0.0f);
    TestEqual(TEXT("Live HMI exposes remote reservation state"), StateText->GetTextRender()->Text.ToString(), FString(TEXT("REMOTE RESERVATION WAIT")));

    auto RunUntilStable = [Station]()
    {
        for (int32 Index = 0; Index < 12; ++Index) Station->Tick(0.5f);
    };
    TestTrue(TEXT("PR-010 accepts identified stack A1"), Station->OfferUpstreamStack(TEXT("PR009-STACK-A1")));
    RunUntilStable();
    TestTrue(TEXT("PR-010 accepts identified stack A2"), Station->OfferUpstreamStack(TEXT("PR009-STACK-A2")));
    RunUntilStable();
    TestTrue(TEXT("PR-010 accepts identified stack B1"), Station->OfferUpstreamStack(TEXT("PR009-STACK-B1")));
    RunUntilStable();
    FLBPR010HMIStatus Status = Station->GetHMIStatus();
    TestEqual(TEXT("Lane A holds its two fixed positions"), Status.LaneStackCounts[0], 2);
    TestEqual(TEXT("Third stack deterministically enters lane B"), Status.LaneStackCounts[1], 1);
    TestEqual(TEXT("Exactly three identified stacks stored"), Status.TotalStacksStored, 3);
    TestEqual(TEXT("Live HMI reports occupied lane capacity"), CapacityText->GetTextRender()->Text.ToString(), FString(TEXT("3 / 8 STACK POSITIONS")));

    TestTrue(TEXT("Train A reserves occupied lane A"), Station->RequestLaneDispatch(0, TEXT("TRAIN-A-REQ-001")));
    RunUntilStable();
    Status = Station->GetHMIStatus();
    TestEqual(TEXT("First lane A stack dispatches autonomously"), Status.LastReleasedStackId, FName(TEXT("PR009-STACK-A1")));
    TestEqual(TEXT("Lane A retains second stack after FIFO dispatch"), Status.LaneStackCounts[0], 1);
    TestEqual(TEXT("Dispatch counter advances"), Status.TotalStacksDispatched, 1);

    TestTrue(TEXT("PR-010 accepts stack for crossing-interlock test"), Station->OfferUpstreamStack(TEXT("PR009-STACK-X")));
    Station->Tick(0.1f);
    Station->Tick(0.5f);
    Station->SetControlledCrossing(false, false);
    TestEqual(TEXT("Opening crossing during motion faults PR-010"), Station->GetHMIStatus().ActiveFault, ELBPR010Fault::ControlledCrossingInterlock);
    Station->SetControlledCrossing(true, true);
    TestTrue(TEXT("Crossing fault acknowledges"), Station->AcknowledgeAlarm(Source));
    TestTrue(TEXT("Corrected crossing fault resets remotely"), Station->ExecuteRemoteCommand(ELBPR010Command::Reset, Source, Authority));

    TestTrue(TEXT("Restart resumes reservation wait"), Station->ExecuteRemoteCommand(ELBPR010Command::Start, Source, Authority));
    Station->Tick(0.1f);
    const FLBPR010SaveState MovingSave = Station->CaptureSaveState();
    ULBPressShopSaveGame* SaveRoot = NewObject<ULBPressShopSaveGame>();
    SaveRoot->PR010 = MovingSave;
    SaveRoot->SavedAtUtc = FDateTime::UtcNow();
    TestEqual(TEXT("PR-010 preserves current factory format eighteen"), SaveRoot->SaveFormatVersion, 18);
    TArray<uint8> Bytes;
    TestTrue(TEXT("PR-010 state serializes"), UGameplayStatics::SaveGameToMemory(SaveRoot, Bytes));
    ULBPressShopSaveGame* Loaded = Cast<ULBPressShopSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes));
    TestNotNull(TEXT("PR-010 state reloads"), Loaded);
    TestTrue(TEXT("PR-010 moving save restores safely"), Reloaded->RestoreSaveState(Loaded ? Loaded->PR010 : MovingSave));
    TestEqual(TEXT("Moving PR-010 save restores stopped and ready"), Reloaded->GetHMIStatus().State, ELBPR010State::Ready);
    TestTrue(TEXT("Moving PR-010 save requires explicit restart"), Reloaded->GetHMIStatus().bRestartRequiredAfterLoad);
    TestEqual(TEXT("Stored stack count survives save/load"), Reloaded->GetHMIStatus().TotalStacksStored, MovingSave.TotalStacksStored);
    TestEqual(TEXT("Inbound stack identity survives safe stop"), Reloaded->GetHMIStatus().InboundStackId, MovingSave.InboundStackId);

    TestTrue(TEXT("Remote isolation request succeeds"),
        Station->ExecuteRemoteCommand(ELBPR010Command::RequestIsolation, Source, Authority));
    TestTrue(TEXT("Zero-energy proof requires motion and stored-energy evidence"),
        Station->ConfirmZeroEnergyIsolation(true, true, TEXT("PR010-ZEP-AUTO-001")));
    TestTrue(TEXT("Authorised isolation release succeeds"),
        Station->ExecuteRemoteCommand(ELBPR010Command::ReleaseIsolation, Source, Authority));
    TestEqual(TEXT("Released PR-010 is ready"), Station->GetHMIStatus().State, ELBPR010State::Ready);

    World->DestroyWorld(false);
    return true;
}

#endif
