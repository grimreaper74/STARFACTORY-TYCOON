#include "LBPR005Station.h"

#include "Components/SceneComponent.h"
#include "Components/AudioComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/WidgetComponent.h"
#include "LBPR005HMIWidget.h"
#include "Sound/SoundBase.h"
#include "Sound/SoundWave.h"
#include "UObject/ConstructorHelpers.h"

#define LOCTEXT_NAMESPACE "LineBossPR005"

ALBPR005Station::ALBPR005Station()
{
    PrimaryActorTick.bCanEverTick = true;

    StationRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PR005_StationRoot"));
    SetRootComponent(StationRoot);

    CoilCarMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR005_CoilCarMover"));
    CoilCarMover->SetupAttachment(StationRoot);
    MandrelMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR005_MandrelMover"));
    MandrelMover->SetupAttachment(StationRoot);
    PayoffCoilMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR005_PayoffCoilMover"));
    PayoffCoilMover->SetupAttachment(MandrelMover);
    StripMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR005_StripMover"));
    StripMover->SetupAttachment(StationRoot);
    CropClampMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR005_CropClampMover"));
    CropClampMover->SetupAttachment(StationRoot);
    CropShearMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR005_CropShearMover"));
    CropShearMover->SetupAttachment(StationRoot);
    CropPieceMover = CreateDefaultSubobject<USceneComponent>(TEXT("PR005_CropPieceMover"));
    CropPieceMover->SetupAttachment(StationRoot);

    OperatorHMI = CreateDefaultSubobject<UWidgetComponent>(TEXT("PR005_OperatorHMI"));
    OperatorHMI->SetupAttachment(StationRoot);
    OperatorHMI->SetWidgetClass(ULBPR005HMIWidget::StaticClass());
    OperatorHMI->SetWidgetSpace(EWidgetSpace::World);
    OperatorHMI->SetEditTimeUsable(true);
    OperatorHMI->SetDrawSize(FVector2D(1024.0f, 768.0f));
    OperatorHMI->SetBlendMode(EWidgetBlendMode::Opaque);
    OperatorHMI->SetBackgroundColor(FLinearColor(0.007f, 0.012f, 0.014f, 1.0f));
    OperatorHMI->SetTwoSided(true);
    OperatorHMI->SetTickWhenOffscreen(true);
    OperatorHMI->SetManuallyRedraw(false);
    OperatorHMI->SetRedrawTime(0.0f);
    OperatorHMI->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    OperatorHMI->SetCollisionResponseToAllChannels(ECR_Ignore);
    OperatorHMI->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    OperatorHMI->SetCanEverAffectNavigation(false);
    // The verified PR-005 source screen is (-296.7, +280.0, 110.5) cm in
    // its validation map. The Press Shop assembly is authored at -90 degrees,
    // so its station-relative full-map transform is (+280.0, +296.7, 110.5).
    OperatorHMI->SetRelativeLocation(FVector(280.0f, 296.7f, 110.5f));
    OperatorHMI->SetRelativeRotation(FRotator(20.0f, 90.0f, 0.0f));
    OperatorHMI->SetRelativeScale3D(FVector(0.033203125f));

    // UE command-line PIE can expose a WidgetComponent render-target fallback.
    // Keep the live widget as the authoritative interaction host, while the
    // following status-driven text remains deterministic in validation captures.
    OperatorHMI->SetVisibility(false, false);
    OperatorHMI->SetHiddenInGame(true, false);

    HMITextRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PR005_HMITextRoot"));
    HMITextRoot->SetupAttachment(StationRoot);
    HMITextRoot->SetRelativeLocation(FVector(280.0f, 296.7f, 110.5f));
    HMITextRoot->SetRelativeRotation(FRotator(20.0f, 90.0f, 0.0f));

    const auto CreateHMIText = [this](const TCHAR* Name, const FText& Text, const FColor Colour,
        const float WorldSize, const float LocalZ)
    {
        UTextRenderComponent* Component = CreateDefaultSubobject<UTextRenderComponent>(Name);
        Component->SetupAttachment(HMITextRoot);
        Component->SetText(Text);
        Component->SetTextRenderColor(Colour);
        Component->SetHorizontalAlignment(EHTA_Center);
        Component->SetVerticalAlignment(EVRTA_TextCenter);
        Component->SetWorldSize(WorldSize);
        Component->SetRelativeLocation(FVector(0.8f, 0.0f, LocalZ));
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCastShadow(false);
        return Component;
    };
    HMIBrandText = CreateHMIText(TEXT("PR005_HMI_BrandText"),
        FText::FromString(TEXT("CAIRNWELL AUTOMOTIVE / MOORCROSS WORKS")), FColor(226, 224, 212), 1.15f, 9.8f);
    HMIStationText = CreateHMIText(TEXT("PR005_HMI_StationText"),
        FText::FromString(TEXT("PR-005 / DECOILER + THREADER")), FColor(110, 128, 130), 1.35f, 6.8f);
    HMIStateText = CreateHMIText(TEXT("PR005_HMI_StateText"),
        FText::FromString(TEXT("NO STATION")), FColor(15, 184, 112), 1.65f, 3.5f);
    HMICoilText = CreateHMIText(TEXT("PR005_HMI_CoilText"),
        FText::FromString(TEXT("COIL  -")), FColor(226, 224, 212), 1.25f, 0.3f);
    HMIRecipeText = CreateHMIText(TEXT("PR005_HMI_RecipeText"),
        FText::FromString(TEXT("RECIPE  -")), FColor(226, 224, 212), 1.15f, -2.6f);
    HMIPermissiveText = CreateHMIText(TEXT("PR005_HMI_PermissiveText"),
        FText::FromString(TEXT("PERMISSIVES  0 / 4")), FColor(227, 166, 0), 1.15f, -5.5f);
    HMIActionText = CreateHMIText(TEXT("PR005_HMI_ActionText"),
        FText::FromString(TEXT("[ REVIEW PERMISSIVES ]")), FColor(227, 166, 0), 1.35f, -9.0f);

    const auto CreateSpatialAudio = [this](const TCHAR* Name, USceneComponent* Parent,
        const FVector& RelativeLocation, const float InnerRadius, const float FalloffDistance)
    {
        UAudioComponent* Component = CreateDefaultSubobject<UAudioComponent>(Name);
        Component->SetupAttachment(Parent ? Parent : StationRoot.Get());
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

    HPUAudio = CreateSpatialAudio(TEXT("PR005_Audio_HPU"), StationRoot,
        FVector(-185.0f, 185.0f, 72.0f), 280.0f, 2200.0f);
    CoilCarAudio = CreateSpatialAudio(TEXT("PR005_Audio_CoilCar"), CoilCarMover,
        FVector::ZeroVector, 220.0f, 1800.0f);
    RollerDriveAudio = CreateSpatialAudio(TEXT("PR005_Audio_RollerDrive"), StripMover,
        FVector(0.0f, 80.0f, 65.0f), 260.0f, 2100.0f);
    StripMotionAudio = CreateSpatialAudio(TEXT("PR005_Audio_StripMotion"), StripMover,
        FVector(0.0f, -80.0f, 35.0f), 220.0f, 1700.0f);
    WarningAlarmAudio = CreateSpatialAudio(TEXT("PR005_Audio_WarningAlarm"), HMITextRoot,
        FVector(0.0f, 0.0f, 35.0f), 500.0f, 4200.0f);
    ActuatorCueAudio = CreateSpatialAudio(TEXT("PR005_Audio_ActuatorCue"), MandrelMover,
        FVector::ZeroVector, 180.0f, 1500.0f);
    SafetyCueAudio = CreateSpatialAudio(TEXT("PR005_Audio_SafetyCue"), HMITextRoot,
        FVector::ZeroVector, 280.0f, 2300.0f);
    TransportCueAudio = CreateSpatialAudio(TEXT("PR005_Audio_TransportCue"), CoilCarMover,
        FVector::ZeroVector, 220.0f, 1800.0f);

    const auto LoadSound = [](const TCHAR* ObjectPath) -> USoundBase*
    {
        ConstructorHelpers::FObjectFinder<USoundBase> Finder(ObjectPath);
        return Finder.Succeeded() ? Finder.Object : nullptr;
    };
    const TCHAR* AudioRoot = TEXT("/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Audio/");
    USoundBase* HPUSound = LoadSound(*FString::Printf(TEXT("%sPR005_HPU_Idle_Loop_v001.PR005_HPU_Idle_Loop_v001"), AudioRoot));
    USoundBase* CoilCarTravelSound = LoadSound(*FString::Printf(TEXT("%sPR005_CoilCar_Travel_Loop_v001.PR005_CoilCar_Travel_Loop_v001"), AudioRoot));
    USoundBase* RollerSound = LoadSound(*FString::Printf(TEXT("%sPR005_RollerDrive_Loop_v001.PR005_RollerDrive_Loop_v001"), AudioRoot));
    USoundBase* StripSound = LoadSound(*FString::Printf(TEXT("%sPR005_StripMotion_Loop_v001.PR005_StripMotion_Loop_v001"), AudioRoot));
    USoundBase* AlarmSound = LoadSound(*FString::Printf(TEXT("%sPR005_WarningAlarm_Loop_v001.PR005_WarningAlarm_Loop_v001"), AudioRoot));
    CoilCarStartSound = LoadSound(*FString::Printf(TEXT("%sPR005_CoilCar_Start_v001.PR005_CoilCar_Start_v001"), AudioRoot));
    CoilCarStopSound = LoadSound(*FString::Printf(TEXT("%sPR005_CoilCar_Stop_v001.PR005_CoilCar_Stop_v001"), AudioRoot));
    MandrelExpandSound = LoadSound(*FString::Printf(TEXT("%sPR005_Mandrel_Expand_v001.PR005_Mandrel_Expand_v001"), AudioRoot));
    KeeperArmEngageSound = LoadSound(*FString::Printf(TEXT("%sPR005_KeeperArm_Engage_v001.PR005_KeeperArm_Engage_v001"), AudioRoot));
    GateInterlockSound = LoadSound(*FString::Printf(TEXT("%sPR005_GateInterlock_v001.PR005_GateInterlock_v001"), AudioRoot));
    ControlledStopSound = LoadSound(*FString::Printf(TEXT("%sPR005_ControlledStop_v001.PR005_ControlledStop_v001"), AudioRoot));
    EmergencyStopSound = LoadSound(*FString::Printf(TEXT("%sPR005_EmergencyStop_v001.PR005_EmergencyStop_v001"), AudioRoot));

    const auto ConfigureLoop = [](USoundBase* Sound)
    {
        if (USoundWave* Wave = Cast<USoundWave>(Sound))
        {
            Wave->bLooping = true;
        }
    };
    ConfigureLoop(HPUSound);
    ConfigureLoop(CoilCarTravelSound);
    ConfigureLoop(RollerSound);
    ConfigureLoop(StripSound);
    ConfigureLoop(AlarmSound);
    HPUAudio->SetSound(HPUSound);
    CoilCarAudio->SetSound(CoilCarTravelSound);
    RollerDriveAudio->SetSound(RollerSound);
    StripMotionAudio->SetSound(StripSound);
    WarningAlarmAudio->SetSound(AlarmSound);
}

void ALBPR005Station::BeginPlay()
{
    Super::BeginPlay();
    if (OperatorHMI)
    {
        OperatorHMI->InitWidget();
        if (ULBPR005HMIWidget* Widget = Cast<ULBPR005HMIWidget>(OperatorHMI->GetUserWidgetObject()))
        {
            Widget->BindStation(this);
        }
    }
    ClampRest = CropClampMover->GetRelativeLocation();
    ShearRest = CropShearMover->GetRelativeLocation();
    CropPieceRest = CropPieceMover->GetRelativeLocation();
    CoilCarRest = CoilCarMover->GetRelativeLocation();
    PayoffCoilRest = PayoffCoilMover->GetRelativeLocation();
    StripRest = StripMover->GetRelativeLocation();
    MandrelRest = MandrelMover->GetRelativeRotation();
    StripRestScale = StripMover->GetRelativeScale3D();
    PayoffCoilRestScale = PayoffCoilMover->GetRelativeScale3D();
    ApplyMachinePose();
    UpdateCoilPresentation();
    UpdateHMITextPresentation();
    UpdateAudioForState(MachineState, false);
}

void ALBPR005Station::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    PhaseElapsedSeconds += DeltaSeconds;
    HMIRefreshAccumulator += FMath::Max(0.0f, DeltaSeconds);
    if (bCoilLoadingPresentationActive)
    {
        CoilLoadingPresentationElapsed += FMath::Max(0.0f, DeltaSeconds);
        CoilLoadingPresentationProgress = FMath::Clamp(
            CoilLoadingPresentationElapsed / CoilLoadingPresentationDuration, 0.0f, 1.0f);
        if (CoilLoadingPresentationProgress >= 1.0f)
        {
            bCoilLoadingPresentationActive = false;
            Checklist.bCoilCarPositioned = true;
            PlayOneShot(TransportCueAudio, CoilCarStopSound, 0.42f);
            UpdateAudioForState(MachineState, false);
        }
    }

    switch (MachineState)
    {
    case ELBStationState::DryCycle:
        if (PhaseElapsedSeconds >= DryCycleDuration)
        {
            Checklist.bDryCycleComplete = true;
            SetMachineState(ELBStationState::FirstOffValidation);
        }
        break;
    case ELBStationState::Starting:
        if (PhaseElapsedSeconds >= StartingDuration)
        {
            SetMachineState(ELBStationState::Running);
        }
        break;
    case ELBStationState::Running:
        StripTravelMetres += DeltaSeconds * StripSpeedMetresPerSecond;
        RunningHours += DeltaSeconds / 3600.0f;
        if (StripTravelMetres - LastReportedCycleDistance >= CyclePitchMetres)
        {
            ++CycleCount;
            LastReportedCycleDistance = StripTravelMetres;
            OnProductionUpdated.Broadcast(CycleCount, StripTravelMetres);
        }
        break;
    case ELBStationState::Stopping:
        if (PhaseElapsedSeconds >= StoppingDuration)
        {
            SetMachineState(ELBStationState::Idle);
        }
        break;
    default:
        break;
    }

    ApplyMachinePose();
    if (HMIRefreshAccumulator >= 0.1f)
    {
        HMIRefreshAccumulator = 0.0f;
        UpdateHMITextPresentation();
    }
}

