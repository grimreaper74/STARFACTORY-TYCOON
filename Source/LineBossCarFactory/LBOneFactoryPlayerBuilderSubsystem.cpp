#include "LBOneFactoryPlayerBuilderSubsystem.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryMachineBuilderSubsystem.h"
#include "LBOneFactoryAssemblyStarterLayout.h"
#include "LBOneFactoryAssemblyStarterPresentationActor.h"
#include "LBOneFactoryBodyWeldStarterPresentationActor.h"
#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryPaintStarterPresentationActor.h"
#include "LBOneFactoryPressArtDirectionActor.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "LBOneFactoryPressFeedController.h"
#include "LBOneFactoryPressFeedPresentationActor.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "LBOneFactoryPressToolingSupportActor.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactorySaveGame.h"
#include "LBPressTrainAStation.h"
#include "LBPressShopOverheadVisualLayerActor.h"
#include "LBVehiclePanelCatalog.h"

namespace LBOneFactoryPlayerBuilderPrivate
{
    constexpr float EditStepCm = 100.0f;

    bool IsLive(const AActor* Actor)
    {
        return IsValid(Actor) && !Actor->IsActorBeingDestroyed();
    }

    template<typename AuthorityType, typename PresentationType,
        typename StateType>
    bool RestoreCommissionTransaction(AuthorityType& Authority,
        PresentationType& Presentation,
        ALBOneFactoryProductionFlowAuthority& Production,
        const StateType& LayoutBefore,
        const FLBOneFactoryProductionLedgerState& LedgerBefore,
        FString& OutDetail)
    {
        FString DataReason;
        const bool bDataRestored = Authority.RestoreLayout(
            LayoutBefore, DataReason);
        FString PresentationReason;
        const bool bPresentationRestored = Presentation.ConfigureFromLayout(
            LayoutBefore, PresentationReason);
        FString LedgerReason;
        const bool bLedgerRestored = Production.RestoreLedger(
            LedgerBefore, LedgerReason);
        OutDetail = FString::Printf(TEXT(
            "DATA %s | PRESENTATION %s | LEDGER %s"),
            bDataRestored ? TEXT("RESTORED") : *DataReason,
            bPresentationRestored ? TEXT("RESTORED") : *PresentationReason,
            bLedgerRestored ? TEXT("RESTORED") : *LedgerReason);
        return bDataRestored && bPresentationRestored && bLedgerRestored;
    }

    void DestroyCreatedActors(TArray<AActor*>& Actors)
    {
        for (int32 Index = Actors.Num() - 1; Index >= 0; --Index)
            if (IsLive(Actors[Index])) Actors[Index]->Destroy();
        Actors.Reset();
    }

    int32 RetireLegacyPressPresentationForOneFactory(UWorld* World)
    {
        // OneFactory is the fixed, curated factory experience.  The old player-
        // placeable press-train actor has a separate save/build workflow and still
        // references candidate-era art. The protected map also contains map-baked
        // StaticMeshActors from the old PressShop candidate folder and the
        // map-baked Stations/Press and Candidates/PressTrains imports. Neither may
        // coexist with the native S01-S07 presentation. Retiring them at runtime
        // preserves the old sandbox and other departments while keeping OneFactory
        // unambiguous and preventing their non-Nanite shadow cost.
        if (!World) return 0;
        TArray<AActor*> RetiredActors;
        const auto IsRetiredPressMesh = [](const UStaticMeshComponent* Component)
        {
            const UStaticMesh* Mesh = Component
                ? Component->GetStaticMesh() : nullptr;
            if (!Mesh) return false;
            const FString MeshPath = Mesh->GetPathName();
            return MeshPath.Contains(TEXT("/Game/LineBoss/Candidates/PressShop/"),
                       ESearchCase::IgnoreCase)
                || MeshPath.Contains(TEXT("/Game/LineBoss/Stations/Press/"),
                       ESearchCase::IgnoreCase)
                || MeshPath.Contains(TEXT("/Game/LineBoss/Candidates/PressTrains/"),
                       ESearchCase::IgnoreCase)
                || MeshPath.Contains(TEXT("/Game/LineBoss/Developer/Validation/BlenderApproved"),
                       ESearchCase::IgnoreCase)
                || MeshPath.Contains(TEXT("/Game/LineBoss/Developer/Validation/PressTrains/"),
                       ESearchCase::IgnoreCase);
        };
        for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
            if (IsLive(*It)) RetiredActors.AddUnique(*It);
        for (TActorIterator<AActor> It(World); It; ++It)
        {
            AActor* Actor = *It;
            if (!IsLive(Actor)) continue;
            // The guarded overhead candidate deliberately uses one shared
            // plane asset from the candidate PressShop tree.  Its dedicated
            // runtime layer class is the current presentation contract, not
            // legacy map dressing.  Exempt only that final native class;
            // tagged generic actors using the same candidate mesh must still
            // be retired by the path rule below.
            if (Actor->IsA<ALBPressShopOverheadVisualLayerActor>()) continue;
            TInlineComponentArray<UStaticMeshComponent*> MeshComponents(Actor);
            const bool bUsesRetiredPressMesh = MeshComponents.ContainsByPredicate(
                IsRetiredPressMesh);
            if (bUsesRetiredPressMesh)
            {
                // PIE can defer destruction of a level-owned StaticMeshActor.
                // Hide its retired source immediately so it can never overlap
                // the native S01-S07 train for the current frame.
                for (UStaticMeshComponent* Component : MeshComponents)
                    if (IsRetiredPressMesh(Component))
                    {
                        Component->SetVisibility(false, true);
                        Component->SetHiddenInGame(true, true);
                    }
                Actor->SetActorHiddenInGame(true);
                RetiredActors.AddUnique(Actor);
            }
        }
        for (AActor* Actor : RetiredActors) Actor->Destroy();
        return RetiredActors.Num();
    }

    bool HasActiveOrReservedWIP(
        const FLBOneFactoryPressStarterLayoutState& State)
    {
        return State.Stations.ContainsByPredicate([](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return !Station.ActiveOrReservedUnitIds.IsEmpty();
        });
    }

    bool HasActiveOrReservedWIP(
        const FLBOneFactoryAssemblyLayoutState& State)
    {
        return State.Stations.ContainsByPredicate([](
            const FLBOneFactoryAssemblyStationState& Station)
        {
            return !Station.ActiveOrReservedUnitIds.IsEmpty();
        });
    }

    bool HasActiveOrReservedWIP(
        const FLBOneFactoryBodyWeldLayoutState& State)
    {
        return State.Stations.ContainsByPredicate([](
            const FLBOneFactoryBodyWeldStationState& Station)
        {
            return !Station.ActiveOrReservedUnitIds.IsEmpty();
        });
    }

    bool HasActiveOrReservedWIP(
        const FLBOneFactoryPaintStarterLayoutState& State)
    {
        return State.Stations.ContainsByPredicate([](
            const FLBOneFactoryPaintStarterStationState& Station)
        {
            return !Station.ActiveOrReservedUnitIds.IsEmpty();
        });
    }

    FString RoleLabel(const ELBOneFactoryPressStarterRole Role)
    {
        switch (Role)
        {
        case ELBOneFactoryPressStarterRole::InboundCoilReceiving:
            return TEXT("Inbound coil receiving");
        case ELBOneFactoryPressStarterRole::WrappedCoilStorage:
            return TEXT("Wrapped coil storage");
        case ELBOneFactoryPressStarterRole::BlankPreparation:
            return TEXT("Blank preparation");
        case ELBOneFactoryPressStarterRole::PreparedBlankBuffer:
            return TEXT("Prepared blank buffer");
        case ELBOneFactoryPressStarterRole::ConfigurablePressTrain:
            return TEXT("Configurable press train");
        case ELBOneFactoryPressStarterRole::PanelInspection:
            return TEXT("Panel inspection");
        case ELBOneFactoryPressStarterRole::PanelStillageDispatch:
            return TEXT("Panel stillage dispatch");
        default:
            return TEXT("Press responsibility");
        }
    }

    FString MachineLabel(const ALBFactoryBuildMachine& Machine)
    {
        const UEnum* Enum = StaticEnum<ELBFactoryBuildMachineType>();
        const FString TypeLabel = Enum
            ? Enum->GetDisplayNameTextByValue(
                static_cast<int64>(Machine.GetMachineType())).ToString()
            : TEXT("Player machine");
        return FString::Printf(TEXT("%s [%s]"), *TypeLabel,
            *Machine.GetMachineId().ToString());
    }

    FString AssemblyPositionLabel(
        const FLBOneFactoryAssemblyStationState& Station)
    {
        FString Operations;
        for (const ELBOneFactoryAssemblyOperation Operation :
            Station.AssignedOperations)
        {
            if (!Operations.IsEmpty()) Operations += TEXT(" + ");
            Operations += ULBOneFactoryAssemblyStarterLayoutLibrary::
                GetOperationDisplayName(Operation);
        }
        if (Operations.IsEmpty()) Operations = TEXT("unassigned position");
        return FString::Printf(TEXT("Assembly %02d: %s"),
            Station.LinePosition, *Operations);
    }

    FString BodyWeldPositionLabel(
        const FLBOneFactoryBodyWeldStationState& Station)
    {
        FString Programmes;
        for (const ELBOneFactoryBodyWeldProgramme Programme :
            Station.AssignedProgrammes)
        {
            if (!Programmes.IsEmpty()) Programmes += TEXT(" + ");
            Programmes += ULBOneFactoryBodyWeldStarterLayoutLibrary::
                GetProgrammeDisplayName(Programme);
        }
        if (Programmes.IsEmpty()) Programmes = TEXT("unassigned position");
        return FString::Printf(TEXT("Body/Weld %02d: %s"),
            Station.LinePosition, *Programmes);
    }

    bool BuildBodyWeldConfigurationCandidate(
        const FLBOneFactoryBodyWeldLayoutState& Before,
        const FName TargetStationId,
        const ELBOneFactoryBodyWeldProgramme Programme,
        FLBOneFactoryBodyWeldLayoutState& OutCandidate,
        FString& OutReason)
    {
        OutCandidate = Before;
        FLBOneFactoryBodyWeldStationState* Target =
            OutCandidate.Stations.FindByPredicate([TargetStationId](
                const FLBOneFactoryBodyWeldStationState& Station)
            {
                return Station.StationId == TargetStationId;
            });
        FLBOneFactoryBodyWeldStationState* Source =
            OutCandidate.Stations.FindByPredicate([Programme](
                const FLBOneFactoryBodyWeldStationState& Station)
            {
                return Station.AssignedProgrammes.Contains(Programme);
            });
        if (!Target || !Source
            || !ULBOneFactoryBodyWeldStarterLayoutLibrary::
                StationSupportsProgramme(*Target, Programme))
        {
            OutReason = TEXT(
                "BODY/WELD PROGRAMME HAS NO COMPATIBLE AUTHORITATIVE TARGET");
            return false;
        }

        const bool bProgrammeMoves = Source != Target;
        const ELBOneFactoryBodyWeldRobotRole InitialLeft =
            Target->LeftRobotRole;
        const ELBOneFactoryBodyWeldRobotRole InitialRight =
            Target->RightRobotRole;
        if (bProgrammeMoves)
        {
            Source->AssignedProgrammes.RemoveSingle(Programme);
            Target->AssignedProgrammes.Add(Programme);
            Target->AssignedProgrammes.Sort([](
                const ELBOneFactoryBodyWeldProgramme Left,
                const ELBOneFactoryBodyWeldProgramme Right)
            {
                return static_cast<uint8>(Left)
                    < static_cast<uint8>(Right);
            });
        }

        TArray<ELBOneFactoryBodyWeldRobotRole> RequiredRoles;
        for (const ELBOneFactoryBodyWeldProgramme Assigned :
            Target->AssignedProgrammes)
        {
            const ELBOneFactoryBodyWeldRobotRole Required =
                ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    GetRequiredRobotRole(Assigned);
            if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    StationSupportsRobotRole(*Target, Required))
            {
                OutReason = TEXT(
                    "BODY/WELD TARGET ROBOT PAIR CANNOT COVER EVERY ASSIGNED PROGRAMME");
                return false;
            }
            RequiredRoles.AddUnique(Required);
        }
        if (RequiredRoles.IsEmpty() || RequiredRoles.Num() > 2)
        {
            OutReason = TEXT(
                "BODY/WELD TARGET REQUIRES AN INVALID ROBOT DUTY COMBINATION");
            return false;
        }

        ELBOneFactoryBodyWeldRobotRole DesiredLeft = Target->LeftRobotRole;
        ELBOneFactoryBodyWeldRobotRole DesiredRight = Target->RightRobotRole;
        if (!bProgrammeMoves)
        {
            if (DesiredLeft != DesiredRight)
            {
                Swap(DesiredLeft, DesiredRight);
            }
            else
            {
                const ELBOneFactoryBodyWeldRobotRole* Alternate =
                    Target->SupportedRobotRoles.FindByPredicate(
                        [DesiredLeft](
                            const ELBOneFactoryBodyWeldRobotRole Role)
                        {
                            return Role != DesiredLeft;
                        });
                if (!Alternate)
                {
                    OutReason = TEXT(
                        "BODY/WELD ROBOT PAIR HAS NO ALTERNATE COMPATIBLE DUTY");
                    return false;
                }
                DesiredLeft = *Alternate;
            }
        }
        else if (RequiredRoles.Num() == 2)
        {
            DesiredLeft = RequiredRoles[0];
            DesiredRight = RequiredRoles[1];
        }
        else if (DesiredLeft != RequiredRoles[0]
            && DesiredRight != RequiredRoles[0])
        {
            DesiredLeft = RequiredRoles[0];
            const ELBOneFactoryBodyWeldRobotRole* Alternate =
                Target->SupportedRobotRoles.FindByPredicate(
                    [DesiredLeft](
                        const ELBOneFactoryBodyWeldRobotRole Role)
                    {
                        return Role != DesiredLeft;
                    });
            DesiredRight = Alternate ? *Alternate : DesiredLeft;
        }

        Target->LeftRobotRole = DesiredLeft;
        Target->RightRobotRole = DesiredRight;
        OutCandidate.bCommissioned = false;
        OutCandidate.Revision = Before.Revision + 1;
        if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
                OutCandidate, OutReason))
        {
            return false;
        }
        if (!bProgrammeMoves
            && DesiredLeft == InitialLeft
            && DesiredRight == InitialRight)
        {
            OutReason = TEXT("BODY/WELD CONFIGURATION IS UNCHANGED");
            return false;
        }
        OutReason = bProgrammeMoves
            ? TEXT("BODY/WELD PROGRAMME AND MIRRORED ROBOT DUTIES ARE COMPATIBLE")
            : TEXT("BODY/WELD MIRRORED ROBOT DUTIES CAN BE RECONFIGURED");
        return true;
    }

    FString PaintRoleLabel(const ELBOneFactoryPaintStarterRole Role)
    {
        using R = ELBOneFactoryPaintStarterRole;
        switch (Role)
        {
        case R::BodySkidReceiving: return TEXT("Body skid receiving");
        case R::PretreatmentWash: return TEXT("Pretreatment wash");
        case R::EDCoatLogicalProcess: return TEXT("ED-coat black box");
        case R::FlashOff: return TEXT("Flash-off tunnel");
        case R::BlackBoxSprayBooth: return TEXT("Black-box spray booth");
        case R::CuringOven: return TEXT("Curing oven");
        case R::QualityLightInspection: return TEXT("Quality light inspection");
        case R::PaintedBodyDispatch: return TEXT("Painted body dispatch");
        default: return TEXT("Paint responsibility");
        }
    }

    template<typename ActorType>
    void CollectLiveActors(UWorld* World, TArray<ActorType*>& OutActors)
    {
        OutActors.Reset();
        if (!World) return;
        for (TActorIterator<ActorType> It(World); It; ++It)
        {
            if (IsLive(*It)) OutActors.Add(*It);
        }
    }
}

bool ULBOneFactoryPlayerBuilderSubsystem::IsOneFactoryBuilderWorld() const
{
    UWorld* World = GetWorld();
    if (!World) return false;
    for (TActorIterator<ALBOneFactoryBootstrap> It(World); It; ++It)
    {
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(*It)) return true;
    }
    return false;
}

