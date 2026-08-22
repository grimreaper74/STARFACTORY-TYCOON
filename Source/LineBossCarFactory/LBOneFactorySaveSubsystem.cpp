#include "LBOneFactorySaveSubsystem.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "LBOneFactoryAssemblyStarterPresentationActor.h"
#include "LBOneFactoryBodyWeldStarterPresentationActor.h"
#include "LBOneFactoryPaintStarterPresentationActor.h"
#include "LBOneFactoryPlayerBuilderSubsystem.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactoryRuntimeRegistrySubsystem.h"

namespace LBOneFactorySaveSubsystemPrivate
{
    struct FFactoryActors
    {
        ALBOneFactoryPressStarterLayoutAuthority* PressAuthority = nullptr;
        ALBOneFactoryPressStarterPresentationActor* PressPresentation = nullptr;
        ALBOneFactoryBodyWeldStarterLayoutAuthority* BodyAuthority = nullptr;
        ALBOneFactoryBodyWeldStarterPresentationActor* BodyPresentation = nullptr;
        ALBOneFactoryPaintStarterLayoutAuthority* PaintAuthority = nullptr;
        ALBOneFactoryPaintStarterPresentationActor* PaintPresentation = nullptr;
        ALBOneFactoryAssemblyStarterLayoutAuthority* AssemblyAuthority = nullptr;
        ALBOneFactoryAssemblyStarterPresentationActor* AssemblyPresentation = nullptr;
        ALBOneFactoryProductionFlowAuthority* ProductionAuthority = nullptr;
    };

    struct FStarterActorCounts
    {
        int32 PressAuthority = 0;
        int32 PressPresentation = 0;
        int32 BodyAuthority = 0;
        int32 BodyPresentation = 0;
        int32 PaintAuthority = 0;
        int32 PaintPresentation = 0;
        int32 AssemblyAuthority = 0;
        int32 AssemblyPresentation = 0;

        int32 Total() const
        {
            return PressAuthority + PressPresentation + BodyAuthority
                + BodyPresentation + PaintAuthority + PaintPresentation
                + AssemblyAuthority + AssemblyPresentation;
        }

        bool IsComplete() const
        {
            return PressAuthority == 1 && PressPresentation == 1
                && BodyAuthority == 1 && BodyPresentation == 1
                && PaintAuthority == 1 && PaintPresentation == 1
                && AssemblyAuthority == 1 && AssemblyPresentation == 1;
        }
    };

    template<typename ActorType>
    bool FindExactActor(UWorld* World, const TCHAR* Label, ActorType*& OutActor,
        FString& OutReason)
    {
        OutActor = nullptr;
        int32 Count = 0;
        if (World)
        {
            for (TActorIterator<ActorType> It(World); It; ++It)
            {
                ActorType* Candidate = *It;
                if (!IsValid(Candidate) || Candidate->IsActorBeingDestroyed())
                {
                    continue;
                }
                ++Count;
                OutActor = Candidate;
            }
        }
        if (Count != 1)
        {
            OutActor = nullptr;
            OutReason = FString::Printf(
                TEXT("ONEFACTORY SAVE REQUIRES EXACTLY ONE %s; FOUND %d"),
                Label, Count);
            return false;
        }
        if (!OutActor || OutActor->GetClass() != ActorType::StaticClass())
        {
            OutActor = nullptr;
            OutReason = FString::Printf(TEXT(
                "ONEFACTORY SAVE REQUIRES THE EXACT NATIVE %s CLASS"), Label);
            return false;
        }
        return true;
    }

    template<typename ActorType>
    int32 CountLiveActors(UWorld* World)
    {
        int32 Count = 0;
        if (!World) return Count;
        for (TActorIterator<ActorType> It(World); It; ++It)
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++Count;
        return Count;
    }

    FStarterActorCounts CountStarterActors(UWorld* World)
    {
        FStarterActorCounts Counts;
        Counts.PressAuthority =
            CountLiveActors<ALBOneFactoryPressStarterLayoutAuthority>(World);
        Counts.PressPresentation =
            CountLiveActors<ALBOneFactoryPressStarterPresentationActor>(World);
        Counts.BodyAuthority =
            CountLiveActors<ALBOneFactoryBodyWeldStarterLayoutAuthority>(World);
        Counts.BodyPresentation =
            CountLiveActors<ALBOneFactoryBodyWeldStarterPresentationActor>(World);
        Counts.PaintAuthority =
            CountLiveActors<ALBOneFactoryPaintStarterLayoutAuthority>(World);
        Counts.PaintPresentation =
            CountLiveActors<ALBOneFactoryPaintStarterPresentationActor>(World);
        Counts.AssemblyAuthority =
            CountLiveActors<ALBOneFactoryAssemblyStarterLayoutAuthority>(World);
        Counts.AssemblyPresentation =
            CountLiveActors<ALBOneFactoryAssemblyStarterPresentationActor>(World);
        return Counts;
    }

