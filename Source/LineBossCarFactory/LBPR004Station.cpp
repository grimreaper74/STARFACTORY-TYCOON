#include "LBPR004Station.h"

#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Components/WidgetComponent.h"
#include "LBPR004HMIWidget.h"
#include "Misc/Crc.h"

#define LOCTEXT_NAMESPACE "LBPR004Station"

namespace
{
    const FName BandComponentType(TEXT("Band"));
    const FName ProtectorComponentType(TEXT("EdgeProtector"));
    const FName WrapComponentType(TEXT("WrapSection"));
    const FName CompactedBandCoilType(TEXT("CompactedBandCoil"));
    const FName CompactedPlasticBaleType(TEXT("CompactedPlasticBale"));
    const FName EdgeProtectorWasteType(TEXT("RecoveredEdgeProtector"));

    const FName BandActionContract(TEXT("CAPTURE_BOTH_ENDS__SNIP__KINKED_SPLINE_PULL__STRAIGHTENER_FEED__COMPACT_PANCAKE_WIND__TAIL_SECURE__VISIBLE_STEEL_BIN_EJECTION"));
    const FName ProtectorActionContract(TEXT("GRIP__DETACH__VISIBLE_BIN_ENTRY"));
    const FName WrapActionContract(TEXT("VACUUM_GRIP__FLEXIBLE_PEEL__NIP_ROLLER_FEED_ACK"));
    const FName FinalWrapActionContract(TEXT("VACUUM_GRIP__FLEXIBLE_PEEL__NIP_ROLLER_FEED__COMPACT_IRREGULAR_BALE__VISIBLE_PLASTIC_BIN_EJECTION"));

    struct FScopedBoolFlag
    {
        explicit FScopedBoolFlag(bool& InFlag)
            : Flag(InFlag)
        {
            Flag = true;
        }

        ~FScopedBoolFlag()
        {
            Flag = false;
        }

        bool& Flag;
    };

    bool IsNameSet(FName Value)
    {
        return !Value.IsNone();
    }
}

ALBPR004Station::ALBPR004Station()
{
    PrimaryActorTick.bCanEverTick = true;

    StationRoot = CreateDefaultSubobject<USceneComponent>(TEXT("StationRoot"));
    SetRootComponent(StationRoot);

    CradleMover = CreateDefaultSubobject<USceneComponent>(TEXT("CradleMover"));
    CradleMover->SetupAttachment(StationRoot);

    PersistentCoilRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PR004_PersistentCoilRoot"));
    PersistentCoilRoot->SetupAttachment(CradleMover);

    WrappedCoilVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PR004_WrappedCoilVisual"));
    WrappedCoilVisual->SetupAttachment(PersistentCoilRoot);
    WrappedCoilVisual->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    WrappedCoilVisual->SetCollisionResponseToAllChannels(ECR_Ignore);
    WrappedCoilVisual->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    WrappedCoilVisual->SetCanEverAffectNavigation(false);

    WrappedCoilLabelVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PR004_WrappedCoilLabelVisual"));
    WrappedCoilLabelVisual->SetupAttachment(WrappedCoilVisual);
    WrappedCoilLabelVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WrappedCoilLabelVisual->SetCastShadow(false);

    WrappedCoilLabelHeading = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PR004_WrappedCoilLabelHeading"));
    WrappedCoilLabelHeading->SetupAttachment(WrappedCoilVisual);
    WrappedCoilLabelHeading->SetText(FText::FromString(TEXT("CAIRNWELL AUTOMOTIVE")));
    WrappedCoilLabelHeading->SetTextRenderColor(FColor(31, 75, 68));
    WrappedCoilLabelHeading->SetHorizontalAlignment(EHTA_Center);
    WrappedCoilLabelHeading->SetWorldSize(7.0f);

    WrappedCoilLabelDetail = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PR004_WrappedCoilLabelDetail"));
    WrappedCoilLabelDetail->SetupAttachment(WrappedCoilVisual);
    WrappedCoilLabelDetail->SetText(FText::FromString(TEXT("MOORCROSS WORKS  /  U-SERIES\nMCX-U  1512 mm  18 640 kg")));
    WrappedCoilLabelDetail->SetTextRenderColor(FColor(32, 36, 40));
    WrappedCoilLabelDetail->SetHorizontalAlignment(EHTA_Center);
    WrappedCoilLabelDetail->SetWorldSize(5.0f);

    WrappedCoilTraceLabelVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PR004_WrappedCoilTraceLabelVisual"));
    WrappedCoilTraceLabelVisual->SetupAttachment(WrappedCoilVisual);
    WrappedCoilTraceLabelVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WrappedCoilTraceLabelVisual->SetCastShadow(false);

    WrappedCoilTraceText = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PR004_WrappedCoilTraceText"));
    WrappedCoilTraceText->SetupAttachment(WrappedCoilVisual);
    WrappedCoilTraceText->SetText(FText::FromString(TEXT("HEAT  -\nLOT   -")));
    WrappedCoilTraceText->SetTextRenderColor(FColor(32, 36, 40));
    WrappedCoilTraceText->SetHorizontalAlignment(EHTA_Center);
    WrappedCoilTraceText->SetWorldSize(4.0f);
    WrappedCoilTraceText->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WrappedCoilTraceText->SetCastShadow(false);

    WrappedCoilBarcodeText = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PR004_WrappedCoilBarcodeText"));
    WrappedCoilBarcodeText->SetupAttachment(WrappedCoilVisual);
    WrappedCoilBarcodeText->SetText(FText::FromString(TEXT("|||| ||| ||||  -")));
    WrappedCoilBarcodeText->SetTextRenderColor(FColor(16, 18, 20));
    WrappedCoilBarcodeText->SetHorizontalAlignment(EHTA_Center);
    WrappedCoilBarcodeText->SetWorldSize(3.2f);
    WrappedCoilBarcodeText->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    WrappedCoilBarcodeText->SetCastShadow(false);

    OperatorHMI = CreateDefaultSubobject<UWidgetComponent>(TEXT("PR004_OperatorHMI"));
    OperatorHMI->SetupAttachment(StationRoot);
    OperatorHMI->SetWidgetClass(ULBPR004HMIWidget::StaticClass());
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
    // Keep the WidgetComponent as the authoritative cursor hit target and
    // widget host, but do not render its command-line PIE render target. UE's
    // off-screen widget renderer can expose its checkerboard fallback even
    // when the Slate tree is valid. The live, deterministic TextRender layer
    // is the visible diegetic display on the physical black screen.
    OperatorHMI->SetVisibility(false, false);
    OperatorHMI->SetHiddenInGame(true, false);

    const auto CreateHMIText = [this](const TCHAR* Name, const FText& Text, const FColor Colour, const float WorldSize)
    {
        UTextRenderComponent* Component = CreateDefaultSubobject<UTextRenderComponent>(Name);
        Component->SetupAttachment(StationRoot);
        Component->SetText(Text);
        Component->SetTextRenderColor(Colour);
        Component->SetHorizontalAlignment(EHTA_Center);
        Component->SetVerticalAlignment(EVRTA_TextCenter);
        Component->SetWorldSize(WorldSize);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetCastShadow(false);
        return Component;
    };
    HMIBrandText = CreateHMIText(TEXT("PR004_HMI_BrandText"),
        FText::FromString(TEXT("CAIRNWELL AUTOMOTIVE / MOORCROSS WORKS")), FColor(226, 224, 212), 2.35f);
    HMIStationText = CreateHMIText(TEXT("PR004_HMI_StationText"),
        FText::FromString(TEXT("PR-004  /  COIL PREPARATION")), FColor(110, 128, 130), 2.45f);
    HMIStateText = CreateHMIText(TEXT("PR004_HMI_StateText"),
        FText::FromString(TEXT("NO STATION")), FColor(15, 184, 112), 2.75f);
    HMICoilText = CreateHMIText(TEXT("PR004_HMI_CoilText"),
        FText::FromString(TEXT("COIL  -")), FColor(226, 224, 212), 2.25f);
    HMIRecipeText = CreateHMIText(TEXT("PR004_HMI_RecipeText"),
        FText::FromString(TEXT("RECORD  -")), FColor(226, 224, 212), 2.0f);
    HMIChecklistText = CreateHMIText(TEXT("PR004_HMI_ChecklistText"),
        FText::FromString(TEXT("WAITING FOR STATION BINDING")), FColor(226, 224, 212), 1.9f);
    HMIActionText = CreateHMIText(TEXT("PR004_HMI_ActionText"),
        FText::FromString(TEXT("[  UNPACKAGE COIL  ]")), FColor(227, 166, 0), 3.0f);

    // The native station root is centred on the cradle and rotated with the
    // process line. Author the screen text in station-local space so every
    // instance retains the same 0.6 cm standoff and cannot lose editor-only
    // component transform overrides during reconstruction.
    const auto PlaceHMIText = [](UTextRenderComponent* Component, const float LocalZ)
    {
        Component->SetRelativeLocation(FVector(-510.0f, -233.4f, LocalZ));
        Component->SetRelativeRotation(FRotator(0.0f, 90.0f, 0.0f));
    };
    PlaceHMIText(HMIBrandText, 36.37f);
    PlaceHMIText(HMIStationText, 30.37f);
    PlaceHMIText(HMIStateText, 22.37f);
    PlaceHMIText(HMICoilText, 14.37f);
    PlaceHMIText(HMIRecipeText, 7.37f);
    PlaceHMIText(HMIChecklistText, 0.37f);
    PlaceHMIText(HMIActionText, -8.63f);

    BareCoilVisual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PR004_BareCoilVisual"));
    BareCoilVisual->SetupAttachment(PersistentCoilRoot);
    BareCoilVisual->SetVisibility(false, true);
    BareCoilVisual->SetHiddenInGame(true, true);
    BareCoilVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    BareCoilVisual->SetCanEverAffectNavigation(false);

    RobotRoot = CreateDefaultSubobject<USceneComponent>(TEXT("RobotRoot"));
    RobotRoot->SetupAttachment(StationRoot);

    InspectionRoot = CreateDefaultSubobject<USceneComponent>(TEXT("InspectionRoot"));
    InspectionRoot->SetupAttachment(StationRoot);

    ApprovedRecipeIds.Add(TEXT("PR004_DEPACK_STANDARD"));
}

void ALBPR004Station::BeginPlay()
{
    Super::BeginPlay();
    if (OperatorHMI)
    {
        OperatorHMI->InitWidget();
        if (ULBPR004HMIWidget* Widget = Cast<ULBPR004HMIWidget>(OperatorHMI->GetUserWidgetObject()))
        {
            Widget->BindStation(this);
        }
    }
    UpdateCoilPresentation();
    UpdateHMITextPresentation();
}

void ALBPR004Station::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    HMIRefreshAccumulator += FMath::Max(0.0f, DeltaSeconds);
    if (HMIRefreshAccumulator >= 0.1f)
    {
        HMIRefreshAccumulator = 0.0f;
        UpdateHMITextPresentation();
    }

    if (!bControlPowerOn)
    {
        return;
    }

    const float ScaledDelta = FMath::Max(0.0f, DeltaSeconds) * FMath::Max(0.01f, CycleSpeedMultiplier);
    PhaseElapsedSeconds += ScaledDelta;
    if (ActiveAction.bIsActive)
    {
        ItemElapsedSeconds += ScaledDelta;
    }

    if (ProcessState != ELBPR004State::Fault && IsHazardousMotionState(ProcessState))
    {
        if (!SafetyEnvelopeHealthy())
        {
            StopFilmDrives();
            RaiseFaultInternal(ELBPR004Fault::GateOrSafetyInterlockOpen);
            return;
        }

        if (!StateSpecificMotionInterlocksHealthy())
        {
            StopFilmDrives();
            RaiseFaultInternal(IsPackagingRemovalState(ProcessState)
                ? ELBPR004Fault::RobotNotHealthy
                : ELBPR004Fault::CradleNotLocked);
            return;
        }
    }

    if (bCradleIndexDriveEnabled || bFilmSpindleDriveEnabled)
    {
        ELBPR004Fault FilmFault = ELBPR004Fault::None;
        if (!FilmDewrapStatus.bSpindleHealthy)
        {
            FilmFault = ELBPR004Fault::FilmSpindleNotHealthy;
        }
        else if (!FilmDewrapStatus.bDancerAndTensionHealthy)
        {
            FilmFault = ELBPR004Fault::FilmTensionHighOrLost;
        }
        else if (!FilmDewrapStatus.bCradleSpindleSynchronized)
        {
            FilmFault = ELBPR004Fault::CradleSpindleSyncFault;
        }
        else if (!FilmDewrapStatus.bRobotClearForIndex)
        {
            FilmFault = ELBPR004Fault::RobotNotClearForFilmIndex;
        }

        if (FilmFault != ELBPR004Fault::None)
        {
            StopFilmDrives();
            RaiseFaultInternal(FilmFault);
            return;
        }
    }

    if (ProcessState == ELBPR004State::Fault || bManualWrapRecoveryRequired)
    {
        return;
    }

    AdvanceAutomaticSequence(ScaledDelta);
}

void ALBPR004Station::UpdateHMITextPresentation()
{
    if (!HMIStateText || !HMICoilText || !HMIRecipeText || !HMIChecklistText || !HMIActionText)
    {
        return;
    }

    const UEnum* StateEnum = StaticEnum<ELBPR004State>();
    const FString StateName = StateEnum
        ? FName::NameToDisplayString(StateEnum->GetNameStringByValue(static_cast<int64>(ProcessState)), false).ToUpper()
        : TEXT("UNKNOWN");
    TArray<FText> BlockingReasons;
    const bool bCanUnpackage = CanUnpackageCoil(BlockingReasons);
    HMIStateText->SetText(FText::FromString(IsCoilUnpackaged()
        ? TEXT("COIL UNPACKAGED")
        : bCanUnpackage ? TEXT("READY TO UNPACKAGE") : StateName));
    HMIStateText->SetTextRenderColor(ActiveFault == ELBPR004Fault::None
        ? FColor(15, 184, 112) : FColor(199, 20, 10));
    HMICoilText->SetText(FText::FromString(FString::Printf(TEXT("COIL  %s"),
        CoilId.IsEmpty() ? TEXT("NO COIL LOADED") : *CoilId)));
    HMIRecipeText->SetText(FText::FromString(FString::Printf(TEXT("RECORD  %s"),
        ActiveRecipeId.IsNone() ? TEXT("-") : *ActiveRecipeId.ToString())));

    FString Checklist = TEXT("CRADLE LOCKED  /  HOOK CLEAR\nCOIL ID + RECIPE VERIFIED");
    if (!BlockingReasons.IsEmpty())
    {
        Checklist = BlockingReasons[0].ToString();
        if (BlockingReasons.Num() > 1)
        {
            Checklist += TEXT("\n") + BlockingReasons[1].ToString();
        }
    }
    HMIChecklistText->SetText(FText::FromString(Checklist));
    HMIActionText->SetText(FText::FromString(IsCoilUnpackaged()
        ? TEXT("[  COIL UNPACKAGED  ]")
        : bCanUnpackage ? TEXT("[  UNPACKAGE COIL  ]") : TEXT("[  ACTION BLOCKED  ]")));
}

