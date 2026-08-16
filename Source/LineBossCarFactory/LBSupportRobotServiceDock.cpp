#include "LBSupportRobotServiceDock.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "LBSupportRobot.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
    constexpr TCHAR MRStaticPath[] = TEXT("/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026/MR01/SM_LB_MR01_ServiceDock_Static_v026.SM_LB_MR01_ServiceDock_Static_v026");
    constexpr TCHAR CRStaticPath[] = TEXT("/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026/CR01/SM_LB_CR01_ServiceDock_Static_v026.SM_LB_CR01_ServiceDock_Static_v026");
    constexpr TCHAR ProbePath[] = TEXT("/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026/MR01/SM_LB_MR01_ServiceDock_calibration_probe_v026.SM_LB_MR01_ServiceDock_calibration_probe_v026");
    constexpr TCHAR DoorPath[] = TEXT("/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026/MR01/SM_LB_MR01_ServiceDock_tool_rack_door_v026.SM_LB_MR01_ServiceDock_tool_rack_door_v026");
    constexpr TCHAR DrawerPath[] = TEXT("/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026/MR01/SM_LB_MR01_ServiceDock_waste_drawer_v026.SM_LB_MR01_ServiceDock_waste_drawer_v026");
    constexpr TCHAR MRResolvedPath[] = TEXT("/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006/SM_LB_MR01_ServiceDock_ResolvedMaterials_v006.SM_LB_MR01_ServiceDock_ResolvedMaterials_v006");
    constexpr TCHAR CRResolvedPath[] = TEXT("/Game/LineBoss/SupportRobots/ServiceDocks/Resolved_v006/SM_LB_CR01_ServiceDock_ResolvedMaterials_v006.SM_LB_CR01_ServiceDock_ResolvedMaterials_v006");
}

ALBSupportRobotServiceDock::ALBSupportRobotServiceDock()
{
    PrimaryActorTick.bCanEverTick = true;

    BlockingEnvelope = CreateDefaultSubobject<UBoxComponent>(TEXT("BlockingEnvelope"));
    SetRootComponent(BlockingEnvelope);
    BlockingEnvelope->SetBoxExtent(FVector(130.0f, 75.0f, 85.0f));
    BlockingEnvelope->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BlockingEnvelope->SetCanEverAffectNavigation(false);

    StructuralLeft = CreateDefaultSubobject<UBoxComponent>(TEXT("StructuralLeft"));
    StructuralLeft->SetupAttachment(BlockingEnvelope);
    StructuralLeft->SetBoxExtent(FVector(33.5f, 74.55f, 85.35f));
    StructuralLeft->SetRelativeLocation(FVector(-96.5f, -144.45f, 85.35f));
    StructuralLeft->SetCollisionProfileName(TEXT("BlockAll"));
    StructuralLeft->SetCanEverAffectNavigation(true);

    StructuralRight = CreateDefaultSubobject<UBoxComponent>(TEXT("StructuralRight"));
    StructuralRight->SetupAttachment(BlockingEnvelope);
    StructuralRight->SetBoxExtent(FVector(33.5f, 74.55f, 85.35f));
    StructuralRight->SetRelativeLocation(FVector(96.5f, -144.45f, 85.35f));
    StructuralRight->SetCollisionProfileName(TEXT("BlockAll"));
    StructuralRight->SetCanEverAffectNavigation(true);

    StructuralHeader = CreateDefaultSubobject<UBoxComponent>(TEXT("StructuralHeader"));
    StructuralHeader->SetupAttachment(BlockingEnvelope);
    StructuralHeader->SetBoxExtent(FVector(63.0f, 74.55f, 10.0f));
    StructuralHeader->SetRelativeLocation(FVector(0.0f, -144.45f, 160.7f));
    StructuralHeader->SetCollisionProfileName(TEXT("BlockAll"));
    StructuralHeader->SetCanEverAffectNavigation(true);

    StaticBody = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("StaticBody"));
    StaticBody->SetupAttachment(BlockingEnvelope);
    StaticBody->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    StaticBody->SetCanEverAffectNavigation(false);

    CalibrationProbe = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CalibrationProbe"));
    CalibrationProbe->SetupAttachment(StaticBody);
    CalibrationProbe->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    CalibrationProbe->SetCollisionProfileName(TEXT("OverlapAllDynamic"));

    ToolRackDoor = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ToolRackDoor"));
    ToolRackDoor->SetupAttachment(StaticBody);
    ToolRackDoor->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    ToolRackDoor->SetCollisionProfileName(TEXT("BlockAll"));

    WasteDrawer = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WasteDrawer"));
    WasteDrawer->SetupAttachment(StaticBody);
    WasteDrawer->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
    WasteDrawer->SetCollisionProfileName(TEXT("BlockAll"));

    static ConstructorHelpers::FObjectFinder<UStaticMesh> MRStatic(MRStaticPath);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CRStatic(CRStaticPath);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Probe(ProbePath);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Door(DoorPath);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Drawer(DrawerPath);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> MRResolved(MRResolvedPath);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CRResolved(CRResolvedPath);
    MR01StaticMesh = MRStatic.Object;
    CR01StaticMesh = CRStatic.Object;
    MR01ResolvedMaterialSource = MRResolved.Object;
    CR01ResolvedMaterialSource = CRResolved.Object;
    CalibrationProbe->SetStaticMesh(Probe.Object);
    ToolRackDoor->SetStaticMesh(Door.Object);
    WasteDrawer->SetStaticMesh(Drawer.Object);
    ApplyVariantPresentation();
    ApplyMechanismPose();
}

