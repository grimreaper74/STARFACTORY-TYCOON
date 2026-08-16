#include "LBControlRoomOperationsConsole.h"

#include "Components/BoxComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "LBPR005Station.h"
#include "LBPR006Station.h"
#include "LBPR007Station.h"
#include "LBPR008Station.h"
#include "LBPR009Station.h"
#include "LBPR010Station.h"
#include "LBPressTrainAStation.h"
#include "LBPressShopSupportFleetController.h"
#include "LBPressShopMaterialFlowController.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
const TArray<FName> PanelFamilies = {
    TEXT("ROOF_OUTER"), TEXT("MAIN_FLOOR"), TEXT("DOOR_OUTER"), TEXT("WHEELHOUSE")};
const TArray<FName> TrainIds = []
{
    TArray<FName> Result;
    for (TCHAR Letter = TCHAR('A'); Letter <= TCHAR('Z'); ++Letter)
        Result.Add(FName(*FString::Printf(TEXT("TRAIN_%c"), Letter)));
    return Result;
}();
const TArray<FName> SupportUnitIds = {
    TEXT("LB-CR01-01"), TEXT("LB-CR01-02"), TEXT("LB-MR01-01"), TEXT("LB-MR01-02")};

FString DisplayName(const FName Name)
{
    return FName::NameToDisplayString(Name.ToString(), false).ToUpper();
}

template <typename EnumType>
FString EnumDisplay(EnumType Value)
{
    if (const UEnum* Enum = StaticEnum<EnumType>())
    {
        return FName::NameToDisplayString(Enum->GetNameStringByValue(static_cast<int64>(Value)), false).ToUpper();
    }
    return TEXT("UNKNOWN");
}
}

ALBControlRoomOperationsConsole::ALBControlRoomOperationsConsole()
{
    PrimaryActorTick.bCanEverTick = true;
    ConsoleRoot = CreateDefaultSubobject<USceneComponent>(TEXT("OperationsConsoleRoot"));
    SetRootComponent(ConsoleRoot);

    ScreenBack = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("OperationsScreenBack"));
    ScreenBack->SetupAttachment(ConsoleRoot);
    // One contained industrial HMI face: header, live state, alarm and all
    // physical control rows must remain on the panel rather than floating
    // above/below the console geometry.
    ScreenBack->SetRelativeLocation(FVector(0.0f, 0.0f, -10.0f));
    ScreenBack->SetRelativeScale3D(FVector(0.035f, 1.55f, 2.0f));
    ScreenBack->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ScreenBack->SetCanEverAffectNavigation(false);
    ScreenBack->SetCastShadow(false);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded())
    {
        PrimitiveCubeMesh = Cube.Object;
        ScreenBack->SetStaticMesh(PrimitiveCubeMesh);
    }
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> ScreenMaterial(
        TEXT("/Game/LineBoss/Candidates/ControlRoom/OperationsConsole_v271/Materials/M_CA_OperationsScreenDark_v271.M_CA_OperationsScreenDark_v271"));
    if (ScreenMaterial.Succeeded())
    {
        ScreenFaceMaterial = ScreenMaterial.Object;
        ScreenBack->SetMaterial(0, ScreenFaceMaterial);
    }
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> ButtonMaterial(
        TEXT("/Game/LineBoss/Candidates/ControlRoom/OperationsConsole_v271/Materials/M_CA_OperationsButtonCharcoal_v271.M_CA_OperationsButtonCharcoal_v271"));
    if (ButtonMaterial.Succeeded()) ButtonFaceMaterial = ButtonMaterial.Object;

    ScreenBezel = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("OperationsScreenBezel"));
    ScreenBezel->SetupAttachment(ConsoleRoot);
    ScreenBezel->SetRelativeLocation(FVector(-2.0f, 0.0f, -10.0f));
    ScreenBezel->SetRelativeScale3D(FVector(0.055f, 1.68f, 2.13f));
    ScreenBezel->SetStaticMesh(PrimitiveCubeMesh);
    if (ButtonFaceMaterial) ScreenBezel->SetMaterial(0, ButtonFaceMaterial);
    ScreenBezel->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    ScreenBezel->SetCanEverAffectNavigation(false);

    HeaderText = CreateText(TEXT("OperationsHeader"), 70.0f, 5.0f, FColor(226, 224, 212));
    HeaderText->SetText(FText::FromString(TEXT("CAIRNWELL AUTOMOTIVE  /  MOORCROSS WORKS\nPRESS SHOP OPERATIONS")));
    OrderText = CreateText(TEXT("OperationsOrder"), 34.0f, 4.0f, FColor(205, 218, 212));
    ProductionText = CreateText(TEXT("OperationsProduction"), 4.0f, 3.6f, FColor(205, 218, 212));
    AuthorityText = CreateText(TEXT("OperationsAuthority"), -25.0f, 3.2f, FColor(99, 200, 168));
    AlarmText = CreateText(TEXT("OperationsAlarm"), -52.0f, 3.0f, FColor(227, 166, 0));

    PanelButton = CreateInteractionButton(TEXT("BTN_PANEL"), -62.5f, -65.0f, TEXT("PANEL"));
    QuantityDownButton = CreateInteractionButton(TEXT("BTN_QTY_DOWN"), -37.5f, -65.0f, TEXT("-100"));
    QuantityUpButton = CreateInteractionButton(TEXT("BTN_QTY_UP"), -12.5f, -65.0f, TEXT("+100"));
    PriorityButton = CreateInteractionButton(TEXT("BTN_PRIORITY"), 12.5f, -65.0f, TEXT("PRIORITY"));
    TrainButton = CreateInteractionButton(TEXT("BTN_TRAIN"), 37.5f, -65.0f, TEXT("TRAIN"));
    ModeButton = CreateInteractionButton(TEXT("BTN_MODE"), 62.5f, -65.0f, TEXT("MODE"));
    CreateButton = CreateInteractionButton(TEXT("BTN_CREATE"), -62.5f, -78.0f, TEXT("CREATE"));
    SelectCoilButton = CreateInteractionButton(TEXT("BTN_SELECT_COIL"), -37.5f, -78.0f, TEXT("SELECT"));
    LoadCoilButton = CreateInteractionButton(TEXT("BTN_LOAD_COIL"), -12.5f, -78.0f, TEXT("LOAD"));
    StartButton = CreateInteractionButton(TEXT("BTN_START"), 12.5f, -78.0f, TEXT("START"));
    PauseButton = CreateInteractionButton(TEXT("BTN_PAUSE"), 37.5f, -78.0f, TEXT("PAUSE"));
    StopButton = CreateInteractionButton(TEXT("BTN_STOP"), 62.5f, -78.0f, TEXT("STOP"));
    SupportUnitButton = CreateInteractionButton(TEXT("BTN_SUPPORT_UNIT"), -37.5f, -91.0f, TEXT("ROBOT"));
    SupportDispatchButton = CreateInteractionButton(TEXT("BTN_SUPPORT_DISPATCH"), 0.0f, -91.0f, TEXT("DISPATCH"));
    SupportRecallButton = CreateInteractionButton(TEXT("BTN_SUPPORT_RECALL"), 37.5f, -91.0f, TEXT("RECALL"));
}

