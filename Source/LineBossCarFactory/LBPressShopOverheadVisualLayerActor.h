#pragma once

#include "CoreMinimal.h"
#include "Engine/StaticMeshActor.h"
#include "LBPressShopOverheadVisualLayerActor.generated.h"

/**
 * Runtime meaning of one true-overhead press-shop sprite layer.
 *
 * The layer remains presentation-only: it never owns WIP, station state or
 * collision.  The companion presentation actor reads the canonical
 * OneFactory ledger/coordinator and decides which layers are visible.
 */
UENUM(BlueprintType)
enum class ELBPressShopOverheadLayerRole : uint8
{
    Base,
    FrameState,
    Workpiece,
    MovingOverlay,
    ContactEffect,
    CyanTransfer,
    BeaconGlow,
    TaskLightGlow,
    ConveyorMotion,
    RobotPose
};

/**
 * One imported RGBA sprite plane in the isolated 2126 overhead candidate.
 *
 * A dedicated actor gives packaged C++ stable metadata without relying on
 * editor-only actor labels or Python at runtime.  The source image, material
 * and plane are supplied by the guarded import lane; this class only carries
 * the gameplay binding contract.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPressShopOverheadVisualLayerActor final :
    public AStaticMeshActor
{
    GENERATED_BODY()

public:
    ALBPressShopOverheadVisualLayerActor();

    virtual void PostRegisterAllComponents() override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead")
    FName LayerId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead")
    FName AssemblyId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead")
    FName MachineId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead")
    ELBPressShopOverheadLayerRole LayerRole =
        ELBPressShopOverheadLayerRole::Base;

    /** OPEN/DESCENDING/CONTACT/RISING, robot pose, or beacon colour. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead")
    FName StateId = NAME_None;

    /** Stable descriptive binding such as INBOUND_UNLOAD or PRESS_S02_Z. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead")
    FName MotionChannel = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead|Motion")
    bool bHasMotionRange = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead|Motion",
        meta=(EditCondition="bHasMotionRange"))
    FTransform MotionStart = FTransform::Identity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead|Motion",
        meta=(EditCondition="bHasMotionRange"))
    FTransform MotionEnd = FTransform::Identity;

    /**
     * Optional exact texture-frame selector for layered sprite animation.
     * INDEX_NONE/zero means this is not a sequence frame.  When enabled, every
     * sibling in the same MotionChannel carries one unique zero-based index and
     * the same count; the presentation controller exposes exactly one frame.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead|Sequence",
        meta=(ClampMin="-1"))
    int32 SequenceFrameIndex = INDEX_NONE;

    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead|Sequence",
        meta=(ClampMin="0"))
    int32 SequenceFrameCount = 0;

    /** Looping is for rollers/belts; one-shot scans clamp on their last frame. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite,
        Category="Cairnwell|Press Shop|Overhead|Sequence")
    bool bSequenceLoops = false;

    /** Makes the presentation controller's intent explicit and testable. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Press Shop|Overhead")
    void ApplyPresentationState(bool bVisible, float MotionAlpha01);

    /** Invalid or partial sequence metadata fails closed (the layer is hidden). */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Shop|Overhead|Sequence")
    bool IsSequenceFrameVisible(float NormalizedSequenceProgress) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Press Shop|Overhead")
    static FName GetLayerTag();
};
