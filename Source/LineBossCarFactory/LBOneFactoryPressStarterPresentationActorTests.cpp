#include "LBOneFactoryPressStarterPresentationActor.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "LBFactoryProcessPortComponent.h"
#include "Materials/MaterialInterface.h"
#include "Misc/AutomationTest.h"
#include "UObject/UnrealType.h"

namespace LBOneFactoryPressPresentationTestsPrivate
{
    const TCHAR* DetailedPresentationRoot =
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/");
    const TCHAR* DetailedMeshPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/"
        "SM_OneFactoryDetailedPressPresentation_v001."
        "SM_OneFactoryDetailedPressPresentation_v001");

    TArray<FSoftObjectPath> ExpectedNativeAssets()
    {
        return {
            FSoftObjectPath(DetailedMeshPath),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_AmberSafetyActive_v086.M_CA_MW_PR009_AmberSafetyActive_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_DriveBlue_v086.M_CA_MW_PR009_DriveBlue_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_EStopRed_v086.M_CA_MW_PR009_EStopRed_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LabelWhite_v086.M_CA_MW_PR009_LabelWhite_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v086.M_CA_MW_PR009_LayeredCairnwellGreen_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v086.M_CA_MW_PR009_LayeredFoundryCharcoal_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v086.M_CA_MW_PR009_LayeredSafetyYellow_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredServiceGrey_v086.M_CA_MW_PR009_LayeredServiceGrey_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_MachinedSteel_v086.M_CA_MW_PR009_MachinedSteel_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_OiledBlankSteel_v086.M_CA_MW_PR009_OiledBlankSteel_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_Rubber_v086.M_CA_MW_PR009_Rubber_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_SensorGlass_v086.M_CA_MW_PR009_SensorGlass_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PT_ServiceCopper_v383.M_CA_MW_PT_ServiceCopper_v383"))
        };
    }

    const FLBOneFactoryPressStarterStationState* FindStation(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        const ELBOneFactoryPressStarterRole Role)
    {
        return Layout.Stations.FindByPredicate([Role](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.Role == Role;
        });
    }

    UStaticMeshComponent* FindActiveDetailedComponent(
        const ALBOneFactoryPressStarterPresentationActor& Presentation)
    {
        TArray<UStaticMeshComponent*> Components;
        Presentation.GetComponents<UStaticMeshComponent>(Components);
        UStaticMeshComponent* Active = nullptr;
        for (UStaticMeshComponent* Component : Components)
        {
            if (!Component || !Component->GetStaticMesh()
                || !Component->IsVisible() || Component->bHiddenInGame)
            {
                continue;
            }
            if (Active) return nullptr;
            Active = Component;
        }
        return Active;
    }

    int32 CountRole(const TArray<FLBOneFactoryPressPresentationItem>& Items,
        const ELBOneFactoryPressStarterRole Role)
    {
        int32 Count = 0;
        for (const FLBOneFactoryPressPresentationItem& Item : Items)
        {
            if (Item.Role == Role) ++Count;
        }
        return Count;
    }

    int32 CountBatch(const TArray<FLBOneFactoryPressPresentationItem>& Items,
        const ELBOneFactoryPressPresentationBatch Batch)
    {
        int32 Count = 0;
        for (const FLBOneFactoryPressPresentationItem& Item : Items)
        {
            if (Item.Batch == Batch) ++Count;
        }
        return Count;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryPressPresentationContractTest,
    "LineBoss.OneFactory.PressStarter.Presentation.NativeContractCountsAndRoleLookup",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPressPresentationContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    const FLBOneFactoryPressStarterLayoutState Layout =
        ULBOneFactoryPressStarterLayoutLibrary::MakeCanonicalStarterLayout();
    const TArray<FLBOneFactoryPressPresentationItem> Items =
        ALBOneFactoryPressStarterPresentationActor::
            BuildExpectedPresentationItems(Layout);
    FString Reason;
    TestTrue(TEXT("Exact native Press presentation contract validates"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidatePresentationContract(Layout, Items, Reason));
    TestEqual(TEXT("Presentation renders exactly one detailed aggregate batch"),
        ALBOneFactoryPressStarterPresentationActor::
            GetExpectedVisualBatchCount(), 1);
    TestEqual(TEXT("Presentation renders exactly one visible aggregate"),
        ALBOneFactoryPressStarterPresentationActor::
            GetExpectedVisibleInstanceCount(), 1);
    TestEqual(TEXT("Presentation retains exactly 268 logical selection records"),
        Items.Num(), 268);

    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPressStarterRole::InboundCoilReceiving);
        Value <= static_cast<int32>(
            ELBOneFactoryPressStarterRole::PanelStillageDispatch); ++Value)
    {
        const ELBOneFactoryPressStarterRole Role =
            static_cast<ELBOneFactoryPressStarterRole>(Value);
        TestEqual(TEXT("Each stable station role has its frozen visual count"),
            LBOneFactoryPressPresentationTestsPrivate::CountRole(Items, Role),
            ALBOneFactoryPressStarterPresentationActor::
                GetExpectedInstanceCountForRole(Role));
    }
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPressPresentationBatch::GraphiteCube);
        Value <= static_cast<int32>(
            ELBOneFactoryPressPresentationBatch::FloorRouteCube); ++Value)
    {
        const ELBOneFactoryPressPresentationBatch Batch =
            static_cast<ELBOneFactoryPressPresentationBatch>(Value);
        TestEqual(TEXT("Each logical semantic batch retains its frozen item count"),
            LBOneFactoryPressPresentationTestsPrivate::CountBatch(Items, Batch),
            ALBOneFactoryPressStarterPresentationActor::
                GetExpectedInstanceCountForBatch(Batch));
    }
    TestFalse(TEXT("No presentation primitive claims process WIP"),
        Items.ContainsByPredicate([](
            const FLBOneFactoryPressPresentationItem& Item)
        {
            return Item.bRepresentsProcessWIP;
        }));

    const TArray<FSoftObjectPath> NativeAssets =
        ALBOneFactoryPressStarterPresentationActor::
            GetRequiredNativeAssetPaths();
    TestTrue(TEXT("Exact class plus owned v449 mesh/material closure passes"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPressStarterPresentationActor::
                    GetPresentationClassPath(), NativeAssets, Reason));
    const TArray<FSoftObjectPath> ExpectedNativeAssets =
        LBOneFactoryPressPresentationTestsPrivate::ExpectedNativeAssets();
    TestEqual(TEXT("Exact owned closure contains one mesh plus 13 materials"),
        NativeAssets.Num(), 14);
    TestTrue(TEXT("Owned asset list has exact immutable order"),
        NativeAssets == ExpectedNativeAssets);

    const FObjectPropertyBase* DetailedMeshProperty =
        FindFProperty<FObjectPropertyBase>(
            ALBOneFactoryPressStarterPresentationActor::StaticClass(),
            TEXT("DetailedPresentationMesh"));
    TestNotNull(TEXT(
        "Detailed aggregate dependency is a reflected hard-object property"),
        DetailedMeshProperty);
    if (DetailedMeshProperty)
    {
        TestFalse(TEXT(
            "Detailed aggregate dependency is serialized, never Transient"),
            DetailedMeshProperty->HasAnyPropertyFlags(CPF_Transient));
        TestTrue(TEXT("Hard dependency accepts only UStaticMesh"),
            DetailedMeshProperty->PropertyClass == UStaticMesh::StaticClass());
        const ALBOneFactoryPressStarterPresentationActor* CDO =
            ALBOneFactoryPressStarterPresentationActor::StaticClass()
                ->GetDefaultObject<
                    ALBOneFactoryPressStarterPresentationActor>();
        const UObject* HardReferencedMesh = CDO
            ? DetailedMeshProperty->GetObjectPropertyValue_InContainer(CDO)
            : nullptr;
        TestNotNull(TEXT(
            "Native CDO resolves the packaged-cook aggregate dependency"),
            HardReferencedMesh);
        if (HardReferencedMesh)
        {
            TestEqual(TEXT(
                "Native CDO hard dependency resolves the exact owned mesh"),
                HardReferencedMesh->GetPathName(),
                FString(LBOneFactoryPressPresentationTestsPrivate::
                    DetailedMeshPath));
        }
    }
    for (const FSoftObjectPath& Asset : NativeAssets)
    {
        TestTrue(TEXT("Every required asset is inside the dedicated owned root"),
            Asset.ToString().StartsWith(
                LBOneFactoryPressPresentationTestsPrivate::
                    DetailedPresentationRoot,
                ESearchCase::CaseSensitive));
    }
    TArray<FSoftObjectPath> MeshyInjected = NativeAssets;
    MeshyInjected[0] = FSoftObjectPath(
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MeshyAGV.MeshyAGV"));
    TestFalse(TEXT("A Meshy/vendor substitution fails closed"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPressStarterPresentationActor::
                    GetPresentationClassPath(), MeshyInjected, Reason));
    TestFalse(TEXT("An unapproved presentation class fails closed"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidateNativePresentationReferences(
                TEXT("/Script/LineBossCarFactory.LBFactoryBuildMachine"),
                NativeAssets, Reason));

    TArray<FLBOneFactoryPressPresentationItem> Tampered = Items;
    Tampered[0].bRepresentsProcessWIP = true;
    TestFalse(TEXT("A WIP claim invalidates the complete visual contract"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidatePresentationContract(Layout, Tampered, Reason));
    Tampered = Items;
    Tampered.RemoveAt(Tampered.Num() - 1);
    TestFalse(TEXT("A missing route/primitive invalidates the complete contract"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidatePresentationContract(Layout, Tampered, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryPressPresentationMaterialisationTest,
    "LineBoss.OneFactory.PressStarter.Presentation.FailClosedMaterialisationAndRebind",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPressPresentationMaterialisationTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPressPresentationMaterialisationTest"));
    ALBOneFactoryPressStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryPressStarterLayoutAuthority>() : nullptr;
    ALBOneFactoryPressStarterPresentationActor* Presentation = World
        ? World->SpawnActor<ALBOneFactoryPressStarterPresentationActor>() : nullptr;
    if (!TestNotNull(TEXT("Layout authority fixture exists"), Authority)
        || !TestNotNull(TEXT("Presentation fixture exists"), Presentation))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("Actor has its stable native presentation identity"),
        Presentation->ActorHasTag(
            ALBOneFactoryPressStarterPresentationActor::GetPresentationTag()));
    TestFalse(TEXT("Presentation never ticks"),
        Presentation->PrimaryActorTick.bCanEverTick);
    TestFalse(TEXT("Presentation never replicates"),
        Presentation->GetIsReplicated());
    TestFalse(TEXT("Presentation has no actor collision"),
        Presentation->GetActorEnableCollision());
    TestNull(TEXT("Presentation owns no production process port"),
        Presentation->FindComponentByClass<ULBFactoryProcessPortComponent>());
    TestFalse(TEXT("Presentation never represents process WIP"),
        Presentation->RepresentsProcessWIP());
    TestTrue(TEXT("Actor advertises verified pre-Meshy native provenance"),
        Presentation->ActorHasTag(
            TEXT("LB.Provenance.VerifiedPreMeshyNative")));

    FString Reason;
    TestTrue(TEXT("Canonical layout materialises atomically"),
        Presentation->ConfigureFromLayout(Authority->CaptureLayout(), Reason));
    TestTrue(TEXT("Presentation reports configured"),
        Presentation->IsPresentationConfigured());
    TestEqual(TEXT("Exactly one detailed aggregate is visible"),
        Presentation->GetVisibleInstanceCount(), 1);
    TestEqual(TEXT("Exactly one detailed visual batch is active"),
        Presentation->GetVisualBatchCount(), 1);
    TestEqual(TEXT("Seven-stage Press role retains exact logical inventory"),
        Presentation->GetInstanceCountForRole(
            ELBOneFactoryPressStarterRole::ConfigurablePressTrain), 89);
    TestEqual(TEXT("Graphite logical batch remains available for selection"),
        Presentation->GetInstanceCountForBatch(
            ELBOneFactoryPressPresentationBatch::GraphiteCube), 32);

    TArray<UStaticMeshComponent*> DetailedComponents;
    Presentation->GetComponents<UStaticMeshComponent>(DetailedComponents);
    TestEqual(TEXT("Actor owns exactly two private double-buffer components"),
        DetailedComponents.Num(), 2);
    int32 PopulatedComponentCount = 0;
    for (const UStaticMeshComponent* Component : DetailedComponents)
    {
        if (!TestNotNull(TEXT("Every detailed component exists"), Component))
            continue;
        TestEqual(TEXT("Every detailed component is non-colliding"),
            Component->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
        TestFalse(TEXT("No detailed component affects navigation"),
            Component->CanEverAffectNavigation());
        if (Component->GetStaticMesh())
        {
            ++PopulatedComponentCount;
            TestEqual(TEXT("Active component resolves exact owned v449 mesh"),
                Component->GetStaticMesh()->GetPathName(),
                FString(LBOneFactoryPressPresentationTestsPrivate::
                    DetailedMeshPath));
            TestEqual(TEXT("Detailed aggregate retains exactly 306 slots"),
                Component->GetStaticMesh()->GetStaticMaterials().Num(), 306);
            TSet<FString> ObservedMaterials;
            for (int32 SlotIndex = 0; SlotIndex <
                    Component->GetStaticMesh()->GetStaticMaterials().Num();
                ++SlotIndex)
            {
                const UMaterialInterface* Material =
                    Component->GetStaticMesh()->GetMaterial(SlotIndex);
                if (TestNotNull(TEXT("Every detailed slot resolves a material"),
                        Material))
                {
                    TestTrue(TEXT("Every detailed slot is rebound to owned root"),
                        Material->GetPathName().StartsWith(
                            LBOneFactoryPressPresentationTestsPrivate::
                                DetailedPresentationRoot,
                            ESearchCase::CaseSensitive));
                    ObservedMaterials.Add(Material->GetPathName());
                }
            }
            TestEqual(TEXT("All 13 accepted PBR materials are represented"),
                ObservedMaterials.Num(), 13);
        }
    }
    TestEqual(TEXT("Only one double buffer is populated after commit"),
        PopulatedComponentCount, 1);

    UStaticMeshComponent* FirstCommittedComponent =
        LBOneFactoryPressPresentationTestsPrivate::
            FindActiveDetailedComponent(*Presentation);
    TestNotNull(TEXT("Exactly one detailed component is active"),
        FirstCommittedComponent);

    const FLBOneFactoryPressStarterLayoutState FirstCommittedLayout =
        Authority->CaptureLayout();
    const FLBOneFactoryPressStarterStationState* PressStation =
        LBOneFactoryPressPresentationTestsPrivate::FindStation(
            FirstCommittedLayout,
            ELBOneFactoryPressStarterRole::ConfigurablePressTrain);
    if (TestNotNull(TEXT("Configurable Press train anchor exists"), PressStation)
        && FirstCommittedComponent)
    {
        const FTransform LocalAggregateTransform(FQuat::Identity,
            FVector(9.25f, 2367.5f, 0.0f),
            FVector(100.0f, 100.0f, 100.0f));
        const FTransform ExpectedAggregateTransform =
            LocalAggregateTransform * PressStation->WorldTransform;
        TestTrue(TEXT("Detailed aggregate uses exact datum-relative anchor"),
            FirstCommittedComponent->GetComponentTransform().Equals(
                ExpectedAggregateTransform, 0.01f));
    }

    const FLBOneFactoryPressStarterLayoutState BeforeMove =
        Authority->CaptureLayout();
    const FLBOneFactoryPressStarterStationState* Inspection =
        BeforeMove.Stations.FindByPredicate([](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.StationId ==
                LBOneFactoryPressStarterIds::PanelInspection();
        });
    if (TestNotNull(TEXT("Inspection station exists"), Inspection))
    {
        FTransform Moved = Inspection->WorldTransform;
        Moved.AddToTranslation(FVector(100.0f, 0.0f, 0.0f));
        TestTrue(TEXT("Authority accepts a coherent small station move"),
            Authority->MoveStation(
                LBOneFactoryPressStarterIds::PanelInspection(), Moved, Reason));
        TestTrue(TEXT("Presentation rebinds to the moved authority snapshot"),
            Presentation->ConfigureFromLayout(Authority->CaptureLayout(), Reason));
        FTransform Bound;
        TestTrue(TEXT("Stable station-ID lookup survives the rebind"),
            Presentation->GetConfiguredStationTransform(
                LBOneFactoryPressStarterIds::PanelInspection(), Bound));
        TestTrue(TEXT("Lookup reports the exact moved transform"),
            Bound.Equals(Moved, 0.001f));
    }

    UStaticMeshComponent* SecondCommittedComponent =
        LBOneFactoryPressPresentationTestsPrivate::
            FindActiveDetailedComponent(*Presentation);
    TestNotNull(TEXT("Rebind leaves exactly one detailed component active"),
        SecondCommittedComponent);
    TestTrue(TEXT("Successful rebind commits through the inactive buffer"),
        FirstCommittedComponent && SecondCommittedComponent
            && FirstCommittedComponent != SecondCommittedComponent);

    const FName CommittedLayoutId = Presentation->GetConfiguredLayoutId();
    const int32 CommittedRevision =
        Presentation->GetConfiguredLayoutRevision();
    FTransform CommittedInspectionTransform;
    const bool bHadCommittedInspection =
        Presentation->GetConfiguredStationTransform(
            LBOneFactoryPressStarterIds::PanelInspection(),
            CommittedInspectionTransform);
    const FTransform CommittedAggregateTransform = SecondCommittedComponent
        ? SecondCommittedComponent->GetComponentTransform()
        : FTransform::Identity;

    FLBOneFactoryPressStarterLayoutState Invalid = Authority->CaptureLayout();
    Invalid.Stations[1].StationId = Invalid.Stations[0].StationId;
    TestFalse(TEXT("Invalid authority data fails closed"),
        Presentation->ConfigureFromLayout(Invalid, Reason));
    TestTrue(TEXT("Failed reconfigure preserves committed visual state"),
        Presentation->IsPresentationConfigured());
    TestEqual(TEXT("Failed reconfigure preserves the visible aggregate"),
        Presentation->GetVisibleInstanceCount(), 1);
    TestEqual(TEXT("Failed reconfigure preserves the active batch"),
        Presentation->GetVisualBatchCount(), 1);
    TestEqual(TEXT("Failed reconfigure preserves committed layout identity"),
        Presentation->GetConfiguredLayoutId(), CommittedLayoutId);
    TestEqual(TEXT("Failed reconfigure preserves committed revision"),
        Presentation->GetConfiguredLayoutRevision(), CommittedRevision);
    UStaticMeshComponent* AfterFailedComponent =
        LBOneFactoryPressPresentationTestsPrivate::
            FindActiveDetailedComponent(*Presentation);
    TestTrue(TEXT("Failed reconfigure preserves exact committed buffer"),
        AfterFailedComponent && AfterFailedComponent == SecondCommittedComponent);
    TestTrue(TEXT("Failed reconfigure preserves exact aggregate transform"),
        AfterFailedComponent
            && AfterFailedComponent->GetComponentTransform().Equals(
                CommittedAggregateTransform, 0.001f));
    FTransform AfterFailureInspectionTransform;
    TestTrue(TEXT("Failed reconfigure preserves station-transform snapshot"),
        bHadCommittedInspection
            && Presentation->GetConfiguredStationTransform(
                LBOneFactoryPressStarterIds::PanelInspection(),
                AfterFailureInspectionTransform)
            && AfterFailureInspectionTransform.Equals(
                CommittedInspectionTransform, 0.001f));

    Presentation->ClearPresentation();
    TestEqual(TEXT("Repeated clear is idempotently empty"),
        Presentation->GetVisibleInstanceCount(), 0);
    TestEqual(TEXT("Clear removes the visual batch"),
        Presentation->GetVisualBatchCount(), 0);
    TestEqual(TEXT("Clear removes cached layout identity"),
        Presentation->GetConfiguredLayoutId(), NAME_None);
    for (const UStaticMeshComponent* Component : DetailedComponents)
    {
        TestNull(TEXT("Clear releases both detailed mesh buffers"),
            Component ? Component->GetStaticMesh() : nullptr);
    }
    TestFalse(TEXT("Invalid first configure remains atomically empty"),
        Presentation->ConfigureFromLayout(Invalid, Reason));
    TestFalse(TEXT("Failed first configure has no committed state"),
        Presentation->IsPresentationConfigured());
    TestEqual(TEXT("Failed first configure has zero rendered aggregates"),
        Presentation->GetVisibleInstanceCount(), 0);
    World->DestroyWorld(false);
    return true;
}

#endif
