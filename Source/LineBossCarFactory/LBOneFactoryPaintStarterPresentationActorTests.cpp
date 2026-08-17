#include "LBOneFactoryPaintStarterPresentationActor.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UObject/UnrealType.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPaintPresentationContractTest,
    "LineBoss.OneFactory.PaintStarter.PresentationExactNativeTrackedEDContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPaintPresentationContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    FString Reason;
    const FLBOneFactoryPaintStarterLayoutState Layout =
        ULBOneFactoryPaintStarterLayoutLibrary::MakeCanonicalStarterLayout();
    const TArray<FSoftObjectPath> Paths =
        ALBOneFactoryPaintStarterPresentationActor::GetRequiredNativeAssetPaths();
    TestEqual(TEXT("Presentation has 10 profile plus 14 ED/BIW dependencies"),
        Paths.Num(), 24);
    TestTrue(TEXT("Exact native presentation references validate"),
        ALBOneFactoryPaintStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPaintStarterPresentationActor::
                    GetPresentationClassPath(), Paths, Reason));
    for (const FSoftObjectPath& Path : Paths)
    {
        const FString Reference = Path.ToString();
        TestFalse(TEXT("No exact reference contains Meshy"),
            Reference.Contains(TEXT("Meshy"), ESearchCase::IgnoreCase));
        TestFalse(TEXT("No exact reference is external-generated"),
            Reference.Contains(TEXT("ExternalGenerated"),
                ESearchCase::IgnoreCase));
    }
    TestTrue(TEXT("Immersed bath body uses the approved C2040 BIW authority"),
        Paths.Contains(FSoftObjectPath(TEXT(
            "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
            "Cairnwell2040Runtime_v001/Meshes/"
            "SM_LB_C2040_BIW_AutomotiveSkeleton_v001."
            "SM_LB_C2040_BIW_AutomotiveSkeleton_v001"))));
    TestEqual(TEXT("Immersed BIW uses its V013 galvanized material"),
        Paths.Last().ToString(), FString(TEXT(
            "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
            "Cairnwell2040Runtime_v001/Materials/"
            "M_LB_C2040_BIWGalvanized_v001."
            "M_LB_C2040_BIWGalvanized_v001")));
    TArray<FSoftObjectPath> WrongPaths = Paths;
    WrongPaths[0] = FSoftObjectPath(
        TEXT("/Game/LineBoss/Candidates/PaintShop/Unknown.SM_Unknown"));
    TestFalse(TEXT("One changed dependency rejects the whole allowlist"),
        ALBOneFactoryPaintStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPaintStarterPresentationActor::
                    GetPresentationClassPath(), WrongPaths, Reason));
    TestFalse(TEXT("A subclass-like name cannot widen the exact class list"),
        ALBOneFactoryPaintStarterPresentationActor::
            ValidateNativePresentationReferences(
                TEXT("/Script/LineBossCarFactory.LBOneFactoryPaintStarterPresentationActorChild"),
                Paths, Reason));
    TArray<FSoftObjectPath> MissingEDPath = Paths;
    MissingEDPath.RemoveAt(MissingEDPath.Num() - 1);
    TestFalse(TEXT("One missing ED material rejects the whole closure"),
        ALBOneFactoryPaintStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPaintStarterPresentationActor::
                    GetPresentationClassPath(), MissingEDPath, Reason));

    ALBOneFactoryPaintStarterPresentationActor* CDO =
        ALBOneFactoryPaintStarterPresentationActor::StaticClass()
            ->GetDefaultObject<ALBOneFactoryPaintStarterPresentationActor>();
    const FName HardMeshProperties[] = {
        TEXT("EDTreatmentStartMesh"), TEXT("EDTreatmentEndMesh"),
        TEXT("EDDrainInspectionMesh"), TEXT("EDOvenSegmentMesh"),
        TEXT("EDCarrierGantryMesh"),
        TEXT("EDTreatmentLiquidMesh"), TEXT("EDImmersedBIWMesh")};
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(HardMeshProperties); ++Index)
    {
        const FObjectPropertyBase* Property =
            FindFProperty<FObjectPropertyBase>(
                ALBOneFactoryPaintStarterPresentationActor::StaticClass(),
                HardMeshProperties[Index]);
        TestNotNull(TEXT("Every ED mesh is a reflected hard-object property"),
            Property);
        if (!Property) continue;
        TestFalse(TEXT("Every ED mesh hard reference is serialized"),
            Property->HasAnyPropertyFlags(CPF_Transient));
        TestTrue(TEXT("Every ED mesh property accepts only UStaticMesh"),
            Property->PropertyClass == UStaticMesh::StaticClass());
        const UObject* Object = CDO
            ? Property->GetObjectPropertyValue_InContainer(CDO) : nullptr;
        TestNotNull(TEXT("Every CDO ED mesh hard reference resolves"), Object);
        if (Object)
        {
            // Assert membership, not position: the ED asset list's order
            // is free to change as the contract is versioned.
            TestTrue(TEXT("Every CDO ED mesh is in the frozen asset list"),
                Paths.ContainsByPredicate(
                    [Object](const FSoftObjectPath& Candidate)
                    {
                        return Candidate.ToString()
                            == Object->GetPathName();
                    }));
        }
    }
    const FArrayProperty* LiquidMaterialProperty =
        FindFProperty<FArrayProperty>(
            ALBOneFactoryPaintStarterPresentationActor::StaticClass(),
            TEXT("EDTreatmentLiquidMaterials"));
    TestNotNull(TEXT("ED liquid material closure is a reflected hard array"),
        LiquidMaterialProperty);
    if (LiquidMaterialProperty && CDO)
    {
        TestFalse(TEXT("ED liquid material closure is serialized"),
            LiquidMaterialProperty->HasAnyPropertyFlags(CPF_Transient));
        const FObjectPropertyBase* Inner =
            CastField<FObjectPropertyBase>(LiquidMaterialProperty->Inner);
        TestNotNull(TEXT("ED liquid array holds hard object references"), Inner);
        FScriptArrayHelper Helper(LiquidMaterialProperty,
            LiquidMaterialProperty->ContainerPtrToValuePtr<void>(CDO));
        TestEqual(TEXT("CDO holds all six ED liquid materials"),
            Helper.Num(), 6);
        if (Inner)
        {
            TestTrue(TEXT("ED liquid array accepts material interfaces"),
                Inner->PropertyClass == UMaterialInterface::StaticClass());
            for (int32 Index = 0; Index < Helper.Num(); ++Index)
            {
                const UObject* Object = Inner->GetObjectPropertyValue(
                    Helper.GetRawPtr(Index));
                TestNotNull(TEXT("Every CDO ED liquid material resolves"),
                    Object);
                if (Object)
                {
                    // Membership, not position - see the mesh loop above.
                    TestTrue(TEXT("Every CDO ED liquid material is frozen"),
                        Paths.ContainsByPredicate(
                            [Object](const FSoftObjectPath& Candidate)
                            {
                                return Candidate.ToString()
                                    == Object->GetPathName();
                            }));
                }
            }
        }
    }
    const FObjectPropertyBase* BIWMaterialProperty =
        FindFProperty<FObjectPropertyBase>(
            ALBOneFactoryPaintStarterPresentationActor::StaticClass(),
            TEXT("EDImmersedBIWMaterial"));
    TestNotNull(TEXT("C2040 BIW material is a reflected hard property"),
        BIWMaterialProperty);
    if (BIWMaterialProperty && CDO)
    {
        TestFalse(TEXT("C2040 BIW material hard reference is serialized"),
            BIWMaterialProperty->HasAnyPropertyFlags(CPF_Transient));
        TestTrue(TEXT("C2040 BIW material property is exact interface type"),
            BIWMaterialProperty->PropertyClass
                == UMaterialInterface::StaticClass());
        const UObject* Object =
            BIWMaterialProperty->GetObjectPropertyValue_InContainer(CDO);
        TestNotNull(TEXT("C2040 BIW material resolves on the native CDO"),
            Object);
        if (Object)
        {
            TestEqual(TEXT("C2040 BIW material path is exact"),
                Object->GetPathName(), Paths.Last().ToString());
        }
    }

    const TArray<FLBOneFactoryPaintPresentationItem> Items =
        ALBOneFactoryPaintStarterPresentationActor::
            BuildExpectedPresentationItems(Layout);
    TestEqual(TEXT("Deterministic contract has 119 visual items"),
        Items.Num(), 119);
    TestTrue(TEXT("Deterministic Paint presentation validates"),
        ALBOneFactoryPaintStarterPresentationActor::
            ValidatePresentationContract(Layout, Items, Reason));
    TestEqual(TEXT("Presentation uses 22 non-empty HISM batches"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedVisualBatchCount(), 22);
    TestEqual(TEXT("Only one spray booth shell is shown"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::BlackBoxSprayBooth), 1);
    TestEqual(TEXT("Pretreatment black-box tunnel is no longer presented"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::PretreatmentWashTunnel),
        0);
    TestEqual(TEXT("Flash black-box tunnel is replaced by drain and oven"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::FlashOffTunnel), 0);
    TestEqual(TEXT("Two skids are environmental, not seeded bodies"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::BodySkidCarrier), 2);
    TestEqual(TEXT("Six open treatment starts are visible"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::EDTreatmentStartModule), 6);
    TestEqual(TEXT("Six open treatment ends are visible"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::EDTreatmentEndModule), 6);
    TestEqual(TEXT("Profiled dip rails use 60 deterministic segments"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::EDProfiledRailCube), 60);
    TestEqual(TEXT("One static immersed BIW makes the ED tank legible"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::EDImmersedBody), 1);
    TestEqual(TEXT("The ED bake oven runs as four production bays"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::EDOvenSegment), 4);
    TestEqual(TEXT("A carrier gantry bay stands over each of the six tanks"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::EDCarrierGantryBay), 6);
    TestEqual(TEXT("Every responsibility has one semantic status marker"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForBatch(
                ELBOneFactoryPaintPresentationBatch::StatusCube), 8);
    TestEqual(TEXT("Pretreatment role carries four complete open tanks"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForRole(
                ELBOneFactoryPaintStarterRole::PretreatmentWash), 60);
    TestEqual(TEXT("ED role carries two baths plus one immersed C2040 BIW"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForRole(
                ELBOneFactoryPaintStarterRole::EDCoatLogicalProcess), 33);
    TestEqual(TEXT("Existing flash role carries drain and ED bake oven"),
        ALBOneFactoryPaintStarterPresentationActor::
            GetExpectedInstanceCountForRole(
                ELBOneFactoryPaintStarterRole::FlashOff), 8);
    for (const FLBOneFactoryPaintPresentationItem& Item : Items)
    {
        TestFalse(TEXT("Visual item owns no process WIP"),
            Item.bRepresentsProcessWIP);
        TestFalse(TEXT("Visual item claims no hidden process internals"),
            Item.bClaimsHiddenProcessInternals);
        const FString Id = Item.PresentationId.ToString();
        TestFalse(TEXT("Visual inventory contains no robot claim"),
            Id.Contains(TEXT("ROBOT"), ESearchCase::IgnoreCase));
        TestFalse(TEXT("Visual inventory contains no window claim"),
            Id.Contains(TEXT("WINDOW"), ESearchCase::IgnoreCase));
        TestFalse(TEXT("Visual inventory contains no side-door claim"),
            Id.Contains(TEXT("SIDE_DOOR"), ESearchCase::IgnoreCase));
    }

    const FLBOneFactoryPaintPresentationItem* FirstTankStart =
        Items.FindByPredicate([](const FLBOneFactoryPaintPresentationItem& Item)
        {
            return Item.PresentationId == FName(
                TEXT("OF_PAINT_VIS_OF_PAINT_PRETREAT_WASH_001_TANK_01_START"));
        });
    TestNotNull(TEXT("Pretreatment starts with an exact open tank module"),
        FirstTankStart);
    if (FirstTankStart)
    {
        TestTrue(TEXT("First treatment start is anchored inside pretreatment"),
            FirstTankStart->WorldTransform.GetLocation().Equals(
                FVector(1133.0f, -8500.0f, 0.0f), 0.001f));
        TestTrue(TEXT("First treatment module uses the frozen compression"),
            FirstTankStart->WorldTransform.GetScale3D().Equals(
                FVector(0.18f, 0.55f, 0.65f), 0.001f));
    }
    const FLBOneFactoryPaintPresentationItem* ImmersedBody =
        Items.FindByPredicate([](const FLBOneFactoryPaintPresentationItem& Item)
        {
            return Item.Batch ==
                ELBOneFactoryPaintPresentationBatch::EDImmersedBody;
        });
    TestNotNull(TEXT("ED tank contains one static presentation BIW"),
        ImmersedBody);
    if (ImmersedBody)
    {
        TestTrue(TEXT("Static BIW is anchored in the ED bath"),
            ImmersedBody->WorldTransform.GetLocation().Equals(
                FVector(3238.0f, -8500.0f, 113.75f), 0.001f));
        TestFalse(TEXT("Static BIW is explicitly not production WIP"),
            ImmersedBody->bRepresentsProcessWIP);
    }
    const FLBOneFactoryPaintPresentationItem* EDOvenExit =
        Items.FindByPredicate([](const FLBOneFactoryPaintPresentationItem& Item)
        {
            return Item.Batch ==
                ELBOneFactoryPaintPresentationBatch::EDOvenSegment;
        });
    TestNotNull(TEXT("ED route ends with visible production oven bays"),
        EDOvenExit);
    if (EDOvenExit)
    {
        TestTrue(TEXT("The oven run starts at the flash station"),
            EDOvenExit->WorldTransform.GetLocation().Equals(
                FVector(4620.0f, -8500.0f, 0.0f), 0.001f));
        // v002: the production bay is authored at true size, so it stands at
        // scale one instead of the blockout's station-fit squeeze.
        TestTrue(TEXT("The oven bay stands at authored scale"),
            EDOvenExit->WorldTransform.GetScale3D().Equals(
                FVector::OneVector, 0.001f));
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPaintPresentationConfigureTest,
    "LineBoss.OneFactory.PaintStarter.PresentationFreshAssetResolutionAndHISMCommit",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPaintPresentationConfigureTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPaintPresentationConfigureTest"));
    ALBOneFactoryPaintStarterPresentationActor* Presentation = World
        ? World->SpawnActor<ALBOneFactoryPaintStarterPresentationActor>()
        : nullptr;
    if (!TestNotNull(TEXT("Paint presentation actor spawns"), Presentation))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    TestFalse(TEXT("Paint presentation never ticks"),
        Presentation->PrimaryActorTick.bCanEverTick);
    TestFalse(TEXT("Paint presentation is non-replicated"),
        Presentation->GetIsReplicated());
    TestFalse(TEXT("Paint presentation has no actor collision"),
        Presentation->GetActorEnableCollision());
    TestFalse(TEXT("Paint presentation never represents WIP"),
        Presentation->RepresentsProcessWIP());
    TestFalse(TEXT("Paint presentation never claims hidden internals"),
        Presentation->ClaimsHiddenProcessInternals());
    TestTrue(TEXT("Tracked ED line has an explicit truthful tag"),
        Presentation->Tags.Contains(FName(
            TEXT("LB.Paint.TrackedEDLineVisible"))));
    TArray<UHierarchicalInstancedStaticMeshComponent*> VisualComponents;
    Presentation->GetComponents(VisualComponents);
    TestEqual(TEXT("Actor owns the exact 24 visual components"),
        VisualComponents.Num(), 24);
    for (const UHierarchicalInstancedStaticMeshComponent* Component
        : VisualComponents)
    {
        TestNotNull(TEXT("Every visual component is present"), Component);
        if (!Component) continue;
        TestEqual(TEXT("Every visual component has collision disabled"),
            Component->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
        TestFalse(TEXT("Every visual component is excluded from navigation"),
            Component->CanEverAffectNavigation());
        TestFalse(TEXT("Every visual component is tick-free"),
            Component->PrimaryComponentTick.bCanEverTick);
    }

    const FLBOneFactoryPaintStarterLayoutState Layout =
        ULBOneFactoryPaintStarterLayoutLibrary::MakeCanonicalStarterLayout();
    FString Reason;
    TestTrue(TEXT("All native assets/LODs resolve before HISM commit"),
        Presentation->ConfigureFromLayout(Layout, Reason));
    TestTrue(TEXT("Presentation reports configured only after full commit"),
        Presentation->IsPresentationConfigured());
    const UHierarchicalInstancedStaticMeshComponent* RailBatch = nullptr;
    const UHierarchicalInstancedStaticMeshComponent* ImmersedBatch = nullptr;
    for (const UHierarchicalInstancedStaticMeshComponent* Component
        : VisualComponents)
    {
        if (!Component) continue;
        if (Component->GetFName() == FName(TEXT("EDProfiledRailBatch")))
            RailBatch = Component;
        if (Component->GetFName() == FName(TEXT("EDImmersedBodyBatch")))
            ImmersedBatch = Component;
    }
    TestNotNull(TEXT("Profiled carrier rail batch exists"), RailBatch);
    if (RailBatch && RailBatch->GetMaterial(0))
    {
        TestEqual(TEXT("Profiled rails retain exact graphite binding"),
            RailBatch->GetMaterial(0)->GetPathName(), FString(TEXT(
                "/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001/"
                "Materials/MI_LB_EDLine_StructuralSteel_Graphite_v001."
                "MI_LB_EDLine_StructuralSteel_Graphite_v001")));
    }
    else
    {
        AddError(TEXT("Profiled carrier rail material did not resolve"));
    }
    TestNotNull(TEXT("Immersed C2040 BIW batch exists"), ImmersedBatch);
    if (ImmersedBatch && ImmersedBatch->GetStaticMesh())
    {
        TestEqual(TEXT("Immersed batch uses exact C2040 BIW mesh"),
            ImmersedBatch->GetStaticMesh()->GetPathName(), FString(TEXT(
                "/Game/LineBoss/Factory/OneFactory/v001/Vehicles/"
                "Cairnwell2040Runtime_v001/Meshes/"
                "SM_LB_C2040_BIW_AutomotiveSkeleton_v001."
                "SM_LB_C2040_BIW_AutomotiveSkeleton_v001")));
    }
    TestEqual(TEXT("Exact visible item count committed"),
        Presentation->GetVisibleInstanceCount(), 119);
    TestEqual(TEXT("Every expected HISM batch is non-empty"),
        Presentation->GetVisualBatchCount(), 22);
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPaintPresentationBatch::CuringOvenTunnel);
        Value <= static_cast<int32>(
            ELBOneFactoryPaintPresentationBatch::EDCarrierGantryBay); ++Value)
    {
        const ELBOneFactoryPaintPresentationBatch Batch =
            static_cast<ELBOneFactoryPaintPresentationBatch>(Value);
        TestEqual(TEXT("Committed batch has its frozen exact count"),
            Presentation->GetInstanceCountForBatch(Batch),
            ALBOneFactoryPaintStarterPresentationActor::
                GetExpectedInstanceCountForBatch(Batch));
    }
    TestEqual(TEXT("Configured colour matches source data snapshot"),
        Presentation->GetConfiguredBodyColour(),
        ELBOneFactoryPaintColour::CairnwellTeal);
    FTransform ConfiguredSpray;
    TestTrue(TEXT("Configured station transform is queryable"),
        Presentation->GetConfiguredStationTransform(
            LBOneFactoryPaintStarterIds::Station(
                ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth),
            ConfiguredSpray));
    TestTrue(TEXT("Queried spray transform is exact"),
        ConfiguredSpray.Equals(Layout.Stations[4].WorldTransform, 0.001f));

    Presentation->ClearPresentation();
    TestFalse(TEXT("Explicit clear removes configured state"),
        Presentation->IsPresentationConfigured());
    TestEqual(TEXT("Explicit clear removes every visible item"),
        Presentation->GetVisibleInstanceCount(), 0);
    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPaintPresentationRollbackTest,
    "LineBoss.OneFactory.PaintStarter.PresentationFailureClearsAndFollowsSnapshot",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPaintPresentationRollbackTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPaintPresentationRollbackTest"));
    ALBOneFactoryPaintStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryPaintStarterLayoutAuthority>() : nullptr;
    ALBOneFactoryPaintStarterPresentationActor* Presentation = World
        ? World->SpawnActor<ALBOneFactoryPaintStarterPresentationActor>()
        : nullptr;
    if (!TestNotNull(TEXT("Paint authority exists"), Authority)
        || !TestNotNull(TEXT("Paint presentation exists"), Presentation))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    FLBOneFactoryPaintStarterLayoutState Invalid = Authority->CaptureLayout();
    Invalid.Stations[1].StationId = Invalid.Stations[0].StationId;
    TestFalse(TEXT("Invalid source snapshot cannot produce partial visuals"),
        Presentation->ConfigureFromLayout(Invalid, Reason));
    TestFalse(TEXT("Failure leaves actor unconfigured"),
        Presentation->IsPresentationConfigured());
    TestEqual(TEXT("Failure leaves zero partial instances"),
        Presentation->GetVisibleInstanceCount(), 0);

    TestTrue(TEXT("Player changes complete Paint programme"),
        Authority->SetStationPaintProgramme(
            LBOneFactoryPaintStarterIds::Station(
                ELBOneFactoryPaintStarterRole::EDCoatLogicalProcess),
            ELBOneFactoryPaintColour::AuroraBlue, Reason));
    FLBOneFactoryPaintStarterLayoutState Blue = Authority->CaptureLayout();
    const FTransform OriginalSpray = Blue.Stations[4].WorldTransform;
    FTransform MovedSpray = OriginalSpray;
    MovedSpray.AddToTranslation(FVector(0.0f, 25.0f, 0.0f));
    TestTrue(TEXT("Player safely repositions idle spray responsibility"),
        Authority->MoveStation(Blue.Stations[4].StationId,
            MovedSpray, Reason));
    Blue = Authority->CaptureLayout();
    TestTrue(TEXT("Presentation follows changed data snapshot"),
        Presentation->ConfigureFromLayout(Blue, Reason));
    TestEqual(TEXT("Programme colour follows authoritative selection"),
        Presentation->GetConfiguredBodyColour(),
        ELBOneFactoryPaintColour::AuroraBlue);
    FTransform ConfiguredSpray;
    TestTrue(TEXT("Moved spray transform remains queryable"),
        Presentation->GetConfiguredStationTransform(
            Blue.Stations[4].StationId, ConfiguredSpray));
    TestTrue(TEXT("Visual moved exactly with source responsibility"),
        ConfiguredSpray.Equals(MovedSpray, 0.001f));

    TArray<FLBOneFactoryPaintPresentationItem> Tampered =
        ALBOneFactoryPaintStarterPresentationActor::
            BuildExpectedPresentationItems(Blue);
    Tampered[0].bClaimsHiddenProcessInternals = true;
    TestFalse(TEXT("Any invented hidden-internal claim fails the contract"),
        ALBOneFactoryPaintStarterPresentationActor::
            ValidatePresentationContract(Blue, Tampered, Reason));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryPaintCookManifestContractTest,
    "LineBoss.OneFactory.PaintStarter.Presentation.CookManifestCoversEveryFrozenBinding",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPaintCookManifestContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    // The frozen presentation resolves every binding by path string, which
    // the cooker cannot see: without an always-cook root the shop ships
    // empty. Mirrors FLBOneFactoryBodyWeldCookManifestContractTest.
    const FString ConfigPath =
        FPaths::ProjectConfigDir() / TEXT("DefaultGame.ini");
    FString ConfigContents;
    TestTrue(TEXT("Project packaging configuration is readable"),
        FFileHelper::LoadFileToString(ConfigContents, *ConfigPath));

    for (const FSoftObjectPath& Asset :
        ALBOneFactoryPaintStarterPresentationActor::
            GetRequiredNativeAssetPaths())
    {
        const FString Path = Asset.ToString();
        if (!Path.StartsWith(TEXT("/Game/")))
        {
            continue;
        }
        FString PackagePath = Path;
        int32 DotIndex = INDEX_NONE;
        if (PackagePath.FindChar(TEXT('.'), DotIndex))
        {
            PackagePath.LeftInline(DotIndex);
        }
        // Every /Game binding must sit under some always-cook root.
        FString Folder = PackagePath;
        bool bCovered = false;
        while (!bCovered)
        {
            int32 SlashIndex = INDEX_NONE;
            if (!Folder.FindLastChar(TEXT('/'), SlashIndex)
                || SlashIndex <= 6)
            {
                break;
            }
            Folder.LeftInline(SlashIndex);
            bCovered = ConfigContents.Contains(FString::Printf(
                TEXT("DirectoriesToAlwaysCook=(Path=\"%s\")"), *Folder));
        }
        TestTrue(FString::Printf(
            TEXT("Cook manifest covers frozen binding %s"), *Path), bCovered);

        const FString FilePath = FPaths::ProjectContentDir()
            / PackagePath.RightChop(6) + TEXT(".uasset");
        TestTrue(FString::Printf(
            TEXT("Frozen binding exists on disk: %s"), *Path),
            FPaths::FileExists(FilePath));
    }
    return true;
}

#endif
