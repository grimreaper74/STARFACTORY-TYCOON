#include "LBBodyShopRobotActor.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "LBBodyShopPresentationPalette.h"

namespace LBBodyShopRobotPrivate
{
    constexpr int32 JointCount = 6;
    constexpr float ArticulationSpeedDegreesPerSecond = 42.0f;
    constexpr float WeldWorkPoseHoldSeconds = 0.35f;
    constexpr float CredibleContactDistanceCm = 12.0f;
    constexpr float CredibleContactDirectionDot = 0.95f;
    constexpr float MinimumWipClearanceCm = 11.999985f;
    constexpr float MinimumFloorClearanceCm = 64.0f;
    constexpr float MinimumOuterFenceClearanceCm = 114.0f;
    constexpr float MinimumPairedRobotClearanceCm = 167.999969f;

    const TCHAR* BasePath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_Base_v001.SM_LB_BodyShopRobotNative_Base_v001");
    const TCHAR* J1Path =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J1_v001.SM_LB_BodyShopRobotNative_J1_v001");
    const TCHAR* J2Path =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J2_v001.SM_LB_BodyShopRobotNative_J2_v001");
    const TCHAR* J3Path =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J3_v001.SM_LB_BodyShopRobotNative_J3_v001");
    const TCHAR* J4Path =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J4_v001.SM_LB_BodyShopRobotNative_J4_v001");
    const TCHAR* J5Path =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J5_v001.SM_LB_BodyShopRobotNative_J5_v001");
    const TCHAR* J6Path =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J6_v001.SM_LB_BodyShopRobotNative_J6_v001");
    const TCHAR* PanelPick8CupToolPath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001.SM_LB_BodyShopTool_PanelPick8Cup_v001");
    const TCHAR* SpotCGunToolPath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001.SM_LB_BodyShopToolNative_OpenCGun_v001");
    const TCHAR* SprayApplicatorToolPath =
        TEXT("/Game/LineBoss/Candidates/PaintShop/SprayApplicator_v001/SM_LB_Paint_SprayApplicatorTool_v001.SM_LB_Paint_SprayApplicatorTool_v001");

    const FVector PivotLocations[JointCount] = {
        FVector(0.0f, 0.0f, 35.0f),
        FVector(0.0f, 0.0f, 45.0f),
        FVector(125.0f, 0.0f, 0.0f),
        FVector(125.0f, 0.0f, 0.0f),
        FVector::ZeroVector,
        FVector::ZeroVector
    };
    const float JointMinimum[JointCount] = {
        -110.0f, -80.0f, -10.0f, -180.0f, 0.0f, -180.0f
    };
    const float JointMaximum[JointCount] = {
        110.0f, 65.0f, 120.0f, 180.0f, 145.0f, 180.0f
    };

    constexpr int32 WeldSideCount = 2;
    constexpr int32 WeldWorkPoseCount = 3;
    constexpr int32 WeldPhaseCount = 3;
    constexpr int32 LeftWeldSideIndex = 0;
    constexpr int32 RightWeldSideIndex = 1;
    constexpr int32 AcquirePhaseIndex = 0;
    constexpr int32 ProcessPhaseIndex = 1;
    constexpr int32 RetractPhaseIndex = 2;

    // Frozen Audit/contact_fk_validation_v001.json samples. Dimensions are
    // [left/right][target -X/centre/+X][acquire/process/retract][J1..J6].
    const float WeldPoseProgram[WeldSideCount][WeldWorkPoseCount]
        [WeldPhaseCount][JointCount] = {
        {
            {
                {91.456480f, -25.220006f, 13.790929f, -8.543199f, 89.700497f, 15.622156f},
                {91.240831f, -24.935079f, 15.949661f, -8.509025f, 87.252369f, 35.774566f},
                {91.456480f, -25.220006f, 13.790929f, -8.543199f, 89.700497f, 55.622145f}
            },
            {
                {55.000000f, -57.321082f, 69.880943f, 0.000001f, 62.962630f, -20.000000f},
                {55.000000f, -55.947736f, 70.469811f, 0.000001f, 61.000413f, -0.000005f},
                {55.000000f, -57.321082f, 69.880943f, 0.000001f, 62.962630f, 19.999991f}
            },
            {
                {18.543520f, -25.220006f, 13.790929f, 8.543201f, 89.700497f, -55.622150f},
                {18.759169f, -24.935079f, 15.949661f, 8.509027f, 87.252370f, -35.774574f},
                {18.543520f, -25.220006f, 13.790929f, 8.543201f, 89.700497f, -15.622161f}
            }
        },
        {
            {
                {-91.456480f, -25.220006f, 13.790929f, 8.543199f, 89.700497f, -55.622145f},
                {-91.240831f, -24.935079f, 15.949661f, 8.509028f, 87.252371f, -35.774578f},
                {-91.456480f, -25.220006f, 13.790929f, 8.543199f, 89.700497f, -15.622156f}
            },
            {
                {-55.000000f, -57.321082f, 69.880943f, 0.000001f, 62.962630f, -19.999997f},
                {-55.000000f, -55.947736f, 70.469811f, 0.000001f, 61.000413f, -0.000003f},
                {-55.000000f, -57.321082f, 69.880943f, 0.000001f, 62.962630f, 19.999993f}
            },
            {
                {-18.543520f, -25.220006f, 13.790929f, -8.543198f, 89.700496f, 15.622154f},
                {-18.759169f, -24.935079f, 15.949661f, -8.509027f, 87.252370f, 35.774574f},
                {-18.543520f, -25.220006f, 13.790929f, -8.543198f, 89.700496f, 55.622143f}
            }
        }
    };

