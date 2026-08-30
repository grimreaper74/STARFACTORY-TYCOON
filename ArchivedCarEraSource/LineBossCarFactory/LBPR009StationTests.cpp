#include "LBPR009Station.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "Components/SceneComponent.h"
#include "GameFramework/Actor.h"
#include "Kismet/GameplayStatics.h"
#include "LBPressShopSaveGame.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPR009RuntimeAndSaveTest,
    "LineBoss.PressShop.PR009.RuntimeAndSave",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPR009RuntimeAndSaveTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PR009_RuntimeTest"));
    ALBPR009Station* Station = World ? World->SpawnActor<ALBPR009Station>() : nullptr;
    ALBPR009Station* Reloaded = World ? World->SpawnActor<ALBPR009Station>() : nullptr;
    TestNotNull(TEXT("PR-009 station spawns"), Station);
    TestNotNull(TEXT("PR-009 reload target spawns"), Reloaded);
    if (!Station || !Reloaded)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    const FName Authority(TEXT("CW.MW.CONTROL_ROOM"));
    const FName Source(TEXT("MW.MCR.PR009.CONSOLE"));
    Station->ConfigureHealthyInputs(false);
    Station->SetStackRecipe(4, 2, 1.2f);
    TestFalse(TEXT("Untrusted authority cannot power PR-009"),
        Station->ExecuteRemoteCommand(ELBPR009Command::PowerOn, Source, TEXT("UNTRUSTED")));
    TestTrue(TEXT("Control room powers PR-009"),
        Station->ExecuteRemoteCommand(ELBPR009Command::PowerOn, Source, Authority));
    TestTrue(TEXT("Control room starts PR-009"),
        Station->ExecuteRemoteCommand(ELBPR009Command::Start, Source, Authority));
    int32 SuppliedBlankIndex = 1;
    Station->SetUpstreamBlankAvailable(true, TEXT("PR009-BLANK-RUNTIME-0001"));

    TInlineComponentArray<USceneComponent*> PresentationComponents;
    Station->GetComponents(PresentationComponents);
    TestTrue(TEXT("PR-009 exposes modular native presentation contracts"), PresentationComponents.Num() >= 28);
    USceneComponent* FirstInfeedRoll = nullptr;
    for (USceneComponent* Component : PresentationComponents)
    {
        if (Component && Component->GetFName() == TEXT("PR009_InfeedRollMover_01"))
        {
            FirstInfeedRoll = Component;
            break;
        }
    }
    TestNotNull(TEXT("PR-009 exposes the first infeed-roll pivot contract"), FirstInfeedRoll);

    auto SpawnBindingProbe = [World](const TCHAR* Name)
    {
        AActor* Probe = World->SpawnActor<AActor>();
        USceneComponent* Root = NewObject<USceneComponent>(Probe, Name);
        Root->RegisterComponent();
        Probe->SetRootComponent(Root);
        return Probe;
    };
    AActor* InfeedProbe = SpawnBindingProbe(TEXT("InfeedProbeRoot"));
    AActor* GantryZProbe = SpawnBindingProbe(TEXT("GantryZProbeRoot"));
    AActor* OutputProbe = SpawnBindingProbe(TEXT("OutputProbeRoot"));
    AActor* FixedProbe = SpawnBindingProbe(TEXT("FixedProbeRoot"));
    AActor* ServiceDoorProbe = SpawnBindingProbe(TEXT("ServiceDoorProbeRoot"));
    TestTrue(TEXT("Semantic M01 roll binds to its native roll pivot"), Station->BindPresentationActor(
        TEXT("PR009_M01_InfeedRoll_01"), TEXT("moving_roller"), TEXT("ROOT_CA_MW_PR009_STK01"), InfeedProbe));
    TestEqual(TEXT("M01 probe attaches to roll 01"), InfeedProbe->GetRootComponent()->GetAttachParent()->GetFName(),
        FName(TEXT("PR009_InfeedRollMover_01")));
    TestTrue(TEXT("Gantry descendant binds to native Z carriage"), Station->BindPresentationActor(
        TEXT("PR009_03_VacuumCup_01"), TEXT("vacuum_cup"), TEXT("PR009_M04_GantryZ_Carriage_01"), GantryZProbe));
    TestEqual(TEXT("Gantry descendant attaches to Z mover"), GantryZProbe->GetRootComponent()->GetAttachParent()->GetFName(),
        FName(TEXT("PR009_GantryZMover")));
    TestTrue(TEXT("Output roller binds to its native release pivot"), Station->BindPresentationActor(
        TEXT("PR009_08_OutputRoll_09"), TEXT("moving_output_roller"), TEXT("ROOT_CA_MW_PR009_STK01"), OutputProbe));
    TestEqual(TEXT("Output probe attaches to roll 09"), OutputProbe->GetRootComponent()->GetAttachParent()->GetFName(),
        FName(TEXT("PR009_OutputRollMover_09")));
    TestTrue(TEXT("Fixed modular part binds to the station root"), Station->BindPresentationActor(
        TEXT("PR009_01_FrameRail_L"), TEXT("frame"), TEXT("ROOT_CA_MW_PR009_STK01"), FixedProbe));
    TestEqual(TEXT("Fixed probe attaches to station root"), FixedProbe->GetRootComponent()->GetAttachParent()->GetFName(),
        FName(TEXT("PR009_StationRoot")));
    TestTrue(TEXT("Enclosure service door binds to its native hinge pivot"), Station->BindPresentationActor(
        TEXT("PR009_ENC_ServiceDoor_01"), TEXT("service_door"), TEXT("PR009_StationRoot"), ServiceDoorProbe));
    TestEqual(TEXT("Service-door probe attaches to the enclosure hinge"),
        ServiceDoorProbe->GetRootComponent()->GetAttachParent()->GetFName(), FName(TEXT("PR009_ServiceDoorMover")));
    const FRotator InfeedRotationBefore = FirstInfeedRoll ? FirstInfeedRoll->GetRelativeRotation() : FRotator::ZeroRotator;
    Station->Tick(0.25f);
    if (FirstInfeedRoll)
        TestFalse(TEXT("Receiving phase visibly rotates the infeed-roll contract"),
            FirstInfeedRoll->GetRelativeRotation().Equals(InfeedRotationBefore, 0.1f));

    for (int32 Index = 0; Index < 30 && Station->GetHMIStatus().CarriersReleased == 0; ++Index)
    {
        const FLBPR009HMIStatus BeforeTick = Station->GetHMIStatus();
        if (BeforeTick.State == ELBPR009State::Receiving && !BeforeTick.bUpstreamBlankAvailable)
        {
            ++SuppliedBlankIndex;
            Station->SetUpstreamBlankAvailable(true,
                FName(*FString::Printf(TEXT("PR009-BLANK-RUNTIME-%04d"), SuppliedBlankIndex)));
        }
        Station->Tick(1.1f);
    }
    const FLBPR009HMIStatus Running = Station->GetHMIStatus();
    TestTrue(TEXT("PR-009 stacks blanks"), Running.TotalBlanksStacked >= 4);
    TestTrue(TEXT("PR-009 places recipe separators"), Running.SeparatorSheetsPlaced >= 1);
    TestTrue(TEXT("PR-009 releases a completed carrier"), Running.CarriersReleased >= 1);
    TestEqual(TEXT("Released carrier retains all four exact blank identities"), Running.PendingReleasedBlankCount, 4);
    TestFalse(TEXT("Released carrier retains its stack identity"), Running.PendingReleasedStackId.IsNone());

    Station->SetUpstreamBlankAvailable(true, TEXT("PR009-BLANK-AUDIT-0001"));
    Station->Tick(0.2f);
    const FLBPR009SaveState MovingSave = Station->CaptureSaveState();
    ULBPressShopSaveGame* SaveRoot = NewObject<ULBPressShopSaveGame>();
    SaveRoot->PR009 = MovingSave;
    SaveRoot->SavedAtUtc = FDateTime::UtcNow();
    TestEqual(TEXT("Factory save root is format eighteen"), SaveRoot->SaveFormatVersion, 18);
    TArray<uint8> Bytes;
    TestTrue(TEXT("PR-009 state serializes"), UGameplayStatics::SaveGameToMemory(SaveRoot, Bytes));
    ULBPressShopSaveGame* Loaded = Cast<ULBPressShopSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes));
    TestNotNull(TEXT("PR-009 state reloads"), Loaded);
    TestTrue(TEXT("PR-009 moving save restores safely"), Reloaded->RestoreSaveState(Loaded ? Loaded->PR009 : MovingSave));
    TestEqual(TEXT("Moving save restores ready"), Reloaded->GetHMIStatus().State, ELBPR009State::Ready);
    TestTrue(TEXT("Moving save requires explicit restart"), Reloaded->GetHMIStatus().bRestartRequiredAfterLoad);
    TestEqual(TEXT("Stack genealogy count persists"), Reloaded->GetHMIStatus().TotalBlanksStacked, MovingSave.TotalBlanksStacked);

    Station->SetGuardsClosed(false);
    TestEqual(TEXT("Open guard faults PR-009"), Station->GetHMIStatus().ActiveFault, ELBPR009Fault::GuardOpen);
    Station->Tick(2.0f);
    TestEqual(TEXT("Open guard visibly opens the interlocked enclosure door"), Station->GetServiceDoorAngleDegrees(), 105.0f);
    const FLBPR009SaveState OpenDoorSave = Station->CaptureSaveState();
    TestTrue(TEXT("Open service-door state restores"), Reloaded->RestoreSaveState(OpenDoorSave));
    Reloaded->Tick(2.0f);
    TestFalse(TEXT("Restored service door remains interlock-open"), Reloaded->GetHMIStatus().bGuardsClosed);
    TestEqual(TEXT("Restored open door returns to its visible angle"), Reloaded->GetServiceDoorAngleDegrees(), 105.0f);
    Station->SetGuardsClosed(true);
    Station->Tick(2.0f);
    TestEqual(TEXT("Corrected interlock closes the visible enclosure door"), Station->GetServiceDoorAngleDegrees(), 0.0f);
    TestTrue(TEXT("Alarm acknowledgement is required"), Station->AcknowledgeAlarm(Source));
    TestTrue(TEXT("Corrected guard fault resets remotely"),
        Station->ExecuteRemoteCommand(ELBPR009Command::Reset, Source, Authority));

    TestTrue(TEXT("Remote isolation request succeeds"),
        Station->ExecuteRemoteCommand(ELBPR009Command::RequestIsolation, Source, Authority));
    TestTrue(TEXT("Zero-energy proof requires motion and pneumatic evidence"),
        Station->ConfirmZeroEnergyIsolation(true, true, TEXT("PR009-ZEP-AUTO-001")));
    TestTrue(TEXT("Authorised isolation release succeeds"),
        Station->ExecuteRemoteCommand(ELBPR009Command::ReleaseIsolation, Source, Authority));
    TestEqual(TEXT("Released station is ready"), Station->GetHMIStatus().State, ELBPR009State::Ready);

    World->DestroyWorld(false);
    return true;
}

#endif