void ALBPR005Station::SetMachineState(ELBStationState NewState)
{
    if (MachineState == NewState)
    {
        return;
    }
    const ELBStationState Previous = MachineState;
    MachineState = NewState;
    PhaseElapsedSeconds = 0.0f;
    UpdateAudioForState(NewState, true);
    OnStateChanged.Broadcast(Previous, NewState);
}

void ALBPR005Station::SetLoopRequested(UAudioComponent* Component, bool bRequested, float TargetVolume)
{
    if (!Component || !Component->GetSound())
    {
        return;
    }
    if (bRequested)
    {
        if (!Component->IsPlaying())
        {
            Component->FadeIn(0.35f, TargetVolume);
        }
        else
        {
            Component->SetVolumeMultiplier(TargetVolume);
        }
    }
    else if (Component->IsPlaying())
    {
        Component->FadeOut(0.25f, 0.0f);
    }
}

void ALBPR005Station::PlayOneShot(UAudioComponent* Component, USoundBase* Sound, float Volume)
{
    if (!Component || !Sound)
    {
        return;
    }
    Component->Stop();
    Component->SetSound(Sound);
    Component->SetVolumeMultiplier(Volume);
    Component->Play();
    LastAudioCueId = Sound->GetFName();
    ++AudioCueSequence;
}

