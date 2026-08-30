#if WITH_DEV_AUTOMATION_TESTS

#include "Misc/AutomationTest.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "LBFactoryBrandSubsystem.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryFloorMarkingComponent.h"
#include "LBMachineLiveryComponent.h"
#include "Materials/MaterialInstance.h"
#include "Materials/MaterialInstanceDynamic.h"

namespace
{
    UStaticMeshComponent* FindMachineMeshByName(
        ALBFactoryBuildMachine* Machine, const FName ComponentName)
    {
        if (!Machine) return nullptr;
        TInlineComponentArray<UStaticMeshComponent*> Meshes;
        Machine->GetComponents(Meshes);
        UStaticMeshComponent** Found = Meshes.FindByPredicate(
            [ComponentName](const UStaticMeshComponent* Mesh)
            {
                return Mesh && (Mesh->GetFName() == ComponentName
                    || Mesh->GetName().EndsWith(ComponentName.ToString()));
            });
        return Found ? *Found : nullptr;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBMachineLiveryOptInMaterialTest,
    "LineBoss.FactoryBrand.MachineLivery.OptInMaterialsAndLiveEdits",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBMachineLiveryOptInMaterialTest::RunTest(const FString& Parameters)
{
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, TEXT("LB_MachineLivery"));
    TestNotNull(TEXT("Transient livery world exists"), World);
    if (!World) return false;
    FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
    Context.SetCurrentWorld(World);
    World->InitializeActorsForPlay(FURL());

    ULBFactoryBrandSubsystem* Brand = World->GetSubsystem<ULBFactoryBrandSubsystem>();
    TestNotNull(TEXT("World has one shared brand/livery authority"), Brand);
    const FLinearColor FirstPrimary(0.025f, 0.22f, 0.55f, 1.0f);
    const FLinearColor FirstSecondary(0.12f, 0.135f, 0.15f, 1.0f);
    FString Reason;
    TestTrue(TEXT("Readable test livery is accepted"), Brand
        && Brand->SetMachineLiveryColours(FirstPrimary, FirstSecondary, Reason));

    ALBFactoryBuildMachine* GenericMachine = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Generic inspection package configures"), GenericMachine
        && GenericMachine->Configure(TEXT("LIVERY-GENERIC-001"),
            ELBFactoryBuildMachineType::InspectionCell));
    ULBMachineLiveryComponent* Livery = GenericMachine
        ? GenericMachine->GetMachineLiveryComponent() : nullptr;
    TestNotNull(TEXT("Generic machine owns the explicit livery component"), Livery);
    TestTrue(TEXT("Only authored body/frame placeholder slots are registered"),
        Livery && Livery->GetMaterialBindingCount() == 4);

    UStaticMeshComponent* PrimaryBody = FindMachineMeshByName(
        GenericMachine, TEXT("ProvisionalModule_01"));
    UStaticMeshComponent* SecondaryFrame = FindMachineMeshByName(
        GenericMachine, TEXT("ProvisionalModule_04"));
    UStaticMeshComponent* SafetyGuard = FindMachineMeshByName(
        GenericMachine, TEXT("ProvisionalModule_12"));
    UStaticMeshComponent* RedBeaconLens = FindMachineMeshByName(
        GenericMachine, TEXT("RedLens"));
    TestNotNull(TEXT("Primary body fixture exists"), PrimaryBody);
    TestNotNull(TEXT("Secondary frame fixture exists"), SecondaryFrame);
    TestNotNull(TEXT("Fixed safety-yellow guard fixture exists"), SafetyGuard);
    TestNotNull(TEXT("Fixed status-red beacon lens exists"), RedBeaconLens);
    UMaterialInstanceDynamic* PrimaryMID = PrimaryBody
        ? Cast<UMaterialInstanceDynamic>(PrimaryBody->GetMaterial(0)) : nullptr;
    UMaterialInstanceDynamic* SecondaryMID = SecondaryFrame
        ? Cast<UMaterialInstanceDynamic>(SecondaryFrame->GetMaterial(0)) : nullptr;
    UMaterialInterface* SafetyMaterialBeforeEdit = SafetyGuard
        ? SafetyGuard->GetMaterial(0) : nullptr;
    UMaterialInterface* RedBeaconMaterialBeforeEdit = RedBeaconLens
        ? RedBeaconLens->GetMaterial(0) : nullptr;
    const FLinearColor SafetyFloorYellowBeforeEdit =
        ULBFactoryFloorMarkingComponent::GetSemanticColour(
            ELBFactoryFloorMarkingSemantic::ServiceEnvelope);
    const FLinearColor WarningFloorRedBeforeEdit =
        ULBFactoryFloorMarkingComponent::GetSemanticColour(
            ELBFactoryFloorMarkingSemantic::KeepClearHatch);
    TestNotNull(TEXT("Primary generic body uses a MID"), PrimaryMID);
    TestNotNull(TEXT("Secondary generic frame uses a MID"), SecondaryMID);
    TestTrue(TEXT("Primary MID receives the player body colour"), PrimaryMID
        && PrimaryMID->K2_GetVectorParameterValue(TEXT("Color")).Equals(FirstPrimary, 0.0001f));
    TestTrue(TEXT("Secondary MID receives the player frame colour"), SecondaryMID
        && SecondaryMID->K2_GetVectorParameterValue(TEXT("Color")).Equals(FirstSecondary, 0.0001f));
    TestFalse(TEXT("Safety yellow was never converted into a player-livery MID"),
        SafetyMaterialBeforeEdit && SafetyMaterialBeforeEdit->IsA<UMaterialInstanceDynamic>());

