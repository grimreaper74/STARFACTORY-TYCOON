#include "LBSupportRobotAuthorityRegistryV002.h"

#include "GameFramework/Actor.h"

namespace
{
    template <typename InterfaceType>
    InterfaceType* ResolveNativeInterface(const TWeakObjectPtr<UObject>& Candidate)
    {
        return Candidate.IsValid() ? Cast<InterfaceType>(Candidate.Get()) : nullptr;
    }
}

bool ULBSupportRobotAuthorityRegistryV002::RegisterRouteProvider(UObject* Provider)
{
    if (!IsValid(Provider) || Provider->GetWorld() != GetWorld()
        || Cast<ILBRouteAuthorityProviderV002>(Provider) == nullptr)
    {
        return false;
    }
    if (RouteProvider.IsValid() && RouteProvider.Get() != Provider)
    {
        return false;
    }
    RouteProvider = Provider;
    return true;
}

bool ULBSupportRobotAuthorityRegistryV002::RegisterDockProvider(UObject* Provider)
{
    if (!IsValid(Provider) || Provider->GetWorld() != GetWorld()
        || Cast<ILBDockAuthorityProviderV002>(Provider) == nullptr)
    {
        return false;
    }
    if (DockProvider.IsValid() && DockProvider.Get() != Provider)
    {
        return false;
    }
    DockProvider = Provider;
    return true;
}

bool ULBSupportRobotAuthorityRegistryV002::RegisterSafetyProvider(UObject* Provider)
{
    if (!IsValid(Provider) || Provider->GetWorld() != GetWorld()
        || Cast<ILBSafetyAuthorityProviderV002>(Provider) == nullptr)
    {
        return false;
    }
    if (SafetyProvider.IsValid() && SafetyProvider.Get() != Provider)
    {
        return false;
    }
    SafetyProvider = Provider;
    return true;
}

bool ULBSupportRobotAuthorityRegistryV002::RegisterCleaningProcessProvider(UObject* Provider)
{
    if (!IsValid(Provider) || Provider->GetWorld() != GetWorld()
        || Cast<ILBCleaningProcessAuthorityProviderV002>(Provider) == nullptr)
    {
        return false;
    }
    if (CleaningProcessProvider.IsValid() && CleaningProcessProvider.Get() != Provider)
    {
        return false;
    }
    CleaningProcessProvider = Provider;
    return true;
}

void ULBSupportRobotAuthorityRegistryV002::UnregisterProvider(UObject* Provider)
{
    if (RouteProvider.Get() == Provider) RouteProvider.Reset();
    if (DockProvider.Get() == Provider) DockProvider.Reset();
    if (SafetyProvider.Get() == Provider) SafetyProvider.Reset();
    if (CleaningProcessProvider.Get() == Provider) CleaningProcessProvider.Reset();
}

ILBRouteAuthorityProviderV002* ULBSupportRobotAuthorityRegistryV002::GetRouteProvider() const
{
    return ResolveNativeInterface<ILBRouteAuthorityProviderV002>(RouteProvider);
}

ILBDockAuthorityProviderV002* ULBSupportRobotAuthorityRegistryV002::GetDockProvider() const
{
    return ResolveNativeInterface<ILBDockAuthorityProviderV002>(DockProvider);
}

ILBSafetyAuthorityProviderV002* ULBSupportRobotAuthorityRegistryV002::GetSafetyProvider() const
{
    return ResolveNativeInterface<ILBSafetyAuthorityProviderV002>(SafetyProvider);
}

ILBCleaningProcessAuthorityProviderV002*
ULBSupportRobotAuthorityRegistryV002::GetCleaningProcessProvider() const
{
    return ResolveNativeInterface<ILBCleaningProcessAuthorityProviderV002>(
        CleaningProcessProvider);
}

