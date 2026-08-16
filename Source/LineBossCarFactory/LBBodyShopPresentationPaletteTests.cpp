#if WITH_DEV_AUTOMATION_TESTS

#include "LBBodyShopPresentationPalette.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Materials/MaterialParameters.h"
#include "Misc/AutomationTest.h"
#include "UObject/UObjectGlobals.h"

namespace
{
    const FName SemanticSlots[] = {
        TEXT("M_LB_BS_CreamPaint"), TEXT("M_LB_BS_BlackMotor"),
        TEXT("M_LB_BS_StructuralLightGrey"), TEXT("M_LB_BS_BrushedSteel"),
        TEXT("M_LB_BS_GraphiteTooling"), TEXT("M_LB_BS_EmeraldPanel"),
        TEXT("M_LB_BS_SafetyYellow"), TEXT("M_LB_BS_VacuumRubber"),
        TEXT("M_LB_BS_ScannerLens"), TEXT("M_LB_BS_StatusGreen"),
        TEXT("M_LB_BS_StatusAmber"), TEXT("M_LB_BS_StatusRed")
    };

    const TCHAR* FinalMeshes[] = {
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Fixture/SM_LB_BodyShop_UnderbodyFixture_v001.SM_LB_BodyShop_UnderbodyFixture_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_Base_v001.SM_LB_BodyShopRobotNative_Base_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J1_v001.SM_LB_BodyShopRobotNative_J1_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J2_v001.SM_LB_BodyShopRobotNative_J2_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J3_v001.SM_LB_BodyShopRobotNative_J3_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J4_v001.SM_LB_BodyShopRobotNative_J4_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J5_v001.SM_LB_BodyShopRobotNative_J5_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Robot/SM_LB_BodyShopRobotNative_J6_v001.SM_LB_BodyShopRobotNative_J6_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Tools/SM_LB_BodyShopTool_PanelPick8Cup_v001.SM_LB_BodyShopTool_PanelPick8Cup_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopUnderbodySlice_v001/Vision/SM_LB_BodyShop_VisionGate_v001.SM_LB_BodyShop_VisionGate_v001"),
        TEXT("/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001/Tools/SM_LB_BodyShopToolNative_OpenCGun_v001.SM_LB_BodyShopToolNative_OpenCGun_v001")
    };

    bool GetVector(UMaterialInterface* Material, const FName Name, FLinearColor& OutValue)
    {
        return Material && Material->GetVectorParameterValue(
            FHashedMaterialParameterInfo(Name), OutValue);
    }

    bool GetScalar(UMaterialInterface* Material, const FName Name, float& OutValue)
    {
        return Material && Material->GetScalarParameterValue(
            FHashedMaterialParameterInfo(Name), OutValue);
    }

