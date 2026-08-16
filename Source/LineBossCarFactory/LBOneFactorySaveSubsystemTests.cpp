#include "LBOneFactorySaveSubsystem.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "LBOneFactoryAssemblyStarterPresentationActor.h"
#include "LBOneFactoryBodyWeldStarterPresentationActor.h"
#include "LBOneFactoryPaintStarterPresentationActor.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "LBOneFactoryRuntimeCoordinator.h"
#include "Misc/AutomationTest.h"
#include "UObject/UnrealType.h"

namespace LBOneFactorySaveSubsystemTestsPrivate
{
    struct FFactoryFixture
    {
        UWorld* World = nullptr;
        ALBOneFactoryPressStarterLayoutAuthority* PressAuthority = nullptr;
        ALBOneFactoryPressStarterPresentationActor* PressPresentation = nullptr;
        ALBOneFactoryBodyWeldStarterLayoutAuthority* BodyAuthority = nullptr;
        ALBOneFactoryBodyWeldStarterPresentationActor* BodyPresentation = nullptr;
        ALBOneFactoryPaintStarterLayoutAuthority* PaintAuthority = nullptr;
        ALBOneFactoryPaintStarterPresentationActor* PaintPresentation = nullptr;
        ALBOneFactoryAssemblyStarterLayoutAuthority* AssemblyAuthority = nullptr;
        ALBOneFactoryAssemblyStarterPresentationActor* AssemblyPresentation = nullptr;
        ALBOneFactoryProductionFlowAuthority* ProductionAuthority = nullptr;
        ALBOneFactoryRuntimeCoordinator* RuntimeCoordinator = nullptr;
        ULBOneFactorySaveSubsystem* SaveSubsystem = nullptr;

        bool Create(const TCHAR* WorldName, FString& OutReason)
        {
            World = UWorld::CreateWorld(EWorldType::Game, false,
                FName(WorldName));
            if (!World)
            {
                OutReason = TEXT("TEST WORLD FAILED");
                return false;
            }
            PressAuthority = World->SpawnActor<
                ALBOneFactoryPressStarterLayoutAuthority>();
            PressPresentation = World->SpawnActor<
                ALBOneFactoryPressStarterPresentationActor>();
            BodyAuthority = World->SpawnActor<
                ALBOneFactoryBodyWeldStarterLayoutAuthority>();
            BodyPresentation = World->SpawnActor<
                ALBOneFactoryBodyWeldStarterPresentationActor>();
            PaintAuthority = World->SpawnActor<
                ALBOneFactoryPaintStarterLayoutAuthority>();
            PaintPresentation = World->SpawnActor<
                ALBOneFactoryPaintStarterPresentationActor>();
            AssemblyAuthority = World->SpawnActor<
                ALBOneFactoryAssemblyStarterLayoutAuthority>();
            AssemblyPresentation = World->SpawnActor<
                ALBOneFactoryAssemblyStarterPresentationActor>();
            ProductionAuthority = World->SpawnActor<
                ALBOneFactoryProductionFlowAuthority>();
            RuntimeCoordinator = World->SpawnActor<
                ALBOneFactoryRuntimeCoordinator>();
            SaveSubsystem = World->GetSubsystem<ULBOneFactorySaveSubsystem>();
            if (!PressAuthority || !PressPresentation
                || !BodyAuthority || !BodyPresentation
                || !PaintAuthority || !PaintPresentation
                || !AssemblyAuthority || !AssemblyPresentation
                || !ProductionAuthority || !RuntimeCoordinator || !SaveSubsystem)
            {
                OutReason = TEXT("TEST FACTORY ACTOR CREATION FAILED");
                return false;
            }

            return PressPresentation->ConfigureFromLayout(
                    PressAuthority->CaptureLayout(), OutReason)
                && BodyPresentation->ConfigureFromLayout(
                    BodyAuthority->CaptureLayout(), OutReason)
                && PaintPresentation->ConfigureFromLayout(
                    PaintAuthority->CaptureLayout(), OutReason)
                && AssemblyPresentation->ConfigureFromLayout(
                    AssemblyAuthority->CaptureLayout(), OutReason);
        }

        void Destroy()
        {
            if (World) World->DestroyWorld(false);
            *this = FFactoryFixture();
        }
    };

