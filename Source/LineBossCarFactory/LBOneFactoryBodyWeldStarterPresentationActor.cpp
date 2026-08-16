#include "LBOneFactoryBodyWeldStarterPresentationActor.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "LBBodyShopRobotActor.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"

#include <initializer_list>

namespace LBOneFactoryBodyWeldPresentationPrivate
{
    constexpr int32 ExpectedBatchCount = static_cast<int32>(
        ELBOneFactoryBodyWeldPresentationBatch::BatchCount);
    constexpr int32 CanonicalInstanceCount = 597;

    /**
     * The dress pack rides every robot at a uniform 0.68: the PR004 trio's
     * 186 cm upper tube, measured in Blender, fits the weld robot's 125 cm
     * links at exactly that ratio.
     */
    constexpr float DressPackScale = 0.68f;
    constexpr float TransformTolerance = 0.01f;

    /**
     * The frozen PROCESS-phase contact poses (LEFT side) from the native
     * pack's own FK validation:
     * SourceAssets/Candidate/WeldShop/BodyShopRobotNative_v001/Audit/
     * contact_fk_validation_v001.json (18/18 contact passes, max distance
     * 10.0 cm, min direction dot 0.99999998). The RIGHT side is the exact
     * mirror: J1, J4 and J6 negate.
     */
    constexpr float ContactProcessPoseDegrees[3][6] =
    {
        { 91.240831f, -24.935079f, 15.949661f, -8.509025f, 87.252369f,
          35.774566f },
        { 55.0f, -55.947736f, 70.469811f, 0.000001f, 61.000413f,
          -0.000005f },
        { 18.759169f, -24.935079f, 15.949661f, 8.509027f, 87.25237f,
          -35.774574f },
    };

    const TCHAR* BatchComponentNames[ExpectedBatchCount] =
    {
        TEXT("RobotBaseBatch"),
        TEXT("RobotJ1Batch"),
        TEXT("RobotJ2Batch"),
        TEXT("RobotJ3Batch"),
        TEXT("RobotJ4Batch"),
        TEXT("RobotJ5Batch"),
        TEXT("RobotJ6Batch"),
        TEXT("RobotOpenCGunBatch"),
        TEXT("RobotPanelPickToolBatch"),
        TEXT("RobotDressLowerBatch"),
        TEXT("RobotDressUpperBatch"),
        TEXT("RobotDressWristBatch"),
        TEXT("ComponentServicePalletBatch"),
        TEXT("ElectricalCabinetBatch"),
        TEXT("EmptyReturnCartBatch"),
        TEXT("ExtractionPedestalBatch"),
        TEXT("GuardGateBatch"),
        TEXT("GuardPanelBatch"),
        TEXT("HMIPedestalBatch"),
        TEXT("PanelStillageEmptyBatch"),
        TEXT("PanelStillageFullBatch"),
        TEXT("SmallPartsBinOpenBatch"),
        TEXT("SmallPartsCrateOpenBatch"),
        TEXT("UtilityPedestalBatch"),
        TEXT("ProgrammeFixtureFramingBatch"),
        TEXT("ProgrammeFixtureUnderbodyBatch"),
        TEXT("FloorRouteCubeBatch"),
        TEXT("RobotRoleCubeBatch"),
        TEXT("StatusCubeBatch")
    };

    const TCHAR* BatchMeshPaths[ExpectedBatchCount] =
    {
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_Base_v001.SM_LB_BodyShopRobotNative_Base_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J1_v001.SM_LB_BodyShopRobotNative_J1_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J2_v001.SM_LB_BodyShopRobotNative_J2_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J3_v001.SM_LB_BodyShopRobotNative_J3_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J4_v001.SM_LB_BodyShopRobotNative_J4_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J5_v001.SM_LB_BodyShopRobotNative_J5_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J6_v001.SM_LB_BodyShopRobotNative_J6_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001.SM_LB_BodyShopToolNative_OpenCGun_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001.SM_LB_BodyShopTool_PanelPick8Cup_v001"),
        TEXT("/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/Meshes/SM_LB_PR004_Robot_DressPackLower_v020.SM_LB_PR004_Robot_DressPackLower_v020"),
        TEXT("/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/Meshes/SM_LB_PR004_Robot_DressPackUpper_v020.SM_LB_PR004_Robot_DressPackUpper_v020"),
        TEXT("/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/Meshes/SM_LB_PR004_Robot_DressPackWrist_v020.SM_LB_PR004_Robot_DressPackWrist_v020"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_ComponentServicePallet_v002.SM_LB_BodyShopSupport_ComponentServicePallet_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Controls/SM_LB_BodyShopSupport_ElectricalCabinet_v002.SM_LB_BodyShopSupport_ElectricalCabinet_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_EmptyReturnCart_v002.SM_LB_BodyShopSupport_EmptyReturnCart_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Services/SM_LB_BodyShopSupport_ExtractionPedestal_v002.SM_LB_BodyShopSupport_ExtractionPedestal_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Safety/SM_LB_BodyShopSupport_GuardGate_2m_v002.SM_LB_BodyShopSupport_GuardGate_2m_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Safety/SM_LB_BodyShopSupport_GuardPanel_2m_v002.SM_LB_BodyShopSupport_GuardPanel_2m_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Controls/SM_LB_BodyShopSupport_HMIPedestal_v002.SM_LB_BodyShopSupport_HMIPedestal_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_PanelStillage_Empty_v002.SM_LB_BodyShopSupport_PanelStillage_Empty_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_PanelStillage_Full_v002.SM_LB_BodyShopSupport_PanelStillage_Full_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_SmallPartsBin_Open_v002.SM_LB_BodyShopSupport_SmallPartsBin_Open_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002.SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Services/SM_LB_BodyShopSupport_UtilityPedestal_v002.SM_LB_BodyShopSupport_UtilityPedestal_v002"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyWeldLine/Runtime_v001/Fixture/SM_LB_BodyWeld_FramingFixture_v001.SM_LB_BodyWeld_FramingFixture_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Fixture/SM_LB_BodyShop_UnderbodyFixture_v001.SM_LB_BodyShop_UnderbodyFixture_v001"),
        TEXT("/Engine/BasicShapes/Cube.Cube"),
        TEXT("/Engine/BasicShapes/Cube.Cube"),
        TEXT("/Engine/BasicShapes/Cube.Cube")
    };

    const TCHAR* BasicMaterialPath =
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
    const TCHAR* ExpectedPresentationClassPath = TEXT(
        "/Script/LineBossCarFactory.LBOneFactoryBodyWeldStarterPresentationActor");

