// Spacecraft-era objectives panel (research doc: rewarded objectives,
// no modal tutorial): a slim right-edge ladder showing the delivery
// milestones and what each unlocks, the current contract target, and
// owned land. Read-only mirror of the progression + production
// authorities; rebuilt only when its revision changes.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "LBSpacecraftObjectivesWidget.generated.h"

class ALBSpacecraftGameMode;
class UTextBlock;
class UVerticalBox;

UCLASS()
class LINEBOSSCARFACTORY_API ULBSpacecraftObjectivesWidget
	: public UUserWidget
{
	GENERATED_BODY()

public:
	void BindGame(ALBSpacecraftGameMode* InGameMode);

	/** "[2/3] QUALITY CONTROL" or "[DONE] CONVEYOR BELTS" - pure. */
	static FString BuildObjectiveLine(int32 Delivered, int32 Needed,
		const FString& UnlockName);

protected:
	virtual void NativeOnInitialized() override;
	virtual void NativeTick(const FGeometry& MyGeometry,
		float InDeltaTime) override;

private:
	UPROPERTY()
	TObjectPtr<ALBSpacecraftGameMode> GameMode;

	UPROPERTY()
	TObjectPtr<UVerticalBox> LadderBox;

	FString LastRevision;

	void Rebuild();
	void AddLine(const FString& Text, bool bDone);
};