    const FVector LeftFixtureWeldTargets[WeldWorkPoseCount] = {
        FVector(-140.0f, -95.0f, 98.0f),
        FVector(0.0f, -95.0f, 98.0f),
        FVector(140.0f, -95.0f, 98.0f)
    };
    const FVector WeldContactSocketRelative(52.0f, 0.0f, 0.0f);
    const FVector VacuumContacts[8] = {
        FVector(-80.0f, -50.0f, -31.0f), FVector(-27.0f, -50.0f, -31.0f),
        FVector(27.0f, -50.0f, -31.0f), FVector(80.0f, -50.0f, -31.0f),
        FVector(-80.0f, 50.0f, -31.0f), FVector(-27.0f, 50.0f, -31.0f),
        FVector(27.0f, 50.0f, -31.0f), FVector(80.0f, 50.0f, -31.0f)
    };

    bool IsLeftWeldSlot(const FName SlotId)
    {
        return SlotId == TEXT("ROBOT_WELD_LEFT");
    }

    bool IsRightWeldSlot(const FName SlotId)
    {
        return SlotId == TEXT("ROBOT_WELD_RIGHT");
    }

    int32 GetWeldSideIndex(const FName SlotId)
    {
        if (SlotId.IsNone() || IsLeftWeldSlot(SlotId)) return LeftWeldSideIndex;
        return IsRightWeldSlot(SlotId) ? RightWeldSideIndex : INDEX_NONE;
    }

    int32 GetWeldPhaseIndex(const ELBBodyShopRobotPose Pose)
    {
        switch (Pose)
        {
        case ELBBodyShopRobotPose::Acquire: return AcquirePhaseIndex;
        case ELBBodyShopRobotPose::Process: return ProcessPhaseIndex;
        case ELBBodyShopRobotPose::Retract: return RetractPhaseIndex;
        default: return INDEX_NONE;
        }
    }

    bool CopyWeldPose(const int32 WorkPoseIndex, const ELBBodyShopRobotPose Pose,
        const FName SlotId, TArray<float>& OutJointAngles)
    {
        OutJointAngles.Reset();
        const int32 SideIndex = GetWeldSideIndex(SlotId);
        const int32 PhaseIndex = GetWeldPhaseIndex(Pose);
        if (SideIndex == INDEX_NONE || PhaseIndex == INDEX_NONE
            || WorkPoseIndex < 0 || WorkPoseIndex >= WeldWorkPoseCount)
        {
            return false;
        }
        OutJointAngles.Reserve(JointCount);
        for (int32 JointIndex = 0; JointIndex < JointCount; ++JointIndex)
        {
            OutJointAngles.Add(FMath::Clamp(
                WeldPoseProgram[SideIndex][WorkPoseIndex][PhaseIndex][JointIndex],
                JointMinimum[JointIndex], JointMaximum[JointIndex]));
        }
        return true;
    }
}

