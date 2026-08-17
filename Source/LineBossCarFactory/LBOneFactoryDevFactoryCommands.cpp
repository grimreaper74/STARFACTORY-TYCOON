#include "LBOneFactoryDevFactoryCommands.h"

#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/PointLight.h"
#include "Engine/Engine.h"
#include "Engine/SkyLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "UnrealClient.h"
#include "LBOneFactoryBodyWeldStarterLayout.h"
#include "LBOneFactoryPaintStarterLayout.h"
#include "LBOneFactoryPlayerBuilderSubsystem.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactoryDevEnvelopeActor.h"
#include "LBOneFactoryDevRestoredShopActor.h"
#include "LBOneFactoryDevStationDressingActor.h"
#include "LBOneFactoryProductionHUD.h"
#include "LBOneFactoryWIPPresentationActor.h"

DEFINE_LOG_CATEGORY_STATIC(LogLineBossOneFactoryDev, Display, All);

namespace
{
    /** Finds exactly one actor of the given type; duplicates are a failure. */
    template <typename ActorType>
    ActorType* FindExactlyOne(const UWorld* World)
    {
        if (!World)
        {
            return nullptr;
        }
        ActorType* Found = nullptr;
        for (TActorIterator<ActorType> It(World); It; ++It)
        {
            if (!IsValid(*It) || It->IsActorBeingDestroyed())
            {
                continue;
            }
            if (Found)
            {
                return nullptr;
            }
            Found = *It;
        }
        return Found;
    }

    UWorld* ResolveWorld(const UObject* WorldContextObject)
    {
        if (!GEngine || !WorldContextObject)
        {
            return nullptr;
        }
        return GEngine->GetWorldFromContextObject(
            WorldContextObject, EGetWorldErrorMode::ReturnNull);
    }

    FString EnumName(const UEnum* Enum, const int64 Value)
    {
        return Enum ? Enum->GetNameStringByValue(Value) : FString(TEXT("?"));
    }

    /** Monotonic suffix so every submitted quality evidence ID stays unique. */
    int32 GDevEvidenceCounter = 0;

    /**
     * Build order IDs must stay unique for the life of the session, not just
     * within one call, so staggering cars onto the line across several
     * StartProduction calls does not collide with an existing order.
     */
    int32 GDevBuildOrderCounter = 0;
}

ALBOneFactoryRuntimeCoordinator* ULBOneFactoryDevFactory::FindCoordinator(
    const UWorld* World)
{
    return FindExactlyOne<ALBOneFactoryRuntimeCoordinator>(World);
}

ALBOneFactoryProductionFlowAuthority*
ULBOneFactoryDevFactory::FindProductionFlow(const UWorld* World)
{
    return FindExactlyOne<ALBOneFactoryProductionFlowAuthority>(World);
}

bool ULBOneFactoryDevFactory::BuildAndCommissionWholeFactory(
    UObject* WorldContextObject, FString& OutReason)
{
    UWorld* World = ResolveWorld(WorldContextObject);
    if (!World)
    {
        OutReason = TEXT("NO WORLD");
        return false;
    }

    ULBOneFactoryPlayerBuilderSubsystem* Builder =
        World->GetSubsystem<ULBOneFactoryPlayerBuilderSubsystem>();
    if (!Builder)
    {
        OutReason = TEXT("ONEFACTORY PLAYER BUILDER SUBSYSTEM UNAVAILABLE");
        return false;
    }
    if (!Builder->IsOneFactoryBuilderWorld())
    {
        OutReason = TEXT("THIS WORLD IS NOT A ONEFACTORY BUILDER WORLD");
        return false;
    }

    // Press, Body/Weld, Paint then Assembly: the contract's lifecycle order.
    // CreateNewFactory establishes the Press starter, so it has no separate
    // create step of its own.
    using FBuilderStep = bool (ULBOneFactoryPlayerBuilderSubsystem::*)(FString&);
    struct FNamedStep
    {
        const TCHAR* Label;
        FBuilderStep Step;
    };
    static const FNamedStep Steps[] = {
        { TEXT("CreateNewFactory"),
            &ULBOneFactoryPlayerBuilderSubsystem::CreateNewFactory },
        { TEXT("CommissionPressStarter"),
            &ULBOneFactoryPlayerBuilderSubsystem::CommissionPressStarter },
        { TEXT("CreateBodyWeldStarter"),
            &ULBOneFactoryPlayerBuilderSubsystem::CreateBodyWeldStarter },
        { TEXT("CommissionBodyWeldStarter"),
            &ULBOneFactoryPlayerBuilderSubsystem::CommissionBodyWeldStarter },
        { TEXT("CreatePaintStarter"),
            &ULBOneFactoryPlayerBuilderSubsystem::CreatePaintStarter },
        { TEXT("CommissionPaintStarter"),
            &ULBOneFactoryPlayerBuilderSubsystem::CommissionPaintStarter },
        { TEXT("CreateAssemblyStarter"),
            &ULBOneFactoryPlayerBuilderSubsystem::CreateAssemblyStarter },
        { TEXT("CommissionAssemblyStarter"),
            &ULBOneFactoryPlayerBuilderSubsystem::CommissionAssemblyStarter },
    };

    for (const FNamedStep& Named : Steps)
    {
        FString StepReason;
        if (!(Builder->*(Named.Step))(StepReason))
        {
            OutReason = FString::Printf(TEXT("%s FAILED: %s"), Named.Label,
                StepReason.IsEmpty() ? TEXT("no reason given") : *StepReason);
            return false;
        }
        UE_LOG(LogLineBossOneFactoryDev, Display,
            TEXT("LINE_BOSS_DEV_BUILD_STEP ok=%s"), Named.Label);
    }

    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(World);
    if (!Coordinator)
    {
        OutReason = TEXT("EXPECTED EXACTLY ONE RUNTIME COORDINATOR");
        return false;
    }
    if (!Coordinator->ValidateRuntimeFactory(OutReason))
    {
        return false;
    }

    OutReason = TEXT("WHOLE FACTORY CREATED, COMMISSIONED AND VALIDATED");
    UE_LOG(LogLineBossOneFactoryDev, Display,
        TEXT("LINE_BOSS_DEV_BUILD_COMPLETE %s"), *OutReason);
    return true;
}

bool ULBOneFactoryDevFactory::StartDemoProduction(UObject* WorldContextObject,
    const int32 VehicleCount, FString& OutReason)
{
    UWorld* World = ResolveWorld(WorldContextObject);
    if (!World)
    {
        OutReason = TEXT("NO WORLD");
        return false;
    }
    if (VehicleCount <= 0)
    {
        OutReason = TEXT("VEHICLE COUNT MUST BE POSITIVE");
        return false;
    }

    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(World);
    ALBOneFactoryBodyWeldStarterLayoutAuthority* Body =
        FindExactlyOne<ALBOneFactoryBodyWeldStarterLayoutAuthority>(World);
    ALBOneFactoryPaintStarterLayoutAuthority* Paint =
        FindExactlyOne<ALBOneFactoryPaintStarterLayoutAuthority>(World);
    if (!Coordinator || !Body || !Paint)
    {
        OutReason = TEXT(
            "NEED EXACTLY ONE COORDINATOR, BODY/WELD AND PAINT AUTHORITY - "
            "BUILD THE FACTORY FIRST");
        return false;
    }

    // Identities come from the committed layouts, exactly as the runtime
    // automation does, so a reassigned programme is honoured automatically.
    const FName VehicleModelId = Body->CaptureLayout().VehicleModelId;
    const FName PaintProgrammeId = Paint->CaptureLayout().PaintProgrammeId;

    int32 Started = 0;
    for (int32 Index = 0; Index < VehicleCount; ++Index)
    {
        const FName BuildOrderId(
            *FString::Printf(TEXT("DEV_ORDER_%03d"), ++GDevBuildOrderCounter));
        const FName CoilLotId(
            *FString::Printf(TEXT("COIL_%s"), *BuildOrderId.ToString()));

        FName UnitId = NAME_None;
        FString StepReason;
        if (!Coordinator->CreateRuntimeVehicleOrder(BuildOrderId,
                VehicleModelId, PaintProgrammeId, TEXT("CAIRNWELL_TEAL"),
                CoilLotId, UnitId, StepReason))
        {
            // The inbound reservation is a single physical position, so a
            // later order legitimately waits for the line to clear.
            OutReason = FString::Printf(
                TEXT("started %d of %d; %s could not be created: %s"),
                Started, VehicleCount, *BuildOrderId.ToString(), *StepReason);
            return Started > 0;
        }
        if (!Coordinator->StartVehicle(UnitId, StepReason))
        {
            OutReason = FString::Printf(
                TEXT("started %d of %d; %s could not start: %s"), Started,
                VehicleCount, *UnitId.ToString(), *StepReason);
            return Started > 0;
        }
        ++Started;
        UE_LOG(LogLineBossOneFactoryDev, Display,
            TEXT("LINE_BOSS_DEV_ORDER_STARTED unit=%s model=%s"),
            *UnitId.ToString(), *VehicleModelId.ToString());
    }

    OutReason = FString::Printf(TEXT("started %d vehicle order(s)"), Started);
    return true;
}

