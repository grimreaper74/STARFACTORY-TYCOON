#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBOneFactoryCaptureBridge.generated.h"

/**
 * Narrow native bridge used by fail-closed OneFactory render validation.
 *
 * A Slate UI screenshot uses the arranged size of the captured SViewport, not
 * the FSceneViewport backbuffer size. This bridge changes the owning window by
 * the exact arranged-widget size delta, reports the cached arranged size, and
 * requests Unreal's native UI-inclusive screenshot restricted to that game
 * widget. It does not read, rescale, crop, composite, or save an image itself.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryCaptureBridge final
    : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /**
     * Resize the owning Slate window by the delta between the live PIE game
     * widget's arranged draw size and the requested size. Slate geometry is
     * frame-cached, so callers must wait for a later frame and query again.
     * Returns (0,0) outside a live PIE/game viewport or for invalid input.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Validation",
        meta=(WorldContext="WorldContextObject"))
    static FIntPoint ResizePIEWindowForGameWidgetSize(
        const UObject* WorldContextObject,
        int32 Width,
        int32 Height);

    /** Return the cached arranged draw size used by Slate widget screenshots. */
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Validation",
        meta=(WorldContext="WorldContextObject"))
    static FIntPoint GetPIEGameWidgetDrawSize(const UObject* WorldContextObject);

    /**
     * Request a native UI screenshot of only the live PIE game widget.
     * Refuses unless its cached arranged draw size is exactly Width x Height.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Validation",
        meta=(WorldContext="WorldContextObject"))
    static bool RequestPIERestrictedUIScreenshot(
        const UObject* WorldContextObject,
        const FString& Filename,
        int32 Width,
        int32 Height);
};
