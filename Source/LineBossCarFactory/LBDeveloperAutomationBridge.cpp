#include "LBDeveloperAutomationBridge.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformProcess.h"
#include "LBBodyWeldLineActor.h"
#include "LBControlRoomHUD.h"
#include "LBCoilAGVController.h"
#include "LBInboundDeliveryController.h"
#include "LBECoatLineActor.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryMachineBuilderSubsystem.h"
#include "LBFactoryUIStateSubsystem.h"
#include "LBManagementPawn.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressShopStorageZone.h"
#include "LBPressShopSupportFleetController.h"
#include "LBPressTrainAStation.h"
#include "Misc/CommandLine.h"
#include "Misc/DateTime.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Misc/SecureHash.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "UnrealClient.h"

namespace
{
    constexpr int32 BridgeProtocolVersion = 1;
    constexpr int32 MaximumCommandBytes = 64 * 1024;
    constexpr int32 MaximumCommandsPerPump = 8;
    const TCHAR* BridgeProtocol = TEXT("lineboss.automation");

    FString SerializeCondensed(const TSharedRef<FJsonObject>& Object)
    {
        FString Text;
        const TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
            TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Text);
        FJsonSerializer::Serialize(Object, Writer);
        Writer->Close();
        return Text;
    }

    void SetVectorFields(const TSharedRef<FJsonObject>& Object, const FVector& Value)
    {
        Object->SetNumberField(TEXT("x"), Value.X);
        Object->SetNumberField(TEXT("y"), Value.Y);
        Object->SetNumberField(TEXT("z"), Value.Z);
    }

    FString MachineTypeName(const ELBFactoryBuildMachineType Type)
    {
        return ALBDeveloperAutomationBridge::SerializeMachineType(Type);
    }

    FString MachineStateName(const ELBFactoryMachineOperatingState State)
    {
        switch (State)
        {
        case ELBFactoryMachineOperatingState::Idle: return TEXT("idle");
        case ELBFactoryMachineOperatingState::Starved: return TEXT("starved");
        case ELBFactoryMachineOperatingState::Ready: return TEXT("ready");
        case ELBFactoryMachineOperatingState::Blocked: return TEXT("blocked");
        case ELBFactoryMachineOperatingState::Processing: return TEXT("processing");
        case ELBFactoryMachineOperatingState::Fault: return TEXT("fault");
        default: return TEXT("unknown");
        }
    }

    FString BodyWeldPhaseName(const ELBBodyWeldPhase Phase)
    {
        switch (Phase)
        {
        case ELBBodyWeldPhase::AwaitingRecipe: return TEXT("awaiting_recipe");
        case ELBBodyWeldPhase::ReservingInputs: return TEXT("reserving_inputs");
        case ELBBodyWeldPhase::ClosurePreparation: return TEXT("closure_preparation");
        case ELBBodyWeldPhase::Framing: return TEXT("framing");
        case ELBBodyWeldPhase::Welding: return TEXT("welding");
        case ELBBodyWeldPhase::GeometryCheck: return TEXT("geometry_check");
        case ELBBodyWeldPhase::OutputReady: return TEXT("output_ready");
        case ELBBodyWeldPhase::TransferringToED: return TEXT("transferring_to_ed");
        default: return TEXT("unknown");
        }
    }

    FString StorageTypeName(const ELBPressShopStorageType Type)
    {
        switch (Type)
        {
        case ELBPressShopStorageType::BareCoils: return TEXT("bare_coils");
        case ELBPressShopStorageType::PreparedBlanks: return TEXT("prepared_blanks");
        case ELBPressShopStorageType::FinishedPanelStillages: return TEXT("finished_panel_stillages");
        case ELBPressShopStorageType::Scrap: return TEXT("scrap");
        case ELBPressShopStorageType::MaintenanceParts: return TEXT("maintenance_parts");
        case ELBPressShopStorageType::Quarantine: return TEXT("quarantine");
        case ELBPressShopStorageType::EmptyPanelStillages: return TEXT("empty_panel_stillages");
        default: return TEXT("unknown");
        }
    }

    FString CoilPhaseName(const ELBCoilAGVPhase Phase)
    {
        switch (Phase)
        {
        case ELBCoilAGVPhase::IdleLoaded: return TEXT("idle_loaded");
        case ELBCoilAGVPhase::TravelToTurn: return TEXT("travel_to_turn");
        case ELBCoilAGVPhase::RotateForDock: return TEXT("corner_to_dock");
        case ELBCoilAGVPhase::TravelToDock: return TEXT("travel_to_dock");
        case ELBCoilAGVPhase::DockProving: return TEXT("dock_proving");
        case ELBCoilAGVPhase::RaiseTransferDeck: return TEXT("raise_transfer_deck");
        case ELBCoilAGVPhase::HandoffReady: return TEXT("handoff_ready");
        case ELBCoilAGVPhase::LowerAfterHandoff: return TEXT("lower_after_handoff");
        case ELBCoilAGVPhase::ReturnToTurn: return TEXT("return_to_turn");
        case ELBCoilAGVPhase::RotateToStaged: return TEXT("corner_to_staged");
        case ELBCoilAGVPhase::ReturnToStaged: return TEXT("return_to_staged");
        case ELBCoilAGVPhase::AwaitingReload: return TEXT("awaiting_reload");
        case ELBCoilAGVPhase::Fault: return TEXT("fault");
        default: return TEXT("unknown");
        }
    }

    FString CoilFaultName(const ELBCoilAGVFault Fault)
    {
        switch (Fault)
        {
        case ELBCoilAGVFault::None: return TEXT("none");
        case ELBCoilAGVFault::BindingIncomplete: return TEXT("binding_incomplete");
        case ELBCoilAGVFault::ControlPowerLost: return TEXT("control_power_lost");
        case ELBCoilAGVFault::RouteAuthorityLost: return TEXT("route_authority_lost");
        case ELBCoilAGVFault::PedestrianGateOpen: return TEXT("pedestrian_gate_open");
        case ELBCoilAGVFault::ScannerObstructed: return TEXT("scanner_obstructed");
        case ELBCoilAGVFault::LoadUnsecured: return TEXT("load_unsecured");
        case ELBCoilAGVFault::DestinationNotReady: return TEXT("destination_not_ready");
        case ELBCoilAGVFault::CraneEnvelopeConflict: return TEXT("crane_envelope_conflict");
        case ELBCoilAGVFault::EmergencyCircuitOpen: return TEXT("emergency_circuit_open");
        case ELBCoilAGVFault::RouteObstructed: return TEXT("route_obstructed");
        case ELBCoilAGVFault::DockTimeout: return TEXT("dock_timeout");
        default: return TEXT("unknown");
        }
    }

    FString ManagementPageName(const ELBManagementPage Page)
    {
        switch (Page)
        {
        case ELBManagementPage::Overview: return TEXT("overview");
        case ELBManagementPage::FactoryBuild: return TEXT("factory_build");
        case ELBManagementPage::Production: return TEXT("production");
        case ELBManagementPage::PressTrains: return TEXT("press_trains");
        case ELBManagementPage::SupportFleet: return TEXT("support_fleet");
        case ELBManagementPage::Research: return TEXT("research");
        case ELBManagementPage::Analytics: return TEXT("analytics");
        default: return TEXT("unknown");
        }
    }

    FString AlertSeverityName(const ELBFactoryUIAlertSeverity Severity)
    {
        switch (Severity)
        {
        case ELBFactoryUIAlertSeverity::Critical: return TEXT("critical");
        case ELBFactoryUIAlertSeverity::Warning: return TEXT("warning");
        default: return TEXT("information");
        }
    }

    ALBControlRoomHUD* FindManagementHUD(UWorld* World)
    {
        if (!World) return nullptr;
        for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
        {
            if (APlayerController* Controller = It->Get())
                if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(Controller->GetHUD())) return HUD;
        }
        for (TActorIterator<ALBControlRoomHUD> It(World); It; ++It)
            if (IsValid(*It)) return *It;
        return nullptr;
    }

    ALBManagementPawn* FindManagementPawn(UWorld* World)
    {
        if (!World) return nullptr;
        for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
        {
            if (APlayerController* Controller = It->Get())
                if (ALBManagementPawn* Pawn = Cast<ALBManagementPawn>(Controller->GetPawn())) return Pawn;
        }
        for (TActorIterator<ALBManagementPawn> It(World); It; ++It)
            if (IsValid(*It)) return *It;
        return nullptr;
    }

    template <typename T>
    T* FindFirstActor(UWorld* World)
    {
        if (!World) return nullptr;
        for (TActorIterator<T> It(World); It; ++It)
            if (IsValid(*It)) return *It;
        return nullptr;
    }

    bool ReadStringArgument(const TSharedPtr<FJsonObject>& Args, const TCHAR* Field,
        FString& OutValue, const bool bRequired, const FString& DefaultValue,
        FString& OutError)
    {
        if (!Args->HasField(Field))
        {
            OutValue = DefaultValue;
            if (!bRequired) return true;
            OutError = FString::Printf(TEXT("MISSING STRING ARGUMENT: %s"), Field);
            return false;
        }
        if (!Args->HasTypedField<EJson::String>(Field))
        {
            OutError = FString::Printf(TEXT("ARGUMENT %s MUST BE A STRING"), Field);
            return false;
        }
        OutValue = Args->GetStringField(Field);
        if (bRequired && OutValue.IsEmpty())
        {
            OutError = FString::Printf(TEXT("ARGUMENT %s CANNOT BE EMPTY"), Field);
            return false;
        }
        return true;
    }

    bool ReadNumberArgument(const TSharedPtr<FJsonObject>& Args, const TCHAR* Field,
        double& OutValue, const bool bRequired, const double DefaultValue,
        FString& OutError)
    {
        if (!Args->HasField(Field))
        {
            OutValue = DefaultValue;
            if (!bRequired) return true;
            OutError = FString::Printf(TEXT("MISSING NUMBER ARGUMENT: %s"), Field);
            return false;
        }
        if (!Args->HasTypedField<EJson::Number>(Field))
        {
            OutError = FString::Printf(TEXT("ARGUMENT %s MUST BE A NUMBER"), Field);
            return false;
        }
        OutValue = Args->GetNumberField(Field);
        if (!FMath::IsFinite(OutValue))
        {
            OutError = FString::Printf(TEXT("ARGUMENT %s MUST BE FINITE"), Field);
            return false;
        }
        return true;
    }

    bool ReadBoolArgument(const TSharedPtr<FJsonObject>& Args, const TCHAR* Field,
        bool& OutValue, const bool DefaultValue, FString& OutError)
    {
        if (!Args->HasField(Field))
        {
            OutValue = DefaultValue;
            return true;
        }
        if (!Args->HasTypedField<EJson::Boolean>(Field))
        {
            OutError = FString::Printf(TEXT("ARGUMENT %s MUST BE A BOOLEAN"), Field);
            return false;
        }
        OutValue = Args->GetBoolField(Field);
        return true;
    }
}

