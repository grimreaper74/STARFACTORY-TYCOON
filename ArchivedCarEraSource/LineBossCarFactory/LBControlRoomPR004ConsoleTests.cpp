#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBControlRoomPR004Console.h"
#include "LBControlRoomPawn.h"
#include "LBPR004Station.h"
#include "LBPressShopSaveGame.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBControlRoomPR004ConsoleAuthorityTest,
    "LineBoss.ControlRoom.PR004Console.AuthorityBinding",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBControlRoomPR004ConsoleAuthorityTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LBControlRoomConsoleTestWorld"));
    TestNotNull(TEXT("Transient game world created"), World);
    if (!World)
    {
        return false;
    }

    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());
    ALBControlRoomPR004Console* Console = World->SpawnActor<ALBControlRoomPR004Console>();
    World->BeginPlay();
    if (Console && !Console->HasActorBegunPlay())
    {
        Console->DispatchBeginPlay();
    }

    TestNotNull(TEXT("PR-004 control-room console spawned"), Console);
    TestTrue(TEXT("Console binds or creates authoritative station"), Console && Console->BindAvailableStation());
    ALBPR004Station* Station = Console ? Console->GetBoundStation() : nullptr;
    TestNotNull(TEXT("Bound PR-004 station exists"), Station);
    if (Station)
    {
        TestEqual(TEXT("Configured packaged coil identity"), Station->GetCurrentCoilId(), FString(TEXT("MCX-U-MCR-PR004-001")));
        TArray<FText> BlockingReasons;
        TestTrue(TEXT("Remote unpackage action is authority-permitted"), Station->CanUnpackageCoil(BlockingReasons));

        ALBControlRoomPawn* Pawn = World->SpawnActor<ALBControlRoomPawn>(
            ALBControlRoomPawn::StaticClass(), FVector(-100.0f, 0.0f, 0.0f), FRotator::ZeroRotator);
        TestNotNull(TEXT("Seated interaction pawn exists"), Pawn);
        World->UpdateWorldComponents(true, false);
        FHitResult ScreenHit;
        FCollisionQueryParams ScreenQuery(TEXT("PR004ControlRoomScreenTrace"), true);
        if (Pawn)
        {
            ScreenQuery.AddIgnoredActor(Pawn);
        }
        TestTrue(TEXT("Visibility trace hits the PR-004 screen interaction surface"),
            World->LineTraceSingleByChannel(
                ScreenHit, FVector(-100.0f, 0.0f, 0.0f), FVector(100.0f, 0.0f, 0.0f),
                ECC_Visibility, ScreenQuery));
        TestTrue(TEXT("Screen trace resolves to the control-room console actor"),
            ScreenHit.GetActor() == Console);
        TestTrue(TEXT("Seated pawn routes the screen click to the guarded authority action"),
            Pawn && Pawn->InteractWithActor(ScreenHit.GetActor()));
        TestTrue(TEXT("Console action removes authoritative packaging state"), Station->IsCoilUnpackaged());
        TestEqual(TEXT("Console action advances PR-004 to handoff"),
            Station->GetProcessState(), ELBPR004State::ReadyForHandoff);

        FLBPR004SaveState Saved;
        TestTrue(TEXT("Control-room-mutated PR-004 state captures coherently"), Station->GetStableSaveState(Saved));
        ULBPressShopSaveGame* SaveRoot = NewObject<ULBPressShopSaveGame>();
        TestNotNull(TEXT("Versioned Press Shop save root exists"), SaveRoot);
        SaveRoot->PR004 = Saved;
        TArray<uint8> SaveBytes;
        TestTrue(TEXT("Control-room-mutated Press Shop state serializes"),
            UGameplayStatics::SaveGameToMemory(SaveRoot, SaveBytes));
        ULBPressShopSaveGame* LoadedRoot = Cast<ULBPressShopSaveGame>(
            UGameplayStatics::LoadGameFromMemory(SaveBytes));
        TestNotNull(TEXT("Serialized control-room state loads through the game save system"), LoadedRoot);
        ALBPR004Station* Reloaded = World->SpawnActor<ALBPR004Station>();
        TestNotNull(TEXT("Fresh PR-004 restore target exists"), Reloaded);
        TestTrue(TEXT("Fresh station restores the control-room-mutated save"),
            Reloaded && Reloaded->RestoreSaveState(LoadedRoot ? LoadedRoot->PR004 : Saved));
        TestTrue(TEXT("Restored authority remains unpackaged"), Reloaded && Reloaded->IsCoilUnpackaged());
        TestEqual(TEXT("Restored authority remains ready for handoff"),
            Reloaded ? Reloaded->GetProcessState() : ELBPR004State::Fault,
            ELBPR004State::ReadyForHandoff);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
