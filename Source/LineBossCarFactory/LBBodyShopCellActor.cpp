#include "LBBodyShopCellActor.h"

#include "Components/BoxComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "LBBodyShopPortComponent.h"
#include "LBBodyShopPresentationPalette.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/UObjectGlobals.h"

namespace LBBodyShopCellPrivate
{
    const TCHAR* CubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR* CylinderPath = TEXT("/Engine/BasicShapes/Cylinder.Cylinder");
    const TCHAR* BaseMaterialPath =
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
    const TCHAR* FramingFixturePath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyWeldLine/Runtime_v001/Fixture/SM_LB_BodyWeld_FramingFixture_v001.SM_LB_BodyWeld_FramingFixture_v001");
    const TCHAR* VisionGateRuntimePath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001.SM_LB_BodyShop_VisionGate_v001");
    const TCHAR* RobotBasePath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_Base_v001.SM_LB_BodyShopRobotNative_Base_v001");
    const TCHAR* SpotToolPath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001.SM_LB_BodyShopToolNative_OpenCGun_v001");
    const TCHAR* PanelPickToolPath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001.SM_LB_BodyShopTool_PanelPick8Cup_v001");

    // The frozen Cairnwell 2040 pilot skid is 560 x 212 cm with longitudinal
    // runners centred at Y +/-90 cm. Dressing follows that authored carrier,
    // rather than using the generic 180 cm full-width roller link.
    constexpr float PilotSkidOverallWidthCm = 212.0f;
    constexpr float PilotSkidRunnerGaugeCm = 180.0f;
    constexpr float PoweredTrackWidthCm = 28.0f;
    constexpr float RollerRadiusCm = 6.0f;
    constexpr float RollerSpacingCm = 50.0f;
    constexpr float SupportSpacingCm = 200.0f;
    constexpr float CellFloorNeutralLaneHalfWidthCm = 130.0f;
    constexpr float CellFloorPaintEndInsetCm = 14.0f;
    constexpr float CellFloorPaintSideInsetCm = 13.0f;
    constexpr float CellFloorSafetyLineWidthCm = 10.0f;
    constexpr float CellFloorWorkingZoneThicknessCm = 0.5f;
    constexpr float CellFloorSafetyLineThicknessCm = 0.8f;

    const FLinearColor CellFloorWorkingZoneColour = FLinearColor::FromSRGBColor(
        FColor(0x1F, 0x4B, 0x44, 0xFF));
    const FLinearColor CellFloorSafetyMarkingColour = FLinearColor::FromSRGBColor(
        FColor(0xF2, 0xC3, 0x00, 0xFF));

    void ConfigureHISM(UHierarchicalInstancedStaticMeshComponent* Component)
    {
        if (!Component) return;
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCollisionResponseToAllChannels(ECR_Ignore);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetCastShadow(true);
    }

    void ApplyColour(UPrimitiveComponent* Component, UMaterialInterface* Material,
        const FLinearColor& Colour)
    {
        if (!Component || !Material) return;
        UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(Material, Component);
        if (!MID) return;
        MID->SetVectorParameterValue(TEXT("Color"), Colour);
        MID->SetVectorParameterValue(TEXT("BaseColor"), Colour);
        MID->SetScalarParameterValue(TEXT("Roughness"), 0.62f);
        Component->SetMaterial(0, MID);
    }

    bool IsVisualOnlyFloorBatch(const UHierarchicalInstancedStaticMeshComponent* Component)
    {
        if (!Component || Component->GetCollisionEnabled() != ECollisionEnabled::NoCollision
            || Component->GetGenerateOverlapEvents() || Component->CanEverAffectNavigation()
            || Component->CastShadow || Component->bReceivesDecals)
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

    bool InstanceMatches(const UHierarchicalInstancedStaticMeshComponent* Component,
        const int32 Index, const FVector& Centre, const FVector& Dimensions)
    {
        FTransform Actual;
        if (!Component || !Component->GetInstanceTransform(Index, Actual, false)) return false;
        return Actual.GetLocation().Equals(Centre, 0.01f)
            && Actual.GetScale3D().Equals(Dimensions / 100.0f, 0.0001f)
            && Actual.GetRotation().Equals(FQuat::Identity, 0.0001f);
    }
}

ALBBodyShopCellActor::ALBBodyShopCellActor()
{
    PrimaryActorTick.bCanEverTick = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    Footprint = CreateDefaultSubobject<UBoxComponent>(TEXT("Footprint"));
    Footprint->SetupAttachment(SceneRoot);
    Footprint->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Footprint->SetCollisionObjectType(ECC_WorldDynamic);
    Footprint->SetCollisionResponseToAllChannels(ECR_Ignore);
    Footprint->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Footprint->SetGenerateOverlapEvents(false);
    Footprint->SetCanEverAffectNavigation(false);
    Footprint->SetHiddenInGame(true);

    MaintenanceEnvelope = CreateDefaultSubobject<UBoxComponent>(TEXT("MaintenanceEnvelope"));
    MaintenanceEnvelope->SetupAttachment(SceneRoot);
    MaintenanceEnvelope->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    MaintenanceEnvelope->SetCollisionResponseToAllChannels(ECR_Ignore);
    MaintenanceEnvelope->SetGenerateOverlapEvents(false);
    MaintenanceEnvelope->SetCanEverAffectNavigation(false);
    MaintenanceEnvelope->SetHiddenInGame(true);

    MainPresentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("MainPresentation"));
    MainPresentation->SetupAttachment(SceneRoot);
    WorkpiecePresentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WorkpiecePresentation"));
    WorkpiecePresentation->SetupAttachment(SceneRoot);
    CarrierPresentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CarrierPresentation"));
    CarrierPresentation->SetupAttachment(SceneRoot);
    for (UStaticMeshComponent* Component : {MainPresentation.Get(), WorkpiecePresentation.Get(),
        CarrierPresentation.Get()})
    {
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
    }

