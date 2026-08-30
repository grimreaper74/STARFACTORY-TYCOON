#include "LBPressShopOverheadVisualLayerActor.h"

#include "Components/StaticMeshComponent.h"

ALBPressShopOverheadVisualLayerActor::
    ALBPressShopOverheadVisualLayerActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    SetActorEnableCollision(false);
    Tags.AddUnique(GetLayerTag());
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));

    if (UStaticMeshComponent* Mesh = GetStaticMeshComponent())
    {
        Mesh->SetMobility(EComponentMobility::Movable);
        Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Mesh->SetCollisionResponseToAllChannels(ECR_Ignore);
        Mesh->SetGenerateOverlapEvents(false);
        Mesh->SetCanEverAffectNavigation(false);
        Mesh->SetReceivesDecals(false);
        Mesh->SetCastShadow(false);
    }
}

void ALBPressShopOverheadVisualLayerActor::PostRegisterAllComponents()
{
    Super::PostRegisterAllComponents();

    UStaticMeshComponent* Mesh = GetStaticMeshComponent();
    if (!Mesh || !Mesh->IsRegistered() || !Mesh->GetStaticMesh())
    {
        return;
    }

    // Imported sprite instances can finish loading with the correct UObject in
    // slot zero while the newly registered proxy still holds the unit plane's
    // fallback material. Reassert the exact resolved object, then explicitly
    // recreate the proxy even when SetMaterial detects an identical override.
    UMaterialInterface* const SpriteMaterial = Mesh->GetMaterial(0);
    if (SpriteMaterial && Mesh->IsRenderStateCreated())
    {
        Mesh->SetMaterial(0, SpriteMaterial);
        Mesh->MarkRenderStateDirty();
    }
}

FName ALBPressShopOverheadVisualLayerActor::GetLayerTag()
{
    return TEXT("LB.PressShop.Overhead.VisualLayer.v001");
}

bool ALBPressShopOverheadVisualLayerActor::IsSequenceFrameVisible(
    const float NormalizedSequenceProgress) const
{
    const bool bNoSequence = SequenceFrameIndex == INDEX_NONE
        && SequenceFrameCount == 0;
    if (bNoSequence) return true;
    if (!FMath::IsFinite(NormalizedSequenceProgress)
        || SequenceFrameCount <= 0 || SequenceFrameIndex < 0
        || SequenceFrameIndex >= SequenceFrameCount)
    {
        return false;
    }

    float Progress = FMath::Max(0.0f, NormalizedSequenceProgress);
    if (bSequenceLoops)
    {
        Progress = FMath::Frac(Progress);
    }
    else
    {
        Progress = FMath::Clamp(Progress, 0.0f, 1.0f);
    }
    const int32 ActiveFrame = Progress >= 1.0f
        ? SequenceFrameCount - 1
        : FMath::Clamp(FMath::FloorToInt(
            Progress * static_cast<float>(SequenceFrameCount)),
            0, SequenceFrameCount - 1);
    return SequenceFrameIndex == ActiveFrame;
}

void ALBPressShopOverheadVisualLayerActor::ApplyPresentationState(
    const bool bVisible, const float MotionAlpha01)
{
    SetActorHiddenInGame(!bVisible);
    if (UStaticMeshComponent* Mesh = GetStaticMeshComponent())
    {
        Mesh->SetVisibility(bVisible, true);
        Mesh->SetHiddenInGame(!bVisible, true);
        Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    }

    if (bHasMotionRange)
    {
        FTransform Blended;
        Blended.Blend(MotionStart, MotionEnd,
            FMath::Clamp(MotionAlpha01, 0.0f, 1.0f));
        SetActorTransform(Blended, false, nullptr,
            ETeleportType::TeleportPhysics);
    }
}
