#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopExperimentalSaveGame.h"

#include "Kismet/GameplayStatics.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopExperimentalSaveIsolationTest,
    "LineBoss.BodyShop.Experimental.SaveGameV1Isolation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopExperimentalSaveIsolationTest::RunTest(const FString& Parameters)
{
    ULBBodyShopExperimentalSaveGame* Save = NewObject<ULBBodyShopExperimentalSaveGame>();
    TestNotNull(TEXT("Experimental Body Shop save class can be created"), Save);
    if (!Save) return false;

    TestEqual(TEXT("Experimental save uses its dedicated v1 slot"),
        Save->GetSlotName(), FName(TEXT("LineBoss_BodyShopExperimental_v001")));
    TestEqual(TEXT("Experimental save remains schema v1"),
        Save->SaveSchemaVersion, ULBBodyShopExperimentalSaveGame::SchemaVersion);
    TestEqual(TEXT("Experimental save targets only the isolated prototype map"),
        Save->PrototypeMapId, FString(TEXT("LB_BodyShop_Prototype_v001")));

    FString Reason;
    Save->SaveSchemaVersion = 2;
    TestFalse(TEXT("Campaign or future schemas cannot be mistaken for Body Shop v1"),
        Save->ValidateForLoad(Reason));
    TestTrue(TEXT("Rejected schema gives a reason"), !Reason.IsEmpty());

    Save->SaveSchemaVersion = ULBBodyShopExperimentalSaveGame::SchemaVersion;
    const FString DiskSlot = TEXT("LineBoss_Automation_BodyShopExperimentalSaveV1");
    TArray<uint8> Bytes;
    TestTrue(TEXT("Experimental Body Shop save serializes independently"),
        UGameplayStatics::SaveGameToMemory(Save, Bytes));
    ULBBodyShopExperimentalSaveGame* MemoryReload =
        Cast<ULBBodyShopExperimentalSaveGame>(UGameplayStatics::LoadGameFromMemory(Bytes));
    TestNotNull(TEXT("Experimental Body Shop save reloads independently"), MemoryReload);
    TestTrue(TEXT("Experimental Body Shop save writes to its own disk slot"),
        UGameplayStatics::SaveGameToSlot(Save, DiskSlot, ULBBodyShopExperimentalSaveGame::GetUserIndex()));
    ULBBodyShopExperimentalSaveGame* DiskReload = Cast<ULBBodyShopExperimentalSaveGame>(
        UGameplayStatics::LoadGameFromSlot(DiskSlot, ULBBodyShopExperimentalSaveGame::GetUserIndex()));
    TestNotNull(TEXT("Experimental Body Shop save reads from its own disk slot"), DiskReload);
    TestTrue(TEXT("Automation experimental slot is removed"),
        UGameplayStatics::DeleteGameInSlot(DiskSlot, ULBBodyShopExperimentalSaveGame::GetUserIndex()));
    return true;
}

#endif
