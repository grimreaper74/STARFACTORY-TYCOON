#include "LBPressShopSupportFleetController.h"

#include "LBCleaningAMR.h"
#include "LBMaintenanceAMR.h"
#include "LBPressShopSaveGame.h"
#include "LBSupportRobot.h"
#include "Algo/Reverse.h"
#include "EngineUtils.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

ALBPressShopSupportFleetController::ALBPressShopSupportFleetController()
{
    PrimaryActorTick.bCanEverTick = false;

    const TArray<TPair<FName, FVector>> Units = {
        {TEXT("LB-MR01-01"), FVector(-6495.0f, 5160.0f, 62.5f)},
        {TEXT("LB-MR01-02"), FVector(-5095.0f, 5160.0f, 62.5f)},
        {TEXT("LB-CR01-01"), FVector(-1495.0f, 5160.0f, 56.0f)},
        {TEXT("LB-CR01-02"), FVector(-295.0f, 5160.0f, 56.0f)},
    };
    for (const TPair<FName, FVector>& Unit : Units)
    {
        BerthRoots.Add(Unit.Key, Unit.Value);
        ApronPoints.Add(Unit.Key, FVector(Unit.Value.X, 4990.0f, Unit.Value.Z));
        AislePoints.Add(Unit.Key, FVector(Unit.Value.X, 4200.0f, Unit.Value.Z));
        StandbyPoints.Add(Unit.Key, FVector(-3300.0f, 3000.0f, Unit.Value.Z));
        DockIds.Add(Unit.Key, FName(*FString::Printf(TEXT("LB-DOCK-%s"), *Unit.Key.ToString().RightChop(3))));
    }

    // Exact XY vertices from the v262 nonpartial Recast paths. Z retains each
    // robot actor root rather than the navmesh floor projection.
    OutboundWaypoints.Add(TEXT("LB-CR01-01"), {
        FVector(-1495.0f, 4990.0f, 56.0f), FVector(-1320.0f, 4900.0f, 56.0f),
        FVector(-1320.0f, 4600.0f, 56.0f), FVector(-1495.0f, 4200.0f, 56.0f),
        FVector(-1550.0f, 3600.0f, 56.0f), FVector(-2200.0f, 3600.0f, 56.0f),
        FVector(-3300.0f, 3000.0f, 56.0f)});
    OutboundWaypoints.Add(TEXT("LB-CR01-02"), {
        FVector(-295.0f, 4990.0f, 56.0f), FVector(-500.0f, 4900.0f, 56.0f),
        FVector(-500.0f, 4600.0f, 56.0f), FVector(-295.0f, 4200.0f, 56.0f),
        FVector(-3300.0f, 3000.0f, 56.0f)});
    OutboundWaypoints.Add(TEXT("LB-MR01-01"), {
        FVector(-6495.0f, 4990.0f, 62.5f), FVector(-6495.0f, 4200.0f, 62.5f),
        FVector(-5206.0f, 4142.0f, 62.5f), FVector(-5050.0f, 3750.0f, 62.5f),
        FVector(-3300.0f, 3000.0f, 62.5f)});
    OutboundWaypoints.Add(TEXT("LB-MR01-02"), {
        FVector(-5095.0f, 4990.0f, 62.5f), FVector(-5095.0f, 4200.0f, 62.5f),
        FVector(-5050.0f, 3750.0f, 62.5f),
        FVector(-3300.0f, 3000.0f, 62.5f)});
}

void ALBPressShopSupportFleetController::BeginPlay()
{
    Super::BeginPlay();
    GetWorldTimerManager().SetTimerForNextTick(FTimerDelegate::CreateWeakLambda(this, [this]()
    {
        if (!DiscoverInstalledFleet())
        {
            return;
        }
        if (!bAutoLoadCampaignFleet)
        {
            InitialiseInstalledFleet();
            return;
        }
        if (UGameplayStatics::DoesSaveGameExist(CampaignSlotName, CampaignUserIndex))
        {
            // An existing campaign is authoritative. A malformed/incomplete
            // fleet snapshot must hold the fleet unavailable, never be hidden
            // by silently commissioning replacement defaults.
            LoadFleetFromCampaignSlot();
            return;
        }
        InitialiseInstalledFleet();
    }));
}

ALBSupportRobot* ALBPressShopSupportFleetController::FindUnit(FName UnitId) const
{
    const TObjectPtr<ALBSupportRobot>* Found = InstalledRobots.Find(UnitId);
    return Found ? Found->Get() : nullptr;
}

bool ALBPressShopSupportFleetController::GetUnitSnapshot(FName UnitId, FLBSupportRobotSaveState& OutState) const
{
    if (const ALBSupportRobot* Robot = FindUnit(UnitId))
    {
        OutState = Robot->CaptureCommonSaveState();
        return true;
    }
    return false;
}

