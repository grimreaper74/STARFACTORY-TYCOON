#include "LBControlRoomHUD.h"

#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/Texture2D.h"
#include "Engine/TextureRenderTarget2D.h"
#include "Blueprint/UserWidget.h"
#include "LBControlRoomPawn.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBPressTrainAStation.h"
#include "LBPressShopSupportFleetController.h"
#include "LBPressShopCampaignController.h"
#include "LBManagementPawn.h"
#include "LBManagementRootWidget.h"
#include "LBSettingsRootWidget.h"
#include "LBFactoryUIStateSubsystem.h"
#include "LBFactoryMachineBuilderSubsystem.h"
#include "LBFactoryBrandSubsystem.h"
#include "LBOneFactoryPlayerBuilderSubsystem.h"
#include "LBOneFactoryOperationsSubsystem.h"
#include "LBOneFactorySaveSubsystem.h"
#include "LBPlayerBuiltPressFlowController.h"
#include "EngineUtils.h"
#include "InputCoreTypes.h"
#include "UObject/StrongObjectPtr.h"

DEFINE_LOG_CATEGORY_STATIC(LogLineBossModernUI, Log, All);

void ALBControlRoomHUD::BeginPlay()
{
    Super::BeginPlay();
    EnsureModernOverviewWidget();
    SyncModernOverviewWidget();
}

void ALBControlRoomHUD::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (ManagementRootWidget)
    {
        ManagementRootWidget->RemoveFromParent();
        ManagementRootWidget = nullptr;
    }
    if (SettingsRootWidget)
    {
        SettingsRootWidget->CancelAndRevertPendingDisplayChange();
        SettingsRootWidget->RemoveFromParent();
        SettingsRootWidget = nullptr;
    }
    Super::EndPlay(EndPlayReason);
}

namespace
{
constexpr int32 MaximumVisibleFactoryCatalogueCards = 5;

struct FFactoryMachinePresentationCard
{
    ELBFactoryBuildMachineType Type = ELBFactoryBuildMachineType::InboundDeliveryDock;
    int32 ActionIndex = INDEX_NONE;
    bool bLocked = false;
    FString LockReason;
};

bool IsFactoryAreaMilestone(const ELBFactoryBuildMachineType Type)
{
    return Type == ELBFactoryBuildMachineType::BodyWeldLine
        || Type == ELBFactoryBuildMachineType::ECoatLine;
}

TArray<FFactoryMachinePresentationCard> BuildMachinePresentationCards(
    const ULBFactoryMachineBuilderSubsystem* Builder,
    const TArray<ELBFactoryBuildMachineType>& AvailableMachines)
{
    TArray<FFactoryMachinePresentationCard> Result;
    TArray<int32> RegularActions;
    for (int32 Index = 0; Index < AvailableMachines.Num(); ++Index)
        if (!IsFactoryAreaMilestone(AvailableMachines[Index])) RegularActions.Add(Index);

    // Keep both ordered area milestones visible on page one without hiding the familiar
    // first three press-shop choices. Placed milestones disappear; future milestones stay.
    const int32 LeadingRegularCount = FMath::Min(3, RegularActions.Num());
    for (int32 Index = 0; Index < LeadingRegularCount; ++Index)
        Result.Add(FFactoryMachinePresentationCard{
            AvailableMachines[RegularActions[Index]], RegularActions[Index], false, FString()});

    const ELBFactoryBuildMachineType Milestones[] = {
        ELBFactoryBuildMachineType::BodyWeldLine,
        ELBFactoryBuildMachineType::ECoatLine
    };
    for (const ELBFactoryBuildMachineType Type : Milestones)
    {
        const int32 ActionIndex = AvailableMachines.IndexOfByKey(Type);
        if (ActionIndex != INDEX_NONE)
        {
            Result.Add(FFactoryMachinePresentationCard{Type, ActionIndex, false, FString()});
            continue;
        }
        FString Reason;
        if (Builder) Builder->CanPlaceMachine(Type, Reason);
        if (!Reason.Contains(TEXT("ALREADY HAS"), ESearchCase::IgnoreCase))
            Result.Add(FFactoryMachinePresentationCard{Type, INDEX_NONE, true, Reason});
    }
    for (int32 Index = LeadingRegularCount; Index < RegularActions.Num(); ++Index)
        Result.Add(FFactoryMachinePresentationCard{
            AvailableMachines[RegularActions[Index]], RegularActions[Index], false, FString()});
    return Result;
}

const TCHAR* MachineProcessStageName(const ELBFactoryBuildMachineType Type)
{
    switch (Type)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock: return TEXT("PRESS / INBOUND");
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell: return TEXT("PRESS / PR002");
    case ELBFactoryBuildMachineType::DepackagingRobot: return TEXT("PRESS / PR004");
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("PRESS / PR005-PR010");
    case ELBFactoryBuildMachineType::PressTrain: return TEXT("PRESS / FORMING");
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("PRESS / INSPECTION");
    case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("WELD / INTAKE");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("WELD / BODY SHOP");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("PAINT / ED E-COAT");
    default: return TEXT("FACTORY");
    }
}

const TCHAR* MachinePurpose(const ELBFactoryBuildMachineType Type)
{
    switch (Type)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock: return TEXT("Unload four wrapped coils");
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell: return TEXT("Weigh, identify and inspect");
    case ELBFactoryBuildMachineType::DepackagingRobot: return TEXT("Remove coil packaging");
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("Prepare and stack blanks");
    case ELBFactoryBuildMachineType::PressTrain: return TEXT("Form vehicle panels");
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("Inspect formed panels");
    case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("Dispatch full stillages");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("Join panels into body-in-white");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("Dip and cure body shells");
    default: return TEXT("Factory process asset");
    }
}

const TCHAR* MachineInputFlow(const ELBFactoryBuildMachineType Type)
{
    switch (Type)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock: return TEXT("IN  DELIVERY LORRY");
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell:
    case ELBFactoryBuildMachineType::DepackagingRobot:
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("IN  WRAPPED COIL");
    case ELBFactoryBuildMachineType::PressTrain: return TEXT("IN  PREPARED BLANK");
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("IN  FORMED PANEL");
    case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("IN  FULL STILLAGE");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("IN  PANEL STILLAGES + BASE KIT");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("IN  BODY-IN-WHITE");
    default: return TEXT("IN  PROCESS MATERIAL");
    }
}

const TCHAR* MachineOutputFlow(const ELBFactoryBuildMachineType Type)
{
    switch (Type)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock:
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell:
    case ELBFactoryBuildMachineType::DepackagingRobot: return TEXT("OUT COIL / AGV HANDOFF");
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("OUT BLANK / ROLLER");
    case ELBFactoryBuildMachineType::PressTrain: return TEXT("OUT FORMED PANEL");
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("OUT INSPECTED PANEL");
    case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("OUT WELD SHOP INTAKE");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("OUT BODY-IN-WHITE");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("OUT E-COATED BODY");
    default: return TEXT("OUT PROCESS MATERIAL");
    }
}

const TCHAR* MachineRouteRequirement(const ELBFactoryBuildMachineType Type)
{
    switch (Type)
    {
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("AGV in | roller out");
    case ELBFactoryBuildMachineType::PressTrain:
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("Keep transfer path clear");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("189 m clear bay | body ports");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("60 x 30 m clear bay | FLT + body ports");
    default: return TEXT("Keep AGV handoff clear");
    }
}

const TCHAR* MachinePreviewKind(const ELBFactoryBuildMachineType Type)
{
    switch (Type)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock: return TEXT("DELIVERY");
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell: return TEXT("INSPECTION");
    case ELBFactoryBuildMachineType::DepackagingRobot: return TEXT("ROBOT");
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("PROCESS_LINE");
    case ELBFactoryBuildMachineType::PressTrain: return TEXT("PRESS");
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("PORTAL");
    case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("STILLAGE_DOCK");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("ED_LINE");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("BODY_WELD_LINE");
    default: return TEXT("MACHINE");
    }
}

const TCHAR* MachineEnvelopeLabel(const ELBFactoryBuildMachineType Type)
{
    // These full protected-envelope dimensions mirror the placement authority's
    // source contracts; they are decision facts, not invented prices or estimates.
    switch (Type)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock: return TEXT("ENVELOPE 14.3 x 18.2 m");
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell: return TEXT("ENVELOPE 3.8 x 3.9 m");
    case ELBFactoryBuildMachineType::DepackagingRobot: return TEXT("ENVELOPE 6.6 x 4.6 m");
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("ENVELOPE 15.0 x 26.0 m");
    case ELBFactoryBuildMachineType::PressTrain: return TEXT("ENVELOPE 15.0 x 72.8 m");
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("ENVELOPE 12.0 x 10.0 m");
    case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("ENVELOPE 9.0 x 7.0 m");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("ENVELOPE 189 m LINE");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("ENVELOPE 60.0 x 30.0 m");
    default: return TEXT("ENVELOPE FROM PLACEMENT GHOST");
    }
}

TArray<FString> WrapCatalogueText(const FString& Text, const int32 MaximumCharacters,
    const int32 MaximumLines)
{
    TArray<FString> Lines;
    TArray<FString> Words;
    Text.ParseIntoArrayWS(Words);
    FString Line;
    for (const FString& Word : Words)
    {
        if (!Line.IsEmpty() && Line.Len() + 1 + Word.Len() > MaximumCharacters)
        {
            Lines.Add(Line);
            Line.Reset();
            if (Lines.Num() == MaximumLines) break;
        }
        if (!Line.IsEmpty()) Line += TEXT(" ");
        Line += Word;
    }
    if (Lines.Num() < MaximumLines && !Line.IsEmpty()) Lines.Add(Line);
    return Lines;
}

const TCHAR* ManagementPageName(const ELBManagementPage Page)
{
    switch (Page)
    {
    case ELBManagementPage::Overview: return TEXT("OVERVIEW");
    case ELBManagementPage::FactoryBuild: return TEXT("BUILD");
    case ELBManagementPage::Production: return TEXT("ORDERS");
    case ELBManagementPage::PressTrains: return TEXT("ASSETS");
    case ELBManagementPage::SupportFleet: return TEXT("MAINT.");
    case ELBManagementPage::Research: return TEXT("RESEARCH");
    case ELBManagementPage::Analytics: return TEXT("ANALYTICS");
    default: return TEXT("UNKNOWN");
    }
}

FString FormatMoneyPence(const int64 Pence)
{
    const double Pounds = static_cast<double>(Pence) / 100.0;
    if (FMath::Abs(Pounds) >= 1000000.0)
        return FString::Printf(TEXT("GBP %.2fm"), Pounds / 1000000.0);
    if (FMath::Abs(Pounds) >= 1000.0)
        return FString::Printf(TEXT("GBP %.1fk"), Pounds / 1000.0);
    return FString::Printf(TEXT("GBP %.2f"), Pounds);
}

FString FormatPercent(const double Ratio)
{
    return FString::Printf(TEXT("%.1f%%"), FMath::Clamp(Ratio, 0.0, 1.0) * 100.0);
}

struct FLBHUDRect
{
    float X = 0.0f;
    float Y = 0.0f;
    float W = 0.0f;
    float H = 0.0f;

    bool Contains(const float ScreenX, const float ScreenY) const
    {
        return ScreenX >= X && ScreenX <= X + W
            && ScreenY >= Y && ScreenY <= Y + H;
    }

    FVector2D Centre() const
    {
        return FVector2D(X + W * 0.5f, Y + H * 0.5f);
    }
};

struct FLBManagementHUDLayout
{
    float PanelX = 0.0f;
    float PanelY = 0.0f;
    float PanelW = 0.0f;
    float PanelH = 0.0f;
    float HeaderH = 0.0f;
    float ContentX = 0.0f;
    float ContentY = 0.0f;
    float InformationLineStep = 30.0f;
    TArray<FLBHUDRect> PageTabs;
    TArray<FLBHUDRect> ActionRows;
};

FLBHUDReadabilityContract MakeHUDReadabilityContract(
    const float ViewWidth, const float ViewHeight)
{
    const float W = FMath::Max(1.0f, ViewWidth);
    const float H = FMath::Max(1.0f, ViewHeight);
    FLBHUDReadabilityContract Contract;
    // Canvas coordinates can be substantially larger than the physical PIE
    // window on a high-DPI desktop. Scale the complete 720p design contract,
    // not only the panel bounds, so Slate downsampling preserves readable ink.
    Contract.LayoutScale = FMath::Clamp(FMath::Min(W / 1280.0f, H / 720.0f),
        1.0f, 3.0f);
    const float LogicalW = W / Contract.LayoutScale;
    const float LogicalH = H / Contract.LayoutScale;
    Contract.bCompactMode = LogicalW < 1500.0f || LogicalH < 850.0f;
    const float S = Contract.LayoutScale;
    Contract.NormalTextScale = (Contract.bCompactMode ? 1.34f : 1.40f) * S;
    Contract.DetailTextScale = (Contract.bCompactMode ? 1.16f : 1.22f) * S;
    Contract.HeadingTextScale = (Contract.bCompactMode ? 0.92f : 1.0f) * S;
    Contract.ExpectedNormalTextPixelHeight = 16.0f * S;
    Contract.ExpectedDetailTextPixelHeight = 14.0f * S;
    Contract.ExpectedHeadingTextPixelHeight = 24.0f * S;
    Contract.MinimumInteractiveHeight = 44.0f * S;
    Contract.PersistentHUDHeight = FMath::Clamp(H * 0.09f, 65.0f * S, 78.0f * S);
    Contract.PersistentBounds = FBox2D(FVector2D(0.0f, 0.0f),
        FVector2D(W, Contract.PersistentHUDHeight));

    const float EdgeMargin = FMath::Clamp(W * 0.025f, 18.0f * S, 48.0f * S);
    const float ManagementW = FMath::Clamp(
        W * (Contract.bCompactMode ? 0.54f : 0.48f), 680.0f * S, 900.0f * S);
    const float ManagementX = W - ManagementW - EdgeMargin;
    const float ManagementY = FMath::Max(H * 0.075f,
        Contract.PersistentHUDHeight + 10.0f * S);
    const float ManagementBottomMargin = FMath::Clamp(H * 0.025f, 16.0f * S, 30.0f * S);
    const float AvailableManagementH = FMath::Max(0.0f,
        H - ManagementY - ManagementBottomMargin);
    const float DesiredManagementH = Contract.bCompactMode
        ? AvailableManagementH : FMath::Clamp(H * 0.80f, 600.0f * S, 820.0f * S);
    const float ManagementH = FMath::Min(DesiredManagementH, AvailableManagementH);
    Contract.ManagementBounds = FBox2D(FVector2D(ManagementX, ManagementY),
        FVector2D(ManagementX + ManagementW, ManagementY + ManagementH));

    const float BuildMarginX = FMath::Clamp(W * 0.035f, 24.0f * S, 64.0f * S);
    const float BuildBottomMargin = FMath::Clamp(H * 0.024f, 16.0f * S, 30.0f * S);
    // Five decision-ready cards need enough height for identity, silhouette, flow,
    // footprint and lock facts. The catalogue remains a bottom drawer, leaving the
    // upper factory view visible while avoiding the old 100 px text-only strips.
    const float BuildH = FMath::Clamp(H * (Contract.bCompactMode ? 0.57f : 0.48f),
        410.0f * S, 520.0f * S);
    const float BuildY = H - BuildBottomMargin - BuildH;
    Contract.FactoryBuildBounds = FBox2D(FVector2D(BuildMarginX, BuildY),
        FVector2D(W - BuildMarginX, BuildY + BuildH));

    const float BrandLayoutScale = S * FMath::Clamp(LogicalH / 900.0f, 0.92f, 1.0f);
    const float BrandW = FMath::Clamp(W * 0.64f, 680.0f * BrandLayoutScale,
        1080.0f * BrandLayoutScale);
    const float BrandH = 620.0f * BrandLayoutScale;
    const float BrandX = (W - BrandW) * 0.5f;
    const float BrandY = FMath::Max(8.0f * S, (H - BrandH) * 0.5f);
    Contract.FactoryBrandBounds = FBox2D(FVector2D(BrandX, BrandY),
        FVector2D(BrandX + BrandW, BrandY + BrandH));
    return Contract;
}

FLBProductionFlowHUDLayout MakeProductionFlowHUDLayout(
    const float ViewWidth, const float ViewHeight)
{
    const FLBHUDReadabilityContract Contract = MakeHUDReadabilityContract(
        ViewWidth, ViewHeight);
    const float S = Contract.LayoutScale;
    const float W = FMath::Max(1.0f, ViewWidth);
    const float H = FMath::Max(1.0f, ViewHeight);
    FLBProductionFlowHUDLayout Layout;
    const float MarginX = 22.0f * S;
    const float BottomMargin = 18.0f * S;
    const float CanvasH = 229.0f * S;
    const float CanvasY = H - BottomMargin - CanvasH;
    Layout.FlowCanvasBounds = FBox2D(FVector2D(MarginX, CanvasY),
        FVector2D(W - MarginX, CanvasY + CanvasH));
    const float TopH = 48.0f * S;
    // Overview is a low, unobtrusive live-flow drawer. Keeping its page rail in
    // the drawer (rather than over the world at eye level) leaves the factory
    // readable and gives mouse misses above the drawer back to world input.
    Layout.TopBarBounds = FBox2D(Layout.FlowCanvasBounds.Min,
        FVector2D(Layout.FlowCanvasBounds.Max.X, CanvasY + TopH));

    const float Pad = 18.0f * S;
    const float DetailW = 244.0f * S;
    const float DetailGap = 18.0f * S;
    const float StageX = MarginX + Pad;
    const float StageY = CanvasY + 58.0f * S;
    const float StageW = Layout.FlowCanvasBounds.GetSize().X
        - Pad * 2.0f - DetailW - DetailGap;
    const float StageH = CanvasH - 70.0f * S;
    Layout.StageLaneBounds = FBox2D(FVector2D(StageX, StageY),
        FVector2D(StageX + StageW, StageY + StageH));
    Layout.DetailBounds = FBox2D(FVector2D(StageX + StageW + DetailGap, StageY),
        FVector2D(W - MarginX - Pad, StageY + StageH));

    constexpr int32 StageCount = 6;
    const float CardGap = 11.0f * S;
    // FBox2D::IsInside is strictly exclusive at every edge. Keep the cards a
    // scaled pixel inside the semantic lane so draw geometry and hit geometry
    // remain identical while the public containment contract is actually true.
    const float CardInset = 1.0f * S;
    const float CardLaneW = StageW - 2.0f * CardInset;
    const float CardW = (CardLaneW - CardGap * (StageCount - 1)) / StageCount;
    for (int32 Index = 0; Index < StageCount; ++Index)
    {
        const FVector2D Min(StageX + CardInset
                + Index * (CardW + CardGap), StageY + CardInset);
        Layout.StageCardBounds.Add(FBox2D(Min,
            FVector2D(Min.X + CardW, StageY + StageH - CardInset)));
    }
    Layout.PrimaryActionBounds = FBox2D(
        FVector2D(Layout.DetailBounds.Min.X + 18.0f * S,
            Layout.DetailBounds.Max.Y - 52.0f * S),
        FVector2D(Layout.DetailBounds.Max.X - 10.0f * S,
            Layout.DetailBounds.Max.Y - 8.0f * S));
    return Layout;
}

TArray<FBox2D> MakeProductionFlowPageTabBounds(
    const FLBProductionFlowHUDLayout& Layout, const float Scale)
{
    TArray<FBox2D> Result;
    constexpr int32 PageCount = static_cast<int32>(ELBManagementPage::PageCount);
    const float TitleReserve = 174.0f * Scale;
    const float TabsX = Layout.TopBarBounds.Min.X + TitleReserve;
    const float AvailableW = FMath::Max(1.0f,
        Layout.TopBarBounds.Max.X - TabsX);
    const float TabW = AvailableW / static_cast<float>(PageCount);
    for (int32 Index = 0; Index < PageCount; ++Index)
    {
        const FVector2D Min(TabsX + Index * TabW,
            Layout.TopBarBounds.Min.Y);
        Result.Add(FBox2D(Min, FVector2D(Min.X + TabW - 2.0f * Scale,
            Layout.TopBarBounds.Max.Y)));
    }
    return Result;
}

const TCHAR* ProductionFlowThumbnailKey(const FName StageId)
{
    if (StageId == TEXT("COIL_INTAKE")) return TEXT("CoilIntake");
    if (StageId == TEXT("BLANK_BUFFER")) return TEXT("BlankBuffer");
    if (StageId == TEXT("TRANSFER_PRESS")) return TEXT("TransferPress");
    if (StageId == TEXT("PANEL_STILLAGES")) return TEXT("PanelStillages");
    if (StageId == TEXT("BODY_WELD")) return TEXT("BodyWeld");
    if (StageId == TEXT("ED_COAT")) return TEXT("EDCoat");
    return nullptr;
}

UTexture2D* ResolveProductionFlowThumbnail(const FName StageId)
{
    const TCHAR* Key = ProductionFlowThumbnailKey(StageId);
    if (!Key) return nullptr;

    static TMap<FName, TStrongObjectPtr<UTexture2D>> CachedTextures;
    static TSet<FName> AttemptedLoads;
    if (const TStrongObjectPtr<UTexture2D>* Cached = CachedTextures.Find(StageId))
        if (Cached->IsValid()) return Cached->Get();
    if (AttemptedLoads.Contains(StageId)) return nullptr;
    AttemptedLoads.Add(StageId);

    const FString AssetName = FString::Printf(TEXT("T_LB_UI_PF_%s_v003"), Key);
    const FSoftObjectPath AssetPath(FString::Printf(
        TEXT("/Game/LineBoss/UI/ProductionFlow/v003/%s.%s"),
        *AssetName, *AssetName));
    UTexture2D* Texture = Cast<UTexture2D>(AssetPath.TryLoad());
    if (Texture) CachedTextures.Add(StageId, TStrongObjectPtr<UTexture2D>(Texture));
    return Texture;
}

bool ResolveProductionStagePlacement(const FName StageId,
    bool& bOutStorage, ELBFactoryBuildMachineType& OutMachine,
    ELBPressShopStorageType& OutStorage)
{
    bOutStorage = false;
    if (StageId == TEXT("COIL_INTAKE"))
        OutMachine = ELBFactoryBuildMachineType::InboundDeliveryDock;
    else if (StageId == TEXT("TRANSFER_PRESS"))
        OutMachine = ELBFactoryBuildMachineType::PressTrain;
    else if (StageId == TEXT("BODY_WELD"))
        OutMachine = ELBFactoryBuildMachineType::BodyWeldLine;
    else if (StageId == TEXT("ED_COAT"))
        OutMachine = ELBFactoryBuildMachineType::ECoatLine;
    else if (StageId == TEXT("BLANK_BUFFER"))
    {
        bOutStorage = true;
        OutStorage = ELBPressShopStorageType::PreparedBlanks;
    }
    else if (StageId == TEXT("PANEL_STILLAGES"))
    {
        bOutStorage = true;
        OutStorage = ELBPressShopStorageType::FinishedPanelStillages;
    }
    else return false;
    return true;
}

FLBManagementHUDLayout MakeManagementHUDLayout(const float ViewWidth,
    const float ViewHeight, const float PersistentHeight, const int32 InformationLineCount,
    const int32 ActionCount)
{
    const FLBHUDReadabilityContract Contract = MakeHUDReadabilityContract(
        ViewWidth, ViewHeight);
    FLBManagementHUDLayout Layout;
    const float S = Contract.LayoutScale;
    Layout.PanelX = Contract.ManagementBounds.Min.X;
    Layout.PanelY = FMath::Max(Contract.ManagementBounds.Min.Y, PersistentHeight + 10.0f * S);
    Layout.PanelW = Contract.ManagementBounds.GetSize().X;
    Layout.PanelH = Contract.ManagementBounds.Max.Y - Layout.PanelY;
    Layout.HeaderH = (Contract.bCompactMode ? 64.0f : 72.0f) * S;
    Layout.InformationLineStep = (Contract.bCompactMode ? 30.0f : 32.0f) * S;
    const float TabsY = Layout.PanelY + Layout.HeaderH + 8.0f * S;
    const int32 PageCount = static_cast<int32>(ELBManagementPage::PageCount);
    const float TabW = Layout.PanelW / static_cast<float>(PageCount);
    for (int32 Index = 0; Index < PageCount; ++Index)
        Layout.PageTabs.Add(FLBHUDRect{
            Layout.PanelX + Index * TabW, TabsY, TabW - 2.0f * S,
            Contract.MinimumInteractiveHeight});
    Layout.ContentX = Layout.PanelX + 24.0f * S;
    Layout.ContentY = TabsY + Contract.MinimumInteractiveHeight + 10.0f * S;
    const float ActionTop = Layout.ContentY
        + static_cast<float>(InformationLineCount) * Layout.InformationLineStep + 8.0f * S;
    const bool bTwoActionColumns = Contract.bCompactMode && ActionCount > 5;
    const int32 ActionRowsPerColumn = bTwoActionColumns
        ? FMath::DivideAndRoundUp(ActionCount, 2) : ActionCount;
    const float ActionGap = 10.0f * S;
    const float ActionW = bTwoActionColumns
        ? (Layout.PanelW - 48.0f * S - ActionGap) * 0.5f : Layout.PanelW - 48.0f * S;
    for (int32 Index = 0; Index < ActionCount; ++Index)
    {
        const int32 Column = bTwoActionColumns ? Index / ActionRowsPerColumn : 0;
        const int32 Row = bTwoActionColumns ? Index % ActionRowsPerColumn : Index;
        Layout.ActionRows.Add(FLBHUDRect{
            Layout.ContentX + Column * (ActionW + ActionGap),
            ActionTop + Row * 50.0f * S, ActionW, Contract.MinimumInteractiveHeight});
    }
    return Layout;
}