    AutoFence = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("AutoFence"));
    AutoFence->SetupAttachment(SceneRoot);
    AutoServices = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("AutoServices"));
    AutoServices->SetupAttachment(SceneRoot);
    SkidConveyorStructure = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("SkidConveyorStructure"));
    SkidConveyorStructure->SetupAttachment(SceneRoot);
    SkidConveyorRollers = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("SkidConveyorRollers"));
    SkidConveyorRollers->SetupAttachment(SceneRoot);
    SkidConveyorSafety = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("SkidConveyorSafety"));
    SkidConveyorSafety->SetupAttachment(SceneRoot);
    CellFloorWorkingZone = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("CellFloorWorkingZone"));
    CellFloorWorkingZone->SetupAttachment(SceneRoot);
    CellFloorSafetyMarking = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("CellFloorSafetyMarking"));
    CellFloorSafetyMarking->SetupAttachment(SceneRoot);
    ReachOverlay = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("ReachOverlay"));
    ReachOverlay->SetupAttachment(SceneRoot);
    SweepOverlay = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(TEXT("SweepOverlay"));
    SweepOverlay->SetupAttachment(SceneRoot);
    LBBodyShopCellPrivate::ConfigureHISM(AutoFence);
    LBBodyShopCellPrivate::ConfigureHISM(AutoServices);
    LBBodyShopCellPrivate::ConfigureHISM(SkidConveyorStructure);
    LBBodyShopCellPrivate::ConfigureHISM(SkidConveyorRollers);
    LBBodyShopCellPrivate::ConfigureHISM(SkidConveyorSafety);
    LBBodyShopCellPrivate::ConfigureHISM(CellFloorWorkingZone);
    LBBodyShopCellPrivate::ConfigureHISM(CellFloorSafetyMarking);
    CellFloorWorkingZone->SetCastShadow(false);
    CellFloorSafetyMarking->SetCastShadow(false);
    CellFloorWorkingZone->SetReceivesDecals(false);
    CellFloorSafetyMarking->SetReceivesDecals(false);
    LBBodyShopCellPrivate::ConfigureHISM(ReachOverlay);
    LBBodyShopCellPrivate::ConfigureHISM(SweepOverlay);

    CubeMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopCellPrivate::CubePath));
    CylinderMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopCellPrivate::CylinderPath));
    BaseMaterial = TSoftObjectPtr<UMaterialInterface>(
        FSoftObjectPath(LBBodyShopCellPrivate::BaseMaterialPath));
    FramingFixtureMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopCellPrivate::FramingFixturePath));
    VisionGateRuntimeMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopCellPrivate::VisionGateRuntimePath));
    RobotBaseMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopCellPrivate::RobotBasePath));
    SpotToolMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopCellPrivate::SpotToolPath));
    PanelPickToolMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopCellPrivate::PanelPickToolPath));

    Tags.AddUnique(TEXT("LB.BodyShop.Experimental.Cell.v001"));
}

void ALBBodyShopCellActor::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    if (!DefinitionId.IsNone()) RebuildConfiguredPresentation();
}

bool ALBBodyShopCellActor::ConfigureCell(const FName InCellId, const FName InDefinitionId,
    FString& OutReason)
{
    OutReason.Reset();
    FLBBodyShopCellDefinition Candidate;
    if (InCellId.IsNone()
        || !FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(InDefinitionId, Candidate)
        || !FLBBodyShopDefinitionRegistry::ValidateDefinition(Candidate, OutReason))
    {
        if (OutReason.IsEmpty()) OutReason = TEXT("BODY SHOP CELL CONFIGURATION IS INVALID");
        return false;
    }

    CellId = InCellId;
    DefinitionId = InDefinitionId;
    Definition = Candidate;
    CellState = ELBBodyShopCellState::Constructed;
    bCommissioned = false;
    RobotAssignments.Reset();
    QueuedWIPIds.Reset();
    ActiveWIPId = NAME_None;
    ProcessProgress01 = 0.0f;
    Tags.AddUnique(CellId);
    Tags.AddUnique(DefinitionId);
    RebuildConfiguredPresentation();
    if (!bPresentationMaterialContractValid)
    {
        OutReason = PresentationMaterialContractFailureReason;
        return false;
    }
    return true;
}

bool ALBBodyShopCellActor::ApplyRobotAssignments(
    const TArray<FLBBodyShopRobotAssignment>& InAssignments, FString& OutReason)
{
    if (!FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(
        Definition, InAssignments, OutReason)) return false;
    RobotAssignments = InAssignments;
    bCommissioned = false;
    CellState = ELBBodyShopCellState::Constructed;
    RebuildConfiguredPresentation();
    if (!bPresentationMaterialContractValid)
    {
        OutReason = PresentationMaterialContractFailureReason;
        return false;
    }
    return true;
}

bool ALBBodyShopCellActor::SetCommissioned(const bool bInCommissioned, FString& OutReason)
{
    OutReason.Reset();
    if (bInCommissioned)
    {
        if (!bPresentationMaterialContractValid)
        {
            OutReason = PresentationMaterialContractFailureReason;
            return false;
        }
        if (RobotAssignments.Num() != Definition.RobotSlots.Num()
            || !FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(
                Definition, RobotAssignments, OutReason))
        {
            if (OutReason.IsEmpty())
                OutReason = TEXT("BODY SHOP CELL REQUIRES EVERY AUTHORED ROBOT SLOT");
            return false;
        }
        if (RobotAssignments.ContainsByPredicate([](const FLBBodyShopRobotAssignment& Assignment)
            { return !Assignment.bEnabled || Assignment.Condition01 <= 0.0f; }))
        {
            OutReason = TEXT("BODY SHOP CELL HAS AN UNAVAILABLE ROBOT ASSIGNMENT");
            return false;
        }
    }
    bCommissioned = bInCommissioned;
    CellState = bCommissioned ? ELBBodyShopCellState::Idle
        : ELBBodyShopCellState::Constructed;
    return true;
}

