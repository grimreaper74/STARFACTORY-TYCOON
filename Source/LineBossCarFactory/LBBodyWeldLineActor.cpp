#include "LBBodyWeldLineActor.h"

#include "LBFactoryFloorMarkingComponent.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBMachineLiveryComponent.h"
#include "LBStatusBeaconComponent.h"
#include "LBVehiclePanelCatalog.h"

#include "Components/BoxComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace LBBodyWeldPrivate
{
    const FName Cairnwell2040(TEXT("CAIRNWELL_2040"));
    const FName RobotToolPanelPick(TEXT("PANEL_PICK"));
    const FName RobotToolSpot(TEXT("SPOT"));
    const FName RobotToolMIG(TEXT("MIG"));

    struct FRobotStationSpec
    {
        FVector RootLocationCm;
        FName ToolRole;
    };

    // Fixed-pose visual substitution only. These roots exactly replace the four
    // legacy cube triplets; the shared master authored the tool origin at this flange.
    const FRobotStationSpec RobotStations[] = {
        {FVector(1700.0f, -500.0f, 0.0f), RobotToolPanelPick},
        {FVector(2800.0f, 500.0f, 0.0f), RobotToolSpot},
        {FVector(3300.0f, -500.0f, 0.0f), RobotToolSpot},
        {FVector(3900.0f, 500.0f, 0.0f), RobotToolMIG}
    };
    const FVector RobotToolFlangeRelativeCm(-38.9165f, -9.4918f, 137.6317f);


    template<typename T>
    bool AddUniqueId(TSet<FName>& Ids, const T& Value)
    {
        if (Value.IsNone() || Ids.Contains(Value)) return false;
        Ids.Add(Value);
        return true;
    }

    void ApplyColour(UHierarchicalInstancedStaticMeshComponent* Component,
        const FLinearColor& Colour)
    {
        if (!Component) return;
        if (UMaterialInstanceDynamic* Material = Component->CreateAndSetMaterialInstanceDynamic(0))
        {
            Material->SetVectorParameterValue(TEXT("Color"), Colour);
            Material->SetVectorParameterValue(TEXT("BaseColor"), Colour);
        }
    }

    void ApplyColour(UStaticMeshComponent* Component, const FLinearColor& Colour)
    {
        if (!Component) return;
        if (UMaterialInstanceDynamic* Material = Component->CreateAndSetMaterialInstanceDynamic(0))
        {
            Material->SetVectorParameterValue(TEXT("Color"), Colour);
            Material->SetVectorParameterValue(TEXT("BaseColor"), Colour);
        }
    }

    FLinearColor RuntimeArtColourForSlot(const FName SlotName)
    {
        const FString Slot = SlotName.ToString();
        if (Slot.Contains(TEXT("LightStructuralSteel")))
            return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("D8DEE3")));
        if (Slot.Contains(TEXT("GraphiteTooling")) || Slot.Contains(TEXT("SkidGraphite")))
            return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("303A42")));
        if (Slot.Contains(TEXT("TealMachinePanel")))
            return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("2F9E86")));
        if (Slot.Contains(TEXT("SafetyYellow")))
            return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("F2C94C")));
        if (Slot.Contains(TEXT("BrushedToolSteel")))
            return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("9FAAB3")));
        if (Slot.Contains(TEXT("HoseBlack")))
            return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("12181D")));
        if (Slot.Contains(TEXT("BeaconGreen")))
            return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("43C77A")));
        if (Slot.Contains(TEXT("BeaconAmber")))
            return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("FFB020")));
        if (Slot.Contains(TEXT("BeaconRed")))
            return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("E05252")));
        if (Slot.Contains(TEXT("GalvanisedBIW")))
            return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("C9D1D8")));
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("D8DEE3")));
    }

    bool LineageLess(const FLBBodyWeldPanelLineage& A, const FLBBodyWeldPanelLineage& B)
    {
        if (A.PanelTypeId != B.PanelTypeId) return A.PanelTypeId.LexicalLess(B.PanelTypeId);
        return A.PanelId.LexicalLess(B.PanelId);
    }
}

ALBBodyWeldLineActor::ALBBodyWeldLineActor()
{
    PrimaryActorTick.bCanEverTick = true;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    ProtectedEnvelope = CreateDefaultSubobject<UBoxComponent>(TEXT("ProtectedEnvelope"));
    ProtectedEnvelope->SetupAttachment(SceneRoot);
    ProtectedEnvelope->SetRelativeLocation(FVector(2700.0f, 0.0f, 350.0f));
    ProtectedEnvelope->SetBoxExtent(FVector(3000.0f, 1500.0f, 350.0f));
    ProtectedEnvelope->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    ProtectedEnvelope->SetCollisionObjectType(ECC_WorldDynamic);
    ProtectedEnvelope->SetCollisionResponseToAllChannels(ECR_Ignore);
    ProtectedEnvelope->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    ProtectedEnvelope->SetGenerateOverlapEvents(true);
    ProtectedEnvelope->SetCanEverAffectNavigation(false);

    FloorMarkings = CreateDefaultSubobject<ULBFactoryFloorMarkingComponent>(TEXT("FloorMarkings"));
    FloorMarkings->SetupAttachment(SceneRoot);
    MachineLivery = CreateDefaultSubobject<ULBMachineLiveryComponent>(TEXT("MachineLivery"));
    StatusBeacon = CreateDefaultSubobject<ULBStatusBeaconComponent>(TEXT("StatusBeacon"));
    StatusBeacon->SetupAttachment(SceneRoot);
    StatusBeacon->SetRelativeLocation(FVector(5200.0f, -950.0f, 640.0f));

    StillageInputPort = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("StillageInputPort"));
    StillageInputPort->SetupAttachment(SceneRoot);
    StillageInputPort->Direction = ELBFactoryPortDirection::Input;
    StillageInputPort->TransportKind = ELBFactoryTransportKind::AGVHandoff;
    StillageInputPort->MaterialClass = ELBFactoryMaterialClass::Stillage;
    StillageInputPort->ProcessStage = LBFactoryProcessStage::BodyWeld;
    StillageInputPort->MaximumAutomaticLinkDistanceCm = 2500.0f;
    StillageInputPort->SetRelativeLocation(FVector(0.0f, -900.0f, 100.0f));

    BaseKitInputPort = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("BaseKitInputPort"));
    BaseKitInputPort->SetupAttachment(SceneRoot);
    BaseKitInputPort->Direction = ELBFactoryPortDirection::Input;
    BaseKitInputPort->TransportKind = ELBFactoryTransportKind::AGVHandoff;
    // Compatibility only: the integration owner may append BIWBaseKit later.
    BaseKitInputPort->MaterialClass = ELBFactoryMaterialClass::GeneralParts;
    BaseKitInputPort->ProcessStage = LBFactoryProcessStage::BodyWeld;
    BaseKitInputPort->MaximumAutomaticLinkDistanceCm = 2500.0f;
    BaseKitInputPort->SetRelativeLocation(FVector(0.0f, 900.0f, 100.0f));

    BIWOutputPort = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("BIWOutputPort"));
    BIWOutputPort->SetupAttachment(SceneRoot);
    BIWOutputPort->Direction = ELBFactoryPortDirection::Output;
    BIWOutputPort->TransportKind = ELBFactoryTransportKind::PanelTransfer;
    BIWOutputPort->MaterialClass = ELBFactoryMaterialClass::BodyInWhite;
    BIWOutputPort->ProcessStage = LBFactoryProcessStage::BodyWeld;
    BIWOutputPort->MaximumAutomaticLinkDistanceCm = 2500.0f;
    BIWOutputPort->SetRelativeLocation(FVector(5400.0f, 0.0f, 150.0f));

    const auto CreateInstanceComponent = [this](const TCHAR* Name)
    {
        UHierarchicalInstancedStaticMeshComponent* Component =
            CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(Name);
        Component->SetupAttachment(SceneRoot);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCanEverAffectNavigation(false);
        return Component;
    };
    PrimaryMachineInstances = CreateInstanceComponent(TEXT("PrimaryMachineInstances"));
    SecondaryMachineInstances = CreateInstanceComponent(TEXT("SecondaryMachineInstances"));
    SafetyInstances = CreateInstanceComponent(TEXT("SafetyInstances"));
    BIWProxyInstances = CreateInstanceComponent(TEXT("BIWProxyInstances"));

    BIWProxy = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BIWProxy"));
    BIWProxy->SetupAttachment(SceneRoot);
    BIWProxy->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BIWProxy->SetCanEverAffectNavigation(false);
    BIWProxy->SetRelativeLocation(FVector(4750.0f, 0.0f, 62.0f));
    BIWProxy->SetRelativeScale3D(FVector(4.5f, 1.8f, 0.12f));

    const auto CreatePresentationComponent = [this](const TCHAR* Name, USceneComponent* Parent)
    {
        UStaticMeshComponent* Component = CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Component->SetupAttachment(Parent ? Parent : SceneRoot.Get());
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        return Component;
    };
    FramingFixturePresentation = CreatePresentationComponent(
        TEXT("FramingFixturePresentation"), SceneRoot);
    FramingFixturePresentation->SetRelativeLocation(FVector(2700.0f, 0.0f, 0.0f));

    BaseKitWorkpieceRoot = CreateDefaultSubobject<USceneComponent>(TEXT("BaseKitWorkpieceRoot"));
    BaseKitWorkpieceRoot->SetupAttachment(SceneRoot);
    BaseKitWorkpieceRoot->SetRelativeLocation(FVector(2700.0f, 0.0f, 0.0f));
    BaseKitSkidPresentation = CreatePresentationComponent(
        TEXT("BaseKitSkidPresentation"), BaseKitWorkpieceRoot);
    BaseKitUnderbodyPresentation = CreatePresentationComponent(
        TEXT("BaseKitUnderbodyPresentation"), BaseKitWorkpieceRoot);
    BaseKitWorkpieceRoot->SetVisibility(false, true);

    static_assert(UE_ARRAY_COUNT(LBBodyWeldPrivate::RobotStations) == RobotStationCount,
        "The fixed Body Weld robot station contract must remain four entries");
    RobotBasePresentations.Reserve(RobotStationCount);
    RobotToolPresentations.Reserve(RobotStationCount);
    for (int32 StationIndex = 0; StationIndex < RobotStationCount; ++StationIndex)
    {
        UStaticMeshComponent* Base = CreatePresentationComponent(
            *FString::Printf(TEXT("WeldRobotBasePresentation_%d"), StationIndex), SceneRoot);
        Base->SetRelativeLocation(LBBodyWeldPrivate::RobotStations[StationIndex].RootLocationCm);
        Base->SetRelativeRotation(FRotator::ZeroRotator);
        // This line actor is placed/restored at runtime, so its root remains movable.
        // A static child cannot attach to that movable root during registration.
        Base->SetMobility(EComponentMobility::Movable);
        RobotBasePresentations.Add(Base);

        UStaticMeshComponent* Tool = CreatePresentationComponent(
            *FString::Printf(TEXT("WeldRobotToolPresentation_%d"), StationIndex), Base);
        Tool->SetRelativeLocation(LBBodyWeldPrivate::RobotToolFlangeRelativeCm);
        Tool->SetRelativeRotation(FRotator::ZeroRotator);
        Tool->SetMobility(EComponentMobility::Movable);
        RobotToolPresentations.Add(Tool);
    }

    FramingFixtureMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyWeldLine/Runtime_v001/Fixture/")
        TEXT("SM_LB_BodyWeld_FramingFixture_v001.SM_LB_BodyWeld_FramingFixture_v001")));
    BaseKitSkidMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
        TEXT("/Game/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Carrier/")
        TEXT("SM_LB_C2040_BIWBaseSkid_v001.SM_LB_C2040_BIWBaseSkid_v001")));
    BaseKitUnderbodyMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
        TEXT("/Game/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Workpiece/")
        TEXT("SM_LB_C2040_BIWBaseKit_Underbody_v001.SM_LB_C2040_BIWBaseKit_Underbody_v001")));
    WeldRobotSharedBaseMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
        TEXT("/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/SharedBase/")
        TEXT("SM_LB_WeldRobot_SharedBase_v001.SM_LB_WeldRobot_SharedBase_v001")));
    WeldRobotMIGToolMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
        TEXT("/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/MIG/")
        TEXT("SM_LB_WeldTool_MIG_v001.SM_LB_WeldTool_MIG_v001")));
    WeldRobotSpotToolMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
        TEXT("/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/SpotGun/")
        TEXT("SM_LB_WeldTool_SpotGun_v001.SM_LB_WeldTool_SpotGun_v001")));
    WeldRobotPanelPickToolMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(
        TEXT("/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/PanelPick/")
        TEXT("SM_LB_WeldTool_PanelPick_v001.SM_LB_WeldTool_PanelPick_v001")));

    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> BasicMaterial(
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
    if (Cube.Succeeded())
    {
        CubeFallbackMesh = Cube.Object;
        PrimaryMachineInstances->SetStaticMesh(Cube.Object);
        SecondaryMachineInstances->SetStaticMesh(Cube.Object);
        SafetyInstances->SetStaticMesh(Cube.Object);
        BIWProxyInstances->SetStaticMesh(Cube.Object);
        BIWProxy->SetStaticMesh(Cube.Object);
    }
    if (BasicMaterial.Succeeded())
    {
        BasicPresentationMaterial = BasicMaterial.Object;
        PrimaryMachineInstances->SetMaterial(0, BasicMaterial.Object);
        SecondaryMachineInstances->SetMaterial(0, BasicMaterial.Object);
        SafetyInstances->SetMaterial(0, BasicMaterial.Object);
        BIWProxyInstances->SetMaterial(0, BasicMaterial.Object);
        BIWProxy->SetMaterial(0, BasicMaterial.Object);
        MachineLivery->RegisterGenericMaterialBinding(PrimaryMachineInstances, 0,
            ELBMachineLiveryRole::PrimaryBody, BasicMaterial.Object);
        MachineLivery->RegisterGenericMaterialBinding(SecondaryMachineInstances, 0,
            ELBMachineLiveryRole::SecondaryFrame, BasicMaterial.Object);
        if (UMaterialInstanceDynamic* Primary = MachineLivery->GetDynamicMaterialForBinding(0))
            Primary->SetVectorParameterValue(TEXT("Color"),
                FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("2F9E86"))));
        if (UMaterialInstanceDynamic* Secondary = MachineLivery->GetDynamicMaterialForBinding(1))
            Secondary->SetVectorParameterValue(TEXT("Color"),
                FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("496579"))));
    }

    RefreshOperatingState();
}

void ALBBodyWeldLineActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ResolveRuntimeVisuals();
    RebuildProxyVisuals();
    RefreshPresentation();
}

void ALBBodyWeldLineActor::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    AdvanceSimulation(DeltaSeconds);
}

bool ALBBodyWeldLineActor::Configure(const FName InLineId)
{
    if (InLineId.IsNone()) return false;
    if (!LineId.IsNone() && LineId != InLineId) return false;
    LineId = InLineId;
    StillageInputPort->PortId = FName(*FString::Printf(TEXT("%s-STILLAGE-IN"), *LineId.ToString()));
    BaseKitInputPort->PortId = FName(*FString::Printf(TEXT("%s-BASE-KIT-IN"), *LineId.ToString()));
    BIWOutputPort->PortId = FName(*FString::Printf(TEXT("%s-BIW-OUT"), *LineId.ToString()));
    RefreshOperatingState();
    return true;
}

void ALBBodyWeldLineActor::SetEnabled(const bool bInEnabled)
{
    bEnabled = bInEnabled;
    RefreshOperatingState();
}

bool ALBBodyWeldLineActor::SetAssignedOrder(const FName InOrderId)
{
    if (InOrderId.IsNone() || ActiveReservation.bValid || bHasOutputBody || bHasReworkBody) return false;
    AssignedOrderId = InOrderId;
    RefreshOperatingState();
    return true;
}

void ALBBodyWeldLineActor::SetPaused(const bool bInPaused)
{
    bPaused = bInPaused;
    RefreshOperatingState();
}

void ALBBodyWeldLineActor::SetServiceHeld(const bool bInServiceHeld)
{
    bServiceHeld = bInServiceHeld;
    RefreshOperatingState();
}

void ALBBodyWeldLineActor::SetEDAvailable(const bool bInAvailable)
{
    bEDAvailable = bInAvailable;
    RefreshOperatingState();
}

void ALBBodyWeldLineActor::SetQualityConditions(const FLBBodyWeldQualityConditions& InConditions)
{
    QualityConditions = InConditions;
    if (ActiveReservation.bValid && ActiveReservation.bConsumptionCommitted)
    {
        ActiveCycleQualityConditions.bFixtureProgramCorrect &= InConditions.bFixtureProgramCorrect;
        ActiveCycleQualityConditions.bRobotCalibrationInTolerance &= InConditions.bRobotCalibrationInTolerance;
        ActiveCycleQualityConditions.bServiceConditionAcceptable &= InConditions.bServiceConditionAcceptable;
        ActiveCycleQualityConditions.bSafetyInterlockClear &= InConditions.bSafetyInterlockClear;
    }
}

FName ALBBodyWeldLineActor::GetVehicleModelId()
{
    return LBBodyWeldPrivate::Cairnwell2040;
}

FName ALBBodyWeldLineActor::GetBaseKitTypeId()
{
    TArray<FName> Families;
    FName BaseKitTypeId;
    return LBVehicleModelCatalog::GetBodyWeldContract(GetVehicleModelId(), Families, BaseKitTypeId)
        ? BaseKitTypeId : NAME_None;
}

TArray<FName> ALBBodyWeldLineActor::GetRequiredPanelFamilies()
{
    TArray<FName> Families;
    FName BaseKitTypeId;
    LBVehicleModelCatalog::GetBodyWeldContract(GetVehicleModelId(), Families, BaseKitTypeId);
    return Families;
}

bool ALBBodyWeldLineActor::ReceivePanelStillage(const FLBBodyWeldStillageInventory& Stillage,
    FString& OutReason)
{
    OutReason.Reset();
    if (!IsStillageContractValid(Stillage))
    {
        OutReason = TEXT("Invalid exact panel-stillage payload");
        return false;
    }
    if (Stillages.ContainsByPredicate([&Stillage](const FLBBodyWeldStillageInventory& Existing)
        { return Existing.StillageId == Stillage.StillageId; }))
    {
        OutReason = FString::Printf(TEXT("Duplicate stillage identity %s"), *Stillage.StillageId.ToString());
        return false;
    }
    TSet<FName> ExistingPanels;
    for (const FLBBodyWeldStillageInventory& Existing : Stillages)
        for (const FLBBodyWeldPanelUnit& Panel : Existing.PanelUnits) ExistingPanels.Add(Panel.PanelId);
    for (const FLBBodyInWhiteRecord& Body : CompletedBodies)
        for (const FLBBodyWeldPanelLineage& Panel : Body.Panels) ExistingPanels.Add(Panel.PanelId);
    if (bHasOutputBody)
        for (const FLBBodyWeldPanelLineage& Panel : OutputBody.Panels) ExistingPanels.Add(Panel.PanelId);
    if (bHasReworkBody)
        for (const FLBBodyWeldPanelLineage& Panel : ReworkBody.Panels) ExistingPanels.Add(Panel.PanelId);
    for (const FLBBodyWeldPanelUnit& Panel : Stillage.PanelUnits)
    {
        if (ExistingPanels.Contains(Panel.PanelId))
        {
            OutReason = FString::Printf(TEXT("Duplicate panel identity %s"), *Panel.PanelId.ToString());
            return false;
        }
    }
    Stillages.Add(Stillage);
    RefreshOperatingState();
    return true;
}

bool ALBBodyWeldLineActor::ReceiveBaseKit(const FLBBodyWeldBaseKitUnit& BaseKit, FString& OutReason)
{
    OutReason.Reset();
    if (!IsBaseKitContractValid(BaseKit))
    {
        OutReason = TEXT("Invalid finite BIW base-kit payload");
        return false;
    }
    const bool bPreviouslyUsed = CompletedBodies.ContainsByPredicate(
        [&BaseKit](const FLBBodyInWhiteRecord& Body) { return Body.BaseKitId == BaseKit.KitId; })
        || (bHasOutputBody && OutputBody.BaseKitId == BaseKit.KitId)
        || (bHasReworkBody && ReworkBody.BaseKitId == BaseKit.KitId);
    if (bPreviouslyUsed || BaseKits.ContainsByPredicate([&BaseKit](const FLBBodyWeldBaseKitUnit& Existing)
        { return Existing.KitId == BaseKit.KitId; }))
    {
        OutReason = FString::Printf(TEXT("Duplicate base-kit identity %s"), *BaseKit.KitId.ToString());
        return false;
    }
    BaseKits.Add(BaseKit);
    RefreshOperatingState();
    return true;
}

bool ALBBodyWeldLineActor::PopEmptyStillageReturn(FLBBodyWeldEmptyStillageReturn& OutReturn)
{
    OutReturn = FLBBodyWeldEmptyStillageReturn();
    if (PendingEmptyReturns.IsEmpty()) return false;
    PendingEmptyReturns.Sort([](const FLBBodyWeldEmptyStillageReturn& A,
        const FLBBodyWeldEmptyStillageReturn& B)
    {
        if (A.QueueSequence != B.QueueSequence) return A.QueueSequence < B.QueueSequence;
        return A.StillageId.LexicalLess(B.StillageId);
    });
    OutReturn = PendingEmptyReturns[0];
    PendingEmptyReturns.RemoveAt(0);
    if (FLBBodyWeldStillageInventory* Stillage = Stillages.FindByPredicate(
        [&OutReturn](const FLBBodyWeldStillageInventory& Candidate)
        { return Candidate.StillageId == OutReturn.StillageId; }))
    {
        Stillage->bEmptyReturnIssued = true;
        Stillage->bEmptyReturnQueued = false;
    }
    RefreshOperatingState();
    return true;
}

bool ALBBodyWeldLineActor::FindFirstMissingRecipeItem(FString& OutReason) const
{
    if (AssignedOrderId.IsNone())
    {
        OutReason = TEXT("No vehicle order assigned");
        return true;
    }
    TArray<FName> Families;
    FName BaseKitTypeId;
    FName ModelId;
    return !ResolveReservableModel(ModelId, Families, BaseKitTypeId, OutReason);
}

