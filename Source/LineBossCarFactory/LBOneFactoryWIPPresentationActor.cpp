#include "LBOneFactoryWIPPresentationActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactoryRuntimeRegistrySubsystem.h"
#include "LBPressShopOverheadPresentationActor.h"
#include "LBVehiclePanelCatalog.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace LBOneFactoryWIPPresentationPrivate
{
    constexpr double OverheadPresentationRediscoverySeconds = 1.0;

    constexpr int32 VisualCount =
        static_cast<int32>(ELBOneFactoryWIPVisual::FinishedCar) + 1;

    const TCHAR* const BatchComponentNames[VisualCount] = {
        TEXT("WIP_Coil"), TEXT("WIP_PanelStack"), TEXT("WIP_BodyInWhite"),
        TEXT("WIP_PrimedBody"), TEXT("WIP_PaintedBody"), TEXT("WIP_FinishedCar")
    };

    constexpr int32 StampedPanelCount = 11;
    const TCHAR* const StampedPanelNames[StampedPanelCount] = {
        TEXT("HOOD_PANEL"), TEXT("ROOF_PANEL"), TEXT("DOOR_FRONT_LEFT"),
        TEXT("DOOR_FRONT_RIGHT"), TEXT("DOOR_REAR_LEFT"), TEXT("DOOR_REAR_RIGHT"),
        TEXT("FENDER_FRONT_LEFT"), TEXT("FENDER_FRONT_RIGHT"),
        TEXT("QUARTER_PANEL_LEFT"), TEXT("QUARTER_PANEL_RIGHT"), TEXT("TAILGATE_PANEL")
    };
    const TCHAR* const StampedPanelMeshPath[StampedPanelCount] = {
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_Hood.SM_LB_C2040_Hood"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_Roof.SM_LB_C2040_Roof"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_FrontDoor_L.SM_LB_C2040_FrontDoor_L"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_FrontDoor_L.SM_LB_C2040_FrontDoor_L"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_RearDoor_L.SM_LB_C2040_RearDoor_L"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_RearDoor_L.SM_LB_C2040_RearDoor_L"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_FrontFender_L.SM_LB_C2040_FrontFender_L"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_FrontFender_L.SM_LB_C2040_FrontFender_L"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_QuarterPanel_L.SM_LB_C2040_QuarterPanel_L"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_QuarterPanel_L.SM_LB_C2040_QuarterPanel_L"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Panels/SM_LB_C2040_Tailgate.SM_LB_C2040_Tailgate")
    };
    const bool StampedPanelMirrored[StampedPanelCount] = {
        false, false, false, true, false, true, false, true, false, true, false
    };
    const FVector StampedPanelOffsets[StampedPanelCount] = {
        {-90.0, -68.0, 82.0}, {0.0, -68.0, 92.0}, {90.0, -68.0, 72.0},
        {-90.0, 68.0, 82.0}, {0.0, 68.0, 92.0}, {90.0, 68.0, 72.0},
        {-90.0, -30.0, 30.0}, {90.0, -30.0, 30.0}, {-90.0, 30.0, 30.0},
        {90.0, 30.0, 30.0}, {0.0, 0.0, 145.0}
    };

    /**
     * Real authored meshes for every family, measured in the editor. The
     * The body stages use the clean-room VehicleWIPNativeKit layer imported by
     * the guarded native lane. The coil and panel stillage keep their existing
     * production presentation authorities. Scale is 1.0 everywhere - these
     * are true-size assets, not primitives.
     *
     *   Engine cylinder coil proxy         181 x 150 x 179  pivot at base
     *   PanelStillage_Runtime_v001         190 x 139 x 116  pivot centred
     *   C2040_UpperStructure (native)      open BIW structure, floor at pivot
     *   C2040_RoofClosures (native)        452 x 191 x 126  floor at pivot
     *   C2040_RollingGear (native)         347 x 184 x 72   floor at pivot
     */
    const TCHAR* const BatchMeshPath[VisualCount] = {
        // The deprecated external coil family is intentionally never cooked.
        // This safe, built-in cylinder is a deliberate WIP proxy and is always
        // present in a packaged Unreal game.
        TEXT("/Engine/BasicShapes/Cylinder.Cylinder"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/PanelStillageRuntime_v001"
             "/SM_LB_PanelStillage_Runtime_v001"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Layers"
             "/SM_LB_C2040_UpperStructure"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Layers"
             "/SM_LB_C2040_RoofClosures"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Layers"
             "/SM_LB_C2040_RoofClosures"),
        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Layers"
             "/SM_LB_C2040_RoofClosures")
    };

    /**
     * Optional material override per family. Null keeps the mesh's authored
     * materials, which is right for every family except the distinct body
     * phases. BIW is an open structure; primed, painted and finished reuse the
     * closed shell with stage-specific solid colours, keeping the route legible
     * even at the factory overview camera distance.
     */
    const TCHAR* const BatchMaterialOverride[VisualCount] = {
        nullptr, nullptr,
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"),
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"),
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"),
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")
    };

    const FLinearColor BatchSolidColours[VisualCount] = {
        FLinearColor::White, FLinearColor::White,
        FLinearColor(0.34f, 0.39f, 0.43f), // bare BIW steel
        FLinearColor(0.09f, 0.12f, 0.14f), // e-coat
        FLinearColor(0.04f, 0.31f, 0.18f), // development paint
        FLinearColor(0.03f, 0.24f, 0.13f)  // finished development car
    };

    /**
     * Local size and lift per family, in centimetres. Engine Cube and Cylinder
     * are 100 cm, so these double as scale factors.
     */
    struct FVisualForm
    {
        FVector Scale;
        double LiftCm;
        FRotator LocalRotation;
    };

    const FVisualForm VisualForms[VisualCount] = {
        // Coil: a true-size horizontal proxy, pivoted on the floor.
        { FVector(1.79, 1.50, 1.81), 0.0, FRotator(90.0f, 0.0f, 0.0f) },
        // Stillage: pivot centred, so lift by half its 116 cm height.
        { FVector(1.0), 58.0, FRotator::ZeroRotator },
        // BIW uses the open upper structure; the primed body is closed after
        // the panel/body marriage. Both authored floors sit at their pivots.
        { FVector(1.0), 0.0, FRotator::ZeroRotator },
        { FVector(1.0), 0.0, FRotator::ZeroRotator },
        // Painted and finished body.
        { FVector(1.0), 0.0, FRotator::ZeroRotator },
        { FVector(1.0), 0.0, FRotator::ZeroRotator }
    };
}

