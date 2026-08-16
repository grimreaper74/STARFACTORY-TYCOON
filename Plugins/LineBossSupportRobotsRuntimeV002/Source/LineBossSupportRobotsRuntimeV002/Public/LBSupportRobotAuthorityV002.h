#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "LBSupportRobotRuntimeTypesV002.h"
#include "LBSupportRobotAuthorityV002.generated.h"

class AActor;

/**
 * Native-only route authority. Blueprint cannot implement this interface or mint
 * a route grant. The provider must own the certified route catalog/corridors.
 */
UINTERFACE(MinimalAPI, meta = (CannotImplementInterfaceInBlueprint))
class ULBRouteAuthorityProviderV002 : public UInterface
{
    GENERATED_BODY()
};

class LINEBOSSSUPPORTROBOTSRUNTIMEV002_API ILBRouteAuthorityProviderV002
{
    GENERATED_BODY()

public:
    virtual bool IssueRouteGrantV002(FName UnitId, FName VariantId,
        const FLBRouteRequestV002& Request, const AActor* Robot,
        FLBTrustedRouteGrantV002& OutGrant, FString& OutFailure) = 0;
    virtual bool RevalidateRouteGrantV002(const FLBTrustedRouteGrantV002& Grant, const AActor* Robot,
        FLBRouteSafetySnapshotV002& OutSafety, FString& OutFailure) const = 0;
    virtual FLBRouteAdvanceResultV002 AdvanceAlongGrantedCorridorV002(const FLBTrustedRouteGrantV002& Grant,
        AActor* Robot, double DeltaSeconds, double MaximumSpeedCentimetresPerSecond,
        double AccelerationCentimetresPerSecondSquared) = 0;
    virtual void RevokeRouteGrantV002(const FGuid& GrantId, FName UnitId) = 0;
};

/** Native-only dock proof. A route destination name is never itself docking proof. */
UINTERFACE(MinimalAPI, meta = (CannotImplementInterfaceInBlueprint))
class ULBDockAuthorityProviderV002 : public UInterface
{
    GENERATED_BODY()
};

class LINEBOSSSUPPORTROBOTSRUNTIMEV002_API ILBDockAuthorityProviderV002
{
    GENERATED_BODY()

public:
    virtual bool AcquireDockProofV002(FName UnitId, FName DockId, const AActor* Robot,
        FLBTrustedDockProofV002& OutProof, FString& OutFailure) = 0;
    virtual bool RevalidateDockProofV002(const FLBTrustedDockProofV002& Proof, const AActor* Robot,
        FString& OutFailure) const = 0;
    virtual void ReleaseDockProofV002(const FGuid& ProofId, FName UnitId) = 0;
};

/**
 * Native-only safety authority for evidence, permits and physical proofs. All
 * returned facts must be derived from current game systems, never caller bools.
 */
UINTERFACE(MinimalAPI, meta = (CannotImplementInterfaceInBlueprint))
class ULBSafetyAuthorityProviderV002 : public UInterface
{
    GENERATED_BODY()
};

