#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "LBPressShopMaterialFlowController.generated.h"

class ALBPR004Station;
class ALBPR005Station;
class ALBPR008Station;
class ALBPR009Station;
class ALBPR010Station;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPressShopCoilTransferred, FString, CoilId, FName, TransactionId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FLBPressShopBlankTransferred, FName, BlankId, FName, TransactionId);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FLBPressShopStackTransferred, FName, StackId, int32, BlankCount, FName, TransactionId);

/** Transactional front-end material handoff. PR-004 remains authoritative until PR-005 accepts the exact coil. */
UCLASS(BlueprintType)
class LINEBOSSCARFACTORY_API ALBPressShopMaterialFlowController : public AActor
{
    GENERATED_BODY()

public:
    ALBPressShopMaterialFlowController();
    virtual void BeginPlay() override;

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Press Shop|Material Flow")
    void BindStations(ALBPR004Station* InPR004, ALBPR005Station* InPR005);

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Press Shop|Material Flow")
    bool CanTransferReadyCoil(float WidthMillimetres, TArray<FText>& BlockingReasons) const;

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Press Shop|Material Flow")
    bool TransferReadyCoilToPR005(FName TransactionId, float WidthMillimetres = 1500.0f);

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Press Shop|Material Flow")
    void BindBlankStations(ALBPR008Station* InPR008, ALBPR009Station* InPR009);

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Press Shop|Material Flow")
    bool CanTransferProducedBlank(TArray<FText>& BlockingReasons) const;

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Press Shop|Material Flow")
    bool TransferProducedBlankToPR009(FName TransactionId);

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Press Shop|Material Flow")
    void BindStackStations(ALBPR009Station* InPR009, ALBPR010Station* InPR010);

    UFUNCTION(BlueprintPure, Category = "Cairnwell|Press Shop|Material Flow")
    bool CanTransferReleasedStack(TArray<FText>& BlockingReasons) const;

    UFUNCTION(BlueprintCallable, Category = "Cairnwell|Press Shop|Material Flow")
    bool TransferReleasedStackToPR010(FName TransactionId);

    UPROPERTY(BlueprintAssignable, Category = "Cairnwell|Press Shop|Material Flow")
    FLBPressShopCoilTransferred OnCoilTransferred;

    UPROPERTY(BlueprintAssignable, Category = "Cairnwell|Press Shop|Material Flow")
    FLBPressShopBlankTransferred OnBlankTransferred;

    UPROPERTY(BlueprintAssignable, Category = "Cairnwell|Press Shop|Material Flow")
    FLBPressShopStackTransferred OnStackTransferred;

protected:
    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Cairnwell|Press Shop|Material Flow")
    TObjectPtr<ALBPR004Station> PR004Station;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Cairnwell|Press Shop|Material Flow")
    TObjectPtr<ALBPR005Station> PR005Station;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Cairnwell|Press Shop|Material Flow")
    TObjectPtr<ALBPR008Station> PR008Station;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Cairnwell|Press Shop|Material Flow")
    TObjectPtr<ALBPR009Station> PR009Station;

    UPROPERTY(EditInstanceOnly, BlueprintReadOnly, Category = "Cairnwell|Press Shop|Material Flow")
    TObjectPtr<ALBPR010Station> PR010Station;
};
