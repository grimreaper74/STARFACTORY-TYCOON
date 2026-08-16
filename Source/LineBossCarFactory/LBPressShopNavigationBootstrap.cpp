#include "LBPressShopNavigationBootstrap.h"

#include "AI/NavigationSystemBase.h"
#include "EngineUtils.h"
#include "GameFramework/WorldSettings.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavigationPath.h"
#include "NavigationSystem.h"
#include "TimerManager.h"

ALBPressShopNavigationBootstrap::ALBPressShopNavigationBootstrap()
{
    PrimaryActorTick.bCanEverTick = false;
}

void ALBPressShopNavigationBootstrap::BeginPlay()
{
    Super::BeginPlay();
    GetWorldTimerManager().SetTimer(BuildTimer, this,
        &ALBPressShopNavigationBootstrap::EnsureNavigationReady, 0.25f, false);
}

void ALBPressShopNavigationBootstrap::EnsureNavigationReady()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
    if (!Navigation)
    {
        AWorldSettings* WorldSettings = World->GetWorldSettings();
        UNavigationSystemModuleConfig* Config = NewObject<UNavigationSystemModuleConfig>(
            WorldSettings, TEXT("LB_PressShopRuntimeNavigationConfig"));
        Config->NavigationSystemClass = FSoftClassPath(UNavigationSystemV1::StaticClass());
        WorldSettings->SetNavigationSystemConfigOverride(Config);
        FNavigationSystem::AddNavigationSystemToWorld(
            *World, FNavigationSystemRunMode::GameMode, Config, true, true);
        Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
    }

    if (!Navigation)
    {
        UE_LOG(LogNavigation, Error, TEXT("Line Boss could not create Press Shop navigation system"));
        return;
    }

    for (TActorIterator<ANavMeshBoundsVolume> It(World); It; ++It)
    {
        Navigation->OnNavigationBoundsUpdated(*It);
    }
    Navigation->Build();
    bNavigationReady = Navigation->GetDefaultNavDataInstance(FNavigationSystem::DontCreate) != nullptr;
    UE_LOG(LogNavigation, Display, TEXT("LINE_BOSS_PRESS_SHOP_NAVIGATION_READY=%s"),
        bNavigationReady ? TEXT("true") : TEXT("false"));
}

bool ALBPressShopNavigationBootstrap::ValidatePath(const FVector& Start, const FVector& End)
{
    ValidatedPathLength = -1.0f;
    ValidatedPathPoints.Reset();
    bValidatedPathPartial = false;

    UNavigationPath* Path = UNavigationSystemV1::FindPathToLocationSynchronously(
        this, Start, End, nullptr, nullptr);
    if (!Path || !Path->IsValid())
    {
        return false;
    }

    bValidatedPathPartial = Path->IsPartial();
    ValidatedPathLength = Path->GetPathLength();
    ValidatedPathPoints = Path->PathPoints;
    return !bValidatedPathPartial;
}