class LINEBOSSSUPPORTROBOTSRUNTIMEV002_API ILBSafetyAuthorityProviderV002
{
    GENERATED_BODY()

public:
    virtual bool ValidateCommissioningEvidenceV002(FName UnitId, FName VariantId, FName StageId,
        FName EvidenceId, const AActor* Robot, FString& OutFailure) const = 0;
    virtual bool ValidateStoppedRouteRevalidationV002(FName UnitId, FName EvidenceId,
        const AActor* Robot, FString& OutFailure) const = 0;
    virtual bool ValidateFaultClearanceV002(FName UnitId, FName VariantId,
        ELBSupportRobotCommonFaultV002 CommonFault, FName VariantFaultId, FName EvidenceId,
        const AActor* Robot, FString& OutFailure) const = 0;
    virtual bool ValidateSensorCoverageV002(FName UnitId, FName VariantId, FName EvidenceId,
        const AActor* Robot, FString& OutFailure) const = 0;
    virtual bool ValidateVariantTaskAuthorityV002(FName UnitId, FName VariantId, FName TaskId,
        FName WorkAreaId, FName EvidenceId, const AActor* Robot, FString& OutFailure) const = 0;
    virtual bool IssueWorkAuthorityV002(FName UnitId, FName VariantId, FName WorkPointId,
        FName PermitId, FName TaskId, const AActor* Robot, FLBTrustedWorkAuthorityV002& OutGrant,
        FString& OutFailure) = 0;
    virtual bool RevalidateWorkAuthorityV002(const FLBTrustedWorkAuthorityV002& Grant,
        const AActor* Robot, FLBTrustedWorkAuthorityV002& OutCurrentProof,
        FString& OutFailure) const = 0;
    virtual void RevokeWorkAuthorityV002(const FGuid& GrantId, FName UnitId) = 0;
    virtual bool AcquireOutriggerProofV002(FName UnitId, FName WorkPointId,
        const AActor* Robot, FLBTrustedOutriggerProofV002& OutProof,
        FString& OutFailure) const = 0;
    virtual bool RevalidateOutriggerProofV002(const FLBTrustedOutriggerProofV002& Proof,
        const AActor* Robot, FLBTrustedOutriggerProofV002& OutCurrentProof,
        FString& OutFailure) const = 0;
    virtual bool AcquireTravelInterlockProofV002(FName UnitId, FName EvidenceId,
        const AActor* Robot, FLBTrustedTravelInterlockProofV002& OutProof,
        FString& OutFailure) const = 0;
    virtual bool RevalidateTravelInterlockProofV002(const FLBTrustedTravelInterlockProofV002& Proof,
        const AActor* Robot, FLBTrustedTravelInterlockProofV002& OutCurrentProof,
        FString& OutFailure) const = 0;
    virtual bool AcquireToolCouplingProofV002(FName UnitId, FName ToolId, int32 RackSlot,
        FName EvidenceId, const AActor* Robot, FLBTrustedToolCouplingProofV002& OutProof,
        FString& OutFailure) const = 0;
    virtual bool RevalidateToolCouplingProofV002(const FLBTrustedToolCouplingProofV002& Proof,
        const AActor* Robot, FLBTrustedToolCouplingProofV002& OutCurrentProof,
        FString& OutFailure) const = 0;
    virtual bool AcquireToolReturnProofV002(FName UnitId, FName ToolId, int32 RackSlot,
        FName EvidenceId, const AActor* Robot, FLBTrustedToolReturnProofV002& OutProof,
        FString& OutFailure) const = 0;
    virtual bool ValidateArmParkedProofV002(FName UnitId, const AActor* Robot,
        FString& OutFailure) const = 0;
    virtual bool ValidateTaskCompletionEvidenceV002(FName UnitId, FName TaskId, FName PermitId,
        FName EvidenceId, const AActor* Robot, FString& OutFailure) const = 0;
};

/** Native-only CR01 process authority; callers cannot select mode or mint consumption. */
UINTERFACE(MinimalAPI, meta = (CannotImplementInterfaceInBlueprint))
class ULBCleaningProcessAuthorityProviderV002 : public UInterface
{
    GENERATED_BODY()
};

class LINEBOSSSUPPORTROBOTSRUNTIMEV002_API ILBCleaningProcessAuthorityProviderV002
{
    GENERATED_BODY()

public:
    virtual bool IssueCleaningTaskGrantV002(FName UnitId, FName TaskId,
        FName CleaningZoneId, FName EvidenceId, const AActor* Robot,
        FLBTrustedCleaningTaskGrantV002& OutGrant, FString& OutFailure) = 0;
    virtual bool RevalidateCleaningTaskGrantV002(
        const FLBTrustedCleaningTaskGrantV002& Grant, const AActor* Robot,
        FString& OutFailure) const = 0;
    virtual bool SampleCleaningProcessV002(const FLBTrustedCleaningTaskGrantV002& Grant,
        const AActor* Robot, double DeltaSeconds,
        FLBTrustedCleaningProcessSampleV002& OutSample, FString& OutFailure) = 0;
    virtual void RevokeCleaningTaskGrantV002(const FGuid& GrantId, FName UnitId) = 0;
};
