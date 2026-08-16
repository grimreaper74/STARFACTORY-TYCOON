#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/BoxComponent.h"
#include "LBBodyWeldLineActor.h"
#include "LBECoatLineActor.h"
#include "LBManagementPawn.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressTrainAStation.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPlacementPreviewPresentationContractTest,
    "LineBoss.Management.PlacementPreview.StatusGeometryAndActionableReasons",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlacementPreviewPresentationContractTest::RunTest(const FString& Parameters)
{
    const FLBPlacementPreviewStyle Waiting = ALBManagementPawn::BuildPlacementPreviewStyle(
        false, false, TEXT("NO FACTORY FLOOR UNDER CURSOR"));
    TestTrue(TEXT("No surface has a distinct amber waiting state"),
        Waiting.State == ELBPlacementPreviewState::WaitingForSurface
        && Waiting.FootprintColour.R > Waiting.FootprintColour.G
        && Waiting.FootprintColour.G > Waiting.FootprintColour.B
        && Waiting.StateMarker.Contains(TEXT("[WAIT]"))
        && Waiting.NextAction.Contains(TEXT("AUTHORISED FACTORY FLOOR")));

    const FLBPlacementPreviewStyle Ready = ALBManagementPawn::BuildPlacementPreviewStyle(
        true, true, TEXT("TRAIN ENVELOPE CLEAR; UTILITY IN REACH"));
    TestTrue(TEXT("Valid placement has a green state and a non-colour OK marker"),
        Ready.IsPlacementAllowed()
        && Ready.State == ELBPlacementPreviewState::Ready
        && Ready.FootprintColour.G > Ready.FootprintColour.R
        && Ready.StateMarker.Contains(TEXT("[OK]"))
        && Ready.NextAction.Contains(TEXT("CONFIRM")));

    const FString BlockReason = TEXT("PROTECTED AREA PEDESTRIAN_AISLE MUST REMAIN CLEAR");
    const FLBPlacementPreviewStyle Blocked = ALBManagementPawn::BuildPlacementPreviewStyle(
        true, false, BlockReason);
    TestTrue(TEXT("Invalid placement has a red state and a non-colour blocked marker"),
        !Blocked.IsPlacementAllowed()
        && Blocked.State == ELBPlacementPreviewState::Blocked
        && Blocked.FootprintColour.R > Blocked.FootprintColour.G
        && Blocked.StateMarker.Contains(TEXT("[X]")));
    TestEqual(TEXT("Preview retains the exact authoritative reason"),
        Blocked.AuthorityReason, BlockReason);
    TestTrue(TEXT("Protected-area rejection gives a corrective action"),
        Blocked.NextAction.Contains(TEXT("MOVE OR ROTATE")));
    const FLBPlacementPreviewStyle Recovered = ALBManagementPawn::BuildPlacementPreviewStyle(
        true, true, TEXT("TRAIN ENVELOPE CLEAR; UTILITY IN REACH"));
    TestTrue(TEXT("A clear current-frame authority result replaces the prior blocked state"),
        Recovered.State == ELBPlacementPreviewState::Ready
        && Recovered.IsPlacementAllowed()
        && Recovered.StateMarker.Contains(TEXT("[OK]"))
        && !Recovered.StateMarker.Contains(TEXT("[X]"))
        && !Recovered.NextAction.Contains(TEXT("PEDESTRIAN_AISLE")));

    const FTransform PreviewTransform(FRotator(0.0f, 90.0f, 0.0f),
        FVector(100.0f, 200.0f, 50.0f), FVector::OneVector);
    const FVector RelativeCentre(0.0f, 300.0f, 100.0f);
    const FVector HalfExtent(200.0f, 500.0f, 100.0f);
    const FLBPlacementPreviewGeometry Geometry = ALBManagementPawn::BuildPlacementPreviewGeometry(
        PreviewTransform, RelativeCentre, HalfExtent, 25.0f, false, true);
    TestTrue(TEXT("Protected envelope centre follows the complete rotated placement transform"),
        Geometry.EnvelopeCentre.Equals(PreviewTransform.TransformPosition(RelativeCentre), 0.01f));
    TestTrue(TEXT("Ground footprint preserves full envelope X/Y and a thin floor fill"),
        Geometry.GroundHalfExtent.Equals(FVector(200.0f, 500.0f, 2.0f), 0.01f)
        && FMath::IsNearlyEqual(Geometry.GroundCentre.Z, 27.0f, 0.01f));
    TestTrue(TEXT("Input socket is on the local negative-Y edge"),
        Geometry.InputSocket.Equals(
            PreviewTransform.TransformPosition(FVector(0.0f, -200.0f, 0.0f)), 0.01f));
    TestTrue(TEXT("Output socket is on the local positive-Y edge"),
        Geometry.OutputSocket.Equals(
            PreviewTransform.TransformPosition(FVector(0.0f, 800.0f, 0.0f)), 0.01f));
    TestTrue(TEXT("Flow cue remains explicitly enabled"), Geometry.bShowProcessFlow);

    const ALBECoatLineActor* ECoatDefaults = GetDefault<ALBECoatLineActor>();
    const FLBPlacementPreviewGeometry ECoatGeometry =
        ALBManagementPawn::BuildMachinePlacementPreviewGeometry(
            ELBFactoryBuildMachineType::ECoatLine, FTransform::Identity,
            FVector(9750.0f, 0.0f, 500.0f), FVector(9750.0f, 750.0f, 500.0f), 0.0f);
    TestTrue(TEXT("ED-line preview uses its authored body-weld input socket"),
        ECoatDefaults && ECoatDefaults->GetInputPort()
        && ECoatGeometry.InputSocket.Equals(
            ECoatDefaults->GetInputPort()->GetRelativeLocation(), 0.01f));
    TestTrue(TEXT("ED-line preview uses its authored paint-output socket, not the safety-box edge"),
        ECoatDefaults && ECoatDefaults->GetOutputPort()
        && ECoatGeometry.OutputSocket.Equals(
            ECoatDefaults->GetOutputPort()->GetRelativeLocation(), 0.01f));

    const ALBBodyWeldLineActor* WeldDefaults = GetDefault<ALBBodyWeldLineActor>();
    const UBoxComponent* WeldEnvelope = WeldDefaults ? WeldDefaults->GetProtectedEnvelope() : nullptr;
    const FLBPlacementPreviewGeometry WeldGeometry =
        ALBManagementPawn::BuildMachinePlacementPreviewGeometry(
            ELBFactoryBuildMachineType::BodyWeldLine, FTransform::Identity,
            WeldEnvelope ? WeldEnvelope->GetRelativeLocation() : FVector::ZeroVector,
            WeldEnvelope ? WeldEnvelope->GetUnscaledBoxExtent() : FVector::OneVector, 0.0f);
    TestTrue(TEXT("Body-weld preview uses its authored stillage input and not optional base-kit input"),
        WeldDefaults && WeldDefaults->GetStillageInputPort()
        && WeldGeometry.InputSocket.Equals(
            WeldDefaults->GetStillageInputPort()->GetRelativeLocation(), 0.01f));
    TestTrue(TEXT("Body-weld preview uses its authored body-in-white output"),
        WeldDefaults && WeldDefaults->GetBIWOutputPort()
        && WeldGeometry.OutputSocket.Equals(
            WeldDefaults->GetBIWOutputPort()->GetRelativeLocation(), 0.01f));

    const FString NamedReason = ALBManagementPawn::FormatNamedObstructionReason(
        TEXT("protected machine envelope"), TEXT("PR002_COIL_CELL"), TEXT("SafetyEnvelope"));
    TestTrue(TEXT("Physics obstruction names the blocking actor and component"),
        NamedReason.Contains(TEXT("PR002_COIL_CELL"))
        && NamedReason.Contains(TEXT("SafetyEnvelope")));
    TestTrue(TEXT("Physics obstruction says how to correct it"),
        NamedReason.Contains(TEXT("MOVE OR ROTATE TO CLEAR IT")));
    const FLBPlacementPreviewStyle NamedBlocked = ALBManagementPawn::BuildPlacementPreviewStyle(
        true, false, NamedReason);
    TestTrue(TEXT("Large blocked-status detail retains the named obstruction"),
        NamedBlocked.State == ELBPlacementPreviewState::Blocked
        && NamedBlocked.NextAction.Contains(TEXT("PR002_COIL_CELL"))
        && NamedBlocked.NextAction.Contains(TEXT("SafetyEnvelope"))
        && NamedBlocked.NextAction.Contains(TEXT("MOVE OR ROTATE")));

    const FLBPlacementCardData Card = ALBManagementPawn::BuildPlacementCardData(
        TEXT("Seven-stage press train"), NamedBlocked,
        TEXT("PR002 Coil Cell_2147482471"), TEXT("PR002-01"));
    TestTrue(TEXT("Player card is visible, non-confirmable and uses a friendly obstruction name"),
        Card.bVisible && !Card.bCanConfirm
        && Card.Title == TEXT("SEVEN-STAGE PRESS TRAIN")
        && Card.Cause.Contains(TEXT("PR002 Coil Cell"))
        && !Card.Cause.Contains(TEXT("2147482471")));
    TestTrue(TEXT("Stable identity is optional but retained separately from the friendly name"),
        Card.ObstructionDisplayName == TEXT("PR002 Coil Cell")
        && Card.ObstructionStableId == TEXT("PR002-01")
        && Card.Cause.Contains(TEXT("[PR002-01]")));
    TestTrue(TEXT("Mouse and controller placement controls are presented together"),
        Card.Controls.Contains(TEXT("CLICK")) && Card.Controls.Contains(TEXT("ENTER"))
        && Card.Controls.Contains(TEXT("A")) && Card.Controls.Contains(TEXT("RB"))
        && Card.Controls.Contains(TEXT("ESC")) && Card.Controls.Contains(TEXT("B")));

    const FIntPoint HD(1280, 720);
    const FLBPlacementCardLayout HDRight = ALBManagementPawn::BuildPlacementCardLayout(
        HD, 320.0f);
    const FLBPlacementCardLayout HDLeft = ALBManagementPawn::BuildPlacementCardLayout(
        HD, 1000.0f);
    TestTrue(TEXT("720p card stays inside the viewport safe area on either side"),
        HDRight.IsInsideViewport(HD) && HDLeft.IsInsideViewport(HD)
        && !HDRight.bCardOnLeft && HDLeft.bCardOnLeft);
    const FIntPoint FullHD(1920, 1080);
    const FLBPlacementCardLayout FullHDLayout = ALBManagementPawn::BuildPlacementCardLayout(
        FullHD, 960.0f, true, false);
    TestTrue(TEXT("1080p card scales and remains safe-area clamped"),
        FullHDLayout.IsInsideViewport(FullHD)
        && FullHDLayout.UIScale > HDRight.UIScale
        && FullHDLayout.MaximumCharactersPerLine >= HDRight.MaximumCharactersPerLine);

    const TArray<FString> Wrapped = ALBManagementPawn::WrapPlacementCardText(
        TEXT("PROTECTED MACHINE ENVELOPE IS OBSTRUCTED BY A VERY LONG NAMED FACTORY ACTOR"),
        28, 3);
    TestTrue(TEXT("Card copy wraps to a strict bounded line count"),
        Wrapped.Num() > 1 && Wrapped.Num() <= 3);
    for (const FString& Line : Wrapped)
        TestTrue(TEXT("Every wrapped card line remains bounded including ellipsis"), Line.Len() <= 28);

    const FLBPlacementFramingContract Framing = ALBManagementPawn::BuildPlacementFramingContract(
        Geometry, HD, HDRight);
    TestTrue(TEXT("Placement framing reserves card space and never zooms inside placement minimum"),
        Framing.RequiredZoomDistanceCm >= ALBManagementPawn::GetMinimumPlacementZoomDistance()
        && FMath::Abs(Framing.CameraLateralOffsetCm) >= 350.0f
        && Framing.bCardOnLeft == HDRight.bCardOnLeft);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBPlacementGhostHierarchyTest,
    "LineBoss.Management.PlacementPreview.RecognisableMeshHierarchyGhost",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPlacementGhostHierarchyTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBPlacementGhostHierarchyWorld"));
    TestNotNull(TEXT("Ghost test world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ALBManagementPawn* Pawn = World->SpawnActor<ALBManagementPawn>();
    AActor* Source = World->SpawnActor<AActor>();
    TestNotNull(TEXT("Ghost pawn exists"), Pawn);
    TestNotNull(TEXT("Source preview actor exists"), Source);
    if (Pawn && Source)
    {
        USceneComponent* SourceRoot = NewObject<USceneComponent>(Source, TEXT("SourceRoot"));
        Source->SetRootComponent(SourceRoot);
        Source->AddInstanceComponent(SourceRoot);
        SourceRoot->RegisterComponent();
        UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr,
            TEXT("/Engine/BasicShapes/Cube.Cube"));
        for (int32 Index = 0; Index < 3; ++Index)
        {
            UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Source,
                *FString::Printf(TEXT("MachineModule%d"), Index));
            Mesh->SetupAttachment(SourceRoot);
            Mesh->SetStaticMesh(Cube);
            Mesh->SetRelativeLocation(FVector(Index * 140.0f, 0.0f, Index * 60.0f));
            Source->AddInstanceComponent(Mesh);
            Mesh->RegisterComponent();
        }
        TestTrue(TEXT("Actual source component hierarchy becomes a preview ghost"),
            Pawn->BuildPlacementGhostForAutomation(Source));
        TestEqual(TEXT("Ghost retains every recognisable mesh module"),
            Pawn->GetPlacementGhostMeshCount(), 3);
    }
    if (Pawn)
    {
        ALBBodyWeldLineActor* WeldSource = World->SpawnActor<ALBBodyWeldLineActor>();
        TestTrue(TEXT("Body-weld preview source configures"),
            WeldSource && WeldSource->Configure(TEXT("WELD-GHOST-TEST")));
        TestTrue(TEXT("Body-weld composite produces a recognisable multi-part ghost"),
            WeldSource && Pawn->BuildPlacementGhostForAutomation(WeldSource)
            && Pawn->GetPlacementGhostMeshCount() > 0);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBRenderableFactoryOverviewCameraTest,
    "LineBoss.Management.Camera.RenderableFactoryOverviewFraming",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBRenderableFactoryOverviewCameraTest::RunTest(const FString& Parameters)
{
    const FBox RepresentativeVisualBounds(
        FVector(-9251.75f, -2430.0f, 0.0f),
        FVector(9251.75f, 2430.0f, 1022.0f));
    const FLBFactoryOverviewFramingContract Contract =
        ALBManagementPawn::BuildFactoryOverviewFramingContract(
            RepresentativeVisualBounds, 6);
    TestTrue(TEXT("Representative production geometry resolves a valid overview contract"),
        Contract.IsValid());
    TestTrue(TEXT("Overview uses the intentional three-quarter factory pose"),
        FMath::IsNearlyEqual(Contract.PivotRotation.Yaw, -50.0f, 0.01f)
        && FMath::IsNearlyEqual(Contract.BoomRotation.Pitch, -32.0f, 0.01f));
    TestTrue(TEXT("Renderable framing is materially closer than the retired envelope rule"),
        Contract.ZoomDistanceCm < 22000.0f
        && Contract.ZoomDistanceCm >= ALBManagementPawn::GetMinimumPlacementZoomDistance());
    TestTrue(TEXT("Lower production-flow tray receives an explicit world-view composition bias"),
        !Contract.PivotLocation.Equals(RepresentativeVisualBounds.GetCenter(), 1.0f)
        && FMath::IsNearlyZero(Contract.PivotLocation.Z, 0.01f));
    TestTrue(TEXT("Explicit wide contract retains the complete renderable long axis"),
        Contract.bFramesWholeFactory
        && FMath::IsNearlyEqual(Contract.FramedLongAxisCm,
            RepresentativeVisualBounds.GetSize().X, 0.1f));
    TestFalse(TEXT("Invalid render bounds fail closed"),
        ALBManagementPawn::BuildFactoryOverviewFramingContract(FBox(ForceInit), 1).IsValid());

    // Exact visual bounds recorded by populated-overview visual QA v008. The
    // current 1280x720 management tray uses 229 px plus its 18 px bottom margin,
    // leaving 65.69% as the process-view aperture.
    const FBox V008PopulatedBounds(
        FVector(-10969.5f, -3210.0f, -525.0f),
        FVector(14479.0f, 6050.0f, 996.5f));
    const FLBFactoryOverviewFramingContract V008WholeContract =
        ALBManagementPawn::BuildFactoryOverviewFramingContract(V008PopulatedBounds, 12);
    const FLBFactoryOverviewFramingContract V008ProcessContract =
        ALBManagementPawn::BuildProcessOverviewFramingContract(V008PopulatedBounds, 12);
    TestTrue(TEXT("V008 process crop resolves a valid deterministic contract"),
        V008WholeContract.IsValid() && V008ProcessContract.IsValid());
    TestTrue(TEXT("Tray-safe aperture is fixed to the selected management composition"),
        FMath::IsNearlyEqual(ALBManagementPawn::GetProcessOverviewWorldApertureFraction(),
            473.0f / 720.0f, KINDA_SMALL_NUMBER));
    TestTrue(TEXT("Default populated view uses only the unobscured v008 process span"),
        !V008ProcessContract.bFramesWholeFactory
        && FMath::IsNearlyEqual(V008ProcessContract.FramedLongAxisCm,
            V008PopulatedBounds.GetSize().X
                * ALBManagementPawn::GetProcessOverviewWorldApertureFraction(), 0.1f));
    TestTrue(TEXT("V008 default crop is materially denser than the 25.4k cm wide fit"),
        V008ProcessContract.ZoomDistanceCm < V008WholeContract.ZoomDistanceCm * 0.70f);
    TestTrue(TEXT("Process and whole views preserve the same authored camera angles"),
        V008ProcessContract.PivotRotation.Equals(V008WholeContract.PivotRotation, 0.01f)
        && V008ProcessContract.BoomRotation.Equals(V008WholeContract.BoomRotation, 0.01f));
    TestFalse(TEXT("Invalid process bounds also fail closed"),
        ALBManagementPawn::BuildProcessOverviewFramingContract(FBox(ForceInit), 1).IsValid());

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBRenderableFactoryOverviewCameraWorld"));
    TestNotNull(TEXT("Renderable-overview camera test world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr,
        TEXT("/Engine/BasicShapes/Cube.Cube"));
    AStaticMeshActor* LeftMachine = World->SpawnActor<AStaticMeshActor>(
        FVector(-9000.0f, 0.0f, 100.0f), FRotator::ZeroRotator);
    AStaticMeshActor* RightMachine = World->SpawnActor<AStaticMeshActor>(
        FVector(9000.0f, 0.0f, 100.0f), FRotator::ZeroRotator);
    ALBManagementPawn* Pawn = World->SpawnActor<ALBManagementPawn>();
    TestTrue(TEXT("Two visible machine proxies and the management pawn spawn"),
        Cube && LeftMachine && RightMachine && Pawn);
    if (Cube && LeftMachine && RightMachine && Pawn)
    {
        for (AStaticMeshActor* Machine : {LeftMachine, RightMachine})
        {
            Machine->Tags.Add(TEXT("LB.FactoryBuilder.Machine"));
            Machine->GetStaticMeshComponent()->SetStaticMesh(Cube);
            Machine->SetActorScale3D(FVector(4.0f, 4.0f, 2.0f));
        }
        UBoxComponent* OversizedProtectedEnvelope = NewObject<UBoxComponent>(
            LeftMachine, TEXT("OversizedProtectedEnvelope"));
        TestNotNull(TEXT("Fixture has an oversized non-renderable placement envelope"),
            OversizedProtectedEnvelope);
        if (OversizedProtectedEnvelope)
        {
            OversizedProtectedEnvelope->SetBoxExtent(FVector(25000.0f));
            OversizedProtectedEnvelope->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
            OversizedProtectedEnvelope->SetupAttachment(
                LeftMachine->GetStaticMeshComponent());
            OversizedProtectedEnvelope->RegisterComponentWithWorld(World);
        }

        TestTrue(TEXT("Overview focuses the actual visible machine proxies"),
            Pawn->FocusBuiltFactory());
        const float ProcessZoomDistance = Pawn->GetManagementZoomDistance();
        TestTrue(TEXT("Protected query envelope cannot force the overview to maximum zoom"),
            ProcessZoomDistance
                < ALBManagementPawn::GetMaximumManagementZoomDistance() * 0.5f);
        TestTrue(TEXT("Default process overview retains the 4.2 m tray-safe minimum while respecting larger visible content"),
            ProcessZoomDistance >= 4200.0f);
        TestTrue(TEXT("Live overview applies the same isometric yaw contract"),
            FMath::IsNearlyEqual(Pawn->GetActorRotation().Yaw, -50.0f, 0.01f));
        TestTrue(TEXT("Explicit whole-factory focus remains available"),
            Pawn->FocusWholeBuiltFactory());
    TestTrue(TEXT("Whole-factory focus is materially wider than the default process crop"),
        Pawn->GetManagementZoomDistance() > ProcessZoomDistance * 1.35f);
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBInitialEmptyFactoryCameraTargetTest,
    "LineBoss.Management.Camera.EmptyCampaignFramesAuthorisedBuildBay",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBInitialEmptyFactoryCameraTargetTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBInitialEmptyFactoryCameraTargetWorld"));
    TestNotNull(TEXT("Empty-campaign camera test world created"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ALBPressShopBuildAuthority* Authority = World->SpawnActor<ALBPressShopBuildAuthority>();
    ALBManagementPawn* Pawn = World->SpawnActor<ALBManagementPawn>();
    TestNotNull(TEXT("Factory-floor authority exists"), Authority);
    TestNotNull(TEXT("Management pawn exists"), Pawn);
    if (Authority && Pawn)
    {
        FLBPressShopBuildBay Bay;
        Bay.BayId = TEXT("STARTER_BUILD_BAY");
        Bay.Centre = FVector(4200.0f, -1800.0f, 0.0f);
        Bay.HalfExtent = FVector(5000.0f, 4000.0f, 500.0f);
        Authority->BuildBays.Add(Bay);
        TestTrue(TEXT("A machine-free campaign can focus its authorised starter bay"),
            Pawn->FocusInitialBuildBay());
        TestTrue(TEXT("Camera pivot targets the authored bay centre"),
            Pawn->GetActorLocation().Equals(Bay.Centre, 0.01f));
        TestTrue(TEXT("Starter bay uses the readable production-line yaw"),
            FMath::IsNearlyEqual(Pawn->GetActorRotation().Yaw, -65.0f, 0.01f));
        TestTrue(TEXT("Starter bay starts at the established placement framing distance"),
            FMath::IsNearlyEqual(Pawn->GetManagementZoomDistance(),
                ALBManagementPawn::GetMinimumPlacementZoomDistance(), 0.01f));

        ALBPressShopBuildAuthority* Ambiguous = World->SpawnActor<ALBPressShopBuildAuthority>();
        if (Ambiguous) Ambiguous->BuildBays.Add(Bay);
        TestFalse(TEXT("Ambiguous build authorities fail closed instead of choosing a random bay"),
            Pawn->FocusInitialBuildBay());
    }

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
