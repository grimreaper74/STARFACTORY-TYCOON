#include "LBGameMode.h"
#include "LBManagementPawn.h"
#include "LBControlRoomHUD.h"
#include "LBDeveloperAutomationBridge.h"
#include "LBPressShopBuildAuthority.h"
#include "LBFactoryMachineBuilderSubsystem.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "LBStillageFLTFleetController.h"
#include "LBCoilAGVController.h"
#include "LBInboundDeliveryController.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBCleaningAMR.h"
#include "LBMaintenanceAMR.h"
#include "LBPressShopSupportFleetController.h"
#include "LBPressShopCampaignController.h"
#include "LBFactoryManagementSubsystem.h"
#include "LBSupportRobot.h"
#include "LBSupportRobotServiceDock.h"
#include "LBBodyWeldLineActor.h"
#include "LBECoatLineActor.h"
#include "LBFactoryEnvelopeShutterActor.h"
#include "LBFactoryEnvelopeSideDressingActor.h"
#include "Components/SkyLightComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/RectLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/RectLight.h"
#include "Engine/SkyLight.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/StaticMeshActor.h"
#include "EngineUtils.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"
#include "UnrealClient.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "TimerManager.h"

namespace
{
    constexpr float DemoECoatTotalLengthCm = 18900.0f;
    constexpr float DemoECoatTreatmentBayLengthCm = 1800.0f;
    constexpr float DemoECoatFirstCureCentreCm = 13050.0f;
    const FName CleanShellAuthorityTag(TEXT("LB.CleanShell.v20260809.v001"));
    const FName CleanShellAuthorityV2Tag(TEXT("LB.CleanShell.v20260809.v002"));
    const FName CleanFloorTag(TEXT("LB.Environment.Floor"));
    const FName CleanWallTag(TEXT("LB.Environment.Wall"));
    const TCHAR* CleanFloorMaterialPath =
        TEXT("/Game/LineBoss/Materials/Environment/MI_LB_SealedFactoryConcrete_Neutral_v001.MI_LB_SealedFactoryConcrete_Neutral_v001");
    const TCHAR* CleanWallMaterialPath =
        TEXT("/Game/LineBoss/Candidates/Architecture/FactoryEnvelopeKitRuntime_v001/Materials/MI_LB_Architecture_WarmOffWhite_v001.MI_LB_Architecture_WarmOffWhite_v001");
    const FName CleanRoofLinerTag(TEXT("LB.Environment.RoofLiner"));
    const FName CleanRoofStructureTag(TEXT("LB.Environment.RoofStructure"));
    const FName AuthoredTrainFillLightTag(TEXT("LB.Lighting.TrainFill"));

    bool IsCleanShellLightAuthority(const AActor& Actor)
    {
        // Editor labels are stripped/renamed in cooked builds. The clean-shell tag is the
        // durable authored authority; the caller's typed light iterator supplies the class gate.
        return Actor.ActorHasTag(CleanShellAuthorityTag)
            && !Actor.ActorHasTag(AuthoredTrainFillLightTag);
    }

    bool IsCleanShellFloorPaletteAuthority(const AActor& Actor)
    {
        // Both tags are authored into the shipping map. Depending on an editor-only label—or
        // on a test-only structural-slab tag—caused the real game to report zero tuned surfaces.
        return Actor.ActorHasTag(CleanShellAuthorityTag)
            && Actor.ActorHasTag(CleanFloorTag);
    }

    bool IsCleanShellWallPaletteAuthority(const AActor& Actor)
    {
        return Actor.ActorHasTag(CleanShellAuthorityTag)
            && Actor.ActorHasTag(CleanWallTag);
    }

    bool IsCleanShellRoofAuthority(const AActor& Actor)
    {
        // The sealed roof liner was intentionally promoted from the original v001
        // shell authority to v002 while the structural beams retained v001. Both are
        // authored clean-shell generations; ignoring the successor leaves the opaque
        // 220 m liner above the management camera target and hides the whole factory.
        return (Actor.ActorHasTag(CleanShellAuthorityTag)
                || Actor.ActorHasTag(CleanShellAuthorityV2Tag))
            && (Actor.ActorHasTag(CleanRoofLinerTag)
                || Actor.ActorHasTag(CleanRoofStructureTag));
    }

    struct FStarterSupportUnit
    {
        FName UnitId;
        FName VariantId;
        FVector RobotLocation;
        ELBServiceDockVariant DockVariant;
    };

    const FStarterSupportUnit StarterSupportUnits[] = {
        {TEXT("LB-CR01-01"), TEXT("LB-CR01"), FVector(-750.0f, -4050.0f, 56.0f), ELBServiceDockVariant::CR01_Cleaning},
        {TEXT("LB-CR01-02"), TEXT("LB-CR01"), FVector(-250.0f, -4050.0f, 56.0f), ELBServiceDockVariant::CR01_Cleaning},
        {TEXT("LB-MR01-01"), TEXT("LB-MR01"), FVector(250.0f, -4050.0f, 62.5f), ELBServiceDockVariant::MR01_Maintenance},
        {TEXT("LB-MR01-02"), TEXT("LB-MR01"), FVector(750.0f, -4050.0f, 62.5f), ELBServiceDockVariant::MR01_Maintenance},
    };

    FName StarterDockId(const FName UnitId)
    {
        return FName(*FString::Printf(TEXT("LB-DOCK-%s"), *UnitId.ToString().RightChop(3)));
    }

