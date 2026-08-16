#include "LBOneFactoryPressStarterLayout.h"

#include "LBVehiclePanelCatalog.h"

namespace LBOneFactoryPressStarterPrivate
{
    constexpr float TransformTolerance = 0.001f;
    constexpr float LayoutToleranceCm = 0.1f;
    constexpr float CanonicalMaximumRouteLengthCm = 8000.0f;

    struct FRoleContract
    {
        ELBOneFactoryPressStarterRole Role;
        FName StationId;
        bool bRecipeBound;
        bool bPlayerReconfigurable;
    };

    FName StableName(const TCHAR* Text)
    {
        return FName(Text);
    }

    const TArray<FRoleContract>& RoleContracts()
    {
        static const TArray<FRoleContract> Contracts =
        {
            {ELBOneFactoryPressStarterRole::InboundCoilReceiving,
                LBOneFactoryPressStarterIds::InboundReceiving(), false, false},
            {ELBOneFactoryPressStarterRole::WrappedCoilStorage,
                LBOneFactoryPressStarterIds::WrappedCoilStorage(), false, false},
            {ELBOneFactoryPressStarterRole::BlankPreparation,
                LBOneFactoryPressStarterIds::BlankPreparation(), true, true},
            {ELBOneFactoryPressStarterRole::PreparedBlankBuffer,
                LBOneFactoryPressStarterIds::PreparedBlankBuffer(), true, false},
            {ELBOneFactoryPressStarterRole::ConfigurablePressTrain,
                LBOneFactoryPressStarterIds::PressTrain(), true, true},
            {ELBOneFactoryPressStarterRole::PanelInspection,
                LBOneFactoryPressStarterIds::PanelInspection(), true, true},
            {ELBOneFactoryPressStarterRole::PanelStillageDispatch,
                LBOneFactoryPressStarterIds::PanelDispatch(), true, false}
        };
        return Contracts;
    }

    const FRoleContract* FindRoleContract(
        const ELBOneFactoryPressStarterRole Role)
    {
        return RoleContracts().FindByPredicate([Role](const FRoleContract& Contract)
        {
            return Contract.Role == Role;
        });
    }

    FBox StationEnvelope(const FLBOneFactoryPressStarterStationState& Station)
    {
        const FVector Half(Station.FootprintSizeCm.X * 0.5f,
            Station.FootprintSizeCm.Y * 0.5f, 0.0f);
        return FBox(FVector(-Half.X, -Half.Y, 0.0f),
            FVector(Half.X, Half.Y, Station.FootprintSizeCm.Z))
            .TransformBy(Station.WorldTransform);
    }

    bool IsTransformUsable(const FTransform& Transform)
    {
        const FRotator Rotation = Transform.Rotator();
        return Transform.IsValid() && !Transform.ContainsNaN()
            && Transform.GetScale3D().Equals(FVector::OneVector,
                TransformTolerance)
            && FMath::IsNearlyZero(Transform.GetLocation().Z,
                LayoutToleranceCm)
            && FMath::IsNearlyZero(Rotation.Roll, TransformTolerance)
            && FMath::IsNearlyZero(Rotation.Pitch, TransformTolerance);
    }

    const FLBOneFactoryPressStarterStationState* FindStationByRole(
        const FLBOneFactoryPressStarterLayoutState& State,
        const ELBOneFactoryPressStarterRole Role)
    {
        return State.Stations.FindByPredicate([Role](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.Role == Role;
        });
    }

    FLBOneFactoryPressStarterStationState* FindStationByRole(
        FLBOneFactoryPressStarterLayoutState& State,
        const ELBOneFactoryPressStarterRole Role)
    {
        return State.Stations.FindByPredicate([Role](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.Role == Role;
        });
    }

    FBox GetPressBayBounds()
    {
        const FLBOneFactoryLayoutDefinition Layout =
            ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
        const FLBOneFactoryDepartmentBay* PressBay =
            Layout.DepartmentBays.FindByPredicate([](
                const FLBOneFactoryDepartmentBay& Bay)
            {
                return Bay.BayId == LBOneFactoryIds::PressBay()
                    && Bay.Department == ELBOneFactoryDepartment::Press;
            });
        return PressBay ? PressBay->GetWorldBounds() : FBox(ForceInit);
    }

