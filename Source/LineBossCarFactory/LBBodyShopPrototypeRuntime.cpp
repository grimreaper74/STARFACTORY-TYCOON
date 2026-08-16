#include "LBBodyShopPrototypeRuntime.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "LBBodyShopBuildAuthority.h"
#include "LBBodyShopCellActor.h"
#include "LBBodyShopExperimentalSaveGame.h"
#include "LBBodyShopRobotActor.h"

namespace LBBodyShopPrototypeRuntimePrivate
{
    constexpr float StillageTransferSeconds = 1.5f;
    // Matches the authored skid-conveyor ports. The powered rollers reach 31 cm,
    // so this datum keeps the carrier runners visibly above the continuous line.
    constexpr float SkidConveyorDatumHeightCm = 35.0f;
    constexpr float PoweredRollerTopCm = 31.0f;
    constexpr float WorkpieceHeightCm = 54.0f;
    constexpr float PanelTransferArcHeightCm = 220.0f;
    const FVector PanelStillageLocalOffset(-190.0f, 110.0f, 0.0f);
    const FName PilotSourceStillageId(TEXT("BODYSHOP-PILOT-STILLAGE-001"));
    const FName PilotSkidId(TEXT("BODYSHOP-PILOT-SKID-001"));
    const TCHAR* PilotStillagePath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_PanelStillage_Full_v002.SM_LB_BodyShopSupport_PanelStillage_Full_v002");
    const TCHAR* PilotSkidPath =
        TEXT("/Game/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Carrier/SM_LB_C2040_BIWBaseSkid_v001.SM_LB_C2040_BIWBaseSkid_v001");
    const TCHAR* PilotUnderbodyPath =
        TEXT("/Game/LineBoss/Candidates/Vehicles/Cairnwell2040/BIWBaseKitRuntime_v001/Workpiece/SM_LB_C2040_BIWBaseKit_Underbody_v001.SM_LB_C2040_BIWBaseKit_Underbody_v001");

    FString StageStatus(const ELBBodyShopRuntimeStage Stage)
    {
        switch (Stage)
        {
        case ELBBodyShopRuntimeStage::Ready:
            return TEXT("BODY SHOP UNDERBODY SLICE READY");
        case ELBBodyShopRuntimeStage::AwaitingPanelStillage:
            return TEXT("BODY SHOP STARVED: PILOT PANEL STILLAGE REQUIRED");
        case ELBBodyShopRuntimeStage::TransferringStillage:
            return TEXT("BODY SHOP TRANSFERRING FULL STILLAGE TO PRESENTATION");
        case ELBBodyShopRuntimeStage::PresentingPanel:
            return TEXT("BODY SHOP PRESENTING PANEL WITH EIGHT-CUP HANDLING TOOL");
        case ELBBodyShopRuntimeStage::WeldingUnderbody:
            return TEXT("BODY SHOP SPOT-WELDING UNDERBODY ON PILOT SKID");
        case ELBBodyShopRuntimeStage::ConveyingSkid:
            return TEXT("BODY SHOP CONVEYING PILOT SKID TO VISION");
        case ELBBodyShopRuntimeStage::Inspecting:
            return TEXT("BODY SHOP INSPECTING UNDERBODY AT VISION GATE");
        case ELBBodyShopRuntimeStage::OutputBlocked:
            return TEXT("BODY SHOP BLOCKED: OUTPUT BUFFER UNAVAILABLE");
        case ELBBodyShopRuntimeStage::QualityHold:
            return TEXT("BODY SHOP QUALITY HOLD: VISION FAILURE");
        case ELBBodyShopRuntimeStage::Complete:
            return TEXT("BODY SHOP PILOT UNDERBODY HELD IN OUTPUT BUFFER");
        case ELBBodyShopRuntimeStage::Faulted:
            return TEXT("BODY SHOP PROTOTYPE RUNTIME FAULTED");
        case ELBBodyShopRuntimeStage::Offline:
        default:
            return TEXT("BODY SHOP PROTOTYPE WAITING FOR ISOLATED BUILD AUTHORITY");
        }
    }

    void ConfigurePresentationSafety(UStaticMeshComponent* Component)
    {
        if (!Component) return;
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCollisionResponseToAllChannels(ECR_Ignore);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetCastShadow(true);
        Component->SetHiddenInGame(false, true);
        Component->SetVisibility(false, true);
    }

    FString PresentationMeshPath(const UStaticMeshComponent* Component)
    {
        const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
        return Mesh ? Mesh->GetPathName() : FString();
    }

    bool IsPresentationVisibleAndUnhidden(const AActor* Owner,
        const UStaticMeshComponent* Component)
    {
        return Owner && !Owner->IsHidden() && Component && Component->GetStaticMesh()
            && Component->IsVisible() && !Component->bHiddenInGame;
    }

    FBox PresentationWorldBounds(const UStaticMeshComponent* Component)
    {
        const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
        return Mesh
            ? Mesh->GetBoundingBox().TransformBy(Component->GetComponentTransform())
            : FBox(EForceInit::ForceInit);
    }

    FBox PresentationBoundsRelativeTo(const UStaticMeshComponent* Component,
        const FTransform& ParentWorldTransform)
    {
        const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
        if (!Mesh) return FBox(EForceInit::ForceInit);
        const FTransform RelativeTransform = Component->GetComponentTransform().GetRelativeTransform(
            ParentWorldTransform);
        return Mesh->GetBoundingBox().TransformBy(RelativeTransform);
    }

    float SmoothProgress(const float Progress01)
    {
        const float Clamped = FMath::Clamp(Progress01, 0.0f, 1.0f);
        return Clamped * Clamped * (3.0f - 2.0f * Clamped);
    }

    FTransform WithLocalOffset(const FTransform& Transform, const FVector& LocalOffset)
    {
        return FTransform(Transform.GetRotation(), Transform.TransformPosition(LocalOffset),
            Transform.GetScale3D());
    }

    FTransform BlendTransforms(const FTransform& Start, const FTransform& End,
        const float Progress01)
    {
        FTransform Result;
        Result.Blend(Start, End, SmoothProgress(Progress01));
        return Result;
    }
}

ALBBodyShopPrototypeRuntime::ALBBodyShopPrototypeRuntime()
{
    PrimaryActorTick.bCanEverTick = true;
    SetActorEnableCollision(false);
    SetReplicates(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PrototypeRuntimeRoot"));
    SetRootComponent(SceneRoot);
    PilotStillagePresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("PilotStillagePresentation"));
    PilotStillagePresentation->SetupAttachment(SceneRoot);
    PilotPanelPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("PilotPanelPresentation"));
    PilotPanelPresentation->SetupAttachment(SceneRoot);
    PilotSkidPresentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PilotSkidPresentation"));
    PilotSkidPresentation->SetupAttachment(SceneRoot);
    PilotUnderbodyPresentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PilotUnderbodyPresentation"));
    PilotUnderbodyPresentation->SetupAttachment(SceneRoot);
    LBBodyShopPrototypeRuntimePrivate::ConfigurePresentationSafety(PilotStillagePresentation);
    LBBodyShopPrototypeRuntimePrivate::ConfigurePresentationSafety(PilotPanelPresentation);
    LBBodyShopPrototypeRuntimePrivate::ConfigurePresentationSafety(PilotSkidPresentation);
    LBBodyShopPrototypeRuntimePrivate::ConfigurePresentationSafety(PilotUnderbodyPresentation);

    PilotStillageMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopPrototypeRuntimePrivate::PilotStillagePath));
    PilotSkidMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopPrototypeRuntimePrivate::PilotSkidPath));
    PilotUnderbodyMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopPrototypeRuntimePrivate::PilotUnderbodyPath));
    // AInfo deliberately hides itself in its base constructor. This runtime owns
    // game-visible WIP components, so it must explicitly opt back into rendering.
    SetActorHiddenInGame(false);
    RuntimeStatusText = LBBodyShopPrototypeRuntimePrivate::StageStatus(RuntimeStage);
    Tags.AddUnique(TEXT("LB.BodyShop.Experimental.Runtime.v001"));
}

void ALBBodyShopPrototypeRuntime::BeginPlay()
{
    Super::BeginPlay();
    RefreshRuntimeCellStates();
    RefreshPilotPresentation();
}

void ALBBodyShopPrototypeRuntime::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bRuntimeInitialised) return;
    if (bSimulationRunning) AdvanceSimulation(DeltaSeconds);
    RefreshRuntimeCellStates();
    RefreshRobotPoses();
    RefreshPilotPresentation();
}

