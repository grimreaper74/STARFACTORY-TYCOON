#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopCellActor.h"
#include "LBBodyShopPortComponent.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopDedicatedCellPresentationTest,
    "LineBoss.BodyShop.Experimental.Presentation.DedicatedRuntimeArtAndOpenSafetyRails",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopDedicatedCellPresentationTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBBodyShopDedicatedCellPresentationTest")));
    if (!TestNotNull(TEXT("Synthetic Body Shop presentation world exists"), World))
        return false;

    ALBBodyShopCellActor* Underbody = World->SpawnActor<ALBBodyShopCellActor>();
    ALBBodyShopCellActor* Vision = World->SpawnActor<ALBBodyShopCellActor>();
    ALBBodyShopCellActor* StillageDock = World->SpawnActor<ALBBodyShopCellActor>();
    ALBBodyShopCellActor* PanelPresentation = World->SpawnActor<ALBBodyShopCellActor>();
    FString Reason;
    TestNotNull(TEXT("Underbody cell actor spawns"), Underbody);
    TestNotNull(TEXT("Vision cell actor spawns"), Vision);
    TestNotNull(TEXT("Stillage dock cell actor spawns"), StillageDock);
    TestNotNull(TEXT("Panel-presentation cell actor spawns"), PanelPresentation);
    TestTrue(TEXT("Duplicate-WIP guard retains legacy stillage recognition"),
        ALBBodyShopCellActor::IsRuntimeStillagePresentationMeshName(
            TEXT("SM_LB_PanelStillage_Runtime_v001")));
    TestTrue(TEXT("Duplicate-WIP guard recognizes the promoted native v002 full stillage"),
        ALBBodyShopCellActor::IsRuntimeStillagePresentationMeshName(
            TEXT("SM_LB_BodyShopSupport_PanelStillage_Full_v002")));
    TestFalse(TEXT("Duplicate-WIP guard rejects an unrelated native service prop"),
        ALBBodyShopCellActor::IsRuntimeStillagePresentationMeshName(
            TEXT("SM_LB_BodyShopSupport_EmptyReturnCart_v002")));

    if (StillageDock)
    {
        Reason.Reset();
        TestTrue(TEXT("Full-stillage dock configures"), StillageDock->ConfigureCell(
            TEXT("TEST_STILLAGE_DOCK"), LBBodyShopPrototypeIds::FullStillageDock, Reason));
        TestFalse(TEXT("Full-stillage dock contains no duplicate static WIP stillage"),
            StillageDock->HasStaticStillagePresentation());
        TestFalse(TEXT("Full-stillage dock fixed presentation contains no carrier or workpiece"),
            StillageDock->HasStaticCarrierOrWorkpiecePresentation());
    }

    if (PanelPresentation)
    {
        Reason.Reset();
        TestTrue(TEXT("Panel-presentation cell configures"), PanelPresentation->ConfigureCell(
            TEXT("TEST_PANEL_PRESENTATION"), LBBodyShopPrototypeIds::PanelPresentation, Reason));
        TestFalse(TEXT("Panel-presentation cell contains no second static stillage"),
            PanelPresentation->HasStaticStillagePresentation());
        TestFalse(TEXT("Panel-presentation fixed art contains no carrier or workpiece WIP"),
            PanelPresentation->HasStaticCarrierOrWorkpiecePresentation());
    }

    if (Underbody)
    {
        TestTrue(TEXT("Underbody cell configures"), Underbody->ConfigureCell(
            TEXT("TEST_UNDERBODY"), LBBodyShopPrototypeIds::UnderbodyFixture, Reason));
        TestTrue(TEXT("Underbody removes the former large black tooling-bed presentation"),
            Underbody->GetMainPresentationAssetPath().IsEmpty());
        TestTrue(TEXT("Underbody presents the skid on the continuous twin-track conveyor"),
            Underbody->HasAutomotiveSkidConveyorPresentation());
        TestEqual(TEXT("Underbody safety assembly has deterministic posts and rails"),
            Underbody->GetAutoAssembledFenceSegmentCount(), 18);
        TestTrue(TEXT("Underbody safety assembly contains no opaque full-height side walls"),
            Underbody->UsesOpenRailSafetyPresentation());
        TestTrue(TEXT("Underbody floor has the isolated painted working-zone presentation"),
            Underbody->HasPaintedUnderbodyWorkZone());
        TestEqual(TEXT("Underbody floor has two Cairnwell-green side pads"),
            Underbody->GetCellFloorWorkingZoneInstanceCount(), 2);
        TestEqual(TEXT("Underbody floor has six yellow perimeter markings with open transfer ends"),
            Underbody->GetCellFloorSafetyMarkingInstanceCount(), 6);
        TestEqual(TEXT("Underbody floor leaves a neutral concrete corridor beneath the skid"),
            Underbody->GetCellFloorNeutralConveyorLaneWidthCm(), 260.0f);
        TestTrue(TEXT("Underbody floor green is exact Cairnwell #1F4B44"),
            Underbody->GetCellFloorWorkingZoneColour().Equals(
                FLinearColor::FromSRGBColor(FColor(0x1F, 0x4B, 0x44, 0xFF))));
        TestTrue(TEXT("Underbody floor boundary is exact Cairnwell safety yellow #F2C300"),
            Underbody->GetCellFloorSafetyMarkingColour().Equals(
                FLinearColor::FromSRGBColor(FColor(0xF2, 0xC3, 0x00, 0xFF))));
        TestFalse(TEXT("Underbody fixture cell does not duplicate runtime-owned skid or workpiece WIP"),
            Underbody->HasStaticCarrierOrWorkpiecePresentation());
        TestTrue(TEXT("Underbody fixture resolves every required semantic material slot"),
            Underbody->HasValidPresentationMaterialContract());
    }

    if (Vision)
    {
        Reason.Reset();
        TestTrue(TEXT("Vision cell configures"), Vision->ConfigureCell(
            TEXT("TEST_VISION"), LBBodyShopPrototypeIds::BasicVisionGate, Reason));
        TestEqual(TEXT("Vision cell uses the dedicated four-scanner gate"),
            Vision->GetMainPresentationAssetPath(),
            FString(TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001.SM_LB_BodyShop_VisionGate_v001")));
        TestTrue(TEXT("Vision gate resolves every required semantic material slot"),
            Vision->HasValidPresentationMaterialContract());
    }

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopAutomaticSkidConveyorDressingTest,
    "LineBoss.BodyShop.Experimental.Presentation.AutomaticSkidConveyorDressing",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopAutomaticSkidConveyorDressingTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBBodyShopAutomaticSkidConveyorDressingTest")));
    if (!TestNotNull(TEXT("Synthetic Body Shop conveyor world exists"), World))
        return false;

    ALBBodyShopCellActor* Fixture = World->SpawnActor<ALBBodyShopCellActor>();
    ALBBodyShopCellActor* Straight = World->SpawnActor<ALBBodyShopCellActor>();
    ALBBodyShopCellActor* Vision = World->SpawnActor<ALBBodyShopCellActor>();
    ALBBodyShopCellActor* Output = World->SpawnActor<ALBBodyShopCellActor>();
    FString Reason;
    TestNotNull(TEXT("Fixture actor spawns"), Fixture);
    TestNotNull(TEXT("Straight conveyor actor spawns"), Straight);
    TestNotNull(TEXT("Vision actor spawns"), Vision);
    TestNotNull(TEXT("Output-buffer actor spawns"), Output);

    if (Fixture)
    {
        TestTrue(TEXT("Fixture configures without presentation regression"),
            Fixture->ConfigureCell(TEXT("TEST_FIXTURE_DRESSING"),
                LBBodyShopPrototypeIds::UnderbodyFixture, Reason));
        TestTrue(TEXT("Fixture continues the same automatic twin-track skid conveyor"),
            Fixture->HasAutomotiveSkidConveyorPresentation());
        TestTrue(TEXT("Fixture has no large opaque tooling-bed mesh"),
            Fixture->GetMainPresentationAssetPath().IsEmpty());
        TestEqual(TEXT("Fixture conveyor spans its full weld-cell transfer length"),
            Fixture->GetSkidConveyorPresentationSpanCm(), 1200.0f);
        TestEqual(TEXT("Fixture conveyor retains the skid's runner gauge"),
            Fixture->GetSkidConveyorTrackGaugeCm(), 180.0f);
        TestEqual(TEXT("Fixture conveyor has deterministic structure instances"),
            Fixture->GetSkidConveyorStructureInstanceCount(), 23);
        TestEqual(TEXT("Fixture conveyor has two continuous rows of powered rollers"),
            Fixture->GetSkidConveyorRollerInstanceCount(), 50);
        TestEqual(TEXT("Fixture conveyor has two open yellow side guides"),
            Fixture->GetSkidConveyorSafetyInstanceCount(), 2);
        TestTrue(TEXT("Fixture carries its derived floor-paint presentation with player placement"),
            Fixture->HasPaintedUnderbodyWorkZone());
        const ULBBodyShopPortComponent* FixtureOutput = Fixture->FindPort(
            LBBodyShopPrototypeIds::SkidOut);
        TestNotNull(TEXT("Fixture retains its canonical skid output"), FixtureOutput);
        if (FixtureOutput)
        {
            TestEqual(TEXT("Fixture output meets the continuous conveyor end"),
                FixtureOutput->GetRelativeLocation().X,
                static_cast<double>(Fixture->GetSkidConveyorPresentationSpanCm()) * 0.5);
        }
        Reason.Reset();
        TestTrue(TEXT("The same actor can be reconfigured away from an underbody cell"),
            Fixture->ConfigureCell(TEXT("TEST_FLOOR_CLEAR"),
                LBBodyShopPrototypeIds::StraightSkidConveyor, Reason));
        TestEqual(TEXT("Non-underbody reconfiguration clears green floor paint"),
            Fixture->GetCellFloorWorkingZoneInstanceCount(), 0);
        TestEqual(TEXT("Non-underbody reconfiguration clears yellow floor paint"),
            Fixture->GetCellFloorSafetyMarkingInstanceCount(), 0);
        TestFalse(TEXT("Non-underbody cell never claims the painted weld-cell contract"),
            Fixture->HasPaintedUnderbodyWorkZone());
    }

    if (Straight)
    {
        Reason.Reset();
        TestTrue(TEXT("Straight conveyor configures"), Straight->ConfigureCell(
            TEXT("TEST_STRAIGHT_CONVEYOR"), LBBodyShopPrototypeIds::StraightSkidConveyor,
            Reason));
        TestTrue(TEXT("Straight cell uses automatic twin-track conveyor dressing"),
            Straight->HasAutomotiveSkidConveyorPresentation());
        TestTrue(TEXT("Straight cell removes the former opaque cube slab"),
            Straight->GetMainPresentationAssetPath().IsEmpty());
        TestEqual(TEXT("Straight dressing spans its connected port pair"),
            Straight->GetSkidConveyorPresentationSpanCm(), 1000.0f);
        TestEqual(TEXT("Tracks match the frozen skid's +/-90 cm runner centres"),
            Straight->GetSkidConveyorTrackGaugeCm(), 180.0f);
        TestEqual(TEXT("Straight dressing has deterministic structure instances"),
            Straight->GetSkidConveyorStructureInstanceCount(), 20);
        TestEqual(TEXT("Straight dressing has two rows of powered rollers"),
            Straight->GetSkidConveyorRollerInstanceCount(), 42);
        TestEqual(TEXT("Straight dressing has two open yellow side guides"),
            Straight->GetSkidConveyorSafetyInstanceCount(), 2);
        const ULBBodyShopPortComponent* Input = Straight->FindPort(
            LBBodyShopPrototypeIds::SkidIn);
        const ULBBodyShopPortComponent* OutputPort = Straight->FindPort(
            LBBodyShopPrototypeIds::SkidOut);
        TestNotNull(TEXT("Straight dressing retains canonical skid input"), Input);
        TestNotNull(TEXT("Straight dressing retains canonical skid output"), OutputPort);
        if (Input && OutputPort)
        {
            TestEqual(TEXT("Straight input meets the dressing start"),
                Input->GetRelativeLocation().X,
                -static_cast<double>(Straight->GetSkidConveyorPresentationSpanCm()) * 0.5);
            TestEqual(TEXT("Straight output meets the dressing end"),
                OutputPort->GetRelativeLocation().X,
                static_cast<double>(Straight->GetSkidConveyorPresentationSpanCm()) * 0.5);
        }
        TestTrue(TEXT("Straight conveyor resolves the v002 structural, steel and safety palette"),
            Straight->HasValidPresentationMaterialContract());
    }

    if (Vision)
    {
        Reason.Reset();
        TestTrue(TEXT("Vision conveyor configures"), Vision->ConfigureCell(
            TEXT("TEST_VISION_CONVEYOR"), LBBodyShopPrototypeIds::BasicVisionGate, Reason));
        TestTrue(TEXT("Vision gate includes the same continuous twin-track dressing"),
            Vision->HasAutomotiveSkidConveyorPresentation());
        TestEqual(TEXT("Vision dressing spans its body ports"),
            Vision->GetSkidConveyorPresentationSpanCm(), 800.0f);
        TestEqual(TEXT("Vision dressing has deterministic structure instances"),
            Vision->GetSkidConveyorStructureInstanceCount(), 17);
        TestEqual(TEXT("Vision dressing has two rows of powered rollers"),
            Vision->GetSkidConveyorRollerInstanceCount(), 34);
        const ULBBodyShopPortComponent* Input = Vision->FindPort(
            LBBodyShopPrototypeIds::BodyIn);
        const ULBBodyShopPortComponent* OutputPort = Vision->FindPort(
            LBBodyShopPrototypeIds::BodyOut);
        TestNotNull(TEXT("Vision dressing retains canonical body input"), Input);
        TestNotNull(TEXT("Vision dressing retains canonical body output"), OutputPort);
        if (Input && OutputPort)
        {
            TestEqual(TEXT("Vision input meets the dressing start"),
                Input->GetRelativeLocation().X,
                -static_cast<double>(Vision->GetSkidConveyorPresentationSpanCm()) * 0.5);
            TestEqual(TEXT("Vision output meets the dressing end"),
                OutputPort->GetRelativeLocation().X,
                static_cast<double>(Vision->GetSkidConveyorPresentationSpanCm()) * 0.5);
        }
        TestEqual(TEXT("Vision gate retains its dedicated main art"),
            Vision->GetMainPresentationAssetPath(),
            FString(TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001.SM_LB_BodyShop_VisionGate_v001")));
    }

    if (Output)
    {
        Reason.Reset();
        TestTrue(TEXT("Output buffer configures"), Output->ConfigureCell(
            TEXT("TEST_OUTPUT_CONVEYOR"), LBBodyShopPrototypeIds::OutputBuffer, Reason));
        TestTrue(TEXT("Output uses automatic twin-track buffer dressing"),
            Output->HasAutomotiveSkidConveyorPresentation());
        TestTrue(TEXT("Output removes the former opaque cube slab"),
            Output->GetMainPresentationAssetPath().IsEmpty());
        TestEqual(TEXT("Output dressing continues from the vision port"),
            Output->GetSkidConveyorPresentationSpanCm(), 1000.0f);
        TestEqual(TEXT("Output buffer adds guides plus a three-piece positive end stop"),
            Output->GetSkidConveyorSafetyInstanceCount(), 5);
        const ULBBodyShopPortComponent* Input = Output->FindPort(
            LBBodyShopPrototypeIds::BodyIn);
        TestNotNull(TEXT("Output dressing retains canonical body input"), Input);
        if (Input)
        {
            TestEqual(TEXT("Output input meets the dressing start"),
                Input->GetRelativeLocation().X,
                -static_cast<double>(Output->GetSkidConveyorPresentationSpanCm()) * 0.5);
        }
        const FLBBodyShopPlacedCellSaveState State = Output->CaptureSaveState();
        TestEqual(TEXT("Presentation dressing preserves the canonical saved definition identity"),
            State.DefinitionId, LBBodyShopPrototypeIds::OutputBuffer);
    }

    World->DestroyWorld(false);
    return true;
}

#endif