struct FLBFactoryBuildHUDLayout
{
    float PanelX = 0.0f;
    float PanelY = 0.0f;
    float PanelW = 0.0f;
    float PanelH = 0.0f;
    FLBHUDRect ProfileButton;
    FLBHUDRect PreviousPageButton;
    FLBHUDRect NextPageButton;
    TArray<FLBHUDRect> PageTabs;
    TArray<FLBHUDRect> CategoryTabs;
    TArray<FLBHUDRect> Cards;
};

FLBFactoryBuildHUDLayout MakeFactoryBuildHUDLayout(
    const float ViewWidth, const float ViewHeight)
{
    const FLBHUDReadabilityContract Contract = MakeHUDReadabilityContract(
        ViewWidth, ViewHeight);
    FLBFactoryBuildHUDLayout Layout;
    const float S = Contract.LayoutScale;
    Layout.PanelX = Contract.FactoryBuildBounds.Min.X;
    Layout.PanelY = Contract.FactoryBuildBounds.Min.Y;
    Layout.PanelW = Contract.FactoryBuildBounds.GetSize().X;
    Layout.PanelH = Contract.FactoryBuildBounds.GetSize().Y;
    Layout.ProfileButton = {Layout.PanelX + Layout.PanelW - 204.0f * S,
        Layout.PanelY + 2.0f * S, 192.0f * S, Contract.MinimumInteractiveHeight};
    Layout.PreviousPageButton = {Layout.PanelX + Layout.PanelW - 430.0f * S,
        Layout.PanelY + 2.0f * S, 96.0f * S, Contract.MinimumInteractiveHeight};
    Layout.NextPageButton = {Layout.PanelX + Layout.PanelW - 326.0f * S,
        Layout.PanelY + 2.0f * S, 96.0f * S, Contract.MinimumInteractiveHeight};
    const float PageTabsY = Layout.PanelY + 52.0f * S;
    const int32 PageCount = static_cast<int32>(ELBManagementPage::PageCount);
    const float PageTabW = Layout.PanelW / static_cast<float>(PageCount);
    for (int32 Index = 0; Index < PageCount; ++Index)
        Layout.PageTabs.Add(FLBHUDRect{Layout.PanelX + Index * PageTabW, PageTabsY,
            PageTabW - 3.0f * S, Contract.MinimumInteractiveHeight});
    const float CategoryY = PageTabsY + Contract.MinimumInteractiveHeight + 6.0f * S;
    const float CategoryW = Layout.PanelW / 4.0f;
    for (int32 Index = 0; Index < 4; ++Index)
        Layout.CategoryTabs.Add(FLBHUDRect{Layout.PanelX + Index * CategoryW, CategoryY,
            CategoryW - 3.0f * S, Contract.MinimumInteractiveHeight});
    const float CardsY = CategoryY + Contract.MinimumInteractiveHeight + 8.0f * S;
    const float Gap = 12.0f * S;
    const float CardW = (Layout.PanelW
        - static_cast<float>(MaximumVisibleFactoryCatalogueCards - 1) * Gap)
        / static_cast<float>(MaximumVisibleFactoryCatalogueCards);
    for (int32 Index = 0; Index < MaximumVisibleFactoryCatalogueCards; ++Index)
        Layout.Cards.Add(FLBHUDRect{
            Layout.PanelX + Index * (CardW + Gap), CardsY, CardW,
            FMath::Clamp(Layout.PanelY + Layout.PanelH - CardsY - 14.0f * S,
                220.0f * S, 286.0f * S)});
    return Layout;
}

// The 2040 is the sole approved first-vehicle programme. Hydrogen remains a later
// derivative, so the live order editor truthfully offers only the initial BEV here.
const FName PreProductionVehicleModels[] = { TEXT("CAIRNWELL_2040") };
const TCHAR* PreProductionVehicleDisplayNames[] = {
    TEXT("CAIRNWELL 2040 / BEV PRE-PRODUCTION")
};
static_assert(UE_ARRAY_COUNT(PreProductionVehicleModels)
    == UE_ARRAY_COUNT(PreProductionVehicleDisplayNames));
const FName FuturePanelTypes[] = {
    TEXT("DOOR_FRONT_LEFT"), TEXT("DOOR_FRONT_RIGHT"),
    TEXT("DOOR_REAR_LEFT"), TEXT("DOOR_REAR_RIGHT"),
    TEXT("FENDER_FRONT_LEFT"), TEXT("FENDER_FRONT_RIGHT"),
    TEXT("HOOD_PANEL"), TEXT("ROOF_PANEL"),
    TEXT("QUARTER_PANEL_LEFT"), TEXT("QUARTER_PANEL_RIGHT"),
    TEXT("TAILGATE_PANEL")
};

const FLinearColor FactoryLiverySwatches[] = {
    FLinearColor(0.035f, 0.36f, 0.16f, 1.0f), // Cairnwell green
    FLinearColor(0.025f, 0.22f, 0.55f, 1.0f), // production blue
    FLinearColor(0.55f, 0.055f, 0.045f, 1.0f), // deep red
    FLinearColor(0.80f, 0.24f, 0.025f, 1.0f), // orange
    FLinearColor(0.30f, 0.075f, 0.48f, 1.0f), // violet
    FLinearColor(0.38f, 0.43f, 0.46f, 1.0f), // steel
    FLinearColor(0.055f, 0.07f, 0.075f, 1.0f), // charcoal frame
    FLinearColor(0.55f, 0.50f, 0.40f, 1.0f) // warm alloy
};
constexpr int32 FactoryLiverySwatchCount = UE_ARRAY_COUNT(FactoryLiverySwatches);

int32 FindClosestFactoryLiverySwatch(const FLinearColor& Colour)
{
    int32 BestIndex = 0;
    float BestDistance = MAX_flt;
    for (int32 Index = 0; Index < FactoryLiverySwatchCount; ++Index)
    {
        const FVector Delta(
            Colour.R - FactoryLiverySwatches[Index].R,
            Colour.G - FactoryLiverySwatches[Index].G,
            Colour.B - FactoryLiverySwatches[Index].B);
        const float Distance = Delta.SizeSquared();
        if (Distance < BestDistance)
        {
            BestDistance = Distance;
            BestIndex = Index;
        }
    }
    return BestIndex;
}

struct FLBFactoryBrandEditorLayout
{
    float Scale = 1.0f;
    float BoxX = 0.0f;
    float BoxY = 0.0f;
    float BoxW = 0.0f;
    float BoxH = 0.0f;
    float NameY = 0.0f;
    float PrimaryY = 0.0f;
    float SecondaryY = 0.0f;
    float SwatchW = 0.0f;
    float SwatchH = 0.0f;
    float SwatchGap = 0.0f;
    float PreviewY = 0.0f;
    float ContinueY = 0.0f;
};

FLBFactoryBrandEditorLayout MakeFactoryBrandEditorLayout(
    const float ViewWidth, const float ViewHeight)
{
    const FLBHUDReadabilityContract Contract = MakeHUDReadabilityContract(
        ViewWidth, ViewHeight);
    FLBFactoryBrandEditorLayout Layout;
    Layout.Scale = Contract.LayoutScale * FMath::Clamp(
        (ViewHeight / Contract.LayoutScale) / 900.0f, 0.92f, 1.0f);
    Layout.BoxW = Contract.FactoryBrandBounds.GetSize().X;
    Layout.BoxH = Contract.FactoryBrandBounds.GetSize().Y;
    Layout.BoxX = Contract.FactoryBrandBounds.Min.X;
    Layout.BoxY = Contract.FactoryBrandBounds.Min.Y;
    Layout.NameY = Layout.BoxY + 92.0f * Layout.Scale;
    Layout.PrimaryY = Layout.BoxY + 194.0f * Layout.Scale;
    Layout.SecondaryY = Layout.BoxY + 286.0f * Layout.Scale;
    Layout.SwatchGap = 10.0f * Layout.Scale;
    Layout.SwatchH = 48.0f * Layout.Scale;
    Layout.SwatchW = (Layout.BoxW - 48.0f * Layout.Scale
        - static_cast<float>(FactoryLiverySwatchCount - 1) * Layout.SwatchGap)
        / static_cast<float>(FactoryLiverySwatchCount);
    Layout.PreviewY = Layout.BoxY + 366.0f * Layout.Scale;
    Layout.ContinueY = Layout.BoxY + 548.0f * Layout.Scale;
    return Layout;
}

const TCHAR* OrderStateName(const ELBControlRoomOrderState State)
{
    switch (State)
    {
    case ELBControlRoomOrderState::Draft: return TEXT("DRAFT");
    case ELBControlRoomOrderState::Ready: return TEXT("READY");
    case ELBControlRoomOrderState::Running: return TEXT("RUNNING");
    case ELBControlRoomOrderState::Paused: return TEXT("PAUSED");
    case ELBControlRoomOrderState::Completed: return TEXT("COMPLETED");
    case ELBControlRoomOrderState::Held: return TEXT("HELD");
    default: return TEXT("UNKNOWN");
    }
}

const TCHAR* StorageTypeName(const ELBPressShopStorageType Type)
{
    switch (Type)
    {
    // Legacy serialized enum value 0 now represents the inbound wrapped-coil
    // buffer. Keep the value stable for existing saves while presenting the
    // corrected player-facing process state.
    case ELBPressShopStorageType::BareCoils: return TEXT("WRAPPED COIL STORAGE");
    case ELBPressShopStorageType::PreparedBlanks: return TEXT("PREPARED BLANK BUFFER");
    case ELBPressShopStorageType::FinishedPanelStillages: return TEXT("FULL PRESSED-PANEL STILLAGE STORE");
    case ELBPressShopStorageType::Scrap: return TEXT("SCRAP STORAGE");
    case ELBPressShopStorageType::MaintenanceParts: return TEXT("MAINTENANCE PARTS");
    case ELBPressShopStorageType::Quarantine: return TEXT("QUARANTINE STORAGE");
    case ELBPressShopStorageType::EmptyPanelStillages: return TEXT("EMPTY STILLAGE RETURN STORE");
    default: return TEXT("UNKNOWN STORAGE");
    }
}

const TCHAR* MachineTypeName(const ELBFactoryBuildMachineType Type)
{
    switch (Type)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock: return TEXT("INBOUND COIL DELIVERY CELL");
    case ELBFactoryBuildMachineType::DepackagingRobot: return TEXT("PR-004 DEPACKAGING ROBOT");
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell: return TEXT("PR-002 COIL WEIGH / INSPECTION");
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("PR005-PR010 COIL PREPARATION LINE");
    case ELBFactoryBuildMachineType::PressTrain: return TEXT("COMPLETE PRESS TRAIN");
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("ROBOTIC UNLOAD / INSPECTION CELL");
    case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("WELD SHOP STILLAGE INTAKE");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("COMPLETE 189 m ED / E-COAT LINE");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("COMPLETE BODY WELD LINE");
    default: return TEXT("UNKNOWN MACHINE");
    }
}

const TCHAR* InfrastructureTypeName(const ELBFactoryAGVInfrastructureType Type)
{
    switch (Type)
    {
    case ELBFactoryAGVInfrastructureType::PedestrianWalkway: return TEXT("PEDESTRIAN WALKWAY");
    case ELBFactoryAGVInfrastructureType::PedestrianCrossing: return TEXT("PEDESTRIAN CROSSING");
    case ELBFactoryAGVInfrastructureType::SafetyFence: return TEXT("SAFETY FENCE");
    case ELBFactoryAGVInfrastructureType::AGVRouteSegment: return TEXT("AGV ROUTE SEGMENT");
    case ELBFactoryAGVInfrastructureType::RouteWaypoint: return TEXT("AGV ROUTE WAYPOINT");
    case ELBFactoryAGVInfrastructureType::WaitPoint: return TEXT("AGV WAIT BAY");
    case ELBFactoryAGVInfrastructureType::ChargingStation: return TEXT("AGV CHARGING STATION");
    case ELBFactoryAGVInfrastructureType::PressTrainHandoff: return TEXT("PRESS-TRAIN HANDOFF");
    default: return TEXT("UNKNOWN INFRASTRUCTURE");
    }
}

const TCHAR* InfrastructureProvenanceName(const ELBFactoryInfrastructureProvenance Provenance)
{
    switch (Provenance)
    {
    case ELBFactoryInfrastructureProvenance::Automatic: return TEXT("AUTOMATIC");
    case ELBFactoryInfrastructureProvenance::PlayerEditedAutomatic: return TEXT("AUTOMATIC / PLAYER EDITED");
    default: return TEXT("PLAYER PLACED");
    }
}
}

FLBHUDReadabilityContract ALBControlRoomHUD::GetReadabilityContract(
    const float ViewWidth, const float ViewHeight)
{
    return MakeHUDReadabilityContract(ViewWidth, ViewHeight);
}

FLBProductionFlowHUDLayout ALBControlRoomHUD::GetProductionFlowLayout(
    const float ViewWidth, const float ViewHeight)
{
    return MakeProductionFlowHUDLayout(ViewWidth, ViewHeight);
}

bool ALBControlRoomHUD::GetProductionFlowStageHitRect(const int32 StageIndex,
    const float ViewWidth, const float ViewHeight, FBox2D& OutScreenRect) const
{
    OutScreenRect = FBox2D(ForceInit);
    const FLBProductionFlowHUDLayout Layout = MakeProductionFlowHUDLayout(
        ViewWidth, ViewHeight);
    if (!Layout.StageCardBounds.IsValidIndex(StageIndex)) return false;
    OutScreenRect = Layout.StageCardBounds[StageIndex];
    return true;
}

bool ALBControlRoomHUD::GetProductionFlowPrimaryActionHitRect(
    const float ViewWidth, const float ViewHeight, FBox2D& OutScreenRect) const
{
    OutScreenRect = MakeProductionFlowHUDLayout(ViewWidth, ViewHeight)
        .PrimaryActionBounds;
    return OutScreenRect.bIsValid;
}

FLinearColor ALBControlRoomHUD::ChooseReadableTextColour(const FLinearColor& Background)
{
    // Relative luminance 0.19 is the crossover where this near-black ink gives
    // more contrast than the existing off-white. Keep both choices tied to the
    // HUD palette so this improves legibility without globally brightening it.
    static const FLinearColor LightInk(0.96f, 0.98f, 0.96f, 1.0f);
    static const FLinearColor DarkInk(0.002f, 0.006f, 0.007f, 1.0f);
    return Background.GetLuminance() >= 0.19f ? DarkInk : LightInk;
}

float ALBControlRoomHUD::GetPersistentHUDHeight() const
{
    int32 ViewWidth = 0;
    int32 ViewHeight = 0;
    if (const APlayerController* PC = GetOwningPlayerController())
        PC->GetViewportSize(ViewWidth, ViewHeight);
    return MakeHUDReadabilityContract(static_cast<float>(ViewWidth),
        static_cast<float>(ViewHeight)).PersistentHUDHeight;
}

// Retired together with the Canvas alert strip.
#if 0
bool ALBControlRoomHUD::HandlePersistentHUDClick(const float ScreenX, const float ScreenY)
{
    if (IsCCTVFeedVisible() || !GetWorld()) return false;

    int32 ViewW = 0;
    int32 ViewH = 0;
    if (const APlayerController* PC = GetOwningPlayerController()) PC->GetViewportSize(ViewW, ViewH);
    if (ViewW <= 0 || ViewH <= 0) return false;

    const float AlertCellX = static_cast<float>(ViewW) * 0.85f;
    if (ScreenX < AlertCellX || ScreenX > static_cast<float>(ViewW)
        || ScreenY < 0.0f || ScreenY > GetPersistentHUDHeight())
    {
        return false;
    }

    ULBFactoryUIStateSubsystem* UIState = GetWorld()->GetSubsystem<ULBFactoryUIStateSubsystem>();
    if (!UIState || UIState->GetSnapshot().Alerts.IsEmpty()) return false;

    if (ALBManagementPawn* ManagementPawn = Cast<ALBManagementPawn>(GetOwningPawn()))
    {
        ManagementPawn->JumpToTopFactoryAlert();
        return true;
    }
    return false;
}
#endif

