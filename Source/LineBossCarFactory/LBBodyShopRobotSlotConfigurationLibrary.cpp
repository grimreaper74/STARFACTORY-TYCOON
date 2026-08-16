#include "LBBodyShopRobotSlotConfigurationLibrary.h"

#include "LBBodyShopBuildAuthority.h"
#include "LBBodyShopCellActor.h"

namespace LBBodyShopRobotSlotConfigurationPrivate
{
    const FLBBodyShopRobotSlotDefinition* FindSlot(
        const FLBBodyShopCellDefinition& Definition, const FName SlotId)
    {
        return Definition.RobotSlots.FindByPredicate([SlotId](
            const FLBBodyShopRobotSlotDefinition& Candidate)
        {
            return Candidate.SlotId == SlotId;
        });
    }

    const FLBBodyShopRobotAssignment* FindAssignment(
        const TArray<FLBBodyShopRobotAssignment>& Assignments, const FName SlotId)
    {
        return Assignments.FindByPredicate([SlotId](
            const FLBBodyShopRobotAssignment& Candidate)
        {
            return Candidate.SlotId == SlotId;
        });
    }

    bool ResolveCell(ALBBodyShopBuildAuthority* BuildAuthority, const FName CellId,
        ALBBodyShopCellActor*& OutCell, FString& OutReason)
    {
        OutCell = nullptr;
        OutReason.Reset();
        if (!IsValid(BuildAuthority))
        {
            OutReason = TEXT("BODY SHOP ROBOT CONFIGURATION REQUIRES ITS BUILD AUTHORITY");
            return false;
        }
        OutCell = BuildAuthority->FindCell(CellId);
        if (!IsValid(OutCell))
        {
            OutReason = TEXT("BODY SHOP ROBOT CONFIGURATION CELL DOES NOT EXIST");
            return false;
        }
        return true;
    }
}

bool ULBBodyShopRobotSlotConfigurationLibrary::BuildSlotInventory(
    const FLBBodyShopCellDefinition& Definition,
    const TArray<FLBBodyShopRobotAssignment>& Assignments,
    const FTransform& CellWorldTransform, TArray<FLBBodyShopRobotSlotView>& OutSlots,
    FString& OutReason)
{
    OutSlots.Reset();
    OutReason.Reset();
    if (!FLBBodyShopDefinitionRegistry::ValidateDefinition(Definition, OutReason)
        || !FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(
            Definition, Assignments, OutReason))
    {
        return false;
    }
    if (CellWorldTransform.ContainsNaN())
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT INVENTORY HAS AN INVALID CELL TRANSFORM");
        return false;
    }

    OutSlots.Reserve(Definition.RobotSlots.Num());
    for (const FLBBodyShopRobotSlotDefinition& SlotDefinition : Definition.RobotSlots)
    {
        FLBBodyShopRobotSlotView& View = OutSlots.AddDefaulted_GetRef();
        View.SlotId = SlotDefinition.SlotId;
        View.LocalMountTransform = SlotDefinition.LocalMountTransform;
        View.WorldMountTransform = SlotDefinition.LocalMountTransform * CellWorldTransform;
        View.ReachRadiusCm = SlotDefinition.ReachRadiusCm;
        View.SweepRadiusCm = SlotDefinition.SweepRadiusCm;

        for (const ELBBodyShopRobotRole Role : SlotDefinition.AllowedRoles)
        {
            if (Role == ELBBodyShopRobotRole::None) continue;
            for (const ELBBodyShopToolType Tool : SlotDefinition.AllowedTools)
            {
                if (Tool == ELBBodyShopToolType::None) continue;
                FLBBodyShopRobotSelection& Selection =
                    View.CompatibleSelections.AddDefaulted_GetRef();
                Selection.Role = Role;
                Selection.Tool = Tool;
            }
        }

        const FLBBodyShopRobotAssignment* Assignment =
            LBBodyShopRobotSlotConfigurationPrivate::FindAssignment(
                Assignments, SlotDefinition.SlotId);
        View.bOccupied = Assignment != nullptr;
        if (Assignment) View.CurrentAssignment = *Assignment;
    }
    return true;
}

bool ULBBodyShopRobotSlotConfigurationLibrary::GetRobotSlotInventory(
    ALBBodyShopCellActor* Cell, TArray<FLBBodyShopRobotSlotView>& OutSlots,
    FString& OutReason)
{
    OutSlots.Reset();
    OutReason.Reset();
    if (!IsValid(Cell))
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT INVENTORY REQUIRES A CELL");
        return false;
    }
    return BuildSlotInventory(Cell->GetDefinition(), Cell->GetRobotAssignments(),
        Cell->GetActorTransform(), OutSlots, OutReason);
}