bool ALBPR005Station::IsAudioLayerRequested(FName LayerId) const
{
    if (LayerId == TEXT("hpu_idle"))
    {
        return bControlPowerOn && (MachineState == ELBStationState::ReadyForTest
            || MachineState == ELBStationState::Idle || MachineState == ELBStationState::Running);
    }
    if (LayerId == TEXT("coil_car_travel"))
    {
        return bCoilLoadingPresentationActive || MachineState == ELBStationState::ManualCommissioning
            || MachineState == ELBStationState::Setup;
    }
    if (LayerId == TEXT("roller_drive") || LayerId == TEXT("strip_motion"))
    {
        return MachineState == ELBStationState::DryCycle || MachineState == ELBStationState::Running;
    }
    if (LayerId == TEXT("warning_alarm"))
    {
        return MachineState == ELBStationState::Starting || MachineState == ELBStationState::Fault;
    }
    return false;
}

void ALBPR005Station::UpdateAudioForState(ELBStationState NewState, bool bPlayTransitionCues)
{
    SetLoopRequested(HPUAudio, IsAudioLayerRequested(TEXT("hpu_idle")), 0.24f);
    SetLoopRequested(CoilCarAudio, IsAudioLayerRequested(TEXT("coil_car_travel")), 0.30f);
    SetLoopRequested(RollerDriveAudio, IsAudioLayerRequested(TEXT("roller_drive")), 0.34f);
    SetLoopRequested(StripMotionAudio, IsAudioLayerRequested(TEXT("strip_motion")), 0.25f);
    SetLoopRequested(WarningAlarmAudio, IsAudioLayerRequested(TEXT("warning_alarm")),
        NewState == ELBStationState::Fault ? 0.60f : 0.46f);

    if (!bPlayTransitionCues)
    {
        return;
    }
    if (NewState == ELBStationState::Stopping)
    {
        PlayOneShot(ActuatorCueAudio, ControlledStopSound, 0.48f);
    }
    else if (NewState == ELBStationState::Blocked)
    {
        PlayOneShot(SafetyCueAudio, GateInterlockSound, 0.48f);
    }
}