// Retired Canvas implementation. The active HUD is UMG-only; this block is
// excluded from every build while legacy geometry-only tests are migrated.
#if 0
void ALBControlRoomHUD::DrawPersistentFactoryHUD()
{
    UWorld* World = GetWorld();
    if (!Canvas || !World || IsCCTVFeedVisible()) return;

    ULBFactoryUIStateSubsystem* UIState = World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    if (!UIState) return;
    const FLBFactoryUIStateSnapshot& Snapshot = UIState->GetSnapshot();
    const FLBFactoryUIAlertSnapshot* TopAlert = Snapshot.GetTopAlert();

    const float W = static_cast<float>(Canvas->SizeX);
    const float H = static_cast<float>(Canvas->SizeY);
    const FLBHUDReadabilityContract Readability = MakeHUDReadabilityContract(W, H);
    const float S = Readability.LayoutScale;
    const float StripH = GetPersistentHUDHeight();
    const float UIScale = S;
    const float SmallScale = Readability.NormalTextScale;
    const float DetailScale = Readability.DetailTextScale;
    const float Pad = 16.0f * S;

    const ULBFactoryBrandSubsystem* Brand = World->GetSubsystem<ULBFactoryBrandSubsystem>();
    const FLinearColor Primary = Brand ? Brand->GetPrimaryColour()
        : FLinearColor(0.035f, 0.36f, 0.16f, 1.0f);
    const FLinearColor Accent = Brand ? Brand->GetSafetyAccentColour()
        : FLinearColor(1.0f, 0.62f, 0.035f, 1.0f);
    const FString FactoryName = Brand ? Brand->GetFactoryName().ToUpper() : TEXT("CAIRNWELL AUTOMOTIVE");
    const FString StripBrand = Readability.bCompactMode
        ? FactoryName.Left(16)
        : FactoryName;
    const FLinearColor Strip(0.004f, 0.024f, 0.022f, 0.95f);
    const FLinearColor Cell(0.012f, 0.047f, 0.042f, 0.93f);
    const FLinearColor Divider(0.28f, 0.48f, 0.43f, 0.52f);
    const FLinearColor White(0.93f, 0.97f, 0.94f, 1.0f);
    const FLinearColor Muted(0.62f, 0.75f, 0.70f, 1.0f);
    const FLinearColor Green(0.14f, 0.86f, 0.49f, 1.0f);
    const FLinearColor Warning(1.0f, 0.63f, 0.06f, 1.0f);
    const FLinearColor Critical(0.96f, 0.16f, 0.09f, 1.0f);
    UFont* Small = GEngine ? GEngine->GetSmallFont() : nullptr;
    UFont* Large = GEngine ? GEngine->GetLargeFont() : nullptr;

    // Stable proportional cells preserve the approved compact silhouette from 1280p upward.
    const float BrandX = 0.0f;
    const float OrderX = W * 0.18f;
    const float ProgressX = W * 0.41f;
    const float OperationsX = W * 0.57f;
    const float HealthX = W * 0.70f;
    const float AlertX = W * 0.85f;
    const float CellTop = 3.0f * S;
    const float CellH = StripH - 6.0f * S;

    DrawRect(Strip, 0.0f, 0.0f, W, StripH);
    DrawRect(Cell, BrandX + 3.0f * S, CellTop, AlertX - 6.0f * S, CellH);
    DrawRect(Primary.CopyWithNewOpacity(0.92f), 0.0f,
        StripH - 3.0f * S, W, 3.0f * S);
    for (const float X : {OrderX, ProgressX, OperationsX, HealthX, AlertX})
    {
        DrawLine(X, CellTop, X, StripH - 3.0f * S, Divider, FMath::Max(1.0f, S));
    }

    FString FactoryStatus = TEXT("READY");
    FLinearColor StatusColour = Green;
    if (Snapshot.FaultCount > 0)
    {
        FactoryStatus = TEXT("FAULT");
        StatusColour = Critical;
    }
    else if (Snapshot.WaitingCount > 0 || TopAlert)
    {
        FactoryStatus = TEXT("ATTENTION");
        StatusColour = Warning;
    }
    else if (Snapshot.RunningCount > 0)
    {
        FactoryStatus = TEXT("RUNNING");
    }
    else if (Snapshot.OperationalAssetCount == 0)
    {
        FactoryStatus = TEXT("SETUP");
        StatusColour = Muted;
    }

    if (Large)
    {
        DrawText(StripBrand.Left(28), White, BrandX + Pad, 9.0f * S, Large,
            Readability.HeadingTextScale, false);
    }
    if (Small)
    {
        DrawText(FString::Printf(TEXT("STATUS  %s"), *FactoryStatus), StatusColour,
            BrandX + Pad, StripH - 27.0f * S, Small, DetailScale, false);
    }

    if (Small)
    {
        if (Snapshot.Order.bHasActiveOrder)
        {
            FString Vehicle = Snapshot.Order.VehicleModelId.ToString();
            FString Panel = Snapshot.Order.PanelTypeId.ToString();
            Vehicle.ReplaceInline(TEXT("_"), TEXT(" "));
            Panel.ReplaceInline(TEXT("_"), TEXT(" "));
            DrawText(FString::Printf(TEXT("ORDER  %s"), *Snapshot.Order.OrderId.ToString()),
                White, OrderX + Pad, 10.0f * S, Small, SmallScale, false);
            DrawText(FString::Printf(TEXT("%s / %s"), *Vehicle, *Panel).Left(40),
                Muted, OrderX + Pad, StripH - 27.0f * S, Small, DetailScale, false);
        }
        else
        {
            DrawText(TEXT("NEXT OBJECTIVE"), Green, OrderX + Pad, 10.0f * S,
                Small, SmallScale, false);
            DrawText(Snapshot.Order.Objective.Left(
                Readability.bCompactMode ? 30 : 43), Muted,
                OrderX + Pad, StripH - 27.0f * S, Small, DetailScale, false);
        }

        const int32 Requested = FMath::Max(0, Snapshot.Order.RequestedQuantity);
        const int32 Issued = FMath::Clamp(Snapshot.Order.IssuedQuantity, 0, FMath::Max(Requested, 0));
        DrawText(FString::Printf(TEXT("ISSUED  %d / %d"), Issued, Requested),
            White, ProgressX + Pad, 10.0f * S, Small, SmallScale, false);
        const float ProgressBarX = ProgressX + Pad;
        const float ProgressBarW = FMath::Max(40.0f * S, OperationsX - ProgressBarX - Pad);
        const float ProgressBarY = StripH - 20.0f * S;
        DrawRect(FLinearColor(0.07f, 0.11f, 0.105f, 0.98f),
            ProgressBarX, ProgressBarY, ProgressBarW, 7.0f * S);
        const float Progress = Requested > 0 ? FMath::Clamp(static_cast<float>(Issued) / Requested, 0.0f, 1.0f) : 0.0f;
        if (Progress > 0.0f) DrawRect(Green, ProgressBarX, ProgressBarY, ProgressBarW * Progress, 7.0f);

        if (Snapshot.Management.bCampaignInitialised)
        {
            DrawText(FString::Printf(TEXT("CASH  %s"),
                *FormatMoneyPence(Snapshot.Management.CashBalancePence)),
                White, OperationsX + Pad, 10.0f * S, Small, SmallScale, false);
            DrawText(FString::Printf(TEXT("RP  %lld  |  SIM %.1fx"),
                Snapshot.Management.AvailableResearchPoints,
                Snapshot.EffectiveSimulationRate), Muted,
                OperationsX + Pad, StripH - 27.0f * S, Small, DetailScale, false);
        }
        else
        {
            DrawText(TEXT("MANAGEMENT  INITIALISING"), Warning,
                OperationsX + Pad, 10.0f * S, Small, SmallScale, false);
            DrawText(FString::Printf(TEXT("SIM  %.1fx"), Snapshot.EffectiveSimulationRate),
                Muted, OperationsX + Pad, StripH - 27.0f * S, Small, DetailScale, false);
        }

        DrawText(FString::Printf(TEXT("HEALTH  %d ASSETS"), Snapshot.OperationalAssetCount),
            White, HealthX + Pad, 10.0f * S, Small, SmallScale, false);
        const FString HealthDetail = Readability.bCompactMode
            ? FString::Printf(TEXT("R %d | W %d | F %d"), Snapshot.RunningCount,
                Snapshot.WaitingCount, Snapshot.FaultCount)
            : FString::Printf(TEXT("%d RUNNING  |  %d WAITING  |  %d FAULT"), Snapshot.RunningCount,
                Snapshot.WaitingCount, Snapshot.FaultCount);
        DrawText(HealthDetail, Snapshot.FaultCount > 0 ? Critical
            : Snapshot.WaitingCount > 0 ? Warning : Green,
            HealthX + Pad, StripH - 27.0f * S, Small, DetailScale, false);
    }

    FLinearColor AlertFill(0.015f, 0.12f, 0.085f, 0.98f);
    if (TopAlert)
    {
        AlertFill = TopAlert->Severity == ELBFactoryUIAlertSeverity::Critical
            ? FLinearColor(0.78f, 0.075f, 0.035f, 0.98f)
            : TopAlert->Severity == ELBFactoryUIAlertSeverity::Warning
                ? FLinearColor(0.97f, 0.50f, 0.025f, 0.98f)
                : Accent.CopyWithNewOpacity(0.98f);
    }
    DrawRect(AlertFill, AlertX + 8.0f * S, 8.0f * S,
        W - AlertX - 16.0f * S, StripH - 16.0f * S);
    const FLinearColor AlertInk = ChooseReadableTextColour(AlertFill);
    if (Small)
    {
        const FString AlertCount = TopAlert
            ? FString::Printf(TEXT("%d ALERT%s  |  VIEW"), Snapshot.Alerts.Num(),
                Snapshot.Alerts.Num() == 1 ? TEXT("") : TEXT("S"))
            : TEXT("0 ALERTS  |  CLEAR");
        DrawText(AlertCount, AlertInk, AlertX + Pad + 4.0f * S,
            10.0f * S, Small, SmallScale, false);
        const FString AlertDetail = TopAlert
            ? Readability.bCompactMode
                ? TopAlert->Title
                : FString::Printf(TEXT("%s  %s"), *TopAlert->Title, *TopAlert->EntityId.ToString())
            : TEXT("FACTORY FLOW HEALTHY");
        DrawText(Readability.bCompactMode ? AlertDetail : AlertDetail.Left(36), AlertInk,
            AlertX + Pad + 4.0f * S, StripH - 27.0f * S, Small, DetailScale, false);
    }

    // The projected marker is deliberately suppressed behind full management panels, but the
    // alert remains actionable in the persistent strip.
    if (TopAlert && !bManagementVisible)
    {
        const FVector MarkerWorld = TopAlert->MarkerWorldLocation;
        FVector2D MarkerScreen;
        APlayerController* PC = GetOwningPlayerController();
        if (PC && (TopAlert->TargetActor.IsValid() || !MarkerWorld.IsNearlyZero())
            && PC->ProjectWorldLocationToScreen(MarkerWorld, MarkerScreen, false)
            && MarkerScreen.X >= 0.0f && MarkerScreen.X <= W
            && MarkerScreen.Y >= StripH && MarkerScreen.Y <= H)
        {
            const FLinearColor MarkerColour = TopAlert->Severity == ELBFactoryUIAlertSeverity::Critical
                ? Critical : TopAlert->Severity == ELBFactoryUIAlertSeverity::Warning ? Warning : Accent;
            const float Diamond = 9.0f * UIScale;
            DrawLine(MarkerScreen.X, MarkerScreen.Y - Diamond,
                MarkerScreen.X + Diamond, MarkerScreen.Y, MarkerColour, 2.0f);
            DrawLine(MarkerScreen.X + Diamond, MarkerScreen.Y,
                MarkerScreen.X, MarkerScreen.Y + Diamond, MarkerColour, 2.0f);
            DrawLine(MarkerScreen.X, MarkerScreen.Y + Diamond,
                MarkerScreen.X - Diamond, MarkerScreen.Y, MarkerColour, 2.0f);
            DrawLine(MarkerScreen.X - Diamond, MarkerScreen.Y,
                MarkerScreen.X, MarkerScreen.Y - Diamond, MarkerColour, 2.0f);

            const FString MarkerTitle = TopAlert->Title.Left(30);
            const FString MarkerId = TopAlert->EntityId.ToString();
            float TitleW = 150.0f;
            float TitleH = 12.0f;
            float IdW = 80.0f;
            float IdH = 12.0f;
            if (Small)
            {
                GetTextSize(MarkerTitle, TitleW, TitleH, Small, SmallScale);
                GetTextSize(MarkerId, IdW, IdH, Small, DetailScale);
            }
            const float LabelW = FMath::Clamp(FMath::Max(TitleW, IdW) + 40.0f, 180.0f, 310.0f);
            const float LabelH = 54.0f;
            float LabelX = FMath::Clamp(MarkerScreen.X - LabelW * 0.5f, 10.0f, W - LabelW - 10.0f);
            float LabelY = MarkerScreen.Y - LabelH - 38.0f;
            const bool bLabelBelow = LabelY < StripH + 10.0f;
            if (bLabelBelow) LabelY = MarkerScreen.Y + 28.0f;
            DrawLine(MarkerScreen.X, bLabelBelow ? MarkerScreen.Y + Diamond : LabelY + LabelH,
                MarkerScreen.X, bLabelBelow ? LabelY : MarkerScreen.Y - Diamond,
                MarkerColour.CopyWithNewOpacity(0.88f), 1.5f);
            DrawRect(FLinearColor(0.010f, 0.024f, 0.024f, 0.94f), LabelX, LabelY, LabelW, LabelH);
            DrawRect(MarkerColour, LabelX, LabelY, 5.0f, LabelH);
            DrawLine(LabelX, LabelY, LabelX + LabelW, LabelY, MarkerColour, 1.0f);
            if (Small)
            {
                DrawText(MarkerTitle, White, LabelX + 18.0f, LabelY + 10.0f,
                    Small, SmallScale, false);
                DrawText(MarkerId, MarkerColour, LabelX + 18.0f, LabelY + 30.0f,
                    Small, DetailScale, false);
            }
        }
    }

    // Selection details stay compact and local to the world view. Existing infrastructure
    // inspection is drawn by its established path below and therefore retains its hit regions.
    const ALBManagementPawn* ManagementPawn = Cast<ALBManagementPawn>(GetOwningPawn());
    if (!ManagementPawn || bManagementVisible) return;
    AActor* InspectedActor = ManagementPawn->GetInspectedFactoryActor();
    FLBFactoryUIInspectorSnapshot Inspector;
    if (!UIState->BuildInspectorSnapshot(InspectedActor, Inspector) || !Inspector.bValid) return;

    const int32 DetailCount = FMath::Min(Inspector.DetailLines.Num(), 10);
    const float InspectorW = FMath::Clamp(W * 0.225f, 330.0f, 430.0f);
    const float InspectorX = W - InspectorW - 22.0f;
    const float InspectorY = StripH + 18.0f;
    const float InspectorH = 146.0f + DetailCount * 22.0f;
    const FLinearColor InspectorBack(0.008f, 0.022f, 0.023f, 0.95f);
    const FLinearColor InspectorHeader = Primary.CopyWithNewOpacity(0.98f);
    const FLinearColor HeaderInk = ChooseReadableTextColour(InspectorHeader);
    const bool bInspectorFault = Inspector.State.Contains(TEXT("FAULT"));
    const bool bInspectorWarning = Inspector.State.Contains(TEXT("WAIT"))
        || Inspector.State.Contains(TEXT("BLOCK")) || Inspector.State.Contains(TEXT("FULL"))
        || Inspector.State.Contains(TEXT("EMPTY")) || Inspector.State.Contains(TEXT("ISOLATED"));
    const FLinearColor InspectorStateColour = bInspectorFault ? Critical
        : bInspectorWarning ? Warning : Green;

    DrawRect(InspectorBack, InspectorX, InspectorY, InspectorW, InspectorH);
    DrawRect(InspectorHeader, InspectorX, InspectorY, InspectorW, 42.0f);
    DrawRect(InspectorStateColour, InspectorX, InspectorY + 42.0f, 4.0f, InspectorH - 42.0f);
    if (Large)
    {
        DrawText(Inspector.DisplayName.Left(32), HeaderInk,
            InspectorX + 16.0f, InspectorY + 9.0f, Large,
            Readability.HeadingTextScale, false);
    }
    if (Small)
    {
        float InspectorTextY = InspectorY + 52.0f;
        DrawText(FString::Printf(TEXT("%s  |  %s"), *Inspector.Kind, *Inspector.EntityId.ToString()),
            Muted, InspectorX + 16.0f, InspectorTextY, Small, DetailScale, false);
        InspectorTextY += 23.0f;
        DrawText(FString::Printf(TEXT("STATE  %s"), *Inspector.State),
            InspectorStateColour, InspectorX + 16.0f, InspectorTextY, Small, SmallScale, false);
        InspectorTextY += 23.0f;
        DrawText(Inspector.Reason.Left(48), White,
            InspectorX + 16.0f, InspectorTextY, Small, DetailScale, false);
        InspectorTextY += 30.0f;
        DrawLine(InspectorX + 16.0f, InspectorTextY - 7.0f,
            InspectorX + InspectorW - 16.0f, InspectorTextY - 7.0f, Divider, 1.0f);
        for (int32 Index = 0; Index < DetailCount; ++Index)
        {
            DrawText(Inspector.DetailLines[Index].Left(48), Index % 2 == 0 ? White : Muted,
                InspectorX + 16.0f, InspectorTextY, Small, DetailScale, false);
            InspectorTextY += 22.0f;
        }
        DrawText(TEXT("SELECT AGAIN / A: FOCUS  |  ESC: CLEAR"), Muted,
            InspectorX + 16.0f, InspectorY + InspectorH - 25.0f,
            Small, DetailScale, false);
    }
}

#endif

void ALBControlRoomHUD::ShowCCTVFeed(UTextureRenderTarget2D* InFeed)
{
    Feed = InFeed;
    bCCTVFeedVisible = Feed.IsValid();
}

void ALBControlRoomHUD::HideCCTVFeed()
{
    bCCTVFeedVisible = false;
}

bool ALBControlRoomHUD::IsModernOverviewActive() const
{
    return bManagementVisible
        && ManagementPage == ELBManagementPage::Overview
        && !bSettingsVisible
        && !bBrandEditorVisible
        && !IsCCTVFeedVisible();
}

bool ALBControlRoomHUD::EnsureSettingsWidget()
{
    if (IsValid(SettingsRootWidget)) return true;
    APlayerController* Controller = GetOwningPlayerController();
    if (!Controller || !Controller->IsLocalController()) return false;

    SettingsRootWidget = CreateWidget<ULBSettingsRootWidget>(
        Controller, ULBSettingsRootWidget::StaticClass());
    if (!SettingsRootWidget) return false;
    SettingsRootWidget->OnCloseRequested.AddDynamic(
        this, &ALBControlRoomHUD::HandleSettingsCloseRequested);
    SettingsRootWidget->OnAppearanceRequested.AddDynamic(
        this, &ALBControlRoomHUD::HandleSettingsAppearanceRequested);
    if (!SettingsRootWidget->AddToPlayerScreen(100))
    {
        SettingsRootWidget = nullptr;
        return false;
    }
    SettingsRootWidget->SetVisibility(ESlateVisibility::Collapsed);
    return true;
}

bool ALBControlRoomHUD::EnsureModernOverviewWidget()
{
    if (IsValid(ManagementRootWidget)) return true;
    APlayerController* Controller = GetOwningPlayerController();
    if (!Controller || !Controller->IsLocalController()) return false;

    ManagementRootWidget = CreateWidget<ULBManagementRootWidget>(
        Controller, ULBManagementRootWidget::StaticClass());
    if (!ManagementRootWidget) return false;

    ManagementRootWidget->OnDestinationRequested.AddDynamic(
        this, &ALBControlRoomHUD::HandleModernManagementDestinationRequested);
    ManagementRootWidget->OnStageSelectionChanged.AddDynamic(
        this, &ALBControlRoomHUD::HandleModernProductionStageSelectionRequested);
    ManagementRootWidget->OnStageActionRequested.AddDynamic(
        this, &ALBControlRoomHUD::HandleModernProductionStageActionRequested);
    ManagementRootWidget->OnContextActionRequested.AddDynamic(
        this, &ALBControlRoomHUD::HandleModernContextActionRequested);
    ManagementRootWidget->OnSimulationRateRequested.AddDynamic(
        this, &ALBControlRoomHUD::HandleModernSimulationRateRequested);
    if (!ManagementRootWidget->AddToPlayerScreen(50))
    {
        ManagementRootWidget = nullptr;
        return false;
    }
    ManagementRootWidget->SetVisibility(ESlateVisibility::Collapsed);
    return true;
}

bool ALBControlRoomHUD::IsModernOverviewRendered() const
{
    return IsModernOverviewActive()
        && IsValid(ManagementRootWidget)
        && ManagementRootWidget->IsInViewport()
        && ManagementRootWidget->GetVisibility() == ESlateVisibility::Visible
        && ManagementRootWidget->HasRenderableShell();
}

bool ALBControlRoomHUD::IsModernManagementActive() const
{
    return bManagementVisible && !bSettingsVisible
        && !bBrandEditorVisible && !IsCCTVFeedVisible();
}

bool ALBControlRoomHUD::IsModernManagementRendered() const
{
    return IsModernManagementActive() && IsValid(ManagementRootWidget)
        && ManagementRootWidget->IsInViewport()
        && ManagementRootWidget->GetVisibility() == ESlateVisibility::Visible
        && ManagementRootWidget->HasRenderableShell();
}

void ALBControlRoomHUD::RefreshModernManagementContext()
{
    if (!IsValid(ManagementRootWidget)) return;
    if (ManagementPage == ELBManagementPage::Overview)
    {
        ManagementRootWidget->SetManagementContext(TEXT("FACTORY"),
            TEXT("Production flow"), TEXT(""), {});
        return;
    }

    FString Heading;
    FString Summary;
    switch (ManagementPage)
    {
    case ELBManagementPage::FactoryBuild:
        Heading = TEXT("Build factory");
        Summary = TEXT("Select an approved asset, then place it through the existing factory builder.");
        break;
    case ELBManagementPage::Production:
        Heading = TEXT("Orders");
        Summary = TEXT("Create and control a production order through the existing operations authority.");
        break;
    case ELBManagementPage::PressTrains:
        Heading = TEXT("Assets");
        Summary = TEXT("Review and focus capital production assets.");
        break;
    case ELBManagementPage::SupportFleet:
        Heading = TEXT("Maintenance");
        Summary = TEXT("Dispatch and recall the factory support fleet.");
        break;
    case ELBManagementPage::Research:
        Heading = TEXT("Research");
        Summary = TEXT("Research status is shown from the live management authority.");
        break;
    case ELBManagementPage::Analytics:
        Heading = TEXT("Analytics");
        Summary = TEXT("Review factory health, output and explicit campaign save/load actions.");
        break;
    default:
        Heading = TEXT("Management");
        Summary = TEXT("Choose an available action.");
        break;
    }

    if (ManagementPage == ELBManagementPage::Production)
    {
        ULBOneFactoryOperationsSubsystem* OneFactoryOperations = GetWorld()
            ? GetWorld()->GetSubsystem<ULBOneFactoryOperationsSubsystem>()
            : nullptr;
        if (OneFactoryOperations
            && OneFactoryOperations->IsOneFactoryOperationsWorld())
        {
            Heading = TEXT("OneFactory vehicles");
            Summary = OneFactoryOperations->GetUMGSummary();
            TArray<FLBManagementContextActionPresentation> OneFactoryActions;
            for (const FLBOneFactoryBuilderUMGAction& Source :
                OneFactoryOperations->GetUMGActions())
            {
                FLBManagementContextActionPresentation& Action =
                    OneFactoryActions.AddDefaulted_GetRef();
                Action.ActionIndex = Source.ActionIndex;
                Action.Title = FText::FromString(Source.Title);
                Action.Detail = FText::FromString(Source.Detail);
                Action.bEnabled = Source.bEnabled;
            }
            ManagementRootWidget->SetManagementContext(
                UEnum::GetValueAsName(ManagementPage), Heading, Summary,
                OneFactoryActions);
            return;
        }
    }

    if (ManagementPage == ELBManagementPage::Analytics)
    {
        ULBOneFactoryOperationsSubsystem* OneFactoryOperations = GetWorld()
            ? GetWorld()->GetSubsystem<ULBOneFactoryOperationsSubsystem>()
            : nullptr;
        if (OneFactoryOperations
            && OneFactoryOperations->IsOneFactoryOperationsWorld())
        {
            const ULBOneFactorySaveSubsystem* Save = GetWorld()
                ? GetWorld()->GetSubsystem<ULBOneFactorySaveSubsystem>()
                : nullptr;
            Heading = TEXT("OneFactory save / load");
            Summary = CampaignPersistenceFeedback;
            TArray<FLBManagementContextActionPresentation> OneFactoryActions;
            OneFactoryActions.SetNum(2);
            OneFactoryActions[0].ActionIndex = 0;
            OneFactoryActions[0].Title = FText::FromString(
                TEXT("Save OneFactory"));
            OneFactoryActions[0].Detail = FText::FromString(
                TEXT("WRITE LAYOUTS, COMMISSIONING, 57-STATION WIP AND GENEALOGY TO THE ISOLATED SLOT"));
            OneFactoryActions[0].bEnabled = Save != nullptr;
            OneFactoryActions[1].ActionIndex = 1;
            OneFactoryActions[1].Title = FText::FromString(
                bCampaignLoadConfirmationArmed
                    ? TEXT("Confirm load OneFactory")
                    : TEXT("Load OneFactory"));
            OneFactoryActions[1].Detail = FText::FromString(
                Save && Save->DoesOneFactorySaveExist()
                    ? TEXT("LOAD THE ISOLATED SLOT; A FRESH SHELL WILL MATERIALISE ITS SAVED FACTORY")
                    : TEXT("NO ONEFACTORY ISOLATED SAVE EXISTS"));
            OneFactoryActions[1].bEnabled = Save
                && Save->DoesOneFactorySaveExist();
            ManagementRootWidget->SetManagementContext(
                UEnum::GetValueAsName(ManagementPage), Heading, Summary,
                OneFactoryActions);
            return;
        }
    }

    // The dedicated OneFactory shell uses the same native UMG surface, but its
    // first transaction is the canonical Press starter rather than the legacy
    // catalogue. Data/presentation creation and exact rejection reasons stay in
    // the isolated OneFactory subsystem; this HUD only projects its view model.
    if (ManagementPage == ELBManagementPage::FactoryBuild)
    {
        ULBOneFactoryPlayerBuilderSubsystem* OneFactoryBuilder = GetWorld()
            ? GetWorld()->GetSubsystem<ULBOneFactoryPlayerBuilderSubsystem>()
            : nullptr;
        if (OneFactoryBuilder && OneFactoryBuilder->IsOneFactoryBuilderWorld())
        {
            Heading = TEXT("OneFactory builder");
            Summary = OneFactoryBuilder->GetUMGSummary();
            TArray<FLBManagementContextActionPresentation> OneFactoryActions;
            for (const FLBOneFactoryBuilderUMGAction& Source :
                OneFactoryBuilder->GetUMGActions())
            {
                FLBManagementContextActionPresentation& Action =
                    OneFactoryActions.AddDefaulted_GetRef();
                Action.ActionIndex = Source.ActionIndex;
                Action.Title = FText::FromString(Source.Title);
                Action.Detail = FText::FromString(Source.Detail);
                Action.bEnabled = Source.bEnabled;
            }
            ManagementRootWidget->SetManagementContext(
                UEnum::GetValueAsName(ManagementPage), Heading, Summary,
                OneFactoryActions);
            return;
        }
    }

    TArray<FLBManagementContextActionPresentation> Actions;
    const int32 Count = FMath::Min(GetManagementActionCount(), 5);
    for (int32 Index = 0; Index < Count; ++Index)
    {
        FLBManagementContextActionPresentation& Action = Actions.AddDefaulted_GetRef();
        Action.ActionIndex = Index;
        Action.bEnabled = true;
        if (ManagementPage == ELBManagementPage::FactoryBuild)
        {
            FLBFactoryCatalogueDecisionFacts Facts;
            if (GetFactoryMachineCardDecisionFacts(Index, Facts))
            {
                Action.ActionIndex = GetFactoryMachineCardActionIndex(Index);
                Action.Title = FText::FromString(Facts.DisplayName);
                Action.Detail = FText::FromString(Facts.bLocked
                    ? Facts.LockReason : FString::Printf(TEXT("%s  |  %s"),
                        *Facts.ProcessStage, *Facts.Purpose));
                Action.bEnabled = !Facts.bLocked && Action.ActionIndex != INDEX_NONE;
            }
            else
            {
                Action.Title = FText::FromString(FString::Printf(TEXT("Build option %02d"), Index + 1));
                Action.Detail = FText::FromString(TEXT("Choose this approved factory-build option."));
            }
        }
        else
        {
            FString Title;
            FString Detail;
            if (ManagementPage == ELBManagementPage::Production)
            {
                if (FindOperationsConsole())
                {
                    static const TCHAR* Labels[] = {TEXT("Change panel family"), TEXT("Quantity -"), TEXT("Quantity +"), TEXT("Change priority"), TEXT("Create / validate order")};
                    Title = Labels[Index];
                    Detail = TEXT("Update the live production order through the operations authority.");
                }
                else
                {
                    static const TCHAR* Labels[] = {TEXT("Change vehicle programme"), TEXT("Change panel type"), TEXT("Quantity -"), TEXT("Quantity +"), TEXT("Queue production batch")};
                    Title = Labels[Index];
                    Detail = Index == 4 ? TEXT("Queue the selected batch for the automatic material flow.")
                        : TEXT("Adjust the next player production batch.");
                }
            }
            else if (ManagementPage == ELBManagementPage::PressTrains)
            {
                Title = TEXT("Select next press train");
                Detail = TEXT("Cycle the production asset selected by the operations authority.");
            }
            else if (ManagementPage == ELBManagementPage::SupportFleet)
            {
                static const TCHAR* Labels[] = {TEXT("Select support unit"), TEXT("Dispatch selected unit"), TEXT("Recall selected unit")};
                Title = Labels[Index];
                Detail = TEXT("Use the existing support-fleet authority.");
            }
            else if (ManagementPage == ELBManagementPage::Analytics)
            {
                Title = Index == 0 ? TEXT("Save campaign")
                    : bCampaignLoadConfirmationArmed
                        ? TEXT("Confirm load campaign") : TEXT("Load campaign");
                Detail = Index == 0 ? TEXT("Write the current campaign to the manual save slot.")
                    : TEXT("Load the manual save only after explicit confirmation.");
            }
            else
            {
                Title = FString::Printf(TEXT("%s action %02d"), *Heading, Index + 1);
                Detail = TEXT("Run the existing management action.");
            }
            Action.Title = FText::FromString(Title);
            Action.Detail = FText::FromString(Detail);
        }
    }
    ManagementRootWidget->SetManagementContext(
        UEnum::GetValueAsName(ManagementPage), Heading, Summary, Actions);
}

void ALBControlRoomHUD::SyncModernOverviewWidget()
{
    const bool bShouldShow = IsModernManagementActive();
    if (!EnsureModernOverviewWidget())
    {
        bModernOverviewWasActive = false;
        return;
    }

    if (!bShouldShow)
    {
        ManagementRootWidget->SetVisibility(ESlateVisibility::Collapsed);
        bModernOverviewWasActive = false;
        return;
    }

    ManagementRootWidget->SetVisibility(ESlateVisibility::Visible);
    ManagementRootWidget->ForceLayoutPrepass();
    if (ManagementPage == ELBManagementPage::Overview)
    {
        const int32 StageIndex = FMath::Clamp(SelectedProductionFlowStage, 0,
            ULBManagementRootWidget::ProductionStageCount - 1);
        const bool bSelectionChanged =
            ManagementRootWidget->GetSelectedProductionStage() != StageIndex;
        ManagementRootWidget->SelectProductionStage(StageIndex,
            bSelectionChanged || !bModernOverviewWasActive);
    }
    if (!bModernOverviewWasActive)
    {
        ManagementRootWidget->RefreshFromFactoryState(true);
        ManagementRootWidget->ForceLayoutPrepass();
        UE_LOG(LogLineBossModernUI, Display,
            TEXT("Modern Overview activated: viewport=%s desired=%s cached=%s"),
            ManagementRootWidget->IsInViewport() ? TEXT("yes") : TEXT("no"),
            *ManagementRootWidget->GetDesiredSize().ToString(),
            *ManagementRootWidget->GetCachedGeometry().GetLocalSize().ToString());
        if (APlayerController* Controller = GetOwningPlayerController())
            ManagementRootWidget->SetUserFocus(Controller);
    }
    RefreshModernManagementContext();
    bModernOverviewWasActive = true;
}