bool ALBPR004Station::SetControlPower(bool bEnabled)
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    if (bControlPowerOn == bEnabled)
    {
        return true;
    }

    if (!bEnabled)
    {
        const bool bInterruptedWork = ProcessState == ELBPR004State::Scanning
            || ProcessState == ELBPR004State::Securing
            || IsHazardousMotionState(ProcessState)
            || ActiveAction.bIsActive;

        if (bInterruptedWork)
        {
            StateBeforePowerLoss = ProcessState;
            bPowerLossReconciliationRequired = true;
        }

        bControlPowerOn = false;
        StopFilmDrives();

        if (bInterruptedWork && ProcessState != ELBPR004State::Fault)
        {
            RaiseFaultInternal(ActiveAction.bIsActive
                ? ELBPR004Fault::InFlightMaterialOwnershipUnclear
                : ELBPR004Fault::PowerLossReconciliationRequired);
        }
        else if (!bInterruptedWork && ProcessState != ELBPR004State::Unsurveyed)
        {
            SetProcessStateInternal(ELBPR004State::Isolated, false);
        }
        return true;
    }

    bControlPowerOn = true;
    if (ProcessState == ELBPR004State::Unsurveyed || ProcessState == ELBPR004State::Isolated)
    {
        SetProcessStateInternal(bCellCommissioned ? ELBPR004State::AwaitingCoil : ELBPR004State::Isolated, false);
    }
    return true;
}

bool ALBPR004Station::SetCellCommissioned(bool bCommissioned)
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    if (bCommissioned && !bControlPowerOn)
    {
        return false;
    }

    if (!bCommissioned && (bCoilPresent || IsHazardousMotionState(ProcessState)))
    {
        return false;
    }

    bCellCommissioned = bCommissioned;
    if (!bCommissioned)
    {
        StopFilmDrives();
        SetProcessStateInternal(bControlPowerOn ? ELBPR004State::SafeForAccess : ELBPR004State::Isolated, false);
    }
    else if (!bCoilPresent && ActiveFault == ELBPR004Fault::None)
    {
        SetProcessStateInternal(ELBPR004State::AwaitingCoil, false);
    }
    return true;
}

bool ALBPR004Station::SetSafetyInputs(bool bGatesAreClosed, bool bSafetyCircuitIsHealthy, bool bPersonnelAreClear)
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    bGatesClosed = bGatesAreClosed;
    bSafetyCircuitHealthy = bSafetyCircuitIsHealthy;
    bPersonnelClear = bPersonnelAreClear;

    if (IsHazardousMotionState(ProcessState) && !SafetyEnvelopeHealthy())
    {
        StopFilmDrives();
        RaiseFaultInternal(ELBPR004Fault::GateOrSafetyInterlockOpen);
    }
    else if (ProcessState == ELBPR004State::AwaitingRobotClearance)
    {
        TryResumeAfterCraneClearance();
    }
    return true;
}

bool ALBPR004Station::SetRobotHealthy(bool bHealthy)
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    bRobotHealthy = bHealthy;
    if (!bRobotHealthy && IsHazardousMotionState(ProcessState))
    {
        StopFilmDrives();
        RaiseFaultInternal(ELBPR004Fault::RobotNotHealthy);
    }
    else if (ProcessState == ELBPR004State::AwaitingRobotClearance)
    {
        TryResumeAfterCraneClearance();
    }
    return true;
}

bool ALBPR004Station::SetInspectionSystemsHealthy(bool bPackagingScannerIsHealthy, bool bInspectionSystemIsHealthy)
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    bPackagingScannerHealthy = bPackagingScannerIsHealthy;
    bInspectionSystemHealthy = bInspectionSystemIsHealthy;
    if (ProcessState == ELBPR004State::Scanning && !bPackagingScannerHealthy)
    {
        RaiseFaultInternal(ELBPR004Fault::PackagingScanFault);
    }
    else if (ProcessState == ELBPR004State::Inspecting && !bInspectionSystemHealthy)
    {
        RaiseFaultInternal(ELBPR004Fault::InspectionVisionFault);
    }
    return true;
}

bool ALBPR004Station::SetWasteStreamStatus(ELBPR004WasteStream Stream, const FLBPR004WasteStreamStatus& NewStatus)
{
    if (!CanBeginExternalMutation() || Stream == ELBPR004WasteStream::None)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    FLBPR004WasteStreamStatus* Target = nullptr;
    switch (Stream)
    {
    case ELBPR004WasteStream::SteelBand: Target = &BandStreamStatus; break;
    case ELBPR004WasteStream::EdgeProtector: Target = &ProtectorStreamStatus; break;
    case ELBPR004WasteStream::PlasticWrap: Target = &PlasticStreamStatus; break;
    default: break;
    }
    if (Target == nullptr)
    {
        return false;
    }
    *Target = NewStatus;

    if (ActiveAction.bIsActive && ActiveAction.WasteStream == Stream)
    {
        ELBPR004Fault StreamFault = ELBPR004Fault::None;
        const bool bRequireEject = ActiveAction.TerminalSubstage == ELBPR004ActionSubstage::WasteEjected;
        if (!IsWasteStreamReady(Stream, bRequireEject, StreamFault))
        {
            StopFilmDrives();
            RaiseFaultInternal(StreamFault);
        }
    }
    return true;
}

bool ALBPR004Station::SetFilmDewrapStatus(const FLBPR004FilmDewrapStatus& NewStatus)
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    FilmDewrapStatus = NewStatus;

    if (ProcessState == ELBPR004State::RemovingWrap && ActiveAction.bIsActive)
    {
        ELBPR004Fault FilmFault = ELBPR004Fault::None;
        if (!FilmDewrapStatus.bSpindleHealthy)
        {
            FilmFault = ELBPR004Fault::FilmSpindleNotHealthy;
        }
        else if ((bCradleIndexDriveEnabled || bFilmSpindleDriveEnabled) && !FilmDewrapStatus.bDancerAndTensionHealthy)
        {
            FilmFault = ELBPR004Fault::FilmTensionHighOrLost;
        }
        else if ((bCradleIndexDriveEnabled || bFilmSpindleDriveEnabled) && !FilmDewrapStatus.bCradleSpindleSynchronized)
        {
            FilmFault = ELBPR004Fault::CradleSpindleSyncFault;
        }
        else if ((bCradleIndexDriveEnabled || bFilmSpindleDriveEnabled) && !FilmDewrapStatus.bRobotClearForIndex)
        {
            FilmFault = ELBPR004Fault::RobotNotClearForFilmIndex;
        }

        if (FilmFault != ELBPR004Fault::None)
        {
            StopFilmDrives();
            RaiseFaultInternal(FilmFault);
        }
    }
    return true;
}

bool ALBPR004Station::RegisterUnrecoveredWrapFragment(FName FragmentId, bool bTrappedBeneathCoil)
{
    if (!CanBeginExternalMutation() || !IsNameSet(FragmentId)
        || ProcessState != ELBPR004State::RemovingWrap || !ActiveAction.bIsActive)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    StopFilmDrives();
    UnrecoveredWrapFragmentIds.AddUnique(FragmentId);
    RecoveredWrapFragmentIds.Remove(FragmentId);
    bManualWrapRecoveryRequired = true;
    bManualWrapRecoveryInProgress = false;
    bRecoveryZeroMotionVerified = false;
    TrappedKeyState = ELBPR004TrappedKeyState::Installed;
    RaiseFaultInternal(bTrappedBeneathCoil
        ? ELBPR004Fault::WrapTrappedBeneathCoil
        : ELBPR004Fault::WrapTornOrFragmented);

    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnManualRecoveryChanged.Broadcast(true, TrappedKeyState);
    return true;
}

bool ALBPR004Station::BeginTrappedKeyManualRecovery(FName PermitId)
{
    if (!CanBeginExternalMutation() || !bManualWrapRecoveryRequired || !IsNameSet(PermitId)
        || ProcessState != ELBPR004State::Fault || bManualWrapRecoveryInProgress)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    StopFilmDrives();
    ManualRecoveryPermitId = PermitId;
    bManualWrapRecoveryInProgress = true;
    bRecoveryZeroMotionVerified = false;
    TrappedKeyState = ELBPR004TrappedKeyState::Installed;
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnManualRecoveryChanged.Broadcast(true, TrappedKeyState);
    return true;
}

bool ALBPR004Station::ConfirmTrappedKeyIsolation(bool bZeroMotionVerified, bool bKeyRemovedAndRetained, FName EvidenceId)
{
    if (!CanBeginExternalMutation() || !bManualWrapRecoveryInProgress || !bZeroMotionVerified
        || !bKeyRemovedAndRetained || !IsNameSet(EvidenceId)
        || bCradleIndexDriveEnabled || bFilmSpindleDriveEnabled)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    bRecoveryZeroMotionVerified = true;
    TrappedKeyState = ELBPR004TrappedKeyState::RemovedAndRetained;
    LastManualRecoveryEvidenceId = EvidenceId;
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnManualRecoveryChanged.Broadcast(true, TrappedKeyState);
    return true;
}

bool ALBPR004Station::RecordRecoveredWrapFragment(FName FragmentId, FName EvidenceId)
{
    if (!CanBeginExternalMutation() || !bManualWrapRecoveryInProgress || !bRecoveryZeroMotionVerified
        || TrappedKeyState != ELBPR004TrappedKeyState::RemovedAndRetained
        || !IsNameSet(FragmentId) || !IsNameSet(EvidenceId)
        || !UnrecoveredWrapFragmentIds.Contains(FragmentId))
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    UnrecoveredWrapFragmentIds.Remove(FragmentId);
    RecoveredWrapFragmentIds.AddUnique(FragmentId);
    LastManualRecoveryEvidenceId = EvidenceId;
    return true;
}

bool ALBPR004Station::CompleteTrappedKeyManualRecovery(FName EvidenceId)
{
    if (!CanBeginExternalMutation() || !bManualWrapRecoveryInProgress || !bRecoveryZeroMotionVerified
        || TrappedKeyState != ELBPR004TrappedKeyState::RemovedAndRetained
        || !UnrecoveredWrapFragmentIds.IsEmpty() || !IsNameSet(EvidenceId)
        || !SafetyEnvelopeHealthy())
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    TrappedKeyState = ELBPR004TrappedKeyState::Restored;
    LastManualRecoveryEvidenceId = EvidenceId;
    bManualWrapRecoveryRequired = false;
    bManualWrapRecoveryInProgress = false;
    bRecoveryZeroMotionVerified = false;
    ManualRecoveryPermitId = NAME_None;
    ActiveFault = ELBPR004Fault::None;
    SetProcessStateInternal(ELBPR004State::RemovingWrap, false);

    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnManualRecoveryChanged.Broadcast(false, TrappedKeyState);
    }
    BroadcastActiveActionRequest();
    return true;
}

bool ALBPR004Station::LoadPackagedCoil(const FString& NewCoilId)
{
    const uint32 IdentityHash = FCrc::StrCrc32(*NewCoilId);
    return LoadPackagedCoilWithTraceability(
        NewCoilId,
        FString::Printf(TEXT("HT-%08X"), IdentityHash),
        FString::Printf(TEXT("LOT-CW-%06u"), IdentityHash % 1000000u),
        FString::Printf(TEXT("503184%09u"), IdentityHash % 1000000000u));
}

bool ALBPR004Station::LoadPackagedCoilWithTraceability(const FString& NewCoilId,
    const FString& NewHeatId, const FString& NewSupplierLotId,
    const FString& NewTraceabilityBarcode)
{
    if (!CanBeginExternalMutation() || NewCoilId.IsEmpty() || !bControlPowerOn || !bCellCommissioned
        || NewHeatId.IsEmpty() || NewSupplierLotId.IsEmpty() || NewTraceabilityBarcode.IsEmpty()
        || ProcessState != ELBPR004State::AwaitingCoil || bCoilPresent || ActiveFault != ELBPR004Fault::None)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    CoilId = NewCoilId;
    HeatId = NewHeatId;
    SupplierLotId = NewSupplierLotId;
    TraceabilityBarcode = NewTraceabilityBarcode;
    ExpectedCoilId.Empty();
    ActiveRecipeId = NAME_None;
    bCoilPresent = true;
    bIdentityVerified = false;
    bPackagingScanAccepted = false;
    bInspectionReportAccepted = false;
    bCoilTailSecured = false;
    CoilTailEvidenceId = NAME_None;
    Disposition = ELBPR004Disposition::Unknown;
    RemainingBandMask = FullBandMask;
    RemainingProtectorMask = FullProtectorMask;
    RemainingWrapMask = FullWrapMask;
    AcceptedWrapMask = 0;
    CompactedBandCoilCount = 0;
    CompactedPlasticBaleCount = 0;
    UnrecoveredWrapFragmentIds.Reset();
    RecoveredWrapFragmentIds.Reset();
    WasteLedger.Reset();
    PackagingScanReport = FLBPR004PackagingScanReport();
    InspectionReport = FLBPR004InspectionReport();
    ActiveCycleSerial = NextCycleSerial++;
    ActiveScanRequestToken = 0;
    ActiveInspectionRequestToken = 0;
    ActiveHandoffTransactionId = NAME_None;
    ActiveRejectRemovalTransactionId = NAME_None;
    ClearActiveAction();
    SetProcessStateInternal(ELBPR004State::CoilLoaded, false);
    UpdateCoilPresentation();
    return true;
}

