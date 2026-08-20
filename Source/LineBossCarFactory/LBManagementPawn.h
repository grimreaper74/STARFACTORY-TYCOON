#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "LBFactoryBuildMachine.h"
#include "LBPressShopBuildAuthority.h"
#include "LBFactoryAGVInfrastructure.h"
#include "LBManagementPawn.generated.h"

class UCameraComponent;
class UCanvas;
class UMaterialInterface;
class UMaterialInstanceDynamic;
class USceneComponent;
class USpringArmComponent;
class UWidgetInteractionComponent;
class UPrimitiveComponent;
class ALBControlRoomPawn;

/** Colour-independent state used by every floor-placement preview. */
enum class ELBPlacementPreviewState : uint8
{
    WaitingForSurface,
    Ready,
    Blocked
};

/**
 * Testable presentation contract kept separate from the authoritative placement result.
 * Debug geometry and the HUD can therefore explain the same result without ever changing it.
 */
struct LINEBOSSCARFACTORY_API FLBPlacementPreviewStyle
{
    ELBPlacementPreviewState State = ELBPlacementPreviewState::WaitingForSurface;
    FColor FootprintColour = FColor(255, 190, 40, 48);
    FColor AccentColour = FColor(255, 235, 170);
    FString StateMarker = TEXT("[WAIT] FIND FACTORY FLOOR");
    FString AuthorityReason;
    FString NextAction = TEXT("MOVE CURSOR ONTO AN AUTHORISED FACTORY FLOOR");
    float HatchSpacingCm = 150.0f;

    bool IsPlacementAllowed() const { return State == ELBPlacementPreviewState::Ready; }
};

/** World-space geometry shared by the footprint, protected envelope and process-flow cues. */
struct LINEBOSSCARFACTORY_API FLBPlacementPreviewGeometry
{
    FVector GroundCentre = FVector::ZeroVector;
    FVector GroundHalfExtent = FVector::ZeroVector;
    FVector EnvelopeCentre = FVector::ZeroVector;
    FVector EnvelopeHalfExtent = FVector::ZeroVector;
    FVector InputSocket = FVector::ZeroVector;
    FVector OutputSocket = FVector::ZeroVector;
    bool bShowProcessFlow = false;
};

/** Player-facing replacement for world-space debug strings during placement. */
struct LINEBOSSCARFACTORY_API FLBPlacementCardData
{
    bool bVisible = false;
    bool bCanConfirm = false;
    FString Title;
    FString State;
    FString ObstructionDisplayName;
    FString ObstructionStableId;
    FString Cause;
    FString CorrectiveAction;
    FString Controls;
    FLinearColor AccentColour = FLinearColor::White;
};

/** Resolution-independent safe-area contract used by the native placement card. */
struct LINEBOSSCARFACTORY_API FLBPlacementCardLayout
{
    FVector2D Position = FVector2D::ZeroVector;
    FVector2D Size = FVector2D::ZeroVector;
    float SafeMargin = 0.0f;
    float ContentWidth = 0.0f;
    float UIScale = 1.0f;
    int32 MaximumCharactersPerLine = 48;
    bool bCardOnLeft = false;

    bool IsInsideViewport(const FIntPoint& Viewport) const
    {
        return Position.X >= SafeMargin && Position.Y >= SafeMargin
            && Position.X + Size.X <= Viewport.X - SafeMargin + 0.1f
            && Position.Y + Size.Y <= Viewport.Y - SafeMargin + 0.1f;
    }
};

/** Camera distance and lateral offset required to keep the envelope clear of its card. */
struct LINEBOSSCARFACTORY_API FLBPlacementFramingContract
{
    float RequiredZoomDistanceCm = 6500.0f;
    float CameraLateralOffsetCm = 0.0f;
    bool bCardOnLeft = false;
};

/** Deterministic three-quarter framing derived from renderable factory geometry only. */
struct LINEBOSSCARFACTORY_API FLBFactoryOverviewFramingContract
{
    FVector PivotLocation = FVector::ZeroVector;
    FRotator PivotRotation = FRotator(0.0f, -50.0f, 0.0f);
    FRotator BoomRotation = FRotator(-32.0f, 0.0f, 0.0f);
    float ZoomDistanceCm = 9000.0f;
    int32 FramedActorCount = 0;
    /** Long-axis span this composition intentionally frames. */
    float FramedLongAxisCm = 0.0f;
    bool bFramesWholeFactory = false;

    bool IsValid() const
    {
        return FramedActorCount > 0 && !PivotLocation.ContainsNaN()
            && FMath::IsFinite(ZoomDistanceCm) && ZoomDistanceCm > 0.0f;
    }
};

