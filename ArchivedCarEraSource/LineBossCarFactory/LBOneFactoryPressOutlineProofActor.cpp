#include "LBOneFactoryPressOutlineProofActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace LBOneFactoryPressOutlineProofPrivate
{
    const TCHAR* const OutlineMaterialPath =
        TEXT("/Game/Fx/Material/M_Outline_Only.M_Outline_Only");
    const FName OutlineColourParameter(TEXT("Color1"));
    const FName OutlineThicknessParameter(TEXT("OutlineThickness"));
    constexpr int32 RequiredStencilCustomDepthMode = 3;
    constexpr int32 RequiredStencilValue = 1;
    constexpr float RequiredPriority = 2002.0f;

    const FLinearColor FoundryCharcoal = FLinearColor::FromSRGBColor(
        FColor(0x20, 0x24, 0x28, 0xff));

    bool HasNamedParameter(const TArray<FMaterialParameterInfo>& Parameters,
        const FName RequiredName)
    {
        return Parameters.ContainsByPredicate([RequiredName](
            const FMaterialParameterInfo& Parameter)
        {
            return Parameter.Name == RequiredName;
        });
    }
}

ALBOneFactoryPressOutlineProofActor::ALBOneFactoryPressOutlineProofActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetActorEnableCollision(false);
    SetReplicates(false);
    Tags.AddUnique(GetOutlineProofTag());
    Tags.AddUnique(TEXT("LB.Provenance.NativePressOutlineProofV001"));

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> OutlineFinder(
        LBOneFactoryPressOutlineProofPrivate::OutlineMaterialPath);
    OutlineMaterial = OutlineFinder.Succeeded() ? OutlineFinder.Object : nullptr;
}

void ALBOneFactoryPressOutlineProofActor::EndPlay(
    const EEndPlayReason::Type EndPlayReason)
{
    DisableOutlineProof();
    Super::EndPlay(EndPlayReason);
}

FName ALBOneFactoryPressOutlineProofActor::GetOutlineProofTag()
{
    return TEXT("LB.OneFactory.PressOutlineProof");
}

const TCHAR* ALBOneFactoryPressOutlineProofActor::GetOutlineProofClassPath()
{
    return TEXT("/Script/LineBossCarFactory.LBOneFactoryPressOutlineProofActor");
}

bool ALBOneFactoryPressOutlineProofActor::FindExactlyOneConfiguredPresentation(
    ALBOneFactoryPressStarterPresentationActor*& OutPresentation,
    FString& OutReason) const
{
    OutPresentation = nullptr;
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("PRESS OUTLINE PROOF HAS NO WORLD");
        return false;
    }

    int32 ConfiguredCount = 0;
    for (TActorIterator<ALBOneFactoryPressStarterPresentationActor> It(World);
        It; ++It)
    {
        ALBOneFactoryPressStarterPresentationActor* Candidate = *It;
        if (!IsValid(Candidate) || !Candidate->IsPresentationConfigured())
        {
            continue;
        }
        ++ConfiguredCount;
        OutPresentation = Candidate;
    }

    if (ConfiguredCount != 1 || !OutPresentation)
    {
        OutReason = FString::Printf(TEXT(
            "PRESS OUTLINE PROOF REQUIRES EXACTLY ONE CONFIGURED PRESS PRESENTATION; FOUND %d"),
            ConfiguredCount);
        OutPresentation = nullptr;
        return false;
    }

    return true;
}

bool ALBOneFactoryPressOutlineProofActor::ValidateOutlineMaterial(
    FString& OutReason) const
{
    using namespace LBOneFactoryPressOutlineProofPrivate;
    if (!OutlineMaterial || !OutlineMaterial->GetPathName().Equals(
            OutlineMaterialPath, ESearchCase::CaseSensitive))
    {
        OutReason = TEXT("PRESS OUTLINE PROOF OUTLINE MATERIAL DID NOT RESOLVE EXACTLY");
        return false;
    }

    const UMaterial* BaseMaterial = OutlineMaterial->GetMaterial();
    if (!BaseMaterial || BaseMaterial->MaterialDomain != MD_PostProcess)
    {
        OutReason = TEXT("PRESS OUTLINE PROOF MATERIAL IS NOT A POST-PROCESS MATERIAL");
        return false;
    }

    TArray<FMaterialParameterInfo> VectorParameters;
    TArray<FGuid> VectorParameterIds;
    OutlineMaterial->GetAllVectorParameterInfo(VectorParameters, VectorParameterIds);
    TArray<FMaterialParameterInfo> ScalarParameters;
    TArray<FGuid> ScalarParameterIds;
    OutlineMaterial->GetAllScalarParameterInfo(ScalarParameters, ScalarParameterIds);
    if (!HasNamedParameter(VectorParameters, OutlineColourParameter)
        || !HasNamedParameter(ScalarParameters, OutlineThicknessParameter))
    {
        OutReason = TEXT(
            "PRESS OUTLINE PROOF MATERIAL PARAMETER CONTRACT DRIFTED (Color1/OutlineThickness)");
        return false;
    }

    if (!FMath::IsFinite(OutlineThickness) || OutlineThickness <= 0.0f)
    {
        OutReason = TEXT("PRESS OUTLINE PROOF THICKNESS IS NOT A FINITE POSITIVE VALUE");
        return false;
    }

    return true;
}