ALBBodyShopRobotActor::ALBBodyShopRobotActor()
{
    PrimaryActorTick.bCanEverTick = true;
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("RobotRoot"));
    SetRootComponent(SceneRoot);
    J1Pivot = CreateDefaultSubobject<USceneComponent>(TEXT("PIVOT_J1_BASE_YAW_Z"));
    J1Pivot->SetupAttachment(SceneRoot);
    J2Pivot = CreateDefaultSubobject<USceneComponent>(TEXT("PIVOT_J2_SHOULDER_PITCH_Y"));
    J2Pivot->SetupAttachment(J1Pivot);
    J3Pivot = CreateDefaultSubobject<USceneComponent>(TEXT("PIVOT_J3_ELBOW_PITCH_Y"));
    J3Pivot->SetupAttachment(J2Pivot);
    J4Pivot = CreateDefaultSubobject<USceneComponent>(TEXT("PIVOT_J4_WRIST_ROLL_X"));
    J4Pivot->SetupAttachment(J3Pivot);
    J5Pivot = CreateDefaultSubobject<USceneComponent>(TEXT("PIVOT_J5_WRIST_PITCH_Y"));
    J5Pivot->SetupAttachment(J4Pivot);
    J6Pivot = CreateDefaultSubobject<USceneComponent>(TEXT("PIVOT_J6_TOOL_ROLL_X"));
    J6Pivot->SetupAttachment(J5Pivot);
    ToolFlange = CreateDefaultSubobject<USceneComponent>(TEXT("SOCKET_TOOL_FLANGE"));
    ToolFlange->SetupAttachment(J6Pivot);
    ToolAdapter = CreateDefaultSubobject<USceneComponent>(TEXT("FIXTURE_TOOL_ADAPTER"));
    ToolAdapter->SetupAttachment(ToolFlange);

    BasePresentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("BasePresentation"));
    BasePresentation->SetupAttachment(SceneRoot);
    J1Presentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("J1Presentation"));
    J1Presentation->SetupAttachment(J1Pivot);
    J2Presentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("J2Presentation"));
    J2Presentation->SetupAttachment(J2Pivot);
    J3Presentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("J3Presentation"));
    J3Presentation->SetupAttachment(J3Pivot);
    J4Presentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("J4Presentation"));
    J4Presentation->SetupAttachment(J4Pivot);
    J5Presentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("J5Presentation"));
    J5Presentation->SetupAttachment(J5Pivot);
    J6Presentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("J6Presentation"));
    J6Presentation->SetupAttachment(J6Pivot);
    ToolPresentation = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ToolPresentation"));
    ToolPresentation->SetupAttachment(ToolAdapter);
    for (UStaticMeshComponent* Component : {BasePresentation.Get(), J1Presentation.Get(),
        J2Presentation.Get(), J3Presentation.Get(), J4Presentation.Get(), J5Presentation.Get(),
        J6Presentation.Get(), ToolPresentation.Get()})
    {
        SetPresentationSafety(Component);
    }

    BaseMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopRobotPrivate::BasePath));
    J1Mesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopRobotPrivate::J1Path));
    J2Mesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopRobotPrivate::J2Path));
    J3Mesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopRobotPrivate::J3Path));
    J4Mesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopRobotPrivate::J4Path));
    J5Mesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopRobotPrivate::J5Path));
    J6Mesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopRobotPrivate::J6Path));
    PanelPick8CupToolMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopRobotPrivate::PanelPick8CupToolPath));
    SpotCGunToolMesh = TSoftObjectPtr<UStaticMesh>(FSoftObjectPath(LBBodyShopRobotPrivate::SpotCGunToolPath));
    SprayApplicatorToolMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopRobotPrivate::SprayApplicatorToolPath));
    CurrentJointAngles.Init(0.0f, LBBodyShopRobotPrivate::JointCount);
    TargetJointAngles.Init(0.0f, LBBodyShopRobotPrivate::JointCount);
    ConfigureHierarchy();
    Tags.AddUnique(TEXT("LB.BodyShop.Experimental.ArticulatedRobot.v001"));
    Tags.AddUnique(TEXT("LB.BodyShop.Experimental.WeldWorkCycle.v003"));
    Tags.AddUnique(TEXT("LB.BodyShop.Robot.NativeSixAxis.HighElbow.v001"));
}

void ALBBodyShopRobotActor::ConfigureHierarchy()
{
    J1Pivot->SetRelativeLocation(LBBodyShopRobotPrivate::PivotLocations[0]);
    J2Pivot->SetRelativeLocation(LBBodyShopRobotPrivate::PivotLocations[1]);
    J3Pivot->SetRelativeLocation(LBBodyShopRobotPrivate::PivotLocations[2]);
    J4Pivot->SetRelativeLocation(LBBodyShopRobotPrivate::PivotLocations[3]);
    J5Pivot->SetRelativeLocation(LBBodyShopRobotPrivate::PivotLocations[4]);
    J6Pivot->SetRelativeLocation(LBBodyShopRobotPrivate::PivotLocations[5]);
    ToolFlange->SetRelativeTransform(GetAuthoredToolFlangeRelativeTransform());
    ToolAdapter->SetRelativeTransform(FTransform::Identity);
}

