#include "LBPaintShopCellActor.h"

#include "Components/BoxComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "LBPaintShopPortComponent.h"
#include "Materials/MaterialInterface.h"

namespace LBPaintShopCellPrivate
{
    const TCHAR* TreatmentStartPath =
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v002/Modules/")
        TEXT("SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002.")
        TEXT("SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002");
    const TCHAR* TreatmentEndPath =
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v002/Modules/")
        TEXT("SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002.")
        TEXT("SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002");
    const TCHAR* LiquidSurfacePath =
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Process/")
        TEXT("SM_LB_EDLine_TreatmentLiquidSurface_Blockout_v001.")
        TEXT("SM_LB_EDLine_TreatmentLiquidSurface_Blockout_v001");
    const TCHAR* CarrierTrolleyPath =
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Carrier/")
        TEXT("SM_LB_EDLine_CarrierTrolley_Blockout_v001.")
        TEXT("SM_LB_EDLine_CarrierTrolley_Blockout_v001");
    const TCHAR* CarrierHoistPath =
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Carrier/")
        TEXT("SM_LB_EDLine_CarrierHoistCables_Blockout_v001.")
        TEXT("SM_LB_EDLine_CarrierHoistCables_Blockout_v001");
    const TCHAR* CarrierHangerPath =
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Carrier/")
        TEXT("SM_LB_EDLine_CarrierHanger_Blockout_v001.")
        TEXT("SM_LB_EDLine_CarrierHanger_Blockout_v001");
    const TCHAR* ProxyBIWPath =
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Validation/")
        TEXT("SM_LB_EDLine_ProxyBIW_Blockout_v001.")
        TEXT("SM_LB_EDLine_ProxyBIW_Blockout_v001");
    const TCHAR* EDCoatLiquidMaterialPath =
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/")
        TEXT("MI_LB_EDLine_Liquid_ED_Ecoat_v001.MI_LB_EDLine_Liquid_ED_Ecoat_v001");
    const TCHAR* ProfiledRailSegmentPath = TEXT("/Engine/BasicShapes/Cube.Cube");

    constexpr float BayLengthCm = 1800.0f;
    constexpr float ModulePitchCm = 900.0f;
    constexpr float DryBodyRootZCm = 430.0f;
    constexpr float RailHeightCm = 800.0f;
    constexpr float TreatmentLowRailHeightCm = 545.0f;
    constexpr float HangerRootZCm = 735.0f;
    constexpr float AuthoredHoistPivotZCm = 772.0f;
    constexpr float LiquidSurfaceZCm = 285.0f;
    constexpr float EmptyTankSurfaceZCm = 45.0f;
    constexpr float RailOffsetYCm = 300.0f;
    constexpr float TrackSampleSpacingCm = 75.0f;

    const FVector FootprintDimensionsCm(BayLengthCm, 1000.0f, 853.0f);
    // The imported halves overhang the nominal 18 m bay by up to 22.5 cm.
    // A 19 m envelope contains that geometry and a small end-service margin.
    const FVector ProtectedEnvelopeDimensionsCm(1900.0f, 1300.0f, 950.0f);

    void ConfigureCandidateMesh(UStaticMeshComponent* Component)
    {
        if (!Component) return;
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCollisionResponseToAllChannels(ECR_Ignore);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetCastShadow(true);
    }

    void ConfigureGeneratedRail(UHierarchicalInstancedStaticMeshComponent* Component)
    {
        if (!Component) return;
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCollisionResponseToAllChannels(ECR_Ignore);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetCastShadow(true);
    }

    bool IsVisualOnly(const UStaticMeshComponent* Component)
    {
        if (!Component || Component->GetCollisionEnabled() != ECollisionEnabled::NoCollision
            || Component->GetGenerateOverlapEvents() || Component->CanEverAffectNavigation())
        {
            return false;
        }
        for (int32 Channel = 0; Channel < ECollisionChannel::ECC_MAX; ++Channel)
        {
            if (Component->GetCollisionResponseToChannel(
                static_cast<ECollisionChannel>(Channel)) != ECR_Ignore)
            {
                return false;
            }
        }
        return true;
    }