bool ALBPressShopSupportFleetController::CommissionRobot(ALBSupportRobot* Robot, FName DockId)
{
    if (!Robot || DockId.IsNone())
    {
        return false;
    }

    if (ALBCleaningAMR* Cleaning = Cast<ALBCleaningAMR>(Robot))
    {
        FLBCleaningAMRSaveState Saved = Cleaning->CaptureSaveState();
        Saved.Common.Condition = ELBSupportRobotCondition::Restored;
        Saved.Common.State = ELBSupportRobotState::Certified;
        Saved.Common.ActiveFault = ELBSupportRobotFault::None;
        Saved.Common.BatteryStateOfChargePercent = 100.0f;
        Saved.Common.BatteryHealthPercent = 100.0f;
        Saved.Common.bCertified = true;
        Saved.Common.bDocked = false;
        Saved.Common.DockId = NAME_None;
        Saved.Common.SavedTransform = Cleaning->GetActorTransform();
        Saved.Common.bRouteRevalidationRequired = true;
        if (!Cleaning->RestoreSaveState(Saved))
        {
            return false;
        }
        Cleaning->SetSensorCoverageCertified(true);
    }
    else if (ALBMaintenanceAMR* Maintenance = Cast<ALBMaintenanceAMR>(Robot))
    {
        FLBMaintenanceAMRSaveState Saved = Maintenance->CaptureSaveState();
        Saved.Common.Condition = ELBSupportRobotCondition::Restored;
        Saved.Common.State = ELBSupportRobotState::Certified;
        Saved.Common.ActiveFault = ELBSupportRobotFault::None;
        Saved.Common.BatteryStateOfChargePercent = 100.0f;
        Saved.Common.BatteryHealthPercent = 100.0f;
        Saved.Common.bCertified = true;
        Saved.Common.bDocked = false;
        Saved.Common.DockId = NAME_None;
        Saved.Common.SavedTransform = Maintenance->GetActorTransform();
        Saved.Common.bRouteRevalidationRequired = true;
        if (!Maintenance->RestoreSaveState(Saved))
        {
            return false;
        }
    }
    else
    {
        return false;
    }

    Robot->SetSafetyHealth(true, true);
    Robot->SetRouteEnvironment(true, false, false, false);
    if (!Robot->ClearCommonFault() || !Robot->BeginRouteValidation() || !Robot->CertifyRobot()
        || !Robot->ConfirmDocked(DockId))
    {
        return false;
    }
    return true;
}

bool ALBPressShopSupportFleetController::InitialiseInstalledFleet()
{
    bFleetReady = false;
    bRestoredFromDisk = false;
    if (!DiscoverInstalledFleet())
    {
        return false;
    }

    for (const TPair<FName, TObjectPtr<ALBSupportRobot>>& Entry : InstalledRobots)
    {
        if (!CommissionRobot(Entry.Value.Get(), DockIds.FindRef(Entry.Key)))
        {
            return false;
        }

        if (!ConfigureAutomaticReturn(Entry.Value.Get(), Entry.Key))
        {
            return false;
        }
    }
    bFleetReady = true;
    return true;
}

bool ALBPressShopSupportFleetController::DiscoverInstalledFleet()
{
    InstalledRobots.Empty();
    if (!GetWorld())
    {
        return false;
    }
    for (TActorIterator<ALBSupportRobot> It(GetWorld()); It; ++It)
    {
        ALBSupportRobot* Robot = *It;
        const FName UnitId = Robot->CaptureCommonSaveState().UnitId;
        if (BerthRoots.Contains(UnitId) && !InstalledRobots.Contains(UnitId))
        {
            InstalledRobots.Add(UnitId, Robot);
        }
    }
    if (InstalledRobots.Num() != BerthRoots.Num())
    {
        return false;
    }
    return !bUseInstalledActorTransforms || BuildInstalledTransformRoutes();
}

bool ALBPressShopSupportFleetController::BuildInstalledTransformRoutes()
{
    if (InstalledRobots.Num() != 4)
    {
        return false;
    }

    BerthRoots.Empty();
    ApronPoints.Empty();
    AislePoints.Empty();
    StandbyPoints.Empty();
    OutboundWaypoints.Empty();

    for (const TPair<FName, TObjectPtr<ALBSupportRobot>>& Entry : InstalledRobots)
    {
        ALBSupportRobot* Robot = Entry.Value.Get();
        if (!Robot)
        {
            return false;
        }
        const FVector Root = Robot->GetActorLocation();
        const FVector Apron(Root.X, FMath::Max(Root.Y + 230.0f, -3820.0f), Root.Z);
        const FVector Aisle(Root.X, InstalledLayoutServiceAisleY, Root.Z);
        const FVector Standby(InstalledLayoutStandbyPoint.X, InstalledLayoutStandbyPoint.Y, Root.Z);
        BerthRoots.Add(Entry.Key, Root);
        ApronPoints.Add(Entry.Key, Apron);
        AislePoints.Add(Entry.Key, Aisle);
        StandbyPoints.Add(Entry.Key, Standby);
        OutboundWaypoints.Add(Entry.Key, {Apron, Aisle, Standby});
    }
    return true;
}

