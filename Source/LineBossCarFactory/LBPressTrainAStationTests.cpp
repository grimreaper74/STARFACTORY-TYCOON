#include "LBPressTrainAStation.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "Engine/StaticMeshActor.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "LBPressShopSaveGame.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPressTrainARuntimeSafetySaveTest,
    "LineBoss.PressShop.PressTrains.TrainA.RuntimeSafetySave",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPressTrainAModularPresentationBindingTest,
    "LineBoss.PressShop.PressTrains.TrainA.ModularPresentationBinding",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPressTrainAApprovedTransferHierarchyTest,
    "LineBoss.PressShop.PressTrains.TrainA.ApprovedTransferHierarchy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPressTrainAFeedBlankPresentationTest,
    "LineBoss.PressShop.PressTrains.TrainA.FeedBlankPresentation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
    const FName TrainAControlRoomAuthority(TEXT("CW.MW.CONTROL_ROOM"));
    const FName TrainAControlRoomSource(TEXT("MW.MCR.TRAIN_A.CONSOLE"));
    const FName TrainATestVehicleModel(TEXT("CAIRNWELL_2040"));
    const FName TrainATestPanelType(TEXT("DOOR_FRONT_LEFT"));
    const FName TrainATestDie(TEXT("DIE_DOOR_FRONT_LEFT_2040"));
    constexpr const TCHAR* TrainASaveSlot = TEXT("LB_AUTOMATION_PRESS_TRAIN_A_V001");

    bool ConfigureHealthyTrainA(ALBPressTrainAStation* Train)
    {
        Train->SetAccessInterlocksClosed(true);
        Train->SetSafetyCircuitHealthy(true);
        Train->SetEmergencyStopActive(false);
        Train->SetDestackHealthy(true);
        Train->SetTransferHealthy(true);
        Train->SetHydraulicPressure(280.0f);
        Train->SetPressLoad(45.0f);
        Train->SetInspectionHealthy(true);
        Train->SetStillageOutputClear(true);
        Train->SetTargetStrokesPerMinute(10.0f);
        return Train->SetActiveProductionRecipe(
            TrainATestVehicleModel, TrainATestPanelType, TrainATestDie);
    }
}

