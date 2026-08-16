#include "LBBodyShopServiceDressingActor.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/StaticMesh.h"
#include "LBBodyShopBuildAuthority.h"
#include "LBBodyShopTypes.h"

namespace LBBodyShopServiceDressingPrivate
{
    const TCHAR* EmptyReturnCartPath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_EmptyReturnCart_v002.SM_LB_BodyShopSupport_EmptyReturnCart_v002");
    const TCHAR* ComponentServicePalletPath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_ComponentServicePallet_v002.SM_LB_BodyShopSupport_ComponentServicePallet_v002");
    const TCHAR* SmallPartsCratePath =
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002.SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002");

    const FName EmptyReturnStillage(TEXT("EmptyReturnStillage"));
    const FName ComponentServicePallet(TEXT("ComponentServicePallet"));
    const FName EmptySmallPartsCrate(TEXT("EmptySmallPartsCrate"));

    constexpr float TransformTolerance = 0.01f;

    FLBBodyShopServiceDressingItem MakeItem(const TCHAR* Id, const FName Role,
        const TCHAR* AssetPath, const FVector& Location, const float YawDegrees,
        const FVector& FootprintCm)
    {
        FLBBodyShopServiceDressingItem Item;
        Item.PresentationId = FName(Id);
        Item.Role = Role;
        Item.AssetPath = FSoftObjectPath(AssetPath);
        Item.RelativeTransform = FTransform(FRotator(0.0f, YawDegrees, 0.0f), Location,
            FVector::OneVector);
        Item.FootprintCm = FootprintCm;
        Item.bRepresentsProcessWIP = false;
        return Item;
    }

    TArray<FLBBodyShopServiceDressingItem> BuildApprovedLayout()
    {
        TArray<FLBBodyShopServiceDressingItem> Layout;
        Layout.Reserve(12);

        // South apron: visibly empty return equipment, parallel to the service aisle.
        Layout.Add(MakeItem(TEXT("BS_EMPTY_RETURN_01"), EmptyReturnStillage,
            EmptyReturnCartPath, FVector(-6500.0f, -2850.0f, 0.0f), 90.0f,
            FVector(220.0f, 220.0f, 170.0f)));
        Layout.Add(MakeItem(TEXT("BS_EMPTY_RETURN_02"), EmptyReturnStillage,
            EmptyReturnCartPath, FVector(-5600.0f, -2850.0f, 0.0f), 90.0f,
            FVector(220.0f, 190.0f, 170.0f)));
        Layout.Add(MakeItem(TEXT("BS_EMPTY_RETURN_03"), EmptyReturnStillage,
            EmptyReturnCartPath, FVector(-4500.0f, -2850.0f, 0.0f), 90.0f,
            FVector(220.0f, 220.0f, 170.0f)));
        Layout.Add(MakeItem(TEXT("BS_EMPTY_RETURN_04"), EmptyReturnStillage,
            EmptyReturnCartPath, FVector(-3400.0f, -2850.0f, 0.0f), 90.0f,
            FVector(220.0f, 190.0f, 170.0f)));
        Layout.Add(MakeItem(TEXT("BS_EMPTY_RETURN_05"), EmptyReturnStillage,
            EmptyReturnCartPath, FVector(-2500.0f, -2850.0f, 0.0f), 90.0f,
            FVector(220.0f, 220.0f, 170.0f)));
        Layout.Add(MakeItem(TEXT("BS_EMPTY_RETURN_06"), EmptyReturnStillage,
            EmptyReturnCartPath, FVector(-1600.0f, -2850.0f, 0.0f), 90.0f,
            FVector(220.0f, 190.0f, 170.0f)));

        // North apron: empty component-service pallets and small-parts crates.  They are
        // deliberately offset from one another so the row reads as serviced storage, not WIP.
        Layout.Add(MakeItem(TEXT("BS_COMPONENT_PALLET_01"), ComponentServicePallet,
            ComponentServicePalletPath, FVector(-6200.0f, -850.0f, 0.0f), 0.0f,
            FVector(180.0f, 180.0f, 25.0f)));
        Layout.Add(MakeItem(TEXT("BS_COMPONENT_PALLET_02"), ComponentServicePallet,
            ComponentServicePalletPath, FVector(-4700.0f, -850.0f, 0.0f), 90.0f,
            FVector(180.0f, 180.0f, 25.0f)));
        Layout.Add(MakeItem(TEXT("BS_COMPONENT_PALLET_03"), ComponentServicePallet,
            ComponentServicePalletPath, FVector(-3200.0f, -850.0f, 0.0f), 0.0f,
            FVector(180.0f, 180.0f, 25.0f)));
        Layout.Add(MakeItem(TEXT("BS_EMPTY_CRATE_01"), EmptySmallPartsCrate,
            SmallPartsCratePath, FVector(-5500.0f, -850.0f, 0.0f), 90.0f,
            FVector(140.0f, 120.0f, 120.0f)));
        Layout.Add(MakeItem(TEXT("BS_EMPTY_CRATE_02"), EmptySmallPartsCrate,
            SmallPartsCratePath, FVector(-4000.0f, -850.0f, 0.0f), 0.0f,
            FVector(140.0f, 120.0f, 120.0f)));
        Layout.Add(MakeItem(TEXT("BS_EMPTY_CRATE_03"), EmptySmallPartsCrate,
            SmallPartsCratePath, FVector(-2350.0f, -850.0f, 0.0f), 90.0f,
            FVector(140.0f, 120.0f, 120.0f)));
        return Layout;
    }