bool ULBOneFactoryDevFactory::AdvanceFactory(UObject* WorldContextObject,
    const float DeltaSeconds, const bool bAutoPassQualityGates,
    int32& OutProcessedUnitCount, FString& OutReason)
{
    OutProcessedUnitCount = 0;

    UWorld* World = ResolveWorld(WorldContextObject);
    if (!World)
    {
        OutReason = TEXT("NO WORLD");
        return false;
    }
    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(World);
    ALBOneFactoryProductionFlowAuthority* Production = FindProductionFlow(World);
    if (!Coordinator || !Production)
    {
        OutReason = TEXT("NEED EXACTLY ONE COORDINATOR AND PRODUCTION FLOW");
        return false;
    }

    if (!Coordinator->TickAutomaticFlow(DeltaSeconds, OutProcessedUnitCount,
            OutReason))
    {
        return false;
    }

    if (!bAutoPassQualityGates)
    {
        return true;
    }

    // Body, Paint and end-of-line inspections deliberately hold at 100 percent
    // until a result arrives. Passing them here keeps the developer loop moving
    // without inventing a second decision path: it calls the same API the UMG
    // quality control calls.
    // CaptureLedger returns by value; hold it in a local so the units array
    // outlives the loop rather than dangling on a destroyed temporary.
    const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        if (Unit.bCompleted || Unit.bDispatched)
        {
            continue;
        }
        FLBOneFactoryRuntimeVehicleStatus Status;
        FString StatusReason;
        if (!Coordinator->GetVehicleRuntimeStatus(Unit.UnitId, Status,
                StatusReason))
        {
            continue;
        }
        if (!Status.bAwaitingQualityResult)
        {
            continue;
        }
        const FName EvidenceId(*FString::Printf(TEXT("DEV_QA_%s_%d"),
            *Unit.UnitId.ToString(), ++GDevEvidenceCounter));
        FString QualityReason;
        if (Coordinator->SubmitRuntimeQualityResult(Unit.UnitId,
                ELBOneFactoryVehicleQualityState::Passed, EvidenceId,
                QualityReason))
        {
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_QUALITY_PASS unit=%s station=%s"),
                *Unit.UnitId.ToString(), *Status.CurrentStationId.ToString());
        }
    }
    return true;
}

bool ULBOneFactoryDevFactory::RunFactory(UObject* WorldContextObject,
    const int32 Iterations, const float StepSeconds,
    const bool bAutoPassQualityGates, FString& OutReason)
{
    if (Iterations <= 0 || StepSeconds <= 0.0f)
    {
        OutReason = TEXT("ITERATIONS AND STEP SECONDS MUST BE POSITIVE");
        return false;
    }
    UWorld* World = ResolveWorld(WorldContextObject);
    ALBOneFactoryProductionFlowAuthority* Production = FindProductionFlow(World);
    if (!Production)
    {
        OutReason = TEXT("NEED EXACTLY ONE PRODUCTION FLOW");
        return false;
    }

    for (int32 Step = 0; Step < Iterations; ++Step)
    {
        int32 Processed = 0;
        FString StepReason;
        if (!AdvanceFactory(WorldContextObject, StepSeconds,
                bAutoPassQualityGates, Processed, StepReason))
        {
            OutReason = FString::Printf(TEXT("stopped at step %d/%d: %s"),
                Step + 1, Iterations, *StepReason);
            return false;
        }
    }

    int32 Dispatched = 0;
    int32 Completed = 0;
    const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        Dispatched += Unit.bDispatched ? 1 : 0;
        Completed += Unit.bCompleted ? 1 : 0;
    }
    OutReason = FString::Printf(
        TEXT("ran %d x %.1fs; units=%d completed=%d dispatched=%d"),
        Iterations, StepSeconds, Ledger.Units.Num(), Completed, Dispatched);
    return true;
}

bool ULBOneFactoryDevFactory::BuildFactoryStatusReport(
    UObject* WorldContextObject, FString& OutReport)
{
    UWorld* World = ResolveWorld(WorldContextObject);
    if (!World)
    {
        OutReport = TEXT("NO WORLD");
        return false;
    }
    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(World);
    ALBOneFactoryProductionFlowAuthority* Production = FindProductionFlow(World);
    if (!Coordinator || !Production)
    {
        OutReport = TEXT("NEED EXACTLY ONE COORDINATOR AND PRODUCTION FLOW");
        return false;
    }

    const UEnum* StageEnum = StaticEnum<ELBOneFactoryVehicleStage>();
    const UEnum* DepartmentEnum = StaticEnum<ELBOneFactoryDepartment>();

    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId = NAME_None;
    FString RouteReason;
    TArray<FString> Lines;
    if (Coordinator->GetConfiguredStationRoute(Route, TopologyId, RouteReason))
    {
        int32 BodyStations = 0;
        for (const FLBOneFactoryRuntimeStationStep& Step : Route)
        {
            if (Step.Department == ELBOneFactoryDepartment::Body)
            {
                ++BodyStations;
            }
        }
        Lines.Add(FString::Printf(
            TEXT("route: %d stations (%d Body/Weld), topology=%s"),
            Route.Num(), BodyStations, *TopologyId.ToString()));
    }
    else
    {
        Lines.Add(FString::Printf(TEXT("route unavailable: %s"), *RouteReason));
    }

    const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    Lines.Add(FString::Printf(TEXT("units: %d"), Ledger.Units.Num()));

    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        FLBOneFactoryRuntimeVehicleStatus Status;
        FString StatusReason;
        const bool bHasStatus =
            Coordinator->GetVehicleRuntimeStatus(Unit.UnitId, Status,
                StatusReason);
        Lines.Add(FString::Printf(
            TEXT("  %s  %s/%s  station=%s  %d/%d  cycle=%.0f%%%s%s"),
            *Unit.UnitId.ToString(),
            *EnumName(DepartmentEnum, static_cast<int64>(Unit.Department)),
            *EnumName(StageEnum, static_cast<int64>(Unit.Stage)),
            *Unit.CurrentStationId.ToString(),
            bHasStatus ? Status.CompletedStationCount : 0,
            bHasStatus ? Status.TotalStationCount : 0,
            bHasStatus ? Status.NormalizedCycleProgress * 100.0f : 0.0f,
            (bHasStatus && Status.bAwaitingQualityResult)
                ? TEXT("  [AWAITING QA]") : TEXT(""),
            Unit.bDispatched ? TEXT("  [DISPATCHED]") : TEXT("")));
    }

    OutReport = FString::Join(Lines, TEXT("\n"));
    return true;
}

