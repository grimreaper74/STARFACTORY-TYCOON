#include "LBECoatLineActor.h"

#include "LBFactoryFloorMarkingComponent.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBStatusBeaconComponent.h"
#include "LBVehiclePanelCatalog.h"

#include "Components/BoxComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/RectLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

const FVector ALBECoatLineActor::ProtectedEnvelopeHalfExtentCm(9750.0f, 750.0f, 500.0f);
const FVector ALBECoatLineActor::ProtectedEnvelopeRelativeCentreCm(9650.0f, 0.0f, 500.0f);

namespace LBECoatLinePrivate
{
    float Ease01(const float Value)
    {
        return FMath::SmoothStep(0.0f, 1.0f, FMath::Clamp(Value, 0.0f, 1.0f));
    }

    void SetFallbackColour(UStaticMeshComponent* Component, const FLinearColor& Colour)
    {
        if (!Component) return;
        if (UMaterialInstanceDynamic* Material = Component->CreateAndSetMaterialInstanceDynamic(0))
            Material->SetVectorParameterValue(TEXT("Color"), Colour);
    }

    void SetFallbackColour(UHierarchicalInstancedStaticMeshComponent* Component,
        const FLinearColor& Colour)
    {
        if (!Component) return;
        if (UMaterialInstanceDynamic* Material = Component->CreateAndSetMaterialInstanceDynamic(0))
            Material->SetVectorParameterValue(TEXT("Color"), Colour);
    }

    bool IsBayAvailable(const FLBECoatBayOperatingState& State)
    {
        return State.bEnabled && !State.bFaulted && !State.bStarved;
    }
}

ALBECoatLineActor::ALBECoatLineActor()
{
    PrimaryActorTick.bCanEverTick = true;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    ProtectedEnvelope = CreateDefaultSubobject<UBoxComponent>(TEXT("ProtectedEnvelope"));
    ProtectedEnvelope->SetupAttachment(SceneRoot);
    ProtectedEnvelope->SetRelativeLocation(ProtectedEnvelopeRelativeCentreCm);
    ProtectedEnvelope->SetBoxExtent(ProtectedEnvelopeHalfExtentCm);
    ProtectedEnvelope->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    ProtectedEnvelope->SetCollisionObjectType(ECC_WorldDynamic);
    ProtectedEnvelope->SetCollisionResponseToAllChannels(ECR_Ignore);
    ProtectedEnvelope->SetCollisionResponseToChannel(ECC_WorldDynamic, ECR_Overlap);
    ProtectedEnvelope->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    ProtectedEnvelope->SetGenerateOverlapEvents(true);
    ProtectedEnvelope->SetCanEverAffectNavigation(false);

    FloorMarkings = CreateDefaultSubobject<ULBFactoryFloorMarkingComponent>(TEXT("FloorMarkings"));
    FloorMarkings->SetupAttachment(SceneRoot);

    InputPort = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("InputPort"));
    InputPort->SetupAttachment(SceneRoot);
    InputPort->Direction = ELBFactoryPortDirection::Input;
    InputPort->TransportKind = ELBFactoryTransportKind::PanelTransfer;
    InputPort->MaterialClass = ELBFactoryMaterialClass::BodyInWhite;
    InputPort->ProcessStage = LBFactoryProcessStage::ECoat;
    InputPort->MaximumAutomaticLinkDistanceCm = 2500.0f;
    InputPort->SetRelativeLocation(FVector(0.0f, 0.0f, DryBodyRootZCm));

    OutputPort = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("OutputPort"));
    OutputPort->SetupAttachment(SceneRoot);
    OutputPort->Direction = ELBFactoryPortDirection::Output;
    OutputPort->TransportKind = ELBFactoryTransportKind::PanelTransfer;
    OutputPort->MaterialClass = ELBFactoryMaterialClass::GeneralParts;
    OutputPort->ProcessStage = LBFactoryProcessStage::ECoat;
    OutputPort->MaximumAutomaticLinkDistanceCm = 2500.0f;
    OutputPort->SetRelativeLocation(FVector(TotalLengthCm, 0.0f, DryBodyRootZCm));

    auto CreateInstanceComponent = [this](const TCHAR* Name)
    {
        UHierarchicalInstancedStaticMeshComponent* Component =
            CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(Name);
        Component->SetupAttachment(SceneRoot);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCanEverAffectNavigation(false);
        return Component;
    };

    StructureInstances = CreateInstanceComponent(TEXT("StructureInstances"));
    RailInstances = CreateInstanceComponent(TEXT("RailInstances"));
    TreatmentModuleInstances = CreateInstanceComponent(TEXT("TreatmentModuleInstances"));
    TreatmentEndModuleInstances = CreateInstanceComponent(TEXT("TreatmentEndModuleInstances"));
    TankFallbackInstances = CreateInstanceComponent(TEXT("TankFallbackInstances"));
    CatwalkFallbackInstances = CreateInstanceComponent(TEXT("CatwalkFallbackInstances"));
    OvenProcessInstances = CreateInstanceComponent(TEXT("OvenProcessInstances"));
    OvenFallbackInstances = CreateInstanceComponent(TEXT("OvenFallbackInstances"));
    OvenServiceDoorInstances = CreateInstanceComponent(TEXT("OvenServiceDoorInstances"));
    OvenServiceLightHousingInstances = CreateInstanceComponent(TEXT("OvenServiceLightHousingInstances"));
    OvenFanHousingInstances = CreateInstanceComponent(TEXT("OvenFanHousingInstances"));
    BeaconBaseInstances = CreateInstanceComponent(TEXT("BeaconBaseInstances"));
    BeaconGreenLensInstances = CreateInstanceComponent(TEXT("BeaconGreenLensInstances"));
    BeaconAmberLensInstances = CreateInstanceComponent(TEXT("BeaconAmberLensInstances"));
    BeaconRedLensInstances = CreateInstanceComponent(TEXT("BeaconRedLensInstances"));

    auto CreateModuleComponent = [this](const TCHAR* Name)
    {
        UStaticMeshComponent* Component = CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Component->SetupAttachment(SceneRoot);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCanEverAffectNavigation(false);
        return Component;
    };

    DrainInspectionPresentation = CreateModuleComponent(TEXT("DrainInspectionPresentation"));
    OvenEntryPresentation = CreateModuleComponent(TEXT("OvenEntryPresentation"));
    OvenExitPresentation = CreateModuleComponent(TEXT("OvenExitPresentation"));

    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) CubeFallbackMesh = Cube.Object;

    // These are individual modular destinations, never a guessed monolithic review-assembly path.
    const FString RuntimeRoot = TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/");
    // v002 deliberately removes the source module's baked flat rails. The treatment
    // track is generated from the same continuous dipping contract used by carriers.
    TreatmentBayMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v002/Modules/")
        TEXT("SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002.")
        TEXT("SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002")));
    TreatmentBayEndMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v002/Modules/")
        TEXT("SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002.")
        TEXT("SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002")));
    DrainInspectionMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Modules/SM_LB_EDLine_DrainInspectionModule_Blockout_v001.SM_LB_EDLine_DrainInspectionModule_Blockout_v001")));
    OvenEntryMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Modules/SM_LB_EDLine_OvenEntryModule_Blockout_v001.SM_LB_EDLine_OvenEntryModule_Blockout_v001")));
    OvenProcessBayMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Modules/SM_LB_EDLine_OvenProcessModule_Blockout_v001.SM_LB_EDLine_OvenProcessModule_Blockout_v001")));
    OvenExitMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Modules/SM_LB_EDLine_OvenExitModule_Blockout_v001.SM_LB_EDLine_OvenExitModule_Blockout_v001")));
    LiquidSurfaceMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Process/SM_LB_EDLine_TreatmentLiquidSurface_Blockout_v001.SM_LB_EDLine_TreatmentLiquidSurface_Blockout_v001")));
    CarrierTrolleyMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Carrier/SM_LB_EDLine_CarrierTrolley_Blockout_v001.SM_LB_EDLine_CarrierTrolley_Blockout_v001")));
    CarrierHoistMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Carrier/SM_LB_EDLine_CarrierHoistCables_Blockout_v001.SM_LB_EDLine_CarrierHoistCables_Blockout_v001")));
    CarrierHangerMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Carrier/SM_LB_EDLine_CarrierHanger_Blockout_v001.SM_LB_EDLine_CarrierHanger_Blockout_v001")));
    VehicleShellMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Validation/SM_LB_EDLine_ProxyBIW_Blockout_v001.SM_LB_EDLine_ProxyBIW_Blockout_v001")));
    OvenFanMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Operations/SM_LB_EDLine_OvenFanAssembly_Blockout_v001.SM_LB_EDLine_OvenFanAssembly_Blockout_v001")));
    OvenServiceDoorMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Operations/SM_LB_EDLine_OvenServiceDoor_Blockout_v001.SM_LB_EDLine_OvenServiceDoor_Blockout_v001")));
    OvenServiceLightHousingMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Operations/SM_LB_EDLine_OvenServiceLight_Blockout_v001.SM_LB_EDLine_OvenServiceLight_Blockout_v001")));
    BeaconBaseMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Operations/SM_LB_EDLine_BeaconBase_Blockout_v001.SM_LB_EDLine_BeaconBase_Blockout_v001")));
    BeaconGreenLensMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Operations/SM_LB_EDLine_BeaconGreenLens_Blockout_v001.SM_LB_EDLine_BeaconGreenLens_Blockout_v001")));
    BeaconAmberLensMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Operations/SM_LB_EDLine_BeaconAmberLens_Blockout_v001.SM_LB_EDLine_BeaconAmberLens_Blockout_v001")));
    BeaconRedLensMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(RuntimeRoot
        + TEXT("Operations/SM_LB_EDLine_BeaconRedLens_Blockout_v001.SM_LB_EDLine_BeaconRedLens_Blockout_v001")));
    const TCHAR* LiquidMaterialNames[TreatmentBayCount] = {
        TEXT("MI_LB_EDLine_Liquid_Degrease_v001"),
        TEXT("MI_LB_EDLine_Liquid_Rinse1_v001"),
        TEXT("MI_LB_EDLine_Liquid_Phosphate_v001"),
        TEXT("MI_LB_EDLine_Liquid_Rinse2_v001"),
        TEXT("MI_LB_EDLine_Liquid_ED_Ecoat_v001"),
        TEXT("MI_LB_EDLine_Liquid_UF_Rinse_v001")
    };
    for (const TCHAR* MaterialName : LiquidMaterialNames)
        TreatmentLiquidMaterials.Add(TSoftObjectPtr<UMaterialInterface>(FSoftObjectPath(RuntimeRoot
            + FString::Printf(TEXT("Materials/%s.%s"), MaterialName, MaterialName))));

    for (int32 Index = 0; Index < TreatmentBayCount; ++Index)
    {
        const FName ComponentName(*FString::Printf(TEXT("LiquidSurface_%02d"), Index));
        UStaticMeshComponent* Liquid = CreateDefaultSubobject<UStaticMeshComponent>(ComponentName);
        Liquid->SetupAttachment(SceneRoot);
        Liquid->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Liquid->SetCanEverAffectNavigation(false);
        Liquid->SetCastShadow(false);
        LiquidSurfaces.Add(Liquid);

    }

    for (int32 Index = 0; Index < TreatmentBayCount * TreatmentModulesPerBay; ++Index)
    {
        const FName LightName(*FString::Printf(TEXT("TreatmentServiceLight_%02d"), Index));
        UPointLightComponent* ServiceLight = CreateDefaultSubobject<UPointLightComponent>(LightName);
        ServiceLight->SetupAttachment(SceneRoot);
        ServiceLight->SetRelativeLocation(FVector((Index + 0.5f) * ModulePitchCm, -430.0f, 560.0f));
        ServiceLight->SetAttenuationRadius(900.0f);
        ServiceLight->SetCastShadows(false);
        TreatmentServiceLights.Add(ServiceLight);
    }

    for (int32 Index = 0; Index < 8; ++Index)
    {
        const float X = OvenSectionStartCm + (Index + 0.5f) * ModulePitchCm;
        const FName InteriorLightName(*FString::Printf(TEXT("OvenInteriorLight_%02d"), Index));
        URectLightComponent* InteriorLight = CreateDefaultSubobject<URectLightComponent>(InteriorLightName);
        InteriorLight->SetupAttachment(SceneRoot);
        InteriorLight->SetRelativeLocation(FVector(X, 0.0f, 735.0f));
        InteriorLight->SetRelativeRotation(FRotator(-90.0f, 0.0f, 0.0f));
        InteriorLight->SetSourceWidth(620.0f);
        InteriorLight->SetSourceHeight(160.0f);
        InteriorLight->SetAttenuationRadius(1150.0f);
        InteriorLight->SetCastShadows(false);
        OvenInteriorLights.Add(InteriorLight);

        const FName FanName(*FString::Printf(TEXT("OvenFan_%02d"), Index));
        UStaticMeshComponent* Fan = CreateDefaultSubobject<UStaticMeshComponent>(FanName);
        Fan->SetupAttachment(SceneRoot);
        Fan->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Fan->SetCanEverAffectNavigation(false);
        Fan->SetRelativeLocation(FVector(X, 0.0f, 875.0f));
        OvenFans.Add(Fan);
    }

    for (int32 Index = 0; Index < 2; ++Index)
    {
        const FName SpotName(*FString::Printf(TEXT("PortalSpotLight_%02d"), Index));
        USpotLightComponent* Spot = CreateDefaultSubobject<USpotLightComponent>(SpotName);
        Spot->SetupAttachment(SceneRoot);
        Spot->SetRelativeLocation(FVector(Index == 0 ? OvenSectionStartCm : TotalLengthCm,
            0.0f, 720.0f));
        Spot->SetRelativeRotation(FRotator(-90.0f, 0.0f, 0.0f));
        Spot->SetAttenuationRadius(1000.0f);
        Spot->SetInnerConeAngle(32.0f);
        Spot->SetOuterConeAngle(50.0f);
        Spot->SetCastShadows(false);
        PortalSpotLights.Add(Spot);
    }

    EntryBeacon = CreateDefaultSubobject<ULBStatusBeaconComponent>(TEXT("EntryBeacon"));
    EntryBeacon->SetupAttachment(SceneRoot);
    EntryBeacon->SetRelativeLocation(FVector(OvenSectionStartCm + ModulePitchCm * 0.5f,
        350.0f, 900.0f));
    ExitBeacon = CreateDefaultSubobject<ULBStatusBeaconComponent>(TEXT("ExitBeacon"));
    ExitBeacon->SetupAttachment(SceneRoot);
    ExitBeacon->SetRelativeLocation(FVector(TotalLengthCm - ModulePitchCm * 0.5f,
        350.0f, 900.0f));

    InitializeBayDefinitions();
    Tags = { TEXT("LB.PlayerBuilt.ECoatLine"), TEXT("LB.Factory.PaintShop"),
        TEXT("LB.FactoryBuilder.Machine") };
}

void ALBECoatLineActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    InitializeBayDefinitions();
    RebuildLineVisuals();
}

void ALBECoatLineActor::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    AdvanceSimulation(DeltaSeconds);
}

bool ALBECoatLineActor::Configure(const FName InLineId)
{
    if (InLineId.IsNone()) return false;
    LineId = InLineId;
    InputPort->PortId = FName(*FString::Printf(TEXT("%s-IN"), *LineId.ToString()));
    OutputPort->PortId = FName(*FString::Printf(TEXT("%s-OUT"), *LineId.ToString()));
    Tags = { TEXT("LB.PlayerBuilt.ECoatLine"), TEXT("LB.Factory.PaintShop"),
        TEXT("LB.FactoryBuilder.Machine"),
        FName(*FString::Printf(TEXT("LB.ECoatLine.%s"), *LineId.ToString())) };
    RebuildLineVisuals();
    return true;
}

void ALBECoatLineActor::InitializeBayDefinitions()
{
    BayDescriptors.Reset(TotalBayCount);
    const ELBECoatBayType Types[TotalBayCount] = {
        ELBECoatBayType::Degrease,
        ELBECoatBayType::Rinse1,
        ELBECoatBayType::Phosphate,
        ELBECoatBayType::Rinse2,
        ELBECoatBayType::EDCoat,
        ELBECoatBayType::UFRinse,
        ELBECoatBayType::DrainInspection,
        ELBECoatBayType::OvenEntry,
        ELBECoatBayType::OvenCure,
        ELBECoatBayType::OvenCure,
        ELBECoatBayType::OvenCure,
        ELBECoatBayType::OvenCure,
        ELBECoatBayType::OvenCure,
        ELBECoatBayType::OvenCure,
        ELBECoatBayType::OvenExit
    };
    const TCHAR* Names[TotalBayCount] = {
        TEXT("DEGREASE"), TEXT("RINSE_1"), TEXT("PHOSPHATE"), TEXT("RINSE_2"),
        TEXT("ED_ECOAT"), TEXT("UF_RINSE"), TEXT("DRAIN_INSPECTION"),
        TEXT("OVEN_ENTRY"), TEXT("OVEN_CURE_1"), TEXT("OVEN_CURE_2"),
        TEXT("OVEN_CURE_3"), TEXT("OVEN_CURE_4"), TEXT("OVEN_CURE_5"),
        TEXT("OVEN_CURE_6"), TEXT("OVEN_EXIT")
    };
    float CursorX = 0.0f;
    for (int32 Index = 0; Index < TotalBayCount; ++Index)
    {
        const float BayLength = Index < TreatmentBayCount ? TreatmentBayLengthCm : ModulePitchCm;
        FLBECoatBayDescriptor Descriptor;
        Descriptor.BayIndex = Index;
        Descriptor.BayId = Names[Index];
        Descriptor.BayType = Types[Index];
        Descriptor.StartXCm = CursorX;
        Descriptor.EndXCm = CursorX + BayLength;
        Descriptor.bHasLiquid = Index < TreatmentBayCount;
        Descriptor.bEnclosed = Index >= 7;
        BayDescriptors.Add(Descriptor);
        CursorX += BayLength;
    }

    if (BayOperatingStates.Num() != TotalBayCount)
    {
        BayOperatingStates.Reset(TotalBayCount);
        const float DefaultTemperatures[TotalBayCount] = {
            55.0f, 25.0f, 45.0f, 25.0f, 30.0f, 25.0f, 20.0f,
            80.0f, 180.0f, 180.0f, 180.0f, 180.0f, 180.0f, 180.0f, 80.0f
        };
        for (int32 Index = 0; Index < TotalBayCount; ++Index)
        {
            FLBECoatBayOperatingState State;
            State.BayIndex = Index;
            State.TemperatureC = DefaultTemperatures[Index];
            State.LiquidLevel01 = Index < TreatmentBayCount ? 1.0f : 0.0f;
            BayOperatingStates.Add(State);
        }
    }
}

int32 ALBECoatLineActor::FindBayIndexAtDistance(const float DistanceCm) const
{
    if (BayDescriptors.Num() != TotalBayCount) return INDEX_NONE;
    const float Distance = FMath::Clamp(DistanceCm, 0.0f, TotalLengthCm);
    if (FMath::IsNearlyEqual(Distance, TotalLengthCm, KINDA_SMALL_NUMBER))
        return TotalBayCount - 1;
    for (const FLBECoatBayDescriptor& Bay : BayDescriptors)
        if (Distance >= Bay.StartXCm && Distance < Bay.EndXCm) return Bay.BayIndex;
    return INDEX_NONE;
}

float ALBECoatLineActor::MigrateLegacyCarrierDistance(const float LegacyDistanceCm)
{
    const float Distance = FMath::Clamp(LegacyDistanceCm, 0.0f, LegacyTotalLengthCm);
    if (FMath::IsNearlyEqual(Distance, LegacyTotalLengthCm, KINDA_SMALL_NUMBER))
        return TotalLengthCm;
    const int32 LegacyBay = FMath::Clamp(FMath::FloorToInt(Distance / ModulePitchCm),
        0, TotalBayCount - 1);
    const float Alpha = FMath::Clamp((Distance - LegacyBay * ModulePitchCm) / ModulePitchCm,
        0.0f, 1.0f);
    if (LegacyBay < TreatmentBayCount)
        return LegacyBay * TreatmentBayLengthCm + Alpha * TreatmentBayLengthCm;
    return TreatmentSectionLengthCm
        + (LegacyBay - TreatmentBayCount) * ModulePitchCm + Alpha * ModulePitchCm;
}

bool ALBECoatLineActor::EvaluateTrackPoseAtDistance(const float DistanceCm,
    FVector& OutTrolleyLocationCm, FRotator& OutTrolleyRotation) const
{
    if (!FMath::IsFinite(DistanceCm)) return false;

    const float Distance = FMath::Clamp(DistanceCm, 0.0f, TotalLengthCm);
    float TrackZ = RailHeightCm;
    float TrackSlope = 0.0f;
    const int32 BayIndex = FindBayIndexAtDistance(Distance);
    if (BayDescriptors.IsValidIndex(BayIndex) && BayIndex < TreatmentBayCount)
    {
        const FLBECoatBayDescriptor& Bay = BayDescriptors[BayIndex];
        const float LocalX = FMath::Clamp(Distance - Bay.StartXCm, 0.0f,
            TreatmentBayLengthCm);
        constexpr float RampStartCm = 300.0f;
        constexpr float RampEndCm = 750.0f;
        constexpr float LowEndCm = 1050.0f;
        constexpr float RiseEndCm = 1500.0f;
        constexpr float RampLengthCm = RampEndCm - RampStartCm;
        const float HeightDelta = TreatmentLowRailHeightCm - RailHeightCm;

        if (LocalX > RampStartCm && LocalX < RampEndCm)
        {
            const float Alpha = (LocalX - RampStartCm) / RampLengthCm;
            const float Eased = LBECoatLinePrivate::Ease01(Alpha);
            TrackZ = FMath::Lerp(RailHeightCm, TreatmentLowRailHeightCm, Eased);
            TrackSlope = HeightDelta * (6.0f * Alpha * (1.0f - Alpha)) / RampLengthCm;
        }
        else if (LocalX >= RampEndCm && LocalX <= LowEndCm)
        {
            TrackZ = TreatmentLowRailHeightCm;
        }
        else if (LocalX > LowEndCm && LocalX < RiseEndCm)
        {
            const float Alpha = (LocalX - LowEndCm) / RampLengthCm;
            const float Eased = LBECoatLinePrivate::Ease01(Alpha);
            TrackZ = FMath::Lerp(TreatmentLowRailHeightCm, RailHeightCm, Eased);
            TrackSlope = -HeightDelta * (6.0f * Alpha * (1.0f - Alpha)) / RampLengthCm;
        }
    }

    OutTrolleyLocationCm = FVector(Distance, 0.0f, TrackZ);
    OutTrolleyRotation = FRotator(FMath::RadiansToDegrees(FMath::Atan(TrackSlope)),
        0.0f, 0.0f);
    return true;
}

UStaticMesh* ALBECoatLineActor::ResolveMesh(const TSoftObjectPtr<UStaticMesh>& Reference) const
{
    if (Reference.IsNull()) return nullptr;
    if (UStaticMesh* Loaded = Reference.Get()) return Loaded;
    return bLoadReferencedMeshesSynchronously ? Reference.LoadSynchronous() : nullptr;
}

