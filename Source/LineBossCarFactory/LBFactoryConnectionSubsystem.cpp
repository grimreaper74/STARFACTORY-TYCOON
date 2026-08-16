#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBFactoryTransportLink.h"
#include "EngineUtils.h"

namespace
{
FString ConnectionPairKey(const FName SourcePortId, const FName TargetPortId)
{
    return FString::Printf(TEXT("%s>%s"), *SourcePortId.ToString(), *TargetPortId.ToString());
}

bool ConnectionStateLess(const FLBFactoryTransportLinkSaveState& A,
    const FLBFactoryTransportLinkSaveState& B)
{
    const int32 SourceCompare = A.SourcePortId.ToString().Compare(B.SourcePortId.ToString());
    return SourceCompare == 0
        ? A.TargetPortId.ToString() < B.TargetPortId.ToString() : SourceCompare < 0;
}

bool ConnectionStatesEqual(const TArray<FLBFactoryTransportLinkSaveState>& A,
    const TArray<FLBFactoryTransportLinkSaveState>& B)
{
    if (A.Num() != B.Num()) return false;
    for (int32 Index = 0; Index < A.Num(); ++Index)
    {
        if (A[Index].Version != B[Index].Version
            || A[Index].SourcePortId != B[Index].SourcePortId
            || A[Index].TargetPortId != B[Index].TargetPortId
            || A[Index].TransferredUnits != B[Index].TransferredUnits)
        {
            return false;
        }
    }
    return true;
}

void RemoveLinkFromEveryPortCache(UWorld& World, ALBFactoryTransportLink* Link)
{
    if (!Link) return;
    for (TActorIterator<AActor> ActorIt(&World); ActorIt; ++ActorIt)
    {
        TArray<ULBFactoryProcessPortComponent*> Ports;
        ActorIt->GetComponents(Ports);
        for (ULBFactoryProcessPortComponent* Port : Ports)
            if (Port) Port->RemoveConnection(Link);
    }
}

bool ResolveUniquePort(UWorld& World, const FName PortId,
    ULBFactoryProcessPortComponent*& OutPort)
{
    OutPort = nullptr;
    if (PortId.IsNone()) return false;
    for (TActorIterator<AActor> ActorIt(&World); ActorIt; ++ActorIt)
    {
        TArray<ULBFactoryProcessPortComponent*> Ports;
        ActorIt->GetComponents(Ports);
        for (ULBFactoryProcessPortComponent* Port : Ports)
        {
            if (!IsValid(Port) || Port->PortId != PortId) continue;
            if (OutPort) return false;
            OutPort = Port;
        }
    }
    return OutPort != nullptr;
}
}

bool ULBFactoryConnectionSubsystem::CanConnect(
    const ULBFactoryProcessPortComponent* Source,
    const ULBFactoryProcessPortComponent* Target, FString& OutReason) const
{
    OutReason.Reset();
    if (!Source || !Target || Source == Target)
    {
        OutReason = TEXT("BOTH PROCESS PORTS ARE REQUIRED");
        return false;
    }
    if (Source->Direction != ELBFactoryPortDirection::Output
        || Target->Direction != ELBFactoryPortDirection::Input)
    {
        OutReason = TEXT("CONNECTION MUST RUN FROM OUTPUT TO INPUT");
        return false;
    }
    if (!Source->HasAvailableConnection() || !Target->HasAvailableConnection())
    {
        OutReason = TEXT("A PROCESS PORT HAS REACHED ITS AUTHORED CONNECTION CAPACITY");
        return false;
    }
    if (Source->IsConnectedTo(Target) || Target->IsConnectedTo(Source))
    {
        OutReason = TEXT("THESE PROCESS PORTS ARE ALREADY CONNECTED");
        return false;
    }
    if (Source->ProcessStage + 1 != Target->ProcessStage)
    {
        OutReason = TEXT("ONLY THE NEXT REQUIRED PROCESS STAGE MAY CONNECT");
        return false;
    }
    if (Source->TransportKind != Target->TransportKind
        || Source->MaterialClass != Target->MaterialClass)
    {
        OutReason = TEXT("PROCESS PORT TRANSPORT OR MATERIAL TYPE IS INCOMPATIBLE");
        return false;
    }
    const float Distance = FVector::Distance(Source->GetComponentLocation(), Target->GetComponentLocation());
    if (Distance > FMath::Min(Source->MaximumAutomaticLinkDistanceCm,
        Target->MaximumAutomaticLinkDistanceCm))
    {
        OutReason = TEXT("COMPATIBLE PROCESS PORT IS OUT OF AUTOMATIC CONNECTION RANGE");
        return false;
    }
    OutReason = TEXT("NEXT PROCESS STAGE IS COMPATIBLE");
    return true;
}

