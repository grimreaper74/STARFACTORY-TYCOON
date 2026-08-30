#include "LBPR008Station.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "LBPressShopSaveGame.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPR008RuntimeAndSaveTest,
    "LineBoss.PressShop.PR008.RuntimeAndSave",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    constexpr const TCHAR* PR008SaveSlot = TEXT("LB_AUTOMATION_PR008_RUNTIME_V002");
    const FName ControlRoomAuthority(TEXT("CW.MW.CONTROL_ROOM"));
    const FName ControlRoomSource(TEXT("MW.MCR.PR008.CONSOLE"));

    void ConfigureHealthyPR008(ALBPR008Station* Station)
    {
        Station->SetGuardsClosed(true);
        Station->SetStripAvailable(true);
        Station->SetStripLoopPercent(50.0f);
        Station->SetEdgeTrackingDeviation(0.0f);
        Station->SetFeedPositionError(0.0f);
        Station->SetFeedServoHealthy(true);
        Station->SetPrePunchToolHealthy(true);
        Station->SetPressShearLoad(45.0f);
        Station->SetHydraulicPressure(215.0f);
        Station->SetSlugChuteFill(12.0f);
        Station->SetScrapBinFill(12.0f);
        Station->SetBlankOutfeedClear(true);
        Station->SetSafetyCircuitHealthy(true);
        Station->SetEmergencyStopActive(false);
        Station->SetBlankRecipe(1450.0f, 6.0f);
        Station->SetMeasuredCutLength(1450.0f);
    }
}