UMaterialInterface* ALBECoatLineActor::ResolveMaterial(
    const TSoftObjectPtr<UMaterialInterface>& Reference) const
{
    if (Reference.IsNull()) return nullptr;
    if (UMaterialInterface* Loaded = Reference.Get()) return Loaded;
    return bLoadReferencedMeshesSynchronously ? Reference.LoadSynchronous() : nullptr;
}

bool ALBECoatLineActor::HasImportedModuleForBay(const int32 BayIndex) const
{
    if (!FMath::IsWithinInclusive(BayIndex, 0, TotalBayCount - 1)) return false;
    if (BayIndex < TreatmentBayCount)
        return ResolveMesh(TreatmentBayMesh) != nullptr
            && ResolveMesh(TreatmentBayEndMesh) != nullptr;
    if (BayIndex == 6) return ResolveMesh(DrainInspectionMesh) != nullptr;
    if (BayIndex == 7) return ResolveMesh(OvenEntryMesh) != nullptr;
    if (BayIndex <= 13) return ResolveMesh(OvenProcessBayMesh) != nullptr;
    return ResolveMesh(OvenExitMesh) != nullptr;
}

void ALBECoatLineActor::AddBoxInstance(UHierarchicalInstancedStaticMeshComponent* Component,
    const FVector& CentreCm, const FVector& SizeCm) const
{
    if (!Component || !CubeFallbackMesh) return;
    Component->SetStaticMesh(CubeFallbackMesh);
    Component->AddInstance(FTransform(FRotator::ZeroRotator, CentreCm, SizeCm / 100.0f));
}

void ALBECoatLineActor::BuildFallbackStructure()
{
    StructureInstances->SetStaticMesh(CubeFallbackMesh);
    TankFallbackInstances->SetStaticMesh(CubeFallbackMesh);
    CatwalkFallbackInstances->SetStaticMesh(CubeFallbackMesh);

    // Imported modules already carry their own gantry and access structure. Emit a seam
    // only where at least one neighbouring physical 900 cm module is unresolved.
    TSet<int32> UnresolvedSeams;
    for (int32 ModuleIndex = 0; ModuleIndex < GetPhysicalVisualModuleCount(); ++ModuleIndex)
    {
        const float CentreX = (ModuleIndex + 0.5f) * ModulePitchCm;
        const int32 BayIndex = FindBayIndexAtDistance(CentreX);
        if (BayIndex != INDEX_NONE && !HasImportedModuleForBay(BayIndex))
        {
            UnresolvedSeams.Add(ModuleIndex);
            UnresolvedSeams.Add(ModuleIndex + 1);
        }
    }
    for (const int32 SeamIndex : UnresolvedSeams)
    {
        const float X = SeamIndex * ModulePitchCm;
        AddBoxInstance(StructureInstances, FVector(X, -520.0f, 400.0f), FVector(40.0f, 40.0f, 800.0f));
        AddBoxInstance(StructureInstances, FVector(X, 520.0f, 400.0f), FVector(40.0f, 40.0f, 800.0f));
        AddBoxInstance(StructureInstances, FVector(X, 0.0f, RailHeightCm), FVector(40.0f, 1080.0f, 40.0f));
    }

    if (!ResolveMesh(TreatmentBayMesh) || !ResolveMesh(TreatmentBayEndMesh))
    {
        for (int32 Index = 0; Index < TreatmentBayCount; ++Index)
        {
            const FLBECoatBayDescriptor& Bay = BayDescriptors[Index];
            const float X = (Bay.StartXCm + Bay.EndXCm) * 0.5f;
            constexpr float VesselInsideLengthCm = 1700.0f;
            AddBoxInstance(TankFallbackInstances, FVector(X, 0.0f, 20.0f),
                FVector(VesselInsideLengthCm, 520.0f, 40.0f));
            AddBoxInstance(TankFallbackInstances, FVector(X, -260.0f, TankRimZCm * 0.5f),
                FVector(VesselInsideLengthCm, 30.0f, TankRimZCm));
            AddBoxInstance(TankFallbackInstances, FVector(X, 260.0f, TankRimZCm * 0.5f),
                FVector(VesselInsideLengthCm, 30.0f, TankRimZCm));
            AddBoxInstance(TankFallbackInstances, FVector(X - VesselInsideLengthCm * 0.5f,
                0.0f, TankRimZCm * 0.5f),
                FVector(30.0f, 520.0f, TankRimZCm));
            AddBoxInstance(TankFallbackInstances, FVector(X + VesselInsideLengthCm * 0.5f,
                0.0f, TankRimZCm * 0.5f),
                FVector(30.0f, 520.0f, TankRimZCm));
        }
    }

    // Independent service decks are fallback-only because the imported treatment and
    // drain modules already include their catwalks and guardrails.
    for (int32 Index = 0; Index < TreatmentBayCount; ++Index)
    {
        if (HasImportedModuleForBay(Index)) continue;
        const FLBECoatBayDescriptor& Bay = BayDescriptors[Index];
        const float X = (Bay.StartXCm + Bay.EndXCm) * 0.5f;
        AddBoxInstance(CatwalkFallbackInstances, FVector(X, -370.0f, 315.0f),
            FVector(1760.0f, 120.0f, 20.0f));
        AddBoxInstance(CatwalkFallbackInstances, FVector(X, 370.0f, 315.0f),
            FVector(1760.0f, 120.0f, 20.0f));
    }
    if (!HasImportedModuleForBay(6))
    {
        const float X = (BayDescriptors[6].StartXCm + BayDescriptors[6].EndXCm) * 0.5f;
        AddBoxInstance(CatwalkFallbackInstances, FVector(X, -370.0f, 315.0f), FVector(860.0f, 120.0f, 20.0f));
        AddBoxInstance(CatwalkFallbackInstances, FVector(X, 370.0f, 315.0f), FVector(860.0f, 120.0f, 20.0f));
        AddBoxInstance(CatwalkFallbackInstances, FVector(X, 0.0f, 20.0f), FVector(700.0f, 500.0f, 20.0f));
    }

    LBECoatLinePrivate::SetFallbackColour(StructureInstances,
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("343D45"))));
    LBECoatLinePrivate::SetFallbackColour(TankFallbackInstances,
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("3F6C61"))));
    LBECoatLinePrivate::SetFallbackColour(CatwalkFallbackInstances,
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("D6A821"))));
}

