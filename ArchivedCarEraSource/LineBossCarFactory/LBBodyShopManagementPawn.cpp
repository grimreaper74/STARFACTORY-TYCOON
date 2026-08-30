#include "LBBodyShopManagementPawn.h"

#include "Camera/CameraComponent.h"
#include "Components/InputComponent.h"
#include "Components/SceneComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Controller.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "GameFramework/SpringArmComponent.h"
#include "LBBodyShopBuildAuthority.h"
#include "LBBodyShopCellActor.h"
#include "LBBodyShopPrototypeRuntime.h"
#include "LBBodyShopPrototypeWorldBootstrap.h"

namespace LBBodyShopManagementPawnPrivate
{
    constexpr float MinimumZoomDistanceCm = 1800.0f;
    constexpr float MaximumZoomDistanceCm = 16000.0f;
    constexpr float ReleaseComparisonZoomDistanceCm = 3400.0f;
    constexpr float ReleaseComparisonPitchDegrees = -30.0f;
    constexpr float ReleaseComparisonYawDegrees = 55.0f;
    constexpr float ReleaseComparisonFieldOfViewDegrees = 60.0f;
    constexpr float HorizontalFramingMarginCm = 400.0f;
    constexpr float HorizontalSpanToDistanceScale = 0.55f;
    constexpr float HorizontalFramingSnapCm = 100.0f;
    constexpr float UpstreamCompositionBiasCm = -100.0f;
    constexpr float MinimumProcessFocusHeightCm = 180.0f;

    bool TryBuildCellFootprintBounds(const ALBBodyShopCellActor* Cell, FBox& OutBounds)
    {
        if (!IsValid(Cell) || Cell->IsActorBeingDestroyed()) return false;

        const FVector Footprint = Cell->GetDefinition().FootprintCm;
        if (Footprint.ContainsNaN() || Footprint.X <= 0.0f || Footprint.Y <= 0.0f
            || Footprint.Z <= 0.0f)
        {
            return false;
        }

        const FVector HalfExtent = Footprint * 0.5f;
        OutBounds = FBox(-HalfExtent, HalfExtent).TransformBy(Cell->GetActorTransform());
        return OutBounds.IsValid != 0 && !OutBounds.Min.ContainsNaN()
            && !OutBounds.Max.ContainsNaN();
    }
}

ALBBodyShopManagementPawn::ALBBodyShopManagementPawn()
{
    PrimaryActorTick.bCanEverTick = false;
    AutoPossessPlayer = EAutoReceiveInput::Player0;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PrototypeCameraRoot"));
    SetRootComponent(SceneRoot);

    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("PrototypeCameraBoom"));
    CameraBoom->SetupAttachment(SceneRoot);
    CameraBoom->TargetArmLength = InitialZoomDistanceCm;
    CameraBoom->SetRelativeRotation(FRotator(
        LBBodyShopManagementPawnPrivate::ReleaseComparisonPitchDegrees,
        LBBodyShopManagementPawnPrivate::ReleaseComparisonYawDegrees, 0.0f));
    CameraBoom->bDoCollisionTest = false;
    CameraBoom->bUsePawnControlRotation = true;

    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("PrototypeCamera"));
    Camera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    Camera->bUsePawnControlRotation = false;
    Camera->FieldOfView = LBBodyShopManagementPawnPrivate::ReleaseComparisonFieldOfViewDegrees;

    CameraMovement = CreateDefaultSubobject<UFloatingPawnMovement>(TEXT("PrototypeCameraMovement"));
    CameraMovement->UpdatedComponent = SceneRoot;
    CameraMovement->MaxSpeed = 3800.0f;
    CameraMovement->Acceleration = 10000.0f;
    CameraMovement->Deceleration = 14000.0f;

    // The boom follows controller rotation directly. Keeping the root level
    // avoids applying pitch/yaw twice through the pawn and the spring arm.
    bUseControllerRotationYaw = false;
    bUseControllerRotationPitch = false;
    bUseControllerRotationRoll = false;
}