bool ALBPressShopSupportFleetController::ConfigureAutomaticReturn(ALBSupportRobot* Robot, FName UnitId)
{
    if (!Robot || !OutboundWaypoints.Contains(UnitId))
    {
        return false;
    }
    FLBSupportRobotRoute AutomaticReturn;
    AutomaticReturn.RouteId = FName(*FString::Printf(TEXT("%s_AUTO_RETURN_R05"), *UnitId.ToString()));
    AutomaticReturn.Revision = 5;
    AutomaticReturn.bCertified = true;
    AutomaticReturn.SpeedClass = ELBRouteSpeedClass::OccupiedAisle;
    AutomaticReturn.Waypoints = OutboundWaypoints.FindRef(UnitId);
    Algo::Reverse(AutomaticReturn.Waypoints);
    AutomaticReturn.Waypoints.Add(BerthRoots.FindRef(UnitId));
    AutomaticReturn.DestinationDockId = DockIds.FindRef(UnitId);
    return Robot->ConfigureAutomaticChargingRoute(AutomaticReturn, 30.0f);
}

bool ALBPressShopSupportFleetController::RevalidateRestoredRobot(
    ALBSupportRobot* Robot, FName ExpectedDockId, bool bWasDocked)
{
    if (!Robot)
    {
        return false;
    }
    if (ALBCleaningAMR* Cleaning = Cast<ALBCleaningAMR>(Robot))
    {
        Cleaning->SetSensorCoverageCertified(true);
    }
    Robot->SetSafetyHealth(true, true);
    Robot->SetRouteEnvironment(true, false, false, false);
    Robot->RaiseCommonFault(ELBSupportRobotFault::RestoreRevalidationRequired,
        TEXT("Campaign load requires a fresh route and safety revalidation."));
    if (!Robot->ClearCommonFault() || !Robot->BeginRouteValidation() || !Robot->CertifyRobot())
    {
        return false;
    }
    return !bWasDocked || Robot->ConfirmDocked(ExpectedDockId);
}

bool ALBPressShopSupportFleetController::CaptureFleetSaveState(ULBPressShopSaveGame* SaveRoot)
{
    if (!SaveRoot || !DiscoverInstalledFleet())
    {
        return false;
    }
    SaveRoot->CleaningRobots.Reset();
    SaveRoot->MaintenanceRobots.Reset();
    const TArray<FName> OrderedIds = {TEXT("LB-CR01-01"), TEXT("LB-CR01-02"), TEXT("LB-MR01-01"), TEXT("LB-MR01-02")};
    for (const FName UnitId : OrderedIds)
    {
        ALBSupportRobot* Robot = FindUnit(UnitId);
        if (ALBCleaningAMR* Cleaning = Cast<ALBCleaningAMR>(Robot))
        {
            SaveRoot->CleaningRobots.Add(Cleaning->CaptureSaveState());
        }
        else if (ALBMaintenanceAMR* Maintenance = Cast<ALBMaintenanceAMR>(Robot))
        {
            SaveRoot->MaintenanceRobots.Add(Maintenance->CaptureSaveState());
        }
        else
        {
            return false;
        }
    }
    SaveRoot->SavedAtUtc = FDateTime::UtcNow();
    return SaveRoot->CleaningRobots.Num() == 2 && SaveRoot->MaintenanceRobots.Num() == 2;
}

