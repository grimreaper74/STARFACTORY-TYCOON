#include "LBControlRoomPawn.h"

#include "Camera/CameraComponent.h"
#include "CollisionQueryParams.h"
#include "Components/CapsuleComponent.h"
#include "Components/InputComponent.h"
#include "Components/WidgetInteractionComponent.h"
#include "EngineUtils.h"
#include "Engine/Engine.h"
#include "Engine/CollisionProfile.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/FloatingPawnMovement.h"
#include "InputCoreTypes.h"
#include "HAL/FileManager.h"
#include "LBControlRoomCCTVFeed.h"
#include "LBControlRoomHUD.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBControlRoomPR004Console.h"
#include "LBManagementPawn.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPR004Station.h"
#include "Misc/Paths.h"
#include "UnrealClient.h"

ALBControlRoomPawn::ALBControlRoomPawn()
{
    PrimaryActorTick.bCanEverTick = true;

    OperatorCollision = CreateDefaultSubobject<UCapsuleComponent>(TEXT("OperatorCollision"));
    OperatorCollision->InitCapsuleSize(34.0f, 88.0f);
    OperatorCollision->SetCollisionProfileName(UCollisionProfile::Pawn_ProfileName);
    OperatorCollision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetRootComponent(OperatorCollision);

    SeatRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SeatRoot"));
    SeatRoot->SetupAttachment(OperatorCollision);
    SeatRoot->SetRelativeLocation(FVector(0.0f, 0.0f, StandingCameraHeightCm));

    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("SeatedOperatorCamera"));
    Camera->SetupAttachment(SeatRoot);
    Camera->FieldOfView = 112.0f;
    Camera->bUsePawnControlRotation = true;

    WidgetInteraction = CreateDefaultSubobject<UWidgetInteractionComponent>(TEXT("ControlRoomWidgetInteraction"));
    WidgetInteraction->SetupAttachment(Camera);
    WidgetInteraction->InteractionSource = EWidgetInteractionSource::Mouse;
    WidgetInteraction->InteractionDistance = 900.0f;

    WalkingMovement = CreateDefaultSubobject<UFloatingPawnMovement>(TEXT("WalkingMovement"));
    WalkingMovement->UpdatedComponent = OperatorCollision;
    WalkingMovement->MaxSpeed = 300.0f;
    WalkingMovement->Acceleration = 1200.0f;
    WalkingMovement->Deceleration = 1600.0f;

    AutoPossessPlayer = EAutoReceiveInput::Player0;
    bUseControllerRotationYaw = true;
    bUseControllerRotationPitch = true;
}

void ALBControlRoomPawn::BeginPlay()
{
    Super::BeginPlay();

    // A default pawn spawned without a PlayerStart arrives at the world origin.
    // For the standing operator that transform describes the capsule centre, not
    // its feet, so Z=0 embeds half the pawn in a floor at Z=0 and blocks WASD.
    // Resolve the initial standing pose against the first static surface below
    // the spawn point before locking the operator's permitted walking area.
    if (bStanding && OperatorCollision && GetWorld())
    {
        const float CapsuleHalfHeight = OperatorCollision->GetScaledCapsuleHalfHeight();
        const FVector InitialLocation = GetActorLocation();
        const FVector TraceStart = InitialLocation + FVector(0.0f, 0.0f, CapsuleHalfHeight + 200.0f);
        const FVector TraceEnd = InitialLocation - FVector(0.0f, 0.0f, 2000.0f);
        FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(LBControlRoomStandingSpawn), false, this);
        FHitResult FloorHit;
        FVector ResolvedLocation = InitialLocation;
        if (GetWorld()->LineTraceSingleByChannel(
                FloorHit, TraceStart, TraceEnd, ECC_WorldStatic, QueryParams)
            && FloorHit.bBlockingHit)
        {
            ResolvedLocation.Z = FloorHit.ImpactPoint.Z + CapsuleHalfHeight + 2.0f;
        }
        else if (ResolvedLocation.Z < CapsuleHalfHeight + 2.0f)
        {
            ResolvedLocation.Z = CapsuleHalfHeight + 2.0f;
        }
        SetActorLocation(ResolvedLocation, false, nullptr, ETeleportType::TeleportPhysics);
    }
    LockedSeatLocation = GetActorLocation();
    OperatorCollision->SetCollisionEnabled(
        bStanding ? ECollisionEnabled::QueryAndPhysics : ECollisionEnabled::NoCollision);

    if (APlayerController* PlayerController = Cast<APlayerController>(GetController()))
    {
        InitialControlRotation = PlayerController->GetControlRotation();
        PlayerController->bShowMouseCursor = true;
        PlayerController->bEnableClickEvents = true;
        PlayerController->bEnableMouseOverEvents = true;

        FInputModeGameAndUI InputMode;
        InputMode.SetHideCursorDuringCapture(false);
        PlayerController->SetInputMode(InputMode);
    }
    else
    {
        InitialControlRotation = GetActorRotation();
    }

    // Keep the collision body upright. View pitch belongs to the controller;
    // otherwise a local eye-height offset is rotated backward into the desk.
    SetActorRotation(FRotator(0.0f, GetActorRotation().Yaw, 0.0f));
    SeatRoot->SetRelativeLocation(bStanding
        ? FVector(0.0f, 0.0f, StandingCameraHeightCm)
        : FVector(SeatedCameraForwardOffsetCm, 0.0f, SeatedCameraHeightCm));
    UE_LOG(LogTemp, Display,
        TEXT("ControlRoom operator seat=%s actor_rotation=%s camera=%s camera_rotation=%s control_rotation=%s"),
        *LockedSeatLocation.ToString(), *GetActorRotation().ToString(),
        *Camera->GetComponentLocation().ToString(), *Camera->GetComponentRotation().ToString(),
        *InitialControlRotation.ToString());
}

void ALBControlRoomPawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    const float TargetCameraHeight = bStanding ? StandingCameraHeightCm : SeatedCameraHeightCm;
    const float TargetCameraForward = bStanding ? 0.0f : SeatedCameraForwardOffsetCm;
    const FVector CurrentCameraOffset = SeatRoot->GetRelativeLocation();
    SeatRoot->SetRelativeLocation(FVector(
        FMath::FInterpTo(CurrentCameraOffset.X, TargetCameraForward, DeltaSeconds, 8.0f),
        CurrentCameraOffset.Y,
        FMath::FInterpTo(CurrentCameraOffset.Z, TargetCameraHeight, DeltaSeconds, 8.0f)));

    if (!bStanding && !GetActorLocation().Equals(LockedSeatLocation, 0.01f))
    {
        SetActorLocation(LockedSeatLocation, false, nullptr, ETeleportType::TeleportPhysics);
    }
    else if (bStanding)
    {
        FVector BoundedLocation = GetActorLocation();
        BoundedLocation.X = FMath::Clamp(BoundedLocation.X,
            LockedSeatLocation.X - StandingRoomHalfExtentCm.X,
            LockedSeatLocation.X + StandingRoomHalfExtentCm.X);
        BoundedLocation.Y = FMath::Clamp(BoundedLocation.Y,
            LockedSeatLocation.Y - StandingRoomHalfExtentCm.Y,
            LockedSeatLocation.Y + StandingRoomHalfExtentCm.Y);
        BoundedLocation.Z = LockedSeatLocation.Z;
        SetActorLocation(BoundedLocation, true, nullptr, ETeleportType::None);
    }

    if (AController* PawnController = GetController())
    {
        FRotator Rotation = PawnController->GetControlRotation();
        Rotation.Yaw = InitialControlRotation.Yaw + FMath::Clamp(
            FMath::FindDeltaAngleDegrees(InitialControlRotation.Yaw, Rotation.Yaw) + PendingYawInput * 58.0f * DeltaSeconds,
            -MaximumYawOffsetDegrees,
            MaximumYawOffsetDegrees);
        Rotation.Pitch = InitialControlRotation.Pitch + FMath::Clamp(
            FMath::FindDeltaAngleDegrees(InitialControlRotation.Pitch, Rotation.Pitch) + PendingPitchInput * 46.0f * DeltaSeconds,
            -MaximumPitchOffsetDegrees,
            MaximumPitchOffsetDegrees);
        Rotation.Roll = 0.0f;
        PawnController->SetControlRotation(Rotation);
    }

    if (!FMath::IsNearlyZero(PendingZoomInput) && Camera)
    {
        Camera->SetFieldOfView(FMath::Clamp(
            Camera->FieldOfView - PendingZoomInput * 7.0f,
            MinimumFieldOfView,
            MaximumFieldOfView));
        PendingZoomInput = 0.0f;
    }
}

void ALBControlRoomPawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    PlayerInputComponent->BindAxis(TEXT("LB_ControlRoomLookYaw"), this, &ALBControlRoomPawn::LookYaw);
    PlayerInputComponent->BindAxis(TEXT("LB_ControlRoomLookPitch"), this, &ALBControlRoomPawn::LookPitch);
    PlayerInputComponent->BindAxis(TEXT("LB_MoveForward"), this, &ALBControlRoomPawn::MoveForward);
    PlayerInputComponent->BindAxis(TEXT("LB_MoveRight"), this, &ALBControlRoomPawn::MoveRight);
    PlayerInputComponent->BindAxis(TEXT("LB_Rotate"), this, &ALBControlRoomPawn::LookYaw);
    PlayerInputComponent->BindAxis(TEXT("LB_Zoom"), this, &ALBControlRoomPawn::Zoom);
    PlayerInputComponent->BindAction(TEXT("LB_CameraReset"), IE_Pressed, this, &ALBControlRoomPawn::ResetView);
    PlayerInputComponent->BindAction(TEXT("LB_CCTVFocus"), IE_Pressed, this, &ALBControlRoomPawn::FocusSelectedCCTV);
    PlayerInputComponent->BindAction(TEXT("LB_CaptureOperatorEvidence"), IE_Pressed, this, &ALBControlRoomPawn::CaptureOperatorEvidence);
    PlayerInputComponent->BindAction(TEXT("LB_ToggleSeat"), IE_Pressed, this, &ALBControlRoomPawn::ToggleSeatState);
    PlayerInputComponent->BindAction(TEXT("LB_PrimaryClick"), IE_Pressed, this, &ALBControlRoomPawn::InteractUnderCursor);
    PlayerInputComponent->BindAction(TEXT("LB_PrimaryClick"), IE_Released, this, &ALBControlRoomPawn::EndPointerInteraction);
    PlayerInputComponent->BindAction(TEXT("LB_Interact"), IE_Pressed, this, &ALBControlRoomPawn::InteractUnderCursor);
    PlayerInputComponent->BindAction(TEXT("LB_GamepadInteract"), IE_Pressed, this, &ALBControlRoomPawn::InteractAtViewCentre);
    PlayerInputComponent->BindAction(TEXT("LB_ToggleManagement"), IE_Pressed, this, &ALBControlRoomPawn::ToggleManagement);
    PlayerInputComponent->BindAction(TEXT("LB_ManagementNextPage"), IE_Pressed, this, &ALBControlRoomPawn::ManagementNextPage);
    PlayerInputComponent->BindAction(TEXT("LB_ManagementPreviousPage"), IE_Pressed, this, &ALBControlRoomPawn::ManagementPreviousPage);
    PlayerInputComponent->BindAction(TEXT("LB_ManagementNextAction"), IE_Pressed, this, &ALBControlRoomPawn::ManagementNextAction);
    PlayerInputComponent->BindAction(TEXT("LB_ManagementPreviousAction"), IE_Pressed, this, &ALBControlRoomPawn::ManagementPreviousAction);
    PlayerInputComponent->BindAction(TEXT("LB_ManagementConfirm"), IE_Pressed, this, &ALBControlRoomPawn::ManagementConfirm);
}

void ALBControlRoomPawn::MoveForward(float Value)
{
    if (IsManagementOpen() || !bStanding || FMath::IsNearlyZero(Value) || !Controller)
    {
        return;
    }
    const FRotator YawRotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X), Value);
}

void ALBControlRoomPawn::MoveRight(float Value)
{
    if (IsManagementOpen() || !bStanding || FMath::IsNearlyZero(Value) || !Controller)
    {
        return;
    }
    const FRotator YawRotation(0.0f, Controller->GetControlRotation().Yaw, 0.0f);
    AddMovementInput(FRotationMatrix(YawRotation).GetUnitAxis(EAxis::Y), Value);
}

void ALBControlRoomPawn::LookYaw(float Value)
{
    if (IsManagementOpen()) return;
    PendingYawInput = Value;
}

void ALBControlRoomPawn::LookPitch(float Value)
{
    if (IsManagementOpen()) return;
    PendingPitchInput = Value;
}

void ALBControlRoomPawn::Zoom(float Value)
{
    if (IsManagementOpen()) return;
    PendingZoomInput += Value;
}

bool ALBControlRoomPawn::IsManagementOpen() const
{
    const APlayerController* PC = Cast<APlayerController>(GetController());
    const ALBControlRoomHUD* HUD = PC ? Cast<ALBControlRoomHUD>(PC->GetHUD()) : nullptr;
    return HUD && HUD->IsManagementVisible();
}

void ALBControlRoomPawn::ToggleManagement()
{
    EnterManagementView();
}