bool ULBOneFactoryDevFactory::EnsureDevLighting(UObject* WorldContextObject,
    const float Intensity, FString& OutReason)
{
    UWorld* World = ResolveWorld(WorldContextObject);
    if (!World)
    {
        OutReason = TEXT("NO WORLD");
        return false;
    }

    static const FName DevLightTag(TEXT("LB.OneFactory.DevLighting"));
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        if (IsValid(*It) && It->Tags.Contains(DevLightTag))
        {
            OutReason = TEXT("DEV LIGHTING ALREADY PRESENT");
            return true;
        }
    }

    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

    // A steep key light so the long shop floor is lit end to end rather than
    // only near the origin.
    ADirectionalLight* Key = World->SpawnActor<ADirectionalLight>(
        ADirectionalLight::StaticClass(),
        FVector(0.0f, 0.0f, 20000.0f),
        FRotator(-48.0f, 35.0f, 0.0f), Params);
    if (!Key)
    {
        OutReason = TEXT("COULD NOT SPAWN DIRECTIONAL LIGHT");
        return false;
    }
    Key->SetMobility(EComponentMobility::Movable);
    Key->Tags.AddUnique(DevLightTag);
    if (UDirectionalLightComponent* KeyComponent =
        Cast<UDirectionalLightComponent>(Key->GetLightComponent()))
    {
        KeyComponent->SetIntensity(FMath::Max(0.1f, Intensity));
        // Nominal 5000 K per the factory-wide lighting standard.
        KeyComponent->SetLightColor(FLinearColor(1.0f, 0.894f, 0.804f));
    }

    // The site is roofed, so a sun alone leaves whole bays black - the press
    // shop especially. Hang interior fixtures over the stations themselves,
    // derived from the live route so every occupied bay is actually lit.
    int32 BayLights = 0;
    if (ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(World))
    {
        TArray<FLBOneFactoryRuntimeStationStep> Route;
        FName TopologyId = NAME_None;
        FString RouteReason;
        if (Coordinator->GetConfiguredStationRoute(Route, TopologyId,
                RouteReason) && Route.Num() > 0)
        {
            // One lamp grid per department, sized to that department's own
            // footprint. A single grid over the union of the whole route
            // spread most of its lamps over empty mid-hall floor and left
            // the press bay's corners black at floor level.
            FBox DeptBounds[4];
            for (FBox& Box : DeptBounds) { Box.Init(); }
            for (const FLBOneFactoryRuntimeStationStep& Step : Route)
            {
                DeptBounds[static_cast<int32>(Step.Department)] +=
                    Step.WorldTransform.GetLocation();
            }
            for (const FBox& RawBox : DeptBounds)
            {
            if (!RawBox.IsValid)
            {
                continue;
            }
            const FBox Bounds =
                RawBox.ExpandBy(FVector(4000.0, 4000.0, 0.0));
            const FVector Min = Bounds.Min;
            const FVector Size = Bounds.GetSize();
            // Roughly one lamp per 18 m bay in each axis.
            const int32 GridX = FMath::Clamp(
                FMath::CeilToInt32(Size.X / 1800.0), 2, 12);
            const int32 GridY = FMath::Clamp(
                FMath::CeilToInt32(Size.Y / 1800.0), 2, 12);
            for (int32 X = 0; X < GridX; ++X)
            {
                for (int32 Y = 0; Y < GridY; ++Y)
                {
                    const FVector Where(
                        Min.X + Size.X * (X + 0.5) / GridX,
                        Min.Y + Size.Y * (Y + 0.5) / GridY,
                        1400.0);
                    APointLight* Bay = World->SpawnActor<APointLight>(
                        APointLight::StaticClass(), Where,
                        FRotator::ZeroRotator, Params);
                    if (!Bay)
                    {
                        continue;
                    }
                    Bay->SetMobility(EComponentMobility::Movable);
                    Bay->Tags.AddUnique(DevLightTag);
                    if (UPointLightComponent* BayComponent =
                        Cast<UPointLightComponent>(Bay->GetLightComponent()))
                    {
                        BayComponent->SetIntensity(68000.0f);
                        BayComponent->SetAttenuationRadius(
                            FMath::Max(Size.X, Size.Y) / 5.0f + 3000.0f);
                        BayComponent->SetLightColor(
                            FLinearColor(1.0f, 0.894f, 0.804f));
                        // A sparse quarter of the grid casts shadows, so
                        // machines are grounded by contact shadows instead
                        // of floating as flat marks - without paying for a
                        // shadow-casting light in every bay.
                        BayComponent->SetCastShadows(
                            (X % 2) == 0 && (Y % 2) == 0);
                    }
                    ++BayLights;
                }
            }
            }
        }
    }

    // Ambient fill so machine undersides and the far end of the line read.
    ASkyLight* Sky = World->SpawnActor<ASkyLight>(ASkyLight::StaticClass(),
        FVector(0.0f, 0.0f, 8000.0f), FRotator::ZeroRotator, Params);
    if (Sky)
    {
        if (USceneComponent* SkyRoot = Sky->GetRootComponent())
        {
            SkyRoot->SetMobility(EComponentMobility::Movable);
        }
        Sky->Tags.AddUnique(DevLightTag);
        if (USkyLightComponent* SkyComponent = Sky->GetLightComponent())
        {
            SkyComponent->SetIntensity(1.5f);
            SkyComponent->SetLightColor(FLinearColor(0.62f, 0.68f, 0.80f));
            SkyComponent->bLowerHemisphereIsBlack = false;
            // SLS_SpecifiedCubemap with no cubemap assigned contributes
            // nothing - the ambient fill was dead. Capture the scene
            // instead.
            SkyComponent->SourceType = ESkyLightSourceType::SLS_CapturedScene;
            SkyComponent->RecaptureSky();
        }
    }

    OutReason = FString::Printf(
        TEXT("directional light (%.1f), %d bay lights and sky fill"),
        Intensity, BayLights);
    return true;
}

