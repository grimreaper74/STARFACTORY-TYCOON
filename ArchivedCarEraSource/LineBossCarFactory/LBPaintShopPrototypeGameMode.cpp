#include "LBPaintShopPrototypeGameMode.h"

#include "Components/ActorComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "LBBodyWeldLineActor.h"
#include "LBPaintShopBuildAuthority.h"
#include "LBPaintShopCellActor.h"
#include "LBPaintShopManagementPawn.h"
#include "LBPaintShopPrototypeHUD.h"
#include "LBPaintShopPrototypeRuntime.h"
#include "TimerManager.h"

ALBPaintShopPrototypeGameMode::ALBPaintShopPrototypeGameMode()
{
    PrimaryActorTick.bCanEverTick = false;
    DefaultPawnClass = ALBPaintShopManagementPawn::StaticClass();
    HUDClass = ALBPaintShopPrototypeHUD::StaticClass();
}

void ALBPaintShopPrototypeGameMode::BeginPlay()
{
    Super::BeginPlay();
    // The bootstrap owns startup. Retry inspection for at most twelve frames so
    // actor BeginPlay order cannot create a false failure; no retry initializes it.
    DeferredValidationAttemptsRemaining = 12;
    GetWorldTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(
        this, &ALBPaintShopPrototypeGameMode::RunDeferredStartupValidation));
}

void ALBPaintShopPrototypeGameMode::EndPlay(
    const EEndPlayReason::Type EndPlayReason)
{
    GetWorldTimerManager().ClearTimer(IntegrityValidationTimer);
    DestroyOperatorWeldSource();
    Super::EndPlay(EndPlayReason);
}

void ALBPaintShopPrototypeGameMode::HandleStartingNewPlayer_Implementation(
    APlayerController* NewPlayer)
{
    Super::HandleStartingNewPlayer_Implementation(NewPlayer);
    ValidatePrototypeShellNow(NewPlayer);
}

bool ALBPaintShopPrototypeGameMode::ValidateBootstrapContract(
    const int32 BootstrapCount, const int32 BuildAuthorityCount,
    const int32 RuntimeCount,
    const ELBPaintShopPrototypeBootstrapState BootstrapState,
    const bool bHasBuildAuthority, const bool bHasRuntime,
    const bool bRuntimeInitialized, const bool bRuntimeBoundToAuthority,
    const bool bHasApprovedEDCoatCell, FString& OutReason)
{
    if (BootstrapCount != 1)
    {
        OutReason = FString::Printf(
            TEXT("PAINT SHOP PLAYER SHELL REQUIRES EXACTLY ONE MAP BOOTSTRAP; FOUND %d"),
            BootstrapCount);
        return false;
    }
    if (BuildAuthorityCount != 1 || RuntimeCount != 1)
    {
        OutReason = FString::Printf(
            TEXT("PAINT SHOP PLAYER SHELL REQUIRES EXACTLY ONE BUILD AUTHORITY AND ONE RUNTIME; FOUND %d AND %d"),
            BuildAuthorityCount, RuntimeCount);
        return false;
    }
    if (BootstrapState != ELBPaintShopPrototypeBootstrapState::Ready)
    {
        OutReason = TEXT("PAINT SHOP MAP BOOTSTRAP IS NOT READY");
        return false;
    }
    if (!bHasBuildAuthority || !bHasRuntime)
    {
        OutReason = TEXT("PAINT SHOP READY BOOTSTRAP IS MISSING ITS OWNED AUTHORITIES");
        return false;
    }
    if (!bRuntimeInitialized)
    {
        OutReason = TEXT("PAINT SHOP PROTOTYPE RUNTIME IS NOT INITIALIZED");
        return false;
    }
    if (!bRuntimeBoundToAuthority)
    {
        OutReason = TEXT("PAINT SHOP PROTOTYPE AUTHORITIES ARE NOT BOUND");
        return false;
    }
    if (!bHasApprovedEDCoatCell)
    {
        OutReason = TEXT("PAINT SHOP APPROVED ED-COAT CELL IS NOT DISCOVERABLE");
        return false;
    }
    OutReason = TEXT("PAINT SHOP PROTOTYPE ISOLATED - ED-COAT READY");
    return true;
}