    bool FindRuntimeBackbone(UWorld* World,
        ALBOneFactoryProductionFlowAuthority*& OutProduction,
        ALBOneFactoryRuntimeCoordinator*& OutCoordinator,
        FString& OutReason)
    {
        OutProduction = nullptr;
        OutCoordinator = nullptr;
        ULBOneFactoryRuntimeRegistrySubsystem* Registry =
            World ? World->GetSubsystem<ULBOneFactoryRuntimeRegistrySubsystem>()
                : nullptr;
        if (!Registry || !Registry->ResolveRuntimeBackbone(
                OutProduction, OutCoordinator, OutReason))
        {
            if (OutReason.IsEmpty())
            {
                OutReason = TEXT(
                    "ONEFACTORY SAVE REQUIRES THE REGISTERED RUNTIME BACKBONE");
            }
            return false;
        }
        return true;
    }

    bool ValidateFreshLedger(
        const FLBOneFactoryProductionLedgerState& Ledger,
        FString& OutReason)
    {
        if (!ULBOneFactoryProductionFlowLibrary::ValidateLedger(
                Ledger, OutReason))
            return false;
        if (!Ledger.Units.IsEmpty()
            || Ledger.Commissioning.bPressCommissioned
            || Ledger.Commissioning.bBodyCommissioned
            || Ledger.Commissioning.bPaintCommissioned
            || Ledger.Commissioning.bAssemblyCommissioned
            || Ledger.CompletedVehicleCount != 0
            || Ledger.DispatchedVehicleCount != 0)
        {
            OutReason = TEXT(
                "ONEFACTORY EMPTY-SHELL LOAD REQUIRES AN EMPTY UNCOMMISSIONED LIVE LEDGER");
            return false;
        }
        return true;
    }

    void DestroyCreatedActors(TArray<AActor*>& Actors)
    {
        for (int32 Index = Actors.Num() - 1; Index >= 0; --Index)
            if (IsValid(Actors[Index])
                && !Actors[Index]->IsActorBeingDestroyed())
                Actors[Index]->Destroy();
        Actors.Reset();
    }

    bool DiscoverFactory(UWorld* World, FFactoryActors& OutActors,
        FString& OutReason)
    {
        OutActors = FFactoryActors();
        OutReason.Reset();
        if (!World)
        {
            OutReason = TEXT("ONEFACTORY SAVE HAS NO WORLD");
            return false;
        }

        return FindExactActor(World, TEXT("PRESS LAYOUT AUTHORITY"),
                OutActors.PressAuthority, OutReason)
            && FindExactActor(World, TEXT("PRESS PRESENTATION PAIR"),
                OutActors.PressPresentation, OutReason)
            && FindExactActor(World, TEXT("BODY/WELD LAYOUT AUTHORITY"),
                OutActors.BodyAuthority, OutReason)
            && FindExactActor(World, TEXT("BODY/WELD PRESENTATION PAIR"),
                OutActors.BodyPresentation, OutReason)
            && FindExactActor(World, TEXT("PAINT LAYOUT AUTHORITY"),
                OutActors.PaintAuthority, OutReason)
            && FindExactActor(World, TEXT("PAINT PRESENTATION PAIR"),
                OutActors.PaintPresentation, OutReason)
            && FindExactActor(World, TEXT("ASSEMBLY LAYOUT AUTHORITY"),
                OutActors.AssemblyAuthority, OutReason)
            && FindExactActor(World, TEXT("ASSEMBLY PRESENTATION PAIR"),
                OutActors.AssemblyPresentation, OutReason)
            && FindExactActor(World, TEXT("PRODUCTION LEDGER AUTHORITY"),
                OutActors.ProductionAuthority, OutReason);
    }

