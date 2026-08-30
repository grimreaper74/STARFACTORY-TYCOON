#include "LBOneFactoryPressToolingSupportActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace LBOneFactoryPressToolingPrivate
{
    const FLBOneFactoryPressStarterStationState* FindPressTrain(
        const FLBOneFactoryPressStarterLayoutState& Layout)
    {
        return Layout.Stations.FindByPredicate([](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.Role ==
                ELBOneFactoryPressStarterRole::ConfigurablePressTrain;
        });
    }

    // Same datum as the retained press visual; using it here puts the tooling
    // on the service side of the actual rendered train rather than its abstract
    // logical footprint.
    const FTransform AggregateDatum(FQuat::Identity,
        FVector(9.25f, 2367.5f, 0.0f), FVector(100.0f));
}

ALBOneFactoryPressToolingSupportActor::ALBOneFactoryPressToolingSupportActor()
{
    PrimaryActorTick.bCanEverTick = true;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    RackFrames = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("DieStorageRacks"));
    StoredDies = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("StoredDieSets"));
    SafetyRoute = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("DieChangeSafetyRoute"));
    BolsterInterfaces = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("PressBolsterInterfaces"));
    DieChangeStaging = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("DieChangeStagingPads"));
    DieChangeCart = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("DieChangeCart"));
    for (UStaticMeshComponent* Component :
        {static_cast<UStaticMeshComponent*>(RackFrames.Get()),
         static_cast<UStaticMeshComponent*>(StoredDies.Get()),
         static_cast<UStaticMeshComponent*>(SafetyRoute.Get()), DieChangeCart.Get()})
    {
        Component->SetupAttachment(SceneRoot);
        ConfigureStaticVisual(Component);
    }
    for (int32 Index = 0; Index < 5; ++Index)
    {
        UTextRenderComponent* Label = CreateDefaultSubobject<UTextRenderComponent>(
            *FString::Printf(TEXT("DieBayLabel_S%02d"), Index + 2));
        Label->SetupAttachment(SceneRoot);
        Label->SetHorizontalAlignment(EHTA_Center);
        Label->SetVerticalAlignment(EVRTA_TextCenter);
        Label->SetWorldSize(42.0f);
        Label->SetTextRenderColor(FColor(245, 245, 235));
        Label->SetVisibility(false, true);
        Label->SetHiddenInGame(true, true);
        DieBayLabels.Add(Label);
    }
    for (UInstancedStaticMeshComponent* Component :
        {BolsterInterfaces.Get(), DieChangeStaging.Get()})
    {
        Component->SetupAttachment(SceneRoot);
        ConfigureStaticVisual(Component);
    }

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(
        TEXT("/Engine/BasicShapes/Cube.Cube"));
    NativeCube = CubeFinder.Succeeded() ? CubeFinder.Object : nullptr;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> StructureFinder(
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v086.M_CA_MW_PR009_LayeredCairnwellGreen_v086"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SteelFinder(
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_MachinedSteel_v086.M_CA_MW_PR009_MachinedSteel_v086"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SafetyFinder(
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v086.M_CA_MW_PR009_LayeredSafetyYellow_v086"));
    StructureMaterial = StructureFinder.Succeeded() ? StructureFinder.Object : nullptr;
    SteelMaterial = SteelFinder.Succeeded() ? SteelFinder.Object : nullptr;
    SafetyMaterial = SafetyFinder.Succeeded() ? SafetyFinder.Object : nullptr;
    Tags.AddUnique(GetToolingTag());
    Tags.AddUnique(TEXT("LB.Provenance.NativeCode"));
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    SetActorHiddenInGame(true);
}

void ALBOneFactoryPressToolingSupportActor::ConfigureStaticVisual(
    UStaticMeshComponent* Component)
{
    if (!Component) return;
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
    Component->SetVisibility(false, true);
    Component->SetHiddenInGame(true, true);
}