ALBOneFactoryWIPPresentationActor::ALBOneFactoryWIPPresentationActor()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    using namespace LBOneFactoryWIPPresentationPrivate;
    Batches.Reserve(VisualCount);
    for (int32 Index = 0; Index < VisualCount; ++Index)
    {
        UInstancedStaticMeshComponent* Batch =
            CreateDefaultSubobject<UInstancedStaticMeshComponent>(
                FName(BatchComponentNames[Index]));
        Batch->SetupAttachment(SceneRoot);
        Batch->SetMobility(EComponentMobility::Movable);
        Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Batch->SetCollisionResponseToAllChannels(ECR_Ignore);
        Batch->SetGenerateOverlapEvents(false);
        // Moving WIP must never contribute to navigation.
        Batch->SetCanEverAffectNavigation(false);
        Batch->SetReceivesDecals(false);
        Batches.Add(Batch);
    }

    StampedPanelBatches.Reserve(StampedPanelCount);
    for (int32 Index = 0; Index < StampedPanelCount; ++Index)
    {
        UInstancedStaticMeshComponent* Batch =
            CreateDefaultSubobject<UInstancedStaticMeshComponent>(
                FName(*FString::Printf(TEXT("WIP_Stamped_%s"),
                    StampedPanelNames[Index])));
        Batch->SetupAttachment(SceneRoot);
        Batch->SetMobility(EComponentMobility::Movable);
        Batch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Batch->SetCollisionResponseToAllChannels(ECR_Ignore);
        Batch->SetGenerateOverlapEvents(false);
        Batch->SetCanEverAffectNavigation(false);
        Batch->SetReceivesDecals(false);
        const ConstructorHelpers::FObjectFinder<UStaticMesh> PanelMesh(StampedPanelMeshPath[Index]);
        if (PanelMesh.Succeeded())
        {
            Batch->SetStaticMesh(PanelMesh.Object);
        }
        StampedPanelBatches.Add(Batch);
    }

    GearBatch = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("WIP_FinishedCarGear"));
    GearBatch->SetupAttachment(SceneRoot);
    GearBatch->SetMobility(EComponentMobility::Movable);
    GearBatch->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    GearBatch->SetCollisionResponseToAllChannels(ECR_Ignore);
    GearBatch->SetGenerateOverlapEvents(false);
    GearBatch->SetCanEverAffectNavigation(false);
    GearBatch->SetReceivesDecals(false);

    Tags.AddUnique(GetPresentationTag());
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
}

