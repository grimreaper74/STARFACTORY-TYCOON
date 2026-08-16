#include "LBOneFactorySaveGame.h"

namespace LBOneFactorySaveGamePrivate
{
    bool IsTerminalUnit(const FLBOneFactoryVehicleUnitState& Unit)
    {
        return Unit.Stage == ELBOneFactoryVehicleStage::Dispatched
            || Unit.QualityState == ELBOneFactoryVehicleQualityState::Scrapped;
    }

    const FLBOneFactoryVehicleUnitState* FindUnit(
        const FLBOneFactoryProductionLedgerState& Ledger, const FName UnitId)
    {
        return Ledger.Units.FindByPredicate(
            [UnitId](const FLBOneFactoryVehicleUnitState& Unit)
            {
                return Unit.UnitId == UnitId;
            });
    }

    bool AddStationWIP(const TArray<FName>& UnitIds,
        const ELBOneFactoryDepartment Department, const TCHAR* DepartmentLabel,
        const FLBOneFactoryProductionLedgerState& Ledger,
        TSet<FName>& SeenUnitIds, FString& OutReason)
    {
        for (const FName UnitId : UnitIds)
        {
            if (UnitId.IsNone())
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY %s STATION CONTAINS AN EMPTY WIP ID"),
                    DepartmentLabel);
                return false;
            }
            if (SeenUnitIds.Contains(UnitId))
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY WIP ID %s IS RESERVED MORE THAN ONCE"),
                    *UnitId.ToString());
                return false;
            }

            const FLBOneFactoryVehicleUnitState* Unit = FindUnit(Ledger, UnitId);
            if (!Unit)
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY WIP ID %s HAS NO PRODUCTION-LEDGER UNIT"),
                    *UnitId.ToString());
                return false;
            }
            if (IsTerminalUnit(*Unit))
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY TERMINAL UNIT %s CANNOT REMAIN STATION WIP"),
                    *UnitId.ToString());
                return false;
            }
            if (Unit->Department != Department)
            {
                OutReason = FString::Printf(
                    TEXT("ONEFACTORY WIP ID %s IS RESERVED IN THE WRONG DEPARTMENT"),
                    *UnitId.ToString());
                return false;
            }
            SeenUnitIds.Add(UnitId);
        }
        return true;
    }
}

FName ULBOneFactorySaveGame::GetSaveFormatId()
{
    return TEXT("LB_ONE_FACTORY_SAVE_V001");
}

FName ULBOneFactorySaveGame::GetFactoryId()
{
    return TEXT("MOORCROSS_WORKS_ONE_FACTORY");
}

FLBOneFactorySaveState ULBOneFactorySaveGame::MakeCanonicalEmptyState()
{
    FLBOneFactorySaveState State;
    State.SchemaVersion = CurrentSchemaVersion;
    State.SaveFormatId = GetSaveFormatId();
    State.FactoryId = GetFactoryId();
    State.PayloadRevision = 0;
    State.PressLayout =
        ULBOneFactoryPressStarterLayoutLibrary::MakeCanonicalStarterLayout();
    State.BodyWeldLayout =
        ULBOneFactoryBodyWeldStarterLayoutLibrary::MakeCanonicalStarterLayout();
    State.PaintLayout =
        ULBOneFactoryPaintStarterLayoutLibrary::MakeCanonicalStarterLayout();
    State.AssemblyLayout =
        ULBOneFactoryAssemblyStarterLayoutLibrary::MakeCanonicalStarterLayout();
    State.ProductionLedger =
        ULBOneFactoryProductionFlowLibrary::MakeEmptyLedger();
    return State;
}

