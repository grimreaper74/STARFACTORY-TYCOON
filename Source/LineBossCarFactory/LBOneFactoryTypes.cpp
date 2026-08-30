#include "LBOneFactoryTypes.h"

#include "LBPressShopBuildAuthority.h"

#include <initializer_list>

namespace LBOneFactoryTypesPrivate
{
    constexpr float LayoutToleranceCm = 0.1f;
    constexpr float TransformTolerance = 0.001f;

    bool IsFinitePositiveSize(const FVector& Size)
    {
        return FMath::IsFinite(Size.X) && FMath::IsFinite(Size.Y)
            && FMath::IsFinite(Size.Z) && Size.X > 0.0f && Size.Y > 0.0f
            && Size.Z > 0.0f;
    }

    bool IsStableTransform(const FTransform& Transform)
    {
        return !Transform.ContainsNaN()
            && Transform.GetScale3D().Equals(FVector::OneVector, TransformTolerance);
    }

    bool SameTransform(const FTransform& Left, const FTransform& Right)
    {
        return Left.Equals(Right, TransformTolerance);
    }

    bool SameDepartmentBay(const FLBOneFactoryDepartmentBay& Left,
        const FLBOneFactoryDepartmentBay& Right)
    {
        return Left.BayId == Right.BayId && Left.Department == Right.Department
            && SameTransform(Left.WorldTransform, Right.WorldTransform)
            && Left.SizeCm.Equals(Right.SizeCm, LayoutToleranceCm);
    }

    bool SameSharedSpine(const FLBOneFactorySharedSpine& Left,
        const FLBOneFactorySharedSpine& Right)
    {
        return Left.SpineId == Right.SpineId && Left.Role == Right.Role
            && SameTransform(Left.WorldTransform, Right.WorldTransform)
            && Left.SizeCm.Equals(Right.SizeCm, LayoutToleranceCm)
            && FMath::IsNearlyEqual(Left.MaximumReachCm, Right.MaximumReachCm,
                LayoutToleranceCm);
    }

    bool IsForbiddenSourceReference(const FString& SourceReference)
    {
        // The generator-name ban (Meshy/ExternalGenerated substrings) was
        // RETIRED on 2026-08-24; provenance is judged by its declared record.
        // Working-state and licence guards remain - raw downloads and
        // validation-only folders are never production sources.
        return SourceReference.Contains(TEXT("/Downloads/"), ESearchCase::IgnoreCase)
            || SourceReference.Contains(TEXT("/Developer/Validation/"), ESearchCase::IgnoreCase)
            || SourceReference.Contains(TEXT("/Vendor/"), ESearchCase::IgnoreCase);
    }

    FString NormaliseClassName(FString ClassName)
    {
        ClassName.TrimStartAndEndInline();
        ClassName.RemoveFromEnd(TEXT("_C"), ESearchCase::IgnoreCase);
        return ClassName;
    }

    bool MatchesAnyExactClass(const FString& ClassName,
        const std::initializer_list<const TCHAR*>& Candidates)
    {
        const FString Normalised = NormaliseClassName(ClassName);
        for (const TCHAR* Candidate : Candidates)
        {
            if (Normalised.Equals(Candidate, ESearchCase::IgnoreCase)) return true;
        }
        return false;
    }
}

FBox FLBOneFactoryDepartmentBay::GetWorldBounds() const
{
    return FBox(SizeCm * -0.5f, SizeCm * 0.5f).TransformBy(WorldTransform);
}

FBox FLBOneFactorySharedSpine::GetWorldBounds() const
{
    return FBox(SizeCm * -0.5f, SizeCm * 0.5f).TransformBy(WorldTransform);
}

FBox FLBOneFactoryLayoutDefinition::GetFactoryEnvelopeBounds() const
{
    return FBox(FactoryEnvelopeSizeCm * -0.5f,
        FactoryEnvelopeSizeCm * 0.5f).TransformBy(FactoryEnvelopeTransform);
}

FName LBOneFactoryIds::MoorcrossWorksLayout()
{
    static const FName Id(TEXT("MOORCROSS_WORKS_ONE_FACTORY_V001"));
    return Id;
}

FName LBOneFactoryIds::PressBay()
{
    static const FName Id(TEXT("OF_BAY_PRESS_01"));
    return Id;
}

FName LBOneFactoryIds::BodyBay()
{
    static const FName Id(TEXT("OF_BAY_BODY_01"));
    return Id;
}

