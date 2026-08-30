#include "LBSpacecraftTrackAuthority.h"

#include "LBSpacecraftBuildAuthority.h"

namespace LBSpacecraftTrackAuthorityPrivate
{
	// Unity-build safety: helpers qualified by subject.
	bool SpacecraftTrackTransformLegal(const FTransform& Transform,
		FString& OutReason)
	{
		const FVector Location = Transform.GetLocation();
		if (!FMath::IsNearlyZero(Location.Z, 0.01f))
		{
			OutReason = TEXT("TRACK LIES ON THE FLOOR DATUM Z=0");
			return false;
		}
		if (!FMath::IsNearlyZero(
				FMath::Fmod(Location.X, 100.f), 0.01f)
			|| !FMath::IsNearlyZero(
				FMath::Fmod(Location.Y, 100.f), 0.01f))
		{
			OutReason = TEXT("TRACK SNAPS TO THE 100 CM GRID");
			return false;
		}
		const float Yaw = FMath::Fmod(
			FMath::Abs(Transform.Rotator().Yaw) + 360.f, 90.f);
		if (Yaw > 0.1f && 90.f - Yaw > 0.1f)
		{
			OutReason = TEXT("TRACK RUNS IN 90 DEGREE STEPS ONLY");
			return false;
		}
		if (FMath::Abs(Location.X) > 11000.f
			|| FMath::Abs(Location.Y) > 11000.f)
		{
			OutReason = TEXT("TRACK LEAVES THE BUILDABLE FLOOR");
			return false;
		}
		OutReason.Reset();
		return true;
	}
}

FTransform ALBSpacecraftTrackAuthority::ComputePieceExit(
	const FTransform& Entry, ELBSpacecraftTrackPiece PieceType)
{
	// The exit sits one piece-length along the piece's OUT direction;
	// turns rotate the direction a quarter turn at the piece centre.
	float YawDelta = 0.f;
	if (PieceType == ELBSpacecraftTrackPiece::TurnLeft)
	{
		YawDelta = -90.f;
	}
	else if (PieceType == ELBSpacecraftTrackPiece::TurnRight)
	{
		YawDelta = 90.f;
	}
	FRotator OutRotation = Entry.Rotator();
	OutRotation.Yaw = FRotator::NormalizeAxis(
		OutRotation.Yaw + YawDelta);
	const FVector OutDirection =
		FRotationMatrix(OutRotation).GetUnitAxis(EAxis::X);
	FTransform Exit;
	Exit.SetRotation(OutRotation.Quaternion());
	Exit.SetLocation(Entry.GetLocation()
		+ OutDirection * GetPieceLengthCm());
	return Exit;
}