void ALBECoatLineActor::RebuildLineVisuals()
{
    InitializeBayDefinitions();
    StructureInstances->ClearInstances();
    RailInstances->ClearInstances();
    TreatmentModuleInstances->ClearInstances();
    TreatmentEndModuleInstances->ClearInstances();
    TankFallbackInstances->ClearInstances();
    CatwalkFallbackInstances->ClearInstances();
    OvenProcessInstances->ClearInstances();
    OvenFallbackInstances->ClearInstances();
    OvenServiceDoorInstances->ClearInstances();
    OvenServiceLightHousingInstances->ClearInstances();
    OvenFanHousingInstances->ClearInstances();
    BeaconBaseInstances->ClearInstances();
    BeaconGreenLensInstances->ClearInstances();
    BeaconAmberLensInstances->ClearInstances();
    BeaconRedLensInstances->ClearInstances();

    BuildFallbackStructure();

    UStaticMesh* TreatmentStartMesh = ResolveMesh(TreatmentBayMesh);
    UStaticMesh* TreatmentEndMesh = ResolveMesh(TreatmentBayEndMesh);
    TreatmentModuleInstances->SetStaticMesh(TreatmentStartMesh);
    TreatmentEndModuleInstances->SetStaticMesh(TreatmentEndMesh);
    TreatmentModuleInstances->SetVisibility(TreatmentStartMesh != nullptr);
    TreatmentEndModuleInstances->SetVisibility(TreatmentEndMesh != nullptr);
    for (int32 BayIndex = 0; BayIndex < TreatmentBayCount; ++BayIndex)
    {
        const float BayStartX = BayIndex * TreatmentBayLengthCm;
        if (TreatmentStartMesh)
            TreatmentModuleInstances->AddInstance(FTransform(
                FVector(BayStartX + ModulePitchCm * 0.5f, 0.0f, 0.0f)));
        if (TreatmentEndMesh)
            TreatmentEndModuleInstances->AddInstance(FTransform(
                FVector(BayStartX + ModulePitchCm * 1.5f, 0.0f, 0.0f)));
    }

    // The treatment track is generated from the exact motion curve. Never reinstate the
    // baked flat rail from the Meshy module: doing so would make the carrier leave its rail.
    RailInstances->SetStaticMesh(CubeFallbackMesh);
    RailInstances->SetVisibility(CubeFallbackMesh != nullptr);
    auto AddRailBetween = [this](const FVector& Start, const FVector& End)
    {
        if (!RailInstances || !CubeFallbackMesh) return;
        const FVector Delta = End - Start;
        const float Length = Delta.Size();
        if (Length <= KINDA_SMALL_NUMBER) return;
        const FRotator Rotation(FMath::RadiansToDegrees(FMath::Atan2(Delta.Z, Delta.X)),
            0.0f, 0.0f);
        RailInstances->AddInstance(FTransform(Rotation, (Start + End) * 0.5f,
            FVector(Length / 100.0f, 0.18f, 0.18f)));
    };
    constexpr float TrackSampleSpacingCm = 75.0f;
    for (float StartX = 0.0f; StartX < TreatmentSectionLengthCm - KINDA_SMALL_NUMBER;
        StartX += TrackSampleSpacingCm)
    {
        const float EndX = FMath::Min(StartX + TrackSampleSpacingCm, TreatmentSectionLengthCm);
        FVector StartTrack;
        FVector EndTrack;
        FRotator IgnoredRotation;
        EvaluateTrackPoseAtDistance(StartX, StartTrack, IgnoredRotation);
        EvaluateTrackPoseAtDistance(EndX, EndTrack, IgnoredRotation);
        for (const float Y : {-RailOffsetYCm, RailOffsetYCm})
            AddRailBetween(FVector(StartX, Y, StartTrack.Z), FVector(EndX, Y, EndTrack.Z));
    }
    // Drain/oven imports already contain their high-level straight carrier rails. Supply
    // straight fallback rails only for unresolved modules so visuals never double up.
    for (int32 BayIndex = TreatmentBayCount; BayIndex < TotalBayCount; ++BayIndex)
    {
        if (HasImportedModuleForBay(BayIndex)) continue;
        const FLBECoatBayDescriptor& Bay = BayDescriptors[BayIndex];
        for (const float Y : {-RailOffsetYCm, RailOffsetYCm})
            AddRailBetween(FVector(Bay.StartXCm, Y, RailHeightCm),
                FVector(Bay.EndXCm, Y, RailHeightCm));
    }
    LBECoatLinePrivate::SetFallbackColour(RailInstances,
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("182027"))));

    UStaticMesh* DrainMesh = ResolveMesh(DrainInspectionMesh);
    DrainInspectionPresentation->SetStaticMesh(DrainMesh);
    DrainInspectionPresentation->SetVisibility(DrainMesh != nullptr);
    DrainInspectionPresentation->SetRelativeTransform(FTransform(FVector(11250.0f, 0.0f, 0.0f)));

    UStaticMesh* EntryMesh = ResolveMesh(OvenEntryMesh);
    OvenEntryPresentation->SetStaticMesh(EntryMesh);
    OvenEntryPresentation->SetVisibility(EntryMesh != nullptr);
    OvenEntryPresentation->SetRelativeTransform(FTransform(FVector(12150.0f, 0.0f, 0.0f)));

    UStaticMesh* ProcessMesh = ResolveMesh(OvenProcessBayMesh);
    OvenProcessInstances->SetStaticMesh(ProcessMesh);
    OvenProcessInstances->SetVisibility(ProcessMesh != nullptr);
    if (ProcessMesh)
        for (int32 Index = 0; Index < OvenProcessBayCount; ++Index)
            OvenProcessInstances->AddInstance(FTransform(FVector(13050.0f + Index * ModulePitchCm, 0.0f, 0.0f)));

    UStaticMesh* ExitMesh = ResolveMesh(OvenExitMesh);
    OvenExitPresentation->SetStaticMesh(ExitMesh);
    OvenExitPresentation->SetVisibility(ExitMesh != nullptr);
    OvenExitPresentation->SetRelativeTransform(FTransform(FVector(18450.0f, 0.0f, 0.0f)));

    OvenFallbackInstances->SetStaticMesh(CubeFallbackMesh);
    auto AddFallbackOvenBay = [this](const int32 BayIndex)
    {
        const float X = (BayDescriptors[BayIndex].StartXCm + BayDescriptors[BayIndex].EndXCm) * 0.5f;
        AddBoxInstance(OvenFallbackInstances, FVector(X, -320.0f, 410.0f), FVector(900.0f, 35.0f, 820.0f));
        AddBoxInstance(OvenFallbackInstances, FVector(X, 320.0f, 410.0f), FVector(900.0f, 35.0f, 820.0f));
        AddBoxInstance(OvenFallbackInstances, FVector(X, 0.0f, 820.0f), FVector(900.0f, 675.0f, 35.0f));
    };
    if (!EntryMesh) AddFallbackOvenBay(7);
    if (!ProcessMesh)
        for (int32 Index = 8; Index <= 13; ++Index) AddFallbackOvenBay(Index);
    if (!ExitMesh) AddFallbackOvenBay(14);
    LBECoatLinePrivate::SetFallbackColour(OvenFallbackInstances,
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("59666A"))));

    if (UStaticMesh* DoorMesh = ResolveMesh(OvenServiceDoorMesh))
    {
        OvenServiceDoorInstances->SetStaticMesh(DoorMesh);
        OvenServiceDoorInstances->SetVisibility(true);
        for (int32 Index = 0; Index < OvenVisualModuleCount; ++Index)
        {
            const float CentreX = OvenSectionStartCm + (Index + 0.5f) * ModulePitchCm;
            OvenServiceDoorInstances->AddInstance(FTransform(FVector(
                CentreX - 77.5f, 424.5f, 205.0f)));
        }
    }
    else OvenServiceDoorInstances->SetVisibility(false);

    if (UStaticMesh* HousingMesh = ResolveMesh(OvenServiceLightHousingMesh))
    {
        OvenServiceLightHousingInstances->SetStaticMesh(HousingMesh);
        OvenServiceLightHousingInstances->SetVisibility(true);
        for (int32 Index = 0; Index < OvenVisualModuleCount; ++Index)
        {
            const float CentreX = OvenSectionStartCm + (Index + 0.5f) * ModulePitchCm;
            OvenServiceLightHousingInstances->AddInstance(FTransform(FVector(CentreX, 355.0f, 670.0f)));
            OvenServiceLightHousingInstances->AddInstance(FTransform(FVector(CentreX, -355.0f, 670.0f)));
        }
    }
    else OvenServiceLightHousingInstances->SetVisibility(false);

    UStaticMesh* FanHousingMesh = ResolveMesh(OvenFanMesh);
    OvenFanHousingInstances->SetStaticMesh(FanHousingMesh);
    OvenFanHousingInstances->SetVisibility(FanHousingMesh != nullptr);
    if (FanHousingMesh)
        for (int32 Index = 0; Index < OvenVisualModuleCount; ++Index)
            OvenFanHousingInstances->AddInstance(FTransform(FVector(
                OvenSectionStartCm + (Index + 0.5f) * ModulePitchCm, 0.0f, 925.0f)));

    UStaticMesh* FanRotorMesh = ResolveMesh(OvenFanRotorMesh);
    for (int32 Index = 0; Index < OvenFans.Num(); ++Index)
    {
        UStaticMeshComponent* Fan = OvenFans[Index];
        Fan->SetStaticMesh(FanRotorMesh ? FanRotorMesh : CubeFallbackMesh.Get());
        Fan->SetRelativeLocation(FVector(OvenSectionStartCm + (Index + 0.5f) * ModulePitchCm,
            0.0f, 970.0f));
        Fan->SetRelativeScale3D(FanRotorMesh ? FVector::OneVector : FVector(2.4f, 0.18f, 0.12f));
        Fan->SetRelativeRotation(FRotator(0.0f, FanRotationDegrees + Index * 17.0f, 0.0f));
        Fan->SetVisibility(true);
        if (!FanRotorMesh)
            LBECoatLinePrivate::SetFallbackColour(Fan,
                FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("C8D2D8"))));
    }

    UStaticMesh* BaseMesh = ResolveMesh(BeaconBaseMesh);
    UStaticMesh* GreenMesh = ResolveMesh(BeaconGreenLensMesh);
    UStaticMesh* AmberMesh = ResolveMesh(BeaconAmberLensMesh);
    UStaticMesh* RedMesh = ResolveMesh(BeaconRedLensMesh);
    UHierarchicalInstancedStaticMeshComponent* BeaconLayers[] = {
        BeaconBaseInstances, BeaconGreenLensInstances, BeaconAmberLensInstances, BeaconRedLensInstances
    };
    UStaticMesh* BeaconMeshes[] = { BaseMesh, GreenMesh, AmberMesh, RedMesh };
    for (int32 Layer = 0; Layer < UE_ARRAY_COUNT(BeaconLayers); ++Layer)
    {
        BeaconLayers[Layer]->SetStaticMesh(BeaconMeshes[Layer]);
        BeaconLayers[Layer]->SetVisibility(BeaconMeshes[Layer] != nullptr);
        if (!BeaconMeshes[Layer]) continue;
        BeaconLayers[Layer]->AddInstance(FTransform(FVector(12150.0f, 355.0f, 861.0f)));
        BeaconLayers[Layer]->AddInstance(FTransform(FVector(18450.0f, 355.0f, 861.0f)));
    }
    const bool bHasCompleteImportedBeacon = BaseMesh && GreenMesh && AmberMesh && RedMesh;
    EntryBeacon->SetGeneratedLampHeadsVisible(!bHasCompleteImportedBeacon);
    ExitBeacon->SetGeneratedLampHeadsVisible(!bHasCompleteImportedBeacon);

    if (FloorMarkings)
    {
        FloorMarkings->ClearMarkings();
        FloorMarkings->AddRectangleOutline(FVector2D(TotalLengthCm * 0.5f, 0.0f),
            FVector2D(TotalLengthCm * 0.5f, 650.0f), 0.8f, 12.0f,
            ELBFactoryFloorMarkingSemantic::ServiceEnvelope, 1.0f);
        for (int32 Index = 0; Index < TreatmentBayCount; ++Index)
        {
            const FLBECoatBayDescriptor& Bay = BayDescriptors[Index];
            const float X = (Bay.StartXCm + Bay.EndXCm) * 0.5f;
            FloorMarkings->AddDiagonalHatching(FVector2D(X, -520.0f), FVector2D(840.0f, 95.0f),
                0.5f, 14.0f, 68.0f, ELBFactoryFloorMarkingSemantic::KeepClearHatch, 0.8f);
            FloorMarkings->AddDiagonalHatching(FVector2D(X, 520.0f), FVector2D(840.0f, 95.0f),
                0.5f, 14.0f, 68.0f, ELBFactoryFloorMarkingSemantic::KeepClearHatch, 0.8f);
        }
        for (const float X : {OvenSectionStartCm, TotalLengthCm})
            FloorMarkings->AddDiagonalHatching(FVector2D(X, 0.0f), FVector2D(210.0f, 610.0f),
                0.5f, 14.0f, 68.0f, ELBFactoryFloorMarkingSemantic::KeepClearHatch, 0.8f);
    }

    for (int32 Index = 0; Index < TreatmentBayCount; ++Index) RefreshLiquidSurface(Index);
    RefreshOperationalPresentation();
    RefreshAllCarrierPresentations();
}

bool ALBECoatLineActor::SetOperatingState(const ELBECoatOperatingState NewState, const FName Reason)
{
    if (OperatingState == NewState && StateReason == Reason) return false;
    const ELBECoatOperatingState Previous = OperatingState;
    OperatingState = NewState;
    StateReason = Reason;
    RefreshOperationalPresentation();
    OnOperatingStateChanged.Broadcast(Previous, OperatingState, StateReason);
    return true;
}

void ALBECoatLineActor::RefreshOperationalPresentation()
{
    ELBStatusBeaconState BeaconState = ELBStatusBeaconState::Stopped;
    float LightFactor = 0.25f;
    FLinearColor PortalColour = FLinearColor(0.72f, 0.82f, 0.88f, 1.0f);
    switch (OperatingState)
    {
    case ELBECoatOperatingState::Starting:
        BeaconState = ELBStatusBeaconState::Waiting;
        LightFactor = 0.65f;
        PortalColour = FLinearColor(1.0f, 0.42f, 0.04f, 1.0f);
        break;
    case ELBECoatOperatingState::Running:
        BeaconState = ELBStatusBeaconState::Running;
        LightFactor = 1.0f;
        PortalColour = FLinearColor(0.30f, 1.0f, 0.48f, 1.0f);
        break;
    case ELBECoatOperatingState::Paused:
        BeaconState = ELBStatusBeaconState::Idle;
        LightFactor = 0.55f;
        PortalColour = FLinearColor(1.0f, 0.42f, 0.04f, 1.0f);
        break;
    case ELBECoatOperatingState::Starved:
        BeaconState = ELBStatusBeaconState::Waiting;
        LightFactor = 0.55f;
        PortalColour = FLinearColor(1.0f, 0.42f, 0.04f, 1.0f);
        break;
    case ELBECoatOperatingState::Faulted:
        BeaconState = ELBStatusBeaconState::Fault;
        LightFactor = 0.70f;
        PortalColour = FLinearColor(1.0f, 0.04f, 0.02f, 1.0f);
        break;
    case ELBECoatOperatingState::Maintenance:
        BeaconState = ELBStatusBeaconState::Idle;
        LightFactor = 1.0f;
        PortalColour = FLinearColor(1.0f, 0.64f, 0.16f, 1.0f);
        break;
    case ELBECoatOperatingState::EmergencyStop:
        BeaconState = ELBStatusBeaconState::Emergency;
        LightFactor = 0.45f;
        PortalColour = FLinearColor(1.0f, 0.02f, 0.01f, 1.0f);
        break;
    case ELBECoatOperatingState::Stopped:
    default:
        break;
    }

    if (EntryBeacon) EntryBeacon->SetStatus(BeaconState);
    if (ExitBeacon) ExitBeacon->SetStatus(BeaconState);

    const FLinearColor TreatmentColour(0.72f, 0.91f, 1.0f, 1.0f);
    for (UPointLightComponent* Light : TreatmentServiceLights)
    {
        if (!Light) continue;
        Light->SetLightColor(TreatmentColour);
        Light->SetIntensity(1250.0f * LightFactor);
        Light->SetVisibility(true);
    }
    const FLinearColor OvenColour(1.0f, 0.73f, 0.40f, 1.0f);
    for (URectLightComponent* Light : OvenInteriorLights)
    {
        if (!Light) continue;
        Light->SetLightColor(OvenColour);
        Light->SetIntensity(2600.0f * LightFactor);
        Light->SetVisibility(true);
    }
    for (USpotLightComponent* Light : PortalSpotLights)
    {
        if (!Light) continue;
        Light->SetLightColor(PortalColour);
        Light->SetIntensity(2200.0f * LightFactor);
        Light->SetVisibility(true);
    }

    const bool bGreenActive = BeaconState == ELBStatusBeaconState::Ready
        || BeaconState == ELBStatusBeaconState::Running;
    const bool bAmberActive = BeaconState == ELBStatusBeaconState::Idle
        || BeaconState == ELBStatusBeaconState::Waiting || BeaconState == ELBStatusBeaconState::Moving;
    const bool bRedActive = BeaconState == ELBStatusBeaconState::Stopped
        || BeaconState == ELBStatusBeaconState::Fault || BeaconState == ELBStatusBeaconState::Emergency;
    LBECoatLinePrivate::SetFallbackColour(BeaconGreenLensInstances,
        FLinearColor(0.03f, bGreenActive ? 1.0f : 0.10f, 0.18f, 1.0f));
    LBECoatLinePrivate::SetFallbackColour(BeaconAmberLensInstances,
        FLinearColor(bAmberActive ? 1.0f : 0.10f, bAmberActive ? 0.34f : 0.04f, 0.015f, 1.0f));
    LBECoatLinePrivate::SetFallbackColour(BeaconRedLensInstances,
        FLinearColor(bRedActive ? 1.0f : 0.10f, 0.015f, 0.01f, 1.0f));
}