    void ApplyBrightFactorySurfacePalette(UWorld* World)
    {
        if (!World) return;

        UMaterialInterface* FloorMaterial = LoadObject<UMaterialInterface>(
            nullptr, CleanFloorMaterialPath);
        UMaterialInterface* WallMaterial = LoadObject<UMaterialInterface>(
            nullptr, CleanWallMaterialPath);
        if (!FloorMaterial || !WallMaterial)
        {
            UE_LOG(LogTemp, Error,
                TEXT("LINE_BOSS_VISUAL_TUNING missing_shell_material floor=%s wall=%s"),
                CleanFloorMaterialPath, CleanWallMaterialPath);
            return;
        }

        int32 UpdatedFloors = 0;
        int32 UpdatedWalls = 0;
        for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
        {
            UStaticMeshComponent* Mesh = It->GetStaticMeshComponent();
            if (!Mesh) continue;

            if (IsCleanShellFloorPaletteAuthority(**It))
            {
                // This dedicated material reads absolute world position, so its concrete
                // variation and 6 m saw cuts stay correctly scaled across the 220 m slab.
                // Generated AGV routes, walkways and safety paint are separate actors and
                // deliberately remain the only route authority above this neutral base.
                Mesh->SetMaterial(0, FloorMaterial);
                ++UpdatedFloors;
            }
            else if (IsCleanShellWallPaletteAuthority(**It))
            {
                // The map's perimeter is intentionally simple, but it should
                // still read as a bright enclosed factory—not an unlit void.
                // Keep all fixed/automatic floor paint separate and preserve
                // the shutter actor, which has already replaced the west wall.
                // The authored shell carries a separate interior-facing slot.
                // Apply the approved finish across all slots so a second dark
                // material cannot leave the hall looking open to the void.
                for (int32 SlotIndex = 0; SlotIndex < Mesh->GetNumMaterials(); ++SlotIndex)
                    Mesh->SetMaterial(SlotIndex, WallMaterial);
                ++UpdatedWalls;
            }
        }

        UE_LOG(LogTemp, Display,
            TEXT("LINE_BOSS_VISUAL_TUNING bright_shell_floors=%d warm_shell_walls=%d"),
            UpdatedFloors, UpdatedWalls);
    }

    void ApplyFactoryColourGrade(UWorld* World)
    {
        if (!World) return;

        APostProcessVolume* Grade = nullptr;
        for (TActorIterator<APostProcessVolume> It(World); It; ++It)
        {
            if (It->ActorHasTag(TEXT("LB.Visual.FactoryColourGrade")))
            {
                Grade = *It;
                break;
            }
        }
        if (!Grade)
        {
            FActorSpawnParameters SpawnParams;
            SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
            Grade = World->SpawnActor<APostProcessVolume>(APostProcessVolume::StaticClass(),
                FTransform::Identity, SpawnParams);
        }
        if (!Grade) return;

        Grade->Tags.AddUnique(TEXT("LB.Visual.FactoryColourGrade"));
        Grade->bUnbound = true;
        Grade->Priority = 1000.0f;
        Grade->BlendWeight = 1.0f;

        FPostProcessSettings& Settings = Grade->Settings;
        Settings.bOverride_AutoExposureBias = true;
        // Keep only a fractional global lift. The previous +1.25 EV setting clipped the
        // sealed floor and erased machine recesses in the live 720p management view.
        // The first broad-fill pass removed the distracting rect-light pools, but the
        // dark painted press assemblies still collapsed into silhouette at management
        // distance. Keep the lift global and modest: it raises the machinery and
        // floor together without reintroducing local hot spots.
        Settings.AutoExposureBias = 0.95f;
        Settings.bOverride_ColorContrast = true;
        Settings.ColorContrast = FVector4(1.02f, 1.02f, 1.02f, 1.0f);
        Settings.bOverride_ColorSaturation = true;
        Settings.ColorSaturation = FVector4(1.06f, 1.06f, 1.06f, 1.0f);
        Settings.bOverride_VignetteIntensity = true;
        Settings.VignetteIntensity = 0.10f;
        Settings.bOverride_AmbientOcclusionIntensity = true;
        Settings.AmbientOcclusionIntensity = 0.58f;
        Settings.bOverride_AmbientOcclusionRadius = true;
        Settings.AmbientOcclusionRadius = 120.0f;
        Settings.bOverride_AmbientOcclusionRadiusInWS = true;
        Settings.AmbientOcclusionRadiusInWS = 1;
        Settings.bOverride_LumenAmbientOcclusionIntensity = true;
        Settings.LumenAmbientOcclusionIntensity = 0.58f;
    }
}

ALBGameMode::ALBGameMode()
{
    DefaultPawnClass = ALBManagementPawn::StaticClass();
    HUDClass = ALBControlRoomHUD::StaticClass();

    static ConstructorHelpers::FClassFinder<ALBCleaningAMR> CleaningRobotBP(
        TEXT("/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v065/Blueprints/BP_LB_CR01_CleaningAMR_v065"));
    if (CleaningRobotBP.Succeeded()) CleaningRobotClass = CleaningRobotBP.Class;
    static ConstructorHelpers::FClassFinder<ALBMaintenanceAMR> MaintenanceRobotBP(
        TEXT("/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v022/Blueprints/BP_LB_MR01_MaintenanceAMR_v022"));
    if (MaintenanceRobotBP.Succeeded()) MaintenanceRobotClass = MaintenanceRobotBP.Class;
}

