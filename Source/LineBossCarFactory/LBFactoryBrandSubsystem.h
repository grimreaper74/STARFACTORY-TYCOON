#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LBFactoryBrandSubsystem.generated.h"

/** The two player-controlled colours which make factory equipment recognisably theirs. */
USTRUCT(BlueprintType)
struct FLBFactoryMachineLivery
{
    GENERATED_BODY()

    /** Painted machine guards, cabinets and main body panels. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLinearColor PrimaryColour = FLinearColor(0.035f, 0.36f, 0.16f, 1.0f);

    /** Structural frames, plinths and secondary housings. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLinearColor SecondaryColour = FLinearColor(0.055f, 0.07f, 0.075f, 1.0f);

    bool Equals(const FLBFactoryMachineLivery& Other, float Tolerance = KINDA_SMALL_NUMBER) const
    {
        return PrimaryColour.Equals(Other.PrimaryColour, Tolerance)
            && SecondaryColour.Equals(Other.SecondaryColour, Tolerance);
    }
};

USTRUCT(BlueprintType)
struct FLBFactoryBrandSaveState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 2;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString FactoryName = TEXT("Cairnwell Automotive");

    /** Main painted bodywork. Deliberately brighter than the old near-black green. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLinearColor PrimaryColour = FLinearColor(0.035f, 0.36f, 0.16f, 1.0f);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FLinearColor SecondaryColour = FLinearColor(0.055f, 0.07f, 0.075f, 1.0f);

    /**
     * Retained only so v1 campaign saves deserialize cleanly. Safety paint is a fixed
     * factory semantic from v2 onward and this stored value is ignored on restore.
     */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, SaveGame)
    FLinearColor SafetyAccentColour = FLinearColor(1.0f, 0.62f, 0.035f, 1.0f);

    /**
     * Legacy v2 onboarding bit retained for save compatibility. New and restored
     * campaigns start ready to play; identity and livery are optional settings.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bInitialSetupComplete = true;

    /** Optional project asset path for a later imported player logo. Empty uses the built-in geometric mark. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FString LogoAssetPath;
};

DECLARE_MULTICAST_DELEGATE_OneParam(FLBFactoryMachineLiveryChanged,
    const FLBFactoryMachineLivery&);

/** Per-campaign player company identity and shared factory paint authority. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBFactoryBrandSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Brand")
    FString GetFactoryName() const { return Brand.FactoryName; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Brand")
    FLinearColor GetPrimaryColour() const { return Brand.PrimaryColour; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Brand")
    FLinearColor GetSecondaryColour() const { return Brand.SecondaryColour; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Brand")
    FLinearColor GetSafetyAccentColour() const { return GetFixedSafetyYellowColour(); }

    /** Safety and state colours are deliberately outside the player livery. */
    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Brand|Safety")
    static FLinearColor GetFixedSafetyYellowColour();

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Brand")
    FLBFactoryMachineLivery GetMachineLivery() const;

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Brand")
    bool IsInitialSetupComplete() const { return Brand.bInitialSetupComplete; }

    /** Accepts a player-entered printable name, normalises whitespace and caps it at 40 characters. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Brand")
    bool SetFactoryName(const FString& NewName);

    /**
     * Compatibility entry point for the existing profile screen. SafetyAccent must be
     * the fixed safety yellow; it can no longer recolour safety-critical markings.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Brand",
        meta=(DeprecatedFunction, DeprecationMessage="Use SetMachineLiveryColours; safety paint is fixed."))
    bool SetFactoryColours(FLinearColor Primary, FLinearColor Secondary, FLinearColor SafetyAccent);

    /** Validates and applies both player-controlled machine colours. It remains callable later. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Brand")
    bool SetMachineLiveryColours(FLinearColor Primary, FLinearColor Secondary, FString& OutReason);

    /** Legacy compatibility endpoint. Factory appearance no longer blocks campaign startup. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Brand")
    bool CompleteInitialSetup();

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Brand")
    static bool ValidateMachineLiveryColours(
        FLinearColor Primary, FLinearColor Secondary, FString& OutReason);

    /** Native hook for opt-in runtime/approved-art livery components. */
    FLBFactoryMachineLiveryChanged& OnMachineLiveryChanged() { return MachineLiveryChanged; }

    uint32 GetMachineLiveryRevision() const { return MachineLiveryRevision; }

    UFUNCTION(BlueprintPure, Category="Line Boss|Factory Brand")
    FLBFactoryBrandSaveState CaptureSaveState() const { return Brand; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|Factory Brand")
    bool RestoreSaveState(const FLBFactoryBrandSaveState& State);

private:
    UPROPERTY(Transient)
    FLBFactoryBrandSaveState Brand;

    FLBFactoryMachineLiveryChanged MachineLiveryChanged;
    uint32 MachineLiveryRevision = 0;

    static FString SanitiseName(const FString& Input);
    static bool IsFiniteUnitColour(const FLinearColor& Colour);
    static float ContrastRatio(const FLinearColor& A, const FLinearColor& B);
    bool SetMachineLiveryColoursWithoutReason(FLinearColor Primary, FLinearColor Secondary);
    void BroadcastMachineLiveryIfChanged(const FLBFactoryMachineLivery& PreviousLivery);
};