    float Ease01(const float Alpha)
    {
        const float Clamped = FMath::Clamp(Alpha, 0.0f, 1.0f);
        return Clamped * Clamped * (3.0f - 2.0f * Clamped);
    }

    void EvaluateTrackPose(const float InLocalX, float& OutTrackZ, float& OutTrackSlope)
    {
        const float LocalX = FMath::Clamp(InLocalX, 0.0f, BayLengthCm);
        OutTrackZ = RailHeightCm;
        OutTrackSlope = 0.0f;
        constexpr float RampStartCm = 300.0f;
        constexpr float RampEndCm = 750.0f;
        constexpr float LowEndCm = 1050.0f;
        constexpr float RiseEndCm = 1500.0f;
        constexpr float RampLengthCm = RampEndCm - RampStartCm;
        const float HeightDelta = TreatmentLowRailHeightCm - RailHeightCm;

        if (LocalX > RampStartCm && LocalX < RampEndCm)
        {
            const float Alpha = (LocalX - RampStartCm) / RampLengthCm;
            OutTrackZ = FMath::Lerp(RailHeightCm, TreatmentLowRailHeightCm, Ease01(Alpha));
            OutTrackSlope = HeightDelta * (6.0f * Alpha * (1.0f - Alpha)) / RampLengthCm;
        }
        else if (LocalX >= RampEndCm && LocalX <= LowEndCm)
        {
            OutTrackZ = TreatmentLowRailHeightCm;
        }
        else if (LocalX > LowEndCm && LocalX < RiseEndCm)
        {
            const float Alpha = (LocalX - LowEndCm) / RampLengthCm;
            OutTrackZ = FMath::Lerp(TreatmentLowRailHeightCm, RailHeightCm, Ease01(Alpha));
            OutTrackSlope = -HeightDelta * (6.0f * Alpha * (1.0f - Alpha)) / RampLengthCm;
        }
    }

    void EvaluateCarrierPose(const float CycleProgress01, FVector& OutTrolleyLocation,
        FRotator& OutTrolleyRotation, FVector& OutBodyLocation, FRotator& OutBodyRotation)
    {
        const float LocalX = FMath::Clamp(CycleProgress01, 0.0f, 1.0f) * BayLengthCm;
        float TrackZ;
        float TrackSlope;
        EvaluateTrackPose(LocalX, TrackZ, TrackSlope);

        const float ActorLocalX = LocalX - BayLengthCm * 0.5f;
        OutTrolleyLocation = FVector(ActorLocalX, 0.0f, TrackZ);
        OutTrolleyRotation = FRotator(
            FMath::RadiansToDegrees(FMath::Atan(TrackSlope)), 0.0f, 0.0f);
        OutBodyLocation = FVector(ActorLocalX, 0.0f,
            DryBodyRootZCm + TrackZ - RailHeightCm);
        OutBodyRotation = FRotator(FMath::Clamp(
            OutTrolleyRotation.Pitch * 0.65f, -18.0f, 18.0f), 0.0f, 0.0f);
    }
}

