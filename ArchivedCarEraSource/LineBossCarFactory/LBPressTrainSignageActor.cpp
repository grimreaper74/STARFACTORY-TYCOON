#include "LBPressTrainSignageActor.h"

#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "UObject/ConstructorHelpers.h"

ALBPressTrainSignageActor::ALBPressTrainSignageActor()
{
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("SignRoot"));

    SignPlate = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("SignPlate"));
    SignPlate->SetupAttachment(RootComponent);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeAsset(
        TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (CubeAsset.Succeeded())
    {
        SignPlate->SetStaticMesh(CubeAsset.Object);
    }
    SignPlate->SetRelativeScale3D(FVector(1.5f, 0.08f, 0.45f));
    SignPlate->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SignPlate->SetGenerateOverlapEvents(false);
    SignPlate->SetCanEverAffectNavigation(false);

    Label = CreateDefaultSubobject<UTextRenderComponent>(TEXT("TrainLabel"));
    Label->SetupAttachment(RootComponent);
    Label->SetText(FText::FromString(TEXT("PRESS TRAIN")));
    Label->SetHorizontalAlignment(EHorizTextAligment::EHTA_Center);
    Label->SetVerticalAlignment(EVerticalTextAligment::EVRTA_TextCenter);
    Label->SetTextRenderColor(FColor(255, 214, 64));
    Label->SetWorldSize(30.0f);
    Label->SetRelativeLocation(FVector(0.0f, 9.0f, 0.0f));
    Label->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
    Label->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Label->SetGenerateOverlapEvents(false);
    Label->SetCanEverAffectNavigation(false);
}