bool ULBFactoryConnectionSubsystem::Connect(ULBFactoryProcessPortComponent* Source,
    ULBFactoryProcessPortComponent* Target, ALBFactoryTransportLink*& OutLink, FString& OutReason)
{
    OutLink = nullptr;
    if (!CanConnect(Source, Target, OutReason) || !GetWorld()) return false;
    ALBFactoryTransportLink* Link = GetWorld()->SpawnActor<ALBFactoryTransportLink>();
    if (!Link || !Link->Configure(Source, Target))
    {
        if (Link) Link->Destroy();
        OutReason = TEXT("AUTOMATIC TRANSPORT LINK COULD NOT BE CREATED");
        return false;
    }
    Source->SetConnection(Target, Link);
    Target->SetConnection(Source, Link);
    OutLink = Link;
    OutReason = FString::Printf(TEXT("%s CONNECTED TO %s"),
        *Source->PortId.ToString(), *Target->PortId.ToString());
    return true;
}

bool ULBFactoryConnectionSubsystem::AutoConnectNewMachine(AActor* NewlyPlacedMachine,
    TArray<ALBFactoryTransportLink*>& OutLinks, FString& OutReason)
{
    OutLinks.Reset();
    if (!NewlyPlacedMachine || NewlyPlacedMachine->GetWorld() != GetWorld())
    {
        OutReason = TEXT("NEWLY PLACED MACHINE IS NOT IN THIS FACTORY WORLD");
        return false;
    }
    TArray<ULBFactoryProcessPortComponent*> NewPorts;
    NewlyPlacedMachine->GetComponents(NewPorts);
    bool bHasRequiredInput = false;
    auto RollBackCreatedLinks = [this, &OutLinks]()
    {
        for (ALBFactoryTransportLink* CreatedLink : OutLinks)
        {
            if (!CreatedLink) continue;
            for (TActorIterator<AActor> ActorIt(GetWorld()); ActorIt; ++ActorIt)
            {
                TArray<ULBFactoryProcessPortComponent*> ActorPorts;
                (*ActorIt)->GetComponents(ActorPorts);
                for (ULBFactoryProcessPortComponent* Port : ActorPorts)
                    if (Port) Port->RemoveConnection(CreatedLink);
            }
            CreatedLink->Destroy();
        }
        OutLinks.Reset();
    };
    for (ULBFactoryProcessPortComponent* Target : NewPorts)
    {
        if (!Target || Target->Direction != ELBFactoryPortDirection::Input || Target->ProcessStage <= 0) continue;
        bHasRequiredInput = true;
        struct FSourceCandidate
        {
            ULBFactoryProcessPortComponent* Port = nullptr;
            double DistanceSquared = 0.0;
        };
        TArray<FSourceCandidate> Candidates;
        for (TActorIterator<AActor> It(GetWorld()); It; ++It)
        {
            if (*It == NewlyPlacedMachine) continue;
            TArray<ULBFactoryProcessPortComponent*> CandidatePorts;
            (*It)->GetComponents(CandidatePorts);
            for (ULBFactoryProcessPortComponent* Source : CandidatePorts)
            {
                FString CandidateReason;
                if (!CanConnect(Source, Target, CandidateReason)) continue;
                Candidates.Add({Source, FVector::DistSquared(
                    Source->GetComponentLocation(), Target->GetComponentLocation())});
            }
        }
        Candidates.Sort([](const FSourceCandidate& A, const FSourceCandidate& B)
        {
            if (!FMath::IsNearlyEqual(A.DistanceSquared, B.DistanceSquared))
                return A.DistanceSquared < B.DistanceSquared;
            return A.Port->PortId.ToString() < B.Port->PortId.ToString();
        });
        int32 ConnectedForInput = 0;
        for (const FSourceCandidate& Candidate : Candidates)
        {
            if (!Target->HasAvailableConnection()) break;
            ALBFactoryTransportLink* Link = nullptr;
            if (Connect(Candidate.Port, Target, Link, OutReason))
            {
                OutLinks.Add(Link);
                ++ConnectedForInput;
            }
        }
        if (ConnectedForInput == 0)
        {
            RollBackCreatedLinks();
            OutReason = FString::Printf(TEXT("NO VALID PREDECESSOR FOR %s"), *Target->PortId.ToString());
            return false;
        }
    }
    if (!bHasRequiredInput)
    {
        OutReason = TEXT("MACHINE HAS NO AUTHORED INPUT REQUIRING AUTOMATIC CONNECTION");
        return true;
    }
    // If a player adds parallel capacity after its downstream buffer/cell already exists,
    // connect the new output forward to the nearest compatible target. This turns a late
    // PR004, preparation package or Press Train into working capacity immediately.
    for (ULBFactoryProcessPortComponent* Source : NewPorts)
    {
        if (!Source || Source->Direction != ELBFactoryPortDirection::Output
            || !Source->HasAvailableConnection()) continue;
        ULBFactoryProcessPortComponent* BestTarget = nullptr;
        double BestDistance = TNumericLimits<double>::Max();
        for (TActorIterator<AActor> It(GetWorld()); It; ++It)
        {
            if (*It == NewlyPlacedMachine) continue;
            TArray<ULBFactoryProcessPortComponent*> CandidatePorts;
            (*It)->GetComponents(CandidatePorts);
            for (ULBFactoryProcessPortComponent* Target : CandidatePorts)
            {
                FString CandidateReason;
                if (!CanConnect(Source, Target, CandidateReason)) continue;
                const double Distance = FVector::DistSquared(
                    Source->GetComponentLocation(), Target->GetComponentLocation());
                if (Distance < BestDistance || (FMath::IsNearlyEqual(Distance, BestDistance)
                    && BestTarget && Target->PortId.ToString() < BestTarget->PortId.ToString()))
                {
                    BestDistance = Distance;
                    BestTarget = Target;
                }
            }
        }
        if (BestTarget)
        {
            ALBFactoryTransportLink* Link = nullptr;
            if (Connect(Source, BestTarget, Link, OutReason)) OutLinks.Add(Link);
        }
    }
    OutReason = FString::Printf(TEXT("CREATED %d AUTOMATIC TRANSPORT LINK(S)"), OutLinks.Num());
    return true;
}