ALBDeveloperAutomationBridge::ALBDeveloperAutomationBridge()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = false;
    PrimaryActorTick.TickInterval = 0.10f;
}

bool ALBDeveloperAutomationBridge::IsEnabledFromCommandLine(const TCHAR* CommandLine)
{
    return CommandLine && FParse::Param(CommandLine, TEXT("LineBossAutomationBridge"));
}

FString ALBDeveloperAutomationBridge::SerializeMachineType(
    const ELBFactoryBuildMachineType Type)
{
    switch (Type)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock: return TEXT("inbound_delivery_dock");
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell: return TEXT("coil_weigh_inspection_cell");
    case ELBFactoryBuildMachineType::DepackagingRobot: return TEXT("depackaging_robot");
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("decoiler_feeder");
    case ELBFactoryBuildMachineType::PressTrain: return TEXT("press_train");
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("inspection_cell");
    case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("outbound_panel_dock");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("ecoat_line");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("body_weld_line");
    default: return TEXT("unknown");
    }
}

bool ALBDeveloperAutomationBridge::TryParseMachineType(
    FString Name, ELBFactoryBuildMachineType& OutType)
{
    Name = NormalizeKey(MoveTemp(Name));
    if (Name == TEXT("inbound_delivery") || Name == TEXT("inbound_delivery_dock"))
        OutType = ELBFactoryBuildMachineType::InboundDeliveryDock;
    else if (Name == TEXT("coil_weigh_inspection") || Name == TEXT("coil_weigh_inspection_cell"))
        OutType = ELBFactoryBuildMachineType::CoilWeighInspectionCell;
    else if (Name == TEXT("depackaging_robot"))
        OutType = ELBFactoryBuildMachineType::DepackagingRobot;
    else if (Name == TEXT("decoiler_feeder"))
        OutType = ELBFactoryBuildMachineType::DecoilerFeeder;
    else if (Name == TEXT("press_train"))
        OutType = ELBFactoryBuildMachineType::PressTrain;
    else if (Name == TEXT("inspection_cell"))
        OutType = ELBFactoryBuildMachineType::InspectionCell;
    else if (Name == TEXT("outbound_panel_dock") || Name == TEXT("weld_shop_intake")
        || Name == TEXT("weld_shop_stillage_intake"))
        OutType = ELBFactoryBuildMachineType::OutboundPanelDock;
    else if (Name == TEXT("ecoat_line") || Name == TEXT("e_coat_line")
        || Name == TEXT("ed_line"))
        OutType = ELBFactoryBuildMachineType::ECoatLine;
    else if (Name == TEXT("body_weld_line") || Name == TEXT("weld_line"))
        OutType = ELBFactoryBuildMachineType::BodyWeldLine;
    else
        return false;
    return true;
}

void ALBDeveloperAutomationBridge::BeginPlay()
{
    Super::BeginPlay();
#if !UE_BUILD_SHIPPING
    if (IsEnabledFromCommandLine(FCommandLine::Get())) StartBridge();
#endif
}

void ALBDeveloperAutomationBridge::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bBridgeEnabled) return;
    ProcessReadyCommands();
    HeartbeatAccumulator += FMath::Max(0.0f, DeltaSeconds);
    if (HeartbeatAccumulator >= 1.0f)
    {
        HeartbeatAccumulator = 0.0f;
        WriteStateSnapshot();
    }
}

void ALBDeveloperAutomationBridge::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    StopBridge();
    Super::EndPlay(EndPlayReason);
}

#if WITH_DEV_AUTOMATION_TESTS
bool ALBDeveloperAutomationBridge::StartForTesting(const FString& SafeLeafName)
{
    return StartBridge(SafeLeafName);
}

int32 ALBDeveloperAutomationBridge::PumpForTesting()
{
    return ProcessReadyCommands();
}
#endif

bool ALBDeveloperAutomationBridge::StartBridge(const FString& TestLeafName)
{
#if UE_BUILD_SHIPPING
    return false;
#else
    if (bBridgeEnabled) return true;
    if (!TestLeafName.IsEmpty() && !IsSafeToken(TestLeafName, 96)) return false;

    RootDirectory = FPaths::ConvertRelativePathToFull(TestLeafName.IsEmpty()
        ? FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("AutomationBridge"))
        : FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("AutomationBridgeTests"), TestLeafName));
    FPaths::NormalizeDirectoryName(RootDirectory);
    const FString CompactUtc = FDateTime::UtcNow().ToString(TEXT("%Y%m%dT%H%M%SZ"));
    SessionId = FString::Printf(TEXT("%s-%u-%s"), *CompactUtc,
        FPlatformProcess::GetCurrentProcessId(),
        *FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(8));
    SessionDirectory = FPaths::Combine(RootDirectory, TEXT("sessions"), SessionId);
    InboxDirectory = FPaths::Combine(SessionDirectory, TEXT("inbox"));
    ProcessingDirectory = FPaths::Combine(SessionDirectory, TEXT("processing"));
    OutboxDirectory = FPaths::Combine(SessionDirectory, TEXT("outbox"));
    ArchiveDirectory = FPaths::Combine(SessionDirectory, TEXT("archive"));
    ScreenshotDirectory = FPaths::Combine(SessionDirectory, TEXT("screenshots"));

    IFileManager& Files = IFileManager::Get();
    for (const FString* Directory : {&RootDirectory, &SessionDirectory, &InboxDirectory,
        &ProcessingDirectory, &OutboxDirectory, &ArchiveDirectory, &ScreenshotDirectory})
    {
        if (!Files.MakeDirectory(**Directory, true)) return false;
    }

    ExpectedSequence = 1;
    StateRevision = 0;
    HeartbeatAccumulator = 0.0f;
    ProcessedCommands.Reset();
    bBridgeEnabled = true;
    SetActorTickEnabled(true);
    WriteSessionDescriptor();
    WriteStateSnapshot();
    UE_LOG(LogTemp, Display,
        TEXT("LINE_BOSS_AUTOMATION_BRIDGE_READY session=%s inbox=%s outbox=%s"),
        *SessionId, *InboxDirectory, *OutboxDirectory);
    return true;
#endif
}

void ALBDeveloperAutomationBridge::StopBridge()
{
    if (!bBridgeEnabled) return;
    bBridgeEnabled = false;
    SetActorTickEnabled(false);
    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_AUTOMATION_BRIDGE_STOPPED session=%s"), *SessionId);
}

FString ALBDeveloperAutomationBridge::UtcNowString()
{
    return FDateTime::UtcNow().ToIso8601();
}

bool ALBDeveloperAutomationBridge::IsSafeToken(const FString& Value, const int32 MaximumLength)
{
    if (Value.IsEmpty() || Value.Len() > MaximumLength) return false;
    for (const TCHAR Character : Value)
    {
        if (!FChar::IsAlnum(Character) && Character != TEXT('_') && Character != TEXT('-')) return false;
    }
    return true;
}

FString ALBDeveloperAutomationBridge::NormalizeKey(FString Value)
{
    Value.TrimStartAndEndInline();
    Value.ToLowerInline();
    Value.ReplaceInline(TEXT("-"), TEXT("_"));
    Value.ReplaceInline(TEXT(" "), TEXT("_"));
    return Value;
}

bool ALBDeveloperAutomationBridge::ParseReadyFilename(const FString& Filename,
    int64& OutSequence, FString& OutCommandId)
{
    if (!Filename.EndsWith(TEXT(".ready"), ESearchCase::IgnoreCase)) return false;
    const FString Base = Filename.LeftChop(6);
    int32 Separator = INDEX_NONE;
    if (!Base.FindChar(TEXT('_'), Separator) || Separator <= 0) return false;
    const FString SequenceText = Base.Left(Separator);
    for (const TCHAR Character : SequenceText) if (!FChar::IsDigit(Character)) return false;
    OutSequence = FCString::Atoi64(*SequenceText);
    OutCommandId = Base.Mid(Separator + 1);
    return OutSequence > 0 && IsSafeToken(OutCommandId);
}

bool ALBDeveloperAutomationBridge::IsPathInsideRoot(const FString& Path) const
{
    FString Root = FPaths::ConvertRelativePathToFull(RootDirectory);
    FString Candidate = FPaths::ConvertRelativePathToFull(Path);
    FPaths::NormalizeFilename(Root);
    FPaths::NormalizeFilename(Candidate);
    Root.RemoveFromEnd(TEXT("/"));
    return Candidate.Equals(Root, ESearchCase::IgnoreCase)
        || Candidate.StartsWith(Root + TEXT("/"), ESearchCase::IgnoreCase);
}

bool ALBDeveloperAutomationBridge::WriteTextAtomic(const FString& FinalPath,
    const FString& Text) const
{
    if (!bBridgeEnabled || !IsPathInsideRoot(FinalPath)) return false;
    const FString TemporaryPath = FinalPath + TEXT(".tmp");
    if (!IsPathInsideRoot(TemporaryPath)
        || !FFileHelper::SaveStringToFile(Text, *TemporaryPath,
            FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)) return false;
    return IFileManager::Get().Move(*FinalPath, *TemporaryPath, true, true, false, true);
}

bool ALBDeveloperAutomationBridge::WriteJsonAtomic(const FString& FinalPath,
    const TSharedRef<FJsonObject>& Object) const
{
    return WriteTextAtomic(FinalPath, SerializeCondensed(Object));
}