bool ALBOneFactoryPressToolingSupportActor::ConfigureFromPressLayout(
    const FLBOneFactoryPressStarterLayoutState& Layout, FString& OutReason)
{
    OutReason.Reset();
    const FLBOneFactoryPressStarterStationState* PressTrain =
        LBOneFactoryPressToolingPrivate::FindPressTrain(Layout);
    if (!NativeCube || !PressTrain)
    {
        OutReason = TEXT("PRESS TOOLING SUPPORT REQUIRES A NATIVE CUBE AND A PRESS-TRAIN ANCHOR");
        return false;
    }

    const FTransform Aggregate = LBOneFactoryPressToolingPrivate::AggregateDatum
        * PressTrain->WorldTransform;
    // Store is beyond the service-side rail, clear of S02-S06 tool openings.
    SetActorLocation(Aggregate.TransformPosition(FVector(39.0f, 52.5f, 0.0f)));
    SetActorRotation(Aggregate.GetRotation());

    RackFrames->ClearInstances();
    StoredDies->ClearInstances();
    SafetyRoute->ClearInstances();
    BolsterInterfaces->ClearInstances();
    DieChangeStaging->ClearInstances();
    for (UInstancedStaticMeshComponent* Component :
        {RackFrames.Get(), StoredDies.Get(), SafetyRoute.Get(),
         BolsterInterfaces.Get(), DieChangeStaging.Get()})
    {
        Component->SetStaticMesh(NativeCube);
    }
    DieChangeCart->SetStaticMesh(NativeCube);
    RackFrames->SetMaterial(0, StructureMaterial);
    StoredDies->SetMaterial(0, SteelMaterial);
    SafetyRoute->SetMaterial(0, SafetyMaterial);
    BolsterInterfaces->SetMaterial(0, SteelMaterial);
    DieChangeStaging->SetMaterial(0, SafetyMaterial);
    DieChangeCart->SetMaterial(0, StructureMaterial);

    // Five labelled tool positions: one for each S02-S06 die family.  Frames
    // are separate from the die blocks so later authored assets replace either
    // side without changing the cart, access or programme contracts.
    for (int32 Index = 0; Index < 5; ++Index)
    {
        const float X = -900.0f + Index * 450.0f;
        RackFrames->AddInstance(FTransform(FQuat::Identity, FVector(X, 0.0f, 250.0f),
            FVector(3.70f, 3.00f, 5.00f)));
        RackFrames->AddInstance(FTransform(FQuat::Identity, FVector(X, -250.0f, 590.0f),
            FVector(3.70f, 0.18f, 0.18f)));
        StoredDies->AddInstance(FTransform(FQuat::Identity, FVector(X, 0.0f, 130.0f),
            FVector(2.70f, 2.20f, 1.15f)));
        if (DieBayLabels.IsValidIndex(Index) && DieBayLabels[Index])
        {
            UTextRenderComponent* Label = DieBayLabels[Index];
            Label->SetText(FText::FromString(FString::Printf(
                TEXT("DIE BAY S%02d"), Index + 2)));
            Label->SetRelativeLocation(FVector(X, -360.0f, 700.0f));
            Label->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
            Label->SetVisibility(true, true);
            Label->SetHiddenInGame(false, true);
        }
    }
    // A clear, visible guarded corridor is more valuable than a fake dense rack.
    SafetyRoute->AddInstance(FTransform(FQuat::Identity, FVector(0.0f, -560.0f, 5.0f),
        FVector(15.0f, 0.24f, 0.05f)));
    SafetyRoute->AddInstance(FTransform(FQuat::Identity, FVector(0.0f, 560.0f, 5.0f),
        FVector(15.0f, 0.24f, 0.05f)));

    // Five protected changeover positions at the real S02-S06 press centres.
    // The train is authored in metres while primitive components use cm.
    constexpr float ServiceSideRelativeY = -980.0f;
    constexpr float StagingRelativeY = -650.0f;
    constexpr float StationXMetres[] = {23.5f, 31.0f, 38.5f, 46.0f, 53.5f};
    for (const float StationX : StationXMetres)
    {
        const float RelativeX = (StationX - 39.0f) * 100.0f;
        BolsterInterfaces->AddInstance(FTransform(FQuat::Identity,
            FVector(RelativeX, ServiceSideRelativeY, 42.0f),
            FVector(3.70f, 3.10f, 0.42f)));
        DieChangeStaging->AddInstance(FTransform(FQuat::Identity,
            FVector(RelativeX, StagingRelativeY, 3.0f),
            FVector(4.35f, 3.55f, 0.03f)));
    }
    DieChangeCart->SetRelativeTransform(FTransform(FQuat::Identity, FVector(0.0f, -900.0f, 95.0f),
        FVector(3.30f, 2.30f, 0.95f)));
    CartRestTransform = DieChangeCart->GetRelativeTransform();
    StoredDieSetCount = 5;
    bConfigured = true;
    SetActorHiddenInGame(false);
    for (UStaticMeshComponent* Component :
        {static_cast<UStaticMeshComponent*>(RackFrames.Get()),
         static_cast<UStaticMeshComponent*>(StoredDies.Get()),
         static_cast<UStaticMeshComponent*>(SafetyRoute.Get()),
         static_cast<UStaticMeshComponent*>(BolsterInterfaces.Get()),
         static_cast<UStaticMeshComponent*>(DieChangeStaging.Get()), DieChangeCart.Get()})
    {
        Component->SetVisibility(true, true);
        Component->SetHiddenInGame(false, true);
    }
    OutReason = TEXT("NATIVE PRESS TOOLING STORE ACTIVE: FIVE DIE SETS, MOVABLE CART, GUARDED SERVICE ROUTE");
    return true;
}

void ALBOneFactoryPressToolingSupportActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bConfigured || !DieChangeCart) return;
    const float Time = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
    FTransform CartTransform = CartRestTransform;
    // Demonstration/idle loop: 3.5 m of the supplied die-cart travel envelope.
    CartTransform.AddToTranslation(FVector(FMath::Sin(Time * 0.18f) * 175.0f,
        0.0f, 0.0f));
    DieChangeCart->SetRelativeTransform(CartTransform,
        false, nullptr, ETeleportType::TeleportPhysics);
}

FName ALBOneFactoryPressToolingSupportActor::GetToolingTag()
{
    return FName(TEXT("LB.OneFactory.PressTooling.Native"));
}