FName ALBOneFactoryWIPPresentationActor::GetPresentationTag()
{
    return FName(TEXT("LB.OneFactory.WIPPresentation"));
}

bool ALBOneFactoryWIPPresentationActor::SupportsVehicleModel(const FName VehicleModelId)
{
    // The current hard references are deliberately Cairnwell-only.  A future
    // programme must bring its own registered WIP presentation authority;
    // silently reusing these meshes would make the factory lie to the player.
    return VehicleModelId == LBCairnwell2040PanelCatalog::GetVehicleModelId();
}

bool ALBOneFactoryWIPPresentationActor::
    IsOverheadPressPresentationAuthoritative(
        const ALBPressShopOverheadPresentationActor* Presentation)
{
    return IsValid(Presentation) && Presentation->IsPresentationEnabled()
        && !Presentation->IsActorBeingDestroyed()
        && !Presentation->IsHidden();
}

bool ALBOneFactoryWIPPresentationActor::
    HasEnabledOverheadPressPresentation(UWorld* World)
{
    using namespace LBOneFactoryWIPPresentationPrivate;
    if (!World) return false;

    ALBPressShopOverheadPresentationActor* Cached =
        CachedOverheadPressPresentation.Get();
    if (IsOverheadPressPresentationAuthoritative(Cached))
    {
        // Enable/disable is deliberately checked every frame so the generic
        // Press WIP returns immediately when the overhead view is switched.
        return true;
    }

    const double WorldSeconds = World->GetTimeSeconds();
    if (WorldSeconds < NextOverheadPresentationDiscoverySeconds)
    {
        return false;
    }
    NextOverheadPresentationDiscoverySeconds =
        WorldSeconds + OverheadPresentationRediscoverySeconds;

    ALBPressShopOverheadPresentationActor* FirstValid =
        IsValid(Cached) && !Cached->IsActorBeingDestroyed() ? Cached : nullptr;
    for (TActorIterator<ALBPressShopOverheadPresentationActor> It(World); It;
        ++It)
    {
        ALBPressShopOverheadPresentationActor* Candidate = *It;
        if (!IsValid(Candidate) || Candidate->IsActorBeingDestroyed()) continue;
        if (!FirstValid) FirstValid = Candidate;
        if (IsOverheadPressPresentationAuthoritative(Candidate))
        {
            CachedOverheadPressPresentation = Candidate;
            return true;
        }
    }
    CachedOverheadPressPresentation = FirstValid;
    return false;
}