bool ULBOneFactoryPlayerBuilderSubsystem::FindSingleBootstrap(
    ALBOneFactoryBootstrap*& OutBootstrap, FString& OutReason) const
{
    OutBootstrap = nullptr;
    TArray<ALBOneFactoryBootstrap*> Bootstraps;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Bootstraps);
    if (Bootstraps.Num() != 1)
    {
        OutReason = FString::Printf(
            TEXT("NEW FACTORY REQUIRES EXACTLY ONE ONEFACTORY BOOTSTRAP (FOUND %d)"),
            Bootstraps.Num());
        return false;
    }
    if (Bootstraps[0]->GetClass() != ALBOneFactoryBootstrap::StaticClass())
    {
        OutReason = TEXT("NEW FACTORY REQUIRES THE EXACT NATIVE ONEFACTORY BOOTSTRAP CLASS");
        return false;
    }
    OutBootstrap = Bootstraps[0];
    OutReason = OutBootstrap->GetBootstrapStatus();
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::FindStarterPair(
    ALBOneFactoryPressStarterLayoutAuthority*& OutAuthority,
    ALBOneFactoryPressStarterPresentationActor*& OutPresentation,
    FString& OutReason) const
{
    OutAuthority = nullptr;
    OutPresentation = nullptr;
    TArray<ALBOneFactoryPressStarterLayoutAuthority*> Authorities;
    TArray<ALBOneFactoryPressStarterPresentationActor*> Presentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Authorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Presentations);
    if (Authorities.Num() != 1 || Presentations.Num() != 1)
    {
        OutReason = FString::Printf(TEXT(
            "PRESS STARTER REQUIRES ONE DATA AUTHORITY AND ONE NATIVE PRESENTATION (FOUND %d / %d)"),
            Authorities.Num(), Presentations.Num());
        return false;
    }
    if (Authorities[0]->GetClass()
            != ALBOneFactoryPressStarterLayoutAuthority::StaticClass()
        || Presentations[0]->GetClass()
            != ALBOneFactoryPressStarterPresentationActor::StaticClass())
    {
        OutReason = TEXT("PRESS STARTER PAIR MUST USE THE EXACT NATIVE CLASSES");
        return false;
    }
    OutAuthority = Authorities[0];
    OutPresentation = Presentations[0];
    OutReason = TEXT("EXACT PRESS STARTER DATA AND PRESENTATION PAIR FOUND");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::FindAssemblyStarterPair(
    ALBOneFactoryAssemblyStarterLayoutAuthority*& OutAuthority,
    ALBOneFactoryAssemblyStarterPresentationActor*& OutPresentation,
    FString& OutReason) const
{
    OutAuthority = nullptr;
    OutPresentation = nullptr;
    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*> Authorities;
    TArray<ALBOneFactoryAssemblyStarterPresentationActor*> Presentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Authorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Presentations);
    if (Authorities.Num() != 1 || Presentations.Num() != 1)
    {
        OutReason = FString::Printf(TEXT(
            "ASSEMBLY STARTER REQUIRES ONE DATA AUTHORITY AND ONE NATIVE PRESENTATION (FOUND %d / %d)"),
            Authorities.Num(), Presentations.Num());
        return false;
    }
    if (Authorities[0]->GetClass()
            != ALBOneFactoryAssemblyStarterLayoutAuthority::StaticClass()
        || Presentations[0]->GetClass()
            != ALBOneFactoryAssemblyStarterPresentationActor::StaticClass())
    {
        OutReason = TEXT(
            "ASSEMBLY STARTER PAIR MUST USE THE EXACT NATIVE CLASSES");
        return false;
    }
    OutAuthority = Authorities[0];
    OutPresentation = Presentations[0];
    OutReason = TEXT(
        "EXACT ASSEMBLY STARTER DATA AND PRESENTATION PAIR FOUND");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::FindBodyWeldStarterPair(
    ALBOneFactoryBodyWeldStarterLayoutAuthority*& OutAuthority,
    ALBOneFactoryBodyWeldStarterPresentationActor*& OutPresentation,
    FString& OutReason) const
{
    OutAuthority = nullptr;
    OutPresentation = nullptr;
    TArray<ALBOneFactoryBodyWeldStarterLayoutAuthority*> Authorities;
    TArray<ALBOneFactoryBodyWeldStarterPresentationActor*> Presentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), Authorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), Presentations);
    if (Authorities.Num() != 1 || Presentations.Num() != 1)
    {
        OutReason = FString::Printf(TEXT(
            "BODY/WELD STARTER REQUIRES ONE DATA AUTHORITY AND ONE NATIVE PRESENTATION (FOUND %d / %d)"),
            Authorities.Num(), Presentations.Num());
        return false;
    }
    if (Authorities[0]->GetClass()
            != ALBOneFactoryBodyWeldStarterLayoutAuthority::StaticClass()
        || Presentations[0]->GetClass()
            != ALBOneFactoryBodyWeldStarterPresentationActor::StaticClass())
    {
        OutReason = TEXT(
            "BODY/WELD STARTER PAIR MUST USE THE EXACT NATIVE CLASSES");
        return false;
    }
    OutAuthority = Authorities[0];
    OutPresentation = Presentations[0];
    OutReason = TEXT(
        "EXACT BODY/WELD STARTER DATA AND PRESENTATION PAIR FOUND");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::FindPaintStarterPair(
    ALBOneFactoryPaintStarterLayoutAuthority*& OutAuthority,
    ALBOneFactoryPaintStarterPresentationActor*& OutPresentation,
    FString& OutReason) const
{
    OutAuthority = nullptr;
    OutPresentation = nullptr;
    TArray<ALBOneFactoryPaintStarterLayoutAuthority*> Authorities;
    TArray<ALBOneFactoryPaintStarterPresentationActor*> Presentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Authorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), Presentations);
    if (Authorities.Num() != 1 || Presentations.Num() != 1)
    {
        OutReason = FString::Printf(TEXT(
            "PAINT STARTER REQUIRES ONE DATA AUTHORITY AND ONE NATIVE PRESENTATION (FOUND %d / %d)"),
            Authorities.Num(), Presentations.Num());
        return false;
    }
    if (Authorities[0]->GetClass()
            != ALBOneFactoryPaintStarterLayoutAuthority::StaticClass()
        || Presentations[0]->GetClass()
            != ALBOneFactoryPaintStarterPresentationActor::StaticClass())
    {
        OutReason = TEXT(
            "PAINT STARTER PAIR MUST USE THE EXACT NATIVE CLASSES");
        return false;
    }
    OutAuthority = Authorities[0];
    OutPresentation = Presentations[0];
    OutReason = TEXT("EXACT PAINT STARTER DATA AND PRESENTATION PAIR FOUND");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::FindRuntimeBackbone(
    ALBOneFactoryProductionFlowAuthority*& OutProduction,
    ALBOneFactoryRuntimeCoordinator*& OutCoordinator,
    FString& OutReason) const
{
    OutProduction = nullptr;
    OutCoordinator = nullptr;
    TArray<ALBOneFactoryProductionFlowAuthority*> ProductionActors;
    TArray<ALBOneFactoryRuntimeCoordinator*> Coordinators;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), ProductionActors);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), Coordinators);
    if (ProductionActors.Num() != 1 || Coordinators.Num() != 1)
    {
        OutReason = FString::Printf(TEXT(
            "ONEFACTORY PLAYER BUILDER REQUIRES ONE PRODUCTION FLOW AUTHORITY AND ONE RUNTIME COORDINATOR (FOUND %d / %d)"),
            ProductionActors.Num(), Coordinators.Num());
        return false;
    }
    if (ProductionActors[0]->GetClass()
            != ALBOneFactoryProductionFlowAuthority::StaticClass()
        || Coordinators[0]->GetClass()
            != ALBOneFactoryRuntimeCoordinator::StaticClass()
        || !ProductionActors[0]->ActorHasTag(
            ALBOneFactoryProductionFlowAuthority::GetAuthorityTag())
        || !Coordinators[0]->ActorHasTag(
            ALBOneFactoryRuntimeCoordinator::GetCoordinatorTag()))
    {
        OutReason = TEXT(
            "ONEFACTORY PLAYER BUILDER RUNTIME BACKBONE IDENTITY FAILED");
        return false;
    }
    OutProduction = ProductionActors[0];
    OutCoordinator = Coordinators[0];
    OutReason = TEXT("ONEFACTORY PLAYER BUILDER RUNTIME BACKBONE READY");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ValidateStarterPair(
    const ALBOneFactoryPressStarterLayoutAuthority& Authority,
    const ALBOneFactoryPressStarterPresentationActor& Presentation,
    FString& OutReason) const
{
    const FLBOneFactoryPressStarterLayoutState State = Authority.CaptureLayout();
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            State, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS STARTER DATA IS INVALID: %s"),
            *OutReason);
        return false;
    }
    if (!Authority.ActorHasTag(
            ALBOneFactoryPressStarterLayoutAuthority::GetAuthorityTag())
        || !Authority.ActorHasTag(
            ALBOneFactoryPressStarterLayoutAuthority::GetNativeOnlyTag()))
    {
        OutReason = TEXT("PRESS STARTER DATA AUTHORITY LOST ITS NATIVE-ONLY IDENTITY");
        return false;
    }

    const FLBOneFactoryPressNativeOnlyProfile Profile =
        ULBOneFactoryPressStarterLayoutLibrary::MakeNativeOnlyProfile();
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
            ELBOneFactoryAssetProvenance::NativeCode, OutReason))
    {
        return false;
    }
    if (!Presentation.ActorHasTag(
            ALBOneFactoryPressStarterPresentationActor::GetPresentationTag())
        || !Presentation.ActorHasTag(
            TEXT("LB.OneFactory.PressStarter.NativeProcedural"))
        || Presentation.RepresentsProcessWIP())
    {
        OutReason = TEXT("PRESS PRESENTATION IDENTITY OR ZERO-WIP CONTRACT FAILED");
        return false;
    }
    const TArray<FSoftObjectPath> RequiredAssets =
        ALBOneFactoryPressStarterPresentationActor::GetRequiredNativeAssetPaths();
    if (!ALBOneFactoryPressStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPressStarterPresentationActor::
                    GetPresentationClassPath(),
                RequiredAssets, OutReason))
    {
        return false;
    }
    for (const FSoftObjectPath& Asset : RequiredAssets)
    {
        if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(
                Profile,
                ALBOneFactoryPressStarterPresentationActor::
                    GetPresentationClassPath(),
                Asset.ToString(),
                ELBOneFactoryAssetProvenance::NativeProcedural, OutReason))
        {
            return false;
        }
    }

    // ConfigureFromLayout already performs the full 268-item contract check.
    // Runtime UI refreshes only verify its externally observable postconditions;
    // rebuilding the entire expected item array every UI refresh would be wasteful.
    if (!Presentation.IsPresentationConfigured()
        || Presentation.GetConfiguredLayoutId() != State.LayoutId
        || Presentation.GetConfiguredLayoutRevision() != State.Revision
        || Presentation.GetVisualBatchCount()
            != ALBOneFactoryPressStarterPresentationActor::
                GetExpectedVisualBatchCount()
        || Presentation.GetVisibleInstanceCount()
            != ALBOneFactoryPressStarterPresentationActor::
                GetExpectedVisibleInstanceCount())
    {
        OutReason = TEXT("PRESS PRESENTATION DOES NOT MATCH THE LIVE DATA REVISION");
        return false;
    }
    for (const FLBOneFactoryPressStarterStationState& Station : State.Stations)
    {
        FTransform PresentedTransform;
        if (!Presentation.GetConfiguredStationTransform(
                Station.StationId, PresentedTransform)
            || !PresentedTransform.Equals(Station.WorldTransform, 0.01f))
        {
            OutReason = FString::Printf(
                TEXT("PRESS PRESENTATION TRANSFORM DRIFTED FOR %s"),
                *Station.StationId.ToString());
            return false;
        }
    }
    OutReason = TEXT(
        "PRESS STARTER DATA AND 268-PRIMITIVE PRESENTATION ARE COHERENT AND NATIVE-ONLY");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ValidateAssemblyStarterPair(
    const ALBOneFactoryAssemblyStarterLayoutAuthority& Authority,
    const ALBOneFactoryAssemblyStarterPresentationActor& Presentation,
    FString& OutReason) const
{
    const FLBOneFactoryAssemblyLayoutState State = Authority.CaptureLayout();
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            State, OutReason))
    {
        OutReason = FString::Printf(TEXT("ASSEMBLY STARTER DATA IS INVALID: %s"),
            *OutReason);
        return false;
    }
    if (!Authority.ActorHasTag(
            ALBOneFactoryAssemblyStarterLayoutAuthority::GetAuthorityTag())
        || !Authority.ActorHasTag(
            ALBOneFactoryAssemblyStarterLayoutAuthority::GetNativeOnlyTag())
        || !Presentation.ActorHasTag(
            ALBOneFactoryAssemblyStarterPresentationActor::GetPresentationTag())
        || !Presentation.ActorHasTag(
            TEXT("LB.OneFactory.AssemblyStarter.NativeAuthored"))
        || Presentation.RepresentsProcessWIP())
    {
        OutReason = TEXT(
            "ASSEMBLY STARTER DATA OR PRESENTATION LOST ITS NATIVE ZERO-WIP IDENTITY");
        return false;
    }
    if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::NativeCode,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryAssemblyStarterLayoutAuthority"),
            OutReason))
    {
        return false;
    }
    if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::NativeCode,
            ALBOneFactoryAssemblyStarterPresentationActor::
                GetPresentationClassPath(), OutReason))
    {
        return false;
    }
    if (!ALBOneFactoryAssemblyStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryAssemblyStarterPresentationActor::
                    GetPresentationClassPath(),
                ALBOneFactoryAssemblyStarterPresentationActor::
                    GetRequiredNativeAssetPaths(), OutReason))
    {
        return false;
    }
    if (!Presentation.IsPresentationConfigured()
        // Fail closed on visibility, like Body/Weld: a hidden presentation
        // passes every count check while rendering nothing.
        || Presentation.IsHidden()
        || Presentation.GetConfiguredLayoutId() != State.LayoutId
        || Presentation.GetConfiguredLayoutRevision() != State.Revision
        || Presentation.GetVisualBatchCount()
            != ALBOneFactoryAssemblyStarterPresentationActor::
                GetExpectedVisualBatchCount()
        || Presentation.GetVisibleInstanceCount()
            != ALBOneFactoryAssemblyStarterPresentationActor::
                GetExpectedVisibleInstanceCount())
    {
        OutReason = TEXT(
            "ASSEMBLY PRESENTATION DOES NOT MATCH THE LIVE DATA REVISION");
        return false;
    }
    for (const FLBOneFactoryAssemblyStationState& Station : State.Stations)
    {
        FTransform PresentedTransform;
        if (!Presentation.GetConfiguredStationTransform(
                Station.StationId, PresentedTransform)
            || !PresentedTransform.Equals(Station.WorldTransform, 0.01f))
        {
            OutReason = FString::Printf(
                TEXT("ASSEMBLY PRESENTATION TRANSFORM DRIFTED FOR %s"),
                *Station.StationId.ToString());
            return false;
        }
    }
    OutReason = TEXT(
        "ASSEMBLY DATA AND 95-INSTANCE PRESENTATION ARE COHERENT AND NATIVE-ONLY");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ValidateBodyWeldStarterPair(
    const ALBOneFactoryBodyWeldStarterLayoutAuthority& Authority,
    const ALBOneFactoryBodyWeldStarterPresentationActor& Presentation,
    FString& OutReason) const
{
    const FLBOneFactoryBodyWeldLayoutState State = Authority.CaptureLayout();
    if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            State, OutReason))
    {
        OutReason = FString::Printf(TEXT(
            "BODY/WELD STARTER DATA IS INVALID: %s"), *OutReason);
        return false;
    }
    if (!Authority.ActorHasTag(
            ALBOneFactoryBodyWeldStarterLayoutAuthority::GetAuthorityTag())
        || !Authority.ActorHasTag(
            ALBOneFactoryBodyWeldStarterLayoutAuthority::GetNativeOnlyTag())
        || !Presentation.ActorHasTag(
            ALBOneFactoryBodyWeldStarterPresentationActor::
                GetPresentationTag())
        || !Presentation.ActorHasTag(
            TEXT("LB.OneFactory.BodyWeldStarter.NativeAuthored"))
        || !Presentation.ActorHasTag(TEXT("LB.Environment.VisualOnly"))
        || !Presentation.ActorHasTag(TEXT("LB.NotProcessWIP"))
        || Presentation.RepresentsProcessWIP())
    {
        OutReason = TEXT(
            "BODY/WELD DATA OR PRESENTATION LOST ITS NATIVE ZERO-WIP IDENTITY");
        return false;
    }
    if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::NativeCode,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryBodyWeldStarterLayoutAuthority"),
            OutReason)
        || !ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::NativeCode,
            ALBOneFactoryBodyWeldStarterPresentationActor::
                GetPresentationClassPath(), OutReason)
        || !ALBOneFactoryBodyWeldStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryBodyWeldStarterPresentationActor::
                    GetPresentationClassPath(),
                ALBOneFactoryBodyWeldStarterPresentationActor::
                    GetRequiredNativeAssetPaths(), OutReason))
    {
        return false;
    }
    if (!Presentation.IsPresentationConfigured()
        // Fail closed on visibility: a configured-but-hidden presentation
        // would pass every count check while the shop renders nothing.
        || Presentation.IsHidden()
        || Presentation.GetConfiguredLayoutId() != State.LayoutId
        || Presentation.GetConfiguredLayoutRevision() != State.Revision
        || Presentation.GetVisualBatchCount()
            != ALBOneFactoryBodyWeldStarterPresentationActor::
                GetExpectedVisualBatchCount()
        || Presentation.GetVisibleInstanceCount()
            != ALBOneFactoryBodyWeldStarterPresentationActor::
                GetExpectedVisibleInstanceCount(State))
    {
        OutReason = TEXT(
            "BODY/WELD PRESENTATION DOES NOT MATCH THE COMMITTED DATA SNAPSHOT");
        return false;
    }
    for (const FLBOneFactoryBodyWeldStationState& Station : State.Stations)
    {
        FTransform PresentedTransform;
        if (!Presentation.GetConfiguredStationTransform(
                Station.StationId, PresentedTransform)
            || !PresentedTransform.Equals(Station.WorldTransform, 0.01f))
        {
            OutReason = FString::Printf(TEXT(
                "BODY/WELD PRESENTATION TRANSFORM DRIFTED FOR %s"),
                *Station.StationId.ToString());
            return false;
        }
    }
    OutReason = FString::Printf(TEXT(
        "BODY/WELD DATA AND %d-INSTANCE PRESENTATION ARE COHERENT AND NATIVE-ONLY"),
        Presentation.GetVisibleInstanceCount());
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ValidatePaintStarterPair(
    const ALBOneFactoryPaintStarterLayoutAuthority& Authority,
    const ALBOneFactoryPaintStarterPresentationActor& Presentation,
    FString& OutReason) const
{
    const FLBOneFactoryPaintStarterLayoutState State =
        Authority.CaptureLayout();
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            State, OutReason))
    {
        OutReason = FString::Printf(TEXT("PAINT STARTER DATA IS INVALID: %s"),
            *OutReason);
        return false;
    }
    if (!Authority.ActorHasTag(
            ALBOneFactoryPaintStarterLayoutAuthority::GetAuthorityTag())
        || !Authority.ActorHasTag(
            ALBOneFactoryPaintStarterLayoutAuthority::GetNativeOnlyTag())
        || !Presentation.ActorHasTag(
            ALBOneFactoryPaintStarterPresentationActor::GetPresentationTag())
        || !Presentation.ActorHasTag(
            TEXT("LB.OneFactory.PaintStarter.NativeAuthored"))
        || !Presentation.ActorHasTag(TEXT("LB.Paint.BlackBoxExteriorOnly"))
        || Presentation.RepresentsProcessWIP()
        || Presentation.ClaimsHiddenProcessInternals())
    {
        OutReason = TEXT(
            "PAINT STARTER DATA OR PRESENTATION LOST ITS NATIVE BLACK-BOX ZERO-WIP IDENTITY");
        return false;
    }

    const FLBOneFactoryPaintNativeOnlyProfile Profile =
        ULBOneFactoryPaintStarterLayoutLibrary::MakeNativeOnlyProfile();
    const FString AuthorityClassPath = TEXT(
        "/Script/LineBossCarFactory.LBOneFactoryPaintStarterLayoutAuthority");
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeReference(
            Profile, AuthorityClassPath, AuthorityClassPath,
            ELBOneFactoryAssetProvenance::NativeCode, OutReason))
    {
        return false;
    }
    if (!ALBOneFactoryPaintStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPaintStarterPresentationActor::
                    GetPresentationClassPath(),
                ALBOneFactoryPaintStarterPresentationActor::
                    GetRequiredNativeAssetPaths(), OutReason))
    {
        return false;
    }
    if (!Presentation.IsPresentationConfigured()
        // Fail closed on visibility, like Body/Weld.
        || Presentation.IsHidden()
        || Presentation.GetConfiguredLayoutId() != State.LayoutId
        || Presentation.GetConfiguredLayoutRevision() != State.Revision
        || Presentation.GetConfiguredBodyColour() != State.SelectedBodyColour
        || Presentation.GetVisualBatchCount()
            != ALBOneFactoryPaintStarterPresentationActor::
                GetExpectedVisualBatchCount()
        || Presentation.GetVisibleInstanceCount()
            != ALBOneFactoryPaintStarterPresentationActor::
                GetExpectedVisibleInstanceCount())
    {
        OutReason = TEXT(
            "PAINT PRESENTATION DOES NOT MATCH THE COMMITTED DATA SNAPSHOT");
        return false;
    }
    for (const FLBOneFactoryPaintStarterStationState& Station : State.Stations)
    {
        FTransform PresentedTransform;
        if (!Presentation.GetConfiguredStationTransform(
                Station.StationId, PresentedTransform)
            || !PresentedTransform.Equals(Station.WorldTransform, 0.01f))
        {
            OutReason = FString::Printf(
                TEXT("PAINT PRESENTATION TRANSFORM DRIFTED FOR %s"),
                *Station.StationId.ToString());
            return false;
        }
    }
    OutReason = TEXT(
        "PAINT DATA AND 32-INSTANCE BLACK-BOX PRESENTATION ARE COHERENT AND NATIVE-ONLY");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanCreateNewFactory(
    FString& OutReason) const
{
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    if (!FindSingleBootstrap(Bootstrap, OutReason)) return false;
    if (!Bootstrap->HasValidShell()
        || Bootstrap->GetBootstrapState() != ELBOneFactoryBootstrapState::Ready)
    {
        OutReason = FString::Printf(TEXT("NEW FACTORY IS LOCKED UNTIL BOOTSTRAP READY: %s"),
            *Bootstrap->GetBootstrapStatus());
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, OutReason)) return false;

    TArray<ALBOneFactoryPressStarterLayoutAuthority*> Authorities;
    TArray<ALBOneFactoryPressStarterPresentationActor*> Presentations;
    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*> AssemblyAuthorities;
    TArray<ALBOneFactoryAssemblyStarterPresentationActor*>
        AssemblyPresentations;
    TArray<ALBOneFactoryBodyWeldStarterLayoutAuthority*> BodyAuthorities;
    TArray<ALBOneFactoryBodyWeldStarterPresentationActor*>
        BodyPresentations;
    TArray<ALBOneFactoryPaintStarterLayoutAuthority*> PaintAuthorities;
    TArray<ALBOneFactoryPaintStarterPresentationActor*> PaintPresentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Authorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Presentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyPresentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), BodyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), BodyPresentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintPresentations);
    if (!Authorities.IsEmpty() || !Presentations.IsEmpty()
        || !AssemblyAuthorities.IsEmpty() || !AssemblyPresentations.IsEmpty()
        || !BodyAuthorities.IsEmpty() || !BodyPresentations.IsEmpty()
        || !PaintAuthorities.IsEmpty() || !PaintPresentations.IsEmpty())
    {
        OutReason = FString::Printf(TEXT(
            "NEW FACTORY WILL NOT OVERWRITE EXISTING OR PARTIAL STARTERS (PRESS %d/%d, BODY/WELD %d/%d, PAINT %d/%d, ASSEMBLY %d/%d)"),
            Authorities.Num(), Presentations.Num(), BodyAuthorities.Num(),
            BodyPresentations.Num(), PaintAuthorities.Num(),
            PaintPresentations.Num(), AssemblyAuthorities.Num(),
            AssemblyPresentations.Num());
        return false;
    }

    const FLBOneFactoryPressStarterLayoutState Canonical =
        ULBOneFactoryPressStarterLayoutLibrary::MakeCanonicalStarterLayout();
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            Canonical, OutReason))
    {
        return false;
    }
    const FLBOneFactoryPressNativeOnlyProfile Profile =
        ULBOneFactoryPressStarterLayoutLibrary::MakeNativeOnlyProfile();
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
            ELBOneFactoryAssetProvenance::NativeCode, OutReason))
    {
        return false;
    }
    const TArray<FSoftObjectPath> RequiredAssets =
        ALBOneFactoryPressStarterPresentationActor::GetRequiredNativeAssetPaths();
    if (!ALBOneFactoryPressStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPressStarterPresentationActor::
                    GetPresentationClassPath(),
                RequiredAssets, OutReason))
    {
        return false;
    }
    for (const FSoftObjectPath& Asset : RequiredAssets)
    {
        if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(
                Profile,
                ALBOneFactoryPressStarterPresentationActor::
                    GetPresentationClassPath(),
                Asset.ToString(),
                ELBOneFactoryAssetProvenance::NativeProcedural, OutReason))
        {
            return false;
        }
    }
    const TArray<FLBOneFactoryPressPresentationItem> ExpectedItems =
        ALBOneFactoryPressStarterPresentationActor::
            BuildExpectedPresentationItems(Canonical);
    if (!ALBOneFactoryPressStarterPresentationActor::
            ValidatePresentationContract(Canonical, ExpectedItems, OutReason))
    {
        return false;
    }
    OutReason = TEXT(
        "BOOTSTRAP READY; CANONICAL PRESS DATA AND EXACT NATIVE PRESENTATION ARE ADMITTED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanCreateBodyWeldStarter(
    FString& OutReason) const
{
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    if (!FindSingleBootstrap(Bootstrap, OutReason)
        || !Bootstrap->HasValidShell())
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT("ONEFACTORY BOOTSTRAP IS NOT READY");
        return false;
    }
    ALBOneFactoryPressStarterLayoutAuthority* PressAuthority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* PressPresentation = nullptr;
    if (!FindStarterPair(PressAuthority, PressPresentation, OutReason)
        || !ValidateStarterPair(
            *PressAuthority, *PressPresentation, OutReason))
    {
        return false;
    }
    if (!PressAuthority->IsCommissioned())
    {
        OutReason = TEXT(
            "COMMISSION THE PRESS STARTER BEFORE BUILDING BODY/WELD");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            PressAuthority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE PRESS WIP BEFORE BUILDING BODY/WELD");
        return false;
    }

    TArray<ALBOneFactoryBodyWeldStarterLayoutAuthority*> Authorities;
    TArray<ALBOneFactoryBodyWeldStarterPresentationActor*> Presentations;
    TArray<ALBOneFactoryPaintStarterLayoutAuthority*> PaintAuthorities;
    TArray<ALBOneFactoryPaintStarterPresentationActor*> PaintPresentations;
    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*> AssemblyAuthorities;
    TArray<ALBOneFactoryAssemblyStarterPresentationActor*>
        AssemblyPresentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), Authorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), Presentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintPresentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyPresentations);
    if (!Authorities.IsEmpty() || !Presentations.IsEmpty())
    {
        OutReason = FString::Printf(TEXT(
            "BODY/WELD CREATE WILL NOT OVERWRITE AN EXISTING OR PARTIAL STARTER (%d DATA / %d PRESENTATION)"),
            Authorities.Num(), Presentations.Num());
        return false;
    }
    if (!PaintAuthorities.IsEmpty() || !PaintPresentations.IsEmpty()
        || !AssemblyAuthorities.IsEmpty()
        || !AssemblyPresentations.IsEmpty())
    {
        OutReason = TEXT(
            "BODY/WELD MUST PRECEDE PAINT AND ASSEMBLY; DOWNSTREAM STARTER ACTORS EXIST");
        return false;
    }

    const FLBOneFactoryBodyWeldLayoutState Canonical =
        ULBOneFactoryBodyWeldStarterLayoutLibrary::
            MakeCanonicalStarterLayout();
    if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            Canonical, OutReason)
        || !ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::NativeCode,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryBodyWeldStarterLayoutAuthority"),
            OutReason)
        || !ALBOneFactoryBodyWeldStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryBodyWeldStarterPresentationActor::
                    GetPresentationClassPath(),
                ALBOneFactoryBodyWeldStarterPresentationActor::
                    GetRequiredNativeAssetPaths(), OutReason))
    {
        return false;
    }
    const TArray<FLBOneFactoryBodyWeldPresentationItem> ExpectedItems =
        ALBOneFactoryBodyWeldStarterPresentationActor::
            BuildExpectedPresentationItems(Canonical);
    if (!ALBOneFactoryBodyWeldStarterPresentationActor::
            ValidatePresentationContract(Canonical, ExpectedItems, OutReason))
    {
        return false;
    }
    OutReason = TEXT(
        "PRESS COMMISSIONED; CANONICAL 18-POSITION BODY/WELD DATA AND EXACT 26-BATCH NATIVE PRESENTATION ARE ADMITTED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanCreateAssemblyStarter(
    FString& OutReason) const
{
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    if (!FindSingleBootstrap(Bootstrap, OutReason)
        || !Bootstrap->HasValidShell())
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT("ONEFACTORY BOOTSTRAP IS NOT READY");
        return false;
    }
    ALBOneFactoryPressStarterLayoutAuthority* PressAuthority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* PressPresentation = nullptr;
    if (!FindStarterPair(PressAuthority, PressPresentation, OutReason)
        || !ValidateStarterPair(*PressAuthority, *PressPresentation, OutReason))
    {
        return false;
    }
    if (!PressAuthority->IsCommissioned())
    {
        OutReason = TEXT(
            "COMMISSION THE PRESS STARTER BEFORE BUILDING GENERAL ASSEMBLY");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            PressAuthority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE PRESS WIP BEFORE BUILDING GENERAL ASSEMBLY");
        return false;
    }

    ALBOneFactoryBodyWeldStarterLayoutAuthority* BodyAuthority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* BodyPresentation = nullptr;
    if (!FindBodyWeldStarterPair(
            BodyAuthority, BodyPresentation, OutReason)
        || !ValidateBodyWeldStarterPair(
            *BodyAuthority, *BodyPresentation, OutReason))
    {
        return false;
    }
    if (!BodyAuthority->IsCommissioned())
    {
        OutReason = TEXT(
            "COMMISSION BODY/WELD BEFORE BUILDING GENERAL ASSEMBLY");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            BodyAuthority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE BODY/WELD WIP BEFORE BUILDING GENERAL ASSEMBLY");
        return false;
    }

    ALBOneFactoryPaintStarterLayoutAuthority* PaintAuthority = nullptr;
    ALBOneFactoryPaintStarterPresentationActor* PaintPresentation = nullptr;
    if (!FindPaintStarterPair(
            PaintAuthority, PaintPresentation, OutReason)
        || !ValidatePaintStarterPair(
            *PaintAuthority, *PaintPresentation, OutReason))
    {
        return false;
    }
    if (!PaintAuthority->IsCommissioned())
    {
        OutReason = TEXT(
            "COMMISSION PAINT BEFORE BUILDING GENERAL ASSEMBLY");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            PaintAuthority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE PAINT WIP BEFORE BUILDING GENERAL ASSEMBLY");
        return false;
    }

    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*> Authorities;
    TArray<ALBOneFactoryAssemblyStarterPresentationActor*> Presentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Authorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Presentations);
    if (!Authorities.IsEmpty() || !Presentations.IsEmpty())
    {
        OutReason = FString::Printf(TEXT(
            "ASSEMBLY CREATE WILL NOT OVERWRITE AN EXISTING OR PARTIAL STARTER (%d DATA / %d PRESENTATION)"),
            Authorities.Num(), Presentations.Num());
        return false;
    }

    const FLBOneFactoryAssemblyLayoutState Canonical =
        ULBOneFactoryAssemblyStarterLayoutLibrary::MakeCanonicalStarterLayout();
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            Canonical, OutReason))
    {
        return false;
    }
    if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::NativeCode,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryAssemblyStarterLayoutAuthority"),
            OutReason))
    {
        return false;
    }
    if (!ALBOneFactoryAssemblyStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryAssemblyStarterPresentationActor::
                    GetPresentationClassPath(),
                ALBOneFactoryAssemblyStarterPresentationActor::
                    GetRequiredNativeAssetPaths(), OutReason))
    {
        return false;
    }
    const TArray<FLBOneFactoryAssemblyPresentationItem> ExpectedItems =
        ALBOneFactoryAssemblyStarterPresentationActor::
            BuildExpectedPresentationItems(Canonical);
    if (!ALBOneFactoryAssemblyStarterPresentationActor::
            ValidatePresentationContract(Canonical, ExpectedItems, OutReason))
    {
        return false;
    }
    OutReason = TEXT(
        "PRESS + BODY/WELD + PAINT COMMISSIONED; CANONICAL 24-POSITION ASSEMBLY DATA AND EXACT NATIVE PRESENTATION ARE ADMITTED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanCreatePaintStarter(
    FString& OutReason) const
{
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    if (!FindSingleBootstrap(Bootstrap, OutReason)
        || !Bootstrap->HasValidShell())
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT("ONEFACTORY BOOTSTRAP IS NOT READY");
        return false;
    }

    ALBOneFactoryPressStarterLayoutAuthority* PressAuthority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* PressPresentation = nullptr;
    if (!FindStarterPair(PressAuthority, PressPresentation, OutReason)
        || !ValidateStarterPair(
            *PressAuthority, *PressPresentation, OutReason))
    {
        return false;
    }
    if (!PressAuthority->IsCommissioned())
    {
        OutReason = TEXT("COMMISSION THE PRESS STARTER BEFORE PAINT");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            PressAuthority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE PRESS WIP BEFORE BUILDING THE PAINT STARTER");
        return false;
    }

    ALBOneFactoryBodyWeldStarterLayoutAuthority* BodyAuthority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* BodyPresentation = nullptr;
    if (!FindBodyWeldStarterPair(
            BodyAuthority, BodyPresentation, OutReason)
        || !ValidateBodyWeldStarterPair(
            *BodyAuthority, *BodyPresentation, OutReason))
    {
        return false;
    }
    if (!BodyAuthority->IsCommissioned())
    {
        OutReason = TEXT(
            "COMMISSION BODY/WELD BEFORE BUILDING THE PAINT STARTER");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            BodyAuthority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE BODY/WELD WIP BEFORE BUILDING THE PAINT STARTER");
        return false;
    }

    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*>
        AssemblyAuthorities;
    TArray<ALBOneFactoryAssemblyStarterPresentationActor*>
        AssemblyPresentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyPresentations);
    if (!AssemblyAuthorities.IsEmpty() || !AssemblyPresentations.IsEmpty())
    {
        OutReason = TEXT(
            "PAINT MUST PRECEDE ASSEMBLY; OUT-OF-ORDER ASSEMBLY STARTER ACTORS EXIST");
        return false;
    }

    TArray<ALBOneFactoryPaintStarterLayoutAuthority*> Authorities;
    TArray<ALBOneFactoryPaintStarterPresentationActor*> Presentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Authorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), Presentations);
    if (!Authorities.IsEmpty() || !Presentations.IsEmpty())
    {
        OutReason = FString::Printf(TEXT(
            "PAINT CREATE WILL NOT OVERWRITE AN EXISTING OR PARTIAL STARTER (%d DATA / %d PRESENTATION)"),
            Authorities.Num(), Presentations.Num());
        return false;
    }

    const FLBOneFactoryPaintStarterLayoutState Canonical =
        ULBOneFactoryPaintStarterLayoutLibrary::MakeCanonicalStarterLayout();
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            Canonical, OutReason))
    {
        return false;
    }
    const FLBOneFactoryPaintNativeOnlyProfile Profile =
        ULBOneFactoryPaintStarterLayoutLibrary::MakeNativeOnlyProfile();
    const FString AuthorityClassPath = TEXT(
        "/Script/LineBossCarFactory.LBOneFactoryPaintStarterLayoutAuthority");
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeReference(
            Profile, AuthorityClassPath, AuthorityClassPath,
            ELBOneFactoryAssetProvenance::NativeCode, OutReason))
    {
        return false;
    }
    if (!ALBOneFactoryPaintStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPaintStarterPresentationActor::
                    GetPresentationClassPath(),
                ALBOneFactoryPaintStarterPresentationActor::
                    GetRequiredNativeAssetPaths(), OutReason))
    {
        return false;
    }
    const TArray<FLBOneFactoryPaintPresentationItem> ExpectedItems =
        ALBOneFactoryPaintStarterPresentationActor::
            BuildExpectedPresentationItems(Canonical);
    if (!ALBOneFactoryPaintStarterPresentationActor::
            ValidatePresentationContract(Canonical, ExpectedItems, OutReason))
    {
        return false;
    }
    OutReason = TEXT(
        "PRESS + BODY/WELD COMMISSIONED; CANONICAL BLACK-BOX PAINT DATA AND EXACT NATIVE PRESENTATION ARE ADMITTED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CreateStarterData(
    ALBOneFactoryPressStarterLayoutAuthority*& OutAuthority,
    FString& OutReason)
{
    OutAuthority = nullptr;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("NEW FACTORY WORLD IS UNAVAILABLE");
        return false;
    }
    FActorSpawnParameters Parameters;
    Parameters.Name = TEXT("LB_OneFactory_PressStarter_Data_v001");
    Parameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    OutAuthority = World->SpawnActor<ALBOneFactoryPressStarterLayoutAuthority>(
        ALBOneFactoryPressStarterLayoutAuthority::StaticClass(),
        FTransform::Identity, Parameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(OutAuthority)
        || OutAuthority->GetClass()
            != ALBOneFactoryPressStarterLayoutAuthority::StaticClass()
        || !ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            OutAuthority->CaptureLayout(), OutReason))
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT("CANONICAL PRESS DATA AUTHORITY FAILED TO SPAWN");
        return false;
    }
    OutReason = TEXT("CANONICAL SEVEN-STATION PRESS DATA CREATED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::MaterialiseStarterPresentation(
    ALBOneFactoryPressStarterLayoutAuthority& Authority,
    ALBOneFactoryPressStarterPresentationActor*& OutPresentation,
    FString& OutReason)
{
    OutPresentation = nullptr;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("NATIVE PRESS PRESENTATION WORLD IS UNAVAILABLE");
        return false;
    }
    FActorSpawnParameters Parameters;
    Parameters.Name = TEXT("LB_OneFactory_PressStarter_Presentation_v001");
    Parameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    OutPresentation =
        World->SpawnActor<ALBOneFactoryPressStarterPresentationActor>(
            ALBOneFactoryPressStarterPresentationActor::StaticClass(),
            FTransform::Identity, Parameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(OutPresentation))
    {
        OutReason = TEXT("NATIVE PRESS PRESENTATION ACTOR FAILED TO SPAWN");
        return false;
    }