bool ALBBodyShopPrototypeRuntime::BindBuildAuthority(ALBBodyShopBuildAuthority* InBuildAuthority,
    FString& OutReason)
{
    OutReason.Reset();
    if (!IsValid(InBuildAuthority))
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE REQUIRES A VALID ISOLATED BUILD AUTHORITY");
        return false;
    }
    if (GetWorld() && InBuildAuthority->GetWorld() && GetWorld() != InBuildAuthority->GetWorld())
    {
        OutReason = TEXT("BODY SHOP BUILD AUTHORITY MUST BELONG TO THE SAME ISOLATED WORLD");
        return false;
    }
    if (BuildAuthority.Get() != InBuildAuthority && (bRuntimeInitialised || IsPilotCycleActive()))
    {
        OutReason = TEXT("BODY SHOP RUNTIME CANNOT REBIND AFTER ITS SLICE HAS BEEN INITIALISED");
        return false;
    }
    BuildAuthority = InBuildAuthority;
    RuntimeStage = ELBBodyShopRuntimeStage::Offline;
    RuntimeStatusText = TEXT("BODY SHOP BUILD AUTHORITY BOUND; SLICE NOT YET INITIALISED");
    OutReason = RuntimeStatusText;
    return true;
}

bool ALBBodyShopPrototypeRuntime::IsAuthorityReady(FString& OutReason) const
{
    OutReason.Reset();
    if (!IsValid(BuildAuthority.Get()))
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE HAS NO BOUND BUILD AUTHORITY");
        return false;
    }
    if (GetWorld() && BuildAuthority->GetWorld() && GetWorld() != BuildAuthority->GetWorld())
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE BUILD AUTHORITY IS IN A DIFFERENT WORLD");
        return false;
    }
    return true;
}

TArray<FLBBodyShopPilotRobotBinding> ALBBodyShopPrototypeRuntime::GetRequiredPilotRobotBindings()
{
    TArray<FLBBodyShopPilotRobotBinding> Result;
    const auto Add = [&Result](const FName DefinitionId, const FName SlotId,
        const ELBBodyShopRobotRole RobotRole, const ELBBodyShopToolType Tool)
    {
        FLBBodyShopPilotRobotBinding& Binding = Result.AddDefaulted_GetRef();
        Binding.CellDefinitionId = DefinitionId;
        Binding.SlotId = SlotId;
        Binding.Role = RobotRole;
        Binding.Tool = Tool;
    };
    Add(LBBodyShopPrototypeIds::PanelPresentation, TEXT("ROBOT_HND_01"),
        ELBBodyShopRobotRole::PanelHandling, ELBBodyShopToolType::VacuumEightCup);
    Add(LBBodyShopPrototypeIds::UnderbodyFixture, TEXT("ROBOT_WELD_LEFT"),
        ELBBodyShopRobotRole::SpotWelding, ELBBodyShopToolType::SpotCGun);
    Add(LBBodyShopPrototypeIds::UnderbodyFixture, TEXT("ROBOT_WELD_RIGHT"),
        ELBBodyShopRobotRole::SpotWelding, ELBBodyShopToolType::SpotCGun);
    return Result;
}

FLBBodyShopWIPPresentationSample ALBBodyShopPrototypeRuntime::SampleWIPPresentation(
    const ELBBodyShopRuntimeStage Stage, const float StageProgress01,
    const FTransform& StillageDockTransform,
    const FTransform& PanelPresentationTransform,
    const FTransform& UnderbodyFixtureTransform,
    const FTransform& StraightConveyorTransform,
    const FTransform& VisionGateTransform,
    const FTransform& OutputBufferTransform)
{
    using namespace LBBodyShopPrototypeRuntimePrivate;

    FLBBodyShopWIPPresentationSample Sample;
    Sample.Progress01 = FMath::Clamp(StageProgress01, 0.0f, 1.0f);
    const FTransform PanelStillageAnchor = WithLocalOffset(
        PanelPresentationTransform, PanelStillageLocalOffset);
    const FTransform PanelPickupAnchor = WithLocalOffset(PanelPresentationTransform,
        PanelStillageLocalOffset + FVector(0.0f, 0.0f, WorkpieceHeightCm));
    const FTransform FixtureSkidAnchor = WithLocalOffset(UnderbodyFixtureTransform,
        FVector(0.0f, 0.0f, SkidConveyorDatumHeightCm));
    const FTransform FixtureWorkpieceAnchor = WithLocalOffset(FixtureSkidAnchor,
        FVector(0.0f, 0.0f, WorkpieceHeightCm));

    switch (Stage)
    {
    case ELBBodyShopRuntimeStage::TransferringStillage:
        Sample.Kind = ELBBodyShopWIPPresentationKind::Stillage;
        Sample.WorldTransform = BlendTransforms(StillageDockTransform,
            PanelStillageAnchor, Sample.Progress01);
        break;
    case ELBBodyShopRuntimeStage::PresentingPanel:
    {
        Sample.Kind = ELBBodyShopWIPPresentationKind::Panel;
        Sample.WorldTransform = BlendTransforms(PanelPickupAnchor,
            FixtureWorkpieceAnchor, Sample.Progress01);
        FVector Location = Sample.WorldTransform.GetLocation();
        Location.Z += PanelTransferArcHeightCm * FMath::Sin(
            PI * SmoothProgress(Sample.Progress01));
        Sample.WorldTransform.SetLocation(Location);
        break;
    }
    case ELBBodyShopRuntimeStage::WeldingUnderbody:
        Sample.Kind = ELBBodyShopWIPPresentationKind::SkidUnderbody;
        Sample.WorldTransform = FixtureSkidAnchor;
        break;
    case ELBBodyShopRuntimeStage::ConveyingSkid:
        Sample.Kind = ELBBodyShopWIPPresentationKind::SkidUnderbody;
        Sample.WorldTransform = Sample.Progress01 <= 0.5f
            ? BlendTransforms(FixtureSkidAnchor,
                WithLocalOffset(StraightConveyorTransform,
                    FVector(0.0f, 0.0f, SkidConveyorDatumHeightCm)),
                Sample.Progress01 * 2.0f)
            : BlendTransforms(
                WithLocalOffset(StraightConveyorTransform,
                    FVector(0.0f, 0.0f, SkidConveyorDatumHeightCm)),
                WithLocalOffset(VisionGateTransform,
                    FVector(0.0f, 0.0f, SkidConveyorDatumHeightCm)),
                (Sample.Progress01 - 0.5f) * 2.0f);
        break;
    case ELBBodyShopRuntimeStage::Inspecting:
    case ELBBodyShopRuntimeStage::OutputBlocked:
    case ELBBodyShopRuntimeStage::QualityHold:
        Sample.Kind = ELBBodyShopWIPPresentationKind::SkidUnderbody;
        Sample.WorldTransform = WithLocalOffset(VisionGateTransform,
            FVector(0.0f, 0.0f, SkidConveyorDatumHeightCm));
        break;
    case ELBBodyShopRuntimeStage::Complete:
        Sample.Kind = ELBBodyShopWIPPresentationKind::SkidUnderbody;
        Sample.WorldTransform = WithLocalOffset(OutputBufferTransform,
            FVector(0.0f, 0.0f, SkidConveyorDatumHeightCm));
        break;
    default:
        Sample.Kind = ELBBodyShopWIPPresentationKind::None;
        Sample.WorldTransform = FTransform::Identity;
        Sample.Progress01 = 0.0f;
        break;
    }
    return Sample;
}

ALBBodyShopCellActor* ALBBodyShopPrototypeRuntime::FindCellByDefinition(
    const FName DefinitionId) const
{
    if (!BuildAuthority) return nullptr;
    for (ALBBodyShopCellActor* Cell : BuildAuthority->GetPlacedCells())
    {
        if (IsValid(Cell) && Cell->GetDefinitionId() == DefinitionId) return Cell;
    }
    return nullptr;
}

void ALBBodyShopPrototypeRuntime::HidePilotPresentation()
{
    for (UStaticMeshComponent* Component : {PilotStillagePresentation.Get(),
        PilotPanelPresentation.Get(), PilotSkidPresentation.Get(),
        PilotUnderbodyPresentation.Get()})
    {
        if (Component) Component->SetVisibility(false, true);
    }
    CurrentWIPPresentationSample = FLBBodyShopWIPPresentationSample();
}

bool ALBBodyShopPrototypeRuntime::ValidatePilotPresentationArt(FString& OutReason)
{
    OutReason.Reset();
    UStaticMesh* Stillage = PilotStillageMesh.LoadSynchronous();
    UStaticMesh* Skid = PilotSkidMesh.LoadSynchronous();
    UStaticMesh* Underbody = PilotUnderbodyMesh.LoadSynchronous();
    TArray<FString> MissingArt;
    if (!Stillage) MissingArt.Add(TEXT("PILOT STILLAGE"));
    if (!Skid) MissingArt.Add(TEXT("PILOT SKID"));
    if (!Underbody) MissingArt.Add(TEXT("PILOT PANEL/UNDERBODY"));
    if (!MissingArt.IsEmpty())
    {
        for (UStaticMeshComponent* Component : {PilotStillagePresentation.Get(),
            PilotPanelPresentation.Get(), PilotSkidPresentation.Get(),
            PilotUnderbodyPresentation.Get()})
        {
            if (Component) Component->SetStaticMesh(nullptr);
        }
        HidePilotPresentation();
        bWIPPresentationArtValid = false;
        WIPPresentationFailureReason = FString::Printf(
            TEXT("BODY SHOP RUNTIME WIP ART IS MISSING: %s"),
            *FString::Join(MissingArt, TEXT(", ")));
        OutReason = WIPPresentationFailureReason;
        return false;
    }

    PilotStillagePresentation->SetStaticMesh(Stillage);
    PilotPanelPresentation->SetStaticMesh(Underbody);
    PilotSkidPresentation->SetStaticMesh(Skid);
    PilotUnderbodyPresentation->SetStaticMesh(Underbody);
    HidePilotPresentation();
    bWIPPresentationArtValid = true;
    WIPPresentationFailureReason.Reset();
    return true;
}