    bool ValidateActorIdentity(const FFactoryActors& Actors,
        FString& OutReason)
    {
        if (!Actors.PressAuthority->ActorHasTag(
                ALBOneFactoryPressStarterLayoutAuthority::GetAuthorityTag())
            || !Actors.PressPresentation->ActorHasTag(
                ALBOneFactoryPressStarterPresentationActor::GetPresentationTag())
            || !Actors.BodyAuthority->ActorHasTag(
                ALBOneFactoryBodyWeldStarterLayoutAuthority::GetAuthorityTag())
            || !Actors.BodyPresentation->ActorHasTag(
                ALBOneFactoryBodyWeldStarterPresentationActor::GetPresentationTag())
            || !Actors.PaintAuthority->ActorHasTag(
                ALBOneFactoryPaintStarterLayoutAuthority::GetAuthorityTag())
            || !Actors.PaintPresentation->ActorHasTag(
                ALBOneFactoryPaintStarterPresentationActor::GetPresentationTag())
            || !Actors.AssemblyAuthority->ActorHasTag(
                ALBOneFactoryAssemblyStarterLayoutAuthority::GetAuthorityTag())
            || !Actors.AssemblyPresentation->ActorHasTag(
                ALBOneFactoryAssemblyStarterPresentationActor::GetPresentationTag())
            || !Actors.ProductionAuthority->ActorHasTag(
                ALBOneFactoryProductionFlowAuthority::GetAuthorityTag()))
        {
            OutReason = TEXT("ONEFACTORY SAVE ACTOR IDENTITY TAG CONTRACT FAILED");
            return false;
        }
        if (!Actors.PressPresentation->ActorHasTag(TEXT("LB.NotProcessWIP"))
            || !Actors.BodyPresentation->ActorHasTag(TEXT("LB.NotProcessWIP"))
            || !Actors.PaintPresentation->ActorHasTag(TEXT("LB.NotProcessWIP"))
            || !Actors.AssemblyPresentation->ActorHasTag(TEXT("LB.NotProcessWIP"))
            || Actors.PressPresentation->RepresentsProcessWIP()
            || Actors.BodyPresentation->RepresentsProcessWIP()
            || Actors.PaintPresentation->RepresentsProcessWIP()
            || Actors.AssemblyPresentation->RepresentsProcessWIP())
        {
            OutReason = TEXT(
                "ONEFACTORY SAVE PRESENTATION PAIRS MUST BE VISUAL-ONLY PROXIES");
            return false;
        }
        return true;
    }

    bool ValidatePresentationPairing(const FFactoryActors& Actors,
        const FLBOneFactorySaveState& State, FString& OutReason)
    {
        if (!Actors.PressPresentation->IsPresentationConfigured()
            || Actors.PressPresentation->GetConfiguredLayoutId()
                != State.PressLayout.LayoutId
            || Actors.PressPresentation->GetConfiguredLayoutRevision()
                != State.PressLayout.Revision
            || Actors.PressPresentation->GetVisibleInstanceCount() <= 0)
        {
            OutReason = TEXT(
                "ONEFACTORY PRESS AUTHORITY/PRESENTATION PAIR IS NOT COHERENT");
            return false;
        }
        if (!Actors.BodyPresentation->IsPresentationConfigured()
            // Fail closed: a hidden presentation renders nothing yet counts
            // every instance.
            || Actors.BodyPresentation->IsHidden()
            || Actors.BodyPresentation->GetConfiguredLayoutId()
                != State.BodyWeldLayout.LayoutId
            || Actors.BodyPresentation->GetConfiguredLayoutRevision()
                != State.BodyWeldLayout.Revision
            || Actors.BodyPresentation->GetVisibleInstanceCount() <= 0)
        {
            OutReason = TEXT(
                "ONEFACTORY BODY/WELD AUTHORITY/PRESENTATION PAIR IS NOT COHERENT");
            return false;
        }
        if (!Actors.PaintPresentation->IsPresentationConfigured()
            // Fail closed on visibility, like Body/Weld.
            || Actors.PaintPresentation->IsHidden()
            || Actors.PaintPresentation->GetConfiguredLayoutId()
                != State.PaintLayout.LayoutId
            || Actors.PaintPresentation->GetConfiguredLayoutRevision()
                != State.PaintLayout.Revision
            || Actors.PaintPresentation->GetVisibleInstanceCount() <= 0)
        {
            OutReason = TEXT(
                "ONEFACTORY PAINT AUTHORITY/PRESENTATION PAIR IS NOT COHERENT");
            return false;
        }
        if (!Actors.AssemblyPresentation->IsPresentationConfigured()
            // Fail closed on visibility, like Body/Weld.
            || Actors.AssemblyPresentation->IsHidden()
            || Actors.AssemblyPresentation->GetConfiguredLayoutId()
                != State.AssemblyLayout.LayoutId
            || Actors.AssemblyPresentation->GetConfiguredLayoutRevision()
                != State.AssemblyLayout.Revision
            || Actors.AssemblyPresentation->GetVisibleInstanceCount() <= 0)
        {
            OutReason = TEXT(
                "ONEFACTORY ASSEMBLY AUTHORITY/PRESENTATION PAIR IS NOT COHERENT");
            return false;
        }
        return true;
    }

