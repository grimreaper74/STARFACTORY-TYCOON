#include "LBPaintShopManagementPawn.h"

#include "Camera/CameraComponent.h"
#include "Components/InputComponent.h"
#include "Components/SceneComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Controller.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "GameFramework/SpringArmComponent.h"
#include "LBPaintShopBuildAuthority.h"
#include "LBPaintShopCellActor.h"
#include "LBPaintShopPrototypeGameMode.h"
#include "LBPaintShopPrototypeRuntime.h"
#include "LBPaintShopPrototypeWorldBootstrap.h"
#include "InputCoreTypes.h"

namespace LBPaintShopManagementPawnPrivate
{
    constexpr float MinimumZoomDistanceCm = 1400.0f;
    constexpr float MaximumZoomDistanceCm = 9000.0f;
    constexpr float DefaultZoomDistanceCm = 2700.0f;
    constexpr float DefaultPitchDegrees = -32.0f;
    constexpr float DefaultYawDegrees = 45.0f;
    constexpr float DefaultFieldOfViewDegrees = 55.0f;
    constexpr float MinimumPitchDegrees = -80.0f;
    constexpr float MaximumPitchDegrees = -10.0f;
    constexpr float OrbitYawRateDegreesPerSecond = 90.0f;
    constexpr float OrbitPitchRateDegreesPerSecond = 70.0f;
    constexpr float ZoomRateCmPerSecond = 3600.0f;
    const FVector ApprovedCellDimensionsCm(1800.0f, 1000.0f, 853.0f);
    const FVector ApprovedCellLocalFocus(0.0f, 0.0f, 426.5f);

    float GetBoundedInputDeltaSeconds(const UWorld* World)
    {
        return World ? FMath::Clamp(World->GetDeltaSeconds(), 1.0f / 240.0f, 0.05f)
            : 1.0f / 60.0f;
    }
}

ALBPaintShopManagementPawn::ALBPaintShopManagementPawn()
{
    PrimaryActorTick.bCanEverTick = false;

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PaintPrototypeCameraRoot"));
    SetRootComponent(SceneRoot);

    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("PaintPrototypeCameraBoom"));
    CameraBoom->SetupAttachment(SceneRoot);
    CameraBoom->TargetArmLength = LBPaintShopManagementPawnPrivate::DefaultZoomDistanceCm;
    CameraBoom->SetRelativeRotation(FRotator(
        LBPaintShopManagementPawnPrivate::DefaultPitchDegrees,
        LBPaintShopManagementPawnPrivate::DefaultYawDegrees, 0.0f));
    CameraBoom->bDoCollisionTest = false;
    CameraBoom->bUsePawnControlRotation = true;

    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("PaintPrototypeCamera"));
    Camera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    Camera->bUsePawnControlRotation = false;
    Camera->FieldOfView = LBPaintShopManagementPawnPrivate::DefaultFieldOfViewDegrees;

    CameraMovement = CreateDefaultSubobject<UFloatingPawnMovement>(
        TEXT("PaintPrototypeCameraMovement"));
    CameraMovement->UpdatedComponent = SceneRoot;
    CameraMovement->MaxSpeed = 2600.0f;
    CameraMovement->Acceleration = 8000.0f;
    CameraMovement->Deceleration = 11000.0f;

    bUseControllerRotationYaw = false;
    bUseControllerRotationPitch = false;
    bUseControllerRotationRoll = false;
}

void ALBPaintShopManagementPawn::BeginPlay()
{
    Super::BeginPlay();
    if (!FocusEDCoatCellFromWorld())
    {
        UE_LOG(LogTemp, Warning,
            TEXT("LINE_BOSS_PAINT_SHOP_CAMERA waiting_for_exact_ready_bootstrap"));
    }
}