ELBOneFactoryWIPVisual ALBOneFactoryWIPPresentationActor::VisualForStage(
    const ELBOneFactoryVehicleStage Stage)
{
    switch (Stage)
    {
    case ELBOneFactoryVehicleStage::InboundCoil:
    case ELBOneFactoryVehicleStage::BlankPreparation:
        return ELBOneFactoryWIPVisual::Coil;

    case ELBOneFactoryVehicleStage::Pressing:
    case ELBOneFactoryVehicleStage::PressPanelInspection:
    case ELBOneFactoryVehicleStage::PressedPanelStillage:
        return ELBOneFactoryWIPVisual::PanelStack;

    case ELBOneFactoryVehicleStage::BodyFraming:
    case ELBOneFactoryVehicleStage::BodyInWhite:
    case ELBOneFactoryVehicleStage::BodyQualityInspection:
        return ELBOneFactoryWIPVisual::BodyInWhite;

    case ELBOneFactoryVehicleStage::Pretreatment:
    case ELBOneFactoryVehicleStage::EDCoat:
        return ELBOneFactoryWIPVisual::PrimedBody;

    case ELBOneFactoryVehicleStage::ColourCoat:
    case ELBOneFactoryVehicleStage::Cure:
    case ELBOneFactoryVehicleStage::PaintQualityInspection:
        return ELBOneFactoryWIPVisual::PaintedBody;

    default:
        return ELBOneFactoryWIPVisual::FinishedCar;
    }
}

bool ALBOneFactoryWIPPresentationActor::ComputeUnitTransform(
    const TArray<FLBOneFactoryRuntimeStationStep>& Route,
    const TMap<FName, FTransform>& StationTransforms,
    ALBOneFactoryRuntimeCoordinator* Coordinator,
    const FLBOneFactoryVehicleUnitState& Unit,
    FTransform& OutTransform) const
{
    using namespace LBOneFactoryWIPPresentationPrivate;

    const FTransform* Station = StationTransforms.Find(Unit.CurrentStationId);
    if (!Station)
    {
        return false;
    }
    const int32 VisualIndex = static_cast<int32>(VisualForStage(Unit.Stage));
    if (VisualIndex < 0 || VisualIndex >= VisualCount)
    {
        return false;
    }
    const FVisualForm& Form = VisualForms[VisualIndex];

    FVector Location = Station->GetLocation();
    FQuat Rotation = Station->GetRotation();

    // At the press train the station transform sits inside the machine body:
    // the v449 train spans +-678 cm across the datum, so a unit standing at
    // the raw station location renders inside the press for most of its
    // cycle. Stand it on the outfeed side instead, clear of the footprint,
    // and let the transfer start from there.
    static const FName PressTrainStation(TEXT("OF_PRESS_TRAIN_001"));
    if (Unit.CurrentStationId == PressTrainStation)
    {
        Location += Rotation.RotateVector(FVector(0.0, 900.0, 0.0));
    }

    FLBOneFactoryRuntimeVehicleStatus Status;
    FString StatusReason;
    if (Coordinator
        && Coordinator->GetVehicleRuntimeStatus(Unit.UnitId, Status,
            StatusReason)
        && !Status.bAwaitingQualityResult
        // A unit at a quality gate holds at the gate: no creep toward the
        // next station during the tail of the inspection cycle, and no
        // rendering at the next station through a rework hold.
        && !Status.bAtQualityGate
        // A completed cycle without a cursor advance is a transfer hold -
        // the target station is occupied - so the unit waits visibly at its
        // own station instead of rendering coincident with the occupant.
        && Status.NormalizedCycleProgress < 1.0f
        && Route.IsValidIndex(Status.StationCursor)
        && Route.IsValidIndex(Status.StationCursor + 1)
        && Route[Status.StationCursor].StationId == Unit.CurrentStationId)
    {
        constexpr float TransferStart = 0.80f;
        if (Status.NormalizedCycleProgress > TransferStart)
        {
            const FLBOneFactoryRuntimeStationStep& NextStep =
                Route[Status.StationCursor + 1];
            FVector NextLocation = NextStep.WorldTransform.GetLocation();
            // Transfers into the press train aim at the same outfeed-side
            // point, so the inbound visual never passes through the train
            // body.
            if (NextStep.StationId == PressTrainStation)
            {
                NextLocation += NextStep.WorldTransform.GetRotation()
                    .RotateVector(FVector(0.0, 900.0, 0.0));
            }
            const float Alpha = FMath::Clamp(
                (Status.NormalizedCycleProgress - TransferStart)
                    / (1.0f - TransferStart), 0.0f, 1.0f);
            // Ease in and out so the transfer starts and stops smoothly.
            const float Smooth = Alpha * Alpha * (3.0f - 2.0f * Alpha);

            const bool bCrossDepartment =
                Route[Status.StationCursor].Department
                    != NextStep.Department;
            FVector Travel = NextLocation - Location;
            if (bCrossDepartment
                && FMath::Abs(NextLocation.X - Location.X) > 600.0
                && FMath::Abs(NextLocation.Y - Location.Y) > 600.0)
            {
                // Cross-department transfers follow the same Manhattan
                // corner as the painted routes and the conveyors, instead
                // of cutting a diagonal through the intervening bays.
                const FVector Corner(NextLocation.X, Location.Y, Location.Z);
                const double LegA = FVector::Dist2D(Location, Corner);
                const double LegB = FVector::Dist2D(Corner, NextLocation);
                const double Travelled = Smooth * (LegA + LegB);
                if (Travelled <= LegA && LegA > 1.0)
                {
                    const FVector Dir =
                        (Corner - Location).GetSafeNormal();
                    Travel = Dir;
                    Location += Dir * Travelled;
                }
                else if (LegB > 1.0)
                {
                    const FVector Dir =
                        (NextLocation - Corner).GetSafeNormal();
                    Travel = Dir;
                    Location = Corner + Dir * (Travelled - LegA);
                }
            }
            else
            {
                Location = FMath::Lerp(Location, NextLocation, Smooth);
            }
            if (!Travel.IsNearlyZero())
            {
                Rotation =
                    FRotationMatrix::MakeFromX(Travel.GetSafeNormal()).ToQuat();
            }
        }
    }

    OutTransform.SetRotation(Rotation * Form.LocalRotation.Quaternion());
    OutTransform.SetScale3D(Form.Scale);
    OutTransform.SetLocation(Location + FVector(0.0, 0.0, Form.LiftCm));
    return true;
}