bool ALBPaintShopPrototypeGameMode::ValidatePrototypeShellNow(
    APlayerController* PreferredController)
{
    const bool bWasReady = bPrototypeBootstrapValid && bManagementCameraFocused;
    const FString PreviousStatus = PrototypeShellStatus;
    UWorld* World = GetWorld();
    int32 BootstrapCount = 0;
    int32 BuildAuthorityCount = 0;
    int32 RuntimeCount = 0;
    ALBPaintShopPrototypeWorldBootstrap* OnlyBootstrap = nullptr;
    if (World)
    {
        for (TActorIterator<ALBPaintShopPrototypeWorldBootstrap> It(World); It; ++It)
        {
            if (!IsValid(*It) || It->IsActorBeingDestroyed()) continue;
            ++BootstrapCount;
            OnlyBootstrap = *It;
        }
        for (TActorIterator<ALBPaintShopBuildAuthority> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++BuildAuthorityCount;
        }
        for (TActorIterator<ALBPaintShopPrototypeRuntime> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++RuntimeCount;
        }
    }

    ALBPaintShopBuildAuthority* Authority = BootstrapCount == 1
        ? OnlyBootstrap->GetBuildAuthority() : nullptr;
    ALBPaintShopPrototypeRuntime* Runtime = BootstrapCount == 1
        ? OnlyBootstrap->GetRuntime() : nullptr;
    ALBPaintShopCellActor* Cell = Runtime ? Runtime->GetEDCoatCell() : nullptr;
    const FLBPaintShopApprovedEDCoatLayoutItem Approved =
        ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
    FString PlacementReason;
    const bool bRuntimeBound = Runtime && Authority
        && Runtime->GetBuildAuthority() == Authority
        && Authority->GetOwner() == OnlyBootstrap
        && Runtime->GetOwner() == OnlyBootstrap;
    const bool bApprovedCell = Cell && Authority
        && Cell->GetOwner() == Authority
        && Authority->FindCell(Approved.CellId) == Cell
        && Cell->GetCellId() == Approved.CellId
        && Cell->GetDefinitionId() == Approved.DefinitionId
        && Cell->GetActorTransform().Equals(Approved.WorldTransform, 0.01f)
        && Authority->ValidateApprovedCellPlacement(
            Cell->GetDefinitionId(), Cell->GetActorTransform(), PlacementReason);

    bPrototypeBootstrapValid = ValidateBootstrapContract(BootstrapCount,
        BuildAuthorityCount, RuntimeCount,
        BootstrapCount == 1 ? OnlyBootstrap->GetBootstrapState()
            : ELBPaintShopPrototypeBootstrapState::Uninitialized,
        IsValid(Authority), IsValid(Runtime), Runtime && Runtime->IsInitialized(),
        bRuntimeBound, bApprovedCell, PrototypeShellStatus);
    PrototypeBootstrap = bPrototypeBootstrapValid ? OnlyBootstrap : nullptr;
    if (!bPrototypeBootstrapValid)
    {
        bManagementCameraFocused = false;
        FocusedManagementController.Reset();
        if (bWasReady || PrototypeShellStatus != PreviousStatus)
        {
            UE_LOG(LogTemp, Error,
                TEXT("LINE_BOSS_PAINT_SHOP_PLAYER_SHELL result=FAIL detail=\"%s\""),
                *PrototypeShellStatus);
        }
        return false;
    }

    APlayerController* Controller = PreferredController
        ? PreferredController : World ? World->GetFirstPlayerController() : nullptr;
    ALBPaintShopManagementPawn* Pawn = Controller
        ? Cast<ALBPaintShopManagementPawn>(Controller->GetPawn()) : nullptr;
    const bool bExistingFocusIsCoherent = Pawn
        && Pawn->IsBoundToPrototypeBootstrap(OnlyBootstrap);
    bManagementCameraFocused = bExistingFocusIsCoherent
        ? true : FocusManagementPawn(Controller);
    if (bManagementCameraFocused)
    {
        FocusedManagementController = Controller;
    }
    if (!bManagementCameraFocused)
    {
        PrototypeShellStatus = TEXT(
            "PAINT SHOP PROTOTYPE ISOLATED - ED-COAT READY - MANAGEMENT PAWN NOT YET AVAILABLE");
        if (PrototypeShellStatus != PreviousStatus)
        {
            UE_LOG(LogTemp, Warning,
                TEXT("LINE_BOSS_PAINT_SHOP_PLAYER_SHELL result=WAIT camera_focused=false detail=\"%s\""),
                *PrototypeShellStatus);
        }
        return false;
    }
    PrototypeShellStatus = TEXT("PAINT SHOP PROTOTYPE ISOLATED - ED-COAT READY");
    if (HasActorBegunPlay()
        && !GetWorldTimerManager().IsTimerActive(IntegrityValidationTimer))
    {
        GetWorldTimerManager().SetTimer(IntegrityValidationTimer, this,
            &ALBPaintShopPrototypeGameMode::MonitorPrototypeShellIntegrity,
            1.0f, true, 1.0f);
    }
    if (!bWasReady || PrototypeShellStatus != PreviousStatus)
    {
        UE_LOG(LogTemp, Display,
            TEXT("LINE_BOSS_PAINT_SHOP_PLAYER_SHELL result=PASS camera_focused=true detail=\"%s\""),
            *PrototypeShellStatus);
    }
    return true;
}