bool ULBFactoryConnectionSubsystem::Disconnect(
    ALBFactoryTransportLink* Link, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("FACTORY CONNECTION WORLD IS OFFLINE");
        return false;
    }
    if (!IsValid(Link))
    {
        OutReason = TEXT("TRANSPORT LINK IS ALREADY DISCONNECTED");
        return true;
    }
    if (Link->GetWorld() != World)
    {
        OutReason = TEXT("TRANSPORT LINK BELONGS TO A DIFFERENT FACTORY WORLD");
        return false;
    }

    const FName SourceId = Link->GetSourcePort() ? Link->GetSourcePort()->PortId : NAME_None;
    const FName TargetId = Link->GetTargetPort() ? Link->GetTargetPort()->PortId : NAME_None;
    RemoveLinkFromEveryPortCache(*World, Link);
    Link->Destroy();
    OutReason = SourceId.IsNone() || TargetId.IsNone()
        ? TEXT("DISCONNECTED TRANSPORT LINK WITH INCOMPLETE LEGACY PORT CACHE")
        : FString::Printf(TEXT("DISCONNECTED %s"),
            *ConnectionPairKey(SourceId, TargetId));
    return true;
}

bool ULBFactoryConnectionSubsystem::DisconnectActor(AActor* Actor, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World || !IsValid(Actor) || Actor->GetWorld() != World)
    {
        OutReason = TEXT("EDITED ACTOR IS NOT IN THIS FACTORY WORLD");
        return false;
    }

    TArray<ULBFactoryProcessPortComponent*> ActorPorts;
    Actor->GetComponents(ActorPorts);
    TSet<ULBFactoryProcessPortComponent*> RemotePorts;
    for (ULBFactoryProcessPortComponent* Port : ActorPorts)
    {
        if (!Port) continue;
        for (int32 Index = 0; Index < Port->GetConnectedPortCacheCount(); ++Index)
            if (ULBFactoryProcessPortComponent* Remote = Port->GetConnectedPortAt(Index))
                RemotePorts.Add(Remote);
    }
    for (TActorIterator<AActor> ActorIt(World); ActorIt; ++ActorIt)
    {
        if (*ActorIt == Actor) continue;
        TArray<ULBFactoryProcessPortComponent*> CandidateRemotePorts;
        ActorIt->GetComponents(CandidateRemotePorts);
        for (ULBFactoryProcessPortComponent* CandidateRemote : CandidateRemotePorts)
            for (ULBFactoryProcessPortComponent* ActorPort : ActorPorts)
                if (CandidateRemote && ActorPort && CandidateRemote->IsConnectedTo(ActorPort))
                    RemotePorts.Add(CandidateRemote);
    }

    TArray<ALBFactoryTransportLink*> Links;
    for (TActorIterator<ALBFactoryTransportLink> It(World); It; ++It)
    {
        ALBFactoryTransportLink* Link = *It;
        const ULBFactoryProcessPortComponent* Source = Link ? Link->GetSourcePort() : nullptr;
        const ULBFactoryProcessPortComponent* Target = Link ? Link->GetTargetPort() : nullptr;
        if (IsValid(Link) && ((Source && Source->GetOwner() == Actor)
            || (Target && Target->GetOwner() == Actor)))
        {
            Links.Add(Link);
        }
    }
    Links.Sort([](const ALBFactoryTransportLink& A, const ALBFactoryTransportLink& B)
    {
        const ULBFactoryProcessPortComponent* ASource = A.GetSourcePort();
        const ULBFactoryProcessPortComponent* ATarget = A.GetTargetPort();
        const ULBFactoryProcessPortComponent* BSource = B.GetSourcePort();
        const ULBFactoryProcessPortComponent* BTarget = B.GetTargetPort();
        return ConnectionPairKey(ASource ? ASource->PortId : NAME_None,
            ATarget ? ATarget->PortId : NAME_None)
            < ConnectionPairKey(BSource ? BSource->PortId : NAME_None,
                BTarget ? BTarget->PortId : NAME_None);
    });

    const int32 RemovedCount = Links.Num();
    for (ALBFactoryTransportLink* Link : Links)
    {
        FString DisconnectReason;
        Disconnect(Link, DisconnectReason);
    }
    // Fail-closed cleanup for a legacy half-cache: the edited side and every known remote
    // side are both cleared even when the corresponding link actor was already absent.
    for (ULBFactoryProcessPortComponent* Port : ActorPorts)
    {
        if (!Port) continue;
        for (ULBFactoryProcessPortComponent* Remote : RemotePorts)
            if (Remote) Remote->RemoveConnectionsTo(Port);
        Port->ClearConnection();
    }

    OutReason = RemovedCount == 0
        ? TEXT("ACTOR TRANSPORT CONNECTIONS ARE ALREADY DISCONNECTED")
        : FString::Printf(TEXT("DISCONNECTED %d ACTOR TRANSPORT LINK(S)"), RemovedCount);
    return true;
}