    bool CaptureAuthorities(const FFactoryActors& Actors,
        FLBOneFactorySaveState& OutState, FString& OutReason)
    {
        OutState = ULBOneFactorySaveGame::MakeCanonicalEmptyState();
        OutState.CapturedAtUtc = FDateTime::UtcNow();
        OutState.PressLayout = Actors.PressAuthority->CaptureLayout();
        OutState.BodyWeldLayout = Actors.BodyAuthority->CaptureLayout();
        OutState.PaintLayout = Actors.PaintAuthority->CaptureLayout();
        OutState.AssemblyLayout = Actors.AssemblyAuthority->CaptureLayout();
        OutState.ProductionLedger = Actors.ProductionAuthority->CaptureLedger();
        OutState.PayloadRevision = OutState.ProductionLedger.Revision;

        if (!ULBOneFactorySaveGame::ValidateState(OutState, OutReason))
        {
            return false;
        }
        return ValidatePresentationPairing(Actors, OutState, OutReason);
    }

    bool ResolveAll(const TArray<FSoftObjectPath>& Paths, const TCHAR* Label,
        FString& OutReason)
    {
        for (const FSoftObjectPath& Path : Paths)
        {
            if (!Path.IsValid() || (!Path.ResolveObject() && !Path.TryLoad()))
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY %s PRESENTATION DEPENDENCY FAILED: %s"),
                    Label, *Path.ToString());
                return false;
            }
        }
        return true;
    }

    bool PreflightPresentations(const FLBOneFactorySaveState& State,
        FString& OutReason)
    {
        TArray<FSoftObjectPath> Paths =
            ALBOneFactoryPressStarterPresentationActor::GetRequiredNativeAssetPaths();
        if (!ALBOneFactoryPressStarterPresentationActor::
                ValidateNativePresentationReferences(
                    ALBOneFactoryPressStarterPresentationActor::
                        GetPresentationClassPath(), Paths, OutReason)
            || !ALBOneFactoryPressStarterPresentationActor::
                ValidatePresentationContract(State.PressLayout,
                    ALBOneFactoryPressStarterPresentationActor::
                        BuildExpectedPresentationItems(State.PressLayout), OutReason)
            || !ResolveAll(Paths, TEXT("PRESS"), OutReason))
        {
            return false;
        }

        Paths = ALBOneFactoryBodyWeldStarterPresentationActor::
            GetRequiredNativeAssetPaths();
        if (!ALBOneFactoryBodyWeldStarterPresentationActor::
                ValidateNativePresentationReferences(
                    ALBOneFactoryBodyWeldStarterPresentationActor::
                        GetPresentationClassPath(), Paths, OutReason)
            || !ALBOneFactoryBodyWeldStarterPresentationActor::
                ValidatePresentationContract(State.BodyWeldLayout,
                    ALBOneFactoryBodyWeldStarterPresentationActor::
                        BuildExpectedPresentationItems(State.BodyWeldLayout), OutReason)
            || !ResolveAll(Paths, TEXT("BODY/WELD"), OutReason))
        {
            return false;
        }

        Paths = ALBOneFactoryPaintStarterPresentationActor::
            GetRequiredNativeAssetPaths();
        if (!ALBOneFactoryPaintStarterPresentationActor::
                ValidateNativePresentationReferences(
                    ALBOneFactoryPaintStarterPresentationActor::
                        GetPresentationClassPath(), Paths, OutReason)
            || !ALBOneFactoryPaintStarterPresentationActor::
                ValidatePresentationContract(State.PaintLayout,
                    ALBOneFactoryPaintStarterPresentationActor::
                        BuildExpectedPresentationItems(State.PaintLayout), OutReason)
            || !ResolveAll(Paths, TEXT("PAINT"), OutReason))
        {
            return false;
        }

        Paths = ALBOneFactoryAssemblyStarterPresentationActor::
            GetRequiredNativeAssetPaths();
        if (!ALBOneFactoryAssemblyStarterPresentationActor::
                ValidateNativePresentationReferences(
                    ALBOneFactoryAssemblyStarterPresentationActor::
                        GetPresentationClassPath(), Paths, OutReason)
            || !ALBOneFactoryAssemblyStarterPresentationActor::
                ValidatePresentationContract(State.AssemblyLayout,
                    ALBOneFactoryAssemblyStarterPresentationActor::
                        BuildExpectedPresentationItems(State.AssemblyLayout), OutReason)
            || !ResolveAll(Paths, TEXT("ASSEMBLY"), OutReason))
        {
            return false;
        }
        return true;
    }

    bool RestoreAuthorities(const FFactoryActors& Actors,
        const FLBOneFactorySaveState& State, FString& OutReason)
    {
        FString Detail;
        if (!Actors.PressAuthority->RestoreLayout(State.PressLayout, Detail))
        {
            OutReason = FString(TEXT("PRESS AUTHORITY RESTORE FAILED: "))
                + Detail;
            return false;
        }
        if (!Actors.BodyAuthority->RestoreLayout(State.BodyWeldLayout, Detail))
        {
            OutReason = FString(TEXT("BODY/WELD AUTHORITY RESTORE FAILED: "))
                + Detail;
            return false;
        }
        if (!Actors.PaintAuthority->RestoreLayout(State.PaintLayout, Detail))
        {
            OutReason = FString(TEXT("PAINT AUTHORITY RESTORE FAILED: "))
                + Detail;
            return false;
        }
        if (!Actors.AssemblyAuthority->RestoreLayout(State.AssemblyLayout, Detail))
        {
            OutReason = FString(TEXT("ASSEMBLY AUTHORITY RESTORE FAILED: "))
                + Detail;
            return false;
        }
        if (!Actors.ProductionAuthority->RestoreLedger(
                State.ProductionLedger, Detail))
        {
            OutReason = FString(TEXT("PRODUCTION LEDGER RESTORE FAILED: "))
                + Detail;
            return false;
        }
        return true;
    }

    bool RebuildPresentations(const FFactoryActors& Actors,
        const FLBOneFactorySaveState& State, FString& OutReason)
    {
        FString Detail;
        if (!Actors.PressPresentation->ConfigureFromLayout(
                State.PressLayout, Detail))
        {
            OutReason = FString(TEXT("PRESS PRESENTATION REBUILD FAILED: "))
                + Detail;
            return false;
        }
        if (!Actors.BodyPresentation->ConfigureFromLayout(
                State.BodyWeldLayout, Detail))
        {
            OutReason = FString(
                TEXT("BODY/WELD PRESENTATION REBUILD FAILED: ")) + Detail;
            return false;
        }
        if (!Actors.PaintPresentation->ConfigureFromLayout(
                State.PaintLayout, Detail))
        {
            OutReason = FString(TEXT("PAINT PRESENTATION REBUILD FAILED: "))
                + Detail;
            return false;
        }
        if (!Actors.AssemblyPresentation->ConfigureFromLayout(
                State.AssemblyLayout, Detail))
        {
            OutReason = FString(TEXT("ASSEMBLY PRESENTATION REBUILD FAILED: "))
                + Detail;
            return false;
        }
        return ValidatePresentationPairing(Actors, State, OutReason);
    }

    bool RestoreAuthoritiesForRollback(const FFactoryActors& Actors,
        const FLBOneFactorySaveState& State, FString& OutReason)
    {
        TArray<FString> Failures;
        FString Detail;
        if (!Actors.PressAuthority->RestoreLayout(State.PressLayout, Detail))
        {
            Failures.Add(FString(TEXT("PRESS: ")) + Detail);
        }
        Detail.Reset();
        if (!Actors.BodyAuthority->RestoreLayout(State.BodyWeldLayout, Detail))
        {
            Failures.Add(FString(TEXT("BODY/WELD: ")) + Detail);
        }
        Detail.Reset();
        if (!Actors.PaintAuthority->RestoreLayout(State.PaintLayout, Detail))
        {
            Failures.Add(FString(TEXT("PAINT: ")) + Detail);
        }
        Detail.Reset();
        if (!Actors.AssemblyAuthority->RestoreLayout(
                State.AssemblyLayout, Detail))
        {
            Failures.Add(FString(TEXT("ASSEMBLY: ")) + Detail);
        }
        Detail.Reset();
        if (!Actors.ProductionAuthority->RestoreLedger(
                State.ProductionLedger, Detail))
        {
            Failures.Add(FString(TEXT("PRODUCTION: ")) + Detail);
        }

        if (!Failures.IsEmpty())
        {
            OutReason = FString::Join(Failures, TEXT(" | "));
            return false;
        }
        OutReason = TEXT("ALL FIVE DATA AUTHORITIES RESTORED");
        return true;
    }

    bool RebuildPresentationsForRollback(const FFactoryActors& Actors,
        const FLBOneFactorySaveState& State, FString& OutReason)
    {
        TArray<FString> Failures;
        FString Detail;
        if (!Actors.PressPresentation->ConfigureFromLayout(
                State.PressLayout, Detail))
        {
            Failures.Add(FString(TEXT("PRESS: ")) + Detail);
        }
        Detail.Reset();
        if (!Actors.BodyPresentation->ConfigureFromLayout(
                State.BodyWeldLayout, Detail))
        {
            Failures.Add(FString(TEXT("BODY/WELD: ")) + Detail);
        }
        Detail.Reset();
        if (!Actors.PaintPresentation->ConfigureFromLayout(
                State.PaintLayout, Detail))
        {
            Failures.Add(FString(TEXT("PAINT: ")) + Detail);
        }
        Detail.Reset();
        if (!Actors.AssemblyPresentation->ConfigureFromLayout(
                State.AssemblyLayout, Detail))
        {
            Failures.Add(FString(TEXT("ASSEMBLY: ")) + Detail);
        }

        Detail.Reset();
        if (!ValidatePresentationPairing(Actors, State, Detail))
        {
            Failures.Add(FString(TEXT("PAIRING: ")) + Detail);
        }
        if (!Failures.IsEmpty())
        {
            OutReason = FString::Join(Failures, TEXT(" | "));
            return false;
        }
        OutReason = TEXT("ALL FOUR PRESENTATION PAIRS REBUILT");
        return true;
    }

    bool Rollback(const FFactoryActors& Actors,
        const FLBOneFactorySaveState& RollbackState, FString& OutDetail)
    {
        FString AuthorityDetail;
        const bool bAuthoritiesRestored = RestoreAuthoritiesForRollback(
            Actors, RollbackState, AuthorityDetail);
        FString PresentationDetail;
        const bool bPresentationsRestored = RebuildPresentationsForRollback(
            Actors, RollbackState, PresentationDetail);
        if (!bAuthoritiesRestored || !bPresentationsRestored)
        {
            OutDetail = FString::Printf(
                TEXT("ROLLBACK FAILED [DATA: %s] [PRESENTATION: %s]"),
                *AuthorityDetail, *PresentationDetail);
            return false;
        }
        OutDetail = TEXT("DATA AND PRESENTATION ROLLED BACK");
        return true;
    }
}