UTextRenderComponent* ALBControlRoomOperationsConsole::CreateText(
    const TCHAR* Name, float LocalZ, float WorldSize, const FColor& Colour)
{
    UTextRenderComponent* Text = CreateDefaultSubobject<UTextRenderComponent>(Name);
    Text->SetupAttachment(ConsoleRoot);
    Text->SetRelativeLocation(FVector(4.0f, 0.0f, LocalZ));
    Text->SetHorizontalAlignment(EHTA_Center);
    Text->SetVerticalAlignment(EVRTA_TextCenter);
    Text->SetWorldSize(WorldSize);
    Text->SetTextRenderColor(Colour);
    Text->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Text->SetCastShadow(false);
    return Text;
}

UBoxComponent* ALBControlRoomOperationsConsole::CreateInteractionButton(
    const TCHAR* Name, float LocalY, float LocalZ, const TCHAR* Label)
{
    UBoxComponent* Button = CreateDefaultSubobject<UBoxComponent>(Name);
    Button->SetupAttachment(ConsoleRoot);
    Button->SetRelativeLocation(FVector(7.0f, LocalY, LocalZ));
    Button->SetBoxExtent(FVector(2.0f, 10.5f, 5.0f));
    Button->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
    Button->SetCollisionResponseToAllChannels(ECR_Ignore);
    Button->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Button->SetCanEverAffectNavigation(false);
    Button->SetHiddenInGame(true);

    UTextRenderComponent* Text = CreateDefaultSubobject<UTextRenderComponent>(
        *FString::Printf(TEXT("%s_LABEL"), Name));
    Text->SetupAttachment(Button);
    Text->SetRelativeLocation(FVector(3.0f, 0.0f, 0.0f));
    Text->SetText(FText::FromString(Label));
    Text->SetHorizontalAlignment(EHTA_Center);
    Text->SetVerticalAlignment(EVRTA_TextCenter);
    Text->SetWorldSize(2.6f);
    Text->SetTextRenderColor(FColor(12, 206, 135));
    Text->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Text->SetCastShadow(false);

    UStaticMeshComponent* Face = CreateDefaultSubobject<UStaticMeshComponent>(
        *FString::Printf(TEXT("%s_FACE"), Name));
    Face->SetupAttachment(Button);
    Face->SetRelativeLocation(FVector(0.0f, 0.0f, 0.0f));
    Face->SetRelativeScale3D(FVector(0.04f, 0.20f, 0.08f));
    Face->SetStaticMesh(PrimitiveCubeMesh);
    if (ButtonFaceMaterial) Face->SetMaterial(0, ButtonFaceMaterial);
    Face->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Face->SetCanEverAffectNavigation(false);
    Face->SetCastShadow(false);
    return Button;
}

void ALBControlRoomOperationsConsole::BeginPlay()
{
    Super::BeginPlay();
    // Existing retained maps may serialize an earlier diagnostic-cyan material
    // override. The native release presentation is authoritative at runtime.
    if (ScreenBack && ScreenFaceMaterial) ScreenBack->SetMaterial(0, ScreenFaceMaterial);
    BindExistingAuthority();
    RefreshPresentation();
}

void ALBControlRoomOperationsConsole::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    RefreshAccumulator += FMath::Max(0.0f, DeltaSeconds);
    if (RefreshAccumulator >= 0.25f)
    {
        RefreshAccumulator = 0.0f;
        if (!BoundPR005.IsValid() || !BoundPR006.IsValid() || !BoundPR007.IsValid()
            || !BoundPR008.IsValid() || !BoundPR009.IsValid() || !BoundPR010.IsValid()
            || !BoundMaterialFlow.IsValid()
            || !BoundSupportFleet.IsValid()
            || !GetAssignedPressTrain()) BindExistingAuthority();
        if (State.OrderState == ELBControlRoomOrderState::Running
            && State.OperatingMode == ELBControlRoomOperatingMode::Automatic)
        {
            AdvanceAutomaticOrder();
        }
        RefreshPresentation();
    }
}

void ALBControlRoomOperationsConsole::BindExistingAuthority()
{
    BoundPR005.Reset();
    BoundPR006.Reset();
    BoundPR007.Reset();
    BoundPR008.Reset();
    BoundPR009.Reset();
    BoundPR010.Reset();
    BoundMaterialFlow.Reset();
    BoundSupportFleet.Reset();
    BoundPressTrains.Reset();
    if (UWorld* World = GetWorld())
    {
        for (TActorIterator<ALBPR005Station> It(World); It; ++It)
        {
            BoundPR005 = *It;
            break;
        }
        for (TActorIterator<ALBPR006Station> It(World); It; ++It) { BoundPR006 = *It; break; }
        for (TActorIterator<ALBPR007Station> It(World); It; ++It) { BoundPR007 = *It; break; }
        for (TActorIterator<ALBPR008Station> It(World); It; ++It) { BoundPR008 = *It; break; }
        for (TActorIterator<ALBPR009Station> It(World); It; ++It) { BoundPR009 = *It; break; }
        for (TActorIterator<ALBPR010Station> It(World); It; ++It) { BoundPR010 = *It; break; }
        for (TActorIterator<ALBPressShopMaterialFlowController> It(World); It; ++It)
        {
            BoundMaterialFlow = *It;
            break;
        }
        for (TActorIterator<ALBPressShopSupportFleetController> It(World); It; ++It)
        {
            BoundSupportFleet = *It;
            break;
        }
        for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
        {
            ALBPressTrainAStation* Train = *It;
            if (!Train) continue;
            const FName TrainId = Train->GetHMIStatus().TrainId;
            if (TrainIds.Contains(TrainId) && !BoundPressTrains.Contains(TrainId))
            {
                BoundPressTrains.Add(TrainId, Train);
            }
        }
        if (ALBPressTrainAStation* Assigned = GetAssignedPressTrain())
            State.AssignedTrainGuid = Assigned->GetPersistentTrainGuid();
    }
}

