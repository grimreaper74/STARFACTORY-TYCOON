#include "LBOneFactoryPressArtDirectionActor.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Components/MeshComponent.h"
#include "Components/SceneComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "LBFactoryFloorMarkingComponent.h"
#include "LBOneFactoryPressStarterPresentationActor.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace LBOneFactoryPressArtDirectionPrivate
{
    const TCHAR* const ArtDirectionRoot = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001/");
    const TCHAR* const PaletteMasterPath = TEXT(
        "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001/"
        "Materials/M_CA_MW_PT_ArtDirectionPalette_Master_v001."
        "M_CA_MW_PT_ArtDirectionPalette_Master_v001");
    const TCHAR* const PaletteMaterialPaths[] =
    {
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001/Materials/MI_CA_MW_PT_AD_CairnwellGreen_v001.MI_CA_MW_PT_AD_CairnwellGreen_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001/Materials/MI_CA_MW_PT_AD_FoundryCharcoal_v001.MI_CA_MW_PT_AD_FoundryCharcoal_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001/Materials/MI_CA_MW_PT_AD_SteelGrey_v001.MI_CA_MW_PT_AD_SteelGrey_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001/Materials/MI_CA_MW_PT_AD_WarmWhite_v001.MI_CA_MW_PT_AD_WarmWhite_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001/Materials/MI_CA_MW_PT_AD_SafetyYellow_v001.MI_CA_MW_PT_AD_SafetyYellow_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001/Materials/MI_CA_MW_PT_AD_SignalRed_v001.MI_CA_MW_PT_AD_SignalRed_v001"),
        TEXT("/Game/LineBoss/Factory/OneFactory/v001/Native/Press/ArtDirection_v001/Materials/MI_CA_MW_PT_AD_PaleGreenZone_v001.MI_CA_MW_PT_AD_PaleGreenZone_v001")
    };

    enum EPaletteMaterial : int32
    {
        CairnwellGreen = 0,
        FoundryCharcoal,
        SteelGrey,
        WarmWhite,
        SafetyYellow,
        SignalRed,
        PaleGreenZone
    };

    const FVector TrainAggregateLocalLocationCm(9.25f, 2367.5f, 0.0f);
    constexpr float TrainPitchCm = 1450.0f;
    constexpr int32 ExpectedFloorPaintInstances = 36;
    constexpr int32 ExpectedOverheadStructureInstances = 8;
    constexpr int32 ExpectedOverheadAccentInstances = 3;

    bool IsKnownTechnicalSlot(const FName SlotName)
    {
        static const TSet<FName> TechnicalSlots =
        {
            TEXT("CA_MW_WorkedSteel"), TEXT("CA_MW_InspectionGlass"),
            TEXT("CA_MW_StatusGreen"), TEXT("CA_MW_StatusAmber"),
            TEXT("CA_MW_DarkRubber"), TEXT("CA_MW_GalvanizedCoil"),
            TEXT("CA_MW_StampedPanel"), TEXT("CA_MW_TaskLightGlass"),
            TEXT("M_CA_LampGreen"), TEXT("M_CA_LampAmber")
        };
        return TechnicalSlots.Contains(SlotName);
    }

    bool IsPaletteSemanticSlot(const FName SlotName)
    {
        const FString Value = SlotName.ToString();
        return Value.StartsWith(TEXT("CA_MW_")) || Value.StartsWith(TEXT("M_CA_"));
    }

    int32 PaletteIndexForSlot(const FName SlotName)
    {
        if (SlotName == TEXT("CA_MW_CairnwellGreen")
            || SlotName == TEXT("M_CA_MainGreen"))
        {
            return CairnwellGreen;
        }
        if (SlotName == TEXT("CA_MW_FoundryCharcoal")
            || SlotName == TEXT("M_CA_DarkSteel")
            || SlotName == TEXT("M_CA_CharcoalGrey")
            || SlotName == TEXT("M_CA_ScreenDark"))
        {
            return FoundryCharcoal;
        }
        if (SlotName == TEXT("CA_MW_ServiceGrey")
            || SlotName == TEXT("M_CA_CleanSteel"))
        {
            return SteelGrey;
        }
        if (SlotName == TEXT("CA_MW_TrainAAccent")
            || SlotName == TEXT("M_CA_Concrete"))
        {
            // The source's ubiquitous blue is not a brand token. Warm White
            // preserves a readable contrast accent while staying in palette.
            return WarmWhite;
        }
        if (SlotName == TEXT("CA_MW_SafetyYellow")
            || SlotName == TEXT("M_CA_SafetyYellow"))
        {
            return SafetyYellow;
        }
        if (SlotName == TEXT("CA_MW_StatusRed")
            || SlotName == TEXT("M_CA_LampRed"))
        {
            return SignalRed;
        }
        return INDEX_NONE;
    }

    void ConfigureGraphicBatch(UInstancedStaticMeshComponent* Component)
    {
        if (!Component) return;
        Component->SetMobility(EComponentMobility::Movable);
        Component->SetCollisionEnabled(ECollisionEnabled::NoCollision);
        Component->SetGenerateOverlapEvents(false);
        Component->SetCanEverAffectNavigation(false);
        Component->SetCastShadow(true);
        Component->SetReceivesDecals(false);
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
    }
}

