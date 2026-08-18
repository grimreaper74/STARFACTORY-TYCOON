#include "LBOneFactoryWIPPresentationActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace LBOneFactoryWIPPresentationPrivate
{
    constexpr int32 VisualCount =
        static_cast<int32>(ELBOneFactoryWIPVisual::FinishedCar) + 1;

    const TCHAR* const BatchComponentNames[VisualCount] = {
        TEXT("WIP_Coil"), TEXT("WIP_PanelStack"), TEXT("WIP_BodyInWhite"),
        TEXT("WIP_PrimedBody"), TEXT("WIP_PaintedBody"), TEXT("WIP_FinishedCar")
    };

    /**
     * Real authored meshes for every family, measured in the editor. The
     * Cairnwell runtime and panel-stillage assets were imported by the guarded
     * lanes on 2026-08-15 and carry their own authored materials; the coil is
     * the repaired press-shop wrapped coil. Scale is 1.0 everywhere - these are
     * true-size assets, not primitives.
     *
     *   WrappedCoil_Repaired_v003          181 x 150 x 179  pivot at base
     *   PanelStillage_Runtime_v001         190 x 139 x 116  pivot centred
     *   C2040_BIW_AutomotiveSkeleton_v001  452 x 161 x 143  floor at pivot
     *   C2040_EmeraldBodyVisualAuthority   456 x 188 x 138  floor at pivot
     */
    const TCHAR* const BatchMeshPath[VisualCount] = {
        TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004"
             "/Inbound/SM_CA_MW_WrappedCoil_Repaired_v003"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/PanelStillageRuntime_v001"
             "/SM_LB_PanelStillage_Runtime_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Vehicles"
             "/Cairnwell2040Runtime_v001/Meshes"
             "/SM_LB_C2040_BIW_AutomotiveSkeleton_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Vehicles"
             "/Cairnwell2040Runtime_v001/Meshes"
             "/SM_LB_C2040_BIW_AutomotiveSkeleton_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Vehicles"
             "/Cairnwell2040Runtime_v001/Meshes"
             "/SM_LB_C2040_EmeraldBodyVisualAuthority_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Vehicles"
             "/Cairnwell2040Runtime_v001/Meshes"
             "/SM_LB_C2040_EmeraldBodyVisualAuthority_v001")
    };

    /**
     * Optional material override per family. Null keeps the mesh's authored
     * materials, which is right for every family except Primed: the primed body
     * reuses the BIW skeleton mesh with the authored ED-coat material, which is
     * exactly what a body leaving the ED tank looks like.
     */
    const TCHAR* const BatchMaterialOverride[VisualCount] = {
        nullptr,
        nullptr,
        nullptr,
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Vehicles"
             "/Cairnwell2040Runtime_v001/Materials/M_LB_C2040_EDCoat_v001"),
        nullptr,
        nullptr
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
        // Coil: pivot at base, stands on the floor as delivered.
        { FVector(1.0), 0.0, FRotator::ZeroRotator },
        // Stillage: pivot centred, so lift by half its 116 cm height.
        { FVector(1.0), 58.0, FRotator::ZeroRotator },
        // BIW and primed body: authored floor sits at the pivot.
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

ELBOneFactoryWIPVisual ALBOneFactoryWIPPresentationActor::VisualForStage(
    const ELBOneFactoryVehicleStage Stage)
{
    switch (Stage)
    {
    case ELBOneFactoryVehicleStage::InboundCoil:
    case ELBOneFactoryVehicleStage::BlankPreparation:
        return ELBOneFactoryWIPVisual::Coil;

    case ELBOneFactoryVehicleStage::Pressing:
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
    VisibleUnitCount = 0;
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

    ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
    ALBOneFactoryProductionFlowAuthority* Production = nullptr;
    for (TActorIterator<ALBOneFactoryRuntimeCoordinator> It(World); It; ++It)
    {
        if (IsValid(*It)) { Coordinator = *It; break; }
    }
    for (TActorIterator<ALBOneFactoryProductionFlowAuthority> It(World); It; ++It)
    {
        if (IsValid(*It)) { Production = *It; break; }
    }
    if (!Coordinator || !Production)
    {
        ClearPresentation();
        OutReason = TEXT("NO COORDINATOR OR PRODUCTION FLOW YET");
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
                        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Vehicles"
                             "/Cairnwell2040Runtime_v001/Meshes"
                             "/SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001")));
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
                    for (int32 Slot = 0;
                        Slot < Mesh->GetStaticMaterials().Num(); ++Slot)
                    {
                        Batches[Index]->SetMaterial(Slot, Override);
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

    // Membership signature: which unit is drawn in which batch. A unit changes
    // batch only when it earns a new stage, so this changes rarely. Position
    // changes every frame and is handled by updating transforms in place - an
    // ISM that is cleared and refilled every tick never settles.
    uint32 Signature = static_cast<uint32>(Route.Num());
    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        if (Unit.bDispatched)
        {
            continue;
        }
        Signature = HashCombine(Signature, GetTypeHash(Unit.UnitId));
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
            FTransform Moved;
            if (ComputeUnitTransform(Route, StationTransforms, Coordinator,
                    *Unit, Moved))
            {
                Batches[Ref.BatchIndex]->UpdateInstanceTransform(
                    Ref.InstanceIndex, Moved, true, false, true);
            }
        }
        for (UInstancedStaticMeshComponent* Batch : Batches)
        {
            if (Batch && Batch->GetInstanceCount() > 0)
            {
                Batch->MarkRenderStateDirty();
            }
        }
        OutReason = FString::Printf(TEXT("%d unit(s) on the line"),
            VisibleUnitCount);
        return true;
    }
    LastSignature = Signature;
    bHasBuiltOnce = true;

    ClearPresentation();
    InstanceRefs.Reset();

    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        // A dispatched car has left the building; it is no longer on the line.
        if (Unit.bDispatched)
        {
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

    if (VisibleUnitCount != LastLoggedUnitCount)
    {
        LastLoggedUnitCount = VisibleUnitCount;
        UE_LOG(LogTemp, Display,
            TEXT("LINE_BOSS_WIP_VISIBLE units=%d ledger=%d route=%d "
                 "actorHidden=%d"),
            VisibleUnitCount, Ledger.Units.Num(), Route.Num(),
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

    OutReason = FString::Printf(TEXT("%d unit(s) on the line"),
        VisibleUnitCount);
    return true;
}
