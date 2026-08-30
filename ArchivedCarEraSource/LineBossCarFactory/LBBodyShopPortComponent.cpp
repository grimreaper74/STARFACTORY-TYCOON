#include "LBBodyShopPortComponent.h"

ULBBodyShopPortComponent::ULBBodyShopPortComponent()
{
    PrimaryComponentTick.bCanEverTick = false;
    SetMobility(EComponentMobility::Movable);
}

void ULBBodyShopPortComponent::Configure(const FLBBodyShopPortDefinition& InDefinition)
{
    Definition = InDefinition;
    SetRelativeTransform(Definition.LocalTransform);
    ComponentTags.Reset();
    ComponentTags.Add(TEXT("LB.BodyShop.Port.v001"));
    ComponentTags.Add(Definition.Direction == ELBBodyShopPortDirection::Input
        ? TEXT("LB.BodyShop.Port.Input") : TEXT("LB.BodyShop.Port.Output"));
    ComponentTags.Add(Definition.MaterialId);
}