void ALBBodyShopCellActor::SetRobotConfigurationOverlayVisible(const bool bVisible)
{
    bOverlayVisible = bVisible;
    ReachOverlay->SetVisibility(bOverlayVisible, true);
    SweepOverlay->SetVisibility(bOverlayVisible, true);
}

int32 ALBBodyShopCellActor::GetAutoAssembledFenceSegmentCount() const
{
    return AutoFence ? AutoFence->GetInstanceCount() : 0;
}

int32 ALBBodyShopCellActor::GetAutoAssembledServiceCount() const
{
    return AutoServices ? AutoServices->GetInstanceCount() : 0;
}

FString ALBBodyShopCellActor::GetMainPresentationAssetPath() const
{
    const UStaticMesh* Mesh = MainPresentation ? MainPresentation->GetStaticMesh() : nullptr;
    return Mesh ? Mesh->GetPathName() : FString();
}

bool ALBBodyShopCellActor::UsesOpenRailSafetyPresentation() const
{
    if (!AutoFence) return true;
    for (int32 Index = 0; Index < AutoFence->GetInstanceCount(); ++Index)
    {
        FTransform InstanceTransform;
        if (!AutoFence->GetInstanceTransform(Index, InstanceTransform, false)) return false;
        const FVector Dimensions = InstanceTransform.GetScale3D().GetAbs() * 100.0f;
        if (Dimensions.X > 100.0f && Dimensions.Y <= 20.0f && Dimensions.Z > 100.0f)
            return false;
    }
    return true;
}

bool ALBBodyShopCellActor::HasStaticCarrierOrWorkpiecePresentation() const
{
    const bool bHasCarrier = CarrierPresentation && CarrierPresentation->IsVisible()
        && CarrierPresentation->GetStaticMesh();
    const bool bHasWorkpiece = WorkpiecePresentation && WorkpiecePresentation->IsVisible()
        && WorkpiecePresentation->GetStaticMesh();
    return bHasCarrier || bHasWorkpiece;
}

bool ALBBodyShopCellActor::HasStaticStillagePresentation() const
{
    for (const UStaticMeshComponent* Component : {MainPresentation.Get(),
        WorkpiecePresentation.Get(), CarrierPresentation.Get()})
    {
        const UStaticMesh* Mesh = Component && Component->IsVisible()
            ? Component->GetStaticMesh() : nullptr;
        if (Mesh && IsRuntimeStillagePresentationMeshName(Mesh->GetFName())) return true;
    }
    return false;
}

bool ALBBodyShopCellActor::IsRuntimeStillagePresentationMeshName(const FName MeshName)
{
    return MeshName == TEXT("SM_LB_PanelStillage_Runtime_v001")
        || MeshName == TEXT("SM_LB_BodyShopSupport_PanelStillage_Full_v002");
}

bool ALBBodyShopCellActor::HasAutomotiveSkidConveyorPresentation() const
{
    return SkidConveyorPresentationSpanCm > 0.0f
        && SkidConveyorTrackGaugeCm > 0.0f
        && GetSkidConveyorStructureInstanceCount() > 0
        && GetSkidConveyorRollerInstanceCount() > 0
        && GetSkidConveyorSafetyInstanceCount() > 0;
}

int32 ALBBodyShopCellActor::GetSkidConveyorStructureInstanceCount() const
{
    return SkidConveyorStructure ? SkidConveyorStructure->GetInstanceCount() : 0;
}

int32 ALBBodyShopCellActor::GetSkidConveyorRollerInstanceCount() const
{
    return SkidConveyorRollers ? SkidConveyorRollers->GetInstanceCount() : 0;
}

int32 ALBBodyShopCellActor::GetSkidConveyorSafetyInstanceCount() const
{
    return SkidConveyorSafety ? SkidConveyorSafety->GetInstanceCount() : 0;
}

bool ALBBodyShopCellActor::HasPaintedUnderbodyWorkZone() const
{
    if (Definition.CellType != ELBBodyShopCellType::UnderbodyFixture
        || !LBBodyShopCellPrivate::IsVisualOnlyFloorBatch(CellFloorWorkingZone)
        || !LBBodyShopCellPrivate::IsVisualOnlyFloorBatch(CellFloorSafetyMarking)
        || !FMath::IsNearlyEqual(CellFloorNeutralConveyorLaneWidthCm, 260.0f)
        || GetCellFloorWorkingZoneInstanceCount() != 2
        || GetCellFloorSafetyMarkingInstanceCount() != 6)
    {
        return false;
    }

    const FVector Half = Definition.FootprintCm * 0.5f;
    const float PaintHalfX = Half.X - LBBodyShopCellPrivate::CellFloorPaintEndInsetCm;
    const float PaintOuterY = Half.Y - LBBodyShopCellPrivate::CellFloorPaintSideInsetCm;
    const float NeutralHalfY = LBBodyShopCellPrivate::CellFloorNeutralLaneHalfWidthCm;
    const float WorkingZoneWidthY = PaintOuterY - NeutralHalfY;
    const float WorkingZoneCentreY = (PaintOuterY + NeutralHalfY) * 0.5f;
    const float WorkingZoneZ = LBBodyShopCellPrivate::CellFloorWorkingZoneThicknessCm * 0.5f;
    for (int32 Index = 0; Index < 2; ++Index)
    {
        const float Side = Index == 0 ? -1.0f : 1.0f;
        if (!LBBodyShopCellPrivate::InstanceMatches(CellFloorWorkingZone, Index,
            FVector(0.0f, Side * WorkingZoneCentreY, WorkingZoneZ),
            FVector(PaintHalfX * 2.0f, WorkingZoneWidthY,
                LBBodyShopCellPrivate::CellFloorWorkingZoneThicknessCm)))
        {
            return false;
        }
    }

    const float SafetyHalfWidth = LBBodyShopCellPrivate::CellFloorSafetyLineWidthCm * 0.5f;
    const float SafetyLineZ = LBBodyShopCellPrivate::CellFloorSafetyLineThicknessCm * 0.5f;
    const float LongLineY = Half.Y - SafetyHalfWidth - 3.0f;
    const float EndLineOuterY = LongLineY + SafetyHalfWidth;
    const float EndLineWidthY = EndLineOuterY - NeutralHalfY;
    const float EndLineCentreY = (EndLineOuterY + NeutralHalfY) * 0.5f;
    int32 SafetyIndex = 0;
    for (const float Side : {-1.0f, 1.0f})
    {
        if (!LBBodyShopCellPrivate::InstanceMatches(CellFloorSafetyMarking, SafetyIndex++,
            FVector(0.0f, Side * LongLineY, SafetyLineZ),
            FVector(PaintHalfX * 2.0f, LBBodyShopCellPrivate::CellFloorSafetyLineWidthCm,
                LBBodyShopCellPrivate::CellFloorSafetyLineThicknessCm)))
        {
            return false;
        }
        for (const float End : {-1.0f, 1.0f})
        {
            if (!LBBodyShopCellPrivate::InstanceMatches(CellFloorSafetyMarking, SafetyIndex++,
                FVector(End * (Half.X - SafetyHalfWidth - 4.0f),
                    Side * EndLineCentreY, SafetyLineZ),
                FVector(LBBodyShopCellPrivate::CellFloorSafetyLineWidthCm,
                    EndLineWidthY, LBBodyShopCellPrivate::CellFloorSafetyLineThicknessCm)))
            {
                return false;
            }
        }
    }
    return true;
}