    const FLBOneFactoryBodyWeldStationState* FindStation(
        const FLBOneFactoryBodyWeldLayoutState& Layout,
        const int32 LinePosition)
    {
        return Layout.Stations.FindByPredicate([LinePosition](
            const FLBOneFactoryBodyWeldStationState& Station)
        {
            return Station.LinePosition == LinePosition;
        });
    }

    const FLBOneFactoryBodyWeldStationState* FindStation(
        const FLBOneFactoryBodyWeldLayoutState& Layout,
        const FName StationId)
    {
        return Layout.Stations.FindByPredicate([StationId](
            const FLBOneFactoryBodyWeldStationState& Station)
        {
            return Station.StationId == StationId;
        });
    }

    bool IsFiniteTransform(const FTransform& Transform)
    {
        const FVector Location = Transform.GetLocation();
        const FVector Scale = Transform.GetScale3D();
        const FQuat Rotation = Transform.GetRotation();
        return !Transform.ContainsNaN() && Rotation.IsNormalized()
            && FMath::IsFinite(Location.X) && FMath::IsFinite(Location.Y)
            && FMath::IsFinite(Location.Z) && FMath::IsFinite(Scale.X)
            && FMath::IsFinite(Scale.Y) && FMath::IsFinite(Scale.Z)
            && Scale.GetMin() > 0.0f;
    }

    bool RobotRoleUsesCGun(
        const ELBOneFactoryBodyWeldRobotRole RobotRole)
    {
        using R = ELBOneFactoryBodyWeldRobotRole;
        return RobotRole == R::SpotWelding || RobotRole == R::StudWelding
            || RobotRole == R::ReworkWelding;
    }

    ELBOneFactoryBodyWeldPresentationBatch FixtureBatchForProgramme(
        const ELBOneFactoryBodyWeldProgramme Programme)
    {
        using P = ELBOneFactoryBodyWeldProgramme;
        return (Programme == P::FrontUnderbodyGeometry
                || Programme == P::RearUnderbodyGeometry
                || Programme == P::UnderbodyFramingAndRespot)
            ? ELBOneFactoryBodyWeldPresentationBatch::ProgrammeFixtureUnderbody
            : ELBOneFactoryBodyWeldPresentationBatch::ProgrammeFixtureFraming;
    }

    bool PositionIn(const int32 Position,
        const std::initializer_list<int32> Candidates)
    {
        for (const int32 Candidate : Candidates)
        {
            if (Position == Candidate) return true;
        }
        return false;
    }

    FString MakePresentationId(const FName StationId, const TCHAR* Suffix)
    {
        return FString::Printf(TEXT("OF_BODY_WELD_VIS_%s_%s"),
            *StationId.ToString(), Suffix);
    }

    void AddItem(TArray<FLBOneFactoryBodyWeldPresentationItem>& Items,
        const FName PresentationId, const FName StationId,
        const int32 LinePosition,
        const ELBOneFactoryBodyWeldPresentationBatch Batch,
        const FTransform& WorldTransform,
        const bool bProgrammeFixture = false,
        const ELBOneFactoryBodyWeldProgramme Programme =
            ELBOneFactoryBodyWeldProgramme::PressedPanelReceive,
        const bool bRobotPart = false,
        const ELBOneFactoryBodyWeldRobotSide RobotSide =
            ELBOneFactoryBodyWeldRobotSide::Left,
        const ELBOneFactoryBodyWeldRobotRole RobotRole =
            ELBOneFactoryBodyWeldRobotRole::None)
    {
        FLBOneFactoryBodyWeldPresentationItem& Item =
            Items.AddDefaulted_GetRef();
        Item.PresentationId = PresentationId;
        Item.StationId = StationId;
        Item.LinePosition = LinePosition;
        Item.Batch = Batch;
        Item.Programme = Programme;
        Item.bProgrammeFixture = bProgrammeFixture;
        Item.bRobotPart = bRobotPart;
        Item.RobotSide = RobotSide;
        Item.RobotRole = RobotRole;
        Item.WorldTransform = WorldTransform;
        Item.bRepresentsProcessWIP = false;
    }

