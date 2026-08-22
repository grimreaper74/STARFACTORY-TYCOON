#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBOneFactoryTypes.h"
#include "LBOneFactoryBodyWeldStarterLayout.generated.h"

/** Player-facing capability families for the configurable Body/Weld line. */
UENUM(BlueprintType)
enum class ELBOneFactoryBodyWeldCapability : uint8
{
    PanelLogistics,
    MaterialHandling,
    UnderbodyGeometry,
    FramingGeometry,
    SpotJoining,
    AdhesiveJoining,
    RoofInstall,
    ClosureFit,
    StudMount,
    Metrology,
    Quality,
    Rework,
    Handoff
};

/** Ordered Body/Weld bill of process, from pressed panels to BIW handoff. */
UENUM(BlueprintType)
enum class ELBOneFactoryBodyWeldProgramme : uint8
{
    PressedPanelReceive,
    FrontUnderbodyGeometry,
    RearUnderbodyGeometry,
    UnderbodyFramingAndRespot,
    LeftBodysideLoad,
    RightBodysideLoad,
    BodyFramingAndMarriage,
    RoofAndCrossmemberFit,
    MainBodySpotWeld,
    AdhesiveAndBrazedSeams,
    ClosurePreparation,
    ClosureFitAndHingeSet,
    DimensionalGeometryScan,
    RespotAndFinishWeld,
    StudMountAndBracketWeld,
    WeldQualityInspection,
    BIWReworkAndBuffer,
    BIWHandoff
};

/** Explicit duties for each side of a mirrored large six-axis robot pair. */
UENUM(BlueprintType)
enum class ELBOneFactoryBodyWeldRobotRole : uint8
{
    None,
    PanelHandling,
    TransferHandling,
    GeometryClamp,
    SpotWelding,
    AdhesiveSealing,
    RoofHandling,
    ClosureHandling,
    StudWelding,
    VisionInspection,
    ReworkWelding
};

UENUM(BlueprintType)
enum class ELBOneFactoryBodyWeldRobotSide : uint8
{
    Left,
    Right
};

UENUM(BlueprintType)
enum class ELBOneFactoryBodyWeldMaterialState : uint8
{
    PressedPanelSet,
    BodyInWhite
};

