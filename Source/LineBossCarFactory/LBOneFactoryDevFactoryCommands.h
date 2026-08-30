#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBOneFactoryDevFactoryCommands.generated.h"

class ALBOneFactoryProductionFlowAuthority;
class ALBOneFactoryRuntimeCoordinator;

/**
 * Drives a timed visual tour of the factory.
 *
 * Console commands issued through -ExecCmds all execute inside a single
 * deferred batch, so a camera move and a screenshot in the same batch produce
 * one image of the last camera. This actor spreads the steps across frames so
 * each viewpoint is actually rendered, streamed and captured, which makes
 * visual iteration repeatable.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryDevTourActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryDevTourActor();

    virtual void Tick(float DeltaSeconds) override;

    /** Departments to visit, in order. */
    void BeginTour(const TArray<FString>& InDepartments, int32 InSettleFrames,
        float InSecondsPerStop, const FString& InLabel);

private:
    UPROPERTY()
    TArray<FString> Departments;

    UPROPERTY()
    FString Label;

    int32 SettleFrames = 30;
    int32 FrameCounter = 0;
    int32 StopIndex = INDEX_NONE;
    float SecondsPerStop = 0.0f;
    bool bAwaitingCapture = false;
    bool bFinished = false;
};

/**
 * A deliberately small, one-shot packaged-runtime measurement.  Unlike an
 * editor mesh count, this waits for the actual management view to render and
 * reports frame-time percentiles plus the static-mesh LOD population that was
 * live in that world.  It is developer-only, owns no factory state and exits
 * as soon as the requested sample has been written to the log.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBOneFactoryDevPerformanceCaptureActor : public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryDevPerformanceCaptureActor();

    virtual void Tick(float DeltaSeconds) override;

    void BeginCapture(int32 InSettleFrames, int32 InSampleFrames,
        const FString& InLabel, bool bInQuitAfterCapture);

private:
    int32 SettleFramesRemaining = 120;
    int32 SampleFramesRemaining = 300;
    FString Label;
    TArray<float> FrameTimesMs;
    bool bQuitAfterCapture = false;
};

/**
 * Developer-only orchestration that drives the shipped OneFactory player
 * builder and runtime coordinator through a whole working factory in one step.
 *
 * ALBOneFactoryGameMode deliberately seeds nothing: SeedsProductionStations()
 * is false and ValidateBootstrapContract() rejects a shell that would seed. The
 * Moorcross Works map therefore always opens ready but empty, and the runtime
 * coordinator refuses to run until a player has created and commissioned all
 * four departments. That is correct for the shipped product, but it means the
 * 57-station loop had only ever been exercised by synthetic-world automation.
 *
 * Every function below calls the same public API a player action calls. It
 * creates no second authority, seeds no station into the map package, persists
 * nothing and owns no presentation. It is a way to *run* the existing factory,
 * not a new factory.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryDevFactory :
    public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /**
     * Creates and commissions Press, Body/Weld, Paint and Assembly in the
     * contract's lifecycle order, then audits the resulting 57-station route.
     * Stops at the first failing step and reports which one failed.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool BuildAndCommissionWholeFactory(UObject* WorldContextObject,
        FString& OutReason);

    /**
     * Creates VehicleCount build orders and releases each into processing.
     * Vehicle model and paint programme are read from the live committed
     * layouts rather than hard-coded, matching the automation setup.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool StartDemoProduction(UObject* WorldContextObject,
        int32 VehicleCount, FString& OutReason);

    /**
     * Advances every started unit by DeltaSeconds. Body, Paint and end-of-line
     * inspections hold at 100 percent until a quality result is submitted; with
     * bAutoPassQualityGates the developer loop passes them so cars keep moving.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool AdvanceFactory(UObject* WorldContextObject, float DeltaSeconds,
        bool bAutoPassQualityGates, int32& OutProcessedUnitCount,
        FString& OutReason);

    /**
     * Runs Iterations deterministic steps of StepSeconds each. Deterministic
     * stepping is used rather than wall-clock so an unattended run produces the
     * same result every time.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool RunFactory(UObject* WorldContextObject, int32 Iterations,
        float StepSeconds, bool bAutoPassQualityGates, FString& OutReason);

    /** Route topology plus per-unit progress. Reads only; mutates nothing. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool BuildFactoryStatusReport(UObject* WorldContextObject,
        FString& OutReport);

    /**
     * Ensures runtime lighting for the active presentation. The generic
     * fallback uses a broad site rig; a configured Press art-direction actor
     * instead selects the approved B_stylized calibration (six 1200-lumen
     * fixtures, sun 0.30, sky 0.20, exposure -0.50) and ignores Intensity.
     * Runtime-only and never saved, so the protected map is untouched.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool EnsureDevLighting(UObject* WorldContextObject, float Intensity,
        FString& OutReason);

    /**
     * Frames the configured route, optionally one department only, by pointing
     * the active view at the station centroid from a distance that fits its
     * bounds. Department accepts Press, Body, Paint, Assembly or All.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    /**
     * Solves a management framing for a department and applies it.
     *
     * bDriveViewTarget=true keeps the historic behaviour: a transient dev
     * ACameraActor becomes the view target. That is right for tours and
     * captures, but it must NOT be used on the live player path - taking the
     * view target and never handing it back is why every camera control
     * appeared broken, with pan, orbit and zoom all still driving an
     * off-screen pawn. Pass false to push the same solved pose into the
     * player's own ALBManagementPawn and leave it as the view target.
     */
    static bool FrameProductionLine(UObject* WorldContextObject,
        const FString& Department, FString& OutReason,
        bool bDriveViewTarget = true);

    /**
     * Transient high-quality capture framing with an explicitly authored eye
     * and look target.  Intended for runtime tours and screenshots only: the
     * camera is tagged, is never saved into a map, and is reclaimed with PIE.
     * Unlike the department solver this does not infer a viewing side from a
     * route, which is essential for enclosed production cells.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool FrameTransientPhotoCamera(UObject* WorldContextObject,
        FVector EyeWorldLocation, FVector TargetWorldLocation,
        float FieldOfViewDegrees, float ExposureBias, FString& OutReason);

    /**
     * Hides only the two audited legacy wall panels and five proven shell
     * column instances that intersect the transient Press Shop photo lane.
     * The live shell and map data stay untouched; passing false restores
     * precisely the geometry this helper hid in the current PIE world.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool SetPressPhotoStructuralCutaway(UObject* WorldContextObject,
        bool bHidden, FString& OutReason);

    /**
     * Hides the exact legacy foreground post set only while capturing a Press
     * Shop beauty shot. It is separate from the structural cutaway so the
     * photo-only aesthetic decision remains explicit and reversible.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool SetPressPhotoForegroundCutaway(UObject* WorldContextObject,
        bool bHidden, FString& OutReason);

    /**
     * Binds a brand material to every semantic material slot in the world.
     *
     * The native import lanes set import_materials=False by policy, so meshes
     * arrive carrying named semantic slots such as M_LB_BS_CreamPaint and
     * M_LB_BS_EmeraldPanel with nothing bound to them. No material assets exist
     * for those slots, so the whole factory renders in default grey and good
     * geometry reads as a featureless blob.
     *
     * This walks every static mesh component, reads each slot's authored name
     * and binds a material instance in the BRAND_IDENTITY_AUTHORITY palette.
     * Runtime-only: no Content package is created or modified, no mesh is
     * altered, and no frozen instance count changes. Unmatched slot names are
     * reported so the table can be extended rather than guessed at.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool ApplySemanticMaterials(UObject* WorldContextObject,
        FString& OutReason);

    /**
     * Hides or restores high structure so the management view is not sliced up
     * by roof beams.
     *
     * The map's authored roof sits between a management camera and the floor at
     * any sensible pitch. Factory-management games cut the roof away for exactly
     * this reason. Visibility only: nothing is destroyed, the map is untouched,
     * and passing bShow restores every component this hid.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool SetRoofHidden(UObject* WorldContextObject, bool bHidden,
        double AboveZCm, FString& OutReason);

    /** Whether this world's roof is currently hidden by SetRoofHidden. */
    static bool IsRoofHidden(UObject* WorldContextObject);

    /** Body/Weld slice: every unit currently standing in a Body station. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Developer",
        meta=(WorldContext="WorldContextObject"))
    static bool BuildBodyWeldReport(UObject* WorldContextObject,
        FString& OutReport);

    static ALBOneFactoryRuntimeCoordinator* FindCoordinator(const UWorld* World);
    static ALBOneFactoryProductionFlowAuthority* FindProductionFlow(
        const UWorld* World);
};