bool ALBBodyShopPrototypeRuntime::TryGetPilotPresentationAnchors(
    FTransform& OutStillageDock, FTransform& OutPanelPresentation,
    FTransform& OutUnderbodyFixture, FTransform& OutStraightConveyor,
    FTransform& OutVisionGate, FTransform& OutOutputBuffer, FString& OutReason) const
{
    OutReason.Reset();
    const ALBBodyShopCellActor* StillageDock = FindCellByDefinition(
        LBBodyShopPrototypeIds::FullStillageDock);
    const ALBBodyShopCellActor* PanelPresentation = FindCellByDefinition(
        LBBodyShopPrototypeIds::PanelPresentation);
    const ALBBodyShopCellActor* UnderbodyFixture = FindCellByDefinition(
        LBBodyShopPrototypeIds::UnderbodyFixture);
    const ALBBodyShopCellActor* StraightConveyor = FindCellByDefinition(
        LBBodyShopPrototypeIds::StraightSkidConveyor);
    const ALBBodyShopCellActor* VisionGate = FindCellByDefinition(
        LBBodyShopPrototypeIds::BasicVisionGate);
    const ALBBodyShopCellActor* OutputBuffer = FindCellByDefinition(
        LBBodyShopPrototypeIds::OutputBuffer);
    if (!StillageDock || !PanelPresentation || !UnderbodyFixture || !StraightConveyor
        || !VisionGate || !OutputBuffer)
    {
        OutReason = TEXT("BODY SHOP RUNTIME WIP PRESENTATION REQUIRES ALL SIX AUTHORED CELL ANCHORS");
        return false;
    }
    OutStillageDock = StillageDock->GetActorTransform();
    OutPanelPresentation = PanelPresentation->GetActorTransform();
    OutUnderbodyFixture = UnderbodyFixture->GetActorTransform();
    OutStraightConveyor = StraightConveyor->GetActorTransform();
    OutVisionGate = VisionGate->GetActorTransform();
    OutOutputBuffer = OutputBuffer->GetActorTransform();
    return true;
}

bool ALBBodyShopPrototypeRuntime::ValidateRequiredRobotBindings(FString& OutReason) const
{
    OutReason.Reset();
    for (const FLBBodyShopPilotRobotBinding& Binding : GetRequiredPilotRobotBindings())
    {
        const ALBBodyShopCellActor* Cell = FindCellByDefinition(Binding.CellDefinitionId);
        if (!Cell)
        {
            OutReason = TEXT("BODY SHOP PILOT SLICE IS MISSING A ROBOT HOST FIXTURE");
            return false;
        }
        const FLBBodyShopRobotSlotDefinition* Slot = Cell->GetDefinition().RobotSlots.FindByPredicate(
            [&Binding](const FLBBodyShopRobotSlotDefinition& Candidate)
            {
                return Candidate.SlotId == Binding.SlotId;
            });
        const FLBBodyShopRobotAssignment* Assignment = Cell->GetRobotAssignments().FindByPredicate(
            [&Binding](const FLBBodyShopRobotAssignment& Candidate)
            {
                return Candidate.SlotId == Binding.SlotId;
            });
        if (!Slot || !Assignment || Assignment->Role != Binding.Role || Assignment->Tool != Binding.Tool
            || !Assignment->bEnabled || Assignment->Condition01 <= 0.0f)
        {
            OutReason = TEXT("BODY SHOP PILOT ROBOT DOES NOT MATCH ITS AUTHORED FIXTURE SLOT");
            return false;
        }
    }
    return true;
}

void ALBBodyShopPrototypeRuntime::DestroyRuntimeRobots()
{
    for (ALBBodyShopRobotActor* Robot : SpawnedRobots)
    {
        if (IsValid(Robot)) Robot->Destroy();
    }
    SpawnedRobots.Reset();
}

int32 ALBBodyShopPrototypeRuntime::GetRunningRobotArticulationCount() const
{
    int32 Result = 0;
    for (const ALBBodyShopRobotActor* Robot : SpawnedRobots)
    {
        if (IsValid(Robot) && Robot->IsArticulationRunning()) ++Result;
    }
    return Result;
}

void ALBBodyShopPrototypeRuntime::ApplyRobotArticulationRunningState()
{
    for (ALBBodyShopRobotActor* Robot : SpawnedRobots)
    {
        if (IsValid(Robot)) Robot->SetArticulationRunning(bSimulationRunning);
    }
}

void ALBBodyShopPrototypeRuntime::SetSimulationAndArticulationRunning(
    const bool bInRunning)
{
    bSimulationRunning = bInRunning;
    ApplyRobotArticulationRunningState();
}

bool ALBBodyShopPrototypeRuntime::SpawnConfiguredRobots(FString& OutReason)
{
    OutReason.Reset();
    DestroyRuntimeRobots();
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE WORLD IS UNAVAILABLE FOR ROBOT SPAWNING");
        return false;
    }

    for (const FLBBodyShopPilotRobotBinding& Binding : GetRequiredPilotRobotBindings())
    {
        ALBBodyShopCellActor* Cell = FindCellByDefinition(Binding.CellDefinitionId);
        if (!Cell)
        {
            OutReason = TEXT("BODY SHOP PILOT ROBOT HOST CELL IS MISSING");
            DestroyRuntimeRobots();
            return false;
        }
        const FLBBodyShopRobotSlotDefinition* Slot = Cell->GetDefinition().RobotSlots.FindByPredicate(
            [&Binding](const FLBBodyShopRobotSlotDefinition& Candidate)
            {
                return Candidate.SlotId == Binding.SlotId;
            });
        const FLBBodyShopRobotAssignment* Assignment = Cell->GetRobotAssignments().FindByPredicate(
            [&Binding](const FLBBodyShopRobotAssignment& Candidate)
            {
                return Candidate.SlotId == Binding.SlotId;
            });
        if (!Slot || !Assignment)
        {
            OutReason = TEXT("BODY SHOP PILOT ROBOT HAS NO AUTHORED SLOT ASSIGNMENT");
            DestroyRuntimeRobots();
            return false;
        }

        FActorSpawnParameters SpawnParams;
        SpawnParams.Owner = this;
        SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        const FTransform WorldTransform = Slot->LocalMountTransform * Cell->GetActorTransform();
        ALBBodyShopRobotActor* Robot = World->SpawnActor<ALBBodyShopRobotActor>(
            ALBBodyShopRobotActor::StaticClass(), WorldTransform, SpawnParams);
        if (!Robot || !Robot->ConfigureForAuthoredSlot(Cell->GetCellId(), *Slot, *Assignment, OutReason))
        {
            if (Robot) Robot->Destroy();
            if (OutReason.IsEmpty())
                OutReason = TEXT("BODY SHOP PILOT ROBOT COULD NOT LOAD ITS AUTHORED ART");
            DestroyRuntimeRobots();
            return false;
        }
        Robot->SetAuthoredPose(ELBBodyShopRobotPose::Home, true);
        Robot->SetArticulationRunning(bSimulationRunning);
        SpawnedRobots.Add(Robot);
    }

    if (SpawnedRobots.Num() != GetRequiredPilotRobotBindings().Num())
    {
        OutReason = TEXT("BODY SHOP PILOT ROBOT COUNT DOES NOT MATCH THE APPROVED THREE-ROBOT SLICE");
        DestroyRuntimeRobots();
        return false;
    }
    return true;
}

