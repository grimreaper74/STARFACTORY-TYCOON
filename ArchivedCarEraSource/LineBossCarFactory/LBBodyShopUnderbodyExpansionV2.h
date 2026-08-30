#pragma once

#include "CoreMinimal.h"
#include "LBBodyShopUnderbodyProcess.h"
#include "LBBodyShopUnderbodyExpansionV2.generated.h"

/**
 * Stable process roles for the expanded underbody line. This catalogue is
 * deliberately separate from the verified six-cell Experimental_v001 slice.
 */
UENUM(BlueprintType)
enum class ELBBodyShopUnderbodyExpansionStageV2 : uint8
{
    ComponentKitPresentation,
    RailCrossmemberPreparation,
    MainUnderbodyJoining,
    SideSillRockerJoining,
    DeburrFinish,
    UnderbodyInspection,
    UnderbodyRework,
    PassBuffer
};

namespace LBBodyShopUnderbodyExpansionStationIdsV2
{
    LINEBOSSCARFACTORY_API extern const FName ComponentKitPresentation;
    LINEBOSSCARFACTORY_API extern const FName RailCrossmemberPreparation;
    LINEBOSSCARFACTORY_API extern const FName MainUnderbodyJoining;
    LINEBOSSCARFACTORY_API extern const FName SideSillRockerJoining;
    LINEBOSSCARFACTORY_API extern const FName DeburrFinish;
    LINEBOSSCARFACTORY_API extern const FName UnderbodyInspection;
    LINEBOSSCARFACTORY_API extern const FName UnderbodyRework;
    LINEBOSSCARFACTORY_API extern const FName PassBuffer;
}

namespace LBBodyShopUnderbodyExpansionMaterialIdsV2
{
    LINEBOSSCARFACTORY_API extern const FName RawPrimaryKit;
    LINEBOSSCARFACTORY_API extern const FName PresentedPrimaryKit;
    LINEBOSSCARFACTORY_API extern const FName PreparedPrimaryStructure;
    LINEBOSSCARFACTORY_API extern const FName PrimaryStructureJoined;
    LINEBOSSCARFACTORY_API extern const FName SideSillKit;
    LINEBOSSCARFACTORY_API extern const FName SideSillsJoined;
    LINEBOSSCARFACTORY_API extern const FName FinishChecked;
    LINEBOSSCARFACTORY_API extern const FName ReworkHold;
    LINEBOSSCARFACTORY_API extern const FName ReinspectReady;
}

namespace LBBodyShopUnderbodyExpansionPortIdsV2
{
    LINEBOSSCARFACTORY_API extern const FName PrimaryKitIn;
    LINEBOSSCARFACTORY_API extern const FName BodyIn;
    LINEBOSSCARFACTORY_API extern const FName BodyOut;
    LINEBOSSCARFACTORY_API extern const FName SideSillKitIn;
    LINEBOSSCARFACTORY_API extern const FName PassOut;
    LINEBOSSCARFACTORY_API extern const FName ReworkOut;
    LINEBOSSCARFACTORY_API extern const FName ReworkIn;
    LINEBOSSCARFACTORY_API extern const FName ReinspectOut;
    LINEBOSSCARFACTORY_API extern const FName ReinspectIn;
}

/** Stable identities for the exact approved connection order. */
namespace LBBodyShopUnderbodyExpansionConnectionIdsV2
{
    LINEBOSSCARFACTORY_API extern const FName KitToPreparation;
    LINEBOSSCARFACTORY_API extern const FName PreparationToMainJoin;
    LINEBOSSCARFACTORY_API extern const FName MainJoinToSideJoin;
    LINEBOSSCARFACTORY_API extern const FName SideJoinToFinish;
    LINEBOSSCARFACTORY_API extern const FName FinishToInspection;
    LINEBOSSCARFACTORY_API extern const FName InspectionToPassBuffer;
    LINEBOSSCARFACTORY_API extern const FName InspectionToRework;
    LINEBOSSCARFACTORY_API extern const FName ReworkToReinspection;
}