    bool TestMeshContract(FAutomationTestBase& Test, const TCHAR* Path)
    {
        UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, Path);
        if (!Test.TestNotNull(FString::Printf(TEXT("Final mesh resolves: %s"), Path), Mesh))
            return false;
        const TArray<FStaticMaterial>& Slots = Mesh->GetStaticMaterials();
        Test.TestTrue(TEXT("Final mesh has semantic slots"), !Slots.IsEmpty());
        for (int32 Index = 0; Index < Slots.Num(); ++Index)
        {
            const TCHAR* ExpectedPath = LBBodyShopPresentationPalette::GetMaterialPath(
                Slots[Index].MaterialSlotName);
            Test.TestNotNull(TEXT("Every final mesh slot maps to the v002 palette"), ExpectedPath);
            UMaterialInterface* Material = Mesh->GetMaterial(Index);
            Test.TestNotNull(TEXT("Every final mesh package slot has a material"), Material);
            if (ExpectedPath && Material)
            {
                Test.TestEqual(TEXT("Package slot uses its exact semantic v002 MIC"),
                    Material->GetPathName(), FString(ExpectedPath));
                Test.TestFalse(TEXT("WorldGrid never remains on final Body Shop art"),
                    Material->GetPathName().Contains(TEXT("WorldGridMaterial")));
            }
        }
        return true;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopSemanticPalettePathTest,
    "LineBoss.BodyShop.Experimental.Presentation.MaterialsV002.PathsAndParameters",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopSemanticPalettePathTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    TestEqual(TEXT("Exactly twelve semantic slots are supported"),
        LBBodyShopPresentationPalette::GetSupportedSemanticSlotCount(), 12);
    for (const FName Slot : SemanticSlots)
    {
        const TCHAR* Path = LBBodyShopPresentationPalette::GetMaterialPath(Slot);
        TestNotNull(TEXT("Every known semantic slot has a path"), Path);
        if (!Path) continue;
        const FString PathString(Path);
        TestTrue(TEXT("Every palette asset is isolated under Materials_v002"),
            PathString.StartsWith(LBBodyShopPresentationPalette::GetMaterialRootPath()));
        TestFalse(TEXT("Candidate_v004 is never a runtime palette dependency"),
            PathString.Contains(TEXT("Candidate_v004")));
        UMaterialInstanceConstant* Instance = LoadObject<UMaterialInstanceConstant>(nullptr, Path);
        TestNotNull(TEXT("Semantic palette asset resolves as a MIC"), Instance);
        if (!Instance) continue;
        FLBBodyShopPresentationPaletteSpec Spec;
        TestTrue(TEXT("Semantic palette spec resolves"),
            LBBodyShopPresentationPalette::FindSpec(Slot, Spec));
        const FString ExpectedParent = Spec.bUsesLayeredPaint
            ? LBBodyShopPresentationPalette::GetLayeredMasterMaterialPath()
            : LBBodyShopPresentationPalette::GetFunctionalMasterMaterialPath();
        TestNotNull(TEXT("Semantic MIC parent resolves"), Instance->Parent.Get());
        if (Instance->Parent)
            TestEqual(TEXT("Semantic MIC uses its exact local parent"),
                Instance->Parent->GetPathName(), ExpectedParent);
        if (Spec.bUsesLayeredPaint)
        {
            FLinearColor PaintColour;
            float NormalStrength = 0.0f;
            float TextureScale = 0.0f;
            float DustAmount = 0.0f;
            float WearContrast = 0.0f;
            float PaintCoverageBias = 0.0f;
            float BaseRoughness = 0.0f;
            float RoughnessVariation = 0.0f;
            const bool bIsReadabilityTunedCream = Slot == TEXT("M_LB_BS_CreamPaint");
            TestTrue(TEXT("Layered paint colour matches frozen v002 spec"),
                GetVector(Instance, TEXT("PaintColour"), PaintColour)
                    && PaintColour.Equals(Spec.BaseColour, 0.0001f));
            TestTrue(TEXT("Layered paint normal strength matches its approved presentation role"),
                GetScalar(Instance, TEXT("NormalStrength"), NormalStrength)
                    && FMath::IsNearlyEqual(NormalStrength,
                        bIsReadabilityTunedCream ? 0.02f : 0.05f, 0.0001f));
            TestTrue(TEXT("Layered paint uses fine normalized-UV texture scale"),
                GetScalar(Instance, TEXT("TextureScale"), TextureScale)
                    && FMath::IsNearlyEqual(TextureScale, 18.0f, 0.0001f));
            TestTrue(TEXT("Layered paint dust matches its approved presentation role"),
                GetScalar(Instance, TEXT("DustAmount"), DustAmount)
                    && FMath::IsNearlyEqual(DustAmount,
                        bIsReadabilityTunedCream ? 0.0f : 0.035f, 0.0001f));
            TestTrue(TEXT("Layered paint wear contrast matches its approved presentation role"),
                GetScalar(Instance, TEXT("WearContrast"), WearContrast)
                    && FMath::IsNearlyEqual(WearContrast,
                        bIsReadabilityTunedCream ? 0.0f : 2.45f, 0.0001f));
            TestTrue(TEXT("Layered paint coverage matches its approved presentation role"),
                GetScalar(Instance, TEXT("PaintCoverageBias"), PaintCoverageBias)
                    && FMath::IsNearlyEqual(PaintCoverageBias,
                        bIsReadabilityTunedCream ? 1.0f : 0.93f, 0.0001f));
            TestTrue(TEXT("Layered paint base roughness matches its approved presentation role"),
                GetScalar(Instance, TEXT("BaseRoughness"), BaseRoughness)
                    && FMath::IsNearlyEqual(BaseRoughness,
                        bIsReadabilityTunedCream ? 0.58f : 0.56f, 0.0001f));
            TestTrue(TEXT("Layered paint roughness variation matches its approved presentation role"),
                GetScalar(Instance, TEXT("RoughnessVariation"), RoughnessVariation)
                    && FMath::IsNearlyEqual(RoughnessVariation,
                        bIsReadabilityTunedCream ? 0.06f : 0.28f, 0.0001f));
        }
        else
        {
            FLinearColor BaseColour;
            float Metallic = 0.0f;
            float Roughness = 0.0f;
            float RoughnessVariation = 0.0f;
            float EmissiveStrength = 0.0f;
            TestTrue(TEXT("Functional base colour matches frozen v002 spec"),
                GetVector(Instance, TEXT("BaseColour"), BaseColour)
                    && BaseColour.Equals(Spec.BaseColour, 0.0001f));
            TestTrue(TEXT("Functional metallic matches frozen v002 spec"),
                GetScalar(Instance, TEXT("Metallic"), Metallic)
                    && FMath::IsNearlyEqual(Metallic, Spec.Metallic, 0.0001f));
            TestTrue(TEXT("Functional roughness matches frozen v002 spec"),
                GetScalar(Instance, TEXT("Roughness"), Roughness)
                    && FMath::IsNearlyEqual(Roughness, Spec.Roughness, 0.0001f));
            TestTrue(TEXT("Functional roughness variation matches frozen v002 spec"),
                GetScalar(Instance, TEXT("RoughnessVariation"), RoughnessVariation)
                    && FMath::IsNearlyEqual(RoughnessVariation,
                        Spec.RoughnessVariation, 0.0001f));
            TestTrue(TEXT("Functional emissive strength matches frozen v002 spec"),
                GetScalar(Instance, TEXT("EmissiveStrength"), EmissiveStrength)
                    && FMath::IsNearlyEqual(EmissiveStrength,
                        Spec.EmissiveStrength, 0.0001f));
        }
    }
    FLBBodyShopPresentationPaletteSpec Unknown;
    TestNull(TEXT("Unknown semantic material path fails closed"),
        LBBodyShopPresentationPalette::GetMaterialPath(TEXT("M_LB_UNKNOWN")));
    TestFalse(TEXT("Unknown semantic material spec fails closed"),
        LBBodyShopPresentationPalette::FindSpec(TEXT("M_LB_UNKNOWN"), Unknown));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLBBodyShopFinalMeshMaterialBindingTest,
    "LineBoss.BodyShop.Experimental.Presentation.MaterialsV002.FinalMeshBindings",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBBodyShopFinalMeshMaterialBindingTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    for (const TCHAR* Path : FinalMeshes) TestMeshContract(*this, Path);

