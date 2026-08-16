#include "LBECoatLineActor.h"

#include "LBFactoryFloorMarkingComponent.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBStatusBeaconComponent.h"
#include "LBVehiclePanelCatalog.h"

#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include <limits>

#if WITH_DEV_AUTOMATION_TESTS

namespace LBECoatLineTests
{
    struct FExpectedBay
    {
        ELBECoatBayType Type;
        float StartXCm;
        float EndXCm;
        bool bHasLiquid;
        bool bEnclosed;
    };

    static const FExpectedBay ExpectedBays[] = {
        { ELBECoatBayType::Degrease,         0.0f,  1800.0f, true,  false },
        { ELBECoatBayType::Rinse1,        1800.0f,  3600.0f, true,  false },
        { ELBECoatBayType::Phosphate,     3600.0f,  5400.0f, true,  false },
        { ELBECoatBayType::Rinse2,        5400.0f,  7200.0f, true,  false },
        { ELBECoatBayType::EDCoat,        7200.0f,  9000.0f, true,  false },
        { ELBECoatBayType::UFRinse,       9000.0f, 10800.0f, true,  false },
        { ELBECoatBayType::DrainInspection,10800.0f,11700.0f, false, false },
        { ELBECoatBayType::OvenEntry,    11700.0f, 12600.0f, false, true  },
        { ELBECoatBayType::OvenCure,     12600.0f, 13500.0f, false, true  },
        { ELBECoatBayType::OvenCure,     13500.0f, 14400.0f, false, true  },
        { ELBECoatBayType::OvenCure,     14400.0f, 15300.0f, false, true  },
        { ELBECoatBayType::OvenCure,     15300.0f, 16200.0f, false, true  },
        { ELBECoatBayType::OvenCure,     16200.0f, 17100.0f, false, true  },
        { ELBECoatBayType::OvenCure,     17100.0f, 18000.0f, false, true  },
        { ELBECoatBayType::OvenExit,     18000.0f, 18900.0f, false, true  }
    };

    static UStaticMeshComponent* FindCarrierPart(ALBECoatLineActor* Line,
        const FString& NameSuffix)
    {
        if (!Line) return nullptr;
        TInlineComponentArray<UStaticMeshComponent*> Components;
        Line->GetComponents(Components);
        // Dynamically-created instance components may receive a numeric uniqueness suffix
        // (for example `_Hoist_0`) when multiple short-lived automation worlds reuse an
        // object name.  Match the stable semantic role within the generated name instead
        // of assuming that role is always the final token.
        for (UStaticMeshComponent* Component : Components)
            if (Component && Component->GetName().Contains(NameSuffix)) return Component;
        return nullptr;
    }