void ALBBodyShopManagementPawn::BeginPlay()
{
    Super::BeginPlay();
    PrototypeBootstrap = FindPrototypeBootstrap();
    if (PrototypeBootstrap.IsValid())
    {
        PrototypeBuildOrigin = PrototypeBootstrap->GetPrototypeBuildOrigin();
        FocusPrototypeProcess();
    }
    else
    {
        UE_LOG(LogTemp, Warning,
            TEXT("LINE_BOSS_BODY_SHOP_PROTOTYPE_CAMERA bootstrap_missing; retaining map spawn"));
    }
    if (Controller)
    {
        Controller->SetControlRotation(FRotator(
            LBBodyShopManagementPawnPrivate::ReleaseComparisonPitchDegrees,
            LBBodyShopManagementPawnPrivate::ReleaseComparisonYawDegrees, 0.0f));
    }
}

void ALBBodyShopManagementPawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    if (!PlayerInputComponent) return;

    // Existing generic camera mappings are read-only consumers here; this prototype
    // does not add or mutate project input configuration.
    PlayerInputComponent->BindAxis(TEXT("LB_MoveForward"), this,
        &ALBBodyShopManagementPawn::MoveForward);
    PlayerInputComponent->BindAxis(TEXT("LB_MoveRight"), this,
        &ALBBodyShopManagementPawn::MoveRight);
    PlayerInputComponent->BindAxis(TEXT("LB_ControlRoomLookYaw"), this,
        &ALBBodyShopManagementPawn::LookYaw);
    PlayerInputComponent->BindAxis(TEXT("LB_ControlRoomLookPitch"), this,
        &ALBBodyShopManagementPawn::LookPitch);
    PlayerInputComponent->BindAxis(TEXT("LB_Zoom"), this,
        &ALBBodyShopManagementPawn::SetPrototypeZoomInput);
    PlayerInputComponent->BindAction(TEXT("LB_CameraReset"), IE_Pressed, this,
        &ALBBodyShopManagementPawn::HandleCameraReset);
    PlayerInputComponent->BindAction(TEXT("LB_BodyShopStartPause"), IE_Pressed, this,
        &ALBBodyShopManagementPawn::HandlePrototypeStartPause);
    PlayerInputComponent->BindAction(TEXT("LB_BodyShopSave"), IE_Pressed, this,
        &ALBBodyShopManagementPawn::HandlePrototypeSave);
    PlayerInputComponent->BindAction(TEXT("LB_BodyShopLoad"), IE_Pressed, this,
        &ALBBodyShopManagementPawn::HandlePrototypeLoad);
    PlayerInputComponent->BindAction(TEXT("LB_BodyShopClearHeld"), IE_Pressed, this,
        &ALBBodyShopManagementPawn::HandlePrototypeClearHeld);
    PlayerInputComponent->BindAction(TEXT("LB_BodyShopRobotSlots"), IE_Pressed, this,
        &ALBBodyShopManagementPawn::ToggleRobotSlotOverlay);
}

bool ALBBodyShopManagementPawn::FocusPrototypeBuildOrigin()
{
    if (ALBBodyShopPrototypeWorldBootstrap* Bootstrap = FindPrototypeBootstrap())
    {
        PrototypeBootstrap = Bootstrap;
        PrototypeBuildOrigin = Bootstrap->GetPrototypeBuildOrigin();
    }

    ApplyFocusContract(BuildFocusContract(FBox(EForceInit::ForceInit), PrototypeBuildOrigin));
    return !PrototypeBuildOrigin.ContainsNaN();
}

bool ALBBodyShopManagementPawn::FocusPrototypeProcess()
{
    ALBBodyShopPrototypeWorldBootstrap* Bootstrap = FindPrototypeBootstrap();
    if (Bootstrap)
    {
        PrototypeBootstrap = Bootstrap;
        PrototypeBuildOrigin = Bootstrap->GetPrototypeBuildOrigin();
    }

    FBox CommissionedBounds(EForceInit::ForceInit);
    FBox PlacedBounds(EForceInit::ForceInit);
    if (Bootstrap)
    {
        if (const ALBBodyShopBuildAuthority* BuildAuthority =
            Cast<ALBBodyShopBuildAuthority>(Bootstrap->GetBuildAuthorityActor()))
        {
            for (const ALBBodyShopCellActor* Cell : BuildAuthority->GetPlacedCells())
            {
                FBox CellBounds(EForceInit::ForceInit);
                if (!LBBodyShopManagementPawnPrivate::TryBuildCellFootprintBounds(
                    Cell, CellBounds))
                {
                    continue;
                }
                PlacedBounds += CellBounds;
                if (Cell->IsCommissioned()) CommissionedBounds += CellBounds;
            }
        }
    }

    const FBox& SelectedBounds = CommissionedBounds.IsValid
        ? CommissionedBounds : PlacedBounds;
    const FLBBodyShopCameraFocusContract Contract =
        BuildFocusContract(SelectedBounds, PrototypeBuildOrigin);
    ApplyFocusContract(Contract);
    return Contract.bUsedProcessBounds;
}