ALBPressTrainAStation* ALBControlRoomOperationsConsole::GetAssignedPressTrain() const
{
    if (State.AssignedTrainGuid.IsValid())
    {
        for (const TPair<FName, TWeakObjectPtr<ALBPressTrainAStation>>& Pair : BoundPressTrains)
            if (ALBPressTrainAStation* Train = Pair.Value.Get())
                if (Train->GetPersistentTrainGuid() == State.AssignedTrainGuid) return Train;
    }
    if (const TWeakObjectPtr<ALBPressTrainAStation>* Found = BoundPressTrains.Find(State.AssignedTrain))
    {
        return Found->Get();
    }
    return nullptr;
}

void ALBControlRoomOperationsConsole::RefreshForEditorEvidence()
{
    BindExistingAuthority();
    RefreshPresentation();
}

bool ALBControlRoomOperationsConsole::HandleComponentInteraction(UPrimitiveComponent* HitComponent)
{
    if (!HitComponent) return false;
    if (HitComponent == PanelButton) CyclePanelFamily();
    else if (HitComponent == QuantityDownButton) DecreaseQuantity();
    else if (HitComponent == QuantityUpButton) IncreaseQuantity();
    else if (HitComponent == PriorityButton) CyclePriority();
    else if (HitComponent == TrainButton) CycleAssignedTrain();
    else if (HitComponent == ModeButton) ToggleOperatingMode();
    else if (HitComponent == CreateButton) return CreateProductionOrder();
    else if (HitComponent == SelectCoilButton) return SelectAvailableCoil();
    else if (HitComponent == LoadCoilButton) return LoadSelectedCoil();
    else if (HitComponent == StartButton) return StartOrResumeOrder();
    else if (HitComponent == PauseButton) return PauseOrder();
    else if (HitComponent == StopButton) return StopOrder();
    else if (HitComponent == SupportUnitButton) CycleSupportUnit();
    else if (HitComponent == SupportDispatchButton) return DispatchSelectedSupportUnit();
    else if (HitComponent == SupportRecallButton) return RecallSelectedSupportUnit();
    else return false;
    RefreshPresentation();
    return true;
}

void ALBControlRoomOperationsConsole::CycleSupportUnit()
{
    int32 Index = SupportUnitIds.IndexOfByKey(SelectedSupportUnitId);
    SelectedSupportUnitId = SupportUnitIds[(Index + 1) % SupportUnitIds.Num()];
    State.LastAlarm = FString::Printf(TEXT("SUPPORT ROBOT %s SELECTED"), *SelectedSupportUnitId.ToString());
}

bool ALBControlRoomOperationsConsole::DispatchSelectedSupportUnit()
{
    ALBPressShopSupportFleetController* Fleet = BoundSupportFleet.Get();
    if (!Fleet || !Fleet->IsFleetReady())
    {
        SetHold(TEXT("SUPPORT FLEET AUTHORITY NOT READY"));
        return false;
    }
    if (!Fleet->DispatchUnit(SelectedSupportUnitId))
    {
        SetHold(FString::Printf(TEXT("%s DISPATCH INTERLOCK REJECTED"), *SelectedSupportUnitId.ToString()));
        return false;
    }
    State.LastAlarm = FString::Printf(TEXT("%s DISPATCH ACCEPTED"), *SelectedSupportUnitId.ToString());
    RefreshPresentation();
    return true;
}

bool ALBControlRoomOperationsConsole::RecallSelectedSupportUnit()
{
    ALBPressShopSupportFleetController* Fleet = BoundSupportFleet.Get();
    if (!Fleet || !Fleet->IsFleetReady())
    {
        SetHold(TEXT("SUPPORT FLEET AUTHORITY NOT READY"));
        return false;
    }
    if (!Fleet->ReturnUnitToDock(SelectedSupportUnitId))
    {
        SetHold(FString::Printf(TEXT("%s RECALL INTERLOCK REJECTED"), *SelectedSupportUnitId.ToString()));
        return false;
    }
    State.LastAlarm = FString::Printf(TEXT("%s RECALL ACCEPTED"), *SelectedSupportUnitId.ToString());
    RefreshPresentation();
    return true;
}

void ALBControlRoomOperationsConsole::CyclePanelFamily()
{
    int32 Index = PanelFamilies.IndexOfByKey(State.PanelFamily);
    Index = (Index + 1) % PanelFamilies.Num();
    State.PanelFamily = PanelFamilies[Index];
    State.AssignedTrain = TrainIds[Index];
    State.AssignedTrainGuid.Invalidate();
    if (const TWeakObjectPtr<ALBPressTrainAStation>* Found = BoundPressTrains.Find(State.AssignedTrain))
        if (ALBPressTrainAStation* Train = Found->Get()) State.AssignedTrainGuid = Train->GetPersistentTrainGuid();
    State.RecipeId = NAME_None;
    ResolvedRequiredStripWidthMillimetres = 0.0f;
    State.OrderState = ELBControlRoomOrderState::Draft;
    State.LastAlarm = TEXT("PANEL FAMILY CHANGED / RECIPE AUTHORITY REQUIRED");
}

void ALBControlRoomOperationsConsole::IncreaseQuantity()
{
    State.RequestedQuantity = FMath::Clamp(State.RequestedQuantity + 100, 0, 999900);
    State.OrderState = ELBControlRoomOrderState::Draft;
}

void ALBControlRoomOperationsConsole::DecreaseQuantity()
{
    State.RequestedQuantity = FMath::Clamp(State.RequestedQuantity - 100, 0, 999900);
    State.OrderState = ELBControlRoomOrderState::Draft;
}