bool ULBFactoryConnectionSubsystem::CaptureConnections(
    TArray<FLBFactoryTransportLinkSaveState>& OutStates) const
{
    OutStates.Reset();
    if (!GetWorld()) return false;
    TSet<FName> UniquePairs;
    for (TActorIterator<ALBFactoryTransportLink> It(GetWorld()); It; ++It)
    {
        const ALBFactoryTransportLink* Link = *It;
        const ULBFactoryProcessPortComponent* Source = Link ? Link->GetSourcePort() : nullptr;
        const ULBFactoryProcessPortComponent* Target = Link ? Link->GetTargetPort() : nullptr;
        if (!Source || !Target || Source->PortId.IsNone() || Target->PortId.IsNone()) return false;
        const FName PairId(*FString::Printf(TEXT("%s>%s"),
            *Source->PortId.ToString(), *Target->PortId.ToString()));
        if (UniquePairs.Contains(PairId)) return false;
        UniquePairs.Add(PairId);
        FLBFactoryTransportLinkSaveState& State = OutStates.AddDefaulted_GetRef();
        State.SourcePortId = Source->PortId;
        State.TargetPortId = Target->PortId;
        State.TransferredUnits = Link->GetTransferredUnits();
    }
    OutStates.Sort([](const FLBFactoryTransportLinkSaveState& A,
        const FLBFactoryTransportLinkSaveState& B)
    {
        return ConnectionStateLess(A, B);
    });
    return true;
}