FName LBOneFactoryIds::PaintBay()
{
    static const FName Id(TEXT("OF_BAY_PAINT_01"));
    return Id;
}

FName LBOneFactoryIds::AssemblyBay()
{
    static const FName Id(TEXT("OF_BAY_ASSEMBLY_01"));
    return Id;
}

FName LBOneFactoryIds::LogisticsSpine()
{
    static const FName Id(TEXT("OF_SPINE_LOGISTICS_EW_01"));
    return Id;
}

FName LBOneFactoryIds::ServiceSpine()
{
    static const FName Id(TEXT("OF_SPINE_SERVICE_EW_01"));
    return Id;
}

FLBOneFactoryLayoutDefinition ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout()
{
    FLBOneFactoryLayoutDefinition Layout;
    Layout.LayoutId = LBOneFactoryIds::MoorcrossWorksLayout();
    Layout.FactoryDisplayName = TEXT("Moorcross Works");
    Layout.FactoryEnvelopeTransform = FTransform(FRotator::ZeroRotator,
        FVector(0.0f, 0.0f, 1500.0f), FVector::OneVector);
    Layout.FactoryEnvelopeSizeCm = FVector(62000.0f, 31000.0f, 3000.0f);
    Layout.ProvenancePolicy = ELBOneFactoryProvenancePolicy::NativeOnly;
    Layout.bSeedStationsOnBeginPlay = false;

    auto AddDepartment = [&Layout](const FName BayId,
        const ELBOneFactoryDepartment Department, const FVector& Centre,
        const FVector& Size)
    {
        FLBOneFactoryDepartmentBay& Bay = Layout.DepartmentBays.AddDefaulted_GetRef();
        Bay.BayId = BayId;
        Bay.Department = Department;
        Bay.WorldTransform = FTransform(FRotator::ZeroRotator, Centre,
            FVector::OneVector);
        Bay.SizeCm = Size;
    };
    AddDepartment(LBOneFactoryIds::PressBay(), ELBOneFactoryDepartment::Press,
        FVector(-14500.0f, 8000.0f, 1000.0f),
        FVector(32000.0f, 13000.0f, 2000.0f));
    AddDepartment(LBOneFactoryIds::BodyBay(), ELBOneFactoryDepartment::Body,
        FVector(-11000.0f, -8500.0f, 1000.0f),
        FVector(18000.0f, 10000.0f, 2000.0f));
    AddDepartment(LBOneFactoryIds::PaintBay(), ELBOneFactoryDepartment::Paint,
        FVector(10000.0f, -8500.0f, 1000.0f),
        FVector(22000.0f, 10000.0f, 2000.0f));
    AddDepartment(LBOneFactoryIds::AssemblyBay(), ELBOneFactoryDepartment::Assembly,
        FVector(16500.0f, 8500.0f, 1000.0f),
        FVector(28000.0f, 12000.0f, 2000.0f));

    auto AddSpine = [&Layout](const FName SpineId,
        const ELBOneFactorySharedSpineRole Role, const FVector& Centre,
        const FVector& Size, const float MaximumReachCm)
    {
        FLBOneFactorySharedSpine& Spine = Layout.SharedSpines.AddDefaulted_GetRef();
        Spine.SpineId = SpineId;
        Spine.Role = Role;
        Spine.WorldTransform = FTransform(FRotator::ZeroRotator, Centre,
            FVector::OneVector);
        Spine.SizeCm = Size;
        Spine.MaximumReachCm = MaximumReachCm;
    };
    AddSpine(LBOneFactoryIds::LogisticsSpine(),
        ELBOneFactorySharedSpineRole::Logistics,
        FVector(0.0f, 0.0f, 200.0f), FVector(61000.0f, 1200.0f, 400.0f),
        1200.0f);
    AddSpine(LBOneFactoryIds::ServiceSpine(),
        ELBOneFactorySharedSpineRole::Service,
        FVector(0.0f, -14500.0f, 200.0f), FVector(61000.0f, 600.0f, 400.0f),
        30000.0f);
    return Layout;
}