void ALBGameMode::EnsureCleanSupportFleet(UWorld* World)
{
    if (!World || !CleaningRobotClass || !MaintenanceRobotClass) return;

    TMap<FName, ALBSupportRobot*> ExistingUnits;
    for (TActorIterator<ALBSupportRobot> It(World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        const FName UnitId = It->CaptureCommonSaveState().UnitId;
        if (!UnitId.IsNone()) ExistingUnits.FindOrAdd(UnitId) = *It;
    }
    TMap<FName, ALBSupportRobotServiceDock*> ExistingDocks;
    for (TActorIterator<ALBSupportRobotServiceDock> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->GetDockId().IsNone()) ExistingDocks.FindOrAdd(It->GetDockId()) = *It;
    }

    FActorSpawnParameters SpawnParams;
    SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
    for (const FStarterSupportUnit& Unit : StarterSupportUnits)
    {
        if (!ExistingUnits.Contains(Unit.UnitId))
        {
            UClass* UnitClass = Unit.DockVariant == ELBServiceDockVariant::CR01_Cleaning
                ? CleaningRobotClass.Get() : MaintenanceRobotClass.Get();
            if (ALBSupportRobot* Robot = World->SpawnActor<ALBSupportRobot>(
                UnitClass, Unit.RobotLocation, FRotator::ZeroRotator, SpawnParams))
            {
                Robot->ConfigureIdentity(Unit.UnitId, Unit.VariantId);
                Robot->Tags.AddUnique(TEXT("LB.CleanPlayerBuilt.StarterSupportFleet"));
                ExistingUnits.Add(Unit.UnitId, Robot);
            }
        }

        const FName DockId = StarterDockId(Unit.UnitId);
        if (!ExistingDocks.Contains(DockId))
        {
            const FVector DockLocation(Unit.RobotLocation.X, -4380.0f, 0.0f);
            if (ALBSupportRobotServiceDock* Dock = World->SpawnActor<ALBSupportRobotServiceDock>(
                ALBSupportRobotServiceDock::StaticClass(), DockLocation,
                FRotator(0.0f, 90.0f, 0.0f), SpawnParams))
            {
                Dock->ConfigureDock(DockId, Unit.DockVariant);
                Dock->Tags.AddUnique(TEXT("LB.CleanPlayerBuilt.StarterSupportFleet"));
                ExistingDocks.Add(DockId, Dock);
            }
        }
    }

    ALBPressShopSupportFleetController* Fleet = nullptr;
    for (TActorIterator<ALBPressShopSupportFleetController> It(World); It; ++It)
    {
        if (IsValid(*It)) { Fleet = *It; break; }
    }
    if (!Fleet) Fleet = World->SpawnActor<ALBPressShopSupportFleetController>();
    if (Fleet)
    {
        // Build routes from the accepted clean service-bank positions, never from retired map coordinates.
        Fleet->bUseInstalledActorTransforms = true;
        Fleet->InstalledLayoutServiceAisleY = -3500.0f;
        Fleet->InstalledLayoutStandbyPoint = FVector(0.0f, -3500.0f, 0.0f);
        Fleet->Tags.AddUnique(TEXT("LB.CleanPlayerBuilt.StarterSupportFleet"));
    }
}

