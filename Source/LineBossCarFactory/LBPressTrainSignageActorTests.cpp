#include "LBPressTrainSignageActor.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBPressTrainNativeSignageTest,
    "LineBoss.PressShop.NativeTrainSignageIsCookSafe",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBPressTrainNativeSignageTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
    TestNotNull(TEXT("Creates isolated test world"), World);
    if (!World) return false;

    ALBPressTrainSignageActor* Sign = World->SpawnActor<ALBPressTrainSignageActor>();
    TestNotNull(TEXT("Spawns native press sign"), Sign);
    if (Sign)
    {
        UStaticMeshComponent* Plate = Sign->GetSignPlate();
        UTextRenderComponent* Label = Sign->GetLabel();
        TestNotNull(TEXT("Owns sign plate"), Plate);
        TestNotNull(TEXT("Owns text label"), Label);
        if (Plate)
        {
            const UStaticMesh* Mesh = Plate->GetStaticMesh();
            TestNotNull(TEXT("Uses engine-native cube plate"), Mesh);
            if (Mesh)
            {
                TestEqual(TEXT("Sign plate is engine basic shape"), Mesh->GetPathName(),
                    FString(TEXT("/Engine/BasicShapes/Cube.Cube")));
            }
            TestEqual(TEXT("Sign plate has no collision"),
                Plate->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
            TestFalse(TEXT("Sign plate cannot affect navigation"),
                Plate->CanEverAffectNavigation());
        }
        if (Label)
        {
            TestEqual(TEXT("Sign has a clear default label"), Label->Text.ToString(),
                FString(TEXT("PRESS TRAIN")));
            TestEqual(TEXT("Sign label has no collision"),
                Label->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
        }
    }

    World->DestroyWorld(false);
    return true;
}

#endif
