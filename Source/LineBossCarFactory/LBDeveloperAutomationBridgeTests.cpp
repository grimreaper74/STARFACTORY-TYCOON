#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "LBBodyWeldLineActor.h"
#include "LBControlRoomHUD.h"
#include "LBDeveloperAutomationBridge.h"
#include "LBFactoryBuildMachine.h"
#include "LBManagementPawn.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBPressShopBuildAuthority.h"
#include "Misc/FileHelper.h"
#include "Misc/Guid.h"
#include "Misc/Paths.h"
#include "Policies/CondensedJsonPrintPolicy.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
    struct FLBBridgeTestWorld
    {
        UWorld* World = nullptr;

        explicit FLBBridgeTestWorld(const TCHAR* Prefix)
        {
            const FString Name = FString::Printf(TEXT("%s_%s"), Prefix,
                *FGuid::NewGuid().ToString(EGuidFormats::Digits).Left(8));
            World = UWorld::CreateWorld(EWorldType::Game, false, FName(*Name));
            if (World)
            {
                FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
                Context.SetCurrentWorld(World);
                World->InitializeActorsForPlay(FURL());
                World->BeginPlay();
            }
        }

        ~FLBBridgeTestWorld()
        {
            if (World)
            {
                World->DestroyWorld(false);
                GEngine->DestroyWorldContext(World);
            }
        }
    };

    FString JsonText(const TSharedRef<FJsonObject>& Object)
    {
        FString Text;
        const TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
            TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Text);
        FJsonSerializer::Serialize(Object, Writer);
        Writer->Close();
        return Text;
    }

    FString ReadyFilename(const int64 Sequence, const FString& CommandId)
    {
        return FString::Printf(TEXT("%012lld_%s.ready"),
            static_cast<long long>(Sequence), *CommandId);
    }

    bool WriteRawReady(const ALBDeveloperAutomationBridge* Bridge, const int64 Sequence,
        const FString& CommandId, const FString& Payload)
    {
        const FString FinalPath = FPaths::Combine(Bridge->GetInboxDirectory(),
            ReadyFilename(Sequence, CommandId));
        const FString TemporaryPath = FinalPath + TEXT(".tmp");
        return FFileHelper::SaveStringToFile(Payload, *TemporaryPath,
            FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM)
            && IFileManager::Get().Move(*FinalPath, *TemporaryPath, true, true, false, true);
    }

    bool WriteCommand(const ALBDeveloperAutomationBridge* Bridge, const int64 Sequence,
        const FString& CommandId, const FString& Type,
        const TSharedRef<FJsonObject>& Args = MakeShared<FJsonObject>())
    {
        const TSharedRef<FJsonObject> Command = MakeShared<FJsonObject>();
        Command->SetStringField(TEXT("protocol"), TEXT("lineboss.automation"));
        Command->SetNumberField(TEXT("version"), 1);
        Command->SetStringField(TEXT("kind"), TEXT("command"));
        Command->SetStringField(TEXT("session_id"), Bridge->GetSessionId());
        Command->SetStringField(TEXT("command_id"), CommandId);
        Command->SetNumberField(TEXT("sequence"), Sequence);
        Command->SetStringField(TEXT("type"), Type);
        Command->SetObjectField(TEXT("args"), Args);
        return WriteRawReady(Bridge, Sequence, CommandId, JsonText(Command));
    }

    TSharedPtr<FJsonObject> ReadReply(const ALBDeveloperAutomationBridge* Bridge,
        const int64 Sequence, const FString& CommandId)
    {
        const FString Path = FPaths::Combine(Bridge->GetOutboxDirectory(),
            FString::Printf(TEXT("%012lld_%s.reply.ready"),
                static_cast<long long>(Sequence), *CommandId));
        FString Text;
        TSharedPtr<FJsonObject> Reply;
        if (!FFileHelper::LoadFileToString(Text, *Path)) return nullptr;
        const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
        return FJsonSerializer::Deserialize(Reader, Reply) ? Reply : nullptr;
    }

    void CleanupBridgeRoot(const FString& Root)
    {
        FString SavedTests = FPaths::ConvertRelativePathToFull(
            FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("AutomationBridgeTests")));
        FString Candidate = FPaths::ConvertRelativePathToFull(Root);
        FPaths::NormalizeFilename(SavedTests);
        FPaths::NormalizeFilename(Candidate);
        if (Candidate.StartsWith(SavedTests + TEXT("/"), ESearchCase::IgnoreCase))
            IFileManager::Get().DeleteDirectory(*Candidate, false, true);
    }

    ALBDeveloperAutomationBridge* SpawnTestBridge(UWorld* World, FString& OutRoot)
    {
        ALBDeveloperAutomationBridge* Bridge = World
            ? World->SpawnActor<ALBDeveloperAutomationBridge>() : nullptr;
        if (!Bridge) return nullptr;
        const FString Leaf = FString::Printf(TEXT("Bridge_%s"),
            *FGuid::NewGuid().ToString(EGuidFormats::Digits));
        if (!Bridge->StartForTesting(Leaf)) return nullptr;
        OutRoot = Bridge->GetBridgeRootDirectory();
        return Bridge;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBDeveloperAutomationBridgeGatingTest,
    "LineBoss.AutomationBridge.Gating.DisabledByDefault",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBDeveloperAutomationBridgeGatingTest::RunTest(const FString& Parameters)
{
    TestFalse(TEXT("Empty command line does not enable bridge"),
        ALBDeveloperAutomationBridge::IsEnabledFromCommandLine(TEXT("")));
    TestTrue(TEXT("Exact explicit launch flag enables bridge"),
        ALBDeveloperAutomationBridge::IsEnabledFromCommandLine(TEXT("-LineBossAutomationBridge")));
    TestFalse(TEXT("Similar-looking longer flag is not accepted"),
        ALBDeveloperAutomationBridge::IsEnabledFromCommandLine(TEXT("-LineBossAutomationBridgeExtra")));
    TestFalse(TEXT("Unprefixed word is not treated as a launch flag"),
        ALBDeveloperAutomationBridge::IsEnabledFromCommandLine(TEXT("LineBossAutomationBridge")));

    FLBBridgeTestWorld Fixture(TEXT("LBBridgeGate"));
    ALBDeveloperAutomationBridge* Bridge = Fixture.World
        ? Fixture.World->SpawnActor<ALBDeveloperAutomationBridge>() : nullptr;
    TestNotNull(TEXT("Bridge actor exists for gating test"), Bridge);
    if (Bridge)
    {
        TestFalse(TEXT("Ordinary actor remains disabled by default"), Bridge->IsBridgeEnabled());
        TestTrue(TEXT("Disabled bridge creates no mailbox path"),
            Bridge->GetBridgeRootDirectory().IsEmpty());
        FString Root;
        Bridge = SpawnTestBridge(Fixture.World, Root);
        TestNotNull(TEXT("Test-only isolated bridge starts"), Bridge);
        if (Bridge)
        {
            TestTrue(TEXT("Test bridge reports enabled"), Bridge->IsBridgeEnabled());
            TestFalse(TEXT("Bridge publishes an absolute inbox path for external clients"),
                FPaths::IsRelative(Bridge->GetInboxDirectory()));
            TestFalse(TEXT("Bridge publishes an absolute outbox path for external clients"),
                FPaths::IsRelative(Bridge->GetOutboxDirectory()));
            TestTrue(TEXT("Mailbox is rooted below Saved AutomationBridgeTests"),
                FPaths::ConvertRelativePathToFull(Root).Contains(TEXT("/Saved/AutomationBridgeTests/"),
                    ESearchCase::IgnoreCase));
        }
        CleanupBridgeRoot(Root);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBDeveloperAutomationBridgeECoatMachineNamesTest,
    "LineBoss.AutomationBridge.Protocol.ECoatMachineNames",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBDeveloperAutomationBridgeECoatMachineNamesTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("ED line has one canonical serialized machine name"),
        ALBDeveloperAutomationBridge::SerializeMachineType(
            ELBFactoryBuildMachineType::ECoatLine), FString(TEXT("ecoat_line")));

    const FString AcceptedNames[] = {
        TEXT("ecoat_line"), TEXT("e_coat_line"), TEXT("ed_line")
    };
    for (const FString& Name : AcceptedNames)
    {
        ELBFactoryBuildMachineType Parsed = ELBFactoryBuildMachineType::InboundDeliveryDock;
        TestTrue(FString::Printf(TEXT("place_machine accepts %s as the ED line"), *Name),
            ALBDeveloperAutomationBridge::TryParseMachineType(Name, Parsed));
        TestEqual(FString::Printf(TEXT("%s resolves to the ED-line enum"), *Name),
            Parsed, ELBFactoryBuildMachineType::ECoatLine);
    }
    ELBFactoryBuildMachineType Rejected = ELBFactoryBuildMachineType::InboundDeliveryDock;
    TestFalse(TEXT("Undocumented near-match remains rejected"),
        ALBDeveloperAutomationBridge::TryParseMachineType(TEXT("ecoat"), Rejected));

    // Exercise the actual command route as well as the parser. In this deliberately empty
    // factory each accepted name reaches progression validation and is rejected there; an
    // unknown machine name would instead fail earlier with INVALID_ARGUMENT.
    FLBBridgeTestWorld Fixture(TEXT("LBBridgeECoatNames"));
    FString Root;
    ALBDeveloperAutomationBridge* Bridge = SpawnTestBridge(Fixture.World, Root);
    TestNotNull(TEXT("Bridge starts for ED-line alias command test"), Bridge);
    if (!Bridge) return false;
    constexpr int32 AcceptedNameCount = static_cast<int32>(UE_ARRAY_COUNT(AcceptedNames));
    for (int32 Index = 0; Index < AcceptedNameCount; ++Index)
    {
        const TSharedRef<FJsonObject> Args = MakeShared<FJsonObject>();
        Args->SetStringField(TEXT("machine_type"), AcceptedNames[Index]);
        Args->SetNumberField(TEXT("x"), 0.0);
        Args->SetNumberField(TEXT("y"), 0.0);
        TestTrue(FString::Printf(TEXT("%s place_machine command is written"), *AcceptedNames[Index]),
            WriteCommand(Bridge, Index + 1,
                FString::Printf(TEXT("ecoat_alias_%d"), Index + 1),
                TEXT("place_machine"), Args));
    }
    TestEqual(TEXT("All three ED-line names receive terminal command replies"),
        Bridge->PumpForTesting(), AcceptedNameCount);
    for (int32 Index = 0; Index < AcceptedNameCount; ++Index)
    {
        const TSharedPtr<FJsonObject> Reply = ReadReply(Bridge, Index + 1,
            FString::Printf(TEXT("ecoat_alias_%d"), Index + 1));
        TestTrue(FString::Printf(TEXT("%s reaches placement validation"), *AcceptedNames[Index]),
            Reply.IsValid() && !Reply->GetBoolField(TEXT("ok"))
            && Reply->GetObjectField(TEXT("error"))->GetStringField(TEXT("code"))
                == TEXT("PLACEMENT_REJECTED"));
    }
    CleanupBridgeRoot(Root);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBDeveloperAutomationBridgeOrderedTest,
    "LineBoss.AutomationBridge.Protocol.OrderedExactlyOnce",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBDeveloperAutomationBridgeOrderedTest::RunTest(const FString& Parameters)
{
    FLBBridgeTestWorld Fixture(TEXT("LBBridgeOrdered"));
    FString Root;
    ALBDeveloperAutomationBridge* Bridge = SpawnTestBridge(Fixture.World, Root);
    ALBPlayerBuiltPressFlowController* Flow = Fixture.World
        ? Fixture.World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    TestNotNull(TEXT("Bridge starts"), Bridge);
    TestNotNull(TEXT("Flow authority starts"), Flow);
    if (!Bridge || !Flow) return false;

    const TSharedRef<FJsonObject> OrderArgs = MakeShared<FJsonObject>();
    OrderArgs->SetStringField(TEXT("order_id"), TEXT("BRIDGE-ORDER-01"));
    OrderArgs->SetStringField(TEXT("panel_type_id"), TEXT("DOOR_FRONT_LEFT"));
    OrderArgs->SetNumberField(TEXT("quantity"), 12);
    TestTrue(TEXT("Out-of-order sequence two is delivered"),
        WriteCommand(Bridge, 2, TEXT("order_once"), TEXT("queue_panel_batch"), OrderArgs));
    TestEqual(TEXT("Sequence two waits for sequence one"), Bridge->PumpForTesting(), 0);
    TestEqual(TEXT("Waiting command has no side effect"), Flow->GetPanelBatches().Num(), 0);

    FFileHelper::SaveStringToFile(TEXT("partial"),
        *FPaths::Combine(Bridge->GetInboxDirectory(), TEXT("000000000001_partial.tmp")));
    TestEqual(TEXT("Temporary files are ignored"), Bridge->PumpForTesting(), 0);
    TestTrue(TEXT("Sequence one is delivered"),
        WriteCommand(Bridge, 1, TEXT("first_ping"), TEXT("ping")));
    TestEqual(TEXT("One pump drains consecutive one and two in order"),
        Bridge->PumpForTesting(), 2);
    TestEqual(TEXT("Order executes exactly once"), Flow->GetPanelBatches().Num(), 1);
    if (!Flow->GetPanelBatches().IsEmpty())
    {
        TestEqual(TEXT("Omitted automation model defaults to the Cairnwell 2040 programme"),
            Flow->GetPanelBatches()[0].VehicleModelId, FName(TEXT("CAIRNWELL_2040")));
    }

    TestTrue(TEXT("Identical command-id replay is delivered at next sequence"),
        WriteCommand(Bridge, 3, TEXT("order_once"), TEXT("queue_panel_batch"), OrderArgs));
    TestEqual(TEXT("Replay receives one terminal reply"), Bridge->PumpForTesting(), 1);
    TestEqual(TEXT("Replay does not queue a second order"), Flow->GetPanelBatches().Num(), 1);
    const TSharedPtr<FJsonObject> Replay = ReadReply(Bridge, 3, TEXT("order_once"));
    TestTrue(TEXT("Identical replay is acknowledged successfully"),
        Replay.IsValid() && Replay->GetBoolField(TEXT("ok")));
    if (Replay.IsValid())
        TestTrue(TEXT("Reply identifies replay"),
            Replay->GetObjectField(TEXT("result"))->GetBoolField(TEXT("replayed")));

    const TSharedRef<FJsonObject> ChangedArgs = MakeShared<FJsonObject>();
    ChangedArgs->SetStringField(TEXT("order_id"), TEXT("BRIDGE-ORDER-01"));
    ChangedArgs->SetStringField(TEXT("panel_type_id"), TEXT("DOOR_FRONT_LEFT"));
    ChangedArgs->SetNumberField(TEXT("quantity"), 24);
    TestTrue(TEXT("Changed command-id reuse is delivered"),
        WriteCommand(Bridge, 4, TEXT("order_once"), TEXT("queue_panel_batch"), ChangedArgs));
    TestEqual(TEXT("Changed reuse receives terminal reply"), Bridge->PumpForTesting(), 1);
    TestEqual(TEXT("Changed reuse has no side effect"), Flow->GetPanelBatches().Num(), 1);
    const TSharedPtr<FJsonObject> Reuse = ReadReply(Bridge, 4, TEXT("order_once"));
    TestTrue(TEXT("Changed reuse is rejected"), Reuse.IsValid() && !Reuse->GetBoolField(TEXT("ok")));
    if (Reuse.IsValid())
        TestEqual(TEXT("Changed reuse reports exact code"),
            Reuse->GetObjectField(TEXT("error"))->GetStringField(TEXT("code")), FString(TEXT("ID_REUSE")));

    CleanupBridgeRoot(Root);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBDeveloperAutomationBridgeBodyWeldContractTest,
    "LineBoss.AutomationBridge.Protocol.BodyWeldAliasesSnapshotAndCompositePlacementIdentity",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBDeveloperAutomationBridgeBodyWeldContractTest::RunTest(const FString& Parameters)
{
    TestEqual(TEXT("Body Weld has one canonical serialized machine name"),
        ALBDeveloperAutomationBridge::SerializeMachineType(
            ELBFactoryBuildMachineType::BodyWeldLine), FString(TEXT("body_weld_line")));
    const FString AcceptedNames[] = {TEXT("body_weld_line"), TEXT("weld_line")};
    for (const FString& Name : AcceptedNames)
    {
        ELBFactoryBuildMachineType Parsed = ELBFactoryBuildMachineType::InboundDeliveryDock;
        TestTrue(FString::Printf(TEXT("Bridge accepts documented Body Weld name %s"), *Name),
            ALBDeveloperAutomationBridge::TryParseMachineType(Name, Parsed));
        TestEqual(FString::Printf(TEXT("%s resolves to BodyWeldLine"), *Name),
            Parsed, ELBFactoryBuildMachineType::BodyWeldLine);
    }
    ELBFactoryBuildMachineType Rejected = ELBFactoryBuildMachineType::InboundDeliveryDock;
    TestFalse(TEXT("Undocumented broad weld alias remains rejected"),
        ALBDeveloperAutomationBridge::TryParseMachineType(TEXT("weld"), Rejected));

    FLBBridgeTestWorld Fixture(TEXT("LBBridgeBodyWeld"));
    FString Root;
    ALBDeveloperAutomationBridge* Bridge = SpawnTestBridge(Fixture.World, Root);
    ALBBodyWeldLineActor* Line = Fixture.World
        ? Fixture.World->SpawnActor<ALBBodyWeldLineActor>(
            FVector(1234.0f, -567.0f, 0.0f), FRotator::ZeroRotator) : nullptr;
    TestTrue(TEXT("Bridge snapshot fixture uses one stable Body Weld LineId"), Line
        && Line->Configure(TEXT("BODY-WELD-BRIDGE-01"))
        && Line->SetAssignedOrder(TEXT("ORDER-BODY-WELD-BRIDGE-01")));
    TestNotNull(TEXT("Bridge starts for Body Weld contract"), Bridge);
    if (!Bridge || !Line)
    {
        CleanupBridgeRoot(Root);
        return false;
    }

    TestTrue(TEXT("Aggregated Body Weld state command is written"),
        WriteCommand(Bridge, 1, TEXT("body_weld_state"), TEXT("get_state")));
    TestEqual(TEXT("Aggregated Body Weld state command completes"),
        Bridge->PumpForTesting(), 1);
    const TSharedPtr<FJsonObject> Reply = ReadReply(Bridge, 1, TEXT("body_weld_state"));
    TestTrue(TEXT("Body Weld state reply succeeds"),
        Reply.IsValid() && Reply->GetBoolField(TEXT("ok")));
    if (Reply.IsValid() && Reply->GetBoolField(TEXT("ok")))
    {
        const TSharedPtr<FJsonObject> Result = Reply->GetObjectField(TEXT("result"));
        const TArray<TSharedPtr<FJsonValue>>* Lines = nullptr;
        TestTrue(TEXT("Backward-compatible body_weld_lines array is present"),
            Result->TryGetArrayField(TEXT("body_weld_lines"), Lines) && Lines
            && Lines->Num() == 1);
        TestEqual(TEXT("Body Weld line count matches the array"),
            static_cast<int32>(Result->GetNumberField(TEXT("body_weld_line_count"))), 1);
        if (Lines && Lines->Num() == 1)
        {
            const TSharedPtr<FJsonObject> Item = (*Lines)[0]->AsObject();
            TestEqual(TEXT("Snapshot keys the composite line by stable LineId"),
                Item->GetStringField(TEXT("line_id")), FString(TEXT("BODY-WELD-BRIDGE-01")));
            TestEqual(TEXT("Snapshot retains assigned production order"),
                Item->GetStringField(TEXT("order_id")),
                FString(TEXT("ORDER-BODY-WELD-BRIDGE-01")));
            TestEqual(TEXT("Snapshot maps actual material-starved state"),
                Item->GetStringField(TEXT("state")), FString(TEXT("starved")));
            TestEqual(TEXT("Snapshot exposes exact authored phase"),
                Item->GetStringField(TEXT("phase")), FString(TEXT("awaiting_recipe")));
            TestTrue(TEXT("Snapshot exposes progress, inventory, output, rework and completion"),
                Item->HasField(TEXT("progress")) && Item->HasField(TEXT("inventory"))
                && Item->HasField(TEXT("output")) && Item->HasField(TEXT("rework"))
                && Item->HasField(TEXT("completed")) && Item->HasField(TEXT("location")));
            TestEqual(TEXT("Empty fixture reports no panels without fabrication"),
                static_cast<int32>(Item->GetObjectField(TEXT("inventory"))
                    ->GetNumberField(TEXT("available_panel_count"))), 0);
            TestFalse(TEXT("Empty fixture reports no output body"),
                Item->GetObjectField(TEXT("output"))->GetBoolField(TEXT("present")));
            TestFalse(TEXT("Empty fixture reports no rework body"),
                Item->GetObjectField(TEXT("rework"))->GetBoolField(TEXT("present")));
        }
    }

    // Remove the read-only snapshot fixture and prove the canonical placement command returns
    // the composite LineId. The predecessor is close enough to the weld intake but outside
    // the protected 60 x 30 m envelope.
    Line->Destroy();
    ALBFactoryBuildMachine* Outbound = Fixture.World->SpawnActor<ALBFactoryBuildMachine>(
        FVector(-1000.0f, -900.0f, 0.0f), FRotator::ZeroRotator);
    TestTrue(TEXT("Placement fixture has a real outbound stillage handoff"), Outbound
        && Outbound->Configure(TEXT("BRIDGE-WELD-OUTBOUND-01"),
            ELBFactoryBuildMachineType::OutboundPanelDock));
    ALBPressShopBuildAuthority* Authority =
        Fixture.World->SpawnActor<ALBPressShopBuildAuthority>();
    TestNotNull(TEXT("Placement fixture has one factory floor authority"), Authority);
    if (Authority)
    {
        FLBPressShopBuildBay Bay;
        Bay.BayId = TEXT("BRIDGE-BODY-WELD-BAY");
        Bay.Centre = FVector::ZeroVector;
        Bay.HalfExtent = FVector(25000.0f, 25000.0f, 2000.0f);
        Authority->BuildBays.Add(Bay);
        FLBPressShopUtilitySpine Spine;
        Spine.SpineId = TEXT("BRIDGE-BODY-WELD-UTILITY");
        Spine.Start = FVector(-25000.0f, 0.0f, 0.0f);
        Spine.End = FVector(25000.0f, 0.0f, 0.0f);
        Spine.MaximumConnectionDistanceCm = 10000.0f;
        Authority->UtilitySpines.Add(Spine);
    }
    const TSharedRef<FJsonObject> CanonicalArgs = MakeShared<FJsonObject>();
    CanonicalArgs->SetStringField(TEXT("machine_type"), TEXT("body_weld_line"));
    CanonicalArgs->SetNumberField(TEXT("x"), 0.0);
    CanonicalArgs->SetNumberField(TEXT("y"), 0.0);
    TestTrue(TEXT("Canonical Body Weld placement command is written"),
        WriteCommand(Bridge, 2, TEXT("place_body_weld"),
            TEXT("place_machine"), CanonicalArgs));
    TestEqual(TEXT("Canonical Body Weld placement receives a terminal reply"),
        Bridge->PumpForTesting(), 1);
    const TSharedPtr<FJsonObject> PlacementReply =
        ReadReply(Bridge, 2, TEXT("place_body_weld"));
    TestTrue(TEXT("Canonical Body Weld placement succeeds"),
        PlacementReply.IsValid() && PlacementReply->GetBoolField(TEXT("ok")));
    if (PlacementReply.IsValid() && PlacementReply->GetBoolField(TEXT("ok")))
    {
        const TSharedPtr<FJsonObject> Result = PlacementReply->GetObjectField(TEXT("result"));
        TestEqual(TEXT("Composite placement returns the canonical machine type"),
            Result->GetStringField(TEXT("machine_type")), FString(TEXT("body_weld_line")));
        TestEqual(TEXT("Composite placement returns the allocated stable LineId"),
            Result->GetStringField(TEXT("line_id")), FString(TEXT("WELD-LINE-01")));
    }

    // The alias is accepted by the parser and now reaches the duplicate-line placement guard.
    const TSharedRef<FJsonObject> AliasArgs = MakeShared<FJsonObject>();
    AliasArgs->SetStringField(TEXT("machine_type"), TEXT("weld_line"));
    AliasArgs->SetNumberField(TEXT("x"), 0.0);
    AliasArgs->SetNumberField(TEXT("y"), 0.0);
    TestTrue(TEXT("Body Weld compatibility alias command is written"),
        WriteCommand(Bridge, 3, TEXT("place_weld_alias"),
            TEXT("place_machine"), AliasArgs));
    TestEqual(TEXT("Body Weld alias receives a terminal reply"), Bridge->PumpForTesting(), 1);
    const TSharedPtr<FJsonObject> AliasReply =
        ReadReply(Bridge, 3, TEXT("place_weld_alias"));
    TestTrue(TEXT("Compatibility alias reaches the real duplicate-line guard"),
        AliasReply.IsValid() && !AliasReply->GetBoolField(TEXT("ok"))
        && AliasReply->GetObjectField(TEXT("error"))->GetStringField(TEXT("code"))
            == TEXT("PLACEMENT_REJECTED"));

    CleanupBridgeRoot(Root);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBDeveloperAutomationBridgeErrorsTest,
    "LineBoss.AutomationBridge.Protocol.ErrorsDoNotBlockQueue",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBDeveloperAutomationBridgeErrorsTest::RunTest(const FString& Parameters)
{
    FLBBridgeTestWorld Fixture(TEXT("LBBridgeErrors"));
    FString Root;
    ALBDeveloperAutomationBridge* Bridge = SpawnTestBridge(Fixture.World, Root);
    TestNotNull(TEXT("Bridge starts"), Bridge);
    if (!Bridge) return false;

    TestTrue(TEXT("Malformed command is delivered"),
        WriteRawReady(Bridge, 1, TEXT("bad_json"), TEXT("{\"protocol\":")));
    TestTrue(TEXT("Valid following command is delivered"),
        WriteCommand(Bridge, 2, TEXT("recovery_ping"), TEXT("ping")));
    TestEqual(TEXT("Malformed command does not block following sequence"),
        Bridge->PumpForTesting(), 2);
    const TSharedPtr<FJsonObject> Bad = ReadReply(Bridge, 1, TEXT("bad_json"));
    const TSharedPtr<FJsonObject> Good = ReadReply(Bridge, 2, TEXT("recovery_ping"));
    TestTrue(TEXT("Malformed command gets terminal failure"), Bad.IsValid() && !Bad->GetBoolField(TEXT("ok")));
    if (Bad.IsValid())
        TestEqual(TEXT("Malformed command has stable error code"),
            Bad->GetObjectField(TEXT("error"))->GetStringField(TEXT("code")), FString(TEXT("MALFORMED_JSON")));
    TestTrue(TEXT("Following valid command still succeeds"), Good.IsValid() && Good->GetBoolField(TEXT("ok")));

    CleanupBridgeRoot(Root);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBDeveloperAutomationBridgeCoreGameplayTest,
    "LineBoss.AutomationBridge.Commands.CoreGameplay",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBDeveloperAutomationBridgeCoreGameplayTest::RunTest(const FString& Parameters)
{
    FLBBridgeTestWorld Fixture(TEXT("LBBridgeCore"));
    FString Root;
    ALBDeveloperAutomationBridge* Bridge = SpawnTestBridge(Fixture.World, Root);
    ALBControlRoomHUD* HUD = Fixture.World ? Fixture.World->SpawnActor<ALBControlRoomHUD>() : nullptr;
    ALBManagementPawn* Pawn = Fixture.World ? Fixture.World->SpawnActor<ALBManagementPawn>() : nullptr;
    ALBPlayerBuiltPressFlowController* Flow = Fixture.World
        ? Fixture.World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    TestNotNull(TEXT("Bridge starts"), Bridge);
    TestNotNull(TEXT("HUD exists"), HUD);
    TestNotNull(TEXT("Management pawn exists"), Pawn);
    TestNotNull(TEXT("Flow authority exists"), Flow);
    if (!Bridge || !HUD || !Pawn || !Flow) return false;

    const TSharedRef<FJsonObject> MachineArgs = MakeShared<FJsonObject>();
    MachineArgs->SetStringField(TEXT("machine_type"), TEXT("inbound_delivery_dock"));
    MachineArgs->SetNumberField(TEXT("x"), 0);
    MachineArgs->SetNumberField(TEXT("y"), 0);
    const TSharedRef<FJsonObject> UIArgs = MakeShared<FJsonObject>();
    UIArgs->SetStringField(TEXT("page"), TEXT("production"));
    const TSharedRef<FJsonObject> CameraArgs = MakeShared<FJsonObject>();
    CameraArgs->SetNumberField(TEXT("x"), 1250);
    CameraArgs->SetNumberField(TEXT("y"), -750);
    CameraArgs->SetNumberField(TEXT("yaw_degrees"), -20);
    CameraArgs->SetNumberField(TEXT("zoom_cm"), 4200);
    const TSharedRef<FJsonObject> OrderArgs = MakeShared<FJsonObject>();
    OrderArgs->SetStringField(TEXT("order_id"), TEXT("DIRECT-PLAY-001"));
    OrderArgs->SetStringField(TEXT("vehicle_model_id"), TEXT("CAIRNWELL_2040"));
    OrderArgs->SetStringField(TEXT("panel_type_id"), TEXT("HOOD_PANEL"));
    OrderArgs->SetNumberField(TEXT("quantity"), 8);

    TestTrue(TEXT("Machine command written"), WriteCommand(Bridge, 1, TEXT("place_inbound"), TEXT("place_machine"), MachineArgs));
    TestTrue(TEXT("UI command written"), WriteCommand(Bridge, 2, TEXT("show_orders"), TEXT("open_ui"), UIArgs));
    TestTrue(TEXT("Camera command written"), WriteCommand(Bridge, 3, TEXT("camera_pose"), TEXT("set_camera"), CameraArgs));
    TestTrue(TEXT("Order command written"), WriteCommand(Bridge, 4, TEXT("panel_order"), TEXT("queue_panel_batch"), OrderArgs));
    TestEqual(TEXT("Four core commands complete in order"), Bridge->PumpForTesting(), 4);

    int32 InboundCount = 0;
    for (TActorIterator<ALBFactoryBuildMachine> It(Fixture.World); It; ++It)
        if (IsValid(*It) && It->GetMachineType() == ELBFactoryBuildMachineType::InboundDeliveryDock) ++InboundCount;
    TestEqual(TEXT("Direct command places one real inbound machine"), InboundCount, 1);
    TestTrue(TEXT("Direct command opens requested management page"),
        HUD->IsManagementVisible() && HUD->GetManagementPage() == ELBManagementPage::Production);
    TestTrue(TEXT("Direct command applies camera location"),
        Pawn->GetActorLocation().Equals(FVector(1250.0f, -750.0f, 0.0f), 0.1f));
    TestEqual(TEXT("Camera zoom remains exact inside gameplay limits"), Pawn->GetManagementZoomDistance(), 4200.0f);
    TestEqual(TEXT("Direct command queues one production order"), Flow->GetPanelBatches().Num(), 1);
    if (!Flow->GetPanelBatches().IsEmpty())
        TestEqual(TEXT("Direct order quantity is preserved"), Flow->GetPanelBatches()[0].RequestedQuantity, 8);

    TestTrue(TEXT("Focus command written after factory exists"),
        WriteCommand(Bridge, 5, TEXT("focus_factory"), TEXT("focus_factory")));
    TestEqual(TEXT("Focus command completes"), Bridge->PumpForTesting(), 1);
    const TSharedPtr<FJsonObject> FocusReply = ReadReply(Bridge, 5, TEXT("focus_factory"));
    TestTrue(TEXT("Focus succeeds on the built factory"),
        FocusReply.IsValid() && FocusReply->GetBoolField(TEXT("ok")));

    const TSharedRef<FJsonObject> UnsafeScreenshot = MakeShared<FJsonObject>();
    UnsafeScreenshot->SetStringField(TEXT("name"), TEXT("../escape"));
    TestTrue(TEXT("Unsafe screenshot command written"),
        WriteCommand(Bridge, 6, TEXT("unsafe_shot"), TEXT("capture_screenshot"), UnsafeScreenshot));
    TestEqual(TEXT("Unsafe screenshot receives terminal response"), Bridge->PumpForTesting(), 1);
    const TSharedPtr<FJsonObject> UnsafeReply = ReadReply(Bridge, 6, TEXT("unsafe_shot"));
    TestTrue(TEXT("Path traversal is rejected"),
        UnsafeReply.IsValid() && !UnsafeReply->GetBoolField(TEXT("ok")));

    CleanupBridgeRoot(Root);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBDeveloperAutomationBridgeUISelectionAndAlertFocusTest,
    "LineBoss.AutomationBridge.Commands.UISelectionAndAlertFocus",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBDeveloperAutomationBridgeUISelectionAndAlertFocusTest::RunTest(
    const FString& Parameters)
{
    FLBBridgeTestWorld Fixture(TEXT("LBBridgeUISelection"));
    FString Root;
    ALBDeveloperAutomationBridge* Bridge = SpawnTestBridge(Fixture.World, Root);
    ALBManagementPawn* Pawn = Fixture.World
        ? Fixture.World->SpawnActor<ALBManagementPawn>() : nullptr;
    ALBPlayerBuiltPressFlowController* Flow = Fixture.World
        ? Fixture.World->SpawnActor<ALBPlayerBuiltPressFlowController>() : nullptr;
    ALBFactoryBuildMachine* Faulted = Fixture.World
        ? Fixture.World->SpawnActor<ALBFactoryBuildMachine>(
            FVector(2500.0f, 750.0f, 100.0f), FRotator::ZeroRotator) : nullptr;
    TestNotNull(TEXT("Bridge starts for UI selection test"), Bridge);
    TestNotNull(TEXT("Management pawn exists for UI selection test"), Pawn);
    TestNotNull(TEXT("Flow authority exists for UI selection test"), Flow);
    TestNotNull(TEXT("Faulted machine exists for UI selection test"), Faulted);
    if (!Bridge || !Pawn || !Flow || !Faulted) return false;

    FLBPlayerBuiltPressFlowSaveState FlowSave;
    FLBVehiclePanelBatch Batch;
    Batch.OrderId = TEXT("BRIDGE-UI-ORDER");
    Batch.VehicleModelId = TEXT("CAIRNWELL_2040");
    Batch.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
    Batch.RequestedQuantity = 12;
    Batch.DispatchedQuantity = 3;
    FlowSave.PanelBatches.Add(Batch);
    TestTrue(TEXT("Bridge UI fixture restores truthful issued progress"),
        Flow->RestoreSaveState(FlowSave));

    FLBFactoryBuildMachineSaveState MachineSave;
    MachineSave.MachineId = TEXT("BRIDGE-FAULT-001");
    MachineSave.MachineType = ELBFactoryBuildMachineType::InspectionCell;
    MachineSave.WorldTransform = FTransform(FRotator::ZeroRotator,
        FVector(2500.0f, 750.0f, 100.0f));
    MachineSave.OperatingState = ELBFactoryMachineOperatingState::Fault;
    MachineSave.OperatingReason = TEXT("VISION SENSOR LOST");
    TestTrue(TEXT("Bridge UI fixture restores an actionable fault"),
        Faulted->RestoreSaveState(MachineSave));

    const TSharedRef<FJsonObject> SelectArgs = MakeShared<FJsonObject>();
    SelectArgs->SetStringField(TEXT("kind"), TEXT("machine"));
    SelectArgs->SetStringField(TEXT("id"), TEXT("BRIDGE-FAULT-001"));
    SelectArgs->SetBoolField(TEXT("focus"), false);
    TestTrue(TEXT("Factory selection command written"),
        WriteCommand(Bridge, 1, TEXT("select_fault"),
            TEXT("select_factory_actor"), SelectArgs));
    TestTrue(TEXT("Aggregated state command written"),
        WriteCommand(Bridge, 2, TEXT("read_ui_state"), TEXT("get_state")));
    TestTrue(TEXT("Alert jump command written"),
        WriteCommand(Bridge, 3, TEXT("jump_fault"), TEXT("jump_to_alert")));
    TestEqual(TEXT("Selection, state and alert focus complete in order"),
        Bridge->PumpForTesting(), 3);

    TestTrue(TEXT("Bridge selection uses the same pawn selection authority"),
        Pawn->GetInspectedFactoryActor() == Faulted);
    const TSharedPtr<FJsonObject> SelectReply =
        ReadReply(Bridge, 1, TEXT("select_fault"));
    TestTrue(TEXT("Factory selection command succeeds"),
        SelectReply.IsValid() && SelectReply->GetBoolField(TEXT("ok")));

    const TSharedPtr<FJsonObject> StateReply =
        ReadReply(Bridge, 2, TEXT("read_ui_state"));
    TestTrue(TEXT("Aggregated UI state command succeeds"),
        StateReply.IsValid() && StateReply->GetBoolField(TEXT("ok")));
    if (StateReply.IsValid() && StateReply->GetBoolField(TEXT("ok")))
    {
        const TSharedPtr<FJsonObject> Result =
            StateReply->GetObjectField(TEXT("result"));
        const TSharedPtr<FJsonObject> Operations =
            Result->GetObjectField(TEXT("operations"));
        TestEqual(TEXT("Bridge reports issued production progress"),
            static_cast<int32>(FMath::RoundToInt(
                Operations->GetNumberField(TEXT("issued_quantity")))), 3);
        TestEqual(TEXT("Bridge reports requested production progress"),
            static_cast<int32>(FMath::RoundToInt(
                Operations->GetNumberField(TEXT("requested_quantity")))), 12);
        TestEqual(TEXT("Bridge reports the deterministic top alert"),
            Operations->GetObjectField(TEXT("top_alert"))->GetStringField(TEXT("entity_id")),
            FString(TEXT("BRIDGE-FAULT-001")));
        TestEqual(TEXT("Bridge reports the selected actor through get_state"),
            Result->GetObjectField(TEXT("ui"))
                ->GetObjectField(TEXT("selected_actor"))
                ->GetStringField(TEXT("entity_id")),
            FString(TEXT("BRIDGE-FAULT-001")));
    }

    const TSharedPtr<FJsonObject> JumpReply =
        ReadReply(Bridge, 3, TEXT("jump_fault"));
    TestTrue(TEXT("Alert jump command succeeds"),
        JumpReply.IsValid() && JumpReply->GetBoolField(TEXT("ok")));
    if (JumpReply.IsValid() && JumpReply->GetBoolField(TEXT("ok")))
    {
        TestEqual(TEXT("Alert jump identifies the focused fault"),
            JumpReply->GetObjectField(TEXT("result"))->GetStringField(TEXT("entity_id")),
            FString(TEXT("BRIDGE-FAULT-001")));
    }

    CleanupBridgeRoot(Root);
    return true;
}

#endif
