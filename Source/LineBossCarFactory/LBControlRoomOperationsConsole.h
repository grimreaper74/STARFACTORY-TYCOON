#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBControlRoomOperationsConsole.generated.h"

class ALBPR005Station;
class ALBPR006Station;
class ALBPR007Station;
class ALBPR008Station;
class ALBPR009Station;
class ALBPR010Station;
class ALBPressTrainAStation;
class ALBPressShopSupportFleetController;
class ALBPressShopMaterialFlowController;
class UBoxComponent;
class UPrimitiveComponent;
class USceneComponent;
class UStaticMeshComponent;
class UTextRenderComponent;
class UMaterialInterface;
class UStaticMesh;

UENUM(BlueprintType)
enum class ELBControlRoomOperatingMode : uint8
{
    Automatic,
    AssistedManual
};

UENUM(BlueprintType)
enum class ELBControlRoomOrderPriority : uint8
{
    Normal,
    High,
    Urgent
};

UENUM(BlueprintType)
enum class ELBControlRoomOrderState : uint8
{
    Draft,
    Ready,
    Running,
    Paused,
    Completed,
    Held
};

/** Saveable control-room planning state. Machine state remains authoritative in each station save record. */
USTRUCT(BlueprintType)
struct FLBControlRoomOperationsSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 Version = 2;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName PanelFamily = TEXT("ROOF_OUTER");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName AssignedTrain = TEXT("TRAIN_A");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FGuid AssignedTrainGuid;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName RecipeId = NAME_None;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 RequestedQuantity = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBControlRoomOrderPriority Priority = ELBControlRoomOrderPriority::Normal;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBControlRoomOperatingMode OperatingMode = ELBControlRoomOperatingMode::Automatic;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) ELBControlRoomOrderState OrderState = ELBControlRoomOrderState::Draft;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString SelectedCoilId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float SelectedCoilWidthMillimetres = 0.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 GoodPanels = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 RejectedPanels = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) float RemainingMaterialMetres = -1.0f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString BufferStatus = TEXT("AUTHORITY LINK PENDING");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FString LastAlarm = TEXT("CREATE A PRODUCTION ORDER");
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextOrchestrationTransactionSerial = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) FName ActiveReleasedStackId;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame) int32 NextReleasedBlankIndex = 0;
};