bool ULBSupportRobotAuthorityRegistryV002::IssueRouteGrant(FName UnitId, FName VariantId,
    const FLBRouteRequestV002& Request, const AActor* Robot,
    FLBTrustedRouteGrantV002& OutGrant, FString& OutFailure)
{
    OutGrant = FLBTrustedRouteGrantV002();
    ILBRouteAuthorityProviderV002* Provider = GetRouteProvider();
    if (Provider == nullptr || UnitId.IsNone() || VariantId.IsNone()
        || Request.RouteId.IsNone() || Request.ExpectedRevision <= 0
        || !IsValid(Robot) || Robot->GetWorld() != GetWorld())
    {
        OutFailure = Provider == nullptr
            ? TEXT("No trusted native route authority provider is registered.")
            : TEXT("Route authority rejected an incomplete unit, variant or route request.");
        return false;
    }
    const bool bProviderIssued = Provider->IssueRouteGrantV002(
        UnitId, VariantId, Request, Robot, OutGrant, OutFailure);
    const bool bAccepted = bProviderIssued && OutGrant.IsStructurallyValid()
        && OutGrant.UnitId == UnitId
        && OutGrant.RouteId == Request.RouteId && OutGrant.Revision == Request.ExpectedRevision
        && OutGrant.bEmergencyDispatch == Request.bEmergencyDispatch;
    if (!bAccepted)
    {
        // A provider may have reserved a corridor before returning malformed or
        // mismatched output. Never strand that reservation at this boundary.
        if (OutGrant.GrantId.IsValid())
        {
            Provider->RevokeRouteGrantV002(OutGrant.GrantId,
                OutGrant.UnitId.IsNone() ? UnitId : OutGrant.UnitId);
        }
        OutGrant = FLBTrustedRouteGrantV002();
        if (OutFailure.IsEmpty())
        {
            OutFailure = TEXT("Route provider returned an invalid or identity-mismatched grant.");
        }
    }
    return bAccepted;
}

bool ULBSupportRobotAuthorityRegistryV002::RevalidateRouteGrant(const FLBTrustedRouteGrantV002& Grant,
    const AActor* Robot, FLBRouteSafetySnapshotV002& OutSafety, FString& OutFailure) const
{
    OutSafety = FLBRouteSafetySnapshotV002();
    ILBRouteAuthorityProviderV002* Provider = GetRouteProvider();
    return Provider != nullptr && Grant.IsStructurallyValid() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->RevalidateRouteGrantV002(Grant, Robot, OutSafety, OutFailure);
}

FLBRouteAdvanceResultV002 ULBSupportRobotAuthorityRegistryV002::AdvanceRoute(
    const FLBTrustedRouteGrantV002& Grant, AActor* Robot, double DeltaSeconds,
    double MaximumSpeedCentimetresPerSecond, double AccelerationCentimetresPerSecondSquared)
{
    FLBRouteAdvanceResultV002 Result;
    ILBRouteAuthorityProviderV002* Provider = GetRouteProvider();
    if (Provider == nullptr || !Grant.IsStructurallyValid() || !IsValid(Robot)
        || Robot->GetWorld() != GetWorld()
        || !FMath::IsFinite(DeltaSeconds) || DeltaSeconds <= 0.0
        || !FMath::IsFinite(MaximumSpeedCentimetresPerSecond) || MaximumSpeedCentimetresPerSecond < 0.0
        || !FMath::IsFinite(AccelerationCentimetresPerSecondSquared) || AccelerationCentimetresPerSecondSquared <= 0.0)
    {
        Result.FailureDetail = TEXT("Route advance rejected invalid authority, actor or finite motion input.");
        return Result;
    }
    Result = Provider->AdvanceAlongGrantedCorridorV002(Grant, Robot, DeltaSeconds,
        MaximumSpeedCentimetresPerSecond, AccelerationCentimetresPerSecondSquared);
    const double MaximumPlausibleDistanceCentimetres =
        MaximumSpeedCentimetresPerSecond * DeltaSeconds + 0.1;
    if (!FMath::IsFinite(Result.DistanceMovedCentimetres)
        || Result.DistanceMovedCentimetres < 0.0
        || Result.DistanceMovedCentimetres > MaximumPlausibleDistanceCentimetres)
    {
        Result.bSucceeded = false;
        Result.bRouteComplete = false;
        Result.DistanceMovedCentimetres = 0.0;
        Result.FailureDetail = TEXT("Route provider returned movement outside the finite commanded-speed envelope.");
    }
    return Result;
}

void ULBSupportRobotAuthorityRegistryV002::RevokeRouteGrant(const FGuid& GrantId, FName UnitId)
{
    if (ILBRouteAuthorityProviderV002* Provider = GetRouteProvider())
    {
        Provider->RevokeRouteGrantV002(GrantId, UnitId);
    }
}