void ALBGameMode::BeginPlay()
{
    Super::BeginPlay();
    UWorld* World = GetWorld();
    if (!World) return;

    // The persistent clean-shell actors are available at GameMode BeginPlay.  Install one
    // guarded envelope authority before support-fleet and automatic-route bootstrapping so
    // navigation never observes both the superseded solid wall and the truthful opening.
    ALBFactoryEnvelopeShutterActor* FactoryEnvelopeShutter = nullptr;
    for (TActorIterator<ALBFactoryEnvelopeShutterActor> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed())
        {
            FactoryEnvelopeShutter = *It;
            break;
        }
    }
    if (!FactoryEnvelopeShutter)
    {
        FActorSpawnParameters ShutterSpawn;
        ShutterSpawn.SpawnCollisionHandlingOverride =
            ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        FactoryEnvelopeShutter = World->SpawnActor<ALBFactoryEnvelopeShutterActor>(
            ALBFactoryEnvelopeShutterActor::StaticClass(),
            ALBFactoryEnvelopeShutterActor::GetAuthoredWorldTransform(), ShutterSpawn);
    }
    const bool bFactoryEnvelopeShutterActive = FactoryEnvelopeShutter
        && FactoryEnvelopeShutter->ActivateCleanShellWestWallReplacement();
    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_FACTORY_ENVELOPE_SHUTTER_BOOTSTRAP active=%d"),
        bFactoryEnvelopeShutterActive ? 1 : 0);

    // Build the interior elevation rhythm after the shutter has atomically replaced its one
    // wall.  This actor is visual-only: it never changes the shell, navigation, AGV routes,
    // player-build placement or save data.
    ALBFactoryEnvelopeSideDressingActor* FactoryEnvelopeSides = nullptr;
    for (TActorIterator<ALBFactoryEnvelopeSideDressingActor> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed())
        {
            FactoryEnvelopeSides = *It;
            break;
        }
    }
    if (!FactoryEnvelopeSides)
    {
        FActorSpawnParameters SideSpawn;
        SideSpawn.SpawnCollisionHandlingOverride =
            ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        FactoryEnvelopeSides = World->SpawnActor<ALBFactoryEnvelopeSideDressingActor>(
            ALBFactoryEnvelopeSideDressingActor::StaticClass(), FTransform::Identity, SideSpawn);
    }
    const bool bFactoryEnvelopeSidesActive = FactoryEnvelopeSides
        && FactoryEnvelopeSides->ActivatePresentation();
    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_FACTORY_ENVELOPE_SIDES_BOOTSTRAP active=%d"),
        bFactoryEnvelopeSidesActive ? 1 : 0);

    // One world, one campaign transaction authority. Retain the deterministic
    // first authored instance, remove accidental duplicates, or create the clean
    // player-built authority when the shell contains none.
    TArray<ALBPressShopCampaignController*> CampaignAuthorities;
    for (TActorIterator<ALBPressShopCampaignController> It(World); It; ++It)
    {
        if (IsValid(*It) && !It->IsActorBeingDestroyed()) CampaignAuthorities.Add(*It);
    }
    CampaignAuthorities.Sort([](const ALBPressShopCampaignController& Left,
        const ALBPressShopCampaignController& Right)
    {
        return Left.GetName() < Right.GetName();
    });
    if (CampaignAuthorities.IsEmpty())
    {
        FActorSpawnParameters CampaignSpawn;
        CampaignSpawn.SpawnCollisionHandlingOverride =
            ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        if (ALBPressShopCampaignController* Spawned =
            World->SpawnActor<ALBPressShopCampaignController>(
                ALBPressShopCampaignController::StaticClass(),
                FTransform::Identity, CampaignSpawn))
        {
            CampaignAuthorities.Add(Spawned);
        }
    }
    for (int32 Index = 1; Index < CampaignAuthorities.Num(); ++Index)
    {
        CampaignAuthorities[Index]->Destroy();
    }
    if (!CampaignAuthorities.IsEmpty())
    {
        CampaignAuthorities[0]->Tags.AddUnique(TEXT("LB.Campaign.Authority"));
    }

    if (ULBFactoryManagementSubsystem* Management =
        World->GetSubsystem<ULBFactoryManagementSubsystem>())
    {
        const FLBFactoryManagementSaveState Current = Management->CaptureSaveState();
        if (!Current.bCampaignInitialised)
        {
            ensureMsgf(Management->InitialiseNewCampaign(
                ULBFactoryManagementSubsystem::DefaultStartingCashPence, 0),
                TEXT("Line Boss could not initialise its one new-campaign management authority"));
        }
    }

#if !UE_BUILD_SHIPPING
    if (ALBDeveloperAutomationBridge::IsEnabledFromCommandLine(FCommandLine::Get()))
    {
        FActorSpawnParameters BridgeSpawn;
        BridgeSpawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        if (ALBDeveloperAutomationBridge* Bridge = World->SpawnActor<ALBDeveloperAutomationBridge>(
            ALBDeveloperAutomationBridge::StaticClass(), FTransform::Identity, BridgeSpawn))
        {
            Bridge->Tags.AddUnique(TEXT("LB.Developer.AutomationBridge"));
        }
    }

    // Reliable developer backdoor for unattended visual smoke tests. Unreal captures its own
    // viewport (including Canvas HUD), avoiding foreground-window restrictions on DirectX apps.
    if (FParse::Param(FCommandLine::Get(), TEXT("LineBossAutoCapture")))
    {
        FTimerHandle CaptureTimer;
        World->GetTimerManager().SetTimer(CaptureTimer, []()
        {
            const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Screenshots"), TEXT("Windows"));
            IFileManager::Get().MakeDirectory(*Directory, true);
            const FString Path = FPaths::Combine(Directory, TEXT("LineBoss_AutoCapture.png"));
            FScreenshotRequest::RequestScreenshot(Path, true, false);
            UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_AUTO_CAPTURE_REQUESTED path=%s"), *Path);
        }, 5.0f, false);
    }
    if (FParse::Param(FCommandLine::Get(), TEXT("LineBossAutoProductionHUD")))
    {
        FTimerHandle ProductionHudTimer;
        World->GetTimerManager().SetTimer(ProductionHudTimer, [World]()
        {
            if (!World) return;
            for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
            {
                if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(It->Get()->GetHUD()))
                {
                    HUD->OpenManagementPage(ELBManagementPage::Overview);
                    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_AUTO_PRODUCTION_HUD_OPENED"));
                    break;
                }
            }
        }, 4.25f, false);
    }
