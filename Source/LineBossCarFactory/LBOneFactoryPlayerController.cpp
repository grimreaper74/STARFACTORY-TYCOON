#include "LBOneFactoryPlayerController.h"

#include "Components/InputComponent.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "LBOneFactoryDevEnvelopeActor.h"
#include "LBOneFactoryDevFactoryCommands.h"
#include "LBOneFactoryDevRestoredShopActor.h"
#include "LBOneFactoryDevStationDressingActor.h"
#include "LBOneFactoryFlowStripWidget.h"
#include "LBManagementPawn.h"
#include "LBOneFactoryOperationsSubsystem.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryProductionHUD.h"
#include "LBOneFactoryRuntimeRegistrySubsystem.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactoryScanBeamActor.h"
#include "LBOneFactorySaveSubsystem.h"
#include "LBOneFactoryWIPPresentationActor.h"

DEFINE_LOG_CATEGORY_STATIC(LogLineBossOneFactoryPlayer, Display, All);

namespace LBOneFactoryPlayerPrivate
{
    /**
     * The three quality gates are real work positions on the canonical route,
     * not generic scenery.  Keeping the scanner placement derived from that
     * route means a restored or rebuilt factory gets exactly the same visual
     * inspection points without adding map-owned actors or save state.
     */
    void EnsureInspectionScanners(UWorld* World,
        const ALBOneFactoryRuntimeCoordinator* Coordinator)
    {
        if (!World || !Coordinator)
        {
            return;
        }

        TArray<FLBOneFactoryRuntimeStationStep> Route;
        FName TopologyId = NAME_None;
        FString RouteReason;
        if (!Coordinator->GetConfiguredStationRoute(Route, TopologyId,
                RouteReason))
        {
            UE_LOG(LogLineBossOneFactoryPlayer, Warning,
                TEXT("LINE_BOSS_PLAYER_SCANNERS no route: %s"),
                *RouteReason);
            return;
        }

        const TSet<ELBOneFactoryDepartment> ScannerDepartments =
        {
            ELBOneFactoryDepartment::Body,
            ELBOneFactoryDepartment::Paint,
            ELBOneFactoryDepartment::Assembly
        };
        int32 Configured = 0;
        for (const FLBOneFactoryRuntimeStationStep& Step : Route)
        {
            if (!Step.bQualityGate
                || !ScannerDepartments.Contains(Step.Department))
            {
                continue;
            }

            const FName ScannerTag(*FString::Printf(
                TEXT("LB.OneFactory.ScanBeam.%s"),
                *Step.StationId.ToString()));
            bool bAlreadyPresent = false;
            for (TActorIterator<ALBOneFactoryScanBeamActor> It(World); It;
                ++It)
            {
                if (IsValid(*It) && It->Tags.Contains(ScannerTag))
                {
                    bAlreadyPresent = true;
                    break;
                }
            }

            if (!bAlreadyPresent)
            {
                FTransform Transform = Step.WorldTransform;
                // The authored beam is a suspended carriage. The line datum
                // is floor-level, so raise it over the vehicle envelope while
                // preserving the station's route-facing rotation.
                Transform.AddToTranslation(FVector(0.0f, 0.0f, 340.0f));
                FActorSpawnParameters Params;
                Params.SpawnCollisionHandlingOverride =
                    ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
                if (ALBOneFactoryScanBeamActor* Scanner =
                        World->SpawnActor<ALBOneFactoryScanBeamActor>(
                            ALBOneFactoryScanBeamActor::StaticClass(),
                            Transform, Params))
                {
                    Scanner->Tags.AddUnique(ScannerTag);
                    Scanner->Tags.AddUnique(TEXT("LB.OneFactory.Inspection"));
                    ++Configured;
                }
            }
            else
            {
                ++Configured;
            }
        }

        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_SCANNERS configured=%d expected=3"),
            Configured);
    }

    ALBOneFactoryRuntimeCoordinator* FindCoordinator(const UWorld* World)
    {
        if (!World) return nullptr;
        if (ULBOneFactoryRuntimeRegistrySubsystem* Registry =
                World->GetSubsystem<ULBOneFactoryRuntimeRegistrySubsystem>())
        {
            ALBOneFactoryProductionFlowAuthority* Production = nullptr;
            ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
            FString Reason;
            return Registry->ResolveRuntimeBackbone(Production, Coordinator, Reason)
                ? Coordinator : nullptr;
        }
        return nullptr;
    }

    ALBOneFactoryProductionFlowAuthority* FindProduction(const UWorld* World)
    {
        if (!World) return nullptr;
        if (ULBOneFactoryRuntimeRegistrySubsystem* Registry =
                World->GetSubsystem<ULBOneFactoryRuntimeRegistrySubsystem>())
        {
            ALBOneFactoryProductionFlowAuthority* Production = nullptr;
            ALBOneFactoryRuntimeCoordinator* Coordinator = nullptr;
            FString Reason;
            if (Registry->ResolveRuntimeBackbone(Production, Coordinator, Reason))
            {
                return Production;
            }
        }
        return nullptr;
    }
}