bool ULBSupportRobotAuthorityRegistryV002::AcquireDockProof(FName UnitId, FName DockId,
    const AActor* Robot, FLBTrustedDockProofV002& OutProof, FString& OutFailure)
{
    OutProof = FLBTrustedDockProofV002();
    ILBDockAuthorityProviderV002* Provider = GetDockProvider();
    if (Provider == nullptr || UnitId.IsNone() || DockId.IsNone() || !IsValid(Robot)
        || Robot->GetWorld() != GetWorld())
    {
        OutFailure = TEXT("Dock authority rejected an invalid provider, identity, dock or actor.");
        return false;
    }
    const bool bProviderAcquired = Provider->AcquireDockProofV002(
        UnitId, DockId, Robot, OutProof, OutFailure);
    const bool bAccepted = bProviderAcquired && OutProof.IsComplete()
        && OutProof.UnitId == UnitId && OutProof.DockId == DockId;
    if (!bAccepted)
    {
        if (OutProof.ProofId.IsValid())
        {
            Provider->ReleaseDockProofV002(OutProof.ProofId,
                OutProof.UnitId.IsNone() ? UnitId : OutProof.UnitId);
        }
        OutProof = FLBTrustedDockProofV002();
        if (OutFailure.IsEmpty())
        {
            OutFailure = TEXT("Dock provider returned an incomplete or identity-mismatched proof.");
        }
    }
    return bAccepted;
}

bool ULBSupportRobotAuthorityRegistryV002::RevalidateDockProof(const FLBTrustedDockProofV002& Proof,
    const AActor* Robot, FString& OutFailure) const
{
    ILBDockAuthorityProviderV002* Provider = GetDockProvider();
    return Provider != nullptr && Proof.IsComplete() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->RevalidateDockProofV002(Proof, Robot, OutFailure);
}

void ULBSupportRobotAuthorityRegistryV002::ReleaseDockProof(const FGuid& ProofId, FName UnitId)
{
    if (ILBDockAuthorityProviderV002* Provider = GetDockProvider())
    {
        Provider->ReleaseDockProofV002(ProofId, UnitId);
    }
}

bool ULBSupportRobotAuthorityRegistryV002::ValidateCommissioningEvidence(FName UnitId, FName VariantId,
    FName StageId, FName EvidenceId, const AActor* Robot, FString& OutFailure) const
{
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && !VariantId.IsNone()
        && !StageId.IsNone() && !EvidenceId.IsNone() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->ValidateCommissioningEvidenceV002(
            UnitId, VariantId, StageId, EvidenceId, Robot, OutFailure);
}

bool ULBSupportRobotAuthorityRegistryV002::ValidateRouteRevalidation(FName UnitId, FName EvidenceId,
    const AActor* Robot, FString& OutFailure) const
{
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && !EvidenceId.IsNone() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->ValidateStoppedRouteRevalidationV002(UnitId, EvidenceId, Robot, OutFailure);
}

bool ULBSupportRobotAuthorityRegistryV002::ValidateFaultClearance(FName UnitId, FName VariantId,
    ELBSupportRobotCommonFaultV002 CommonFault, FName VariantFaultId, FName EvidenceId,
    const AActor* Robot, FString& OutFailure) const
{
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && !VariantId.IsNone()
        && !EvidenceId.IsNone() && IsValid(Robot) && Robot->GetWorld() == GetWorld()
        && (CommonFault != ELBSupportRobotCommonFaultV002::None || !VariantFaultId.IsNone())
        && Provider->ValidateFaultClearanceV002(UnitId, VariantId, CommonFault,
            VariantFaultId, EvidenceId, Robot, OutFailure);
}

bool ULBSupportRobotAuthorityRegistryV002::ValidateSensorCoverage(FName UnitId, FName VariantId,
    FName EvidenceId, const AActor* Robot, FString& OutFailure) const
{
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && !VariantId.IsNone()
        && !EvidenceId.IsNone() && IsValid(Robot) && Robot->GetWorld() == GetWorld()
        && Provider->ValidateSensorCoverageV002(UnitId, VariantId, EvidenceId, Robot, OutFailure);
}