void ALBPaintShopPrototypeGameMode::RunDeferredStartupValidation()
{
    APlayerController* Controller = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
    if (ValidatePrototypeShellNow(Controller))
    {
        return;
    }

    --DeferredValidationAttemptsRemaining;
    if (DeferredValidationAttemptsRemaining > 0)
    {
        GetWorldTimerManager().SetTimerForNextTick(FTimerDelegate::CreateUObject(
            this, &ALBPaintShopPrototypeGameMode::RunDeferredStartupValidation));
    }
}

void ALBPaintShopPrototypeGameMode::MonitorPrototypeShellIntegrity()
{
    ValidatePrototypeShellNow(GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr);
}

bool ALBPaintShopPrototypeGameMode::FocusManagementPawn(APlayerController* Controller)
{
    ALBPaintShopManagementPawn* Pawn = Controller
        ? Cast<ALBPaintShopManagementPawn>(Controller->GetPawn()) : nullptr;
    const bool bFocused = Pawn && PrototypeBootstrap.IsValid()
        && Pawn->FocusEDCoatCell(PrototypeBootstrap.Get());
    bManagementCameraFocused = bFocused;
    if (bFocused)
    {
        FocusedManagementController = Controller;
        PrototypeShellStatus = TEXT("PAINT SHOP PROTOTYPE ISOLATED - ED-COAT READY");
    }
    return bFocused;
}

ALBPaintShopPrototypeRuntime* ALBPaintShopPrototypeGameMode::ResolveOperatorRuntime(
    FString& OutReason)
{
    OutReason.Reset();
    APlayerController* Controller = FocusedManagementController.Get();
    if (!Controller && GetWorld())
    {
        Controller = GetWorld()->GetFirstPlayerController();
    }
    if (!ValidatePrototypeShellNow(Controller))
    {
        OutReason = PrototypeShellStatus.IsEmpty()
            ? TEXT("PAINT OPERATOR SHELL IS NOT READY") : PrototypeShellStatus;
        return nullptr;
    }
    ALBPaintShopPrototypeWorldBootstrap* Bootstrap = PrototypeBootstrap.Get();
    ALBPaintShopPrototypeRuntime* Runtime = Bootstrap ? Bootstrap->GetRuntime() : nullptr;
    if (!IsValid(Runtime) || Runtime->IsActorBeingDestroyed()
        || Runtime->GetOwner() != Bootstrap || !Runtime->IsInitialized())
    {
        OutReason = TEXT("PAINT OPERATOR RUNTIME AUTHORITY IS NOT COHERENT");
        return nullptr;
    }
    return Runtime;
}