void ALBPaintShopManagementPawn::SetupPlayerInputComponent(
    UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    if (!PlayerInputComponent) return;

    // Read-only consumers of the existing generic management-camera mappings.
    PlayerInputComponent->BindAxis(TEXT("LB_MoveForward"), this,
        &ALBPaintShopManagementPawn::PanForward);
    PlayerInputComponent->BindAxis(TEXT("LB_MoveRight"), this,
        &ALBPaintShopManagementPawn::PanRight);
    PlayerInputComponent->BindAxis(TEXT("LB_ControlRoomLookYaw"), this,
        &ALBPaintShopManagementPawn::OrbitYaw);
    PlayerInputComponent->BindAxis(TEXT("LB_ControlRoomLookPitch"), this,
        &ALBPaintShopManagementPawn::OrbitPitch);
    PlayerInputComponent->BindAxis(TEXT("LB_Zoom"), this,
        &ALBPaintShopManagementPawn::SetPrototypeZoomInput);
    PlayerInputComponent->BindAction(TEXT("LB_CameraReset"), IE_Pressed, this,
        &ALBPaintShopManagementPawn::HandleCameraReset);

    // Explicit raw keys keep the isolated Paint slice deterministic without
    // changing shared Config. Every handler delegates to GameMode authority.
    PlayerInputComponent->BindKey(EKeys::SpaceBar, IE_Pressed, this,
        &ALBPaintShopManagementPawn::HandleStartCanonicalWeldHandoff);
    PlayerInputComponent->BindKey(EKeys::P, IE_Pressed, this,
        &ALBPaintShopManagementPawn::HandleToggleProcessPause);
    PlayerInputComponent->BindKey(EKeys::O, IE_Pressed, this,
        &ALBPaintShopManagementPawn::HandleToggleOutputBlock);
    PlayerInputComponent->BindKey(EKeys::R, IE_Pressed, this,
        &ALBPaintShopManagementPawn::HandleReleasePaintOutput);
    PlayerInputComponent->BindKey(EKeys::F5, IE_Pressed, this,
        &ALBPaintShopManagementPawn::HandleSavePaintState);
    PlayerInputComponent->BindKey(EKeys::F9, IE_Pressed, this,
        &ALBPaintShopManagementPawn::HandleLoadPaintState);
}

bool ALBPaintShopManagementPawn::FocusEDCoatCell(
    ALBPaintShopPrototypeWorldBootstrap* Bootstrap)
{
    CameraStatus = TEXT("READY BOOTSTRAP OR ED-COAT CELL IS MISSING");
    if (!IsValid(Bootstrap) || Bootstrap->IsActorBeingDestroyed() || !Bootstrap->IsReady())
    {
        return false;
    }

    UWorld* World = GetWorld();
    if (!World || Bootstrap->GetWorld() != World)
    {
        CameraStatus = TEXT("PAINT BOOTSTRAP BELONGS TO A DIFFERENT WORLD");
        return false;
    }

    int32 BootstrapCount = 0;
    int32 AuthorityCount = 0;
    int32 RuntimeCount = 0;
    for (TActorIterator<ALBPaintShopPrototypeWorldBootstrap> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++BootstrapCount;
    }
    for (TActorIterator<ALBPaintShopBuildAuthority> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++AuthorityCount;
    }
    for (TActorIterator<ALBPaintShopPrototypeRuntime> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++RuntimeCount;
    }
    if (BootstrapCount != 1 || AuthorityCount != 1 || RuntimeCount != 1)
    {
        CameraStatus = FString::Printf(
            TEXT("PAINT CARDINALITY INVALID: BOOTSTRAP %d, AUTHORITY %d, RUNTIME %d"),
            BootstrapCount, AuthorityCount, RuntimeCount);
        return false;
    }

    ALBPaintShopBuildAuthority* Authority = Bootstrap->GetBuildAuthority();
    ALBPaintShopPrototypeRuntime* Runtime = Bootstrap->GetRuntime();
    ALBPaintShopCellActor* Cell = Runtime ? Runtime->GetEDCoatCell() : nullptr;
    const FLBPaintShopApprovedEDCoatLayoutItem Approved =
        ALBPaintShopBuildAuthority::GetApprovedEDCoatDipLayout();
    FString PlacementReason;
    if (!IsValid(Authority) || !IsValid(Runtime) || !Runtime->IsInitialized()
        || Runtime->GetBuildAuthority() != Authority || !IsValid(Cell)
        || Authority->GetOwner() != Bootstrap || Runtime->GetOwner() != Bootstrap
        || Cell->GetOwner() != Authority || Authority->FindCell(Approved.CellId) != Cell
        || Cell->GetCellId() != Approved.CellId
        || Cell->GetDefinitionId() != Approved.DefinitionId
        || !Cell->GetActorTransform().Equals(Approved.WorldTransform, 0.01f)
        || !Authority->ValidateApprovedCellPlacement(
            Cell->GetDefinitionId(), Cell->GetActorTransform(), PlacementReason))
    {
        return false;
    }

    PrototypeBootstrap = Bootstrap;
    ApplyFocusContract(BuildEDCoatFocusContract(Cell->GetActorTransform()));
    CameraStatus = TEXT("FOCUSED ON 1800 X 1000 CM ED-COAT CELL");
    return true;
}