ALBOneFactoryPlayerController::ALBOneFactoryPlayerController()
{
    PrimaryActorTick.bCanEverTick = false;
    bShowMouseCursor = true;
}

void ALBOneFactoryPlayerController::BeginPlay()
{
    Super::BeginPlay();

    // The production HUD is deliberately mouse-first, but it must never turn
    // the factory shortcuts into UI-only input after an operator clicks a
    // card, transport chip or inspector button.
    FInputModeGameAndUI InputMode;
    InputMode.SetHideCursorDuringCapture(false);
    SetInputMode(InputMode);
    SetShowMouseCursor(true);
    InstallEnhancedInputMappings();
}

void ALBOneFactoryPlayerController::SetupInputComponent()
{
    Super::SetupInputComponent();
    if (!InputComponent)
    {
        return;
    }

    // SetupInputComponent happens before BeginPlay for normal possession, so
    // create the actions here. BeginPlay then installs the same context on
    // the local-player subsystem once UI focus has been configured.
    InstallEnhancedInputMappings();
    BindEnhancedInputActions();
}

UInputAction* ALBOneFactoryPlayerController::CreateCommandAction(
    const FName ActionName)
{
    UInputAction* Action = NewObject<UInputAction>(this, ActionName);
    if (Action)
    {
        Action->ValueType = EInputActionValueType::Boolean;
    }
    return Action;
}

void ALBOneFactoryPlayerController::MapCommand(UInputAction* Action,
    const FKey& Key)
{
    if (OneFactoryInputContext && Action && Key.IsValid())
    {
        OneFactoryInputContext->MapKey(Action, Key);
    }
}