bool ALBPR004Station::SelectDepackRecipe(FName NewRecipeId, const FString& NewExpectedCoilId)
{
    if (!CanBeginExternalMutation() || !bCoilPresent || !IsNameSet(NewRecipeId)
        || NewExpectedCoilId.IsEmpty() || !IsApprovedRecipe(NewRecipeId)
        || (ProcessState != ELBPR004State::CoilLoaded && ProcessState != ELBPR004State::AwaitingAuthorisation))
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    ActiveRecipeId = NewRecipeId;
    ExpectedCoilId = NewExpectedCoilId;
    bIdentityVerified = false;
    SetProcessStateInternal(ELBPR004State::AwaitingAuthorisation, false);
    return true;
}

bool ALBPR004Station::SetCradleLocked(bool bLocked)
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    bCradleLocked = bLocked;
    if (!bCradleLocked && IsHazardousMotionState(ProcessState) && ProcessState != ELBPR004State::Securing)
    {
        StopFilmDrives();
        RaiseFaultInternal(ELBPR004Fault::CradleNotLocked);
    }
    else if (ProcessState == ELBPR004State::AwaitingRobotClearance)
    {
        TryResumeAfterCraneClearance();
    }
    return true;
}

bool ALBPR004Station::SetCHookWithdrawn(bool bWithdrawn)
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    bCHookWithdrawn = bWithdrawn;
    if (!bCHookWithdrawn && IsHazardousMotionState(ProcessState) && ProcessState != ELBPR004State::Securing)
    {
        StopFilmDrives();
        RaiseFaultInternal(ELBPR004Fault::CHookNotWithdrawn);
    }
    else if (ProcessState == ELBPR004State::AwaitingRobotClearance)
    {
        TryResumeAfterCraneClearance();
    }
    return true;
}

bool ALBPR004Station::AuthoriseAutomaticCycle()
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    TArray<FText> BlockingReasons;
    if (!CanAuthoriseCycle(BlockingReasons))
    {
        if (bCoilPresent && !ExpectedCoilId.IsEmpty() && CoilId != ExpectedCoilId)
        {
            FScopedBoolFlag MutationGuard(bMutationInProgress);
            RaiseFaultInternal(ELBPR004Fault::WrongCoilIdentity);
        }
        return false;
    }

    FScopedBoolFlag MutationGuard(bMutationInProgress);
    ActiveScanRequestToken = NextReportRequestToken++;
    SetProcessStateInternal(ELBPR004State::Scanning, false);
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnPackagingScanRequested.Broadcast(ActiveScanRequestToken, CoilId, ActiveRecipeId);
    return true;
}

bool ALBPR004Station::UnpackageCoil(FName EvidenceId)
{
    TArray<FText> BlockingReasons;
    if (!CanBeginExternalMutation() || !IsNameSet(EvidenceId) || !CanUnpackageCoil(BlockingReasons))
    {
        return false;
    }

    FScopedBoolFlag MutationGuard(bMutationInProgress);
    if (CoilId != ExpectedCoilId)
    {
        RaiseFaultInternal(ELBPR004Fault::WrongCoilIdentity);
        return false;
    }

    // The deliberately simple player action is still authoritative: record
    // identity, removed packaging and automated inspection evidence atomically so
    // save/load and downstream PR-005 handoff cannot see a cosmetic-only swap.
    PackagingScanReport = FLBPR004PackagingScanReport();
    PackagingScanReport.ReportId = FName(*FString::Printf(TEXT("PR004_UNPACKAGE_%s"), *EvidenceId.ToString()));
    PackagingScanReport.CoilId = CoilId;
    PackagingScanReport.RecipeId = ActiveRecipeId;
    PackagingScanReport.DetectedBandMask = FullBandMask;
    PackagingScanReport.DetectedProtectorMask = FullProtectorMask;
    PackagingScanReport.DetectedWrapMask = FullWrapMask;
    PackagingScanReport.bScannerHealthy = true;
    PackagingScanReport.bIdentityReadable = true;
    PackagingScanReport.bDimensionsWithinRecipe = true;
    PackagingScanReport.bPackagingClassificationComplete = true;

    bIdentityVerified = true;
    bPackagingScanAccepted = true;
    ActiveScanRequestToken = 0;
    ActiveInspectionRequestToken = 0;
    RemainingBandMask = 0;
    RemainingProtectorMask = 0;
    RemainingWrapMask = 0;
    AcceptedWrapMask = FullWrapMask;
    ClearActiveAction();

    WasteLedger.Reset();
    CompactedBandCoilCount = 4;
    CompactedPlasticBaleCount = 1;
    for (int32 Index = 1; Index <= 4; ++Index)
    {
        FLBPR004WasteRecord Record;
        Record.RecordId = FName(*FString::Printf(TEXT("PR004_%lld_SIMPLE_BAND_%02d"), ActiveCycleSerial, Index));
        Record.CycleSerial = ActiveCycleSerial;
        Record.ActionToken = NextActionToken++;
        Record.CoilId = CoilId;
        Record.WasteStream = ELBPR004WasteStream::SteelBand;
        Record.WasteType = CompactedBandCoilType;
        Record.SourceComponentType = BandComponentType;
        Record.SourceComponentIndex = Index;
        Record.AcceptedSourceMask = 1 << (Index - 1);
        Record.EvidenceId = EvidenceId;
        WasteLedger.Add(Record);
    }
    {
        FLBPR004WasteRecord Record;
        Record.RecordId = FName(*FString::Printf(TEXT("PR004_%lld_SIMPLE_WRAP"), ActiveCycleSerial));
        Record.CycleSerial = ActiveCycleSerial;
        Record.ActionToken = NextActionToken++;
        Record.CoilId = CoilId;
        Record.WasteStream = ELBPR004WasteStream::PlasticWrap;
        Record.WasteType = CompactedPlasticBaleType;
        Record.SourceComponentType = WrapComponentType;
        Record.SourceComponentIndex = 1;
        Record.AcceptedSourceMask = FullWrapMask;
        Record.EvidenceId = EvidenceId;
        WasteLedger.Add(Record);
    }

    bCoilTailSecured = true;
    CoilTailEvidenceId = EvidenceId;
    InspectionReport = FLBPR004InspectionReport();
    InspectionReport.ReportId = FName(*FString::Printf(TEXT("PR004_AUTOMATED_CHECK_%s"), *EvidenceId.ToString()));
    InspectionReport.CoilId = CoilId;
    InspectionReport.bVisionHealthy = true;
    InspectionReport.bFaceInspectionPassed = true;
    InspectionReport.bBoreInspectionPassed = true;
    InspectionReport.bEdgeInspectionPassed = true;
    InspectionReport.bCoilTailSecuredObserved = true;
    bInspectionReportAccepted = true;
    Disposition = ELBPR004Disposition::Ready;
    SetProcessStateInternal(ELBPR004State::ReadyForHandoff, false);
    UpdateCoilPresentation();

    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnDispositionChanged.Broadcast(CoilId, Disposition);
    return true;
}

bool ALBPR004Station::CanUnpackageCoil(TArray<FText>& OutBlockingReasons) const
{
    OutBlockingReasons.Reset();
    if (ProcessState != ELBPR004State::AwaitingAuthorisation) OutBlockingReasons.Add(LOCTEXT("UnpackageState", "Station is not awaiting player authorisation."));
    if (!bControlPowerOn) OutBlockingReasons.Add(LOCTEXT("UnpackagePower", "Control power is off."));
    if (!bCellCommissioned) OutBlockingReasons.Add(LOCTEXT("UnpackageCommissioned", "PR-004 has not been commissioned."));
    if (!bCoilPresent || CoilId.IsEmpty()) OutBlockingReasons.Add(LOCTEXT("UnpackageCoil", "No packaged coil is loaded."));
    if (ExpectedCoilId.IsEmpty() || !IsNameSet(ActiveRecipeId)) OutBlockingReasons.Add(LOCTEXT("UnpackageRecipe", "Select the coil and approved preparation recipe."));
    if (bCoilPresent && !ExpectedCoilId.IsEmpty() && CoilId != ExpectedCoilId) OutBlockingReasons.Add(LOCTEXT("UnpackageIdentity", "The selected coil does not match the preparation record."));
    if (!bCradleLocked) OutBlockingReasons.Add(LOCTEXT("UnpackageCradle", "Lock the preparation stand."));
    if (!bCHookWithdrawn) OutBlockingReasons.Add(LOCTEXT("UnpackageHook", "Withdraw the crane C-hook."));
    if (ActiveFault != ELBPR004Fault::None) OutBlockingReasons.Add(LOCTEXT("UnpackageFault", "Clear the active PR-004 fault."));
    return OutBlockingReasons.IsEmpty();
}

bool ALBPR004Station::SubmitPackagingScanReport(int64 RequestToken, const FLBPR004PackagingScanReport& Report)
{
    if (!CanBeginExternalMutation() || ProcessState != ELBPR004State::Scanning
        || RequestToken <= 0 || RequestToken != ActiveScanRequestToken)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    const bool bValid = IsNameSet(Report.ReportId)
        && Report.CoilId == CoilId
        && Report.RecipeId == ActiveRecipeId
        && Report.bScannerHealthy
        && Report.bIdentityReadable
        && Report.bDimensionsWithinRecipe
        && Report.bPackagingClassificationComplete
        && Report.DetectedBandMask == FullBandMask
        && Report.DetectedProtectorMask == FullProtectorMask
        && Report.DetectedWrapMask == FullWrapMask;

    if (!bValid)
    {
        RaiseFaultInternal(Report.CoilId != CoilId ? ELBPR004Fault::WrongCoilIdentity : ELBPR004Fault::PackagingScanFault);
        return false;
    }

    PackagingScanReport = Report;
    RemainingBandMask = Report.DetectedBandMask;
    RemainingProtectorMask = Report.DetectedProtectorMask;
    RemainingWrapMask = Report.DetectedWrapMask;
    bIdentityVerified = CoilId == ExpectedCoilId;
    bPackagingScanAccepted = bIdentityVerified;
    ActiveScanRequestToken = 0;
    if (!bIdentityVerified)
    {
        RaiseFaultInternal(ELBPR004Fault::WrongCoilIdentity);
        return false;
    }

    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnPackagingScanAccepted.Broadcast(RequestToken, Report.ReportId);
    }
    SetProcessStateInternal(ELBPR004State::Securing, false);
    return true;
}

bool ALBPR004Station::ConfirmCoilSecured(FName EvidenceId)
{
    if (!CanBeginExternalMutation() || ProcessState != ELBPR004State::Securing
        || !IsNameSet(EvidenceId) || !bCradleLocked)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    SetProcessStateInternal(ELBPR004State::AwaitingRobotClearance, false);
    TryResumeAfterCraneClearance();
    return true;
}

bool ALBPR004Station::AcknowledgePackagingSubstage(int64 ActionToken, ELBPR004ActionSubstage Substage, FName EvidenceId)
{
    if (!CanBeginExternalMutation() || !ActiveAction.bIsActive || ActionToken != ActiveAction.ActionToken
        || !IsNameSet(EvidenceId) || Substage == ELBPR004ActionSubstage::None)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    const ELBPR004ActionSubstage Expected = ExpectedNextSubstage();
    if (Substage != Expected)
    {
        StopFilmDrives();
        RaiseFaultInternal(TimeoutFaultForActiveAction());
        return false;
    }

    ELBPR004Fault BlockingFault = ELBPR004Fault::None;
    if (!SafetyEnvelopeHealthy() || !bRobotHealthy || !bCradleLocked || !bCHookWithdrawn)
    {
        BlockingFault = !SafetyEnvelopeHealthy()
            ? ELBPR004Fault::GateOrSafetyInterlockOpen
            : (!bRobotHealthy ? ELBPR004Fault::RobotNotHealthy
                : (!bCradleLocked ? ELBPR004Fault::CradleNotLocked : ELBPR004Fault::CHookNotWithdrawn));
    }
    else if (Substage == ELBPR004ActionSubstage::SpindleGripConfirmed && !FilmDewrapStatus.bSpindleGripConfirmed)
    {
        BlockingFault = ELBPR004Fault::FilmSpindleGripFailed;
    }
    else if (Substage == ELBPR004ActionSubstage::RobotClearForIndex && !FilmDewrapStatus.bRobotClearForIndex)
    {
        BlockingFault = ELBPR004Fault::RobotNotClearForFilmIndex;
    }
    else if (Substage == ELBPR004ActionSubstage::CradleSpindleSynchronized
        && (!FilmDewrapStatus.bCradleSpindleSynchronized
            || !FilmDewrapStatus.bSpindleHealthy
            || !FilmDewrapStatus.bDancerAndTensionHealthy
            || !FilmDewrapStatus.bRobotClearForIndex))
    {
        BlockingFault = !FilmDewrapStatus.bSpindleHealthy
            ? ELBPR004Fault::FilmSpindleNotHealthy
            : (!FilmDewrapStatus.bDancerAndTensionHealthy
                ? ELBPR004Fault::FilmTensionHighOrLost
                : (!FilmDewrapStatus.bRobotClearForIndex
                    ? ELBPR004Fault::RobotNotClearForFilmIndex
                    : ELBPR004Fault::CradleSpindleSyncFault));
    }
    else if (Substage == ELBPR004ActionSubstage::TensionControlledWindComplete
        && !FilmDewrapStatus.bDancerAndTensionHealthy)
    {
        BlockingFault = ELBPR004Fault::FilmTensionHighOrLost;
    }
    else if (Substage == ELBPR004ActionSubstage::WasteTransferAccepted
        && ActiveAction.ComponentType == WrapComponentType
        && (!FilmDewrapStatus.bTransferChuteClear || !FilmDewrapStatus.bStripperReady || !FilmDewrapStatus.bFragmentCameraClear))
    {
        BlockingFault = ELBPR004Fault::FilmStripOffFailed;
    }
    else if (Substage == ELBPR004ActionSubstage::WasteTransferAccepted
        || Substage == ELBPR004ActionSubstage::WasteProcessed
        || Substage == ELBPR004ActionSubstage::WasteEjected)
    {
        IsWasteStreamReady(ActiveAction.WasteStream, Substage == ELBPR004ActionSubstage::WasteEjected, BlockingFault);
    }

    if (BlockingFault != ELBPR004Fault::None)
    {
        StopFilmDrives();
        RaiseFaultInternal(BlockingFault);
        return false;
    }

    ActiveAction.LastAcknowledgedSubstage = Substage;
    ActiveAction.MaterialOwner = OwnerForSubstage(Substage);
    ActiveAction.LastEvidenceId = EvidenceId;
    ItemElapsedSeconds = 0.0f;

    if (Substage == ELBPR004ActionSubstage::CradleSpindleSynchronized)
    {
        StartFilmDrives();
    }
    else if (Substage == ELBPR004ActionSubstage::TensionControlledWindComplete)
    {
        StopFilmDrives();
    }

    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnPackagingActionAdvanced.Broadcast(ActionToken, Substage, ActiveAction.MaterialOwner);
    }

    return Substage == ActiveAction.TerminalSubstage ? FinalizeActiveAction(EvidenceId) : true;
}