bool ALBSpacecraftTrackAuthority::StartLine(const FTransform& Transform,
	FName& OutPieceId, FString& OutReason)
{
	using namespace LBSpacecraftTrackAuthorityPrivate;
	OutPieceId = NAME_None;
	if (Track.Pieces.Num() > 0)
	{
		OutReason = TEXT("THE LINE IS ALREADY STARTED - EXTEND IT");
		return false;
	}
	if (!SpacecraftTrackTransformLegal(Transform, OutReason))
	{
		return false;
	}
	FLBSpacecraftTrackPieceRecord Piece;
	Piece.PieceId = FName(*FString::Printf(TEXT("TRACK-%03d"),
		Track.NextPieceSequence));
	Piece.PieceType = ELBSpacecraftTrackPiece::Start;
	Piece.WorldTransform = Transform;
	Track.Pieces.Add(Piece);
	++Track.NextPieceSequence;
	OutPieceId = Piece.PieceId;
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftTrackAuthority::ExtendLine(
	ELBSpacecraftTrackPiece PieceType, FName& OutPieceId,
	FString& OutReason)
{
	using namespace LBSpacecraftTrackAuthorityPrivate;
	OutPieceId = NAME_None;
	if (PieceType == ELBSpacecraftTrackPiece::Start)
	{
		OutReason = TEXT("A LINE HAS ONE START - USE StartLine");
		return false;
	}
	if (Track.Pieces.Num() == 0)
	{
		OutReason = TEXT("START THE LINE FIRST");
		return false;
	}
	if (Track.Pieces.Last().PieceType == ELBSpacecraftTrackPiece::End)
	{
		OutReason = TEXT("THE LINE IS CAPPED - REMOVE THE END TO GROW");
		return false;
	}
	FTransform Entry;
	if (!GetOpenEndExit(Entry))
	{
		OutReason = TEXT("THE LINE HAS NO OPEN END");
		return false;
	}
	if (!SpacecraftTrackTransformLegal(Entry, OutReason))
	{
		return false;
	}
	// The chain never crosses itself: the new cell must be free.
	for (const FLBSpacecraftTrackPieceRecord& Existing : Track.Pieces)
	{
		if (Existing.WorldTransform.GetLocation().Equals(
			Entry.GetLocation(), 1.f))
		{
			OutReason = TEXT("THE LINE WOULD CROSS ITSELF");
			return false;
		}
	}
	FLBSpacecraftTrackPieceRecord Piece;
	Piece.PieceId = FName(*FString::Printf(TEXT("TRACK-%03d"),
		Track.NextPieceSequence));
	Piece.PieceType = PieceType;
	Piece.WorldTransform = Entry;
	Track.Pieces.Add(Piece);
	++Track.NextPieceSequence;
	OutPieceId = Piece.PieceId;
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftTrackAuthority::RemoveOpenEnd(FString& OutReason)
{
	if (Track.Pieces.Num() == 0)
	{
		OutReason = TEXT("THERE IS NO LINE TO REMOVE");
		return false;
	}
	if (!Track.Pieces.Last().NodeStationId.IsNone())
	{
		OutReason = FString::Printf(
			TEXT("DETACH STATION %s FROM THE PIECE FIRST"),
			*Track.Pieces.Last().NodeStationId.ToString());
		return false;
	}
	Track.Pieces.Pop();
	OutReason.Reset();
	return true;
}

bool ALBSpacecraftTrackAuthority::AttachStationNode(FName StationId,
	FName PieceId, const ALBSpacecraftBuildAuthority* InBuild,
	FString& OutReason)
{
	if (InBuild == nullptr || InBuild->FindStation(StationId) == nullptr)
	{
		OutReason = FString::Printf(TEXT("UNKNOWN STATION %s"),
			*StationId.ToString());
		return false;
	}
	int32 Nodes = 0;
	for (const FLBSpacecraftTrackPieceRecord& Piece : Track.Pieces)
	{
		if (!Piece.NodeStationId.IsNone())
		{
			++Nodes;
			if (Piece.NodeStationId == StationId)
			{
				OutReason = FString::Printf(
					TEXT("%s IS ALREADY ON THE LINE"),
					*StationId.ToString());
				return false;
			}
		}
	}
	if (Nodes >= MaxNodes)
	{
		OutReason = FString::Printf(
			TEXT("THE LINE CARRIES %d NODES AT MOST"), MaxNodes);
		return false;
	}
	for (FLBSpacecraftTrackPieceRecord& Piece : Track.Pieces)
	{
		if (Piece.PieceId != PieceId)
		{
			continue;
		}
		if (Piece.PieceType != ELBSpacecraftTrackPiece::Straight)
		{
			OutReason = TEXT(
				"STATIONS ATTACH TO STRAIGHT TRACK ONLY");
			return false;
		}
		if (!Piece.NodeStationId.IsNone())
		{
			OutReason = FString::Printf(
				TEXT("PIECE %s ALREADY CARRIES %s"),
				*PieceId.ToString(),
				*Piece.NodeStationId.ToString());
			return false;
		}
		Piece.NodeStationId = StationId;
		OutReason.Reset();
		return true;
	}
	OutReason = FString::Printf(TEXT("UNKNOWN TRACK PIECE %s"),
		*PieceId.ToString());
	return false;
}

bool ALBSpacecraftTrackAuthority::DetachStationNode(FName StationId,
	FString& OutReason)
{
	for (FLBSpacecraftTrackPieceRecord& Piece : Track.Pieces)
	{
		if (Piece.NodeStationId == StationId)
		{
			Piece.NodeStationId = NAME_None;
			OutReason.Reset();
			return true;
		}
	}
	OutReason = FString::Printf(TEXT("%s IS NOT ON THE LINE"),
		*StationId.ToString());
	return false;
}

bool ALBSpacecraftTrackAuthority::IsComplete() const
{
	return Track.Pieces.Num() >= 2
		&& Track.Pieces[0].PieceType == ELBSpacecraftTrackPiece::Start
		&& Track.Pieces.Last().PieceType == ELBSpacecraftTrackPiece::End;
}

FString ALBSpacecraftTrackAuthority::DescribeProblem() const
{
	if (Track.Pieces.Num() == 0)
	{
		return TEXT("NO LINE LAID - START THE TRACK");
	}
	if (Track.Pieces.Last().PieceType != ELBSpacecraftTrackPiece::End)
	{
		// The Car Manufacture problem system's END_NOT_SET, ours.
		return TEXT("LINE END NOT SET - CAP THE TRACK");
	}
	return FString();
}

TArray<FName> ALBSpacecraftTrackAuthority::GetNodeStationsInOrder() const
{
	TArray<FName> Out;
	for (const FLBSpacecraftTrackPieceRecord& Piece : Track.Pieces)
	{
		if (!Piece.NodeStationId.IsNone())
		{
			Out.Add(Piece.NodeStationId);
		}
	}
	return Out;
}

bool ALBSpacecraftTrackAuthority::GetOpenEndExit(
	FTransform& OutExit) const
{
	if (Track.Pieces.Num() == 0)
	{
		return false;
	}
	const FLBSpacecraftTrackPieceRecord& Last = Track.Pieces.Last();
	OutExit = ComputePieceExit(Last.WorldTransform, Last.PieceType);
	return true;
}

bool ALBSpacecraftTrackAuthority::ValidateSnapshot(
	const FLBSpacecraftTrackSnapshot& Snapshot, FString& OutReason) const
{
	using namespace LBSpacecraftTrackAuthorityPrivate;
	TSet<FName> Ids;
	TSet<FName> Stations;
	for (int32 Index = 0; Index < Snapshot.Pieces.Num(); ++Index)
	{
		const FLBSpacecraftTrackPieceRecord& Piece =
			Snapshot.Pieces[Index];
		if (Piece.PieceId.IsNone())
		{
			OutReason = TEXT("A SAVED TRACK PIECE HAS NO ID");
			return false;
		}
		bool bAlready = false;
		Ids.Add(Piece.PieceId, &bAlready);
		if (bAlready)
		{
			OutReason = FString::Printf(
				TEXT("DUPLICATE TRACK PIECE %s"),
				*Piece.PieceId.ToString());
			return false;
		}
		FString TransformReason;
		if (!SpacecraftTrackTransformLegal(Piece.WorldTransform,
			TransformReason))
		{
			OutReason = FString::Printf(TEXT("PIECE %s: %s"),
				*Piece.PieceId.ToString(), *TransformReason);
			return false;
		}
		if (Index == 0 && Piece.PieceType
			!= ELBSpacecraftTrackPiece::Start)
		{
			OutReason = TEXT("SAVED TRACK MUST BEGIN WITH ITS START");
			return false;
		}
		if (Index > 0)
		{
			if (Piece.PieceType == ELBSpacecraftTrackPiece::Start)
			{
				OutReason = TEXT("SAVED TRACK HAS TWO STARTS");
				return false;
			}
			// The chain must be continuous: this piece must sit at
			// the previous piece's exit.
			const FTransform Expected = ComputePieceExit(
				Snapshot.Pieces[Index - 1].WorldTransform,
				Snapshot.Pieces[Index - 1].PieceType);
			if (!Expected.GetLocation().Equals(
				Piece.WorldTransform.GetLocation(), 1.f))
			{
				OutReason = FString::Printf(
					TEXT("SAVED TRACK BREAKS AT PIECE %s"),
					*Piece.PieceId.ToString());
				return false;
			}
			if (Index < Snapshot.Pieces.Num() - 1
				&& Piece.PieceType == ELBSpacecraftTrackPiece::End)
			{
				OutReason = TEXT("SAVED TRACK ENDS MID-CHAIN");
				return false;
			}
		}
		if (!Piece.NodeStationId.IsNone())
		{
			if (Piece.PieceType != ELBSpacecraftTrackPiece::Straight)
			{
				OutReason = FString::Printf(
					TEXT("SAVED NODE %s SITS OFF STRAIGHT TRACK"),
					*Piece.NodeStationId.ToString());
				return false;
			}
			bool bStationAlready = false;
			Stations.Add(Piece.NodeStationId, &bStationAlready);
			if (bStationAlready)
			{
				OutReason = FString::Printf(
					TEXT("SAVED STATION %s NODES TWICE"),
					*Piece.NodeStationId.ToString());
				return false;
			}
		}
	}
	OutReason = TEXT("SNAPSHOT VALID");
	return true;
}

bool ALBSpacecraftTrackAuthority::RestoreSnapshot(
	const FLBSpacecraftTrackSnapshot& Snapshot, FString& OutReason)
{
	if (!ValidateSnapshot(Snapshot, OutReason))
	{
		return false;
	}
	Track = Snapshot;
	OutReason.Reset();
	return true;
}