    void AddRobotItems(
        TArray<FLBOneFactoryBodyWeldPresentationItem>& Items,
        const FLBOneFactoryBodyWeldStationState& Station,
        const ELBOneFactoryBodyWeldRobotSide RobotSide,
        const ELBOneFactoryBodyWeldRobotRole RobotRole)
    {
        const bool bLeft = RobotSide ==
            ELBOneFactoryBodyWeldRobotSide::Left;
        const TCHAR* SideToken = bLeft ? TEXT("LEFT") : TEXT("RIGHT");
        const float SideSign = bLeft ? -1.0f : 1.0f;
        // v002: the pack's own contact FK validation mounts the pair at
        // fixture-local Y = +-300 with yaw +-35 - the v001 stand-off of
        // 1240 put ~10.7 m of floor between a ~3 m arm and its work.
        const FTransform RobotLocal(FRotator(0.0f,
                bLeft ? 35.0f : -35.0f, 0.0f),
            FVector(0.0f, SideSign * 300.0f, 0.0f), FVector::OneVector);
        const FTransform RobotRoot = RobotLocal * Station.WorldTransform;

        AddItem(Items,
            FName(*MakePresentationId(Station.StationId,
                *FString::Printf(TEXT("ROBOT_%s_BASE"), SideToken))),
            Station.StationId, Station.LinePosition,
            ELBOneFactoryBodyWeldPresentationBatch::RobotBase,
            RobotRoot, false,
            ELBOneFactoryBodyWeldProgramme::PressedPanelReceive,
            true, RobotSide, RobotRole);

        // v002: the frozen PROCESS-phase contact pose for this station's
        // target, mirrored for the right side by negating J1/J4/J6.
        const int32 TargetIndex = Station.LinePosition % 3;
        float JointAngles[6];
        for (int32 JointIndex = 0; JointIndex < 6; ++JointIndex)
        {
            float Degrees = ContactProcessPoseDegrees[TargetIndex][JointIndex];
            if (!bLeft
                && (JointIndex == 0 || JointIndex == 3 || JointIndex == 5))
            {
                Degrees = -Degrees;
            }
            JointAngles[JointIndex] = Degrees;
        }
        FTransform CurrentTransform = RobotRoot;
        FTransform UpperArmTransform = RobotRoot;
        FTransform WristTransform = RobotRoot;
        for (int32 JointIndex = 0; JointIndex < 6; ++JointIndex)
        {
            FVector PivotLocation = FVector::ZeroVector;
            if (!ALBBodyShopRobotActor::GetAuthoredJointPivotRelativeLocation(
                    JointIndex, PivotLocation))
            {
                return;
            }
            const FTransform JointLocal(
                ALBBodyShopRobotActor::GetAuthoredJointRelativeRotation(
                    JointIndex, JointAngles[JointIndex]),
                PivotLocation, FVector::OneVector);
            CurrentTransform = JointLocal * CurrentTransform;
            const ELBOneFactoryBodyWeldPresentationBatch JointBatch =
                static_cast<ELBOneFactoryBodyWeldPresentationBatch>(
                    static_cast<uint8>(
                        ELBOneFactoryBodyWeldPresentationBatch::RobotJ1)
                    + JointIndex);
            AddItem(Items,
                FName(*MakePresentationId(Station.StationId,
                    *FString::Printf(TEXT("ROBOT_%s_J%d"), SideToken,
                        JointIndex + 1))),
                Station.StationId, Station.LinePosition, JointBatch,
                CurrentTransform, false,
                ELBOneFactoryBodyWeldProgramme::PressedPanelReceive,
                true, RobotSide, RobotRole);
            if (JointIndex == 1)
            {
                UpperArmTransform = CurrentTransform;
            }
            else if (JointIndex == 4)
            {
                WristTransform = CurrentTransform;
            }
        }

        // v003: the dress pack rides every robot - the PR004 trio at the
        // measured 0.68 fit (lower on the base stack, upper along the J2
        // link, wrist at J5).
        const FTransform DressScale(FQuat::Identity, FVector::ZeroVector,
            FVector(DressPackScale));
        AddItem(Items,
            FName(*MakePresentationId(Station.StationId,
                *FString::Printf(TEXT("ROBOT_%s_DRESS_LOWER"), SideToken))),
            Station.StationId, Station.LinePosition,
            ELBOneFactoryBodyWeldPresentationBatch::RobotDressLower,
            DressScale * RobotRoot, false,
            ELBOneFactoryBodyWeldProgramme::PressedPanelReceive,
            true, RobotSide, RobotRole);
        AddItem(Items,
            FName(*MakePresentationId(Station.StationId,
                *FString::Printf(TEXT("ROBOT_%s_DRESS_UPPER"), SideToken))),
            Station.StationId, Station.LinePosition,
            ELBOneFactoryBodyWeldPresentationBatch::RobotDressUpper,
            DressScale * UpperArmTransform, false,
            ELBOneFactoryBodyWeldProgramme::PressedPanelReceive,
            true, RobotSide, RobotRole);
        AddItem(Items,
            FName(*MakePresentationId(Station.StationId,
                *FString::Printf(TEXT("ROBOT_%s_DRESS_WRIST"), SideToken))),
            Station.StationId, Station.LinePosition,
            ELBOneFactoryBodyWeldPresentationBatch::RobotDressWrist,
            DressScale * WristTransform, false,
            ELBOneFactoryBodyWeldProgramme::PressedPanelReceive,
            true, RobotSide, RobotRole);
        // v002: every robot carries a visible tool - welding roles the open
        // C-gun, every other role the native eight-cup panel-pick.
        if (RobotRoleUsesCGun(RobotRole))
        {
            AddItem(Items,
                FName(*MakePresentationId(Station.StationId,
                    *FString::Printf(TEXT("ROBOT_%s_CGUN"), SideToken))),
                Station.StationId, Station.LinePosition,
                ELBOneFactoryBodyWeldPresentationBatch::RobotOpenCGun,
                CurrentTransform, false,
                ELBOneFactoryBodyWeldProgramme::PressedPanelReceive,
                true, RobotSide, RobotRole);
        }
        else
        {
            AddItem(Items,
                FName(*MakePresentationId(Station.StationId,
                    *FString::Printf(TEXT("ROBOT_%s_TOOL"), SideToken))),
                Station.StationId, Station.LinePosition,
                ELBOneFactoryBodyWeldPresentationBatch::RobotPanelPickTool,
                CurrentTransform, false,
                ELBOneFactoryBodyWeldProgramme::PressedPanelReceive,
                true, RobotSide, RobotRole);
        }

        const FTransform RoleMarkerLocal(FRotator::ZeroRotator,
            FVector(0.0f, SideSign * 1430.0f, 125.0f),
            FVector(0.24f, 0.24f, 1.25f));
        AddItem(Items,
            FName(*MakePresentationId(Station.StationId,
                *FString::Printf(TEXT("ROBOT_%s_ROLE"), SideToken))),
            Station.StationId, Station.LinePosition,
            ELBOneFactoryBodyWeldPresentationBatch::RobotRoleCube,
            RoleMarkerLocal * Station.WorldTransform, false,
            ELBOneFactoryBodyWeldProgramme::PressedPanelReceive,
            false, RobotSide, RobotRole);
    }

    void AddSupportItem(
        TArray<FLBOneFactoryBodyWeldPresentationItem>& Items,
        const FLBOneFactoryBodyWeldStationState& Station,
        const ELBOneFactoryBodyWeldPresentationBatch Batch,
        const TCHAR* Suffix, const FVector& LocalLocation,
        const float LocalYawDegrees = 0.0f)
    {
        const FTransform Local(FRotator(0.0f, LocalYawDegrees, 0.0f),
            LocalLocation, FVector::OneVector);
        AddItem(Items,
            FName(*MakePresentationId(Station.StationId, Suffix)),
            Station.StationId, Station.LinePosition, Batch,
            Local * Station.WorldTransform);
    }

    bool SameItem(const FLBOneFactoryBodyWeldPresentationItem& Left,
        const FLBOneFactoryBodyWeldPresentationItem& Right)
    {
        return Left.Version == Right.Version
            && Left.PresentationId == Right.PresentationId
            && Left.StationId == Right.StationId
            && Left.LinePosition == Right.LinePosition
            && Left.Batch == Right.Batch
            && Left.Programme == Right.Programme
            && Left.bProgrammeFixture == Right.bProgrammeFixture
            && Left.RobotSide == Right.RobotSide
            && Left.RobotRole == Right.RobotRole
            && Left.bRobotPart == Right.bRobotPart
            && Left.WorldTransform.Equals(Right.WorldTransform,
                TransformTolerance)
            && Left.bRepresentsProcessWIP == Right.bRepresentsProcessWIP;
    }
}