void ALBBodyShopRobotActor::SetPresentationSafety(UStaticMeshComponent* Component) const
{
    if (!Component) return;
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
}

bool ALBBodyShopRobotActor::LoadCompleteArt(const ELBBodyShopToolType InTool, FString& OutReason)
{
    UStaticMesh* Meshes[] = {BaseMesh.LoadSynchronous(), J1Mesh.LoadSynchronous(),
        J2Mesh.LoadSynchronous(), J3Mesh.LoadSynchronous(), J4Mesh.LoadSynchronous(),
        J5Mesh.LoadSynchronous(), J6Mesh.LoadSynchronous()};
    UStaticMesh* Tool = nullptr;
    switch (InTool)
    {
    case ELBBodyShopToolType::VacuumEightCup:
        Tool = PanelPick8CupToolMesh.LoadSynchronous();
        break;
    case ELBBodyShopToolType::SprayApplicator:
        Tool = SprayApplicatorToolMesh.LoadSynchronous();
        break;
    default:
        Tool = SpotCGunToolMesh.LoadSynchronous();
        break;
    }
    if (!Meshes[0] || !Meshes[1] || !Meshes[2] || !Meshes[3] || !Meshes[4] || !Meshes[5]
        || !Meshes[6] || !Tool)
    {
        OutReason = TEXT("BODY SHOP ARTICULATED ROBOT REQUIRES EVERY LINK AND ITS AUTHORED TOOL");
        return false;
    }
    UStaticMeshComponent* Components[] = {BasePresentation.Get(), J1Presentation.Get(),
        J2Presentation.Get(), J3Presentation.Get(), J4Presentation.Get(), J5Presentation.Get(),
        J6Presentation.Get()};
    for (int32 Index = 0; Index < LBBodyShopRobotPrivate::JointCount + 1; ++Index)
    {
        Components[Index]->EmptyOverrideMaterials();
        Components[Index]->SetStaticMesh(Meshes[Index]);
        Components[Index]->SetVisibility(true, true);
        if (LBBodyShopPresentationPalette::ApplyToComponent(Components[Index])
            != Meshes[Index]->GetStaticMaterials().Num())
        {
            OutReason = TEXT("BODY SHOP ROBOT LINK IS MISSING ITS SEMANTIC PALETTE CONTRACT");
            return false;
        }
    }
    ToolPresentation->EmptyOverrideMaterials();
    ToolPresentation->SetStaticMesh(Tool);
    ToolPresentation->SetVisibility(true, true);
    if (LBBodyShopPresentationPalette::ApplyToComponent(ToolPresentation)
        != Tool->GetStaticMaterials().Num())
    {
        OutReason = TEXT("BODY SHOP ROBOT TOOL IS MISSING ITS SEMANTIC PALETTE CONTRACT");
        return false;
    }
    return true;
}

bool ALBBodyShopRobotActor::ConfigureForAuthoredSlot(const FName InCellId,
    const FLBBodyShopRobotSlotDefinition& InSlot,
    const FLBBodyShopRobotAssignment& InAssignment, FString& OutReason)
{
    OutReason.Reset();
    if (InCellId.IsNone() || InSlot.SlotId.IsNone() || !InSlot.AllowedRoles.Contains(InAssignment.Role)
        || !InSlot.AllowedTools.Contains(InAssignment.Tool) || !InAssignment.bEnabled
        || InAssignment.Condition01 <= 0.0f)
    {
        OutReason = TEXT("BODY SHOP ROBOT MUST USE AN ENABLED AUTHORISED FIXTURE SLOT");
        return false;
    }
    bCompleteArtPresentation = LoadCompleteArt(InAssignment.Tool, OutReason);
    if (!bCompleteArtPresentation) return false;
    OwningCellId = InCellId;
    SlotId = InSlot.SlotId;
    RobotRole = InAssignment.Role;
    ToolType = InAssignment.Tool;
    ToolAdapter->SetRelativeTransform(
        GetAuthoredToolAdapterRelativeTransform(RobotRole, SlotId));
    CurrentJointAngles.Init(0.0f, LBBodyShopRobotPrivate::JointCount);
    TargetJointAngles.Init(0.0f, LBBodyShopRobotPrivate::JointCount);
    CurrentPose = ELBBodyShopRobotPose::Home;
    TargetPose = ELBBodyShopRobotPose::Home;
    WeldWorkPoseIndex = INDEX_NONE;
    WeldWorkPoseHoldSeconds = 0.0f;
    bConfigured = true;
    Tags.AddUnique(OwningCellId);
    Tags.AddUnique(SlotId);
    ApplyJointTransforms();
    return true;
}