bool ALBPaintShopPrototypeGameMode::StartCanonicalWeldHandoff(FString& OutReason)
{
    ALBPaintShopPrototypeRuntime* Runtime = ResolveOperatorRuntime(OutReason);
    if (!Runtime)
    {
        return FinishOperatorAction(TEXT("START"), false, OutReason, OutReason);
    }
    if (Runtime->IsProcessFaulted())
    {
        return FinishOperatorAction(TEXT("START"), false,
            TEXT("PAINT PROCESS IS FAULTED; START IS LOCKED"), OutReason);
    }
    if (Runtime->HasActiveWIP())
    {
        return FinishOperatorAction(TEXT("START"), false,
            TEXT("PAINT ALREADY OWNS ONE ACTIVE WIP; DUPLICATE START REJECTED"), OutReason);
    }

    FLBPaintShopExperimentalSaveState BeforeStart;
    FString CaptureReason;
    if (!Runtime->CaptureSaveState(BeforeStart, CaptureReason))
    {
        return FinishOperatorAction(TEXT("START"), false,
            CaptureReason.IsEmpty() ? TEXT("PAINT START PREFLIGHT COULD NOT CAPTURE STATE")
                                    : CaptureReason,
            OutReason);
    }

    DestroyOperatorWeldSource();
    ALBBodyWeldLineActor* Source = nullptr;
    FName BodyId = NAME_None;
    FName CarrierId = NAME_None;
    FString ManufactureReason;
    if (!BuildCanonicalWeldOutput(BeforeStart.NextWIPSerial,
        Source, BodyId, CarrierId, ManufactureReason))
    {
        return FinishOperatorAction(TEXT("START"), false, ManufactureReason, OutReason);
    }

    FString HandoffReason;
    if (!Runtime->AcceptAndAcknowledgeBodyInWhite(
        Source, BodyId, CarrierId, HandoffReason))
    {
        if (IsValid(Source) && !Source->IsActorBeingDestroyed()) Source->Destroy();
        return FinishOperatorAction(TEXT("START"), false,
            HandoffReason.IsEmpty()
                ? TEXT("CANONICAL WELD HANDOFF FAILED WITHOUT PAINT MUTATION")
                : HandoffReason,
            OutReason);
    }

    EnforceOperatorWeldSourceIsolation(Source);
    OperatorWeldSource = Source;
    return FinishOperatorAction(TEXT("START"), true,
        FString::Printf(TEXT("%s ACCEPTED FROM WELD ON %s"),
            *BodyId.ToString(), *CarrierId.ToString()),
        OutReason);
}

bool ALBPaintShopPrototypeGameMode::ToggleProcessPause(FString& OutReason)
{
    ALBPaintShopPrototypeRuntime* Runtime = ResolveOperatorRuntime(OutReason);
    if (!Runtime)
    {
        return FinishOperatorAction(TEXT("PAUSE"), false, OutReason, OutReason);
    }
    if (Runtime->IsProcessFaulted() || !Runtime->HasActiveWIP()
        || Runtime->GetPhase() == ELBPaintShopPrototypePhase::OutputReady)
    {
        return FinishOperatorAction(TEXT("PAUSE"), false,
            TEXT("PAUSE/RESUME REQUIRES ONE HEALTHY IN-FLIGHT PAINT WIP"), OutReason);
    }

    const bool bPause = !Runtime->IsPaused();
    Runtime->SetPaused(bPause);
    if (Runtime->IsPaused() != bPause)
    {
        return FinishOperatorAction(TEXT("PAUSE"), false,
            TEXT("PAINT RUNTIME REJECTED THE PAUSE/RESUME COMMAND"), OutReason);
    }
    return FinishOperatorAction(TEXT("PAUSE"), true,
        bPause ? TEXT("PAINT PROCESS PAUSED") : TEXT("PAINT PROCESS RESUMED"),
        OutReason);
}

bool ALBPaintShopPrototypeGameMode::ToggleOutputBlock(FString& OutReason)
{
    ALBPaintShopPrototypeRuntime* Runtime = ResolveOperatorRuntime(OutReason);
    if (!Runtime)
    {
        return FinishOperatorAction(TEXT("OUTPUT BLOCK"), false, OutReason, OutReason);
    }
    const bool bBlock = !Runtime->IsOutputBlocked();
    Runtime->SetOutputBlocked(bBlock);
    if (Runtime->IsOutputBlocked() != bBlock)
    {
        return FinishOperatorAction(TEXT("OUTPUT BLOCK"), false,
            TEXT("PAINT RUNTIME REJECTED THE OUTPUT BLOCK COMMAND"), OutReason);
    }
    return FinishOperatorAction(TEXT("OUTPUT BLOCK"), true,
        bBlock ? TEXT("PAINT OUTPUT BLOCKED") : TEXT("PAINT OUTPUT UNBLOCKED"),
        OutReason);
}