bool ALBBodyShopPrototypeRuntime::BuildAndCommissionApprovedUnderbodySlice(FString& OutReason)
{
    OutReason.Reset();
    if (!IsAuthorityReady(OutReason)) return false;
    if (IsPilotCycleActive())
    {
        OutReason = TEXT("BODY SHOP PILOT WIP MUST BE CLEARED BEFORE REBUILDING THE SLICE");
        return false;
    }
    // Commissioning is a stopped-state operation. Failures below must never
    // leave an earlier robot articulation state running behind a faulted stage.
    SetSimulationAndArticulationRunning(false);
    if (!ValidatePilotPresentationArt(OutReason))
    {
        bRuntimeInitialised = false;
        SetSimulationAndArticulationRunning(false);
        EnterStage(ELBBodyShopRuntimeStage::Faulted);
        RuntimeStatusText = OutReason;
        return false;
    }

    FLBBodyShopValidationReport SliceReport;
    const bool bAuthorityEmpty = BuildAuthority->GetPlacedCells().IsEmpty()
        && BuildAuthority->GetConnections().IsEmpty();
    if (bAuthorityEmpty && !BuildAuthority->BuildApprovedUnderbodySliceLayout(OutReason))
    {
        RuntimeStage = ELBBodyShopRuntimeStage::Faulted;
        RuntimeStatusText = OutReason;
        return false;
    }
    if (!BuildAuthority->ValidateUnderbodySlice(SliceReport))
    {
        OutReason = FString::Join(SliceReport.Errors, TEXT(" | "));
        RuntimeStage = ELBBodyShopRuntimeStage::Faulted;
        RuntimeStatusText = OutReason;
        return false;
    }
    if (!ValidateRequiredRobotBindings(OutReason) || !SpawnConfiguredRobots(OutReason))
    {
        RuntimeStage = ELBBodyShopRuntimeStage::Faulted;
        RuntimeStatusText = OutReason;
        return false;
    }

    bRuntimeInitialised = true;
    SetSimulationAndArticulationRunning(false);
    NextWIPSerial = 1;
    NextGenealogySequence = 1;
    ResetRuntimeWIP();
    EnterStage(ELBBodyShopRuntimeStage::Ready);
    RefreshRuntimeCellStates();
    RefreshRobotPoses();
    RefreshPilotPresentation();
    OutReason = RuntimeStatusText;
    return true;
}

bool ALBBodyShopPrototypeRuntime::IsPilotCycleActive() const
{
    return ActiveWIP.Num() > 0;
}

int32 ALBBodyShopPrototypeRuntime::GetVisibleRuntimeWIPPresentationCount() const
{
    const auto IsVisibleMesh = [this](const UStaticMeshComponent* Component)
    {
        return LBBodyShopPrototypeRuntimePrivate::IsPresentationVisibleAndUnhidden(
            this, Component);
    };
    if (ActiveWIP.Num() != 1 || !bWIPPresentationArtValid) return 0;
    const bool bStillageVisible = IsVisibleMesh(PilotStillagePresentation.Get());
    const bool bPanelVisible = IsVisibleMesh(PilotPanelPresentation.Get());
    const bool bSkidVisible = IsVisibleMesh(PilotSkidPresentation.Get());
    const bool bUnderbodyVisible = IsVisibleMesh(PilotUnderbodyPresentation.Get());
    switch (CurrentWIPPresentationSample.Kind)
    {
    case ELBBodyShopWIPPresentationKind::Stillage:
        return bStillageVisible && !bPanelVisible && !bSkidVisible && !bUnderbodyVisible ? 1 : 0;
    case ELBBodyShopWIPPresentationKind::Panel:
        return !bStillageVisible && bPanelVisible && !bSkidVisible && !bUnderbodyVisible ? 1 : 0;
    case ELBBodyShopWIPPresentationKind::SkidUnderbody:
        return !bStillageVisible && !bPanelVisible && bSkidVisible && bUnderbodyVisible ? 1 : 0;
    default:
        return 0;
    }
}

FString ALBBodyShopPrototypeRuntime::GetPilotSkidPresentationMeshPath() const
{
    return LBBodyShopPrototypeRuntimePrivate::PresentationMeshPath(
        PilotSkidPresentation.Get());
}

FString ALBBodyShopPrototypeRuntime::GetPilotStillagePresentationMeshPath() const
{
    return LBBodyShopPrototypeRuntimePrivate::PresentationMeshPath(
        PilotStillagePresentation.Get());
}

FString ALBBodyShopPrototypeRuntime::GetPilotUnderbodyPresentationMeshPath() const
{
    return LBBodyShopPrototypeRuntimePrivate::PresentationMeshPath(
        PilotUnderbodyPresentation.Get());
}

bool ALBBodyShopPrototypeRuntime::IsPilotSkidPresentationVisibleAndUnhidden() const
{
    return LBBodyShopPrototypeRuntimePrivate::IsPresentationVisibleAndUnhidden(
        this, PilotSkidPresentation.Get());
}

bool ALBBodyShopPrototypeRuntime::IsPilotUnderbodyPresentationVisibleAndUnhidden() const
{
    return LBBodyShopPrototypeRuntimePrivate::IsPresentationVisibleAndUnhidden(
        this, PilotUnderbodyPresentation.Get());
}

FVector ALBBodyShopPrototypeRuntime::GetPilotSkidPresentationWorldBoundsMin() const
{
    const FBox Bounds = LBBodyShopPrototypeRuntimePrivate::PresentationWorldBounds(
        PilotSkidPresentation.Get());
    return Bounds.IsValid ? Bounds.Min : FVector::ZeroVector;
}

FVector ALBBodyShopPrototypeRuntime::GetPilotSkidPresentationWorldBoundsMax() const
{
    const FBox Bounds = LBBodyShopPrototypeRuntimePrivate::PresentationWorldBounds(
        PilotSkidPresentation.Get());
    return Bounds.IsValid ? Bounds.Max : FVector::ZeroVector;
}

FVector ALBBodyShopPrototypeRuntime::GetPilotUnderbodyPresentationWorldBoundsMin() const
{
    const FBox Bounds = LBBodyShopPrototypeRuntimePrivate::PresentationWorldBounds(
        PilotUnderbodyPresentation.Get());
    return Bounds.IsValid ? Bounds.Min : FVector::ZeroVector;
}

FVector ALBBodyShopPrototypeRuntime::GetPilotUnderbodyPresentationWorldBoundsMax() const
{
    const FBox Bounds = LBBodyShopPrototypeRuntimePrivate::PresentationWorldBounds(
        PilotUnderbodyPresentation.Get());
    return Bounds.IsValid ? Bounds.Max : FVector::ZeroVector;
}

bool ALBBodyShopPrototypeRuntime::IsSkidUnderbodyPresentationAlignedInWeldFixture() const
{
    using namespace LBBodyShopPrototypeRuntimePrivate;
    if (RuntimeStage != ELBBodyShopRuntimeStage::WeldingUnderbody
        || CurrentWIPPresentationSample.Kind != ELBBodyShopWIPPresentationKind::SkidUnderbody
        || !IsPilotSkidPresentationVisibleAndUnhidden()
        || !IsPilotUnderbodyPresentationVisibleAndUnhidden())
    {
        return false;
    }

    const ALBBodyShopCellActor* Fixture = FindCellByDefinition(
        LBBodyShopPrototypeIds::UnderbodyFixture);
    if (!Fixture) return false;
    const FBox SkidBounds = PresentationBoundsRelativeTo(PilotSkidPresentation.Get(),
        Fixture->GetActorTransform());
    const FBox UnderbodyBounds = PresentationBoundsRelativeTo(
        PilotUnderbodyPresentation.Get(), Fixture->GetActorTransform());
    if (!SkidBounds.IsValid || !UnderbodyBounds.IsValid) return false;

    const FVector Footprint = Fixture->GetDefinition().FootprintCm;
    const FVector Half = Footprint * 0.5f;
    constexpr float ToleranceCm = 0.1f;
    const auto IsInsideFixture = [&Half, &Footprint, ToleranceCm](const FBox& Bounds)
    {
        return Bounds.Min.X >= -Half.X - ToleranceCm
            && Bounds.Max.X <= Half.X + ToleranceCm
            && Bounds.Min.Y >= -Half.Y - ToleranceCm
            && Bounds.Max.Y <= Half.Y + ToleranceCm
            && Bounds.Min.Z >= PoweredRollerTopCm - ToleranceCm
            && Bounds.Max.Z <= Footprint.Z + ToleranceCm;
    };
    return IsInsideFixture(SkidBounds) && IsInsideFixture(UnderbodyBounds)
        && SkidBounds.Min.Z > PoweredRollerTopCm
        && UnderbodyBounds.Min.Z > SkidBounds.Min.Z;
}

bool ALBBodyShopPrototypeRuntime::WasPilotSkidPresentationRecentlyRendered(
    const float ToleranceSeconds) const
{
    const UWorld* World = GetWorld();
    const float LastOnScreenTime = GetPilotSkidLastRenderTimeOnScreenSeconds();
    const float WorldTime = World ? World->GetTimeSeconds() : 0.0f;
    return FMath::IsFinite(ToleranceSeconds) && ToleranceSeconds >= 0.0f
        && World && IsPilotSkidPresentationVisibleAndUnhidden()
        && LastOnScreenTime > 0.0f && WorldTime >= LastOnScreenTime
        && WorldTime - LastOnScreenTime <= ToleranceSeconds;
}

bool ALBBodyShopPrototypeRuntime::WasPilotUnderbodyPresentationRecentlyRendered(
    const float ToleranceSeconds) const
{
    const UWorld* World = GetWorld();
    const float LastOnScreenTime = GetPilotUnderbodyLastRenderTimeOnScreenSeconds();
    const float WorldTime = World ? World->GetTimeSeconds() : 0.0f;
    return FMath::IsFinite(ToleranceSeconds) && ToleranceSeconds >= 0.0f
        && World && IsPilotUnderbodyPresentationVisibleAndUnhidden()
        && LastOnScreenTime > 0.0f && WorldTime >= LastOnScreenTime
        && WorldTime - LastOnScreenTime <= ToleranceSeconds;
}