bool ULBOneFactoryDevFactory::FrameProductionLine(UObject* WorldContextObject,
    const FString& Department, FString& OutReason)
{
    UWorld* World = ResolveWorld(WorldContextObject);
    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(World);
    if (!World || !Coordinator)
    {
        OutReason = TEXT("NEED A WORLD AND EXACTLY ONE COORDINATOR");
        return false;
    }

    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId = NAME_None;
    if (!Coordinator->GetConfiguredStationRoute(Route, TopologyId, OutReason))
    {
        return false;
    }

    // "Press@0.25~16" frames Press at a quarter of the solved distance from a
    // 16-degree pitch: the close-up syntax the polish tours shoot with. Both
    // modifiers are optional and filename-safe, so tour shot names keep them.
    FString Wanted = Department.IsEmpty() ? TEXT("All") : Department;
    double DistanceScale = 1.0;
    double PitchDegrees = 34.0;
    {
        FString Base = Wanted;
        FString Modifiers;
        if (Wanted.Split(TEXT("@"), &Base, &Modifiers))
        {
            FString ScaleText = Modifiers;
            FString PitchText;
            if (Modifiers.Split(TEXT("~"), &ScaleText, &PitchText))
            {
                PitchDegrees = FMath::Clamp(
                    FCString::Atod(*PitchText), 2.0, 88.0);
            }
            DistanceScale = FMath::Clamp(
                FCString::Atod(*ScaleText), 0.05, 4.0);
            Wanted = Base;
        }
    }
    const bool bAll = Wanted.Equals(TEXT("All"), ESearchCase::IgnoreCase);
    const bool bWIP = Wanted.Equals(TEXT("WIP"), ESearchCase::IgnoreCase);
    const UEnum* DepartmentEnum = StaticEnum<ELBOneFactoryDepartment>();

    FBox Bounds(ForceInit);
    int32 Counted = 0;

    // "WIP" frames the live units themselves rather than a department, so a
    // close shot of actual cars on the line is one command away.
    if (bWIP)
    {
        ALBOneFactoryProductionFlowAuthority* Production =
            FindProductionFlow(World);
        if (!Production)
        {
            OutReason = TEXT("NO PRODUCTION FLOW");
            return false;
        }
        TMap<FName, FTransform> ByStation;
        for (const FLBOneFactoryRuntimeStationStep& Step : Route)
        {
            ByStation.Add(Step.StationId, Step.WorldTransform);
        }
        const FLBOneFactoryProductionLedgerState Ledger =
            Production->CaptureLedger();
        for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
        {
            if (Unit.bDispatched)
            {
                continue;
            }
            if (const FTransform* At = ByStation.Find(Unit.CurrentStationId))
            {
                // Frame the first live unit only. Framing every unit averages
                // across departments hundreds of metres apart and puts the cars
                // at the edge of frame or outside it entirely.
                Bounds += At->GetLocation();
                ++Counted;
                break;
            }
        }
        if (Counted == 0)
        {
            OutReason = TEXT("no live units to frame");
            return false;
        }
    }
    // Keep the picked stations in route order: that order is the line direction.
    TArray<FVector> Picked;
    for (const FLBOneFactoryRuntimeStationStep& Step : Route)
    {
        if (bWIP)
        {
            break;
        }
        if (!bAll)
        {
            const FString Name = DepartmentEnum
                ? DepartmentEnum->GetNameStringByValue(
                    static_cast<int64>(Step.Department))
                : FString();
            if (!Name.Equals(Wanted, ESearchCase::IgnoreCase))
            {
                continue;
            }
        }
        Bounds += Step.WorldTransform.GetLocation();
        Picked.Add(Step.WorldTransform.GetLocation());
        ++Counted;
    }
    if (Counted == 0)
    {
        OutReason = FString::Printf(TEXT("no stations matched '%s'"), *Wanted);
        return false;
    }

    const FVector Centre = Bounds.GetCenter();
    const FVector Size = Bounds.GetSize();

    // Solve the distance from the camera's field of view against the footprint
    // diagonal, instead of scaling a guessed multiplier. A long department
    // framed at an arbitrary angle puts most of its stations outside the frame,
    // which is exactly why earlier department shots looked like empty floor.
    constexpr double ManagementFovDegrees = 78.0;
    const double HalfFov = FMath::DegreesToRadians(ManagementFovDegrees * 0.5);
    const double Diagonal =
        FMath::Sqrt(Size.X * Size.X + Size.Y * Size.Y);
    const double Distance = (bWIP
        ? 1500.0
        : (FMath::Max(Diagonal, 900.0) * 0.5) / FMath::Tan(HalfFov) * 1.16)
        * DistanceScale;

    // Route order gives the line's axis directly: first station to last.
    FVector LineDir(1.0, 0.0, 0.0);
    if (Picked.Num() >= 2)
    {
        const FVector Flat(Picked.Last().X - Picked[0].X,
                           Picked.Last().Y - Picked[0].Y, 0.0);
        if (!Flat.IsNearlyZero())
        {
            LineDir = Flat.GetSafeNormal();
        }
    }
    // Stand off to one side and slightly down the line, so it reads in
    // perspective rather than as a flat elevation.
    const FVector Across(-LineDir.Y, LineDir.X, 0.0);
    const FVector ViewDir = (Across + LineDir * 0.45).GetSafeNormal();

    // A consistent management pitch by default, so every department is shot
    // the same way; close-up tours may override it per stop.
    const double Pitch = FMath::DegreesToRadians(PitchDegrees);
    const FVector Eye = Centre
        - ViewDir * (Distance * FMath::Cos(Pitch))
        + FVector(0.0, 0.0, Distance * FMath::Sin(Pitch));
    // Aim above the floor so machines fill the frame, not concrete.
    const FVector Target = Centre + FVector(0.0, 0.0, 260.0);

    APlayerController* Controller = World->GetFirstPlayerController();
    if (!Controller)
    {
        OutReason = TEXT("NO PLAYER CONTROLLER");
        return false;
    }

    // Roof visibility follows the camera: a management shot from above the
    // eaves needs the roof out of the way, a floor-level close-up needs it
    // back or the frame tops out in black void.
    constexpr double RoofHideAboveZCm = 900.0;
    FString RoofReason;
    SetRoofHidden(WorldContextObject, Eye.Z > RoofHideAboveZCm,
        RoofHideAboveZCm, RoofReason);

    // One dev camera per world: every framing used to leak a live camera
    // actor.
    static const FName DevCameraTag(TEXT("LB.OneFactory.DevCamera"));
    for (TActorIterator<ACameraActor> It(World); It; ++It)
    {
        if (IsValid(*It) && It->Tags.Contains(DevCameraTag))
        {
            It->Destroy();
        }
    }

    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    ACameraActor* Camera = World->SpawnActor<ACameraActor>(
        ACameraActor::StaticClass(), Eye,
        (Target - Eye).Rotation(), Params);
    if (!Camera)
    {
        OutReason = TEXT("COULD NOT SPAWN VIEW CAMERA");
        return false;
    }
    if (UCameraComponent* Lens = Camera->GetCameraComponent())
    {
        Lens->SetFieldOfView(static_cast<float>(ManagementFovDegrees));
        // Fixed exposure per the factory-wide lighting standard: bias -0.50,
        // clamped so the view cannot auto-adapt into blown or crushed frames.
        // "Fixed exposure bias -0.50" per the standard means the bias is
        // pinned, not that eye adaptation is disabled - clamping the
        // adaptation range to a constant turned every interior black.
        Lens->PostProcessSettings.bOverride_AutoExposureBias = true;
        Lens->PostProcessSettings.AutoExposureBias = -0.5f;
        Lens->PostProcessBlendWeight = 1.0f;
    }
    Camera->Tags.AddUnique(TEXT("LB.OneFactory.DevCamera"));
    Controller->SetViewTargetWithBlend(Camera, 0.0f);

    OutReason = FString::Printf(
        TEXT("framed %d %s station(s); footprint %.0fx%.0f; distance=%.0f"),
        Counted, *Wanted, Size.X, Size.Y, Distance);
    return true;
}

namespace LBOneFactoryRoofPrivate
{
    struct FRoofState
    {
        TSet<TWeakObjectPtr<UStaticMeshComponent>> Hidden;
        bool bHidden = false;
    };
    static TMap<TWeakObjectPtr<UWorld>, FRoofState> GStatePerWorld;
}

bool ULBOneFactoryDevFactory::IsRoofHidden(UObject* WorldContextObject)
{
    UWorld* World = ResolveWorld(WorldContextObject);
    const LBOneFactoryRoofPrivate::FRoofState* State =
        World ? LBOneFactoryRoofPrivate::GStatePerWorld.Find(World) : nullptr;
    return State && State->bHidden;
}

bool ULBOneFactoryDevFactory::SetRoofHidden(UObject* WorldContextObject,
    const bool bHidden, const double AboveZCm, FString& OutReason)
{
    UWorld* World = ResolveWorld(WorldContextObject);
    if (!World)
    {
        OutReason = TEXT("NO WORLD");
        return false;
    }

    // Remember what was hidden so the toggle is exactly reversible rather
    // than guessing again on the way back. State is per world: PIE, editor
    // and reloaded worlds must never restore or mutate each other's roofs.
    for (auto It = LBOneFactoryRoofPrivate::GStatePerWorld.CreateIterator();
        It; ++It)
    {
        if (!It->Key.IsValid())
        {
            It.RemoveCurrent();
        }
    }
    LBOneFactoryRoofPrivate::FRoofState& State =
        LBOneFactoryRoofPrivate::GStatePerWorld.FindOrAdd(World);
    State.bHidden = bHidden;

    int32 Changed = 0;
    if (!bHidden)
    {
        for (const TWeakObjectPtr<UStaticMeshComponent>& Weak : State.Hidden)
        {
            if (UStaticMeshComponent* Component = Weak.Get())
            {
                Component->SetVisibility(true, false);
                ++Changed;
            }
        }
        State.Hidden.Reset();
        OutReason = FString::Printf(TEXT("restored %d component(s)"), Changed);
        return true;
    }

    static const FName WipTag(TEXT("LB.OneFactory.WIPPresentation"));
    static const FName EnvTag(TEXT("LB.OneFactory.DevEnvelope"));
    static const FName DressTag(TEXT("LB.OneFactory.DevStationDressing"));
    // The restored shop's overhead crane, runway and trusses are release
    // content the owner asked to see - "also everything, the crains" - so
    // roof-hiding never touches them.
    static const FName ShopTag(TEXT("LB.OneFactory.DevRestoredShop"));

    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!IsValid(Actor) || Actor->Tags.Contains(WipTag)
            || Actor->Tags.Contains(EnvTag) || Actor->Tags.Contains(DressTag)
            || Actor->Tags.Contains(ShopTag))
        {
            continue;
        }
        for (UActorComponent* Component : Actor->GetComponents())
        {
            UStaticMeshComponent* Mesh = Cast<UStaticMeshComponent>(Component);
            if (!Mesh || !Mesh->GetStaticMesh() || !Mesh->IsVisible())
            {
                continue;
            }
            // Only structure that sits entirely above the working height, so
            // machines, floor and markings are never touched.
            const FBoxSphereBounds Bounds = Mesh->Bounds;
            const double LowestZ = Bounds.Origin.Z - Bounds.BoxExtent.Z;
            if (LowestZ < AboveZCm)
            {
                continue;
            }
            Mesh->SetVisibility(false, false);
            State.Hidden.Add(Mesh);
            ++Changed;
        }
    }

    OutReason = FString::Printf(
        TEXT("hid %d component(s) sitting entirely above %.0f cm"),
        Changed, AboveZCm);
    return true;
}

