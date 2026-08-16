#include "LBOneFactoryPaintStarterLayout.h"

#include "LBVehiclePanelCatalog.h"

namespace LBOneFactoryPaintStarterPrivate
{
    constexpr float TransformTolerance = 0.001f;
    constexpr float LayoutToleranceCm = 0.1f;
    constexpr float MaximumRouteLengthCm = 2800.0f;

    const TCHAR* AuthorityClassPath =
        TEXT("/Script/LineBossCarFactory.LBOneFactoryPaintStarterLayoutAuthority");
    const TCHAR* PresentationClassPath =
        TEXT("/Script/LineBossCarFactory.LBOneFactoryPaintStarterPresentationActor");

    const TCHAR* CuringOvenPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Process/"
        "SM_LB_Paint_CuringOvenTunnel_v001.SM_LB_Paint_CuringOvenTunnel_v001");
    const TCHAR* PretreatmentPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Process/"
        "SM_LB_Paint_PretreatmentWashTunnel_v001.SM_LB_Paint_PretreatmentWashTunnel_v001");
    const TCHAR* FlashOffPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Process/"
        "SM_LB_Paint_FlashOffTunnel_v001.SM_LB_Paint_FlashOffTunnel_v001");
    const TCHAR* QualityLightPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Quality/"
        "SM_LB_Paint_QualityLightTunnel_v001.SM_LB_Paint_QualityLightTunnel_v001");
    const TCHAR* BodySkidPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Logistics/"
        "SM_LB_Paint_BodySkidCarrier_v001.SM_LB_Paint_BodySkidCarrier_v001");
    const TCHAR* ServiceSetPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Services/"
        "SM_LB_Paint_ServiceSet_v001.SM_LB_Paint_ServiceSet_v001");
    const TCHAR* AirExtractionPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001/Services/"
        "SM_LB_Paint_AirExtractionModule_v001.SM_LB_Paint_AirExtractionModule_v001");
    const TCHAR* SprayBoothPath = TEXT(
        "/Game/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v002/"
        "SM_LB_PaintSprayBooth_Runtime_v002.SM_LB_PaintSprayBooth_Runtime_v002");
    const TCHAR* CubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
    const TCHAR* BasicMaterialPath =
        TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");

    struct FRoleContract
    {
        ELBOneFactoryPaintStarterRole Role;
        const TCHAR* StationId;
        FVector CanonicalLocation;
        FVector FootprintSizeCm;
        ELBOneFactoryPaintBodyState InputState;
        ELBOneFactoryPaintBodyState OutputState;
        bool bProgrammeBound;
        bool bProgrammeSelectable;
        bool bPlayerPositionable;
    };

    const TArray<FRoleContract>& RoleContracts()
    {
        using R = ELBOneFactoryPaintStarterRole;
        using S = ELBOneFactoryPaintBodyState;
        static const TArray<FRoleContract> Contracts =
        {
            {R::BodySkidReceiving, TEXT("OF_PAINT_BODY_SKID_RECEIVING_001"),
                FVector(0.0f, -8500.0f, 0.0f), FVector(800.0f, 500.0f, 250.0f),
                S::BodyInWhite, S::BodyInWhite, false, false, true},
            {R::PretreatmentWash, TEXT("OF_PAINT_PRETREAT_WASH_001"),
                FVector(1700.0f, -8500.0f, 0.0f), FVector(1300.0f, 1200.0f, 650.0f),
                S::BodyInWhite, S::PretreatedBody, false, false, true},
            {R::EDCoatLogicalProcess, TEXT("OF_PAINT_ED_COAT_LOGICAL_001"),
                FVector(3400.0f, -8500.0f, 0.0f), FVector(1000.0f, 1000.0f, 650.0f),
                S::PretreatedBody, S::EDCoatedBody, true, true, true},
            {R::FlashOff, TEXT("OF_PAINT_FLASH_OFF_001"),
                FVector(4800.0f, -8500.0f, 0.0f), FVector(1000.0f, 1100.0f, 600.0f),
                S::EDCoatedBody, S::EDCoatedBody, false, false, true},
            {R::BlackBoxSprayBooth, TEXT("OF_PAINT_SPRAY_BOOTH_001"),
                FVector(6600.0f, -8500.0f, 0.0f), FVector(1500.0f, 1100.0f, 550.0f),
                S::EDCoatedBody, S::ColourCoatedBody, true, true, true},
            {R::CuringOven, TEXT("OF_PAINT_CURING_OVEN_001"),
                FVector(8800.0f, -8500.0f, 0.0f), FVector(1200.0f, 1200.0f, 650.0f),
                S::ColourCoatedBody, S::CuredPaintedBody, true, false, true},
            {R::QualityLightInspection, TEXT("OF_PAINT_QUALITY_LIGHT_001"),
                FVector(10500.0f, -8500.0f, 0.0f), FVector(800.0f, 800.0f, 500.0f),
                S::CuredPaintedBody, S::InspectedPaintedBody, true, true, true},
            {R::PaintedBodyDispatch, TEXT("OF_PAINT_BODY_DISPATCH_001"),
                FVector(11800.0f, -8500.0f, 0.0f), FVector(800.0f, 500.0f, 250.0f),
                S::InspectedPaintedBody, S::InspectedPaintedBody, true, false, true}
        };
        return Contracts;
    }

    const FRoleContract* FindRoleContract(
        const ELBOneFactoryPaintStarterRole Role)
    {
        return RoleContracts().FindByPredicate([Role](const FRoleContract& Contract)
        {
            return Contract.Role == Role;
        });
    }

    const FRoleContract* FindRoleContract(const FName StationId)
    {
        return RoleContracts().FindByPredicate([StationId](
            const FRoleContract& Contract)
        {
            return StationId == FName(Contract.StationId);
        });
    }

    FBox GetPaintBayBounds()
    {
        const FLBOneFactoryLayoutDefinition Shell =
            ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
        const FLBOneFactoryDepartmentBay* PaintBay =
            Shell.DepartmentBays.FindByPredicate([](
                const FLBOneFactoryDepartmentBay& Bay)
            {
                return Bay.BayId == LBOneFactoryIds::PaintBay()
                    && Bay.Department == ELBOneFactoryDepartment::Paint;
            });
        return PaintBay ? PaintBay->GetWorldBounds() : FBox(ForceInit);
    }

    FBox StationEnvelope(const FLBOneFactoryPaintStarterStationState& Station)
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

    bool SameStringArray(const TArray<FString>& Left,
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

    bool SameAssetAllowance(
        const FLBOneFactoryPaintNativeAssetAllowance& Left,
        const FLBOneFactoryPaintNativeAssetAllowance& Right)
    {
        return Left.AssetPath == Right.AssetPath
            && Left.Provenance == Right.Provenance
            && Left.RequiredAuthoredLODCount == Right.RequiredAuthoredLODCount;
    }

    bool ContainsForbiddenToken(const TArray<FString>& Tokens,
        const FString& Reference)
    {
        return Tokens.ContainsByPredicate([&Reference](const FString& Token)
        {
            return !Token.IsEmpty()
                && Reference.Contains(Token, ESearchCase::IgnoreCase);
        });
    }
}