#if WITH_DEV_AUTOMATION_TESTS
    if (bForcePresentationFailureForTests)
    {
        OutReason = TEXT("FORCED PRESENTATION FAILURE FOR ATOMIC ROLLBACK TEST");
        return false;
    }
#endif
    if (!OutPresentation->ConfigureFromLayout(
            Authority.CaptureLayout(), OutReason)
        || !ValidateStarterPair(Authority, *OutPresentation, OutReason))
    {
        return false;
    }
    FActorSpawnParameters ToolingParameters;
    ToolingParameters.Name = TEXT("LB_OneFactory_PressToolingSupport_v001");
    ToolingParameters.Owner = OutPresentation;
    ToolingParameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ALBOneFactoryPressToolingSupportActor* Tooling =
        World->SpawnActor<ALBOneFactoryPressToolingSupportActor>(
            ALBOneFactoryPressToolingSupportActor::StaticClass(),
            FTransform::Identity, ToolingParameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(Tooling)
        || !Tooling->ConfigureFromPressLayout(Authority.CaptureLayout(), OutReason))
    {
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(Tooling))
            Tooling->Destroy();
        OutPresentation->Destroy();
        OutPresentation = nullptr;
        if (OutReason.IsEmpty())
            OutReason = TEXT("NATIVE PRESS TOOLING SUPPORT FAILED TO MATERIALISE");
        return false;
    }
    Tooling->AttachToActor(OutPresentation,
        FAttachmentTransformRules::KeepWorldTransform);
    FActorSpawnParameters FeedParameters;
    FeedParameters.Name = TEXT("LB_OneFactory_PressFeed_v001");
    FeedParameters.Owner = OutPresentation;
    FeedParameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ALBOneFactoryPressFeedController* Feed =
        World->SpawnActor<ALBOneFactoryPressFeedController>(
            ALBOneFactoryPressFeedController::StaticClass(),
            FTransform::Identity, FeedParameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(Feed)
        || !Feed->ConfigureAutomaticRoute(OutReason))
    {
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(Feed)) Feed->Destroy();
        Tooling->Destroy();
        OutPresentation->Destroy();
        OutPresentation = nullptr;
        if (OutReason.IsEmpty())
            OutReason = TEXT("NATIVE PR008-PR010 FEED ROUTE FAILED TO MATERIALISE");
        return false;
    }
    Feed->AttachToActor(OutPresentation,
        FAttachmentTransformRules::KeepWorldTransform);
    FActorSpawnParameters FeedVisualParameters;
    FeedVisualParameters.Name = TEXT("LB_OneFactory_PressFeedPresentation_v001");
    FeedVisualParameters.Owner = OutPresentation;
    FeedVisualParameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ALBOneFactoryPressFeedPresentationActor* FeedVisual =
        World->SpawnActor<ALBOneFactoryPressFeedPresentationActor>(
            ALBOneFactoryPressFeedPresentationActor::StaticClass(),
            FTransform::Identity, FeedVisualParameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(FeedVisual)
        || !FeedVisual->ConfigureFromPressLayout(Authority.CaptureLayout(), OutReason))
    {
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(FeedVisual)) FeedVisual->Destroy();
        Feed->Destroy(); Tooling->Destroy(); OutPresentation->Destroy();
        OutPresentation = nullptr;
        if (OutReason.IsEmpty())
            OutReason = TEXT("NATIVE PR008-PR010 PRESENTATION FAILED TO MATERIALISE");
        return false;
    }
    FeedVisual->AttachToActor(OutPresentation,
        FAttachmentTransformRules::KeepWorldTransform);
    const FLBOneFactoryPressNativeOnlyProfile PressProfile =
        ULBOneFactoryPressStarterLayoutLibrary::MakeNativeOnlyProfile();
    const TArray<FSoftObjectPath> ArtDirectionAssets =
        ALBOneFactoryPressArtDirectionActor::GetRequiredNativeAssetPaths();
    if (!ALBOneFactoryPressArtDirectionActor::ValidateNativeArtDirectionReferences(
            ArtDirectionAssets, OutReason))
    {
        FeedVisual->Destroy(); Feed->Destroy(); Tooling->Destroy();
        OutPresentation->Destroy(); OutPresentation = nullptr;
        return false;
    }
    for (const FSoftObjectPath& Asset : ArtDirectionAssets)
    {
        if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(
                PressProfile,
                ALBOneFactoryPressArtDirectionActor::GetArtDirectionClassPath(),
                Asset.ToString(), ELBOneFactoryAssetProvenance::NativeAuthored,
                OutReason))
        {
            FeedVisual->Destroy(); Feed->Destroy(); Tooling->Destroy();
            OutPresentation->Destroy(); OutPresentation = nullptr;
            return false;
        }
    }
    FActorSpawnParameters ArtDirectionParameters;
    ArtDirectionParameters.Name = TEXT("LB_OneFactory_PressArtDirection_v001");
    ArtDirectionParameters.Owner = OutPresentation;
    ArtDirectionParameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ALBOneFactoryPressArtDirectionActor* ArtDirection =
        World->SpawnActor<ALBOneFactoryPressArtDirectionActor>(
            ALBOneFactoryPressArtDirectionActor::StaticClass(),
            FTransform::Identity, ArtDirectionParameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(ArtDirection)
        || !ArtDirection->ConfigureFromPressPresentation(
            *OutPresentation, Authority.CaptureLayout(), OutReason))
    {
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(ArtDirection))
            ArtDirection->Destroy();
        FeedVisual->Destroy(); Feed->Destroy(); Tooling->Destroy();
        OutPresentation->Destroy(); OutPresentation = nullptr;
        if (OutReason.IsEmpty())
            OutReason = TEXT("NATIVE PRESS ART-DIRECTION LAYER FAILED TO MATERIALISE");
        return false;
    }
    ArtDirection->AttachToActor(OutPresentation,
        FAttachmentTransformRules::KeepWorldTransform);
    const int32 RetiredLegacyPresentationCount =
        LBOneFactoryPlayerBuilderPrivate::RetireLegacyPressPresentationForOneFactory(World);
    OutReason = RetiredLegacyPresentationCount > 0
        ? FString::Printf(TEXT("NATIVE PRESS, ART DIRECTION, TOOLING, PR008-PR010 ROUTE AND FEED PRESENTATION MATERIALISED; RETIRED %d LEGACY PRESS PRESENTATION ACTOR(S)"), RetiredLegacyPresentationCount)
        : TEXT("NATIVE PRESS, ART DIRECTION, TOOLING, PR008-PR010 ROUTE AND FEED PRESENTATION MATERIALISED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CreateBodyWeldStarterData(
    ALBOneFactoryBodyWeldStarterLayoutAuthority*& OutAuthority,
    FString& OutReason)
{
    OutAuthority = nullptr;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("BODY/WELD STARTER WORLD IS UNAVAILABLE");
        return false;
    }
    FActorSpawnParameters Parameters;
    Parameters.Name = TEXT("LB_OneFactory_BodyWeldStarter_Data_v001");
    Parameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    OutAuthority = World->SpawnActor<
        ALBOneFactoryBodyWeldStarterLayoutAuthority>(
            ALBOneFactoryBodyWeldStarterLayoutAuthority::StaticClass(),
            FTransform::Identity, Parameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(OutAuthority)
        || OutAuthority->GetClass()
            != ALBOneFactoryBodyWeldStarterLayoutAuthority::StaticClass()
        || !ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            OutAuthority->CaptureLayout(), OutReason))
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT(
                "CANONICAL BODY/WELD DATA AUTHORITY FAILED TO SPAWN");
        return false;
    }
    OutReason = TEXT("CANONICAL 18-POSITION BODY/WELD DATA CREATED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    MaterialiseBodyWeldStarterPresentation(
        ALBOneFactoryBodyWeldStarterLayoutAuthority& Authority,
        ALBOneFactoryBodyWeldStarterPresentationActor*& OutPresentation,
        FString& OutReason)
{
    OutPresentation = nullptr;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT(
            "NATIVE BODY/WELD PRESENTATION WORLD IS UNAVAILABLE");
        return false;
    }
    FActorSpawnParameters Parameters;
    Parameters.Name =
        TEXT("LB_OneFactory_BodyWeldStarter_Presentation_v002");
    Parameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    OutPresentation = World->SpawnActor<
        ALBOneFactoryBodyWeldStarterPresentationActor>(
            ALBOneFactoryBodyWeldStarterPresentationActor::StaticClass(),
            FTransform::Identity, Parameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(OutPresentation))
    {
        OutReason = TEXT(
            "NATIVE BODY/WELD PRESENTATION ACTOR FAILED TO SPAWN");
        return false;
    }
#if WITH_DEV_AUTOMATION_TESTS
    if (bForceBodyWeldPresentationFailureForTests)
    {
        OutReason = TEXT(
            "FORCED BODY/WELD PRESENTATION FAILURE FOR ATOMIC ROLLBACK TEST");
        return false;
    }
#endif
    if (!OutPresentation->ConfigureFromLayout(
            Authority.CaptureLayout(), OutReason)
        || !ValidateBodyWeldStarterPair(
            Authority, *OutPresentation, OutReason))
    {
        return false;
    }
    OutReason = TEXT(
        "EXACT NATIVE 26-BATCH BODY/WELD PRESENTATION MATERIALISED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CreateAssemblyStarterData(
    ALBOneFactoryAssemblyStarterLayoutAuthority*& OutAuthority,
    FString& OutReason)
{
    OutAuthority = nullptr;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("ASSEMBLY STARTER WORLD IS UNAVAILABLE");
        return false;
    }
    FActorSpawnParameters Parameters;
    Parameters.Name = TEXT("LB_OneFactory_AssemblyStarter_Data_v001");
    Parameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    OutAuthority =
        World->SpawnActor<ALBOneFactoryAssemblyStarterLayoutAuthority>(
            ALBOneFactoryAssemblyStarterLayoutAuthority::StaticClass(),
            FTransform::Identity, Parameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(OutAuthority)
        || OutAuthority->GetClass()
            != ALBOneFactoryAssemblyStarterLayoutAuthority::StaticClass()
        || !ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            OutAuthority->CaptureLayout(), OutReason))
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT(
                "CANONICAL ASSEMBLY DATA AUTHORITY FAILED TO SPAWN");
        return false;
    }
    OutReason = TEXT("CANONICAL 24-POSITION ASSEMBLY DATA CREATED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    MaterialiseAssemblyStarterPresentation(
        ALBOneFactoryAssemblyStarterLayoutAuthority& Authority,
        ALBOneFactoryAssemblyStarterPresentationActor*& OutPresentation,
        FString& OutReason)
{
    OutPresentation = nullptr;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("NATIVE ASSEMBLY PRESENTATION WORLD IS UNAVAILABLE");
        return false;
    }
    FActorSpawnParameters Parameters;
    Parameters.Name = TEXT("LB_OneFactory_AssemblyStarter_Presentation_v001");
    Parameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    OutPresentation =
        World->SpawnActor<ALBOneFactoryAssemblyStarterPresentationActor>(
            ALBOneFactoryAssemblyStarterPresentationActor::StaticClass(),
            FTransform::Identity, Parameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(OutPresentation))
    {
        OutReason = TEXT(
            "NATIVE ASSEMBLY PRESENTATION ACTOR FAILED TO SPAWN");
        return false;
    }
#if WITH_DEV_AUTOMATION_TESTS
    if (bForceAssemblyPresentationFailureForTests)
    {
        OutReason = TEXT(
            "FORCED ASSEMBLY PRESENTATION FAILURE FOR ATOMIC ROLLBACK TEST");
        return false;
    }
#endif
    if (!OutPresentation->ConfigureFromLayout(
            Authority.CaptureLayout(), OutReason)
        || !ValidateAssemblyStarterPair(
            Authority, *OutPresentation, OutReason))
    {
        return false;
    }
    OutReason = TEXT("EXACT NATIVE ASSEMBLY PRESENTATION MATERIALISED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CreatePaintStarterData(
    ALBOneFactoryPaintStarterLayoutAuthority*& OutAuthority,
    FString& OutReason)
{
    OutAuthority = nullptr;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("PAINT STARTER WORLD IS UNAVAILABLE");
        return false;
    }
    FActorSpawnParameters Parameters;
    Parameters.Name = TEXT("LB_OneFactory_PaintStarter_Data_v001");
    Parameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    OutAuthority = World->SpawnActor<
        ALBOneFactoryPaintStarterLayoutAuthority>(
            ALBOneFactoryPaintStarterLayoutAuthority::StaticClass(),
            FTransform::Identity, Parameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(OutAuthority)
        || OutAuthority->GetClass()
            != ALBOneFactoryPaintStarterLayoutAuthority::StaticClass()
        || !ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            OutAuthority->CaptureLayout(), OutReason))
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT("CANONICAL PAINT DATA AUTHORITY FAILED TO SPAWN");
        return false;
    }
    OutReason = TEXT("CANONICAL EIGHT-RESPONSIBILITY PAINT DATA CREATED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    MaterialisePaintStarterPresentation(
        ALBOneFactoryPaintStarterLayoutAuthority& Authority,
        ALBOneFactoryPaintStarterPresentationActor*& OutPresentation,
        FString& OutReason)
{
    OutPresentation = nullptr;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("NATIVE PAINT PRESENTATION WORLD IS UNAVAILABLE");
        return false;
    }
    FActorSpawnParameters Parameters;
    Parameters.Name = TEXT("LB_OneFactory_PaintStarter_Presentation_v001");
    Parameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    OutPresentation = World->SpawnActor<
        ALBOneFactoryPaintStarterPresentationActor>(
            ALBOneFactoryPaintStarterPresentationActor::StaticClass(),
            FTransform::Identity, Parameters);
    if (!LBOneFactoryPlayerBuilderPrivate::IsLive(OutPresentation))
    {
        OutReason = TEXT("NATIVE PAINT PRESENTATION ACTOR FAILED TO SPAWN");
        return false;
    }