bool ALBPaintShopPrototypeGameMode::ReleasePaintOutput(FString& OutReason)
{
    ALBPaintShopPrototypeRuntime* Runtime = ResolveOperatorRuntime(OutReason);
    if (!Runtime)
    {
        return FinishOperatorAction(TEXT("RELEASE"), false, OutReason, OutReason);
    }
    FLBPaintShopWIPSaveState ReleasedWIP;
    FString ReleaseReason;
    if (!Runtime->ReleaseOutput(ReleasedWIP, ReleaseReason))
    {
        return FinishOperatorAction(TEXT("RELEASE"), false, ReleaseReason, OutReason);
    }
    DestroyOperatorWeldSource();
    return FinishOperatorAction(TEXT("RELEASE"), true,
        FString::Printf(TEXT("%s RELEASED AS ED-COATED OUTPUT"),
            *ReleasedWIP.UnitId.ToString()),
        OutReason);
}

bool ALBPaintShopPrototypeGameMode::SavePaintState(FString& OutReason)
{
    ALBPaintShopPrototypeRuntime* Runtime = ResolveOperatorRuntime(OutReason);
    if (!Runtime)
    {
        return FinishOperatorAction(TEXT("SAVE"), false, OutReason, OutReason);
    }
    FString SaveReason;
    const bool bSaved = Runtime->SaveToExperimentalSlot(SaveReason);
    return FinishOperatorAction(TEXT("SAVE"), bSaved, SaveReason, OutReason);
}

bool ALBPaintShopPrototypeGameMode::LoadPaintState(FString& OutReason)
{
    ALBPaintShopPrototypeRuntime* Runtime = ResolveOperatorRuntime(OutReason);
    if (!Runtime)
    {
        return FinishOperatorAction(TEXT("LOAD"), false, OutReason, OutReason);
    }
    FString LoadReason;
    const bool bLoaded = Runtime->LoadFromExperimentalSlot(LoadReason);
    if (bLoaded)
    {
        // The exact acknowledged BIW is now wholly owned by restored Paint WIP.
        // No synthetic Weld actor is reconstructed from save data.
        DestroyOperatorWeldSource();
    }
    return FinishOperatorAction(TEXT("LOAD"), bLoaded, LoadReason, OutReason);
}

#if WITH_DEV_AUTOMATION_TESTS
bool ALBPaintShopPrototypeGameMode::SavePaintStateToAutomationSlot(
    const FString& SlotName, FString& OutReason)
{
    ALBPaintShopPrototypeRuntime* Runtime = ResolveOperatorRuntime(OutReason);
    if (!Runtime)
    {
        return FinishOperatorAction(TEXT("SAVE"), false, OutReason, OutReason);
    }
    FString SaveReason;
    const bool bSaved = Runtime->SaveToAutomationSlot(SlotName, SaveReason);
    return FinishOperatorAction(TEXT("SAVE"), bSaved, SaveReason, OutReason);
}

bool ALBPaintShopPrototypeGameMode::LoadPaintStateFromAutomationSlot(
    const FString& SlotName, FString& OutReason)
{
    ALBPaintShopPrototypeRuntime* Runtime = ResolveOperatorRuntime(OutReason);
    if (!Runtime)
    {
        return FinishOperatorAction(TEXT("LOAD"), false, OutReason, OutReason);
    }
    FString LoadReason;
    const bool bLoaded = Runtime->LoadFromAutomationSlot(SlotName, LoadReason);
    if (bLoaded) DestroyOperatorWeldSource();
    return FinishOperatorAction(TEXT("LOAD"), bLoaded, LoadReason, OutReason);
}
#endif