ALBOneFactoryBodyWeldStarterPresentationActor::
    ALBOneFactoryBodyWeldStarterPresentationActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    using namespace LBOneFactoryBodyWeldPresentationPrivate;
    VisualBatches.Reserve(ExpectedBatchCount);
    MeshBindings.Reserve(ExpectedBatchCount);
    for (int32 Index = 0; Index < ExpectedBatchCount; ++Index)
    {
        UHierarchicalInstancedStaticMeshComponent* Batch =
            CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
                FName(BatchComponentNames[Index]));
        Batch->SetupAttachment(SceneRoot);
        ConfigureVisualBatch(Batch);
        // Only the three semantic Engine-cube batches skip shadows; the
        // authored fixtures cast like every other machine.
        if (Index >= static_cast<int32>(
                ELBOneFactoryBodyWeldPresentationBatch::FloorRouteCube))
        {
            Batch->SetCastShadow(false);
        }
        VisualBatches.Add(Batch);
        MeshBindings.Add(TSoftObjectPtr<UStaticMesh>(
            FSoftObjectPath(BatchMeshPaths[Index])));
    }
    SemanticBaseMaterial = TSoftObjectPtr<UMaterialInterface>(
        FSoftObjectPath(BasicMaterialPath));

    Tags.AddUnique(GetPresentationTag());
    Tags.AddUnique(TEXT("LB.OneFactory.BodyWeldStarter.NativeAuthored"));
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
    SetActorHiddenInGame(true);
}

void ALBOneFactoryBodyWeldStarterPresentationActor::ConfigureVisualBatch(
    UHierarchicalInstancedStaticMeshComponent* Component)
{
    if (!Component) return;
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetReceivesDecals(false);
}

TArray<UHierarchicalInstancedStaticMeshComponent*>
ALBOneFactoryBodyWeldStarterPresentationActor::GetAllBatches() const
{
    TArray<UHierarchicalInstancedStaticMeshComponent*> Result;
    Result.Reserve(VisualBatches.Num());
    for (const TObjectPtr<UHierarchicalInstancedStaticMeshComponent>& Batch :
        VisualBatches)
    {
        Result.Add(Batch.Get());
    }
    return Result;
}

UHierarchicalInstancedStaticMeshComponent*
ALBOneFactoryBodyWeldStarterPresentationActor::FindBatchComponent(
    const ELBOneFactoryBodyWeldPresentationBatch Batch) const
{
    const int32 Index = static_cast<int32>(Batch);
    return VisualBatches.IsValidIndex(Index) ? VisualBatches[Index].Get()
        : nullptr;
}

void ALBOneFactoryBodyWeldStarterPresentationActor::ClearPresentation()
{
    for (UHierarchicalInstancedStaticMeshComponent* Batch : GetAllBatches())
    {
        if (!Batch) continue;
        Batch->ClearInstances();
        Batch->SetStaticMesh(nullptr);
        Batch->SetMaterial(0, nullptr);
    }
    SemanticMaterials.Reset();
    ConfiguredItems.Reset();
    ConfiguredStationTransforms.Reset();
    ConfiguredLayoutId = NAME_None;
    ConfiguredLayoutRevision = INDEX_NONE;
    bPresentationConfigured = false;
    SetActorHiddenInGame(true);
}

bool ALBOneFactoryBodyWeldStarterPresentationActor::ConfigureFromLayout(
    const FLBOneFactoryBodyWeldLayoutState& Layout, FString& OutReason)
{
    ClearPresentation();
    if (!ValidateNativePresentationReferences(GetPresentationClassPath(),
            GetRequiredNativeAssetPaths(), OutReason))
    {
        OutReason = FString::Printf(
            TEXT("BODY/WELD PRESENTATION PROVENANCE FAILED: %s"),
            *OutReason);
        return false;
    }
    const TArray<FLBOneFactoryBodyWeldPresentationItem> CandidateItems =
        BuildExpectedPresentationItems(Layout);
    if (!ValidatePresentationContract(Layout, CandidateItems, OutReason))
    {
        OutReason = FString::Printf(
            TEXT("BODY/WELD PRESENTATION CONTRACT FAILED: %s"),
            *OutReason);
        return false;
    }

    TArray<UStaticMesh*> ResolvedMeshes;
    ResolvedMeshes.Reserve(MeshBindings.Num());
    for (const TSoftObjectPtr<UStaticMesh>& Binding : MeshBindings)
    {
        ResolvedMeshes.Add(Binding.LoadSynchronous());
    }
    UMaterialInterface* ResolvedMaterial =
        SemanticBaseMaterial.LoadSynchronous();
    const TArray<UHierarchicalInstancedStaticMeshComponent*> Batches =
        GetAllBatches();
    if (ResolvedMeshes.Num() != GetExpectedVisualBatchCount()
        || ResolvedMeshes.Contains(nullptr) || !ResolvedMaterial
        || Batches.Num() != GetExpectedVisualBatchCount()
        || Batches.Contains(nullptr))
    {
        OutReason = TEXT(
            "BODY/WELD PRESENTATION COULD NOT RESOLVE ALL 26 NATIVE MESHES, THREE ENGINE BINDINGS AND MATERIAL");
        ClearPresentation();
        return false;
    }
    for (int32 Index = 0; Index < Batches.Num(); ++Index)
    {
        Batches[Index]->SetStaticMesh(ResolvedMeshes[Index]);
    }

    // v002: the authored fixtures keep their own materials; only the three
    // semantic cube batches take tinted materials.
    const FLinearColor SemanticColours[] =
    {
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("D79F2B"))),
        FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("50C9C3"))),
        FLinearColor::FromSRGBColor(FColor::FromHex(
            Layout.bCommissioned ? TEXT("39C980") : TEXT("E1B83F")))
    };
    for (int32 SemanticIndex = 0;
        SemanticIndex < UE_ARRAY_COUNT(SemanticColours); ++SemanticIndex)
    {
        UMaterialInstanceDynamic* Material =
            UMaterialInstanceDynamic::Create(ResolvedMaterial, this);
        if (!Material)
        {
            OutReason = TEXT(
                "BODY/WELD PRESENTATION COULD NOT CREATE ALL THREE SEMANTIC MATERIALS");
            ClearPresentation();
            return false;
        }
        Material->SetVectorParameterValue(TEXT("Color"),
            SemanticColours[SemanticIndex]);
        Material->SetVectorParameterValue(TEXT("BaseColor"),
            SemanticColours[SemanticIndex]);
        const int32 BatchIndex = static_cast<int32>(
            ELBOneFactoryBodyWeldPresentationBatch::FloorRouteCube)
            + SemanticIndex;
        Batches[BatchIndex]->SetMaterial(0, Material);
        SemanticMaterials.Add(Material);
    }

    for (const FLBOneFactoryBodyWeldPresentationItem& Item : CandidateItems)
    {
        UHierarchicalInstancedStaticMeshComponent* Batch =
            FindBatchComponent(Item.Batch);
        if (!Batch
            || Batch->AddInstance(Item.WorldTransform, true) == INDEX_NONE)
        {
            OutReason = FString::Printf(
                TEXT("BODY/WELD PRESENTATION FAILED TO COMMIT %s"),
                *Item.PresentationId.ToString());
            ClearPresentation();
            return false;
        }
    }
    if (GetVisibleInstanceCount()
            != GetExpectedVisibleInstanceCount(Layout)
        || GetVisualBatchCount() != GetExpectedVisualBatchCount())
    {
        OutReason = TEXT(
            "BODY/WELD PRESENTATION COMMIT DID NOT MATCH ITS EXACT BATCH/INSTANCE COUNTS");
        ClearPresentation();
        return false;
    }

    for (const FLBOneFactoryBodyWeldStationState& Station : Layout.Stations)
    {
        ConfiguredStationTransforms.Add(
            Station.StationId, Station.WorldTransform);
    }
    ConfiguredItems = CandidateItems;
    ConfiguredLayoutId = Layout.LayoutId;
    ConfiguredLayoutRevision = Layout.Revision;
    bPresentationConfigured = true;
    SetActorHiddenInGame(false);
    OutReason = FString::Printf(TEXT(
        "NATIVE BODY/WELD PRESENTATION ACTIVE: 29 BATCHES, %d INSTANCES, 18 POSITIONS, 36 LARGE ROBOTS, WIP 0"),
        CandidateItems.Num());
    return true;
}