void ALBControlRoomOperationsConsole::CyclePriority()
{
    State.Priority = static_cast<ELBControlRoomOrderPriority>(
        (static_cast<uint8>(State.Priority) + 1) % 3);
}

void ALBControlRoomOperationsConsole::CycleAssignedTrain()
{
    TArray<FName> Available;
    BoundPressTrains.GetKeys(Available);
    Available.Sort(FNameLexicalLess());
    const TArray<FName>& Choices = Available.IsEmpty() ? TrainIds : Available;
    int32 Index = Choices.IndexOfByKey(State.AssignedTrain);
    State.AssignedTrain = Choices[(Index + 1) % Choices.Num()];
    State.AssignedTrainGuid.Invalidate();
    if (const TWeakObjectPtr<ALBPressTrainAStation>* Found = BoundPressTrains.Find(State.AssignedTrain))
        if (ALBPressTrainAStation* Train = Found->Get()) State.AssignedTrainGuid = Train->GetPersistentTrainGuid();
    State.LastAlarm = TEXT("TRAIN CHANGED / COMPATIBILITY CHECK REQUIRED");
    State.OrderState = ELBControlRoomOrderState::Draft;
}

void ALBControlRoomOperationsConsole::ToggleOperatingMode()
{
    if (State.OrderState == ELBControlRoomOrderState::Running)
    {
        SetHold(TEXT("PAUSE OR STOP BEFORE CHANGING MODE"));
        return;
    }
    State.OperatingMode = State.OperatingMode == ELBControlRoomOperatingMode::Automatic
        ? ELBControlRoomOperatingMode::AssistedManual
        : ELBControlRoomOperatingMode::Automatic;
    State.LastAlarm = State.OperatingMode == ELBControlRoomOperatingMode::Automatic
        ? TEXT("AUTOMATIC MODE SELECTED")
        : TEXT("ASSISTED MANUAL / INTERLOCKS REMAIN ACTIVE");
}

bool ALBControlRoomOperationsConsole::CreateProductionOrder()
{
    if (!PanelFamilies.Contains(State.PanelFamily) || !TrainIds.Contains(State.AssignedTrain)
        || State.RequestedQuantity <= 0)
    {
        SetHold(TEXT("PANEL, TRAIN AND POSITIVE QUANTITY REQUIRED"));
        return false;
    }
    State.GoodPanels = 0;
    State.RejectedPanels = 0;
    State.NextOrchestrationTransactionSerial = 1;
    State.ActiveReleasedStackId = NAME_None;
    State.NextReleasedBlankIndex = 0;
    State.OrderState = ELBControlRoomOrderState::Ready;
    State.LastAlarm = State.RecipeId.IsNone()
        ? TEXT("ORDER SAVED / RECIPE AUTHORITY LINK REQUIRED TO RUN")
        : TEXT("ORDER READY / SELECT COIL");
    RefreshPresentation();
    return true;
}

bool ALBControlRoomOperationsConsole::SelectAvailableCoil()
{
    ALBPR005Station* Station = BoundPR005.Get();
    if (!Station)
    {
        SetHold(TEXT("COIL INVENTORY / PR-005 AUTHORITY LINK UNAVAILABLE"));
        return false;
    }
    const FLBPR005HMIStatus Status = Station->GetHMIStatus();
    if (Status.CoilId.IsEmpty() || Status.CoilWidthMillimetres <= 0.0f)
    {
        SetHold(TEXT("NO AUTHORITATIVE COIL AVAILABLE AT PR-005"));
        return false;
    }
    State.SelectedCoilId = Status.CoilId;
    State.SelectedCoilWidthMillimetres = Status.CoilWidthMillimetres;
    State.LastAlarm = TEXT("AUTHORITATIVE PR-005 COIL SELECTED");
    RefreshPresentation();
    return true;
}

bool ALBControlRoomOperationsConsole::LoadSelectedCoil()
{
    ALBPR005Station* Station = BoundPR005.Get();
    if (!Station || State.SelectedCoilId.IsEmpty() || State.SelectedCoilWidthMillimetres <= 0.0f)
    {
        SetHold(TEXT("SELECT AN AUTHORITATIVE COIL BEFORE LOAD"));
        return false;
    }
    if (!Station->LoadCoil(State.SelectedCoilId, State.SelectedCoilWidthMillimetres))
    {
        SetHold(TEXT("PR-005 LOAD INTERLOCK REJECTED COMMAND"));
        return false;
    }
    State.LastAlarm = TEXT("PR-005 ACCEPTED LOAD COIL COMMAND");
    RefreshPresentation();
    return true;
}

bool ALBControlRoomOperationsConsole::HasExecutableOrder() const
{
    return State.RequestedQuantity > 0 && !State.RecipeId.IsNone()
        && ResolvedRequiredStripWidthMillimetres > 0.0f && BoundPR005.IsValid()
        && BoundPR006.IsValid() && BoundPR007.IsValid() && BoundPR008.IsValid()
        && BoundPR009.IsValid() && BoundPR010.IsValid() && BoundMaterialFlow.IsValid()
        && GetAssignedPressTrain() != nullptr;
}

FName ALBControlRoomOperationsConsole::MakeOrchestrationTransactionId(const TCHAR* Stage)
{
    const int32 Serial = FMath::Max(1, State.NextOrchestrationTransactionSerial++);
    return FName(*FString::Printf(TEXT("MCR-%s-%06d"), Stage, Serial));
}

bool ALBControlRoomOperationsConsole::RecordAuthoritativePanelWithoutMaterialEstimate(
    const FString& NewBufferStatus)
{
    if (State.OrderState != ELBControlRoomOrderState::Running || NewBufferStatus.IsEmpty()) return false;
    ++State.GoodPanels;
    State.BufferStatus = NewBufferStatus;
    if (State.GoodPanels >= State.RequestedQuantity)
    {
        State.OrderState = ELBControlRoomOrderState::Completed;
        State.LastAlarm = TEXT("REQUESTED GOOD-PANEL QUANTITY COMPLETE");
        RequestWholeLineControlledStop();
    }
    return true;
}