bool ALBPaintShopPrototypeGameMode::BuildCanonicalWeldOutput(
    const int32 IdentitySerial, ALBBodyWeldLineActor*& OutSource,
    FName& OutBodyId, FName& OutCarrierId, FString& OutReason)
{
    OutSource = nullptr;
    OutBodyId = NAME_None;
    OutCarrierId = NAME_None;
    OutReason.Reset();
    UWorld* World = GetWorld();
    if (!World || IdentitySerial < 1)
    {
        OutReason = TEXT("CANONICAL WELD SOURCE REQUIRES A VALID WORLD AND IDENTITY SERIAL");
        return false;
    }

    const TArray<FName> Families = ALBBodyWeldLineActor::GetRequiredPanelFamilies();
    if (Families.Num() != 11)
    {
        OutReason = FString::Printf(
            TEXT("CANONICAL CAIRNWELL WELD RECIPE REQUIRES 11 PANEL FAMILIES; FOUND %d"),
            Families.Num());
        return false;
    }

    FActorSpawnParameters SpawnParameters;
    SpawnParameters.Owner = this;
    SpawnParameters.ObjectFlags |= RF_Transient;
    SpawnParameters.SpawnCollisionHandlingOverride =
        ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    const FTransform HiddenTransform(FRotator::ZeroRotator,
        FVector(0.0f, 0.0f, -100000.0f));
    OutSource = World->SpawnActor<ALBBodyWeldLineActor>(
        ALBBodyWeldLineActor::StaticClass(), HiddenTransform, SpawnParameters);
    if (!OutSource)
    {
        OutReason = TEXT("HIDDEN CANONICAL WELD SOURCE COULD NOT BE SPAWNED");
        return false;
    }
    OutSource->Tags.AddUnique(TEXT("LB.PaintShop.OperatorWeldSource.v001"));
    EnforceOperatorWeldSourceIsolation(OutSource);

    const auto Fail = [this, &OutSource, &OutReason](const FString& Detail)
    {
        OutReason = Detail.IsEmpty()
            ? TEXT("CANONICAL WELD MANUFACTURING FAILED") : Detail;
        if (IsValid(OutSource) && !OutSource->IsActorBeingDestroyed())
        {
            EnforceOperatorWeldSourceIsolation(OutSource);
            OutSource->Destroy();
        }
        OutSource = nullptr;
        return false;
    };

    const FName LineId(*FString::Printf(TEXT("WL-PAINT-PLAYER-%06d"), IdentitySerial));
    const FName OrderId(*FString::Printf(TEXT("ORDER-PAINT-PLAYER-%06d"), IdentitySerial));
    OutCarrierId = FName(*FString::Printf(
        TEXT("CARRIER-PAINT-PLAYER-%06d"), IdentitySerial));
    if (!OutSource->Configure(LineId) || !OutSource->SetAssignedOrder(OrderId))
    {
        return Fail(TEXT("HIDDEN WELD SOURCE COULD NOT CONFIGURE ITS CANONICAL ORDER"));
    }

    FLBBodyWeldQualityConditions Conditions;
    Conditions.bFixtureProgramCorrect = true;
    Conditions.bRobotCalibrationInTolerance = true;
    Conditions.bServiceConditionAcceptable = true;
    Conditions.bSafetyInterlockClear = true;
    OutSource->SetQualityConditions(Conditions);

    const FName VehicleId = ALBBodyWeldLineActor::GetVehicleModelId();
    FString WeldReason;
    for (int32 FamilyIndex = 0; FamilyIndex < Families.Num(); ++FamilyIndex)
    {
        const FName Family = Families[FamilyIndex];
        const int64 PanelSerial = static_cast<int64>(IdentitySerial - 1)
            * Families.Num() + FamilyIndex + 1;
        FLBBodyWeldStillageInventory Stillage;
        Stillage.StillageId = FName(*FString::Printf(
            TEXT("PAINT-PLAYER-STILLAGE-%s-%06lld"),
            *Family.ToString(), PanelSerial));
        Stillage.OrderId = OrderId;
        Stillage.VehicleModelId = VehicleId;
        Stillage.PanelTypeId = Family;
        Stillage.DeliverySequence = PanelSerial;
        Stillage.CapacityPanels = 1;
        FLBBodyWeldPanelUnit& Panel = Stillage.PanelUnits.AddDefaulted_GetRef();
        Panel.PanelId = FName(*FString::Printf(TEXT("PTR-PANEL-%s-%s-%06lld"),
            *VehicleId.ToString(), *Family.ToString(), PanelSerial));
        Panel.OrderId = OrderId;
        Panel.VehicleModelId = VehicleId;
        Panel.PanelTypeId = Family;
        Panel.StillageId = Stillage.StillageId;
        if (!OutSource->ReceivePanelStillage(Stillage, WeldReason))
        {
            return Fail(WeldReason);
        }
    }

    FLBBodyWeldBaseKitUnit BaseKit;
    BaseKit.KitId = FName(*FString::Printf(
        TEXT("PAINT-PLAYER-BASE-KIT-%06d"), IdentitySerial));
    BaseKit.KitTypeId = ALBBodyWeldLineActor::GetBaseKitTypeId();
    BaseKit.OrderId = OrderId;
    BaseKit.VehicleModelId = VehicleId;
    BaseKit.DeliverySequence = IdentitySerial;
    if (!OutSource->ReceiveBaseKit(BaseKit, WeldReason))
    {
        return Fail(WeldReason);
    }

    OutSource->SetEDAvailable(true);
    FLBBodyWeldInputReservation Reservation;
    if (!OutSource->TryReserveRecipe(WeldReason)
        || !OutSource->GetActiveReservation(Reservation) || !Reservation.bValid
        || !OutSource->CommitReservedInputs(WeldReason))
    {
        return Fail(WeldReason.IsEmpty()
            ? TEXT("CANONICAL WELD RECIPE COULD NOT BE RESERVED AND COMMITTED")
            : WeldReason);
    }
    OutSource->AdvanceSimulation(22.0f);

    FLBBodyInWhiteRecord OutputBody;
    if (!OutSource->GetOutputBody(OutputBody)
        || OutputBody.QualityState != ELBBodyWeldQualityState::Good
        || OutputBody.bEDAccepted || OutputBody.Panels.Num() != Families.Num()
        || !OutputBody.QualityEvidence.bRecipeComplete
        || !OutputBody.QualityEvidence.bFixtureProgramCorrect
        || !OutputBody.QualityEvidence.bSpotOperationsComplete
        || !OutputBody.QualityEvidence.bMIGOperationsComplete
        || !OutputBody.QualityEvidence.bRobotCalibrationInTolerance
        || !OutputBody.QualityEvidence.bServiceConditionAcceptable
        || !OutputBody.QualityEvidence.bSafetyInterlockClear
        || !OutputBody.QualityEvidence.ReasonCodes.IsEmpty()
        || !ALBBodyWeldLineActor::IsSaveStateContractValid(
            OutSource->CaptureSaveState()))
    {
        return Fail(TEXT("CANONICAL WELD SOURCE DID NOT PRODUCE EXACT GOOD BIW EVIDENCE"));
    }

    OutBodyId = OutputBody.BodyId;
    EnforceOperatorWeldSourceIsolation(OutSource);
    return true;
}

