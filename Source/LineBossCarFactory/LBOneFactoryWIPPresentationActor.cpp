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

    /** Engine primitives stand in until VehicleWIPNativeKit_v001 is imported. */
    const TCHAR* const BatchMeshPath[VisualCount] = {
        TEXT("/Engine/BasicShapes/Cylinder.Cylinder"),
        TEXT("/Engine/BasicShapes/Cube.Cube"),
        TEXT("/Engine/BasicShapes/Cube.Cube"),
        TEXT("/Engine/BasicShapes/Cube.Cube"),
        TEXT("/Engine/BasicShapes/Cube.Cube"),
        TEXT("/Engine/BasicShapes/Cube.Cube")
    };

    const TCHAR* const BasicMaterialPath =
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");

    /**
     * Semantic colours. Bare steel reads cool and desaturated, primer dull, and
     * only the colour coat carries the Cairnwell livery, so a glance down the
     * line tells the player how far each body has travelled.
     */
    const TCHAR* const BatchColour[VisualCount] = {
        TEXT("C2C8D0"),   // coil: mill steel
        TEXT("D8DDE3"),   // pressed panels: brighter cut steel
        TEXT("9AA3AF"),   // body in white: welded shell
        TEXT("7A848F"),   // primed: dull e-coat grey
        TEXT("3FD4C8"),   // painted: Cairnwell teal
        TEXT("58E6DA")    // finished: brighter trimmed car
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
        // A coil lies on its side across the line.
        { FVector(1.6, 1.6, 1.3), 80.0, FRotator(90.0, 0.0, 0.0) },
        // A flat stack of panels in stillage.
        { FVector(2.6, 1.7, 0.55), 30.0, FRotator::ZeroRotator },
        { FVector(4.4, 1.8, 1.30), 75.0, FRotator::ZeroRotator },
        { FVector(4.4, 1.8, 1.30), 75.0, FRotator::ZeroRotator },
        { FVector(4.5, 1.85, 1.35), 78.0, FRotator::ZeroRotator },
        { FVector(4.6, 1.90, 1.45), 82.0, FRotator::ZeroRotator }
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

    FLBOneFactoryRuntimeVehicleStatus Status;
    FString StatusReason;
    if (Coordinator
        && Coordinator->GetVehicleRuntimeStatus(Unit.UnitId, Status,
            StatusReason)
        && !Status.bAwaitingQualityResult
        && Route.IsValidIndex(Status.StationCursor)
        && Route.IsValidIndex(Status.StationCursor + 1)
        && Route[Status.StationCursor].StationId == Unit.CurrentStationId)
    {
        constexpr float TransferStart = 0.80f;
        if (Status.NormalizedCycleProgress > TransferStart)
        {
            const FVector NextLocation =
                Route[Status.StationCursor + 1].WorldTransform.GetLocation();
            const float Alpha = FMath::Clamp(
                (Status.NormalizedCycleProgress - TransferStart)
                    / (1.0f - TransferStart), 0.0f, 1.0f);
            // Ease in and out so the transfer starts and stops smoothly.
            const float Smooth = Alpha * Alpha * (3.0f - 2.0f * Alpha);
            Location = FMath::Lerp(Location, NextLocation, Smooth);

            const FVector Travel = NextLocation - Station->GetLocation();
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

    // Resolve meshes and semantic materials once, on first successful refresh.
    if (!bMaterialsResolved)
    {
        UMaterialInterface* Base = Cast<UMaterialInterface>(
            StaticLoadObject(UMaterialInterface::StaticClass(), nullptr,
                BasicMaterialPath));
        if (!Base)
        {
            OutReason = TEXT("WIP PRESENTATION COULD NOT RESOLVE BASE MATERIAL");
            return false;
        }
        for (int32 Index = 0; Index < Batches.Num(); ++Index)
        {
            UStaticMesh* Mesh = Cast<UStaticMesh>(
                StaticLoadObject(UStaticMesh::StaticClass(), nullptr,
                    BatchMeshPath[Index]));
            UMaterialInstanceDynamic* Material =
                UMaterialInstanceDynamic::Create(Base, this);
            if (!Mesh || !Material || !Batches[Index])
            {
                ClearPresentation();
                OutReason = TEXT("WIP PRESENTATION COULD NOT RESOLVE A BATCH");
                return false;
            }
            const FLinearColor Colour = FLinearColor::FromSRGBColor(
                FColor::FromHex(BatchColour[Index]));
            Material->SetVectorParameterValue(TEXT("Color"), Colour);
            Material->SetVectorParameterValue(TEXT("BaseColor"), Colour);
            Batches[Index]->SetStaticMesh(Mesh);
            Batches[Index]->SetMaterial(0, Material);
            BatchMaterials.Add(Material);
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