bool ALBPR004Station::SetCoilTailSecured(bool bSecured, FName EvidenceId)
{
    if (!CanBeginExternalMutation() || !bCoilPresent || (bSecured && !IsNameSet(EvidenceId)))
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    bCoilTailSecured = bSecured;
    CoilTailEvidenceId = bSecured ? EvidenceId : NAME_None;
    return true;
}

bool ALBPR004Station::SubmitInspectionReport(int64 RequestToken, const FLBPR004InspectionReport& Report)
{
    if (!CanBeginExternalMutation() || ProcessState != ELBPR004State::Inspecting
        || RequestToken <= 0 || RequestToken != ActiveInspectionRequestToken)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    if (!IsNameSet(Report.ReportId) || Report.CoilId != CoilId || !Report.bVisionHealthy
        || !bInspectionSystemHealthy || Report.bCoilTailSecuredObserved != bCoilTailSecured)
    {
        RaiseFaultInternal(ELBPR004Fault::InspectionVisionFault);
        return false;
    }

    InspectionReport = Report;
    bInspectionReportAccepted = true;
    ActiveInspectionRequestToken = 0;
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnInspectionAccepted.Broadcast(RequestToken, Report.ReportId);
    }
    SetProcessStateInternal(ELBPR004State::AwaitingDisposition, false);
    return true;
}

bool ALBPR004Station::RequestReinspection(FName ReasonId)
{
    if (!CanBeginExternalMutation() || !IsNameSet(ReasonId)
        || (ProcessState != ELBPR004State::AwaitingDisposition
            && ProcessState != ELBPR004State::QualityHold
            && ProcessState != ELBPR004State::Rejected))
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    Disposition = ELBPR004Disposition::Unknown;
    bInspectionReportAccepted = false;
    InspectionReport = FLBPR004InspectionReport();
    CreateInspectionRequest(true);
    return true;
}

bool ALBPR004Station::SetQualityDisposition(ELBPR004Disposition NewDisposition)
{
    if (!CanBeginExternalMutation() || !bInspectionReportAccepted
        || (ProcessState != ELBPR004State::AwaitingDisposition
            && ProcessState != ELBPR004State::QualityHold
            && ProcessState != ELBPR004State::Rejected)
        || NewDisposition == ELBPR004Disposition::Unknown)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);

    if (NewDisposition == ELBPR004Disposition::Ready)
    {
        TArray<FText> BlockingReasons;
        if (!ValidateReleaseInvariants(BlockingReasons, false)
            || !InspectionReport.bFaceInspectionPassed
            || !InspectionReport.bBoreInspectionPassed
            || !InspectionReport.bEdgeInspectionPassed
            || InspectionReport.bSurfaceCorrosionDetected
            || InspectionReport.bSurfaceDamageDetected)
        {
            return false;
        }
    }

    Disposition = NewDisposition;
    switch (Disposition)
    {
    case ELBPR004Disposition::Ready: SetProcessStateInternal(ELBPR004State::ReadyForHandoff, false); break;
    case ELBPR004Disposition::QualityHold: SetProcessStateInternal(ELBPR004State::QualityHold, false); break;
    case ELBPR004Disposition::Reject: SetProcessStateInternal(ELBPR004State::Rejected, false); break;
    default: return false;
    }
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnDispositionChanged.Broadcast(CoilId, Disposition);
    return true;
}

bool ALBPR004Station::RequestHandoff(FName TransactionId)
{
    if (!CanBeginExternalMutation() || !IsNameSet(TransactionId) || IsNameSet(ActiveHandoffTransactionId)
        || TransactionId == LastCompletedHandoffTransactionId)
    {
        return false;
    }
    TArray<FText> BlockingReasons;
    if (!CanReleaseCoil(BlockingReasons))
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    ActiveHandoffTransactionId = TransactionId;
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnHandoffCommandRequested.Broadcast(CoilId, TransactionId);
    return true;
}

bool ALBPR004Station::ConfirmHandoffComplete(FName TransactionId)
{
    if (!CanBeginExternalMutation() || !IsNameSet(TransactionId)
        || TransactionId != ActiveHandoffTransactionId || ProcessState != ELBPR004State::ReadyForHandoff)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    const FString CompletedCoil = CoilId;
    LastCompletedHandoffTransactionId = TransactionId;
    LastCompletedCoilId = CoilId;
    LastCompletedCycleSerial = ActiveCycleSerial;
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnHandoffCompleted.Broadcast(CompletedCoil, TransactionId);
    }
    ResetActiveCycleAfterTransfer();
    return true;
}

bool ALBPR004Station::RequestRejectedCoilRemoval(FName TransactionId)
{
    if (!CanBeginExternalMutation() || ProcessState != ELBPR004State::Rejected
        || Disposition != ELBPR004Disposition::Reject || !IsNameSet(TransactionId)
        || IsNameSet(ActiveRejectRemovalTransactionId)
        || TransactionId == LastCompletedRejectRemovalTransactionId)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    ActiveRejectRemovalTransactionId = TransactionId;
    SetProcessStateInternal(ELBPR004State::AwaitingRejectRemoval, false);
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnRejectedCoilRemovalRequested.Broadcast(CoilId, TransactionId);
    return true;
}

bool ALBPR004Station::ConfirmRejectedCoilArchived(FName TransactionId, FName ArchiveRecordId)
{
    if (!CanBeginExternalMutation() || ProcessState != ELBPR004State::AwaitingRejectRemoval
        || TransactionId != ActiveRejectRemovalTransactionId || !IsNameSet(ArchiveRecordId))
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    const FString RejectedCoil = CoilId;
    LastCompletedRejectRemovalTransactionId = TransactionId;
    LastRejectArchiveRecordId = ArchiveRecordId;
    LastCompletedCoilId = CoilId;
    LastCompletedCycleSerial = ActiveCycleSerial;
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnRejectedCoilArchived.Broadcast(RejectedCoil, TransactionId, ArchiveRecordId);
    }
    ResetActiveCycleAfterTransfer();
    return true;
}

bool ALBPR004Station::RaiseFault(ELBPR004Fault Fault)
{
    if (!CanBeginExternalMutation() || Fault == ELBPR004Fault::None)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    RaiseFaultInternal(Fault);
    return true;
}

bool ALBPR004Station::ResetFault(FName RecoveryEvidenceId)
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    TArray<FText> BlockingReasons;
    if (!FaultRecoverySatisfied(RecoveryEvidenceId, BlockingReasons))
    {
        return false;
    }

    FScopedBoolFlag MutationGuard(bMutationInProgress);
    ActiveFault = ELBPR004Fault::None;
    const ELBPR004State ResumeState = StateBeforeFault == ELBPR004State::Fault
        ? ELBPR004State::AwaitingAuthorisation
        : StateBeforeFault;
    SetProcessStateInternal(ResumeState, false);
    if (ActiveAction.bIsActive && IsPackagingRemovalState(ResumeState))
    {
        BroadcastActiveActionRequest();
    }
    else if (ResumeState == ELBPR004State::Scanning && ActiveScanRequestToken > 0)
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnPackagingScanRequested.Broadcast(ActiveScanRequestToken, CoilId, ActiveRecipeId);
    }
    else if (ResumeState == ELBPR004State::Inspecting && ActiveInspectionRequestToken > 0)
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnInspectionRequested.Broadcast(ActiveInspectionRequestToken, CoilId);
    }
    return true;
}

bool ALBPR004Station::ReconcilePowerLoss(ELBPR004MaterialOwner ConfirmedOwner, FName RecoveryEvidenceId)
{
    if (!CanBeginExternalMutation() || !bPowerLossReconciliationRequired || !bControlPowerOn
        || ConfirmedOwner == ELBPR004MaterialOwner::None || !IsNameSet(RecoveryEvidenceId)
        || ProcessState != ELBPR004State::Fault || ActiveFault == ELBPR004Fault::None)
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    if (ActiveAction.bIsActive)
    {
        ActiveAction.MaterialOwner = ConfirmedOwner;
        ActiveAction.LastEvidenceId = RecoveryEvidenceId;
    }
    bPowerLossReconciliationRequired = false;
    const bool bPreservePreExistingFault = StateBeforePowerLoss == ELBPR004State::Fault
        && ActiveFault != ELBPR004Fault::PowerLossReconciliationRequired
        && ActiveFault != ELBPR004Fault::InFlightMaterialOwnershipUnclear;
    if (!bPreservePreExistingFault)
    {
        ActiveFault = ELBPR004Fault::None;
        ResumeAfterPowerLossWithoutCommand();
    }
    return true;
}

float ALBPR004Station::GetPhaseProgress() const
{
    const float Duration = GetCurrentPhaseDuration();
    return Duration <= 0.0f ? 0.0f : FMath::Clamp(PhaseElapsedSeconds / Duration, 0.0f, 1.0f);
}

bool ALBPR004Station::CanAuthoriseCycle(TArray<FText>& OutBlockingReasons) const
{
    OutBlockingReasons.Reset();
    if (ProcessState != ELBPR004State::AwaitingAuthorisation) OutBlockingReasons.Add(LOCTEXT("AuthoriseState", "Cell is not awaiting authorisation."));
    if (!bControlPowerOn) OutBlockingReasons.Add(LOCTEXT("AuthorisePower", "Control power is off."));
    if (!bCellCommissioned) OutBlockingReasons.Add(LOCTEXT("AuthoriseCommission", "Cell has not been commissioned."));
    if (!bCoilPresent || CoilId.IsEmpty()) OutBlockingReasons.Add(LOCTEXT("AuthoriseCoil", "No packaged coil is present."));
    if (ExpectedCoilId.IsEmpty() || CoilId != ExpectedCoilId) OutBlockingReasons.Add(LOCTEXT("AuthoriseIdentity", "Coil identity does not match the reservation."));
    if (!IsApprovedRecipe(ActiveRecipeId)) OutBlockingReasons.Add(LOCTEXT("AuthoriseRecipe", "A valid approved depack recipe is required."));
    if (!SafetyEnvelopeHealthy()) OutBlockingReasons.Add(LOCTEXT("AuthoriseSafety", "Safety envelope is not healthy."));
    if (!bRobotHealthy) OutBlockingReasons.Add(LOCTEXT("AuthoriseRobot", "Robot is not healthy."));
    if (!bPackagingScannerHealthy) OutBlockingReasons.Add(LOCTEXT("AuthoriseScanner", "Packaging scanner is not healthy."));
    if (ActiveFault != ELBPR004Fault::None) OutBlockingReasons.Add(LOCTEXT("AuthoriseFault", "An active fault must be recovered."));
    if (bManualWrapRecoveryRequired || bPowerLossReconciliationRequired) OutBlockingReasons.Add(LOCTEXT("AuthoriseRecovery", "A recovery workflow is incomplete."));

    ELBPR004Fault WasteFault = ELBPR004Fault::None;
    if (!IsWasteStreamReady(ELBPR004WasteStream::SteelBand, true, WasteFault)) OutBlockingReasons.Add(LOCTEXT("AuthoriseBandWaste", "Steel-band waste module is not ready."));
    if (!IsWasteStreamReady(ELBPR004WasteStream::EdgeProtector, false, WasteFault)) OutBlockingReasons.Add(LOCTEXT("AuthoriseProtectorWaste", "Edge-protector waste stream is not ready."));
    if (!IsWasteStreamReady(ELBPR004WasteStream::PlasticWrap, true, WasteFault)) OutBlockingReasons.Add(LOCTEXT("AuthorisePlasticWaste", "Plastic-wrap waste module is not ready."));
    if (!FilmDewrapStatus.bSpindleHealthy || !FilmDewrapStatus.bDancerAndTensionHealthy
        || !FilmDewrapStatus.bTransferChuteClear || !FilmDewrapStatus.bStripperReady
        || !FilmDewrapStatus.bFragmentCameraClear)
    {
        OutBlockingReasons.Add(LOCTEXT("AuthoriseFilm", "Film dewrapping module is not ready."));
    }
    return OutBlockingReasons.IsEmpty();
}

bool ALBPR004Station::CanReleaseCoil(TArray<FText>& OutBlockingReasons) const
{
    return ValidateReleaseInvariants(OutBlockingReasons, true);
}