bool ULBSupportRobotAuthorityRegistryV002::ValidateVariantTaskAuthority(FName UnitId,
    FName VariantId, FName TaskId, FName WorkAreaId, FName EvidenceId,
    const AActor* Robot, FString& OutFailure) const
{
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && !VariantId.IsNone()
        && !TaskId.IsNone() && !WorkAreaId.IsNone() && !EvidenceId.IsNone()
        && IsValid(Robot) && Robot->GetWorld() == GetWorld()
        && Provider->ValidateVariantTaskAuthorityV002(UnitId, VariantId, TaskId,
            WorkAreaId, EvidenceId, Robot, OutFailure);
}

bool ULBSupportRobotAuthorityRegistryV002::IssueWorkAuthority(FName UnitId, FName VariantId,
    FName WorkPointId, FName PermitId, FName TaskId, const AActor* Robot,
    FLBTrustedWorkAuthorityV002& OutGrant, FString& OutFailure)
{
    OutGrant = FLBTrustedWorkAuthorityV002();
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    if (Provider == nullptr || UnitId.IsNone() || VariantId.IsNone()
        || WorkPointId.IsNone() || PermitId.IsNone() || TaskId.IsNone()
        || !IsValid(Robot) || Robot->GetWorld() != GetWorld())
    {
        OutFailure = TEXT("Work authority rejected an invalid provider or incomplete identity.");
        return false;
    }
    const bool bProviderIssued = Provider->IssueWorkAuthorityV002(UnitId, VariantId,
        WorkPointId, PermitId, TaskId, Robot, OutGrant, OutFailure);
    const bool bAccepted = bProviderIssued && OutGrant.IsComplete()
        && OutGrant.UnitId == UnitId && OutGrant.WorkPointId == WorkPointId
        && OutGrant.PermitId == PermitId && OutGrant.TaskId == TaskId;
    if (!bAccepted)
    {
        if (OutGrant.GrantId.IsValid())
        {
            Provider->RevokeWorkAuthorityV002(OutGrant.GrantId,
                OutGrant.UnitId.IsNone() ? UnitId : OutGrant.UnitId);
        }
        OutGrant = FLBTrustedWorkAuthorityV002();
        if (OutFailure.IsEmpty())
        {
            OutFailure = TEXT("Safety provider returned an incomplete or identity-mismatched work grant.");
        }
    }
    return bAccepted;
}

bool ULBSupportRobotAuthorityRegistryV002::RevalidateWorkAuthority(
    const FLBTrustedWorkAuthorityV002& Grant, const AActor* Robot,
    FLBTrustedWorkAuthorityV002& OutCurrentProof, FString& OutFailure) const
{
    OutCurrentProof = FLBTrustedWorkAuthorityV002();
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && Grant.IsComplete() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->RevalidateWorkAuthorityV002(Grant, Robot, OutCurrentProof, OutFailure)
        && OutCurrentProof.IsComplete() && OutCurrentProof.GrantId == Grant.GrantId
        && OutCurrentProof.UnitId == Grant.UnitId && OutCurrentProof.TaskId == Grant.TaskId
        && OutCurrentProof.WorkPointId == Grant.WorkPointId
        && OutCurrentProof.PermitId == Grant.PermitId;
}

void ULBSupportRobotAuthorityRegistryV002::RevokeWorkAuthority(const FGuid& GrantId, FName UnitId)
{
    if (ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider())
    {
        Provider->RevokeWorkAuthorityV002(GrantId, UnitId);
    }
}

bool ULBSupportRobotAuthorityRegistryV002::AcquireOutriggerProof(FName UnitId, FName WorkPointId,
    const AActor* Robot, FLBTrustedOutriggerProofV002& OutProof, FString& OutFailure) const
{
    OutProof = FLBTrustedOutriggerProofV002();
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && !WorkPointId.IsNone() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->AcquireOutriggerProofV002(UnitId, WorkPointId, Robot, OutProof, OutFailure)
        && OutProof.HasFiniteFourLoads() && OutProof.UnitId == UnitId
        && OutProof.WorkPointId == WorkPointId;
}

bool ULBSupportRobotAuthorityRegistryV002::RevalidateOutriggerProof(
    const FLBTrustedOutriggerProofV002& Proof, const AActor* Robot,
    FLBTrustedOutriggerProofV002& OutCurrentProof, FString& OutFailure) const
{
    OutCurrentProof = FLBTrustedOutriggerProofV002();
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && Proof.HasFiniteFourLoads() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->RevalidateOutriggerProofV002(Proof, Robot, OutCurrentProof, OutFailure)
        && OutCurrentProof.HasFiniteFourLoads()
        && OutCurrentProof.ProofId == Proof.ProofId
        && OutCurrentProof.UnitId == Proof.UnitId
        && OutCurrentProof.WorkPointId == Proof.WorkPointId;
}