ALBPaintShopCellActor::ALBPaintShopCellActor()
{
    PrimaryActorTick.bCanEverTick = false;
    PrimaryActorTick.bStartWithTickEnabled = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    Footprint = CreateDefaultSubobject<UBoxComponent>(TEXT("GameplayFootprint"));
    Footprint->SetupAttachment(SceneRoot);
    Footprint->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Footprint->SetCollisionObjectType(ECC_WorldDynamic);
    Footprint->SetCollisionResponseToAllChannels(ECR_Ignore);
    Footprint->SetGenerateOverlapEvents(false);
    Footprint->SetCanEverAffectNavigation(false);
    Footprint->SetHiddenInGame(true);

    ProtectedEnvelope = CreateDefaultSubobject<UBoxComponent>(TEXT("ProtectedEnvelope"));
    ProtectedEnvelope->SetupAttachment(SceneRoot);
    ProtectedEnvelope->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ProtectedEnvelope->SetCollisionObjectType(ECC_WorldDynamic);
    ProtectedEnvelope->SetCollisionResponseToAllChannels(ECR_Ignore);
    ProtectedEnvelope->SetGenerateOverlapEvents(false);
    ProtectedEnvelope->SetCanEverAffectNavigation(false);
    ProtectedEnvelope->SetHiddenInGame(true);

    InputPort = CreateDefaultSubobject<ULBPaintShopPortComponent>(TEXT("CarrierInputPort"));
    InputPort->SetupAttachment(SceneRoot);
    OutputPort = CreateDefaultSubobject<ULBPaintShopPortComponent>(TEXT("CarrierOutputPort"));
    OutputPort->SetupAttachment(SceneRoot);

    TreatmentStartPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("TreatmentStartPresentation"));
    TreatmentStartPresentation->SetupAttachment(SceneRoot);
    TreatmentEndPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("TreatmentEndPresentation"));
    TreatmentEndPresentation->SetupAttachment(SceneRoot);
    LiquidSurfacePresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("LiquidSurfacePresentation"));
    LiquidSurfacePresentation->SetupAttachment(SceneRoot);
    ProfiledRailPresentation = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("ProfiledRailPresentation"));
    ProfiledRailPresentation->SetupAttachment(SceneRoot);
    LBPaintShopCellPrivate::ConfigureGeneratedRail(ProfiledRailPresentation);
    ProfiledRailPresentation->SetVisibility(false, true);

    CarrierPresentationRoot = CreateDefaultSubobject<USceneComponent>(
        TEXT("CarrierPresentationRoot"));
    CarrierPresentationRoot->SetupAttachment(SceneRoot);
    CarrierPresentationRoot->SetMobility(EComponentMobility::Movable);
    CarrierTrolleyPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("CarrierTrolleyPresentation"));
    CarrierTrolleyPresentation->SetupAttachment(CarrierPresentationRoot);
    CarrierHoistPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("CarrierHoistPresentation"));
    CarrierHoistPresentation->SetupAttachment(CarrierPresentationRoot);
    CarrierHangerPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("CarrierHangerPresentation"));
    CarrierHangerPresentation->SetupAttachment(CarrierPresentationRoot);
    ProxyBIWPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("ProxyBIWPresentation"));
    ProxyBIWPresentation->SetupAttachment(CarrierPresentationRoot);

    for (UStaticMeshComponent* Component : {
        TreatmentStartPresentation.Get(), TreatmentEndPresentation.Get(),
        LiquidSurfacePresentation.Get(), CarrierTrolleyPresentation.Get(),
        CarrierHoistPresentation.Get(), CarrierHangerPresentation.Get(),
        ProxyBIWPresentation.Get()})
    {
        LBPaintShopCellPrivate::ConfigureCandidateMesh(Component);
        Component->SetVisibility(false, true);
    }

    TreatmentStartMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBPaintShopCellPrivate::TreatmentStartPath));
    TreatmentEndMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBPaintShopCellPrivate::TreatmentEndPath));
    LiquidSurfaceMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBPaintShopCellPrivate::LiquidSurfacePath));
    CarrierTrolleyMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBPaintShopCellPrivate::CarrierTrolleyPath));
    CarrierHoistMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBPaintShopCellPrivate::CarrierHoistPath));
    CarrierHangerMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBPaintShopCellPrivate::CarrierHangerPath));
    ProxyBIWMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBPaintShopCellPrivate::ProxyBIWPath));
    ProfiledRailSegmentMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBPaintShopCellPrivate::ProfiledRailSegmentPath));
    EDCoatLiquidMaterial = TSoftObjectPtr<UMaterialInterface>(
        FSoftObjectPath(LBPaintShopCellPrivate::EDCoatLiquidMaterialPath));

    Tags.AddUnique(TEXT("LB.PaintShop.Experimental.Cell.v001"));
    ConfigurationFailureReason = TEXT("PAINT SHOP CELL HAS NOT BEEN CONFIGURED");
}

void ALBPaintShopCellActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    if (!bConfigured) return;

    FString FailureReason;
    if (!RebuildConfiguredPresentation(FailureReason))
    {
        ClearConfiguration(FailureReason);
    }
}