    struct FConnectionContract
    {
        const TCHAR* ConnectionId;
        ELBOneFactoryPressStarterRole SourceRole;
        ELBOneFactoryPressStarterRole TargetRole;
        ELBFactoryMaterialClass MaterialClass;
    };

    const TArray<FConnectionContract>& ConnectionContracts()
    {
        static const TArray<FConnectionContract> Contracts =
        {
            {TEXT("OF_PRESS_ROUTE_01_RECEIVING_TO_COIL_STORE"),
                ELBOneFactoryPressStarterRole::InboundCoilReceiving,
                ELBOneFactoryPressStarterRole::WrappedCoilStorage,
                ELBFactoryMaterialClass::Coil},
            {TEXT("OF_PRESS_ROUTE_02_COIL_STORE_TO_BLANK_PREP"),
                ELBOneFactoryPressStarterRole::WrappedCoilStorage,
                ELBOneFactoryPressStarterRole::BlankPreparation,
                ELBFactoryMaterialClass::Coil},
            {TEXT("OF_PRESS_ROUTE_03_BLANK_PREP_TO_BUFFER"),
                ELBOneFactoryPressStarterRole::BlankPreparation,
                ELBOneFactoryPressStarterRole::PreparedBlankBuffer,
                ELBFactoryMaterialClass::Blank},
            {TEXT("OF_PRESS_ROUTE_04_BUFFER_TO_PRESS"),
                ELBOneFactoryPressStarterRole::PreparedBlankBuffer,
                ELBOneFactoryPressStarterRole::ConfigurablePressTrain,
                ELBFactoryMaterialClass::Blank},
            {TEXT("OF_PRESS_ROUTE_05_PRESS_TO_INSPECTION"),
                ELBOneFactoryPressStarterRole::ConfigurablePressTrain,
                ELBOneFactoryPressStarterRole::PanelInspection,
                ELBFactoryMaterialClass::FormedPanel},
            {TEXT("OF_PRESS_ROUTE_06_INSPECTION_TO_DISPATCH"),
                ELBOneFactoryPressStarterRole::PanelInspection,
                ELBOneFactoryPressStarterRole::PanelStillageDispatch,
                ELBFactoryMaterialClass::InspectedPanel}
        };
        return Contracts;
    }

    bool EqualsExactStrings(const TArray<FString>& Left,
        const TArray<FString>& Right)
    {
        if (Left.Num() != Right.Num()) return false;
        for (int32 Index = 0; Index < Left.Num(); ++Index)
        {
            if (!Left[Index].Equals(Right[Index], ESearchCase::CaseSensitive))
                return false;
        }
        return true;
    }
}

FName LBOneFactoryPressStarterIds::Layout()
{
    return LBOneFactoryPressStarterPrivate::StableName(
        TEXT("MOORCROSS_PRESS_STARTER_NATIVE_V001"));
}

FName LBOneFactoryPressStarterIds::NativeOnlyProfile()
{
    return LBOneFactoryPressStarterPrivate::StableName(
        TEXT("MOORCROSS_PRESS_NATIVE_ONLY_V001"));
}

FName LBOneFactoryPressStarterIds::InboundReceiving()
{
    return LBOneFactoryPressStarterPrivate::StableName(
        TEXT("OF_PRESS_INBOUND_RECEIVING_001"));
}

FName LBOneFactoryPressStarterIds::WrappedCoilStorage()
{
    return LBOneFactoryPressStarterPrivate::StableName(
        TEXT("OF_PRESS_WRAPPED_COIL_STORE_001"));
}

FName LBOneFactoryPressStarterIds::BlankPreparation()
{
    return LBOneFactoryPressStarterPrivate::StableName(
        TEXT("OF_PRESS_BLANK_PREP_001"));
}

FName LBOneFactoryPressStarterIds::PreparedBlankBuffer()
{
    return LBOneFactoryPressStarterPrivate::StableName(
        TEXT("OF_PRESS_PREPARED_BLANK_BUFFER_001"));
}