#endif

    ALBPlayerBuiltPressFlowController* PlayerFlowAuthority = nullptr;
    for (TActorIterator<ALBPlayerBuiltPressFlowController> It(World); It; ++It)
    {
        if (IsValid(*It))
        {
            PlayerFlowAuthority = *It;
            break;
        }
    }
    if (!PlayerFlowAuthority)
        PlayerFlowAuthority = World->SpawnActor<ALBPlayerBuiltPressFlowController>();

    ALBStillageFLTFleetController* StillageFleet = nullptr;
    for (TActorIterator<ALBStillageFLTFleetController> It(World); It; ++It)
    {
        if (IsValid(*It)) { StillageFleet = *It; break; }
    }
    if (!StillageFleet)
        StillageFleet = World->SpawnActor<ALBStillageFLTFleetController>();
    if (StillageFleet)
    {
        // A new factory owns one compact stillage FLT. Additional units remain an
        // explicit paid capacity upgrade through TryPurchaseAdditionalFLT.
        StillageFleet->InitialiseFreshFleet();
        StillageFleet->Tags.AddUnique(TEXT("LB.CleanPlayerBuilt.StarterStillageFleet"));
    }

    bool bHasCoilAGV = false;
    for (TActorIterator<ALBCoilAGVController> It(World); It; ++It) { bHasCoilAGV = true; break; }
    if (!bHasCoilAGV) World->SpawnActor<ALBCoilAGVController>();

    bool bHasLegacyOperationsConsole = false;
    for (TActorIterator<ALBControlRoomOperationsConsole> It(World); It; ++It)
    {
        if (IsValid(*It))
        {
            bHasLegacyOperationsConsole = true;
            break;
        }
    }
    if (!bHasLegacyOperationsConsole)
    {
        TArray<ALBInboundDeliveryController*> InboundAuthorities;
        for (TActorIterator<ALBInboundDeliveryController> It(World); It; ++It)
            if (IsValid(*It)) InboundAuthorities.Add(*It);
        InboundAuthorities.Sort([](const ALBInboundDeliveryController& A,
            const ALBInboundDeliveryController& B)
        {
            return A.GetName() < B.GetName();
        });
        if (InboundAuthorities.IsEmpty())
        {
            if (ALBInboundDeliveryController* Spawned =
                World->SpawnActor<ALBInboundDeliveryController>())
            {
                InboundAuthorities.Add(Spawned);
            }
        }
        for (int32 Index = 1; Index < InboundAuthorities.Num(); ++Index)
            InboundAuthorities[Index]->Destroy();
        if (!InboundAuthorities.IsEmpty())
            InboundAuthorities[0]->SetPlayerBuilderBootstrapEnabled(true);
        if (PlayerFlowAuthority)
            PlayerFlowAuthority->SetConsoleFreeTrainAutostartEnabled(true);
        EnsureCleanSupportFleet(World);
    }

    // The factory shell retains its roof for exterior/reference views, but the primary game
    // camera is an overhead builder. Hide only the clean-shell roof pieces at runtime so the
    // player sees the factory floor instead of the roof liner.
    int32 HiddenRoofPieces = 0;
    for (TActorIterator<AStaticMeshActor> It(World); It; ++It)
    {
        if (IsCleanShellRoofAuthority(**It))
        {
            It->SetActorHiddenInGame(true);
            It->SetActorEnableCollision(false);
            ++HiddenRoofPieces;
        }
    }
    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_VISUAL_TUNING hidden_roof_pieces=%d"),
        HiddenRoofPieces);
    ApplyBrightFactorySurfacePalette(World);
    ApplyFactoryColourGrade(World);
    int32 TunedSkyLights = 0;
    for (TActorIterator<ASkyLight> It(World); It; ++It)
    {
        if (!IsCleanShellLightAuthority(**It))
        {
            continue;
        }
        if (USkyLightComponent* Sky = It->GetLightComponent())
        {
            Sky->SetMobility(EComponentMobility::Movable);
            Sky->SetIntensity(1.65f);
            Sky->SetLightColor(FLinearColor(0.94f, 0.97f, 1.0f, 1.0f));
            Sky->bLowerHemisphereIsBlack = false;
            Sky->SetLowerHemisphereColor(FLinearColor(0.18f, 0.19f, 0.20f, 1.0f));
            Sky->SetOcclusionExponent(1.10f);
            Sky->SetMinOcclusion(0.08f);
            // Do not issue a startup cubemap capture here. The map's authored
            // skylight data is already valid, while forcing a recapture after
            // the shell runtime pass can trigger a D3D12 device loss before
            // the first playable frame on affected PCs.
            ++TunedSkyLights;
        }
    }
    int32 TunedDirectionalLights = 0;
    for (TActorIterator<ADirectionalLight> It(World); It; ++It)
    {
        if (!IsCleanShellLightAuthority(**It))
        {
            continue;
        }
        if (UDirectionalLightComponent* Light = Cast<UDirectionalLightComponent>(It->GetLightComponent()))
        {
            Light->SetMobility(EComponentMobility::Movable);
            Light->SetIntensity(1.80f);
            Light->SetLightColor(FLinearColor(1.0f, 0.97f, 0.92f, 1.0f), false);
            Light->SetLightSourceAngle(8.0f);
            Light->SetShadowSourceAngleFactor(1.0f);
            // Keep a very soft grounding shadow for three-dimensional read, but do not let
            // the clean-shell roof structure project dominant dark bands across the build floor.
            // The ceiling grid remains the primary readable factory light.
            Light->SetShadowAmount(0.03f);
            Light->SetCastShadows(true);
            ++TunedDirectionalLights;
        }
    }
    int32 TunedRectLights = 0;
    for (TActorIterator<ARectLight> It(World); It; ++It)
    {
        if (!IsCleanShellLightAuthority(**It))
        {
            continue;
        }
        if (URectLightComponent* Light = Cast<URectLightComponent>(It->GetLightComponent()))
        {
            Light->SetMobility(EComponentMobility::Movable);
            // Keep the authored ceiling-fixture meshes, but suppress their 21 individual
            // light components. Even with broad sources and no shadows, the overlapping
            // inverse-square falloff produced clipped white pools across the management
            // view. The skylight and soft directional rig provide the uniform hall fill.
            Light->SetIntensity(0.0f);
            Light->SetCastShadows(false);
            Light->SetVisibility(false);
            ++TunedRectLights;
        }
    }
    UE_LOG(LogTemp, Display,
        TEXT("LINE_BOSS_VISUAL_TUNING package_safe_lights sky=%d directional=%d rect=%d sky_recapture=0"),
        TunedSkyLights, TunedDirectionalLights, TunedRectLights);

    for (TActorIterator<ALBPressShopBuildAuthority> It(World); It; ++It) return;

    ALBPressShopBuildAuthority* Authority = World->SpawnActor<ALBPressShopBuildAuthority>();
    if (!Authority) return;

    FLBPressShopBuildBay BuildBay;
    BuildBay.BayId = TEXT("PLAYER_BUILDABLE_PRESS_SHOP_FLOOR");
    BuildBay.Centre = FVector::ZeroVector;
    BuildBay.HalfExtent = FVector(16000.0f, 6500.0f, 1000.0f);
    Authority->BuildBays.Add(BuildBay);

    auto AddStorageBay = [Authority](const FName Id, const ELBPressShopStorageType Type,
        const FVector Defaults, const int32 Capacity, const FVector2D Pitch)
    {
        FLBPressShopStorageBay Bay;
        Bay.BayId = Id;
        Bay.Centre = FVector::ZeroVector;
        Bay.HalfExtent = FVector(16000.0f, 6500.0f, 500.0f);
        Bay.AcceptedTypes.Add(Type);
        Bay.DefaultZoneHalfExtent = Defaults;
        Bay.DefaultCapacity = Capacity;
        Bay.StorageUnitPitchCm = Pitch;
        Bay.BoundaryClearanceCm = 50.0f;
        Authority->StorageBays.Add(Bay);
    };
    AddStorageBay(TEXT("WRAPPED_COIL_STORAGE"), ELBPressShopStorageType::BareCoils,
        FVector(710.0f, 650.0f, 125.0f), 12, FVector2D(220.0f, 600.0f));
    AddStorageBay(TEXT("PREPARED_BLANK_STORAGE"), ELBPressShopStorageType::PreparedBlanks,
        FVector(550.0f, 550.0f, 100.0f), 16, FVector2D(250.0f, 250.0f));
    AddStorageBay(TEXT("FINISHED_PANEL_STORAGE"), ELBPressShopStorageType::FinishedPanelStillages,
        FVector(550.0f, 550.0f, 235.0f), 48, FVector2D(250.0f, 250.0f));
    AddStorageBay(TEXT("EMPTY_STILLAGE_RETURN_STORAGE"), ELBPressShopStorageType::EmptyPanelStillages,
        FVector(550.0f, 550.0f, 235.0f), 48, FVector2D(250.0f, 250.0f));
    AddStorageBay(TEXT("SCRAP_STORAGE"), ELBPressShopStorageType::Scrap,
        FVector(425.0f, 425.0f, 125.0f), 9, FVector2D(250.0f, 250.0f));
    AddStorageBay(TEXT("MAINTENANCE_STORAGE"), ELBPressShopStorageType::MaintenanceParts,
        FVector(425.0f, 425.0f, 125.0f), 9, FVector2D(250.0f, 250.0f));
    AddStorageBay(TEXT("QUARANTINE_STORAGE"), ELBPressShopStorageType::Quarantine,
        FVector(425.0f, 425.0f, 125.0f), 9, FVector2D(250.0f, 250.0f));

    // Utilities and navigable logistics authority are treated as the building's fixed
    // under-floor grid. Machines remain entirely player placed; visible AGV routes and safe
    // service walkways are generated from the player's actual material-flow connections.
    for (int32 Lane = -6; Lane <= 6; ++Lane)
    {
        FLBPressShopUtilitySpine Spine;
        Spine.SpineId = FName(*FString::Printf(TEXT("UNDERFLOOR_SERVICE_%02d"), Lane + 6));
        Spine.Start = FVector(-16000.0f, Lane * 1000.0f, 0.0f);
        Spine.End = FVector(16000.0f, Lane * 1000.0f, 0.0f);
        Spine.MaximumConnectionDistanceCm = 750.0f;
        Authority->UtilitySpines.Add(Spine);

        FLBPressShopLogisticsSpine Logistics;
        Logistics.SpineId = FName(*FString::Printf(TEXT("AUTOMATIC_LOGISTICS_%02d"), Lane + 6));
        Logistics.Start = FVector(-16000.0f, Lane * 1000.0f, 0.0f);
        Logistics.End = FVector(16000.0f, Lane * 1000.0f, 0.0f);
        Logistics.MaximumAccessDistanceCm = 600.0f;
        Authority->LogisticsSpines.Add(Logistics);
    }

