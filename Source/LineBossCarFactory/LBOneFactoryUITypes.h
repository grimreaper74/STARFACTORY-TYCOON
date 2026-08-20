#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBOneFactoryUITypes.generated.h"

/**
 * The single status model every UI surface reads (UI research rule 1):
 * the card dot, the detail panel's cause line and the world toast all
 * derive from this one enum, so they can never disagree.
 */
UENUM(BlueprintType)
enum class ELBOneFactoryStationStatus : uint8
{
    Working,
    Starved,
    Blocked,
    QualityHold,
    WearCritical,
    Offline,
    Paused
};

/** Fixed shape per status: colour is never the only encoding (rule 4). */
UENUM(BlueprintType)
enum class ELBOneFactoryStatusGlyph : uint8
{
    CircleFilled,
    Triangle,
    Square,
    Diamond,
    Wrench,
    Cross,
    BarsPaused
};

/** Where a condition surfaces (rule 3's severity table). */
UENUM(BlueprintType)
enum class ELBOneFactoryAlertSeverity : uint8
{
    /** Card dot only. */
    Passive,
    /** Card dot + bell inbox entry. */
    Inbox,
    /** Card dot + inbox + world toast. */
    Toast
};

/** One status's complete UI identity. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryStatusToken
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|UI")
    ELBOneFactoryStationStatus Status = ELBOneFactoryStationStatus::Working;

    /** Okabe-Ito colourblind-safe palette; validated under deuteranopia. */
    UPROPERTY(BlueprintReadOnly, Category="Line Boss|UI")
    FLinearColor Colour = FLinearColor::White;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|UI")
    ELBOneFactoryStatusGlyph Glyph = ELBOneFactoryStatusGlyph::CircleFilled;

    UPROPERTY(BlueprintReadOnly, Category="Line Boss|UI")
    ELBOneFactoryAlertSeverity Severity = ELBOneFactoryAlertSeverity::Passive;

    /** Localised cause template; surfaces name the cause, never just a
        magnitude (rule 2). */
    UPROPERTY(BlueprintReadOnly, Category="Line Boss|UI")
    FText CauseLabel;
};

UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryUITokens :
    public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    /** The one token map. Every UI surface goes through here. */
    UFUNCTION(BlueprintPure, Category="Line Boss|UI")
    static FLBOneFactoryStatusToken TokenForStatus(
        ELBOneFactoryStationStatus Status);

    /** Type ramp floors (UI research rule 10). */
    static constexpr float MinTextPxAt1280x800 = 12.0f;
    static constexpr float BodyTextPxAt1080p = 18.0f;

    /** The canonical rate unit is cars/hour (rule 5). */
    UFUNCTION(BlueprintPure, Category="Line Boss|UI")
    static float StampsToRatePerHour(int32 StampCount,
        float WindowSimSeconds);
};
