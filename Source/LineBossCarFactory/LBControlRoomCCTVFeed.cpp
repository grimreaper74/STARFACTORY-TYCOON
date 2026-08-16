#include "LBControlRoomCCTVFeed.h"

#include "Components/SceneCaptureComponent2D.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Scene.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ALBControlRoomCCTVFeed::ALBControlRoomCCTVFeed()
{
    PrimaryActorTick.bCanEverTick = false;

    FeedRoot = CreateDefaultSubobject<USceneComponent>(TEXT("CCTVFeedRoot"));
    SetRootComponent(FeedRoot);

    DisplaySurface = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CCTVDisplaySurface"));
    DisplaySurface->SetupAttachment(FeedRoot);
    DisplaySurface->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    DisplaySurface->SetCollisionObjectType(ECC_WorldDynamic);
    DisplaySurface->SetCollisionResponseToAllChannels(ECR_Ignore);
    DisplaySurface->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    DisplaySurface->SetCanEverAffectNavigation(false);
    DisplaySurface->SetCastShadow(false);
    // The authored Camera Overview wall panel is 1.30 x 0.58 m and faces
    // south toward the seated player after Blender-to-Unreal Y conversion.
    DisplaySurface->SetRelativeRotation(FRotator(0.0f, 0.0f, 90.0f));
    DisplaySurface->SetRelativeScale3D(FVector(1.30f, 0.58f, 1.0f));

    static ConstructorHelpers::FObjectFinder<UStaticMesh> PlaneMesh(TEXT("/Engine/BasicShapes/Plane.Plane"));
    if (PlaneMesh.Succeeded())
    {
        DisplaySurface->SetStaticMesh(PlaneMesh.Object);
    }

    SceneCapture = CreateDefaultSubobject<USceneCaptureComponent2D>(TEXT("SelectedCCTVSceneCapture"));
    SceneCapture->SetupAttachment(FeedRoot);
    SceneCapture->CaptureSource = ESceneCaptureSource::SCS_FinalColorLDR;
    SceneCapture->bCaptureEveryFrame = true;
    SceneCapture->bCaptureOnMovement = true;
    SceneCapture->bAlwaysPersistRenderingState = true;
    SceneCapture->PrimitiveRenderMode = ESceneCapturePrimitiveRenderMode::PRM_RenderScenePrimitives;
    // Industrial CCTV cameras use a fixed exposure so the feed does not pulse
    // when a bright coil wrap or dark machine enclosure enters frame. The
    // remote stage deliberately has no global skylight/directional light, so a
    // strong fixed compensation is required on the selected camera only.
    SceneCapture->PostProcessSettings.bOverride_AutoExposureBias = true;
    SceneCapture->PostProcessSettings.AutoExposureBias = CaptureExposureBias;
    SceneCapture->MaxViewDistanceOverride = 12000.0f;
    SceneCapture->ShowFlags.SetDynamicShadows(true);

    FeedMaterial = TSoftObjectPtr<UMaterialInterface>(
        FSoftObjectPath(TEXT("/Game/LineBoss/Candidates/ControlRoom/CCTV/M_CairnwellCCTVFeed.M_CairnwellCCTVFeed")));
}

void ALBControlRoomCCTVFeed::BeginPlay()
{
    Super::BeginPlay();

    RenderTarget = NewObject<UTextureRenderTarget2D>(this, TEXT("CairnwellSelectedCCTVRenderTarget"));
    RenderTarget->RenderTargetFormat = ETextureRenderTargetFormat::RTF_RGBA8;
    RenderTarget->ClearColor = FLinearColor(0.002f, 0.006f, 0.008f, 1.0f);
    RenderTarget->InitAutoFormat(FMath::Max(320, CaptureWidth), FMath::Max(180, CaptureHeight));
    RenderTarget->UpdateResourceImmediate(true);

    SceneCapture->TextureTarget = RenderTarget;
    SceneCapture->FOVAngle = CaptureFieldOfView;
    // Reapply runtime policy after serialized component state is loaded.
    SceneCapture->PostProcessSettings.bOverride_AutoExposureBias = true;
    SceneCapture->PostProcessSettings.AutoExposureBias = CaptureExposureBias;
    SceneCapture->MaxViewDistanceOverride = 12000.0f;
    SceneCapture->ShowFlags.SetDynamicShadows(true);
    SceneCapture->SetWorldLocationAndRotation(CaptureWorldLocation, CaptureWorldRotation);

    if (UMaterialInterface* ParentMaterial = FeedMaterial.LoadSynchronous())
    {
        DisplayMaterial = UMaterialInstanceDynamic::Create(ParentMaterial, this);
        DisplayMaterial->SetTextureParameterValue(TEXT("CCTVTexture"), RenderTarget);
        DisplaySurface->SetMaterial(0, DisplayMaterial);
    }

    SetSelectedFeed(bSelectedFeed);
}

void ALBControlRoomCCTVFeed::SetSelectedFeed(bool bSelected)
{
    bSelectedFeed = bSelected;
    if (!SceneCapture)
    {
        return;
    }

    SceneCapture->bCaptureEveryFrame = bSelectedFeed;
    SceneCapture->bCaptureOnMovement = bSelectedFeed;
}

void ALBControlRoomCCTVFeed::SetCaptureTransform(const FVector& WorldLocation, const FRotator& WorldRotation)
{
    CaptureWorldLocation = WorldLocation;
    CaptureWorldRotation = WorldRotation;
    if (SceneCapture)
    {
        SceneCapture->SetWorldLocationAndRotation(CaptureWorldLocation, CaptureWorldRotation);
    }
}