bool ALBControlRoomHUD::SelectModernProductionStage(const FName StageId)
{
    const TArray<FName> StageIds =
        ULBManagementRootWidget::GetCanonicalProductionStageIds();
    const int32 StageIndex = StageIds.IndexOfByKey(StageId);
    if (StageIndex == INDEX_NONE) return false;
    SelectedProductionFlowStage = StageIndex;
    SelectedManagementAction = StageIndex;
    DisarmCampaignLoadConfirmation();
    return true;
}

bool ALBControlRoomHUD::HandleModernManagementDestination(const FName DestinationId)
{
    if (DestinationId == TEXT("SETTINGS"))
    {
        OpenSettings();
        return true;
    }
    ELBManagementPage Destination = ELBManagementPage::Overview;
    if (DestinationId == TEXT("FACTORY"))
    {
        // Factory is a useful two-state camera control: the first press opens the
        // production Overview, while further presses switch cleanly between the
        // dense production camera and the whole-factory planning frame. Home/reset
        // remains the controller/keyboard equivalent for the wide frame.
        if (ALBManagementPawn* ManagementPawn = Cast<ALBManagementPawn>(GetOwningPawn()))
        {
            if (ManagementPage != ELBManagementPage::Overview)
            {
                ManagementPawn->FocusBuiltFactory();
                bWholeFactoryCameraSelected = false;
            }
            else if (bWholeFactoryCameraSelected)
            {
                ManagementPawn->FocusBuiltFactory();
                bWholeFactoryCameraSelected = false;
            }
            else if (ManagementPawn->FocusWholeBuiltFactory())
            {
                bWholeFactoryCameraSelected = true;
            }
        }
        Destination = ELBManagementPage::Overview;
    }
    else if (DestinationId == TEXT("BUILD")) Destination = ELBManagementPage::FactoryBuild;
    else if (DestinationId == TEXT("ORDERS")) Destination = ELBManagementPage::Production;
    else if (DestinationId == TEXT("ASSETS")) Destination = ELBManagementPage::PressTrains;
    else if (DestinationId == TEXT("MAINTENANCE")) Destination = ELBManagementPage::SupportFleet;
    else if (DestinationId == TEXT("RESEARCH")) Destination = ELBManagementPage::Research;
    else if (DestinationId == TEXT("ANALYTICS")) Destination = ELBManagementPage::Analytics;
    else return false;

    OpenManagementPage(Destination);
    if (Destination != ELBManagementPage::Overview)
    {
        bWholeFactoryCameraSelected = false;
    }
    SyncModernOverviewWidget();
    return true;
}

bool ALBControlRoomHUD::HandleModernProductionStageAction(const FName StageId)
{
    if (!SelectModernProductionStage(StageId)) return false;
    const bool bHandled = ActivateProductionFlowPrimaryAction();
    SyncModernOverviewWidget();
    return bHandled;
}

void ALBControlRoomHUD::HandleModernManagementDestinationRequested(
    const FName DestinationId)
{
    HandleModernManagementDestination(DestinationId);
}

void ALBControlRoomHUD::HandleModernProductionStageSelectionRequested(
    const FName StageId)
{
    SelectModernProductionStage(StageId);
}

void ALBControlRoomHUD::HandleModernProductionStageActionRequested(
    const FName StageId)
{
    HandleModernProductionStageAction(StageId);
}

void ALBControlRoomHUD::HandleModernContextActionRequested(const int32 ActionIndex)
{
    ActivateManagementAction(ActionIndex);
    SyncModernOverviewWidget();
}

void ALBControlRoomHUD::HandleModernSimulationRateRequested(
    const float RequestedRate)
{
    ULBOneFactoryOperationsSubsystem* Operations = GetWorld()
        ? GetWorld()->GetSubsystem<ULBOneFactoryOperationsSubsystem>()
        : nullptr;
    if (!Operations || !Operations->IsOneFactoryOperationsWorld()) return;
    FString Reason;
    Operations->SetSimulationRate(RequestedRate, Reason);
    SyncModernOverviewWidget();
}

void ALBControlRoomHUD::HandleSettingsCloseRequested()
{
    CloseSettings();
}

void ALBControlRoomHUD::HandleSettingsAppearanceRequested()
{
    // The native Settings surface now contains the livery controls. Keep the
    // delegate for Blueprint compatibility without reopening a Canvas overlay.
    if (SettingsRootWidget) SettingsRootWidget->FocusInitialControl();
}

ALBControlRoomOperationsConsole* ALBControlRoomHUD::FindOperationsConsole() const
{
    if (UWorld* World = GetWorld())
    {
        for (TActorIterator<ALBControlRoomOperationsConsole> It(World); It; ++It)
        {
            return *It;
        }
    }
    return nullptr;
}

ALBPlayerBuiltPressFlowController* ALBControlRoomHUD::FindPlayerFlow() const
{
    if (UWorld* World = GetWorld())
        for (TActorIterator<ALBPlayerBuiltPressFlowController> It(World); It; ++It) return *It;
    return nullptr;
}

ALBPressShopCampaignController* ALBControlRoomHUD::FindCampaignController() const
{
    if (UWorld* World = GetWorld())
        for (TActorIterator<ALBPressShopCampaignController> It(World); It; ++It) return *It;
    return nullptr;
}

void ALBControlRoomHUD::DisarmCampaignLoadConfirmation()
{
    if (bCampaignLoadConfirmationArmed && !bCampaignPersistenceAttempted)
        CampaignPersistenceFeedback = TEXT("LOAD CANCELLED - NO CAMPAIGN CHANGES MADE");
    bCampaignLoadConfirmationArmed = false;
}

bool ALBControlRoomHUD::IsMandatoryFactorySetupActive() const
{
    return false;
}

void ALBControlRoomHUD::InitialiseFactoryBrandDraft()
{
    const UWorld* World = GetWorld();
    const ULBFactoryBrandSubsystem* Brand = World
        ? World->GetSubsystem<ULBFactoryBrandSubsystem>() : nullptr;
    FactoryNameEditBuffer = Brand ? Brand->GetFactoryName() : TEXT("Cairnwell Automotive");
    DraftPrimaryMachineColour = Brand ? Brand->GetPrimaryColour()
        : FactoryLiverySwatches[0];
    DraftSecondaryMachineColour = Brand ? Brand->GetSecondaryColour()
        : FactoryLiverySwatches[6];
    SelectedPrimarySwatch = FindClosestFactoryLiverySwatch(DraftPrimaryMachineColour);
    SelectedSecondarySwatch = FindClosestFactoryLiverySwatch(DraftSecondaryMachineColour);
    SelectedBrandEditorControl = 0;
    bEditingFactoryName = false;
    RefreshFactoryBrandValidation();
}

void ALBControlRoomHUD::EnsureMandatoryFactorySetup()
{
    // Compatibility shim for existing call sites. Factory appearance no longer owns
    // startup or input; it opens only through OpenFactoryAppearanceSettings().
}

void ALBControlRoomHUD::OpenFactoryAppearanceSettings()
{
    // Compatibility entry point: factory colours now live in the native
    // settings surface, never in the retired Canvas editor.
    OpenSettings();
}

void ALBControlRoomHUD::OpenSettings()
{
    if (bSettingsVisible)
    {
        if (SettingsRootWidget)
        {
            SettingsRootWidget->RefreshFromSettings();
            SettingsRootWidget->FocusInitialControl();
        }
        return;
    }
    bManagementWasVisibleBeforeSettings = bManagementVisible;
    bManagementVisible = true;
    bCCTVFeedVisible = false;
    bBrandEditorVisible = false;
    bEditingFactoryName = false;
    if (!EnsureSettingsWidget())
    {
        bManagementVisible = bManagementWasVisibleBeforeSettings;
        bSettingsVisible = false;
        return;
    }
    bSettingsVisible = true;
    SettingsRootWidget->RefreshFromSettings();
    SettingsRootWidget->SetVisibility(ESlateVisibility::Visible);
    SettingsRootWidget->ForceLayoutPrepass();
    SettingsRootWidget->FocusInitialControl();
    SyncModernOverviewWidget();
}

void ALBControlRoomHUD::CloseSettings()
{
    const bool bWasOpen = bSettingsVisible;
    bSettingsVisible = false;
    if (SettingsRootWidget)
    {
        SettingsRootWidget->CancelAndRevertPendingDisplayChange();
        SettingsRootWidget->SetVisibility(ESlateVisibility::Collapsed);
    }
    if (bWasOpen) bManagementVisible = bManagementWasVisibleBeforeSettings;
    SyncModernOverviewWidget();
}

void ALBControlRoomHUD::OpenFactoryProfile()
{
    OpenFactoryAppearanceSettings();
}

void ALBControlRoomHUD::SetFactoryNameDraft(const FString& NewName)
{
    FactoryNameEditBuffer = NewName.Left(40);
    RefreshFactoryBrandValidation();
}

bool ALBControlRoomHUD::SelectFactoryLiverySwatch(
    const bool bPrimary, const int32 SwatchIndex)
{
    if (!FMath::IsWithin(SwatchIndex, 0, FactoryLiverySwatchCount)) return false;
    if (bPrimary)
    {
        SelectedPrimarySwatch = SwatchIndex;
        DraftPrimaryMachineColour = FactoryLiverySwatches[SwatchIndex];
    }
    else
    {
        SelectedSecondarySwatch = SwatchIndex;
        DraftSecondaryMachineColour = FactoryLiverySwatches[SwatchIndex];
    }
    RefreshFactoryBrandValidation();
    return true;
}

void ALBControlRoomHUD::RefreshFactoryBrandValidation()
{
    FString TrimmedName = FactoryNameEditBuffer;
    TrimmedName.TrimStartAndEndInline();
    if (TrimmedName.IsEmpty())
    {
        FactoryBrandValidationReason = TEXT("ENTER A FACTORY NAME TO CONTINUE");
        return;
    }
    FString ColourReason;
    if (!ULBFactoryBrandSubsystem::ValidateMachineLiveryColours(
        DraftPrimaryMachineColour, DraftSecondaryMachineColour, ColourReason))
    {
        FactoryBrandValidationReason = ColourReason;
        return;
    }
    FactoryBrandValidationReason = TEXT("READY - APPLY TO EVERY APPROVED MACHINE");
}

bool ALBControlRoomHUD::SubmitFactoryBrandEditor()
{
    if (!bBrandEditorVisible || !GetWorld()) return false;
    RefreshFactoryBrandValidation();

    FString TrimmedName = FactoryNameEditBuffer;
    TrimmedName.TrimStartAndEndInline();
    FString ColourReason;
    if (TrimmedName.IsEmpty()
        || !ULBFactoryBrandSubsystem::ValidateMachineLiveryColours(
            DraftPrimaryMachineColour, DraftSecondaryMachineColour, ColourReason))
    {
        if (!ColourReason.IsEmpty()) FactoryBrandValidationReason = ColourReason;
        return false;
    }

    ULBFactoryBrandSubsystem* Brand = GetWorld()->GetSubsystem<ULBFactoryBrandSubsystem>();
    if (!Brand || !Brand->SetFactoryName(FactoryNameEditBuffer))
    {
        FactoryBrandValidationReason = TEXT("ENTER A PRINTABLE FACTORY NAME TO CONTINUE");
        return false;
    }
    if (!Brand->SetMachineLiveryColours(
        DraftPrimaryMachineColour, DraftSecondaryMachineColour, FactoryBrandValidationReason))
    {
        return false;
    }
    if (!Brand->CompleteInitialSetup())
    {
        FactoryBrandValidationReason = TEXT("FACTORY APPEARANCE COULD NOT BE APPLIED");
        return false;
    }

    bBrandEditorVisible = false;
    bEditingFactoryName = false;
    SelectedBrandEditorControl = 0;
    FactoryBrandValidationReason.Reset();
    return true;
}

void ALBControlRoomHUD::AdjustSelectedFactoryLiverySwatch(const int32 Direction)
{
    if (Direction == 0) return;
    if (SelectedBrandEditorControl == 1)
    {
        const int32 Index = (SelectedPrimarySwatch + Direction
            + FactoryLiverySwatchCount) % FactoryLiverySwatchCount;
        SelectFactoryLiverySwatch(true, Index);
    }
    else if (SelectedBrandEditorControl == 2)
    {
        const int32 Index = (SelectedSecondarySwatch + Direction
            + FactoryLiverySwatchCount) % FactoryLiverySwatchCount;
        SelectFactoryLiverySwatch(false, Index);
    }
}

bool ALBControlRoomHUD::ActivateSelectedBrandEditorControl()
{
    if (!bBrandEditorVisible) return false;
    switch (SelectedBrandEditorControl)
    {
    case 0:
        bEditingFactoryName = true;
        return true;
    case 1:
    case 2:
        AdjustSelectedFactoryLiverySwatch(1);
        return true;
    case 3:
        return SubmitFactoryBrandEditor();
    default:
        return false;
    }
}

int32 ALBControlRoomHUD::GetManagementActionCount() const
{
    if (bBrandEditorVisible) return 4;
    switch (ManagementPage)
    {
    case ELBManagementPage::FactoryBuild:
        if (const UWorld* World = GetWorld())
            if (const ULBOneFactoryPlayerBuilderSubsystem* OneFactoryBuilder =
                World->GetSubsystem<ULBOneFactoryPlayerBuilderSubsystem>())
                if (OneFactoryBuilder->IsOneFactoryBuilderWorld())
                    return ULBOneFactoryPlayerBuilderSubsystem::UMGActionCount;
        if (const UWorld* World = GetWorld())
            if (const ULBFactoryMachineBuilderSubsystem* Builder = World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>())
            {
                if (SelectedBuildCategory == 0) return Builder->GetAvailableMachineTypes().Num();
                if (SelectedBuildCategory == 1) return Builder->GetAvailableStorageTypes().Num();
                int32 Count = 0;
                for (const ELBFactoryAGVInfrastructureType Type : Builder->GetAvailableInfrastructureTypes())
                {
                    const bool bSafety = Type == ELBFactoryAGVInfrastructureType::PedestrianCrossing
                        || Type == ELBFactoryAGVInfrastructureType::SafetyFence;
                    const bool bLogistics = Type == ELBFactoryAGVInfrastructureType::ChargingStation
                        || Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff;
                    Count += (SelectedBuildCategory == 2 && bLogistics)
                        || (SelectedBuildCategory == 3 && bSafety) ? 1 : 0;
                }
                return Count;
            }
        return 0;
    case ELBManagementPage::Production:
        if (const UWorld* World = GetWorld())
            if (const ULBOneFactoryOperationsSubsystem* OneFactoryOperations =
                World->GetSubsystem<ULBOneFactoryOperationsSubsystem>())
                if (OneFactoryOperations->IsOneFactoryOperationsWorld())
                    return ULBOneFactoryOperationsSubsystem::UMGActionCount;
        return FindOperationsConsole() ? 9 : 5;
    case ELBManagementPage::PressTrains: return FindOperationsConsole() ? 1 : 0;
    case ELBManagementPage::SupportFleet: return FindOperationsConsole() ? 3 : 0;
    // Overview actions are the six stable flow-stage selections. Confirm then
    // invokes the selected stage's single contextual primary action.
    case ELBManagementPage::Overview: return 6;
    case ELBManagementPage::Analytics:
        if (const UWorld* World = GetWorld())
            if (const ULBOneFactoryOperationsSubsystem* OneFactoryOperations =
                World->GetSubsystem<ULBOneFactoryOperationsSubsystem>())
                if (OneFactoryOperations->IsOneFactoryOperationsWorld()) return 2;
        return FindCampaignController() ? 2 : 0;
    case ELBManagementPage::Research:
        return 0;
    default: return 0;
    }
}

int32 ALBControlRoomHUD::GetManagementInformationLineCount() const
{
    switch (ManagementPage)
    {
    case ELBManagementPage::Overview: return 0;
    case ELBManagementPage::Production: return 4;
    case ELBManagementPage::PressTrains: return 6;
    case ELBManagementPage::SupportFleet:
    {
        UWorld* World = GetWorld();
        ULBFactoryUIStateSubsystem* UIState = World
            ? World->GetSubsystem<ULBFactoryUIStateSubsystem>() : nullptr;
        int32 VisibleMaintenanceRows = 0;
        if (UIState)
        {
            for (const FLBFactoryUIManagementAssetSnapshot& Asset :
                UIState->GetSnapshot().Management.Assets)
            {
                if (Asset.bHasMaintenance && ++VisibleMaintenanceRows == 3) break;
            }
        }
        return 4 + VisibleMaintenanceRows;
    }
    case ELBManagementPage::Research:
    {
        UWorld* World = GetWorld();
        ULBFactoryUIStateSubsystem* UIState = World
            ? World->GetSubsystem<ULBFactoryUIStateSubsystem>() : nullptr;
        const int32 UnlockRows = UIState
            ? FMath::Min(3, UIState->GetSnapshot().Management.ResearchUnlockIds.Num()) : 0;
        return 4 + UnlockRows;
    }
    case ELBManagementPage::Analytics: return 9;
    default: return 0;
    }
}

FName ALBControlRoomHUD::GetSelectedVehicleModelId() const
{
    const int32 SafeIndex = FMath::Clamp(SelectedVehicleModel, 0,
        UE_ARRAY_COUNT(PreProductionVehicleModels) - 1);
    return PreProductionVehicleModels[SafeIndex];
}

FString ALBControlRoomHUD::GetSelectedVehicleDisplayName() const
{
    const int32 SafeIndex = FMath::Clamp(SelectedVehicleModel, 0,
        UE_ARRAY_COUNT(PreProductionVehicleDisplayNames) - 1);
    return PreProductionVehicleDisplayNames[SafeIndex];
}

int32 ALBControlRoomHUD::GetVisibleFactoryMachineCardCount() const
{
    const UWorld* World = GetWorld();
    const ULBFactoryMachineBuilderSubsystem* Builder = World
        ? World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    if (!Builder) return 0;
    const TArray<ELBFactoryBuildMachineType> Available = Builder->GetAvailableMachineTypes();
    const int32 PresentationCount = BuildMachinePresentationCards(Builder, Available).Num();
    return FMath::Clamp(PresentationCount - FactoryCataloguePage
        * MaximumVisibleFactoryCatalogueCards, 0, MaximumVisibleFactoryCatalogueCards);
}

bool ALBControlRoomHUD::IsFactoryMachineCardLocked(const int32 CardIndex) const
{
    const UWorld* World = GetWorld();
    const ULBFactoryMachineBuilderSubsystem* Builder = World
        ? World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    if (!Builder) return false;
    const TArray<ELBFactoryBuildMachineType> Available = Builder->GetAvailableMachineTypes();
    const TArray<FFactoryMachinePresentationCard> Cards = BuildMachinePresentationCards(Builder, Available);
    const int32 PresentationIndex = FactoryCataloguePage
        * MaximumVisibleFactoryCatalogueCards + CardIndex;
    return Cards.IsValidIndex(PresentationIndex) && Cards[PresentationIndex].bLocked
        && FMath::IsWithin(CardIndex, 0, GetVisibleFactoryMachineCardCount());
}

int32 ALBControlRoomHUD::GetFactoryMachineCardActionIndex(const int32 CardIndex) const
{
    const UWorld* World = GetWorld();
    const ULBFactoryMachineBuilderSubsystem* Builder = World
        ? World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    if (!Builder) return INDEX_NONE;
    const TArray<ELBFactoryBuildMachineType> Available = Builder->GetAvailableMachineTypes();
    const TArray<FFactoryMachinePresentationCard> Cards = BuildMachinePresentationCards(Builder, Available);
    const int32 PresentationIndex = FactoryCataloguePage
        * MaximumVisibleFactoryCatalogueCards + CardIndex;
    return Cards.IsValidIndex(PresentationIndex) ? Cards[PresentationIndex].ActionIndex : INDEX_NONE;
}

int32 ALBControlRoomHUD::GetFactoryCatalogueItemCount() const
{
    const UWorld* World = GetWorld();
    const ULBFactoryMachineBuilderSubsystem* Builder = World
        ? World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    if (!Builder) return 0;
    if (SelectedBuildCategory == 0)
    {
        const TArray<ELBFactoryBuildMachineType> Available = Builder->GetAvailableMachineTypes();
        return BuildMachinePresentationCards(Builder, Available).Num();
    }
    if (SelectedBuildCategory == 1) return Builder->GetAvailableStorageTypes().Num();
    int32 Count = 0;
    for (const ELBFactoryAGVInfrastructureType Type : Builder->GetAvailableInfrastructureTypes())
    {
        const bool bSafety = Type == ELBFactoryAGVInfrastructureType::PedestrianCrossing
            || Type == ELBFactoryAGVInfrastructureType::SafetyFence;
        const bool bLogistics = Type == ELBFactoryAGVInfrastructureType::ChargingStation
            || Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff;
        Count += (SelectedBuildCategory == 2 && bLogistics)
            || (SelectedBuildCategory == 3 && bSafety) ? 1 : 0;
    }
    return Count;
}

int32 ALBControlRoomHUD::GetFactoryCataloguePageCount() const
{
    return FMath::Max(1, FMath::DivideAndRoundUp(GetFactoryCatalogueItemCount(),
        MaximumVisibleFactoryCatalogueCards));
}

void ALBControlRoomHUD::NextFactoryCataloguePage()
{
    if (!bManagementVisible || ManagementPage != ELBManagementPage::FactoryBuild) return;
    FactoryCataloguePage = (FactoryCataloguePage + 1) % GetFactoryCataloguePageCount();
    if (SelectedBuildCategory == 0)
    {
        for (int32 Card = 0; Card < GetVisibleFactoryMachineCardCount(); ++Card)
            if (const int32 Action = GetFactoryMachineCardActionIndex(Card); Action != INDEX_NONE)
            { SelectedManagementAction = Action; break; }
    }
    else SelectedManagementAction = FMath::Min(FactoryCataloguePage
        * MaximumVisibleFactoryCatalogueCards, FMath::Max(0, GetManagementActionCount() - 1));
}

void ALBControlRoomHUD::PreviousFactoryCataloguePage()
{
    if (!bManagementVisible || ManagementPage != ELBManagementPage::FactoryBuild) return;
    const int32 Count = GetFactoryCataloguePageCount();
    FactoryCataloguePage = (FactoryCataloguePage + Count - 1) % Count;
    if (SelectedBuildCategory == 0)
    {
        for (int32 Card = 0; Card < GetVisibleFactoryMachineCardCount(); ++Card)
            if (const int32 Action = GetFactoryMachineCardActionIndex(Card); Action != INDEX_NONE)
            { SelectedManagementAction = Action; break; }
    }
    else SelectedManagementAction = FMath::Min(FactoryCataloguePage
        * MaximumVisibleFactoryCatalogueCards, FMath::Max(0, GetManagementActionCount() - 1));
}

bool ALBControlRoomHUD::SelectFactoryBuildCategory(const int32 CategoryIndex)
{
    if (!bManagementVisible || ManagementPage != ELBManagementPage::FactoryBuild
        || !FMath::IsWithin(CategoryIndex, 0, 4)) return false;
    SelectedBuildCategory = CategoryIndex;
    SelectedManagementAction = 0;
    FactoryCataloguePage = 0;
    DisarmCampaignLoadConfirmation();
    return true;
}

void ALBControlRoomHUD::SyncFactoryCataloguePageToSelection()
{
    if (ManagementPage != ELBManagementPage::FactoryBuild) return;
    if (SelectedBuildCategory == 0)
    {
        const UWorld* World = GetWorld();
        const ULBFactoryMachineBuilderSubsystem* Builder = World
            ? World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
        if (Builder)
        {
            const TArray<FFactoryMachinePresentationCard> Cards = BuildMachinePresentationCards(
                Builder, Builder->GetAvailableMachineTypes());
            const int32 PresentationIndex = Cards.IndexOfByPredicate([this](const auto& Card)
                { return Card.ActionIndex == SelectedManagementAction; });
            if (PresentationIndex != INDEX_NONE)
            {
                FactoryCataloguePage = PresentationIndex / MaximumVisibleFactoryCatalogueCards;
                return;
            }
        }
    }
    FactoryCataloguePage = FMath::Clamp(SelectedManagementAction
        / MaximumVisibleFactoryCatalogueCards, 0, GetFactoryCataloguePageCount() - 1);
}

