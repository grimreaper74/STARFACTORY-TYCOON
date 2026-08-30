#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonValue.h"
#include "GameFramework/GameModeBase.h"
#include "LBBodyShopPrototypeWorldBootstrap.h"
#include "LBBodyShopPrototypeGameMode.generated.h"

enum class ELBBodyShopPackagedValidationMode : uint8
{
    None,
    Save,
    Load
};

/** Parsed, token-safe request for the Development-package two-process gate. */
struct FLBBodyShopPackagedValidationRequest
{
    ELBBodyShopPackagedValidationMode Mode = ELBBodyShopPackagedValidationMode::None;
    FString Token;
};

enum class ELBBodyShopPackagedPerformanceView : uint8
{
    None,
    Management,
    Focus
};

/** Token-safe request for one real-RHI packaged Development performance view. */
struct FLBBodyShopPackagedPerformanceRequest
{
    ELBBodyShopPackagedPerformanceView View = ELBBodyShopPackagedPerformanceView::None;
    FString Token;
};

/**
 * Deliberately isolated game mode for the experimental player-built Body Shop.
 *
 * This mode has no dependency on ALBGameMode, campaign v18, Press Shop v913, or
 * the legacy composite Body Weld actor. A map opts in by selecting this mode and
 * placing one ALBBodyShopPrototypeWorldBootstrap actor.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBBodyShopPrototypeGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ALBBodyShopPrototypeGameMode();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    /** The map-local bootstrap is required; this mode never creates legacy authorities. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    ALBBodyShopPrototypeWorldBootstrap* GetPrototypeBootstrap() const
    {
        return PrototypeBootstrap.Get();
    }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    bool HasValidPrototypeBootstrap() const { return bPrototypeBootstrapValid; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Body Shop|Prototype")
    FString GetPrototypeIsolationStatus() const { return PrototypeIsolationStatus; }

    /**
     * Pure contract used by focused tests and map setup diagnostics. It
     * requires runtime-only authorities to be bound and the approved slice to
     * be commissioned after BeginPlay; the saved map itself remains empty.
     */
    static bool ValidatePrototypeWorldContract(bool bHasBootstrap,
        bool bBootstrapFlagsValid, bool bWorldIsolationValid,
        bool bFoundLegacyAuthority, bool bRuntimeAuthoritiesBound,
        bool bInitialUnderbodySliceCommissioned, FString& OutReason);

    /** Pure parser used by the non-Shipping packaged save/restart/load bridge. */
    static bool ParsePackagedValidationRequest(const TCHAR* CommandLine,
        FLBBodyShopPackagedValidationRequest& OutRequest, FString& OutReason);

    /** Stable tokened line accepted by the package runner; failures never share a PASS prefix. */
    static FString BuildPackagedValidationMarker(ELBBodyShopPackagedValidationMode Mode,
        const FString& Token, bool bPassed, const FString& StageName,
        int32 LogicalWIPCount, int32 VisibleWIPCount, const FString& FailureReason = FString());

    /** Pure parser for the isolated non-Shipping packaged performance lane. */
    static bool ParsePackagedPerformanceRequest(const TCHAR* CommandLine,
        FLBBodyShopPackagedPerformanceRequest& OutRequest, FString& OutReason);

    /** Stable one-line handoff consumed by the external packaged-performance runner. */
    static FString BuildPackagedPerformanceMarker(ELBBodyShopPackagedPerformanceView View,
        const FString& Token, bool bPassed, const FString& GraphicsRHI,
        int32 ViewportWidth, int32 ViewportHeight, int32 CapturedFrames,
        int32 TargetComponentCount, int32 UniqueMeshCount, const FString& ReceiptLeaf,
        const FString& FailureReason = FString());

    /** Pure fail-closed cardinality contract used by runtime validation and focused tests. */
    static bool ValidatePackagedPerformanceTargetCounts(int32 RobotCount,
        int32 TargetComponentCount, int32 UniqueMeshCount, bool bAnyForcedLOD,
        FString& OutReason);

private:
    UPROPERTY(Transient)
    TWeakObjectPtr<ALBBodyShopPrototypeWorldBootstrap> PrototypeBootstrap;

    bool bPrototypeBootstrapValid = false;
    FString PrototypeIsolationStatus;

#if !UE_BUILD_SHIPPING
    enum class EPackagedPerformancePhase : uint8
    {
        None,
        WaitRuntime,
        Warmup,
        CaptureCsv,
        FinaliseCsv
    };

    FLBBodyShopPackagedValidationRequest PackagedValidationRequest;
    float PackagedValidationElapsedSeconds = 0.0f;
    bool bPackagedValidationActionIssued = false;
    bool bPackagedValidationSavePointPaused = false;

    FLBBodyShopPackagedPerformanceRequest PackagedPerformanceRequest;
    EPackagedPerformancePhase PackagedPerformancePhase = EPackagedPerformancePhase::None;
    float PackagedPerformanceElapsedSeconds = 0.0f;
    int32 PackagedPerformancePhaseFrames = 0;
    int32 PackagedPerformanceStableFrames = 0;
    int64 PackagedPerformanceLastFileSize = -1;
    FString PackagedPerformanceProfileStem;
    FString PackagedPerformanceProfilePath;
    FString PackagedPerformanceReceiptPath;
    TArray<TSharedPtr<FJsonValue>> PackagedPerformanceTargetSnapshot;
    TSet<FString> PackagedPerformanceTargetMeshPaths;
    int32 PackagedPerformanceSceneViewWidth = -1;
    int32 PackagedPerformanceSceneViewHeight = -1;
    int32 PackagedPerformanceGlobalForcedLOD = INDEX_NONE;
    int32 PackagedPerformanceRegisteredSceneProxyCount = -1;
    float PackagedPerformanceViewConfiguredWorldSeconds = -1.0f;
    float PackagedPerformanceLODSnapshotWorldSeconds = -1.0f;

    void InitialisePackagedValidationBridge(const TCHAR* CommandLine);
    void TickPackagedValidationBridge(float DeltaSeconds);
    void FinishPackagedValidationBridge(bool bPassed, const FString& FailureReason);

    void InitialisePackagedPerformanceBridge(const TCHAR* CommandLine);
    void TickPackagedPerformanceBridge(float DeltaSeconds);
    void FinishPackagedPerformanceBridge(bool bPassed, const FString& FailureReason);
    bool ValidatePackagedPerformanceEnvironment(FString& OutReason) const;
    bool WritePackagedPerformanceReceipt(FString& OutReceiptPath, FString& OutReason) const;
#endif
};
