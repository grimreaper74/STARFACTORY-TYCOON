#include "LBOneFactoryPressStarterPresentationActor.h"

#include "Components/SceneComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "UObject/ConstructorHelpers.h"

namespace LBOneFactoryPressPresentationPrivate
{
    // Ten native ISM batches, one authored S02 bundle, four static S03-S06
    // frame/cue bundles, plus the S01 and S07 MaterialFlow endpoint bundles.
    constexpr int32 ExpectedVisualBatchCount = 17;
    constexpr int32 ExpectedRenderedAggregateCount = 7;
    constexpr int32 ExpectedLogicalItemCount = 268;
    constexpr int32 ExpectedMaterialSlotCount = 306;
    constexpr float TransformTolerance = 0.01f;

    const TCHAR* DetailedPresentationRoot =
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/");
    const TCHAR* DetailedMeshPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/"
        "SM_OneFactoryDetailedPressPresentation_v001."
        "SM_OneFactoryDetailedPressPresentation_v001");
    const TCHAR* S02DeepDrawStaticMeshPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "DetailedPresentation_v001/S02DeepDraw_v003/"
        "SM_CA_S02DeepDraw_Static_LOD0_v003.SM_CA_S02DeepDraw_Static_LOD0_v003");
    const TCHAR* S02DeepDrawRamMeshPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "DetailedPresentation_v001/S02DeepDraw_v003/"
        "SM_CA_S02DeepDraw_Ram_LOD0_v003.SM_CA_S02DeepDraw_Ram_LOD0_v003");
    const TCHAR* S02DeepDrawBlankholderMeshPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "DetailedPresentation_v001/S02DeepDraw_v003/"
        "SM_CA_S02DeepDraw_Blankholder_LOD0_v003.SM_CA_S02DeepDraw_Blankholder_LOD0_v003");
    const TCHAR* S02DeepDrawBolsterMeshPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "DetailedPresentation_v001/S02DeepDraw_v003/"
        "SM_CA_S02DeepDraw_Bolster_LOD0_v003.SM_CA_S02DeepDraw_Bolster_LOD0_v003");
    const TCHAR* S02DeepDrawFlywheelMeshPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "DetailedPresentation_v001/S02DeepDraw_v003/"
        "SM_CA_S02DeepDraw_Flywheel_LOD0_v003.SM_CA_S02DeepDraw_Flywheel_LOD0_v003");
    const TCHAR* S02DeepDrawSafetyGateMeshPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "DetailedPresentation_v001/S02DeepDraw_v003/"
        "SM_CA_S02DeepDraw_SafetyGate_LOD0_v003.SM_CA_S02DeepDraw_SafetyGate_LOD0_v003");
    const TCHAR* S02DeepDrawMaterialMasterPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "DetailedPresentation_v001/S02DeepDraw_v003/Materials/"
        "M_CA_S02DeepDraw_PBR_Master_v003.M_CA_S02DeepDraw_PBR_Master_v003");
    const TCHAR* S02DeepDrawMaterialPaths[] =
    {
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Static_MainGreen_v003.MI_CA_S02DeepDraw_Static_MainGreen_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Static_Concrete_v003.MI_CA_S02DeepDraw_Static_Concrete_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Static_DarkSteel_v003.MI_CA_S02DeepDraw_Static_DarkSteel_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Static_CleanSteel_v003.MI_CA_S02DeepDraw_Static_CleanSteel_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Static_CharcoalGrey_v003.MI_CA_S02DeepDraw_Static_CharcoalGrey_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Static_SafetyYellow_v003.MI_CA_S02DeepDraw_Static_SafetyYellow_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Static_ScreenDark_v003.MI_CA_S02DeepDraw_Static_ScreenDark_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Static_LampGreen_v003.MI_CA_S02DeepDraw_Static_LampGreen_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Static_LampAmber_v003.MI_CA_S02DeepDraw_Static_LampAmber_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Static_LampRed_v003.MI_CA_S02DeepDraw_Static_LampRed_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Ram_DarkSteel_v003.MI_CA_S02DeepDraw_Ram_DarkSteel_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Blankholder_CleanSteel_v003.MI_CA_S02DeepDraw_Blankholder_CleanSteel_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Bolster_CleanSteel_v003.MI_CA_S02DeepDraw_Bolster_CleanSteel_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_Flywheel_DarkSteel_v003.MI_CA_S02DeepDraw_Flywheel_DarkSteel_v003"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/S02DeepDraw_v003/Materials/MI_CA_S02DeepDraw_SafetyGate_SafetyYellow_v003.MI_CA_S02DeepDraw_SafetyGate_SafetyYellow_v003")
    };
    enum ES02DeepDrawMaterialIndex : int32
    {
        S02StaticMainGreen = 0,
        S02StaticConcrete,
        S02StaticDarkSteel,
        S02StaticCleanSteel,
        S02StaticCharcoalGrey,
        S02StaticSafetyYellow,
        S02StaticScreenDark,
        S02StaticLampGreen,
        S02StaticLampAmber,
        S02StaticLampRed,
        S02RamDarkSteel,
        S02BlankholderCleanSteel,
        S02BolsterCleanSteel,
        S02FlywheelDarkSteel,
        S02SafetyGateSafetyYellow
    };
    const TCHAR* S03S06StagePackRoot = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "SharedTrainModules_v003/");
    const TCHAR* S03S06StagePackFrameMeshPaths[] =
    {
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Meshes/SM_CA_MW_PT_S03_Frame_Form_LOD0_v001.SM_CA_MW_PT_S03_Frame_Form_LOD0_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Meshes/SM_CA_MW_PT_S04_Frame_Trim_LOD0_v001.SM_CA_MW_PT_S04_Frame_Trim_LOD0_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Meshes/SM_CA_MW_PT_S05_Frame_Pierce_LOD0_v001.SM_CA_MW_PT_S05_Frame_Pierce_LOD0_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Meshes/SM_CA_MW_PT_S06_Frame_Flange_LOD0_v001.SM_CA_MW_PT_S06_Frame_Flange_LOD0_v001")
    };
    const TCHAR* S03S06StagePackCueMeshPaths[] =
    {
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Meshes/SM_CA_MW_PT_S03_Cue_SecondaryForm_LOD0_v001.SM_CA_MW_PT_S03_Cue_SecondaryForm_LOD0_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Meshes/SM_CA_MW_PT_S04_Cue_TrimScrap_LOD0_v001.SM_CA_MW_PT_S04_Cue_TrimScrap_LOD0_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Meshes/SM_CA_MW_PT_S05_Cue_PierceSlug_LOD0_v001.SM_CA_MW_PT_S05_Cue_PierceSlug_LOD0_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Meshes/SM_CA_MW_PT_S06_Cue_RestrikeQuality_LOD0_v001.SM_CA_MW_PT_S06_Cue_RestrikeQuality_LOD0_v001")
    };
    const TCHAR* S03S06StagePackMaterialMasterPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "SharedTrainModules_v003/Materials/"
        "M_CA_MW_PT_StagePack_PBR_Master_v001.M_CA_MW_PT_StagePack_PBR_Master_v001");
    const TCHAR* S03S06StagePackMaterialPaths[] =
    {
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/MI_CA_MW_PT_CairnwellGreen_v001.MI_CA_MW_PT_CairnwellGreen_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/MI_CA_MW_PT_FoundryCharcoal_v001.MI_CA_MW_PT_FoundryCharcoal_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/MI_CA_MW_PT_ServiceGrey_v001.MI_CA_MW_PT_ServiceGrey_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/MI_CA_MW_PT_SafetyYellow_v001.MI_CA_MW_PT_SafetyYellow_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/MI_CA_MW_PT_WorkedSteel_v001.MI_CA_MW_PT_WorkedSteel_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/MI_CA_MW_PT_InspectionGlass_v001.MI_CA_MW_PT_InspectionGlass_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/MI_CA_MW_PT_TrainAAccent_v001.MI_CA_MW_PT_TrainAAccent_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/MI_CA_MW_PT_StatusGreen_v001.MI_CA_MW_PT_StatusGreen_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/MI_CA_MW_PT_StatusAmber_v001.MI_CA_MW_PT_StatusAmber_v001")
    };
    enum ES03S06StagePackMaterialIndex : int32
    {
        StagePackCairnwellGreen = 0,
        StagePackFoundryCharcoal,
        StagePackServiceGrey,
        StagePackSafetyYellow,
        StagePackWorkedSteel,
        StagePackInspectionGlass,
        StagePackTrainAAccent,
        StagePackStatusGreen,
        StagePackStatusAmber
    };
    const FName S03S06StagePackFrameSlots[] =
    {
        TEXT("CA_MW_FoundryCharcoal"), TEXT("CA_MW_CairnwellGreen"),
        TEXT("CA_MW_ServiceGrey"), TEXT("CA_MW_SafetyYellow"),
        TEXT("CA_MW_InspectionGlass"), TEXT("CA_MW_TrainAAccent"),
        TEXT("CA_MW_WorkedSteel")
    };
    const FName S03S06StagePackS03CueSlots[] =
    {
        TEXT("CA_MW_FoundryCharcoal"), TEXT("CA_MW_ServiceGrey"),
        TEXT("CA_MW_CairnwellGreen"), TEXT("CA_MW_WorkedSteel"),
        TEXT("CA_MW_TrainAAccent"), TEXT("CA_MW_SafetyYellow"),
        TEXT("CA_MW_StatusGreen")
    };
    const FName S03S06StagePackS04CueSlots[] =
    {
        TEXT("CA_MW_FoundryCharcoal"), TEXT("CA_MW_ServiceGrey"),
        TEXT("CA_MW_SafetyYellow"), TEXT("CA_MW_CairnwellGreen"),
        TEXT("CA_MW_WorkedSteel"), TEXT("CA_MW_StatusAmber")
    };
    const FName S03S06StagePackS05CueSlots[] =
    {
        TEXT("CA_MW_FoundryCharcoal"), TEXT("CA_MW_ServiceGrey"),
        TEXT("CA_MW_CairnwellGreen"), TEXT("CA_MW_StatusAmber"),
        TEXT("CA_MW_SafetyYellow"), TEXT("CA_MW_WorkedSteel")
    };
    const FName S03S06StagePackS06CueSlots[] =
    {
        TEXT("CA_MW_FoundryCharcoal"), TEXT("CA_MW_WorkedSteel"),
        TEXT("CA_MW_CairnwellGreen"), TEXT("CA_MW_StatusGreen"),
        TEXT("CA_MW_TrainAAccent")
    };
    struct FS03S06StagePackMeshContract
    {
        const TCHAR* Path;
        FVector DimensionsCm;
        const FName* Slots;
        int32 SlotCount;
    };
    const FS03S06StagePackMeshContract S03S06StagePackFrameContracts[] =
    {
        { S03S06StagePackFrameMeshPaths[0], FVector(648.0f, 620.0f, 950.0f), S03S06StagePackFrameSlots, UE_ARRAY_COUNT(S03S06StagePackFrameSlots) },
        { S03S06StagePackFrameMeshPaths[1], FVector(648.0f, 620.0f, 900.0f), S03S06StagePackFrameSlots, UE_ARRAY_COUNT(S03S06StagePackFrameSlots) },
        { S03S06StagePackFrameMeshPaths[2], FVector(648.0f, 620.0f, 850.0f), S03S06StagePackFrameSlots, UE_ARRAY_COUNT(S03S06StagePackFrameSlots) },
        { S03S06StagePackFrameMeshPaths[3], FVector(648.0f, 620.0f, 900.0f), S03S06StagePackFrameSlots, UE_ARRAY_COUNT(S03S06StagePackFrameSlots) }
    };
    const FS03S06StagePackMeshContract S03S06StagePackCueContracts[] =
    {
        { S03S06StagePackCueMeshPaths[0], FVector(56.5f, 222.0f, 178.0f), S03S06StagePackS03CueSlots, UE_ARRAY_COUNT(S03S06StagePackS03CueSlots) },
        { S03S06StagePackCueMeshPaths[1], FVector(68.0f, 232.0f, 225.0f), S03S06StagePackS04CueSlots, UE_ARRAY_COUNT(S03S06StagePackS04CueSlots) },
        { S03S06StagePackCueMeshPaths[2], FVector(71.5f, 226.0f, 224.0f), S03S06StagePackS05CueSlots, UE_ARRAY_COUNT(S03S06StagePackS05CueSlots) },
        { S03S06StagePackCueMeshPaths[3], FVector(54.5f, 224.0f, 178.0f), S03S06StagePackS06CueSlots, UE_ARRAY_COUNT(S03S06StagePackS06CueSlots) }
    };

    int32 GetS03S06StagePackMaterialIndex(const FName SlotName)
    {
        if (SlotName == TEXT("CA_MW_CairnwellGreen")) return StagePackCairnwellGreen;
        if (SlotName == TEXT("CA_MW_FoundryCharcoal")) return StagePackFoundryCharcoal;
        if (SlotName == TEXT("CA_MW_ServiceGrey")) return StagePackServiceGrey;
        if (SlotName == TEXT("CA_MW_SafetyYellow")) return StagePackSafetyYellow;
        if (SlotName == TEXT("CA_MW_WorkedSteel")) return StagePackWorkedSteel;
        if (SlotName == TEXT("CA_MW_InspectionGlass")) return StagePackInspectionGlass;
        if (SlotName == TEXT("CA_MW_TrainAAccent")) return StagePackTrainAAccent;
        if (SlotName == TEXT("CA_MW_StatusGreen")) return StagePackStatusGreen;
        if (SlotName == TEXT("CA_MW_StatusAmber")) return StagePackStatusAmber;
        return INDEX_NONE;
    }

    // Imported by Unreal 5.8's native legacy FbxFactory with the verified
    // v002 pivot-safe recipe.  These are the promoted content assets, not the
    // source FBXs; their MaterialFlow-specific instances are deliberately kept
    // alongside the shared StagePack library used for the common families.
    const TCHAR* MaterialFlowPackRoot = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
        "MaterialFlowPack_v002/");
    const TCHAR* MaterialFlowMeshPaths[] =
    {
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01CoilCart_v001.SM_CA_MW_PT_S01CoilCart_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01CoilRack_v001.SM_CA_MW_PT_S01CoilRack_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01DecoilerBase_v001.SM_CA_MW_PT_S01DecoilerBase_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01DecoilerSpindle_v001.SM_CA_MW_PT_S01DecoilerSpindle_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01StraightenerFeed_v001.SM_CA_MW_PT_S01StraightenerFeed_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S01FeedBridge_v001.SM_CA_MW_PT_S01FeedBridge_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorBelt_v001.SM_CA_MW_PT_S07ExitConveyorBelt_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07ExitConveyorFrame_v001.SM_CA_MW_PT_S07ExitConveyorFrame_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07InspectionCell_v001.SM_CA_MW_PT_S07InspectionCell_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Meshes/SM_CA_MW_PT_S07OutboundDunnage_v001.SM_CA_MW_PT_S07OutboundDunnage_v001")
    };
    const TCHAR* MaterialFlowMaterialPaths[] =
    {
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Materials/MI_CA_MW_PT_DarkRubber_v001.MI_CA_MW_PT_DarkRubber_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Materials/MI_CA_MW_PT_GalvanizedCoil_v001.MI_CA_MW_PT_GalvanizedCoil_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Materials/MI_CA_MW_PT_StampedPanel_v001.MI_CA_MW_PT_StampedPanel_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/Materials/MI_CA_MW_PT_TaskLightGlass_v001.MI_CA_MW_PT_TaskLightGlass_v001")
    };
    enum EMaterialFlowMaterialIndex : int32
    {
        MaterialFlowDarkRubber = 0,
        MaterialFlowGalvanizedCoil,
        MaterialFlowStampedPanel,
        MaterialFlowTaskLightGlass
    };
    struct FMaterialFlowMeshContract
    {
        const TCHAR* Path;
        FVector DimensionsCm;
        int32 SlotCount;
    };
    const FMaterialFlowMeshContract MaterialFlowMeshContracts[] =
    {
        { MaterialFlowMeshPaths[0], FVector(200.0f, 161.0f, 68.50256f), 4 },
        { MaterialFlowMeshPaths[1], FVector(327.0f, 480.00002f, 168.0f), 5 },
        { MaterialFlowMeshPaths[2], FVector(279.50001f, 177.0f, 225.50807f), 7 },
        { MaterialFlowMeshPaths[3], FVector(161.0f, 144.0f, 144.0f), 3 },
        { MaterialFlowMeshPaths[4], FVector(338.0f, 304.0f, 167.5f), 9 },
        { MaterialFlowMeshPaths[5], FVector(110.0f, 428.0f, 135.0f), 5 },
        { MaterialFlowMeshPaths[6], FVector(150.0f, 460.00002f, 28.0f), 1 },
        { MaterialFlowMeshPaths[7], FVector(250.0f, 505.0f, 98.0f), 6 },
        { MaterialFlowMeshPaths[8], FVector(440.0f, 238.0f, 240.99998f), 10 },
        { MaterialFlowMeshPaths[9], FVector(392.50002f, 330.5f, 149.09938f), 5 }
    };

    const TCHAR* GetMaterialFlowExpectedMaterialPath(const FName SlotName)
    {
        const int32 SharedMaterialIndex = GetS03S06StagePackMaterialIndex(SlotName);
        if (SharedMaterialIndex != INDEX_NONE)
        {
            return S03S06StagePackMaterialPaths[SharedMaterialIndex];
        }
        if (SlotName == TEXT("CA_MW_DarkRubber"))
        {
            return MaterialFlowMaterialPaths[MaterialFlowDarkRubber];
        }
        if (SlotName == TEXT("CA_MW_GalvanizedCoil"))
        {
            return MaterialFlowMaterialPaths[MaterialFlowGalvanizedCoil];
        }
        if (SlotName == TEXT("CA_MW_StampedPanel"))
        {
            return MaterialFlowMaterialPaths[MaterialFlowStampedPanel];
        }
        if (SlotName == TEXT("CA_MW_TaskLightGlass"))
        {
            return MaterialFlowMaterialPaths[MaterialFlowTaskLightGlass];
        }
        return nullptr;
    }

    bool ValidateMaterialFlowMeshAsset(const UStaticMesh* Mesh,
        const FMaterialFlowMeshContract& Contract, FString& OutReason)
    {
        if (!Mesh || !Mesh->GetPathName().Equals(Contract.Path,
                ESearchCase::CaseSensitive))
        {
            OutReason = TEXT("MATERIALFLOW V002 MESH DID NOT RESOLVE TO ITS EXACT NATIVE PATH");
            return false;
        }
        const FVector DimensionsCm = Mesh->GetBounds().BoxExtent * 2.0f;
        const TArray<FStaticMaterial>& Materials = Mesh->GetStaticMaterials();
        if (!DimensionsCm.Equals(Contract.DimensionsCm, 0.5f)
            || Materials.Num() != Contract.SlotCount)
        {
            OutReason = FString::Printf(TEXT(
                "MATERIALFLOW V002 IMPORT RECEIPT DRIFTED (BOUNDS %s, SLOTS %d)"),
                *DimensionsCm.ToString(), Materials.Num());
            return false;
        }
        for (int32 SlotIndex = 0; SlotIndex < Materials.Num(); ++SlotIndex)
        {
            const TCHAR* ExpectedMaterialPath = GetMaterialFlowExpectedMaterialPath(
                Materials[SlotIndex].MaterialSlotName);
            const UMaterialInterface* ActualMaterial = Mesh->GetMaterial(SlotIndex);
            if (!ExpectedMaterialPath || !ActualMaterial
                || !ActualMaterial->GetPathName().Equals(ExpectedMaterialPath,
                    ESearchCase::CaseSensitive))
            {
                OutReason = FString::Printf(TEXT(
                    "MATERIALFLOW V002 MATERIAL SLOT %d DRIFTED FROM ITS NATIVE RECEIPT"),
                    SlotIndex);
                return false;
            }
        }
        return true;
    }

    bool ValidateS03S06StagePackMeshAsset(const UStaticMesh* Mesh,
        const FS03S06StagePackMeshContract& Contract, FString& OutReason)
    {
        if (!Mesh || !Mesh->GetPathName().Equals(Contract.Path,
                ESearchCase::CaseSensitive))
        {
            OutReason = TEXT("S03-S06 STAGEPACK MESH DID NOT RESOLVE TO ITS EXACT NATIVE-AUTHORED PATH");
            return false;
        }
        const FVector DimensionsCm = Mesh->GetBounds().BoxExtent * 2.0f;
        const TArray<FStaticMaterial>& Materials = Mesh->GetStaticMaterials();
        if (!DimensionsCm.Equals(Contract.DimensionsCm, 3.0f)
            || Materials.Num() != Contract.SlotCount)
        {
            OutReason = FString::Printf(TEXT(
                "S03-S06 STAGEPACK IMPORT RECEIPT DRIFTED (BOUNDS %s, SLOTS %d)"),
                *DimensionsCm.ToString(), Materials.Num());
            return false;
        }
        for (int32 SlotIndex = 0; SlotIndex < Contract.SlotCount; ++SlotIndex)
        {
            if (Materials[SlotIndex].MaterialSlotName != Contract.Slots[SlotIndex])
            {
                OutReason = FString::Printf(TEXT(
                    "S03-S06 STAGEPACK MATERIAL SLOT %d DRIFTED FROM ITS RECEIPT"),
                    SlotIndex);
                return false;
            }
        }
        return true;
    }
    const TCHAR* DetailedMaterialPaths[] =
    {
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_AmberSafetyActive_v086.M_CA_MW_PR009_AmberSafetyActive_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_DriveBlue_v086.M_CA_MW_PR009_DriveBlue_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_EStopRed_v086.M_CA_MW_PR009_EStopRed_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LabelWhite_v086.M_CA_MW_PR009_LabelWhite_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v086.M_CA_MW_PR009_LayeredCairnwellGreen_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v086.M_CA_MW_PR009_LayeredFoundryCharcoal_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v086.M_CA_MW_PR009_LayeredSafetyYellow_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredServiceGrey_v086.M_CA_MW_PR009_LayeredServiceGrey_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_MachinedSteel_v086.M_CA_MW_PR009_MachinedSteel_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_OiledBlankSteel_v086.M_CA_MW_PR009_OiledBlankSteel_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_Rubber_v086.M_CA_MW_PR009_Rubber_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_SensorGlass_v086.M_CA_MW_PR009_SensorGlass_v086"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PT_ServiceCopper_v383.M_CA_MW_PT_ServiceCopper_v383")
    };
    const FVector DetailedAggregateLocalLocationCm(9.25f, 2367.5f, 0.0f);
    const FVector DetailedAggregateLocalScale(100.0f, 100.0f, 100.0f);
    // Import preflight proved the authored FBX comes into Unreal at 1.0 units.
    // This is the deliberate layout scale that fits its 6.57 x 6.63 x 8.15 m
    // source envelope to the established 14.5 m station pitch and press height.
    const FVector S02DeepDrawIntegrationScale(1.80f, 1.80f, 1.80f);
    const FVector S02DeepDrawLocalLocationCm(0.0f, -2900.0f, 0.0f);
    const TCHAR* ExpectedPresentationClassPath =
        TEXT("/Script/LineBossCarFactory.LBOneFactoryPressStarterPresentationActor");

    const FLBOneFactoryPressStarterStationState* FindStation(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        const ELBOneFactoryPressStarterRole Role)
    {
        return Layout.Stations.FindByPredicate([Role](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.Role == Role;
        });
    }

    const FLBOneFactoryPressStarterStationState* FindStation(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        const FName StationId)
    {
        return Layout.Stations.FindByPredicate([StationId](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.StationId == StationId;
        });
    }

    bool IsFiniteTransform(const FTransform& Transform)
    {
        const FVector Location = Transform.GetLocation();
        const FVector Scale = Transform.GetScale3D();
        const FQuat Rotation = Transform.GetRotation();
        return !Transform.ContainsNaN() && Rotation.IsNormalized()
            && FMath::IsFinite(Location.X) && FMath::IsFinite(Location.Y)
            && FMath::IsFinite(Location.Z) && FMath::IsFinite(Scale.X)
            && FMath::IsFinite(Scale.Y) && FMath::IsFinite(Scale.Z)
            && Scale.GetMin() > 0.0f;
    }

    bool SameItem(const FLBOneFactoryPressPresentationItem& Left,
        const FLBOneFactoryPressPresentationItem& Right)
    {
        return Left.Version == Right.Version
            && Left.PresentationId == Right.PresentationId
            && Left.StationId == Right.StationId
            && Left.Role == Right.Role
            && Left.Batch == Right.Batch
            && Left.WorldTransform.Equals(Right.WorldTransform,
                TransformTolerance)
            && Left.bRepresentsProcessWIP == Right.bRepresentsProcessWIP;
    }

    FString MakePresentationId(const FName StationId, const FString& Suffix)
    {
        return FString::Printf(TEXT("OF_PRESS_VIS_%s_%s"),
            *StationId.ToString(), *Suffix);
    }

    struct FStationBuilder
    {
        TArray<FLBOneFactoryPressPresentationItem>& Items;
        const FLBOneFactoryPressStarterStationState& Station;

        void Add(const FString& Suffix,
            const ELBOneFactoryPressPresentationBatch Batch,
            const FVector& LocalLocation, const FVector& DimensionsCm,
            const FRotator& LocalRotation = FRotator::ZeroRotator)
        {
            FLBOneFactoryPressPresentationItem& Item =
                Items.AddDefaulted_GetRef();
            Item.PresentationId = FName(*MakePresentationId(
                Station.StationId, Suffix));
            Item.StationId = Station.StationId;
            Item.Role = Station.Role;
            Item.Batch = Batch;
            const FTransform LocalTransform(LocalRotation, LocalLocation,
                DimensionsCm / 100.0f);
            Item.WorldTransform = LocalTransform * Station.WorldTransform;
            Item.bRepresentsProcessWIP = false;
        }

        void AddFootprintAndStatus()
        {
            const FVector Half = Station.FootprintSizeCm * 0.5f;
            constexpr float LineWidthCm = 18.0f;
            constexpr float PaintHeightCm = 4.0f;
            Add(TEXT("FOOTPRINT_SOUTH"),
                ELBOneFactoryPressPresentationBatch::FloorRouteCube,
                FVector(0.0f, -Half.Y + LineWidthCm * 0.5f,
                    PaintHeightCm * 0.5f),
                FVector(Station.FootprintSizeCm.X, LineWidthCm,
                    PaintHeightCm));
            Add(TEXT("FOOTPRINT_NORTH"),
                ELBOneFactoryPressPresentationBatch::FloorRouteCube,
                FVector(0.0f, Half.Y - LineWidthCm * 0.5f,
                    PaintHeightCm * 0.5f),
                FVector(Station.FootprintSizeCm.X, LineWidthCm,
                    PaintHeightCm));
            Add(TEXT("FOOTPRINT_WEST"),
                ELBOneFactoryPressPresentationBatch::FloorRouteCube,
                FVector(-Half.X + LineWidthCm * 0.5f, 0.0f,
                    PaintHeightCm * 0.5f),
                FVector(LineWidthCm,
                    Station.FootprintSizeCm.Y - LineWidthCm * 2.0f,
                    PaintHeightCm));
            Add(TEXT("FOOTPRINT_EAST"),
                ELBOneFactoryPressPresentationBatch::FloorRouteCube,
                FVector(Half.X - LineWidthCm * 0.5f, 0.0f,
                    PaintHeightCm * 0.5f),
                FVector(LineWidthCm,
                    Station.FootprintSizeCm.Y - LineWidthCm * 2.0f,
                    PaintHeightCm));
            const FVector MarkerLocation(Half.X - 90.0f,
                Half.Y - 90.0f, 100.0f);
            Add(TEXT("STATUS_POST"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                MarkerLocation, FVector(32.0f, 32.0f, 200.0f));
            Add(TEXT("STATUS_CAP"),
                ELBOneFactoryPressPresentationBatch::StatusCube,
                MarkerLocation + FVector(0.0f, 0.0f, 125.0f),
                FVector(62.0f, 62.0f, 50.0f));
        }
    };

    void BuildInboundReceiving(
        TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        B.Add(TEXT("AGV_DECK_LOWER"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(-250.0f, 0.0f, 90.0f),
            FVector(1300.0f, 720.0f, 150.0f));
        B.Add(TEXT("AGV_DECK_UPPER"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(-250.0f, 0.0f, 190.0f),
            FVector(980.0f, 560.0f, 80.0f));
        const FVector WheelLocations[] = {
            FVector(-700.0f, -330.0f, 65.0f),
            FVector(200.0f, -330.0f, 65.0f),
            FVector(-700.0f, 330.0f, 65.0f),
            FVector(200.0f, 330.0f, 65.0f)};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(WheelLocations); ++Index)
        {
            B.Add(FString::Printf(TEXT("AGV_WHEEL_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::GraphiteCylinder,
                WheelLocations[Index], FVector(170.0f, 170.0f, 90.0f),
                FRotator(0.0f, 0.0f, 90.0f));
        }
        B.Add(TEXT("DELIVERY_COIL"),
            ELBOneFactoryPressPresentationBatch::GraphiteCylinder,
            FVector(-250.0f, 0.0f, 390.0f),
            FVector(480.0f, 480.0f, 580.0f),
            FRotator(0.0f, 0.0f, 90.0f));
        B.Add(TEXT("COIL_CRADLE_LEFT"),
            ELBOneFactoryPressPresentationBatch::SafetyCube,
            FVector(-250.0f, -270.0f, 270.0f),
            FVector(720.0f, 90.0f, 120.0f));
        B.Add(TEXT("COIL_CRADLE_RIGHT"),
            ELBOneFactoryPressPresentationBatch::SafetyCube,
            FVector(-250.0f, 270.0f, 270.0f),
            FVector(720.0f, 90.0f, 120.0f));
        B.Add(TEXT("UNLOAD_ARCH_LEFT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(850.0f, -650.0f, 325.0f),
            FVector(140.0f, 140.0f, 650.0f));
        B.Add(TEXT("UNLOAD_ARCH_RIGHT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(850.0f, 650.0f, 325.0f),
            FVector(140.0f, 140.0f, 650.0f));
        B.Add(TEXT("UNLOAD_ARCH_BEAM"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(850.0f, 0.0f, 650.0f),
            FVector(160.0f, 1440.0f, 150.0f));
        B.AddFootprintAndStatus();
    }

    void BuildCoilStore(TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        int32 CoilIndex = 0;
        for (int32 Row = 0; Row < 2; ++Row)
        {
            for (int32 Column = 0; Column < 3; ++Column)
            {
                ++CoilIndex;
                const FVector Centre(-950.0f + Column * 950.0f,
                    -520.0f + Row * 1040.0f, 350.0f);
                B.Add(FString::Printf(TEXT("COIL_%02d"), CoilIndex),
                    ELBOneFactoryPressPresentationBatch::GraphiteCylinder,
                    Centre, FVector(520.0f, 520.0f, 650.0f),
                    FRotator(0.0f, 0.0f, 90.0f));
                B.Add(FString::Printf(TEXT("CRADLE_%02d_LEFT"), CoilIndex),
                    ELBOneFactoryPressPresentationBatch::SafetyCube,
                    Centre + FVector(0.0f, -310.0f, -220.0f),
                    FVector(720.0f, 80.0f, 100.0f));
                B.Add(FString::Printf(TEXT("CRADLE_%02d_RIGHT"), CoilIndex),
                    ELBOneFactoryPressPresentationBatch::SafetyCube,
                    Centre + FVector(0.0f, 310.0f, -220.0f),
                    FVector(720.0f, 80.0f, 100.0f));
                B.Add(FString::Printf(TEXT("STORE_PAD_%02d"), CoilIndex),
                    ELBOneFactoryPressPresentationBatch::TealStructureCube,
                    Centre + FVector(0.0f, 0.0f, -300.0f),
                    FVector(760.0f, 780.0f, 70.0f));
            }
        }
        const FVector PostLocations[] = {
            FVector(-1650.0f, -1050.0f, 300.0f),
            FVector(1650.0f, -1050.0f, 300.0f),
            FVector(-1650.0f, 1050.0f, 300.0f),
            FVector(1650.0f, 1050.0f, 300.0f)};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(PostLocations); ++Index)
        {
            B.Add(FString::Printf(TEXT("STORE_POST_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                PostLocations[Index], FVector(100.0f, 100.0f, 600.0f));
        }
        B.Add(TEXT("STORE_BEAM_SOUTH"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, -1050.0f, 600.0f),
            FVector(3400.0f, 100.0f, 100.0f));
        B.Add(TEXT("STORE_BEAM_NORTH"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, 1050.0f, 600.0f),
            FVector(3400.0f, 100.0f, 100.0f));
        B.AddFootprintAndStatus();
    }

    void BuildBlankPreparation(
        TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        B.Add(TEXT("PREP_FOUNDATION"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, 0.0f, 35.0f),
            FVector(4200.0f, 1600.0f, 70.0f));
        B.Add(TEXT("DECOILER_COIL"),
            ELBOneFactoryPressPresentationBatch::GraphiteCylinder,
            FVector(-1850.0f, 0.0f, 390.0f),
            FVector(620.0f, 620.0f, 720.0f),
            FRotator(0.0f, 0.0f, 90.0f));
        B.Add(TEXT("DECOILER_HUB"),
            ELBOneFactoryPressPresentationBatch::SteelCylinder,
            FVector(-1850.0f, 0.0f, 390.0f),
            FVector(210.0f, 210.0f, 900.0f),
            FRotator(0.0f, 0.0f, 90.0f));
        for (int32 Index = 0; Index < 4; ++Index)
        {
            B.Add(FString::Printf(TEXT("FEED_ROLLER_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::SteelCylinder,
                FVector(-1050.0f + Index * 520.0f, 0.0f, 245.0f),
                FVector(150.0f, 150.0f, 1050.0f),
                FRotator(0.0f, 0.0f, 90.0f));
        }
        for (int32 Index = 0; Index < 3; ++Index)
        {
            B.Add(FString::Printf(TEXT("FEED_BED_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(-1100.0f + Index * 900.0f, 0.0f, 140.0f),
                FVector(780.0f, 1250.0f, 120.0f));
        }
        const FVector FramePosts[] = {
            FVector(-500.0f, -700.0f, 390.0f),
            FVector(-500.0f, 700.0f, 390.0f),
            FVector(1350.0f, -700.0f, 390.0f),
            FVector(1350.0f, 700.0f, 390.0f)};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(FramePosts); ++Index)
        {
            B.Add(FString::Printf(TEXT("PREP_FRAME_POST_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FramePosts[Index], FVector(120.0f, 120.0f, 720.0f));
        }
        B.Add(TEXT("PREP_FRAME_BEAM_SOUTH"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(425.0f, -700.0f, 750.0f),
            FVector(1970.0f, 120.0f, 120.0f));
        B.Add(TEXT("PREP_FRAME_BEAM_NORTH"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(425.0f, 700.0f, 750.0f),
            FVector(1970.0f, 120.0f, 120.0f));
        B.Add(TEXT("CUTTER_CROWN"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(1350.0f, 0.0f, 700.0f),
            FVector(500.0f, 1500.0f, 180.0f));
        B.Add(TEXT("CUTTER_SLIDE"),
            ELBOneFactoryPressPresentationBatch::SteelCube,
            FVector(1350.0f, 0.0f, 465.0f),
            FVector(280.0f, 1250.0f, 130.0f));
        B.Add(TEXT("PREP_CONSOLE"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(1950.0f, -720.0f, 180.0f),
            FVector(380.0f, 420.0f, 360.0f));
        B.Add(TEXT("PREP_SCREEN"),
            ELBOneFactoryPressPresentationBatch::StatusCube,
            FVector(1950.0f, -935.0f, 300.0f),
            FVector(240.0f, 25.0f, 120.0f));
        for (int32 Index = 0; Index < 4; ++Index)
        {
            B.Add(FString::Printf(TEXT("EXIT_BLANK_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::SteelCube,
                FVector(1850.0f, 100.0f, 185.0f + Index * 20.0f),
                FVector(650.0f, 1050.0f, 12.0f));
        }
        B.AddFootprintAndStatus();
    }

    void BuildPreparedBlankAndDieBuffer(
        TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        const float StackX[] = {-760.0f, 0.0f, 760.0f};
        for (int32 Stack = 0; Stack < UE_ARRAY_COUNT(StackX); ++Stack)
        {
            B.Add(FString::Printf(TEXT("BLANK_PALLET_%02d"), Stack + 1),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(StackX[Stack], -430.0f, 55.0f),
                FVector(620.0f, 850.0f, 110.0f));
            for (int32 Sheet = 0; Sheet < 4; ++Sheet)
            {
                B.Add(FString::Printf(TEXT("BLANK_%02d_%02d"),
                        Stack + 1, Sheet + 1),
                    ELBOneFactoryPressPresentationBatch::SteelCube,
                    FVector(StackX[Stack], -430.0f,
                        120.0f + Sheet * 18.0f),
                    FVector(570.0f, 790.0f, 10.0f));
            }
        }
        const FVector RackPosts[] = {
            FVector(-1120.0f, 860.0f, 330.0f),
            FVector(1120.0f, 860.0f, 330.0f),
            FVector(-1120.0f, 180.0f, 330.0f),
            FVector(1120.0f, 180.0f, 330.0f)};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(RackPosts); ++Index)
        {
            B.Add(FString::Printf(TEXT("DIE_RACK_POST_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                RackPosts[Index], FVector(100.0f, 100.0f, 660.0f));
        }
        B.Add(TEXT("DIE_RACK_BEAM_FRONT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, 180.0f, 650.0f),
            FVector(2340.0f, 100.0f, 100.0f));
        B.Add(TEXT("DIE_RACK_BEAM_REAR"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, 860.0f, 650.0f),
            FVector(2340.0f, 100.0f, 100.0f));
        for (int32 Die = 0; Die < 3; ++Die)
        {
            const float X = -720.0f + Die * 720.0f;
            B.Add(FString::Printf(TEXT("DIE_PALLET_%02d"), Die + 1),
                ELBOneFactoryPressPresentationBatch::SafetyCube,
                FVector(X, 520.0f, 85.0f),
                FVector(590.0f, 520.0f, 90.0f));
            B.Add(FString::Printf(TEXT("DIE_TOOL_%02d"), Die + 1),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(X, 520.0f, 210.0f),
                FVector(480.0f, 400.0f, 170.0f));
        }
        B.AddFootprintAndStatus();
    }

    void BuildPressTrain(TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        for (int32 Stage = 0; Stage < 7; ++Stage)
        {
            const float Y = -3000.0f + Stage * 1000.0f;
            const float ColumnHeight = 400.0f + Stage * 45.0f;
            const FString Prefix = FString::Printf(TEXT("PRESS_STAGE_%02d"),
                Stage + 1);
            B.Add(Prefix + TEXT("_BASE"),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(0.0f, Y, 60.0f),
                FVector(1800.0f, 720.0f, 120.0f));
            B.Add(Prefix + TEXT("_COLUMN_LEFT"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FVector(-700.0f, Y, 100.0f + ColumnHeight * 0.5f),
                FVector(210.0f, 560.0f, ColumnHeight));
            B.Add(Prefix + TEXT("_COLUMN_RIGHT"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FVector(700.0f, Y, 100.0f + ColumnHeight * 0.5f),
                FVector(210.0f, 560.0f, ColumnHeight));
            B.Add(Prefix + TEXT("_CROWN"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FVector(0.0f, Y, 180.0f + ColumnHeight),
                FVector(1700.0f, 620.0f, 160.0f));
            B.Add(Prefix + TEXT("_SLIDE"),
                ELBOneFactoryPressPresentationBatch::SteelCube,
                FVector(0.0f, Y, ColumnHeight),
                FVector(1100.0f, 500.0f, 120.0f));
            B.Add(Prefix + TEXT("_BOLSTER"),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(0.0f, Y, 155.0f),
                FVector(1200.0f, 520.0f, 90.0f));
            B.Add(Prefix + TEXT("_GUARD_LEFT"),
                ELBOneFactoryPressPresentationBatch::SafetyCube,
                FVector(-1030.0f, Y, 175.0f),
                FVector(90.0f, 680.0f, 350.0f));
            B.Add(Prefix + TEXT("_GUARD_RIGHT"),
                ELBOneFactoryPressPresentationBatch::SafetyCube,
                FVector(1030.0f, Y, 175.0f),
                FVector(90.0f, 680.0f, 350.0f));
            B.Add(Prefix + TEXT("_STATUS"),
                ELBOneFactoryPressPresentationBatch::StatusCube,
                FVector(1030.0f, Y, 395.0f),
                FVector(75.0f, 75.0f, 75.0f));
        }
        for (int32 Transfer = 0; Transfer < 8; ++Transfer)
        {
            B.Add(FString::Printf(TEXT("PRESS_TRANSFER_%02d"), Transfer + 1),
                ELBOneFactoryPressPresentationBatch::SteelCube,
                FVector(0.0f, -3500.0f + Transfer * 1000.0f, 105.0f),
                FVector(1120.0f, 250.0f, 90.0f));
        }
        const FVector SilhouetteColumns[] = {
            FVector(-1000.0f, -3500.0f, 450.0f),
            FVector(1000.0f, -3500.0f, 450.0f),
            FVector(-1000.0f, 3500.0f, 450.0f),
            FVector(1000.0f, 3500.0f, 450.0f)};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(SilhouetteColumns); ++Index)
        {
            B.Add(FString::Printf(TEXT("HIGH_GANTRY_COLUMN_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                SilhouetteColumns[Index], FVector(120.0f, 120.0f, 900.0f));
        }
        B.Add(TEXT("HIGH_GANTRY_RAIL_LEFT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(-1000.0f, 0.0f, 850.0f),
            FVector(120.0f, 7500.0f, 120.0f));
        B.Add(TEXT("HIGH_GANTRY_RAIL_RIGHT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(1000.0f, 0.0f, 850.0f),
            FVector(120.0f, 7500.0f, 120.0f));
        const float BridgeY[] = {-2500.0f, 0.0f, 2500.0f};
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(BridgeY); ++Index)
        {
            B.Add(FString::Printf(TEXT("HIGH_CRANE_BRIDGE_%02d"), Index + 1),
                ELBOneFactoryPressPresentationBatch::SafetyCube,
                FVector(0.0f, BridgeY[Index], 830.0f),
                FVector(2200.0f, 120.0f, 120.0f));
        }
        B.Add(TEXT("HIGH_CRANE_HOIST"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(0.0f, 0.0f, 740.0f),
            FVector(260.0f, 260.0f, 180.0f));
        B.Add(TEXT("HIGH_CRANE_HOOK"),
            ELBOneFactoryPressPresentationBatch::SteelCylinder,
            FVector(0.0f, 0.0f, 610.0f),
            FVector(80.0f, 80.0f, 180.0f));
        B.AddFootprintAndStatus();
    }

    void BuildInspection(TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        B.Add(TEXT("INSPECTION_TABLE"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(-150.0f, 0.0f, 150.0f),
            FVector(1500.0f, 1100.0f, 300.0f));
        B.Add(TEXT("INSPECTION_SURFACE"),
            ELBOneFactoryPressPresentationBatch::SteelCube,
            FVector(-150.0f, 0.0f, 315.0f),
            FVector(1400.0f, 1000.0f, 30.0f));
        B.Add(TEXT("SCANNER_POST_LEFT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(-760.0f, 0.0f, 390.0f),
            FVector(120.0f, 120.0f, 780.0f));
        B.Add(TEXT("SCANNER_POST_RIGHT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(460.0f, 0.0f, 390.0f),
            FVector(120.0f, 120.0f, 780.0f));
        B.Add(TEXT("SCANNER_BEAM"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(-150.0f, 0.0f, 760.0f),
            FVector(1340.0f, 140.0f, 140.0f));
        B.Add(TEXT("SCANNER_HEAD_LEFT"),
            ELBOneFactoryPressPresentationBatch::SteelCylinder,
            FVector(-450.0f, 0.0f, 650.0f),
            FVector(110.0f, 110.0f, 180.0f));
        B.Add(TEXT("SCANNER_HEAD_RIGHT"),
            ELBOneFactoryPressPresentationBatch::SteelCylinder,
            FVector(150.0f, 0.0f, 650.0f),
            FVector(110.0f, 110.0f, 180.0f));
        B.Add(TEXT("DISPLAY_PANEL"),
            ELBOneFactoryPressPresentationBatch::SteelCube,
            FVector(-150.0f, 0.0f, 345.0f),
            FVector(900.0f, 650.0f, 16.0f));
        B.Add(TEXT("LIGHT_BAR_LEFT"),
            ELBOneFactoryPressPresentationBatch::StatusCube,
            FVector(-760.0f, -180.0f, 700.0f),
            FVector(50.0f, 280.0f, 50.0f));
        B.Add(TEXT("LIGHT_BAR_RIGHT"),
            ELBOneFactoryPressPresentationBatch::StatusCube,
            FVector(460.0f, -180.0f, 700.0f),
            FVector(50.0f, 280.0f, 50.0f));
        B.Add(TEXT("INSPECTION_CONSOLE"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(800.0f, -650.0f, 180.0f),
            FVector(360.0f, 320.0f, 360.0f));
        B.Add(TEXT("INSPECTION_SCREEN"),
            ELBOneFactoryPressPresentationBatch::StatusCube,
            FVector(800.0f, -825.0f, 300.0f),
            FVector(230.0f, 30.0f, 120.0f));
        B.AddFootprintAndStatus();
    }

    void BuildDispatch(TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterStationState& Station)
    {
        FStationBuilder B{Items, Station};
        for (int32 Stillage = 0; Stillage < 3; ++Stillage)
        {
            const float X = -780.0f + Stillage * 780.0f;
            const FString Prefix = FString::Printf(TEXT("EMPTY_STILLAGE_%02d"),
                Stillage + 1);
            B.Add(Prefix + TEXT("_BASE"),
                ELBOneFactoryPressPresentationBatch::GraphiteCube,
                FVector(X, 360.0f, 65.0f),
                FVector(620.0f, 850.0f, 130.0f));
            const FVector PostOffsets[] = {
                FVector(-270.0f, -380.0f, 300.0f),
                FVector(270.0f, -380.0f, 300.0f),
                FVector(-270.0f, 380.0f, 300.0f),
                FVector(270.0f, 380.0f, 300.0f)};
            for (int32 Post = 0; Post < UE_ARRAY_COUNT(PostOffsets); ++Post)
            {
                B.Add(Prefix + FString::Printf(TEXT("_POST_%02d"), Post + 1),
                    ELBOneFactoryPressPresentationBatch::TealStructureCube,
                    FVector(X, 360.0f, 0.0f) + PostOffsets[Post],
                    FVector(70.0f, 70.0f, 600.0f));
            }
            B.Add(Prefix + TEXT("_RAIL_FRONT"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FVector(X, -20.0f, 570.0f),
                FVector(620.0f, 70.0f, 70.0f));
            B.Add(Prefix + TEXT("_RAIL_REAR"),
                ELBOneFactoryPressPresentationBatch::TealStructureCube,
                FVector(X, 740.0f, 570.0f),
                FVector(620.0f, 70.0f, 70.0f));
            B.Add(Prefix + TEXT("_EMPTY_BOARD"),
                ELBOneFactoryPressPresentationBatch::SafetyCube,
                FVector(X, -35.0f, 410.0f),
                FVector(300.0f, 30.0f, 130.0f));
        }
        B.Add(TEXT("DISPATCH_AGV_DECK"),
            ELBOneFactoryPressPresentationBatch::GraphiteCube,
            FVector(0.0f, -650.0f, 90.0f),
            FVector(1250.0f, 560.0f, 150.0f));
        B.Add(TEXT("DISPATCH_AGV_TOP"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(0.0f, -650.0f, 185.0f),
            FVector(900.0f, 430.0f, 70.0f));
        const float WheelX[] = {-450.0f, 450.0f};
        const float WheelY[] = {-880.0f, -420.0f};
        int32 Wheel = 0;
        for (const float X : WheelX)
        {
            for (const float Y : WheelY)
            {
                ++Wheel;
                B.Add(FString::Printf(TEXT("DISPATCH_AGV_WHEEL_%02d"), Wheel),
                    ELBOneFactoryPressPresentationBatch::GraphiteCylinder,
                    FVector(X, Y, 65.0f), FVector(150.0f, 150.0f, 80.0f),
                    FRotator(0.0f, 0.0f, 90.0f));
            }
        }
        B.Add(TEXT("DISPATCH_SIGN_LEFT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(-850.0f, -900.0f, 360.0f),
            FVector(100.0f, 100.0f, 720.0f));
        B.Add(TEXT("DISPATCH_SIGN_RIGHT"),
            ELBOneFactoryPressPresentationBatch::TealStructureCube,
            FVector(850.0f, -900.0f, 360.0f),
            FVector(100.0f, 100.0f, 720.0f));
        B.Add(TEXT("DISPATCH_SIGN_TOP"),
            ELBOneFactoryPressPresentationBatch::SafetyCube,
            FVector(0.0f, -900.0f, 700.0f),
            FVector(1800.0f, 120.0f, 120.0f));
        B.AddFootprintAndStatus();
    }

    void AddMaterialRoutes(TArray<FLBOneFactoryPressPresentationItem>& Items,
        const FLBOneFactoryPressStarterLayoutState& Layout)
    {
        for (const FLBOneFactoryPressStarterConnectionState& Connection :
            Layout.Connections)
        {
            const FLBOneFactoryPressStarterStationState* Source =
                FindStation(Layout, Connection.SourceStationId);
            const FLBOneFactoryPressStarterStationState* Target =
                FindStation(Layout, Connection.TargetStationId);
            if (!Source || !Target) continue;
            const FVector Start = Source->WorldTransform.GetLocation();
            const FVector End = Target->WorldTransform.GetLocation();
            const FVector Delta = End - Start;
            const float Length = Delta.Size2D();
            if (Length <= KINDA_SMALL_NUMBER) continue;
            FLBOneFactoryPressPresentationItem& Item =
                Items.AddDefaulted_GetRef();
            Item.PresentationId = FName(*FString::Printf(TEXT("OF_PRESS_VIS_%s"),
                *Connection.ConnectionId.ToString()));
            Item.StationId = Target->StationId;
            Item.Role = Target->Role;
            Item.Batch = ELBOneFactoryPressPresentationBatch::FloorRouteCube;
            const float Yaw = FMath::RadiansToDegrees(
                FMath::Atan2(Delta.Y, Delta.X));
            Item.WorldTransform = FTransform(FRotator(0.0f, Yaw, 0.0f),
                (Start + End) * 0.5f + FVector(0.0f, 0.0f, 3.0f),
                FVector(Length / 100.0f, 0.22f, 0.06f));
            Item.bRepresentsProcessWIP = false;
        }
    }
}

ALBOneFactoryPressStarterPresentationActor::
    ALBOneFactoryPressStarterPresentationActor()
{
    // The retained visual body remains a static aggregate.  These independently
    // movable parts are deliberately owned by Unreal so the visible production
    // cycle is real component motion rather than a baked/Meshy animation.
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    SetReplicates(false);
    SetActorEnableCollision(false);

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SceneRoot->SetMobility(EComponentMobility::Movable);
    SetRootComponent(SceneRoot);

    DetailedPresentationA = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("DetailedPresentationA"));
    DetailedPresentationB = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("DetailedPresentationB"));
    for (UStaticMeshComponent* Component : GetDetailedPresentationComponents())
    {
        if (!Component) continue;
        Component->SetupAttachment(SceneRoot);
        ConfigureDetailedPresentationComponent(Component);
    }
    S02DeepDrawPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S02DeepDrawPresentation"));
    S02DeepDrawBlankholderPresentation =
        CreateDefaultSubobject<UStaticMeshComponent>(
            TEXT("S02DeepDrawBlankholderPresentation"));
    S02DeepDrawBolsterPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S02DeepDrawBolsterPresentation"));
    S02DeepDrawFlywheelPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S02DeepDrawFlywheelPresentation"));
    S02DeepDrawSafetyGatePresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S02DeepDrawSafetyGatePresentation"));
    for (UStaticMeshComponent* Component : GetS02DeepDrawPresentationComponents())
    {
        if (!Component) continue;
        Component->SetupAttachment(SceneRoot);
        ConfigureDetailedPresentationComponent(Component);
    }
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackFrameMeshPaths);
        ++Index)
    {
        UStaticMeshComponent* Frame = CreateDefaultSubobject<UStaticMeshComponent>(
            *FString::Printf(TEXT("S%02dStagePackFramePresentation"), Index + 3));
        UStaticMeshComponent* Cue = CreateDefaultSubobject<UStaticMeshComponent>(
            *FString::Printf(TEXT("S%02dStagePackCuePresentation"), Index + 3));
        Frame->SetupAttachment(SceneRoot);
        Cue->SetupAttachment(SceneRoot);
        ConfigureDetailedPresentationComponent(Frame);
        ConfigureDetailedPresentationComponent(Cue);
        S03S06StagePackFrames.Add(Frame);
        S03S06StagePackCues.Add(Cue);
    }

    S01CoilCartMover = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S01CoilCartMover"));
    S01CoilRackPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S01CoilRackPresentation"));
    S01DecoilerBasePresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S01DecoilerBasePresentation"));
    S01DecoilerSpindleMover = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S01DecoilerSpindleMover"));
    S01StraightenerFeedPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S01StraightenerFeedPresentation"));
    S01FeedBridgePresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S01FeedBridgePresentation"));
    S07ExitConveyorBeltPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S07ExitConveyorBeltPresentation"));
    S07ExitConveyorFramePresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S07ExitConveyorFramePresentation"));
    S07InspectionCellPresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S07InspectionCellPresentation"));
    S07OutboundDunnagePresentation = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S07OutboundDunnagePresentation"));
    for (UStaticMeshComponent* Component : GetMaterialFlowPresentationComponents())
    {
        if (!Component) continue;
        Component->SetupAttachment(SceneRoot);
        ConfigureDetailedPresentationComponent(Component);
    }

    StationBases = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("NativeStationBases"));
    StationColumns = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("NativeStationColumns"));
    StationCrowns = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("NativeStationCrowns"));
    StationTables = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("NativeStationTables"));
    SafetyFrames = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("NativeSafetyFrames"));
    TransferRails = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("NativeTransferRails"));
    ServiceRuns = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("NativeServiceRuns"));
    AccessPlatforms = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("NativeAccessPlatforms"));
    ControlKiosks = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("NativeControlKiosks"));
    SignalLights = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("NativeSignalLights"));
    for (UInstancedStaticMeshComponent* Component : { StationBases.Get(),
            StationColumns.Get(), StationCrowns.Get(), StationTables.Get(),
            SafetyFrames.Get(), TransferRails.Get(), ServiceRuns.Get(),
            AccessPlatforms.Get(), ControlKiosks.Get(), SignalLights.Get() })
    {
        Component->SetupAttachment(SceneRoot);
        ConfigureNativeBatchComponent(Component);
    }
    for (int32 Index = 0; Index < 7; ++Index)
    {
        UTextRenderComponent* Label = CreateDefaultSubobject<UTextRenderComponent>(
            *FString::Printf(TEXT("NativeStationLabel_S%02d"), Index + 1));
        Label->SetupAttachment(SceneRoot);
        Label->SetHorizontalAlignment(EHTA_Center);
        Label->SetVerticalAlignment(EVRTA_TextCenter);
        Label->SetWorldSize(48.0f);
        Label->SetTextRenderColor(FColor(245, 245, 235));
        Label->SetVisibility(false, true);
        Label->SetHiddenInGame(true, true);
        StationLabels.Add(Label);
    }

    TransferCarriage = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("PressTransferCarriage"));
    TransferBeam = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("PressTransferBeam"));
    TransferGripperFrame = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("PressTransferGripperFrame"));
    DestackLift = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S01DestackLift"));
    UnloadRobotArm = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S07UnloadRobotArm"));
    UnloadRobotGripper = CreateDefaultSubobject<UStaticMeshComponent>(
        TEXT("S07UnloadRobotGripper"));
    TransferCarriage->SetupAttachment(SceneRoot);
    TransferBeam->SetupAttachment(SceneRoot);
    TransferGripperFrame->SetupAttachment(SceneRoot);
    DestackLift->SetupAttachment(SceneRoot);
    UnloadRobotArm->SetupAttachment(SceneRoot);
    UnloadRobotGripper->SetupAttachment(SceneRoot);
    ConfigureMotionComponent(TransferCarriage);
    ConfigureMotionComponent(TransferBeam);
    ConfigureMotionComponent(TransferGripperFrame);
    ConfigureMotionComponent(DestackLift);
    ConfigureMotionComponent(UnloadRobotArm);
    ConfigureMotionComponent(UnloadRobotGripper);
    for (int32 Index = 0; Index < 5; ++Index)
    {
        UStaticMeshComponent* Ram = CreateDefaultSubobject<UStaticMeshComponent>(
            *FString::Printf(TEXT("PressRam_%02d"), Index + 2));
        Ram->SetupAttachment(SceneRoot);
        ConfigureMotionComponent(Ram);
        PressRams.Add(Ram);
    }

    static ConstructorHelpers::FObjectFinder<UStaticMesh> DetailedMeshFinder(
        LBOneFactoryPressPresentationPrivate::DetailedMeshPath);
    DetailedPresentationMesh = DetailedMeshFinder.Succeeded()
        ? DetailedMeshFinder.Object : nullptr;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> S02DeepDrawStaticFinder(
        LBOneFactoryPressPresentationPrivate::S02DeepDrawStaticMeshPath);
    S02DeepDrawStaticMesh = S02DeepDrawStaticFinder.Succeeded()
        ? S02DeepDrawStaticFinder.Object : nullptr;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> S02DeepDrawRamFinder(
        LBOneFactoryPressPresentationPrivate::S02DeepDrawRamMeshPath);
    S02DeepDrawRamMesh = S02DeepDrawRamFinder.Succeeded()
        ? S02DeepDrawRamFinder.Object : nullptr;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> S02DeepDrawBlankholderFinder(
        LBOneFactoryPressPresentationPrivate::S02DeepDrawBlankholderMeshPath);
    S02DeepDrawBlankholderMesh = S02DeepDrawBlankholderFinder.Succeeded()
        ? S02DeepDrawBlankholderFinder.Object : nullptr;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> S02DeepDrawBolsterFinder(
        LBOneFactoryPressPresentationPrivate::S02DeepDrawBolsterMeshPath);
    S02DeepDrawBolsterMesh = S02DeepDrawBolsterFinder.Succeeded()
        ? S02DeepDrawBolsterFinder.Object : nullptr;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> S02DeepDrawFlywheelFinder(
        LBOneFactoryPressPresentationPrivate::S02DeepDrawFlywheelMeshPath);
    S02DeepDrawFlywheelMesh = S02DeepDrawFlywheelFinder.Succeeded()
        ? S02DeepDrawFlywheelFinder.Object : nullptr;

    static ConstructorHelpers::FObjectFinder<UStaticMesh> S02DeepDrawSafetyGateFinder(
        LBOneFactoryPressPresentationPrivate::S02DeepDrawSafetyGateMeshPath);
    S02DeepDrawSafetyGateMesh = S02DeepDrawSafetyGateFinder.Succeeded()
        ? S02DeepDrawSafetyGateFinder.Object : nullptr;

    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02DeepDrawMaterialMasterFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialMasterPath);
    S02DeepDrawMaterialMaster = S02DeepDrawMaterialMasterFinder.Succeeded()
        ? S02DeepDrawMaterialMasterFinder.Object : nullptr;

    // These are static constructor helpers deliberately.  The actor can be
    // instantiated by the builder as well as by editor/automation worlds, and
    // the v003 PBR closure must be resolved once while the CDO is constructed,
    // then copied as hard references rather than synchronously loaded again by
    // every live presentation actor.
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02StaticMainGreenFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02StaticMainGreen]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02StaticConcreteFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02StaticConcrete]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02StaticDarkSteelFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02StaticDarkSteel]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02StaticCleanSteelFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02StaticCleanSteel]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02StaticCharcoalGreyFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02StaticCharcoalGrey]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02StaticSafetyYellowFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02StaticSafetyYellow]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02StaticScreenDarkFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02StaticScreenDark]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02StaticLampGreenFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02StaticLampGreen]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02StaticLampAmberFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02StaticLampAmber]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02StaticLampRedFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02StaticLampRed]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02RamDarkSteelFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02RamDarkSteel]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02BlankholderCleanSteelFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02BlankholderCleanSteel]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02BolsterCleanSteelFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02BolsterCleanSteel]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02FlywheelDarkSteelFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02FlywheelDarkSteel]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S02SafetyGateSafetyYellowFinder(
            LBOneFactoryPressPresentationPrivate::S02DeepDrawMaterialPaths[
                LBOneFactoryPressPresentationPrivate::S02SafetyGateSafetyYellow]);
    const ConstructorHelpers::FObjectFinder<UMaterialInterface>* const
        S02DeepDrawMaterialFinders[] =
    {
        &S02StaticMainGreenFinder,
        &S02StaticConcreteFinder,
        &S02StaticDarkSteelFinder,
        &S02StaticCleanSteelFinder,
        &S02StaticCharcoalGreyFinder,
        &S02StaticSafetyYellowFinder,
        &S02StaticScreenDarkFinder,
        &S02StaticLampGreenFinder,
        &S02StaticLampAmberFinder,
        &S02StaticLampRedFinder,
        &S02RamDarkSteelFinder,
        &S02BlankholderCleanSteelFinder,
        &S02BolsterCleanSteelFinder,
        &S02FlywheelDarkSteelFinder,
        &S02SafetyGateSafetyYellowFinder
    };
    S02DeepDrawMaterialLibrary.Reset();
    S02DeepDrawMaterialLibrary.Reserve(
        UE_ARRAY_COUNT(LBOneFactoryPressPresentationPrivate::
            S02DeepDrawMaterialPaths));
    for (const ConstructorHelpers::FObjectFinder<UMaterialInterface>* Finder :
        S02DeepDrawMaterialFinders)
    {
        S02DeepDrawMaterialLibrary.Add(Finder->Succeeded() ? Finder->Object : nullptr);
    }

    static ConstructorHelpers::FObjectFinder<UStaticMesh> S03StagePackFrameFinder(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackFrameMeshPaths[0]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S04StagePackFrameFinder(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackFrameMeshPaths[1]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S05StagePackFrameFinder(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackFrameMeshPaths[2]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S06StagePackFrameFinder(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackFrameMeshPaths[3]);
    const ConstructorHelpers::FObjectFinder<UStaticMesh>* const
        S03S06StagePackFrameFinders[] =
    {
        &S03StagePackFrameFinder, &S04StagePackFrameFinder,
        &S05StagePackFrameFinder, &S06StagePackFrameFinder
    };
    S03S06StagePackFrameMeshes.Reset();
    S03S06StagePackFrameMeshes.Reserve(UE_ARRAY_COUNT(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackFrameMeshPaths));
    for (const ConstructorHelpers::FObjectFinder<UStaticMesh>* Finder :
        S03S06StagePackFrameFinders)
    {
        S03S06StagePackFrameMeshes.Add(Finder->Succeeded() ? Finder->Object : nullptr);
    }

    static ConstructorHelpers::FObjectFinder<UStaticMesh> S03StagePackCueFinder(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackCueMeshPaths[0]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S04StagePackCueFinder(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackCueMeshPaths[1]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S05StagePackCueFinder(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackCueMeshPaths[2]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S06StagePackCueFinder(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackCueMeshPaths[3]);
    const ConstructorHelpers::FObjectFinder<UStaticMesh>* const
        S03S06StagePackCueFinders[] =
    {
        &S03StagePackCueFinder, &S04StagePackCueFinder,
        &S05StagePackCueFinder, &S06StagePackCueFinder
    };
    S03S06StagePackCueMeshes.Reset();
    S03S06StagePackCueMeshes.Reserve(UE_ARRAY_COUNT(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackCueMeshPaths));
    for (const ConstructorHelpers::FObjectFinder<UStaticMesh>* Finder :
        S03S06StagePackCueFinders)
    {
        S03S06StagePackCueMeshes.Add(Finder->Succeeded() ? Finder->Object : nullptr);
    }

    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        S03S06StagePackMasterFinder(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialMasterPath);
    S03S06StagePackMaterialMaster = S03S06StagePackMasterFinder.Succeeded()
        ? S03S06StagePackMasterFinder.Object : nullptr;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        StagePackCairnwellGreenFinder(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialPaths[
                LBOneFactoryPressPresentationPrivate::StagePackCairnwellGreen]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        StagePackFoundryCharcoalFinder(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialPaths[
                LBOneFactoryPressPresentationPrivate::StagePackFoundryCharcoal]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        StagePackServiceGreyFinder(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialPaths[
                LBOneFactoryPressPresentationPrivate::StagePackServiceGrey]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        StagePackSafetyYellowFinder(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialPaths[
                LBOneFactoryPressPresentationPrivate::StagePackSafetyYellow]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        StagePackWorkedSteelFinder(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialPaths[
                LBOneFactoryPressPresentationPrivate::StagePackWorkedSteel]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        StagePackInspectionGlassFinder(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialPaths[
                LBOneFactoryPressPresentationPrivate::StagePackInspectionGlass]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        StagePackTrainAAccentFinder(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialPaths[
                LBOneFactoryPressPresentationPrivate::StagePackTrainAAccent]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        StagePackStatusGreenFinder(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialPaths[
                LBOneFactoryPressPresentationPrivate::StagePackStatusGreen]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        StagePackStatusAmberFinder(
            LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialPaths[
                LBOneFactoryPressPresentationPrivate::StagePackStatusAmber]);
    const ConstructorHelpers::FObjectFinder<UMaterialInterface>* const
        S03S06StagePackMaterialFinders[] =
    {
        &StagePackCairnwellGreenFinder, &StagePackFoundryCharcoalFinder,
        &StagePackServiceGreyFinder, &StagePackSafetyYellowFinder,
        &StagePackWorkedSteelFinder, &StagePackInspectionGlassFinder,
        &StagePackTrainAAccentFinder, &StagePackStatusGreenFinder,
        &StagePackStatusAmberFinder
    };
    S03S06StagePackMaterialLibrary.Reset();
    S03S06StagePackMaterialLibrary.Reserve(UE_ARRAY_COUNT(
        LBOneFactoryPressPresentationPrivate::S03S06StagePackMaterialPaths));
    for (const ConstructorHelpers::FObjectFinder<UMaterialInterface>* Finder :
        S03S06StagePackMaterialFinders)
    {
        S03S06StagePackMaterialLibrary.Add(
            Finder->Succeeded() ? Finder->Object : nullptr);
    }

    // The MaterialFlow assets are native UE imports, not soft-loaded dressing.
    // Keep the entire exact mesh/MI closure on the CDO so an endpoint cannot
    // silently degrade back to generic primitives in a cooked build.
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S01CoilCartFinder(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths[0]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S01CoilRackFinder(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths[1]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S01DecoilerBaseFinder(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths[2]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S01DecoilerSpindleFinder(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths[3]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S01StraightenerFeedFinder(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths[4]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S01FeedBridgeFinder(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths[5]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S07ExitConveyorBeltFinder(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths[6]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S07ExitConveyorFrameFinder(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths[7]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S07InspectionCellFinder(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths[8]);
    static ConstructorHelpers::FObjectFinder<UStaticMesh> S07OutboundDunnageFinder(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths[9]);
    const ConstructorHelpers::FObjectFinder<UStaticMesh>* const
        MaterialFlowMeshFinders[] =
    {
        &S01CoilCartFinder, &S01CoilRackFinder, &S01DecoilerBaseFinder,
        &S01DecoilerSpindleFinder, &S01StraightenerFeedFinder,
        &S01FeedBridgeFinder, &S07ExitConveyorBeltFinder,
        &S07ExitConveyorFrameFinder, &S07InspectionCellFinder,
        &S07OutboundDunnageFinder
    };
    MaterialFlowMeshLibrary.Reset();
    MaterialFlowMeshLibrary.Reserve(UE_ARRAY_COUNT(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMeshPaths));
    for (const ConstructorHelpers::FObjectFinder<UStaticMesh>* Finder :
        MaterialFlowMeshFinders)
    {
        MaterialFlowMeshLibrary.Add(Finder->Succeeded() ? Finder->Object : nullptr);
    }

    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        MaterialFlowDarkRubberFinder(
            LBOneFactoryPressPresentationPrivate::MaterialFlowMaterialPaths[
                LBOneFactoryPressPresentationPrivate::MaterialFlowDarkRubber]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        MaterialFlowGalvanizedCoilFinder(
            LBOneFactoryPressPresentationPrivate::MaterialFlowMaterialPaths[
                LBOneFactoryPressPresentationPrivate::MaterialFlowGalvanizedCoil]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        MaterialFlowStampedPanelFinder(
            LBOneFactoryPressPresentationPrivate::MaterialFlowMaterialPaths[
                LBOneFactoryPressPresentationPrivate::MaterialFlowStampedPanel]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface>
        MaterialFlowTaskLightGlassFinder(
            LBOneFactoryPressPresentationPrivate::MaterialFlowMaterialPaths[
                LBOneFactoryPressPresentationPrivate::MaterialFlowTaskLightGlass]);
    const ConstructorHelpers::FObjectFinder<UMaterialInterface>* const
        MaterialFlowMaterialFinders[] =
    {
        &MaterialFlowDarkRubberFinder, &MaterialFlowGalvanizedCoilFinder,
        &MaterialFlowStampedPanelFinder, &MaterialFlowTaskLightGlassFinder
    };
    MaterialFlowMaterialLibrary.Reset();
    MaterialFlowMaterialLibrary.Reserve(UE_ARRAY_COUNT(
        LBOneFactoryPressPresentationPrivate::MaterialFlowMaterialPaths));
    for (const ConstructorHelpers::FObjectFinder<UMaterialInterface>* Finder :
        MaterialFlowMaterialFinders)
    {
        MaterialFlowMaterialLibrary.Add(
            Finder->Succeeded() ? Finder->Object : nullptr);
    }

    static ConstructorHelpers::FObjectFinder<UStaticMesh> MotionPrimitiveFinder(
        TEXT("/Engine/BasicShapes/Cube.Cube"));
    MotionPrimitiveMesh = MotionPrimitiveFinder.Succeeded()
        ? MotionPrimitiveFinder.Object : nullptr;

    Tags.AddUnique(GetPresentationTag());
    // Retained verbatim because the existing exact-pair validator consumes it.
    Tags.AddUnique(TEXT("LB.OneFactory.PressStarter.NativeProcedural"));
    Tags.AddUnique(TEXT("LB.Provenance.VerifiedPreMeshyNative"));
    Tags.AddUnique(TEXT("LB.Provenance.NativeAuthoredS02"));
    Tags.AddUnique(TEXT("LB.Provenance.NativeAuthoredS03S06StagePack"));
    Tags.AddUnique(TEXT("LB.Provenance.NativeAuthoredMaterialFlowV002"));
    Tags.AddUnique(TEXT("LB.Environment.VisualOnly"));
    Tags.AddUnique(TEXT("LB.NotProcessWIP"));
    SetActorHiddenInGame(true);
}

void ALBOneFactoryPressStarterPresentationActor::Tick(const float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    if (bPresentationConfigured)
    {
        EnsureS02DeepDrawRuntimeVisibility();
        EnsureS03S06StagePackRuntimeVisibility();
        EnsureMaterialFlowRuntimeVisibility();
    }
    if (!bPresentationConfigured || !bMechanismAnimationActive
        || MechanismRestTransforms.Num() != GetMotionComponents().Num())
    {
        return;
    }

    const float Time = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
    const TArray<UStaticMeshComponent*> Components = GetMotionComponents();
    // Values are bounded by the supplied Train A motion authority: M01 ram
    // travel is 300–800 mm, M04 lift is 600 mm and M05 pitch is 7,500 mm.
    // The phase offsets keep S02-S06 legible without pretending they strike
    // simultaneously as one monolithic machine.
    const float TransferPitchCm = (FMath::Sin(Time * 0.55f) + 1.0f) * 375.0f;
    const float TransferLiftCm = (FMath::Sin(Time * 0.78f) + 1.0f) * 30.0f;
    for (int32 Index = 0; Index < Components.Num(); ++Index)
    {
        UStaticMeshComponent* Component = Components[Index];
        if (!Component) continue;
        const FTransform& Rest = MechanismRestTransforms[Index];
        FVector Location = Rest.GetLocation();
        if (Index == 0)
        {
            Location += Rest.GetRotation().RotateVector(
                FVector(0.0f, TransferPitchCm, 0.0f));
        }
        else if (Index == 1 || Index == 2)
        {
            Location += Rest.GetRotation().RotateVector(
                FVector(0.0f, TransferPitchCm, TransferLiftCm));
        }
        else if (Index <= 7)
        {
            const float Phase = Time * 1.35f + float(Index - 3) * 0.86f;
            const float Closed = FMath::SmoothStep(0.35f, 0.85f,
                (FMath::Sin(Phase) + 1.0f) * 0.5f);
            Location.Z -= 30.0f + Closed * 50.0f;
        }
        else if (Index == 8)
        {
            // M07: S01 destack lift moves through its 1,200 mm envelope.
            Location.Z += (FMath::Sin(Time * 0.62f) + 1.0f) * 60.0f;
        }
        else
        {
            // M08: S07's six-axis unload motion reads as a controlled pick arc.
            Location.Y += FMath::Sin(Time * 0.48f) * 145.0f;
            if (Index == 10)
            {
                Location.Z -= 170.0f + FMath::Cos(Time * 0.48f) * 45.0f;
            }
            Component->SetWorldRotation(Rest.GetRotation() * FQuat(
                FVector::UpVector, FMath::DegreesToRadians(FMath::Sin(Time * 0.48f) * 24.0f)),
                false, nullptr, ETeleportType::TeleportPhysics);
        }
        Component->SetWorldLocation(Location, false, nullptr,
            ETeleportType::TeleportPhysics);
    }
}

void ALBOneFactoryPressStarterPresentationActor::EndPlay(
    const EEndPlayReason::Type EndPlayReason)
{
    // These are spawned as companions of this presentation rather than loose
    // map content.  Tear them down with the press so a rebuild never leaves a
    // second PR008→PR010 route or a ghost die cart running in the world.
    TArray<AActor*> AttachedActors;
    GetAttachedActors(AttachedActors, true, false);
    for (AActor* Attached : AttachedActors)
    {
        if (IsValid(Attached)
            && (Attached->ActorHasTag(TEXT("LB.OneFactory.PressTooling.Native"))
                || Attached->ActorHasTag(TEXT("LB.OneFactory.PressFeed.Native"))
                || Attached->ActorHasTag(TEXT("LB.OneFactory.PressFeedPresentation.Native"))))
        {
            Attached->Destroy();
        }
    }
    Super::EndPlay(EndPlayReason);
}

TArray<UStaticMeshComponent*>
ALBOneFactoryPressStarterPresentationActor::
    GetDetailedPresentationComponents() const
{
    return { DetailedPresentationA.Get(), DetailedPresentationB.Get() };
}

TArray<UStaticMeshComponent*>
ALBOneFactoryPressStarterPresentationActor::
    GetS02DeepDrawPresentationComponents() const
{
    // The Ram is deliberately absent: PressRam_02 is the pre-existing movable
    // Unreal seam that drives it. These five preserve their supplied source
    // pivots for the next motion-control pass.
    return { S02DeepDrawPresentation.Get(),
        S02DeepDrawBlankholderPresentation.Get(),
        S02DeepDrawBolsterPresentation.Get(),
        S02DeepDrawFlywheelPresentation.Get(),
        S02DeepDrawSafetyGatePresentation.Get() };
}

TArray<UStaticMeshComponent*>
ALBOneFactoryPressStarterPresentationActor::
    GetS03S06StagePackPresentationComponents() const
{
    TArray<UStaticMeshComponent*> Components;
    Components.Reserve(S03S06StagePackFrames.Num() + S03S06StagePackCues.Num());
    for (const TObjectPtr<UStaticMeshComponent>& Frame : S03S06StagePackFrames)
    {
        Components.Add(Frame.Get());
    }
    for (const TObjectPtr<UStaticMeshComponent>& Cue : S03S06StagePackCues)
    {
        Components.Add(Cue.Get());
    }
    return Components;
}

TArray<UStaticMeshComponent*>
ALBOneFactoryPressStarterPresentationActor::
    GetMaterialFlowPresentationComponents() const
{
    return { S01CoilCartMover.Get(), S01CoilRackPresentation.Get(),
        S01DecoilerBasePresentation.Get(), S01DecoilerSpindleMover.Get(),
        S01StraightenerFeedPresentation.Get(), S01FeedBridgePresentation.Get(),
        S07ExitConveyorBeltPresentation.Get(), S07ExitConveyorFramePresentation.Get(),
        S07InspectionCellPresentation.Get(), S07OutboundDunnagePresentation.Get() };
}

UStaticMeshComponent* ALBOneFactoryPressStarterPresentationActor::
    GetDetailedPresentationComponent(const int32 Index) const
{
    switch (Index)
    {
    case 0: return DetailedPresentationA.Get();
    case 1: return DetailedPresentationB.Get();
    default: return nullptr;
    }
}

void ALBOneFactoryPressStarterPresentationActor::
    ConfigureDetailedPresentationComponent(UStaticMeshComponent* Component)
{
    if (!Component) return;
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
    Component->SetReceivesDecals(false);
    Component->SetVisibility(false, true);
    Component->SetHiddenInGame(true, true);
}

void ALBOneFactoryPressStarterPresentationActor::
    ApplyS02DeepDrawMaterialBindings(UStaticMeshComponent* Component) const
{
    if (!Component || !Component->GetStaticMesh()) return;
    using namespace LBOneFactoryPressPresentationPrivate;
    const UStaticMesh* Mesh = Component->GetStaticMesh();
    const TArray<FStaticMaterial>& Slots =
        Mesh->GetStaticMaterials();
    for (int32 SlotIndex = 0; SlotIndex < Slots.Num(); ++SlotIndex)
    {
        const FName SlotName = Slots[SlotIndex].MaterialSlotName;
        int32 MaterialIndex = INDEX_NONE;
        if (Mesh == S02DeepDrawStaticMesh)
        {
            if (SlotName == TEXT("M_CA_MainGreen"))
                MaterialIndex = S02StaticMainGreen;
            else if (SlotName == TEXT("M_CA_Concrete"))
                MaterialIndex = S02StaticConcrete;
            else if (SlotName == TEXT("M_CA_DarkSteel"))
                MaterialIndex = S02StaticDarkSteel;
            else if (SlotName == TEXT("M_CA_CleanSteel"))
                MaterialIndex = S02StaticCleanSteel;
            else if (SlotName == TEXT("M_CA_CharcoalGrey"))
                MaterialIndex = S02StaticCharcoalGrey;
            else if (SlotName == TEXT("M_CA_SafetyYellow"))
                MaterialIndex = S02StaticSafetyYellow;
            else if (SlotName == TEXT("M_CA_ScreenDark"))
                MaterialIndex = S02StaticScreenDark;
            else if (SlotName == TEXT("M_CA_LampGreen"))
                MaterialIndex = S02StaticLampGreen;
            else if (SlotName == TEXT("M_CA_LampAmber"))
                MaterialIndex = S02StaticLampAmber;
            else if (SlotName == TEXT("M_CA_LampRed"))
                MaterialIndex = S02StaticLampRed;
        }
        else if (Mesh == S02DeepDrawRamMesh && SlotName == TEXT("M_CA_DarkSteel"))
            MaterialIndex = S02RamDarkSteel;
        else if (Mesh == S02DeepDrawBlankholderMesh
            && SlotName == TEXT("M_CA_CleanSteel"))
            MaterialIndex = S02BlankholderCleanSteel;
        else if (Mesh == S02DeepDrawBolsterMesh
            && SlotName == TEXT("M_CA_CleanSteel"))
            MaterialIndex = S02BolsterCleanSteel;
        else if (Mesh == S02DeepDrawFlywheelMesh
            && SlotName == TEXT("M_CA_DarkSteel"))
            MaterialIndex = S02FlywheelDarkSteel;
        else if (Mesh == S02DeepDrawSafetyGateMesh
            && SlotName == TEXT("M_CA_SafetyYellow"))
            MaterialIndex = S02SafetyGateSafetyYellow;

        if (S02DeepDrawMaterialLibrary.IsValidIndex(MaterialIndex))
        {
            if (UMaterialInterface* Material =
                    S02DeepDrawMaterialLibrary[MaterialIndex].Get())
            {
                Component->SetMaterial(SlotIndex, Material);
            }
        }
    }
}

void ALBOneFactoryPressStarterPresentationActor::
    ApplyS03S06StagePackMaterialBindings(UStaticMeshComponent* Component) const
{
    if (!Component || !Component->GetStaticMesh()) return;
    using namespace LBOneFactoryPressPresentationPrivate;
    Component->EmptyOverrideMaterials();
    const TArray<FStaticMaterial>& Slots =
        Component->GetStaticMesh()->GetStaticMaterials();
    for (int32 SlotIndex = 0; SlotIndex < Slots.Num(); ++SlotIndex)
    {
        const int32 MaterialIndex = GetS03S06StagePackMaterialIndex(
            Slots[SlotIndex].MaterialSlotName);
        if (S03S06StagePackMaterialLibrary.IsValidIndex(MaterialIndex)
            && S03S06StagePackMaterialLibrary[MaterialIndex])
        {
            Component->SetMaterial(SlotIndex,
                S03S06StagePackMaterialLibrary[MaterialIndex]);
        }
    }
}

bool ALBOneFactoryPressStarterPresentationActor::
    IsS03S06StagePackStationReady(const int32 StationIndex) const
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (!S03S06StagePackFrames.IsValidIndex(StationIndex)
        || !S03S06StagePackCues.IsValidIndex(StationIndex)
        || !S03S06StagePackFrameMeshes.IsValidIndex(StationIndex)
        || !S03S06StagePackCueMeshes.IsValidIndex(StationIndex)
        || !S03S06StagePackFrames[StationIndex]
        || !S03S06StagePackCues[StationIndex])
    {
        return false;
    }
    FString IgnoreReason;
    return ValidateS03S06StagePackMaterialAssets(
            S03S06StagePackMaterialMaster,
            S03S06StagePackMaterialLibrary, IgnoreReason)
        && ValidateS03S06StagePackMeshAsset(
            S03S06StagePackFrameMeshes[StationIndex],
            S03S06StagePackFrameContracts[StationIndex], IgnoreReason)
        && ValidateS03S06StagePackMeshAsset(
            S03S06StagePackCueMeshes[StationIndex],
            S03S06StagePackCueContracts[StationIndex], IgnoreReason);
}

bool ALBOneFactoryPressStarterPresentationActor::
    IsMaterialFlowStationReady(const bool bS01) const
{
    using namespace LBOneFactoryPressPresentationPrivate;
    FString IgnoreReason;
    if (!ValidateMaterialFlowMeshAssets(MaterialFlowMeshLibrary, IgnoreReason)
        || !ValidateMaterialFlowMaterialAssets(MaterialFlowMaterialLibrary,
            IgnoreReason))
    {
        return false;
    }
    const TArray<UStaticMeshComponent*> Components =
        GetMaterialFlowPresentationComponents();
    const int32 StartIndex = bS01 ? 0 : 6;
    const int32 EndIndex = bS01 ? 6 : UE_ARRAY_COUNT(MaterialFlowMeshPaths);
    if (Components.Num() != UE_ARRAY_COUNT(MaterialFlowMeshPaths))
    {
        return false;
    }
    for (int32 Index = StartIndex; Index < EndIndex; ++Index)
    {
        UStaticMeshComponent* Component = Components[Index];
        UStaticMesh* Mesh = MaterialFlowMeshLibrary[Index].Get();
        if (!Component || !Mesh || Component->GetStaticMesh() != Mesh)
        {
            return false;
        }
        const TArray<FStaticMaterial>& Slots = Mesh->GetStaticMaterials();
        for (int32 SlotIndex = 0; SlotIndex < Slots.Num(); ++SlotIndex)
        {
            if (Component->GetMaterial(SlotIndex) != Mesh->GetMaterial(SlotIndex))
            {
                return false;
            }
        }
    }
    return true;
}

void ALBOneFactoryPressStarterPresentationActor::
ConfigureMotionComponent(UStaticMeshComponent* Component)
{
    if (!Component) return;
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
    Component->SetReceivesDecals(false);
    Component->SetVisibility(false, true);
    Component->SetHiddenInGame(true, true);
}

void ALBOneFactoryPressStarterPresentationActor::
ConfigureNativeBatchComponent(UInstancedStaticMeshComponent* Component)
{
    if (!Component) return;
    Component->SetMobility(EComponentMobility::Movable);
    Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Component->SetCollisionResponseToAllChannels(ECR_Ignore);
    Component->SetGenerateOverlapEvents(false);
    Component->SetCanEverAffectNavigation(false);
    Component->SetCastShadow(true);
    Component->SetReceivesDecals(false);
    Component->SetVisibility(false, true);
    Component->SetHiddenInGame(true, true);
}

void ALBOneFactoryPressStarterPresentationActor::ConfigureNativeTrainModules()
{
    for (UStaticMeshComponent* Component : GetS03S06StagePackPresentationComponents())
    {
        if (!Component) continue;
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
        Component->SetStaticMesh(nullptr);
        Component->EmptyOverrideMaterials();
    }
    if (!MotionPrimitiveMesh) return;
    UMaterialInterface* Green = DetailedPresentationMesh
        ? DetailedPresentationMesh->GetMaterial(4) : nullptr;
    UMaterialInterface* Steel = DetailedPresentationMesh
        ? DetailedPresentationMesh->GetMaterial(8) : nullptr;
    UMaterialInterface* Yellow = DetailedPresentationMesh
        ? DetailedPresentationMesh->GetMaterial(6) : nullptr;
    // The staged aggregate is deliberately not rendered. Resolve the authored
    // materials directly as a robust fallback for the independent native cells.
    if (!Green) Green = Cast<UMaterialInterface>(StaticLoadObject(
        UMaterialInterface::StaticClass(), nullptr,
        LBOneFactoryPressPresentationPrivate::DetailedMaterialPaths[4]));
    if (!Steel) Steel = Cast<UMaterialInterface>(StaticLoadObject(
        UMaterialInterface::StaticClass(), nullptr,
        LBOneFactoryPressPresentationPrivate::DetailedMaterialPaths[8]));
    if (!Yellow) Yellow = Cast<UMaterialInterface>(StaticLoadObject(
        UMaterialInterface::StaticClass(), nullptr,
        LBOneFactoryPressPresentationPrivate::DetailedMaterialPaths[6]));
    // The game's chosen factory style is deliberately graphic rather than
    // textured. Use the engine's lightweight shape material with explicit
    // colours so every native module stays readable at management-camera range.
    if (UMaterialInterface* ShapeMaterial = Cast<UMaterialInterface>(
            StaticLoadObject(UMaterialInterface::StaticClass(), nullptr,
                TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"))))
    {
        UMaterialInstanceDynamic* GreenSolid =
            UMaterialInstanceDynamic::Create(ShapeMaterial, this);
        UMaterialInstanceDynamic* SteelSolid =
            UMaterialInstanceDynamic::Create(ShapeMaterial, this);
        UMaterialInstanceDynamic* YellowSolid =
            UMaterialInstanceDynamic::Create(ShapeMaterial, this);
        if (GreenSolid && SteelSolid && YellowSolid)
        {
            GreenSolid->SetVectorParameterValue(TEXT("Color"),
                FLinearColor(0.045f, 0.22f, 0.14f, 1.0f));
            SteelSolid->SetVectorParameterValue(TEXT("Color"),
                FLinearColor(0.18f, 0.23f, 0.26f, 1.0f));
            YellowSolid->SetVectorParameterValue(TEXT("Color"),
                FLinearColor(0.95f, 0.55f, 0.03f, 1.0f));
            Green = GreenSolid;
            Steel = SteelSolid;
            Yellow = YellowSolid;
        }
    }
    for (UInstancedStaticMeshComponent* Component : { StationBases.Get(),
            StationColumns.Get(), StationCrowns.Get(), StationTables.Get(),
            SafetyFrames.Get(), TransferRails.Get(), ServiceRuns.Get(),
            AccessPlatforms.Get(), ControlKiosks.Get(), SignalLights.Get() })
    {
        Component->ClearInstances();
        Component->SetStaticMesh(MotionPrimitiveMesh);
        Component->SetMaterial(0, Component == StationTables
                || Component == TransferRails || Component == ServiceRuns ? Steel
            : Component == SafetyFrames || Component == AccessPlatforms
                || Component == SignalLights ? Yellow
            : Green);
    }

    // The supplied Train A reference is a left-to-right S01-S07 line.  Anchor
    // it to the live train-station datum rather than to an editor-world
    // coordinate: that keeps it aligned after a save restore or map revision.
    FTransform TrainAnchor = FTransform::Identity;
    if (const FTransform* TrainStation = ConfiguredStationTransforms.Find(
            TEXT("OF_PRESS_TRAIN_001")))
    {
        TrainAnchor = FTransform(FQuat::Identity,
            LBOneFactoryPressPresentationPrivate::DetailedAggregateLocalLocationCm)
            * *TrainStation;
    }
    const FQuat TrainRotation = TrainAnchor.GetRotation();
    const auto AtTrain = [&TrainAnchor](const FVector& Local)
    {
        return TrainAnchor.TransformPosition(Local);
    };
    const bool bUseMaterialFlowS01 = IsMaterialFlowStationReady(true);
    const bool bUseMaterialFlowS07 = IsMaterialFlowStationReady(false);
    // The centre station is S04.  One pitch separates every reference cell.
    constexpr float Pitch = 1450.0f;
    const TCHAR* StationNames[] = { TEXT("S01  DESTACK / BLANK"),
        TEXT("S02  DEEP DRAW"), TEXT("S03  FORM / RESTRIKE"),
        TEXT("S04  TRIM / SCRAP"), TEXT("S05  PIERCE / SLUGS"),
        TEXT("S06  FLANGE / HEM"), TEXT("S07  INSPECT / UNLOAD") };
    const auto ClearStagePackPair = [](UStaticMeshComponent* Frame,
        UStaticMeshComponent* Cue)
    {
        for (UStaticMeshComponent* Component : { Frame, Cue })
        {
            if (!Component) continue;
            Component->SetVisibility(false, true);
            Component->SetHiddenInGame(true, true);
            Component->SetStaticMesh(nullptr);
            Component->EmptyOverrideMaterials();
        }
    };
    const auto ConfigureStagePackComponent = [this](
        UStaticMeshComponent* Component, UStaticMesh* Mesh,
        const FTransform& WorldTransform)
    {
        using namespace LBOneFactoryPressPresentationPrivate;
        if (!Component || !Mesh) return false;
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
        Component->SetStaticMesh(nullptr);
        Component->EmptyOverrideMaterials();
        Component->SetWorldTransform(WorldTransform, false, nullptr,
            ETeleportType::TeleportPhysics);
        const bool bMeshAssigned = Component->SetStaticMesh(Mesh);
        ApplyS03S06StagePackMaterialBindings(Component);
        bool bSemanticMaterialsBound = bMeshAssigned;
        const TArray<FStaticMaterial>& Slots = Mesh->GetStaticMaterials();
        for (int32 SlotIndex = 0; SlotIndex < Slots.Num(); ++SlotIndex)
        {
            const int32 MaterialIndex = GetS03S06StagePackMaterialIndex(
                Slots[SlotIndex].MaterialSlotName);
            bSemanticMaterialsBound &= S03S06StagePackMaterialLibrary
                    .IsValidIndex(MaterialIndex)
                && Component->GetMaterial(SlotIndex)
                    == S03S06StagePackMaterialLibrary[MaterialIndex];
        }
        return bMeshAssigned && Component->GetStaticMesh() == Mesh
            && Component->GetComponentTransform().Equals(WorldTransform,
                TransformTolerance)
            && bSemanticMaterialsBound;
    };
    for (int32 Index = 0; Index < 7; ++Index)
    {
        const float AlongTrain = Pitch * (Index - 3);
        bool bUseStagePackStation = false;
        const bool bUseMaterialFlowStation = (Index == 0 && bUseMaterialFlowS01)
            || (Index == 6 && bUseMaterialFlowS07);
        if (Index >= 2 && Index <= 5)
        {
            const int32 StagePackIndex = Index - 2;
            if (IsS03S06StagePackStationReady(StagePackIndex))
            {
                UStaticMeshComponent* Frame = S03S06StagePackFrames[StagePackIndex];
                UStaticMeshComponent* Cue = S03S06StagePackCues[StagePackIndex];
                const FTransform StagePackWorldTransform(TrainRotation,
                    AtTrain(FVector(0.0f, AlongTrain, 0.0f)),
                    FVector::OneVector);
                bUseStagePackStation = ConfigureStagePackComponent(Frame,
                    S03S06StagePackFrameMeshes[StagePackIndex],
                    StagePackWorldTransform)
                    && ConfigureStagePackComponent(Cue,
                        S03S06StagePackCueMeshes[StagePackIndex],
                        StagePackWorldTransform);
                if (!bUseStagePackStation)
                {
                    ClearStagePackPair(Frame, Cue);
                }
                else
                {
                    Frame->SetVisibility(true, true);
                    Frame->SetHiddenInGame(false, true);
                    Cue->SetVisibility(true, true);
                    Cue->SetHiddenInGame(false, true);
                }
            }
        }
        // S02 is supplied by the authored shell below. Do not add its generic
        // ISM pieces: ISMs cannot hide one instance without hiding all stations.
        // S03-S06 make the same all-or-nothing decision per station pair, so a
        // drifted StagePack entry keeps its generic fallback rather than leaving
        // a partial press visible.
        const bool bUseGenericStationShell = (Index != 1
            || !S02DeepDrawPresentation
            || S02DeepDrawPresentation->GetStaticMesh()
                != S02DeepDrawStaticMesh)
            && !bUseStagePackStation
            && !bUseMaterialFlowStation;
        // These are factory-scale presses, not individual workbenches.  The
        // first native pass used a 4.6 m cell which got lost in the management
        // camera's 80 m train bay.  Give each operation a clear 12 m-wide
        // press body and a substantial crown/bed silhouette.
        if (bUseGenericStationShell)
        {
            const FTransform Base(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain, 55.0f)),
                FVector(7.8f, 5.10f, 0.55f));
            StationBases->AddInstance(Base);
            StationTables->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain, 350.0f)),
                FVector(5.55f, 3.65f, 0.34f)));
            StationCrowns->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain, 1375.0f)),
                FVector(7.35f, 4.15f, 1.85f)));
            for (const float XOffset : { -220.0f, 220.0f })
                StationColumns->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(XOffset * 2.70f, AlongTrain, 790.0f)),
                    FVector(1.35f, 1.35f, 7.15f)));
            // Broad side housings make the presses read as industrial machines
            // from the overview, while keeping the open centre visible for motion.
            for (const float Side : { -1.0f, 1.0f })
                StationColumns->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(Side * 650.0f, AlongTrain, 920.0f)),
                    FVector(0.72f, 3.75f, 4.70f)));
            // Two light guard uprights per side leave the operator opening at the
            // front while reading as a protected station rather than a loose prop.
            for (const float YOffset : { -390.0f, 390.0f })
                SafetyFrames->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(-910.0f, AlongTrain + YOffset * 1.15f, 485.0f)),
                    FVector(0.13f, 0.13f, 3.15f)));
            // The authored S02 includes its own platform, HMI and stack light.
            AccessPlatforms->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(-900.0f, AlongTrain, 285.0f)),
                FVector(0.72f, 4.65f, 0.10f)));
            ControlKiosks->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(-1110.0f, AlongTrain - 560.0f, 205.0f)),
                FVector(0.34f, 0.24f, 1.50f)));
            SignalLights->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(-1110.0f, AlongTrain - 560.0f, 560.0f)),
                FVector(0.10f, 0.10f, 0.55f)));
        }
        // The overhead service run is continuous across the authored station.
        ServiceRuns->AddInstance(FTransform(TrainRotation,
            AtTrain(FVector(910.0f, AlongTrain, 1860.0f)),
            FVector(0.16f, 7.20f, 0.16f)));

        // Continuous transfer rails and their safety/maintenance structure are
        // what turn seven press cells into one recognisable press train.
        for (const float Side : { -1.0f, 1.0f })
        {
            TransferRails->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(Side * 470.0f, AlongTrain, 1900.0f)),
                FVector(0.20f, 7.35f, 0.20f)));
            if (bUseGenericStationShell)
            {
                SafetyFrames->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(Side * 980.0f, AlongTrain, 910.0f)),
                    FVector(0.10f, 4.85f, 0.10f)));
                for (const float End : { -510.0f, 510.0f })
                    SafetyFrames->AddInstance(FTransform(TrainRotation,
                        AtTrain(FVector(Side * 980.0f, AlongTrain + End, 750.0f)),
                        FVector(0.12f, 0.12f, 4.30f)));
            }
        }
        // Service-side hydraulic cabinet and an operator-side lower die door.
        if (bUseGenericStationShell)
        {
            ServiceRuns->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(970.0f, AlongTrain + 250.0f, 480.0f)),
                FVector(0.88f, 1.10f, 1.25f)));
            AccessPlatforms->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(-710.0f, AlongTrain, 585.0f)),
                FVector(0.18f, 2.55f, 1.20f)));
        }

        // Station-specific equipment silhouettes, derived from the supplied
        // Train A sheets. They share the native batches but make every cell
        // read as a different operation rather than seven copies of one press.
        if (Index == 0 && !bUseMaterialFlowS01) // S01 generic fallback only
        {
            StationTables->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain - 420.0f, 500.0f)),
                FVector(2.5f, 1.25f, 1.65f)));
            SafetyFrames->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain + 540.0f, 430.0f)),
                FVector(2.8f, 0.12f, 0.18f)));
            TransferRails->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain - 760.0f, 410.0f)),
                FVector(2.8f, 0.32f, 0.14f)));
        }
        else if (Index == 1 && bUseGenericStationShell) // S02 fallback only
        {
            // The deep-draw station is visually deeper than the common body:
            // a rear power pack and a broad lower cushion distinguish it from
            // the S03 restrike and S06 hem cells at management-camera range.
            StationTables->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain, 505.0f)),
                FVector(3.05f, 2.15f, 0.42f)));
            ServiceRuns->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(585.0f, AlongTrain - 330.0f, 470.0f)),
                FVector(0.72f, 1.15f, 0.95f)));
            SafetyFrames->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(-620.0f, AlongTrain - 690.0f, 510.0f)),
                FVector(0.12f, 0.12f, 3.25f)));
        }
        else if (Index == 2 && bUseGenericStationShell) // S03 fallback
        {
            StationTables->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain, 490.0f)),
                FVector(2.82f, 1.90f, 0.31f)));
            for (const float Side : { -1.0f, 1.0f })
                TransferRails->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(Side * 320.0f, AlongTrain + 200.0f, 610.0f)),
                    FVector(0.22f, 1.05f, 0.22f)));
            AccessPlatforms->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(-610.0f, AlongTrain + 490.0f, 540.0f)),
                FVector(0.52f, 0.15f, 2.70f)));
        }
        else if (Index == 3 && bUseGenericStationShell) // S04 fallback
        {
            StationTables->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain, 540.0f)),
                FVector(2.65f, 1.7f, 0.35f)));
            for (const float Side : { -1.0f, 1.0f })
                StationTables->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(Side * 470.0f, AlongTrain + 420.0f, 330.0f)),
                    FVector(0.55f, 1.25f, 0.35f)));
            ServiceRuns->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(540.0f, AlongTrain + 340.0f, 440.0f)),
                FVector(0.16f, 1.65f, 0.18f)));
        }
        else if (Index == 4 && bUseGenericStationShell) // S05 fallback
        {
            for (const float Offset : { -270.0f, -90.0f, 90.0f, 270.0f })
                StationColumns->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(Offset, AlongTrain, 780.0f)),
                    FVector(0.22f, 0.22f, 2.1f)));
            for (const float Side : { -1.0f, 1.0f })
                StationTables->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(Side * 460.0f, AlongTrain + 430.0f, 250.0f)),
                    FVector(0.62f, 0.82f, 0.48f)));
        }
        else if (Index == 5 && bUseGenericStationShell) // S06 fallback
        {
            StationTables->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain, 470.0f)),
                FVector(3.00f, 2.28f, 0.28f)));
            for (const float Side : { -1.0f, 1.0f })
            {
                StationColumns->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(Side * 390.0f, AlongTrain + 135.0f, 690.0f)),
                    FVector(0.30f, 0.36f, 2.85f)));
                SafetyFrames->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(Side * 610.0f, AlongTrain + 480.0f, 500.0f)),
                    FVector(0.16f, 1.48f, 0.14f)));
            }
        }
        else if (Index == 6 && !bUseMaterialFlowS07) // S07 generic fallback only
        {
            StationCrowns->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain, 1280.0f)),
                FVector(5.8f, 0.28f, 0.25f)));
            for (const float Side : { -1.0f, 1.0f })
                StationColumns->AddInstance(FTransform(TrainRotation,
                    AtTrain(FVector(Side * 520.0f, AlongTrain, 720.0f)),
                    FVector(0.26f, 0.26f, 4.5f)));
            TransferRails->AddInstance(FTransform(TrainRotation,
                AtTrain(FVector(0.0f, AlongTrain + 730.0f, 310.0f)),
                FVector(2.9f, 1.45f, 0.18f)));
        }
        if (StationLabels.IsValidIndex(Index) && StationLabels[Index])
        {
            UTextRenderComponent* Label = StationLabels[Index];
            Label->SetText(FText::FromString(StationNames[Index]));
            Label->SetWorldLocation(AtTrain(FVector(-600.0f, AlongTrain, 1020.0f)));
            Label->SetWorldRotation((TrainRotation
                * FQuat(FVector::UpVector, PI * 0.5f)).Rotator());
            Label->SetVisibility(true, true);
            Label->SetHiddenInGame(false, true);
        }
    }
    for (UInstancedStaticMeshComponent* Component : { StationBases.Get(),
            StationColumns.Get(), StationCrowns.Get(), StationTables.Get(),
            SafetyFrames.Get(), TransferRails.Get(), ServiceRuns.Get(),
            AccessPlatforms.Get(), ControlKiosks.Get(), SignalLights.Get() })
    {
        Component->SetVisibility(true, true);
        Component->SetHiddenInGame(false, true);
    }
}

