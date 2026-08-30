#if WITH_DEV_AUTOMATION_TESTS

#include "LBPaintShopTypes.h"

#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopStableIdsAndDefinitionsTest,
    "LineBoss.PaintShop.Experimental.StableIdsAndCanonicalDefinitions",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopStableIdsAndDefinitionsTest::RunTest(const FString& Parameters)
{
    const TArray<FName> ExpectedCellIds = {
        TEXT("PAINT_BIW_LOAD_DOCK"),
        TEXT("PAINT_PHOSPHATE_DIP_CELL"),
        TEXT("PAINT_ED_COAT_DIP_CELL"),
        TEXT("PAINT_DRAIN_INSPECTION_CELL"),
        TEXT("PAINT_ED_CURE_OVEN_CELL"),
        TEXT("PAINT_ED_OUTPUT_BUFFER")
    };
    TestEqual(TEXT("The isolated Paint Shop has the six exact stable cell IDs"),
        FLBPaintShopDefinitionRegistry::GetCanonicalDefinitionIds(), ExpectedCellIds);

    const TArray<FName> WIPIds = {
        LBPaintShopWIPIds::BIWComplete,
        LBPaintShopWIPIds::BIWEDCoated,
        LBPaintShopWIPIds::BIWCuredEDCoat
    };
    TestEqual(TEXT("The three stable WIP IDs remain exact"), WIPIds,
        TArray<FName>({TEXT("BIW_COMPLETE"), TEXT("BIW_ED_COATED"),
            TEXT("BIW_CURED_ED_COAT")}));

    const TArray<FName> RecipeIds = {
        LBPaintShopRecipeIds::PhosphateV001,
        LBPaintShopRecipeIds::EDCoatV001,
        LBPaintShopRecipeIds::EDCureV001
    };
    TestEqual(TEXT("The three versioned recipe IDs remain exact"), RecipeIds,
        TArray<FName>({TEXT("RECIPE_PHOSPHATE_V001"), TEXT("RECIPE_ED_COAT_V001"),
            TEXT("RECIPE_ED_CURE_V001")}));

    const TArray<FName> QualityIds = {
        LBPaintShopQualityIds::PhosphateCoverage,
        LBPaintShopQualityIds::EDFilmBuild,
        LBPaintShopQualityIds::EDCure
    };
    TestEqual(TEXT("The three stable quality IDs remain exact"), QualityIds,
        TArray<FName>({TEXT("QC_PHOSPHATE_COVERAGE"), TEXT("QC_ED_FILM_BUILD"),
            TEXT("QC_ED_CURE")}));
    TestEqual(TEXT("Carrier input port ID remains exact"), LBPaintShopPortIds::CarrierIn,
        FName(TEXT("CARRIER_IN")));
    TestEqual(TEXT("Carrier output port ID remains exact"), LBPaintShopPortIds::CarrierOut,
        FName(TEXT("CARRIER_OUT")));

    const TArray<FLBPaintShopCellDefinition> Definitions =
        FLBPaintShopDefinitionRegistry::GetCanonicalDefinitions();
    TestEqual(TEXT("Exactly six deterministic canonical definitions exist"),
        Definitions.Num(), 6);
    FString Reason;
    for (const FLBPaintShopCellDefinition& Definition : Definitions)
    {
        TestTrue(FString::Printf(TEXT("Canonical definition %s validates"),
            *Definition.DefinitionId.ToString()),
            FLBPaintShopDefinitionRegistry::ValidateDefinition(Definition, Reason));
        TestEqual(TEXT("Every cell has exactly two semantic carrier ports"),
            Definition.Ports.Num(), 2);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopCanonicalFlowValidationTest,
    "LineBoss.PaintShop.Experimental.CanonicalCarrierFlowValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopCanonicalFlowValidationTest::RunTest(const FString& Parameters)
{
    const TArray<FLBPaintShopCellDefinition> Definitions =
        FLBPaintShopDefinitionRegistry::GetCanonicalDefinitions();
    FString Reason;
    TestTrue(TEXT("The canonical six-cell Paint Shop carrier flow validates"),
        FLBPaintShopDefinitionRegistry::ValidateCanonicalDefinitionSet(
            Definitions, Reason));

    TestEqual(TEXT("ED coating creates the coated BIW WIP identity"),
        Definitions[2].OutputWIPId, LBPaintShopWIPIds::BIWEDCoated);
    TestEqual(TEXT("Drain inspection owns the ED film-build quality check"),
        Definitions[3].QualityCheckIds,
        TArray<FName>({LBPaintShopQualityIds::EDFilmBuild}));
    TestEqual(TEXT("ED curing creates the cured ED-coat WIP identity"),
        Definitions[4].OutputWIPId, LBPaintShopWIPIds::BIWCuredEDCoat);

    TArray<FLBPaintShopCellDefinition> WrongRecipe = Definitions;
    WrongRecipe[2].RecipeId = TEXT("RECIPE_UNAPPROVED");
    TestFalse(TEXT("An unapproved recipe is rejected"),
        FLBPaintShopDefinitionRegistry::ValidateCanonicalDefinitionSet(
            WrongRecipe, Reason));

    TArray<FLBPaintShopCellDefinition> BrokenPort = Definitions;
    BrokenPort[4].Ports[0].WIPId = LBPaintShopWIPIds::BIWComplete;
    TestFalse(TEXT("A carrier port with the wrong WIP identity is rejected"),
        FLBPaintShopDefinitionRegistry::ValidateCanonicalDefinitionSet(
            BrokenPort, Reason));

    TArray<FLBPaintShopCellDefinition> WrongOrder = Definitions;
    WrongOrder.Swap(1, 2);
    TestFalse(TEXT("The deterministic canonical cell order is enforced"),
        FLBPaintShopDefinitionRegistry::ValidateCanonicalDefinitionSet(
            WrongOrder, Reason));

    TArray<FLBPaintShopCellDefinition> DuplicateQuality = Definitions;
    DuplicateQuality[3].QualityCheckIds.Add(LBPaintShopQualityIds::EDFilmBuild);
    TestFalse(TEXT("Duplicate quality contracts are rejected"),
        FLBPaintShopDefinitionRegistry::ValidateCanonicalDefinitionSet(
            DuplicateQuality, Reason));
    return true;
}

#endif