int32 ALBOneFactoryBodyWeldStarterPresentationActor::
    GetVisibleInstanceCount() const
{
    int32 Count = 0;
    for (const UHierarchicalInstancedStaticMeshComponent* Batch :
        GetAllBatches())
    {
        Count += Batch ? Batch->GetInstanceCount() : 0;
    }
    return Count;
}

int32 ALBOneFactoryBodyWeldStarterPresentationActor::
    GetVisualBatchCount() const
{
    int32 Count = 0;
    for (const UHierarchicalInstancedStaticMeshComponent* Batch :
        GetAllBatches())
    {
        if (Batch && Batch->GetInstanceCount() > 0) ++Count;
    }
    return Count;
}

int32 ALBOneFactoryBodyWeldStarterPresentationActor::
    GetInstanceCountForBatch(
        const ELBOneFactoryBodyWeldPresentationBatch Batch) const
{
    const UHierarchicalInstancedStaticMeshComponent* Component =
        FindBatchComponent(Batch);
    return Component ? Component->GetInstanceCount() : 0;
}

bool ALBOneFactoryBodyWeldStarterPresentationActor::
    GetConfiguredStationTransform(
        const FName StationId, FTransform& OutWorldTransform) const
{
    const FTransform* Found = ConfiguredStationTransforms.Find(StationId);
    if (!bPresentationConfigured || !Found) return false;
    OutWorldTransform = *Found;
    return true;
}

TArray<FLBOneFactoryBodyWeldPresentationItem>
ALBOneFactoryBodyWeldStarterPresentationActor::
    GetConfiguredItemsForProgramme(
        const ELBOneFactoryBodyWeldProgramme InProgramme) const
{
    TArray<FLBOneFactoryBodyWeldPresentationItem> Result;
    for (const FLBOneFactoryBodyWeldPresentationItem& Item : ConfiguredItems)
    {
        if (Item.bProgrammeFixture && Item.Programme == InProgramme)
            Result.Add(Item);
    }
    return Result;
}

TArray<FLBOneFactoryBodyWeldPresentationItem>
ALBOneFactoryBodyWeldStarterPresentationActor::GetConfiguredRobotItems(
    const FName StationId,
    const ELBOneFactoryBodyWeldRobotSide InRobotSide) const
{
    TArray<FLBOneFactoryBodyWeldPresentationItem> Result;
    for (const FLBOneFactoryBodyWeldPresentationItem& Item : ConfiguredItems)
    {
        if (Item.StationId == StationId && Item.RobotSide == InRobotSide
            && Item.RobotRole != ELBOneFactoryBodyWeldRobotRole::None)
        {
            Result.Add(Item);
        }
    }
    return Result;
}

int32 ALBOneFactoryBodyWeldStarterPresentationActor::
    GetExpectedVisualBatchCount()
{
    return LBOneFactoryBodyWeldPresentationPrivate::ExpectedBatchCount;
}

int32 ALBOneFactoryBodyWeldStarterPresentationActor::
    GetCanonicalVisibleInstanceCount()
{
    return LBOneFactoryBodyWeldPresentationPrivate::CanonicalInstanceCount;
}

int32 ALBOneFactoryBodyWeldStarterPresentationActor::
    GetExpectedVisibleInstanceCount(
        const FLBOneFactoryBodyWeldLayoutState& Layout)
{
    int32 Result = 0;
    for (int32 Index = 0; Index < GetExpectedVisualBatchCount(); ++Index)
    {
        Result += GetExpectedInstanceCountForBatch(Layout,
            static_cast<ELBOneFactoryBodyWeldPresentationBatch>(Index));
    }
    return Result;
}

int32 ALBOneFactoryBodyWeldStarterPresentationActor::
    GetExpectedInstanceCountForBatch(
        const FLBOneFactoryBodyWeldLayoutState& Layout,
        const ELBOneFactoryBodyWeldPresentationBatch Batch)
{
    using B = ELBOneFactoryBodyWeldPresentationBatch;
    if (Batch >= B::RobotBase && Batch <= B::RobotJ6) return 36;
    if (Batch >= B::RobotDressLower && Batch <= B::RobotDressWrist)
    {
        return 36;
    }
    if (Batch == B::RobotOpenCGun || Batch == B::RobotPanelPickTool)
    {
        int32 CGunCount = 0;
        for (const FLBOneFactoryBodyWeldStationState& Station :
            Layout.Stations)
        {
            if (LBOneFactoryBodyWeldPresentationPrivate::RobotRoleUsesCGun(
                    Station.LeftRobotRole)) ++CGunCount;
            if (LBOneFactoryBodyWeldPresentationPrivate::RobotRoleUsesCGun(
                    Station.RightRobotRole)) ++CGunCount;
        }
        // v002: every robot carries exactly one tool, so the two batches
        // always partition the 36 arms.
        return Batch == B::RobotOpenCGun ? CGunCount : 36 - CGunCount;
    }
    switch (Batch)
    {
    case B::ComponentServicePallet: return 10;
    case B::ElectricalCabinet: return 7;
    case B::EmptyReturnCart: return 3;
    case B::ExtractionPedestal: return 12;
    case B::GuardGate: return 9;
    case B::GuardPanel: return 18;
    case B::HMIPedestal: return 18;
    case B::PanelStillageEmpty: return 3;
    case B::PanelStillageFull: return 5;
    case B::SmallPartsBinOpen: return 7;
    case B::SmallPartsCrateOpen: return 5;
    case B::UtilityPedestal: return 15;
    // The 18 programmes appear exactly once each (ValidateStarterLayout),
    // and exactly three are underbody programmes.
    case B::ProgrammeFixtureFraming: return 15;
    case B::ProgrammeFixtureUnderbody: return 3;
    case B::FloorRouteCube: return 17;
    case B::RobotRoleCube: return 36;
    case B::StatusCube: return 18;
    default: return 0;
    }
}

