#include "LBOneFactoryPaintStarterLayout.h"
#include "LBVehiclePanelCatalog.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

namespace LBOneFactoryPaintStarterTestsPrivate
{
    bool SameStation(const FLBOneFactoryPaintStarterStationState& Left,
        const FLBOneFactoryPaintStarterStationState& Right)
    {
        return Left.Version == Right.Version
            && Left.StationId == Right.StationId
            && Left.Role == Right.Role
            && Left.WorldTransform.Equals(Right.WorldTransform, 0.001f)
            && Left.FootprintSizeCm.Equals(Right.FootprintSizeCm, 0.01f)
            && Left.InputBodyState == Right.InputBodyState
            && Left.OutputBodyState == Right.OutputBodyState
            && Left.bPlayerProgrammeSelectable ==
                Right.bPlayerProgrammeSelectable
            && Left.bPlayerPositionable == Right.bPlayerPositionable
            && Left.PaintProgrammeId == Right.PaintProgrammeId
            && Left.TargetBodyColour == Right.TargetBodyColour
            && Left.ActiveOrReservedUnitIds == Right.ActiveOrReservedUnitIds;
    }

    bool SameConnection(const FLBOneFactoryPaintStarterConnectionState& Left,
        const FLBOneFactoryPaintStarterConnectionState& Right)
    {
        return Left.Version == Right.Version
            && Left.ConnectionId == Right.ConnectionId
            && Left.SourceStationId == Right.SourceStationId
            && Left.TargetStationId == Right.TargetStationId
            && Left.CarriedBodyState == Right.CarriedBodyState
            && FMath::IsNearlyEqual(Left.MaximumRouteLengthCm,
                Right.MaximumRouteLengthCm, 0.01f);
    }

    bool SameState(const FLBOneFactoryPaintStarterLayoutState& Left,
        const FLBOneFactoryPaintStarterLayoutState& Right)
    {
        if (Left.Version != Right.Version || Left.LayoutId != Right.LayoutId
            || Left.VehicleModelId != Right.VehicleModelId
            || Left.PaintProgrammeId != Right.PaintProgrammeId
            || Left.SelectedBodyColour != Right.SelectedBodyColour
            || Left.Revision != Right.Revision
            || Left.bCommissioned != Right.bCommissioned
            || Left.InputBodyState != Right.InputBodyState
            || Left.OutputBodyState != Right.OutputBodyState
            || Left.Stations.Num() != Right.Stations.Num()
            || Left.Connections.Num() != Right.Connections.Num())
        {
            return false;
        }
        for (int32 Index = 0; Index < Left.Stations.Num(); ++Index)
            if (!SameStation(Left.Stations[Index], Right.Stations[Index]))
                return false;
        for (int32 Index = 0; Index < Left.Connections.Num(); ++Index)
            if (!SameConnection(Left.Connections[Index],
                    Right.Connections[Index])) return false;
        return true;
    }

    FLBOneFactoryPaintStarterStationState* FindStation(
        FLBOneFactoryPaintStarterLayoutState& State,
        const ELBOneFactoryPaintStarterRole Role)
    {
        return State.Stations.FindByPredicate([Role](
            const FLBOneFactoryPaintStarterStationState& Station)
        {
            return Station.Role == Role;
        });
    }