void ALBOneFactoryPlayerController::InstallEnhancedInputMappings()
{
    if (!OneFactoryInputContext)
    {
        OneFactoryInputContext = NewObject<UInputMappingContext>(this,
            TEXT("IMC_OneFactoryRuntime"));
        if (!OneFactoryInputContext)
        {
            UE_LOG(LogLineBossOneFactoryPlayer, Error,
                TEXT("LINE_BOSS_PLAYER_INPUT mapping_context=0"));
            return;
        }

        PlaceOrderInputAction = CreateCommandAction(TEXT("IA_PlaceOrder"));
        TogglePauseInputAction = CreateCommandAction(TEXT("IA_TogglePause"));
        SpeedNormalInputAction = CreateCommandAction(TEXT("IA_SpeedNormal"));
        SpeedFastInputAction = CreateCommandAction(TEXT("IA_SpeedFast"));
        SpeedVeryFastInputAction = CreateCommandAction(TEXT("IA_SpeedVeryFast"));
        PassQualityInputAction = CreateCommandAction(TEXT("IA_PassQuality"));
        ReworkInputAction = CreateCommandAction(TEXT("IA_Rework"));
        ServiceInputAction = CreateCommandAction(TEXT("IA_Service"));
        SaveInputAction = CreateCommandAction(TEXT("IA_Save"));
        LoadInputAction = CreateCommandAction(TEXT("IA_Load"));
        FocusPressInputAction = CreateCommandAction(TEXT("IA_FocusPress"));
        FocusBodyInputAction = CreateCommandAction(TEXT("IA_FocusBody"));
        FocusPaintInputAction = CreateCommandAction(TEXT("IA_FocusPaint"));
        FocusAssemblyInputAction = CreateCommandAction(TEXT("IA_FocusAssembly"));

        MapCommand(PlaceOrderInputAction, EKeys::B);
        MapCommand(PlaceOrderInputAction, EKeys::N);
        MapCommand(TogglePauseInputAction, EKeys::SpaceBar);
        MapCommand(SpeedNormalInputAction, EKeys::One);
        MapCommand(SpeedFastInputAction, EKeys::Two);
        MapCommand(SpeedVeryFastInputAction, EKeys::Three);
        MapCommand(PassQualityInputAction, EKeys::Q);
        MapCommand(ReworkInputAction, EKeys::R);
        MapCommand(ServiceInputAction, EKeys::M);
        MapCommand(SaveInputAction, EKeys::F5);
        MapCommand(LoadInputAction, EKeys::F9);
        MapCommand(FocusPressInputAction, EKeys::F1);
        MapCommand(FocusBodyInputAction, EKeys::F2);
        MapCommand(FocusPaintInputAction, EKeys::F3);
        MapCommand(FocusAssemblyInputAction, EKeys::F4);
    }

    if (!bEnhancedInputContextInstalled)
    {
        if (ULocalPlayer* LocalPlayer = GetLocalPlayer())
        {
            if (UEnhancedInputLocalPlayerSubsystem* InputSubsystem =
                    LocalPlayer->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
            {
                InputSubsystem->AddMappingContext(OneFactoryInputContext, 0);
                bEnhancedInputContextInstalled = true;
                UE_LOG(LogLineBossOneFactoryPlayer, Display,
                    TEXT("LINE_BOSS_PLAYER_INPUT enhanced_context=installed mappings=15"));
            }
        }
    }
}

void ALBOneFactoryPlayerController::BindEnhancedInputActions()
{
    UEnhancedInputComponent* EnhancedInput =
        Cast<UEnhancedInputComponent>(InputComponent);
    if (!EnhancedInput)
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_INPUT enhanced_component=0"));
        return;
    }

    const auto Bind = [EnhancedInput, this](UInputAction* Action,
        void (ALBOneFactoryPlayerController::*Handler)())
    {
        if (Action)
        {
            EnhancedInput->BindAction(Action, ETriggerEvent::Started, this,
                Handler);
        }
    };
    Bind(PlaceOrderInputAction, &ALBOneFactoryPlayerController::PlaceOrder);
    Bind(TogglePauseInputAction, &ALBOneFactoryPlayerController::TogglePause);
    Bind(SpeedNormalInputAction, &ALBOneFactoryPlayerController::SetSpeedNormal);
    Bind(SpeedFastInputAction, &ALBOneFactoryPlayerController::SetSpeedFast);
    Bind(SpeedVeryFastInputAction, &ALBOneFactoryPlayerController::SetSpeedVeryFast);
    Bind(PassQualityInputAction, &ALBOneFactoryPlayerController::PassOldestQualityHold);
    Bind(ReworkInputAction, &ALBOneFactoryPlayerController::ReworkOldestQualityHold);
    Bind(ServiceInputAction, &ALBOneFactoryPlayerController::ServicePlant);
    Bind(SaveInputAction, &ALBOneFactoryPlayerController::SaveFactory);
    Bind(LoadInputAction, &ALBOneFactoryPlayerController::LoadFactory);
    Bind(FocusPressInputAction, &ALBOneFactoryPlayerController::FocusPressShop);
    Bind(FocusBodyInputAction, &ALBOneFactoryPlayerController::FocusBodyShop);
    Bind(FocusPaintInputAction, &ALBOneFactoryPlayerController::FocusPaintShop);
    Bind(FocusAssemblyInputAction, &ALBOneFactoryPlayerController::FocusAssemblyShop);
}

bool ALBOneFactoryPlayerController::InputKey(const FInputKeyEventArgs& Params)
{
    // UMG's focus path is allowed to consume input before the normal binding
    // stack sees it. Handle the advertised keyboard controls and mouse-wheel
    // zoom at the controller boundary so the mouse-first production HUD
    // cannot disable the management camera.
    if (Params.Event == IE_Axis && Params.Key == EKeys::MouseWheelAxis
        && GetPawn() && Cast<ALBManagementPawn>(GetPawn())->HandleDirectZoomInput(
            Params.AmountDepressed))
    {
        return true;
    }
    if ((Params.Event == IE_Pressed || Params.Event == IE_Released)
        && GetPawn() && Cast<ALBManagementPawn>(GetPawn())->HandleDirectNavigationKey(
            Params.Key, Params.Event == IE_Pressed))
    {
        return true;
    }
    if (Params.Event == IE_Pressed && HandleKeyboardShortcut(Params.Key))
    {
        return true;
    }
    return Super::InputKey(Params);
}