void ALBPaintShopPrototypeGameMode::EnforceOperatorWeldSourceIsolation(
    ALBBodyWeldLineActor* Source) const
{
    if (!IsValid(Source)) return;
    Source->SetActorHiddenInGame(true);
    Source->SetActorEnableCollision(false);
    Source->SetActorTickEnabled(false);
    Source->SetReplicates(false);
    Source->SetCanBeDamaged(false);
    TArray<UActorComponent*> Components;
    Source->GetComponents(Components);
    for (UActorComponent* Component : Components)
    {
        if (!IsValid(Component)) continue;
        Component->SetComponentTickEnabled(false);
        if (UPrimitiveComponent* Primitive = Cast<UPrimitiveComponent>(Component))
        {
            Primitive->SetCollisionEnabled(ECollisionEnabled::NoCollision);
            Primitive->SetGenerateOverlapEvents(false);
            Primitive->SetVisibility(false, true);
            Primitive->SetHiddenInGame(true, true);
        }
    }
}

void ALBPaintShopPrototypeGameMode::DestroyOperatorWeldSource()
{
    if (IsValid(OperatorWeldSource) && !OperatorWeldSource->IsActorBeingDestroyed())
    {
        OperatorWeldSource->Destroy();
    }
    OperatorWeldSource = nullptr;
}

bool ALBPaintShopPrototypeGameMode::FinishOperatorAction(
    const TCHAR* Action, const bool bSuccess, const FString& Detail,
    FString& OutReason)
{
    const FString StableDetail = Detail.IsEmpty()
        ? (bSuccess ? TEXT("COMMAND COMPLETED") : TEXT("COMMAND FAILED"))
        : Detail;
    OutReason = StableDetail;
    bLastOperatorActionSuccessful = bSuccess;
    LastOperatorActionStatus = FString::Printf(TEXT("OPERATOR %s: %s - %s"),
        Action ? Action : TEXT("COMMAND"), bSuccess ? TEXT("PASS") : TEXT("FAIL"),
        *StableDetail);
    if (bSuccess)
    {
        UE_LOG(LogTemp, Display,
            TEXT("LINE_BOSS_PAINT_SHOP_OPERATOR action=%s result=PASS detail=\"%s\""),
            Action ? Action : TEXT("COMMAND"), *StableDetail);
    }
    else
    {
        UE_LOG(LogTemp, Warning,
            TEXT("LINE_BOSS_PAINT_SHOP_OPERATOR action=%s result=FAIL detail=\"%s\""),
            Action ? Action : TEXT("COMMAND"), *StableDetail);
    }
    return bSuccess;
}