bool ULBOneFactoryLayoutLibrary::ValidateLayout(
    const FLBOneFactoryLayoutDefinition& Layout, FString& OutReason)
{
    OutReason.Reset();
    if (Layout.LayoutId.IsNone() || Layout.FactoryDisplayName.TrimStartAndEnd().IsEmpty())
    {
        OutReason = TEXT("ONEFACTORY LAYOUT REQUIRES A STABLE ID AND DISPLAY NAME");
        return false;
    }
    if (!LBOneFactoryTypesPrivate::IsStableTransform(Layout.FactoryEnvelopeTransform)
        || !LBOneFactoryTypesPrivate::IsFinitePositiveSize(Layout.FactoryEnvelopeSizeCm))
    {
        OutReason = TEXT("ONEFACTORY ENVELOPE TRANSFORM OR SIZE IS INVALID");
        return false;
    }
    if (Layout.ProvenancePolicy != ELBOneFactoryProvenancePolicy::NativeOnly
        && Layout.ProvenancePolicy
            != ELBOneFactoryProvenancePolicy::GeneratedAllowed)
    {
        OutReason = TEXT("ONEFACTORY SHELL REQUIRES THE NATIVE-ONLY PROVENANCE POLICY");
        return false;
    }
    if (Layout.bSeedStationsOnBeginPlay)
    {
        OutReason = TEXT("ONEFACTORY SHELL MUST NOT SEED PRODUCTION STATIONS");
        return false;
    }
    if (Layout.DepartmentBays.Num() != 4)
    {
        OutReason = FString::Printf(TEXT("ONEFACTORY REQUIRES FOUR DEPARTMENT BAYS (FOUND %d)"),
            Layout.DepartmentBays.Num());
        return false;
    }
    if (Layout.SharedSpines.Num() != 2)
    {
        OutReason = FString::Printf(TEXT("ONEFACTORY REQUIRES TWO SHARED SPINES (FOUND %d)"),
            Layout.SharedSpines.Num());
        return false;
    }

    const FBox Envelope = Layout.GetFactoryEnvelopeBounds();
    if (!Envelope.IsValid)
    {
        OutReason = TEXT("ONEFACTORY ENVELOPE BOUNDS ARE INVALID");
        return false;
    }

    TSet<FName> StableIds;
    TSet<uint8> Departments;
    TArray<FBox> DepartmentBounds;
    for (const FLBOneFactoryDepartmentBay& Bay : Layout.DepartmentBays)
    {
        if (Bay.BayId.IsNone() || StableIds.Contains(Bay.BayId))
        {
            OutReason = TEXT("ONEFACTORY DEPARTMENT BAY IDS MUST BE NON-EMPTY AND UNIQUE");
            return false;
        }
        StableIds.Add(Bay.BayId);
        const uint8 DepartmentKey = static_cast<uint8>(Bay.Department);
        if (Departments.Contains(DepartmentKey))
        {
            OutReason = TEXT("ONEFACTORY REQUIRES EXACTLY ONE BAY PER DEPARTMENT");
            return false;
        }
        Departments.Add(DepartmentKey);
        if (!LBOneFactoryTypesPrivate::IsStableTransform(Bay.WorldTransform)
            || !LBOneFactoryTypesPrivate::IsFinitePositiveSize(Bay.SizeCm))
        {
            OutReason = FString::Printf(TEXT("ONEFACTORY BAY %s HAS AN INVALID TRANSFORM OR SIZE"),
                *Bay.BayId.ToString());
            return false;
        }
        const FBox Bounds = Bay.GetWorldBounds();
        if (!Envelope.ExpandBy(0.1f).IsInsideOrOn(Bounds.Min)
            || !Envelope.ExpandBy(0.1f).IsInsideOrOn(Bounds.Max))
        {
            OutReason = FString::Printf(TEXT("ONEFACTORY BAY %s IS OUTSIDE THE FACTORY ENVELOPE"),
                *Bay.BayId.ToString());
            return false;
        }
        DepartmentBounds.Add(Bounds);
    }
    if (Departments.Num() != 4
        || !Departments.Contains(static_cast<uint8>(ELBOneFactoryDepartment::Press))
        || !Departments.Contains(static_cast<uint8>(ELBOneFactoryDepartment::Body))
        || !Departments.Contains(static_cast<uint8>(ELBOneFactoryDepartment::Paint))
        || !Departments.Contains(static_cast<uint8>(ELBOneFactoryDepartment::Assembly)))
    {
        OutReason = TEXT("ONEFACTORY DEPARTMENT SET IS INCOMPLETE");
        return false;
    }
    for (int32 Left = 0; Left < DepartmentBounds.Num(); ++Left)
    {
        for (int32 Right = Left + 1; Right < DepartmentBounds.Num(); ++Right)
        {
            if (DepartmentBounds[Left].Intersect(DepartmentBounds[Right]))
            {
                OutReason = TEXT("ONEFACTORY DEPARTMENT BAYS MUST NOT OVERLAP");
                return false;
            }
        }
    }

    TSet<uint8> SpineRoles;
    TArray<FBox> SpineBounds;
    for (const FLBOneFactorySharedSpine& Spine : Layout.SharedSpines)
    {
        if (Spine.SpineId.IsNone() || StableIds.Contains(Spine.SpineId))
        {
            OutReason = TEXT("ONEFACTORY SPINE IDS MUST BE NON-EMPTY AND GLOBALLY UNIQUE");
            return false;
        }
        StableIds.Add(Spine.SpineId);
        const uint8 SpineRoleKey = static_cast<uint8>(Spine.Role);
        if (SpineRoles.Contains(SpineRoleKey))
        {
            OutReason = TEXT("ONEFACTORY REQUIRES ONE LOGISTICS AND ONE SERVICE SPINE");
            return false;
        }
        SpineRoles.Add(SpineRoleKey);
        if (!LBOneFactoryTypesPrivate::IsStableTransform(Spine.WorldTransform)
            || !LBOneFactoryTypesPrivate::IsFinitePositiveSize(Spine.SizeCm)
            || !FMath::IsFinite(Spine.MaximumReachCm) || Spine.MaximumReachCm <= 0.0f)
        {
            OutReason = FString::Printf(TEXT("ONEFACTORY SPINE %s HAS AN INVALID CONTRACT"),
                *Spine.SpineId.ToString());
            return false;
        }
        const FBox Bounds = Spine.GetWorldBounds();
        if (!Envelope.ExpandBy(0.1f).IsInsideOrOn(Bounds.Min)
            || !Envelope.ExpandBy(0.1f).IsInsideOrOn(Bounds.Max))
        {
            OutReason = FString::Printf(TEXT("ONEFACTORY SPINE %s IS OUTSIDE THE FACTORY ENVELOPE"),
                *Spine.SpineId.ToString());
            return false;
        }
        for (const FBox& BayBounds : DepartmentBounds)
        {
            if (Bounds.Intersect(BayBounds))
            {
                OutReason = FString::Printf(TEXT("ONEFACTORY SPINE %s OVERLAPS A DEPARTMENT BAY"),
                    *Spine.SpineId.ToString());
                return false;
            }
        }
        SpineBounds.Add(Bounds);
    }
    if (SpineRoles.Num() != 2
        || !SpineRoles.Contains(static_cast<uint8>(
            ELBOneFactorySharedSpineRole::Logistics))
        || !SpineRoles.Contains(static_cast<uint8>(
            ELBOneFactorySharedSpineRole::Service)))
    {
        OutReason = TEXT("ONEFACTORY SHARED SPINE ROLE SET IS INCOMPLETE");
        return false;
    }
    if (SpineBounds[0].Intersect(SpineBounds[1]))
    {
        OutReason = TEXT("ONEFACTORY SHARED SPINES MUST REMAIN DISTINCT");
        return false;
    }

    OutReason = TEXT("ONEFACTORY LAYOUT STRUCTURE VALID");
    return true;
}