    bool IsFiniteTransform(const FTransform& Transform)
    {
        const FVector Location = Transform.GetLocation();
        const FVector Scale = Transform.GetScale3D();
        const FQuat Rotation = Transform.GetRotation();
        return !Location.ContainsNaN() && !Scale.ContainsNaN() && !Rotation.ContainsNaN()
            && Rotation.IsNormalized()
            && FMath::IsFinite(Location.X) && FMath::IsFinite(Location.Y)
            && FMath::IsFinite(Location.Z) && FMath::IsFinite(Scale.X)
            && FMath::IsFinite(Scale.Y) && FMath::IsFinite(Scale.Z);
    }

    FBox MakeValidationFootprint(const FVector& SizeCm, const FTransform& Transform)
    {
        const FVector Half = SizeCm * 0.5f;
        const FBox LocalBox(FVector(-Half.X, -Half.Y, 0.0f),
            FVector(Half.X, Half.Y, SizeCm.Z));
        return LocalBox.TransformBy(Transform);
    }

    bool OverlapsInPlan(const FBox& Left, const FBox& Right)
    {
        return Left.Min.X < Right.Max.X && Left.Max.X > Right.Min.X
            && Left.Min.Y < Right.Max.Y && Left.Max.Y > Right.Min.Y;
    }
}

ALBBodyShopServiceDressingActor::ALBBodyShopServiceDressingActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetActorEnableCollision(false);
    SetReplicates(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    EmptyReturnCartInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("EmptyReturnCartNativeV002Instances"));
    EmptyReturnCartInstances->SetupAttachment(SceneRoot);
    ComponentServicePalletInstances =
        CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
            TEXT("ComponentServicePalletNativeV002Instances"));
    ComponentServicePalletInstances->SetupAttachment(SceneRoot);
    SmallPartsCrateInstances = CreateDefaultSubobject<UHierarchicalInstancedStaticMeshComponent>(
        TEXT("EmptySmallPartsCrateNativeV002Instances"));
    SmallPartsCrateInstances->SetupAttachment(SceneRoot);

    ConfigureVisualInstances(EmptyReturnCartInstances);
    ConfigureVisualInstances(ComponentServicePalletInstances);
    ConfigureVisualInstances(SmallPartsCrateInstances);

    EmptyReturnCartMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopServiceDressingPrivate::EmptyReturnCartPath));
    ComponentServicePalletMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopServiceDressingPrivate::ComponentServicePalletPath));
    SmallPartsCrateMesh = TSoftObjectPtr<UStaticMesh>(
        FSoftObjectPath(LBBodyShopServiceDressingPrivate::SmallPartsCratePath));

    bPresentationContractValid = ValidatePresentationContract(
        GetApprovedPresentationLayout(), PresentationContractFailureReason);
    bRepresentsProcessWIP = false;

    Tags.AddUnique(TEXT("LB.BodyShop.ServiceDressing.v002"));
    Tags.AddUnique(TEXT("LB.BodyShop.EmptyContainers"));
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.Asset.CleanRoomNative.v002"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
}