/**
 * Walk-up Press Shop operations terminal for the Moorcross Works control room.
 *
 * The terminal owns planning state only. Load/start/stop requests are routed to
 * an existing PR-005 authority actor and never bootstrap, certify or bypass it.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBControlRoomOperationsConsole : public AActor
{
    GENERATED_BODY()

public:
    ALBControlRoomOperationsConsole();
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations")
    bool HandleComponentInteraction(UPrimitiveComponent* HitComponent);

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") void CyclePanelFamily();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") void IncreaseQuantity();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") void DecreaseQuantity();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") void CyclePriority();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") void CycleAssignedTrain();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") void ToggleOperatingMode();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") bool CreateProductionOrder();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") bool SelectAvailableCoil();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") bool LoadSelectedCoil();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") bool StartOrResumeOrder();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") bool PauseOrder();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations") bool StopOrder();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Support Fleet") void CycleSupportUnit();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Support Fleet") bool DispatchSelectedSupportUnit();
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Support Fleet") bool RecallSelectedSupportUnit();
    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Support Fleet")
    ALBPressShopSupportFleetController* GetBoundSupportFleet() const { return BoundSupportFleet.Get(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Support Fleet")
    FName GetSelectedSupportUnitId() const { return SelectedSupportUnitId; }

    /** Integration endpoint for future panel-counter authority; never advanced by presentation time. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations")
    bool RecordAuthoritativePanelResult(bool bAccepted, float RemainingMaterialInMetres, const FString& NewBufferStatus);

    /** Integration endpoint populated only by an authoritative recipe catalogue. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Operations")
    bool ResolveRecipeAuthority(FName AuthoritativeRecipeId, float RequiredStripWidthMillimetres);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Save")
    FLBControlRoomOperationsSaveState CaptureSaveState() const { return State; }

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Save")
    bool RestoreSaveState(const FLBControlRoomOperationsSaveState& SavedState);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Operations")
    ALBPR005Station* GetBoundPR005Station() const { return BoundPR005.Get(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Operations") ALBPR006Station* GetBoundPR006Station() const { return BoundPR006.Get(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Operations") ALBPR007Station* GetBoundPR007Station() const { return BoundPR007.Get(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Operations") ALBPR008Station* GetBoundPR008Station() const { return BoundPR008.Get(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Operations") ALBPR009Station* GetBoundPR009Station() const { return BoundPR009.Get(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Operations") ALBPR010Station* GetBoundPR010Station() const { return BoundPR010.Get(); }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Operations")
    ALBPressShopMaterialFlowController* GetBoundMaterialFlow() const { return BoundMaterialFlow.Get(); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Control Room|Operations")
    ALBPressTrainAStation* GetAssignedPressTrain() const;

    /** Deterministic editor evidence refresh; does not execute or mutate machine authority. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Control Room|Validation")
    void RefreshForEditorEvidence();

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> ConsoleRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> ScreenBack;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UStaticMeshComponent> ScreenBezel;
    UPROPERTY(Transient) TObjectPtr<UStaticMesh> PrimitiveCubeMesh;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> ScreenFaceMaterial;
    UPROPERTY(Transient) TObjectPtr<UMaterialInterface> ButtonFaceMaterial;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UTextRenderComponent> HeaderText;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UTextRenderComponent> OrderText;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UTextRenderComponent> ProductionText;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UTextRenderComponent> AuthorityText;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UTextRenderComponent> AlarmText;

    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> PanelButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> QuantityDownButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> QuantityUpButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> PriorityButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> TrainButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> ModeButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> CreateButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> SelectCoilButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> LoadCoilButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> StartButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> PauseButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> StopButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> SupportUnitButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> SupportDispatchButton;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> SupportRecallButton;

    UPROPERTY(EditAnywhere, SaveGame, Category="Cairnwell|Control Room|Operations")
    FLBControlRoomOperationsSaveState State;

    UPROPERTY(Transient) TWeakObjectPtr<ALBPR005Station> BoundPR005;
    UPROPERTY(Transient) TWeakObjectPtr<ALBPR006Station> BoundPR006;
    UPROPERTY(Transient) TWeakObjectPtr<ALBPR007Station> BoundPR007;
    UPROPERTY(Transient) TWeakObjectPtr<ALBPR008Station> BoundPR008;
    UPROPERTY(Transient) TWeakObjectPtr<ALBPR009Station> BoundPR009;
    UPROPERTY(Transient) TWeakObjectPtr<ALBPR010Station> BoundPR010;
    UPROPERTY(Transient) TWeakObjectPtr<ALBPressShopMaterialFlowController> BoundMaterialFlow;
    UPROPERTY(Transient) TWeakObjectPtr<ALBPressShopSupportFleetController> BoundSupportFleet;
    TMap<FName, TWeakObjectPtr<ALBPressTrainAStation>> BoundPressTrains;
    FName SelectedSupportUnitId = TEXT("LB-CR01-01");
    float ResolvedRequiredStripWidthMillimetres = 0.0f;
    float RefreshAccumulator = 0.0f;

    UTextRenderComponent* CreateText(const TCHAR* Name, float LocalZ, float WorldSize, const FColor& Colour);
    UBoxComponent* CreateInteractionButton(const TCHAR* Name, float LocalY, float LocalZ, const TCHAR* Label);
    void BindExistingAuthority();
    void RefreshPresentation();
    void SetHold(const FString& Reason);
    bool HasExecutableOrder() const;
    void AdvanceAutomaticOrder();
    FName MakeOrchestrationTransactionId(const TCHAR* Stage);
    bool RecordAuthoritativePanelWithoutMaterialEstimate(const FString& NewBufferStatus);
    void RequestWholeLineControlledStop();
};