    FLBOneFactoryVehicleUnitState MakePressWIPUnit()
    {
        FLBOneFactoryVehicleUnitState Unit;
        Unit.Version = 1;
        Unit.UnitId = TEXT("CAIRNWELL_2040-000001");
        Unit.BuildOrderId = TEXT("ORDER-SAVE-0001");
        Unit.VehicleModelId = TEXT("CAIRNWELL_2040");
        Unit.PaintProgrammeId = TEXT("PAINT-CAIRNWELL-TEAL");
        Unit.PaintColourId = TEXT("CAIRNWELL-TEAL");
        Unit.Stage = ELBOneFactoryVehicleStage::InboundCoil;
        Unit.Department = ELBOneFactoryDepartment::Press;
        Unit.CurrentStationId = TEXT("PRESS-INBOUND");
        Unit.QualityState = ELBOneFactoryVehicleQualityState::NotInspected;
        Unit.SourceMaterialUnitIds.Add(TEXT("COIL-LOT-SAVE-0001"));
        return Unit;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactorySaveSchemaIntegrityTest,
    "LineBoss.OneFactory.Save.SchemaIsolationAndDuplicateIdentityRejection",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactorySaveSchemaIntegrityTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    FLBOneFactorySaveState State =
        ULBOneFactorySaveGame::MakeCanonicalEmptyState();
    FString Reason;
    TestTrue(TEXT("Canonical whole-factory state validates"),
        ULBOneFactorySaveGame::ValidateState(State, Reason));
    TestTrue(TEXT("OneFactory disk slot is isolated from the campaign slot"),
        ULBOneFactorySaveSubsystem::GetIsolatedSlotName()
            != TEXT("LB_PRESS_SHOP_CAMPAIGN"));

    bool bContainsPresentationProxyField = false;
    for (TFieldIterator<FProperty> It(FLBOneFactorySaveState::StaticStruct());
        It; ++It)
    {
        const FString Name = It->GetName().ToLower();
        bContainsPresentationProxyField |= Name.Contains(TEXT("presentation"))
            || Name.Contains(TEXT("proxy"))
            || It->IsA<FObjectPropertyBase>();
    }
    TestFalse(TEXT("Save schema cannot persist presentation proxy actors"),
        bContainsPresentationProxyField);

    State.ProductionLedger.Units.Add(
        LBOneFactorySaveSubsystemTestsPrivate::MakePressWIPUnit());
    State.ProductionLedger.NextVehicleSerial = 2;
    State.ProductionLedger.Revision = 1;
    State.PayloadRevision = 1;
    State.PressLayout.Stations[0].ActiveOrReservedUnitIds.Add(
        State.ProductionLedger.Units[0].UnitId);
    State.BodyWeldLayout.Stations[0].ActiveOrReservedUnitIds.Add(
        State.ProductionLedger.Units[0].UnitId);
    TestFalse(TEXT("One logical vehicle cannot be duplicated across station WIP"),
        ULBOneFactorySaveGame::ValidateState(State, Reason));
    TestTrue(TEXT("Duplicate WIP rejection is explicit"),
        Reason.Contains(TEXT("RESERVED MORE THAN ONCE")));

    State = ULBOneFactorySaveGame::MakeCanonicalEmptyState();
    const FLBOneFactoryVehicleUnitState Unit =
        LBOneFactorySaveSubsystemTestsPrivate::MakePressWIPUnit();
    State.ProductionLedger.Units.Add(Unit);
    State.ProductionLedger.Units.Add(Unit);
    State.ProductionLedger.NextVehicleSerial = 2;
    TestFalse(TEXT("Duplicate ledger UnitIds reject before restore"),
        ULBOneFactorySaveGame::ValidateState(State, Reason));
    TestTrue(TEXT("Duplicate UnitId rejection comes from the genealogy ledger"),
        Reason.Contains(TEXT("DUPLICATED")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactorySaveExactPairsTest,
    "LineBoss.OneFactory.Save.ExactAuthorityPresentationPairsAndCapture",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactorySaveExactPairsTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactorySaveSubsystemTestsPrivate;
    FString Reason;
    FFactoryFixture Fixture;
    if (!TestTrue(TEXT("Complete visual/data factory fixture configures"),
            Fixture.Create(TEXT("LBOneFactorySaveExactPairsTest"), Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }

    FLBOneFactorySaveState Captured;
    TestTrue(TEXT("Exact five authorities and four pairs capture in memory"),
        Fixture.SaveSubsystem->CaptureCurrentFactory(Captured, Reason));
    TestEqual(TEXT("Capture contains the stable factory identity"),
        Captured.FactoryId, ULBOneFactorySaveGame::GetFactoryId());

    ALBOneFactoryPressStarterPresentationActor* Duplicate =
        Fixture.World->SpawnActor<ALBOneFactoryPressStarterPresentationActor>();
    TestNotNull(TEXT("Duplicate Press presentation fixture exists"), Duplicate);
    TestFalse(TEXT("Duplicate presentation pair rejects capture"),
        Fixture.SaveSubsystem->CaptureCurrentFactory(Captured, Reason));
    TestTrue(TEXT("Duplicate pair count is visible in the reason"),
        Reason.Contains(TEXT("EXACTLY ONE PRESS PRESENTATION PAIR; FOUND 2")));
    Fixture.Destroy();

    UWorld* MissingWorld = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactorySaveMissingPairTest"));
    if (MissingWorld)
    {
        MissingWorld->SpawnActor<ALBOneFactoryPressStarterLayoutAuthority>();
        ULBOneFactorySaveSubsystem* MissingSubsystem =
            MissingWorld->GetSubsystem<ULBOneFactorySaveSubsystem>();
        TestNotNull(TEXT("Save subsystem exists in incomplete factory"),
            MissingSubsystem);
        if (MissingSubsystem)
        {
            TestFalse(TEXT("Missing Press presentation pair rejects capture"),
                MissingSubsystem->CaptureCurrentFactory(Captured, Reason));
            TestTrue(TEXT("Missing pair count is explicit"),
                Reason.Contains(TEXT("PRESS PRESENTATION PAIR; FOUND 0")));
        }
        MissingWorld->DestroyWorld(false);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactorySaveTransactionalRollbackTest,
    "LineBoss.OneFactory.Save.InMemoryRestoreAndPostCommitRollback",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactorySaveTransactionalRollbackTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    using namespace LBOneFactorySaveSubsystemTestsPrivate;
    FString Reason;
    FFactoryFixture Fixture;
    if (!TestTrue(TEXT("Transactional restore fixture configures"),
            Fixture.Create(TEXT("LBOneFactorySaveRollbackTest"), Reason)))
    {
        AddError(Reason);
        Fixture.Destroy();
        return false;
    }

    FLBOneFactorySaveState Initial;
    TestTrue(TEXT("Initial rollback state captures"),
        Fixture.SaveSubsystem->CaptureCurrentFactory(Initial, Reason));

    FLBOneFactorySaveState FirstCommit = Initial;
    ++FirstCommit.PressLayout.Revision;
    ++FirstCommit.BodyWeldLayout.Revision;
    ++FirstCommit.PaintLayout.Revision;
    ++FirstCommit.AssemblyLayout.Revision;
    TestTrue(TEXT("Valid state restores all authorities and presentation pairs"),
        Fixture.SaveSubsystem->RestoreFactoryState(FirstCommit, Reason));

    FLBOneFactorySaveState BeforeForcedFailure;
    TestTrue(TEXT("Committed state captures as next rollback boundary"),
        Fixture.SaveSubsystem->CaptureCurrentFactory(
            BeforeForcedFailure, Reason));
    TestEqual(TEXT("Press presentation follows committed revision"),
        Fixture.PressPresentation->GetConfiguredLayoutRevision(),
        FirstCommit.PressLayout.Revision);
    TestEqual(TEXT("Body presentation follows committed revision"),
        Fixture.BodyPresentation->GetConfiguredLayoutRevision(),
        FirstCommit.BodyWeldLayout.Revision);

    // A hidden Body/Weld presentation counts every instance yet renders
    // nothing: the capture preflight must fail closed on it.
    Fixture.BodyPresentation->SetActorHiddenInGame(true);
    FLBOneFactorySaveState HiddenCapture;
    TestFalse(TEXT("Capture rejects a hidden Body/Weld presentation"),
        Fixture.SaveSubsystem->CaptureCurrentFactory(HiddenCapture, Reason));
    Fixture.BodyPresentation->SetActorHiddenInGame(false);
    FLBOneFactorySaveState UnhiddenCapture;
    TestTrue(TEXT("Capture succeeds once the presentation is visible again"),
        Fixture.SaveSubsystem->CaptureCurrentFactory(
            UnhiddenCapture, Reason));

    FLBOneFactorySaveState InvalidPreflight = FirstCommit;
    InvalidPreflight.SchemaVersion = 99;
    TestFalse(TEXT("Invalid incoming schema rejects before live mutation"),
        Fixture.SaveSubsystem->RestoreFactoryState(InvalidPreflight, Reason));
    FLBOneFactorySaveState AfterPreflightRejection;
    TestTrue(TEXT("Factory remains coherent after preflight rejection"),
        Fixture.SaveSubsystem->CaptureCurrentFactory(
            AfterPreflightRejection, Reason));
    TestEqual(TEXT("Preflight rejection preserves Press revision"),
        AfterPreflightRejection.PressLayout.Revision,
        BeforeForcedFailure.PressLayout.Revision);
    TestEqual(TEXT("Preflight rejection preserves Assembly revision"),
        AfterPreflightRejection.AssemblyLayout.Revision,
        BeforeForcedFailure.AssemblyLayout.Revision);

    FLBOneFactorySaveState FailedCommit = FirstCommit;
    ++FailedCommit.PressLayout.Revision;
    ++FailedCommit.BodyWeldLayout.Revision;
    ++FailedCommit.PaintLayout.Revision;
    ++FailedCommit.AssemblyLayout.Revision;
    ++FailedCommit.ProductionLedger.Revision;
    FailedCommit.PayloadRevision = FailedCommit.ProductionLedger.Revision;
    FailedCommit.ProductionLedger.bLinePaused =
        !BeforeForcedFailure.ProductionLedger.bLinePaused;
    Fixture.SaveSubsystem->SetForcePresentationFailureForTests(true);
    TestFalse(TEXT("Forced failure occurs after the data commit boundary"),
        Fixture.SaveSubsystem->RestoreFactoryState(FailedCommit, Reason));
    Fixture.SaveSubsystem->SetForcePresentationFailureForTests(false);
    TestTrue(TEXT("Failure reports successful data and presentation rollback"),
        Reason.Contains(TEXT("DATA AND PRESENTATION ROLLED BACK")));

    FLBOneFactorySaveState AfterRollback;
    TestTrue(TEXT("Rolled-back factory is immediately recapturable"),
        Fixture.SaveSubsystem->CaptureCurrentFactory(AfterRollback, Reason));
    TestEqual(TEXT("Press data revision rolled back exactly"),
        AfterRollback.PressLayout.Revision,
        BeforeForcedFailure.PressLayout.Revision);
    TestEqual(TEXT("Body data revision rolled back exactly"),
        AfterRollback.BodyWeldLayout.Revision,
        BeforeForcedFailure.BodyWeldLayout.Revision);
    TestEqual(TEXT("Paint data revision rolled back exactly"),
        AfterRollback.PaintLayout.Revision,
        BeforeForcedFailure.PaintLayout.Revision);
    TestEqual(TEXT("Assembly data revision rolled back exactly"),
        AfterRollback.AssemblyLayout.Revision,
        BeforeForcedFailure.AssemblyLayout.Revision);
    TestEqual(TEXT("Production authority revision rolled back exactly"),
        AfterRollback.ProductionLedger.Revision,
        BeforeForcedFailure.ProductionLedger.Revision);
    TestEqual(TEXT("Production runtime gate rolled back exactly"),
        AfterRollback.ProductionLedger.bLinePaused,
        BeforeForcedFailure.ProductionLedger.bLinePaused);
    TestEqual(TEXT("Press presentation was rebuilt from rollback snapshot"),
        Fixture.PressPresentation->GetConfiguredLayoutRevision(),
        BeforeForcedFailure.PressLayout.Revision);
    TestEqual(TEXT("Body presentation was rebuilt from rollback snapshot"),
        Fixture.BodyPresentation->GetConfiguredLayoutRevision(),
        BeforeForcedFailure.BodyWeldLayout.Revision);
    TestEqual(TEXT("Paint presentation was rebuilt from rollback snapshot"),
        Fixture.PaintPresentation->GetConfiguredLayoutRevision(),
        BeforeForcedFailure.PaintLayout.Revision);
    TestEqual(TEXT("Assembly presentation was rebuilt from rollback snapshot"),
        Fixture.AssemblyPresentation->GetConfiguredLayoutRevision(),
        BeforeForcedFailure.AssemblyLayout.Revision);
    Fixture.Destroy();
    return true;
}

#endif