void ALBControlRoomOperationsConsole::AdvanceAutomaticOrder()
{
    ALBPressShopMaterialFlowController* Flow = BoundMaterialFlow.Get();
    ALBPR005Station* PR005 = BoundPR005.Get();
    ALBPR006Station* PR006 = BoundPR006.Get();
    ALBPR007Station* PR007 = BoundPR007.Get();
    ALBPR008Station* PR008 = BoundPR008.Get();
    ALBPR009Station* PR009 = BoundPR009.Get();
    ALBPR010Station* PR010 = BoundPR010.Get();
    ALBPressTrainAStation* Train = GetAssignedPressTrain();
    if (!Flow || !PR005 || !PR006 || !PR007 || !PR008 || !PR009 || !PR010 || !Train)
    {
        RequestWholeLineControlledStop();
        SetHold(TEXT("AUTOMATIC ORDER HELD / MATERIAL-FLOW AUTHORITY LOST"));
        return;
    }

    const FLBPR005HMIStatus PR005Status = PR005->GetHMIStatus();
    const FLBPR006HMIStatus PR006Status = PR006->GetHMIStatus();
    const FLBPR007HMIStatus PR007Status = PR007->GetHMIStatus();
    const FLBPR008HMIStatus PR008Status = PR008->GetHMIStatus();
    const FLBPR009HMIStatus PR009Status = PR009->GetHMIStatus();
    const FLBPR010HMIStatus PR010Status = PR010->GetHMIStatus();
    const FLBPressTrainAHMIStatus TrainStatus = Train->GetHMIStatus();
    if (PR005Status.MachineState == ELBStationState::Fault || PR006Status.State == ELBPR006State::Fault
        || PR007Status.State == ELBPR007State::Fault || PR008Status.State == ELBPR008State::Fault
        || PR009Status.State == ELBPR009State::Fault
        || PR010Status.State == ELBPR010State::Fault || TrainStatus.State == ELBPressTrainAState::Fault)
    {
        FString FaultAuthority = TEXT("DOWNSTREAM AUTHORITY");
        FString FaultName = TEXT("FAULT");
        if (PR005Status.MachineState == ELBStationState::Fault) { FaultAuthority = TEXT("PR-005"); FaultName = EnumDisplay(PR005Status.ActiveFault); }
        else if (PR006Status.State == ELBPR006State::Fault) { FaultAuthority = TEXT("PR-006"); FaultName = EnumDisplay(PR006Status.ActiveFault); }
        else if (PR007Status.State == ELBPR007State::Fault) { FaultAuthority = TEXT("PR-007"); FaultName = EnumDisplay(PR007Status.ActiveFault); }
        else if (PR008Status.State == ELBPR008State::Fault) { FaultAuthority = TEXT("PR-008"); FaultName = EnumDisplay(PR008Status.ActiveFault); }
        else if (PR009Status.State == ELBPR009State::Fault) { FaultAuthority = TEXT("PR-009"); FaultName = EnumDisplay(PR009Status.ActiveFault); }
        else if (PR010Status.State == ELBPR010State::Fault) { FaultAuthority = TEXT("PR-010"); FaultName = EnumDisplay(PR010Status.ActiveFault); }
        else { FaultAuthority = State.AssignedTrain.ToString(); FaultName = EnumDisplay(TrainStatus.ActiveFault); }
        RequestWholeLineControlledStop();
        SetHold(FString::Printf(TEXT("%s FAULT / %s / CONTROLLED LINE STOP"), *FaultAuthority, *FaultName));
        return;
    }

    const FName Source(TEXT("MW.MCR.LINE.CONSOLE"));
    const FName Authority(TEXT("CW.MW.CONTROL_ROOM"));
    TArray<FText> BlockingReasons;
    if (Flow->CanTransferProducedBlank(BlockingReasons))
    {
        if (!Flow->TransferProducedBlankToPR009(MakeOrchestrationTransactionId(TEXT("BLANK"))))
        {
            RequestWholeLineControlledStop();
            SetHold(TEXT("PR-008 TO PR-009 TRANSACTION ROLLED BACK"));
            return;
        }
        if (PR009->GetHMIStatus().State == ELBPR009State::Ready
            && !PR009->ExecuteRemoteCommand(ELBPR009Command::Start, Source, Authority))
        {
            RequestWholeLineControlledStop();
            SetHold(TEXT("PR-009 REJECTED TRACEABLE BLANK START"));
            return;
        }
        State.BufferStatus = TEXT("TRACEABLE BLANK AT PR-009");
    }

    BlockingReasons.Reset();
    if (Flow->CanTransferReleasedStack(BlockingReasons))
    {
        if (!Flow->TransferReleasedStackToPR010(MakeOrchestrationTransactionId(TEXT("STACK"))))
        {
            RequestWholeLineControlledStop();
            SetHold(TEXT("PR-009 TO PR-010 TRANSACTION ROLLED BACK"));
            return;
        }
        State.BufferStatus = TEXT("TRACEABLE STACK AT PR-010");
    }

    FLBPR010SaveState Buffer = PR010->CaptureSaveState();
    const bool bReleasedStackStillFeedingTrain = !State.ActiveReleasedStackId.IsNone()
        && Buffer.LastReleasedStackId == State.ActiveReleasedStackId
        && State.NextReleasedBlankIndex < Buffer.LastReleasedBlankIds.Num();
    if (!bReleasedStackStillFeedingTrain && Buffer.PendingDispatchLaneIndex < 0)
    {
        const TArray<TArray<FName>> Lanes = {
            Buffer.LaneAStackIds, Buffer.LaneBStackIds, Buffer.LaneCStackIds, Buffer.LaneDStackIds};
        for (int32 LaneIndex = 0; LaneIndex < Lanes.Num(); ++LaneIndex)
        {
            if (!Lanes[LaneIndex].IsEmpty())
            {
                PR010->RequestLaneDispatch(LaneIndex, MakeOrchestrationTransactionId(TEXT("TRAINRES")));
                break;
            }
        }
    }

    Buffer = PR010->CaptureSaveState();
    if (!Buffer.LastReleasedStackId.IsNone() && Buffer.LastReleasedStackId != State.ActiveReleasedStackId)
    {
        State.ActiveReleasedStackId = Buffer.LastReleasedStackId;
        State.NextReleasedBlankIndex = 0;
    }
    while (State.ActiveReleasedStackId == Buffer.LastReleasedStackId
        && Buffer.LastReleasedBlankIds.IsValidIndex(State.NextReleasedBlankIndex)
        && Train->GetPendingBlankCount() < 4)
    {
        const FName BlankId = Buffer.LastReleasedBlankIds[State.NextReleasedBlankIndex];
        const FName ReservationId = MakeOrchestrationTransactionId(TEXT("TRAINBLANK"));
        if (!Train->QueueReservedBlank(ReservationId, BlankId)) break;
        ++State.NextReleasedBlankIndex;
        State.BufferStatus = FString::Printf(TEXT("%s FEEDING %s"),
            *State.AssignedTrain.ToString(), *State.ActiveReleasedStackId.ToString());
    }

    const ELBPressTrainAState CurrentTrainState = Train->GetHMIStatus().State;
    if (Train->GetPendingBlankCount() > 0 && CurrentTrainState == ELBPressTrainAState::Isolated)
    {
        const FName TrainSource(*FString::Printf(TEXT("MW.MCR.%s.CONSOLE"), *State.AssignedTrain.ToString()));
        if (!Train->ExecuteRemoteCommand(ELBPressTrainACommand::PowerOn, TrainSource, Authority)
            || !Train->ExecuteRemoteCommand(ELBPressTrainACommand::Start, TrainSource, Authority))
        {
            RequestWholeLineControlledStop();
            SetHold(TEXT("SELECTED TRAIN REJECTED RESERVED BLANK START"));
            return;
        }
    }
    else if (Train->GetPendingBlankCount() > 0 && CurrentTrainState == ELBPressTrainAState::Ready)
    {
        const FName TrainSource(*FString::Printf(TEXT("MW.MCR.%s.CONSOLE"), *State.AssignedTrain.ToString()));
        if (!Train->ExecuteRemoteCommand(ELBPressTrainACommand::Start, TrainSource, Authority))
        {
            RequestWholeLineControlledStop();
            SetHold(TEXT("SELECTED TRAIN RESTART INTERLOCK REJECTED"));
            return;
        }
    }

    if (Train->GetHMIStatus().PendingPanelCount > 0)
    {
        const FName HandoffId = MakeOrchestrationTransactionId(TEXT("PANEL"));
        FName PanelId;
        if (!Train->RequestPanelHandoff(HandoffId, PanelId) || !Train->ConfirmPanelHandoff(HandoffId))
        {
            Train->CancelPanelHandoff(HandoffId);
            RequestWholeLineControlledStop();
            SetHold(TEXT("FINISHED-PANEL HANDOFF ROLLED BACK"));
            return;
        }
        RecordAuthoritativePanelWithoutMaterialEstimate(
            FString::Printf(TEXT("FINISHED PANEL %s RELEASED"), *PanelId.ToString()));
    }
}

