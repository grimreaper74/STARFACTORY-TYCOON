#include "LBPR006Station.h"

#if WITH_DEV_AUTOMATION_TESTS
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPR006RuntimeAndSaveTest, "LineBoss.PressShop.PR006.RuntimeAndSave", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPR006RuntimeAndSaveTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PR006_RuntimeTest"));
    ALBPR006Station* Station = World ? World->SpawnActor<ALBPR006Station>() : nullptr;
    ALBPR006Station* Reloaded = World ? World->SpawnActor<ALBPR006Station>() : nullptr;
    TestNotNull(TEXT("PR-006 station spawns"), Station); TestNotNull(TEXT("PR-006 reload target spawns"), Reloaded);
    if (!Station || !Reloaded) { if (World) World->DestroyWorld(false); return false; }
    Station->SetControlPower(true); Station->SetGuardsClosed(true); Station->SetStripAvailable(true); Station->SetCassetteLocked(true); Station->SetDrivesHealthy(true);
    Station->SetLevellerRecipe(TEXT("L-1500-A"), 1.20f, 1.15f, 16.0f);
    TestTrue(TEXT("Healthy leveller starts calibration"), Station->StartLine());
    Station->Tick(2.5f); TestEqual(TEXT("Calibration reaches running"), Station->GetHMIStatus().State, ELBPR006State::Running);
    TestTrue(TEXT("Gap calibrates to recipe"), FMath::IsNearlyEqual(Station->GetHMIStatus().ActualRollGapMm, 1.15f, 0.01f));
    Station->Tick(60.0f); const FLBPR006SaveState RunningSave = Station->CaptureSaveState();
    TestTrue(TEXT("Running advances strip"), RunningSave.StripTravelMetres > 0.0f); TestTrue(TEXT("Running reports realistic load"), RunningSave.MotorLoadPercent > 30.0f);
    TestTrue(TEXT("Moving save restores safely"), Reloaded->RestoreSaveState(RunningSave)); TestEqual(TEXT("Moving restore becomes Ready"), Reloaded->GetHMIStatus().State, ELBPR006State::Ready);
    TestEqual(TEXT("Travel persists"), Reloaded->CaptureSaveState().StripTravelMetres, RunningSave.StripTravelMetres);
    Station->SetCassetteLocked(false); TestEqual(TEXT("Unlocked cassette trips"), Station->GetHMIStatus().ActiveFault, ELBPR006Fault::CassetteUnlocked);
    TestFalse(TEXT("Unsafe cassette fault cannot reset"), Station->ResetFault()); Station->SetCassetteLocked(true); TestTrue(TEXT("Corrected cassette fault resets"), Station->ResetFault());
    World->DestroyWorld(false); return true;
}
#endif
