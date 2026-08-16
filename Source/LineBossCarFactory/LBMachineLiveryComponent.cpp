#include "LBMachineLiveryComponent.h"

#include "Components/MeshComponent.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

ULBMachineLiveryComponent::ULBMachineLiveryComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
}

void ULBMachineLiveryComponent::BeginPlay()
{
    Super::BeginPlay();
    SubscribeToFactoryBrand();
}

void ULBMachineLiveryComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    UnsubscribeFromFactoryBrand();
    Super::EndPlay(EndPlayReason);
}

bool ULBMachineLiveryComponent::RegisterTexturedMaterialBinding(
    UMeshComponent* MeshComponent, const int32 MaterialIndex,
    const ELBMachineLiveryRole Role, const FName TintParameter)
{
    return RegisterBinding(MeshComponent, MaterialIndex, Role, TintParameter, nullptr);
}

bool ULBMachineLiveryComponent::RegisterGenericMaterialBinding(
    UMeshComponent* MeshComponent, const int32 MaterialIndex,
    const ELBMachineLiveryRole Role, UMaterialInterface* TintableParent,
    const FName TintParameter)
{
    if (!TintableParent) return false;
    return RegisterBinding(MeshComponent, MaterialIndex, Role, TintParameter, TintableParent);
}

bool ULBMachineLiveryComponent::RegisterBinding(
    UMeshComponent* MeshComponent, const int32 MaterialIndex,
    const ELBMachineLiveryRole Role, const FName TintParameter,
    UMaterialInterface* ExplicitTintableParent)
{
    if (!IsValid(MeshComponent) || MaterialIndex < 0
        || MaterialIndex >= MeshComponent->GetNumMaterials() || TintParameter.IsNone())
        return false;

    if (MaterialBindings.ContainsByPredicate(
        [MeshComponent, MaterialIndex](const FLBMachineLiveryMaterialBinding& Binding)
        {
            return Binding.MeshComponent == MeshComponent && Binding.MaterialIndex == MaterialIndex;
        }))
        return false;

    UMaterialInterface* CurrentMaterial = MeshComponent->GetMaterial(MaterialIndex);
    UMaterialInterface* TintableParent = ExplicitTintableParent
        ? ExplicitTintableParent : CurrentMaterial;
    if (!TintableParent) return false;

    FLBMachineLiveryMaterialBinding& Binding = MaterialBindings.AddDefaulted_GetRef();
    Binding.MeshComponent = MeshComponent;
    Binding.MaterialIndex = MaterialIndex;
    Binding.Role = Role;
    Binding.TintParameter = TintParameter;
    Binding.ExplicitTintableParent = ExplicitTintableParent;
    Binding.OriginalMaterial = CurrentMaterial;
    Binding.DynamicMaterial = UMaterialInstanceDynamic::Create(TintableParent, this,
        FName(*FString::Printf(TEXT("LB_Livery_%s_%d"),
            *MeshComponent->GetName(), MaterialIndex)));
    if (!Binding.DynamicMaterial)
    {
        MaterialBindings.Pop();
        return false;
    }
    MeshComponent->SetMaterial(MaterialIndex, Binding.DynamicMaterial);
    // Bind as soon as the first authored slot is registered. Runtime machines can be
    // configured before their actor/component BeginPlay callbacks, but Factory Profile
    // edits must still propagate to those already-created MIDs.
    SubscribeToFactoryBrand();
    RefreshFromFactoryBrand();
    return true;
}

void ULBMachineLiveryComponent::ClearMaterialBindings()
{
    for (const FLBMachineLiveryMaterialBinding& Binding : MaterialBindings)
    {
        if (IsValid(Binding.MeshComponent) && Binding.MaterialIndex >= 0
            && Binding.MaterialIndex < Binding.MeshComponent->GetNumMaterials()
            && Binding.MeshComponent->GetMaterial(Binding.MaterialIndex) == Binding.DynamicMaterial)
        {
            Binding.MeshComponent->SetMaterial(Binding.MaterialIndex, Binding.OriginalMaterial);
        }
    }
    MaterialBindings.Reset();
}

void ULBMachineLiveryComponent::RefreshFromFactoryBrand()
{
    if (const ULBFactoryBrandSubsystem* Brand = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryBrandSubsystem>() : nullptr)
    {
        ApplyMachineLivery(Brand->GetMachineLivery());
    }
}

void ULBMachineLiveryComponent::ApplyMachineLivery(const FLBFactoryMachineLivery& Livery)
{
    for (FLBMachineLiveryMaterialBinding& Binding : MaterialBindings)
    {
        if (!IsValid(Binding.MeshComponent) || !IsValid(Binding.DynamicMaterial)) continue;
        const FLinearColor Colour = Binding.Role == ELBMachineLiveryRole::PrimaryBody
            ? Livery.PrimaryColour : Livery.SecondaryColour;
        Binding.DynamicMaterial->SetVectorParameterValue(Binding.TintParameter, Colour);
    }
}

void ULBMachineLiveryComponent::HandleMachineLiveryChanged(
    const FLBFactoryMachineLivery& Livery)
{
    ApplyMachineLivery(Livery);
}

void ULBMachineLiveryComponent::SubscribeToFactoryBrand()
{
    if (LiveryChangedHandle.IsValid()) return;
    if (ULBFactoryBrandSubsystem* Brand = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryBrandSubsystem>() : nullptr)
    {
        LiveryChangedHandle = Brand->OnMachineLiveryChanged().AddUObject(
            this, &ULBMachineLiveryComponent::HandleMachineLiveryChanged);
        ApplyMachineLivery(Brand->GetMachineLivery());
    }
}

void ULBMachineLiveryComponent::UnsubscribeFromFactoryBrand()
{
    if (!LiveryChangedHandle.IsValid()) return;
    if (ULBFactoryBrandSubsystem* Brand = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryBrandSubsystem>() : nullptr)
    {
        Brand->OnMachineLiveryChanged().Remove(LiveryChangedHandle);
    }
    LiveryChangedHandle.Reset();
}

UMaterialInstanceDynamic* ULBMachineLiveryComponent::GetDynamicMaterialForBinding(
    const int32 BindingIndex) const
{
    return MaterialBindings.IsValidIndex(BindingIndex)
        ? MaterialBindings[BindingIndex].DynamicMaterial.Get() : nullptr;
}
