#include "LBPaintShopPortComponent.h"

namespace LBPaintShopPortPrivate
{
    bool IsKnownWIPId(const FName WIPId)
    {
        return WIPId == LBPaintShopWIPIds::BIWComplete
            || WIPId == LBPaintShopWIPIds::BIWEDCoated
            || WIPId == LBPaintShopWIPIds::BIWCuredEDCoat;
    }
}

ULBPaintShopPortComponent::ULBPaintShopPortComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    PrimaryComponentTick.bStartWithTickEnabled = false;
    SetMobility(EComponentMobility::Movable);
    ClearConfiguration(TEXT("PAINT SHOP PORT HAS NOT BEEN CONFIGURED"));
}

bool ULBPaintShopPortComponent::Configure(
    const FLBPaintShopPortDefinition& InDefinition, const FTransform& InLocalTransform)
{
    FString FailureReason;
    if (!ValidateConfiguration(InDefinition, InLocalTransform, FailureReason))
    {
        ClearConfiguration(FailureReason);
        return false;
    }

    Definition = InDefinition;
    ConfiguredLocalTransform = InLocalTransform;
    bConfigured = true;
    ConfigurationFailureReason.Reset();
    SetRelativeTransform(ConfiguredLocalTransform);

    ComponentTags.Reset();
    ComponentTags.Add(TEXT("LB.PaintShop.Port.v001"));
    ComponentTags.Add(Definition.Direction == ELBPaintShopPortDirection::Input
        ? TEXT("LB.PaintShop.Port.Input") : TEXT("LB.PaintShop.Port.Output"));
    ComponentTags.Add(Definition.PortId);
    ComponentTags.Add(Definition.WIPId);
    return true;
}

bool ULBPaintShopPortComponent::TryGetDirection(
    ELBPaintShopPortDirection& OutDirection) const
{
    OutDirection = ELBPaintShopPortDirection::Input;
    if (!bConfigured)
    {
        return false;
    }
    OutDirection = Definition.Direction;
    return true;
}

bool ULBPaintShopPortComponent::TryGetDefinition(
    FLBPaintShopPortDefinition& OutDefinition) const
{
    OutDefinition = FLBPaintShopPortDefinition();
    if (!bConfigured)
    {
        return false;
    }
    OutDefinition = Definition;
    return true;
}

void ULBPaintShopPortComponent::ClearConfiguration(const FString& FailureReason)
{
    Definition = FLBPaintShopPortDefinition();
    ConfiguredLocalTransform = FTransform::Identity;
    bConfigured = false;
    ConfigurationFailureReason = FailureReason;
    SetRelativeTransform(FTransform::Identity);
    ComponentTags.Reset();
}

bool ULBPaintShopPortComponent::ValidateConfiguration(
    const FLBPaintShopPortDefinition& InDefinition, const FTransform& InLocalTransform,
    FString& OutReason)
{
    OutReason.Reset();
    const bool bIsInputId = InDefinition.PortId == LBPaintShopPortIds::CarrierIn;
    const bool bIsOutputId = InDefinition.PortId == LBPaintShopPortIds::CarrierOut;
    if (!bIsInputId && !bIsOutputId)
    {
        OutReason = TEXT("PAINT SHOP PORT ID IS NOT A STABLE CARRIER PORT");
        return false;
    }
    if ((bIsInputId && InDefinition.Direction != ELBPaintShopPortDirection::Input)
        || (bIsOutputId && InDefinition.Direction != ELBPaintShopPortDirection::Output))
    {
        OutReason = TEXT("PAINT SHOP PORT DIRECTION DOES NOT MATCH ITS STABLE ID");
        return false;
    }
    if (!LBPaintShopPortPrivate::IsKnownWIPId(InDefinition.WIPId))
    {
        OutReason = TEXT("PAINT SHOP PORT WIP ID IS UNKNOWN");
        return false;
    }
    if (!InLocalTransform.IsValid()
        || !InLocalTransform.GetScale3D().Equals(FVector::OneVector, KINDA_SMALL_NUMBER))
    {
        OutReason = TEXT("PAINT SHOP PORT LOCAL TRANSFORM IS INVALID OR SCALED");
        return false;
    }
    return true;
}