FName LBOneFactoryPaintStarterIds::Layout()
{
    return FName(TEXT("MOORCROSS_PAINT_STARTER_NATIVE_BLACK_BOX_V001"));
}

FName LBOneFactoryPaintStarterIds::NativeOnlyProfile()
{
    return FName(TEXT("MOORCROSS_PAINT_NATIVE_ONLY_V001"));
}

FName LBOneFactoryPaintStarterIds::Station(
    const ELBOneFactoryPaintStarterRole Role)
{
    const LBOneFactoryPaintStarterPrivate::FRoleContract* Contract =
        LBOneFactoryPaintStarterPrivate::FindRoleContract(Role);
    return Contract ? FName(Contract->StationId) : NAME_None;
}

FName LBOneFactoryPaintStarterIds::Connection(const int32 SourceSequenceIndex)
{
    return SourceSequenceIndex >= 0
        && SourceSequenceIndex <
            ULBOneFactoryPaintStarterLayoutLibrary::RequiredConnectionCount
        ? FName(*FString::Printf(TEXT("OF_PAINT_ROUTE_%02d"),
            SourceSequenceIndex + 1))
        : NAME_None;
}

bool ULBOneFactoryPaintStarterLayoutLibrary::IsPlayerSelectableColour(
    const ELBOneFactoryPaintColour Colour)
{
    return Colour == ELBOneFactoryPaintColour::ArcticWhite
        || Colour == ELBOneFactoryPaintColour::FoundryGraphite
        || Colour == ELBOneFactoryPaintColour::CairnwellTeal
        || Colour == ELBOneFactoryPaintColour::SignalRed
        || Colour == ELBOneFactoryPaintColour::AuroraBlue;
}