TSharedPtr<FJsonObject> ALBDeveloperAutomationBridge::CaptureState() const
{
    const TSharedRef<FJsonObject> State = MakeShared<FJsonObject>();
    State->SetStringField(TEXT("protocol"), BridgeProtocol);
    State->SetNumberField(TEXT("version"), BridgeProtocolVersion);
    State->SetStringField(TEXT("kind"), TEXT("state"));
    State->SetStringField(TEXT("session_id"), SessionId);
    State->SetNumberField(TEXT("state_revision"), StateRevision);
    State->SetNumberField(TEXT("next_sequence"), ExpectedSequence);
    State->SetStringField(TEXT("captured_at_utc"), UtcNowString());

    UWorld* World = GetWorld();
    State->SetStringField(TEXT("map"), World ? World->GetMapName() : TEXT("none"));
    State->SetNumberField(TEXT("world_time_seconds"), World ? World->GetTimeSeconds() : 0.0f);

    TArray<TSharedPtr<FJsonValue>> Machines;
    if (World)
    {
        for (TActorIterator<ALBFactoryBuildMachine> It(World); It; ++It)
        {
            const ALBFactoryBuildMachine* Machine = *It;
            if (!IsValid(Machine) || !Machine->ActorHasTag(TEXT("LB.FactoryBuilder.Machine"))) continue;
            const TSharedRef<FJsonObject> Item = MakeShared<FJsonObject>();
            Item->SetStringField(TEXT("id"), Machine->GetMachineId().ToString());
            Item->SetStringField(TEXT("type"), MachineTypeName(Machine->GetMachineType()));
            Item->SetStringField(TEXT("state"), MachineStateName(Machine->GetOperatingState()));
            Item->SetStringField(TEXT("reason"), Machine->GetOperatingReason());
            Item->SetNumberField(TEXT("input_count"), Machine->GetInputUnitCount());
            Item->SetNumberField(TEXT("output_count"), Machine->GetOutputUnitCount());
            Item->SetNumberField(TEXT("completed_count"), Machine->GetCompletedUnitCount());
            const TSharedRef<FJsonObject> Location = MakeShared<FJsonObject>();
            SetVectorFields(Location, Machine->GetActorLocation());
            Item->SetObjectField(TEXT("location"), Location);
            Machines.Add(MakeShared<FJsonValueObject>(Item));
        }
    }
    State->SetArrayField(TEXT("machines"), Machines);
    State->SetNumberField(TEXT("machine_count"), Machines.Num());

    // Composite Body Weld lines retain a dedicated, backward-compatible array. They are
    // not flattened into generic machine buffers because exact BIW lineage, output and
    // rework slots have different semantics.
    TArray<ALBBodyWeldLineActor*> WeldActors;
    if (World)
    {
        for (TActorIterator<ALBBodyWeldLineActor> It(World); It; ++It)
        {
            ALBBodyWeldLineActor* Line = *It;
            if (IsValid(Line) && !Line->GetLineId().IsNone()) WeldActors.Add(Line);
        }
    }
    WeldActors.Sort([](const ALBBodyWeldLineActor& A, const ALBBodyWeldLineActor& B)
    {
        return A.GetLineId().LexicalLess(B.GetLineId());
    });
    TArray<TSharedPtr<FJsonValue>> BodyWeldLines;
    for (const ALBBodyWeldLineActor* Line : WeldActors)
    {
        FLBBodyInWhiteRecord OutputBody;
        FLBBodyInWhiteRecord ReworkBody;
        const bool bHasOutput = Line->GetOutputBody(OutputBody);
        const bool bHasRework = Line->GetReworkBody(ReworkBody);
        const TSharedRef<FJsonObject> Item = MakeShared<FJsonObject>();
        Item->SetStringField(TEXT("line_id"), Line->GetLineId().ToString());
        Item->SetStringField(TEXT("state"), MachineStateName(Line->GetOperatingState()));
        Item->SetStringField(TEXT("phase"), BodyWeldPhaseName(Line->GetPhase()));
        Item->SetNumberField(TEXT("progress"), Line->GetPhaseProgress01());
        Item->SetNumberField(TEXT("progress01"), Line->GetPhaseProgress01());
        Item->SetStringField(TEXT("reason"), Line->GetOperatingReason());
        Item->SetStringField(TEXT("order_id"), Line->GetAssignedOrderId().ToString());
        Item->SetNumberField(TEXT("available_panel_count"), Line->GetAvailablePanelCount());
        Item->SetNumberField(TEXT("reserved_panel_count"), Line->GetReservedPanelCount());
        Item->SetNumberField(TEXT("available_base_kit_count"), Line->GetAvailableBaseKitCount());
        Item->SetNumberField(TEXT("pending_empty_return_count"), Line->GetPendingEmptyReturnCount());
        Item->SetBoolField(TEXT("ed_available"), Line->IsEDAvailable());
        Item->SetBoolField(TEXT("has_output_body"), bHasOutput);
        Item->SetStringField(TEXT("output_body_id"),
            bHasOutput ? OutputBody.BodyId.ToString() : FString());
        Item->SetBoolField(TEXT("has_rework_body"), bHasRework);
        Item->SetStringField(TEXT("rework_body_id"),
            bHasRework ? ReworkBody.BodyId.ToString() : FString());
        Item->SetNumberField(TEXT("completed"), Line->GetCompletedBodyCount());
        Item->SetNumberField(TEXT("completed_body_count"), Line->GetCompletedBodyCount());

        const TSharedRef<FJsonObject> Inventory = MakeShared<FJsonObject>();
        Inventory->SetNumberField(TEXT("available_panel_count"), Line->GetAvailablePanelCount());
        Inventory->SetNumberField(TEXT("reserved_panel_count"), Line->GetReservedPanelCount());
        Inventory->SetNumberField(TEXT("available_base_kit_count"), Line->GetAvailableBaseKitCount());
        Inventory->SetNumberField(TEXT("pending_empty_return_count"), Line->GetPendingEmptyReturnCount());
        Item->SetObjectField(TEXT("inventory"), Inventory);

        const TSharedRef<FJsonObject> Output = MakeShared<FJsonObject>();
        Output->SetBoolField(TEXT("present"), bHasOutput);
        Output->SetStringField(TEXT("body_id"),
            bHasOutput ? OutputBody.BodyId.ToString() : FString());
        Item->SetObjectField(TEXT("output"), Output);
        const TSharedRef<FJsonObject> Rework = MakeShared<FJsonObject>();
        Rework->SetBoolField(TEXT("present"), bHasRework);
        Rework->SetStringField(TEXT("body_id"),
            bHasRework ? ReworkBody.BodyId.ToString() : FString());
        Item->SetObjectField(TEXT("rework"), Rework);

        const TSharedRef<FJsonObject> Location = MakeShared<FJsonObject>();
        SetVectorFields(Location, Line->GetActorLocation());
        Item->SetObjectField(TEXT("location"), Location);
        BodyWeldLines.Add(MakeShared<FJsonValueObject>(Item));
    }
    State->SetArrayField(TEXT("body_weld_lines"), BodyWeldLines);
    State->SetNumberField(TEXT("body_weld_line_count"), BodyWeldLines.Num());

    int32 PressTrainCount = 0;
    if (World)
        for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
            if (IsValid(*It)) ++PressTrainCount;
    State->SetNumberField(TEXT("press_train_count"), PressTrainCount);

    TArray<TSharedPtr<FJsonValue>> StorageZones;
    if (World)
    {
        for (TActorIterator<ALBPressShopStorageZone> It(World); It; ++It)
        {
            const ALBPressShopStorageZone* Zone = *It;
            if (!IsValid(Zone) || !Zone->ActorHasTag(TEXT("LB.FactoryBuilder.StorageZone"))) continue;
            const TSharedRef<FJsonObject> Item = MakeShared<FJsonObject>();
            Item->SetStringField(TEXT("id"), Zone->GetZoneId().ToString());
            Item->SetStringField(TEXT("type"), StorageTypeName(Zone->GetStorageType()));
            Item->SetNumberField(TEXT("capacity"), Zone->GetCapacity());
            Item->SetNumberField(TEXT("stored_count"), Zone->GetIdentifiedUnitCount());
            const TSharedRef<FJsonObject> Location = MakeShared<FJsonObject>();
            SetVectorFields(Location, Zone->GetActorLocation());
            Item->SetObjectField(TEXT("location"), Location);
            StorageZones.Add(MakeShared<FJsonValueObject>(Item));
        }
    }
    State->SetArrayField(TEXT("storage_zones"), StorageZones);
    State->SetNumberField(TEXT("storage_zone_count"), StorageZones.Num());
    State->SetNumberField(TEXT("factory_actor_count"),
        Machines.Num() + BodyWeldLines.Num() + PressTrainCount + StorageZones.Num());

    const TSharedRef<FJsonObject> Production = MakeShared<FJsonObject>();
    if (ALBPlayerBuiltPressFlowController* Flow = FindFirstActor<ALBPlayerBuiltPressFlowController>(World))
    {
        const TArray<FLBVehiclePanelBatch> Batches = Flow->GetPanelBatches();
        int32 RemainingPanels = 0;
        for (const FLBVehiclePanelBatch& Batch : Batches)
            RemainingPanels += FMath::Max(0, Batch.RequestedQuantity - Batch.DispatchedQuantity);
        Production->SetBoolField(TEXT("automatic_flow_enabled"), Flow->IsAutomaticFlowEnabled());
        Production->SetNumberField(TEXT("queued_batch_count"), Batches.Num());
        Production->SetNumberField(TEXT("remaining_panel_count"), RemainingPanels);
        Production->SetStringField(TEXT("last_flow_summary"), Flow->GetLastAutomaticFlowSummary());
    }
    else
    {
        Production->SetBoolField(TEXT("automatic_flow_enabled"), false);
        Production->SetNumberField(TEXT("queued_batch_count"), 0);
        Production->SetNumberField(TEXT("remaining_panel_count"), 0);
        Production->SetStringField(TEXT("last_flow_summary"), TEXT("FLOW AUTHORITY NOT FOUND"));
    }
    State->SetObjectField(TEXT("production"), Production);

    const TSharedRef<FJsonObject> Operations = MakeShared<FJsonObject>();
    if (ULBFactoryUIStateSubsystem* UIState = World
        ? World->GetSubsystem<ULBFactoryUIStateSubsystem>() : nullptr)
    {
        const FLBFactoryUIStateSnapshot& Snapshot = UIState->GetSnapshot(true);
        Operations->SetBoolField(TEXT("has_active_order"), Snapshot.Order.bHasActiveOrder);
        Operations->SetStringField(TEXT("order_id"), Snapshot.Order.OrderId.ToString());
        Operations->SetStringField(TEXT("vehicle_model_id"), Snapshot.Order.VehicleModelId.ToString());
        Operations->SetStringField(TEXT("panel_type_id"), Snapshot.Order.PanelTypeId.ToString());
        Operations->SetNumberField(TEXT("issued_quantity"), Snapshot.Order.IssuedQuantity);
        Operations->SetNumberField(TEXT("requested_quantity"), Snapshot.Order.RequestedQuantity);
        Operations->SetStringField(TEXT("objective"), Snapshot.Order.Objective);
        Operations->SetNumberField(TEXT("effective_simulation_rate"), Snapshot.EffectiveSimulationRate);
        Operations->SetNumberField(TEXT("target_spm"), Snapshot.TargetStrokesPerMinute);
        Operations->SetNumberField(TEXT("machine_count"), Snapshot.MachineCount);
        Operations->SetNumberField(TEXT("running_count"), Snapshot.RunningCount);
        Operations->SetNumberField(TEXT("waiting_count"), Snapshot.WaitingCount);
        Operations->SetNumberField(TEXT("fault_count"), Snapshot.FaultCount);
        Operations->SetNumberField(TEXT("alert_count"), Snapshot.Alerts.Num());
        if (const FLBFactoryUIAlertSnapshot* Alert = Snapshot.GetTopAlert())
        {
            const TSharedRef<FJsonObject> TopAlert = MakeShared<FJsonObject>();
            TopAlert->SetStringField(TEXT("severity"), AlertSeverityName(Alert->Severity));
            TopAlert->SetStringField(TEXT("entity_id"), Alert->EntityId.ToString());
            TopAlert->SetStringField(TEXT("title"), Alert->Title);
            TopAlert->SetStringField(TEXT("detail"), Alert->Detail);
            const TSharedRef<FJsonObject> Marker = MakeShared<FJsonObject>();
            SetVectorFields(Marker, Alert->MarkerWorldLocation);
            TopAlert->SetObjectField(TEXT("marker_location"), Marker);
            Operations->SetObjectField(TEXT("top_alert"), TopAlert);
        }
    }
    else
    {
        Operations->SetBoolField(TEXT("has_active_order"), false);
        Operations->SetNumberField(TEXT("alert_count"), 0);
    }
    State->SetObjectField(TEXT("operations"), Operations);

    const TSharedRef<FJsonObject> SupportFleet = MakeShared<FJsonObject>();
    if (ALBPressShopSupportFleetController* Fleet = FindFirstActor<ALBPressShopSupportFleetController>(World))
    {
        SupportFleet->SetBoolField(TEXT("ready"), Fleet->IsFleetReady());
        SupportFleet->SetNumberField(TEXT("installed_unit_count"), Fleet->GetInstalledUnitCount());
        TArray<TSharedPtr<FJsonValue>> Units;
        const FName UnitIds[] = {TEXT("LB-CR01-01"), TEXT("LB-CR01-02"),
            TEXT("LB-MR01-01"), TEXT("LB-MR01-02")};
        for (const FName UnitId : UnitIds)
        {
            FLBSupportRobotSaveState Snapshot;
            if (!Fleet->GetUnitSnapshot(UnitId, Snapshot)) continue;
            const TSharedRef<FJsonObject> Unit = MakeShared<FJsonObject>();
            Unit->SetStringField(TEXT("unit_id"), Snapshot.UnitId.ToString());
            Unit->SetStringField(TEXT("variant_id"), Snapshot.VariantId.ToString());
            Unit->SetStringField(TEXT("state"),
                StaticEnum<ELBSupportRobotState>()->GetNameStringByValue(
                    static_cast<int64>(Snapshot.State)));
            Unit->SetStringField(TEXT("fault"),
                StaticEnum<ELBSupportRobotFault>()->GetNameStringByValue(
                    static_cast<int64>(Snapshot.ActiveFault)));
            Unit->SetNumberField(TEXT("battery_percent"), Snapshot.BatteryStateOfChargePercent);
            Unit->SetBoolField(TEXT("docked"), Snapshot.bDocked);
            const TSharedRef<FJsonObject> Location = MakeShared<FJsonObject>();
            SetVectorFields(Location, Snapshot.SavedTransform.GetLocation());
            Unit->SetObjectField(TEXT("location"), Location);
            Units.Add(MakeShared<FJsonValueObject>(Unit));
        }
        SupportFleet->SetArrayField(TEXT("units"), Units);
    }
    else
    {
        SupportFleet->SetBoolField(TEXT("ready"), false);
        SupportFleet->SetNumberField(TEXT("installed_unit_count"), 0);
    }
    State->SetObjectField(TEXT("support_fleet"), SupportFleet);

    const TSharedRef<FJsonObject> CoilAGV = MakeShared<FJsonObject>();
    if (ALBCoilAGVController* AGV = FindFirstActor<ALBCoilAGVController>(World))
    {
        CoilAGV->SetStringField(TEXT("phase"), CoilPhaseName(AGV->GetPhase()));
        CoilAGV->SetStringField(TEXT("fault"), CoilFaultName(AGV->GetFault()));
        CoilAGV->SetStringField(TEXT("coil_id"), AGV->GetActiveCoilId());
        CoilAGV->SetBoolField(TEXT("owns_load"), AGV->OwnsLoad());
        CoilAGV->SetNumberField(TEXT("yaw_degrees"), AGV->GetVehicleYawDegrees());
        CoilAGV->SetNumberField(TEXT("lift_height_cm"), AGV->GetLiftHeightCm());
        const TSharedRef<FJsonObject> Location = MakeShared<FJsonObject>();
        SetVectorFields(Location, AGV->GetVehicleLocation());
        CoilAGV->SetObjectField(TEXT("location"), Location);
    }
    else
    {
        CoilAGV->SetStringField(TEXT("phase"), TEXT("not_found"));
        CoilAGV->SetStringField(TEXT("fault"), TEXT("not_found"));
    }
    State->SetObjectField(TEXT("coil_agv"), CoilAGV);

    const TSharedRef<FJsonObject> InboundDelivery = MakeShared<FJsonObject>();
    if (ALBInboundDeliveryController* Delivery = FindFirstActor<ALBInboundDeliveryController>(World))
    {
        InboundDelivery->SetBoolField(TEXT("bootstrap_enabled"),
            Delivery->IsPlayerBuilderBootstrapEnabled());
        InboundDelivery->SetBoolField(TEXT("bootstrap_bound"),
            Delivery->IsPlayerBuilderBootstrapBound());
        InboundDelivery->SetBoolField(TEXT("visual_sequence_bound"),
            Delivery->IsVisualSequenceBound());
        InboundDelivery->SetStringField(TEXT("phase"),
            StaticEnum<ELBInboundDeliveryPhase>()->GetNameStringByValue(
                static_cast<int64>(Delivery->GetPhase())));
        InboundDelivery->SetStringField(TEXT("active_coil_id"),
            Delivery->GetActiveCoilId().ToString());
        InboundDelivery->SetStringField(TEXT("inbound_dock_id"),
            Delivery->GetInboundDockId().ToString());
        InboundDelivery->SetStringField(TEXT("pr002_machine_id"),
            Delivery->GetPR002MachineId().ToString());
        InboundDelivery->SetNumberField(TEXT("completed_deliveries"),
            Delivery->GetCompletedDeliveries());
        InboundDelivery->SetStringField(TEXT("reason"), Delivery->GetLastReason());
    }
    else
    {
        InboundDelivery->SetBoolField(TEXT("bootstrap_enabled"), false);
        InboundDelivery->SetBoolField(TEXT("bootstrap_bound"), false);
        InboundDelivery->SetStringField(TEXT("phase"), TEXT("not_found"));
        InboundDelivery->SetStringField(TEXT("reason"), TEXT("INBOUND DELIVERY AUTHORITY NOT FOUND"));
    }
    State->SetObjectField(TEXT("inbound_delivery"), InboundDelivery);

    const TSharedRef<FJsonObject> UI = MakeShared<FJsonObject>();
    if (ALBControlRoomHUD* HUD = FindManagementHUD(World))
    {
        UI->SetBoolField(TEXT("visible"), HUD->IsManagementVisible());
        UI->SetStringField(TEXT("page"), ManagementPageName(HUD->GetManagementPage()));
    }
    else
    {
        UI->SetBoolField(TEXT("visible"), false);
        UI->SetStringField(TEXT("page"), TEXT("not_found"));
    }
    if (ALBManagementPawn* Pawn = FindManagementPawn(World))
    {
        const TSharedRef<FJsonObject> Camera = MakeShared<FJsonObject>();
        SetVectorFields(Camera, Pawn->GetActorLocation());
        Camera->SetNumberField(TEXT("yaw_degrees"), Pawn->GetActorRotation().Yaw);
        Camera->SetNumberField(TEXT("zoom_cm"), Pawn->GetManagementZoomDistance());
        UI->SetObjectField(TEXT("camera"), Camera);
        if (AActor* Selected = Pawn->GetInspectedFactoryActor())
        {
            const TSharedRef<FJsonObject> Selection = MakeShared<FJsonObject>();
            if (ULBFactoryUIStateSubsystem* UIState = World
                ? World->GetSubsystem<ULBFactoryUIStateSubsystem>() : nullptr)
            {
                FLBFactoryUIInspectorSnapshot Inspector;
                if (UIState->BuildInspectorSnapshot(Selected, Inspector))
                {
                    Selection->SetStringField(TEXT("entity_id"), Inspector.EntityId.ToString());
                    Selection->SetStringField(TEXT("kind"), Inspector.Kind);
                    Selection->SetStringField(TEXT("display_name"), Inspector.DisplayName);
                    Selection->SetStringField(TEXT("state"), Inspector.State);
                    Selection->SetStringField(TEXT("reason"), Inspector.Reason);
                }
            }
            Selection->SetStringField(TEXT("actor_name"), Selected->GetName());
            UI->SetObjectField(TEXT("selected_actor"), Selection);
        }
    }
    State->SetObjectField(TEXT("ui"), UI);
    return State;
}

