#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryBootstrap.h"
#include "LBOneFactoryGameMode.h"
#include "LBOneFactoryProductionHUD.h"
#include "LBOneFactoryProductionFlow.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactoryTypes.h"

#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/GameModeBase.h"
#include "LBBodyWeldLineActor.h"
#include "LBControlRoomHUD.h"
#include "LBECoatLineActor.h"
#include "LBFactoryBuildMachine.h"
#include "LBManagementPawn.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressShopStorageZone.h"
#include "LBPressTrainAStation.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryTestsPrivate
{
    template<typename ActorType>
    int32 CountLiveActors(UWorld* World)
    {
        int32 Count = 0;
        if (!World) return Count;
        for (TActorIterator<ActorType> It(World); It; ++It)
        {
            if (IsValid(*It) && !It->IsActorBeingDestroyed()) ++Count;
        }
        return Count;
    }

    void ConfigureCanonicalAuthority(ALBPressShopBuildAuthority& Authority,
        const FLBOneFactoryLayoutDefinition& Layout)
    {
        ULBOneFactoryLayoutLibrary::BuildExpectedPressAuthorityContract(Layout,
            Authority.BuildBays, Authority.ProtectedAreas, Authority.UtilitySpines,
            Authority.LogisticsSpines);
        Authority.StorageBays.Reset();
        Authority.SetActorTransform(FTransform::Identity);
        Authority.Tags.AddUnique(ALBOneFactoryBootstrap::GetPressBuildAuthorityTag());
        Authority.Tags.AddUnique(ALBOneFactoryBootstrap::GetNativeOnlyTag());
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryStableLayoutTest,
    "LineBoss.OneFactory.Layout.StableMoorcrossWorksContract",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryStableLayoutTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const FLBOneFactoryLayoutDefinition Layout =
        ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
    FString Reason;
    TestTrue(TEXT("Canonical Moorcross Works layout validates structurally"),
        ULBOneFactoryLayoutLibrary::ValidateLayout(Layout, Reason));
    TestTrue(TEXT("Canonical Moorcross Works layout passes exact drift validation"),
        ULBOneFactoryLayoutLibrary::ValidateMoorcrossWorksLayout(Layout, Reason));
    TestEqual(TEXT("Factory display name is stable"), Layout.FactoryDisplayName,
        FString(TEXT("Moorcross Works")));
    TestEqual(TEXT("Factory layout ID is stable"), Layout.LayoutId,
        LBOneFactoryIds::MoorcrossWorksLayout());
    TestTrue(TEXT("Factory envelope is exactly 620 x 310 x 30 m"),
        Layout.FactoryEnvelopeSizeCm.Equals(FVector(62000.0f, 31000.0f, 3000.0f),
            0.01f));
    TestEqual(TEXT("Exactly four department bays are authored"),
        Layout.DepartmentBays.Num(), 4);
    TestEqual(TEXT("Exactly two shared spines are authored"),
        Layout.SharedSpines.Num(), 2);
    TestFalse(TEXT("Shell never seeds stations"), Layout.bSeedStationsOnBeginPlay);
    TestEqual(TEXT("Shell policy is native-only"), Layout.ProvenancePolicy,
        ELBOneFactoryProvenancePolicy::NativeOnly);

    struct FExpectedDepartment
    {
        FName BayId;
        ELBOneFactoryDepartment Department;
        FVector Centre;
        FVector Size;
    };
    const FExpectedDepartment Expected[] = {
        {LBOneFactoryIds::PressBay(), ELBOneFactoryDepartment::Press,
            FVector(-14500.0f, 8000.0f, 1000.0f),
            FVector(32000.0f, 13000.0f, 2000.0f)},
        {LBOneFactoryIds::BodyBay(), ELBOneFactoryDepartment::Body,
            FVector(-11000.0f, -8500.0f, 1000.0f),
            FVector(18000.0f, 10000.0f, 2000.0f)},
        {LBOneFactoryIds::PaintBay(), ELBOneFactoryDepartment::Paint,
            FVector(10000.0f, -8500.0f, 1000.0f),
            FVector(22000.0f, 10000.0f, 2000.0f)},
        {LBOneFactoryIds::AssemblyBay(), ELBOneFactoryDepartment::Assembly,
            FVector(16500.0f, 8500.0f, 1000.0f),
            FVector(28000.0f, 12000.0f, 2000.0f)}
    };
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Expected); ++Index)
    {
        const FLBOneFactoryDepartmentBay& Actual = Layout.DepartmentBays[Index];
        TestEqual(*FString::Printf(TEXT("Department %d stable ID"), Index),
            Actual.BayId, Expected[Index].BayId);
        TestEqual(*FString::Printf(TEXT("Department %d role"), Index),
            Actual.Department, Expected[Index].Department);
        TestTrue(*FString::Printf(TEXT("Department %d stable centre"), Index),
            Actual.WorldTransform.GetLocation().Equals(Expected[Index].Centre, 0.01f));
        TestTrue(*FString::Printf(TEXT("Department %d stable size"), Index),
            Actual.SizeCm.Equals(Expected[Index].Size, 0.01f));
    }
    TestEqual(TEXT("Central logistics ID is stable"), Layout.SharedSpines[0].SpineId,
        LBOneFactoryIds::LogisticsSpine());
    TestEqual(TEXT("South service ID is stable"), Layout.SharedSpines[1].SpineId,
        LBOneFactoryIds::ServiceSpine());
    TestTrue(TEXT("Logistics spine is 610 x 12 m"),
        Layout.SharedSpines[0].SizeCm.Equals(FVector(61000.0f, 1200.0f, 400.0f),
            0.01f));
    TestTrue(TEXT("Service spine is 610 x 6 m"),
        Layout.SharedSpines[1].SizeCm.Equals(FVector(61000.0f, 600.0f, 400.0f),
            0.01f));
    TestEqual(TEXT("Logistics access remains a local 12 m handoff"),
        Layout.SharedSpines[0].MaximumReachCm, 1200.0f);
    TestEqual(TEXT("Shared service backbone reaches every department bay"),
        Layout.SharedSpines[1].MaximumReachCm, 30000.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryInvalidLayoutAndProvenanceTest,
    "LineBoss.OneFactory.Layout.InvalidLayoutProvenanceAndProtectedIsolation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryInvalidLayoutAndProvenanceTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    FString Reason;
    FLBOneFactoryLayoutDefinition Layout =
        ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
    Layout.DepartmentBays[1].WorldTransform.SetLocation(
        Layout.DepartmentBays[0].WorldTransform.GetLocation());
    TestFalse(TEXT("Overlapping departments fail structural validation"),
        ULBOneFactoryLayoutLibrary::ValidateLayout(Layout, Reason));

    Layout = ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
    Layout.bSeedStationsOnBeginPlay = true;
    TestFalse(TEXT("Station seeding fails the empty-shell contract"),
        ULBOneFactoryLayoutLibrary::ValidateLayout(Layout, Reason));

    Layout = ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
    Layout.ProvenancePolicy = ELBOneFactoryProvenancePolicy::Unspecified;
    TestFalse(TEXT("An unspecified shell provenance policy fails closed"),
        ULBOneFactoryLayoutLibrary::ValidateLayout(Layout, Reason));

    Layout = ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
    Swap(Layout.DepartmentBays[0], Layout.DepartmentBays[1]);
    TestTrue(TEXT("Reordered bays remain structurally safe"),
        ULBOneFactoryLayoutLibrary::ValidateLayout(Layout, Reason));
    TestFalse(TEXT("Reordered bays fail the stable authored layout contract"),
        ULBOneFactoryLayoutLibrary::ValidateMoorcrossWorksLayout(Layout, Reason));

    TestTrue(TEXT("Native procedural presentation is accepted"),
        ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::NativeProcedural,
            TEXT("/Game/LineBoss/Factory/OneFactory/v001/NativeHall"), Reason));
    TestTrue(TEXT("Verified native pre-Meshy work remains eligible"),
        ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::VerifiedPreMeshyNative,
            TEXT("/Game/LineBoss/PressShop/NativeRestored"), Reason));
    TestFalse(TEXT("Unspecified provenance fails closed"),
        ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::Unspecified, FString(), Reason));
    TestFalse(TEXT("External-generated provenance fails closed"),
        ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::ExternalGenerated,
            TEXT("/Game/LineBoss/Candidates/ExternalGenerated"), Reason));
    TestFalse(TEXT("A raw-download source is rejected even if labeled native"),
        ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::NativeOnly,
            ELBOneFactoryAssetProvenance::NativeAuthored,
            TEXT("C:/Downloads/Meshy_AI_fixture.glb"), Reason));

    // Spacecraft-era policy (2026-08-24 reversal): declared generated
    // provenance WITH a recorded source is accepted under GeneratedAllowed,
    // still rejected under NativeOnly, and never accepted without a record.
    TestTrue(TEXT("Generated provenance with a record passes GeneratedAllowed"),
        ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::GeneratedAllowed,
            ELBOneFactoryAssetProvenance::ExternalGenerated,
            TEXT("SourceAssets/Candidate/Spacecraft/Scout01_MeshyDelta_v001"),
            Reason));
    TestFalse(TEXT("Generated provenance without a record still fails closed"),
        ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::GeneratedAllowed,
            ELBOneFactoryAssetProvenance::ExternalGenerated,
            FString(), Reason));
    TestFalse(TEXT("Raw downloads stay barred even under GeneratedAllowed"),
        ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            ELBOneFactoryProvenancePolicy::GeneratedAllowed,
            ELBOneFactoryAssetProvenance::ExternalGenerated,
            TEXT("C:/Users/x/Downloads/raw.glb"), Reason));

    TestTrue(TEXT("Protected v913 package is rejected"),
        ULBOneFactoryLayoutLibrary::IsProtectedMapPackageName(
            TEXT("/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913")));
    TestTrue(TEXT("Protected restored Press package is rejected"),
        ULBOneFactoryLayoutLibrary::IsProtectedMapPackageName(
            TEXT("/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001")));
    TestTrue(TEXT("Protected isolated Paint prototype package is rejected"),
        ULBOneFactoryLayoutLibrary::IsProtectedMapPackageName(
            TEXT("/Game/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001")));
    TestFalse(TEXT("Dedicated OneFactory package is not protected legacy state"),
        ULBOneFactoryLayoutLibrary::IsProtectedMapPackageName(
            TEXT("/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryGameModeDefaultsTest,
    "LineBoss.OneFactory.PlayerShell.DefaultClassesAndNoLegacySpawnPolicy",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryGameModeDefaultsTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const ALBOneFactoryBootstrap* BootstrapDefaults =
        GetDefault<ALBOneFactoryBootstrap>();
    TestNotNull(TEXT("OneFactory bootstrap defaults exist"), BootstrapDefaults);
    if (BootstrapDefaults)
    {
        FString LayoutReason;
        TestTrue(TEXT("Bootstrap CDO carries the exact canonical shell layout"),
            ULBOneFactoryLayoutLibrary::ValidateMoorcrossWorksLayout(
                BootstrapDefaults->GetShellLayout(), LayoutReason));
        TestTrue(TEXT("Bootstrap CDO carries both native authority tags"),
            BootstrapDefaults->ActorHasTag(
                ALBOneFactoryBootstrap::GetBootstrapAuthorityTag())
            && BootstrapDefaults->ActorHasTag(
                ALBOneFactoryBootstrap::GetNativeOnlyTag()));
        TestFalse(TEXT("Bootstrap never ticks"),
            BootstrapDefaults->PrimaryActorTick.bCanEverTick);
    }
    const ALBOneFactoryGameMode* Defaults = GetDefault<ALBOneFactoryGameMode>();
    TestNotNull(TEXT("OneFactory game mode defaults exist"), Defaults);
    if (Defaults)
    {
        TestEqual(TEXT("OneFactory reuses the proven management pawn"),
            Defaults->DefaultPawnClass.Get(), ALBManagementPawn::StaticClass());
        // Versioned contract change, 2026-08-16: the shell now installs the
        // production-flow HUD directly, so the factory is legible without a
        // console swap. It derives from ALBControlRoomHUD, so every ControlRoom
        // surface is still drawn - which this asserts, rather than merely
        // dropping the old requirement.
        TestEqual(TEXT("OneFactory installs the production-flow HUD"),
            Defaults->HUDClass.Get(),
            ALBOneFactoryProductionHUD::StaticClass());
        TestTrue(TEXT("The production HUD still provides the ControlRoom surface"),
            ALBOneFactoryProductionHUD::StaticClass()->IsChildOf(
                ALBControlRoomHUD::StaticClass()));
        TestFalse(TEXT("OneFactory game mode never ticks"),
            Defaults->PrimaryActorTick.bCanEverTick);
        TestTrue(TEXT("GameMode authority tag is stable"),
            Defaults->ActorHasTag(ALBOneFactoryGameMode::GetGameModeAuthorityTag()));
    }
    TestEqual(TEXT("OneFactory derives directly from the engine game mode base"),
        ALBOneFactoryGameMode::StaticClass()->GetSuperClass(),
        AGameModeBase::StaticClass());
    TestFalse(TEXT("OneFactory does not run a legacy content bootstrap"),
        ALBOneFactoryGameMode::SpawnsLegacyFactoryContent());
    TestFalse(TEXT("OneFactory does not seed stations"),
        ALBOneFactoryGameMode::SeedsProductionStations());
    TestEqual(TEXT("Player-facing factory name is stable"),
        ALBOneFactoryGameMode::GetFactoryDisplayName(), FString(TEXT("Moorcross Works")));

    FString Reason;
    TestTrue(TEXT("Exact Ready shell passes the pure GameMode gate"),
        ALBOneFactoryGameMode::ValidateBootstrapContract(1,
            ELBOneFactoryBootstrapState::Ready, true, false, false, Reason));
    TestFalse(TEXT("Missing bootstrap fails the pure GameMode gate"),
        ALBOneFactoryGameMode::ValidateBootstrapContract(0,
            ELBOneFactoryBootstrapState::Ready, true, false, false, Reason));
    TestFalse(TEXT("Duplicate bootstraps fail the pure GameMode gate"),
        ALBOneFactoryGameMode::ValidateBootstrapContract(2,
            ELBOneFactoryBootstrapState::Ready, true, false, false, Reason));
    TestFalse(TEXT("Ready label cannot hide failed validation"),
        ALBOneFactoryGameMode::ValidateBootstrapContract(1,
            ELBOneFactoryBootstrapState::Ready, false, false, false, Reason));
    TestFalse(TEXT("Any future legacy spawn path fails the pure GameMode gate"),
        ALBOneFactoryGameMode::ValidateBootstrapContract(1,
            ELBOneFactoryBootstrapState::Ready, true, true, false, Reason));
    TestFalse(TEXT("Any future station seed path fails the pure GameMode gate"),
        ALBOneFactoryGameMode::ValidateBootstrapContract(1,
            ELBOneFactoryBootstrapState::Ready, true, false, true, Reason));

    TestTrue(TEXT("Legacy ALBGameMode is explicitly forbidden"),
        ULBOneFactoryLayoutLibrary::IsForbiddenLegacyActorClassName(TEXT("LBGameMode")));
    TestTrue(TEXT("Legacy envelope shutters are explicitly forbidden"),
        ULBOneFactoryLayoutLibrary::IsForbiddenLegacyActorClassName(
            TEXT("LBFactoryEnvelopeShutterActor")));
    TestTrue(TEXT("Old Coil AGV is explicitly forbidden"),
        ULBOneFactoryLayoutLibrary::IsForbiddenLegacyActorClassName(
            TEXT("LBCoilAGVController")));
    TestTrue(TEXT("Press-only support fleet is explicitly forbidden"),
        ULBOneFactoryLayoutLibrary::IsForbiddenLegacyActorClassName(
            TEXT("LBPressShopSupportFleetController")));
    TestFalse(TEXT("OneFactory GameMode is not mistaken for legacy ALBGameMode"),
        ULBOneFactoryLayoutLibrary::IsForbiddenLegacyActorClassName(
            TEXT("LBOneFactoryGameMode")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryLiveWorldContractTest,
    "LineBoss.OneFactory.World.LiveCardinalityOwnershipIdempotenceAndNoSeeding",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryLiveWorldContractTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryLiveWorldContractTest"));
    if (!TestNotNull(TEXT("Synthetic OneFactory world exists"), World)) return false;

    ALBOneFactoryBootstrap* Bootstrap = World->SpawnActor<ALBOneFactoryBootstrap>();
    ALBPressShopBuildAuthority* Authority =
        World->SpawnActor<ALBPressShopBuildAuthority>();
    if (!TestNotNull(TEXT("One map-peer bootstrap spawns for the fixture"), Bootstrap)
        || !TestNotNull(TEXT("One map-peer Press build authority spawns for the fixture"),
            Authority))
    {
        World->DestroyWorld(false);
        return false;
    }
    const FLBOneFactoryLayoutDefinition Layout =
        ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout();
    LBOneFactoryTestsPrivate::ConfigureCanonicalAuthority(*Authority, Layout);

    FString Reason;
    const FLBOneFactoryWorldAudit InitialAudit =
        ALBOneFactoryBootstrap::AuditWorld(World);
    TestTrue(TEXT("Exact live cardinality and ownership pass"),
        ULBOneFactoryLayoutLibrary::ValidateWorldAudit(InitialAudit, Reason));
    TestEqual(TEXT("Live world has one bootstrap"), InitialAudit.BootstrapCount, 1);
    TestEqual(TEXT("Live world has one Press build authority"),
        InitialAudit.PressBuildAuthorityCount, 1);
    TestTrue(TEXT("Map-peer actors share a level"),
        InitialAudit.bBootstrapAndAuthorityShareLevel);
    TestTrue(TEXT("Map-peer actors are not runtime-owned children"),
        InitialAudit.bBootstrapUnowned && InitialAudit.bPressBuildAuthorityUnowned);
    TestTrue(TEXT("Press authority carries the exact map-authored native identity"),
        InitialAudit.bPressBuildAuthorityMapTagged);
    TestTrue(TEXT("Map-authored authority matches the canonical arrays"),
        ULBOneFactoryLayoutLibrary::ValidatePressBuildAuthorityContract(
            Layout, Authority, Reason));
    TestTrue(TEXT("A representative train fits the Press bay and reaches the shared service backbone"),
        Authority->EvaluateTrainTransform(FTransform(FRotator::ZeroRotator,
            FVector(-14500.0f, 5108.0f, 0.0f), FVector::OneVector), Reason));
    Authority->BuildBays[0].Centre.X += 100.0f;
    TestFalse(TEXT("A one-metre authority datum drift fails closed"),
        ULBOneFactoryLayoutLibrary::ValidatePressBuildAuthorityContract(
            Layout, Authority, Reason));
    LBOneFactoryTestsPrivate::ConfigureCanonicalAuthority(*Authority, Layout);

    Bootstrap->DispatchBeginPlay();
    TestTrue(TEXT("Bootstrap BeginPlay validates the empty shell"),
        Bootstrap->HasValidShell());
    TestEqual(TEXT("Bootstrap binds the existing authority instead of spawning one"),
        Bootstrap->GetPressBuildAuthority(), Authority);
    const FString FirstStatus = Bootstrap->GetBootstrapStatus();
    TestTrue(TEXT("Repeated bootstrap validation is idempotently successful"),
        Bootstrap->ValidateAndLockShell(Reason));
    TestEqual(TEXT("Repeated validation retains the first stable status"),
        Bootstrap->GetBootstrapStatus(), FirstStatus);
    TestEqual(TEXT("Repeated validation does not duplicate the build authority"),
        LBOneFactoryTestsPrivate::CountLiveActors<ALBPressShopBuildAuthority>(World), 1);

    ALBOneFactoryGameMode* GameMode = World->SpawnActor<ALBOneFactoryGameMode>();
    TestNotNull(TEXT("Local OneFactory map override GameMode spawns"), GameMode);
    if (GameMode)
    {
        GameMode->DispatchBeginPlay();
        TestTrue(TEXT("GameMode accepts the already-validated bootstrap"),
            GameMode->HasValidOneFactoryShell());
        TestEqual(TEXT("GameMode binds the same bootstrap"),
            GameMode->GetOneFactoryBootstrap(), Bootstrap);
        TestTrue(TEXT("GameMode creates the exact runtime backbone after shell validation"),
            GameMode->HasValidRuntimeBackbone());
        TestEqual(TEXT("Startup creates one presentation-free production ledger"),
            LBOneFactoryTestsPrivate::CountLiveActors<
                ALBOneFactoryProductionFlowAuthority>(World), 1);
        TestEqual(TEXT("Startup creates one presentation-free runtime coordinator"),
            LBOneFactoryTestsPrivate::CountLiveActors<
                ALBOneFactoryRuntimeCoordinator>(World), 1);
    }

    TestEqual(TEXT("Startup seeds no Press train"),
        LBOneFactoryTestsPrivate::CountLiveActors<ALBPressTrainAStation>(World), 0);
    TestEqual(TEXT("Startup seeds no generic production machine"),
        LBOneFactoryTestsPrivate::CountLiveActors<ALBFactoryBuildMachine>(World), 0);
    TestEqual(TEXT("Startup seeds no Body line"),
        LBOneFactoryTestsPrivate::CountLiveActors<ALBBodyWeldLineActor>(World), 0);
    TestEqual(TEXT("Startup seeds no Paint line"),
        LBOneFactoryTestsPrivate::CountLiveActors<ALBECoatLineActor>(World), 0);
    TestEqual(TEXT("Startup seeds no storage or WIP"),
        LBOneFactoryTestsPrivate::CountLiveActors<ALBPressShopStorageZone>(World), 0);

    ALBOneFactoryBootstrap* Duplicate = World->SpawnActor<ALBOneFactoryBootstrap>();
    const FLBOneFactoryWorldAudit DuplicateAudit =
        ALBOneFactoryBootstrap::AuditWorld(World);
    TestFalse(TEXT("A duplicate bootstrap fails the live audit"),
        ULBOneFactoryLayoutLibrary::ValidateWorldAudit(DuplicateAudit, Reason));
    if (Duplicate) Duplicate->Destroy();

    Authority->SetOwner(Bootstrap);
    const FLBOneFactoryWorldAudit OwnedAudit = ALBOneFactoryBootstrap::AuditWorld(World);
    TestFalse(TEXT("A runtime-owned authority fails map-peer ownership"),
        ULBOneFactoryLayoutLibrary::ValidateWorldAudit(OwnedAudit, Reason));
    Authority->SetOwner(nullptr);

    Authority->Tags.Remove(ALBOneFactoryBootstrap::GetPressBuildAuthorityTag());
    const FLBOneFactoryWorldAudit UntaggedAudit =
        ALBOneFactoryBootstrap::AuditWorld(World);
    TestFalse(TEXT("An untagged runtime authority cannot masquerade as map-authored"),
        ULBOneFactoryLayoutLibrary::ValidateWorldAudit(UntaggedAudit, Reason));
    Authority->Tags.AddUnique(ALBOneFactoryBootstrap::GetPressBuildAuthorityTag());

    AActor* WIPFixture = World->SpawnActor<AActor>();
    if (WIPFixture) WIPFixture->Tags.Add(TEXT("LB.WIP.Test"));
    const FLBOneFactoryWorldAudit WIPAudit = ALBOneFactoryBootstrap::AuditWorld(World);
    TestFalse(TEXT("Any map-owned WIP identity fails the empty shell"),
        ULBOneFactoryLayoutLibrary::ValidateWorldAudit(WIPAudit, Reason));
    if (WIPFixture) WIPFixture->Destroy();

    AActor* LegacyFixture = World->SpawnActor<AActor>();
    if (LegacyFixture) LegacyFixture->Tags.Add(TEXT("LB.Vehicle.CoilAGV"));
    const FLBOneFactoryWorldAudit LegacyAudit =
        ALBOneFactoryBootstrap::AuditWorld(World);
    TestFalse(TEXT("A generic actor carrying the old Coil AGV identity fails isolation"),
        ULBOneFactoryLayoutLibrary::ValidateWorldAudit(LegacyAudit, Reason));
    if (LegacyFixture) LegacyFixture->Destroy();

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryFailClosedRetryTest,
    "LineBoss.OneFactory.World.FailedBeginPlayCannotBeReopenedByLateAuthority",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryFailClosedRetryTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryFailClosedRetryTest"));
    ALBOneFactoryBootstrap* Bootstrap = World
        ? World->SpawnActor<ALBOneFactoryBootstrap>() : nullptr;
    if (!TestNotNull(TEXT("Fail-closed fixture bootstrap exists"), Bootstrap))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    AddExpectedErrorPlain(
        TEXT("LINE_BOSS_ONEFACTORY_BOOTSTRAP_REJECTED reason=ONEFACTORY REQUIRES EXACTLY ONE MAP-AUTHORED PRESS BUILD AUTHORITY (FOUND 0)"),
        EAutomationExpectedErrorFlags::Contains, 1);
    Bootstrap->DispatchBeginPlay();
    TestEqual(TEXT("Missing map authority rejects BeginPlay"),
        Bootstrap->GetBootstrapState(), ELBOneFactoryBootstrapState::Rejected);
    TestFalse(TEXT("Rejected bootstrap is not a valid shell"),
        Bootstrap->HasValidShell());
    const FString RejectedStatus = Bootstrap->GetBootstrapStatus();

    ALBPressShopBuildAuthority* LateAuthority =
        World->SpawnActor<ALBPressShopBuildAuthority>();
    if (LateAuthority)
    {
        LBOneFactoryTestsPrivate::ConfigureCanonicalAuthority(*LateAuthority,
            ULBOneFactoryLayoutLibrary::MakeMoorcrossWorksShellLayout());
    }
    FString Reason;
    TestFalse(TEXT("A late runtime authority cannot reopen failed startup"),
        Bootstrap->ValidateAndLockShell(Reason));
    TestEqual(TEXT("Failure status remains stable after the retry"),
        Bootstrap->GetBootstrapStatus(), RejectedStatus);
    TestNull(TEXT("Rejected bootstrap never binds the late authority"),
        Bootstrap->GetPressBuildAuthority());

    World->DestroyWorld(false);
    return true;
}

#endif
