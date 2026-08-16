#include "LBPressShopMaterialFlowController.h"

#include "EngineUtils.h"
#include "LBPR004Station.h"
#include "LBPR005Station.h"
#include "LBPR008Station.h"
#include "LBPR009Station.h"
#include "LBPR010Station.h"

#define LOCTEXT_NAMESPACE "LineBossPressShopMaterialFlow"

ALBPressShopMaterialFlowController::ALBPressShopMaterialFlowController()
{
    PrimaryActorTick.bCanEverTick = false;
}

void ALBPressShopMaterialFlowController::BeginPlay()
{
    Super::BeginPlay();
    if (!PR004Station)
    {
        for (TActorIterator<ALBPR004Station> It(GetWorld()); It; ++It) { PR004Station = *It; break; }
    }
    if (!PR005Station)
    {
        for (TActorIterator<ALBPR005Station> It(GetWorld()); It; ++It) { PR005Station = *It; break; }
    }
    if (!PR008Station)
    {
        for (TActorIterator<ALBPR008Station> It(GetWorld()); It; ++It) { PR008Station = *It; break; }
    }
    if (!PR009Station)
    {
        for (TActorIterator<ALBPR009Station> It(GetWorld()); It; ++It) { PR009Station = *It; break; }
    }
    if (!PR010Station)
    {
        for (TActorIterator<ALBPR010Station> It(GetWorld()); It; ++It) { PR010Station = *It; break; }
    }
}

void ALBPressShopMaterialFlowController::BindBlankStations(ALBPR008Station* InPR008, ALBPR009Station* InPR009)
{
    PR008Station = InPR008;
    PR009Station = InPR009;
}

bool ALBPressShopMaterialFlowController::CanTransferProducedBlank(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (!PR008Station) BlockingReasons.Add(LOCTEXT("MissingPR008", "PR-008 is not bound."));
    if (!PR009Station) BlockingReasons.Add(LOCTEXT("MissingPR009", "PR-009 is not bound."));
    if (!BlockingReasons.IsEmpty()) return false;

    TArray<FText> PR008Reasons;
    PR008Station->CanReleaseBlank(PR008Reasons);
    BlockingReasons.Append(PR008Reasons);
    TArray<FText> PR009Reasons;
    PR009Station->CanAcceptUpstreamBlank(PR009Reasons);
    BlockingReasons.Append(PR009Reasons);
    return BlockingReasons.IsEmpty();
}

bool ALBPressShopMaterialFlowController::TransferProducedBlankToPR009(FName TransactionId)
{
    if (TransactionId.IsNone()) return false;
    TArray<FText> BlockingReasons;
    if (!CanTransferProducedBlank(BlockingReasons)) return false;

    const FLBPR008SaveState PR008Before = PR008Station->CaptureSaveState();
    const FLBPR009SaveState PR009Before = PR009Station->CaptureSaveState();
    FName BlankId;
    if (!PR008Station->RequestBlankHandoff(TransactionId, BlankId)
        || !PR009Station->AcceptUpstreamBlank(BlankId)
        || !PR008Station->ConfirmBlankHandoff(TransactionId))
    {
        PR008Station->RestoreSaveState(PR008Before);
        PR009Station->RestoreSaveState(PR009Before);
        return false;
    }

    OnBlankTransferred.Broadcast(BlankId, TransactionId);
    return true;
}

void ALBPressShopMaterialFlowController::BindStackStations(ALBPR009Station* InPR009, ALBPR010Station* InPR010)
{
    PR009Station = InPR009;
    PR010Station = InPR010;
}

bool ALBPressShopMaterialFlowController::CanTransferReleasedStack(TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (!PR009Station) BlockingReasons.Add(LOCTEXT("StackMissingPR009", "PR-009 is not bound."));
    if (!PR010Station) BlockingReasons.Add(LOCTEXT("StackMissingPR010", "PR-010 is not bound."));
    if (!BlockingReasons.IsEmpty()) return false;
    TArray<FText> PR009Reasons;
    PR009Station->CanReleaseCompletedStack(PR009Reasons);
    BlockingReasons.Append(PR009Reasons);
    TArray<FText> PR010Reasons;
    PR010Station->CanAcceptUpstreamStack(PR010Reasons);
    BlockingReasons.Append(PR010Reasons);
    return BlockingReasons.IsEmpty();
}