int32 ALBBodyShopCellActor::GetCellFloorWorkingZoneInstanceCount() const
{
    return CellFloorWorkingZone ? CellFloorWorkingZone->GetInstanceCount() : 0;
}

int32 ALBBodyShopCellActor::GetCellFloorSafetyMarkingInstanceCount() const
{
    return CellFloorSafetyMarking ? CellFloorSafetyMarking->GetInstanceCount() : 0;
}

FLinearColor ALBBodyShopCellActor::GetCellFloorWorkingZoneColour() const
{
    return LBBodyShopCellPrivate::CellFloorWorkingZoneColour;
}

FLinearColor ALBBodyShopCellActor::GetCellFloorSafetyMarkingColour() const
{
    return LBBodyShopCellPrivate::CellFloorSafetyMarkingColour;
}

ULBBodyShopPortComponent* ALBBodyShopCellActor::FindPort(const FName PortId) const
{
    const TObjectPtr<ULBBodyShopPortComponent>* Found = Ports.FindByPredicate(
        [PortId](const ULBBodyShopPortComponent* Port)
        {
            return Port && Port->GetPortId() == PortId;
        });
    return Found ? Found->Get() : nullptr;
}

FLBBodyShopPlacedCellSaveState ALBBodyShopCellActor::CaptureSaveState() const
{
    FLBBodyShopPlacedCellSaveState State;
    State.CellId = CellId;
    State.DefinitionId = DefinitionId;
    State.WorldTransform = GetActorTransform();
    State.State = CellState;
    State.bCommissioned = bCommissioned;
    State.RobotAssignments = RobotAssignments;
    State.QueuedWIPIds = QueuedWIPIds;
    State.ActiveWIPId = ActiveWIPId;
    State.ProcessProgress01 = ProcessProgress01;
    return State;
}

bool ALBBodyShopCellActor::ValidateSaveState(const FLBBodyShopPlacedCellSaveState& State,
    FString& OutReason)
{
    FLBBodyShopCellDefinition SavedDefinition;
    const FVector Scale = State.WorldTransform.GetScale3D();
    const FRotator Rotation = State.WorldTransform.Rotator();
    if (State.Version != 1 || State.CellId.IsNone()
        || !FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(
            State.DefinitionId, SavedDefinition)
        || !Scale.Equals(FVector::OneVector, KINDA_SMALL_NUMBER)
        || !FMath::IsNearlyZero(Rotation.Pitch, 0.01f)
        || !FMath::IsNearlyZero(Rotation.Roll, 0.01f)
        || !FMath::IsNearlyZero(FMath::Fmod(FMath::Abs(Rotation.Yaw), 90.0f), 0.01f)
        || !FMath::IsFinite(State.ProcessProgress01)
        || !FMath::IsWithinInclusive(State.ProcessProgress01, 0.0f, 1.0f)
        || !FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(
            SavedDefinition, State.RobotAssignments, OutReason))
    {
        if (OutReason.IsEmpty()) OutReason = TEXT("BODY SHOP CELL SAVE STATE IS INVALID");
        return false;
    }
    if (State.bCommissioned && State.RobotAssignments.Num() != SavedDefinition.RobotSlots.Num())
    {
        OutReason = TEXT("COMMISSIONED BODY SHOP CELL IS MISSING AUTHORED ROBOT ASSIGNMENTS");
        return false;
    }
    return true;
}

bool ALBBodyShopCellActor::RestoreSaveState(const FLBBodyShopPlacedCellSaveState& State,
    FString& OutReason)
{
    if (!ValidateSaveState(State, OutReason)) return false;
    FLBBodyShopCellDefinition Candidate;
    if (!FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(State.DefinitionId, Candidate))
        return false;

    CellId = State.CellId;
    DefinitionId = State.DefinitionId;
    Definition = Candidate;
    RobotAssignments = State.RobotAssignments;
    CellState = State.State;
    bCommissioned = State.bCommissioned;
    QueuedWIPIds = State.QueuedWIPIds;
    ActiveWIPId = State.ActiveWIPId;
    ProcessProgress01 = State.ProcessProgress01;
    SetActorTransform(State.WorldTransform, false, nullptr, ETeleportType::TeleportPhysics);
    Tags.AddUnique(CellId);
    Tags.AddUnique(DefinitionId);
    RebuildConfiguredPresentation();
    if (!bPresentationMaterialContractValid)
    {
        OutReason = PresentationMaterialContractFailureReason;
        return false;
    }
    return true;
}