void ALBBodyShopServiceDressingActor::ConfigureVisualInstances(
    UHierarchicalInstancedStaticMeshComponent* Component) const
{
    if (!Component) return;
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
}

void ALBBodyShopServiceDressingActor::ClearPresentation()
{
    UHierarchicalInstancedStaticMeshComponent* Components[] = {
        EmptyReturnCartInstances,
        ComponentServicePalletInstances,
        SmallPartsCrateInstances
    };
    for (UHierarchicalInstancedStaticMeshComponent* Component : Components)
    {
        if (!Component) continue;
        Component->ClearInstances();
        Component->SetStaticMesh(nullptr);
    }
    bPresentationActive = false;
}

bool ALBBodyShopServiceDressingActor::ActivatePresentation()
{
    if (bPresentationActive && bPresentationContractValid) return true;

    ClearPresentation();
    const TArray<FLBBodyShopServiceDressingItem> Layout = GetApprovedPresentationLayout();
    if (!ValidatePresentationContract(Layout, PresentationContractFailureReason))
    {
        bPresentationContractValid = false;
        return false;
    }

    UStaticMesh* LoadedEmptyReturnCart = EmptyReturnCartMesh.LoadSynchronous();
    UStaticMesh* LoadedComponentServicePallet = ComponentServicePalletMesh.LoadSynchronous();
    UStaticMesh* LoadedSmallPartsCrate = SmallPartsCrateMesh.LoadSynchronous();

    TArray<FSoftObjectPath> ResolvedAssetPaths;
    if (LoadedEmptyReturnCart)
        ResolvedAssetPaths.Add(EmptyReturnCartMesh.ToSoftObjectPath());
    if (LoadedComponentServicePallet)
        ResolvedAssetPaths.Add(ComponentServicePalletMesh.ToSoftObjectPath());
    if (LoadedSmallPartsCrate) ResolvedAssetPaths.Add(SmallPartsCrateMesh.ToSoftObjectPath());
    if (!ValidateResolvedAssetPaths(ResolvedAssetPaths, PresentationContractFailureReason))
    {
        ClearPresentation();
        bPresentationContractValid = false;
        UE_LOG(LogTemp, Warning, TEXT("LINE_BOSS_BODYSHOP_SERVICE_DRESSING_FAILED %s"),
            *PresentationContractFailureReason);
        return false;
    }

    // SetStaticMesh retains each native source mesh's authored material array. This actor
    // deliberately supplies no material overrides, dynamic materials or recolouring.
    EmptyReturnCartInstances->SetStaticMesh(LoadedEmptyReturnCart);
    ComponentServicePalletInstances->SetStaticMesh(LoadedComponentServicePallet);
    SmallPartsCrateInstances->SetStaticMesh(LoadedSmallPartsCrate);

    for (const FLBBodyShopServiceDressingItem& Item : Layout)
    {
        UHierarchicalInstancedStaticMeshComponent* Component =
            FindComponentForAssetPath(Item.AssetPath);
        if (!Component)
        {
            PresentationContractFailureReason = FString::Printf(
                TEXT("BODY SHOP SERVICE DRESSING HAS NO COMPONENT FOR %s"),
                *Item.AssetPath.ToString());
            ClearPresentation();
            bPresentationContractValid = false;
            return false;
        }
        Component->AddInstance(Item.RelativeTransform);
    }

    if (GetVisibleInstanceCount() != Layout.Num())
    {
        PresentationContractFailureReason = TEXT(
            "BODY SHOP SERVICE DRESSING DID NOT CREATE ITS EXACT INSTANCE INVENTORY");
        ClearPresentation();
        bPresentationContractValid = false;
        return false;
    }

    bPresentationContractValid = true;
    PresentationContractFailureReason.Reset();
    bPresentationActive = true;
    UE_LOG(LogTemp, Display,
        TEXT("LINE_BOSS_BODYSHOP_SERVICE_DRESSING_ACTIVE empty_returns=6 service_pallets=3 empty_crates=3 wip=0"));
    return true;
}