void ALBDeveloperAutomationBridge::WriteSessionDescriptor()
{
    if (!bBridgeEnabled) return;
    const TSharedRef<FJsonObject> Session = MakeShared<FJsonObject>();
    Session->SetStringField(TEXT("protocol"), BridgeProtocol);
    Session->SetNumberField(TEXT("version"), BridgeProtocolVersion);
    Session->SetStringField(TEXT("kind"), TEXT("session"));
    Session->SetStringField(TEXT("session_id"), SessionId);
    Session->SetBoolField(TEXT("enabled"), true);
    Session->SetNumberField(TEXT("next_sequence"), ExpectedSequence);
    Session->SetStringField(TEXT("updated_at_utc"), UtcNowString());
    Session->SetStringField(TEXT("inbox"), InboxDirectory);
    Session->SetStringField(TEXT("outbox"), OutboxDirectory);
    Session->SetStringField(TEXT("screenshots"), ScreenshotDirectory);
    const TArray<FString> CommandNames = {
        TEXT("ping"), TEXT("get_state"), TEXT("open_ui"), TEXT("focus_factory"),
        TEXT("focus_production_stage"),
        TEXT("select_factory_actor"), TEXT("jump_to_alert"),
        TEXT("set_camera"), TEXT("place_machine"), TEXT("place_storage"),
        TEXT("queue_panel_batch"), TEXT("step_flow"), TEXT("support_robot"),
        TEXT("coil_agv"), TEXT("capture_screenshot")};
    TArray<TSharedPtr<FJsonValue>> Commands;
    for (const FString& Command : CommandNames) Commands.Add(MakeShared<FJsonValueString>(Command));
    Session->SetArrayField(TEXT("commands"), Commands);
    WriteJsonAtomic(FPaths::Combine(RootDirectory, TEXT("session.ready")), Session);
}