void ALBPR005Station::SetControlPower(bool bEnabled)
{
    bControlPowerOn = bEnabled;
    if (!bEnabled)
    {
        ControlMode = ELBPR005ControlMode::Off;
        SetMachineState(ELBStationState::Isolated);
    }
    else if (MachineState == ELBStationState::Isolated || MachineState == ELBStationState::Unsurveyed)
    {
        SetMachineState(ELBStationState::SafeForAccess);
    }
}

bool ALBPR005Station::SetControlMode(ELBPR005ControlMode NewMode)
{
    if (!bControlPowerOn && NewMode != ELBPR005ControlMode::Off)
    {
        return false;
    }
    if ((MachineState == ELBStationState::Starting || MachineState == ELBStationState::Running)
        && NewMode != ELBPR005ControlMode::Automatic)
    {
        return false;
    }
    ControlMode = NewMode;
    return true;
}

bool ALBPR005Station::PressCycleStart()
{
    if (!bControlPowerOn || ActiveFault != ELBPR005Fault::None)
    {
        return false;
    }
    if (bCertifiedForProduction)
    {
        return ControlMode == ELBPR005ControlMode::Automatic && StartAutomaticProduction();
    }
    return ControlMode == ELBPR005ControlMode::Manual && BeginDryCycle();
}

void ALBPR005Station::SetUtilitiesAvailable(bool bAvailable)
{
    Checklist.bUtilitiesAvailable = bAvailable;
}

bool ALBPR005Station::LoadCoil(const FString& NewCoilId, float WidthMillimetres)
{
    TArray<FText> BlockingReasons;
    if (!CanLoadCoil(NewCoilId, WidthMillimetres, BlockingReasons))
    {
        return false;
    }
    const bool bWasEmpty = CoilId.IsEmpty();
    CoilId = NewCoilId;
    HeatId.Reset();
    SupplierLotId.Reset();
    TraceabilityBarcode.Reset();
    CoilWidthMillimetres = WidthMillimetres;
    Checklist.bCorrectCoilIdentified = ActiveRecipeId.IsNone() || CoilMatchesRecipe();
    UpdateCoilPresentation();
    if (bWasEmpty) StartCoilLoadingPresentation();
    return true;
}

bool ALBPR005Station::LoadCoilWithTraceability(const FString& NewCoilId, const FString& NewHeatId,
    const FString& NewSupplierLotId, const FString& NewTraceabilityBarcode, float WidthMillimetres)
{
    TArray<FText> BlockingReasons;
    if (!CanLoadCoil(NewCoilId, WidthMillimetres, BlockingReasons)
        || NewHeatId.IsEmpty() || NewSupplierLotId.IsEmpty() || NewTraceabilityBarcode.IsEmpty())
    {
        return false;
    }
    const bool bWasEmpty = CoilId.IsEmpty();
    CoilId = NewCoilId;
    HeatId = NewHeatId;
    SupplierLotId = NewSupplierLotId;
    TraceabilityBarcode = NewTraceabilityBarcode;
    CoilWidthMillimetres = WidthMillimetres;
    Checklist.bCorrectCoilIdentified = ActiveRecipeId.IsNone() || CoilMatchesRecipe();
    UpdateCoilPresentation();
    if (bWasEmpty) StartCoilLoadingPresentation();
    return true;
}

bool ALBPR005Station::CanLoadCoil(const FString& NewCoilId, float WidthMillimetres,
    TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (NewCoilId.IsEmpty()) BlockingReasons.Add(LOCTEXT("LoadCoilIdentity", "A coil identity is required."));
    if (WidthMillimetres <= 0.0f) BlockingReasons.Add(LOCTEXT("LoadCoilWidth", "A positive coil width is required."));
    if (!CoilId.IsEmpty() && CoilId != NewCoilId) BlockingReasons.Add(LOCTEXT("LoadCoilOccupied", "PR-005 already owns a different coil."));
    if (MachineState == ELBStationState::Starting || MachineState == ELBStationState::Running
        || MachineState == ELBStationState::Stopping || MachineState == ELBStationState::DryCycle)
    {
        BlockingReasons.Add(LOCTEXT("LoadCoilMotion", "PR-005 cannot accept a coil while machinery is moving."));
    }
    return BlockingReasons.IsEmpty();
}

bool ALBPR005Station::SelectRecipe(const FName NewRecipeId, float RequiredWidthMillimetres)
{
    if (NewRecipeId.IsNone() || RequiredWidthMillimetres <= 0.0f)
    {
        return false;
    }
    ActiveRecipeId = NewRecipeId;
    RequiredStripWidthMillimetres = RequiredWidthMillimetres;
    Checklist.bRecipeSelected = true;
    Checklist.bCorrectCoilIdentified = !CoilId.IsEmpty() && CoilMatchesRecipe();
    return true;
}