bool ALBPressShopSupportFleetController::RestoreFleetSaveState(const ULBPressShopSaveGame* SaveRoot)
{
    bFleetReady = false;
    bRestoredFromDisk = false;
    if (!SaveRoot || (SaveRoot->SaveFormatVersion != 13 && SaveRoot->SaveFormatVersion != 14
        && SaveRoot->SaveFormatVersion != 15 && SaveRoot->SaveFormatVersion != 16
        && SaveRoot->SaveFormatVersion != 17 && SaveRoot->SaveFormatVersion != 18)
        || SaveRoot->CleaningRobots.Num() != 2
        || SaveRoot->MaintenanceRobots.Num() != 2 || !DiscoverInstalledFleet())
    {
        return false;
    }

    TSet<FName> Seen;
    for (const FLBCleaningAMRSaveState& Saved : SaveRoot->CleaningRobots)
    {
        if (!InstalledRobots.Contains(Saved.Common.UnitId) || Seen.Contains(Saved.Common.UnitId)
            || !Cast<ALBCleaningAMR>(FindUnit(Saved.Common.UnitId)))
        {
            return false;
        }
        Seen.Add(Saved.Common.UnitId);
    }
    for (const FLBMaintenanceAMRSaveState& Saved : SaveRoot->MaintenanceRobots)
    {
        if (!InstalledRobots.Contains(Saved.Common.UnitId) || Seen.Contains(Saved.Common.UnitId)
            || !Cast<ALBMaintenanceAMR>(FindUnit(Saved.Common.UnitId)))
        {
            return false;
        }
        Seen.Add(Saved.Common.UnitId);
    }
    if (Seen.Num() != 4)
    {
        return false;
    }

    for (const FLBCleaningAMRSaveState& Saved : SaveRoot->CleaningRobots)
    {
        ALBCleaningAMR* Robot = CastChecked<ALBCleaningAMR>(FindUnit(Saved.Common.UnitId));
        if (!Robot->RestoreSaveState(Saved)
            || !RevalidateRestoredRobot(Robot, DockIds.FindRef(Saved.Common.UnitId), Saved.Common.bDocked)
            || !ConfigureAutomaticReturn(Robot, Saved.Common.UnitId))
        {
            return false;
        }
    }
    for (const FLBMaintenanceAMRSaveState& Saved : SaveRoot->MaintenanceRobots)
    {
        ALBMaintenanceAMR* Robot = CastChecked<ALBMaintenanceAMR>(FindUnit(Saved.Common.UnitId));
        if (!Robot->RestoreSaveState(Saved)
            || !RevalidateRestoredRobot(Robot, DockIds.FindRef(Saved.Common.UnitId), Saved.Common.bDocked)
            || !ConfigureAutomaticReturn(Robot, Saved.Common.UnitId))
        {
            return false;
        }
    }
    bFleetReady = true;
    bRestoredFromDisk = true;
    return true;
}

bool ALBPressShopSupportFleetController::SaveFleetToCampaignSlot()
{
    ULBPressShopSaveGame* SaveRoot = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromSlot(CampaignSlotName, CampaignUserIndex));
    if (!SaveRoot)
    {
        SaveRoot = Cast<ULBPressShopSaveGame>(UGameplayStatics::CreateSaveGameObject(ULBPressShopSaveGame::StaticClass()));
    }
    return CaptureFleetSaveState(SaveRoot)
        && UGameplayStatics::SaveGameToSlot(SaveRoot, CampaignSlotName, CampaignUserIndex);
}

bool ALBPressShopSupportFleetController::LoadFleetFromCampaignSlot()
{
    const ULBPressShopSaveGame* SaveRoot = Cast<ULBPressShopSaveGame>(
        UGameplayStatics::LoadGameFromSlot(CampaignSlotName, CampaignUserIndex));
    return RestoreFleetSaveState(SaveRoot);
}

bool ALBPressShopSupportFleetController::DispatchUnit(FName UnitId)
{
    ALBSupportRobot* Robot = FindUnit(UnitId);
    if (!bFleetReady || !Robot || !Robot->IsDocked() || !Robot->Undock())
    {
        return false;
    }
    Robot->SetSafetyHealth(true, true);
    Robot->SetRouteEnvironment(true, false, false, false);

    FLBSupportRobotRoute Route;
    Route.RouteId = FName(*FString::Printf(TEXT("%s_DISPATCH_R05"), *UnitId.ToString()));
    Route.Revision = 5;
    Route.bCertified = true;
    Route.SpeedClass = ELBRouteSpeedClass::OccupiedAisle;
    Route.Waypoints = OutboundWaypoints.FindRef(UnitId);
    return Robot->BeginCertifiedRoute(Route, false);
}

bool ALBPressShopSupportFleetController::ReturnUnitToDock(FName UnitId)
{
    ALBSupportRobot* Robot = FindUnit(UnitId);
    if (!bFleetReady || !Robot || Robot->IsDocked() || Robot->HasRouteAuthority())
    {
        return false;
    }
    Robot->SetSafetyHealth(true, true);
    Robot->SetRouteEnvironment(true, false, false, false);

    FLBSupportRobotRoute Route;
    Route.RouteId = FName(*FString::Printf(TEXT("%s_RETURN_R05"), *UnitId.ToString()));
    Route.Revision = 5;
    Route.bCertified = true;
    Route.SpeedClass = ELBRouteSpeedClass::OccupiedAisle;
    Route.Waypoints = OutboundWaypoints.FindRef(UnitId);
    Algo::Reverse(Route.Waypoints);
    Route.Waypoints.Add(BerthRoots.FindRef(UnitId));
    Route.DestinationDockId = DockIds.FindRef(UnitId);
    return Robot->BeginCertifiedRoute(Route, false);
}