#if WITH_DEV_AUTOMATION_TESTS
    if (bForcePaintPresentationFailureForTests)
    {
        OutReason = TEXT(
            "FORCED PAINT PRESENTATION FAILURE FOR ATOMIC ROLLBACK TEST");
        return false;
    }
#endif
    if (!OutPresentation->ConfigureFromLayout(
            Authority.CaptureLayout(), OutReason)
        || !ValidatePaintStarterPair(Authority, *OutPresentation, OutReason))
    {
        return false;
    }
    OutReason = TEXT("EXACT NATIVE BLACK-BOX PAINT PRESENTATION MATERIALISED");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::MaterialiseFactoryForRestore(
    const FLBOneFactorySaveState& State, TArray<AActor*>& OutCreatedActors,
    FString& OutReason)
{
    OutCreatedActors.Reset();
    FString Reason;
    if (!ULBOneFactorySaveGame::ValidateState(State, Reason))
    {
        OutReason = FString(TEXT("ONEFACTORY RESTORE MATERIALISATION REJECTED: "))
            + Reason;
        return false;
    }
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    if (!FindSingleBootstrap(Bootstrap, Reason) || !Bootstrap->HasValidShell())
    {
        OutReason = Reason.IsEmpty()
            ? TEXT("ONEFACTORY RESTORE REQUIRES A VALID EMPTY SHELL") : Reason;
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, Reason))
    {
        OutReason = Reason;
        return false;
    }

    TArray<ALBOneFactoryPressStarterLayoutAuthority*> PressAuthorities;
    TArray<ALBOneFactoryPressStarterPresentationActor*> PressPresentations;
    TArray<ALBOneFactoryBodyWeldStarterLayoutAuthority*> BodyAuthorities;
    TArray<ALBOneFactoryBodyWeldStarterPresentationActor*> BodyPresentations;
    TArray<ALBOneFactoryPaintStarterLayoutAuthority*> PaintAuthorities;
    TArray<ALBOneFactoryPaintStarterPresentationActor*> PaintPresentations;
    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*> AssemblyAuthorities;
    TArray<ALBOneFactoryAssemblyStarterPresentationActor*>
        AssemblyPresentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PressAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PressPresentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), BodyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), BodyPresentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintPresentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyPresentations);
    const int32 ExistingActorCount = PressAuthorities.Num()
        + PressPresentations.Num() + BodyAuthorities.Num()
        + BodyPresentations.Num() + PaintAuthorities.Num()
        + PaintPresentations.Num() + AssemblyAuthorities.Num()
        + AssemblyPresentations.Num();
    if (ExistingActorCount != 0)
    {
        OutReason = FString::Printf(TEXT(
            "ONEFACTORY FRESH RESTORE REQUIRES ZERO STARTER ACTORS; FOUND %d"),
            ExistingActorCount);
        return false;
    }

    auto FailAndDestroy = [&](const FString& Failure)
    {
        LBOneFactoryPlayerBuilderPrivate::DestroyCreatedActors(
            OutCreatedActors);
        OutReason = FString(TEXT(
            "ONEFACTORY FRESH RESTORE MATERIALISATION ROLLED BACK: "))
            + Failure;
    };

    ALBOneFactoryPressStarterLayoutAuthority* PressAuthority = nullptr;
    bool bStep = CreateStarterData(PressAuthority, Reason);
    if (LBOneFactoryPlayerBuilderPrivate::IsLive(PressAuthority))
        OutCreatedActors.Add(PressAuthority);
    if (!bStep || !PressAuthority->RestoreLayout(State.PressLayout, Reason))
    {
        FailAndDestroy(Reason);
        return false;
    }
    ALBOneFactoryPressStarterPresentationActor* PressPresentation = nullptr;
    bStep = MaterialiseStarterPresentation(
        *PressAuthority, PressPresentation, Reason);
    if (LBOneFactoryPlayerBuilderPrivate::IsLive(PressPresentation))
        OutCreatedActors.Add(PressPresentation);
    if (!bStep)
    {
        FailAndDestroy(Reason);
        return false;
    }

    ALBOneFactoryBodyWeldStarterLayoutAuthority* BodyAuthority = nullptr;
    bStep = CreateBodyWeldStarterData(BodyAuthority, Reason);
    if (LBOneFactoryPlayerBuilderPrivate::IsLive(BodyAuthority))
        OutCreatedActors.Add(BodyAuthority);
    if (!bStep || !BodyAuthority->RestoreLayout(
            State.BodyWeldLayout, Reason))
    {
        FailAndDestroy(Reason);
        return false;
    }
    ALBOneFactoryBodyWeldStarterPresentationActor* BodyPresentation = nullptr;
    bStep = MaterialiseBodyWeldStarterPresentation(
        *BodyAuthority, BodyPresentation, Reason);
    if (LBOneFactoryPlayerBuilderPrivate::IsLive(BodyPresentation))
        OutCreatedActors.Add(BodyPresentation);
    if (!bStep)
    {
        FailAndDestroy(Reason);
        return false;
    }

    ALBOneFactoryPaintStarterLayoutAuthority* PaintAuthority = nullptr;
    bStep = CreatePaintStarterData(PaintAuthority, Reason);
    if (LBOneFactoryPlayerBuilderPrivate::IsLive(PaintAuthority))
        OutCreatedActors.Add(PaintAuthority);
    if (!bStep || !PaintAuthority->RestoreLayout(State.PaintLayout, Reason))
    {
        FailAndDestroy(Reason);
        return false;
    }
    ALBOneFactoryPaintStarterPresentationActor* PaintPresentation = nullptr;
    bStep = MaterialisePaintStarterPresentation(
        *PaintAuthority, PaintPresentation, Reason);
    if (LBOneFactoryPlayerBuilderPrivate::IsLive(PaintPresentation))
        OutCreatedActors.Add(PaintPresentation);
    if (!bStep)
    {
        FailAndDestroy(Reason);
        return false;
    }

    ALBOneFactoryAssemblyStarterLayoutAuthority* AssemblyAuthority = nullptr;
    bStep = CreateAssemblyStarterData(AssemblyAuthority, Reason);
    if (LBOneFactoryPlayerBuilderPrivate::IsLive(AssemblyAuthority))
        OutCreatedActors.Add(AssemblyAuthority);
    if (!bStep || !AssemblyAuthority->RestoreLayout(
            State.AssemblyLayout, Reason))
    {
        FailAndDestroy(Reason);
        return false;
    }
    ALBOneFactoryAssemblyStarterPresentationActor* AssemblyPresentation =
        nullptr;
    bStep = MaterialiseAssemblyStarterPresentation(
        *AssemblyAuthority, AssemblyPresentation, Reason);
    if (LBOneFactoryPlayerBuilderPrivate::IsLive(AssemblyPresentation))
        OutCreatedActors.Add(AssemblyPresentation);
    if (!bStep)
    {
        FailAndDestroy(Reason);
        return false;
    }

    OutReason = TEXT(
        "ONEFACTORY FRESH RESTORE MATERIALISED FOUR DATA/PRESENTATION PAIRS");
    return true;
}