bool ALBBodyShopPrototypeRuntime::WasSkidUnderbodyPresentationRecentlyRendered(
    const float ToleranceSeconds) const
{
    return RuntimeStage == ELBBodyShopRuntimeStage::WeldingUnderbody
        && CurrentWIPPresentationSample.Kind == ELBBodyShopWIPPresentationKind::SkidUnderbody
        && WasPilotSkidPresentationRecentlyRendered(ToleranceSeconds)
        && WasPilotUnderbodyPresentationRecentlyRendered(ToleranceSeconds);
}

float ALBBodyShopPrototypeRuntime::GetPilotSkidLastRenderTimeOnScreenSeconds() const
{
    return PilotSkidPresentation
        ? PilotSkidPresentation->GetLastRenderTimeOnScreen() : 0.0f;
}

float ALBBodyShopPrototypeRuntime::GetPilotUnderbodyLastRenderTimeOnScreenSeconds() const
{
    return PilotUnderbodyPresentation
        ? PilotUnderbodyPresentation->GetLastRenderTimeOnScreen() : 0.0f;
}

FLBBodyShopWIPSaveState* ALBBodyShopPrototypeRuntime::GetPilotWIP()
{
    return ActiveWIP.Num() == 1 ? &ActiveWIP[0] : nullptr;
}

const FLBBodyShopWIPSaveState* ALBBodyShopPrototypeRuntime::GetPilotWIP() const
{
    return ActiveWIP.Num() == 1 ? &ActiveWIP[0] : nullptr;
}

void ALBBodyShopPrototypeRuntime::ResetRuntimeWIP()
{
    ActiveWIP.Reset();
    StageElapsedSeconds = 0.0f;
    HidePilotPresentation();
}

void ALBBodyShopPrototypeRuntime::SeedPilotStillage()
{
    ALBBodyShopCellActor* Dock = FindCellByDefinition(LBBodyShopPrototypeIds::FullStillageDock);
    if (!Dock) return;
    FLBBodyShopWIPSaveState& Unit = ActiveWIP.AddDefaulted_GetRef();
    Unit.UnitId = FName(*FString::Printf(TEXT("BODYSHOP-WIP-%03d"), NextWIPSerial++));
    Unit.MaterialId = LBBodyShopMaterialIds::PressedPanelStillage;
    Unit.CurrentCellId = Dock->GetCellId();
    Unit.SourceStillageId = LBBodyShopPrototypeRuntimePrivate::PilotSourceStillageId;
    Unit.SkidId = NAME_None;
    Unit.GenealogySequence = NextGenealogySequence++;
    Unit.Quality = ELBBodyShopQualityResult::Pending;
}

bool ALBBodyShopPrototypeRuntime::StartPilotCycle(FString& OutReason)
{
    OutReason.Reset();
    if (!bRuntimeInitialised)
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE SLICE HAS NOT BEEN BUILT AND COMMISSIONED");
        return false;
    }
    if (IsPilotCycleActive())
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE ALREADY HAS A PILOT UNIT; CLEAR THE HELD UNIT FIRST");
        return false;
    }
    SetSimulationAndArticulationRunning(false);
    if (!bPilotStillageAvailable)
    {
        SetSimulationAndArticulationRunning(false);
        EnterStage(ELBBodyShopRuntimeStage::AwaitingPanelStillage);
        RefreshRuntimeCellStates();
        OutReason = RuntimeStatusText;
        return false;
    }

    SeedPilotStillage();
    if (!GetPilotWIP())
    {
        OutReason = TEXT("BODY SHOP PILOT STILLAGE COULD NOT BE SEEDED");
        RuntimeStage = ELBBodyShopRuntimeStage::Faulted;
        RuntimeStatusText = OutReason;
        return false;
    }
    SetSimulationAndArticulationRunning(true);
    EnterStage(ELBBodyShopRuntimeStage::TransferringStillage);
    RefreshRuntimeCellStates();
    RefreshRobotPoses();
    RefreshPilotPresentation();
    OutReason = RuntimeStatusText;
    return true;
}

bool ALBBodyShopPrototypeRuntime::SetSimulationRunning(const bool bInRunning, FString& OutReason)
{
    OutReason.Reset();
    if (!bRuntimeInitialised)
    {
        SetSimulationAndArticulationRunning(false);
        OutReason = TEXT("BODY SHOP PROTOTYPE SLICE HAS NOT BEEN INITIALISED");
        return false;
    }
    if (bInRunning && (!GetPilotWIP() || !IsActiveFlowStage(RuntimeStage)))
    {
        SetSimulationAndArticulationRunning(false);
        OutReason = TEXT("BODY SHOP PROTOTYPE HAS NO RUNNABLE PILOT PROCESS");
        return false;
    }
    SetSimulationAndArticulationRunning(bInRunning);
    OutReason = bSimulationRunning ? TEXT("BODY SHOP PILOT CYCLE RUNNING")
        : TEXT("BODY SHOP PILOT CYCLE PAUSED");
    return true;
}

void ALBBodyShopPrototypeRuntime::SetPilotStillageAvailable(const bool bInAvailable)
{
    bPilotStillageAvailable = bInAvailable;
    if (!bRuntimeInitialised || IsPilotCycleActive()) return;
    SetSimulationAndArticulationRunning(false);
    EnterStage(bPilotStillageAvailable ? ELBBodyShopRuntimeStage::Ready
        : ELBBodyShopRuntimeStage::AwaitingPanelStillage);
    RefreshRuntimeCellStates();
    RefreshRobotPoses();
}

void ALBBodyShopPrototypeRuntime::SetOutputBufferBlockedForValidation(const bool bInBlocked)
{
    bOutputBufferBlockedForValidation = bInBlocked;
    if (RuntimeStage != ELBBodyShopRuntimeStage::OutputBlocked || bInBlocked) return;
    FLBBodyShopWIPSaveState* Unit = GetPilotWIP();
    if (!Unit || Unit->Quality != ELBBodyShopQualityResult::Pass) return;
    TransferPilotUnitToDefinition(LBBodyShopPrototypeIds::OutputBuffer);
    SetSimulationAndArticulationRunning(false);
    EnterStage(ELBBodyShopRuntimeStage::Complete);
    RefreshRuntimeCellStates();
    RefreshRobotPoses();
    RefreshPilotPresentation();
}

void ALBBodyShopPrototypeRuntime::SetNextVisionResultForValidation(const bool bInPass)
{
    bNextVisionPassForValidation = bInPass;
}

bool ALBBodyShopPrototypeRuntime::ReleaseHeldPilotUnit(FString& OutReason)
{
    OutReason.Reset();
    if (!GetPilotWIP())
    {
        OutReason = TEXT("BODY SHOP PROTOTYPE HAS NO HELD PILOT UNIT TO CLEAR");
        return false;
    }
    if (RuntimeStage != ELBBodyShopRuntimeStage::Complete
        && RuntimeStage != ELBBodyShopRuntimeStage::QualityHold)
    {
        OutReason = TEXT("BODY SHOP PILOT UNIT CAN ONLY BE CLEARED FROM OUTPUT OR QUALITY HOLD");
        return false;
    }
    SetSimulationAndArticulationRunning(false);
    ResetRuntimeWIP();
    EnterStage(bPilotStillageAvailable ? ELBBodyShopRuntimeStage::Ready
        : ELBBodyShopRuntimeStage::AwaitingPanelStillage);
    RefreshRuntimeCellStates();
    RefreshRobotPoses();
    RefreshPilotPresentation();
    OutReason = RuntimeStatusText;
    return true;
}

bool ALBBodyShopPrototypeRuntime::ClearHeldPilotUnitForValidation(FString& OutReason)
{
    return ReleaseHeldPilotUnit(OutReason);
}

bool ALBBodyShopPrototypeRuntime::IsActiveFlowStage(const ELBBodyShopRuntimeStage InStage)
{
    return InStage == ELBBodyShopRuntimeStage::TransferringStillage
        || InStage == ELBBodyShopRuntimeStage::PresentingPanel
        || InStage == ELBBodyShopRuntimeStage::WeldingUnderbody
        || InStage == ELBBodyShopRuntimeStage::ConveyingSkid
        || InStage == ELBBodyShopRuntimeStage::Inspecting;
}

float ALBBodyShopPrototypeRuntime::GetCurrentStageDurationSeconds() const
{
    if (RuntimeStage == ELBBodyShopRuntimeStage::TransferringStillage)
        return LBBodyShopPrototypeRuntimePrivate::StillageTransferSeconds;
    FName DefinitionId = NAME_None;
    switch (RuntimeStage)
    {
    case ELBBodyShopRuntimeStage::PresentingPanel:
        DefinitionId = LBBodyShopPrototypeIds::PanelPresentation;
        break;
    case ELBBodyShopRuntimeStage::WeldingUnderbody:
        DefinitionId = LBBodyShopPrototypeIds::UnderbodyFixture;
        break;
    case ELBBodyShopRuntimeStage::ConveyingSkid:
        DefinitionId = LBBodyShopPrototypeIds::StraightSkidConveyor;
        break;
    case ELBBodyShopRuntimeStage::Inspecting:
        DefinitionId = LBBodyShopPrototypeIds::BasicVisionGate;
        break;
    default:
        return 0.0f;
    }
    const ALBBodyShopCellActor* Cell = FindCellByDefinition(DefinitionId);
    return Cell ? FMath::Max(0.01f, Cell->GetDefinition().CycleSeconds) : 1.0f;
}