bool ALBControlRoomHUD::GetFactoryMachineCardDecisionFacts(const int32 CardIndex,
    FLBFactoryCatalogueDecisionFacts& OutFacts) const
{
    OutFacts = FLBFactoryCatalogueDecisionFacts();
    const UWorld* World = GetWorld();
    const ULBFactoryMachineBuilderSubsystem* Builder = World
        ? World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    if (!Builder || SelectedBuildCategory != 0
        || !FMath::IsWithin(CardIndex, 0, GetVisibleFactoryMachineCardCount())) return false;
    const TArray<ELBFactoryBuildMachineType> Available = Builder->GetAvailableMachineTypes();
    const TArray<FFactoryMachinePresentationCard> Cards = BuildMachinePresentationCards(Builder, Available);
    const int32 PresentationIndex = FactoryCataloguePage
        * MaximumVisibleFactoryCatalogueCards + CardIndex;
    if (!Cards.IsValidIndex(PresentationIndex)) return false;
    const FFactoryMachinePresentationCard& Card = Cards[PresentationIndex];
    const bool bLocked = Card.bLocked;
    const ELBFactoryBuildMachineType Type = Card.Type;
    OutFacts.DisplayName = MachineTypeName(Type);
    OutFacts.ProcessStage = MachineProcessStageName(Type);
    OutFacts.Purpose = MachinePurpose(Type);
    OutFacts.InputFlow = MachineInputFlow(Type);
    OutFacts.OutputFlow = MachineOutputFlow(Type);
    OutFacts.RouteAndClearance = MachineRouteRequirement(Type);
    OutFacts.PreviewKind = MachinePreviewKind(Type);
    OutFacts.bLocked = bLocked;
    if (bLocked)
    {
        OutFacts.LockReason = Card.LockReason.IsEmpty()
            ? TEXT("COMPLETE THE PREVIOUS FACTORY AREA FIRST") : Card.LockReason;
    }
    OutFacts.FootprintAndServiceEnvelope = MachineEnvelopeLabel(Type);
    return true;
}

bool ALBControlRoomHUD::GetFactoryCatalogueCardHitRect(const int32 CardIndex,
    const float ViewWidth, const float ViewHeight, FBox2D& OutScreenRect) const
{
    OutScreenRect = FBox2D(ForceInit);
    const int32 VisibleCount = SelectedBuildCategory == 0
        ? GetVisibleFactoryMachineCardCount()
        : FMath::Clamp(GetFactoryCatalogueItemCount() - FactoryCataloguePage
            * MaximumVisibleFactoryCatalogueCards, 0, MaximumVisibleFactoryCatalogueCards);
    if (!FMath::IsWithin(CardIndex, 0, VisibleCount)
        || ViewWidth <= 0.0f || ViewHeight <= 0.0f) return false;
    const FLBFactoryBuildHUDLayout Layout = MakeFactoryBuildHUDLayout(ViewWidth, ViewHeight);
    if (!Layout.Cards.IsValidIndex(CardIndex)) return false;
    const FLBHUDRect& Rect = Layout.Cards[CardIndex];
    OutScreenRect = FBox2D(FVector2D(Rect.X, Rect.Y),
        FVector2D(Rect.X + Rect.W, Rect.Y + Rect.H));
    return true;
}

bool ALBControlRoomHUD::GetFactoryCataloguePageButtonHitRect(const bool bNext,
    const float ViewWidth, const float ViewHeight, FBox2D& OutScreenRect) const
{
    OutScreenRect = FBox2D(ForceInit);
    if (ViewWidth <= 0.0f || ViewHeight <= 0.0f) return false;
    const FLBFactoryBuildHUDLayout Layout = MakeFactoryBuildHUDLayout(ViewWidth, ViewHeight);
    const FLBHUDRect& Rect = bNext ? Layout.NextPageButton : Layout.PreviousPageButton;
    OutScreenRect = FBox2D(FVector2D(Rect.X, Rect.Y),
        FVector2D(Rect.X + Rect.W, Rect.Y + Rect.H));
    return true;
}

bool ALBControlRoomHUD::ActivateFactoryMachineCard(const int32 CardIndex)
{
    if (!bManagementVisible || ManagementPage != ELBManagementPage::FactoryBuild
        || SelectedBuildCategory != 0)
    {
        return false;
    }
    const int32 ActionIndex = GetFactoryMachineCardActionIndex(CardIndex);
    return ActionIndex != INDEX_NONE && ActivateManagementAction(ActionIndex);
}

void ALBControlRoomHUD::ToggleManagement()
{
    EnsureMandatoryFactorySetup();
    if (IsMandatoryFactorySetupActive()) return;
    if (bSettingsVisible)
    {
        CloseSettings();
        return;
    }
    if (bBrandEditorVisible)
    {
        bBrandEditorVisible = false;
        bEditingFactoryName = false;
        return;
    }
    bManagementVisible = !bManagementVisible;
    DisarmCampaignLoadConfirmation();
    bCCTVFeedVisible = false;
    SelectedManagementAction = FMath::Clamp(SelectedProductionFlowStage, 0, 5);
    // Clean player-built maps still open the practical build catalogue; authored
    // control-room maps retain Overview as their management landing page.
    if (bManagementVisible && !FindOperationsConsole())
    {
        ManagementPage = ELBManagementPage::FactoryBuild;
        SelectedManagementAction = 0;
    }
}

void ALBControlRoomHUD::OpenFactoryBuild()
{
    bManagementVisible = true;
    bCCTVFeedVisible = false;
    ManagementPage = ELBManagementPage::FactoryBuild;
    SelectedManagementAction = 0;
    SelectedBuildCategory = 0;
    FactoryCataloguePage = 0;
    DisarmCampaignLoadConfirmation();
    EnsureMandatoryFactorySetup();
}

void ALBControlRoomHUD::OpenManagementPage(const ELBManagementPage Page)
{
    if (!FMath::IsWithin(static_cast<int32>(Page), 0,
        static_cast<int32>(ELBManagementPage::PageCount))) return;
    bManagementVisible = true;
    bCCTVFeedVisible = false;
    ManagementPage = Page;
    SelectedManagementAction = Page == ELBManagementPage::Overview
        ? FMath::Clamp(SelectedProductionFlowStage, 0, 5) : 0;
    if (Page == ELBManagementPage::FactoryBuild) FactoryCataloguePage = 0;
    DisarmCampaignLoadConfirmation();
    EnsureMandatoryFactorySetup();
}

void ALBControlRoomHUD::CloseManagement()
{
    EnsureMandatoryFactorySetup();
    if (IsMandatoryFactorySetupActive()) return;
    CloseSettings();
    bBrandEditorVisible = false;
    bEditingFactoryName = false;
    bManagementVisible = false;
    SelectedManagementAction = 0;
    DisarmCampaignLoadConfirmation();
}

void ALBControlRoomHUD::NextManagementPage()
{
    EnsureMandatoryFactorySetup();
    if (bSettingsVisible) return;
    if (bBrandEditorVisible)
    {
        AdjustSelectedFactoryLiverySwatch(1);
        return;
    }
    if (!bManagementVisible) return;
    const int32 PageCount = static_cast<int32>(ELBManagementPage::PageCount);
    ManagementPage = static_cast<ELBManagementPage>(
        (static_cast<int32>(ManagementPage) + 1) % PageCount);
    SelectedManagementAction = ManagementPage == ELBManagementPage::Overview
        ? FMath::Clamp(SelectedProductionFlowStage, 0, 5) : 0;
    DisarmCampaignLoadConfirmation();
}

void ALBControlRoomHUD::PreviousManagementPage()
{
    EnsureMandatoryFactorySetup();
    if (bSettingsVisible) return;
    if (bBrandEditorVisible)
    {
        AdjustSelectedFactoryLiverySwatch(-1);
        return;
    }
    if (!bManagementVisible) return;
    const int32 PageCount = static_cast<int32>(ELBManagementPage::PageCount);
    ManagementPage = static_cast<ELBManagementPage>(
        (static_cast<int32>(ManagementPage) + PageCount - 1) % PageCount);
    SelectedManagementAction = ManagementPage == ELBManagementPage::Overview
        ? FMath::Clamp(SelectedProductionFlowStage, 0, 5) : 0;
    DisarmCampaignLoadConfirmation();
}

void ALBControlRoomHUD::NextManagementAction()
{
    EnsureMandatoryFactorySetup();
    if (bSettingsVisible) return;
    if (bBrandEditorVisible)
    {
        SelectedBrandEditorControl = (SelectedBrandEditorControl + 1) % 4;
        bEditingFactoryName = false;
        return;
    }
    if (bManagementVisible && ManagementPage == ELBManagementPage::Overview)
    {
        SelectedProductionFlowStage = (FMath::Clamp(
            SelectedProductionFlowStage, 0, 5) + 1) % 6;
        SelectedManagementAction = SelectedProductionFlowStage;
        DisarmCampaignLoadConfirmation();
        return;
    }
    const int32 Count = GetManagementActionCount();
    if (bManagementVisible && Count > 0)
    {
        SelectedManagementAction = (SelectedManagementAction + 1) % Count;
        SyncFactoryCataloguePageToSelection();
        DisarmCampaignLoadConfirmation();
    }
}

void ALBControlRoomHUD::PreviousManagementAction()
{
    EnsureMandatoryFactorySetup();
    if (bSettingsVisible) return;
    if (bBrandEditorVisible)
    {
        SelectedBrandEditorControl = (SelectedBrandEditorControl + 3) % 4;
        bEditingFactoryName = false;
        return;
    }
    if (bManagementVisible && ManagementPage == ELBManagementPage::Overview)
    {
        SelectedProductionFlowStage = (FMath::Clamp(
            SelectedProductionFlowStage, 0, 5) + 5) % 6;
        SelectedManagementAction = SelectedProductionFlowStage;
        DisarmCampaignLoadConfirmation();
        return;
    }
    const int32 Count = GetManagementActionCount();
    if (bManagementVisible && Count > 0)
    {
        SelectedManagementAction = (SelectedManagementAction + Count - 1) % Count;
        SyncFactoryCataloguePageToSelection();
        DisarmCampaignLoadConfirmation();
    }
}

bool ALBControlRoomHUD::ActivateManagementAction(const int32 ActionIndex)
{
    EnsureMandatoryFactorySetup();
    if (bBrandEditorVisible)
    {
        if (!FMath::IsWithin(ActionIndex, 0, 4)) return false;
        SelectedBrandEditorControl = ActionIndex;
        return ActivateSelectedBrandEditorControl();
    }
    if (!bManagementVisible || !FMath::IsWithin(ActionIndex, 0, GetManagementActionCount())) return false;
    if (ManagementPage == ELBManagementPage::Overview)
    {
        SelectedProductionFlowStage = ActionIndex;
        SelectedManagementAction = ActionIndex;
        return ActivateProductionFlowPrimaryAction();
    }
    SelectedManagementAction = ActionIndex;
    SyncFactoryCataloguePageToSelection();
    return ConfirmManagementAction();
}

bool ALBControlRoomHUD::HandleFactoryBrandEditorClick(
    const float ScreenX, const float ScreenY,
    const float ViewWidth, const float ViewHeight)
{
    if (!bBrandEditorVisible || ViewWidth <= 0.0f || ViewHeight <= 0.0f) return false;
    const FLBFactoryBrandEditorLayout Layout = MakeFactoryBrandEditorLayout(
        ViewWidth, ViewHeight);
    const float Pad = 24.0f * Layout.Scale;
    if (ScreenX >= Layout.BoxX + Pad && ScreenX <= Layout.BoxX + Layout.BoxW - Pad
        && ScreenY >= Layout.NameY
        && ScreenY <= Layout.NameY + 48.0f * Layout.Scale)
    {
        SelectedBrandEditorControl = 0;
        bEditingFactoryName = true;
        return true;
    }
    const auto TrySelectSwatch = [&](const float RowY, const bool bPrimary)
    {
        if (ScreenY < RowY || ScreenY > RowY + Layout.SwatchH
            || ScreenX < Layout.BoxX + Pad
            || ScreenX > Layout.BoxX + Layout.BoxW - Pad) return false;
        const float CellW = Layout.SwatchW + Layout.SwatchGap;
        const float RelativeX = ScreenX - Layout.BoxX - Pad;
        const int32 Index = FMath::FloorToInt(RelativeX / CellW);
        if (!FMath::IsWithin(Index, 0, FactoryLiverySwatchCount)
            || FMath::Fmod(RelativeX, CellW) > Layout.SwatchW) return true;
        SelectedBrandEditorControl = bPrimary ? 1 : 2;
        bEditingFactoryName = false;
        SelectFactoryLiverySwatch(bPrimary, Index);
        return true;
    };
    if (TrySelectSwatch(Layout.PrimaryY, true)
        || TrySelectSwatch(Layout.SecondaryY, false))
    {
        return true;
    }
    const float ButtonW = 214.0f * Layout.Scale;
    if (ScreenX >= Layout.BoxX + Layout.BoxW - Pad - ButtonW
        && ScreenX <= Layout.BoxX + Layout.BoxW - Pad
        && ScreenY >= Layout.ContinueY
        && ScreenY <= Layout.ContinueY + 48.0f * Layout.Scale)
    {
        SelectedBrandEditorControl = 3;
        SubmitFactoryBrandEditor();
        return true;
    }
    // The optional settings surface owns pointer input while open; ToggleManagement
    // and CloseManagement remain the explicit cancel paths.
    return true;
}

bool ALBControlRoomHUD::GetManagementTabHitRect(const ELBManagementPage Page,
    const float ViewWidth, const float ViewHeight, FBox2D& OutScreenRect) const
{
    OutScreenRect = FBox2D(ForceInit);
    const int32 Index = static_cast<int32>(Page);
    if (!FMath::IsWithin(Index, 0, static_cast<int32>(ELBManagementPage::PageCount))
        || ViewWidth <= 0.0f || ViewHeight <= 0.0f)
    {
        return false;
    }
    if (ManagementPage == ELBManagementPage::FactoryBuild)
    {
        const FLBFactoryBuildHUDLayout Layout = MakeFactoryBuildHUDLayout(ViewWidth, ViewHeight);
        if (!Layout.PageTabs.IsValidIndex(Index)) return false;
        const FLBHUDRect& Rect = Layout.PageTabs[Index];
        OutScreenRect = FBox2D(FVector2D(Rect.X, Rect.Y),
            FVector2D(Rect.X + Rect.W, Rect.Y + Rect.H));
        return true;
    }
    if (ManagementPage == ELBManagementPage::Overview)
    {
        const FLBHUDReadabilityContract Contract = MakeHUDReadabilityContract(
            ViewWidth, ViewHeight);
        const TArray<FBox2D> Tabs = MakeProductionFlowPageTabBounds(
            MakeProductionFlowHUDLayout(ViewWidth, ViewHeight),
            Contract.LayoutScale);
        if (!Tabs.IsValidIndex(Index)) return false;
        OutScreenRect = Tabs[Index];
        return true;
    }
    const FLBHUDReadabilityContract Contract = MakeHUDReadabilityContract(
        ViewWidth, ViewHeight);
    const FLBManagementHUDLayout Layout = MakeManagementHUDLayout(ViewWidth, ViewHeight,
        Contract.PersistentHUDHeight,
        GetManagementInformationLineCount(), GetManagementActionCount());
    if (!Layout.PageTabs.IsValidIndex(Index)) return false;
    const FLBHUDRect& Rect = Layout.PageTabs[Index];
    OutScreenRect = FBox2D(FVector2D(Rect.X, Rect.Y),
        FVector2D(Rect.X + Rect.W, Rect.Y + Rect.H));
    return true;
}

bool ALBControlRoomHUD::GetManagementTabHitTarget(const ELBManagementPage Page,
    const float ViewWidth, const float ViewHeight, FVector2D& OutScreenPosition) const
{
    OutScreenPosition = FVector2D::ZeroVector;
    FBox2D Rect(ForceInit);
    if (!GetManagementTabHitRect(Page, ViewWidth, ViewHeight, Rect)) return false;
    OutScreenPosition = Rect.GetCenter();
    return true;
}

bool ALBControlRoomHUD::GetManagementActionHitRect(const int32 ActionIndex,
    const float ViewWidth, const float ViewHeight, FBox2D& OutScreenRect) const
{
    OutScreenRect = FBox2D(ForceInit);
    if (!FMath::IsWithin(ActionIndex, 0, GetManagementActionCount())
        || ViewWidth <= 0.0f || ViewHeight <= 0.0f)
    {
        return false;
    }
    if (ManagementPage == ELBManagementPage::FactoryBuild)
    {
        const FLBFactoryBuildHUDLayout Layout = MakeFactoryBuildHUDLayout(ViewWidth, ViewHeight);
        int32 CardIndex = ActionIndex;
        if (SelectedBuildCategory == 0)
        {
            CardIndex = INDEX_NONE;
            for (int32 Index = 0; Index < GetVisibleFactoryMachineCardCount(); ++Index)
            {
                if (GetFactoryMachineCardActionIndex(Index) == ActionIndex)
                {
                    CardIndex = Index;
                    break;
                }
            }
        }
        else
        {
            CardIndex = ActionIndex - FactoryCataloguePage
                * MaximumVisibleFactoryCatalogueCards;
        }
        if (!Layout.Cards.IsValidIndex(CardIndex)) return false;
        const FLBHUDRect& Rect = Layout.Cards[CardIndex];
        OutScreenRect = FBox2D(FVector2D(Rect.X, Rect.Y),
            FVector2D(Rect.X + Rect.W, Rect.Y + Rect.H));
        return true;
    }
    if (ManagementPage == ELBManagementPage::Overview)
        return GetProductionFlowStageHitRect(ActionIndex, ViewWidth,
            ViewHeight, OutScreenRect);
    const FLBHUDReadabilityContract Contract = MakeHUDReadabilityContract(
        ViewWidth, ViewHeight);
    const FLBManagementHUDLayout Layout = MakeManagementHUDLayout(ViewWidth, ViewHeight,
        Contract.PersistentHUDHeight,
        GetManagementInformationLineCount(), GetManagementActionCount());
    if (!Layout.ActionRows.IsValidIndex(ActionIndex)) return false;
    const FLBHUDRect& Rect = Layout.ActionRows[ActionIndex];
    OutScreenRect = FBox2D(FVector2D(Rect.X, Rect.Y),
        FVector2D(Rect.X + Rect.W, Rect.Y + Rect.H));
    return true;
}

bool ALBControlRoomHUD::GetManagementActionHitTarget(const int32 ActionIndex,
    const float ViewWidth, const float ViewHeight, FVector2D& OutScreenPosition) const
{
    OutScreenPosition = FVector2D::ZeroVector;
    FBox2D Rect(ForceInit);
    if (!GetManagementActionHitRect(ActionIndex, ViewWidth, ViewHeight, Rect)) return false;
    OutScreenPosition = Rect.GetCenter();
    return true;
}

bool ALBControlRoomHUD::GetFactoryBrandControlHitRect(const int32 ControlIndex,
    const float ViewWidth, const float ViewHeight, FBox2D& OutScreenRect) const
{
    OutScreenRect = FBox2D(ForceInit);
    if (!FMath::IsWithin(ControlIndex, 0, 4)
        || ViewWidth <= 0.0f || ViewHeight <= 0.0f) return false;
    const FLBFactoryBrandEditorLayout Layout = MakeFactoryBrandEditorLayout(
        ViewWidth, ViewHeight);
    const float Pad = 24.0f * Layout.Scale;
    FLBHUDRect Rect;
    if (ControlIndex == 0)
        Rect = {Layout.BoxX + Pad, Layout.NameY,
            Layout.BoxW - 2.0f * Pad, 48.0f * Layout.Scale};
    else if (ControlIndex == 1 || ControlIndex == 2)
        Rect = {Layout.BoxX + Pad,
            ControlIndex == 1 ? Layout.PrimaryY : Layout.SecondaryY,
            Layout.BoxW - 2.0f * Pad, Layout.SwatchH};
    else
    {
        const float ButtonW = 214.0f * Layout.Scale;
        Rect = {Layout.BoxX + Layout.BoxW - Pad - ButtonW, Layout.ContinueY,
            ButtonW, 48.0f * Layout.Scale};
    }
    OutScreenRect = FBox2D(FVector2D(Rect.X, Rect.Y),
        FVector2D(Rect.X + Rect.W, Rect.Y + Rect.H));
    return true;
}

bool ALBControlRoomHUD::HandleManagementClick(const float ScreenX, const float ScreenY)
{
    EnsureMandatoryFactorySetup();
    if (bSettingsVisible) return true;
    // Slate owns pointer dispatch for every management page. Never fall back to
    // Canvas hit testing: a widget failure must leave the world clickable, not
    // resurrect the retired HUD beneath it.
    if (IsModernManagementRendered()) return true;
    return false;
}

bool ALBControlRoomHUD::HandleManagementClickForViewport(const float ScreenX,
    const float ScreenY, const float W, const float H)
{
    EnsureMandatoryFactorySetup();
    if (!bManagementVisible || W <= 0.0f || H <= 0.0f) return false;
    if (bBrandEditorVisible)
    {
        return HandleFactoryBrandEditorClick(ScreenX, ScreenY, W, H);
    }
    if (ManagementPage == ELBManagementPage::Overview)
        return HandleProductionFlowClick(ScreenX, ScreenY, W, H);
    if (ManagementPage == ELBManagementPage::FactoryBuild)
    {
        const FLBFactoryBuildHUDLayout Layout = MakeFactoryBuildHUDLayout(W, H);
        if (Layout.ProfileButton.Contains(ScreenX, ScreenY))
        {
            OpenFactoryAppearanceSettings();
            return true;
        }
        if (Layout.PreviousPageButton.Contains(ScreenX, ScreenY))
        {
            PreviousFactoryCataloguePage();
            return true;
        }
        if (Layout.NextPageButton.Contains(ScreenX, ScreenY))
        {
            NextFactoryCataloguePage();
            return true;
        }
        for (int32 Index = 0; Index < Layout.PageTabs.Num(); ++Index)
        {
            if (Layout.PageTabs[Index].Contains(ScreenX, ScreenY))
            {
                ManagementPage = static_cast<ELBManagementPage>(Index);
                SelectedManagementAction = ManagementPage == ELBManagementPage::Overview
                    ? FMath::Clamp(SelectedProductionFlowStage, 0, 5) : 0;
                DisarmCampaignLoadConfirmation();
                return true;
            }
        }
        for (int32 Index = 0; Index < Layout.CategoryTabs.Num(); ++Index)
        {
            if (Layout.CategoryTabs[Index].Contains(ScreenX, ScreenY))
            {
                return SelectFactoryBuildCategory(Index);
            }
        }
        const int32 VisibleCardCount = SelectedBuildCategory == 0
            ? GetVisibleFactoryMachineCardCount()
            : FMath::Clamp(GetManagementActionCount() - FactoryCataloguePage
                * MaximumVisibleFactoryCatalogueCards, 0,
                MaximumVisibleFactoryCatalogueCards);
        for (int32 CardIndex = 0; CardIndex < VisibleCardCount; ++CardIndex)
        {
            if (!Layout.Cards.IsValidIndex(CardIndex)
                || !Layout.Cards[CardIndex].Contains(ScreenX, ScreenY)) continue;
            // A locked milestone consumes its own click without becoming an action. This keeps
            // mouse input aligned with the same action indices used by keyboard/controller.
            if (SelectedBuildCategory == 0)
            {
                if (IsFactoryMachineCardLocked(CardIndex)) return true;
                return ActivateFactoryMachineCard(CardIndex);
            }
            return ActivateManagementAction(FactoryCataloguePage
                * MaximumVisibleFactoryCatalogueCards + CardIndex);
        }
        return false;
    }
    const FLBManagementHUDLayout Layout = MakeManagementHUDLayout(W, H,
        GetPersistentHUDHeight(), GetManagementInformationLineCount(),
        GetManagementActionCount());
    for (int32 Index = 0; Index < Layout.PageTabs.Num(); ++Index)
    {
        if (Layout.PageTabs[Index].Contains(ScreenX, ScreenY))
        {
            ManagementPage = static_cast<ELBManagementPage>(Index);
            SelectedManagementAction = ManagementPage == ELBManagementPage::Overview
                ? FMath::Clamp(SelectedProductionFlowStage, 0, 5) : 0;
            DisarmCampaignLoadConfirmation();
            return true;
        }
    }
    for (int32 Index = 0; Index < Layout.ActionRows.Num(); ++Index)
        if (Layout.ActionRows[Index].Contains(ScreenX, ScreenY))
            return ActivateManagementAction(Index);
    return false;
}

bool ALBControlRoomHUD::HandleBrandingKey(const FKey& Key)
{
    if (!IsBrandingNameEditActive()) return false;
    if (Key == EKeys::BackSpace)
    {
        if (!FactoryNameEditBuffer.IsEmpty()) FactoryNameEditBuffer.LeftChopInline(1);
        RefreshFactoryBrandValidation();
        return true;
    }
    if (Key == EKeys::Enter)
    {
        bEditingFactoryName = false;
        RefreshFactoryBrandValidation();
        return true;
    }
    if (Key == EKeys::Escape)
    {
        bEditingFactoryName = false;
        return true;
    }
    FString Character;
    const FName Name = Key.GetFName();
    const FString KeyName = Name.ToString();
    if (KeyName.Len() == 1 && FChar::IsAlnum(KeyName[0])) Character = KeyName;
    else if (Key == EKeys::SpaceBar) Character = TEXT(" ");
    else if (Key == EKeys::Hyphen) Character = TEXT("-");
    else if (Key == EKeys::Period) Character = TEXT(".");
    else if (Key == EKeys::Apostrophe) Character = TEXT("'");
    if (!Character.IsEmpty() && FactoryNameEditBuffer.Len() < 40)
    {
        FactoryNameEditBuffer += Character;
        RefreshFactoryBrandValidation();
        return true;
    }
    return false;
}

