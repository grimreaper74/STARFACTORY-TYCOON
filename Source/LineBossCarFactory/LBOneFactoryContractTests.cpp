#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryProductionFlow.h"
#include "LBVehiclePanelCatalog.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryContractLifecycleTest,
    "LineBoss.OneFactory.ProductionFlow.ContractSeedExpiryAndIdempotency",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryContractLifecycleTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBContractWorld")));
    ALBOneFactoryProductionFlowAuthority* Production =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    if (!TestNotNull(TEXT("production authority spawns"), Production))
    {
        World->DestroyWorld(false);
        return false;
    }
    FString Reason;

    // Validation: no id, no quantity, no price -> rejected.
    FLBOneFactoryVehicleContract Bad;
    TestFalse(TEXT("an empty contract is rejected"),
        Production->AddVehicleContract(Bad, Reason));

    FLBOneFactoryVehicleContract UnknownProgramme;
    UnknownProgramme.ContractId = TEXT("CON_UNKNOWN_PROGRAMME");
    UnknownProgramme.VehicleModelId = TEXT("UNKNOWN_PROGRAMME");
    UnknownProgramme.Quantity = 1;
    UnknownProgramme.PricePerVehiclePence = 100;
    TestFalse(TEXT("a contract cannot advertise an unregistered vehicle programme"),
        Production->AddVehicleContract(UnknownProgramme, Reason));

    // The starter chain seeds once and is idempotent.
    TestTrue(Reason, Production->SeedStarterContracts(Reason));
    TestTrue(Reason, Production->SeedStarterContracts(Reason));
    FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    TestEqual(TEXT("three starter contracts, seeded once"),
        Ledger.Contracts.Num(), 3);
    TestEqual(TEXT("starter contracts open"),
        Ledger.Contracts[0].State, ELBOneFactoryContractState::Open);
    TestTrue(TEXT("starter contracts use the runtime Cairnwell identity"),
        Ledger.Contracts[0].VehicleModelId == TEXT("CAIRNWELL_2040")
        && Ledger.Contracts[1].VehicleModelId == TEXT("CAIRNWELL_2040")
        && Ledger.Contracts[2].VehicleModelId == TEXT("CAIRNWELL_2040"));

    FLBOneFactoryProductionLedgerState InvalidSettlement = Ledger;
    ++InvalidSettlement.Contracts[0].DispatchedCount;
    TestFalse(TEXT("a contract count without a dispatched unit fails closed"),
        ULBOneFactoryProductionFlowLibrary::ValidateLedger(
            InvalidSettlement, Reason));

    FLBOneFactoryProductionLedgerState UnknownProgrammeLedger = Ledger;
    UnknownProgrammeLedger.Contracts[0].VehicleModelId = TEXT("UNKNOWN_PROGRAMME");
    TestFalse(TEXT("a restored ledger cannot retain a contract for an unknown programme"),
        ULBOneFactoryProductionFlowLibrary::ValidateLedger(
            UnknownProgrammeLedger, Reason));

    // Deadlines: the 4-hour contract expires when the clock passes it;
    // the 10 and 20 hour contracts stay open.
    TestTrue(Reason, Production->AdvanceSimulationClock(5.0f * 3600.0f,
        Reason));
    TestEqual(TEXT("exactly one contract expires at 5h"),
        Production->SweepContractDeadlines(Reason), 1);
    TestEqual(TEXT("sweep is idempotent"),
        Production->SweepContractDeadlines(Reason), 0);
    Ledger = Production->CaptureLedger();
    TestEqual(TEXT("first contract expired"),
        Ledger.Contracts[0].State, ELBOneFactoryContractState::Expired);
    TestEqual(TEXT("second contract still open"),
        Ledger.Contracts[1].State, ELBOneFactoryContractState::Open);

    // Contracts survive a capture/restore round trip.
    ALBOneFactoryProductionFlowAuthority* Restored =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    if (TestNotNull(TEXT("second authority spawns"), Restored))
    {
        TestTrue(Reason, Restored->RestoreLedger(Ledger, Reason));
        TestEqual(TEXT("restored contracts intact"),
            Restored->CaptureLedger().Contracts.Num(), 3);
    }

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryVehicleRecipeCatalogueTest,
    "LineBoss.OneFactory.ProductionFlow.VehicleRecipeCatalogueKeepsIdentityAndBOMTogether",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryVehicleRecipeCatalogueTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const TArray<FLBVehicleModelRecipe>& Recipes = LBVehicleModelCatalog::GetRecipes();
    TestTrue(TEXT("the recipe catalogue has a selectable vehicle programme"), !Recipes.IsEmpty());
    TestEqual(TEXT("the default programme is stable gameplay identity"),
        LBVehicleModelCatalog::GetDefaultModelId(), FName(TEXT("CAIRNWELL_2040")));
    TestTrue(TEXT("the development programme is registered"),
        LBVehicleModelCatalog::IsKnownModel(TEXT("CAIRNWELL_2040")));
    TestFalse(TEXT("an unregistered programme is rejected by the catalogue"),
        LBVehicleModelCatalog::IsKnownModel(TEXT("UNREGISTERED_MODEL")));

    const FLBVehicleModelRecipe* Recipe = LBVehicleModelCatalog::Find(TEXT("CAIRNWELL_2040"));
    if (!TestNotNull(TEXT("the registered programme resolves to one recipe"), Recipe))
    {
        return false;
    }
    TestEqual(TEXT("development lifecycle is separate from model identity"),
        Recipe->RecipeRevisionId, FName(TEXT("CAIRNWELL_2040_DEVELOPMENT_RECIPE_V001")));
    TestTrue(TEXT("the current visual status remains explicitly development"),
        Recipe->bDevelopmentVisual);
    TestTrue(TEXT("the full panel set has a separate validated development authority"),
        Recipe->bPanelGeometryValidated);
    TestTrue(TEXT("the built-in programme is eligible for contracts and shop changeovers"),
        LBVehicleModelCatalog::IsProductionReady(*Recipe));
    TestEqual(TEXT("panel geometry revision is separate from the car body authority"),
        Recipe->PanelGeometryAuthorityId,
        FName(TEXT("Cairnwell2040NativeWIPPanelArchetypes_v001")));
    TestEqual(TEXT("the active development recipe names the cooked native vehicle representation"),
        Recipe->GeometryAuthorityId,
        FName(TEXT("Cairnwell2040NativeWIPVehicleRepresentation_v001")));
    TestEqual(TEXT("the programme owns its fallback spot value in the recipe"),
        Recipe->DefaultRevenuePence, int64(3200000));
    TestEqual(TEXT("the recipe owns the full 11-panel Cairnwell BOM"),
        Recipe->RequiredPanels.Num(), 11);
    TestEqual(TEXT("the HUD/production panel lookup comes from the recipe BOM"),
        LBVehicleModelCatalog::GetPanels(Recipe->ModelId).Num(), Recipe->RequiredPanels.Num());
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryDevelopmentRecipeRegistrationTest,
    "LineBoss.OneFactory.ProductionFlow.VehicleRecipeCatalogueRegistersAdditionalDevelopmentProgrammes",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryDevelopmentRecipeRegistrationTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const FName ProgrammeId(TEXT("NORTHSTAR_DEVELOPMENT"));
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ProgrammeId);

    FLBVehicleModelRecipe Programme;
    Programme.ModelId = ProgrammeId;
    Programme.DisplayName = TEXT("Northstar development programme");
    Programme.RecipeRevisionId = TEXT("NORTHSTAR_DEVELOPMENT_RECIPE_V001");
    Programme.PaintRouteProfileId = TEXT("PAINT_ROUTE_EDCOAT_VISIBLE_V001");
    Programme.GeometryAuthorityId = TEXT("NorthstarDevelopmentGeometry_V001");
    Programme.PanelGeometryAuthorityId = TEXT("NorthstarDevelopmentPanels_V001");
    Programme.BaseKitTypeId = TEXT("NORTHSTAR_DEVELOPMENT_BIW_BASE_KIT");
    Programme.bDevelopmentVisual = true;
    Programme.bPanelGeometryValidated = false;
    Programme.DefaultRevenuePence = 2750000;
    Programme.RequiredPanels = {
        { TEXT("NORTHSTAR_HOOD"), TEXT("Northstar hood"), ELBPanelHandedness::None,
            12, FVector(160.0f, 140.0f, 20.0f), NAME_None },
        { TEXT("NORTHSTAR_DOOR_LEFT"), TEXT("Northstar door left"), ELBPanelHandedness::Left,
            16, FVector(120.0f, 18.0f, 110.0f), NAME_None }
    };

    FString Reason;
    TestTrue(TEXT("an additional development programme registers without a Cairnwell branch"),
        LBVehicleModelCatalog::RegisterDevelopmentRecipe(Programme, Reason));
    TestTrue(TEXT("the additional programme resolves by its stable model ID"),
        LBVehicleModelCatalog::IsKnownModel(ProgrammeId));
    TestEqual(TEXT("the additional programme exposes its own two-panel BOM"),
        LBVehicleModelCatalog::GetPanels(ProgrammeId).Num(), 2);
    TestTrue(TEXT("the generic panel gate accepts the additional programme BOM"),
        LBVehicleModelCatalog::IsApprovedStampedPanelRecipe(
            ProgrammeId, TEXT("NORTHSTAR_HOOD")));
    FName ParsedModelId;
    FName ParsedPanelTypeId;
    TestTrue(TEXT("press panel identity resolves through the model registry rather than Cairnwell"),
        LBVehicleModelCatalog::ParsePressedPanelUnitId(
            TEXT("PTB-PANEL-NORTHSTAR_DEVELOPMENT-NORTHSTAR_HOOD-000001"),
            ParsedModelId, ParsedPanelTypeId));
    TestEqual(TEXT("parsed panel identity retains the alternate model"),
        ParsedModelId, ProgrammeId);
    TestEqual(TEXT("parsed panel identity retains the alternate panel family"),
        ParsedPanelTypeId, FName(TEXT("NORTHSTAR_HOOD")));
    TestFalse(TEXT("a staged programme cannot be selected for production or changeover"),
        LBVehicleModelCatalog::IsProductionReady(Programme));
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBUnvalidatedProgrammeWorld"));
    ALBOneFactoryProductionFlowAuthority* Production =
        World ? World->SpawnActor<ALBOneFactoryProductionFlowAuthority>() : nullptr;
    FLBOneFactoryVehicleContract Contract;
    Contract.ContractId = TEXT("CON_UNVALIDATED_PROGRAMME");
    Contract.VehicleModelId = ProgrammeId;
    Contract.Quantity = 1;
    Contract.PricePerVehiclePence = 100;
    TestNotNull(TEXT("production authority spawns for the eligibility gate"), Production);
    TestFalse(TEXT("a staged recipe cannot become a live contract before panel validation"),
        Production && Production->AddVehicleContract(Contract, Reason));
    if (World) World->DestroyWorld(false);
    TestFalse(TEXT("duplicate model IDs are rejected"),
        LBVehicleModelCatalog::RegisterDevelopmentRecipe(Programme, Reason));
    TestTrue(TEXT("the temporary development programme can be removed cleanly"),
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ProgrammeId));
    TestFalse(TEXT("removed development programme no longer resolves"),
        LBVehicleModelCatalog::IsKnownModel(ProgrammeId));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryStarterContractsUseRegisteredProgrammesTest,
    "LineBoss.OneFactory.ProductionFlow.StarterContractsRotateRegisteredProgrammes",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryStarterContractsUseRegisteredProgrammesTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    const FName ProgrammeId(TEXT("OXFORD_DEVELOPMENT"));
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ProgrammeId);

    FLBVehicleModelRecipe Programme;
    Programme.ModelId = ProgrammeId;
    Programme.DisplayName = TEXT("Oxford development programme");
    Programme.RecipeRevisionId = TEXT("OXFORD_DEVELOPMENT_RECIPE_V001");
    Programme.PaintRouteProfileId = TEXT("PAINT_ROUTE_EDCOAT_VISIBLE_V001");
    Programme.GeometryAuthorityId = TEXT("OxfordDevelopmentGeometry_V001");
    Programme.PanelGeometryAuthorityId = TEXT("OxfordDevelopmentPanels_V001");
    Programme.BaseKitTypeId = TEXT("OXFORD_DEVELOPMENT_BIW_BASE_KIT");
    Programme.bDevelopmentVisual = true;
    Programme.bPanelGeometryValidated = true;
    Programme.DefaultRevenuePence = 2650000;
    Programme.RequiredPanels = {
        { TEXT("OXFORD_HOOD"), TEXT("Oxford hood"), ELBPanelHandedness::None,
            12, FVector(160.0f, 140.0f, 20.0f), NAME_None }
    };
    FString Reason;
    if (!TestTrue(TEXT("second programme registers before contract seeding"),
            LBVehicleModelCatalog::RegisterDevelopmentRecipe(Programme, Reason)))
    {
        return false;
    }

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBMultiModelStarterContractWorld"));
    ALBOneFactoryProductionFlowAuthority* Production =
        World ? World->SpawnActor<ALBOneFactoryProductionFlowAuthority>() : nullptr;
    bool bPassed = TestNotNull(TEXT("multi-model production authority spawns"), Production);
    if (bPassed)
    {
        bPassed = TestTrue(Reason, Production->SeedStarterContracts(Reason));
        const FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
        bPassed &= TestEqual(TEXT("starter ladder keeps its three contracts"),
            Ledger.Contracts.Num(), 3);
        bPassed &= TestEqual(TEXT("second starter contract advertises the second programme"),
            Ledger.Contracts.IsValidIndex(1) ? Ledger.Contracts[1].VehicleModelId : NAME_None,
            ProgrammeId);
        bPassed &= TestEqual(TEXT("third contract deterministically cycles back to default"),
            Ledger.Contracts.IsValidIndex(2) ? Ledger.Contracts[2].VehicleModelId : NAME_None,
            FName(TEXT("CAIRNWELL_2040")));
    }
    if (World) World->DestroyWorld(false);
    TestTrue(TEXT("temporary programme unregisters after contract test"),
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ProgrammeId));
    return bPassed;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactorySoftFailureTest,
    "LineBoss.OneFactory.ProductionFlow.SoftFailureWarnsRescuesAndCostsReputation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactorySoftFailureTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBSoftFailureWorld")));
    ALBOneFactoryProductionFlowAuthority* Production =
        World->SpawnActor<ALBOneFactoryProductionFlowAuthority>();
    if (!TestNotNull(TEXT("production authority spawns"), Production))
    {
        World->DestroyWorld(false);
        return false;
    }
    FString Reason;

    TestEqual(TEXT("reputation starts at 100"),
        Production->CaptureLedger().ReputationScore, 100);

    // Healthy -> Warning -> Emergency, all soft.
    TestTrue(Reason, Production->ApplyFinancialPolicy(100000000, Reason));
    TestEqual(TEXT("healthy above the floor"),
        Production->CaptureLedger().FinancialState,
        ELBOneFactoryFinancialState::Healthy);
    TestTrue(Reason, Production->ApplyFinancialPolicy(10000000, Reason));
    TestEqual(TEXT("warning below the floor"),
        Production->CaptureLedger().FinancialState,
        ELBOneFactoryFinancialState::Warning);

    TestTrue(Reason, Production->ApplyFinancialPolicy(-500000, Reason));
    FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
    TestEqual(TEXT("emergency below zero"),
        Ledger.FinancialState, ELBOneFactoryFinancialState::Emergency);
    TestEqual(TEXT("one rescue contract offered"), Ledger.Contracts.Num(), 1);
    TestTrue(TEXT("rescue is flagged emergency"),
        Ledger.Contracts[0].bEmergency);
    TestEqual(TEXT("rescue costs ten reputation"),
        Ledger.ReputationScore, 90);

    // Still in crisis: the open rescue is not duplicated.
    TestTrue(Reason, Production->ApplyFinancialPolicy(-800000, Reason));
    Ledger = Production->CaptureLedger();
    TestEqual(TEXT("no second rescue while one is open"),
        Ledger.Contracts.Num(), 1);
    TestEqual(TEXT("reputation charged once"), Ledger.ReputationScore, 90);

    // Expiring the rescue costs standing and permits a fresh offer.
    TestTrue(Reason, Production->AdvanceSimulationClock(7.0f * 3600.0f,
        Reason));
    TestEqual(TEXT("rescue expires past its deadline"),
        Production->SweepContractDeadlines(Reason), 1);
    TestTrue(Reason, Production->ApplyFinancialPolicy(-800000, Reason));
    Ledger = Production->CaptureLedger();
    TestEqual(TEXT("a second rescue can then be offered"),
        Ledger.Contracts.Num(), 2);
    TestEqual(TEXT("expiry and second rescue both cost reputation"),
        Ledger.ReputationScore, 75);

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryEmergencyContractsUseRegisteredProgrammesTest,
    "LineBoss.OneFactory.ProductionFlow.EmergencyContractsRotateRegisteredProgrammes",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryEmergencyContractsUseRegisteredProgrammesTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    const FName ProgrammeId(TEXT("EMERGENCY_DEVELOPMENT"));
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ProgrammeId);
    FLBVehicleModelRecipe Programme;
    Programme.ModelId = ProgrammeId;
    Programme.DisplayName = TEXT("Emergency development programme");
    Programme.RecipeRevisionId = TEXT("EMERGENCY_DEVELOPMENT_RECIPE_V001");
    Programme.PaintRouteProfileId = TEXT("PAINT_ROUTE_EDCOAT_VISIBLE_V001");
    Programme.GeometryAuthorityId = TEXT("EmergencyDevelopmentGeometry_V001");
    Programme.PanelGeometryAuthorityId = TEXT("EmergencyDevelopmentPanels_V001");
    Programme.BaseKitTypeId = TEXT("EMERGENCY_DEVELOPMENT_BIW_BASE_KIT");
    Programme.bDevelopmentVisual = true;
    Programme.bPanelGeometryValidated = true;
    Programme.DefaultRevenuePence = 2500000;
    Programme.RequiredPanels = {
        { TEXT("EMERGENCY_HOOD"), TEXT("Emergency hood"), ELBPanelHandedness::None,
            12, FVector(160.0f, 140.0f, 20.0f), NAME_None }
    };
    FString Reason;
    if (!TestTrue(TEXT("emergency test programme registers"),
            LBVehicleModelCatalog::RegisterDevelopmentRecipe(Programme, Reason)))
    {
        return false;
    }

    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBMultiModelEmergencyContractWorld"));
    ALBOneFactoryProductionFlowAuthority* Production = World
        ? World->SpawnActor<ALBOneFactoryProductionFlowAuthority>() : nullptr;
    bool bPassed = TestNotNull(TEXT("emergency production authority spawns"), Production);
    if (bPassed)
    {
        bPassed = TestTrue(Reason, Production->ApplyFinancialPolicy(-1, Reason));
        FLBOneFactoryProductionLedgerState Ledger = Production->CaptureLedger();
        bPassed &= TestEqual(TEXT("first emergency offer uses the first registered programme"),
            Ledger.Contracts[0].VehicleModelId, FName(TEXT("CAIRNWELL_2040")));
        bPassed &= TestTrue(Reason, Production->AdvanceSimulationClock(7.0f * 3600.0f, Reason));
        Production->SweepContractDeadlines(Reason);
        bPassed &= TestTrue(Reason, Production->ApplyFinancialPolicy(-1, Reason));
        Ledger = Production->CaptureLedger();
        bPassed &= TestEqual(TEXT("second emergency offer rotates to the additional programme"),
            Ledger.Contracts.Last().VehicleModelId, ProgrammeId);
    }
    if (World) World->DestroyWorld(false);
    TestTrue(TEXT("temporary emergency programme unregisters after test"),
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(ProgrammeId));
    return bPassed;
}

#endif