bool ALBPaintShopCellActor::ConfigureCell(const FName InCellId,
    const FName InDefinitionId, FString& OutReason)
{
    OutReason.Reset();
    FLBPaintShopCellDefinition Candidate;
    if (InCellId.IsNone()
        || InDefinitionId != LBPaintShopCellIds::EDCoatDipCell
        || !FLBPaintShopDefinitionRegistry::FindCanonicalDefinition(InDefinitionId, Candidate)
        || !FLBPaintShopDefinitionRegistry::ValidateDefinition(Candidate, OutReason)
        || Candidate.CellType != ELBPaintShopCellType::EDCoatDip
        || Candidate.RecipeId != LBPaintShopRecipeIds::EDCoatV001
        || Candidate.InputWIPId != LBPaintShopWIPIds::BIWComplete
        || Candidate.OutputWIPId != LBPaintShopWIPIds::BIWEDCoated)
    {
        if (OutReason.IsEmpty())
        {
            OutReason = TEXT("PAINT SHOP CELL SUPPORTS ONLY THE CANONICAL ED-COAT DIP DEFINITION");
        }
        ClearConfiguration(OutReason);
        return false;
    }

    const FName PreviousCellId = CellId;
    const FName PreviousDefinitionId = DefinitionId;
    if (!PreviousCellId.IsNone()) Tags.Remove(PreviousCellId);
    if (!PreviousDefinitionId.IsNone()) Tags.Remove(PreviousDefinitionId);

    bConfigured = true;
    CellId = InCellId;
    DefinitionId = InDefinitionId;
    Definition = Candidate;
    PresentationState = FLBPaintShopCellPresentationState();
    ConfigurationFailureReason.Reset();
    Tags.AddUnique(CellId);
    Tags.AddUnique(DefinitionId);

    if (!RebuildConfiguredPresentation(OutReason))
    {
        ClearConfiguration(OutReason);
        return false;
    }
    return true;
}

ULBPaintShopPortComponent* ALBPaintShopCellActor::FindPort(const FName PortId) const
{
    if (!bConfigured) return nullptr;
    if (InputPort && InputPort->GetPortId() == PortId) return InputPort;
    if (OutputPort && OutputPort->GetPortId() == PortId) return OutputPort;
    return nullptr;
}

bool ALBPaintShopCellActor::HasCompletePresentationAssetSet() const
{
    return bConfigured
        && TreatmentStartPresentation && TreatmentStartPresentation->GetStaticMesh()
        && TreatmentEndPresentation && TreatmentEndPresentation->GetStaticMesh()
        && LiquidSurfacePresentation && LiquidSurfacePresentation->GetStaticMesh()
        && CarrierTrolleyPresentation && CarrierTrolleyPresentation->GetStaticMesh()
        && CarrierHoistPresentation && CarrierHoistPresentation->GetStaticMesh()
        && CarrierHangerPresentation && CarrierHangerPresentation->GetStaticMesh()
        && ProxyBIWPresentation && ProxyBIWPresentation->GetStaticMesh()
        && ProfiledRailPresentation && ProfiledRailPresentation->GetStaticMesh()
        && ProfiledRailPresentation->GetInstanceCount() == 48
        && ProfiledRailPresentation->GetMaterial(0)
            == TreatmentStartPresentation->GetMaterial(1)
        && LiquidSurfacePresentation->GetMaterial(0) == EDCoatLiquidMaterial.Get();
}

TArray<FString> ALBPaintShopCellActor::GetRequiredPresentationAssetPaths() const
{
    return {
        TreatmentStartMesh.ToSoftObjectPath().ToString(),
        TreatmentEndMesh.ToSoftObjectPath().ToString(),
        LiquidSurfaceMesh.ToSoftObjectPath().ToString(),
        CarrierTrolleyMesh.ToSoftObjectPath().ToString(),
        CarrierHoistMesh.ToSoftObjectPath().ToString(),
        CarrierHangerMesh.ToSoftObjectPath().ToString(),
        ProxyBIWMesh.ToSoftObjectPath().ToString(),
        ProfiledRailSegmentMesh.ToSoftObjectPath().ToString(),
        EDCoatLiquidMaterial.ToSoftObjectPath().ToString()
    };
}

int32 ALBPaintShopCellActor::GetProfiledRailSegmentCount() const
{
    return ProfiledRailPresentation ? ProfiledRailPresentation->GetInstanceCount() : 0;
}

