#if WITH_DEV_AUTOMATION_TESTS

#include "LBOneFactoryRuntimeCoordinator.h"
#include "LBOneFactoryUITypes.h"

#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryUITokensTest,
    "LineBoss.OneFactory.UI.StatusTokensAreCompleteDistinctAndCauseNamed",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryUITokensTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    const ELBOneFactoryStationStatus All[] = {
        ELBOneFactoryStationStatus::Working,
        ELBOneFactoryStationStatus::Starved,
        ELBOneFactoryStationStatus::Blocked,
        ELBOneFactoryStationStatus::QualityHold,
        ELBOneFactoryStationStatus::WearCritical,
        ELBOneFactoryStationStatus::Offline,
        ELBOneFactoryStationStatus::Paused,
    };
    TSet<FString> Colours;
    TSet<ELBOneFactoryStatusGlyph> Glyphs;
    for (const ELBOneFactoryStationStatus Status : All)
    {
        const FLBOneFactoryStatusToken Token =
            ULBOneFactoryUITokens::TokenForStatus(Status);
        TestEqual(TEXT("token carries its own status"), Token.Status, Status);
        TestFalse(TEXT("every status names a cause"),
            Token.CauseLabel.IsEmpty());
        Colours.Add(Token.Colour.ToString());
        Glyphs.Add(Token.Glyph);
    }
    // Colour is never the only encoding, and neither colour nor shape may
    // collide: seven statuses, seven colours, seven glyphs.
    TestEqual(TEXT("all colours distinct"), Colours.Num(),
        static_cast<int32>(UE_ARRAY_COUNT(All)));
    TestEqual(TEXT("all glyphs distinct"), Glyphs.Num(),
        static_cast<int32>(UE_ARRAY_COUNT(All)));

    // The canonical rate helper: 12 stamps in a half-hour window = 24/hr.
    TestEqual(TEXT("stamps convert to cars/hour"),
        ULBOneFactoryUITokens::StampsToRatePerHour(12, 1800.0f), 24.0f);
    TestEqual(TEXT("empty window rates zero"),
        ULBOneFactoryUITokens::StampsToRatePerHour(0, 1800.0f), 0.0f);
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBOneFactoryMeasuredRateTest,
    "LineBoss.OneFactory.UI.MeasuredRateCountsOnlyTheWindowedDepartment",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryMeasuredRateTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        FName(TEXT("LBMeasuredRateWorld")));
    ALBOneFactoryRuntimeCoordinator* Coordinator =
        World->SpawnActor<ALBOneFactoryRuntimeCoordinator>();
    if (!TestNotNull(TEXT("coordinator spawns"), Coordinator))
    {
        World->DestroyWorld(false);
        return false;
    }
    // Six press completions inside the last hour, two outside it, and
    // three paint completions that must not leak into the press rate.
    for (int32 Index = 0; Index < 6; ++Index)
    {
        Coordinator->RecordStationCompletion(
            ELBOneFactoryDepartment::Press, 4000.0 + Index * 100.0);
    }
    Coordinator->RecordStationCompletion(ELBOneFactoryDepartment::Press,
        100.0);
    Coordinator->RecordStationCompletion(ELBOneFactoryDepartment::Press,
        200.0);
    for (int32 Index = 0; Index < 3; ++Index)
    {
        Coordinator->RecordStationCompletion(
            ELBOneFactoryDepartment::Paint, 4100.0 + Index * 50.0);
    }
    const float PressRate = Coordinator->MeasuredRatePerHour(
        ELBOneFactoryDepartment::Press, 4600.0, 3600.0f);
    TestEqual(TEXT("press rate counts its six windowed stamps"),
        PressRate, 6.0f);
    const float PaintRate = Coordinator->MeasuredRatePerHour(
        ELBOneFactoryDepartment::Paint, 4600.0, 3600.0f);
    TestEqual(TEXT("paint rate is its own"), PaintRate, 3.0f);
    World->DestroyWorld(false);
    return true;
}

#endif