void ALBOneFactoryWIPPresentationActor::ClearPresentation()
{
    for (UInstancedStaticMeshComponent* Batch : Batches)
    {
        if (Batch)
        {
            Batch->ClearInstances();
        }
    }
    if (GearBatch)
    {
        GearBatch->ClearInstances();
    }
    for (UInstancedStaticMeshComponent* Batch : StampedPanelBatches)
    {
        if (Batch)
        {
            Batch->ClearInstances();
        }
    }
    VisibleUnitCount = 0;
}

void ALBOneFactoryWIPPresentationActor::AddStampedPanelSet(
    const FTransform& StillageTransform)
{
    using namespace LBOneFactoryWIPPresentationPrivate;
    constexpr double DisplayScale = 0.34;
    for (int32 Index = 0; Index < StampedPanelCount; ++Index)
    {
        UInstancedStaticMeshComponent* Batch = StampedPanelBatches.IsValidIndex(Index)
            ? StampedPanelBatches[Index] : nullptr;
        if (!Batch || !Batch->GetStaticMesh()) continue;
        FTransform Part = StillageTransform;
        FVector Scale = StillageTransform.GetScale3D() * DisplayScale;
        if (StampedPanelMirrored[Index]) Scale.Y *= -1.0;
        // The clean-room native kit retains its common full-car datum. Recenter
        // each mesh around its own bounds before placing it on the stillage rack.
        const FVector RecenteredOffset = StampedPanelOffsets[Index]
            - (Batch->GetStaticMesh()->GetBounds().Origin * DisplayScale);
        Part.SetLocation(StillageTransform.TransformPosition(RecenteredOffset));
        Part.SetScale3D(Scale);
        Batch->AddInstance(Part, true);
    }
}

void ALBOneFactoryWIPPresentationActor::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    FString Reason;
    RefreshFromLedger(Reason);
}