bool ALBPR004Station::CanResetFault(TArray<FText>& OutBlockingReasons) const
{
    OutBlockingReasons.Reset();
    if (ProcessState != ELBPR004State::Fault || ActiveFault == ELBPR004Fault::None)
    {
        OutBlockingReasons.Add(LOCTEXT("ResetNoFault", "No active latched fault is available to reset."));
    }
    if (!bControlPowerOn)
    {
        OutBlockingReasons.Add(LOCTEXT("ResetPower", "Control power must be restored."));
    }
    if (bPowerLossReconciliationRequired)
    {
        OutBlockingReasons.Add(LOCTEXT("ResetOwnership", "In-flight material ownership must be reconciled explicitly."));
    }
    if (bManualWrapRecoveryRequired || bManualWrapRecoveryInProgress || !UnrecoveredWrapFragmentIds.IsEmpty())
    {
        OutBlockingReasons.Add(LOCTEXT("ResetManualRecovery", "Trapped-key wrap recovery must be completed first."));
    }
    if (IsHazardousMotionState(StateBeforeFault) && !SafetyEnvelopeHealthy())
    {
        OutBlockingReasons.Add(LOCTEXT("ResetSafety", "Safety envelope is not healthy."));
    }

    ELBPR004Fault WasteFault = ELBPR004Fault::None;
    switch (ActiveFault)
    {
    case ELBPR004Fault::RobotNotHealthy:
        if (!bRobotHealthy) OutBlockingReasons.Add(LOCTEXT("ResetRobot", "Robot health has not recovered."));
        break;
    case ELBPR004Fault::PackagingScanFault:
        if (!bPackagingScannerHealthy) OutBlockingReasons.Add(LOCTEXT("ResetScanner", "Packaging scanner has not recovered."));
        break;
    case ELBPR004Fault::InspectionVisionFault:
        if (!bInspectionSystemHealthy) OutBlockingReasons.Add(LOCTEXT("ResetInspection", "Inspection system has not recovered."));
        break;
    case ELBPR004Fault::BandWinderJam:
    case ELBPR004Fault::BandGuardOpen:
    case ELBPR004Fault::BandCoilEjectionFault:
        if (!IsWasteStreamReady(ELBPR004WasteStream::SteelBand, true, WasteFault)) OutBlockingReasons.Add(LOCTEXT("ResetBandWaste", "Band module remains unavailable."));
        break;
    case ELBPR004Fault::ProtectorWasteStreamFault:
    case ELBPR004Fault::ProtectorGuardOpen:
        if (!IsWasteStreamReady(ELBPR004WasteStream::EdgeProtector, false, WasteFault)) OutBlockingReasons.Add(LOCTEXT("ResetProtectorWaste", "Protector waste stream remains unavailable."));
        break;
    case ELBPR004Fault::FilmSpindleNotHealthy:
    case ELBPR004Fault::FilmSpindleGripFailed:
    case ELBPR004Fault::FilmTensionHighOrLost:
    case ELBPR004Fault::DancerTravelLimit:
    case ELBPR004Fault::CradleSpindleSyncFault:
    case ELBPR004Fault::RobotNotClearForFilmIndex:
    case ELBPR004Fault::FilmStripOffFailed:
        if (!FilmDewrapStatus.bSpindleHealthy || !FilmDewrapStatus.bDancerAndTensionHealthy
            || !FilmDewrapStatus.bRobotClearForIndex || !FilmDewrapStatus.bCradleSpindleSynchronized
            || !FilmDewrapStatus.bTransferChuteClear || !FilmDewrapStatus.bStripperReady)
        {
            OutBlockingReasons.Add(LOCTEXT("ResetFilm", "Film dewrapping recovery conditions are incomplete."));
        }
        break;
    case ELBPR004Fault::PlasticCompactorJam:
    case ELBPR004Fault::PlasticGuardOpen:
    case ELBPR004Fault::PlasticBaleEjectionFault:
        if (!IsWasteStreamReady(ELBPR004WasteStream::PlasticWrap, true, WasteFault)) OutBlockingReasons.Add(LOCTEXT("ResetPlasticWaste", "Plastic compactor remains unavailable."));
        break;
    default:
        break;
    }
    return OutBlockingReasons.IsEmpty();
}

bool ALBPR004Station::IsAtStableSaveBoundary() const
{
    return IsStableStateValue(ProcessState)
        && !bCradleIndexDriveEnabled
        && !bFilmSpindleDriveEnabled
        && !bMutationInProgress
        && !bDispatchingEvents;
}

bool ALBPR004Station::IsSaveStateCoherent(const FLBPR004SaveState& CandidateState, TArray<FText>& OutErrors) const
{
    OutErrors.Reset();
    if (CandidateState.SaveVersion != CurrentSaveVersion) OutErrors.Add(LOCTEXT("SaveVersion", "PR-004 save version is unsupported."));
    if (!IsStableStateValue(CandidateState.State)) OutErrors.Add(LOCTEXT("SaveTransient", "PR-004 snapshot is not at a stable boundary."));
    if (CandidateState.RemainingBandMask < 0 || (CandidateState.RemainingBandMask & ~FullBandMask) != 0) OutErrors.Add(LOCTEXT("SaveBandMask", "Band mask is invalid."));
    if (CandidateState.RemainingProtectorMask < 0 || (CandidateState.RemainingProtectorMask & ~FullProtectorMask) != 0) OutErrors.Add(LOCTEXT("SaveProtectorMask", "Protector mask is invalid."));
    if (CandidateState.RemainingWrapMask < 0 || (CandidateState.RemainingWrapMask & ~FullWrapMask) != 0) OutErrors.Add(LOCTEXT("SaveWrapMask", "Wrap mask is invalid."));
    if ((CandidateState.AcceptedWrapMask & ~FullWrapMask) != 0 || (CandidateState.AcceptedWrapMask & CandidateState.RemainingWrapMask) != 0) OutErrors.Add(LOCTEXT("SaveAcceptedWrap", "Accepted and remaining wrap masks overlap or exceed the contract."));
    if (CandidateState.bCoilPresent && (CandidateState.CoilId.IsEmpty() || CandidateState.HeatId.IsEmpty()
        || CandidateState.SupplierLotId.IsEmpty() || CandidateState.TraceabilityBarcode.IsEmpty()
        || CandidateState.ActiveCycleSerial <= 0)) OutErrors.Add(LOCTEXT("SaveCoilIdentity", "A present coil requires coil, heat, lot and barcode identity plus cycle serial."));
    if (!CandidateState.bCoilPresent && (!CandidateState.CoilId.IsEmpty() || !CandidateState.HeatId.IsEmpty()
        || !CandidateState.SupplierLotId.IsEmpty() || !CandidateState.TraceabilityBarcode.IsEmpty()
        || CandidateState.RemainingBandMask != 0 || CandidateState.RemainingProtectorMask != 0
        || CandidateState.RemainingWrapMask != 0 || CandidateState.ActiveAction.bIsActive)) OutErrors.Add(LOCTEXT("SaveEmptyCell", "An empty cell contains active coil state."));
    if (CandidateState.bIdentityVerified && (CandidateState.CoilId.IsEmpty() || CandidateState.CoilId != CandidateState.ExpectedCoilId)) OutErrors.Add(LOCTEXT("SaveIdentity", "Verified identity does not match the reservation."));
    if (CandidateState.bManualWrapRecoveryInProgress && !CandidateState.bManualWrapRecoveryRequired) OutErrors.Add(LOCTEXT("SaveManualFlag", "Manual recovery is active without a recovery requirement."));
    if (CandidateState.TrappedKeyState == ELBPR004TrappedKeyState::RemovedAndRetained && (!CandidateState.bManualWrapRecoveryInProgress || !CandidateState.bRecoveryZeroMotionVerified)) OutErrors.Add(LOCTEXT("SaveKey", "Retained trapped key lacks an isolated manual-recovery state."));
    if (!CandidateState.UnrecoveredWrapFragmentIds.IsEmpty() && !CandidateState.bManualWrapRecoveryRequired) OutErrors.Add(LOCTEXT("SaveFragments", "Unrecovered wrap fragments are not tied to recovery."));
    if (CandidateState.CompactedBandCoilCount < 0 || CandidateState.CompactedBandCoilCount > 4) OutErrors.Add(LOCTEXT("SaveBandCount", "Compacted band count is outside the four-band contract."));
    if (CandidateState.CompactedPlasticBaleCount < 0 || CandidateState.CompactedPlasticBaleCount > 1) OutErrors.Add(LOCTEXT("SavePlasticCount", "Plastic bale count is outside the one-bale contract."));
    if (CandidateState.State == ELBPR004State::ReadyForHandoff && CandidateState.Disposition != ELBPR004Disposition::Ready) OutErrors.Add(LOCTEXT("SaveReadyDisposition", "Ready state lacks READY disposition."));
    if (CandidateState.State == ELBPR004State::QualityHold && CandidateState.Disposition != ELBPR004Disposition::QualityHold) OutErrors.Add(LOCTEXT("SaveHoldDisposition", "Quality-hold state lacks HOLD disposition."));
    if ((CandidateState.State == ELBPR004State::Rejected || CandidateState.State == ELBPR004State::AwaitingRejectRemoval) && CandidateState.Disposition != ELBPR004Disposition::Reject) OutErrors.Add(LOCTEXT("SaveRejectDisposition", "Reject state lacks REJECT disposition."));
    if (CandidateState.State == ELBPR004State::AwaitingRejectRemoval && CandidateState.ActiveRejectRemovalTransactionId.IsNone()) OutErrors.Add(LOCTEXT("SaveRejectTransaction", "Reject-removal state lacks a transaction."));
    if (CandidateState.bPowerLossReconciliationRequired && CandidateState.State != ELBPR004State::Fault) OutErrors.Add(LOCTEXT("SavePowerLoss", "Power-loss reconciliation must remain latched in FAULT."));

    ValidateActiveActionCoherence(CandidateState, OutErrors);
    ValidateWasteLedgerCoherence(CandidateState, OutErrors);
    return OutErrors.IsEmpty();
}

bool ALBPR004Station::GetStableSaveState(FLBPR004SaveState& OutState) const
{
    if (!IsAtStableSaveBoundary())
    {
        return false;
    }

    OutState = FLBPR004SaveState();
    OutState.SaveVersion = CurrentSaveVersion;
    OutState.State = ProcessState;
    OutState.StateBeforeFault = StateBeforeFault;
    OutState.StateBeforePowerLoss = StateBeforePowerLoss;
    OutState.ActiveFault = ActiveFault;
    OutState.Disposition = Disposition;
    OutState.CoilId = CoilId;
    OutState.HeatId = HeatId;
    OutState.SupplierLotId = SupplierLotId;
    OutState.TraceabilityBarcode = TraceabilityBarcode;
    OutState.ExpectedCoilId = ExpectedCoilId;
    OutState.RecipeId = ActiveRecipeId;
    OutState.ActiveCycleSerial = ActiveCycleSerial;
    OutState.NextCycleSerial = NextCycleSerial;
    OutState.NextActionToken = NextActionToken;
    OutState.NextReportRequestToken = NextReportRequestToken;
    OutState.ActiveScanRequestToken = ActiveScanRequestToken;
    OutState.ActiveInspectionRequestToken = ActiveInspectionRequestToken;
    OutState.RemainingBandMask = RemainingBandMask;
    OutState.RemainingProtectorMask = RemainingProtectorMask;
    OutState.RemainingWrapMask = RemainingWrapMask;
    OutState.AcceptedWrapMask = AcceptedWrapMask;
    OutState.ActiveAction = ActiveAction;
    OutState.WasteLedger = WasteLedger;
    OutState.PackagingScanReport = PackagingScanReport;
    OutState.InspectionReport = InspectionReport;
    OutState.BandStreamStatus = BandStreamStatus;
    OutState.ProtectorStreamStatus = ProtectorStreamStatus;
    OutState.PlasticStreamStatus = PlasticStreamStatus;
    OutState.FilmDewrapStatus = FilmDewrapStatus;
    OutState.CompactedBandCoilCount = CompactedBandCoilCount;
    OutState.CompactedPlasticBaleCount = CompactedPlasticBaleCount;
    OutState.UnrecoveredWrapFragmentIds = UnrecoveredWrapFragmentIds;
    OutState.RecoveredWrapFragmentIds = RecoveredWrapFragmentIds;
    OutState.bManualWrapRecoveryRequired = bManualWrapRecoveryRequired;
    OutState.bManualWrapRecoveryInProgress = bManualWrapRecoveryInProgress;
    OutState.bRecoveryZeroMotionVerified = bRecoveryZeroMotionVerified;
    OutState.TrappedKeyState = TrappedKeyState;
    OutState.ManualRecoveryPermitId = ManualRecoveryPermitId;
    OutState.LastManualRecoveryEvidenceId = LastManualRecoveryEvidenceId;
    OutState.bControlPowerOn = bControlPowerOn;
    OutState.bCellCommissioned = bCellCommissioned;
    OutState.bCoilPresent = bCoilPresent;
    OutState.bIdentityVerified = bIdentityVerified;
    OutState.bPackagingScanAccepted = bPackagingScanAccepted;
    OutState.bInspectionReportAccepted = bInspectionReportAccepted;
    OutState.bCoilTailSecured = bCoilTailSecured;
    OutState.CoilTailEvidenceId = CoilTailEvidenceId;
    OutState.bCradleLocked = bCradleLocked;
    OutState.bCHookWithdrawn = bCHookWithdrawn;
    OutState.bGatesClosed = bGatesClosed;
    OutState.bSafetyCircuitHealthy = bSafetyCircuitHealthy;
    OutState.bPersonnelClear = bPersonnelClear;
    OutState.bRobotHealthy = bRobotHealthy;
    OutState.bPackagingScannerHealthy = bPackagingScannerHealthy;
    OutState.bInspectionSystemHealthy = bInspectionSystemHealthy;
    OutState.bPowerLossReconciliationRequired = bPowerLossReconciliationRequired;
    OutState.ActiveHandoffTransactionId = ActiveHandoffTransactionId;
    OutState.LastCompletedHandoffTransactionId = LastCompletedHandoffTransactionId;
    OutState.ActiveRejectRemovalTransactionId = ActiveRejectRemovalTransactionId;
    OutState.LastCompletedRejectRemovalTransactionId = LastCompletedRejectRemovalTransactionId;
    OutState.LastRejectArchiveRecordId = LastRejectArchiveRecordId;
    OutState.LastCompletedCoilId = LastCompletedCoilId;
    OutState.LastCompletedCycleSerial = LastCompletedCycleSerial;

    TArray<FText> Errors;
    return IsSaveStateCoherent(OutState, Errors);
}