void ALBPR005Station::SetCoilCarPositioned(bool bPositioned)
{
    Checklist.bCoilCarPositioned = bPositioned;
    if (bPositioned && bCoilLoadingPresentationActive)
    {
        bCoilLoadingPresentationActive = false;
        CoilLoadingPresentationProgress = 1.0f;
        PlayOneShot(TransportCueAudio, CoilCarStopSound, 0.42f);
        UpdateAudioForState(MachineState, false);
    }
}

void ALBPR005Station::SetMandrelExpanded(bool bExpanded)
{
    const bool bWasExpanded = Checklist.bMandrelExpanded;
    Checklist.bMandrelExpanded = bExpanded;
    if (!bWasExpanded && bExpanded)
    {
        PlayOneShot(ActuatorCueAudio, MandrelExpandSound, 0.40f);
    }
}

void ALBPR005Station::SetKeeperAndSnubber(bool bKeeperIsEngaged, bool bSnubberIsEngaged)
{
    const bool bWasKeeperEngaged = Checklist.bKeeperEngaged;
    Checklist.bKeeperEngaged = bKeeperIsEngaged;
    Checklist.bSnubberEngaged = bSnubberIsEngaged;
    if (!bWasKeeperEngaged && bKeeperIsEngaged)
    {
        PlayOneShot(ActuatorCueAudio, KeeperArmEngageSound, 0.42f);
    }
}

void ALBPR005Station::SetGuardsClosed(bool bClosed)
{
    const bool bWasClosed = Checklist.bGuardsClosed;
    Checklist.bGuardsClosed = bClosed;
    if (bWasClosed != bClosed)
    {
        PlayOneShot(SafetyCueAudio, GateInterlockSound, 0.46f);
    }
    if (!bClosed && (MachineState == ELBStationState::Starting || MachineState == ELBStationState::Running))
    {
        RaiseFault(ELBPR005Fault::GateOrInterlockOpen);
    }
}

void ALBPR005Station::SetSafetyCircuitHealthy(bool bHealthy)
{
    Checklist.bSafetyCircuitReset = bHealthy;
    if (!bHealthy && (MachineState == ELBStationState::Starting || MachineState == ELBStationState::Running))
    {
        RaiseFault(ELBPR005Fault::GateOrInterlockOpen);
    }
}

void ALBPR005Station::SetStripThreaded(bool bThreaded)
{
    Checklist.bStripPeeledAndThreaded = bThreaded;
}

bool ALBPR005Station::BeginCommissioning()
{
    if (!bControlPowerOn || !Checklist.bUtilitiesAvailable)
    {
        return false;
    }
    SetMachineState(ELBStationState::ManualCommissioning);
    return true;
}

bool ALBPR005Station::BeginDryCycle()
{
    TArray<FText> BlockingReasons;
    if (!CanBeginDryCycle(BlockingReasons))
    {
        return false;
    }
    SetMachineState(ELBStationState::DryCycle);
    return true;
}

void ALBPR005Station::RecordFirstOffProduced()
{
    if (MachineState == ELBStationState::FirstOffValidation)
    {
        Checklist.bFirstOffProduced = true;
    }
}

bool ALBPR005Station::ApproveFirstOff()
{
    if (MachineState != ELBStationState::FirstOffValidation || !Checklist.bFirstOffProduced)
    {
        return false;
    }
    Checklist.bQualityApproved = true;
    bCertifiedForProduction = true;
    SetMachineState(ELBStationState::CertifiedForProduction);
    SetMachineState(ELBStationState::Idle);
    return true;
}

bool ALBPR005Station::StartAutomaticProduction()
{
    TArray<FText> BlockingReasons;
    if (!CanStartAutomatic(BlockingReasons))
    {
        return false;
    }
    SetMachineState(ELBStationState::Starting);
    return true;
}

void ALBPR005Station::RequestControlledStop()
{
    if (MachineState == ELBStationState::Running || MachineState == ELBStationState::Starting)
    {
        SetMachineState(ELBStationState::Stopping);
    }
}

void ALBPR005Station::RaiseFault(ELBPR005Fault Fault)
{
    if (Fault == ELBPR005Fault::None)
    {
        return;
    }
    StateBeforeFault = MachineState;
    ActiveFault = Fault;
    SetMachineState(ELBStationState::Fault);
    PlayOneShot(SafetyCueAudio, EmergencyStopSound, 0.62f);
    OnFaultRaised.Broadcast(Fault);
}

bool ALBPR005Station::ResetFault()
{
    if (MachineState != ELBStationState::Fault || ActiveFault == ELBPR005Fault::None)
    {
        return false;
    }
    if (!bControlPowerOn || !Checklist.bGuardsClosed || !Checklist.bSafetyCircuitReset)
    {
        return false;
    }
    ActiveFault = ELBPR005Fault::None;
    SetMachineState(bCertifiedForProduction ? ELBStationState::Idle : ELBStationState::ReadyForTest);
    return true;
}