bool ALBPaintShopCellActor::IsProfiledRailVisualOnly() const
{
    if (!ProfiledRailPresentation
        || ProfiledRailPresentation->GetCollisionEnabled() != ECollisionEnabled::NoCollision
        || ProfiledRailPresentation->GetGenerateOverlapEvents()
        || ProfiledRailPresentation->CanEverAffectNavigation())
    {
        return false;
    }
    for (int32 Channel = 0; Channel < ECollisionChannel::ECC_MAX; ++Channel)
    {
        if (ProfiledRailPresentation->GetCollisionResponseToChannel(
            static_cast<ECollisionChannel>(Channel)) != ECR_Ignore)
        {
            return false;
        }
    }
    return true;
}

bool ALBPaintShopCellActor::AreCandidateMeshesVisualOnly() const
{
    for (const UStaticMeshComponent* Component : {
        TreatmentStartPresentation.Get(), TreatmentEndPresentation.Get(),
        LiquidSurfacePresentation.Get(), CarrierTrolleyPresentation.Get(),
        CarrierHoistPresentation.Get(), CarrierHangerPresentation.Get(),
        ProxyBIWPresentation.Get()})
    {
        if (!LBPaintShopCellPrivate::IsVisualOnly(Component)) return false;
    }
    return true;
}

FLBPaintShopCellPresentationState ALBPaintShopCellActor::CapturePresentationState() const
{
    return PresentationState;
}

bool ALBPaintShopCellActor::ValidatePresentationState(
    const FLBPaintShopCellPresentationState& State, FString& OutReason)
{
    OutReason.Reset();
    if (State.Version != 1
        || !FMath::IsFinite(State.CycleProgress01)
        || !FMath::IsFinite(State.LiquidLevel01)
        || !FMath::IsWithinInclusive(State.CycleProgress01, 0.0f, 1.0f)
        || !FMath::IsWithinInclusive(State.LiquidLevel01, 0.0f, 1.0f))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT PRESENTATION STATE IS INVALID");
        return false;
    }
    return true;
}

bool ALBPaintShopCellActor::RestorePresentationState(
    const FLBPaintShopCellPresentationState& State, FString& OutReason)
{
    OutReason.Reset();
    if (!bConfigured)
    {
        OutReason = TEXT("PAINT SHOP CELL MUST BE CONFIGURED BEFORE PRESENTATION RESTORE");
        return false;
    }
    if (!ValidatePresentationState(State, OutReason)) return false;

    PresentationState = State;
    ApplyPresentationState();
    return true;
}

bool ALBPaintShopCellActor::SetPresentationState(
    const FLBPaintShopCellPresentationState& State, FString& OutReason)
{
    return RestorePresentationState(State, OutReason);
}