bool ALBControlRoomHUD::HandleProductionFlowClick(const float ScreenX,
    const float ScreenY, const float ViewWidth, const float ViewHeight)
{
    if (!bManagementVisible || ManagementPage != ELBManagementPage::Overview
        || ViewWidth <= 0.0f || ViewHeight <= 0.0f)
    {
        return false;
    }

    const FLBHUDReadabilityContract Readability = MakeHUDReadabilityContract(
        ViewWidth, ViewHeight);
    const FLBProductionFlowHUDLayout Layout = MakeProductionFlowHUDLayout(
        ViewWidth, ViewHeight);
    const TArray<FBox2D> PageTabs = MakeProductionFlowPageTabBounds(
        Layout, Readability.LayoutScale);
    const FVector2D Point(ScreenX, ScreenY);
    for (int32 Index = 0; Index < PageTabs.Num(); ++Index)
    {
        if (!PageTabs[Index].IsInside(Point)) continue;
        ManagementPage = static_cast<ELBManagementPage>(Index);
        SelectedManagementAction = ManagementPage == ELBManagementPage::Overview
            ? FMath::Clamp(SelectedProductionFlowStage, 0, 5) : 0;
        if (ManagementPage == ELBManagementPage::FactoryBuild)
            FactoryCataloguePage = 0;
        DisarmCampaignLoadConfirmation();
        return true;
    }
    for (int32 StageIndex = 0; StageIndex < Layout.StageCardBounds.Num(); ++StageIndex)
    {
        if (!Layout.StageCardBounds[StageIndex].IsInside(Point)) continue;
        SelectedProductionFlowStage = StageIndex;
        SelectedManagementAction = StageIndex;
        DisarmCampaignLoadConfirmation();
        return true;
    }
    if (Layout.PrimaryActionBounds.IsInside(Point))
        return ActivateProductionFlowPrimaryAction();
    return false;
}

bool ALBControlRoomHUD::ActivateProductionFlowPrimaryAction()
{
    // The stage action is deliberately consumed even when progression or world
    // authority makes it unavailable. That gives mouse and controller identical
    // behaviour without letting a disabled action leak through to the factory.
    if (!bManagementVisible || ManagementPage != ELBManagementPage::Overview)
        return false;

    SelectedProductionFlowStage = FMath::Clamp(
        SelectedProductionFlowStage, 0, 5);
    SelectedManagementAction = SelectedProductionFlowStage;
    UWorld* World = GetWorld();
    if (!World) return true;
    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    if (!UIState) return true;
    const FLBFactoryUIStateSnapshot& Snapshot = UIState->GetSnapshot(true);
    if (!Snapshot.ProductionStages.IsValidIndex(SelectedProductionFlowStage))
        return true;
    const FLBFactoryUIProductionStageSnapshot& Stage =
        Snapshot.ProductionStages[SelectedProductionFlowStage];
    ALBManagementPawn* ManagementPawn = Cast<ALBManagementPawn>(GetOwningPawn());
    if (!ManagementPawn) return true;

    if (Stage.bInstalled && Stage.TargetActor.IsValid())
    {
        if (ManagementPawn->SelectFactoryActor(Stage.TargetActor.Get(), true))
            bManagementVisible = false;
        return true;
    }

    bool bStorage = false;
    ELBFactoryBuildMachineType MachineType = ELBFactoryBuildMachineType::InboundDeliveryDock;
    ELBPressShopStorageType StorageType = ELBPressShopStorageType::BareCoils;
    if (!ResolveProductionStagePlacement(Stage.StageId, bStorage,
        MachineType, StorageType)) return true;

    ULBFactoryMachineBuilderSubsystem* Builder =
        World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    if (!Builder) return true;
    bool bStarted = false;
    if (bStorage)
    {
        if (Builder->GetAvailableStorageTypes().Contains(StorageType))
            bStarted = ManagementPawn->StartStoragePlacement(StorageType);
    }
    else
    {
        FString Reason;
        if (Builder->CanPlaceMachine(MachineType, Reason))
            bStarted = ManagementPawn->StartMachinePlacement(MachineType);
    }
    if (bStarted) bManagementVisible = false;
    return true;
}

// Retired Canvas production-flow implementation; ULBManagementRootWidget owns
// every visible management surface.
#if 0
void ALBControlRoomHUD::DrawProductionFlowHUD()
{
    if (!Canvas || !GetWorld()) return;
    const float W = static_cast<float>(Canvas->SizeX);
    const float H = static_cast<float>(Canvas->SizeY);
    const FLBHUDReadabilityContract Readability = MakeHUDReadabilityContract(W, H);
    const float S = Readability.LayoutScale;
    const FLBProductionFlowHUDLayout Layout = MakeProductionFlowHUDLayout(W, H);
    UFont* Small = GEngine ? GEngine->GetSmallFont() : nullptr;
    UFont* Large = GEngine ? GEngine->GetLargeFont() : nullptr;

    const ULBFactoryBrandSubsystem* Brand =
        GetWorld()->GetSubsystem<ULBFactoryBrandSubsystem>();
    const FLinearColor Primary = Brand ? Brand->GetPrimaryColour()
        : FLinearColor(0.035f, 0.36f, 0.16f, 1.0f);
    FLinearColor Accent = Primary;
    const float Luminance = Accent.GetLuminance();
    if (Luminance < 0.30f)
    {
        Accent *= 0.30f / FMath::Max(0.055f, Luminance);
        Accent = Accent.GetClamped();
        Accent.A = 1.0f;
    }
    const FLinearColor Back(0.006f, 0.016f, 0.020f, 0.965f);
    const FLinearColor TopBack(0.018f, 0.036f, 0.041f, 0.985f);
    const FLinearColor Card(0.028f, 0.047f, 0.052f, 0.985f);
    const FLinearColor CardSelected(0.045f, 0.075f, 0.080f, 0.995f);
    const FLinearColor Aperture(0.006f, 0.012f, 0.015f, 1.0f);
    const FLinearColor White(0.96f, 0.98f, 0.97f, 1.0f);
    const FLinearColor Muted(0.58f, 0.69f, 0.69f, 1.0f);
    const FLinearColor Ready(0.18f, 0.84f, 0.55f, 1.0f);
    const FLinearColor Running(0.10f, 0.78f, 0.95f, 1.0f);
    const FLinearColor Waiting(1.0f, 0.63f, 0.06f, 1.0f);
    const FLinearColor Fault(0.96f, 0.15f, 0.09f, 1.0f);
    const FLinearColor Disabled(0.20f, 0.25f, 0.26f, 1.0f);

    const auto DrawBorder = [this](const FBox2D& Bounds,
        const FLinearColor& Colour, const float Thickness)
    {
        const FVector2D Size = Bounds.GetSize();
        DrawRect(Colour, Bounds.Min.X, Bounds.Min.Y, Size.X, Thickness);
        DrawRect(Colour, Bounds.Min.X, Bounds.Max.Y - Thickness, Size.X, Thickness);
        DrawRect(Colour, Bounds.Min.X, Bounds.Min.Y, Thickness, Size.Y);
        DrawRect(Colour, Bounds.Max.X - Thickness, Bounds.Min.Y, Thickness, Size.Y);
    };

    DrawRect(Back, Layout.FlowCanvasBounds.Min.X, Layout.FlowCanvasBounds.Min.Y,
        Layout.FlowCanvasBounds.GetSize().X, Layout.FlowCanvasBounds.GetSize().Y);
    DrawRect(TopBack, Layout.TopBarBounds.Min.X, Layout.TopBarBounds.Min.Y,
        Layout.TopBarBounds.GetSize().X, Layout.TopBarBounds.GetSize().Y);
    DrawRect(Accent, Layout.FlowCanvasBounds.Min.X,
        Layout.FlowCanvasBounds.Min.Y, 5.0f * S,
        Layout.FlowCanvasBounds.GetSize().Y);
    if (Small)
    {
        DrawText(TEXT("LIVE FACTORY FLOW"), White,
            Layout.TopBarBounds.Min.X + 16.0f * S,
            Layout.TopBarBounds.Min.Y + 9.0f * S, Small,
            Readability.NormalTextScale, false);
        DrawText(TEXT("6 CONNECTED STAGES"), Muted,
            Layout.TopBarBounds.Min.X + 16.0f * S,
            Layout.TopBarBounds.Min.Y + 28.0f * S, Small,
            Readability.DetailTextScale, false);
    }

    const TArray<FBox2D> PageTabs = MakeProductionFlowPageTabBounds(Layout, S);
    for (int32 Index = 0; Index < PageTabs.Num(); ++Index)
    {
        const bool bActive = Index == static_cast<int32>(ManagementPage);
        const FBox2D& Tab = PageTabs[Index];
        DrawRect(bActive ? Accent : TopBack, Tab.Min.X, Tab.Min.Y,
            Tab.GetSize().X, Tab.GetSize().Y);
        if (bActive) DrawRect(White, Tab.Min.X, Tab.Max.Y - 3.0f * S,
            Tab.GetSize().X, 3.0f * S);
        if (Small)
        {
            FString Label = ManagementPageName(static_cast<ELBManagementPage>(Index));
            if (Readability.bCompactMode
                && Index == static_cast<int32>(ELBManagementPage::Analytics))
                Label = TEXT("DATA");
            DrawText(Label, bActive ? ChooseReadableTextColour(Accent) : Muted,
                Tab.Min.X + 9.0f * S, Tab.Min.Y + 15.0f * S, Small,
                Readability.DetailTextScale, false);
        }
    }

    ULBFactoryUIStateSubsystem* UIState =
        GetWorld()->GetSubsystem<ULBFactoryUIStateSubsystem>();
    const FLBFactoryUIStateSnapshot EmptySnapshot;
    const FLBFactoryUIStateSnapshot& Snapshot = UIState
        ? UIState->GetSnapshot() : EmptySnapshot;
    static const FName FallbackIds[] = {
        TEXT("COIL_INTAKE"), TEXT("BLANK_BUFFER"), TEXT("TRANSFER_PRESS"),
        TEXT("PANEL_STILLAGES"), TEXT("BODY_WELD"), TEXT("ED_COAT")};
    static const TCHAR* FallbackNames[] = {
        TEXT("Coil intake"), TEXT("Blank buffer"), TEXT("Transfer press"),
        TEXT("Panel stillages"), TEXT("Body weld"), TEXT("ED coat")};

    // A thin rail makes the material direction immediately readable while the
    // opaque cards retain strong individual hit targets.
    if (Layout.StageCardBounds.Num() == 6)
    {
        const float RailY = Layout.StageCardBounds[0].Min.Y + 18.0f * S;
        DrawLine(Layout.StageCardBounds[0].GetCenter().X, RailY,
            Layout.StageCardBounds.Last().GetCenter().X, RailY,
            Accent.CopyWithNewOpacity(0.62f), 3.0f * S);
    }

    for (int32 Index = 0; Index < Layout.StageCardBounds.Num(); ++Index)
    {
        const FBox2D& Bounds = Layout.StageCardBounds[Index];
        FLBFactoryUIProductionStageSnapshot Stage;
        if (Snapshot.ProductionStages.IsValidIndex(Index))
            Stage = Snapshot.ProductionStages[Index];
        else
        {
            Stage.StageId = FallbackIds[Index];
            Stage.DisplayName = FallbackNames[Index];
        }
        const bool bSelected = Index == SelectedProductionFlowStage;
        const FLinearColor StateColour = Stage.bFaulted ? Fault
            : Stage.bWaiting ? Waiting : Stage.bRunning ? Running
            : Stage.bInstalled ? Ready : Disabled;
        DrawRect(bSelected ? CardSelected : Card, Bounds.Min.X, Bounds.Min.Y,
            Bounds.GetSize().X, Bounds.GetSize().Y);
        DrawRect(StateColour, Bounds.Min.X, Bounds.Min.Y,
            Bounds.GetSize().X, 4.0f * S);
        if (bSelected) DrawBorder(Bounds, Accent, 2.0f * S);

        const float Pad = 8.0f * S;
        if (Small)
        {
            DrawText(FString::Printf(TEXT("%02d  %s"), Index + 1,
                *Stage.DisplayName.ToUpper()).Left(24),
                bSelected ? White : Muted, Bounds.Min.X + Pad,
                Bounds.Min.Y + 8.0f * S, Small,
                Readability.DetailTextScale, false);
        }

        const float PreviewX = Bounds.Min.X + Pad;
        const float PreviewY = Bounds.Min.Y + 29.0f * S;
        const float PreviewW = Bounds.GetSize().X - 2.0f * Pad;
        const float PreviewH = 58.0f * S;
        DrawRect(Aperture, PreviewX, PreviewY, PreviewW, PreviewH);
        if (UTexture2D* Thumbnail = ResolveProductionFlowThumbnail(Stage.StageId))
        {
            Canvas->SetDrawColor(FColor::White);
            Canvas->DrawTile(Thumbnail, PreviewX, PreviewY, PreviewW, PreviewH,
                0.0f, 0.0f, static_cast<float>(Thumbnail->GetSizeX()),
                static_cast<float>(Thumbnail->GetSizeY()), BLEND_Translucent);
        }
        else
        {
            const float CentreX = PreviewX + PreviewW * 0.5f;
            const float BaseY = PreviewY + PreviewH - 12.0f * S;
            const FLinearColor Silhouette = Stage.bInstalled
                ? Accent.CopyWithNewOpacity(0.78f)
                : FLinearColor(0.27f, 0.33f, 0.34f, 1.0f);
            if (Index == 0)
            {
                for (int32 Coil = 0; Coil < 3; ++Coil)
                    DrawRect(Silhouette, CentreX + (Coil - 1) * 25.0f * S
                        - 9.0f * S, BaseY - 22.0f * S,
                        18.0f * S, 22.0f * S);
            }
            else if (Index == 1)
            {
                for (int32 Blank = 0; Blank < 4; ++Blank)
                    DrawRect(Silhouette, CentreX - 43.0f * S + Blank * 5.0f * S,
                        BaseY - (8.0f + Blank * 5.0f) * S,
                        82.0f * S, 4.0f * S);
            }
            else if (Index == 2)
            {
                DrawRect(Silhouette, CentreX - 44.0f * S, BaseY - 38.0f * S,
                    88.0f * S, 9.0f * S);
                DrawRect(Silhouette, CentreX - 39.0f * S, BaseY - 29.0f * S,
                    10.0f * S, 29.0f * S);
                DrawRect(Silhouette, CentreX + 29.0f * S, BaseY - 29.0f * S,
                    10.0f * S, 29.0f * S);
                DrawRect(StateColour, CentreX - 24.0f * S,
                    BaseY - 24.0f * S, 48.0f * S, 8.0f * S);
            }
            else if (Index == 3)
            {
                DrawRect(Silhouette, CentreX - 47.0f * S, BaseY - 33.0f * S,
                    94.0f * S, 5.0f * S);
                for (int32 Post = 0; Post < 4; ++Post)
                    DrawRect(Silhouette, CentreX - 45.0f * S + Post * 30.0f * S,
                        BaseY - 28.0f * S, 5.0f * S, 28.0f * S);
            }
            else if (Index == 4)
            {
                DrawRect(Silhouette, CentreX - 36.0f * S, BaseY - 18.0f * S,
                    72.0f * S, 16.0f * S);
                DrawLine(CentreX - 48.0f * S, BaseY - 35.0f * S,
                    CentreX - 18.0f * S, BaseY - 18.0f * S,
                    StateColour, 5.0f * S);
                DrawLine(CentreX + 48.0f * S, BaseY - 35.0f * S,
                    CentreX + 18.0f * S, BaseY - 18.0f * S,
                    StateColour, 5.0f * S);
            }
            else
            {
                DrawRect(Silhouette, CentreX - 50.0f * S, BaseY - 22.0f * S,
                    100.0f * S, 22.0f * S);
                DrawRect(StateColour, CentreX - 38.0f * S,
                    BaseY - 29.0f * S, 76.0f * S, 5.0f * S);
            }
            if (Small) DrawText(TEXT("PREVIEW PENDING"), Muted,
                PreviewX + 7.0f * S, PreviewY + 4.0f * S, Small,
                0.74f * S, false);
        }
        if (Small)
        {
            DrawText(Stage.State.ToUpper().Left(20), StateColour,
                Bounds.Min.X + Pad, Bounds.Min.Y + 94.0f * S,
                Small, Readability.NormalTextScale, false);
            const TArray<FString> DetailLines = WrapCatalogueText(
                Stage.Detail.ToUpper(), 22, 2);
            for (int32 LineIndex = 0; LineIndex < DetailLines.Num(); ++LineIndex)
                DrawText(DetailLines[LineIndex], bSelected ? White : Muted,
                    Bounds.Min.X + Pad,
                    Bounds.Min.Y + (117.0f + LineIndex * 15.0f) * S,
                    Small, Readability.DetailTextScale, false);
        }
    }

    SelectedProductionFlowStage = FMath::Clamp(
        SelectedProductionFlowStage, 0, 5);
    FLBFactoryUIProductionStageSnapshot SelectedStage;
    if (Snapshot.ProductionStages.IsValidIndex(SelectedProductionFlowStage))
        SelectedStage = Snapshot.ProductionStages[SelectedProductionFlowStage];
    else
    {
        SelectedStage.StageId = FallbackIds[SelectedProductionFlowStage];
        SelectedStage.DisplayName = FallbackNames[SelectedProductionFlowStage];
    }

    bool bStorage = false;
    ELBFactoryBuildMachineType MachineType = ELBFactoryBuildMachineType::InboundDeliveryDock;
    ELBPressShopStorageType StorageType = ELBPressShopStorageType::BareCoils;
    const bool bHasPlacement = ResolveProductionStagePlacement(
        SelectedStage.StageId, bStorage, MachineType, StorageType);
    bool bCanAct = SelectedStage.bInstalled && SelectedStage.TargetActor.IsValid();
    FString UnavailableReason;
    if (!SelectedStage.bInstalled && bHasPlacement)
    {
        const ULBFactoryMachineBuilderSubsystem* Builder =
            GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
        if (!Builder) UnavailableReason = TEXT("BUILD AUTHORITY OFFLINE");
        else if (bStorage)
        {
            bCanAct = Builder->GetAvailableStorageTypes().Contains(StorageType);
            if (!bCanAct) UnavailableReason =
                TEXT("COMPLETE THE PREVIOUS FACTORY STAGE FIRST");
        }
        else
        {
            bCanAct = Builder->CanPlaceMachine(MachineType, UnavailableReason);
        }
    }

    const FBox2D& Detail = Layout.DetailBounds;
    const FLinearColor SelectedStateColour = SelectedStage.bFaulted ? Fault
        : SelectedStage.bWaiting ? Waiting : SelectedStage.bRunning ? Running
        : SelectedStage.bInstalled ? Ready : Disabled;
    DrawRect(Card, Detail.Min.X, Detail.Min.Y,
        Detail.GetSize().X, Detail.GetSize().Y);
    DrawRect(SelectedStateColour, Detail.Min.X, Detail.Min.Y,
        5.0f * S, Detail.GetSize().Y);
    if (Large) DrawText(SelectedStage.DisplayName.ToUpper().Left(24), White,
        Detail.Min.X + 14.0f * S, Detail.Min.Y + 7.0f * S,
        Large, 0.70f * S, false);
    if (Small)
    {
        DrawText(FString::Printf(TEXT("STAGE %02d / 06  |  %s"),
            SelectedProductionFlowStage + 1, *SelectedStage.State.ToUpper()).Left(36),
            SelectedStateColour, Detail.Min.X + 14.0f * S,
            Detail.Min.Y + 31.0f * S, Small,
            Readability.DetailTextScale, false);
        const FString StageDetail = !SelectedStage.bInstalled
            && !bCanAct && !UnavailableReason.IsEmpty()
            ? UnavailableReason : SelectedStage.Detail;
        const TArray<FString> InspectorLines = WrapCatalogueText(
            StageDetail.ToUpper(), 34, 2);
        for (int32 LineIndex = 0; LineIndex < InspectorLines.Num(); ++LineIndex)
            DrawText(InspectorLines[LineIndex], Muted,
                Detail.Min.X + 14.0f * S,
                Detail.Min.Y + (49.0f + LineIndex * 14.0f) * S,
                Small, Readability.DetailTextScale, false);

        const int32 Requested = FMath::Max(0, Snapshot.Order.RequestedQuantity);
        const int32 Issued = FMath::Clamp(Snapshot.Order.IssuedQuantity,
            0, Requested);
        const float Progress = Requested > 0
            ? FMath::Clamp(static_cast<float>(Issued)
                / static_cast<float>(Requested), 0.0f, 1.0f) : 0.0f;
        DrawText(Snapshot.Order.bHasActiveOrder
            ? FString::Printf(TEXT("ORDER OUTPUT  %d / %d"), Issued, Requested)
            : TEXT("NO ACTIVE PRODUCTION ORDER"),
            Snapshot.Order.bHasActiveOrder ? White : Muted,
            Detail.Min.X + 14.0f * S, Detail.Min.Y + 79.0f * S,
            Small, Readability.DetailTextScale, false);
        const float ProgressX = Detail.Min.X + 14.0f * S;
        const float ProgressY = Detail.Min.Y + 96.0f * S;
        const float ProgressW = Detail.GetSize().X - 28.0f * S;
        DrawRect(Aperture, ProgressX, ProgressY, ProgressW, 5.0f * S);
        if (Progress > 0.0f)
            DrawRect(Accent, ProgressX, ProgressY, ProgressW * Progress, 5.0f * S);
    }

    const FBox2D& Action = Layout.PrimaryActionBounds;
    const FLinearColor ActionFill = bCanAct ? Accent : Disabled;
    DrawRect(ActionFill, Action.Min.X, Action.Min.Y,
        Action.GetSize().X, Action.GetSize().Y);
    if (bCanAct) DrawBorder(Action, White.CopyWithNewOpacity(0.70f), 1.0f * S);
    if (Small)
    {
        const FString ActionLabel = SelectedStage.bInstalled
            ? TEXT("FOCUS LIVE ASSET")
            : bCanAct ? TEXT("BUILD THIS STAGE") : TEXT("STAGE UNAVAILABLE");
        DrawText(ActionLabel, bCanAct ? ChooseReadableTextColour(ActionFill) : Muted,
            Action.Min.X + 14.0f * S, Action.Min.Y + 14.0f * S,
            Small, Readability.NormalTextScale, false);
    }
}

#endif

