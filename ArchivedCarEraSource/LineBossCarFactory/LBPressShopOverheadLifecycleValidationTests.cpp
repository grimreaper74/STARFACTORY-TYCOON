#if WITH_DEV_AUTOMATION_TESTS

#include "LBPressShopOverheadPresentationActor.h"

#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBPressShopOverheadVisualLayerActor.h"
#include "Misc/AutomationTest.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace LBPressShopOverheadLifecycleValidationPrivate
{
    constexpr TCHAR ReceiptSchema[] =
        TEXT("LB_PRESS_SHOP_OVERHEAD_LIFECYCLE_VALIDATION_V002");

    struct FFactoryFixture
    {
        UWorld* World = nullptr;
        ALBOneFactoryPressStarterLayoutAuthority* Press = nullptr;
        ALBOneFactoryBodyWeldStarterLayoutAuthority* Body = nullptr;
        ALBOneFactoryPaintStarterLayoutAuthority* Paint = nullptr;
        ALBOneFactoryAssemblyStarterLayoutAuthority* Assembly = nullptr;
        ALBOneFactoryProductionFlowAuthority* Production = nullptr;
        ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
        ALBPressShopOverheadPresentationActor* Presentation = nullptr;

        bool Create(FString& OutReason)
        {
            World = UWorld::CreateWorld(EWorldType::Game, false,
                TEXT("LB_PressShop_Overhead_Lifecycle_Integration"));
            if (!World)
            {
                OutReason = TEXT("TRANSIENT INTEGRATION WORLD FAILED");
                return false;
            }

            Press = World->SpawnActor<
                ALBOneFactoryPressStarterLayoutAuthority>();
            Body = World->SpawnActor<
                ALBOneFactoryBodyWeldStarterLayoutAuthority>();
            Paint = World->SpawnActor<
                ALBOneFactoryPaintStarterLayoutAuthority>();
            Assembly = World->SpawnActor<
                ALBOneFactoryAssemblyStarterLayoutAuthority>();
            Production = World->SpawnActor<
                ALBOneFactoryProductionFlowAuthority>();
            Coordinator = World->SpawnActor<ALBOneFactoryRuntimeCoordinator>();
            if (!Press || !Body || !Paint || !Assembly || !Production
                || !Coordinator)
            {
                OutReason = TEXT("CANONICAL RUNTIME AUTHORITIES FAILED");
                return false;
            }

            Coordinator->bAdvanceStartedVehiclesOnActorTick = false;
            if (!Press->Commission(OutReason)
                || !Body->Commission(OutReason)
                || !Paint->Commission(OutReason)
                || !Assembly->Commission(OutReason))
            {
                return false;
            }
            for (int32 DepartmentIndex = 0; DepartmentIndex < 4;
                ++DepartmentIndex)
            {
                if (!Production->SetDepartmentCommissioned(
                        static_cast<ELBOneFactoryDepartment>(DepartmentIndex),
                        true, OutReason))
                {
                    return false;
                }
            }
            return Coordinator->ValidateRuntimeFactory(OutReason);
        }

        bool CreateAndStartUnit(FName& OutUnitId, FString& OutReason)
        {
            const FLBOneFactoryBodyWeldLayoutState BodyState =
                Body->CaptureLayout();
            const FLBOneFactoryPaintStarterLayoutState PaintState =
                Paint->CaptureLayout();
            if (!Coordinator->CreateRuntimeVehicleOrder(
                    TEXT("PRESS_OVERHEAD_EVIDENCE_ORDER_001"),
                    BodyState.VehicleModelId, PaintState.PaintProgrammeId,
                    TEXT("CAIRNWELL_TEAL"), TEXT("COIL_EVIDENCE_001"),
                    OutUnitId, OutReason))
            {
                return false;
            }
            return Coordinator->StartVehicle(OutUnitId, OutReason);
        }

        void Destroy()
        {
            if (World)
            {
                World->DestroyWorld(false);
            }
            *this = FFactoryFixture();
        }
    };

    struct FLayerProbe
    {
        ALBPressShopOverheadVisualLayerActor* Actor = nullptr;
        FName MachineId = NAME_None;
        ELBPressShopOverheadLayerRole Role =
            ELBPressShopOverheadLayerRole::Base;
        FName StateId = NAME_None;
    };

    struct FExpectedCheckpoint
    {
        FString CheckpointId;
        FName StationId = NAME_None;
        float Progress01 = 0.0f;
        TArray<FName> ActiveMachines;
        TArray<FName> TransferMachines;
        FName PoseMachine = NAME_None;
        FName PoseState = NAME_None;
        FName ActivePress = NAME_None;
        ELBPressShopOverheadPressFrame PressFrame =
            ELBPressShopOverheadPressFrame::Open;
        int32 ExpectedS01SequenceFrames = 0;
        bool bCheckCartTransform = false;
        FVector ExpectedCartLocation = FVector::ZeroVector;
    };

    FString PressFrameName(const ELBPressShopOverheadPressFrame Frame)
    {
        switch (Frame)
        {
        case ELBPressShopOverheadPressFrame::Descending:
            return TEXT("DESCENDING");
        case ELBPressShopOverheadPressFrame::Contact:
            return TEXT("CONTACT");
        case ELBPressShopOverheadPressFrame::Rising:
            return TEXT("RISING");
        default:
            return TEXT("OPEN");
        }
    }

    FString StageName(const ELBOneFactoryVehicleStage Stage)
    {
        if (const UEnum* Enum = StaticEnum<ELBOneFactoryVehicleStage>())
        {
            return Enum->GetNameStringByValue(static_cast<int64>(Stage));
        }
        return TEXT("UNKNOWN");
    }

    TArray<TSharedPtr<FJsonValue>> NamesToJson(const TArray<FName>& Names)
    {
        TArray<TSharedPtr<FJsonValue>> Values;
        Values.Reserve(Names.Num());
        for (const FName Name : Names)
        {
            Values.Add(MakeShared<FJsonValueString>(Name.ToString()));
        }
        return Values;
    }

    TSharedPtr<FJsonObject> VectorToJson(const FVector& Value)
    {
        TSharedPtr<FJsonObject> Json = MakeShared<FJsonObject>();
        Json->SetNumberField(TEXT("x_cm"), Value.X);
        Json->SetNumberField(TEXT("y_cm"), Value.Y);
        Json->SetNumberField(TEXT("z_cm"), Value.Z);
        return Json;
    }

    bool IsLayerVisible(const FLayerProbe& Probe)
    {
        return Probe.Actor && !Probe.Actor->IsHidden()
            && Probe.Actor->GetStaticMeshComponent()
            && Probe.Actor->GetStaticMeshComponent()->IsVisible();
    }

    void SortNames(TArray<FName>& Names)
    {
        Names.Sort([](const FName Left, const FName Right)
        {
            return Left.LexicalLess(Right);
        });
    }

    bool SameNames(TArray<FName> Left, TArray<FName> Right)
    {
        SortNames(Left);
        SortNames(Right);
        return Left == Right;
    }

    ALBPressShopOverheadVisualLayerActor* AddLayer(
        FFactoryFixture& Fixture, TArray<FLayerProbe>& OutLayers,
        const FName MachineId, const ELBPressShopOverheadLayerRole Role,
        const FName StateId = NAME_None,
        const FName MotionChannel = NAME_None,
        const int32 SequenceFrameIndex = INDEX_NONE,
        const int32 SequenceFrameCount = 0,
        const bool bSequenceLoops = false)
    {
        ALBPressShopOverheadVisualLayerActor* Layer = Fixture.World
            ? Fixture.World->SpawnActor<
                ALBPressShopOverheadVisualLayerActor>() : nullptr;
        if (!Layer)
        {
            return nullptr;
        }
        Layer->LayerId = FName(*FString::Printf(TEXT("PROBE_%s_%d_%s_%d"),
            *MachineId.ToString(), static_cast<int32>(Role),
            *StateId.ToString(), SequenceFrameIndex));
        Layer->AssemblyId = TEXT("PRESS_OVERHEAD_LIFECYCLE_PROBE");
        Layer->MachineId = MachineId;
        Layer->LayerRole = Role;
        Layer->StateId = StateId;
        Layer->MotionChannel = MotionChannel;
        Layer->SequenceFrameIndex = SequenceFrameIndex;
        Layer->SequenceFrameCount = SequenceFrameCount;
        Layer->bSequenceLoops = bSequenceLoops;
        OutLayers.Add({Layer, MachineId, Role, StateId});
        return Layer;
    }

    void AddExhaustiveLayerMatrix(FFactoryFixture& Fixture,
        TArray<FLayerProbe>& OutLayers,
        ALBPressShopOverheadVisualLayerActor*& OutCartLayer)
    {
        const FName MachineIds[] = {
            TEXT("IN01_ARTICULATED_CARRIER"),
            TEXT("IN02_COIL_HANDLER_AGV"), TEXT("IN03_COIL_STORAGE"),
            TEXT("IN04_DEPACK"), TEXT("IN05_COIL_PREP"),
            TEXT("S01_DESTACK_LOAD"), TEXT("S02_DEEP_DRAW"),
            TEXT("S03_FORM"), TEXT("S04_TRIM"), TEXT("S05_PIERCE"),
            TEXT("S06_FLANGE"), TEXT("S07_INSPECTION"),
            TEXT("S07_PALLETISER"), TEXT("SUPPORT_FLEET")
        };
        const FName BeaconStates[] = {
            TEXT("OFF"), TEXT("GREEN"), TEXT("AMBER"), TEXT("RED")
        };
        for (const FName MachineId : MachineIds)
        {
            AddLayer(Fixture, OutLayers, MachineId,
                ELBPressShopOverheadLayerRole::Workpiece);
            AddLayer(Fixture, OutLayers, MachineId,
                ELBPressShopOverheadLayerRole::CyanTransfer);
            for (const FName BeaconState : BeaconStates)
            {
                AddLayer(Fixture, OutLayers, MachineId,
                    ELBPressShopOverheadLayerRole::BeaconGlow, BeaconState);
            }
        }

        const FName PressMachines[] = {
            TEXT("S02_DEEP_DRAW"), TEXT("S03_FORM"), TEXT("S04_TRIM"),
            TEXT("S05_PIERCE"), TEXT("S06_FLANGE")
        };
        const FName FrameStates[] = {
            TEXT("OPEN"), TEXT("DESCENDING"), TEXT("CONTACT"),
            TEXT("RISING")
        };
        for (const FName MachineId : PressMachines)
        {
            for (const FName FrameState : FrameStates)
            {
                AddLayer(Fixture, OutLayers, MachineId,
                    ELBPressShopOverheadLayerRole::FrameState, FrameState);
            }
            AddLayer(Fixture, OutLayers, MachineId,
                ELBPressShopOverheadLayerRole::ContactEffect);
        }

        const auto AddPoses = [&Fixture, &OutLayers](
            const FName MachineId, const TArray<FName>& Poses)
        {
            for (const FName Pose : Poses)
            {
                AddLayer(Fixture, OutLayers, MachineId,
                    ELBPressShopOverheadLayerRole::RobotPose, Pose);
            }
        };
        AddPoses(TEXT("IN01_ARTICULATED_CARRIER"),
            TArray<FName>{TEXT("UNLOADING")});
        AddPoses(TEXT("IN02_COIL_HANDLER_AGV"),
            TArray<FName>{TEXT("TRANSFER")});
        AddPoses(TEXT("IN03_COIL_STORAGE"),
            TArray<FName>{TEXT("STORE")});
        AddPoses(TEXT("IN04_DEPACK"), TArray<FName>{TEXT("ROLLERS"),
            TEXT("WRAP_REMOVE"), TEXT("VISION_INSPECT")});
        AddPoses(TEXT("IN05_COIL_PREP"), TArray<FName>{TEXT("FEED")});
        AddPoses(TEXT("S01_DESTACK_LOAD"), TArray<FName>{TEXT("LOAD")});
        AddPoses(TEXT("S07_INSPECTION"), TArray<FName>{TEXT("PARKED"),
            TEXT("PICK"), TEXT("INSPECT"), TEXT("PLACE")});
        AddPoses(TEXT("S07_PALLETISER"), TArray<FName>{TEXT("PARKED"),
            TEXT("PICK"), TEXT("PLACE")});
        AddPoses(TEXT("SUPPORT_FLEET"), TArray<FName>{TEXT("PARKED"),
            TEXT("TRANSFER"), TEXT("OUTBOUND")});

        OutCartLayer = AddLayer(Fixture, OutLayers,
            TEXT("S01_DESTACK_LOAD"),
            ELBPressShopOverheadLayerRole::MovingOverlay, TEXT("LOAD"),
            TEXT("CoilTransferToDecoiler"));
        if (OutCartLayer)
        {
            OutCartLayer->SetActorLocation(FVector(1000.0, 200.0, 10.0));
        }
        for (int32 Frame = 0; Frame < 8; ++Frame)
        {
            AddLayer(Fixture, OutLayers, TEXT("S01_DESTACK_LOAD"),
                ELBPressShopOverheadLayerRole::ConveyorMotion, NAME_None,
                TEXT("S01_DECOILER_PAYOFF"), Frame, 8, false);
        }
    }

    bool ReachProgress(FFactoryFixture& Fixture, const FName UnitId,
        const FName ExpectedStation, const float TargetProgress,
        FLBOneFactoryRuntimeVehicleStatus& OutStatus, FString& OutReason)
    {
        if (!Fixture.Coordinator->GetVehicleRuntimeStatus(
                UnitId, OutStatus, OutReason)
            || OutStatus.CurrentStationId != ExpectedStation
            || TargetProgress + KINDA_SMALL_NUMBER
                < OutStatus.NormalizedCycleProgress)
        {
            return false;
        }
        const float RemainingProgress = TargetProgress
            - OutStatus.NormalizedCycleProgress;
        if (RemainingProgress > KINDA_SMALL_NUMBER)
        {
            const float Delta = RemainingProgress
                * OutStatus.CycleDurationSeconds;
            if (!Fixture.Coordinator->TickVehicle(
                    UnitId, Delta, OutReason)
                || !Fixture.Coordinator->GetVehicleRuntimeStatus(
                    UnitId, OutStatus, OutReason))
            {
                return false;
            }
        }
        return OutStatus.CurrentStationId == ExpectedStation
            && FMath::IsNearlyEqual(OutStatus.NormalizedCycleProgress,
                TargetProgress, 0.001f);
    }

    bool AdvanceStation(FFactoryFixture& Fixture, const FName UnitId,
        const FName ExpectedSource, FString& OutReason)
    {
        FLBOneFactoryRuntimeVehicleStatus Before;
        if (!Fixture.Coordinator->GetVehicleRuntimeStatus(
                UnitId, Before, OutReason)
            || Before.CurrentStationId != ExpectedSource)
        {
            return false;
        }
        return Fixture.Coordinator->TickVehicle(UnitId,
            Before.CycleDurationSeconds + 1.0f, OutReason);
    }

    bool CaptureCheckpoint(FAutomationTestBase& Test,
        FFactoryFixture& Fixture, const FName UnitId,
        const FExpectedCheckpoint& Expected,
        const TArray<FLayerProbe>& Layers,
        ALBPressShopOverheadVisualLayerActor* CartLayer,
        TArray<TSharedPtr<FJsonValue>>& OutCheckpointJson,
        FString& OutReason)
    {
        FLBOneFactoryRuntimeVehicleStatus Status;
        bool bPassed = ReachProgress(Fixture, UnitId, Expected.StationId,
            Expected.Progress01, Status, OutReason);
        if (bPassed)
        {
            Fixture.Presentation->Tick(0.0f);
            bPassed = Fixture.Presentation->RefreshFromRuntime(OutReason);
        }

        TArray<FName> VisibleWorkpieces;
        TArray<FName> VisibleTransfers;
        TArray<FName> VisiblePoses;
        TMap<FName, TArray<FName>> VisibleFrames;
        TMap<FName, int32> VisibleBeaconCount;
        int32 VisibleContactEffects = 0;
        int32 VisibleS01SequenceFrames = 0;
        bool bAllCollisionDisabled = true;
        for (const FLayerProbe& Probe : Layers)
        {
            if (Probe.Actor && (Probe.Actor->GetActorEnableCollision()
                    || (Probe.Actor->GetStaticMeshComponent()
                        && Probe.Actor->GetStaticMeshComponent()
                            ->GetCollisionEnabled()
                            != ECollisionEnabled::NoCollision)))
            {
                bAllCollisionDisabled = false;
            }
            if (!IsLayerVisible(Probe))
            {
                continue;
            }
            switch (Probe.Role)
            {
            case ELBPressShopOverheadLayerRole::Workpiece:
                VisibleWorkpieces.Add(Probe.MachineId);
                break;
            case ELBPressShopOverheadLayerRole::CyanTransfer:
                VisibleTransfers.Add(Probe.MachineId);
                break;
            case ELBPressShopOverheadLayerRole::RobotPose:
                if (Probe.MachineId == Expected.PoseMachine)
                {
                    VisiblePoses.Add(Probe.StateId);
                }
                break;
            case ELBPressShopOverheadLayerRole::FrameState:
                VisibleFrames.FindOrAdd(Probe.MachineId).Add(Probe.StateId);
                break;
            case ELBPressShopOverheadLayerRole::ContactEffect:
                ++VisibleContactEffects;
                break;
            case ELBPressShopOverheadLayerRole::BeaconGlow:
                ++VisibleBeaconCount.FindOrAdd(Probe.MachineId);
                break;
            case ELBPressShopOverheadLayerRole::ConveyorMotion:
                if (Probe.MachineId == TEXT("S01_DESTACK_LOAD"))
                {
                    ++VisibleS01SequenceFrames;
                }
                break;
            default:
                break;
            }
        }
        SortNames(VisibleWorkpieces);
        SortNames(VisibleTransfers);
        SortNames(VisiblePoses);

        const FName PressMachines[] = {
            TEXT("S02_DEEP_DRAW"), TEXT("S03_FORM"), TEXT("S04_TRIM"),
            TEXT("S05_PIERCE"), TEXT("S06_FLANGE")
        };
        bool bFrameExclusivity = true;
        for (const FName PressMachine : PressMachines)
        {
            const TArray<FName>* Frames = VisibleFrames.Find(PressMachine);
            const FName ExpectedFrame = PressMachine == Expected.ActivePress
                ? FName(*PressFrameName(Expected.PressFrame))
                : FName(TEXT("OPEN"));
            bFrameExclusivity = bFrameExclusivity && Frames
                && Frames->Num() == 1 && (*Frames)[0] == ExpectedFrame;
        }
        bool bBeaconExclusivity = VisibleBeaconCount.Num() == 14;
        for (const TPair<FName, int32>& Pair : VisibleBeaconCount)
        {
            bBeaconExclusivity = bBeaconExclusivity && Pair.Value == 1;
        }

        const bool bWorkpieceExclusive = SameNames(
            VisibleWorkpieces, Expected.ActiveMachines);
        const bool bTransferExclusive = SameNames(
            VisibleTransfers, Expected.TransferMachines);
        const bool bPoseExclusive = Expected.PoseMachine.IsNone()
            || (VisiblePoses.Num() == 1
                && VisiblePoses[0] == Expected.PoseState);
        const int32 ExpectedContactCount =
            Expected.PressFrame == ELBPressShopOverheadPressFrame::Contact
            && !Expected.ActivePress.IsNone() ? 1 : 0;
        const bool bContactExclusive =
            VisibleContactEffects == ExpectedContactCount;
        const bool bSequenceExclusive = VisibleS01SequenceFrames
            == Expected.ExpectedS01SequenceFrames;
        const FVector CartLocation = CartLayer
            ? CartLayer->GetActorLocation() : FVector::ZeroVector;
        const bool bCartTransformMatches = !Expected.bCheckCartTransform
            || (CartLayer && CartLocation.Equals(
                Expected.ExpectedCartLocation, 0.05));
        bPassed = bPassed && bWorkpieceExclusive && bTransferExclusive
            && bPoseExclusive && bFrameExclusivity && bContactExclusive
            && bBeaconExclusivity && bSequenceExclusive
            && bCartTransformMatches && bAllCollisionDisabled;

        Test.TestTrue(*FString::Printf(TEXT("%s lifecycle checkpoint"),
            *Expected.CheckpointId), bPassed);

        TSharedPtr<FJsonObject> Json = MakeShared<FJsonObject>();
        Json->SetStringField(TEXT("checkpoint_id"), Expected.CheckpointId);
        Json->SetStringField(TEXT("station_id"),
            Status.CurrentStationId.ToString());
        Json->SetStringField(TEXT("semantic_stage"), StageName(Status.Stage));
        Json->SetNumberField(TEXT("station_cursor"), Status.StationCursor);
        Json->SetNumberField(TEXT("normalized_cycle_progress"),
            Status.NormalizedCycleProgress);
        Json->SetArrayField(TEXT("expected_active_machine_ids"),
            NamesToJson(Expected.ActiveMachines));
        Json->SetArrayField(TEXT("visible_workpiece_machine_ids"),
            NamesToJson(VisibleWorkpieces));
        Json->SetArrayField(TEXT("expected_transfer_machine_ids"),
            NamesToJson(Expected.TransferMachines));
        Json->SetArrayField(TEXT("visible_transfer_machine_ids"),
            NamesToJson(VisibleTransfers));
        Json->SetBoolField(TEXT("workpiece_exclusivity_pass"),
            bWorkpieceExclusive);
        Json->SetBoolField(TEXT("transfer_exclusivity_pass"),
            bTransferExclusive);
        Json->SetBoolField(TEXT("pose_exclusivity_pass"), bPoseExclusive);
        Json->SetBoolField(TEXT("press_frame_exclusivity_pass"),
            bFrameExclusivity);
        Json->SetBoolField(TEXT("contact_effect_exclusivity_pass"),
            bContactExclusive);
        Json->SetBoolField(TEXT("beacon_layer_exclusivity_pass"),
            bBeaconExclusivity);
        Json->SetBoolField(TEXT("sequence_frame_exclusivity_pass"),
            bSequenceExclusive);
        Json->SetBoolField(TEXT("collision_disabled_pass"),
            bAllCollisionDisabled);
        Json->SetObjectField(TEXT("coil_cart_world_location"),
            VectorToJson(CartLocation));
        Json->SetBoolField(TEXT("coil_cart_transform_pass"),
            bCartTransformMatches);
        Json->SetBoolField(TEXT("pass"), bPassed);
        if (!bPassed)
        {
            Json->SetStringField(TEXT("reason"), OutReason);
        }
        OutCheckpointJson.Add(MakeShared<FJsonValueObject>(Json));
        return bPassed;
    }

    bool WriteReceipt(const FName UnitId, const FName RuntimeTopologyId,
        const int32 RouteProfileVersion, const bool bIntegrationPass,
        const bool bPressHandoffPass,
        const bool bPressInspectionQualityGatePresent,
        const TArray<TSharedPtr<FJsonValue>>& Checkpoints,
        FString& OutPath)
    {
        const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(),
            TEXT("Automation"),
            TEXT("PressShopOverheadLifecycle_v002"));
        IFileManager::Get().MakeDirectory(*Directory, true);
        OutPath = FPaths::Combine(Directory,
            TEXT("press_shop_overhead_lifecycle_receipt_v002.json"));

        TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
        Root->SetStringField(TEXT("schema"), ReceiptSchema);
        Root->SetStringField(TEXT("generated_utc"),
            FDateTime::UtcNow().ToIso8601());
        Root->SetStringField(TEXT("unit_id"), UnitId.ToString());
        Root->SetStringField(TEXT("route_profile"),
            TEXT("PRESS_INSPECTION_V002"));
        Root->SetNumberField(TEXT("route_profile_version"),
            RouteProfileVersion);
        Root->SetStringField(TEXT("runtime_topology_id"),
            RuntimeTopologyId.ToString());
        Root->SetStringField(TEXT("validation_world"),
            TEXT("transient_game_integration_world"));
        Root->SetStringField(TEXT("validated_scope"),
            TEXT("canonical seven-station Press department lifecycle and overhead presentation adapter"));
        Root->SetBoolField(TEXT("protected_map_loaded"), false);
        Root->SetBoolField(TEXT("map_mutated_or_saved"), false);
        Root->SetBoolField(TEXT("exact_candidate_map_pie_proved"), false);
        Root->SetBoolField(TEXT("canonical_runtime_cycle_pass"),
            bIntegrationPass);
        Root->SetBoolField(TEXT("press_to_body_handoff_pass"),
            bPressHandoffPass);
        Root->SetBoolField(TEXT("press_inspection_quality_gate_present"),
            bPressInspectionQualityGatePresent);
        Root->SetBoolField(TEXT("imported_candidate_layer_metadata_proved"),
            false);
        Root->SetBoolField(TEXT("steam_readiness_pass"), false);
        Root->SetArrayField(TEXT("checkpoints"), Checkpoints);

        TArray<TSharedPtr<FJsonValue>> ProvenTransformChannels;
        ProvenTransformChannels.Add(MakeShared<FJsonValueString>(
            TEXT("S01 CoilTransferToDecoiler: +X 320 cm, start/mid/end")));
        Root->SetArrayField(TEXT("proven_mover_transform_channels"),
            ProvenTransformChannels);

        TArray<TSharedPtr<FJsonValue>> MissingEvidence;
        const TCHAR* Missing[] = {
            TEXT("Exact candidate-map Play-In-Editor run has not been executed by this transient integration test."),
            TEXT("Imported candidate layer metadata and material render proxies require a separate exact-map audit/capture."),
            TEXT("IN02 coil-handler AGV has a pose/transfer layer but no authored measurable cargo transform range."),
            TEXT("S02-S06 transfers are frame/cyan-overlay presentation; no authored per-panel mover transform range is exposed."),
            TEXT("S07 inspection and palletiser are pose sprites; no authored pick/place payload transform ranges are exposed."),
            TEXT("Packaged runtime, performance and Steam screenshot gates remain outside this receipt.")
        };
        for (const TCHAR* Item : Missing)
        {
            MissingEvidence.Add(MakeShared<FJsonValueString>(Item));
        }
        Root->SetArrayField(TEXT("missing_evidence_for_steam_readiness"),
            MissingEvidence);

        FString Serialized;
        const TSharedRef<TJsonWriter<>> Writer =
            TJsonWriterFactory<>::Create(&Serialized);
        if (!FJsonSerializer::Serialize(Root.ToSharedRef(), Writer))
        {
            return false;
        }
        return FFileHelper::SaveStringToFile(Serialized, *OutPath,
            FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPressShopOverheadCanonicalLifecycleReceiptTest,
    "LineBoss.PressShop.Overhead.CanonicalLifecycleIntegrationReceipt",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPressShopOverheadCanonicalLifecycleReceiptTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBPressShopOverheadLifecycleValidationPrivate;

    FString Reason;
    FFactoryFixture Fixture;
    if (!TestTrue(TEXT("canonical OneFactory fixture commissions"),
            Fixture.Create(Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }

    TArray<FLBOneFactoryRuntimeStationStep> ReceiptRoute;
    FName ReceiptTopologyId;
    const bool bV002RouteProfilePresent = Fixture.Coordinator
            ->GetConfiguredStationRoute(
                ReceiptRoute, ReceiptTopologyId, Reason)
        && ReceiptTopologyId.ToString().StartsWith(
            TEXT("OF_RUNTIME_TOPOLOGY_V002_"))
        && ReceiptRoute.IsValidIndex(5)
        && ReceiptRoute[5].SemanticStage ==
            ELBOneFactoryVehicleStage::PressPanelInspection
        && ReceiptRoute[5].bQualityGate;
    TestTrue(TEXT("receipt binds explicitly to the V002 Press route profile"),
        bV002RouteProfilePresent);

    TArray<FLayerProbe> Layers;
    ALBPressShopOverheadVisualLayerActor* CartLayer = nullptr;
    AddExhaustiveLayerMatrix(Fixture, Layers, CartLayer);
    Fixture.Presentation = Fixture.World->SpawnActor<
        ALBPressShopOverheadPresentationActor>();
    if (!TestNotNull(TEXT("native overhead adapter spawns"),
            Fixture.Presentation)
        || !TestNotNull(TEXT("authored coil-cart probe spawns"), CartLayer))
    {
        Fixture.Destroy();
        return false;
    }
    Fixture.Presentation->Tick(0.0f);
    TestTrue(TEXT("all exhaustive probe layers bind"),
        Fixture.Presentation->GetBoundVisualLayerCount() == Layers.Num());
    TestTrue(TEXT("coil cart receives the sole authored mover range"),
        CartLayer->bHasMotionRange
        && CartLayer->MotionStart.GetLocation().Equals(
            FVector(1000.0, 200.0, 10.0), 0.01)
        && CartLayer->MotionEnd.GetLocation().Equals(
            FVector(1320.0, 200.0, 10.0), 0.01));

    FName UnitId;
    if (!TestTrue(TEXT("one canonical evidence unit starts"),
            Fixture.CreateAndStartUnit(UnitId, Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }

    const FLBOneFactoryProductionLedgerState StartedLedger =
        Fixture.Production->CaptureLedger();
    const FLBOneFactoryVehicleUnitState* StartedUnit =
        StartedLedger.Units.FindByPredicate([UnitId](
            const FLBOneFactoryVehicleUnitState& Unit)
            { return Unit.UnitId == UnitId; });
    const bool bUnitPersistsV002Profile = StartedUnit
        && StartedUnit->RouteProfileVersion ==
            ULBOneFactoryProductionFlowLibrary::
                PressInspectionRouteProfileV002
        && StartedUnit->RuntimeTopologyId == ReceiptTopologyId;
    TestTrue(TEXT("evidence unit persists V002 profile and topology"),
        bUnitPersistsV002Profile);

    TArray<TSharedPtr<FJsonValue>> Checkpoints;
    bool bLifecyclePass = bV002RouteProfilePresent
        && bUnitPersistsV002Profile;
    auto Check = [&](const FExpectedCheckpoint& Expected)
    {
        bLifecyclePass = CaptureCheckpoint(*this, Fixture, UnitId, Expected,
            Layers, CartLayer, Checkpoints, Reason) && bLifecyclePass;
    };

    Check({TEXT("INBOUND_LORRY_UNLOAD"),
        LBOneFactoryPressStarterIds::InboundReceiving(), 0.20f,
        {TEXT("IN01_ARTICULATED_CARRIER")}, {},
        TEXT("IN01_ARTICULATED_CARRIER"), TEXT("UNLOADING")});
    Check({TEXT("INBOUND_COIL_AGV_TRANSFER"),
        LBOneFactoryPressStarterIds::InboundReceiving(), 0.75f,
        {TEXT("IN02_COIL_HANDLER_AGV")},
        {TEXT("IN02_COIL_HANDLER_AGV")},
        TEXT("IN02_COIL_HANDLER_AGV"), TEXT("TRANSFER")});
    bLifecyclePass = AdvanceStation(Fixture, UnitId,
        LBOneFactoryPressStarterIds::InboundReceiving(), Reason)
        && bLifecyclePass;

    Check({TEXT("WRAPPED_COIL_STORAGE"),
        LBOneFactoryPressStarterIds::WrappedCoilStorage(), 0.50f,
        {TEXT("IN03_COIL_STORAGE")}, {},
        TEXT("IN03_COIL_STORAGE"), TEXT("STORE")});
    bLifecyclePass = AdvanceStation(Fixture, UnitId,
        LBOneFactoryPressStarterIds::WrappedCoilStorage(), Reason)
        && bLifecyclePass;

    Check({TEXT("DEPACK_ROLLERS"),
        LBOneFactoryPressStarterIds::BlankPreparation(), 0.05f,
        {TEXT("IN04_DEPACK")}, {}, TEXT("IN04_DEPACK"),
        TEXT("ROLLERS")});
    Check({TEXT("DEPACK_WRAP_REMOVE"),
        LBOneFactoryPressStarterIds::BlankPreparation(), 0.20f,
        {TEXT("IN04_DEPACK")}, {}, TEXT("IN04_DEPACK"),
        TEXT("WRAP_REMOVE")});
    Check({TEXT("DEPACK_VISION_INSPECT"),
        LBOneFactoryPressStarterIds::BlankPreparation(), 0.32f,
        {TEXT("IN04_DEPACK")}, {}, TEXT("IN04_DEPACK"),
        TEXT("VISION_INSPECT")});
    Check({TEXT("COIL_PREPARATION_FEED"),
        LBOneFactoryPressStarterIds::BlankPreparation(), 0.70f,
        {TEXT("IN05_COIL_PREP")}, {}, TEXT("IN05_COIL_PREP"),
        TEXT("FEED")});
    Check({TEXT("COIL_PREPARATION_TRANSFER"),
        LBOneFactoryPressStarterIds::BlankPreparation(), 0.90f,
        {TEXT("IN05_COIL_PREP")}, {TEXT("IN05_COIL_PREP")},
        TEXT("IN05_COIL_PREP"), TEXT("FEED")});
    bLifecyclePass = AdvanceStation(Fixture, UnitId,
        LBOneFactoryPressStarterIds::BlankPreparation(), Reason)
        && bLifecyclePass;

    FExpectedCheckpoint CartCheckpoint;
    CartCheckpoint.CheckpointId = TEXT("S01_COIL_CART_MID_TRANSFER");
    CartCheckpoint.StationId =
        LBOneFactoryPressStarterIds::PreparedBlankBuffer();
    CartCheckpoint.Progress01 = 0.18f;
    CartCheckpoint.ActiveMachines = {TEXT("S01_DESTACK_LOAD")};
    CartCheckpoint.PoseMachine = TEXT("S01_DESTACK_LOAD");
    CartCheckpoint.PoseState = TEXT("LOAD");
    CartCheckpoint.bCheckCartTransform = true;
    CartCheckpoint.ExpectedCartLocation = FVector(1160.0, 200.0, 10.0);
    Check(CartCheckpoint);

    FExpectedCheckpoint PayoffCheckpoint;
    PayoffCheckpoint.CheckpointId = TEXT("S01_PAYOFF_AND_STRIP_FEED");
    PayoffCheckpoint.StationId =
        LBOneFactoryPressStarterIds::PreparedBlankBuffer();
    PayoffCheckpoint.Progress01 = 0.68f;
    PayoffCheckpoint.ActiveMachines = {TEXT("S01_DESTACK_LOAD")};
    PayoffCheckpoint.PoseMachine = TEXT("S01_DESTACK_LOAD");
    PayoffCheckpoint.PoseState = TEXT("LOAD");
    PayoffCheckpoint.ExpectedS01SequenceFrames = 1;
    PayoffCheckpoint.bCheckCartTransform = true;
    PayoffCheckpoint.ExpectedCartLocation = FVector(1320.0, 200.0, 10.0);
    Check(PayoffCheckpoint);

    Check({TEXT("S01_PREPARED_BLANK_TRANSFER"),
        LBOneFactoryPressStarterIds::PreparedBlankBuffer(), 0.90f,
        {TEXT("S01_DESTACK_LOAD")}, {TEXT("S01_DESTACK_LOAD")},
        TEXT("S01_DESTACK_LOAD"), TEXT("LOAD"), NAME_None,
        ELBPressShopOverheadPressFrame::Open, 1});
    bLifecyclePass = AdvanceStation(Fixture, UnitId,
        LBOneFactoryPressStarterIds::PreparedBlankBuffer(), Reason)
        && bLifecyclePass;

    const FName PressMachines[] = {
        TEXT("S02_DEEP_DRAW"), TEXT("S03_FORM"), TEXT("S04_TRIM"),
        TEXT("S05_PIERCE"), TEXT("S06_FLANGE")
    };
    for (int32 PressIndex = 0; PressIndex < 5; ++PressIndex)
    {
        FExpectedCheckpoint PressCheckpoint;
        PressCheckpoint.CheckpointId = FString::Printf(
            TEXT("%s_CONTACT"), *PressMachines[PressIndex].ToString());
        PressCheckpoint.StationId = LBOneFactoryPressStarterIds::PressTrain();
        PressCheckpoint.Progress01 =
            (static_cast<float>(PressIndex) + 0.60f) / 5.0f;
        PressCheckpoint.ActiveMachines = {PressMachines[PressIndex]};
        PressCheckpoint.ActivePress = PressMachines[PressIndex];
        PressCheckpoint.PressFrame =
            ELBPressShopOverheadPressFrame::Contact;
        Check(PressCheckpoint);
    }
    Check({TEXT("S06_TO_INSPECTION_TRANSFER"),
        LBOneFactoryPressStarterIds::PressTrain(), 0.99f,
        {TEXT("S06_FLANGE"), TEXT("SUPPORT_FLEET")},
        {TEXT("S06_FLANGE"), TEXT("SUPPORT_FLEET")},
        TEXT("SUPPORT_FLEET"), TEXT("TRANSFER"), TEXT("S06_FLANGE"),
        ELBPressShopOverheadPressFrame::Open});
    bLifecyclePass = AdvanceStation(Fixture, UnitId,
        LBOneFactoryPressStarterIds::PressTrain(), Reason)
        && bLifecyclePass;

    Check({TEXT("S07_INSPECTION_PICK"),
        LBOneFactoryPressStarterIds::PanelInspection(), 0.30f,
        {TEXT("S07_INSPECTION")}, {}, TEXT("S07_INSPECTION"),
        TEXT("PICK")});
    Check({TEXT("S07_INSPECTION_SCAN"),
        LBOneFactoryPressStarterIds::PanelInspection(), 0.60f,
        {TEXT("S07_INSPECTION")}, {}, TEXT("S07_INSPECTION"),
        TEXT("INSPECT")});
    Check({TEXT("S07_INSPECTION_PLACE"),
        LBOneFactoryPressStarterIds::PanelInspection(), 0.90f,
        {TEXT("S07_INSPECTION")}, {TEXT("S07_INSPECTION")},
        TEXT("S07_INSPECTION"), TEXT("PLACE")});

    FLBOneFactoryRuntimeVehicleStatus InspectionStatus;
    const bool bInspectionQualityGatePresent = Fixture.Coordinator
            ->GetVehicleRuntimeStatus(
            UnitId, InspectionStatus, Reason)
        && InspectionStatus.CurrentStationId
            == LBOneFactoryPressStarterIds::PanelInspection()
        && InspectionStatus.bAtQualityGate;
    TestTrue(TEXT("Press panel inspection exposes a real quality-decision gate"),
        bInspectionQualityGatePresent);
    bLifecyclePass = bInspectionQualityGatePresent && bLifecyclePass;
    bLifecyclePass = AdvanceStation(Fixture, UnitId,
        LBOneFactoryPressStarterIds::PanelInspection(), Reason)
        && bLifecyclePass;
    FLBOneFactoryRuntimeVehicleStatus InspectionHold;
    const bool bInspectionHeld = Fixture.Coordinator
            ->GetVehicleRuntimeStatus(UnitId, InspectionHold, Reason)
        && InspectionHold.CurrentStationId
            == LBOneFactoryPressStarterIds::PanelInspection()
        && InspectionHold.bAwaitingQualityResult;
    TestTrue(TEXT("Completed Press inspection cycle holds for player evidence"),
        bInspectionHeld);
    bLifecyclePass = bInspectionHeld && bLifecyclePass;
    const bool bInspectionPassed = Fixture.Coordinator
        ->SubmitRuntimeQualityResult(UnitId,
            ELBOneFactoryVehicleQualityState::Passed,
            TEXT("OVERHEAD_PRESS_PANEL_INSPECTION_PASS"), Reason);
    TestTrue(TEXT("Press inspection accepts unique passing evidence"),
        bInspectionPassed);
    bLifecyclePass = bInspectionPassed && bLifecyclePass;
    const bool bInspectionReleased = bInspectionPassed
        && Fixture.Coordinator->TickVehicle(UnitId, 0.1f, Reason);
    TestTrue(TEXT("Passed Press inspection releases to panel dispatch"),
        bInspectionReleased);
    bLifecyclePass = bInspectionReleased && bLifecyclePass;

    Check({TEXT("S07_PALLETISER_PICK"),
        LBOneFactoryPressStarterIds::PanelDispatch(), 0.35f,
        {TEXT("S07_PALLETISER")}, {}, TEXT("S07_PALLETISER"),
        TEXT("PICK")});
    Check({TEXT("S07_PALLETISER_PLACE"),
        LBOneFactoryPressStarterIds::PanelDispatch(), 0.70f,
        {TEXT("S07_PALLETISER")}, {}, TEXT("S07_PALLETISER"),
        TEXT("PLACE")});
    Check({TEXT("OUTBOUND_PANEL_STILLAGE_TRANSFER"),
        LBOneFactoryPressStarterIds::PanelDispatch(), 0.90f,
        {TEXT("S07_PALLETISER"), TEXT("SUPPORT_FLEET")},
        {TEXT("S07_PALLETISER"), TEXT("SUPPORT_FLEET")},
        TEXT("S07_PALLETISER"), TEXT("PARKED")});

    bLifecyclePass = AdvanceStation(Fixture, UnitId,
        LBOneFactoryPressStarterIds::PanelDispatch(), Reason)
        && bLifecyclePass;
    FLBOneFactoryRuntimeVehicleStatus BodyHandoff;
    const bool bPressHandoffPass = Fixture.Coordinator
            ->GetVehicleRuntimeStatus(UnitId, BodyHandoff, Reason)
        && BodyHandoff.StationCursor == 7
        && BodyHandoff.Department == ELBOneFactoryDepartment::Body
        && BodyHandoff.Stage == ELBOneFactoryVehicleStage::BodyFraming;
    TestTrue(TEXT("press dispatch hands the same UnitId to Body/Weld"),
        bPressHandoffPass);
    bLifecyclePass = bPressHandoffPass && bLifecyclePass;

    Fixture.Presentation->Tick(0.0f);
    FString RefreshReason;
    const bool bPostHandoffRefresh =
        Fixture.Presentation->RefreshFromRuntime(RefreshReason);
    int32 VisiblePressWorkpieces = 0;
    for (const FLayerProbe& Probe : Layers)
    {
        if (Probe.Role == ELBPressShopOverheadLayerRole::Workpiece
            && IsLayerVisible(Probe))
        {
            ++VisiblePressWorkpieces;
        }
    }
    const bool bPressVisualsClear = bPostHandoffRefresh
        && VisiblePressWorkpieces == 0;
    TestTrue(TEXT("press workpiece layers clear after exact handoff"),
        bPressVisualsClear);
    bLifecyclePass = bPressVisualsClear && bLifecyclePass;

    FString ReceiptPath;
    const bool bReceiptWritten = WriteReceipt(UnitId, ReceiptTopologyId,
        ULBOneFactoryProductionFlowLibrary::PressInspectionRouteProfileV002,
        bLifecyclePass,
        bPressHandoffPass, bInspectionQualityGatePresent,
        Checkpoints, ReceiptPath);
    TestTrue(TEXT("machine-readable lifecycle receipt is written"),
        bReceiptWritten);
    if (bReceiptWritten)
    {
        AddInfo(FString::Printf(TEXT("Receipt: %s"), *ReceiptPath));
    }

    Fixture.Destroy();
    return !HasAnyErrors();
}

#endif