FName LBOneFactoryPressStarterIds::PressTrain()
{
    return LBOneFactoryPressStarterPrivate::StableName(
        TEXT("OF_PRESS_TRAIN_001"));
}

FName LBOneFactoryPressStarterIds::PanelInspection()
{
    return LBOneFactoryPressStarterPrivate::StableName(
        TEXT("OF_PRESS_PANEL_INSPECTION_001"));
}

FName LBOneFactoryPressStarterIds::PanelDispatch()
{
    return LBOneFactoryPressStarterPrivate::StableName(
        TEXT("OF_PRESS_PANEL_DISPATCH_001"));
}

FName ULBOneFactoryPressStarterLayoutLibrary::MakeDieId(
    const FName PanelTypeId)
{
    return PanelTypeId.IsNone() ? NAME_None
        : FName(*FString::Printf(TEXT("DIE_%s_V1"),
            *PanelTypeId.ToString()));
}

FLBOneFactoryPressStarterLayoutState
ULBOneFactoryPressStarterLayoutLibrary::MakeCanonicalStarterLayout()
{
    FLBOneFactoryPressStarterLayoutState State;
    State.LayoutId = LBOneFactoryPressStarterIds::Layout();
    State.Revision = 0;
    State.bCommissioned = false;

    const FName VehicleModelId =
        LBCairnwell2040PanelCatalog::GetVehicleModelId();
    const FName PanelTypeId(TEXT("HOOD_PANEL"));
    const FName DieId = MakeDieId(PanelTypeId);

    auto AddStation = [&State, VehicleModelId, PanelTypeId, DieId](
        const ELBOneFactoryPressStarterRole Role, const FVector& Location,
        const FVector& FootprintSizeCm)
    {
        const LBOneFactoryPressStarterPrivate::FRoleContract* Contract =
            LBOneFactoryPressStarterPrivate::FindRoleContract(Role);
        check(Contract);
        FLBOneFactoryPressStarterStationState& Station =
            State.Stations.AddDefaulted_GetRef();
        Station.StationId = Contract->StationId;
        Station.Role = Role;
        Station.WorldTransform = FTransform(FRotator::ZeroRotator, Location,
            FVector::OneVector);
        Station.FootprintSizeCm = FootprintSizeCm;
        Station.bPlayerReconfigurable = Contract->bPlayerReconfigurable;
        if (Contract->bRecipeBound)
        {
            Station.VehicleModelId = VehicleModelId;
            Station.PanelTypeId = PanelTypeId;
            Station.DieId = DieId;
        }
    };

    // Every footprint is inside OF_BAY_PRESS_01 and clear of the central
    // logistics spine. The arrangement remains readable from the management view.
    AddStation(ELBOneFactoryPressStarterRole::InboundCoilReceiving,
        FVector(-28000.0f, 3000.0f, 0.0f), FVector(2600.0f, 2600.0f, 500.0f));
    AddStation(ELBOneFactoryPressStarterRole::WrappedCoilStorage,
        FVector(-23800.0f, 3000.0f, 0.0f), FVector(3600.0f, 2400.0f, 500.0f));
    AddStation(ELBOneFactoryPressStarterRole::BlankPreparation,
        FVector(-19000.0f, 3000.0f, 0.0f), FVector(5000.0f, 2500.0f, 900.0f));
    AddStation(ELBOneFactoryPressStarterRole::PreparedBlankBuffer,
        FVector(-14500.0f, 3000.0f, 0.0f), FVector(2500.0f, 2000.0f, 350.0f));
    AddStation(ELBOneFactoryPressStarterRole::ConfigurablePressTrain,
        FVector(-9000.0f, 8000.0f, 0.0f), FVector(2500.0f, 8000.0f, 950.0f));
    AddStation(ELBOneFactoryPressStarterRole::PanelInspection,
        FVector(-5500.0f, 12000.0f, 0.0f), FVector(2500.0f, 2200.0f, 700.0f));
    AddStation(ELBOneFactoryPressStarterRole::PanelStillageDispatch,
        FVector(-2000.0f, 12000.0f, 0.0f), FVector(2600.0f, 2200.0f, 500.0f));

    for (const LBOneFactoryPressStarterPrivate::FConnectionContract& Contract :
        LBOneFactoryPressStarterPrivate::ConnectionContracts())
    {
        const LBOneFactoryPressStarterPrivate::FRoleContract* Source =
            LBOneFactoryPressStarterPrivate::FindRoleContract(Contract.SourceRole);
        const LBOneFactoryPressStarterPrivate::FRoleContract* Target =
            LBOneFactoryPressStarterPrivate::FindRoleContract(Contract.TargetRole);
        check(Source && Target);
        FLBOneFactoryPressStarterConnectionState& Connection =
            State.Connections.AddDefaulted_GetRef();
        Connection.ConnectionId = FName(Contract.ConnectionId);
        Connection.SourceStationId = Source->StationId;
        Connection.TargetStationId = Target->StationId;
        Connection.MaterialClass = Contract.MaterialClass;
        Connection.MaximumRouteLengthCm =
            LBOneFactoryPressStarterPrivate::CanonicalMaximumRouteLengthCm;
    }
    return State;
}