bool ULBFactoryConnectionSubsystem::CaptureConnectionsForActor(const AActor* Actor,
    TArray<FLBFactoryTransportLinkSaveState>& OutStates, FString& OutReason) const
{
    OutStates.Reset();
    UWorld* World = GetWorld();
    if (!World || !IsValid(Actor) || Actor->GetWorld() != World)
    {
        OutReason = TEXT("EDITED ACTOR IS NOT IN THIS FACTORY WORLD");
        return false;
    }

    TSet<const ALBFactoryTransportLink*> CapturedLinks;
    TSet<FString> PairKeys;
    for (TActorIterator<ALBFactoryTransportLink> It(World); It; ++It)
    {
        const ALBFactoryTransportLink* Link = *It;
        const ULBFactoryProcessPortComponent* Source = Link ? Link->GetSourcePort() : nullptr;
        const ULBFactoryProcessPortComponent* Target = Link ? Link->GetTargetPort() : nullptr;
        if (!IsValid(Link) || !Source || !Target) continue;
        if (Source->GetOwner() != Actor && Target->GetOwner() != Actor) continue;
        const FString PairKey = ConnectionPairKey(Source->PortId, Target->PortId);
        ULBFactoryProcessPortComponent* UniqueSource = nullptr;
        ULBFactoryProcessPortComponent* UniqueTarget = nullptr;
        if (Source->PortId.IsNone() || Target->PortId.IsNone() || PairKeys.Contains(PairKey)
            || !ResolveUniquePort(*World, Source->PortId, UniqueSource)
            || !ResolveUniquePort(*World, Target->PortId, UniqueTarget)
            || UniqueSource != Source || UniqueTarget != Target
            || Source->Direction != ELBFactoryPortDirection::Output
            || Target->Direction != ELBFactoryPortDirection::Input
            || Source->ProcessStage + 1 != Target->ProcessStage
            || Source->TransportKind != Target->TransportKind
            || Source->MaterialClass != Target->MaterialClass
            || FVector::Distance(Source->GetComponentLocation(), Target->GetComponentLocation())
                > FMath::Min(Source->MaximumAutomaticLinkDistanceCm,
                    Target->MaximumAutomaticLinkDistanceCm)
            || Link->GetTransferredUnits() < 0
            || !Source->HasTransportLink(Link) || !Target->HasTransportLink(Link)
            || !Source->IsConnectedTo(Target) || !Target->IsConnectedTo(Source))
        {
            OutStates.Reset();
            OutReason = TEXT("ACTOR TRANSPORT GRAPH HAS AMBIGUOUS IDENTITIES OR HALF-CONNECTED PORT CACHES");
            return false;
        }
        PairKeys.Add(PairKey);
        CapturedLinks.Add(Link);
        FLBFactoryTransportLinkSaveState& State = OutStates.AddDefaulted_GetRef();
        State.SourcePortId = Source->PortId;
        State.TargetPortId = Target->PortId;
        State.TransferredUnits = Link->GetTransferredUnits();
    }

    TArray<ULBFactoryProcessPortComponent*> ActorPorts;
    const_cast<AActor*>(Actor)->GetComponents(ActorPorts);
    for (const ULBFactoryProcessPortComponent* Port : ActorPorts)
    {
        if (!Port || Port->GetConnectedPortCacheCount() != Port->GetTransportLinkCacheCount())
        {
            OutStates.Reset();
            OutReason = TEXT("ACTOR PROCESS PORT CACHES ARE NOT COHERENT");
            return false;
        }
        for (int32 Index = 0; Index < Port->GetTransportLinkCacheCount(); ++Index)
        {
            const ALBFactoryTransportLink* Link = Port->GetTransportLinkAt(Index);
            const ULBFactoryProcessPortComponent* Remote = Port->GetConnectedPortAt(Index);
            if (!IsValid(Link) || !Remote || !CapturedLinks.Contains(Link)
                || !Remote->HasTransportLink(Link) || !Remote->IsConnectedTo(Port))
            {
                OutStates.Reset();
                OutReason = TEXT("ACTOR PROCESS PORT CACHE DOES NOT MATCH WORLD LINK INVENTORY");
                return false;
            }
        }
    }
    OutStates.Sort(ConnectionStateLess);
    OutReason = FString::Printf(TEXT("CAPTURED %d EXACT ACTOR TRANSPORT LINK(S)"), OutStates.Num());
    return true;
}

