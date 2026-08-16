#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBControlRoomCCTVFeed.generated.h"

class UMaterialInstanceDynamic;
class UMaterialInterface;
class USceneCaptureComponent2D;
class USceneComponent;
class UStaticMeshComponent;
class UTextureRenderTarget2D;

/**
 * Reusable selected-feed terminal for the seated control room.
 *
 * The capture renders the actual streamed factory world. Selected feeds update
 * continuously; inactive feeds can be throttled without replacing them with
 * fictitious UI imagery.
 */
UCLASS()
class LINEBOSSCARFACTORY_API ALBControlRoomCCTVFeed : public AActor
{
    GENERATED_BODY()

public:
    ALBControlRoomCCTVFeed();
    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|CCTV")
    void SetSelectedFeed(bool bSelected);

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|CCTV")
    bool IsSelectedFeed() const { return bSelectedFeed; }

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|CCTV")
    UTextureRenderTarget2D* GetRenderTarget() const { return RenderTarget; }

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|CCTV")
    UStaticMeshComponent* GetDisplaySurface() const { return DisplaySurface; }

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|CCTV")
    USceneCaptureComponent2D* GetCaptureComponent() const { return SceneCapture; }

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Control Room|CCTV")
    float GetCaptureExposureBias() const { return CaptureExposureBias; }

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Control Room|CCTV")
    void SetCaptureTransform(const FVector& WorldLocation, const FRotator& WorldRotation);

private:
    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|CCTV")
    TObjectPtr<USceneComponent> FeedRoot;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|CCTV")
    TObjectPtr<UStaticMeshComponent> DisplaySurface;

    UPROPERTY(VisibleAnywhere, Category = "Cairnwell|Control Room|CCTV")
    TObjectPtr<USceneCaptureComponent2D> SceneCapture;

    UPROPERTY(Transient)
    TObjectPtr<UTextureRenderTarget2D> RenderTarget;

    UPROPERTY(Transient)
    TObjectPtr<UMaterialInstanceDynamic> DisplayMaterial;

    UPROPERTY(EditAnywhere, Category = "Cairnwell|Control Room|CCTV")
    TSoftObjectPtr<UMaterialInterface> FeedMaterial;

    UPROPERTY(EditAnywhere, Category = "Cairnwell|Control Room|CCTV")
    FVector CaptureWorldLocation = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, Category = "Cairnwell|Control Room|CCTV")
    FRotator CaptureWorldRotation = FRotator::ZeroRotator;

    UPROPERTY(EditAnywhere, Category = "Cairnwell|Control Room|CCTV", meta = (ClampMin = "320", ClampMax = "3840"))
    int32 CaptureWidth = 1280;

    UPROPERTY(EditAnywhere, Category = "Cairnwell|Control Room|CCTV", meta = (ClampMin = "180", ClampMax = "2160"))
    int32 CaptureHeight = 720;

    UPROPERTY(EditAnywhere, Category = "Cairnwell|Control Room|CCTV", meta = (ClampMin = "20.0", ClampMax = "120.0"))
    float CaptureFieldOfView = 62.0f;

    UPROPERTY(EditAnywhere, Category = "Cairnwell|Control Room|CCTV", meta = (ClampMin = "-5.0", ClampMax = "5.0"))
    float CaptureExposureBias = 0.5f;

    UPROPERTY(EditAnywhere, Category = "Cairnwell|Control Room|CCTV")
    bool bSelectedFeed = false;
};