bool ULBOneFactoryLayoutLibrary::ValidateMoorcrossWorksLayout(
    const FLBOneFactoryLayoutDefinition& Layout, FString& OutReason)
{
    if (!ValidateLayout(Layout, OutReason)) return false;
    const FLBOneFactoryLayoutDefinition Expected = MakeMoorcrossWorksShellLayout();
    if (Layout.LayoutId != Expected.LayoutId
        || Layout.FactoryDisplayName != Expected.FactoryDisplayName
        || !LBOneFactoryTypesPrivate::SameTransform(Layout.FactoryEnvelopeTransform,
            Expected.FactoryEnvelopeTransform)
        || !Layout.FactoryEnvelopeSizeCm.Equals(Expected.FactoryEnvelopeSizeCm,
            LBOneFactoryTypesPrivate::LayoutToleranceCm)
        || Layout.ProvenancePolicy != Expected.ProvenancePolicy
        || Layout.bSeedStationsOnBeginPlay != Expected.bSeedStationsOnBeginPlay)
    {
        OutReason = TEXT("MOORCROSS WORKS FACTORY ENVELOPE OR POLICY DRIFTED");
        return false;
    }
    for (int32 Index = 0; Index < Expected.DepartmentBays.Num(); ++Index)
    {
        if (!LBOneFactoryTypesPrivate::SameDepartmentBay(
            Layout.DepartmentBays[Index], Expected.DepartmentBays[Index]))
        {
            OutReason = FString::Printf(TEXT("MOORCROSS WORKS DEPARTMENT BAY %d DRIFTED"),
                Index);
            return false;
        }
    }
    for (int32 Index = 0; Index < Expected.SharedSpines.Num(); ++Index)
    {
        if (!LBOneFactoryTypesPrivate::SameSharedSpine(
            Layout.SharedSpines[Index], Expected.SharedSpines[Index]))
        {
            OutReason = FString::Printf(TEXT("MOORCROSS WORKS SHARED SPINE %d DRIFTED"),
                Index);
            return false;
        }
    }
    OutReason = TEXT("MOORCROSS WORKS ONEFACTORY SHELL LAYOUT VALID");
    return true;
}