bool ALBECoatLineActor::AreOperationalLightsRegisteredAndVisible() const
{
    if (TreatmentServiceLights.Num() != TreatmentBayCount * TreatmentModulesPerBay
        || OvenInteriorLights.Num() != OvenVisualModuleCount
        || PortalSpotLights.Num() != 2) return false;
    for (const UPointLightComponent* Light : TreatmentServiceLights)
        if (!Light || !Light->IsRegistered() || !Light->IsVisible()) return false;
    for (const URectLightComponent* Light : OvenInteriorLights)
        if (!Light || !Light->IsRegistered() || !Light->IsVisible()) return false;
    for (const USpotLightComponent* Light : PortalSpotLights)
        if (!Light || !Light->IsRegistered() || !Light->IsVisible()) return false;
    return true;
}

int32 ALBECoatLineActor::GetBuiltTreatmentVisualInstanceCount() const
{
    const int32 StartCount = TreatmentModuleInstances
        ? TreatmentModuleInstances->GetInstanceCount() : 0;
    const int32 EndCount = TreatmentEndModuleInstances
        ? TreatmentEndModuleInstances->GetInstanceCount() : 0;
    return StartCount + EndCount;
}

int32 ALBECoatLineActor::GetBuiltRailSegmentInstanceCount() const
{
    return RailInstances ? RailInstances->GetInstanceCount() : 0;
}

void ALBECoatLineActor::AdvanceFanPresentation(const float DeltaSeconds)
{
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.0f
        || OperatingState != ELBECoatOperatingState::Running) return;
    FanRotationDegrees = FMath::Fmod(FanRotationDegrees + DeltaSeconds * 180.0f, 360.0f);
    for (int32 Index = 0; Index < OvenFans.Num(); ++Index)
        if (OvenFans[Index]) OvenFans[Index]->SetRelativeRotation(
            FRotator(0.0f, FanRotationDegrees + Index * 17.0f, 0.0f));
}

bool ALBECoatLineActor::SetBayOperatingState(const int32 BayIndex, const bool bEnabled,
    const bool bFaulted, const bool bStarved, const float ProcessValue01, const float TemperatureC)
{
    if (!BayOperatingStates.IsValidIndex(BayIndex) || !FMath::IsFinite(ProcessValue01)
        || !FMath::IsFinite(TemperatureC)) return false;
    FLBECoatBayOperatingState& State = BayOperatingStates[BayIndex];
    State.bEnabled = bEnabled;
    State.bFaulted = bFaulted;
    State.bStarved = bStarved;
    State.ProcessValue01 = FMath::Clamp(ProcessValue01, 0.0f, 1.0f);
    State.TemperatureC = TemperatureC;
    OnBayStateChanged.Broadcast(BayIndex, BayDescriptors[BayIndex].BayType,
        State.bEnabled, State.bFaulted, State.bStarved);

    bool bAnyFaulted = false;
    bool bAnyStarved = false;
    int32 FirstFaultedBay = INDEX_NONE;
    int32 FirstStarvedBay = INDEX_NONE;
    for (const FLBECoatBayOperatingState& BayState : BayOperatingStates)
    {
        if (BayState.bFaulted && FirstFaultedBay == INDEX_NONE) FirstFaultedBay = BayState.BayIndex;
        if (BayState.bStarved && FirstStarvedBay == INDEX_NONE) FirstStarvedBay = BayState.BayIndex;
        bAnyFaulted |= BayState.bFaulted;
        bAnyStarved |= BayState.bStarved;
    }
    if (OperatingState != ELBECoatOperatingState::EmergencyStop && bAnyFaulted)
    {
        const FName FaultReason = BayDescriptors.IsValidIndex(FirstFaultedBay)
            ? FName(*FString::Printf(TEXT("%s_FAULT"),
                *BayDescriptors[FirstFaultedBay].BayId.ToString())) : FName(TEXT("PROCESS_BAY_FAULT"));
        SetOperatingState(ELBECoatOperatingState::Faulted, FaultReason);
    }
    else if (OperatingState != ELBECoatOperatingState::EmergencyStop
        && OperatingState != ELBECoatOperatingState::Faulted && bAnyStarved)
    {
        const FName StarvedReason = BayDescriptors.IsValidIndex(FirstStarvedBay)
            ? FName(*FString::Printf(TEXT("%s_STARVED"),
                *BayDescriptors[FirstStarvedBay].BayId.ToString())) : FName(TEXT("PROCESS_BAY_STARVED"));
        SetOperatingState(ELBECoatOperatingState::Starved, StarvedReason);
    }
    return true;
}

bool ALBECoatLineActor::SetLiquidLevel01(const int32 TreatmentBayIndex, const float NewLevel01)
{
    if (!FMath::IsWithinInclusive(TreatmentBayIndex, 0, TreatmentBayCount - 1)
        || !FMath::IsFinite(NewLevel01)) return false;
    BayOperatingStates[TreatmentBayIndex].LiquidLevel01 = FMath::Clamp(NewLevel01, 0.0f, 1.0f);
    RefreshLiquidSurface(TreatmentBayIndex);
    return true;
}

void ALBECoatLineActor::RefreshLiquidSurface(const int32 TreatmentBayIndex)
{
    if (!LiquidSurfaces.IsValidIndex(TreatmentBayIndex)
        || !BayOperatingStates.IsValidIndex(TreatmentBayIndex)) return;
    UStaticMeshComponent* Surface = LiquidSurfaces[TreatmentBayIndex];
    UStaticMesh* Mesh = ResolveMesh(LiquidSurfaceMesh);
    const bool bUsingFallback = Mesh == nullptr;
    if (bUsingFallback) Mesh = CubeFallbackMesh;
    Surface->SetStaticMesh(Mesh);
    const float Level = BayOperatingStates[TreatmentBayIndex].LiquidLevel01;
    Surface->SetVisibility(Level > KINDA_SMALL_NUMBER && Mesh != nullptr);
    const FLBECoatBayDescriptor& Bay = BayDescriptors[TreatmentBayIndex];
    Surface->SetRelativeLocation(FVector((Bay.StartXCm + Bay.EndXCm) * 0.5f, 0.0f,
        FMath::Lerp(45.0f, LiquidSurfaceZCm, Level)));
    Surface->SetRelativeRotation(FRotator::ZeroRotator);
    Surface->SetRelativeScale3D(bUsingFallback ? FVector(16.3f, 4.7f, 0.04f)
        : FVector(2.0f, 1.0f, 1.0f));

    static const FColor ProcessColours[TreatmentBayCount] = {
        FColor::FromHex(TEXT("72C4B8")), FColor::FromHex(TEXT("71C8E4")),
        FColor::FromHex(TEXT("C7A65A")), FColor::FromHex(TEXT("75CDE4")),
        FColor::FromHex(TEXT("5DA9A4")), FColor::FromHex(TEXT("8BD2E1"))
    };
    UMaterialInterface* ProcessMaterial = TreatmentLiquidMaterials.IsValidIndex(TreatmentBayIndex)
        ? ResolveMaterial(TreatmentLiquidMaterials[TreatmentBayIndex]) : nullptr;
    if (ProcessMaterial) Surface->SetMaterial(0, ProcessMaterial);
    else LBECoatLinePrivate::SetFallbackColour(Surface,
        FLinearColor::FromSRGBColor(ProcessColours[TreatmentBayIndex]));
}

bool ALBECoatLineActor::EvaluateCarrierPoseAtDistance(const float DistanceCm,
    FLBECoatCarrierPose& OutPose) const
{
    if (!FMath::IsFinite(DistanceCm)) return false;
    const float Distance = FMath::Clamp(DistanceCm, 0.0f, TotalLengthCm);
    OutPose = FLBECoatCarrierPose();
    OutPose.DistanceCm = Distance;
    if (!EvaluateTrackPoseAtDistance(Distance, OutPose.TrolleyRootLocationCm,
        OutPose.TrolleyRotation)) return false;
    OutPose.BodyRootLocationCm = FVector(Distance, 0.0f,
        DryBodyRootZCm + OutPose.TrolleyRootLocationCm.Z - RailHeightCm);

    if (FMath::IsNearlyEqual(Distance, TotalLengthCm, KINDA_SMALL_NUMBER))
    {
        OutPose.BayIndex = TotalBayCount - 1;
        OutPose.Stage = ELBECoatCarrierStage::Complete;
        return true;
    }

    OutPose.BayIndex = FindBayIndexAtDistance(Distance);
    if (!BayDescriptors.IsValidIndex(OutPose.BayIndex)) return false;
    const FLBECoatBayDescriptor& Bay = BayDescriptors[OutPose.BayIndex];
    const float LocalX = FMath::Clamp(Distance - Bay.StartXCm, 0.0f,
        Bay.EndXCm - Bay.StartXCm);

    if (OutPose.BayIndex < TreatmentBayCount)
    {
        if (LocalX <= 300.0f) OutPose.Stage = ELBECoatCarrierStage::DryTravel;
        else if (LocalX < 750.0f) OutPose.Stage = ELBECoatCarrierStage::Descending;
        else if (LocalX <= 1050.0f) OutPose.Stage = ELBECoatCarrierStage::Immersed;
        else if (LocalX < 1500.0f) OutPose.Stage = ELBECoatCarrierStage::Rising;
        else OutPose.Stage = ELBECoatCarrierStage::Draining;

        OutPose.Immersion01 = FMath::Clamp((RailHeightCm
            - OutPose.TrolleyRootLocationCm.Z) / (RailHeightCm - TreatmentLowRailHeightCm),
            0.0f, 1.0f);
        // The bogies follow the full track tangent. The sprung lower hanger follows more
        // gently, which reads as heavy automotive tooling instead of a rigid rollercoaster car.
        OutPose.BodyRotation = FRotator(FMath::Clamp(
            OutPose.TrolleyRotation.Pitch * 0.65f, -18.0f, 18.0f), 0.0f, 0.0f);
    }
    else if (OutPose.BayIndex == 6)
    {
        OutPose.Stage = ELBECoatCarrierStage::Draining;
    }
    else if (OutPose.BayIndex == 7)
    {
        OutPose.Stage = ELBECoatCarrierStage::OvenEntry;
    }
    else if (OutPose.BayIndex <= 13)
    {
        OutPose.Stage = ELBECoatCarrierStage::OvenCure;
    }
    else
    {
        OutPose.Stage = ELBECoatCarrierStage::OvenExit;
    }
    return true;
}

int32 ALBECoatLineActor::FindCarrierIndex(const FName CarrierId) const
{
    return Carriers.IndexOfByPredicate([CarrierId](const FLBECoatCarrierRuntimeEntry& Carrier)
    {
        return Carrier.State.CarrierId == CarrierId;
    });
}