bool ALBControlRoomOperationsConsole::StartOrResumeOrder()
{
    ALBPR005Station* Station = BoundPR005.Get();
    ALBPR006Station* PR006 = BoundPR006.Get();
    ALBPR007Station* PR007 = BoundPR007.Get();
    ALBPR008Station* PR008 = BoundPR008.Get();
    ALBPR009Station* PR009 = BoundPR009.Get();
    ALBPR010Station* PR010 = BoundPR010.Get();
    ALBPressTrainAStation* Train = GetAssignedPressTrain();
    if (!HasExecutableOrder() || !Station || !PR006 || !PR007 || !PR008 || !PR009 || !PR010 || !Train)
    {
        SetHold(TEXT("START HELD / RECIPE AND COMPLETE PR-005 TO PR-010 MATERIAL AUTHORITY REQUIRED"));
        return false;
    }
    const FLBPR005HMIStatus InitialPR005Status = Station->GetHMIStatus();
    const bool bPR005AlreadyMoving = InitialPR005Status.MachineState == ELBStationState::Starting
        || InitialPR005Status.MachineState == ELBStationState::Running;
    if (!bPR005AlreadyMoving
        && !Station->SelectRecipe(State.RecipeId, ResolvedRequiredStripWidthMillimetres))
    {
        SetHold(TEXT("PR-005 REJECTED AUTHORITATIVE RECIPE"));
        return false;
    }
    const ELBPR005ControlMode Mode = State.OperatingMode == ELBControlRoomOperatingMode::Automatic
        ? ELBPR005ControlMode::Automatic : ELBPR005ControlMode::Manual;
    if (!Station->SetControlMode(Mode) || (!bPR005AlreadyMoving && !Station->PressCycleStart()))
    {
        const FLBPR005HMIStatus Status = Station->GetHMIStatus();
        SetHold(Status.BlockingReasons.IsEmpty()
            ? TEXT("PR-005 START INTERLOCK REJECTED COMMAND")
            : Status.BlockingReasons[0].ToString().ToUpper());
        return false;
    }
    auto FailAndStop = [this](const FString& Reason) -> bool
    {
        RequestWholeLineControlledStop();
        SetHold(Reason);
        return false;
    };
    PR006->SetControlPower(true);
    const ELBPR006State PR006State = PR006->GetHMIStatus().State;
    if (PR006State != ELBPR006State::Running && PR006State != ELBPR006State::Calibrating
        && !PR006->StartLine())
    {
        const FLBPR006HMIStatus Status = PR006->GetHMIStatus();
        return FailAndStop(Status.BlockingReasons.IsEmpty()
            ? TEXT("PR-006 START INTERLOCK REJECTED COMMAND")
            : Status.BlockingReasons[0].ToString().ToUpper());
    }
    PR007->SetControlPower(true);
    const ELBPR007State PR007State = PR007->GetHMIStatus().State;
    if (PR007State != ELBPR007State::Running && PR007State != ELBPR007State::Priming
        && !PR007->StartLine())
    {
        const FLBPR007HMIStatus Status = PR007->GetHMIStatus();
        return FailAndStop(Status.BlockingReasons.IsEmpty()
            ? TEXT("PR-007 START INTERLOCK REJECTED COMMAND")
            : Status.BlockingReasons[0].ToString().ToUpper());
    }
    const FName LineSource(TEXT("MW.MCR.LINE.CONSOLE"));
    const FName Authority(TEXT("CW.MW.CONTROL_ROOM"));
    const ELBPR008State PR008State = PR008->GetHMIStatus().State;
    if (PR008State != ELBPR008State::Running && PR008State != ELBPR008State::Threading
        && (!PR008->ExecuteRemoteCommand(ELBPR008Command::PowerOn, LineSource, Authority)
            || !PR008->ExecuteRemoteCommand(ELBPR008Command::Start, LineSource, Authority)))
    {
        const FLBPR008HMIStatus Status = PR008->GetHMIStatus();
        return FailAndStop(Status.BlockingReasons.IsEmpty()
            ? TEXT("PR-008 START INTERLOCK REJECTED COMMAND")
            : Status.BlockingReasons[0].ToString().ToUpper());
    }
    if (PR009->GetHMIStatus().State == ELBPR009State::Isolated
        && !PR009->ExecuteRemoteCommand(ELBPR009Command::PowerOn, LineSource, Authority))
        return FailAndStop(TEXT("PR-009 POWER-ON INTERLOCK REJECTED COMMAND"));
    const ELBPR010State PR010State = PR010->GetHMIStatus().State;
    if (PR010State == ELBPR010State::Isolated
        && !PR010->ExecuteRemoteCommand(ELBPR010Command::PowerOn, LineSource, Authority))
        return FailAndStop(TEXT("PR-010 POWER-ON INTERLOCK REJECTED COMMAND"));
    if (PR010->GetHMIStatus().State == ELBPR010State::Ready
        && !PR010->ExecuteRemoteCommand(ELBPR010Command::Start, LineSource, Authority))
        return FailAndStop(TEXT("PR-010 START INTERLOCK REJECTED COMMAND"));

    // PR-009 cannot start until a traceable PR-008 blank is accepted. Likewise,
    // the selected train remains powered down until PR-010 releases reserved
    // blanks. Tick-driven orchestration advances those authorities later.
    if (Train->GetPendingBlankCount() > 0)
    {
        const FName TrainSource(*FString::Printf(TEXT("MW.MCR.%s.CONSOLE"), *State.AssignedTrain.ToString()));
        if (!Train->ExecuteRemoteCommand(ELBPressTrainACommand::PowerOn, TrainSource, Authority)
            || !Train->ExecuteRemoteCommand(ELBPressTrainACommand::Start, TrainSource, Authority))
        {
            const FLBPressTrainAHMIStatus Status = Train->GetHMIStatus();
            return FailAndStop(Status.BlockingReasons.IsEmpty()
                ? TEXT("SELECTED TRAIN START INTERLOCK REJECTED COMMAND")
                : Status.BlockingReasons[0].ToString().ToUpper());
        }
    }
    State.OrderState = ELBControlRoomOrderState::Running;
    State.LastAlarm = State.OperatingMode == ELBControlRoomOperatingMode::Automatic
        ? TEXT("AUTOMATIC LINE SEQUENCE ACCEPTED / MATERIAL FLOW ACTIVE")
        : TEXT("ASSISTED MANUAL SAFE CYCLE ACCEPTED");
    RefreshPresentation();
    return true;
}