bool FLBPressTrainARuntimeSafetySaveTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PressTrainA_RuntimeSafetySave"));
    ALBPressTrainAStation* Train = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    ALBPressTrainAStation* Reloaded = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    TestNotNull(TEXT("Train A authority spawns"), Train);
    TestNotNull(TEXT("Train A reload target spawns"), Reloaded);
    if (!Train || !Reloaded)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("Train A selects an approved Cairnwell 2040 panel recipe and installed die"),
        ConfigureHealthyTrainA(Train));
    TestTrue(TEXT("Train A loads its complete isolated audio asset set"), Train->HasCompleteAudioAssetSet());
    TestFalse(TEXT("Isolated Train A requests no hydraulic sound"), Train->IsAudioLayerRequested(TEXT("hydraulic_power")));
    TestTrue(TEXT("Identified reserved blank enters Train A input buffer"),
        Train->QueueReservedBlank(TEXT("RES-AUTO-0001"), TEXT("PR010-BLANK-000001")));
    TestFalse(TEXT("Duplicate blank identity is rejected"),
        Train->QueueReservedBlank(TEXT("RES-AUTO-0002"), TEXT("PR010-BLANK-000001")));
    TestFalse(TEXT("Untrusted authority cannot power Train A"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::PowerOn, TrainAControlRoomSource, TEXT("UNTRUSTED")));
    TestTrue(TEXT("Moorcross control-room authority powers Train A"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::PowerOn, TrainAControlRoomSource, TrainAControlRoomAuthority));
    TestTrue(TEXT("Powered ready Train A requests the hydraulic layer"), Train->IsAudioLayerRequested(TEXT("hydraulic_power")));
    TestFalse(TEXT("Ready Train A does not request transfer motion"), Train->IsAudioLayerRequested(TEXT("transfer_servo")));
    TestTrue(TEXT("Healthy Train A starts through the remote gateway"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::Start, TrainAControlRoomSource, TrainAControlRoomAuthority));
    TestTrue(TEXT("Destack phase requests transfer motion sound"), Train->IsAudioLayerRequested(TEXT("transfer_servo")));
    TestFalse(TEXT("Active process blank retains source identity"), Train->GetHMIStatus().InProcessBlankId.IsNone());
    Train->Tick(6.1f);
    TestEqual(TEXT("One complete seven-stage cycle produces one good panel"), Train->GetHMIStatus().GoodPanels, 1);
    TestEqual(TEXT("Completed panel enters identified output buffer"), Train->GetHMIStatus().PendingPanelCount, 1);
    TestFalse(TEXT("Output panel has a semantic identity"), Train->GetHMIStatus().OldestPendingPanelId.IsNone());
    TestEqual(TEXT("Train waits ready when no further blank is available"), Train->GetHMIStatus().State, ELBPressTrainAState::Ready);

    FName PanelId;
    TestTrue(TEXT("Panel handoff reserves the oldest identified panel"),
        Train->RequestPanelHandoff(TEXT("PTA-HANDOFF-0001"), PanelId));
    TestFalse(TEXT("Reserved output panel identity is non-empty"), PanelId.IsNone());
    TestFalse(TEXT("Mismatched handoff transaction cannot consume a panel"),
        Train->ConfirmPanelHandoff(TEXT("PTA-HANDOFF-WRONG")));
    TestTrue(TEXT("Matching handoff transaction consumes exactly one panel"),
        Train->ConfirmPanelHandoff(TEXT("PTA-HANDOFF-0001")));

    TestTrue(TEXT("Second identified blank is accepted"),
        Train->QueueReservedBlank(TEXT("RES-AUTO-0002"), TEXT("PR010-BLANK-000002")));
    TestTrue(TEXT("Train restarts for controlled-stop proof"), Train->StartLine());
    Train->Tick(2.0f);
    TestTrue(TEXT("A forming phase requests press cause-and-effect sound"), Train->IsAudioLayerRequested(TEXT("press_phase")));
    TestTrue(TEXT("Press phase emits an identified stroke cue"), Train->GetAudioCueSequence() > 0);
    TestEqual(TEXT("Press cue uses the authored stroke asset"), Train->GetLastAudioCueId(), FName(TEXT("PTA_PressStroke_v002")));
    const float ProgressBeforeStop = Train->GetHMIStatus().CycleProgress;
    Train->RequestControlledStop();
    TestEqual(TEXT("Controlled stop enters stopping state"), Train->GetHMIStatus().State, ELBPressTrainAState::Stopping);
    TestEqual(TEXT("Controlled stop emits its authored transition cue"), Train->GetLastAudioCueId(), FName(TEXT("PTA_ControlledStop_v002")));
    Train->Tick(0.6f);
    TestEqual(TEXT("Controlled stop reaches stationary ready state"), Train->GetHMIStatus().State, ELBPressTrainAState::Ready);
    TestTrue(TEXT("Controlled stop preserves deterministic cycle position"),
        FMath::IsNearlyEqual(Train->GetHMIStatus().CycleProgress, ProgressBeforeStop, 0.001f));
    TestTrue(TEXT("Explicit restart resumes the preserved in-process blank"), Train->StartLine());

    Train->SetAccessInterlocksClosed(false);
    TestEqual(TEXT("Opening an access interlock latches a fault"),
        Train->GetHMIStatus().ActiveFault, ELBPressTrainAFault::AccessInterlockOpen);
    TestTrue(TEXT("Access fault requests the warning alarm layer"), Train->IsAudioLayerRequested(TEXT("warning_alarm")));
    TestEqual(TEXT("Access fault emits the guarded-access cue"), Train->GetLastAudioCueId(), FName(TEXT("PTA_GateInterlock_v002")));
    Train->SetAccessInterlocksClosed(true);
    TestFalse(TEXT("Corrected fault cannot reset before acknowledgement"), Train->ResetFault());
    TestTrue(TEXT("Control room acknowledges the latched alarm"), Train->AcknowledgeAlarm(TrainAControlRoomSource));
    TestTrue(TEXT("Corrected and acknowledged access fault resets"), Train->ResetFault());
    TestTrue(TEXT("Train explicitly restarts after fault reset"), Train->StartLine());

    Train->SetEmergencyStopActive(true);
    TestEqual(TEXT("Emergency stop latches a distinct fault"),
        Train->GetHMIStatus().ActiveFault, ELBPressTrainAFault::EmergencyStopActive);
    TestEqual(TEXT("Emergency stop emits the distinct emergency cue"), Train->GetLastAudioCueId(), FName(TEXT("PTA_EmergencyStop_v002")));
    Train->SetEmergencyStopActive(false);
    TestFalse(TEXT("Released E-stop still requires safety reset and acknowledgement"), Train->ResetFault());
    Train->SetSafetyCircuitHealthy(true);
    Train->AcknowledgeAlarm(TrainAControlRoomSource);
    TestTrue(TEXT("Released, reset and acknowledged E-stop permits fault reset"), Train->ResetFault());

    TestTrue(TEXT("Remote isolation request is accepted"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::RequestIsolation, TrainAControlRoomSource, TrainAControlRoomAuthority));
    TestEqual(TEXT("Isolation removes control power"), Train->GetHMIStatus().State, ELBPressTrainAState::Isolated);
    TestFalse(TEXT("Zero-energy proof rejects missing evidence"),
        Train->ConfirmZeroEnergyIsolation(true, true, NAME_None));
    TestTrue(TEXT("Zero-energy proof records explicit evidence"),
        Train->ConfirmZeroEnergyIsolation(true, true, TEXT("PTA-ZEP-AUTO-001")));
    TestEqual(TEXT("Safety evidence identity is exposed to HMI consumers"),
        Train->GetHMIStatus().LastSafetyEvidenceId, FName(TEXT("PTA-ZEP-AUTO-001")));
    TestTrue(TEXT("Authorised isolation release succeeds after proof"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::ReleaseIsolation, TrainAControlRoomSource, TrainAControlRoomAuthority));
    TestEqual(TEXT("Released isolation returns Train A ready"), Train->GetHMIStatus().State, ELBPressTrainAState::Ready);

    TestTrue(TEXT("Third identified blank is accepted for save proof"),
        Train->QueueReservedBlank(TEXT("RES-AUTO-0003"), TEXT("PR010-BLANK-000003")));
    TestTrue(TEXT("Train starts before moving-state save"), Train->StartLine());
    Train->Tick(1.5f);
    const FLBPressTrainASaveState MovingSave = Train->CaptureSaveState();
    TestEqual(TEXT("Train A snapshot uses approved-recipe save version four"), MovingSave.Version, 4);
    TestTrue(TEXT("Train A snapshot carries an immutable persistent GUID"), MovingSave.PersistentTrainGuid.IsValid());
    TestEqual(TEXT("Train A snapshot carries its station identity"), Train->GetStationId(3), FName(TEXT("A-S03")));
    TestEqual(TEXT("Train A moving snapshot is cycling"), MovingSave.State, ELBPressTrainAState::Cycling);
    TestFalse(TEXT("Moving snapshot preserves in-process blank identity"), MovingSave.InProcessBlankId.IsNone());
    TestTrue(TEXT("Moving snapshot preserves nonzero deterministic progress"), MovingSave.CycleElapsedSeconds > 0.0f);

    ULBPressShopSaveGame* SaveRoot = NewObject<ULBPressShopSaveGame>();
    SaveRoot->PressTrainA = MovingSave;
    SaveRoot->SavedAtUtc = FDateTime::UtcNow();
    SaveRoot->PressTrains.Add(MovingSave);
    TestEqual(TEXT("Factory save root advances to format eighteen"), SaveRoot->SaveFormatVersion, 18);
    TArray<uint8> SaveBytes;
    TestTrue(TEXT("Train A production state serializes to memory"), UGameplayStatics::SaveGameToMemory(SaveRoot, SaveBytes));
    ULBPressShopSaveGame* MemoryLoaded = Cast<ULBPressShopSaveGame>(UGameplayStatics::LoadGameFromMemory(SaveBytes));
    TestNotNull(TEXT("Train A production state reloads from memory"), MemoryLoaded);
    TestTrue(TEXT("Train A production state writes to disk slot"), UGameplayStatics::SaveGameToSlot(SaveRoot, TrainASaveSlot, 0));
    ULBPressShopSaveGame* DiskLoaded = Cast<ULBPressShopSaveGame>(UGameplayStatics::LoadGameFromSlot(TrainASaveSlot, 0));
    TestNotNull(TEXT("Train A production state reads from disk slot"), DiskLoaded);
    const FLBPressTrainASaveState& LoadedState = DiskLoaded ? DiskLoaded->PressTrainA
        : (MemoryLoaded ? MemoryLoaded->PressTrainA : MovingSave);
    TestTrue(TEXT("Moving Train A save restores safely"), Reloaded->RestoreSaveState(LoadedState));
    TestEqual(TEXT("Moving save restores stationary ready"), Reloaded->GetHMIStatus().State, ELBPressTrainAState::Ready);
    TestTrue(TEXT("Moving save requires explicit restart"), Reloaded->GetHMIStatus().bRestartRequiredAfterLoad);
    TestEqual(TEXT("In-process blank identity persists"), Reloaded->GetHMIStatus().InProcessBlankId, MovingSave.InProcessBlankId);
    TestTrue(TEXT("Cycle progress persists deterministically"),
        FMath::IsNearlyEqual(Reloaded->GetHMIStatus().CycleProgress,
            MovingSave.CycleElapsedSeconds / (60.0f / MovingSave.TargetStrokesPerMinute), 0.001f));
    TestTrue(TEXT("Automation disk slot is removed"), UGameplayStatics::DeleteGameInSlot(TrainASaveSlot, 0));

    ALBPressTrainAStation* Variant = World->SpawnActor<ALBPressTrainAStation>();
    TestNotNull(TEXT("Shared press-train authority spawns for an isolated variant"), Variant);
    if (Variant)
    {
        TestFalse(TEXT("Malformed train identity is rejected"), Variant->ConfigureTrainVariant(
            TEXT("TRAIN_AA"), TEXT("TRAIN AA"), TEXT("UNAUTHORISED"), FLinearColor::White));
        TestFalse(TEXT("Factory-builder range stops after the four designed trains"), Variant->ConfigureTrainVariant(
            TEXT("TRAIN_E"), TEXT("TRAIN E"), TEXT("UNAUTHORISED CAPACITY"), FLinearColor::White));
        TestTrue(TEXT("Factory-builder range includes designed Train D"), Variant->ConfigureTrainVariant(
            TEXT("TRAIN_D"), TEXT("TRAIN D"), TEXT("FRONT WINGS"), FLinearColor::White));
        TestTrue(TEXT("Train B identity configures on the shared authority"), Variant->ConfigureTrainVariant(
            TEXT("TRAIN_B"), TEXT("TRAIN B"), TEXT("FLOORS / UNDERBODY"), FLinearColor(0.302f, 0.545f, 0.290f)));
        TestEqual(TEXT("Configured Train B identity reaches HMI consumers"),
            Variant->GetHMIStatus().TrainId, FName(TEXT("TRAIN_B")));
        TestEqual(TEXT("Configured Train B part family is retained"),
            Variant->GetPartFamily(), FString(TEXT("FLOORS / UNDERBODY")));
        TestFalse(TEXT("Train B rejects a Train A save snapshot"), Variant->RestoreSaveState(MovingSave));
        TestTrue(TEXT("Train B selects an approved Cairnwell 2040 panel recipe and installed die"),
            ConfigureHealthyTrainA(Variant));
        TestTrue(TEXT("Train B accepts an identified reserved blank"),
            Variant->QueueReservedBlank(TEXT("RES-B-0001"), TEXT("PR010-BLANK-B-000001")));
        TestTrue(TEXT("Train B powers through the same trusted remote authority"),
            Variant->ExecuteRemoteCommand(ELBPressTrainACommand::PowerOn, TEXT("MW.MCR.TRAIN_B.CONSOLE"), TrainAControlRoomAuthority));
        TestTrue(TEXT("Train B starts through the shared safe process authority"),
            Variant->ExecuteRemoteCommand(ELBPressTrainACommand::Start, TEXT("MW.MCR.TRAIN_B.CONSOLE"), TrainAControlRoomAuthority));
        Variant->Tick(6.1f);
        TestTrue(TEXT("Train B output identity uses its own namespace"),
            Variant->GetHMIStatus().OldestPendingPanelId.ToString().StartsWith(TEXT("PTB-PANEL-")));
    }

    World->DestroyWorld(false);
    return true;
}

bool FLBPressTrainAModularPresentationBindingTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PressTrainA_ModularPresentation"));
    auto SpawnTagged = [World](const TCHAR* Role, bool bStageS03)
    {
        AStaticMeshActor* Actor = World ? World->SpawnActor<AStaticMeshActor>() : nullptr;
        if (Actor)
        {
            Actor->Tags.Add(FName(Role));
            if (bStageS03) Actor->Tags.Add(TEXT("LB.PressTrain.Stage.S03"));
        }
        return Actor;
    };
    AStaticMeshActor* Gate = SpawnTagged(TEXT("LB.PressTrain.Role.access_gate"), false);
    AStaticMeshActor* Flywheel = SpawnTagged(TEXT("LB.PressTrain.Role.flywheel_rotor"), false);
    AStaticMeshActor* Slide = SpawnTagged(TEXT("LB.PressTrain.Role.moving_press_slide"), true);
    AStaticMeshActor* UpperDie = SpawnTagged(TEXT("LB.PressTrain.Role.moving_upper_die"), true);
    ALBPressTrainAStation* Train = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    TestNotNull(TEXT("Modular validation train spawns"), Train);
    TestNotNull(TEXT("Hinge-pivot gate presentation spawns"), Gate);
    TestNotNull(TEXT("Flywheel presentation spawns"), Flywheel);
    TestNotNull(TEXT("S03 slide presentation spawns"), Slide);
    TestNotNull(TEXT("S03 upper-die presentation spawns"), UpperDie);
    if (!World || !Train || !Gate || !Flywheel || !Slide || !UpperDie)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    // This transient unit-test world is not initialized through the editor/PIE
    // lifecycle. Dispatch the authority's BeginPlay explicitly so it performs
    // the same presentation-tag scan used by the saved v658 runtime map.
    Train->DispatchBeginPlay();
    const float S03SlideOpenZ = Slide->GetActorLocation().Z;
    const float S03UpperDieOpenZ = UpperDie->GetActorLocation().Z;
    TestTrue(TEXT("Idle S03 tagged slide opens one accepted 65 cm stroke above contact"),
        FMath::IsNearlyEqual(S03SlideOpenZ, 65.0f, 0.1f));
    TestTrue(TEXT("Idle S03 tagged upper die opens with its slide"),
        FMath::IsNearlyEqual(S03UpperDieOpenZ, S03SlideOpenZ, 0.1f));
    Train->SetAccessInterlocksClosed(false);
    Train->Tick(0.0f);
    TestTrue(TEXT("Opening the access interlock rotates its hinge-tagged visual"),
        FMath::IsNearlyEqual(Gate->GetActorRotation().Yaw, 72.0f, 0.1f));
    Train->SetAccessInterlocksClosed(true);
    Train->Tick(0.0f);
    TestTrue(TEXT("Closing the access interlock restores its authored pose"),
        FMath::IsNearlyZero(Gate->GetActorRotation().Yaw, 0.1f));

    TestTrue(TEXT("Modular motion proof selects an approved panel recipe and installed die"),
        ConfigureHealthyTrainA(Train));
    TestTrue(TEXT("Modular motion proof accepts one reserved blank"),
        Train->QueueReservedBlank(TEXT("RES-MODULAR-0001"), TEXT("PR010-BLANK-MODULAR-0001")));
    TestTrue(TEXT("Modular motion proof powers the native authority"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::PowerOn, TrainAControlRoomSource, TrainAControlRoomAuthority));
    TestTrue(TEXT("Modular motion proof starts the native authority"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::Start, TrainAControlRoomSource, TrainAControlRoomAuthority));
    Train->Tick(0.5f);
    TestFalse(TEXT("Cycling rotates the separate flywheel visual"),
        FMath::IsNearlyZero(Flywheel->GetActorRotation().Pitch, 0.1f));
    Train->Tick(1.5f);
    // The accepted v735 transform is the closed/contact pose. The presentation now
    // approaches that zero datum from its +65 cm idle/open pose; negative travel would
    // push the ram and upper die through the bolster.
    TestTrue(TEXT("S03 phase lowers the separate ram/slide toward contact"),
        Slide->GetActorLocation().Z < S03SlideOpenZ - 1.0f
            && Slide->GetActorLocation().Z >= -0.1f);
    TestTrue(TEXT("S03 phase carries the separate upper die toward contact"),
        UpperDie->GetActorLocation().Z < S03UpperDieOpenZ - 1.0f
            && UpperDie->GetActorLocation().Z >= -0.1f);
    TestTrue(TEXT("S03 ram and upper die retain the same commanded stroke"),
        FMath::IsNearlyEqual(Slide->GetActorLocation().Z, UpperDie->GetActorLocation().Z, 0.1f));
    World->DestroyWorld(false);
    return true;
}