bool ALBPaintShopCellActor::RebuildConfiguredPresentation(FString& OutReason)
{
    OutReason.Reset();
    if (!bConfigured || DefinitionId != LBPaintShopCellIds::EDCoatDipCell
        || Definition.CellType != ELBPaintShopCellType::EDCoatDip)
    {
        OutReason = TEXT("PAINT SHOP CELL DOES NOT HOLD THE CANONICAL ED-COAT CONTRACT");
        return false;
    }

    UStaticMesh* Start = TreatmentStartMesh.LoadSynchronous();
    UStaticMesh* End = TreatmentEndMesh.LoadSynchronous();
    UStaticMesh* Liquid = LiquidSurfaceMesh.LoadSynchronous();
    UStaticMesh* Trolley = CarrierTrolleyMesh.LoadSynchronous();
    UStaticMesh* Hoist = CarrierHoistMesh.LoadSynchronous();
    UStaticMesh* Hanger = CarrierHangerMesh.LoadSynchronous();
    UStaticMesh* BIW = ProxyBIWMesh.LoadSynchronous();
    UStaticMesh* RailSegment = ProfiledRailSegmentMesh.LoadSynchronous();
    UMaterialInterface* LiquidMaterial = EDCoatLiquidMaterial.LoadSynchronous();
    if (!Start || !End || !Liquid || !Trolley || !Hoist || !Hanger || !BIW
        || !RailSegment || !LiquidMaterial || !Start->GetMaterial(1))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT CELL IS MISSING A REQUIRED VALIDATED PRESENTATION ASSET");
        return false;
    }

    Footprint->SetRelativeLocation(FVector(0.0f, 0.0f,
        LBPaintShopCellPrivate::FootprintDimensionsCm.Z * 0.5f));
    Footprint->SetBoxExtent(LBPaintShopCellPrivate::FootprintDimensionsCm * 0.5f);
    Footprint->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    Footprint->SetCollisionResponseToAllChannels(ECR_Ignore);
    Footprint->SetCollisionResponseToChannel(ECC_Pawn, ECR_Block);
    Footprint->SetCollisionResponseToChannel(ECC_Vehicle, ECR_Block);
    Footprint->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Footprint->SetCollisionResponseToChannel(ECC_Camera, ECR_Block);
    Footprint->SetCanEverAffectNavigation(true);

    ProtectedEnvelope->SetRelativeLocation(FVector(0.0f, 0.0f,
        LBPaintShopCellPrivate::ProtectedEnvelopeDimensionsCm.Z * 0.5f));
    ProtectedEnvelope->SetBoxExtent(
        LBPaintShopCellPrivate::ProtectedEnvelopeDimensionsCm * 0.5f);
    ProtectedEnvelope->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    ProtectedEnvelope->SetCollisionResponseToAllChannels(ECR_Ignore);
    ProtectedEnvelope->SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
    ProtectedEnvelope->SetCollisionResponseToChannel(ECC_Vehicle, ECR_Overlap);
    ProtectedEnvelope->SetGenerateOverlapEvents(true);
    ProtectedEnvelope->SetCanEverAffectNavigation(false);

    TreatmentStartPresentation->SetStaticMesh(Start);
    TreatmentStartPresentation->SetRelativeTransform(FTransform(
        FVector(-LBPaintShopCellPrivate::ModulePitchCm * 0.5f, 0.0f, 0.0f)));
    TreatmentStartPresentation->SetVisibility(true, true);
    TreatmentEndPresentation->SetStaticMesh(End);
    TreatmentEndPresentation->SetRelativeTransform(FTransform(
        FVector(LBPaintShopCellPrivate::ModulePitchCm * 0.5f, 0.0f, 0.0f)));
    TreatmentEndPresentation->SetVisibility(true, true);

    LiquidSurfacePresentation->SetStaticMesh(Liquid);
    LiquidSurfacePresentation->SetRelativeScale3D(FVector(2.0f, 1.0f, 1.0f));
    LiquidSurfacePresentation->SetMaterial(0, LiquidMaterial);
    CarrierTrolleyPresentation->SetStaticMesh(Trolley);
    CarrierHoistPresentation->SetStaticMesh(Hoist);
    CarrierHangerPresentation->SetStaticMesh(Hanger);
    ProxyBIWPresentation->SetStaticMesh(BIW);
    RebuildProfiledRail(RailSegment);
    ProfiledRailPresentation->SetMaterial(0, Start->GetMaterial(1));

    if (!ConfigurePorts(OutReason)) return false;
    if (!AreCandidateMeshesVisualOnly() || !IsProfiledRailVisualOnly())
    {
        OutReason = TEXT("PAINT SHOP CANDIDATE PRESENTATION MESH OWNS GAMEPLAY COLLISION");
        return false;
    }

    ApplyPresentationState();
    if (!HasCompletePresentationAssetSet())
    {
        OutReason = TEXT("PAINT SHOP ED-COAT PRESENTATION ASSET CONTRACT IS INCOMPLETE");
        return false;
    }
    return true;
}