bool ALBBodyShopRobotActor::GetAuthoredJointLimits(const int32 JointIndex,
    float& OutMinimumDegrees, float& OutMaximumDegrees)
{
    if (JointIndex < 0 || JointIndex >= LBBodyShopRobotPrivate::JointCount) return false;
    OutMinimumDegrees = LBBodyShopRobotPrivate::JointMinimum[JointIndex];
    OutMaximumDegrees = LBBodyShopRobotPrivate::JointMaximum[JointIndex];
    return true;
}

int32 ALBBodyShopRobotActor::GetAuthoredJointCount()
{
    return LBBodyShopRobotPrivate::JointCount;
}

bool ALBBodyShopRobotActor::GetAuthoredPoseAngles(const ELBBodyShopRobotPose Pose,
    const ELBBodyShopRobotRole InRobotRole, TArray<float>& OutJointAngles)
{
    return GetAuthoredPoseAnglesForSlot(Pose, InRobotRole, NAME_None, OutJointAngles);
}

bool ALBBodyShopRobotActor::GetAuthoredPoseAnglesForSlot(const ELBBodyShopRobotPose Pose,
    const ELBBodyShopRobotRole InRobotRole, const FName AuthoredSlotId,
    TArray<float>& OutJointAngles)
{
    OutJointAngles.Init(0.0f, LBBodyShopRobotPrivate::JointCount);
    if (InRobotRole == ELBBodyShopRobotRole::None) return false;
    if (InRobotRole == ELBBodyShopRobotRole::SpotWelding)
    {
        if (Pose == ELBBodyShopRobotPose::Home || Pose == ELBBodyShopRobotPose::FaultSafe)
            return true;
        return LBBodyShopRobotPrivate::CopyWeldPose(
            0, Pose, AuthoredSlotId, OutJointAngles);
    }
    switch (Pose)
    {
    case ELBBodyShopRobotPose::Acquire:
        OutJointAngles = TArray<float>{-17.0f, 5.0f, -4.0f, 0.0f, 0.0f, 8.0f};
        break;
    case ELBBodyShopRobotPose::Process:
        OutJointAngles = TArray<float>{15.0f, -5.0f, 5.0f, 0.0f, 0.0f, -9.0f};
        break;
    case ELBBodyShopRobotPose::Retract:
        OutJointAngles = TArray<float>{5.0f, 2.0f, -2.0f, 0.0f, 0.0f, 4.0f};
        break;
    case ELBBodyShopRobotPose::FaultSafe:
    case ELBBodyShopRobotPose::Home:
    default:
        break;
    }
    for (int32 Index = 0; Index < LBBodyShopRobotPrivate::JointCount; ++Index)
    {
        OutJointAngles[Index] = FMath::Clamp(OutJointAngles[Index],
            LBBodyShopRobotPrivate::JointMinimum[Index], LBBodyShopRobotPrivate::JointMaximum[Index]);
    }
    return true;
}

int32 ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseCount()
{
    return LBBodyShopRobotPrivate::WeldWorkPoseCount;
}

bool ALBBodyShopRobotActor::GetAuthoredJointPivotRelativeLocation(
    const int32 JointIndex, FVector& OutPivotParentCm)
{
    OutPivotParentCm = FVector::ZeroVector;
    if (JointIndex < 0 || JointIndex >= LBBodyShopRobotPrivate::JointCount) return false;
    OutPivotParentCm = LBBodyShopRobotPrivate::PivotLocations[JointIndex];
    return true;
}

bool ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseAngles(const int32 WorkPoseIndex,
    const FName AuthoredSlotId, TArray<float>& OutJointAngles)
{
    return LBBodyShopRobotPrivate::CopyWeldPose(WorkPoseIndex,
        ELBBodyShopRobotPose::Process, AuthoredSlotId, OutJointAngles);
}