bool FLBPressTrainAApprovedTransferHierarchyTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PressTrainA_ApprovedTransferHierarchy"));
    ALBPressTrainAStation* Train = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    TestNotNull(TEXT("Approved transfer hierarchy train spawns"), Train);
    if (!World || !Train)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    Train->SetActorLocation(FVector(1234.0f, -5678.0f, 90.0f));
    Train->SetActorRotation(FRotator(0.0f, 37.0f, 0.0f));
    TestTrue(TEXT("Approved modular visual enables"), Train->EnableCompletedRuntimeVisual());
    TestTrue(TEXT("Approved modular visual reports active"), Train->HasCompletedRuntimeVisual());
    TestEqual(TEXT("Complete train exposes the six-part compatible press presentation for five stages"),
        Train->GetApprovedModularVisualCount(), 105);
    const FBox ProtectedEnvelope = ALBPressTrainAStation::GetProtectedLocalEnvelope();
    TestTrue(TEXT("Protected train envelope starts at the S01 clearance datum"),
        ProtectedEnvelope.Min.Equals(FVector(-750.0f, -750.0f, 0.0f), 0.01f));
    TestTrue(TEXT("Protected train envelope contains the complete S01-S07 line"),
        ProtectedEnvelope.Max.Equals(FVector(750.0f, 6534.0f, 950.0f), 0.01f));

    TArray<USceneComponent*> SceneComponents;
    Train->GetComponents<USceneComponent>(SceneComponents);
    const auto FindScene = [&SceneComponents](const FName Name) -> USceneComponent*
    {
        for (USceneComponent* Component : SceneComponents)
            if (Component && Component->GetFName() == Name) return Component;
        return nullptr;
    };

    const TCHAR* PressPartAssets[] = {TEXT("S03_STATIC_SHELL"), TEXT("S03_RAM_SLIDE"),
        TEXT("S03_UPPER_DIE"), TEXT("S03_LOWER_DIE_BOLSTER"),
        TEXT("SM_CA_Factory_Elect_net_MeshyMaster_v632"), TEXT("SM_CA_Factory_Opera_HMI_MeshyMaster_v632")};
    const TCHAR* PressMoverNames[] = {TEXT("PTA_S02SlideMover"), TEXT("PTA_S03SlideMover"),
        TEXT("PTA_S04SlideMover"), TEXT("PTA_S05SlideMover"), TEXT("PTA_S06SlideMover")};
    UStaticMeshComponent* S03Ram = nullptr;
    UStaticMeshComponent* S03UpperDie = nullptr;
    TArray<UStaticMeshComponent*> PressShells;
    for (int32 Stage = 0; Stage < 5; ++Stage)
    {
        USceneComponent* StageMover = FindScene(PressMoverNames[Stage]);
        TestNotNull(*FString::Printf(TEXT("S%02d slide mover exists"), Stage + 2), StageMover);
        for (int32 Part = 0; Part < UE_ARRAY_COUNT(PressPartAssets); ++Part)
        {
            UStaticMeshComponent* PressPart = Cast<UStaticMeshComponent>(FindScene(
                FName(*FString::Printf(TEXT("PTA_ApprovedPressS%02d_Part%02d"), Stage + 2, Part))));
            TestNotNull(*FString::Printf(TEXT("Complete S%02d press part %d exists"), Stage + 2, Part), PressPart);
            if (!PressPart || !PressPart->GetStaticMesh()) continue;
            const FString ExpectedPath = FString::Printf(TEXT("/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/Cairnwell_S03_Movable_v632Controls_v735/StaticMeshes/%s.%s"),
                PressPartAssets[Part], PressPartAssets[Part]);
            TestEqual(*FString::Printf(TEXT("S%02d part %d uses the approved runtime asset"), Stage + 2, Part),
                PressPart->GetStaticMesh()->GetPathName(), ExpectedPath);
            TestTrue(*FString::Printf(TEXT("S%02d part %d retains the accepted scale"), Stage + 2, Part),
                PressPart->GetRelativeScale3D().Equals(FVector(6.57f), 0.001f));
            TestTrue(*FString::Printf(TEXT("S%02d part %d preserves the compact 10.07 m pitch"), Stage + 2, Part),
                PressPart->GetRelativeLocation().Equals(
                    FVector(0.0f, 654.0f + Stage * 1007.0f, 410.997f), 0.02f));
            TestTrue(*FString::Printf(TEXT("S%02d part %d throat follows local +Y flow"), Stage + 2, Part),
                FMath::IsNearlyZero(PressPart->GetRelativeRotation().Yaw, 0.01f));
            if (Part == 1 || Part == 2)
            {
                TestTrue(*FString::Printf(TEXT("S%02d moving part %d follows its stage mover"), Stage + 2, Part),
                    PressPart->GetAttachParent() == StageMover);
                TestTrue(*FString::Printf(TEXT("S%02d moving part %d is movable"), Stage + 2, Part),
                    PressPart->Mobility == EComponentMobility::Movable);
            }
            else
            {
                TestTrue(*FString::Printf(TEXT("S%02d fixed part %d stays off its slide mover"), Stage + 2, Part),
                    PressPart->GetAttachParent() != StageMover);
            }
            if (Stage == 1 && Part == 1) S03Ram = PressPart;
            if (Stage == 1 && Part == 2) S03UpperDie = PressPart;
            if (Part == 0) PressShells.Add(PressPart);
        }
    }
    UStaticMeshComponent* S02Shell = Cast<UStaticMeshComponent>(
            FindScene(TEXT("PTA_ApprovedPressS02_Part00")));
    if (S02Shell && S02Shell->GetStaticMesh())
    {
        const float FloorZ = S02Shell->GetRelativeLocation().Z
            + S02Shell->GetStaticMesh()->GetBoundingBox().Min.Z * S02Shell->GetRelativeScale3D().Z;
        TestTrue(TEXT("Complete press shell is floor seated from its accepted transform"),
            FMath::IsNearlyZero(FloorZ, 0.2f));

        const auto BoundsInTrain = [Train](UStaticMeshComponent* Component)
        {
            const FTransform ComponentToTrain = Component->GetComponentTransform()
                .GetRelativeTransform(Train->GetActorTransform());
            return Component->GetStaticMesh()->GetBoundingBox().TransformBy(ComponentToTrain);
        };
        FBox S01Bounds(ForceInit);
        if (UStaticMeshComponent* Part0 = Cast<UStaticMeshComponent>(
            FindScene(TEXT("PTA_CompletedRuntimeVisual"))))
        {
            if (Part0->GetStaticMesh()) S01Bounds += BoundsInTrain(Part0);
        }
        for (int32 PartIndex = 1; PartIndex < 52; ++PartIndex)
        {
            UStaticMeshComponent* Part = Cast<UStaticMeshComponent>(FindScene(FName(
                *FString::Printf(TEXT("PTA_ApprovedS01Part%02d"), PartIndex))));
            if (Part && Part->GetStaticMesh()) S01Bounds += BoundsInTrain(Part);
        }
        const FBox S02Bounds = BoundsInTrain(S02Shell);
        TestTrue(TEXT("S01 aggregate reaches its audited 3.50 m process end"),
            S01Bounds.IsValid && FMath::IsNearlyEqual(S01Bounds.Max.Y, 350.0f, 0.2f));
        TestTrue(*FString::Printf(TEXT("S02 shell starts about 25 cm after S01 (%.3f cm)"),
            S02Bounds.Min.Y - S01Bounds.Max.Y),
            S01Bounds.IsValid && FMath::IsNearlyEqual(
                S02Bounds.Min.Y - S01Bounds.Max.Y, 25.315f, 0.2f));
    }

    USceneComponent* PanelDatum = FindScene(TEXT("PTA_InternalProcessPanelDatum"));
    TestNotNull(TEXT("Geometry-audited internal panel datum exists"), PanelDatum);
    if (PanelDatum)
        TestTrue(TEXT("Internal panel datum stays on the verified 2.02221 m throat centreline"),
            FMath::IsNearlyEqual(PanelDatum->GetRelativeLocation().Z, 202.221f, 0.01f));
    TestTrue(TEXT("Builder input port remains on the lower adapter datum"),
        FMath::IsNearlyEqual(Train->FactoryInputPort->GetRelativeLocation().Z, 110.0f, 0.01f));
    TestTrue(TEXT("Builder output port remains on the lower adapter datum"),
        FMath::IsNearlyEqual(Train->FactoryOutputPort->GetRelativeLocation().Z, 110.0f, 0.01f));
    TestTrue(TEXT("Builder output port follows the compact S07 end"),
        FMath::IsNearlyEqual(Train->FactoryOutputPort->GetRelativeLocation().Y, 6284.0f, 0.01f));

    USceneComponent* S07RobotBase = FindScene(TEXT("PTA_ApprovedS07Base"));
    USceneComponent* S07RobotMover = FindScene(TEXT("PTA_UnloadRobotMover"));
    USceneComponent* S07Portal = FindScene(TEXT("PTA_ApprovedS07InspectionPortal"));
    TestNotNull(TEXT("Approved S07 robot base exists"), S07RobotBase);
    TestNotNull(TEXT("Approved S07 robot base mover exists"), S07RobotMover);
    TestNotNull(TEXT("Approved S07 inspection portal exists"), S07Portal);
    if (S07RobotBase && S07RobotMover)
    {
        TestTrue(TEXT("S07 robot follows its own grounded rotation origin"),
            S07RobotBase->GetAttachParent() == S07RobotMover);
        TestTrue(TEXT("S07 robot base mover is raised to its audited floor seat"),
            S07RobotMover->GetRelativeLocation().Equals(FVector(-300.0f, 5684.0f, 130.0f), 0.01f));
        TestTrue(TEXT("S07 split source keeps its shared local origin"),
            S07RobotBase->GetRelativeLocation().IsNearlyZero(0.01f));
    }
    if (S07Portal)
        TestTrue(TEXT("S07 grounded portal follows the compact unload station"),
            S07Portal->GetRelativeLocation().Equals(FVector(0.0f, 5684.0f, 0.0f), 0.01f));

    USceneComponent* S03Mover = FindScene(TEXT("PTA_S03SlideMover"));
    TestNotNull(TEXT("Complete S03 ram exists"), S03Ram);
    TestNotNull(TEXT("Complete S03 upper die exists"), S03UpperDie);
    TestNotNull(TEXT("S03 slide mover exists"), S03Mover);
    if (S03Ram && S03UpperDie && S03Mover && PanelDatum && S03UpperDie->GetStaticMesh())
    {
        // This focused test world is intentionally not editor/PIE initialised, so
        // component-world transforms are not a reliable parent-propagation oracle.
        // Verify the authored hierarchy in train-local coordinates instead: the stage
        // mover is relative to StationRoot and both accepted moving parts are relative
        // to that mover.
        // The imported v735 transform is the closed/contact datum at mover Z=0,
        // while the live train deliberately initialises at its safe open/idle pose.
        const FVector InitialOpenLocation = S03Mover->GetRelativeLocation();
        TestTrue(TEXT("S03 live idle pose starts exactly one 65 cm stroke open"),
            InitialOpenLocation.Equals(FVector(0.0f, 0.0f, 65.0f), 0.01f));
        const auto UpperDieUndersideInTrain = [S03Mover, S03UpperDie]()
        {
            return S03Mover->GetRelativeLocation().Z + S03UpperDie->GetRelativeLocation().Z
                + S03UpperDie->GetStaticMesh()->GetBoundingBox().Min.Z
                    * S03UpperDie->GetRelativeScale3D().Z;
        };
        const auto RamOriginInTrain = [S03Mover, S03Ram]()
        {
            return S03Mover->GetRelativeLocation().Z + S03Ram->GetRelativeLocation().Z;
        };
        S03Mover->SetRelativeLocation(FVector::ZeroVector);
        const float ContactUndersideZ = UpperDieUndersideInTrain();
        const float RamContactZ = RamOriginInTrain();
        TestTrue(TEXT("Accepted S03 closed pose lands on the geometry-audited panel datum"),
            FMath::IsNearlyEqual(ContactUndersideZ, PanelDatum->GetRelativeLocation().Z, 0.3f));
        S03Mover->SetRelativeLocation(InitialOpenLocation);
        const float OpenUndersideZ = UpperDieUndersideInTrain();
        TestTrue(TEXT("S03 idle pose opens the upper die exactly one 65 cm stroke"),
            FMath::IsNearlyEqual(OpenUndersideZ - ContactUndersideZ, 65.0f, 0.05f));
        TestTrue(TEXT("S03 idle pose raises the accepted ram with its upper die"),
            FMath::IsNearlyEqual(RamOriginInTrain() - RamContactZ, 65.0f, 0.05f));
        S03Mover->SetRelativeLocation(InitialOpenLocation);
    }

    TArray<USceneComponent*> GapRoots;
    TArray<USceneComponent*> LiftMovers;
    TArray<USceneComponent*> PitchMovers;
    TArray<USceneComponent*> Frames;
    TArray<UStaticMeshComponent*> CupArrays;
    TArray<FTransform> FrameRestTransforms;
    const TCHAR* TransferPartNames[] = {TEXT("Frame"), TEXT("Crossbeam"), TEXT("Actuator"), TEXT("CupArray")};
    const TCHAR* TransferAssetNames[] = {TEXT("SM_CA_PT_SEG__TIC_FRAME_v746"),
        TEXT("SM_CA_PT_SEG__CROSSBEAM_v746"), TEXT("SM_CA_PT_SEG__ATOR_PACK_v746"),
        TEXT("SM_CA_PT_SEG_CUP_ARRAY_v746")};
    for (int32 Gap = 0; Gap < 4; ++Gap)
    {
        const FName RootName(*FString::Printf(TEXT("PTA_ApprovedTransfer%02d_Root"), Gap + 1));
        const FName LiftName = Gap == 0 ? FName(TEXT("PTA_TransferLiftMover"))
            : FName(*FString::Printf(TEXT("PTA_ApprovedTransfer%02d_LiftMover"), Gap + 1));
        const FName PitchName = Gap == 0 ? FName(TEXT("PTA_TransferPitchMover"))
            : FName(*FString::Printf(TEXT("PTA_ApprovedTransfer%02d_PitchMover"), Gap + 1));
        const FName FrameName(*FString::Printf(TEXT("PTA_ApprovedTransfer%02d_Frame"), Gap + 1));
        USceneComponent* Root = FindScene(RootName);
        USceneComponent* Lift = FindScene(LiftName);
        USceneComponent* Pitch = FindScene(PitchName);
        USceneComponent* Frame = FindScene(FrameName);
        TestNotNull(*FString::Printf(TEXT("Gap %d root exists"), Gap + 1), Root);
        TestNotNull(*FString::Printf(TEXT("Gap %d lift mover exists"), Gap + 1), Lift);
        TestNotNull(*FString::Printf(TEXT("Gap %d pitch mover exists"), Gap + 1), Pitch);
        TestNotNull(*FString::Printf(TEXT("Gap %d fixed frame exists"), Gap + 1), Frame);
        if (!Root || !Lift || !Pitch || !Frame) continue;
        TestTrue(*FString::Printf(TEXT("Gap %d frame stays on its fixed root"), Gap + 1),
            Frame->GetAttachParent() == Root);
        TestTrue(*FString::Printf(TEXT("Gap %d lift attaches to its fixed root"), Gap + 1),
            Lift->GetAttachParent() == Root);
        TestTrue(*FString::Printf(TEXT("Gap %d pitch nests beneath lift"), Gap + 1),
            Pitch->GetAttachParent() == Lift);
        TestTrue(*FString::Printf(TEXT("Gap %d frame is centred for equal compact press clearance"), Gap + 1),
            Root->GetRelativeLocation().Equals(
                FVector(0.0f, 1157.188f + Gap * 1007.0f, 109.0f), 0.01f));
        TestTrue(*FString::Printf(TEXT("Gap %d lift mover is movable"), Gap + 1),
            Lift->Mobility == EComponentMobility::Movable);
        TestTrue(*FString::Printf(TEXT("Gap %d pitch mover is movable"), Gap + 1),
            Pitch->Mobility == EComponentMobility::Movable);
        TestTrue(*FString::Printf(TEXT("Gap %d lift is assembled at the authored idle origin"), Gap + 1),
            Lift->GetRelativeLocation().IsNearlyZero(0.01f));
        TestTrue(*FString::Printf(TEXT("Gap %d pitch is assembled at the authored idle origin"), Gap + 1),
            Pitch->GetRelativeLocation().IsNearlyZero(0.01f));
        FBox ProductionBounds(ForceInit);
        for (int32 PartIndex = 0; PartIndex < UE_ARRAY_COUNT(TransferPartNames); ++PartIndex)
        {
            const TCHAR* Part = TransferPartNames[PartIndex];
            UStaticMeshComponent* TransferPart = Cast<UStaticMeshComponent>(FindScene(
                FName(*FString::Printf(TEXT("PTA_ApprovedTransfer%02d_%s"), Gap + 1, Part))));
            TestNotNull(*FString::Printf(TEXT("Gap %d %s exists"), Gap + 1, Part), TransferPart);
            if (TransferPart && TransferPart->GetStaticMesh())
            {
                const FString ExpectedPath = FString::Printf(TEXT("/Game/LineBoss/Developer/Validation/PressTrains/SegmentedTransferRuntime_v747/Cairnwell_InterPressTransfer_Runtime_v746/StaticMeshes/%s.%s"),
                    TransferAssetNames[PartIndex], TransferAssetNames[PartIndex]);
                TestEqual(*FString::Printf(TEXT("Gap %d %s uses accepted v763 asset"), Gap + 1, Part),
                    TransferPart->GetStaticMesh()->GetPathName(), ExpectedPath);
                TestTrue(*FString::Printf(TEXT("Gap %d %s keeps its shared authored origin"), Gap + 1, Part),
                    TransferPart->GetRelativeLocation().IsNearlyZero(0.01f));
                TestTrue(*FString::Printf(TEXT("Gap %d %s is rebased onto local +Y flow"), Gap + 1, Part),
                    FMath::IsNearlyEqual(TransferPart->GetRelativeRotation().Yaw, 90.0f, 0.01f));
                TestTrue(*FString::Printf(TEXT("Gap %d %s uses the owner-approved middle uniform scale"), Gap + 1, Part),
                    TransferPart->GetRelativeScale3D().Equals(FVector(2.0f), 0.001f));
                ProductionBounds += TransferPart->GetStaticMesh()->GetBoundingBox().TransformBy(
                    TransferPart->GetRelativeTransform());
                TestTrue(*FString::Printf(TEXT("Gap %d %s follows the correct assembly parent"), Gap + 1, Part),
                    TransferPart->GetAttachParent() == (PartIndex == 0 ? Root : Pitch));
                if (PartIndex > 0)
                    TestTrue(*FString::Printf(TEXT("Gap %d %s is movable"), Gap + 1, Part),
                        TransferPart->Mobility == EComponentMobility::Movable);
                if (PartIndex == 3) CupArrays.Add(TransferPart);
            }
        }
        if (Gap == 0 && ProductionBounds.IsValid)
        {
            const FVector ProductionSize = ProductionBounds.GetSize();
            TestTrue(TEXT("Production traverse stays near 2.11 m across the line"),
                FMath::IsNearlyEqual(ProductionSize.X, 211.0f, 1.0f));
            TestTrue(TEXT("Production traverse stays near 4.00 m along the press gap"),
                FMath::IsNearlyEqual(ProductionSize.Y, 399.97f, 1.0f));
            TestTrue(TEXT("Production traverse stays near 2.15 m high"),
                FMath::IsNearlyEqual(ProductionSize.Z, 215.05f, 1.0f));
            TestTrue(TEXT("Production traverse remains floor seated at middle size"),
                FMath::IsNearlyEqual(Root->GetRelativeLocation().Z + ProductionBounds.Min.Z, 0.3f, 1.0f));
        }
        GapRoots.Add(Root);
        LiftMovers.Add(Lift);
        PitchMovers.Add(Pitch);
        Frames.Add(Frame);
        FrameRestTransforms.Add(Frame->GetRelativeTransform());
    }

    TestEqual(TEXT("All four approved inter-press transfer roots are present"), GapRoots.Num(), 4);
    TestEqual(TEXT("All four approved inter-press transfer lift movers are present"), LiftMovers.Num(), 4);
    TestEqual(TEXT("All four approved inter-press transfer pitch movers are present"), PitchMovers.Num(), 4);
    TestEqual(TEXT("All four suction arrays are present for throat-to-throat transfer"), CupArrays.Num(), 4);
    if (GapRoots.Num() != 4 || LiftMovers.Num() != 4 || PitchMovers.Num() != 4
        || Frames.Num() != 4 || CupArrays.Num() != 4 || PressShells.Num() != 5)
    {
        World->DestroyWorld(false);
        return false;
    }

    for (int32 Gap = 0; Gap < 4; ++Gap)
    {
        UStaticMeshComponent* UpstreamShell = PressShells[Gap];
        UStaticMeshComponent* DownstreamShell = PressShells[Gap + 1];
        UStaticMeshComponent* FrameMesh = Cast<UStaticMeshComponent>(Frames[Gap]);
        UStaticMeshComponent* CupMesh = CupArrays[Gap];
        if (!UpstreamShell || !DownstreamShell || !FrameMesh || !CupMesh
            || !UpstreamShell->GetStaticMesh() || !DownstreamShell->GetStaticMesh()
            || !FrameMesh->GetStaticMesh() || !CupMesh->GetStaticMesh()) continue;

        const auto BoundsInTrain = [Train](UStaticMeshComponent* Component)
        {
            const FTransform ComponentToTrain = Component->GetComponentTransform()
                .GetRelativeTransform(Train->GetActorTransform());
            return Component->GetStaticMesh()->GetBoundingBox().TransformBy(ComponentToTrain);
        };
        const FBox UpstreamBounds = BoundsInTrain(UpstreamShell);
        const FBox DownstreamBounds = BoundsInTrain(DownstreamShell);
        FBox TraverseBounds(ForceInit);
        for (const TCHAR* Part : TransferPartNames)
        {
            if (UStaticMeshComponent* TransferPart = Cast<UStaticMeshComponent>(FindScene(
                FName(*FString::Printf(TEXT("PTA_ApprovedTransfer%02d_%s"), Gap + 1, Part)))))
            {
                if (TransferPart->GetStaticMesh()) TraverseBounds += BoundsInTrain(TransferPart);
            }
        }
        const float UpstreamClearance = TraverseBounds.Min.Y - UpstreamBounds.Max.Y;
        const float DownstreamClearance = DownstreamBounds.Min.Y - TraverseBounds.Max.Y;
        TestTrue(*FString::Printf(TEXT("Gap %d keeps about 25 cm after the upstream shell (%.3f cm; shell max %.3f, traverse min %.3f)"),
            Gap + 1, UpstreamClearance, UpstreamBounds.Max.Y, TraverseBounds.Min.Y),
            FMath::IsNearlyEqual(UpstreamClearance, 25.149f, 0.05f));
        TestTrue(*FString::Printf(TEXT("Gap %d keeps about 25 cm before the downstream shell (%.3f cm; traverse max %.3f, shell min %.3f)"),
            Gap + 1, DownstreamClearance, TraverseBounds.Max.Y, DownstreamBounds.Min.Y),
            FMath::IsNearlyEqual(DownstreamClearance, 25.149f, 0.05f));

        const FVector CupCentreInPitch = CupMesh->GetRelativeTransform().TransformPosition(
            CupMesh->GetStaticMesh()->GetBoundingBox().GetCenter());
        const float IdleCupCentreY = GapRoots[Gap]->GetRelativeLocation().Y
            + CupCentreInPitch.Y;
        TestTrue(*FString::Printf(TEXT("Gap %d suction tooling is stored inside its fixed frame"), Gap + 1),
            FMath::Abs(IdleCupCentreY - GapRoots[Gap]->GetRelativeLocation().Y) < 30.0f);
        TestTrue(*FString::Printf(TEXT("Gap %d moving tooling shares the frame origin at idle"), Gap + 1),
            PitchMovers[Gap]->GetComponentTransform().Equals(
                GapRoots[Gap]->GetComponentTransform(), 0.01f));
    }

    TestTrue(TEXT("Transfer hierarchy proof selects an approved panel recipe and installed die"),
        ConfigureHealthyTrainA(Train));
    TestTrue(TEXT("Transfer hierarchy proof accepts an identified blank"),
        Train->QueueReservedBlank(TEXT("RES-TRANSFER-0001"), TEXT("PR010-BLANK-TRANSFER-0001")));
    TestTrue(TEXT("Transfer hierarchy proof powers on"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::PowerOn, TrainAControlRoomSource, TrainAControlRoomAuthority));
    TestTrue(TEXT("Transfer hierarchy proof starts"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::Start, TrainAControlRoomSource, TrainAControlRoomAuthority));

    const float TransferSourceContactSeconds[] = {1.5336f, 2.4936f, 3.4536f, 4.4136f};
    const float TransferMidpointsSeconds[] = {1.62f, 2.58f, 3.54f, 4.50f};
    const float TransferDestinationContactSeconds[] = {1.7064f, 2.6664f, 3.6264f, 4.5864f};
    const float TransferEndSeconds[] = {1.80f, 2.76f, 3.72f, 4.68f};
    float PreviousSeconds = 0.0f;
    for (int32 ActiveGap = 0; ActiveGap < 4; ++ActiveGap)
    {
        Train->Tick(TransferSourceContactSeconds[ActiveGap] - PreviousSeconds);
        PreviousSeconds = TransferSourceContactSeconds[ActiveGap];
        for (int32 Gap = 0; Gap < 4; ++Gap)
        {
            const float ExpectedPitch = Gap == ActiveGap ? -527.413f : 0.0f;
            const float ExpectedLift = Gap == ActiveGap ? 201.923f : 0.0f;
            TestTrue(*FString::Printf(TEXT("Gap %d reaches the source independently during transfer %d"), Gap + 1, ActiveGap + 1),
                FMath::IsNearlyEqual(PitchMovers[Gap]->GetRelativeLocation().Y, ExpectedPitch, 0.2f));
            TestTrue(*FString::Printf(TEXT("Gap %d reaches source contact height during transfer %d"), Gap + 1, ActiveGap + 1),
                FMath::IsNearlyEqual(LiftMovers[Gap]->GetRelativeLocation().Z, ExpectedLift, 0.2f));
            TestTrue(*FString::Printf(TEXT("Gap %d fixed frame never follows the shuttle"), Gap + 1),
                Frames[Gap]->GetRelativeTransform().Equals(FrameRestTransforms[Gap], 0.01f));
        }
        const FVector CupCentreInPitch = CupArrays[ActiveGap]->GetRelativeTransform().TransformPosition(
            CupArrays[ActiveGap]->GetStaticMesh()->GetBoundingBox().GetCenter());
        const FBox CupBoundsInPitch = CupArrays[ActiveGap]->GetStaticMesh()->GetBoundingBox().TransformBy(
            CupArrays[ActiveGap]->GetRelativeTransform());
        const float SourceCupCentreY = GapRoots[ActiveGap]->GetRelativeLocation().Y
            + PitchMovers[ActiveGap]->GetRelativeLocation().Y + CupCentreInPitch.Y;
        const float SourceContactZ = GapRoots[ActiveGap]->GetRelativeLocation().Z
            + LiftMovers[ActiveGap]->GetRelativeLocation().Z + CupBoundsInPitch.Min.Z;
        TestTrue(*FString::Printf(TEXT("Gap %d suction centre enters the upstream throat"), ActiveGap + 1),
            FMath::IsNearlyEqual(SourceCupCentreY, 654.0f + ActiveGap * 1007.0f, 0.2f));
        TestTrue(*FString::Printf(TEXT("Gap %d source pickup reaches the sheet datum"), ActiveGap + 1),
            FMath::IsNearlyEqual(SourceContactZ, 202.221f, 0.2f));

        Train->Tick(TransferMidpointsSeconds[ActiveGap] - PreviousSeconds);
        PreviousSeconds = TransferMidpointsSeconds[ActiveGap];
        TestTrue(*FString::Printf(TEXT("Gap %d traverses through the raised midpoint"), ActiveGap + 1),
            FMath::IsNearlyEqual(PitchMovers[ActiveGap]->GetRelativeLocation().Y, -23.913f, 0.2f));
        TestTrue(*FString::Printf(TEXT("Gap %d keeps the blank clear at midpoint"), ActiveGap + 1),
            FMath::IsNearlyEqual(LiftMovers[ActiveGap]->GetRelativeLocation().Z, 261.923f, 0.2f));

        Train->Tick(TransferDestinationContactSeconds[ActiveGap] - PreviousSeconds);
        PreviousSeconds = TransferDestinationContactSeconds[ActiveGap];
        TestTrue(*FString::Printf(TEXT("Gap %d reaches the next press at full pitch"), ActiveGap + 1),
            FMath::IsNearlyEqual(PitchMovers[ActiveGap]->GetRelativeLocation().Y, 479.587f, 0.2f));
        TestTrue(*FString::Printf(TEXT("Gap %d lowers smoothly for handoff"), ActiveGap + 1),
            FMath::IsNearlyEqual(LiftMovers[ActiveGap]->GetRelativeLocation().Z, 201.923f, 0.2f));
        const float DestinationCupCentreY = GapRoots[ActiveGap]->GetRelativeLocation().Y
            + PitchMovers[ActiveGap]->GetRelativeLocation().Y + CupCentreInPitch.Y;
        const float DestinationContactZ = GapRoots[ActiveGap]->GetRelativeLocation().Z
            + LiftMovers[ActiveGap]->GetRelativeLocation().Z + CupBoundsInPitch.Min.Z;
        TestTrue(*FString::Printf(TEXT("Gap %d suction centre reaches the downstream throat"), ActiveGap + 1),
            FMath::IsNearlyEqual(DestinationCupCentreY,
                654.0f + (ActiveGap + 1) * 1007.0f, 0.2f));
        TestTrue(*FString::Printf(TEXT("Gap %d destination handoff reaches the sheet datum"), ActiveGap + 1),
            FMath::IsNearlyEqual(DestinationContactZ, 202.221f, 0.2f));

        Train->Tick(TransferEndSeconds[ActiveGap] - PreviousSeconds);
        PreviousSeconds = TransferEndSeconds[ActiveGap];
        TestTrue(*FString::Printf(TEXT("Gap %d pitch fully reassembles after handoff"), ActiveGap + 1),
            PitchMovers[ActiveGap]->GetRelativeLocation().IsNearlyZero(0.01f));
        TestTrue(*FString::Printf(TEXT("Gap %d lift fully reassembles after handoff"), ActiveGap + 1),
            LiftMovers[ActiveGap]->GetRelativeLocation().IsNearlyZero(0.01f));
    }

    for (int32 Gap = 0; Gap < 4; ++Gap)
    {
        TestTrue(*FString::Printf(TEXT("Gap %d pitch returns home without drift"), Gap + 1),
            PitchMovers[Gap]->GetRelativeLocation().IsNearlyZero(0.01f));
        TestTrue(*FString::Printf(TEXT("Gap %d lift returns home without drift"), Gap + 1),
            LiftMovers[Gap]->GetRelativeLocation().IsNearlyZero(0.01f));
    }

    World->DestroyWorld(false);
    return true;
}