void ALBPaintShopCellActor::RebuildProfiledRail(UStaticMesh* RailMesh)
{
    ProfiledRailPresentation->ClearInstances();
    ProfiledRailPresentation->SetStaticMesh(RailMesh);
    ProfiledRailPresentation->SetVisibility(RailMesh != nullptr, true);
    if (!RailMesh) return;

    for (float StartX = 0.0f;
        StartX < LBPaintShopCellPrivate::BayLengthCm - KINDA_SMALL_NUMBER;
        StartX += LBPaintShopCellPrivate::TrackSampleSpacingCm)
    {
        const float EndX = FMath::Min(
            StartX + LBPaintShopCellPrivate::TrackSampleSpacingCm,
            LBPaintShopCellPrivate::BayLengthCm);
        float StartZ;
        float StartSlope;
        float EndZ;
        float EndSlope;
        LBPaintShopCellPrivate::EvaluateTrackPose(StartX, StartZ, StartSlope);
        LBPaintShopCellPrivate::EvaluateTrackPose(EndX, EndZ, EndSlope);
        const float ActorStartX = StartX - LBPaintShopCellPrivate::BayLengthCm * 0.5f;
        const float ActorEndX = EndX - LBPaintShopCellPrivate::BayLengthCm * 0.5f;

        for (const float Y : {-LBPaintShopCellPrivate::RailOffsetYCm,
            LBPaintShopCellPrivate::RailOffsetYCm})
        {
            const FVector Start(ActorStartX, Y, StartZ);
            const FVector End(ActorEndX, Y, EndZ);
            const FVector Delta = End - Start;
            const float Length = Delta.Size();
            if (Length <= KINDA_SMALL_NUMBER) continue;
            const FRotator Rotation(
                FMath::RadiansToDegrees(FMath::Atan2(Delta.Z, Delta.X)), 0.0f, 0.0f);
            ProfiledRailPresentation->AddInstance(FTransform(
                Rotation, (Start + End) * 0.5f, FVector(Length / 100.0f, 0.18f, 0.18f)));
        }
    }
}

bool ALBPaintShopCellActor::ConfigurePorts(FString& OutReason)
{
    OutReason.Reset();
    if (Definition.Ports.Num() != 2)
    {
        OutReason = TEXT("PAINT SHOP ED-COAT CELL REQUIRES EXACTLY TWO CARRIER PORTS");
        return false;
    }

    const FLBPaintShopPortDefinition* InputDefinition = Definition.Ports.FindByPredicate([](
        const FLBPaintShopPortDefinition& Port)
    {
        return Port.PortId == LBPaintShopPortIds::CarrierIn;
    });
    const FLBPaintShopPortDefinition* OutputDefinition = Definition.Ports.FindByPredicate([](
        const FLBPaintShopPortDefinition& Port)
    {
        return Port.PortId == LBPaintShopPortIds::CarrierOut;
    });
    const FTransform InputTransform(FRotator(0.0f, 180.0f, 0.0f),
        FVector(-LBPaintShopCellPrivate::BayLengthCm * 0.5f, 0.0f,
            LBPaintShopCellPrivate::DryBodyRootZCm), FVector::OneVector);
    const FTransform OutputTransform(FRotator::ZeroRotator,
        FVector(LBPaintShopCellPrivate::BayLengthCm * 0.5f, 0.0f,
            LBPaintShopCellPrivate::DryBodyRootZCm), FVector::OneVector);
    if (!InputDefinition || !OutputDefinition
        || !InputPort->Configure(*InputDefinition, InputTransform)
        || !OutputPort->Configure(*OutputDefinition, OutputTransform))
    {
        OutReason = TEXT("PAINT SHOP ED-COAT CARRIER PORT CONFIGURATION FAILED");
        return false;
    }
    return true;
}

