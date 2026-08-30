#include "LBOneFactoryPressFeedPresentationActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "LBOneFactoryPressStarterLayout.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

#if WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#endif

namespace LBOneFactoryPressFeedPresentationPrivate
{
    const FTransform AggregateDatum(FQuat::Identity,
        FVector(9.25f, 2367.5f, 0.0f), FVector(100.0f));
}

ALBOneFactoryPressFeedPresentationActor::ALBOneFactoryPressFeedPresentationActor()
{
    PrimaryActorTick.bCanEverTick = true;
    SetActorEnableCollision(false);
    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);
    GreenStructure = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("FeedGreenStructure"));
    SteelConveyors = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("FeedSteelConveyors"));
    SafetyGuarding = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("FeedSafetyGuarding"));
    ShearBlade = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PR008ShearBlade"));
    SupermarketShuttle = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PR010Shuttle"));
    for (UStaticMeshComponent* Component :
        {static_cast<UStaticMeshComponent*>(GreenStructure.Get()),
         static_cast<UStaticMeshComponent*>(SteelConveyors.Get()),
         static_cast<UStaticMeshComponent*>(SafetyGuarding.Get()), ShearBlade.Get(),
         SupermarketShuttle.Get()})
    {
        Component->SetupAttachment(SceneRoot);
        ConfigureVisual(Component);
    }
    for (const TCHAR* Name : { TEXT("PR008Label"), TEXT("PR009Label"),
            TEXT("PR010Label") })
    {
        UTextRenderComponent* Label =
            CreateDefaultSubobject<UTextRenderComponent>(Name);
        Label->SetupAttachment(SceneRoot);
        Label->SetHorizontalAlignment(EHTA_Center);
        Label->SetVerticalAlignment(EVRTA_TextCenter);
        Label->SetWorldSize(44.0f);
        Label->SetTextRenderColor(FColor(245, 245, 235));
        Label->SetVisibility(false, true);
        Label->SetHiddenInGame(true, true);
        ModuleLabels.Add(Label);
    }
    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(TEXT("/Engine/BasicShapes/Cube.Cube"));
    Cube = CubeFinder.Succeeded() ? CubeFinder.Object : nullptr;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> GreenFinder(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v086.M_CA_MW_PR009_LayeredCairnwellGreen_v086"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SteelFinder(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_MachinedSteel_v086.M_CA_MW_PR009_MachinedSteel_v086"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> YellowFinder(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v086.M_CA_MW_PR009_LayeredSafetyYellow_v086"));
    Green = GreenFinder.Succeeded() ? GreenFinder.Object : nullptr;
    Steel = SteelFinder.Succeeded() ? SteelFinder.Object : nullptr;
    Yellow = YellowFinder.Succeeded() ? YellowFinder.Object : nullptr;
    Tags.AddUnique(GetPresentationTag());
    Tags.AddUnique(TEXT("LB.Provenance.NativeCode"));
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    SetActorHiddenInGame(true);
}

void ALBOneFactoryPressFeedPresentationActor::ConfigureVisual(UStaticMeshComponent* Component)
{
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetCanEverAffectNavigation(false);
    Component->SetGenerateOverlapEvents(false);
    Component->SetVisibility(false, true);
    Component->SetHiddenInGame(true, true);
}

bool ALBOneFactoryPressFeedPresentationActor::ConfigureFromPressLayout(
    const FLBOneFactoryPressStarterLayoutState& Layout, FString& OutReason)
{
    const FLBOneFactoryPressStarterStationState* Train = Layout.Stations.FindByPredicate([](const FLBOneFactoryPressStarterStationState& Station)
    { return Station.Role == ELBOneFactoryPressStarterRole::ConfigurablePressTrain; });
    if (!Cube || !Train) { OutReason = TEXT("PRESS FEED VISUAL REQUIRES NATIVE CUBE AND PRESS ANCHOR"); return false; }
    const FTransform Aggregate = LBOneFactoryPressFeedPresentationPrivate::AggregateDatum * Train->WorldTransform;
    SetActorLocation(Aggregate.TransformPosition(FVector(-15.0f, 42.7f, 0.0f)));
    SetActorRotation(Aggregate.GetRotation());
    for (UInstancedStaticMeshComponent* Component : {GreenStructure.Get(), SteelConveyors.Get(), SafetyGuarding.Get()})
        Component->ClearInstances();
    GreenStructure->SetStaticMesh(Cube); GreenStructure->SetMaterial(0, Green);
    SteelConveyors->SetStaticMesh(Cube); SteelConveyors->SetMaterial(0, Steel);
    SafetyGuarding->SetStaticMesh(Cube); SafetyGuarding->SetMaterial(0, Yellow);
    ShearBlade->SetStaticMesh(Cube); ShearBlade->SetMaterial(0, Steel);
    SupermarketShuttle->SetStaticMesh(Cube); SupermarketShuttle->SetMaterial(0, Green);
    auto Add = [](UInstancedStaticMeshComponent* Target, const FVector& L, const FVector& S)
    { Target->AddInstance(FTransform(FQuat::Identity, L, S)); };
    // PR008: strip / blank preparation line with guarded shear.
    Add(GreenStructure, FVector(-950, 0, 175), FVector(8.0f, 2.6f, 3.5f));
    Add(SteelConveyors, FVector(-950, 0, 55), FVector(14.0f, 1.3f, .18f));
    // PR009: stacker gantry and lifting table.
    Add(GreenStructure, FVector(-50, 0, 240), FVector(3.4f, 3.8f, 4.8f));
    Add(SteelConveyors, FVector(-50, 0, 62), FVector(4.0f, 2.6f, .22f));
    // PR010: four physically separated supermarket lanes.
    for (int32 Lane = 0; Lane < 4; ++Lane)
    {
        const float Y = -450.0f + Lane * 300.0f;
        Add(SteelConveyors, FVector(900, Y, 48), FVector(6.0f, 1.0f, .16f));
        Add(GreenStructure, FVector(900, Y, 105), FVector(5.5f, .8f, .55f));
    }
    // Protected separation around each process module and the supermarket aisle.
    for (float X : {-950.0f, -50.0f, 900.0f})
    {
        Add(SafetyGuarding, FVector(X, -390, 110), FVector(7.0f, .12f, 2.2f));
        Add(SafetyGuarding, FVector(X, 390, 110), FVector(7.0f, .12f, 2.2f));
    }
    ShearBlade->SetRelativeTransform(FTransform(FQuat::Identity, FVector(-650, 0, 375), FVector(1.5f, 2.2f, .28f)));
    SupermarketShuttle->SetRelativeTransform(FTransform(FQuat::Identity, FVector(250, 0, 80), FVector(2.2f, 1.2f, .45f)));
    ShearRest = ShearBlade->GetRelativeTransform(); ShuttleRest = SupermarketShuttle->GetRelativeTransform();
    const TCHAR* LabelText[] = { TEXT("PR008  STRIP / BLANK PREP"),
        TEXT("PR009  STACK PREP"), TEXT("PR010  FOUR-LANE SUPERMARKET") };
    const FVector LabelLocations[] = { FVector(-950, -430, 600),
        FVector(-50, -430, 650), FVector(900, -560, 390) };
    for (int32 Index = 0; Index < ModuleLabels.Num() && Index < UE_ARRAY_COUNT(LabelText);
        ++Index)
    {
        UTextRenderComponent* Label = ModuleLabels[Index];
        if (!Label) continue;
        Label->SetText(FText::FromString(LabelText[Index]));
        Label->SetRelativeLocation(LabelLocations[Index]);
        Label->SetRelativeRotation(FRotator(0.0f, -90.0f, 0.0f));
        Label->SetVisibility(true, true);
        Label->SetHiddenInGame(false, true);
    }
    bConfigured = true; SetActorHiddenInGame(false);
    for (UStaticMeshComponent* Component : {static_cast<UStaticMeshComponent*>(GreenStructure.Get()), static_cast<UStaticMeshComponent*>(SteelConveyors.Get()), static_cast<UStaticMeshComponent*>(SafetyGuarding.Get()), ShearBlade.Get(), SupermarketShuttle.Get()})
    { Component->SetVisibility(true, true); Component->SetHiddenInGame(false, true); }
    OutReason = TEXT("NATIVE PR008 SHEAR, PR009 STACKER AND FOUR-LANE PR010 SUPERMARKET VISIBLE");
    return true;
}

void ALBOneFactoryPressFeedPresentationActor::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (!bConfigured) return;
    const float Time = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
    FTransform Shear = ShearRest; Shear.AddToTranslation(FVector(0, 0, -FMath::Max(0.0f, FMath::Sin(Time * 2.2f)) * 75.0f));
    ShearBlade->SetRelativeTransform(Shear, false, nullptr, ETeleportType::TeleportPhysics);
    FTransform Shuttle = ShuttleRest; Shuttle.AddToTranslation(FVector(0, FMath::Sin(Time * .35f) * 430.0f, 0));
    SupermarketShuttle->SetRelativeTransform(Shuttle, false, nullptr, ETeleportType::TeleportPhysics);
}