bool ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
    const FLBOneFactoryPressStarterLayoutState& State, FString& OutReason)
{
    using namespace LBOneFactoryPressStarterPrivate;
    OutReason.Reset();
    if (State.Version != 1 || State.LayoutId !=
            LBOneFactoryPressStarterIds::Layout() || State.Revision < 0)
    {
        OutReason = TEXT("PRESS STARTER ROOT VERSION, ID OR REVISION IS INVALID");
        return false;
    }
    if (State.Stations.Num() != RoleContracts().Num()
        || State.Connections.Num() != ConnectionContracts().Num())
    {
        OutReason = TEXT("PRESS STARTER REQUIRES EXACTLY SEVEN STATIONS AND SIX ROUTES");
        return false;
    }

    const FBox PressBounds = GetPressBayBounds();
    if (!PressBounds.IsValid)
    {
        OutReason = TEXT("ONEFACTORY PRESS BAY CONTRACT IS OFFLINE");
        return false;
    }

    TSet<FName> StationIds;
    TSet<uint8> Roles;
    TSet<FName> WIPIds;
    TArray<FBox> StationEnvelopes;
    FName ProgrammeVehicle = NAME_None;
    FName ProgrammePanel = NAME_None;
    FName ProgrammeDie = NAME_None;
    for (const FLBOneFactoryPressStarterStationState& Station : State.Stations)
    {
        const FRoleContract* Contract = FindRoleContract(Station.Role);
        if (Station.Version != 1 || !Contract
            || Station.StationId != Contract->StationId
            || StationIds.Contains(Station.StationId)
            || Roles.Contains(static_cast<uint8>(Station.Role))
            || !IsTransformUsable(Station.WorldTransform)
            || !FMath::IsFinite(Station.FootprintSizeCm.X)
            || !FMath::IsFinite(Station.FootprintSizeCm.Y)
            || !FMath::IsFinite(Station.FootprintSizeCm.Z)
            || Station.FootprintSizeCm.GetMin() <= 0.0f
            || Station.bPlayerReconfigurable != Contract->bPlayerReconfigurable)
        {
            OutReason = TEXT("PRESS STARTER STATION IDENTITY, TRANSFORM OR FOOTPRINT IS INVALID");
            return false;
        }

        const FBox Envelope = StationEnvelope(Station);
        if (!PressBounds.ExpandBy(LayoutToleranceCm).IsInsideOrOn(Envelope.Min)
            || !PressBounds.ExpandBy(LayoutToleranceCm).IsInsideOrOn(Envelope.Max))
        {
            OutReason = FString::Printf(
                TEXT("PRESS STARTER STATION %s IS OUTSIDE OF_BAY_PRESS_01"),
                *Station.StationId.ToString());
            return false;
        }
        for (const FBox& Existing : StationEnvelopes)
        {
            if (Envelope.Intersect(Existing))
            {
                OutReason = TEXT("PRESS STARTER STATION FOOTPRINTS OVERLAP");
                return false;
            }
        }
        StationEnvelopes.Add(Envelope);

        for (const FName UnitId : Station.ActiveOrReservedUnitIds)
        {
            if (UnitId.IsNone() || WIPIds.Contains(UnitId))
            {
                OutReason = TEXT("PRESS STARTER ACTIVE OR RESERVED WIP IDENTITIES ARE INVALID");
                return false;
            }
            WIPIds.Add(UnitId);
        }

        if (!Contract->bRecipeBound)
        {
            if (!Station.VehicleModelId.IsNone() || !Station.PanelTypeId.IsNone()
                || !Station.DieId.IsNone())
            {
                OutReason = TEXT("FIXED COIL RESPONSIBILITIES MUST NOT CLAIM A PANEL RECIPE");
                return false;
            }
        }
        else
        {
            if (!LBCairnwell2040PanelCatalog::IsApprovedStampedRecipe(
                    Station.VehicleModelId, Station.PanelTypeId)
                || Station.DieId != MakeDieId(Station.PanelTypeId))
            {
                OutReason = TEXT("PRESS STARTER PANEL PROGRAMME IS NOT IN THE APPROVED CAR CATALOGUE");
                return false;
            }
            if (ProgrammePanel.IsNone())
            {
                ProgrammeVehicle = Station.VehicleModelId;
                ProgrammePanel = Station.PanelTypeId;
                ProgrammeDie = Station.DieId;
            }
            else if (Station.VehicleModelId != ProgrammeVehicle
                || Station.PanelTypeId != ProgrammePanel
                || Station.DieId != ProgrammeDie)
            {
                OutReason = TEXT("BLANK, PRESS, INSPECTION AND DISPATCH RESPONSIBILITIES DO NOT MATCH");
                return false;
            }
        }
        StationIds.Add(Station.StationId);
        Roles.Add(static_cast<uint8>(Station.Role));
    }

    TSet<FName> ConnectionIds;
    for (const FConnectionContract& Contract : ConnectionContracts())
    {
        const FRoleContract* SourceRole = FindRoleContract(Contract.SourceRole);
        const FRoleContract* TargetRole = FindRoleContract(Contract.TargetRole);
        const FLBOneFactoryPressStarterConnectionState* Connection =
            State.Connections.FindByPredicate([&Contract](
                const FLBOneFactoryPressStarterConnectionState& Candidate)
            {
                return Candidate.ConnectionId == FName(Contract.ConnectionId);
            });
        if (!SourceRole || !TargetRole || !Connection || Connection->Version != 1
            || ConnectionIds.Contains(Connection->ConnectionId)
            || Connection->SourceStationId != SourceRole->StationId
            || Connection->TargetStationId != TargetRole->StationId
            || Connection->MaterialClass != Contract.MaterialClass
            || !FMath::IsFinite(Connection->MaximumRouteLengthCm)
            || !FMath::IsNearlyEqual(Connection->MaximumRouteLengthCm,
                CanonicalMaximumRouteLengthCm, LayoutToleranceCm))
        {
            OutReason = TEXT("PRESS STARTER MATERIAL ROUTE IDENTITY OR RESPONSIBILITY IS INVALID");
            return false;
        }
        const FLBOneFactoryPressStarterStationState* Source =
            State.Stations.FindByPredicate([Connection](
                const FLBOneFactoryPressStarterStationState& Station)
            { return Station.StationId == Connection->SourceStationId; });
        const FLBOneFactoryPressStarterStationState* Target =
            State.Stations.FindByPredicate([Connection](
                const FLBOneFactoryPressStarterStationState& Station)
            { return Station.StationId == Connection->TargetStationId; });
        if (!Source || !Target || FVector::Dist2D(
                Source->WorldTransform.GetLocation(),
                Target->WorldTransform.GetLocation())
                > Connection->MaximumRouteLengthCm + LayoutToleranceCm)
        {
            OutReason = TEXT("PRESS STARTER MATERIAL ROUTE EXCEEDS ITS AUTHORED REACH");
            return false;
        }
        ConnectionIds.Add(Connection->ConnectionId);
    }
    if (ConnectionIds.Num() != State.Connections.Num())
    {
        OutReason = TEXT("PRESS STARTER CONTAINS AN UNAUTHORISED MATERIAL ROUTE");
        return false;
    }

    OutReason = FString::Printf(
        TEXT("PRESS STARTER VALID: 7 STATIONS, 6 ROUTES, PROGRAMME %s"),
        *ProgrammePanel.ToString());
    return true;
}

