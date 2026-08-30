#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopPrototypeRootWidget.h"

#include "Components/Button.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopPrototypeUMGShellTest,
    "LineBoss.BodyShop.Experimental.UI.UMGOnlyOperatorShell",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopPrototypeUMGShellTest::RunTest(const FString& Parameters)
{
    ULBBodyShopPrototypeRootWidget* Widget =
        NewObject<ULBBodyShopPrototypeRootWidget>();
    TestNotNull(TEXT("Native Body Shop operator widget can be instantiated"), Widget);
    if (!Widget) return false;
    TestTrue(TEXT("Native Body Shop operator widget initializes"), Widget->Initialize());
    const TSharedRef<SWidget> SlateShell = Widget->TakeWidget();
    TestTrue(TEXT("Native UMG shell has a complete renderable tree"),
        Widget->HasRenderableShell());

    const TArray<FName> Controls =
        ULBBodyShopPrototypeRootWidget::GetCanonicalControlIds();
    TestEqual(TEXT("Operator shell exposes exactly five bounded controls"),
        Controls.Num(), 5);
    TSet<FName> DistinctControls;
    for (const FName ControlId : Controls) DistinctControls.Add(ControlId);
    TestEqual(TEXT("Operator controls have stable unique IDs"),
        DistinctControls.Num(), Controls.Num());

    const FName ButtonNames[] = {
        TEXT("BodyShopStartPause"), TEXT("BodyShopSave"), TEXT("BodyShopLoad"),
        TEXT("BodyShopClearHeld"), TEXT("BodyShopRobotSlots")};
    for (const FName ButtonName : ButtonNames)
    {
        UButton* Button = Cast<UButton>(Widget->GetWidgetFromName(ButtonName));
        TestNotNull(FString::Printf(TEXT("%s is a real UMG button"),
            *ButtonName.ToString()), Button);
        if (Button)
        {
            TestTrue(FString::Printf(TEXT("%s owns functional behavior"),
                *ButtonName.ToString()), Button->OnClicked.IsBound());
        }
    }

    TestEqual(TEXT("A ready line offers a new pilot cycle"),
        ULBBodyShopPrototypeRootWidget::GetPrimaryActionLabel(
            ELBBodyShopRuntimeStage::Ready, false),
        FString(TEXT("Start pilot cycle")));
    TestEqual(TEXT("A running line offers pause"),
        ULBBodyShopPrototypeRootWidget::GetPrimaryActionLabel(
            ELBBodyShopRuntimeStage::WeldingUnderbody, true),
        FString(TEXT("Pause line")));
    TestEqual(TEXT("A paused in-process line offers resume"),
        ULBBodyShopPrototypeRootWidget::GetPrimaryActionLabel(
            ELBBodyShopRuntimeStage::WeldingUnderbody, false),
        FString(TEXT("Resume line")));
    TestEqual(TEXT("A held unit cannot be silently restarted"),
        ULBBodyShopPrototypeRootWidget::GetPrimaryActionLabel(
            ELBBodyShopRuntimeStage::QualityHold, false),
        FString(TEXT("Line unavailable")));
    TestEqual(TEXT("A complete unit directs the player to release output"),
        ULBBodyShopPrototypeRootWidget::GetPrimaryActionLabel(
            ELBBodyShopRuntimeStage::Complete, false),
        FString(TEXT("Release output first")));
    TestEqual(TEXT("Starvation is exposed rather than starting an impossible cycle"),
        ULBBodyShopPrototypeRootWidget::GetPrimaryActionLabel(
            ELBBodyShopRuntimeStage::AwaitingPanelStillage, false),
        FString(TEXT("Waiting for stillage")));
    return true;
}

#endif
