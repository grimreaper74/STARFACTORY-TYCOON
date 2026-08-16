#pragma once

#include "CoreMinimal.h"
#include "LBSupportRobotRuntimeTypesV002.generated.h"

UENUM(BlueprintType)
enum class ELBSupportRobotCommissioningStateV002 : uint8
{
    Mothballed,
    Inspection,
    RepairRequired,
    ReadyForTest,
    ManualCommissioning,
    Calibration,
    RouteValidation,
    Certified
};

UENUM(BlueprintType)
enum class ELBSupportRobotOperatingStateV002 : uint8
{
    Stopped,
    Docked,
    Dispatched,
    Navigating,
    Working,
    Returning,
    Servicing,
    Charging,
    SafetyStop,
    Fault
};

UENUM(BlueprintType)
enum class ELBSupportRobotConditionV002 : uint8
{
    Mothballed,
    Surveyed,
    RepairInProgress,
    Restored,
    Commissioned
};

UENUM(BlueprintType)
enum class ELBSupportRobotCommonFaultV002 : uint8
{
    None,
    AnchorContractInvalid,
    RouteAuthorityUnavailable,
    RouteAuthorityLost,
    RouteObstructed,
    LocalisationLost,
    SafetyNetworkUnhealthy,
    ProtectiveFieldIntrusion,
    OpenGate,
    TrappedKeyBoundary,
    SuspendedLoadZone,
    LowTractionOrSpill,
    LowBattery,
    DockProofLost,
    VariantInterlockOpen,
    RestoreRevalidationRequired
};

UENUM(BlueprintType)
enum class ELBRouteSpeedClassV002 : uint8
{
    Docking,
    MachineApproach,
    OccupiedAisle,
    NormalTransit,
    EmergencyCertifiedClearRoute
};

/** Save DTO only. LastObservedTransform is diagnostic and is never applied by restore. */
USTRUCT(BlueprintType)
struct LINEBOSSSUPPORTROBOTSRUNTIMEV002_API FLBSupportRobotSafeSaveV002
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    int32 Version = 2;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    FName UnitId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    FName VariantId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    ELBSupportRobotCommissioningStateV002 CommissioningState = ELBSupportRobotCommissioningStateV002::Mothballed;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    ELBSupportRobotConditionV002 Condition = ELBSupportRobotConditionV002::Mothballed;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    ELBSupportRobotCommonFaultV002 PersistedFault = ELBSupportRobotCommonFaultV002::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    double BatteryStateOfChargePercent = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    double BatteryHealthPercent = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    double OperatingHours = 0.0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    int32 MissionCount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    int32 ServiceCycles = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    bool bCommissioningCertified = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Line Boss|Support Robots v002|Save")
    FTransform LastObservedTransform = FTransform::Identity;
};

/** Blueprint callers request an existing catalog route; they cannot submit certification or waypoints. */
USTRUCT(BlueprintType)
struct LINEBOSSSUPPORTROBOTSRUNTIMEV002_API FLBRouteRequestV002
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Line Boss|Support Robots v002|Route")
    FName RouteId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Line Boss|Support Robots v002|Route",
        meta = (ClampMin = "1"))
    int32 ExpectedRevision = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Line Boss|Support Robots v002|Route")
    bool bEmergencyDispatch = false;
};

/** Plain C++ grant: intentionally not reflected or constructible in Blueprint. */
struct FLBTrustedRouteGrantV002
{
    FGuid GrantId;
    FName UnitId = NAME_None;
    FName RouteId = NAME_None;
    int32 Revision = 0;
    ELBRouteSpeedClassV002 SpeedClass = ELBRouteSpeedClassV002::NormalTransit;
    FName DestinationDockId = NAME_None;
    bool bEmergencyDispatch = false;

    bool IsStructurallyValid() const
    {
        return GrantId.IsValid() && !UnitId.IsNone() && !RouteId.IsNone() && Revision > 0
            && static_cast<uint8>(SpeedClass)
                <= static_cast<uint8>(ELBRouteSpeedClassV002::EmergencyCertifiedClearRoute);
    }
};

