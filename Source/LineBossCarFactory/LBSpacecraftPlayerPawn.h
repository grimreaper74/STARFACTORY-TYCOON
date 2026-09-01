// Spacecraft-era player pawn: the proven 2.5D camera contract (pivot +
// spring arm, pitch -35, FOV 48 near-isometric perspective, zoom clamps,
// WASD pan, quarter-turn-friendly rotate) in a lean spacecraft-only pawn,
// plus click-to-build: a grid-snapped ghost follows the cursor while a
// station family is armed, left-click places through the game mode's
// powered placement (research gate, supply/store wiring, power draw),
// and every refusal reason is surfaced to the command panel - the
// fail-closed strings ARE the player feedback.
//
// The bindings are the FLBSpacecraftInputMap scheme (the Car Manufacture
// adoption, owner 2026-08-26): WASD/edge/MMB-drag pan, Q/E rotate,
// wheel + C/V zoom (settings-scaled, invertible), LMB select/place,
// RMB cancel/deselect, Z/X + R/F ghost rotation, Home camera reset,
// 1/2/3/4 factory speed, Tab panel cycling, F5/F9 quick save/load.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "LBSpacecraftPlayerPawn.generated.h"

class UCameraComponent;
class USpringArmComponent;
class UStaticMeshComponent;
class ALBSpacecraftGameMode;

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftPlayerPawn : public APawn
{
	GENERATED_BODY()

public:
	ALBSpacecraftPlayerPawn();

	virtual void Tick(float DeltaSeconds) override;
	virtual void BeginPlay() override;

	virtual void SetupPlayerInputComponent(
		UInputComponent* PlayerInputComponent) override;

	/** Arms placement of a station family; NAME_None disarms. */
	void SetPlacementDefinition(FName DefinitionId);
	FName GetPlacementDefinition() const { return PlacementDefinitionId; }


	/** The station record under the cursor, if any (pure footprint test
	 *  against the build authority's records - no collision needed). */
	FName FindStationUnderCursor() const;

	/** Last action feedback (placement result, selection, refusal). */
	const FString& GetLastActionText() const { return LastActionText; }

	/** Selected placed station (for the panel's station view). */
	FName GetSelectedStation() const { return SelectedStationId; }

	/** THE SITE MAP (owner 2026-08-27: "it's just a map and you click
	 *  on building to enter"). Clicking a slot-host BUILDING flies the
	 *  camera to frame it - that is entering; the panel already scopes
	 *  to the building's slots on selection. M pulls back to frame the
	 *  whole site. Line stations select without the camera jumping,
	 *  because managing the line means clicking along it constantly. */
	void FocusStation(FName StationId);
	/** Frames the whole site. Returns FALSE when it could not run
	 *  because the authorities are not up yet - the caller is expected
	 *  to ask again rather than assume the view was set. */
	bool FocusSite();

	/** Frames the RUNWAY - the strip a finished craft self-starts on,
	 *  swings the chicane and sprints out of (owner's signature moment:
	 *  "every delivery is a show"). Its own framing because the launch
	 *  happens at the site's edge while the player is usually looking
	 *  at the line. */
	void FocusRunway();

	/** Frames ONE station and holds the camera at the given range -
	 *  the close-up a dev capture needs. Entering a 160 m hall frames
	 *  the whole floor, at which range a 3 m drone is a speck, so a
	 *  visual claim about what the crew is doing cannot be made from
	 *  there. Selects the station too, so the panel shows its page. */
	void WatchStation(FName StationId, float ZoomCm);

	FName GetFocusedBuilding() const { return FocusedBuildingId; }

	/** Camera state, for dev diagnostics: the arm the boom is ACTUALLY
	 *  at, the length it is heading for, and the field of view. The
	 *  three disagree exactly when something is overriding the zoom. */
	float GetCameraArmLengthCm() const;
	float GetDesiredZoomCm() const { return DesiredZoomCm; }
	float GetCameraFovDeg() const;

	/** True while the camera is in the SITE MAP state (owner
	 *  2026-08-27: "the map should be the full building meshes").
	 *  The presenter keys the building-shell layer on this: shells
	 *  stand and hide their interiors on the map, lift when you enter. */
	bool IsSiteMapView() const { return bSiteMapView; }

	/** Boom length that frames a footprint under the FOV-48 camera,
	 *  with margin. Pure and monotonic: a bigger footprint always
	 *  frames from further out, clamped into the zoom range so a
	 *  focused view is always a legal camera state. */
	static float ComputeFramingZoomCm(const FVector2D& ExtentCm,
		float MarginRatio, float MinZoomCm, float MaxZoomCm);

	/** The zoom ceiling the MAP states use. Play zoom stays clamped to
	 *  ZoomMaxCm; the site map and a site building's interior framing
	 *  both need to pull back past it. Sized so the WHOLE 600 m site
	 *  fits the frame (owner 2026-08-28: the world map is where the
	 *  parts factory and power plant will stand beside the ship
	 *  factory, and a map you cannot see all of is not a map). */
	static constexpr float SiteMapZoomCeilingCm() { return 85000.f; }
	void ClearSelectedStation() { SelectedStationId = NAME_None; }
	/** Panel rows select stations too (the split list). */
	void SetSelectedStation(FName StationId)
	{
		SelectedStationId = StationId;
	}

	/** Returns the camera to the boot framing (position, yaw, zoom). */
	void ResetCameraFraming();

	/** The boot framing contract shared with BeginPlay and tests. */
	static FVector GetBootFramingLocation() { return FVector(-6800.f, -1500.f, 0.f); }
	static float GetBootFramingZoomCm() { return 6500.f; }

	// ---- pure, testable helpers ----
	/** Snaps a floor point to the build grid (Z forced to the datum). */
	static FVector SnapToBuildGrid(const FVector& FloorPoint, float GridCm);

	/** Does a station's rotated footprint contain a floor point? */
	static bool StationContainsPoint(const FTransform& StationTransform,
		const FVector2D& FootprintCm, const FVector& FloorPoint);

	/** Edge-scroll direction for a cursor position in a viewport: each
	 *  component is -1/0/+1 when the cursor sits within MarginPx of that
	 *  edge. X is screen-right, Y is screen-down. Off-viewport cursors
	 *  scroll nothing (windowed play must not creep). */
	static FIntPoint ComputeEdgeScrollDirection(const FVector2D& CursorPx,
		const FVector2D& ViewportPx, float MarginPx);

private:
	UPROPERTY(VisibleAnywhere, Category = "LineBoss")
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, Category = "LineBoss")
	TObjectPtr<UCameraComponent> Camera;

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> PlacementGhost;

	/** PLACEMENT GRID (owner 2026-09-01 + benchmark research: a grid
	 *  shows during placement). Thin translucent strips on the 100 cm
	 *  build grid around the ghost; visible only while placing. */
	TArray<TObjectPtr<UStaticMeshComponent>> PlacementGridLines;


	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float ZoomMinCm = 2500.f;

	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float ZoomMaxCm = 16000.f;

	/** Pixels from a viewport edge that count as edge-scroll ground. */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	float EdgeScrollMarginPx = 12.f;

	FName PlacementDefinitionId;
	FName SelectedStationId;

	/** The building the camera last flew into, NAME_None on the site
	 *  view. Presentation state only - deliberately NOT saved: a load
	 *  reopens on the site, which is the honest default. */
	FName FocusedBuildingId;

	bool bSiteMapView = false;

	/** Has the OPENING view actually been framed?
	 *
	 *  BeginPlay asks FocusSite to open on the world map, but FocusSite
	 *  needs the build authority and the pawn can boot first. In a
	 *  packaged build it did, the call silently did nothing, and the
	 *  player was left looking at a station menu for a factory that did
	 *  not exist - with no way to place one. The opening view must not
	 *  depend on winning that race, so this stays false until the
	 *  framing really happened and the tick keeps trying. */
	bool bOpeningViewFramed = false;
	float DesiredZoomCm = 9000.f;
	float GhostYawDeg = 0.f;
	FString LastActionText;

	/** MMB drag-pan state: while held, the floor point grabbed at the
	 *  previous tick stays glued to the cursor. */
	bool bDragPanActive = false;
	bool bDragAnchorValid = false;
	FVector DragAnchorFloor = FVector::ZeroVector;

	void MoveForward(float Value);
	void MoveRight(float Value);
	void Rotate(float Value);
	void Zoom(float Value);
	void ZoomKeys(float Value);
	void RotateGhost();
	void RotateGhostBack();
	void PrimaryClick();
	void SecondaryClick();
	void CancelPlacement();
	void HandleSiteMap();
	void DragPanPressed();
	void DragPanReleased();
	/** Escape: cancel placement, else toggle the pause menu. */
	void EscapePressed();
	void SpeedPause();
	void SpeedNormal();
	void SpeedFast();
	void SpeedFastest();
	void PanelNextTab();
	void PanelPrevTab();
	void QuickSavePressed();
	void QuickLoadPressed();

	/** Pan on the floor plane in camera-yaw space, settings-scaled. */
	void PanCamera(float ForwardValue, float RightValue);
	void ApplyZoomDelta(float Value);
	void TickEdgeScroll(float DeltaSeconds);
	void TickDragPan();
	void SetSimSpeedWithToast(float Scale);
	float GetPanSpeedScale() const;

	/** Cursor ray intersected with the Z=0 floor plane. */
	bool CursorToFloor(FVector& OutFloorPoint) const;

	ALBSpacecraftGameMode* GetSpacecraftGameMode() const;
	void UpdateGhost();
};