void ALBSupportRobotServiceDock::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    ApplyVariantPresentation();
    ApplyMechanismPose();
}

void ALBSupportRobotServiceDock::BeginPlay()
{
    Super::BeginPlay();
    DockState = ELBServiceDockState::SafeClosed;
    MechanismAlpha = 0.0f;
    bSafetyZoneClear = false;
    bOperatorPermitGranted = false;
    bIsolationHealthy = false;
    ApplyVariantPresentation();
    ApplyMechanismPose();
}

void ALBSupportRobotServiceDock::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if ((DockState == ELBServiceDockState::Opening || DockState == ELBServiceDockState::ServiceReady)
        && (!HasServicePermissives() || FindCompatibleDockedRobot() == nullptr))
    {
        ForceSafeClose(TEXT("Docked robot or service permissive lost"));
    }

    const float Step = DeltaSeconds / MechanismTravelSeconds;
    if (DockState == ELBServiceDockState::Opening)
    {
        MechanismAlpha = FMath::Min(1.0f, MechanismAlpha + Step);
        if (MechanismAlpha >= 1.0f)
        {
            DockState = ELBServiceDockState::ServiceReady;
        }
    }
    else if (DockState == ELBServiceDockState::Closing || DockState == ELBServiceDockState::SafetyStop)
    {
        MechanismAlpha = FMath::Max(0.0f, MechanismAlpha - Step);
        if (MechanismAlpha <= 0.0f)
        {
            DockState = ELBServiceDockState::SafeClosed;
        }
    }
    ApplyMechanismPose();
}

bool ALBSupportRobotServiceDock::ConfigureDock(FName NewDockId, ELBServiceDockVariant NewVariant)
{
    if (NewDockId.IsNone() || DockState != ELBServiceDockState::SafeClosed)
    {
        return false;
    }
    DockId = NewDockId;
    Variant = NewVariant;
    ApplyVariantPresentation();
    return true;
}

void ALBSupportRobotServiceDock::SetServicePermissives(bool bInSafetyZoneClear, bool bInOperatorPermitGranted, bool bInIsolationHealthy)
{
    bSafetyZoneClear = bInSafetyZoneClear;
    bOperatorPermitGranted = bInOperatorPermitGranted;
    bIsolationHealthy = bInIsolationHealthy;
    if (!HasServicePermissives() && MechanismAlpha > 0.0f)
    {
        ForceSafeClose(TEXT("Service permissive removed"));
    }
}

bool ALBSupportRobotServiceDock::BeginServiceSequence()
{
    if (DockState != ELBServiceDockState::SafeClosed || !HasServicePermissives() || FindCompatibleDockedRobot() == nullptr)
    {
        return false;
    }
    if (Variant == ELBServiceDockVariant::CR01_Cleaning)
    {
        // CR service connectors are visually retained, but their actuator travel is still TBC.
        DockState = ELBServiceDockState::ServiceReady;
        return true;
    }
    DockState = ELBServiceDockState::Opening;
    return true;
}

bool ALBSupportRobotServiceDock::CompleteServiceSequence()
{
    if (DockState != ELBServiceDockState::ServiceReady)
    {
        return false;
    }
    ++CompletedServiceCycles;
    DockState = Variant == ELBServiceDockVariant::MR01_Maintenance ? ELBServiceDockState::Closing : ELBServiceDockState::SafeClosed;
    return true;
}

void ALBSupportRobotServiceDock::ForceSafeClose(const FString& Reason)
{
    LastSafeStopReason = Reason;
    bOperatorPermitGranted = false;
    DockState = MechanismAlpha > 0.0f ? ELBServiceDockState::SafetyStop : ELBServiceDockState::SafeClosed;
}

FLBServiceDockSaveState ALBSupportRobotServiceDock::CaptureSaveState() const
{
    FLBServiceDockSaveState Result;
    Result.DockId = DockId;
    Result.Variant = Variant;
    Result.CompletedServiceCycles = CompletedServiceCycles;
    Result.bInspectionDue = bInspectionDue;
    return Result;
}

