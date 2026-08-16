#include "LBBodyWeldLineActor.h"

#include "LBFactoryFloorMarkingComponent.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBStatusBeaconComponent.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace LBBodyWeldTests
{
    const FName OrderId(TEXT("ORDER-CAIRNWELL-001"));

    FString SerialFor(const int32 Value)
    {
        return FString::Printf(TEXT("%06d"), Value);
    }

    FName MakePanelId(const FName Family, const int32 Serial)
    {
        return FName(*FString::Printf(TEXT("PTA-PANEL-CAIRNWELL_2040-%s-%s"),
            *Family.ToString(), *SerialFor(Serial)));
    }

    FLBBodyWeldStillageInventory MakeStillage(const FName Family, const int32 Serial,
        const int64 DeliverySequence, const FName InOrderId = OrderId)
    {
        FLBBodyWeldStillageInventory Stillage;
        Stillage.StillageId = FName(*FString::Printf(TEXT("STILLAGE-%s-%03d"),
            *Family.ToString(), Serial));
        Stillage.OrderId = InOrderId;
        Stillage.VehicleModelId = TEXT("CAIRNWELL_2040");
        Stillage.PanelTypeId = Family;
        Stillage.DeliverySequence = DeliverySequence;
        Stillage.CapacityPanels = 1;
        FLBBodyWeldPanelUnit& Panel = Stillage.PanelUnits.AddDefaulted_GetRef();
        Panel.PanelId = MakePanelId(Family, Serial);
        Panel.OrderId = InOrderId;
        Panel.VehicleModelId = Stillage.VehicleModelId;
        Panel.PanelTypeId = Family;
        Panel.StillageId = Stillage.StillageId;
        return Stillage;
    }

    FLBBodyWeldBaseKitUnit MakeBaseKit(const int32 Serial, const int64 DeliverySequence,
        const FName InOrderId = OrderId)
    {
        FLBBodyWeldBaseKitUnit Kit;
        Kit.KitId = FName(*FString::Printf(TEXT("BIW-BASE-KIT-%06d"), Serial));
        Kit.OrderId = InOrderId;
        Kit.DeliverySequence = DeliverySequence;
        return Kit;
    }

    bool FeedRecipe(ALBBodyWeldLineActor* Line, const bool bAddBaseKit = true,
        const FName OmitFamily = NAME_None, const int32 SerialOffset = 0)
    {
        if (!Line) return false;
        FString Reason;
        int32 Serial = 1 + SerialOffset;
        for (const FName Family : ALBBodyWeldLineActor::GetRequiredPanelFamilies())
        {
            if (Family == OmitFamily)
            {
                ++Serial;
                continue;
            }
            if (!Line->ReceivePanelStillage(MakeStillage(Family, Serial, Serial), Reason)) return false;
            ++Serial;
        }
        return !bAddBaseKit || Line->ReceiveBaseKit(MakeBaseKit(1 + SerialOffset, 1), Reason);
    }

    ALBBodyWeldLineActor* SpawnLine(UWorld*& OutWorld, const TCHAR* WorldName,
        const FName LineId = TEXT("WL-TEST-001"))
    {
        OutWorld = UWorld::CreateWorld(EWorldType::Game, false, FName(WorldName));
        ALBBodyWeldLineActor* Line = OutWorld
            ? OutWorld->SpawnActor<ALBBodyWeldLineActor>() : nullptr;
        if (!Line) return nullptr;
        return LineId.IsNone() || Line->Configure(LineId) ? Line : nullptr;
    }

    const FLBBodyWeldPanelLineage* FindReservedFamily(
        const FLBBodyWeldInputReservation& Reservation, const FName Family)
    {
        return Reservation.Panels.FindByPredicate([Family](const FLBBodyWeldPanelLineage& Panel)
            { return Panel.PanelTypeId == Family; });
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyWeldRecipeAndPortContractTest,
    "LineBoss.BodyWeld.Runtime.RecipePortsAndProxyContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyWeldRecipeAndPortContractTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    ALBBodyWeldLineActor* Line = LBBodyWeldTests::SpawnLine(World, TEXT("LB_Weld_Contract"));
    TestNotNull(TEXT("Body Weld Line spawns as an isolated runtime authority"), Line);
    if (!World || !Line)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    const TArray<FName> Families = ALBBodyWeldLineActor::GetRequiredPanelFamilies();
    TestEqual(TEXT("Cairnwell recipe contains exactly eleven panel families"), Families.Num(), 11);
    TSet<FName> UniqueFamilies;
    for (const FName Family : Families) UniqueFamilies.Add(Family);
    TestEqual(TEXT("Every recipe family is unique"), UniqueFamilies.Num(), 11);
    TestEqual(TEXT("Finite base kit has a stable explicit identity"),
        ALBBodyWeldLineActor::GetBaseKitTypeId(), FName(TEXT("CAIRNWELL_2040_BIW_BASE_KIT")));

    TestTrue(TEXT("Full stillage intake preserves stage-10 Stillage/AGVHandoff contract"),
        Line->GetStillageInputPort()
        && Line->GetStillageInputPort()->ProcessStage == LBFactoryProcessStage::BodyWeld
        && Line->GetStillageInputPort()->Direction == ELBFactoryPortDirection::Input
        && Line->GetStillageInputPort()->MaterialClass == ELBFactoryMaterialClass::Stillage
        && Line->GetStillageInputPort()->TransportKind == ELBFactoryTransportKind::AGVHandoff);
    TestTrue(TEXT("Finite-kit input uses existing GeneralParts only as compatibility contract"),
        Line->GetBaseKitInputPort()
        && Line->GetBaseKitInputPort()->ProcessStage == LBFactoryProcessStage::BodyWeld
        && Line->GetBaseKitInputPort()->MaterialClass == ELBFactoryMaterialClass::GeneralParts
        && Line->GetBaseKitInputPort()->TransportKind == ELBFactoryTransportKind::AGVHandoff);
    TestTrue(TEXT("BIW output preserves stage-10 BodyInWhite/PanelTransfer contract"),
        Line->GetBIWOutputPort()
        && Line->GetBIWOutputPort()->ProcessStage == LBFactoryProcessStage::BodyWeld
        && Line->GetBIWOutputPort()->Direction == ELBFactoryPortDirection::Output
        && Line->GetBIWOutputPort()->MaterialClass == ELBFactoryMaterialClass::BodyInWhite
        && Line->GetBIWOutputPort()->TransportKind == ELBFactoryTransportKind::PanelTransfer);
    TestTrue(TEXT("Authored cell is readable and protected without becoming a navigation wall"),
        Line->GetProxyPartCount() == 9 && Line->GetProtectedEnvelope()
        && Line->GetProtectedEnvelope()->GetCollisionEnabled() == ECollisionEnabled::QueryOnly
        && !Line->GetProtectedEnvelope()->CanEverAffectNavigation()
        && Line->GetFloorMarkings() && Line->GetFloorMarkings()->HasNonCollidingPresentation());
    TestTrue(TEXT("Validated modular fixture, skid and lower-underbody assets all resolve"),
        Line->HasResolvedRuntimeArt());
    if (Line->HasResolvedRuntimeArt())
    {
        UStaticMeshComponent* Fixture = Line->GetFramingFixturePresentation();
        UStaticMeshComponent* Skid = Line->GetBaseKitSkidPresentation();
        UStaticMeshComponent* Underbody = Line->GetBaseKitUnderbodyPresentation();
        UStaticMesh* FixtureMesh = Fixture ? Fixture->GetStaticMesh() : nullptr;
        UStaticMesh* SkidMesh = Skid ? Skid->GetStaticMesh() : nullptr;
        UStaticMesh* UnderbodyMesh = Underbody ? Underbody->GetStaticMesh() : nullptr;
        TestTrue(TEXT("Skid and lower underbody remain genuinely separate runtime meshes"),
            FixtureMesh && SkidMesh && UnderbodyMesh
            && FixtureMesh != SkidMesh && FixtureMesh != UnderbodyMesh
            && SkidMesh != UnderbodyMesh);
        const FVector FixtureSize = FixtureMesh ? FixtureMesh->GetBounds().BoxExtent * 2.0f
            : FVector::ZeroVector;
        const FVector SkidSize = SkidMesh ? SkidMesh->GetBounds().BoxExtent * 2.0f
            : FVector::ZeroVector;
        const FVector UnderbodySize = UnderbodyMesh
            ? UnderbodyMesh->GetBounds().BoxExtent * 2.0f : FVector::ZeroVector;
        TestTrue(TEXT("Imported art keeps its validated centimetre-scale bounds"),
            FixtureSize.Equals(FVector(622.0f, 576.0f, 404.0f), 3.0f)
            && SkidSize.Equals(FVector(560.0f, 212.0f, 65.0f), 3.0f)
            && UnderbodySize.Equals(FVector(482.0f, 191.0f, 82.4446f), 3.0f));
        TestTrue(TEXT("Runtime art is presentation-only and cannot become a navigation wall"),
            Fixture->GetCollisionEnabled() == ECollisionEnabled::NoCollision
            && Skid->GetCollisionEnabled() == ECollisionEnabled::NoCollision
            && Underbody->GetCollisionEnabled() == ECollisionEnabled::NoCollision
            && !Fixture->CanEverAffectNavigation() && !Skid->CanEverAffectNavigation()
            && !Underbody->CanEverAffectNavigation());
        const auto HasSemanticColourMaterials = [](const UStaticMeshComponent* Component)
        {
            if (!Component || Component->GetNumMaterials() <= 0) return false;
            for (int32 Slot = 0; Slot < Component->GetNumMaterials(); ++Slot)
            {
                if (!Cast<UMaterialInstanceDynamic>(Component->GetMaterial(Slot))) return false;
            }
            return true;
        };
        TestTrue(TEXT("Every imported semantic slot receives a clean bright runtime material"),
            HasSemanticColourMaterials(Fixture) && HasSemanticColourMaterials(Skid)
            && HasSemanticColourMaterials(Underbody));
    }
    TestFalse(TEXT("Finite base-kit workpiece is not scenery before exact consumption"),
        Line->IsBaseKitWorkpiecePresented());

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyWeldRobotRuntimeArtFallbackTest,
    "LineBoss.BodyWeld.Presentation.WeldRobotRuntimeArtAtomicFallback",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyWeldRobotRuntimeArtFallbackTest::RunTest(const FString& Parameters)
{
    const FSoftObjectPath SharedBasePath(TEXT(
        "/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/SharedBase/"
        "SM_LB_WeldRobot_SharedBase_v001.SM_LB_WeldRobot_SharedBase_v001"));
    const FSoftObjectPath MIGToolPath(TEXT(
        "/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/MIG/"
        "SM_LB_WeldTool_MIG_v001.SM_LB_WeldTool_MIG_v001"));
    const FSoftObjectPath SpotToolPath(TEXT(
        "/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/SpotGun/"
        "SM_LB_WeldTool_SpotGun_v001.SM_LB_WeldTool_SpotGun_v001"));
    const FSoftObjectPath PanelPickToolPath(TEXT(
        "/Game/LineBoss/Candidates/WeldShop/Robots/WeldRobotRuntime_v001/Tools/PanelPick/"
        "SM_LB_WeldTool_PanelPick_v001.SM_LB_WeldTool_PanelPick_v001"));

    UWorld* World = nullptr;
    ALBBodyWeldLineActor* Line = LBBodyWeldTests::SpawnLine(
        World, TEXT("LB_Weld_Robot_Runtime_Art"), TEXT("WL-ROBOT-ART-001"));
    TestNotNull(TEXT("Body Weld robot-art test line spawns"), Line);
    if (!World || !Line)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    const TArray<FString> Paths = Line->GetRobotRuntimeArtPaths();
    TestTrue(TEXT("Guarded resolver exposes the four exact promoted soft paths in stable order"),
        Paths.Num() == 4
        && Paths[0] == SharedBasePath.ToString()
        && Paths[1] == MIGToolPath.ToString()
        && Paths[2] == SpotToolPath.ToString()
        && Paths[3] == PanelPickToolPath.ToString());
    TestTrue(TEXT("The fixed visual family is explicitly static-pose only"),
        Line->IsRobotRuntimeArtStaticPoseOnly());
    TestTrue(TEXT("All four complete base/tool pairs resolve and suppress exactly twelve cubes"),
        Line->GetRobotStationCount() == 4
        && Line->GetResolvedRobotStationCount() == 4
        && Line->GetFallbackRobotStationCount() == 0
        && Line->GetImportedRobotPartCount() == 8
        && Line->GetRobotProxyPartCount() == 0
        && Line->HasResolvedRobotRuntimeArt());

    const TArray<FName> ExpectedRoles = {
        TEXT("PANEL_PICK"), TEXT("SPOT"), TEXT("SPOT"), TEXT("MIG")
    };
    const TArray<FVector> ExpectedRoots = {
        FVector(1700.0f, -500.0f, 0.0f), FVector(2800.0f, 500.0f, 0.0f),
        FVector(3300.0f, -500.0f, 0.0f), FVector(3900.0f, 500.0f, 0.0f)
    };
    const FVector ExpectedFlange(-38.9165f, -9.4918f, 137.6317f);
    TestTrue(TEXT("Tool flange remains the exact visually approved fixed-pose translation"),
        Line->GetRobotToolFlangeRelativeLocation().Equals(ExpectedFlange, 0.0001f));

    UStaticMesh* SharedBaseMesh = nullptr;
    for (int32 StationIndex = 0; StationIndex < Line->GetRobotStationCount(); ++StationIndex)
    {
        UStaticMeshComponent* Base = Line->GetRobotBasePresentation(StationIndex);
        UStaticMeshComponent* Tool = Line->GetRobotToolPresentation(StationIndex);
        TestTrue(*FString::Printf(TEXT("Station %d owns one complete exact-role pair"), StationIndex),
            Base && Tool && Base->GetStaticMesh() && Tool->GetStaticMesh()
            && Line->GetRobotStationToolRole(StationIndex) == ExpectedRoles[StationIndex]);
        if (!Base || !Tool || !Base->GetStaticMesh() || !Tool->GetStaticMesh()) continue;

        if (!SharedBaseMesh) SharedBaseMesh = Base->GetStaticMesh();
        TestTrue(*FString::Printf(TEXT("Station %d reuses the one validated shared base"), StationIndex),
            Base->GetStaticMesh() == SharedBaseMesh);
        TestTrue(*FString::Printf(TEXT("Station %d preserves fixed root and flange transforms"), StationIndex),
            Base->GetRelativeLocation().Equals(ExpectedRoots[StationIndex], 0.0001f)
            && Base->GetAttachParent() == Line->GetRootComponent()
            && Tool->GetAttachParent() == Base
            && Tool->GetRelativeLocation().Equals(ExpectedFlange, 0.0001f)
            && Base->GetRelativeRotation().Equals(FRotator::ZeroRotator, 0.0001f)
            && Tool->GetRelativeRotation().Equals(FRotator::ZeroRotator, 0.0001f)
            && Base->Mobility == EComponentMobility::Movable
            && Tool->Mobility == EComponentMobility::Movable);
        TestTrue(*FString::Printf(TEXT("Station %d cannot collide, overlap, simulate, or affect navigation"), StationIndex),
            Base->GetCollisionEnabled() == ECollisionEnabled::NoCollision
            && Tool->GetCollisionEnabled() == ECollisionEnabled::NoCollision
            && !Base->GetGenerateOverlapEvents() && !Tool->GetGenerateOverlapEvents()
            && !Base->IsSimulatingPhysics() && !Tool->IsSimulatingPhysics()
            && !Base->CanEverAffectNavigation() && !Tool->CanEverAffectNavigation());

        const auto UsesExactImportedMaterials = [](const UStaticMeshComponent* Component)
        {
            const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
            if (!Mesh || Component->GetNumMaterials() != Mesh->GetStaticMaterials().Num()
                || Component->GetNumMaterials() <= 0) return false;
            for (int32 Slot = 0; Slot < Component->GetNumMaterials(); ++Slot)
            {
                if (!Component->GetMaterial(Slot)
                    || Component->GetMaterial(Slot) != Mesh->GetMaterial(Slot)
                    || Cast<UMaterialInstanceDynamic>(Component->GetMaterial(Slot))) return false;
            }
            return true;
        };
        TestTrue(*FString::Printf(TEXT("Station %d keeps exact interim source materials without runtime repaint"), StationIndex),
            UsesExactImportedMaterials(Base) && UsesExactImportedMaterials(Tool));
    }
    if (SharedBaseMesh)
    {
        const FVector BaseSize = SharedBaseMesh->GetBounds().BoxExtent * 2.0f;
        TestTrue(TEXT("Shared base keeps its validated centimetre-scale bounds"),
            BaseSize.Equals(FVector(90.1776f, 66.1541f, 186.3424f), 2.0f));
    }

    UBoxComponent* EnvelopeBefore = Line->GetProtectedEnvelope();
    ULBFactoryProcessPortComponent* StillagePortBefore = Line->GetStillageInputPort();
    ULBFactoryProcessPortComponent* BaseKitPortBefore = Line->GetBaseKitInputPort();
    ULBFactoryProcessPortComponent* OutputPortBefore = Line->GetBIWOutputPort();
    const FLBBodyWeldLineSaveState StateBefore = Line->CaptureSaveState();

    // Missing pick art must restore only the corresponding triplet; both spot stations
    // and the MIG station remain complete. No missing-object load is attempted.
    Line->SetRobotRuntimeArtReferencesForTests(
        SharedBasePath, MIGToolPath, SpotToolPath, FSoftObjectPath());
    TestTrue(TEXT("One missing role fails closed for only its complete-pair station"),
        Line->GetResolvedRobotStationCount() == 3
        && Line->GetFallbackRobotStationCount() == 1
        && Line->GetImportedRobotPartCount() == 6
        && Line->GetRobotProxyPartCount() == 3
        && !Line->HasResolvedRobotRuntimeArt()
        && Line->GetRobotBasePresentation(0)
        && !Line->GetRobotBasePresentation(0)->GetStaticMesh()
        && Line->GetRobotToolPresentation(0)
        && !Line->GetRobotToolPresentation(0)->GetStaticMesh());
    TestTrue(TEXT("Unrelated exact role pairs remain resolved after one-role failure"),
        Line->GetRobotBasePresentation(1)->GetStaticMesh()
        && Line->GetRobotToolPresentation(1)->GetStaticMesh()
        && Line->GetRobotBasePresentation(2)->GetStaticMesh()
        && Line->GetRobotToolPresentation(2)->GetStaticMesh()
        && Line->GetRobotBasePresentation(3)->GetStaticMesh()
        && Line->GetRobotToolPresentation(3)->GetStaticMesh());

    Line->SetRobotRuntimeArtReferencesForTests(
        FSoftObjectPath(), MIGToolPath, SpotToolPath, PanelPickToolPath);
    TestTrue(TEXT("Missing shared base fails closed to all four legacy robot triplets"),
        Line->GetResolvedRobotStationCount() == 0
        && Line->GetFallbackRobotStationCount() == 4
        && Line->GetImportedRobotPartCount() == 0
        && Line->GetRobotProxyPartCount() == 12
        && !Line->HasResolvedRobotRuntimeArt());

    const FLBBodyWeldLineSaveState StateAfter = Line->CaptureSaveState();
    TestTrue(TEXT("Presentation fallback cannot mutate ports, envelope, gameplay, or save state"),
        Line->GetProtectedEnvelope() == EnvelopeBefore
        && Line->GetStillageInputPort() == StillagePortBefore
        && Line->GetBaseKitInputPort() == BaseKitPortBefore
        && Line->GetBIWOutputPort() == OutputPortBefore
        && StateAfter.LineId == StateBefore.LineId
        && StateAfter.Phase == StateBefore.Phase
        && FMath::IsNearlyEqual(StateAfter.PhaseProgress01, StateBefore.PhaseProgress01)
        && StateAfter.Stillages.Num() == StateBefore.Stillages.Num()
        && StateAfter.BaseKits.Num() == StateBefore.BaseKits.Num()
        && StateAfter.PendingEmptyReturns.Num() == StateBefore.PendingEmptyReturns.Num()
        && StateAfter.NextReservationSerial == StateBefore.NextReservationSerial
        && StateAfter.NextBodySerial == StateBefore.NextBodySerial
        && StateAfter.NextEventSequence == StateBefore.NextEventSequence);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyWeldAtomicReservationTest,
    "LineBoss.BodyWeld.Runtime.AtomicReservationSelectionAndRollback",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyWeldAtomicReservationTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    ALBBodyWeldLineActor* Line = LBBodyWeldTests::SpawnLine(World, TEXT("LB_Weld_Reservation"));
    if (!World || !Line) return false;
    TestTrue(TEXT("Order assignment succeeds"), Line->SetAssignedOrder(LBBodyWeldTests::OrderId));
    TestTrue(TEXT("Incomplete exact recipe can be received"),
        LBBodyWeldTests::FeedRecipe(Line, true, TEXT("FENDER_FRONT_RIGHT")));
    const int32 AvailableBefore = Line->GetAvailablePanelCount();
    const int32 KitsBefore = Line->GetAvailableBaseKitCount();
    FString Reason;
    TestFalse(TEXT("One missing family prevents all reservation mutation"), Line->TryReserveRecipe(Reason));
    TestTrue(TEXT("Starvation reason names the exact missing identity"),
        Reason.Contains(TEXT("FENDER_FRONT_RIGHT"))
        && Line->GetOperatingState() == ELBFactoryMachineOperatingState::Starved);
    TestTrue(TEXT("Failed transaction leaves panels, kits and reservation untouched"),
        Line->GetAvailablePanelCount() == AvailableBefore && Line->GetReservedPanelCount() == 0
        && Line->GetAvailableBaseKitCount() == KitsBefore);
    FLBBodyWeldInputReservation Reservation;
    TestFalse(TEXT("No partial reservation record leaks from failure"),
        Line->GetActiveReservation(Reservation));

    TestTrue(TEXT("Missing family can be delivered without rewriting prior stock"),
        Line->ReceivePanelStillage(LBBodyWeldTests::MakeStillage(
            TEXT("FENDER_FRONT_RIGHT"), 99, 99), Reason));
    // Three roof candidates prove stable selection: delivery sequence first, then ID.
    TestTrue(TEXT("Later roof candidate is accepted"), Line->ReceivePanelStillage(
        LBBodyWeldTests::MakeStillage(TEXT("ROOF_PANEL"), 900, 5), Reason));
    TestTrue(TEXT("Lexically smaller candidate at same delivery sequence is accepted"),
        Line->ReceivePanelStillage(LBBodyWeldTests::MakeStillage(TEXT("ROOF_PANEL"), 800, 5), Reason));
    FLBBodyWeldStillageInventory Earliest = LBBodyWeldTests::MakeStillage(TEXT("ROOF_PANEL"), 999, 0);
    TestTrue(TEXT("Earliest delivery candidate is accepted"), Line->ReceivePanelStillage(Earliest, Reason));
    TestTrue(TEXT("Complete recipe reserves as one transaction"), Line->TryReserveRecipe(Reason));
    TestTrue(TEXT("Reservation contains all and only eleven families"),
        Line->GetActiveReservation(Reservation) && Reservation.Panels.Num() == 11
        && Line->GetReservedPanelCount() == 11 && Line->GetAvailableBaseKitCount() == 0);
    const FLBBodyWeldPanelLineage* Roof =
        LBBodyWeldTests::FindReservedFamily(Reservation, TEXT("ROOF_PANEL"));
    TestTrue(TEXT("Stable selection uses earliest delivery before lexical panel ID"),
        Roof && Roof->PanelId == Earliest.PanelUnits[0].PanelId
        && Roof->StillageId == Earliest.StillageId);

    // Malformed, wrong-program and duplicate payloads are rejected before mutation.
    FLBBodyWeldStillageInventory Invalid = LBBodyWeldTests::MakeStillage(TEXT("HOOD_PANEL"), 777, 777);
    Invalid.PanelUnits[0].PanelId = TEXT("MALFORMED-PANEL");
    const int32 TotalBeforeInvalid = Line->GetAvailablePanelCount() + Line->GetReservedPanelCount();
    TestFalse(TEXT("Malformed exact panel ID is rejected"), Line->ReceivePanelStillage(Invalid, Reason));
    TestEqual(TEXT("Rejected payload cannot mutate inventory"),
        Line->GetAvailablePanelCount() + Line->GetReservedPanelCount(), TotalBeforeInvalid);

    FLBBodyWeldStillageInventory WrongVehicle =
        LBBodyWeldTests::MakeStillage(TEXT("HOOD_PANEL"), 778, 778);
    WrongVehicle.VehicleModelId = TEXT("OTHER_VEHICLE");
    WrongVehicle.PanelUnits[0].VehicleModelId = WrongVehicle.VehicleModelId;
    TestFalse(TEXT("Wrong vehicle program is rejected even when the payload is self-consistent"),
        Line->ReceivePanelStillage(WrongVehicle, Reason));
    TestEqual(TEXT("Wrong-program rejection is also non-mutating"),
        Line->GetAvailablePanelCount() + Line->GetReservedPanelCount(), TotalBeforeInvalid);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyWeldCycleLineageAndAckTest,
    "LineBoss.BodyWeld.Runtime.DeterministicCycleLineageEmptyReturnsAndEDAck",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyWeldCycleLineageAndAckTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    ALBBodyWeldLineActor* Line = LBBodyWeldTests::SpawnLine(World,
        TEXT("LB_Weld_Cycle"), TEXT("WL-DETERMINISTIC-A"));
    if (!World || !Line) return false;
    TestTrue(TEXT("Order and complete finite recipe are accepted"),
        Line->SetAssignedOrder(LBBodyWeldTests::OrderId)
        && LBBodyWeldTests::FeedRecipe(Line));
    FString CommitReason;
    TestTrue(TEXT("Exact recipe reserves before the visible workpiece enters the fixture"),
        Line->TryReserveRecipe(CommitReason));
    TestFalse(TEXT("Reserved-but-unconsumed stock is not displayed as production WIP"),
        Line->IsBaseKitWorkpiecePresented());
    TestTrue(TEXT("Committed exact inputs reveal the separate skid and lower underbody"),
        Line->CommitReservedInputs(CommitReason)
        && Line->IsBaseKitWorkpiecePresented());
    if (USceneComponent* WorkpieceRoot = Line->GetBaseKitSkidPresentation()
        ? Line->GetBaseKitSkidPresentation()->GetAttachParent() : nullptr)
    {
        TestTrue(TEXT("Committed workpiece occupies the framing fixture datum"),
            WorkpieceRoot->GetRelativeLocation().Equals(FVector(2700.0f, 0.0f, 0.0f), 0.1f));
    }

    // One large deterministic step must equal the authored 5+6+8+3 second sequence.
    Line->AdvanceSimulation(22.0f);
    FLBBodyInWhiteRecord Body;
    TestTrue(TEXT("Large step consumes every bounded phase remainder and creates one good BIW"),
        Line->GetOutputBody(Body) && Body.QualityState == ELBBodyWeldQualityState::Good
        && Body.BodyId == TEXT("BIW-CAIRNWELL_2040-WL-DETERMINISTIC-A-000001")
        && Body.Panels.Num() == 11 && Body.OrderId == LBBodyWeldTests::OrderId
        && Body.BaseKitId == TEXT("BIW-BASE-KIT-000001") && !Body.bEDAccepted);
    if (USceneComponent* WorkpieceRoot = Line->GetBaseKitSkidPresentation()
        ? Line->GetBaseKitSkidPresentation()->GetAttachParent() : nullptr)
    {
        TestTrue(TEXT("Completed lower structure moves to the exact BIW output position"),
            Line->IsBaseKitWorkpiecePresented()
            && WorkpieceRoot->GetRelativeLocation().Equals(
                FVector(4750.0f, 0.0f, 0.0f), 0.1f));
    }
    TestTrue(TEXT("Cycle evidence retains exact deterministic authored phase time"),
        FMath::IsNearlyEqual(Body.CycleEvidence.ClosurePreparationSeconds, 5.0f)
        && FMath::IsNearlyEqual(Body.CycleEvidence.FramingSeconds, 6.0f)
        && FMath::IsNearlyEqual(Body.CycleEvidence.WeldingSeconds, 8.0f)
        && FMath::IsNearlyEqual(Body.CycleEvidence.GeometryCheckSeconds, 3.0f));
    TestEqual(TEXT("Each now-empty one-panel stillage queues its same identity exactly once"),
        Line->GetPendingEmptyReturnCount(), 11);
    TSet<FName> ReturnedIds;
    FLBBodyWeldEmptyStillageReturn EmptyReturn;
    while (Line->PopEmptyStillageReturn(EmptyReturn)) ReturnedIds.Add(EmptyReturn.StillageId);
    TestTrue(TEXT("No substitute or duplicate empty container is emitted"),
        ReturnedIds.Num() == 11 && ReturnedIds.Contains(TEXT("STILLAGE-ROOF_PANEL-001")));

    Line->AdvanceSimulation(100.0f);
    FLBBodyInWhiteRecord Preserved;
    TestTrue(TEXT("Full one-slot output blocks without deleting or replacing the exact BIW"),
        Line->GetOutputBody(Preserved) && Preserved.BodyId == Body.BodyId
        && Line->GetOperatingState() == ELBFactoryMachineOperatingState::Blocked);
    FLBBodyInWhiteRecord Transferred;
    TestFalse(TEXT("Unavailable ED cannot acknowledge or remove the body"),
        Line->AcknowledgeEDTransfer(Body.BodyId, Transferred));
    TestTrue(TEXT("Failed acknowledgement preserves exact output"),
        Line->GetOutputBody(Preserved) && Preserved.BodyId == Body.BodyId);
    Line->SetEDAvailable(true);
    TestTrue(TEXT("Compatible ED acknowledges the same body identity once"),
        Line->AcknowledgeEDTransfer(Body.BodyId, Transferred)
        && Transferred.BodyId == Body.BodyId && Transferred.bEDAccepted
        && Line->GetCompletedBodyCount() == 1);
    TestFalse(TEXT("Same BIW cannot acknowledge twice"),
        Line->AcknowledgeEDTransfer(Body.BodyId, Transferred));
    TestFalse(TEXT("Transferred body is no longer present in weld output"), Line->GetOutputBody(Preserved));
    TestFalse(TEXT("ED acknowledgement removes the weld-owned workpiece presentation"),
        Line->IsBaseKitWorkpiecePresented());

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyWeldEmptyReturnCapacityRollbackTest,
    "LineBoss.BodyWeld.Runtime.EmptyReturnCapacityRollbackIsAtomic",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyWeldEmptyReturnCapacityRollbackTest::RunTest(const FString& Parameters)
{
    UWorld* World = nullptr;
    ALBBodyWeldLineActor* Line = LBBodyWeldTests::SpawnLine(World,
        TEXT("LB_Weld_Return_Capacity"), TEXT("WL-RETURN-CAPACITY"));
    if (!World || !Line) return false;
    TestTrue(TEXT("Overflow fixture starts with an assigned Cairnwell order"),
        Line->SetAssignedOrder(LBBodyWeldTests::OrderId));
    Line->SetEDAvailable(true);

    FLBBodyInWhiteRecord Transferred;
    for (int32 Batch = 0; Batch < 2; ++Batch)
    {
        TestTrue(TEXT("A complete batch is received before the capacity boundary"),
            LBBodyWeldTests::FeedRecipe(Line, true, NAME_None, Batch * 100));
        Line->AdvanceSimulation(22.0f);
        FLBBodyInWhiteRecord Output;
        TestTrue(TEXT("Capacity fixture creates an exact good BIW"), Line->GetOutputBody(Output));
        TestTrue(TEXT("Completed capacity-fixture BIW is acknowledged exactly once"),
            Line->AcknowledgeEDTransfer(Output.BodyId, Transferred));
    }
    TestEqual(TEXT("Two uncollected batches retain twenty-two exact empty returns"),
        Line->GetPendingEmptyReturnCount(), 22);

    TestTrue(TEXT("Third complete batch can be received and atomically reserved"),
        LBBodyWeldTests::FeedRecipe(Line, true, NAME_None, 200));
    FString Reason;
    TestTrue(TEXT("Third recipe reserves before return-capacity preflight"),
        Line->TryReserveRecipe(Reason));
    FLBBodyWeldInputReservation Before;
    TestTrue(TEXT("Preflight fixture holds all eleven exact reserved inputs"),
        Line->GetActiveReservation(Before) && !Before.bConsumptionCommitted
        && Before.Panels.Num() == 11 && Line->GetReservedPanelCount() == 11);
    const FLBBodyWeldLineSaveState BeforeState = Line->CaptureSaveState();

    TestFalse(TEXT("Commit refuses eleven more returns when only ten queue slots remain"),
        Line->CommitReservedInputs(Reason));
    FLBBodyWeldInputReservation After;
    const FLBBodyWeldLineSaveState AfterState = Line->CaptureSaveState();
    TestTrue(TEXT("Capacity failure reports the actionable empty-return reason"),
        Reason.Contains(TEXT("Empty-stillage return queue")));
    TestTrue(TEXT("Capacity failure consumes no panel, kit, reservation, ID, or queue sequence"),
        Line->GetActiveReservation(After) && !After.bConsumptionCommitted
        && After.ReservationId == Before.ReservationId && After.Panels.Num() == Before.Panels.Num()
        && Line->GetReservedPanelCount() == 11 && Line->GetPendingEmptyReturnCount() == 22
        && AfterState.NextReservationSerial == BeforeState.NextReservationSerial
        && AfterState.NextBodySerial == BeforeState.NextBodySerial
        && AfterState.NextEventSequence == BeforeState.NextEventSequence);
    TestTrue(TEXT("Failed capacity commit remains a valid, recoverable save contract"),
        ALBBodyWeldLineActor::IsSaveStateContractValid(AfterState));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyWeldPauseQualityAndStepEquivalenceTest,
    "LineBoss.BodyWeld.Runtime.HoldsDeterministicQualityAndStepEquivalence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyWeldPauseQualityAndStepEquivalenceTest::RunTest(const FString& Parameters)
{
    UWorld* WorldA = nullptr;
    UWorld* WorldB = nullptr;
    ALBBodyWeldLineActor* LineA = LBBodyWeldTests::SpawnLine(WorldA,
        TEXT("LB_Weld_Step_A"), TEXT("WL-STEP-EQUIVALENT"));
    ALBBodyWeldLineActor* LineB = LBBodyWeldTests::SpawnLine(WorldB,
        TEXT("LB_Weld_Step_B"), TEXT("WL-STEP-EQUIVALENT"));
    if (!WorldA || !WorldB || !LineA || !LineB) return false;
    TestTrue(TEXT("Both deterministic lines receive identical recipes"),
        LineA->SetAssignedOrder(LBBodyWeldTests::OrderId) && LBBodyWeldTests::FeedRecipe(LineA)
        && LineB->SetAssignedOrder(LBBodyWeldTests::OrderId) && LBBodyWeldTests::FeedRecipe(LineB));

    LineA->AdvanceSimulation(4.0f);
    const ELBBodyWeldPhase HeldPhase = LineA->GetPhase();
    const float HeldProgress = LineA->GetPhaseProgress01();
    LineA->SetPaused(true);
    LineA->AdvanceSimulation(100.0f);
    TestTrue(TEXT("Paused line advances neither phase nor progress"),
        LineA->GetPhase() == HeldPhase && FMath::IsNearlyEqual(LineA->GetPhaseProgress01(), HeldProgress));
    LineA->SetPaused(false);
    LineA->AdvanceSimulation(18.0f);
    for (int32 Index = 0; Index < 22; ++Index) LineB->AdvanceSimulation(1.0f);
    FLBBodyInWhiteRecord BodyA;
    FLBBodyInWhiteRecord BodyB;
    TestTrue(TEXT("Large and small deterministic time steps yield the same identity and evidence"),
        LineA->GetOutputBody(BodyA) && LineB->GetOutputBody(BodyB)
        && BodyA.BodyId == BodyB.BodyId && BodyA.QualityState == BodyB.QualityState
        && BodyA.QualityEvidence.ReasonCodes == BodyB.QualityEvidence.ReasonCodes
        && FMath::IsNearlyEqual(BodyA.CycleEvidence.WeldingSeconds,
            BodyB.CycleEvidence.WeldingSeconds));

    UWorld* ReworkWorld = nullptr;
    ALBBodyWeldLineActor* Rework = LBBodyWeldTests::SpawnLine(ReworkWorld,
        TEXT("LB_Weld_Rework"), TEXT("WL-REWORK"));
    if (!ReworkWorld || !Rework) return false;
    FLBBodyWeldQualityConditions Conditions;
    Conditions.bRobotCalibrationInTolerance = false;
    Rework->SetQualityConditions(Conditions);
    TestTrue(TEXT("Rework line receives complete recipe"),
        Rework->SetAssignedOrder(LBBodyWeldTests::OrderId) && LBBodyWeldTests::FeedRecipe(Rework));
    Rework->AdvanceSimulation(22.0f);
    FLBBodyInWhiteRecord HeldBody;
    TestTrue(TEXT("Identical bad calibration evidence deterministically creates a visible rework hold"),
        Rework->GetReworkBody(HeldBody)
        && HeldBody.QualityState == ELBBodyWeldQualityState::ReworkRequired
        && HeldBody.QualityEvidence.ReasonCodes.Contains(TEXT("ROBOT_CALIBRATION_OUT_OF_TOLERANCE")));
    Conditions.bRobotCalibrationInTolerance = true;
    Rework->SetQualityConditions(Conditions);
    FString Reason;
    TestTrue(TEXT("Player repair/calibration action re-runs the deterministic failed evidence"),
        Rework->RetryHeldBody(Reason) && Rework->GetOutputBody(HeldBody)
        && HeldBody.QualityState == ELBBodyWeldQualityState::Good);

    WorldA->DestroyWorld(false);
    WorldB->DestroyWorld(false);
    ReworkWorld->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyWeldSavePreflightTest,
    "LineBoss.BodyWeld.Runtime.SaveRoundTripAndAtomicPreflight",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyWeldSavePreflightTest::RunTest(const FString& Parameters)
{
    UWorld* SourceWorld = nullptr;
    UWorld* RestoredWorld = nullptr;
    ALBBodyWeldLineActor* Source = LBBodyWeldTests::SpawnLine(SourceWorld,
        TEXT("LB_Weld_Save_Source"), TEXT("WL-SAVE-001"));
    ALBBodyWeldLineActor* Restored = LBBodyWeldTests::SpawnLine(RestoredWorld,
        TEXT("LB_Weld_Save_Target"), NAME_None);
    if (!SourceWorld || !RestoredWorld || !Source || !Restored) return false;
    TestTrue(TEXT("Source accepts exact recipe"), Source->SetAssignedOrder(LBBodyWeldTests::OrderId)
        && LBBodyWeldTests::FeedRecipe(Source));
    Source->AdvanceSimulation(8.0f); // committed, closure complete, three seconds into framing
    const FLBBodyWeldLineSaveState Saved = Source->CaptureSaveState();
    TestTrue(TEXT("Mid-cycle actor-local save passes pure contract preflight"),
        ALBBodyWeldLineActor::IsSaveStateContractValid(Saved));
    TestTrue(TEXT("Mid-cycle state restores exact reservation, phase, inventory and progress"),
        Restored->RestoreSaveState(Saved)
        && Restored->GetLineId() == Saved.LineId && Restored->GetPhase() == Saved.Phase
        && FMath::IsNearlyEqual(Restored->GetPhaseProgress01(), Saved.PhaseProgress01)
        && Restored->GetReservedPanelCount() == 0
        && Restored->GetAvailablePanelCount() == 0
        && Restored->GetPendingEmptyReturnCount() == 11);
    FLBBodyWeldInputReservation Reservation;
    TestTrue(TEXT("Committed exact reservation survives round trip"),
        Restored->GetActiveReservation(Reservation) && Reservation.bConsumptionCommitted
        && Reservation.Panels.Num() == 11);

    const FLBBodyWeldLineSaveState BeforeInvalid = Restored->CaptureSaveState();
    FLBBodyWeldLineSaveState Corrupt = Saved;
    Corrupt.Stillages[1].PanelUnits[0].PanelId = Corrupt.Stillages[0].PanelUnits[0].PanelId;
    TestFalse(TEXT("Duplicate exact panel identity is rejected in full preflight"),
        ALBBodyWeldLineActor::IsSaveStateContractValid(Corrupt));
    TestFalse(TEXT("Invalid restore fails before mutating the live actor"),
        Restored->RestoreSaveState(Corrupt));
    const FLBBodyWeldLineSaveState AfterInvalid = Restored->CaptureSaveState();
    TestTrue(TEXT("Failed restore preserves prior line identity, phase, progress and reservation"),
        AfterInvalid.LineId == BeforeInvalid.LineId && AfterInvalid.Phase == BeforeInvalid.Phase
        && FMath::IsNearlyEqual(AfterInvalid.PhaseProgress01, BeforeInvalid.PhaseProgress01)
        && AfterInvalid.ActiveReservation.ReservationId == BeforeInvalid.ActiveReservation.ReservationId
        && AfterInvalid.PendingEmptyReturns.Num() == BeforeInvalid.PendingEmptyReturns.Num());

    FLBBodyWeldLineSaveState InvalidEnum = Saved;
    InvalidEnum.Phase = static_cast<ELBBodyWeldPhase>(255);
    TestFalse(TEXT("Invalid enum ordinal is rejected before mutation"),
        ALBBodyWeldLineActor::IsSaveStateContractValid(InvalidEnum));

    SourceWorld->DestroyWorld(false);
    RestoredWorld->DestroyWorld(false);
    return true;
}

#endif