    const FLinearColor LaterPrimary(0.47f, 0.075f, 0.16f, 1.0f);
    const FLinearColor LaterSecondary(0.08f, 0.10f, 0.11f, 1.0f);
    TestTrue(TEXT("Pre-BeginPlay Factory Profile edit is accepted"), Brand
        && Brand->SetMachineLiveryColours(LaterPrimary, LaterSecondary, Reason));
    TestTrue(TEXT("Registered primary MID updates before actor BeginPlay"), PrimaryMID
        && PrimaryMID->K2_GetVectorParameterValue(TEXT("Color")).Equals(LaterPrimary, 0.0001f));
    TestTrue(TEXT("Registered secondary MID updates before actor BeginPlay"), SecondaryMID
        && SecondaryMID->K2_GetVectorParameterValue(TEXT("Color")).Equals(LaterSecondary, 0.0001f));
    World->BeginPlay();
    TestTrue(TEXT("Safety yellow remains the exact untouched material after livery edits"),
        SafetyGuard && SafetyGuard->GetMaterial(0) == SafetyMaterialBeforeEdit);
    TestTrue(TEXT("Status beacon red remains controlled only by the beacon state system"),
        RedBeaconLens && RedBeaconLens->GetMaterial(0) == RedBeaconMaterialBeforeEdit);
    TestTrue(TEXT("Safety-yellow floor semantics are outside player livery"),
        ULBFactoryFloorMarkingComponent::GetSemanticColour(
            ELBFactoryFloorMarkingSemantic::ServiceEnvelope).Equals(
                SafetyFloorYellowBeforeEdit, 0.0001f));
    TestTrue(TEXT("Warning-red floor semantics are outside player livery"),
        ULBFactoryFloorMarkingComponent::GetSemanticColour(
            ELBFactoryFloorMarkingSemantic::KeepClearHatch).Equals(
                WarningFloorRedBeforeEdit, 0.0001f));

    ALBFactoryBuildMachine* ApprovedMachine = World->SpawnActor<ALBFactoryBuildMachine>();
    TestTrue(TEXT("Approved Meshy-backed inbound package configures"), ApprovedMachine
        && ApprovedMachine->Configure(TEXT("LIVERY-APPROVED-001"),
            ELBFactoryBuildMachineType::InboundDeliveryDock));
    UStaticMeshComponent* ApprovedVisual = ApprovedMachine
        ? ApprovedMachine->GetApprovedVisualComponent() : nullptr;
    UMaterialInterface* ApprovedMaterialBeforeEdit = ApprovedVisual
        ? ApprovedVisual->GetMaterial(0) : nullptr;
    TestNotNull(TEXT("Approved package has its baked material parent"), ApprovedMaterialBeforeEdit);
    TestEqual(TEXT("Approved imported art has no guessed livery slots"),
        ApprovedMachine && ApprovedMachine->GetMachineLiveryComponent()
            ? ApprovedMachine->GetMachineLiveryComponent()->GetMaterialBindingCount() : -1, 0);
    TestTrue(TEXT("Approved baked material remains installed"), ApprovedVisual
        && ApprovedVisual->GetMaterial(0) == ApprovedMaterialBeforeEdit);

    ULBMachineLiveryComponent* ApprovedLivery = ApprovedMachine
        ? ApprovedMachine->GetMachineLiveryComponent() : nullptr;
    TestTrue(TEXT("Approved-art hook requires an explicit component, slot and tint parameter"),
        ApprovedLivery && ApprovedMaterialBeforeEdit
        && ApprovedLivery->RegisterTexturedMaterialBinding(ApprovedVisual, 0,
            ELBMachineLiveryRole::PrimaryBody, TEXT("LiveryTint")));
    UMaterialInstanceDynamic* ApprovedMID = ApprovedLivery
        ? ApprovedLivery->GetDynamicMaterialForBinding(0) : nullptr;
    TestTrue(TEXT("Approved-art MID retains the exact baked material as its parent"),
        ApprovedMID && ApprovedMID->Parent == ApprovedMaterialBeforeEdit);
    if (ApprovedLivery) ApprovedLivery->ClearMaterialBindings();
    TestEqual(TEXT("Clearing an approved-art binding removes the opt-in registration"),
        ApprovedLivery ? ApprovedLivery->GetMaterialBindingCount() : -1, 0);
    TestTrue(TEXT("Clearing restores the exact original baked material"), ApprovedVisual
        && ApprovedVisual->GetMaterial(0) == ApprovedMaterialBeforeEdit);

    const FLinearColor FinalPrimary(0.10f, 0.40f, 0.18f, 1.0f);
    const FLinearColor FinalSecondary(0.09f, 0.105f, 0.115f, 1.0f);
    TestTrue(TEXT("Another later livery edit succeeds"), Brand
        && Brand->SetMachineLiveryColours(FinalPrimary, FinalSecondary, Reason));
    TestTrue(TEXT("Primary MID remains subscribed after actor BeginPlay"), PrimaryMID
        && PrimaryMID->K2_GetVectorParameterValue(TEXT("Color")).Equals(FinalPrimary, 0.0001f));
    TestTrue(TEXT("Secondary MID remains subscribed after actor BeginPlay"), SecondaryMID
        && SecondaryMID->K2_GetVectorParameterValue(TEXT("Color")).Equals(FinalSecondary, 0.0001f));
    TestTrue(TEXT("Unregistered approved texture detail is never replaced"), ApprovedVisual
        && ApprovedVisual->GetMaterial(0) == ApprovedMaterialBeforeEdit);

    World->DestroyWorld(false);
    GEngine->DestroyWorldContext(World);
    return true;
}

#endif