void ALBOneFactoryPressStarterPresentationActor::ClearNativeTrainModules()
{
    for (UInstancedStaticMeshComponent* Component : { StationBases.Get(),
            StationColumns.Get(), StationCrowns.Get(), StationTables.Get(),
            SafetyFrames.Get(), TransferRails.Get(), ServiceRuns.Get(),
            AccessPlatforms.Get(), ControlKiosks.Get(), SignalLights.Get() })
    {
        if (!Component) continue;
        Component->ClearInstances();
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
    }
    for (UTextRenderComponent* Label : StationLabels)
        if (Label) { Label->SetVisibility(false, true); Label->SetHiddenInGame(true, true); }
    for (UStaticMeshComponent* Component : GetS03S06StagePackPresentationComponents())
    {
        if (!Component) continue;
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
        Component->SetStaticMesh(nullptr);
        Component->EmptyOverrideMaterials();
    }
}

TArray<UStaticMeshComponent*> ALBOneFactoryPressStarterPresentationActor::
    GetMotionComponents() const
{
    TArray<UStaticMeshComponent*> Components;
    Components.Reserve(6 + PressRams.Num());
    Components.Add(TransferCarriage.Get());
    Components.Add(TransferBeam.Get());
    Components.Add(TransferGripperFrame.Get());
    for (const TObjectPtr<UStaticMeshComponent>& Ram : PressRams)
        Components.Add(Ram.Get());
    Components.Add(DestackLift.Get());
    Components.Add(UnloadRobotArm.Get());
    Components.Add(UnloadRobotGripper.Get());
    return Components;
}