void ALBDeveloperAutomationBridge::WriteStateSnapshot()
{
    if (!bBridgeEnabled) return;
    const TSharedPtr<FJsonObject> State = CaptureState();
    if (State.IsValid())
        WriteJsonAtomic(FPaths::Combine(RootDirectory, TEXT("state.ready")), State.ToSharedRef());
}

int32 ALBDeveloperAutomationBridge::ProcessReadyCommands()
{
    if (!bBridgeEnabled || !GetWorld() || !IsInGameThread()) return 0;

    struct FReadyCommand
    {
        FString Filename;
        FString CommandId;
        int64 Sequence = 0;
    };

    TArray<FString> Filenames;
    IFileManager::Get().FindFiles(Filenames,
        *FPaths::Combine(InboxDirectory, TEXT("*.ready")), true, false);
    TArray<FReadyCommand> Commands;
    for (const FString& Filename : Filenames)
    {
        FReadyCommand Candidate;
        Candidate.Filename = Filename;
        if (ParseReadyFilename(Filename, Candidate.Sequence, Candidate.CommandId))
            Commands.Add(MoveTemp(Candidate));
        else
            UE_LOG(LogTemp, Warning, TEXT("LINE_BOSS_AUTOMATION_IGNORED_BAD_FILENAME file=%s"),
                *Filename);
    }
    Commands.Sort([](const FReadyCommand& A, const FReadyCommand& B)
    {
        if (A.Sequence != B.Sequence) return A.Sequence < B.Sequence;
        return A.Filename < B.Filename;
    });

    // Old deliveries can only be replays. Archive them without touching gameplay; the original
    // terminal reply remains in outbox for the client to recover.
    for (const FReadyCommand& Command : Commands)
    {
        if (Command.Sequence >= ExpectedSequence) break;
        const FString Source = FPaths::Combine(InboxDirectory, Command.Filename);
        const FString Destination = FPaths::Combine(ArchiveDirectory,
            FString::Printf(TEXT("replay_%s"), *Command.Filename));
        if (IsPathInsideRoot(Source) && IsPathInsideRoot(Destination))
            IFileManager::Get().Move(*Destination, *Source, true, true, false, true);
    }

    int32 Processed = 0;
    for (const FReadyCommand& Command : Commands)
    {
        if (Processed >= MaximumCommandsPerPump || Command.Sequence > ExpectedSequence) break;
        if (Command.Sequence < ExpectedSequence) continue;
        if (!ProcessReadyCommand(Command.Filename, Command.Sequence, Command.CommandId)) break;
        ++Processed;
    }
    return Processed;
}

bool ALBDeveloperAutomationBridge::ProcessReadyCommand(const FString& Filename,
    const int64 Sequence, const FString& FilenameCommandId)
{
    const FString InboxPath = FPaths::Combine(InboxDirectory, Filename);
    const FString ProcessingPath = FPaths::Combine(ProcessingDirectory, Filename);
    if (!IsPathInsideRoot(InboxPath) || !IsPathInsideRoot(ProcessingPath)
        || !IFileManager::Get().Move(*ProcessingPath, *InboxPath, false, true, false, true))
    {
        return false;
    }

    FString Payload;
    FString Type = TEXT("unknown");
    FString ErrorCode;
    FString ErrorMessage;
    TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
    bool bSucceeded = false;

    const int64 FileSize = IFileManager::Get().FileSize(*ProcessingPath);
    TSharedPtr<FJsonObject> Request;
    if (FileSize < 0 || FileSize > MaximumCommandBytes)
    {
        ErrorCode = TEXT("COMMAND_TOO_LARGE");
        ErrorMessage = TEXT("COMMAND FILE MUST BE BETWEEN 0 AND 65536 BYTES");
    }
    else if (!FFileHelper::LoadFileToString(Payload, *ProcessingPath))
    {
        ErrorCode = TEXT("READ_FAILED");
        ErrorMessage = TEXT("COMMAND FILE COULD NOT BE READ");
    }
    else
    {
        const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Payload);
        if (!FJsonSerializer::Deserialize(Reader, Request) || !Request.IsValid())
        {
            ErrorCode = TEXT("MALFORMED_JSON");
            ErrorMessage = TEXT("COMMAND MUST BE ONE COMPLETE JSON OBJECT");
        }
    }

    TSharedPtr<FJsonObject> Args = MakeShared<FJsonObject>();
    if (ErrorCode.IsEmpty())
    {
        if (!Request->HasTypedField<EJson::String>(TEXT("protocol"))
            || Request->GetStringField(TEXT("protocol")) != BridgeProtocol)
        {
            ErrorCode = TEXT("PROTOCOL_MISMATCH");
            ErrorMessage = TEXT("protocol MUST BE lineboss.automation");
        }
        else if (!Request->HasTypedField<EJson::Number>(TEXT("version"))
            || FMath::RoundToInt(Request->GetNumberField(TEXT("version"))) != BridgeProtocolVersion)
        {
            ErrorCode = TEXT("UNSUPPORTED_VERSION");
            ErrorMessage = TEXT("ONLY PROTOCOL VERSION 1 IS SUPPORTED");
        }
        else if (!Request->HasTypedField<EJson::String>(TEXT("kind"))
            || Request->GetStringField(TEXT("kind")) != TEXT("command"))
        {
            ErrorCode = TEXT("KIND_MISMATCH");
            ErrorMessage = TEXT("kind MUST BE command");
        }
        else if (!Request->HasTypedField<EJson::String>(TEXT("session_id"))
            || Request->GetStringField(TEXT("session_id")) != SessionId)
        {
            ErrorCode = TEXT("STALE_SESSION");
            ErrorMessage = TEXT("COMMAND session_id DOES NOT MATCH THE ACTIVE SESSION");
        }
        else if (!Request->HasTypedField<EJson::String>(TEXT("command_id"))
            || Request->GetStringField(TEXT("command_id")) != FilenameCommandId)
        {
            ErrorCode = TEXT("COMMAND_ID_MISMATCH");
            ErrorMessage = TEXT("COMMAND command_id MUST MATCH ITS READY FILENAME");
        }
        else if (!Request->HasTypedField<EJson::Number>(TEXT("sequence"))
            || static_cast<int64>(Request->GetNumberField(TEXT("sequence"))) != Sequence)
        {
            ErrorCode = TEXT("SEQUENCE_MISMATCH");
            ErrorMessage = TEXT("COMMAND sequence MUST MATCH ITS READY FILENAME");
        }
        else if (!Request->HasTypedField<EJson::String>(TEXT("type"))
            || Request->GetStringField(TEXT("type")).IsEmpty())
        {
            ErrorCode = TEXT("INVALID_TYPE");
            ErrorMessage = TEXT("COMMAND type MUST BE A NON-EMPTY STRING");
        }
        else if (Request->HasField(TEXT("args"))
            && !Request->HasTypedField<EJson::Object>(TEXT("args")))
        {
            ErrorCode = TEXT("INVALID_ARGUMENT");
            ErrorMessage = TEXT("COMMAND args MUST BE A JSON OBJECT");
        }
        else
        {
            Type = NormalizeKey(Request->GetStringField(TEXT("type")));
            if (Request->HasField(TEXT("args"))) Args = Request->GetObjectField(TEXT("args"));

            const FString Canonical = Type + TEXT("\n") + SerializeCondensed(Args.ToSharedRef());
            const FString Digest = FMD5::HashAnsiString(*Canonical);
            if (const FProcessedCommandRecord* Existing = ProcessedCommands.Find(FilenameCommandId))
            {
                if (Existing->Digest != Digest)
                {
                    ErrorCode = TEXT("ID_REUSE");
                    ErrorMessage = TEXT("command_id WAS ALREADY USED WITH DIFFERENT ARGUMENTS");
                }
                else
                {
                    bSucceeded = Existing->bSucceeded;
                    Result->SetBoolField(TEXT("replayed"), true);
                    Result->SetNumberField(TEXT("original_sequence"), Existing->OriginalSequence);
                    if (!bSucceeded)
                    {
                        ErrorCode = TEXT("REPLAYED_FAILED_COMMAND");
                        ErrorMessage = TEXT("THE ORIGINAL COMMAND COMPLETED WITH AN ERROR");
                    }
                }
            }
            else
            {
                bSucceeded = ExecuteCommand(Type, Args, FilenameCommandId,
                    Result, ErrorCode, ErrorMessage);
                FProcessedCommandRecord Record;
                Record.Digest = Digest;
                Record.OriginalSequence = Sequence;
                Record.bSucceeded = bSucceeded;
                ProcessedCommands.Add(FilenameCommandId, MoveTemp(Record));
            }
        }
    }

    ++StateRevision;
    if (Type == TEXT("get_state") && Result.IsValid())
    {
        Result->SetNumberField(TEXT("state_revision"), StateRevision);
        Result->SetNumberField(TEXT("next_sequence"), Sequence + 1);
    }
    const TSharedRef<FJsonObject> Reply = MakeShared<FJsonObject>();
    Reply->SetStringField(TEXT("protocol"), BridgeProtocol);
    Reply->SetNumberField(TEXT("version"), BridgeProtocolVersion);
    Reply->SetStringField(TEXT("kind"), TEXT("reply"));
    Reply->SetStringField(TEXT("session_id"), SessionId);
    Reply->SetStringField(TEXT("command_id"), FilenameCommandId);
    Reply->SetNumberField(TEXT("sequence"), Sequence);
    Reply->SetStringField(TEXT("type"), Type);
    Reply->SetBoolField(TEXT("ok"), bSucceeded);
    Reply->SetStringField(TEXT("completed_at_utc"), UtcNowString());
    Reply->SetStringField(TEXT("snapshot_id"),
        FString::Printf(TEXT("state-%lld"), static_cast<long long>(StateRevision)));
    Reply->SetObjectField(TEXT("result"), Result.ToSharedRef());
    if (bSucceeded)
    {
        Reply->SetField(TEXT("error"), MakeShared<FJsonValueNull>());
    }
    else
    {
        const TSharedRef<FJsonObject> Error = MakeShared<FJsonObject>();
        Error->SetStringField(TEXT("code"), ErrorCode.IsEmpty() ? TEXT("COMMAND_FAILED") : ErrorCode);
        Error->SetStringField(TEXT("message"), ErrorMessage.IsEmpty()
            ? TEXT("COMMAND COULD NOT BE COMPLETED") : ErrorMessage);
        Reply->SetObjectField(TEXT("error"), Error);
    }

    const FString ReplyFilename = FString::Printf(TEXT("%012lld_%s.reply.ready"),
        static_cast<long long>(Sequence), *FilenameCommandId);
    const FString ReplyPath = FPaths::Combine(OutboxDirectory, ReplyFilename);
    if (!WriteJsonAtomic(ReplyPath, Reply))
    {
        // The command record prevents a second gameplay side effect if this delivery is retried.
        IFileManager::Get().Move(*InboxPath, *ProcessingPath, true, true, false, true);
        return false;
    }

    const FString ArchivePath = FPaths::Combine(ArchiveDirectory,
        FString::Printf(TEXT("%012lld_%s.request.ready"),
            static_cast<long long>(Sequence), *FilenameCommandId));
    IFileManager::Get().Move(*ArchivePath, *ProcessingPath, true, true, false, true);
    ++ExpectedSequence;
    WriteSessionDescriptor();
    WriteStateSnapshot();
    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_AUTOMATION_COMMAND sequence=%lld id=%s type=%s ok=%d"),
        static_cast<long long>(Sequence), *FilenameCommandId, *Type, bSucceeded ? 1 : 0);
    return true;
}