TArray<FSoftObjectPath>
ALBOneFactoryBodyWeldStarterPresentationActor::GetRequiredNativeAssetPaths()
{
    using namespace LBOneFactoryBodyWeldPresentationPrivate;
    TArray<FSoftObjectPath> Result;
    Result.Reserve(ExpectedBatchCount + 1);
    for (const TCHAR* Path : BatchMeshPaths)
    {
        Result.Add(FSoftObjectPath(Path));
    }
    Result.Add(FSoftObjectPath(BasicMaterialPath));
    return Result;
}

bool ALBOneFactoryBodyWeldStarterPresentationActor::
    ValidateNativePresentationReferences(
        const FString& PresentationClassPath,
        const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason)
{
    using namespace LBOneFactoryBodyWeldPresentationPrivate;
    if (!PresentationClassPath.Equals(ExpectedPresentationClassPath,
            ESearchCase::CaseSensitive))
    {
        OutReason = TEXT(
            "BODY/WELD PRESENTATION CLASS DRIFTED FROM ITS EXACT NATIVE CODE CONTRACT");
        return false;
    }
    if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::NativeCode,
            PresentationClassPath, OutReason))
    {
        return false;
    }
    const TArray<FSoftObjectPath> Expected = GetRequiredNativeAssetPaths();
    if (AssetPaths.Num() != Expected.Num())
    {
        OutReason = TEXT(
            "BODY/WELD PRESENTATION REQUIRES 29 ORDERED MESH BINDINGS AND ONE MATERIAL");
        return false;
    }
    // v002 deliberately unlocks two roots that v001 forbade: the
    // BodyShopUnderbodySlice_v001 pack (clean native Blender source, frozen
    // roundtrip PASS) and the BodyWeldLine/Runtime_v001 fixture (clean-room
    // derivative with an Unreal promotion receipt). WeldRobotRuntime is
    // newly forbidden: its tool meshes derive from the Meshy SpotRobot
    // intake and must never drift into this NativeOnly contract.
    static const TCHAR* ForbiddenTokens[] =
    {
        TEXT("Meshy"), TEXT("RuntimeGLB"), TEXT("ExternalGenerated"),
        TEXT("OriginalHighPoly"), TEXT("/Downloads/"),
        TEXT("/Developer/Validation/"), TEXT("Robots/WeldRobotRuntime")
    };
    const FString RobotRoot = TEXT(
        "/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/");
    const FString SupportRoot = TEXT(
        "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/");
    const FString SliceRoot = TEXT(
        "/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/");
    const FString FixtureRoot = TEXT(
        "/Game/LineBoss/Candidates/WeldShop/BodyWeldLine/Runtime_v001/");
    for (int32 Index = 0; Index < Expected.Num(); ++Index)
    {
        if (AssetPaths[Index].IsNull() || AssetPaths[Index] != Expected[Index])
        {
            OutReason = TEXT(
                "BODY/WELD PRESENTATION ASSET LIST OR ORDER DRIFTED FROM V003");
            return false;
        }
        const FString Reference = AssetPaths[Index].ToString();
        for (const TCHAR* Token : ForbiddenTokens)
        {
            if (Reference.Contains(Token, ESearchCase::IgnoreCase))
            {
                OutReason = TEXT(
                    "BODY/WELD PRESENTATION REFERENCE CONTAINS A FORBIDDEN SOURCE TOKEN");
                return false;
            }
        }
        // v003 index windows: 0-7 robot kit, 8 slice tool, 9-11 dress trio,
        // 12-23 support kit, 24 framing fixture, 25 slice fixture, 26-28
        // engine cubes.
        const bool bRobot = Index < 8;
        const bool bSliceTool = Index == 8;
        const bool bDress = Index >= 9 && Index < 12;
        const bool bSupport = Index >= 12 && Index < 24;
        const bool bFraming = Index == 24;
        const bool bSliceFixture = Index == 25;
        const bool bEngine = Index >= 26;
        const FString DressRoot = TEXT(
            "/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v020/");
        if ((bRobot && !Reference.StartsWith(RobotRoot,
                ESearchCase::CaseSensitive))
            || ((bSliceTool || bSliceFixture)
                && !Reference.StartsWith(SliceRoot,
                    ESearchCase::CaseSensitive))
            || (bDress && !Reference.StartsWith(DressRoot,
                ESearchCase::CaseSensitive))
            || (bSupport && !Reference.StartsWith(SupportRoot,
                ESearchCase::CaseSensitive))
            || (bFraming && !Reference.StartsWith(FixtureRoot,
                ESearchCase::CaseSensitive))
            || (bEngine && !Reference.StartsWith(
                TEXT("/Engine/BasicShapes/"),
                ESearchCase::CaseSensitive)))
        {
            OutReason = TEXT(
                "BODY/WELD PRESENTATION REFERENCE LEFT ITS EXACT NATIVE ROOT");
            return false;
        }
        if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
                ELBOneFactoryProvenancePolicy::NativeOnly,
                bEngine
                    ? ELBOneFactoryAssetProvenance::NativeProcedural
                    : ELBOneFactoryAssetProvenance::NativeAuthored,
                Reference, OutReason))
        {
            return false;
        }
    }
    OutReason = TEXT(
        "BODY/WELD PRESENTATION CLASS, ROBOT KIT, SLICE KIT, FIXTURES, SUPPORT KIT AND ENGINE REFERENCES ARE NATIVE-ONLY");
    return true;
}