bool ALBPressShopMaterialFlowController::TransferReleasedStackToPR010(FName TransactionId)
{
    if (TransactionId.IsNone()) return false;
    TArray<FText> BlockingReasons;
    if (!CanTransferReleasedStack(BlockingReasons)) return false;

    const FLBPR009SaveState PR009Before = PR009Station->CaptureSaveState();
    const FLBPR010SaveState PR010Before = PR010Station->CaptureSaveState();
    FName StackId;
    TArray<FName> BlankIds;
    if (!PR009Station->RequestStackHandoff(TransactionId, StackId, BlankIds)
        || !PR010Station->OfferUpstreamStackWithManifest(StackId, BlankIds)
        || !PR009Station->ConfirmStackHandoff(TransactionId))
    {
        PR009Station->RestoreSaveState(PR009Before);
        PR010Station->RestoreSaveState(PR010Before);
        return false;
    }

    OnStackTransferred.Broadcast(StackId, BlankIds.Num(), TransactionId);
    return true;
}

void ALBPressShopMaterialFlowController::BindStations(ALBPR004Station* InPR004, ALBPR005Station* InPR005)
{
    PR004Station = InPR004;
    PR005Station = InPR005;
}

bool ALBPressShopMaterialFlowController::CanTransferReadyCoil(float WidthMillimetres,
    TArray<FText>& BlockingReasons) const
{
    BlockingReasons.Reset();
    if (!PR004Station) BlockingReasons.Add(LOCTEXT("MissingPR004", "PR-004 is not bound."));
    if (!PR005Station) BlockingReasons.Add(LOCTEXT("MissingPR005", "PR-005 is not bound."));
    if (!BlockingReasons.IsEmpty()) return false;

    TArray<FText> PR004Reasons;
    PR004Station->CanReleaseCoil(PR004Reasons);
    BlockingReasons.Append(PR004Reasons);
    TArray<FText> PR005Reasons;
    PR005Station->CanLoadCoil(PR004Station->GetCurrentCoilId(), WidthMillimetres, PR005Reasons);
    BlockingReasons.Append(PR005Reasons);
    if (PR004Station->GetCurrentHeatId().IsEmpty() || PR004Station->GetCurrentSupplierLotId().IsEmpty()
        || PR004Station->GetCurrentTraceabilityBarcode().IsEmpty())
    {
        BlockingReasons.Add(LOCTEXT("MissingTraceability", "The PR-004 coil is missing heat, supplier lot or barcode traceability."));
    }
    return BlockingReasons.IsEmpty();
}

bool ALBPressShopMaterialFlowController::TransferReadyCoilToPR005(FName TransactionId, float WidthMillimetres)
{
    if (TransactionId.IsNone()) return false;
    TArray<FText> BlockingReasons;
    if (!CanTransferReadyCoil(WidthMillimetres, BlockingReasons)) return false;

    FLBPR004SaveState PR004Before;
    if (!PR004Station->GetStableSaveState(PR004Before)) return false;
    const FLBPR005SaveState PR005Before = PR005Station->CaptureSaveState();
    const FString CoilId = PR004Station->GetCurrentCoilId();

    if (!PR004Station->RequestHandoff(TransactionId)
        || !PR005Station->LoadCoilWithTraceability(CoilId, PR004Station->GetCurrentHeatId(),
            PR004Station->GetCurrentSupplierLotId(), PR004Station->GetCurrentTraceabilityBarcode(), WidthMillimetres)
        || !PR004Station->ConfirmHandoffComplete(TransactionId))
    {
        PR004Station->RestoreSaveState(PR004Before);
        PR005Station->RestoreSaveState(PR005Before);
        return false;
    }

    OnCoilTransferred.Broadcast(CoilId, TransactionId);
    return true;
}

#undef LOCTEXT_NAMESPACE
