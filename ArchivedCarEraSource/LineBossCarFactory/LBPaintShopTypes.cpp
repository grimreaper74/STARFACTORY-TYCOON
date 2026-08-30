#include "LBPaintShopTypes.h"

const FName LBPaintShopCellIds::BIWLoadDock(TEXT("PAINT_BIW_LOAD_DOCK"));
const FName LBPaintShopCellIds::PhosphateDipCell(TEXT("PAINT_PHOSPHATE_DIP_CELL"));
const FName LBPaintShopCellIds::EDCoatDipCell(TEXT("PAINT_ED_COAT_DIP_CELL"));
const FName LBPaintShopCellIds::DrainInspectionCell(TEXT("PAINT_DRAIN_INSPECTION_CELL"));
const FName LBPaintShopCellIds::EDCureOvenCell(TEXT("PAINT_ED_CURE_OVEN_CELL"));
const FName LBPaintShopCellIds::EDOutputBuffer(TEXT("PAINT_ED_OUTPUT_BUFFER"));

const FName LBPaintShopWIPIds::BIWComplete(TEXT("BIW_COMPLETE"));
const FName LBPaintShopWIPIds::BIWEDCoated(TEXT("BIW_ED_COATED"));
const FName LBPaintShopWIPIds::BIWCuredEDCoat(TEXT("BIW_CURED_ED_COAT"));

const FName LBPaintShopRecipeIds::PhosphateV001(TEXT("RECIPE_PHOSPHATE_V001"));
const FName LBPaintShopRecipeIds::EDCoatV001(TEXT("RECIPE_ED_COAT_V001"));
const FName LBPaintShopRecipeIds::EDCureV001(TEXT("RECIPE_ED_CURE_V001"));

const FName LBPaintShopQualityIds::PhosphateCoverage(TEXT("QC_PHOSPHATE_COVERAGE"));
const FName LBPaintShopQualityIds::EDFilmBuild(TEXT("QC_ED_FILM_BUILD"));
const FName LBPaintShopQualityIds::EDCure(TEXT("QC_ED_CURE"));

const FName LBPaintShopPortIds::CarrierIn(TEXT("CARRIER_IN"));
const FName LBPaintShopPortIds::CarrierOut(TEXT("CARRIER_OUT"));

namespace LBPaintShopTypesPrivate
{
    struct FCellContract
    {
        FName DefinitionId;
        ELBPaintShopCellType CellType;
        const TCHAR* DisplayName;
        FName InputWIPId;
        FName OutputWIPId;
        FName RecipeId;
        FName QualityCheckId;
    };

    TArray<FCellContract> GetContracts()
    {
        return {
            {LBPaintShopCellIds::BIWLoadDock, ELBPaintShopCellType::BIWLoadDock,
                TEXT("BIW load dock"), LBPaintShopWIPIds::BIWComplete,
                LBPaintShopWIPIds::BIWComplete, NAME_None, NAME_None},
            {LBPaintShopCellIds::PhosphateDipCell, ELBPaintShopCellType::PhosphateDip,
                TEXT("Phosphate dip cell"), LBPaintShopWIPIds::BIWComplete,
                LBPaintShopWIPIds::BIWComplete, LBPaintShopRecipeIds::PhosphateV001,
                LBPaintShopQualityIds::PhosphateCoverage},
            {LBPaintShopCellIds::EDCoatDipCell, ELBPaintShopCellType::EDCoatDip,
                TEXT("ED coat dip cell"), LBPaintShopWIPIds::BIWComplete,
                LBPaintShopWIPIds::BIWEDCoated, LBPaintShopRecipeIds::EDCoatV001,
                NAME_None},
            {LBPaintShopCellIds::DrainInspectionCell, ELBPaintShopCellType::DrainInspection,
                TEXT("Drain and inspection cell"), LBPaintShopWIPIds::BIWEDCoated,
                LBPaintShopWIPIds::BIWEDCoated, NAME_None,
                LBPaintShopQualityIds::EDFilmBuild},
            {LBPaintShopCellIds::EDCureOvenCell, ELBPaintShopCellType::EDCureOven,
                TEXT("ED cure oven cell"), LBPaintShopWIPIds::BIWEDCoated,
                LBPaintShopWIPIds::BIWCuredEDCoat, LBPaintShopRecipeIds::EDCureV001,
                LBPaintShopQualityIds::EDCure},
            {LBPaintShopCellIds::EDOutputBuffer, ELBPaintShopCellType::EDOutputBuffer,
                TEXT("ED output buffer"), LBPaintShopWIPIds::BIWCuredEDCoat,
                LBPaintShopWIPIds::BIWCuredEDCoat, NAME_None, NAME_None}
        };
    }