FLBOneFactoryPressNativeOnlyProfile
ULBOneFactoryPressStarterLayoutLibrary::MakeNativeOnlyProfile()
{
    FLBOneFactoryPressNativeOnlyProfile Profile;
    Profile.ProfileId = LBOneFactoryPressStarterIds::NativeOnlyProfile();
    Profile.Policy = ELBOneFactoryProvenancePolicy::NativeOnly;
    Profile.AllowedClassPaths =
    {
        TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority"),
        TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterPresentationActor"),
        TEXT("/Script/LineBossCarFactory.LBFactoryAGVInfrastructure")
    };
    Profile.AllowedAssetRoots =
    {
        TEXT("/Script/LineBossCarFactory."),
        TEXT("/Engine/BasicShapes/"),
        TEXT("/Engine/EngineMaterials/"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/")
    };
    Profile.ForbiddenSourceTokens =
    {
        TEXT("Meshy"),
        TEXT("RuntimeGLB"),
        TEXT("ExternalGenerated"),
        TEXT("OriginalHighPoly"),
        TEXT("/Downloads/"),
        TEXT("/Developer/Validation/"),
        TEXT("/Candidates/"),
        TEXT("/Runtime/PressShop/"),
        TEXT("/Stations/Press/")
    };
    return Profile;
}

bool ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeOnlyProfile(
    const FLBOneFactoryPressNativeOnlyProfile& Profile, FString& OutReason)
{
    using namespace LBOneFactoryPressStarterPrivate;
    const FLBOneFactoryPressNativeOnlyProfile Expected = MakeNativeOnlyProfile();
    if (Profile.Version != Expected.Version
        || Profile.ProfileId != Expected.ProfileId
        || Profile.Policy != Expected.Policy
        || !EqualsExactStrings(Profile.AllowedClassPaths,
            Expected.AllowedClassPaths)
        || !EqualsExactStrings(Profile.AllowedAssetRoots,
            Expected.AllowedAssetRoots)
        || !EqualsExactStrings(Profile.ForbiddenSourceTokens,
            Expected.ForbiddenSourceTokens))
    {
        OutReason = TEXT("ONEFACTORY PRESS NATIVE-ONLY PROFILE DRIFTED FROM ITS EXACT ALLOWLIST");
        return false;
    }
    OutReason = TEXT("ONEFACTORY PRESS NATIVE-ONLY PROFILE IS EXACT");
    return true;
}

bool ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeReference(
    const FLBOneFactoryPressNativeOnlyProfile& Profile,
    const FString& ClassPath, const FString& AssetReference,
    const ELBOneFactoryAssetProvenance Provenance, FString& OutReason)
{
    if (!ValidateNativeOnlyProfile(Profile, OutReason)) return false;
    const bool bClassAllowed = Profile.AllowedClassPaths.ContainsByPredicate(
        [&ClassPath](const FString& Allowed)
        {
            return Allowed.Equals(ClassPath, ESearchCase::IgnoreCase);
        });
    if (!bClassAllowed)
    {
        OutReason = FString::Printf(TEXT("CLASS IS NOT IN THE PRESS NATIVE-ONLY ALLOWLIST: %s"),
            *ClassPath);
        return false;
    }
    for (const FString& Token : Profile.ForbiddenSourceTokens)
    {
        if (ClassPath.Contains(Token, ESearchCase::IgnoreCase)
            || AssetReference.Contains(Token, ESearchCase::IgnoreCase))
        {
            OutReason = FString::Printf(TEXT("FORBIDDEN PRESS PRESENTATION SOURCE TOKEN: %s"),
                *Token);
            return false;
        }
    }
    const bool bAssetRootAllowed = Profile.AllowedAssetRoots.ContainsByPredicate(
        [&AssetReference](const FString& Root)
        {
            return AssetReference.StartsWith(Root, ESearchCase::IgnoreCase);
        });
    if (!bAssetRootAllowed)
    {
        OutReason = FString::Printf(TEXT("ASSET IS OUTSIDE THE PRESS NATIVE-ONLY ROOTS: %s"),
            *AssetReference);
        return false;
    }
    if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(Profile.Policy,
        Provenance, AssetReference, OutReason))
    {
        return false;
    }
    OutReason = TEXT("CLASS, ASSET ROOT AND DECLARED PROVENANCE ARE NATIVE-ONLY");
    return true;
}