UCLASS()
class LINEBOSSCARFACTORY_API ALBManagementPawn : public APawn
{
    GENERATED_BODY()

public:
    ALBManagementPawn();
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void Tick(float DeltaSeconds) override;
    virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
    virtual void PostRenderFor(APlayerController* PC, UCanvas* Canvas,
        FVector CameraPosition, FVector CameraDir) override;

    /** Executes the same guarded station action used after a cursor hit. */
    UFUNCTION(BlueprintCallable, Category = "Line Boss|Interaction")
    bool InteractWithActor(AActor* TargetActor);

    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder") void StartPressTrainPlacement();
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder") bool StartMachinePlacement(ELBFactoryBuildMachineType MachineType);
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") ELBFactoryBuildMachineType GetSelectedMachineType() const { return SelectedMachineType; }
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder") void CancelPressTrainPlacement();
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder") bool ConfirmPressTrainPlacement();
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder") void RotatePressTrainPlacement();
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") bool IsPressTrainPlacementActive() const { return bPressTrainPlacementActive; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") bool IsPressTrainPlacementValid() const { return bPressTrainPlacementValid; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") FString GetPressTrainPlacementReason() const { return PressTrainPlacementReason; }
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder") bool StartStoragePlacement(ELBPressShopStorageType StorageType);
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") bool IsStoragePlacementActive() const { return bStoragePlacementActive; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") bool IsStoragePlacementValid() const { return bStoragePlacementValid; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") FString GetStoragePlacementReason() const { return StoragePlacementReason; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") ELBPressShopStorageType GetSelectedStorageType() const { return SelectedStorageType; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") int32 GetStoragePreviewColumns() const { return StoragePreviewColumns; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") int32 GetStoragePreviewRows() const { return StoragePreviewRows; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") int32 GetStoragePreviewCapacity() const { return StoragePreviewCapacity; }
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder") bool StartInfrastructurePlacement(ELBFactoryAGVInfrastructureType Type);
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") bool IsInfrastructurePlacementActive() const { return bInfrastructurePlacementActive; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") bool IsInfrastructurePlacementValid() const { return bInfrastructurePlacementValid; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") FString GetInfrastructurePlacementReason() const { return InfrastructurePlacementReason; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder") ELBFactoryAGVInfrastructureType GetSelectedInfrastructureType() const { return SelectedInfrastructureType; }
    /** Click-selection and safe transform edit for generated/player-placed floor infrastructure. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder|Edit") bool SelectInfrastructure(ALBFactoryAGVInfrastructure* Infrastructure);
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder|Edit") bool StartSelectedInfrastructureEdit();
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder|Edit") bool ConfirmInfrastructureEdit();
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder|Edit") void CancelInfrastructureEdit(bool bClearSelection = false);
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder|Edit") void ClearInfrastructureSelection();
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder|Edit") bool HasSelectedInfrastructure() const { return IsValid(InspectedInfrastructure); }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder|Edit") bool IsInfrastructureEditActive() const { return bInfrastructureEditActive; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder|Edit") bool IsInfrastructureEditValid() const { return bInfrastructureEditValid; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder|Edit") FString GetInfrastructureEditReason() const { return InfrastructureEditReason; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder|Edit") FName GetInspectedInfrastructureId() const;
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder|Edit") ELBFactoryAGVInfrastructureType GetInspectedInfrastructureType() const;
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder|Edit") ELBFactoryInfrastructureProvenance GetInspectedInfrastructureProvenance() const;
    /** Shared screen-centre/controller ray selection; mouse selection uses the same actor proxy. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Builder|Edit")
    bool SelectInfrastructureAlongViewRay(const FVector& RayOrigin, const FVector& RayDirection);
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder|Edit")
    bool IsUsingScreenCentrePlacementCursor() const { return bUseScreenCentrePlacementCursor; }

    /** Player-local operational selection used by the persistent inspector and automation bridge. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Inspection")
    AActor* GetInspectedFactoryActor() const { return InspectedFactoryActor.Get(); }
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Inspection")
    bool SelectFactoryActor(AActor* FactoryActor, bool bFocus = false);
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Inspection")
    void ClearFactoryActorSelection();
    /** Smoothly frames the selected machine, storage zone, press, AGV or support robot. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Inspection")
    bool FocusFactoryActor(AActor* FactoryActor);
    /** Smoothly moves the management camera pivot to a truthful world-space problem marker. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Inspection")
    bool FocusWorldTarget(const FVector& WorldTarget, float ZoomDistanceCm = 3200.0f);
    /** Selects and frames the highest-priority deterministic factory alert. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Inspection")
    bool JumpToTopFactoryAlert();
    /** Infrastructure actors use a floor-level root; their own visuals provide the vertical offset. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder|Edit")
    static FVector SnapInfrastructureRootToFloor(const FVector& FloorImpactPoint)
    {
        return FVector(FMath::GridSnap(FloorImpactPoint.X, 50.0f),
            FMath::GridSnap(FloorImpactPoint.Y, 50.0f), FloorImpactPoint.Z);
    }
    /** Tests the raised volume above a floor-level infrastructure root. */
    static bool IsInfrastructurePreviewEnvelopeObstructed(
        UWorld* World, const FTransform& RootTransform, const FVector& HalfExtent,
        const UPrimitiveComponent* TracedSupportComponent, const FVector& TracedImpactNormal,
        const AActor* IgnoredActor = nullptr);
    UFUNCTION(BlueprintPure, Category="Line Boss|Camera") float GetManagementZoomDistance() const;
    /** Dense process-centred view used for the default populated-factory composition. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Camera") bool FocusBuiltFactory();
    /** Explicit all-actors view retained for Home/reset and wide factory inspection. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Camera") bool FocusWholeBuiltFactory();
    /** Pure whole-factory contract retained for explicit wide inspection. */
    static FLBFactoryOverviewFramingContract BuildFactoryOverviewFramingContract(
        const FBox& RenderableFactoryBounds, int32 FramedActorCount);
    /**
     * Pure default-populated composition contract. Its process span follows the
     * current 1280x720 tray's 229 px height plus 18 px bottom margin.
     */
    static FLBFactoryOverviewFramingContract BuildProcessOverviewFramingContract(
        const FBox& RenderableFactoryBounds, int32 FramedActorCount);
    static constexpr float GetProcessOverviewWorldApertureFraction()
    {
        return (720.0f - 229.0f - 18.0f) / 720.0f;
    }
    /** Frames the first authorised build bay when a new campaign has no machines to focus yet. */
    bool FocusInitialBuildBay();
    /** Deterministic local developer-control camera pose; values retain the normal gameplay zoom limits. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Camera")
    bool SetAutomationCamera(const FVector& WorldLocation, float YawDegrees, float ZoomDistanceCm);
    UFUNCTION(BlueprintPure, Category="Line Boss|Camera") static float GetMinimumManagementZoomDistance() { return 1000.0f; }
    UFUNCTION(BlueprintPure, Category="Line Boss|Camera") static float GetMinimumPlacementZoomDistance() { return 6500.0f; }
    /** Wide enough to frame the complete 189 m ED line without clipping either process port. */
    /**
     * 30,000 cm could not frame a shop, let alone the works: the department bays
     * span 310 m and the station envelope 562 m, which need roughly 35,000 and
     * 63,000 cm at this pawn's field of view. The camera was capped below the
     * size of its own subject.
     */
    UFUNCTION(BlueprintPure, Category="Line Boss|Camera") static float GetMaximumManagementZoomDistance() { return 70000.0f; }
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Management") void SetReturnPawn(ALBControlRoomPawn* InReturnPawn) { ReturnPawn = InReturnPawn; }
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Management") bool ReturnToControlRoom();
    UFUNCTION(BlueprintPure, Category="Cairnwell|Management") ALBControlRoomPawn* GetReturnPawn() const { return ReturnPawn.Get(); }
    /** V / top-face button: legacy maps return to their operator; clean maps toggle the build catalogue. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Management") void UseContextualBuilderShortcut();
    /** Enter / Cross / A confirms the open catalogue or the currently active floor placement. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Management") void UseContextualConfirm();

    /** Development-build shortcut: opens the live build catalogue without any authored control-room path. */
    UFUNCTION(Exec, Category="Line Boss|Developer Test") void LBTestOpenBuilder();

    /** Pure preview helpers used by runtime drawing and focused automation coverage. */
    static FLBPlacementPreviewStyle BuildPlacementPreviewStyle(
        bool bHasFactoryFloor, bool bPlacementAllowed, const FString& AuthorityReason);
    static FLBPlacementPreviewGeometry BuildPlacementPreviewGeometry(
        const FTransform& PreviewTransform, const FVector& EnvelopeRelativeCentre,
        const FVector& EnvelopeHalfExtent, float FloorZ, bool bFlowAlongLocalX,
        bool bShowProcessFlow = true);
    static FLBPlacementPreviewGeometry BuildMachinePlacementPreviewGeometry(
        ELBFactoryBuildMachineType MachineType, const FTransform& PreviewTransform,
        const FVector& EnvelopeRelativeCentre, const FVector& EnvelopeHalfExtent,
        float FloorZ);
    static FString FormatNamedObstructionReason(const FString& EnvelopeLabel,
        const FString& ActorLabel, const FString& ComponentLabel);
    static FLBPlacementCardData BuildPlacementCardData(const FString& ItemTitle,
        const FLBPlacementPreviewStyle& Style, const FString& ObstructionDisplayName = FString(),
        const FString& ObstructionStableId = FString());
    static FLBPlacementCardLayout BuildPlacementCardLayout(const FIntPoint& Viewport,
        float GhostScreenX, bool bForceCardSide = false, bool bForcedCardOnLeft = false);
    static TArray<FString> WrapPlacementCardText(const FString& Text, int32 MaximumCharactersPerLine,
        int32 MaximumLines = 3);
    static FLBPlacementFramingContract BuildPlacementFramingContract(
        const FLBPlacementPreviewGeometry& Geometry, const FIntPoint& Viewport,
        const FLBPlacementCardLayout& CardLayout);
    static FString GetMachinePlacementDisplayName(ELBFactoryBuildMachineType MachineType);
    static FString GetStoragePlacementDisplayName(ELBPressShopStorageType StorageType);
    static FString GetInfrastructurePlacementDisplayName(ELBFactoryAGVInfrastructureType Type);
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Builder|Preview")
    int32 GetPlacementGhostMeshCount() const;
    const FLBPlacementCardData& GetPlacementCardData() const { return PlacementCardData; }

