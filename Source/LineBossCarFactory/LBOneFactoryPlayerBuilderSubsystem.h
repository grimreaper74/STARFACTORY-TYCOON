#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBOneFactoryAssemblyStarterLayout.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryPlayerBuilderSubsystem.generated.h"

class ALBFactoryBuildMachine;
class ALBOneFactoryBootstrap;
class ALBOneFactoryAssemblyStarterPresentationActor;
class ALBOneFactoryBodyWeldStarterPresentationActor;
class ALBOneFactoryPaintStarterPresentationActor;
class ALBOneFactoryProductionFlowAuthority;
class ALBOneFactoryRuntimeCoordinator;
class ALBOneFactoryPressStarterLayoutAuthority;
class ALBOneFactoryPressStarterPresentationActor;
struct FLBOneFactorySaveState;
struct FLBOneFactoryPressStarterLayoutState;

/** The exact kind of live object selected by the native OneFactory builder. */
UENUM(BlueprintType)
enum class ELBOneFactoryBuilderTargetKind : uint8
{
    None,
    PressStarterStation,
    PlayerBuildMachine,
    AssemblyStarterPosition,
    PaintStarterStation,
    BodyWeldStarterPosition
};

/** Small view model consumed by the existing native UMG management surface. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryBuilderUMGAction
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly)
    int32 ActionIndex = INDEX_NONE;

    UPROPERTY(BlueprintReadOnly)
    FString Title;

    UPROPERTY(BlueprintReadOnly)
    FString Detail;

    UPROPERTY(BlueprintReadOnly)
    bool bEnabled = false;
};

/**
 * Native-UMG orchestration for the dedicated OneFactory map.
 *
 * The protected map stays an empty shell. The explicit lifecycle advances through
 * Press, Body/Weld, black-box Paint and Assembly. Each starter creates canonical data, then
 * materialises its exact native presentation as a separate phase; either both
 * phases commit or both newly-created actors are destroyed. Gameplay edits keep
 * each data authority and presentation in the same atomic transaction.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryPlayerBuilderSubsystem :
    public UWorldSubsystem
{
    GENERATED_BODY()

public:
    static constexpr int32 UMGActionCount = 5;

    /** True when at least one OneFactory bootstrap marks this as its builder world. */
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Player Builder")
    bool IsOneFactoryBuilderWorld() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Player Builder|UMG")
    TArray<FLBOneFactoryBuilderUMGAction> GetUMGActions() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Player Builder|UMG")
    FString GetUMGSummary() const;

    /** Executes one of the five stable UMG actions and retains its exact result reason. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder|UMG")
    bool ExecuteUMGAction(int32 ActionIndex, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Player Builder")
    FString GetLastActionReason() const { return LastActionReason; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Player Builder")
    ELBOneFactoryBuilderTargetKind GetSelectedTargetKind() const
    { return SelectedTargetKind; }

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Player Builder")
    FName GetSelectedTargetId() const { return SelectedTargetId; }

    /** Atomic data + presentation creation; commission remains an explicit player action. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder")
    bool CreateNewFactory(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder")
    bool CommissionPressStarter(FString& OutReason);

    /** Atomic configurable Body/Weld data + native robot-line presentation. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder")
    bool CreateBodyWeldStarter(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder")
    bool CommissionBodyWeldStarter(FString& OutReason);

    /** Removes only a complete idle pair; downstream Paint/Assembly block it. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder")
    bool RemoveBodyWeldStarter(FString& OutReason);

    /** Atomic configurable Assembly data + exact native presentation creation. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder")
    bool CreateAssemblyStarter(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder")
    bool CommissionAssemblyStarter(FString& OutReason);

    /** Atomic black-box Paint data + exact native presentation creation. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder")
    bool CreatePaintStarter(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder")
    bool CommissionPaintStarter(FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Player Builder")
    bool SelectNextTarget(FString& OutReason);

    /**
     * C++ restore seam used only after a validated fresh-shell save preflight.
     * It materialises the four exact data/presentation pairs and reports every
     * newly created actor so the save transaction can destroy them on rollback.
     */
    bool MaterialiseFactoryForRestore(const FLBOneFactorySaveState& State,
        TArray<AActor*>& OutCreatedActors, FString& OutReason);

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Player Builder|Assembly")
    bool HasSelectedAssemblyOperation() const
    { return bHasSelectedAssemblyOperation; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Player Builder|Assembly")
    ELBOneFactoryAssemblyOperation GetSelectedAssemblyOperation() const
    { return SelectedAssemblyOperation; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Player Builder|Body Weld")
    bool HasSelectedBodyWeldProgramme() const
    { return bHasSelectedBodyWeldProgramme; }

    UFUNCTION(BlueprintPure,
        Category="Line Boss|OneFactory|Player Builder|Body Weld")
    ELBOneFactoryBodyWeldProgramme GetSelectedBodyWeldProgramme() const
    { return SelectedBodyWeldProgramme; }

#if WITH_DEV_AUTOMATION_TESTS
    /** Deterministic fault injection proving the data/presentation rollback boundary. */
    void SetForcePresentationFailureForTests(const bool bForce)
    { bForcePresentationFailureForTests = bForce; }

    void SetForceAssemblyPresentationFailureForTests(const bool bForce)
    { bForceAssemblyPresentationFailureForTests = bForce; }

    void SetForcePaintPresentationFailureForTests(const bool bForce)
    { bForcePaintPresentationFailureForTests = bForce; }

    void SetForceBodyWeldPresentationFailureForTests(const bool bForce)
    { bForceBodyWeldPresentationFailureForTests = bForce; }
#endif

private:
    struct FSelectableTarget
    {
        ELBOneFactoryBuilderTargetKind Kind =
            ELBOneFactoryBuilderTargetKind::None;
        FName Id = NAME_None;
        FString Label;
    };

    bool FindSingleBootstrap(ALBOneFactoryBootstrap*& OutBootstrap,
        FString& OutReason) const;
    bool FindStarterPair(ALBOneFactoryPressStarterLayoutAuthority*& OutAuthority,
        ALBOneFactoryPressStarterPresentationActor*& OutPresentation,
        FString& OutReason) const;
    bool FindAssemblyStarterPair(
        ALBOneFactoryAssemblyStarterLayoutAuthority*& OutAuthority,
        ALBOneFactoryAssemblyStarterPresentationActor*& OutPresentation,
        FString& OutReason) const;
    bool FindBodyWeldStarterPair(
        ALBOneFactoryBodyWeldStarterLayoutAuthority*& OutAuthority,
        ALBOneFactoryBodyWeldStarterPresentationActor*& OutPresentation,
        FString& OutReason) const;
    bool FindPaintStarterPair(
        ALBOneFactoryPaintStarterLayoutAuthority*& OutAuthority,
        ALBOneFactoryPaintStarterPresentationActor*& OutPresentation,
        FString& OutReason) const;
    bool FindRuntimeBackbone(
        ALBOneFactoryProductionFlowAuthority*& OutProduction,
        ALBOneFactoryRuntimeCoordinator*& OutCoordinator,
        FString& OutReason) const;
    void CollectSelectableTargets(TArray<FSelectableTarget>& OutTargets) const;
    bool ResolveSelectedStarter(
        ALBOneFactoryPressStarterLayoutAuthority*& OutAuthority,
        int32& OutStationIndex, FString& OutReason) const;
    bool ResolveSelectedAssembly(
        ALBOneFactoryAssemblyStarterLayoutAuthority*& OutAuthority,
        int32& OutStationIndex, FString& OutReason) const;
    bool ResolveSelectedBodyWeld(
        ALBOneFactoryBodyWeldStarterLayoutAuthority*& OutAuthority,
        int32& OutStationIndex, FString& OutReason) const;
    bool ResolveSelectedPaint(
        ALBOneFactoryPaintStarterLayoutAuthority*& OutAuthority,
        int32& OutStationIndex, FString& OutReason) const;
    bool ResolveSelectedMachine(ALBFactoryBuildMachine*& OutMachine,
        FString& OutReason) const;

    bool CanCreateNewFactory(FString& OutReason) const;
    bool CanCommissionPressStarter(FString& OutReason) const;
    bool CanCreateBodyWeldStarter(FString& OutReason) const;
    bool CanCommissionBodyWeldStarter(FString& OutReason) const;
    bool CanRemoveBodyWeldStarter(FString& OutReason) const;
    bool CanCreateAssemblyStarter(FString& OutReason) const;
    bool CanCommissionAssemblyStarter(FString& OutReason) const;
    bool CanCreatePaintStarter(FString& OutReason) const;
    bool CanCommissionPaintStarter(FString& OutReason) const;
    bool CanChangeSelectedProgramme(FString& OutReason) const;
    bool CanChangeSelectedPaintProgramme(FString& OutReason) const;
    bool CanSelectNextCompatibleBodyWeldProgramme(FString& OutReason) const;
    bool CanApplySelectedBodyWeldConfiguration(FString& OutReason) const;
    bool CanSelectNextCompatibleAssemblyOperation(FString& OutReason) const;
    bool CanAssignSelectedAssemblyOperation(FString& OutReason) const;
    bool CanMoveSelected(FString& OutReason) const;
    bool CanDisconnectSelected(FString& OutReason) const;
    bool CanRemoveSelected(FString& OutReason) const;

    bool CreateStarterData(
        ALBOneFactoryPressStarterLayoutAuthority*& OutAuthority,
        FString& OutReason);
    bool MaterialiseStarterPresentation(
        ALBOneFactoryPressStarterLayoutAuthority& Authority,
        ALBOneFactoryPressStarterPresentationActor*& OutPresentation,
        FString& OutReason);
    bool CreateBodyWeldStarterData(
        ALBOneFactoryBodyWeldStarterLayoutAuthority*& OutAuthority,
        FString& OutReason);
    bool MaterialiseBodyWeldStarterPresentation(
        ALBOneFactoryBodyWeldStarterLayoutAuthority& Authority,
        ALBOneFactoryBodyWeldStarterPresentationActor*& OutPresentation,
        FString& OutReason);
    bool CreateAssemblyStarterData(
        ALBOneFactoryAssemblyStarterLayoutAuthority*& OutAuthority,
        FString& OutReason);
    bool MaterialiseAssemblyStarterPresentation(
        ALBOneFactoryAssemblyStarterLayoutAuthority& Authority,
        ALBOneFactoryAssemblyStarterPresentationActor*& OutPresentation,
        FString& OutReason);
    bool CreatePaintStarterData(
        ALBOneFactoryPaintStarterLayoutAuthority*& OutAuthority,
        FString& OutReason);
    bool MaterialisePaintStarterPresentation(
        ALBOneFactoryPaintStarterLayoutAuthority& Authority,
        ALBOneFactoryPaintStarterPresentationActor*& OutPresentation,
        FString& OutReason);
    bool ValidateStarterPair(
        const ALBOneFactoryPressStarterLayoutAuthority& Authority,
        const ALBOneFactoryPressStarterPresentationActor& Presentation,
        FString& OutReason) const;
    bool ValidateBodyWeldStarterPair(
        const ALBOneFactoryBodyWeldStarterLayoutAuthority& Authority,
        const ALBOneFactoryBodyWeldStarterPresentationActor& Presentation,
        FString& OutReason) const;
    bool ValidateAssemblyStarterPair(
        const ALBOneFactoryAssemblyStarterLayoutAuthority& Authority,
        const ALBOneFactoryAssemblyStarterPresentationActor& Presentation,
        FString& OutReason) const;
    bool ValidatePaintStarterPair(
        const ALBOneFactoryPaintStarterLayoutAuthority& Authority,
        const ALBOneFactoryPaintStarterPresentationActor& Presentation,
        FString& OutReason) const;
    bool SynchronisePresentationOrRestore(
        ALBOneFactoryPressStarterLayoutAuthority& Authority,
        ALBOneFactoryPressStarterPresentationActor& Presentation,
        const FLBOneFactoryPressStarterLayoutState& Before,
        const TCHAR* Operation, FString& OutReason) const;
    bool SynchroniseBodyWeldPresentationOrRestore(
        ALBOneFactoryBodyWeldStarterLayoutAuthority& Authority,
        ALBOneFactoryBodyWeldStarterPresentationActor& Presentation,
        const FLBOneFactoryBodyWeldLayoutState& Before,
        const TCHAR* Operation, FString& OutReason) const;
    bool SynchroniseAssemblyPresentationOrRestore(
        ALBOneFactoryAssemblyStarterLayoutAuthority& Authority,
        ALBOneFactoryAssemblyStarterPresentationActor& Presentation,
        const FLBOneFactoryAssemblyLayoutState& Before,
        const TCHAR* Operation, FString& OutReason) const;
    bool SynchronisePaintPresentationOrRestore(
        ALBOneFactoryPaintStarterLayoutAuthority& Authority,
        ALBOneFactoryPaintStarterPresentationActor& Presentation,
        const FLBOneFactoryPaintStarterLayoutState& Before,
        const TCHAR* Operation, FString& OutReason) const;

    bool ChangeSelectedProgramme(FString& OutReason);
    bool SelectNextCompatibleBodyWeldProgramme(FString& OutReason);
    bool ApplySelectedBodyWeldConfiguration(FString& OutReason);
    bool ChangeSelectedPaintProgramme(FString& OutReason);
    bool SelectNextCompatibleAssemblyOperation(FString& OutReason);
    bool AssignSelectedAssemblyOperation(FString& OutReason);
    bool MoveSelected(FString& OutReason);
    bool DisconnectSelected(FString& OutReason);
    bool RemoveSelected(FString& OutReason);
    FName GetNextPanelProgramme(FName CurrentPanelTypeId) const;
    ELBOneFactoryPaintColour GetNextPaintColour(
        ELBOneFactoryPaintColour CurrentColour) const;
    FString DescribeSelectedTarget() const;
    void SetLastResult(bool bSucceeded, const FString& Reason,
        FString& OutReason);

    UPROPERTY(Transient)
    ELBOneFactoryBuilderTargetKind SelectedTargetKind =
        ELBOneFactoryBuilderTargetKind::None;

    UPROPERTY(Transient)
    FName SelectedTargetId = NAME_None;

    UPROPERTY(Transient)
    ELBOneFactoryAssemblyOperation SelectedAssemblyOperation =
        ELBOneFactoryAssemblyOperation::PaintedBodyReceive;

    UPROPERTY(Transient)
    bool bHasSelectedAssemblyOperation = false;

    UPROPERTY(Transient)
    ELBOneFactoryBodyWeldProgramme SelectedBodyWeldProgramme =
        ELBOneFactoryBodyWeldProgramme::PressedPanelReceive;

    UPROPERTY(Transient)
    bool bHasSelectedBodyWeldProgramme = false;

    UPROPERTY(Transient)
    FString LastActionReason = TEXT("NEW FACTORY HAS NOT BEEN CREATED");

    UPROPERTY(Transient)
    bool bLastActionSucceeded = false;

#if WITH_DEV_AUTOMATION_TESTS
    bool bForcePresentationFailureForTests = false;
    bool bForceAssemblyPresentationFailureForTests = false;
    bool bForcePaintPresentationFailureForTests = false;
    bool bForceBodyWeldPresentationFailureForTests = false;
#endif
};