bool ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
    const ELBOneFactoryProvenancePolicy Policy,
    const ELBOneFactoryAssetProvenance Provenance,
    const FString& SourceReference, FString& OutReason)
{
    OutReason.Reset();
    const bool bNativeOnly =
        Policy == ELBOneFactoryProvenancePolicy::NativeOnly;
    const bool bGeneratedAllowed =
        Policy == ELBOneFactoryProvenancePolicy::GeneratedAllowed;
    if (!bNativeOnly && !bGeneratedAllowed)
    {
        OutReason = TEXT("ONEFACTORY DOES NOT RECOGNISE THIS PROVENANCE POLICY");
        return false;
    }
    if (LBOneFactoryTypesPrivate::IsForbiddenSourceReference(SourceReference))
    {
        OutReason = FString::Printf(
            TEXT("SOURCE REFERENCE IS A NON-PRODUCTION LOCATION: %s"),
            *SourceReference);
        return false;
    }
    switch (Provenance)
    {
    case ELBOneFactoryAssetProvenance::NativeCode:
    case ELBOneFactoryAssetProvenance::NativeProcedural:
    case ELBOneFactoryAssetProvenance::NativeAuthored:
    case ELBOneFactoryAssetProvenance::VerifiedPreMeshyNative:
        OutReason = TEXT("ONEFACTORY NATIVE PROVENANCE ACCEPTED");
        return true;
    case ELBOneFactoryAssetProvenance::ExternalGenerated:
        // Accepted only under the spacecraft-era policy, and only with a
        // recorded source - a declared generator without a record is still
        // an unproven asset and fails closed.
        if (bGeneratedAllowed && !SourceReference.IsEmpty())
        {
            OutReason = TEXT("ONEFACTORY GENERATED PROVENANCE ACCEPTED WITH RECORD");
            return true;
        }
        OutReason = bGeneratedAllowed
            ? TEXT("GENERATED PROVENANCE REQUIRES A RECORDED SOURCE")
            : TEXT("ONEFACTORY REQUIRES VERIFIED NATIVE ASSET PROVENANCE");
        return false;
    default:
        OutReason = TEXT("ONEFACTORY REQUIRES VERIFIED NATIVE ASSET PROVENANCE");
        return false;
    }
}

bool ULBOneFactoryLayoutLibrary::IsProtectedMapPackageName(const FString& PackageName)
{
    static const TCHAR* ProtectedLeaves[] = {
        TEXT("LB_PressShop_RebuildFromLorry_v20260810_v913"),
        TEXT("LB_PressShop_FullFactoryRestored_v001"),
        TEXT("LB_BodyShop_Prototype_v001"),
        TEXT("LB_PaintShop_Prototype_v001")
    };
    for (const TCHAR* Leaf : ProtectedLeaves)
    {
        if (PackageName.Contains(Leaf, ESearchCase::IgnoreCase)) return true;
    }
    return false;
}