FName ALBOneFactoryPressFeedPresentationActor::GetPresentationTag()
{ return FName(TEXT("LB.OneFactory.PressFeedPresentation.Native")); }

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryPressFeedPresentationTest,
    "LineBoss.OneFactory.PressStarter.Feed.NativePresentation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPressFeedPresentationTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPressFeedPresentationTest"));
    ALBOneFactoryPressStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryPressStarterLayoutAuthority>() : nullptr;
    ALBOneFactoryPressFeedPresentationActor* Presentation = World
        ? World->SpawnActor<ALBOneFactoryPressFeedPresentationActor>() : nullptr;
    if (!TestNotNull(TEXT("Press layout authority exists"), Authority)
        || !TestNotNull(TEXT("Feed presentation fixture exists"), Presentation))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    FString Reason;
    TestTrue(TEXT("Native upstream feed visual materialises"),
        Presentation->ConfigureFromPressLayout(Authority->CaptureLayout(), Reason));
    TestTrue(TEXT("Feed presentation has a stable native tag"),
        Presentation->ActorHasTag(ALBOneFactoryPressFeedPresentationActor::GetPresentationTag()));
    TestEqual(TEXT("PR008, PR009 and PR010 remain separately represented"),
        Presentation->GetVisibleModuleCount(), 3);
    TArray<UStaticMeshComponent*> Components;
    Presentation->GetComponents<UStaticMeshComponent>(Components);
    for (const UStaticMeshComponent* Component : Components)
    {
        if (!TestNotNull(TEXT("Every native feed component exists"), Component)) continue;
        TestEqual(TEXT("Feed presentation is visual only"),
            Component->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
        TestFalse(TEXT("Feed presentation has no navigation impact"),
            Component->CanEverAffectNavigation());
    }
    Presentation->Destroy(); Authority->Destroy(); World->DestroyWorld(false);
    return true;
}

#endif
