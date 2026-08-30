// Spacecraft-era DIFFICULTY (owner 2026-08-27: "does unreal do a
// difficulty in options as need that in aswell").
//
// Unreal has nothing for this. GameUserSettings covers graphics
// scalability - resolution, shadows, view distance - and gameplay
// difficulty is entirely a game's own business, so this is it.
//
// The whole of difficulty is FIVE NUMBERS, gathered in one place rather
// than scattered as multipliers through the authorities that use them.
// Each was chosen because it is a dial the player actually feels:
// how much rope you start with, how long customers wait, how forgiving
// the hover test is, what failing costs, and what the work pays. Every
// value is PROVISIONAL pending the owner's tuning, like the rest of the
// economy.

#pragma once

#include "CoreMinimal.h"
#include "LBSpacecraftDifficulty.generated.h"

UENUM(BlueprintType)
enum class ELBSpacecraftDifficulty : uint8
{
	/** A factory to potter in: deep pockets, patient customers, and a
	 *  hover test that lets workmanship slide. */
	Relaxed = 0,
	/** The game as designed. */
	Standard,
	/** Thin margins, impatient customers, and a test that passes only
	 *  clean work. */
	Demanding
};

/** What a difficulty actually changes. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftDifficultyRules
{
	GENERATED_BODY()

	/** Opening balance, in hundredths. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int64 StartingCapitalPence = 90000000;

	/** Multiplier on how long a customer allows for an order. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float DeadlineScale = 1.f;

	/** Defects a craft may carry and still pass its hover test. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	int32 HoverTestDefectTolerance = 1;

	/** Multiplier on what missing a deadline costs your name. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float LatePenaltyScale = 1.f;

	/** Multiplier on what a contract pays. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float ContractPriceScale = 1.f;
};

/** The chosen difficulty and the rules it implies.
 *
 *  This is deliberately ONE global: difficulty is a game-wide constant
 *  the player picks once, and threading it through every authority
 *  would be ceremony without meaning. The game mode sets it from the
 *  saved settings at BeginPlay; tests set it directly and put it back. */
class LINEBOSSCARFACTORY_API FLBSpacecraftDifficulty
{
public:
	static FLBSpacecraftDifficultyRules RulesFor(
		ELBSpacecraftDifficulty Difficulty);

	static ELBSpacecraftDifficulty GetCurrent();
	static void SetCurrent(ELBSpacecraftDifficulty Difficulty);

	/** The rules in force right now. */
	static FLBSpacecraftDifficultyRules Current()
	{
		return RulesFor(GetCurrent());
	}

	/** Player-facing name, for the settings page. */
	static FText DisplayName(ELBSpacecraftDifficulty Difficulty);

	/** Every difficulty, in order, for cycling through the option. */
	static const TArray<ELBSpacecraftDifficulty>& All();
};