bool ALBPaintShopManagementPawn::FocusEDCoatCellFromWorld()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        CameraStatus = TEXT("PAINT SHOP WORLD IS UNAVAILABLE");
        return false;
    }

    int32 BootstrapCount = 0;
    ALBPaintShopPrototypeWorldBootstrap* OnlyBootstrap = nullptr;
    for (TActorIterator<ALBPaintShopPrototypeWorldBootstrap> It(World); It; ++It)
    {
        if (!IsValid(*It) || It->IsActorBeingDestroyed()) continue;
        ++BootstrapCount;
        OnlyBootstrap = *It;
    }
    if (BootstrapCount != 1)
    {
        CameraStatus = FString::Printf(
            TEXT("EXPECTED ONE PAINT BOOTSTRAP; FOUND %d"), BootstrapCount);
        return false;
    }
    return FocusEDCoatCell(OnlyBootstrap);
}

void ALBPaintShopManagementPawn::SetPrototypeZoomInput(const float Value)
{
    if (FMath::IsNearlyZero(Value) || !CameraBoom) return;
    const float DeltaSeconds =
        LBPaintShopManagementPawnPrivate::GetBoundedInputDeltaSeconds(GetWorld());
    CameraBoom->TargetArmLength = ClampPrototypeZoomDistance(
        CameraBoom->TargetArmLength - Value
            * LBPaintShopManagementPawnPrivate::ZoomRateCmPerSecond * DeltaSeconds);
}

float ALBPaintShopManagementPawn::GetPrototypeZoomDistance() const
{
    return CameraBoom ? CameraBoom->TargetArmLength : 0.0f;
}

bool ALBPaintShopManagementPawn::IsBoundToPrototypeBootstrap(
    ALBPaintShopPrototypeWorldBootstrap* InBootstrap) const
{
    return IsValid(InBootstrap) && InBootstrap->GetWorld() == GetWorld()
        && PrototypeBootstrap.Get() == InBootstrap;
}

float ALBPaintShopManagementPawn::ClampPrototypeZoomDistance(const float InDistanceCm)
{
    return FMath::Clamp(InDistanceCm,
        LBPaintShopManagementPawnPrivate::MinimumZoomDistanceCm,
        LBPaintShopManagementPawnPrivate::MaximumZoomDistanceCm);
}

FLBPaintShopCameraFocusContract ALBPaintShopManagementPawn::BuildEDCoatFocusContract(
    const FTransform& CellWorldTransform)
{
    const FTransform SafeTransform = CellWorldTransform.IsValid()
        && !CellWorldTransform.ContainsNaN()
        ? CellWorldTransform : FTransform::Identity;
    FLBPaintShopCameraFocusContract Result;
    Result.Target = SafeTransform.TransformPosition(
        LBPaintShopManagementPawnPrivate::ApprovedCellLocalFocus);
    Result.ZoomDistanceCm = LBPaintShopManagementPawnPrivate::DefaultZoomDistanceCm;
    Result.Rotation = FRotator(
        LBPaintShopManagementPawnPrivate::DefaultPitchDegrees,
        LBPaintShopManagementPawnPrivate::DefaultYawDegrees, 0.0f);
    Result.FieldOfViewDegrees =
        LBPaintShopManagementPawnPrivate::DefaultFieldOfViewDegrees;
    Result.CellDimensionsCm =
        LBPaintShopManagementPawnPrivate::ApprovedCellDimensionsCm;
    return Result;
}