bool ALBControlRoomHUD::ConfirmManagementAction()
{
    if (bSettingsVisible) return false;
    EnsureMandatoryFactorySetup();
    if (bBrandEditorVisible) return ActivateSelectedBrandEditorControl();
    if (bManagementVisible && ManagementPage == ELBManagementPage::Overview)
        return ActivateProductionFlowPrimaryAction();
    if (bManagementVisible && ManagementPage == ELBManagementPage::FactoryBuild)
    {
        ULBOneFactoryPlayerBuilderSubsystem* OneFactoryBuilder = GetWorld()
            ? GetWorld()->GetSubsystem<ULBOneFactoryPlayerBuilderSubsystem>()
            : nullptr;
        if (OneFactoryBuilder && OneFactoryBuilder->IsOneFactoryBuilderWorld())
        {
            FString Reason;
            return OneFactoryBuilder->ExecuteUMGAction(
                SelectedManagementAction, Reason);
        }
        if (ALBManagementPawn* ManagementPawn = Cast<ALBManagementPawn>(GetOwningPawn()))
        {
            const ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()
                ? GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
            const TArray<ELBFactoryBuildMachineType> Available = Builder
                ? Builder->GetAvailableMachineTypes() : TArray<ELBFactoryBuildMachineType>();
            const TArray<ELBPressShopStorageType> AvailableStorage = Builder
                ? Builder->GetAvailableStorageTypes() : TArray<ELBPressShopStorageType>();
            const TArray<ELBFactoryAGVInfrastructureType> AvailableInfrastructure = Builder
                ? Builder->GetAvailableInfrastructureTypes() : TArray<ELBFactoryAGVInfrastructureType>();
            if (SelectedBuildCategory == 0 && Available.IsValidIndex(SelectedManagementAction))
            {
                if (ManagementPawn->StartMachinePlacement(Available[SelectedManagementAction]))
                {
                    bManagementVisible = false;
                    return true;
                }
                return false;
            }
            if (SelectedBuildCategory == 1 && AvailableStorage.IsValidIndex(SelectedManagementAction)
                && ManagementPawn->StartStoragePlacement(AvailableStorage[SelectedManagementAction]))
            {
                bManagementVisible = false;
                return true;
            }
            TArray<ELBFactoryAGVInfrastructureType> FilteredInfrastructure;
            for (const ELBFactoryAGVInfrastructureType Type : AvailableInfrastructure)
            {
                const bool bSafety = Type == ELBFactoryAGVInfrastructureType::PedestrianCrossing
                    || Type == ELBFactoryAGVInfrastructureType::SafetyFence;
                const bool bLogistics = Type == ELBFactoryAGVInfrastructureType::ChargingStation
                    || Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff;
                if ((SelectedBuildCategory == 2 && bLogistics)
                    || (SelectedBuildCategory == 3 && bSafety)) FilteredInfrastructure.Add(Type);
            }
            if (FilteredInfrastructure.IsValidIndex(SelectedManagementAction)
                && ManagementPawn->StartInfrastructurePlacement(FilteredInfrastructure[SelectedManagementAction]))
            {
                bManagementVisible = false;
                return true;
            }
            return false;
        }
        return false;
    }

    if (bManagementVisible && ManagementPage == ELBManagementPage::Production)
    {
        ULBOneFactoryOperationsSubsystem* OneFactoryOperations = GetWorld()
            ? GetWorld()->GetSubsystem<ULBOneFactoryOperationsSubsystem>()
            : nullptr;
        if (OneFactoryOperations
            && OneFactoryOperations->IsOneFactoryOperationsWorld())
        {
            FString Reason;
            return OneFactoryOperations->ExecuteUMGAction(
                SelectedManagementAction, Reason);
        }
    }

    if (bManagementVisible && ManagementPage == ELBManagementPage::Analytics)
    {
        ULBOneFactoryOperationsSubsystem* OneFactoryOperations = GetWorld()
            ? GetWorld()->GetSubsystem<ULBOneFactoryOperationsSubsystem>()
            : nullptr;
        if (OneFactoryOperations
            && OneFactoryOperations->IsOneFactoryOperationsWorld())
        {
            ULBOneFactorySaveSubsystem* Save = GetWorld()
                ? GetWorld()->GetSubsystem<ULBOneFactorySaveSubsystem>()
                : nullptr;
            if (!Save)
            {
                CampaignPersistenceFeedback =
                    TEXT("ONEFACTORY SAVE SUBSYSTEM IS UNAVAILABLE");
                bCampaignPersistenceAttempted = true;
                bCampaignPersistenceSucceeded = false;
                return false;
            }
            if (SelectedManagementAction == 0)
            {
                DisarmCampaignLoadConfirmation();
                bCampaignPersistenceAttempted = true;
                FString Reason;
                bCampaignPersistenceSucceeded = Save->SaveOneFactory(Reason);
                CampaignPersistenceFeedback = Reason;
                return bCampaignPersistenceSucceeded;
            }
            if (SelectedManagementAction == 1)
            {
                if (!Save->DoesOneFactorySaveExist())
                {
                    bCampaignPersistenceAttempted = true;
                    bCampaignPersistenceSucceeded = false;
                    CampaignPersistenceFeedback =
                        TEXT("ONEFACTORY ISOLATED SAVE SLOT DOES NOT EXIST");
                    return false;
                }
                if (!bCampaignLoadConfirmationArmed)
                {
                    bCampaignLoadConfirmationArmed = true;
                    bCampaignPersistenceSucceeded = false;
                    CampaignPersistenceFeedback =
                        TEXT("CONFIRM LOAD ONEFACTORY - UNSAVED CHANGES WILL BE LOST");
                    return true;
                }
                DisarmCampaignLoadConfirmation();
                bCampaignPersistenceAttempted = true;
                FString Reason;
                bCampaignPersistenceSucceeded = Save->LoadOneFactory(Reason);
                CampaignPersistenceFeedback = Reason;
                return bCampaignPersistenceSucceeded;
            }
            return false;
        }
        ALBPressShopCampaignController* Campaign = FindCampaignController();
        if (!Campaign) return true;
        if (SelectedManagementAction == 0)
        {
            DisarmCampaignLoadConfirmation();
            bCampaignPersistenceAttempted = true;
            bCampaignPersistenceSucceeded = Campaign->SaveCampaignToSlot();
            CampaignPersistenceFeedback = bCampaignPersistenceSucceeded
                ? TEXT("CAMPAIGN SAVED TO THE MANUAL SLOT")
                : TEXT("SAVE FAILED - CAMPAIGN STATE WAS NOT WRITTEN");
            return true;
        }
        if (SelectedManagementAction == 1)
        {
            if (!bCampaignLoadConfirmationArmed)
            {
                bCampaignLoadConfirmationArmed = true;
                bCampaignPersistenceSucceeded = false;
                CampaignPersistenceFeedback =
                    TEXT("CONFIRM LOAD - UNSAVED CHANGES WILL BE LOST");
                return true;
            }
            DisarmCampaignLoadConfirmation();
            bCampaignPersistenceAttempted = true;
            bCampaignPersistenceSucceeded = Campaign->LoadCampaignFromSlot();
            CampaignPersistenceFeedback = bCampaignPersistenceSucceeded
                ? TEXT("CAMPAIGN LOADED FROM THE MANUAL SLOT")
                : TEXT("LOAD FAILED - CURRENT CAMPAIGN LEFT UNCHANGED");
            return true;
        }
        return false;
    }

    ALBControlRoomOperationsConsole* Operations = bManagementVisible ? FindOperationsConsole() : nullptr;
    if (!Operations && bManagementVisible && ManagementPage == ELBManagementPage::Production)
    {
        switch (SelectedManagementAction)
        {
        case 0: SelectedVehicleModel = (SelectedVehicleModel + 1) % UE_ARRAY_COUNT(PreProductionVehicleModels); return true;
        case 1: SelectedPanelType = (SelectedPanelType + 1) % UE_ARRAY_COUNT(FuturePanelTypes); return true;
        case 2: PlayerBatchQuantity = FMath::Max(1, PlayerBatchQuantity - 1); return true;
        case 3: PlayerBatchQuantity = FMath::Min(1000, PlayerBatchQuantity + 1); return true;
        case 4:
            if (ALBPlayerBuiltPressFlowController* Flow = FindPlayerFlow())
            {
                FLBVehiclePanelBatch Batch;
                Batch.VehicleModelId = GetSelectedVehicleModelId();
                Batch.PanelTypeId = FuturePanelTypes[SelectedPanelType];
                Batch.RequestedQuantity = PlayerBatchQuantity;
                FString Reason;
                return Flow->QueuePanelBatch(Batch, Reason);
            }
            return false;
        default: return false;
        }
    }
    if (!Operations) return false;

    if (ManagementPage == ELBManagementPage::Production)
    {
        switch (SelectedManagementAction)
        {
        case 0: Operations->CyclePanelFamily(); return true;
        case 1: Operations->DecreaseQuantity(); return true;
        case 2: Operations->IncreaseQuantity(); return true;
        case 3: Operations->CyclePriority(); return true;
        case 4: return Operations->CreateProductionOrder();
        case 5: return Operations->SelectAvailableCoil();
        case 6: return Operations->LoadSelectedCoil();
        case 7:
        {
            const ELBControlRoomOrderState State = Operations->CaptureSaveState().OrderState;
            return State == ELBControlRoomOrderState::Running
                ? Operations->PauseOrder()
                : Operations->StartOrResumeOrder();
        }
        case 8: return Operations->StopOrder();
        default: return false;
        }
    }
    if (ManagementPage == ELBManagementPage::PressTrains)
    {
        Operations->CycleAssignedTrain();
        return true;
    }
    if (ManagementPage == ELBManagementPage::SupportFleet)
    {
        if (SelectedManagementAction == 0) { Operations->CycleSupportUnit(); return true; }
        if (SelectedManagementAction == 1) return Operations->DispatchSelectedSupportUnit();
        if (SelectedManagementAction == 2) return Operations->RecallSelectedSupportUnit();
    }
    return false;
}

// Retired Canvas build, appearance and management drawers. Their action
// authority remains in use through ULBManagementRootWidget's UMG controls.
#if 0
void ALBControlRoomHUD::DrawFactoryBuildHUD()
{
    if (!Canvas) return;
    const float W = static_cast<float>(Canvas->SizeX);
    const float H = static_cast<float>(Canvas->SizeY);
    const FLBHUDReadabilityContract Readability = MakeHUDReadabilityContract(W, H);
    const float S = Readability.LayoutScale;
    const FLBFactoryBuildHUDLayout Layout = MakeFactoryBuildHUDLayout(W, H);
    const float PanelX = Layout.PanelX;
    const float PanelY = Layout.PanelY;
    const float PanelW = Layout.PanelW;
    const float PanelH = Layout.PanelH;
    const FLinearColor Back(0.014f, 0.024f, 0.028f, 0.96f);
    const ULBFactoryBrandSubsystem* Brand = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryBrandSubsystem>() : nullptr;
    const FLinearColor BrandPrimary = Brand ? Brand->GetPrimaryColour() : FLinearColor(0.035f, 0.36f, 0.16f);
    const FString FactoryName = Brand ? Brand->GetFactoryName() : TEXT("Cairnwell Automotive");
    const FLinearColor Header(BrandPrimary.R * 0.58f, BrandPrimary.G * 0.58f, BrandPrimary.B * 0.58f, 0.98f);
    const FLinearColor Card(0.055f, 0.075f, 0.080f, 0.98f);
    const FLinearColor LockedCard(0.026f, 0.032f, 0.034f, 0.98f);
    const FLinearColor LockedStripe(0.46f, 0.33f, 0.08f, 1.0f);
    const FLinearColor LockedText(0.56f, 0.59f, 0.58f, 1.0f);
    const FLinearColor Selected(BrandPrimary.R, BrandPrimary.G, BrandPrimary.B, 0.98f);
    const FLinearColor White(0.96f, 0.98f, 0.96f, 1.0f);
    const FLinearColor HeaderText = ChooseReadableTextColour(Header);
    const FLinearColor SelectedText = ChooseReadableTextColour(Selected);
    const FLinearColor Green = BrandPrimary.GetLuminance() < 0.35f
        ? BrandPrimary + FLinearColor(0.22f, 0.38f, 0.22f, 0.0f) : BrandPrimary;
    UFont* Small = GEngine ? GEngine->GetSmallFont() : nullptr;
    UFont* Large = GEngine ? GEngine->GetLargeFont() : nullptr;

    DrawRect(Back, PanelX, PanelY, PanelW, PanelH);
    DrawRect(Header, PanelX, PanelY, PanelW, 48.0f * S);
    const FString BuildHeaderName = Readability.bCompactMode
        ? FactoryName.ToUpper().Left(12) : FactoryName.ToUpper().Left(30);
    if (Large) DrawText(FString::Printf(TEXT("%s  |  BUILD FACTORY"), *BuildHeaderName),
        HeaderText, PanelX + 18.0f * S, PanelY + 9.0f * S, Large,
        Readability.HeadingTextScale, false);
    if (Small && !Readability.bCompactMode) DrawText(
        TEXT("DECISION FACTS, PROTECTED ENVELOPE AND MATERIAL FLOW"), Green,
        PanelX + 390.0f * S, PanelY + 15.0f * S, Small,
        Readability.DetailTextScale, false);
    DrawRect(Selected, Layout.ProfileButton.X, Layout.ProfileButton.Y,
        Layout.ProfileButton.W, Layout.ProfileButton.H);
    if (Small) DrawText(TEXT("APPEARANCE SETTINGS"), SelectedText,
        Layout.ProfileButton.X + 16.0f * S, Layout.ProfileButton.Y + 13.0f * S,
        Small, Readability.NormalTextScale, false);
    const int32 CataloguePageCount = GetFactoryCataloguePageCount();
    DrawRect(CataloguePageCount > 1 ? Card : LockedCard,
        Layout.PreviousPageButton.X, Layout.PreviousPageButton.Y,
        Layout.PreviousPageButton.W, Layout.PreviousPageButton.H);
    DrawRect(CataloguePageCount > 1 ? Card : LockedCard,
        Layout.NextPageButton.X, Layout.NextPageButton.Y,
        Layout.NextPageButton.W, Layout.NextPageButton.H);
    if (Small)
    {
        DrawText(TEXT("< PREV"), CataloguePageCount > 1 ? Green : LockedText,
            Layout.PreviousPageButton.X + 10.0f * S,
            Layout.PreviousPageButton.Y + 13.0f * S, Small,
            Readability.DetailTextScale, false);
        DrawText(FString::Printf(TEXT("NEXT > %d/%d"), FactoryCataloguePage + 1,
            CataloguePageCount), CataloguePageCount > 1 ? Green : LockedText,
            Layout.NextPageButton.X + 7.0f * S,
            Layout.NextPageButton.Y + 13.0f * S, Small,
            Readability.DetailTextScale, false);
    }

    for (int32 Index = 0; Index < Layout.PageTabs.Num(); ++Index)
    {
        const FLBHUDRect& Tab = Layout.PageTabs[Index];
        const bool bActive = Index == static_cast<int32>(ManagementPage);
        DrawRect(bActive ? Selected : Card, Tab.X, Tab.Y, Tab.W, Tab.H);
        if (Small) DrawText(ManagementPageName(static_cast<ELBManagementPage>(Index)),
            bActive ? SelectedText : Green, Tab.X + 10.0f * S, Tab.Y + 13.0f * S,
            Small, Readability.NormalTextScale, false);
    }

    static const TCHAR* Categories[] = {TEXT("MACHINES"), TEXT("STORAGE"), TEXT("LOGISTICS"), TEXT("SAFETY")};
    for (int32 Index = 0; Index < 4; ++Index)
    {
        const FLBHUDRect& Tab = Layout.CategoryTabs[Index];
        const bool bActive = SelectedBuildCategory == Index;
        DrawRect(bActive ? Selected : Card, Tab.X, Tab.Y, Tab.W, Tab.H);
        if (Small) DrawText(Categories[Index], bActive ? SelectedText : Green,
            Tab.X + 14.0f * S, Tab.Y + 13.0f * S, Small,
            Readability.NormalTextScale, false);
    }

    TArray<FString> Labels;
    TArray<int32> CardActionIndices;
    TArray<bool> LockedCards;
    TArray<FString> CardStatusLabels;
    TArray<FLBFactoryCatalogueDecisionFacts> MachineFacts;
    const ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>() : nullptr;
    if (Builder && SelectedBuildCategory == 0)
    {
        const TArray<ELBFactoryBuildMachineType> AvailableMachines = Builder->GetAvailableMachineTypes();
        const TArray<FFactoryMachinePresentationCard> Cards = BuildMachinePresentationCards(
            Builder, AvailableMachines);
        const int32 PageStart = FactoryCataloguePage
            * MaximumVisibleFactoryCatalogueCards;
        const int32 VisibleCount = FMath::Clamp(Cards.Num() - PageStart,
            0, MaximumVisibleFactoryCatalogueCards);
        for (int32 CardIndex = 0; CardIndex < VisibleCount; ++CardIndex)
        {
            const int32 PresentationIndex = PageStart + CardIndex;
            const int32 ActionIndex = Cards[PresentationIndex].ActionIndex;
            const bool bLocked = Cards[PresentationIndex].bLocked;
            FLBFactoryCatalogueDecisionFacts Facts;
            GetFactoryMachineCardDecisionFacts(CardIndex, Facts);
            Labels.Add(Facts.DisplayName);
            MachineFacts.Add(Facts);
            CardActionIndices.Add(ActionIndex);
            LockedCards.Add(bLocked);
            CardStatusLabels.Add(bLocked
                ? Facts.LockReason : TEXT("READY TO PLACE"));
        }
    }
    if (Builder && SelectedBuildCategory == 1)
        for (const ELBPressShopStorageType Type : Builder->GetAvailableStorageTypes())
        {
            CardActionIndices.Add(Labels.Num());
            LockedCards.Add(false);
            CardStatusLabels.Add(TEXT("CLICK TO PLACE"));
            Labels.Add(StorageTypeName(Type));
        }
    if (Builder && SelectedBuildCategory >= 2)
        for (const ELBFactoryAGVInfrastructureType Type : Builder->GetAvailableInfrastructureTypes())
        {
            const bool bSafety = Type == ELBFactoryAGVInfrastructureType::PedestrianCrossing
                || Type == ELBFactoryAGVInfrastructureType::SafetyFence;
            const bool bLogistics = Type == ELBFactoryAGVInfrastructureType::ChargingStation
                || Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff;
            if ((SelectedBuildCategory == 2 && bLogistics)
                || (SelectedBuildCategory == 3 && bSafety))
            {
                CardActionIndices.Add(Labels.Num());
                LockedCards.Add(false);
                CardStatusLabels.Add(TEXT("CLICK TO PLACE"));
                Labels.Add(InfrastructureTypeName(Type));
            }
        }

    const int32 FirstVisibleItem = SelectedBuildCategory == 0 ? 0
        : FactoryCataloguePage * MaximumVisibleFactoryCatalogueCards;
    const int32 LastVisibleItem = FMath::Min(Labels.Num(),
        FirstVisibleItem + MaximumVisibleFactoryCatalogueCards);
    for (int32 ItemIndex = FirstVisibleItem; ItemIndex < LastVisibleItem; ++ItemIndex)
    {
        const int32 Index = ItemIndex - FirstVisibleItem;
        const FLBHUDRect& Rect = Layout.Cards[Index];
        const float X = Rect.X;
        const bool bLocked = LockedCards.IsValidIndex(ItemIndex) && LockedCards[ItemIndex];
        const int32 ActionIndex = CardActionIndices.IsValidIndex(ItemIndex)
            ? CardActionIndices[ItemIndex] : INDEX_NONE;
        const bool bActive = !bLocked && SelectedManagementAction == ActionIndex;
        DrawRect(bLocked ? LockedCard : bActive ? Selected : Card,
            Rect.X, Rect.Y, Rect.W, Rect.H);
        if (bLocked) DrawRect(LockedStripe, Rect.X, Rect.Y, 5.0f * S, Rect.H);
        else DrawRect(bActive ? White : Green, Rect.X, Rect.Y, Rect.W, 4.0f * S);
        if (Small)
        {
            const FLinearColor MainInk = bLocked ? LockedText
                : bActive ? SelectedText : White;
            const FLinearColor AccentInk = bLocked ? LockedText
                : bActive ? SelectedText : Green;
            const float Pad = 10.0f * S;
            if (SelectedBuildCategory == 0 && MachineFacts.IsValidIndex(Index))
            {
                const FLBFactoryCatalogueDecisionFacts& Facts = MachineFacts[Index];
                const FString Number = bLocked ? TEXT("LOCK")
                    : FString::Printf(TEXT("%02d"), ActionIndex + 1);
                DrawText(FString::Printf(TEXT("%s | %s"), *Number,
                    *Facts.ProcessStage), AccentInk, X + Pad, Rect.Y + 8.0f * S,
                    Small, Readability.DetailTextScale, false);

                // Recognisable source-derived silhouette today. ThumbnailAsset is an
                // explicit stable hook for approved authored renders later.
                const float PreviewY = Rect.Y + 28.0f * S;
                DrawRect(FLinearColor(0.02f, 0.035f, 0.04f, 0.95f),
                    X + Pad, PreviewY, Rect.W - 2.0f * Pad, 38.0f * S);
                const float CentreX = X + Rect.W * 0.5f;
                const FLinearColor Silhouette = bLocked
                    ? FLinearColor(0.23f, 0.27f, 0.28f, 1.0f)
                    : BrandPrimary.CopyWithNewOpacity(1.0f);
                if (Facts.PreviewKind == TEXT("ED_LINE")
                    || Facts.PreviewKind == TEXT("BODY_WELD_LINE")
                    || Facts.PreviewKind == TEXT("PROCESS_LINE"))
                {
                    DrawRect(Silhouette, X + 18.0f * S, PreviewY + 12.0f * S,
                        Rect.W - 36.0f * S, 20.0f * S);
                    for (int32 Module = 0; Module < 4; ++Module)
                        DrawRect(AccentInk, X + (26.0f + Module * 35.0f) * S,
                            PreviewY + 7.0f * S, 6.0f * S, 30.0f * S);
                }
                else if (Facts.PreviewKind == TEXT("ROBOT"))
                {
                    DrawRect(Silhouette, CentreX - 30.0f * S,
                        PreviewY + 27.0f * S, 60.0f * S, 7.0f * S);
                    DrawRect(Silhouette, CentreX - 5.0f * S,
                        PreviewY + 10.0f * S, 10.0f * S, 20.0f * S);
                    DrawRect(AccentInk, CentreX, PreviewY + 9.0f * S,
                        28.0f * S, 7.0f * S);
                }
                else
                {
                    DrawRect(Silhouette, CentreX - 55.0f * S,
                        PreviewY + 14.0f * S, 110.0f * S, 20.0f * S);
                    DrawRect(AccentInk, CentreX - 32.0f * S,
                        PreviewY + 7.0f * S, 64.0f * S, 10.0f * S);
                    DrawRect(AccentInk, CentreX - 46.0f * S,
                        PreviewY + 34.0f * S, 14.0f * S, 4.0f * S);
                    DrawRect(AccentInk, CentreX + 32.0f * S,
                        PreviewY + 34.0f * S, 14.0f * S, 4.0f * S);
                }

                const TArray<FString> NameLines = WrapCatalogueText(
                    Facts.DisplayName, 25, 2);
                for (int32 LineIndex = 0; LineIndex < NameLines.Num(); ++LineIndex)
                    DrawText(NameLines[LineIndex], MainInk, X + Pad,
                        Rect.Y + (70.0f + LineIndex * 16.0f) * S, Small,
                        Readability.NormalTextScale, false);
                DrawText(Facts.Purpose, MainInk, X + Pad, Rect.Y + 104.0f * S,
                    Small, Readability.DetailTextScale, false);
                DrawText(Facts.InputFlow, AccentInk, X + Pad, Rect.Y + 124.0f * S,
                    Small, Readability.DetailTextScale, false);
                DrawText(Facts.OutputFlow, AccentInk, X + Pad, Rect.Y + 141.0f * S,
                    Small, Readability.DetailTextScale, false);
                DrawText(Facts.FootprintAndServiceEnvelope, MainInk, X + Pad,
                    Rect.Y + 160.0f * S, Small, Readability.DetailTextScale, false);
                DrawText(Facts.RouteAndClearance, MainInk, X + Pad,
                    Rect.Y + 177.0f * S, Small, Readability.DetailTextScale, false);
                if (bLocked)
                {
                    const TArray<FString> ReasonLines = WrapCatalogueText(
                        Facts.LockReason, 29, 3);
                    for (int32 LineIndex = 0; LineIndex < ReasonLines.Num(); ++LineIndex)
                        DrawText(ReasonLines[LineIndex], LockedText, X + Pad,
                            Rect.Y + (198.0f + LineIndex * 13.0f) * S, Small,
                            Readability.DetailTextScale, false);
                }
                else DrawText(TEXT("READY TO PLACE"), AccentInk, X + Pad,
                    Rect.Y + 202.0f * S, Small, Readability.DetailTextScale, false);
            }
            else
            {
                DrawText(FString::Printf(TEXT("%02d"), ActionIndex + 1), AccentInk,
                    X + Pad, Rect.Y + 10.0f * S, Small,
                    Readability.DetailTextScale, false);
                const TArray<FString> NameLines = WrapCatalogueText(
                    Labels[ItemIndex], 25, 3);
                for (int32 LineIndex = 0; LineIndex < NameLines.Num(); ++LineIndex)
                    DrawText(NameLines[LineIndex], MainInk, X + Pad,
                        Rect.Y + (40.0f + LineIndex * 18.0f) * S, Small,
                        Readability.NormalTextScale, false);
                DrawText(TEXT("AREA SIZE SET DURING PLACEMENT"), MainInk,
                    X + Pad, Rect.Y + 112.0f * S, Small,
                    Readability.DetailTextScale, false);
                DrawText(SelectedBuildCategory == 1
                    ? TEXT("PORTS FOLLOW STORAGE TYPE")
                    : TEXT("CLEARANCE SHOWN IN GHOST"), AccentInk,
                    X + Pad, Rect.Y + 142.0f * S, Small,
                    Readability.DetailTextScale, false);
                DrawText(TEXT("READY TO PLACE"), AccentInk, X + Pad,
                    Rect.Y + 211.0f * S, Small,
                    Readability.DetailTextScale, false);
            }
        }
    }
    if (Labels.IsEmpty() && Small)
        DrawText(TEXT("NO ITEM IN THIS CATEGORY IS REQUIRED YET - CONTINUE WITH THE NEXT MACHINE"),
            Green, PanelX + 18.0f * S, Layout.Cards[0].Y + 30.0f * S,
            Small, Readability.NormalTextScale, false);
}