bool ALBBodyWeldLineActor::FindFirstMissingRecipeItemForModel(const FName ModelId,
    FString& OutReason) const
{
    TArray<FName> Families;
    FName BaseKitTypeId;
    if (!LBVehicleModelCatalog::GetBodyWeldContract(ModelId, Families, BaseKitTypeId))
    {
        OutReason = FString::Printf(TEXT("Model %s has no valid Body Weld recipe"), *ModelId.ToString());
        return true;
    }
    for (const FName Family : Families)
    {
        const bool bFound = Stillages.ContainsByPredicate(
            [this, ModelId, Family](const FLBBodyWeldStillageInventory& Stillage)
        {
            if (Stillage.OrderId != AssignedOrderId
                || Stillage.VehicleModelId != ModelId
                || Stillage.PanelTypeId != Family) return false;
            return Stillage.PanelUnits.ContainsByPredicate(
                [](const FLBBodyWeldPanelUnit& Panel)
                { return !Panel.bReserved && !Panel.bConsumed; });
        });
        if (!bFound)
        {
            OutReason = FString::Printf(TEXT("Missing %s (0/1)"), *Family.ToString());
            return true;
        }
    }
    const bool bKitFound = BaseKits.ContainsByPredicate([this, ModelId, BaseKitTypeId](const FLBBodyWeldBaseKitUnit& Kit)
    {
        return Kit.OrderId == AssignedOrderId
            && Kit.VehicleModelId == ModelId
            && Kit.KitTypeId == BaseKitTypeId
            && !Kit.bReserved && !Kit.bConsumed;
    });
    if (!bKitFound)
    {
        OutReason = FString::Printf(TEXT("Missing %s (0/1)"), *BaseKitTypeId.ToString());
        return true;
    }
    OutReason.Reset();
    return false;
}

bool ALBBodyWeldLineActor::ResolveReservableModel(FName& OutModelId, TArray<FName>& OutPanelFamilies,
    FName& OutBaseKitTypeId, FString& OutReason) const
{
    OutModelId = NAME_None;
    OutPanelFamilies.Reset();
    OutBaseKitTypeId = NAME_None;
    FString FirstMissingReason;
    for (const FLBVehicleModelRecipe& Recipe : LBVehicleModelCatalog::GetRecipes())
    {
        FString CandidateReason;
        if (FindFirstMissingRecipeItemForModel(Recipe.ModelId, CandidateReason))
        {
            if (FirstMissingReason.IsEmpty()) FirstMissingReason = CandidateReason;
            continue;
        }
        if (!LBVehicleModelCatalog::GetBodyWeldContract(Recipe.ModelId, OutPanelFamilies, OutBaseKitTypeId))
            continue;
        OutModelId = Recipe.ModelId;
        OutReason.Reset();
        return true;
    }
    OutReason = FirstMissingReason.IsEmpty() ? TEXT("No registered model has a complete Body Weld recipe")
        : FirstMissingReason;
    return false;
}

bool ALBBodyWeldLineActor::TryReserveRecipe(FString& OutReason)
{
    OutReason.Reset();
    if (bFaulted || !bEnabled || bPaused || bServiceHeld || ActiveReservation.bValid
        || bHasOutputBody || bHasReworkBody)
    {
        OutReason = TEXT("Weld line is not available for a new reservation");
        return false;
    }
    FName ModelId;
    TArray<FName> Families;
    FName BaseKitTypeId;
    if (!ResolveReservableModel(ModelId, Families, BaseKitTypeId, OutReason))
    {
        RefreshOperatingState();
        return false;
    }

    struct FPanelSelection { int32 StillageIndex; int32 PanelIndex; };
    TArray<FPanelSelection> Selections;
    Selections.Reserve(Families.Num());
    for (const FName Family : Families)
    {
        FPanelSelection Best{INDEX_NONE, INDEX_NONE};
        for (int32 StillageIndex = 0; StillageIndex < Stillages.Num(); ++StillageIndex)
        {
            const FLBBodyWeldStillageInventory& Stillage = Stillages[StillageIndex];
            if (Stillage.OrderId != AssignedOrderId
                || Stillage.VehicleModelId != ModelId
                || Stillage.PanelTypeId != Family) continue;
            for (int32 PanelIndex = 0; PanelIndex < Stillage.PanelUnits.Num(); ++PanelIndex)
            {
                const FLBBodyWeldPanelUnit& Panel = Stillage.PanelUnits[PanelIndex];
                if (Panel.bReserved || Panel.bConsumed) continue;
                if (Best.StillageIndex == INDEX_NONE)
                {
                    Best = { StillageIndex, PanelIndex };
                    continue;
                }
                const FLBBodyWeldStillageInventory& CurrentStillage = Stillages[Best.StillageIndex];
                const FLBBodyWeldPanelUnit& CurrentPanel = CurrentStillage.PanelUnits[Best.PanelIndex];
                if (Stillage.DeliverySequence < CurrentStillage.DeliverySequence
                    || (Stillage.DeliverySequence == CurrentStillage.DeliverySequence
                        && Panel.PanelId.LexicalLess(CurrentPanel.PanelId)))
                {
                    Best = { StillageIndex, PanelIndex };
                }
            }
        }
        if (Best.StillageIndex == INDEX_NONE)
        {
            OutReason = FString::Printf(TEXT("Reservation changed while selecting %s"), *Family.ToString());
            return false;
        }
        Selections.Add(Best);
    }

    int32 KitIndex = INDEX_NONE;
    for (int32 Index = 0; Index < BaseKits.Num(); ++Index)
    {
        const FLBBodyWeldBaseKitUnit& Kit = BaseKits[Index];
        if (Kit.OrderId != AssignedOrderId || Kit.VehicleModelId != ModelId
            || Kit.KitTypeId != BaseKitTypeId || Kit.bReserved || Kit.bConsumed)
            continue;
        if (KitIndex == INDEX_NONE || Kit.DeliverySequence < BaseKits[KitIndex].DeliverySequence
            || (Kit.DeliverySequence == BaseKits[KitIndex].DeliverySequence
                && Kit.KitId.LexicalLess(BaseKits[KitIndex].KitId))) KitIndex = Index;
    }
    if (Selections.Num() != Families.Num() || KitIndex == INDEX_NONE)
    {
        OutReason = TEXT("Atomic reservation could not select the full recipe");
        return false;
    }

    // Every read-only selection succeeded; mutation starts only at this transaction boundary.
    FLBBodyWeldInputReservation NewReservation;
    NewReservation.bValid = true;
    NewReservation.OrderId = AssignedOrderId;
    NewReservation.VehicleModelId = ModelId;
    NewReservation.BaseKitId = BaseKits[KitIndex].KitId;
    NewReservation.ReservationId = FName(*FString::Printf(TEXT("WELDRES-%s-%06d"),
        *StableIdentityToken(LineId), NextReservationSerial));
    for (const FPanelSelection& Selection : Selections)
    {
        const FLBBodyWeldStillageInventory& Stillage = Stillages[Selection.StillageIndex];
        const FLBBodyWeldPanelUnit& Panel = Stillage.PanelUnits[Selection.PanelIndex];
        FLBBodyWeldPanelLineage& Lineage = NewReservation.Panels.AddDefaulted_GetRef();
        Lineage.PanelId = Panel.PanelId;
        Lineage.PanelTypeId = Panel.PanelTypeId;
        Lineage.StillageId = Stillage.StillageId;
    }
    NewReservation.Panels.Sort(LBBodyWeldPrivate::LineageLess);
    for (const FPanelSelection& Selection : Selections)
        Stillages[Selection.StillageIndex].PanelUnits[Selection.PanelIndex].bReserved = true;
    BaseKits[KitIndex].bReserved = true;
    ++NextReservationSerial;
    ActiveReservation = MoveTemp(NewReservation);
    Phase = ELBBodyWeldPhase::ReservingInputs;
    PhaseProgress01 = 0.0f;
    RefreshOperatingState();
    return true;
}

bool ALBBodyWeldLineActor::WouldCommitOverflowEmptyReturnQueue() const
{
    int32 NewlyEmpty = 0;
    TSet<FName> ReservationStillages;
    for (const FLBBodyWeldPanelLineage& Panel : ActiveReservation.Panels)
        ReservationStillages.Add(Panel.StillageId);
    for (const FName StillageId : ReservationStillages)
    {
        const FLBBodyWeldStillageInventory* Stillage = Stillages.FindByPredicate(
            [StillageId](const FLBBodyWeldStillageInventory& Candidate)
            { return Candidate.StillageId == StillageId; });
        if (!Stillage || Stillage->bEmptyReturnQueued || Stillage->bEmptyReturnIssued) continue;
        bool bAnyRemainingAfterCommit = false;
        for (const FLBBodyWeldPanelUnit& Panel : Stillage->PanelUnits)
        {
            const bool bSelected = ActiveReservation.Panels.ContainsByPredicate(
                [&Panel](const FLBBodyWeldPanelLineage& Reserved)
                { return Reserved.PanelId == Panel.PanelId; });
            bAnyRemainingAfterCommit |= !Panel.bConsumed && !bSelected;
        }
        if (!bAnyRemainingAfterCommit) ++NewlyEmpty;
    }
    return PendingEmptyReturns.Num() + NewlyEmpty > MaximumPendingEmptyReturns;
}

bool ALBBodyWeldLineActor::ValidateActiveReservationReferences(const bool bExpectConsumed) const
{
    TArray<FName> Families;
    FName BaseKitTypeId;
    if (!ActiveReservation.bValid
        || !LBVehicleModelCatalog::GetBodyWeldContract(ActiveReservation.VehicleModelId, Families, BaseKitTypeId)
        || ActiveReservation.Panels.Num() != Families.Num()) return false;
    const FLBBodyWeldBaseKitUnit* Kit = BaseKits.FindByPredicate([this](const FLBBodyWeldBaseKitUnit& Candidate)
        { return Candidate.KitId == ActiveReservation.BaseKitId; });
    if (!Kit || Kit->VehicleModelId != ActiveReservation.VehicleModelId || Kit->KitTypeId != BaseKitTypeId
        || Kit->bConsumed != bExpectConsumed || (!bExpectConsumed && !Kit->bReserved)) return false;
    TSet<FName> SeenFamilies;
    for (const FLBBodyWeldPanelLineage& Reserved : ActiveReservation.Panels)
    {
        const FLBBodyWeldStillageInventory* Stillage = Stillages.FindByPredicate(
            [&Reserved](const FLBBodyWeldStillageInventory& Candidate)
            { return Candidate.StillageId == Reserved.StillageId; });
        if (!Stillage) return false;
        const FLBBodyWeldPanelUnit* Panel = Stillage->PanelUnits.FindByPredicate(
            [&Reserved](const FLBBodyWeldPanelUnit& Candidate)
            { return Candidate.PanelId == Reserved.PanelId && Candidate.PanelTypeId == Reserved.PanelTypeId; });
        if (!Panel || !Families.Contains(Reserved.PanelTypeId) || SeenFamilies.Contains(Reserved.PanelTypeId)
            || Panel->VehicleModelId != ActiveReservation.VehicleModelId
            || Panel->bConsumed != bExpectConsumed || (!bExpectConsumed && !Panel->bReserved)) return false;
        SeenFamilies.Add(Reserved.PanelTypeId);
    }
    return SeenFamilies.Num() == Families.Num();
}