bool ALBOneFactoryPressOutlineProofActor::SnapshotVisiblePressMeshes(
    ALBOneFactoryPressStarterPresentationActor& Presentation,
    TArray<FCustomDepthBackup>& OutBackups, FString& OutReason) const
{
    OutBackups.Reset();
    TInlineComponentArray<UStaticMeshComponent*> Components(&Presentation);
    for (UStaticMeshComponent* Component : Components)
    {
        // Only the actual configured, player-visible press geometry belongs to
        // this proof.  Hidden staging buffers and empty component shells must
        // not receive an accidental persistent render-state mutation.
        if (!IsValid(Component) || !Component->IsRegistered()
            || !Component->IsVisible() || Component->bHiddenInGame
            || !Component->ShouldRender()
            || !Component->GetStaticMesh())
        {
            continue;
        }

        FCustomDepthBackup& Backup = OutBackups.Emplace_GetRef();
        Backup.Component = Component;
        Backup.bRenderCustomDepth = Component->bRenderCustomDepth != 0;
        Backup.CustomDepthStencilValue = Component->CustomDepthStencilValue;
        Backup.CustomDepthStencilWriteMask =
            Component->CustomDepthStencilWriteMask;
    }

    if (OutBackups.IsEmpty())
    {
        OutReason = TEXT(
            "PRESS OUTLINE PROOF FOUND NO REGISTERED VISIBLE PRESS STATIC-MESH COMPONENTS");
        return false;
    }

    return true;
}

bool ALBOneFactoryPressOutlineProofActor::RequireStencilCustomDepth(
    FString& OutReason)
{
    using namespace LBOneFactoryPressOutlineProofPrivate;
    IConsoleVariable* CustomDepth = IConsoleManager::Get().FindConsoleVariable(
        TEXT("r.CustomDepth"));
    if (!CustomDepth)
    {
        OutReason = TEXT("PRESS OUTLINE PROOF COULD NOT FIND r.CustomDepth");
        return false;
    }

    PreviousCustomDepthMode = CustomDepth->GetInt();
    bHasPreviousCustomDepthMode = true;
    CustomDepth->Set(RequiredStencilCustomDepthMode, ECVF_SetByCode);
    if (CustomDepth->GetInt() != RequiredStencilCustomDepthMode)
    {
        CustomDepth->Set(PreviousCustomDepthMode, ECVF_SetByCode);
        bHasPreviousCustomDepthMode = false;
        OutReason = FString::Printf(TEXT(
            "PRESS OUTLINE PROOF REQUIRES r.CustomDepth=%d EXACTLY"),
            RequiredStencilCustomDepthMode);
        return false;
    }
    return true;
}

void ALBOneFactoryPressOutlineProofActor::RestoreStencilCustomDepth()
{
    if (!bHasPreviousCustomDepthMode)
    {
        return;
    }

    if (IConsoleVariable* CustomDepth = IConsoleManager::Get().FindConsoleVariable(
            TEXT("r.CustomDepth")))
    {
        CustomDepth->Set(PreviousCustomDepthMode, ECVF_SetByCode);
    }
    else
    {
        UE_LOG(LogTemp, Error, TEXT(
            "PRESS OUTLINE PROOF COULD NOT RESTORE r.CustomDepth=%d"),
            PreviousCustomDepthMode);
    }
    bHasPreviousCustomDepthMode = false;
}

void ALBOneFactoryPressOutlineProofActor::RestoreComponentBackups()
{
    for (const FCustomDepthBackup& Backup : ComponentBackups)
    {
        UStaticMeshComponent* Component = Backup.Component.Get();
        if (!IsValid(Component))
        {
            continue;
        }
        Component->SetRenderCustomDepth(Backup.bRenderCustomDepth);
        Component->SetCustomDepthStencilValue(Backup.CustomDepthStencilValue);
        Component->SetCustomDepthStencilWriteMask(
            Backup.CustomDepthStencilWriteMask);
    }
    ComponentBackups.Reset();
}

void ALBOneFactoryPressOutlineProofActor::DestroyOutlineVolume()
{
    if (IsValid(OutlinePostProcessVolume))
    {
        OutlinePostProcessVolume->Destroy();
    }
    OutlinePostProcessVolume = nullptr;
    OutlineMaterialInstance = nullptr;
}