FName ULBOneFactoryPaintStarterLayoutLibrary::MakePaintProgrammeId(
    const ELBOneFactoryPaintColour Colour)
{
    switch (Colour)
    {
    case ELBOneFactoryPaintColour::ArcticWhite:
        return FName(TEXT("PAINT_CAIRNWELL_2040_ARCTIC_WHITE_V1"));
    case ELBOneFactoryPaintColour::FoundryGraphite:
        return FName(TEXT("PAINT_CAIRNWELL_2040_FOUNDRY_GRAPHITE_V1"));
    case ELBOneFactoryPaintColour::CairnwellTeal:
        return FName(TEXT("PAINT_CAIRNWELL_2040_CAIRNWELL_TEAL_V1"));
    case ELBOneFactoryPaintColour::SignalRed:
        return FName(TEXT("PAINT_CAIRNWELL_2040_SIGNAL_RED_V1"));
    case ELBOneFactoryPaintColour::AuroraBlue:
        return FName(TEXT("PAINT_CAIRNWELL_2040_AURORA_BLUE_V1"));
    default:
        return NAME_None;
    }
}

FString ULBOneFactoryPaintStarterLayoutLibrary::GetColourDisplayName(
    const ELBOneFactoryPaintColour Colour)
{
    switch (Colour)
    {
    case ELBOneFactoryPaintColour::BodyInWhite: return TEXT("Body in white");
    case ELBOneFactoryPaintColour::EDPrimerGrey: return TEXT("ED primer grey");
    case ELBOneFactoryPaintColour::ArcticWhite: return TEXT("Arctic white");
    case ELBOneFactoryPaintColour::FoundryGraphite: return TEXT("Foundry graphite");
    case ELBOneFactoryPaintColour::CairnwellTeal: return TEXT("Cairnwell teal");
    case ELBOneFactoryPaintColour::SignalRed: return TEXT("Signal red");
    case ELBOneFactoryPaintColour::AuroraBlue: return TEXT("Aurora blue");
    default: return TEXT("Unknown");
    }
}

FLinearColor ULBOneFactoryPaintStarterLayoutLibrary::GetProgrammeDisplayColour(
    const ELBOneFactoryPaintColour Colour)
{
    switch (Colour)
    {
    case ELBOneFactoryPaintColour::BodyInWhite:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("D7D9D8")));
    case ELBOneFactoryPaintColour::EDPrimerGrey:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("7E8587")));
    case ELBOneFactoryPaintColour::ArcticWhite:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("F2F0E8")));
    case ELBOneFactoryPaintColour::FoundryGraphite:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("283238")));
    case ELBOneFactoryPaintColour::CairnwellTeal:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("315F66")));
    case ELBOneFactoryPaintColour::SignalRed:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("B63C38")));
    case ELBOneFactoryPaintColour::AuroraBlue:
        return FLinearColor::FromSRGBColor(FColor::FromHex(TEXT("3973A6")));
    default:
        return FLinearColor::Black;
    }
}