bool ALBBodyShopRobotActor::GetAuthoredWeldContactCandidate(const int32 WorkPoseIndex,
    const FName AuthoredSlotId, FVector& OutGunTipFixtureLocal,
    FVector& OutFixtureTargetLocal, FVector& OutGunApproachFixtureLocal)
{
    using namespace LBBodyShopRobotPrivate;
    OutGunTipFixtureLocal = FVector::ZeroVector;
    OutFixtureTargetLocal = FVector::ZeroVector;
    OutGunApproachFixtureLocal = FVector::ZeroVector;
    if (!IsLeftWeldSlot(AuthoredSlotId) && !IsRightWeldSlot(AuthoredSlotId)) return false;

    TArray<float> Angles;
    if (!GetAuthoredWeldWorkPoseAngles(WorkPoseIndex, AuthoredSlotId, Angles)) return false;
    FLBBodyShopCellDefinition Underbody;
    if (!FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(
        LBBodyShopPrototypeIds::UnderbodyFixture, Underbody)) return false;
    const FLBBodyShopRobotSlotDefinition* Slot = Underbody.RobotSlots.FindByPredicate(
        [AuthoredSlotId](const FLBBodyShopRobotSlotDefinition& Candidate)
        { return Candidate.SlotId == AuthoredSlotId; });
    if (!Slot) return false;

    FTransform FixtureTransform = Slot->LocalMountTransform;
    for (int32 JointIndex = 0; JointIndex < JointCount; ++JointIndex)
    {
        const FTransform JointTransform(
            GetAuthoredJointRelativeRotation(JointIndex, Angles[JointIndex]),
            PivotLocations[JointIndex]);
        FixtureTransform = JointTransform * FixtureTransform;
    }
    FixtureTransform = GetAuthoredToolFlangeRelativeTransform() * FixtureTransform;
    FixtureTransform = GetAuthoredToolAdapterRelativeTransform(
        ELBBodyShopRobotRole::SpotWelding, AuthoredSlotId) * FixtureTransform;
    OutGunTipFixtureLocal = FixtureTransform.TransformPosition(WeldContactSocketRelative);
    OutGunApproachFixtureLocal = FixtureTransform.TransformVectorNoScale(
        FVector::ForwardVector).GetSafeNormal();
    OutFixtureTargetLocal = LeftFixtureWeldTargets[WorkPoseIndex];
    if (IsRightWeldSlot(AuthoredSlotId)) OutFixtureTargetLocal.Y *= -1.0f;
    return !OutGunTipFixtureLocal.ContainsNaN() && !OutGunApproachFixtureLocal.ContainsNaN();
}

bool ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseKinematics(
    const int32 WorkPoseIndex, const FName AuthoredSlotId,
    FVector& OutShoulderFixtureLocal, FVector& OutElbowFixtureLocal,
    FVector& OutWristFixtureLocal)
{
    using namespace LBBodyShopRobotPrivate;
    OutShoulderFixtureLocal = FVector::ZeroVector;
    OutElbowFixtureLocal = FVector::ZeroVector;
    OutWristFixtureLocal = FVector::ZeroVector;
    if (!IsLeftWeldSlot(AuthoredSlotId) && !IsRightWeldSlot(AuthoredSlotId)) return false;

    TArray<float> Angles;
    if (!GetAuthoredWeldWorkPoseAngles(WorkPoseIndex, AuthoredSlotId, Angles)) return false;
    FLBBodyShopCellDefinition Underbody;
    if (!FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(
        LBBodyShopPrototypeIds::UnderbodyFixture, Underbody)) return false;
    const FLBBodyShopRobotSlotDefinition* Slot = Underbody.RobotSlots.FindByPredicate(
        [AuthoredSlotId](const FLBBodyShopRobotSlotDefinition& Candidate)
        { return Candidate.SlotId == AuthoredSlotId; });
    if (!Slot) return false;

    FTransform FixtureTransform = Slot->LocalMountTransform;
    for (int32 JointIndex = 0; JointIndex <= 3; ++JointIndex)
    {
        const FTransform JointTransform(
            GetAuthoredJointRelativeRotation(JointIndex, Angles[JointIndex]),
            PivotLocations[JointIndex]);
        FixtureTransform = JointTransform * FixtureTransform;
        if (JointIndex == 1) OutShoulderFixtureLocal = FixtureTransform.GetLocation();
        if (JointIndex == 2) OutElbowFixtureLocal = FixtureTransform.GetLocation();
        if (JointIndex == 3) OutWristFixtureLocal = FixtureTransform.GetLocation();
    }
    return !OutShoulderFixtureLocal.ContainsNaN() && !OutElbowFixtureLocal.ContainsNaN()
        && !OutWristFixtureLocal.ContainsNaN();
}