void ALBBodyShopManagementPawn::SetPrototypeZoomInput(const float Value)
{
    if (FMath::IsNearlyZero(Value) || !CameraBoom) return;
    CameraBoom->TargetArmLength = ClampPrototypeZoomDistance(
        CameraBoom->TargetArmLength - Value * 520.0f);
}

void ALBBodyShopManagementPawn::SetRobotSlotOverlayRequested(const bool bVisible)
{
    bRobotSlotOverlayRequested = bVisible;
    UWorld* World = GetWorld();
    if (!World) return;

    for (TActorIterator<ALBBodyShopCellActor> It(World); It; ++It)
    {
        if (IsValid(*It)) It->SetRobotConfigurationOverlayVisible(bVisible);
    }
}

void ALBBodyShopManagementPawn::ToggleRobotSlotOverlay()
{
    SetRobotSlotOverlayRequested(!bRobotSlotOverlayRequested);
}

float ALBBodyShopManagementPawn::GetPrototypeZoomDistance() const
{
    return CameraBoom ? CameraBoom->TargetArmLength : 0.0f;
}

float ALBBodyShopManagementPawn::ClampPrototypeZoomDistance(const float InDistanceCm)
{
    return FMath::Clamp(InDistanceCm,
        LBBodyShopManagementPawnPrivate::MinimumZoomDistanceCm,
        LBBodyShopManagementPawnPrivate::MaximumZoomDistanceCm);
}

FLBBodyShopCameraFocusContract ALBBodyShopManagementPawn::BuildFocusContract(
    const FBox& ProcessBounds, const FVector& FallbackBuildOrigin)
{
    FLBBodyShopCameraFocusContract Result;
    Result.Target = FallbackBuildOrigin.ContainsNaN()
        ? FVector::ZeroVector : FallbackBuildOrigin;
    Result.ZoomDistanceCm = LBBodyShopManagementPawnPrivate::ReleaseComparisonZoomDistanceCm;
    Result.Rotation = FRotator(
        LBBodyShopManagementPawnPrivate::ReleaseComparisonPitchDegrees,
        LBBodyShopManagementPawnPrivate::ReleaseComparisonYawDegrees, 0.0f);
    Result.FieldOfViewDegrees =
        LBBodyShopManagementPawnPrivate::ReleaseComparisonFieldOfViewDegrees;

    if (!ProcessBounds.IsValid || ProcessBounds.Min.ContainsNaN()
        || ProcessBounds.Max.ContainsNaN())
    {
        return Result;
    }

    const FVector BoundsSize = ProcessBounds.GetSize();
    if (BoundsSize.X < 0.0f || BoundsSize.Y < 0.0f || BoundsSize.ContainsNaN())
    {
        return Result;
    }

    Result.Target = ProcessBounds.GetCenter();
    Result.Target.X += LBBodyShopManagementPawnPrivate::UpstreamCompositionBiasCm;
    Result.Target.Z = FMath::Max(Result.Target.Z,
        LBBodyShopManagementPawnPrivate::MinimumProcessFocusHeightCm);

    const float HorizontalSpanCm = FMath::Max(BoundsSize.X, BoundsSize.Y);
    const float FramedDistanceCm = FMath::GridSnap(
        HorizontalSpanCm * LBBodyShopManagementPawnPrivate::HorizontalSpanToDistanceScale
            + LBBodyShopManagementPawnPrivate::HorizontalFramingMarginCm,
        LBBodyShopManagementPawnPrivate::HorizontalFramingSnapCm);
    Result.ZoomDistanceCm = ClampPrototypeZoomDistance(FramedDistanceCm);
    Result.bUsedProcessBounds = true;
    return Result;
}

void ALBBodyShopManagementPawn::MoveForward(const float Value)
{
    if (FMath::IsNearlyZero(Value) || !Controller) return;
    const FRotator YawRotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X), Value);
}

void ALBBodyShopManagementPawn::MoveRight(const float Value)
{
    if (FMath::IsNearlyZero(Value) || !Controller) return;
    const FRotator YawRotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y), Value);
}