bool ULBSupportRobotAuthorityRegistryV002::AcquireTravelInterlockProof(FName UnitId,
    FName EvidenceId, const AActor* Robot, FLBTrustedTravelInterlockProofV002& OutProof,
    FString& OutFailure) const
{
    OutProof = FLBTrustedTravelInterlockProofV002();
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && !EvidenceId.IsNone() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->AcquireTravelInterlockProofV002(UnitId, EvidenceId, Robot, OutProof, OutFailure)
        && OutProof.IsCompleteForNormalTravel() && OutProof.UnitId == UnitId;
}

bool ULBSupportRobotAuthorityRegistryV002::RevalidateTravelInterlockProof(
    const FLBTrustedTravelInterlockProofV002& Proof, const AActor* Robot,
    FLBTrustedTravelInterlockProofV002& OutCurrentProof, FString& OutFailure) const
{
    OutCurrentProof = FLBTrustedTravelInterlockProofV002();
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && Proof.IsCompleteForNormalTravel() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->RevalidateTravelInterlockProofV002(Proof, Robot, OutCurrentProof, OutFailure)
        && OutCurrentProof.IsCompleteForNormalTravel()
        && OutCurrentProof.ProofId == Proof.ProofId && OutCurrentProof.UnitId == Proof.UnitId;
}

bool ULBSupportRobotAuthorityRegistryV002::AcquireToolCouplingProof(FName UnitId,
    FName ToolId, int32 RackSlot, FName EvidenceId, const AActor* Robot,
    FLBTrustedToolCouplingProofV002& OutProof, FString& OutFailure) const
{
    OutProof = FLBTrustedToolCouplingProofV002();
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && !ToolId.IsNone() && !EvidenceId.IsNone()
        && RackSlot >= 1 && RackSlot <= 8 && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->AcquireToolCouplingProofV002(UnitId, ToolId, RackSlot, EvidenceId,
            Robot, OutProof, OutFailure)
        && OutProof.IsComplete() && OutProof.UnitId == UnitId
        && OutProof.ToolId == ToolId && OutProof.RackSlot == RackSlot;
}

bool ULBSupportRobotAuthorityRegistryV002::RevalidateToolCouplingProof(
    const FLBTrustedToolCouplingProofV002& Proof, const AActor* Robot,
    FLBTrustedToolCouplingProofV002& OutCurrentProof, FString& OutFailure) const
{
    OutCurrentProof = FLBTrustedToolCouplingProofV002();
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && Proof.IsComplete() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->RevalidateToolCouplingProofV002(Proof, Robot, OutCurrentProof, OutFailure)
        && OutCurrentProof.IsComplete() && OutCurrentProof.ProofId == Proof.ProofId
        && OutCurrentProof.UnitId == Proof.UnitId && OutCurrentProof.ToolId == Proof.ToolId
        && OutCurrentProof.RackSlot == Proof.RackSlot;
}

bool ULBSupportRobotAuthorityRegistryV002::AcquireToolReturnProof(FName UnitId,
    FName ToolId, int32 RackSlot, FName EvidenceId, const AActor* Robot,
    FLBTrustedToolReturnProofV002& OutProof, FString& OutFailure) const
{
    OutProof = FLBTrustedToolReturnProofV002();
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && !ToolId.IsNone()
        && !EvidenceId.IsNone() && RackSlot >= 1 && RackSlot <= 8
        && IsValid(Robot) && Robot->GetWorld() == GetWorld()
        && Provider->AcquireToolReturnProofV002(
            UnitId, ToolId, RackSlot, EvidenceId, Robot, OutProof, OutFailure)
        && OutProof.IsComplete() && OutProof.UnitId == UnitId
        && OutProof.ToolId == ToolId && OutProof.RackSlot == RackSlot;
}

bool ULBSupportRobotAuthorityRegistryV002::ValidateArmParkedProof(FName UnitId,
    const AActor* Robot, FString& OutFailure) const
{
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->ValidateArmParkedProofV002(UnitId, Robot, OutFailure);
}

