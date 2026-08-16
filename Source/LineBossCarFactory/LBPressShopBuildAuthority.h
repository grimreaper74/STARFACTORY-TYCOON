#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPressShopBuildAuthority.generated.h"

class ALBPressShopStorageZone;
struct FLBPressShopStorageZoneSaveState;

UENUM(BlueprintType)
enum class ELBPressShopStorageType : uint8
{
    BareCoils,
    PreparedBlanks,
    FinishedPanelStillages,
    Scrap,
    MaintenanceParts,
    Quarantine,
    /** Empty pressed-panel stillages waiting to be allocated to an S07 loading bay. */
    EmptyPanelStillages
};

USTRUCT(BlueprintType)
struct FLBPressShopBuildBay
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FName BayId = TEXT("PRESS_TRAIN_BAY");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FVector Centre = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder", meta=(ClampMin="0.0"))
    FVector HalfExtent = FVector(7500.0, 7500.0, 1000.0);
};

USTRUCT(BlueprintType)
struct FLBPressShopProtectedArea
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FName AreaId = TEXT("PROTECTED_AISLE");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FVector Centre = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder", meta=(ClampMin="0.0"))
    FVector HalfExtent = FVector(100.0, 100.0, 1000.0);
};

USTRUCT(BlueprintType)
struct FLBPressShopUtilitySpine
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FName SpineId = TEXT("PRESS_SHOP_UTILITY_SPINE");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FVector Start = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FVector End = FVector(1000.0, 0.0, 0.0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder", meta=(ClampMin="0.0"))
    float MaximumConnectionDistanceCm = 1500.0f;
};

USTRUCT(BlueprintType)
struct FLBPressShopStorageBay
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FName BayId = TEXT("STORAGE_BAY");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FVector Centre = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder", meta=(ClampMin="0.0"))
    FVector HalfExtent = FVector(500.0, 500.0, 250.0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    TArray<ELBPressShopStorageType> AcceptedTypes;

    /** Authored gameplay footprint for a single zone; never inferred from presentation geometry. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder", meta=(ClampMin="0.0"))
    FVector DefaultZoneHalfExtent = FVector::ZeroVector;

    /** Authored material-unit capacity for a single zone. Zero means unresolved/TBC and blocks placement. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder", meta=(ClampMin="0"))
    int32 DefaultCapacity = 0;

    /** Authored centre pitch per stored unit in local zone X/Y. Zero remains TBC. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder", meta=(ClampMin="0.0"))
    FVector2D StorageUnitPitchCm = FVector2D::ZeroVector;

    /** Clear floor margin inside every edge before the first storage position. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder", meta=(ClampMin="0.0"))
    float BoundaryClearanceCm = 0.0f;
};

USTRUCT(BlueprintType)
struct FLBPressShopLogisticsSpine
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FName SpineId = TEXT("AGV_ROUTE");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FVector Start = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    FVector End = FVector(1000.0, 0.0, 0.0);

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder", meta=(ClampMin="0.0"))
    float MaximumAccessDistanceCm = 600.0f;
};

/** Map-owned authority for buildable floor, protected routes and verified utility reach. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPressShopBuildAuthority : public AActor
{
    GENERATED_BODY()

public:
    ALBPressShopBuildAuthority();

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    TArray<FLBPressShopBuildBay> BuildBays;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    TArray<FLBPressShopProtectedArea> ProtectedAreas;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    TArray<FLBPressShopUtilitySpine> UtilitySpines;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    TArray<FLBPressShopStorageBay> StorageBays;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="Cairnwell|Factory Builder")
    TArray<FLBPressShopLogisticsSpine> LogisticsSpines;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder")
    bool EvaluateTrainTransform(const FTransform& WorldTransform, FString& OutReason) const;

    /** Python/Blueprint-friendly diagnostic preserving both validity and the exact player-facing reason. */
    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder")
    FString DescribeTrainTransform(const FTransform& WorldTransform) const;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder")
    bool EvaluateStorageTransform(ELBPressShopStorageType StorageType,
        const FTransform& WorldTransform, const FVector& HalfExtent, FString& OutReason) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder")
    FString DescribeStorageTransform(ELBPressShopStorageType StorageType,
        const FTransform& WorldTransform, const FVector& HalfExtent) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder")
    bool GetStoragePlacementDefaults(ELBPressShopStorageType StorageType,
        FVector& OutHalfExtent, int32& OutCapacity, FString& OutReason) const;

    UFUNCTION(BlueprintPure, Category="Cairnwell|Factory Builder")
    bool CalculateStorageLayout(ELBPressShopStorageType StorageType,
        const FTransform& WorldTransform, const FVector& HalfExtent,
        int32& OutColumns, int32& OutRows, int32& OutCapacity, FString& OutReason) const;

    UFUNCTION(BlueprintCallable, Category="Cairnwell|Factory Builder")
    bool PlaceStorageZone(ELBPressShopStorageType StorageType, const FTransform& WorldTransform,
        const FVector& HalfExtent, int32 Capacity, ALBPressShopStorageZone*& OutZone, FString& OutReason);

    bool CaptureStorageZones(TArray<FLBPressShopStorageZoneSaveState>& OutStates) const;
    /** Mutation-free campaign preflight for the complete persisted storage set. */
    bool ValidateStorageSaveSet(const TArray<FLBPressShopStorageZoneSaveState>& States,
        FString& OutReason) const;
    bool RestoreStorageZones(const TArray<FLBPressShopStorageZoneSaveState>& States, FString& OutReason);

    bool EvaluateTrainEnvelope(const FBox& WorldEnvelope, FString& OutReason) const;

private:
    UPROPERTY(Transient)
    int32 NextStorageSequence = 1;

    static float DistanceSquaredToSegment2D(const FVector& Point, const FVector& Start, const FVector& End);
};