    static bool BuildOneGoodWeldBody(ALBBodyWeldLineActor* WeldLine, const FName OrderId,
        FString& OutReason)
    {
        if (!WeldLine || !WeldLine->Configure(TEXT("WELD-ED-HANDOFF-001"))
            || !WeldLine->SetAssignedOrder(OrderId)) return false;
        int64 Sequence = 1;
        for (const FName Family : ALBBodyWeldLineActor::GetRequiredPanelFamilies())
        {
            FLBBodyWeldStillageInventory Stillage;
            Stillage.StillageId = FName(*FString::Printf(TEXT("STILLAGE-%s"), *Family.ToString()));
            Stillage.OrderId = OrderId;
            Stillage.VehicleModelId = ALBBodyWeldLineActor::GetVehicleModelId();
            Stillage.PanelTypeId = Family;
            Stillage.DeliverySequence = Sequence++;
            Stillage.CapacityPanels = 1;
            FLBBodyWeldPanelUnit& Panel = Stillage.PanelUnits.AddDefaulted_GetRef();
            Panel.PanelId = FName(*FString::Printf(TEXT("PTA-PANEL-CAIRNWELL_2040-%s-000001"),
                *Family.ToString()));
            Panel.OrderId = OrderId;
            Panel.VehicleModelId = Stillage.VehicleModelId;
            Panel.PanelTypeId = Family;
            Panel.StillageId = Stillage.StillageId;
            if (!WeldLine->ReceivePanelStillage(Stillage, OutReason)) return false;
        }
        FLBBodyWeldBaseKitUnit Kit;
        Kit.KitId = TEXT("BIW-KIT-000001");
        Kit.OrderId = OrderId;
        Kit.DeliverySequence = Sequence;
        if (!WeldLine->ReceiveBaseKit(Kit, OutReason)
            || !WeldLine->TryReserveRecipe(OutReason)
            || !WeldLine->CommitReservedInputs(OutReason)) return false;
        WeldLine->AdvanceSimulation(30.0f);
        FLBBodyInWhiteRecord Body;
        return WeldLine->GetOutputBody(Body)
            && Body.QualityState == ELBBodyWeldQualityState::Good;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBECoatLineLayoutContractTest,
    "LineBoss.PaintShop.EDLine.LayoutAndVisualContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBECoatLineLayoutContractTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_EDLine_Layout"));
    ALBECoatLineActor* Line = World ? World->SpawnActor<ALBECoatLineActor>() : nullptr;
    TestTrue(TEXT("ED line actor spawns and accepts stable identity"),
        Line && Line->Configure(TEXT("ED-LINE-TEST-001")));
    if (!World || !Line)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestEqual(TEXT("Complete line contains fifteen logical process bays"), Line->GetBayCount(), 15);
    TestEqual(TEXT("Six logical bays remain open liquid-treatment processes"),
        Line->GetTreatmentBayCount(), 6);
    TestEqual(TEXT("Oven contains six repeatable heated cure positions"),
        Line->GetOvenProcessBayCount(), 6);
    TestEqual(TEXT("Physical module pitch remains nine metres"), Line->GetModulePitchCm(), 900.0f);
    TestEqual(TEXT("Combined ED line is exactly 189 metres"), Line->GetTotalLengthCm(), 18900.0f);
    TestEqual(TEXT("Every open process owns an independent liquid presentation"),
        Line->GetLiquidSurfaceCount(), 6);
    TestEqual(TEXT("Six long tanks resolve to twelve reusable nine-metre visual modules"),
        Line->GetTreatmentVisualModuleCount(), 12);
    TestEqual(TEXT("Treatment, drain and oven resolve to twenty-one physical visual modules"),
        Line->GetPhysicalVisualModuleCount(), 21);
    TestEqual(TEXT("All twelve treatment visual modules are built by the runtime actor"),
        Line->GetBuiltTreatmentVisualInstanceCount(), 12);
    TestTrue(TEXT("Runtime builds a sampled rail presentation instead of one stretched flat beam"),
        Line->GetBuiltRailSegmentInstanceCount() > 24);

    static_assert(UE_ARRAY_COUNT(LBECoatLineTests::ExpectedBays) == 15,
        "The test table must describe every logical ED line bay");
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(LBECoatLineTests::ExpectedBays); ++Index)
    {
        const LBECoatLineTests::FExpectedBay& Expected = LBECoatLineTests::ExpectedBays[Index];
        FLBECoatBayDescriptor Actual;
        TestTrue(FString::Printf(TEXT("Bay %d descriptor is available"), Index),
            Line->GetBayDescriptor(Index, Actual));
        TestTrue(FString::Printf(TEXT("Bay %d preserves its exact semantic and 189 m datum"), Index),
            Actual.BayIndex == Index && Actual.BayType == Expected.Type
            && FMath::IsNearlyEqual(Actual.StartXCm, Expected.StartXCm, 0.01f)
            && FMath::IsNearlyEqual(Actual.EndXCm, Expected.EndXCm, 0.01f)
            && Actual.bHasLiquid == Expected.bHasLiquid
            && Actual.bEnclosed == Expected.bEnclosed);
    }

    FTransform Socket;
    TestTrue(TEXT("E-coat rail input uses the doubled treatment-bay start datum"),
        Line->GetBaySocketTransform(4, TEXT("RailLeftIn"), Socket)
        && Socket.GetLocation().Equals(FVector(7200.0f, -300.0f, 800.0f), 0.01f));
    TestTrue(TEXT("E-coat liquid socket uses the centre of its eighteen-metre tank"),
        Line->GetBaySocketTransform(4, TEXT("Fluid"), Socket)
        && Socket.GetLocation().Equals(FVector(8100.0f, 0.0f, 285.0f), 0.01f));
    TestTrue(TEXT("Dry drain cannot falsely provide a fluid socket"),
        !Line->GetBaySocketTransform(6, TEXT("Fluid"), Socket));
    TestTrue(TEXT("Oven entry exposes its air-seal hook at 117 metres"),
        Line->GetBaySocketTransform(7, TEXT("AirSeal"), Socket)
        && Socket.GetLocation().Equals(FVector(11700.0f, 0.0f, 430.0f), 0.01f));

    const FVector EnvelopeMin = Line->GetProtectedEnvelopeRelativeCentreCm()
        - Line->GetProtectedEnvelopeHalfExtentCm();
    const FVector EnvelopeMax = Line->GetProtectedEnvelopeRelativeCentreCm()
        + Line->GetProtectedEnvelopeHalfExtentCm();
    TestTrue(TEXT("Placement envelope exactly protects the enlarged line and its service access"),
        EnvelopeMin.Equals(FVector(-100.0f, -750.0f, 0.0f), 0.01f)
        && EnvelopeMax.Equals(FVector(19400.0f, 750.0f, 1000.0f), 0.01f));
    TestTrue(TEXT("Placement envelope remains query-only instead of becoming an invisible wall"),
        Line->GetProtectedEnvelope()
        && Line->GetProtectedEnvelope()->GetCollisionEnabled() == ECollisionEnabled::QueryOnly
        && !Line->GetProtectedEnvelope()->CanEverAffectNavigation());

    TestTrue(TEXT("Whole-body input preserves the exact ED process contract"), Line->GetInputPort()
        && Line->GetInputPort()->PortId == TEXT("ED-LINE-TEST-001-IN")
        && Line->GetInputPort()->ProcessStage == LBFactoryProcessStage::ECoat
        && Line->GetInputPort()->MaterialClass == ELBFactoryMaterialClass::BodyInWhite
        && Line->GetInputPort()->TransportKind == ELBFactoryTransportKind::PanelTransfer
        && Line->GetInputPort()->GetRelativeLocation().Equals(FVector(0.0f, 0.0f, 430.0f), 0.01f));
    TestTrue(TEXT("Whole-body output sits at the exact 189 metre handoff"), Line->GetOutputPort()
        && Line->GetOutputPort()->PortId == TEXT("ED-LINE-TEST-001-OUT")
        && Line->GetOutputPort()->GetRelativeLocation().Equals(FVector(18900.0f, 0.0f, 430.0f), 0.01f));

    TestTrue(TEXT("Line paints a non-colliding yellow service boundary"), Line->GetFloorMarkings()
        && Line->GetFloorMarkings()->HasNonCollidingPresentation()
        && Line->GetFloorMarkings()->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::ServiceEnvelope) == 4);
    TestTrue(TEXT("Long tanks and oven portals receive readable red keep-clear hatching"),
        Line->GetFloorMarkings()->GetMarkingCountBySemantic(
            ELBFactoryFloorMarkingSemantic::KeepClearHatch) > 60);

    const FString TreatmentAssetPath = Line->TreatmentBayMesh.ToSoftObjectPath().ToString();
    const FString TreatmentEndAssetPath = Line->TreatmentBayEndMesh.ToSoftObjectPath().ToString();
    TestTrue(TEXT("Treatment authority is the seamless v002 Start/End pair with no baked rail"),
        TreatmentAssetPath.Contains(
            TEXT("Runtime_v002/Modules/SM_LB_EDLine_OpenTreatmentModule_NoRail_Start_v002"))
        && TreatmentEndAssetPath.Contains(
            TEXT("Runtime_v002/Modules/SM_LB_EDLine_OpenTreatmentModule_NoRail_End_v002"))
        && !TreatmentAssetPath.Contains(TEXT("Combined"))
        && !TreatmentEndAssetPath.Contains(TEXT("Combined")));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBECoatLineSmoothCarrierTest,
    "LineBoss.PaintShop.EDLine.SmoothCarrierMotionAndInterlocks",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBECoatLineSmoothCarrierTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_EDLine_Carriers"));
    ALBECoatLineActor* Line = World ? World->SpawnActor<ALBECoatLineActor>() : nullptr;
    if (!World || !Line)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FVector TrolleyLocation;
    FRotator TrolleyRotation;
    for (int32 TankIndex = 0; TankIndex < 6; ++TankIndex)
    {
        const float StartX = TankIndex * 1800.0f;
        TestTrue(FString::Printf(TEXT("Tank %d rail enters at the 800 cm high datum"), TankIndex),
            Line->EvaluateTrackPoseAtDistance(StartX, TrolleyLocation, TrolleyRotation)
            && TrolleyLocation.Equals(FVector(StartX, 0.0f, 800.0f), 0.01f)
            && FMath::IsNearlyZero(TrolleyRotation.Pitch, 0.01f));
        TestTrue(FString::Printf(TEXT("Tank %d has a level 300 cm immersed rail section"), TankIndex),
            Line->EvaluateTrackPoseAtDistance(StartX + 900.0f, TrolleyLocation, TrolleyRotation)
            && TrolleyLocation.Equals(FVector(StartX + 900.0f, 0.0f, 545.0f), 0.01f)
            && FMath::IsNearlyZero(TrolleyRotation.Pitch, 0.01f));
        TestTrue(FString::Printf(TEXT("Tank %d rail exits at the same high datum"), TankIndex),
            Line->EvaluateTrackPoseAtDistance(StartX + 1800.0f, TrolleyLocation, TrolleyRotation)
            && TrolleyLocation.Equals(FVector(StartX + 1800.0f, 0.0f, 800.0f), 0.01f)
            && FMath::IsNearlyZero(TrolleyRotation.Pitch, 0.01f));
    }

    TestTrue(TEXT("Descent sample follows the eased rollercoaster tangent"),
        Line->EvaluateTrackPoseAtDistance(525.0f, TrolleyLocation, TrolleyRotation)
        && TrolleyLocation.Equals(FVector(525.0f, 0.0f, 672.5f), 0.01f)
        && TrolleyRotation.Pitch < -35.0f && TrolleyRotation.Pitch > -45.0f);
    TestTrue(TEXT("Rise sample mirrors the descent without teleporting"),
        Line->EvaluateTrackPoseAtDistance(1275.0f, TrolleyLocation, TrolleyRotation)
        && TrolleyLocation.Equals(FVector(1275.0f, 0.0f, 672.5f), 0.01f)
        && TrolleyRotation.Pitch > 35.0f && TrolleyRotation.Pitch < 45.0f);

    auto TrackZ = [Line](const float Distance)
    {
        FVector Location;
        FRotator Rotation;
        return Line->EvaluateTrackPoseAtDistance(Distance, Location, Rotation)
            ? Location.Z : std::numeric_limits<float>::quiet_NaN();
    };
    constexpr float EpsilonCm = 0.25f;
    for (int32 TankIndex = 0; TankIndex < 6; ++TankIndex)
    {
        const float StartX = TankIndex * 1800.0f;
        for (const float LocalBoundary : {300.0f, 750.0f, 1050.0f, 1500.0f, 1800.0f})
        {
            const float Boundary = StartX + LocalBoundary;
            const float LeftDerivative = (TrackZ(Boundary) - TrackZ(Boundary - EpsilonCm)) / EpsilonCm;
            const float RightDerivative = (TrackZ(Boundary + EpsilonCm) - TrackZ(Boundary)) / EpsilonCm;
            TestTrue(FString::Printf(TEXT("Rail vertical velocity is continuous at X %.0f cm"), Boundary),
                FMath::IsFinite(LeftDerivative) && FMath::IsFinite(RightDerivative)
                && FMath::Abs(LeftDerivative - RightDerivative) < 0.01f);
        }
    }

    FLBECoatCarrierPose Pose;
    TestTrue(TEXT("Carrier starts dry with trolley and body at the same actual X"),
        Line->EvaluateCarrierPoseAtDistance(100.0f, Pose)
        && Pose.Stage == ELBECoatCarrierStage::DryTravel
        && Pose.TrolleyRootLocationCm.Equals(FVector(100.0f, 0.0f, 800.0f), 0.01f)
        && Pose.BodyRootLocationCm.Equals(FVector(100.0f, 0.0f, 430.0f), 0.01f));
    TestTrue(TEXT("Carrier descends with the rail rather than sliding vertically at a fixed X"),
        Line->EvaluateCarrierPoseAtDistance(525.0f, Pose)
        && Pose.Stage == ELBECoatCarrierStage::Descending
        && FMath::IsNearlyEqual(Pose.TrolleyRootLocationCm.X, 525.0f, 0.01f)
        && FMath::IsNearlyEqual(Pose.BodyRootLocationCm.X, 525.0f, 0.01f)
        && FMath::IsNearlyEqual(Pose.BodyRootLocationCm.Z, 302.5f, 0.01f)
        && Pose.TrolleyRotation.Pitch < 0.0f && Pose.BodyRotation.Pitch < 0.0f
        && Pose.Immersion01 > 0.0f && Pose.Immersion01 < 1.0f);
    TestTrue(TEXT("Immersed body reaches the 175 cm root without losing X progression"),
        Line->EvaluateCarrierPoseAtDistance(900.0f, Pose)
        && Pose.Stage == ELBECoatCarrierStage::Immersed
        && Pose.BodyRootLocationCm.Equals(FVector(900.0f, 0.0f, 175.0f), 0.01f)
        && FMath::IsNearlyEqual(Pose.Immersion01, 1.0f, 0.01f));
    TestTrue(TEXT("Rise and high-level draining remain distinct readable stages"),
        Line->EvaluateCarrierPoseAtDistance(1275.0f, Pose)
        && Pose.Stage == ELBECoatCarrierStage::Rising
        && Line->EvaluateCarrierPoseAtDistance(1650.0f, Pose)
        && Pose.Stage == ELBECoatCarrierStage::Draining);
    TestTrue(TEXT("Eighteen-metre treatment seam starts the next logical process dry"),
        Line->EvaluateCarrierPoseAtDistance(1800.0f, Pose)
        && Pose.BayIndex == 1 && Pose.Stage == ELBECoatCarrierStage::DryTravel
        && Pose.BodyRootLocationCm.Equals(FVector(1800.0f, 0.0f, 430.0f), 0.01f));
    TestTrue(TEXT("Downstream line exposes drain, oven entry, cure, exit and complete states"),
        Line->EvaluateCarrierPoseAtDistance(11250.0f, Pose)
        && Pose.Stage == ELBECoatCarrierStage::Draining
        && Line->EvaluateCarrierPoseAtDistance(12150.0f, Pose)
        && Pose.Stage == ELBECoatCarrierStage::OvenEntry
        && Line->EvaluateCarrierPoseAtDistance(13050.0f, Pose)
        && Pose.Stage == ELBECoatCarrierStage::OvenCure
        && Line->EvaluateCarrierPoseAtDistance(18450.0f, Pose)
        && Pose.Stage == ELBECoatCarrierStage::OvenExit
        && Line->EvaluateCarrierPoseAtDistance(18900.0f, Pose)
        && Pose.Stage == ELBECoatCarrierStage::Complete);

    TestTrue(TEXT("Legacy API creates a proxy-only compatibility carrier"),
        Line->AddCarrier(TEXT("BODY-NOSTRETCH"), 100.0f));
    TestFalse(TEXT("Legacy carrier never presents a physical body without BIW lineage"),
        Line->IsCarrierBodyPresented(TEXT("BODY-NOSTRETCH")));
    UStaticMeshComponent* Hoist = LBECoatLineTests::FindCarrierPart(Line, TEXT("_Hoist"));
    TestNotNull(TEXT("Carrier presentation exposes its hoist component"), Hoist);
    const FVector DryHoistScale = Hoist ? Hoist->GetRelativeScale3D() : FVector::ZeroVector;
    TestTrue(TEXT("Carrier can move to the fully immersed track pose"),
        Line->SetCarrierProgress(TEXT("BODY-NOSTRETCH"), 900.0f));
    TestTrue(TEXT("Hoist remains a rigid authored assembly instead of stretching during immersion"),
        Hoist && Hoist->GetRelativeScale3D().Equals(DryHoistScale, 0.001f));

    TestTrue(TEXT("Running line accepts a deterministic simulation command"),
        Line->SetCarrierProgress(TEXT("BODY-NOSTRETCH"), 0.0f)
        && Line->SetOperatingState(ELBECoatOperatingState::Running, TEXT("PRODUCTION")));
    Line->AdvanceSimulation(0.5f);
    FLBECoatCarrierSaveState Carrier;
    TestTrue(TEXT("Legacy proxy carrier cannot advance as a real body without BIW lineage"),
        Line->GetCarrierState(TEXT("BODY-NOSTRETCH"), Carrier)
        && FMath::IsNearlyEqual(Carrier.DistanceCm, 0.0f, 0.01f)
        && !Carrier.bHasBodyInWhite);

    TestTrue(TEXT("A physical nine-metre module seam does not become a false process boundary"),
        Line->SetCarrierProgress(TEXT("BODY-NOSTRETCH"), 850.0f));
    Line->AdvanceSimulation(2.0f);
    TestTrue(TEXT("Legacy proxy remains stationary at a visual seam"),
        Line->GetCarrierState(TEXT("BODY-NOSTRETCH"), Carrier)
        && FMath::IsNearlyEqual(Carrier.DistanceCm, 850.0f, 0.01f));

    TestTrue(TEXT("Interlock fixture arms the next logical treatment bay"),
        Line->SetCarrierProgress(TEXT("BODY-NOSTRETCH"), 1790.0f)
        && Line->SetBayOperatingState(1, true, true, false, 0.0f, 25.0f));
    Line->SetOperatingState(ELBECoatOperatingState::Running, TEXT("INTERLOCK_TEST"));
    Line->AdvanceSimulation(2.0f);
    TestTrue(TEXT("Legacy proxy remains stationary before an unavailable bay"),
        Line->GetCarrierState(TEXT("BODY-NOSTRETCH"), Carrier)
        && FMath::IsNearlyEqual(Carrier.DistanceCm, 1790.0f, 0.01f));
    Line->AdvanceSimulation(1.0f);
    TestTrue(TEXT("Unavailable next bay continues to hold the carrier"),
        Line->GetCarrierState(TEXT("BODY-NOSTRETCH"), Carrier)
        && FMath::IsNearlyEqual(Carrier.DistanceCm, 1790.0f, 0.01f));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBECoatLineOperationsPersistenceTest,
    "LineBoss.PaintShop.EDLine.OperationsLightsFansAndPersistence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBECoatLineOperationsPersistenceTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_EDLine_Operations"));
    ALBECoatLineActor* Line = World ? World->SpawnActor<ALBECoatLineActor>() : nullptr;
    TestTrue(TEXT("Operations fixture configures"), Line && Line->Configure(TEXT("ED-LINE-OPS-001")));
    if (!World || !Line)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("Twelve tank lights, eight oven lights and two portal spots are live components"),
        Line->GetTreatmentServiceLightCount() == 12 && Line->GetOvenInteriorLightCount() == 8
        && Line->GetPortalSpotLightCount() == 2
        && Line->AreOperationalLightsRegisteredAndVisible());
    TestTrue(TEXT("Stopped line presents a red safety state at both portals"),
        Line->GetEntryBeacon() && Line->GetExitBeacon()
        && Line->GetEntryBeacon()->GetStatus() == ELBStatusBeaconState::Stopped
        && Line->GetExitBeacon()->GetStatus() == ELBStatusBeaconState::Stopped
        && Line->GetEntryBeacon()->IsRedLampLit());

    const float FanBefore = Line->GetFanRotationDegrees();
    TestTrue(TEXT("Running state lights both portal beacons green"),
        Line->SetOperatingState(ELBECoatOperatingState::Running, TEXT("BATCH_ACTIVE"))
        && Line->GetEntryBeacon()->GetStatus() == ELBStatusBeaconState::Running
        && Line->GetEntryBeacon()->IsGreenLampLit());
    Line->AdvanceSimulation(0.5f);
    TestTrue(TEXT("All eight oven fan movers visibly rotate while running"),
        Line->GetOvenFanCount() == 8
        && !FMath::IsNearlyEqual(Line->GetFanRotationDegrees(), FanBefore, 0.01f));
    const float FanWhilePaused = Line->GetFanRotationDegrees();
    TestTrue(TEXT("Fault state changes both stack lights to red"),
        Line->SetOperatingState(ELBECoatOperatingState::Faulted, TEXT("OVEN_OVERTEMP"))
        && Line->GetEntryBeacon()->GetStatus() == ELBStatusBeaconState::Fault
        && Line->GetExitBeacon()->IsRedLampLit());
    Line->AdvanceSimulation(0.5f);
    TestTrue(TEXT("Oven fans stop rotating outside Running state"),
        FMath::IsNearlyEqual(Line->GetFanRotationDegrees(), FanWhilePaused, 0.01f));
    TestTrue(TEXT("Emergency stop selects the shared flashing-red language"),
        Line->SetOperatingState(ELBECoatOperatingState::EmergencyStop, TEXT("E_STOP"))
        && Line->GetEntryBeacon()->GetStatus() == ELBStatusBeaconState::Emergency
        && Line->GetEntryBeacon()->IsFlashing());

    FVector LiquidLocation;
    bool bLiquidVisible = false;
    TestTrue(TEXT("Independent ED liquid level moves its long-tank surface"),
        Line->SetLiquidLevel01(4, 0.5f)
        && Line->GetLiquidSurfacePresentation(4, LiquidLocation, bLiquidVisible)
        && bLiquidVisible
        && LiquidLocation.Equals(FVector(8100.0f, 0.0f, 165.0f), 0.01f));
    TestTrue(TEXT("Empty process vessel hides only its own liquid surface"),
        Line->SetLiquidLevel01(2, 0.0f)
        && Line->GetLiquidSurfacePresentation(2, LiquidLocation, bLiquidVisible)
        && !bLiquidVisible
        && Line->GetLiquidSurfacePresentation(3, LiquidLocation, bLiquidVisible)
        && bLiquidVisible);

    Line->SetActorTransform(FTransform(FRotator(0.0f, 15.0f, 0.0f),
        FVector(1200.0f, -800.0f, 0.0f)));
    TestTrue(TEXT("Version-three fixture contains two legacy proxy carriers"),
        Line->AddCarrier(TEXT("BODY-SAVE-001"), 8100.0f)
        && Line->AddCarrier(TEXT("BODY-SAVE-002"), 16650.0f));
    const FLBECoatLineSaveState Saved = Line->CaptureSaveState();
    TestEqual(TEXT("New saves explicitly use ED line schema version three"), Saved.Version, 3);
    TestTrue(TEXT("Captured version-three contract passes preflight"),
        ALBECoatLineActor::IsSaveStateContractValid(Saved));

    ALBECoatLineActor* Restored = World->SpawnActor<ALBECoatLineActor>();
    TestTrue(TEXT("Version-three identity, operation, liquids and carriers restore together"),
        Restored && Restored->RestoreSaveState(Saved)
        && Restored->GetLineId() == TEXT("ED-LINE-OPS-001")
        && Restored->GetActorTransform().Equals(Saved.WorldTransform, 0.01f)
        && Restored->GetOperatingState() == ELBECoatOperatingState::EmergencyStop
        && Restored->GetStateReason() == TEXT("E_STOP")
        && Restored->GetCarrierCount() == 2);
    FLBECoatBayOperatingState RestoredED;
    TestTrue(TEXT("Restored e-coat tank retains its half-full semantic state"),
        Restored && Restored->GetBayOperatingState(4, RestoredED)
        && FMath::IsNearlyEqual(RestoredED.LiquidLevel01, 0.5f, 0.01f));
    FLBECoatCarrierSaveState RestoredCarrier;
    TestTrue(TEXT("Version-three roundtrip preserves legacy proxy carrier distances"),
        Restored && Restored->GetCarrierState(TEXT("BODY-SAVE-001"), RestoredCarrier)
        && FMath::IsNearlyEqual(RestoredCarrier.DistanceCm, 8100.0f, 0.01f)
        && Restored->GetCarrierState(TEXT("BODY-SAVE-002"), RestoredCarrier)
        && FMath::IsNearlyEqual(RestoredCarrier.DistanceCm, 16650.0f, 0.01f));
    TestTrue(TEXT("Restored emergency beacon remains flashing red"), Restored
        && Restored->GetEntryBeacon()->GetStatus() == ELBStatusBeaconState::Emergency
        && Restored->GetEntryBeacon()->IsFlashing());

    FLBECoatLineSaveState VersionTwo = Saved;
    VersionTwo.Version = 2;
    TestTrue(TEXT("Version-two 189 m schema remains a valid proxy-only migration input"),
        ALBECoatLineActor::IsSaveStateContractValid(VersionTwo));
    ALBECoatLineActor* MigratedV2 = World->SpawnActor<ALBECoatLineActor>();
    TestTrue(TEXT("Version-two carriers restore without inventing BIW lineage"),
        MigratedV2 && MigratedV2->RestoreSaveState(VersionTwo)
        && MigratedV2->GetCarrierState(TEXT("BODY-SAVE-001"), RestoredCarrier)
        && !RestoredCarrier.bHasBodyInWhite
        && !MigratedV2->IsCarrierBodyPresented(TEXT("BODY-SAVE-001")));

    FLBECoatLineSaveState Legacy = Saved;
    Legacy.Version = 1;
    Legacy.LineId = TEXT("ED-LINE-LEGACY-001");
    Legacy.Carriers.Reset();
    auto AddLegacyCarrier = [&Legacy](const TCHAR* Id, const float DistanceCm,
        const bool bEnabled = true)
    {
        FLBECoatCarrierSaveState& Carrier = Legacy.Carriers.AddDefaulted_GetRef();
        Carrier.CarrierId = Id;
        Carrier.DistanceCm = DistanceCm;
        Carrier.bEnabled = bEnabled;
    };
    AddLegacyCarrier(TEXT("LEGACY-TREATMENT"), 4050.0f);
    AddLegacyCarrier(TEXT("LEGACY-DRAIN"), 5850.0f);
    AddLegacyCarrier(TEXT("LEGACY-OVEN"), 9900.0f);
    AddLegacyCarrier(TEXT("LEGACY-COMPLETE"), 13500.0f, false);
    TestTrue(TEXT("Legacy 135 m schema remains a valid migration input"),
        ALBECoatLineActor::IsSaveStateContractValid(Legacy));

    ALBECoatLineActor* Migrated = World->SpawnActor<ALBECoatLineActor>();
    TestTrue(TEXT("Legacy 135 m ED line restores through semantic-distance migration"),
        Migrated && Migrated->RestoreSaveState(Legacy)
        && Migrated->GetCarrierCount() == 4);
    TestTrue(TEXT("Legacy e-coat midpoint migrates to the midpoint of the doubled e-coat tank"),
        Migrated && Migrated->GetCarrierState(TEXT("LEGACY-TREATMENT"), RestoredCarrier)
        && FMath::IsNearlyEqual(RestoredCarrier.DistanceCm, 8100.0f, 0.01f));
    TestTrue(TEXT("Legacy drain midpoint retains its logical bay and normalized progress"),
        Migrated && Migrated->GetCarrierState(TEXT("LEGACY-DRAIN"), RestoredCarrier)
        && FMath::IsNearlyEqual(RestoredCarrier.DistanceCm, 11250.0f, 0.01f));
    TestTrue(TEXT("Legacy oven position shifts downstream by the added 54 metres"),
        Migrated && Migrated->GetCarrierState(TEXT("LEGACY-OVEN"), RestoredCarrier)
        && FMath::IsNearlyEqual(RestoredCarrier.DistanceCm, 15300.0f, 0.01f));
    TestTrue(TEXT("Legacy completed carrier maps to the exact new 189 m endpoint"),
        Migrated && Migrated->GetCarrierState(TEXT("LEGACY-COMPLETE"), RestoredCarrier)
        && FMath::IsNearlyEqual(RestoredCarrier.DistanceCm, 18900.0f, 0.01f)
        && !RestoredCarrier.bEnabled);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBECoatLineBodyWeldHandoffTest,
    "LineBoss.PaintShop.EDLine.BodyWeldExactOnceAtomicHandoff",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBECoatLineBodyWeldHandoffTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_EDLine_WeldHandoff"));
    ALBBodyWeldLineActor* Weld = World ? World->SpawnActor<ALBBodyWeldLineActor>() : nullptr;
    ALBECoatLineActor* ED = World ? World->SpawnActor<ALBECoatLineActor>() : nullptr;
    FString Reason;
    TestTrue(TEXT("Cross-actor fixture produces one deterministic quality-approved BIW"),
        World && Weld && ED && ED->Configure(TEXT("ED-HANDOFF-001"))
        && LBECoatLineTests::BuildOneGoodWeldBody(Weld, TEXT("ORDER-ED-001"), Reason));
    if (!World || !Weld || !ED)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FLBBodyInWhiteRecord AtWeldOutput;
    TestTrue(TEXT("Weld exposes exact unacknowledged BIW lineage"),
        Weld->GetOutputBody(AtWeldOutput) && !AtWeldOutput.bEDAccepted
        && AtWeldOutput.Panels.Num() == ALBBodyWeldLineActor::GetRequiredPanelFamilies().Num());
    const FLBECoatLineSaveState BeforeFailure = ED->CaptureSaveState();
    const FLBBodyWeldLineSaveState WeldBeforeFailure = Weld->CaptureSaveState();
    TestFalse(TEXT("Wrong body identity is rejected before either actor mutates"),
        ED->AcceptAndAcknowledgeBodyInWhite(Weld, TEXT("WRONG-BODY"),
            TEXT("ED-CARRIER-001"), Reason));
    const FLBECoatLineSaveState AfterFailure = ED->CaptureSaveState();
    const FLBBodyWeldLineSaveState WeldAfterFailure = Weld->CaptureSaveState();
    TestTrue(TEXT("Failed handoff preserves ED byte-equivalent logical state"),
        BeforeFailure.Version == AfterFailure.Version
        && BeforeFailure.LineId == AfterFailure.LineId
        && BeforeFailure.WorldTransform.Equals(AfterFailure.WorldTransform, 0.001f)
        && BeforeFailure.Carriers.Num() == AfterFailure.Carriers.Num()
        && BeforeFailure.OperatingState == AfterFailure.OperatingState
        && BeforeFailure.StateReason == AfterFailure.StateReason
        && FMath::IsNearlyEqual(BeforeFailure.TargetLineSpeedCmPerSecond,
            AfterFailure.TargetLineSpeedCmPerSecond)
        && BeforeFailure.bLoopCarriers == AfterFailure.bLoopCarriers
        && BeforeFailure.BayStates.Num() == AfterFailure.BayStates.Num());
    TestTrue(TEXT("Failed handoff preserves weld output and ED-availability state"),
        WeldBeforeFailure.bEDAvailable == WeldAfterFailure.bEDAvailable
        && WeldBeforeFailure.bHasOutputBody == WeldAfterFailure.bHasOutputBody
        && WeldBeforeFailure.OutputBody.BodyId == WeldAfterFailure.OutputBody.BodyId
        && WeldBeforeFailure.OutputBody.ReservationId
            == WeldAfterFailure.OutputBody.ReservationId
        && WeldBeforeFailure.OutputBody.Panels.Num() == WeldAfterFailure.OutputBody.Panels.Num()
        && WeldBeforeFailure.CompletedBodies.Num() == WeldAfterFailure.CompletedBodies.Num()
        && WeldBeforeFailure.NextEventSequence == WeldAfterFailure.NextEventSequence);

    TestTrue(TEXT("Exact BIW is atomically accepted and acknowledged once"),
        ED->AcceptAndAcknowledgeBodyInWhite(Weld, AtWeldOutput.BodyId,
            TEXT("ED-CARRIER-001"), Reason));
    FLBBodyInWhiteRecord AtED;
    FLBECoatCarrierSaveState EDCarrier;
    TestTrue(TEXT("ED owns the acknowledged body and preserves exact source identity"),
        ED->GetCarrierState(TEXT("ED-CARRIER-001"), EDCarrier)
        && EDCarrier.bHasBodyInWhite
        && ED->IsCarrierBodyPresented(TEXT("ED-CARRIER-001"))
        && ED->GetCarrierBodyInWhite(TEXT("ED-CARRIER-001"), AtED)
        && AtED.bEDAccepted && AtED.BodyId == AtWeldOutput.BodyId
        && AtED.VehicleModelId == AtWeldOutput.VehicleModelId
        && AtED.OrderId == AtWeldOutput.OrderId
        && AtED.BaseKitId == AtWeldOutput.BaseKitId
        && AtED.ReservationId == AtWeldOutput.ReservationId
        && AtED.WeldLineId == AtWeldOutput.WeldLineId
        && AtED.Panels.Num() == AtWeldOutput.Panels.Num());
    bool bExactPanels = AtED.Panels.Num() == AtWeldOutput.Panels.Num();
    for (int32 Index = 0; bExactPanels && Index < AtED.Panels.Num(); ++Index)
        bExactPanels = AtED.Panels[Index].PanelId == AtWeldOutput.Panels[Index].PanelId
            && AtED.Panels[Index].PanelTypeId == AtWeldOutput.Panels[Index].PanelTypeId
            && AtED.Panels[Index].StillageId == AtWeldOutput.Panels[Index].StillageId;
    TestTrue(TEXT("All eleven exact pressed-panel lineage records cross unchanged"), bExactPanels);
    TestTrue(TEXT("Weld releases output into its completed exact-once history"),
        !Weld->GetOutputBody(AtWeldOutput) && Weld->GetCompletedBodyCount() == 1);
    TestFalse(TEXT("A second acceptance of the same body cannot duplicate ED inventory"),
        ED->AcceptAndAcknowledgeBodyInWhite(Weld, AtED.BodyId,
            TEXT("ED-CARRIER-002"), Reason));
    TestEqual(TEXT("ED still owns exactly one carrier after duplicate rejection"),
        ED->GetCarrierCount(), 1);

    const FLBECoatLineSaveState Saved = ED->CaptureSaveState();
    TestTrue(TEXT("Version-three save contract includes accepted BIW lineage"),
        Saved.Version == 3 && ALBECoatLineActor::IsSaveStateContractValid(Saved)
        && Saved.Carriers.Num() == 1 && Saved.Carriers[0].bHasBodyInWhite);
    ALBECoatLineActor* Restored = World->SpawnActor<ALBECoatLineActor>();
    FLBBodyInWhiteRecord RestoredBody;
    TestTrue(TEXT("Accepted carrier/body lineage round-trips through persistence"),
        Restored && Restored->RestoreSaveState(Saved)
        && Restored->GetCarrierBodyInWhite(TEXT("ED-CARRIER-001"), RestoredBody)
        && RestoredBody.BodyId == AtED.BodyId && RestoredBody.Panels.Num() == AtED.Panels.Num());

    World->DestroyWorld(false);
    return true;
}

#endif