void ALBPaintShopManagementPawn::PanForward(const float Value)
{
    if (FMath::IsNearlyZero(Value) || !Controller) return;
    const FRotator YawRotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X), Value);
}

void ALBPaintShopManagementPawn::PanRight(const float Value)
{
    if (FMath::IsNearlyZero(Value) || !Controller) return;
    const FRotator YawRotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y), Value);
}

void ALBPaintShopManagementPawn::OrbitYaw(const float Value)
{
    if (FMath::IsNearlyZero(Value) || !Controller) return;
    const float DeltaSeconds =
        LBPaintShopManagementPawnPrivate::GetBoundedInputDeltaSeconds(GetWorld());
    FRotator Rotation = Controller->GetControlRotation();
    Rotation.Yaw = FRotator::NormalizeAxis(Rotation.Yaw + Value
        * LBPaintShopManagementPawnPrivate::OrbitYawRateDegreesPerSecond * DeltaSeconds);
    Rotation.Roll = 0.0f;
    Controller->SetControlRotation(Rotation);
}

void ALBPaintShopManagementPawn::OrbitPitch(const float Value)
{
    if (FMath::IsNearlyZero(Value) || !Controller) return;
    const float DeltaSeconds =
        LBPaintShopManagementPawnPrivate::GetBoundedInputDeltaSeconds(GetWorld());
    FRotator Rotation = Controller->GetControlRotation();
    Rotation.Pitch = FMath::Clamp(FRotator::NormalizeAxis(Rotation.Pitch + Value
        * LBPaintShopManagementPawnPrivate::OrbitPitchRateDegreesPerSecond * DeltaSeconds),
        LBPaintShopManagementPawnPrivate::MinimumPitchDegrees,
        LBPaintShopManagementPawnPrivate::MaximumPitchDegrees);
    Rotation.Roll = 0.0f;
    Controller->SetControlRotation(Rotation);
}

void ALBPaintShopManagementPawn::HandleCameraReset()
{
    FocusEDCoatCellFromWorld();
}

void ALBPaintShopManagementPawn::HandleStartCanonicalWeldHandoff()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
    {
        Mode->StartCanonicalWeldHandoff(Reason);
    }
}

void ALBPaintShopManagementPawn::HandleToggleProcessPause()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
    {
        Mode->ToggleProcessPause(Reason);
    }
}

void ALBPaintShopManagementPawn::HandleToggleOutputBlock()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
    {
        Mode->ToggleOutputBlock(Reason);
    }
}

void ALBPaintShopManagementPawn::HandleReleasePaintOutput()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
    {
        Mode->ReleasePaintOutput(Reason);
    }
}

void ALBPaintShopManagementPawn::HandleSavePaintState()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
    {
        Mode->SavePaintState(Reason);
    }
}

void ALBPaintShopManagementPawn::HandleLoadPaintState()
{
    FString Reason;
    if (ALBPaintShopPrototypeGameMode* Mode = ResolveOperatorGameMode())
    {
        Mode->LoadPaintState(Reason);
    }
}

ALBPaintShopPrototypeGameMode* ALBPaintShopManagementPawn::ResolveOperatorGameMode() const
{
    return GetWorld() ? GetWorld()->GetAuthGameMode<ALBPaintShopPrototypeGameMode>()
                      : nullptr;
}

void ALBPaintShopManagementPawn::ApplyFocusContract(
    const FLBPaintShopCameraFocusContract& Contract)
{
    SetActorLocation(Contract.Target, false, nullptr, ETeleportType::TeleportPhysics);
    if (CameraBoom)
    {
        CameraBoom->TargetArmLength = ClampPrototypeZoomDistance(
            Contract.ZoomDistanceCm);
        CameraBoom->SetRelativeRotation(Contract.Rotation);
    }
    if (Camera) Camera->FieldOfView = Contract.FieldOfViewDegrees;
    if (Controller) Controller->SetControlRotation(Contract.Rotation);
}
