#include "LBVehiclePanelCatalog.h"

namespace
{
    const FName Cairnwell2040Id(TEXT("CAIRNWELL_2040"));

    const TArray<FLBStampedPanelDefinition> Cairnwell2040Panels =
    {
        { TEXT("HOOD_PANEL"), TEXT("Hood outer"), ELBPanelHandedness::None,
            16, FVector(165.0f, 145.0f, 24.0f), NAME_None },
        { TEXT("ROOF_PANEL"), TEXT("Roof outer"), ELBPanelHandedness::None,
            12, FVector(205.0f, 150.0f, 20.0f), NAME_None },
        { TEXT("DOOR_FRONT_LEFT"), TEXT("Front door left"), ELBPanelHandedness::Left,
            20, FVector(125.0f, 18.0f, 115.0f), NAME_None },
        { TEXT("DOOR_FRONT_RIGHT"), TEXT("Front door right"), ELBPanelHandedness::Right,
            20, FVector(125.0f, 18.0f, 115.0f), TEXT("DOOR_FRONT_LEFT") },
        { TEXT("DOOR_REAR_LEFT"), TEXT("Rear door left"), ELBPanelHandedness::Left,
            20, FVector(110.0f, 18.0f, 112.0f), NAME_None },
        { TEXT("DOOR_REAR_RIGHT"), TEXT("Rear door right"), ELBPanelHandedness::Right,
            20, FVector(110.0f, 18.0f, 112.0f), NAME_None },
        { TEXT("FENDER_FRONT_LEFT"), TEXT("Front fender left"), ELBPanelHandedness::Left,
            24, FVector(118.0f, 42.0f, 92.0f), NAME_None },
        { TEXT("FENDER_FRONT_RIGHT"), TEXT("Front fender right"), ELBPanelHandedness::Right,
            24, FVector(118.0f, 42.0f, 92.0f), TEXT("FENDER_FRONT_LEFT") },
        { TEXT("QUARTER_PANEL_LEFT"), TEXT("Quarter panel left"), ELBPanelHandedness::Left,
            12, FVector(175.0f, 42.0f, 118.0f), NAME_None },
        { TEXT("QUARTER_PANEL_RIGHT"), TEXT("Quarter panel right"), ELBPanelHandedness::Right,
            12, FVector(175.0f, 42.0f, 118.0f), NAME_None },
        { TEXT("TAILGATE_PANEL"), TEXT("Tailgate outer"), ELBPanelHandedness::None,
            14, FVector(145.0f, 22.0f, 108.0f), NAME_None }
    };
}

FName LBCairnwell2040PanelCatalog::GetVehicleModelId()
{
    return Cairnwell2040Id;
}

const TArray<FLBStampedPanelDefinition>& LBCairnwell2040PanelCatalog::GetDefinitions()
{
    return Cairnwell2040Panels;
}

const FLBStampedPanelDefinition* LBCairnwell2040PanelCatalog::Find(
    const FName VehicleModelId, const FName PanelTypeId)
{
    if (VehicleModelId != Cairnwell2040Id || PanelTypeId.IsNone()) return nullptr;
    return Cairnwell2040Panels.FindByPredicate([PanelTypeId](const FLBStampedPanelDefinition& Definition)
    {
        return Definition.PanelTypeId == PanelTypeId;
    });
}

bool LBCairnwell2040PanelCatalog::IsApprovedStampedRecipe(
    const FName VehicleModelId, const FName PanelTypeId)
{
    return Find(VehicleModelId, PanelTypeId) != nullptr;
}

bool LBCairnwell2040PanelCatalog::ParsePressedPanelUnitId(const FName UnitId,
    FName& OutVehicleModelId, FName& OutPanelTypeId)
{
    OutVehicleModelId = NAME_None;
    OutPanelTypeId = NAME_None;
    if (UnitId.IsNone()) return false;

    FString Payload;
    if (!UnitId.ToString().Split(TEXT("-PANEL-"), nullptr, &Payload)
        || Payload.IsEmpty()) return false;

    FString WithoutSerial;
    FString Serial;
    if (!Payload.Split(TEXT("-"), &WithoutSerial, &Serial, ESearchCase::CaseSensitive,
        ESearchDir::FromEnd) || WithoutSerial.IsEmpty() || !Serial.IsNumeric()) return false;

    FString Vehicle;
    FString Panel;
    if (!WithoutSerial.Split(TEXT("-"), &Vehicle, &Panel) || Vehicle.IsEmpty() || Panel.IsEmpty())
        return false;

    OutVehicleModelId = FName(*Vehicle);
    OutPanelTypeId = FName(*Panel);
    return Find(OutVehicleModelId, OutPanelTypeId) != nullptr;
}
