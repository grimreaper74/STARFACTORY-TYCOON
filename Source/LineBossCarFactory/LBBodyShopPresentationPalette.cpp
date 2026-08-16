#include "LBBodyShopPresentationPalette.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "UObject/UObjectGlobals.h"

namespace
{
    constexpr const TCHAR* MaterialRoot =
        TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002");
    constexpr const TCHAR* LayeredMasterPath =
        TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/M_LB_BodyShop_LayeredPaint_Master_v002.M_LB_BodyShop_LayeredPaint_Master_v002");
    constexpr const TCHAR* FunctionalMasterPath =
        TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/M_LB_BodyShop_Functional_Master_v002.M_LB_BodyShop_Functional_Master_v002");

    struct FLBPaletteRow
    {
        const TCHAR* SlotName;
        const TCHAR* MaterialPath;
        FLBBodyShopPresentationPaletteSpec Spec;
    };

    const FLBPaletteRow PaletteRows[] = {
        {TEXT("M_LB_BS_CreamPaint"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_CreamPaint_v002.MI_LB_BodyShop_CreamPaint_v002"),
            {FLinearColor(0.637596874f, 0.571124829f, 0.381326011f), 0.18f, 0.54f,
                0.28f, FLinearColor::Black, 0.0f, true}},
        {TEXT("M_LB_BS_BlackMotor"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_BlackMotor_v002.MI_LB_BodyShop_BlackMotor_v002"),
            {FLinearColor(0.014443844f, 0.017641954f, 0.021219010f), 0.25f, 0.56f,
                0.28f, FLinearColor::Black, 0.0f, true}},
        {TEXT("M_LB_BS_StructuralLightGrey"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_StructuralLightGrey_v002.MI_LB_BodyShop_StructuralLightGrey_v002"),
            {FLinearColor(0.318546778f, 0.391572478f, 0.450785783f), 0.65f, 0.32f,
                0.035f, FLinearColor::Black, 0.0f, false}},
        {TEXT("M_LB_BS_BrushedSteel"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_BrushedSteel_v002.MI_LB_BodyShop_BrushedSteel_v002"),
            {FLinearColor(0.147027266f, 0.194617830f, 0.234550582f), 0.82f, 0.27f,
                0.045f, FLinearColor::Black, 0.0f, false}},
        {TEXT("M_LB_BS_GraphiteTooling"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_GraphiteTooling_v002.MI_LB_BodyShop_GraphiteTooling_v002"),
            {FLinearColor(0.010960094f, 0.018500220f, 0.024157632f), 0.62f, 0.34f,
                0.030f, FLinearColor::Black, 0.0f, false}},
        {TEXT("M_LB_BS_EmeraldPanel"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_EmeraldPanel_v002.MI_LB_BodyShop_EmeraldPanel_v002"),
            {FLinearColor(0.003035270f, 0.194617830f, 0.086500462f), 0.28f, 0.34f,
                0.025f, FLinearColor::Black, 0.0f, false}},
        {TEXT("M_LB_BS_SafetyYellow"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_SafetyYellow_v002.MI_LB_BodyShop_SafetyYellow_v002"),
            {FLinearColor(0.887923118f, 0.396755231f, 0.0f), 0.22f, 0.36f,
                0.025f, FLinearColor::Black, 0.0f, false}},
        {TEXT("M_LB_BS_VacuumRubber"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_VacuumRubber_v002.MI_LB_BodyShop_VacuumRubber_v002"),
            {FLinearColor(0.003346536f, 0.004776953f, 0.006048833f), 0.02f, 0.74f,
                0.018f, FLinearColor::Black, 0.0f, false}},
        {TEXT("M_LB_BS_ScannerLens"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_ScannerLens_v002.MI_LB_BodyShop_ScannerLens_v002"),
            {FLinearColor(0.002731743f, 0.144128471f, 0.262250658f), 0.15f, 0.22f,
                0.015f, FLinearColor(0.0f, 0.35f, 0.65f), 0.22f, false}},
        {TEXT("M_LB_BS_StatusGreen"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_StatusGreen_v002.MI_LB_BodyShop_StatusGreen_v002"),
            {FLinearColor(0.015996293f, 0.644479682f, 0.212230757f), 0.05f, 0.24f,
                0.010f, FLinearColor(0.015996293f, 0.644479682f, 0.212230757f), 3.0f, false}},
        {TEXT("M_LB_BS_StatusAmber"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_StatusAmber_v002.MI_LB_BodyShop_StatusAmber_v002"),
            {FLinearColor(1.0f, 0.337163615f, 0.009721217f), 0.05f, 0.24f,
                0.010f, FLinearColor(1.0f, 0.337163615f, 0.009721217f), 3.0f, false}},
        {TEXT("M_LB_BS_StatusRed"),
            TEXT("/Game/LineBoss/BodyShop/Experimental/v001/Presentation/Materials_v002/MI_LB_BodyShop_StatusRed_v002.MI_LB_BodyShop_StatusRed_v002"),
            {FLinearColor(0.745404210f, 0.026241222f, 0.048171824f), 0.05f, 0.24f,
                0.010f, FLinearColor(0.745404210f, 0.026241222f, 0.048171824f), 3.0f, false}}
    };

    const FLBPaletteRow* FindRow(const FName SemanticSlotName)
    {
        for (const FLBPaletteRow& Row : PaletteRows)
        {
            if (SemanticSlotName == FName(Row.SlotName)) return &Row;
        }
        return nullptr;
    }
}

const TCHAR* LBBodyShopPresentationPalette::GetMaterialRootPath()
{
    return MaterialRoot;
}

const TCHAR* LBBodyShopPresentationPalette::GetLayeredMasterMaterialPath()
{
    return LayeredMasterPath;
}

const TCHAR* LBBodyShopPresentationPalette::GetFunctionalMasterMaterialPath()
{
    return FunctionalMasterPath;
}

const TCHAR* LBBodyShopPresentationPalette::GetMaterialPath(const FName SemanticSlotName)
{
    const FLBPaletteRow* Row = FindRow(SemanticSlotName);
    return Row ? Row->MaterialPath : nullptr;
}

int32 LBBodyShopPresentationPalette::GetSupportedSemanticSlotCount()
{
    return UE_ARRAY_COUNT(PaletteRows);
}

bool LBBodyShopPresentationPalette::FindSpec(const FName SemanticSlotName,
    FLBBodyShopPresentationPaletteSpec& OutSpec)
{
    const FLBPaletteRow* Row = FindRow(SemanticSlotName);
    if (!Row) return false;
    OutSpec = Row->Spec;
    return true;
}

int32 LBBodyShopPresentationPalette::CountSupportedSlots(const UStaticMesh* Mesh)
{
    if (!Mesh) return 0;
    int32 Count = 0;
    for (const FStaticMaterial& Slot : Mesh->GetStaticMaterials())
    {
        if (FindRow(Slot.MaterialSlotName)) ++Count;
    }
    return Count;
}

int32 LBBodyShopPresentationPalette::ApplyToComponent(UStaticMeshComponent* Component)
{
    UStaticMesh* Mesh = Component ? Component->GetStaticMesh() : nullptr;
    if (!Mesh) return 0;

    const TArray<FStaticMaterial>& Slots = Mesh->GetStaticMaterials();
    if (Slots.IsEmpty()) return 0;
    TArray<UMaterialInterface*> ResolvedMaterials;
    ResolvedMaterials.Reserve(Slots.Num());
    for (const FStaticMaterial& Slot : Slots)
    {
        const FLBPaletteRow* Row = FindRow(Slot.MaterialSlotName);
        if (!Row) return 0;
        UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, Row->MaterialPath);
        if (!Material) return 0;
        ResolvedMaterials.Add(Material);
    }

    for (int32 SlotIndex = 0; SlotIndex < ResolvedMaterials.Num(); ++SlotIndex)
    {
        Component->SetMaterial(SlotIndex, ResolvedMaterials[SlotIndex]);
    }
    return ResolvedMaterials.Num();
}