void ALBBodyShopCellActor::SetRuntimeState(const ELBBodyShopCellState InState,
    const float InProcessProgress01, const TArray<FName>& InQueuedWIPIds,
    const FName InActiveWIPId)
{
    CellState = InState;
    ProcessProgress01 = FMath::Clamp(InProcessProgress01, 0.0f, 1.0f);
    QueuedWIPIds = InQueuedWIPIds;
    ActiveWIPId = InActiveWIPId;
}

void ALBBodyShopCellActor::RebuildConfiguredPresentation()
{
    bPresentationMaterialContractValid = true;
    PresentationMaterialContractFailureReason.Reset();
    UStaticMesh* Cube = CubeMesh.LoadSynchronous();
    UStaticMesh* Cylinder = CylinderMesh.LoadSynchronous();
    UMaterialInterface* Material = BaseMaterial.LoadSynchronous();
    if (!Cube || !Cylinder || !Material)
    {
        bPresentationMaterialContractValid = false;
        PresentationMaterialContractFailureReason =
            TEXT("BODY SHOP PRESENTATION PRIMITIVES OR BASE MATERIAL ARE MISSING");
        return;
    }

    Footprint->SetRelativeLocation(FVector(0.0f, 0.0f, Definition.FootprintCm.Z * 0.5f));
    Footprint->SetBoxExtent(Definition.FootprintCm * 0.5f);
    MaintenanceEnvelope->SetRelativeLocation(
        FVector(0.0f, 0.0f, Definition.MaintenanceEnvelopeCm.Z * 0.5f));
    MaintenanceEnvelope->SetBoxExtent(Definition.MaintenanceEnvelopeCm * 0.5f);

    AutoFence->SetStaticMesh(Cube);
    AutoServices->SetStaticMesh(Cube);
    ReachOverlay->SetStaticMesh(Cylinder);
    SweepOverlay->SetStaticMesh(Cylinder);
    LBBodyShopCellPrivate::ApplyColour(AutoFence, Material,
        FLinearColor(0.96f, 0.68f, 0.04f, 1.0f));
    LBBodyShopCellPrivate::ApplyColour(AutoServices, Material,
        FLinearColor(0.10f, 0.16f, 0.14f, 1.0f));
    LBBodyShopCellPrivate::ApplyColour(ReachOverlay, Material,
        FLinearColor(0.08f, 0.75f, 0.48f, 0.20f));
    LBBodyShopCellPrivate::ApplyColour(SweepOverlay, Material,
        FLinearColor(0.95f, 0.24f, 0.10f, 0.20f));

    MainPresentation->SetStaticMesh(nullptr);
    WorkpiecePresentation->SetStaticMesh(nullptr);
    CarrierPresentation->SetStaticMesh(nullptr);
    MainPresentation->SetVisibility(false, true);
    WorkpiecePresentation->SetVisibility(false, true);
    CarrierPresentation->SetVisibility(false, true);

    switch (Definition.CellType)
    {
    case ELBBodyShopCellType::FullStillageDock:
        // The dock owns only its fixed floor plate. Its live stillage is runtime WIP.
        ConfigurePresentationMesh(MainPresentation, Cube,
            FVector(0.0f, 0.0f, 12.0f), FVector(3.6f, 3.2f, 0.12f),
            FRotator::ZeroRotator, FLinearColor(0.10f, 0.20f, 0.17f, 1.0f), true,
            false, false);
        break;
    case ELBBodyShopCellType::PanelPresentation:
        // The runtime moves the same logical stillage into this fixed presentation table.
        ConfigurePresentationMesh(MainPresentation, Cube,
            FVector(170.0f, 0.0f, 75.0f), FVector(2.4f, 1.8f, 0.18f),
            FRotator::ZeroRotator, FLinearColor(0.10f, 0.34f, 0.25f, 1.0f), false,
            false, false);
        break;
    case ELBBodyShopCellType::UnderbodyFixture:
        // The weld cell is an open section of the continuous skid conveyor. Runtime
        // exclusively owns the live skid/underbody; clamps and robots surround it.
        // Do not reintroduce the former large black tooling-bed presentation.
        break;
    case ELBBodyShopCellType::StraightSkidConveyor:
    case ELBBodyShopCellType::OutputBuffer:
        // These cells are dressed below as open twin-track skid conveyors. Do not
        // reintroduce the opaque cube slab that previously hid their function.
        break;
    case ELBBodyShopCellType::BasicVisionGate:
        ConfigurePresentationMesh(MainPresentation, VisionGateRuntimeMesh.LoadSynchronous(),
            FVector::ZeroVector, FVector::OneVector, FRotator::ZeroRotator,
            FLinearColor::White, false, true, true);
        break;
    default:
        break;
    }

    RebuildSkidConveyorPresentation(Cube, Cylinder);
    RebuildCellFloorPresentation(Cube, Material);
    RebuildPorts();
    RebuildAutoSafetyAndServices();
    RebuildOverlays();
    SetRobotConfigurationOverlayVisible(bOverlayVisible);
}