FLBOneFactoryPaintNativeOnlyProfile
ULBOneFactoryPaintStarterLayoutLibrary::MakeNativeOnlyProfile()
{
    using namespace LBOneFactoryPaintStarterPrivate;
    FLBOneFactoryPaintNativeOnlyProfile Profile;
    Profile.ProfileId = LBOneFactoryPaintStarterIds::NativeOnlyProfile();
    Profile.Policy = ELBOneFactoryProvenancePolicy::NativeOnly;
    Profile.AllowedClassPaths = {AuthorityClassPath, PresentationClassPath};

    auto AddAsset = [&Profile](const TCHAR* Path,
        const ELBOneFactoryAssetProvenance Provenance, const int32 LODCount)
    {
        FLBOneFactoryPaintNativeAssetAllowance& Asset =
            Profile.AllowedAssets.AddDefaulted_GetRef();
        Asset.AssetPath = FSoftObjectPath(Path);
        Asset.Provenance = Provenance;
        Asset.RequiredAuthoredLODCount = LODCount;
    };
    AddAsset(CuringOvenPath, ELBOneFactoryAssetProvenance::NativeAuthored, 3);
    AddAsset(PretreatmentPath, ELBOneFactoryAssetProvenance::NativeAuthored, 3);
    AddAsset(FlashOffPath, ELBOneFactoryAssetProvenance::NativeAuthored, 3);
    AddAsset(QualityLightPath, ELBOneFactoryAssetProvenance::NativeAuthored, 3);
    AddAsset(BodySkidPath, ELBOneFactoryAssetProvenance::NativeAuthored, 3);
    AddAsset(ServiceSetPath, ELBOneFactoryAssetProvenance::NativeAuthored, 3);
    AddAsset(AirExtractionPath, ELBOneFactoryAssetProvenance::NativeAuthored, 3);
    AddAsset(SprayBoothPath, ELBOneFactoryAssetProvenance::NativeAuthored, 2);
    AddAsset(CubePath, ELBOneFactoryAssetProvenance::NativeProcedural, 1);
    AddAsset(BasicMaterialPath,
        ELBOneFactoryAssetProvenance::NativeProcedural, 0);

    Profile.ForbiddenSourceTokens = {
        TEXT("Meshy"),
        TEXT("ExternalGenerated"),
        TEXT("Industrial_Welding_Ro"),
        TEXT("part-segmentation"),
        TEXT("AI_Character_output")
    };
    return Profile;
}

bool ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeOnlyProfile(
    const FLBOneFactoryPaintNativeOnlyProfile& Profile, FString& OutReason)
{
    using namespace LBOneFactoryPaintStarterPrivate;
    const FLBOneFactoryPaintNativeOnlyProfile Expected = MakeNativeOnlyProfile();
    if (Profile.Version != 1 || Profile.ProfileId != Expected.ProfileId
        || Profile.Policy != ELBOneFactoryProvenancePolicy::NativeOnly
        || !SameStringArray(Profile.AllowedClassPaths,
            Expected.AllowedClassPaths)
        || !SameStringArray(Profile.ForbiddenSourceTokens,
            Expected.ForbiddenSourceTokens)
        || Profile.AllowedAssets.Num() !=
            RequiredDirectPresentationAssetCount)
    {
        OutReason = TEXT("PAINT NATIVE-ONLY PROFILE HEADER OR EXACT LISTS DRIFTED");
        return false;
    }

    TSet<FString> AssetIdentities;
    for (int32 Index = 0; Index < Expected.AllowedAssets.Num(); ++Index)
    {
        if (!SameAssetAllowance(Profile.AllowedAssets[Index],
                Expected.AllowedAssets[Index])
            || Profile.AllowedAssets[Index].AssetPath.IsNull())
        {
            OutReason = TEXT("PAINT NATIVE-ONLY ASSET ALLOWLIST DRIFTED");
            return false;
        }
        const FString Reference = Profile.AllowedAssets[Index]
            .AssetPath.ToString();
        if (AssetIdentities.Contains(Reference))
        {
            OutReason = TEXT("PAINT NATIVE-ONLY ASSET IDENTITY IS DUPLICATED");
            return false;
        }
        if (ContainsForbiddenToken(Profile.ForbiddenSourceTokens, Reference))
        {
            OutReason = TEXT("PAINT NATIVE-ONLY ASSET CONTAINS A FORBIDDEN TOKEN");
            return false;
        }
        if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
                Profile.Policy, Profile.AllowedAssets[Index].Provenance,
                Reference, OutReason))
        {
            return false;
        }
        AssetIdentities.Add(Reference);
    }
    OutReason = TEXT("PAINT NATIVE-ONLY PROFILE VALID: 2 CLASSES, 10 EXACT ASSETS");
    return true;
}