FString ULBOneFactorySaveSubsystem::GetIsolatedSlotName()
{
    return TEXT("LB_ONE_FACTORY_ISOLATED_SAVE_V001");
}

int32 ULBOneFactorySaveSubsystem::GetIsolatedUserIndex()
{
    return 0;
}

bool ULBOneFactorySaveSubsystem::DoesOneFactorySaveExist() const
{
    return UGameplayStatics::DoesSaveGameExist(
        GetIsolatedSlotName(), GetIsolatedUserIndex());
}

bool ULBOneFactorySaveSubsystem::CaptureCurrentFactory(
    FLBOneFactorySaveState& OutState, FString& OutReason) const
{
    using namespace LBOneFactorySaveSubsystemPrivate;
    FFactoryActors Actors;
    if (!DiscoverFactory(GetWorld(), Actors, OutReason)
        || !ValidateActorIdentity(Actors, OutReason))
    {
        return false;
    }
    if (!CaptureAuthorities(Actors, OutState, OutReason))
    {
        return false;
    }
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(GetWorld(), Production, Coordinator, OutReason)
        || Production != Actors.ProductionAuthority
        || !Coordinator->ValidateRuntimeFactory(OutReason))
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT(
                "ONEFACTORY CAPTURE RUNTIME BACKBONE OR 57-STATION TOPOLOGY FAILED");
        return false;
    }
    if (ULBFactoryManagementSubsystem* Management =
            GetWorld()->GetSubsystem<ULBFactoryManagementSubsystem>())
    {
        OutState.Management = Management->CaptureSaveState();
        OutState.bHasManagementState = true;
    }
    OutReason = TEXT("ONEFACTORY CAPTURE VALID; PRESENTATION PROXIES EXCLUDED");
    return true;
}