bool ALBECoatLineActor::AddCarrier(const FName CarrierId, const float InitialDistanceCm)
{
    if (CarrierId.IsNone() || !FMath::IsFinite(InitialDistanceCm)
        || FindCarrierIndex(CarrierId) != INDEX_NONE) return false;
    FLBECoatCarrierRuntimeEntry& Carrier = Carriers.AddDefaulted_GetRef();
    Carrier.State.CarrierId = CarrierId;
    Carrier.State.DistanceCm = FMath::Clamp(InitialDistanceCm, 0.0f, TotalLengthCm);
    Carrier.State.bEnabled = true;
    CreateCarrierPresentation(Carrier);
    RefreshCarrierPresentation(Carrier);
    return true;
}

bool ALBECoatLineActor::AcceptAndAcknowledgeBodyInWhite(ALBBodyWeldLineActor* SourceLine,
    const FName BodyId, const FName CarrierId, FString& OutReason)
{
    OutReason.Reset();
    if (!SourceLine)
    {
        OutReason = TEXT("WELD_SOURCE_REQUIRED");
        return false;
    }
    if (BodyId.IsNone() || CarrierId.IsNone())
    {
        OutReason = TEXT("BODY_AND_CARRIER_IDS_REQUIRED");
        return false;
    }
    if (!InputPort || InputPort->Direction != ELBFactoryPortDirection::Input
        || InputPort->TransportKind != ELBFactoryTransportKind::PanelTransfer
        || InputPort->MaterialClass != ELBFactoryMaterialClass::BodyInWhite
        || InputPort->ProcessStage != LBFactoryProcessStage::ECoat)
    {
        OutReason = TEXT("ED_INPUT_CONTRACT_INVALID");
        return false;
    }
    ULBFactoryProcessPortComponent* SourcePort = SourceLine->GetBIWOutputPort();
    if (!SourcePort || SourcePort->Direction != ELBFactoryPortDirection::Output
        || SourcePort->TransportKind != ELBFactoryTransportKind::PanelTransfer
        || SourcePort->MaterialClass != ELBFactoryMaterialClass::BodyInWhite
        || SourcePort->ProcessStage != LBFactoryProcessStage::BodyWeld)
    {
        OutReason = TEXT("WELD_OUTPUT_CONTRACT_INVALID");
        return false;
    }

    FLBBodyInWhiteRecord Candidate;
    if (!SourceLine->GetOutputBody(Candidate) || Candidate.BodyId != BodyId)
    {
        OutReason = TEXT("BODY_NOT_READY_AT_WELD_OUTPUT");
        return false;
    }
    TArray<FName> CandidateFamilies;
    FName CandidateBaseKitTypeId;
    if (Candidate.BodyId.IsNone()
        || !LBVehicleModelCatalog::GetBodyWeldContract(
            Candidate.VehicleModelId, CandidateFamilies, CandidateBaseKitTypeId)
        || Candidate.OrderId.IsNone() || Candidate.BaseKitId.IsNone()
        || Candidate.ReservationId.IsNone() || Candidate.WeldLineId.IsNone()
        || Candidate.QualityState != ELBBodyWeldQualityState::Good
        || Candidate.bEDAccepted
        || Candidate.Panels.Num() != CandidateFamilies.Num()
        || !FMath::IsFinite(Candidate.CycleEvidence.ClosurePreparationSeconds)
        || !FMath::IsFinite(Candidate.CycleEvidence.FramingSeconds)
        || !FMath::IsFinite(Candidate.CycleEvidence.WeldingSeconds)
        || !FMath::IsFinite(Candidate.CycleEvidence.GeometryCheckSeconds)
        || Candidate.CycleEvidence.CompletionSequence <= 0)
    {
        OutReason = TEXT("BODY_LINEAGE_OR_QUALITY_INVALID");
        return false;
    }

    TSet<FName> PanelIds;
    TSet<FName> LineageFamilies;
    for (const FLBBodyWeldPanelLineage& Panel : Candidate.Panels)
    {
        FName ParsedVehicle;
        FName ParsedFamily;
        if (Panel.PanelId.IsNone() || Panel.PanelTypeId.IsNone() || Panel.StillageId.IsNone()
            || PanelIds.Contains(Panel.PanelId) || LineageFamilies.Contains(Panel.PanelTypeId)
            || !LBCairnwell2040PanelCatalog::ParsePressedPanelUnitId(
                Panel.PanelId, ParsedVehicle, ParsedFamily)
            || ParsedVehicle != Candidate.VehicleModelId || ParsedFamily != Panel.PanelTypeId
            || !CandidateFamilies.Contains(Panel.PanelTypeId))
        {
            OutReason = TEXT("PANEL_LINEAGE_INVALID");
            return false;
        }
        PanelIds.Add(Panel.PanelId);
        LineageFamilies.Add(Panel.PanelTypeId);
    }
    if (FindCarrierIndex(CarrierId) != INDEX_NONE)
    {
        OutReason = TEXT("CARRIER_ID_ALREADY_EXISTS");
        return false;
    }
    if (Carriers.ContainsByPredicate([BodyId](const FLBECoatCarrierRuntimeEntry& Carrier)
        { return Carrier.State.bHasBodyInWhite && Carrier.State.BodyInWhite.BodyId == BodyId; }))
    {
        OutReason = TEXT("BODY_ALREADY_ACCEPTED_BY_ED");
        return false;
    }

    const int32 OriginalCarrierCount = Carriers.Num();
    const bool bOriginalEDAvailable = SourceLine->IsEDAvailable();
    FLBECoatCarrierRuntimeEntry& Carrier = Carriers.AddDefaulted_GetRef();
    Carrier.State.CarrierId = CarrierId;
    Carrier.State.DistanceCm = 0.0f;
    Carrier.State.bEnabled = true;
    Carrier.State.bHasBodyInWhite = true;
    Carrier.State.BodyInWhite = Candidate;
    Carrier.State.BodyInWhite.bEDAccepted = false;

    SourceLine->SetEDAvailable(true);
    FLBBodyInWhiteRecord Acknowledged;
    const bool bAcknowledged = SourceLine->AcknowledgeEDTransfer(BodyId, Acknowledged);
    if (!bAcknowledged)
    {
        Carriers.SetNum(OriginalCarrierCount, EAllowShrinking::No);
        SourceLine->SetEDAvailable(bOriginalEDAvailable);
        OutReason = TEXT("WELD_ACKNOWLEDGEMENT_FAILED");
        return false;
    }

    // AcknowledgeEDTransfer returns the exact OutputBody copy after setting only
    // bEDAccepted. The source API has no fallible transformation after its commit point,
    // so validation belongs before that call and success can be consumed without a second
    // rejection branch that would make a two-actor rollback impossible.
    check(Acknowledged.bEDAccepted && Acknowledged.BodyId == Candidate.BodyId
        && Acknowledged.VehicleModelId == Candidate.VehicleModelId
        && Acknowledged.OrderId == Candidate.OrderId
        && Acknowledged.BaseKitId == Candidate.BaseKitId
        && Acknowledged.ReservationId == Candidate.ReservationId
        && Acknowledged.WeldLineId == Candidate.WeldLineId
        && Acknowledged.QualityState == Candidate.QualityState
        && Acknowledged.Panels.Num() == Candidate.Panels.Num());
    for (int32 PanelIndex = 0; PanelIndex < Candidate.Panels.Num(); ++PanelIndex)
    {
        check(Acknowledged.Panels[PanelIndex].PanelId == Candidate.Panels[PanelIndex].PanelId
            && Acknowledged.Panels[PanelIndex].PanelTypeId
                == Candidate.Panels[PanelIndex].PanelTypeId
            && Acknowledged.Panels[PanelIndex].StillageId
                == Candidate.Panels[PanelIndex].StillageId);
    }
    Carrier.State.BodyInWhite = Acknowledged;
    CreateCarrierPresentation(Carrier);
    RefreshCarrierPresentation(Carrier);
    OutReason = TEXT("ACCEPTED");
    return true;
}

bool ALBECoatLineActor::RemoveCarrier(const FName CarrierId)
{
    const int32 Index = FindCarrierIndex(CarrierId);
    if (!Carriers.IsValidIndex(Index)) return false;
    DestroyCarrierPresentation(Carriers[Index]);
    Carriers.RemoveAt(Index);
    return true;
}

void ALBECoatLineActor::ClearCarriers()
{
    for (FLBECoatCarrierRuntimeEntry& Carrier : Carriers) DestroyCarrierPresentation(Carrier);
    Carriers.Reset();
}

bool ALBECoatLineActor::SetCarrierProgress(const FName CarrierId, const float DistanceCm)
{
    const int32 Index = FindCarrierIndex(CarrierId);
    if (!Carriers.IsValidIndex(Index) || !FMath::IsFinite(DistanceCm)) return false;
    Carriers[Index].State.DistanceCm = FMath::Clamp(DistanceCm, 0.0f, TotalLengthCm);
    RefreshCarrierPresentation(Carriers[Index]);
    return true;
}

bool ALBECoatLineActor::CanCarrierAdvance(const FLBECoatCarrierRuntimeEntry& Carrier) const
{
    FLBECoatCarrierPose Pose;
    return Carrier.State.bEnabled && Carrier.State.bHasBodyInWhite
        && EvaluateCarrierPoseAtDistance(Carrier.State.DistanceCm, Pose)
        && BayOperatingStates.IsValidIndex(Pose.BayIndex)
        && LBECoatLinePrivate::IsBayAvailable(BayOperatingStates[Pose.BayIndex]);
}

void ALBECoatLineActor::AdvanceSimulation(const float DeltaSeconds)
{
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.0f
        || OperatingState != ELBECoatOperatingState::Running) return;
    AdvanceFanPresentation(DeltaSeconds);
    const float TravelCm = FMath::Max(1.0f, TargetLineSpeedCmPerSecond) * DeltaSeconds;
    for (FLBECoatCarrierRuntimeEntry& Carrier : Carriers)
    {
        if (!CanCarrierAdvance(Carrier)) continue;
        const float StartDistance = Carrier.State.DistanceCm;
        float ProposedDistance = StartDistance + TravelCm;
        if (bLoopCarriers && ProposedDistance >= TotalLengthCm)
            ProposedDistance = FMath::Fmod(ProposedDistance, TotalLengthCm);
        else
            ProposedDistance = FMath::Min(ProposedDistance, TotalLengthCm);

        auto StopAtFirstUnavailableBoundary = [this](const float SegmentStart,
            const float SegmentEnd, float& InOutDistance)
        {
            const int32 StartBay = FindBayIndexAtDistance(SegmentStart);
            if (!BayDescriptors.IsValidIndex(StartBay)) return false;
            for (int32 BayIndex = StartBay + 1; BayIndex < TotalBayCount; ++BayIndex)
            {
                const FLBECoatBayDescriptor& Bay = BayDescriptors[BayIndex];
                if (Bay.StartXCm > SegmentEnd + KINDA_SMALL_NUMBER) break;
                if (!LBECoatLinePrivate::IsBayAvailable(BayOperatingStates[BayIndex]))
                {
                    InOutDistance = Bay.StartXCm;
                    return true;
                }
            }
            return false;
        };

        if (ProposedDistance >= StartDistance)
        {
            StopAtFirstUnavailableBoundary(StartDistance, ProposedDistance, ProposedDistance);
        }
        else if (bLoopCarriers)
        {
            float BeforeWrapDistance = TotalLengthCm;
            if (StopAtFirstUnavailableBoundary(StartDistance, TotalLengthCm, BeforeWrapDistance))
            {
                ProposedDistance = BeforeWrapDistance;
            }
            else if (!LBECoatLinePrivate::IsBayAvailable(BayOperatingStates[0]))
            {
                ProposedDistance = 0.0f;
            }
            else
            {
                StopAtFirstUnavailableBoundary(0.0f, ProposedDistance, ProposedDistance);
            }
        }

        Carrier.State.DistanceCm = ProposedDistance;
        if (!bLoopCarriers && FMath::IsNearlyEqual(ProposedDistance, TotalLengthCm, KINDA_SMALL_NUMBER))
            Carrier.State.bEnabled = false;
        RefreshCarrierPresentation(Carrier);
    }
}

