#pragma once

#include "CoreMinimal.h"

enum class ELBPanelHandedness : uint8
{
    None,
    Left,
    Right
};

/** Stable gameplay definition for one stamped closure/body-side panel family. */
struct FLBStampedPanelDefinition
{
    FName PanelTypeId = NAME_None;
    FString DisplayName;
    ELBPanelHandedness Handedness = ELBPanelHandedness::None;
    /** Number of like panels carried by one production WIP stillage. */
    int32 StillageCapacity = 1;
    /** Honest placeholder envelope until the registered Meshy derivative is imported. */
    FVector NominalSizeCm = FVector::ZeroVector;
    /** Optional opposite-hand authority used to build a controlled mirrored derivative. */
    FName MirrorAuthorityPanelTypeId = NAME_None;
};

namespace LBCairnwell2040PanelCatalog
{
    LINEBOSSCARFACTORY_API FName GetVehicleModelId();
    LINEBOSSCARFACTORY_API const TArray<FLBStampedPanelDefinition>& GetDefinitions();
    LINEBOSSCARFACTORY_API const FLBStampedPanelDefinition* Find(FName VehicleModelId, FName PanelTypeId);
    LINEBOSSCARFACTORY_API bool IsApprovedStampedRecipe(FName VehicleModelId, FName PanelTypeId);

    /** Parses the press authority ID: PT?-PANEL-<vehicle>-<panel>-<serial>. */
    LINEBOSSCARFACTORY_API bool ParsePressedPanelUnitId(FName UnitId,
        FName& OutVehicleModelId, FName& OutPanelTypeId);
}