    const FLBOneFactoryPaintStarterStationState* FindStation(
        const FLBOneFactoryPaintStarterLayoutState& State,
        const ELBOneFactoryPaintStarterRole Role)
    {
        return State.Stations.FindByPredicate([Role](
            const FLBOneFactoryPaintStarterStationState& Station)
        {
            return Station.Role == Role;
        });
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPaintStarterCanonicalTest,
    "LineBoss.OneFactory.PaintStarter.NativeProfileCanonicalBlackBoxTopology",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPaintStarterCanonicalTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    FString Reason;
    const FLBOneFactoryPaintNativeOnlyProfile Profile =
        ULBOneFactoryPaintStarterLayoutLibrary::MakeNativeOnlyProfile();
    TestTrue(TEXT("Exact Paint native-only profile validates"),
        ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeOnlyProfile(
            Profile, Reason));
    TestEqual(TEXT("Only the two reviewed Paint classes are allowed"),
        Profile.AllowedClassPaths.Num(), 2);
    TestEqual(TEXT("Ten exact direct presentation assets are allowed"),
        Profile.AllowedAssets.Num(), 10);
    TestTrue(TEXT("Native data authority is accepted"),
        ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPaintStarterLayoutAuthority"),
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPaintStarterLayoutAuthority"),
            ELBOneFactoryAssetProvenance::NativeCode, Reason));
    TestTrue(TEXT("Exact three-LOD native oven is accepted"),
        ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPaintStarterPresentationActor"),
            Profile.AllowedAssets[0].AssetPath.ToString(),
            ELBOneFactoryAssetProvenance::NativeAuthored, Reason));
    TestFalse(TEXT("Correct path with incorrect provenance fails closed"),
        ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPaintStarterPresentationActor"),
            Profile.AllowedAssets[0].AssetPath.ToString(),
            ELBOneFactoryAssetProvenance::ExternalGenerated, Reason));
    TestFalse(TEXT("Unknown asset under a broad Candidate root is rejected"),
        ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPaintStarterPresentationActor"),
            TEXT("/Game/LineBoss/Candidates/PaintShop/Unknown/SM_Unknown.SM_Unknown"),
            ELBOneFactoryAssetProvenance::NativeAuthored, Reason));
    TestFalse(TEXT("Meshy token fails even under an allowed package"),
        ULBOneFactoryPaintStarterLayoutLibrary::ValidateNativeReference(Profile,
            TEXT("/Script/LineBossCarFactory.LBOneFactoryPaintStarterPresentationActor"),
            TEXT("/Game/LineBoss/Candidates/PaintShop/Meshy/SM_Test.SM_Test"),
            ELBOneFactoryAssetProvenance::NativeAuthored, Reason));

    const FLBOneFactoryPaintStarterLayoutState Canonical =
        ULBOneFactoryPaintStarterLayoutLibrary::MakeCanonicalStarterLayout();
    TestTrue(TEXT("Canonical eight-responsibility Paint starter validates"),
        ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            Canonical, Reason));
    TestEqual(TEXT("Paint starter has eight stable responsibilities"),
        Canonical.Stations.Num(), 8);
    TestEqual(TEXT("Paint starter has seven sequential routes"),
        Canonical.Connections.Num(), 7);
    TestEqual(TEXT("Default body colour is the Cairnwell programme"),
        Canonical.SelectedBodyColour,
        ELBOneFactoryPaintColour::CairnwellTeal);
    TestFalse(TEXT("Process colours cannot be selected as body colours"),
        ULBOneFactoryPaintStarterLayoutLibrary::IsPlayerSelectableColour(
            ELBOneFactoryPaintColour::EDPrimerGrey));

    // Programme identity must follow the selected vehicle recipe.  This keeps
    // a future car's paint orders separate from Cairnwell even when both offer
    // the same factory colour palette.
    const FName AlternateModelId(TEXT("PAINT_PROGRAMME_TEST_MODEL"));
    LBVehicleModelCatalog::UnregisterDevelopmentRecipe(AlternateModelId);
    FLBVehicleModelRecipe AlternateRecipe;
    AlternateRecipe.ModelId = AlternateModelId;
    AlternateRecipe.DisplayName = TEXT("Paint programme test vehicle");
    AlternateRecipe.RecipeRevisionId = TEXT("PAINT_PROGRAMME_TEST_RECIPE_V001");
    AlternateRecipe.PaintRouteProfileId = TEXT("PAINT_ROUTE_EDCOAT_VISIBLE_V001");
    AlternateRecipe.GeometryAuthorityId = TEXT("PaintProgrammeTestGeometry_V001");
    AlternateRecipe.PanelGeometryAuthorityId = TEXT("PaintProgrammeTestPanels_V001");
    AlternateRecipe.BaseKitTypeId = TEXT("PAINT_PROGRAMME_TEST_BIW_KIT");
    AlternateRecipe.DefaultRevenuePence = 100;
    AlternateRecipe.bDevelopmentVisual = true;
    AlternateRecipe.bPanelGeometryValidated = true;
    AlternateRecipe.RequiredPanels.Add({TEXT("HOOD_PANEL"), TEXT("Hood"),
        ELBPanelHandedness::None, 1, FVector(100.0f), NAME_None});
    TestTrue(TEXT("an alternate development recipe can be registered for paint programme IDs"),
        LBVehicleModelCatalog::RegisterDevelopmentRecipe(AlternateRecipe, Reason));
    TestEqual(TEXT("Cairnwell retains its existing programme identity"),
        ULBOneFactoryPaintStarterLayoutLibrary::MakePaintProgrammeId(
            ELBOneFactoryPaintColour::SignalRed),
        FName(TEXT("PAINT_CAIRNWELL_2040_SIGNAL_RED_V1")));
    TestEqual(TEXT("alternate model receives its own programme identity"),
        ULBOneFactoryPaintStarterLayoutLibrary::MakePaintProgrammeIdForModel(
            AlternateModelId, ELBOneFactoryPaintColour::SignalRed),
        FName(TEXT("PAINT_PAINT_PROGRAMME_TEST_MODEL_SIGNAL_RED_V1")));
    TestTrue(TEXT("alternate development recipe cleanup succeeds"),
        LBVehicleModelCatalog::UnregisterDevelopmentRecipe(AlternateModelId));
    TestEqual(TEXT("unknown models cannot generate a paint programme"),
        ULBOneFactoryPaintStarterLayoutLibrary::MakePaintProgrammeIdForModel(
            TEXT("UNKNOWN_MODEL"), ELBOneFactoryPaintColour::SignalRed), NAME_None);

    int32 ProgrammeBound = 0;
    int32 ProgrammeSelectors = 0;
    for (const FLBOneFactoryPaintStarterStationState& Station :
        Canonical.Stations)
    {
        if (!Station.PaintProgrammeId.IsNone()) ++ProgrammeBound;
        if (Station.bPlayerProgrammeSelectable) ++ProgrammeSelectors;
        TestTrue(TEXT("Canonical definition contains no seeded WIP"),
            Station.ActiveOrReservedUnitIds.IsEmpty());
    }
    TestEqual(TEXT("Five downstream responsibilities share one programme"),
        ProgrammeBound, 5);
    TestEqual(TEXT("ED, spray and quality expose the same programme action"),
        ProgrammeSelectors, 3);

    const FLBOneFactoryPaintStarterStationState* ED =
        LBOneFactoryPaintStarterTestsPrivate::FindStation(Canonical,
            ELBOneFactoryPaintStarterRole::EDCoatLogicalProcess);
    const FLBOneFactoryPaintStarterStationState* Spray =
        LBOneFactoryPaintStarterTestsPrivate::FindStation(Canonical,
            ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth);
    if (TestNotNull(TEXT("Logical ED seam exists"), ED)
        && TestNotNull(TEXT("Black-box spray responsibility exists"), Spray))
    {
        TestEqual(TEXT("ED produces the explicit coated material state"),
            ED->OutputBodyState,
            ELBOneFactoryPaintBodyState::EDCoatedBody);
        TestEqual(TEXT("Spray booth alone applies the selected colour state"),
            Spray->OutputBodyState,
            ELBOneFactoryPaintBodyState::ColourCoatedBody);
    }
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPaintStarterAtomicProgrammeTest,
    "LineBoss.OneFactory.PaintStarter.AtomicColourCaptureRestoreAndWIPFailClosed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPaintStarterAtomicProgrammeTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPaintStarterAtomicProgrammeTest"));
    ALBOneFactoryPaintStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryPaintStarterLayoutAuthority>() : nullptr;
    if (!TestNotNull(TEXT("Paint authority spawns"), Authority))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }
    TestFalse(TEXT("Paint data authority never ticks"),
        Authority->PrimaryActorTick.bCanEverTick);
    TestFalse(TEXT("Paint data authority is non-replicated"),
        Authority->GetIsReplicated());
    TestTrue(TEXT("Paint authority carries native-only identity"),
        Authority->ActorHasTag(
            ALBOneFactoryPaintStarterLayoutAuthority::GetAuthorityTag())
        && Authority->ActorHasTag(
            ALBOneFactoryPaintStarterLayoutAuthority::GetNativeOnlyTag()));

    FString Reason;
    const FLBOneFactoryPaintStarterLayoutState Original =
        Authority->CaptureLayout();
    TestTrue(TEXT("Spray station accepts a player body colour"),
        Authority->SetStationPaintProgramme(
            LBOneFactoryPaintStarterIds::Station(
                ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth),
            ELBOneFactoryPaintColour::SignalRed, Reason));
    const FLBOneFactoryPaintStarterLayoutState Red = Authority->CaptureLayout();
    TestEqual(TEXT("Atomic colour change increments one revision"),
        Red.Revision, Original.Revision + 1);
    TestEqual(TEXT("Layout owns the selected colour"), Red.SelectedBodyColour,
        ELBOneFactoryPaintColour::SignalRed);
    int32 MatchingResponsibilities = 0;
    for (const FLBOneFactoryPaintStarterStationState& Station : Red.Stations)
    {
        if (!Station.PaintProgrammeId.IsNone())
        {
            ++MatchingResponsibilities;
            TestEqual(TEXT("Every programme-bound station changes together"),
                Station.TargetBodyColour,
                ELBOneFactoryPaintColour::SignalRed);
            TestEqual(TEXT("Every programme-bound station has the same ID"),
                Station.PaintProgrammeId, Red.PaintProgrammeId);
        }
    }
    TestEqual(TEXT("Five downstream responsibilities changed atomically"),
        MatchingResponsibilities, 5);

    TestFalse(TEXT("Receiving cannot initiate a colour change"),
        Authority->SetStationPaintProgramme(
            LBOneFactoryPaintStarterIds::Station(
                ELBOneFactoryPaintStarterRole::BodySkidReceiving),
            ELBOneFactoryPaintColour::AuroraBlue, Reason));
    TestTrue(TEXT("Rejected responsibility leaves state unchanged"),
        LBOneFactoryPaintStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Red));
    TestFalse(TEXT("ED primer cannot be selected as finished colour"),
        Authority->SetStationPaintProgramme(
            LBOneFactoryPaintStarterIds::Station(
                ELBOneFactoryPaintStarterRole::EDCoatLogicalProcess),
            ELBOneFactoryPaintColour::EDPrimerGrey, Reason));
    TestTrue(TEXT("Rejected colour leaves state unchanged"),
        LBOneFactoryPaintStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Red));

    TestTrue(TEXT("Exact original capture restores atomically"),
        Authority->RestoreLayout(Original, Reason));
    TestTrue(TEXT("Paint capture/restore is lossless"),
        LBOneFactoryPaintStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Original));

    FLBOneFactoryPaintStarterLayoutState WithWIP = Original;
    FLBOneFactoryPaintStarterStationState* Spray =
        LBOneFactoryPaintStarterTestsPrivate::FindStation(WithWIP,
            ELBOneFactoryPaintStarterRole::BlackBoxSprayBooth);
    if (TestNotNull(TEXT("Spray record exists"), Spray))
        Spray->ActiveOrReservedUnitIds.Add(TEXT("BODY-SKID-RESERVATION-001"));
    TestTrue(TEXT("Coherent active-WIP snapshot restores"),
        Authority->RestoreLayout(WithWIP, Reason));
    const FLBOneFactoryPaintStarterLayoutState BeforeBlocked =
        Authority->CaptureLayout();
    TestFalse(TEXT("Active WIP blocks colour change"),
        Authority->SetStationPaintProgramme(
            LBOneFactoryPaintStarterIds::Station(
                ELBOneFactoryPaintStarterRole::QualityLightInspection),
            ELBOneFactoryPaintColour::ArcticWhite, Reason));
    TestFalse(TEXT("Active WIP blocks commissioning"),
        Authority->Commission(Reason));
    TestTrue(TEXT("WIP-rejected operations are mutation-free"),
        LBOneFactoryPaintStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), BeforeBlocked));

    FLBOneFactoryPaintStarterLayoutState DuplicateWIP = WithWIP;
    DuplicateWIP.Stations[0].ActiveOrReservedUnitIds.Add(
        TEXT("BODY-SKID-RESERVATION-001"));
    TestFalse(TEXT("Duplicated WIP ownership rejects restore"),
        Authority->RestoreLayout(DuplicateWIP, Reason));
    TestTrue(TEXT("Rejected restore preserves previous full state"),
        LBOneFactoryPaintStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), BeforeBlocked));

    World->DestroyWorld(false);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryPaintStarterMoveCommissionTest,
    "LineBoss.OneFactory.PaintStarter.TransactionalMoveRollbackAndCommission",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPaintStarterMoveCommissionTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPaintStarterMoveCommissionTest"));
    ALBOneFactoryPaintStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryPaintStarterLayoutAuthority>() : nullptr;
    if (!TestNotNull(TEXT("Paint move fixture exists"), Authority))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    FString Reason;
    const FLBOneFactoryPaintStarterLayoutState Before =
        Authority->CaptureLayout();
    const FLBOneFactoryPaintStarterStationState* Quality =
        LBOneFactoryPaintStarterTestsPrivate::FindStation(Before,
            ELBOneFactoryPaintStarterRole::QualityLightInspection);
    if (!TestNotNull(TEXT("Quality station exists"), Quality))
    {
        World->DestroyWorld(false);
        return false;
    }
    FTransform SmallMove = Quality->WorldTransform;
    SmallMove.AddToTranslation(FVector(50.0f, 0.0f, 0.0f));
    TestTrue(TEXT("Idle station moves inside bay and route reach"),
        Authority->MoveStation(Quality->StationId, SmallMove, Reason));
    const FLBOneFactoryPaintStarterLayoutState AfterMove =
        Authority->CaptureLayout();
    TestEqual(TEXT("Successful move increments one revision"),
        AfterMove.Revision, Before.Revision + 1);
    for (int32 Index = 0; Index < Before.Connections.Num(); ++Index)
        TestTrue(TEXT("Exact material route survives station movement"),
            LBOneFactoryPaintStarterTestsPrivate::SameConnection(
                Before.Connections[Index], AfterMove.Connections[Index]));

    FTransform Outside = SmallMove;
    Outside.SetLocation(FVector(30000.0f, -8500.0f, 0.0f));
    TestFalse(TEXT("Move outside Paint bay fails"),
        Authority->MoveStation(Quality->StationId, Outside, Reason));
    TestTrue(TEXT("Out-of-bay move rolls back the complete state"),
        LBOneFactoryPaintStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), AfterMove));

    const FLBOneFactoryPaintStarterStationState* Dispatch =
        LBOneFactoryPaintStarterTestsPrivate::FindStation(AfterMove,
            ELBOneFactoryPaintStarterRole::PaintedBodyDispatch);
    if (TestNotNull(TEXT("Dispatch station exists"), Dispatch))
    {
        TestFalse(TEXT("Overlapping dispatch fails"),
            Authority->MoveStation(Quality->StationId,
                Dispatch->WorldTransform, Reason));
        TestTrue(TEXT("Overlap rejection rolls back completely"),
            LBOneFactoryPaintStarterTestsPrivate::SameState(
                Authority->CaptureLayout(), AfterMove));
    }

    TestTrue(TEXT("Idle complete Paint route commissions"),
        Authority->Commission(Reason));
    TestTrue(TEXT("Commission gate is explicit"), Authority->IsCommissioned());
    const FLBOneFactoryPaintStarterLayoutState Commissioned =
        Authority->CaptureLayout();
    TestTrue(TEXT("Repeated commission is idempotent"),
        Authority->Commission(Reason));
    TestTrue(TEXT("Repeated commission does not increment revision"),
        LBOneFactoryPaintStarterTestsPrivate::SameState(
            Authority->CaptureLayout(), Commissioned));

    World->DestroyWorld(false);
    return true;
}

#endif