bool ALBOneFactoryPlayerController::HandleKeyboardShortcut(const FKey& Key)
{
    if (Key == EKeys::B || Key == EKeys::N) { PlaceOrder(); return true; }
    if (Key == EKeys::SpaceBar) { TogglePause(); return true; }
    if (Key == EKeys::One) { SetSpeedNormal(); return true; }
    if (Key == EKeys::Two) { SetSpeedFast(); return true; }
    if (Key == EKeys::Three) { SetSpeedVeryFast(); return true; }
    if (Key == EKeys::Q) { PassOldestQualityHold(); return true; }
    if (Key == EKeys::R) { ReworkOldestQualityHold(); return true; }
    if (Key == EKeys::M) { ServicePlant(); return true; }
    if (Key == EKeys::F5) { SaveFactory(); return true; }
    if (Key == EKeys::F9) { LoadFactory(); return true; }
    if (Key == EKeys::F1) { FocusPressShop(); return true; }
    if (Key == EKeys::F2) { FocusBodyShop(); return true; }
    if (Key == EKeys::F3) { FocusPaintShop(); return true; }
    if (Key == EKeys::F4) { FocusAssemblyShop(); return true; }
    return false;
}

void ALBOneFactoryPlayerController::FocusShopGroup(const int32 GroupIndex)
{
    const ALBOneFactoryProductionHUD* ProductionHUD =
        Cast<ALBOneFactoryProductionHUD>(GetHUD());
    ULBOneFactoryFlowStripWidget* Strip =
        ProductionHUD ? ProductionHUD->GetFlowStripWidget() : nullptr;
    if (Strip)
    {
        // Same path as a card click: frame the shop, open its panel.
        Strip->SimulateCardClick(GroupIndex);
    }
}

// Group indices follow the seven-card strip: press 1, body 3, paint 4,
// assembly 5 (0/2/6 are intake, stillages and dispatch).
void ALBOneFactoryPlayerController::FocusPressShop() { FocusShopGroup(1); }
void ALBOneFactoryPlayerController::FocusBodyShop() { FocusShopGroup(3); }
void ALBOneFactoryPlayerController::FocusPaintShop() { FocusShopGroup(4); }
void ALBOneFactoryPlayerController::FocusAssemblyShop()
{
    FocusShopGroup(5);
}

void ALBOneFactoryPlayerController::ServicePlant()
{
    using namespace LBOneFactoryPlayerPrivate;

    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(GetWorld());
    if (!Coordinator)
    {
        return;
    }
    FString Reason;
    const bool bOk = Coordinator->PerformPlantMaintenance(Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_MAINTENANCE ok=%d %s"), bOk ? 1 : 0, *Reason);
}

void ALBOneFactoryPlayerController::CommissionFactory()
{
    FString Reason;
    const bool bActivated = ActivatePrebuiltFactory(Reason);
    if (bActivated)
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_COMMISSION activated=1 %s"), *Reason);
    }
    else
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_COMMISSION activated=0 %s"), *Reason);
    }
}

bool ALBOneFactoryPlayerController::ActivatePrebuiltFactory(FString& OutReason)
{
    OutReason.Reset();
    UWorld* World = GetWorld();
    if (!World)
    {
        OutReason = TEXT("ONEFACTORY PLAYER HAS NO WORLD");
        return false;
    }

    FString Reason;
    const bool bBuilt =
        ULBOneFactoryDevFactory::BuildAndCommissionWholeFactory(this, Reason);
    if (!bBuilt)
    {
        // A restored factory is only "already commissioned" if its complete
        // 57-station runtime contract validates.  Finding a coordinator alone
        // used to accept a press-only partial map and strand every order once
        // it reached the missing Paint authority.
        ALBOneFactoryRuntimeCoordinator* Coordinator =
            ULBOneFactoryDevFactory::FindCoordinator(World);
        FString RuntimeReason;
        if (!Coordinator || !Coordinator->ValidateRuntimeFactory(RuntimeReason))
        {
            OutReason = !Reason.IsEmpty()
                ? Reason
                : !RuntimeReason.IsEmpty()
                    ? RuntimeReason
                    : TEXT("PREBUILT FACTORY COMMISSIONING FAILED");
            return false;
        }
    }
    EnsureSitePresentation();
    OutReason = bBuilt
        ? Reason
        : TEXT("PREBUILT FACTORY ALREADY COMMISSIONED; PRESENTATION RESTORED");
    return true;
}