#if WITH_DEV_AUTOMATION_TESTS
    bool BuildPlacementGhostForAutomation(AActor* SourceActor);
#endif

private:
    bool FocusBuiltFactoryInternal(bool bWholeFactory);

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USceneComponent> Pivot;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<USpringArmComponent> CameraBoom;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UCameraComponent> Camera;

    UPROPERTY(VisibleAnywhere)
    TObjectPtr<UWidgetInteractionComponent> WidgetInteraction;

    UPROPERTY()
    TObjectPtr<ALBControlRoomPawn> ReturnPawn;

    float ForwardInput = 0.0f;
    float RightInput = 0.0f;
    float RotateInput = 0.0f;
    float ZoomInput = 0.0f;
    float DesiredZoomDistance = 11000.0f;
    bool bPressTrainPlacementActive = false;
    bool bPressTrainPlacementValid = false;
    ELBFactoryBuildMachineType SelectedMachineType = ELBFactoryBuildMachineType::PressTrain;
    FVector MachinePreviewHalfExtent = FVector(750.0f, 3642.0f, 475.0f);
    FVector MachinePreviewEnvelopeRelativeCentre = FVector(0.0f, 2892.0f, 475.0f);
    float MachinePreviewRootHeightCm = 0.0f;
    FTransform PressTrainPreviewTransform;
    FString PressTrainPlacementReason = TEXT("MOVE CURSOR OVER THE FACTORY FLOOR");
    bool bStoragePlacementActive = false;
    bool bStoragePlacementValid = false;
    ELBPressShopStorageType SelectedStorageType = ELBPressShopStorageType::BareCoils;
    FTransform StoragePreviewTransform;
    FVector StoragePreviewHalfExtent = FVector::ZeroVector;
    int32 StoragePreviewCapacity = 0;
    int32 StoragePreviewColumns = 0;
    int32 StoragePreviewRows = 0;
    bool bStorageDragActive = false;
    FVector StorageDragAnchor = FVector::ZeroVector;
    FString StoragePlacementReason = TEXT("SELECT A STORAGE TYPE");
    bool bInfrastructurePlacementActive = false;
    bool bInfrastructurePlacementValid = false;
    ELBFactoryAGVInfrastructureType SelectedInfrastructureType = ELBFactoryAGVInfrastructureType::PedestrianWalkway;
    int32 SelectedInfrastructureTrainIndex = INDEX_NONE;
    FTransform InfrastructurePreviewTransform;
    FVector InfrastructurePreviewHalfExtent = FVector(250.0f, 75.0f, 2.0f);
    FString InfrastructurePlacementReason = TEXT("SELECT FLOOR INFRASTRUCTURE");
    UPROPERTY(Transient) TObjectPtr<ALBFactoryAGVInfrastructure> InspectedInfrastructure;
    UPROPERTY(Transient) TWeakObjectPtr<AActor> InspectedFactoryActor;
    bool bInfrastructureEditActive = false;
    bool bInfrastructureEditValid = false;
    FTransform InfrastructureEditOriginalTransform;
    FTransform InfrastructureEditPreviewTransform;
    FVector InfrastructureEditHalfExtent = FVector::ZeroVector;
    FString InfrastructureEditReason = TEXT("CLICK A ROUTE OR WALKWAY TO SELECT IT");
    bool bUseScreenCentrePlacementCursor = false;
    bool bFactoryFocusTransitionActive = false;
    FVector FactoryFocusTargetLocation = FVector::ZeroVector;
    FRotator FactoryFocusTargetRotation = FRotator::ZeroRotator;
    TArray<TWeakObjectPtr<UPrimitiveComponent>> FactoryHighlightComponents;
    TArray<bool> FactoryHighlightPreviousCustomDepth;
    TSet<FKey> BrandingKeysDown;
    bool bInitialBuilderHUDReady = false;
    UPROPERTY(Transient) TObjectPtr<AActor> PlacementGhostActor;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> PlacementGhostMaterialParent;
    UPROPERTY(Transient) TArray<TObjectPtr<UMaterialInstanceDynamic>> PlacementGhostMaterials;
    TArray<uint8> PlacementGhostMaterialRoles;
    FLBPlacementCardData PlacementCardData;
    FLBPlacementPreviewGeometry CurrentPlacementGeometry;
    FString CurrentPlacementObstructionDisplayName;
    FString CurrentPlacementObstructionStableId;
    bool bPlacementFramingSideLocked = false;
    bool bPlacementCardOnLeft = false;

    /** v2.1 camera bookmarks: F5-F8 recall a stored framing, Shift+F5-F8
        store the current one. Session-scoped, management view only. */
    struct FLBCameraBookmark
    {
        FVector Location = FVector::ZeroVector;
        float YawDegrees = 0.0f;
        float ZoomDistanceCm = 11000.0f;
        bool bSet = false;
    };
    FLBCameraBookmark CameraBookmarks[4];
    void StoreCameraBookmark(int32 SlotIndex);
    void RecallCameraBookmark(int32 SlotIndex);
    void StoreBookmark0(); void StoreBookmark1();
    void StoreBookmark2(); void StoreBookmark3();
    void RecallBookmark0(); void RecallBookmark1();
    void RecallBookmark2(); void RecallBookmark3();

    void MoveForward(float Value);
    void MoveRight(float Value);
    void Rotate(float Value);
    void Zoom(float Value);
    void ResetCamera();
    void InteractUnderCursor();
    void EndPointerInteraction();
    void ToggleManagement();
    void ManagementNextPage();
    void ManagementPreviousPage();
    void ManagementNextAction();
    void ManagementPreviousAction();
    bool IsManagementOpen() const;
    void UpdatePressTrainPlacementPreview();
    void UpdateStoragePlacementPreview();
    void UpdateInfrastructurePlacementPreview();
    void UpdateInfrastructureEditPreview();
    bool ConfirmStoragePlacement();
    bool ConfirmInfrastructurePlacement();
    bool IsAnyPlacementActive() const { return bPressTrainPlacementActive || bStoragePlacementActive || bInfrastructurePlacementActive || bInfrastructureEditActive; }
    bool TraceFactoryFloorUnderCursor(FHitResult& OutHit) const;
    bool SelectInfrastructureAtScreenCentre();
    bool SelectFactoryActorAtScreenCentre();
    bool SelectFactoryActorAlongViewRay(const FVector& RayOrigin, const FVector& RayDirection,
        bool bFocusIfAlreadySelected = false);
    void RestoreFactorySelectionHighlight();
    void ApplyFactorySelectionHighlight(AActor* FactoryActor);
    void UpdateFactoryFocusTransition(float DeltaSeconds);
    void PollFactoryNameKeyboard();
    void DestroyPlacementGhost();
    bool BuildPlacementGhostFromActor(AActor* SourceActor);
    bool BuildMachinePlacementGhost(ELBFactoryBuildMachineType MachineType);
    bool BuildStoragePlacementGhost();
    bool BuildInfrastructurePlacementGhost(ELBFactoryAGVInfrastructureType Type,
        int32 TrainIndex, const AActor* ExistingSource = nullptr);
    void UpdatePlacementGhostTransform(const FTransform& Transform,
        const FLBPlacementPreviewStyle& Style);
    void UpdatePlacementPresentation(const FString& ItemTitle,
        const FLBPlacementPreviewGeometry& Geometry, const FLBPlacementPreviewStyle& Style);
    void UpdatePlacementFraming(const FLBPlacementPreviewGeometry& Geometry);
    void DrawPlacementCard(UCanvas* Canvas) const;
    FString ResolveCurrentPlacementTitle() const;
    void ResetPlacementPresentation();
};