bool ALBOneFactoryPressOutlineProofActor::EnableOutlineProof(FString& OutReason)
{
    using namespace LBOneFactoryPressOutlineProofPrivate;
    OutReason.Reset();
    if (bOutlineProofEnabled)
    {
        if (IsValid(OutlinePostProcessVolume)
            && ConfiguredPresentation.IsValid() && !ComponentBackups.IsEmpty())
        {
            OutReason = TEXT("PRESS OUTLINE PROOF IS ALREADY ACTIVE");
            return true;
        }
        // A destroyed transient helper must not leave the actor claiming a
        // valid proof.  Clean up its snapshots before accepting another try.
        DisableOutlineProof();
    }

    ALBOneFactoryPressStarterPresentationActor* Presentation = nullptr;
    if (!FindExactlyOneConfiguredPresentation(Presentation, OutReason)
        || !ValidateOutlineMaterial(OutReason))
    {
        UE_LOG(LogTemp, Error, TEXT("%s"), *OutReason);
        return false;
    }

    TArray<FCustomDepthBackup> PendingBackups;
    if (!SnapshotVisiblePressMeshes(*Presentation, PendingBackups, OutReason))
    {
        UE_LOG(LogTemp, Error, TEXT("%s"), *OutReason);
        return false;
    }

    UMaterialInstanceDynamic* NewMaterialInstance =
        UMaterialInstanceDynamic::Create(OutlineMaterial, this);
    if (!NewMaterialInstance)
    {
        OutReason = TEXT("PRESS OUTLINE PROOF COULD NOT CREATE ITS DYNAMIC MATERIAL");
        UE_LOG(LogTemp, Error, TEXT("%s"), *OutReason);
        return false;
    }
    NewMaterialInstance->SetFlags(RF_Transient);
    NewMaterialInstance->SetVectorParameterValue(OutlineColourParameter,
        FoundryCharcoal);
    NewMaterialInstance->SetScalarParameterValue(OutlineThicknessParameter,
        OutlineThickness);

    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("PRESS OUTLINE PROOF LOST ITS WORLD DURING PREFLIGHT");
        UE_LOG(LogTemp, Error, TEXT("%s"), *OutReason);
        return false;
    }

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.Owner = this;
    SpawnParameters.ObjectFlags |= RF_Transient;
    SpawnParameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    APostProcessVolume* NewVolume = World->SpawnActor<APostProcessVolume>(
        APostProcessVolume::StaticClass(), FVector::ZeroVector,
        FRotator::ZeroRotator, SpawnParameters);
    if (!NewVolume)
    {
        OutReason = TEXT("PRESS OUTLINE PROOF COULD NOT SPAWN ITS TRANSIENT POST-PROCESS VOLUME");
        UE_LOG(LogTemp, Error, TEXT("%s"), *OutReason);
        return false;
    }
    NewVolume->SetActorEnableCollision(false);
    NewVolume->Tags.AddUnique(GetOutlineProofTag());
    NewVolume->Tags.AddUnique(TEXT("LB.RuntimeOnly"));
    NewVolume->bEnabled = true;
    NewVolume->bUnbound = true;
    NewVolume->Priority = RequiredPriority;
    NewVolume->BlendWeight = 1.0f;
    NewVolume->Settings.AddBlendable(NewMaterialInstance, 1.0f);

    // All non-render-state setup has succeeded before any shared setting is
    // touched.  A CVar refusal therefore leaves only a transient actor to
    // destroy, never a partially outlined Press Shop.
    if (!RequireStencilCustomDepth(OutReason))
    {
        NewVolume->Destroy();
        UE_LOG(LogTemp, Error, TEXT("%s"), *OutReason);
        return false;
    }

    ComponentBackups = MoveTemp(PendingBackups);
    for (const FCustomDepthBackup& Backup : ComponentBackups)
    {
        UStaticMeshComponent* Component = Backup.Component.Get();
        if (!IsValid(Component))
        {
            // Components were preflighted in the same game-thread call.  If a
            // lifetime violation still appears, roll every prior mutation back.
            RestoreComponentBackups();
            RestoreStencilCustomDepth();
            NewVolume->Destroy();
            OutReason = TEXT("PRESS OUTLINE PROOF LOST A PRESS COMPONENT DURING ENABLE");
            UE_LOG(LogTemp, Error, TEXT("%s"), *OutReason);
            return false;
        }
        Component->SetRenderCustomDepth(true);
        Component->SetCustomDepthStencilValue(RequiredStencilValue);
        Component->SetCustomDepthStencilWriteMask(
            ERendererStencilMask::ERSM_Default);
    }

    ConfiguredPresentation = Presentation;
    OutlineMaterialInstance = NewMaterialInstance;
    OutlinePostProcessVolume = NewVolume;
    bOutlineProofEnabled = true;
    OutReason = FString::Printf(TEXT(
        "PRESS OUTLINE PROOF ACTIVE: %d VISIBLE PRESS MESH COMPONENTS, stencil %d, r.CustomDepth=%d, priority %.0f"),
        ComponentBackups.Num(), RequiredStencilValue,
        RequiredStencilCustomDepthMode, RequiredPriority);
    UE_LOG(LogTemp, Display, TEXT("%s"), *OutReason);
    return true;
}

void ALBOneFactoryPressOutlineProofActor::DisableOutlineProof()
{
    DestroyOutlineVolume();
    RestoreComponentBackups();
    RestoreStencilCustomDepth();
    ConfiguredPresentation.Reset();
    bOutlineProofEnabled = false;
}