struct FLBRouteSafetySnapshotV002
{
    bool bGrantValid = false;
    bool bRouteClear = false;
    bool bLocalisationHealthy = false;
    bool bSafetyNetworkHealthy = false;
    bool bProtectiveFieldIntrusion = false;
    bool bSharedAisleOccupied = false;
    bool bMachineApproach = false;
    bool bDockingApproach = false;
    bool bOpenGate = false;
    bool bOpenTrappedKeyBoundary = false;
    bool bSuspendedLoadZoneIntersection = false;
    bool bLowTractionOrSpill = false;
};

struct FLBRouteAdvanceResultV002
{
    bool bSucceeded = false;
    bool bRouteComplete = false;
    double DistanceMovedCentimetres = 0.0;
    FString FailureDetail;
};

enum class ELBCleaningModeV002 : uint8
{
    DrySweep,
    WetScrub
};

struct FLBTrustedCleaningTaskGrantV002
{
    FGuid GrantId;
    FName UnitId = NAME_None;
    FName TaskId = NAME_None;
    FName CleaningZoneId = NAME_None;
    ELBCleaningModeV002 Mode = ELBCleaningModeV002::DrySweep;
    bool bZoneReserved = false;
    bool bProcessRecipeValid = false;

    bool IsComplete() const
    {
        return GrantId.IsValid() && !UnitId.IsNone() && !TaskId.IsNone()
            && !CleaningZoneId.IsNone() && bZoneReserved && bProcessRecipeValid;
    }
};

struct FLBTrustedCleaningProcessSampleV002
{
    FGuid GrantId;
    FName UnitId = NAME_None;
    FName TaskId = NAME_None;
    FName CleaningZoneId = NAME_None;
    ELBCleaningModeV002 Mode = ELBCleaningModeV002::DrySweep;
    uint64 Sequence = 0;
    double CoverageDeltaSquareMetres = 0.0;
    double CleanWaterConsumedLitres = 0.0;
    double RecoveryWaterAddedLitres = 0.0;
    double HopperLoadAddedLitres = 0.0;
    double FrontBrushWearConsumedPercent = 0.0;
    double SideBrushWearConsumedPercent = 0.0;
    double ScrubDiscWearConsumedPercent = 0.0;
    double SqueegeeWearConsumedPercent = 0.0;
    bool bCleaningHeadsProvedLowered = false;
    bool bBrushRotationProved = false;
    bool bWaterFlowProved = false;

    bool IsFiniteAndConsistentWith(const FLBTrustedCleaningTaskGrantV002& Grant) const
    {
        const bool bFiniteNonNegative = FMath::IsFinite(CoverageDeltaSquareMetres)
            && FMath::IsFinite(CleanWaterConsumedLitres)
            && FMath::IsFinite(RecoveryWaterAddedLitres)
            && FMath::IsFinite(HopperLoadAddedLitres)
            && FMath::IsFinite(FrontBrushWearConsumedPercent)
            && FMath::IsFinite(SideBrushWearConsumedPercent)
            && FMath::IsFinite(ScrubDiscWearConsumedPercent)
            && FMath::IsFinite(SqueegeeWearConsumedPercent)
            && CoverageDeltaSquareMetres >= 0.0 && CleanWaterConsumedLitres >= 0.0
            && RecoveryWaterAddedLitres >= 0.0 && HopperLoadAddedLitres >= 0.0
            && FrontBrushWearConsumedPercent >= 0.0 && SideBrushWearConsumedPercent >= 0.0
            && ScrubDiscWearConsumedPercent >= 0.0 && SqueegeeWearConsumedPercent >= 0.0;
        const bool bWetModeConsistent = Mode == ELBCleaningModeV002::WetScrub
            ? bWaterFlowProved : FMath::IsNearlyZero(CleanWaterConsumedLitres);
        return Grant.IsComplete() && GrantId == Grant.GrantId && UnitId == Grant.UnitId
            && TaskId == Grant.TaskId && CleaningZoneId == Grant.CleaningZoneId
            && Mode == Grant.Mode && Sequence > 0 && bFiniteNonNegative
            && bCleaningHeadsProvedLowered && bBrushRotationProved && bWetModeConsistent;
    }
};

struct FLBTrustedDockProofV002
{
    FGuid ProofId;
    FName UnitId = NAME_None;
    FName DockId = NAME_None;
    bool bDatumAligned = false;
    bool bChargeContactsProved = false;
    bool bNetworkContactProved = false;
    bool bParkingBrakeApplied = false;
    bool bLeakSensorsHealthy = false;