void ALBOneFactoryPlayerController::EnsureSitePresentation()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    FActorSpawnParameters Params;
    Params.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

    // Bring the site up with the factory: enclosure, machinery, lighting and
    // the work-in-progress view. Every step finds an existing actor before
    // spawning, and every builder rebuilds its own content, so running this
    // after a save-load, a console build or a repeated B press converges on
    // exactly one of everything.
    FString StepReason;
    ALBOneFactoryDevEnvelopeActor* Envelope = nullptr;
    for (TActorIterator<ALBOneFactoryDevEnvelopeActor> It(World); It; ++It)
    {
        if (IsValid(*It)) { Envelope = *It; break; }
    }
    if (!Envelope)
    {
        Envelope = World->SpawnActor<ALBOneFactoryDevEnvelopeActor>(
            ALBOneFactoryDevEnvelopeActor::StaticClass(),
            FVector::ZeroVector, FRotator::ZeroRotator, Params);
    }
    if (Envelope)
    {
        // 2200 cm eaves: the restored shop's wide-span trusses hang at
        // 1740 cm with their top chords near 2000, so a 1400 wall left the
        // whole roof zone floating against void.
        Envelope->BuildFromRoute(6000.0, 2200.0, StepReason);
    }

    ALBOneFactoryDevStationDressingActor* Dressing = nullptr;
    for (TActorIterator<ALBOneFactoryDevStationDressingActor> It(World); It;
        ++It)
    {
        if (IsValid(*It)) { Dressing = *It; break; }
    }
    if (!Dressing)
    {
        Dressing = World->SpawnActor<ALBOneFactoryDevStationDressingActor>(
            ALBOneFactoryDevStationDressingActor::StaticClass(),
            FVector::ZeroVector, FRotator::ZeroRotator, Params);
    }
    if (Dressing)
    {
        const bool bDressed = Dressing->BuildFromRoute(StepReason);
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_DRESSING ok=%d %s"), bDressed ? 1 : 0,
            *StepReason);
    }

    // The scanner is attached to the three real quality gates after the
    // canonical route and station dressing exist. It is actor-owned visual
    // motion only, so it cannot alter WIP, route topology or saved progress.
    LBOneFactoryPlayerPrivate::EnsureInspectionScanners(World,
        LBOneFactoryPlayerPrivate::FindCoordinator(World));

    // The old restored-shop manifest was a visual recovery aid, not a
    // production authority. It placed legacy imported press scenery around
    // the new native train, creating duplicate machines, intersecting
    // conveyors and the non-Nanite shadow overflow visible in the playable
    // press shop. The canonical station dressing above is the only visual
    // owner in the player build. Remove any stale runtime instance as well,
    // so an old session cannot reintroduce the duplicate layer.
    for (TActorIterator<ALBOneFactoryDevRestoredShopActor> It(World); It; ++It)
    {
        if (IsValid(*It))
        {
            It->Destroy();
        }
    }

    ULBOneFactoryDevFactory::SetRoofHidden(this, true, 900.0, StepReason);

    // The detailed press train now stands at the ConfigurablePressTrain
    // station, so the 268-primitive press blockout must no longer render,
    // exactly as the detailed-press recovery design specifies. Visibility
    // only; LB.OneFactory.PressBlockout 1 restores it.
    for (TActorIterator<ALBOneFactoryPressStarterPresentationActor> It(World);
        It; ++It)
    {
        if (IsValid(*It))
        {
            It->SetActorHiddenInGame(true);
        }
    }
    ULBOneFactoryDevFactory::EnsureDevLighting(this, 9.0f, StepReason);

    bool bHasWip = false;
    for (TActorIterator<ALBOneFactoryWIPPresentationActor> It(World); It; ++It)
    {
        if (IsValid(*It)) { bHasWip = true; break; }
    }
    if (!bHasWip)
    {
        World->SpawnActor<ALBOneFactoryWIPPresentationActor>(
            ALBOneFactoryWIPPresentationActor::StaticClass(),
            FVector::ZeroVector, FRotator::ZeroRotator, Params);
    }

    // Frame onto the player's own pawn, not a dev camera. Passing true here
    // handed the view target to a transient ACameraActor that was never given
    // back, so from this point on every camera control moved an off-screen pawn
    // while the screen stayed frozen on one fixed shot for the whole session.
    ULBOneFactoryDevFactory::FrameProductionLine(this, TEXT("All"), StepReason,
        /*bDriveViewTarget=*/false);

    // Report who actually owns the view. This regressed silently once and cost a
    // great deal of confusion: the camera controls all worked, so nothing looked
    // broken except the screen. viewIsPawn=1 is the contract.
    const AActor* ViewTarget = GetViewTarget();
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_VIEW viewIsPawn=%d viewTarget=%s pawn=%s %s"),
        (ViewTarget && ViewTarget == GetPawn()) ? 1 : 0,
        ViewTarget ? *ViewTarget->GetName() : TEXT("<none>"),
        GetPawn() ? *GetPawn()->GetName() : TEXT("<none>"),
        *StepReason);
}