bool ALBPR004Station::RestoreSaveState(const FLBPR004SaveState& InState)
{
    if (!CanBeginExternalMutation())
    {
        return false;
    }
    TArray<FText> Errors;
    if (!IsSaveStateCoherent(InState, Errors))
    {
        return false;
    }
    FScopedBoolFlag MutationGuard(bMutationInProgress);
    StopFilmDrives();

    ProcessState = InState.State;
    StateBeforeFault = InState.StateBeforeFault;
    StateBeforePowerLoss = InState.StateBeforePowerLoss;
    ActiveFault = InState.ActiveFault;
    Disposition = InState.Disposition;
    CoilId = InState.CoilId;
    HeatId = InState.HeatId;
    SupplierLotId = InState.SupplierLotId;
    TraceabilityBarcode = InState.TraceabilityBarcode;
    ExpectedCoilId = InState.ExpectedCoilId;
    ActiveRecipeId = InState.RecipeId;
    ActiveCycleSerial = InState.ActiveCycleSerial;
    NextCycleSerial = FMath::Max<int64>(InState.NextCycleSerial, ActiveCycleSerial + 1);
    NextActionToken = FMath::Max<int64>(InState.NextActionToken, 1);
    NextReportRequestToken = FMath::Max<int64>(InState.NextReportRequestToken, 1);
    ActiveScanRequestToken = InState.ActiveScanRequestToken;
    ActiveInspectionRequestToken = InState.ActiveInspectionRequestToken;
    RemainingBandMask = InState.RemainingBandMask;
    RemainingProtectorMask = InState.RemainingProtectorMask;
    RemainingWrapMask = InState.RemainingWrapMask;
    AcceptedWrapMask = InState.AcceptedWrapMask;
    ActiveAction = InState.ActiveAction;
    WasteLedger = InState.WasteLedger;
    PackagingScanReport = InState.PackagingScanReport;
    InspectionReport = InState.InspectionReport;
    BandStreamStatus = InState.BandStreamStatus;
    ProtectorStreamStatus = InState.ProtectorStreamStatus;
    PlasticStreamStatus = InState.PlasticStreamStatus;
    FilmDewrapStatus = InState.FilmDewrapStatus;
    CompactedBandCoilCount = InState.CompactedBandCoilCount;
    CompactedPlasticBaleCount = InState.CompactedPlasticBaleCount;
    UnrecoveredWrapFragmentIds = InState.UnrecoveredWrapFragmentIds;
    RecoveredWrapFragmentIds = InState.RecoveredWrapFragmentIds;
    bManualWrapRecoveryRequired = InState.bManualWrapRecoveryRequired;
    bManualWrapRecoveryInProgress = InState.bManualWrapRecoveryInProgress;
    bRecoveryZeroMotionVerified = InState.bRecoveryZeroMotionVerified;
    TrappedKeyState = InState.TrappedKeyState;
    ManualRecoveryPermitId = InState.ManualRecoveryPermitId;
    LastManualRecoveryEvidenceId = InState.LastManualRecoveryEvidenceId;
    bControlPowerOn = InState.bControlPowerOn;
    bCellCommissioned = InState.bCellCommissioned;
    bCoilPresent = InState.bCoilPresent;
    bIdentityVerified = InState.bIdentityVerified;
    bPackagingScanAccepted = InState.bPackagingScanAccepted;
    bInspectionReportAccepted = InState.bInspectionReportAccepted;
    bCoilTailSecured = InState.bCoilTailSecured;
    CoilTailEvidenceId = InState.CoilTailEvidenceId;
    bCradleLocked = InState.bCradleLocked;
    bCHookWithdrawn = InState.bCHookWithdrawn;
    bGatesClosed = InState.bGatesClosed;
    bSafetyCircuitHealthy = InState.bSafetyCircuitHealthy;
    bPersonnelClear = InState.bPersonnelClear;
    bRobotHealthy = InState.bRobotHealthy;
    bPackagingScannerHealthy = InState.bPackagingScannerHealthy;
    bInspectionSystemHealthy = InState.bInspectionSystemHealthy;
    bPowerLossReconciliationRequired = InState.bPowerLossReconciliationRequired;
    ActiveHandoffTransactionId = InState.ActiveHandoffTransactionId;
    LastCompletedHandoffTransactionId = InState.LastCompletedHandoffTransactionId;
    ActiveRejectRemovalTransactionId = InState.ActiveRejectRemovalTransactionId;
    LastCompletedRejectRemovalTransactionId = InState.LastCompletedRejectRemovalTransactionId;
    LastRejectArchiveRecordId = InState.LastRejectArchiveRecordId;
    LastCompletedCoilId = InState.LastCompletedCoilId;
    LastCompletedCycleSerial = InState.LastCompletedCycleSerial;
    PhaseElapsedSeconds = 0.0f;
    ItemElapsedSeconds = 0.0f;
    UpdateCoilPresentation();

    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnStateChanged.Broadcast(ELBPR004State::Unsurveyed, ProcessState);
        if (ActiveFault != ELBPR004Fault::None)
        {
            OnFaultRaised.Broadcast(ActiveFault);
        }
        if (bManualWrapRecoveryRequired)
        {
            OnManualRecoveryChanged.Broadcast(true, TrappedKeyState);
        }
    }
    return true;
}

bool ALBPR004Station::CanBeginExternalMutation() const
{
    return !bMutationInProgress && !bDispatchingEvents;
}

void ALBPR004Station::SetProcessStateInternal(ELBPR004State NewState, bool bIssueCommands)
{
    if (ProcessState == NewState)
    {
        return;
    }
    const ELBPR004State Previous = ProcessState;
    ProcessState = NewState;
    PhaseElapsedSeconds = 0.0f;
    ItemElapsedSeconds = 0.0f;
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnStateChanged.Broadcast(Previous, NewState);
    }

    if (!bIssueCommands)
    {
        return;
    }
    if (NewState == ELBPR004State::Scanning && ActiveScanRequestToken > 0)
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnPackagingScanRequested.Broadcast(ActiveScanRequestToken, CoilId, ActiveRecipeId);
    }
    else if (IsPackagingRemovalState(NewState) && ActiveAction.bIsActive)
    {
        BroadcastActiveActionRequest();
    }
    else if (NewState == ELBPR004State::Inspecting && ActiveInspectionRequestToken > 0)
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnInspectionRequested.Broadcast(ActiveInspectionRequestToken, CoilId);
    }
}

void ALBPR004Station::RaiseFaultInternal(ELBPR004Fault Fault)
{
    if (Fault == ELBPR004Fault::None)
    {
        return;
    }
    StopFilmDrives();
    if (ProcessState != ELBPR004State::Fault)
    {
        StateBeforeFault = ProcessState;
    }
    ActiveFault = Fault;
    SetProcessStateInternal(ELBPR004State::Fault, false);
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnFaultRaised.Broadcast(Fault);
}

void ALBPR004Station::AdvanceAutomaticSequence(float DeltaSeconds)
{
    (void)DeltaSeconds;
    if (ProcessState == ELBPR004State::AwaitingRobotClearance)
    {
        TryResumeAfterCraneClearance();
        return;
    }

    if (ProcessState == ELBPR004State::Scanning && PhaseElapsedSeconds >= ReportTimeoutSeconds)
    {
        RaiseFaultInternal(ELBPR004Fault::PackagingScanFault);
    }
    else if (ProcessState == ELBPR004State::Securing && PhaseElapsedSeconds >= PackagingActionTimeoutSeconds)
    {
        RaiseFaultInternal(ELBPR004Fault::CoilNotSeated);
    }
    else if (ProcessState == ELBPR004State::Inspecting && PhaseElapsedSeconds >= ReportTimeoutSeconds)
    {
        RaiseFaultInternal(ELBPR004Fault::InspectionVisionFault);
    }
    else if (ActiveAction.bIsActive && ItemElapsedSeconds >= PackagingActionTimeoutSeconds)
    {
        RaiseFaultInternal(TimeoutFaultForActiveAction());
    }
}

void ALBPR004Station::TryResumeAfterCraneClearance()
{
    if (ProcessState != ELBPR004State::AwaitingRobotClearance)
    {
        return;
    }
    if (!bCradleLocked || !bCHookWithdrawn || !SafetyEnvelopeHealthy() || !bRobotHealthy)
    {
        return;
    }
    SetProcessStateInternal(ELBPR004State::LocatingBands, false);
    CreateNextPackagingAction(true);
}

void ALBPR004Station::CreateNextPackagingAction(bool bBroadcastCommand)
{
    ClearActiveAction();

    int32 Index = INDEX_NONE;
    if (RemainingBandMask != 0)
    {
        SetProcessStateInternal(ELBPR004State::RemovingBands, false);
        Index = FindFirstSetBit(RemainingBandMask, 4);
        ActiveAction.ComponentType = BandComponentType;
        ActiveAction.ActionContract = BandActionContract;
        ActiveAction.WasteStream = ELBPR004WasteStream::SteelBand;
        ActiveAction.TerminalSubstage = ELBPR004ActionSubstage::WasteEjected;
    }
    else if (RemainingProtectorMask != 0)
    {
        SetProcessStateInternal(ELBPR004State::RemovingEdgeProtectors, false);
        Index = FindFirstSetBit(RemainingProtectorMask, 8);
        ActiveAction.ComponentType = ProtectorComponentType;
        ActiveAction.ActionContract = ProtectorActionContract;
        ActiveAction.WasteStream = ELBPR004WasteStream::EdgeProtector;
        ActiveAction.TerminalSubstage = ELBPR004ActionSubstage::WasteTransferAccepted;
    }
    else if (RemainingWrapMask != 0)
    {
        SetProcessStateInternal(ELBPR004State::RemovingWrap, false);
        Index = FindFirstSetBit(RemainingWrapMask, 16);
        const bool bFinalWrap = CountSetBits(RemainingWrapMask) == 1;
        ActiveAction.ComponentType = WrapComponentType;
        ActiveAction.ActionContract = bFinalWrap ? FinalWrapActionContract : WrapActionContract;
        ActiveAction.WasteStream = ELBPR004WasteStream::PlasticWrap;
        ActiveAction.TerminalSubstage = bFinalWrap
            ? ELBPR004ActionSubstage::WasteEjected
            : ELBPR004ActionSubstage::WasteTransferAccepted;
    }
    else
    {
        CreateInspectionRequest(bBroadcastCommand);
        return;
    }

    if (Index == INDEX_NONE)
    {
        RaiseFaultInternal(ELBPR004Fault::PackagingScanFault);
        return;
    }

    ActiveAction.bIsActive = true;
    ActiveAction.ActionToken = NextActionToken++;
    ActiveAction.ComponentIndex = Index + 1;
    ActiveAction.LastAcknowledgedSubstage = ELBPR004ActionSubstage::None;
    ActiveAction.MaterialOwner = ELBPR004MaterialOwner::Coil;
    ActiveAction.LastEvidenceId = NAME_None;
    ItemElapsedSeconds = 0.0f;

    ELBPR004Fault WasteFault = ELBPR004Fault::None;
    const bool bRequireEject = ActiveAction.TerminalSubstage == ELBPR004ActionSubstage::WasteEjected;
    if (!IsWasteStreamReady(ActiveAction.WasteStream, bRequireEject, WasteFault))
    {
        RaiseFaultInternal(WasteFault);
        return;
    }
    if (ActiveAction.ComponentType == WrapComponentType
        && (!FilmDewrapStatus.bSpindleHealthy || !FilmDewrapStatus.bDancerAndTensionHealthy))
    {
        RaiseFaultInternal(!FilmDewrapStatus.bSpindleHealthy
            ? ELBPR004Fault::FilmSpindleNotHealthy
            : ELBPR004Fault::FilmTensionHighOrLost);
        return;
    }

    if (bBroadcastCommand)
    {
        BroadcastActiveActionRequest();
    }
}

void ALBPR004Station::BroadcastActiveActionRequest()
{
    if (!ActiveAction.bIsActive)
    {
        return;
    }
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnPackagingActionRequested.Broadcast(
        ActiveAction.ActionToken,
        ActiveAction.ComponentType,
        ActiveAction.ComponentIndex,
        ActiveAction.ActionContract);
}

void ALBPR004Station::CreateInspectionRequest(bool bBroadcastCommand)
{
    ClearActiveAction();
    ActiveInspectionRequestToken = NextReportRequestToken++;
    SetProcessStateInternal(ELBPR004State::Inspecting, false);
    if (bBroadcastCommand)
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnInspectionRequested.Broadcast(ActiveInspectionRequestToken, CoilId);
    }
}

bool ALBPR004Station::FinalizeActiveAction(FName EvidenceId)
{
    if (!ActiveAction.bIsActive || ActiveAction.LastAcknowledgedSubstage != ActiveAction.TerminalSubstage)
    {
        return false;
    }

    const FLBPR004ActiveAction CompletedAction = ActiveAction;
    const int32 Bit = 1 << (CompletedAction.ComponentIndex - 1);
    bool bWasAppended = false;

    if (CompletedAction.ComponentType == BandComponentType)
    {
        if ((RemainingBandMask & Bit) == 0)
        {
            return false;
        }
        FLBPR004WasteRecord Record;
        Record.RecordId = FName(*FString::Printf(TEXT("PR004_%lld_BAND_%02d"), ActiveCycleSerial, CompletedAction.ComponentIndex));
        Record.CycleSerial = ActiveCycleSerial;
        Record.ActionToken = CompletedAction.ActionToken;
        Record.CoilId = CoilId;
        Record.WasteStream = ELBPR004WasteStream::SteelBand;
        Record.WasteType = CompactedBandCoilType;
        Record.SourceComponentType = BandComponentType;
        Record.SourceComponentIndex = CompletedAction.ComponentIndex;
        Record.AcceptedSourceMask = Bit;
        Record.EvidenceId = EvidenceId;
        if (!AppendWasteRecordIfAbsent(Record, bWasAppended))
        {
            return false;
        }
        if (bWasAppended)
        {
            ++CompactedBandCoilCount;
        }
        RemainingBandMask &= ~Bit;
    }
    else if (CompletedAction.ComponentType == ProtectorComponentType)
    {
        if ((RemainingProtectorMask & Bit) == 0)
        {
            return false;
        }
        FLBPR004WasteRecord Record;
        Record.RecordId = FName(*FString::Printf(TEXT("PR004_%lld_PROTECTOR_%02d"), ActiveCycleSerial, CompletedAction.ComponentIndex));
        Record.CycleSerial = ActiveCycleSerial;
        Record.ActionToken = CompletedAction.ActionToken;
        Record.CoilId = CoilId;
        Record.WasteStream = ELBPR004WasteStream::EdgeProtector;
        Record.WasteType = EdgeProtectorWasteType;
        Record.SourceComponentType = ProtectorComponentType;
        Record.SourceComponentIndex = CompletedAction.ComponentIndex;
        Record.AcceptedSourceMask = Bit;
        Record.EvidenceId = EvidenceId;
        if (!AppendWasteRecordIfAbsent(Record, bWasAppended))
        {
            return false;
        }
        RemainingProtectorMask &= ~Bit;
    }
    else if (CompletedAction.ComponentType == WrapComponentType)
    {
        if ((RemainingWrapMask & Bit) == 0 || !UnrecoveredWrapFragmentIds.IsEmpty())
        {
            return false;
        }
        const bool bFinalWrap = CountSetBits(RemainingWrapMask) == 1;
        if (bFinalWrap)
        {
            FLBPR004WasteRecord Record;
            Record.RecordId = FName(*FString::Printf(TEXT("PR004_%lld_PLASTIC_BALE"), ActiveCycleSerial));
            Record.CycleSerial = ActiveCycleSerial;
            Record.ActionToken = CompletedAction.ActionToken;
            Record.CoilId = CoilId;
            Record.WasteStream = ELBPR004WasteStream::PlasticWrap;
            Record.WasteType = CompactedPlasticBaleType;
            Record.SourceComponentType = WrapComponentType;
            Record.SourceComponentIndex = CompletedAction.ComponentIndex;
            Record.AcceptedSourceMask = AcceptedWrapMask | Bit;
            Record.EvidenceId = EvidenceId;
            if (!AppendWasteRecordIfAbsent(Record, bWasAppended))
            {
                return false;
            }
            if (bWasAppended)
            {
                ++CompactedPlasticBaleCount;
            }
        }
        AcceptedWrapMask |= Bit;
        RemainingWrapMask &= ~Bit;
    }
    else
    {
        return false;
    }

    ClearActiveAction();
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnPackagingRemoved.Broadcast(
            CompletedAction.ActionToken,
            CompletedAction.ComponentType,
            CompletedAction.ComponentIndex);
    }
    CreateNextPackagingAction(true);
    return true;
}

