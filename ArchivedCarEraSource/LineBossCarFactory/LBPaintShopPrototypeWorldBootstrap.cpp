#include "LBPaintShopPrototypeWorldBootstrap.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBPaintShopBuildAuthority.h"
#include "LBPaintShopCellActor.h"
#include "LBPaintShopPrototypeRuntime.h"

namespace LBPaintShopPrototypeWorldBootstrapPrivate
{
    template<typename ActorType>
    TArray<ActorType*> FindLiveActors(UWorld* World)
    {
        TArray<ActorType*> Result;
        if (!World) return Result;
        for (TActorIterator<ActorType> It(World); It; ++It)
        {
            ActorType* Actor = *It;
            if (IsValid(Actor) && !Actor->IsActorBeingDestroyed())
            {
                Result.Add(Actor);
            }
        }
        return Result;
    }
}

ALBPaintShopPrototypeWorldBootstrap::ALBPaintShopPrototypeWorldBootstrap()
{
    PrimaryActorTick.bCanEverTick = false;
    PrimaryActorTick.bStartWithTickEnabled = false;
    SetActorEnableCollision(false);
    SetReplicates(false);
    Tags.AddUnique(TEXT("LB.PaintShop.Experimental.WorldBootstrap.v001"));
}

void ALBPaintShopPrototypeWorldBootstrap::BeginPlay()
{
    Super::BeginPlay();
    FString IgnoredReason;
    InitializePrototypeWorld(IgnoredReason);
}

bool ALBPaintShopPrototypeWorldBootstrap::ValidateSpawnPreconditions(
    const int32 ExistingBuildAuthorityCount, const int32 ExistingRuntimeCount,
    FString& OutReason)
{
    OutReason.Reset();
    if (ExistingBuildAuthorityCount < 0 || ExistingRuntimeCount < 0)
    {
        OutReason = TEXT("PAINT SHOP PROTOTYPE AUTHORITY COUNTS ARE INVALID");
        return false;
    }
    if (ExistingBuildAuthorityCount != 0 || ExistingRuntimeCount != 0)
    {
        OutReason = TEXT("PAINT SHOP PROTOTYPE REQUIRES AN EMPTY PAINT AUTHORITY WORLD");
        return false;
    }
    return true;
}

bool ALBPaintShopPrototypeWorldBootstrap::HasCoherentReadyState(FString& OutReason) const
{
    OutReason.Reset();
    UWorld* World = GetWorld();
    if (!World || !IsValid(BuildAuthority) || !IsValid(Runtime)
        || BuildAuthority->IsActorBeingDestroyed() || Runtime->IsActorBeingDestroyed())
    {
        OutReason = TEXT("PAINT SHOP PROTOTYPE READY AUTHORITIES ARE MISSING");
        return false;
    }

    const TArray<ALBPaintShopBuildAuthority*> Authorities =
        LBPaintShopPrototypeWorldBootstrapPrivate::FindLiveActors<
            ALBPaintShopBuildAuthority>(World);
    const TArray<ALBPaintShopPrototypeRuntime*> Runtimes =
        LBPaintShopPrototypeWorldBootstrapPrivate::FindLiveActors<
            ALBPaintShopPrototypeRuntime>(World);
    const FLBPaintShopApprovedEDCoatLayoutItem Approved =
        ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
    ALBPaintShopCellActor* Cell = BuildAuthority->FindCell(Approved.CellId);
    FString PlacementReason;
    const bool bApprovedPlacement = Cell && Cell->IsConfigured()
        && Cell->GetCellId() == Approved.CellId
        && Cell->GetDefinitionId() == Approved.DefinitionId
        && BuildAuthority->ValidateApprovedCellPlacement(
            Cell->GetDefinitionId(), Cell->GetActorTransform(), PlacementReason);
    if (Authorities.Num() != 1 || Runtimes.Num() != 1
        || Authorities[0] != BuildAuthority || Runtimes[0] != Runtime
        || BuildAuthority->GetOwner() != this || Runtime->GetOwner() != this
        || !Runtime->IsInitialized() || Runtime->GetBuildAuthority() != BuildAuthority
        || !bApprovedPlacement || Cell->GetOwner() != BuildAuthority
        || Runtime->GetEDCoatCell() != Cell)
    {
        OutReason = PlacementReason.IsEmpty()
            ? TEXT("PAINT SHOP PROTOTYPE READY STATE IS INCOHERENT")
            : PlacementReason;
        return false;
    }
    return true;
}

bool ALBPaintShopPrototypeWorldBootstrap::FailInitialization(
    ALBPaintShopBuildAuthority* StagedBuildAuthority,
    ALBPaintShopPrototypeRuntime* StagedRuntime, const FString& FailureReason,
    FString& OutReason)
{
    const FString StableFailureReason = FailureReason;
    if (IsValid(StagedRuntime) && !StagedRuntime->IsActorBeingDestroyed())
    {
        StagedRuntime->Destroy();
    }
    if (IsValid(StagedBuildAuthority) && !StagedBuildAuthority->IsActorBeingDestroyed())
    {
        const FLBPaintShopApprovedEDCoatLayoutItem Approved =
            ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
        if (ALBPaintShopCellActor* Cell = StagedBuildAuthority->FindCell(Approved.CellId))
        {
            Cell->Destroy();
        }
        StagedBuildAuthority->Destroy();
    }

    BuildAuthority = nullptr;
    Runtime = nullptr;
    BootstrapState = ELBPaintShopPrototypeBootstrapState::Failed;
    BootstrapReason = StableFailureReason.IsEmpty()
        ? TEXT("PAINT SHOP PROTOTYPE INITIALIZATION FAILED") : StableFailureReason;
    OutReason = BootstrapReason;
    return false;
}

