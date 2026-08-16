#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "LBControlRoomCCTVFeed.h"
#include "LBControlRoomPawn.h"
#include "Components/SceneCaptureComponent2D.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBControlRoomCCTVFeedRuntimeTest,
    "LineBoss.ControlRoom.CCTV.SelectedFeedRuntime",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBControlRoomCCTVFeedRuntimeTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LBControlRoomCCTVTestWorld"));
    TestNotNull(TEXT("Transient CCTV game world created"), World);
    if (!World)
    {
        return false;
    }

    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ALBControlRoomPawn* Pawn = World->SpawnActor<ALBControlRoomPawn>(
        ALBControlRoomPawn::StaticClass(), FVector(0.0f, 0.0f, 112.0f), FRotator::ZeroRotator);
    APlayerController* Controller = World->SpawnActor<APlayerController>();
    ALBControlRoomCCTVFeed* Feed = World->SpawnActor<ALBControlRoomCCTVFeed>(
        ALBControlRoomCCTVFeed::StaticClass(), FVector(0.0f, 300.0f, 160.0f), FRotator::ZeroRotator);
    TestNotNull(TEXT("Seated pawn exists"), Pawn);
    TestNotNull(TEXT("Player controller exists"), Controller);
    TestNotNull(TEXT("Selected CCTV feed exists"), Feed);
    if (Controller && Pawn)
    {
        Controller->Possess(Pawn);
    }

    World->BeginPlay();
    if (Pawn && !Pawn->HasActorBegunPlay())
    {
        Pawn->DispatchBeginPlay();
    }
    if (Feed && !Feed->HasActorBegunPlay())
    {
        Feed->DispatchBeginPlay();
    }
    World->UpdateWorldComponents(true, false);

    if (Feed)
    {
        TestFalse(TEXT("CCTV capture is dormant until selected"), Feed->IsSelectedFeed());
        UTextureRenderTarget2D* Target = Feed->GetRenderTarget();
        TestNotNull(TEXT("Runtime render target is created"), Target);
        if (Target)
        {
            TestEqual(TEXT("Selected feed width is 1280"), Target->SizeX, 1280);
            TestEqual(TEXT("Selected feed height is 720"), Target->SizeY, 720);
        }
        TestEqual(TEXT("Selected feed uses calibrated exposure"), Feed->GetCaptureExposureBias(), 0.5f);
        TestTrue(TEXT("CCTV capture retains machinery depth shadows"),
            Feed->GetCaptureComponent()->ShowFlags.DynamicShadows);
        TestTrue(TEXT("Display surface blocks pointer visibility traces"),
            Feed->GetDisplaySurface() &&
            Feed->GetDisplaySurface()->GetCollisionResponseToChannel(ECC_Visibility) == ECR_Block);

        Feed->SetSelectedFeed(false);
        TestFalse(TEXT("Inactive feed state is retained"), Feed->IsSelectedFeed());
        TestFalse(TEXT("Inactive feed stops per-frame capture"),
            Feed->GetCaptureComponent() && Feed->GetCaptureComponent()->bCaptureEveryFrame);
        Feed->SetSelectedFeed(true);
        TestTrue(TEXT("Selected feed resumes per-frame capture"),
            Feed->GetCaptureComponent() && Feed->GetCaptureComponent()->bCaptureEveryFrame);
    }

    if (Pawn && Feed)
    {
        TestTrue(TEXT("Clicking the CCTV actor focuses the seated view"), Pawn->InteractWithActor(Feed));
        TestEqual(TEXT("Focused screen FOV uses the bounded accessibility zoom"),
            Pawn->GetCurrentFieldOfView(), 38.0f);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