bool ULBBodyShopRobotSlotConfigurationLibrary::GetRobotSlot(
    ALBBodyShopCellActor* Cell, const FName SlotId, FLBBodyShopRobotSlotView& OutSlot,
    FString& OutReason)
{
    OutSlot = FLBBodyShopRobotSlotView();
    TArray<FLBBodyShopRobotSlotView> Slots;
    if (!GetRobotSlotInventory(Cell, Slots, OutReason)) return false;
    const FLBBodyShopRobotSlotView* Found = Slots.FindByPredicate([SlotId](
        const FLBBodyShopRobotSlotView& Candidate)
    {
        return Candidate.SlotId == SlotId;
    });
    if (!Found)
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT DOES NOT EXIST");
        return false;
    }
    OutSlot = *Found;
    return true;
}

bool ULBBodyShopRobotSlotConfigurationLibrary::IsRobotSelectionCompatible(
    ALBBodyShopCellActor* Cell, const FName SlotId,
    const ELBBodyShopRobotRole RobotRole, const ELBBodyShopToolType Tool,
    FString& OutReason)
{
    OutReason.Reset();
    if (!IsValid(Cell))
    {
        OutReason = TEXT("BODY SHOP ROBOT SELECTION REQUIRES A CELL");
        return false;
    }
    const FLBBodyShopRobotSlotDefinition* Slot =
        LBBodyShopRobotSlotConfigurationPrivate::FindSlot(Cell->GetDefinition(), SlotId);
    if (!Slot)
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT DOES NOT EXIST");
        return false;
    }
    if (RobotRole == ELBBodyShopRobotRole::None || Tool == ELBBodyShopToolType::None
        || !Slot->AllowedRoles.Contains(RobotRole) || !Slot->AllowedTools.Contains(Tool))
    {
        OutReason = TEXT("BODY SHOP ROBOT AND TOOL ARE NOT COMPATIBLE WITH THE AUTHORED SLOT");
        return false;
    }
    return true;
}

bool ULBBodyShopRobotSlotConfigurationLibrary::ValidateRobotSlotMutation(
    const FLBBodyShopCellDefinition& Definition,
    const TArray<FLBBodyShopRobotAssignment>& Assignments, const FName SlotId,
    const ELBBodyShopRobotSlotMutation Mutation, const ELBBodyShopRobotRole RobotRole,
    const ELBBodyShopToolType Tool, FString& OutReason)
{
    OutReason.Reset();
    if (!FLBBodyShopDefinitionRegistry::ValidateDefinition(Definition, OutReason)
        || !FLBBodyShopDefinitionRegistry::ValidateRobotAssignments(
            Definition, Assignments, OutReason))
    {
        return false;
    }

    const FLBBodyShopRobotSlotDefinition* Slot =
        LBBodyShopRobotSlotConfigurationPrivate::FindSlot(Definition, SlotId);
    if (!Slot)
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT DOES NOT EXIST");
        return false;
    }
    const bool bOccupied = LBBodyShopRobotSlotConfigurationPrivate::FindAssignment(
        Assignments, SlotId) != nullptr;

    if (Mutation != ELBBodyShopRobotSlotMutation::AddToVacantSlot
        && Mutation != ELBBodyShopRobotSlotMutation::ReplaceOccupiedSlot
        && Mutation != ELBBodyShopRobotSlotMutation::RemoveFromOccupiedSlot)
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT MUTATION IS INVALID");
        return false;
    }
    if (Mutation == ELBBodyShopRobotSlotMutation::AddToVacantSlot && bOccupied)
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT IS ALREADY OCCUPIED");
        return false;
    }
    if ((Mutation == ELBBodyShopRobotSlotMutation::ReplaceOccupiedSlot
            || Mutation == ELBBodyShopRobotSlotMutation::RemoveFromOccupiedSlot)
        && !bOccupied)
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT IS VACANT");
        return false;
    }
    if (Mutation == ELBBodyShopRobotSlotMutation::RemoveFromOccupiedSlot)
    {
        return true;
    }
    if (RobotRole == ELBBodyShopRobotRole::None || Tool == ELBBodyShopToolType::None
        || !Slot->AllowedRoles.Contains(RobotRole) || !Slot->AllowedTools.Contains(Tool))
    {
        OutReason = TEXT("BODY SHOP ROBOT AND TOOL ARE NOT COMPATIBLE WITH THE AUTHORED SLOT");
        return false;
    }
    return true;
}