bool ULBOneFactoryDevFactory::ApplySemanticMaterials(
    UObject* WorldContextObject, FString& OutReason)
{
    UWorld* World = ResolveWorld(WorldContextObject);
    if (!World)
    {
        OutReason = TEXT("NO WORLD");
        return false;
    }

    UMaterialInterface* Base = Cast<UMaterialInterface>(StaticLoadObject(
        UMaterialInterface::StaticClass(), nullptr,
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")));
    if (!Base)
    {
        OutReason = TEXT("COULD NOT RESOLVE BASE MATERIAL");
        return false;
    }

    // Semantic slot name fragment -> colour, roughness, metallic.
    // Colours are BRAND_IDENTITY_AUTHORITY tokens. Safety Yellow and Signal Red
    // appear only where the authored slot name asks for a safety colour, so they
    // stay functional rather than becoming decoration.
    struct FSemantic
    {
        const TCHAR* Fragment;
        const TCHAR* Hex;
        float Roughness;
        float Metallic;
    };
    static const FSemantic Semantics[] = {
        { TEXT("CreamPaint"),      TEXT("F3F1E9"), 0.45f, 0.00f },
        { TEXT("EmeraldPanel"),    TEXT("1F4B44"), 0.38f, 0.00f },
        { TEXT("GraphiteTooling"), TEXT("202428"), 0.55f, 0.25f },
        { TEXT("SafetyYellow"),    TEXT("F2C300"), 0.50f, 0.00f },
        { TEXT("BlackMotor"),      TEXT("14171A"), 0.45f, 0.30f },
        { TEXT("BrushedSteel"),    TEXT("70777C"), 0.30f, 0.85f },
        // Broader fallbacks for the support kit and other native families.
        { TEXT("Steel"),           TEXT("70777C"), 0.32f, 0.80f },
        { TEXT("Emerald"),         TEXT("1F4B44"), 0.38f, 0.00f },
        { TEXT("Green"),           TEXT("1F4B44"), 0.38f, 0.00f },
        { TEXT("Graphite"),        TEXT("202428"), 0.55f, 0.25f },
        { TEXT("Charcoal"),        TEXT("202428"), 0.55f, 0.20f },
        { TEXT("Cream"),           TEXT("F3F1E9"), 0.45f, 0.00f },
        { TEXT("White"),           TEXT("F3F1E9"), 0.45f, 0.00f },
        { TEXT("Yellow"),          TEXT("F2C300"), 0.50f, 0.00f },
        { TEXT("Safety"),          TEXT("F2C300"), 0.50f, 0.00f },
        { TEXT("Red"),             TEXT("C7352C"), 0.45f, 0.00f },
        { TEXT("Signal"),          TEXT("C7352C"), 0.45f, 0.00f },
        { TEXT("Copper"),          TEXT("B46A3A"), 0.30f, 0.85f },
        { TEXT("Electrode"),       TEXT("B46A3A"), 0.30f, 0.85f },
        { TEXT("Glass"),           TEXT("BFD4DE"), 0.12f, 0.00f },
        { TEXT("Rubber"),          TEXT("24272A"), 0.75f, 0.00f },
        { TEXT("Motor"),           TEXT("14171A"), 0.45f, 0.30f },
    };

    TMap<FString, UMaterialInstanceDynamic*> Cache;
    TSet<FString> Unmatched;
    int32 Bound = 0;
    int32 Components = 0;
    int32 AlreadyAuthored = 0;

    // Our own dev actors already carry deliberate materials; leave them alone.
    static const FName WipTag(TEXT("LB.OneFactory.WIPPresentation"));
    static const FName EnvTag(TEXT("LB.OneFactory.DevEnvelope"));

    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!IsValid(Actor) || Actor->Tags.Contains(WipTag)
            || Actor->Tags.Contains(EnvTag))
        {
            continue;
        }
        for (UActorComponent* Component : Actor->GetComponents())
        {
            UStaticMeshComponent* Mesh = Cast<UStaticMeshComponent>(Component);
            if (!Mesh || !Mesh->GetStaticMesh())
            {
                continue;
            }
            const TArray<FStaticMaterial>& Slots =
                Mesh->GetStaticMesh()->GetStaticMaterials();
            if (Slots.Num() == 0)
            {
                continue;
            }
            ++Components;
            for (int32 Index = 0; Index < Slots.Num(); ++Index)
            {
                // Only fill genuinely unbound slots. Several native families
                // (the press trains, the paint line, the oven) already carry
                // authored materials, and overwriting those would make the
                // factory worse, not better.
                if (Slots[Index].MaterialInterface != nullptr)
                {
                    ++AlreadyAuthored;
                    continue;
                }
                const FString SlotName = Slots[Index].MaterialSlotName.ToString();
                const FSemantic* Match = nullptr;
                for (const FSemantic& Candidate : Semantics)
                {
                    if (SlotName.Contains(Candidate.Fragment,
                            ESearchCase::IgnoreCase))
                    {
                        Match = &Candidate;
                        break;
                    }
                }
                if (!Match)
                {
                    Unmatched.Add(SlotName);
                    continue;
                }
                UMaterialInstanceDynamic** Found = Cache.Find(Match->Fragment);
                UMaterialInstanceDynamic* Material =
                    Found ? *Found : nullptr;
                if (!Material)
                {
                    Material = UMaterialInstanceDynamic::Create(Base, Actor);
                    if (!Material)
                    {
                        continue;
                    }
                    const FLinearColor Colour = FLinearColor::FromSRGBColor(
                        FColor::FromHex(Match->Hex));
                    Material->SetVectorParameterValue(TEXT("Color"), Colour);
                    Material->SetVectorParameterValue(TEXT("BaseColor"), Colour);
                    // Applied best-effort: BasicShapeMaterial may expose no
                    // such scalars, in which case these are simply ignored.
                    Material->SetScalarParameterValue(TEXT("Roughness"),
                        Match->Roughness);
                    Material->SetScalarParameterValue(TEXT("Metallic"),
                        Match->Metallic);
                    Cache.Add(Match->Fragment, Material);
                }
                Mesh->SetMaterial(Index, Material);
                ++Bound;
            }
        }
    }

    TArray<FString> UnmatchedList = Unmatched.Array();
    UnmatchedList.Sort();
    OutReason = FString::Printf(
        TEXT("bound %d empty slot(s) across %d component(s); left %d authored "
             "slot(s) alone; %d distinct material(s); unmatched: %s"),
        Bound, Components, AlreadyAuthored, Cache.Num(),
        UnmatchedList.Num() == 0
            ? TEXT("none")
            : *FString::Join(UnmatchedList, TEXT(", ")));
    return true;
}

bool ULBOneFactoryDevFactory::BuildBodyWeldReport(UObject* WorldContextObject,
    FString& OutReport)
{
    UWorld* World = ResolveWorld(WorldContextObject);
    if (!World)
    {
        OutReport = TEXT("NO WORLD");
        return false;
    }
    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(World);
    ALBOneFactoryProductionFlowAuthority* Production = FindProductionFlow(World);
    if (!Coordinator || !Production)
    {
        OutReport = TEXT("NEED EXACTLY ONE COORDINATOR AND PRODUCTION FLOW");
        return false;
    }

    TArray<FLBOneFactoryRuntimeStationStep> Route;
    FName TopologyId = NAME_None;
    FString RouteReason;
    if (!Coordinator->GetConfiguredStationRoute(Route, TopologyId, RouteReason))
    {
        OutReport = FString::Printf(TEXT("route unavailable: %s"), *RouteReason);
        return false;
    }

    const UEnum* StageEnum = StaticEnum<ELBOneFactoryVehicleStage>();
    TMap<FName, const FLBOneFactoryVehicleUnitState*> UnitsByStation;
    const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        if (!Unit.bDispatched && Unit.CurrentStationId != NAME_None)
        {
            UnitsByStation.Add(Unit.CurrentStationId, &Unit);
        }
    }

    TArray<FString> Lines;
    Lines.Add(TEXT("Body/Weld line - Moorcross Works"));
    for (const FLBOneFactoryRuntimeStationStep& Step : Route)
    {
        if (Step.Department != ELBOneFactoryDepartment::Body)
        {
            continue;
        }
        const FLBOneFactoryVehicleUnitState* const* Occupant =
            UnitsByStation.Find(Step.StationId);
        const FString Work = Step.ConfiguredWorkIds.Num() > 0
            ? FString::JoinBy(Step.ConfiguredWorkIds, TEXT(","),
                [](const FName& Id) { return Id.ToString(); })
            : FString(TEXT("PASS_THROUGH"));
        Lines.Add(FString::Printf(TEXT("  %02d %-28s %-24s %s%s"),
            Step.RouteIndex, *Step.StationId.ToString(), *Work,
            Occupant ? *(*Occupant)->UnitId.ToString() : TEXT("-"),
            Step.bQualityGate ? TEXT("  [QUALITY GATE]") : TEXT("")));
        if (Occupant)
        {
            Lines[Lines.Num() - 1] += FString::Printf(TEXT("  (%s)"),
                *EnumName(StageEnum,
                    static_cast<int64>((*Occupant)->Stage)));
        }
    }
    OutReport = FString::Join(Lines, TEXT("\n"));
    return true;
}