bool ALBPaintShopPrototypeWorldBootstrap::InitializePrototypeWorld(FString& OutReason)
{
    OutReason.Reset();
    if (BootstrapState == ELBPaintShopPrototypeBootstrapState::Ready)
    {
        if (HasCoherentReadyState(OutReason))
        {
            OutReason = BootstrapReason;
            return true;
        }
        return FailInitialization(BuildAuthority.Get(), Runtime.Get(), OutReason, OutReason);
    }
    if (BootstrapState == ELBPaintShopPrototypeBootstrapState::Failed)
    {
        OutReason = BootstrapReason;
        return false;
    }
    if (BootstrapState == ELBPaintShopPrototypeBootstrapState::Initializing)
    {
        return FailInitialization(BuildAuthority.Get(), Runtime.Get(),
            TEXT("PAINT SHOP PROTOTYPE INITIALIZATION REENTERED"), OutReason);
    }

    UWorld* World = GetWorld();
    if (!World)
    {
        return FailInitialization(nullptr, nullptr,
            TEXT("PAINT SHOP PROTOTYPE REQUIRES A WORLD"), OutReason);
    }
    if (World->GetNetMode() == NM_Client)
    {
        return FailInitialization(nullptr, nullptr,
            TEXT("PAINT SHOP PROTOTYPE AUTHORITIES ARE SERVER-ONLY"), OutReason);
    }

    const TArray<ALBPaintShopBuildAuthority*> ExistingAuthorities =
        LBPaintShopPrototypeWorldBootstrapPrivate::FindLiveActors<
            ALBPaintShopBuildAuthority>(World);
    const TArray<ALBPaintShopPrototypeRuntime*> ExistingRuntimes =
        LBPaintShopPrototypeWorldBootstrapPrivate::FindLiveActors<
            ALBPaintShopPrototypeRuntime>(World);
    if (!ValidateSpawnPreconditions(ExistingAuthorities.Num(), ExistingRuntimes.Num(), OutReason))
    {
        return FailInitialization(nullptr, nullptr, OutReason, OutReason);
    }

    BootstrapState = ELBPaintShopPrototypeBootstrapState::Initializing;
    BootstrapReason = TEXT("PAINT SHOP PROTOTYPE AUTHORITIES ARE INITIALIZING");

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.Owner = this;
    SpawnParameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ALBPaintShopBuildAuthority* NewBuildAuthority =
        World->SpawnActor<ALBPaintShopBuildAuthority>(
            ALBPaintShopBuildAuthority::StaticClass(), FTransform::Identity,
            SpawnParameters);
    ALBPaintShopPrototypeRuntime* NewRuntime =
        World->SpawnActor<ALBPaintShopPrototypeRuntime>(
            ALBPaintShopPrototypeRuntime::StaticClass(), FTransform::Identity,
            SpawnParameters);
    if (!NewBuildAuthority || !NewRuntime)
    {
        return FailInitialization(NewBuildAuthority, NewRuntime,
            TEXT("PAINT SHOP PROTOTYPE COULD NOT SPAWN ITS TWO AUTHORITIES"), OutReason);
    }

    FString StageReason;
    if (!NewRuntime->BindBuildAuthority(NewBuildAuthority, StageReason)
        || !NewRuntime->InitializePrototype(StageReason))
    {
        return FailInitialization(NewBuildAuthority, NewRuntime, StageReason, OutReason);
    }

    const FLBPaintShopApprovedEDCoatLayoutItem Approved =
        ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
    ALBPaintShopCellActor* Cell = NewBuildAuthority->FindCell(Approved.CellId);
    FString PlacementReason;
    const bool bApprovedPlacement = Cell && Cell->IsConfigured()
        && Cell->GetCellId() == Approved.CellId
        && Cell->GetDefinitionId() == Approved.DefinitionId
        && NewBuildAuthority->ValidateApprovedCellPlacement(
            Cell->GetDefinitionId(), Cell->GetActorTransform(), PlacementReason);
    const TArray<ALBPaintShopBuildAuthority*> BuiltAuthorities =
        LBPaintShopPrototypeWorldBootstrapPrivate::FindLiveActors<
            ALBPaintShopBuildAuthority>(World);
    const TArray<ALBPaintShopPrototypeRuntime*> BuiltRuntimes =
        LBPaintShopPrototypeWorldBootstrapPrivate::FindLiveActors<
            ALBPaintShopPrototypeRuntime>(World);
    if (!NewRuntime->IsInitialized() || NewRuntime->GetBuildAuthority() != NewBuildAuthority
        || !bApprovedPlacement || NewRuntime->GetEDCoatCell() != Cell
        || NewBuildAuthority->GetOwner() != this || NewRuntime->GetOwner() != this
        || Cell->GetOwner() != NewBuildAuthority
        || BuiltAuthorities.Num() != 1 || BuiltAuthorities[0] != NewBuildAuthority
        || BuiltRuntimes.Num() != 1 || BuiltRuntimes[0] != NewRuntime)
    {
        const FString FailureReason = PlacementReason.IsEmpty()
            ? TEXT("PAINT SHOP PROTOTYPE DID NOT PRODUCE ONE COHERENT ED-COAT RUNTIME")
            : PlacementReason;
        return FailInitialization(NewBuildAuthority, NewRuntime, FailureReason, OutReason);
    }

    BuildAuthority = NewBuildAuthority;
    Runtime = NewRuntime;
    BootstrapState = ELBPaintShopPrototypeBootstrapState::Ready;
    BootstrapReason = TEXT("PAINT SHOP PROTOTYPE ED-COAT CELL IS READY");
    OutReason = BootstrapReason;
    return true;
}