bool ULBFactoryConnectionSubsystem::RebuildActorConnections(AActor* Actor,
    const TArray<FLBFactoryTransportLinkSaveState>& ExactStates, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World || !IsValid(Actor) || Actor->GetWorld() != World)
    {
        OutReason = TEXT("EDITED ACTOR IS NOT IN THIS FACTORY WORLD");
        return false;
    }

    TArray<FLBFactoryTransportLinkSaveState> CurrentStates;
    if (!CaptureConnectionsForActor(Actor, CurrentStates, OutReason)) return false;
    TArray<FLBFactoryTransportLinkSaveState> SortedExactStates = ExactStates;
    SortedExactStates.Sort(ConnectionStateLess);
    if (!ConnectionStatesEqual(CurrentStates, SortedExactStates))
    {
        OutReason = TEXT("ACTOR TRANSPORT GRAPH CHANGED AFTER THE EDIT SNAPSHOT");
        return false;
    }

    struct FResolvedConnection
    {
        FLBFactoryTransportLinkSaveState State;
        ULBFactoryProcessPortComponent* Source = nullptr;
        ULBFactoryProcessPortComponent* Target = nullptr;
    };
    TArray<FResolvedConnection> Resolved;
    TSet<FString> PairKeys;
    TMap<ULBFactoryProcessPortComponent*, int32> ReplacementCounts;
    for (const FLBFactoryTransportLinkSaveState& State : SortedExactStates)
    {
        ULBFactoryProcessPortComponent* Source = nullptr;
        ULBFactoryProcessPortComponent* Target = nullptr;
        const FString PairKey = ConnectionPairKey(State.SourcePortId, State.TargetPortId);
        if (State.Version != 1 || State.TransferredUnits < 0 || PairKeys.Contains(PairKey)
            || !ResolveUniquePort(*World, State.SourcePortId, Source)
            || !ResolveUniquePort(*World, State.TargetPortId, Target)
            || !Source || !Target || Source == Target
            || (Source->GetOwner() != Actor && Target->GetOwner() != Actor)
            || Source->Direction != ELBFactoryPortDirection::Output
            || Target->Direction != ELBFactoryPortDirection::Input
            || Source->ProcessStage + 1 != Target->ProcessStage
            || Source->TransportKind != Target->TransportKind
            || Source->MaterialClass != Target->MaterialClass
            || FVector::Distance(Source->GetComponentLocation(), Target->GetComponentLocation())
                > FMath::Min(Source->MaximumAutomaticLinkDistanceCm,
                    Target->MaximumAutomaticLinkDistanceCm))
        {
            OutReason = TEXT("PROPOSED ACTOR TRANSPORT RECONNECTION IS INVALID");
            return false;
        }
        PairKeys.Add(PairKey);
        ++ReplacementCounts.FindOrAdd(Source);
        ++ReplacementCounts.FindOrAdd(Target);
        Resolved.Add({State, Source, Target});
    }

    TMap<ULBFactoryProcessPortComponent*, int32> UntouchedCounts;
    TArray<ALBFactoryTransportLink*> OldLinks;
    for (TActorIterator<ALBFactoryTransportLink> It(World); It; ++It)
    {
        ALBFactoryTransportLink* Link = *It;
        ULBFactoryProcessPortComponent* Source = Link ? Link->GetSourcePort() : nullptr;
        ULBFactoryProcessPortComponent* Target = Link ? Link->GetTargetPort() : nullptr;
        if (!IsValid(Link) || !Source || !Target)
        {
            OutReason = TEXT("WORLD TRANSPORT LINK INVENTORY IS INCOMPLETE");
            return false;
        }
        if (Source->GetOwner() == Actor || Target->GetOwner() == Actor)
            OldLinks.Add(Link);
        else
        {
            ++UntouchedCounts.FindOrAdd(Source);
            ++UntouchedCounts.FindOrAdd(Target);
        }
    }
    for (const TPair<ULBFactoryProcessPortComponent*, int32>& Pair : ReplacementCounts)
    {
        ULBFactoryProcessPortComponent* Port = Pair.Key;
        if (!Port || UntouchedCounts.FindRef(Port) + Pair.Value
            > FMath::Max(1, Port->MaximumConnections))
        {
            OutReason = TEXT("PROPOSED ACTOR TRANSPORT RECONNECTION EXCEEDS PORT CAPACITY");
            return false;
        }
    }

    // Nothing live changes until every route visual and transfer counter is staged.
    TArray<ALBFactoryTransportLink*> StagedLinks;
    StagedLinks.Reserve(Resolved.Num());
    for (const FResolvedConnection& Connection : Resolved)
    {
        ALBFactoryTransportLink* Link = World->SpawnActor<ALBFactoryTransportLink>();
        if (!Link || !Link->Configure(Connection.Source, Connection.Target)
            || (Connection.State.TransferredUnits > 0
                && !Link->TryTransferUnits(Connection.State.TransferredUnits)))
        {
            if (Link) Link->Destroy();
            for (ALBFactoryTransportLink* Staged : StagedLinks)
                if (Staged) Staged->Destroy();
            OutReason = TEXT("ACTOR TRANSPORT RECONNECTION COULD NOT BE STAGED");
            return false;
        }
        StagedLinks.Add(Link);
    }

    for (ALBFactoryTransportLink* OldLink : OldLinks)
        RemoveLinkFromEveryPortCache(*World, OldLink);
    for (int32 Index = 0; Index < Resolved.Num(); ++Index)
    {
        Resolved[Index].Source->SetConnection(Resolved[Index].Target, StagedLinks[Index]);
        Resolved[Index].Target->SetConnection(Resolved[Index].Source, StagedLinks[Index]);
    }
    for (ALBFactoryTransportLink* OldLink : OldLinks)
        if (OldLink) OldLink->Destroy();

    OutReason = FString::Printf(TEXT("REBUILT %d EXACT ACTOR TRANSPORT LINK(S)"),
        StagedLinks.Num());
    return true;
}