bool ALBDeveloperAutomationBridge::ExecuteCommand(const FString& Type,
    const TSharedPtr<FJsonObject>& Args, const FString& CommandId,
    TSharedPtr<FJsonObject>& OutResult, FString& OutErrorCode, FString& OutErrorMessage)
{
    UWorld* World = GetWorld();
    OutResult = MakeShared<FJsonObject>();
    OutErrorCode.Reset();
    OutErrorMessage.Reset();
    if (!World)
    {
        OutErrorCode = TEXT("WORLD_NOT_READY");
        OutErrorMessage = TEXT("THE PLAYABLE WORLD IS NOT AVAILABLE");
        return false;
    }

    auto InvalidArguments = [&OutErrorCode, &OutErrorMessage](const FString& Message)
    {
        OutErrorCode = TEXT("INVALID_ARGUMENT");
        OutErrorMessage = Message;
        return false;
    };

    if (Type == TEXT("ping"))
    {
        OutResult->SetStringField(TEXT("message"), TEXT("pong"));
        OutResult->SetStringField(TEXT("session_id"), SessionId);
        OutResult->SetNumberField(TEXT("next_sequence"), ExpectedSequence + 1);
        return true;
    }

    if (Type == TEXT("get_state"))
    {
        OutResult = CaptureState();
        return OutResult.IsValid();
    }

    if (Type == TEXT("open_ui"))
    {
        ALBControlRoomHUD* HUD = FindManagementHUD(World);
        if (!HUD)
        {
            OutErrorCode = TEXT("HUD_NOT_READY");
            OutErrorMessage = TEXT("THE MANAGEMENT HUD IS NOT AVAILABLE");
            return false;
        }
        bool bVisible = true;
        if (!ReadBoolArgument(Args, TEXT("visible"), bVisible, true, OutErrorMessage))
            return InvalidArguments(OutErrorMessage);
        if (!bVisible)
        {
            HUD->CloseManagement();
            OutResult->SetBoolField(TEXT("visible"), false);
            return true;
        }

        FString PageName;
        if (!ReadStringArgument(Args, TEXT("page"), PageName, false,
            TEXT("factory_build"), OutErrorMessage)) return InvalidArguments(OutErrorMessage);
        PageName = NormalizeKey(PageName);
        ELBManagementPage Page = ELBManagementPage::FactoryBuild;
        if (PageName == TEXT("overview")) Page = ELBManagementPage::Overview;
        else if (PageName == TEXT("factory_build") || PageName == TEXT("build"))
            Page = ELBManagementPage::FactoryBuild;
        else if (PageName == TEXT("production") || PageName == TEXT("orders"))
            Page = ELBManagementPage::Production;
        else if (PageName == TEXT("press_trains") || PageName == TEXT("trains"))
            Page = ELBManagementPage::PressTrains;
        else if (PageName == TEXT("support_fleet") || PageName == TEXT("robots"))
            Page = ELBManagementPage::SupportFleet;
        else if (PageName == TEXT("research"))
            Page = ELBManagementPage::Research;
        else if (PageName == TEXT("analytics"))
            Page = ELBManagementPage::Analytics;
        else return InvalidArguments(TEXT("UNKNOWN MANAGEMENT PAGE"));
        HUD->OpenManagementPage(Page);
        OutResult->SetBoolField(TEXT("visible"), true);
        OutResult->SetStringField(TEXT("page"), ManagementPageName(Page));
        return true;
    }

    if (Type == TEXT("focus_production_stage"))
    {
        ALBControlRoomHUD* HUD = FindManagementHUD(World);
        if (!HUD)
        {
            OutErrorCode = TEXT("HUD_NOT_READY");
            OutErrorMessage = TEXT("THE MANAGEMENT HUD IS NOT AVAILABLE");
            return false;
        }
        FString StageId;
        if (!ReadStringArgument(Args, TEXT("stage_id"), StageId, false,
            TEXT(""), OutErrorMessage)) return InvalidArguments(OutErrorMessage);
        const FName CanonicalStageId(*StageId.ToUpper());
        if (!HUD->HandleModernProductionStageAction(CanonicalStageId))
        {
            OutErrorCode = TEXT("STAGE_ACTION_REJECTED");
            OutErrorMessage = TEXT("STAGE MUST BE INSTALLED AND FOCUSABLE");
            return false;
        }
        OutResult->SetStringField(TEXT("stage_id"), CanonicalStageId.ToString());
        OutResult->SetStringField(TEXT("action"), TEXT("FOCUS_LIVE_ASSET"));
        return true;
    }

    if (Type == TEXT("focus_factory"))
    {
        ALBManagementPawn* Pawn = FindManagementPawn(World);
        if (!Pawn)
        {
            OutErrorCode = TEXT("CAMERA_NOT_READY");
            OutErrorMessage = TEXT("THE MANAGEMENT CAMERA IS NOT AVAILABLE");
            return false;
        }
        if (!Pawn->FocusBuiltFactory())
        {
            OutErrorCode = TEXT("NO_FACTORY_TO_FOCUS");
            OutErrorMessage = TEXT("PLACE AT LEAST ONE MACHINE OR STORAGE ZONE FIRST");
            return false;
        }
        const TSharedRef<FJsonObject> Location = MakeShared<FJsonObject>();
        SetVectorFields(Location, Pawn->GetActorLocation());
        OutResult->SetObjectField(TEXT("location"), Location);
        OutResult->SetNumberField(TEXT("yaw_degrees"), Pawn->GetActorRotation().Yaw);
        OutResult->SetNumberField(TEXT("zoom_cm"), Pawn->GetManagementZoomDistance());
        return true;
    }

    if (Type == TEXT("select_factory_actor"))
    {
        ALBManagementPawn* Pawn = FindManagementPawn(World);
        ULBFactoryUIStateSubsystem* UIState =
            World->GetSubsystem<ULBFactoryUIStateSubsystem>();
        if (!Pawn || !UIState)
        {
            OutErrorCode = TEXT("UI_NOT_READY");
            OutErrorMessage = TEXT("THE MANAGEMENT SELECTION AUTHORITY IS NOT AVAILABLE");
            return false;
        }
        FString EntityId;
        FString ExpectedKind;
        bool bFocus = false;
        if (!ReadStringArgument(Args, TEXT("id"), EntityId, true,
                FString(), OutErrorMessage)
            || !ReadStringArgument(Args, TEXT("kind"), ExpectedKind, false,
                FString(), OutErrorMessage)
            || !ReadBoolArgument(Args, TEXT("focus"), bFocus, false, OutErrorMessage))
        {
            return InvalidArguments(OutErrorMessage);
        }
        if (!IsSafeToken(EntityId, 80))
            return InvalidArguments(TEXT("id CONTAINS UNSAFE CHARACTERS"));
        AActor* Target = UIState->FindFactoryActorById(FName(*EntityId));
        FLBFactoryUIInspectorSnapshot Inspector;
        if (!Target || !UIState->BuildInspectorSnapshot(Target, Inspector))
        {
            OutErrorCode = TEXT("FACTORY_ACTOR_NOT_FOUND");
            OutErrorMessage = TEXT("NO SELECTABLE FACTORY ACTOR MATCHES THAT ID");
            return false;
        }
        if (!ExpectedKind.IsEmpty()
            && NormalizeKey(ExpectedKind) != NormalizeKey(Inspector.Kind))
        {
            return InvalidArguments(TEXT("kind DOES NOT MATCH THE FACTORY ACTOR"));
        }
        if (!Pawn->SelectFactoryActor(Target, bFocus))
        {
            OutErrorCode = TEXT("SELECTION_REJECTED");
            OutErrorMessage = TEXT("THE FACTORY ACTOR COULD NOT BE SELECTED SAFELY");
            return false;
        }
        OutResult->SetStringField(TEXT("entity_id"), Inspector.EntityId.ToString());
        OutResult->SetStringField(TEXT("kind"), Inspector.Kind);
        OutResult->SetStringField(TEXT("display_name"), Inspector.DisplayName);
        OutResult->SetBoolField(TEXT("focused"), bFocus);
        return true;
    }

    if (Type == TEXT("jump_to_alert"))
    {
        ALBManagementPawn* Pawn = FindManagementPawn(World);
        ULBFactoryUIStateSubsystem* UIState =
            World->GetSubsystem<ULBFactoryUIStateSubsystem>();
        const FLBFactoryUIAlertSnapshot* Alert = UIState
            ? UIState->GetSnapshot(true).GetTopAlert() : nullptr;
        if (!Pawn || !Alert)
        {
            OutErrorCode = TEXT("NO_ACTIVE_ALERT");
            OutErrorMessage = TEXT("THERE IS NO ACTIVE FACTORY ALERT TO FOCUS");
            return false;
        }
        const FName EntityId = Alert->EntityId;
        const FString Title = Alert->Title;
        if (!Pawn->JumpToTopFactoryAlert())
        {
            OutErrorCode = TEXT("ALERT_FOCUS_REJECTED");
            OutErrorMessage = TEXT("THE TOP ALERT DOES NOT HAVE A SAFE CAMERA TARGET");
            return false;
        }
        OutResult->SetStringField(TEXT("entity_id"), EntityId.ToString());
        OutResult->SetStringField(TEXT("title"), Title);
        OutResult->SetBoolField(TEXT("focused"), true);
        return true;
    }

    if (Type == TEXT("set_camera"))
    {
        ALBManagementPawn* Pawn = FindManagementPawn(World);
        if (!Pawn)
        {
            OutErrorCode = TEXT("CAMERA_NOT_READY");
            OutErrorMessage = TEXT("THE MANAGEMENT CAMERA IS NOT AVAILABLE");
            return false;
        }
        const FVector Current = Pawn->GetActorLocation();
        double X = Current.X, Y = Current.Y, Z = Current.Z;
        double Yaw = Pawn->GetActorRotation().Yaw;
        double Zoom = Pawn->GetManagementZoomDistance();
        if (!ReadNumberArgument(Args, TEXT("x"), X, false, X, OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("y"), Y, false, Y, OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("z"), Z, false, Z, OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("yaw_degrees"), Yaw, false, Yaw, OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("zoom_cm"), Zoom, false, Zoom, OutErrorMessage))
        {
            return InvalidArguments(OutErrorMessage);
        }
        if (FMath::Abs(X) > 1000000.0 || FMath::Abs(Y) > 1000000.0
            || FMath::Abs(Z) > 100000.0) return InvalidArguments(TEXT("CAMERA LOCATION IS OUT OF RANGE"));
        if (!Pawn->SetAutomationCamera(FVector(X, Y, Z), Yaw, Zoom))
        {
            OutErrorCode = TEXT("CAMERA_REJECTED");
            OutErrorMessage = TEXT("CAMERA VALUES COULD NOT BE APPLIED");
            return false;
        }
        const TSharedRef<FJsonObject> Location = MakeShared<FJsonObject>();
        SetVectorFields(Location, Pawn->GetActorLocation());
        OutResult->SetObjectField(TEXT("location"), Location);
        OutResult->SetNumberField(TEXT("yaw_degrees"), Pawn->GetActorRotation().Yaw);
        OutResult->SetNumberField(TEXT("zoom_cm"), Pawn->GetManagementZoomDistance());
        return true;
    }

    if (Type == TEXT("place_machine"))
    {
        FString MachineName;
        if (!ReadStringArgument(Args, TEXT("machine_type"), MachineName, true,
            FString(), OutErrorMessage)) return InvalidArguments(OutErrorMessage);
        ELBFactoryBuildMachineType MachineType = ELBFactoryBuildMachineType::InboundDeliveryDock;
        if (!TryParseMachineType(MachineName, MachineType))
            return InvalidArguments(TEXT("UNKNOWN MACHINE TYPE"));

        double X = 0.0, Y = 0.0, Z = 0.0, Yaw = 0.0;
        if (!ReadNumberArgument(Args, TEXT("x"), X, true, 0.0, OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("y"), Y, true, 0.0, OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("z"), Z, false, 0.0, OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("yaw_degrees"), Yaw, false, 0.0, OutErrorMessage))
        {
            return InvalidArguments(OutErrorMessage);
        }
        if (FMath::Abs(X) > 100000.0 || FMath::Abs(Y) > 100000.0
            || FMath::Abs(Z) > 10000.0) return InvalidArguments(TEXT("PLACEMENT LOCATION IS OUT OF RANGE"));

        ULBFactoryMachineBuilderSubsystem* Builder =
            World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
        AActor* BuiltActor = nullptr;
        FString Reason;
        if (!Builder || !Builder->PlaceMachine(MachineType,
            FTransform(FRotator(0.0f, Yaw, 0.0f), FVector(X, Y, Z)), BuiltActor, Reason))
        {
            OutErrorCode = TEXT("PLACEMENT_REJECTED");
            OutErrorMessage = Reason.IsEmpty() ? TEXT("MACHINE PLACEMENT WAS REJECTED") : Reason;
            return false;
        }
        OutResult->SetStringField(TEXT("machine_type"), MachineTypeName(MachineType));
        OutResult->SetStringField(TEXT("actor_name"), BuiltActor ? BuiltActor->GetName() : TEXT("unknown"));
        if (const ALBFactoryBuildMachine* Machine = Cast<ALBFactoryBuildMachine>(BuiltActor))
            OutResult->SetStringField(TEXT("machine_id"), Machine->GetMachineId().ToString());
        if (const ALBBodyWeldLineActor* WeldLine = Cast<ALBBodyWeldLineActor>(BuiltActor))
            OutResult->SetStringField(TEXT("line_id"), WeldLine->GetLineId().ToString());
        else if (const ALBECoatLineActor* ECoatLine = Cast<ALBECoatLineActor>(BuiltActor))
            OutResult->SetStringField(TEXT("line_id"), ECoatLine->GetLineId().ToString());
        const TSharedRef<FJsonObject> Location = MakeShared<FJsonObject>();
        SetVectorFields(Location, BuiltActor ? BuiltActor->GetActorLocation() : FVector(X, Y, Z));
        OutResult->SetObjectField(TEXT("location"), Location);
        return true;
    }

    if (Type == TEXT("place_storage"))
    {
        FString StorageName;
        if (!ReadStringArgument(Args, TEXT("storage_type"), StorageName, true,
            FString(), OutErrorMessage)) return InvalidArguments(OutErrorMessage);
        StorageName = NormalizeKey(StorageName);
        ELBPressShopStorageType StorageType = ELBPressShopStorageType::BareCoils;
        if (StorageName == TEXT("bare_coils")) StorageType = ELBPressShopStorageType::BareCoils;
        else if (StorageName == TEXT("prepared_blanks")) StorageType = ELBPressShopStorageType::PreparedBlanks;
        else if (StorageName == TEXT("finished_panel_stillages") || StorageName == TEXT("finished_panels")
            || StorageName == TEXT("wip_panel_stillages") || StorageName == TEXT("pressed_panel_wip"))
            StorageType = ELBPressShopStorageType::FinishedPanelStillages;
        else if (StorageName == TEXT("scrap")) StorageType = ELBPressShopStorageType::Scrap;
        else if (StorageName == TEXT("maintenance_parts")) StorageType = ELBPressShopStorageType::MaintenanceParts;
        else if (StorageName == TEXT("quarantine")) StorageType = ELBPressShopStorageType::Quarantine;
        else if (StorageName == TEXT("empty_panel_stillages")
            || StorageName == TEXT("empty_stillages") || StorageName == TEXT("stillage_returns"))
            StorageType = ELBPressShopStorageType::EmptyPanelStillages;
        else return InvalidArguments(TEXT("UNKNOWN STORAGE TYPE"));

        double X = 0.0, Y = 0.0, Z = 0.0, Yaw = 0.0;
        if (!ReadNumberArgument(Args, TEXT("x"), X, true, 0.0, OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("y"), Y, true, 0.0, OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("z"), Z, false, 0.0, OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("yaw_degrees"), Yaw, false, 0.0, OutErrorMessage))
        {
            return InvalidArguments(OutErrorMessage);
        }
        ALBPressShopBuildAuthority* Authority = FindFirstActor<ALBPressShopBuildAuthority>(World);
        if (!Authority)
        {
            OutErrorCode = TEXT("BUILD_AUTHORITY_NOT_READY");
            OutErrorMessage = TEXT("THE FACTORY FLOOR BUILD AUTHORITY IS NOT AVAILABLE");
            return false;
        }
        FVector HalfExtent;
        int32 Capacity = 0;
        FString Reason;
        if (!Authority->GetStoragePlacementDefaults(StorageType, HalfExtent, Capacity, Reason))
        {
            OutErrorCode = TEXT("STORAGE_DEFAULTS_UNAVAILABLE");
            OutErrorMessage = Reason;
            return false;
        }
        if (!Args->HasField(TEXT("z"))) Z = HalfExtent.Z;
        ALBPressShopStorageZone* Zone = nullptr;
        if (!Authority->PlaceStorageZone(StorageType,
            FTransform(FRotator(0.0f, Yaw, 0.0f), FVector(X, Y, Z)),
            HalfExtent, Capacity, Zone, Reason))
        {
            OutErrorCode = TEXT("PLACEMENT_REJECTED");
            OutErrorMessage = Reason.IsEmpty() ? TEXT("STORAGE PLACEMENT WAS REJECTED") : Reason;
            return false;
        }
        OutResult->SetStringField(TEXT("storage_type"), StorageTypeName(StorageType));
        OutResult->SetStringField(TEXT("zone_id"), Zone ? Zone->GetZoneId().ToString() : TEXT("unknown"));
        OutResult->SetNumberField(TEXT("capacity"), Capacity);
        return true;
    }

    if (Type == TEXT("queue_panel_batch"))
    {
        ALBPlayerBuiltPressFlowController* Flow =
            FindFirstActor<ALBPlayerBuiltPressFlowController>(World);
        if (!Flow)
        {
            OutErrorCode = TEXT("FLOW_NOT_READY");
            OutErrorMessage = TEXT("THE PRODUCTION FLOW AUTHORITY IS NOT AVAILABLE");
            return false;
        }
        FString OrderId, VehicleModel, PanelType, ProductionLine, DedicatedTrain;
        double Quantity = 10.0;
        if (!ReadStringArgument(Args, TEXT("order_id"), OrderId, false,
                FString::Printf(TEXT("AUTO-%s"), *CommandId), OutErrorMessage)
            || !ReadStringArgument(Args, TEXT("vehicle_model_id"), VehicleModel, false,
                TEXT("CAIRNWELL_2040"), OutErrorMessage)
            || !ReadStringArgument(Args, TEXT("panel_type_id"), PanelType, false,
                TEXT("DOOR_FRONT_LEFT"), OutErrorMessage)
            || !ReadStringArgument(Args, TEXT("production_line_id"), ProductionLine, false,
                FString(), OutErrorMessage)
            || !ReadStringArgument(Args, TEXT("dedicated_train_id"), DedicatedTrain, false,
                FString(), OutErrorMessage)
            || !ReadNumberArgument(Args, TEXT("quantity"), Quantity, false, 10.0, OutErrorMessage))
        {
            return InvalidArguments(OutErrorMessage);
        }
        if (Quantity < 1.0 || Quantity > 10000.0 || !FMath::IsNearlyEqual(Quantity, FMath::RoundToDouble(Quantity)))
            return InvalidArguments(TEXT("quantity MUST BE A WHOLE NUMBER FROM 1 TO 10000"));
        FLBVehiclePanelBatch Batch;
        Batch.OrderId = FName(*OrderId);
        Batch.VehicleModelId = FName(*VehicleModel);
        Batch.PanelTypeId = FName(*PanelType);
        Batch.ProductionLineId = FName(*ProductionLine);
        Batch.DedicatedTrainId = FName(*DedicatedTrain);
        Batch.RequestedQuantity = FMath::RoundToInt(Quantity);
        FString Reason;
        if (!Flow->QueuePanelBatch(Batch, Reason))
        {
            OutErrorCode = TEXT("ORDER_REJECTED");
            OutErrorMessage = Reason;
            return false;
        }
        OutResult->SetStringField(TEXT("order_id"), Batch.OrderId.ToString());
        OutResult->SetStringField(TEXT("vehicle_model_id"), Batch.VehicleModelId.ToString());
        OutResult->SetStringField(TEXT("panel_type_id"), Batch.PanelTypeId.ToString());
        OutResult->SetNumberField(TEXT("quantity"), Batch.RequestedQuantity);
        OutResult->SetStringField(TEXT("message"), Reason);
        return true;
    }

    if (Type == TEXT("step_flow"))
    {
        ALBPlayerBuiltPressFlowController* Flow =
            FindFirstActor<ALBPlayerBuiltPressFlowController>(World);
        if (!Flow)
        {
            OutErrorCode = TEXT("FLOW_NOT_READY");
            OutErrorMessage = TEXT("THE PRODUCTION FLOW AUTHORITY IS NOT AVAILABLE");
            return false;
        }
        FString Summary;
        const int32 TransferCount = Flow->ExecuteAutomaticStep(Summary);
        OutResult->SetNumberField(TEXT("transfer_count"), TransferCount);
        OutResult->SetStringField(TEXT("summary"), Summary);
        return true;
    }

    if (Type == TEXT("support_robot"))
    {
        ALBPressShopSupportFleetController* Fleet =
            FindFirstActor<ALBPressShopSupportFleetController>(World);
        if (!Fleet)
        {
            OutErrorCode = TEXT("SUPPORT_FLEET_NOT_READY");
            OutErrorMessage = TEXT("THE SUPPORT FLEET AUTHORITY IS NOT AVAILABLE");
            return false;
        }
        FString Action, UnitId;
        if (!ReadStringArgument(Args, TEXT("action"), Action, true, FString(), OutErrorMessage)
            || !ReadStringArgument(Args, TEXT("unit_id"), UnitId, true, FString(), OutErrorMessage))
        {
            return InvalidArguments(OutErrorMessage);
        }
        Action = NormalizeKey(Action);
        if (!IsSafeToken(UnitId, 64)) return InvalidArguments(TEXT("unit_id CONTAINS UNSAFE CHARACTERS"));
        bool bCompleted = false;
        if (Action == TEXT("dispatch")) bCompleted = Fleet->DispatchUnit(FName(*UnitId));
        else if (Action == TEXT("return") || Action == TEXT("return_to_dock"))
            bCompleted = Fleet->ReturnUnitToDock(FName(*UnitId));
        else return InvalidArguments(TEXT("support_robot action MUST BE dispatch OR return"));
        if (!bCompleted)
        {
            OutErrorCode = TEXT("ROBOT_COMMAND_REJECTED");
            OutErrorMessage = TEXT("THE UNIT IS UNKNOWN OR NOT IN A SAFE STATE FOR THAT ACTION");
            return false;
        }
        OutResult->SetStringField(TEXT("unit_id"), UnitId);
        OutResult->SetStringField(TEXT("action"), Action);
        return true;
    }

    if (Type == TEXT("coil_agv"))
    {
        ALBCoilAGVController* AGV = FindFirstActor<ALBCoilAGVController>(World);
        if (!AGV)
        {
            OutErrorCode = TEXT("COIL_AGV_NOT_READY");
            OutErrorMessage = TEXT("THE COIL AGV AUTHORITY IS NOT AVAILABLE");
            return false;
        }
        FString Action;
        if (!ReadStringArgument(Args, TEXT("action"), Action, false,
            TEXT("state"), OutErrorMessage)) return InvalidArguments(OutErrorMessage);
        Action = NormalizeKey(Action);
        bool bCompleted = true;
        FString CoilId;
        if (Action == TEXT("dispatch"))
        {
            if (!ReadStringArgument(Args, TEXT("coil_id"), CoilId, true,
                FString(), OutErrorMessage)) return InvalidArguments(OutErrorMessage);
            bCompleted = AGV->StartDispatch(CoilId);
        }
        else if (Action == TEXT("reload"))
        {
            if (!ReadStringArgument(Args, TEXT("coil_id"), CoilId, true,
                FString(), OutErrorMessage)) return InvalidArguments(OutErrorMessage);
            bCompleted = AGV->ReloadAtStagedPoint(CoilId);
        }
        else if (Action == TEXT("confirm_handoff"))
        {
            bCompleted = AGV->ConfirmHandoff(CoilId);
        }
        else if (Action == TEXT("reset_fault"))
        {
            FString EvidenceId;
            if (!ReadStringArgument(Args, TEXT("evidence_id"), EvidenceId, true,
                FString(), OutErrorMessage)) return InvalidArguments(OutErrorMessage);
            bCompleted = AGV->ResetFault(FName(*EvidenceId));
        }
        else if (Action != TEXT("state"))
        {
            return InvalidArguments(TEXT("UNKNOWN coil_agv action"));
        }
        if (!bCompleted)
        {
            OutErrorCode = TEXT("COIL_AGV_COMMAND_REJECTED");
            OutErrorMessage = TEXT("THE AGV SAFETY OR PHASE CONTRACT REJECTED THAT ACTION");
            return false;
        }
        OutResult->SetStringField(TEXT("action"), Action);
        OutResult->SetStringField(TEXT("phase"), CoilPhaseName(AGV->GetPhase()));
        OutResult->SetStringField(TEXT("fault"), CoilFaultName(AGV->GetFault()));
        OutResult->SetStringField(TEXT("coil_id"), CoilId.IsEmpty() ? AGV->GetActiveCoilId() : CoilId);
        return true;
    }

    if (Type == TEXT("capture_screenshot"))
    {
        FString Name;
        if (!ReadStringArgument(Args, TEXT("name"), Name, false,
            CommandId, OutErrorMessage)) return InvalidArguments(OutErrorMessage);
        if (!IsSafeToken(Name, 80))
            return InvalidArguments(TEXT("SCREENSHOT name MAY ONLY USE LETTERS, NUMBERS, DASH OR UNDERSCORE"));
        const FString ScreenshotPath = FPaths::Combine(ScreenshotDirectory, Name + TEXT(".png"));
        if (!IsPathInsideRoot(ScreenshotPath)) return InvalidArguments(TEXT("SCREENSHOT PATH IS OUTSIDE THE BRIDGE ROOT"));
        FScreenshotRequest::RequestScreenshot(ScreenshotPath, true, false);
        OutResult->SetBoolField(TEXT("queued"), true);
        OutResult->SetStringField(TEXT("path"), ScreenshotPath);
        OutResult->SetStringField(TEXT("completion"), TEXT("poll path until the rendered frame is written"));
        return true;
    }

    OutErrorCode = TEXT("UNSUPPORTED_COMMAND");
    OutErrorMessage = FString::Printf(TEXT("UNKNOWN COMMAND TYPE: %s"), *Type);
    return false;
}
