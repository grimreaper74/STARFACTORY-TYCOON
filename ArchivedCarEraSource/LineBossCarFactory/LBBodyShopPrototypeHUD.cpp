#include "LBBodyShopPrototypeHUD.h"

#include "Blueprint/UserWidget.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "LBBodyShopPrototypeRootWidget.h"
#include "LBBodyShopPrototypeWorldBootstrap.h"

ALBBodyShopPrototypeHUD::ALBBodyShopPrototypeHUD()
{
    // AHUD::BeginPlay can run before PIE has attached the local player's screen.
    // Keep a short-lived retry tick so the UMG-only shell is also reliable in a
    // normal packaged launch, then disable it as soon as the widget is active.
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
}

void ALBBodyShopPrototypeHUD::BeginPlay()
{
    Super::BeginPlay();
    if (EnsurePrototypeWidget()) SetActorTickEnabled(false);
}

void ALBBodyShopPrototypeHUD::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (EnsurePrototypeWidget()) SetActorTickEnabled(false);
}

void ALBBodyShopPrototypeHUD::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (IsValid(PrototypeRootWidget)) PrototypeRootWidget->RemoveFromParent();
    PrototypeRootWidget = nullptr;
    Super::EndPlay(EndPlayReason);
}

bool ALBBodyShopPrototypeHUD::EnsurePrototypeWidget()
{
    if (IsValid(PrototypeRootWidget)) return true;
    ALBBodyShopPrototypeWorldBootstrap* Bootstrap = FindPrototypeBootstrap();
    if (Bootstrap && !Bootstrap->ShouldShowPrototypeHUD()) return false;
    APlayerController* Controller = GetOwningPlayerController();
    if (!Controller || !Controller->IsLocalController()) return false;

    PrototypeRootWidget = CreateWidget<ULBBodyShopPrototypeRootWidget>(
        Controller, ULBBodyShopPrototypeRootWidget::StaticClass());
    if (!PrototypeRootWidget || !PrototypeRootWidget->AddToPlayerScreen(40))
    {
        PrototypeRootWidget = nullptr;
        return false;
    }
    Controller->bShowMouseCursor = true;
    FInputModeGameAndUI InputMode;
    InputMode.SetHideCursorDuringCapture(false);
    InputMode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
    Controller->SetInputMode(InputMode);
    PrototypeRootWidget->RefreshFromRuntime();
    return true;
}

bool ALBBodyShopPrototypeHUD::IsPrototypeWidgetActive() const
{
    const ESlateVisibility Visibility = IsValid(PrototypeRootWidget)
        ? PrototypeRootWidget->GetVisibility()
        : ESlateVisibility::Collapsed;
    return IsValid(PrototypeRootWidget) && PrototypeRootWidget->IsInViewport()
        && (Visibility == ESlateVisibility::Visible
            || Visibility == ESlateVisibility::SelfHitTestInvisible)
        && PrototypeRootWidget->HasRenderableShell();
}

FString ALBBodyShopPrototypeHUD::BuildIsolationReadout(const bool bHasBootstrap,
    const bool bFlagsValid, const bool bWorldIsolationValid,
    const bool bHasLegacyAuthority,
    const bool bAuthoritiesBound)
{
    if (!bHasBootstrap) return TEXT("MAP BOOTSTRAP MISSING - NO FACTORY AUTHORITY CREATED");
    if (!bFlagsValid) return TEXT("ISOLATION FLAGS INVALID - EXPERIMENTAL RUNTIME LOCKED");
    if (!bWorldIsolationValid)
    {
        return bHasLegacyAuthority
            ? TEXT("LEGACY AUTHORITY DETECTED - EXPERIMENTAL RUNTIME LOCKED")
            : TEXT("MAP IS NOT ISOLATED - EXPERIMENTAL RUNTIME LOCKED");
    }
    if (!bAuthoritiesBound) return TEXT("ISOLATED MAP READY - WAITING FOR MODULE AUTHORITIES");
    return TEXT("ISOLATED MAP READY - EXPERIMENTAL SAVE V1 ONLY");
}

ALBBodyShopPrototypeWorldBootstrap* ALBBodyShopPrototypeHUD::FindPrototypeBootstrap() const
{
    UWorld* World = GetWorld();
    if (!World) return nullptr;
    for (TActorIterator<ALBBodyShopPrototypeWorldBootstrap> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
    }
    return nullptr;
}