#if !UE_BUILD_SHIPPING
    // Development-only packaged-game play-test driver. It uses the same ordered catalogue,
    // placement authority, automatic links/routes and storage layout code as the player UI.
    const bool bAutoBuildPressShop =
        FParse::Param(FCommandLine::Get(), TEXT("LineBossAutoBuildPressShop"));
    const bool bAutoBuildPaintShop =
        FParse::Param(FCommandLine::Get(), TEXT("LineBossAutoBuildPaintShop"));
    if (bAutoBuildPressShop || bAutoBuildPaintShop)
    {
        ULBFactoryMachineBuilderSubsystem* Builder =
            World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
        auto PlaceMachine = [Builder](const ELBFactoryBuildMachineType Type,
            const FVector& Location, const float Yaw = 0.0f)
        {
            AActor* Built = nullptr;
            FString Reason;
            const bool bPlaced = Builder && Builder->PlaceMachine(
                Type, FTransform(FRotator(0.0f, Yaw, 0.0f), Location), Built, Reason);
            UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_AUTOPLAY machine=%d placed=%d location=%s reason=%s"),
                static_cast<int32>(Type), bPlaced ? 1 : 0,
                *Location.ToCompactString(), *Reason);
            return bPlaced ? Built : nullptr;
        };
        auto ProbeMachinePlacement = [Builder](const ELBFactoryBuildMachineType Type,
            const FVector& Location, const float Yaw)
        {
            FString Reason;
            const bool bValid = Builder && Builder->ValidateMachineTransform(Type,
                FTransform(FRotator(0.0f, Yaw, 0.0f), Location), Reason);
            UE_LOG(LogTemp, Display,
                TEXT("LINE_BOSS_AUTOPLAY_PROBE machine=%d valid=%d location=%s yaw=%.1f reason=%s"),
                static_cast<int32>(Type), bValid ? 1 : 0,
                *Location.ToCompactString(), Yaw, *Reason);
        };
        auto PlaceStorage = [Authority](const ELBPressShopStorageType Type,
            const FVector2D& FloorLocation, const float Yaw = 0.0f)
        {
            FVector Extent;
            int32 Capacity = 0;
            FString Reason;
            ALBPressShopStorageZone* Zone = nullptr;
            const bool bDefaults = Authority->GetStoragePlacementDefaults(
                Type, Extent, Capacity, Reason);
            const FVector Location(FloorLocation.X, FloorLocation.Y, Extent.Z);
            const bool bPlaced = bDefaults && Authority->PlaceStorageZone(
                Type, FTransform(FRotator(0.0f, Yaw, 0.0f), Location),
                Extent, Capacity, Zone, Reason);
            UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_AUTOPLAY storage=%d placed=%d location=%s reason=%s"),
                static_cast<int32>(Type), bPlaced ? 1 : 0,
                *Location.ToCompactString(), *Reason);
            return bPlaced;
        };

        // Keep the press demonstration on one readable left-to-right process axis, with
        // storage in the adjacent logistics aisles. Every offset below stays within the
        // real 20 m storage-port connection contract; this fixture must exercise the same
        // ordered links as player placement rather than merely scattering unlocked props.
        constexpr float DemoLineY = -1000.0f;
        constexpr float DemoLowerLogisticsY = DemoLineY - 1500.0f;
        constexpr float DemoUpperLogisticsY = DemoLineY + 1500.0f;
        PlaceMachine(ELBFactoryBuildMachineType::InboundDeliveryDock,
            FVector(-10000, DemoLineY, 0), -90.0f);
        // Keep the three-high storage envelopes in their own logistics aisle. Storage
        // height was raised to 4.7 m and its exact protected footprint is now enforced;
        // placing buffers on the process centreline would correctly obstruct the next
        // machine and make this deterministic packaged-play fixture stop after INBOUND.
        // PR002's output must feed the wrapped-coil store before that store can feed
        // PR004. The former store position plus its 18 m lateral offset left both links
        // just outside their authored 20 m range, so the visual-QA fixture stopped after PR002.
        PlaceStorage(ELBPressShopStorageType::BareCoils,
            FVector2D(-6950, DemoLowerLogisticsY), -90.0f);
        PlaceMachine(ELBFactoryBuildMachineType::CoilWeighInspectionCell,
            FVector(-6800, DemoLineY, 0), -90.0f);
        PlaceMachine(ELBFactoryBuildMachineType::DepackagingRobot,
            FVector(-5700, DemoLineY, 0), -90.0f);
        PlaceMachine(ELBFactoryBuildMachineType::DecoilerFeeder,
            FVector(-4400, DemoLineY, 0), -90.0f);

        // One train can stamp the complete vehicle programme through player-selected die
        // changes. Extra trains remain optional catalogue expansions for later bottlenecks.
        PlaceStorage(ELBPressShopStorageType::PreparedBlanks,
            FVector2D(-3000, DemoLowerLogisticsY), -90.0f);
        PlaceMachine(ELBFactoryBuildMachineType::PressTrain,
            FVector(-2200, DemoLineY, 0), -90.0f);

        PlaceMachine(ELBFactoryBuildMachineType::InspectionCell,
            FVector(5484, DemoLineY, 0), -90.0f);
        PlaceStorage(ELBPressShopStorageType::EmptyPanelStillages,
            FVector2D(6984, DemoUpperLogisticsY), -90.0f);
        PlaceStorage(ELBPressShopStorageType::FinishedPanelStillages,
            FVector2D(6984, DemoLowerLogisticsY), -90.0f);
        PlaceMachine(ELBFactoryBuildMachineType::OutboundPanelDock,
            FVector(8684, DemoLineY, 0), -90.0f);

        // Opt-in only: visual captures may demonstrate the real automatic line under a
        // genuine Cairnwell order. This never runs in a normal new campaign, does not add
        // fake panel stock, and uses the same batch/coil/AGV/train authorities as the UI.
        if (FParse::Param(FCommandLine::Get(), TEXT("LineBossAutoLiveProduction"))
            && PlayerFlowAuthority && PlayerFlowAuthority->GetPanelBatches().IsEmpty())
        {
            FLBVehiclePanelBatch DemoBatch;
            DemoBatch.OrderId = TEXT("AUTOPLAY-LIVE-ORDER-0001");
            DemoBatch.VehicleModelId = TEXT("CAIRNWELL_2040");
            DemoBatch.PanelTypeId = TEXT("DOOR_FRONT_LEFT");
            DemoBatch.RequestedQuantity = 10;
            FString DemoOrderReason;
            const bool bQueued = PlayerFlowAuthority->QueuePanelBatch(DemoBatch, DemoOrderReason);
            UE_LOG(LogTemp, Display,
                TEXT("LINE_BOSS_AUTOPLAY_LIVE_PRODUCTION queued=%d reason=%s"),
                bQueued ? 1 : 0, *DemoOrderReason);
        }

        // A separate opt-in flag extends the same truthful player-built demonstration through
        // Body Weld and into Paint Shop. The body-weld origin is offset from the outbound dock
        // by exactly the difference between their authored hand-off sockets: the dock output is
        // at local +Y after its -90 degree rotation, while the weld stillage input is local -Y.
        // This leaves a clear 60 x 30 m weld envelope and a real sub-25 m logical hand-off.
        // ED then runs back in the upper aisle with its input aligned to the weld BIW output;
        // both complete envelopes stay inside the authored floor without weakening validation.
        if (bAutoBuildPaintShop)
        {
            // The former east-wall position put the rotated 60 x 30 m protected
            // envelope through the shell, so the development showcase could only
            // spawn as a visual exception.  Keep the optional cell in a real clear
            // bay inside the hall: it reads in the opening overview and can be
            // inspected without looking through a wall.  This remains a QA-only
            // presentation fixture; player placement continues through its normal
            // validation and connection authority.
            const FVector BodyWeldLocation(8700.0f, 0.0f, 0.0f);
            const FTransform BodyWeldTransform(
                FRotator(0.0f, 90.0f, 0.0f), BodyWeldLocation);
            ProbeMachinePlacement(ELBFactoryBuildMachineType::BodyWeldLine,
                BodyWeldLocation, 90.0f);
            FString VisualQAReason;
            ALBBodyWeldLineActor* BodyWeldLine = Cast<ALBBodyWeldLineActor>(
                Builder ? Builder->PlaceMachineForVisualQA(
                    ELBFactoryBuildMachineType::BodyWeldLine,
                    BodyWeldTransform, VisualQAReason) : nullptr);
            UE_LOG(LogTemp, Display,
                TEXT("LINE_BOSS_AUTOPLAY_VISUAL_QA machine=%d spawned=%d reason=%s"),
                static_cast<int32>(ELBFactoryBuildMachineType::BodyWeldLine),
                BodyWeldLine ? 1 : 0, *VisualQAReason);

            // The full 189 m ED line runs west from its local origin.  Keep its
            // 195 m protected envelope in the north aisle, rather than putting
            // the showcase origin outside the east shell where a camera sees
            // black exterior space instead of the factory.
            const FTransform ECoatTransform(FRotator(0.0f, 180.0f, 0.0f),
                FVector(9500.0f, 4000.0f, 0.0f));
            ALBECoatLineActor* ECoatLine = Cast<ALBECoatLineActor>(
                BodyWeldLine && Builder ? Builder->PlaceMachineForVisualQA(
                    ELBFactoryBuildMachineType::ECoatLine,
                    ECoatTransform, VisualQAReason) : nullptr);
            UE_LOG(LogTemp, Display,
                TEXT("LINE_BOSS_AUTOPLAY_VISUAL_QA machine=%d spawned=%d reason=%s"),
                static_cast<int32>(ELBFactoryBuildMachineType::ECoatLine),
                ECoatLine ? 1 : 0, *VisualQAReason);
            if (BodyWeldLine && ECoatLine)
            {
                ECoatLine->bLoopCarriers = true;
                ECoatLine->TargetLineSpeedCmPerSecond = 75.0f;

                // One body at the immersed centre of every 18 m treatment stage and all six
                // cure positions makes dipping, oven capacity, lighting and spacing visible
                // in one full-line capture.
                for (int32 TreatmentIndex = 0; TreatmentIndex < 6; ++TreatmentIndex)
                {
                    ECoatLine->AddCarrier(
                        FName(*FString::Printf(TEXT("ED-DEMO-TREAT-%02d"), TreatmentIndex + 1)),
                        DemoECoatTreatmentBayLengthCm * (TreatmentIndex + 0.5f));
                }
                for (int32 OvenIndex = 0; OvenIndex < 6; ++OvenIndex)
                {
                    ECoatLine->AddCarrier(
                        FName(*FString::Printf(TEXT("ED-DEMO-OVEN-%02d"), OvenIndex + 1)),
                        DemoECoatFirstCureCentreCm + (900.0f * OvenIndex));
                }
                ECoatLine->SetOperatingState(
                    ELBECoatOperatingState::Running, TEXT("AUTOPLAY_VISUAL_PROOF"));
            }
        }

        const bool bAutoWideFactory = FParse::Param(
            FCommandLine::Get(), TEXT("LineBossAutoWideFactory"));
        FTimerHandle FocusTimer;
        World->GetTimerManager().SetTimer(FocusTimer, [World, bAutoWideFactory]()
        {
            if (!World) return;
            for (TActorIterator<ALBManagementPawn> It(World); It; ++It)
            {
                if (IsValid(*It)
                    && (bAutoWideFactory ? It->FocusWholeBuiltFactory()
                        : It->FocusBuiltFactory())) break;
            }
        }, 0.5f, false);
    }
#endif
}