bool ALBOneFactoryWIPPresentationActor::RefreshFromLedger(FString& OutReason)
{
    using namespace LBOneFactoryWIPPresentationPrivate;

    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("NO WORLD");
        return false;
    }

    ULBOneFactoryRuntimeRegistrySubsystem* Registry =
        World->GetSubsystem<ULBOneFactoryRuntimeRegistrySubsystem>();
    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    FString RegistryReason;
    if (!Registry || !Registry->ResolveRuntimeBackbone(Production,
            Coordinator, RegistryReason))
    {
        ClearPresentation();
        OutReason = RegistryReason.IsEmpty()
            ? TEXT("NO COORDINATOR OR PRODUCTION FLOW YET")
            : RegistryReason;
        return false;
    }

    if (bMaterialResolutionFailed)
    {
        OutReason = TEXT("WIP PRESENTATION HAS AN UNRESOLVED OPTIONAL MESH; REBUILD REQUIRED");
        return false;
    }

    // Resolve meshes once, on first successful refresh. Authored materials are
    // kept; only families with a declared override (the ED-coat primed body)
    // replace them.
    if (!bMaterialsResolved)
    {
        for (int32 Index = 0; Index < Batches.Num(); ++Index)
        {
            UStaticMesh* Mesh = Cast<UStaticMesh>(
                StaticLoadObject(UStaticMesh::StaticClass(), nullptr,
                    BatchMeshPath[Index]));
            if (!Mesh || !Batches[Index])
            {
                ClearPresentation();
                bMaterialResolutionFailed = true;
                OutReason = FString::Printf(
                    TEXT("WIP PRESENTATION COULD NOT RESOLVE MESH %d: %s"),
                    Index, BatchMeshPath[Index]);
                return false;
            }
            Batches[Index]->SetStaticMesh(Mesh);
            if (Index == static_cast<int32>(ELBOneFactoryWIPVisual::FinishedCar)
                && GearBatch)
            {
                UStaticMesh* Gear = Cast<UStaticMesh>(
                    StaticLoadObject(UStaticMesh::StaticClass(), nullptr,
                        TEXT("/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/Layers"
                             "/SM_LB_C2040_RollingGear")));
                if (Gear)
                {
                    GearBatch->SetStaticMesh(Gear);
                }
            }
            if (BatchMaterialOverride[Index])
            {
                UMaterialInterface* Override = Cast<UMaterialInterface>(
                    StaticLoadObject(UMaterialInterface::StaticClass(), nullptr,
                        BatchMaterialOverride[Index]));
                if (Override)
                {
                    UMaterialInstanceDynamic* Solid =
                        UMaterialInstanceDynamic::Create(Override, this);
                    Solid->SetVectorParameterValue(TEXT("Color"), BatchSolidColours[Index]);
                    Solid->SetVectorParameterValue(TEXT("BaseColor"), BatchSolidColours[Index]);
                    BatchMaterials.Add(Solid);
                    for (int32 Slot = 0;
                        Slot < Mesh->GetStaticMaterials().Num(); ++Slot)
                    {
                        Batches[Index]->SetMaterial(Slot, Solid);
                    }
                }
            }
        }
        bMaterialsResolved = true;
    }

    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId = NAME_None;
    FString RouteReason;
    if (!Coordinator->GetConfiguredStationRoute(Route, TopologyId, RouteReason))
    {
        ClearPresentation();
        OutReason = RouteReason;
        return false;
    }

    TMap<FName, FTransform> StationTransforms;
    StationTransforms.Reserve(Route.Num());
    for (const FLBOneFactoryRuntimeStationStep& Step : Route)
    {
        StationTransforms.Add(Step.StationId, Step.WorldTransform);
    }

    const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();

    // The isolated 2126 overhead controller owns Press WIP only while its
    // presentation is explicitly enabled. A typed weak reference makes the
    // steady-state check O(1); absent controllers are rediscovered at most
    // once per second rather than by an untyped full-world scan every frame.
    const bool bOverheadPressPresentationActive =
        HasEnabledOverheadPressPresentation(World);
    const auto IsOwnedByOverheadPressPresentation =
        [bOverheadPressPresentationActive](
            const FLBOneFactoryVehicleUnitState& Unit)
        {
            return bOverheadPressPresentationActive
                && Unit.Department == ELBOneFactoryDepartment::Press;
        };

    // Membership signature: which unit is drawn in which batch. A unit changes
    // batch only when it earns a new stage, so this changes rarely. Position
    // changes every frame and is handled by updating transforms in place - an
    // ISM that is cleared and refilled every tick never settles.
    uint32 Signature = static_cast<uint32>(Route.Num());
    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        if (IsOwnedByOverheadPressPresentation(Unit) || Unit.bDispatched
            || Unit.QualityState == ELBOneFactoryVehicleQualityState::Scrapped)
        {
            continue;
        }
        Signature = HashCombine(Signature, GetTypeHash(Unit.UnitId));
        Signature = HashCombine(Signature, GetTypeHash(Unit.VehicleModelId));
        Signature = HashCombine(Signature,
            static_cast<uint32>(Unit.Stage) + 1u);
    }

    if (bHasBuiltOnce && Signature == LastSignature)
    {
        // Same cars in the same families: just move them.
        for (const FInstanceRef& Ref : InstanceRefs)
        {
            if (!Batches.IsValidIndex(Ref.BatchIndex) || !Batches[Ref.BatchIndex])
            {
                continue;
            }
            const FLBOneFactoryVehicleUnitState* Unit = Ledger.Units.FindByPredicate(
                [&Ref](const FLBOneFactoryVehicleUnitState& Candidate)
                { return Candidate.UnitId == Ref.UnitId; });
            if (!Unit)
            {
                continue;
            }
            if (!SupportsVehicleModel(Unit->VehicleModelId))
            {
                continue;
            }
            FTransform Moved;
            if (ComputeUnitTransform(Route, StationTransforms, Coordinator,
                    *Unit, Moved))
            {
                Batches[Ref.BatchIndex]->UpdateInstanceTransform(
                    Ref.InstanceIndex, Moved, true, false, true);
                // Finished vehicles own a matching rolling-gear instance in a
                // separate batch.  The membership signature keeps both batches
                // in the same finished-car order, so move the matching gear
                // instance during stable-frame interpolation as well.
                if (Ref.BatchIndex
                        == static_cast<int32>(ELBOneFactoryWIPVisual::FinishedCar)
                    && GearBatch
                    && GearBatch->GetInstanceCount() > Ref.InstanceIndex)
                {
                    GearBatch->UpdateInstanceTransform(
                        Ref.InstanceIndex, Moved, true, false, true);
                }
            }
        }
        for (UInstancedStaticMeshComponent* Batch : Batches)
        {
            if (Batch && Batch->GetInstanceCount() > 0)
            {
                Batch->MarkRenderStateDirty();
            }
        }
        if (GearBatch && GearBatch->GetInstanceCount() > 0)
        {
            GearBatch->MarkRenderStateDirty();
        }
        // The panel rack is compact (11 meshes per pressed stillage) and is
        // intentionally rebuilt so it follows the moving stillage exactly.
        for (UInstancedStaticMeshComponent* Batch : StampedPanelBatches)
        {
            if (Batch) Batch->ClearInstances();
        }
        int32 UnsupportedUnitCount = 0;
        for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
        {
            if (IsOwnedByOverheadPressPresentation(Unit) || Unit.bDispatched
                || Unit.QualityState == ELBOneFactoryVehicleQualityState::Scrapped)
            {
                continue;
            }
            if (!SupportsVehicleModel(Unit.VehicleModelId))
            {
                ++UnsupportedUnitCount;
                continue;
            }
            if (VisualForStage(Unit.Stage) != ELBOneFactoryWIPVisual::PanelStack)
            {
                continue;
            }
            FTransform Stillage;
            if (ComputeUnitTransform(Route, StationTransforms, Coordinator, Unit, Stillage))
            {
                AddStampedPanelSet(Stillage);
            }
        }
        OutReason = UnsupportedUnitCount == 0
            ? FString::Printf(TEXT("%d unit(s) on the line"), VisibleUnitCount)
            : FString::Printf(TEXT("%d unit(s) visible; %d unit(s) withheld: no model-specific WIP visual authority"),
                VisibleUnitCount, UnsupportedUnitCount);
        return UnsupportedUnitCount == 0;
    }
    LastSignature = Signature;
    bHasBuiltOnce = true;

    ClearPresentation();
    InstanceRefs.Reset();
    int32 UnsupportedUnitCount = 0;

    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        // A dispatched car has left the building; it is no longer on the line.
        if (IsOwnedByOverheadPressPresentation(Unit) || Unit.bDispatched
            || Unit.QualityState == ELBOneFactoryVehicleQualityState::Scrapped)
        {
            continue;
        }
        if (!SupportsVehicleModel(Unit.VehicleModelId))
        {
            ++UnsupportedUnitCount;
            continue;
        }

        const int32 VisualIndex = static_cast<int32>(VisualForStage(Unit.Stage));
        if (!Batches.IsValidIndex(VisualIndex) || !Batches[VisualIndex])
        {
            continue;
        }

        FTransform Instance;
        if (!ComputeUnitTransform(Route, StationTransforms, Coordinator, Unit,
                Instance))
        {
            continue;
        }

        const int32 Added = Batches[VisualIndex]->AddInstance(Instance, true);
        if (VisualIndex == static_cast<int32>(ELBOneFactoryWIPVisual::PanelStack))
        {
            AddStampedPanelSet(Instance);
        }
        if (VisualIndex == static_cast<int32>(ELBOneFactoryWIPVisual::FinishedCar)
            && GearBatch && GearBatch->GetStaticMesh())
        {
            GearBatch->AddInstance(Instance, true);
        }
        if (Added != INDEX_NONE)
        {
            FInstanceRef Ref;
            Ref.UnitId = Unit.UnitId;
            Ref.BatchIndex = VisualIndex;
            Ref.InstanceIndex = Added;
            InstanceRefs.Add(Ref);
            ++VisibleUnitCount;
        }
    }

    if (VisibleUnitCount != LastLoggedUnitCount
        || UnsupportedUnitCount != LastUnsupportedModelUnitCount)
    {
        LastLoggedUnitCount = VisibleUnitCount;
        LastUnsupportedModelUnitCount = UnsupportedUnitCount;
        UE_LOG(LogTemp, Display,
            TEXT("LINE_BOSS_WIP_VISIBLE units=%d withheldUnsupported=%d ledger=%d route=%d "
                 "actorHidden=%d"),
            VisibleUnitCount, UnsupportedUnitCount, Ledger.Units.Num(), Route.Num(),
            IsHidden() ? 1 : 0);
        for (int32 Index = 0; Index < Batches.Num(); ++Index)
        {
            UInstancedStaticMeshComponent* Batch = Batches[Index];
            if (!Batch || Batch->GetInstanceCount() == 0)
            {
                continue;
            }
            const FBoxSphereBounds B = Batch->Bounds;
            UE_LOG(LogTemp, Display,
                TEXT("LINE_BOSS_WIP_BATCH %d count=%d mesh=%s visible=%d "
                     "registered=%d origin=(%.0f,%.0f,%.0f) "
                     "extent=(%.0f,%.0f,%.0f)"),
                Index, Batch->GetInstanceCount(),
                Batch->GetStaticMesh()
                    ? *Batch->GetStaticMesh()->GetName() : TEXT("NONE"),
                Batch->IsVisible() ? 1 : 0,
                Batch->IsRegistered() ? 1 : 0,
                B.Origin.X, B.Origin.Y, B.Origin.Z,
                B.BoxExtent.X, B.BoxExtent.Y, B.BoxExtent.Z);
        }
        for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
        {
            if (!Unit.bDispatched)
            {
                UE_LOG(LogTemp, Display,
                    TEXT("LINE_BOSS_WIP_UNIT %s station=%s matched=%d"),
                    *Unit.UnitId.ToString(), *Unit.CurrentStationId.ToString(),
                    StationTransforms.Contains(Unit.CurrentStationId) ? 1 : 0);
            }
        }
    }

    OutReason = UnsupportedUnitCount == 0
        ? FString::Printf(TEXT("%d unit(s) on the line"), VisibleUnitCount)
        : FString::Printf(TEXT("%d unit(s) visible; %d unit(s) withheld: no model-specific WIP visual authority"),
            VisibleUnitCount, UnsupportedUnitCount);
    return UnsupportedUnitCount == 0;
}