bool ALBBodyWeldLineActor::CommitReservedInputs(FString& OutReason)
{
    OutReason.Reset();
    if (bFaulted || !ActiveReservation.bValid || ActiveReservation.bConsumptionCommitted)
    {
        OutReason = TEXT("No uncommitted weld reservation exists");
        return false;
    }
    if (!ValidateActiveReservationReferences(false))
    {
        OutReason = TEXT("Committed lineage reference was lost before consumption");
        SetFault(TEXT("INVALID_COMMITTED_LINEAGE"));
        return false;
    }
    if (WouldCommitOverflowEmptyReturnQueue())
    {
        OutReason = TEXT("Empty-stillage return queue has no safe capacity");
        RefreshOperatingState();
        return false;
    }

    TArray<FLBBodyWeldPanelUnit*> PanelsToCommit;
    PanelsToCommit.Reserve(ActiveReservation.Panels.Num());
    for (const FLBBodyWeldPanelLineage& Reserved : ActiveReservation.Panels)
    {
        FLBBodyWeldStillageInventory* Stillage = Stillages.FindByPredicate(
            [&Reserved](const FLBBodyWeldStillageInventory& Candidate)
            { return Candidate.StillageId == Reserved.StillageId; });
        FLBBodyWeldPanelUnit* Panel = Stillage ? Stillage->PanelUnits.FindByPredicate(
            [&Reserved](const FLBBodyWeldPanelUnit& Candidate)
            { return Candidate.PanelId == Reserved.PanelId; }) : nullptr;
        if (!Stillage || !Panel)
        {
            OutReason = TEXT("Atomic commit lost a preflighted panel identity");
            SetFault(TEXT("INVALID_COMMITTED_LINEAGE"));
            return false;
        }
        PanelsToCommit.Add(Panel);
    }
    FLBBodyWeldBaseKitUnit* Kit = BaseKits.FindByPredicate([this](const FLBBodyWeldBaseKitUnit& Candidate)
        { return Candidate.KitId == ActiveReservation.BaseKitId; });
    if (!Kit)
    {
        OutReason = TEXT("Atomic commit lost a preflighted base-kit identity");
        SetFault(TEXT("INVALID_COMMITTED_LINEAGE"));
        return false;
    }
    // All mutable references have now been resolved. No failure path exists below this point.
    for (FLBBodyWeldPanelUnit* Panel : PanelsToCommit)
    {
        Panel->bReserved = false;
        Panel->bConsumed = true;
    }
    Kit->bReserved = false;
    Kit->bConsumed = true;
    ActiveReservation.bConsumptionCommitted = true;

    TSet<FName> ReservationStillages;
    for (const FLBBodyWeldPanelLineage& Panel : ActiveReservation.Panels)
        ReservationStillages.Add(Panel.StillageId);
    for (const FName StillageId : ReservationStillages)
    {
        FLBBodyWeldStillageInventory* Stillage = Stillages.FindByPredicate(
            [StillageId](const FLBBodyWeldStillageInventory& Candidate)
            { return Candidate.StillageId == StillageId; });
        if (!Stillage || Stillage->bEmptyReturnQueued || Stillage->bEmptyReturnIssued) continue;
        const bool bEmpty = !Stillage->PanelUnits.ContainsByPredicate(
            [](const FLBBodyWeldPanelUnit& Panel) { return !Panel.bConsumed; });
        if (!bEmpty) continue;
        FLBBodyWeldEmptyStillageReturn& Return = PendingEmptyReturns.AddDefaulted_GetRef();
        Return.StillageId = Stillage->StillageId;
        Return.OrderId = Stillage->OrderId;
        Return.VehicleModelId = Stillage->VehicleModelId;
        Return.PanelTypeId = Stillage->PanelTypeId;
        Return.QueueSequence = NextEventSequence++;
        Stillage->bEmptyReturnQueued = true;
    }

    Phase = ELBBodyWeldPhase::ClosurePreparation;
    PhaseProgress01 = 0.0f;
    ActiveCycleQualityConditions = QualityConditions;
    ActiveCycleEvidence = FLBBodyWeldCycleEvidence();
    RefreshOperatingState();
    return true;
}

void ALBBodyWeldLineActor::AdvanceSimulation(const float DeltaSeconds)
{
    if (!FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.0f || bFaulted || !bEnabled
        || bPaused || bServiceHeld) return;
    float RemainingDelta = DeltaSeconds;
    // Four timed phases plus the two instantaneous recipe transitions. The guard makes
    // malformed future phase edits fail boundedly instead of spinning in a frame.
    for (int32 TransitionGuard = 0; TransitionGuard < 8 && RemainingDelta > UE_SMALL_NUMBER;
        ++TransitionGuard)
    {
        if (Phase == ELBBodyWeldPhase::AwaitingRecipe)
        {
            FString Reason;
            if (ActiveReservation.bValid || bHasOutputBody || bHasReworkBody
                || !TryReserveRecipe(Reason)) return;
            continue;
        }
        if (Phase == ELBBodyWeldPhase::ReservingInputs)
        {
            FString Reason;
            if (!CommitReservedInputs(Reason)) return;
            continue;
        }
        if (Phase == ELBBodyWeldPhase::OutputReady
            || Phase == ELBBodyWeldPhase::TransferringToED)
        {
            RefreshOperatingState();
            return;
        }
        if (!ActiveReservation.bValid || !ActiveReservation.bConsumptionCommitted)
        {
            SetFault(TEXT("INVALID_COMMITTED_LINEAGE"));
            return;
        }

        float* EvidenceSeconds = nullptr;
        float Duration = 1.0f;
        switch (Phase)
        {
        case ELBBodyWeldPhase::ClosurePreparation:
            EvidenceSeconds = &ActiveCycleEvidence.ClosurePreparationSeconds;
            Duration = ClosurePreparationDurationSeconds;
            break;
        case ELBBodyWeldPhase::Framing:
            EvidenceSeconds = &ActiveCycleEvidence.FramingSeconds;
            Duration = FramingDurationSeconds;
            break;
        case ELBBodyWeldPhase::Welding:
            EvidenceSeconds = &ActiveCycleEvidence.WeldingSeconds;
            Duration = WeldingDurationSeconds;
            break;
        case ELBBodyWeldPhase::GeometryCheck:
            EvidenceSeconds = &ActiveCycleEvidence.GeometryCheckSeconds;
            Duration = GeometryCheckDurationSeconds;
            break;
        default:
            return;
        }

        const float PhaseRemaining = FMath::Max(0.0f, Duration - *EvidenceSeconds);
        const float Advanced = FMath::Min(RemainingDelta, PhaseRemaining);
        *EvidenceSeconds += Advanced;
        RemainingDelta -= Advanced;
        PhaseProgress01 = FMath::Clamp(*EvidenceSeconds / Duration, 0.0f, 1.0f);
        if (Phase == ELBBodyWeldPhase::ClosurePreparation || Phase == ELBBodyWeldPhase::Framing)
            RobotBaseWear01 = FMath::Clamp(RobotBaseWear01 + Advanced * 0.0005f, 0.0f, 1.0f);
        else if (Phase == ELBBodyWeldPhase::Welding)
        {
            RobotBaseWear01 = FMath::Clamp(RobotBaseWear01 + Advanced * 0.0010f, 0.0f, 1.0f);
            SpotHeadWear01 = FMath::Clamp(SpotHeadWear01 + Advanced * 0.0010f, 0.0f, 1.0f);
            MIGHeadWear01 = FMath::Clamp(MIGHeadWear01 + Advanced * 0.0005f, 0.0f, 1.0f);
        }
        if (PhaseProgress01 < 1.0f) break;
        AdvanceToNextPhase();
    }
    RefreshOperatingState();
}

void ALBBodyWeldLineActor::AdvanceToNextPhase()
{
    PhaseProgress01 = 0.0f;
    switch (Phase)
    {
    case ELBBodyWeldPhase::ClosurePreparation: Phase = ELBBodyWeldPhase::Framing; break;
    case ELBBodyWeldPhase::Framing: Phase = ELBBodyWeldPhase::Welding; break;
    case ELBBodyWeldPhase::Welding: Phase = ELBBodyWeldPhase::GeometryCheck; break;
    case ELBBodyWeldPhase::GeometryCheck: FinalizeGeometryGate(); break;
    default: break;
    }
}

FLBBodyWeldQualityEvidence ALBBodyWeldLineActor::BuildQualityEvidence() const
{
    FLBBodyWeldQualityEvidence Evidence;
    Evidence.bRecipeComplete = ActiveReservation.bValid
        && ActiveReservation.bConsumptionCommitted
        && ValidateActiveReservationReferences(true);
    Evidence.bFixtureProgramCorrect = ActiveCycleQualityConditions.bFixtureProgramCorrect;
    Evidence.bSpotOperationsComplete = ActiveCycleEvidence.WeldingSeconds >= WeldingDurationSeconds;
    Evidence.bMIGOperationsComplete = ActiveCycleEvidence.WeldingSeconds >= WeldingDurationSeconds;
    Evidence.bRobotCalibrationInTolerance = ActiveCycleQualityConditions.bRobotCalibrationInTolerance;
    Evidence.bServiceConditionAcceptable = ActiveCycleQualityConditions.bServiceConditionAcceptable;
    Evidence.bSafetyInterlockClear = ActiveCycleQualityConditions.bSafetyInterlockClear;
    if (!Evidence.bRecipeComplete) Evidence.ReasonCodes.Add(TEXT("RECIPE_INCOMPLETE"));
    if (!Evidence.bFixtureProgramCorrect) Evidence.ReasonCodes.Add(TEXT("FIXTURE_PROGRAM_MISMATCH"));
    if (!Evidence.bSpotOperationsComplete) Evidence.ReasonCodes.Add(TEXT("SPOT_OPERATIONS_INCOMPLETE"));
    if (!Evidence.bMIGOperationsComplete) Evidence.ReasonCodes.Add(TEXT("MIG_OPERATIONS_INCOMPLETE"));
    if (!Evidence.bRobotCalibrationInTolerance) Evidence.ReasonCodes.Add(TEXT("ROBOT_CALIBRATION_OUT_OF_TOLERANCE"));
    if (!Evidence.bServiceConditionAcceptable) Evidence.ReasonCodes.Add(TEXT("SERVICE_CONDITION_UNACCEPTABLE"));
    if (!Evidence.bSafetyInterlockClear) Evidence.ReasonCodes.Add(TEXT("SAFETY_INTERLOCK_VIOLATION"));
    return Evidence;
}

ELBBodyWeldQualityState ALBBodyWeldLineActor::EvaluateQuality(
    const FLBBodyWeldQualityEvidence& Evidence)
{
    if (!Evidence.bRecipeComplete || !Evidence.bSafetyInterlockClear)
        return ELBBodyWeldQualityState::Rejected;
    if (!Evidence.bFixtureProgramCorrect || !Evidence.bSpotOperationsComplete
        || !Evidence.bMIGOperationsComplete || !Evidence.bRobotCalibrationInTolerance
        || !Evidence.bServiceConditionAcceptable)
        return ELBBodyWeldQualityState::ReworkRequired;
    return ELBBodyWeldQualityState::Good;
}