void ULBOneFactorySaveSubsystem::RestoreManagementState(
    const FLBOneFactorySaveState& State) const
{
    // Money is auxiliary to the factory restore: a missing or invalid
    // management payload never fails the transaction, because the economy
    // bridge re-initialises a fresh campaign idempotently on the next tick.
    if (!State.bHasManagementState)
    {
        return;
    }
    UWorld* World = GetWorld();
    ULBFactoryManagementSubsystem* Management =
        World ? World->GetSubsystem<ULBFactoryManagementSubsystem>() : nullptr;
    FString Ignored;
    if (Management
        && ULBFactoryManagementSubsystem::ValidateSaveState(State.Management,
            Ignored))
    {
        Management->RestoreSaveState(State.Management);
    }
}

bool ULBOneFactorySaveSubsystem::RestoreFactoryState(
    const FLBOneFactorySaveState& State, FString& OutReason)
{
    using namespace LBOneFactorySaveSubsystemPrivate;
    if (!ULBOneFactorySaveGame::ValidateState(State, OutReason))
    {
        return false;
    }
    if (!PreflightPresentations(State, OutReason))
    {
        OutReason = FString(TEXT("ONEFACTORY PRESENTATION PREFLIGHT FAILED: "))
            + OutReason;
        return false;
    }

    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("ONEFACTORY RESTORE HAS NO WORLD");
        return false;
    }

    const FStarterActorCounts Counts = CountStarterActors(World);
    if (Counts.Total() == 0)
    {
        ALBOneFactoryProductionFlowAuthority* Production = nullptr;
        ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
        if (!FindRuntimeBackbone(World, Production, Coordinator, OutReason))
        {
            if (OutReason.IsEmpty())
                OutReason = TEXT(
                    "ONEFACTORY FRESH RESTORE RUNTIME BACKBONE IDENTITY FAILED");
            return false;
        }
        const FLBOneFactoryProductionLedgerState LedgerBefore =
            Production->CaptureLedger();
        if (!ValidateFreshLedger(LedgerBefore, OutReason)) return false;

        ULBOneFactoryPlayerBuilderSubsystem* Builder =
            World->GetSubsystem<ULBOneFactoryPlayerBuilderSubsystem>();
        if (!Builder || !Builder->IsOneFactoryBuilderWorld())
        {
            OutReason = TEXT(
                "ONEFACTORY FRESH RESTORE REQUIRES THE PLAYER-BUILDER SHELL");
            return false;
        }
        TArray<AActor*> CreatedActors;
        if (!Builder->MaterialiseFactoryForRestore(
                State, CreatedActors, OutReason))
            return false;

        FFactoryActors Actors;
        FString ApplyFailure;
        bool bApplied = DiscoverFactory(World, Actors, ApplyFailure)
            && ValidateActorIdentity(Actors, ApplyFailure)
            && Actors.ProductionAuthority == Production
            && Production->RestoreLedger(State.ProductionLedger, ApplyFailure);
#if WITH_DEV_AUTOMATION_TESTS
        if (bApplied && bForcePresentationFailureForTests)
        {
            bApplied = false;
            ApplyFailure = TEXT(
                "FORCED FRESH-SHELL POST-MATERIALISATION FAILURE FOR TEST");
        }
#endif
        if (bApplied)
            bApplied = ValidatePresentationPairing(
                Actors, State, ApplyFailure)
                && Coordinator->ValidateRuntimeFactory(ApplyFailure);
        if (!bApplied)
        {
            FString LedgerRollbackReason;
            const bool bLedgerRolledBack = Production->RestoreLedger(
                LedgerBefore, LedgerRollbackReason);
            DestroyCreatedActors(CreatedActors);
            OutReason = FString::Printf(TEXT(
                "ONEFACTORY FRESH RESTORE ROLLED BACK [%s]; LEDGER %s; NEW ACTORS DESTROYED"),
                *ApplyFailure,
                bLedgerRolledBack ? TEXT("RESTORED")
                    : *LedgerRollbackReason);
            return false;
        }

        RestoreManagementState(State);
        OutReason = TEXT(
            "ONEFACTORY FRESH RESTORE COMMITTED; FOUR DATA/PRESENTATION PAIRS MATERIALISED AND 57-STATION RUNTIME VALIDATED");
        return true;
    }

    if (!Counts.IsComplete())
    {
        OutReason = FString::Printf(TEXT(
            "ONEFACTORY RESTORE REJECTED A PARTIAL STARTER SET (%d OF 8 ACTORS); LIVE WORLD UNCHANGED"),
            Counts.Total());
        return false;
    }

    FFactoryActors Actors;
    if (!DiscoverFactory(World, Actors, OutReason)
        || !ValidateActorIdentity(Actors, OutReason))
        return false;
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    if (!FindRuntimeBackbone(World, Production, Coordinator, OutReason)
        || Production != Actors.ProductionAuthority)
    {
        if (OutReason.IsEmpty())
            OutReason = TEXT(
                "ONEFACTORY POPULATED RESTORE RUNTIME BACKBONE IDENTITY FAILED");
        return false;
    }
    if (!Coordinator->ValidateRuntimeFactory(OutReason))
    {
        OutReason = FString(
            TEXT("ONEFACTORY CURRENT RUNTIME CANNOT FORM ROLLBACK: "))
            + OutReason;
        return false;
    }

    FLBOneFactorySaveState RollbackState;
    if (!CaptureAuthorities(Actors, RollbackState, OutReason))
    {
        OutReason = FString(
            TEXT("ONEFACTORY CURRENT STATE CANNOT FORM ROLLBACK: "))
            + OutReason;
        return false;
    }

    FString ApplyFailure;
    bool bApplied = RestoreAuthorities(Actors, State, ApplyFailure);