TArray<FLBOneFactoryBodyWeldPresentationItem>
ALBOneFactoryBodyWeldStarterPresentationActor::
    BuildExpectedPresentationItems(
        const FLBOneFactoryBodyWeldLayoutState& Layout)
{
    using namespace LBOneFactoryBodyWeldPresentationPrivate;
    FString Reason;
    if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            Layout, Reason))
    {
        return {};
    }

    TArray<FLBOneFactoryBodyWeldPresentationItem> Items;
    Items.Reserve(GetExpectedVisibleInstanceCount(Layout));
    for (int32 Position = 1;
        Position <= ULBOneFactoryBodyWeldStarterLayoutLibrary::
            RequiredStationCount; ++Position)
    {
        const FLBOneFactoryBodyWeldStationState* Station =
            FindStation(Layout, Position);
        if (!Station) return {};

        TArray<ELBOneFactoryBodyWeldProgramme> Programmes =
            Station->AssignedProgrammes;
        Programmes.Sort([](const ELBOneFactoryBodyWeldProgramme Left,
            const ELBOneFactoryBodyWeldProgramme Right)
        {
            return static_cast<uint8>(Left) < static_cast<uint8>(Right);
        });
        for (int32 ProgrammeIndex = 0;
            ProgrammeIndex < Programmes.Num(); ++ProgrammeIndex)
        {
            const ELBOneFactoryBodyWeldProgramme Programme =
                Programmes[ProgrammeIndex];
            const float OffsetX =
                (static_cast<float>(ProgrammeIndex)
                    - (static_cast<float>(Programmes.Num()) - 1.0f) * 0.5f)
                * 360.0f;
            // v002: the authored fixtures replace the flat cube slab. Both
            // fixture meshes carry station-centre-at-floor pivots, so the
            // z-lift and cube scaling are gone.
            const FTransform FixtureLocal(FRotator::ZeroRotator,
                FVector(OffsetX, 0.0f, 0.0f), FVector::OneVector);
            AddItem(Items,
                FName(*MakePresentationId(Station->StationId,
                    *FString::Printf(TEXT("PROGRAMME_%02d"),
                        static_cast<int32>(Programme) + 1))),
                Station->StationId, Station->LinePosition,
                FixtureBatchForProgramme(Programme),
                FixtureLocal * Station->WorldTransform,
                true, Programme);
        }

        AddRobotItems(Items, *Station,
            ELBOneFactoryBodyWeldRobotSide::Left,
            Station->LeftRobotRole);
        AddRobotItems(Items, *Station,
            ELBOneFactoryBodyWeldRobotSide::Right,
            Station->RightRobotRole);

        AddSupportItem(Items, *Station,
            ELBOneFactoryBodyWeldPresentationBatch::HMIPedestal,
            TEXT("HMI"), FVector(-620.0f, -1510.0f, 0.0f));
        AddSupportItem(Items, *Station,
            ELBOneFactoryBodyWeldPresentationBatch::GuardPanel,
            TEXT("GUARD_PANEL"), FVector(0.0f, 1570.0f, 0.0f));
        if ((Position % 2) == 1)
        {
            AddSupportItem(Items, *Station,
                ELBOneFactoryBodyWeldPresentationBatch::GuardGate,
                TEXT("GUARD_GATE"), FVector(0.0f, -1570.0f, 0.0f));
        }
        if (PositionIn(Position, {2, 4, 7, 9, 12, 14, 16}))
        {
            AddSupportItem(Items, *Station,
                ELBOneFactoryBodyWeldPresentationBatch::ElectricalCabinet,
                TEXT("ELECTRICAL"), FVector(620.0f, -1490.0f, 0.0f));
        }
        if (Position >= 2 && Position <= 16)
        {
            AddSupportItem(Items, *Station,
                ELBOneFactoryBodyWeldPresentationBatch::UtilityPedestal,
                TEXT("UTILITY"), FVector(-420.0f, 1450.0f, 0.0f));
        }
        if (PositionIn(Position,
            {2, 3, 4, 7, 8, 9, 10, 12, 14, 15, 16, 17}))
        {
            AddSupportItem(Items, *Station,
                ELBOneFactoryBodyWeldPresentationBatch::ExtractionPedestal,
                TEXT("EXTRACTION"), FVector(420.0f, 1450.0f, 0.0f));
        }
        if (PositionIn(Position, {1, 5, 6, 8, 11}))
        {
            AddSupportItem(Items, *Station,
                ELBOneFactoryBodyWeldPresentationBatch::PanelStillageFull,
                TEXT("STILLAGE_FULL"), FVector(-650.0f, -2020.0f, 0.0f));
        }
        if (PositionIn(Position, {1, 11, 17}))
        {
            AddSupportItem(Items, *Station,
                ELBOneFactoryBodyWeldPresentationBatch::PanelStillageEmpty,
                TEXT("STILLAGE_EMPTY"), FVector(650.0f, -2020.0f, 0.0f));
        }
        if (PositionIn(Position, {1, 17, 18}))
        {
            AddSupportItem(Items, *Station,
                ELBOneFactoryBodyWeldPresentationBatch::EmptyReturnCart,
                TEXT("RETURN_CART"), FVector(0.0f, 2050.0f, 0.0f));
        }
        if (PositionIn(Position,
            {2, 3, 4, 7, 9, 10, 12, 14, 15, 16}))
        {
            AddSupportItem(Items, *Station,
                ELBOneFactoryBodyWeldPresentationBatch::
                    ComponentServicePallet,
                TEXT("SERVICE_PALLET"), FVector(0.0f, 1900.0f, 0.0f));
        }
        if (PositionIn(Position, {2, 3, 7, 8, 10, 12, 15}))
        {
            AddSupportItem(Items, *Station,
                ELBOneFactoryBodyWeldPresentationBatch::SmallPartsBinOpen,
                TEXT("PARTS_BIN"), FVector(-680.0f, 1840.0f, 0.0f));
        }
        if (PositionIn(Position, {1, 5, 6, 11, 17}))
        {
            AddSupportItem(Items, *Station,
                ELBOneFactoryBodyWeldPresentationBatch::SmallPartsCrateOpen,
                TEXT("PARTS_CRATE"), FVector(680.0f, 1840.0f, 0.0f));
        }

        const FTransform StatusLocal(FRotator::ZeroRotator,
            FVector(700.0f, 1340.0f, 100.0f),
            FVector(0.34f, 0.34f, 1.0f));
        AddItem(Items,
            FName(*MakePresentationId(Station->StationId, TEXT("STATUS"))),
            Station->StationId, Station->LinePosition,
            ELBOneFactoryBodyWeldPresentationBatch::StatusCube,
            StatusLocal * Station->WorldTransform);
    }

    for (const FLBOneFactoryBodyWeldConnectionState& Connection :
        Layout.Connections)
    {
        const FLBOneFactoryBodyWeldStationState* Source =
            FindStation(Layout, Connection.SourceStationId);
        const FLBOneFactoryBodyWeldStationState* Target =
            FindStation(Layout, Connection.TargetStationId);
        if (!Source || !Target) return {};
        const FVector Start = Source->WorldTransform.GetLocation();
        const FVector End = Target->WorldTransform.GetLocation();
        const FVector Delta = End - Start;
        const float Length = Delta.Size2D();
        const float Yaw = FMath::RadiansToDegrees(
            FMath::Atan2(Delta.Y, Delta.X));
        const FTransform RouteTransform(FRotator(0.0f, Yaw, 0.0f),
            (Start + End) * 0.5f + FVector(0.0f, 0.0f, 4.0f),
            FVector(Length / 100.0f, 1.5f, 0.08f));
        AddItem(Items,
            FName(*FString::Printf(TEXT("OF_BODY_WELD_VIS_%s"),
                *Connection.ConnectionId.ToString())),
            Target->StationId, Target->LinePosition,
            ELBOneFactoryBodyWeldPresentationBatch::FloorRouteCube,
            RouteTransform);
    }
    return Items;
}