bool ALBSupportRobotServiceDock::RestoreSaveState(const FLBServiceDockSaveState& SavedState)
{
    if (SavedState.Version != 1 || SavedState.DockId.IsNone() || SavedState.DockId != DockId || SavedState.Variant != Variant)
    {
        return false;
    }
    CompletedServiceCycles = FMath::Max(0, SavedState.CompletedServiceCycles);
    bInspectionDue = SavedState.bInspectionDue;
    DockState = ELBServiceDockState::SafeClosed;
    MechanismAlpha = 0.0f;
    bSafetyZoneClear = false;
    bOperatorPermitGranted = false;
    bIsolationHealthy = false;
    ApplyMechanismPose();
    return true;
}

void ALBSupportRobotServiceDock::ApplyVariantPresentation()
{
    const bool bMaintenance = Variant == ELBServiceDockVariant::MR01_Maintenance;
    StaticBody->SetStaticMesh(bMaintenance ? MR01StaticMesh : CR01StaticMesh);
    UStaticMesh* ResolvedSource = bMaintenance ? MR01ResolvedMaterialSource : CR01ResolvedMaterialSource;
    ApplyResolvedMaterialOverrides(StaticBody, ResolvedSource);
    ApplyResolvedMaterialOverrides(CalibrationProbe, ResolvedSource);
    ApplyResolvedMaterialOverrides(ToolRackDoor, ResolvedSource);
    ApplyResolvedMaterialOverrides(WasteDrawer, ResolvedSource);
    CalibrationProbe->SetVisibility(bMaintenance, true);
    ToolRackDoor->SetVisibility(bMaintenance, true);
    WasteDrawer->SetVisibility(bMaintenance, true);
    CalibrationProbe->SetCollisionEnabled(bMaintenance ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    ToolRackDoor->SetCollisionEnabled(bMaintenance ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
    WasteDrawer->SetCollisionEnabled(bMaintenance ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);
}

void ALBSupportRobotServiceDock::ApplyResolvedMaterialOverrides(UStaticMeshComponent* TargetComponent, UStaticMesh* MaterialSource)
{
    UStaticMesh* TargetMesh = TargetComponent ? TargetComponent->GetStaticMesh() : nullptr;
    if (!TargetMesh || !MaterialSource)
    {
        return;
    }
    const TArray<FStaticMaterial>& SourceMaterials = MaterialSource->GetStaticMaterials();
    const TArray<FStaticMaterial>& TargetMaterials = TargetMesh->GetStaticMaterials();
    for (int32 TargetIndex = 0; TargetIndex < TargetMaterials.Num(); ++TargetIndex)
    {
        const FName SlotName = TargetMaterials[TargetIndex].MaterialSlotName;
        const FStaticMaterial* Match = SourceMaterials.FindByPredicate([SlotName](const FStaticMaterial& Candidate)
        {
            return Candidate.MaterialSlotName == SlotName;
        });
        if (Match && Match->MaterialInterface)
        {
            TargetComponent->SetMaterial(TargetIndex, Match->MaterialInterface);
        }
    }
}

void ALBSupportRobotServiceDock::ApplyMechanismPose()
{
    // Exact source-authorised pivots, converted millimetres to centimetres.
    // FBX -Y-forward conversion maps authored Blender +Y to Unreal -Y.
    CalibrationProbe->SetRelativeLocation(FVector(0.0f + 18.0f * MechanismAlpha, -90.0f, 95.0f));
    ToolRackDoor->SetRelativeLocation(FVector(50.0f, -100.0f, 90.0f));
    ToolRackDoor->SetRelativeRotation(FRotator(0.0f, 100.0f * MechanismAlpha, 0.0f));
    WasteDrawer->SetRelativeLocation(FVector(-50.0f, -90.0f + 45.0f * MechanismAlpha, 42.0f));
}

ALBSupportRobot* ALBSupportRobotServiceDock::FindCompatibleDockedRobot() const
{
    UWorld* World = GetWorld();
    if (!World || DockId.IsNone())
    {
        return nullptr;
    }
    const FName ExpectedVariant = Variant == ELBServiceDockVariant::MR01_Maintenance ? FName(TEXT("LB-MR01")) : FName(TEXT("LB-CR01"));
    for (TActorIterator<ALBSupportRobot> It(World); It; ++It)
    {
        ALBSupportRobot* Robot = *It;
        const FLBSupportRobotSaveState State = Robot->CaptureCommonSaveState();
        if (Robot->IsDocked() && Robot->GetDockId() == DockId && State.VariantId == ExpectedVariant && !Robot->HasRouteAuthority())
        {
            return Robot;
        }
    }
    return nullptr;
}

bool ALBSupportRobotServiceDock::HasServicePermissives() const
{
    return bSafetyZoneClear && bOperatorPermitGranted && bIsolationHealthy;
}
