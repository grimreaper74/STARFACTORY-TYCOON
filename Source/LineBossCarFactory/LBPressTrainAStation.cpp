#include "LBPressTrainAStation.h"
#include "LBVehiclePanelCatalog.h"

#include "Components/AudioComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWave.h"
#include "UObject/ConstructorHelpers.h"
#include "Engine/TextRenderActor.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Materials/MaterialInterface.h"
#include "LBPressTrainIdentitySubsystem.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBStatusBeaconComponent.h"

#define LOCTEXT_NAMESPACE "CairnwellPressTrainA"

namespace
{
    constexpr int32 ApprovedTrainModuleCount = 95;
    // Engine-measured production fit. At 10.07 m pitch the 5.57 m press shell
    // and scale-2 transfer assembly retain about 25 cm on both sides. S02 also
    // begins about 25 cm after S01, so the train reads as one connected machine.
    constexpr float PressStageSpacingCm = 1007.0f;
    constexpr float FirstPressStageYcm = 654.0f;
    constexpr float TransferRootFromUpstreamStageYcm = 503.188f;
    constexpr float TransferPitchSourceYcm = -527.413f;
    constexpr float TransferPitchDestinationYcm =
        TransferPitchSourceYcm + PressStageSpacingCm;
    constexpr float TransferGroundZcm = 109.0f;
    constexpr float TransferSheetContactLiftZcm = 201.923f;
    constexpr float TransferClearanceLiftZcm = 60.0f;
    constexpr float S07StageYcm = 5684.0f;
    constexpr float OutputPortYcm = 6284.0f;
    constexpr float ProcessDatumZcm = 202.221f;
    constexpr float DestackLiftTravelCm = 120.0f;
    constexpr float DestackBlankRestZcm = ProcessDatumZcm - DestackLiftTravelCm;
    constexpr float S03StrokeCm = 65.0f;
    // Every v735 press part shares the same source origin. Unreal's audited local
    // bounds put the shell floor at -410.819 cm and the closed upper-die underside
    // at -208.953 cm after the accepted 6.57 scale. This common lift seats the shell
    // within 2 mm of Z=0 while landing the die within 2 mm of ProcessDatumZcm.
    constexpr float CompletePressSharedOriginZcm = 410.997f;
}

FBox ALBPressTrainAStation::GetProtectedLocalEnvelope()
{
    // The actor root remains the S01/infeed datum. The compact owner-approved stage
    // pitch brings the five presses around their transfers while preserving the S07
    // robot service aisle and honest connection-port clearance.
    return FBox(FVector(-750.0f, -750.0f, 0.0f), FVector(750.0f, 6534.0f, 950.0f));
}