FName ALBOneFactoryPressStarterLayoutAuthority::GetAuthorityTag()
{
    return FName(TEXT("LB.OneFactory.Press.StarterLayoutAuthority.v001"));
}

FName ALBOneFactoryPressStarterLayoutAuthority::GetNativeOnlyTag()
{
    return FName(TEXT("LB.Provenance.NativeOnly"));
}

ALBOneFactoryPressStarterLayoutAuthority::
ALBOneFactoryPressStarterLayoutAuthority()
{
    PrimaryActorTick.bCanEverTick = false;
    SetActorEnableCollision(false);
    SetReplicates(false);
    CurrentState =
        ULBOneFactoryPressStarterLayoutLibrary::MakeCanonicalStarterLayout();
    Tags.AddUnique(GetAuthorityTag());
    Tags.AddUnique(GetNativeOnlyTag());
}

bool ALBOneFactoryPressStarterLayoutAuthority::StateHasActiveOrReservedWIP(
    const FLBOneFactoryPressStarterLayoutState& State)
{
    return State.Stations.ContainsByPredicate([](
        const FLBOneFactoryPressStarterStationState& Station)
    {
        return !Station.ActiveOrReservedUnitIds.IsEmpty();
    });
}

bool ALBOneFactoryPressStarterLayoutAuthority::RestoreLayout(
    const FLBOneFactoryPressStarterLayoutState& State, FString& OutReason)
{
    FString ValidationReason;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
        State, ValidationReason))
    {
        OutReason = FString::Printf(TEXT("PRESS STARTER RESTORE REJECTED WITHOUT MUTATION: %s"),
            *ValidationReason);
        return false;
    }
    CurrentState = State;
    OutReason = FString::Printf(TEXT("RESTORED PRESS STARTER REVISION %d ATOMICALLY"),
        CurrentState.Revision);
    return true;
}

