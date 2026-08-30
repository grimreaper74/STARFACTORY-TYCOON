#if WITH_DEV_AUTOMATION_TESTS

#include "LBPaintShopCellActor.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "LBPaintShopPortComponent.h"
#include "Misc/AutomationTest.h"

#include <limits>

namespace LBPaintShopCellActorTests
{
    const FName TestCellId(TEXT("PAINT_ED_COAT_DIP_CELL_TEST_INSTANCE"));

    bool StateEquals(const FLBPaintShopCellPresentationState& A,
        const FLBPaintShopCellPresentationState& B)
    {
        return A.Version == B.Version
            && A.bCarrierVisible == B.bCarrierVisible
            && FMath::IsNearlyEqual(A.CycleProgress01, B.CycleProgress01)
            && FMath::IsNearlyEqual(A.LiquidLevel01, B.LiquidLevel01)
            && A.bFaulted == B.bFaulted;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopEDCoatCellCanonicalConfigurationTest,
    "LineBoss.PaintShop.Experimental.CellActor.EDCoat.CanonicalConfiguration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopEDCoatCellCanonicalConfigurationTest::RunTest(const FString& Parameters)
{
    ALBPaintShopCellActor* Cell = NewObject<ALBPaintShopCellActor>();
    TestNotNull(TEXT("ED-coat cell fixture can be created"), Cell);
    if (!Cell) return false;

    TestFalse(TEXT("A new cell starts fail-closed"), Cell->IsConfigured());
    TestEqual(TEXT("A new cell exposes no instance ID"), Cell->GetCellId(), NAME_None);
    TestFalse(TEXT("The ED-coat cell never ticks"), Cell->PrimaryActorTick.bCanEverTick);

    FString Reason;
    TestTrue(TEXT("The canonical ED-coat cell configures"), Cell->ConfigureCell(
        LBPaintShopCellActorTests::TestCellId, LBPaintShopCellIds::EDCoatDipCell, Reason));
    TestTrue(TEXT("A valid ED-coat cell is configured"), Cell->IsConfigured());
    TestEqual(TEXT("The instance ID remains exact"), Cell->GetCellId(),
        LBPaintShopCellActorTests::TestCellId);
    TestEqual(TEXT("The definition ID remains exact"), Cell->GetDefinitionId(),
        LBPaintShopCellIds::EDCoatDipCell);
    TestEqual(TEXT("The cell type remains ED coat"), Cell->GetDefinition().CellType,
        ELBPaintShopCellType::EDCoatDip);
    TestEqual(TEXT("The ED recipe remains exact"), Cell->GetDefinition().RecipeId,
        LBPaintShopRecipeIds::EDCoatV001);
    TestTrue(TEXT("The stable cell tag is retained"),
        Cell->ActorHasTag(TEXT("LB.PaintShop.Experimental.Cell.v001")));
    TestTrue(TEXT("The exact instance tag is installed"),
        Cell->ActorHasTag(LBPaintShopCellActorTests::TestCellId));
    const TArray<FString> ExpectedAssetPaths = {
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v002/Modules/SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002.SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v002/Modules/SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002.SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Process/SM_LB_EDLine_TreatmentLiquidSurface_Blockout_v001.SM_LB_EDLine_TreatmentLiquidSurface_Blockout_v001"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Carrier/SM_LB_EDLine_CarrierTrolley_Blockout_v001.SM_LB_EDLine_CarrierTrolley_Blockout_v001"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Carrier/SM_LB_EDLine_CarrierHoistCables_Blockout_v001.SM_LB_EDLine_CarrierHoistCables_Blockout_v001"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Carrier/SM_LB_EDLine_CarrierHanger_Blockout_v001.SM_LB_EDLine_CarrierHanger_Blockout_v001"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Validation/SM_LB_EDLine_ProxyBIW_Blockout_v001.SM_LB_EDLine_ProxyBIW_Blockout_v001"),
        TEXT("/Engine/BasicShapes/Cube.Cube"),
        TEXT("/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/Materials/MI_LB_EDLine_Liquid_ED_Ecoat_v001.MI_LB_EDLine_Liquid_ED_Ecoat_v001")
    };
    TestTrue(TEXT("The asset contract pins approved source paths and the rail primitive"),
        Cell->GetRequiredPresentationAssetPaths() == ExpectedAssetPaths);
    TestTrue(TEXT("All nine required assets resolve into a complete presentation"),
        Cell->HasCompletePresentationAssetSet());
    TestEqual(TEXT("The required twin profiled track has 48 deterministic segments"),
        Cell->GetProfiledRailSegmentCount(), 48);
    TestTrue(TEXT("The generated profiled track is visual-only"),
        Cell->IsProfiledRailVisualOnly());
    TestTrue(TEXT("The two treatment halves occupy one centred 18 m bay"),
        Cell->GetTreatmentStartPresentation()->GetRelativeLocation().Equals(
            FVector(-450.0f, 0.0f, 0.0f), 0.01f)
        && Cell->GetTreatmentEndPresentation()->GetRelativeLocation().Equals(
            FVector(450.0f, 0.0f, 0.0f), 0.01f));
    TestTrue(TEXT("The validated liquid surface spans both 9 m halves"),
        Cell->GetLiquidSurfacePresentation()->GetRelativeScale3D().Equals(
            FVector(2.0f, 1.0f, 1.0f), 0.001f));
    TestTrue(TEXT("The default cell is full but carries no synthesized WIP"),
        Cell->GetLiquidSurfacePresentation()->IsVisible()
        && Cell->GetLiquidSurfacePresentation()->GetRelativeLocation().Equals(
            FVector(0.0f, 0.0f, 285.0f), 0.01f)
        && !Cell->CapturePresentationState().bCarrierVisible);

    ULBPaintShopPortComponent* Input = Cell->GetInputPort();
    ULBPaintShopPortComponent* Output = Cell->GetOutputPort();
    TestNotNull(TEXT("The ED-coat input port exists"), Input);
    TestNotNull(TEXT("The ED-coat output port exists"), Output);
    if (!Input || !Output) return false;
    TestTrue(TEXT("Both carrier ports are configured"),
        Input->IsConfigured() && Output->IsConfigured());
    TestEqual(TEXT("The input port ID is exact"), Input->GetPortId(),
        LBPaintShopPortIds::CarrierIn);
    TestEqual(TEXT("The output port ID is exact"), Output->GetPortId(),
        LBPaintShopPortIds::CarrierOut);
    TestEqual(TEXT("The input accepts complete BIW"), Input->GetWIPId(),
        LBPaintShopWIPIds::BIWComplete);
    TestEqual(TEXT("The output emits ED-coated BIW"), Output->GetWIPId(),
        LBPaintShopWIPIds::BIWEDCoated);
    TestTrue(TEXT("The input socket is on the centred bay boundary"),
        Input->GetRelativeLocation().Equals(FVector(-900.0f, 0.0f, 430.0f), 0.01f));
    TestTrue(TEXT("The output socket is on the centred bay boundary"),
        Output->GetRelativeLocation().Equals(FVector(900.0f, 0.0f, 430.0f), 0.01f));
    const FVector InputForward = Input->GetRelativeRotation().Vector();
    const FVector OutputForward = Output->GetRelativeRotation().Vector();
    TestTrue(TEXT("The input faces outward along local negative X"),
        InputForward.Equals(FVector(-1.0f, 0.0f, 0.0f), 0.001f));
    TestTrue(TEXT("The output faces outward along local positive X"),
        OutputForward.Equals(FVector(1.0f, 0.0f, 0.0f), 0.001f));
    TestTrue(TEXT("The two physical port forwards oppose exactly"),
        FMath::IsNearlyEqual(FVector::DotProduct(InputForward, OutputForward), -1.0f, 0.001f));
    TestTrue(TEXT("FindPort resolves only the stable carrier ports"),
        Cell->FindPort(LBPaintShopPortIds::CarrierIn) == Input
        && Cell->FindPort(LBPaintShopPortIds::CarrierOut) == Output
        && Cell->FindPort(TEXT("UNKNOWN_PORT")) == nullptr);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopEDCoatCellCollisionAuthorityTest,
    "LineBoss.PaintShop.Experimental.CellActor.EDCoat.CollisionAuthority",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopEDCoatCellCollisionAuthorityTest::RunTest(const FString& Parameters)
{
    ALBPaintShopCellActor* Cell = NewObject<ALBPaintShopCellActor>();
    FString Reason;
    TestTrue(TEXT("Collision fixture configures"), Cell && Cell->ConfigureCell(
        LBPaintShopCellActorTests::TestCellId, LBPaintShopCellIds::EDCoatDipCell, Reason));
    if (!Cell) return false;

    UBoxComponent* Footprint = Cell->GetFootprint();
    UBoxComponent* Envelope = Cell->GetProtectedEnvelope();
    TestNotNull(TEXT("A separate gameplay footprint exists"), Footprint);
    TestNotNull(TEXT("A separate protected envelope exists"), Envelope);
    if (!Footprint || !Envelope) return false;
    TestTrue(TEXT("The two collision authorities are distinct components"),
        Footprint != Envelope);
    TestTrue(TEXT("The gameplay footprint has exact one-bay dimensions"),
        Footprint->GetUnscaledBoxExtent().Equals(FVector(900.0f, 500.0f, 426.5f), 0.01f));
    TestTrue(TEXT("The protected envelope includes a service margin"),
        Envelope->GetUnscaledBoxExtent().Equals(FVector(950.0f, 650.0f, 475.0f), 0.01f));
    TestEqual(TEXT("The footprint owns blocking collision"),
        Footprint->GetCollisionEnabled(), ECollisionEnabled::QueryAndPhysics);
    TestEqual(TEXT("The protected envelope is query-only"),
        Envelope->GetCollisionEnabled(), ECollisionEnabled::QueryOnly);
    TestTrue(TEXT("All imported candidate meshes remain visual-only"),
        Cell->AreCandidateMeshesVisualOnly());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopEDCoatCellPresentationStateTest,
    "LineBoss.PaintShop.Experimental.CellActor.EDCoat.PresentationStateRoundTrip",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopEDCoatCellPresentationStateTest::RunTest(const FString& Parameters)
{
    ALBPaintShopCellActor* Source = NewObject<ALBPaintShopCellActor>();
    FString Reason;
    TestTrue(TEXT("Presentation source configures"), Source && Source->ConfigureCell(
        LBPaintShopCellActorTests::TestCellId, LBPaintShopCellIds::EDCoatDipCell, Reason));
    if (!Source) return false;

    FLBPaintShopCellPresentationState Expected;
    Expected.bCarrierVisible = true;
    Expected.CycleProgress01 = 0.5f;
    Expected.LiquidLevel01 = 0.4f;
    Expected.bFaulted = true;
    TestTrue(TEXT("A valid presentation state applies"),
        Source->SetPresentationState(Expected, Reason));
    TestTrue(TEXT("Capture returns the exact applied state"),
        LBPaintShopCellActorTests::StateEquals(Source->CapturePresentationState(), Expected));
    TestTrue(TEXT("Mid-cycle places the trolley on the low treatment rail"),
        Source->GetCarrierTrolleyPresentation()->GetRelativeLocation().Equals(
            FVector(0.0f, 0.0f, 545.0f), 0.01f));
    TestTrue(TEXT("Mid-cycle fully immerses the BIW root"),
        Source->GetProxyBIWPresentation()->GetRelativeLocation().Equals(
            FVector(0.0f, 0.0f, 175.0f), 0.01f));
    TestTrue(TEXT("Liquid level maps deterministically from empty to full"),
        Source->GetLiquidSurfacePresentation()->GetRelativeLocation().Equals(
            FVector(0.0f, 0.0f, 141.0f), 0.01f));
    TestTrue(TEXT("Visible state shows the complete carrier assembly"),
        Source->GetCarrierTrolleyPresentation()->IsVisible()
        && Source->GetCarrierHoistPresentation()->IsVisible()
        && Source->GetCarrierHangerPresentation()->IsVisible()
        && Source->GetProxyBIWPresentation()->IsVisible());
    TestTrue(TEXT("Fault presentation is tagged deterministically"),
        Source->ActorHasTag(TEXT("LB.PaintShop.Cell.Faulted")));

    ALBPaintShopCellActor* Restored = NewObject<ALBPaintShopCellActor>();
    TestTrue(TEXT("Presentation destination configures"), Restored && Restored->ConfigureCell(
        TEXT("PAINT_ED_COAT_DIP_CELL_RESTORED"), LBPaintShopCellIds::EDCoatDipCell, Reason));
    TestTrue(TEXT("Captured display state restores independently of SaveGame"),
        Restored && Restored->RestorePresentationState(
            Source->CapturePresentationState(), Reason));
    if (!Restored) return false;
    TestTrue(TEXT("Restored capture is exact"),
        LBPaintShopCellActorTests::StateEquals(
            Restored->CapturePresentationState(), Expected));
    TestTrue(TEXT("Restored transforms are deterministic"),
        Restored->GetCarrierTrolleyPresentation()->GetRelativeTransform().Equals(
            Source->GetCarrierTrolleyPresentation()->GetRelativeTransform(), 0.001f)
        && Restored->GetProxyBIWPresentation()->GetRelativeTransform().Equals(
            Source->GetProxyBIWPresentation()->GetRelativeTransform(), 0.001f));

    const FLBPaintShopCellPresentationState BeforeInvalid =
        Restored->CapturePresentationState();
    FLBPaintShopCellPresentationState Invalid = BeforeInvalid;
    Invalid.CycleProgress01 = std::numeric_limits<float>::quiet_NaN();
    TestFalse(TEXT("A non-finite cycle value is rejected"),
        Restored->RestorePresentationState(Invalid, Reason));
    TestTrue(TEXT("Invalid restore cannot mutate the current presentation"),
        LBPaintShopCellActorTests::StateEquals(
            Restored->CapturePresentationState(), BeforeInvalid));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopEDCoatCellFailClosedTest,
    "LineBoss.PaintShop.Experimental.CellActor.EDCoat.FailClosed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopEDCoatCellFailClosedTest::RunTest(const FString& Parameters)
{
    ALBPaintShopCellActor* Cell = NewObject<ALBPaintShopCellActor>();
    FString Reason;
    TestTrue(TEXT("Fail-closed fixture first configures"), Cell && Cell->ConfigureCell(
        LBPaintShopCellActorTests::TestCellId, LBPaintShopCellIds::EDCoatDipCell, Reason));
    if (!Cell) return false;

    TestFalse(TEXT("A canonical non-ED cell is rejected"), Cell->ConfigureCell(
        TEXT("PHOSPHATE_TEST"), LBPaintShopCellIds::PhosphateDipCell, Reason));
    TestFalse(TEXT("Non-ED rejection clears configured state"), Cell->IsConfigured());
    TestEqual(TEXT("Non-ED rejection clears the cell ID"), Cell->GetCellId(), NAME_None);
    TestFalse(TEXT("Non-ED rejection clears both carrier ports"),
        Cell->GetInputPort()->IsConfigured() || Cell->GetOutputPort()->IsConfigured());
    TestFalse(TEXT("Non-ED rejection disables collision authority"),
        Cell->GetFootprint()->GetCollisionEnabled() != ECollisionEnabled::NoCollision
        || Cell->GetProtectedEnvelope()->GetCollisionEnabled() != ECollisionEnabled::NoCollision);
    TestFalse(TEXT("Non-ED rejection clears presentation assets"),
        Cell->HasCompletePresentationAssetSet());
    TestTrue(TEXT("Non-ED rejection records a reason"),
        !Cell->GetConfigurationFailureReason().IsEmpty());

    TestFalse(TEXT("An empty instance ID is rejected"), Cell->ConfigureCell(
        NAME_None, LBPaintShopCellIds::EDCoatDipCell, Reason));
    TestFalse(TEXT("An unconfigured cell rejects presentation restore"),
        Cell->RestorePresentationState(FLBPaintShopCellPresentationState(), Reason));
    return true;
}

#endif