TArray<FLBBodyShopServiceDressingItem>
ALBBodyShopServiceDressingActor::GetPresentationLayout() const
{
    return GetApprovedPresentationLayout();
}

int32 ALBBodyShopServiceDressingActor::GetApprovedRoleCount(const FName InRole) const
{
    int32 Count = 0;
    for (const FLBBodyShopServiceDressingItem& Item : GetApprovedPresentationLayout())
    {
        if (Item.Role == InRole) ++Count;
    }
    return Count;
}

int32 ALBBodyShopServiceDressingActor::GetVisibleInstanceCount() const
{
    int32 Count = 0;
    const UHierarchicalInstancedStaticMeshComponent* Components[] = {
        EmptyReturnCartInstances,
        ComponentServicePalletInstances,
        SmallPartsCrateInstances
    };
    for (const UHierarchicalInstancedStaticMeshComponent* Component : Components)
    {
        Count += Component ? Component->GetInstanceCount() : 0;
    }
    return Count;
}

TArray<FSoftObjectPath> ALBBodyShopServiceDressingActor::GetRuntimeAssetPaths() const
{
    return {
        EmptyReturnCartMesh.ToSoftObjectPath(),
        ComponentServicePalletMesh.ToSoftObjectPath(),
        SmallPartsCrateMesh.ToSoftObjectPath()
    };
}

FName ALBBodyShopServiceDressingActor::GetEmptyReturnStillageRole()
{
    return LBBodyShopServiceDressingPrivate::EmptyReturnStillage;
}

FName ALBBodyShopServiceDressingActor::GetComponentServicePalletRole()
{
    return LBBodyShopServiceDressingPrivate::ComponentServicePallet;
}

FName ALBBodyShopServiceDressingActor::GetEmptySmallPartsCrateRole()
{
    return LBBodyShopServiceDressingPrivate::EmptySmallPartsCrate;
}

TArray<FLBBodyShopServiceDressingItem>
ALBBodyShopServiceDressingActor::GetApprovedPresentationLayout()
{
    return LBBodyShopServiceDressingPrivate::BuildApprovedLayout();
}

TArray<FSoftObjectPath>
ALBBodyShopServiceDressingActor::GetApprovedNativeAssetPaths()
{
    return {
        FSoftObjectPath(LBBodyShopServiceDressingPrivate::EmptyReturnCartPath),
        FSoftObjectPath(LBBodyShopServiceDressingPrivate::ComponentServicePalletPath),
        FSoftObjectPath(LBBodyShopServiceDressingPrivate::SmallPartsCratePath)
    };
}

TArray<FBox> ALBBodyShopServiceDressingActor::GetVerifiedSixCellMaintenanceFootprints()
{
    TArray<FBox> Footprints;
    const TArray<FLBBodyShopApprovedLayoutItem> Layout =
        ALBBodyShopBuildAuthority::GetApprovedUnderbodySliceLayout();
    Footprints.Reserve(Layout.Num());
    for (const FLBBodyShopApprovedLayoutItem& Placed : Layout)
    {
        FLBBodyShopCellDefinition Definition;
        if (!FLBBodyShopDefinitionRegistry::FindCanonicalDefinition(
                Placed.DefinitionId, Definition))
        {
            // An invalid box makes the presentation contract fail rather than silently
            // accepting dressing against an unknown process envelope.
            Footprints.Add(FBox(EForceInit::ForceInit));
            continue;
        }
        Footprints.Add(LBBodyShopServiceDressingPrivate::MakeValidationFootprint(
            Definition.MaintenanceEnvelopeCm, Placed.WorldTransform));
    }
    return Footprints;
}

