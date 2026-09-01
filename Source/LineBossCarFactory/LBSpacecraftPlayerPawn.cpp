#include "LBSpacecraftPlayerPawn.h"
#include "LBSpacecraftTrackAuthority.h"

#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/InputSettings.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "LBGameUserSettings.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftGameMode.h"
#include "LBSpacecraftInputMap.h"
#include "LBSpacecraftProgressionAuthority.h"
#include "Materials/MaterialInstanceDynamic.h"

#define LOCTEXT_NAMESPACE "LBSpacecraftPawn"

namespace LBSpacecraftPlayerPawnPrivate
{
	// Unity-build safety: helpers qualified by subject.
	const TCHAR* SpacecraftGhostCubePath =
		TEXT("/Engine/BasicShapes/Cube.Cube");
	const TCHAR* SpacecraftGhostMaterialPath =
		TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
	constexpr float SpacecraftGhostHeightCm = 300.f;
	const FLinearColor SpacecraftGhostColour(0.35f, 0.65f, 1.f, 0.5f);
	const FLinearColor SpacecraftGhostRefusedColour(1.f, 0.32f, 0.1f, 0.5f);
}

ALBSpacecraftPlayerPawn::ALBSpacecraftPlayerPawn()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Pivot"));
	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("Boom"));
	CameraBoom->SetupAttachment(RootComponent);
	// The proven framing contract: pitch -35, perspective FOV 48.
	CameraBoom->SetRelativeRotation(FRotator(-35.f, 0.f, 0.f));
	CameraBoom->TargetArmLength = DesiredZoomCm;
	CameraBoom->bDoCollisionTest = false;
	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(CameraBoom);
	Camera->SetFieldOfView(48.f);
	AutoPossessPlayer = EAutoReceiveInput::Player0;
}

void ALBSpacecraftPlayerPawn::BeginPlay()
{
	Super::BeginPlay();
	// THE GAME OPENS ON THE WORLD MAP (owner 2026-08-28: "game should
	// start on world map and player should be only able to pick the
	// ship factory, place on map, click on it to enter then build
	// factory"). FocusSite frames the whole site; on a bare site that
	// is the boot framing, so the first view is the plot the player is
	// about to build on.
	// May legitimately fail here: the pawn can boot before the game
	// mode has built its authorities, and in a PACKAGED build it does.
	// Tick keeps asking until it takes.
	bOpeningViewFramed = FocusSite();
	CameraBoom->TargetArmLength = DesiredZoomCm;
}

