#pragma once

#include "CoreMinimal.h"

class UStaticMesh;
class UStaticMeshComponent;

/** Frozen semantic presentation definition for the isolated Body Shop v002 pack. */
struct FLBBodyShopPresentationPaletteSpec
{
    FLinearColor BaseColour = FLinearColor::White;
    float Metallic = 0.0f;
    float Roughness = 0.5f;
    float RoughnessVariation = 0.0f;
    FLinearColor EmissiveColour = FLinearColor::Black;
    float EmissiveStrength = 0.0f;
    bool bUsesLayeredPaint = false;
};

/**
 * Component-only semantic binding for the isolated Body Shop presentation pack.
 * ApplyToComponent is atomic: an unknown slot or missing MIC applies nothing.
 */
namespace LBBodyShopPresentationPalette
{
    LINEBOSSCARFACTORY_API const TCHAR* GetMaterialRootPath();
    LINEBOSSCARFACTORY_API const TCHAR* GetLayeredMasterMaterialPath();
    LINEBOSSCARFACTORY_API const TCHAR* GetFunctionalMasterMaterialPath();
    LINEBOSSCARFACTORY_API const TCHAR* GetMaterialPath(FName SemanticSlotName);
    LINEBOSSCARFACTORY_API int32 GetSupportedSemanticSlotCount();

    LINEBOSSCARFACTORY_API bool FindSpec(FName SemanticSlotName,
        FLBBodyShopPresentationPaletteSpec& OutSpec);

    LINEBOSSCARFACTORY_API int32 CountSupportedSlots(const UStaticMesh* Mesh);

    /** Returns the exact slot count on success, or zero without partial overrides. */
    LINEBOSSCARFACTORY_API int32 ApplyToComponent(UStaticMeshComponent* Component);
}