void ALBBodyWeldLineActor::FinalizeGeometryGate()
{
    if (!ActiveReservation.bValid || !ActiveReservation.bConsumptionCommitted)
    {
        SetFault(TEXT("INVALID_COMMITTED_LINEAGE"));
        return;
    }
    FLBBodyInWhiteRecord Body;
    Body.BodyId = FName(*FString::Printf(TEXT("BIW-%s-%s-%06d"),
        *StableIdentityToken(ActiveReservation.VehicleModelId), *StableIdentityToken(LineId), NextBodySerial++));
    Body.VehicleModelId = ActiveReservation.VehicleModelId;
    Body.OrderId = ActiveReservation.OrderId;
    Body.BaseKitId = ActiveReservation.BaseKitId;
    Body.ReservationId = ActiveReservation.ReservationId;
    Body.WeldLineId = LineId;
    Body.Panels = ActiveReservation.Panels;
    Body.QualityEvidence = BuildQualityEvidence();
    Body.QualityState = EvaluateQuality(Body.QualityEvidence);
    ActiveCycleEvidence.CompletionSequence = NextEventSequence++;
    Body.CycleEvidence = ActiveCycleEvidence;

    ActiveReservation = FLBBodyWeldInputReservation();
    ActiveCycleQualityConditions = FLBBodyWeldQualityConditions();
    ActiveCycleEvidence = FLBBodyWeldCycleEvidence();
    if (Body.QualityState == ELBBodyWeldQualityState::Good)
    {
        OutputBody = MoveTemp(Body);
        bHasOutputBody = true;
        Phase = ELBBodyWeldPhase::OutputReady;
    }
    else
    {
        ReworkBody = MoveTemp(Body);
        bHasReworkBody = true;
        Phase = ELBBodyWeldPhase::AwaitingRecipe;
    }
    PhaseProgress01 = 0.0f;
    RefreshPresentation();
}

bool ALBBodyWeldLineActor::RetryHeldBody(FString& OutReason)
{
    OutReason.Reset();
    if (!bHasReworkBody || ReworkBody.QualityState == ELBBodyWeldQualityState::Rejected)
    {
        OutReason = TEXT("No recoverable BIW is held for rework");
        return false;
    }
    FLBBodyWeldQualityEvidence Evidence = ReworkBody.QualityEvidence;
    Evidence.bFixtureProgramCorrect = QualityConditions.bFixtureProgramCorrect;
    Evidence.bRobotCalibrationInTolerance = QualityConditions.bRobotCalibrationInTolerance;
    Evidence.bServiceConditionAcceptable = QualityConditions.bServiceConditionAcceptable;
    Evidence.bSafetyInterlockClear = QualityConditions.bSafetyInterlockClear;
    Evidence.ReasonCodes.Reset();
    if (!Evidence.bFixtureProgramCorrect) Evidence.ReasonCodes.Add(TEXT("FIXTURE_PROGRAM_MISMATCH"));
    if (!Evidence.bRobotCalibrationInTolerance) Evidence.ReasonCodes.Add(TEXT("ROBOT_CALIBRATION_OUT_OF_TOLERANCE"));
    if (!Evidence.bServiceConditionAcceptable) Evidence.ReasonCodes.Add(TEXT("SERVICE_CONDITION_UNACCEPTABLE"));
    if (!Evidence.bSafetyInterlockClear) Evidence.ReasonCodes.Add(TEXT("SAFETY_INTERLOCK_VIOLATION"));
    ReworkBody.QualityEvidence = Evidence;
    ReworkBody.QualityState = EvaluateQuality(Evidence);
    if (ReworkBody.QualityState != ELBBodyWeldQualityState::Good)
    {
        OutReason = TEXT("Deterministic rework evidence still fails the geometry gate");
        RefreshOperatingState();
        return false;
    }
    OutputBody = ReworkBody;
    bHasOutputBody = true;
    ReworkBody = FLBBodyInWhiteRecord();
    bHasReworkBody = false;
    Phase = ELBBodyWeldPhase::OutputReady;
    RefreshOperatingState();
    return true;
}

bool ALBBodyWeldLineActor::AcknowledgeEDTransfer(const FName BodyId,
    FLBBodyInWhiteRecord& OutTransferredBody)
{
    OutTransferredBody = FLBBodyInWhiteRecord();
    if (!bEDAvailable || !bHasOutputBody || BodyId.IsNone() || OutputBody.BodyId != BodyId
        || OutputBody.bEDAccepted || OutputBody.QualityState != ELBBodyWeldQualityState::Good)
        return false;
    Phase = ELBBodyWeldPhase::TransferringToED;
    OutputBody.bEDAccepted = true;
    OutTransferredBody = OutputBody;
    CompletedBodies.Add(OutputBody);
    OutputBody = FLBBodyInWhiteRecord();
    bHasOutputBody = false;
    Phase = ELBBodyWeldPhase::AwaitingRecipe;
    PhaseProgress01 = 0.0f;
    RefreshOperatingState();
    return true;
}

bool ALBBodyWeldLineActor::GetActiveReservation(FLBBodyWeldInputReservation& OutReservation) const
{
    OutReservation = ActiveReservation;
    return ActiveReservation.bValid;
}

bool ALBBodyWeldLineActor::GetOutputBody(FLBBodyInWhiteRecord& OutBody) const
{
    OutBody = OutputBody;
    return bHasOutputBody;
}

bool ALBBodyWeldLineActor::GetReworkBody(FLBBodyInWhiteRecord& OutBody) const
{
    OutBody = ReworkBody;
    return bHasReworkBody;
}

int32 ALBBodyWeldLineActor::GetAvailablePanelCount() const
{
    int32 Count = 0;
    for (const FLBBodyWeldStillageInventory& Stillage : Stillages)
        for (const FLBBodyWeldPanelUnit& Panel : Stillage.PanelUnits)
            Count += !Panel.bReserved && !Panel.bConsumed ? 1 : 0;
    return Count;
}

int32 ALBBodyWeldLineActor::GetReservedPanelCount() const
{
    int32 Count = 0;
    for (const FLBBodyWeldStillageInventory& Stillage : Stillages)
        for (const FLBBodyWeldPanelUnit& Panel : Stillage.PanelUnits) Count += Panel.bReserved ? 1 : 0;
    return Count;
}

int32 ALBBodyWeldLineActor::GetAvailableBaseKitCount() const
{
    int32 Count = 0;
    for (const FLBBodyWeldBaseKitUnit& Kit : BaseKits)
        Count += !Kit.bReserved && !Kit.bConsumed ? 1 : 0;
    return Count;
}

void ALBBodyWeldLineActor::SetFault(const FName Reason)
{
    bFaulted = true;
    FaultReason = Reason.IsNone() ? FName(TEXT("UNSPECIFIED_FAULT")) : Reason;
    RefreshOperatingState();
}

void ALBBodyWeldLineActor::RefreshOperatingState()
{
    ELBFactoryMachineOperatingState NewState = ELBFactoryMachineOperatingState::Idle;
    FString NewReason;
    if (bFaulted)
    {
        NewState = ELBFactoryMachineOperatingState::Fault;
        NewReason = FaultReason.ToString();
    }
    else if (!bEnabled)
    {
        NewState = ELBFactoryMachineOperatingState::Idle;
        NewReason = TEXT("Body Weld Line disabled");
    }
    else if (bPaused)
    {
        NewState = ELBFactoryMachineOperatingState::Idle;
        NewReason = TEXT("Body Weld Line paused");
    }
    else if (bServiceHeld)
    {
        NewState = ELBFactoryMachineOperatingState::Blocked;
        NewReason = TEXT("Planned service hold");
    }
    else if (bHasReworkBody)
    {
        NewState = ELBFactoryMachineOperatingState::Blocked;
        NewReason = TEXT("Geometry gate rework hold occupied");
    }
    else if (bHasOutputBody)
    {
        NewState = ELBFactoryMachineOperatingState::Blocked;
        NewReason = bEDAvailable ? TEXT("BIW awaits exact ED acknowledgement")
            : TEXT("BIW output full: ED unavailable");
    }
    else if (ActiveReservation.bValid)
    {
        NewState = ELBFactoryMachineOperatingState::Processing;
        NewReason = FString::Printf(TEXT("Body weld phase: %s"),
            *StaticEnum<ELBBodyWeldPhase>()->GetNameStringByValue(static_cast<int64>(Phase)));
    }
    else
    {
        FString Missing;
        if (FindFirstMissingRecipeItem(Missing))
        {
            NewState = AssignedOrderId.IsNone()
                ? ELBFactoryMachineOperatingState::Idle : ELBFactoryMachineOperatingState::Starved;
            NewReason = Missing;
        }
        else
        {
            NewState = ELBFactoryMachineOperatingState::Ready;
            NewReason = TEXT("Complete exact Cairnwell recipe available");
        }
    }
    OperatingState = NewState;
    OperatingReason = MoveTemp(NewReason);
    RefreshPresentation();
}

void ALBBodyWeldLineActor::RefreshPresentation()
{
    if (StatusBeacon)
    {
        ELBStatusBeaconState Beacon = ELBStatusBeaconState::Idle;
        switch (OperatingState)
        {
        case ELBFactoryMachineOperatingState::Ready: Beacon = ELBStatusBeaconState::Ready; break;
        case ELBFactoryMachineOperatingState::Processing: Beacon = ELBStatusBeaconState::Running; break;
        case ELBFactoryMachineOperatingState::Starved:
        case ELBFactoryMachineOperatingState::Blocked: Beacon = ELBStatusBeaconState::Waiting; break;
        case ELBFactoryMachineOperatingState::Fault: Beacon = ELBStatusBeaconState::Fault; break;
        default: Beacon = ELBStatusBeaconState::Idle; break;
        }
        StatusBeacon->SetStatus(Beacon);
    }
    const bool bBodyAtOutput = bHasOutputBody || bHasReworkBody;
    const bool bCommittedWorkpiece = ActiveReservation.bValid
        && ActiveReservation.bConsumptionCommitted;
    const bool bPresentBaseKit = bCommittedWorkpiece || bBodyAtOutput;
    if (BaseKitWorkpieceRoot)
    {
        BaseKitWorkpieceRoot->SetRelativeLocation(
            FVector(bBodyAtOutput ? 4750.0f : 2700.0f, 0.0f, 0.0f));
        BaseKitWorkpieceRoot->SetVisibility(bPresentBaseKit, true);
    }
    const bool bHasImportedUnderbody = BaseKitUnderbodyPresentation
        && BaseKitUnderbodyPresentation->GetStaticMesh();
    if (BIWProxy) BIWProxy->SetVisibility(bBodyAtOutput && !bHasImportedUnderbody, true);
    if (BIWProxyInstances) BIWProxyInstances->SetVisibility(bBodyAtOutput, true);
}

UStaticMesh* ALBBodyWeldLineActor::ResolveMesh(
    const TSoftObjectPtr<UStaticMesh>& Reference) const
{
    if (Reference.IsNull()) return nullptr;
    if (UStaticMesh* Loaded = Reference.Get()) return Loaded;
    return bLoadReferencedMeshesSynchronously ? Reference.LoadSynchronous() : nullptr;
}

void ALBBodyWeldLineActor::ResolveRuntimeVisuals()
{
    if (FramingFixturePresentation)
    {
        FramingFixturePresentation->SetStaticMesh(ResolveMesh(FramingFixtureMesh));
        ApplyRuntimeArtMaterials(FramingFixturePresentation);
    }
    if (BaseKitSkidPresentation)
    {
        BaseKitSkidPresentation->SetStaticMesh(ResolveMesh(BaseKitSkidMesh));
        ApplyRuntimeArtMaterials(BaseKitSkidPresentation);
    }
    if (BaseKitUnderbodyPresentation)
    {
        BaseKitUnderbodyPresentation->SetStaticMesh(ResolveMesh(BaseKitUnderbodyMesh));
        ApplyRuntimeArtMaterials(BaseKitUnderbodyPresentation);
    }
    ResolveRobotRuntimeVisuals();
}