void ALBControlRoomHUD::DrawFactoryBrandEditor()
{
    if (!Canvas) return;
    const float W = static_cast<float>(Canvas->SizeX);
    const float H = static_cast<float>(Canvas->SizeY);
    const FLBHUDReadabilityContract Readability = MakeHUDReadabilityContract(W, H);
    const FLBFactoryBrandEditorLayout Layout = MakeFactoryBrandEditorLayout(W, H);
    const float S = Layout.Scale;
    const float Pad = 24.0f * S;
    const FLinearColor PrimaryText = ChooseReadableTextColour(DraftPrimaryMachineColour);
    const FLinearColor Back(0.014f, 0.022f, 0.026f, 0.995f);
    const FLinearColor Panel(0.045f, 0.060f, 0.064f, 1.0f);
    const FLinearColor White(0.94f, 0.97f, 0.95f, 1.0f);
    const FLinearColor Muted(0.67f, 0.76f, 0.73f, 1.0f);
    const FLinearColor Ready(0.18f, 0.90f, 0.55f, 1.0f);
    const FLinearColor Invalid(1.0f, 0.54f, 0.08f, 1.0f);
    const FLinearColor SafetyYellow = ULBFactoryBrandSubsystem::GetFixedSafetyYellowColour();
    const FLinearColor SafetyRed(0.85f, 0.025f, 0.02f, 1.0f);
    UFont* Small = GEngine ? GEngine->GetSmallFont() : nullptr;
    UFont* Large = GEngine ? GEngine->GetLargeFont() : nullptr;
    RefreshFactoryBrandValidation();
    const bool bReady = FactoryBrandValidationReason.StartsWith(TEXT("READY"));

    const auto DrawBorder = [this](const float X, const float Y, const float Width,
        const float Height, const FLinearColor& Colour, const float Thickness)
    {
        DrawRect(Colour, X, Y, Width, Thickness);
        DrawRect(Colour, X, Y + Height - Thickness, Width, Thickness);
        DrawRect(Colour, X, Y, Thickness, Height);
        DrawRect(Colour, X + Width - Thickness, Y, Thickness, Height);
    };

    // The settings surface dims the factory so swatches retain readable contrast.
    DrawRect(FLinearColor(0.0f, 0.006f, 0.007f, 0.78f), 0.0f, 0.0f, W, H);
    DrawRect(Back, Layout.BoxX, Layout.BoxY, Layout.BoxW, Layout.BoxH);
    DrawRect(DraftPrimaryMachineColour, Layout.BoxX, Layout.BoxY,
        Layout.BoxW, 58.0f * S);
    if (Large) DrawText(TEXT("FACTORY APPEARANCE"),
        PrimaryText, Layout.BoxX + Pad, Layout.BoxY + 14.0f * S,
        Large, Readability.HeadingTextScale, false);
    if (Small) DrawText(TEXT("EDIT THE LIVERY APPLIED TO EVERY APPROVED MACHINE"),
        PrimaryText, Layout.BoxX + Layout.BoxW * 0.47f,
        Layout.BoxY + 20.0f * S, Small, Readability.DetailTextScale, false);

    if (Small) DrawText(TEXT("FACTORY NAME  |  SELECT, TYPE, THEN ENTER"),
        Muted, Layout.BoxX + Pad, Layout.BoxY + 70.0f * S,
        Small, Readability.NormalTextScale, false);
    DrawRect(bEditingFactoryName ? DraftPrimaryMachineColour : Panel,
        Layout.BoxX + Pad, Layout.NameY, Layout.BoxW - 2.0f * Pad, 48.0f * S);
    if (Large) DrawText(FactoryNameEditBuffer + (bEditingFactoryName ? TEXT("|") : TEXT("")),
        bEditingFactoryName ? PrimaryText : FLinearColor::White,
        Layout.BoxX + 38.0f * S, Layout.NameY + 12.0f * S,
        Large, Readability.HeadingTextScale, false);
    if (SelectedBrandEditorControl == 0)
        DrawBorder(Layout.BoxX + Pad, Layout.NameY,
            Layout.BoxW - 2.0f * Pad, 48.0f * S, White, 3.0f * S);

    const auto DrawSwatchRow = [&](const TCHAR* Label, const float RowY,
        const int32 SelectedIndex, const int32 ControlIndex)
    {
        if (Small) DrawText(Label, Muted, Layout.BoxX + Pad,
            RowY - 28.0f * S, Small, Readability.NormalTextScale, false);
        for (int32 Index = 0; Index < FactoryLiverySwatchCount; ++Index)
        {
            const float X = Layout.BoxX + Pad
                + Index * (Layout.SwatchW + Layout.SwatchGap);
            DrawRect(FactoryLiverySwatches[Index], X, RowY,
                Layout.SwatchW, Layout.SwatchH);
            if (Index == SelectedIndex)
            {
                DrawBorder(X - 2.0f * S, RowY - 2.0f * S,
                    Layout.SwatchW + 4.0f * S, Layout.SwatchH + 4.0f * S,
                    White, 3.0f * S);
            }
        }
        if (SelectedBrandEditorControl == ControlIndex)
            DrawBorder(Layout.BoxX + Pad - 7.0f * S, RowY - 7.0f * S,
                Layout.BoxW - 2.0f * Pad + 14.0f * S,
                Layout.SwatchH + 14.0f * S, Ready, 2.0f * S);
    };
    DrawSwatchRow(TEXT("PRIMARY  |  PANELS, GUARDS AND CABINETS"),
        Layout.PrimaryY, SelectedPrimarySwatch, 1);
    DrawSwatchRow(TEXT("SECONDARY  |  FRAMES, PLINTHS AND HOUSINGS"),
        Layout.SecondaryY, SelectedSecondarySwatch, 2);

    const float PreviewX = Layout.BoxX + Pad;
    const float PreviewW = Layout.BoxW - 2.0f * Pad;
    const float PreviewH = 132.0f * S;
    DrawRect(Panel, PreviewX, Layout.PreviewY, PreviewW, PreviewH);
    if (Small) DrawText(TEXT("LIVE MACHINE PREVIEW"), Muted,
        PreviewX + 14.0f * S, Layout.PreviewY + 10.0f * S,
        Small, Readability.DetailTextScale, false);
    // Compact, legible equipment silhouette: player colours own the machine while
    // yellow guards and red emergency/state semantics remain locked for safety.
    const float MachineX = PreviewX + 18.0f * S;
    const float MachineY = Layout.PreviewY + 42.0f * S;
    DrawRect(DraftSecondaryMachineColour, MachineX, MachineY,
        PreviewW * 0.48f, 72.0f * S);
    DrawRect(DraftPrimaryMachineColour, MachineX + 22.0f * S,
        MachineY + 14.0f * S, PreviewW * 0.35f, 43.0f * S);
    DrawRect(SafetyYellow, MachineX + PreviewW * 0.38f,
        MachineY + 5.0f * S, 12.0f * S, 62.0f * S);
    DrawRect(SafetyRed, MachineX + 11.0f * S,
        MachineY - 10.0f * S, 12.0f * S, 12.0f * S);
    if (Small)
    {
        const float LegendX = PreviewX + PreviewW * 0.55f;
        DrawText(TEXT("PLAYER-SELECTED"), White, LegendX,
            MachineY + 3.0f * S, Small, Readability.NormalTextScale, false);
        DrawRect(DraftPrimaryMachineColour, LegendX,
            MachineY + 25.0f * S, 30.0f * S, 12.0f * S);
        DrawText(TEXT("PRIMARY"), White, LegendX + 39.0f * S,
            MachineY + 23.0f * S, Small, Readability.DetailTextScale, false);
        DrawRect(DraftSecondaryMachineColour, LegendX,
            MachineY + 44.0f * S, 30.0f * S, 12.0f * S);
        DrawText(TEXT("SECONDARY"), White, LegendX + 39.0f * S,
            MachineY + 42.0f * S, Small, Readability.DetailTextScale, false);
        DrawText(TEXT("LOCKED SAFETY  |  YELLOW GUARDS  +  RED EMERGENCY / FAULT"),
            SafetyYellow, LegendX, MachineY + 64.0f * S,
            Small, Readability.DetailTextScale, false);
    }

    if (Small) DrawText(FactoryBrandValidationReason,
        bReady ? Ready : Invalid, Layout.BoxX + Pad,
        Layout.BoxY + 518.0f * S, Small, Readability.NormalTextScale, false);
    const float ButtonW = 214.0f * S;
    const float ButtonX = Layout.BoxX + Layout.BoxW - Pad - ButtonW;
    const FLinearColor ButtonFill = bReady ? DraftPrimaryMachineColour
        : FLinearColor(0.14f, 0.15f, 0.15f, 1.0f);
    DrawRect(ButtonFill, ButtonX, Layout.ContinueY, ButtonW, 48.0f * S);
    if (SelectedBrandEditorControl == 3)
        DrawBorder(ButtonX - 3.0f * S, Layout.ContinueY - 3.0f * S,
            ButtonW + 6.0f * S, 54.0f * S, White, 3.0f * S);
    if (Small) DrawText(TEXT("APPLY & CLOSE"),
        bReady ? ChooseReadableTextColour(ButtonFill) : Muted,
        ButtonX + 34.0f * S, Layout.ContinueY + 15.0f * S,
        Small, Readability.NormalTextScale, false);
    if (Small) DrawText(TEXT("UP/DOWN: FIELD   |   LEFT/RIGHT: COLOUR   |   A/ENTER: SELECT"),
        Muted, Layout.BoxX + Pad, Layout.ContinueY + 16.0f * S,
        Small, Readability.DetailTextScale, false);
}

void ALBControlRoomHUD::DrawManagementHUD()
{
    if (!Canvas) return;
    if (ManagementPage == ELBManagementPage::Overview)
    {
        DrawProductionFlowHUD();
        return;
    }
    if (ManagementPage == ELBManagementPage::FactoryBuild)
    {
        DrawFactoryBuildHUD();
        return;
    }
    const float W = static_cast<float>(Canvas->SizeX);
    const float H = static_cast<float>(Canvas->SizeY);
    const FLBHUDReadabilityContract Readability = MakeHUDReadabilityContract(W, H);
    const float S = Readability.LayoutScale;
    const FLBManagementHUDLayout Layout = MakeManagementHUDLayout(W, H,
        GetPersistentHUDHeight(), GetManagementInformationLineCount(),
        GetManagementActionCount());
    const float PanelW = Layout.PanelW;
    const float PanelX = Layout.PanelX;
    const float PanelY = Layout.PanelY;
    const float PanelH = Layout.PanelH;
    const FLinearColor Back(0.014f, 0.024f, 0.028f, 0.96f);
    const FLinearColor Row(0.055f, 0.075f, 0.080f, 0.96f);
    const FLinearColor White(0.96f, 0.98f, 0.96f, 1.0f);
    const FLinearColor Amber(1.0f, 0.66f, 0.08f, 1.0f);
    const FLinearColor Critical(0.96f, 0.16f, 0.09f, 1.0f);
    const FLinearColor Muted(0.62f, 0.75f, 0.70f, 1.0f);
    UFont* Small = GEngine ? GEngine->GetSmallFont() : nullptr;
    UFont* Large = GEngine ? GEngine->GetLargeFont() : nullptr;

    const ULBFactoryBrandSubsystem* Brand = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryBrandSubsystem>() : nullptr;
    const FLinearColor Primary = Brand ? Brand->GetPrimaryColour()
        : FLinearColor(0.035f, 0.36f, 0.16f, 1.0f);
    const FLinearColor Header(Primary.R * 0.62f, Primary.G * 0.62f,
        Primary.B * 0.62f, 0.98f);
    const FLinearColor Selected = Primary.CopyWithNewOpacity(0.98f);
    const FLinearColor Green = Primary.GetLuminance() < 0.35f
        ? Primary + FLinearColor(0.22f, 0.38f, 0.22f, 0.0f) : Primary;
    const FLinearColor HeaderText = ChooseReadableTextColour(Header);
    const FLinearColor SelectedText = ChooseReadableTextColour(Selected);
    ULBFactoryUIStateSubsystem* UIState = GetWorld()
        ? GetWorld()->GetSubsystem<ULBFactoryUIStateSubsystem>() : nullptr;
    const FLBFactoryUIStateSnapshot EmptySnapshot;
    const FLBFactoryUIStateSnapshot& Snapshot = UIState
        ? UIState->GetSnapshot() : EmptySnapshot;
    const FLBFactoryUIManagementSnapshot& Management = Snapshot.Management;

    DrawRect(Back, PanelX, PanelY, PanelW, PanelH);
    DrawRect(Header, PanelX, PanelY, PanelW, Layout.HeaderH);
    FString HeaderName = Brand ? Brand->GetFactoryName().ToUpper() : TEXT("YOUR FACTORY");
    HeaderName = HeaderName.Left(Readability.bCompactMode ? 12 : 30);
    if (Large) DrawText(FString::Printf(TEXT("%s  |  MANAGEMENT"), *HeaderName),
        HeaderText, PanelX + 22.0f * S, PanelY + 17.0f * S, Large,
        Readability.HeadingTextScale, false);
    if (Small)
    {
        const FString Balance = Management.bCampaignInitialised
            ? FString::Printf(TEXT("CASH  %s   |   RP  %lld"),
                *FormatMoneyPence(Management.CashBalancePence),
                Management.AvailableResearchPoints)
            : TEXT("MANAGEMENT AUTHORITY INITIALISING");
        DrawText(Balance, HeaderText, PanelX + PanelW * 0.54f,
            PanelY + 23.0f * S, Small, Readability.DetailTextScale, false);
    }

    for (int32 Index = 0; Index < Layout.PageTabs.Num(); ++Index)
    {
        const FLBHUDRect& Tab = Layout.PageTabs[Index];
        const bool bActive = Index == static_cast<int32>(ManagementPage);
        FString PageLabel = ManagementPageName(static_cast<ELBManagementPage>(Index));
        if (Readability.bCompactMode)
        {
            if (Index == static_cast<int32>(ELBManagementPage::SupportFleet))
                PageLabel = TEXT("MAINT.");
            else if (Index == static_cast<int32>(ELBManagementPage::Analytics))
                PageLabel = TEXT("DATA");
        }
        DrawRect(bActive ? Selected : Row, Tab.X, Tab.Y, Tab.W, Tab.H);
        if (Small) DrawText(PageLabel,
            bActive ? SelectedText : Green, Tab.X + 7.0f * S, Tab.Y + 13.0f * S,
            Small, Readability.NormalTextScale, false);
    }

    const float ContentX = Layout.ContentX;
    float Y = Layout.ContentY;
    auto DrawLineColour = [&](const FString& Label, const FString& Value, const FLinearColor& ValueColour)
    {
        if (Small)
        {
            DrawText(Label, Green, ContentX, Y, Small,
                Readability.NormalTextScale, false);
            DrawText(Value, ValueColour, ContentX + PanelW * 0.43f, Y,
                Small, Readability.NormalTextScale, false);
        }
        Y += Layout.InformationLineStep;
    };
    auto DrawLine = [&](const FString& Label, const FString& Value)
    {
        DrawLineColour(Label, Value, White);
    };
    auto DrawAction = [&](const FString& Label, const int32 Index)
    {
        if (!Layout.ActionRows.IsValidIndex(Index)) return;
        const FLBHUDRect& Rect = Layout.ActionRows[Index];
        const bool bActive = SelectedManagementAction == Index;
        DrawRect(bActive ? Selected : Row, Rect.X, Rect.Y, Rect.W, Rect.H);
        DrawRect(bActive ? White : Green, Rect.X, Rect.Y, Rect.W, 3.0f * S);
        if (Small) DrawText(Label, bActive ? SelectedText : Green,
            Rect.X + 12.0f * S, Rect.Y + 13.0f * S, Small,
            Readability.NormalTextScale, false);
    };

    ALBControlRoomOperationsConsole* Operations = FindOperationsConsole();
    if (ManagementPage == ELBManagementPage::Production)
    {
        if (!Operations)
        {
            const ALBPlayerBuiltPressFlowController* Flow = FindPlayerFlow();
            DrawLine(TEXT("VEHICLE PROGRAM"), GetSelectedVehicleDisplayName());
            DrawLine(TEXT("PANEL BATCH"), FuturePanelTypes[SelectedPanelType].ToString());
            DrawLine(TEXT("QUANTITY"), FString::FromInt(PlayerBatchQuantity));
            DrawLine(TEXT("QUEUED ORDERS"), Flow
                ? FString::FromInt(Flow->GetPanelBatches().Num()) : TEXT("ORDER SCHEDULER OFFLINE"));
            DrawAction(TEXT("2040 BEV PROGRAM SELECTED"), 0);
            DrawAction(TEXT("CHANGE PANEL TYPE"), 1);
            DrawAction(TEXT("QUANTITY -"), 2);
            DrawAction(TEXT("QUANTITY +"), 3);
            DrawAction(TEXT("QUEUE PRODUCTION BATCH"), 4);
        }
        else
        {
            const FLBControlRoomOperationsSaveState State = Operations->CaptureSaveState();
            DrawLine(TEXT("STATE"), OrderStateName(State.OrderState));
            DrawLine(TEXT("PANEL"), State.PanelFamily.ToString());
            DrawLine(TEXT("QUANTITY"), FString::FromInt(State.RequestedQuantity));
            DrawLine(TEXT("COIL"), State.SelectedCoilId.IsEmpty()
                ? TEXT("NOT SELECTED") : State.SelectedCoilId);
            DrawAction(TEXT("CHANGE PANEL FAMILY"), 0);
            DrawAction(TEXT("QUANTITY -"), 1);
            DrawAction(TEXT("QUANTITY +"), 2);
            DrawAction(TEXT("CHANGE PRIORITY"), 3);
            DrawAction(TEXT("CREATE / VALIDATE ORDER"), 4);
            DrawAction(TEXT("SELECT AVAILABLE COIL"), 5);
            DrawAction(TEXT("LOAD SELECTED COIL"), 6);
            DrawAction(State.OrderState == ELBControlRoomOrderState::Running
                ? TEXT("PAUSE LINE") : TEXT("START / RESUME LINE"), 7);
            DrawAction(TEXT("CONTROLLED STOP"), 8);
        }
    }
    else if (ManagementPage == ELBManagementPage::PressTrains)
    {
        int32 TrainCount = 0;
        for (TActorIterator<ALBPressTrainAStation> It(GetWorld()); It; ++It) ++TrainCount;
        DrawLine(TEXT("CAPITAL ASSETS"), Management.CapitalAssetCount > 0
            ? FString::FromInt(Management.CapitalAssetCount) : TEXT("NONE PURCHASED YET"));
        DrawLine(TEXT("LIVE PROCESS ASSETS"), FString::FromInt(Snapshot.OperationalAssetCount));
        DrawLine(TEXT("PRESS TRAINS"), TrainCount > 0
            ? FString::FromInt(TrainCount) : TEXT("NONE INSTALLED"));
        DrawLine(TEXT("INSTALLED UPGRADES"), Management.UpgradeCount > 0
            ? FString::FromInt(Management.UpgradeCount) : TEXT("NONE INSTALLED"));
        DrawLine(TEXT("QUALITY OUTPUT"), Management.ProducedCount > 0
            ? FString::Printf(TEXT("%lld PRODUCED / %lld PASSED"),
                Management.ProducedCount, Management.PassedCount)
            : TEXT("NO PRODUCTION RECORDS"));
        DrawLine(TEXT("CAPITAL SPEND"), FormatMoneyPence(Management.CapitalSpendPence));
        if (Operations) DrawAction(TEXT("SELECT NEXT AVAILABLE PRESS TRAIN"), 0);
    }
    else if (ManagementPage == ELBManagementPage::SupportFleet)
    {
        DrawLine(TEXT("TRACKED ASSETS"), FString::FromInt(
            Management.TrackedMaintenanceAssetCount));
        DrawLineColour(TEXT("SERVICE DUE"), FString::FromInt(Management.ServiceDueCount),
            Management.ServiceDueCount > 0 ? Amber : Green);
        DrawLine(TEXT("PLANNED SERVICES"), FString::FromInt(Management.PlannedServiceCount));
        DrawLineColour(TEXT("ACTIVE FAULTS"), FString::FromInt(Management.ManagementFaultCount),
            Management.ManagementFaultCount > 0 ? Critical : Green);
        int32 VisibleRows = 0;
        for (const FLBFactoryUIManagementAssetSnapshot& Asset : Management.Assets)
        {
            if (!Asset.bHasMaintenance || VisibleRows >= 3) continue;
            const FString State = Asset.bFaulted
                ? FString::Printf(TEXT("FAULT  %s"), *Asset.FaultCode.ToString())
                : Asset.bServiceDue
                    ? FString::Printf(TEXT("SERVICE DUE  %.0f%% WEAR"), Asset.WearFraction * 100.0)
                    : FString::Printf(TEXT("WEAR  %.0f%%"), Asset.WearFraction * 100.0);
            DrawLineColour(Asset.AssetId.ToString(), State,
                Asset.bFaulted ? Critical : Asset.bServiceDue ? Amber : White);
            ++VisibleRows;
        }
        if (Management.TrackedMaintenanceAssetCount == 0 && Small)
            DrawText(TEXT("NO MAINTAINABLE ASSETS REGISTERED YET"), Muted,
                ContentX, Y + 8.0f * S, Small, Readability.DetailTextScale, false);
        if (Operations)
        {
            DrawAction(TEXT("SELECT NEXT SUPPORT UNIT"), 0);
            DrawAction(TEXT("DISPATCH SELECTED UNIT"), 1);
            DrawAction(TEXT("RECALL SELECTED UNIT"), 2);
        }
    }
    else if (ManagementPage == ELBManagementPage::Research)
    {
        DrawLine(TEXT("AVAILABLE RP"), FString::Printf(TEXT("%lld"),
            Management.AvailableResearchPoints));
        DrawLine(TEXT("TOTAL EARNED"), FString::Printf(TEXT("%lld"),
            Management.TotalResearchEarnedPoints));
        DrawLine(TEXT("TOTAL SPENT"), FString::Printf(TEXT("%lld"),
            Management.TotalResearchSpentPoints));
        DrawLine(TEXT("UNLOCKS"), FString::FromInt(Management.ResearchUnlockIds.Num()));
        for (int32 Index = 0;
            Index < Management.ResearchUnlockIds.Num() && Index < 3; ++Index)
        {
            DrawLine(FString::Printf(TEXT("UNLOCK %02d"), Index + 1),
                Management.ResearchUnlockIds[Index].ToString());
        }
        if (Management.ResearchUnlockIds.IsEmpty() && Small)
            DrawText(TEXT("NO RESEARCH UNLOCKS PURCHASED YET"), Muted,
                ContentX, Y + 8.0f * S, Small, Readability.DetailTextScale, false);
    }
    else if (ManagementPage == ELBManagementPage::Analytics)
    {
        const bool bHasAnalytics = Management.AnalyticsBucketCount > 0;
        DrawLine(TEXT("SAMPLES"), FString::FromInt(Management.AnalyticsBucketCount));
        DrawLine(TEXT("GOOD THROUGHPUT"), bHasAnalytics
            ? FString::Printf(TEXT("%.1f UNITS / HOUR"),
                Management.ThroughputGoodUnitsPerHour) : TEXT("NO DATA"));
        DrawLine(TEXT("AVAILABILITY"), bHasAnalytics
            ? FormatPercent(Management.AvailabilityRatio) : TEXT("NO DATA"));
        DrawLine(TEXT("PERFORMANCE"), bHasAnalytics
            ? FormatPercent(Management.PerformanceRatio) : TEXT("NO DATA"));
        DrawLine(TEXT("QUALITY"), bHasAnalytics
            ? FormatPercent(Management.QualityRatio) : TEXT("NO DATA"));
        DrawLine(TEXT("OEE"), bHasAnalytics
            ? FormatPercent(Management.OEE) : TEXT("NO DATA"));
        DrawLine(TEXT("STARVED / BLOCKED"), bHasAnalytics
            ? FString::Printf(TEXT("%s / %s"), *FormatPercent(Management.StarvationRatio),
                *FormatPercent(Management.BlockingRatio)) : TEXT("NO DATA"));
        DrawLine(TEXT("FAULT DOWNTIME"), bHasAnalytics
            ? FormatPercent(Management.FaultDowntimeRatio) : TEXT("NO DATA"));
        const bool bHasCampaignAuthority = FindCampaignController() != nullptr;
        DrawLineColour(TEXT("MANUAL SAVE / LOAD"), bHasCampaignAuthority
                ? CampaignPersistenceFeedback : TEXT("SAVE AUTHORITY OFFLINE"),
            !bHasCampaignAuthority ? Critical
                : bCampaignLoadConfirmationArmed ? Amber
                : !bCampaignPersistenceAttempted ? Muted
                : bCampaignPersistenceSucceeded ? Green : Critical);
        if (bHasCampaignAuthority)
        {
            DrawAction(TEXT("SAVE CAMPAIGN"), 0);
            DrawAction(bCampaignLoadConfirmationArmed
                ? TEXT("CONFIRM LOAD - UNSAVED CHANGES WILL BE LOST")
                : TEXT("LOAD CAMPAIGN"), 1);
        }
    }

    if (Small)
    {
        DrawText(TEXT("L1/R1 OR LEFT/RIGHT: PAGE   |   UP/DOWN: SELECT   |   X/ENTER: CONFIRM   |   TOUCHPAD/M: CLOSE"),
            Green, PanelX + 18.0f * S, PanelY + PanelH - 32.0f * S,
            Small, Readability.DetailTextScale, false);
    }
}

#endif

void ALBControlRoomHUD::DrawHUD()
{
    EnsureMandatoryFactorySetup();
    SyncModernOverviewWidget();
}