bool ALBControlRoomOperationsConsole::PauseOrder()
{
    ALBPR005Station* Station = BoundPR005.Get();
    if (!Station || State.OrderState != ELBControlRoomOrderState::Running)
    {
        SetHold(TEXT("NO RUNNING ORDER TO PAUSE"));
        return false;
    }
    RequestWholeLineControlledStop();
    State.OrderState = ELBControlRoomOrderState::Paused;
    State.LastAlarm = TEXT("CONTROLLED PAUSE REQUESTED");
    RefreshPresentation();
    return true;
}

bool ALBControlRoomOperationsConsole::StopOrder()
{
    RequestWholeLineControlledStop();
    if (State.OrderState == ELBControlRoomOrderState::Draft) return false;
    State.OrderState = ELBControlRoomOrderState::Ready;
    State.LastAlarm = TEXT("CONTROLLED STOP REQUESTED / ORDER RETAINED");
    RefreshPresentation();
    return true;
}

void ALBControlRoomOperationsConsole::RequestWholeLineControlledStop()
{
    if (ALBPR005Station* Station = BoundPR005.Get()) Station->RequestControlledStop();
    if (ALBPR006Station* Station = BoundPR006.Get()) Station->RequestControlledStop();
    if (ALBPR007Station* Station = BoundPR007.Get()) Station->RequestControlledStop();
    if (ALBPR008Station* Station = BoundPR008.Get()) Station->RequestControlledStop();
    const FName Source(TEXT("MW.MCR.LINE.CONSOLE"));
    const FName Authority(TEXT("CW.MW.CONTROL_ROOM"));
    if (ALBPR009Station* Station = BoundPR009.Get())
        Station->ExecuteRemoteCommand(ELBPR009Command::ControlledStop, Source, Authority);
    if (ALBPR010Station* Station = BoundPR010.Get())
        Station->ExecuteRemoteCommand(ELBPR010Command::ControlledStop, Source, Authority);
    if (ALBPressTrainAStation* Train = GetAssignedPressTrain()) Train->RequestControlledStop();
}

bool ALBControlRoomOperationsConsole::RecordAuthoritativePanelResult(
    bool bAccepted, float RemainingMaterialInMetres, const FString& NewBufferStatus)
{
    if (State.OrderState != ELBControlRoomOrderState::Running || RemainingMaterialInMetres < 0.0f
        || NewBufferStatus.IsEmpty()) return false;
    if (bAccepted) ++State.GoodPanels; else ++State.RejectedPanels;
    State.RemainingMaterialMetres = RemainingMaterialInMetres;
    State.BufferStatus = NewBufferStatus;
    if (State.GoodPanels >= State.RequestedQuantity)
    {
        State.OrderState = ELBControlRoomOrderState::Completed;
        State.LastAlarm = TEXT("REQUESTED GOOD-PANEL QUANTITY COMPLETE");
        if (ALBPR005Station* Station = BoundPR005.Get()) Station->RequestControlledStop();
    }
    RefreshPresentation();
    return true;
}