/** One installed position; its programme and two robot roles are assignments. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryBodyWeldStationState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName StationId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 LinePosition = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FTransform WorldTransform = FTransform::Identity;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FVector FootprintSizeCm = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<ELBOneFactoryBodyWeldCapability> Capabilities;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<ELBOneFactoryBodyWeldProgramme> AssignedProgrammes;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<ELBOneFactoryBodyWeldRobotRole> SupportedRobotRoles;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryBodyWeldRobotRole LeftRobotRole =
        ELBOneFactoryBodyWeldRobotRole::None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryBodyWeldRobotRole RightRobotRole =
        ELBOneFactoryBodyWeldRobotRole::None;

    /** Frozen true: every position visibly uses a mirrored large robot pair. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bMirroredLargeSixAxisPair = true;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float NominalCycleSeconds = 0.0f;

    /**
     * Optional named sub-assembly cell inside this BIW station.  Closure
     * work remains on the same physical route but doors must not be confused
     * with the bonnet/tailgate build-up before final body marriage.
     */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName SubassemblyCellId = NAME_None;

    /** Any live or reserved unit blocks configuration and commissioning. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FName> ActiveOrReservedUnitIds;
};

/** One exact sequential skid route; bypass connections are not legal. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryBodyWeldConnectionState
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
    float MaximumRouteLengthCm = 6200.0f;
};

/** Complete, versioned data snapshot. Presentation and decorative WIP are absent. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryBodyWeldLayoutState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Version = 1;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName LayoutId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    FName VehicleModelId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    int32 Revision = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    bool bCommissioned = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryBodyWeldMaterialState InputState =
        ELBOneFactoryBodyWeldMaterialState::PressedPanelSet;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryBodyWeldMaterialState OutputState =
        ELBOneFactoryBodyWeldMaterialState::BodyInWhite;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBOneFactoryBodyWeldStationState> Stations;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBOneFactoryBodyWeldConnectionState> Connections;
};

namespace LBOneFactoryBodyWeldStarterIds
{
    LINEBOSSCARFACTORY_API FName Layout();
    LINEBOSSCARFACTORY_API FName VehicleModel();
    LINEBOSSCARFACTORY_API FName Station(int32 LinePosition);
    LINEBOSSCARFACTORY_API FName Connection(int32 SourceLinePosition);
}

/** Pure definition and validation seam for the native-only 18-position line. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryBodyWeldStarterLayoutLibrary :
    public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    static constexpr int32 RequiredStationCount = 18;
    static constexpr int32 RequiredProgrammeCount = 18;
    static constexpr int32 RequiredConnectionCount = 17;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Body Weld")
    static FLBOneFactoryBodyWeldLayoutState MakeCanonicalStarterLayout();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Body Weld")
    static bool ValidateStarterLayout(
        const FLBOneFactoryBodyWeldLayoutState& State, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Body Weld")
    static ELBOneFactoryBodyWeldCapability GetRequiredCapability(
        ELBOneFactoryBodyWeldProgramme InProgramme);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Body Weld")
    static ELBOneFactoryBodyWeldRobotRole GetRequiredRobotRole(
        ELBOneFactoryBodyWeldProgramme InProgramme);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Body Weld")
    static FString GetProgrammeDisplayName(
        ELBOneFactoryBodyWeldProgramme InProgramme);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Body Weld")
    static FString GetRobotRoleDisplayName(
        ELBOneFactoryBodyWeldRobotRole InRobotRole);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Body Weld")
    static bool StationSupportsProgramme(
        const FLBOneFactoryBodyWeldStationState& Station,
        ELBOneFactoryBodyWeldProgramme InProgramme);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Body Weld")
    static bool StationSupportsRobotRole(
        const FLBOneFactoryBodyWeldStationState& Station,
        ELBOneFactoryBodyWeldRobotRole InRobotRole);
};

/** Player-created NativeOnly authority. It owns no visual objects or WIP actors. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryBodyWeldStarterLayoutAuthority :
    public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryBodyWeldStarterLayoutAuthority();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Body Weld|Save")
    FLBOneFactoryBodyWeldLayoutState CaptureLayout() const
    { return CurrentState; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Body Weld|Save")
    bool RestoreLayout(const FLBOneFactoryBodyWeldLayoutState& State,
        FString& OutReason);

    /** Moves one required programme atomically; all programmes remain exactly once. */
    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Body Weld|Configuration")
    bool AssignProgramme(ELBOneFactoryBodyWeldProgramme InProgramme,
        FName TargetStationId, FString& OutReason);

    /** Reassigns both sides in one transaction so a valid mirrored pair never tears. */
    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Body Weld|Configuration")
    bool AssignRobotPairRoles(FName StationId,
        ELBOneFactoryBodyWeldRobotRole InLeftRobotRole,
        ELBOneFactoryBodyWeldRobotRole InRightRobotRole,
        FString& OutReason);

    UFUNCTION(BlueprintCallable,
        Category="Line Boss|OneFactory|Body Weld|Editing")
    bool MoveStation(FName StationId, const FTransform& WorldTransform,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Body Weld")
    bool Commission(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Body Weld")
    bool IsCommissioned() const { return CurrentState.bCommissioned; }

    static FName GetAuthorityTag();
    static FName GetNativeOnlyTag();

private:
    UPROPERTY(VisibleInstanceOnly, SaveGame,
        Category="Line Boss|OneFactory|Body Weld")
    FLBOneFactoryBodyWeldLayoutState CurrentState;

    static bool HasActiveOrReservedWIP(
        const FLBOneFactoryBodyWeldLayoutState& State);
};