// ---------------------------------------------------------------------------
// Timed visual tour.
// ---------------------------------------------------------------------------

ALBOneFactoryDevTourActor::ALBOneFactoryDevTourActor()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    SetReplicates(false);
    SetActorEnableCollision(false);
}

void ALBOneFactoryDevTourActor::BeginTour(const TArray<FString>& InDepartments,
    const int32 InSettleFrames, const float InSecondsPerStop,
    const FString& InLabel)
{
    Departments = InDepartments;
    SettleFrames = FMath::Max(1, InSettleFrames);
    SecondsPerStop = FMath::Max(0.0f, InSecondsPerStop);
    Label = InLabel;
    StopIndex = INDEX_NONE;
    FrameCounter = 0;
    bAwaitingCapture = false;
    bFinished = false;
}

void ALBOneFactoryDevTourActor::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bFinished || Departments.Num() == 0)
    {
        return;
    }

    if (FrameCounter > 0)
    {
        --FrameCounter;
        return;
    }

    if (bAwaitingCapture)
    {
        FString Name = FString::Printf(TEXT("%s_%02d_%s"), *Label,
            StopIndex + 1, *Departments[StopIndex]);
        // A dot in a close-up stop like Press@0.3~20 would read as a file
        // extension and cost the shot its .png suffix.
        Name.ReplaceInline(TEXT("."), TEXT("p"));
        FScreenshotRequest::RequestScreenshot(Name, false, false);
        UE_LOG(LogLineBossOneFactoryDev, Display,
            TEXT("LINE_BOSS_DEV_TOUR_SHOT %s"), *Name);
        bAwaitingCapture = false;
        FrameCounter = 8;
        return;
    }

    ++StopIndex;
    if (!Departments.IsValidIndex(StopIndex))
    {
        bFinished = true;
        UE_LOG(LogLineBossOneFactoryDev, Display,
            TEXT("LINE_BOSS_DEV_TOUR_COMPLETE stops=%d"), Departments.Num());
        // The tour is one-shot; a finished tour actor lingering in the world
        // would re-run on the next BeginTour call against stale state.
        Destroy();
        return;
    }

    // Advance the line exactly once per stop, so successive shots show real
    // movement at the promised simulated seconds per stop (the old per-tick
    // advance ran ~39x faster than the console usage stated).
    if (SecondsPerStop > 0.0f && StopIndex > 0)
    {
        int32 Processed = 0;
        FString RunReason;
        ULBOneFactoryDevFactory::AdvanceFactory(this, SecondsPerStop, true,
            Processed, RunReason);
    }

    FString ViewReason;
    ULBOneFactoryDevFactory::FrameProductionLine(this,
        Departments[StopIndex], ViewReason);
    UE_LOG(LogLineBossOneFactoryDev, Display,
        TEXT("LINE_BOSS_DEV_TOUR_STOP %s :: %s"), *Departments[StopIndex],
        *ViewReason);
    bAwaitingCapture = true;
    FrameCounter = SettleFrames;
}