bool ULBOneFactorySaveGame::ValidateState(
    const FLBOneFactorySaveState& State, FString& OutReason)
{
    using namespace LBOneFactorySaveGamePrivate;
    OutReason.Reset();

    if (State.SchemaVersion != CurrentSchemaVersion
        || State.SaveFormatId != GetSaveFormatId()
        || State.FactoryId != GetFactoryId())
    {
        OutReason = TEXT("ONEFACTORY SAVE SCHEMA OR FACTORY IDENTITY IS INVALID");
        return false;
    }
    if (State.PayloadRevision < 0
        || State.PayloadRevision != State.ProductionLedger.Revision)
    {
        OutReason = TEXT(
            "ONEFACTORY SAVE PAYLOAD AND PRODUCTION REVISIONS DISAGREE");
        return false;
    }

    FString Detail;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            State.PressLayout, Detail))
    {
        OutReason = FString(TEXT("ONEFACTORY SAVE PRESS SNAPSHOT INVALID: "))
            + Detail;
        return false;
    }
    if (!ULBOneFactoryBodyWeldStarterLayoutLibrary::ValidateStarterLayout(
            State.BodyWeldLayout, Detail))
    {
        OutReason = FString(
            TEXT("ONEFACTORY SAVE BODY/WELD SNAPSHOT INVALID: ")) + Detail;
        return false;
    }
    if (!ULBOneFactoryPaintStarterLayoutLibrary::ValidateStarterLayout(
            State.PaintLayout, Detail))
    {
        OutReason = FString(TEXT("ONEFACTORY SAVE PAINT SNAPSHOT INVALID: "))
            + Detail;
        return false;
    }
    if (!ULBOneFactoryAssemblyStarterLayoutLibrary::ValidateStarterLayout(
            State.AssemblyLayout, Detail))
    {
        OutReason = FString(
            TEXT("ONEFACTORY SAVE ASSEMBLY SNAPSHOT INVALID: ")) + Detail;
        return false;
    }
    if (!ULBOneFactoryProductionFlowLibrary::ValidateLedger(
            State.ProductionLedger, Detail))
    {
        OutReason = FString(
            TEXT("ONEFACTORY SAVE PRODUCTION LEDGER INVALID: ")) + Detail;
        return false;
    }

    const FLBOneFactoryDepartmentCommissioningState& Commissioning =
        State.ProductionLedger.Commissioning;
    if (State.PressLayout.bCommissioned != Commissioning.bPressCommissioned
        || State.BodyWeldLayout.bCommissioned != Commissioning.bBodyCommissioned
        || State.PaintLayout.bCommissioned != Commissioning.bPaintCommissioned
        || State.AssemblyLayout.bCommissioned
            != Commissioning.bAssemblyCommissioned)
    {
        OutReason = TEXT(
            "ONEFACTORY SAVE LAYOUT AND PRODUCTION COMMISSIONING DISAGREE");
        return false;
    }

    const FName VehicleModelId = State.BodyWeldLayout.VehicleModelId;
    if (VehicleModelId.IsNone()
        || State.PaintLayout.VehicleModelId != VehicleModelId
        || State.AssemblyLayout.VehicleModelId != VehicleModelId)
    {
        OutReason = TEXT(
            "ONEFACTORY SAVE DEPARTMENT VEHICLE-MODEL IDENTITIES DISAGREE");
        return false;
    }
    for (const FLBOneFactoryPressStarterStationState& Station :
        State.PressLayout.Stations)
    {
        if (!Station.VehicleModelId.IsNone()
            && Station.VehicleModelId != VehicleModelId)
        {
            OutReason = TEXT(
                "ONEFACTORY SAVE PRESS VEHICLE MODEL DISAGREES WITH THE FACTORY");
            return false;
        }
    }
    for (const FLBOneFactoryVehicleUnitState& Unit :
        State.ProductionLedger.Units)
    {
        if (Unit.VehicleModelId != VehicleModelId)
        {
            OutReason = TEXT(
                "ONEFACTORY LEDGER VEHICLE MODEL DISAGREES WITH THE FACTORY");
            return false;
        }
    }

    TSet<FName> SeenStationWIP;
    for (const FLBOneFactoryPressStarterStationState& Station :
        State.PressLayout.Stations)
    {
        if (!AddStationWIP(Station.ActiveOrReservedUnitIds,
                ELBOneFactoryDepartment::Press, TEXT("PRESS"),
                State.ProductionLedger, SeenStationWIP, OutReason))
        {
            return false;
        }
    }
    for (const FLBOneFactoryBodyWeldStationState& Station :
        State.BodyWeldLayout.Stations)
    {
        if (!AddStationWIP(Station.ActiveOrReservedUnitIds,
                ELBOneFactoryDepartment::Body, TEXT("BODY/WELD"),
                State.ProductionLedger, SeenStationWIP, OutReason))
        {
            return false;
        }
    }
    for (const FLBOneFactoryPaintStarterStationState& Station :
        State.PaintLayout.Stations)
    {
        if (!AddStationWIP(Station.ActiveOrReservedUnitIds,
                ELBOneFactoryDepartment::Paint, TEXT("PAINT"),
                State.ProductionLedger, SeenStationWIP, OutReason))
        {
            return false;
        }
    }
    for (const FLBOneFactoryAssemblyStationState& Station :
        State.AssemblyLayout.Stations)
    {
        if (!AddStationWIP(Station.ActiveOrReservedUnitIds,
                ELBOneFactoryDepartment::Assembly, TEXT("ASSEMBLY"),
                State.ProductionLedger, SeenStationWIP, OutReason))
        {
            return false;
        }
    }

    OutReason = TEXT("ONEFACTORY SAVE STATE VALID");
    return true;
}
