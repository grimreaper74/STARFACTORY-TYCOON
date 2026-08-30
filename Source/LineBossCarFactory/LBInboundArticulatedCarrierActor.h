#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBInboundArticulatedCarrierActor.generated.h"

class UBoxComponent;
class USceneComponent;

/**
 * Native kinematic authority for the IN-01A tractor + IN-01B trailer pair.
 *
 * The registered sprite cards remain presentation-only and attach to the two
 * presentation anchors.  These hidden rectangular proxies own collision and
 * the trailer rotates only about the coincident native hitch components.  The
 * actor owns no delivery inventory and therefore cannot duplicate the inbound
 * controller's gameplay authority.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBInboundArticulatedCarrierActor : public AActor
{
    GENERATED_BODY()

public:
    ALBInboundArticulatedCarrierActor();

    /** Exact registered v001 parked contract, expressed in Unreal centimetres. */
    static constexpr float TractorLengthCm = 480.0f;
    static constexpr float TractorWidthCm = 255.0f;
    static constexpr float TractorHitchLocalXCm = 215.0f;
    static constexpr float TrailerLengthCm = 1220.0f;
    static constexpr float TrailerWidthCm = 255.0f;
    static constexpr float TrailerHitchLocalXCm = -585.0f;
    static constexpr float ParkedEnvelopeLengthCm = 1650.0f;
    static constexpr float ParkedCentreSeparationCm = 800.0f;
    static constexpr float HitchOverlapCm = 50.0f;

    /**
     * Applies a new tractor pose while retaining the previous trailer centre as
     * the kinematic tracking point.  This is the forward-pull path operation;
     * large teleports, pitched/scaled poses, and jack-knifed steps fail closed
     * without mutating either body.
     */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery|Articulated Carrier")
    bool AdvanceTractorPoseAndSolveTrailer(const FTransform& NewTractorWorldTransform,
        FString& OutReason);

    /** Teleport/reset operation for load, spawn and deterministic route restart. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery|Articulated Carrier")
    bool ResetStraightAtTractorPose(const FTransform& NewTractorWorldTransform,
        FString& OutReason);

    /** Manual reverse/docking authority may set a proved yaw directly. */
    UFUNCTION(BlueprintCallable, Category="Cairnwell|Inbound Delivery|Articulated Carrier")
    bool SetTrailerRelativeYawDegrees(float NewRelativeYawDegrees, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Articulated Carrier")
    float GetTrailerRelativeYawDegrees() const;
    /** Pure save/load validation; unlike the setter this never mutates the hitch. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Articulated Carrier")
    bool IsTrailerRelativeYawWithinLimits(float CandidateRelativeYawDegrees) const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Articulated Carrier")
    FVector GetTractorHitchWorldLocation() const;
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Articulated Carrier")
    FVector GetTrailerBodyCentreWorldLocation() const;

    /** Visual-only cards attach here with KeepRelative transform. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Articulated Carrier|Presentation")
    USceneComponent* GetTractorPresentationAnchor() const { return TractorPresentationAnchor; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Articulated Carrier|Presentation")
    USceneComponent* GetTrailerPresentationAnchor() const { return TrailerPresentationAnchor; }

    /** Separate wrapped-coil actors attach below this root; inventory stays external. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Articulated Carrier|Cargo")
    USceneComponent* GetTrailerCargoRoot() const { return TrailerCargoRoot; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Articulated Carrier|Collision")
    UBoxComponent* GetTractorAuthorityProxy() const { return TractorAuthorityProxy; }
    UFUNCTION(BlueprintPure, Category="Cairnwell|Inbound Delivery|Articulated Carrier|Collision")
    UBoxComponent* GetTrailerAuthorityProxy() const { return TrailerAuthorityProxy; }

    static FName GetAuthorityTag();

private:
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> SceneRoot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> TractorAuthorityProxy;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> TractorPresentationAnchor;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> TractorHitch;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> TrailerYawPivot;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> TrailerBodyCentre;
    UPROPERTY(VisibleAnywhere) TObjectPtr<UBoxComponent> TrailerAuthorityProxy;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> TrailerPresentationAnchor;
    UPROPERTY(VisibleAnywhere) TObjectPtr<USceneComponent> TrailerCargoRoot;

    /** Planar authority height; footprint dimensions come from the registered art contract. */
    UPROPERTY(EditDefaultsOnly, Category="Cairnwell|Inbound Delivery|Articulated Carrier|Collision",
        meta=(ClampMin="10.0"))
    float AuthorityHeightCm = 100.0f;

    UPROPERTY(EditDefaultsOnly, Category="Cairnwell|Inbound Delivery|Articulated Carrier|Motion",
        meta=(ClampMin="5.0", ClampMax="89.0"))
    float MaximumArticulationDegrees = 82.0f;

    /** Bounds one solver step so a dropped frame cannot tunnel the trailer through a corner. */
    UPROPERTY(EditDefaultsOnly, Category="Cairnwell|Inbound Delivery|Articulated Carrier|Motion",
        meta=(ClampMin="10.0"))
    float MaximumSolverStepCm = 220.0f;

    bool IsValidPlanarPose(const FTransform& Transform, FString& OutReason) const;
    void ApplyTrailerRelativeYawUnchecked(float NewRelativeYawDegrees);
    static void ConfigureAuthorityProxy(UBoxComponent* Proxy);
};
