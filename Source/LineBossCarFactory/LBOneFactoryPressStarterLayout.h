#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBOneFactoryTypes.h"
#include "LBOneFactoryPressStarterLayout.generated.h"

/**
 * Player-facing responsibilities in the smallest honest Press starter chain.
 * BlankPreparation is deliberately a compact weigh/identify/de-pack/cut package;
 * it does not claim that the omitted engineering detail exists behind the shell.
 */
UENUM(BlueprintType)
enum class ELBOneFactoryPressStarterRole : uint8
{
    InboundCoilReceiving,
    WrappedCoilStorage,
    BlankPreparation,
    PreparedBlankBuffer,
    ConfigurablePressTrain,
    PanelInspection,
    PanelStillageDispatch
};

/** One stable station record. Presentation remains outside the save contract. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPressStarterStationState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName StationId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryPressStarterRole Role =
        ELBOneFactoryPressStarterRole::InboundCoilReceiving;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FTransform WorldTransform = FTransform::Identity;

    /** Complete authored gameplay footprint, independent of replaceable art. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FVector FootprintSizeCm = FVector::ZeroVector;

    /** The UMG station picker may initiate a panel-programme change here. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bPlayerReconfigurable = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName VehicleModelId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName PanelTypeId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName DieId = NAME_None;

    /** Any active/reserved material blocks movement and programme changes. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FName> ActiveOrReservedUnitIds;
};

/** Stable, presentation-free material route between two starter stations. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPressStarterConnectionState
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
    ELBFactoryMaterialClass MaterialClass = ELBFactoryMaterialClass::Coil;

    /** Keeps a moved station from silently stretching a route across the factory. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame,
        meta=(ClampMin="1.0"))
    float MaximumRouteLengthCm = 8000.0f;
};

/** Exact, fail-closed presentation policy for this starter milestone. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPressNativeOnlyProfile
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FName ProfileId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    ELBOneFactoryProvenancePolicy Policy =
        ELBOneFactoryProvenancePolicy::NativeOnly;

    /** Exact class paths; inheritance never expands this allowlist. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FString> AllowedClassPaths;

    /** Exact path prefixes. No historic Candidate/Runtime root is implicitly trusted. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FString> AllowedAssetRoots;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FString> ForbiddenSourceTokens;
};

/** Versioned, self-contained topology snapshot for atomic capture/restore. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryPressStarterLayoutState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LayoutId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Revision = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCommissioned = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBOneFactoryPressStarterStationState> Stations;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBOneFactoryPressStarterConnectionState> Connections;
};

namespace LBOneFactoryPressStarterIds
{
    LINEBOSSCARFACTORY_API FName Layout();
    LINEBOSSCARFACTORY_API FName NativeOnlyProfile();
    LINEBOSSCARFACTORY_API FName InboundReceiving();
    LINEBOSSCARFACTORY_API FName WrappedCoilStorage();
    LINEBOSSCARFACTORY_API FName BlankPreparation();
    LINEBOSSCARFACTORY_API FName PreparedBlankBuffer();
    LINEBOSSCARFACTORY_API FName PressTrain();
    LINEBOSSCARFACTORY_API FName PanelInspection();
    LINEBOSSCARFACTORY_API FName PanelDispatch();
}

/** Pure canonical-definition, validation and provenance seam. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryPressStarterLayoutLibrary :
    public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Starter")
    static FLBOneFactoryPressStarterLayoutState MakeCanonicalStarterLayout();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Starter")
    static bool ValidateStarterLayout(
        const FLBOneFactoryPressStarterLayoutState& State, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Starter|Provenance")
    static FLBOneFactoryPressNativeOnlyProfile MakeNativeOnlyProfile();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Starter|Provenance")
    static bool ValidateNativeOnlyProfile(
        const FLBOneFactoryPressNativeOnlyProfile& Profile, FString& OutReason);

    /** Both the exact class and exact asset root must be allowlisted. */
    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Starter|Provenance")
    static bool ValidateNativeReference(
        const FLBOneFactoryPressNativeOnlyProfile& Profile,
        const FString& ClassPath, const FString& AssetReference,
        ELBOneFactoryAssetProvenance Provenance, FString& OutReason);

    static FName MakeDieId(FName PanelTypeId);
};

/**
 * Runtime data authority created only when a player starts the Press department.
 * It never spawns map content, WIP, machines or presentation in its constructor or
 * BeginPlay, so the protected empty OneFactory shell remains an honest boundary.
 */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryPressStarterLayoutAuthority :
    public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryPressStarterLayoutAuthority();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Starter|Save")
    FLBOneFactoryPressStarterLayoutState CaptureLayout() const
    { return CurrentState; }

    /** Mutation-free validation precedes the single assignment commit. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Press Starter|Save")
    bool RestoreLayout(const FLBOneFactoryPressStarterLayoutState& State,
        FString& OutReason);

    /**
     * Configuring any exposed recipe station changes the blank, die, inspection
     * and dispatch responsibilities together; a partial incompatible chain can
     * never be committed.
     */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Press Starter|Configuration")
    bool SetStationPanelProgramme(FName StationId, FName PanelTypeId,
        FString& OutReason);

    /** Transactional layout edit. The exact station identity and graph survive. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Press Starter|Editing")
    bool MoveStation(FName StationId, const FTransform& WorldTransform,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Press Starter")
    bool Commission(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Press Starter")
    bool IsCommissioned() const { return CurrentState.bCommissioned; }

    static FName GetAuthorityTag();
    static FName GetNativeOnlyTag();

private:
    UPROPERTY(VisibleInstanceOnly, SaveGame,
        Category="Line Boss|OneFactory|Press Starter")
    FLBOneFactoryPressStarterLayoutState CurrentState;

    static bool StateHasActiveOrReservedWIP(
        const FLBOneFactoryPressStarterLayoutState& State);
};