FBox ALBBodyShopServiceDressingActor::GetCentralConveyorProtectedFootprint()
{
    // The visible neutral lane is 260 cm wide.  Its protected validation corridor spans
    // the full six-cell line, including both end-transfer clearances.
    return FBox(FVector(-7100.0f, -1930.0f, -1.0f),
        FVector(-1050.0f, -1670.0f, 500.0f));
}

FBox ALBBodyShopServiceDressingActor::GetItemValidationFootprint(
    const FLBBodyShopServiceDressingItem& Item)
{
    return LBBodyShopServiceDressingPrivate::MakeValidationFootprint(
        Item.FootprintCm, Item.RelativeTransform);
}

bool ALBBodyShopServiceDressingActor::ValidatePresentationContract(
    const TArray<FLBBodyShopServiceDressingItem>& Layout, FString& OutReason)
{
    OutReason.Reset();
    const TArray<FLBBodyShopServiceDressingItem> Approved = GetApprovedPresentationLayout();
    if (Layout.Num() != 12 || Layout.Num() != Approved.Num())
    {
        OutReason = TEXT("BODY SHOP SERVICE DRESSING REQUIRES EXACTLY 12 EMPTY PROPS");
        return false;
    }

    TSet<FName> Identities;
    TMap<FName, int32> RoleCounts;
    for (int32 Index = 0; Index < Layout.Num(); ++Index)
    {
        const FLBBodyShopServiceDressingItem& Item = Layout[Index];
        const FLBBodyShopServiceDressingItem& Expected = Approved[Index];
        if (Item.Version != 1 || Item.PresentationId.IsNone() || Item.Role.IsNone()
            || Item.AssetPath.IsNull() || Item.FootprintCm.ContainsNaN()
            || !FMath::IsFinite(Item.FootprintCm.X) || !FMath::IsFinite(Item.FootprintCm.Y)
            || !FMath::IsFinite(Item.FootprintCm.Z) || Item.FootprintCm.GetMin() <= 0.0f
            || !LBBodyShopServiceDressingPrivate::IsFiniteTransform(Item.RelativeTransform))
        {
            OutReason = TEXT("BODY SHOP SERVICE DRESSING HAS INVALID CORE PRESENTATION DATA");
            return false;
        }
        const FRotator Rotation = Item.RelativeTransform.Rotator();
        if (!Item.RelativeTransform.GetScale3D().Equals(FVector::OneVector,
                LBBodyShopServiceDressingPrivate::TransformTolerance)
            || !FMath::IsNearlyZero(Rotation.Pitch,
                LBBodyShopServiceDressingPrivate::TransformTolerance)
            || !FMath::IsNearlyZero(Rotation.Roll,
                LBBodyShopServiceDressingPrivate::TransformTolerance))
        {
            OutReason = TEXT("BODY SHOP SERVICE DRESSING REQUIRES FINITE UNSCALED FLOOR TRANSFORMS");
            return false;
        }
        if (Item.bRepresentsProcessWIP)
        {
            OutReason = TEXT("BODY SHOP SERVICE DRESSING CANNOT REPRESENT PROCESS WIP");
            return false;
        }
        if (Identities.Contains(Item.PresentationId))
        {
            OutReason = TEXT("BODY SHOP SERVICE DRESSING PRESENTATION IDENTITIES MUST BE UNIQUE");
            return false;
        }
        Identities.Add(Item.PresentationId);
        RoleCounts.FindOrAdd(Item.Role) += 1;

        if (Item.PresentationId != Expected.PresentationId || Item.Role != Expected.Role
            || Item.AssetPath != Expected.AssetPath
            || !Item.RelativeTransform.Equals(Expected.RelativeTransform,
                LBBodyShopServiceDressingPrivate::TransformTolerance)
            || !Item.FootprintCm.Equals(Expected.FootprintCm,
                LBBodyShopServiceDressingPrivate::TransformTolerance))
        {
            OutReason = TEXT("BODY SHOP SERVICE DRESSING INVENTORY OR LAYOUT DRIFTED FROM V1");
            return false;
        }
    }

    if (RoleCounts.Num() != 3
        || RoleCounts.FindRef(GetEmptyReturnStillageRole()) != 6
        || RoleCounts.FindRef(GetComponentServicePalletRole()) != 3
        || RoleCounts.FindRef(GetEmptySmallPartsCrateRole()) != 3)
    {
        OutReason = TEXT("BODY SHOP SERVICE DRESSING HAS AN INVALID EMPTY-CONTAINER ROLE COUNT");
        return false;
    }

    const TArray<FBox> MaintenanceFootprints = GetVerifiedSixCellMaintenanceFootprints();
    if (MaintenanceFootprints.Num() != 6)
    {
        OutReason = TEXT("BODY SHOP SERVICE DRESSING CANNOT RESOLVE THE VERIFIED SIX-CELL LINE");
        return false;
    }
    for (const FBox& Footprint : MaintenanceFootprints)
    {
        if (!Footprint.IsValid)
        {
            OutReason = TEXT("BODY SHOP SERVICE DRESSING HAS AN INVALID PROCESS ENVELOPE");
            return false;
        }
    }

    const FBox Conveyor = GetCentralConveyorProtectedFootprint();
    for (int32 Left = 0; Left < Layout.Num(); ++Left)
    {
        const FBox ItemFootprint = GetItemValidationFootprint(Layout[Left]);
        if (!ItemFootprint.IsValid
            || LBBodyShopServiceDressingPrivate::OverlapsInPlan(ItemFootprint, Conveyor))
        {
            OutReason = TEXT("BODY SHOP SERVICE DRESSING OVERLAPS THE CENTRAL CONVEYOR");
            return false;
        }
        for (const FBox& ProcessFootprint : MaintenanceFootprints)
        {
            if (LBBodyShopServiceDressingPrivate::OverlapsInPlan(
                    ItemFootprint, ProcessFootprint))
            {
                OutReason = TEXT("BODY SHOP SERVICE DRESSING OVERLAPS A CELL MAINTENANCE ZONE");
                return false;
            }
        }
        for (int32 Right = Left + 1; Right < Layout.Num(); ++Right)
        {
            if (LBBodyShopServiceDressingPrivate::OverlapsInPlan(
                    ItemFootprint, GetItemValidationFootprint(Layout[Right])))
            {
                OutReason = TEXT("BODY SHOP SERVICE DRESSING PROPS OVERLAP ONE ANOTHER");
                return false;
            }
        }
    }
    return true;
}