void ALBBodyWeldLineActor::ResolveRobotRuntimeVisuals()
{
    UStaticMesh* SharedBase = ResolveMesh(WeldRobotSharedBaseMesh);
    UStaticMesh* MIGTool = ResolveMesh(WeldRobotMIGToolMesh);
    UStaticMesh* SpotTool = ResolveMesh(WeldRobotSpotToolMesh);
    UStaticMesh* PanelPickTool = ResolveMesh(WeldRobotPanelPickToolMesh);

    for (int32 StationIndex = 0; StationIndex < RobotStationCount; ++StationIndex)
    {
        UStaticMeshComponent* Base = GetRobotBasePresentation(StationIndex);
        UStaticMeshComponent* Tool = GetRobotToolPresentation(StationIndex);
        if (!Base || !Tool) continue;

        const FName ToolRole = GetRobotStationToolRole(StationIndex);
        UStaticMesh* RequiredTool = ToolRole == LBBodyWeldPrivate::RobotToolMIG ? MIGTool
            : ToolRole == LBBodyWeldPrivate::RobotToolSpot ? SpotTool
            : ToolRole == LBBodyWeldPrivate::RobotToolPanelPick ? PanelPickTool : nullptr;
        const bool bCompletePair = SharedBase && RequiredTool;

        // Clear any stale override before changing mesh: approved source materials must
        // remain exact. A station is either the complete pair or no imported art at all.
        Base->EmptyOverrideMaterials();
        Tool->EmptyOverrideMaterials();
        Base->SetStaticMesh(bCompletePair ? SharedBase : nullptr);
        Tool->SetStaticMesh(bCompletePair ? RequiredTool : nullptr);
        Base->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Tool->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Base->SetGenerateOverlapEvents(false);
        Tool->SetGenerateOverlapEvents(false);
        Base->SetCanEverAffectNavigation(false);
        Tool->SetCanEverAffectNavigation(false);
        Base->SetSimulatePhysics(false);
        Tool->SetSimulatePhysics(false);
        Base->SetVisibility(bCompletePair, true);
        Tool->SetVisibility(bCompletePair, true);
    }
}

bool ALBBodyWeldLineActor::IsRobotStationUsingRuntimeArt(const int32 StationIndex) const
{
    const UStaticMeshComponent* Base = GetRobotBasePresentation(StationIndex);
    const UStaticMeshComponent* Tool = GetRobotToolPresentation(StationIndex);
    if (!Base || !Tool || !Base->GetStaticMesh() || !Tool->GetStaticMesh()) return false;

    const UStaticMesh* ExpectedBase = WeldRobotSharedBaseMesh.Get();
    const FName ToolRole = GetRobotStationToolRole(StationIndex);
    const UStaticMesh* ExpectedTool = ToolRole == LBBodyWeldPrivate::RobotToolMIG
        ? WeldRobotMIGToolMesh.Get()
        : ToolRole == LBBodyWeldPrivate::RobotToolSpot ? WeldRobotSpotToolMesh.Get()
        : ToolRole == LBBodyWeldPrivate::RobotToolPanelPick
            ? WeldRobotPanelPickToolMesh.Get() : nullptr;
    return ExpectedBase && ExpectedTool
        && Base->GetStaticMesh() == ExpectedBase && Tool->GetStaticMesh() == ExpectedTool
        && Base->IsVisible() && Tool->IsVisible()
        && Base->GetCollisionEnabled() == ECollisionEnabled::NoCollision
        && Tool->GetCollisionEnabled() == ECollisionEnabled::NoCollision
        && !Base->CanEverAffectNavigation() && !Tool->CanEverAffectNavigation()
        && !Base->GetGenerateOverlapEvents() && !Tool->GetGenerateOverlapEvents();
}

void ALBBodyWeldLineActor::ApplyRuntimeArtMaterials(UStaticMeshComponent* Component)
{
    if (!Component || !Component->GetStaticMesh() || !BasicPresentationMaterial) return;
    const TArray<FStaticMaterial>& Slots = Component->GetStaticMesh()->GetStaticMaterials();
    for (int32 SlotIndex = 0; SlotIndex < Slots.Num(); ++SlotIndex)
    {
        UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(
            BasicPresentationMaterial, Component);
        if (!Material) continue;
        const FLinearColor Colour = LBBodyWeldPrivate::RuntimeArtColourForSlot(
            Slots[SlotIndex].MaterialSlotName);
        Material->SetVectorParameterValue(TEXT("Color"), Colour);
        Material->SetVectorParameterValue(TEXT("BaseColor"), Colour);
        Component->SetMaterial(SlotIndex, Material);
    }
}

void ALBBodyWeldLineActor::AddBoxInstance(UHierarchicalInstancedStaticMeshComponent* Component,
    const FVector& CentreCm, const FVector& SizeCm) const
{
    if (!Component || !CubeFallbackMesh || SizeCm.GetMin() <= 0.0f) return;
    Component->AddInstance(FTransform(FRotator::ZeroRotator, CentreCm, SizeCm / 100.0f));
}

void ALBBodyWeldLineActor::RebuildProxyVisuals()
{
    if (!PrimaryMachineInstances || !SecondaryMachineInstances || !SafetyInstances
        || !BIWProxyInstances) return;
    PrimaryMachineInstances->ClearInstances();
    SecondaryMachineInstances->ClearInstances();
    SafetyInstances->ClearInstances();
    BIWProxyInstances->ClearInstances();

    // The old five generic cube islands only existed to make an otherwise empty
    // prototype readable.  Once the authored fixture is available they visually
    // compete with it, so retain the real fixture, robots and floor-safety cues
    // instead of surrounding them with false gantries and green plinths.
    const bool bHasFixtureArt = FramingFixturePresentation
        && FramingFixturePresentation->GetStaticMesh();
    if (!bHasFixtureArt)
    {
        for (int32 Station = 0; Station < 5; ++Station)
        {
            const float X = 500.0f + Station * 1100.0f;
            AddBoxInstance(SecondaryMachineInstances, FVector(X, -700.0f, 180.0f), FVector(55.0f, 55.0f, 360.0f));
            AddBoxInstance(SecondaryMachineInstances, FVector(X, 700.0f, 180.0f), FVector(55.0f, 55.0f, 360.0f));
            AddBoxInstance(SecondaryMachineInstances, FVector(X, 0.0f, 360.0f), FVector(55.0f, 1455.0f, 55.0f));
            AddBoxInstance(PrimaryMachineInstances, FVector(X, 0.0f, 65.0f), FVector(760.0f, 450.0f, 130.0f));
        }
    }
    // Atomic per-station fallback: suppress a cube triplet only when both the validated
    // shared base and that station's exact role tool resolved and remain presentation-only.
    for (int32 StationIndex = 0; StationIndex < RobotStationCount; ++StationIndex)
    {
        if (IsRobotStationUsingRuntimeArt(StationIndex)) continue;
        const FVector Root = LBBodyWeldPrivate::RobotStations[StationIndex].RootLocationCm;
        AddBoxInstance(PrimaryMachineInstances, Root + FVector(0.0f, 0.0f, 120.0f), FVector(180.0f, 180.0f, 240.0f));
        AddBoxInstance(SecondaryMachineInstances, Root + FVector(0.0f, 0.0f, 320.0f), FVector(90.0f, 90.0f, 300.0f));
        AddBoxInstance(SafetyInstances, Root + FVector(120.0f, 0.0f, 455.0f), FVector(240.0f, 70.0f, 70.0f));
    }
    if (!bHasFixtureArt)
    {
        AddBoxInstance(SafetyInstances, FVector(0.0f, -900.0f, 40.0f), FVector(600.0f, 500.0f, 80.0f));
        AddBoxInstance(SafetyInstances, FVector(0.0f, 900.0f, 40.0f), FVector(600.0f, 500.0f, 80.0f));
    }

    LBBodyWeldPrivate::ApplyColour(SafetyInstances,
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("F2C94C"))));
    // A recognisable lightweight body-frame proxy: sill/roof rails, crossmembers and
    // A/B/C pillars. It is deliberately a skeleton rather than a false finished car.
    for (const float Y : {-78.0f, 78.0f})
    {
        AddBoxInstance(BIWProxyInstances, FVector(4750.0f, Y, 85.0f), FVector(440.0f, 10.0f, 14.0f));
        AddBoxInstance(BIWProxyInstances, FVector(4750.0f, Y, 205.0f), FVector(270.0f, 10.0f, 12.0f));
        for (const float X : {4630.0f, 4750.0f, 4870.0f})
            AddBoxInstance(BIWProxyInstances, FVector(X, Y, 145.0f), FVector(12.0f, 12.0f, 125.0f));
    }
    for (const float X : {4560.0f, 4750.0f, 4940.0f})
        AddBoxInstance(BIWProxyInstances, FVector(X, 0.0f, 80.0f), FVector(12.0f, 170.0f, 12.0f));
    LBBodyWeldPrivate::ApplyColour(BIWProxyInstances,
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("C9D1D9"))));
    LBBodyWeldPrivate::ApplyColour(BIWProxy,
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("C9D1D9"))));

    if (FloorMarkings)
    {
        FloorMarkings->ClearMarkings();
        FloorMarkings->AddRectangleOutline(FVector2D(2700.0f, 0.0f), FVector2D(2900.0f, 1400.0f),
            0.0f, 10.0f, ELBFactoryFloorMarkingSemantic::ServiceEnvelope);
        // A single, restrained hatch follows the real framing fixture. The former
        // five 90 cm-pitch proxy hatches covered the complete cell and became the
        // dominant visual from the management camera.
        FloorMarkings->AddDiagonalHatching(FVector2D(2700.0f, 0.0f),
            FVector2D(360.0f, 320.0f), 0.0f, 8.0f, 160.0f,
            ELBFactoryFloorMarkingSemantic::KeepClearHatch);
        FloorMarkings->AddFilledRectangle(FVector2D(0.0f, -900.0f), FVector2D(300.0f, 250.0f),
            0.0f, ELBFactoryFloorMarkingSemantic::StillageLoadingBay);
    }
}

int32 ALBBodyWeldLineActor::GetProxyPartCount() const
{
    return (PrimaryMachineInstances ? PrimaryMachineInstances->GetInstanceCount() : 0)
        + (SecondaryMachineInstances ? SecondaryMachineInstances->GetInstanceCount() : 0)
        + (SafetyInstances ? SafetyInstances->GetInstanceCount() : 0)
        + (BIWProxyInstances && BIWProxyInstances->IsVisible()
            ? BIWProxyInstances->GetInstanceCount() : 0)
        + (BIWProxy && BIWProxy->IsVisible() ? 1 : 0)
        + (FramingFixturePresentation && FramingFixturePresentation->GetStaticMesh() ? 1 : 0)
        + (BaseKitSkidPresentation && BaseKitSkidPresentation->GetStaticMesh()
            && BaseKitSkidPresentation->IsVisible() ? 1 : 0)
        + (BaseKitUnderbodyPresentation && BaseKitUnderbodyPresentation->GetStaticMesh()
            && BaseKitUnderbodyPresentation->IsVisible() ? 1 : 0)
        + GetImportedRobotPartCount();
}

bool ALBBodyWeldLineActor::HasResolvedRuntimeArt() const
{
    return FramingFixturePresentation && FramingFixturePresentation->GetStaticMesh()
        && BaseKitSkidPresentation && BaseKitSkidPresentation->GetStaticMesh()
        && BaseKitUnderbodyPresentation && BaseKitUnderbodyPresentation->GetStaticMesh();
}

