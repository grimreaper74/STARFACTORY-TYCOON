#include "LBOneFactoryBootstrap.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/Level.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBPressShopBuildAuthority.h"
#include "Materials/MaterialInterface.h"

DEFINE_LOG_CATEGORY_STATIC(LogLineBossOneFactory, Log, All);

namespace LBOneFactoryBootstrapPrivate
{
    bool ContainsForbiddenPresentationToken(const FString& Value)
    {
        // RETIRED 2026-08-24 (spacecraft pivot): the generator-name ban
        // ("Meshy"/"ExternalGenerated" substrings) is lifted - generated
        // assets are judged by their recorded provenance, not their name.
        // See SPACECRAFT_PIVOT_AUTHORITY_v001.md and the reversal plan.
        (void)Value;
        return false;
    }

    bool HasTagPrefix(const AActor& Actor, const TCHAR* Prefix)
    {
        for (const FName Tag : Actor.Tags)
        {
            if (Tag.ToString().StartsWith(Prefix, ESearchCase::IgnoreCase)) return true;
        }
        return false;
    }

    bool HasExactTag(const AActor& Actor, const TCHAR* TagText)
    {
        for (const FName Tag : Actor.Tags)
        {
            if (Tag.ToString().Equals(TagText, ESearchCase::IgnoreCase)) return true;
        }
        return false;
    }
}

FName ALBOneFactoryBootstrap::GetBootstrapAuthorityTag()
{
    static const FName Tag(TEXT("LB.OneFactory.Bootstrap.v001"));
    return Tag;
}

FName ALBOneFactoryBootstrap::GetNativeOnlyTag()
{
    static const FName Tag(TEXT("LB.Provenance.NativeOnly"));
    return Tag;
}

FName ALBOneFactoryBootstrap::GetPressBuildAuthorityTag()
{
    static const FName Tag(TEXT("LB.OneFactory.MapAuthored.PressBuildAuthority.v001"));
    return Tag;
}

ALBOneFactoryBootstrap::ALBOneFactoryBootstrap()
{
    PrimaryActorTick.bCanEverTick = false;
    SetActorEnableCollision(false);
    SetReplicates(false);
    ShellLayout = ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
    Tags.AddUnique(GetBootstrapAuthorityTag());
    Tags.AddUnique(GetNativeOnlyTag());
}

void ALBOneFactoryBootstrap::BeginPlay()
{
    Super::BeginPlay();
    FString Reason;
    if (!ValidateAndLockShell(Reason))
    {
        UE_LOG(LogLineBossOneFactory, Error,
            TEXT("LINE_BOSS_ONEFACTORY_BOOTSTRAP_REJECTED reason=%s"), *Reason);
        return;
    }
    UE_LOG(LogLineBossOneFactory, Display,
        TEXT("LINE_BOSS_ONEFACTORY_BOOTSTRAP_READY layout=%s factory=\"%s\""),
        *ShellLayout.LayoutId.ToString(), *ShellLayout.FactoryDisplayName);
}

bool ALBOneFactoryBootstrap::ActorHasWIPIdentity(const AActor& Actor)
{
    return LBOneFactoryBootstrapPrivate::HasTagPrefix(Actor, TEXT("LB.WIP"))
        || LBOneFactoryBootstrapPrivate::HasTagPrefix(Actor, TEXT("LB.Inventory"))
        || LBOneFactoryBootstrapPrivate::HasTagPrefix(Actor, TEXT("LB.Material.Unit"))
        || LBOneFactoryBootstrapPrivate::HasExactTag(Actor, TEXT("ProcessWIP"));
}