bool ALBBodyShopRobotActor::IsAuthoredWeldContactCandidateCredible(
    const int32 WorkPoseIndex, const FName AuthoredSlotId,
    float& OutTipToTargetDistanceCm, float& OutApproachToTargetDot)
{
    OutTipToTargetDistanceCm = TNumericLimits<float>::Max();
    OutApproachToTargetDot = -1.0f;
    FVector Tip;
    FVector Target;
    FVector Approach;
    if (!GetAuthoredWeldContactCandidate(
        WorkPoseIndex, AuthoredSlotId, Tip, Target, Approach)) return false;
    const FVector TipToTarget = Target - Tip;
    OutTipToTargetDistanceCm = TipToTarget.Size();
    OutApproachToTargetDot = FVector::DotProduct(
        Approach, TipToTarget.GetSafeNormal());
    return OutTipToTargetDistanceCm <= LBBodyShopRobotPrivate::CredibleContactDistanceCm
        && OutApproachToTargetDot >= LBBodyShopRobotPrivate::CredibleContactDirectionDot;
}

FTransform ALBBodyShopRobotActor::GetAuthoredToolFlangeRelativeTransform()
{
    return FTransform::Identity;
}

FTransform ALBBodyShopRobotActor::GetAuthoredToolAdapterRelativeTransform(
    const ELBBodyShopRobotRole InRobotRole, const FName AuthoredSlotId)
{
    (void)InRobotRole;
    (void)AuthoredSlotId;
    return FTransform::Identity;
}

FVector ALBBodyShopRobotActor::GetAuthoredWeldContactSocketRelativeLocation()
{
    return LBBodyShopRobotPrivate::WeldContactSocketRelative;
}

void ALBBodyShopRobotActor::GetAuthoredAnalyticalClearanceEvidence(
    float& OutMinimumWipClearanceCm, float& OutMinimumFloorClearanceCm,
    float& OutMinimumOuterFenceClearanceCm, float& OutMinimumPairedRobotClearanceCm)
{
    OutMinimumWipClearanceCm = LBBodyShopRobotPrivate::MinimumWipClearanceCm;
    OutMinimumFloorClearanceCm = LBBodyShopRobotPrivate::MinimumFloorClearanceCm;
    OutMinimumOuterFenceClearanceCm = LBBodyShopRobotPrivate::MinimumOuterFenceClearanceCm;
    OutMinimumPairedRobotClearanceCm = LBBodyShopRobotPrivate::MinimumPairedRobotClearanceCm;
}

void ALBBodyShopRobotActor::SetAuthoredPose(const ELBBodyShopRobotPose InPose, const bool bInstant)
{
    if (!bConfigured || (!bInstant && InPose == TargetPose)) return;
    if (RobotRole == ELBBodyShopRobotRole::SpotWelding
        && InPose == ELBBodyShopRobotPose::Process)
    {
        WeldWorkPoseIndex = 0;
        WeldWorkPoseHoldSeconds = 0.0f;
        if (!GetAuthoredWeldWorkPoseAngles(
            WeldWorkPoseIndex, SlotId, TargetJointAngles)) return;
    }
    else
    {
        WeldWorkPoseIndex = INDEX_NONE;
        WeldWorkPoseHoldSeconds = 0.0f;
        if (!GetAuthoredPoseAnglesForSlot(InPose, RobotRole, SlotId, TargetJointAngles)) return;
    }
    TargetPose = InPose;
    if (bInstant)
    {
        CurrentJointAngles = TargetJointAngles;
        CurrentPose = TargetPose;
        ApplyJointTransforms();
    }
}

void ALBBodyShopRobotActor::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bConfigured || !bArticulationRunning
        || CurrentJointAngles.Num() != LBBodyShopRobotPrivate::JointCount) return;
    bool bAtTarget = true;
    for (int32 Index = 0; Index < LBBodyShopRobotPrivate::JointCount; ++Index)
    {
        const float Next = FMath::FInterpConstantTo(CurrentJointAngles[Index], TargetJointAngles[Index],
            DeltaSeconds, LBBodyShopRobotPrivate::ArticulationSpeedDegreesPerSecond);
        bAtTarget &= FMath::IsNearlyEqual(Next, TargetJointAngles[Index], 0.01f);
        CurrentJointAngles[Index] = Next;
    }
    ApplyJointTransforms();
    if (bAtTarget)
    {
        CurrentPose = TargetPose;
        if (RobotRole == ELBBodyShopRobotRole::SpotWelding
            && TargetPose == ELBBodyShopRobotPose::Process)
        {
            WeldWorkPoseHoldSeconds += DeltaSeconds;
            if (WeldWorkPoseHoldSeconds >= LBBodyShopRobotPrivate::WeldWorkPoseHoldSeconds)
                AdvanceWeldWorkPose();
        }
    }
}