bool ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeReference(
    const FLBOneFactoryPaintNativeOnlyProfile& Profile,
    const FString& ClassPath, const FString& AssetReference,
    const ELBOneFactoryAssetProvenance Provenance, FString& OutReason)
{
    using namespace LBOneFactoryPaintStarterPrivate;
    if (!ValidateNativeOnlyProfile(Profile, OutReason)) return false;
    if (!Profile.AllowedClassPaths.Contains(ClassPath)
        || ContainsForbiddenToken(Profile.ForbiddenSourceTokens, ClassPath)
        || ContainsForbiddenToken(Profile.ForbiddenSourceTokens,
            AssetReference))
    {
        OutReason = TEXT("PAINT REFERENCE CLASS OR SOURCE IS NOT EXACTLY ALLOWLISTED");
        return false;
    }

    if (AssetReference.Equals(ClassPath, ESearchCase::CaseSensitive))
    {
        if (Provenance != ELBOneFactoryAssetProvenance::NativeCode)
        {
            OutReason = TEXT("PAINT NATIVE CLASS REFERENCE MUST DECLARE NATIVE CODE");
            return false;
        }
        return ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            Profile.Policy, Provenance, AssetReference, OutReason);
    }

    const FLBOneFactoryPaintNativeAssetAllowance* Allowance =
        Profile.AllowedAssets.FindByPredicate([&AssetReference](
            const FLBOneFactoryPaintNativeAssetAllowance& Candidate)
        {
            return Candidate.AssetPath.ToString().Equals(AssetReference,
                ESearchCase::CaseSensitive);
        });
    if (!Allowance || Allowance->Provenance != Provenance)
    {
        OutReason = TEXT("PAINT ASSET PATH OR DECLARED PROVENANCE IS NOT EXACTLY ALLOWLISTED");
        return false;
    }
    return ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
        Profile.Policy, Provenance, AssetReference, OutReason);
}

FLBOneFactoryPaintStarterLayoutState
ULBOneFactoryPaintStarterLayoutLibrary::MakeCanonicalStarterLayout()
{
    using namespace LBOneFactoryPaintStarterPrivate;
    FLBOneFactoryPaintStarterLayoutState State;
    State.LayoutId = LBOneFactoryPaintStarterIds::Layout();
    State.VehicleModelId = LBCairnwell2040PanelCatalog::GetVehicleModelId();
    State.SelectedBodyColour = ELBOneFactoryPaintColour::CairnwellTeal;
    State.PaintProgrammeId = MakePaintProgrammeId(State.SelectedBodyColour);
    State.Revision = 0;
    State.bCommissioned = false;
    State.InputBodyState = ELBOneFactoryPaintBodyState::BodyInWhite;
    State.OutputBodyState = ELBOneFactoryPaintBodyState::InspectedPaintedBody;

    for (const FRoleContract& Contract : RoleContracts())
    {
        FLBOneFactoryPaintStarterStationState& Station =
            State.Stations.AddDefaulted_GetRef();
        Station.StationId = FName(Contract.StationId);
        Station.Role = Contract.Role;
        Station.WorldTransform = FTransform(FRotator::ZeroRotator,
            Contract.CanonicalLocation, FVector::OneVector);
        Station.FootprintSizeCm = Contract.FootprintSizeCm;
        Station.InputBodyState = Contract.InputState;
        Station.OutputBodyState = Contract.OutputState;
        Station.bPlayerProgrammeSelectable = Contract.bProgrammeSelectable;
        Station.bPlayerPositionable = Contract.bPlayerPositionable;
        if (Contract.bProgrammeBound)
        {
            Station.PaintProgrammeId = State.PaintProgrammeId;
            Station.TargetBodyColour = State.SelectedBodyColour;
        }
    }

    for (int32 Index = 0; Index < RequiredConnectionCount; ++Index)
    {
        FLBOneFactoryPaintStarterConnectionState& Connection =
            State.Connections.AddDefaulted_GetRef();
        Connection.ConnectionId = LBOneFactoryPaintStarterIds::Connection(Index);
        Connection.SourceStationId = State.Stations[Index].StationId;
        Connection.TargetStationId = State.Stations[Index + 1].StationId;
        Connection.CarriedBodyState = State.Stations[Index].OutputBodyState;
        Connection.MaximumRouteLengthCm = MaximumRouteLengthCm;
    }
    return State;
}