bool ALBPR005Station::CanBeginDryCycle(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (!bControlPowerOn) BlockingReasons.Add(LOCTEXT("ControlPowerOff", "Control power is off"));
    if (ControlMode != ELBPR005ControlMode::Manual) BlockingReasons.Add(LOCTEXT("DryCycleMode", "Select MANUAL mode for commissioning dry cycle"));
    if (!Checklist.bUtilitiesAvailable) BlockingReasons.Add(LOCTEXT("UtilitiesUnavailable", "Utilities are unavailable"));
    if (!Checklist.bCorrectCoilIdentified) BlockingReasons.Add(LOCTEXT("IncorrectCoil", "Correct coil is not identified"));
    if (!Checklist.bRecipeSelected) BlockingReasons.Add(LOCTEXT("RecipeMissing", "Production recipe is not selected"));
    if (!Checklist.bCoilCarPositioned) BlockingReasons.Add(LOCTEXT("CoilCarNotPositioned", "Coil car is not positioned"));
    if (!Checklist.bMandrelExpanded) BlockingReasons.Add(LOCTEXT("MandrelNotExpanded", "Mandrel is not expanded"));
    if (!Checklist.bKeeperEngaged) BlockingReasons.Add(LOCTEXT("KeeperNotEngaged", "Keeper arm is not engaged"));
    if (!Checklist.bSnubberEngaged) BlockingReasons.Add(LOCTEXT("SnubberNotEngaged", "Snubber roll is not engaged"));
    if (!Checklist.bGuardsClosed) BlockingReasons.Add(LOCTEXT("GuardsOpen", "Guarding is open"));
    if (!Checklist.bSafetyCircuitReset) BlockingReasons.Add(LOCTEXT("SafetyNotReset", "Safety circuit is not reset"));
    if (!Checklist.bStripPeeledAndThreaded) BlockingReasons.Add(LOCTEXT("StripNotThreaded", "Strip is not peeled and threaded"));
    return BlockingReasons.IsEmpty();
}

bool ALBPR005Station::CanStartAutomatic(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (!bControlPowerOn) BlockingReasons.Add(LOCTEXT("AutoControlPowerOff", "Control power is off"));
    if (ControlMode != ELBPR005ControlMode::Automatic) BlockingReasons.Add(LOCTEXT("AutomaticMode", "Select AUTOMATIC mode"));
    if (!bCertifiedForProduction) BlockingReasons.Add(LOCTEXT("NotCertified", "Station is not certified for production"));
    if (!Checklist.bQualityApproved) BlockingReasons.Add(LOCTEXT("QualityNotApproved", "First-off quality approval is missing"));
    if (!Checklist.bGuardsClosed) BlockingReasons.Add(LOCTEXT("RunGuardsOpen", "Guarding is open"));
    if (!Checklist.bSafetyCircuitReset) BlockingReasons.Add(LOCTEXT("RunSafetyNotReset", "Safety circuit is not reset"));
    if (!CoilMatchesRecipe()) BlockingReasons.Add(LOCTEXT("RunRecipeMismatch", "Coil and recipe width do not match"));
    return BlockingReasons.IsEmpty();
}

float ALBPR005Station::GetPhaseProgress() const
{
    switch (MachineState)
    {
    case ELBStationState::DryCycle:
        return FMath::Clamp(PhaseElapsedSeconds / DryCycleDuration, 0.0f, 1.0f);
    case ELBStationState::Starting:
        return FMath::Clamp(PhaseElapsedSeconds / StartingDuration, 0.0f, 1.0f);
    case ELBStationState::Stopping:
        return FMath::Clamp(PhaseElapsedSeconds / StoppingDuration, 0.0f, 1.0f);
    default:
        return 0.0f;
    }
}

bool ALBPR005Station::CoilMatchesRecipe() const
{
    return !CoilId.IsEmpty()
        && !ActiveRecipeId.IsNone()
        && FMath::IsNearlyEqual(CoilWidthMillimetres, RequiredStripWidthMillimetres, CoilWidthToleranceMillimetres);
}

float ALBPR005Station::GetStripVisualWidthScale() const
{
    return CoilWidthMillimetres > 0.0f && AuthoredStripWidthMillimetres > 0.0f
        ? CoilWidthMillimetres / AuthoredStripWidthMillimetres
        : 1.0f;
}

float ALBPR005Station::GetCoilVisualWidthScale() const
{
    return CoilWidthMillimetres > 0.0f && AuthoredCoilWidthMillimetres > 0.0f
        ? CoilWidthMillimetres / AuthoredCoilWidthMillimetres
        : 1.0f;
}

float ALBPR005Station::GetVisualMotionTravelMetres() const
{
    // A dry cycle must visibly move the strip and mandrel without being counted
    // as produced material.  Production travel remains the saveable authority;
    // phase travel is a deterministic, transient commissioning presentation.
    const float DryCycleTravel = MachineState == ELBStationState::DryCycle
        ? PhaseElapsedSeconds * StripSpeedMetresPerSecond
        : 0.0f;
    return StripTravelMetres + DryCycleTravel;
}

FLBPR005HMIStatus ALBPR005Station::GetHMIStatus() const
{
    FLBPR005HMIStatus Status;
    Status.StationId = StationId;
    Status.MachineState = MachineState;
    Status.ActiveFault = ActiveFault;
    Status.ControlMode = ControlMode;
    Status.CoilId = CoilId;
    Status.RecipeId = ActiveRecipeId;
    Status.CoilWidthMillimetres = CoilWidthMillimetres;
    Status.RequiredWidthMillimetres = RequiredStripWidthMillimetres;
    Status.TargetSpeedMetresPerMinute = TargetSpeedMetresPerMinute;
    Status.PhaseProgress = GetPhaseProgress();
    Status.StripLengthMetres = StripTravelMetres;
    Status.CycleCount = CycleCount;
    Status.ScrapCount = ScrapCount;
    Status.bControlPowerOn = bControlPowerOn;
    Status.bUtilitiesAvailable = Checklist.bUtilitiesAvailable;
    Status.bGuardsClosed = Checklist.bGuardsClosed;
    Status.bSafetyCircuitHealthy = Checklist.bSafetyCircuitReset;
    Status.bCorrectCoilAndRecipe = Checklist.bCorrectCoilIdentified && Checklist.bRecipeSelected;
    Status.bDryCycleComplete = Checklist.bDryCycleComplete;
    Status.bQualityApproved = Checklist.bQualityApproved;
    Status.bCertifiedForProduction = bCertifiedForProduction;

    TArray<FText> DryCycleReasons;
    Status.bCanAuthoriseDryCycle = CanBeginDryCycle(DryCycleReasons);
    TArray<FText> AutomaticReasons;
    Status.bCanStartAutomatic = CanStartAutomatic(AutomaticReasons);
    Status.BlockingReasons = bCertifiedForProduction ? MoveTemp(AutomaticReasons) : MoveTemp(DryCycleReasons);
    return Status;
}