bool ULBSupportRobotAuthorityRegistryV002::ValidateTaskCompletionEvidence(FName UnitId,
    FName TaskId, FName PermitId, FName EvidenceId,
    const AActor* Robot, FString& OutFailure) const
{
    ILBSafetyAuthorityProviderV002* Provider = GetSafetyProvider();
    return Provider != nullptr && !UnitId.IsNone() && !TaskId.IsNone()
        && !PermitId.IsNone() && !EvidenceId.IsNone()
        && IsValid(Robot) && Robot->GetWorld() == GetWorld()
        && Provider->ValidateTaskCompletionEvidenceV002(UnitId, TaskId, PermitId,
            EvidenceId, Robot, OutFailure);
}

bool ULBSupportRobotAuthorityRegistryV002::IssueCleaningTaskGrant(FName UnitId,
    FName TaskId, FName CleaningZoneId, FName EvidenceId, const AActor* Robot,
    FLBTrustedCleaningTaskGrantV002& OutGrant, FString& OutFailure)
{
    OutGrant = FLBTrustedCleaningTaskGrantV002();
    ILBCleaningProcessAuthorityProviderV002* Provider = GetCleaningProcessProvider();
    if (Provider == nullptr || UnitId.IsNone() || TaskId.IsNone()
        || CleaningZoneId.IsNone() || EvidenceId.IsNone() || !IsValid(Robot)
        || Robot->GetWorld() != GetWorld())
    {
        OutFailure = TEXT("Cleaning authority rejected an invalid provider, identity or actor.");
        return false;
    }
    const bool bIssued = Provider->IssueCleaningTaskGrantV002(UnitId, TaskId,
        CleaningZoneId, EvidenceId, Robot, OutGrant, OutFailure);
    const bool bAccepted = bIssued && OutGrant.IsComplete() && OutGrant.UnitId == UnitId
        && OutGrant.TaskId == TaskId && OutGrant.CleaningZoneId == CleaningZoneId;
    if (!bAccepted)
    {
        if (OutGrant.GrantId.IsValid())
        {
            Provider->RevokeCleaningTaskGrantV002(OutGrant.GrantId,
                OutGrant.UnitId.IsNone() ? UnitId : OutGrant.UnitId);
        }
        OutGrant = FLBTrustedCleaningTaskGrantV002();
        if (OutFailure.IsEmpty())
        {
            OutFailure = TEXT("Cleaning provider returned an incomplete or identity-mismatched grant.");
        }
    }
    return bAccepted;
}

bool ULBSupportRobotAuthorityRegistryV002::RevalidateCleaningTaskGrant(
    const FLBTrustedCleaningTaskGrantV002& Grant, const AActor* Robot,
    FString& OutFailure) const
{
    ILBCleaningProcessAuthorityProviderV002* Provider = GetCleaningProcessProvider();
    return Provider != nullptr && Grant.IsComplete() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld()
        && Provider->RevalidateCleaningTaskGrantV002(Grant, Robot, OutFailure);
}

bool ULBSupportRobotAuthorityRegistryV002::SampleCleaningProcess(
    const FLBTrustedCleaningTaskGrantV002& Grant, const AActor* Robot,
    double DeltaSeconds, FLBTrustedCleaningProcessSampleV002& OutSample,
    FString& OutFailure)
{
    OutSample = FLBTrustedCleaningProcessSampleV002();
    ILBCleaningProcessAuthorityProviderV002* Provider = GetCleaningProcessProvider();
    return Provider != nullptr && Grant.IsComplete() && IsValid(Robot)
        && Robot->GetWorld() == GetWorld() && FMath::IsFinite(DeltaSeconds)
        && DeltaSeconds > 0.0
        && Provider->SampleCleaningProcessV002(Grant, Robot, DeltaSeconds,
            OutSample, OutFailure)
        && OutSample.IsFiniteAndConsistentWith(Grant);
}

void ULBSupportRobotAuthorityRegistryV002::RevokeCleaningTaskGrant(
    const FGuid& GrantId, FName UnitId)
{
    if (ILBCleaningProcessAuthorityProviderV002* Provider = GetCleaningProcessProvider())
    {
        Provider->RevokeCleaningTaskGrantV002(GrantId, UnitId);
    }
}

bool ULBSupportRobotAuthorityRegistryV002::HasAllSharedProviders() const
{
    return GetRouteProvider() != nullptr && GetDockProvider() != nullptr && GetSafetyProvider() != nullptr;
}
