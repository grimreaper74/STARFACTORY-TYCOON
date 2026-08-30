#include "LBFactoryConnectionSubsystem.h"
#include "LBFactoryProcessPortComponent.h"
#include "LBFactoryTransportLink.h"
#include "LBFactoryBuildMachine.h"
#include "LBPressShopSaveGame.h"
#include "LBPressShopStorageZone.h"
#include "LBPressTrainAStation.h"
#include "Components/SceneComponent.h"
#include "Components/SplineComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Kismet/GameplayStatics.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryAutomaticConnectionTest,
    "LineBoss.FactoryBuilder.Transport.AutomaticNextStageConnection",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFourPressTrainSharedFlowTest,
    "LineBoss.FactoryBuilder.Transport.FourPressTrainsPhysicalBranchedFlow",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryTransactionalDisconnectTest,
    "LineBoss.FactoryBuilder.Transport.TransactionalDisconnectAndIdempotence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

namespace
{
ULBFactoryProcessPortComponent* AddPort(AActor* Owner, const TCHAR* Name,
    ELBFactoryPortDirection Direction, int32 Stage, const FVector& Location)
{
    ULBFactoryProcessPortComponent* Port = NewObject<ULBFactoryProcessPortComponent>(Owner, Name);
    Port->Direction = Direction;
    Port->ProcessStage = Stage;
    Port->PortId = FName(Name);
    Port->TransportKind = ELBFactoryTransportKind::RollerConveyor;
    Port->MaterialClass = ELBFactoryMaterialClass::FormedPanel;
    Port->MaximumAutomaticLinkDistanceCm = 2000.0f;
    Owner->AddInstanceComponent(Port);
    Port->RegisterComponent();
    Port->SetWorldLocation(Location);
    return Port;
}
}

bool FLBFactoryTransactionalDisconnectTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LB_TransactionalDisconnect"));
    ULBFactoryConnectionSubsystem* Connections = World
        ? NewObject<ULBFactoryConnectionSubsystem>(World) : nullptr;
    AActor* SourceActor = World ? World->SpawnActor<AActor>() : nullptr;
    AActor* TargetActor = World ? World->SpawnActor<AActor>() : nullptr;
    TestTrue(TEXT("Transactional disconnect fixture exists"),
        World && Connections && SourceActor && TargetActor);
    if (!World || !Connections || !SourceActor || !TargetActor)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    ULBFactoryProcessPortComponent* Source = AddPort(SourceActor, TEXT("TX-SOURCE-OUT"),
        ELBFactoryPortDirection::Output, 20, FVector(0.0f, 0.0f, 100.0f));
    ULBFactoryProcessPortComponent* Target = AddPort(TargetActor, TEXT("TX-TARGET-IN"),
        ELBFactoryPortDirection::Input, 21, FVector(600.0f, 0.0f, 100.0f));
    ALBFactoryTransportLink* Link = nullptr;
    FString Reason;
    TestTrue(TEXT("Exact transactional fixture link connects"),
        Connections->Connect(Source, Target, Link, Reason));
    TestTrue(TEXT("Transactional fixture retains its transfer counter"),
        Link && Link->TryTransferUnits(3));
    TArray<FLBFactoryTransportLinkSaveState> Before;
    TestTrue(TEXT("Connected inventory captures before disconnect"),
        Connections->CaptureConnections(Before));
    TestEqual(TEXT("One exact link exists before disconnect"), Before.Num(), 1);
    TestEqual(TEXT("Transfer counter is captured before disconnect"),
        Before.Num() == 1 ? Before[0].TransferredUnits : -1, 3);

    TestTrue(TEXT("DisconnectActor removes every touching link"),
        Connections->DisconnectActor(TargetActor, Reason));
    TestEqual(TEXT("Source connected-port cache is cleared"),
        Source->GetConnectedPortCacheCount(), 0);
    TestEqual(TEXT("Source link cache is cleared"), Source->GetTransportLinkCacheCount(), 0);
    TestEqual(TEXT("Target connected-port cache is cleared"),
        Target->GetConnectedPortCacheCount(), 0);
    TestEqual(TEXT("Target link cache is cleared"), Target->GetTransportLinkCacheCount(), 0);
    TArray<FLBFactoryTransportLinkSaveState> AfterActorDisconnect;
    TestTrue(TEXT("World link inventory captures after actor disconnect"),
        Connections->CaptureConnections(AfterActorDisconnect));
    TestEqual(TEXT("Actor disconnect removes the world link inventory"),
        AfterActorDisconnect.Num(), 0);
    TestTrue(TEXT("Repeated actor disconnect is idempotent"),
        Connections->DisconnectActor(TargetActor, Reason));

    ALBFactoryTransportLink* SecondLink = nullptr;
    TestTrue(TEXT("Ports reconnect after complete cache cleanup"),
        Connections->Connect(Source, Target, SecondLink, Reason));
    Source->ClearConnection();
    TestTrue(TEXT("Legacy half-cache fixture retains only the remote side"),
        !Source->IsConnected() && Target->IsConnected());
    TestTrue(TEXT("Actor disconnect repairs a remote-only half-cache and its link inventory"),
        Connections->DisconnectActor(SourceActor, Reason));
    TestFalse(TEXT("Remote-only half-cache is cleared"), Target->IsConnected());

    ALBFactoryTransportLink* ThirdLink = nullptr;
    TestTrue(TEXT("Ports reconnect after half-cache repair"),
        Connections->Connect(Source, Target, ThirdLink, Reason));
    TestTrue(TEXT("Direct disconnect clears both endpoint caches"),
        Connections->Disconnect(ThirdLink, Reason));
    TestTrue(TEXT("Repeated direct disconnect is idempotent"),
        Connections->Disconnect(ThirdLink, Reason));
    TestFalse(TEXT("Neither port retains a half-connection"),
        Source->IsConnected() || Target->IsConnected());

    World->DestroyWorld(false);
    return true;
}

bool FLBFactoryAutomaticConnectionTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_AutoTransport"));
    ULBFactoryConnectionSubsystem* Connections = World
        ? NewObject<ULBFactoryConnectionSubsystem>(World) : nullptr;
    AActor* StageOne = World ? World->SpawnActor<AActor>() : nullptr;
    AActor* StageTwo = World ? World->SpawnActor<AActor>() : nullptr;
    TestNotNull(TEXT("Connection authority exists"), Connections);
    TestNotNull(TEXT("Predecessor machine exists"), StageOne);
    TestNotNull(TEXT("New machine exists"), StageTwo);
    if (!Connections || !StageOne || !StageTwo)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    ULBFactoryProcessPortComponent* Output = AddPort(StageOne, TEXT("S01_OUT"),
        ELBFactoryPortDirection::Output, 1, FVector(0.0f, 0.0f, 100.0f));
    Output->MaximumConnections = 2;
    ULBFactoryProcessPortComponent* Input = AddPort(StageTwo, TEXT("S02_IN"),
        ELBFactoryPortDirection::Input, 2, FVector(900.0f, 600.0f, 100.0f));

    FString Reason;
    TestTrue(TEXT("Exact next-stage compatible ports pass"), Connections->CanConnect(Output, Input, Reason));
    TestFalse(TEXT("Reverse connection is rejected"), Connections->CanConnect(Input, Output, Reason));
    Input->ProcessStage = 3;
    TestFalse(TEXT("Skipping a required process stage is rejected"), Connections->CanConnect(Output, Input, Reason));
    Input->ProcessStage = 2;
    Input->MaterialClass = ELBFactoryMaterialClass::Scrap;
    TestFalse(TEXT("Wrong material route is rejected"), Connections->CanConnect(Output, Input, Reason));
    Input->MaterialClass = ELBFactoryMaterialClass::FormedPanel;
    Input->MaximumAutomaticLinkDistanceCm = 100.0f;
    TestFalse(TEXT("Out-of-range automatic route is rejected"), Connections->CanConnect(Output, Input, Reason));
    Input->MaximumAutomaticLinkDistanceCm = 2000.0f;

    TArray<ALBFactoryTransportLink*> Links;
    TestTrue(TEXT("New machine automatically connects to nearest valid predecessor"),
        Connections->AutoConnectNewMachine(StageTwo, Links, Reason));
    TestEqual(TEXT("One transport link is generated"), Links.Num(), 1);
    TestTrue(TEXT("Both authored process ports become connected"), Output->IsConnected() && Input->IsConnected());
    TestTrue(TEXT("Generated route contains a dogleg path"),
        Links.Num() == 1 && Links[0] && Links[0]->RouteSpline->GetNumberOfSplinePoints() == 3);
    TestTrue(TEXT("Generated route builds visible side rails"),
        Links.Num() == 1 && Links[0] && Links[0]->SideRails->GetInstanceCount() >= 4);
    TestTrue(TEXT("Generated route builds visible rollers"),
        Links.Num() == 1 && Links[0] && Links[0]->RollerOrBeltDeck->GetInstanceCount() >= 4);
    TestTrue(TEXT("Generated route builds floor supports"),
        Links.Num() == 1 && Links[0] && Links[0]->SupportLegs->GetInstanceCount() >= 4);
    TestTrue(TEXT("Functional route records transferred production units"),
        Links.Num() == 1 && Links[0] && Links[0]->TryTransferUnits(4));
    TestEqual(TEXT("Transferred production quantity is retained"),
        Links.Num() == 1 && Links[0] ? Links[0]->GetTransferredUnits() : -1, 4);

    AActor* ParallelStageTwo = World->SpawnActor<AActor>();
    ULBFactoryProcessPortComponent* ParallelInput = AddPort(ParallelStageTwo, TEXT("S02B_IN"),
        ELBFactoryPortDirection::Input, 2, FVector(1100.0f, -500.0f, 100.0f));
    TArray<ALBFactoryTransportLink*> ParallelLinks;
    TestTrue(TEXT("Authored distributor output feeds a second parallel next-stage machine"),
        Connections->AutoConnectNewMachine(ParallelStageTwo, ParallelLinks, Reason));
    TestEqual(TEXT("Parallel machine receives one independent route"), ParallelLinks.Num(), 1);
    TestFalse(TEXT("Distributor output reaches its authored two-route capacity"), Output->HasAvailableConnection());
    TestTrue(TEXT("Parallel machine input is connected"), ParallelInput->IsConnected());

    ULBFactoryProcessPortComponent* StageTwoOutput = AddPort(StageTwo, TEXT("S02_OUT"),
        ELBFactoryPortDirection::Output, 2, FVector(900.0f, 700.0f, 100.0f));
    ULBFactoryProcessPortComponent* ParallelOutput = AddPort(ParallelStageTwo, TEXT("S02B_OUT"),
        ELBFactoryPortDirection::Output, 2, FVector(1100.0f, -400.0f, 100.0f));
    AActor* SharedAggregator = World->SpawnActor<AActor>();
    ULBFactoryProcessPortComponent* AggregatorInput = AddPort(SharedAggregator, TEXT("S03_SHARED_IN"),
        ELBFactoryPortDirection::Input, 3, FVector(1500.0f, 100.0f, 100.0f));
    AggregatorInput->MaximumConnections = 3;
    TArray<ALBFactoryTransportLink*> AggregatorLinks;
    TestTrue(TEXT("New shared buffer automatically collects every compatible parallel source"),
        Connections->AutoConnectNewMachine(SharedAggregator, AggregatorLinks, Reason));
    TestEqual(TEXT("Two existing parallel machines merge into the shared buffer"), AggregatorLinks.Num(), 2);
    TestTrue(TEXT("Shared input records both upstream identities"),
        AggregatorInput->IsConnectedTo(StageTwoOutput)
        && AggregatorInput->IsConnectedTo(ParallelOutput));

    // Add capacity after the shared downstream cell already exists. The new machine must
    // connect backward to its predecessor and forward into the existing aggregator.
    Output->MaximumConnections = 3;
    AActor* LateParallelStageTwo = World->SpawnActor<AActor>();
    ULBFactoryProcessPortComponent* LateInput = AddPort(LateParallelStageTwo, TEXT("S02C_IN"),
        ELBFactoryPortDirection::Input, 2, FVector(500.0f, -700.0f, 100.0f));
    ULBFactoryProcessPortComponent* LateOutput = AddPort(LateParallelStageTwo, TEXT("S02C_OUT"),
        ELBFactoryPortDirection::Output, 2, FVector(700.0f, -700.0f, 100.0f));
    TArray<ALBFactoryTransportLink*> LateLinks;
    TestTrue(TEXT("Late parallel machine joins both sides of the live process graph"),
        Connections->AutoConnectNewMachine(LateParallelStageTwo, LateLinks, Reason));
    TestEqual(TEXT("Late capacity creates predecessor and downstream links"), LateLinks.Num(), 2);
    TestTrue(TEXT("Late input joins the distributor"), LateInput->IsConnectedTo(Output));
    TestTrue(TEXT("Late output merges into the shared downstream buffer"),
        LateOutput->IsConnectedTo(AggregatorInput));

    TArray<FLBFactoryTransportLinkSaveState> SavedLinks;
    TestTrue(TEXT("Automatic routes capture to stable port identities"),
        Connections->CaptureConnections(SavedLinks));
    TestEqual(TEXT("Fan-out, fan-in and late-capacity routes are captured"), SavedLinks.Num(), 6);
    TestTrue(TEXT("Captured route quantity is retained in one connection record"),
        SavedLinks.ContainsByPredicate([](const FLBFactoryTransportLinkSaveState& State)
        { return State.TransferredUnits == 4; }));
    TestTrue(TEXT("Exact automatic route set restores"),
        Connections->RestoreConnections(SavedLinks, Reason));
    TArray<FLBFactoryTransportLinkSaveState> RoundTripLinks;
    TestTrue(TEXT("Restored routes recapture"), Connections->CaptureConnections(RoundTripLinks));
    TestEqual(TEXT("Round-trip route count is stable"), RoundTripLinks.Num(), SavedLinks.Num());
    ULBPressShopSaveGame* SaveRoot = NewObject<ULBPressShopSaveGame>();
    SaveRoot->FactoryTransportLinks = RoundTripLinks;
    TArray<uint8> SaveBytes;
    TestTrue(TEXT("Transport topology serializes in the campaign root"),
        UGameplayStatics::SaveGameToMemory(SaveRoot, SaveBytes));
    const ULBPressShopSaveGame* LoadedRoot = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromMemory(SaveBytes));
    TestEqual(TEXT("Campaign round trip preserves the complete branched graph"),
        LoadedRoot ? LoadedRoot->FactoryTransportLinks.Num() : -1, 6);

    // Heavy coils move by AGV. The logical connection remains in the process graph, but its
    // presentation must be floor paint only--never the roller-bed fallback used by old builds.
    AActor* AGVSourceActor = World->SpawnActor<AActor>();
    AActor* AGVTargetActor = World->SpawnActor<AActor>();
    ULBFactoryProcessPortComponent* AGVOutput = AddPort(AGVSourceActor, TEXT("AGV_SOURCE_OUT"),
        ELBFactoryPortDirection::Output, 10, FVector(0.0f, 2500.0f, 120.0f));
    ULBFactoryProcessPortComponent* AGVInput = AddPort(AGVTargetActor, TEXT("AGV_TARGET_IN"),
        ELBFactoryPortDirection::Input, 11, FVector(1200.0f, 3100.0f, 120.0f));
    AGVOutput->TransportKind = AGVInput->TransportKind = ELBFactoryTransportKind::AGVHandoff;
    AGVOutput->MaterialClass = AGVInput->MaterialClass = ELBFactoryMaterialClass::Coil;
    ALBFactoryTransportLink* AGVLink = World->SpawnActor<ALBFactoryTransportLink>();
    TestTrue(TEXT("AGV logical handoff configures"), AGVLink && AGVLink->Configure(AGVOutput, AGVInput));
    TestEqual(TEXT("AGV dogleg draws one painted line per straight leg"),
        AGVLink ? AGVLink->SideRails->GetInstanceCount() : -1, 2);
    TestEqual(TEXT("AGV handoff creates no roller bed"),
        AGVLink ? AGVLink->RollerOrBeltDeck->GetInstanceCount() : -1, 0);
    TestEqual(TEXT("AGV handoff creates no conveyor support legs"),
        AGVLink ? AGVLink->SupportLegs->GetInstanceCount() : -1, 0);

    World->DestroyWorld(false);
    return true;
}

bool FLBFourPressTrainSharedFlowTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_FourTrainPhysicalBranchedFlow"));
    ULBFactoryConnectionSubsystem* Connections = World
        ? NewObject<ULBFactoryConnectionSubsystem>(World) : nullptr;
    TestNotNull(TEXT("Four-train connection authority exists"), Connections);
    if (!World || !Connections)
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    // Two preparation packages feed four local blank buffers. This preserves the accepted
    // 22 m pitch between the wider train envelopes instead of drawing implausible 33 m
    // conveyors from one central port across the service aisles.
    TArray<ALBFactoryBuildMachine*> PrepLines;
    for (int32 Index = 0; Index < 2; ++Index)
    {
        ALBFactoryBuildMachine* Prep = World->SpawnActor<ALBFactoryBuildMachine>(
            ALBFactoryBuildMachine::StaticClass(),
            FTransform(FVector(Index == 0 ? -2200.0f : 2200.0f, -4800.0f, 0.0f)));
        TestTrue(FString::Printf(TEXT("Preparation branch %d configures"), Index + 1), Prep
            && Prep->Configure(FName(*FString::Printf(TEXT("COIL-PREP-%03d"), Index + 1)),
                ELBFactoryBuildMachineType::DecoilerFeeder));
        if (Prep) PrepLines.Add(Prep);
    }

    const float TrainX[] = {-3300.0f, -1100.0f, 1100.0f, 3300.0f};
    TArray<ALBPressShopStorageZone*> BlankBuffers;
    FString Reason;
    for (int32 Index = 0; Index < 4; ++Index)
    {
        ALBPressShopStorageZone* Buffer = World->SpawnActor<ALBPressShopStorageZone>(
            ALBPressShopStorageZone::StaticClass(),
            FTransform(FVector(TrainX[Index], -2900.0f, 0.0f)));
        TestTrue(FString::Printf(TEXT("Local blank buffer %c configures"), TCHAR('A' + Index)),
            Buffer && Buffer->Configure(FName(*FString::Printf(TEXT("SZ-BLANK-%c"), TCHAR('A' + Index))),
                ELBPressShopStorageType::PreparedBlanks, 8, FVector(300.0f)));
        TArray<ALBFactoryTransportLink*> BufferLinks;
        TestTrue(FString::Printf(TEXT("Local blank buffer %c joins its nearby preparation branch"),
            TCHAR('A' + Index)), Buffer
            && Connections->AutoConnectNewMachine(Buffer, BufferLinks, Reason));
        TestEqual(FString::Printf(TEXT("Local blank buffer %c has one short preparation feed"),
            TCHAR('A' + Index)), BufferLinks.Num(), 1);
        if (Buffer) BlankBuffers.Add(Buffer);
    }

    TArray<ALBPressTrainAStation*> Trains;
    const TCHAR* TrainNames[] = {TEXT("TRAIN_A"), TEXT("TRAIN_B"), TEXT("TRAIN_C"), TEXT("TRAIN_D")};
    for (int32 Index = 0; Index < 4; ++Index)
    {
        ALBPressTrainAStation* Train = World->SpawnActor<ALBPressTrainAStation>(
            ALBPressTrainAStation::StaticClass(), FTransform(FVector(TrainX[Index], -2000.0f, 0.0f)));
        TestNotNull(FString::Printf(TEXT("Press Train %c spawns"), TCHAR('A' + Index)), Train);
        if (!Train) continue;
        Train->FactoryInputPort->PortId = FName(*FString::Printf(TEXT("%s-IN"), TrainNames[Index]));
        Train->FactoryOutputPort->PortId = FName(*FString::Printf(TEXT("%s-OUT"), TrainNames[Index]));
        TArray<ALBFactoryTransportLink*> CreatedLinks;
        TestTrue(FString::Printf(TEXT("Press Train %c automatically joins its local blank buffer"),
            TCHAR('A' + Index)), Connections->AutoConnectNewMachine(Train, CreatedLinks, Reason));
        TestEqual(FString::Printf(TEXT("Press Train %c creates one short blank-feed route"),
            TCHAR('A' + Index)), CreatedLinks.Num(), 1);
        Trains.Add(Train);
    }

    // One common inspection package per train pair keeps every formed-panel transfer
    // inside the authored 25 m connection limit and clear of the adjacent train aisle.
    TArray<ALBFactoryBuildMachine*> Inspections;
    for (int32 Index = 0; Index < 2; ++Index)
    {
        ALBFactoryBuildMachine* Inspection = World->SpawnActor<ALBFactoryBuildMachine>(
            ALBFactoryBuildMachine::StaticClass(),
            FTransform(FVector(Index == 0 ? -2200.0f : 2200.0f, 5284.0f, 0.0f)));
        TestTrue(FString::Printf(TEXT("Inspection branch %d configures"), Index + 1), Inspection
            && Inspection->Configure(FName(*FString::Printf(TEXT("INSPECT-%03d"), Index + 1)),
                ELBFactoryBuildMachineType::InspectionCell));
        TArray<ALBFactoryTransportLink*> InspectionLinks;
        TestTrue(FString::Printf(TEXT("Inspection branch %d collects its two nearby train outputs"),
            Index + 1), Inspection
            && Connections->AutoConnectNewMachine(Inspection, InspectionLinks, Reason));
        TestEqual(FString::Printf(TEXT("Inspection branch %d has exactly two short panel routes"),
            Index + 1), InspectionLinks.Num(), 2);
        if (Inspection) Inspections.Add(Inspection);
    }

    for (int32 Index = 0; Index < Trains.Num(); ++Index)
    {
        ALBPressTrainAStation* Train = Trains[Index];
        TestTrue(FString::Printf(TEXT("Press Train %c has both required live routes"),
            TCHAR('A' + Index)), Train
            && BlankBuffers.IsValidIndex(Index)
            && Inspections.IsValidIndex(Index / 2)
            && Train->FactoryInputPort->IsConnectedTo(BlankBuffers[Index]->EgressPoint)
            && Train->FactoryOutputPort->IsConnectedTo(Inspections[Index / 2]->InputPort));
        if (Index > 0 && Train && Trains[Index - 1])
        {
            const FBox PreviousEnvelope = ALBPressTrainAStation::GetProtectedLocalEnvelope()
                .TransformBy(Trains[Index - 1]->GetActorTransform());
            const FBox ThisEnvelope = ALBPressTrainAStation::GetProtectedLocalEnvelope()
                .TransformBy(Train->GetActorTransform());
            TestFalse(FString::Printf(TEXT("Press Train %c retains a physical service aisle from Train %c"),
                TCHAR('A' + Index), TCHAR('A' + Index - 1)), PreviousEnvelope.Intersect(ThisEnvelope));
            TestTrue(FString::Printf(TEXT("Press Train %c uses the accepted 22 m row pitch"),
                TCHAR('A' + Index)), FMath::IsNearlyEqual(
                    Train->GetActorLocation().X - Trains[Index - 1]->GetActorLocation().X, 2200.0f, 0.01f));
        }
    }

    TArray<FLBFactoryTransportLinkSaveState> PhysicalLinks;
    TestTrue(TEXT("The full physically spaced A-D branch graph captures"),
        Connections->CaptureConnections(PhysicalLinks));
    TestEqual(TEXT("The physical graph contains four prep, four blank and four panel routes"),
        PhysicalLinks.Num(), 12);

    World->DestroyWorld(false);
    return true;
}

#endif
