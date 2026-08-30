#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopRobotActor.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopRobotPoseContractTest,
    "LineBoss.BodyShop.Experimental.Robot.AuthoredPoseAndEightCupContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopRobotPoseContractTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    constexpr int32 JointCount = 6;
    const float ExpectedMinimum[JointCount] = {-110.0f, -80.0f, -10.0f, -180.0f, 0.0f, -180.0f};
    const float ExpectedMaximum[JointCount] = {110.0f, 65.0f, 120.0f, 180.0f, 145.0f, 180.0f};
    const FVector ExpectedPivots[JointCount] = {
        FVector(0.0f, 0.0f, 35.0f), FVector(0.0f, 0.0f, 45.0f),
        FVector(125.0f, 0.0f, 0.0f), FVector(125.0f, 0.0f, 0.0f),
        FVector::ZeroVector, FVector::ZeroVector
    };
    TestEqual(TEXT("Native robot exposes exactly six source-ordered joints"),
        ALBBodyShopRobotActor::GetAuthoredJointCount(), JointCount);
    for (int32 Joint = 0; Joint < JointCount; ++Joint)
    {
        float Minimum = 0.0f;
        float Maximum = 0.0f;
        FVector Pivot;
        TestTrue(TEXT("Each native articulated degree has explicit bounds"),
            ALBBodyShopRobotActor::GetAuthoredJointLimits(Joint, Minimum, Maximum));
        TestTrue(TEXT("Each native joint limit exactly matches the frozen manifest"),
            FMath::IsNearlyEqual(Minimum, ExpectedMinimum[Joint], 0.0001f)
            && FMath::IsNearlyEqual(Maximum, ExpectedMaximum[Joint], 0.0001f));
        TestTrue(TEXT("Each native joint exposes its exact parent-relative pivot"),
            ALBBodyShopRobotActor::GetAuthoredJointPivotRelativeLocation(Joint, Pivot)
            && Pivot.Equals(ExpectedPivots[Joint], 0.0001f));
    }
    float RejectedMinimum = 0.0f;
    float RejectedMaximum = 0.0f;
    FVector RejectedPivot;
    TestFalse(TEXT("A seventh joint cannot leak into the six-axis contract"),
        ALBBodyShopRobotActor::GetAuthoredJointLimits(6, RejectedMinimum, RejectedMaximum));
    TestFalse(TEXT("A seventh pivot cannot leak into the six-axis contract"),
        ALBBodyShopRobotActor::GetAuthoredJointPivotRelativeLocation(6, RejectedPivot));

    const FRotator J1 = ALBBodyShopRobotActor::GetAuthoredJointRelativeRotation(0, 7.0f);
    const FRotator J2 = ALBBodyShopRobotActor::GetAuthoredJointRelativeRotation(1, 7.0f);
    const FRotator J4 = ALBBodyShopRobotActor::GetAuthoredJointRelativeRotation(3, 7.0f);
    const FRotator J5 = ALBBodyShopRobotActor::GetAuthoredJointRelativeRotation(4, 7.0f);
    const FRotator J6 = ALBBodyShopRobotActor::GetAuthoredJointRelativeRotation(5, 7.0f);
    TestTrue(TEXT("J1 is the source local-Z yaw axis"),
        FMath::IsNearlyEqual(J1.Yaw, 7.0f) && FMath::IsNearlyZero(J1.Pitch)
        && FMath::IsNearlyZero(J1.Roll));
    TestTrue(TEXT("J2/J3/J5 use Blender-to-Unreal local-Y pitch conversion"),
        FMath::IsNearlyEqual(J2.Pitch, -7.0f)
        && FMath::IsNearlyEqual(J5.Pitch, -7.0f));
    TestTrue(TEXT("J4/J6 use Blender-to-Unreal local-X roll conversion"),
        FMath::IsNearlyEqual(J4.Roll, -7.0f)
        && FMath::IsNearlyEqual(J6.Roll, -7.0f));

    TestTrue(TEXT("Native source flange remains exact identity"),
        ALBBodyShopRobotActor::GetAuthoredToolFlangeRelativeTransform().Equals(
            FTransform::Identity, 0.0001f));
    TestTrue(TEXT("Native C-gun needs no fixture-specific correction adapter"),
        ALBBodyShopRobotActor::GetAuthoredToolAdapterRelativeTransform(
            ELBBodyShopRobotRole::SpotWelding, TEXT("ROBOT_WELD_LEFT")).Equals(
                FTransform::Identity, 0.0001f)
        && ALBBodyShopRobotActor::GetAuthoredToolAdapterRelativeTransform(
            ELBBodyShopRobotRole::SpotWelding, TEXT("ROBOT_WELD_RIGHT")).Equals(
                FTransform::Identity, 0.0001f));
    TestTrue(TEXT("Native weld-contact socket is exact +X 52 cm"),
        ALBBodyShopRobotActor::GetAuthoredWeldContactSocketRelativeLocation().Equals(
            FVector(52.0f, 0.0f, 0.0f), 0.0001f));

    TArray<float> HandlingAcquire;
    TArray<float> HandlingProcess;
    TArray<float> HandlingRetract;
    TestTrue(TEXT("Current vertical-slice panel handler keeps an authored six-axis process pose"),
        ALBBodyShopRobotActor::GetAuthoredPoseAngles(ELBBodyShopRobotPose::Process,
            ELBBodyShopRobotRole::PanelHandling, HandlingProcess));
    ALBBodyShopRobotActor::GetAuthoredPoseAngles(ELBBodyShopRobotPose::Acquire,
        ELBBodyShopRobotRole::PanelHandling, HandlingAcquire);
    ALBBodyShopRobotActor::GetAuthoredPoseAngles(ELBBodyShopRobotPose::Retract,
        ELBBodyShopRobotRole::PanelHandling, HandlingRetract);
    TestEqual(TEXT("Panel-handler compatibility pose drives the full six-joint array"),
        HandlingProcess.Num(), JointCount);
    TestTrue(TEXT("Panel-handler compatibility retains its bounded legacy roll on J6"),
        HandlingProcess.Num() == JointCount
        && FMath::IsNearlyEqual(HandlingProcess[5], -9.0f, 0.0001f));
    TestTrue(TEXT("Panel-handler acquire/process/retract remain distinct"),
        HandlingAcquire != HandlingProcess && HandlingRetract != HandlingProcess);
    TArray<float> RejectedNoRolePose;
    TestFalse(TEXT("No role means no robot path-programming pose"),
        ALBBodyShopRobotActor::GetAuthoredPoseAngles(ELBBodyShopRobotPose::Process,
            ELBBodyShopRobotRole::None, RejectedNoRolePose));

    const ELBBodyShopRobotPose StagePoses[] = {
        ELBBodyShopRobotPose::Acquire, ELBBodyShopRobotPose::Process,
        ELBBodyShopRobotPose::Retract
    };
    const float ExpectedLeftStage[][JointCount] = {
        {91.456480f, -25.220006f, 13.790929f, -8.543199f, 89.700497f, 15.622156f},
        {91.240831f, -24.935079f, 15.949661f, -8.509025f, 87.252369f, 35.774566f},
        {91.456480f, -25.220006f, 13.790929f, -8.543199f, 89.700497f, 55.622145f}
    };
    const float ExpectedRightStage[][JointCount] = {
        {-91.456480f, -25.220006f, 13.790929f, 8.543199f, 89.700497f, -55.622145f},
        {-91.240831f, -24.935079f, 15.949661f, 8.509028f, 87.252371f, -35.774578f},
        {-91.456480f, -25.220006f, 13.790929f, 8.543199f, 89.700497f, -15.622156f}
    };
    for (int32 StageIndex = 0; StageIndex < UE_ARRAY_COUNT(StagePoses); ++StageIndex)
    {
        TArray<float> LeftStage;
        TArray<float> RightStage;
        TestTrue(TEXT("Left weld slot has its exact frozen stage pose"),
            ALBBodyShopRobotActor::GetAuthoredPoseAnglesForSlot(StagePoses[StageIndex],
                ELBBodyShopRobotRole::SpotWelding, TEXT("ROBOT_WELD_LEFT"), LeftStage));
        TestTrue(TEXT("Right weld slot has its exact frozen stage pose"),
            ALBBodyShopRobotActor::GetAuthoredPoseAnglesForSlot(StagePoses[StageIndex],
                ELBBodyShopRobotRole::SpotWelding, TEXT("ROBOT_WELD_RIGHT"), RightStage));
        TestEqual(TEXT("Each frozen weld stage drives six joints"), LeftStage.Num(), JointCount);
        TestEqual(TEXT("Each mirrored frozen weld stage drives six joints"),
            RightStage.Num(), JointCount);
        if (LeftStage.Num() != JointCount || RightStage.Num() != JointCount) continue;
        for (int32 Joint = 0; Joint < JointCount; ++Joint)
        {
            TestTrue(TEXT("Left stage angle exactly matches the FK audit"),
                FMath::IsNearlyEqual(LeftStage[Joint], ExpectedLeftStage[StageIndex][Joint], 0.0001f));
            TestTrue(TEXT("Right stage angle exactly matches the FK audit"),
                FMath::IsNearlyEqual(RightStage[Joint], ExpectedRightStage[StageIndex][Joint], 0.0001f));
            TestTrue(TEXT("Left stage angle stays inside its source joint limit"),
                FMath::IsWithinInclusive(LeftStage[Joint], ExpectedMinimum[Joint], ExpectedMaximum[Joint]));
            TestTrue(TEXT("Right stage angle stays inside its source joint limit"),
                FMath::IsWithinInclusive(RightStage[Joint], ExpectedMinimum[Joint], ExpectedMaximum[Joint]));
        }
    }

    const float ExpectedLeftProcess[][JointCount] = {
        {91.240831f, -24.935079f, 15.949661f, -8.509025f, 87.252369f, 35.774566f},
        {55.000000f, -55.947736f, 70.469811f, 0.000001f, 61.000413f, -0.000005f},
        {18.759169f, -24.935079f, 15.949661f, 8.509027f, 87.252370f, -35.774574f}
    };
    const float ExpectedRightProcess[][JointCount] = {
        {-91.240831f, -24.935079f, 15.949661f, 8.509028f, 87.252371f, -35.774578f},
        {-55.000000f, -55.947736f, 70.469811f, 0.000001f, 61.000413f, -0.000003f},
        {-18.759169f, -24.935079f, 15.949661f, -8.509027f, 87.252370f, 35.774574f}
    };
    TestEqual(TEXT("Weld Process owns exactly three fixture work points"),
        ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseCount(), 3);
    float MinimumElbowRiseCm = TNumericLimits<float>::Max();
    float CentreElbowAboveWristCm = 0.0f;
    float MaximumContactDistanceCm = 0.0f;
    float MinimumDirectionDot = 1.0f;
    int32 CredibleContactCount = 0;
    for (int32 WorkPoseIndex = 0;
        WorkPoseIndex < ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseCount();
        ++WorkPoseIndex)
    {
        TArray<float> LeftWorkPose;
        TArray<float> RightWorkPose;
        TestTrue(TEXT("Left fixture work point has its exact frozen process pose"),
            ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseAngles(
                WorkPoseIndex, TEXT("ROBOT_WELD_LEFT"), LeftWorkPose));
        TestTrue(TEXT("Right fixture work point has its exact frozen process pose"),
            ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseAngles(
                WorkPoseIndex, TEXT("ROBOT_WELD_RIGHT"), RightWorkPose));
        if (LeftWorkPose.Num() != JointCount || RightWorkPose.Num() != JointCount) continue;
        for (int32 Joint = 0; Joint < JointCount; ++Joint)
        {
            TestTrue(TEXT("Left process angle exactly matches the FK audit"),
                FMath::IsNearlyEqual(LeftWorkPose[Joint],
                    ExpectedLeftProcess[WorkPoseIndex][Joint], 0.0001f));
            TestTrue(TEXT("Right process angle exactly matches the FK audit"),
                FMath::IsNearlyEqual(RightWorkPose[Joint],
                    ExpectedRightProcess[WorkPoseIndex][Joint], 0.0001f));
        }
        TestTrue(TEXT("Process mirror preserves J2/J3/J5 and mirrors J1/J4/J6"),
            FMath::IsNearlyEqual(LeftWorkPose[0], -RightWorkPose[0], 0.0001f)
            && FMath::IsNearlyEqual(LeftWorkPose[1], RightWorkPose[1], 0.0001f)
            && FMath::IsNearlyEqual(LeftWorkPose[2], RightWorkPose[2], 0.0001f)
            && FMath::IsNearlyEqual(LeftWorkPose[3], -RightWorkPose[3], 0.0001f)
            && FMath::IsNearlyEqual(LeftWorkPose[4], RightWorkPose[4], 0.0001f)
            && FMath::IsNearlyEqual(LeftWorkPose[5], -RightWorkPose[5], 0.0001f));

        FVector LeftTip;
        FVector LeftTarget;
        FVector LeftApproach;
        FVector RightTip;
        FVector RightTarget;
        FVector RightApproach;
        TestTrue(TEXT("Left work point resolves its native C-gun contact"),
            ALBBodyShopRobotActor::GetAuthoredWeldContactCandidate(WorkPoseIndex,
                TEXT("ROBOT_WELD_LEFT"), LeftTip, LeftTarget, LeftApproach));
        TestTrue(TEXT("Right work point resolves its native C-gun contact"),
            ALBBodyShopRobotActor::GetAuthoredWeldContactCandidate(WorkPoseIndex,
                TEXT("ROBOT_WELD_RIGHT"), RightTip, RightTarget, RightApproach));
        TestTrue(TEXT("Six underbody targets remain exact fixture-space mirrors"),
            FMath::IsNearlyEqual(LeftTarget.X, RightTarget.X, 0.01f)
            && FMath::IsNearlyEqual(LeftTarget.Y, -RightTarget.Y, 0.01f)
            && FMath::IsNearlyEqual(LeftTarget.Z, RightTarget.Z, 0.01f));
        TestTrue(TEXT("Native C-gun directions remain downward and inward"),
            FVector::DotProduct(LeftApproach, FVector::DownVector) > 0.95f
            && FVector::DotProduct(RightApproach, FVector::DownVector) > 0.95f
            && LeftApproach.Y > 0.24f && RightApproach.Y < -0.24f);

        float LeftDistanceCm = 0.0f;
        float LeftDirectionDot = 0.0f;
        float RightDistanceCm = 0.0f;
        float RightDirectionDot = 0.0f;
        const bool bLeftCredible =
            ALBBodyShopRobotActor::IsAuthoredWeldContactCandidateCredible(WorkPoseIndex,
                TEXT("ROBOT_WELD_LEFT"), LeftDistanceCm, LeftDirectionDot);
        const bool bRightCredible =
            ALBBodyShopRobotActor::IsAuthoredWeldContactCandidateCredible(WorkPoseIndex,
                TEXT("ROBOT_WELD_RIGHT"), RightDistanceCm, RightDirectionDot);
        TestTrue(TEXT("Frozen left native contact passes <=12 cm and dot>=0.95"), bLeftCredible);
        TestTrue(TEXT("Frozen right native contact passes <=12 cm and dot>=0.95"), bRightCredible);
        CredibleContactCount += bLeftCredible ? 1 : 0;
        CredibleContactCount += bRightCredible ? 1 : 0;
        MaximumContactDistanceCm = FMath::Max(MaximumContactDistanceCm,
            FMath::Max(LeftDistanceCm, RightDistanceCm));
        MinimumDirectionDot = FMath::Min(MinimumDirectionDot,
            FMath::Min(LeftDirectionDot, RightDirectionDot));
        TestTrue(TEXT("Process contact sits at the exact four-centimetre standoff"),
            FMath::IsNearlyEqual(LeftDistanceCm, 4.0f, 0.01f)
            && FMath::IsNearlyEqual(RightDistanceCm, 4.0f, 0.01f));
        TestTrue(TEXT("Process approach reaches its target along the contact axis"),
            LeftTip.Equals(LeftTarget - LeftApproach * LeftDistanceCm, 0.02f)
            && RightTip.Equals(RightTarget - RightApproach * RightDistanceCm, 0.02f));

        FVector LeftShoulder;
        FVector LeftElbow;
        FVector LeftWrist;
        FVector RightShoulder;
        FVector RightElbow;
        FVector RightWrist;
        TestTrue(TEXT("Left process pose exposes high-elbow kinematic points"),
            ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseKinematics(WorkPoseIndex,
                TEXT("ROBOT_WELD_LEFT"), LeftShoulder, LeftElbow, LeftWrist));
        TestTrue(TEXT("Right process pose exposes high-elbow kinematic points"),
            ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseKinematics(WorkPoseIndex,
                TEXT("ROBOT_WELD_RIGHT"), RightShoulder, RightElbow, RightWrist));
        TestTrue(TEXT("High-elbow process gate keeps J3 at least 45 cm above each shoulder"),
            LeftElbow.Z - LeftShoulder.Z >= 45.0f
            && RightElbow.Z - RightShoulder.Z >= 45.0f);
        TestTrue(TEXT("High-elbow kinematic points remain exact left/right mirrors"),
            LeftShoulder.Equals(FVector(RightShoulder.X, -RightShoulder.Y, RightShoulder.Z), 0.02f)
            && LeftElbow.Equals(FVector(RightElbow.X, -RightElbow.Y, RightElbow.Z), 0.02f)
            && LeftWrist.Equals(FVector(RightWrist.X, -RightWrist.Y, RightWrist.Z), 0.02f));
        MinimumElbowRiseCm = FMath::Min(MinimumElbowRiseCm,
            FMath::Min(LeftElbow.Z - LeftShoulder.Z, RightElbow.Z - RightShoulder.Z));
        if (WorkPoseIndex == 1)
            CentreElbowAboveWristCm = FMath::Min(
                LeftElbow.Z - LeftWrist.Z, RightElbow.Z - RightWrist.Z);
    }
    TestEqual(TEXT("All six mirrored process contacts pass the credibility gate"),
        CredibleContactCount, 6);
    TestTrue(TEXT("Process contact summary remains safely inside the frozen gate"),
        MaximumContactDistanceCm <= 4.01f && MinimumDirectionDot >= 0.999f);
    TestTrue(TEXT("Minimum process elbow rise matches the high-elbow audit"),
        FMath::IsNearlyEqual(MinimumElbowRiseCm, 52.698883f, 0.02f));
    TestTrue(TEXT("Centre management pose keeps J3 at least 20 cm above the wrist"),
        CentreElbowAboveWristCm >= 20.0f
        && FMath::IsNearlyEqual(CentreElbowAboveWristCm, 31.344131f, 0.02f));

    float MinimumWipClearanceCm = 0.0f;
    float MinimumFloorClearanceCm = 0.0f;
    float MinimumOuterFenceClearanceCm = 0.0f;
    float MinimumPairedRobotClearanceCm = 0.0f;
    ALBBodyShopRobotActor::GetAuthoredAnalyticalClearanceEvidence(
        MinimumWipClearanceCm, MinimumFloorClearanceCm,
        MinimumOuterFenceClearanceCm, MinimumPairedRobotClearanceCm);
    TestTrue(TEXT("Frozen analytical WIP clearance remains at least 11.99 cm"),
        MinimumWipClearanceCm >= 11.99f);
    TestTrue(TEXT("Frozen analytical floor/fence/paired-robot clearances remain positive"),
        FMath::IsNearlyEqual(MinimumFloorClearanceCm, 64.0f, 0.001f)
        && FMath::IsNearlyEqual(MinimumOuterFenceClearanceCm, 114.0f, 0.001f)
        && FMath::IsNearlyEqual(MinimumPairedRobotClearanceCm, 167.999969f, 0.001f));

    TArray<float> RejectedWorkPose;
    TestFalse(TEXT("Unknown work point cannot enter the weld articulation program"),
        ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseAngles(3,
            TEXT("ROBOT_WELD_LEFT"), RejectedWorkPose));
    TestFalse(TEXT("Free-placement slot cannot enter the weld articulation program"),
        ALBBodyShopRobotActor::GetAuthoredWeldWorkPoseAngles(0,
            TEXT("UNAUTHORISED_SLOT"), RejectedWorkPose));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopRobotMaterialV002ContractTest,
    "LineBoss.BodyShop.Experimental.Robot.MaterialsV002RobotEOATAndProtectedCGun",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopRobotMaterialV002ContractTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBBodyShopRobotMaterialV002ContractTest")));
    if (!TestNotNull(TEXT("Synthetic Body Shop robot world exists"), World)) return false;

    auto ConfigureRobot = [this, World](const ELBBodyShopRobotRole Role,
        const ELBBodyShopToolType Tool, const TCHAR* SlotName)
    {
        ALBBodyShopRobotActor* Robot = World->SpawnActor<ALBBodyShopRobotActor>();
        TestNotNull(TEXT("Articulated robot spawns"), Robot);
        if (!Robot) return;
        FLBBodyShopRobotSlotDefinition Slot;
        Slot.SlotId = FName(SlotName);
        Slot.AllowedRoles.Add(Role);
        Slot.AllowedTools.Add(Tool);
        FLBBodyShopRobotAssignment Assignment;
        Assignment.SlotId = Slot.SlotId;
        Assignment.Role = Role;
        Assignment.Tool = Tool;
        FString Reason;
        const bool bConfigured = Robot->ConfigureForAuthoredSlot(
            TEXT("TEST_CELL"), Slot, Assignment, Reason);
        TestTrue(TEXT("Robot resolves complete release material presentation"), bConfigured);
        TestTrue(TEXT("Configured robot reports complete art"),
            Robot->HasCompleteArtPresentation());
        if (bConfigured)
        {
            TArray<UStaticMeshComponent*> Presentations;
            Robot->GetComponents<UStaticMeshComponent>(Presentations);
            TSet<FName> PresentationNames;
            for (UStaticMeshComponent* Presentation : Presentations)
            {
                if (Presentation && Presentation->GetStaticMesh())
                    PresentationNames.Add(Presentation->GetFName());
            }
            TestEqual(TEXT("Complete robot has Base + J1..J6 + one EOAT presentation"),
                PresentationNames.Num(), 8);
            TestTrue(TEXT("Complete robot includes the new native J6 mesh component"),
                PresentationNames.Contains(TEXT("J6Presentation")));
            if (Role == ELBBodyShopRobotRole::PanelHandling)
            {
                TestEqual(TEXT("Panel handler retains exactly eight procedural vacuum contacts"),
                    Robot->GetVacuumContactSocketCount(), 8);
                TestTrue(TEXT("Panel handler retains a finite procedural vacuum contact"),
                    !Robot->GetVacuumContactSocketLocation(0).ContainsNaN());
            }
        }
        if (bConfigured && Role == ELBBodyShopRobotRole::SpotWelding)
        {
            Robot->SetAuthoredPose(ELBBodyShopRobotPose::Process, true);
            TestEqual(TEXT("Weld Process starts at authored work point zero"),
                Robot->GetCurrentWeldWorkPoseIndex(), 0);
            Robot->Tick(0.36f);
            TestEqual(TEXT("Weld Process advances after the exact bounded hold"),
                Robot->GetCurrentWeldWorkPoseIndex(), 1);
            const float StartingJ1 = Robot->GetJointAngleDegrees(0);
            Robot->Tick(0.20f);
            TestEqual(TEXT("Work-point transition stays on the active destination"),
                Robot->GetCurrentWeldWorkPoseIndex(), 1);
            TestTrue(TEXT("Work-point transition produces visible interpolated J1 travel"),
                FMath::Abs(Robot->GetJointAngleDegrees(0) - StartingJ1) > 8.0f);
            const float PausedJ1 = Robot->GetJointAngleDegrees(0);
            const float PausedJ6 = Robot->GetJointAngleDegrees(5);
            const int32 PausedWorkPose = Robot->GetCurrentWeldWorkPoseIndex();
            Robot->SetArticulationRunning(false);
            TestFalse(TEXT("Articulation pause state is observable"),
                Robot->IsArticulationRunning());
            Robot->Tick(2.0f);
            TestTrue(TEXT("Paused articulation freezes the exact interpolated joint frame"),
                FMath::IsNearlyEqual(Robot->GetJointAngleDegrees(0), PausedJ1, 0.001f)
                && FMath::IsNearlyEqual(Robot->GetJointAngleDegrees(5), PausedJ6, 0.001f));
            TestEqual(TEXT("Paused articulation cannot advance the weld work-point cycle"),
                Robot->GetCurrentWeldWorkPoseIndex(), PausedWorkPose);
            Robot->SetArticulationRunning(true);
            TestTrue(TEXT("Articulation resume state is observable"),
                Robot->IsArticulationRunning());
            Robot->Tick(0.20f);
            TestTrue(TEXT("Resumed articulation continues from the held joint frame"),
                FMath::Abs(Robot->GetJointAngleDegrees(0) - PausedJ1) > 8.0f
                && FMath::Abs(Robot->GetJointAngleDegrees(5) - PausedJ6) > 8.0f);
            TestTrue(TEXT("Configured C-gun exposes a finite presentation-only tip"),
                !Robot->GetWeldGunPresentationTipLocation().ContainsNaN()
                && !Robot->GetWeldGunPresentationTipLocation().IsNearlyZero());
            TestTrue(TEXT("Configured C-gun exposes a normalised approach direction"),
                FMath::IsNearlyEqual(
                    Robot->GetWeldGunPresentationApproachDirection().Size(), 1.0f, 0.001f));
        }
    };

    ConfigureRobot(ELBBodyShopRobotRole::PanelHandling,
        ELBBodyShopToolType::VacuumEightCup, TEXT("TEST_HANDLING"));
    ConfigureRobot(ELBBodyShopRobotRole::SpotWelding,
        ELBBodyShopToolType::SpotCGun, TEXT("ROBOT_WELD_LEFT"));
    World->DestroyWorld(false);
    return true;
}

#endif