    const FCellContract* FindContract(const TArray<FCellContract>& Contracts,
        const FName DefinitionId)
    {
        return Contracts.FindByPredicate([DefinitionId](const FCellContract& Candidate)
        {
            return Candidate.DefinitionId == DefinitionId;
        });
    }

    FLBPaintShopPortDefinition MakePort(const FName PortId,
        const ELBPaintShopPortDirection Direction, const FName WIPId)
    {
        FLBPaintShopPortDefinition Port;
        Port.PortId = PortId;
        Port.Direction = Direction;
        Port.WIPId = WIPId;
        return Port;
    }

    FLBPaintShopCellDefinition MakeDefinition(const FCellContract& Contract)
    {
        FLBPaintShopCellDefinition Definition;
        Definition.Version = 1;
        Definition.DefinitionId = Contract.DefinitionId;
        Definition.CellType = Contract.CellType;
        Definition.DisplayName = FText::FromString(Contract.DisplayName);
        Definition.InputWIPId = Contract.InputWIPId;
        Definition.OutputWIPId = Contract.OutputWIPId;
        Definition.RecipeId = Contract.RecipeId;
        if (!Contract.QualityCheckId.IsNone())
        {
            Definition.QualityCheckIds.Add(Contract.QualityCheckId);
        }
        Definition.Ports = {
            MakePort(LBPaintShopPortIds::CarrierIn, ELBPaintShopPortDirection::Input,
                Contract.InputWIPId),
            MakePort(LBPaintShopPortIds::CarrierOut, ELBPaintShopPortDirection::Output,
                Contract.OutputWIPId)
        };
        return Definition;
    }
}

TArray<FName> FLBPaintShopDefinitionRegistry::GetCanonicalDefinitionIds()
{
    TArray<FName> Result;
    for (const LBPaintShopTypesPrivate::FCellContract& Contract :
        LBPaintShopTypesPrivate::GetContracts())
    {
        Result.Add(Contract.DefinitionId);
    }
    return Result;
}

TArray<FLBPaintShopCellDefinition> FLBPaintShopDefinitionRegistry::GetCanonicalDefinitions()
{
    TArray<FLBPaintShopCellDefinition> Result;
    for (const LBPaintShopTypesPrivate::FCellContract& Contract :
        LBPaintShopTypesPrivate::GetContracts())
    {
        Result.Add(LBPaintShopTypesPrivate::MakeDefinition(Contract));
    }
    return Result;
}

bool FLBPaintShopDefinitionRegistry::FindCanonicalDefinition(const FName DefinitionId,
    FLBPaintShopCellDefinition& OutDefinition)
{
    OutDefinition = FLBPaintShopCellDefinition();
    const TArray<LBPaintShopTypesPrivate::FCellContract> Contracts =
        LBPaintShopTypesPrivate::GetContracts();
    const LBPaintShopTypesPrivate::FCellContract* Contract =
        LBPaintShopTypesPrivate::FindContract(Contracts, DefinitionId);
    if (!Contract) return false;
    OutDefinition = LBPaintShopTypesPrivate::MakeDefinition(*Contract);
    return true;
}