FLBPR005SaveState ALBPR005Station::CaptureSaveState() const
{
    FLBPR005SaveState Saved;
    Saved.StationId = StationId;
    Saved.MachineState = MachineState;
    Saved.StateBeforeFault = StateBeforeFault;
    Saved.ActiveFault = ActiveFault;
    Saved.ControlMode = ControlMode;
    Saved.Condition = Condition;
    Saved.Checklist = Checklist;
    Saved.CoilId = CoilId;
    Saved.HeatId = HeatId;
    Saved.SupplierLotId = SupplierLotId;
    Saved.TraceabilityBarcode = TraceabilityBarcode;
    Saved.ActiveRecipeId = ActiveRecipeId;
    Saved.CoilWidthMillimetres = CoilWidthMillimetres;
    Saved.RequiredStripWidthMillimetres = RequiredStripWidthMillimetres;
    Saved.StripTravelMetres = StripTravelMetres;
    Saved.CycleCount = CycleCount;
    Saved.ScrapCount = ScrapCount;
    Saved.RunningHours = RunningHours;
    Saved.TargetSpeedMetresPerMinute = TargetSpeedMetresPerMinute;
    Saved.bControlPowerOn = bControlPowerOn;
    Saved.bCertifiedForProduction = bCertifiedForProduction;
    return Saved;
}

bool ALBPR005Station::RestoreSaveState(const FLBPR005SaveState& SavedState)
{
    if ((SavedState.Version != 1 && SavedState.Version != 2) || SavedState.StationId != StationId)
    {
        return false;
    }

    StateBeforeFault = SavedState.StateBeforeFault;
    ActiveFault = SavedState.ActiveFault;
    ControlMode = SavedState.ControlMode;
    Condition = SavedState.Condition;
    Checklist = SavedState.Checklist;
    CoilId = SavedState.CoilId;
    HeatId = SavedState.Version >= 2 ? SavedState.HeatId : FString();
    SupplierLotId = SavedState.Version >= 2 ? SavedState.SupplierLotId : FString();
    TraceabilityBarcode = SavedState.Version >= 2 ? SavedState.TraceabilityBarcode : FString();
    ActiveRecipeId = SavedState.ActiveRecipeId;
    CoilWidthMillimetres = FMath::Max(0.0f, SavedState.CoilWidthMillimetres);
    RequiredStripWidthMillimetres = FMath::Max(0.0f, SavedState.RequiredStripWidthMillimetres);
    StripTravelMetres = FMath::Max(0.0f, SavedState.StripTravelMetres);
    CycleCount = FMath::Max(0, SavedState.CycleCount);
    ScrapCount = FMath::Max(0, SavedState.ScrapCount);
    RunningHours = FMath::Max(0.0f, SavedState.RunningHours);
    TargetSpeedMetresPerMinute = FMath::Max(0.0f, SavedState.TargetSpeedMetresPerMinute);
    bControlPowerOn = SavedState.bControlPowerOn;
    bCertifiedForProduction = SavedState.bCertifiedForProduction;

    const bool bWasInMotion = SavedState.MachineState == ELBStationState::DryCycle
        || SavedState.MachineState == ELBStationState::Starting
        || SavedState.MachineState == ELBStationState::Running
        || SavedState.MachineState == ELBStationState::Stopping;
    if (bWasInMotion)
    {
        MachineState = bCertifiedForProduction ? ELBStationState::Idle : ELBStationState::ReadyForTest;
        ControlMode = bControlPowerOn ? ELBPR005ControlMode::Manual : ELBPR005ControlMode::Off;
        Checklist.bSafetyCircuitReset = false;
        if (SavedState.MachineState == ELBStationState::DryCycle)
        {
            Checklist.bDryCycleComplete = false;
        }
    }
    else
    {
        MachineState = SavedState.MachineState;
    }

    if (!bControlPowerOn)
    {
        ControlMode = ELBPR005ControlMode::Off;
        MachineState = ELBStationState::Isolated;
    }
    PhaseElapsedSeconds = 0.0f;
    LastReportedCycleDistance = FMath::FloorToFloat(StripTravelMetres / CyclePitchMetres) * CyclePitchMetres;
    if (HasActorBegunPlay())
    {
        if (!CoilId.IsEmpty() && !Checklist.bCoilCarPositioned)
        {
            StartCoilLoadingPresentation();
        }
        else
        {
            bCoilLoadingPresentationActive = false;
            CoilLoadingPresentationProgress = 1.0f;
        }
        ApplyMachinePose();
        UpdateCoilPresentation();
        UpdateAudioForState(MachineState, false);
    }
    return true;
}

void ALBPR005Station::UpdateCoilPresentation()
{
    const bool bHasCoil = !CoilId.IsEmpty();
    for (AActor* Actor : PayoffCoilPresentationActors)
    {
        if (IsValid(Actor))
        {
            Actor->SetActorHiddenInGame(!bHasCoil);
            Actor->SetActorEnableCollision(bHasCoil);
        }
    }
}