#if WITH_DEV_AUTOMATION_TESTS
    if (bApplied && bForcePresentationFailureForTests)
    {
        bApplied = false;
        ApplyFailure = TEXT("FORCED POST-DATA PRESENTATION FAILURE FOR TEST");
    }
#endif
    if (bApplied)
    {
        bApplied = RebuildPresentations(Actors, State, ApplyFailure);
    }
    if (bApplied)
        bApplied = Coordinator->ValidateRuntimeFactory(ApplyFailure);
    if (!bApplied)
    {
        FString RollbackDetail;
        Rollback(Actors, RollbackState, RollbackDetail);
        OutReason = FString::Printf(
            TEXT("ONEFACTORY RESTORE FAILED [%s]; %s"), *ApplyFailure,
            *RollbackDetail);
        return false;
    }

    RestoreManagementState(State);
    OutReason = TEXT(
        "ONEFACTORY RESTORE COMMITTED; FOUR PRESENTATION PAIRS REBUILT");
    return true;
}

bool ULBOneFactorySaveSubsystem::SaveOneFactory(FString& OutReason)
{
    FLBOneFactorySaveState State;
    if (!CaptureCurrentFactory(State, OutReason))
    {
        return false;
    }

    ULBOneFactorySaveGame* SaveRoot = Cast<ULBOneFactorySaveGame>(
        UGameplayStatics::CreateSaveGameObject(ULBOneFactorySaveGame::StaticClass()));
    if (!SaveRoot)
    {
        OutReason = TEXT("ONEFACTORY COULD NOT CREATE ITS ISOLATED SAVE ROOT");
        return false;
    }
    SaveRoot->FactoryState = MoveTemp(State);
    if (!UGameplayStatics::SaveGameToSlot(SaveRoot,
            GetIsolatedSlotName(), GetIsolatedUserIndex()))
    {
        OutReason = TEXT("ONEFACTORY ISOLATED SLOT WRITE FAILED");
        return false;
    }
    OutReason = TEXT("ONEFACTORY ISOLATED SLOT SAVED");
    return true;
}

bool ULBOneFactorySaveSubsystem::LoadOneFactory(FString& OutReason)
{
    if (!DoesOneFactorySaveExist())
    {
        OutReason = TEXT("ONEFACTORY ISOLATED SAVE SLOT DOES NOT EXIST");
        return false;
    }
    ULBOneFactorySaveGame* SaveRoot = Cast<ULBOneFactorySaveGame>(
        UGameplayStatics::LoadGameFromSlot(
            GetIsolatedSlotName(), GetIsolatedUserIndex()));
    if (!SaveRoot)
    {
        OutReason = TEXT("ONEFACTORY ISOLATED SLOT HAS THE WRONG SAVE TYPE");
        return false;
    }
    if (!ULBOneFactorySaveGame::ValidateState(SaveRoot->FactoryState, OutReason))
    {
        OutReason = FString(TEXT("ONEFACTORY ISOLATED SLOT REJECTED: "))
            + OutReason;
        return false;
    }
    return RestoreFactoryState(SaveRoot->FactoryState, OutReason);
}
