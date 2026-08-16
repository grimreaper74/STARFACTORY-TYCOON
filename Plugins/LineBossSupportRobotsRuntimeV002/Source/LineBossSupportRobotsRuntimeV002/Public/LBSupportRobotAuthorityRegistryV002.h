#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBSupportRobotAuthorityV002.h"
#include "LBSupportRobotAuthorityRegistryV002.generated.h"

/**
 * World-scoped native authority registry. Provider registration is deliberately
 * not reflected; Blueprint code cannot install a provider or fabricate proofs.
 */
UCLASS()
class LINEBOSSSUPPORTROBOTSRUNTIMEV002_API ULBSupportRobotAuthorityRegistryV002 : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    bool RegisterRouteProvider(UObject* Provider);
    bool RegisterDockProvider(UObject* Provider);
    bool RegisterSafetyProvider(UObject* Provider);
    bool RegisterCleaningProcessProvider(UObject* Provider);
    void UnregisterProvider(UObject* Provider);

    bool IssueRouteGrant(FName UnitId, FName VariantId, const FLBRouteRequestV002& Request,
        const AActor* Robot, FLBTrustedRouteGrantV002& OutGrant, FString& OutFailure);
    bool RevalidateRouteGrant(const FLBTrustedRouteGrantV002& Grant, const AActor* Robot,
        FLBRouteSafetySnapshotV002& OutSafety, FString& OutFailure) const;
    FLBRouteAdvanceResultV002 AdvanceRoute(const FLBTrustedRouteGrantV002& Grant, AActor* Robot,
        double DeltaSeconds, double MaximumSpeedCentimetresPerSecond,
        double AccelerationCentimetresPerSecondSquared);
    void RevokeRouteGrant(const FGuid& GrantId, FName UnitId);

    bool AcquireDockProof(FName UnitId, FName DockId, const AActor* Robot,
        FLBTrustedDockProofV002& OutProof, FString& OutFailure);
    bool RevalidateDockProof(const FLBTrustedDockProofV002& Proof, const AActor* Robot,
        FString& OutFailure) const;
    void ReleaseDockProof(const FGuid& ProofId, FName UnitId);

    bool ValidateCommissioningEvidence(FName UnitId, FName VariantId, FName StageId,
        FName EvidenceId, const AActor* Robot, FString& OutFailure) const;
    bool ValidateRouteRevalidation(FName UnitId, FName EvidenceId, const AActor* Robot,
        FString& OutFailure) const;
    bool ValidateFaultClearance(FName UnitId, FName VariantId,
        ELBSupportRobotCommonFaultV002 CommonFault, FName VariantFaultId,
        FName EvidenceId, const AActor* Robot, FString& OutFailure) const;
    bool ValidateSensorCoverage(FName UnitId, FName VariantId, FName EvidenceId,
        const AActor* Robot, FString& OutFailure) const;
    bool ValidateVariantTaskAuthority(FName UnitId, FName VariantId, FName TaskId,
        FName WorkAreaId, FName EvidenceId, const AActor* Robot, FString& OutFailure) const;
    bool IssueWorkAuthority(FName UnitId, FName VariantId, FName WorkPointId, FName PermitId,
        FName TaskId, const AActor* Robot, FLBTrustedWorkAuthorityV002& OutGrant,
        FString& OutFailure);
    bool RevalidateWorkAuthority(const FLBTrustedWorkAuthorityV002& Grant, const AActor* Robot,
        FLBTrustedWorkAuthorityV002& OutCurrentProof, FString& OutFailure) const;
    void RevokeWorkAuthority(const FGuid& GrantId, FName UnitId);
    bool AcquireOutriggerProof(FName UnitId, FName WorkPointId, const AActor* Robot,
        FLBTrustedOutriggerProofV002& OutProof, FString& OutFailure) const;
    bool RevalidateOutriggerProof(const FLBTrustedOutriggerProofV002& Proof,
        const AActor* Robot, FLBTrustedOutriggerProofV002& OutCurrentProof,
        FString& OutFailure) const;
    bool AcquireTravelInterlockProof(FName UnitId, FName EvidenceId, const AActor* Robot,
        FLBTrustedTravelInterlockProofV002& OutProof, FString& OutFailure) const;
    bool RevalidateTravelInterlockProof(const FLBTrustedTravelInterlockProofV002& Proof,
        const AActor* Robot, FLBTrustedTravelInterlockProofV002& OutCurrentProof,
        FString& OutFailure) const;
    bool AcquireToolCouplingProof(FName UnitId, FName ToolId, int32 RackSlot,
        FName EvidenceId, const AActor* Robot, FLBTrustedToolCouplingProofV002& OutProof,
        FString& OutFailure) const;
    bool RevalidateToolCouplingProof(const FLBTrustedToolCouplingProofV002& Proof,
        const AActor* Robot, FLBTrustedToolCouplingProofV002& OutCurrentProof,
        FString& OutFailure) const;
    bool AcquireToolReturnProof(FName UnitId, FName ToolId, int32 RackSlot,
        FName EvidenceId, const AActor* Robot, FLBTrustedToolReturnProofV002& OutProof,
        FString& OutFailure) const;
    bool ValidateArmParkedProof(FName UnitId, const AActor* Robot, FString& OutFailure) const;
    bool ValidateTaskCompletionEvidence(FName UnitId, FName TaskId, FName PermitId,
        FName EvidenceId, const AActor* Robot, FString& OutFailure) const;

    bool IssueCleaningTaskGrant(FName UnitId, FName TaskId, FName CleaningZoneId,
        FName EvidenceId, const AActor* Robot, FLBTrustedCleaningTaskGrantV002& OutGrant,
        FString& OutFailure);
    bool RevalidateCleaningTaskGrant(const FLBTrustedCleaningTaskGrantV002& Grant,
        const AActor* Robot, FString& OutFailure) const;
    bool SampleCleaningProcess(const FLBTrustedCleaningTaskGrantV002& Grant,
        const AActor* Robot, double DeltaSeconds, FLBTrustedCleaningProcessSampleV002& OutSample,
        FString& OutFailure);
    void RevokeCleaningTaskGrant(const FGuid& GrantId, FName UnitId);

    bool HasAllSharedProviders() const;

private:
    TWeakObjectPtr<UObject> RouteProvider;
    TWeakObjectPtr<UObject> DockProvider;
    TWeakObjectPtr<UObject> SafetyProvider;
    TWeakObjectPtr<UObject> CleaningProcessProvider;

    ILBRouteAuthorityProviderV002* GetRouteProvider() const;
    ILBDockAuthorityProviderV002* GetDockProvider() const;
    ILBSafetyAuthorityProviderV002* GetSafetyProvider() const;
    ILBCleaningProcessAuthorityProviderV002* GetCleaningProcessProvider() const;
};