void ALBECoatLineActor::CreateCarrierPresentation(FLBECoatCarrierRuntimeEntry& Carrier)
{
    const FString SafeId = Carrier.State.CarrierId.ToString().Replace(TEXT(" "), TEXT("_"));
    Carrier.PresentationRoot = NewObject<USceneComponent>(this,
        MakeUniqueObjectName(this, USceneComponent::StaticClass(),
            FName(*FString::Printf(TEXT("Carrier_%s"), *SafeId))));
    Carrier.PresentationRoot->SetupAttachment(SceneRoot);
    AddInstanceComponent(Carrier.PresentationRoot);
    Carrier.PresentationRoot->RegisterComponent();

    auto CreateMeshPart = [this, &Carrier, &SafeId](const TCHAR* PartName)
    {
        UStaticMeshComponent* Part = NewObject<UStaticMeshComponent>(this,
            MakeUniqueObjectName(this, UStaticMeshComponent::StaticClass(),
                FName(*FString::Printf(TEXT("Carrier_%s_%s"), *SafeId, PartName))));
        Part->SetupAttachment(Carrier.PresentationRoot);
        Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Part->SetCanEverAffectNavigation(false);
        AddInstanceComponent(Part);
        Part->RegisterComponent();
        return Part;
    };

    Carrier.Trolley = CreateMeshPart(TEXT("Trolley"));
    Carrier.Hoist = CreateMeshPart(TEXT("Hoist"));
    Carrier.Hanger = CreateMeshPart(TEXT("Hanger"));
    Carrier.VehicleBody = CreateMeshPart(TEXT("VehicleBody"));

    UStaticMesh* TrolleyMesh = ResolveMesh(CarrierTrolleyMesh);
    Carrier.Trolley->SetStaticMesh(TrolleyMesh ? TrolleyMesh : CubeFallbackMesh.Get());
    UStaticMesh* HoistMesh = ResolveMesh(CarrierHoistMesh);
    Carrier.Hoist->SetStaticMesh(HoistMesh ? HoistMesh : CubeFallbackMesh.Get());
    UStaticMesh* HangerMesh = ResolveMesh(CarrierHangerMesh);
    Carrier.Hanger->SetStaticMesh(HangerMesh ? HangerMesh : CubeFallbackMesh.Get());
    UStaticMesh* BodyMesh = ResolveMesh(VehicleShellMesh);
    Carrier.VehicleBody->SetStaticMesh(BodyMesh ? BodyMesh : CubeFallbackMesh.Get());

    if (!TrolleyMesh)
        LBECoatLinePrivate::SetFallbackColour(Carrier.Trolley,
            FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("222A31"))));
    if (!HoistMesh)
        LBECoatLinePrivate::SetFallbackColour(Carrier.Hoist,
            FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("D9A91A"))));
    if (!HangerMesh)
        LBECoatLinePrivate::SetFallbackColour(Carrier.Hanger,
            FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("D9A91A"))));
    if (!BodyMesh)
        LBECoatLinePrivate::SetFallbackColour(Carrier.VehicleBody,
            FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("D9E1E6"))));
}

void ALBECoatLineActor::DestroyCarrierPresentation(FLBECoatCarrierRuntimeEntry& Carrier)
{
    if (Carrier.VehicleBody) Carrier.VehicleBody->DestroyComponent();
    if (Carrier.Hanger) Carrier.Hanger->DestroyComponent();
    if (Carrier.Hoist) Carrier.Hoist->DestroyComponent();
    if (Carrier.Trolley) Carrier.Trolley->DestroyComponent();
    if (Carrier.PresentationRoot) Carrier.PresentationRoot->DestroyComponent();
    Carrier.PresentationRoot = nullptr;
    Carrier.Trolley = nullptr;
    Carrier.Hoist = nullptr;
    Carrier.Hanger = nullptr;
    Carrier.VehicleBody = nullptr;
}

void ALBECoatLineActor::RefreshCarrierPresentation(FLBECoatCarrierRuntimeEntry& Carrier)
{
    if (!Carrier.PresentationRoot) CreateCarrierPresentation(Carrier);
    FLBECoatCarrierPose Pose;
    if (!EvaluateCarrierPoseAtDistance(Carrier.State.DistanceCm, Pose)) return;
    Carrier.PresentationRoot->SetRelativeLocation(FVector(Pose.BodyRootLocationCm.X, 0.0f, 0.0f));
    Carrier.PresentationRoot->SetRelativeRotation(FRotator::ZeroRotator);

    const bool bTrolleyFallback = ResolveMesh(CarrierTrolleyMesh) == nullptr;
    Carrier.Trolley->SetRelativeLocation(FVector(0.0f, 0.0f,
        Pose.TrolleyRootLocationCm.Z));
    Carrier.Trolley->SetRelativeRotation(Pose.TrolleyRotation);
    Carrier.Trolley->SetRelativeScale3D(bTrolleyFallback ? FVector(1.8f, 1.0f, 0.25f) : FVector::OneVector);

    const float LiftDeltaZ = Pose.BodyRootLocationCm.Z - DryBodyRootZCm;
    const float MovingHangerRootZ = HangerRootZCm + LiftDeltaZ;
    const bool bHoistFallback = ResolveMesh(CarrierHoistMesh) == nullptr;
    if (bHoistFallback)
    {
        // The rollercoaster rail carries the complete rigid hanger assembly down into the
        // vessel.  The short suspension link therefore keeps its authored length; it does
        // not telescope while the whole carrier follows the rail profile.
        constexpr float SuspensionLengthCm = RailHeightCm - HangerRootZCm;
        Carrier.Hoist->SetRelativeLocation(FVector(0.0f, 0.0f,
            (Pose.TrolleyRootLocationCm.Z + MovingHangerRootZ) * 0.5f));
        Carrier.Hoist->SetRelativeScale3D(FVector(0.08f, 0.08f,
            SuspensionLengthCm / 100.0f));
    }
    else
    {
        constexpr float AuthoredHoistPivotZCm = 772.0f;
        Carrier.Hoist->SetRelativeLocation(FVector(0.0f, 0.0f,
            AuthoredHoistPivotZCm + LiftDeltaZ));
        Carrier.Hoist->SetRelativeScale3D(FVector::OneVector);
    }
    Carrier.Hoist->SetRelativeRotation(Pose.BodyRotation);

    const bool bHangerFallback = ResolveMesh(CarrierHangerMesh) == nullptr;
    if (bHangerFallback)
    {
        const float HangerLength = HangerRootZCm - DryBodyRootZCm;
        Carrier.Hanger->SetRelativeLocation(FVector(0.0f, 0.0f,
            (HangerRootZCm + DryBodyRootZCm) * 0.5f + LiftDeltaZ));
        Carrier.Hanger->SetRelativeScale3D(FVector(0.12f, 0.12f, HangerLength / 100.0f));
    }
    else
    {
        Carrier.Hanger->SetRelativeLocation(FVector(0.0f, 0.0f, MovingHangerRootZ));
        Carrier.Hanger->SetRelativeScale3D(FVector::OneVector);
    }
    Carrier.Hanger->SetRelativeRotation(Pose.BodyRotation);

    const bool bBodyFallback = ResolveMesh(VehicleShellMesh) == nullptr;
    Carrier.VehicleBody->SetRelativeLocation(FVector(0.0f, 0.0f, Pose.BodyRootLocationCm.Z));
    Carrier.VehicleBody->SetRelativeRotation(Pose.BodyRotation);
    Carrier.VehicleBody->SetRelativeScale3D(bBodyFallback ? FVector(4.7f, 2.14f, 1.7f) : FVector::OneVector);
    Carrier.PresentationRoot->SetVisibility(Carrier.State.bEnabled, true);
    // Legacy v1/v2 carrier slots remain restorable as proxy-only automation data. They do
    // not receive or present a physical body until exact weld lineage is attached. Apply
    // this after root propagation so the parent cannot accidentally reveal the body child.
    Carrier.VehicleBody->SetVisibility(Carrier.State.bEnabled && Carrier.State.bHasBodyInWhite,
        false);

    if (Carrier.LastBayIndex != Pose.BayIndex || Carrier.LastStage != Pose.Stage)
    {
        const ELBECoatCarrierStage PreviousStage = Carrier.LastStage;
        Carrier.LastBayIndex = Pose.BayIndex;
        Carrier.LastStage = Pose.Stage;
        OnCarrierStageChanged.Broadcast(Carrier.State.CarrierId, Pose.BayIndex,
            PreviousStage, Pose.Stage);
    }
}

void ALBECoatLineActor::RefreshAllCarrierPresentations()
{
    for (FLBECoatCarrierRuntimeEntry& Carrier : Carriers) RefreshCarrierPresentation(Carrier);
}

bool ALBECoatLineActor::GetCarrierState(const FName CarrierId,
    FLBECoatCarrierSaveState& OutState) const
{
    const int32 Index = FindCarrierIndex(CarrierId);
    if (!Carriers.IsValidIndex(Index)) return false;
    OutState = Carriers[Index].State;
    return true;
}

bool ALBECoatLineActor::GetCarrierBodyInWhite(const FName CarrierId,
    FLBBodyInWhiteRecord& OutBody) const
{
    const int32 Index = FindCarrierIndex(CarrierId);
    if (!Carriers.IsValidIndex(Index) || !Carriers[Index].State.bHasBodyInWhite) return false;
    OutBody = Carriers[Index].State.BodyInWhite;
    return true;
}

bool ALBECoatLineActor::IsCarrierBodyPresented(const FName CarrierId) const
{
    const int32 Index = FindCarrierIndex(CarrierId);
    return Carriers.IsValidIndex(Index) && Carriers[Index].VehicleBody
        && Carriers[Index].VehicleBody->IsVisible();
}

bool ALBECoatLineActor::GetBayDescriptor(const int32 BayIndex,
    FLBECoatBayDescriptor& OutDescriptor) const
{
    if (!BayDescriptors.IsValidIndex(BayIndex)) return false;
    OutDescriptor = BayDescriptors[BayIndex];
    return true;
}

bool ALBECoatLineActor::GetBayOperatingState(const int32 BayIndex,
    FLBECoatBayOperatingState& OutState) const
{
    if (!BayOperatingStates.IsValidIndex(BayIndex)) return false;
    OutState = BayOperatingStates[BayIndex];
    return true;
}

bool ALBECoatLineActor::GetLiquidSurfacePresentation(const int32 TreatmentBayIndex,
    FVector& OutActorLocalLocation, bool& bOutVisible) const
{
    if (!LiquidSurfaces.IsValidIndex(TreatmentBayIndex) || !LiquidSurfaces[TreatmentBayIndex])
        return false;
    OutActorLocalLocation = LiquidSurfaces[TreatmentBayIndex]->GetRelativeLocation();
    bOutVisible = LiquidSurfaces[TreatmentBayIndex]->IsVisible();
    return true;
}

