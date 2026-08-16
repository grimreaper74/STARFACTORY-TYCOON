#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "LBFactoryProcessPortComponent.generated.h"

class ALBFactoryTransportLink;

UENUM(BlueprintType)
enum class ELBFactoryPortDirection : uint8 { Input, Output };

UENUM(BlueprintType)
enum class ELBFactoryTransportKind : uint8
{
    RollerConveyor,
    BeltConveyor,
    PanelTransfer,
    AGVHandoff
};

UENUM(BlueprintType)
enum class ELBFactoryMaterialClass : uint8
{
    Coil,
    Blank,
    FormedPanel,
    Scrap,
    Stillage,
    GeneralParts,
    /** Individually traced, quality-approved pressed panel before WIP-stillage packing. */
    InspectedPanel,
    /** Welded body shell handed from Body Weld into surface treatment. */
    BodyInWhite
};

/**
 * One authoritative material-flow sequence for the player-built press shop.
 * Ports at a stage may connect only to the immediately following stage, so
 * keeping these values named prevents an upstream cell from being bypassed.
 */
namespace LBFactoryProcessStage
{
    static constexpr int32 InboundUnloading = 0;
    static constexpr int32 PR002WeighInspection = 1;
    static constexpr int32 CoilStorage = 2;
    static constexpr int32 DepackAndIdentify = 3;
    static constexpr int32 DecoilerThreader = 4;
    static constexpr int32 PreparedBlankBuffer = 5;
    static constexpr int32 PressTrain = 6;
    static constexpr int32 Inspection = 7;
    static constexpr int32 WIPPanelStillageBuffer = 8;
    static constexpr int32 WeldShopIntake = 9;
    // Serialized/API compatibility aliases. Player-facing UI uses the truthful names above.
    static constexpr int32 FinishedBuffer = WIPPanelStillageBuffer;
    static constexpr int32 Outbound = WeldShopIntake;
    // Whole-vehicle production continues after the press-shop panel chain. These named
    // stages reserve truthful connection contracts while body-weld, paint and assembly
    // assets are delivered independently.
    static constexpr int32 BodyWeld = 10;
    static constexpr int32 ECoat = 11;
    static constexpr int32 Paint = 12;
    static constexpr int32 Assembly = 13;
}

static_assert(LBFactoryProcessStage::PR002WeighInspection == LBFactoryProcessStage::InboundUnloading + 1
    && LBFactoryProcessStage::CoilStorage == LBFactoryProcessStage::PR002WeighInspection + 1
    && LBFactoryProcessStage::DepackAndIdentify == LBFactoryProcessStage::CoilStorage + 1
    && LBFactoryProcessStage::DecoilerThreader == LBFactoryProcessStage::DepackAndIdentify + 1
    && LBFactoryProcessStage::PreparedBlankBuffer == LBFactoryProcessStage::DecoilerThreader + 1
    && LBFactoryProcessStage::PressTrain == LBFactoryProcessStage::PreparedBlankBuffer + 1
    && LBFactoryProcessStage::Inspection == LBFactoryProcessStage::PressTrain + 1
    && LBFactoryProcessStage::FinishedBuffer == LBFactoryProcessStage::Inspection + 1
    && LBFactoryProcessStage::Outbound == LBFactoryProcessStage::FinishedBuffer + 1
    && LBFactoryProcessStage::BodyWeld == LBFactoryProcessStage::Outbound + 1
    && LBFactoryProcessStage::ECoat == LBFactoryProcessStage::BodyWeld + 1
    && LBFactoryProcessStage::Paint == LBFactoryProcessStage::ECoat + 1
    && LBFactoryProcessStage::Assembly == LBFactoryProcessStage::Paint + 1,
    "Player-built vehicle process stages must remain contiguous and cannot bypass required operations");

/** Authored process socket used by the builder's automatic transport linker. */
UCLASS(ClassGroup=(Cairnwell), meta=(BlueprintSpawnableComponent))
class LINEBOSSCARFACTORY_API ULBFactoryProcessPortComponent : public USceneComponent
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder|Process Port")
    FName PortId = TEXT("PROCESS_PORT");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder|Process Port")
    ELBFactoryPortDirection Direction = ELBFactoryPortDirection::Input;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder|Process Port")
    ELBFactoryTransportKind TransportKind = ELBFactoryTransportKind::RollerConveyor;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder|Process Port")
    ELBFactoryMaterialClass MaterialClass = ELBFactoryMaterialClass::Blank;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder|Process Port", meta=(ClampMin="0"))
    int32 ProcessStage = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder|Process Port", meta=(ClampMin="0.0"))
    float MaximumAutomaticLinkDistanceCm = 1500.0f;

    /** One for normal station inputs; increase on authored buffers/aggregators and distributor outputs. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder|Process Port", meta=(ClampMin="1"))
    int32 MaximumConnections = 1;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Process Port")
    bool IsConnected() const { return ConnectedPorts.Num() > 0 && TransportLinks.Num() > 0; }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Process Port")
    bool HasAvailableConnection() const { return TransportLinks.Num() < FMath::Max(1, MaximumConnections); }

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder|Process Port")
    ULBFactoryProcessPortComponent* GetConnectedPort() const
    { return ConnectedPorts.Num() > 0 ? ConnectedPorts[0].Get() : nullptr; }

    ALBFactoryTransportLink* GetTransportLink() const
    { return TransportLinks.Num() > 0 ? TransportLinks[0].Get() : nullptr; }

    /** Exact cache inspection used by transactional factory-graph edits. */
    int32 GetConnectedPortCacheCount() const { return ConnectedPorts.Num(); }
    int32 GetTransportLinkCacheCount() const { return TransportLinks.Num(); }
    ULBFactoryProcessPortComponent* GetConnectedPortAt(int32 Index) const
    { return ConnectedPorts.IsValidIndex(Index) ? ConnectedPorts[Index].Get() : nullptr; }
    ALBFactoryTransportLink* GetTransportLinkAt(int32 Index) const
    { return TransportLinks.IsValidIndex(Index) ? TransportLinks[Index].Get() : nullptr; }
    bool HasTransportLink(const ALBFactoryTransportLink* Link) const;

    bool IsConnectedTo(const ULBFactoryProcessPortComponent* Other) const;

    void SetConnection(ULBFactoryProcessPortComponent* Other, ALBFactoryTransportLink* Link);
    void ClearConnection();
    void RemoveConnection(ALBFactoryTransportLink* Link);
    void RemoveConnectionsTo(const ULBFactoryProcessPortComponent* Other);

private:
    UPROPERTY(Transient)
    TArray<TWeakObjectPtr<ULBFactoryProcessPortComponent>> ConnectedPorts;

    UPROPERTY(Transient)
    TArray<TWeakObjectPtr<ALBFactoryTransportLink>> TransportLinks;
};