    UStaticMesh* Fixture = LoadObject<UStaticMesh>(nullptr, FinalMeshes[0]);
    UStaticMesh* EightCup = LoadObject<UStaticMesh>(nullptr, FinalMeshes[8]);
    UStaticMesh* Vision = LoadObject<UStaticMesh>(nullptr, FinalMeshes[9]);
    UStaticMesh* CGun = LoadObject<UStaticMesh>(nullptr, FinalMeshes[10]);
    if (Fixture)
        TestEqual(TEXT("Fixture has exactly two fully mapped semantic slots"),
            LBBodyShopPresentationPalette::CountSupportedSlots(Fixture), 2);
    if (EightCup)
        TestEqual(TEXT("Eight-cup EOAT has exactly four fully mapped semantic slots"),
            LBBodyShopPresentationPalette::CountSupportedSlots(EightCup), 4);
    if (Vision)
        TestEqual(TEXT("Vision gate has exactly seven fully mapped semantic slots"),
            LBBodyShopPresentationPalette::CountSupportedSlots(Vision), 7);

    const int32 NativeMeshIndices[] = {1, 2, 3, 4, 5, 6, 7, 10};
    const int32 ExpectedSlotCounts[] = {4, 5, 5, 4, 4, 3, 4, 5};
    const int32 ExpectedTriangles[][3] = {
        {468, 372, 228}, {392, 360, 208}, {312, 176, 144}, {312, 264, 144},
        {208, 132, 100}, {208, 176, 144}, {224, 132, 84}, {504, 352, 304}
    };
    int32 TriangleTotals[3] = {0, 0, 0};
    for (int32 NativeIndex = 0; NativeIndex < UE_ARRAY_COUNT(NativeMeshIndices); ++NativeIndex)
    {
        UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr,
            FinalMeshes[NativeMeshIndices[NativeIndex]]);
        if (!Mesh) continue;
        TestEqual(TEXT("Every native robot/tool mesh has exactly three imported source LODs"),
            Mesh->GetNumLODs(), 3);
        TestEqual(TEXT("Every native LOD0 keeps its exact semantic material-slot count"),
            LBBodyShopPresentationPalette::CountSupportedSlots(Mesh),
            ExpectedSlotCounts[NativeIndex]);
        for (int32 LODIndex = 0; LODIndex < 3; ++LODIndex)
        {
            const int32 Triangles = Mesh->GetNumTriangles(LODIndex);
            TestEqual(TEXT("Native mesh LOD retains its frozen source triangle count"),
                Triangles, ExpectedTriangles[NativeIndex][LODIndex]);
            TriangleTotals[LODIndex] += Triangles;
        }
    }
    TestEqual(TEXT("Native complete-robot LOD0 total is frozen"), TriangleTotals[0], 2628);
    TestEqual(TEXT("Native complete-robot LOD1 total is frozen"), TriangleTotals[1], 1964);
    TestEqual(TEXT("Native complete-robot LOD2 total is frozen"), TriangleTotals[2], 1356);

    UStaticMesh* NativeBase = LoadObject<UStaticMesh>(nullptr, FinalMeshes[1]);
    if (NativeBase)
        TestTrue(TEXT("Native large-class base retains its exact 84x74x40 cm source bounds"),
            NativeBase->GetBoundingBox().GetSize().Equals(FVector(84.0f, 74.0f, 40.0f), 0.1f));
    if (CGun)
        TestTrue(TEXT("Native open C-gun retains its exact 59.5x31.3x77 cm source bounds"),
            CGun->GetBoundingBox().GetSize().Equals(FVector(59.5f, 31.3f, 77.0f), 0.1f));

    TestNotNull(TEXT("Native open C-gun resolves"), CGun);
    if (CGun)
    {
        TestEqual(TEXT("Native open C-gun has five fully mapped semantic slots"),
            LBBodyShopPresentationPalette::CountSupportedSlots(CGun), 5);
        for (const FStaticMaterial& Slot : CGun->GetStaticMaterials())
            TestNotNull(TEXT("Every native C-gun slot is in the Body Shop palette"),
                LBBodyShopPresentationPalette::GetMaterialPath(Slot.MaterialSlotName));
    }
    return true;
}

#endif