bool ULBOneFactoryLayoutLibrary::IsForbiddenLegacyActorClassName(
    const FString& ClassName)
{
    return LBOneFactoryTypesPrivate::MatchesAnyExactClass(ClassName, {
        TEXT("LBGameMode"),
        TEXT("LBFactoryEnvelopeShutterActor"),
        TEXT("LBFactoryEnvelopeSideDressingActor"),
        TEXT("LBInboundDeliveryController"),
        TEXT("LBCoilAGVController"),
        TEXT("LBCompactStillageFLT"),
        TEXT("LBStillageFLTFleetController"),
        TEXT("LBPressShopSupportFleetController"),
        TEXT("LBPressShopNavigationBootstrap"),
        TEXT("LBPressShopMaterialFlowController"),
        TEXT("LBBridgeCraneController"),
        TEXT("LBSupportCraneController"),
        TEXT("LBSupportRobot"),
        TEXT("LBSupportRobotServiceDock"),
        TEXT("LBCleaningAMR"),
        TEXT("LBMaintenanceAMR"),
        TEXT("LBControlRoomOperationsConsole"),
        TEXT("LBDeveloperAutomationBridge")
    });
}

bool ULBOneFactoryLayoutLibrary::IsMapOwnedProductionActorClassName(
    const FString& ClassName)
{
    const FString Normalised = LBOneFactoryTypesPrivate::NormaliseClassName(ClassName);
    if (Normalised.StartsWith(TEXT("LBPR"), ESearchCase::IgnoreCase)
        && Normalised.EndsWith(TEXT("Station"), ESearchCase::IgnoreCase))
    {
        return true;
    }
    return LBOneFactoryTypesPrivate::MatchesAnyExactClass(Normalised, {
        TEXT("LBFactoryBuildMachine"),
        TEXT("LBPressTrainAStation"),
        TEXT("LBPressShopStorageZone"),
        TEXT("LBFactoryTransportLink"),
        TEXT("LBPlayerBuiltPressFlowController"),
        TEXT("LBPressShopCampaignController"),
        TEXT("LBBodyWeldLineActor"),
        TEXT("LBECoatLineActor"),
        TEXT("LBBodyShopCellActor"),
        TEXT("LBBodyShopPrototypeRuntime"),
        TEXT("LBBodyShopPrototypeWorldBootstrap"),
        TEXT("LBBodyShopBuildAuthority"),
        TEXT("LBPaintShopCellActor"),
        TEXT("LBPaintShopPrototypeRuntime"),
        TEXT("LBPaintShopPrototypeWorldBootstrap"),
        TEXT("LBPaintShopBuildAuthority")
    });
}

bool ULBOneFactoryLayoutLibrary::ValidateWorldAudit(
    const FLBOneFactoryWorldAudit& Audit, FString& OutReason)
{
    OutReason.Reset();
    if (Audit.bProtectedMapPackage)
    {
        OutReason = TEXT("ONEFACTORY MUST NOT RUN INSIDE A PROTECTED LEGACY MAP PACKAGE");
        return false;
    }
    if (Audit.BootstrapCount != 1)
    {
        OutReason = FString::Printf(TEXT("ONEFACTORY REQUIRES EXACTLY ONE BOOTSTRAP (FOUND %d)"),
            Audit.BootstrapCount);
        return false;
    }
    if (Audit.PressBuildAuthorityCount != 1)
    {
        OutReason = FString::Printf(
            TEXT("ONEFACTORY REQUIRES EXACTLY ONE MAP-AUTHORED PRESS BUILD AUTHORITY (FOUND %d)"),
            Audit.PressBuildAuthorityCount);
        return false;
    }
    if (!Audit.bBootstrapUnowned || !Audit.bPressBuildAuthorityUnowned
        || !Audit.bPressBuildAuthorityMapTagged
        || !Audit.bBootstrapAndAuthorityShareLevel)
    {
        OutReason = TEXT("ONEFACTORY BOOTSTRAP AND TAGGED BUILD AUTHORITY MUST BE UNOWNED MAP PEERS");
        return false;
    }
    if (Audit.MapOwnedProductionActorCount != 0 || Audit.MapOwnedWIPActorCount != 0)
    {
        OutReason = FString::Printf(
            TEXT("ONEFACTORY SHELL MUST BE EMPTY OF PRODUCTION ACTORS AND WIP (ACTORS %d WIP %d)"),
            Audit.MapOwnedProductionActorCount, Audit.MapOwnedWIPActorCount);
        return false;
    }
    if (Audit.ForbiddenLegacyActorCount != 0)
    {
        OutReason = FString::Printf(TEXT("ONEFACTORY FOUND %d FORBIDDEN LEGACY ACTORS"),
            Audit.ForbiddenLegacyActorCount);
        return false;
    }
    if (Audit.ForbiddenProvenanceActorCount != 0)
    {
        OutReason = FString::Printf(TEXT("ONEFACTORY FOUND %d NON-NATIVE PRESENTATION ACTORS"),
            Audit.ForbiddenProvenanceActorCount);
        return false;
    }
    OutReason = TEXT("ONEFACTORY WORLD CARDINALITY AND ISOLATION VALID");
    return true;
}