void ALBBodyShopCellActor::RebuildCellFloorPresentation(UStaticMesh* Cube,
    UMaterialInterface* Material)
{
    for (UHierarchicalInstancedStaticMeshComponent* Component : {
        CellFloorWorkingZone.Get(), CellFloorSafetyMarking.Get()})
    {
        if (!Component) continue;
        Component->ClearInstances();
        Component->EmptyOverrideMaterials();
        Component->SetVisibility(false, true);
    }
    CellFloorNeutralConveyorLaneWidthCm = 0.0f;
    if (Definition.CellType != ELBBodyShopCellType::UnderbodyFixture) return;

    if (!Cube || !Material)
    {
        bPresentationMaterialContractValid = false;
        PresentationMaterialContractFailureReason =
            TEXT("BODY SHOP CELL FLOOR PAINT PRIMITIVE OR MATERIAL IS MISSING");
        return;
    }

    CellFloorWorkingZone->SetStaticMesh(Cube);
    CellFloorSafetyMarking->SetStaticMesh(Cube);
    LBBodyShopCellPrivate::ApplyColour(CellFloorWorkingZone, Material,
        LBBodyShopCellPrivate::CellFloorWorkingZoneColour);
    LBBodyShopCellPrivate::ApplyColour(CellFloorSafetyMarking, Material,
        LBBodyShopCellPrivate::CellFloorSafetyMarkingColour);
    if (!CellFloorWorkingZone->GetMaterial(0) || !CellFloorSafetyMarking->GetMaterial(0))
    {
        bPresentationMaterialContractValid = false;
        PresentationMaterialContractFailureReason =
            TEXT("BODY SHOP CELL FLOOR PAINT MATERIAL INSTANCES COULD NOT BE CREATED");
        return;
    }
    CellFloorWorkingZone->SetVisibility(true, true);
    CellFloorSafetyMarking->SetVisibility(true, true);

    const FVector Half = Definition.FootprintCm * 0.5f;
    const float PaintHalfX = Half.X - LBBodyShopCellPrivate::CellFloorPaintEndInsetCm;
    const float PaintOuterY = Half.Y - LBBodyShopCellPrivate::CellFloorPaintSideInsetCm;
    const float NeutralHalfY = LBBodyShopCellPrivate::CellFloorNeutralLaneHalfWidthCm;
    if (PaintHalfX <= LBBodyShopCellPrivate::CellFloorSafetyLineWidthCm
        || PaintOuterY <= NeutralHalfY)
    {
        bPresentationMaterialContractValid = false;
        PresentationMaterialContractFailureReason =
            TEXT("BODY SHOP CELL FOOTPRINT CANNOT CONTAIN THE AUTHORED FLOOR PAINT PATTERN");
        return;
    }

    CellFloorNeutralConveyorLaneWidthCm = NeutralHalfY * 2.0f;
    const float WorkingZoneWidthY = PaintOuterY - NeutralHalfY;
    const float WorkingZoneCentreY = (PaintOuterY + NeutralHalfY) * 0.5f;
    const float WorkingZoneZ = LBBodyShopCellPrivate::CellFloorWorkingZoneThicknessCm * 0.5f;
    for (const float Side : {-1.0f, 1.0f})
    {
        AddBoxInstance(CellFloorWorkingZone,
            FVector(0.0f, Side * WorkingZoneCentreY, WorkingZoneZ),
            FVector(PaintHalfX * 2.0f, WorkingZoneWidthY,
                LBBodyShopCellPrivate::CellFloorWorkingZoneThicknessCm));
    }

    const float SafetyHalfWidth = LBBodyShopCellPrivate::CellFloorSafetyLineWidthCm * 0.5f;
    const float SafetyLineZ = LBBodyShopCellPrivate::CellFloorSafetyLineThicknessCm * 0.5f;
    const float LongLineY = Half.Y - SafetyHalfWidth - 3.0f;
    const float EndLineOuterY = LongLineY + SafetyHalfWidth;
    const float EndLineWidthY = EndLineOuterY - NeutralHalfY;
    const float EndLineCentreY = (EndLineOuterY + NeutralHalfY) * 0.5f;
    for (const float Side : {-1.0f, 1.0f})
    {
        AddBoxInstance(CellFloorSafetyMarking, FVector(0.0f, Side * LongLineY, SafetyLineZ),
            FVector(PaintHalfX * 2.0f, LBBodyShopCellPrivate::CellFloorSafetyLineWidthCm,
                LBBodyShopCellPrivate::CellFloorSafetyLineThicknessCm));
        for (const float End : {-1.0f, 1.0f})
        {
            AddBoxInstance(CellFloorSafetyMarking,
                FVector(End * (Half.X - SafetyHalfWidth - 4.0f),
                    Side * EndLineCentreY, SafetyLineZ),
                FVector(LBBodyShopCellPrivate::CellFloorSafetyLineWidthCm,
                    EndLineWidthY, LBBodyShopCellPrivate::CellFloorSafetyLineThicknessCm));
        }
    }
}

void ALBBodyShopCellActor::RebuildPorts()
{
    for (ULBBodyShopPortComponent* Port : Ports)
    {
        if (Port) Port->DestroyComponent();
    }
    Ports.Reset();
    for (int32 Index = 0; Index < Definition.Ports.Num(); ++Index)
    {
        ULBBodyShopPortComponent* Port = NewObject<ULBBodyShopPortComponent>(this,
            *FString::Printf(TEXT("BodyShopPort_%02d"), Index));
        if (!Port) continue;
        AddInstanceComponent(Port);
        Port->SetupAttachment(SceneRoot);
        Port->Configure(Definition.Ports[Index]);
        Port->RegisterComponent();
        Ports.Add(Port);
    }
}