void ALBOneFactoryPlayerController::PlaceOrder()
{
    FString Reason;
    const bool bOk =
        ULBOneFactoryDevFactory::StartDemoProduction(this, 1, Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_ORDER ok=%d %s"), bOk ? 1 : 0, *Reason);
}

void ALBOneFactoryPlayerController::ApplyTimeScale(const float TimeScale)
{
    // Routed through the operations subsystem, not the coordinator directly:
    // rate 0 must become the ledger's durable bLinePaused, and the
    // coordinator's SetRuntimeTimeScale clamp ([0.25, 4.0]) rejects 0, which
    // is how the pause key shipped dead.
    UWorld* World = GetWorld();
    ULBOneFactoryOperationsSubsystem* Operations =
        World ? World->GetSubsystem<ULBOneFactoryOperationsSubsystem>()
              : nullptr;
    if (!Operations)
    {
        return;
    }
    FString Reason;
    if (Operations->SetSimulationRate(TimeScale, Reason))
    {
        if (TimeScale > KINDA_SMALL_NUMBER)
        {
            LastRunningTimeScale = TimeScale;
        }
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_SPEED %.2fx %s"), TimeScale, *Reason);
    }
    else
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_SPEED rejected %.2f: %s"), TimeScale,
            *Reason);
    }
}

void ALBOneFactoryPlayerController::TogglePause()
{
    using namespace LBOneFactoryPlayerPrivate;

    ALBOneFactoryProductionFlowAuthority* Production =
        FindProduction(GetWorld());
    if (!Production)
    {
        return;
    }
    // Pause state lives on the ledger, not in the time scale: the scale
    // never goes below 0.25, so reading it always claimed "running".
    const bool bPaused = Production->CaptureLedger().bLinePaused;
    ApplyTimeScale(bPaused ? LastRunningTimeScale : 0.0f);
}

void ALBOneFactoryPlayerController::SetSpeedNormal() { ApplyTimeScale(1.0f); }
void ALBOneFactoryPlayerController::SetSpeedFast() { ApplyTimeScale(2.0f); }
void ALBOneFactoryPlayerController::SetSpeedVeryFast() { ApplyTimeScale(4.0f); }

bool ALBOneFactoryPlayerController::ResolveOldestHold(FName& OutUnitId,
    FString& OutReason) const
{
    using namespace LBOneFactoryPlayerPrivate;

    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(GetWorld());
    ALBOneFactoryProductionFlowAuthority* Production =
        FindProduction(GetWorld());
    if (!Coordinator || !Production)
    {
        OutReason = TEXT("no commissioned factory yet");
        return false;
    }

    // Ledger order is creation order, so the first match is the oldest car
    // waiting - which is the one a line manager would clear first.
    const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    for (const FLBOneFactoryVehicleUnitState& Unit : Ledger.Units)
    {
        if (Unit.bDispatched)
        {
            continue;
        }
        FLBOneFactoryRuntimeVehicleStatus Status;
        FString StatusReason;
        if (Coordinator->GetVehicleRuntimeStatus(Unit.UnitId, Status,
                StatusReason)
            && Status.bAwaitingQualityResult)
        {
            OutUnitId = Unit.UnitId;
            return true;
        }
    }
    OutReason = TEXT("nothing is waiting on a quality result");
    return false;
}

