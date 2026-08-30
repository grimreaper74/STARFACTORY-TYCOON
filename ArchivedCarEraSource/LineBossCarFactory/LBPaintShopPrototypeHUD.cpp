#include "LBPaintShopPrototypeHUD.h"

#include "Blueprint/UserWidget.h"
#include "GameFramework/PlayerController.h"
#include "LBPaintShopPrototypeRootWidget.h"

namespace LBPaintShopPrototypeHUDPrivate
{
    FString PhaseName(const ELBPaintShopPrototypePhase Phase)
    {
        switch (Phase)
        {
        case ELBPaintShopPrototypePhase::Uninitialized: return TEXT("UNINITIALIZED");
        case ELBPaintShopPrototypePhase::Starved: return TEXT("STARVED");
        case ELBPaintShopPrototypePhase::Loading: return TEXT("LOADING");
        case ELBPaintShopPrototypePhase::Descending: return TEXT("DESCENDING");
        case ELBPaintShopPrototypePhase::Immersing: return TEXT("IMMERSING");
        case ELBPaintShopPrototypePhase::Rising: return TEXT("RISING");
        case ELBPaintShopPrototypePhase::Draining: return TEXT("DRAINING");
        case ELBPaintShopPrototypePhase::OutputReady: return TEXT("OUTPUT READY");
        case ELBPaintShopPrototypePhase::Faulted: return TEXT("FAULTED");
        default: return TEXT("UNKNOWN");
        }
    }
}

ALBPaintShopPrototypeHUD::ALBPaintShopPrototypeHUD()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
}

void ALBPaintShopPrototypeHUD::BeginPlay()
{
    Super::BeginPlay();
    if (EnsurePrototypeWidget()) SetActorTickEnabled(false);
}

void ALBPaintShopPrototypeHUD::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (EnsurePrototypeWidget()) SetActorTickEnabled(false);
}

void ALBPaintShopPrototypeHUD::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (IsValid(PrototypeRootWidget)) PrototypeRootWidget->RemoveFromParent();
    PrototypeRootWidget = nullptr;
    Super::EndPlay(EndPlayReason);
}

bool ALBPaintShopPrototypeHUD::EnsurePrototypeWidget()
{
    if (IsValid(PrototypeRootWidget)) return true;
    APlayerController* Controller = GetOwningPlayerController();
    if (!Controller || !Controller->IsLocalController()) return false;

    PrototypeRootWidget = CreateWidget<ULBPaintShopPrototypeRootWidget>(
        Controller, ULBPaintShopPrototypeRootWidget::StaticClass());
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

bool ALBPaintShopPrototypeHUD::IsPrototypeWidgetActive() const
{
    const ESlateVisibility Visibility = IsValid(PrototypeRootWidget)
        ? PrototypeRootWidget->GetVisibility()
        : ESlateVisibility::Collapsed;
    return IsValid(PrototypeRootWidget) && PrototypeRootWidget->IsInViewport()
        && (Visibility == ESlateVisibility::Visible
            || Visibility == ESlateVisibility::SelfHitTestInvisible)
        && PrototypeRootWidget->HasRenderableShell();
}

FString ALBPaintShopPrototypeHUD::BuildIsolationReadout(const int32 BootstrapCount,
    const ELBPaintShopPrototypeBootstrapState BootstrapState,
    const bool bCoherentReadyState, const FString& DetailReason)
{
    if (BootstrapCount == 0) return TEXT("ISOLATION: FAIL - MAP BOOTSTRAP MISSING");
    if (BootstrapCount != 1)
    {
        return FString::Printf(TEXT("ISOLATION: FAIL - EXPECTED 1 BOOTSTRAP, FOUND %d"),
            BootstrapCount);
    }
    switch (BootstrapState)
    {
    case ELBPaintShopPrototypeBootstrapState::Ready:
        return bCoherentReadyState
            ? TEXT("ISOLATION: PASS - EXACTLY ONE COHERENT PAINT AUTHORITY PAIR")
            : FString::Printf(TEXT("ISOLATION: FAIL - %s"),
                DetailReason.IsEmpty() ? TEXT("READY STATE IS INCOHERENT")
                    : *DetailReason);
    case ELBPaintShopPrototypeBootstrapState::Initializing:
        return TEXT("ISOLATION: WAIT - PAINT BOOTSTRAP INITIALIZING");
    case ELBPaintShopPrototypeBootstrapState::Failed:
        return FString::Printf(TEXT("ISOLATION: FAIL - %s"),
            DetailReason.IsEmpty() ? TEXT("BOOTSTRAP FAILED") : *DetailReason);
    case ELBPaintShopPrototypeBootstrapState::Uninitialized:
    default:
        return TEXT("ISOLATION: WAIT - PAINT BOOTSTRAP UNINITIALIZED");
    }
}

FString ALBPaintShopPrototypeHUD::BuildRuntimeStageReadout(
    const ELBPaintShopPrototypePhase Phase, const float PhaseProgress01,
    const bool bPaused, const bool bOutputBlocked, const bool bFaulted,
    const FString& FaultReason)
{
    const float SafeProgress01 = FMath::IsFinite(PhaseProgress01)
        ? FMath::Clamp(PhaseProgress01, 0.0f, 1.0f) : 0.0f;
    FString Result = FString::Printf(TEXT("PROCESS: %s  |  %d%%"),
        *LBPaintShopPrototypeHUDPrivate::PhaseName(Phase),
        FMath::RoundToInt(SafeProgress01 * 100.0f));
    if (bPaused) Result += TEXT("  |  PAUSED");
    if (bOutputBlocked) Result += TEXT("  |  OUTPUT BLOCKED");
    if (bFaulted)
    {
        Result += FaultReason.IsEmpty()
            ? TEXT("  |  FAULT")
            : FString::Printf(TEXT("  |  FAULT: %s"), *FaultReason);
    }
    return Result;
}

FString ALBPaintShopPrototypeHUD::GetCameraControlsReadout()
{
    return TEXT("CAMERA: W/A/S/D PAN  |  ARROWS/GAMEPAD ORBIT  |  WHEEL/TRIGGERS ZOOM  |  HOME/B RESET");
}

FString ALBPaintShopPrototypeHUD::GetOperatorControlsReadout()
{
    return TEXT("LINE: SPACE START  |  P PAUSE/RESUME  |  O BLOCK OUTPUT  |  R RELEASE  |  F5 SAVE  |  F9 LOAD");
}