void ALBBodyShopRobotActor::AdvanceWeldWorkPose()
{
    if (RobotRole != ELBBodyShopRobotRole::SpotWelding
        || TargetPose != ELBBodyShopRobotPose::Process
        || LBBodyShopRobotPrivate::WeldWorkPoseCount <= 0) return;
    WeldWorkPoseIndex = (FMath::Max(0, WeldWorkPoseIndex) + 1)
        % LBBodyShopRobotPrivate::WeldWorkPoseCount;
    WeldWorkPoseHoldSeconds = 0.0f;
    GetAuthoredWeldWorkPoseAngles(WeldWorkPoseIndex, SlotId, TargetJointAngles);
}

void ALBBodyShopRobotActor::ApplyJointTransforms()
{
    const float J1 = CurrentJointAngles.IsValidIndex(0) ? CurrentJointAngles[0] : 0.0f;
    const float J2 = CurrentJointAngles.IsValidIndex(1) ? CurrentJointAngles[1] : 0.0f;
    const float J3 = CurrentJointAngles.IsValidIndex(2) ? CurrentJointAngles[2] : 0.0f;
    const float J4 = CurrentJointAngles.IsValidIndex(3) ? CurrentJointAngles[3] : 0.0f;
    const float J5 = CurrentJointAngles.IsValidIndex(4) ? CurrentJointAngles[4] : 0.0f;
    const float J6 = CurrentJointAngles.IsValidIndex(5) ? CurrentJointAngles[5] : 0.0f;
    J1Pivot->SetRelativeRotation(GetAuthoredJointRelativeRotation(0, J1));
    J2Pivot->SetRelativeRotation(GetAuthoredJointRelativeRotation(1, J2));
    J3Pivot->SetRelativeRotation(GetAuthoredJointRelativeRotation(2, J3));
    J4Pivot->SetRelativeRotation(GetAuthoredJointRelativeRotation(3, J4));
    J5Pivot->SetRelativeRotation(GetAuthoredJointRelativeRotation(4, J5));
    J6Pivot->SetRelativeRotation(GetAuthoredJointRelativeRotation(5, J6));
}

FRotator ALBBodyShopRobotActor::GetAuthoredJointRelativeRotation(
    const int32 JointIndex, const float JointAngleDegrees)
{
    switch (JointIndex)
    {
    case 0: // J1 local Z yaw.
        return FRotator(0.0f, JointAngleDegrees, 0.0f);
    case 1: // J2 local Y pitch.
    case 2: // J3 local Y pitch.
    case 4: // J5 local Y pitch.
        // Unreal's positive Pitch is opposite Blender's positive local-Y rotation.
        return FRotator(-JointAngleDegrees, 0.0f, 0.0f);
    case 3: // J4 local X wrist roll.
    case 5: // J6 local X tool roll.
        // Unreal's positive Roll is opposite Blender's positive local-X rotation.
        return FRotator(0.0f, 0.0f, -JointAngleDegrees);
    default:
        return FRotator::ZeroRotator;
    }
}

float ALBBodyShopRobotActor::GetJointAngleDegrees(const int32 JointIndex) const
{
    return CurrentJointAngles.IsValidIndex(JointIndex) ? CurrentJointAngles[JointIndex] : 0.0f;
}

FVector ALBBodyShopRobotActor::GetWeldGunPresentationTipLocation() const
{
    if (!bConfigured || ToolType != ELBBodyShopToolType::SpotCGun || !ToolAdapter)
        return FVector::ZeroVector;
    return ToolAdapter->GetComponentTransform().TransformPosition(
        LBBodyShopRobotPrivate::WeldContactSocketRelative);
}

FVector ALBBodyShopRobotActor::GetWeldGunPresentationApproachDirection() const
{
    if (!bConfigured || ToolType != ELBBodyShopToolType::SpotCGun || !ToolAdapter)
        return FVector::ZeroVector;
    return ToolAdapter->GetComponentTransform().TransformVectorNoScale(
        FVector::ForwardVector).GetSafeNormal();
}

int32 ALBBodyShopRobotActor::GetVacuumContactSocketCount() const
{
    return ToolType == ELBBodyShopToolType::VacuumEightCup ? UE_ARRAY_COUNT(LBBodyShopRobotPrivate::VacuumContacts) : 0;
}

FVector ALBBodyShopRobotActor::GetVacuumContactSocketLocation(const int32 SocketIndex) const
{
    if (ToolType != ELBBodyShopToolType::VacuumEightCup
        || SocketIndex < 0 || SocketIndex >= UE_ARRAY_COUNT(LBBodyShopRobotPrivate::VacuumContacts))
    {
        return FVector::ZeroVector;
    }
    return ToolFlange->GetComponentTransform().TransformPosition(
        LBBodyShopRobotPrivate::VacuumContacts[SocketIndex]);
}