void ALBSpacecraftPlayerPawn::SetupPlayerInputComponent(
	UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	// The LB_SC_* scheme (FLBSpacecraftInputMap): shipped defaults live
	// in DefaultInput.ini; EnsureSpacecraftBindings backfills mappings a
	// stale Saved/Input.ini predates, so a new action can never be dead.
	if (UInputSettings* Settings = UInputSettings::GetInputSettings())
	{
		FLBSpacecraftInputMap::EnsureSpacecraftBindings(*Settings);
	}
	PlayerInputComponent->BindAxis(TEXT("LB_SC_PanForward"), this,
		&ALBSpacecraftPlayerPawn::MoveForward);
	PlayerInputComponent->BindAxis(TEXT("LB_SC_PanRight"), this,
		&ALBSpacecraftPlayerPawn::MoveRight);
	PlayerInputComponent->BindAxis(TEXT("LB_SC_Rotate"), this,
		&ALBSpacecraftPlayerPawn::Rotate);
	PlayerInputComponent->BindAxis(TEXT("LB_SC_ZoomWheel"), this,
		&ALBSpacecraftPlayerPawn::Zoom);
	PlayerInputComponent->BindAxis(TEXT("LB_SC_ZoomKeys"), this,
		&ALBSpacecraftPlayerPawn::ZoomKeys);
	PlayerInputComponent->BindAction(TEXT("LB_SC_PrimaryClick"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::PrimaryClick);
	PlayerInputComponent->BindAction(TEXT("LB_SC_SecondaryClick"),
		IE_Pressed, this, &ALBSpacecraftPlayerPawn::SecondaryClick);
	PlayerInputComponent->BindAction(TEXT("LB_SC_RotateGhost"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::RotateGhost);
	PlayerInputComponent->BindAction(TEXT("LB_SC_RotateGhostBack"),
		IE_Pressed, this, &ALBSpacecraftPlayerPawn::RotateGhostBack);
	PlayerInputComponent->BindAction(TEXT("LB_SC_SiteMap"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::HandleSiteMap);
	PlayerInputComponent->BindAction(TEXT("LB_SC_CameraReset"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::ResetCameraFraming);
	PlayerInputComponent->BindAction(TEXT("LB_SC_DragPan"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::DragPanPressed);
	PlayerInputComponent->BindAction(TEXT("LB_SC_DragPan"), IE_Released,
		this, &ALBSpacecraftPlayerPawn::DragPanReleased);
	PlayerInputComponent->BindAction(TEXT("LB_SC_SpeedPause"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::SpeedPause);
	PlayerInputComponent->BindAction(TEXT("LB_SC_SpeedNormal"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::SpeedNormal);
	PlayerInputComponent->BindAction(TEXT("LB_SC_SpeedFast"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::SpeedFast);
	PlayerInputComponent->BindAction(TEXT("LB_SC_SpeedFastest"),
		IE_Pressed, this, &ALBSpacecraftPlayerPawn::SpeedFastest);
	PlayerInputComponent->BindAction(TEXT("LB_SC_PanelNext"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::PanelNextTab);
	PlayerInputComponent->BindAction(TEXT("LB_SC_PanelPrev"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::PanelPrevTab);
	PlayerInputComponent->BindAction(TEXT("LB_SC_QuickSave"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::QuickSavePressed);
	PlayerInputComponent->BindAction(TEXT("LB_SC_QuickLoad"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::QuickLoadPressed);
	// Escape: cancel an active placement, else the pause menu. Must
	// still fire while paused so Escape also RESUMES.
	FInputActionBinding& PauseBinding = PlayerInputComponent->BindAction(
		TEXT("LB_SC_Menu"), IE_Pressed,
		this, &ALBSpacecraftPlayerPawn::EscapePressed);
	PauseBinding.bExecuteWhenPaused = true;
	if (APlayerController* PlayerController =
		Cast<APlayerController>(GetController()))
	{
		PlayerController->bShowMouseCursor = true;
		PlayerController->bEnableClickEvents = true;
	}
}

void ALBSpacecraftPlayerPawn::MoveForward(float Value)
{
	PanCamera(Value, 0.f);
}

void ALBSpacecraftPlayerPawn::MoveRight(float Value)
{
	PanCamera(0.f, Value);
}

float ALBSpacecraftPlayerPawn::GetPanSpeedScale() const
{
	const ULBGameUserSettings* Settings =
		ULBGameUserSettings::GetLineBossGameUserSettings();
	return Settings != nullptr ? Settings->GetCameraPanSpeedScale() : 1.f;
}

void ALBSpacecraftPlayerPawn::PanCamera(float ForwardValue, float RightValue)
{
	if (FMath::IsNearlyZero(ForwardValue) && FMath::IsNearlyZero(RightValue))
	{
		return;
	}
	const float Speed = DesiredZoomCm * 0.9f * GetPanSpeedScale();
	const FRotator Yaw(0.f, GetActorRotation().Yaw, 0.f);
	const FVector Direction =
		Yaw.RotateVector(FVector::ForwardVector) * ForwardValue
		+ Yaw.RotateVector(FVector::RightVector) * RightValue;
	AddActorWorldOffset(Direction * Speed * GetWorld()->GetDeltaSeconds());
}

void ALBSpacecraftPlayerPawn::Rotate(float Value)
{
	if (!FMath::IsNearlyZero(Value))
	{
		AddActorWorldRotation(FRotator(0.f,
			Value * 90.f * GetWorld()->GetDeltaSeconds(), 0.f));
	}
}

void ALBSpacecraftPlayerPawn::Zoom(float Value)
{
	ApplyZoomDelta(Value);
}

void ALBSpacecraftPlayerPawn::ZoomKeys(float Value)
{
	// Held keys (the Car Manufacture C/V pair) zoom continuously at
	// three wheel-notches per second, frame-rate independent.
	if (!FMath::IsNearlyZero(Value))
	{
		ApplyZoomDelta(Value * 3.f * GetWorld()->GetDeltaSeconds());
	}
}

void ALBSpacecraftPlayerPawn::ApplyZoomDelta(float Value)
{
	if (FMath::IsNearlyZero(Value))
	{
		return;
	}
	const ULBGameUserSettings* Settings =
		ULBGameUserSettings::GetLineBossGameUserSettings();
	if (Settings != nullptr)
	{
		Value *= Settings->GetCameraZoomSpeedScale();
		if (Settings->IsZoomInverted())
		{
			Value = -Value;
		}
	}
	DesiredZoomCm = FMath::Clamp(
		DesiredZoomCm - Value * DesiredZoomCm * 0.12f,
		ZoomMinCm, ZoomMaxCm);
}

void ALBSpacecraftPlayerPawn::ResetCameraFraming()
{
	bSiteMapView = false;
	SetActorLocation(GetBootFramingLocation());
	SetActorRotation(FRotator::ZeroRotator);
	DesiredZoomCm = GetBootFramingZoomCm();
}


void ALBSpacecraftPlayerPawn::EscapePressed()
{
	// Review fix: the ghost COMPONENT can outlive or lag the logical
	// placement state - the definition is the truth.
	if (!GetPlacementDefinition().IsNone())
	{
		CancelPlacement();
		return;
	}
	if (ALBSpacecraftGameMode* LaunchGameMode =
		GetWorld()->GetAuthGameMode<ALBSpacecraftGameMode>())
	{
		if (LaunchGameMode->IsLaunchCameraActive())
		{
			LaunchGameMode->CancelLaunchCamera();
			return;
		}
	}
	if (ALBSpacecraftGameMode* GameMode =
		GetWorld()->GetAuthGameMode<ALBSpacecraftGameMode>())
	{
		GameMode->TogglePauseMenu();
	}
}

void ALBSpacecraftPlayerPawn::RotateGhost()
{
	if (!PlacementDefinitionId.IsNone())
	{
		GhostYawDeg = FMath::Fmod(GhostYawDeg + 90.f, 360.f);
	}
}

void ALBSpacecraftPlayerPawn::RotateGhostBack()
{
	if (!PlacementDefinitionId.IsNone())
	{
		GhostYawDeg = FMath::Fmod(GhostYawDeg + 270.f, 360.f);
	}
}

void ALBSpacecraftPlayerPawn::SecondaryClick()
{
	// The Car Manufacture right-click: cancel what is armed, else drop
	// the selection. (Their RMB-drag camera rotate is deferred until a
	// click-vs-drag threshold exists - see the input map doc.)
	if (!PlacementDefinitionId.IsNone())
	{
		CancelPlacement();
		return;
	}
	if (!SelectedStationId.IsNone())
	{
		SelectedStationId = NAME_None;
		LastActionText = LOCTEXT("Deselected", "SELECTION CLEARED")
			.ToString();
	}
}

void ALBSpacecraftPlayerPawn::DragPanPressed()
{
	bDragPanActive = true;
}

void ALBSpacecraftPlayerPawn::DragPanReleased()
{
	bDragPanActive = false;
}

void ALBSpacecraftPlayerPawn::TickDragPan()
{
	// Grab-the-floor pan: the floor point under the cursor at the last
	// tick stays glued to the cursor - exact at every zoom, no tuning.
	if (!bDragPanActive)
	{
		bDragAnchorValid = false;
		return;
	}
	FVector FloorPoint;
	if (!CursorToFloor(FloorPoint))
	{
		bDragAnchorValid = false;
		return;
	}
	if (bDragAnchorValid)
	{
		const FVector Offset = DragAnchorFloor - FloorPoint;
		AddActorWorldOffset(FVector(Offset.X, Offset.Y, 0.f));
	}
	else
	{
		DragAnchorFloor = FloorPoint;
		bDragAnchorValid = true;
	}
}

FIntPoint ALBSpacecraftPlayerPawn::ComputeEdgeScrollDirection(
	const FVector2D& CursorPx, const FVector2D& ViewportPx,
	const float MarginPx)
{
	if (CursorPx.X < 0.f || CursorPx.Y < 0.f
		|| CursorPx.X > ViewportPx.X || CursorPx.Y > ViewportPx.Y
		|| ViewportPx.X <= 2.f * MarginPx || ViewportPx.Y <= 2.f * MarginPx)
	{
		return FIntPoint::ZeroValue;
	}
	FIntPoint Direction = FIntPoint::ZeroValue;
	if (CursorPx.X <= MarginPx)
	{
		Direction.X = -1;
	}
	else if (CursorPx.X >= ViewportPx.X - MarginPx)
	{
		Direction.X = 1;
	}
	if (CursorPx.Y <= MarginPx)
	{
		Direction.Y = -1;
	}
	else if (CursorPx.Y >= ViewportPx.Y - MarginPx)
	{
		Direction.Y = 1;
	}
	return Direction;
}

void ALBSpacecraftPlayerPawn::TickEdgeScroll(float DeltaSeconds)
{
	// Off by default (the genre reference ships without it); a settings
	// toggle turns it on. Never fights an active drag-pan.
	(void)DeltaSeconds;
	const ULBGameUserSettings* Settings =
		ULBGameUserSettings::GetLineBossGameUserSettings();
	if (Settings == nullptr || !Settings->IsEdgeScrollEnabled()
		|| bDragPanActive)
	{
		return;
	}
	const APlayerController* PlayerController =
		Cast<APlayerController>(GetController());
	if (PlayerController == nullptr)
	{
		return;
	}
	float MouseX = 0.f;
	float MouseY = 0.f;
	if (!PlayerController->GetMousePosition(MouseX, MouseY))
	{
		return;
	}
	int32 SizeX = 0;
	int32 SizeY = 0;
	PlayerController->GetViewportSize(SizeX, SizeY);
	const FIntPoint Direction = ComputeEdgeScrollDirection(
		FVector2D(MouseX, MouseY), FVector2D(SizeX, SizeY),
		EdgeScrollMarginPx);
	if (Direction != FIntPoint::ZeroValue)
	{
		// Screen-up is camera-forward; screen-right is camera-right.
		PanCamera(-Direction.Y, Direction.X);
	}
}

void ALBSpacecraftPlayerPawn::SetSimSpeedWithToast(float Scale)
{
	if (ALBSpacecraftGameMode* GameMode = GetSpacecraftGameMode())
	{
		FString Reason;
		GameMode->SetSimSpeed(Scale, Reason);
		LastActionText = Reason;
	}
}

void ALBSpacecraftPlayerPawn::SpeedPause()
{
	SetSimSpeedWithToast(0.f);
}

void ALBSpacecraftPlayerPawn::SpeedNormal()
{
	SetSimSpeedWithToast(1.f);
}

void ALBSpacecraftPlayerPawn::SpeedFast()
{
	SetSimSpeedWithToast(2.f);
}

void ALBSpacecraftPlayerPawn::SpeedFastest()
{
	SetSimSpeedWithToast(4.f);
}

void ALBSpacecraftPlayerPawn::PanelNextTab()
{
	// Legacy chords: a plain-Tab action also fires while Shift is held,
	// so Shift+Tab must be ceded to the PanelPrev binding here.
	const APlayerController* PlayerController =
		Cast<APlayerController>(GetController());
	if (PlayerController != nullptr
		&& (PlayerController->IsInputKeyDown(EKeys::LeftShift)
			|| PlayerController->IsInputKeyDown(EKeys::RightShift)))
	{
		return;
	}
	if (ALBSpacecraftGameMode* GameMode = GetSpacecraftGameMode())
	{
		GameMode->CyclePanelTab(1);
	}
}

void ALBSpacecraftPlayerPawn::PanelPrevTab()
{
	if (ALBSpacecraftGameMode* GameMode = GetSpacecraftGameMode())
	{
		GameMode->CyclePanelTab(-1);
	}
}

void ALBSpacecraftPlayerPawn::QuickSavePressed()
{
	if (ALBSpacecraftGameMode* GameMode = GetSpacecraftGameMode())
	{
		FString Reason;
		GameMode->QuickSave(Reason);
		LastActionText = Reason;
	}
}

void ALBSpacecraftPlayerPawn::QuickLoadPressed()
{
	if (ALBSpacecraftGameMode* GameMode = GetSpacecraftGameMode())
	{
		FString Reason;
		GameMode->QuickLoad(Reason);
		LastActionText = Reason;
	}
}

FVector ALBSpacecraftPlayerPawn::SnapToBuildGrid(const FVector& FloorPoint,
	float GridCm)
{
	return FVector(FMath::GridSnap(FloorPoint.X, GridCm),
		FMath::GridSnap(FloorPoint.Y, GridCm), 0.f);
}

bool ALBSpacecraftPlayerPawn::StationContainsPoint(
	const FTransform& StationTransform, const FVector2D& FootprintCm,
	const FVector& FloorPoint)
{
	const FVector Local =
		StationTransform.InverseTransformPosition(FloorPoint);
	return FMath::Abs(Local.X) <= FootprintCm.X * 0.5f
		&& FMath::Abs(Local.Y) <= FootprintCm.Y * 0.5f;
}

bool ALBSpacecraftPlayerPawn::CursorToFloor(FVector& OutFloorPoint) const
{
	const APlayerController* PlayerController =
		Cast<APlayerController>(GetController());
	if (PlayerController == nullptr)
	{
		return false;
	}
	FVector Origin;
	FVector Direction;
	if (!PlayerController->DeprojectMousePositionToWorld(Origin, Direction)
		|| Direction.Z >= -0.001f)
	{
		return false;
	}
	const float T = -Origin.Z / Direction.Z;
	OutFloorPoint = Origin + Direction * T;
	return true;
}

ALBSpacecraftGameMode* ALBSpacecraftPlayerPawn::GetSpacecraftGameMode() const
{
	return ALBSpacecraftGameMode::FindInWorld(GetWorld());
}

FName ALBSpacecraftPlayerPawn::FindStationUnderCursor() const
{
	FVector FloorPoint;
	ALBSpacecraftGameMode* GameMode = GetSpacecraftGameMode();
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr
		|| !CursorToFloor(FloorPoint))
	{
		return NAME_None;
	}
	for (const FLBSpacecraftStationRecord& Record :
		GameMode->GetBuildAuthority()->GetStations())
	{
		const FLBSpacecraftStationDefinition* Definition =
			ALBSpacecraftBuildAuthority::FindDefinition(Record.DefinitionId);
		if (Definition != nullptr && StationContainsPoint(
			Record.WorldTransform, Definition->FootprintCm, FloorPoint))
		{
			return Record.StationId;
		}
	}
	return NAME_None;
}

void ALBSpacecraftPlayerPawn::SetPlacementDefinition(FName DefinitionId)
{
	PlacementDefinitionId = DefinitionId;
	SelectedStationId = NAME_None;
	if (DefinitionId.IsNone())
	{
		LastActionText = LOCTEXT("PlacementCancelled",
			"PLACEMENT CANCELLED").ToString();
	}
	else
	{
		LastActionText = FText::Format(LOCTEXT("PlacingHint",
			"PLACING {0} - click the floor; X/Z rotates; right-click cancels"),
			FText::FromName(DefinitionId)).ToString();
	}
}

void ALBSpacecraftPlayerPawn::CancelPlacement()
{
	SetPlacementDefinition(NAME_None);
}

void ALBSpacecraftPlayerPawn::PrimaryClick()
{
	ALBSpacecraftGameMode* GameMode = GetSpacecraftGameMode();
	if (GameMode == nullptr)
	{
		return;
	}
	if (!PlacementDefinitionId.IsNone())
	{
		FVector FloorPoint;
		if (!CursorToFloor(FloorPoint)
			|| GameMode->GetBuildAuthority() == nullptr
			|| GameMode->GetPowerAuthority() == nullptr
			|| GameMode->GetInventoryAuthority() == nullptr)
		{
			return;
		}
		const FVector Snapped = SnapToBuildGrid(FloorPoint,
			ALBSpacecraftBuildAuthority::GetPlacementGridCm());
		// LINE STATIONS STAND ON THE TRACK (owner 2026-09-01: "you can
		// put stuff anywhere" - seven scattered stations later the
		// commission gate shouted a paragraph. The rule existed but
		// fired LATE; now it fires at the click). A line-station drop
		// snaps to the nearest FREE straight piece and attaches as its
		// node in the same click; with no track in reach it refuses
		// immediately, in one line, while the mistake is still free.
		FTransform PlaceTransform(FRotator(0.f, GhostYawDeg, 0.f),
			Snapped);
		FName SnapPieceId = NAME_None;
		const FLBSpacecraftStationDefinition* PlacingDefinition =
			ALBSpacecraftBuildAuthority::FindDefinition(
				PlacementDefinitionId);
		if (PlacingDefinition != nullptr
			&& PlacingDefinition->StageClassId
				== FName(TEXT("LineStation"))
			&& GameMode->GetTrackAuthority() != nullptr)
		{
			float BestDistSq = FMath::Square(3000.f);
			const FLBSpacecraftTrackPieceRecord* BestPiece = nullptr;
			for (const FLBSpacecraftTrackPieceRecord& Piece :
				GameMode->GetTrackAuthority()->GetPieces())
			{
				if (Piece.PieceType != ELBSpacecraftTrackPiece::Straight
					|| !Piece.NodeStationId.IsNone())
				{
					continue;
				}
				const float DistSq = FVector::DistSquared2D(
					Piece.WorldTransform.GetLocation(), Snapped);
				if (DistSq < BestDistSq)
				{
					BestDistSq = DistSq;
					BestPiece = &Piece;
				}
			}
			if (BestPiece == nullptr)
			{
				LastActionText = LOCTEXT("NeedTrack",
					"LINE STATIONS STAND ON THE TRACK - lay track, "
					"then click beside a free straight piece")
					.ToString();
				return;
			}
			PlaceTransform = FTransform(
				BestPiece->WorldTransform.GetRotation(),
				FVector(BestPiece->WorldTransform.GetLocation().X,
					BestPiece->WorldTransform.GetLocation().Y, 0.f));
			SnapPieceId = BestPiece->PieceId;
		}
		FName StationId;
		FString Reason;
		if (ALBSpacecraftGameMode::PlaceStationPowered(
			*GameMode->GetBuildAuthority(), *GameMode->GetPowerAuthority(),
			*GameMode->GetInventoryAuthority(), PlacementDefinitionId,
			PlaceTransform,
			StationId, Reason, GameMode->GetProductionAuthority(),
			GameMode->GetProgression()))
		{
			LastActionText = FText::Format(LOCTEXT("Placed",
				"PLACED {0}"), FText::FromName(StationId)).ToString();
			if (!SnapPieceId.IsNone())
			{
				FString AttachReason;
				if (GameMode->GetTrackAuthority()->AttachStationNode(
					StationId, SnapPieceId,
					GameMode->GetBuildAuthority(), AttachReason))
				{
					LastActionText = FText::Format(LOCTEXT(
						"PlacedOnTrack",
						"PLACED {0} ON THE TRACK"),
						FText::FromName(StationId)).ToString();
				}
				else
				{
					LastActionText = AttachReason;
				}
			}
			// A NEW SHIP FACTORY COMES WITH ITS STARTING LOADOUT
			// (owner 2026-08-28): one assembly station crewed by one
			// of each drone, commissioned, with the whole build
			// happening at that one station. The game mode owns the
			// policy and decides whether it applies - the pawn only
			// reports that a building went down.
			FString LoadoutReason;
			if (ALBSpacecraftGameMode::SeedShipFactoryLoadout(
				*GameMode->GetBuildAuthority(),
				*GameMode->GetPowerAuthority(),
				*GameMode->GetInventoryAuthority(), StationId,
				LoadoutReason, GameMode->GetProgression(),
				GameMode->GetCoordinator(),
				GameMode->GetProductionAuthority(),
				GameMode->GetTrackAuthority()))
			{
				LastActionText = LoadoutReason;
			}
		}
		else
		{
			// The fail-closed reason IS the player feedback.
			LastActionText = Reason;
		}
		return;
	}
	// No placement armed: clicking selects a station for the panel.
	SelectedStationId = FindStationUnderCursor();
	if (!SelectedStationId.IsNone())
	{
		LastActionText = FText::Format(LOCTEXT("Selected",
			"SELECTED {0}"),
			FText::FromName(SelectedStationId)).ToString();
		// Clicking a BUILDING enters it: the camera flies to frame it
		// and the panel - which already scopes to the selection - shows
		// what is installed inside. Line stations just select; the
		// camera jumping on every line click would fight the player.
		const ALBSpacecraftGameMode* SelectMode =
			ALBSpacecraftGameMode::FindInWorld(GetWorld());
		const FLBSpacecraftStationRecord* Record =
			SelectMode != nullptr
				&& SelectMode->GetBuildAuthority() != nullptr
				? SelectMode->GetBuildAuthority()->FindStation(
					SelectedStationId)
				: nullptr;
		const FLBSpacecraftStationDefinition* Definition =
			Record != nullptr
				? ALBSpacecraftBuildAuthority::FindDefinition(
					Record->DefinitionId)
				: nullptr;
		// Site buildings enter too, and are the main reason entering
		// exists (owner 2026-08-28: "click on it to enter then build
		// factory") - a placed ship factory is the doorway from the
		// world map into the floor you build on.
		if (Definition != nullptr
			&& (Definition->SlotCount > 0 || Definition->bSiteBuilding))
		{
			FocusStation(SelectedStationId);
		}
	}
}

void ALBSpacecraftPlayerPawn::FocusStation(FName StationId)
{
	const ALBSpacecraftGameMode* GameMode =
		ALBSpacecraftGameMode::FindInWorld(GetWorld());
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr)
	{
		return;
	}
	const FLBSpacecraftStationRecord* Record =
		GameMode->GetBuildAuthority()->FindStation(StationId);
	const FLBSpacecraftStationDefinition* Definition =
		Record != nullptr
			? ALBSpacecraftBuildAuthority::FindDefinition(
				Record->DefinitionId)
			: nullptr;
	if (Record == nullptr || Definition == nullptr)
	{
		return;
	}
	FVector Pivot = Record->WorldTransform.GetLocation();
	Pivot.Z = 0.f;
	SetActorLocation(Pivot);
	// A SITE BUILDING frames its whole INTERIOR FLOOR, tight (the
	// player is standing on the floor they build on, not looking at a
	// roof), and needs the site ceiling to do it - a 160 m hall does
	// not fit inside the ordinary 16000 cm zoom limit. Slot buildings
	// keep the roomier margin: there the point is the building in its
	// surroundings.
	const bool bInterior = Definition->bSiteBuilding
		&& !Definition->InteriorFloorCm.IsNearlyZero();
	DesiredZoomCm = ComputeFramingZoomCm(
		bInterior ? Definition->InteriorFloorCm : Definition->FootprintCm,
		/*MarginRatio=*/bInterior ? 1.15f : 2.6f, ZoomMinCm,
		bInterior ? SiteMapZoomCeilingCm() : ZoomMaxCm);
	FocusedBuildingId = StationId;
	bSiteMapView = false;
	LastActionText = FText::Format(
		LOCTEXT("EnteredBuilding", "ENTERED {0} - M FOR THE SITE MAP"),
		FText::FromString(Definition->DisplayName)).ToString();
}

float ALBSpacecraftPlayerPawn::GetCameraArmLengthCm() const
{
	return CameraBoom != nullptr ? CameraBoom->TargetArmLength : 0.f;
}

float ALBSpacecraftPlayerPawn::GetCameraFovDeg() const
{
	return Camera != nullptr ? Camera->FieldOfView : 0.f;
}

void ALBSpacecraftPlayerPawn::WatchStation(FName StationId, float ZoomCm)
{
	FocusStation(StationId);
	SelectedStationId = StationId;
	// After FocusStation, deliberately: its framing is computed for the
	// whole footprint and would otherwise overwrite the close range
	// this exists to set.
	DesiredZoomCm = FMath::Clamp(ZoomCm, 500.f, SiteMapZoomCeilingCm());
	bSiteMapView = false;
}

void ALBSpacecraftPlayerPawn::FocusRunway()
{
	// The runway is permanent site furniture at the +X edge, and the
	// departure runs down it. Frame the strip itself, from far enough
	// back that the whole run - hover, chicane, sprint - is in shot.
	// Not a cinematic: a camera position, which is what the launch has
	// been missing every time it was captured from the factory floor.
	// Derived from the site, like the runway itself: a literal here
	// would drift the moment the map changed size, which is exactly
	// how the strip ended up inside the factory.
	const float RunwayX =
		ALBSpacecraftBuildAuthority::SiteHalfExtentCm() - 2500.f;
	// Centred ON the strip and pulled back far enough to hold the whole
	// run in frame. The first attempt sat 60 m short of it and framed a
	// district building instead - a camera that has to be lucky to
	// catch the shot is not a camera for the game's signature moment.
	SetActorLocation(FVector(RunwayX, -3500.f, 0.f));
	DesiredZoomCm = ComputeFramingZoomCm(FVector2D(30000.f, 30000.f),
		/*MarginRatio=*/1.0f, ZoomMinCm, SiteMapZoomCeilingCm());
	FocusedBuildingId = NAME_None;
	bSiteMapView = false;
	LastActionText = LOCTEXT("WatchRunway",
		"WATCHING THE RUNWAY").ToString();
}

bool ALBSpacecraftPlayerPawn::FocusSite()
{
	const ALBSpacecraftGameMode* GameMode =
		ALBSpacecraftGameMode::FindInWorld(GetWorld());
	if (GameMode == nullptr || GameMode->GetBuildAuthority() == nullptr)
	{
		// NOT a no-op any more. This silently doing nothing at startup
		// is what shipped a game that could not be started: the opening
		// view stayed off the site map, the menu offered stations for a
		// factory that did not exist, and the ship factory could not be
		// placed at all.
		return false;
	}
	const TArray<FLBSpacecraftStationRecord>& Stations =
		GameMode->GetBuildAuthority()->GetStations();
	if (Stations.Num() == 0)
	{
		// AN EMPTY SITE IS THE OPENING VIEW (owner 2026-08-28: the game
		// starts on the world map). It frames the whole plot the player
		// is about to place their ship factory on - boot framing put
		// the camera down among the floor tiles, which reads as being
		// inside a building that does not exist yet.
		SetActorLocation(FVector::ZeroVector);
		DesiredZoomCm = ComputeFramingZoomCm(
			FVector2D(ALBSpacecraftBuildAuthority::SiteHalfExtentCm() * 2.f,
				ALBSpacecraftBuildAuthority::SiteHalfExtentCm() * 2.f),
			/*MarginRatio=*/1.15f, ZoomMinCm, SiteMapZoomCeilingCm());
		FocusedBuildingId = NAME_None;
		bSiteMapView = true;
		return true;
	}
	FVector2D Lo(FLT_MAX, FLT_MAX);
	FVector2D Hi(-FLT_MAX, -FLT_MAX);
	for (const FLBSpacecraftStationRecord& Record : Stations)
	{
		const FVector Location = Record.WorldTransform.GetLocation();
		Lo.X = FMath::Min(Lo.X, static_cast<float>(Location.X));
		Lo.Y = FMath::Min(Lo.Y, static_cast<float>(Location.Y));
		Hi.X = FMath::Max(Hi.X, static_cast<float>(Location.X));
		Hi.Y = FMath::Max(Hi.Y, static_cast<float>(Location.Y));
	}
	// THE MAP IS CENTRED ON THE SITE, not on whatever happens to be
	// built yet: a world map that recentres itself every time a
	// building goes up is a map you cannot learn. The site is the
	// fixed thing; the buildings move around on it.
	SetActorLocation(FVector::ZeroVector);
	// The SITE view has to show the plot, not the hall: the dressed
	// floor is 220 m across while the player's zoom ceiling is 160 m,
	// so a site framed within play-zoom can never show its own walls,
	// let alone the ground beyond them - which is what made the first
	// "site map" screenshot read as an indoor floor. The map state
	// gets its own ceiling; play zoom stays clamped as before.
	const float SiteHalfExtentCm =
		ALBSpacecraftBuildAuthority::SiteHalfExtentCm();
	FVector2D SiteExtent = Hi - Lo;
	SiteExtent.X = FMath::Max(SiteExtent.X, SiteHalfExtentCm * 2.f);
	SiteExtent.Y = FMath::Max(SiteExtent.Y, SiteHalfExtentCm * 2.f);
	DesiredZoomCm = ComputeFramingZoomCm(SiteExtent,
		/*MarginRatio=*/1.35f, ZoomMinCm, SiteMapZoomCeilingCm());
	FocusedBuildingId = NAME_None;
	bSiteMapView = true;
	LastActionText = LOCTEXT("SiteMap",
		"SITE MAP - CLICK A BUILDING TO ENTER IT").ToString();
	return true;
}

void ALBSpacecraftPlayerPawn::HandleSiteMap()
{
	FocusSite();
}

float ALBSpacecraftPlayerPawn::ComputeFramingZoomCm(
	const FVector2D& ExtentCm, float MarginRatio, float MinZoomCm,
	float MaxZoomCm)
{
	// FOV 48 (the framing law every formula assumes): the boom must
	// stand far enough back that the footprint's larger side fits the
	// frustum, with margin for context. Half-angle 24 degrees; the
	// pitch-35 foreshortening on the depth axis is folded into the
	// margin rather than modelled - this is a framing heuristic the
	// owner tunes by eye, not projection maths pretending precision.
	const float HalfAngleTan = FMath::Tan(FMath::DegreesToRadians(24.f));
	const float Span = FMath::Max(100.f,
		FMath::Max(FMath::Abs(ExtentCm.X), FMath::Abs(ExtentCm.Y)));
	const float Distance = MarginRatio * Span * 0.5f / HalfAngleTan;
	return FMath::Clamp(Distance, MinZoomCm, MaxZoomCm);
}

void ALBSpacecraftPlayerPawn::UpdateGhost()
{
	using namespace LBSpacecraftPlayerPawnPrivate;
	const FLBSpacecraftStationDefinition* Definition =
		PlacementDefinitionId.IsNone() ? nullptr
			: ALBSpacecraftBuildAuthority::FindDefinition(
				PlacementDefinitionId);
	FVector FloorPoint;
	const bool bShow =
		Definition != nullptr && CursorToFloor(FloorPoint);
	if (!bShow)
	{
		if (PlacementGhost != nullptr)
		{
			PlacementGhost->SetVisibility(false);
		}
		for (UStaticMeshComponent* Line : PlacementGridLines)
		{
			if (Line != nullptr)
			{
				Line->SetVisibility(false);
			}
		}
		return;
	}
	if (PlacementGhost == nullptr)
	{
		UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr,
			SpacecraftGhostCubePath);
		if (Cube == nullptr)
		{
			return;
		}
		PlacementGhost = NewObject<UStaticMeshComponent>(this,
			UStaticMeshComponent::StaticClass(), TEXT("PlacementGhost"));
		PlacementGhost->SetStaticMesh(Cube);
		PlacementGhost->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		PlacementGhost->SetCastShadow(false);
		PlacementGhost->SetAbsolute(true, true, true);
		PlacementGhost->SetupAttachment(RootComponent);
		PlacementGhost->RegisterComponent();
		if (UMaterialInterface* ShapeMaterial =
			LoadObject<UMaterialInterface>(nullptr,
				SpacecraftGhostMaterialPath))
		{
			UMaterialInstanceDynamic* MID =
				UMaterialInstanceDynamic::Create(ShapeMaterial,
					PlacementGhost);
			MID->SetVectorParameterValue(TEXT("Color"),
				SpacecraftGhostColour);
			PlacementGhost->SetMaterial(0, MID);
		}
	}
	const FVector Snapped = SnapToBuildGrid(FloorPoint,
		ALBSpacecraftBuildAuthority::GetPlacementGridCm());
	// THE GRID SHOWS WHILE PLACING (owner 2026-09-01, and every
	// benchmark does it): 100 cm build-grid strips around the cursor so
	// snapping is visible before the click rather than discovered after.
	{
		const float GridCm =
			ALBSpacecraftBuildAuthority::GetPlacementGridCm();
		constexpr int32 GridHalfLines = 6;
		constexpr int32 GridLineCount = (GridHalfLines * 2 + 1) * 2;
		const float GridSpanCm = GridHalfLines * 2 * GridCm;
		if (PlacementGridLines.Num() == 0)
		{
			UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr,
				SpacecraftGhostCubePath);
			UMaterialInterface* ShapeMaterial =
				LoadObject<UMaterialInterface>(nullptr,
					SpacecraftGhostMaterialPath);
			for (int32 Index = 0;
				Cube != nullptr && Index < GridLineCount; ++Index)
			{
				UStaticMeshComponent* Line =
					NewObject<UStaticMeshComponent>(this,
						UStaticMeshComponent::StaticClass());
				Line->SetStaticMesh(Cube);
				Line->SetCollisionEnabled(
					ECollisionEnabled::NoCollision);
				Line->SetCastShadow(false);
				Line->SetAbsolute(true, true, true);
				Line->SetupAttachment(RootComponent);
				Line->RegisterComponent();
				if (ShapeMaterial != nullptr)
				{
					UMaterialInstanceDynamic* LineMID =
						UMaterialInstanceDynamic::Create(
							ShapeMaterial, Line);
					LineMID->SetVectorParameterValue(TEXT("Color"),
						FLinearColor(0.55f, 0.53f, 0.51f, 0.30f));
					Line->SetMaterial(0, LineMID);
				}
				PlacementGridLines.Add(Line);
			}
		}
		// Centre the grid on the snapped cell so the lines hold still
		// while the cursor slides within a cell.
		for (int32 Index = 0; Index < PlacementGridLines.Num(); ++Index)
		{
			UStaticMeshComponent* Line = PlacementGridLines[Index];
			if (Line == nullptr)
			{
				continue;
			}
			const bool bAlongX = Index < GridLineCount / 2;
			const int32 Offset =
				(Index % (GridHalfLines * 2 + 1)) - GridHalfLines;
			FVector Location = Snapped;
			FVector Scale;
			if (bAlongX)
			{
				Location.Y += Offset * GridCm;
				Scale = FVector(GridSpanCm / 100.f, 0.03f, 0.01f);
			}
			else
			{
				Location.X += Offset * GridCm;
				Scale = FVector(0.03f, GridSpanCm / 100.f, 0.01f);
			}
			Location.Z = 2.f;
			Line->SetWorldTransform(FTransform(
				FRotator::ZeroRotator, Location, Scale));
			Line->SetVisibility(true);
		}
	}
	// Polish (owner 2026-08-25): the ghost carries a verdict - blue
	// where the placement would be accepted, warning orange where the
	// fail-closed refusal would fire (land, bounds, funds).
	bool bWouldPlace = true;
	if (ALBSpacecraftGameMode* GhostGameMode = GetSpacecraftGameMode())
	{
		FString GhostReason;
		if (GhostGameMode->GetProgression() != nullptr
			&& !GhostGameMode->GetProgression()->IsFootprintOwned(
				Snapped, Definition->FootprintCm, GhostReason))
		{
			bWouldPlace = false;
		}
		const float HalfX = Definition->FootprintCm.X * 0.5f;
		const float HalfY = Definition->FootprintCm.Y * 0.5f;
		const float Bound =
			ALBSpacecraftBuildAuthority::SiteHalfExtentCm();
		if (FMath::Abs(Snapped.X) + HalfX > Bound
			|| FMath::Abs(Snapped.Y) + HalfY > Bound)
		{
			bWouldPlace = false;
		}
		if (GhostGameMode->GetProductionAuthority() != nullptr
			&& GhostGameMode->GetProductionAuthority()->GetCashPence()
				< Definition->CostPence)
		{
			bWouldPlace = false;
		}
	}
	if (UMaterialInstanceDynamic* GhostMID =
		Cast<UMaterialInstanceDynamic>(PlacementGhost->GetMaterial(0)))
	{
		GhostMID->SetVectorParameterValue(TEXT("Color"), bWouldPlace
			? SpacecraftGhostColour : SpacecraftGhostRefusedColour);
	}
	FTransform GhostTransform(FRotator(0.f, GhostYawDeg, 0.f),
		Snapped + FVector(0.f, 0.f, SpacecraftGhostHeightCm * 0.5f));
	GhostTransform.SetScale3D(FVector(
		Definition->FootprintCm.X / 100.f,
		Definition->FootprintCm.Y / 100.f,
		SpacecraftGhostHeightCm / 100.f));
	PlacementGhost->SetVisibility(true);
	PlacementGhost->SetWorldTransform(GhostTransform);
}

void ALBSpacecraftPlayerPawn::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	// THE OPENING VIEW, kept trying until it takes. BeginPlay asks for
	// it, but the pawn can boot before the game mode has its
	// authorities - in a PACKAGED build it does, FocusSite returned
	// early, and the player was left with a station menu for a factory
	// that did not exist and no way to place one. The game could not be
	// started at all.
	//
	// Cheap: one bool, and the moment it takes this never runs again.
	if (!bOpeningViewFramed)
	{
		bOpeningViewFramed = FocusSite();
		if (bOpeningViewFramed && CameraBoom != nullptr)
		{
			CameraBoom->TargetArmLength = DesiredZoomCm;
		}
	}
	if (CameraBoom != nullptr)
	{
		CameraBoom->TargetArmLength = FMath::FInterpTo(
			CameraBoom->TargetArmLength, DesiredZoomCm, DeltaSeconds, 10.f);
	}
	TickDragPan();
	TickEdgeScroll(DeltaSeconds);
	UpdateGhost();
}

#undef LOCTEXT_NAMESPACE