bool ALBOneFactoryPressStarterLayoutAuthority::SetStationPanelProgramme(
    const FName StationId, const FName PanelTypeId, FString& OutReason)
{
    FString ValidationReason;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            CurrentState, ValidationReason))
    {
        OutReason = FString::Printf(TEXT("LIVE PRESS STARTER IS INVALID: %s"),
            *ValidationReason);
        return false;
    }
    const FLBOneFactoryPressStarterStationState* Requested =
        CurrentState.Stations.FindByPredicate([StationId](
            const FLBOneFactoryPressStarterStationState& Station)
        { return Station.StationId == StationId; });
    if (!Requested || !Requested->bPlayerReconfigurable)
    {
        OutReason = TEXT("SELECT BLANK PREP, PRESS TRAIN OR PANEL INSPECTION TO CHANGE THE JOB");
        return false;
    }
    if (StateHasActiveOrReservedWIP(CurrentState))
    {
        OutReason = TEXT("FINISH OR RELEASE ALL ACTIVE AND RESERVED PRESS WIP BEFORE CHANGING THE JOB");
        return false;
    }
    const FName VehicleModelId =
        LBCairnwell2040PanelCatalog::GetVehicleModelId();
    if (!LBCairnwell2040PanelCatalog::IsApprovedStampedRecipe(
            VehicleModelId, PanelTypeId))
    {
        OutReason = TEXT("THE SELECTED PANEL JOB IS NOT IN THE CURRENT CAR PROGRAMME");
        return false;
    }
    if (Requested->PanelTypeId == PanelTypeId)
    {
        OutReason = FString::Printf(TEXT("PRESS STARTER ALREADY MAKES %s"),
            *PanelTypeId.ToString());
        return true;
    }

    FLBOneFactoryPressStarterLayoutState Candidate = CurrentState;
    const FName DieId =
        ULBOneFactoryPressStarterLayoutLibrary::MakeDieId(PanelTypeId);
    for (FLBOneFactoryPressStarterStationState& Station : Candidate.Stations)
    {
        const LBOneFactoryPressStarterPrivate::FRoleContract* Contract =
            LBOneFactoryPressStarterPrivate::FindRoleContract(Station.Role);
        if (!Contract || !Contract->bRecipeBound) continue;
        Station.VehicleModelId = VehicleModelId;
        Station.PanelTypeId = PanelTypeId;
        Station.DieId = DieId;
    }
    ++Candidate.Revision;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, ValidationReason))
    {
        OutReason = FString::Printf(TEXT("PANEL JOB CHANGE ROLLED BACK: %s"),
            *ValidationReason);
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = FString::Printf(
        TEXT("PRESS JOB SET TO %s; BLANK PREP, DIE, INSPECTION AND DISPATCH UPDATED TOGETHER"),
        *PanelTypeId.ToString());
    return true;
}