float ALBBodyShopPrototypeRuntime::GetCurrentStageProgress01() const
{
    const float Duration = GetCurrentStageDurationSeconds();
    return Duration > KINDA_SMALL_NUMBER ? FMath::Clamp(StageElapsedSeconds / Duration, 0.0f, 1.0f)
        : (IsActiveFlowStage(RuntimeStage) ? 0.0f : 1.0f);
}

void ALBBodyShopPrototypeRuntime::EnterStage(const ELBBodyShopRuntimeStage InStage,
    const float InElapsedSeconds)
{
    RuntimeStage = InStage;
    StageElapsedSeconds = FMath::Max(0.0f, InElapsedSeconds);
    RuntimeStatusText = LBBodyShopPrototypeRuntimePrivate::StageStatus(RuntimeStage);
}

void ALBBodyShopPrototypeRuntime::TransferPilotUnitToDefinition(const FName TargetDefinitionId)
{
    FLBBodyShopWIPSaveState* Unit = GetPilotWIP();
    ALBBodyShopCellActor* Target = FindCellByDefinition(TargetDefinitionId);
    if (!Unit || !Target) return;
    Unit->CurrentCellId = Target->GetCellId();
}

void ALBBodyShopPrototypeRuntime::CompleteVisionInspection()
{
    FLBBodyShopWIPSaveState* Unit = GetPilotWIP();
    if (!Unit) return;
    if (Unit->Quality == ELBBodyShopQualityResult::Pending)
    {
        Unit->Quality = bNextVisionPassForValidation ? ELBBodyShopQualityResult::Pass
            : ELBBodyShopQualityResult::Fail;
        bNextVisionPassForValidation = true;
    }
    if (Unit->Quality == ELBBodyShopQualityResult::Fail)
    {
        SetSimulationAndArticulationRunning(false);
        EnterStage(ELBBodyShopRuntimeStage::QualityHold);
        return;
    }
    if (bOutputBufferBlockedForValidation)
    {
        SetSimulationAndArticulationRunning(false);
        EnterStage(ELBBodyShopRuntimeStage::OutputBlocked);
        return;
    }
    TransferPilotUnitToDefinition(LBBodyShopPrototypeIds::OutputBuffer);
    SetSimulationAndArticulationRunning(false);
    EnterStage(ELBBodyShopRuntimeStage::Complete);
}

void ALBBodyShopPrototypeRuntime::AdvanceSimulation(const float DeltaSeconds)
{
    if (!GetPilotWIP() || !IsActiveFlowStage(RuntimeStage)) return;
    float RemainingSeconds = FMath::Max(0.0f, DeltaSeconds);
    for (int32 TransitionSafety = 0; TransitionSafety < 8 && bSimulationRunning
        && IsActiveFlowStage(RuntimeStage); ++TransitionSafety)
    {
        const float Duration = GetCurrentStageDurationSeconds();
        const float RemainingInStage = FMath::Max(0.0f, Duration - StageElapsedSeconds);
        if (RemainingSeconds < RemainingInStage)
        {
            StageElapsedSeconds += RemainingSeconds;
            break;
        }
        StageElapsedSeconds = Duration;
        RemainingSeconds -= RemainingInStage;
        switch (RuntimeStage)
        {
        case ELBBodyShopRuntimeStage::TransferringStillage:
            TransferPilotUnitToDefinition(LBBodyShopPrototypeIds::PanelPresentation);
            EnterStage(ELBBodyShopRuntimeStage::PresentingPanel);
            break;
        case ELBBodyShopRuntimeStage::PresentingPanel:
            if (FLBBodyShopWIPSaveState* Unit = GetPilotWIP())
            {
                Unit->MaterialId = LBBodyShopMaterialIds::Underbody;
                Unit->SkidId = LBBodyShopPrototypeRuntimePrivate::PilotSkidId;
            }
            TransferPilotUnitToDefinition(LBBodyShopPrototypeIds::UnderbodyFixture);
            EnterStage(ELBBodyShopRuntimeStage::WeldingUnderbody);
            break;
        case ELBBodyShopRuntimeStage::WeldingUnderbody:
            TransferPilotUnitToDefinition(LBBodyShopPrototypeIds::StraightSkidConveyor);
            EnterStage(ELBBodyShopRuntimeStage::ConveyingSkid);
            break;
        case ELBBodyShopRuntimeStage::ConveyingSkid:
            TransferPilotUnitToDefinition(LBBodyShopPrototypeIds::BasicVisionGate);
            EnterStage(ELBBodyShopRuntimeStage::Inspecting);
            break;
        case ELBBodyShopRuntimeStage::Inspecting:
            CompleteVisionInspection();
            break;
        default:
            return;
        }
        if (RemainingSeconds <= KINDA_SMALL_NUMBER) break;
    }
}

void ALBBodyShopPrototypeRuntime::RefreshRuntimeCellStates()
{
    if (!bRuntimeInitialised || !BuildAuthority) return;
    const FLBBodyShopWIPSaveState* Unit = GetPilotWIP();
    const TArray<FName> Definitions = FLBBodyShopDefinitionRegistry::GetApprovedUnderbodySliceDefinitionIds();
    for (const FName DefinitionId : Definitions)
    {
        ALBBodyShopCellActor* Cell = FindCellByDefinition(DefinitionId);
        if (!Cell) continue;
        ELBBodyShopCellState State = Cell->IsCommissioned() ? ELBBodyShopCellState::Idle
            : ELBBodyShopCellState::Constructed;
        float Progress = 0.0f;
        TArray<FName> Queue;
        FName ActiveId = NAME_None;
        if (!Unit)
        {
            if (DefinitionId == LBBodyShopPrototypeIds::FullStillageDock
                && RuntimeStage == ELBBodyShopRuntimeStage::AwaitingPanelStillage)
            {
                State = ELBBodyShopCellState::Starved;
            }
        }
        else if (Unit->CurrentCellId == Cell->GetCellId())
        {
            if (RuntimeStage == ELBBodyShopRuntimeStage::Complete
                && DefinitionId == LBBodyShopPrototypeIds::OutputBuffer)
            {
                Queue.Add(Unit->UnitId);
            }
            else
            {
                ActiveId = Unit->UnitId;
                Progress = GetCurrentStageProgress01();
                State = RuntimeStage == ELBBodyShopRuntimeStage::OutputBlocked
                    ? ELBBodyShopCellState::Blocked
                    : RuntimeStage == ELBBodyShopRuntimeStage::QualityHold
                        ? ELBBodyShopCellState::Faulted : ELBBodyShopCellState::Running;
            }
        }
        Cell->SetRuntimeState(State, Progress, Queue, ActiveId);
    }
}

void ALBBodyShopPrototypeRuntime::RefreshRobotPoses()
{
    const bool bSnapStoppedPose = !bSimulationRunning && !IsActiveFlowStage(RuntimeStage);
    for (ALBBodyShopRobotActor* Robot : SpawnedRobots)
    {
        if (!IsValid(Robot) || !Robot->IsConfiguredForAuthoredSlot()) continue;
        ELBBodyShopRobotPose Pose = ELBBodyShopRobotPose::Home;
        const ELBBodyShopRobotRole RobotRole = Robot->GetSlotId() == TEXT("ROBOT_HND_01")
            ? ELBBodyShopRobotRole::PanelHandling : ELBBodyShopRobotRole::SpotWelding;
        switch (RuntimeStage)
        {
        case ELBBodyShopRuntimeStage::TransferringStillage:
            Pose = RobotRole == ELBBodyShopRobotRole::PanelHandling
                ? ELBBodyShopRobotPose::Acquire : ELBBodyShopRobotPose::Home;
            break;
        case ELBBodyShopRuntimeStage::PresentingPanel:
            Pose = RobotRole == ELBBodyShopRobotRole::PanelHandling
                ? ELBBodyShopRobotPose::Process : ELBBodyShopRobotPose::Retract;
            break;
        case ELBBodyShopRuntimeStage::WeldingUnderbody:
            Pose = RobotRole == ELBBodyShopRobotRole::SpotWelding
                ? ELBBodyShopRobotPose::Process : ELBBodyShopRobotPose::Retract;
            break;
        case ELBBodyShopRuntimeStage::QualityHold:
        case ELBBodyShopRuntimeStage::Faulted:
            Pose = ELBBodyShopRobotPose::FaultSafe;
            break;
        case ELBBodyShopRuntimeStage::ConveyingSkid:
        case ELBBodyShopRuntimeStage::Inspecting:
        case ELBBodyShopRuntimeStage::OutputBlocked:
            Pose = ELBBodyShopRobotPose::Retract;
            break;
        default:
            break;
        }
        Robot->SetAuthoredPose(Pose, bSnapStoppedPose);
        Robot->SetArticulationRunning(bSimulationRunning);
    }
}