bool ULBFactoryConnectionSubsystem::RestoreConnections(
    const TArray<FLBFactoryTransportLinkSaveState>& States, FString& OutReason)
{
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("FACTORY CONNECTION WORLD IS OFFLINE");
        return false;
    }
    TMap<FName, ULBFactoryProcessPortComponent*> PortsById;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        TArray<ULBFactoryProcessPortComponent*> Ports;
        (*It)->GetComponents(Ports);
        for (ULBFactoryProcessPortComponent* Port : Ports)
        {
            if (!Port || Port->PortId.IsNone() || PortsById.Contains(Port->PortId))
            {
                OutReason = TEXT("PROCESS PORT IDENTITIES ARE MISSING OR DUPLICATED");
                return false;
            }
            PortsById.Add(Port->PortId, Port);
        }
    }
    TSet<FName> PairIds;
    TMap<ULBFactoryProcessPortComponent*, int32> SavedConnectionCounts;
    for (const FLBFactoryTransportLinkSaveState& State : States)
    {
        const FName PairId(*FString::Printf(TEXT("%s>%s"),
            *State.SourcePortId.ToString(), *State.TargetPortId.ToString()));
        ULBFactoryProcessPortComponent* Source = PortsById.FindRef(State.SourcePortId);
        ULBFactoryProcessPortComponent* Target = PortsById.FindRef(State.TargetPortId);
        if (State.Version != 1 || State.SourcePortId.IsNone() || State.TargetPortId.IsNone()
            || State.TransferredUnits < 0 || PairIds.Contains(PairId)
            || !Source || !Target || Source == Target
            || Source->Direction != ELBFactoryPortDirection::Output
            || Target->Direction != ELBFactoryPortDirection::Input
            || Source->ProcessStage + 1 != Target->ProcessStage
            || Source->TransportKind != Target->TransportKind
            || Source->MaterialClass != Target->MaterialClass
            || FVector::Distance(Source->GetComponentLocation(), Target->GetComponentLocation())
                > FMath::Min(Source->MaximumAutomaticLinkDistanceCm,
                    Target->MaximumAutomaticLinkDistanceCm))
        {
            OutReason = TEXT("SAVED TRANSPORT CONNECTION SET IS INVALID");
            return false;
        }
        const int32 SourceCount = ++SavedConnectionCounts.FindOrAdd(Source);
        const int32 TargetCount = ++SavedConnectionCounts.FindOrAdd(Target);
        if (SourceCount > FMath::Max(1, Source->MaximumConnections)
            || TargetCount > FMath::Max(1, Target->MaximumConnections))
        {
            OutReason = TEXT("SAVED TRANSPORT CONNECTION SET EXCEEDS AN AUTHORED PORT CAPACITY");
            return false;
        }
        PairIds.Add(PairId);
    }

    // Stage the complete replacement graph first. Existing port/link authority is not touched
    // unless every saved route visual and transfer counter can be constructed successfully.
    TArray<ALBFactoryTransportLink*> ExistingLinks;
    for (TActorIterator<ALBFactoryTransportLink> It(World); It; ++It)
        if (IsValid(*It)) ExistingLinks.Add(*It);
    TArray<ALBFactoryTransportLink*> StagedLinks;
    StagedLinks.Reserve(States.Num());
    for (int32 StateIndex = 0; StateIndex < States.Num(); ++StateIndex)
    {
        const FLBFactoryTransportLinkSaveState& State = States[StateIndex];
        ULBFactoryProcessPortComponent* Source = PortsById[State.SourcePortId];
        ULBFactoryProcessPortComponent* Target = PortsById[State.TargetPortId];
        ALBFactoryTransportLink* Link = World->SpawnActor<ALBFactoryTransportLink>();
        if (!Link || !Link->Configure(Source, Target)
            || (State.TransferredUnits > 0 && !Link->TryTransferUnits(State.TransferredUnits)))
        {
            if (Link) Link->Destroy();
            for (ALBFactoryTransportLink* Staged : StagedLinks)
                if (Staged) Staged->Destroy();
            OutReason = TEXT("SAVED TRANSPORT ROUTE VISUAL COULD NOT BE STAGED");
            return false;
        }
        StagedLinks.Add(Link);
    }

    for (TPair<FName, ULBFactoryProcessPortComponent*>& Pair : PortsById)
        Pair.Value->ClearConnection();
    for (int32 StateIndex = 0; StateIndex < States.Num(); ++StateIndex)
    {
        const FLBFactoryTransportLinkSaveState& State = States[StateIndex];
        ULBFactoryProcessPortComponent* Source = PortsById[State.SourcePortId];
        ULBFactoryProcessPortComponent* Target = PortsById[State.TargetPortId];
        Source->SetConnection(Target, StagedLinks[StateIndex]);
        Target->SetConnection(Source, StagedLinks[StateIndex]);
    }
    for (ALBFactoryTransportLink* Existing : ExistingLinks)
        if (Existing) Existing->Destroy();
    OutReason = FString::Printf(TEXT("RESTORED %d AUTOMATIC TRANSPORT LINK(S)"), StagedLinks.Num());
    return true;
}