bool ALBBodyWeldLineActor::IsBaseKitWorkpiecePresented() const
{
    return BaseKitWorkpieceRoot && BaseKitWorkpieceRoot->IsVisible()
        && BaseKitSkidPresentation && BaseKitSkidPresentation->IsVisible()
        && BaseKitUnderbodyPresentation && BaseKitUnderbodyPresentation->IsVisible();
}

int32 ALBBodyWeldLineActor::GetResolvedRobotStationCount() const
{
    int32 Resolved = 0;
    for (int32 StationIndex = 0; StationIndex < RobotStationCount; ++StationIndex)
        Resolved += IsRobotStationUsingRuntimeArt(StationIndex) ? 1 : 0;
    return Resolved;
}

int32 ALBBodyWeldLineActor::GetFallbackRobotStationCount() const
{
    return RobotStationCount - GetResolvedRobotStationCount();
}

int32 ALBBodyWeldLineActor::GetImportedRobotPartCount() const
{
    return GetResolvedRobotStationCount() * 2;
}

int32 ALBBodyWeldLineActor::GetRobotProxyPartCount() const
{
    return GetFallbackRobotStationCount() * 3;
}

bool ALBBodyWeldLineActor::HasResolvedRobotRuntimeArt() const
{
    return GetResolvedRobotStationCount() == RobotStationCount;
}

TArray<FString> ALBBodyWeldLineActor::GetRobotRuntimeArtPaths() const
{
    return {
        WeldRobotSharedBaseMesh.ToSoftObjectPath().ToString(),
        WeldRobotMIGToolMesh.ToSoftObjectPath().ToString(),
        WeldRobotSpotToolMesh.ToSoftObjectPath().ToString(),
        WeldRobotPanelPickToolMesh.ToSoftObjectPath().ToString()
    };
}

FName ALBBodyWeldLineActor::GetRobotStationToolRole(const int32 StationIndex) const
{
    return StationIndex >= 0 && StationIndex < RobotStationCount
        ? LBBodyWeldPrivate::RobotStations[StationIndex].ToolRole : NAME_None;
}

UStaticMeshComponent* ALBBodyWeldLineActor::GetRobotBasePresentation(
    const int32 StationIndex) const
{
    return RobotBasePresentations.IsValidIndex(StationIndex)
        ? RobotBasePresentations[StationIndex] : nullptr;
}

UStaticMeshComponent* ALBBodyWeldLineActor::GetRobotToolPresentation(
    const int32 StationIndex) const
{
    return RobotToolPresentations.IsValidIndex(StationIndex)
        ? RobotToolPresentations[StationIndex] : nullptr;
}

FVector ALBBodyWeldLineActor::GetRobotToolFlangeRelativeLocation() const
{
    return LBBodyWeldPrivate::RobotToolFlangeRelativeCm;
}

#if WITH_DEV_AUTOMATION_TESTS
void ALBBodyWeldLineActor::SetRobotRuntimeArtReferencesForTests(
    const FSoftObjectPath& SharedBasePath, const FSoftObjectPath& MIGToolPath,
    const FSoftObjectPath& SpotToolPath, const FSoftObjectPath& PanelPickToolPath)
{
    WeldRobotSharedBaseMesh = TSoftObjectPtr<UStaticMesh>(SharedBasePath);
    WeldRobotMIGToolMesh = TSoftObjectPtr<UStaticMesh>(MIGToolPath);
    WeldRobotSpotToolMesh = TSoftObjectPtr<UStaticMesh>(SpotToolPath);
    WeldRobotPanelPickToolMesh = TSoftObjectPtr<UStaticMesh>(PanelPickToolPath);
    ResolveRobotRuntimeVisuals();
    RebuildProxyVisuals();
    RefreshPresentation();
}
#endif

FString ALBBodyWeldLineActor::StableIdentityToken(const FName Source)
{
    FString Token = Source.IsNone() ? TEXT("UNCONFIGURED") : Source.ToString();
    for (TCHAR& Character : Token)
        if (!FChar::IsAlnum(Character) && Character != TEXT('_') && Character != TEXT('-'))
            Character = TEXT('_');
    return Token.ToUpper();
}

bool ALBBodyWeldLineActor::IsStillageContractValid(const FLBBodyWeldStillageInventory& Stillage)
{
    TArray<FName> Families;
    FName BaseKitTypeId;
    if (Stillage.StillageId.IsNone() || Stillage.OrderId.IsNone()
        || !LBVehicleModelCatalog::GetBodyWeldContract(Stillage.VehicleModelId, Families, BaseKitTypeId)
        || !Families.Contains(Stillage.PanelTypeId)
        || Stillage.DeliverySequence < 0 || Stillage.CapacityPanels < 1
        || Stillage.PanelUnits.IsEmpty() || Stillage.PanelUnits.Num() > Stillage.CapacityPanels
        || Stillage.bEmptyReturnQueued || Stillage.bEmptyReturnIssued) return false;
    TSet<FName> PanelIds;
    for (const FLBBodyWeldPanelUnit& Panel : Stillage.PanelUnits)
    {
        FName ParsedVehicle;
        FName ParsedFamily;
        if (!LBBodyWeldPrivate::AddUniqueId(PanelIds, Panel.PanelId)
            || !LBVehicleModelCatalog::ParsePressedPanelUnitId(
                Panel.PanelId, ParsedVehicle, ParsedFamily)
            || ParsedVehicle != Stillage.VehicleModelId || ParsedFamily != Stillage.PanelTypeId
            || Panel.OrderId != Stillage.OrderId || Panel.VehicleModelId != Stillage.VehicleModelId
            || Panel.PanelTypeId != Stillage.PanelTypeId || Panel.StillageId != Stillage.StillageId
            || Panel.bReserved || Panel.bConsumed) return false;
    }
    return true;
}

bool ALBBodyWeldLineActor::IsBaseKitContractValid(const FLBBodyWeldBaseKitUnit& BaseKit)
{
    TArray<FName> Families;
    FName ExpectedBaseKitTypeId;
    return !BaseKit.KitId.IsNone() && !BaseKit.OrderId.IsNone()
        && LBVehicleModelCatalog::GetBodyWeldContract(BaseKit.VehicleModelId, Families, ExpectedBaseKitTypeId)
        && BaseKit.KitTypeId == ExpectedBaseKitTypeId
        && BaseKit.DeliverySequence >= 0 && !BaseKit.bReserved && !BaseKit.bConsumed;
}

bool ALBBodyWeldLineActor::IsBodyRecordContractValid(const FLBBodyInWhiteRecord& Body)
{
    TArray<FName> FamiliesForModel;
    FName BaseKitTypeId;
    if (Body.BodyId.IsNone() || !LBVehicleModelCatalog::GetBodyWeldContract(
            Body.VehicleModelId, FamiliesForModel, BaseKitTypeId)
        || Body.OrderId.IsNone() || Body.BaseKitId.IsNone() || Body.ReservationId.IsNone()
        || Body.WeldLineId.IsNone() || Body.Panels.Num() != FamiliesForModel.Num()
        || !StaticEnum<ELBBodyWeldQualityState>()->IsValidEnumValue(
            static_cast<int64>(Body.QualityState))) return false;
    TSet<FName> Families;
    TSet<FName> PanelIds;
    for (const FLBBodyWeldPanelLineage& Panel : Body.Panels)
    {
        FName Vehicle;
        FName Family;
        if (Panel.StillageId.IsNone() || !LBBodyWeldPrivate::AddUniqueId(PanelIds, Panel.PanelId)
            || !LBBodyWeldPrivate::AddUniqueId(Families, Panel.PanelTypeId)
            || !LBVehicleModelCatalog::ParsePressedPanelUnitId(Panel.PanelId, Vehicle, Family)
            || Vehicle != Body.VehicleModelId || Family != Panel.PanelTypeId
            || !FamiliesForModel.Contains(Family)) return false;
    }
    return Families.Num() == FamiliesForModel.Num()
        && FMath::IsFinite(Body.CycleEvidence.ClosurePreparationSeconds)
        && FMath::IsFinite(Body.CycleEvidence.FramingSeconds)
        && FMath::IsFinite(Body.CycleEvidence.WeldingSeconds)
        && FMath::IsFinite(Body.CycleEvidence.GeometryCheckSeconds)
        && Body.CycleEvidence.CompletionSequence > 0;
}

FLBBodyWeldLineSaveState ALBBodyWeldLineActor::CaptureSaveState() const
{
    FLBBodyWeldLineSaveState State;
    State.LineId = LineId;
    State.WorldTransform = GetActorTransform();
    State.bEnabled = bEnabled;
    State.bPaused = bPaused;
    State.bServiceHeld = bServiceHeld;
    State.bEDAvailable = bEDAvailable;
    State.bFaulted = bFaulted;
    State.FaultReason = FaultReason;
    State.AssignedOrderId = AssignedOrderId;
    State.OperatingState = OperatingState;
    State.OperatingReason = OperatingReason;
    State.Phase = Phase;
    State.PhaseProgress01 = PhaseProgress01;
    State.Stillages = Stillages;
    State.BaseKits = BaseKits;
    State.ActiveReservation = ActiveReservation;
    State.bHasOutputBody = bHasOutputBody;
    State.OutputBody = OutputBody;
    State.bHasReworkBody = bHasReworkBody;
    State.ReworkBody = ReworkBody;
    State.CompletedBodies = CompletedBodies;
    State.PendingEmptyReturns = PendingEmptyReturns;
    State.QualityConditions = QualityConditions;
    State.ActiveCycleQualityConditions = ActiveCycleQualityConditions;
    State.ActiveCycleEvidence = ActiveCycleEvidence;
    State.RobotBaseWear01 = RobotBaseWear01;
    State.SpotHeadWear01 = SpotHeadWear01;
    State.MIGHeadWear01 = MIGHeadWear01;
    State.NextReservationSerial = NextReservationSerial;
    State.NextBodySerial = NextBodySerial;
    State.NextEventSequence = NextEventSequence;
    return State;
}