bool ALBECoatLineActor::GetBaySocketTransform(const int32 BayIndex, const FName SocketSemantic,
    FTransform& OutActorLocalTransform) const
{
    if (!BayDescriptors.IsValidIndex(BayIndex) || SocketSemantic.IsNone()) return false;
    const FLBECoatBayDescriptor& Bay = BayDescriptors[BayIndex];
    const float CentreX = (Bay.StartXCm + Bay.EndXCm) * 0.5f;
    FVector Location = FVector::ZeroVector;

    if (SocketSemantic == TEXT("LineIn")) Location = FVector(Bay.StartXCm, 0.0f, DryBodyRootZCm);
    else if (SocketSemantic == TEXT("LineOut")) Location = FVector(Bay.EndXCm, 0.0f, DryBodyRootZCm);
    else if (SocketSemantic == TEXT("CarrierPathIn")) Location = FVector(Bay.StartXCm, 0.0f, HangerRootZCm);
    else if (SocketSemantic == TEXT("CarrierPathOut")) Location = FVector(Bay.EndXCm, 0.0f, HangerRootZCm);
    else if (SocketSemantic == TEXT("RailLeftIn")) Location = FVector(Bay.StartXCm, -RailOffsetYCm, RailHeightCm);
    else if (SocketSemantic == TEXT("RailLeftOut")) Location = FVector(Bay.EndXCm, -RailOffsetYCm, RailHeightCm);
    else if (SocketSemantic == TEXT("RailRightIn")) Location = FVector(Bay.StartXCm, RailOffsetYCm, RailHeightCm);
    else if (SocketSemantic == TEXT("RailRightOut")) Location = FVector(Bay.EndXCm, RailOffsetYCm, RailHeightCm);
    else if (SocketSemantic == TEXT("HangerRoot")) Location = FVector(CentreX, 0.0f, HangerRootZCm);
    else if (SocketSemantic == TEXT("Fluid") && Bay.bHasLiquid) Location = FVector(CentreX, 0.0f, LiquidSurfaceZCm);
    else if (SocketSemantic == TEXT("Dip") && Bay.bHasLiquid) Location = FVector(CentreX, 0.0f, DippedBodyRootZCm);
    else if (SocketSemantic == TEXT("ServiceLeft")) Location = FVector(CentreX, -520.0f, TankRimZCm);
    else if (SocketSemantic == TEXT("ServiceRight")) Location = FVector(CentreX, 520.0f, TankRimZCm);
    else if (SocketSemantic == TEXT("PlayerInspect")) Location = FVector(CentreX, -650.0f, 0.0f);
    else if (SocketSemantic == TEXT("Maintenance")) Location = FVector(CentreX, 650.0f, 0.0f);
    else if (SocketSemantic == TEXT("ServiceDoor") && Bay.bEnclosed) Location = FVector(CentreX, -320.0f, 180.0f);
    else if (SocketSemantic == TEXT("Fan") && Bay.bEnclosed) Location = FVector(CentreX, 0.0f, 925.0f);
    else if (SocketSemantic == TEXT("ServiceLightLeft") && Bay.bEnclosed) Location = FVector(CentreX, -305.0f, 520.0f);
    else if (SocketSemantic == TEXT("ServiceLightRight") && Bay.bEnclosed) Location = FVector(CentreX, 305.0f, 520.0f);
    else if (SocketSemantic == TEXT("AirSeal")
        && (Bay.BayType == ELBECoatBayType::OvenEntry || Bay.BayType == ELBECoatBayType::OvenExit))
        Location = FVector(Bay.BayType == ELBECoatBayType::OvenEntry ? Bay.StartXCm : Bay.EndXCm,
            0.0f, DryBodyRootZCm);
    else if (SocketSemantic == TEXT("StackLight")
        && (Bay.BayType == ELBECoatBayType::OvenEntry || Bay.BayType == ELBECoatBayType::OvenExit))
        Location = FVector(CentreX, -350.0f, 900.0f);
    else return false;

    OutActorLocalTransform = FTransform(FRotator::ZeroRotator, Location);
    return true;
}

FLBECoatLineSaveState ALBECoatLineActor::CaptureSaveState() const
{
    FLBECoatLineSaveState State;
    State.Version = 3;
    State.LineId = LineId;
    State.WorldTransform = GetActorTransform();
    State.OperatingState = OperatingState;
    State.StateReason = StateReason;
    State.TargetLineSpeedCmPerSecond = TargetLineSpeedCmPerSecond;
    State.bLoopCarriers = bLoopCarriers;
    State.BayStates = BayOperatingStates;
    for (const FLBECoatCarrierRuntimeEntry& Carrier : Carriers) State.Carriers.Add(Carrier.State);
    return State;
}

bool ALBECoatLineActor::IsSaveStateContractValid(const FLBECoatLineSaveState& State)
{
    if ((State.Version != 1 && State.Version != 2 && State.Version != 3)
        || State.LineId.IsNone() || !State.WorldTransform.IsValid()
        || !State.WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f)
        || !StaticEnum<ELBECoatOperatingState>()->IsValidEnumValue(
            static_cast<int64>(State.OperatingState))
        || !FMath::IsFinite(State.TargetLineSpeedCmPerSecond)
        || !FMath::IsWithinInclusive(State.TargetLineSpeedCmPerSecond, 1.0f, 1000.0f)
        || State.BayStates.Num() != TotalBayCount) return false;

    TSet<FName> CarrierIds;
    TSet<FName> BodyIds;
    bool bAnyFaulted = false;
    bool bAnyStarved = false;
    for (int32 Index = 0; Index < State.BayStates.Num(); ++Index)
    {
        const FLBECoatBayOperatingState& BayState = State.BayStates[Index];
        if (BayState.BayIndex != Index || !FMath::IsFinite(BayState.ProcessValue01)
            || !FMath::IsFinite(BayState.TemperatureC) || !FMath::IsFinite(BayState.LiquidLevel01)
            || !FMath::IsWithinInclusive(BayState.ProcessValue01, 0.0f, 1.0f)
            || !FMath::IsWithinInclusive(BayState.LiquidLevel01, 0.0f, 1.0f)) return false;
        bAnyFaulted |= BayState.bFaulted;
        bAnyStarved |= BayState.bStarved;
    }
    const float MaximumCarrierDistanceCm = State.Version == 1
        ? LegacyTotalLengthCm : TotalLengthCm;
    for (const FLBECoatCarrierSaveState& Carrier : State.Carriers)
    {
        if (Carrier.CarrierId.IsNone() || CarrierIds.Contains(Carrier.CarrierId)
            || !FMath::IsFinite(Carrier.DistanceCm)
            || !FMath::IsWithinInclusive(Carrier.DistanceCm, 0.0f,
                MaximumCarrierDistanceCm)) return false;
        if (State.Version < 3 && Carrier.bHasBodyInWhite) return false;
        if (Carrier.bHasBodyInWhite)
        {
            const FLBBodyInWhiteRecord& Body = Carrier.BodyInWhite;
            TArray<FName> BodyFamilies;
            FName BodyBaseKitTypeId;
            if (Body.BodyId.IsNone()
                || !LBVehicleModelCatalog::GetBodyWeldContract(
                    Body.VehicleModelId, BodyFamilies, BodyBaseKitTypeId)
                || Body.OrderId.IsNone()
                || Body.BaseKitId.IsNone() || Body.ReservationId.IsNone()
                || Body.WeldLineId.IsNone() || !Body.bEDAccepted
                || Body.QualityState != ELBBodyWeldQualityState::Good
                || Body.Panels.Num() != BodyFamilies.Num()
                || BodyIds.Contains(Body.BodyId)
                || !FMath::IsFinite(Body.CycleEvidence.ClosurePreparationSeconds)
                || !FMath::IsFinite(Body.CycleEvidence.FramingSeconds)
                || !FMath::IsFinite(Body.CycleEvidence.WeldingSeconds)
                || !FMath::IsFinite(Body.CycleEvidence.GeometryCheckSeconds)
                || Body.CycleEvidence.CompletionSequence <= 0) return false;
            BodyIds.Add(Body.BodyId);
            TSet<FName> PanelIds;
            TSet<FName> LineageFamilies;
            for (const FLBBodyWeldPanelLineage& Panel : Body.Panels)
            {
                FName ParsedVehicle;
                FName ParsedFamily;
                if (Panel.PanelId.IsNone() || Panel.PanelTypeId.IsNone()
                    || Panel.StillageId.IsNone() || PanelIds.Contains(Panel.PanelId)
                    || LineageFamilies.Contains(Panel.PanelTypeId)
                    || !LBCairnwell2040PanelCatalog::ParsePressedPanelUnitId(
                        Panel.PanelId, ParsedVehicle, ParsedFamily)
                    || ParsedVehicle != Body.VehicleModelId || ParsedFamily != Panel.PanelTypeId
                    || !BodyFamilies.Contains(Panel.PanelTypeId)) return false;
                PanelIds.Add(Panel.PanelId);
                LineageFamilies.Add(Panel.PanelTypeId);
            }
        }
        CarrierIds.Add(Carrier.CarrierId);
    }

    const bool bFaultStateCoherent = !bAnyFaulted
        || State.OperatingState == ELBECoatOperatingState::Faulted
        || State.OperatingState == ELBECoatOperatingState::EmergencyStop
        || State.OperatingState == ELBECoatOperatingState::Maintenance;
    const bool bStarvedStateCoherent = bAnyFaulted || !bAnyStarved
        || State.OperatingState == ELBECoatOperatingState::Starved
        || State.OperatingState == ELBECoatOperatingState::EmergencyStop
        || State.OperatingState == ELBECoatOperatingState::Maintenance;
    return bFaultStateCoherent && bStarvedStateCoherent;
}

bool ALBECoatLineActor::RestoreSaveState(const FLBECoatLineSaveState& State)
{
    if (!IsSaveStateContractValid(State)) return false;

    // Keep restore transactional: every fallible carrier allocation is built in a detached
    // temporary array first. Once contract preflight succeeds, the commit path cannot fail.
    TArray<FLBECoatCarrierSaveState> MigratedCarriers;
    MigratedCarriers.Reserve(State.Carriers.Num());
    for (const FLBECoatCarrierSaveState& CarrierState : State.Carriers)
    {
        FLBECoatCarrierSaveState& Migrated = MigratedCarriers.Add_GetRef(CarrierState);
        Migrated.DistanceCm = State.Version == 1
            ? MigrateLegacyCarrierDistance(CarrierState.DistanceCm)
            : CarrierState.DistanceCm;
        Migrated.bHasBodyInWhite = State.Version >= 3 && CarrierState.bHasBodyInWhite;
        if (!Migrated.bHasBodyInWhite) Migrated.BodyInWhite = FLBBodyInWhiteRecord();
    }

    ClearCarriers();
    LineId = State.LineId;
    InputPort->PortId = FName(*FString::Printf(TEXT("%s-IN"), *LineId.ToString()));
    OutputPort->PortId = FName(*FString::Printf(TEXT("%s-OUT"), *LineId.ToString()));
    Tags = { TEXT("LB.PlayerBuilt.ECoatLine"), TEXT("LB.Factory.PaintShop"),
        TEXT("LB.FactoryBuilder.Machine"),
        FName(*FString::Printf(TEXT("LB.ECoatLine.%s"), *LineId.ToString())) };
    SetActorTransform(State.WorldTransform);
    TargetLineSpeedCmPerSecond = State.TargetLineSpeedCmPerSecond;
    bLoopCarriers = State.bLoopCarriers;
    OperatingState = State.OperatingState;
    StateReason = State.StateReason;
    BayOperatingStates = State.BayStates;
    for (int32 Index = 0; Index < TreatmentBayCount; ++Index) RefreshLiquidSurface(Index);
    for (const FLBECoatCarrierSaveState& CarrierState : MigratedCarriers)
    {
        FLBECoatCarrierRuntimeEntry& Carrier = Carriers.AddDefaulted_GetRef();
        Carrier.State = CarrierState;
        CreateCarrierPresentation(Carrier);
        RefreshCarrierPresentation(Carrier);
    }
    RefreshOperationalPresentation();
    return true;
}
