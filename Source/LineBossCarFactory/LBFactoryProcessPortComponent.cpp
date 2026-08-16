#include "LBFactoryProcessPortComponent.h"
#include "LBFactoryTransportLink.h"

void ULBFactoryProcessPortComponent::SetConnection(
    ULBFactoryProcessPortComponent* Other, ALBFactoryTransportLink* Link)
{
    ConnectedPorts.AddUnique(Other);
    TransportLinks.AddUnique(Link);
}

void ULBFactoryProcessPortComponent::ClearConnection()
{
    ConnectedPorts.Reset();
    TransportLinks.Reset();
}

void ULBFactoryProcessPortComponent::RemoveConnection(ALBFactoryTransportLink* Link)
{
    const int32 Index = TransportLinks.IndexOfByPredicate(
        [Link](const TWeakObjectPtr<ALBFactoryTransportLink>& Candidate)
        { return Candidate.Get() == Link; });
    if (Index == INDEX_NONE) return;
    TransportLinks.RemoveAt(Index);
    if (ConnectedPorts.IsValidIndex(Index)) ConnectedPorts.RemoveAt(Index);
}

void ULBFactoryProcessPortComponent::RemoveConnectionsTo(
    const ULBFactoryProcessPortComponent* Other)
{
    for (int32 Index = ConnectedPorts.Num() - 1; Index >= 0; --Index)
    {
        if (ConnectedPorts[Index].Get() != Other) continue;
        ConnectedPorts.RemoveAt(Index);
        if (TransportLinks.IsValidIndex(Index)) TransportLinks.RemoveAt(Index);
    }
}

bool ULBFactoryProcessPortComponent::HasTransportLink(
    const ALBFactoryTransportLink* Link) const
{
    return TransportLinks.ContainsByPredicate(
        [Link](const TWeakObjectPtr<ALBFactoryTransportLink>& Candidate)
        { return Candidate.Get() == Link; });
}

bool ULBFactoryProcessPortComponent::IsConnectedTo(
    const ULBFactoryProcessPortComponent* Other) const
{
    return ConnectedPorts.ContainsByPredicate(
        [Other](const TWeakObjectPtr<ULBFactoryProcessPortComponent>& Candidate)
        { return Candidate.Get() == Other; });
}