bool ALBBodyWeldLineActor::IsSaveStateContractValid(const FLBBodyWeldLineSaveState& State)
{
    if (State.Version != 1 || State.LineId.IsNone() || !State.WorldTransform.IsValid()
        || !State.WorldTransform.GetScale3D().Equals(FVector::OneVector, 0.001f)
        || !StaticEnum<ELBFactoryMachineOperatingState>()->IsValidEnumValue(
            static_cast<int64>(State.OperatingState))
        || !StaticEnum<ELBBodyWeldPhase>()->IsValidEnumValue(static_cast<int64>(State.Phase))
        || !FMath::IsFinite(State.PhaseProgress01)
        || !FMath::IsWithinInclusive(State.PhaseProgress01, 0.0f, 1.0f)
        || !FMath::IsFinite(State.RobotBaseWear01) || !FMath::IsFinite(State.SpotHeadWear01)
        || !FMath::IsFinite(State.MIGHeadWear01)
        || !FMath::IsWithinInclusive(State.RobotBaseWear01, 0.0f, 1.0f)
        || !FMath::IsWithinInclusive(State.SpotHeadWear01, 0.0f, 1.0f)
        || !FMath::IsWithinInclusive(State.MIGHeadWear01, 0.0f, 1.0f)
        || State.NextReservationSerial < 1 || State.NextBodySerial < 1
        || State.NextEventSequence < 1 || State.PendingEmptyReturns.Num() > MaximumPendingEmptyReturns
        || (State.bFaulted && State.FaultReason.IsNone())
        || (!State.bFaulted && State.OperatingState == ELBFactoryMachineOperatingState::Fault)
        || (State.bHasOutputBody && State.bHasReworkBody)) return false;

    TSet<FName> GlobalPanelIds;
    TSet<FName> StillageIds;
    TSet<FName> KitIds;
    TSet<FName> BodyIds;
    TSet<FName> ReservationIds;
    TSet<FName> EmptyReturnIds;
    for (const FLBBodyWeldStillageInventory& Stillage : State.Stillages)
    {
        TArray<FName> ModelFamilies;
        FName ModelBaseKitTypeId;
        if (Stillage.StillageId.IsNone() || StillageIds.Contains(Stillage.StillageId)
            || Stillage.DeliverySequence < 0 || Stillage.CapacityPanels < 1
            || Stillage.PanelUnits.Num() > Stillage.CapacityPanels
            || !LBVehicleModelCatalog::GetBodyWeldContract(
                Stillage.VehicleModelId, ModelFamilies, ModelBaseKitTypeId)
            || !ModelFamilies.Contains(Stillage.PanelTypeId)) return false;
        StillageIds.Add(Stillage.StillageId);
        for (const FLBBodyWeldPanelUnit& Panel : Stillage.PanelUnits)
        {
            FName Vehicle;
            FName Family;
            if (!LBBodyWeldPrivate::AddUniqueId(GlobalPanelIds, Panel.PanelId)
                || !LBVehicleModelCatalog::ParsePressedPanelUnitId(Panel.PanelId, Vehicle, Family)
                || Vehicle != Stillage.VehicleModelId || Family != Stillage.PanelTypeId
                || Panel.OrderId != Stillage.OrderId || Panel.StillageId != Stillage.StillageId
                || Panel.VehicleModelId != Stillage.VehicleModelId || Panel.PanelTypeId != Family
                || (Panel.bReserved && Panel.bConsumed)) return false;
        }
        const bool bEmpty = !Stillage.PanelUnits.ContainsByPredicate(
            [](const FLBBodyWeldPanelUnit& Panel) { return !Panel.bConsumed; });
        if ((Stillage.bEmptyReturnQueued || Stillage.bEmptyReturnIssued) != bEmpty
            || (Stillage.bEmptyReturnQueued && Stillage.bEmptyReturnIssued)) return false;
    }
    for (const FLBBodyWeldBaseKitUnit& Kit : State.BaseKits)
    {
        TArray<FName> ModelFamilies;
        FName ModelBaseKitTypeId;
        if (!LBBodyWeldPrivate::AddUniqueId(KitIds, Kit.KitId) || Kit.OrderId.IsNone()
            || !LBVehicleModelCatalog::GetBodyWeldContract(
                Kit.VehicleModelId, ModelFamilies, ModelBaseKitTypeId)
            || Kit.KitTypeId != ModelBaseKitTypeId
            || Kit.DeliverySequence < 0 || (Kit.bReserved && Kit.bConsumed)) return false;
    }
    for (const FLBBodyWeldEmptyStillageReturn& Return : State.PendingEmptyReturns)
    {
        if (!LBBodyWeldPrivate::AddUniqueId(EmptyReturnIds, Return.StillageId)
            || !StillageIds.Contains(Return.StillageId) || Return.QueueSequence < 1) return false;
        const FLBBodyWeldStillageInventory* Stillage = State.Stillages.FindByPredicate(
            [&Return](const FLBBodyWeldStillageInventory& Candidate)
            { return Candidate.StillageId == Return.StillageId; });
        if (!Stillage || !Stillage->bEmptyReturnQueued || Stillage->bEmptyReturnIssued
            || Return.OrderId != Stillage->OrderId || Return.VehicleModelId != Stillage->VehicleModelId
            || Return.PanelTypeId != Stillage->PanelTypeId) return false;
    }

    if (State.ActiveReservation.bValid)
    {
        const FLBBodyWeldInputReservation& Reservation = State.ActiveReservation;
        TArray<FName> ModelFamilies;
        FName ModelBaseKitTypeId;
        if (Reservation.ReservationId.IsNone() || Reservation.OrderId.IsNone()
            || !LBVehicleModelCatalog::GetBodyWeldContract(
                Reservation.VehicleModelId, ModelFamilies, ModelBaseKitTypeId)
            || Reservation.Panels.Num() != ModelFamilies.Num()
            || !KitIds.Contains(Reservation.BaseKitId)) return false;
        ReservationIds.Add(Reservation.ReservationId);
        TSet<FName> Families;
        TSet<FName> ReservationPanelIds;
        for (const FLBBodyWeldPanelLineage& Reserved : Reservation.Panels)
        {
            if (!LBBodyWeldPrivate::AddUniqueId(ReservationPanelIds, Reserved.PanelId)
                || !LBBodyWeldPrivate::AddUniqueId(Families, Reserved.PanelTypeId)
                || !GlobalPanelIds.Contains(Reserved.PanelId) || !StillageIds.Contains(Reserved.StillageId)
                || !ModelFamilies.Contains(Reserved.PanelTypeId)) return false;
            const FLBBodyWeldStillageInventory* Stillage = State.Stillages.FindByPredicate(
                [&Reserved](const FLBBodyWeldStillageInventory& Candidate)
                { return Candidate.StillageId == Reserved.StillageId; });
            const FLBBodyWeldPanelUnit* Panel = Stillage ? Stillage->PanelUnits.FindByPredicate(
                [&Reserved](const FLBBodyWeldPanelUnit& Candidate)
                { return Candidate.PanelId == Reserved.PanelId; }) : nullptr;
            if (!Panel || Panel->PanelTypeId != Reserved.PanelTypeId
                || Panel->bConsumed != Reservation.bConsumptionCommitted
                || (!Reservation.bConsumptionCommitted && !Panel->bReserved)) return false;
        }
        const FLBBodyWeldBaseKitUnit* Kit = State.BaseKits.FindByPredicate(
            [&Reservation](const FLBBodyWeldBaseKitUnit& Candidate)
            { return Candidate.KitId == Reservation.BaseKitId; });
        if (Families.Num() != ModelFamilies.Num() || !Kit
            || Kit->VehicleModelId != Reservation.VehicleModelId || Kit->KitTypeId != ModelBaseKitTypeId
            || Kit->bConsumed != Reservation.bConsumptionCommitted
            || (!Reservation.bConsumptionCommitted && !Kit->bReserved)) return false;
    }
    else if (State.Phase != ELBBodyWeldPhase::AwaitingRecipe
        && State.Phase != ELBBodyWeldPhase::OutputReady
        && State.Phase != ELBBodyWeldPhase::TransferringToED) return false;

    TSet<FName> BodyPanelIds;
    TSet<FName> BodyKitIds;
    const auto ValidateBody = [&](const FLBBodyInWhiteRecord& Body, const bool bMayBeAccepted)
    {
        if (!IsBodyRecordContractValid(Body) || BodyIds.Contains(Body.BodyId)
            || BodyKitIds.Contains(Body.BaseKitId)
            || (!bMayBeAccepted && Body.bEDAccepted)) return false;
        for (const FLBBodyWeldPanelLineage& Panel : Body.Panels)
        {
            if (BodyPanelIds.Contains(Panel.PanelId)) return false;
            BodyPanelIds.Add(Panel.PanelId);
        }
        BodyKitIds.Add(Body.BaseKitId);
        BodyIds.Add(Body.BodyId);
        if (ReservationIds.Contains(Body.ReservationId)) return false;
        ReservationIds.Add(Body.ReservationId);
        return true;
    };
    if (State.bHasOutputBody && (!ValidateBody(State.OutputBody, false)
        || State.OutputBody.QualityState != ELBBodyWeldQualityState::Good)) return false;
    if (!State.bHasOutputBody && !State.OutputBody.BodyId.IsNone()) return false;
    if (State.bHasReworkBody && (!ValidateBody(State.ReworkBody, false)
        || State.ReworkBody.QualityState == ELBBodyWeldQualityState::Good)) return false;
    if (!State.bHasReworkBody && !State.ReworkBody.BodyId.IsNone()) return false;
    for (const FLBBodyInWhiteRecord& Body : State.CompletedBodies)
        if (!ValidateBody(Body, true) || !Body.bEDAccepted
            || Body.QualityState != ELBBodyWeldQualityState::Good) return false;

    // Every body lineage must resolve to the exact consumed actor-local inventory. This
    // prevents a restore payload from smuggling or reusing an identity already in a BIW.
    for (const FName PanelId : BodyPanelIds)
    {
        const FLBBodyWeldStillageInventory* Owner = State.Stillages.FindByPredicate(
            [PanelId](const FLBBodyWeldStillageInventory& Stillage)
            { return Stillage.PanelUnits.ContainsByPredicate(
                [PanelId](const FLBBodyWeldPanelUnit& Panel) { return Panel.PanelId == PanelId; }); });
        const FLBBodyWeldPanelUnit* Panel = Owner ? Owner->PanelUnits.FindByPredicate(
            [PanelId](const FLBBodyWeldPanelUnit& Candidate) { return Candidate.PanelId == PanelId; }) : nullptr;
        if (!Panel || !Panel->bConsumed) return false;
    }
    for (const FName KitId : BodyKitIds)
    {
        const FLBBodyWeldBaseKitUnit* Kit = State.BaseKits.FindByPredicate(
            [KitId](const FLBBodyWeldBaseKitUnit& Candidate) { return Candidate.KitId == KitId; });
        if (!Kit || !Kit->bConsumed) return false;
    }

    if (State.Phase == ELBBodyWeldPhase::OutputReady && !State.bHasOutputBody) return false;
    if (State.bHasOutputBody && State.Phase != ELBBodyWeldPhase::OutputReady
        && State.Phase != ELBBodyWeldPhase::TransferringToED) return false;
    return true;
}

bool ALBBodyWeldLineActor::RestoreSaveState(const FLBBodyWeldLineSaveState& State)
{
    // Full preflight happens before the first mutation, making failed restore atomic.
    if (!IsSaveStateContractValid(State)
        || (!LineId.IsNone() && LineId != State.LineId)
        || !Configure(State.LineId)) return false;
    SetActorTransform(State.WorldTransform);
    bEnabled = State.bEnabled;
    bPaused = State.bPaused;
    bServiceHeld = State.bServiceHeld;
    bEDAvailable = State.bEDAvailable;
    bFaulted = State.bFaulted;
    FaultReason = State.FaultReason;
    AssignedOrderId = State.AssignedOrderId;
    OperatingState = State.OperatingState;
    OperatingReason = State.OperatingReason;
    Phase = State.Phase;
    PhaseProgress01 = State.PhaseProgress01;
    Stillages = State.Stillages;
    BaseKits = State.BaseKits;
    ActiveReservation = State.ActiveReservation;
    bHasOutputBody = State.bHasOutputBody;
    OutputBody = State.OutputBody;
    bHasReworkBody = State.bHasReworkBody;
    ReworkBody = State.ReworkBody;
    CompletedBodies = State.CompletedBodies;
    PendingEmptyReturns = State.PendingEmptyReturns;
    QualityConditions = State.QualityConditions;
    ActiveCycleQualityConditions = State.ActiveCycleQualityConditions;
    ActiveCycleEvidence = State.ActiveCycleEvidence;
    RobotBaseWear01 = State.RobotBaseWear01;
    SpotHeadWear01 = State.SpotHeadWear01;
    MIGHeadWear01 = State.MIGHeadWear01;
    NextReservationSerial = State.NextReservationSerial;
    NextBodySerial = State.NextBodySerial;
    NextEventSequence = State.NextEventSequence;
    RefreshPresentation();
    return true;
}
