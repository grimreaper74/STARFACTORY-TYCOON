#if WITH_DEV_AUTOMATION_TESTS

#include "LBPaintShopPortComponent.h"

#include "Misc/AutomationTest.h"

#include <limits>

namespace LBPaintShopPortComponentTests
{
    FLBPaintShopPortDefinition MakePort(const FName PortId,
        const ELBPaintShopPortDirection Direction, const FName WIPId)
    {
        FLBPaintShopPortDefinition Result;
        Result.PortId = PortId;
        Result.Direction = Direction;
        Result.WIPId = WIPId;
        return Result;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPortValidConfigurationTest,
    "LineBoss.PaintShop.Experimental.PortComponent.ValidConfiguration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPortValidConfigurationTest::RunTest(const FString& Parameters)
{
    ULBPaintShopPortComponent* Port = NewObject<ULBPaintShopPortComponent>();
    TestNotNull(TEXT("Paint Shop port component can be created"), Port);
    if (!Port)
    {
        return false;
    }

    ELBPaintShopPortDirection Direction = ELBPaintShopPortDirection::Output;
    FLBPaintShopPortDefinition Definition;
    TestFalse(TEXT("A new component starts fail-closed"), Port->IsConfigured());
    TestEqual(TEXT("An unconfigured port exposes no stable ID"), Port->GetPortId(), NAME_None);
    TestEqual(TEXT("An unconfigured port exposes no WIP ID"), Port->GetWIPId(), NAME_None);
    TestFalse(TEXT("An unconfigured port exposes no direction"),
        Port->TryGetDirection(Direction));
    TestFalse(TEXT("An unconfigured port exposes no definition"),
        Port->TryGetDefinition(Definition));
    TestTrue(TEXT("An unconfigured port exposes only the identity transform"),
        Port->GetConfiguredLocalTransform().Equals(FTransform::Identity, 0.001f));
    TestFalse(TEXT("The port component never ticks"), Port->PrimaryComponentTick.bCanEverTick);

    const FLBPaintShopPortDefinition InputDefinition =
        LBPaintShopPortComponentTests::MakePort(LBPaintShopPortIds::CarrierIn,
            ELBPaintShopPortDirection::Input, LBPaintShopWIPIds::BIWComplete);
    const FTransform InputTransform(FRotator(0.0f, 90.0f, 0.0f),
        FVector(-900.0f, 0.0f, 430.0f), FVector::OneVector);
    TestTrue(TEXT("The stable BIW carrier input configures"),
        Port->Configure(InputDefinition, InputTransform));
    TestTrue(TEXT("A valid input becomes configured"), Port->IsConfigured());
    TestEqual(TEXT("The carrier input ID remains exact"), Port->GetPortId(),
        LBPaintShopPortIds::CarrierIn);
    TestEqual(TEXT("The BIW input WIP remains exact"), Port->GetWIPId(),
        LBPaintShopWIPIds::BIWComplete);
    TestTrue(TEXT("The input direction is available after configuration"),
        Port->TryGetDirection(Direction));
    TestEqual(TEXT("The configured input direction remains exact"), Direction,
        ELBPaintShopPortDirection::Input);
    TestTrue(TEXT("The complete semantic input definition is available"),
        Port->TryGetDefinition(Definition));
    TestTrue(TEXT("The configured transform remains separate and exact"),
        Port->GetConfiguredLocalTransform().Equals(InputTransform, 0.001f)
        && Port->GetRelativeTransform().Equals(InputTransform, 0.001f));
    TestTrue(TEXT("The stable Paint Shop component tag is installed"),
        Port->ComponentHasTag(TEXT("LB.PaintShop.Port.v001")));
    TestTrue(TEXT("The input direction tag is installed"),
        Port->ComponentHasTag(TEXT("LB.PaintShop.Port.Input")));
    TestTrue(TEXT("The semantic WIP tag is installed"),
        Port->ComponentHasTag(LBPaintShopWIPIds::BIWComplete));

    const FLBPaintShopPortDefinition OutputDefinition =
        LBPaintShopPortComponentTests::MakePort(LBPaintShopPortIds::CarrierOut,
            ELBPaintShopPortDirection::Output, LBPaintShopWIPIds::BIWEDCoated);
    const FTransform OutputTransform(FRotator(0.0f, 90.0f, 0.0f),
        FVector(900.0f, 0.0f, 430.0f), FVector::OneVector);
    TestTrue(TEXT("The stable coated-BIW carrier output can replace the input"),
        Port->Configure(OutputDefinition, OutputTransform));
    TestEqual(TEXT("The carrier output ID remains exact"), Port->GetPortId(),
        LBPaintShopPortIds::CarrierOut);
    TestEqual(TEXT("The coated-BIW output WIP remains exact"), Port->GetWIPId(),
        LBPaintShopWIPIds::BIWEDCoated);
    TestTrue(TEXT("The output direction tag replaces the stale input tag"),
        Port->ComponentHasTag(TEXT("LB.PaintShop.Port.Output"))
        && !Port->ComponentHasTag(TEXT("LB.PaintShop.Port.Input")));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPaintShopPortFailClosedConfigurationTest,
    "LineBoss.PaintShop.Experimental.PortComponent.FailClosedConfiguration",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPaintShopPortFailClosedConfigurationTest::RunTest(const FString& Parameters)
{
    ULBPaintShopPortComponent* Port = NewObject<ULBPaintShopPortComponent>();
    TestNotNull(TEXT("Fail-closed fixture can be created"), Port);
    if (!Port)
    {
        return false;
    }

    const FLBPaintShopPortDefinition ValidInput =
        LBPaintShopPortComponentTests::MakePort(LBPaintShopPortIds::CarrierIn,
            ELBPaintShopPortDirection::Input, LBPaintShopWIPIds::BIWComplete);
    TestTrue(TEXT("Fixture first accepts a valid input"),
        Port->Configure(ValidInput, FTransform::Identity));

    auto TestCleared = [this, Port](const TCHAR* Context)
    {
        ELBPaintShopPortDirection Direction = ELBPaintShopPortDirection::Output;
        FLBPaintShopPortDefinition Definition;
        TestFalse(FString::Printf(TEXT("%s leaves the component unconfigured"), Context),
            Port->IsConfigured());
        TestEqual(FString::Printf(TEXT("%s clears the stable port ID"), Context),
            Port->GetPortId(), FName());
        TestEqual(FString::Printf(TEXT("%s clears the WIP ID"), Context),
            Port->GetWIPId(), FName());
        TestFalse(FString::Printf(TEXT("%s clears the direction"), Context),
            Port->TryGetDirection(Direction));
        TestFalse(FString::Printf(TEXT("%s clears the definition"), Context),
            Port->TryGetDefinition(Definition));
        TestTrue(FString::Printf(TEXT("%s resets the transform"), Context),
            Port->GetRelativeTransform().Equals(FTransform::Identity, 0.001f));
        TestTrue(FString::Printf(TEXT("%s records a failure reason"), Context),
            !Port->GetConfigurationFailureReason().IsEmpty());
        TestEqual(FString::Printf(TEXT("%s leaves no routing tags"), Context),
            Port->ComponentTags.Num(), 0);
    };

    FLBPaintShopPortDefinition UnknownPort = ValidInput;
    UnknownPort.PortId = TEXT("UNAPPROVED_PORT");
    TestFalse(TEXT("An unknown port ID is rejected"),
        Port->Configure(UnknownPort, FTransform::Identity));
    TestCleared(TEXT("Unknown ID rejection"));
    TestTrue(TEXT("Fixture restores a valid input before direction rejection"),
        Port->Configure(ValidInput, FTransform::Identity));

    FLBPaintShopPortDefinition WrongDirection = ValidInput;
    WrongDirection.Direction = ELBPaintShopPortDirection::Output;
    TestFalse(TEXT("A stable ID with the wrong direction is rejected"),
        Port->Configure(WrongDirection, FTransform::Identity));
    TestCleared(TEXT("Direction rejection"));
    TestTrue(TEXT("Fixture restores a valid input before WIP rejection"),
        Port->Configure(ValidInput, FTransform::Identity));

    FLBPaintShopPortDefinition UnknownWIP = ValidInput;
    UnknownWIP.WIPId = TEXT("UNKNOWN_WIP");
    TestFalse(TEXT("An unknown WIP ID is rejected"),
        Port->Configure(UnknownWIP, FTransform::Identity));
    TestCleared(TEXT("WIP rejection"));
    TestTrue(TEXT("Fixture restores a valid input before transform rejection"),
        Port->Configure(ValidInput, FTransform::Identity));

    const FTransform ScaledTransform(FRotator::ZeroRotator, FVector::ZeroVector,
        FVector(2.0f, 1.0f, 1.0f));
    TestFalse(TEXT("A scaled routing socket is rejected"),
        Port->Configure(ValidInput, ScaledTransform));
    TestCleared(TEXT("Scaled-transform rejection"));
    TestTrue(TEXT("Fixture restores a valid input before non-finite rejection"),
        Port->Configure(ValidInput, FTransform::Identity));

    FTransform InvalidTransform = FTransform::Identity;
    InvalidTransform.SetLocation(FVector(std::numeric_limits<double>::quiet_NaN(), 0.0, 0.0));
    TestFalse(TEXT("A non-finite routing socket is rejected"),
        Port->Configure(ValidInput, InvalidTransform));
    TestCleared(TEXT("Non-finite-transform rejection"));
    return true;
}

#endif