void ALBBodyShopManagementPawn::LookYaw(const float Value)
{
    AddControllerYawInput(Value);
}

void ALBBodyShopManagementPawn::LookPitch(const float Value)
{
    AddControllerPitchInput(Value);
}

void ALBBodyShopManagementPawn::HandleCameraReset()
{
    FocusPrototypeProcess();
}

void ALBBodyShopManagementPawn::HandlePrototypeStartPause()
{
    ALBBodyShopPrototypeRuntime* Runtime = FindPrototypeRuntime();
    if (!Runtime)
    {
        LastPrototypeActionStatus = TEXT("Body Shop runtime is unavailable");
        return;
    }
    FString Reason;
    bool bSuccess = false;
    if (Runtime->IsSimulationRunning())
        bSuccess = Runtime->SetSimulationRunning(false, Reason);
    else if (Runtime->GetActivePilotWIPCount() > 0)
        bSuccess = Runtime->SetSimulationRunning(true, Reason);
    else
        bSuccess = Runtime->StartPilotCycle(Reason);
    LastPrototypeActionStatus = Reason;
    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_BODY_SHOP_PLAYER_ACTION action=start_pause success=%s detail=\"%s\""),
        bSuccess ? TEXT("true") : TEXT("false"), *Reason);
}

void ALBBodyShopManagementPawn::HandlePrototypeSave()
{
    ALBBodyShopPrototypeRuntime* Runtime = FindPrototypeRuntime();
    FString Reason = TEXT("Body Shop runtime is unavailable");
    const bool bSuccess = Runtime && Runtime->SaveToExperimentalSlot(Reason);
    LastPrototypeActionStatus = Reason;
    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_BODY_SHOP_PLAYER_ACTION action=save success=%s detail=\"%s\""),
        bSuccess ? TEXT("true") : TEXT("false"), *Reason);
}

void ALBBodyShopManagementPawn::HandlePrototypeLoad()
{
    ALBBodyShopPrototypeRuntime* Runtime = FindPrototypeRuntime();
    FString Reason = TEXT("Body Shop runtime is unavailable");
    const bool bSuccess = Runtime && Runtime->LoadFromExperimentalSlot(Reason);
    LastPrototypeActionStatus = Reason;
    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_BODY_SHOP_PLAYER_ACTION action=load success=%s detail=\"%s\""),
        bSuccess ? TEXT("true") : TEXT("false"), *Reason);
}

void ALBBodyShopManagementPawn::HandlePrototypeClearHeld()
{
    ALBBodyShopPrototypeRuntime* Runtime = FindPrototypeRuntime();
    FString Reason = TEXT("Body Shop runtime is unavailable");
    const bool bSuccess = Runtime && Runtime->ReleaseHeldPilotUnit(Reason);
    LastPrototypeActionStatus = Reason;
    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_BODY_SHOP_PLAYER_ACTION action=clear_held success=%s detail=\"%s\""),
        bSuccess ? TEXT("true") : TEXT("false"), *Reason);
}

void ALBBodyShopManagementPawn::ApplyFocusContract(
    const FLBBodyShopCameraFocusContract& Contract)
{
    SetActorLocation(Contract.Target, false, nullptr, ETeleportType::TeleportPhysics);
    if (CameraBoom)
    {
        CameraBoom->TargetArmLength = ClampPrototypeZoomDistance(Contract.ZoomDistanceCm);
        CameraBoom->SetRelativeRotation(Contract.Rotation);
    }
    if (Camera) Camera->FieldOfView = Contract.FieldOfViewDegrees;
    if (Controller) Controller->SetControlRotation(Contract.Rotation);
}

ALBBodyShopPrototypeWorldBootstrap* ALBBodyShopManagementPawn::FindPrototypeBootstrap() const
{
    if (PrototypeBootstrap.IsValid()) return PrototypeBootstrap.Get();
    UWorld* World = GetWorld();
    if (!World) return nullptr;
    for (TActorIterator<ALBBodyShopPrototypeWorldBootstrap> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) return *It;
    }
    return nullptr;
}

ALBBodyShopPrototypeRuntime* ALBBodyShopManagementPawn::FindPrototypeRuntime() const
{
    ALBBodyShopPrototypeWorldBootstrap* Bootstrap = FindPrototypeBootstrap();
    return Bootstrap ? Cast<ALBBodyShopPrototypeRuntime>(Bootstrap->GetRuntimeActor()) : nullptr;
}