void ALBPR005Station::StartCoilLoadingPresentation()
{
    Checklist.bCoilCarPositioned = false;
    CoilLoadingPresentationElapsed = 0.0f;
    CoilLoadingPresentationProgress = 0.0f;
    bCoilLoadingPresentationActive = true;
    PlayOneShot(TransportCueAudio, CoilCarStartSound, 0.42f);
    UpdateAudioForState(MachineState, false);
}

void ALBPR005Station::UpdateHMITextPresentation()
{
    if (!HMIStateText || !HMICoilText || !HMIRecipeText || !HMIPermissiveText || !HMIActionText)
    {
        return;
    }

    const FLBPR005HMIStatus Status = GetHMIStatus();
    const UEnum* StateEnum = StaticEnum<ELBStationState>();
    const FString StateName = StateEnum
        ? StateEnum->GetNameStringByValue(static_cast<int64>(Status.MachineState)).ToUpper()
        : TEXT("UNKNOWN");
    HMIStateText->SetText(FText::FromString(StateName));
    HMIStateText->SetTextRenderColor(Status.ActiveFault == ELBPR005Fault::None
        ? FColor(15, 184, 112) : FColor(199, 20, 10));

    HMICoilText->SetText(FText::FromString(Status.CoilId.IsEmpty()
        ? TEXT("COIL  NO COIL")
        : FString::Printf(TEXT("COIL  %s  /  %.0f mm"), *Status.CoilId, Status.CoilWidthMillimetres)));
    HMIRecipeText->SetText(FText::FromString(Status.RecipeId.IsNone()
        ? TEXT("RECIPE  NOT SELECTED")
        : FString::Printf(TEXT("RECIPE  %s  /  %.0f mm"), *Status.RecipeId.ToString(), Status.RequiredWidthMillimetres)));

    const int32 PermissiveCount = static_cast<int32>(Status.bControlPowerOn)
        + static_cast<int32>(Status.bCorrectCoilAndRecipe)
        + static_cast<int32>(Status.bGuardsClosed)
        + static_cast<int32>(Status.bSafetyCircuitHealthy);
    HMIPermissiveText->SetText(FText::FromString(FString::Printf(TEXT("PERMISSIVES  %d / 4"), PermissiveCount)));
    HMIPermissiveText->SetTextRenderColor(PermissiveCount == 4
        ? FColor(15, 184, 112) : FColor(227, 166, 0));

    if (bCoilLoadingPresentationActive)
    {
        HMIActionText->SetText(FText::FromString(FString::Printf(
            TEXT("[ COIL CAR LOADING  %.0f%% ]"), CoilLoadingPresentationProgress * 100.0f)));
        HMIActionText->SetTextRenderColor(FColor(15, 184, 112));
    }
    else
    {
        const bool bReady = Status.bCertifiedForProduction
            ? Status.bCanStartAutomatic : Status.bCanAuthoriseDryCycle;
        HMIActionText->SetText(FText::FromString(bReady
            ? (Status.bCertifiedForProduction ? TEXT("[ START AUTOMATIC ]") : TEXT("[ AUTHORISE DRY CYCLE ]"))
            : TEXT("[ REVIEW PERMISSIVES ]")));
        HMIActionText->SetTextRenderColor(bReady ? FColor(15, 184, 112) : FColor(227, 166, 0));
    }
}

void ALBPR005Station::ApplyMachinePose()
{
    CropClampMover->SetRelativeLocation(ClampRest);
    CropShearMover->SetRelativeLocation(ShearRest);
    CropPieceMover->SetRelativeLocation(CropPieceRest);

    const float StripWidthScale = GetStripVisualWidthScale();
    StripMover->SetRelativeScale3D(FVector(
        StripRestScale.X * StripWidthScale,
        StripRestScale.Y,
        StripRestScale.Z));
    const float CoilWidthScale = GetCoilVisualWidthScale();
    PayoffCoilMover->SetRelativeScale3D(FVector(
        PayoffCoilRestScale.X * CoilWidthScale,
        PayoffCoilRestScale.Y,
        PayoffCoilRestScale.Z));

    if (bCoilLoadingPresentationActive)
    {
        const float TravelAlpha = FMath::SmoothStep(0.0f, 1.0f,
            FMath::Clamp(CoilLoadingPresentationProgress / 0.68f, 0.0f, 1.0f));
        const float LiftAlpha = FMath::SmoothStep(0.0f, 1.0f,
            FMath::Clamp((CoilLoadingPresentationProgress - 0.68f) / 0.32f, 0.0f, 1.0f));
        const FVector LoadingOffset(
            FMath::Lerp(-220.0f, 0.0f, TravelAlpha),
            0.0f,
            FMath::Lerp(-38.0f, 0.0f, LiftAlpha));
        CoilCarMover->SetRelativeLocation(CoilCarRest + LoadingOffset);
        PayoffCoilMover->SetRelativeLocation(PayoffCoilRest + LoadingOffset);
    }
    else
    {
        CoilCarMover->SetRelativeLocation(CoilCarRest);
        PayoffCoilMover->SetRelativeLocation(PayoffCoilRest);
    }

    const bool bMovingStrip = MachineState == ELBStationState::DryCycle || MachineState == ELBStationState::Running;
    if (bMovingStrip)
    {
        const float MotionTravelMetres = GetVisualMotionTravelMetres();
        const float VisualTravel = FMath::Fmod(MotionTravelMetres * 100.0f, 25.0f);
        StripMover->SetRelativeLocation(StripRest + FVector(0.0f, VisualTravel, 0.0f));
        MandrelMover->SetRelativeRotation(MandrelRest + FRotator(MotionTravelMetres * 45.0f, 0.0f, 0.0f));
    }
    else
    {
        StripMover->SetRelativeLocation(StripRest);
        MandrelMover->SetRelativeRotation(MandrelRest);
    }
}

#undef LOCTEXT_NAMESPACE