void ALBBodyShopCellActor::RebuildSkidConveyorPresentation(UStaticMesh* Cube,
    UStaticMesh* Cylinder)
{
    for (UHierarchicalInstancedStaticMeshComponent* Component : {
        SkidConveyorStructure.Get(), SkidConveyorRollers.Get(), SkidConveyorSafety.Get()})
    {
        if (!Component) continue;
        Component->ClearInstances();
        Component->EmptyOverrideMaterials();
        Component->SetVisibility(false, true);
    }
    SkidConveyorPresentationSpanCm = 0.0f;
    SkidConveyorTrackGaugeCm = 0.0f;

    const bool bConveysPilotSkid = Definition.CellType == ELBBodyShopCellType::UnderbodyFixture
        || Definition.CellType == ELBBodyShopCellType::StraightSkidConveyor
        || Definition.CellType == ELBBodyShopCellType::BasicVisionGate
        || Definition.CellType == ELBBodyShopCellType::OutputBuffer;
    if (!bConveysPilotSkid) return;

    const TCHAR* StructureMaterialPath = LBBodyShopPresentationPalette::GetMaterialPath(
        TEXT("M_LB_BS_StructuralLightGrey"));
    const TCHAR* RollerMaterialPath = LBBodyShopPresentationPalette::GetMaterialPath(
        TEXT("M_LB_BS_BrushedSteel"));
    const TCHAR* SafetyMaterialPath = LBBodyShopPresentationPalette::GetMaterialPath(
        TEXT("M_LB_BS_SafetyYellow"));
    UMaterialInterface* StructureMaterial = StructureMaterialPath
        ? LoadObject<UMaterialInterface>(nullptr, StructureMaterialPath) : nullptr;
    UMaterialInterface* RollerMaterial = RollerMaterialPath
        ? LoadObject<UMaterialInterface>(nullptr, RollerMaterialPath) : nullptr;
    UMaterialInterface* SafetyMaterial = SafetyMaterialPath
        ? LoadObject<UMaterialInterface>(nullptr, SafetyMaterialPath) : nullptr;
    if (!Cube || !Cylinder || !StructureMaterial || !RollerMaterial || !SafetyMaterial)
    {
        bPresentationMaterialContractValid = false;
        PresentationMaterialContractFailureReason =
            TEXT("BODY SHOP SKID CONVEYOR PRIMITIVES OR V002 PALETTE MATERIALS ARE MISSING");
        return;
    }

    SkidConveyorStructure->SetStaticMesh(Cube);
    SkidConveyorRollers->SetStaticMesh(Cylinder);
    SkidConveyorSafety->SetStaticMesh(Cube);
    SkidConveyorStructure->SetMaterial(0, StructureMaterial);
    SkidConveyorRollers->SetMaterial(0, RollerMaterial);
    SkidConveyorSafety->SetMaterial(0, SafetyMaterial);
    SkidConveyorStructure->SetVisibility(true, true);
    SkidConveyorRollers->SetVisibility(true, true);
    SkidConveyorSafety->SetVisibility(true, true);

    // Each canonical footprint stops 100 cm short of its authored port pair.
    // The overlap closes those seams without adding another placeable machine.
    SkidConveyorPresentationSpanCm = Definition.FootprintCm.X + 200.0f;
    SkidConveyorTrackGaugeCm = LBBodyShopCellPrivate::PilotSkidRunnerGaugeCm;
    const float HalfSpan = SkidConveyorPresentationSpanCm * 0.5f;
    const float HalfGauge = SkidConveyorTrackGaugeCm * 0.5f;

    // Two low longitudinal beds carry the skid's matching +/-90 cm runners.
    for (const float TrackSide : {-1.0f, 1.0f})
    {
        AddBoxInstance(SkidConveyorStructure, FVector(0.0f, TrackSide * HalfGauge, 10.0f),
            FVector(SkidConveyorPresentationSpanCm,
                LBBodyShopCellPrivate::PoweredTrackWidthCm + 4.0f, 18.0f));
    }

    // Paired short powered rollers read correctly around the 212 cm carrier while
    // keeping the centre of the conveyor open for datum tooling and inspection.
    const int32 RollerIntervals = FMath::Max(2, FMath::FloorToInt(
        SkidConveyorPresentationSpanCm / LBBodyShopCellPrivate::RollerSpacingCm));
    for (int32 RollerIndex = 0; RollerIndex <= RollerIntervals; ++RollerIndex)
    {
        const float Alpha = static_cast<float>(RollerIndex)
            / static_cast<float>(RollerIntervals);
        const float X = FMath::Lerp(-HalfSpan, HalfSpan, Alpha);
        for (const float TrackSide : {-1.0f, 1.0f})
        {
            SkidConveyorRollers->AddInstance(FTransform(FRotator(0.0f, 0.0f, 90.0f),
                FVector(X, TrackSide * HalfGauge, 22.0f),
                FVector(LBBodyShopCellPrivate::RollerRadiusCm / 50.0f,
                    LBBodyShopCellPrivate::RollerRadiusCm / 50.0f,
                    LBBodyShopCellPrivate::PoweredTrackWidthCm / 100.0f)));
        }
    }

    const int32 SupportIntervals = FMath::Max(2, FMath::FloorToInt(
        SkidConveyorPresentationSpanCm / LBBodyShopCellPrivate::SupportSpacingCm));
    for (int32 SupportIndex = 0; SupportIndex <= SupportIntervals; ++SupportIndex)
    {
        const float Alpha = static_cast<float>(SupportIndex)
            / static_cast<float>(SupportIntervals);
        const float X = FMath::Lerp(-HalfSpan, HalfSpan, Alpha);
        AddBoxInstance(SkidConveyorStructure, FVector(X, 0.0f, 7.0f),
            FVector(16.0f, LBBodyShopCellPrivate::PilotSkidOverallWidthCm + 12.0f, 12.0f));
        for (const float TrackSide : {-1.0f, 1.0f})
        {
            AddBoxInstance(SkidConveyorStructure,
                FVector(X, TrackSide * (HalfGauge + 8.0f), 5.0f),
                FVector(14.0f, 14.0f, 10.0f));
        }
    }

    const float GuideY = LBBodyShopCellPrivate::PilotSkidOverallWidthCm * 0.5f + 10.0f;
    for (const float TrackSide : {-1.0f, 1.0f})
    {
        AddBoxInstance(SkidConveyorSafety, FVector(0.0f, TrackSide * GuideY, 22.0f),
            FVector(SkidConveyorPresentationSpanCm, 6.0f, 18.0f));
    }

    if (Definition.CellType == ELBBodyShopCellType::OutputBuffer)
    {
        const float StopX = HalfSpan - 12.0f;
        AddBoxInstance(SkidConveyorSafety, FVector(StopX, 0.0f, 34.0f),
            FVector(16.0f, LBBodyShopCellPrivate::PilotSkidOverallWidthCm + 28.0f, 12.0f));
        for (const float TrackSide : {-1.0f, 1.0f})
        {
            AddBoxInstance(SkidConveyorSafety,
                FVector(StopX, TrackSide * GuideY, 18.0f), FVector(16.0f, 12.0f, 36.0f));
        }
    }
}