bool ALBBodyShopServiceDressingActor::ValidateResolvedAssetPaths(
    const TArray<FSoftObjectPath>& ResolvedAssetPaths, FString& OutReason)
{
    OutReason.Reset();
    const TArray<FSoftObjectPath> Required = GetApprovedNativeAssetPaths();
    if (ResolvedAssetPaths.Num() != Required.Num())
    {
        OutReason = TEXT("BODY SHOP SERVICE DRESSING REQUIRES ALL THREE NATIVE V002 ASSETS");
        return false;
    }
    for (int32 Index = 0; Index < Required.Num(); ++Index)
    {
        if (ResolvedAssetPaths[Index].IsNull()
            || ResolvedAssetPaths[Index] != Required[Index])
        {
            OutReason = TEXT("BODY SHOP SERVICE DRESSING ASSET RESOLUTION IS INCOMPLETE OR DRIFTED");
            return false;
        }
    }
    return true;
}

UHierarchicalInstancedStaticMeshComponent*
ALBBodyShopServiceDressingActor::FindComponentForAssetPath(
    const FSoftObjectPath& AssetPath) const
{
    if (AssetPath == EmptyReturnCartMesh.ToSoftObjectPath()) return EmptyReturnCartInstances;
    if (AssetPath == ComponentServicePalletMesh.ToSoftObjectPath())
        return ComponentServicePalletInstances;
    if (AssetPath == SmallPartsCrateMesh.ToSoftObjectPath()) return SmallPartsCrateInstances;
    return nullptr;
}