void ULBOneFactoryPlayerBuilderSubsystem::SetLastResult(
    const bool bSucceeded, const FString& Reason, FString& OutReason)
{
    bLastActionSucceeded = bSucceeded;
    LastActionReason = Reason.IsEmpty()
        ? (bSucceeded ? TEXT("ONEFACTORY ACTION SUCCEEDED")
            : TEXT("ONEFACTORY ACTION FAILED CLOSED"))
        : Reason;
    OutReason = LastActionReason;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CreateNewFactory(FString& OutReason)
{
    FString Reason;
    if (!CanCreateNewFactory(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }

    ALBOneFactoryPressStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* Presentation = nullptr;
    if (!CreateStarterData(Authority, Reason)
        || !MaterialiseStarterPresentation(*Authority, Presentation, Reason))
    {
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(Presentation))
            Presentation->Destroy();
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(Authority)) Authority->Destroy();
        SelectedTargetKind = ELBOneFactoryBuilderTargetKind::None;
        SelectedTargetId = NAME_None;
        bHasSelectedBodyWeldProgramme = false;
        bHasSelectedAssemblyOperation = false;
        SetLastResult(false, FString::Printf(
            TEXT("NEW FACTORY ROLLED BACK DATA AND PRESENTATION ATOMICALLY: %s"),
            *Reason), OutReason);
        return false;
    }

    SelectedTargetKind = ELBOneFactoryBuilderTargetKind::PressStarterStation;
    SelectedTargetId = LBOneFactoryPressStarterIds::PressTrain();
    bHasSelectedBodyWeldProgramme = false;
    bHasSelectedAssemblyOperation = false;
    SetLastResult(true, TEXT(
        "NEW FACTORY CREATED: CANONICAL PRESS DATA + 268 NATIVE PRIMITIVES; AWAITING COMMISSION"),
        OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CreateBodyWeldStarter(
    FString& OutReason)
{
    FString Reason;
    if (!CanCreateBodyWeldStarter(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }

    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* Presentation = nullptr;
    if (!CreateBodyWeldStarterData(Authority, Reason)
        || !MaterialiseBodyWeldStarterPresentation(
            *Authority, Presentation, Reason))
    {
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(Presentation))
            Presentation->Destroy();
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(Authority))
            Authority->Destroy();
        SelectedTargetKind = ELBOneFactoryBuilderTargetKind::None;
        SelectedTargetId = NAME_None;
        bHasSelectedBodyWeldProgramme = false;
        bHasSelectedAssemblyOperation = false;
        SetLastResult(false, FString::Printf(TEXT(
            "BODY/WELD STARTER ROLLED BACK DATA AND PRESENTATION ATOMICALLY: %s"),
            *Reason), OutReason);
        return false;
    }

    SelectedTargetKind =
        ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition;
    SelectedTargetId = LBOneFactoryBodyWeldStarterIds::Station(2);
    SelectedBodyWeldProgramme =
        ELBOneFactoryBodyWeldProgramme::FrontUnderbodyGeometry;
    bHasSelectedBodyWeldProgramme = true;
    bHasSelectedAssemblyOperation = false;
    SetLastResult(true, TEXT(
        "BODY/WELD STARTER CREATED: 18 CONFIGURABLE POSITIONS + 36 LARGE ROBOTS + 489 NATIVE INSTANCES; AWAITING COMMISSION"),
        OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CreateAssemblyStarter(
    FString& OutReason)
{
    FString Reason;
    if (!CanCreateAssemblyStarter(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }

    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryAssemblyStarterPresentationActor* Presentation = nullptr;
    if (!CreateAssemblyStarterData(Authority, Reason)
        || !MaterialiseAssemblyStarterPresentation(
            *Authority, Presentation, Reason))
    {
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(Presentation))
            Presentation->Destroy();
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(Authority))
            Authority->Destroy();
        SelectedTargetKind = ELBOneFactoryBuilderTargetKind::None;
        SelectedTargetId = NAME_None;
        bHasSelectedBodyWeldProgramme = false;
        bHasSelectedAssemblyOperation = false;
        SetLastResult(false, FString::Printf(TEXT(
            "ASSEMBLY STARTER ROLLED BACK DATA AND PRESENTATION ATOMICALLY: %s"),
            *Reason), OutReason);
        return false;
    }

    SelectedTargetKind =
        ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition;
    SelectedTargetId = LBOneFactoryAssemblyStarterIds::Station(12);
    SelectedAssemblyOperation =
        ELBOneFactoryAssemblyOperation::PowertrainMarriage;
    bHasSelectedAssemblyOperation = true;
    bHasSelectedBodyWeldProgramme = false;
    SetLastResult(true, TEXT(
        "ASSEMBLY STARTER CREATED: 24 CONFIGURABLE POSITIONS + 95 NATIVE INSTANCES; AWAITING COMMISSION"),
        OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CreatePaintStarter(
    FString& OutReason)
{
    FString Reason;
    if (!CanCreatePaintStarter(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }

    ALBOneFactoryPaintStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryPaintStarterPresentationActor* Presentation = nullptr;
    if (!CreatePaintStarterData(Authority, Reason)
        || !MaterialisePaintStarterPresentation(
            *Authority, Presentation, Reason))
    {
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(Presentation))
            Presentation->Destroy();
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(Authority))
            Authority->Destroy();
        SelectedTargetKind = ELBOneFactoryBuilderTargetKind::None;
        SelectedTargetId = NAME_None;
        bHasSelectedBodyWeldProgramme = false;
        bHasSelectedAssemblyOperation = false;
        SetLastResult(false, FString::Printf(TEXT(
            "PAINT STARTER ROLLED BACK DATA AND PRESENTATION ATOMICALLY: %s"),
            *Reason), OutReason);
        return false;
    }

    SelectedTargetKind = ELBOneFactoryBuilderTargetKind::PaintStarterStation;
    SelectedTargetId = LBOneFactoryPaintStarterIds::Station(
        ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth);
    bHasSelectedAssemblyOperation = false;
    bHasSelectedBodyWeldProgramme = false;
    SetLastResult(true, TEXT(
        "PAINT STARTER CREATED: 8 BLACK-BOX RESPONSIBILITIES + 32 NATIVE INSTANCES; AWAITING COMMISSION"),
        OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanCommissionPressStarter(
    FString& OutReason) const
{
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    if (!FindSingleBootstrap(Bootstrap, OutReason)
        || !Bootstrap->HasValidShell())
    {
        if (OutReason.IsEmpty()) OutReason = TEXT("ONEFACTORY BOOTSTRAP IS NOT READY");
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, OutReason)) return false;
    ALBOneFactoryPressStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* Presentation = nullptr;
    if (!FindStarterPair(Authority, Presentation, OutReason)) return false;
    if (Authority->IsCommissioned())
    {
        OutReason = TEXT("PRESS STARTER IS ALREADY COMMISSIONED");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            Authority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED PRESS WIP BEFORE COMMISSIONING");
        return false;
    }
    if (!ValidateStarterPair(*Authority, *Presentation, OutReason)) return false;
    OutReason = TEXT("PRESS DATA, PRESENTATION AND NATIVE-ONLY PROVENANCE ARE READY TO COMMISSION");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanCommissionBodyWeldStarter(
    FString& OutReason) const
{
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    if (!FindSingleBootstrap(Bootstrap, OutReason)
        || !Bootstrap->HasValidShell())
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT("ONEFACTORY BOOTSTRAP IS NOT READY");
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, OutReason)) return false;
    ALBOneFactoryPressStarterLayoutAuthority* PressAuthority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* PressPresentation = nullptr;
    if (!FindStarterPair(PressAuthority, PressPresentation, OutReason)
        || !ValidateStarterPair(
            *PressAuthority, *PressPresentation, OutReason))
    {
        return false;
    }
    if (!PressAuthority->IsCommissioned())
    {
        OutReason = TEXT(
            "BODY/WELD COMMISSION REQUIRES A COMMISSIONED PRESS STARTER");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            PressAuthority->CaptureLayout()))
    {
        OutReason = TEXT(
            "BODY/WELD COMMISSION IS BLOCKED BY ACTIVE OR RESERVED PRESS WIP");
        return false;
    }
    TArray<ALBOneFactoryPaintStarterLayoutAuthority*> PaintAuthorities;
    TArray<ALBOneFactoryPaintStarterPresentationActor*> PaintPresentations;
    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*> AssemblyAuthorities;
    TArray<ALBOneFactoryAssemblyStarterPresentationActor*>
        AssemblyPresentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintPresentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyPresentations);
    if (!PaintAuthorities.IsEmpty() || !PaintPresentations.IsEmpty()
        || !AssemblyAuthorities.IsEmpty()
        || !AssemblyPresentations.IsEmpty())
    {
        OutReason = TEXT(
            "BODY/WELD COMMISSION IS BLOCKED BY OUT-OF-ORDER DOWNSTREAM STARTERS");
        return false;
    }
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* Presentation = nullptr;
    if (!FindBodyWeldStarterPair(Authority, Presentation, OutReason))
        return false;
    if (Authority->IsCommissioned())
    {
        OutReason = TEXT("BODY/WELD STARTER IS ALREADY COMMISSIONED");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            Authority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED BODY/WELD WIP BEFORE COMMISSIONING");
        return false;
    }
    if (!ValidateBodyWeldStarterPair(
            *Authority, *Presentation, OutReason))
    {
        return false;
    }
    OutReason = TEXT(
        "BODY/WELD DATA, 24-BATCH PRESENTATION AND NATIVE-ONLY PROVENANCE ARE READY TO COMMISSION");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanRemoveBodyWeldStarter(
    FString& OutReason) const
{
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, OutReason)) return false;
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* Presentation = nullptr;
    if (!FindBodyWeldStarterPair(Authority, Presentation, OutReason)
        || !ValidateBodyWeldStarterPair(
            *Authority, *Presentation, OutReason))
    {
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            Authority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED BODY/WELD WIP BEFORE REMOVING THE STARTER PAIR");
        return false;
    }
    TArray<ALBOneFactoryPaintStarterLayoutAuthority*> PaintAuthorities;
    TArray<ALBOneFactoryPaintStarterPresentationActor*> PaintPresentations;
    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*> AssemblyAuthorities;
    TArray<ALBOneFactoryAssemblyStarterPresentationActor*>
        AssemblyPresentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintPresentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyPresentations);
    if (!PaintAuthorities.IsEmpty() || !PaintPresentations.IsEmpty()
        || !AssemblyAuthorities.IsEmpty()
        || !AssemblyPresentations.IsEmpty())
    {
        OutReason = TEXT(
            "REMOVE DOWNSTREAM PAINT AND ASSEMBLY STARTERS BEFORE REMOVING BODY/WELD");
        return false;
    }
    OutReason = TEXT(
        "REMOVE THE COMPLETE IDLE BODY/WELD DATA AND PRESENTATION PAIR ATOMICALLY");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanCommissionAssemblyStarter(
    FString& OutReason) const
{
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    if (!FindSingleBootstrap(Bootstrap, OutReason)
        || !Bootstrap->HasValidShell())
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT("ONEFACTORY BOOTSTRAP IS NOT READY");
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, OutReason)) return false;
    ALBOneFactoryPressStarterLayoutAuthority* PressAuthority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* PressPresentation = nullptr;
    ALBOneFactoryBodyWeldStarterLayoutAuthority* BodyAuthority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* BodyPresentation = nullptr;
    ALBOneFactoryPaintStarterLayoutAuthority* PaintAuthority = nullptr;
    ALBOneFactoryPaintStarterPresentationActor* PaintPresentation = nullptr;
    if (!FindStarterPair(PressAuthority, PressPresentation, OutReason)
        || !ValidateStarterPair(
            *PressAuthority, *PressPresentation, OutReason)
        || !FindBodyWeldStarterPair(
            BodyAuthority, BodyPresentation, OutReason)
        || !ValidateBodyWeldStarterPair(
            *BodyAuthority, *BodyPresentation, OutReason)
        || !FindPaintStarterPair(
            PaintAuthority, PaintPresentation, OutReason)
        || !ValidatePaintStarterPair(
            *PaintAuthority, *PaintPresentation, OutReason))
    {
        return false;
    }
    if (!PressAuthority->IsCommissioned()
        || !BodyAuthority->IsCommissioned()
        || !PaintAuthority->IsCommissioned())
    {
        OutReason = TEXT(
            "ASSEMBLY COMMISSION REQUIRES COMMISSIONED PRESS, BODY/WELD AND PAINT STARTERS");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            PressAuthority->CaptureLayout())
        || LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            BodyAuthority->CaptureLayout())
        || LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            PaintAuthority->CaptureLayout()))
    {
        OutReason = TEXT(
            "ASSEMBLY COMMISSION IS BLOCKED BY ACTIVE OR RESERVED UPSTREAM WIP");
        return false;
    }
    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryAssemblyStarterPresentationActor* Presentation = nullptr;
    if (!FindAssemblyStarterPair(Authority, Presentation, OutReason))
        return false;
    if (Authority->IsCommissioned())
    {
        OutReason = TEXT("ASSEMBLY STARTER IS ALREADY COMMISSIONED");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            Authority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED ASSEMBLY WIP BEFORE COMMISSIONING");
        return false;
    }
    if (!ValidateAssemblyStarterPair(*Authority, *Presentation, OutReason))
        return false;
    OutReason = TEXT(
        "ASSEMBLY DATA, PRESENTATION AND NATIVE-ONLY PROVENANCE ARE READY TO COMMISSION");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanCommissionPaintStarter(
    FString& OutReason) const
{
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    if (!FindSingleBootstrap(Bootstrap, OutReason)
        || !Bootstrap->HasValidShell())
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT("ONEFACTORY BOOTSTRAP IS NOT READY");
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, OutReason)) return false;
    ALBOneFactoryPressStarterLayoutAuthority* PressAuthority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* PressPresentation = nullptr;
    if (!FindStarterPair(PressAuthority, PressPresentation, OutReason)
        || !ValidateStarterPair(
            *PressAuthority, *PressPresentation, OutReason))
    {
        return false;
    }
    if (!PressAuthority->IsCommissioned())
    {
        OutReason = TEXT(
            "PAINT COMMISSION REQUIRES A COMMISSIONED PRESS STARTER");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            PressAuthority->CaptureLayout()))
    {
        OutReason = TEXT(
            "PAINT COMMISSION IS BLOCKED BY ACTIVE OR RESERVED PRESS WIP");
        return false;
    }
    ALBOneFactoryBodyWeldStarterLayoutAuthority* BodyAuthority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* BodyPresentation = nullptr;
    if (!FindBodyWeldStarterPair(
            BodyAuthority, BodyPresentation, OutReason)
        || !ValidateBodyWeldStarterPair(
            *BodyAuthority, *BodyPresentation, OutReason))
    {
        return false;
    }
    if (!BodyAuthority->IsCommissioned())
    {
        OutReason = TEXT(
            "PAINT COMMISSION REQUIRES COMMISSIONED BODY/WELD");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            BodyAuthority->CaptureLayout()))
    {
        OutReason = TEXT(
            "PAINT COMMISSION IS BLOCKED BY ACTIVE OR RESERVED BODY/WELD WIP");
        return false;
    }
    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*> AssemblyAuthorities;
    TArray<ALBOneFactoryAssemblyStarterPresentationActor*>
        AssemblyPresentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyPresentations);
    if (!AssemblyAuthorities.IsEmpty() || !AssemblyPresentations.IsEmpty())
    {
        OutReason = TEXT(
            "PAINT COMMISSION IS BLOCKED BY OUT-OF-ORDER ASSEMBLY STARTER ACTORS");
        return false;
    }
    ALBOneFactoryPaintStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryPaintStarterPresentationActor* Presentation = nullptr;
    if (!FindPaintStarterPair(Authority, Presentation, OutReason))
        return false;
    if (Authority->IsCommissioned())
    {
        OutReason = TEXT("PAINT STARTER IS ALREADY COMMISSIONED");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
            Authority->CaptureLayout()))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED PAINT WIP BEFORE COMMISSIONING");
        return false;
    }
    if (!ValidatePaintStarterPair(*Authority, *Presentation, OutReason))
        return false;
    OutReason = TEXT(
        "PAINT DATA, BLACK-BOX PRESENTATION AND NATIVE-ONLY PROVENANCE ARE READY TO COMMISSION");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::SynchronisePresentationOrRestore(
    ALBOneFactoryPressStarterLayoutAuthority& Authority,
    ALBOneFactoryPressStarterPresentationActor& Presentation,
    const FLBOneFactoryPressStarterLayoutState& Before,
    const TCHAR* Operation, FString& OutReason) const
{
    FString FailureReason;
    if (Presentation.ConfigureFromLayout(Authority.CaptureLayout(), FailureReason)
        && ValidateStarterPair(Authority, Presentation, FailureReason))
    {
        OutReason = FString::Printf(TEXT("%s COMMITTED TO DATA AND PRESENTATION"),
            Operation);
        return true;
    }

    FString DataRestoreReason;
    const bool bDataRestored = Authority.RestoreLayout(Before, DataRestoreReason);
    FString PresentationRestoreReason;
    const bool bPresentationRestored = bDataRestored
        && Presentation.ConfigureFromLayout(Before, PresentationRestoreReason)
        && ValidateStarterPair(Authority, Presentation, PresentationRestoreReason);
    OutReason = FString::Printf(TEXT(
        "%s ROLLED BACK: %s | DATA RESTORE: %s | PRESENTATION RESTORE: %s"),
        Operation, *FailureReason, bDataRestored ? TEXT("PASS") : *DataRestoreReason,
        bPresentationRestored ? TEXT("PASS") : *PresentationRestoreReason);
    return false;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    SynchroniseBodyWeldPresentationOrRestore(
        ALBOneFactoryBodyWeldStarterLayoutAuthority& Authority,
        ALBOneFactoryBodyWeldStarterPresentationActor& Presentation,
        const FLBOneFactoryBodyWeldLayoutState& Before,
        const TCHAR* Operation, FString& OutReason) const
{
    FString FailureReason;
    bool bForceFailure = false;
#if WITH_DEV_AUTOMATION_TESTS
    bForceFailure = bForceBodyWeldPresentationFailureForTests;
#endif
    if (!bForceFailure
        && Presentation.ConfigureFromLayout(
            Authority.CaptureLayout(), FailureReason)
        && ValidateBodyWeldStarterPair(
            Authority, Presentation, FailureReason))
    {
        OutReason = FString::Printf(TEXT(
            "%s COMMITTED TO BODY/WELD DATA AND PRESENTATION"), Operation);
        return true;
    }
    if (bForceFailure)
    {
        FailureReason = TEXT(
            "FORCED BODY/WELD PRESENTATION SYNCHRONISATION FAILURE FOR ROLLBACK TEST");
    }

    FString DataRestoreReason;
    const bool bDataRestored = Authority.RestoreLayout(
        Before, DataRestoreReason);
    FString PresentationRestoreReason;
    const bool bPresentationRestored = bDataRestored
        && Presentation.ConfigureFromLayout(Before, PresentationRestoreReason)
        && ValidateBodyWeldStarterPair(
            Authority, Presentation, PresentationRestoreReason);
    OutReason = FString::Printf(TEXT(
        "%s ROLLED BACK: %s | DATA RESTORE: %s | PRESENTATION RESTORE: %s"),
        Operation, *FailureReason,
        bDataRestored ? TEXT("PASS") : *DataRestoreReason,
        bPresentationRestored ? TEXT("PASS") : *PresentationRestoreReason);
    return false;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    SynchroniseAssemblyPresentationOrRestore(
        ALBOneFactoryAssemblyStarterLayoutAuthority& Authority,
        ALBOneFactoryAssemblyStarterPresentationActor& Presentation,
        const FLBOneFactoryAssemblyLayoutState& Before,
        const TCHAR* Operation, FString& OutReason) const
{
    FString FailureReason;
    bool bForceFailure = false;
#if WITH_DEV_AUTOMATION_TESTS
    bForceFailure = bForceAssemblyPresentationFailureForTests;
#endif
    if (!bForceFailure
        && Presentation.ConfigureFromLayout(
            Authority.CaptureLayout(), FailureReason)
        && ValidateAssemblyStarterPair(
            Authority, Presentation, FailureReason))
    {
        OutReason = FString::Printf(
            TEXT("%s COMMITTED TO ASSEMBLY DATA AND PRESENTATION"), Operation);
        return true;
    }
    if (bForceFailure)
    {
        FailureReason = TEXT(
            "FORCED ASSEMBLY PRESENTATION SYNCHRONISATION FAILURE FOR ROLLBACK TEST");
    }

    FString DataRestoreReason;
    const bool bDataRestored = Authority.RestoreLayout(
        Before, DataRestoreReason);
    FString PresentationRestoreReason;
    const bool bPresentationRestored = bDataRestored
        && Presentation.ConfigureFromLayout(Before, PresentationRestoreReason)
        && ValidateAssemblyStarterPair(
            Authority, Presentation, PresentationRestoreReason);
    OutReason = FString::Printf(TEXT(
        "%s ROLLED BACK: %s | DATA RESTORE: %s | PRESENTATION RESTORE: %s"),
        Operation, *FailureReason,
        bDataRestored ? TEXT("PASS") : *DataRestoreReason,
        bPresentationRestored ? TEXT("PASS") : *PresentationRestoreReason);
    return false;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    SynchronisePaintPresentationOrRestore(
        ALBOneFactoryPaintStarterLayoutAuthority& Authority,
        ALBOneFactoryPaintStarterPresentationActor& Presentation,
        const FLBOneFactoryPaintStarterLayoutState& Before,
        const TCHAR* Operation, FString& OutReason) const
{
    FString FailureReason;
    bool bForceFailure = false;
#if WITH_DEV_AUTOMATION_TESTS
    bForceFailure = bForcePaintPresentationFailureForTests;
#endif
    if (!bForceFailure
        && Presentation.ConfigureFromLayout(
            Authority.CaptureLayout(), FailureReason)
        && ValidatePaintStarterPair(Authority, Presentation, FailureReason))
    {
        OutReason = FString::Printf(
            TEXT("%s COMMITTED TO PAINT DATA AND PRESENTATION"), Operation);
        return true;
    }
    if (bForceFailure)
    {
        FailureReason = TEXT(
            "FORCED PAINT PRESENTATION SYNCHRONISATION FAILURE FOR ROLLBACK TEST");
    }

    FString DataRestoreReason;
    const bool bDataRestored = Authority.RestoreLayout(
        Before, DataRestoreReason);
    FString PresentationRestoreReason;
    const bool bPresentationRestored = bDataRestored
        && Presentation.ConfigureFromLayout(Before, PresentationRestoreReason)
        && ValidatePaintStarterPair(
            Authority, Presentation, PresentationRestoreReason);
    OutReason = FString::Printf(TEXT(
        "%s ROLLED BACK: %s | DATA RESTORE: %s | PRESENTATION RESTORE: %s"),
        Operation, *FailureReason,
        bDataRestored ? TEXT("PASS") : *DataRestoreReason,
        bPresentationRestored ? TEXT("PASS") : *PresentationRestoreReason);
    return false;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CommissionPressStarter(
    FString& OutReason)
{
    FString Reason;
    if (!CanCommissionPressStarter(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryPressStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* Presentation = nullptr;
    if (!FindStarterPair(Authority, Presentation, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryPressStarterLayoutState Before = Authority->CaptureLayout();
    const FLBOneFactoryProductionLedgerState LedgerBefore =
        Production->CaptureLedger();
    if (!Authority->Commission(Reason)
        || !SynchronisePresentationOrRestore(*Authority, *Presentation,
            Before, TEXT("PRESS COMMISSION"), Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    if (!Production->SetDepartmentCommissioned(
            ELBOneFactoryDepartment::Press, true, Reason))
    {
        const FString Failure = Reason;
        FString RollbackDetail;
        LBOneFactoryPlayerBuilderPrivate::RestoreCommissionTransaction(
            *Authority, *Presentation, *Production, Before, LedgerBefore,
            RollbackDetail);
        SetLastResult(false, FString::Printf(TEXT(
            "PRESS COMMISSION LEDGER SYNC FAILED [%s]; %s"),
            *Failure, *RollbackDetail), OutReason);
        return false;
    }
    SetLastResult(true,
        TEXT("PRESS STARTER COMMISSIONED WITH COHERENT PRESENTATION AND PRODUCTION LEDGER"),
        OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CommissionBodyWeldStarter(
    FString& OutReason)
{
    FString Reason;
    if (!CanCommissionBodyWeldStarter(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* Presentation = nullptr;
    if (!FindBodyWeldStarterPair(Authority, Presentation, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryBodyWeldLayoutState Before =
        Authority->CaptureLayout();
    const FLBOneFactoryProductionLedgerState LedgerBefore =
        Production->CaptureLedger();
    if (!Authority->Commission(Reason)
        || !SynchroniseBodyWeldPresentationOrRestore(
            *Authority, *Presentation, Before,
            TEXT("BODY/WELD COMMISSION"), Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    if (!Production->SetDepartmentCommissioned(
            ELBOneFactoryDepartment::Body, true, Reason))
    {
        const FString Failure = Reason;
        FString RollbackDetail;
        LBOneFactoryPlayerBuilderPrivate::RestoreCommissionTransaction(
            *Authority, *Presentation, *Production, Before, LedgerBefore,
            RollbackDetail);
        SetLastResult(false, FString::Printf(TEXT(
            "BODY/WELD COMMISSION LEDGER SYNC FAILED [%s]; %s"),
            *Failure, *RollbackDetail), OutReason);
        return false;
    }
    SetLastResult(true, TEXT(
        "BODY/WELD STARTER COMMISSIONED WITH COHERENT PRESENTATION AND PRODUCTION LEDGER"),
        OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::RemoveBodyWeldStarter(
    FString& OutReason)
{
    FString Reason;
    if (!CanRemoveBodyWeldStarter(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* Presentation = nullptr;
    if (!FindBodyWeldStarterPair(Authority, Presentation, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryProductionLedgerState LedgerBefore =
        Production->CaptureLedger();
    if (!Production->SetDepartmentCommissioned(
            ELBOneFactoryDepartment::Body, false, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const bool bPresentationDestroyed = Presentation->Destroy();
    const bool bAuthorityDestroyed = Authority->Destroy();
    const bool bPairDestroyed =
        bPresentationDestroyed && bAuthorityDestroyed;
    if (bPairDestroyed)
    {
        if (SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition)
        {
            SelectedTargetKind = ELBOneFactoryBuilderTargetKind::None;
            SelectedTargetId = NAME_None;
        }
        bHasSelectedBodyWeldProgramme = false;
        Reason = TEXT(
            "REMOVED COMPLETE BODY/WELD DATA + PRESENTATION PAIR ATOMICALLY");
    }
    else
    {
        FString LedgerRestoreReason;
        Production->RestoreLedger(LedgerBefore, LedgerRestoreReason);
        Reason = FString::Printf(TEXT(
            "BODY/WELD PAIR DESTROY FAILED CLOSED (DATA %s / PRESENTATION %s / LEDGER %s)"),
            bAuthorityDestroyed ? TEXT("DESTROYED") : TEXT("LIVE"),
            bPresentationDestroyed ? TEXT("DESTROYED") : TEXT("LIVE"),
            *LedgerRestoreReason);
    }
    SetLastResult(bPairDestroyed, Reason, OutReason);
    return bPairDestroyed;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CommissionAssemblyStarter(
    FString& OutReason)
{
    FString Reason;
    if (!CanCommissionAssemblyStarter(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryAssemblyStarterPresentationActor* Presentation = nullptr;
    if (!FindAssemblyStarterPair(Authority, Presentation, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryAssemblyLayoutState Before = Authority->CaptureLayout();
    const FLBOneFactoryProductionLedgerState LedgerBefore =
        Production->CaptureLedger();
    if (!Authority->Commission(Reason)
        || !SynchroniseAssemblyPresentationOrRestore(
            *Authority, *Presentation, Before, TEXT("ASSEMBLY COMMISSION"),
            Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    if (!Production->SetDepartmentCommissioned(
            ELBOneFactoryDepartment::Assembly, true, Reason)
        || !Production->SeedStarterContracts(Reason)
        || !Coordinator->ValidateRuntimeFactory(Reason))
    {
        const FString Failure = Reason;
        FString RollbackDetail;
        LBOneFactoryPlayerBuilderPrivate::RestoreCommissionTransaction(
            *Authority, *Presentation, *Production, Before, LedgerBefore,
            RollbackDetail);
        SetLastResult(false, FString::Printf(TEXT(
            "ASSEMBLY COMMISSION 57-STATION RUNTIME VALIDATION FAILED [%s]; %s"),
            *Failure, *RollbackDetail), OutReason);
        return false;
    }
    SetLastResult(true, TEXT(
        "ASSEMBLY STARTER COMMISSIONED; STARTER CONTRACTS SEEDED AND THE CONFIGURED 57-STATION ROUTE IS VALID"),
        OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CommissionPaintStarter(
    FString& OutReason)
{
    FString Reason;
    if (!CanCommissionPaintStarter(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryPaintStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryPaintStarterPresentationActor* Presentation = nullptr;
    if (!FindPaintStarterPair(Authority, Presentation, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(Production, Coordinator, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryPaintStarterLayoutState Before =
        Authority->CaptureLayout();
    const FLBOneFactoryProductionLedgerState LedgerBefore =
        Production->CaptureLedger();
    if (!Authority->Commission(Reason)
        || !SynchronisePaintPresentationOrRestore(
            *Authority, *Presentation, Before, TEXT("PAINT COMMISSION"),
            Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    if (!Production->SetDepartmentCommissioned(
            ELBOneFactoryDepartment::Paint, true, Reason))
    {
        const FString Failure = Reason;
        FString RollbackDetail;
        LBOneFactoryPlayerBuilderPrivate::RestoreCommissionTransaction(
            *Authority, *Presentation, *Production, Before, LedgerBefore,
            RollbackDetail);
        SetLastResult(false, FString::Printf(TEXT(
            "PAINT COMMISSION LEDGER SYNC FAILED [%s]; %s"),
            *Failure, *RollbackDetail), OutReason);
        return false;
    }
    SetLastResult(true, TEXT(
        "PAINT STARTER COMMISSIONED WITH COHERENT PRESENTATION AND PRODUCTION LEDGER"),
        OutReason);
    return true;
}

void ULBOneFactoryPlayerBuilderSubsystem::CollectSelectableTargets(
    TArray<FSelectableTarget>& OutTargets) const
{
    OutTargets.Reset();
    TArray<ALBOneFactoryPressStarterLayoutAuthority*> Authorities;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Authorities);
    if (Authorities.Num() == 1
        && Authorities[0]->GetClass()
            == ALBOneFactoryPressStarterLayoutAuthority::StaticClass())
    {
        const FLBOneFactoryPressStarterLayoutState State =
            Authorities[0]->CaptureLayout();
        for (const FLBOneFactoryPressStarterStationState& Station : State.Stations)
        {
            OutTargets.Add(FSelectableTarget{
                ELBOneFactoryBuilderTargetKind::PressStarterStation,
                Station.StationId,
                LBOneFactoryPlayerBuilderPrivate::RoleLabel(Station.Role)});
        }
    }

    TArray<ALBOneFactoryBodyWeldStarterLayoutAuthority*> BodyAuthorities;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), BodyAuthorities);
    if (BodyAuthorities.Num() == 1
        && BodyAuthorities[0]->GetClass()
            == ALBOneFactoryBodyWeldStarterLayoutAuthority::StaticClass())
    {
        const FLBOneFactoryBodyWeldLayoutState State =
            BodyAuthorities[0]->CaptureLayout();
        TArray<FLBOneFactoryBodyWeldStationState> Stations = State.Stations;
        Stations.Sort([](
            const FLBOneFactoryBodyWeldStationState& Left,
            const FLBOneFactoryBodyWeldStationState& Right)
        {
            return Left.LinePosition < Right.LinePosition;
        });
        for (const FLBOneFactoryBodyWeldStationState& Station : Stations)
        {
            OutTargets.Add(FSelectableTarget{
                ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition,
                Station.StationId,
                LBOneFactoryPlayerBuilderPrivate::BodyWeldPositionLabel(
                    Station)});
        }
    }

    TArray<ALBOneFactoryPaintStarterLayoutAuthority*> PaintAuthorities;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintAuthorities);
    if (PaintAuthorities.Num() == 1
        && PaintAuthorities[0]->GetClass()
            == ALBOneFactoryPaintStarterLayoutAuthority::StaticClass())
    {
        const FLBOneFactoryPaintStarterLayoutState State =
            PaintAuthorities[0]->CaptureLayout();
        for (const FLBOneFactoryPaintStarterStationState& Station :
            State.Stations)
        {
            OutTargets.Add(FSelectableTarget{
                ELBOneFactoryBuilderTargetKind::PaintStarterStation,
                Station.StationId,
                FString::Printf(TEXT("Paint: %s"),
                    *LBOneFactoryPlayerBuilderPrivate::PaintRoleLabel(
                        Station.Role))});
        }
    }

    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*> AssemblyAuthorities;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyAuthorities);
    if (AssemblyAuthorities.Num() == 1
        && AssemblyAuthorities[0]->GetClass()
            == ALBOneFactoryAssemblyStarterLayoutAuthority::StaticClass())
    {
        const FLBOneFactoryAssemblyLayoutState State =
            AssemblyAuthorities[0]->CaptureLayout();
        TArray<FLBOneFactoryAssemblyStationState> Stations = State.Stations;
        Stations.Sort([](const FLBOneFactoryAssemblyStationState& Left,
            const FLBOneFactoryAssemblyStationState& Right)
        {
            return Left.LinePosition < Right.LinePosition;
        });
        for (const FLBOneFactoryAssemblyStationState& Station : Stations)
        {
            OutTargets.Add(FSelectableTarget{
                ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition,
                Station.StationId,
                LBOneFactoryPlayerBuilderPrivate::AssemblyPositionLabel(
                    Station)});
        }
    }

    TArray<ALBFactoryBuildMachine*> Machines;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Machines);
    Machines.RemoveAll([](const ALBFactoryBuildMachine* Machine)
    {
        return !Machine || Machine->GetMachineId().IsNone();
    });
    Machines.Sort([](const ALBFactoryBuildMachine& A,
        const ALBFactoryBuildMachine& B)
    {
        return A.GetMachineId().LexicalLess(B.GetMachineId());
    });
    for (const ALBFactoryBuildMachine* Machine : Machines)
    {
        OutTargets.Add(FSelectableTarget{
            ELBOneFactoryBuilderTargetKind::PlayerBuildMachine,
            Machine->GetMachineId(),
            LBOneFactoryPlayerBuilderPrivate::MachineLabel(*Machine)});
    }
}

bool ULBOneFactoryPlayerBuilderSubsystem::SelectNextTarget(FString& OutReason)
{
    TArray<FSelectableTarget> Targets;
    CollectSelectableTargets(Targets);
    if (Targets.IsEmpty())
    {
        SelectedTargetKind = ELBOneFactoryBuilderTargetKind::None;
        SelectedTargetId = NAME_None;
        SetLastResult(false, TEXT("NO PRESS STATION EXISTS; CREATE NEW FACTORY FIRST"),
            OutReason);
        return false;
    }
    int32 CurrentIndex = Targets.IndexOfByPredicate([this](
        const FSelectableTarget& Target)
    {
        return Target.Kind == SelectedTargetKind && Target.Id == SelectedTargetId;
    });
    CurrentIndex = (CurrentIndex + 1) % Targets.Num();
    SelectedTargetKind = Targets[CurrentIndex].Kind;
    SelectedTargetId = Targets[CurrentIndex].Id;
    bHasSelectedAssemblyOperation = false;
    bHasSelectedBodyWeldProgramme = false;
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition)
    {
        ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        FString ResolveReason;
        if (ResolveSelectedBodyWeld(
                Authority, StationIndex, ResolveReason))
        {
            const FLBOneFactoryBodyWeldLayoutState State =
                Authority->CaptureLayout();
            const FLBOneFactoryBodyWeldStationState& Station =
                State.Stations[StationIndex];
            if (!Station.AssignedProgrammes.IsEmpty())
            {
                SelectedBodyWeldProgramme = Station.AssignedProgrammes[0];
                bHasSelectedBodyWeldProgramme = true;
            }
            else
            {
                for (int32 Value = 0;
                    Value < ULBOneFactoryBodyWeldStarterLayoutLibrary::
                        RequiredProgrammeCount; ++Value)
                {
                    const ELBOneFactoryBodyWeldProgramme Candidate =
                        static_cast<ELBOneFactoryBodyWeldProgramme>(Value);
                    if (ULBOneFactoryBodyWeldStarterLayoutLibrary::
                            StationSupportsProgramme(Station, Candidate))
                    {
                        SelectedBodyWeldProgramme = Candidate;
                        bHasSelectedBodyWeldProgramme = true;
                        break;
                    }
                }
            }
        }
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition)
    {
        ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        FString ResolveReason;
        if (ResolveSelectedAssembly(
                Authority, StationIndex, ResolveReason))
        {
            const FLBOneFactoryAssemblyLayoutState State =
                Authority->CaptureLayout();
            const FLBOneFactoryAssemblyStationState& Station =
                State.Stations[StationIndex];
            if (!Station.AssignedOperations.IsEmpty())
            {
                SelectedAssemblyOperation = Station.AssignedOperations[0];
                bHasSelectedAssemblyOperation = true;
            }
            else
            {
                for (int32 Value = 0;
                    Value < ULBOneFactoryAssemblyStarterLayoutLibrary::
                        RequiredOperationCount; ++Value)
                {
                    const ELBOneFactoryAssemblyOperation Candidate =
                        static_cast<ELBOneFactoryAssemblyOperation>(Value);
                    if (ULBOneFactoryAssemblyStarterLayoutLibrary::
                            StationSupportsOperation(Station, Candidate))
                    {
                        SelectedAssemblyOperation = Candidate;
                        bHasSelectedAssemblyOperation = true;
                        break;
                    }
                }
            }
        }
    }
    SetLastResult(true, FString::Printf(TEXT("SELECTED %s"),
        *Targets[CurrentIndex].Label), OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ResolveSelectedStarter(
    ALBOneFactoryPressStarterLayoutAuthority*& OutAuthority,
    int32& OutStationIndex, FString& OutReason) const
{
    OutAuthority = nullptr;
    OutStationIndex = INDEX_NONE;
    if (SelectedTargetKind
        != ELBOneFactoryBuilderTargetKind::PressStarterStation
        || SelectedTargetId.IsNone())
    {
        OutReason = TEXT("SELECT A CANONICAL PRESS STARTER STATION FIRST");
        return false;
    }
    ALBOneFactoryPressStarterPresentationActor* Presentation = nullptr;
    if (!FindStarterPair(OutAuthority, Presentation, OutReason)) return false;
    const FLBOneFactoryPressStarterLayoutState State = OutAuthority->CaptureLayout();
    OutStationIndex = State.Stations.IndexOfByPredicate([this](
        const FLBOneFactoryPressStarterStationState& Station)
    {
        return Station.StationId == SelectedTargetId;
    });
    if (!State.Stations.IsValidIndex(OutStationIndex))
    {
        OutReason = TEXT("SELECTED PRESS STARTER STATION NO LONGER EXISTS");
        return false;
    }
    if (!ValidateStarterPair(*OutAuthority, *Presentation, OutReason)) return false;
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ResolveSelectedAssembly(
    ALBOneFactoryAssemblyStarterLayoutAuthority*& OutAuthority,
    int32& OutStationIndex, FString& OutReason) const
{
    OutAuthority = nullptr;
    OutStationIndex = INDEX_NONE;
    if (SelectedTargetKind
            != ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition
        || SelectedTargetId.IsNone())
    {
        OutReason = TEXT(
            "SELECT A CONFIGURABLE ASSEMBLY POSITION FIRST");
        return false;
    }
    ALBOneFactoryAssemblyStarterPresentationActor* Presentation = nullptr;
    if (!FindAssemblyStarterPair(OutAuthority, Presentation, OutReason))
        return false;
    const FLBOneFactoryAssemblyLayoutState State =
        OutAuthority->CaptureLayout();
    OutStationIndex = State.Stations.IndexOfByPredicate([this](
        const FLBOneFactoryAssemblyStationState& Station)
    {
        return Station.StationId == SelectedTargetId;
    });
    if (!State.Stations.IsValidIndex(OutStationIndex))
    {
        OutReason = TEXT(
            "SELECTED ASSEMBLY POSITION NO LONGER EXISTS");
        return false;
    }
    if (!ValidateAssemblyStarterPair(
            *OutAuthority, *Presentation, OutReason))
    {
        return false;
    }
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ResolveSelectedBodyWeld(
    ALBOneFactoryBodyWeldStarterLayoutAuthority*& OutAuthority,
    int32& OutStationIndex, FString& OutReason) const
{
    OutAuthority = nullptr;
    OutStationIndex = INDEX_NONE;
    if (SelectedTargetKind
            != ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition
        || SelectedTargetId.IsNone())
    {
        OutReason = TEXT(
            "SELECT A CONFIGURABLE BODY/WELD POSITION FIRST");
        return false;
    }
    ALBOneFactoryBodyWeldStarterPresentationActor* Presentation = nullptr;
    if (!FindBodyWeldStarterPair(OutAuthority, Presentation, OutReason))
        return false;
    const FLBOneFactoryBodyWeldLayoutState State =
        OutAuthority->CaptureLayout();
    OutStationIndex = State.Stations.IndexOfByPredicate([this](
        const FLBOneFactoryBodyWeldStationState& Station)
    {
        return Station.StationId == SelectedTargetId;
    });
    if (!State.Stations.IsValidIndex(OutStationIndex))
    {
        OutReason = TEXT(
            "SELECTED BODY/WELD POSITION NO LONGER EXISTS");
        return false;
    }
    if (!ValidateBodyWeldStarterPair(
            *OutAuthority, *Presentation, OutReason))
    {
        return false;
    }
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ResolveSelectedPaint(
    ALBOneFactoryPaintStarterLayoutAuthority*& OutAuthority,
    int32& OutStationIndex, FString& OutReason) const
{
    OutAuthority = nullptr;
    OutStationIndex = INDEX_NONE;
    if (SelectedTargetKind
            != ELBOneFactoryBuilderTargetKind::PaintStarterStation
        || SelectedTargetId.IsNone())
    {
        OutReason = TEXT("SELECT A BLACK-BOX PAINT RESPONSIBILITY FIRST");
        return false;
    }
    ALBOneFactoryPaintStarterPresentationActor* Presentation = nullptr;
    if (!FindPaintStarterPair(OutAuthority, Presentation, OutReason))
        return false;
    const FLBOneFactoryPaintStarterLayoutState State =
        OutAuthority->CaptureLayout();
    OutStationIndex = State.Stations.IndexOfByPredicate([this](
        const FLBOneFactoryPaintStarterStationState& Station)
    {
        return Station.StationId == SelectedTargetId;
    });
    if (!State.Stations.IsValidIndex(OutStationIndex))
    {
        OutReason = TEXT("SELECTED PAINT RESPONSIBILITY NO LONGER EXISTS");
        return false;
    }
    if (!ValidatePaintStarterPair(
            *OutAuthority, *Presentation, OutReason))
    {
        return false;
    }
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ResolveSelectedMachine(
    ALBFactoryBuildMachine*& OutMachine, FString& OutReason) const
{
    OutMachine = nullptr;
    if (SelectedTargetKind != ELBOneFactoryBuilderTargetKind::PlayerBuildMachine
        || SelectedTargetId.IsNone())
    {
        OutReason = TEXT("SELECT A PLAYER-BUILT MACHINE FIRST");
        return false;
    }
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("PLAYER-BUILT MACHINE WORLD IS UNAVAILABLE");
        return false;
    }
    for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
    {
        if (LBOneFactoryPlayerBuilderPrivate::IsLive(*It)
            && It->GetMachineId() == SelectedTargetId)
        {
            if (OutMachine)
            {
                OutReason = TEXT("PLAYER-BUILT MACHINE ID IS NOT UNIQUE");
                OutMachine = nullptr;
                return false;
            }
            OutMachine = *It;
        }
    }
    if (!OutMachine)
    {
        OutReason = TEXT("SELECTED PLAYER-BUILT MACHINE NO LONGER EXISTS");
        return false;
    }
    return true;
}

FName ULBOneFactoryPlayerBuilderSubsystem::GetNextPanelProgramme(
    const FName CurrentPanelTypeId) const
{
    const TArray<FLBStampedPanelDefinition>& Definitions =
        LBCairnwell2040PanelCatalog::GetDefinitions();
    if (Definitions.IsEmpty()) return NAME_None;
    int32 Current = Definitions.IndexOfByPredicate([CurrentPanelTypeId](
        const FLBStampedPanelDefinition& Definition)
    {
        return Definition.PanelTypeId == CurrentPanelTypeId;
    });
    return Definitions[(Current + 1) % Definitions.Num()].PanelTypeId;
}

ELBOneFactoryPaintColour
ULBOneFactoryPlayerBuilderSubsystem::GetNextPaintColour(
    const ELBOneFactoryPaintColour CurrentColour) const
{
    using C = ELBOneFactoryPaintColour;
    switch (CurrentColour)
    {
    case C::ArcticWhite: return C::FoundryGraphite;
    case C::FoundryGraphite: return C::CairnwellTeal;
    case C::CairnwellTeal: return C::SignalRed;
    case C::SignalRed: return C::AuroraBlue;
    case C::AuroraBlue: return C::ArcticWhite;
    default: return C::CairnwellTeal;
    }
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanChangeSelectedProgramme(
    FString& OutReason) const
{
    ALBOneFactoryPressStarterLayoutAuthority* Authority = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedStarter(Authority, StationIndex, OutReason)) return false;
    const FLBOneFactoryPressStarterLayoutState State = Authority->CaptureLayout();
    const FLBOneFactoryPressStarterStationState& Station = State.Stations[StationIndex];
    if (!Station.bPlayerReconfigurable)
    {
        OutReason = TEXT(
            "THIS FIXED LOGISTICS RESPONSIBILITY HAS NO PANEL PROGRAMME; SELECT BLANK PREP, PRESS OR INSPECTION");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(State))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED PRESS WIP BEFORE CHANGING THE PROGRAMME");
        return false;
    }
    const FName Next = GetNextPanelProgramme(Station.PanelTypeId);
    if (Next.IsNone())
    {
        OutReason = TEXT("NO APPROVED PANEL PROGRAMME IS AVAILABLE");
        return false;
    }
    OutReason = FString::Printf(TEXT(
        "CHANGE %s TO %s; BLANK, DIE, INSPECTION AND DISPATCH UPDATE ATOMICALLY"),
        *Station.PanelTypeId.ToString(), *Next.ToString());
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ChangeSelectedProgramme(
    FString& OutReason)
{
    FString Reason;
    if (!CanChangeSelectedProgramme(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryPressStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* Presentation = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedStarter(Authority, StationIndex, Reason)
        || !FindStarterPair(Authority, Presentation, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryPressStarterLayoutState Before = Authority->CaptureLayout();
    const FName Next = GetNextPanelProgramme(
        Before.Stations[StationIndex].PanelTypeId);
    if (!Authority->SetStationPanelProgramme(SelectedTargetId, Next, Reason)
        || !SynchronisePresentationOrRestore(*Authority, *Presentation, Before,
            TEXT("PRESS PROGRAMME CHANGE"), Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    SetLastResult(true, FString::Printf(
        TEXT("PRESS PROGRAMME CHANGED TO %s ACROSS ALL RECIPE RESPONSIBILITIES"),
        *Next.ToString()), OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanChangeSelectedPaintProgramme(
    FString& OutReason) const
{
    ALBOneFactoryPaintStarterLayoutAuthority* Authority = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedPaint(Authority, StationIndex, OutReason))
        return false;
    const FLBOneFactoryPaintStarterLayoutState State =
        Authority->CaptureLayout();
    const FLBOneFactoryPaintStarterStationState& Station =
        State.Stations[StationIndex];
    if (!Station.bPlayerProgrammeSelectable)
    {
        OutReason = TEXT(
            "CHOOSE PAINT COLOUR AT ED-COAT, SPRAY BOOTH OR QUALITY INSPECTION");
        return false;
    }
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(State))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED PAINT WIP BEFORE CHANGING THE PROGRAMME");
        return false;
    }
    const ELBOneFactoryPaintColour Next =
        GetNextPaintColour(State.SelectedBodyColour);
    if (!ULBOneFactoryPaintStarterLayoutLibrary::IsPlayerSelectableColour(
            Next))
    {
        OutReason = TEXT("NO APPROVED PAINT PROGRAMME IS AVAILABLE");
        return false;
    }
    OutReason = FString::Printf(TEXT("CHANGE COMPLETE PAINT PROGRAMME TO %s"),
        *ULBOneFactoryPaintStarterLayoutLibrary::GetColourDisplayName(Next));
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ChangeSelectedPaintProgramme(
    FString& OutReason)
{
    FString Reason;
    if (!CanChangeSelectedPaintProgramme(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryPaintStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryPaintStarterPresentationActor* Presentation = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedPaint(Authority, StationIndex, Reason)
        || !FindPaintStarterPair(Authority, Presentation, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryPaintStarterLayoutState Before =
        Authority->CaptureLayout();
    const ELBOneFactoryPaintColour Next =
        GetNextPaintColour(Before.SelectedBodyColour);
    const FName ProgrammeStationId =
        Before.Stations[StationIndex].StationId;
    if (!Authority->SetStationPaintProgramme(
            ProgrammeStationId, Next, Reason)
        || !SynchronisePaintPresentationOrRestore(
            *Authority, *Presentation, Before,
            TEXT("PAINT PROGRAMME CHANGE"), Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    SetLastResult(true, FString::Printf(TEXT(
        "PAINT PROGRAMME CHANGED TO %s ACROSS ALL BOUND RESPONSIBILITIES"),
        *ULBOneFactoryPaintStarterLayoutLibrary::GetColourDisplayName(Next)),
        OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    CanSelectNextCompatibleBodyWeldProgramme(FString& OutReason) const
{
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedBodyWeld(Authority, StationIndex, OutReason))
        return false;
    const FLBOneFactoryBodyWeldLayoutState State = Authority->CaptureLayout();
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(State))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED BODY/WELD WIP BEFORE SELECTING A PROGRAMME");
        return false;
    }
    int32 CompatibleCount = 0;
    for (int32 Value = 0;
        Value < ULBOneFactoryBodyWeldStarterLayoutLibrary::
            RequiredProgrammeCount; ++Value)
    {
        const ELBOneFactoryBodyWeldProgramme Candidate =
            static_cast<ELBOneFactoryBodyWeldProgramme>(Value);
        if (bHasSelectedBodyWeldProgramme
            && Candidate == SelectedBodyWeldProgramme)
        {
            continue;
        }
        FLBOneFactoryBodyWeldLayoutState CandidateState;
        FString CandidateReason;
        if (LBOneFactoryPlayerBuilderPrivate::
                BuildBodyWeldConfigurationCandidate(
                    State, SelectedTargetId, Candidate,
                    CandidateState, CandidateReason))
        {
            ++CompatibleCount;
        }
    }
    if (CompatibleCount == 0)
    {
        OutReason = TEXT(
            "SELECTED BODY/WELD POSITION HAS NO OTHER ORDER-SAFE PROGRAMME");
        return false;
    }
    OutReason = FString::Printf(TEXT(
        "CYCLE %d CAPABILITY-, ORDER- AND ROBOT-COMPATIBLE BODY/WELD PROGRAMMES"),
        CompatibleCount);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    SelectNextCompatibleBodyWeldProgramme(FString& OutReason)
{
    FString Reason;
    if (!CanSelectNextCompatibleBodyWeldProgramme(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedBodyWeld(Authority, StationIndex, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryBodyWeldLayoutState State = Authority->CaptureLayout();
    const int32 Start = bHasSelectedBodyWeldProgramme
        ? static_cast<int32>(SelectedBodyWeldProgramme) : -1;
    for (int32 Offset = 1;
        Offset <= ULBOneFactoryBodyWeldStarterLayoutLibrary::
            RequiredProgrammeCount; ++Offset)
    {
        const int32 Value = (Start + Offset)
            % ULBOneFactoryBodyWeldStarterLayoutLibrary::
                RequiredProgrammeCount;
        const ELBOneFactoryBodyWeldProgramme Candidate =
            static_cast<ELBOneFactoryBodyWeldProgramme>(Value);
        FLBOneFactoryBodyWeldLayoutState CandidateState;
        FString CandidateReason;
        if (LBOneFactoryPlayerBuilderPrivate::
                BuildBodyWeldConfigurationCandidate(
                    State, SelectedTargetId, Candidate,
                    CandidateState, CandidateReason))
        {
            SelectedBodyWeldProgramme = Candidate;
            bHasSelectedBodyWeldProgramme = true;
            SetLastResult(true, FString::Printf(TEXT(
                "SELECTED BODY/WELD PROGRAMME: %s"),
                *ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    GetProgrammeDisplayName(Candidate)), OutReason);
            return true;
        }
    }
    SetLastResult(false, TEXT(
        "NO ORDER-SAFE BODY/WELD PROGRAMME COULD BE SELECTED"), OutReason);
    return false;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    CanApplySelectedBodyWeldConfiguration(FString& OutReason) const
{
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedBodyWeld(Authority, StationIndex, OutReason))
        return false;
    if (!bHasSelectedBodyWeldProgramme)
    {
        OutReason = TEXT(
            "CHOOSE A COMPATIBLE BODY/WELD PROGRAMME FIRST");
        return false;
    }
    const FLBOneFactoryBodyWeldLayoutState State = Authority->CaptureLayout();
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(State))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED BODY/WELD WIP BEFORE APPLYING PROGRAMMES OR ROBOT DUTIES");
        return false;
    }
    FLBOneFactoryBodyWeldLayoutState Candidate;
    FString CandidateReason;
    if (!LBOneFactoryPlayerBuilderPrivate::
            BuildBodyWeldConfigurationCandidate(
                State, SelectedTargetId, SelectedBodyWeldProgramme,
                Candidate, CandidateReason))
    {
        OutReason = FString::Printf(TEXT(
            "BODY/WELD CONFIGURATION WOULD BE REJECTED: %s"),
            *CandidateReason);
        return false;
    }
    const FLBOneFactoryBodyWeldStationState& Target =
        Candidate.Stations[StationIndex];
    OutReason = FString::Printf(TEXT(
        "APPLY %s AT POSITION %02d WITH LEFT %s / RIGHT %s"),
        *ULBOneFactoryBodyWeldStarterLayoutLibrary::GetProgrammeDisplayName(
            SelectedBodyWeldProgramme), Target.LinePosition,
        *ULBOneFactoryBodyWeldStarterLayoutLibrary::GetRobotRoleDisplayName(
            Target.LeftRobotRole),
        *ULBOneFactoryBodyWeldStarterLayoutLibrary::GetRobotRoleDisplayName(
            Target.RightRobotRole));
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::ApplySelectedBodyWeldConfiguration(
    FString& OutReason)
{
    FString Reason;
    if (!CanApplySelectedBodyWeldConfiguration(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* Presentation = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedBodyWeld(Authority, StationIndex, Reason)
        || !FindBodyWeldStarterPair(Authority, Presentation, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryBodyWeldLayoutState Before =
        Authority->CaptureLayout();
    FLBOneFactoryBodyWeldLayoutState Candidate;
    if (!LBOneFactoryPlayerBuilderPrivate::
            BuildBodyWeldConfigurationCandidate(
                Before, SelectedTargetId, SelectedBodyWeldProgramme,
                Candidate, Reason)
        || !Authority->RestoreLayout(Candidate, Reason)
        || !SynchroniseBodyWeldPresentationOrRestore(
            *Authority, *Presentation, Before,
            TEXT("BODY/WELD PROGRAMME + ROBOT DUTY CONFIGURATION"), Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryBodyWeldStationState* Target =
        Candidate.Stations.FindByPredicate([this](
            const FLBOneFactoryBodyWeldStationState& Station)
        {
            return Station.StationId == SelectedTargetId;
        });
    const FString Result = Target ? FString::Printf(TEXT(
            "APPLIED %s WITH LEFT %s / RIGHT %s; BODY/WELD RECOMMISSION REQUIRED"),
            *ULBOneFactoryBodyWeldStarterLayoutLibrary::GetProgrammeDisplayName(
                SelectedBodyWeldProgramme),
            *ULBOneFactoryBodyWeldStarterLayoutLibrary::GetRobotRoleDisplayName(
                Target->LeftRobotRole),
            *ULBOneFactoryBodyWeldStarterLayoutLibrary::GetRobotRoleDisplayName(
                Target->RightRobotRole))
        : FString(TEXT("BODY/WELD CONFIGURATION COMMITTED"));
    SetLastResult(true, Result, OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    CanSelectNextCompatibleAssemblyOperation(FString& OutReason) const
{
    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedAssembly(Authority, StationIndex, OutReason))
        return false;
    const FLBOneFactoryAssemblyLayoutState State = Authority->CaptureLayout();
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(State))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED ASSEMBLY WIP BEFORE CONFIGURING OPERATIONS");
        return false;
    }
    const FLBOneFactoryAssemblyStationState& Station =
        State.Stations[StationIndex];
    int32 CompatibleCount = 0;
    for (int32 Value = 0;
        Value < ULBOneFactoryAssemblyStarterLayoutLibrary::
            RequiredOperationCount; ++Value)
    {
        if (ULBOneFactoryAssemblyStarterLayoutLibrary::StationSupportsOperation(
                Station, static_cast<ELBOneFactoryAssemblyOperation>(Value)))
        {
            ++CompatibleCount;
        }
    }
    if (CompatibleCount == 0)
    {
        OutReason = TEXT(
            "SELECTED ASSEMBLY POSITION HAS NO COMPATIBLE OPERATIONS");
        return false;
    }
    OutReason = FString::Printf(TEXT(
        "CYCLE %d CAPABILITY-COMPATIBLE OPERATIONS FOR ASSEMBLY POSITION %02d"),
        CompatibleCount, Station.LinePosition);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    SelectNextCompatibleAssemblyOperation(FString& OutReason)
{
    FString Reason;
    if (!CanSelectNextCompatibleAssemblyOperation(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedAssembly(Authority, StationIndex, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryAssemblyLayoutState State = Authority->CaptureLayout();
    const FLBOneFactoryAssemblyStationState& Station =
        State.Stations[StationIndex];
    const int32 Start = bHasSelectedAssemblyOperation
        ? static_cast<int32>(SelectedAssemblyOperation) : -1;
    for (int32 Offset = 1;
        Offset <= ULBOneFactoryAssemblyStarterLayoutLibrary::
            RequiredOperationCount; ++Offset)
    {
        const int32 Value = (Start + Offset)
            % ULBOneFactoryAssemblyStarterLayoutLibrary::RequiredOperationCount;
        const ELBOneFactoryAssemblyOperation Candidate =
            static_cast<ELBOneFactoryAssemblyOperation>(Value);
        if (ULBOneFactoryAssemblyStarterLayoutLibrary::StationSupportsOperation(
                Station, Candidate))
        {
            SelectedAssemblyOperation = Candidate;
            bHasSelectedAssemblyOperation = true;
            SetLastResult(true, FString::Printf(TEXT("SELECTED OPERATION: %s"),
                *ULBOneFactoryAssemblyStarterLayoutLibrary::
                    GetOperationDisplayName(Candidate)), OutReason);
            return true;
        }
    }
    SetLastResult(false, TEXT(
        "NO CAPABILITY-COMPATIBLE ASSEMBLY OPERATION COULD BE SELECTED"),
        OutReason);
    return false;
}

bool ULBOneFactoryPlayerBuilderSubsystem::
    CanAssignSelectedAssemblyOperation(FString& OutReason) const
{
    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
    int32 TargetIndex = INDEX_NONE;
    if (!ResolveSelectedAssembly(Authority, TargetIndex, OutReason))
        return false;
    if (!bHasSelectedAssemblyOperation)
    {
        OutReason = TEXT(
            "CHOOSE A CAPABILITY-COMPATIBLE ASSEMBLY OPERATION FIRST");
        return false;
    }
    FLBOneFactoryAssemblyLayoutState Candidate = Authority->CaptureLayout();
    if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(Candidate))
    {
        OutReason = TEXT(
            "FINISH OR RELEASE ALL ACTIVE AND RESERVED ASSEMBLY WIP BEFORE REASSIGNING OPERATIONS");
        return false;
    }
    FLBOneFactoryAssemblyStationState& Target =
        Candidate.Stations[TargetIndex];
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::StationSupportsOperation(
            Target, SelectedAssemblyOperation))
    {
        OutReason = TEXT(
            "SELECTED ASSEMBLY POSITION LACKS THE REQUIRED CAPABILITY");
        return false;
    }
    FLBOneFactoryAssemblyStationState* Source =
        Candidate.Stations.FindByPredicate([this](
            const FLBOneFactoryAssemblyStationState& Station)
        {
            return Station.AssignedOperations.Contains(
                SelectedAssemblyOperation);
        });
    if (!Source)
    {
        OutReason = TEXT(
            "SELECTED ASSEMBLY OPERATION HAS NO AUTHORITATIVE SOURCE POSITION");
        return false;
    }
    if (Source->StationId == Target.StationId)
    {
        OutReason = TEXT(
            "SELECTED ASSEMBLY OPERATION IS ALREADY ASSIGNED HERE");
        return false;
    }
    Source->AssignedOperations.RemoveSingle(SelectedAssemblyOperation);
    Target.AssignedOperations.Add(SelectedAssemblyOperation);
    Target.AssignedOperations.Sort([](
        const ELBOneFactoryAssemblyOperation Left,
        const ELBOneFactoryAssemblyOperation Right)
    {
        return static_cast<uint8>(Left) < static_cast<uint8>(Right);
    });
    Candidate.bCommissioned = false;
    ++Candidate.Revision;
    FString ValidationReason;
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, ValidationReason))
    {
        OutReason = FString::Printf(TEXT(
            "ASSEMBLY ASSIGNMENT WOULD BE REJECTED: %s"),
            *ValidationReason);
        return false;
    }
    OutReason = FString::Printf(TEXT("ASSIGN %s TO ASSEMBLY POSITION %02d"),
        *ULBOneFactoryAssemblyStarterLayoutLibrary::GetOperationDisplayName(
            SelectedAssemblyOperation), Target.LinePosition);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::AssignSelectedAssemblyOperation(
    FString& OutReason)
{
    FString Reason;
    if (!CanAssignSelectedAssemblyOperation(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryAssemblyStarterPresentationActor* Presentation = nullptr;
    int32 StationIndex = INDEX_NONE;
    if (!ResolveSelectedAssembly(Authority, StationIndex, Reason)
        || !FindAssemblyStarterPair(Authority, Presentation, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FLBOneFactoryAssemblyLayoutState Before = Authority->CaptureLayout();
    if (!Authority->AssignOperation(
            SelectedAssemblyOperation, SelectedTargetId, Reason)
        || !SynchroniseAssemblyPresentationOrRestore(
            *Authority, *Presentation, Before,
            TEXT("ASSEMBLY OPERATION ASSIGNMENT"), Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    SetLastResult(true, FString::Printf(TEXT("ASSIGNED %s TO %s ATOMICALLY"),
        *ULBOneFactoryAssemblyStarterLayoutLibrary::GetOperationDisplayName(
            SelectedAssemblyOperation), *SelectedTargetId.ToString()),
        OutReason);
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanMoveSelected(
    FString& OutReason) const
{
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PressStarterStation)
    {
        ALBOneFactoryPressStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        if (!ResolveSelectedStarter(Authority, StationIndex, OutReason)) return false;
        FLBOneFactoryPressStarterLayoutState Candidate = Authority->CaptureLayout();
        if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(Candidate))
        {
            OutReason = TEXT(
                "FINISH OR RELEASE ALL ACTIVE AND RESERVED PRESS WIP BEFORE MOVING A STATION");
            return false;
        }
        Candidate.Stations[StationIndex].WorldTransform.AddToTranslation(
            FVector(LBOneFactoryPlayerBuilderPrivate::EditStepCm, 0.0f, 0.0f));
        ++Candidate.Revision;
        if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
                Candidate, OutReason))
        {
            OutReason = FString::Printf(TEXT("ONE-METRE MOVE WOULD BE REJECTED: %s"),
                *OutReason);
            return false;
        }
        OutReason = TEXT("MOVE THE SELECTED STARTER RESPONSIBILITY EAST BY 1 M");
        return true;
    }

    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition)
    {
        ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        if (!ResolveSelectedBodyWeld(Authority, StationIndex, OutReason))
            return false;
        FLBOneFactoryBodyWeldLayoutState Candidate =
            Authority->CaptureLayout();
        if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
                Candidate))
        {
            OutReason = TEXT(
                "FINISH OR RELEASE ALL ACTIVE AND RESERVED BODY/WELD WIP BEFORE MOVING A POSITION");
            return false;
        }
        Candidate.Stations[StationIndex].WorldTransform.AddToTranslation(
            FVector(LBOneFactoryPlayerBuilderPrivate::EditStepCm,
                0.0f, 0.0f));
        Candidate.bCommissioned = false;
        ++Candidate.Revision;
        if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
                Candidate, OutReason))
        {
            OutReason = FString::Printf(TEXT(
                "ONE-METRE BODY/WELD MOVE WOULD BE REJECTED: %s"),
                *OutReason);
            return false;
        }
        OutReason = TEXT(
            "MOVE THE SELECTED BODY/WELD POSITION EAST BY 1 M");
        return true;
    }

    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition)
    {
        ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        if (!ResolveSelectedAssembly(Authority, StationIndex, OutReason))
            return false;
        FLBOneFactoryAssemblyLayoutState Candidate = Authority->CaptureLayout();
        if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(Candidate))
        {
            OutReason = TEXT(
                "FINISH OR RELEASE ALL ACTIVE AND RESERVED ASSEMBLY WIP BEFORE MOVING A POSITION");
            return false;
        }
        Candidate.Stations[StationIndex].WorldTransform.AddToTranslation(
            FVector(LBOneFactoryPlayerBuilderPrivate::EditStepCm, 0.0f, 0.0f));
        Candidate.bCommissioned = false;
        ++Candidate.Revision;
        if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
                Candidate, OutReason))
        {
            OutReason = FString::Printf(TEXT(
                "ONE-METRE ASSEMBLY MOVE WOULD BE REJECTED: %s"),
                *OutReason);
            return false;
        }
        OutReason = TEXT(
            "MOVE THE SELECTED ASSEMBLY POSITION EAST BY 1 M");
        return true;
    }

    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PaintStarterStation)
    {
        ALBOneFactoryPaintStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        if (!ResolveSelectedPaint(Authority, StationIndex, OutReason))
            return false;
        FLBOneFactoryPaintStarterLayoutState Candidate =
            Authority->CaptureLayout();
        if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
                Candidate))
        {
            OutReason = TEXT(
                "FINISH OR RELEASE ALL ACTIVE AND RESERVED PAINT WIP BEFORE MOVING A RESPONSIBILITY");
            return false;
        }
        Candidate.Stations[StationIndex].WorldTransform.AddToTranslation(
            FVector(LBOneFactoryPlayerBuilderPrivate::EditStepCm,
                0.0f, 0.0f));
        ++Candidate.Revision;
        if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
                Candidate, OutReason))
        {
            OutReason = FString::Printf(TEXT(
                "ONE-METRE PAINT MOVE WOULD BE REJECTED: %s"),
                *OutReason);
            return false;
        }
        OutReason = TEXT(
            "MOVE THE SELECTED PAINT RESPONSIBILITY EAST BY 1 M");
        return true;
    }

    ALBFactoryBuildMachine* Machine = nullptr;
    if (!ResolveSelectedMachine(Machine, OutReason)) return false;
    ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    if (!Builder)
    {
        OutReason = TEXT("TRANSACTIONAL MACHINE BUILDER IS UNAVAILABLE");
        return false;
    }
    if (!Builder->CanEditMachine(Machine->GetMachineId(), OutReason)) return false;
    FTransform Proposed = Machine->GetActorTransform();
    Proposed.AddToTranslation(FVector(
        LBOneFactoryPlayerBuilderPrivate::EditStepCm, 0.0f, 0.0f));
    if (!Builder->ValidateMachineTransformForEdit(
            Machine->GetMachineId(), Proposed, OutReason))
    {
        return false;
    }
    OutReason = TEXT("MOVE PLAYER-BUILT MACHINE EAST BY 1 M TRANSACTIONALLY");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::MoveSelected(FString& OutReason)
{
    FString Reason;
    if (!CanMoveSelected(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PressStarterStation)
    {
        ALBOneFactoryPressStarterLayoutAuthority* Authority = nullptr;
        ALBOneFactoryPressStarterPresentationActor* Presentation = nullptr;
        int32 StationIndex = INDEX_NONE;
        if (!ResolveSelectedStarter(Authority, StationIndex, Reason)
            || !FindStarterPair(Authority, Presentation, Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        const FLBOneFactoryPressStarterLayoutState Before = Authority->CaptureLayout();
        FTransform Proposed = Before.Stations[StationIndex].WorldTransform;
        Proposed.AddToTranslation(FVector(
            LBOneFactoryPlayerBuilderPrivate::EditStepCm, 0.0f, 0.0f));
        if (!Authority->MoveStation(SelectedTargetId, Proposed, Reason)
            || !SynchronisePresentationOrRestore(*Authority, *Presentation,
                Before, TEXT("PRESS STATION MOVE"), Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        SetLastResult(true, TEXT(
            "PRESS STATION MOVED 1 M; DATA, SIX ROUTES AND PRESENTATION STAY COHERENT"),
            OutReason);
        return true;
    }

    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition)
    {
        ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
        ALBOneFactoryBodyWeldStarterPresentationActor* Presentation = nullptr;
        int32 StationIndex = INDEX_NONE;
        if (!ResolveSelectedBodyWeld(Authority, StationIndex, Reason)
            || !FindBodyWeldStarterPair(Authority, Presentation, Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        const FLBOneFactoryBodyWeldLayoutState Before =
            Authority->CaptureLayout();
        FTransform Proposed = Before.Stations[StationIndex].WorldTransform;
        Proposed.AddToTranslation(FVector(
            LBOneFactoryPlayerBuilderPrivate::EditStepCm, 0.0f, 0.0f));
        if (!Authority->MoveStation(SelectedTargetId, Proposed, Reason)
            || !SynchroniseBodyWeldPresentationOrRestore(
                *Authority, *Presentation, Before,
                TEXT("BODY/WELD POSITION MOVE"), Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        SetLastResult(true, TEXT(
            "BODY/WELD POSITION MOVED 1 M; DATA, 17 ROUTES AND PRESENTATION STAY COHERENT"),
            OutReason);
        return true;
    }

    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition)
    {
        ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
        ALBOneFactoryAssemblyStarterPresentationActor* Presentation = nullptr;
        int32 StationIndex = INDEX_NONE;
        if (!ResolveSelectedAssembly(Authority, StationIndex, Reason)
            || !FindAssemblyStarterPair(Authority, Presentation, Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        const FLBOneFactoryAssemblyLayoutState Before =
            Authority->CaptureLayout();
        FTransform Proposed = Before.Stations[StationIndex].WorldTransform;
        Proposed.AddToTranslation(FVector(
            LBOneFactoryPlayerBuilderPrivate::EditStepCm, 0.0f, 0.0f));
        if (!Authority->MoveStation(SelectedTargetId, Proposed, Reason)
            || !SynchroniseAssemblyPresentationOrRestore(
                *Authority, *Presentation, Before,
                TEXT("ASSEMBLY POSITION MOVE"), Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        SetLastResult(true, TEXT(
            "ASSEMBLY POSITION MOVED 1 M; DATA, 23 ROUTES AND PRESENTATION STAY COHERENT"),
            OutReason);
        return true;
    }

    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PaintStarterStation)
    {
        ALBOneFactoryPaintStarterLayoutAuthority* Authority = nullptr;
        ALBOneFactoryPaintStarterPresentationActor* Presentation = nullptr;
        int32 StationIndex = INDEX_NONE;
        if (!ResolveSelectedPaint(Authority, StationIndex, Reason)
            || !FindPaintStarterPair(Authority, Presentation, Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        const FLBOneFactoryPaintStarterLayoutState Before =
            Authority->CaptureLayout();
        FTransform Proposed = Before.Stations[StationIndex].WorldTransform;
        Proposed.AddToTranslation(FVector(
            LBOneFactoryPlayerBuilderPrivate::EditStepCm, 0.0f, 0.0f));
        if (!Authority->MoveStation(SelectedTargetId, Proposed, Reason)
            || !SynchronisePaintPresentationOrRestore(
                *Authority, *Presentation, Before,
                TEXT("PAINT RESPONSIBILITY MOVE"), Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        SetLastResult(true, TEXT(
            "PAINT RESPONSIBILITY MOVED 1 M; DATA, SEVEN ROUTES AND PRESENTATION STAY COHERENT"),
            OutReason);
        return true;
    }

    ALBFactoryBuildMachine* Machine = nullptr;
    if (!ResolveSelectedMachine(Machine, Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    FTransform Proposed = Machine->GetActorTransform();
    Proposed.AddToTranslation(FVector(
        LBOneFactoryPlayerBuilderPrivate::EditStepCm, 0.0f, 0.0f));
    const bool bMoved = Builder
        && Builder->MoveMachine(Machine->GetMachineId(), Proposed, Reason);
    SetLastResult(bMoved, Reason, OutReason);
    return bMoved;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanDisconnectSelected(
    FString& OutReason) const
{
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PressStarterStation)
    {
        OutReason = TEXT(
            "CANONICAL STARTER ROUTES ARE ONE COHERENT SIX-ROUTE PACKAGE AND CANNOT BE DISCONNECTED");
        return false;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition)
    {
        OutReason = TEXT(
            "THE 17 BODY/WELD SKID LINKS ARE ONE ORDERED PROCESS AND CANNOT BE DISCONNECTED");
        return false;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition)
    {
        OutReason = TEXT(
            "THE 23 ASSEMBLY CARRIER LINKS ARE ONE ORDERED PROCESS AND CANNOT BE DISCONNECTED");
        return false;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PaintStarterStation)
    {
        OutReason = TEXT(
            "THE SEVEN PAINT CARRIER LINKS ARE ONE BLACK-BOX PROCESS AND CANNOT BE DISCONNECTED");
        return false;
    }
    ALBFactoryBuildMachine* Machine = nullptr;
    if (!ResolveSelectedMachine(Machine, OutReason)) return false;
    const ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    if (!Builder)
    {
        OutReason = TEXT("TRANSACTIONAL MACHINE BUILDER IS UNAVAILABLE");
        return false;
    }
    if (!Builder->CanEditMachine(Machine->GetMachineId(), OutReason)) return false;
    if (!GetWorld()->GetSubsystem<ULBFactoryConnectionSubsystem>())
    {
        OutReason = TEXT("TRANSACTIONAL CONNECTION AUTHORITY IS UNAVAILABLE");
        return false;
    }
    OutReason = TEXT("DISCONNECT EVERY ROUTE TOUCHING THE SELECTED PLAYER-BUILT MACHINE");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::DisconnectSelected(FString& OutReason)
{
    FString Reason;
    if (!CanDisconnectSelected(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    ALBFactoryBuildMachine* Machine = nullptr;
    ULBFactoryConnectionSubsystem* Connections = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryConnectionSubsystem>() : nullptr;
    const bool bDisconnected = ResolveSelectedMachine(Machine, Reason)
        && Connections && Connections->DisconnectActor(Machine, Reason);
    SetLastResult(bDisconnected, Reason, OutReason);
    return bDisconnected;
}

bool ULBOneFactoryPlayerBuilderSubsystem::CanRemoveSelected(
    FString& OutReason) const
{
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PressStarterStation)
    {
        OutReason = TEXT(
            "CANONICAL STARTER STATIONS CANNOT BE REMOVED INDIVIDUALLY; PLAYER-ADDED MACHINES CAN");
        return false;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition)
    {
        OutReason = TEXT(
            "CANONICAL BODY/WELD POSITIONS CANNOT BE REMOVED INDIVIDUALLY; USE REMOVE BODY/WELD STARTER FOR THE COMPLETE IDLE PAIR");
        return false;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition)
    {
        OutReason = TEXT(
            "CANONICAL ASSEMBLY POSITIONS CANNOT BE REMOVED INDIVIDUALLY; REASSIGN THEIR OPERATIONS INSTEAD");
        return false;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PaintStarterStation)
    {
        ALBOneFactoryProductionFlowAuthority* Production = nullptr;
        ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
        if (!FindRuntimeBackbone(Production, Coordinator, OutReason))
            return false;
        ALBOneFactoryPaintStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        if (!ResolveSelectedPaint(Authority, StationIndex, OutReason))
            return false;
        (void)StationIndex;
        if (LBOneFactoryPlayerBuilderPrivate::HasActiveOrReservedWIP(
                Authority->CaptureLayout()))
        {
            OutReason = TEXT(
                "FINISH OR RELEASE ALL ACTIVE AND RESERVED PAINT WIP BEFORE REMOVING THE STARTER PAIR");
            return false;
        }
        TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*>
            AssemblyAuthorities;
        TArray<ALBOneFactoryAssemblyStarterPresentationActor*>
            AssemblyPresentations;
        LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
            GetWorld(), AssemblyAuthorities);
        LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
            GetWorld(), AssemblyPresentations);
        if (!AssemblyAuthorities.IsEmpty()
            || !AssemblyPresentations.IsEmpty())
        {
            OutReason = TEXT(
                "REMOVE THE DOWNSTREAM ASSEMBLY STARTER BEFORE REMOVING PAINT");
            return false;
        }
        OutReason = TEXT(
            "REMOVE THE COMPLETE PAINT DATA AND PRESENTATION PAIR ATOMICALLY");
        return true;
    }
    ALBFactoryBuildMachine* Machine = nullptr;
    if (!ResolveSelectedMachine(Machine, OutReason)) return false;
    const ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    if (!Builder)
    {
        OutReason = TEXT("TRANSACTIONAL MACHINE BUILDER IS UNAVAILABLE");
        return false;
    }
    if (!Builder->CanEditMachine(Machine->GetMachineId(), OutReason)) return false;
    OutReason = TEXT("REMOVE THE SELECTED PLAYER-BUILT MACHINE TRANSACTIONALLY");
    return true;
}

bool ULBOneFactoryPlayerBuilderSubsystem::RemoveSelected(FString& OutReason)
{
    FString Reason;
    if (!CanRemoveSelected(Reason))
    {
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PaintStarterStation)
    {
        ALBOneFactoryPaintStarterLayoutAuthority* Authority = nullptr;
        ALBOneFactoryPaintStarterPresentationActor* Presentation = nullptr;
        if (!FindPaintStarterPair(Authority, Presentation, Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        ALBOneFactoryProductionFlowAuthority* Production = nullptr;
        ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
        if (!FindRuntimeBackbone(Production, Coordinator, Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        const FLBOneFactoryProductionLedgerState LedgerBefore =
            Production->CaptureLedger();
        if (!Production->SetDepartmentCommissioned(
                ELBOneFactoryDepartment::Paint, false, Reason))
        {
            SetLastResult(false, Reason, OutReason);
            return false;
        }
        const bool bPresentationDestroyed = Presentation->Destroy();
        const bool bAuthorityDestroyed = Authority->Destroy();
        const bool bPairDestroyed =
            bPresentationDestroyed && bAuthorityDestroyed;
        if (bPairDestroyed)
        {
            SelectedTargetKind = ELBOneFactoryBuilderTargetKind::None;
            SelectedTargetId = NAME_None;
            bHasSelectedBodyWeldProgramme = false;
            bHasSelectedAssemblyOperation = false;
            Reason = TEXT(
                "REMOVED COMPLETE PAINT DATA + PRESENTATION PAIR ATOMICALLY");
        }
        else
        {
            FString LedgerRestoreReason;
            Production->RestoreLedger(LedgerBefore, LedgerRestoreReason);
            Reason = FString::Printf(TEXT(
                "PAINT PAIR DESTROY FAILED CLOSED (DATA %s / PRESENTATION %s / LEDGER %s)"),
                bAuthorityDestroyed ? TEXT("DESTROYED") : TEXT("LIVE"),
                bPresentationDestroyed ? TEXT("DESTROYED") : TEXT("LIVE"),
                *LedgerRestoreReason);
        }
        SetLastResult(bPairDestroyed, Reason, OutReason);
        return bPairDestroyed;
    }
    ALBFactoryBuildMachine* Machine = nullptr;
    ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    if (!ResolveSelectedMachine(Machine, Reason) || !Builder)
    {
        if (Reason.IsEmpty()) Reason = TEXT("TRANSACTIONAL MACHINE BUILDER IS UNAVAILABLE");
        SetLastResult(false, Reason, OutReason);
        return false;
    }
    const FName RemovedId = Machine->GetMachineId();
    const bool bRemoved = Builder->RemoveMachine(RemovedId, Reason);
    if (bRemoved)
    {
        SelectedTargetKind = ELBOneFactoryBuilderTargetKind::None;
        SelectedTargetId = NAME_None;
        Reason = FString::Printf(TEXT("REMOVED PLAYER-BUILT MACHINE %s TRANSACTIONALLY"),
            *RemovedId.ToString());
    }
    SetLastResult(bRemoved, Reason, OutReason);
    return bRemoved;
}

FString ULBOneFactoryPlayerBuilderSubsystem::DescribeSelectedTarget() const
{
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PressStarterStation)
    {
        ALBOneFactoryPressStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        FString Reason;
        if (ResolveSelectedStarter(Authority, StationIndex, Reason))
        {
            const FLBOneFactoryPressStarterLayoutState State =
                Authority->CaptureLayout();
            const FLBOneFactoryPressStarterStationState& Station =
                State.Stations[StationIndex];
            const FString Programme = Station.PanelTypeId.IsNone()
                ? TEXT("fixed responsibility") : Station.PanelTypeId.ToString();
            return FString::Printf(TEXT("%s [%s] | %s"),
                *LBOneFactoryPlayerBuilderPrivate::RoleLabel(Station.Role),
                *Station.StationId.ToString(), *Programme);
        }
        return Reason;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition)
    {
        ALBOneFactoryBodyWeldStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        FString Reason;
        if (ResolveSelectedBodyWeld(Authority, StationIndex, Reason))
        {
            const FLBOneFactoryBodyWeldLayoutState State =
                Authority->CaptureLayout();
            const FLBOneFactoryBodyWeldStationState& Station =
                State.Stations[StationIndex];
            const FString SelectedProgramme =
                bHasSelectedBodyWeldProgramme
                ? ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    GetProgrammeDisplayName(SelectedBodyWeldProgramme)
                : TEXT("none selected");
            return FString::Printf(TEXT(
                "%s [%s] | CHOSEN: %s | ROBOTS: %s / %s"),
                *LBOneFactoryPlayerBuilderPrivate::BodyWeldPositionLabel(
                    Station), *Station.StationId.ToString(),
                *SelectedProgramme,
                *ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    GetRobotRoleDisplayName(Station.LeftRobotRole),
                *ULBOneFactoryBodyWeldStarterLayoutLibrary::
                    GetRobotRoleDisplayName(Station.RightRobotRole));
        }
        return Reason;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition)
    {
        ALBOneFactoryAssemblyStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        FString Reason;
        if (ResolveSelectedAssembly(Authority, StationIndex, Reason))
        {
            const FLBOneFactoryAssemblyLayoutState State =
                Authority->CaptureLayout();
            const FLBOneFactoryAssemblyStationState& Station =
                State.Stations[StationIndex];
            const FString SelectedOperation = bHasSelectedAssemblyOperation
                ? ULBOneFactoryAssemblyStarterLayoutLibrary::
                    GetOperationDisplayName(SelectedAssemblyOperation)
                : TEXT("none selected");
            return FString::Printf(TEXT("%s [%s] | CHOSEN: %s"),
                *LBOneFactoryPlayerBuilderPrivate::AssemblyPositionLabel(
                    Station), *Station.StationId.ToString(),
                *SelectedOperation);
        }
        return Reason;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PaintStarterStation)
    {
        ALBOneFactoryPaintStarterLayoutAuthority* Authority = nullptr;
        int32 StationIndex = INDEX_NONE;
        FString Reason;
        if (ResolveSelectedPaint(Authority, StationIndex, Reason))
        {
            const FLBOneFactoryPaintStarterLayoutState State =
                Authority->CaptureLayout();
            const FLBOneFactoryPaintStarterStationState& Station =
                State.Stations[StationIndex];
            return FString::Printf(TEXT("%s [%s] | PROGRAMME: %s"),
                *LBOneFactoryPlayerBuilderPrivate::PaintRoleLabel(
                    Station.Role),
                *Station.StationId.ToString(),
                *ULBOneFactoryPaintStarterLayoutLibrary::
                    GetColourDisplayName(State.SelectedBodyColour));
        }
        return Reason;
    }
    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PlayerBuildMachine)
    {
        ALBFactoryBuildMachine* Machine = nullptr;
        FString Reason;
        return ResolveSelectedMachine(Machine, Reason)
            ? LBOneFactoryPlayerBuilderPrivate::MachineLabel(*Machine) : Reason;
    }
    return TEXT("No station selected");
}

TArray<FLBOneFactoryBuilderUMGAction>
ULBOneFactoryPlayerBuilderSubsystem::GetUMGActions() const
{
    TArray<FLBOneFactoryBuilderUMGAction> Actions;
    Actions.SetNum(UMGActionCount);
    for (int32 Index = 0; Index < Actions.Num(); ++Index)
        Actions[Index].ActionIndex = Index;

    TArray<ALBOneFactoryPressStarterLayoutAuthority*> Authorities;
    TArray<ALBOneFactoryPressStarterPresentationActor*> Presentations;
    TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*> AssemblyAuthorities;
    TArray<ALBOneFactoryAssemblyStarterPresentationActor*>
        AssemblyPresentations;
    TArray<ALBOneFactoryBodyWeldStarterLayoutAuthority*> BodyAuthorities;
    TArray<ALBOneFactoryBodyWeldStarterPresentationActor*>
        BodyPresentations;
    TArray<ALBOneFactoryPaintStarterLayoutAuthority*> PaintAuthorities;
    TArray<ALBOneFactoryPaintStarterPresentationActor*> PaintPresentations;
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Authorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Presentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), AssemblyPresentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), BodyAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), BodyPresentations);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintAuthorities);
    LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
        GetWorld(), PaintPresentations);
    FString Reason;
    const bool bNoStarterActors = Authorities.IsEmpty()
        && Presentations.IsEmpty() && BodyAuthorities.IsEmpty()
        && BodyPresentations.IsEmpty() && PaintAuthorities.IsEmpty()
        && PaintPresentations.IsEmpty() && AssemblyAuthorities.IsEmpty()
        && AssemblyPresentations.IsEmpty();
    const bool bPressPair = Authorities.Num() == 1
        && Presentations.Num() == 1;
    const bool bBodyEmpty = BodyAuthorities.IsEmpty()
        && BodyPresentations.IsEmpty();
    const bool bBodyPair = BodyAuthorities.Num() == 1
        && BodyPresentations.Num() == 1;
    const bool bAssemblyEmpty = AssemblyAuthorities.IsEmpty()
        && AssemblyPresentations.IsEmpty();
    const bool bAssemblyPair = AssemblyAuthorities.Num() == 1
        && AssemblyPresentations.Num() == 1;
    const bool bPaintEmpty = PaintAuthorities.IsEmpty()
        && PaintPresentations.IsEmpty();
    const bool bPaintPair = PaintAuthorities.Num() == 1
        && PaintPresentations.Num() == 1;
    if (bNoStarterActors)
    {
        Actions[0].Title = TEXT("New Factory");
        Actions[0].bEnabled = CanCreateNewFactory(Reason);
        Actions[0].Detail = Reason;
    }
    else if (!bPressPair || (!bBodyEmpty && !bBodyPair)
        || (!bAssemblyEmpty && !bAssemblyPair)
        || (!bPaintEmpty && !bPaintPair))
    {
        Actions[0].Title = TEXT("Starter repair required");
        Actions[0].bEnabled = false;
        Actions[0].Detail = FString::Printf(TEXT(
            "FAIL CLOSED: PRESS %d/%d, BODY/WELD %d/%d, PAINT %d/%d, ASSEMBLY %d/%d; NO PARTIAL STARTER WILL BE OVERWRITTEN"),
            Authorities.Num(), Presentations.Num(), BodyAuthorities.Num(),
            BodyPresentations.Num(), PaintAuthorities.Num(),
            PaintPresentations.Num(), AssemblyAuthorities.Num(),
            AssemblyPresentations.Num());
    }
    else if (!Authorities[0]->IsCommissioned())
    {
        Actions[0].Title = TEXT("Commission Press starter");
        Actions[0].bEnabled = bBodyEmpty && bPaintEmpty && bAssemblyEmpty
            && CanCommissionPressStarter(Reason);
        if (!bBodyEmpty || !bPaintEmpty || !bAssemblyEmpty)
            Reason = TEXT(
                "A DOWNSTREAM STARTER EXISTS BEFORE PRESS COMMISSION; LIFECYCLE IS OUT OF ORDER");
        Actions[0].Detail = Reason;
    }
    else if (bBodyEmpty)
    {
        Actions[0].Title = TEXT("Build Body/Weld starter");
        Actions[0].bEnabled = bPaintEmpty && bAssemblyEmpty
            && CanCreateBodyWeldStarter(Reason);
        if (!bPaintEmpty || !bAssemblyEmpty)
            Reason = TEXT(
                "PAINT OR ASSEMBLY EXISTS BEFORE BODY/WELD; LIFECYCLE IS OUT OF ORDER");
        Actions[0].Detail = Reason;
    }
    else if (!BodyAuthorities[0]->IsCommissioned())
    {
        Actions[0].Title = TEXT("Commission Body/Weld line");
        Actions[0].bEnabled = bPaintEmpty && bAssemblyEmpty
            && CanCommissionBodyWeldStarter(Reason);
        if (!bPaintEmpty || !bAssemblyEmpty)
            Reason = TEXT(
                "PAINT OR ASSEMBLY EXISTS BEFORE BODY/WELD COMMISSION; LIFECYCLE IS OUT OF ORDER");
        Actions[0].Detail = Reason;
    }
    else if (bPaintEmpty)
    {
        Actions[0].Title = TEXT("Build Paint starter");
        Actions[0].bEnabled = bAssemblyEmpty
            && CanCreatePaintStarter(Reason);
        if (!bAssemblyEmpty)
            Reason = TEXT(
                "ASSEMBLY EXISTS BEFORE PAINT; LIFECYCLE IS OUT OF ORDER");
        Actions[0].Detail = Reason;
    }
    else if (!PaintAuthorities[0]->IsCommissioned())
    {
        Actions[0].Title = TEXT("Commission Paint line");
        Actions[0].bEnabled = bAssemblyEmpty
            && CanCommissionPaintStarter(Reason);
        if (!bAssemblyEmpty)
            Reason = TEXT(
                "ASSEMBLY EXISTS BEFORE PAINT COMMISSION; LIFECYCLE IS OUT OF ORDER");
        Actions[0].Detail = Reason;
    }
    else if (bAssemblyEmpty)
    {
        Actions[0].Title = TEXT("Build Assembly starter");
        Actions[0].bEnabled = CanCreateAssemblyStarter(Reason);
        Actions[0].Detail = Reason;
    }
    else if (!AssemblyAuthorities[0]->IsCommissioned())
    {
        Actions[0].Title = TEXT("Commission Assembly line");
        Actions[0].bEnabled = CanCommissionAssemblyStarter(Reason);
        Actions[0].Detail = Reason;
    }
    else
    {
        Actions[0].Title = TEXT("Core starters commissioned");
        Actions[0].bEnabled = false;
        FString PressReason;
        FString BodyReason;
        FString AssemblyReason;
        FString PaintReason;
        const bool bPressValid = ValidateStarterPair(
            *Authorities[0], *Presentations[0], PressReason);
        const bool bBodyValid = ValidateBodyWeldStarterPair(
            *BodyAuthorities[0], *BodyPresentations[0], BodyReason);
        const bool bAssemblyValid = ValidateAssemblyStarterPair(
            *AssemblyAuthorities[0], *AssemblyPresentations[0],
            AssemblyReason);
        const bool bPaintValid = ValidatePaintStarterPair(
            *PaintAuthorities[0], *PaintPresentations[0], PaintReason);
        Actions[0].Detail = bPressValid && bBodyValid
            && bPaintValid && bAssemblyValid
            ? TEXT("PRESS + BODY/WELD + PAINT + ASSEMBLY DATA AND NATIVE PRESENTATIONS LIVE")
            : PressReason + TEXT(" | ") + BodyReason + TEXT(" | ")
                + PaintReason + TEXT(" | ") + AssemblyReason;
    }

    TArray<FSelectableTarget> Targets;
    CollectSelectableTargets(Targets);
    Actions[1].Title = TEXT("Select next station");
    Actions[1].bEnabled = !Targets.IsEmpty();
    Actions[1].Detail = Targets.IsEmpty()
        ? TEXT("CREATE NEW FACTORY BEFORE SELECTING A RESPONSIBILITY")
        : FString::Printf(TEXT("CURRENT: %s | %d SELECTABLE RESPONSIBILITIES"),
            *DescribeSelectedTarget(), Targets.Num());

    if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PressStarterStation)
    {
        Actions[2].Title = TEXT("Next panel programme");
        Actions[2].bEnabled = CanChangeSelectedProgramme(Reason);
        Actions[2].Detail = Reason;
        Actions[3].Title = TEXT("Move station east 1 m");
        Actions[3].bEnabled = CanMoveSelected(Reason);
        Actions[3].Detail = Reason;
        Actions[4].Title = TEXT("Remove / disconnect");
        Actions[4].bEnabled = false;
        CanRemoveSelected(Reason);
        FString DisconnectReason;
        CanDisconnectSelected(DisconnectReason);
        Actions[4].Detail = Reason + TEXT(" | ") + DisconnectReason;
    }
    else if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition)
    {
        Actions[2].Title = TEXT("Next compatible Body/Weld programme");
        Actions[2].bEnabled =
            CanSelectNextCompatibleBodyWeldProgramme(Reason);
        Actions[2].Detail = Reason;
        Actions[3].Title = TEXT("Apply programme + robot duties");
        Actions[3].bEnabled =
            CanApplySelectedBodyWeldConfiguration(Reason);
        Actions[3].Detail = Reason;
        Actions[4].Title = TEXT("Move Body/Weld position east 1 m");
        Actions[4].bEnabled = CanMoveSelected(Reason);
        Actions[4].Detail = Reason;
    }
    else if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition)
    {
        Actions[2].Title = TEXT("Next compatible operation");
        Actions[2].bEnabled =
            CanSelectNextCompatibleAssemblyOperation(Reason);
        Actions[2].Detail = Reason;
        Actions[3].Title = TEXT("Assign operation here");
        Actions[3].bEnabled = CanAssignSelectedAssemblyOperation(Reason);
        Actions[3].Detail = Reason;
        Actions[4].Title = TEXT("Move position east 1 m");
        Actions[4].bEnabled = CanMoveSelected(Reason);
        Actions[4].Detail = Reason;
    }
    else if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PaintStarterStation)
    {
        Actions[2].Title = TEXT("Next paint colour");
        Actions[2].bEnabled = CanChangeSelectedPaintProgramme(Reason);
        Actions[2].Detail = Reason;
        Actions[3].Title = TEXT("Move paint station east 1 m");
        Actions[3].bEnabled = CanMoveSelected(Reason);
        Actions[3].Detail = Reason;
        Actions[4].Title = TEXT("Remove complete Paint starter");
        Actions[4].bEnabled = CanRemoveSelected(Reason);
        Actions[4].Detail = Reason;
    }
    else if (SelectedTargetKind ==
        ELBOneFactoryBuilderTargetKind::PlayerBuildMachine)
    {
        Actions[2].Title = TEXT("Move station east 1 m");
        Actions[2].bEnabled = CanMoveSelected(Reason);
        Actions[2].Detail = Reason;
        Actions[3].Title = TEXT("Disconnect routes");
        Actions[3].bEnabled = CanDisconnectSelected(Reason);
        Actions[3].Detail = Reason;
        Actions[4].Title = TEXT("Remove station");
        Actions[4].bEnabled = CanRemoveSelected(Reason);
        Actions[4].Detail = Reason;
    }
    else
    {
        for (int32 Index = 2; Index < UMGActionCount; ++Index)
        {
            Actions[Index].Title = Index == 2 ? TEXT("Programme")
                : Index == 3 ? TEXT("Move / disconnect") : TEXT("Remove");
            Actions[Index].Detail = TEXT("SELECT A STATION RESPONSIBILITY FIRST");
            Actions[Index].bEnabled = false;
        }
    }
    return Actions;
}

FString ULBOneFactoryPlayerBuilderSubsystem::GetUMGSummary() const
{
    ALBOneFactoryBootstrap* Bootstrap = nullptr;
    FString BootstrapReason;
    const bool bHasBootstrap = FindSingleBootstrap(Bootstrap, BootstrapReason);
    ALBOneFactoryPressStarterLayoutAuthority* Authority = nullptr;
    ALBOneFactoryPressStarterPresentationActor* Presentation = nullptr;
    FString PairReason;
    const bool bHasPair = FindStarterPair(Authority, Presentation, PairReason);
    const FString PairState = bHasPair
        ? (Authority->IsCommissioned() ? TEXT("COMMISSIONED")
            : TEXT("AWAITING COMMISSION"))
        : TEXT("NOT CREATED");
    FString PressProvenance = TEXT("NATIVE-ONLY NOT YET MATERIALISED");
    if (bHasPair)
    {
        FString ValidationReason;
        PressProvenance = ValidateStarterPair(*Authority, *Presentation,
            ValidationReason) ? TEXT("NATIVE-ONLY PASS") : ValidationReason;
    }

    ALBOneFactoryBodyWeldStarterLayoutAuthority* BodyAuthority = nullptr;
    ALBOneFactoryBodyWeldStarterPresentationActor* BodyPresentation = nullptr;
    FString BodyPairReason;
    const bool bHasBodyPair = FindBodyWeldStarterPair(
        BodyAuthority, BodyPresentation, BodyPairReason);
    const FString BodyState = bHasBodyPair
        ? (BodyAuthority->IsCommissioned() ? TEXT("COMMISSIONED")
            : TEXT("AWAITING COMMISSION"))
        : TEXT("NOT CREATED");
    FString BodyProvenance = TEXT("NATIVE-ONLY NOT YET MATERIALISED");
    if (bHasBodyPair)
    {
        FString ValidationReason;
        BodyProvenance = ValidateBodyWeldStarterPair(
            *BodyAuthority, *BodyPresentation, ValidationReason)
            ? TEXT("NATIVE-ONLY PASS") : ValidationReason;
    }

    ALBOneFactoryAssemblyStarterLayoutAuthority* AssemblyAuthority = nullptr;
    ALBOneFactoryAssemblyStarterPresentationActor* AssemblyPresentation =
        nullptr;
    FString AssemblyPairReason;
    const bool bHasAssemblyPair = FindAssemblyStarterPair(
        AssemblyAuthority, AssemblyPresentation, AssemblyPairReason);
    const FString AssemblyState = bHasAssemblyPair
        ? (AssemblyAuthority->IsCommissioned() ? TEXT("COMMISSIONED")
            : TEXT("AWAITING COMMISSION"))
        : TEXT("NOT CREATED");
    FString AssemblyProvenance = TEXT("NATIVE-ONLY NOT YET MATERIALISED");
    if (bHasAssemblyPair)
    {
        FString ValidationReason;
        AssemblyProvenance = ValidateAssemblyStarterPair(
            *AssemblyAuthority, *AssemblyPresentation, ValidationReason)
            ? TEXT("NATIVE-ONLY PASS") : ValidationReason;
    }

    ALBOneFactoryPaintStarterLayoutAuthority* PaintAuthority = nullptr;
    ALBOneFactoryPaintStarterPresentationActor* PaintPresentation = nullptr;
    FString PaintPairReason;
    const bool bHasPaintPair = FindPaintStarterPair(
        PaintAuthority, PaintPresentation, PaintPairReason);
    const FString PaintState = bHasPaintPair
        ? (PaintAuthority->IsCommissioned() ? TEXT("COMMISSIONED")
            : TEXT("AWAITING COMMISSION"))
        : TEXT("NOT CREATED");
    FString PaintProvenance = TEXT("NATIVE-ONLY NOT YET MATERIALISED");
    if (bHasPaintPair)
    {
        FString ValidationReason;
        PaintProvenance = ValidatePaintStarterPair(
            *PaintAuthority, *PaintPresentation, ValidationReason)
            ? TEXT("NATIVE-ONLY PASS") : ValidationReason;
    }
    return FString::Printf(TEXT(
        "BOOTSTRAP: %s | PRESS: %s (%s) | BODY/WELD: %s (%s) | PAINT: %s (%s) | ASSEMBLY: %s (%s) | SELECTED: %s | LAST %s: %s"),
        bHasBootstrap && Bootstrap->HasValidShell() ? TEXT("READY")
            : *BootstrapReason,
        *PairState, *PressProvenance, *BodyState, *BodyProvenance,
        *PaintState, *PaintProvenance, *AssemblyState,
        *AssemblyProvenance, *DescribeSelectedTarget(),
        bLastActionSucceeded ? TEXT("PASS") : TEXT("REJECT"),
        *LastActionReason);
}

bool ULBOneFactoryPlayerBuilderSubsystem::ExecuteUMGAction(
    const int32 ActionIndex, FString& OutReason)
{
    if (!FMath::IsWithin(ActionIndex, 0, UMGActionCount))
    {
        SetLastResult(false, TEXT("ONEFACTORY UMG ACTION INDEX IS INVALID"),
            OutReason);
        return false;
    }
    // A restored/pre-populated OneFactory can reach the management surface without
    // passing through MaterialiseStarterPresentation. Curate the visible press
    // department before evaluating even a disabled action so candidate map dressing
    // cannot reappear behind an already-live native presentation.
    LBOneFactoryPlayerBuilderPrivate::RetireLegacyPressPresentationForOneFactory(
        GetWorld());
    const TArray<FLBOneFactoryBuilderUMGAction> Actions = GetUMGActions();
    if (!Actions[ActionIndex].bEnabled)
    {
        SetLastResult(false, Actions[ActionIndex].Detail, OutReason);
        return false;
    }
    if (ActionIndex == 0)
    {
        TArray<ALBOneFactoryPressStarterLayoutAuthority*> Authorities;
        TArray<ALBOneFactoryPressStarterPresentationActor*> Presentations;
        TArray<ALBOneFactoryBodyWeldStarterLayoutAuthority*> BodyAuthorities;
        TArray<ALBOneFactoryBodyWeldStarterPresentationActor*>
            BodyPresentations;
        TArray<ALBOneFactoryAssemblyStarterLayoutAuthority*>
            AssemblyAuthorities;
        TArray<ALBOneFactoryAssemblyStarterPresentationActor*>
            AssemblyPresentations;
        TArray<ALBOneFactoryPaintStarterLayoutAuthority*> PaintAuthorities;
        TArray<ALBOneFactoryPaintStarterPresentationActor*>
            PaintPresentations;
        LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Authorities);
        LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(GetWorld(), Presentations);
        LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
            GetWorld(), BodyAuthorities);
        LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
            GetWorld(), BodyPresentations);
        LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
            GetWorld(), AssemblyAuthorities);
        LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
            GetWorld(), AssemblyPresentations);
        LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
            GetWorld(), PaintAuthorities);
        LBOneFactoryPlayerBuilderPrivate::CollectLiveActors(
            GetWorld(), PaintPresentations);
        if (Authorities.IsEmpty() && Presentations.IsEmpty()
            && BodyAuthorities.IsEmpty()
            && BodyPresentations.IsEmpty()
            && AssemblyAuthorities.IsEmpty()
            && AssemblyPresentations.IsEmpty()
            && PaintAuthorities.IsEmpty()
            && PaintPresentations.IsEmpty())
        {
            return CreateNewFactory(OutReason);
        }
        if (Authorities.Num() == 1 && Presentations.Num() == 1
            && !Authorities[0]->IsCommissioned())
        {
            return CommissionPressStarter(OutReason);
        }
        if (Authorities.Num() == 1 && Presentations.Num() == 1
            && Authorities[0]->IsCommissioned()
            && BodyAuthorities.IsEmpty()
            && BodyPresentations.IsEmpty())
        {
            return CreateBodyWeldStarter(OutReason);
        }
        if (BodyAuthorities.Num() == 1
            && BodyPresentations.Num() == 1
            && !BodyAuthorities[0]->IsCommissioned())
        {
            return CommissionBodyWeldStarter(OutReason);
        }
        if (BodyAuthorities.Num() == 1
            && BodyPresentations.Num() == 1
            && BodyAuthorities[0]->IsCommissioned()
            && PaintAuthorities.IsEmpty()
            && PaintPresentations.IsEmpty())
        {
            return CreatePaintStarter(OutReason);
        }
        if (PaintAuthorities.Num() == 1
            && PaintPresentations.Num() == 1
            && !PaintAuthorities[0]->IsCommissioned())
        {
            return CommissionPaintStarter(OutReason);
        }
        if (PaintAuthorities.Num() == 1
            && PaintPresentations.Num() == 1
            && PaintAuthorities[0]->IsCommissioned()
            && AssemblyAuthorities.IsEmpty()
            && AssemblyPresentations.IsEmpty())
        {
            return CreateAssemblyStarter(OutReason);
        }
        if (AssemblyAuthorities.Num() == 1
            && AssemblyPresentations.Num() == 1
            && !AssemblyAuthorities[0]->IsCommissioned())
        {
            return CommissionAssemblyStarter(OutReason);
        }
        SetLastResult(false,
            TEXT("ONEFACTORY LIFECYCLE ACTION HAS NO VALID NEXT TRANSITION"),
            OutReason);
        return false;
    }
    if (ActionIndex == 1) return SelectNextTarget(OutReason);
    if (ActionIndex == 2)
    {
        if (SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::PressStarterStation)
        {
            return ChangeSelectedProgramme(OutReason);
        }
        if (SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition)
        {
            return SelectNextCompatibleBodyWeldProgramme(OutReason);
        }
        if (SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition)
        {
            return SelectNextCompatibleAssemblyOperation(OutReason);
        }
        if (SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::PaintStarterStation)
        {
            return ChangeSelectedPaintProgramme(OutReason);
        }
        return MoveSelected(OutReason);
    }
    if (ActionIndex == 3)
    {
        if (SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::PressStarterStation)
        {
            return MoveSelected(OutReason);
        }
        if (SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition)
        {
            return ApplySelectedBodyWeldConfiguration(OutReason);
        }
        if (SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition)
        {
            return AssignSelectedAssemblyOperation(OutReason);
        }
        if (SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::PaintStarterStation)
        {
            return MoveSelected(OutReason);
        }
        return DisconnectSelected(OutReason);
    }
    if (SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::BodyWeldStarterPosition
        || SelectedTargetKind ==
            ELBOneFactoryBuilderTargetKind::AssemblyStarterPosition)
    {
        return MoveSelected(OutReason);
    }
    return RemoveSelected(OutReason);
}