bool FLBPaintShopDefinitionRegistry::ValidateDefinition(
    const FLBPaintShopCellDefinition& Definition, FString& OutReason)
{
    OutReason.Reset();
    const TArray<LBPaintShopTypesPrivate::FCellContract> Contracts =
        LBPaintShopTypesPrivate::GetContracts();
    const LBPaintShopTypesPrivate::FCellContract* Contract =
        LBPaintShopTypesPrivate::FindContract(Contracts, Definition.DefinitionId);
    if (Definition.Version != 1 || !Contract || Definition.DisplayName.IsEmpty())
    {
        OutReason = TEXT("PAINT SHOP CELL DEFINITION HAS AN INVALID VERSION, ID, OR NAME");
        return false;
    }
    if (Definition.CellType != Contract->CellType
        || Definition.InputWIPId != Contract->InputWIPId
        || Definition.OutputWIPId != Contract->OutputWIPId
        || Definition.RecipeId != Contract->RecipeId)
    {
        OutReason = TEXT("PAINT SHOP CELL DEFINITION DOES NOT MATCH ITS STABLE PROCESS CONTRACT");
        return false;
    }

    const TArray<FName> ExpectedQualityIds = Contract->QualityCheckId.IsNone()
        ? TArray<FName>() : TArray<FName>({Contract->QualityCheckId});
    if (Definition.QualityCheckIds != ExpectedQualityIds)
    {
        OutReason = TEXT("PAINT SHOP CELL DEFINITION HAS INVALID QUALITY CHECKS");
        return false;
    }
    if (Definition.Ports.Num() != 2)
    {
        OutReason = TEXT("PAINT SHOP CELL DEFINITION REQUIRES EXACTLY TWO CARRIER PORTS");
        return false;
    }

    const FLBPaintShopPortDefinition* CarrierIn = Definition.Ports.FindByPredicate([](
        const FLBPaintShopPortDefinition& Port)
    {
        return Port.PortId == LBPaintShopPortIds::CarrierIn;
    });
    const FLBPaintShopPortDefinition* CarrierOut = Definition.Ports.FindByPredicate([](
        const FLBPaintShopPortDefinition& Port)
    {
        return Port.PortId == LBPaintShopPortIds::CarrierOut;
    });
    if (!CarrierIn || !CarrierOut || CarrierIn == CarrierOut
        || CarrierIn->Direction != ELBPaintShopPortDirection::Input
        || CarrierOut->Direction != ELBPaintShopPortDirection::Output
        || CarrierIn->WIPId != Definition.InputWIPId
        || CarrierOut->WIPId != Definition.OutputWIPId)
    {
        OutReason = TEXT("PAINT SHOP CELL DEFINITION HAS INVALID CARRIER PORTS");
        return false;
    }
    return true;
}

bool FLBPaintShopDefinitionRegistry::ValidateCanonicalDefinitionSet(
    const TArray<FLBPaintShopCellDefinition>& Definitions, FString& OutReason)
{
    OutReason.Reset();
    const TArray<FName> ExpectedIds = GetCanonicalDefinitionIds();
    if (Definitions.Num() != ExpectedIds.Num())
    {
        OutReason = TEXT("PAINT SHOP CANONICAL DEFINITION SET MUST CONTAIN EXACTLY SIX CELLS");
        return false;
    }

    TSet<FName> SeenIds;
    for (int32 Index = 0; Index < Definitions.Num(); ++Index)
    {
        const FLBPaintShopCellDefinition& Definition = Definitions[Index];
        if (Definition.DefinitionId != ExpectedIds[Index]
            || SeenIds.Contains(Definition.DefinitionId)
            || !ValidateDefinition(Definition, OutReason))
        {
            if (OutReason.IsEmpty())
            {
                OutReason = TEXT("PAINT SHOP CANONICAL DEFINITION ORDER OR ID IS INVALID");
            }
            return false;
        }
        SeenIds.Add(Definition.DefinitionId);
        if (Index > 0 && Definitions[Index - 1].OutputWIPId != Definition.InputWIPId)
        {
            OutReason = TEXT("PAINT SHOP CANONICAL CARRIER FLOW HAS A WIP DISCONTINUITY");
            return false;
        }
    }
    return true;
}