    bool IsComplete() const
    {
        return ProofId.IsValid() && !UnitId.IsNone() && !DockId.IsNone()
            && bDatumAligned && bChargeContactsProved && bNetworkContactProved
            && bParkingBrakeApplied && bLeakSensorsHealthy;
    }
};

struct FLBTrustedWorkAuthorityV002
{
    FGuid GrantId;
    FName UnitId = NAME_None;
    FName WorkPointId = NAME_None;
    FName PermitId = NAME_None;
    FName TaskId = NAME_None;
    bool bParkingBrakeApplied = false;
    bool bExclusionZoneReserved = false;
    bool bOutsideSuspendedLoadZone = false;
    bool bTaskAuthorityValid = false;
    bool bCellPermissionRequired = false;
    bool bCellPermissionGranted = false;
    bool bPlayerAuthorisationRequired = false;
    bool bPlayerAuthorisationGranted = false;
    bool bPhysicalLOTORequired = false;
    bool bPhysicalLOTOValid = false;
    double HandledPayloadMassKilograms = 0.0;
    bool bHandledPayloadMassProved = false;

    bool IsComplete() const
    {
        return GrantId.IsValid() && !UnitId.IsNone() && !WorkPointId.IsNone()
            && !PermitId.IsNone() && !TaskId.IsNone() && bParkingBrakeApplied
            && bExclusionZoneReserved && bOutsideSuspendedLoadZone && bTaskAuthorityValid
            && (!bCellPermissionRequired || bCellPermissionGranted)
            && (!bPlayerAuthorisationRequired || bPlayerAuthorisationGranted)
            && (!bPhysicalLOTORequired || bPhysicalLOTOValid)
            && bHandledPayloadMassProved && FMath::IsFinite(HandledPayloadMassKilograms)
            && HandledPayloadMassKilograms >= 0.0 && HandledPayloadMassKilograms <= 25.0;
    }
};

struct FLBTrustedOutriggerProofV002
{
    FGuid ProofId;
    FName UnitId = NAME_None;
    FName WorkPointId = NAME_None;
    bool bAllFourAtDeployedPosition = false;
    TArray<double> FootLoadsKilograms;
    double SupportedMassKilograms = 0.0;
    double MeasuredChassisTiltDegrees = 0.0;
    double MaximumPermittedChassisTiltDegrees = 0.0;
    bool bGroundBearingCapacityProved = false;
    bool bStabilityMarginProved = false;

    bool HasFiniteFourLoads() const
    {
        if (!ProofId.IsValid() || UnitId.IsNone() || WorkPointId.IsNone()
            || !bAllFourAtDeployedPosition || FootLoadsKilograms.Num() != 4
            || !FMath::IsFinite(SupportedMassKilograms) || SupportedMassKilograms <= 0.0
            || !FMath::IsFinite(MeasuredChassisTiltDegrees)
            || !FMath::IsFinite(MaximumPermittedChassisTiltDegrees)
            || MaximumPermittedChassisTiltDegrees <= 0.0
            || FMath::Abs(MeasuredChassisTiltDegrees) > MaximumPermittedChassisTiltDegrees
            || !bGroundBearingCapacityProved || !bStabilityMarginProved)
        {
            return false;
        }
        double TotalFootLoadKilograms = 0.0;
        for (const double Load : FootLoadsKilograms)
        {
            if (!FMath::IsFinite(Load) || Load <= 0.0)
            {
                return false;
            }
            TotalFootLoadKilograms += Load;
        }
        const double MassToleranceKilograms = FMath::Max(5.0, SupportedMassKilograms * 0.02);
        return FMath::IsNearlyEqual(TotalFootLoadKilograms,
            SupportedMassKilograms, MassToleranceKilograms);
    }
};

