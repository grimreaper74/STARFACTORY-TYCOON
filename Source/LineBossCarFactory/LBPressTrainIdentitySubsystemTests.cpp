#include "LBPressTrainIdentitySubsystem.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "LBPressTrainAStation.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressShopSaveGame.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPressTrainIdentityAllocationTest,
    "LineBoss.PressShop.PressTrains.Identity.NextAvailablePersistence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPressTrainIdentityAllocationTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PressTrainIdentity"));
    ULBPressTrainIdentitySubsystem* Registry = World ? World->GetSubsystem<ULBPressTrainIdentitySubsystem>() : nullptr;
    if (!Registry && World) Registry = NewObject<ULBPressTrainIdentitySubsystem>(World);
    ALBPressTrainAStation* A = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    ALBPressTrainAStation* B = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    ALBPressTrainAStation* C = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    ALBPressTrainAStation* D = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    ALBPressTrainAStation* BeyondDesignedCapacity = World ? World->SpawnActor<ALBPressTrainAStation>() : nullptr;
    TestNotNull(TEXT("Identity registry exists"), Registry);
    TestNotNull(TEXT("Three player-placed trains spawn"), A);
    TestNotNull(TEXT("Second player-placed train spawns"), B);
    TestNotNull(TEXT("Third player-placed train spawns"), C);
    TestNotNull(TEXT("Fourth player-placed train spawns"), D);
    TestNotNull(TEXT("Capacity probe train spawns"), BeyondDesignedCapacity);
    if (!Registry || !A || !B || !C || !D || !BeyondDesignedCapacity)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("First train registers"), Registry->RegisterTrain(A));
    TestTrue(TEXT("Second train registers"), Registry->RegisterTrain(B));
    TestTrue(TEXT("Third train registers"), Registry->RegisterTrain(C));
    TestTrue(TEXT("Fourth designed train registers"), Registry->RegisterTrain(D));
    TestFalse(TEXT("A fifth train cannot exceed the authored A-D factory"), Registry->RegisterTrain(BeyondDesignedCapacity));
    TestEqual(TEXT("First available designation is A"), A->GetTrainId(), FName(TEXT("TRAIN_A")));
    TestEqual(TEXT("Duplicate default advances to B"), B->GetTrainId(), FName(TEXT("TRAIN_B")));
    TestEqual(TEXT("Next duplicate default advances to C"), C->GetTrainId(), FName(TEXT("TRAIN_C")));
    TestEqual(TEXT("Fourth duplicate default advances to D"), D->GetTrainId(), FName(TEXT("TRAIN_D")));
    TestEqual(TEXT("Station IDs derive from stable train designation"), C->GetStationId(7), FName(TEXT("C-S07")));
    Registry->ReleaseTrain(D);
    D->Destroy();
    BeyondDesignedCapacity->Destroy();

    const FGuid AGuid = A->GetPersistentTrainGuid();
    const FGuid CGuid = C->GetPersistentTrainGuid();
    Registry->ReleaseTrain(B);
    ALBPressTrainAStation* Replacement = World->SpawnActor<ALBPressTrainAStation>();
    TestTrue(TEXT("Replacement train registers"), Registry->RegisterTrain(Replacement));
    TestEqual(TEXT("Freed B designation is reused"), Replacement->GetTrainId(), FName(TEXT("TRAIN_B")));
    TestEqual(TEXT("Surviving A is never renumbered"), A->GetTrainId(), FName(TEXT("TRAIN_A")));
    TestEqual(TEXT("Surviving C is never renumbered"), C->GetTrainId(), FName(TEXT("TRAIN_C")));
    TestEqual(TEXT("Surviving A GUID is immutable"), A->GetPersistentTrainGuid(), AGuid);
    TestEqual(TEXT("Surviving C GUID is immutable"), C->GetPersistentTrainGuid(), CGuid);

    const FLBPressTrainASaveState SavedC = C->CaptureSaveState();
    Registry->ReleaseTrain(C);
    ALBPressTrainAStation* ReloadedC = World->SpawnActor<ALBPressTrainAStation>();
    TestTrue(TEXT("Exact saved identity restores"), Registry->RestoreTrainIdentity(ReloadedC,
        SavedC.PersistentTrainGuid, SavedC.TrainId, TEXT("ROOF PANEL EXPRESS")));
    TestEqual(TEXT("Reload preserves immutable GUID"), ReloadedC->GetPersistentTrainGuid(), CGuid);
    TestEqual(TEXT("Reload preserves C designation"), ReloadedC->GetTrainId(), FName(TEXT("TRAIN_C")));
    TestEqual(TEXT("Custom player display name persists independently"),
        ReloadedC->GetTrainDisplayName(), FString(TEXT("ROOF PANEL EXPRESS")));
    TestTrue(TEXT("GUID lookup resolves the restored authority"),
        Registry->FindTrainByPersistentGuid(CGuid) == ReloadedC);

    // Remove superseded actors so the exact world-level campaign set is A, replacement B and reloaded C.
    B->Destroy();
    C->Destroy();
    ULBPressShopSaveGame* Campaign = NewObject<ULBPressShopSaveGame>();
    TestTrue(TEXT("All placed train authorities capture into one campaign root"), Registry->CaptureAllTrains(Campaign));
    TestEqual(TEXT("Campaign captures the exact three-train set"), Campaign->PressTrains.Num(), 3);
    TestEqual(TEXT("Campaign train records are deterministic A-first"),
        Campaign->PressTrains[0].TrainId, FName(TEXT("TRAIN_A")));
    A->SetPressLoad(99.0f);
    const FTransform SavedATransform = Campaign->PressTrains[0].WorldTransform;
    A->SetActorLocation(FVector(12345.0f, 54321.0f, 900.0f));
    TestTrue(TEXT("Exact identity-matched campaign set restores"), Registry->RestoreAllTrains(Campaign));
    TestTrue(TEXT("Campaign restore returns Train A process state"),
        FMath::IsNearlyEqual(A->GetHMIStatus().PressLoadPercent, Campaign->PressTrains[0].PressLoadPercent));
    TestTrue(TEXT("Campaign restore returns Train A to its saved player placement"),
        A->GetActorTransform().Equals(SavedATransform, 0.01f));

    ALBPressTrainAStation* Unexpected = World->SpawnActor<ALBPressTrainAStation>();
    TestTrue(TEXT("Unexpected train registers for fail-closed proof"), Registry->RegisterTrain(Unexpected));
    TestTrue(TEXT("Campaign restore ignores an unrelated authored train outside the managed set"),
        Registry->RestoreAllTrains(Campaign));
    TestTrue(TEXT("Unrelated authored train remains alive after managed-set restore"), IsValid(Unexpected));

    // Use a fresh world so the builder envelope test is independent of the allocation fixtures above.
    UWorld* BuilderWorld = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_PressTrainBuilder"));
    ULBPressTrainIdentitySubsystem* Builder = BuilderWorld
        ? BuilderWorld->GetSubsystem<ULBPressTrainIdentitySubsystem>() : nullptr;
    if (!Builder && BuilderWorld) Builder = NewObject<ULBPressTrainIdentitySubsystem>(BuilderWorld);
    ALBPressShopBuildAuthority* BuildAuthority = BuilderWorld
        ? BuilderWorld->SpawnActor<ALBPressShopBuildAuthority>() : nullptr;
    if (BuildAuthority)
    {
        FLBPressShopBuildBay Bay;
        Bay.BayId = TEXT("TEST_BAY");
        Bay.Centre = FVector(1100.0f, 2892.0f, 475.0f);
        Bay.HalfExtent = FVector(3000.0f, 3642.0f, 1000.0f);
        BuildAuthority->BuildBays.Add(Bay);
        FLBPressShopUtilitySpine Spine;
        Spine.SpineId = TEXT("TEST_UTILITY");
        Spine.Start = FVector(-1000.0f, 2892.0f, 0.0f);
        Spine.End = FVector(4000.0f, 2892.0f, 0.0f);
        Spine.MaximumConnectionDistanceCm = 1000.0f;
        BuildAuthority->UtilitySpines.Add(Spine);
    }
    ALBPressTrainAStation* BuiltA = nullptr;
    ALBPressTrainAStation* BuiltB = nullptr;
    TestTrue(TEXT("Factory builder places an isolated Train A"), Builder && Builder->PlaceTrain(
        FTransform(FRotator::ZeroRotator, FVector::ZeroVector), TEXT("TRAIN A"), TEXT("LARGE OUTER PANELS"), BuiltA));
    TestTrue(TEXT("Player-built train enables the approved complete visual"),
        BuiltA && BuiltA->HasCompletedRuntimeVisual());
    TestEqual(TEXT("Player-built train contains the complete approved modular visual set"),
        BuiltA ? BuiltA->GetApprovedModularVisualCount() : 0, 105);
    FString PreviewReason;
    TestFalse(TEXT("Read-only preview rejects the same protected-envelope overlap"), Builder && Builder->CanPlaceTrain(
        FTransform(FRotator::ZeroRotator, FVector(500.0f, 0.0f, 0.0f)), PreviewReason));
    TestTrue(TEXT("Invalid preview gives an actionable overlap reason"), PreviewReason.Contains(TEXT("OVERLAPS TRAIN_A")));
    TestTrue(TEXT("Read-only preview accepts the next separated bay"), Builder && Builder->CanPlaceTrain(
        FTransform(FRotator::ZeroRotator, FVector(2200.0f, 0.0f, 0.0f)), PreviewReason));
    TestTrue(TEXT("Valid preview reports verified build bay and utility reach"),
        PreviewReason.Contains(TEXT("TEST_BAY")) && PreviewReason.Contains(TEXT("TEST_UTILITY")));
    TestFalse(TEXT("Preview rejects a complete footprint outside the authorised bay"), Builder && Builder->CanPlaceTrain(
        FTransform(FRotator::ZeroRotator, FVector(7000.0f, 0.0f, 0.0f)), PreviewReason));
    TestTrue(TEXT("Out-of-bay rejection is explicit"), PreviewReason.Contains(TEXT("OUTSIDE")));
    FLBPressShopProtectedArea Aisle;
    Aisle.AreaId = TEXT("TEST_PEDESTRIAN_AISLE");
    Aisle.Centre = FVector(2200.0f, 2892.0f, 400.0f);
    Aisle.HalfExtent = FVector(100.0f, 3642.0f, 500.0f);
    if (BuildAuthority) BuildAuthority->ProtectedAreas.Add(Aisle);
    TestFalse(TEXT("Preview rejects a protected aisle intersection"), Builder && Builder->CanPlaceTrain(
        FTransform(FRotator::ZeroRotator, FVector(2200.0f, 0.0f, 0.0f)), PreviewReason));
    TestTrue(TEXT("Protected-area rejection identifies the route"), PreviewReason.Contains(TEXT("TEST_PEDESTRIAN_AISLE")));
    if (BuildAuthority) BuildAuthority->ProtectedAreas.Reset();
    TArray<FLBPressShopUtilitySpine> SavedSpines;
    if (BuildAuthority)
    {
        SavedSpines = BuildAuthority->UtilitySpines;
        BuildAuthority->UtilitySpines.Reset();
    }
    TestFalse(TEXT("Preview fails closed when no utility authority is configured"), Builder && Builder->CanPlaceTrain(
        FTransform(FRotator::ZeroRotator, FVector(2200.0f, 0.0f, 0.0f)), PreviewReason));
    TestTrue(TEXT("Missing utility rejection is explicit"), PreviewReason.Contains(TEXT("UTILITY SPINE NOT CONFIGURED")));
    if (BuildAuthority) BuildAuthority->UtilitySpines = SavedSpines;
    ALBPressShopBuildAuthority* DuplicateAuthority = BuilderWorld
        ? BuilderWorld->SpawnActor<ALBPressShopBuildAuthority>() : nullptr;
    TestFalse(TEXT("Preview fails closed with ambiguous map authority"), Builder && Builder->CanPlaceTrain(
        FTransform(FRotator::ZeroRotator, FVector(2200.0f, 0.0f, 0.0f)), PreviewReason));
    TestTrue(TEXT("Duplicate authority rejection is explicit"), PreviewReason.Contains(TEXT("MULTIPLE")));
    if (DuplicateAuthority) DuplicateAuthority->Destroy();
    ALBPressTrainAStation* Overlap = nullptr;
    TestFalse(TEXT("Factory builder rejects overlapping protected train envelopes"), Builder && Builder->PlaceTrain(
        FTransform(FRotator::ZeroRotator, FVector(500.0f, 0.0f, 0.0f)), TEXT("OVERLAP"), TEXT("TEST"), Overlap));
    TestTrue(TEXT("Factory builder accepts a separated Train B"), Builder && Builder->PlaceTrain(
        FTransform(FRotator::ZeroRotator, FVector(2200.0f, 0.0f, 0.0f)), TEXT("FLOOR LINE"), TEXT("FLOORS / UNDERBODY"), BuiltB));
    TestEqual(TEXT("Builder uses next available B designation"), BuiltB ? BuiltB->GetTrainId() : NAME_None,
        FName(TEXT("TRAIN_B")));
    if (BuiltB) BuiltB->SetControlPower(true);
    TestFalse(TEXT("Powered train cannot be removed"), Builder && Builder->RemoveTrain(BuiltB));
    if (BuiltB) BuiltB->SetControlPower(false);
    TestTrue(TEXT("Isolated empty train can be removed"), Builder && Builder->RemoveTrain(BuiltB));
    ALBPressTrainAStation* ReusedB = nullptr;
    TestTrue(TEXT("Replacement placement succeeds after removal"), Builder && Builder->PlaceTrain(
        FTransform(FRotator::ZeroRotator, FVector(2200.0f, 0.0f, 0.0f)), TEXT("REPLACEMENT"), TEXT("FLOORS"), ReusedB));
    TestEqual(TEXT("Replacement reuses free B without renumbering A"),
        ReusedB ? ReusedB->GetTrainId() : NAME_None, FName(TEXT("TRAIN_B")));
    TestEqual(TEXT("Surviving builder train remains A"), BuiltA ? BuiltA->GetTrainId() : NAME_None,
        FName(TEXT("TRAIN_A")));
    if (BuilderWorld) BuilderWorld->DestroyWorld(false);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPressTrainColdWorldRestoreTest,
    "LineBoss.PressShop.PressTrains.Save.ColdWorldTransactionalRoundTrip",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPressTrainColdWorldRestoreTest::RunTest(const FString& Parameters)
{
    constexpr const TCHAR* Slot = TEXT("LB_AUTOMATION_PRESS_TRAINS_COLD_WORLD_V015");
    const auto CreatePlayingWorld = [](const TCHAR* Name)
    {
        UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, FName(Name));
        if (!World || !GEngine) return World;
        FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
        Context.SetCurrentWorld(World);
        World->InitializeActorsForPlay(FURL());
        World->BeginPlay();
        return World;
    };
    const auto DestroyPlayingWorld = [](UWorld* World)
    {
        if (!World) return;
        World->DestroyWorld(false);
        if (GEngine) GEngine->DestroyWorldContext(World);
    };

    UWorld* SourceWorld = CreatePlayingWorld(TEXT("LB_PressTrainColdSource"));
    ULBPressTrainIdentitySubsystem* SourceRegistry = SourceWorld
        ? SourceWorld->GetSubsystem<ULBPressTrainIdentitySubsystem>() : nullptr;
    ALBPressTrainAStation* SourceTrain = SourceWorld ? SourceWorld->SpawnActor<ALBPressTrainAStation>() : nullptr;
    TestNotNull(TEXT("Cold roundtrip source world exists"), SourceWorld);
    TestNotNull(TEXT("Source identity authority exists"), SourceRegistry);
    TestNotNull(TEXT("Source managed train spawns"), SourceTrain);
    if (!SourceWorld || !SourceRegistry || !SourceTrain)
    {
        DestroyPlayingWorld(SourceWorld);
        return false;
    }

    SourceTrain->SetActorTransform(FTransform(FRotator(0.0f, 90.0f, 0.0f),
        FVector(4321.0f, -876.0f, 25.0f)));
    TestTrue(TEXT("Source train accepts a vehicle-independent roof recipe"),
        SourceTrain->SetActiveProductionRecipe(TEXT("CAIRNWELL_2040"), TEXT("ROOF_PANEL"), TEXT("DIE_ROOF_2040")));
    SourceTrain->SetPressLoad(73.0f);
    SourceTrain->SetControlPower(true);
    TestTrue(TEXT("Source runtime queue contains a reserved blank"),
        SourceTrain->QueueReservedBlank(TEXT("RES-COLD-001"), TEXT("BLANK-COLD-001")));

    ULBPressShopSaveGame* Saved = NewObject<ULBPressShopSaveGame>();
    TestTrue(TEXT("Source managed set captures"), SourceRegistry->CaptureAllTrains(Saved));
    TestEqual(TEXT("Source save contains one train"), Saved->PressTrains.Num(), 1);
    if (Saved->PressTrains.Num() != 1)
    {
        DestroyPlayingWorld(SourceWorld);
        return false;
    }
    const FLBPressTrainASaveState Expected = Saved->PressTrains[0];

    TArray<uint8> Bytes;
    TestTrue(TEXT("Press-train save serializes to memory"), UGameplayStatics::SaveGameToMemory(Saved, Bytes));
    ULBPressShopSaveGame* MemoryLoaded = Cast<ULBPressShopSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes));
    TestNotNull(TEXT("Press-train save deserializes from memory"), MemoryLoaded);
    TestTrue(TEXT("Serialized save writes to a disk-style slot"), MemoryLoaded
        && UGameplayStatics::SaveGameToSlot(MemoryLoaded, Slot, 0));
    ULBPressShopSaveGame* DiskLoaded = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromSlot(Slot, 0));
    TestNotNull(TEXT("Disk-style train save reloads"), DiskLoaded);
    DestroyPlayingWorld(SourceWorld);
    if (!DiskLoaded)
    {
        UGameplayStatics::DeleteGameInSlot(Slot, 0);
        return false;
    }

    UWorld* TargetWorld = CreatePlayingWorld(TEXT("LB_PressTrainColdTarget"));
    ULBPressTrainIdentitySubsystem* TargetRegistry = TargetWorld
        ? TargetWorld->GetSubsystem<ULBPressTrainIdentitySubsystem>() : nullptr;
    ALBPressTrainAStation* UnrelatedAuthored = TargetWorld
        ? TargetWorld->SpawnActor<ALBPressTrainAStation>() : nullptr;
    const FGuid UnrelatedGuid = FGuid::NewGuid();
    TestTrue(TEXT("Unrelated authored fixture receives a non-conflicting D identity"),
        TargetRegistry && UnrelatedAuthored && TargetRegistry->RestoreTrainIdentity(
            UnrelatedAuthored, UnrelatedGuid, TEXT("TRAIN_D"), TEXT("AUTHORED TRAIN D")));
    TestTrue(TEXT("Fresh world respawns the serialized managed train"),
        TargetRegistry && TargetRegistry->RestoreAllTrains(DiskLoaded));

    ALBPressTrainAStation* Restored = TargetRegistry
        ? TargetRegistry->FindTrainByPersistentGuid(Expected.PersistentTrainGuid) : nullptr;
    TestNotNull(TEXT("Cold restore resolves the exact persistent GUID"), Restored);
    TestTrue(TEXT("Cold restore creates a different actor than the destroyed source"),
        Restored && Restored != SourceTrain);
    TestEqual(TEXT("Cold restore preserves stable designation"),
        Restored ? Restored->GetTrainId() : NAME_None, Expected.TrainId);
    TestTrue(TEXT("Cold restore preserves player placement"), Restored
        && Restored->GetActorTransform().Equals(Expected.WorldTransform, 0.01f));
    TestTrue(TEXT("Cold restore preserves recipe authority"), Restored
        && Restored->GetActiveVehicleModelId() == TEXT("CAIRNWELL_2040")
        && Restored->GetActivePanelTypeId() == TEXT("ROOF_PANEL")
        && Restored->GetActiveDieId() == TEXT("DIE_ROOF_2040"));
    TestTrue(TEXT("Cold restore preserves queued runtime material"), Restored
        && Restored->GetHMIStatus().PendingBlankCount == 1
        && Restored->GetHMIStatus().OldestPendingBlankId == TEXT("BLANK-COLD-001"));
    TestTrue(TEXT("Cold restore preserves process settings"), Restored
        && FMath::IsNearlyEqual(Restored->GetHMIStatus().PressLoadPercent, 73.0f));
    TestTrue(TEXT("Cold restore enables the approved complete presentation"), Restored
        && Restored->HasCompletedRuntimeVisual()
        && Restored->GetApprovedModularVisualCount() == 105);
    TestTrue(TEXT("Unrelated authored actor is preserved"), IsValid(UnrelatedAuthored)
        && UnrelatedAuthored->GetPersistentTrainGuid() == UnrelatedGuid
        && UnrelatedAuthored->GetTrainId() == TEXT("TRAIN_D"));

    if (Restored)
    {
        const FLBPressTrainASaveState BeforeRejectedRestore = Restored->CaptureSaveState();
        ULBPressShopSaveGame* Invalid = DuplicateObject<ULBPressShopSaveGame>(DiskLoaded, GetTransientPackage());
        Invalid->PressTrains[0].WorldTransform.SetScale3D(FVector::ZeroVector);
        TestFalse(TEXT("Invalid record is rejected before transaction commit"),
            TargetRegistry->RestoreAllTrains(Invalid));
        TestTrue(TEXT("Invalid restore keeps the previous managed actor"),
            TargetRegistry->FindTrainByPersistentGuid(Expected.PersistentTrainGuid) == Restored);
        TestTrue(TEXT("Invalid restore leaves previous transform unchanged"),
            Restored->GetActorTransform().Equals(BeforeRejectedRestore.WorldTransform, 0.01f));
        TestEqual(TEXT("Invalid restore leaves previous queue unchanged"),
            Restored->GetHMIStatus().PendingBlankCount, BeforeRejectedRestore.PendingBlankIds.Num());
    }

    ULBPressShopSaveGame* Empty = NewObject<ULBPressShopSaveGame>();
    Empty->PressTrains.Reset();
    TestTrue(TEXT("Validated empty train set restores successfully"),
        TargetRegistry && TargetRegistry->RestoreAllTrains(Empty));
    TestNull(TEXT("Empty set removes the previous managed train"),
        TargetRegistry ? TargetRegistry->FindTrainByPersistentGuid(Expected.PersistentTrainGuid) : nullptr);
    TestTrue(TEXT("Empty managed set still preserves unrelated authored actors"),
        IsValid(UnrelatedAuthored) && UnrelatedAuthored->GetPersistentTrainGuid() == UnrelatedGuid);
    ULBPressShopSaveGame* RecapturedEmpty = NewObject<ULBPressShopSaveGame>();
    TestTrue(TEXT("Recapture after empty restore remains an empty managed set"),
        TargetRegistry && TargetRegistry->CaptureAllTrains(RecapturedEmpty));
    TestEqual(TEXT("Unrelated authored actor is not adopted by an established campaign set"),
        RecapturedEmpty->PressTrains.Num(), 0);

    TestTrue(TEXT("Automation train slot is removed"), UGameplayStatics::DeleteGameInSlot(Slot, 0));
    DestroyPlayingWorld(TargetWorld);

    UWorld* EmptyWorld = CreatePlayingWorld(TEXT("LB_PressTrainEmptyCapture"));
    ULBPressTrainIdentitySubsystem* EmptyRegistry = EmptyWorld
        ? EmptyWorld->GetSubsystem<ULBPressTrainIdentitySubsystem>() : nullptr;
    ULBPressShopSaveGame* EmptyCaptured = NewObject<ULBPressShopSaveGame>();
    TestTrue(TEXT("A world with no train captures a valid empty set"),
        EmptyRegistry && EmptyRegistry->CaptureAllTrains(EmptyCaptured));
    TestEqual(TEXT("Empty capture contains zero records"), EmptyCaptured->PressTrains.Num(), 0);
    DestroyPlayingWorld(EmptyWorld);
    return true;
}

#endif
