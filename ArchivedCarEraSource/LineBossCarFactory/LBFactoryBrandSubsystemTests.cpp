#include "LBFactoryBrandSubsystem.h"

#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"
#include "LBPressShopSaveGame.h"
#include "Misc/AutomationTest.h"

#include <limits>

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBFactoryBrandProfileTest,
    "LineBoss.FactoryBrand.FreeNameColourAndPersistence",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBFactoryBrandProfileTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_FactoryBrandProfile"));
    ULBFactoryBrandSubsystem* Brand = World ? NewObject<ULBFactoryBrandSubsystem>(World) : nullptr;
    TestNotNull(TEXT("Factory brand authority exists"), Brand);
    if (!Brand) { if (World) World->DestroyWorld(false); return false; }
    TestEqual(TEXT("Cairnwell is the playable built-in default"), Brand->GetFactoryName(),
        FString(TEXT("Cairnwell Automotive")));
    TestTrue(TEXT("A new campaign can start immediately without appearance onboarding"),
        Brand->IsInitialSetupComplete());
    TestTrue(TEXT("Player can choose an unrelated free factory name"),
        Brand->SetFactoryName(TEXT("  Greg's Future Motors  ")));
    TestEqual(TEXT("Free factory name is normalised but not replaced"), Brand->GetFactoryName(),
        FString(TEXT("Greg's Future Motors")));
    const FLinearColor Blue(0.025f, 0.22f, 0.55f, 1.0f);
    const FLinearColor Frame(0.12f, 0.135f, 0.15f, 1.0f);
    const FLinearColor LegacyMagenta(1.0f, 0.0f, 1.0f, 1.0f);
    int32 LiveryNotifications = 0;
    FLBFactoryMachineLivery LastNotification;
    Brand->OnMachineLiveryChanged().AddLambda(
        [&LiveryNotifications, &LastNotification](const FLBFactoryMachineLivery& Livery)
        {
            ++LiveryNotifications;
            LastNotification = Livery;
        });
    FString Reason;
    TestTrue(TEXT("Player can choose both a brighter body and distinct frame colour"),
        Brand->SetMachineLiveryColours(Blue, Frame, Reason));
    TestTrue(TEXT("Accepted livery has no error message"), Reason.IsEmpty());
    TestEqual(TEXT("A successful visual edit emits one live-update notification"),
        LiveryNotifications, 1);
    TestTrue(TEXT("Notification carries the selected primary colour"),
        LastNotification.PrimaryColour.Equals(Blue, 0.0001f));
    TestTrue(TEXT("Notification carries the selected secondary colour"),
        LastNotification.SecondaryColour.Equals(Frame, 0.0001f));
    TestTrue(TEXT("Legacy setup completion remains an idempotent compatibility endpoint"),
        Brand->CompleteInitialSetup());
    TestTrue(TEXT("Optional appearance edits leave the campaign ready"), Brand->IsInitialSetupComplete());

    const FLBFactoryMachineLivery AcceptedLivery = Brand->GetMachineLivery();
    TestFalse(TEXT("Out-of-gamut HDR colour is rejected"), Brand->SetMachineLiveryColours(
        FLinearColor(1.2f, 0.2f, 0.2f), Frame, Reason));
    TestTrue(TEXT("Gamut rejection explains itself"), Reason.Contains(TEXT("GAMUT")));
    TestFalse(TEXT("Non-finite colour is rejected"), Brand->SetMachineLiveryColours(
        FLinearColor(std::numeric_limits<float>::quiet_NaN(), 0.2f, 0.2f), Frame, Reason));
    TestFalse(TEXT("Near-black body paint is rejected for factory readability"),
        Brand->SetMachineLiveryColours(FLinearColor(0.005f, 0.005f, 0.005f), Frame, Reason));
    TestTrue(TEXT("Dark rejection explains readability"), Reason.Contains(TEXT("TOO DARK")));
    TestFalse(TEXT("Near-white paint is rejected so modeled surface detail survives"),
        Brand->SetMachineLiveryColours(FLinearColor(0.95f, 0.95f, 0.95f), Frame, Reason));
    TestTrue(TEXT("Bright rejection explains detail loss"), Reason.Contains(TEXT("TOO BRIGHT")));
    TestFalse(TEXT("Indistinguishable body and frame paints are rejected"),
        Brand->SetMachineLiveryColours(Blue, Blue, Reason));
    TestTrue(TEXT("Pair rejection explains contrast"), Reason.Contains(TEXT("MORE CONTRAST")));
    TestTrue(TEXT("Rejected edits are atomic"),
        Brand->GetMachineLivery().Equals(AcceptedLivery));

    TestFalse(TEXT("Legacy three-colour entry point cannot change safety yellow"),
        Brand->SetFactoryColours(Blue, Frame, LegacyMagenta));
    TestTrue(TEXT("Safety yellow remains the fixed factory semantic"),
        Brand->GetSafetyAccentColour().Equals(
            ULBFactoryBrandSubsystem::GetFixedSafetyYellowColour(), 0.0001f));

    ULBPressShopSaveGame* Save = NewObject<ULBPressShopSaveGame>();
    Save->FactoryBrand = Brand->CaptureSaveState();
    TestEqual(TEXT("New factory profiles save as version two"), Save->FactoryBrand.Version, 2);
    TestTrue(TEXT("Compatibility setup bit remains complete in the existing save format"),
        Save->FactoryBrand.bInitialSetupComplete);
    TArray<uint8> Bytes;
    TestTrue(TEXT("Brand profile serialises with campaign save"), UGameplayStatics::SaveGameToMemory(Save, Bytes));
    const ULBPressShopSaveGame* Loaded = Cast<ULBPressShopSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes));
    ULBFactoryBrandSubsystem* Reloaded = NewObject<ULBFactoryBrandSubsystem>(World);
    TestTrue(TEXT("Brand profile restores"), Loaded && Reloaded->RestoreSaveState(Loaded->FactoryBrand));
    TestEqual(TEXT("Custom company name survives save/load"), Reloaded->GetFactoryName(),
        FString(TEXT("Greg's Future Motors")));
    TestTrue(TEXT("Custom primary colour survives save/load"), Reloaded->GetPrimaryColour().Equals(Blue, 0.0001f));
    TestTrue(TEXT("Custom secondary colour survives save/load"), Reloaded->GetSecondaryColour().Equals(Frame, 0.0001f));
    TestTrue(TEXT("Campaign readiness survives save/load"), Reloaded->IsInitialSetupComplete());

    const FLinearColor LaterPrimary(0.47f, 0.075f, 0.16f, 1.0f);
    const FLinearColor LaterSecondary(0.08f, 0.10f, 0.11f, 1.0f);
    TestTrue(TEXT("The same livery remains editable after initial setup"),
        Reloaded->SetMachineLiveryColours(LaterPrimary, LaterSecondary, Reason));
    TestTrue(TEXT("Later edits never reset campaign readiness"),
        Reloaded->IsInitialSetupComplete());

    FLBFactoryBrandSaveState IncompleteV2State = Reloaded->CaptureSaveState();
    IncompleteV2State.bInitialSetupComplete = false;
    ULBFactoryBrandSubsystem* NormalisedV2 = NewObject<ULBFactoryBrandSubsystem>(World);
    TestTrue(TEXT("A v2 save written before onboarding dismissal remains loadable"),
        NormalisedV2 && NormalisedV2->RestoreSaveState(IncompleteV2State));
    TestTrue(TEXT("A restored v2 campaign resumes directly in the factory"),
        NormalisedV2 && NormalisedV2->IsInitialSetupComplete());

    FLBFactoryBrandSaveState LegacyState;
    LegacyState.Version = 1;
    LegacyState.FactoryName = TEXT("Returning Factory");
    LegacyState.PrimaryColour = Blue;
    LegacyState.SecondaryColour = Frame;
    LegacyState.SafetyAccentColour = LegacyMagenta;
    LegacyState.bInitialSetupComplete = false;
    ULBFactoryBrandSubsystem* Migrated = NewObject<ULBFactoryBrandSubsystem>(World);
    TestTrue(TEXT("Version-one brand profile migrates cleanly"),
        Migrated && Migrated->RestoreSaveState(LegacyState));
    TestTrue(TEXT("Returning v1 campaigns resume directly in the factory"),
        Migrated && Migrated->IsInitialSetupComplete());
    TestEqual(TEXT("Migrated brand state is upgraded to version two"),
        Migrated ? Migrated->CaptureSaveState().Version : 0, 2);
    TestTrue(TEXT("Migrated arbitrary safety accent is replaced by fixed safety yellow"),
        Migrated && Migrated->GetSafetyAccentColour().Equals(
            ULBFactoryBrandSubsystem::GetFixedSafetyYellowColour(), 0.0001f));

    FLBFactoryBrandSaveState FormerlyLegalDarkLegacy = LegacyState;
    FormerlyLegalDarkLegacy.PrimaryColour = FLinearColor::Black;
    FormerlyLegalDarkLegacy.SecondaryColour = FLinearColor::Black;
    ULBFactoryBrandSubsystem* RepairedLegacy = NewObject<ULBFactoryBrandSubsystem>(World);
    TestTrue(TEXT("A formerly legal low-contrast v1 profile remains loadable"),
        RepairedLegacy && RepairedLegacy->RestoreSaveState(FormerlyLegalDarkLegacy));
    TestTrue(TEXT("Unreadable legacy paints migrate to the readable default pair"),
        RepairedLegacy && RepairedLegacy->GetMachineLivery().Equals(FLBFactoryMachineLivery()));
    World->DestroyWorld(false);
    return true;
}

#endif