bool ALBOneFactoryBootstrap::ActorIsForbiddenLegacyFixture(const AActor& Actor)
{
    for (const UClass* Class = Actor.GetClass(); Class; Class = Class->GetSuperClass())
    {
        if (ULBOneFactoryLayoutLibrary::IsForbiddenLegacyActorClassName(Class->GetName()))
        {
            return true;
        }
    }
    if (LBOneFactoryBootstrapPrivate::HasTagPrefix(Actor, TEXT("LB.Legacy"))
        || LBOneFactoryBootstrapPrivate::HasTagPrefix(Actor, TEXT("LB.VisualQA"))
        || LBOneFactoryBootstrapPrivate::HasTagPrefix(Actor, TEXT("LB.Visual.QA"))
        || LBOneFactoryBootstrapPrivate::HasTagPrefix(Actor, TEXT("LB.Vehicle.CoilAGV"))
        || LBOneFactoryBootstrapPrivate::HasTagPrefix(Actor, TEXT("LB.Inbound.Visual.Lorry"))
        || LBOneFactoryBootstrapPrivate::HasTagPrefix(Actor,
            TEXT("LB.CleanPlayerBuilt.StarterSupportFleet"))
        || LBOneFactoryBootstrapPrivate::HasTagPrefix(Actor,
            TEXT("LB.FactoryEnvelope.Shutter"))
        || LBOneFactoryBootstrapPrivate::HasExactTag(Actor,
            TEXT("LB.Environment.FallbackFloor"))
        || LBOneFactoryBootstrapPrivate::HasExactTag(Actor, TEXT("LB.FallbackFloor")))
    {
        return true;
    }

    const FString ActorIdentity = Actor.GetName() + TEXT(" ") + Actor.GetActorNameOrLabel();
    return ActorIdentity.Contains(TEXT("FallbackFloor"), ESearchCase::IgnoreCase)
        || ActorIdentity.Contains(TEXT("VisualQA"), ESearchCase::IgnoreCase)
        || ActorIdentity.Contains(TEXT("Lorry"), ESearchCase::IgnoreCase);
}

bool ALBOneFactoryBootstrap::ActorUsesForbiddenProvenance(const AActor& Actor,
    FString& OutReference)
{
    OutReference.Reset();
    if (LBOneFactoryBootstrapPrivate::ContainsForbiddenPresentationToken(Actor.GetName())
        || LBOneFactoryBootstrapPrivate::ContainsForbiddenPresentationToken(
            Actor.GetActorNameOrLabel()))
    {
        OutReference = Actor.GetPathName();
        return true;
    }
    for (const FName Tag : Actor.Tags)
    {
        if (LBOneFactoryBootstrapPrivate::ContainsForbiddenPresentationToken(Tag.ToString()))
        {
            OutReference = Tag.ToString();
            return true;
        }
    }

    TInlineComponentArray<UStaticMeshComponent*> MeshComponents;
    const_cast<AActor&>(Actor).GetComponents(MeshComponents);
    for (const UStaticMeshComponent* Component : MeshComponents)
    {
        if (!IsValid(Component)) continue;
        if (const UStaticMesh* Mesh = Component->GetStaticMesh())
        {
            if (LBOneFactoryBootstrapPrivate::ContainsForbiddenPresentationToken(
                Mesh->GetPathName()))
            {
                OutReference = Mesh->GetPathName();
                return true;
            }
        }
        for (int32 MaterialIndex = 0; MaterialIndex < Component->GetNumMaterials();
            ++MaterialIndex)
        {
            const UMaterialInterface* Material = Component->GetMaterial(MaterialIndex);
            if (Material && LBOneFactoryBootstrapPrivate::ContainsForbiddenPresentationToken(
                Material->GetPathName()))
            {
                OutReference = Material->GetPathName();
                return true;
            }
        }
    }
    return false;
}