void ULBOneFactoryLayoutLibrary::BuildExpectedPressAuthorityContract(
    const FLBOneFactoryLayoutDefinition& Layout,
    TArray<FLBPressShopBuildBay>& OutBuildBays,
    TArray<FLBPressShopProtectedArea>& OutProtectedAreas,
    TArray<FLBPressShopUtilitySpine>& OutUtilitySpines,
    TArray<FLBPressShopLogisticsSpine>& OutLogisticsSpines)
{
    OutBuildBays.Reset();
    OutProtectedAreas.Reset();
    OutUtilitySpines.Reset();
    OutLogisticsSpines.Reset();

    for (const FLBOneFactoryDepartmentBay& Department : Layout.DepartmentBays)
    {
        FLBPressShopBuildBay& Bay = OutBuildBays.AddDefaulted_GetRef();
        Bay.BayId = Department.BayId;
        Bay.Centre = Department.WorldTransform.GetLocation();
        Bay.HalfExtent = Department.SizeCm * 0.5f;
    }
    for (const FLBOneFactorySharedSpine& Shared : Layout.SharedSpines)
    {
        FLBPressShopProtectedArea& Protected = OutProtectedAreas.AddDefaulted_GetRef();
        Protected.AreaId = Shared.SpineId;
        Protected.Centre = Shared.WorldTransform.GetLocation();
        Protected.HalfExtent = Shared.SizeCm * 0.5f;

        const FVector LocalHalfLength(Shared.SizeCm.X * 0.5f, 0.0f, 0.0f);
        FVector Start = Shared.WorldTransform.TransformPosition(-LocalHalfLength);
        FVector End = Shared.WorldTransform.TransformPosition(LocalHalfLength);
        Start.Z = 0.0f;
        End.Z = 0.0f;
        if (Shared.Role == ELBOneFactorySharedSpineRole::Service)
        {
            FLBPressShopUtilitySpine& Utility = OutUtilitySpines.AddDefaulted_GetRef();
            Utility.SpineId = Shared.SpineId;
            Utility.Start = Start;
            Utility.End = End;
            Utility.MaximumConnectionDistanceCm = Shared.MaximumReachCm;
        }
        else
        {
            FLBPressShopLogisticsSpine& Logistics =
                OutLogisticsSpines.AddDefaulted_GetRef();
            Logistics.SpineId = Shared.SpineId;
            Logistics.Start = Start;
            Logistics.End = End;
            Logistics.MaximumAccessDistanceCm = Shared.MaximumReachCm;
        }
    }
}