bool ALBPR004Station::AppendWasteRecordIfAbsent(const FLBPR004WasteRecord& Record, bool& bOutWasAppended)
{
    bOutWasAppended = false;
    for (const FLBPR004WasteRecord& Existing : WasteLedger)
    {
        if (Existing.RecordId == Record.RecordId
            || (Existing.CycleSerial == Record.CycleSerial
                && Existing.SourceComponentType == Record.SourceComponentType
                && Existing.SourceComponentIndex == Record.SourceComponentIndex
                && Existing.WasteType == Record.WasteType))
        {
            return Existing.CoilId == Record.CoilId && Existing.EvidenceId == Record.EvidenceId;
        }
    }
    WasteLedger.Add(Record);
    bOutWasAppended = true;
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnWasteRecordAppended.Broadcast(Record);
    return true;
}

void ALBPR004Station::ClearActiveAction()
{
    StopFilmDrives();
    ActiveAction = FLBPR004ActiveAction();
    ItemElapsedSeconds = 0.0f;
}

void ALBPR004Station::ResetActiveCycleAfterTransfer()
{
    StopFilmDrives();
    CoilId.Empty();
    HeatId.Empty();
    SupplierLotId.Empty();
    TraceabilityBarcode.Empty();
    ExpectedCoilId.Empty();
    ActiveRecipeId = NAME_None;
    ActiveCycleSerial = 0;
    bCoilPresent = false;
    bIdentityVerified = false;
    bPackagingScanAccepted = false;
    bInspectionReportAccepted = false;
    bCoilTailSecured = false;
    CoilTailEvidenceId = NAME_None;
    RemainingBandMask = 0;
    RemainingProtectorMask = 0;
    RemainingWrapMask = 0;
    AcceptedWrapMask = 0;
    CompactedBandCoilCount = 0;
    CompactedPlasticBaleCount = 0;
    WasteLedger.Reset();
    PackagingScanReport = FLBPR004PackagingScanReport();
    InspectionReport = FLBPR004InspectionReport();
    UnrecoveredWrapFragmentIds.Reset();
    RecoveredWrapFragmentIds.Reset();
    bManualWrapRecoveryRequired = false;
    bManualWrapRecoveryInProgress = false;
    bRecoveryZeroMotionVerified = false;
    TrappedKeyState = ELBPR004TrappedKeyState::Installed;
    ManualRecoveryPermitId = NAME_None;
    LastManualRecoveryEvidenceId = NAME_None;
    ActiveFault = ELBPR004Fault::None;
    Disposition = ELBPR004Disposition::Unknown;
    ActiveScanRequestToken = 0;
    ActiveInspectionRequestToken = 0;
    ActiveHandoffTransactionId = NAME_None;
    ActiveRejectRemovalTransactionId = NAME_None;
    bPowerLossReconciliationRequired = false;
    ClearActiveAction();
    SetProcessStateInternal(ELBPR004State::AwaitingCoil, false);
    UpdateCoilPresentation();
}

