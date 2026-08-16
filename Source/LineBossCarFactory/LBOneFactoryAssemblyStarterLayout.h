#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "LBOneFactoryTypes.h"
#include "LBOneFactoryAssemblyStarterLayout.generated.h"

/** Capability families exposed to the player-facing station assignment UI. */
UENUM(BlueprintType)
enum class ELBOneFactoryAssemblyCapability : uint8
{
    MaterialHandling,
    TrimInstall,
    HeavyLift,
    PrecisionTorque,
    AdhesiveGlazing,
    Powertrain,
    WheelTire,
    Fluids,
    ElectricalSoftware,
    Inspection,
    DynamicTest,
    Rework,
    Dispatch
};

/** The ordered Cairnwell 2040 General Assembly bill of process. */
UENUM(BlueprintType)
enum class ELBOneFactoryAssemblyOperation : uint8
{
    PaintedBodyReceive,
    DoorOff,
    MainWiringHarness,
    HVACModule,
    InstrumentPanelCockpit,
    InteriorTrim,
    Glazing,
    Closures,
    FrontRearCornerModules,
    PowertrainPreparation,
    BatteryAndFuelSystem,
    PowertrainMarriage,
    UnderbodyTorque,
    ExhaustAndThermal,
    Seats,
    DoorRefit,
    WheelsAndTires,
    FluidsCharge,
    SoftwareFlash,
    ElectricalFunctionalTest,
    WheelAlignment,
    BrakeRollDyno,
    FinalInspectionAndRework,
    FinishedVehicleDispatch
};

UENUM(BlueprintType)
enum class ELBOneFactoryAssemblyMaterialState : uint8
{
    PaintedBody,
    TrimmedBody,
    MarriedVehicle,
    FinishedVehicle
};

/** One installed position. Operations are assignments, not immutable station types. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryAssemblyStationState
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
    TArray<ELBOneFactoryAssemblyCapability> Capabilities;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<ELBOneFactoryAssemblyOperation> AssignedOperations;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    float NominalCycleSeconds = 0.0f;

    /** Any live or reserved unit makes assignment and movement fail closed. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FName> ActiveOrReservedUnitIds;
};

/** Exact sequential carrier route; no bypass connection is legal. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryAssemblyConnectionState
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
    float MaximumRouteLengthCm = 6500.0f;
};

/** Complete, versioned Assembly layout and assignment snapshot. */
USTRUCT(BlueprintType)
struct LINEBOSSCARFACTORY_API FLBOneFactoryAssemblyLayoutState
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
    ELBOneFactoryAssemblyMaterialState InputState =
        ELBOneFactoryAssemblyMaterialState::PaintedBody;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    ELBOneFactoryAssemblyMaterialState OutputState =
        ELBOneFactoryAssemblyMaterialState::FinishedVehicle;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBOneFactoryAssemblyStationState> Stations;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame)
    TArray<FLBOneFactoryAssemblyConnectionState> Connections;
};

namespace LBOneFactoryAssemblyStarterIds
{
    LINEBOSSCARFACTORY_API FName Layout();
    LINEBOSSCARFACTORY_API FName Station(int32 LinePosition);
    LINEBOSSCARFACTORY_API FName Connection(int32 SourceLinePosition);
}

/** Pure definition and validation seam for the configurable 24-position line. */
UCLASS()
class LINEBOSSCARFACTORY_API ULBOneFactoryAssemblyStarterLayoutLibrary :
    public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    static constexpr int32 RequiredStationCount = 24;
    static constexpr int32 RequiredOperationCount = 24;
    static constexpr int32 RequiredConnectionCount = 23;

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Assembly")
    static FLBOneFactoryAssemblyLayoutState MakeCanonicalStarterLayout();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Assembly")
    static bool ValidateStarterLayout(
        const FLBOneFactoryAssemblyLayoutState& State, FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Assembly")
    static ELBOneFactoryAssemblyCapability GetRequiredCapability(
        ELBOneFactoryAssemblyOperation InOperation);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Assembly")
    static FString GetOperationDisplayName(
        ELBOneFactoryAssemblyOperation InOperation);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Assembly")
    static bool StationSupportsOperation(
        const FLBOneFactoryAssemblyStationState& Station,
        ELBOneFactoryAssemblyOperation InOperation);
};

/** Player-created data authority. It owns no presentation and spawns no WIP. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBOneFactoryAssemblyStarterLayoutAuthority :
    public AActor
{
    GENERATED_BODY()

public:
    ALBOneFactoryAssemblyStarterLayoutAuthority();

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Assembly|Save")
    FLBOneFactoryAssemblyLayoutState CaptureLayout() const
    { return CurrentState; }

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Assembly|Save")
    bool RestoreLayout(const FLBOneFactoryAssemblyLayoutState& State,
        FString& OutReason);

    /** Moves one operation atomically; every required operation remains exactly once. */
    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Assembly|Configuration")
    bool AssignOperation(ELBOneFactoryAssemblyOperation InOperation,
        FName TargetStationId, FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Assembly|Editing")
    bool MoveStation(FName StationId, const FTransform& WorldTransform,
        FString& OutReason);

    UFUNCTION(BlueprintCallable, Category="Line Boss|OneFactory|Assembly")
    bool Commission(FString& OutReason);

    UFUNCTION(BlueprintPure, Category="Line Boss|OneFactory|Assembly")
    bool IsCommissioned() const { return CurrentState.bCommissioned; }

    static FName GetAuthorityTag();
    static FName GetNativeOnlyTag();

private:
    UPROPERTY(VisibleInstanceOnly, SaveGame,
        Category="Line Boss|OneFactory|Assembly")
    FLBOneFactoryAssemblyLayoutState CurrentState;

    static bool HasActiveOrReservedWIP(
        const FLBOneFactoryAssemblyLayoutState& State);
};