// ---------------------------------------------------------------------------
// Console surface.
//
// Registered as plain console commands rather than exec functions so they work
// identically in the editor, in a standalone -game session and from -ExecCmds
// in an unattended run.
// ---------------------------------------------------------------------------

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryBuildWholeFactory(
    TEXT("LB.OneFactory.BuildWholeFactory"),
    TEXT("Creates and commissions Press, Body/Weld, Paint and Assembly, then "
         "validates the 57-station route."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            FString Reason;
            const bool bOk =
                ULBOneFactoryDevFactory::BuildAndCommissionWholeFactory(
                    World, Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_BUILD_WHOLE_FACTORY ok=%d %s"),
                bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryStartProduction(
    TEXT("LB.OneFactory.StartProduction"),
    TEXT("Usage: LB.OneFactory.StartProduction [count=1]. Creates and starts "
         "vehicle build orders on the commissioned line."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            const int32 Count = Args.Num() > 0
                ? FMath::Max(1, FCString::Atoi(*Args[0])) : 1;
            FString Reason;
            const bool bOk = ULBOneFactoryDevFactory::StartDemoProduction(
                World, Count, Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_START_PRODUCTION ok=%d %s"),
                bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryAdvance(
    TEXT("LB.OneFactory.Advance"),
    TEXT("Usage: LB.OneFactory.Advance [seconds=1] [autoPassQA=1]. Advances "
         "every started unit by the given deterministic time."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            const float Seconds = Args.Num() > 0
                ? FCString::Atof(*Args[0]) : 1.0f;
            const bool bAutoPass = Args.Num() > 1
                ? FCString::Atoi(*Args[1]) != 0 : true;
            int32 Processed = 0;
            FString Reason;
            const bool bOk = ULBOneFactoryDevFactory::AdvanceFactory(
                World, Seconds, bAutoPass, Processed, Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_ADVANCE ok=%d processed=%d %s"),
                bOk ? 1 : 0, Processed, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryRun(
    TEXT("LB.OneFactory.Run"),
    TEXT("Usage: LB.OneFactory.Run [iterations=600] [stepSeconds=1] "
         "[autoPassQA=1]. Deterministically runs the whole line."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            const int32 Iterations = Args.Num() > 0
                ? FMath::Max(1, FCString::Atoi(*Args[0])) : 600;
            const float StepSeconds = Args.Num() > 1
                ? FCString::Atof(*Args[1]) : 1.0f;
            const bool bAutoPass = Args.Num() > 2
                ? FCString::Atoi(*Args[2]) != 0 : true;
            FString Reason;
            const bool bOk = ULBOneFactoryDevFactory::RunFactory(
                World, Iterations, StepSeconds, bAutoPass, Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_RUN ok=%d %s"), bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryStatus(
    TEXT("LB.OneFactory.Status"),
    TEXT("Prints the configured route summary and every unit's progress."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            FString Report;
            ULBOneFactoryDevFactory::BuildFactoryStatusReport(World, Report);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_STATUS\n%s"), *Report);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryLight(
    TEXT("LB.OneFactory.Light"),
    TEXT("Usage: LB.OneFactory.Light [intensity=8]. Spawns runtime-only "
         "directional and sky lighting sized for the whole site."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            const float Intensity = Args.Num() > 0
                ? FCString::Atof(*Args[0]) : 8.0f;
            FString Reason;
            const bool bOk = ULBOneFactoryDevFactory::EnsureDevLighting(
                World, Intensity, Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_LIGHT ok=%d %s"), bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryView(
    TEXT("LB.OneFactory.View"),
    TEXT("Usage: LB.OneFactory.View [Press|Body|Paint|Assembly|All]. Frames "
         "the configured route."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            const FString Department = Args.Num() > 0 ? Args[0] : TEXT("All");
            FString Reason;
            const bool bOk = ULBOneFactoryDevFactory::FrameProductionLine(
                World, Department, Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_VIEW ok=%d %s"), bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryEDLinePreview(
    TEXT("LB.OneFactory.EDLinePreview"),
    TEXT("Usage: LB.OneFactory.EDLinePreview [standing=1]. Stands the ED "
         "line as the owner's reference draws it: carrier gantry bays over "
         "the tank row at pretreatment and ED coat, then oven segments "
         "end-to-end through the cure stations. Preview only - nothing is "
         "committed to the frozen paint contract."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            if (!World)
            {
                return;
            }
            static const FName PreviewTag(TEXT("LB.OneFactory.EDLinePreview"));
            const bool bStanding = Args.Num() < 1
                || FCString::Atoi(*Args[0]) != 0;
            int32 Removed = 0;
            for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
            {
                if (IsValid(*It) && It->Tags.Contains(PreviewTag))
                {
                    It->Destroy();
                    ++Removed;
                }
            }
            if (!bStanding)
            {
                UE_LOG(LogLineBossOneFactoryDev, Display,
                    TEXT("LINE_BOSS_DEV_ED_LINE_PREVIEW standing=0 "
                         "removed=%d"), Removed);
                return;
            }

            ALBOneFactoryRuntimeCoordinator* Coordinator =
                ULBOneFactoryDevFactory::FindCoordinator(World);
            TArray<FLBOneFactoryRuntimeStationStep> Route;
            FName TopologyId = NAME_None;
            FString Reason;
            if (!Coordinator
                || !Coordinator->GetConfiguredStationRoute(Route, TopologyId,
                        Reason))
            {
                UE_LOG(LogLineBossOneFactoryDev, Warning,
                    TEXT("LINE_BOSS_DEV_ED_LINE_PREVIEW no route: %s"),
                    *Reason);
                return;
            }
            UStaticMesh* Gantry = Cast<UStaticMesh>(StaticLoadObject(
                UStaticMesh::StaticClass(), nullptr,
                TEXT("/Game/LineBoss/Candidates/PaintShop/EDLineGantry_v001"
                     "/SM_LB_EDLine_CarrierGantryBay_v001")));
            UStaticMesh* Oven = Cast<UStaticMesh>(StaticLoadObject(
                UStaticMesh::StaticClass(), nullptr,
                TEXT("/Game/LineBoss/Candidates/PaintShop/EDLineOven_v002"
                     "/SM_LB_EDLine_OvenSegment_v002")));
            if (!Gantry || !Oven)
            {
                UE_LOG(LogLineBossOneFactoryDev, Warning,
                    TEXT("LINE_BOSS_DEV_ED_LINE_PREVIEW meshes unresolved"));
                return;
            }

            auto Stand = [&](UStaticMesh* Mesh, const FVector& Where,
                const FRotator& Rotation)
            {
                FActorSpawnParameters Params;
                Params.SpawnCollisionHandlingOverride =
                    ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
                AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(
                    AStaticMeshActor::StaticClass(), Where, Rotation, Params);
                if (!Actor)
                {
                    return false;
                }
                Actor->Tags.AddUnique(PreviewTag);
                if (UStaticMeshComponent* Component =
                        Actor->GetStaticMeshComponent())
                {
                    Component->SetMobility(EComponentMobility::Movable);
                    Component->SetStaticMesh(Mesh);
                    Component->SetCollisionEnabled(
                        ECollisionEnabled::NoCollision);
                }
                return true;
            };

            // Gantry bays straddle the authored tank pitch of 324 cm at the
            // two wet stages; oven segments tile through the cure stages.
            int32 Gantries = 0;
            int32 Ovens = 0;
            for (const FLBOneFactoryRuntimeStationStep& Step : Route)
            {
                const FVector At = Step.WorldTransform.GetLocation();
                const FRotator Facing = Step.WorldTransform.Rotator();
                const FVector Along =
                    Step.WorldTransform.GetRotation().GetForwardVector();
                if (Step.SemanticStage
                        == ELBOneFactoryVehicleStage::Pretreatment
                    || Step.SemanticStage
                        == ELBOneFactoryVehicleStage::EDCoat)
                {
                    for (int32 Bay = -1; Bay <= 1; ++Bay)
                    {
                        if (Stand(Gantry, At + Along * (324.0 * Bay), Facing))
                        {
                            ++Gantries;
                        }
                    }
                }
                else if (Step.SemanticStage
                    == ELBOneFactoryVehicleStage::Cure)
                {
                    for (int32 Bay = -2; Bay <= 2; ++Bay)
                    {
                        if (Stand(Oven, At + Along * (355.0 * Bay), Facing))
                        {
                            ++Ovens;
                        }
                    }
                }
            }
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_ED_LINE_PREVIEW standing=1 gantries=%d "
                     "ovenSegments=%d removed=%d"),
                Gantries, Ovens, Removed);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryPaintEDPreview(
    TEXT("LB.OneFactory.PaintEDPreview"),
    TEXT("Usage: LB.OneFactory.PaintEDPreview [standing=1] [stations=all]. "
         "Stands the commissioned ED dip tunnel at the ED coat stations for "
         "comparison against the presentation's tracked open ED line, which "
         "it encloses. A preview only - nothing is committed to the frozen "
         "paint contract. 'stations' may be 'all', 'first' or 'second' so "
         "one station can show the enclosure while the other shows the open "
         "line."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            if (!World)
            {
                return;
            }
            static const FName PreviewTag(
                TEXT("LB.OneFactory.PaintEDPreview"));
            const bool bStanding = Args.Num() < 1
                || FCString::Atoi(*Args[0]) != 0;
            const FString Which = Args.Num() > 1 ? Args[1] : TEXT("all");

            int32 Removed = 0;
            for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
            {
                if (IsValid(*It) && It->Tags.Contains(PreviewTag))
                {
                    It->Destroy();
                    ++Removed;
                }
            }
            if (!bStanding)
            {
                UE_LOG(LogLineBossOneFactoryDev, Display,
                    TEXT("LINE_BOSS_DEV_PAINT_ED_PREVIEW standing=0 "
                         "removed=%d"), Removed);
                return;
            }

            ALBOneFactoryRuntimeCoordinator* Coordinator =
                ULBOneFactoryDevFactory::FindCoordinator(World);
            TArray<FLBOneFactoryRuntimeStationStep> Route;
            FName TopologyId = NAME_None;
            FString Reason;
            if (!Coordinator
                || !Coordinator->GetConfiguredStationRoute(Route, TopologyId,
                        Reason))
            {
                UE_LOG(LogLineBossOneFactoryDev, Warning,
                    TEXT("LINE_BOSS_DEV_PAINT_ED_PREVIEW no route: %s"),
                    *Reason);
                return;
            }
            UStaticMesh* Tunnel = Cast<UStaticMesh>(StaticLoadObject(
                UStaticMesh::StaticClass(), nullptr,
                TEXT("/Game/LineBoss/Candidates/PaintShop/EDDipTunnel_v001"
                     "/SM_LB_Paint_EDDipTunnel_v001")));
            if (!Tunnel)
            {
                UE_LOG(LogLineBossOneFactoryDev, Warning,
                    TEXT("LINE_BOSS_DEV_PAINT_ED_PREVIEW tunnel mesh "
                         "unresolved"));
                return;
            }

            int32 EDIndex = 0;
            int32 Placed = 0;
            for (const FLBOneFactoryRuntimeStationStep& Step : Route)
            {
                if (Step.SemanticStage
                    != ELBOneFactoryVehicleStage::EDCoat)
                {
                    continue;
                }
                const int32 ThisIndex = EDIndex++;
                if ((Which.Equals(TEXT("first"), ESearchCase::IgnoreCase)
                        && ThisIndex != 0)
                    || (Which.Equals(TEXT("second"), ESearchCase::IgnoreCase)
                        && ThisIndex != 1))
                {
                    continue;
                }
                FActorSpawnParameters Params;
                Params.SpawnCollisionHandlingOverride =
                    ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
                AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(
                    AStaticMeshActor::StaticClass(),
                    Step.WorldTransform.GetLocation(),
                    Step.WorldTransform.Rotator(), Params);
                if (!Actor)
                {
                    continue;
                }
                Actor->Tags.AddUnique(PreviewTag);
                if (UStaticMeshComponent* Mesh =
                        Actor->GetStaticMeshComponent())
                {
                    Mesh->SetMobility(EComponentMobility::Movable);
                    Mesh->SetStaticMesh(Tunnel);
                    Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
                }
                ++Placed;
            }
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_PAINT_ED_PREVIEW standing=1 which=%s "
                     "placed=%d removed=%d edStations=%d"),
                *Which, Placed, Removed, EDIndex);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryPressBlockout(
    TEXT("LB.OneFactory.PressBlockout"),
    TEXT("Usage: LB.OneFactory.PressBlockout [visible=0]. The detailed-press "
         "recovery design says the 268-primitive blockout batches must no "
         "longer render once the detailed train stands at the station; this "
         "hides or restores them, visibility only."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            if (!World)
            {
                return;
            }
            const bool bVisible = Args.Num() > 0
                && FCString::Atoi(*Args[0]) != 0;
            int32 Changed = 0;
            for (TActorIterator<ALBOneFactoryPressStarterPresentationActor>
                It(World); It; ++It)
            {
                if (IsValid(*It))
                {
                    It->SetActorHiddenInGame(!bVisible);
                    ++Changed;
                }
            }
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_PRESS_BLOCKOUT visible=%d actors=%d"),
                bVisible ? 1 : 0, Changed);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryRoof(
    TEXT("LB.OneFactory.Roof"),
    TEXT("Usage: LB.OneFactory.Roof [hidden=1] [aboveCm=900]. Hides or restores "
         "structure sitting entirely above the working height, so roof beams do "
         "not slice across the management view."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            const bool bHidden = Args.Num() > 0
                ? FCString::Atoi(*Args[0]) != 0 : true;
            const double AboveZ = Args.Num() > 1
                ? FCString::Atod(*Args[1]) : 900.0;
            FString Reason;
            const bool bOk = ULBOneFactoryDevFactory::SetRoofHidden(
                World, bHidden, AboveZ, Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_ROOF ok=%d %s"), bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryRestoredShop(
    TEXT("LB.OneFactory.RestoredShop"),
    TEXT("Rebuilds the complete restored press-shop surroundings - crane, "
         "guarding, grates, lamps, pipework, logistics - around the press "
         "datum from the read-only reference manifest."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            if (!World)
            {
                return;
            }
            ALBOneFactoryDevRestoredShopActor* Existing = nullptr;
            for (TActorIterator<ALBOneFactoryDevRestoredShopActor> It(World);
                It; ++It)
            {
                if (IsValid(*It)) { Existing = *It; break; }
            }
            if (!Existing)
            {
                FActorSpawnParameters Params;
                Params.SpawnCollisionHandlingOverride =
                    ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
                Existing =
                    World->SpawnActor<ALBOneFactoryDevRestoredShopActor>(
                        ALBOneFactoryDevRestoredShopActor::StaticClass(),
                        FVector::ZeroVector, FRotator::ZeroRotator, Params);
            }
            FString Reason;
            const bool bOk = Existing && Existing->BuildFromManifest(Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_RESTORED_SHOP ok=%d %s"),
                bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryDressing(
    TEXT("LB.OneFactory.Dressing"),
    TEXT("Dresses every configured station into a working cell: zone pad, "
         "safety guarding, control cabinet, status beacon, and an overhead beam "
         "at each quality gate."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            if (!World)
            {
                return;
            }
            ALBOneFactoryDevStationDressingActor* Existing = nullptr;
            for (TActorIterator<ALBOneFactoryDevStationDressingActor> It(World);
                It; ++It)
            {
                if (IsValid(*It)) { Existing = *It; break; }
            }
            if (!Existing)
            {
                FActorSpawnParameters Params;
                Params.SpawnCollisionHandlingOverride =
                    ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
                Existing =
                    World->SpawnActor<ALBOneFactoryDevStationDressingActor>(
                        ALBOneFactoryDevStationDressingActor::StaticClass(),
                        FVector::ZeroVector, FRotator::ZeroRotator, Params);
            }
            FString Reason;
            const bool bOk = Existing && Existing->BuildFromRoute(Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_DRESSING ok=%d %s"), bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryHUD(
    TEXT("LB.OneFactory.HUD"),
    TEXT("Swaps in the production-flow HUD: top bar, seven-stage flow strip and "
         "alert toasts, all read from the coordinator and ledger."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            APlayerController* Controller =
                World ? World->GetFirstPlayerController() : nullptr;
            if (!Controller)
            {
                UE_LOG(LogLineBossOneFactoryDev, Error,
                    TEXT("LINE_BOSS_DEV_HUD no player controller"));
                return;
            }
            if (AHUD* Old = Controller->GetHUD())
            {
                Old->Destroy();
            }
            FActorSpawnParameters Params;
            Params.Owner = Controller;
            Params.Instigator = Controller->GetInstigator();
            Params.SpawnCollisionHandlingOverride =
                ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
            ALBOneFactoryProductionHUD* Hud =
                World->SpawnActor<ALBOneFactoryProductionHUD>(
                    ALBOneFactoryProductionHUD::StaticClass(), Params);
            if (Hud)
            {
                Controller->MyHUD = Hud;
            }
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_HUD ok=%d"), Hud ? 1 : 0);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryMaterials(
    TEXT("LB.OneFactory.Materials"),
    TEXT("Binds a brand material to every authored semantic material slot in "
         "the world. The import lanes leave these slots unbound, so the whole "
         "factory otherwise renders in default grey."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            FString Reason;
            const bool bOk = ULBOneFactoryDevFactory::ApplySemanticMaterials(
                World, Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_MATERIALS ok=%d %s"), bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryEnvelope(
    TEXT("LB.OneFactory.Envelope"),
    TEXT("Usage: LB.OneFactory.Envelope [paddingCm=6000] [heightCm=2200]. "
         "Encloses the site with walls, a ceiling deck and roof glazing so it "
         "reads as a factory interior instead of a lit plane. 2200 cm eaves "
         "clear the restored shop's truss top chords (~2000 cm)."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            if (!World)
            {
                return;
            }
            const double Padding = Args.Num() > 0
                ? FCString::Atod(*Args[0]) : 6000.0;
            const double Height = Args.Num() > 1
                ? FCString::Atod(*Args[1]) : 2200.0;
            ALBOneFactoryDevEnvelopeActor* Existing = nullptr;
            for (TActorIterator<ALBOneFactoryDevEnvelopeActor> It(World);
                It; ++It)
            {
                if (IsValid(*It)) { Existing = *It; break; }
            }
            if (!Existing)
            {
                FActorSpawnParameters Params;
                Params.SpawnCollisionHandlingOverride =
                    ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
                Existing = World->SpawnActor<ALBOneFactoryDevEnvelopeActor>(
                    ALBOneFactoryDevEnvelopeActor::StaticClass(),
                    FVector::ZeroVector, FRotator::ZeroRotator, Params);
            }
            FString Reason;
            const bool bOk = Existing
                && Existing->BuildFromRoute(Padding, Height, Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_ENVELOPE ok=%d %s"), bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryShowWIP(
    TEXT("LB.OneFactory.ShowWIP"),
    TEXT("Spawns the presentation-only WIP view so live units are drawn at "
         "their current station, changing appearance by stage."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            if (!World)
            {
                return;
            }
            for (TActorIterator<ALBOneFactoryWIPPresentationActor> It(World);
                It; ++It)
            {
                if (IsValid(*It))
                {
                    UE_LOG(LogLineBossOneFactoryDev, Display,
                        TEXT("LINE_BOSS_DEV_SHOW_WIP already present"));
                    return;
                }
            }
            FActorSpawnParameters Params;
            Params.SpawnCollisionHandlingOverride =
                ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
            ALBOneFactoryWIPPresentationActor* Wip =
                World->SpawnActor<ALBOneFactoryWIPPresentationActor>(
                    ALBOneFactoryWIPPresentationActor::StaticClass(),
                    FVector::ZeroVector, FRotator::ZeroRotator, Params);
            FString Reason;
            const bool bOk = Wip && Wip->RefreshFromLedger(Reason);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_SHOW_WIP ok=%d %s"), bOk ? 1 : 0, *Reason);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryTour(
    TEXT("LB.OneFactory.Tour"),
    TEXT("Usage: LB.OneFactory.Tour [label=Tour] [settleFrames=30] "
         "[secondsPerStop=2] [stop...]. Without explicit stops, captures All, "
         "Press, Body, Paint and Assembly. A stop accepts the close-up "
         "syntax, e.g. Press@0.25~16."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            if (!World)
            {
                return;
            }
            const FString Label = Args.Num() > 0 ? Args[0] : TEXT("Tour");
            const int32 Settle = Args.Num() > 1
                ? FMath::Max(1, FCString::Atoi(*Args[1])) : 30;
            const float PerStop = Args.Num() > 2
                ? FCString::Atof(*Args[2]) : 2.0f;
            FActorSpawnParameters Params;
            Params.SpawnCollisionHandlingOverride =
                ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
            ALBOneFactoryDevTourActor* Tour =
                World->SpawnActor<ALBOneFactoryDevTourActor>(
                    ALBOneFactoryDevTourActor::StaticClass(),
                    FVector::ZeroVector, FRotator::ZeroRotator, Params);
            if (!Tour)
            {
                UE_LOG(LogLineBossOneFactoryDev, Error,
                    TEXT("LINE_BOSS_DEV_TOUR could not spawn tour actor"));
                return;
            }
            TArray<FString> Stops;
            for (int32 Index = 3; Index < Args.Num(); ++Index)
            {
                Stops.Add(Args[Index]);
            }
            if (Stops.Num() == 0)
            {
                Stops = { TEXT("All"), TEXT("Press"), TEXT("Body"),
                    TEXT("Paint"), TEXT("Assembly") };
            }
            Tour->BeginTour(Stops, Settle, PerStop, Label);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_TOUR started label=%s settle=%d"),
                *Label, Settle);
        }));

static FAutoConsoleCommandWithWorldAndArgs GLBOneFactoryBodyWeld(
    TEXT("LB.OneFactory.BodyWeld"),
    TEXT("Prints the Body/Weld line: every position, its configured duty and "
         "the unit standing in it."),
    FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(
        [](const TArray<FString>& Args, UWorld* World)
        {
            FString Report;
            ULBOneFactoryDevFactory::BuildBodyWeldReport(World, Report);
            UE_LOG(LogLineBossOneFactoryDev, Display,
                TEXT("LINE_BOSS_DEV_BODYWELD\n%s"), *Report);
        }));