void ALBBodyShopCellActor::RebuildAutoSafetyAndServices()
{
    AutoFence->ClearInstances();
    AutoServices->ClearInstances();
    if (!Definition.bAutoAssembleSafetyAndServices || Definition.RobotSlots.IsEmpty()) return;

    const FVector Half = Definition.FootprintCm * 0.5f;
    const float FenceHeight = 210.0f;
    const float Post = 8.0f;
    const int32 PostIntervals = FMath::Max(1,
        FMath::CeilToInt(Definition.FootprintCm.X / 200.0f));
    for (int32 PostIndex = 0; PostIndex <= PostIntervals; ++PostIndex)
    {
        const float Alpha = static_cast<float>(PostIndex) / static_cast<float>(PostIntervals);
        const float X = FMath::Lerp(-Half.X, Half.X, Alpha);
        AddBoxInstance(AutoFence, FVector(X, -Half.Y, FenceHeight * 0.5f),
            FVector(Post, Post, FenceHeight));
        AddBoxInstance(AutoFence, FVector(X, Half.Y, FenceHeight * 0.5f),
            FVector(Post, Post, FenceHeight));
    }
    for (const float RailHeight : {35.0f, 110.0f, 185.0f})
    {
        AddBoxInstance(AutoFence, FVector(0.0f, -Half.Y, RailHeight),
            FVector(Definition.FootprintCm.X, 6.0f, 6.0f));
        AddBoxInstance(AutoFence, FVector(0.0f, Half.Y, RailHeight),
            FVector(Definition.FootprintCm.X, 6.0f, 6.0f));
    }

    int32 ServiceIndex = 0;
    for (const FLBBodyShopRobotAssignment& Assignment : RobotAssignments)
    {
        AddBoxInstance(AutoServices,
            FVector(-Half.X + 70.0f + ServiceIndex * 75.0f, Half.Y - 35.0f, 75.0f),
            FVector(55.0f, 45.0f, 150.0f));
        ++ServiceIndex;
    }
    if (RobotAssignments.ContainsByPredicate([](const FLBBodyShopRobotAssignment& Assignment)
        { return Assignment.Role == ELBBodyShopRobotRole::SpotWelding; }))
    {
        AddBoxInstance(AutoServices, FVector(Half.X - 80.0f, Half.Y - 40.0f, 55.0f),
            FVector(120.0f, 50.0f, 110.0f));
        AddBoxInstance(AutoServices, FVector(Half.X - 80.0f, -Half.Y + 40.0f, 90.0f),
            FVector(100.0f, 60.0f, 180.0f));
    }
}

void ALBBodyShopCellActor::RebuildOverlays()
{
    ReachOverlay->ClearInstances();
    SweepOverlay->ClearInstances();
    for (const FLBBodyShopRobotSlotDefinition& Slot : Definition.RobotSlots)
    {
        const FVector Centre = Slot.LocalMountTransform.GetLocation();
        const FVector ReachScale(Slot.ReachRadiusCm / 50.0f,
            Slot.ReachRadiusCm / 50.0f, 0.04f);
        ReachOverlay->AddInstance(FTransform(FRotator::ZeroRotator,
            Centre + FVector(0.0f, 0.0f, 2.0f), ReachScale));
        const FVector SweepScale(Slot.SweepRadiusCm / 50.0f,
            Slot.SweepRadiusCm / 50.0f, 0.025f);
        SweepOverlay->AddInstance(FTransform(FRotator::ZeroRotator,
            Centre + FVector(0.0f, 0.0f, 3.0f), SweepScale));
    }
}

void ALBBodyShopCellActor::ConfigurePresentationMesh(UStaticMeshComponent* Component,
    UStaticMesh* Mesh, const FVector& RelativeLocation, const FVector& Scale,
    const FRotator& Rotation, const FLinearColor& Colour, const bool bCollision,
    const bool bPreserveSourceMaterials, const bool bRequireSemanticPalette)
{
    if (!Component || !Mesh)
    {
        bPresentationMaterialContractValid = false;
        PresentationMaterialContractFailureReason =
            TEXT("BODY SHOP REQUIRED PRESENTATION MESH IS MISSING");
        return;
    }
    Component->EmptyOverrideMaterials();
    Component->SetStaticMesh(Mesh);
    Component->SetRelativeLocation(RelativeLocation);
    Component->SetRelativeRotation(Rotation);
    Component->SetRelativeScale3D(Scale);
    Component->SetVisibility(true, true);
    Component->SetCollisionEnabled(bCollision
        ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(bCollision ? ECR_Block : ECR_Ignore);
    Component->SetCanEverAffectNavigation(bCollision);
    if (bRequireSemanticPalette)
    {
        const int32 ExpectedCount = Mesh->GetStaticMaterials().Num();
        const int32 AppliedCount = LBBodyShopPresentationPalette::ApplyToComponent(Component);
        if (ExpectedCount <= 0 || AppliedCount != ExpectedCount)
        {
            Component->EmptyOverrideMaterials();
            Component->SetVisibility(false, true);
            bPresentationMaterialContractValid = false;
            PresentationMaterialContractFailureReason = FString::Printf(
                TEXT("BODY SHOP PRESENTATION MESH %s HAS %d/%d VALID SEMANTIC MATERIAL SLOTS"),
                *Mesh->GetPathName(), AppliedCount, ExpectedCount);
        }
    }
    else if (!bPreserveSourceMaterials)
        LBBodyShopCellPrivate::ApplyColour(Component, BaseMaterial.Get(), Colour);
}

void ALBBodyShopCellActor::AddBoxInstance(UHierarchicalInstancedStaticMeshComponent* Component,
    const FVector& Centre, const FVector& Dimensions, const FRotator& Rotation)
{
    if (!Component) return;
    Component->AddInstance(FTransform(Rotation, Centre, Dimensions / 100.0f));
}