void ALBBodyShopPrototypeRuntime::RefreshPilotPresentation()
{
    HidePilotPresentation();
    if (!GetPilotWIP() || !bWIPPresentationArtValid) return;

    FTransform StillageDock;
    FTransform PanelPresentation;
    FTransform UnderbodyFixture;
    FTransform StraightConveyor;
    FTransform VisionGate;
    FTransform OutputBuffer;
    FString AnchorFailure;
    if (!TryGetPilotPresentationAnchors(StillageDock, PanelPresentation, UnderbodyFixture,
        StraightConveyor, VisionGate, OutputBuffer, AnchorFailure))
    {
        WIPPresentationFailureReason = AnchorFailure;
        return;
    }
    WIPPresentationFailureReason.Reset();

    CurrentWIPPresentationSample = SampleWIPPresentation(RuntimeStage,
        GetCurrentStageProgress01(), StillageDock, PanelPresentation, UnderbodyFixture,
        StraightConveyor, VisionGate, OutputBuffer);
    switch (CurrentWIPPresentationSample.Kind)
    {
    case ELBBodyShopWIPPresentationKind::Stillage:
        PilotStillagePresentation->SetWorldTransform(
            CurrentWIPPresentationSample.WorldTransform);
        PilotStillagePresentation->SetVisibility(true, true);
        break;
    case ELBBodyShopWIPPresentationKind::Panel:
        PilotPanelPresentation->SetWorldTransform(CurrentWIPPresentationSample.WorldTransform);
        PilotPanelPresentation->SetVisibility(true, true);
        break;
    case ELBBodyShopWIPPresentationKind::SkidUnderbody:
        PilotSkidPresentation->SetWorldTransform(CurrentWIPPresentationSample.WorldTransform);
        PilotUnderbodyPresentation->SetWorldTransform(
            LBBodyShopPrototypeRuntimePrivate::WithLocalOffset(
                CurrentWIPPresentationSample.WorldTransform,
                FVector(0.0f, 0.0f, LBBodyShopPrototypeRuntimePrivate::WorkpieceHeightCm)));
        PilotSkidPresentation->SetVisibility(true, true);
        PilotUnderbodyPresentation->SetVisibility(true, true);
        break;
    default:
        break;
    }
}

FName ALBBodyShopPrototypeRuntime::GetDefinitionIdForCellId(
    const FLBBodyShopExperimentalSaveState& InState, const FName CellId)
{
    const FLBBodyShopPlacedCellSaveState* Found = InState.Cells.FindByPredicate(
        [CellId](const FLBBodyShopPlacedCellSaveState& Cell)
        {
            return Cell.CellId == CellId;
        });
    return Found ? Found->DefinitionId : NAME_None;
}

ELBBodyShopRuntimeStage ALBBodyShopPrototypeRuntime::GetStageForWIPLocation(
    const FName DefinitionId, const ELBBodyShopQualityResult Quality,
    const ELBBodyShopCellState CellState)
{
    if (DefinitionId == LBBodyShopPrototypeIds::FullStillageDock)
        return ELBBodyShopRuntimeStage::TransferringStillage;
    if (DefinitionId == LBBodyShopPrototypeIds::PanelPresentation)
        return ELBBodyShopRuntimeStage::PresentingPanel;
    if (DefinitionId == LBBodyShopPrototypeIds::UnderbodyFixture)
        return ELBBodyShopRuntimeStage::WeldingUnderbody;
    if (DefinitionId == LBBodyShopPrototypeIds::StraightSkidConveyor)
        return ELBBodyShopRuntimeStage::ConveyingSkid;
    if (DefinitionId == LBBodyShopPrototypeIds::BasicVisionGate)
    {
        if (Quality == ELBBodyShopQualityResult::Fail)
            return ELBBodyShopRuntimeStage::QualityHold;
        return CellState == ELBBodyShopCellState::Blocked
            ? ELBBodyShopRuntimeStage::OutputBlocked : ELBBodyShopRuntimeStage::Inspecting;
    }
    if (DefinitionId == LBBodyShopPrototypeIds::OutputBuffer)
        return ELBBodyShopRuntimeStage::Complete;
    return ELBBodyShopRuntimeStage::Faulted;
}

bool ALBBodyShopPrototypeRuntime::ValidateApprovedSliceTopology(
    const FLBBodyShopExperimentalSaveState& InState, FString& OutReason)
{
    OutReason.Reset();
    const TArray<FName> Required = FLBBodyShopDefinitionRegistry::GetApprovedUnderbodySliceDefinitionIds();
    if (InState.Cells.Num() != Required.Num())
    {
        OutReason = TEXT("BODY SHOP RUNTIME SAVE MUST CONTAIN EXACTLY THE SIX APPROVED PILOT CELLS");
        return false;
    }
    TMap<FName, const FLBBodyShopPlacedCellSaveState*> CellsByDefinition;
    for (const FLBBodyShopPlacedCellSaveState& Cell : InState.Cells)
    {
        if (CellsByDefinition.Contains(Cell.DefinitionId))
        {
            OutReason = TEXT("BODY SHOP RUNTIME SAVE DUPLICATES A PILOT CELL DEFINITION");
            return false;
        }
        CellsByDefinition.Add(Cell.DefinitionId, &Cell);
    }
    for (const FName DefinitionId : Required)
    {
        const FLBBodyShopPlacedCellSaveState** Found = CellsByDefinition.Find(DefinitionId);
        if (!Found || !*Found || !(*Found)->bCommissioned)
        {
            OutReason = TEXT("BODY SHOP RUNTIME SAVE HAS AN UNCOMMISSIONED OR MISSING PILOT CELL");
            return false;
        }
    }
    for (const FLBBodyShopPilotRobotBinding& Binding : GetRequiredPilotRobotBindings())
    {
        const FLBBodyShopPlacedCellSaveState** Found = CellsByDefinition.Find(
            Binding.CellDefinitionId);
        const FLBBodyShopPlacedCellSaveState* Cell = Found ? *Found : nullptr;
        const FLBBodyShopRobotAssignment* Assignment = Cell
            ? Cell->RobotAssignments.FindByPredicate([&Binding](const FLBBodyShopRobotAssignment& Candidate)
                { return Candidate.SlotId == Binding.SlotId; }) : nullptr;
        if (!Assignment || Assignment->Role != Binding.Role || Assignment->Tool != Binding.Tool
            || !Assignment->bEnabled || Assignment->Condition01 <= 0.0f)
        {
            OutReason = TEXT("BODY SHOP RUNTIME SAVE HAS LOST AN AUTHORISED PILOT ROBOT BINDING");
            return false;
        }
    }
    struct FRequiredLink
    {
        FName SourceDefinition;
        FName SourcePort;
        FName TargetDefinition;
        FName TargetPort;
    };
    const FRequiredLink Links[] = {
        {LBBodyShopPrototypeIds::FullStillageDock, LBBodyShopPrototypeIds::StillageOut,
            LBBodyShopPrototypeIds::PanelPresentation, LBBodyShopPrototypeIds::StillageIn},
        {LBBodyShopPrototypeIds::PanelPresentation, LBBodyShopPrototypeIds::PanelOut,
            LBBodyShopPrototypeIds::UnderbodyFixture, LBBodyShopPrototypeIds::PanelIn},
        {LBBodyShopPrototypeIds::UnderbodyFixture, LBBodyShopPrototypeIds::SkidOut,
            LBBodyShopPrototypeIds::StraightSkidConveyor, LBBodyShopPrototypeIds::SkidIn},
        {LBBodyShopPrototypeIds::StraightSkidConveyor, LBBodyShopPrototypeIds::SkidOut,
            LBBodyShopPrototypeIds::BasicVisionGate, LBBodyShopPrototypeIds::BodyIn},
        {LBBodyShopPrototypeIds::BasicVisionGate, LBBodyShopPrototypeIds::BodyOut,
            LBBodyShopPrototypeIds::OutputBuffer, LBBodyShopPrototypeIds::BodyIn}
    };
    for (const FRequiredLink& Link : Links)
    {
        const FLBBodyShopPlacedCellSaveState** Source = CellsByDefinition.Find(
            Link.SourceDefinition);
        const FLBBodyShopPlacedCellSaveState** Target = CellsByDefinition.Find(
            Link.TargetDefinition);
        const bool bFound = Source && Target && *Source && *Target
            && InState.Connections.ContainsByPredicate([&Link, Source, Target]
                (const FLBBodyShopConnectionSaveState& Connection)
                {
                    return Connection.SourceCellId == (*Source)->CellId
                        && Connection.SourcePortId == Link.SourcePort
                        && Connection.TargetCellId == (*Target)->CellId
                        && Connection.TargetPortId == Link.TargetPort;
                });
        if (!bFound)
        {
            OutReason = TEXT("BODY SHOP RUNTIME SAVE IS MISSING AN APPROVED PILOT PORT CONNECTION");
            return false;
        }
    }
    return true;
}