bool ALBOneFactoryBodyWeldStarterPresentationActor::
    ValidatePresentationContract(
        const FLBOneFactoryBodyWeldLayoutState& Layout,
        const TArray<FLBOneFactoryBodyWeldPresentationItem>& Items,
        FString& OutReason)
{
    using namespace LBOneFactoryBodyWeldPresentationPrivate;
    if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            Layout, OutReason))
    {
        return false;
    }
    const TArray<FLBOneFactoryBodyWeldPresentationItem> Expected =
        BuildExpectedPresentationItems(Layout);
    const int32 ExpectedCount = GetExpectedVisibleInstanceCount(Layout);
    if (Expected.Num() != ExpectedCount || Items.Num() != ExpectedCount)
    {
        OutReason = FString::Printf(TEXT(
            "BODY/WELD PRESENTATION REQUIRES EXACTLY %d VISUAL INSTANCES FOR THIS ROBOT ASSIGNMENT"),
            ExpectedCount);
        return false;
    }

    TSet<FName> Identities;
    TSet<ELBOneFactoryBodyWeldProgramme> PresentedProgrammes;
    TSet<FString> PresentedRobotSides;
    TMap<ELBOneFactoryBodyWeldPresentationBatch, int32> BatchCounts;
    for (int32 Index = 0; Index < Items.Num(); ++Index)
    {
        const FLBOneFactoryBodyWeldPresentationItem& Item = Items[Index];
        const FLBOneFactoryBodyWeldStationState* Station =
            FindStation(Layout, Item.StationId);
        if (Item.Version != 1 || Item.PresentationId.IsNone()
            || Item.StationId.IsNone() || !Station
            || Station->LinePosition != Item.LinePosition
            || Item.Batch >=
                ELBOneFactoryBodyWeldPresentationBatch::BatchCount
            || Item.bRepresentsProcessWIP
            || !IsFiniteTransform(Item.WorldTransform))
        {
            OutReason = TEXT(
                "BODY/WELD PRESENTATION HAS INVALID CORE DATA OR A WIP CLAIM");
            return false;
        }
        if (Identities.Contains(Item.PresentationId))
        {
            OutReason = TEXT(
                "BODY/WELD PRESENTATION IDENTITIES MUST BE UNIQUE");
            return false;
        }
        Identities.Add(Item.PresentationId);
        BatchCounts.FindOrAdd(Item.Batch) += 1;
        if (!SameItem(Item, Expected[Index]))
        {
            OutReason = TEXT(
                "BODY/WELD PRESENTATION INVENTORY OR TRANSFORM DRIFTED FROM V003");
            return false;
        }
        if (Item.bProgrammeFixture)
        {
            if (!Station->AssignedProgrammes.Contains(Item.Programme)
                || PresentedProgrammes.Contains(Item.Programme)
                || Item.Batch != FixtureBatchForProgramme(Item.Programme))
            {
                OutReason = TEXT(
                    "BODY/WELD PROGRAMME FIXTURE IS DUPLICATED, MISASSIGNED OR USES THE WRONG BATCH");
                return false;
            }
            PresentedProgrammes.Add(Item.Programme);
        }
        if (Item.RobotRole != ELBOneFactoryBodyWeldRobotRole::None)
        {
            const ELBOneFactoryBodyWeldRobotRole AssignedRole =
                Item.RobotSide == ELBOneFactoryBodyWeldRobotSide::Left
                    ? Station->LeftRobotRole : Station->RightRobotRole;
            if (Item.RobotRole != AssignedRole)
            {
                OutReason = TEXT(
                    "BODY/WELD ROBOT VISUAL DOES NOT MATCH ITS AUTHORITATIVE SIDE DUTY");
                return false;
            }
            if (Item.Batch ==
                ELBOneFactoryBodyWeldPresentationBatch::RobotRoleCube)
            {
                PresentedRobotSides.Add(FString::Printf(TEXT("%s:%d"),
                    *Item.StationId.ToString(),
                    static_cast<int32>(Item.RobotSide)));
            }
        }
    }

    if (Identities.Num() != ExpectedCount
        || PresentedProgrammes.Num() !=
            ULBOneFactoryBodyWeldStarterLayoutLibrary::
                RequiredProgrammeCount
        || PresentedRobotSides.Num() != 36)
    {
        OutReason = TEXT(
            "BODY/WELD PRESENTATION LOST A PROGRAMME, MIRRORED ROBOT SIDE OR STABLE ID");
        return false;
    }
    for (int32 Value = 0; Value < GetExpectedVisualBatchCount(); ++Value)
    {
        const ELBOneFactoryBodyWeldPresentationBatch Batch =
            static_cast<ELBOneFactoryBodyWeldPresentationBatch>(Value);
        if (BatchCounts.FindRef(Batch)
            != GetExpectedInstanceCountForBatch(Layout, Batch))
        {
            OutReason = TEXT(
                "BODY/WELD PRESENTATION BATCH COUNTS DRIFTED FROM V003");
            return false;
        }
    }
    OutReason = FString::Printf(TEXT(
        "BODY/WELD PRESENTATION CONTRACT VALID: 29 BATCHES, %d INSTANCES, 18 POSITIONS, 17 ROUTES, 36 LARGE ROBOTS, WIP 0"),
        ExpectedCount);
    return true;
}

bool ALBOneFactoryBodyWeldStarterPresentationActor::
    GetContactProcessPoseJointAngles(
        const ELBOneFactoryBodyWeldRobotSide Side, const int32 TargetIndex,
        TArray<float>& OutDegrees)
{
    using namespace LBOneFactoryBodyWeldPresentationPrivate;
    if (TargetIndex < 0 || TargetIndex > 2)
    {
        return false;
    }
    OutDegrees.Reset(6);
    const bool bLeft = Side == ELBOneFactoryBodyWeldRobotSide::Left;
    for (int32 JointIndex = 0; JointIndex < 6; ++JointIndex)
    {
        float Degrees = ContactProcessPoseDegrees[TargetIndex][JointIndex];
        if (!bLeft
            && (JointIndex == 0 || JointIndex == 3 || JointIndex == 5))
        {
            Degrees = -Degrees;
        }
        OutDegrees.Add(Degrees);
    }
    return true;
}

const TCHAR* ALBOneFactoryBodyWeldStarterPresentationActor::
    GetPresentationClassPath()
{
    return LBOneFactoryBodyWeldPresentationPrivate::
        ExpectedPresentationClassPath;
}

FName ALBOneFactoryBodyWeldStarterPresentationActor::GetPresentationTag()
{
    return TEXT("LB.OneFactory.BodyWeldStarter.Presentation.v003");
}