bool ULBBodyShopRobotSlotConfigurationLibrary::CanApplyRobotSlotMutation(
    ALBBodyShopCellActor* Cell, const FName SlotId,
    const ELBBodyShopRobotSlotMutation Mutation, const ELBBodyShopRobotRole RobotRole,
    const ELBBodyShopToolType Tool, FString& OutReason)
{
    OutReason.Reset();
    if (!IsValid(Cell))
    {
        OutReason = TEXT("BODY SHOP ROBOT SLOT MUTATION REQUIRES A CELL");
        return false;
    }
    return ValidateRobotSlotMutation(Cell->GetDefinition(), Cell->GetRobotAssignments(),
        SlotId, Mutation, RobotRole, Tool, OutReason);
}

bool ULBBodyShopRobotSlotConfigurationLibrary::AddRobotToVacantSlot(
    ALBBodyShopBuildAuthority* BuildAuthority, const FName CellId, const FName SlotId,
    const ELBBodyShopRobotRole RobotRole, const ELBBodyShopToolType Tool,
    FString& OutReason)
{
    ALBBodyShopCellActor* Cell = nullptr;
    if (!LBBodyShopRobotSlotConfigurationPrivate::ResolveCell(
            BuildAuthority, CellId, Cell, OutReason)
        || !ValidateRobotSlotMutation(Cell->GetDefinition(), Cell->GetRobotAssignments(),
            SlotId, ELBBodyShopRobotSlotMutation::AddToVacantSlot, RobotRole, Tool,
            OutReason))
    {
        return false;
    }
    return BuildAuthority->AssignRobotToSlot(CellId, SlotId, RobotRole, Tool, OutReason);
}

bool ULBBodyShopRobotSlotConfigurationLibrary::ReplaceRobotInOccupiedSlot(
    ALBBodyShopBuildAuthority* BuildAuthority, const FName CellId, const FName SlotId,
    const ELBBodyShopRobotRole RobotRole, const ELBBodyShopToolType Tool,
    FString& OutReason)
{
    ALBBodyShopCellActor* Cell = nullptr;
    if (!LBBodyShopRobotSlotConfigurationPrivate::ResolveCell(
            BuildAuthority, CellId, Cell, OutReason)
        || !ValidateRobotSlotMutation(Cell->GetDefinition(), Cell->GetRobotAssignments(),
            SlotId, ELBBodyShopRobotSlotMutation::ReplaceOccupiedSlot, RobotRole, Tool,
            OutReason))
    {
        return false;
    }
    return BuildAuthority->AssignRobotToSlot(CellId, SlotId, RobotRole, Tool, OutReason);
}

bool ULBBodyShopRobotSlotConfigurationLibrary::RemoveRobotFromOccupiedSlot(
    ALBBodyShopBuildAuthority* BuildAuthority, const FName CellId, const FName SlotId,
    FString& OutReason)
{
    ALBBodyShopCellActor* Cell = nullptr;
    if (!LBBodyShopRobotSlotConfigurationPrivate::ResolveCell(
            BuildAuthority, CellId, Cell, OutReason)
        || !ValidateRobotSlotMutation(Cell->GetDefinition(), Cell->GetRobotAssignments(),
            SlotId, ELBBodyShopRobotSlotMutation::RemoveFromOccupiedSlot,
            ELBBodyShopRobotRole::None, ELBBodyShopToolType::None, OutReason))
    {
        return false;
    }
    return BuildAuthority->ClearRobotSlot(CellId, SlotId, OutReason);
}

bool ULBBodyShopRobotSlotConfigurationLibrary::SetCellRobotSlotOverlayVisible(
    ALBBodyShopBuildAuthority* BuildAuthority, const FName CellId, const bool bVisible,
    FString& OutReason)
{
    ALBBodyShopCellActor* Cell = nullptr;
    if (!LBBodyShopRobotSlotConfigurationPrivate::ResolveCell(
        BuildAuthority, CellId, Cell, OutReason)) return false;
    Cell->SetRobotConfigurationOverlayVisible(bVisible);
    OutReason.Reset();
    return true;
}

bool ULBBodyShopRobotSlotConfigurationLibrary::SetAllRobotSlotOverlaysVisible(
    ALBBodyShopBuildAuthority* BuildAuthority, const bool bVisible,
    int32& OutAffectedCellCount, FString& OutReason)
{
    OutAffectedCellCount = 0;
    OutReason.Reset();
    if (!IsValid(BuildAuthority))
    {
        OutReason = TEXT("BODY SHOP ROBOT OVERLAY CONTROL REQUIRES ITS BUILD AUTHORITY");
        return false;
    }
    for (ALBBodyShopCellActor* Cell : BuildAuthority->GetPlacedCells())
    {
        if (!IsValid(Cell)) continue;
        Cell->SetRobotConfigurationOverlayVisible(bVisible);
        ++OutAffectedCellCount;
    }
    return true;
}