bool ALBBodyShopPrototypeRuntime::ValidateRuntimeSaveState(
    const FLBBodyShopExperimentalSaveState& InState, FString& OutReason)
{
    OutReason.Reset();
    if (!FLBBodyShopDefinitionRegistry::ValidateExperimentalSaveState(InState, OutReason))
        return false;
    if (!ValidateApprovedSliceTopology(InState, OutReason)) return false;
    if (InState.WIP.Num() > 1)
    {
        OutReason = TEXT("BODY SHOP PILOT RUNTIME SUPPORTS EXACTLY ONE WIP UNIT IN V001");
        return false;
    }
    int64 MaximumGenealogy = 0;
    for (const FLBBodyShopWIPSaveState& Unit : InState.WIP)
    {
        const FName DefinitionId = GetDefinitionIdForCellId(InState, Unit.CurrentCellId);
        if (Unit.MaterialId != LBBodyShopMaterialIds::PressedPanelStillage
            && Unit.MaterialId != LBBodyShopMaterialIds::Underbody)
        {
            OutReason = TEXT("BODY SHOP PILOT SAVE HAS AN UNAPPROVED WIP MATERIAL");
            return false;
        }
        if (Unit.MaterialId == LBBodyShopMaterialIds::PressedPanelStillage
            && (Unit.SourceStillageId.IsNone() || (DefinitionId != LBBodyShopPrototypeIds::FullStillageDock
                && DefinitionId != LBBodyShopPrototypeIds::PanelPresentation)))
        {
            OutReason = TEXT("BODY SHOP PILOT PANEL STILLAGE IS OUTSIDE ITS APPROVED HAND-OFF");
            return false;
        }
        if (Unit.MaterialId == LBBodyShopMaterialIds::Underbody
            && (Unit.SkidId.IsNone() || DefinitionId == LBBodyShopPrototypeIds::FullStillageDock
                || DefinitionId == LBBodyShopPrototypeIds::PanelPresentation))
        {
            OutReason = TEXT("BODY SHOP PILOT UNDERBODY MUST REMAIN ON ITS APPROVED SKID FLOW");
            return false;
        }
        if (Unit.Quality == ELBBodyShopQualityResult::Fail
            && DefinitionId != LBBodyShopPrototypeIds::BasicVisionGate)
        {
            OutReason = TEXT("BODY SHOP V001 QUALITY FAILURES MUST REMAIN AT THE VISION HOLD");
            return false;
        }
        MaximumGenealogy = FMath::Max(MaximumGenealogy, Unit.GenealogySequence);
    }
    if (InState.NextGenealogySequence <= MaximumGenealogy)
    {
        OutReason = TEXT("BODY SHOP PILOT SAVE WOULD REUSE A WIP GENEALOGY SEQUENCE");
        return false;
    }
    return true;
}

bool ALBBodyShopPrototypeRuntime::CaptureExperimentalSaveState(
    FLBBodyShopExperimentalSaveState& OutState, FString& OutReason)
{
    OutReason.Reset();
    if (!bRuntimeInitialised || !IsAuthorityReady(OutReason)) return false;
    RefreshRuntimeCellStates();
    OutState = BuildAuthority->CaptureTopologySaveState();
    OutState.Version = 1;
    OutState.WIP = ActiveWIP;
    OutState.NextWIPSerial = NextWIPSerial;
    OutState.NextGenealogySequence = NextGenealogySequence;
    if (!ValidateRuntimeSaveState(OutState, OutReason)) return false;
    return true;
}

bool ALBBodyShopPrototypeRuntime::RestoreExperimentalSaveState(
    const FLBBodyShopExperimentalSaveState& InState, FString& OutReason)
{
    OutReason.Reset();
    if (!IsAuthorityReady(OutReason) || !ValidateRuntimeSaveState(InState, OutReason)) return false;
    if (!ValidatePilotPresentationArt(OutReason))
    {
        bRuntimeInitialised = false;
        SetSimulationAndArticulationRunning(false);
        EnterStage(ELBBodyShopRuntimeStage::Faulted);
        RuntimeStatusText = OutReason;
        return false;
    }

    FLBBodyShopExperimentalSaveState TopologyOnly = InState;
    TopologyOnly.WIP.Reset();
    for (FLBBodyShopPlacedCellSaveState& Cell : TopologyOnly.Cells)
    {
        Cell.QueuedWIPIds.Reset();
        Cell.ActiveWIPId = NAME_None;
    }
    // From the first mutating restore step onward, both the runtime and every
    // extant/new robot remain paused until an active flow stage is reconstructed.
    SetSimulationAndArticulationRunning(false);
    if (!BuildAuthority->RestoreTopologySaveState(TopologyOnly, OutReason)) return false;

    DestroyRuntimeRobots();
    if (!SpawnConfiguredRobots(OutReason))
    {
        bRuntimeInitialised = false;
        SetSimulationAndArticulationRunning(false);
        EnterStage(ELBBodyShopRuntimeStage::Faulted);
        RuntimeStatusText = OutReason;
        return false;
    }

    ActiveWIP = InState.WIP;
    NextWIPSerial = InState.NextWIPSerial;
    NextGenealogySequence = InState.NextGenealogySequence;
    bRuntimeInitialised = true;
    SetSimulationAndArticulationRunning(false);
    bOutputBufferBlockedForValidation = false;
    bNextVisionPassForValidation = true;
    if (const FLBBodyShopWIPSaveState* Unit = GetPilotWIP())
    {
        const FName DefinitionId = GetDefinitionIdForCellId(InState, Unit->CurrentCellId);
        const FLBBodyShopPlacedCellSaveState* SavedCell = InState.Cells.FindByPredicate(
            [&Unit](const FLBBodyShopPlacedCellSaveState& Cell)
            {
                return Cell.CellId == Unit->CurrentCellId;
            });
        EnterStage(GetStageForWIPLocation(DefinitionId, Unit->Quality,
            SavedCell ? SavedCell->State : ELBBodyShopCellState::Faulted));
        const float Duration = GetCurrentStageDurationSeconds();
        StageElapsedSeconds = SavedCell && Duration > KINDA_SMALL_NUMBER
            ? FMath::Clamp(SavedCell->ProcessProgress01, 0.0f, 1.0f) * Duration : 0.0f;
        bOutputBufferBlockedForValidation = RuntimeStage == ELBBodyShopRuntimeStage::OutputBlocked;
        SetSimulationAndArticulationRunning(IsActiveFlowStage(RuntimeStage));
    }
    else
    {
        EnterStage(bPilotStillageAvailable ? ELBBodyShopRuntimeStage::Ready
            : ELBBodyShopRuntimeStage::AwaitingPanelStillage);
    }
    RefreshRuntimeCellStates();
    RefreshRobotPoses();
    RefreshPilotPresentation();
    OutReason = RuntimeStatusText;
    return true;
}

bool ALBBodyShopPrototypeRuntime::SaveToExperimentalSlot(FString& OutReason)
{
    OutReason.Reset();
    FLBBodyShopExperimentalSaveState State;
    if (!CaptureExperimentalSaveState(State, OutReason)) return false;
    ULBBodyShopExperimentalSaveGame* Save = Cast<ULBBodyShopExperimentalSaveGame>(
        UGameplayStatics::CreateSaveGameObject(ULBBodyShopExperimentalSaveGame::StaticClass()));
    if (!Save)
    {
        OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE OBJECT COULD NOT BE CREATED");
        return false;
    }
    Save->SaveSchemaVersion = ULBBodyShopExperimentalSaveGame::SchemaVersion;
    Save->PrototypeMapId = TEXT("LB_BodyShop_Prototype_v001");
    Save->State = State;
    if (!Save->ValidateForLoad(OutReason)) return false;
    if (!UGameplayStatics::SaveGameToSlot(Save,
        ULBBodyShopExperimentalSaveGame::GetSlotName().ToString(),
        ULBBodyShopExperimentalSaveGame::GetUserIndex()))
    {
        OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE V1 COULD NOT BE WRITTEN");
        return false;
    }
    OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE V1 WRITTEN");
    return true;
}

bool ALBBodyShopPrototypeRuntime::LoadFromExperimentalSlot(FString& OutReason)
{
    OutReason.Reset();
    ULBBodyShopExperimentalSaveGame* Save = Cast<ULBBodyShopExperimentalSaveGame>(
        UGameplayStatics::LoadGameFromSlot(ULBBodyShopExperimentalSaveGame::GetSlotName().ToString(),
            ULBBodyShopExperimentalSaveGame::GetUserIndex()));
    if (!Save)
    {
        OutReason = TEXT("BODY SHOP EXPERIMENTAL SAVE V1 DOES NOT EXIST OR IS NOT READABLE");
        return false;
    }
    if (!Save->ValidateForLoad(OutReason)) return false;
    return RestoreExperimentalSaveState(Save->State, OutReason);
}