FLBOneFactoryWorldAudit ALBOneFactoryBootstrap::AuditWorld(UWorld* World)
{
    FLBOneFactoryWorldAudit Audit;
    if (!World)
    {
        Audit.bProtectedMapPackage = true;
        return Audit;
    }

    TArray<ALBOneFactoryBootstrap*> Bootstraps;
    TArray<ALBPressShopBuildAuthority*> Authorities;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!IsValid(Actor) || Actor->IsActorBeingDestroyed()) continue;
        if (ALBOneFactoryBootstrap* Bootstrap = Cast<ALBOneFactoryBootstrap>(Actor))
        {
            Bootstraps.Add(Bootstrap);
            continue;
        }
        if (ALBPressShopBuildAuthority* Authority =
            Cast<ALBPressShopBuildAuthority>(Actor))
        {
            Authorities.Add(Authority);
            continue;
        }

        bool bProductionClass = false;
        for (const UClass* Class = Actor->GetClass(); Class; Class = Class->GetSuperClass())
        {
            if (ULBOneFactoryLayoutLibrary::IsMapOwnedProductionActorClassName(
                Class->GetName()))
            {
                bProductionClass = true;
                break;
            }
        }
        if (bProductionClass)
        {
            ++Audit.MapOwnedProductionActorCount;
        }
        if (ActorHasWIPIdentity(*Actor)) ++Audit.MapOwnedWIPActorCount;
        if (ActorIsForbiddenLegacyFixture(*Actor)) ++Audit.ForbiddenLegacyActorCount;
        FString ForbiddenReference;
        if (ActorUsesForbiddenProvenance(*Actor, ForbiddenReference))
        {
            ++Audit.ForbiddenProvenanceActorCount;
            UE_LOG(LogTemp, Warning,
                TEXT("ONEFACTORY FORBIDDEN PROVENANCE: %s (%s)"),
                *Actor->GetActorNameOrLabel(), *ForbiddenReference);
        }
    }

    Audit.BootstrapCount = Bootstraps.Num();
    Audit.PressBuildAuthorityCount = Authorities.Num();
    if (Bootstraps.Num() == 1)
    {
        Audit.bBootstrapUnowned = Bootstraps[0]->GetOwner() == nullptr
            && Bootstraps[0]->GetAttachParentActor() == nullptr;
    }
    if (Authorities.Num() == 1)
    {
        Audit.bPressBuildAuthorityUnowned = Authorities[0]->GetOwner() == nullptr
            && Authorities[0]->GetAttachParentActor() == nullptr;
        Audit.bPressBuildAuthorityMapTagged =
            Authorities[0]->ActorHasTag(GetPressBuildAuthorityTag())
            && Authorities[0]->ActorHasTag(GetNativeOnlyTag());
    }
    if (Bootstraps.Num() == 1 && Authorities.Num() == 1)
    {
        Audit.bBootstrapAndAuthorityShareLevel =
            Bootstraps[0]->GetLevel() == Authorities[0]->GetLevel();
    }

    FString PackageName = World->GetOutermost()->GetName();
    if (World->PersistentLevel)
    {
        PackageName = World->PersistentLevel->GetOutermost()->GetName();
    }
    Audit.bProtectedMapPackage =
        ULBOneFactoryLayoutLibrary::IsProtectedMapPackageName(PackageName);
    return Audit;
}

bool ALBOneFactoryBootstrap::ValidateAndLockShell(FString& OutReason)
{
    if (bValidationAttempted)
    {
        OutReason = BootstrapStatus;
        return BootstrapState == ELBOneFactoryBootstrapState::Ready;
    }

    bValidationAttempted = true;
    BootstrapState = ELBOneFactoryBootstrapState::Validating;
    PressBuildAuthority.Reset();
    const auto Reject = [this, &OutReason](const FString& Reason)
    {
        BootstrapState = ELBOneFactoryBootstrapState::Rejected;
        BootstrapStatus = Reason.IsEmpty()
            ? TEXT("ONEFACTORY SHELL VALIDATION FAILED CLOSED") : Reason;
        OutReason = BootstrapStatus;
        return false;
    };

    UWorld* World = GetWorld();
    if (!World) return Reject(TEXT("ONEFACTORY BOOTSTRAP WORLD IS UNAVAILABLE"));
    if (GetClass() != ALBOneFactoryBootstrap::StaticClass())
    {
        return Reject(TEXT("ONEFACTORY REQUIRES THE EXACT NATIVE BOOTSTRAP CLASS"));
    }
    if (!GetActorTransform().Equals(FTransform::Identity, 0.001f))
    {
        return Reject(TEXT("ONEFACTORY BOOTSTRAP MUST REMAIN AT WORLD IDENTITY"));
    }
    if (!ActorHasTag(GetBootstrapAuthorityTag()) || !ActorHasTag(GetNativeOnlyTag()))
    {
        return Reject(TEXT("ONEFACTORY BOOTSTRAP AUTHORITY OR NATIVE-ONLY TAG IS MISSING"));
    }

    FString Reason;
    if (!ULBOneFactoryLayoutLibrary::ValidateMoorcrossWorksLayout(ShellLayout, Reason))
    {
        return Reject(Reason);
    }

    const FLBOneFactoryWorldAudit Audit = AuditWorld(World);
    if (!ULBOneFactoryLayoutLibrary::ValidateWorldAudit(Audit, Reason))
    {
        return Reject(Reason);
    }

    ALBPressShopBuildAuthority* Authority = nullptr;
    for (TActorIterator<ALBPressShopBuildAuthority> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed())
        {
            Authority = *It;
            break;
        }
    }
    if (!ULBOneFactoryLayoutLibrary::ValidatePressBuildAuthorityContract(
        ShellLayout, Authority, Reason))
    {
        return Reject(Reason);
    }

    PressBuildAuthority = Authority;
    BootstrapState = ELBOneFactoryBootstrapState::Ready;
    BootstrapStatus = TEXT("MOORCROSS WORKS ONEFACTORY NATIVE SHELL READY");
    OutReason = BootstrapStatus;
    return true;
}
