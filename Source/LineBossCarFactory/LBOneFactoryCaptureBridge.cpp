#include "LBOneFactoryCaptureBridge.h"

#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "UnrealClient.h"
#include "Widgets/SViewport.h"
#include "Widgets/SWindow.h"

namespace
{
constexpr int32 MaxValidationCaptureDimension = 16384;

UGameViewportClient* ResolveGameViewportClient(const UObject* WorldContextObject)
{
    if (!GEngine || !WorldContextObject)
    {
        return nullptr;
    }

    UWorld* World = GEngine->GetWorldFromContextObject(
        WorldContextObject,
        EGetWorldErrorMode::ReturnNull);
    if (!World || (World->WorldType != EWorldType::PIE && World->WorldType != EWorldType::Game))
    {
        return nullptr;
    }

    return World->GetGameViewport();
}

TSharedPtr<SViewport> ResolveGameViewportWidget(const UObject* WorldContextObject)
{
    UGameViewportClient* ViewportClient = ResolveGameViewportClient(WorldContextObject);
    return ViewportClient ? ViewportClient->GetGameViewportWidget() : nullptr;
}

FIntPoint GetArrangedDrawSize(const TSharedPtr<SViewport>& GameViewportWidget)
{
    if (!GameViewportWidget.IsValid())
    {
        return FIntPoint::ZeroValue;
    }

    // FSlateApplication::TakeScreenshotCommon uses the arranged widget's
    // Geometry.GetDrawSize(), including its accumulated layout scale, and
    // truncates each component to int32. Mirror that exact size contract.
    const FVector2D DrawSize = GameViewportWidget->GetCachedGeometry().GetDrawSize();
    return FIntPoint(
        static_cast<int32>(DrawSize.X),
        static_cast<int32>(DrawSize.Y));
}
}

FIntPoint ULBOneFactoryCaptureBridge::ResizePIEWindowForGameWidgetSize(
    const UObject* WorldContextObject,
    const int32 Width,
    const int32 Height)
{
    if (Width <= 0 || Height <= 0 ||
        Width > MaxValidationCaptureDimension || Height > MaxValidationCaptureDimension ||
        !FSlateApplication::IsInitialized())
    {
        return FIntPoint::ZeroValue;
    }

    const TSharedPtr<SViewport> GameViewportWidget =
        ResolveGameViewportWidget(WorldContextObject);
    const FIntPoint CurrentDrawSize = GetArrangedDrawSize(GameViewportWidget);
    if (!GameViewportWidget.IsValid() || CurrentDrawSize.X <= 0 || CurrentDrawSize.Y <= 0)
    {
        return FIntPoint::ZeroValue;
    }

    const TSharedPtr<SWindow> Window = FSlateApplication::Get().FindWidgetWindow(
        GameViewportWidget.ToSharedRef());
    if (!Window.IsValid())
    {
        return FIntPoint::ZeroValue;
    }

    // GetDrawSize and GetSizeInScreen are both expressed in absolute screen
    // pixels. Preserve the current non-viewport chrome by adding only the game
    // widget delta to the owning window's outer size.
    const FVector2D CurrentWindowSize = Window->GetSizeInScreen();
    const FVector2D DesiredWindowSize(
        CurrentWindowSize.X + static_cast<double>(Width - CurrentDrawSize.X),
        CurrentWindowSize.Y + static_cast<double>(Height - CurrentDrawSize.Y));
    if (DesiredWindowSize.X <= 0.0 || DesiredWindowSize.Y <= 0.0)
    {
        return FIntPoint::ZeroValue;
    }

    Window->ReshapeWindow(Window->GetPositionInScreen(), DesiredWindowSize);
    return CurrentDrawSize;
}

FIntPoint ULBOneFactoryCaptureBridge::GetPIEGameWidgetDrawSize(
    const UObject* WorldContextObject)
{
    return GetArrangedDrawSize(ResolveGameViewportWidget(WorldContextObject));
}

bool ULBOneFactoryCaptureBridge::RequestPIERestrictedUIScreenshot(
    const UObject* WorldContextObject,
    const FString& Filename,
    const int32 Width,
    const int32 Height)
{
    if (Filename.IsEmpty() || Width <= 0 || Height <= 0 ||
        FScreenshotRequest::IsScreenshotRequested() ||
        GetPIEGameWidgetDrawSize(WorldContextObject) != FIntPoint(Width, Height))
    {
        return false;
    }

    // bShowUI=true and bRestrictToGameViewport=true make
    // UGameViewportClient::ProcessScreenShots pass GetGameViewportWidget() to
    // FSlateApplication::TakeScreenshot. This includes the real native UMG at
    // its arranged 1920x1080 size without editor chrome or image processing.
    FScreenshotRequest::RequestScreenshot(
        Filename,
        true,
        false,
        false,
        FIntRect(),
        true);
    return FScreenshotRequest::IsScreenshotRequested();
}