bool ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
    const FLBOneFactoryPaintStarterLayoutState& State, FString& OutReason)
{
    using namespace LBOneFactoryPaintStarterPrivate;
    OutReason.Reset();
    const TArray<FRoleContract>& Contracts = RoleContracts();
    if (State.Version != 1 || State.LayoutId !=
            LBOneFactoryPaintStarterIds::Layout()
        || State.VehicleModelId !=
            LBCairnwell2040PanelCatalog::GetVehicleModelId()
        || State.Revision < 0
        || State.InputBodyState != ELBOneFactoryPaintBodyState::BodyInWhite
        || State.OutputBodyState !=
            ELBOneFactoryPaintBodyState::InspectedPaintedBody
        || !IsPlayerSelectableColour(State.SelectedBodyColour)
        || State.PaintProgrammeId !=
            MakePaintProgrammeId(State.SelectedBodyColour)
        || State.Stations.Num() != RequiredStationCount
        || State.Connections.Num() != RequiredConnectionCount)
    {
        OutReason = TEXT("PAINT STARTER HEADER, PROGRAMME OR EXACT TOPOLOGY COUNT IS INVALID");
        return false;
    }

    const FBox PaintBay = GetPaintBayBounds();
    if (!PaintBay.IsValid)
    {
        OutReason = TEXT("PAINT STARTER CANNOT RESOLVE ITS ONEFACTORY BAY");
        return false;
    }

    TSet<FName> StationIds;
    TSet<FName> WIPIds;
    TArray<FBox> Envelopes;
    Envelopes.Reserve(State.Stations.Num());
    for (int32 Index = 0; Index < State.Stations.Num(); ++Index)
    {
        const FLBOneFactoryPaintStarterStationState& Station =
            State.Stations[Index];
        const FRoleContract& Contract = Contracts[Index];
        if (Station.Version != 1 || Station.Role != Contract.Role
            || Station.StationId != FName(Contract.StationId)
            || StationIds.Contains(Station.StationId)
            || !Station.FootprintSizeCm.Equals(Contract.FootprintSizeCm,
                LayoutToleranceCm)
            || Station.InputBodyState != Contract.InputState
            || Station.OutputBodyState != Contract.OutputState
            || Station.bPlayerProgrammeSelectable !=
                Contract.bProgrammeSelectable
            || Station.bPlayerPositionable != Contract.bPlayerPositionable
            || !IsTransformUsable(Station.WorldTransform))
        {
            OutReason = TEXT("PAINT STATION IDENTITY, RESPONSIBILITY, FOOTPRINT OR TRANSFORM DRIFTED");
            return false;
        }
        StationIds.Add(Station.StationId);

        if (Contract.bProgrammeBound)
        {
            if (Station.PaintProgrammeId != State.PaintProgrammeId
                || Station.TargetBodyColour != State.SelectedBodyColour)
            {
                OutReason = TEXT("PAINT DOWNSTREAM PROGRAMME RESPONSIBILITIES ARE NOT ATOMIC");
                return false;
            }
        }
        else if (!Station.PaintProgrammeId.IsNone()
            || Station.TargetBodyColour !=
                ELBOneFactoryPaintColour::BodyInWhite)
        {
            OutReason = TEXT("PAINT UPSTREAM STATION FALSELY CLAIMS A COLOUR PROGRAMME");
            return false;
        }

        const FBox Envelope = StationEnvelope(Station);
        if (!PaintBay.IsInsideOrOn(Envelope.Min)
            || !PaintBay.IsInsideOrOn(Envelope.Max))
        {
            OutReason = TEXT("PAINT STATION ENVELOPE LEAVES THE PAINT BAY");
            return false;
        }
        for (const FBox& Existing : Envelopes)
        {
            if (Envelope.Intersect(Existing))
            {
                OutReason = TEXT("PAINT STATION FOOTPRINTS OVERLAP");
                return false;
            }
        }
        Envelopes.Add(Envelope);

        for (const FName UnitId : Station.ActiveOrReservedUnitIds)
        {
            if (UnitId.IsNone() || WIPIds.Contains(UnitId))
            {
                OutReason = TEXT("PAINT WIP IDENTITY IS EMPTY OR DUPLICATED");
                return false;
            }
            WIPIds.Add(UnitId);
        }
    }

    TSet<FName> ConnectionIds;
    for (int32 Index = 0; Index < State.Connections.Num(); ++Index)
    {
        const FLBOneFactoryPaintStarterConnectionState& Connection =
            State.Connections[Index];
        const FLBOneFactoryPaintStarterStationState& Source =
            State.Stations[Index];
        const FLBOneFactoryPaintStarterStationState& Target =
            State.Stations[Index + 1];
        if (Connection.Version != 1
            || Connection.ConnectionId !=
                LBOneFactoryPaintStarterIds::Connection(Index)
            || ConnectionIds.Contains(Connection.ConnectionId)
            || Connection.SourceStationId != Source.StationId
            || Connection.TargetStationId != Target.StationId
            || Connection.CarriedBodyState != Source.OutputBodyState
            || Target.InputBodyState != Source.OutputBodyState
            || !FMath::IsNearlyEqual(Connection.MaximumRouteLengthCm,
                MaximumRouteLengthCm, LayoutToleranceCm)
            || FVector::Dist2D(Source.WorldTransform.GetLocation(),
                Target.WorldTransform.GetLocation()) >
                Connection.MaximumRouteLengthCm + LayoutToleranceCm)
        {
            OutReason = TEXT("PAINT CANONICAL ROUTE IDENTITY, STATE OR REACH IS INVALID");
            return false;
        }
        ConnectionIds.Add(Connection.ConnectionId);
    }

    OutReason = FString::Printf(TEXT(
        "PAINT STARTER VALID: 8 RESPONSIBILITIES, 7 ROUTES, %s, WIP %d"),
        *GetColourDisplayName(State.SelectedBodyColour), WIPIds.Num());
    return true;
}

