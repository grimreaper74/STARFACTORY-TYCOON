// Spacecraft-era HUD top bar: cash, active contract, sim clock and line
// status. A READ-ONLY projection of the authorities - it owns no state,
// creates no records, and formats what the ledger says, nothing more.
// Built entirely in code (native UMG, no Blueprint assets), matching the
// repo's management-widget convention.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "LBSpacecraftBuildAuthority.h"
#include "LBSpacecraftInventoryAuthority.h"
#include "LBSpacecraftPowerAuthority.h"
#include "LBSpacecraftProductionAuthority.h"
#include "LBSpacecraftReputationAuthority.h"
#include "LBSpacecraftResearchAuthority.h"
#include "LBSpacecraftRuntimeCoordinator.h"
#include "LBSpacecraftTopBarWidget.generated.h"

class UTextBlock;
class UHorizontalBox;

/** Everything the top bar shows, computed in one pure pass so it can be
 *  tested without Slate. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBSpacecraftHUDSnapshot
{
	GENERATED_BODY()

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString CashText;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString ContractText;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString ClockText;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString LineStatusText;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString PowerText;

	/** The grid trade state (owner 2026-08-26, Car Manufacture model):
	 *  "SELLING n kW" / "BUYING n kW" / empty when balanced off-grid. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString PowerTradeText;

	/** Draw as a fraction of available capacity, 0..1, for the gauge. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	float PowerLoad01 = 0.f;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString ResearchText;

	/** The career ladder: "REP T2  12 pts". Reputation gates which
	 *  contracts a customer will trust you with, and until now the
	 *  player could only discover their tier by being refused. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString ReputationText;

	/** Workmanship on the craft at the gate - empty when the line is
	 *  clean, "REWORKING 90s" while a failed craft is being put right,
	 *  "DEFECTS 2" when one is carrying bad fits toward the test. Bad
	 *  news must be visible BEFORE the hover test fails, or the
	 *  penalty reads as bad luck rather than an understaffed line. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	FString QualityText;

	/** True while any craft is in rework, so the bar can warn-colour. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "LineBoss")
	bool bQualityAlarm = false;
};

UCLASS()
class LINEBOSSCARFACTORY_API ULBSpacecraftTopBarWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void BindAuthorities(ALBSpacecraftBuildAuthority* InBuild,
		ALBSpacecraftProductionAuthority* InProduction,
		ALBSpacecraftRuntimeCoordinator* InCoordinator,
		ALBSpacecraftPowerAuthority* InPower = nullptr,
		ALBSpacecraftResearchAuthority* InResearch = nullptr,
		ALBSpacecraftReputationAuthority* InReputation = nullptr);

	// ---- pure, testable projection ----
	/** "50,000 cr" from the ledger's integer hundredths (owner decision
	 *  2026-08-25: neutral CREDITS, never a real-world currency). */
	static FString FormatCurrency(int64 Hundredths);

	/** "01:02:05" from sim seconds (hours:minutes:seconds, clamped >= 0). */
	static FString FormatSimClock(double SimSeconds);

	/** Pure: the workmanship line for the worst craft on the floor.
	 *  Rework outranks defects because it is the worse news, and the
	 *  alarm flag is true whenever the player should act - a craft in
	 *  rework, or one carrying a load the hover test will reject. */
	static FString FormatQualityText(int32 DefectPoints,
		float ReworkSecondsRemaining, bool& bOutAlarm);

	/** One coherent read of the authorities; any null pointer yields the
	 *  honest empty-state texts rather than fabricated numbers. Power and
	 *  research are optional (a pre-Phase-2 caller shows their empty
	 *  states). */
	static FLBSpacecraftHUDSnapshot BuildSnapshot(
		const ALBSpacecraftBuildAuthority* InBuild,
		const ALBSpacecraftProductionAuthority* InProduction,
		const ALBSpacecraftRuntimeCoordinator* InCoordinator,
		const ALBSpacecraftPowerAuthority* InPower = nullptr,
		const ALBSpacecraftResearchAuthority* InResearch = nullptr,
		const ALBSpacecraftReputationAuthority* InReputation = nullptr);

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry,
		float InDeltaTime) override;

private:
	UPROPERTY()
	TObjectPtr<ALBSpacecraftBuildAuthority> BuildAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftProductionAuthority> ProductionAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftRuntimeCoordinator> Coordinator;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftPowerAuthority> PowerAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftResearchAuthority> ResearchAuthority;

	UPROPERTY()
	TObjectPtr<ALBSpacecraftReputationAuthority> ReputationAuthority;

	UPROPERTY()
	TObjectPtr<UTextBlock> ReputationBlock;

	UPROPERTY()
	TObjectPtr<UTextBlock> QualityBlock;

	UPROPERTY()
	TObjectPtr<UTextBlock> CashBlock;

	UPROPERTY()
	TObjectPtr<UTextBlock> ContractBlock;

	UPROPERTY()
	TObjectPtr<UTextBlock> ClockBlock;

	UPROPERTY()
	TObjectPtr<UTextBlock> LineBlock;

	UPROPERTY()
	TObjectPtr<UTextBlock> PowerBlock;

	UPROPERTY()
	TObjectPtr<UTextBlock> ResearchBlock;

	UPROPERTY()
	TObjectPtr<UTextBlock> TradeBlock;

	UPROPERTY()
	TObjectPtr<class UProgressBar> PowerGauge;

	/** The four speed chips (pause, 1x, 2x, 4x); the live one is filled. */
	UPROPERTY()
	TArray<TObjectPtr<class ULBSpacecraftTaggedButton>> SpeedChips;

	void MakeBarDivider(UHorizontalBox* Box);
	/** A GAUGE CELL (UI direction step 4, 2026-09-02): a small-caps word
	 *  above a number, and optionally a meter under it. Returns the
	 *  number's text block; the meter, if asked for, comes back through
	 *  OutMeter. */
	UTextBlock* MakeBarGauge(UHorizontalBox* Box, const FText& Label,
		const FLinearColor& Colour, float LeftPadding,
		class UProgressBar** OutMeter = nullptr);
	void MakeSpeedChips(UHorizontalBox* Box);
	void HandleSpeedChip(FName Tag);
};