struct FLBTrustedTravelInterlockProofV002
{
    FGuid ProofId;
    FName UnitId = NAME_None;
    bool bArmParkingSwitchProved = false;
    bool bMastFullyStowed = false;
    bool bMastRestrictedTravelApproved = false;
    bool bAllOutriggersFullyStowed = false;
    bool bAllDoorsClosed = false;
    bool bPartsDrawerClosed = false;
    bool bPayloadSecured = false;
    bool bPayloadMassWithinLimit = false;
    bool bBrakesHealthy = false;
    bool bSteeringHealthy = false;
    bool bSafetyLidarHealthy = false;
    bool bSafetyCamerasHealthy = false;
    bool bPresentToolLocked = false;

    bool IsCompleteForNormalTravel() const
    {
        return ProofId.IsValid() && !UnitId.IsNone() && bArmParkingSwitchProved
            && (bMastFullyStowed || bMastRestrictedTravelApproved)
            && bAllOutriggersFullyStowed && bAllDoorsClosed && bPartsDrawerClosed
            && bPayloadSecured && bPayloadMassWithinLimit && bBrakesHealthy
            && bSteeringHealthy && bSafetyLidarHealthy && bSafetyCamerasHealthy
            && bPresentToolLocked;
    }

    bool IsCompleteForEmergencyTravel() const
    {
        return IsCompleteForNormalTravel() && bMastFullyStowed;
    }
};

struct FLBTrustedToolCouplingProofV002
{
    FGuid ProofId;
    FName UnitId = NAME_None;
    FName ToolId = NAME_None;
    int32 RackSlot = 0;
    double ToolMassKilograms = 0.0;
    double CarouselIndexAngleDegrees = 0.0;
    double StraightWithdrawalMillimetres = 0.0;
    double ClampTravelMillimetres = 0.0;
    bool bPresenceProved = false;
    bool bMechanicalLockProved = false;

    bool IsComplete() const
    {
        return ProofId.IsValid() && !UnitId.IsNone() && !ToolId.IsNone()
            && RackSlot >= 1 && RackSlot <= 8 && FMath::IsFinite(ToolMassKilograms)
            && ToolMassKilograms > 0.0 && ToolMassKilograms <= 12.0
            && FMath::IsFinite(CarouselIndexAngleDegrees)
            && FMath::IsNearlyEqual(CarouselIndexAngleDegrees,
                45.0 * static_cast<double>(RackSlot - 1), 0.25)
            && FMath::IsFinite(StraightWithdrawalMillimetres)
            && StraightWithdrawalMillimetres >= 350.0
            && FMath::IsFinite(ClampTravelMillimetres)
            && FMath::IsNearlyEqual(ClampTravelMillimetres, 12.0, 0.25)
            && bPresenceProved && bMechanicalLockProved;
    }
};

struct FLBTrustedToolReturnProofV002
{
    FGuid ProofId;
    FName UnitId = NAME_None;
    FName ToolId = NAME_None;
    int32 RackSlot = 0;
    bool bRackPresenceProved = false;
    bool bEndEffectorReleaseProved = false;

    bool IsComplete() const
    {
        return ProofId.IsValid() && !UnitId.IsNone() && !ToolId.IsNone()
            && RackSlot >= 1 && RackSlot <= 8
            && bRackPresenceProved && bEndEffectorReleaseProved;
    }
};

struct FLBAnchorSpecV002
{
    FName Name = NAME_None;
    FName ParentName = NAME_None;
    FVector RelativeLocationCentimetres = FVector::ZeroVector;
    FRotator RelativeRotationDegrees = FRotator::ZeroRotator;
    bool bRequired = true;
};

namespace LBSupportRobotFiniteV002
{
    inline bool IsFiniteVector(const FVector& Value)
    {
        return FMath::IsFinite(Value.X) && FMath::IsFinite(Value.Y) && FMath::IsFinite(Value.Z);
    }

    inline bool IsFiniteRotator(const FRotator& Value)
    {
        return FMath::IsFinite(Value.Pitch) && FMath::IsFinite(Value.Yaw) && FMath::IsFinite(Value.Roll);
    }

    inline bool IsFiniteTransform(const FTransform& Value)
    {
        const FQuat Rotation = Value.GetRotation();
        return IsFiniteVector(Value.GetTranslation()) && IsFiniteVector(Value.GetScale3D())
            && FMath::IsFinite(Rotation.X) && FMath::IsFinite(Rotation.Y)
            && FMath::IsFinite(Rotation.Z) && FMath::IsFinite(Rotation.W);
    }
}
