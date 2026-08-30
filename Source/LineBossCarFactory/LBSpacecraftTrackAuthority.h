// Spacecraft-era LINE TRACK authority (owner 2026-08-26, the Car
// Manufacture construction model: conveyors laid from typed elements,
// stations attached as nodes, products riding the path, unfinished
// track a NAMED problem). Single owner of the laid track and its
// station nodes; the coordinator derives the production route from a
// COMPLETE track when one exists, and the presenter renders the pieces.
//
// v001 lays as a CHAIN: a Start piece anchors the line, every further
// piece appends at the open end (position and direction derived - the
// chain can never be discontinuous), End caps it. Removal is from the
// open end only. Fail-closed everywhere; snapshot validated whole.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBSpacecraftTrackAuthority.generated.h"

class ALBSpacecraftBuildAuthority;

UENUM(BlueprintType)
enum class ELBSpacecraftTrackPiece : uint8
{
	Start = 0,
	Straight,
	TurnLeft,
	TurnRight,
	End
};

USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftTrackPieceRecord
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName PieceId;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	ELBSpacecraftTrackPiece PieceType = ELBSpacecraftTrackPiece::Straight;

	/** Piece centre on the grid; yaw is the piece's ENTRY direction. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FTransform WorldTransform = FTransform::Identity;

	/** The line station attached to this piece (None = plain track). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	FName NodeStationId;
};

USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftTrackSnapshot
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	TArray<FLBSpacecraftTrackPieceRecord> Pieces;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss", SaveGame)
	int32 NextPieceSequence = 1;
};

UCLASS()
class LINEBOSSCARFACTORY_API ALBSpacecraftTrackAuthority : public AActor
{
	GENERATED_BODY()

public:
	/** Each piece spans one 400 cm track cell. */
	static float GetPieceLengthCm() { return 400.f; }

	/** PROVISIONAL: cost per laid piece (the belt economy's cousin). */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int64 PieceCostPence = 60000;

	/** Max station nodes one line carries (upgrade path later, the
	 *  Car Manufacture ChangeConveyorMaxStationsCount model). */
	UPROPERTY(EditAnywhere, Category = "LineBoss")
	int32 MaxNodes = 8;

	/** Anchors the line: refused when a track already exists or the
	 *  transform is off-grid. Yaw is the build direction. */
	bool StartLine(const FTransform& Transform, FName& OutPieceId,
		FString& OutReason);

	/** Appends a piece at the open end (position/direction derived -
	 *  the chain stays continuous by construction). Refused after the
	 *  End cap, before a Start exists, or off the buildable floor. */
	bool ExtendLine(ELBSpacecraftTrackPiece PieceType, FName& OutPieceId,
		FString& OutReason);

	/** Removes the open-end piece (LIFO keeps the chain valid). */
	bool RemoveOpenEnd(FString& OutReason);

	/** Attaches a placed line station to a STRAIGHT piece as a node.
	 *  Refused off straight pieces, past MaxNodes, on a taken piece,
	 *  or for a station already attached elsewhere. */
	bool AttachStationNode(FName StationId, FName PieceId,
		const ALBSpacecraftBuildAuthority* InBuild, FString& OutReason);

	/** Detaches a station's node. */
	bool DetachStationNode(FName StationId, FString& OutReason);

	/** Start laid AND End capped - only then does the coordinator
	 *  route from the track. */
	bool IsComplete() const;

	/** The named problem when the line is not usable (the Car
	 *  Manufacture problem-system model); empty when complete. */
	FString DescribeProblem() const;

	/** Station ids in TRACK order (the production route order). */
	TArray<FName> GetNodeStationsInOrder() const;

	const TArray<FLBSpacecraftTrackPieceRecord>& GetPieces() const
	{
		return Track.Pieces;
	}

	/** The open end's exit transform (where the next piece lands). */
	bool GetOpenEndExit(FTransform& OutExit) const;

	FLBSpacecraftTrackSnapshot CaptureSnapshot() const { return Track; }
	bool ValidateSnapshot(const FLBSpacecraftTrackSnapshot& Snapshot,
		FString& OutReason) const;
	bool RestoreSnapshot(const FLBSpacecraftTrackSnapshot& Snapshot,
		FString& OutReason);

	/** Pure: a piece's exit transform from its entry transform and
	 *  type (turns rotate the direction by 90 degrees). */
	static FTransform ComputePieceExit(const FTransform& Entry,
		ELBSpacecraftTrackPiece PieceType);

private:
	UPROPERTY(SaveGame)
	FLBSpacecraftTrackSnapshot Track;
};