ALBOneFactoryPressArtDirectionActor::ALBOneFactoryPressArtDirectionActor()
{
    PrimaryActorTick.bCanEverTick = false;
    SetActorEnableCollision(false);
    SetReplicates(false);
    Tags.AddUnique(GetArtDirectionTag());
    Tags.AddUnique(TEXT("LB.Provenance.NativePressArtDirectionV001"));

    SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
    SetRootComponent(SceneRoot);

    PressFloorPaint = CreateDefaultSubobject<ULBFactoryFloorMarkingComponent>(
        TEXT("PressFloorPaint"));
    PressFloorPaint->SetupAttachment(SceneRoot);

    OverheadStructure = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("OverheadHandlingStructure"));
    OverheadAccent = CreateDefaultSubobject<UInstancedStaticMeshComponent>(
        TEXT("OverheadHandlingAccent"));
    OverheadStructure->SetupAttachment(SceneRoot);
    OverheadAccent->SetupAttachment(SceneRoot);
    LBOneFactoryPressArtDirectionPrivate::ConfigureGraphicBatch(OverheadStructure);
    LBOneFactoryPressArtDirectionPrivate::ConfigureGraphicBatch(OverheadAccent);

    static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeFinder(
        TEXT("/Engine/BasicShapes/Cube.Cube"));
    PrimitiveCubeMesh = CubeFinder.Succeeded() ? CubeFinder.Object : nullptr;

    using namespace LBOneFactoryPressArtDirectionPrivate;
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> GreenFinder(
        PaletteMaterialPaths[CairnwellGreen]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> CharcoalFinder(
        PaletteMaterialPaths[FoundryCharcoal]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> SteelFinder(
        PaletteMaterialPaths[SteelGrey]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> WhiteFinder(
        PaletteMaterialPaths[WarmWhite]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> YellowFinder(
        PaletteMaterialPaths[SafetyYellow]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> RedFinder(
        PaletteMaterialPaths[SignalRed]);
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> PaleGreenFinder(
        PaletteMaterialPaths[PaleGreenZone]);
    PaletteCairnwellGreen = GreenFinder.Succeeded() ? GreenFinder.Object : nullptr;
    PaletteFoundryCharcoal = CharcoalFinder.Succeeded() ? CharcoalFinder.Object : nullptr;
    PaletteSteelGrey = SteelFinder.Succeeded() ? SteelFinder.Object : nullptr;
    PaletteWarmWhite = WhiteFinder.Succeeded() ? WhiteFinder.Object : nullptr;
    PaletteSafetyYellow = YellowFinder.Succeeded() ? YellowFinder.Object : nullptr;
    PaletteSignalRed = RedFinder.Succeeded() ? RedFinder.Object : nullptr;
    PalettePaleGreenZone = PaleGreenFinder.Succeeded() ? PaleGreenFinder.Object : nullptr;
}

void ALBOneFactoryPressArtDirectionActor::EndPlay(
    const EEndPlayReason::Type EndPlayReason)
{
    ClearArtDirection();
    Super::EndPlay(EndPlayReason);
}

FName ALBOneFactoryPressArtDirectionActor::GetArtDirectionTag()
{
    return TEXT("LB.OneFactory.PressArtDirection");
}

const TCHAR* ALBOneFactoryPressArtDirectionActor::GetArtDirectionClassPath()
{
    return TEXT("/Script/LineBossCarFactory.LBOneFactoryPressArtDirectionActor");
}

TArray<FSoftObjectPath>
ALBOneFactoryPressArtDirectionActor::GetRequiredNativeAssetPaths()
{
    using namespace LBOneFactoryPressArtDirectionPrivate;
    TArray<FSoftObjectPath> Result;
    Result.Reserve(1 + UE_ARRAY_COUNT(PaletteMaterialPaths));
    Result.Emplace(PaletteMasterPath);
    for (const TCHAR* Path : PaletteMaterialPaths)
    {
        Result.Emplace(Path);
    }
    return Result;
}

bool ALBOneFactoryPressArtDirectionActor::ValidateNativeArtDirectionReferences(
    const TArray<FSoftObjectPath>& AssetPaths, FString& OutReason)
{
    using namespace LBOneFactoryPressArtDirectionPrivate;
    const TArray<FSoftObjectPath> Expected = GetRequiredNativeAssetPaths();
    if (AssetPaths != Expected)
    {
        OutReason = TEXT("PRESS ART-DIRECTION NATIVE ASSET CLOSURE DRIFTED");
        return false;
    }
    for (const FSoftObjectPath& Path : AssetPaths)
    {
        const FString Value = Path.ToString();
        UObject* Object = Path.TryLoad();
        if (!Value.StartsWith(ArtDirectionRoot, ESearchCase::CaseSensitive)
            || !Object || !Cast<UMaterialInterface>(Object)
            || !Object->GetPathName().Equals(Value, ESearchCase::CaseSensitive))
        {
            OutReason = FString::Printf(TEXT(
                "PRESS ART-DIRECTION NATIVE MATERIAL DID NOT RESOLVE EXACTLY: %s"),
                *Value);
            return false;
        }
    }
    OutReason = TEXT("PRESS ART-DIRECTION V001 NATIVE PALETTE CLOSURE IS EXACT");
    return true;
}

bool ALBOneFactoryPressArtDirectionActor::ValidatePaletteLibrary(
    FString& OutReason) const
{
    using namespace LBOneFactoryPressArtDirectionPrivate;
    const UMaterialInterface* const Materials[] =
    {
        PaletteCairnwellGreen, PaletteFoundryCharcoal, PaletteSteelGrey,
        PaletteWarmWhite, PaletteSafetyYellow, PaletteSignalRed,
        PalettePaleGreenZone
    };
    if (UE_ARRAY_COUNT(Materials) != UE_ARRAY_COUNT(PaletteMaterialPaths))
    {
        OutReason = TEXT("PRESS ART-DIRECTION PALETTE LIBRARY SIZE DRIFTED");
        return false;
    }
    for (int32 Index = 0; Index < UE_ARRAY_COUNT(Materials); ++Index)
    {
        if (!Materials[Index] || !Materials[Index]->GetPathName().Equals(
                PaletteMaterialPaths[Index], ESearchCase::CaseSensitive))
        {
            OutReason = FString::Printf(TEXT(
                "PRESS ART-DIRECTION PALETTE MATERIAL %d DID NOT RESOLVE TO ITS EXACT PATH"),
                Index);
            return false;
        }
    }
    if (!PrimitiveCubeMesh)
    {
        OutReason = TEXT("PRESS ART-DIRECTION ENGINE CUBE MESH IS UNAVAILABLE");
        return false;
    }
    OutReason = TEXT("PRESS ART-DIRECTION PALETTE LIBRARY IS COMPLETE");
    return true;
}

bool ALBOneFactoryPressArtDirectionActor::ApplyPaletteOverrides(
    ALBOneFactoryPressStarterPresentationActor& Presentation, FString& OutReason)
{
    using namespace LBOneFactoryPressArtDirectionPrivate;
    MaterialOverrideBackups.Reset();
    TArray<UMeshComponent*> Components;
    Presentation.GetComponents<UMeshComponent>(Components);
    for (UMeshComponent* RawComponent : Components)
    {
        UStaticMeshComponent* Component = Cast<UStaticMeshComponent>(RawComponent);
        if (!Component || !Component->GetStaticMesh()
            || !Component->IsVisible() || Component->bHiddenInGame)
        {
            continue;
        }
        const TArray<FStaticMaterial>& Slots =
            Component->GetStaticMesh()->GetStaticMaterials();
        FMaterialOverrideBackup Backup;
        Backup.Component = Component;
        Backup.OverrideMaterials = Component->OverrideMaterials;

        bool bBackedUp = false;
        for (int32 SlotIndex = 0; SlotIndex < Slots.Num(); ++SlotIndex)
        {
            const FName SlotName = Slots[SlotIndex].MaterialSlotName;
            const int32 PaletteIndex = PaletteIndexForSlot(SlotName);
            if (PaletteIndex != INDEX_NONE)
            {
                UMaterialInterface* Palette[] =
                {
                    PaletteCairnwellGreen.Get(), PaletteFoundryCharcoal.Get(),
                    PaletteSteelGrey.Get(), PaletteWarmWhite.Get(),
                    PaletteSafetyYellow.Get(), PaletteSignalRed.Get(),
                    PalettePaleGreenZone.Get()
                };
                UMaterialInterface* Target = Palette[PaletteIndex];
                if (!Target)
                {
                    RestorePaletteOverrides();
                    OutReason = TEXT("PRESS ART-DIRECTION PALETTE TARGET IS NULL");
                    return false;
                }
                // Register the exact component override state before the
                // first mutation. A later unknown semantic slot must be able
                // to restore this partially traversed component too.
                if (!bBackedUp)
                {
                    MaterialOverrideBackups.Add(MoveTemp(Backup));
                    bBackedUp = true;
                }
                Component->SetMaterial(SlotIndex, Target);
            }
            else if (IsPaletteSemanticSlot(SlotName)
                && !IsKnownTechnicalSlot(SlotName))
            {
                RestorePaletteOverrides();
                OutReason = FString::Printf(TEXT(
                    "PRESS ART-DIRECTION REFUSED UNKNOWN SEMANTIC MATERIAL SLOT: %s"),
                    *SlotName.ToString());
                return false;
            }
        }
    }
    if (MaterialOverrideBackups.IsEmpty())
    {
        OutReason = TEXT("PRESS ART-DIRECTION DID NOT FIND ANY VISIBLE PALETTE SEMANTIC SLOTS");
        return false;
    }
    OutReason = FString::Printf(TEXT(
        "PRESS ART-DIRECTION PALETTE APPLIED TO %d VISIBLE NATIVE COMPONENTS"),
        MaterialOverrideBackups.Num());
    return true;
}

void ALBOneFactoryPressArtDirectionActor::RestorePaletteOverrides()
{
    for (const FMaterialOverrideBackup& Backup : MaterialOverrideBackups)
    {
        UMeshComponent* Component = Backup.Component.Get();
        if (!Component) continue;
        Component->EmptyOverrideMaterials();
        for (int32 Index = 0; Index < Backup.OverrideMaterials.Num(); ++Index)
        {
            Component->SetMaterial(Index, Backup.OverrideMaterials[Index]);
        }
#if WITH_EDITOR
        Component->CleanUpOverrideMaterials();
#endif
    }
    MaterialOverrideBackups.Reset();
}

void ALBOneFactoryPressArtDirectionActor::ConfigureFloorZones(
    const FTransform& TrainAnchor)
{
    using namespace LBOneFactoryPressArtDirectionPrivate;
    if (!PressFloorPaint) return;
    PressFloorPaint->ClearMarkings();
    PressFloorPaint->SetWorldTransform(TrainAnchor, false, nullptr,
        ETeleportType::TeleportPhysics);

    // Seven large, deliberately simple station fields deliver the readable
    // colour blocking from the approved concept. Their bounds are derived from
    // the train pitch rather than the frozen logical-item route markings.
    for (int32 Index = 0; Index < 7; ++Index)
    {
        const float Along = TrainPitchCm * (Index - 3);
        PressFloorPaint->AddFilledRectangle(FVector2D(0.0f, Along),
            FVector2D(950.0f, 610.0f), 1.5f,
            ELBFactoryFloorMarkingSemantic::PressZoneFill, 1.0f);
        PressFloorPaint->AddRectangleOutline(FVector2D(0.0f, Along),
            FVector2D(1025.0f, 690.0f), 1.75f, 45.0f,
            ELBFactoryFloorMarkingSemantic::PressCreamLane, 1.0f);
    }
    // Continuous -X operator corridor: cream is a literal brand token, while
    // the zone pads remain a separately named lightened Cairnwell derivative.
    PressFloorPaint->AddFilledRectangle(FVector2D(-1280.0f, 0.0f),
        FVector2D(240.0f, 5400.0f), 1.5f,
        ELBFactoryFloorMarkingSemantic::PressCreamLane, 1.0f);
}

void ALBOneFactoryPressArtDirectionActor::ConfigureOverheadHandling(
    const FTransform& TrainAnchor)
{
    if (!OverheadStructure || !OverheadAccent || !PrimitiveCubeMesh) return;
    OverheadStructure->ClearInstances();
    OverheadAccent->ClearInstances();
    OverheadStructure->SetStaticMesh(PrimitiveCubeMesh);
    OverheadAccent->SetStaticMesh(PrimitiveCubeMesh);
    OverheadStructure->SetMaterial(0, PaletteFoundryCharcoal);
    OverheadAccent->SetMaterial(0, PaletteSafetyYellow);
    OverheadStructure->SetWorldTransform(TrainAnchor, false, nullptr,
        ETeleportType::TeleportPhysics);
    OverheadAccent->SetWorldTransform(TrainAnchor, false, nullptr,
        ETeleportType::TeleportPhysics);

    const auto AddStructure = [this](const FVector& Location,
        const FVector& Scale)
    {
        OverheadStructure->AddInstance(FTransform(FQuat::Identity, Location, Scale));
    };
    const auto AddAccent = [this](const FVector& Location,
        const FVector& Scale)
    {
        OverheadAccent->AddInstance(FTransform(FQuat::Identity, Location, Scale));
    };

    // One parked bridge-crane / overhead-transfer silhouette: broad rails,
    // bridge, trolley and hook. It is deliberately static; no crane movement
    // is claimed without a source-authoritative route or range.
    for (const float Side : { -1.0f, 1.0f })
    {
        AddStructure(FVector(Side * 1180.0f, 0.0f, 870.0f),
            FVector(0.22f, 82.0f, 0.20f));
        for (const float End : { -1.0f, 1.0f })
        {
            AddStructure(FVector(Side * 1180.0f, End * 5250.0f, 435.0f),
                FVector(0.34f, 0.34f, 4.35f));
        }
    }
    AddStructure(FVector(0.0f, 700.0f, 835.0f), FVector(12.1f, 0.30f, 0.22f));
    AddStructure(FVector(0.0f, 700.0f, 620.0f), FVector(0.10f, 0.10f, 1.60f));
    AddAccent(FVector(0.0f, 700.0f, 790.0f), FVector(11.25f, 0.56f, 0.42f));
    AddAccent(FVector(0.0f, 700.0f, 735.0f), FVector(1.20f, 0.92f, 0.35f));
    AddAccent(FVector(0.0f, 700.0f, 455.0f), FVector(0.32f, 0.32f, 0.20f));

    OverheadStructure->SetVisibility(true, true);
    OverheadStructure->SetHiddenInGame(false, true);
    OverheadAccent->SetVisibility(true, true);
    OverheadAccent->SetHiddenInGame(false, true);
}

bool ALBOneFactoryPressArtDirectionActor::ConfigureFromPressPresentation(
    ALBOneFactoryPressStarterPresentationActor& Presentation,
    const FLBOneFactoryPressStarterLayoutState& Layout, FString& OutReason)
{
    using namespace LBOneFactoryPressArtDirectionPrivate;
    FString ValidationReason;
    if (!ULBOneFactoryPressStarterLayoutLibrary::ValidateStarterLayout(
            Layout, ValidationReason)
        || !Presentation.IsPresentationConfigured())
    {
        OutReason = FString::Printf(TEXT(
            "PRESS ART-DIRECTION REJECTED INVALID OR UNCONFIGURED PRESENTATION: %s"),
            *ValidationReason);
        return false;
    }
    if (!ValidatePaletteLibrary(ValidationReason))
    {
        OutReason = ValidationReason;
        return false;
    }
    FTransform PressStation = FTransform::Identity;
    if (!Presentation.GetConfiguredStationTransform(
            TEXT("OF_PRESS_TRAIN_001"), PressStation))
    {
        OutReason = TEXT("PRESS ART-DIRECTION COULD NOT RESOLVE THE LIVE TRAIN ANCHOR");
        return false;
    }
    const FTransform TrainAnchor(FQuat::Identity, TrainAggregateLocalLocationCm);
    const FTransform WorldTrainAnchor = TrainAnchor * PressStation;
    if (WorldTrainAnchor.ContainsNaN()
        || !WorldTrainAnchor.GetRotation().IsNormalized())
    {
        OutReason = TEXT("PRESS ART-DIRECTION TRAIN ANCHOR IS NOT FINITE");
        return false;
    }

    ClearArtDirection();
    if (!ApplyPaletteOverrides(Presentation, ValidationReason))
    {
        ClearArtDirection();
        OutReason = ValidationReason;
        return false;
    }
    ConfigureFloorZones(WorldTrainAnchor);
    ConfigureOverheadHandling(WorldTrainAnchor);
    if (GetFloorPaintCount() != ExpectedFloorPaintInstances
        || GetOverheadStructureInstanceCount() != ExpectedOverheadStructureInstances
        || GetOverheadAccentInstanceCount() != ExpectedOverheadAccentInstances)
    {
        ClearArtDirection();
        OutReason = TEXT("PRESS ART-DIRECTION GRAPHIC COMPOSITION COUNT DRIFTED");
        return false;
    }
    bConfigured = true;
    OutReason = FString::Printf(TEXT(
        "PRESS ART-DIRECTION V001 ACTIVE: %d PALETTE COMPONENTS, 7 LARGE FLOOR ZONES (%d PAINT INSTANCES), ONE STATIC OVERHEAD HANDLING SILHOUETTE"),
        MaterialOverrideBackups.Num(), GetFloorPaintCount());
    return true;
}

void ALBOneFactoryPressArtDirectionActor::ClearArtDirection()
{
    RestorePaletteOverrides();
    if (PressFloorPaint) PressFloorPaint->ClearMarkings();
    for (UInstancedStaticMeshComponent* Component : { OverheadStructure.Get(),
            OverheadAccent.Get() })
    {
        if (!Component) continue;
        Component->ClearInstances();
        Component->SetVisibility(false, true);
        Component->SetHiddenInGame(true, true);
    }
    bConfigured = false;
}

int32 ALBOneFactoryPressArtDirectionActor::GetFloorPaintCount() const
{
    return PressFloorPaint ? PressFloorPaint->GetMarkingCount() : 0;
}

int32 ALBOneFactoryPressArtDirectionActor::GetOverheadStructureInstanceCount() const
{
    return OverheadStructure ? OverheadStructure->GetInstanceCount() : 0;
}

int32 ALBOneFactoryPressArtDirectionActor::GetOverheadAccentInstanceCount() const
{
    return OverheadAccent ? OverheadAccent->GetInstanceCount() : 0;
}
