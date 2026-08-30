#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBControlRoomGameMode.h"
#include "LBControlRoomHUD.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBControlRoomPawn.h"
#include "LBManagementPawn.h"
#include "LBPressShopBuildAuthority.h"
#include "Camera/CameraComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/InputSettings.h"
#include "GameFramework/PlayerController.h"
#include "InputCoreTypes.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBControlRoomStandingFirstPawnRuntimeTest,
    "LineBoss.ControlRoom.StandingFirstPawn.RuntimeConstraints",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBControlRoomStandingFirstPawnRuntimeTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LBControlRoomPawnTestWorld"));
    TestNotNull(TEXT("Transient game world created"), World);
    if (!World)
    {
        return false;
    }

    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    const FVector SeatLocation(0.0f, 82.0f, 88.0f);
    ALBControlRoomPawn* Pawn = World->SpawnActor<ALBControlRoomPawn>(
        ALBControlRoomPawn::StaticClass(), SeatLocation, FRotator::ZeroRotator);
    TestNotNull(TEXT("Standing-first control-room pawn spawned"), Pawn);
    APlayerController* PlayerController = World->SpawnActor<APlayerController>(
        APlayerController::StaticClass(), FVector::ZeroVector, FRotator::ZeroRotator);
    TestNotNull(TEXT("Transient player controller spawned"), PlayerController);
    if (PlayerController && Pawn)
    {
        PlayerController->Possess(Pawn);
    }
    World->BeginPlay();
    // Lightweight transient automation worlds do not always dispatch BeginPlay
    // to actors spawned between InitializeActorsForPlay and World::BeginPlay.
    if (Pawn && !Pawn->HasActorBegunPlay())
    {
        Pawn->DispatchBeginPlay();
    }

    if (Pawn)
    {
        const FVector ResolvedSeatLocation = Pawn->GetLockedSeatLocation();
        TestTrue(TEXT("Locked seat preserves the authored horizontal datum"),
            FMath::IsNearlyEqual(ResolvedSeatLocation.X, SeatLocation.X, 0.01f)
            && FMath::IsNearlyEqual(ResolvedSeatLocation.Y, SeatLocation.Y, 0.01f));
        TestTrue(TEXT("Standing spawn is resolved above the floor"), ResolvedSeatLocation.Z >= SeatLocation.Z);
        TestTrue(TEXT("Operator starts standing and can walk to consoles"), Pawn->IsStanding());
        TestEqual(TEXT("Default standing FOV matches authored wide view"), Pawn->GetCurrentFieldOfView(), 112.0f);

        Pawn->SetActorLocation(ResolvedSeatLocation + FVector(650.0f, 400.0f, 80.0f));
        Pawn->Tick(1.0f / 30.0f);
        TestTrue(TEXT("Standing movement remains inside the authored room bounds"),
            Pawn->GetActorLocation().Equals(ResolvedSeatLocation + FVector(550.0f, 310.0f, 0.0f), 0.01f));

        Pawn->SetActorLocation(ResolvedSeatLocation + FVector(200.0f, 0.0f, 0.0f));
        Pawn->ToggleSeatState();
        TestTrue(TEXT("Operator cannot sit away from chair"), Pawn->IsStanding());
        Pawn->SetActorLocation(ResolvedSeatLocation + FVector(80.0f, 0.0f, 0.0f));
        TestTrue(TEXT("Chair return radius is recognized"), Pawn->CanSitAtChair());
        Pawn->ToggleSeatState();
        TestFalse(TEXT("Operator sits after returning to chair"), Pawn->IsStanding());
        TestTrue(TEXT("Sitting restores exact chair datum"), Pawn->GetActorLocation().Equals(ResolvedSeatLocation, 0.01f));

        Pawn->SetActorLocation(ResolvedSeatLocation + FVector(500.0f, 300.0f, 80.0f));
        Pawn->Tick(1.0f / 30.0f);
        TestTrue(TEXT("Seated pawn rejects translation"), Pawn->GetActorLocation().Equals(ResolvedSeatLocation, 0.01f));

        Pawn->ToggleSeatState();
        TestTrue(TEXT("Operator can stand again deliberately"), Pawn->IsStanding());

        const UCameraComponent* OperatorCamera = Pawn->FindComponentByClass<UCameraComponent>();
        TestNotNull(TEXT("Operator camera is available to the controller trace"), OperatorCamera);
        const FVector CameraLocation = OperatorCamera ? OperatorCamera->GetComponentLocation() : FVector::ZeroVector;
        ALBControlRoomOperationsConsole* Console = World->SpawnActor<ALBControlRoomOperationsConsole>(
            ALBControlRoomOperationsConsole::StaticClass(),
            FVector(500.0f, CameraLocation.Y - 12.5f, CameraLocation.Z + 78.0f),
            FRotator::ZeroRotator);
        TestNotNull(TEXT("Controller interaction target spawned"), Console);
        if (Console)
        {
            if (!Console->HasActorBegunPlay())
            {
                Console->DispatchBeginPlay();
            }
            Pawn->SetActorLocation(ResolvedSeatLocation);
            World->UpdateWorldComponents(true, false);
            World->Tick(LEVELTICK_All, 1.0f / 30.0f);
            Pawn->InteractAtViewCentre();
            TestTrue(TEXT("Centre-view interaction reaches the physical Start button"),
                Console->CaptureSaveState().LastAlarm.Contains(TEXT("START HELD")));
        }

        ALBPressShopBuildAuthority* BuildAuthority = World->SpawnActor<ALBPressShopBuildAuthority>(
            ALBPressShopBuildAuthority::StaticClass(), FVector(1000.0f, 2000.0f, 0.0f), FRotator::ZeroRotator);
        TestNotNull(TEXT("Single map build authority fixture exists"), BuildAuthority);
        TestTrue(TEXT("Standing operator enters overhead management view"), Pawn->EnterManagementView());
        ALBManagementPawn* ManagementPawn = PlayerController
            ? Cast<ALBManagementPawn>(PlayerController->GetPawn()) : nullptr;
        TestNotNull(TEXT("Controller possesses the overhead management pawn"), ManagementPawn);
        if (ManagementPawn)
        {
            TestTrue(TEXT("Management pawn retains the exact standing return pawn"),
                ManagementPawn->GetReturnPawn() == Pawn);
            TestTrue(TEXT("Controller returns to the standing control-room pawn"),
                ManagementPawn->ReturnToControlRoom());
            TestTrue(TEXT("Return possession restores the original operator"),
                PlayerController->GetPawn() == Pawn);
        }

    }

    const UInputSettings* InputSettings = GetDefault<UInputSettings>();
    TestNotNull(TEXT("Project input settings are available"), InputSettings);
    if (InputSettings)
    {
        TArray<FInputActionKeyMapping> InteractionMappings;
        InputSettings->GetActionMappingByName(TEXT("LB_GamepadInteract"), InteractionMappings);
        TestTrue(TEXT("Cross/A is mapped to centre-view interaction"),
            InteractionMappings.ContainsByPredicate([](const FInputActionKeyMapping& Mapping)
            {
                return Mapping.Key == EKeys::Gamepad_FaceButton_Bottom;
            }));

        TArray<FInputAxisKeyMapping> ForwardMappings;
        InputSettings->GetAxisMappingByName(TEXT("LB_MoveForward"), ForwardMappings);
        TestTrue(TEXT("Left stick Y is mapped to operator movement"),
            ForwardMappings.ContainsByPredicate([](const FInputAxisKeyMapping& Mapping)
            {
                return Mapping.Key == EKeys::Gamepad_LeftY && FMath::IsNearlyEqual(Mapping.Scale, 1.0f);
            }));
    }

    const ALBControlRoomGameMode* GameModeDefaults = GetDefault<ALBControlRoomGameMode>();
    TestNotNull(TEXT("Control-room game mode defaults exist"), GameModeDefaults);
    if (GameModeDefaults)
    {
        TestTrue(
            TEXT("Control-room game mode selects seated pawn"),
            GameModeDefaults->DefaultPawnClass.Get() == ALBControlRoomPawn::StaticClass());
        TestTrue(
            TEXT("Control-room game mode selects the CCTV HUD"),
            GameModeDefaults->HUDClass.Get() == ALBControlRoomHUD::StaticClass());
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