void ALBOneFactoryPressStarterPresentationActor::
    ConfigureMechanismAnimation(const FTransform& S02DeepDrawWorldTransform)
{
    const TArray<UStaticMeshComponent*> Components = GetMotionComponents();
    if (!MotionPrimitiveMesh || !S02DeepDrawRamMesh || Components.Num() != 11)
    {
        bMechanismAnimationActive = false;
        return;
    }

    // Local positions in the S01-S07 train frame. Motion is deliberately
    // independent from the retired opaque aggregate mesh.
    const FVector LocalPositions[] =
    {
        FVector(0.0f, -1450.0f, 1320.0f), // moving carriage
        FVector(0.0f, 0.0f, 1085.0f), // transfer beam / servo rail
        FVector(0.0f, -1450.0f, 1010.0f), // moving panel gripper frame
        FVector(0.0f, -2900.0f, 1180.0f),
        FVector(0.0f, -1450.0f, 1180.0f),
        FVector(0.0f, 0.0f, 1180.0f),
        FVector(0.0f, 1450.0f, 1180.0f),
        FVector(0.0f, 2900.0f, 1180.0f),
        FVector(0.0f, -4350.0f, 460.0f), // S01 vacuum destack lift
        FVector(570.0f, 4350.0f, 520.0f), // S07 unload robot pick arm
        FVector(570.0f, 4350.0f, 300.0f) // S07 panel unload gripper
    };
    const FVector Scales[] =
    {
        FVector(1.25f, 0.95f, 0.70f),
        FVector(0.22f, 25.0f, 0.18f),
        FVector(2.30f, 0.70f, 0.12f),
        FVector(1.45f, 1.10f, 1.30f),
        FVector(1.45f, 1.10f, 1.30f),
        FVector(1.45f, 1.10f, 1.30f),
        FVector(1.45f, 1.10f, 1.30f),
        FVector(1.45f, 1.10f, 1.30f),
        FVector(1.80f, 1.80f, 0.35f),
        FVector(1.00f, 0.42f, 3.20f),
        FVector(1.65f, 0.65f, 0.16f)
    };

    FTransform TrainAnchor = FTransform::Identity;
    if (const FTransform* TrainStation = ConfiguredStationTransforms.Find(
            TEXT("OF_PRESS_TRAIN_001")))
    {
        TrainAnchor = FTransform(FQuat::Identity,
            LBOneFactoryPressPresentationPrivate::DetailedAggregateLocalLocationCm)
            * *TrainStation;
    }
    const FQuat TrainRotation = TrainAnchor.GetRotation();
    MechanismRestTransforms.Reset();
    MechanismRestTransforms.Reserve(Components.Num());
    // Keep the animated seams in the same lightweight graphic-material family
    // as the static native train.  This prevents a detailed legacy material
    // slot from making the transfer or robot visually read as an imported prop.
    UMaterialInterface* StructureMaterial = DetailedPresentationMesh
        ? DetailedPresentationMesh->GetMaterial(4) : nullptr;
    UMaterialInterface* SteelMaterial = DetailedPresentationMesh
        ? DetailedPresentationMesh->GetMaterial(8) : nullptr;
    if (UMaterialInterface* ShapeMaterial = Cast<UMaterialInterface>(
            StaticLoadObject(UMaterialInterface::StaticClass(), nullptr,
                TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"))))
    {
        UMaterialInstanceDynamic* GreenSolid =
            UMaterialInstanceDynamic::Create(ShapeMaterial, this);
        UMaterialInstanceDynamic* SteelSolid =
            UMaterialInstanceDynamic::Create(ShapeMaterial, this);
        if (GreenSolid && SteelSolid)
        {
            GreenSolid->SetVectorParameterValue(TEXT("Color"),
                FLinearColor(0.045f, 0.22f, 0.14f, 1.0f));
            SteelSolid->SetVectorParameterValue(TEXT("Color"),
                FLinearColor(0.18f, 0.23f, 0.26f, 1.0f));
            StructureMaterial = GreenSolid;
            SteelMaterial = SteelSolid;
        }
    }
    for (int32 Index = 0; Index < Components.Num(); ++Index)
    {
        UStaticMeshComponent* Component = Components[Index];
        if (!Component) continue;
        if (Index == 3)
        {
            // The original `PressRam_02` remains the motion seam, but now drives
            // the authored RamMover + DieUpper module rather than a cube proxy.
            Component->SetStaticMesh(S02DeepDrawRamMesh);
            ApplyS02DeepDrawMaterialBindings(Component);
            Component->SetWorldTransform(S02DeepDrawWorldTransform, false, nullptr,
                ETeleportType::TeleportPhysics);
        }
        else
        {
            Component->SetStaticMesh(MotionPrimitiveMesh);
            Component->SetMaterial(0, Index < 2 ? SteelMaterial : StructureMaterial);
            Component->SetWorldTransform(FTransform(TrainRotation,
                TrainAnchor.TransformPosition(LocalPositions[Index]), Scales[Index]), false,
                nullptr, ETeleportType::TeleportPhysics);
        }
        Component->SetVisibility(true, true);
        Component->SetHiddenInGame(false, true);
        MechanismRestTransforms.Add(Component->GetComponentTransform());
    }
    bMechanismAnimationActive = MechanismRestTransforms.Num() == Components.Num();
}

void ALBOneFactoryPressStarterPresentationActor::ClearMechanismAnimation()
{
    for (UStaticMeshComponent* Component : GetMotionComponents())
    {
        if (!Component) continue;
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
        Component->SetStaticMesh(nullptr);
    }
    MechanismRestTransforms.Reset();
    bMechanismAnimationActive = false;
}

void ALBOneFactoryPressStarterPresentationActor::
    EnsureS02DeepDrawRuntimeVisibility()
{
    // These five modules are separate scene components rather than instances in
    // a shared native batch. Keep their current configured state coherent after
    // actor-level visibility changes and PIE reparenting; this does not control
    // the Ram, which is owned by the existing PressRam_02 motion seam.
    for (UStaticMeshComponent* Component : GetS02DeepDrawPresentationComponents())
    {
        if (!Component || !Component->GetStaticMesh()) continue;
        if (!Component->IsVisible())
        {
            Component->SetVisibility(true, true);
        }
        if (Component->bHiddenInGame)
        {
            Component->SetHiddenInGame(false, true);
        }
    }
}

void ALBOneFactoryPressStarterPresentationActor::
    EnsureS03S06StagePackRuntimeVisibility()
{
    // Only successfully bound static frame/cue pairs are made visible.  A
    // missing or drifted station instead remains clear so its generic fallback
    // can be the sole visible shell.
    for (UStaticMeshComponent* Component : GetS03S06StagePackPresentationComponents())
    {
        if (!Component || !Component->GetStaticMesh()) continue;
        if (!Component->IsVisible())
        {
            Component->SetVisibility(true, true);
        }
        if (Component->bHiddenInGame)
        {
            Component->SetHiddenInGame(false, true);
        }
    }
}

void ALBOneFactoryPressStarterPresentationActor::
    EnsureMaterialFlowRuntimeVisibility()
{
    // The endpoint modules preserve the material assignments stored on their
    // native meshes.  Do not repair a partial bind into visibility: only a
    // complete validated station is allowed to replace its generic fallback.
    const bool bS01Ready = IsMaterialFlowStationReady(true);
    const bool bS07Ready = IsMaterialFlowStationReady(false);
    const TArray<UStaticMeshComponent*> Components =
        GetMaterialFlowPresentationComponents();
    for (int32 Index = 0; Index < Components.Num(); ++Index)
    {
        UStaticMeshComponent* Component = Components[Index];
        const bool bStationReady = Index < 6 ? bS01Ready : bS07Ready;
        if (!Component || !Component->GetStaticMesh() || !bStationReady) continue;
        if (!Component->IsVisible())
        {
            Component->SetVisibility(true, true);
        }
        if (Component->bHiddenInGame)
        {
            Component->SetHiddenInGame(false, true);
        }
    }
}

bool ALBOneFactoryPressStarterPresentationActor::ValidateDetailedMeshAsset(
    const UStaticMesh* Mesh, FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (!Mesh || !Mesh->GetPathName().Equals(DetailedMeshPath,
            ESearchCase::CaseSensitive))
    {
        OutReason = TEXT(
            "PRESS DETAILED PRESENTATION MESH DID NOT RESOLVE TO ITS EXACT OWNED PATH");
        return false;
    }
    if (Mesh->GetStaticMaterials().Num() != ExpectedMaterialSlotCount)
    {
        OutReason = TEXT(
            "PRESS DETAILED PRESENTATION REQUIRES EXACTLY 306 MATERIAL SLOTS");
        return false;
    }

    TSet<FString> ExpectedMaterials;
    for (const TCHAR* MaterialPath : DetailedMaterialPaths)
        ExpectedMaterials.Add(MaterialPath);
    TSet<FString> ObservedMaterials;
    for (int32 SlotIndex = 0; SlotIndex < ExpectedMaterialSlotCount;
        ++SlotIndex)
    {
        const UMaterialInterface* Material = Mesh->GetMaterial(SlotIndex);
        const FString MaterialPath = Material ? Material->GetPathName() : FString();
        if (!Material || !ExpectedMaterials.Contains(MaterialPath))
        {
            OutReason = FString::Printf(TEXT(
                "PRESS DETAILED PRESENTATION MATERIAL SLOT %d IS NULL OR OUTSIDE THE EXACT 13-ASSET OWNED SET"),
                SlotIndex);
            return false;
        }
        ObservedMaterials.Add(MaterialPath);
    }
    if (ObservedMaterials.Num() != UE_ARRAY_COUNT(DetailedMaterialPaths))
    {
        OutReason = TEXT(
            "PRESS DETAILED PRESENTATION DOES NOT USE ALL 13 ACCEPTED PBR MATERIALS");
        return false;
    }
    OutReason = TEXT(
        "PRESS DETAILED PRESENTATION MESH HAS EXACTLY 306 OWNED PBR MATERIAL BINDINGS");
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::ValidateS02DeepDrawMeshAssets(
    const UStaticMesh* StaticMesh, const UStaticMesh* RamMesh,
    const UStaticMesh* BlankholderMesh, const UStaticMesh* BolsterMesh,
    const UStaticMesh* FlywheelMesh, const UStaticMesh* SafetyGateMesh,
    FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (!StaticMesh || !StaticMesh->GetPathName().Equals(
            S02DeepDrawStaticMeshPath, ESearchCase::CaseSensitive))
    {
        OutReason = TEXT(
            "S02 DEEP-DRAW STATIC SHELL DID NOT RESOLVE TO ITS EXACT NATIVE-AUTHORED PATH");
        return false;
    }
    const FVector StaticSize = StaticMesh->GetBounds().BoxExtent * 2.0f;
    if (!StaticSize.Equals(FVector(657.0f, 663.09f, 815.06f), 3.0f)
        || StaticMesh->GetStaticMaterials().Num() != 10)
    {
        OutReason = FString::Printf(TEXT(
            "S02 DEEP-DRAW STATIC IMPORT RECEIPT DRIFTED (BOUNDS %s, SLOTS %d)"),
            *StaticSize.ToString(), StaticMesh->GetStaticMaterials().Num());
        return false;
    }

    const FName ExpectedStaticSlots[] = {
        FName(TEXT("M_CA_MainGreen")), FName(TEXT("M_CA_Concrete")),
        FName(TEXT("M_CA_DarkSteel")), FName(TEXT("M_CA_CleanSteel")),
        FName(TEXT("M_CA_CharcoalGrey")), FName(TEXT("M_CA_SafetyYellow")),
        FName(TEXT("M_CA_ScreenDark")), FName(TEXT("M_CA_LampGreen")),
        FName(TEXT("M_CA_LampAmber")), FName(TEXT("M_CA_LampRed")) };
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(ExpectedStaticSlots); ++Index)
    {
        if (StaticMesh->GetStaticMaterials()[Index].MaterialSlotName
                != ExpectedStaticSlots[Index])
        {
            OutReason = FString::Printf(TEXT(
                "S02 DEEP-DRAW STATIC SHELL SLOT %d DRIFTED FROM IMPORT RECEIPT"),
                Index);
            return false;
        }
    }

    const auto ValidateMover = [&OutReason](const UStaticMesh* Mesh,
        const TCHAR* ExpectedPath, const FVector& ExpectedSize,
        const FName ExpectedSlot, const TCHAR* Label)
    {
        if (!Mesh || !Mesh->GetPathName().Equals(ExpectedPath,
                ESearchCase::CaseSensitive))
        {
            OutReason = FString::Printf(TEXT(
                "S02 DEEP-DRAW %s DID NOT RESOLVE TO ITS EXACT NATIVE-AUTHORED PATH"),
                Label);
            return false;
        }
        const FVector Size = Mesh->GetBounds().BoxExtent * 2.0f;
        if (!Size.Equals(ExpectedSize, 3.0f)
            || Mesh->GetStaticMaterials().Num() != 1
            || Mesh->GetStaticMaterials()[0].MaterialSlotName != ExpectedSlot)
        {
            OutReason = FString::Printf(TEXT(
                "S02 DEEP-DRAW %s IMPORT RECEIPT DRIFTED (BOUNDS %s, SLOTS %d)"),
                Label, *Size.ToString(), Mesh->GetStaticMaterials().Num());
            return false;
        }
        return true;
    };
    if (!ValidateMover(RamMesh, S02DeepDrawRamMeshPath,
            FVector(222.0f, 180.0f, 188.0f), FName(TEXT("M_CA_DarkSteel")),
            TEXT("RAM"))
        || !ValidateMover(BlankholderMesh, S02DeepDrawBlankholderMeshPath,
            FVector(190.0f, 155.0f, 12.0f), FName(TEXT("M_CA_CleanSteel")),
            TEXT("BLANKHOLDER"))
        || !ValidateMover(BolsterMesh, S02DeepDrawBolsterMeshPath,
            FVector(210.0f, 200.0f, 36.0f), FName(TEXT("M_CA_CleanSteel")),
            TEXT("BOLSTER"))
        || !ValidateMover(FlywheelMesh, S02DeepDrawFlywheelMeshPath,
            FVector(194.0f, 43.0f, 194.0f), FName(TEXT("M_CA_DarkSteel")),
            TEXT("FLYWHEEL"))
        || !ValidateMover(SafetyGateMesh, S02DeepDrawSafetyGateMeshPath,
            FVector(92.0f, 11.5f, 160.0f), FName(TEXT("M_CA_SafetyYellow")),
            TEXT("SAFETY GATE")))
    {
        return false;
    }

    OutReason = TEXT(
        "S02 DEEP-DRAW RUNTIMEPREP V003 SIX-MODULE ASSET SET MATCHES ITS IMPORT RECEIPT");
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::
    ValidateS02DeepDrawMaterialAssets(
        const UMaterialInterface* Master,
        const TArray<TObjectPtr<UMaterialInterface>>& Materials,
        FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (!Master || !Master->GetPathName().Equals(S02DeepDrawMaterialMasterPath,
            ESearchCase::CaseSensitive))
    {
        OutReason = TEXT(
            "S02 DEEP-DRAW V003 PBR MASTER DID NOT RESOLVE TO ITS EXACT OWNED PATH");
        return false;
    }
    if (Materials.Num() != UE_ARRAY_COUNT(S02DeepDrawMaterialPaths))
    {
        OutReason = TEXT(
            "S02 DEEP-DRAW V003 REQUIRES THE EXACT FIFTEEN-MATERIAL INSTANCE LIBRARY");
        return false;
    }
    for (int32 Index = 0; Index < Materials.Num(); ++Index)
    {
        const UMaterialInterface* Material = Materials[Index].Get();
        if (!Material || !Material->GetPathName().Equals(
                S02DeepDrawMaterialPaths[Index], ESearchCase::CaseSensitive))
        {
            OutReason = FString::Printf(TEXT(
                "S02 DEEP-DRAW V003 MATERIAL INSTANCE %d DID NOT RESOLVE TO ITS EXACT OWNED PATH"),
                Index);
            return false;
        }
    }
    OutReason = TEXT(
        "S02 DEEP-DRAW V003 PBR MASTER AND FIFTEEN PER-MODULE MATERIAL INSTANCES ARE COMPLETE");
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::
    ValidateS03S06StagePackMaterialAssets(
        const UMaterialInterface* Master,
        const TArray<TObjectPtr<UMaterialInterface>>& Materials,
        FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (!Master || !Master->GetPathName().Equals(
            S03S06StagePackMaterialMasterPath, ESearchCase::CaseSensitive))
    {
        OutReason = TEXT(
            "S03-S06 STAGEPACK PBR MASTER DID NOT RESOLVE TO ITS EXACT OWNED PATH");
        return false;
    }
    if (Materials.Num() != UE_ARRAY_COUNT(S03S06StagePackMaterialPaths))
    {
        OutReason = TEXT(
            "S03-S06 STAGEPACK REQUIRES THE EXACT NINE-FAMILY MATERIAL INSTANCE LIBRARY");
        return false;
    }
    for (int32 Index = 0; Index < Materials.Num(); ++Index)
    {
        const UMaterialInterface* Material = Materials[Index].Get();
        if (!Material || !Material->GetPathName().Equals(
                S03S06StagePackMaterialPaths[Index],
                ESearchCase::CaseSensitive))
        {
            OutReason = FString::Printf(TEXT(
                "S03-S06 STAGEPACK MATERIAL INSTANCE %d DID NOT RESOLVE TO ITS EXACT OWNED PATH"),
                Index);
            return false;
        }
    }
    OutReason = TEXT(
        "S03-S06 STAGEPACK PBR MASTER AND NINE SEMANTIC MATERIAL INSTANCES ARE COMPLETE");
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::
    ValidateMaterialFlowMeshAssets(
        const TArray<TObjectPtr<UStaticMesh>>& Meshes, FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (Meshes.Num() != UE_ARRAY_COUNT(MaterialFlowMeshContracts))
    {
        OutReason = TEXT("MATERIALFLOW V002 REQUIRES ITS EXACT TEN-MESH NATIVE CLOSURE");
        return false;
    }
    for (int32 Index = 0; Index < Meshes.Num(); ++Index)
    {
        if (!ValidateMaterialFlowMeshAsset(Meshes[Index],
                MaterialFlowMeshContracts[Index], OutReason))
        {
            return false;
        }
    }
    OutReason = TEXT(
        "MATERIALFLOW V002 TEN-MESH NATIVE CLOSURE MATCHES ITS FRESH-LOAD RECEIPT");
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::
    ValidateMaterialFlowMaterialAssets(
        const TArray<TObjectPtr<UMaterialInterface>>& Materials,
        FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (Materials.Num() != UE_ARRAY_COUNT(MaterialFlowMaterialPaths))
    {
        OutReason = TEXT("MATERIALFLOW V002 REQUIRES ITS EXACT FOUR NATIVE MATERIAL INSTANCES");
        return false;
    }
    for (int32 Index = 0; Index < Materials.Num(); ++Index)
    {
        const UMaterialInterface* Material = Materials[Index].Get();
        if (!Material || !Material->GetPathName().Equals(
                MaterialFlowMaterialPaths[Index], ESearchCase::CaseSensitive))
        {
            OutReason = FString::Printf(TEXT(
                "MATERIALFLOW V002 MATERIAL INSTANCE %d DID NOT RESOLVE TO ITS EXACT NATIVE PATH"),
                Index);
            return false;
        }
    }
    OutReason = TEXT(
        "MATERIALFLOW V002 FOUR NATIVE MATERIAL INSTANCES ARE COMPLETE");
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::
    BuildDetailedAggregateWorldTransform(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        FTransform& OutWorldTransform, FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    const FLBOneFactoryPressStarterStationState* PressStation = FindStation(
        Layout, ELBOneFactoryPressStarterRole::ConfigurablePressTrain);
    if (!PressStation || !IsFiniteTransform(PressStation->WorldTransform))
    {
        OutReason = TEXT(
            "PRESS DETAILED PRESENTATION HAS NO VALID CONFIGURABLE-PRESS-TRAIN ANCHOR");
        return false;
    }
    const FTransform LocalTransform(FQuat::Identity,
        DetailedAggregateLocalLocationCm, DetailedAggregateLocalScale);
    OutWorldTransform = LocalTransform * PressStation->WorldTransform;
    if (!IsFiniteTransform(OutWorldTransform))
    {
        OutReason = TEXT(
            "PRESS DETAILED PRESENTATION AGGREGATE WORLD TRANSFORM IS INVALID");
        return false;
    }
    OutReason = TEXT(
        "PRESS DETAILED PRESENTATION IS ANCHORED TO CONFIGURABLE PRESS TRAIN");
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::
    BuildS02DeepDrawWorldTransform(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        FTransform& OutWorldTransform, FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    const FLBOneFactoryPressStarterStationState* PressStation = FindStation(
        Layout, ELBOneFactoryPressStarterRole::ConfigurablePressTrain);
    if (!PressStation || !IsFiniteTransform(PressStation->WorldTransform))
    {
        OutReason = TEXT(
            "S02 DEEP-DRAW HAS NO VALID CONFIGURABLE-PRESS-TRAIN ANCHOR");
        return false;
    }

    const FTransform TrainAnchor(FQuat::Identity,
        DetailedAggregateLocalLocationCm, FVector::OneVector);
    // RuntimePrep v003 preserves the verified UE Convert Scene convention, so the
    // imported local mesh already has source -Y mapped to UE +Y. The existing
    // train runs in +Y and its operator aisle is -X: +90 yaw maps the source
    // flow +X to +Y and the converted operator side +Y to -X.
    const FTransform SourceLocal(FRotator(0.0f, 90.0f, 0.0f),
        S02DeepDrawLocalLocationCm, S02DeepDrawIntegrationScale);
    OutWorldTransform = SourceLocal * TrainAnchor * PressStation->WorldTransform;
    if (!IsFiniteTransform(OutWorldTransform))
    {
        OutReason = TEXT("S02 DEEP-DRAW WORLD TRANSFORM IS INVALID");
        return false;
    }
    OutReason = TEXT(
        "S02 DEEP-DRAW IS ANCHORED TO S02 WITH THE VERIFIED AUTHORED ORIENTATION");
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::
    BuildS02DeepDrawModuleWorldTransform(
        const FTransform& CellWorldTransform, const FVector& ModulePlacementCm,
        FTransform& OutWorldTransform, FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (!IsFiniteTransform(CellWorldTransform)
        || !FMath::IsFinite(ModulePlacementCm.X)
        || !FMath::IsFinite(ModulePlacementCm.Y)
        || !FMath::IsFinite(ModulePlacementCm.Z))
    {
        OutReason = TEXT("S02 DEEP-DRAW MODULE ROOT OR IMPORT PLACEMENT IS INVALID");
        return false;
    }
    // Placement values are Unreal centimetres from the RuntimePrep receipt,
    // already including Blender-to-Unreal Y conversion. Preserve the module's
    // local pivot and inherit only the cell root's rotation/scale.
    OutWorldTransform = FTransform(CellWorldTransform.GetRotation(),
        CellWorldTransform.TransformPosition(ModulePlacementCm),
        CellWorldTransform.GetScale3D());
    if (!IsFiniteTransform(OutWorldTransform))
    {
        OutReason = TEXT("S02 DEEP-DRAW MODULE WORLD TRANSFORM IS INVALID");
        return false;
    }
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::
    BuildMaterialFlowStationWorldTransforms(
        const FLBOneFactoryPressStarterLayoutState& Layout,
        FTransform& OutS01WorldTransform, FTransform& OutS07WorldTransform,
        FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    const FLBOneFactoryPressStarterStationState* PressStation = FindStation(
        Layout, ELBOneFactoryPressStarterRole::ConfigurablePressTrain);
    if (!PressStation || !IsFiniteTransform(PressStation->WorldTransform))
    {
        OutReason = TEXT("MATERIALFLOW V002 HAS NO VALID CONFIGURABLE-PRESS-TRAIN ANCHOR");
        return false;
    }
    const FTransform TrainAnchor(FQuat::Identity,
        DetailedAggregateLocalLocationCm, FVector::OneVector);
    // The verified native v002 meshes are origin-authored, unit-scale and
    // yaw-free.  Keep their endpoints at the existing S01/S07 train slots;
    // their in-cell placements remain in the mesh vertices while only the two
    // documented mover offsets are applied separately below.
    OutS01WorldTransform = FTransform(FQuat::Identity,
        FVector(0.0f, -4350.0f, 0.0f), FVector::OneVector)
        * TrainAnchor * PressStation->WorldTransform;
    OutS07WorldTransform = FTransform(FQuat::Identity,
        FVector(0.0f, 4350.0f, 0.0f), FVector::OneVector)
        * TrainAnchor * PressStation->WorldTransform;
    if (!IsFiniteTransform(OutS01WorldTransform)
        || !IsFiniteTransform(OutS07WorldTransform))
    {
        OutReason = TEXT("MATERIALFLOW V002 STATION ROOT TRANSFORM IS INVALID");
        return false;
    }
    OutReason = TEXT(
        "MATERIALFLOW V002 IS ANCHORED TO THE EXISTING YAW-FREE S01 AND S07 TRAIN SLOTS");
    return true;
}

bool ALBOneFactoryPressStarterPresentationActor::
    BuildMaterialFlowMoverWorldTransform(
        const FTransform& StationWorldTransform, const FVector& ParkedOffsetCm,
        FTransform& OutWorldTransform, FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (!IsFiniteTransform(StationWorldTransform)
        || !FMath::IsFinite(ParkedOffsetCm.X)
        || !FMath::IsFinite(ParkedOffsetCm.Y)
        || !FMath::IsFinite(ParkedOffsetCm.Z))
    {
        OutReason = TEXT("MATERIALFLOW V002 MOVER ROOT OR PARKED OFFSET IS INVALID");
        return false;
    }
    OutWorldTransform = FTransform(StationWorldTransform.GetRotation(),
        StationWorldTransform.TransformPosition(ParkedOffsetCm),
        StationWorldTransform.GetScale3D());
    if (!IsFiniteTransform(OutWorldTransform))
    {
        OutReason = TEXT("MATERIALFLOW V002 MOVER WORLD TRANSFORM IS INVALID");
        return false;
    }
    return true;
}

void ALBOneFactoryPressStarterPresentationActor::ClearPresentation()
{
    for (UStaticMeshComponent* Component : GetDetailedPresentationComponents())
    {
        if (!Component) continue;
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
        Component->SetStaticMesh(nullptr);
    }
    for (UStaticMeshComponent* Component : GetS02DeepDrawPresentationComponents())
    {
        if (!Component) continue;
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
        Component->SetStaticMesh(nullptr);
    }
    for (UStaticMeshComponent* Component : GetMaterialFlowPresentationComponents())
    {
        if (!Component) continue;
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
        Component->EmptyOverrideMaterials();
        Component->SetStaticMesh(nullptr);
    }
    ClearNativeTrainModules();
    ClearMechanismAnimation();
    ConfiguredItems.Reset();
    ConfiguredStationTransforms.Reset();
    ConfiguredLayoutId = NAME_None;
    ConfiguredLayoutRevision = INDEX_NONE;
    bPresentationConfigured = false;
    ActiveDetailedPresentationIndex = INDEX_NONE;
    SetActorHiddenInGame(true);
}

bool ALBOneFactoryPressStarterPresentationActor::ConfigureFromLayout(
    const FLBOneFactoryPressStarterLayoutState& Layout, FString& OutReason)
{
    if (!ValidateNativePresentationReferences(GetPresentationClassPath(),
            GetRequiredNativeAssetPaths(), OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION PROVENANCE FAILED: %s"),
            *OutReason);
        return false;
    }
    TArray<FLBOneFactoryPressPresentationItem> CandidateItems =
        BuildExpectedPresentationItems(Layout);
    if (!ValidatePresentationContract(Layout, CandidateItems, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION CONTRACT FAILED: %s"),
            *OutReason);
        return false;
    }

    UStaticMesh* ResolvedDetailedMesh = DetailedPresentationMesh.Get();
    if (!ValidateDetailedMeshAsset(ResolvedDetailedMesh, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION ASSET FAILED: %s"),
            *OutReason);
        return false;
    }

    UStaticMesh* ResolvedS02StaticMesh = S02DeepDrawStaticMesh.Get();
    UStaticMesh* ResolvedS02RamMesh = S02DeepDrawRamMesh.Get();
    UStaticMesh* ResolvedS02BlankholderMesh = S02DeepDrawBlankholderMesh.Get();
    UStaticMesh* ResolvedS02BolsterMesh = S02DeepDrawBolsterMesh.Get();
    UStaticMesh* ResolvedS02FlywheelMesh = S02DeepDrawFlywheelMesh.Get();
    UStaticMesh* ResolvedS02SafetyGateMesh = S02DeepDrawSafetyGateMesh.Get();
    if (!ValidateS02DeepDrawMeshAssets(ResolvedS02StaticMesh,
            ResolvedS02RamMesh, ResolvedS02BlankholderMesh,
            ResolvedS02BolsterMesh, ResolvedS02FlywheelMesh,
            ResolvedS02SafetyGateMesh, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION S02 ASSET FAILED: %s"),
            *OutReason);
        return false;
    }
    if (!ValidateS02DeepDrawMaterialAssets(S02DeepDrawMaterialMaster,
            S02DeepDrawMaterialLibrary, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION S02 MATERIAL FAILED: %s"),
            *OutReason);
        return false;
    }
    if (!ValidateMaterialFlowMeshAssets(MaterialFlowMeshLibrary, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION MATERIALFLOW ASSET FAILED: %s"),
            *OutReason);
        return false;
    }
    if (!ValidateMaterialFlowMaterialAssets(MaterialFlowMaterialLibrary, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION MATERIALFLOW MATERIAL FAILED: %s"),
            *OutReason);
        return false;
    }

    FTransform CandidateAggregateWorldTransform;
    if (!BuildDetailedAggregateWorldTransform(Layout,
            CandidateAggregateWorldTransform, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION ANCHOR FAILED: %s"),
            *OutReason);
        return false;
    }

    FTransform CandidateS02DeepDrawWorldTransform;
    if (!BuildS02DeepDrawWorldTransform(Layout,
            CandidateS02DeepDrawWorldTransform, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION S02 ANCHOR FAILED: %s"),
            *OutReason);
        return false;
    }

    FTransform CandidateMaterialFlowS01WorldTransform;
    FTransform CandidateMaterialFlowS07WorldTransform;
    FTransform CandidateMaterialFlowCoilCartWorldTransform;
    FTransform CandidateMaterialFlowDecoilerSpindleWorldTransform;
    if (!BuildMaterialFlowStationWorldTransforms(Layout,
            CandidateMaterialFlowS01WorldTransform,
            CandidateMaterialFlowS07WorldTransform, OutReason)
        || !BuildMaterialFlowMoverWorldTransform(
            CandidateMaterialFlowS01WorldTransform,
            FVector(220.0f, 430.0f, 32.0f),
            CandidateMaterialFlowCoilCartWorldTransform, OutReason)
        || !BuildMaterialFlowMoverWorldTransform(
            CandidateMaterialFlowS01WorldTransform,
            FVector(-20.0f, 120.0f, 115.0f),
            CandidateMaterialFlowDecoilerSpindleWorldTransform, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION MATERIALFLOW ANCHOR FAILED: %s"),
            *OutReason);
        return false;
    }

    FTransform CandidateS02RamWorldTransform;
    FTransform CandidateS02BlankholderWorldTransform;
    FTransform CandidateS02BolsterWorldTransform;
    FTransform CandidateS02FlywheelWorldTransform;
    FTransform CandidateS02SafetyGateWorldTransform;
    if (!BuildS02DeepDrawModuleWorldTransform(
            CandidateS02DeepDrawWorldTransform, FVector(0.0f, 0.0f, 377.5f),
            CandidateS02RamWorldTransform, OutReason)
        || !BuildS02DeepDrawModuleWorldTransform(
            CandidateS02DeepDrawWorldTransform, FVector(0.0f, 0.0f, 208.0f),
            CandidateS02BlankholderWorldTransform, OutReason)
        || !BuildS02DeepDrawModuleWorldTransform(
            CandidateS02DeepDrawWorldTransform, FVector(0.0f, 0.0f, 158.0f),
            CandidateS02BolsterWorldTransform, OutReason)
        || !BuildS02DeepDrawModuleWorldTransform(
            CandidateS02DeepDrawWorldTransform,
            FVector(-135.0f, -95.0f, 698.0f),
            CandidateS02FlywheelWorldTransform, OutReason)
        || !BuildS02DeepDrawModuleWorldTransform(
            CandidateS02DeepDrawWorldTransform,
            FVector(105.0f, 245.0f, 110.0f),
            CandidateS02SafetyGateWorldTransform, OutReason))
    {
        OutReason = FString::Printf(TEXT("PRESS PRESENTATION S02 MODULE ANCHOR FAILED: %s"),
            *OutReason);
        return false;
    }

    TMap<FName, FTransform> CandidateStationTransforms;
    CandidateStationTransforms.Reserve(Layout.Stations.Num());
    for (const FLBOneFactoryPressStarterStationState& Station : Layout.Stations)
        CandidateStationTransforms.Add(Station.StationId, Station.WorldTransform);

    const TArray<UStaticMeshComponent*> Components =
        GetDetailedPresentationComponents();
    if (Components.Num() != 2 || Components.Contains(nullptr))
    {
        OutReason = TEXT(
            "PRESS PRESENTATION REQUIRES EXACTLY TWO PRIVATE STAGING COMPONENTS");
        return false;
    }
    const TArray<UStaticMeshComponent*> S02Components =
        GetS02DeepDrawPresentationComponents();
    if (S02Components.Num() != 5 || S02Components.Contains(nullptr))
    {
        OutReason = TEXT(
            "PRESS PRESENTATION REQUIRES EXACTLY FIVE DEDICATED S02 DEEP-DRAW PRESENTATION COMPONENTS");
        return false;
    }
    const TArray<UStaticMeshComponent*> MaterialFlowComponents =
        GetMaterialFlowPresentationComponents();
    if (MaterialFlowComponents.Num() != 10
        || MaterialFlowComponents.Contains(nullptr)
        || MaterialFlowMeshLibrary.Num() != MaterialFlowComponents.Num())
    {
        OutReason = TEXT(
            "PRESS PRESENTATION REQUIRES EXACTLY TEN DEDICATED MATERIALFLOW V002 COMPONENTS");
        return false;
    }

    const int32 StagingIndex = ActiveDetailedPresentationIndex == 0 ? 1 : 0;
    UStaticMeshComponent* Staging = GetDetailedPresentationComponent(StagingIndex);
    if (!Staging
        || (bPresentationConfigured
            && StagingIndex == ActiveDetailedPresentationIndex))
    {
        OutReason = TEXT(
            "PRESS PRESENTATION COULD NOT ACQUIRE AN INACTIVE STAGING COMPONENT");
        return false;
    }

    // Keep the historic owned aggregate dependency staged but hidden. It remains
    // validated for packaged provenance; the visible train is authored as
    // separate native station modules below.
    Staging->SetVisibility(false, true);
    Staging->SetHiddenInGame(true, true);
    Staging->SetStaticMesh(nullptr);
    Staging->SetWorldTransform(CandidateAggregateWorldTransform, false, nullptr,
        ETeleportType::TeleportPhysics);
    const bool bMeshAssigned = Staging->SetStaticMesh(ResolvedDetailedMesh);
    if (!bMeshAssigned || Staging->GetStaticMesh() != ResolvedDetailedMesh
        || !Staging->GetComponentTransform().Equals(
            CandidateAggregateWorldTransform,
            LBOneFactoryPressPresentationPrivate::TransformTolerance))
    {
        Staging->SetStaticMesh(nullptr);
        OutReason = TEXT(
            "PRESS PRESENTATION STAGING COMPONENT FAILED EXACT MESH/TRANSFORM VALIDATION");
        return false;
    }

    // The supplied textured RuntimePrep v003 splits S02 into a static shell and five
    // pivoted modules. The Ram goes through PressRam_02 below; assign the five
    // non-Ram components as one rollback bundle so a rebind cannot leave an
    // incomplete visible cell.
    struct FS02Assignment
    {
        UStaticMeshComponent* Component;
        UStaticMesh* Mesh;
        FTransform WorldTransform;
    };
    const FS02Assignment S02Assignments[] =
    {
        { S02DeepDrawPresentation.Get(), ResolvedS02StaticMesh,
            CandidateS02DeepDrawWorldTransform },
        { S02DeepDrawBlankholderPresentation.Get(), ResolvedS02BlankholderMesh,
            CandidateS02BlankholderWorldTransform },
        { S02DeepDrawBolsterPresentation.Get(), ResolvedS02BolsterMesh,
            CandidateS02BolsterWorldTransform },
        { S02DeepDrawFlywheelPresentation.Get(), ResolvedS02FlywheelMesh,
            CandidateS02FlywheelWorldTransform },
        { S02DeepDrawSafetyGatePresentation.Get(), ResolvedS02SafetyGateMesh,
            CandidateS02SafetyGateWorldTransform }
    };
    struct FS02PreviousState
    {
        UStaticMeshComponent* Component;
        UStaticMesh* Mesh;
        FTransform WorldTransform;
        bool bVisible;
        bool bHiddenInGame;
        TArray<TObjectPtr<UMaterialInterface>> Materials;
    };
    TArray<FS02PreviousState> PreviousS02States;
    PreviousS02States.Reserve(UE_ARRAY_COUNT(S02Assignments));
    for (const FS02Assignment& Assignment : S02Assignments)
    {
        FS02PreviousState PreviousState = { Assignment.Component,
            Assignment.Component->GetStaticMesh(),
            Assignment.Component->GetComponentTransform(),
            Assignment.Component->IsVisible(),
            Assignment.Component->bHiddenInGame != 0 };
        const int32 MaterialCount = Assignment.Component->GetNumMaterials();
        PreviousState.Materials.Reserve(MaterialCount);
        for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
        {
            PreviousState.Materials.Add(Assignment.Component->GetMaterial(MaterialIndex));
        }
        PreviousS02States.Add(MoveTemp(PreviousState));
    }

    bool bS02Committed = true;
    for (const FS02Assignment& Assignment : S02Assignments)
    {
        Assignment.Component->SetVisibility(false, true);
        Assignment.Component->SetHiddenInGame(true, true);
        Assignment.Component->SetStaticMesh(nullptr);
        Assignment.Component->SetWorldTransform(Assignment.WorldTransform, false,
            nullptr, ETeleportType::TeleportPhysics);
        const bool bS02MeshAssigned = Assignment.Component->SetStaticMesh(
            Assignment.Mesh);
        ApplyS02DeepDrawMaterialBindings(Assignment.Component);
        bS02Committed = bS02MeshAssigned
            && Assignment.Component->GetStaticMesh() == Assignment.Mesh
            && Assignment.Component->GetComponentTransform().Equals(
                Assignment.WorldTransform,
                LBOneFactoryPressPresentationPrivate::TransformTolerance)
            && Assignment.Component->GetMaterial(0) != nullptr;
        if (!bS02Committed) break;
    }
    const auto RestoreS02States = [&PreviousS02States]()
    {
        for (const FS02PreviousState& Previous : PreviousS02States)
        {
            Previous.Component->SetStaticMesh(Previous.Mesh);
            Previous.Component->EmptyOverrideMaterials();
            for (int32 MaterialIndex = 0;
                MaterialIndex < Previous.Materials.Num(); ++MaterialIndex)
            {
                Previous.Component->SetMaterial(MaterialIndex,
                    Previous.Materials[MaterialIndex]);
            }
            Previous.Component->SetWorldTransform(Previous.WorldTransform, false,
                nullptr, ETeleportType::TeleportPhysics);
            Previous.Component->SetVisibility(Previous.bVisible, true);
            Previous.Component->SetHiddenInGame(Previous.bHiddenInGame, true);
        }
    };
    if (!bS02Committed)
    {
        RestoreS02States();
        Staging->SetStaticMesh(nullptr);
        OutReason = TEXT(
            "PRESS PRESENTATION S02 MODULE BUNDLE FAILED EXACT MESH/TRANSFORM/MATERIAL VALIDATION");
        return false;
    }
    for (const FS02Assignment& Assignment : S02Assignments)
    {
        Assignment.Component->SetVisibility(true, true);
        Assignment.Component->SetHiddenInGame(false, true);
    }

    // The MaterialFlow source has no node transforms: its static in-cell
    // layouts are baked into the mesh vertices.  Only the two documented
    // mover pivots receive their parked metadata offsets here.  We retain the
    // imported static material assignments; no component-level material
    // rebinding is allowed to hide a native asset drift.
    struct FMaterialFlowAssignment
    {
        UStaticMeshComponent* Component;
        UStaticMesh* Mesh;
        FTransform WorldTransform;
    };
    const FTransform MaterialFlowTransforms[] =
    {
        CandidateMaterialFlowCoilCartWorldTransform,
        CandidateMaterialFlowS01WorldTransform,
        CandidateMaterialFlowS01WorldTransform,
        CandidateMaterialFlowDecoilerSpindleWorldTransform,
        CandidateMaterialFlowS01WorldTransform,
        CandidateMaterialFlowS01WorldTransform,
        CandidateMaterialFlowS07WorldTransform,
        CandidateMaterialFlowS07WorldTransform,
        CandidateMaterialFlowS07WorldTransform,
        CandidateMaterialFlowS07WorldTransform
    };
    TArray<FMaterialFlowAssignment> MaterialFlowAssignments;
    MaterialFlowAssignments.Reserve(MaterialFlowComponents.Num());
    for (int32 Index = 0; Index < MaterialFlowComponents.Num(); ++Index)
    {
        MaterialFlowAssignments.Add({ MaterialFlowComponents[Index],
            MaterialFlowMeshLibrary[Index].Get(), MaterialFlowTransforms[Index] });
    }
    struct FMaterialFlowPreviousState
    {
        UStaticMeshComponent* Component;
        UStaticMesh* Mesh;
        FTransform WorldTransform;
        bool bVisible;
        bool bHiddenInGame;
        TArray<TObjectPtr<UMaterialInterface>> Materials;
    };
    TArray<FMaterialFlowPreviousState> PreviousMaterialFlowStates;
    PreviousMaterialFlowStates.Reserve(MaterialFlowAssignments.Num());
    for (const FMaterialFlowAssignment& Assignment : MaterialFlowAssignments)
    {
        FMaterialFlowPreviousState PreviousState = { Assignment.Component,
            Assignment.Component->GetStaticMesh(),
            Assignment.Component->GetComponentTransform(),
            Assignment.Component->IsVisible(),
            Assignment.Component->bHiddenInGame != 0 };
        const int32 MaterialCount = Assignment.Component->GetNumMaterials();
        PreviousState.Materials.Reserve(MaterialCount);
        for (int32 MaterialIndex = 0; MaterialIndex < MaterialCount; ++MaterialIndex)
        {
            PreviousState.Materials.Add(Assignment.Component->GetMaterial(MaterialIndex));
        }
        PreviousMaterialFlowStates.Add(MoveTemp(PreviousState));
    }
    const auto RestoreMaterialFlowStates = [&PreviousMaterialFlowStates]()
    {
        for (const FMaterialFlowPreviousState& Previous : PreviousMaterialFlowStates)
        {
            Previous.Component->SetStaticMesh(Previous.Mesh);
            Previous.Component->EmptyOverrideMaterials();
            for (int32 MaterialIndex = 0;
                MaterialIndex < Previous.Materials.Num(); ++MaterialIndex)
            {
                Previous.Component->SetMaterial(MaterialIndex,
                    Previous.Materials[MaterialIndex]);
            }
            Previous.Component->SetWorldTransform(Previous.WorldTransform, false,
                nullptr, ETeleportType::TeleportPhysics);
            Previous.Component->SetVisibility(Previous.bVisible, true);
            Previous.Component->SetHiddenInGame(Previous.bHiddenInGame, true);
        }
    };
    bool bMaterialFlowCommitted = true;
    for (const FMaterialFlowAssignment& Assignment : MaterialFlowAssignments)
    {
        Assignment.Component->SetVisibility(false, true);
        Assignment.Component->SetHiddenInGame(true, true);
        Assignment.Component->SetStaticMesh(nullptr);
        Assignment.Component->EmptyOverrideMaterials();
        Assignment.Component->SetWorldTransform(Assignment.WorldTransform, false,
            nullptr, ETeleportType::TeleportPhysics);
        const bool bMaterialFlowMeshAssigned = Assignment.Component->SetStaticMesh(
            Assignment.Mesh);
        bool bNativeMaterialsRetained = bMaterialFlowMeshAssigned;
        if (Assignment.Mesh)
        {
            const TArray<FStaticMaterial>& Slots = Assignment.Mesh->GetStaticMaterials();
            for (int32 SlotIndex = 0; SlotIndex < Slots.Num(); ++SlotIndex)
            {
                bNativeMaterialsRetained &= Assignment.Component->GetMaterial(SlotIndex)
                    == Assignment.Mesh->GetMaterial(SlotIndex);
            }
        }
        bMaterialFlowCommitted = bMaterialFlowMeshAssigned
            && Assignment.Component->GetStaticMesh() == Assignment.Mesh
            && Assignment.Component->GetComponentTransform().Equals(
                Assignment.WorldTransform,
                LBOneFactoryPressPresentationPrivate::TransformTolerance)
            && bNativeMaterialsRetained;
        if (!bMaterialFlowCommitted) break;
    }
    if (!bMaterialFlowCommitted)
    {
        RestoreMaterialFlowStates();
        RestoreS02States();
        Staging->SetStaticMesh(nullptr);
        OutReason = TEXT(
            "PRESS PRESENTATION MATERIALFLOW V002 BUNDLE FAILED EXACT MESH/TRANSFORM/NATIVE-MATERIAL VALIDATION");
        return false;
    }
    for (const FMaterialFlowAssignment& Assignment : MaterialFlowAssignments)
    {
        Assignment.Component->SetVisibility(true, true);
        Assignment.Component->SetHiddenInGame(false, true);
    }

    UStaticMeshComponent* Former = GetDetailedPresentationComponent(
        ActiveDetailedPresentationIndex);
    if (Former)
    {
        Former->SetVisibility(false, true);
        Former->SetHiddenInGame(true, true);
        Former->SetStaticMesh(nullptr);
    }

    Staging->SetVisibility(false, true);
    Staging->SetHiddenInGame(true, true);
    ConfiguredStationTransforms = MoveTemp(CandidateStationTransforms);
    ConfiguredItems = MoveTemp(CandidateItems);
    ConfiguredLayoutId = Layout.LayoutId;
    ConfiguredLayoutRevision = Layout.Revision;
    ActiveDetailedPresentationIndex = StagingIndex;
    bPresentationConfigured = true;
    ConfigureNativeTrainModules();
    ConfigureMechanismAnimation(CandidateS02RamWorldTransform);
    // Apply actor visibility last: an earlier aggregate staging pass can leave
    // its hidden state propagated to newly configured child components.
    SetActorHiddenInGame(false);
    EnsureS02DeepDrawRuntimeVisibility();
    EnsureS03S06StagePackRuntimeVisibility();
    EnsureMaterialFlowRuntimeVisibility();
    OutReason = TEXT(
        "NATIVE MODULAR PRESS TRAIN ACTIVE: S01-S07, TEXTURED MATERIALFLOW V002 ENDPOINTS, SIX-MODULE TEXTURED S02 V003, FOUR STATIC TEXTURED S03-S06 STAGEPACK CELLS, 17 SEMANTIC VISUAL BUNDLES, 11 UNREAL-ANIMATED MECHANISMS, 268 LOGICAL ITEMS, WIP 0");
    return true;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetVisibleInstanceCount() const
{
    return bPresentationConfigured && StationBases && StationBases->IsVisible()
        && !StationBases->bHiddenInGame
        ? LBOneFactoryPressPresentationPrivate::ExpectedRenderedAggregateCount : 0;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetVisualBatchCount() const
{
    return GetVisibleInstanceCount() > 0
        ? LBOneFactoryPressPresentationPrivate::ExpectedVisualBatchCount : 0;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetAnimatedMechanismCount() const
{
    return bMechanismAnimationActive ? GetMotionComponents().Num() : 0;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetInstanceCountForRole(
    const ELBOneFactoryPressStarterRole InRole) const
{
    int32 Count = 0;
    for (const FLBOneFactoryPressPresentationItem& Item : ConfiguredItems)
    {
        if (Item.Role == InRole) ++Count;
    }
    return Count;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetInstanceCountForBatch(
    const ELBOneFactoryPressPresentationBatch Batch) const
{
    int32 Count = 0;
    for (const FLBOneFactoryPressPresentationItem& Item : ConfiguredItems)
    {
        if (Item.Batch == Batch) ++Count;
    }
    return Count;
}

bool ALBOneFactoryPressStarterPresentationActor::GetConfiguredStationTransform(
    const FName StationId, FTransform& OutWorldTransform) const
{
    const FTransform* Found = ConfiguredStationTransforms.Find(StationId);
    if (!bPresentationConfigured || !Found) return false;
    OutWorldTransform = *Found;
    return true;
}

TArray<FLBOneFactoryPressPresentationItem>
ALBOneFactoryPressStarterPresentationActor::GetConfiguredItemsForRole(
    const ELBOneFactoryPressStarterRole InRole) const
{
    TArray<FLBOneFactoryPressPresentationItem> Result;
    for (const FLBOneFactoryPressPresentationItem& Item : ConfiguredItems)
    {
        if (Item.Role == InRole) Result.Add(Item);
    }
    return Result;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetExpectedVisualBatchCount()
{
    return LBOneFactoryPressPresentationPrivate::ExpectedVisualBatchCount;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetExpectedVisibleInstanceCount()
{
    return LBOneFactoryPressPresentationPrivate::ExpectedRenderedAggregateCount;
}

int32 ALBOneFactoryPressStarterPresentationActor::GetExpectedInstanceCountForRole(
    const ELBOneFactoryPressStarterRole InRole)
{
    switch (InRole)
    {
    case ELBOneFactoryPressStarterRole::InboundCoilReceiving: return 18;
    case ELBOneFactoryPressStarterRole::WrappedCoilStorage: return 37;
    case ELBOneFactoryPressStarterRole::BlankPreparation: return 31;
    case ELBOneFactoryPressStarterRole::PreparedBlankBuffer: return 34;
    case ELBOneFactoryPressStarterRole::ConfigurablePressTrain: return 89;
    case ELBOneFactoryPressStarterRole::PanelInspection: return 19;
    case ELBOneFactoryPressStarterRole::PanelStillageDispatch: return 40;
    default: return 0;
    }
}

int32 ALBOneFactoryPressStarterPresentationActor::GetExpectedInstanceCountForBatch(
    const ELBOneFactoryPressPresentationBatch Batch)
{
    switch (Batch)
    {
    case ELBOneFactoryPressPresentationBatch::GraphiteCube: return 32;
    case ELBOneFactoryPressPresentationBatch::TealStructureCube: return 88;
    case ELBOneFactoryPressPresentationBatch::SteelCube: return 34;
    case ELBOneFactoryPressPresentationBatch::SafetyCube: return 38;
    case ELBOneFactoryPressPresentationBatch::StatusCube: return 18;
    case ELBOneFactoryPressPresentationBatch::GraphiteCylinder: return 16;
    case ELBOneFactoryPressPresentationBatch::SteelCylinder: return 8;
    case ELBOneFactoryPressPresentationBatch::FloorRouteCube: return 34;
    default: return 0;
    }
}

TArray<FSoftObjectPath>
ALBOneFactoryPressStarterPresentationActor::GetRequiredNativeAssetPaths()
{
    using namespace LBOneFactoryPressPresentationPrivate;
    TArray<FSoftObjectPath> RequiredAssets;
    RequiredAssets.Reserve(1 + 6 + UE_ARRAY_COUNT(DetailedMaterialPaths)
        + 1 + UE_ARRAY_COUNT(S02DeepDrawMaterialPaths)
        + UE_ARRAY_COUNT(S03S06StagePackFrameMeshPaths)
        + UE_ARRAY_COUNT(S03S06StagePackCueMeshPaths)
        + 1 + UE_ARRAY_COUNT(S03S06StagePackMaterialPaths)
        + UE_ARRAY_COUNT(MaterialFlowMeshPaths)
        + UE_ARRAY_COUNT(MaterialFlowMaterialPaths));
    RequiredAssets.Emplace(DetailedMeshPath);
    RequiredAssets.Emplace(S02DeepDrawStaticMeshPath);
    RequiredAssets.Emplace(S02DeepDrawRamMeshPath);
    RequiredAssets.Emplace(S02DeepDrawBlankholderMeshPath);
    RequiredAssets.Emplace(S02DeepDrawBolsterMeshPath);
    RequiredAssets.Emplace(S02DeepDrawFlywheelMeshPath);
    RequiredAssets.Emplace(S02DeepDrawSafetyGateMeshPath);
    for (const TCHAR* MaterialPath : DetailedMaterialPaths)
        RequiredAssets.Emplace(MaterialPath);
    RequiredAssets.Emplace(S02DeepDrawMaterialMasterPath);
    for (const TCHAR* MaterialPath : S02DeepDrawMaterialPaths)
        RequiredAssets.Emplace(MaterialPath);
    for (const TCHAR* MeshPath : S03S06StagePackFrameMeshPaths)
        RequiredAssets.Emplace(MeshPath);
    for (const TCHAR* MeshPath : S03S06StagePackCueMeshPaths)
        RequiredAssets.Emplace(MeshPath);
    RequiredAssets.Emplace(S03S06StagePackMaterialMasterPath);
    for (const TCHAR* MaterialPath : S03S06StagePackMaterialPaths)
        RequiredAssets.Emplace(MaterialPath);
    for (const TCHAR* MeshPath : MaterialFlowMeshPaths)
        RequiredAssets.Emplace(MeshPath);
    for (const TCHAR* MaterialPath : MaterialFlowMaterialPaths)
        RequiredAssets.Emplace(MaterialPath);
    return RequiredAssets;
}

bool ALBOneFactoryPressStarterPresentationActor::
    ValidateNativePresentationReferences(
        const FString& PresentationClassPath,
        const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    const FLBOneFactoryPressNativeOnlyProfile Profile =
        ULBOneFactoryPressStarterLayoutLibrary::MakeNativeOnlyProfile();
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateNativeOnlyProfile(
            Profile, OutReason))
    {
        return false;
    }
    if (!PresentationClassPath.Equals(ExpectedPresentationClassPath,
            ESearchCase::CaseSensitive))
    {
        OutReason = TEXT("PRESS PRESENTATION CLASS DRIFTED FROM ITS EXACT NATIVE CODE CONTRACT");
        return false;
    }
    for (const FString& Token : Profile.ForbiddenSourceTokens)
    {
        if (PresentationClassPath.Contains(Token, ESearchCase::IgnoreCase))
        {
            OutReason = TEXT("PRESS PRESENTATION CLASS CONTAINS A FORBIDDEN SOURCE TOKEN");
            return false;
        }
    }
    if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
            Profile.Policy, ELBOneFactoryAssetProvenance::NativeCode,
            PresentationClassPath, OutReason))
    {
        return false;
    }

    const TArray<FSoftObjectPath> Expected = GetRequiredNativeAssetPaths();
    if (AssetPaths.Num() != Expected.Num())
    {
        OutReason = TEXT(
            "PRESS PRESENTATION REQUIRES THE EXACT LEGACY CLOSURE PLUS S02 V003, STATIC S03-S06 STAGEPACK AND MATERIALFLOW V002 PBR CLOSURES");
        return false;
    }
    for (int32 Index = 0; Index < Expected.Num(); ++Index)
    {
        if (AssetPaths[Index].IsNull() || AssetPaths[Index] != Expected[Index])
        {
            OutReason = TEXT(
                "PRESS PRESENTATION OWNED ASSET REFERENCE LIST DRIFTED");
            return false;
        }
        const FString Reference = AssetPaths[Index].ToString();
        if (!Reference.StartsWith(DetailedPresentationRoot,
                ESearchCase::CaseSensitive)
            && !Reference.StartsWith(S03S06StagePackRoot,
                ESearchCase::CaseSensitive)
            && !Reference.StartsWith(MaterialFlowPackRoot,
                ESearchCase::CaseSensitive))
        {
            OutReason = TEXT(
                "PRESS PRESENTATION REFERENCE IS OUTSIDE ITS OWNED ONEFACTORY NATIVE PRESS ROOT");
            return false;
        }
        for (const FString& Token : Profile.ForbiddenSourceTokens)
        {
            if (Reference.Contains(Token, ESearchCase::IgnoreCase))
            {
                OutReason = TEXT("PRESS PRESENTATION REFERENCE CONTAINS A FORBIDDEN SOURCE TOKEN");
                return false;
            }
        }
        const bool bNativeAuthoredRuntimePrep = Reference.Contains(
                TEXT("/S02DeepDraw_v003/"), ESearchCase::CaseSensitive)
            || Reference.StartsWith(S03S06StagePackRoot,
                ESearchCase::CaseSensitive)
            || Reference.StartsWith(MaterialFlowPackRoot,
                ESearchCase::CaseSensitive);
        const ELBOneFactoryAssetProvenance Provenance = bNativeAuthoredRuntimePrep
            ? ELBOneFactoryAssetProvenance::NativeAuthored
            : ELBOneFactoryAssetProvenance::VerifiedPreMeshyNative;
        if (!ULBOneFactoryLayoutLibrary::ValidateAssetProvenance(
                Profile.Policy, Provenance, Reference, OutReason))
        {
            return false;
        }
    }
    OutReason = TEXT(
        "PRESS PRESENTATION CLASS AND EXACT 68-ASSET OWNED CLOSURE HAVE VERIFIED LEGACY, NATIVE-AUTHORED S02 V003, STATIC S03-S06 STAGEPACK AND MATERIALFLOW V002 PROVENANCE");
    return true;
}

TArray<FLBOneFactoryPressPresentationItem>
ALBOneFactoryPressStarterPresentationActor::BuildExpectedPresentationItems(
    const FLBOneFactoryPressStarterLayoutState& Layout)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    FString LayoutReason;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            Layout, LayoutReason))
    {
        return {};
    }

    TArray<FLBOneFactoryPressPresentationItem> Items;
    Items.Reserve(ExpectedLogicalItemCount);
    const FLBOneFactoryPressStarterStationState* Inbound = FindStation(Layout,
        ELBOneFactoryPressStarterRole::InboundCoilReceiving);
    const FLBOneFactoryPressStarterStationState* CoilStore = FindStation(Layout,
        ELBOneFactoryPressStarterRole::WrappedCoilStorage);
    const FLBOneFactoryPressStarterStationState* BlankPrep = FindStation(Layout,
        ELBOneFactoryPressStarterRole::BlankPreparation);
    const FLBOneFactoryPressStarterStationState* BlankBuffer = FindStation(Layout,
        ELBOneFactoryPressStarterRole::PreparedBlankBuffer);
    const FLBOneFactoryPressStarterStationState* Press = FindStation(Layout,
        ELBOneFactoryPressStarterRole::ConfigurablePressTrain);
    const FLBOneFactoryPressStarterStationState* Inspection = FindStation(Layout,
        ELBOneFactoryPressStarterRole::PanelInspection);
    const FLBOneFactoryPressStarterStationState* Dispatch = FindStation(Layout,
        ELBOneFactoryPressStarterRole::PanelStillageDispatch);
    if (!Inbound || !CoilStore || !BlankPrep || !BlankBuffer || !Press
        || !Inspection || !Dispatch)
    {
        return {};
    }
    BuildInboundReceiving(Items, *Inbound);
    BuildCoilStore(Items, *CoilStore);
    BuildBlankPreparation(Items, *BlankPrep);
    BuildPreparedBlankAndDieBuffer(Items, *BlankBuffer);
    BuildPressTrain(Items, *Press);
    BuildInspection(Items, *Inspection);
    BuildDispatch(Items, *Dispatch);
    AddMaterialRoutes(Items, Layout);
    return Items;
}

bool ALBOneFactoryPressStarterPresentationActor::ValidatePresentationContract(
    const FLBOneFactoryPressStarterLayoutState& Layout,
    const TArray<FLBOneFactoryPressPresentationItem>& Items,
    FString& OutReason)
{
    using namespace LBOneFactoryPressPresentationPrivate;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            Layout, OutReason))
    {
        return false;
    }
    const TArray<FLBOneFactoryPressPresentationItem> Expected =
        BuildExpectedPresentationItems(Layout);
    if (Expected.Num() != ExpectedLogicalItemCount
        || Items.Num() != ExpectedLogicalItemCount)
    {
        OutReason = TEXT(
            "PRESS PRESENTATION REQUIRES EXACTLY 268 LOGICAL VISUAL RECORDS");
        return false;
    }

    TSet<FName> Identities;
    TMap<ELBOneFactoryPressStarterRole, int32> RoleCounts;
    TMap<ELBOneFactoryPressPresentationBatch, int32> BatchCounts;
    int32 PressCrownCount = 0;
    float HighestPrimitiveTopCm = 0.0f;
    for (int32 Index = 0; Index < Items.Num(); ++Index)
    {
        const FLBOneFactoryPressPresentationItem& Item = Items[Index];
        const FLBOneFactoryPressStarterStationState* Station =
            FindStation(Layout, Item.StationId);
        if (Item.Version != 1 || Item.PresentationId.IsNone()
            || Item.StationId.IsNone() || !Station || Station->Role != Item.Role
            || Item.bRepresentsProcessWIP || !IsFiniteTransform(Item.WorldTransform))
        {
            OutReason = TEXT("PRESS PRESENTATION HAS INVALID CORE DATA OR A WIP CLAIM");
            return false;
        }
        if (Identities.Contains(Item.PresentationId))
        {
            OutReason = TEXT("PRESS PRESENTATION IDENTITIES MUST BE UNIQUE");
            return false;
        }
        Identities.Add(Item.PresentationId);
        RoleCounts.FindOrAdd(Item.Role) += 1;
        BatchCounts.FindOrAdd(Item.Batch) += 1;
        if (!SameItem(Item, Expected[Index]))
        {
            OutReason = TEXT("PRESS PRESENTATION INVENTORY OR TRANSFORM DRIFTED FROM V001");
            return false;
        }
        const FString Id = Item.PresentationId.ToString();
        if (Item.Role == ELBOneFactoryPressStarterRole::ConfigurablePressTrain
            && Id.Contains(TEXT("PRESS_STAGE_"))
            && Id.EndsWith(TEXT("_CROWN")))
        {
            ++PressCrownCount;
        }
        HighestPrimitiveTopCm = FMath::Max(HighestPrimitiveTopCm,
            Item.WorldTransform.GetLocation().Z
                + Item.WorldTransform.GetScale3D().Z * 50.0f);
    }
    if (Identities.Num() != ExpectedLogicalItemCount || PressCrownCount != 7
        || HighestPrimitiveTopCm < 900.0f)
    {
        OutReason = TEXT("PRESS PRESENTATION LOST ITS SEVEN-STAGE OR RAISED-SILHOUETTE CONTRACT");
        return false;
    }
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPressStarterRole::InboundCoilReceiving);
        Value <= static_cast<int32>(
            ELBOneFactoryPressStarterRole::PanelStillageDispatch); ++Value)
    {
        const ELBOneFactoryPressStarterRole Role =
            static_cast<ELBOneFactoryPressStarterRole>(Value);
        if (RoleCounts.FindRef(Role) != GetExpectedInstanceCountForRole(Role))
        {
            OutReason = TEXT("PRESS PRESENTATION ROLE COUNTS DRIFTED");
            return false;
        }
    }
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPressPresentationBatch::GraphiteCube);
        Value <= static_cast<int32>(
            ELBOneFactoryPressPresentationBatch::FloorRouteCube); ++Value)
    {
        const ELBOneFactoryPressPresentationBatch Batch =
            static_cast<ELBOneFactoryPressPresentationBatch>(Value);
        if (BatchCounts.FindRef(Batch) !=
            GetExpectedInstanceCountForBatch(Batch))
        {
            OutReason = TEXT("PRESS PRESENTATION BATCH COUNTS DRIFTED");
            return false;
        }
    }
    OutReason = TEXT(
        "PRESS PRESENTATION CONTRACT VALID: 8 LOGICAL BATCHES, 268 LOGICAL ITEMS, 7 STAGES, WIP 0");
    return true;
}

const TCHAR* ALBOneFactoryPressStarterPresentationActor::GetPresentationClassPath()
{
    return LBOneFactoryPressPresentationPrivate::ExpectedPresentationClassPath;
}

FName ALBOneFactoryPressStarterPresentationActor::GetPresentationTag()
{
    return TEXT("LB.OneFactory.PressStarter.Presentation.v001");
}