bool ALBControlRoomPawn::EnterManagementView()
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    UWorld* World = GetWorld();
    if (!PC || !World) return false;

    FVector ManagementCentre = GetActorLocation();
    int32 AuthorityCount = 0;
    for (TActorIterator<ALBPressShopBuildAuthority> It(World); It; ++It)
    {
        ManagementCentre = It->GetActorLocation();
        ++AuthorityCount;
    }
    if (AuthorityCount != 1) return false;

    ALBManagementPawn* ManagementPawn = World->SpawnActor<ALBManagementPawn>(
        ALBManagementPawn::StaticClass(), ManagementCentre, FRotator::ZeroRotator);
    if (!ManagementPawn) return false;
    ManagementPawn->SetReturnPawn(this);
    PC->Possess(ManagementPawn);
    if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD()))
        if (!HUD->IsManagementVisible()) HUD->ToggleManagement();
    return true;
}

void ALBControlRoomPawn::ManagementNextPage()
{
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->NextManagementPage();
}

void ALBControlRoomPawn::ManagementPreviousPage()
{
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->PreviousManagementPage();
}

void ALBControlRoomPawn::ManagementNextAction()
{
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->NextManagementAction();
}

void ALBControlRoomPawn::ManagementPreviousAction()
{
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->PreviousManagementAction();
}

void ALBControlRoomPawn::ManagementConfirm()
{
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->ConfirmManagementAction();
}

void ALBControlRoomPawn::ResetView()
{
    if (APlayerController* PlayerController = Cast<APlayerController>(GetController()))
    {
        if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PlayerController->GetHUD()))
        {
            HUD->HideCCTVFeed();
        }
    }
    if (AController* PawnController = GetController())
    {
        PawnController->SetControlRotation(InitialControlRotation);
    }
    if (Camera)
    {
        Camera->SetFieldOfView(MaximumFieldOfView);
    }
    if (UWorld* World = GetWorld())
    {
        for (TActorIterator<ALBControlRoomCCTVFeed> It(World); It; ++It)
        {
            It->SetSelectedFeed(false);
        }
    }
}

void ALBControlRoomPawn::InteractUnderCursor()
{
    if (IsManagementOpen())
    {
        return;
    }
    if (WidgetInteraction)
    {
        WidgetInteraction->PressPointerKey(EKeys::LeftMouseButton);
    }

    APlayerController* PlayerController = Cast<APlayerController>(GetController());
    if (!PlayerController)
    {
        return;
    }

    FHitResult Hit;
    if (PlayerController->GetHitResultUnderCursor(ECC_Visibility, false, Hit))
    {
        if (ALBControlRoomOperationsConsole* Operations = Cast<ALBControlRoomOperationsConsole>(Hit.GetActor()))
        {
            Operations->HandleComponentInteraction(Hit.GetComponent());
            return;
        }
        InteractWithActor(Hit.GetActor());
    }
}

void ALBControlRoomPawn::InteractAtViewCentre()
{
    if (IsManagementOpen())
    {
        return;
    }
    if (!Camera || !GetWorld())
    {
        return;
    }

    const FVector TraceStart = Camera->GetComponentLocation();
    const FVector TraceEnd = TraceStart + Camera->GetForwardVector() * 900.0f;
    FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(LBControlRoomGamepadInteract), true, this);
    FHitResult Hit;
    if (!GetWorld()->LineTraceSingleByChannel(Hit, TraceStart, TraceEnd, ECC_Visibility, QueryParams))
    {
        UE_LOG(LogTemp, Display, TEXT("ControlRoom centre-view interaction missed start=%s end=%s"),
            *TraceStart.ToString(), *TraceEnd.ToString());
        return;
    }

    UE_LOG(LogTemp, Display, TEXT("ControlRoom centre-view interaction hit actor=%s component=%s"),
        *GetNameSafe(Hit.GetActor()), *GetNameSafe(Hit.GetComponent()));

    if (ALBControlRoomOperationsConsole* Operations = Cast<ALBControlRoomOperationsConsole>(Hit.GetActor()))
    {
        Operations->HandleComponentInteraction(Hit.GetComponent());
        return;
    }
    InteractWithActor(Hit.GetActor());
}

