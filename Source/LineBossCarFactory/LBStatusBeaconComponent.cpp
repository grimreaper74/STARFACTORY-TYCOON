#include "LBStatusBeaconComponent.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"
#include "GameFramework/Actor.h"

namespace
{
    const FLinearColor LBBeaconGreen(0.03f, 1.0f, 0.18f, 1.0f);
    const FLinearColor LBBeaconAmber(1.0f, 0.34f, 0.015f, 1.0f);
    const FLinearColor LBBeaconRed(1.0f, 0.015f, 0.01f, 1.0f);
}

ULBStatusBeaconComponent::ULBStatusBeaconComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.bStartWithTickEnabled = true;
    SetMobility(EComponentMobility::Movable);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMeshAsset(
        TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> BasicShapeMaterial(
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> EmissiveLensMaterial(
        TEXT("/Game/LineBoss/SupportRobots/ServiceDocks/VisualMaterials_v005/M_LB_ServiceDock_SmoothIndustrial_Master_v005.M_LB_ServiceDock_SmoothIndustrial_Master_v005"));

    CylinderMesh = CylinderMeshAsset.Object;
    MastMaterialParent = BasicShapeMaterial.Object;
    LensMaterialParent = EmissiveLensMaterial.Object;
}

void ULBStatusBeaconComponent::OnRegister()
{
    Super::OnRegister();
    EnsureVisualComponents();
    EnsureDynamicMaterials();
    ApplyVisualState();
}

void ULBStatusBeaconComponent::TickComponent(const float DeltaTime, const ELevelTick TickType,
    FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    if (!IsFlashing()) return;

    FlashElapsedSeconds = FMath::Fmod(FlashElapsedSeconds + FMath::Max(0.0f, DeltaTime),
        FMath::Max(FlashPeriodSeconds, 0.1f));
    const bool bNewFlashOn = FlashElapsedSeconds < FMath::Max(FlashPeriodSeconds, 0.1f) * 0.5f;
    if (bNewFlashOn != bFlashOn)
    {
        bFlashOn = bNewFlashOn;
        ApplyVisualState();
    }
}

void ULBStatusBeaconComponent::SetStatus(const ELBStatusBeaconState NewStatus)
{
    if (Status == NewStatus) return;
    Status = NewStatus;
    FlashElapsedSeconds = 0.0f;
    bFlashOn = true;
    ApplyVisualState();
}

bool ULBStatusBeaconComponent::IsGreenLampLit() const
{
    return Status == ELBStatusBeaconState::Ready || Status == ELBStatusBeaconState::Running;
}

bool ULBStatusBeaconComponent::IsAmberLampLit() const
{
    return Status == ELBStatusBeaconState::Idle || Status == ELBStatusBeaconState::Waiting
        || (Status == ELBStatusBeaconState::Moving && bFlashOn);
}

bool ULBStatusBeaconComponent::IsRedLampLit() const
{
    return Status == ELBStatusBeaconState::Stopped || Status == ELBStatusBeaconState::Fault
        || (Status == ELBStatusBeaconState::Emergency && bFlashOn);
}

bool ULBStatusBeaconComponent::IsFlashing() const
{
    return Status == ELBStatusBeaconState::Moving || Status == ELBStatusBeaconState::Emergency;
}

void ULBStatusBeaconComponent::SetGeneratedLampHeadsVisible(const bool bShowLampHeads)
{
    bGeneratedLampHeadsVisible = bShowLampHeads;
    ApplyVisualState();
}

void ULBStatusBeaconComponent::EnsureVisualComponents()
{
    AActor* Owner = GetOwner();
    if (!Owner || IsTemplate()) return;

    const auto EnsureMesh = [&](TObjectPtr<UStaticMeshComponent>& Mesh, const TCHAR* Suffix,
        const FVector& Location, const FVector& Scale)
    {
        if (!IsValid(Mesh) || Mesh->GetOwner() != Owner || Mesh->IsTemplate())
        {
            Mesh = NewObject<UStaticMeshComponent>(Owner,
                FName(*FString::Printf(TEXT("%s_%s"), *GetName(), Suffix)), RF_Transient);
            Owner->AddInstanceComponent(Mesh);
            Mesh->SetupAttachment(this);
            Mesh->SetStaticMesh(CylinderMesh);
            Mesh->SetRelativeLocation(Location);
            Mesh->SetRelativeScale3D(Scale);
            Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Mesh->SetGenerateOverlapEvents(false);
            Mesh->SetCanEverAffectNavigation(false);
            Mesh->SetCastShadow(false);
            Mesh->SetMobility(EComponentMobility::Movable);
        }
        if (!Mesh->IsRegistered()) Mesh->RegisterComponent();
    };

    EnsureMesh(Mast, TEXT("Mast"), FVector(0.0f, 0.0f, 15.0f),
        FVector(0.035f, 0.035f, 0.30f));
    EnsureMesh(GreenLens, TEXT("GreenLens"), FVector(0.0f, 0.0f, 12.0f),
        FVector(0.12f, 0.12f, 0.06f));
    EnsureMesh(AmberLens, TEXT("AmberLens"), FVector(0.0f, 0.0f, 20.0f),
        FVector(0.12f, 0.12f, 0.06f));
    EnsureMesh(RedLens, TEXT("RedLens"), FVector(0.0f, 0.0f, 28.0f),
        FVector(0.12f, 0.12f, 0.06f));
    if (MastMaterialParent) Mast->SetMaterial(0, MastMaterialParent);

    const auto EnsureLight = [&](TObjectPtr<UPointLightComponent>& Light, const TCHAR* Suffix,
        UStaticMeshComponent* Lens, const FLinearColor& Colour)
    {
        if (!IsValid(Light) || Light->GetOwner() != Owner || Light->IsTemplate())
        {
            Light = NewObject<UPointLightComponent>(Owner,
                FName(*FString::Printf(TEXT("%s_%s"), *GetName(), Suffix)), RF_Transient);
            Owner->AddInstanceComponent(Light);
            Light->SetupAttachment(Lens);
            Light->SetRelativeLocation(FVector::ZeroVector);
            Light->SetLightColor(Colour);
            Light->SetIntensity(0.0f);
            Light->SetAttenuationRadius(AttenuationRadiusCm);
            Light->SetCastShadows(false);
            Light->SetAffectTranslucentLighting(true);
            Light->SetMobility(EComponentMobility::Movable);
            Light->SetVisibility(false);
        }
        if (!Light->IsRegistered()) Light->RegisterComponent();
    };
    EnsureLight(GreenLight, TEXT("GreenLight"), GreenLens, LBBeaconGreen);
    EnsureLight(AmberLight, TEXT("AmberLight"), AmberLens, LBBeaconAmber);
    EnsureLight(RedLight, TEXT("RedLight"), RedLens, LBBeaconRed);
}

void ULBStatusBeaconComponent::EnsureDynamicMaterials()
{
    if (!LensMaterialParent || !GreenLens || !AmberLens || !RedLens) return;
    const auto Ensure = [&](UStaticMeshComponent* Lens,
        TObjectPtr<UMaterialInstanceDynamic>& Material, const TCHAR* Name)
    {
        if (!Material)
        {
            Material = UMaterialInstanceDynamic::Create(LensMaterialParent, this, FName(Name));
            Lens->SetMaterial(0, Material);
        }
    };
    Ensure(GreenLens, GreenLensMaterial, TEXT("MID_LB_StatusBeacon_Green"));
    Ensure(AmberLens, AmberLensMaterial, TEXT("MID_LB_StatusBeacon_Amber"));
    Ensure(RedLens, RedLensMaterial, TEXT("MID_LB_StatusBeacon_Red"));
}

void ULBStatusBeaconComponent::ApplyVisualState()
{
    if (!Mast || !GreenLens || !AmberLens || !RedLens) return;
    EnsureDynamicMaterials();
    Mast->SetVisibility(bGeneratedLampHeadsVisible, true);
    GreenLens->SetVisibility(bGeneratedLampHeadsVisible, true);
    AmberLens->SetVisibility(bGeneratedLampHeadsVisible, true);
    RedLens->SetVisibility(bGeneratedLampHeadsVisible, true);

    ApplyLamp(GreenLens, GreenLensMaterial, GreenLight, LBBeaconGreen, IsGreenLampLit());
    ApplyLamp(AmberLens, AmberLensMaterial, AmberLight, LBBeaconAmber, IsAmberLampLit());
    ApplyLamp(RedLens, RedLensMaterial, RedLight, LBBeaconRed, IsRedLampLit());
}

void ULBStatusBeaconComponent::ApplyLamp(UStaticMeshComponent* Lens,
    UMaterialInstanceDynamic* Material, UPointLightComponent* Light,
    const FLinearColor& Colour, const bool bLit)
{
    if (Material)
    {
        Material->SetVectorParameterValue(TEXT("BaseColour"), Colour * (bLit ? 0.42f : 0.06f));
        Material->SetScalarParameterValue(TEXT("Roughness"), bLit ? 0.18f : 0.42f);
        Material->SetScalarParameterValue(TEXT("Metallic"), 0.0f);
        Material->SetVectorParameterValue(TEXT("EmissiveColour"), bLit ? Colour : FLinearColor::Black);
        Material->SetScalarParameterValue(TEXT("EmissiveStrength"), bLit ? 5.0f : 0.0f);
    }
    if (Light)
    {
        Light->SetAttenuationRadius(AttenuationRadiusCm);
        Light->SetIntensity(bLit ? ActiveLightIntensity : 0.0f);
        Light->SetVisibility(bLit, true);
    }
}
