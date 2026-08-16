#include "LBPR007Station.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"
#include "Engine/World.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPR007RuntimeAndSaveTest,
    "LineBoss.PressShop.PR007.RuntimeAndSave",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPR007RuntimeAndSaveTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PR007_RuntimeTest"));
    ALBPR007Station* Station = World ? World->SpawnActor<ALBPR007Station>() : nullptr;
    ALBPR007Station* Reloaded = World ? World->SpawnActor<ALBPR007Station>() : nullptr;
    TestNotNull(TEXT("PR-007 station spawns"), Station);
    TestNotNull(TEXT("PR-007 reload target spawns"), Reloaded);
    if (!Station || !Reloaded) { if (World) World->DestroyWorld(false); return false; }

    Station->SetControlPower(true);
    Station->SetGuardsClosed(true);
    Station->SetStripThreaded(true);
    Station->SetMistExtractionHealthy(true);
    Station->SetFluidLevels(80.0f, 70.0f);
    Station->SetFilterDifferential(0.3f);
    TestTrue(TEXT("Healthy station starts priming"), Station->StartLine());
    Station->Tick(3.0f);
    TestEqual(TEXT("Priming reaches running state"), Station->GetHMIStatus().State, ELBPR007State::Running);
    Station->Tick(60.0f);
    const FLBPR007SaveState RunningSave = Station->CaptureSaveState();
    TestTrue(TEXT("Running consumes wash fluid"), RunningSave.WashLevelPercent < 80.0f);
    TestTrue(TEXT("Running consumes lubricant"), RunningSave.LubeLevelPercent < 70.0f);
    TestTrue(TEXT("Running advances strip"), RunningSave.StripTravelMetres > 0.0f);
    TestTrue(TEXT("Moving save restores safely"), Reloaded->RestoreSaveState(RunningSave));
    TestEqual(TEXT("Moving save restores stationary ready"), Reloaded->GetHMIStatus().State, ELBPR007State::Ready);
    TestEqual(TEXT("Strip travel persists"), Reloaded->CaptureSaveState().StripTravelMetres, RunningSave.StripTravelMetres);

    Station->SetGuardsClosed(false);
    TestEqual(TEXT("Opened guard raises fault"), Station->GetHMIStatus().ActiveFault, ELBPR007Fault::GuardOpen);
    TestFalse(TEXT("Fault cannot reset with guard open"), Station->ResetFault());
    Station->SetGuardsClosed(true);
    TestTrue(TEXT("Corrected interlock permits reset"), Station->ResetFault());

    World->DestroyWorld(false);
    return true;
}

#endif