bool FLBPressTrainAFeedBlankPresentationTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_PressTrainA_FeedBlankPresentation"));
    ALBPressTrainAStation* Train = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    TestNotNull(TEXT("Feed-blank presentation train spawns"), Train);
    if (!World || !Train)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TArray<USceneComponent*> SceneComponents;
    Train->GetComponents<USceneComponent>(SceneComponents);
    const auto FindScene = [&SceneComponents](const FName Name) -> USceneComponent*
    {
        for (USceneComponent* Component : SceneComponents)
            if (Component && Component->GetFName() == Name) return Component;
        return nullptr;
    };

    USceneComponent* DestackMover = FindScene(TEXT("PTA_DestackLiftMover"));
    USceneComponent* FormedPanelMover = FindScene(TEXT("PTA_FormedPanelMover"));
    UStaticMeshComponent* FeedBlank = Train->GetDestackFeedBlankVisualComponent();
    TestNotNull(TEXT("Native S01 destack mover exists"), DestackMover);
    TestNotNull(TEXT("Native flat feed-blank component exists"), FeedBlank);
    TestNotNull(TEXT("Formed-panel mover remains available for the approved car later"), FormedPanelMover);
    if (!DestackMover || !FeedBlank || !FormedPanelMover)
    {
        World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("Flat feed blank is a direct child of the S01 lift mover"),
        FeedBlank->GetAttachParent() == DestackMover);
    TestNotNull(TEXT("Flat feed blank has its audited mesh"), FeedBlank->GetStaticMesh().Get());
    if (FeedBlank->GetStaticMesh())
    {
        TestEqual(TEXT("S01 uses the car-independent separated blank asset"),
            FeedBlank->GetStaticMesh()->GetPathName(),
            FString(TEXT("/Game/LineBoss/Candidates/PressTrains/TrainA/Fabrication_v030/Imported/PTA_S01_SeparatedFeedBlank_v002_Mesh.PTA_S01_SeparatedFeedBlank_v002_Mesh")));
        const FVector PresentedSize = FeedBlank->GetStaticMesh()->GetBoundingBox().GetSize()
            * FeedBlank->GetRelativeScale3D();
        TestTrue(TEXT("Presented blank retains its audited 3.30 m width"),
            FMath::IsNearlyEqual(PresentedSize.X, 330.0f, 0.2f));
        TestTrue(TEXT("Presented blank retains its audited 1.45 m feed length"),
            FMath::IsNearlyEqual(PresentedSize.Y, 145.0f, 0.2f));
    }
    TestTrue(TEXT("Feed blank rests 1.20 m below the verified press datum"),
        FMath::IsNearlyEqual(FeedBlank->GetRelativeLocation().Z, 82.221f, 0.001f));
    TestTrue(TEXT("No formed/car-specific mesh is invented before the 2040 is approved"),
        FormedPanelMover->GetNumChildrenComponents() == 0);

    TestTrue(TEXT("Complete modular machine enables with the feed blank outside its fixed count"),
        Train->EnableCompletedRuntimeVisual());
    TestEqual(TEXT("Feed material does not change the 105 fixed machine-module contract"),
        Train->GetApprovedModularVisualCount(), 105);
    Train->Tick(0.0f);
    TestFalse(TEXT("An empty S01 does not display a phantom sheet"), FeedBlank->IsVisible());
    TestTrue(TEXT("An empty S01 keeps the sheet hidden in game"), FeedBlank->bHiddenInGame);

    TestTrue(TEXT("Feed-blank proof selects an approved panel recipe and installed die"),
        ConfigureHealthyTrainA(Train));
    TestTrue(TEXT("Identified material queues at the S01 input"),
        Train->QueueReservedBlank(TEXT("RES-FEED-BLANK-0001"), TEXT("BLANK-FEED-0001")));
    Train->Tick(0.0f);
    TestTrue(TEXT("A queued identified blank is visible at the resting destacker"),
        FeedBlank->IsVisible() && !FeedBlank->bHiddenInGame);
    TestTrue(TEXT("Queued sheet holds the lift at its rest pose"),
        DestackMover->GetRelativeLocation().IsNearlyZero(0.001f));

    TestTrue(TEXT("Feed-blank proof powers on"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::PowerOn,
            TrainAControlRoomSource, TrainAControlRoomAuthority));
    TestTrue(TEXT("Feed-blank proof starts"),
        Train->ExecuteRemoteCommand(ELBPressTrainACommand::Start,
            TrainAControlRoomSource, TrainAControlRoomAuthority));
    Train->Tick(0.24f); // 10 spm => progress 0.04, the peak of the 0.00-0.08 destack stroke.
    TestTrue(TEXT("The in-process blank remains visible while S01 lifts it"),
        FeedBlank->IsVisible() && !FeedBlank->bHiddenInGame);
    TestTrue(TEXT("S01 reaches its full 1.20 m lift at mid-destack"),
        FMath::IsNearlyEqual(DestackMover->GetRelativeLocation().Z, 120.0f, 0.01f));
    TestTrue(TEXT("The lifted sheet centre lands on the 2.02221 m transfer datum"),
        FMath::IsNearlyEqual(FeedBlank->GetComponentLocation().Z, 202.221f, 0.01f));

    Train->Tick(0.36f); // progress 0.10: current blank has left S01.
    TestFalse(TEXT("The native feed sheet hides after its blank transfers downstream"),
        FeedBlank->IsVisible());
    TestTrue(TEXT("Destacker returns home after transfer"),
        DestackMover->GetRelativeLocation().IsNearlyZero(0.001f));

    TestTrue(TEXT("A second reserved blank can wait while the first is in process"),
        Train->QueueReservedBlank(TEXT("RES-FEED-BLANK-0002"), TEXT("BLANK-FEED-0002")));
    Train->Tick(0.0f);
    TestTrue(TEXT("The next queued sheet is visible at rest without impersonating the downstream blank"),
        FeedBlank->IsVisible() && DestackMover->GetRelativeLocation().IsNearlyZero(0.001f));
    TestTrue(TEXT("Formed-panel art remains deliberately deferred throughout the proof"),
        FormedPanelMover->GetNumChildrenComponents() == 0);

    World->DestroyWorld(false);
    return true;
}

#endif