ALBOneFactoryPaintStarterLayoutAuthority::
    ALBOneFactoryPaintStarterLayoutAuthority()
{
    PrimaryActorTick.bCanEverTick = false;
    SetReplicates(false);
    SetActorEnableCollision(false);
    CurrentState =
        ULBOneFactoryPaintStarterLayoutLibrary::MakeCanonicalStarterLayout();
    Tags.AddUnique(GetAuthorityTag());
    Tags.AddUnique(GetNativeOnlyTag());
    Tags.AddUnique(TEXT("LB.DataAuthority.NoPresentation"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
}

bool ALBOneFactoryPaintStarterLayoutAuthority::HasActiveOrReservedWIP(
    const FLBOneFactoryPaintStarterLayoutState& State)
{
    return State.Stations.ContainsByPredicate([](
        const FLBOneFactoryPaintStarterStationState& Station)
    {
        return !Station.ActiveOrReservedUnitIds.IsEmpty();
    });
}

bool ALBOneFactoryPaintStarterLayoutAuthority::RestoreLayout(
    const FLBOneFactoryPaintStarterLayoutState& State, FString& OutReason)
{
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            State, OutReason))
    {
        return false;
    }
    CurrentState = State;
    OutReason = TEXT("PAINT STARTER LAYOUT RESTORED ATOMICALLY");
    return true;
}