USTRUCT(BlueprintType)
struct FLBBodyShopUnderbodyExpansionPortV2
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName PortId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ELBBodyShopPortDirection Direction = ELBBodyShopPortDirection::Input;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ELBBodyShopTransportType Transport = ELBBodyShopTransportType::SkidConveyor;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName MaterialId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FTransform LocalTransform = FTransform::Identity;
};

USTRUCT(BlueprintType)
struct FLBBodyShopUnderbodyExpansionStationV2
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    int32 ContractVersion = 2;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName StationId = NAME_None;

    /** One canonical line is configured for exactly one centre-structure architecture. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ELBBodyShopUnderbodyArchitecture Architecture =
        ELBBodyShopUnderbodyArchitecture::CentreTunnel;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    ELBBodyShopUnderbodyExpansionStageV2 Stage =
        ELBBodyShopUnderbodyExpansionStageV2::ComponentKitPresentation;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FText DisplayName;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FVector FootprintCm = FVector(800.0f, 800.0f, 400.0f);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FVector MaintenanceEnvelopeCm = FVector(1000.0f, 1000.0f, 500.0f);

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    float CycleSeconds = 1.0f;

    /** Stable process IDs from LBBodyShopUnderbodyProcess, not presentation labels. */
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> ProcessStepIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> ComponentIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> JoinOperationIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FName> QualityCheckIds;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TArray<FLBBodyShopUnderbodyExpansionPortV2> Ports;
};

USTRUCT(BlueprintType)
struct FLBBodyShopUnderbodyExpansionLayoutItemV2
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName StationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FTransform WorldTransform = FTransform::Identity;
};

USTRUCT(BlueprintType)
struct FLBBodyShopUnderbodyExpansionEndpointV2
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName StationId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName PortId = NAME_None;
};

USTRUCT(BlueprintType)
struct FLBBodyShopUnderbodyExpansionConnectionV2
{
    GENERATED_BODY()

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FName ConnectionId = NAME_None;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FLBBodyShopUnderbodyExpansionEndpointV2 Source;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    FLBBodyShopUnderbodyExpansionEndpointV2 Target;
};

/**
 * Pure Experimental_v002 catalogue. It does not mutate the v001 registry,
 * save schema, map, authority or runtime and therefore cannot invalidate the
 * verified six-cell Early Access baseline.
 */
class LINEBOSSCARFACTORY_API FLBBodyShopUnderbodyExpansionRegistryV2
{
public:
    static TArray<FName> GetStableStationIds();
    static TArray<FName> GetStableMaterialIds();
    static TArray<FName> GetStablePortIds();
    static TArray<FName> GetStableConnectionIds();
    static TArray<FLBBodyShopUnderbodyExpansionStationV2> GetCanonicalStations(
        ELBBodyShopUnderbodyArchitecture Architecture =
            ELBBodyShopUnderbodyArchitecture::CentreTunnel);
    static bool FindCanonicalStation(FName StationId,
        FLBBodyShopUnderbodyExpansionStationV2& OutStation,
        ELBBodyShopUnderbodyArchitecture Architecture =
            ELBBodyShopUnderbodyArchitecture::CentreTunnel);

    static TArray<FLBBodyShopUnderbodyExpansionLayoutItemV2> GetApprovedLayout();
    static TArray<FLBBodyShopUnderbodyExpansionConnectionV2> GetApprovedConnections();

    static bool ValidateStation(const FLBBodyShopUnderbodyExpansionStationV2& Station,
        FString& OutReason);

    static bool ValidateExpansion(
        const TArray<FLBBodyShopUnderbodyExpansionStationV2>& Stations,
        const TArray<FLBBodyShopUnderbodyExpansionLayoutItemV2>& Layout,
        const TArray<FLBBodyShopUnderbodyExpansionConnectionV2>& Connections,
        FString& OutReason);

    /** Exact eight-station inventory: seven-station main route plus adjacent rework. */
    static bool ValidateApprovedExpansion(FString& OutReason);
    static bool ValidateApprovedExpansion(ELBBodyShopUnderbodyArchitecture Architecture,
        FString& OutReason);
};
