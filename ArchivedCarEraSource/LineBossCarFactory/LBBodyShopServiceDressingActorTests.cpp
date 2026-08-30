#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopServiceDressingActor.h"

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

#include <limits>

namespace LBBodyShopServiceDressingTestsPrivate
{
    bool OverlapsInPlan(const FBox& Left, const FBox& Right)
    {
        return Left.Min.X < Right.Max.X && Left.Max.X > Right.Min.X
            && Left.Min.Y < Right.Max.Y && Left.Max.Y > Right.Min.Y;
    }

    bool IsFiniteTransform(const FTransform& Transform)
    {
        const FVector Location = Transform.GetLocation();
        const FVector Scale = Transform.GetScale3D();
        const FQuat Rotation = Transform.GetRotation();
        return !Location.ContainsNaN() && !Scale.ContainsNaN() && !Rotation.ContainsNaN()
            && Rotation.IsNormalized() && FMath::IsFinite(Location.X)
            && FMath::IsFinite(Location.Y) && FMath::IsFinite(Location.Z);
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopServiceDressingExactInventoryTest,
    "LineBoss.BodyShop.Experimental.ServiceDressing.ExactInventoryRolesAndAssets",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopServiceDressingExactInventoryTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const TArray<FLBBodyShopServiceDressingItem> Layout =
        ALBBodyShopServiceDressingActor::GetApprovedPresentationLayout();
    TestEqual(TEXT("Service apron contains the exact twelve empty props"), Layout.Num(), 12);

    TSet<FName> Identities;
    TMap<FName, int32> RoleCounts;
    TMap<FSoftObjectPath, int32> AssetCounts;
    for (const FLBBodyShopServiceDressingItem& Item : Layout)
    {
        TestFalse(TEXT("Every presentation identity is unique before insertion"),
            Identities.Contains(Item.PresentationId));
        Identities.Add(Item.PresentationId);
        RoleCounts.FindOrAdd(Item.Role) += 1;
        AssetCounts.FindOrAdd(Item.AssetPath) += 1;
    }
    TestEqual(TEXT("Six props are explicitly empty return stillages"),
        RoleCounts.FindRef(ALBBodyShopServiceDressingActor::GetEmptyReturnStillageRole()), 6);
    TestEqual(TEXT("Three props are component-service pallets"),
        RoleCounts.FindRef(ALBBodyShopServiceDressingActor::GetComponentServicePalletRole()), 3);
    TestEqual(TEXT("Three props are explicitly empty small-parts crates"),
        RoleCounts.FindRef(ALBBodyShopServiceDressingActor::GetEmptySmallPartsCrateRole()), 3);

    const TArray<FSoftObjectPath> Assets =
        ALBBodyShopServiceDressingActor::GetApprovedNativeAssetPaths();
    TestEqual(TEXT("Exactly three native v002 logistics meshes are admitted"), Assets.Num(), 3);
    if (Assets.Num() == 3)
    {
        TestEqual(TEXT("The native empty-return cart has six deterministic instances"),
            AssetCounts.FindRef(Assets[0]), 6);
        TestEqual(TEXT("The native component-service pallet has three instances"),
            AssetCounts.FindRef(Assets[1]), 3);
        TestEqual(TEXT("The native open small-parts crate has three instances"),
            AssetCounts.FindRef(Assets[2]), 3);
        TestEqual(TEXT("The empty-return cart path is exact native v002"),
            Assets[0].ToString(), FString(TEXT(
                "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_EmptyReturnCart_v002.SM_LB_BodyShopSupport_EmptyReturnCart_v002")));
        TestEqual(TEXT("The component-service pallet path is exact native v002"),
            Assets[1].ToString(), FString(TEXT(
                "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_ComponentServicePallet_v002.SM_LB_BodyShopSupport_ComponentServicePallet_v002")));
        TestEqual(TEXT("The open crate path is exact native v002"),
            Assets[2].ToString(), FString(TEXT(
                "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002/Logistics/SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002.SM_LB_BodyShopSupport_SmallPartsCrate_Open_v002")));
        for (const FSoftObjectPath& Asset : Assets)
        {
            const FString Path = Asset.ToString();
            TestFalse(TEXT("No active service binding uses a vendor namespace"),
                Path.Contains(TEXT("/Vendor/")));
            TestFalse(TEXT("No active service binding uses the failed support v001 namespace"),
                Path.Contains(TEXT("BodyShopSupportKitNative_v001")));
        }
    }

    FString Reason;
    TestTrue(TEXT("The frozen inventory passes its pure presentation contract"),
        ALBBodyShopServiceDressingActor::ValidatePresentationContract(Layout, Reason));
    TestTrue(TEXT("A valid presentation contract has no failure reason"), Reason.IsEmpty());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopServiceDressingClearanceTest,
    "LineBoss.BodyShop.Experimental.ServiceDressing.FiniteLayoutAndProcessClearance",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopServiceDressingClearanceTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const TArray<FLBBodyShopServiceDressingItem> Layout =
        ALBBodyShopServiceDressingActor::GetApprovedPresentationLayout();
    const TArray<FBox> Maintenance =
        ALBBodyShopServiceDressingActor::GetVerifiedSixCellMaintenanceFootprints();
    const FBox Conveyor =
        ALBBodyShopServiceDressingActor::GetCentralConveyorProtectedFootprint();
    TestEqual(TEXT("Clearance evidence covers all six verified cell envelopes"),
        Maintenance.Num(), 6);
    TestTrue(TEXT("Central conveyor protected footprint is valid"), Conveyor.IsValid != 0);

    for (const FLBBodyShopServiceDressingItem& Item : Layout)
    {
        TestTrue(TEXT("Every service prop has a finite deterministic transform"),
            LBBodyShopServiceDressingTestsPrivate::IsFiniteTransform(Item.RelativeTransform));
        const FBox Footprint =
            ALBBodyShopServiceDressingActor::GetItemValidationFootprint(Item);
        TestTrue(TEXT("Every service prop validation footprint is valid"),
            Footprint.IsValid != 0);
        TestFalse(TEXT("No service prop overlaps the central skid conveyor"),
            LBBodyShopServiceDressingTestsPrivate::OverlapsInPlan(Footprint, Conveyor));
        for (const FBox& CellEnvelope : Maintenance)
        {
            TestFalse(TEXT("No service prop overlaps a six-cell maintenance envelope"),
                LBBodyShopServiceDressingTestsPrivate::OverlapsInPlan(
                    Footprint, CellEnvelope));
        }
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopServiceDressingVisualOnlyTest,
    "LineBoss.BodyShop.Experimental.ServiceDressing.NonWIPVisualOnlyPresentation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopServiceDressingVisualOnlyTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const TArray<FLBBodyShopServiceDressingItem> Layout =
        ALBBodyShopServiceDressingActor::GetApprovedPresentationLayout();
    for (const FLBBodyShopServiceDressingItem& Item : Layout)
    {
        TestFalse(TEXT("An empty service prop never claims process WIP"),
            Item.bRepresentsProcessWIP);
    }

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBBodyShopServiceDressingVisualOnlyTest")));
    if (!TestNotNull(TEXT("Synthetic service-dressing world exists"), World)) return false;

    ALBBodyShopServiceDressingActor* Actor =
        World->SpawnActor<ALBBodyShopServiceDressingActor>();
    if (TestNotNull(TEXT("Service-dressing actor spawns"), Actor))
    {
        TestFalse(TEXT("Actor-level contract never claims process WIP"),
            Actor->RepresentsProcessWIP());
        TestFalse(TEXT("Service dressing has no actor collision"),
            Actor->GetActorEnableCollision());
        TestFalse(TEXT("Service dressing never ticks"), Actor->PrimaryActorTick.bCanEverTick);
        TestTrue(TEXT("All three native assets resolve before presentation becomes visible"),
            Actor->ActivatePresentation());
        TestTrue(TEXT("Presentation is active only after complete resolution"),
            Actor->IsPresentationActive());
        TestTrue(TEXT("Resolved presentation retains a valid contract"),
            Actor->HasValidPresentationContract());
        TestEqual(TEXT("Complete presentation exposes all twelve instances"),
            Actor->GetVisibleInstanceCount(), 12);
        TestTrue(TEXT("Runtime/cook asset paths equal the exact native v002 authority"),
            Actor->GetRuntimeAssetPaths()
                == ALBBodyShopServiceDressingActor::GetApprovedNativeAssetPaths());

        TArray<UPrimitiveComponent*> Primitives;
        Actor->GetComponents<UPrimitiveComponent>(Primitives);
        TestEqual(TEXT("Exactly three visual-only native HISM batches exist"), Primitives.Num(), 3);
        for (const UPrimitiveComponent* Primitive : Primitives)
        {
            TestEqual(TEXT("A service prop batch has no collision"),
                Primitive->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
            TestFalse(TEXT("A service prop batch emits no overlap events"),
                Primitive->GetGenerateOverlapEvents());
            TestFalse(TEXT("A service prop batch never affects navigation"),
                Primitive->CanEverAffectNavigation());
        }
        TArray<UHierarchicalInstancedStaticMeshComponent*> NativeBatches;
        Actor->GetComponents<UHierarchicalInstancedStaticMeshComponent>(NativeBatches);
        TMap<FName, int32> BatchInstanceCounts;
        for (const UHierarchicalInstancedStaticMeshComponent* Batch : NativeBatches)
            BatchInstanceCounts.Add(Batch->GetFName(), Batch->GetInstanceCount());
        TestEqual(TEXT("Native empty-return cart HISM has exactly six instances"),
            BatchInstanceCounts.FindRef(FName(TEXT("EmptyReturnCartNativeV002Instances"))), 6);
        TestEqual(TEXT("Native component-service pallet HISM has exactly three instances"),
            BatchInstanceCounts.FindRef(
                FName(TEXT("ComponentServicePalletNativeV002Instances"))), 3);
        TestEqual(TEXT("Native empty-crate HISM has exactly three instances"),
            BatchInstanceCounts.FindRef(
                FName(TEXT("EmptySmallPartsCrateNativeV002Instances"))), 3);
    }
    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopServiceDressingFailClosedTest,
    "LineBoss.BodyShop.Experimental.ServiceDressing.FailClosedContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopServiceDressingFailClosedTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    FString Reason;
    TArray<FLBBodyShopServiceDressingItem> Invalid =
        ALBBodyShopServiceDressingActor::GetApprovedPresentationLayout();
    Invalid[0].bRepresentsProcessWIP = true;
    TestFalse(TEXT("Any process-WIP claim invalidates the entire dressing contract"),
        ALBBodyShopServiceDressingActor::ValidatePresentationContract(Invalid, Reason));
    TestTrue(TEXT("A rejected WIP claim supplies a failure reason"), !Reason.IsEmpty());

    Invalid = ALBBodyShopServiceDressingActor::GetApprovedPresentationLayout();
    Invalid[1].PresentationId = Invalid[0].PresentationId;
    Reason.Reset();
    TestFalse(TEXT("Duplicate presentation identity fails closed"),
        ALBBodyShopServiceDressingActor::ValidatePresentationContract(Invalid, Reason));
    TestTrue(TEXT("A duplicate identity supplies a failure reason"), !Reason.IsEmpty());

    Invalid = ALBBodyShopServiceDressingActor::GetApprovedPresentationLayout();
    Invalid[2].RelativeTransform.SetLocation(
        FVector(std::numeric_limits<double>::quiet_NaN(), -2850.0, 0.0));
    Reason.Reset();
    TestFalse(TEXT("A non-finite layout transform fails closed"),
        ALBBodyShopServiceDressingActor::ValidatePresentationContract(Invalid, Reason));
    TestTrue(TEXT("A non-finite transform supplies a failure reason"), !Reason.IsEmpty());

    TArray<FSoftObjectPath> IncompleteAssets =
        ALBBodyShopServiceDressingActor::GetApprovedNativeAssetPaths();
    IncompleteAssets.Pop();
    Reason.Reset();
    TestFalse(TEXT("One missing native asset rejects the complete presentation"),
        ALBBodyShopServiceDressingActor::ValidateResolvedAssetPaths(
            IncompleteAssets, Reason));
    TestTrue(TEXT("Incomplete asset resolution supplies a failure reason"),
        !Reason.IsEmpty());
    return true;
}

#endif
