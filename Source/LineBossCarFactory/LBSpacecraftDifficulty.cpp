#include "LBSpacecraftDifficulty.h"

#define LOCTEXT_NAMESPACE "LineBossSpacecraftDifficulty"

namespace LBSpacecraftDifficultyPrivate
{
	// Unity-build safety: the chosen difficulty, qualified by subject.
	ELBSpacecraftDifficulty SpacecraftChosenDifficulty =
		ELBSpacecraftDifficulty::Standard;
}

FLBSpacecraftDifficultyRules FLBSpacecraftDifficulty::RulesFor(
	ELBSpacecraftDifficulty Difficulty)
{
	FLBSpacecraftDifficultyRules Rules;
	switch (Difficulty)
	{
	case ELBSpacecraftDifficulty::Relaxed:
		// Room to make mistakes: nearly double the opening balance,
		// half again as long to deliver, a hover test that tolerates
		// real sloppiness, and lateness that stings rather than bites.
		Rules.StartingCapitalPence = 160000000;
		Rules.DeadlineScale = 1.6f;
		Rules.HoverTestDefectTolerance = 3;
		Rules.LatePenaltyScale = 0.5f;
		Rules.ContractPriceScale = 1.15f;
		break;

	case ELBSpacecraftDifficulty::Demanding:
		// Thin margins and no forgiveness: only clean work flies, so
		// under-crewing a station is felt immediately.
		Rules.StartingCapitalPence = 60000000;
		Rules.DeadlineScale = 0.7f;
		Rules.HoverTestDefectTolerance = 0;
		Rules.LatePenaltyScale = 1.5f;
		Rules.ContractPriceScale = 0.85f;
		break;

	case ELBSpacecraftDifficulty::Standard:
	default:
		// The shipped numbers, unchanged - Standard is the game as it
		// was tuned, not a modifier applied to it.
		break;
	}
	return Rules;
}

ELBSpacecraftDifficulty FLBSpacecraftDifficulty::GetCurrent()
{
	return LBSpacecraftDifficultyPrivate::SpacecraftChosenDifficulty;
}

void FLBSpacecraftDifficulty::SetCurrent(ELBSpacecraftDifficulty Difficulty)
{
	LBSpacecraftDifficultyPrivate::SpacecraftChosenDifficulty = Difficulty;
}

FText FLBSpacecraftDifficulty::DisplayName(
	ELBSpacecraftDifficulty Difficulty)
{
	switch (Difficulty)
	{
	case ELBSpacecraftDifficulty::Relaxed:
		return LOCTEXT("DifficultyRelaxed", "RELAXED");
	case ELBSpacecraftDifficulty::Demanding:
		return LOCTEXT("DifficultyDemanding", "DEMANDING");
	case ELBSpacecraftDifficulty::Standard:
	default:
		return LOCTEXT("DifficultyStandard", "STANDARD");
	}
}

const TArray<ELBSpacecraftDifficulty>& FLBSpacecraftDifficulty::All()
{
	static const TArray<ELBSpacecraftDifficulty> Order = {
		ELBSpacecraftDifficulty::Relaxed,
		ELBSpacecraftDifficulty::Standard,
		ELBSpacecraftDifficulty::Demanding };
	return Order;
}

#undef LOCTEXT_NAMESPACE
