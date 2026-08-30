#include "LBOneFactoryPressStarterPresentationActor.h"

#if WITH_DEV_AUTOMATION_TESTS

#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "LBFactoryProcessPortComponent.h"
#include "Materials/MaterialInterface.h"
#include "Misc/AutomationTest.h"
#include "UObject/UnrealType.h"

namespace LBOneFactoryPressPresentationTestsPrivate
{
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
    const TCHAR* S03S06StagePackRoot =
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/");
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
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/Materials/"
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
    const TCHAR* MaterialFlowPackRoot =
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MaterialFlowPack_v002/");
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
    const FName MaterialFlowComponentNames[] =
    {
        TEXT("S01CoilCartMover"), TEXT("S01CoilRackPresentation"),
        TEXT("S01DecoilerBasePresentation"), TEXT("S01DecoilerSpindleMover"),
        TEXT("S01StraightenerFeedPresentation"), TEXT("S01FeedBridgePresentation"),
        TEXT("S07ExitConveyorBeltPresentation"), TEXT("S07ExitConveyorFramePresentation"),
        TEXT("S07InspectionCellPresentation"), TEXT("S07OutboundDunnagePresentation")
    };
    const FVector MaterialFlowDimensionsCm[] =
    {
        FVector(200.0f, 161.0f, 68.50256f),
        FVector(327.0f, 480.00002f, 168.0f),
        FVector(279.50001f, 177.0f, 225.50807f),
        FVector(161.0f, 144.0f, 144.0f),
        FVector(338.0f, 304.0f, 167.5f),
        FVector(110.0f, 428.0f, 135.0f),
        FVector(150.0f, 460.00002f, 28.0f),
        FVector(250.0f, 505.0f, 98.0f),
        FVector(440.0f, 238.0f, 240.99998f),
        FVector(392.50002f, 330.5f, 149.09938f)
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
        FVector DimensionsCm;
        const FName* Slots;
        int32 SlotCount;
    };
    const FS03S06StagePackMeshContract S03S06StagePackFrameContracts[] =
    {
        { FVector(648.0f, 620.0f, 950.0f), S03S06StagePackFrameSlots, UE_ARRAY_COUNT(S03S06StagePackFrameSlots) },
        { FVector(648.0f, 620.0f, 900.0f), S03S06StagePackFrameSlots, UE_ARRAY_COUNT(S03S06StagePackFrameSlots) },
        { FVector(648.0f, 620.0f, 850.0f), S03S06StagePackFrameSlots, UE_ARRAY_COUNT(S03S06StagePackFrameSlots) },
        { FVector(648.0f, 620.0f, 900.0f), S03S06StagePackFrameSlots, UE_ARRAY_COUNT(S03S06StagePackFrameSlots) }
    };
    const FS03S06StagePackMeshContract S03S06StagePackCueContracts[] =
    {
        { FVector(56.5f, 222.0f, 178.0f), S03S06StagePackS03CueSlots, UE_ARRAY_COUNT(S03S06StagePackS03CueSlots) },
        { FVector(68.0f, 232.0f, 225.0f), S03S06StagePackS04CueSlots, UE_ARRAY_COUNT(S03S06StagePackS04CueSlots) },
        { FVector(71.5f, 226.0f, 224.0f), S03S06StagePackS05CueSlots, UE_ARRAY_COUNT(S03S06StagePackS05CueSlots) },
        { FVector(54.5f, 224.0f, 178.0f), S03S06StagePackS06CueSlots, UE_ARRAY_COUNT(S03S06StagePackS06CueSlots) }
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

    const TCHAR* GetMaterialFlowExpectedMaterialPath(const FName SlotName)
    {
        const int32 SharedMaterialIndex = GetS03S06StagePackMaterialIndex(SlotName);
        if (SharedMaterialIndex != INDEX_NONE)
        {
            return S03S06StagePackMaterialPaths[SharedMaterialIndex];
        }
        if (SlotName == TEXT("CA_MW_DarkRubber")) return MaterialFlowMaterialPaths[0];
        if (SlotName == TEXT("CA_MW_GalvanizedCoil")) return MaterialFlowMaterialPaths[1];
        if (SlotName == TEXT("CA_MW_StampedPanel")) return MaterialFlowMaterialPaths[2];
        if (SlotName == TEXT("CA_MW_TaskLightGlass")) return MaterialFlowMaterialPaths[3];
        return nullptr;
    }

    int32 FindS03S06StagePackMeshIndex(const FString& MeshPath,
        const TCHAR* const* ExpectedPaths, const int32 ExpectedCount)
    {
        for (int32 Index = 0; Index < ExpectedCount; ++Index)
        {
            if (MeshPath.Equals(ExpectedPaths[Index], ESearchCase::CaseSensitive))
            {
                return Index;
            }
        }
        return INDEX_NONE;
    }

    bool IsOwnedPressAssetPath(const FString& AssetPath)
    {
        return AssetPath.StartsWith(DetailedPresentationRoot,
                ESearchCase::CaseSensitive)
            || AssetPath.StartsWith(S03S06StagePackRoot,
                ESearchCase::CaseSensitive)
            || AssetPath.StartsWith(MaterialFlowPackRoot,
                ESearchCase::CaseSensitive);
    }

    TArray<FSoftObjectPath> ExpectedNativeAssets()
    {
        TArray<FSoftObjectPath> Assets = {
            FSoftObjectPath(DetailedMeshPath),
            FSoftObjectPath(S02DeepDrawStaticMeshPath),
            FSoftObjectPath(S02DeepDrawRamMeshPath),
            FSoftObjectPath(S02DeepDrawBlankholderMeshPath),
            FSoftObjectPath(S02DeepDrawBolsterMeshPath),
            FSoftObjectPath(S02DeepDrawFlywheelMeshPath),
            FSoftObjectPath(S02DeepDrawSafetyGateMeshPath),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_AmberSafetyActive_v086.M_CA_MW_PR009_AmberSafetyActive_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_DriveBlue_v086.M_CA_MW_PR009_DriveBlue_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_EStopRed_v086.M_CA_MW_PR009_EStopRed_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LabelWhite_v086.M_CA_MW_PR009_LabelWhite_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredCairnwellGreen_v086.M_CA_MW_PR009_LayeredCairnwellGreen_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v086.M_CA_MW_PR009_LayeredFoundryCharcoal_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredSafetyYellow_v086.M_CA_MW_PR009_LayeredSafetyYellow_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_LayeredServiceGrey_v086.M_CA_MW_PR009_LayeredServiceGrey_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_MachinedSteel_v086.M_CA_MW_PR009_MachinedSteel_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_OiledBlankSteel_v086.M_CA_MW_PR009_OiledBlankSteel_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_Rubber_v086.M_CA_MW_PR009_Rubber_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PR009_SensorGlass_v086.M_CA_MW_PR009_SensorGlass_v086")),
            FSoftObjectPath(TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/Materials/M_CA_MW_PT_ServiceCopper_v383.M_CA_MW_PT_ServiceCopper_v383"))
        };
        Assets.Emplace(S02DeepDrawMaterialMasterPath);
        for (const TCHAR* MaterialPath : S02DeepDrawMaterialPaths)
        {
            Assets.Emplace(MaterialPath);
        }
        for (const TCHAR* MeshPath : S03S06StagePackFrameMeshPaths)
        {
            Assets.Emplace(MeshPath);
        }
        for (const TCHAR* MeshPath : S03S06StagePackCueMeshPaths)
        {
            Assets.Emplace(MeshPath);
        }
        Assets.Emplace(S03S06StagePackMaterialMasterPath);
        for (const TCHAR* MaterialPath : S03S06StagePackMaterialPaths)
        {
            Assets.Emplace(MaterialPath);
        }
        for (const TCHAR* MeshPath : MaterialFlowMeshPaths)
        {
            Assets.Emplace(MeshPath);
        }
        for (const TCHAR* MaterialPath : MaterialFlowMaterialPaths)
        {
            Assets.Emplace(MaterialPath);
        }
        return Assets;
    }

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

    UStaticMeshComponent* FindActiveDetailedComponent(
        const ALBOneFactoryPressStarterPresentationActor& Presentation)
    {
        TArray<UStaticMeshComponent*> Components;
        Presentation.GetComponents<UStaticMeshComponent>(Components);
        UStaticMeshComponent* Active = nullptr;
        for (UStaticMeshComponent* Component : Components)
        {
            if (!Component || !Component->GetStaticMesh())
            {
                continue;
            }
            if (Component->GetStaticMesh()->GetPathName()
                    != FString(DetailedMeshPath))
            {
                continue;
            }
            if (Active) return nullptr;
            Active = Component;
        }
        return Active;
    }

    int32 CountRole(const TArray<FLBOneFactoryPressPresentationItem>& Items,
        const ELBOneFactoryPressStarterRole Role)
    {
        int32 Count = 0;
        for (const FLBOneFactoryPressPresentationItem& Item : Items)
        {
            if (Item.Role == Role) ++Count;
        }
        return Count;
    }

    int32 CountBatch(const TArray<FLBOneFactoryPressPresentationItem>& Items,
        const ELBOneFactoryPressPresentationBatch Batch)
    {
        int32 Count = 0;
        for (const FLBOneFactoryPressPresentationItem& Item : Items)
        {
            if (Item.Batch == Batch) ++Count;
        }
        return Count;
    }
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryPressPresentationContractTest,
    "LineBoss.OneFactory.PressStarter.Presentation.NativeContractCountsAndRoleLookup",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPressPresentationContractTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    const FLBOneFactoryPressStarterLayoutState Layout =
        ULBOneFactoryPressStarterLayoutLibrary::MakeCanonicalStarterLayout();
    const TArray<FLBOneFactoryPressPresentationItem> Items =
        ALBOneFactoryPressStarterPresentationActor::
            BuildExpectedPresentationItems(Layout);
    FString Reason;
    TestTrue(TEXT("Exact native Press presentation contract validates"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidatePresentationContract(Layout, Items, Reason));
    TestEqual(TEXT("Presentation renders ten native batches, authored S02, four static StagePack cells, and two MaterialFlow endpoints"),
        ALBOneFactoryPressStarterPresentationActor::
            GetExpectedVisualBatchCount(), 17);
    TestEqual(TEXT("Presentation renders seven native S01-S07 station bodies"),
        ALBOneFactoryPressStarterPresentationActor::
            GetExpectedVisibleInstanceCount(), 7);
    TestEqual(TEXT("Presentation retains exactly 268 logical selection records"),
        Items.Num(), 268);

    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPressStarterRole::InboundCoilReceiving);
        Value <= static_cast<int32>(
            ELBOneFactoryPressStarterRole::PanelStillageDispatch); ++Value)
    {
        const ELBOneFactoryPressStarterRole Role =
            static_cast<ELBOneFactoryPressStarterRole>(Value);
        TestEqual(TEXT("Each stable station role has its frozen visual count"),
            LBOneFactoryPressPresentationTestsPrivate::CountRole(Items, Role),
            ALBOneFactoryPressStarterPresentationActor::
                GetExpectedInstanceCountForRole(Role));
    }
    for (int32 Value = static_cast<int32>(
            ELBOneFactoryPressPresentationBatch::GraphiteCube);
        Value <= static_cast<int32>(
            ELBOneFactoryPressPresentationBatch::FloorRouteCube); ++Value)
    {
        const ELBOneFactoryPressPresentationBatch Batch =
            static_cast<ELBOneFactoryPressPresentationBatch>(Value);
        TestEqual(TEXT("Each logical semantic batch retains its frozen item count"),
            LBOneFactoryPressPresentationTestsPrivate::CountBatch(Items, Batch),
            ALBOneFactoryPressStarterPresentationActor::
                GetExpectedInstanceCountForBatch(Batch));
    }
    TestFalse(TEXT("No presentation primitive claims process WIP"),
        Items.ContainsByPredicate([](
            const FLBOneFactoryPressPresentationItem& Item)
        {
            return Item.bRepresentsProcessWIP;
        }));

    const TArray<FSoftObjectPath> NativeAssets =
        ALBOneFactoryPressStarterPresentationActor::
            GetRequiredNativeAssetPaths();
    TestTrue(TEXT("Exact class plus legacy, authored S02, static StagePack, and MaterialFlow closure passes"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPressStarterPresentationActor::
                    GetPresentationClassPath(), NativeAssets, Reason));
    const TArray<FSoftObjectPath> ExpectedNativeAssets =
        LBOneFactoryPressPresentationTestsPrivate::ExpectedNativeAssets();
    TestEqual(TEXT("Exact owned closure contains legacy, textured S02 v003, static S03-S06 StagePack, and MaterialFlow v002 PBR bindings"),
        NativeAssets.Num(), 68);
    TestTrue(TEXT("Owned asset list has exact immutable order"),
        NativeAssets == ExpectedNativeAssets);

    const FObjectPropertyBase* DetailedMeshProperty =
        FindFProperty<FObjectPropertyBase>(
            ALBOneFactoryPressStarterPresentationActor::StaticClass(),
            TEXT("DetailedPresentationMesh"));
    TestNotNull(TEXT(
        "Detailed aggregate dependency is a reflected hard-object property"),
        DetailedMeshProperty);
    if (DetailedMeshProperty)
    {
        TestFalse(TEXT(
            "Detailed aggregate dependency is serialized, never Transient"),
            DetailedMeshProperty->HasAnyPropertyFlags(CPF_Transient));
        TestTrue(TEXT("Hard dependency accepts only UStaticMesh"),
            DetailedMeshProperty->PropertyClass == UStaticMesh::StaticClass());
        const ALBOneFactoryPressStarterPresentationActor* CDO =
            ALBOneFactoryPressStarterPresentationActor::StaticClass()
                ->GetDefaultObject<
                    ALBOneFactoryPressStarterPresentationActor>();
        const UObject* HardReferencedMesh = CDO
            ? DetailedMeshProperty->GetObjectPropertyValue_InContainer(CDO)
            : nullptr;
        TestNotNull(TEXT(
            "Native CDO resolves the packaged-cook aggregate dependency"),
            HardReferencedMesh);
        if (HardReferencedMesh)
        {
            TestEqual(TEXT(
                "Native CDO hard dependency resolves the exact owned mesh"),
                HardReferencedMesh->GetPathName(),
                FString(LBOneFactoryPressPresentationTestsPrivate::
                    DetailedMeshPath));
        }
    }
    const ALBOneFactoryPressStarterPresentationActor* CDO =
        ALBOneFactoryPressStarterPresentationActor::StaticClass()
            ->GetDefaultObject<ALBOneFactoryPressStarterPresentationActor>();
    const auto VerifyAuthoredS02HardReference = [this, CDO](
        const TCHAR* PropertyName, const TCHAR* ExpectedPath)
    {
        const FObjectPropertyBase* Property = FindFProperty<FObjectPropertyBase>(
            ALBOneFactoryPressStarterPresentationActor::StaticClass(), PropertyName);
        TestNotNull(TEXT("S02 authored asset is a reflected hard-object property"),
            Property);
        if (!Property) return;
        TestFalse(TEXT("S02 authored asset dependency is serialized, never Transient"),
            Property->HasAnyPropertyFlags(CPF_Transient));
        TestTrue(TEXT("S02 authored hard dependency accepts only UStaticMesh"),
            Property->PropertyClass == UStaticMesh::StaticClass());
        const UObject* HardReference = CDO
            ? Property->GetObjectPropertyValue_InContainer(CDO) : nullptr;
        TestNotNull(TEXT("Native CDO resolves the authored S02 cooked dependency"),
            HardReference);
        if (HardReference)
        {
            TestEqual(TEXT("Native CDO resolves the exact authored S02 mesh"),
                HardReference->GetPathName(), FString(ExpectedPath));
        }
    };
    VerifyAuthoredS02HardReference(TEXT("S02DeepDrawStaticMesh"),
        LBOneFactoryPressPresentationTestsPrivate::S02DeepDrawStaticMeshPath);
    VerifyAuthoredS02HardReference(TEXT("S02DeepDrawRamMesh"),
        LBOneFactoryPressPresentationTestsPrivate::S02DeepDrawRamMeshPath);
    VerifyAuthoredS02HardReference(TEXT("S02DeepDrawBlankholderMesh"),
        LBOneFactoryPressPresentationTestsPrivate::S02DeepDrawBlankholderMeshPath);
    VerifyAuthoredS02HardReference(TEXT("S02DeepDrawBolsterMesh"),
        LBOneFactoryPressPresentationTestsPrivate::S02DeepDrawBolsterMeshPath);
    VerifyAuthoredS02HardReference(TEXT("S02DeepDrawFlywheelMesh"),
        LBOneFactoryPressPresentationTestsPrivate::S02DeepDrawFlywheelMeshPath);
    VerifyAuthoredS02HardReference(TEXT("S02DeepDrawSafetyGateMesh"),
        LBOneFactoryPressPresentationTestsPrivate::S02DeepDrawSafetyGateMeshPath);
    const FObjectPropertyBase* S02MaterialMasterProperty =
        FindFProperty<FObjectPropertyBase>(
            ALBOneFactoryPressStarterPresentationActor::StaticClass(),
            TEXT("S02DeepDrawMaterialMaster"));
    TestNotNull(TEXT("S02 v003 PBR master is a reflected hard-object property"),
        S02MaterialMasterProperty);
    if (S02MaterialMasterProperty)
    {
        TestFalse(TEXT("S02 v003 PBR master is serialized, never Transient"),
            S02MaterialMasterProperty->HasAnyPropertyFlags(CPF_Transient));
        const UObject* Master = CDO
            ? S02MaterialMasterProperty->GetObjectPropertyValue_InContainer(CDO)
            : nullptr;
        TestEqual(TEXT("S02 v003 PBR master resolves its exact owned path"),
            Master ? Master->GetPathName() : FString(),
            FString(LBOneFactoryPressPresentationTestsPrivate::
                S02DeepDrawMaterialMasterPath));
    }
    const FArrayProperty* S02MaterialLibraryProperty =
        FindFProperty<FArrayProperty>(
            ALBOneFactoryPressStarterPresentationActor::StaticClass(),
            TEXT("S02DeepDrawMaterialLibrary"));
    TestNotNull(TEXT("S02 v003 PBR material library is a reflected hard array"),
        S02MaterialLibraryProperty);
    if (S02MaterialLibraryProperty && CDO)
    {
        const FObjectPropertyBase* Inner =
            CastField<FObjectPropertyBase>(S02MaterialLibraryProperty->Inner);
        TestNotNull(TEXT("S02 v003 PBR material library stores object references"),
            Inner);
        FScriptArrayHelper MaterialLibraryHelper(S02MaterialLibraryProperty,
            S02MaterialLibraryProperty->ContainerPtrToValuePtr<void>(CDO));
        TestEqual(TEXT("S02 v003 PBR material library has its exact fifteen bindings"),
            MaterialLibraryHelper.Num(),
            static_cast<int32>(UE_ARRAY_COUNT(
                LBOneFactoryPressPresentationTestsPrivate::S02DeepDrawMaterialPaths)));
        if (Inner)
        {
            const int32 ExpectedMaterialCount = static_cast<int32>(UE_ARRAY_COUNT(
                LBOneFactoryPressPresentationTestsPrivate::S02DeepDrawMaterialPaths));
            for (int32 Index = 0;
                Index < MaterialLibraryHelper.Num() && Index < ExpectedMaterialCount;
                ++Index)
            {
                const UObject* Material = Inner->GetObjectPropertyValue(
                    MaterialLibraryHelper.GetRawPtr(Index));
                TestEqual(TEXT("S02 v003 PBR material library preserves exact material order"),
                    Material ? Material->GetPathName() : FString(),
                    FString(LBOneFactoryPressPresentationTestsPrivate::
                        S02DeepDrawMaterialPaths[Index]));
            }
        }
    }
    const auto VerifyStagePackHardArray = [this, CDO](
        const TCHAR* PropertyName, const TCHAR* const* ExpectedPaths,
        const int32 ExpectedCount, const UClass* ExpectedClass)
    {
        const FArrayProperty* Property = FindFProperty<FArrayProperty>(
            ALBOneFactoryPressStarterPresentationActor::StaticClass(),
            PropertyName);
        TestNotNull(TEXT("StagePack hard dependency is a reflected array"),
            Property);
        if (!Property || !CDO) return;
        TestFalse(TEXT("StagePack hard dependency array is serialized, never Transient"),
            Property->HasAnyPropertyFlags(CPF_Transient));
        const FObjectPropertyBase* Inner =
            CastField<FObjectPropertyBase>(Property->Inner);
        TestNotNull(TEXT("StagePack hard dependency array stores object references"),
            Inner);
        if (!Inner) return;
        TestTrue(TEXT("StagePack hard dependency array has the expected object class"),
            Inner->PropertyClass == ExpectedClass);
        FScriptArrayHelper Helper(Property,
            Property->ContainerPtrToValuePtr<void>(CDO));
        TestEqual(TEXT("StagePack hard dependency array has its exact authored closure"),
            Helper.Num(), ExpectedCount);
        for (int32 Index = 0; Index < Helper.Num() && Index < ExpectedCount;
            ++Index)
        {
            const UObject* Object = Inner->GetObjectPropertyValue(
                Helper.GetRawPtr(Index));
            TestEqual(TEXT("StagePack CDO dependency preserves exact immutable order"),
                Object ? Object->GetPathName() : FString(),
                FString(ExpectedPaths[Index]));
        }
    };
    VerifyStagePackHardArray(TEXT("S03S06StagePackFrameMeshes"),
        LBOneFactoryPressPresentationTestsPrivate::S03S06StagePackFrameMeshPaths,
        UE_ARRAY_COUNT(LBOneFactoryPressPresentationTestsPrivate::
            S03S06StagePackFrameMeshPaths), UStaticMesh::StaticClass());
    VerifyStagePackHardArray(TEXT("S03S06StagePackCueMeshes"),
        LBOneFactoryPressPresentationTestsPrivate::S03S06StagePackCueMeshPaths,
        UE_ARRAY_COUNT(LBOneFactoryPressPresentationTestsPrivate::
            S03S06StagePackCueMeshPaths), UStaticMesh::StaticClass());
    VerifyStagePackHardArray(TEXT("S03S06StagePackMaterialLibrary"),
        LBOneFactoryPressPresentationTestsPrivate::S03S06StagePackMaterialPaths,
        UE_ARRAY_COUNT(LBOneFactoryPressPresentationTestsPrivate::
            S03S06StagePackMaterialPaths), UMaterialInterface::StaticClass());
    VerifyStagePackHardArray(TEXT("MaterialFlowMeshLibrary"),
        LBOneFactoryPressPresentationTestsPrivate::MaterialFlowMeshPaths,
        UE_ARRAY_COUNT(LBOneFactoryPressPresentationTestsPrivate::
            MaterialFlowMeshPaths), UStaticMesh::StaticClass());
    VerifyStagePackHardArray(TEXT("MaterialFlowMaterialLibrary"),
        LBOneFactoryPressPresentationTestsPrivate::MaterialFlowMaterialPaths,
        UE_ARRAY_COUNT(LBOneFactoryPressPresentationTestsPrivate::
            MaterialFlowMaterialPaths), UMaterialInterface::StaticClass());
    const FObjectPropertyBase* StagePackMasterProperty =
        FindFProperty<FObjectPropertyBase>(
            ALBOneFactoryPressStarterPresentationActor::StaticClass(),
            TEXT("S03S06StagePackMaterialMaster"));
    TestNotNull(TEXT("StagePack PBR master is a reflected hard-object property"),
        StagePackMasterProperty);
    if (StagePackMasterProperty)
    {
        TestFalse(TEXT("StagePack PBR master is serialized, never Transient"),
            StagePackMasterProperty->HasAnyPropertyFlags(CPF_Transient));
        const UObject* Master = CDO
            ? StagePackMasterProperty->GetObjectPropertyValue_InContainer(CDO)
            : nullptr;
        TestEqual(TEXT("StagePack PBR master resolves its exact owned path"),
            Master ? Master->GetPathName() : FString(),
            FString(LBOneFactoryPressPresentationTestsPrivate::
                S03S06StagePackMaterialMasterPath));
    }
    for (const FSoftObjectPath& Asset : NativeAssets)
    {
        TestTrue(TEXT("Every required asset is inside an explicit owned native press root"),
            LBOneFactoryPressPresentationTestsPrivate::IsOwnedPressAssetPath(
                Asset.ToString()));
    }
    TArray<FSoftObjectPath> MeshyInjected = NativeAssets;
    MeshyInjected[0] = FSoftObjectPath(
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/MeshyAGV.MeshyAGV"));
    TestFalse(TEXT("A Meshy/vendor substitution fails closed"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidateNativePresentationReferences(
                ALBOneFactoryPressStarterPresentationActor::
                    GetPresentationClassPath(), MeshyInjected, Reason));
    TestFalse(TEXT("An unapproved presentation class fails closed"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidateNativePresentationReferences(
                TEXT("/Script/LineBossCarFactory.LBFactoryBuildMachine"),
                NativeAssets, Reason));

    TArray<FLBOneFactoryPressPresentationItem> Tampered = Items;
    Tampered[0].bRepresentsProcessWIP = true;
    TestFalse(TEXT("A WIP claim invalidates the complete visual contract"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidatePresentationContract(Layout, Tampered, Reason));
    Tampered = Items;
    Tampered.RemoveAt(Tampered.Num() - 1);
    TestFalse(TEXT("A missing route/primitive invalidates the complete contract"),
        ALBOneFactoryPressStarterPresentationActor::
            ValidatePresentationContract(Layout, Tampered, Reason));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FLBOneFactoryPressPresentationMaterialisationTest,
    "LineBoss.OneFactory.PressStarter.Presentation.FailClosedMaterialisationAndRebind",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FLBOneFactoryPressPresentationMaterialisationTest::RunTest(
    const FString& Parameters)
{
    (void)Parameters;
    UWorld* World = UWorld::CreateWorld(EWorldType::Game, false,
        TEXT("LBOneFactoryPressPresentationMaterialisationTest"));
    ALBOneFactoryPressStarterLayoutAuthority* Authority = World
        ? World->SpawnActor<ALBOneFactoryPressStarterLayoutAuthority>() : nullptr;
    ALBOneFactoryPressStarterPresentationActor* Presentation = World
        ? World->SpawnActor<ALBOneFactoryPressStarterPresentationActor>() : nullptr;
    if (!TestNotNull(TEXT("Layout authority fixture exists"), Authority)
        || !TestNotNull(TEXT("Presentation fixture exists"), Presentation))
    {
        if (World) World->DestroyWorld(false);
        return false;
    }

    TestTrue(TEXT("Actor has its stable native presentation identity"),
        Presentation->ActorHasTag(
            ALBOneFactoryPressStarterPresentationActor::GetPresentationTag()));
    TestTrue(TEXT("Presentation ticks to drive native visible mechanisms"),
        Presentation->PrimaryActorTick.bCanEverTick);
    TestFalse(TEXT("Presentation never replicates"),
        Presentation->GetIsReplicated());
    TestFalse(TEXT("Presentation has no actor collision"),
        Presentation->GetActorEnableCollision());
    TestNull(TEXT("Presentation owns no production process port"),
        Presentation->FindComponentByClass<ULBFactoryProcessPortComponent>());
    TestFalse(TEXT("Presentation never represents process WIP"),
        Presentation->RepresentsProcessWIP());
    TestTrue(TEXT("Actor advertises verified pre-Meshy native provenance"),
        Presentation->ActorHasTag(
            TEXT("LB.Provenance.VerifiedPreMeshyNative")));
    TestTrue(TEXT("Actor separately advertises the native-authored S02 source"),
        Presentation->ActorHasTag(TEXT("LB.Provenance.NativeAuthoredS02")));
    TestTrue(TEXT("Actor separately advertises the native-authored static S03-S06 StagePack"),
        Presentation->ActorHasTag(
            TEXT("LB.Provenance.NativeAuthoredS03S06StagePack")));
    TestTrue(TEXT("Actor separately advertises the native-authored MaterialFlow v002 source"),
        Presentation->ActorHasTag(
            TEXT("LB.Provenance.NativeAuthoredMaterialFlowV002")));

    FString Reason;
    TestTrue(TEXT("Canonical layout materialises atomically"),
        Presentation->ConfigureFromLayout(Authority->CaptureLayout(), Reason));
    TestTrue(TEXT("Presentation reports configured"),
        Presentation->IsPresentationConfigured());
    TestEqual(TEXT("All seven native station bodies are visible"),
        Presentation->GetVisibleInstanceCount(), 7);
    TestEqual(TEXT("Ten native batches, authored S02, four static StagePack cells, and two MaterialFlow endpoints are active"),
        Presentation->GetVisualBatchCount(), 17);
    TestEqual(TEXT("Eleven reference-sheet mechanisms are independently animated"),
        Presentation->GetAnimatedMechanismCount(), 11);
    TestEqual(TEXT("Seven-stage Press role retains exact logical inventory"),
        Presentation->GetInstanceCountForRole(
            ELBOneFactoryPressStarterRole::ConfigurablePressTrain), 89);
    TestEqual(TEXT("Graphite logical batch remains available for selection"),
        Presentation->GetInstanceCountForBatch(
            ELBOneFactoryPressPresentationBatch::GraphiteCube), 32);

    TArray<UStaticMeshComponent*> DetailedComponents;
    Presentation->GetComponents<UStaticMeshComponent>(DetailedComponents);
    TestEqual(TEXT("Actor owns staging, five S02 modules, eight static StagePack modules, ten MaterialFlow modules, ten native batches and eleven mechanisms"),
        DetailedComponents.Num(), 46);
    int32 PopulatedDetailedComponentCount = 0;
    int32 PopulatedAuthoredS02StaticCount = 0;
    int32 PopulatedAuthoredS02RamCount = 0;
    int32 PopulatedAuthoredS02BlankholderCount = 0;
    int32 PopulatedAuthoredS02BolsterCount = 0;
    int32 PopulatedAuthoredS02FlywheelCount = 0;
    int32 PopulatedAuthoredS02SafetyGateCount = 0;
    int32 PopulatedStagePackFrameCount = 0;
    int32 PopulatedStagePackCueCount = 0;
    int32 PopulatedMaterialFlowCount = 0;
    int32 PopulatedNativeStructuralComponentCount = 0;
    int32 PopulatedMotionComponentCount = 0;
    UStaticMeshComponent* AuthoredS02StaticComponent = nullptr;
    UStaticMeshComponent* AuthoredS02RamComponent = nullptr;
    UStaticMeshComponent* AuthoredS02BlankholderComponent = nullptr;
    UStaticMeshComponent* AuthoredS02BolsterComponent = nullptr;
    UStaticMeshComponent* AuthoredS02FlywheelComponent = nullptr;
    UStaticMeshComponent* AuthoredS02SafetyGateComponent = nullptr;
    TArray<const UStaticMeshComponent*> StagePackFrameComponents;
    TArray<const UStaticMeshComponent*> StagePackCueComponents;
    StagePackFrameComponents.SetNumZeroed(UE_ARRAY_COUNT(
        LBOneFactoryPressPresentationTestsPrivate::S03S06StagePackFrameMeshPaths));
    StagePackCueComponents.SetNumZeroed(UE_ARRAY_COUNT(
        LBOneFactoryPressPresentationTestsPrivate::S03S06StagePackCueMeshPaths));
    TArray<const UStaticMeshComponent*> MaterialFlowComponents;
    MaterialFlowComponents.SetNumZeroed(UE_ARRAY_COUNT(
        LBOneFactoryPressPresentationTestsPrivate::MaterialFlowMeshPaths));
    int32 NativeStationBaseInstances = INDEX_NONE;
    int32 NativeStationCrownInstances = INDEX_NONE;
    const auto VerifyStagePackComponent = [this](
        const UStaticMeshComponent* Component, const int32 Index,
        const bool bFrame)
    {
        using namespace LBOneFactoryPressPresentationTestsPrivate;
        const FS03S06StagePackMeshContract& Contract = bFrame
            ? S03S06StagePackFrameContracts[Index]
            : S03S06StagePackCueContracts[Index];
        const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
        TestNotNull(TEXT("Static StagePack component retains its imported mesh"), Mesh);
        if (!Mesh) return;
        TestEqual(TEXT("Static StagePack component uses its dedicated presentation component"),
            Component->GetFName(), FName(*FString::Printf(
                TEXT("S%02dStagePack%sPresentation"), Index + 3,
                bFrame ? TEXT("Frame") : TEXT("Cue"))));
        TestTrue(TEXT("Static StagePack component retains its receipt-scale bounds"),
            (Mesh->GetBounds().BoxExtent * 2.0f).Equals(Contract.DimensionsCm,
                3.0f));
        TestEqual(TEXT("Static StagePack component retains its exact semantic slot count"),
            Mesh->GetStaticMaterials().Num(), Contract.SlotCount);
        for (int32 SlotIndex = 0; SlotIndex < Contract.SlotCount; ++SlotIndex)
        {
            TestEqual(TEXT("Static StagePack component preserves receipt semantic slot order"),
                Mesh->GetStaticMaterials()[SlotIndex].MaterialSlotName,
                Contract.Slots[SlotIndex]);
            const int32 MaterialIndex = GetS03S06StagePackMaterialIndex(
                Contract.Slots[SlotIndex]);
            const UMaterialInterface* Material = Component->GetMaterial(SlotIndex);
            TestTrue(TEXT("Static StagePack component binds an owned semantic PBR material"),
                Material && Material->GetPathName().StartsWith(
                    S03S06StagePackRoot, ESearchCase::CaseSensitive));
            TestEqual(TEXT("Static StagePack component binds its exact semantic PBR instance"),
                Material ? Material->GetPathName() : FString(),
                FString(S03S06StagePackMaterialPaths[MaterialIndex]));
        }
    };
    const auto VerifyMaterialFlowComponent = [this](
        const UStaticMeshComponent* Component, const int32 Index)
    {
        using namespace LBOneFactoryPressPresentationTestsPrivate;
        const UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
        TestNotNull(TEXT("MaterialFlow component retains its native imported mesh"), Mesh);
        if (!Mesh) return;
        TestEqual(TEXT("MaterialFlow component uses its exact semantic component name"),
            Component->GetFName(), MaterialFlowComponentNames[Index]);
        TestEqual(TEXT("MaterialFlow component preserves its exact native mesh path"),
            Mesh->GetPathName(), FString(MaterialFlowMeshPaths[Index]));
        TestTrue(TEXT("MaterialFlow component retains its fresh-audit centimetre bounds"),
            (Mesh->GetBounds().BoxExtent * 2.0f).Equals(
                MaterialFlowDimensionsCm[Index], 0.5f));
        TestTrue(TEXT("MaterialFlow component is visible after atomic commit"),
            Component->IsVisible());
        TestFalse(TEXT("MaterialFlow component is not hidden in game after atomic commit"),
            Component->bHiddenInGame != 0);
        for (int32 SlotIndex = 0; SlotIndex < Mesh->GetStaticMaterials().Num();
            ++SlotIndex)
        {
            const FStaticMaterial& Slot = Mesh->GetStaticMaterials()[SlotIndex];
            const TCHAR* ExpectedMaterialPath = GetMaterialFlowExpectedMaterialPath(
                Slot.MaterialSlotName);
            const UMaterialInterface* NativeMaterial = Mesh->GetMaterial(SlotIndex);
            const UMaterialInterface* ComponentMaterial = Component->GetMaterial(SlotIndex);
            TestNotNull(TEXT("MaterialFlow receipt slot maps to an approved native material"),
                ExpectedMaterialPath);
            TestEqual(TEXT("MaterialFlow component retains the mesh-native material without an override"),
                ComponentMaterial, NativeMaterial);
            TestEqual(TEXT("MaterialFlow material slot preserves its exact native material instance"),
                ComponentMaterial ? ComponentMaterial->GetPathName() : FString(),
                FString(ExpectedMaterialPath ? ExpectedMaterialPath : TEXT("")));
        }
    };
    for (const UStaticMeshComponent* Component : DetailedComponents)
    {
        if (!TestNotNull(TEXT("Every detailed component exists"), Component))
            continue;
        TestEqual(TEXT("Every detailed component is non-colliding"),
            Component->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
        TestFalse(TEXT("No detailed component affects navigation"),
            Component->CanEverAffectNavigation());
        if (Component->GetStaticMesh())
        {
            const FString MeshPath = Component->GetStaticMesh()->GetPathName();
            TestFalse(TEXT("Live native press never binds a candidate PressShop mesh"),
                MeshPath.Contains(TEXT("/Candidates/PressShop/"),
                    ESearchCase::IgnoreCase));
            TestFalse(TEXT("Live native press never binds a candidate press-train mesh"),
                MeshPath.Contains(TEXT("/Candidates/PressTrains/"),
                    ESearchCase::IgnoreCase));
            if (Component->GetFName() == TEXT("PressRam_02")
                || Component->GetFName().ToString().StartsWith(TEXT("S02DeepDraw")))
            {
                TestTrue(TEXT("Every live authored textured S02 v003 module is visible after commit"),
                    Component->IsVisible());
                TestFalse(TEXT("Every live authored textured S02 v003 module is not hidden in game"),
                    Component->bHiddenInGame != 0);
            }
            if (Component->GetFName().ToString().Contains(TEXT("StagePack"),
                    ESearchCase::CaseSensitive))
            {
                TestTrue(TEXT("Every live static StagePack frame/cue module is visible after commit"),
                    Component->IsVisible());
                TestFalse(TEXT("Every live static StagePack frame/cue module is not hidden in game"),
                    Component->bHiddenInGame != 0);
                TestFalse(TEXT("Static-only StagePack pass does not bind the unposed shared slide"),
                    MeshPath.Contains(TEXT("Shared_PressSlide"),
                        ESearchCase::CaseSensitive));
                TestFalse(TEXT("Static-only StagePack pass does not bind the unposed shared bolster"),
                    MeshPath.Contains(TEXT("Shared_MovingBolster"),
                        ESearchCase::CaseSensitive));
                TestFalse(TEXT("Static-only StagePack pass does not bind the unposed shared die set"),
                    MeshPath.Contains(TEXT("Shared_StageDieSet"),
                        ESearchCase::CaseSensitive));
            }
        }
        if (Component->GetStaticMesh() && Component->GetStaticMesh()->GetPathName()
                == FString(LBOneFactoryPressPresentationTestsPrivate::
                    DetailedMeshPath))
        {
            ++PopulatedDetailedComponentCount;
            TestEqual(TEXT("Active component resolves exact owned v449 mesh"),
                Component->GetStaticMesh()->GetPathName(),
                FString(LBOneFactoryPressPresentationTestsPrivate::
                    DetailedMeshPath));
            TestEqual(TEXT("Detailed aggregate retains exactly 306 slots"),
                Component->GetStaticMesh()->GetStaticMaterials().Num(), 306);
            TSet<FString> ObservedMaterials;
            for (int32 SlotIndex = 0; SlotIndex <
                    Component->GetStaticMesh()->GetStaticMaterials().Num();
                ++SlotIndex)
            {
                const UMaterialInterface* Material =
                    Component->GetStaticMesh()->GetMaterial(SlotIndex);
                if (TestNotNull(TEXT("Every detailed slot resolves a material"),
                        Material))
                {
                    TestTrue(TEXT("Every detailed slot is rebound to owned root"),
                        Material->GetPathName().StartsWith(
                            LBOneFactoryPressPresentationTestsPrivate::
                                DetailedPresentationRoot,
                            ESearchCase::CaseSensitive));
                    ObservedMaterials.Add(Material->GetPathName());
                }
            }
            TestEqual(TEXT("All 13 accepted PBR materials are represented"),
                ObservedMaterials.Num(), 13);
        }
        else if (Component->GetStaticMesh() && Component->GetStaticMesh()->GetPathName()
                == FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawStaticMeshPath))
        {
            ++PopulatedAuthoredS02StaticCount;
            AuthoredS02StaticComponent = const_cast<UStaticMeshComponent*>(Component);
            TestEqual(TEXT("Authored S02 shell has its dedicated presentation component"),
                Component->GetFName(), FName(TEXT("S02DeepDrawPresentation")));
            TestTrue(TEXT("Authored S02 shell retains imported centimetre-scale bounds"),
                (Component->GetStaticMesh()->GetBounds().BoxExtent * 2.0f)
                    .Equals(FVector(657.0f, 663.09f, 815.06f), 3.0f));
            TestTrue(TEXT("Authored S02 shell retains operator and safety semantics"),
                Component->GetStaticMesh()->GetStaticMaterials().Num() == 10);
            const FName ExpectedStaticSlots[] = {
                FName(TEXT("M_CA_MainGreen")), FName(TEXT("M_CA_Concrete")),
                FName(TEXT("M_CA_DarkSteel")), FName(TEXT("M_CA_CleanSteel")),
                FName(TEXT("M_CA_CharcoalGrey")), FName(TEXT("M_CA_SafetyYellow")),
                FName(TEXT("M_CA_ScreenDark")), FName(TEXT("M_CA_LampGreen")),
                FName(TEXT("M_CA_LampAmber")), FName(TEXT("M_CA_LampRed")) };
            for (int32 SlotIndex = 0; SlotIndex < UE_ARRAY_COUNT(ExpectedStaticSlots);
                ++SlotIndex)
            {
                TestEqual(TEXT("Authored S02 static slot order matches the v003 receipt"),
                    Component->GetStaticMesh()->GetStaticMaterials()[SlotIndex]
                        .MaterialSlotName, ExpectedStaticSlots[SlotIndex]);
                const UMaterialInterface* Material = Component->GetMaterial(SlotIndex);
                TestTrue(TEXT("Authored S02 static material is rebound to the owned native material root"),
                    Material && Material->GetPathName().StartsWith(
                        LBOneFactoryPressPresentationTestsPrivate::
                            DetailedPresentationRoot,
                        ESearchCase::CaseSensitive));
                TestEqual(TEXT("Authored S02 static material uses its exact v003 PBR instance"),
                    Material ? Material->GetPathName() : FString(),
                    FString(LBOneFactoryPressPresentationTestsPrivate::
                        S02DeepDrawMaterialPaths[SlotIndex]));
            }
        }
        else if (Component->GetStaticMesh() && Component->GetStaticMesh()->GetPathName()
                == FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawRamMeshPath))
        {
            ++PopulatedAuthoredS02RamCount;
            AuthoredS02RamComponent = const_cast<UStaticMeshComponent*>(Component);
            TestEqual(TEXT("Authored S02 ram reuses the existing PressRam_02 motion seam"),
                Component->GetFName(), FName(TEXT("PressRam_02")));
            TestTrue(TEXT("Authored S02 ram retains imported centimetre-scale bounds"),
                (Component->GetStaticMesh()->GetBounds().BoxExtent * 2.0f)
                    .Equals(FVector(222.0f, 180.0f, 188.0f), 3.0f));
            const UMaterialInterface* Material = Component->GetMaterial(0);
            TestTrue(TEXT("Authored S02 ram uses a rebound owned steel material"),
                Material && Material->GetPathName().StartsWith(
                    LBOneFactoryPressPresentationTestsPrivate::
                        DetailedPresentationRoot,
                    ESearchCase::CaseSensitive));
            TestEqual(TEXT("Authored S02 ram uses its exact v003 PBR instance"),
                Material ? Material->GetPathName() : FString(),
                FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawMaterialPaths[10]));
        }
        else if (Component->GetStaticMesh() && Component->GetStaticMesh()->GetPathName()
                == FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawBlankholderMeshPath))
        {
            ++PopulatedAuthoredS02BlankholderCount;
            AuthoredS02BlankholderComponent = const_cast<UStaticMeshComponent*>(Component);
            TestEqual(TEXT("Authored S02 blankholder has its dedicated source component"),
                Component->GetFName(), FName(TEXT("S02DeepDrawBlankholderPresentation")));
            TestTrue(TEXT("Authored S02 blankholder retains imported centimetre-scale bounds"),
                (Component->GetStaticMesh()->GetBounds().BoxExtent * 2.0f)
                    .Equals(FVector(190.0f, 155.0f, 12.0f), 3.0f));
            const UMaterialInterface* Material = Component->GetMaterial(0);
            TestTrue(TEXT("Authored S02 blankholder uses a rebound owned steel material"),
                Material && Material->GetPathName().StartsWith(
                    LBOneFactoryPressPresentationTestsPrivate::
                        DetailedPresentationRoot,
                    ESearchCase::CaseSensitive));
            TestEqual(TEXT("Authored S02 blankholder uses its exact v003 PBR instance"),
                Material ? Material->GetPathName() : FString(),
                FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawMaterialPaths[11]));
        }
        else if (Component->GetStaticMesh() && Component->GetStaticMesh()->GetPathName()
                == FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawBolsterMeshPath))
        {
            ++PopulatedAuthoredS02BolsterCount;
            AuthoredS02BolsterComponent = const_cast<UStaticMeshComponent*>(Component);
            TestEqual(TEXT("Authored S02 bolster has its dedicated source component"),
                Component->GetFName(), FName(TEXT("S02DeepDrawBolsterPresentation")));
            TestTrue(TEXT("Authored S02 bolster retains imported centimetre-scale bounds"),
                (Component->GetStaticMesh()->GetBounds().BoxExtent * 2.0f)
                    .Equals(FVector(210.0f, 200.0f, 36.0f), 3.0f));
            const UMaterialInterface* Material = Component->GetMaterial(0);
            TestTrue(TEXT("Authored S02 bolster uses a rebound owned steel material"),
                Material && Material->GetPathName().StartsWith(
                    LBOneFactoryPressPresentationTestsPrivate::
                        DetailedPresentationRoot,
                    ESearchCase::CaseSensitive));
            TestEqual(TEXT("Authored S02 bolster uses its exact v003 PBR instance"),
                Material ? Material->GetPathName() : FString(),
                FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawMaterialPaths[12]));
        }
        else if (Component->GetStaticMesh() && Component->GetStaticMesh()->GetPathName()
                == FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawFlywheelMeshPath))
        {
            ++PopulatedAuthoredS02FlywheelCount;
            AuthoredS02FlywheelComponent = const_cast<UStaticMeshComponent*>(Component);
            TestEqual(TEXT("Authored S02 flywheel has its dedicated source component"),
                Component->GetFName(), FName(TEXT("S02DeepDrawFlywheelPresentation")));
            TestTrue(TEXT("Authored S02 flywheel retains imported centimetre-scale bounds"),
                (Component->GetStaticMesh()->GetBounds().BoxExtent * 2.0f)
                    .Equals(FVector(194.0f, 43.0f, 194.0f), 3.0f));
            const UMaterialInterface* Material = Component->GetMaterial(0);
            TestTrue(TEXT("Authored S02 flywheel uses a rebound owned steel material"),
                Material && Material->GetPathName().StartsWith(
                    LBOneFactoryPressPresentationTestsPrivate::
                        DetailedPresentationRoot,
                    ESearchCase::CaseSensitive));
            TestEqual(TEXT("Authored S02 flywheel uses its exact v003 PBR instance"),
                Material ? Material->GetPathName() : FString(),
                FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawMaterialPaths[13]));
        }
        else if (Component->GetStaticMesh() && Component->GetStaticMesh()->GetPathName()
                == FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawSafetyGateMeshPath))
        {
            ++PopulatedAuthoredS02SafetyGateCount;
            AuthoredS02SafetyGateComponent = const_cast<UStaticMeshComponent*>(Component);
            TestEqual(TEXT("Authored S02 safety gate has its dedicated source component"),
                Component->GetFName(), FName(TEXT("S02DeepDrawSafetyGatePresentation")));
            TestTrue(TEXT("Authored S02 safety gate retains imported centimetre-scale bounds"),
                (Component->GetStaticMesh()->GetBounds().BoxExtent * 2.0f)
                    .Equals(FVector(92.0f, 11.5f, 160.0f), 3.0f));
            const UMaterialInterface* Material = Component->GetMaterial(0);
            TestTrue(TEXT("Authored S02 safety gate uses its rebound owned yellow material"),
                Material && Material->GetPathName().StartsWith(
                    LBOneFactoryPressPresentationTestsPrivate::
                        DetailedPresentationRoot,
                    ESearchCase::CaseSensitive));
            TestEqual(TEXT("Authored S02 safety gate uses its exact v003 PBR instance"),
                Material ? Material->GetPathName() : FString(),
                FString(LBOneFactoryPressPresentationTestsPrivate::
                    S02DeepDrawMaterialPaths[14]));
        }
        else if (Component->GetStaticMesh())
        {
            using namespace LBOneFactoryPressPresentationTestsPrivate;
            const FString MeshPath = Component->GetStaticMesh()->GetPathName();
            const int32 FrameIndex = FindS03S06StagePackMeshIndex(MeshPath,
                S03S06StagePackFrameMeshPaths,
                UE_ARRAY_COUNT(S03S06StagePackFrameMeshPaths));
            const int32 CueIndex = FindS03S06StagePackMeshIndex(MeshPath,
                S03S06StagePackCueMeshPaths,
                UE_ARRAY_COUNT(S03S06StagePackCueMeshPaths));
            const int32 MaterialFlowIndex = FindS03S06StagePackMeshIndex(MeshPath,
                MaterialFlowMeshPaths, UE_ARRAY_COUNT(MaterialFlowMeshPaths));
            if (MaterialFlowIndex != INDEX_NONE)
            {
                ++PopulatedMaterialFlowCount;
                MaterialFlowComponents[MaterialFlowIndex] = Component;
                VerifyMaterialFlowComponent(Component, MaterialFlowIndex);
            }
            else if (FrameIndex != INDEX_NONE)
            {
                ++PopulatedStagePackFrameCount;
                StagePackFrameComponents[FrameIndex] = Component;
                VerifyStagePackComponent(Component, FrameIndex, true);
            }
            else if (CueIndex != INDEX_NONE)
            {
                ++PopulatedStagePackCueCount;
                StagePackCueComponents[CueIndex] = Component;
                VerifyStagePackComponent(Component, CueIndex, false);
            }
            else if (Component->GetFName().ToString().StartsWith(TEXT("Native")))
            {
                ++PopulatedNativeStructuralComponentCount;
                TestEqual(TEXT("Native station batch uses Unreal's native primitive"),
                    Component->GetStaticMesh()->GetPathName(),
                    FString(TEXT("/Engine/BasicShapes/Cube.Cube")));
                if (const UInstancedStaticMeshComponent* NativeBatch =
                        Cast<UInstancedStaticMeshComponent>(Component))
                {
                    if (Component->GetFName() == TEXT("NativeStationBases"))
                        NativeStationBaseInstances = NativeBatch->GetInstanceCount();
                    else if (Component->GetFName() == TEXT("NativeStationCrowns"))
                        NativeStationCrownInstances = NativeBatch->GetInstanceCount();
                }
            }
            else
            {
                ++PopulatedMotionComponentCount;
                TestEqual(TEXT("Moving mechanism uses Unreal's native primitive"),
                    Component->GetStaticMesh()->GetPathName(),
                    FString(TEXT("/Engine/BasicShapes/Cube.Cube")));
            }
        }
    }
    TestEqual(TEXT("Only one double buffer is populated after commit"),
        PopulatedDetailedComponentCount, 1);
    TestEqual(TEXT("Exactly one authored S02 static shell is populated after commit"),
        PopulatedAuthoredS02StaticCount, 1);
    TestEqual(TEXT("Exactly one authored S02 ram is populated after commit"),
        PopulatedAuthoredS02RamCount, 1);
    TestEqual(TEXT("Exactly one authored S02 blankholder is populated after commit"),
        PopulatedAuthoredS02BlankholderCount, 1);
    TestEqual(TEXT("Exactly one authored S02 bolster is populated after commit"),
        PopulatedAuthoredS02BolsterCount, 1);
    TestEqual(TEXT("Exactly one authored S02 flywheel is populated after commit"),
        PopulatedAuthoredS02FlywheelCount, 1);
    TestEqual(TEXT("Exactly one authored S02 safety gate is populated after commit"),
        PopulatedAuthoredS02SafetyGateCount, 1);
    TestEqual(TEXT("All four authored static StagePack frames are populated after commit"),
        PopulatedStagePackFrameCount, 4);
    TestEqual(TEXT("All four authored static StagePack operator-side cues are populated after commit"),
        PopulatedStagePackCueCount, 4);
    TestEqual(TEXT("All ten native MaterialFlow endpoint meshes are populated after commit"),
        PopulatedMaterialFlowCount, 10);
    TestEqual(TEXT("Ten native structural batches are populated after commit"),
        PopulatedNativeStructuralComponentCount, 10);
    TestEqual(TEXT("Ten non-S02 motion seams retain the native primitive"),
        PopulatedMotionComponentCount, 10);
    TestEqual(TEXT("Generic S01-S07 bases are omitted when all authored station bundles are present"),
        NativeStationBaseInstances, 0);
    TestEqual(TEXT("Generic S01-S07 crowns are omitted when authored endpoints and press bundles are present"),
        NativeStationCrownInstances, 0);

    UStaticMeshComponent* FirstCommittedComponent =
        LBOneFactoryPressPresentationTestsPrivate::
            FindActiveDetailedComponent(*Presentation);
    TestNotNull(TEXT("Exactly one detailed component is active"),
        FirstCommittedComponent);

    const FLBOneFactoryPressStarterLayoutState FirstCommittedLayout =
        Authority->CaptureLayout();
    const FLBOneFactoryPressStarterStationState* PressStation =
        LBOneFactoryPressPresentationTestsPrivate::FindStation(
            FirstCommittedLayout,
            ELBOneFactoryPressStarterRole::ConfigurablePressTrain);
    if (TestNotNull(TEXT("Configurable Press train anchor exists"), PressStation)
        && FirstCommittedComponent)
    {
        const FTransform LocalAggregateTransform(FQuat::Identity,
            FVector(9.25f, 2367.5f, 0.0f),
            FVector(100.0f, 100.0f, 100.0f));
        const FTransform ExpectedAggregateTransform =
            LocalAggregateTransform * PressStation->WorldTransform;
        TestTrue(TEXT("Detailed aggregate uses exact datum-relative anchor"),
            FirstCommittedComponent->GetComponentTransform().Equals(
                ExpectedAggregateTransform, 0.01f));

        const FTransform TrainAnchor(FQuat::Identity,
            FVector(9.25f, 2367.5f, 0.0f), FVector::OneVector);
        const FTransform StagePackTrainAnchor = TrainAnchor
            * PressStation->WorldTransform;
        const FTransform S02SourceLocal(FQuat(FRotator(0.0f, 90.0f, 0.0f)),
            FVector(0.0f, -2900.0f, 0.0f), FVector(1.80f));
        const FTransform ExpectedS02Transform = S02SourceLocal * TrainAnchor
            * PressStation->WorldTransform;
        TestTrue(TEXT("Authored S02 shell uses its exact S02 datum and operator-side yaw"),
            AuthoredS02StaticComponent
                && AuthoredS02StaticComponent->GetComponentTransform().Equals(
                    ExpectedS02Transform, 0.01f));
        const auto ExpectedS02ModuleTransform = [&ExpectedS02Transform](
            const FVector& PlacementCm)
        {
            return FTransform(ExpectedS02Transform.GetRotation(),
                ExpectedS02Transform.TransformPosition(PlacementCm),
                ExpectedS02Transform.GetScale3D());
        };
        TestTrue(TEXT("Authored S02 ram begins at its documented pivot placement"),
            AuthoredS02RamComponent
                && AuthoredS02RamComponent->GetComponentTransform().Equals(
                    ExpectedS02ModuleTransform(FVector(0.0f, 0.0f, 377.5f)),
                    0.01f));
        TestTrue(TEXT("Authored S02 blankholder retains its documented pivot placement"),
            AuthoredS02BlankholderComponent
                && AuthoredS02BlankholderComponent->GetComponentTransform().Equals(
                    ExpectedS02ModuleTransform(FVector(0.0f, 0.0f, 208.0f)),
                    0.01f));
        TestTrue(TEXT("Authored S02 bolster retains its documented pivot placement"),
            AuthoredS02BolsterComponent
                && AuthoredS02BolsterComponent->GetComponentTransform().Equals(
                    ExpectedS02ModuleTransform(FVector(0.0f, 0.0f, 158.0f)),
                    0.01f));
        TestTrue(TEXT("Authored S02 flywheel retains its documented pivot placement"),
            AuthoredS02FlywheelComponent
                && AuthoredS02FlywheelComponent->GetComponentTransform().Equals(
                    ExpectedS02ModuleTransform(FVector(-135.0f, -95.0f, 698.0f)),
                    0.01f));
        TestTrue(TEXT("Authored S02 safety gate retains its documented hinge placement"),
            AuthoredS02SafetyGateComponent
                && AuthoredS02SafetyGateComponent->GetComponentTransform().Equals(
                    ExpectedS02ModuleTransform(FVector(105.0f, 245.0f, 110.0f)),
                    0.01f));

        const float StagePackLocalY[] = {
            -1450.0f, 0.0f, 1450.0f, 2900.0f };
        for (int32 Index = 0; Index < UE_ARRAY_COUNT(StagePackLocalY); ++Index)
        {
            const FTransform ExpectedStagePackRoot(
                StagePackTrainAnchor.GetRotation(),
                StagePackTrainAnchor.TransformPosition(FVector(0.0f,
                    StagePackLocalY[Index], 0.0f)), FVector::OneVector);
            const UStaticMeshComponent* Frame = StagePackFrameComponents[Index];
            const UStaticMeshComponent* Cue = StagePackCueComponents[Index];
            TestTrue(TEXT("Static StagePack frame uses its source station root with no baked yaw or scale"),
                Frame && Frame->GetComponentTransform().Equals(
                    ExpectedStagePackRoot, 0.01f));
            TestTrue(TEXT("Static StagePack operator-side cue shares its frame station root"),
                Cue && Cue->GetComponentTransform().Equals(
                    ExpectedStagePackRoot, 0.01f));
            TestTrue(TEXT("Static StagePack frame/cue pair has exactly the same root transform"),
                Frame && Cue && Frame->GetComponentTransform().Equals(
                    Cue->GetComponentTransform(), 0.01f));
            TestTrue(TEXT("Static StagePack frame preserves source scale one"),
                Frame && Frame->GetComponentTransform().GetScale3D().Equals(
                    FVector::OneVector, 0.001f));
            TestTrue(TEXT("Static StagePack cue preserves source scale one"),
                Cue && Cue->GetComponentTransform().GetScale3D().Equals(
                    FVector::OneVector, 0.001f));
        }

        const FTransform ExpectedMaterialFlowS01Root(
            FQuat::Identity, FVector(0.0f, -4350.0f, 0.0f),
            FVector::OneVector);
        const FTransform ExpectedMaterialFlowS07Root(
            FQuat::Identity, FVector(0.0f, 4350.0f, 0.0f),
            FVector::OneVector);
        const FTransform ExpectedS01Root = ExpectedMaterialFlowS01Root
            * TrainAnchor * PressStation->WorldTransform;
        const FTransform ExpectedS07Root = ExpectedMaterialFlowS07Root
            * TrainAnchor * PressStation->WorldTransform;
        for (int32 Index = 0; Index < MaterialFlowComponents.Num(); ++Index)
        {
            const UStaticMeshComponent* Component = MaterialFlowComponents[Index];
            FTransform ExpectedTransform = Index < 6 ? ExpectedS01Root
                : ExpectedS07Root;
            if (Index == 0)
            {
                ExpectedTransform = FTransform(ExpectedS01Root.GetRotation(),
                    ExpectedS01Root.TransformPosition(FVector(220.0f, 430.0f, 32.0f)),
                    ExpectedS01Root.GetScale3D());
            }
            else if (Index == 3)
            {
                ExpectedTransform = FTransform(ExpectedS01Root.GetRotation(),
                    ExpectedS01Root.TransformPosition(FVector(-20.0f, 120.0f, 115.0f)),
                    ExpectedS01Root.GetScale3D());
            }
            TestTrue(TEXT("MaterialFlow mesh preserves its documented station root or mover pivot offset"),
                Component && Component->GetComponentTransform().Equals(
                    ExpectedTransform, 0.01f));
            TestTrue(TEXT("MaterialFlow mesh preserves unit scale with no endpoint reimport scale"),
                Component && Component->GetComponentTransform().GetScale3D().Equals(
                    FVector::OneVector, 0.001f));
        }
    }

    if (AuthoredS02FlywheelComponent)
    {
        AuthoredS02FlywheelComponent->SetVisibility(false, true);
        AuthoredS02FlywheelComponent->SetHiddenInGame(true, true);
        Presentation->Tick(0.0f);
        TestTrue(TEXT("S02 visibility guard restores a drifted flywheel component"),
            AuthoredS02FlywheelComponent->IsVisible());
        TestFalse(TEXT("S02 visibility guard clears a drifted flywheel hidden-in-game state"),
            AuthoredS02FlywheelComponent->bHiddenInGame != 0);
    }
    if (StagePackCueComponents.IsValidIndex(0) && StagePackCueComponents[0])
    {
        UStaticMeshComponent* StagePackCue =
            const_cast<UStaticMeshComponent*>(StagePackCueComponents[0]);
        StagePackCue->SetVisibility(false, true);
        StagePackCue->SetHiddenInGame(true, true);
        Presentation->Tick(0.0f);
        TestTrue(TEXT("StagePack visibility guard restores a drifted S03 cue component"),
            StagePackCue->IsVisible());
        TestFalse(TEXT("StagePack visibility guard clears a drifted S03 cue hidden-in-game state"),
            StagePackCue->bHiddenInGame != 0);
    }
    if (MaterialFlowComponents.IsValidIndex(0) && MaterialFlowComponents[0]
        && MaterialFlowComponents.IsValidIndex(8) && MaterialFlowComponents[8])
    {
        UStaticMeshComponent* CoilCart =
            const_cast<UStaticMeshComponent*>(MaterialFlowComponents[0]);
        UStaticMeshComponent* InspectionCell =
            const_cast<UStaticMeshComponent*>(MaterialFlowComponents[8]);
        const FTransform CoilCartBeforeTick = CoilCart->GetComponentTransform();
        const FTransform InspectionCellBeforeTick =
            InspectionCell->GetComponentTransform();
        CoilCart->SetVisibility(false, true);
        CoilCart->SetHiddenInGame(true, true);
        InspectionCell->SetVisibility(false, true);
        InspectionCell->SetHiddenInGame(true, true);
        Presentation->Tick(0.0f);
        TestTrue(TEXT("MaterialFlow visibility guard restores a drifted S01 mover"),
            CoilCart->IsVisible());
        TestFalse(TEXT("MaterialFlow visibility guard clears a drifted S01 mover hidden-in-game state"),
            CoilCart->bHiddenInGame != 0);
        TestTrue(TEXT("MaterialFlow visibility guard restores a drifted S07 inspection cell"),
            InspectionCell->IsVisible());
        TestFalse(TEXT("MaterialFlow visibility guard clears a drifted S07 inspection cell hidden-in-game state"),
            InspectionCell->bHiddenInGame != 0);
        TestTrue(TEXT("MaterialFlow coil cart remains parked outside the unproven animation array"),
            CoilCart->GetComponentTransform().Equals(CoilCartBeforeTick, 0.001f));
        TestTrue(TEXT("MaterialFlow inspection cell remains stationary through presentation tick"),
            InspectionCell->GetComponentTransform().Equals(
                InspectionCellBeforeTick, 0.001f));
    }

    const FLBOneFactoryPressStarterLayoutState BeforeMove =
        Authority->CaptureLayout();
    const FLBOneFactoryPressStarterStationState* Inspection =
        BeforeMove.Stations.FindByPredicate([](
            const FLBOneFactoryPressStarterStationState& Station)
        {
            return Station.StationId ==
                LBOneFactoryPressStarterIds::PanelInspection();
        });
    if (TestNotNull(TEXT("Inspection station exists"), Inspection))
    {
        FTransform Moved = Inspection->WorldTransform;
        Moved.AddToTranslation(FVector(100.0f, 0.0f, 0.0f));
        TestTrue(TEXT("Authority accepts a coherent small station move"),
            Authority->MoveStation(
                LBOneFactoryPressStarterIds::PanelInspection(), Moved, Reason));
        TestTrue(TEXT("Presentation rebinds to the moved authority snapshot"),
            Presentation->ConfigureFromLayout(Authority->CaptureLayout(), Reason));
        FTransform Bound;
        TestTrue(TEXT("Stable station-ID lookup survives the rebind"),
            Presentation->GetConfiguredStationTransform(
                LBOneFactoryPressStarterIds::PanelInspection(), Bound));
        TestTrue(TEXT("Lookup reports the exact moved transform"),
            Bound.Equals(Moved, 0.001f));
    }

    UStaticMeshComponent* SecondCommittedComponent =
        LBOneFactoryPressPresentationTestsPrivate::
            FindActiveDetailedComponent(*Presentation);
    TestNotNull(TEXT("Rebind leaves exactly one detailed component active"),
        SecondCommittedComponent);
    TestTrue(TEXT("Successful rebind commits through the inactive buffer"),
        FirstCommittedComponent && SecondCommittedComponent
            && FirstCommittedComponent != SecondCommittedComponent);

    const FName CommittedLayoutId = Presentation->GetConfiguredLayoutId();
    const int32 CommittedRevision =
        Presentation->GetConfiguredLayoutRevision();
    FTransform CommittedInspectionTransform;
    const bool bHadCommittedInspection =
        Presentation->GetConfiguredStationTransform(
            LBOneFactoryPressStarterIds::PanelInspection(),
            CommittedInspectionTransform);
    const FTransform CommittedAggregateTransform = SecondCommittedComponent
        ? SecondCommittedComponent->GetComponentTransform()
        : FTransform::Identity;

    FLBOneFactoryPressStarterLayoutState Invalid = Authority->CaptureLayout();
    Invalid.Stations[1].StationId = Invalid.Stations[0].StationId;
    TestFalse(TEXT("Invalid authority data fails closed"),
        Presentation->ConfigureFromLayout(Invalid, Reason));
    TestTrue(TEXT("Failed reconfigure preserves committed visual state"),
        Presentation->IsPresentationConfigured());
    TestEqual(TEXT("Failed reconfigure preserves the seven station bodies"),
        Presentation->GetVisibleInstanceCount(), 7);
    TestEqual(TEXT("Failed reconfigure preserves authored S02, static StagePack, MaterialFlow, and native batches"),
        Presentation->GetVisualBatchCount(), 17);
    TestEqual(TEXT("Failed reconfigure preserves committed layout identity"),
        Presentation->GetConfiguredLayoutId(), CommittedLayoutId);
    TestEqual(TEXT("Failed reconfigure preserves committed revision"),
        Presentation->GetConfiguredLayoutRevision(), CommittedRevision);
    UStaticMeshComponent* AfterFailedComponent =
        LBOneFactoryPressPresentationTestsPrivate::
            FindActiveDetailedComponent(*Presentation);
    TestTrue(TEXT("Failed reconfigure preserves exact committed buffer"),
        AfterFailedComponent && AfterFailedComponent == SecondCommittedComponent);
    TestTrue(TEXT("Failed reconfigure preserves exact aggregate transform"),
        AfterFailedComponent
            && AfterFailedComponent->GetComponentTransform().Equals(
                CommittedAggregateTransform, 0.001f));
    FTransform AfterFailureInspectionTransform;
    TestTrue(TEXT("Failed reconfigure preserves station-transform snapshot"),
        bHadCommittedInspection
            && Presentation->GetConfiguredStationTransform(
                LBOneFactoryPressStarterIds::PanelInspection(),
                AfterFailureInspectionTransform)
            && AfterFailureInspectionTransform.Equals(
                CommittedInspectionTransform, 0.001f));

    Presentation->ClearPresentation();
    TestEqual(TEXT("Repeated clear is idempotently empty"),
        Presentation->GetVisibleInstanceCount(), 0);
    TestEqual(TEXT("Clear removes the visual batch"),
        Presentation->GetVisualBatchCount(), 0);
    TestEqual(TEXT("Clear releases all animated mechanisms"),
        Presentation->GetAnimatedMechanismCount(), 0);
    TestEqual(TEXT("Clear removes cached layout identity"),
        Presentation->GetConfiguredLayoutId(), NAME_None);
    for (const UStaticMeshComponent* Component : DetailedComponents)
    {
        if (Component && Component->GetFName().ToString().StartsWith(
                TEXT("DetailedPresentation")))
        {
            TestNull(TEXT("Clear releases both hidden aggregate staging buffers"),
                Component->GetStaticMesh());
        }
        if (Component && Component->GetFName().ToString().StartsWith(
                TEXT("S02DeepDraw")))
        {
            TestNull(TEXT("Clear releases every authored non-Ram S02 runtime module"),
                Component->GetStaticMesh());
        }
        if (Component && Component->GetFName().ToString().Contains(
                TEXT("StagePack"), ESearchCase::CaseSensitive))
        {
            TestNull(TEXT("Clear releases every authored static S03-S06 StagePack module"),
                Component->GetStaticMesh());
        }
        if (Component && Component->GetFName() == TEXT("PressRam_02"))
        {
            TestNull(TEXT("Clear releases the authored S02 Ram motion module"),
                Component->GetStaticMesh());
        }
        if (Component)
        {
            for (const FName& MaterialFlowName :
                LBOneFactoryPressPresentationTestsPrivate::MaterialFlowComponentNames)
            {
                if (Component->GetFName() != MaterialFlowName) continue;
                TestNull(TEXT("Clear releases every native MaterialFlow endpoint module"),
                    Component->GetStaticMesh());
                TestEqual(TEXT("Clear leaves no MaterialFlow component material override"),
                    Component->GetNumMaterials(), 0);
            }
        }
    }
    TestFalse(TEXT("Invalid first configure remains atomically empty"),
        Presentation->ConfigureFromLayout(Invalid, Reason));
    TestFalse(TEXT("Failed first configure has no committed state"),
        Presentation->IsPresentationConfigured());
    TestEqual(TEXT("Failed first configure has zero rendered aggregates"),
        Presentation->GetVisibleInstanceCount(), 0);
    World->DestroyWorld(false);
    return true;
}

#endif