void ALBPR004Station::UpdateCoilPresentation()
{
    if (!WrappedCoilVisual || !BareCoilVisual)
    {
        return;
    }

    const bool bShowBare = IsCoilUnpackaged();
    const bool bShowWrapped = bCoilPresent && !bShowBare;
    UpdateTraceabilityPresentation();
    WrappedCoilVisual->SetVisibility(bShowWrapped, true);
    WrappedCoilVisual->SetHiddenInGame(!bShowWrapped, true);
    WrappedCoilVisual->SetCollisionEnabled(bShowWrapped ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    if (WrappedCoilLabelVisual)
    {
        WrappedCoilLabelVisual->SetVisibility(bShowWrapped, true);
        WrappedCoilLabelVisual->SetHiddenInGame(!bShowWrapped, true);
    }
    if (WrappedCoilLabelHeading)
    {
        WrappedCoilLabelHeading->SetVisibility(bShowWrapped, true);
        WrappedCoilLabelHeading->SetHiddenInGame(!bShowWrapped, true);
    }
    if (WrappedCoilLabelDetail)
    {
        WrappedCoilLabelDetail->SetVisibility(bShowWrapped, true);
        WrappedCoilLabelDetail->SetHiddenInGame(!bShowWrapped, true);
    }
    if (WrappedCoilTraceLabelVisual)
    {
        WrappedCoilTraceLabelVisual->SetVisibility(bShowWrapped, true);
        WrappedCoilTraceLabelVisual->SetHiddenInGame(!bShowWrapped, true);
    }
    if (WrappedCoilTraceText)
    {
        WrappedCoilTraceText->SetVisibility(bShowWrapped, true);
        WrappedCoilTraceText->SetHiddenInGame(!bShowWrapped, true);
    }
    if (WrappedCoilBarcodeText)
    {
        WrappedCoilBarcodeText->SetVisibility(bShowWrapped, true);
        WrappedCoilBarcodeText->SetHiddenInGame(!bShowWrapped, true);
    }
    BareCoilVisual->SetVisibility(bShowBare, true);
    BareCoilVisual->SetHiddenInGame(!bShowBare, true);
    BareCoilVisual->SetCollisionEnabled(bShowBare ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    if (bShowBare)
    {
        BareCoilVisual->SetCollisionResponseToAllChannels(ECR_Ignore);
        BareCoilVisual->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    }
}

void ALBPR004Station::UpdateTraceabilityPresentation()
{
    if (WrappedCoilTraceText)
    {
        WrappedCoilTraceText->SetText(FText::FromString(GetWrappedCoilTraceLabelText()));
    }
    if (WrappedCoilBarcodeText)
    {
        const FString BarcodeLine = TraceabilityBarcode.IsEmpty()
            ? TEXT("|||| ||| ||||  -")
            : FString::Printf(TEXT("|||| ||| ||||  %s"), *TraceabilityBarcode);
        WrappedCoilBarcodeText->SetText(FText::FromString(BarcodeLine));
    }
}

FString ALBPR004Station::GetWrappedCoilTraceLabelText() const
{
    return FString::Printf(TEXT("HEAT  %s\nLOT   %s"),
        HeatId.IsEmpty() ? TEXT("-") : *HeatId,
        SupplierLotId.IsEmpty() ? TEXT("-") : *SupplierLotId);
}

void ALBPR004Station::ResumeAfterPowerLossWithoutCommand()
{
    StopFilmDrives();
    ELBPR004State ResumeState = StateBeforePowerLoss;
    if (ResumeState == ELBPR004State::Fault)
    {
        ResumeState = ActiveAction.bIsActive ? ELBPR004State::RemovingWrap : ELBPR004State::AwaitingAuthorisation;
    }
    SetProcessStateInternal(ResumeState, false);
    if (ActiveAction.bIsActive && IsPackagingRemovalState(ResumeState))
    {
        BroadcastActiveActionRequest();
    }
    else if (ResumeState == ELBPR004State::Scanning && ActiveScanRequestToken > 0)
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnPackagingScanRequested.Broadcast(ActiveScanRequestToken, CoilId, ActiveRecipeId);
    }
    else if (ResumeState == ELBPR004State::Inspecting && ActiveInspectionRequestToken > 0)
    {
        FScopedBoolFlag DispatchGuard(bDispatchingEvents);
        OnInspectionRequested.Broadcast(ActiveInspectionRequestToken, CoilId);
    }
}

void ALBPR004Station::StopFilmDrives()
{
    if (!bCradleIndexDriveEnabled && !bFilmSpindleDriveEnabled)
    {
        return;
    }
    bCradleIndexDriveEnabled = false;
    bFilmSpindleDriveEnabled = false;
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnFilmDriveCommand.Broadcast(false, false);
}

void ALBPR004Station::StartFilmDrives()
{
    if (bCradleIndexDriveEnabled && bFilmSpindleDriveEnabled)
    {
        return;
    }
    bCradleIndexDriveEnabled = true;
    bFilmSpindleDriveEnabled = true;
    FScopedBoolFlag DispatchGuard(bDispatchingEvents);
    OnFilmDriveCommand.Broadcast(true, true);
}

bool ALBPR004Station::IsPackagingRemovalState(ELBPR004State State) const
{
    return State == ELBPR004State::RemovingBands
        || State == ELBPR004State::RemovingEdgeProtectors
        || State == ELBPR004State::RemovingWrap;
}

bool ALBPR004Station::IsHazardousMotionState(ELBPR004State State) const
{
    return State == ELBPR004State::Securing
        || State == ELBPR004State::LocatingBands
        || IsPackagingRemovalState(State)
        || State == ELBPR004State::Inspecting;
}

bool ALBPR004Station::SafetyEnvelopeHealthy() const
{
    return bGatesClosed && bSafetyCircuitHealthy && bPersonnelClear;
}

bool ALBPR004Station::StateSpecificMotionInterlocksHealthy() const
{
    if (!IsHazardousMotionState(ProcessState))
    {
        return true;
    }
    // The securing stroke clamps a newly lowered coil while the crane C-hook may
    // still be in the bore. Robot motion is forbidden until the following
    // AwaitingRobotClearance state verifies both clamp and hook-clear sensors.
    if (ProcessState == ELBPR004State::Securing)
    {
        return bCoilPresent;
    }
    if (!bCradleLocked || !bCHookWithdrawn)
    {
        return false;
    }
    if (ProcessState == ELBPR004State::LocatingBands || IsPackagingRemovalState(ProcessState) || ProcessState == ELBPR004State::Inspecting)
    {
        return bRobotHealthy;
    }
    return true;
}

bool ALBPR004Station::IsWasteStreamReady(ELBPR004WasteStream Stream, bool bRequireEject, ELBPR004Fault& OutFault) const
{
    OutFault = ELBPR004Fault::None;
    const FLBPR004WasteStreamStatus* Status = nullptr;
    switch (Stream)
    {
    case ELBPR004WasteStream::SteelBand: Status = &BandStreamStatus; break;
    case ELBPR004WasteStream::EdgeProtector: Status = &ProtectorStreamStatus; break;
    case ELBPR004WasteStream::PlasticWrap: Status = &PlasticStreamStatus; break;
    default: return false;
    }

    if (!Status->bGuardClosed)
    {
        OutFault = Stream == ELBPR004WasteStream::SteelBand ? ELBPR004Fault::BandGuardOpen
            : (Stream == ELBPR004WasteStream::PlasticWrap ? ELBPR004Fault::PlasticGuardOpen : ELBPR004Fault::ProtectorGuardOpen);
    }
    else if (!Status->bEquipmentHealthy)
    {
        OutFault = Stream == ELBPR004WasteStream::SteelBand ? ELBPR004Fault::BandWinderJam
            : (Stream == ELBPR004WasteStream::PlasticWrap ? ELBPR004Fault::PlasticCompactorJam : ELBPR004Fault::ProtectorWasteStreamFault);
    }
    else if (!Status->bBinPresent || !Status->bCapacityAvailable)
    {
        OutFault = ELBPR004Fault::WasteBinFull;
    }
    else if (bRequireEject && !Status->bEjectReady)
    {
        OutFault = Stream == ELBPR004WasteStream::SteelBand
            ? ELBPR004Fault::BandCoilEjectionFault
            : ELBPR004Fault::PlasticBaleEjectionFault;
    }
    return OutFault == ELBPR004Fault::None;
}

bool ALBPR004Station::IsApprovedRecipe(FName RecipeId) const
{
    return !RecipeId.IsNone() && ApprovedRecipeIds.Contains(RecipeId);
}

bool ALBPR004Station::ValidateReleaseInvariants(TArray<FText>& OutBlockingReasons, bool bRequireReadyDisposition) const
{
    OutBlockingReasons.Reset();
    if (!bCoilPresent || CoilId.IsEmpty()) OutBlockingReasons.Add(LOCTEXT("ReleaseCoil", "No coil is present."));
    if (!bIdentityVerified || CoilId != ExpectedCoilId) OutBlockingReasons.Add(LOCTEXT("ReleaseIdentity", "Coil identity is not verified."));
    if (!bPackagingScanAccepted) OutBlockingReasons.Add(LOCTEXT("ReleaseScan", "Packaging scan is not accepted."));
    if (RemainingBandMask != 0 || RemainingProtectorMask != 0 || RemainingWrapMask != 0) OutBlockingReasons.Add(LOCTEXT("ReleasePackaging", "Packaging material remains on the coil."));
    if (CompactedBandCoilCount != 4 || CountWasteRecordsForCycle(ActiveCycleSerial, ELBPR004WasteStream::SteelBand, CompactedBandCoilType) != 4) OutBlockingReasons.Add(LOCTEXT("ReleaseBands", "Four compacted band coils have not been positively accounted for."));
    if (AcceptedWrapMask != FullWrapMask || CompactedPlasticBaleCount != 1 || CountWasteRecordsForCycle(ActiveCycleSerial, ELBPR004WasteStream::PlasticWrap, CompactedPlasticBaleType) != 1) OutBlockingReasons.Add(LOCTEXT("ReleasePlastic", "The full wrapping and one irregular plastic bale have not been positively accounted for."));
    if (!UnrecoveredWrapFragmentIds.IsEmpty() || bManualWrapRecoveryRequired || bManualWrapRecoveryInProgress) OutBlockingReasons.Add(LOCTEXT("ReleaseFragments", "Wrap fragments or manual recovery remain unresolved."));
    if (TrappedKeyState == ELBPR004TrappedKeyState::RemovedAndRetained) OutBlockingReasons.Add(LOCTEXT("ReleaseKey", "Trapped key has not been restored."));
    if (!bInspectionReportAccepted || InspectionReport.CoilId != CoilId) OutBlockingReasons.Add(LOCTEXT("ReleaseInspection", "Inspection report is not accepted for this coil."));
    if (!bCoilTailSecured || CoilTailEvidenceId.IsNone()) OutBlockingReasons.Add(LOCTEXT("ReleaseTail", "Bare coil tail is not secured."));
    if (ActiveFault != ELBPR004Fault::None || bPowerLossReconciliationRequired) OutBlockingReasons.Add(LOCTEXT("ReleaseFault", "A fault or power-loss reconciliation remains active."));
    if (bRequireReadyDisposition && (ProcessState != ELBPR004State::ReadyForHandoff || Disposition != ELBPR004Disposition::Ready)) OutBlockingReasons.Add(LOCTEXT("ReleaseDisposition", "Coil has not received READY disposition."));
    return OutBlockingReasons.IsEmpty();
}

bool ALBPR004Station::FaultRecoverySatisfied(FName RecoveryEvidenceId, TArray<FText>& OutBlockingReasons) const
{
    CanResetFault(OutBlockingReasons);
    if (!IsNameSet(RecoveryEvidenceId))
    {
        OutBlockingReasons.Add(LOCTEXT("ResetEvidence", "Cause-specific recovery evidence is required."));
    }
    return OutBlockingReasons.IsEmpty();
}

bool ALBPR004Station::ValidateActiveActionCoherence(const FLBPR004SaveState& CandidateState, TArray<FText>& OutErrors) const
{
    const FLBPR004ActiveAction& Action = CandidateState.ActiveAction;
    if (!Action.bIsActive)
    {
        return true;
    }
    if (!IsPackagingRemovalState(CandidateState.State) && CandidateState.State != ELBPR004State::Fault)
    {
        OutErrors.Add(LOCTEXT("SaveActionState", "Active packaging action exists outside removal or fault state."));
    }
    if (Action.ActionToken <= 0 || Action.ComponentIndex <= 0 || Action.ComponentType.IsNone() || Action.WasteStream == ELBPR004WasteStream::None)
    {
        OutErrors.Add(LOCTEXT("SaveActionIdentity", "Active packaging action identity is incomplete."));
        return false;
    }

    int32 Mask = 0;
    int32 Maximum = 0;
    if (Action.ComponentType == BandComponentType) { Mask = CandidateState.RemainingBandMask; Maximum = 4; }
    else if (Action.ComponentType == ProtectorComponentType) { Mask = CandidateState.RemainingProtectorMask; Maximum = 8; }
    else if (Action.ComponentType == WrapComponentType) { Mask = CandidateState.RemainingWrapMask; Maximum = 16; }
    else OutErrors.Add(LOCTEXT("SaveActionType", "Active packaging action type is unknown."));
    if (Maximum > 0 && (Action.ComponentIndex > Maximum || (Mask & (1 << (Action.ComponentIndex - 1))) == 0))
    {
        OutErrors.Add(LOCTEXT("SaveActionMask", "Active packaging action no longer owns a pending source component."));
    }
    if (Action.LastAcknowledgedSubstage >= Action.TerminalSubstage)
    {
        OutErrors.Add(LOCTEXT("SaveActionTerminal", "Completed action was persisted as still active."));
    }
    return true;
}

bool ALBPR004Station::ValidateWasteLedgerCoherence(const FLBPR004SaveState& CandidateState, TArray<FText>& OutErrors) const
{
    TArray<FName> RecordIds;
    for (const FLBPR004WasteRecord& Record : CandidateState.WasteLedger)
    {
        if (Record.RecordId.IsNone() || Record.CycleSerial <= 0 || Record.CoilId.IsEmpty()
            || Record.WasteStream == ELBPR004WasteStream::None || Record.WasteType.IsNone()
            || Record.SourceComponentType.IsNone() || Record.SourceComponentIndex <= 0 || Record.EvidenceId.IsNone())
        {
            OutErrors.Add(LOCTEXT("SaveWasteRecord", "Waste ledger contains an incomplete record."));
        }
        if (RecordIds.Contains(Record.RecordId))
        {
            OutErrors.Add(LOCTEXT("SaveWasteDuplicate", "Waste ledger contains a duplicate record ID."));
        }
        RecordIds.Add(Record.RecordId);
    }

    int32 BandRecords = 0;
    int32 PlasticRecords = 0;
    for (const FLBPR004WasteRecord& Record : CandidateState.WasteLedger)
    {
        if (Record.CycleSerial != CandidateState.ActiveCycleSerial)
        {
            continue;
        }
        if (Record.WasteStream == ELBPR004WasteStream::SteelBand && Record.WasteType == CompactedBandCoilType) ++BandRecords;
        if (Record.WasteStream == ELBPR004WasteStream::PlasticWrap && Record.WasteType == CompactedPlasticBaleType) ++PlasticRecords;
    }
    if (BandRecords != CandidateState.CompactedBandCoilCount) OutErrors.Add(LOCTEXT("SaveBandLedger", "Compacted band count does not match the waste ledger."));
    if (PlasticRecords != CandidateState.CompactedPlasticBaleCount) OutErrors.Add(LOCTEXT("SavePlasticLedger", "Plastic bale count does not match the waste ledger."));
    return true;
}

int32 ALBPR004Station::CountWasteRecordsForCycle(int64 CycleSerial, ELBPR004WasteStream Stream, FName WasteType) const
{
    int32 Count = 0;
    for (const FLBPR004WasteRecord& Record : WasteLedger)
    {
        if (Record.CycleSerial == CycleSerial && Record.WasteStream == Stream && Record.WasteType == WasteType)
        {
            ++Count;
        }
    }
    return Count;
}

float ALBPR004Station::GetCurrentPhaseDuration() const
{
    switch (ProcessState)
    {
    case ELBPR004State::Scanning:
    case ELBPR004State::Inspecting:
        return ReportTimeoutSeconds;
    case ELBPR004State::Securing:
    case ELBPR004State::RemovingBands:
    case ELBPR004State::RemovingEdgeProtectors:
    case ELBPR004State::RemovingWrap:
        return PackagingActionTimeoutSeconds;
    default:
        return 0.0f;
    }
}

ELBPR004Fault ALBPR004Station::TimeoutFaultForActiveAction() const
{
    if (!ActiveAction.bIsActive)
    {
        return ELBPR004Fault::PackagingScanFault;
    }
    if (ActiveAction.ComponentType == BandComponentType)
    {
        if (ActiveAction.LastAcknowledgedSubstage == ELBPR004ActionSubstage::None) return ELBPR004Fault::BandEndNotCaptured;
        if (ActiveAction.LastAcknowledgedSubstage == ELBPR004ActionSubstage::SourceSecured) return ELBPR004Fault::BandWithdrawalJam;
        if (ActiveAction.LastAcknowledgedSubstage == ELBPR004ActionSubstage::WasteProcessed) return ELBPR004Fault::BandCoilEjectionFault;
        return ELBPR004Fault::BandWinderJam;
    }
    if (ActiveAction.ComponentType == ProtectorComponentType)
    {
        return ELBPR004Fault::EdgeProtectorJam;
    }
    if (ActiveAction.ComponentType == WrapComponentType)
    {
        switch (ActiveAction.LastAcknowledgedSubstage)
        {
        case ELBPR004ActionSubstage::None: return ELBPR004Fault::WrapTabNotCaptured;
        case ELBPR004ActionSubstage::SourceSecured: return ELBPR004Fault::WrapSeamNotFound;
        case ELBPR004ActionSubstage::SourceDetached: return ELBPR004Fault::FilmSpindleGripFailed;
        case ELBPR004ActionSubstage::SpindleGripConfirmed: return ELBPR004Fault::RobotNotClearForFilmIndex;
        case ELBPR004ActionSubstage::RobotClearForIndex: return ELBPR004Fault::CradleSpindleSyncFault;
        case ELBPR004ActionSubstage::CradleSpindleSynchronized: return ELBPR004Fault::FilmTensionHighOrLost;
        case ELBPR004ActionSubstage::TensionControlledWindComplete: return ELBPR004Fault::FilmStripOffFailed;
        case ELBPR004ActionSubstage::WasteTransferAccepted: return ELBPR004Fault::PlasticCompactorJam;
        case ELBPR004ActionSubstage::WasteProcessed: return ELBPR004Fault::PlasticBaleEjectionFault;
        default: return ELBPR004Fault::WrapTornOrJammed;
        }
    }
    return ELBPR004Fault::PackagingScanFault;
}

ELBPR004ActionSubstage ALBPR004Station::ExpectedNextSubstage() const
{
    if (!ActiveAction.bIsActive)
    {
        return ELBPR004ActionSubstage::None;
    }
    const ELBPR004ActionSubstage Last = ActiveAction.LastAcknowledgedSubstage;
    if (ActiveAction.ComponentType == BandComponentType)
    {
        switch (Last)
        {
        case ELBPR004ActionSubstage::None: return ELBPR004ActionSubstage::SourceSecured;
        case ELBPR004ActionSubstage::SourceSecured: return ELBPR004ActionSubstage::SourceDetached;
        case ELBPR004ActionSubstage::SourceDetached: return ELBPR004ActionSubstage::WasteTransferAccepted;
        case ELBPR004ActionSubstage::WasteTransferAccepted: return ELBPR004ActionSubstage::WasteProcessed;
        case ELBPR004ActionSubstage::WasteProcessed: return ELBPR004ActionSubstage::WasteEjected;
        default: return ELBPR004ActionSubstage::None;
        }
    }
    if (ActiveAction.ComponentType == ProtectorComponentType)
    {
        switch (Last)
        {
        case ELBPR004ActionSubstage::None: return ELBPR004ActionSubstage::SourceSecured;
        case ELBPR004ActionSubstage::SourceSecured: return ELBPR004ActionSubstage::SourceDetached;
        case ELBPR004ActionSubstage::SourceDetached: return ELBPR004ActionSubstage::WasteTransferAccepted;
        default: return ELBPR004ActionSubstage::None;
        }
    }
    if (ActiveAction.ComponentType == WrapComponentType)
    {
        switch (Last)
        {
        case ELBPR004ActionSubstage::None: return ELBPR004ActionSubstage::SourceSecured;
        case ELBPR004ActionSubstage::SourceSecured: return ELBPR004ActionSubstage::SourceDetached;
        case ELBPR004ActionSubstage::SourceDetached: return ELBPR004ActionSubstage::SpindleGripConfirmed;
        case ELBPR004ActionSubstage::SpindleGripConfirmed: return ELBPR004ActionSubstage::RobotClearForIndex;
        case ELBPR004ActionSubstage::RobotClearForIndex: return ELBPR004ActionSubstage::CradleSpindleSynchronized;
        case ELBPR004ActionSubstage::CradleSpindleSynchronized: return ELBPR004ActionSubstage::TensionControlledWindComplete;
        case ELBPR004ActionSubstage::TensionControlledWindComplete: return ELBPR004ActionSubstage::WasteTransferAccepted;
        case ELBPR004ActionSubstage::WasteTransferAccepted:
            return ActiveAction.TerminalSubstage == ELBPR004ActionSubstage::WasteEjected
                ? ELBPR004ActionSubstage::WasteProcessed
                : ELBPR004ActionSubstage::None;
        case ELBPR004ActionSubstage::WasteProcessed: return ELBPR004ActionSubstage::WasteEjected;
        default: return ELBPR004ActionSubstage::None;
        }
    }
    return ELBPR004ActionSubstage::None;
}

int32 ALBPR004Station::FindFirstSetBit(int32 Mask, int32 MaximumItems)
{
    for (int32 Index = 0; Index < MaximumItems; ++Index)
    {
        if ((Mask & (1 << Index)) != 0)
        {
            return Index;
        }
    }
    return INDEX_NONE;
}

int32 ALBPR004Station::CountSetBits(int32 Mask)
{
    int32 Count = 0;
    while (Mask != 0)
    {
        Mask &= (Mask - 1);
        ++Count;
    }
    return Count;
}

bool ALBPR004Station::IsStableStateValue(ELBPR004State State)
{
    switch (State)
    {
    case ELBPR004State::Unsurveyed:
    case ELBPR004State::Isolated:
    case ELBPR004State::SafeForAccess:
    case ELBPR004State::AwaitingCoil:
    case ELBPR004State::CoilLoaded:
    case ELBPR004State::AwaitingAuthorisation:
    case ELBPR004State::AwaitingRobotClearance:
    case ELBPR004State::AwaitingDisposition:
    case ELBPR004State::ReadyForHandoff:
    case ELBPR004State::QualityHold:
    case ELBPR004State::Rejected:
    case ELBPR004State::AwaitingRejectRemoval:
    case ELBPR004State::Fault:
        return true;
    default:
        return false;
    }
}

ELBPR004MaterialOwner ALBPR004Station::OwnerForSubstage(ELBPR004ActionSubstage Substage)
{
    switch (Substage)
    {
    case ELBPR004ActionSubstage::SourceSecured:
    case ELBPR004ActionSubstage::SourceDetached:
        return ELBPR004MaterialOwner::Robot;
    case ELBPR004ActionSubstage::SpindleGripConfirmed:
    case ELBPR004ActionSubstage::RobotClearForIndex:
    case ELBPR004ActionSubstage::CradleSpindleSynchronized:
    case ELBPR004ActionSubstage::TensionControlledWindComplete:
    case ELBPR004ActionSubstage::WasteTransferAccepted:
    case ELBPR004ActionSubstage::WasteProcessed:
        return ELBPR004MaterialOwner::WasteModule;
    case ELBPR004ActionSubstage::WasteEjected:
        return ELBPR004MaterialOwner::WasteBin;
    default:
        return ELBPR004MaterialOwner::Coil;
    }
}

#undef LOCTEXT_NAMESPACE
