#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBOneFactoryTypes.h"
#include "LBOneFactoryPaintStarterLayout.generated.h"

/** The honest player-facing responsibilities in the OneFactory Paint line. */
UENUM(BlueprintType)
enum class ELBOneFactoryPaintStarterRole : uint8
{
    BodySkidReceiving,
    PretreatmentWash,
    EDCoatLogicalProcess,
    FlashOff,
    BlackBoxSprayBooth,
    CuringOven,
    QualityLightInspection,
    PaintedBodyDispatch
};

/** Stable material states on the canonical route; none imply hidden geometry. */
UENUM(BlueprintType)
enum class ELBOneFactoryPaintBodyState : uint8
{
    BodyInWhite,
    PretreatedBody,
    EDCoatedBody,
    ColourCoatedBody,
    CuredPaintedBody,
    InspectedPaintedBody
};

/** Two process colours plus the five player-selectable launch programmes. */
UENUM(BlueprintType)
enum class ELBOneFactoryPaintColour : uint8
{
    BodyInWhite,
    EDPrimerGrey,
    ArcticWhite,
    FoundryGraphite,
    CairnwellTeal,
    SignalRed,
    AuroraBlue
};

/** One exact asset and its frozen provenance/LOD expectation. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPaintNativeAssetAllowance
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FSoftObjectPath AssetPath;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    ELBOneFactoryAssetProvenance Provenance =
        ELBOneFactoryAssetProvenance::Unspecified;

    /** Zero is valid for a non-mesh dependency such as a material. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 RequiredAuthoredLODCount = 0;
};

/** Exact, fail-closed native-only policy for the Paint starter milestone. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPaintNativeOnlyProfile
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FName ProfileId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    ELBOneFactoryProvenancePolicy Policy =
        ELBOneFactoryProvenancePolicy::NativeOnly;

    /** Exact class paths; inheritance never expands this list. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FString> AllowedClassPaths;

    /** Exact object paths; a broader Candidate root receives no trust. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FLBOneFactoryPaintNativeAssetAllowance> AllowedAssets;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FString> ForbiddenSourceTokens;
};

/** One stable responsibility record. Presentation is deliberately absent. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPaintStarterStationState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName StationId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryPaintStarterRole Role =
        ELBOneFactoryPaintStarterRole::BodySkidReceiving;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FTransform WorldTransform = FTransform::Identity;

    /** Complete authored footprint, independent of replaceable art. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FVector FootprintSizeCm = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryPaintBodyState InputBodyState =
        ELBOneFactoryPaintBodyState::BodyInWhite;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryPaintBodyState OutputBodyState =
        ELBOneFactoryPaintBodyState::BodyInWhite;

    /** True only where choosing the line programme is a sensible UI action. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPlayerProgrammeSelectable = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPlayerPositionable = true;

    /** Set together on every programme-bound downstream responsibility. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName PaintProgrammeId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryPaintColour TargetBodyColour =
        ELBOneFactoryPaintColour::BodyInWhite;

    /** Any live or reserved body makes edits and commissioning fail closed. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FName> ActiveOrReservedUnitIds;
};

/** One exact sequential carrier route between adjacent responsibilities. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPaintStarterConnectionState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName ConnectionId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName SourceStationId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName TargetStationId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryPaintBodyState CarriedBodyState =
        ELBOneFactoryPaintBodyState::BodyInWhite;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame,
        meta=(ClampMin="1.0"))
    float MaximumRouteLengthCm = 2800.0f;
};

/** Versioned topology/programme snapshot for atomic capture and restore. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPaintStarterLayoutState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LayoutId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName VehicleModelId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName PaintProgrammeId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryPaintColour SelectedBodyColour =
        ELBOneFactoryPaintColour::CairnwellTeal;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Revision = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCommissioned = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryPaintBodyState InputBodyState =
        ELBOneFactoryPaintBodyState::BodyInWhite;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryPaintBodyState OutputBodyState =
        ELBOneFactoryPaintBodyState::InspectedPaintedBody;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBOneFactoryPaintStarterStationState> Stations;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBOneFactoryPaintStarterConnectionState> Connections;
};

namespace LBOneFactoryPaintStarterIds
{
    LINEBOSSCARFACTORY_API FName Layout();
    LINEBOSSCARFACTORY_API FName NativeOnlyProfile();
    LINEBOSSCARFACTORY_API FName Station(ELBOneFactoryPaintStarterRole Role);
    LINEBOSSCARFACTORY_API FName Connection(int32 SourceSequenceIndex);
}

/** Pure definition, validation, programme and provenance seam. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryPaintStarterLayoutLibrary :
    public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    static constexpr int32 RequiredStationCount = 8;
    static constexpr int32 RequiredConnectionCount = 7;
    static constexpr int32 RequiredDirectPresentationAssetCount = 10;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint")
    static FLBOneFactoryPaintStarterLayoutState MakeCanonicalStarterLayout();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint")
    static bool ValidateStarterLayout(
        const FLBOneFactoryPaintStarterLayoutState& State, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint|Programme")
    static bool IsPlayerSelectableColour(ELBOneFactoryPaintColour Colour);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint|Programme")
    static FName MakePaintProgrammeId(ELBOneFactoryPaintColour Colour);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint|Programme")
    static FString GetColourDisplayName(ELBOneFactoryPaintColour Colour);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint|Programme")
    static FLinearColor GetProgrammeDisplayColour(
        ELBOneFactoryPaintColour Colour);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint|Provenance")
    static FLBOneFactoryPaintNativeOnlyProfile MakeNativeOnlyProfile();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint|Provenance")
    static bool ValidateNativeOnlyProfile(
        const FLBOneFactoryPaintNativeOnlyProfile& Profile,
        FString& OutReason);

    /** Exact class, exact object path and exact declared provenance are required. */
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint|Provenance")
    static bool ValidateNativeReference(
        const FLBOneFactoryPaintNativeOnlyProfile& Profile,
        const FString& ClassPath, const FString& AssetReference,
        ELBOneFactoryAssetProvenance Provenance, FString& OutReason);
};

/**
 * Player-created Paint data authority. It owns no presentation, machinery or
 * process WIP and performs no constructor/BeginPlay spawning.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryPaintStarterLayoutAuthority :
    public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryPaintStarterLayoutAuthority();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint|Save")
    FLBOneFactoryPaintStarterLayoutState CaptureLayout() const
    { return CurrentState; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Paint|Save")
    bool RestoreLayout(const FLBOneFactoryPaintStarterLayoutState& State,
        FString& OutReason);

    /** Changes the complete downstream colour programme in one commit. */
    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Paint|Configuration")
    bool SetStationPaintProgramme(FName StationId,
        ELBOneFactoryPaintColour TargetColour, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Paint|Editing")
    bool MoveStation(FName StationId, const FTransform& WorldTransform,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Paint")
    bool Commission(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Paint")
    bool IsCommissioned() const { return CurrentState.bCommissioned; }

    static FName GetAuthorityTag();
    static FName GetNativeOnlyTag();

private:
    UPROPERTY(VisibleInstanceOnly, SaveGame,
        Category="Line Boss|OneFactory|Paint")
    FLBOneFactoryPaintStarterLayoutState CurrentState;

    static bool HasActiveOrReservedWIP(
        const FLBOneFactoryPaintStarterLayoutState& State);
};