void ALBPaintShopCellActor::ApplyPresentationState()
{
    FVector TrolleyLocation;
    FRotator TrolleyRotation;
    FVector BodyLocation;
    FRotator BodyRotation;
    LBPaintShopCellPrivate::EvaluateCarrierPose(PresentationState.CycleProgress01,
        TrolleyLocation, TrolleyRotation, BodyLocation, BodyRotation);
    const float LiftDeltaZ = BodyLocation.Z - LBPaintShopCellPrivate::DryBodyRootZCm;

    CarrierTrolleyPresentation->SetRelativeLocation(TrolleyLocation);
    CarrierTrolleyPresentation->SetRelativeRotation(TrolleyRotation);
    CarrierTrolleyPresentation->SetRelativeScale3D(FVector::OneVector);
    CarrierHoistPresentation->SetRelativeLocation(FVector(BodyLocation.X, 0.0f,
        LBPaintShopCellPrivate::AuthoredHoistPivotZCm + LiftDeltaZ));
    CarrierHoistPresentation->SetRelativeRotation(BodyRotation);
    CarrierHoistPresentation->SetRelativeScale3D(FVector::OneVector);
    CarrierHangerPresentation->SetRelativeLocation(FVector(BodyLocation.X, 0.0f,
        LBPaintShopCellPrivate::HangerRootZCm + LiftDeltaZ));
    CarrierHangerPresentation->SetRelativeRotation(BodyRotation);
    CarrierHangerPresentation->SetRelativeScale3D(FVector::OneVector);
    ProxyBIWPresentation->SetRelativeLocation(BodyLocation);
    ProxyBIWPresentation->SetRelativeRotation(BodyRotation);
    ProxyBIWPresentation->SetRelativeScale3D(FVector::OneVector);

    for (UStaticMeshComponent* Component : {
        CarrierTrolleyPresentation.Get(), CarrierHoistPresentation.Get(),
        CarrierHangerPresentation.Get(), ProxyBIWPresentation.Get()})
    {
        Component->SetVisibility(PresentationState.bCarrierVisible, true);
    }

    LiquidSurfacePresentation->SetRelativeLocation(FVector(0.0f, 0.0f,
        FMath::Lerp(LBPaintShopCellPrivate::EmptyTankSurfaceZCm,
            LBPaintShopCellPrivate::LiquidSurfaceZCm, PresentationState.LiquidLevel01)));
    LiquidSurfacePresentation->SetVisibility(
        PresentationState.LiquidLevel01 > KINDA_SMALL_NUMBER, true);

    Tags.Remove(TEXT("LB.PaintShop.Cell.Faulted"));
    if (PresentationState.bFaulted)
    {
        Tags.AddUnique(TEXT("LB.PaintShop.Cell.Faulted"));
    }
}

void ALBPaintShopCellActor::ClearConfiguration(const FString& FailureReason)
{
    if (!CellId.IsNone()) Tags.Remove(CellId);
    if (!DefinitionId.IsNone()) Tags.Remove(DefinitionId);
    Tags.Remove(TEXT("LB.PaintShop.Cell.Faulted"));

    bConfigured = false;
    CellId = NAME_None;
    DefinitionId = NAME_None;
    Definition = FLBPaintShopCellDefinition();
    PresentationState = FLBPaintShopCellPresentationState();
    ConfigurationFailureReason = FailureReason.IsEmpty()
        ? TEXT("PAINT SHOP CELL CONFIGURATION FAILED") : FailureReason;

    const FLBPaintShopPortDefinition InvalidPort;
    InputPort->Configure(InvalidPort, FTransform::Identity);
    OutputPort->Configure(InvalidPort, FTransform::Identity);
    Footprint->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Footprint->SetCanEverAffectNavigation(false);
    ProtectedEnvelope->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ProtectedEnvelope->SetGenerateOverlapEvents(false);
    ProfiledRailPresentation->ClearInstances();
    ProfiledRailPresentation->SetStaticMesh(nullptr);
    ProfiledRailPresentation->EmptyOverrideMaterials();
    ProfiledRailPresentation->SetVisibility(false, true);
    ProfiledRailPresentation->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ProfiledRailPresentation->SetCollisionResponseToAllChannels(ECR_Ignore);
    ProfiledRailPresentation->SetGenerateOverlapEvents(false);
    ProfiledRailPresentation->SetCanEverAffectNavigation(false);
    ClearPresentationMeshes();
}

void ALBPaintShopCellActor::ClearPresentationMeshes()
{
    for (UStaticMeshComponent* Component : {
        TreatmentStartPresentation.Get(), TreatmentEndPresentation.Get(),
        LiquidSurfacePresentation.Get(), CarrierTrolleyPresentation.Get(),
        CarrierHoistPresentation.Get(), CarrierHangerPresentation.Get(),
        ProxyBIWPresentation.Get()})
    {
        if (!Component) continue;
        Component->SetStaticMesh(nullptr);
        Component->EmptyOverrideMaterials();
        Component->SetVisibility(false, true);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCollisionResponseToAllChannels(ECR_Ignore);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
    }
}