bool ALBControlRoomPawn::InteractWithActor(AActor* TargetActor)
{
    if (ALBControlRoomOperationsConsole* Operations = Cast<ALBControlRoomOperationsConsole>(TargetActor))
    {
        return FocusOnActor(Operations);
    }
    if (ALBControlRoomCCTVFeed* CCTVFeed = Cast<ALBControlRoomCCTVFeed>(TargetActor))
    {
        CCTVFeed->SetSelectedFeed(true);
        return FocusOnActor(CCTVFeed);
    }

    if (ALBControlRoomPR004Console* Console = Cast<ALBControlRoomPR004Console>(TargetActor))
    {
        return Console->TriggerPrimaryAction(TEXT("CONTROL_ROOM_PR004_POINTER"));
    }

    if (ALBPR004Station* Station = Cast<ALBPR004Station>(TargetActor))
    {
        return Station->UnpackageCoil(TEXT("CONTROL_ROOM_DIRECT_UNPACKAGE"));
    }
    return false;
}

bool ALBControlRoomPawn::FocusOnActor(AActor* TargetActor)
{
    AController* PawnController = GetController();
    if (!TargetActor || !Camera || !PawnController)
    {
        return false;
    }

    Camera->SetFieldOfView(FMath::Clamp(
        FocusedScreenFieldOfView,
        MinimumFieldOfView,
        MaximumFieldOfView));

    if (ALBControlRoomCCTVFeed* CCTVFeed = Cast<ALBControlRoomCCTVFeed>(TargetActor))
    {
        if (APlayerController* PlayerController = Cast<APlayerController>(PawnController))
        {
            if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PlayerController->GetHUD()))
            {
                HUD->ShowCCTVFeed(CCTVFeed->GetRenderTarget());
                UE_LOG(LogTemp, Display, TEXT("Cairnwell CCTV selected-feed HUD opened"));
            }
        }
        return true;
    }

    FRotator DesiredRotation = (TargetActor->GetActorLocation() - Camera->GetComponentLocation()).Rotation();
    DesiredRotation.Yaw = InitialControlRotation.Yaw + FMath::Clamp(
        FMath::FindDeltaAngleDegrees(InitialControlRotation.Yaw, DesiredRotation.Yaw),
        -MaximumYawOffsetDegrees,
        MaximumYawOffsetDegrees);
    DesiredRotation.Pitch = InitialControlRotation.Pitch + FMath::Clamp(
        FMath::FindDeltaAngleDegrees(InitialControlRotation.Pitch, DesiredRotation.Pitch),
        -MaximumPitchOffsetDegrees,
        MaximumPitchOffsetDegrees);
    DesiredRotation.Roll = 0.0f;
    PawnController->SetControlRotation(DesiredRotation);
    return true;
}

void ALBControlRoomPawn::FocusSelectedCCTV()
{
    if (IsManagementOpen())
    {
        return;
    }
    if (UWorld* World = GetWorld())
    {
        ALBControlRoomCCTVFeed* FallbackFeed = nullptr;
        for (TActorIterator<ALBControlRoomCCTVFeed> It(World); It; ++It)
        {
            if (!FallbackFeed)
            {
                FallbackFeed = *It;
            }
            if (It->IsSelectedFeed())
            {
                FocusOnActor(*It);
                return;
            }
        }
        if (FallbackFeed)
        {
            FallbackFeed->SetSelectedFeed(true);
            FocusOnActor(FallbackFeed);
        }
    }
}

void ALBControlRoomPawn::CaptureOperatorEvidence()
{
    const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots/WindowsEditor"));
    IFileManager::Get().MakeDirectory(*Directory, true);
    const FString Filename = FPaths::Combine(
        Directory,
        FString::Printf(TEXT("ControlRoomOperatorEvidence_%s.png"),
            *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S"))));
    FScreenshotRequest::RequestScreenshot(Filename, true, false, false, FIntRect(), true);
}

void ALBControlRoomPawn::EndPointerInteraction()
{
    if (WidgetInteraction)
    {
        WidgetInteraction->ReleasePointerKey(EKeys::LeftMouseButton);
    }
}

float ALBControlRoomPawn::GetCurrentFieldOfView() const
{
    return Camera ? Camera->FieldOfView : 0.0f;
}

bool ALBControlRoomPawn::CanSitAtChair() const
{
    return FVector::Dist2D(GetActorLocation(), LockedSeatLocation) <= ChairSitRadiusCm;
}

void ALBControlRoomPawn::ToggleSeatState()
{
    if (!bStanding)
    {
        OperatorCollision->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
        bStanding = true;
        return;
    }

    if (!CanSitAtChair())
    {
        if (GEngine)
        {
            GEngine->AddOnScreenDebugMessage(-1, 2.5f, FColor::Yellow,
                TEXT("Return to the operator chair before sitting."));
        }
        return;
    }

    bStanding = false;
    OperatorCollision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    SetActorLocation(LockedSeatLocation, false, nullptr, ETeleportType::TeleportPhysics);
    ResetView();
}