bool ALBOneFactoryPaintStarterLayoutAuthority::SetStationPaintProgramme(
    const FName StationId, const ELBOneFactoryPaintColour TargetColour,
    FString& OutReason)
{
    using namespace LBOneFactoryPaintStarterPrivate;
    const FRoleContract* InvokedContract = FindRoleContract(StationId);
    if (!InvokedContract || !InvokedContract->bProgrammeSelectable)
    {
        OutReason = TEXT("PAINT PROGRAMME CAN ONLY BE CHOSEN AT ED, SPRAY OR QUALITY");
        return false;
    }
    if (!ULBOneFactoryPaintStarterLayoutLibrary::IsPlayerSelectableColour(
            TargetColour))
    {
        OutReason = TEXT("PAINT TARGET IS NOT A PLAYER-SELECTABLE BODY COLOUR");
        return false;
    }
    if (HasActiveOrReservedWIP(CurrentState))
    {
        OutReason = TEXT("PAINT PROGRAMME CHANGE BLOCKED BY ACTIVE OR RESERVED WIP");
        return false;
    }
    if (CurrentState.SelectedBodyColour == TargetColour)
    {
        OutReason = TEXT("PAINT PROGRAMME ALREADY SELECTED");
        return true;
    }

    FLBOneFactoryPaintStarterLayoutState Candidate = CurrentState;
    Candidate.SelectedBodyColour = TargetColour;
    Candidate.PaintProgrammeId =
        ULBOneFactoryPaintStarterLayoutLibrary::MakePaintProgrammeId(
            TargetColour);
    for (FLBOneFactoryPaintStarterStationState& Station : Candidate.Stations)
    {
        const FRoleContract* Contract = FindRoleContract(Station.Role);
        if (Contract && Contract->bProgrammeBound)
        {
            Station.PaintProgrammeId = Candidate.PaintProgrammeId;
            Station.TargetBodyColour = TargetColour;
        }
    }
    ++Candidate.Revision;
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, OutReason))
    {
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = FString::Printf(TEXT("PAINT PROGRAMME CHANGED ATOMICALLY TO %s"),
        *ULBOneFactoryPaintStarterLayoutLibrary::GetColourDisplayName(
            TargetColour));
    return true;
}

bool ALBOneFactoryPaintStarterLayoutAuthority::MoveStation(
    const FName StationId, const FTransform& WorldTransform,
    FString& OutReason)
{
    using namespace LBOneFactoryPaintStarterPrivate;
    const FRoleContract* Contract = FindRoleContract(StationId);
    if (!Contract || !Contract->bPlayerPositionable)
    {
        OutReason = TEXT("PAINT STATION IS UNKNOWN OR NOT PLAYER-POSITIONABLE");
        return false;
    }
    if (HasActiveOrReservedWIP(CurrentState))
    {
        OutReason = TEXT("PAINT STATION MOVE BLOCKED BY ACTIVE OR RESERVED WIP");
        return false;
    }
    FLBOneFactoryPaintStarterLayoutState Candidate = CurrentState;
    FLBOneFactoryPaintStarterStationState* Station =
        Candidate.Stations.FindByPredicate([StationId](
            const FLBOneFactoryPaintStarterStationState& Item)
        {
            return Item.StationId == StationId;
        });
    if (!Station)
    {
        OutReason = TEXT("PAINT STATION ID IS NOT PRESENT IN THE LAYOUT");
        return false;
    }
    if (Station->WorldTransform.Equals(WorldTransform, TransformTolerance))
    {
        OutReason = TEXT("PAINT STATION IS ALREADY AT THAT TRANSFORM");
        return true;
    }
    Station->WorldTransform = WorldTransform;
    ++Candidate.Revision;
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, OutReason))
    {
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = TEXT("PAINT STATION MOVED ATOMICALLY");
    return true;
}

bool ALBOneFactoryPaintStarterLayoutAuthority::Commission(FString& OutReason)
{
    if (CurrentState.bCommissioned)
    {
        OutReason = TEXT("PAINT STARTER IS ALREADY COMMISSIONED");
        return true;
    }
    if (HasActiveOrReservedWIP(CurrentState))
    {
        OutReason = TEXT("PAINT COMMISSIONING BLOCKED BY ACTIVE OR RESERVED WIP");
        return false;
    }
    FLBOneFactoryPaintStarterLayoutState Candidate = CurrentState;
    Candidate.bCommissioned = true;
    ++Candidate.Revision;
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            Candidate, OutReason))
    {
        return false;
    }
    CurrentState = MoveTemp(Candidate);
    OutReason = TEXT("PAINT STARTER COMMISSIONED: BLACK-BOX ROUTE READY");
    return true;
}

FName ALBOneFactoryPaintStarterLayoutAuthority::GetAuthorityTag()
{
    return FName(TEXT("LB.OneFactory.PaintStarter.Authority.v001"));
}

FName ALBOneFactoryPaintStarterLayoutAuthority::GetNativeOnlyTag()
{
    return FName(TEXT("LB.OneFactory.Provenance.NativeOnly"));
}