bool ULBOneFactoryLayoutLibrary::ValidatePressBuildAuthorityContract(
    const FLBOneFactoryLayoutDefinition& Layout,
    const ALBPressShopBuildAuthority* Authority, FString& OutReason)
{
    OutReason.Reset();
    if (!ValidateMoorcrossWorksLayout(Layout, OutReason))
    {
        return false;
    }
    if (!Authority)
    {
        OutReason = TEXT("ONEFACTORY PRESS BUILD AUTHORITY IS MISSING");
        return false;
    }
    if (Authority->GetClass() != ALBPressShopBuildAuthority::StaticClass())
    {
        OutReason = TEXT("ONEFACTORY REQUIRES THE EXACT NATIVE PRESS BUILD AUTHORITY CLASS");
        return false;
    }
    if (!Authority->GetActorTransform().Equals(FTransform::Identity,
        LBOneFactoryTypesPrivate::TransformTolerance))
    {
        OutReason = TEXT("ONEFACTORY PRESS BUILD AUTHORITY MUST REMAIN AT WORLD IDENTITY");
        return false;
    }
    if (!Authority->StorageBays.IsEmpty())
    {
        OutReason = TEXT("ONEFACTORY SHELL MUST NOT PRE-SEED STORAGE BAYS");
        return false;
    }

    TArray<FLBPressShopBuildBay> ExpectedBuildBays;
    TArray<FLBPressShopProtectedArea> ExpectedProtectedAreas;
    TArray<FLBPressShopUtilitySpine> ExpectedUtilitySpines;
    TArray<FLBPressShopLogisticsSpine> ExpectedLogisticsSpines;
    BuildExpectedPressAuthorityContract(Layout, ExpectedBuildBays,
        ExpectedProtectedAreas, ExpectedUtilitySpines, ExpectedLogisticsSpines);
    if (Authority->BuildBays.Num() != ExpectedBuildBays.Num()
        || Authority->ProtectedAreas.Num() != ExpectedProtectedAreas.Num()
        || Authority->UtilitySpines.Num() != ExpectedUtilitySpines.Num()
        || Authority->LogisticsSpines.Num() != ExpectedLogisticsSpines.Num())
    {
        OutReason = TEXT("ONEFACTORY PRESS BUILD AUTHORITY CARDINALITY DRIFTED");
        return false;
    }
    for (int32 Index = 0; Index < ExpectedBuildBays.Num(); ++Index)
    {
        const FLBPressShopBuildBay& Actual = Authority->BuildBays[Index];
        const FLBPressShopBuildBay& Expected = ExpectedBuildBays[Index];
        if (Actual.BayId != Expected.BayId
            || !Actual.Centre.Equals(Expected.Centre,
                LBOneFactoryTypesPrivate::LayoutToleranceCm)
            || !Actual.HalfExtent.Equals(Expected.HalfExtent,
                LBOneFactoryTypesPrivate::LayoutToleranceCm))
        {
            OutReason = FString::Printf(TEXT("ONEFACTORY BUILD BAY %d DRIFTED"), Index);
            return false;
        }
    }
    for (int32 Index = 0; Index < ExpectedProtectedAreas.Num(); ++Index)
    {
        const FLBPressShopProtectedArea& Actual = Authority->ProtectedAreas[Index];
        const FLBPressShopProtectedArea& Expected = ExpectedProtectedAreas[Index];
        if (Actual.AreaId != Expected.AreaId
            || !Actual.Centre.Equals(Expected.Centre,
                LBOneFactoryTypesPrivate::LayoutToleranceCm)
            || !Actual.HalfExtent.Equals(Expected.HalfExtent,
                LBOneFactoryTypesPrivate::LayoutToleranceCm))
        {
            OutReason = FString::Printf(TEXT("ONEFACTORY PROTECTED AREA %d DRIFTED"), Index);
            return false;
        }
    }
    for (int32 Index = 0; Index < ExpectedUtilitySpines.Num(); ++Index)
    {
        const FLBPressShopUtilitySpine& Actual = Authority->UtilitySpines[Index];
        const FLBPressShopUtilitySpine& Expected = ExpectedUtilitySpines[Index];
        if (Actual.SpineId != Expected.SpineId
            || !Actual.Start.Equals(Expected.Start,
                LBOneFactoryTypesPrivate::LayoutToleranceCm)
            || !Actual.End.Equals(Expected.End,
                LBOneFactoryTypesPrivate::LayoutToleranceCm)
            || !FMath::IsNearlyEqual(Actual.MaximumConnectionDistanceCm,
                Expected.MaximumConnectionDistanceCm,
                LBOneFactoryTypesPrivate::LayoutToleranceCm))
        {
            OutReason = FString::Printf(TEXT("ONEFACTORY UTILITY SPINE %d DRIFTED"), Index);
            return false;
        }
    }
    for (int32 Index = 0; Index < ExpectedLogisticsSpines.Num(); ++Index)
    {
        const FLBPressShopLogisticsSpine& Actual = Authority->LogisticsSpines[Index];
        const FLBPressShopLogisticsSpine& Expected = ExpectedLogisticsSpines[Index];
        if (Actual.SpineId != Expected.SpineId
            || !Actual.Start.Equals(Expected.Start,
                LBOneFactoryTypesPrivate::LayoutToleranceCm)
            || !Actual.End.Equals(Expected.End,
                LBOneFactoryTypesPrivate::LayoutToleranceCm)
            || !FMath::IsNearlyEqual(Actual.MaximumAccessDistanceCm,
                Expected.MaximumAccessDistanceCm,
                LBOneFactoryTypesPrivate::LayoutToleranceCm))
        {
            OutReason = FString::Printf(TEXT("ONEFACTORY LOGISTICS SPINE %d DRIFTED"), Index);
            return false;
        }
    }
    OutReason = TEXT("ONEFACTORY MAP-AUTHORED PRESS BUILD AUTHORITY VALID");
    return true;
}