void ALBOneFactoryPlayerController::PassOldestQualityHold()
{
    using namespace LBOneFactoryPlayerPrivate;

    FName UnitId = NAME_None;
    FString Reason;
    if (!ResolveOldestHold(UnitId, Reason))
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_QUALITY %s"), *Reason);
        return;
    }
    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(GetWorld());
    FLBOneFactoryRuntimeVehicleStatus Status;
    FString StatusReason;
    if (!Coordinator || !Coordinator->GetVehicleRuntimeStatus(UnitId, Status,
            StatusReason))
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_QUALITY_PASS no durable status unit=%s %s"),
            *UnitId.ToString(), *StatusReason);
        return;
    }
    const FName EvidenceId(*FString::Printf(TEXT("PLAYER_QA_%s_%d"),
        *UnitId.ToString(), Status.StageRevision));
    const bool bOk = Coordinator->SubmitRuntimeQualityResult(
        UnitId, ELBOneFactoryVehicleQualityState::Passed, EvidenceId, Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_QUALITY_PASS ok=%d unit=%s %s"),
        bOk ? 1 : 0, *UnitId.ToString(), *Reason);
}

void ALBOneFactoryPlayerController::ReworkOldestQualityHold()
{
    using namespace LBOneFactoryPlayerPrivate;

    FName UnitId = NAME_None;
    FString Reason;
    if (!ResolveOldestHold(UnitId, Reason))
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Display,
            TEXT("LINE_BOSS_PLAYER_QUALITY %s"), *Reason);
        return;
    }
    ALBOneFactoryRuntimeCoordinator* Coordinator = FindCoordinator(GetWorld());
    FLBOneFactoryRuntimeVehicleStatus Status;
    FString StatusReason;
    if (!Coordinator || !Coordinator->GetVehicleRuntimeStatus(UnitId, Status,
            StatusReason))
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_REWORK no durable status unit=%s %s"),
            *UnitId.ToString(), *StatusReason);
        return;
    }
    const FName EvidenceId(*FString::Printf(TEXT("PLAYER_REWORK_%s_%d"),
        *UnitId.ToString(), Status.StageRevision));
    // Rework repeats the same inspection cycle without creating another unit.
    const bool bOk = Coordinator
        && Coordinator->CompleteRuntimeRework(UnitId, EvidenceId, Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_REWORK ok=%d unit=%s %s"),
        bOk ? 1 : 0, *UnitId.ToString(), *Reason);
}

void ALBOneFactoryPlayerController::SaveFactory()
{
    ULBOneFactorySaveSubsystem* Saves =
        GetWorld() ? GetWorld()->GetSubsystem<ULBOneFactorySaveSubsystem>()
                   : nullptr;
    if (!Saves)
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_SAVE no save subsystem"));
        return;
    }
    FString Reason;
    const bool bOk = Saves->SaveOneFactory(Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_SAVE ok=%d %s"), bOk ? 1 : 0, *Reason);
}

void ALBOneFactoryPlayerController::LoadFactory()
{
    ULBOneFactorySaveSubsystem* Saves =
        GetWorld() ? GetWorld()->GetSubsystem<ULBOneFactorySaveSubsystem>()
                   : nullptr;
    if (!Saves)
    {
        UE_LOG(LogLineBossOneFactoryPlayer, Warning,
            TEXT("LINE_BOSS_PLAYER_LOAD no save subsystem"));
        return;
    }
    FString Reason;
    const bool bOk = Saves->LoadOneFactory(Reason);
    UE_LOG(LogLineBossOneFactoryPlayer, Display,
        TEXT("LINE_BOSS_PLAYER_LOAD ok=%d %s"), bOk ? 1 : 0, *Reason);
    if (bOk)
    {
        // A restored factory arrives without its site presentation - the
        // save carries production state, not scenery - so bring the
        // envelope, dressing, restored shop, lighting and WIP view up
        // around the loaded line.
        EnsureSitePresentation();
    }
}