ALBPressTrainAStation::ALBPressTrainAStation()
{
    PrimaryActorTick.bCanEverTick = true;
    PersistentTrainGuid = FGuid::NewGuid();
    StationRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PTA_StationRoot"));
    SetRootComponent(StationRoot);

    const float CellBeaconY[] = {0.0f, FirstPressStageYcm,
        FirstPressStageYcm + PressStageSpacingCm,
        FirstPressStageYcm + 2.0f * PressStageSpacingCm,
        FirstPressStageYcm + 3.0f * PressStageSpacingCm,
        FirstPressStageYcm + 4.0f * PressStageSpacingCm, S07StageYcm};
    for (int32 CellIndex = 0; CellIndex < UE_ARRAY_COUNT(CellBeaconY); ++CellIndex)
    {
        ULBStatusBeaconComponent* Beacon = CreateDefaultSubobject<ULBStatusBeaconComponent>(
            FName(*FString::Printf(TEXT("PTA_CellS%02d_StatusBeacon"), CellIndex + 1)));
        Beacon->SetupAttachment(StationRoot);
        Beacon->SetRelativeLocation(FVector(-520.0f, CellBeaconY[CellIndex],
            CellIndex == 0 || CellIndex == 6 ? 650.0f : 820.0f));
        Beacon->SetRelativeScale3D(FVector(0.80f));
        Beacon->SetStatus(ELBStatusBeaconState::Stopped);
        CellStatusBeacons.Add(Beacon);
    }

    FactoryInputPort = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("PTA_FactoryInputPort"));
    FactoryInputPort->SetupAttachment(StationRoot);
    FactoryInputPort->Direction = ELBFactoryPortDirection::Input;
    FactoryInputPort->ProcessStage = LBFactoryProcessStage::PressTrain;
    FactoryInputPort->MaterialClass = ELBFactoryMaterialClass::Blank;
    FactoryInputPort->TransportKind = ELBFactoryTransportKind::RollerConveyor;
    FactoryInputPort->MaximumAutomaticLinkDistanceCm = 2500.0f;
    FactoryInputPort->PortId = TEXT("TRAIN_A-IN");
    FactoryInputPort->SetRelativeLocation(FVector(0.0f, -500.0f, 110.0f));
    FactoryOutputPort = CreateDefaultSubobject<ULBFactoryProcessPortComponent>(TEXT("PTA_FactoryOutputPort"));
    FactoryOutputPort->SetupAttachment(StationRoot);
    FactoryOutputPort->Direction = ELBFactoryPortDirection::Output;
    FactoryOutputPort->ProcessStage = LBFactoryProcessStage::PressTrain;
    FactoryOutputPort->MaterialClass = ELBFactoryMaterialClass::FormedPanel;
    FactoryOutputPort->TransportKind = ELBFactoryTransportKind::PanelTransfer;
    FactoryOutputPort->MaximumAutomaticLinkDistanceCm = 2500.0f;
    FactoryOutputPort->MaximumConnections = 4;
    FactoryOutputPort->PortId = TEXT("TRAIN_A-OUT");
    FactoryOutputPort->SetRelativeLocation(FVector(0.0f, OutputPortYcm, 110.0f));

    // The untouched Walker throat defines the 2.02221 m sheet datum. The compact
    // transfer kinematics place the v746 cup low/suction face on that datum at each
    // throat. Public ports remain at 1.10 m; S01/S07 are the vertical adapter cells.
    InternalProcessPanelDatum = CreateDefaultSubobject<USceneComponent>(TEXT("PTA_InternalProcessPanelDatum"));
    InternalProcessPanelDatum->SetupAttachment(StationRoot);
    InternalProcessPanelDatum->SetRelativeLocation(FVector(0.0f, 500.0f, ProcessDatumZcm));

    CompletedRuntimeVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PTA_CompletedRuntimeVisual"));
    CompletedRuntimeVisual->SetupAttachment(StationRoot);
    CompletedRuntimeVisual->SetRelativeTransform(FTransform::Identity);
    CompletedRuntimeVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    CompletedRuntimeVisual->SetGenerateOverlapEvents(false);
    CompletedRuntimeVisual->SetCanEverAffectNavigation(false);
    CompletedRuntimeVisual->SetVisibility(false);
    CompletedRuntimeVisual->SetHiddenInGame(true);
    // Keep the production-safe six-part Walker press while the more detailed v658
    // assembly remains off the live line: its throat is 80 cm above this train's
    // validated transfer datum. Visual upgrades must not break panel flow.
    const TCHAR* CompletePressRoot = TEXT("/Game/LineBoss/Developer/Validation/PressTrains/NewRigidIntake_v741/Cairnwell_S03_Movable_v632Controls_v735/StaticMeshes");
    const TCHAR* CompletePressPartNames[] = {TEXT("S03_STATIC_SHELL"), TEXT("S03_RAM_SLIDE"),
        TEXT("S03_UPPER_DIE"), TEXT("S03_LOWER_DIE_BOLSTER")};
    UStaticMesh* CompletePressMeshes[UE_ARRAY_COUNT(CompletePressPartNames)] = {};
    for (int32 Part = 0; Part < UE_ARRAY_COUNT(CompletePressPartNames); ++Part)
    {
        const FString Path = FString::Printf(TEXT("%s/%s.%s"), CompletePressRoot,
            CompletePressPartNames[Part], CompletePressPartNames[Part]);
        CompletePressMeshes[Part] = LoadObject<UStaticMesh>(nullptr, *Path);
    }
    static ConstructorHelpers::FObjectFinder<UStaticMesh> TransferFrameMesh(TEXT("/Game/LineBoss/Developer/Validation/PressTrains/SegmentedTransferRuntime_v747/Cairnwell_InterPressTransfer_Runtime_v746/StaticMeshes/SM_CA_PT_SEG__TIC_FRAME_v746"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> TransferCrossbeamMesh(TEXT("/Game/LineBoss/Developer/Validation/PressTrains/SegmentedTransferRuntime_v747/Cairnwell_InterPressTransfer_Runtime_v746/StaticMeshes/SM_CA_PT_SEG__CROSSBEAM_v746.SM_CA_PT_SEG__CROSSBEAM_v746"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> TransferActuatorMesh(TEXT("/Game/LineBoss/Developer/Validation/PressTrains/SegmentedTransferRuntime_v747/Cairnwell_InterPressTransfer_Runtime_v746/StaticMeshes/SM_CA_PT_SEG__ATOR_PACK_v746.SM_CA_PT_SEG__ATOR_PACK_v746"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> TransferCupArrayMesh(TEXT("/Game/LineBoss/Developer/Validation/PressTrains/SegmentedTransferRuntime_v747/Cairnwell_InterPressTransfer_Runtime_v746/StaticMeshes/SM_CA_PT_SEG_CUP_ARRAY_v746.SM_CA_PT_SEG_CUP_ARRAY_v746"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S07PortalMesh(TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260810_v950/S07Portal/Cairnwell_S07_InspectionUnload_NewPortal_v949/StaticMeshes/Cairnwell_S07_NewPortal_v949.Cairnwell_S07_NewPortal_v949"));
    const TCHAR* ApprovedS01Root = TEXT("/Game/LineBoss/Developer/Validation/BlenderApproved_v940/S01/Cairnwell_S01_Destack_HandPaintedSplit_v937/StaticMeshes");
    const FString ApprovedS01P0Path = FString::Printf(TEXT("%s/S01_StaticStructure_P0.S01_StaticStructure_P0"), ApprovedS01Root);
    CompletedRuntimeVisual->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, *ApprovedS01P0Path));
    // The approved Blender master flows along local +X. The player train flows along
    // local +Y, so rotate every authored S01 part together by +90 degrees at station 1.
    CompletedRuntimeVisual->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
    ApprovedModularTrainVisuals.Add(CompletedRuntimeVisual);

    const auto CreateApprovedModule = [this](const FName Name, UStaticMesh* Mesh,
        const FVector& Location, const FRotator& Rotation, USceneComponent* Parent = nullptr)
    {
        UStaticMeshComponent* Component = CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Component->SetupAttachment(Parent ? Parent : StationRoot.Get());
        Component->SetStaticMesh(Mesh);
        Component->SetRelativeLocation(Location);
        Component->SetRelativeRotation(Rotation);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetVisibility(false);
        Component->SetHiddenInGame(true);
        ApprovedModularTrainVisuals.Add(Component);
        return Component;
    };
    const auto CreateMover = [this](const TCHAR* Name)
    {
        USceneComponent* Mover = CreateDefaultSubobject<USceneComponent>(Name);
        Mover->SetupAttachment(StationRoot);
        Mover->SetMobility(EComponentMobility::Movable);
        return Mover;
    };
    DestackLiftMover = CreateMover(TEXT("PTA_DestackLiftMover"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> DestackFeedBlankMesh(
        TEXT("/Game/LineBoss/Candidates/PressTrains/TrainA/Fabrication_v030/Imported/PTA_S01_SeparatedFeedBlank_v002_Mesh.PTA_S01_SeparatedFeedBlank_v002_Mesh"));
    DestackFeedBlankVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PTA_DestackFeedBlankVisual"));
    DestackFeedBlankVisual->SetupAttachment(DestackLiftMover);
    DestackFeedBlankVisual->SetStaticMesh(DestackFeedBlankMesh.Object);
    // The audited source mesh is stored at centimetre/100 scale. Resting 1.20 m below
    // the press datum lets the native lift deliver its centre exactly to the verified
    // 2.02221 m transfer plane at peak destack, without inventing a car-specific shape.
    DestackFeedBlankVisual->SetRelativeLocation(FVector(0.0f, 0.0f, DestackBlankRestZcm));
    DestackFeedBlankVisual->SetRelativeScale3D(FVector(100.0f));
    DestackFeedBlankVisual->SetMobility(EComponentMobility::Movable);
    DestackFeedBlankVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    DestackFeedBlankVisual->SetGenerateOverlapEvents(false);
    DestackFeedBlankVisual->SetCanEverAffectNavigation(false);
    DestackFeedBlankVisual->SetVisibility(false);
    DestackFeedBlankVisual->SetHiddenInGame(true);
    S02SlideMover = CreateMover(TEXT("PTA_S02SlideMover"));
    S03SlideMover = CreateMover(TEXT("PTA_S03SlideMover"));
    S04SlideMover = CreateMover(TEXT("PTA_S04SlideMover"));
    S05SlideMover = CreateMover(TEXT("PTA_S05SlideMover"));
    S06SlideMover = CreateMover(TEXT("PTA_S06SlideMover"));
    UnloadRobotMover = CreateMover(TEXT("PTA_UnloadRobotMover"));
    FormedPanelMover = CreateMover(TEXT("PTA_FormedPanelMover"));
    for (int32 PartIndex = 1; PartIndex < 52; ++PartIndex)
    {
        const FString AssetName = FString::Printf(TEXT("S01_StaticStructure_P%d"), PartIndex);
        const FString AssetPath = FString::Printf(TEXT("%s/%s.%s"), ApprovedS01Root, *AssetName, *AssetName);
        if (UStaticMesh* PartMesh = LoadObject<UStaticMesh>(nullptr, *AssetPath))
            CreateApprovedModule(FName(*FString::Printf(TEXT("PTA_ApprovedS01Part%02d"), PartIndex)),
                PartMesh, FVector::ZeroVector, FRotator(0.0f, 90.0f, 0.0f));
    }
    bool bCompletePressAvailable = true;
    for (UStaticMesh* Mesh : CompletePressMeshes) bCompletePressAvailable &= Mesh != nullptr;
    if (bCompletePressAvailable)
    {
        constexpr float PressScale = 6.57f;
        const FRotator PressRotation = FRotator::ZeroRotator;
        USceneComponent* StageMovers[] = {S02SlideMover.Get(), S03SlideMover.Get(),
            S04SlideMover.Get(), S05SlideMover.Get(), S06SlideMover.Get()};
        for (int32 Index = 0; Index < 5; ++Index)
        {
            for (int32 Part = 0; Part < UE_ARRAY_COUNT(CompletePressMeshes); ++Part)
            {
                USceneComponent* Parent = (Part == 1 || Part == 2)
                    ? StageMovers[Index] : StationRoot.Get();
                UStaticMeshComponent* PressPart = CreateApprovedModule(
                    FName(*FString::Printf(TEXT("PTA_ApprovedPressS%02d_Part%02d"), Index + 2, Part)),
                    CompletePressMeshes[Part], FVector(0.0f,
                        FirstPressStageYcm + Index * PressStageSpacingCm,
                        CompletePressSharedOriginZcm),
                    PressRotation, Parent);
                PressPart->SetRelativeScale3D(FVector(PressScale));
                // Keep the supplied press finish intact: the authored green structure,
                // white service hardware, dark running gear and yellow guards are what
                // make this read as a Cairnwell robotic press rather than a grey proxy.
                if (Part == 1 || Part == 2)
                    PressPart->SetMobility(EComponentMobility::Movable);
            }
        }
    }    if (TransferFrameMesh.Succeeded() && TransferCrossbeamMesh.Succeeded()
        && TransferActuatorMesh.Succeeded() && TransferCupArrayMesh.Succeeded())
    {
        UStaticMesh* TransferMeshes[] = {TransferFrameMesh.Object, TransferCrossbeamMesh.Object,
            TransferActuatorMesh.Object, TransferCupArrayMesh.Object};
        const TCHAR* TransferPartNames[] = {TEXT("Frame"), TEXT("Crossbeam"), TEXT("Actuator"), TEXT("CupArray")};
        // The owner-approved middle fit is large enough to handle a body blank while
        // leaving the presses tight to the fixed frame. Preserve all authored origins.
        const FRotator TransferRotation(0.0f, 90.0f, 0.0f);
        const FVector TransferAssemblyScale(2.0f);
        for (int32 Gap = 0; Gap < 4; ++Gap)
        {
            // Engine asset bounds put the equal-clearance frame centre 5.03188 m
            // beyond the upstream press datum, just off the geometric midpoint.
            const float UpstreamStageY = FirstPressStageYcm + Gap * PressStageSpacingCm;
            const FVector TransferOrigin(0.0f,
                UpstreamStageY + TransferRootFromUpstreamStageYcm, TransferGroundZcm);
            USceneComponent* GapRoot = CreateDefaultSubobject<USceneComponent>(
                FName(*FString::Printf(TEXT("PTA_ApprovedTransfer%02d_Root"), Gap + 1)));
            GapRoot->SetupAttachment(StationRoot);
            GapRoot->SetRelativeLocation(TransferOrigin);
            ApprovedTransferGapRoots.Add(GapRoot);

            const FName LiftName = Gap == 0
                ? FName(TEXT("PTA_TransferLiftMover"))
                : FName(*FString::Printf(TEXT("PTA_ApprovedTransfer%02d_LiftMover"), Gap + 1));
            USceneComponent* GapLiftMover = CreateDefaultSubobject<USceneComponent>(LiftName);
            GapLiftMover->SetupAttachment(GapRoot);
            GapLiftMover->SetMobility(EComponentMobility::Movable);
            // All accepted v746 parts share one authored origin. Keep the moving
            // tooling assembled into the fixed frame while idle; pickup offsets are
            // applied only during the explicit source-to-destination motion cycle.
            GapLiftMover->SetRelativeLocation(FVector::ZeroVector);
            ApprovedTransferLiftMovers.Add(GapLiftMover);

            const FName PitchName = Gap == 0
                ? FName(TEXT("PTA_TransferPitchMover"))
                : FName(*FString::Printf(TEXT("PTA_ApprovedTransfer%02d_PitchMover"), Gap + 1));
            USceneComponent* GapPitchMover = CreateDefaultSubobject<USceneComponent>(PitchName);
            GapPitchMover->SetupAttachment(GapLiftMover);
            GapPitchMover->SetMobility(EComponentMobility::Movable);
            GapPitchMover->SetRelativeLocation(FVector::ZeroVector);
            ApprovedTransferPitchMovers.Add(GapPitchMover);

            if (Gap == 0)
            {
                TransferLiftMover = GapLiftMover;
                TransferPitchMover = GapPitchMover;
            }

            for (int32 Part = 0; Part < UE_ARRAY_COUNT(TransferMeshes); ++Part)
            {
                USceneComponent* PartParent = Part == 0 ? GapRoot : GapPitchMover;
                UStaticMeshComponent* TransferPart = CreateApprovedModule(
                    FName(*FString::Printf(TEXT("PTA_ApprovedTransfer%02d_%s"), Gap + 1, TransferPartNames[Part])),
                    TransferMeshes[Part], FVector::ZeroVector, TransferRotation, PartParent);
                TransferPart->SetRelativeScale3D(TransferAssemblyScale);
                if (Part > 0) TransferPart->SetMobility(EComponentMobility::Movable);
            }
        }
    }
    // Rotate the complete unload robot around its own grounded base rather than around
    // the press-train origin. The split meshes preserve one shared authored origin.
    UnloadRobotMover->SetRelativeLocation(FVector(-300.0f, S07StageYcm, 130.0f));
    const TCHAR* S07Parts[] = {TEXT("Base"), TEXT("Turn"), TEXT("Lower"), TEXT("Upper"), TEXT("Wrist"), TEXT("Tool")};
    for (const TCHAR* Part : S07Parts)
    {
        const FString Path = FString::Printf(TEXT("/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v788/S07ConnectedVacuumTool/Cairnwell_S07_UnloadRobot_ShortNames_v787/StaticMeshes/S07_%s.S07_%s"), Part, Part);
        if (UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *Path))
        {
            UStaticMeshComponent* RobotPart = CreateApprovedModule(
                FName(*FString::Printf(TEXT("PTA_ApprovedS07%s"), Part)), Mesh,
                FVector::ZeroVector, FRotator(0.0f, -90.0f, 0.0f), UnloadRobotMover.Get());
            RobotPart->SetMobility(EComponentMobility::Movable);
        }
    }
    if (S07PortalMesh.Succeeded())
        CreateApprovedModule(TEXT("PTA_ApprovedS07InspectionPortal"), S07PortalMesh.Object,
            FVector(0.0f, S07StageYcm, 0.0f), FRotator(0.0f, 90.0f, 0.0f));

    const auto CreateTrainIdentity = [this](const TCHAR* Name, const FVector& Location,
        const FRotator& Rotation)
    {
        UTextRenderComponent* Text = CreateDefaultSubobject<UTextRenderComponent>(Name);
        Text->SetupAttachment(StationRoot);
        Text->SetRelativeLocation(Location);
        Text->SetRelativeRotation(Rotation);
        Text->SetHorizontalAlignment(EHTA_Center);
        Text->SetVerticalAlignment(EVRTA_TextCenter);
        Text->SetWorldSize(58.0f);
        Text->SetTextRenderColor(FColor(245, 245, 235));
        Text->SetText(FText::FromString(TEXT("PRESS TRAIN")));
        Text->SetVisibility(false);
        Text->SetHiddenInGame(true);
        Text->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Text->SetCanEverAffectNavigation(false);
        return Text;
    };
    // The completed assembly flows along local Y. Put one identity at each end so it reads
    // from the material-flow approaches without long floating broadside lettering.
    TrainIdentityOperatorSide = CreateTrainIdentity(TEXT("PTA_IdentityOperatorSide"),
        FVector(0.0f, -520.0f, 720.0f), FRotator(0.0f, -90.0f, 0.0f));
    TrainIdentityServiceSide = CreateTrainIdentity(TEXT("PTA_IdentityServiceSide"),
        FVector(0.0f, OutputPortYcm - 20.0f, 720.0f), FRotator(0.0f, 90.0f, 0.0f));

    const auto CreateSpatialAudio = [this](const TCHAR* Name, const FVector& RelativeLocation,
        const float InnerRadius, const float FalloffDistance)
    {
        UAudioComponent* Component = CreateDefaultSubobject<UAudioComponent>(Name);
        Component->SetupAttachment(StationRoot);
        Component->SetRelativeLocation(RelativeLocation);
        Component->bAutoActivate = false;
        Component->bAllowSpatialization = true;
        Component->bOverrideAttenuation = true;
        Component->AttenuationOverrides.bAttenuate = true;
        Component->AttenuationOverrides.bSpatialize = true;
        Component->AttenuationOverrides.DistanceAlgorithm = EAttenuationDistanceModel::NaturalSound;
        Component->AttenuationOverrides.AttenuationShape = EAttenuationShape::Sphere;
        Component->AttenuationOverrides.AttenuationShapeExtents = FVector(InnerRadius);
        Component->AttenuationOverrides.FalloffDistance = FalloffDistance;
        Component->AttenuationOverrides.dBAttenuationAtMax = -60.0f;
        return Component;
    };
    HydraulicPowerAudio = CreateSpatialAudio(TEXT("PTA_Audio_HydraulicPower"),
        FVector(-500.0f, 2668.0f, 120.0f), 900.0f, 6200.0f);
    TransferServoAudio = CreateSpatialAudio(TEXT("PTA_Audio_TransferServo"),
        FVector(0.0f, 2668.0f, 360.0f), 650.0f, 5000.0f);
    RobotServoAudio = CreateSpatialAudio(TEXT("PTA_Audio_RobotServo"),
        FVector(0.0f, S07StageYcm, 180.0f), 450.0f, 3200.0f);
    WarningAlarmAudio = CreateSpatialAudio(TEXT("PTA_Audio_WarningAlarm"),
        FVector(650.0f, 2668.0f, 220.0f), 1000.0f, 6500.0f);
    PressCueAudio = CreateSpatialAudio(TEXT("PTA_Audio_PressCue"),
        FVector(0.0f, 2668.0f, 320.0f), 700.0f, 5600.0f);
    SafetyCueAudio = CreateSpatialAudio(TEXT("PTA_Audio_SafetyCue"),
        FVector(650.0f, 2668.0f, 180.0f), 800.0f, 6000.0f);

    const auto LoadSound = [](const TCHAR* ObjectPath) -> USoundBase*
    {
        ConstructorHelpers::FObjectFinder<USoundBase> Finder(ObjectPath);
        return Finder.Succeeded() ? Finder.Object : nullptr;
    };
    const TCHAR* AudioRoot = TEXT("/Game/LineBoss/PressTrains/TrainA/Audio/Candidate_v002/");
    USoundBase* HydraulicSound = LoadSound(*FString::Printf(TEXT("%sPTA_HydraulicPower_Loop_v002.PTA_HydraulicPower_Loop_v002"), AudioRoot));
    USoundBase* TransferSound = LoadSound(*FString::Printf(TEXT("%sPTA_TransferServo_Loop_v002.PTA_TransferServo_Loop_v002"), AudioRoot));
    USoundBase* RobotSound = LoadSound(*FString::Printf(TEXT("%sPTA_RobotServo_Loop_v002.PTA_RobotServo_Loop_v002"), AudioRoot));
    USoundBase* WarningSound = LoadSound(*FString::Printf(TEXT("%sPTA_WarningAlarm_Loop_v002.PTA_WarningAlarm_Loop_v002"), AudioRoot));
    PressStrokeSound = LoadSound(*FString::Printf(TEXT("%sPTA_PressStroke_v002.PTA_PressStroke_v002"), AudioRoot));
    ControlledStopSound = LoadSound(*FString::Printf(TEXT("%sPTA_ControlledStop_v002.PTA_ControlledStop_v002"), AudioRoot));
    GateInterlockSound = LoadSound(*FString::Printf(TEXT("%sPTA_GateInterlock_v002.PTA_GateInterlock_v002"), AudioRoot));
    EmergencyStopSound = LoadSound(*FString::Printf(TEXT("%sPTA_EmergencyStop_v002.PTA_EmergencyStop_v002"), AudioRoot));
    const auto ConfigureLoop = [](USoundBase* Sound)
    {
        if (USoundWave* Wave = Cast<USoundWave>(Sound)) Wave->bLooping = true;
    };
    ConfigureLoop(HydraulicSound);
    ConfigureLoop(TransferSound);
    ConfigureLoop(RobotSound);
    ConfigureLoop(WarningSound);
    HydraulicPowerAudio->SetSound(HydraulicSound);
    TransferServoAudio->SetSound(TransferSound);
    RobotServoAudio->SetSound(RobotSound);
    WarningAlarmAudio->SetSound(WarningSound);
}

bool ALBPressTrainAStation::EnableCompletedRuntimeVisual()
{
    // Exactly 135 approved modules: 52-part S01, five complete twelve-part presses,
    // four complete four-part traverses, the six-part S07 robot and its inspection portal.
    // The hierarchy is still one
    // player-placeable train, while its moving assemblies remain independently addressable.
    // Fail closed if any new asset is missing; never fall back to the old aggregate presses.
    if (ApprovedModularTrainVisuals.Num() != ApprovedTrainModuleCount) return false;
    for (UStaticMeshComponent* Component : ApprovedModularTrainVisuals)
    {
        if (!Component || !Component->GetStaticMesh()) return false;
        Component->SetHiddenInGame(false);
        Component->SetVisibility(true, true);
    }
    // Material presentation is state-owned rather than being a permanent 106th
    // machine module. This keeps an empty train visibly empty after placement.
    ApplyMachinePose();
    UpdateTrainIdentityPresentation();
    return true;
}

void ALBPressTrainAStation::UpdateTrainIdentityPresentation()
{
    const bool bShow = CompletedRuntimeVisual && CompletedRuntimeVisual->IsVisible()
        && !CompletedRuntimeVisual->bHiddenInGame;
    for (UTextRenderComponent* Text : {TrainIdentityOperatorSide.Get(), TrainIdentityServiceSide.Get()})
    {
        if (!Text) continue;
        Text->SetText(FText::FromString(TrainDisplayName));
        Text->SetTextRenderColor(TrainAccentColor.ToFColor(true));
        Text->SetHiddenInGame(!bShow);
        Text->SetVisibility(bShow, true);
    }
}

bool ALBPressTrainAStation::HasCompletedRuntimeVisual() const
{
    if (ApprovedModularTrainVisuals.Num() != ApprovedTrainModuleCount) return false;
    for (const UStaticMeshComponent* Component : ApprovedModularTrainVisuals)
        if (!Component || !Component->GetStaticMesh() || !Component->IsVisible() || Component->bHiddenInGame)
            return false;
    return true;
}

void ALBPressTrainAStation::BeginPlay()
{
    Super::BeginPlay();
    if (ULBPressTrainIdentitySubsystem* Identities = GetWorld()->GetSubsystem<ULBPressTrainIdentitySubsystem>())
    {
        Identities->RegisterTrain(this);
    }
    BindMapPresentation();
    ApplyMachinePose();
    UpdateHMITextPresentation();
    UpdateAudioForState(State, false);
}

void ALBPressTrainAStation::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (UWorld* World = GetWorld())
        if (ULBPressTrainIdentitySubsystem* Identities = World->GetSubsystem<ULBPressTrainIdentitySubsystem>())
            Identities->ReleaseTrain(this);
    Super::EndPlay(EndPlayReason);
}

void ALBPressTrainAStation::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (State == ELBPressTrainAState::Cycling)
    {
        EvaluateRuntimePermissives();
        if (State == ELBPressTrainAState::Cycling)
        {
            CycleElapsedSeconds += FMath::Max(0.0f, DeltaSeconds);
            RunningHours += FMath::Max(0.0f, DeltaSeconds) / 3600.0f;
            const float Duration = GetCycleDurationSeconds();
            while (CycleElapsedSeconds >= Duration && State == ELBPressTrainAState::Cycling)
            {
                CycleElapsedSeconds -= Duration;
                CompleteCurrentPanel();
            }
            if (State == ELBPressTrainAState::Cycling)
            {
                UpdatePhaseFromProgress(GetCycleProgress());
            }
        }
    }
    else if (State == ELBPressTrainAState::Stopping)
    {
        StopElapsedSeconds += FMath::Max(0.0f, DeltaSeconds);
        if (StopElapsedSeconds >= ControlledStopDurationSeconds)
        {
            SetState(ELBPressTrainAState::Ready);
        }
    }

    ApplyMachinePose();
    UpdateHMITextPresentation();
}

void ALBPressTrainAStation::SetState(ELBPressTrainAState NewState)
{
    if (State == NewState)
    {
        UpdateStatusBeacons();
        return;
    }
    const ELBPressTrainAState Previous = State;
    State = NewState;
    if (NewState != ELBPressTrainAState::Stopping) StopElapsedSeconds = 0.0f;
    UpdateAudioForState(NewState, true);
    UpdateStatusBeacons();
    OnStateChanged.Broadcast(Previous, NewState);
}

void ALBPressTrainAStation::UpdateStatusBeacons()
{
    ELBStatusBeaconState BeaconState = ELBStatusBeaconState::Stopped;
    switch (State)
    {
    case ELBPressTrainAState::Ready:
        BeaconState = ELBStatusBeaconState::Ready;
        break;
    case ELBPressTrainAState::Cycling:
        BeaconState = ELBStatusBeaconState::Running;
        break;
    case ELBPressTrainAState::Stopping:
        BeaconState = ELBStatusBeaconState::Waiting;
        break;
    case ELBPressTrainAState::Fault:
        BeaconState = bEmergencyStopActive
            ? ELBStatusBeaconState::Emergency : ELBStatusBeaconState::Fault;
        break;
    case ELBPressTrainAState::Isolated:
    default:
        BeaconState = ELBStatusBeaconState::Stopped;
        break;
    }
    for (ULBStatusBeaconComponent* Beacon : CellStatusBeacons)
    {
        if (Beacon) Beacon->SetStatus(BeaconState);
    }
}

bool ALBPressTrainAStation::IsAudioLayerRequested(FName LayerId) const
{
    if (LayerId == TEXT("hydraulic_power"))
    {
        return bControlPowerOn && State != ELBPressTrainAState::Isolated;
    }
    if (LayerId == TEXT("transfer_servo"))
    {
        if (State != ELBPressTrainAState::Cycling) return false;
        return Phase == ELBPressTrainAPhase::DestackAndLoad
            || Phase == ELBPressTrainAPhase::TransferToS02
            || Phase == ELBPressTrainAPhase::TransferToS03
            || Phase == ELBPressTrainAPhase::TransferToS04
            || Phase == ELBPressTrainAPhase::TransferToS05
            || Phase == ELBPressTrainAPhase::TransferToS06
            || Phase == ELBPressTrainAPhase::TransferToS07
            || Phase == ELBPressTrainAPhase::StillageOutput;
    }
    if (LayerId == TEXT("press_phase"))
    {
        return State == ELBPressTrainAState::Cycling
            && (Phase == ELBPressTrainAPhase::DrawS02 || Phase == ELBPressTrainAPhase::FormS03
                || Phase == ELBPressTrainAPhase::TrimS04 || Phase == ELBPressTrainAPhase::PierceS05
                || Phase == ELBPressTrainAPhase::RestrikeS06);
    }
    if (LayerId == TEXT("robot_servo"))
    {
        return State == ELBPressTrainAState::Cycling
            && (Phase == ELBPressTrainAPhase::UnloadAndInspect || Phase == ELBPressTrainAPhase::StillageOutput);
    }
    if (LayerId == TEXT("warning_alarm"))
    {
        return State == ELBPressTrainAState::Fault;
    }
    return false;
}

bool ALBPressTrainAStation::HasCompleteAudioAssetSet() const
{
    return HydraulicPowerAudio && HydraulicPowerAudio->GetSound()
        && TransferServoAudio && TransferServoAudio->GetSound()
        && RobotServoAudio && RobotServoAudio->GetSound()
        && WarningAlarmAudio && WarningAlarmAudio->GetSound()
        && PressStrokeSound && ControlledStopSound && GateInterlockSound && EmergencyStopSound;
}

void ALBPressTrainAStation::SetLoopRequested(UAudioComponent* Component, bool bRequested, float TargetVolume)
{
    if (!Component || !Component->GetSound()) return;
    if (bRequested)
    {
        if (!Component->IsPlaying()) Component->FadeIn(0.25f, TargetVolume);
        else Component->SetVolumeMultiplier(TargetVolume);
    }
    else if (Component->IsPlaying())
    {
        Component->FadeOut(0.18f, 0.0f);
    }
}

void ALBPressTrainAStation::PlayOneShot(UAudioComponent* Component, USoundBase* Sound, float Volume)
{
    if (!Component || !Sound) return;
    Component->Stop();
    Component->SetSound(Sound);
    Component->SetVolumeMultiplier(Volume);
    Component->Play();
    LastAudioCueId = Sound->GetFName();
    ++AudioCueSequence;
}

void ALBPressTrainAStation::UpdateAudioForState(ELBPressTrainAState NewState, bool bPlayTransitionCues)
{
    SetLoopRequested(HydraulicPowerAudio, IsAudioLayerRequested(TEXT("hydraulic_power")), 0.20f);
    SetLoopRequested(TransferServoAudio, IsAudioLayerRequested(TEXT("transfer_servo")), 0.26f);
    SetLoopRequested(RobotServoAudio, IsAudioLayerRequested(TEXT("robot_servo")), 0.24f);
    SetLoopRequested(WarningAlarmAudio, IsAudioLayerRequested(TEXT("warning_alarm")), 0.50f);
    if (bPlayTransitionCues && NewState == ELBPressTrainAState::Stopping)
    {
        PlayOneShot(SafetyCueAudio, ControlledStopSound, 0.45f);
    }
}

void ALBPressTrainAStation::SetControlPower(bool bEnabled)
{
    if (bEnabled && bIsolationRequested) return;
    bControlPowerOn = bEnabled;
    if (!bEnabled)
    {
        SetState(ELBPressTrainAState::Isolated);
    }
    else if (State == ELBPressTrainAState::Isolated)
    {
        SetState(ActiveFault == ELBPressTrainAFault::None ? ELBPressTrainAState::Ready : ELBPressTrainAState::Fault);
    }
}

void ALBPressTrainAStation::SetAccessInterlocksClosed(bool bClosed)
{
    bAccessInterlocksClosed = bClosed;
    if (!bClosed && (State == ELBPressTrainAState::Cycling || State == ELBPressTrainAState::Stopping))
    {
        RaiseFault(ELBPressTrainAFault::AccessInterlockOpen);
    }
}

void ALBPressTrainAStation::SetSafetyCircuitHealthy(bool bHealthy)
{
    bSafetyCircuitHealthy = bHealthy;
    if (!bHealthy && (State == ELBPressTrainAState::Cycling || State == ELBPressTrainAState::Stopping))
    {
        RaiseFault(ELBPressTrainAFault::SafetyCircuitUnhealthy);
    }
}

void ALBPressTrainAStation::SetEmergencyStopActive(bool bActive)
{
    bEmergencyStopActive = bActive;
    bAlarmAcknowledged = false;
    if (bActive)
    {
        bSafetyCircuitHealthy = false;
        RaiseFault(ELBPressTrainAFault::EmergencyStopActive);
    }
}

void ALBPressTrainAStation::SetDestackHealthy(bool bHealthy)
{
    bDestackHealthy = bHealthy;
    if (!bHealthy && State == ELBPressTrainAState::Cycling) RaiseFault(ELBPressTrainAFault::DestackFault);
}

void ALBPressTrainAStation::SetTransferHealthy(bool bHealthy)
{
    bTransferHealthy = bHealthy;
    if (!bHealthy && State == ELBPressTrainAState::Cycling) RaiseFault(ELBPressTrainAFault::TransferFault);
}

void ALBPressTrainAStation::SetHydraulicPressure(float PressureBar)
{
    HydraulicPressureBar = FMath::Clamp(PressureBar, 0.0f, 400.0f);
    if (HydraulicPressureBar < MinimumHydraulicPressureBar && State == ELBPressTrainAState::Cycling)
        RaiseFault(ELBPressTrainAFault::HydraulicPressureLow);
}

void ALBPressTrainAStation::SetPressLoad(float LoadPercent)
{
    PressLoadPercent = FMath::Clamp(LoadPercent, 0.0f, 200.0f);
    if (PressLoadPercent > MaximumPressLoadPercent && State == ELBPressTrainAState::Cycling)
        RaiseFault(ELBPressTrainAFault::PressOverload);
}

void ALBPressTrainAStation::SetInspectionHealthy(bool bHealthy)
{
    bInspectionHealthy = bHealthy;
    if (!bHealthy && State == ELBPressTrainAState::Cycling) RaiseFault(ELBPressTrainAFault::InspectionUnavailable);
}

void ALBPressTrainAStation::SetNextInspectionPass(bool bPass)
{
    bNextInspectionPass = bPass;
}

void ALBPressTrainAStation::SetStillageOutputClear(bool bClear)
{
    bStillageOutputClear = bClear;
    if (!bClear && State == ELBPressTrainAState::Cycling) RaiseFault(ELBPressTrainAFault::StillageOutputBlocked);
}

void ALBPressTrainAStation::SetTargetStrokesPerMinute(float StrokesPerMinute)
{
    if (State == ELBPressTrainAState::Cycling || State == ELBPressTrainAState::Stopping) return;
    TargetStrokesPerMinute = FMath::Clamp(StrokesPerMinute, 4.0f, 15.0f);
}

bool ALBPressTrainAStation::ConfigureTrainVariant(
    FName NewTrainId, const FString& NewDisplayName, const FString& NewPartFamily, FLinearColor NewAccentColor)
{
    if (State == ELBPressTrainAState::Cycling || State == ELBPressTrainAState::Stopping
        || NewDisplayName.IsEmpty() || NewPartFamily.IsEmpty())
    {
        return false;
    }
    const FString Id = NewTrainId.ToString().ToUpper();
    if (Id.Len() != 7 || !Id.StartsWith(TEXT("TRAIN_")) || Id[6] < TCHAR('A') || Id[6] > TCHAR('D'))
    {
        return false;
    }
    TrainId = FName(*Id);
    TrainDisplayName = NewDisplayName.ToUpper();
    PartFamily = NewPartFamily.ToUpper();
    TrainAccentColor = NewAccentColor.GetClamped();
    FactoryInputPort->PortId = FName(*FString::Printf(TEXT("%s-IN"), *TrainId.ToString()));
    FactoryOutputPort->PortId = FName(*FString::Printf(TEXT("%s-OUT"), *TrainId.ToString()));
    UpdateTrainIdentityPresentation();
    UpdateHMITextPresentation();
    return true;
}

bool ALBPressTrainAStation::SetActiveProductionRecipe(
    const FName VehicleModelId, const FName PanelTypeId, const FName DieId)
{
    if (DieId.IsNone()
        || !LBVehicleModelCatalog::IsApprovedStampedPanelRecipe(VehicleModelId, PanelTypeId))
    {
        return false;
    }
    const bool bSameRecipe = ActiveVehicleModelId == VehicleModelId
        && ActivePanelTypeId == PanelTypeId && ActiveDieId == DieId;
    if (!bSameRecipe && (!InProcessBlankId.IsNone() || !PendingBlankIds.IsEmpty())) return false;
    ActiveVehicleModelId = VehicleModelId;
    ActivePanelTypeId = PanelTypeId;
    ActiveDieId = DieId;
    PartFamily = PanelTypeId.ToString().Replace(TEXT("_"), TEXT(" ")).ToUpper();
    return true;
}

void ALBPressTrainAStation::ApplyPersistentIdentity(const FGuid& NewGuid, FName NewTrainId,
    const FString& NewDisplayName)
{
    PersistentTrainGuid = NewGuid;
    TrainId = NewTrainId;
    TrainDisplayName = NewDisplayName.IsEmpty()
        ? FName::NameToDisplayString(NewTrainId.ToString(), false).ToUpper()
        : NewDisplayName;
    FactoryInputPort->PortId = FName(*FString::Printf(TEXT("%s-IN"), *TrainId.ToString()));
    FactoryOutputPort->PortId = FName(*FString::Printf(TEXT("%s-OUT"), *TrainId.ToString()));
    UpdateTrainIdentityPresentation();
    UpdateHMITextPresentation();
}

FName ALBPressTrainAStation::GetStationId(const int32 StationNumber) const
{
    if (StationNumber < 1 || StationNumber > 7) return NAME_None;
    const FString Designation = TrainId.ToString().Right(1).ToUpper();
    return FName(*FString::Printf(TEXT("%s-S%02d"), *Designation, StationNumber));
}

bool ALBPressTrainAStation::QueueReservedBlank(FName ReservationId, FName BlankId)
{
    if (ReservationId.IsNone() || BlankId.IsNone() || PendingBlankIds.Num() >= MaximumPendingBlanks) return false;
    if (PendingBlankIds.Contains(BlankId) || InProcessBlankId == BlankId) return false;
    if (PendingBlankReservationIds.Contains(ReservationId) || InProcessReservationId == ReservationId) return false;
    PendingBlankReservationIds.Add(ReservationId);
    PendingBlankIds.Add(BlankId);
    if (Phase == ELBPressTrainAPhase::WaitingForBlank && State == ELBPressTrainAState::Ready)
        UpdateHMITextPresentation();
    return true;
}

bool ALBPressTrainAStation::CanStart(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (!bControlPowerOn) BlockingReasons.Add(LOCTEXT("PowerOff", "Control power is off"));
    if (State != ELBPressTrainAState::Ready)
        BlockingReasons.Add(FText::FromString(FString::Printf(TEXT("%s is not ready"), *TrainDisplayName)));
    if (bIsolationRequested) BlockingReasons.Add(LOCTEXT("IsolationActive", "Maintenance isolation is active"));
    if (bEmergencyStopActive) BlockingReasons.Add(LOCTEXT("EmergencyStop", "Emergency stop is active"));
    if (!bSafetyCircuitHealthy) BlockingReasons.Add(LOCTEXT("SafetyCircuit", "Safety circuit is not reset"));
    if (!bAccessInterlocksClosed) BlockingReasons.Add(LOCTEXT("AccessOpen", "An interlocked access point is open"));
    if (!bDestackHealthy) BlockingReasons.Add(LOCTEXT("DestackFault", "Blank destack/load equipment is unavailable"));
    if (!bTransferHealthy) BlockingReasons.Add(LOCTEXT("TransferFault", "Transfer equipment is unavailable"));
    if (HydraulicPressureBar < MinimumHydraulicPressureBar) BlockingReasons.Add(LOCTEXT("HydraulicLow", "Press hydraulic pressure is low"));
    if (PressLoadPercent > MaximumPressLoadPercent) BlockingReasons.Add(LOCTEXT("PressOverload", "Press load exceeds the recipe limit"));
    if (!bInspectionHealthy) BlockingReasons.Add(LOCTEXT("InspectionFault", "Final inspection is unavailable"));
    if (!LBVehicleModelCatalog::IsApprovedStampedPanelRecipe(
        ActiveVehicleModelId, ActivePanelTypeId) || ActiveDieId.IsNone())
    {
        BlockingReasons.Add(LOCTEXT("NoApprovedRecipe",
            "Select an approved vehicle stamped-panel recipe and installed die"));
    }
    if (!bStillageOutputClear || PendingPanelIds.Num() >= MaximumPendingPanels)
        BlockingReasons.Add(LOCTEXT("OutputBlocked", "Stillage output buffer is blocked"));
    if (InProcessBlankId.IsNone() && PendingBlankIds.IsEmpty())
        BlockingReasons.Add(LOCTEXT("NoReservedBlank", "No identified reserved blank is available"));
    return BlockingReasons.IsEmpty();
}

bool ALBPressTrainAStation::StartLine()
{
    TArray<FText> Reasons;
    if (!CanStart(Reasons)) return false;
    if (InProcessBlankId.IsNone()) BeginNextBlankIfAvailable();
    if (InProcessBlankId.IsNone()) return false;
    ActiveFault = ELBPressTrainAFault::None;
    bAlarmAcknowledged = false;
    bRestartRequiredAfterLoad = false;
    SetState(ELBPressTrainAState::Cycling);
    UpdatePhaseFromProgress(GetCycleProgress());
    return true;
}

void ALBPressTrainAStation::RequestControlledStop()
{
    if (State == ELBPressTrainAState::Cycling)
    {
        StopElapsedSeconds = 0.0f;
        SetState(ELBPressTrainAState::Stopping);
    }
}

bool ALBPressTrainAStation::AcknowledgeAlarm(FName CommandSource)
{
    if (CommandSource.IsNone() || ActiveFault == ELBPressTrainAFault::None) return false;
    LastCommandSource = CommandSource;
    bAlarmAcknowledged = true;
    return true;
}

void ALBPressTrainAStation::RaiseFault(ELBPressTrainAFault Fault)
{
    if (Fault == ELBPressTrainAFault::None || State == ELBPressTrainAState::Fault) return;
    ActiveFault = Fault;
    bAlarmAcknowledged = false;
    if (bControlPowerOn) SetState(ELBPressTrainAState::Fault);
    PlayOneShot(SafetyCueAudio,
        Fault == ELBPressTrainAFault::EmergencyStopActive ? EmergencyStopSound : GateInterlockSound,
        Fault == ELBPressTrainAFault::EmergencyStopActive ? 0.62f : 0.48f);
    OnFaultRaised.Broadcast(Fault);
}

void ALBPressTrainAStation::EvaluateRuntimePermissives()
{
    if (bEmergencyStopActive) RaiseFault(ELBPressTrainAFault::EmergencyStopActive);
    else if (!bSafetyCircuitHealthy) RaiseFault(ELBPressTrainAFault::SafetyCircuitUnhealthy);
    else if (!bAccessInterlocksClosed) RaiseFault(ELBPressTrainAFault::AccessInterlockOpen);
    else if (!bDestackHealthy) RaiseFault(ELBPressTrainAFault::DestackFault);
    else if (!bTransferHealthy) RaiseFault(ELBPressTrainAFault::TransferFault);
    else if (HydraulicPressureBar < MinimumHydraulicPressureBar) RaiseFault(ELBPressTrainAFault::HydraulicPressureLow);
    else if (PressLoadPercent > MaximumPressLoadPercent) RaiseFault(ELBPressTrainAFault::PressOverload);
    else if (!bInspectionHealthy) RaiseFault(ELBPressTrainAFault::InspectionUnavailable);
    else if (!bStillageOutputClear || PendingPanelIds.Num() >= MaximumPendingPanels)
        RaiseFault(ELBPressTrainAFault::StillageOutputBlocked);
    else if (InProcessBlankId.IsNone()) RaiseFault(ELBPressTrainAFault::ReservedBlankUnavailable);
}

bool ALBPressTrainAStation::ResetFault()
{
    if (State != ELBPressTrainAState::Fault || ActiveFault == ELBPressTrainAFault::None || !bControlPowerOn
        || !bAlarmAcknowledged || bEmergencyStopActive || !bSafetyCircuitHealthy || !bAccessInterlocksClosed
        || bIsolationRequested || !bDestackHealthy || !bTransferHealthy || !bInspectionHealthy
        || !bStillageOutputClear || HydraulicPressureBar < MinimumHydraulicPressureBar
        || PressLoadPercent > MaximumPressLoadPercent)
    {
        return false;
    }
    ActiveFault = ELBPressTrainAFault::None;
    bAlarmAcknowledged = false;
    SetState(ELBPressTrainAState::Ready);
    return true;
}

bool ALBPressTrainAStation::RequestIsolation(FName CommandSource)
{
    if (CommandSource.IsNone()) return false;
    LastCommandSource = CommandSource;
    RequestControlledStop();
    bIsolationRequested = true;
    bZeroEnergyProved = false;
    LastSafetyEvidenceId = NAME_None;
    SetControlPower(false);
    return true;
}

bool ALBPressTrainAStation::ConfirmZeroEnergyIsolation(
    bool bZeroMotionVerified, bool bHydraulicPressureReleased, FName EvidenceId)
{
    if (!bIsolationRequested || bControlPowerOn || State != ELBPressTrainAState::Isolated
        || !bZeroMotionVerified || !bHydraulicPressureReleased || EvidenceId.IsNone())
    {
        return false;
    }
    bZeroEnergyProved = true;
    LastSafetyEvidenceId = EvidenceId;
    return true;
}

bool ALBPressTrainAStation::ReleaseIsolation(FName CommandSource, bool bGuardZoneClear)
{
    if (CommandSource.IsNone() || !bIsolationRequested || !bZeroEnergyProved || !bGuardZoneClear
        || !bAccessInterlocksClosed || bEmergencyStopActive || !bSafetyCircuitHealthy)
    {
        return false;
    }
    LastCommandSource = CommandSource;
    bIsolationRequested = false;
    bZeroEnergyProved = false;
    SetControlPower(true);
    return true;
}

bool ALBPressTrainAStation::ExecuteRemoteCommand(
    ELBPressTrainACommand Command, FName CommandSource, FName AuthorityId)
{
    if (!bRemoteControlEnabled || CommandSource.IsNone() || AuthorityId != RemoteAuthorityId) return false;
    LastCommandSource = CommandSource;
    switch (Command)
    {
    case ELBPressTrainACommand::PowerOn: SetControlPower(true); return bControlPowerOn;
    case ELBPressTrainACommand::PowerOff: SetControlPower(false); return !bControlPowerOn;
    case ELBPressTrainACommand::Start: return StartLine();
    case ELBPressTrainACommand::ControlledStop: RequestControlledStop(); return true;
    case ELBPressTrainACommand::AcknowledgeAlarm: return AcknowledgeAlarm(CommandSource);
    case ELBPressTrainACommand::Reset: return ResetFault();
    case ELBPressTrainACommand::RequestIsolation: return RequestIsolation(CommandSource);
    case ELBPressTrainACommand::ReleaseIsolation: return ReleaseIsolation(CommandSource, true);
    default: return false;
    }
}

float ALBPressTrainAStation::GetCycleDurationSeconds() const
{
    return 60.0f / FMath::Clamp(TargetStrokesPerMinute, 4.0f, 15.0f);
}

float ALBPressTrainAStation::GetCycleProgress() const
{
    return FMath::Clamp(CycleElapsedSeconds / GetCycleDurationSeconds(), 0.0f, 1.0f);
}

void ALBPressTrainAStation::UpdatePhaseFromProgress(float Progress)
{
    const ELBPressTrainAPhase PreviousPhase = Phase;
    if (Progress < 0.08f) Phase = ELBPressTrainAPhase::DestackAndLoad;
    else if (Progress < 0.14f) Phase = ELBPressTrainAPhase::TransferToS02;
    else if (Progress < 0.24f) Phase = ELBPressTrainAPhase::DrawS02;
    else if (Progress < 0.30f) Phase = ELBPressTrainAPhase::TransferToS03;
    else if (Progress < 0.40f) Phase = ELBPressTrainAPhase::FormS03;
    else if (Progress < 0.46f) Phase = ELBPressTrainAPhase::TransferToS04;
    else if (Progress < 0.56f) Phase = ELBPressTrainAPhase::TrimS04;
    else if (Progress < 0.62f) Phase = ELBPressTrainAPhase::TransferToS05;
    else if (Progress < 0.72f) Phase = ELBPressTrainAPhase::PierceS05;
    else if (Progress < 0.78f) Phase = ELBPressTrainAPhase::TransferToS06;
    else if (Progress < 0.86f) Phase = ELBPressTrainAPhase::RestrikeS06;
    else if (Progress < 0.91f) Phase = ELBPressTrainAPhase::TransferToS07;
    else if (Progress < 0.97f) Phase = ELBPressTrainAPhase::UnloadAndInspect;
    else Phase = ELBPressTrainAPhase::StillageOutput;
    if (Phase != PreviousPhase)
    {
        UpdateAudioForState(State, false);
        if (IsAudioLayerRequested(TEXT("press_phase")))
        {
            PlayOneShot(PressCueAudio, PressStrokeSound, 0.54f);
        }
    }
}

void ALBPressTrainAStation::BeginNextBlankIfAvailable()
{
    if (!InProcessBlankId.IsNone() || PendingBlankIds.IsEmpty() || PendingBlankReservationIds.IsEmpty()) return;
    InProcessBlankId = PendingBlankIds[0];
    InProcessReservationId = PendingBlankReservationIds[0];
    PendingBlankIds.RemoveAt(0);
    PendingBlankReservationIds.RemoveAt(0);
    CycleElapsedSeconds = 0.0f;
    Phase = ELBPressTrainAPhase::DestackAndLoad;
}

void ALBPressTrainAStation::CompleteCurrentPanel()
{
    if (InProcessBlankId.IsNone())
    {
        RaiseFault(ELBPressTrainAFault::ReservedBlankUnavailable);
        return;
    }
    if (!bStillageOutputClear || PendingPanelIds.Num() >= MaximumPendingPanels)
    {
        RaiseFault(ELBPressTrainAFault::StillageOutputBlocked);
        return;
    }

    FString VariantLetter = TrainId.ToString().Right(1).ToUpper();
    if (VariantLetter.Len() != 1 || VariantLetter[0] < TCHAR('A') || VariantLetter[0] > TCHAR('D')) VariantLetter = TEXT("A");
    const FName PanelId(*FString::Printf(TEXT("PT%s-PANEL-%s-%s-%06d"),
        *VariantLetter, *ActiveVehicleModelId.ToString(), *ActivePanelTypeId.ToString(),
        NextPanelSerial++));
    if (bNextInspectionPass)
    {
        ++GoodPanels;
        PendingPanelIds.Add(PanelId);
    }
    else
    {
        ++RejectedPanels;
    }
    OnPanelCompleted.Broadcast(PanelId, bNextInspectionPass);
    bNextInspectionPass = true;
    InProcessBlankId = NAME_None;
    InProcessReservationId = NAME_None;
    Phase = ELBPressTrainAPhase::WaitingForBlank;
    BeginNextBlankIfAvailable();
    if (InProcessBlankId.IsNone()) SetState(ELBPressTrainAState::Ready);
}

bool ALBPressTrainAStation::CanReleasePanel(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (PendingPanelIds.IsEmpty()) BlockingReasons.Add(LOCTEXT("NoPanel", "No inspected panel is waiting at Train A output"));
    if (!PendingPanelHandoffTransactionId.IsNone()) BlockingReasons.Add(LOCTEXT("HandoffActive", "Another panel handoff is active"));
    if (!bStillageOutputClear) BlockingReasons.Add(LOCTEXT("OutputRouteBlocked", "Stillage output route is blocked"));
    if (!bAccessInterlocksClosed || bEmergencyStopActive || !bSafetyCircuitHealthy || bIsolationRequested)
        BlockingReasons.Add(LOCTEXT("HandoffSafety", "Train A safety or isolation state prevents panel handoff"));
    return BlockingReasons.IsEmpty();
}

bool ALBPressTrainAStation::RequestPanelHandoff(FName TransactionId, FName& PanelId)
{
    PanelId = NAME_None;
    if (TransactionId.IsNone()) return false;
    TArray<FText> Reasons;
    if (!CanReleasePanel(Reasons)) return false;
    PendingPanelHandoffTransactionId = TransactionId;
    PendingPanelHandoffPanelId = PendingPanelIds[0];
    PanelId = PendingPanelHandoffPanelId;
    return true;
}

bool ALBPressTrainAStation::ConfirmPanelHandoff(FName TransactionId)
{
    if (TransactionId.IsNone() || TransactionId != PendingPanelHandoffTransactionId
        || PendingPanelHandoffPanelId.IsNone() || PendingPanelIds.IsEmpty()
        || PendingPanelIds[0] != PendingPanelHandoffPanelId)
    {
        return false;
    }
    PendingPanelIds.RemoveAt(0);
    PendingPanelHandoffTransactionId = NAME_None;
    PendingPanelHandoffPanelId = NAME_None;
    return true;
}

void ALBPressTrainAStation::CancelPanelHandoff(FName TransactionId)
{
    if (!TransactionId.IsNone() && TransactionId == PendingPanelHandoffTransactionId)
    {
        PendingPanelHandoffTransactionId = NAME_None;
        PendingPanelHandoffPanelId = NAME_None;
    }
}

FLBPressTrainAHMIStatus ALBPressTrainAStation::GetHMIStatus() const
{
    FLBPressTrainAHMIStatus Status;
    Status.TrainId = TrainId;
    Status.State = State;
    Status.Phase = Phase;
    Status.ActiveFault = ActiveFault;
    Status.CycleProgress = GetCycleProgress();
    Status.TargetStrokesPerMinute = TargetStrokesPerMinute;
    Status.HydraulicPressureBar = HydraulicPressureBar;
    Status.PressLoadPercent = PressLoadPercent;
    Status.PendingBlankCount = PendingBlankIds.Num();
    Status.OldestPendingBlankId = PendingBlankIds.IsEmpty() ? NAME_None : PendingBlankIds[0];
    Status.InProcessBlankId = InProcessBlankId;
    Status.GoodPanels = GoodPanels;
    Status.RejectedPanels = RejectedPanels;
    Status.PendingPanelCount = PendingPanelIds.Num();
    Status.OldestPendingPanelId = PendingPanelIds.IsEmpty() ? NAME_None : PendingPanelIds[0];
    Status.bControlPowerOn = bControlPowerOn;
    Status.bAccessInterlocksClosed = bAccessInterlocksClosed;
    Status.bSafetyCircuitHealthy = bSafetyCircuitHealthy;
    Status.bEmergencyStopActive = bEmergencyStopActive;
    Status.bDestackHealthy = bDestackHealthy;
    Status.bTransferHealthy = bTransferHealthy;
    Status.bInspectionHealthy = bInspectionHealthy;
    Status.bStillageOutputClear = bStillageOutputClear;
    Status.bAlarmAcknowledged = bAlarmAcknowledged;
    Status.bIsolationRequested = bIsolationRequested;
    Status.bZeroEnergyProved = bZeroEnergyProved;
    Status.bRestartRequiredAfterLoad = bRestartRequiredAfterLoad;
    Status.LastCommandSource = LastCommandSource;
    Status.LastSafetyEvidenceId = LastSafetyEvidenceId;
    Status.bCanStart = CanStart(Status.BlockingReasons);
    return Status;
}

FLBPressTrainASaveState ALBPressTrainAStation::CaptureSaveState() const
{
    FLBPressTrainASaveState Saved;
    Saved.PersistentTrainGuid = PersistentTrainGuid;
    Saved.TrainId = TrainId;
    Saved.TrainDisplayName = TrainDisplayName;
    Saved.WorldTransform = GetActorTransform();
    Saved.State = State;
    Saved.Phase = Phase;
    Saved.ActiveFault = ActiveFault;
    Saved.PendingBlankIds = PendingBlankIds;
    Saved.PendingBlankReservationIds = PendingBlankReservationIds;
    Saved.InProcessBlankId = InProcessBlankId;
    Saved.InProcessReservationId = InProcessReservationId;
    Saved.PendingPanelIds = PendingPanelIds;
    Saved.PendingPanelHandoffTransactionId = PendingPanelHandoffTransactionId;
    Saved.PendingPanelHandoffPanelId = PendingPanelHandoffPanelId;
    Saved.NextPanelSerial = NextPanelSerial;
    Saved.GoodPanels = GoodPanels;
    Saved.RejectedPanels = RejectedPanels;
    Saved.ActiveVehicleModelId = ActiveVehicleModelId;
    Saved.ActivePanelTypeId = ActivePanelTypeId;
    Saved.ActiveDieId = ActiveDieId;
    Saved.RunningHours = RunningHours;
    Saved.CycleElapsedSeconds = CycleElapsedSeconds;
    Saved.TargetStrokesPerMinute = TargetStrokesPerMinute;
    Saved.HydraulicPressureBar = HydraulicPressureBar;
    Saved.PressLoadPercent = PressLoadPercent;
    Saved.bControlPowerOn = bControlPowerOn;
    Saved.bAccessInterlocksClosed = bAccessInterlocksClosed;
    Saved.bSafetyCircuitHealthy = bSafetyCircuitHealthy;
    Saved.bEmergencyStopActive = bEmergencyStopActive;
    Saved.bDestackHealthy = bDestackHealthy;
    Saved.bTransferHealthy = bTransferHealthy;
    Saved.bInspectionHealthy = bInspectionHealthy;
    Saved.bStillageOutputClear = bStillageOutputClear;
    Saved.bNextInspectionPass = bNextInspectionPass;
    Saved.bAlarmAcknowledged = bAlarmAcknowledged;
    Saved.bIsolationRequested = bIsolationRequested;
    Saved.bZeroEnergyProved = bZeroEnergyProved;
    Saved.bRestartRequiredAfterLoad = bRestartRequiredAfterLoad;
    Saved.LastCommandSource = LastCommandSource;
    Saved.LastSafetyEvidenceId = LastSafetyEvidenceId;
    return Saved;
}

bool ALBPressTrainAStation::RestoreSaveState(const FLBPressTrainASaveState& SavedState)
{
    if (SavedState.Version < 1 || SavedState.Version > 4) return false;
    if (SavedState.Version >= 2)
    {
        if (!SavedState.PersistentTrainGuid.IsValid() || SavedState.WorldTransform.ContainsNaN()
            || SavedState.WorldTransform.GetScale3D().GetAbsMax() > 100.0f
            || SavedState.WorldTransform.GetScale3D().GetAbsMin() < 0.01f) return false;
        if (UWorld* World = GetWorld())
        {
            if (ULBPressTrainIdentitySubsystem* Identities = World->GetSubsystem<ULBPressTrainIdentitySubsystem>())
            {
                if (!Identities->RestoreTrainIdentity(this, SavedState.PersistentTrainGuid,
                    SavedState.TrainId, SavedState.TrainDisplayName)) return false;
            }
            else ApplyPersistentIdentity(SavedState.PersistentTrainGuid, SavedState.TrainId, SavedState.TrainDisplayName);
        }
        else ApplyPersistentIdentity(SavedState.PersistentTrainGuid, SavedState.TrainId, SavedState.TrainDisplayName);
        SetActorTransform(SavedState.WorldTransform, false, nullptr, ETeleportType::TeleportPhysics);
    }
    else if (SavedState.TrainId != TrainId) return false;
    PendingBlankIds = SavedState.PendingBlankIds;
    PendingBlankReservationIds = SavedState.PendingBlankReservationIds;
    const int32 ValidBlankPairs = FMath::Min3(PendingBlankIds.Num(), PendingBlankReservationIds.Num(), MaximumPendingBlanks);
    PendingBlankIds.SetNum(ValidBlankPairs);
    PendingBlankReservationIds.SetNum(ValidBlankPairs);
    for (int32 Index = PendingBlankIds.Num() - 1; Index >= 0; --Index)
    {
        if (PendingBlankIds[Index].IsNone() || PendingBlankReservationIds[Index].IsNone())
        {
            PendingBlankIds.RemoveAt(Index);
            PendingBlankReservationIds.RemoveAt(Index);
        }
    }
    InProcessBlankId = SavedState.InProcessBlankId;
    InProcessReservationId = SavedState.InProcessReservationId;
    if (InProcessBlankId.IsNone() || InProcessReservationId.IsNone())
    {
        InProcessBlankId = NAME_None;
        InProcessReservationId = NAME_None;
    }
    PendingPanelIds = SavedState.PendingPanelIds;
    PendingPanelIds.RemoveAll([](FName PanelId) { return PanelId.IsNone(); });
    if (PendingPanelIds.Num() > MaximumPendingPanels) PendingPanelIds.SetNum(MaximumPendingPanels);
    PendingPanelHandoffTransactionId = SavedState.PendingPanelHandoffTransactionId;
    PendingPanelHandoffPanelId = SavedState.PendingPanelHandoffPanelId;
    if (PendingPanelHandoffTransactionId.IsNone() || PendingPanelHandoffPanelId.IsNone()
        || PendingPanelIds.IsEmpty() || PendingPanelIds[0] != PendingPanelHandoffPanelId)
    {
        PendingPanelHandoffTransactionId = NAME_None;
        PendingPanelHandoffPanelId = NAME_None;
    }
    NextPanelSerial = FMath::Max(1, SavedState.NextPanelSerial);
    GoodPanels = FMath::Max(0, SavedState.GoodPanels);
    RejectedPanels = FMath::Max(0, SavedState.RejectedPanels);
    const bool bSavedRecipeApproved = SavedState.Version >= 3
        && !SavedState.ActiveDieId.IsNone()
        && LBVehicleModelCatalog::IsApprovedStampedPanelRecipe(
            SavedState.ActiveVehicleModelId, SavedState.ActivePanelTypeId);
    ActiveVehicleModelId = bSavedRecipeApproved ? SavedState.ActiveVehicleModelId : NAME_None;
    ActivePanelTypeId = bSavedRecipeApproved ? SavedState.ActivePanelTypeId : NAME_None;
    ActiveDieId = bSavedRecipeApproved ? SavedState.ActiveDieId : NAME_None;
    RunningHours = FMath::Max(0.0f, SavedState.RunningHours);
    TargetStrokesPerMinute = FMath::Clamp(SavedState.TargetStrokesPerMinute, 4.0f, 15.0f);
    CycleElapsedSeconds = FMath::Clamp(SavedState.CycleElapsedSeconds, 0.0f, GetCycleDurationSeconds() - KINDA_SMALL_NUMBER);
    HydraulicPressureBar = FMath::Clamp(SavedState.HydraulicPressureBar, 0.0f, 400.0f);
    PressLoadPercent = FMath::Clamp(SavedState.PressLoadPercent, 0.0f, 200.0f);
    bControlPowerOn = SavedState.bControlPowerOn;
    bAccessInterlocksClosed = SavedState.bAccessInterlocksClosed;
    bSafetyCircuitHealthy = SavedState.bSafetyCircuitHealthy;
    bEmergencyStopActive = SavedState.bEmergencyStopActive;
    bDestackHealthy = SavedState.bDestackHealthy;
    bTransferHealthy = SavedState.bTransferHealthy;
    bInspectionHealthy = SavedState.bInspectionHealthy;
    bStillageOutputClear = SavedState.bStillageOutputClear;
    bNextInspectionPass = SavedState.bNextInspectionPass;
    bAlarmAcknowledged = SavedState.bAlarmAcknowledged;
    bIsolationRequested = SavedState.bIsolationRequested;
    bZeroEnergyProved = SavedState.bZeroEnergyProved;
    bRestartRequiredAfterLoad = SavedState.bRestartRequiredAfterLoad;
    LastCommandSource = SavedState.LastCommandSource;
    LastSafetyEvidenceId = SavedState.LastSafetyEvidenceId;
    ActiveFault = SavedState.ActiveFault;
    Phase = SavedState.Phase;

    const bool bWasMoving = SavedState.State == ELBPressTrainAState::Cycling || SavedState.State == ELBPressTrainAState::Stopping;
    State = !bControlPowerOn ? ELBPressTrainAState::Isolated : (bWasMoving ? ELBPressTrainAState::Ready : SavedState.State);
    if (bWasMoving)
    {
        ActiveFault = ELBPressTrainAFault::None;
        bAlarmAcknowledged = false;
        bRestartRequiredAfterLoad = true;
    }
    StopElapsedSeconds = 0.0f;
    if (HasActorBegunPlay()) ApplyMachinePose();
    UpdateAudioForState(State, false);
    UpdateStatusBeacons();
    return true;
}

void ALBPressTrainAStation::ApplyMachinePose()
{
    const float Progress = GetCycleProgress();
    const bool bMoving = State == ELBPressTrainAState::Cycling;
    auto Stroke = [Progress, bMoving](float Begin, float End)
    {
        if (!bMoving || Progress < Begin || Progress > End) return 0.0f;
        const float Local = FMath::Clamp((Progress - Begin) / FMath::Max(KINDA_SMALL_NUMBER, End - Begin), 0.0f, 1.0f);
        return FMath::Pow(FMath::Sin(PI * Local), 6.0f);
    };
    auto TransferWave = [Progress, bMoving](float Begin, float End)
    {
        if (!bMoving || Progress < Begin || Progress > End) return 0.0f;
        const float Local = FMath::Clamp((Progress - Begin)
            / FMath::Max(KINDA_SMALL_NUMBER, End - Begin), 0.0f, 1.0f);
        // Smooth out-and-return travel: zero position and zero velocity at both ends,
        // with no phase-boundary teleport when the next station takes ownership.
        return 0.5f - 0.5f * FMath::Cos(2.0f * PI * Local);
    };
    auto SmoothBlend = [](float Value)
    {
        const float T = FMath::Clamp(Value, 0.0f, 1.0f);
        // Quintic smoothstep: continuous position, velocity, and acceleration at
        // every pickup-cycle key pose.
        return T * T * T * (T * (T * 6.0f - 15.0f) + 10.0f);
    };
    auto BlendSegment = [&SmoothBlend](float Local, float Begin, float End,
        float From, float To)
    {
        const float Alpha = SmoothBlend((Local - Begin)
            / FMath::Max(KINDA_SMALL_NUMBER, End - Begin));
        return FMath::Lerp(From, To, Alpha);
    };
    auto TransferPose = [Progress, bMoving, &BlendSegment](float Begin, float End)
    {
        // X is pitch and Y is lift. Zero/zero is the complete, authored v746
        // assembly. The sequence raises clear before leaving the frame, visits both
        // press throats only while their strokes are open, then fully reassembles.
        if (!bMoving || Progress < Begin || Progress > End) return FVector2D::ZeroVector;
        const float Local = FMath::Clamp((Progress - Begin)
            / FMath::Max(KINDA_SMALL_NUMBER, End - Begin), 0.0f, 1.0f);
        const float High = TransferSheetContactLiftZcm + TransferClearanceLiftZcm;
        const float Contact = TransferSheetContactLiftZcm;

        if (Local < 0.10f)
            return FVector2D(0.0f, BlendSegment(Local, 0.00f, 0.10f, 0.0f, High));
        if (Local < 0.18f)
            return FVector2D(BlendSegment(Local, 0.10f, 0.18f,
                0.0f, TransferPitchSourceYcm), High);
        if (Local < 0.26f)
            return FVector2D(TransferPitchSourceYcm,
                BlendSegment(Local, 0.18f, 0.26f, High, Contact));
        if (Local < 0.34f)
            return FVector2D(TransferPitchSourceYcm,
                BlendSegment(Local, 0.26f, 0.34f, Contact, High));
        if (Local < 0.66f)
            return FVector2D(BlendSegment(Local, 0.34f, 0.66f,
                TransferPitchSourceYcm, TransferPitchDestinationYcm), High);
        if (Local < 0.74f)
            return FVector2D(TransferPitchDestinationYcm,
                BlendSegment(Local, 0.66f, 0.74f, High, Contact));
        if (Local < 0.82f)
            return FVector2D(TransferPitchDestinationYcm,
                BlendSegment(Local, 0.74f, 0.82f, Contact, High));
        if (Local < 0.90f)
            return FVector2D(BlendSegment(Local, 0.82f, 0.90f,
                TransferPitchDestinationYcm, 0.0f), High);
        return FVector2D(0.0f,
            BlendSegment(Local, 0.90f, 1.00f, High, 0.0f));
    };

    const float Destack = Stroke(0.00f, 0.08f);
    const FVector2D TransferGapPose[] = {
        TransferPose(0.08f, 0.14f),
        TransferPose(0.24f, 0.30f),
        TransferPose(0.40f, 0.46f),
        TransferPose(0.56f, 0.62f),
        TransferPose(0.72f, 0.78f),
        TransferPose(0.86f, 0.91f)
    };
    const float S02 = Stroke(0.14f, 0.24f);
    const float S03 = Stroke(0.30f, 0.40f);
    const float S04 = Stroke(0.46f, 0.56f);
    const float S05 = Stroke(0.62f, 0.72f);
    const float S06 = Stroke(0.78f, 0.86f);
    const float Unload = TransferWave(0.91f, 0.97f);
    const float Output = TransferWave(0.97f, 1.00f);

    DestackLiftMover->SetRelativeLocation(FVector(0.0f, 0.0f, DestackLiftTravelCm * Destack));
    if (DestackFeedBlankVisual)
    {
        // During the first 8% of a cycle this is the identified in-process blank.
        // Afterwards, the same physical display returns home and only represents a
        // separately queued next blank. With neither material state it stays hidden.
        const bool bActiveBlankOnDestacker = !InProcessBlankId.IsNone()
            && Progress < 0.08f;
        const bool bQueuedBlankWaiting = !PendingBlankIds.IsEmpty()
            && !bActiveBlankOnDestacker;
        const bool bCompleteMachineVisible = HasCompletedRuntimeVisual();
        const bool bShowFeedBlank = bCompleteMachineVisible
            && (bActiveBlankOnDestacker || bQueuedBlankWaiting);
        DestackFeedBlankVisual->SetHiddenInGame(!bShowFeedBlank);
        DestackFeedBlankVisual->SetVisibility(bShowFeedBlank, true);
    }
    for (int32 Gap = 0; Gap < ApprovedTransferLiftMovers.Num(); ++Gap)
    {
        if (!ApprovedTransferLiftMovers.IsValidIndex(Gap)
            || !ApprovedTransferPitchMovers.IsValidIndex(Gap)) continue;
        // Only the four S02-S06 inter-press traverses use this approved assembly.
        // S01 infeed and S06 unload are separate equipment and separate phases.
        const FVector2D Pose = TransferGapPose[Gap + 1];
        ApprovedTransferLiftMovers[Gap]->SetRelativeLocation(
            FVector(0.0f, 0.0f, Pose.Y));
        ApprovedTransferPitchMovers[Gap]->SetRelativeLocation(
            FVector(0.0f, Pose.X, 0.0f));
    }
    // The exact accepted v763 transform is each press's closed/contact pose. Hold the
    // ram and upper die above that datum at rest, descend to zero at peak stroke, then
    // return; a negative offset would drive the accepted geometry through its bolster.
    S02SlideMover->SetRelativeLocation(FVector(0.0f, 0.0f, 80.0f * (1.0f - S02)));
    S03SlideMover->SetRelativeLocation(FVector(0.0f, 0.0f, S03StrokeCm * (1.0f - S03)));
    S04SlideMover->SetRelativeLocation(FVector(0.0f, 0.0f, 60.0f * (1.0f - S04)));
    S05SlideMover->SetRelativeLocation(FVector(0.0f, 0.0f, 55.0f * (1.0f - S05)));
    S06SlideMover->SetRelativeLocation(FVector(0.0f, 0.0f, 60.0f * (1.0f - S06)));
    UnloadRobotMover->SetRelativeRotation(FRotator(0.0f, 70.0f * Unload, 0.0f));
    FormedPanelMover->SetRelativeLocation(FVector(0.0f, 300.0f * Output, 80.0f * FMath::Sin(PI * Output)));

    auto ApplyTranslation = [](TArray<TWeakObjectPtr<AActor>>& Actors, const TArray<FTransform>& Rest, const FVector& Offset)
    {
        for (int32 Index = 0; Index < Actors.Num(); ++Index)
        {
            if (!Actors[Index].IsValid() || !Rest.IsValidIndex(Index)) continue;
            FTransform Pose = Rest[Index];
            Pose.AddToTranslation(Offset);
            Actors[Index]->SetActorTransform(Pose);
        }
    };
    ApplyTranslation(DestackPresentations, DestackRestTransforms,
        FVector(0.0f, 0.0f, DestackLiftTravelCm * Destack));
    // Legacy tagged map actors are still supported in isolated validation maps. Apply
    // the same per-gap source/pick/handoff/reassemble pose as the native hierarchy;
    // the former shared wave moved every transfer at once and could pull presentations
    // away from their authored assembly.
    for (int32 Index = 0; Index < TransferPresentations.Num(); ++Index)
    {
        if (!TransferPresentations[Index].IsValid() || !TransferRestTransforms.IsValidIndex(Index)) continue;
        int32 StageIndex = INDEX_NONE;
        for (int32 CandidateStage = 0; CandidateStage < 5; ++CandidateStage)
        {
            const FName StageTag(*FString::Printf(TEXT("LB.PressTrain.Stage.S%02d"), CandidateStage + 2));
            if (TransferPresentations[Index]->ActorHasTag(StageTag))
            {
                StageIndex = CandidateStage;
                break;
            }
        }
        FTransform Pose = TransferRestTransforms[Index];
        if (StageIndex != INDEX_NONE)
        {
            const FVector2D TransferPoseForStage = TransferGapPose[StageIndex + 1];
            Pose.AddToTranslation(FVector(0.0f, TransferPoseForStage.X, TransferPoseForStage.Y));
        }
        TransferPresentations[Index]->SetActorTransform(Pose);
    }

    const float StageStrokes[5] = { S02, S03, S04, S05, S06 };
    const float StageStrokeCm[5] = { 80.0f, 65.0f, 60.0f, 55.0f, 60.0f };
    for (int32 StageIndex = 0; StageIndex < 5; ++StageIndex)
    {
        // Tagged presentations use the same closed/contact rest authority as the
        // approved native press parts: open upward while idle, return to rest at peak.
        const FVector StrokeOffset(0.0f, 0.0f,
            StageStrokeCm[StageIndex] * (1.0f - StageStrokes[StageIndex]));
        ApplyTranslation(StageSlidePresentations[StageIndex], StageSlideRestTransforms[StageIndex], StrokeOffset);
        ApplyTranslation(StageUpperDiePresentations[StageIndex], StageUpperDieRestTransforms[StageIndex], StrokeOffset);

        const float StageBegin[5] = { 0.08f, 0.30f, 0.46f, 0.62f, 0.78f };
        const float StageEnd[5] = { 0.30f, 0.46f, 0.62f, 0.78f, 0.91f };
        const bool bShowWorkpiece = bMoving && !InProcessBlankId.IsNone()
            && Progress >= StageBegin[StageIndex] && Progress < StageEnd[StageIndex];
        for (TWeakObjectPtr<AActor>& Actor : CarriedWorkpiecePresentations[StageIndex])
        {
            if (Actor.IsValid()) Actor->SetActorHiddenInGame(!bShowWorkpiece);
        }
    }

    for (int32 Index = 0; Index < UnloadRobotPresentations.Num(); ++Index)
    {
        if (!UnloadRobotPresentations[Index].IsValid() || !UnloadRobotRestTransforms.IsValidIndex(Index)) continue;
        FTransform Pose = UnloadRobotRestTransforms[Index];
        const FQuat Yaw(FVector::UpVector, FMath::DegreesToRadians(35.0f * Unload));
        Pose.SetRotation(Yaw * Pose.GetRotation());
        UnloadRobotPresentations[Index]->SetActorTransform(Pose);
    }
    ApplyTranslation(FormedPanelPresentations, FormedPanelRestTransforms,
        FVector(0.0f, 300.0f * Output, 80.0f * FMath::Sin(PI * Output)));

    // Authored gate meshes place the actor pivot on the hinge edge.  Opening an
    // interlock is visible even while isolated; process permissives still own
    // whether motion may start.
    for (int32 Index = 0; Index < AccessGatePresentations.Num(); ++Index)
    {
        if (!AccessGatePresentations[Index].IsValid() || !AccessGateRestTransforms.IsValidIndex(Index)) continue;
        FTransform Pose = AccessGateRestTransforms[Index];
        const float OpenDegrees = bAccessInterlocksClosed ? 0.0f : 72.0f;
        Pose.SetRotation(FQuat(FVector::UpVector, FMath::DegreesToRadians(OpenDegrees)) * Pose.GetRotation());
        AccessGatePresentations[Index]->SetActorTransform(Pose);
    }
    for (int32 Index = 0; Index < FlywheelPresentations.Num(); ++Index)
    {
        if (!FlywheelPresentations[Index].IsValid() || !FlywheelRestTransforms.IsValidIndex(Index)) continue;
        FTransform Pose = FlywheelRestTransforms[Index];
        const float Seconds = RunningHours * 3600.0f;
        const float Angle = State == ELBPressTrainAState::Cycling ? FMath::Fmod(Seconds * 180.0f, 360.0f) : 0.0f;
        Pose.SetRotation(FQuat(FVector::YAxisVector, FMath::DegreesToRadians(Angle)) * Pose.GetRotation());
        FlywheelPresentations[Index]->SetActorTransform(Pose);
    }

    auto SetBeaconVisible = [](TArray<TWeakObjectPtr<AActor>>& Actors, bool bVisible)
    {
        for (TWeakObjectPtr<AActor>& Actor : Actors)
        {
            if (Actor.IsValid()) Actor->SetActorHiddenInGame(!bVisible);
        }
    };
    SetBeaconVisible(RedBeaconPresentations, State == ELBPressTrainAState::Fault);
    SetBeaconVisible(AmberBeaconPresentations,
        State == ELBPressTrainAState::Ready || State == ELBPressTrainAState::Stopping);
    SetBeaconVisible(GreenBeaconPresentations, State == ELBPressTrainAState::Cycling);
}

void ALBPressTrainAStation::BindMapPresentation()
{
    DestackPresentations.Reset(); DestackRestTransforms.Reset();
    TransferPresentations.Reset(); TransferRestTransforms.Reset();
    for (int32 StageIndex = 0; StageIndex < 5; ++StageIndex)
    {
        StageSlidePresentations[StageIndex].Reset(); StageSlideRestTransforms[StageIndex].Reset();
        StageUpperDiePresentations[StageIndex].Reset(); StageUpperDieRestTransforms[StageIndex].Reset();
        CarriedWorkpiecePresentations[StageIndex].Reset(); CarriedWorkpieceRestTransforms[StageIndex].Reset();
    }
    UnloadRobotPresentations.Reset(); UnloadRobotRestTransforms.Reset();
    FormedPanelPresentations.Reset(); FormedPanelRestTransforms.Reset();
    AccessGatePresentations.Reset(); AccessGateRestTransforms.Reset();
    FlywheelPresentations.Reset(); FlywheelRestTransforms.Reset();
    RedBeaconPresentations.Reset(); AmberBeaconPresentations.Reset(); GreenBeaconPresentations.Reset();

    auto MakeRuntimeMovable = [](AActor* Actor)
    {
        if (Actor && Actor->GetRootComponent())
        {
            Actor->GetRootComponent()->SetMobility(EComponentMobility::Movable);
        }
    };

    // Isolated validation maps intentionally use the original shared presentation
    // tags.  A combined Press Shop contains four copies of that presentation, so
    // each installed train is additionally tagged with its own authority scope.
    // Use the scope when it exists and retain the proven isolated-map fallback
    // when it does not.
    const FName InstalledScopeTag(*FString::Printf(
        TEXT("LB.PressTrain.Installed.%s"), *TrainId.ToString().ToUpper()));
    bool bUseInstalledScope = false;
    for (TActorIterator<AActor> ScopeIt(GetWorld()); ScopeIt; ++ScopeIt)
    {
        const AActor* Candidate = *ScopeIt;
        if (Candidate && Candidate != this && Candidate->ActorHasTag(InstalledScopeTag))
        {
            bUseInstalledScope = true;
            break;
        }
    }

    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        AActor* Actor = *It;
        if (!Actor || Actor == this) continue;
        if (bUseInstalledScope && !Actor->ActorHasTag(InstalledScopeTag)) continue;
        if (Actor->ActorHasTag(TEXT("LB.PressTrain.Role.destack_lift")))
        {
            MakeRuntimeMovable(Actor);
            DestackPresentations.Add(Actor); DestackRestTransforms.Add(Actor->GetActorTransform());
        }
        if (Actor->ActorHasTag(TEXT("LB.PressTrain.Role.transfer_crossbar"))
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.transfer_gripper")))
        {
            MakeRuntimeMovable(Actor);
            TransferPresentations.Add(Actor); TransferRestTransforms.Add(Actor->GetActorTransform());
        }

        int32 StageIndex = INDEX_NONE;
        for (int32 CandidateStage = 0; CandidateStage < 5; ++CandidateStage)
        {
            const FName StageTag(*FString::Printf(TEXT("LB.PressTrain.Stage.S%02d"), CandidateStage + 2));
            if (Actor->ActorHasTag(StageTag))
            {
                StageIndex = CandidateStage;
                break;
            }
        }
        if (StageIndex != INDEX_NONE && Actor->ActorHasTag(TEXT("LB.PressTrain.Role.moving_press_slide")))
        {
            MakeRuntimeMovable(Actor);
            StageSlidePresentations[StageIndex].Add(Actor);
            StageSlideRestTransforms[StageIndex].Add(Actor->GetActorTransform());
        }
        if (StageIndex != INDEX_NONE && Actor->ActorHasTag(TEXT("LB.PressTrain.Role.moving_upper_die")))
        {
            MakeRuntimeMovable(Actor);
            StageUpperDiePresentations[StageIndex].Add(Actor);
            StageUpperDieRestTransforms[StageIndex].Add(Actor->GetActorTransform());
        }
        if (StageIndex != INDEX_NONE && Actor->ActorHasTag(TEXT("LB.PressTrain.Role.carried_workpiece_state")))
        {
            MakeRuntimeMovable(Actor);
            CarriedWorkpiecePresentations[StageIndex].Add(Actor);
            CarriedWorkpieceRestTransforms[StageIndex].Add(Actor->GetActorTransform());
        }

        const bool bHasHierarchicalRobotRoot = Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_shoulder_runtime"));
        const bool bIsHierarchicalRobotMember = bHasHierarchicalRobotRoot
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_upper_arm_runtime"))
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_elbow_runtime"))
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_forearm_runtime"))
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_wrist_runtime"))
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_gripper_runtime"))
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_tool_runtime"));
        const bool bHasLegacyRobot = Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_arm"))
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_joint"))
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_wrist"))
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.unload_robot_gripper"));
        if (bIsHierarchicalRobotMember)
        {
            // Static attached children do not follow a movable shoulder root in PIE. Make the
            // complete authored hierarchy movable, while retaining only the shoulder as the
            // single native motion authority so its descendants follow without double rotation.
            MakeRuntimeMovable(Actor);
        }
        if (bHasHierarchicalRobotRoot || bHasLegacyRobot)
        {
            MakeRuntimeMovable(Actor);
            UnloadRobotPresentations.Add(Actor); UnloadRobotRestTransforms.Add(Actor->GetActorTransform());
        }
        if (Actor->ActorHasTag(TEXT("LB.PressTrain.Role.visible_formed_panel"))
            || Actor->ActorHasTag(TEXT("LB.PressTrain.Role.formed_panel_positive_y_discharge")))
        {
            MakeRuntimeMovable(Actor);
            FormedPanelPresentations.Add(Actor); FormedPanelRestTransforms.Add(Actor->GetActorTransform());
        }
        if (Actor->ActorHasTag(TEXT("LB.PressTrain.Role.access_gate")))
        {
            MakeRuntimeMovable(Actor);
            AccessGatePresentations.Add(Actor); AccessGateRestTransforms.Add(Actor->GetActorTransform());
        }
        if (Actor->ActorHasTag(TEXT("LB.PressTrain.Role.flywheel_rotor")))
        {
            MakeRuntimeMovable(Actor);
            FlywheelPresentations.Add(Actor); FlywheelRestTransforms.Add(Actor->GetActorTransform());
        }
        if (Actor->ActorHasTag(TEXT("LB.PressTrain.Role.state_beacon_red"))) RedBeaconPresentations.Add(Actor);
        if (Actor->ActorHasTag(TEXT("LB.PressTrain.Role.state_beacon_amber"))) AmberBeaconPresentations.Add(Actor);
        if (Actor->ActorHasTag(TEXT("LB.PressTrain.Role.state_beacon_green"))) GreenBeaconPresentations.Add(Actor);
        ATextRenderActor* TextActor = Cast<ATextRenderActor>(Actor);
        if (TextActor && (TextActor->ActorHasTag(TEXT("LB.HMI.PressTrain.LiveState"))
            || TextActor->ActorHasTag(TEXT("LB.HMI.PressTrainA.LiveState"))))
        {
            HMIStatePresentation = TextActor;
        }
    }
}

void ALBPressTrainAStation::UpdateHMITextPresentation()
{
    if (!HMIStatePresentation.IsValid()) return;
    UTextRenderComponent* Text = HMIStatePresentation->GetTextRender();
    if (!Text) return;
    const UEnum* StateEnum = StaticEnum<ELBPressTrainAState>();
    const UEnum* PhaseEnum = StaticEnum<ELBPressTrainAPhase>();
    const UEnum* FaultEnum = StaticEnum<ELBPressTrainAFault>();
    const FString StateName = StateEnum ? StateEnum->GetNameStringByValue(static_cast<int64>(State)).ToUpper() : TEXT("UNKNOWN");
    FString PhaseName = PhaseEnum ? PhaseEnum->GetNameStringByValue(static_cast<int64>(Phase)).ToUpper() : TEXT("UNKNOWN");
    PhaseName.ReplaceInline(TEXT("DESTACKANDLOAD"), TEXT("DESTACK / LOAD"));
    PhaseName.ReplaceInline(TEXT("TRANSFERTO"), TEXT("TRANSFER TO "));
    PhaseName.ReplaceInline(TEXT("UNLOADANDINSPECT"), TEXT("UNLOAD / INSPECT"));
    PhaseName.ReplaceInline(TEXT("STILLAGEOUTPUT"), TEXT("STILLAGE OUTPUT"));
    Text->SetHorizontalAlignment(EHTA_Center);
    Text->SetVerticalAlignment(EVRTA_TextCenter);
    Text->SetWorldSize(10.0f);
    Text->SetHorizSpacingAdjust(0.0f);
    if (ActiveFault != ELBPressTrainAFault::None)
    {
        FString FaultName = FaultEnum ? FaultEnum->GetNameStringByValue(static_cast<int64>(ActiveFault)).ToUpper() : TEXT("FAULT");
        FaultName.ReplaceInline(TEXT("ACCESSINTERLOCKOPEN"), TEXT("ACCESS INTERLOCK OPEN"));
        FaultName.ReplaceInline(TEXT("EMERGENCYSTOPACTIVE"), TEXT("EMERGENCY STOP ACTIVE"));
        FaultName.ReplaceInline(TEXT("SAFETYCIRCUITUNHEALTHY"), TEXT("SAFETY CIRCUIT UNHEALTHY"));
        FaultName.ReplaceInline(TEXT("HYDRAULICPRESSURELOW"), TEXT("HYDRAULIC PRESSURE LOW"));
        FaultName.ReplaceInline(TEXT("RESERVEDBLANKUNAVAILABLE"), TEXT("RESERVED BLANK UNAVAILABLE"));
        FaultName.ReplaceInline(TEXT("INSPECTIONUNAVAILABLE"), TEXT("INSPECTION UNAVAILABLE"));
        FaultName.ReplaceInline(TEXT("STILLAGEOUTPUTBLOCKED"), TEXT("STILLAGE OUTPUT BLOCKED"));
        Text->SetText(FText::FromString(FString::Printf(TEXT("%s | FAULT\n%s\n%s"), *TrainDisplayName, *FaultName,
            bAlarmAcknowledged ? TEXT("ACKNOWLEDGED") : TEXT("ACK REQUIRED"))));
        Text->SetTextRenderColor(FColor(220, 45, 35));
    }
    else
    {
        Text->SetText(FText::FromString(FString::Printf(TEXT("%s | %s\n%s\n%s | GOOD %d\nOUTPUT BUFFER %d"),
            *TrainDisplayName, *StateName, *PartFamily, *PhaseName, GoodPanels, PendingPanelIds.Num())));
        Text->SetTextRenderColor(State == ELBPressTrainAState::Cycling
            ? TrainAccentColor.ToFColor(true) : FColor(225, 166, 0));
    }
}

#undef LOCTEXT_NAMESPACE