bool ALBOneFactoryPressStarterLayoutAuthority::MoveStation(
    const FName StationId, const FTransform& WorldTransform, FString& OutReason)
{
    FString ValidationReason;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            CurrentState, ValidationReason))
    {
        OutReason = FString::Printf(TEXT("LIVE PRESS STARTER IS INVALID: %s"),
            *ValidationReason);
        return false;
    }
    if (StateHasActiveOrReservedWIP(CurrentState))
    {
        OutReason = TEXT("FINISH OR RELEASE ALL ACTIVE AND RESERVED PRESS WIP BEFORE MOVING A STATION");
        return false;
    }
    FLBOneFactoryPressStarterLayoutState Candidate = CurrentState;
    FLBOneFactoryPressStarterStationState* Station =
        Candidate.Stations.FindByPredicate([StationId](
            const FLBOneFactoryPressStarterStationState& Item)
        { return Item.StationId == StationId; });
    if (!Station)
    {
        OutReason = TEXT("PRESS STARTER STATION ID DOES NOT EXIST");
        return false;
    }
    if (Station->WorldTransform.Equals(WorldTransform,
            LBOneFactoryPressStarterPrivate::TransformTolerance))
    {
        OutReason = TEXT("PRESS STARTER STATION IS ALREADY AT THAT TRANSFORM");
        return true;
    }
    Station->WorldTransform = WorldTransform;
    ++Candidate.Revision;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, ValidationReason))
    {
        OutReason = FString::Printf(TEXT("STATION MOVE ROLLED BACK: %s"),
            *ValidationReason);
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = FString::Printf(TEXT("MOVED %s; SIX-ROUTE STARTER GRAPH PRESERVED"),
        *StationId.ToString());
    return true;
}

bool ALBOneFactoryPressStarterLayoutAuthority::Commission(FString& OutReason)
{
    FString ValidationReason;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            CurrentState, ValidationReason))
    {
        OutReason = FString::Printf(TEXT("PRESS STARTER CANNOT COMMISSION: %s"),
            *ValidationReason);
        return false;
    }
    if (CurrentState.bCommissioned)
    {
        OutReason = TEXT("PRESS STARTER IS ALREADY COMMISSIONED");
        return true;
    }
    FLBOneFactoryPressStarterLayoutState Candidate = CurrentState;
    Candidate.bCommissioned = true;
    ++Candidate.Revision;
    CurrentState = MoveTemp(Candidate);
    OutReason = TEXT("PRESS STARTER LAYOUT COMMISSIONED; PRODUCTION STILL REQUIRES NATIVE STATION MATERIALISATION");
    return true;
}