bool FLBPR008RuntimeAndSaveTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PR008_RuntimeTest"));
    ALBPR008Station* Station = World ? World->SpawnActor<ALBPR008Station>() : nullptr;
    ALBPR008Station* Reloaded = World ? World->SpawnActor<ALBPR008Station>() : nullptr;
    TestNotNull(TEXT("PR-008 station spawns"), Station);
    TestNotNull(TEXT("PR-008 reload target spawns"), Reloaded);
    if (!Station || !Reloaded)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    ConfigureHealthyPR008(Station);
    TestFalse(TEXT("Untrusted remote authority cannot power PR-008"),
        Station->ExecuteRemoteCommand(ELBPR008Command::PowerOn, ControlRoomSource, TEXT("UNTRUSTED")));
    TestTrue(TEXT("Moorcross control-room authority powers PR-008"),
        Station->ExecuteRemoteCommand(ELBPR008Command::PowerOn, ControlRoomSource, ControlRoomAuthority));
    TestTrue(TEXT("Healthy station starts through the shared remote command gateway"),
        Station->ExecuteRemoteCommand(ELBPR008Command::Start, ControlRoomSource, ControlRoomAuthority));
    Station->Tick(2.0f);
    TestEqual(TEXT("Threading reaches running"), Station->GetHMIStatus().State, ELBPR008State::Running);
    Station->Tick(20.0f);
    const FLBPR008SaveState RunningSave = Station->CaptureSaveState();
    TestEqual(TEXT("PR-008 snapshot uses version three"), RunningSave.Version, 3);
    TestTrue(TEXT("Running advances strip"), RunningSave.StripTravelMetres > 0.0f);
    TestTrue(TEXT("Running produces blanks"), RunningSave.BlanksProduced > 0);
    TestTrue(TEXT("Produced blank enters the traceable discharge buffer"), RunningSave.PendingBlankIds.Num() > 0);
    TestFalse(TEXT("Buffered blank has a semantic identity"), RunningSave.PendingBlankIds[0].IsNone());
    TestTrue(TEXT("Running accumulates contained scrap"), RunningSave.ScrapBinFillPercent > 12.0f);
    TestEqual(TEXT("Remote command source is exposed to HMI/audit consumers"),
        Station->GetHMIStatus().LastCommandSource, ControlRoomSource);

    ULBPressShopSaveGame* SaveRoot = NewObject<ULBPressShopSaveGame>();
    SaveRoot->PR008 = RunningSave;
    SaveRoot->SavedAtUtc = FDateTime::UtcNow();
    TestEqual(TEXT("Current factory save root is format eighteen"), SaveRoot->SaveFormatVersion, 18);
    TArray<uint8> SaveBytes;
    TestTrue(TEXT("PR-008 production state serializes to memory"),
        UGameplayStatics::SaveGameToMemory(SaveRoot, SaveBytes));
    ULBPressShopSaveGame* MemoryLoaded = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromMemory(SaveBytes));
    TestNotNull(TEXT("PR-008 production state reloads from memory"), MemoryLoaded);
    TestTrue(TEXT("PR-008 production state writes to disk slot"),
        UGameplayStatics::SaveGameToSlot(SaveRoot, PR008SaveSlot, 0));
    ULBPressShopSaveGame* DiskLoaded = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromSlot(PR008SaveSlot, 0));
    TestNotNull(TEXT("PR-008 production state reads back from disk slot"), DiskLoaded);
    const FLBPR008SaveState& LoadedState = DiskLoaded ? DiskLoaded->PR008
        : (MemoryLoaded ? MemoryLoaded->PR008 : RunningSave);
    TestTrue(TEXT("Moving save restores safely"), Reloaded->RestoreSaveState(LoadedState));
    TestEqual(TEXT("Moving save restores stationary ready"), Reloaded->GetHMIStatus().State, ELBPR008State::Ready);
    TestTrue(TEXT("Moving save requires an explicit restart command"), Reloaded->GetHMIStatus().bRestartRequiredAfterLoad);
    TestEqual(TEXT("Blank count persists"), Reloaded->CaptureSaveState().BlanksProduced, RunningSave.BlanksProduced);
    TestEqual(TEXT("Pending identified blank count persists"),
        Reloaded->CaptureSaveState().PendingBlankIds.Num(), RunningSave.PendingBlankIds.Num());
    TestEqual(TEXT("Oldest identified blank persists"),
        Reloaded->CaptureSaveState().PendingBlankIds[0], RunningSave.PendingBlankIds[0]);
    TestTrue(TEXT("Automation disk slot is removed"), UGameplayStatics::DeleteGameInSlot(PR008SaveSlot, 0));

    Station->SetGuardsClosed(false);
    TestEqual(TEXT("Opened guard raises the Pro guard/gate fault"),
        Station->GetHMIStatus().ActiveFault, ELBPR008Fault::GuardOpen);
    Station->SetGuardsClosed(true);
    TestFalse(TEXT("Corrected fault cannot reset before alarm acknowledgement"), Station->ResetFault());
    TestTrue(TEXT("Control room acknowledges the latched alarm"), Station->AcknowledgeAlarm(ControlRoomSource));
    TestTrue(TEXT("Corrected and acknowledged interlock permits reset"), Station->ResetFault());

    TestTrue(TEXT("Station restarts after explicit reset"), Station->StartLine());
    Station->Tick(2.0f);
    Station->SetStripLoopPercent(5.0f);
    TestEqual(TEXT("Loop high/low fault is represented"), Station->GetHMIStatus().ActiveFault, ELBPR008Fault::StripLoopOutOfRange);
    Station->SetStripLoopPercent(50.0f);
    Station->AcknowledgeAlarm(ControlRoomSource);
    TestTrue(TEXT("Corrected loop fault resets"), Station->ResetFault());

    TestTrue(TEXT("Station restarts for edge-tracking gate"), Station->StartLine());
    Station->Tick(2.0f);
    Station->SetEdgeTrackingDeviation(151.0f);
    TestEqual(TEXT("Edge tracking limit fault is represented"), Station->GetHMIStatus().ActiveFault, ELBPR008Fault::EdgeTrackingLimit);
    Station->SetEdgeTrackingDeviation(0.0f);
    Station->AcknowledgeAlarm(ControlRoomSource);
    TestTrue(TEXT("Corrected edge fault resets"), Station->ResetFault());

    TestTrue(TEXT("Station restarts for feed-position gate"), Station->StartLine());
    Station->Tick(2.0f);
    Station->SetFeedPositionError(2.1f);
    TestEqual(TEXT("Feed position fault is represented"), Station->GetHMIStatus().ActiveFault, ELBPR008Fault::FeedPositionError);
    Station->SetFeedPositionError(0.0f);
    Station->AcknowledgeAlarm(ControlRoomSource);
    TestTrue(TEXT("Corrected feed-position fault resets"), Station->ResetFault());

    TestTrue(TEXT("Station restarts for cut-length gate"), Station->StartLine());
    Station->Tick(2.0f);
    Station->SetMeasuredCutLength(1452.1f);
    TestEqual(TEXT("Incorrect cut length fault is represented"), Station->GetHMIStatus().ActiveFault, ELBPR008Fault::IncorrectCutLength);
    Station->SetMeasuredCutLength(1450.0f);
    Station->AcknowledgeAlarm(ControlRoomSource);
    TestTrue(TEXT("Corrected cut-length fault resets"), Station->ResetFault());

    TestTrue(TEXT("Station restarts for tool gate"), Station->StartLine());
    Station->Tick(2.0f);
    Station->SetPrePunchToolHealthy(false);
    TestEqual(TEXT("Pre-punch tool fault is represented"), Station->GetHMIStatus().ActiveFault, ELBPR008Fault::PrePunchToolFault);
    Station->SetPrePunchToolHealthy(true);
    Station->AcknowledgeAlarm(ControlRoomSource);
    TestTrue(TEXT("Corrected pre-punch fault resets"), Station->ResetFault());

    TestTrue(TEXT("Station restarts for overload gate"), Station->StartLine());
    Station->Tick(2.0f);
    Station->SetPressShearLoad(101.0f);
    TestEqual(TEXT("Press/shear overload fault is represented"), Station->GetHMIStatus().ActiveFault, ELBPR008Fault::PressShearOverload);
    Station->SetPressShearLoad(45.0f);
    Station->AcknowledgeAlarm(ControlRoomSource);
    TestTrue(TEXT("Corrected overload fault resets"), Station->ResetFault());

    TestTrue(TEXT("Station restarts for slug-chute gate"), Station->StartLine());
    Station->Tick(2.0f);
    Station->SetSlugChuteFill(95.0f);
    TestEqual(TEXT("Slug chute full fault is represented"), Station->GetHMIStatus().ActiveFault, ELBPR008Fault::SlugChuteFull);
    Station->SetSlugChuteFill(12.0f);
    Station->AcknowledgeAlarm(ControlRoomSource);
    TestTrue(TEXT("Corrected slug-chute fault resets"), Station->ResetFault());

    TestTrue(TEXT("Station restarts for E-stop gate"), Station->StartLine());
    Station->Tick(2.0f);
    Station->SetEmergencyStopActive(true);
    TestEqual(TEXT("E-stop latches a stopped fault"), Station->GetHMIStatus().ActiveFault, ELBPR008Fault::EmergencyStopActive);
    Station->SetEmergencyStopActive(false);
    TestFalse(TEXT("Released E-stop still requires safety-circuit reset"), Station->ResetFault());
    Station->SetSafetyCircuitHealthy(true);
    Station->AcknowledgeAlarm(ControlRoomSource);
    TestTrue(TEXT("Released, reset and acknowledged E-stop permits reset"), Station->ResetFault());

    TestTrue(TEXT("Remote isolation request is accepted"),
        Station->ExecuteRemoteCommand(ELBPR008Command::RequestIsolation, ControlRoomSource, ControlRoomAuthority));
    TestEqual(TEXT("Isolation removes control power"), Station->GetHMIStatus().State, ELBPR008State::Isolated);
    TestTrue(TEXT("Zero-energy proof requires explicit evidence"),
        Station->ConfirmZeroEnergyIsolation(true, true, TEXT("PR008-ZEP-AUTO-001")));
    TestTrue(TEXT("Zero-energy evidence is exposed to the HMI"), Station->GetHMIStatus().bZeroEnergyProved);
    TestTrue(TEXT("Authorised isolation release succeeds after proof"),
        Station->ExecuteRemoteCommand(ELBPR008Command::ReleaseIsolation, ControlRoomSource, ControlRoomAuthority));
    TestEqual(TEXT("Released isolation returns the healthy station ready"), Station->GetHMIStatus().State, ELBPR008State::Ready);

    World->DestroyWorld(false);
    return true;
}

#endif