bool ALBControlRoomOperationsConsole::ResolveRecipeAuthority(
    FName AuthoritativeRecipeId, float RequiredStripWidthMillimetres)
{
    if (AuthoritativeRecipeId.IsNone() || RequiredStripWidthMillimetres <= 0.0f) return false;
    State.RecipeId = AuthoritativeRecipeId;
    ResolvedRequiredStripWidthMillimetres = RequiredStripWidthMillimetres;
    State.LastAlarm = TEXT("AUTHORITATIVE RECIPE LINKED");
    RefreshPresentation();
    return true;
}

bool ALBControlRoomOperationsConsole::RestoreSaveState(const FLBControlRoomOperationsSaveState& SavedState)
{
    if ((SavedState.Version != 1 && SavedState.Version != 2) || !PanelFamilies.Contains(SavedState.PanelFamily)
        || !TrainIds.Contains(SavedState.AssignedTrain) || SavedState.RequestedQuantity < 0
        || SavedState.GoodPanels < 0 || SavedState.RejectedPanels < 0) return false;
    State = SavedState;
    State.NextOrchestrationTransactionSerial = FMath::Max(1, State.NextOrchestrationTransactionSerial);
    State.NextReleasedBlankIndex = FMath::Max(0, State.NextReleasedBlankIndex);
    if (State.OrderState == ELBControlRoomOrderState::Running)
    {
        State.OrderState = ELBControlRoomOrderState::Paused;
        State.LastAlarm = TEXT("LOADED SAFELY PAUSED / PLAYER RESTART REQUIRED");
    }
    // Width is intentionally not duplicated in this planning record. It must
    // be re-established by the authoritative recipe catalogue after load.
    ResolvedRequiredStripWidthMillimetres = 0.0f;
    BindExistingAuthority();
    RefreshPresentation();
    return true;
}

void ALBControlRoomOperationsConsole::SetHold(const FString& Reason)
{
    if (State.OrderState != ELBControlRoomOrderState::Draft)
        State.OrderState = ELBControlRoomOrderState::Held;
    State.LastAlarm = Reason;
    RefreshPresentation();
}

void ALBControlRoomOperationsConsole::RefreshPresentation()
{
    if (!OrderText || !ProductionText || !AuthorityText || !AlarmText) return;
    OrderText->SetText(FText::FromString(FString::Printf(
        TEXT("ORDER %s   |   PANEL %s   |   %s\nQTY %06d   |   PRIORITY %s   |   MODE %s"),
        *EnumDisplay(State.OrderState), *DisplayName(State.PanelFamily), *DisplayName(State.AssignedTrain),
        State.RequestedQuantity, *EnumDisplay(State.Priority), *EnumDisplay(State.OperatingMode))));
    ProductionText->SetText(FText::FromString(FString::Printf(
        TEXT("GOOD %06d   |   REJECT %05d   |   REMAINING %06d\nMATERIAL %s   |   BUFFER %s"),
        State.GoodPanels, State.RejectedPanels,
        FMath::Max(0, State.RequestedQuantity - State.GoodPanels),
        State.RemainingMaterialMetres < 0.0f ? TEXT("AUTHORITY HOLD")
            : *FString::Printf(TEXT("%.1f m"), State.RemainingMaterialMetres),
        *State.BufferStatus.ToUpper())));
    const FString Recipe = State.RecipeId.IsNone() ? TEXT("AUTHORITY CATALOG HOLD") : State.RecipeId.ToString();
    const FString Coil = State.SelectedCoilId.IsEmpty() ? TEXT("NO AUTHORITATIVE SELECTION") : State.SelectedCoilId;
    const FString PR006 = BoundPR006.IsValid() ? EnumDisplay(BoundPR006->GetHMIStatus().State) : TEXT("OFFLINE");
    const FString PR007 = BoundPR007.IsValid() ? EnumDisplay(BoundPR007->GetHMIStatus().State) : TEXT("OFFLINE");
    const FString PR008 = BoundPR008.IsValid() ? EnumDisplay(BoundPR008->GetHMIStatus().State) : TEXT("OFFLINE");
    const FString PR009 = BoundPR009.IsValid() ? EnumDisplay(BoundPR009->GetHMIStatus().State) : TEXT("OFFLINE");
    const FString PR010 = BoundPR010.IsValid() ? EnumDisplay(BoundPR010->GetHMIStatus().State) : TEXT("OFFLINE");
    const FString Train = GetAssignedPressTrain()
        ? EnumDisplay(GetAssignedPressTrain()->GetHMIStatus().State) : TEXT("OFFLINE");
    FString FleetStatus = TEXT("FLEET OFFLINE");
    if (ALBPressShopSupportFleetController* Fleet = BoundSupportFleet.Get())
    {
        FLBSupportRobotSaveState Robot;
        if (Fleet->GetUnitSnapshot(SelectedSupportUnitId, Robot))
        {
            FleetStatus = FString::Printf(TEXT("ROBOT %s / %s / %s / %.0f%%"),
                *SelectedSupportUnitId.ToString(), *EnumDisplay(Robot.State),
                Robot.bDocked ? TEXT("DOCKED") : TEXT("FIELD"), Robot.BatteryStateOfChargePercent);
        }
        else
        {
            FleetStatus = Fleet->IsFleetReady() ? TEXT("FLEET READY / UNIT LINK HOLD") : TEXT("FLEET NOT READY");
        }
    }
    AuthorityText->SetText(FText::FromString(FString::Printf(
        TEXT("RECIPE %s   |   COIL %s   |   PR-005 %s\nPR-006 %s   PR-007 %s   PR-008 %s\nPR-009 %s   PR-010 %s   %s %s\n%s"),
        *Recipe, *Coil, BoundPR005.IsValid() ? TEXT("ONLINE") : TEXT("OFFLINE"),
        *PR006, *PR007, *PR008, *PR009, *PR010, *DisplayName(State.AssignedTrain), *Train, *FleetStatus)));
    AlarmText->SetText(FText::FromString(FString::Printf(TEXT("ALARM / GUIDANCE:  %s"), *State.LastAlarm.ToUpper())));
    AlarmText->SetTextRenderColor(State.OrderState == ELBControlRoomOrderState::Held
        ? FColor(224, 77, 48) : FColor(227, 166, 0));
}
