#include "LBManagementPawn.h"
#include "Camera/CameraComponent.h"
#include "Components/HierarchicalInstancedStaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/InputComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/SceneComponent.h"
#include "Components/ShapeComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/WidgetInteractionComponent.h"
#include "Components/BoxComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/HUD.h"
#include "GameFramework/SpringArmComponent.h"
#include "LBPR004Station.h"
#include "LBControlRoomHUD.h"
#include "LBControlRoomOperationsConsole.h"
#include "LBControlRoomPawn.h"
#include "LBFactoryBrandSubsystem.h"
#include "LBFactoryBuildMachine.h"
#include "LBFactoryMachineBuilderSubsystem.h"
#include "LBFactoryUIStateSubsystem.h"
#include "LBECoatLineActor.h"
#include "LBBodyWeldLineActor.h"
#include "LBPressTrainAStation.h"
#include "LBPressTrainIdentitySubsystem.h"
#include "LBPressShopBuildAuthority.h"
#include "LBPressShopStorageZone.h"
#include "LBCoilAGVController.h"
#include "DrawDebugHelpers.h"
#include "Engine/OverlapResult.h"
#include "EngineUtils.h"
#include "InputCoreTypes.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
bool AccumulateRenderableActorBounds(AActor* Actor, FBox& InOutBounds)
{
    if (!IsValid(Actor)) return false;
    FBox ActorVisualBounds(ForceInit);
    TInlineComponentArray<UPrimitiveComponent*> PrimitiveComponents;
    Actor->GetComponents(PrimitiveComponents, true);
    for (UPrimitiveComponent* Primitive : PrimitiveComponents)
    {
        // Protected UBox envelopes and other query shapes are placement authority, not
        // presentation. Framing them made a sparse shop look like an empty warehouse even
        // when the player's visible machines occupied only a compact part of that volume.
        if (!IsValid(Primitive) || Primitive->IsA<UShapeComponent>()
            || !Primitive->IsRegistered() || !Primitive->ShouldRender()) continue;
        const FBox ComponentBounds = Primitive->Bounds.GetBox();
        const FVector ComponentSize = ComponentBounds.GetSize();
        if (!ComponentBounds.IsValid || ComponentSize.ContainsNaN()
            || ComponentSize.GetMax() <= 1.0f || ComponentSize.GetMax() > 30000.0f) continue;
        ActorVisualBounds += ComponentBounds;
    }
    if (!ActorVisualBounds.IsValid) return false;
    InOutBounds += ActorVisualBounds;
    return true;
}

FColor Opaque(const FColor& Colour)
{
    return FColor(Colour.R, Colour.G, Colour.B, 255);
}

FString FriendlyActorName(const FString& ActorLabel)
{
    // Runtime suffixes are useful for logs, not for the player's obstruction headline.
    // Strip them before NameToDisplayString turns underscores into spaces.
    FString Result = ActorLabel.TrimStartAndEnd();
    int32 GeneratedSuffix = INDEX_NONE;
    if (Result.FindLastChar(TEXT('_'), GeneratedSuffix)
        && Result.Mid(GeneratedSuffix + 1).IsNumeric())
    {
        Result.LeftInline(GeneratedSuffix);
    }
    return FName::NameToDisplayString(Result.TrimStartAndEnd(), false).TrimStartAndEnd();
}

FString StableIdFromActor(const AActor* Actor)
{
    if (!Actor) return FString();
    if (const ALBFactoryBuildMachine* Machine = Cast<ALBFactoryBuildMachine>(Actor))
        return Machine->GetMachineId().ToString();
    if (const ALBPressTrainAStation* Train = Cast<ALBPressTrainAStation>(Actor))
        return Train->GetTrainId().ToString();
    if (const ALBPressShopStorageZone* Storage = Cast<ALBPressShopStorageZone>(Actor))
        return Storage->GetZoneId().ToString();
    if (const ALBFactoryAGVInfrastructure* Infrastructure = Cast<ALBFactoryAGVInfrastructure>(Actor))
        return Infrastructure->GetInfrastructureId().ToString();
    if (const ALBBodyWeldLineActor* Weld = Cast<ALBBodyWeldLineActor>(Actor))
        return Weld->GetLineId().ToString();
    if (const ALBECoatLineActor* ECoat = Cast<ALBECoatLineActor>(Actor))
        return ECoat->GetLineId().ToString();
    return FString();
}

void SetGhostPrimitiveFlags(UPrimitiveComponent* Primitive)
{
    if (!Primitive) return;
    Primitive->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Primitive->SetGenerateOverlapEvents(false);
    Primitive->SetCanEverAffectNavigation(false);
    Primitive->SetCastShadow(false);
    Primitive->SetRenderCustomDepth(false);
}

void DrawMissingFloorCue(const UWorld* World, const UCameraComponent* Camera,
    const FLBPlacementPreviewStyle& Style)
{
    if (!World || !Camera) return;
    const FVector Centre = Camera->GetComponentLocation() + Camera->GetForwardVector() * 1400.0f;
    const FVector Right = Camera->GetRightVector() * 55.0f;
    const FVector Up = Camera->GetUpVector() * 55.0f;
    const FColor LineColour = Opaque(Style.FootprintColour);
    DrawDebugLine(World, Centre - Right, Centre + Up, LineColour, false, -1.0f, 0, 7.0f);
    DrawDebugLine(World, Centre + Up, Centre + Right, LineColour, false, -1.0f, 0, 7.0f);
    DrawDebugLine(World, Centre + Right, Centre - Up, LineColour, false, -1.0f, 0, 7.0f);
    DrawDebugLine(World, Centre - Up, Centre - Right, LineColour, false, -1.0f, 0, 7.0f);
}

void DrawPlacementGroundFootprint(const UWorld* World, const FTransform& PreviewTransform,
    const FLBPlacementPreviewGeometry& Geometry, const FLBPlacementPreviewStyle& Style)
{
    if (!World || Geometry.GroundHalfExtent.X <= 0.0f || Geometry.GroundHalfExtent.Y <= 0.0f) return;
    const FQuat Rotation = PreviewTransform.GetRotation();
    DrawDebugSolidBox(World, Geometry.GroundCentre, Geometry.GroundHalfExtent,
        Rotation, Style.FootprintColour, false, -1.0f, 0);
    DrawDebugBox(World, Geometry.GroundCentre, Geometry.GroundHalfExtent,
        Rotation, Opaque(Style.FootprintColour), false, -1.0f, 0, 7.0f);

    // Bounded diagonal hatching reads as a footprint even for colour-blind players and
    // remains cheap enough for the complete 195 m ED-line exclusion area.
    const float HalfX = Geometry.GroundHalfExtent.X;
    const float HalfY = Geometry.GroundHalfExtent.Y;
    const float Sweep = HalfX + HalfY;
    const float Spacing = FMath::Max(Style.HatchSpacingCm, (Sweep * 2.0f) / 64.0f);
    const FColor HatchColour = Opaque(Style.AccentColour);
    for (float Offset = -Sweep; Offset <= Sweep + 0.1f; Offset += Spacing)
    {
        const float X0 = FMath::Max(-HalfX, -HalfY + Offset);
        const float X1 = FMath::Min(HalfX, HalfY + Offset);
        if (X1 <= X0) continue;
        const FVector LocalA(X0, X0 - Offset, 3.0f);
        const FVector LocalB(X1, X1 - Offset, 3.0f);
        DrawDebugLine(World,
            Geometry.GroundCentre + Rotation.RotateVector(LocalA),
            Geometry.GroundCentre + Rotation.RotateVector(LocalB),
            HatchColour, false, -1.0f, 0, 1.5f);
    }
}

void DrawPlacementEnvelope(const UWorld* World, const FTransform& PreviewTransform,
    const FLBPlacementPreviewGeometry& Geometry, const FLBPlacementPreviewStyle& Style)
{
    if (!World || Geometry.EnvelopeHalfExtent.GetMin() <= 0.0f) return;
    const FQuat Rotation = PreviewTransform.GetRotation();
    const FColor LineColour = Opaque(Style.FootprintColour);
    DrawDebugBox(World, Geometry.EnvelopeCentre, Geometry.EnvelopeHalfExtent,
        Rotation, LineColour, false, -1.0f, 0, 6.0f);

    const float PostHeight = FMath::Clamp(Geometry.EnvelopeHalfExtent.Z * 0.45f, 60.0f, 300.0f);
    for (const float X : {-Geometry.GroundHalfExtent.X, Geometry.GroundHalfExtent.X})
    {
        for (const float Y : {-Geometry.GroundHalfExtent.Y, Geometry.GroundHalfExtent.Y})
        {
            const FVector Base = Geometry.GroundCentre
                + Rotation.RotateVector(FVector(X, Y, 4.0f));
            DrawDebugLine(World, Base, Base + FVector(0.0f, 0.0f, PostHeight),
                LineColour, false, -1.0f, 0, 5.0f);
        }
    }
}

void DrawPlacementState(const UWorld* World, const FTransform& PreviewTransform,
    const FLBPlacementPreviewGeometry& Geometry, const FLBPlacementPreviewStyle& Style)
{
    if (!World) return;
    const FQuat Rotation = PreviewTransform.GetRotation();
    const FColor Colour = Opaque(Style.FootprintColour);
    const float GlyphSize = FMath::Clamp(
        FMath::Min(Geometry.GroundHalfExtent.X, Geometry.GroundHalfExtent.Y) * 0.28f,
        55.0f, 180.0f);
    const FVector Centre = Geometry.GroundCentre + FVector(0.0f, 0.0f, 12.0f);
    const auto Point = [&Centre, &Rotation](const float X, const float Y)
    {
        return Centre + Rotation.RotateVector(FVector(X, Y, 0.0f));
    };
    if (Style.State == ELBPlacementPreviewState::Ready)
    {
        DrawDebugLine(World, Point(-GlyphSize, 0.0f), Point(-GlyphSize * 0.25f, -GlyphSize * 0.65f),
            Colour, false, -1.0f, 0, 13.0f);
        DrawDebugLine(World, Point(-GlyphSize * 0.25f, -GlyphSize * 0.65f), Point(GlyphSize, GlyphSize),
            Colour, false, -1.0f, 0, 13.0f);
    }
    else if (Style.State == ELBPlacementPreviewState::Blocked)
    {
        DrawDebugLine(World, Point(-GlyphSize, -GlyphSize), Point(GlyphSize, GlyphSize),
            Colour, false, -1.0f, 0, 13.0f);
        DrawDebugLine(World, Point(-GlyphSize, GlyphSize), Point(GlyphSize, -GlyphSize),
            Colour, false, -1.0f, 0, 13.0f);
    }

}

void DrawProcessFlowIntent(const UWorld* World,
    const FLBPlacementPreviewGeometry& Geometry)
{
    if (!World || !Geometry.bShowProcessFlow) return;
    const FVector Flow = (Geometry.OutputSocket - Geometry.InputSocket).GetSafeNormal();
    if (Flow.IsNearlyZero()) return;
    const FColor InputColour(45, 190, 255);
    const FColor OutputColour(255, 175, 35);
    DrawDebugSphere(World, Geometry.InputSocket, 38.0f, 12, InputColour,
        false, -1.0f, 0, 5.0f);
    DrawDebugSphere(World, Geometry.OutputSocket, 38.0f, 12, OutputColour,
        false, -1.0f, 0, 5.0f);
    DrawDebugDirectionalArrow(World, Geometry.InputSocket - Flow * 160.0f,
        Geometry.InputSocket + Flow * 120.0f, 55.0f, InputColour,
        false, -1.0f, 0, 6.0f);
    DrawDebugDirectionalArrow(World, Geometry.OutputSocket - Flow * 120.0f,
        Geometry.OutputSocket + Flow * 180.0f, 55.0f, OutputColour,
        false, -1.0f, 0, 6.0f);
    DrawDebugLine(World, Geometry.InputSocket, Geometry.OutputSocket,
        FColor(225, 235, 240), false, -1.0f, 0, 2.0f);
    // Port meaning is also present in the placement card. Ground rings/arrows remain
    // world-anchored while all player-facing text stays safe-area screen-space.
}

bool FindNamedBlockingOverlap(UWorld* World, const FVector& Centre, const FVector& HalfExtent,
    const FQuat& Rotation, const AActor* IgnoredActor, FString& OutActorLabel,
    FString& OutComponentLabel, FString* OutStableId = nullptr)
{
    OutActorLabel.Reset();
    OutComponentLabel.Reset();
    if (OutStableId) OutStableId->Reset();
    if (!World || HalfExtent.GetMin() <= 0.0f) return false;
    TArray<FOverlapResult> Overlaps;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(LBNamedPlacementObstruction), false, IgnoredActor);
    const bool bBlocked = World->OverlapMultiByChannel(Overlaps, Centre, Rotation,
        ECC_WorldDynamic, FCollisionShape::MakeBox(HalfExtent), Params);
    if (!bBlocked) return false;
    const FOverlapResult* Named = Overlaps.FindByPredicate([](const FOverlapResult& Result)
    {
        return Result.bBlockingHit && (Result.GetActor() || Result.GetComponent());
    });
    if (!Named) Named = Overlaps.FindByPredicate([](const FOverlapResult& Result)
    {
        return Result.GetActor() || Result.GetComponent();
    });
    if (Named)
    {
        if (const AActor* Actor = Named->GetActor())
        {
            OutActorLabel = FriendlyActorName(Actor->GetActorNameOrLabel());
            if (OutStableId) *OutStableId = StableIdFromActor(Actor);
        }
        if (const UPrimitiveComponent* Component = Named->GetComponent())
            OutComponentLabel = Component->GetName();
    }
    return true;
}
}

FLBPlacementPreviewStyle ALBManagementPawn::BuildPlacementPreviewStyle(
    const bool bHasFactoryFloor, const bool bPlacementAllowed, const FString& AuthorityReason)
{
    FLBPlacementPreviewStyle Style;
    Style.AuthorityReason = AuthorityReason.TrimStartAndEnd();
    const FString UpperReason = Style.AuthorityReason.ToUpper();
    if (!bHasFactoryFloor)
    {
        Style.State = ELBPlacementPreviewState::WaitingForSurface;
        Style.FootprintColour = FColor(255, 190, 40, 48);
        Style.AccentColour = FColor(255, 235, 170);
        Style.StateMarker = TEXT("[WAIT] FIND FACTORY FLOOR");
        Style.NextAction = TEXT("MOVE CURSOR ONTO AN AUTHORISED FACTORY FLOOR");
    }
    else if (bPlacementAllowed)
    {
        Style.State = ELBPlacementPreviewState::Ready;
        Style.FootprintColour = FColor(45, 225, 120, 48);
        Style.AccentColour = FColor(205, 255, 225);
        Style.StateMarker = TEXT("[OK] READY TO BUILD");
        Style.NextAction = TEXT("CLICK / CONFIRM TO BUILD   |   R TO ROTATE   |   ESC TO CANCEL");
    }
    else
    {
        Style.State = ELBPlacementPreviewState::Blocked;
        Style.FootprintColour = FColor(255, 65, 50, 48);
        Style.AccentColour = FColor(255, 215, 205);
        Style.StateMarker = TEXT("[X] CANNOT BUILD HERE");
        if (UpperReason.Contains(TEXT("OBSTRUCT")) || UpperReason.Contains(TEXT("OVERLAP"))
            || UpperReason.Contains(TEXT("OCCUPIES")) || UpperReason.Contains(TEXT("MUST REMAIN CLEAR")))
        {
            Style.NextAction = Style.AuthorityReason.IsEmpty()
                ? TEXT("MOVE OR ROTATE AWAY FROM THE NAMED OBSTRUCTION")
                : FString::Printf(TEXT("%s\nMOVE OR ROTATE AWAY FROM THE NAMED OBSTRUCTION"),
                    *Style.AuthorityReason);
        }
        else if (UpperReason.Contains(TEXT("OUTSIDE")) || UpperReason.Contains(TEXT("NOT AUTHORISED IN THIS BAY")))
        {
            Style.NextAction = Style.AuthorityReason.IsEmpty()
                ? TEXT("MOVE THE COMPLETE FOOTPRINT INSIDE AN AUTHORISED BAY")
                : FString::Printf(TEXT("%s\nMOVE THE COMPLETE FOOTPRINT INSIDE AN AUTHORISED BAY"),
                    *Style.AuthorityReason);
        }
        else if (UpperReason.Contains(TEXT("ROUTE")))
        {
            Style.NextAction = Style.AuthorityReason.IsEmpty()
                ? TEXT("DRAW OR MOVE AN AGV ROUTE WITHIN THE REQUIRED REACH")
                : FString::Printf(TEXT("%s\nDRAW OR MOVE AN AGV ROUTE WITHIN THE REQUIRED REACH"),
                    *Style.AuthorityReason);
        }
        else if (UpperReason.StartsWith(TEXT("PLACE ")) || UpperReason.StartsWith(TEXT("COMPLETE "))
            || UpperReason.StartsWith(TEXT("DRAW ")) || UpperReason.StartsWith(TEXT("WAIT ")))
        {
            Style.NextAction = Style.AuthorityReason;
        }
        else
        {
            Style.NextAction = Style.AuthorityReason.IsEmpty()
                ? TEXT("MOVE OR ROTATE THE FOOTPRINT; CHECK THE REASON IN THE BUILD PANEL")
                : FString::Printf(TEXT("%s\nMOVE OR ROTATE THE FOOTPRINT; CHECK THE BUILD PANEL"),
                    *Style.AuthorityReason);
        }
    }
    return Style;
}

FLBPlacementPreviewGeometry ALBManagementPawn::BuildPlacementPreviewGeometry(
    const FTransform& PreviewTransform, const FVector& EnvelopeRelativeCentre,
    const FVector& EnvelopeHalfExtent, const float FloorZ, const bool bFlowAlongLocalX,
    const bool bShowProcessFlow)
{
    FLBPlacementPreviewGeometry Geometry;
    Geometry.EnvelopeHalfExtent = EnvelopeHalfExtent.GetAbs();
    Geometry.EnvelopeCentre = PreviewTransform.TransformPosition(EnvelopeRelativeCentre);
    const FVector LocalGroundCentre(EnvelopeRelativeCentre.X, EnvelopeRelativeCentre.Y, 0.0f);
    Geometry.GroundCentre = PreviewTransform.TransformPosition(LocalGroundCentre);
    Geometry.GroundCentre.Z = FloorZ + 2.0f;
    Geometry.GroundHalfExtent = FVector(Geometry.EnvelopeHalfExtent.X,
        Geometry.EnvelopeHalfExtent.Y, 2.0f);
    const FVector LocalAxis = bFlowAlongLocalX ? FVector::ForwardVector : FVector::RightVector;
    const float AxisHalfExtent = bFlowAlongLocalX
        ? Geometry.EnvelopeHalfExtent.X : Geometry.EnvelopeHalfExtent.Y;
    FVector LocalInput = LocalGroundCentre - LocalAxis * AxisHalfExtent;
    FVector LocalOutput = LocalGroundCentre + LocalAxis * AxisHalfExtent;
    LocalInput.Z = 0.0f;
    LocalOutput.Z = 0.0f;
    Geometry.InputSocket = PreviewTransform.TransformPosition(LocalInput);
    Geometry.OutputSocket = PreviewTransform.TransformPosition(LocalOutput);
    Geometry.bShowProcessFlow = bShowProcessFlow;
    return Geometry;
}

FLBPlacementPreviewGeometry ALBManagementPawn::BuildMachinePlacementPreviewGeometry(
    const ELBFactoryBuildMachineType MachineType, const FTransform& PreviewTransform,
    const FVector& EnvelopeRelativeCentre, const FVector& EnvelopeHalfExtent, const float FloorZ)
{
    FLBPlacementPreviewGeometry Geometry = BuildPlacementPreviewGeometry(PreviewTransform,
        EnvelopeRelativeCentre, EnvelopeHalfExtent, FloorZ,
        MachineType == ELBFactoryBuildMachineType::ECoatLine
            || MachineType == ELBFactoryBuildMachineType::BodyWeldLine, true);
    if (MachineType == ELBFactoryBuildMachineType::PressTrain)
    {
        if (const ALBPressTrainAStation* Defaults = GetDefault<ALBPressTrainAStation>())
        {
            if (Defaults->FactoryInputPort && Defaults->FactoryOutputPort)
            {
                Geometry.InputSocket = PreviewTransform.TransformPosition(
                    Defaults->FactoryInputPort->GetRelativeLocation());
                Geometry.OutputSocket = PreviewTransform.TransformPosition(
                    Defaults->FactoryOutputPort->GetRelativeLocation());
            }
        }
    }
    else if (MachineType == ELBFactoryBuildMachineType::BodyWeldLine)
    {
        if (const ALBBodyWeldLineActor* Defaults = GetDefault<ALBBodyWeldLineActor>())
        {
            if (Defaults->GetStillageInputPort() && Defaults->GetBIWOutputPort())
            {
                Geometry.InputSocket = PreviewTransform.TransformPosition(
                    Defaults->GetStillageInputPort()->GetRelativeLocation());
                Geometry.OutputSocket = PreviewTransform.TransformPosition(
                    Defaults->GetBIWOutputPort()->GetRelativeLocation());
            }
        }
    }
    else if (MachineType == ELBFactoryBuildMachineType::ECoatLine)
    {
        if (const ALBECoatLineActor* Defaults = GetDefault<ALBECoatLineActor>())
        {
            if (Defaults->GetInputPort() && Defaults->GetOutputPort())
            {
                Geometry.InputSocket = PreviewTransform.TransformPosition(
                    Defaults->GetInputPort()->GetRelativeLocation());
                Geometry.OutputSocket = PreviewTransform.TransformPosition(
                    Defaults->GetOutputPort()->GetRelativeLocation());
            }
        }
    }
    return Geometry;
}

FString ALBManagementPawn::FormatNamedObstructionReason(const FString& EnvelopeLabel,
    const FString& ActorLabel, const FString& ComponentLabel)
{
    const FString SafeEnvelope = EnvelopeLabel.TrimStartAndEnd().IsEmpty()
        ? TEXT("PLACEMENT ENVELOPE") : EnvelopeLabel.TrimStartAndEnd().ToUpper();
    const FString SafeActor = ActorLabel.TrimStartAndEnd();
    const FString SafeComponent = ComponentLabel.TrimStartAndEnd();
    if (!SafeActor.IsEmpty() && !SafeComponent.IsEmpty())
    {
        return FString::Printf(TEXT("%s IS OBSTRUCTED BY %s (%s); MOVE OR ROTATE TO CLEAR IT"),
            *SafeEnvelope, *SafeActor, *SafeComponent);
    }
    if (!SafeActor.IsEmpty())
    {
        return FString::Printf(TEXT("%s IS OBSTRUCTED BY %s; MOVE OR ROTATE TO CLEAR IT"),
            *SafeEnvelope, *SafeActor);
    }
    return FString::Printf(TEXT("%s IS OBSTRUCTED; MOVE OR ROTATE TO CLEAR IT"), *SafeEnvelope);
}

FLBPlacementCardData ALBManagementPawn::BuildPlacementCardData(const FString& ItemTitle,
    const FLBPlacementPreviewStyle& Style, const FString& ObstructionDisplayName,
    const FString& ObstructionStableId)
{
    FLBPlacementCardData Card;
    Card.bVisible = true;
    Card.bCanConfirm = Style.IsPlacementAllowed();
    Card.Title = ItemTitle.TrimStartAndEnd().IsEmpty() ? TEXT("PLACE FACTORY ITEM")
        : ItemTitle.TrimStartAndEnd().ToUpper();
    Card.State = Style.StateMarker;
    Card.AccentColour = FLinearColor::FromSRGBColor(Style.FootprintColour);
    Card.AccentColour.A = 1.0f;
    Card.ObstructionDisplayName = FriendlyActorName(ObstructionDisplayName);
    Card.ObstructionStableId = ObstructionStableId.TrimStartAndEnd();
    Card.Cause = Style.AuthorityReason.TrimStartAndEnd();
    Card.CorrectiveAction = Style.NextAction.TrimStartAndEnd();
    // Do not duplicate a two-line authority reason in both card sections.
    if (!Card.Cause.IsEmpty() && Card.CorrectiveAction.StartsWith(Card.Cause))
    {
        Card.CorrectiveAction.RightChopInline(Card.Cause.Len());
        Card.CorrectiveAction.TrimStartAndEndInline();
    }
    if (!Card.ObstructionDisplayName.IsEmpty())
    {
        const FString IdentitySuffix = Card.ObstructionStableId.IsEmpty()
            ? FString() : FString::Printf(TEXT("  [%s]"), *Card.ObstructionStableId);
        Card.Cause = FString::Printf(TEXT("BLOCKED BY %s%s"),
            *Card.ObstructionDisplayName, *IdentitySuffix);
    }
    Card.Controls = TEXT("CONFIRM: CLICK / ENTER / A    ROTATE: R / RB    CANCEL: ESC / B");
    return Card;
}

FLBPlacementCardLayout ALBManagementPawn::BuildPlacementCardLayout(
    const FIntPoint& Viewport, const float GhostScreenX,
    const bool bForceCardSide, const bool bForcedCardOnLeft)
{
    FLBPlacementCardLayout Layout;
    const float Width = FMath::Max(1.0f, static_cast<float>(Viewport.X));
    const float Height = FMath::Max(1.0f, static_cast<float>(Viewport.Y));
    Layout.UIScale = FMath::Clamp(FMath::Min(Width / 1280.0f, Height / 720.0f), 1.0f, 1.5f);
    Layout.SafeMargin = FMath::Max(18.0f * Layout.UIScale, Width * 0.025f);
    Layout.Size.X = FMath::Clamp(390.0f * Layout.UIScale,
        Width * 0.29f, Width * 0.36f);
    Layout.Size.Y = FMath::Clamp(286.0f * Layout.UIScale,
        Height * 0.36f, Height - Layout.SafeMargin * 2.0f);
    Layout.bCardOnLeft = bForceCardSide ? bForcedCardOnLeft : GhostScreenX >= Width * 0.54f;
    Layout.Position.X = Layout.bCardOnLeft ? Layout.SafeMargin
        : Width - Layout.SafeMargin - Layout.Size.X;
    Layout.Position.Y = FMath::Clamp(Height * 0.17f,
        Layout.SafeMargin, Height - Layout.SafeMargin - Layout.Size.Y);
    Layout.ContentWidth = FMath::Max(120.0f, Layout.Size.X - 40.0f * Layout.UIScale);
    Layout.MaximumCharactersPerLine = FMath::Clamp(
        FMath::FloorToInt(Layout.ContentWidth / (7.2f * Layout.UIScale)), 34, 66);
    return Layout;
}

TArray<FString> ALBManagementPawn::WrapPlacementCardText(const FString& Text,
    const int32 MaximumCharactersPerLine, const int32 MaximumLines)
{
    TArray<FString> Result;
    if (MaximumCharactersPerLine <= 0 || MaximumLines <= 0) return Result;
    FString Normalised = Text.TrimStartAndEnd();
    Normalised.ReplaceInline(TEXT("\n"), TEXT(" "));
    TArray<FString> Words;
    Normalised.ParseIntoArrayWS(Words);
    FString Current;
    for (const FString& Word : Words)
    {
        if (Current.IsEmpty()) Current = Word;
        else if (Current.Len() + 1 + Word.Len() <= MaximumCharactersPerLine)
            Current += TEXT(" ") + Word;
        else
        {
            Result.Add(Current);
            Current = Word;
            if (Result.Num() >= MaximumLines) break;
        }
    }
    if (Result.Num() < MaximumLines && !Current.IsEmpty()) Result.Add(Current);
    if (Result.Num() == MaximumLines)
    {
        const FString Joined = FString::Join(Result, TEXT(" "));
        if (Joined.Len() < Normalised.Len())
        {
            FString& Last = Result.Last();
            Last = Last.Left(FMath::Max(1, MaximumCharactersPerLine - 3)).TrimEnd() + TEXT("...");
        }
    }
    return Result;
}

FLBPlacementFramingContract ALBManagementPawn::BuildPlacementFramingContract(
    const FLBPlacementPreviewGeometry& Geometry, const FIntPoint& Viewport,
    const FLBPlacementCardLayout& CardLayout)
{
    FLBPlacementFramingContract Result;
    Result.bCardOnLeft = CardLayout.bCardOnLeft;
    const float Diameter = FMath::Max(Geometry.GroundHalfExtent.X,
        Geometry.GroundHalfExtent.Y) * 2.0f;
    const float ReservedFraction = FMath::Clamp(
        CardLayout.Size.X / FMath::Max(1.0f, static_cast<float>(Viewport.X)), 0.0f, 0.48f);
    Result.RequiredZoomDistanceCm = FMath::Clamp(
        Diameter * (1.28f + ReservedFraction * 0.75f) + 900.0f,
        GetMinimumPlacementZoomDistance(), GetMaximumManagementZoomDistance());
    const float LateralMagnitude = FMath::Clamp(Diameter * 0.18f + 280.0f,
        350.0f, 3200.0f);
    Result.CameraLateralOffsetCm = CardLayout.bCardOnLeft ? LateralMagnitude : -LateralMagnitude;
    return Result;
}

FString ALBManagementPawn::GetMachinePlacementDisplayName(const ELBFactoryBuildMachineType MachineType)
{
    switch (MachineType)
    {
    case ELBFactoryBuildMachineType::InboundDeliveryDock: return TEXT("Inbound delivery dock");
    case ELBFactoryBuildMachineType::DepackagingRobot: return TEXT("Coil depackaging cell");
    case ELBFactoryBuildMachineType::DecoilerFeeder: return TEXT("Coil preparation line");
    case ELBFactoryBuildMachineType::PressTrain: return TEXT("Seven-stage press train");
    case ELBFactoryBuildMachineType::InspectionCell: return TEXT("Panel inspection cell");
    case ELBFactoryBuildMachineType::OutboundPanelDock: return TEXT("Outbound panel dock");
    case ELBFactoryBuildMachineType::CoilWeighInspectionCell: return TEXT("PR002 coil inspection cell");
    case ELBFactoryBuildMachineType::ECoatLine: return TEXT("ED and e-coat line");
    case ELBFactoryBuildMachineType::BodyWeldLine: return TEXT("Body weld line");
    default: return TEXT("Factory machine");
    }
}

FString ALBManagementPawn::GetStoragePlacementDisplayName(const ELBPressShopStorageType StorageType)
{
    switch (StorageType)
    {
    case ELBPressShopStorageType::BareCoils: return TEXT("Bare coil storage");
    case ELBPressShopStorageType::PreparedBlanks: return TEXT("Prepared blank buffer");
    case ELBPressShopStorageType::FinishedPanelStillages: return TEXT("Full panel stillage storage");
    case ELBPressShopStorageType::EmptyPanelStillages: return TEXT("Empty panel stillage storage");
    case ELBPressShopStorageType::Scrap: return TEXT("Scrap storage");
    case ELBPressShopStorageType::MaintenanceParts: return TEXT("Maintenance parts store");
    case ELBPressShopStorageType::Quarantine: return TEXT("Quarantine area");
    default: return TEXT("Storage area");
    }
}

FString ALBManagementPawn::GetInfrastructurePlacementDisplayName(
    const ELBFactoryAGVInfrastructureType Type)
{
    switch (Type)
    {
    case ELBFactoryAGVInfrastructureType::ChargingStation: return TEXT("AGV charging station");
    case ELBFactoryAGVInfrastructureType::WaitPoint: return TEXT("AGV wait point");
    case ELBFactoryAGVInfrastructureType::RouteWaypoint: return TEXT("AGV route waypoint");
    case ELBFactoryAGVInfrastructureType::PressTrainHandoff: return TEXT("Press-train handoff");
    case ELBFactoryAGVInfrastructureType::AGVRouteSegment: return TEXT("AGV route segment");
    case ELBFactoryAGVInfrastructureType::PedestrianWalkway: return TEXT("Pedestrian walkway");
    case ELBFactoryAGVInfrastructureType::PedestrianCrossing: return TEXT("Pedestrian crossing");
    case ELBFactoryAGVInfrastructureType::SafetyFence: return TEXT("Safety fence");
    default: return TEXT("Factory infrastructure");
    }
}

int32 ALBManagementPawn::GetPlacementGhostMeshCount() const
{
    if (!IsValid(PlacementGhostActor)) return 0;
    TInlineComponentArray<UStaticMeshComponent*> Components;
    PlacementGhostActor->GetComponents(Components, true);
    int32 VisibleMeshCount = 0;
    for (const UStaticMeshComponent* Component : Components)
    {
        VisibleMeshCount += Component && Component->GetStaticMesh()
            && Component->IsVisible() ? 1 : 0;
    }
    return VisibleMeshCount;
}

void ALBManagementPawn::DestroyPlacementGhost()
{
    PlacementGhostMaterials.Reset();
    PlacementGhostMaterialRoles.Reset();
    if (IsValid(PlacementGhostActor)) PlacementGhostActor->Destroy();
    PlacementGhostActor = nullptr;
}

bool ALBManagementPawn::BuildPlacementGhostFromActor(AActor* SourceActor)
{
    DestroyPlacementGhost();
    UWorld* World = GetWorld();
    if (!World || !IsValid(SourceActor)) return false;

    AActor* Ghost = World->SpawnActorDeferred<AActor>(AActor::StaticClass(), FTransform::Identity,
        this, nullptr, ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
    if (!Ghost) return false;
    USceneComponent* Root = NewObject<USceneComponent>(Ghost, TEXT("PlacementGhostRoot"));
    Ghost->SetRootComponent(Root);
    Ghost->AddInstanceComponent(Root);
    Root->RegisterComponent();
    Ghost->FinishSpawning(FTransform::Identity);
    Ghost->Tags = { TEXT("LB.PlacementGhost") };

    TInlineComponentArray<UStaticMeshComponent*> SourceMeshes;
    SourceActor->GetComponents(SourceMeshes, true);
    for (UStaticMeshComponent* Source : SourceMeshes)
    {
        if (!IsValid(Source) || !Source->GetStaticMesh() || !Source->ShouldRender()
            || Source->ComponentHasTag(TEXT("LB.NoPlacementPreview"))) continue;
        UStaticMeshComponent* Copy = nullptr;
        if (const UInstancedStaticMeshComponent* SourceInstances =
            Cast<UInstancedStaticMeshComponent>(Source))
        {
            UHierarchicalInstancedStaticMeshComponent* InstanceCopy =
                NewObject<UHierarchicalInstancedStaticMeshComponent>(Ghost,
                    MakeUniqueObjectName(Ghost,
                        UHierarchicalInstancedStaticMeshComponent::StaticClass(),
                        FName(*FString::Printf(TEXT("Ghost_%s"), *Source->GetName()))));
            for (int32 InstanceIndex = 0;
                InstanceIndex < SourceInstances->GetInstanceCount(); ++InstanceIndex)
            {
                FTransform InstanceTransform;
                if (SourceInstances->GetInstanceTransform(InstanceIndex, InstanceTransform, false))
                    InstanceCopy->AddInstance(InstanceTransform);
            }
            Copy = InstanceCopy;
        }
        else
        {
            Copy = NewObject<UStaticMeshComponent>(Ghost,
                MakeUniqueObjectName(Ghost, UStaticMeshComponent::StaticClass(),
                    FName(*FString::Printf(TEXT("Ghost_%s"), *Source->GetName()))));
        }
        Copy->SetupAttachment(Root);
        Copy->SetStaticMesh(Source->GetStaticMesh());
        Copy->SetRelativeTransform(Source->GetComponentTransform().GetRelativeTransform(
            SourceActor->GetActorTransform()));
        Copy->SetVisibility(true, true);
        Copy->SetHiddenInGame(false, true);
        SetGhostPrimitiveFlags(Copy);
        const int32 MaterialCount = FMath::Max(1, Source->GetNumMaterials());
        for (int32 Slot = 0; Slot < MaterialCount; ++Slot)
        {
            UMaterialInterface* Parent = PlacementGhostMaterialParent
                ? PlacementGhostMaterialParent.Get() : Source->GetMaterial(Slot);
            UMaterialInstanceDynamic* MID = Parent
                ? UMaterialInstanceDynamic::Create(Parent, Ghost) : nullptr;
            if (MID)
            {
                Copy->SetMaterial(Slot, MID);
                PlacementGhostMaterials.Add(MID);
                const FString MaterialName = Source->GetMaterial(Slot)
                    ? Source->GetMaterial(Slot)->GetName().ToUpper() : FString();
                PlacementGhostMaterialRoles.Add(MaterialName.Contains(TEXT("CHARCOAL"))
                    || MaterialName.Contains(TEXT("FRAME")) ? 1 : 0);
            }
        }
        Ghost->AddInstanceComponent(Copy);
        Copy->RegisterComponent();
    }
    SourceActor->Destroy();
    PlacementGhostActor = Ghost;
    if (Ghost->GetComponentsBoundingBox(true).IsValid && GetPlacementGhostMeshCount() > 0)
        return true;
    PlacementGhostActor = nullptr;
    Ghost->Destroy();
    return false;
}

bool ALBManagementPawn::BuildMachinePlacementGhost(const ELBFactoryBuildMachineType MachineType)
{
    UWorld* World = GetWorld();
    if (!World) return false;
    AActor* Source = nullptr;
    if (MachineType == ELBFactoryBuildMachineType::PressTrain)
    {
        ALBPressTrainAStation* Train = World->SpawnActor<ALBPressTrainAStation>();
        if (Train)
        {
            Train->ConfigureTrainVariant(TEXT("TRAIN_A"), TEXT("TRAIN A"), TEXT("PLACEMENT PREVIEW"),
                FLinearColor(0.2f, 0.8f, 0.45f));
            Train->EnableCompletedRuntimeVisual();
        }
        Source = Train;
    }
    else if (MachineType == ELBFactoryBuildMachineType::BodyWeldLine)
    {
        ALBBodyWeldLineActor* Line = World->SpawnActor<ALBBodyWeldLineActor>();
        if (Line) Line->Configure(TEXT("WELD-LINE-PREVIEW"));
        Source = Line;
    }
    else if (MachineType == ELBFactoryBuildMachineType::ECoatLine)
    {
        ALBECoatLineActor* Line = World->SpawnActor<ALBECoatLineActor>();
        if (Line) Line->Configure(TEXT("ED-LINE-PREVIEW"));
        Source = Line;
    }
    else
    {
        ALBFactoryBuildMachine* Machine = World->SpawnActor<ALBFactoryBuildMachine>();
        if (Machine) Machine->Configure(TEXT("MACHINE-PREVIEW"), MachineType);
        Source = Machine;
    }
    return BuildPlacementGhostFromActor(Source);
}

bool ALBManagementPawn::BuildStoragePlacementGhost()
{
    UWorld* World = GetWorld();
    if (!World) return false;
    ALBPressShopStorageZone* Zone = World->SpawnActor<ALBPressShopStorageZone>();
    if (!Zone) return false;
    const FVector PreviewExtent(FMath::Max(100.0f, StoragePreviewHalfExtent.X),
        FMath::Max(100.0f, StoragePreviewHalfExtent.Y), FMath::Max(50.0f, StoragePreviewHalfExtent.Z));
    if (!Zone->Configure(TEXT("STORAGE-PREVIEW"), SelectedStorageType,
        FMath::Max(1, StoragePreviewCapacity), PreviewExtent))
    {
        Zone->Destroy();
        return false;
    }
    Zone->ConfigureLayout(FMath::Max(1, StoragePreviewColumns), FMath::Max(1, StoragePreviewRows),
        FVector2D(220.0f, 180.0f), 40.0f);
    return BuildPlacementGhostFromActor(Zone);
}

bool ALBManagementPawn::BuildInfrastructurePlacementGhost(
    const ELBFactoryAGVInfrastructureType Type, const int32 TrainIndex,
    const AActor* ExistingSource)
{
    UWorld* World = GetWorld();
    if (!World) return false;
    ALBFactoryAGVInfrastructure* Source = ExistingSource
        ? World->SpawnActor<ALBFactoryAGVInfrastructure>(
            ALBFactoryAGVInfrastructure::StaticClass(), ExistingSource->GetActorTransform())
        : World->SpawnActor<ALBFactoryAGVInfrastructure>();
    if (!Source || !Source->Configure(TEXT("INFRASTRUCTURE-PREVIEW"), Type, TrainIndex))
    {
        if (Source) Source->Destroy();
        return false;
    }
    return BuildPlacementGhostFromActor(Source);
}

void ALBManagementPawn::UpdatePlacementGhostTransform(const FTransform& Transform,
    const FLBPlacementPreviewStyle& Style)
{
    if (!IsValid(PlacementGhostActor)) return;
    PlacementGhostActor->SetActorTransform(Transform, false, nullptr, ETeleportType::TeleportPhysics);
    FLBFactoryMachineLivery Livery;
    if (const UWorld* World = GetWorld())
        if (const ULBFactoryBrandSubsystem* Brand = World->GetSubsystem<ULBFactoryBrandSubsystem>())
            Livery = Brand->GetMachineLivery();
    const FLinearColor StateTint = Style.State == ELBPlacementPreviewState::Blocked
        ? FLinearColor::FromSRGBColor(FColor(255, 55, 45))
        : (Style.State == ELBPlacementPreviewState::WaitingForSurface
            ? FLinearColor::FromSRGBColor(FColor(255, 190, 40)) : FLinearColor::White);
    for (int32 Index = 0; Index < PlacementGhostMaterials.Num(); ++Index)
    {
        UMaterialInstanceDynamic* MID = PlacementGhostMaterials[Index];
        if (!MID) continue;
        const bool bSecondary = PlacementGhostMaterialRoles.IsValidIndex(Index)
            && PlacementGhostMaterialRoles[Index] == 1;
        FLinearColor Colour = bSecondary ? Livery.SecondaryColour : Livery.PrimaryColour;
        Colour = FLinearColor::LerpUsingHSV(Colour, StateTint,
            Style.State == ELBPlacementPreviewState::Ready ? 0.08f : 0.62f);
        Colour.A = Style.State == ELBPlacementPreviewState::Blocked ? 0.34f : 0.48f;
        for (const FName Parameter : {FName(TEXT("Color")), FName(TEXT("BaseColor")),
            FName(TEXT("LiveryTint")), FName(TEXT("BaseColorTint"))})
            MID->SetVectorParameterValue(Parameter, Colour);
        for (const FName Parameter : {FName(TEXT("Opacity")), FName(TEXT("Alpha"))})
            MID->SetScalarParameterValue(Parameter, Colour.A);
    }
}

void ALBManagementPawn::ResetPlacementPresentation()
{
    PlacementCardData = FLBPlacementCardData();
    CurrentPlacementGeometry = FLBPlacementPreviewGeometry();
    CurrentPlacementObstructionDisplayName.Reset();
    CurrentPlacementObstructionStableId.Reset();
    bPlacementFramingSideLocked = false;
    DestroyPlacementGhost();
}

FString ALBManagementPawn::ResolveCurrentPlacementTitle() const
{
    if (bPressTrainPlacementActive) return GetMachinePlacementDisplayName(SelectedMachineType);
    if (bStoragePlacementActive) return GetStoragePlacementDisplayName(SelectedStorageType);
    if (bInfrastructurePlacementActive) return GetInfrastructurePlacementDisplayName(SelectedInfrastructureType);
    if (bInfrastructureEditActive && IsValid(InspectedInfrastructure))
        return FString::Printf(TEXT("Move %s"),
            *GetInfrastructurePlacementDisplayName(InspectedInfrastructure->GetInfrastructureType()));
    return TEXT("Place factory item");
}

void ALBManagementPawn::UpdatePlacementPresentation(const FString& ItemTitle,
    const FLBPlacementPreviewGeometry& Geometry, const FLBPlacementPreviewStyle& Style)
{
    CurrentPlacementGeometry = Geometry;
    PlacementCardData = BuildPlacementCardData(ItemTitle, Style,
        CurrentPlacementObstructionDisplayName, CurrentPlacementObstructionStableId);
    UpdatePlacementGhostTransform(bPressTrainPlacementActive ? PressTrainPreviewTransform
        : (bStoragePlacementActive ? StoragePreviewTransform
            : (bInfrastructurePlacementActive ? InfrastructurePreviewTransform
                : InfrastructureEditPreviewTransform)), Style);
    UpdatePlacementFraming(Geometry);
}

void ALBManagementPawn::UpdatePlacementFraming(const FLBPlacementPreviewGeometry& Geometry)
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    if (!PC || !CameraBoom) return;
    int32 ViewX = 0;
    int32 ViewY = 0;
    PC->GetViewportSize(ViewX, ViewY);
    FVector2D GhostScreen(ViewX * 0.5f, ViewY * 0.5f);
    PC->ProjectWorldLocationToScreen(Geometry.EnvelopeCentre, GhostScreen, true);
    FLBPlacementCardLayout Card = BuildPlacementCardLayout(FIntPoint(ViewX, ViewY), GhostScreen.X,
        bPlacementFramingSideLocked, bPlacementCardOnLeft);
    if (!bPlacementFramingSideLocked)
    {
        bPlacementCardOnLeft = Card.bCardOnLeft;
        bPlacementFramingSideLocked = true;
    }
    const FLBPlacementFramingContract Framing = BuildPlacementFramingContract(
        Geometry, FIntPoint(ViewX, ViewY), Card);
    DesiredZoomDistance = FMath::Max(DesiredZoomDistance, Framing.RequiredZoomDistanceCm);
    const FVector Right = FRotationMatrix(FRotator(0.0f, GetActorRotation().Yaw, 0.0f))
        .GetUnitAxis(EAxis::Y);
    const FVector DesiredPivot = Geometry.EnvelopeCentre + Right * Framing.CameraLateralOffsetCm;
    const float FollowAlpha = 0.14f;
    SetActorLocation(FMath::Lerp(GetActorLocation(), DesiredPivot, FollowAlpha), false, nullptr,
        ETeleportType::None);
}

void ALBManagementPawn::DrawPlacementCard(UCanvas* Canvas) const
{
    if (!Canvas || !PlacementCardData.bVisible || !GEngine) return;
    APlayerController* PC = Cast<APlayerController>(GetController());
    FVector2D GhostScreen(Canvas->SizeX * 0.5f, Canvas->SizeY * 0.5f);
    if (PC && CurrentPlacementGeometry.EnvelopeHalfExtent.GetMax() > 0.0f)
        PC->ProjectWorldLocationToScreen(CurrentPlacementGeometry.EnvelopeCentre, GhostScreen, true);
    const FLBPlacementCardLayout Layout = BuildPlacementCardLayout(
        FIntPoint(Canvas->SizeX, Canvas->SizeY), GhostScreen.X,
        bPlacementFramingSideLocked, bPlacementCardOnLeft);
    const FLinearColor Panel(0.012f, 0.025f, 0.032f, 0.94f);
    Canvas->K2_DrawBox(Layout.Position, Layout.Size, 1.0f, Panel);
    Canvas->K2_DrawBox(Layout.Position, FVector2D(7.0f * Layout.UIScale, Layout.Size.Y),
        1.0f, PlacementCardData.AccentColour);
    const float Pad = 20.0f * Layout.UIScale;
    float Y = Layout.Position.Y + 15.0f * Layout.UIScale;
    const float X = Layout.Position.X + Pad;
    UFont* LargeFont = GEngine->GetLargeFont();
    UFont* SmallFont = GEngine->GetSmallFont();
    Canvas->K2_DrawText(LargeFont, PlacementCardData.Title, FVector2D(X, Y),
        FVector2D(Layout.UIScale), FLinearColor::White, 1.0f, FLinearColor::Black,
        FVector2D(1.0f), false, false, false, PlacementCardData.AccentColour);
    Y += 35.0f * Layout.UIScale;
    Canvas->K2_DrawText(SmallFont, PlacementCardData.State, FVector2D(X, Y),
        FVector2D(1.15f * Layout.UIScale), FLinearColor::White, 1.0f, FLinearColor::Black,
        FVector2D(1.0f), false, false, false, PlacementCardData.AccentColour);
    Y += 28.0f * Layout.UIScale;
    const auto DrawWrapped = [Canvas, SmallFont, &Layout, X, &Y](const FString& Label,
        const FString& Value, const FLinearColor& Colour, const int32 MaxLines)
    {
        if (Value.IsEmpty()) return;
        if (!Label.IsEmpty())
        {
            Canvas->K2_DrawText(SmallFont, Label, FVector2D(X, Y),
                FVector2D(Layout.UIScale), FLinearColor::White, 1.0f, FLinearColor::Black,
                FVector2D(1.0f), false, false, false, FLinearColor(0.55f, 0.72f, 0.75f));
            Y += 17.0f * Layout.UIScale;
        }
        for (const FString& Line : WrapPlacementCardText(Value,
            Layout.MaximumCharactersPerLine, MaxLines))
        {
            Canvas->K2_DrawText(SmallFont, Line, FVector2D(X, Y),
                FVector2D(Layout.UIScale), FLinearColor::White, 1.0f, FLinearColor::Black,
                FVector2D(1.0f), false, false, false, Colour);
            Y += 17.0f * Layout.UIScale;
        }
        Y += 5.0f * Layout.UIScale;
    };
    DrawWrapped(TEXT("CAUSE"), PlacementCardData.Cause, FLinearColor::White, 3);
    DrawWrapped(TEXT("NEXT"), PlacementCardData.CorrectiveAction,
        PlacementCardData.AccentColour, 2);
    const float ControlsY = Layout.Position.Y + Layout.Size.Y - 33.0f * Layout.UIScale;
    Canvas->K2_DrawText(SmallFont, PlacementCardData.Controls,
        FVector2D(X, ControlsY), FVector2D(0.88f * Layout.UIScale), FLinearColor::White,
        1.0f, FLinearColor::Black, FVector2D(1.0f), false, false, false,
        FLinearColor(0.74f, 0.82f, 0.84f));
}

#if WITH_DEV_AUTOMATION_TESTS
bool ALBManagementPawn::BuildPlacementGhostForAutomation(AActor* SourceActor)
{
    return BuildPlacementGhostFromActor(SourceActor);
}
#endif

ALBManagementPawn::ALBManagementPawn()
{
    PrimaryActorTick.bCanEverTick = true;
    Pivot = CreateDefaultSubobject<USceneComponent>(TEXT("ManagementPivot"));
    SetRootComponent(Pivot);

    CameraBoom = CreateDefaultSubobject<USpringArmComponent>(TEXT("CameraBoom"));
    CameraBoom->SetupAttachment(Pivot);
    CameraBoom->TargetArmLength = 11000.0f;
    // Elevated three-quarter factory view: enough plan visibility for placement while
    // retaining the height, silhouettes and motion readability of Car Manufacture.
    CameraBoom->SetRelativeRotation(FRotator(-35.0f, 0.0f, 0.0f));
    CameraBoom->bDoCollisionTest = false;

    Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("ManagementCamera"));
    Camera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
    Camera->FieldOfView = 48.0f;

    WidgetInteraction = CreateDefaultSubobject<UWidgetInteractionComponent>(TEXT("ManagementWidgetInteraction"));
    WidgetInteraction->SetupAttachment(Camera);
    WidgetInteraction->InteractionSource = EWidgetInteractionSource::Mouse;
    WidgetInteraction->InteractionDistance = 20000.0f;

    static ConstructorHelpers::FObjectFinder<UMaterialInterface> GhostMaterial(
        TEXT("/Engine/EngineDebugMaterials/M_SimpleUnlitTranslucent.M_SimpleUnlitTranslucent"));
    if (GhostMaterial.Succeeded()) PlacementGhostMaterialParent = GhostMaterial.Object;

    AutoPossessPlayer = EAutoReceiveInput::Player0;
    SetActorLocation(FVector::ZeroVector);
    SetActorRotation(FRotator(0.0f, -45.0f, 0.0f));
}

void ALBManagementPawn::BeginPlay()
{
    Super::BeginPlay();
    if (Camera && GetWorld())
    {
        const FVector Start = Camera->GetComponentLocation();
        const FVector End = Start + Camera->GetForwardVector() * 50000.0f;
        FHitResult Hit;
        FCollisionQueryParams Params(SCENE_QUERY_STAT(LineBossInitialBuilderView), true, this);
        const bool bHit = GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params);
        UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_INITIAL_BUILDER_VIEW camera=%s rotation=%s hit=%s distance=%.1f"),
            *Start.ToCompactString(), *Camera->GetComponentRotation().ToCompactString(),
            bHit && Hit.GetActor() ? *Hit.GetActor()->GetActorNameOrLabel() : TEXT("NONE"),
            bHit ? Hit.Distance : -1.0f);
    }
    if (APlayerController* PlayerController = Cast<APlayerController>(GetController()))
    {
        PlayerController->bShowMouseCursor = true;
        PlayerController->bEnableClickEvents = true;
        PlayerController->bEnableMouseOverEvents = true;
        FInputModeGameAndUI InputMode;
        InputMode.SetHideCursorDuringCapture(false);
        PlayerController->SetInputMode(InputMode);

        bool bHasLegacyOperationsConsole = false;
        for (TActorIterator<ALBControlRoomOperationsConsole> It(GetWorld()); It; ++It)
        {
            bHasLegacyOperationsConsole = IsValid(*It);
            if (bHasLegacyOperationsConsole) break;
        }
        if (!bHasLegacyOperationsConsole)
        {
            if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PlayerController->GetHUD()))
            {
                if (HUD->ShouldAutoOpenBuildCatalogue()) HUD->OpenFactoryBuild();
            }
        }
        if (AHUD* HUD = PlayerController->GetHUD()) HUD->AddPostRenderedActor(this);
    }
}

void ALBManagementPawn::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    if (const APlayerController* PlayerController = Cast<APlayerController>(GetController()))
        if (AHUD* HUD = PlayerController->GetHUD()) HUD->RemovePostRenderedActor(this);
    DestroyPlacementGhost();
    RestoreFactorySelectionHighlight();
    InspectedFactoryActor.Reset();
    if (IsValid(InspectedInfrastructure))
    {
        InspectedInfrastructure->SetSelectionHighlighted(false);
        InspectedInfrastructure = nullptr;
    }
    Super::EndPlay(EndPlayReason);
}

void ALBManagementPawn::PostRenderFor(APlayerController* PC, UCanvas* Canvas,
    FVector CameraPosition, FVector CameraDir)
{
    Super::PostRenderFor(PC, Canvas, CameraPosition, CameraDir);
    DrawPlacementCard(Canvas);
}

void ALBManagementPawn::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);
    // Pawn BeginPlay can precede PlayerController/HUD creation in a packaged build. Keep this
    // one-shot bootstrap in Tick so the clean game always opens with a visible mouse catalogue.
    if (!bInitialBuilderHUDReady)
    {
        if (APlayerController* PC = Cast<APlayerController>(GetController()))
        {
            if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD()))
            {
                HUD->bShowHUD = true;
                HUD->AddPostRenderedActor(this);
                bool bHasLegacyConsole = false;
                for (TActorIterator<ALBControlRoomOperationsConsole> It(GetWorld()); It; ++It)
                    if (IsValid(*It)) { bHasLegacyConsole = true; break; }
                if (!bHasLegacyConsole && HUD->ShouldAutoOpenBuildCatalogue())
                    HUD->OpenFactoryBuild();
                bInitialBuilderHUDReady = true;
                UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_BUILDER_HUD_READY clean=%d visible=%d hud=%s"),
                    bHasLegacyConsole ? 0 : 1, HUD->bShowHUD ? 1 : 0, *HUD->GetClass()->GetName());
            }
        }
    }
    PollFactoryNameKeyboard();
    if (!FMath::IsNearlyZero(ZoomInput))
    {
        const float MinimumDistance = IsAnyPlacementActive()
            ? GetMinimumPlacementZoomDistance() : GetMinimumManagementZoomDistance();
        DesiredZoomDistance = FMath::Clamp(
            DesiredZoomDistance - ZoomInput * 900.0f,
            MinimumDistance,
            GetMaximumManagementZoomDistance());
        ZoomInput = 0.0f;
    }
    CameraBoom->TargetArmLength = FMath::FInterpTo(
        CameraBoom->TargetArmLength, DesiredZoomDistance, DeltaSeconds, 10.0f);
    if (!IsValid(InspectedFactoryActor.Get()) && !FactoryHighlightComponents.IsEmpty())
    {
        RestoreFactorySelectionHighlight();
        InspectedFactoryActor.Reset();
    }
    UpdateFactoryFocusTransition(DeltaSeconds);
    if (bPressTrainPlacementActive)
    {
        UpdatePressTrainPlacementPreview();
        return;
    }
    if (bStoragePlacementActive)
    {
        UpdateStoragePlacementPreview();
        return;
    }
    if (bInfrastructurePlacementActive)
    {
        UpdateInfrastructurePlacementPreview();
        return;
    }
    if (bInfrastructureEditActive)
    {
        UpdateInfrastructureEditPreview();
        return;
    }
    // No management gate here. This ran every frame, zeroed the movement inputs
    // and returned before the offset below was ever applied - so it silently
    // overrode the axis handlers and the camera stayed frozen. Since Tick opens
    // the build catalogue on this pawn at startup, the game booted immovable.
    // The target HUD is always-on, so panning with the UI up is the normal case.
    const FRotator YawOnly(0.0f, GetActorRotation().Yaw, 0.0f);
    const FVector Delta =
        (YawOnly.Vector() * ForwardInput + FRotationMatrix(YawOnly).GetUnitAxis(EAxis::Y) * RightInput)
        * 2600.0f * DeltaSeconds;
    AddActorWorldOffset(Delta, true);
    AddActorWorldRotation(FRotator(0.0f, RotateInput * 48.0f * DeltaSeconds, 0.0f));
}

void ALBManagementPawn::LBTestOpenBuilder()
{
#if !UE_BUILD_SHIPPING
    if (APlayerController* PC = Cast<APlayerController>(GetController()))
        if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->OpenFactoryBuild();
#endif
}

void ALBManagementPawn::PollFactoryNameKeyboard()
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    ALBControlRoomHUD* HUD = PC ? Cast<ALBControlRoomHUD>(PC->GetHUD()) : nullptr;
    if (!PC || !HUD || !HUD->IsBrandingNameEditActive())
    {
        BrandingKeysDown.Reset();
        return;
    }
    static const FKey Keys[] = {
        EKeys::A,EKeys::B,EKeys::C,EKeys::D,EKeys::E,EKeys::F,EKeys::G,EKeys::H,EKeys::I,EKeys::J,
        EKeys::K,EKeys::L,EKeys::M,EKeys::N,EKeys::O,EKeys::P,EKeys::Q,EKeys::R,EKeys::S,EKeys::T,
        EKeys::U,EKeys::V,EKeys::W,EKeys::X,EKeys::Y,EKeys::Z,
        EKeys::Zero,EKeys::One,EKeys::Two,EKeys::Three,EKeys::Four,EKeys::Five,EKeys::Six,EKeys::Seven,EKeys::Eight,EKeys::Nine,
        EKeys::SpaceBar,EKeys::Hyphen,EKeys::Period,EKeys::Apostrophe,EKeys::BackSpace,EKeys::Enter,EKeys::Escape};
    for (const FKey& Key : Keys)
    {
        const bool bDown = PC->IsInputKeyDown(Key);
        if (bDown && !BrandingKeysDown.Contains(Key)) HUD->HandleBrandingKey(Key);
        if (bDown) BrandingKeysDown.Add(Key);
        else BrandingKeysDown.Remove(Key);
    }
}

void ALBManagementPawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
    Super::SetupPlayerInputComponent(PlayerInputComponent);
    PlayerInputComponent->BindAxis(TEXT("LB_MoveForward"), this, &ALBManagementPawn::MoveForward);
    PlayerInputComponent->BindAxis(TEXT("LB_MoveRight"), this, &ALBManagementPawn::MoveRight);
    PlayerInputComponent->BindAxis(TEXT("LB_Rotate"), this, &ALBManagementPawn::Rotate);
    PlayerInputComponent->BindAxis(TEXT("LB_Zoom"), this, &ALBManagementPawn::Zoom);
    PlayerInputComponent->BindAction(TEXT("LB_CameraReset"), IE_Pressed, this, &ALBManagementPawn::ResetCamera);
    PlayerInputComponent->BindAction(TEXT("LB_PrimaryClick"), IE_Pressed, this, &ALBManagementPawn::InteractUnderCursor);
    PlayerInputComponent->BindAction(TEXT("LB_PrimaryClick"), IE_Released, this, &ALBManagementPawn::EndPointerInteraction);
    PlayerInputComponent->BindAction(TEXT("LB_Interact"), IE_Pressed, this, &ALBManagementPawn::InteractUnderCursor);
    PlayerInputComponent->BindAction(TEXT("LB_ToggleManagement"), IE_Pressed, this, &ALBManagementPawn::ToggleManagement);
    PlayerInputComponent->BindAction(TEXT("LB_ManagementNextPage"), IE_Pressed, this, &ALBManagementPawn::ManagementNextPage);
    PlayerInputComponent->BindAction(TEXT("LB_ManagementPreviousPage"), IE_Pressed, this, &ALBManagementPawn::ManagementPreviousPage);
    PlayerInputComponent->BindAction(TEXT("LB_ManagementNextAction"), IE_Pressed, this, &ALBManagementPawn::ManagementNextAction);
    PlayerInputComponent->BindAction(TEXT("LB_ManagementPreviousAction"), IE_Pressed, this, &ALBManagementPawn::ManagementPreviousAction);
    PlayerInputComponent->BindAction(TEXT("LB_ManagementConfirm"), IE_Pressed, this, &ALBManagementPawn::UseContextualConfirm);
    PlayerInputComponent->BindAction(TEXT("LB_BuildPressTrain"), IE_Pressed, this, &ALBManagementPawn::StartPressTrainPlacement);
    PlayerInputComponent->BindAction(TEXT("LB_PlacementCancel"), IE_Pressed, this, &ALBManagementPawn::CancelPressTrainPlacement);
    PlayerInputComponent->BindAction(TEXT("LB_PlacementRotate"), IE_Pressed, this, &ALBManagementPawn::RotatePressTrainPlacement);
    PlayerInputComponent->BindAction(TEXT("LB_ToggleSeat"), IE_Pressed, this, &ALBManagementPawn::UseContextualBuilderShortcut);

    // v2.1 camera bookmarks - direct key chords so no input-ini change is
    // needed: Shift+F5..F8 store the current framing, F5..F8 recall it.
    const FKey Keys[4] = { EKeys::F5, EKeys::F6, EKeys::F7, EKeys::F8 };
    typedef void (ALBManagementPawn::*FBookmarkHandler)();
    const FBookmarkHandler Stores[4] = {
        &ALBManagementPawn::StoreBookmark0, &ALBManagementPawn::StoreBookmark1,
        &ALBManagementPawn::StoreBookmark2, &ALBManagementPawn::StoreBookmark3 };
    const FBookmarkHandler Recalls[4] = {
        &ALBManagementPawn::RecallBookmark0, &ALBManagementPawn::RecallBookmark1,
        &ALBManagementPawn::RecallBookmark2, &ALBManagementPawn::RecallBookmark3 };
    for (int32 Index = 0; Index < 4; ++Index)
    {
        FInputKeyBinding StoreBinding(
            FInputChord(Keys[Index], true, false, false, false), IE_Pressed);
        StoreBinding.KeyDelegate.BindDelegate(this, Stores[Index]);
        PlayerInputComponent->KeyBindings.Add(StoreBinding);
        FInputKeyBinding RecallBinding(FInputChord(Keys[Index]), IE_Pressed);
        RecallBinding.KeyDelegate.BindDelegate(this, Recalls[Index]);
        PlayerInputComponent->KeyBindings.Add(RecallBinding);
    }
}

void ALBManagementPawn::StoreCameraBookmark(const int32 SlotIndex)
{
    if (SlotIndex < 0 || SlotIndex >= 4)
    {
        return;
    }
    FLBCameraBookmark& Bookmark = CameraBookmarks[SlotIndex];
    Bookmark.Location = GetActorLocation();
    Bookmark.YawDegrees = GetActorRotation().Yaw;
    Bookmark.ZoomDistanceCm = GetManagementZoomDistance();
    Bookmark.bSet = true;
}

void ALBManagementPawn::RecallCameraBookmark(const int32 SlotIndex)
{
    if (SlotIndex < 0 || SlotIndex >= 4 || !CameraBookmarks[SlotIndex].bSet)
    {
        return;
    }
    const FLBCameraBookmark& Bookmark = CameraBookmarks[SlotIndex];
    SetAutomationCamera(Bookmark.Location, Bookmark.YawDegrees,
        Bookmark.ZoomDistanceCm);
}

void ALBManagementPawn::StoreBookmark0() { StoreCameraBookmark(0); }
void ALBManagementPawn::StoreBookmark1() { StoreCameraBookmark(1); }
void ALBManagementPawn::StoreBookmark2() { StoreCameraBookmark(2); }
void ALBManagementPawn::StoreBookmark3() { StoreCameraBookmark(3); }
void ALBManagementPawn::RecallBookmark0() { RecallCameraBookmark(0); }
void ALBManagementPawn::RecallBookmark1() { RecallCameraBookmark(1); }
void ALBManagementPawn::RecallBookmark2() { RecallCameraBookmark(2); }
void ALBManagementPawn::RecallBookmark3() { RecallCameraBookmark(3); }

void ALBManagementPawn::UseContextualBuilderShortcut()
{
    if (IsValid(ReturnPawn))
    {
        ReturnToControlRoom();
        return;
    }

    if (APlayerController* PC = Cast<APlayerController>(GetController()))
    {
        if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD()))
        {
            if (HUD->IsManagementVisible()) HUD->ToggleManagement();
            else HUD->OpenFactoryBuild();
            return;
        }
    }
}

bool ALBManagementPawn::ReturnToControlRoom()
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    if (!PC || !IsValid(ReturnPawn)) return false;
    if (IsAnyPlacementActive()) CancelPressTrainPlacement();
    if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD()))
        if (HUD->IsManagementVisible()) HUD->ToggleManagement();
    ALBControlRoomPawn* Target = ReturnPawn.Get();
    ReturnPawn = nullptr;
    PC->Possess(Target);
    Destroy();
    return true;
}

void ALBManagementPawn::InteractUnderCursor()
{
    bUseScreenCentrePlacementCursor = false;
    if (bInfrastructureEditActive)
    {
        UpdateInfrastructureEditPreview();
        ConfirmInfrastructureEdit();
        return;
    }
    if (bPressTrainPlacementActive)
    {
        ConfirmPressTrainPlacement();
        return;
    }
    if (bStoragePlacementActive)
    {
        if (!bStorageDragActive)
        {
            bStorageDragActive = true;
            StorageDragAnchor = StoragePreviewTransform.GetLocation();
            StorageDragAnchor.Z -= StoragePreviewHalfExtent.Z;
            StoragePlacementReason = TEXT("DRAG TO SIZE THE STORAGE AREA; RELEASE TO BUILD");
        }
        return;
    }
    if (bInfrastructurePlacementActive)
    {
        ConfirmInfrastructurePlacement();
        return;
    }
    APlayerController* PlayerController = Cast<APlayerController>(GetController());
    float MouseX = 0.0f;
    float MouseY = 0.0f;
    const bool bHasMousePosition = PlayerController
        && PlayerController->GetMousePosition(MouseX, MouseY);
    if (bHasMousePosition)
    {
        if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PlayerController->GetHUD()))
        {
            // The persistent alert strip exists outside the full management panel. Give HUD
            // hit regions first refusal, but retain world selection whenever no HUD cell handled it.
            if (HUD->HandleManagementClick(MouseX, MouseY)) return;
        }
    }
    if (IsManagementOpen()) return;
    if (WidgetInteraction)
    {
        // Preserve direct world-widget input even when its surface is not the first ordinary
        // Visibility hit. Infrastructure selection below still owns the actor-level action.
        WidgetInteraction->PressPointerKey(EKeys::LeftMouseButton);
    }
    if (!PlayerController)
    {
        return;
    }

    FVector RayOrigin;
    FVector RayDirection;
    if (bHasMousePosition
        && PlayerController->DeprojectScreenPositionToWorld(
            MouseX, MouseY, RayOrigin, RayDirection)
        && SelectFactoryActorAlongViewRay(RayOrigin, RayDirection))
    {
        return;
    }

    FHitResult Hit;
    if (!PlayerController->GetHitResultUnderCursor(ECC_Visibility, false, Hit))
    {
        if (HasSelectedInfrastructure()) ClearInfrastructureSelection();
        if (IsValid(InspectedFactoryActor.Get())) ClearFactoryActorSelection();
        return;
    }

    if (HasSelectedInfrastructure()) ClearInfrastructureSelection();
    if (IsValid(InspectedFactoryActor.Get())) ClearFactoryActorSelection();

    InteractWithActor(Hit.GetActor());
}

bool ALBManagementPawn::InteractWithActor(AActor* TargetActor)
{
    if (ALBPR004Station* Station = Cast<ALBPR004Station>(TargetActor))
    {
        return Station->UnpackageCoil(TEXT("PLAYER_DIRECT_UNPACKAGE"));
    }
    return false;
}

void ALBManagementPawn::EndPointerInteraction()
{
    if (bStoragePlacementActive && bStorageDragActive)
    {
        bStorageDragActive = false;
        ConfirmStoragePlacement();
        return;
    }
    if (WidgetInteraction)
    {
        WidgetInteraction->ReleasePointerKey(EKeys::LeftMouseButton);
    }
}

// The camera must keep moving while the management HUD is visible. These axes
// used to zero themselves on IsManagementOpen(), and Tick opens the factory
// build catalogue on this pawn at startup "so the clean game always opens with a
// visible mouse catalogue" - so the game booted with every camera control dead
// and no indication why. The target HUD is always-on by design, which makes
// "UI visible" the normal state rather than a modal one. Text entry is still
// safe: Slate consumes keys while an editable text box holds keyboard focus, so
// these axis mappings do not fire while a name is being typed.
void ALBManagementPawn::MoveForward(float Value)
{
    ForwardInput = Value;
    if (!FMath::IsNearlyZero(ForwardInput)) bFactoryFocusTransitionActive = false;
}

void ALBManagementPawn::MoveRight(float Value)
{
    RightInput = Value;
    if (!FMath::IsNearlyZero(RightInput)) bFactoryFocusTransitionActive = false;
}

void ALBManagementPawn::Rotate(float Value)
{
    RotateInput = Value;
    if (!FMath::IsNearlyZero(RotateInput)) bFactoryFocusTransitionActive = false;
}

void ALBManagementPawn::Zoom(float Value)
{
    ZoomInput += Value;
    if (!FMath::IsNearlyZero(Value)) bFactoryFocusTransitionActive = false;
}

float ALBManagementPawn::GetManagementZoomDistance() const
{
    return CameraBoom ? CameraBoom->TargetArmLength : DesiredZoomDistance;
}

bool ALBManagementPawn::IsManagementOpen() const
{
    const APlayerController* PC = Cast<APlayerController>(GetController());
    const ALBControlRoomHUD* HUD = PC ? Cast<ALBControlRoomHUD>(PC->GetHUD()) : nullptr;
    return HUD && HUD->IsManagementVisible();
}

void ALBManagementPawn::ToggleManagement()
{
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->ToggleManagement();
}

void ALBManagementPawn::ManagementNextPage()
{
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->NextManagementPage();
}

void ALBManagementPawn::ManagementPreviousPage()
{
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->PreviousManagementPage();
}

void ALBManagementPawn::ManagementNextAction()
{
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->NextManagementAction();
}

void ALBManagementPawn::ManagementPreviousAction()
{
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->PreviousManagementAction();
}

void ALBManagementPawn::UseContextualConfirm()
{
    const APlayerController* InputController = Cast<APlayerController>(GetController());
    bUseScreenCentrePlacementCursor = InputController
        && InputController->IsInputKeyDown(EKeys::Gamepad_FaceButton_Bottom);
    if (bInfrastructureEditActive)
    {
        ConfirmInfrastructureEdit();
        return;
    }
    if (bPressTrainPlacementActive)
    {
        ConfirmPressTrainPlacement();
        return;
    }
    if (bStoragePlacementActive)
    {
        ConfirmStoragePlacement();
        return;
    }
    if (bInfrastructurePlacementActive)
    {
        ConfirmInfrastructurePlacement();
        return;
    }
    if (HasSelectedInfrastructure())
    {
        StartSelectedInfrastructureEdit();
        return;
    }
    if (AActor* FactoryActor = InspectedFactoryActor.Get())
    {
        FocusFactoryActor(FactoryActor);
        return;
    }
    if (!IsManagementOpen())
    {
        SelectFactoryActorAtScreenCentre();
        return;
    }
    if (APlayerController* PC = Cast<APlayerController>(GetController())) if (ALBControlRoomHUD* HUD = Cast<ALBControlRoomHUD>(PC->GetHUD())) HUD->ConfirmManagementAction();
}

void ALBManagementPawn::ResetCamera()
{
    if (IsAnyPlacementActive())
    {
        CancelPressTrainPlacement();
        return;
    }
    if (HasSelectedInfrastructure())
    {
        ClearInfrastructureSelection();
        return;
    }
    if (IsValid(InspectedFactoryActor.Get()))
    {
        ClearFactoryActorSelection();
        return;
    }
    bFactoryFocusTransitionActive = false;
    // Home/reset remains the player's explicit way to inspect the complete factory.
    // The automatic populated overview deliberately uses a denser process crop.
    if (FocusWholeBuiltFactory()) return;
    if (FocusInitialBuildBay()) return;
    SetActorLocationAndRotation(FVector::ZeroVector, FRotator(0.0f, -65.0f, 0.0f));
    DesiredZoomDistance = 9000.0f;
    CameraBoom->TargetArmLength = DesiredZoomDistance;
    CameraBoom->SetRelativeRotation(FRotator(-35.0f, 0.0f, 0.0f));
}

bool ALBManagementPawn::FocusInitialBuildBay()
{
    UWorld* World = GetWorld();
    if (!World || !CameraBoom) return false;
    const ALBPressShopBuildAuthority* Authority = nullptr;
    for (TActorIterator<ALBPressShopBuildAuthority> It(World); It; ++It)
    {
        if (!IsValid(*It) || It->BuildBays.IsEmpty()) continue;
        // Multiple floor authorities are unsafe for placement and equally ambiguous for
        // onboarding; let the legacy origin fallback expose that authoring fault.
        if (Authority) return false;
        Authority = *It;
    }
    if (!Authority) return false;

    const FVector Target = Authority->BuildBays[0].Centre;
    bFactoryFocusTransitionActive = false;
    SetActorLocationAndRotation(Target, FRotator(0.0f, -65.0f, 0.0f));
    DesiredZoomDistance = GetMinimumPlacementZoomDistance();
    CameraBoom->TargetArmLength = DesiredZoomDistance;
    CameraBoom->SetRelativeRotation(FRotator(-35.0f, 0.0f, 0.0f));
    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_INITIAL_BUILD_BAY_FOCUSED bay=%s centre=%s zoom=%.1f"),
        *Authority->BuildBays[0].BayId.ToString(), *Target.ToCompactString(), DesiredZoomDistance);
    return true;
}

FLBFactoryOverviewFramingContract ALBManagementPawn::BuildFactoryOverviewFramingContract(
    const FBox& RenderableFactoryBounds, const int32 FramedActorCount)
{
    FLBFactoryOverviewFramingContract Contract;
    Contract.FramedActorCount = FramedActorCount;
    const FVector Size = RenderableFactoryBounds.GetSize();
    if (!RenderableFactoryBounds.IsValid || FramedActorCount <= 0 || Size.ContainsNaN()
        || Size.GetMax() <= 1.0f || Size.GetMax() > 100000.0f)
    {
        Contract.FramedActorCount = 0;
        return Contract;
    }

    const float LongAxis = FMath::Max(Size.X, Size.Y);
    const float ShortAxis = FMath::Min(Size.X, Size.Y);
    const FVector Centre = RenderableFactoryBounds.GetCenter();
    Contract.FramedLongAxisCm = LongAxis;
    Contract.bFramesWholeFactory = true;

    // A slightly steeper-than-placement three-quarter view makes the process lanes read as
    // an intentional isometric composition. The old -65 degree yaw flattened a linear shop
    // against the screen edge and spent most of the viewport on unoccupied floor.
    Contract.PivotRotation = FRotator(0.0f, -50.0f, 0.0f);
    Contract.BoomRotation = FRotator(-32.0f, 0.0f, 0.0f);

    // Weight the visible long axis directly and retain modest depth/height headroom. This
    // is deliberately tighter than the former 1.2 x world-envelope rule, while the hard
    // gameplay limits still protect both compact starter shops and the complete ED line.
    Contract.ZoomDistanceCm = FMath::Clamp(
        LongAxis * 1.04f + ShortAxis * 0.12f + Size.Z * 0.45f,
        GetMinimumPlacementZoomDistance(), GetMaximumManagementZoomDistance());

    // The production-flow tray occupies the lower quarter of the viewport. Bias the pivot
    // toward the camera so the visual centre sits above that overlay without changing any
    // machine, storage or placement coordinates.
    const float OverlayBiasCm = FMath::Clamp(LongAxis * 0.035f, 250.0f, 850.0f);
    Contract.PivotLocation = Centre
        - Contract.PivotRotation.Vector().GetSafeNormal2D() * OverlayBiasCm;
    Contract.PivotLocation.Z = 0.0f;
    return Contract;
}

FLBFactoryOverviewFramingContract ALBManagementPawn::BuildProcessOverviewFramingContract(
    const FBox& RenderableFactoryBounds, const int32 FramedActorCount)
{
    FLBFactoryOverviewFramingContract Contract =
        BuildFactoryOverviewFramingContract(RenderableFactoryBounds, FramedActorCount);
    if (!Contract.IsValid()) return Contract;

    const FVector Size = RenderableFactoryBounds.GetSize();
    const float LongAxis = FMath::Max(Size.X, Size.Y);
    const float ShortAxis = FMath::Min(Size.X, Size.Y);

    // The selected 1280x720 management composition reserves 229 px for the
    // production tray and 18 px for its bottom margin, leaving 65.69% of the
    // canvas for the playable world. Use that same aperture as the default
    // process neighbourhood instead of fitting v008's complete 25,448.5 cm axis.
    // 17,000 cm is the rounded process aperture of those exact v008 bounds and
    // prevents a much larger future campus from silently widening the default crop.
    constexpr float MaximumProcessLongAxisCm = 17000.0f;
    const float ProcessLongAxis = FMath::Min(
        LongAxis * GetProcessOverviewWorldApertureFraction(), MaximumProcessLongAxisCm);
    Contract.FramedLongAxisCm = ProcessLongAxis;
    Contract.bFramesWholeFactory = false;
    Contract.ZoomDistanceCm = FMath::Clamp(
        ProcessLongAxis * 1.04f + ShortAxis * 0.12f + Size.Z * 0.45f,
        GetMinimumManagementZoomDistance(), GetMaximumManagementZoomDistance());

    // Keep the crop centred on the actual process geometry. Only the small
    // camera-facing overlay bias changes with the tighter framed span.
    const float OverlayBiasCm = FMath::Clamp(ProcessLongAxis * 0.035f, 250.0f, 850.0f);
    Contract.PivotLocation = RenderableFactoryBounds.GetCenter()
        - Contract.PivotRotation.Vector().GetSafeNormal2D() * OverlayBiasCm;
    Contract.PivotLocation.Z = 0.0f;
    return Contract;
}

bool ALBManagementPawn::FocusBuiltFactory()
{
    return FocusBuiltFactoryInternal(false);
}

bool ALBManagementPawn::FocusWholeBuiltFactory()
{
    return FocusBuiltFactoryInternal(true);
}

bool ALBManagementPawn::FocusBuiltFactoryInternal(const bool bWholeFactory)
{
    UWorld* World = GetWorld();
    if (!World || !CameraBoom) return false;

    // Explicit refocus always wins immediately; normal pan/orbit/zoom continues
    // untouched after this authored pose has been applied.
    bFactoryFocusTransitionActive = false;

    FBox FactoryBounds(ForceInit);
    FBox ProcessBounds(ForceInit);
    int32 FramedActorCount = 0;
    int32 ProcessActorCount = 0;
    FVector ProcessAnchor = FVector::ZeroVector;
    bool bHasProcessAnchor = false;
    for (TActorIterator<ALBPressTrainAStation> It(World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        ProcessAnchor = It->GetActorLocation();
        bHasProcessAnchor = true;
        break;
    }

    // The default is a usable production-cell view, not a miniaturised campus
    // plan.  Once a press train exists it is the stable centre of the first
    // playable department; nearby prep/blank assets form the dense opening
    // composition. Home still intentionally calls FocusWholeBuiltFactory.
    // The overview tray occupies the lower third of a 720p management view.
    // Keep the opening composition on the active press neighbourhood rather
    // than treating the entire 220 m hall as a starting camera target.
    constexpr float ProcessNeighbourhoodRadiusCm = 4000.0f;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* Actor = *It;
        if (!IsValid(Actor) || (!Actor->ActorHasTag(TEXT("LB.FactoryBuilder.Machine"))
            && !Actor->ActorHasTag(TEXT("LB.FactoryBuilder.StorageZone")))) continue;
        if (!AccumulateRenderableActorBounds(Actor, FactoryBounds)) continue;
        ++FramedActorCount;
        if (bHasProcessAnchor
            && FVector::DistSquared2D(Actor->GetActorLocation(), ProcessAnchor)
                <= FMath::Square(ProcessNeighbourhoodRadiusCm)
            && AccumulateRenderableActorBounds(Actor, ProcessBounds))
        {
            ++ProcessActorCount;
        }
    }
    if (!FactoryBounds.IsValid || FramedActorCount == 0) return false;

    const FBox& FramedBounds = !bWholeFactory && ProcessBounds.IsValid
        && ProcessActorCount > 0 ? ProcessBounds : FactoryBounds;
    const int32 ActualFramedActorCount = !bWholeFactory && ProcessBounds.IsValid
        && ProcessActorCount > 0 ? ProcessActorCount : FramedActorCount;
    const FVector Size = FramedBounds.GetSize();
    FLBFactoryOverviewFramingContract Framing = bWholeFactory
        ? BuildFactoryOverviewFramingContract(FactoryBounds, FramedActorCount)
        : BuildProcessOverviewFramingContract(FramedBounds, ActualFramedActorCount);
    if (!Framing.IsValid()) return false;

    if (!bWholeFactory && bHasProcessAnchor)
    {
        // The press-train root is the authored process datum.  It produces a
        // stable player-facing composition even when far-away logistics, Body
        // Weld, or future departments expand the aggregate factory bounds.
        // The lower production tray needs enough distance to retain both the
        // infeed and the seven press stations above it, but not so much that
        // the opening factory view becomes an empty-floor overview.
        Framing.PivotLocation = ProcessAnchor;
        // The modern UMG tray leaves 473 px at 720p. A 4.2 m floor keeps the
        // selected press cell, transfer heads and stillage cells readable in
        // that aperture, while the full-factory command remains available
        // whenever the player wants the wider planning context.
        constexpr float MinimumProcessOverviewZoomCm = 4200.0f;
        Framing.ZoomDistanceCm = FMath::Max(Framing.ZoomDistanceCm,
            MinimumProcessOverviewZoomCm);
    }
    SetActorLocationAndRotation(Framing.PivotLocation, Framing.PivotRotation);
    DesiredZoomDistance = Framing.ZoomDistanceCm;
    CameraBoom->TargetArmLength = DesiredZoomDistance;
    CameraBoom->SetRelativeRotation(Framing.BoomRotation);
    UE_LOG(LogTemp, Display,
        TEXT("LINE_BOSS_FACTORY_FOCUSED actors=%d visual_centre=%s pivot=%s size=%s yaw=%.1f pitch=%.1f zoom=%.1f mode=%s framed_long_axis=%.1f"),
        ActualFramedActorCount, *FramedBounds.GetCenter().ToCompactString(),
        *Framing.PivotLocation.ToCompactString(), *Size.ToCompactString(),
        Framing.PivotRotation.Yaw, Framing.BoomRotation.Pitch, DesiredZoomDistance,
        bWholeFactory ? TEXT("whole") : TEXT("process"), Framing.FramedLongAxisCm);
    return true;
}

bool ALBManagementPawn::SetAutomationCamera(const FVector& WorldLocation,
    const float YawDegrees, const float ZoomDistanceCm)
{
    if (!CameraBoom || WorldLocation.ContainsNaN() || !FMath::IsFinite(YawDegrees)
        || !FMath::IsFinite(ZoomDistanceCm))
    {
        return false;
    }

    SetActorLocationAndRotation(WorldLocation,
        FRotator(0.0f, FRotator::NormalizeAxis(YawDegrees), 0.0f));
    DesiredZoomDistance = FMath::Clamp(ZoomDistanceCm,
        GetMinimumManagementZoomDistance(), GetMaximumManagementZoomDistance());
    CameraBoom->TargetArmLength = DesiredZoomDistance;
    CameraBoom->SetRelativeRotation(FRotator(-35.0f, 0.0f, 0.0f));
    return true;
}

void ALBManagementPawn::StartPressTrainPlacement()
{
    StartMachinePlacement(ELBFactoryBuildMachineType::PressTrain);
}

bool ALBManagementPawn::StartMachinePlacement(const ELBFactoryBuildMachineType MachineType)
{
    if (IsAnyPlacementActive() || !GetWorld()) return false;
    ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    if (!Builder || !Builder->CanPlaceMachine(MachineType, PressTrainPlacementReason)) return false;
    SelectedMachineType = MachineType;
    if (!Builder->GetMachinePlacementEnvelope(MachineType, MachinePreviewHalfExtent,
        MachinePreviewEnvelopeRelativeCentre, MachinePreviewRootHeightCm,
        PressTrainPlacementReason))
    {
        PressTrainPlacementReason = TEXT("MACHINE PLACEMENT PREVIEW COULD NOT BE CREATED");
        return false;
    }
    bPressTrainPlacementActive = true;
    DesiredZoomDistance = FMath::Max(DesiredZoomDistance, GetMinimumPlacementZoomDistance());
    CameraBoom->TargetArmLength = FMath::Max(CameraBoom->TargetArmLength, GetMinimumPlacementZoomDistance());
    bPressTrainPlacementValid = false;
    PressTrainPlacementReason = TEXT("MOVE CURSOR OVER THE FACTORY FLOOR");
    const FRotator InitialRotation(0.0f,
        MachineType == ELBFactoryBuildMachineType::PressTrain ? -90.0f : 0.0f, 0.0f);
    PressTrainPreviewTransform = FTransform(InitialRotation, GetActorLocation(), FVector::OneVector);
    bPlacementFramingSideLocked = false;
    BuildMachinePlacementGhost(MachineType);
    return true;
}

void ALBManagementPawn::CancelPressTrainPlacement()
{
    // Escape / controller B is also the local inspector's back action. Selection is cleared
    // before the next press can reset the camera, matching the controller confirm hierarchy.
    if (!IsAnyPlacementActive())
    {
        if (HasSelectedInfrastructure())
        {
            ClearInfrastructureSelection();
            return;
        }
        if (IsValid(InspectedFactoryActor.Get()))
        {
            ClearFactoryActorSelection();
            return;
        }
    }
    if (bInfrastructureEditActive) CancelInfrastructureEdit(false);
    bPressTrainPlacementActive = false;
    bPressTrainPlacementValid = false;
    bStoragePlacementActive = false;
    bStoragePlacementValid = false;
    bStorageDragActive = false;
    bInfrastructurePlacementActive = false;
    bInfrastructurePlacementValid = false;
    PressTrainPlacementReason = TEXT("PLACEMENT CANCELLED");
    StoragePlacementReason = TEXT("PLACEMENT CANCELLED");
    InfrastructurePlacementReason = TEXT("PLACEMENT CANCELLED");
    ResetPlacementPresentation();
}

void ALBManagementPawn::RotatePressTrainPlacement()
{
    if (!IsAnyPlacementActive()) return;
    FTransform& Preview = bPressTrainPlacementActive ? PressTrainPreviewTransform
        : (bStoragePlacementActive ? StoragePreviewTransform
            : (bInfrastructurePlacementActive ? InfrastructurePreviewTransform : InfrastructureEditPreviewTransform));
    FRotator Rotation = Preview.Rotator();
    Rotation.Yaw = FMath::GridSnap(Rotation.Yaw + 90.0f, 90.0f);
    Preview.SetRotation(Rotation.Quaternion());
}

FName ALBManagementPawn::GetInspectedInfrastructureId() const
{
    return IsValid(InspectedInfrastructure) ? InspectedInfrastructure->GetInfrastructureId() : NAME_None;
}

ELBFactoryAGVInfrastructureType ALBManagementPawn::GetInspectedInfrastructureType() const
{
    return IsValid(InspectedInfrastructure) ? InspectedInfrastructure->GetInfrastructureType()
        : ELBFactoryAGVInfrastructureType::PedestrianWalkway;
}

ELBFactoryInfrastructureProvenance ALBManagementPawn::GetInspectedInfrastructureProvenance() const
{
    return IsValid(InspectedInfrastructure) ? InspectedInfrastructure->GetProvenance()
        : ELBFactoryInfrastructureProvenance::PlayerPlaced;
}

bool ALBManagementPawn::SelectInfrastructure(ALBFactoryAGVInfrastructure* Infrastructure)
{
    if (!IsValid(Infrastructure) || IsAnyPlacementActive()) return false;
    if (IsValid(InspectedFactoryActor.Get())) ClearFactoryActorSelection();
    if (IsValid(InspectedInfrastructure)) InspectedInfrastructure->SetSelectionHighlighted(false);
    InspectedInfrastructure = Infrastructure;
    InspectedInfrastructure->SetSelectionHighlighted(true);
    InfrastructureEditReason = TEXT("SELECTED; PRESS ENTER / A TO MOVE, OR ESC TO CLEAR");
    return true;
}

bool ALBManagementPawn::SelectInfrastructureAlongViewRay(
    const FVector& RayOrigin, const FVector& RayDirection)
{
    UWorld* World = GetWorld();
    if (!World || RayOrigin.ContainsNaN() || RayDirection.ContainsNaN()
        || RayDirection.IsNearlyZero()) return false;
    TArray<FHitResult> Hits;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(LBInfrastructureSelectionRay), false, this);
    if (!World->LineTraceMultiByChannel(Hits, RayOrigin,
        RayOrigin + RayDirection.GetSafeNormal() * 100000.0f,
        ECC_Visibility, Params)) return false;
    for (const FHitResult& Hit : Hits)
    {
        if (ALBFactoryAGVInfrastructure* Infrastructure =
            Cast<ALBFactoryAGVInfrastructure>(Hit.GetActor()))
        {
            return SelectInfrastructure(Infrastructure);
        }
    }
    return false;
}

bool ALBManagementPawn::SelectInfrastructureAtScreenCentre()
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    if (!PC) return false;
    int32 ViewX = 0;
    int32 ViewY = 0;
    PC->GetViewportSize(ViewX, ViewY);
    FVector RayOrigin;
    FVector RayDirection;
    return ViewX > 0 && ViewY > 0
        && PC->DeprojectScreenPositionToWorld(ViewX * 0.5f, ViewY * 0.5f, RayOrigin, RayDirection)
        && SelectInfrastructureAlongViewRay(RayOrigin, RayDirection);
}

bool ALBManagementPawn::SelectFactoryActorAtScreenCentre()
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    if (!PC) return false;
    int32 ViewX = 0;
    int32 ViewY = 0;
    PC->GetViewportSize(ViewX, ViewY);
    FVector RayOrigin;
    FVector RayDirection;
    return ViewX > 0 && ViewY > 0
        && PC->DeprojectScreenPositionToWorld(
            ViewX * 0.5f, ViewY * 0.5f, RayOrigin, RayDirection)
        && SelectFactoryActorAlongViewRay(RayOrigin, RayDirection, true);
}

bool ALBManagementPawn::SelectFactoryActorAlongViewRay(
    const FVector& RayOrigin, const FVector& RayDirection,
    const bool bFocusIfAlreadySelected)
{
    UWorld* World = GetWorld();
    if (!World || RayOrigin.ContainsNaN() || RayDirection.ContainsNaN()
        || RayDirection.IsNearlyZero() || IsAnyPlacementActive()) return false;

    TArray<FHitResult> Hits;
    FCollisionQueryParams Params(SCENE_QUERY_STAT(LBFactoryActorSelectionRay), false, this);
    if (!World->LineTraceMultiByChannel(Hits, RayOrigin,
        RayOrigin + RayDirection.GetSafeNormal() * 100000.0f,
        ECC_Visibility, Params)) return false;

    // A route/walkway owns selection whenever its existing proxy is in the resolved hit set.
    // That retains the established infrastructure edit flow while allowing overlap-only
    // machine envelopes and empty storage volumes to be considered on the second pass.
    for (const FHitResult& Hit : Hits)
    {
        if (ALBFactoryAGVInfrastructure* Infrastructure =
            Cast<ALBFactoryAGVInfrastructure>(Hit.GetActor()))
        {
            return SelectInfrastructure(Infrastructure);
        }
    }

    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    if (!UIState) return false;
    for (const FHitResult& Hit : Hits)
    {
        AActor* Candidate = Hit.GetActor();
        for (int32 ParentDepth = 0; IsValid(Candidate) && ParentDepth < 3; ++ParentDepth)
        {
            FLBFactoryUIInspectorSnapshot Inspector;
            if (UIState->BuildInspectorSnapshot(Candidate, Inspector) && Inspector.bValid)
            {
                const bool bAlreadySelected = Candidate == InspectedFactoryActor.Get();
                return SelectFactoryActor(Candidate,
                    bFocusIfAlreadySelected && bAlreadySelected);
            }
            AActor* Parent = Candidate->GetAttachParentActor();
            if (!Parent) Parent = Candidate->GetOwner();
            if (Parent == Candidate) break;
            Candidate = Parent;
        }
    }
    return false;
}

bool ALBManagementPawn::SelectFactoryActor(AActor* FactoryActor, const bool bFocus)
{
    UWorld* World = GetWorld();
    if (!World || !IsValid(FactoryActor) || IsAnyPlacementActive()) return false;
    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    FLBFactoryUIInspectorSnapshot Inspector;
    if (!UIState || !UIState->BuildInspectorSnapshot(FactoryActor, Inspector)
        || !Inspector.bValid) return false;

    if (HasSelectedInfrastructure()) ClearInfrastructureSelection();
    if (FactoryActor != InspectedFactoryActor.Get())
    {
        bFactoryFocusTransitionActive = false;
        RestoreFactorySelectionHighlight();
        InspectedFactoryActor = FactoryActor;
        ApplyFactorySelectionHighlight(FactoryActor);
    }
    else if (FactoryHighlightComponents.IsEmpty())
    {
        ApplyFactorySelectionHighlight(FactoryActor);
    }

    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_FACTORY_ACTOR_SELECTED id=%s kind=%s actor=%s focus=%d"),
        *Inspector.EntityId.ToString(), *Inspector.Kind,
        *FactoryActor->GetActorNameOrLabel(), bFocus ? 1 : 0);
    return !bFocus || FocusFactoryActor(FactoryActor);
}

void ALBManagementPawn::ClearFactoryActorSelection()
{
    RestoreFactorySelectionHighlight();
    InspectedFactoryActor.Reset();
    bFactoryFocusTransitionActive = false;
}

void ALBManagementPawn::RestoreFactorySelectionHighlight()
{
    const int32 RestorableCount = FMath::Min(
        FactoryHighlightComponents.Num(), FactoryHighlightPreviousCustomDepth.Num());
    for (int32 Index = 0; Index < RestorableCount; ++Index)
    {
        if (UPrimitiveComponent* Component = FactoryHighlightComponents[Index].Get())
        {
            Component->SetRenderCustomDepth(
                FactoryHighlightPreviousCustomDepth[Index]);
        }
    }
    FactoryHighlightComponents.Reset();
    FactoryHighlightPreviousCustomDepth.Reset();
}

void ALBManagementPawn::ApplyFactorySelectionHighlight(AActor* FactoryActor)
{
    if (!IsValid(FactoryActor)) return;
    TInlineComponentArray<UPrimitiveComponent*> PrimitiveComponents;
    FactoryActor->GetComponents(PrimitiveComponents, true);
    for (UPrimitiveComponent* Component : PrimitiveComponents)
    {
        if (!IsValid(Component) || !Component->IsRegistered()
            || !Component->ShouldRender()) continue;
        FactoryHighlightComponents.Add(Component);
        FactoryHighlightPreviousCustomDepth.Add(Component->bRenderCustomDepth != 0);
        Component->SetRenderCustomDepth(true);
    }
}

bool ALBManagementPawn::FocusFactoryActor(AActor* FactoryActor)
{
    UWorld* World = GetWorld();
    if (!World || !IsValid(FactoryActor) || IsAnyPlacementActive()) return false;
    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    FLBFactoryUIInspectorSnapshot Inspector;
    if (!UIState || !UIState->BuildInspectorSnapshot(FactoryActor, Inspector)
        || !Inspector.bValid) return false;

    FBox Bounds = FactoryActor->GetComponentsBoundingBox(true, true);
    if (!Bounds.IsValid || Bounds.GetSize().ContainsNaN()
        || Bounds.GetSize().GetMax() > 30000.0f)
    {
        const FVector Origin = FactoryActor->GetActorLocation();
        Bounds = FBox(Origin - FVector(150.0f), Origin + FVector(150.0f));
    }
    const FVector Size = Bounds.GetSize();
    float ZoomDistance = 0.0f;
    FVector Target = Bounds.GetCenter();
    if (const ALBBodyWeldLineActor* BodyWeldLine = Cast<ALBBodyWeldLineActor>(FactoryActor))
    {
        // The Body Weld actor includes long port/envelope metadata, but its player-facing
        // cell is the framing fixture, split base kit and four tool robots around local X
        // 2700. A generic whole-actor fit leaves that work visually lost in floor space.
        Target = BodyWeldLine->GetActorTransform().TransformPosition(
            FVector(2700.0f, 0.0f, 220.0f));
        ZoomDistance = 4400.0f;
    }
    else
    {
        const float HorizontalDiameter = FMath::Max(Size.X, Size.Y);
        const float FramingDistance = FMath::Max(
            HorizontalDiameter * 1.35f + 600.0f,
            Size.Z * 2.2f + 600.0f);
        ZoomDistance = FMath::Clamp(FramingDistance,
            1800.0f, GetMaximumManagementZoomDistance());
    }
    if (!FocusWorldTarget(Target, ZoomDistance)) return false;

    UE_LOG(LogTemp, Display, TEXT("LINE_BOSS_FACTORY_ACTOR_FOCUS id=%s target=%s size=%s zoom=%.1f"),
        *Inspector.EntityId.ToString(), *Target.ToCompactString(),
        *Size.ToCompactString(), ZoomDistance);
    return true;
}

bool ALBManagementPawn::FocusWorldTarget(const FVector& WorldTarget,
    const float ZoomDistanceCm)
{
    if (!CameraBoom || IsAnyPlacementActive() || WorldTarget.ContainsNaN()
        || !FMath::IsFinite(ZoomDistanceCm)
        || WorldTarget.GetAbsMax() > 1000000.0f) return false;

    FactoryFocusTargetLocation = WorldTarget;
    FactoryFocusTargetRotation = FRotator(0.0f, GetActorRotation().Yaw, 0.0f);
    DesiredZoomDistance = FMath::Clamp(ZoomDistanceCm,
        GetMinimumManagementZoomDistance(), GetMaximumManagementZoomDistance());
    CameraBoom->SetRelativeRotation(FRotator(-35.0f, 0.0f, 0.0f));
    bFactoryFocusTransitionActive = true;
    return true;
}

void ALBManagementPawn::UpdateFactoryFocusTransition(const float DeltaSeconds)
{
    if (!bFactoryFocusTransitionActive || DeltaSeconds <= 0.0f) return;
    const FVector NewLocation = FMath::VInterpTo(GetActorLocation(),
        FactoryFocusTargetLocation, DeltaSeconds, 5.5f);
    const FRotator NewRotation = FMath::RInterpTo(GetActorRotation(),
        FactoryFocusTargetRotation, DeltaSeconds, 5.5f);
    SetActorLocationAndRotation(NewLocation, NewRotation, false, nullptr,
        ETeleportType::None);
    if (FVector::DistSquared(NewLocation, FactoryFocusTargetLocation) <= 4.0f
        && FMath::Abs(FMath::FindDeltaAngleDegrees(
            NewRotation.Yaw, FactoryFocusTargetRotation.Yaw)) <= 0.1f)
    {
        SetActorLocationAndRotation(FactoryFocusTargetLocation,
            FactoryFocusTargetRotation, false, nullptr, ETeleportType::None);
        bFactoryFocusTransitionActive = false;
    }
}

bool ALBManagementPawn::JumpToTopFactoryAlert()
{
    UWorld* World = GetWorld();
    if (!World || IsAnyPlacementActive()) return false;
    ULBFactoryUIStateSubsystem* UIState =
        World->GetSubsystem<ULBFactoryUIStateSubsystem>();
    if (!UIState) return false;
    const FLBFactoryUIAlertSnapshot* Alert =
        UIState->GetSnapshot(true).GetTopAlert();
    if (!Alert) return false;

    AActor* TargetActor = Alert->TargetActor.Get();
    if (!IsValid(TargetActor))
        TargetActor = UIState->FindFactoryActorById(Alert->EntityId);
    if (IsValid(TargetActor) && SelectFactoryActor(TargetActor, true))
        return true;
    return FocusWorldTarget(Alert->MarkerWorldLocation, 3200.0f);
}

void ALBManagementPawn::ClearInfrastructureSelection()
{
    if (bInfrastructureEditActive) CancelInfrastructureEdit(false);
    if (IsValid(InspectedInfrastructure)) InspectedInfrastructure->SetSelectionHighlighted(false);
    InspectedInfrastructure = nullptr;
    bInfrastructureEditValid = false;
    InfrastructureEditReason = TEXT("CLICK A ROUTE OR WALKWAY TO SELECT IT");
}

bool ALBManagementPawn::StartSelectedInfrastructureEdit()
{
    if (!IsValid(InspectedInfrastructure) || IsAnyPlacementActive() || !GetWorld()) return false;
    ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    if (!Builder || !Builder->CanEditAGVInfrastructure(
        InspectedInfrastructure->GetInfrastructureId(), InfrastructureEditReason)) return false;
    InfrastructureEditOriginalTransform = InspectedInfrastructure->GetActorTransform();
    InfrastructureEditPreviewTransform = InfrastructureEditOriginalTransform;
    InfrastructureEditHalfExtent = InspectedInfrastructure->GetPlacementHalfExtentCm();
    bInfrastructureEditActive = true;
    bInfrastructureEditValid = true;
    DesiredZoomDistance = FMath::Max(DesiredZoomDistance, GetMinimumPlacementZoomDistance());
    InfrastructureEditReason = TEXT("MOVE THE CURSOR; CLICK / ENTER TO CONFIRM OR ESC TO CANCEL");
    bPlacementFramingSideLocked = false;
    BuildInfrastructurePlacementGhost(InspectedInfrastructure->GetInfrastructureType(),
        InspectedInfrastructure->GetTrainIndex(), InspectedInfrastructure);
    return true;
}

bool ALBManagementPawn::ConfirmInfrastructureEdit()
{
    if (!bInfrastructureEditActive || !bInfrastructureEditValid
        || !IsValid(InspectedInfrastructure) || !GetWorld()) return false;
    ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    const bool bUpdated = Builder && Builder->UpdateAGVInfrastructureTransform(
        InspectedInfrastructure->GetInfrastructureId(), InfrastructureEditPreviewTransform,
        InfrastructureEditReason);
    if (bUpdated)
    {
        InfrastructureEditOriginalTransform = InspectedInfrastructure->GetActorTransform();
        bInfrastructureEditActive = false;
        bInfrastructureEditValid = false;
        InfrastructureEditReason = TEXT("EDIT SAVED; AUTOMATIC ROUTE AUTHORITY REBOUND");
        ResetPlacementPresentation();
    }
    return bUpdated;
}

void ALBManagementPawn::CancelInfrastructureEdit(const bool bClearSelection)
{
    bInfrastructureEditActive = false;
    bInfrastructureEditValid = false;
    InfrastructureEditPreviewTransform = InfrastructureEditOriginalTransform;
    InfrastructureEditReason = TEXT("EDIT CANCELLED; ORIGINAL TRANSFORM RETAINED");
    ResetPlacementPresentation();
    if (bClearSelection) ClearInfrastructureSelection();
}

bool ALBManagementPawn::StartInfrastructurePlacement(const ELBFactoryAGVInfrastructureType Type)
{
    if (IsAnyPlacementActive() || !GetWorld()) return false;
    ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    const int32 TrainIndex = Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff
        ? (Builder ? Builder->GetNextAvailablePressTrainHandoffIndex() : INDEX_NONE) : INDEX_NONE;
    if (!Builder || !Builder->CanPlaceAGVInfrastructure(Type, TrainIndex, InfrastructurePlacementReason)) return false;
    ALBFactoryAGVInfrastructure* Defaults = GetWorld()->SpawnActor<ALBFactoryAGVInfrastructure>();
    if (!Defaults || !Defaults->Configure(TEXT("INFRASTRUCTURE-PREVIEW"), Type, TrainIndex))
    {
        if (Defaults) Defaults->Destroy();
        InfrastructurePlacementReason = TEXT("INFRASTRUCTURE PREVIEW COULD NOT BE CREATED");
        return false;
    }
    InfrastructurePreviewHalfExtent = Defaults->GetPlacementHalfExtentCm();
    Defaults->Destroy();
    SelectedInfrastructureType = Type;
    SelectedInfrastructureTrainIndex = TrainIndex;
    bInfrastructurePlacementActive = true;
    bInfrastructurePlacementValid = false;
    InfrastructurePreviewTransform = FTransform(FRotator::ZeroRotator, GetActorLocation(), FVector::OneVector);
    DesiredZoomDistance = FMath::Max(DesiredZoomDistance, GetMinimumPlacementZoomDistance());
    InfrastructurePlacementReason = TEXT("MOVE CURSOR OVER THE FACTORY FLOOR");
    bPlacementFramingSideLocked = false;
    BuildInfrastructurePlacementGhost(Type, TrainIndex);
    return true;
}

bool ALBManagementPawn::ConfirmInfrastructurePlacement()
{
    if (!bInfrastructurePlacementActive || !bInfrastructurePlacementValid || !GetWorld()) return false;
    ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    ALBFactoryAGVInfrastructure* Placed = nullptr;
    const bool bPlaced = Builder && Builder->PlaceAGVInfrastructure(SelectedInfrastructureType,
        SelectedInfrastructureTrainIndex, InfrastructurePreviewTransform, Placed, InfrastructurePlacementReason);
    if (bPlaced)
    {
        // Placement must not change route ownership. Automatic route generation and the
        // transactional editor rebind only the AGVs whose explicit profile owns the route.
        bInfrastructurePlacementActive = false;
        bInfrastructurePlacementValid = false;
        SelectedInfrastructureTrainIndex = INDEX_NONE;
        ResetPlacementPresentation();
    }
    return bPlaced;
}

bool ALBManagementPawn::StartStoragePlacement(ELBPressShopStorageType StorageType)
{
    if (IsAnyPlacementActive() || !GetWorld()) return false;
    ALBPressShopBuildAuthority* Authority = nullptr;
    int32 AuthorityCount = 0;
    for (TActorIterator<ALBPressShopBuildAuthority> It(GetWorld()); It; ++It)
    {
        Authority = *It;
        ++AuthorityCount;
    }
    if (AuthorityCount != 1 || !Authority)
    {
        StoragePlacementReason = AuthorityCount == 0
            ? TEXT("STORAGE BUILD AUTHORITY OFFLINE") : TEXT("STORAGE BUILD AUTHORITY IS AMBIGUOUS");
        return false;
    }
    FString DefaultsReason;
    if (!Authority->GetStoragePlacementDefaults(
        StorageType, StoragePreviewHalfExtent, StoragePreviewCapacity, DefaultsReason))
    {
        StoragePlacementReason = DefaultsReason;
        return false;
    }
    SelectedStorageType = StorageType;
    bStoragePlacementActive = true;
    bStoragePlacementValid = false;
    DesiredZoomDistance = FMath::Max(DesiredZoomDistance, GetMinimumPlacementZoomDistance());
    CameraBoom->TargetArmLength = FMath::Max(CameraBoom->TargetArmLength, GetMinimumPlacementZoomDistance());
    StoragePreviewTransform = FTransform(FRotator::ZeroRotator, GetActorLocation(), FVector::OneVector);
    StoragePreviewColumns = 0;
    StoragePreviewRows = 0;
    StoragePlacementReason = TEXT("MOVE CURSOR OVER AN AUTHORISED STORAGE BAY");
    bPlacementFramingSideLocked = false;
    BuildStoragePlacementGhost();
    return true;
}

bool ALBManagementPawn::ConfirmStoragePlacement()
{
    if (!bStoragePlacementActive || !bStoragePlacementValid || !GetWorld()) return false;
    ALBPressShopBuildAuthority* Authority = nullptr;
    int32 AuthorityCount = 0;
    for (TActorIterator<ALBPressShopBuildAuthority> It(GetWorld()); It; ++It)
    {
        Authority = *It;
        ++AuthorityCount;
    }
    if (AuthorityCount != 1 || !Authority) return false;
    ALBPressShopStorageZone* Zone = nullptr;
    const bool bPlaced = Authority->PlaceStorageZone(SelectedStorageType, StoragePreviewTransform,
        StoragePreviewHalfExtent, StoragePreviewCapacity, Zone, StoragePlacementReason);
    if (bPlaced)
    {
        bStoragePlacementActive = false;
        bStoragePlacementValid = false;
        ResetPlacementPresentation();
    }
    return bPlaced;
}

bool ALBManagementPawn::ConfirmPressTrainPlacement()
{
    if (!bPressTrainPlacementActive || !bPressTrainPlacementValid || !GetWorld()) return false;
    ULBFactoryMachineBuilderSubsystem* Builder = GetWorld()->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    AActor* PlacedMachine = nullptr;
    const bool bPlaced = Builder && Builder->PlaceMachine(
        SelectedMachineType, PressTrainPreviewTransform, PlacedMachine, PressTrainPlacementReason);
    if (bPlaced)
    {
        bPressTrainPlacementActive = false;
        bPressTrainPlacementValid = false;
        ResetPlacementPresentation();
    }
    return bPlaced;
}

bool ALBManagementPawn::TraceFactoryFloorUnderCursor(FHitResult& OutHit) const
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    UWorld* World = GetWorld();
    if (!PC || !World) return false;

    float ScreenX = 0.0f;
    float ScreenY = 0.0f;
    if (bUseScreenCentrePlacementCursor)
    {
        int32 ViewX = 0;
        int32 ViewY = 0;
        PC->GetViewportSize(ViewX, ViewY);
        ScreenX = ViewX * 0.5f;
        ScreenY = ViewY * 0.5f;
    }
    else if (!PC->GetMousePosition(ScreenX, ScreenY))
    {
        int32 ViewX = 0;
        int32 ViewY = 0;
        PC->GetViewportSize(ViewX, ViewY);
        ScreenX = ViewX * 0.5f;
        ScreenY = ViewY * 0.5f;
    }
    FVector RayOrigin;
    FVector RayDirection;
    if (!PC->DeprojectScreenPositionToWorld(ScreenX, ScreenY, RayOrigin, RayDirection)) return false;

    FCollisionQueryParams Params(SCENE_QUERY_STAT(LBFactoryFloorPlacementTrace), false, this);
    // Selection proxies deliberately block Visibility for click inspection. Ignore every
    // infrastructure actor here so the same proxy can never lift a placement preview off floor.
    for (TActorIterator<ALBFactoryAGVInfrastructure> It(World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    // The ED line envelope is intentionally selectable, but placement must still use the
    // underlying build-bay datum rather than floating on its one-storey visibility proxy.
    for (TActorIterator<ALBECoatLineActor> It(World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    for (TActorIterator<ALBBodyWeldLineActor> It(World); It; ++It)
        if (IsValid(*It)) Params.AddIgnoredActor(*It);
    return World->LineTraceSingleByChannel(OutHit, RayOrigin,
        RayOrigin + RayDirection * 100000.0f, ECC_Visibility, Params);
}

void ALBManagementPawn::UpdatePressTrainPlacementPreview()
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    UWorld* World = GetWorld();
    if (!PC || !World) return;

    FHitResult FloorHit;
    const bool bHit = TraceFactoryFloorUnderCursor(FloorHit);

    if (!bHit)
    {
        bPressTrainPlacementValid = false;
        PressTrainPlacementReason = TEXT("NO FACTORY FLOOR UNDER CURSOR; MOVE CURSOR ONTO AN AUTHORISED FACTORY FLOOR");
        const FLBPlacementPreviewStyle Style = BuildPlacementPreviewStyle(
            false, false, PressTrainPlacementReason);
        DrawMissingFloorCue(World, Camera, Style);
        PlacementCardData = BuildPlacementCardData(ResolveCurrentPlacementTitle(), Style);
        return;
    }

    FVector Snapped = FloorHit.ImpactPoint;
    Snapped.X = FMath::GridSnap(Snapped.X, 100.0f);
    Snapped.Y = FMath::GridSnap(Snapped.Y, 100.0f);
    FVector PlacementLocation = Snapped;
    PlacementLocation.Z += MachinePreviewRootHeightCm;
    PressTrainPreviewTransform.SetLocation(PlacementLocation);
    PressTrainPreviewTransform.SetScale3D(FVector::OneVector);
    CurrentPlacementObstructionDisplayName.Reset();
    CurrentPlacementObstructionStableId.Reset();

    if (ULBFactoryMachineBuilderSubsystem* Builder = World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>())
    {
        bPressTrainPlacementValid = Builder->CanPlaceMachine(SelectedMachineType, PressTrainPlacementReason);
        if (bPressTrainPlacementValid
            && (SelectedMachineType == ELBFactoryBuildMachineType::ECoatLine
                || SelectedMachineType == ELBFactoryBuildMachineType::BodyWeldLine))
        {
            bPressTrainPlacementValid = Builder->ValidateMachineTransform(
                SelectedMachineType, PressTrainPreviewTransform, PressTrainPlacementReason);
            if (!bPressTrainPlacementValid
                && PressTrainPlacementReason.Contains(TEXT("IS OBSTRUCTED")))
            {
                FString BlockingActorLabel;
                FString ComponentLabel;
                const FVector EnvelopeCentre = PressTrainPreviewTransform.TransformPosition(
                    MachinePreviewEnvelopeRelativeCentre);
                const FVector CollisionHalfExtent(
                    FMath::Max(1.0f, MachinePreviewHalfExtent.X - 5.0f),
                    FMath::Max(1.0f, MachinePreviewHalfExtent.Y - 5.0f),
                    FMath::Max(1.0f, MachinePreviewHalfExtent.Z - 5.0f));
                if (FindNamedBlockingOverlap(World, EnvelopeCentre, CollisionHalfExtent,
                    PressTrainPreviewTransform.GetRotation(), this,
                    BlockingActorLabel, ComponentLabel, &CurrentPlacementObstructionStableId))
                {
                    CurrentPlacementObstructionDisplayName = BlockingActorLabel;
                    PressTrainPlacementReason = FormatNamedObstructionReason(
                        TEXT("ED LINE PROTECTED ENVELOPE"), BlockingActorLabel, ComponentLabel);
                }
            }
        }
        else if (bPressTrainPlacementValid && SelectedMachineType == ELBFactoryBuildMachineType::PressTrain)
        {
            if (ULBPressTrainIdentitySubsystem* Identity = World->GetSubsystem<ULBPressTrainIdentitySubsystem>())
                bPressTrainPlacementValid = Identity->CanPlaceTrain(PressTrainPreviewTransform, PressTrainPlacementReason);
            else
            {
                bPressTrainPlacementValid = false;
                PressTrainPlacementReason = TEXT("TRAIN IDENTITY AUTHORITY OFFLINE");
            }
        }
        else if (bPressTrainPlacementValid)
        {
            FCollisionShape Shape = FCollisionShape::MakeBox(MachinePreviewHalfExtent - FVector(5.0f));
            FCollisionQueryParams Params(SCENE_QUERY_STAT(LBMachinePlacementEnvelope), false, this);
            const FVector EnvelopeCentre = PressTrainPreviewTransform.TransformPosition(
                MachinePreviewEnvelopeRelativeCentre);
            TArray<FOverlapResult> Overlaps;
            if (World->OverlapMultiByChannel(Overlaps, EnvelopeCentre,
                PressTrainPreviewTransform.GetRotation(), ECC_WorldDynamic, Shape, Params))
            {
                bPressTrainPlacementValid = false;
                const FOverlapResult* Named = Overlaps.FindByPredicate([](const FOverlapResult& Result)
                {
                    return Result.bBlockingHit && (Result.GetActor() || Result.GetComponent());
                });
                if (!Named) Named = Overlaps.FindByPredicate([](const FOverlapResult& Result)
                {
                    return Result.GetActor() || Result.GetComponent();
                });
                PressTrainPlacementReason = FormatNamedObstructionReason(
                    TEXT("PROTECTED MACHINE ENVELOPE"),
                    Named && Named->GetActor() ? Named->GetActor()->GetActorNameOrLabel() : FString(),
                    Named && Named->GetComponent() ? Named->GetComponent()->GetName() : FString());
                if (Named && Named->GetActor())
                {
                    CurrentPlacementObstructionDisplayName = FriendlyActorName(
                        Named->GetActor()->GetActorNameOrLabel());
                    CurrentPlacementObstructionStableId = StableIdFromActor(Named->GetActor());
                }
            }
            else PressTrainPlacementReason = TEXT("ORDER AND PROTECTED ENVELOPE VALID; AUTOMATIC LINK READY");
        }
    }
    else
    {
        bPressTrainPlacementValid = false;
        PressTrainPlacementReason = TEXT("MACHINE BUILDER AUTHORITY OFFLINE");
    }

    const FLBPlacementPreviewStyle Style = BuildPlacementPreviewStyle(
        true, bPressTrainPlacementValid, PressTrainPlacementReason);
    const FLBPlacementPreviewGeometry Geometry = BuildMachinePlacementPreviewGeometry(
        SelectedMachineType, PressTrainPreviewTransform, MachinePreviewEnvelopeRelativeCentre,
        MachinePreviewHalfExtent, Snapped.Z);
    DrawPlacementGroundFootprint(World, PressTrainPreviewTransform, Geometry, Style);
    DrawPlacementEnvelope(World, PressTrainPreviewTransform, Geometry, Style);
    DrawPlacementState(World, PressTrainPreviewTransform, Geometry, Style);
    DrawProcessFlowIntent(World, Geometry);
    UpdatePlacementPresentation(ResolveCurrentPlacementTitle(), Geometry, Style);
}

void ALBManagementPawn::UpdateStoragePlacementPreview()
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    UWorld* World = GetWorld();
    if (!PC || !World) return;

    FHitResult FloorHit;
    const bool bHit = TraceFactoryFloorUnderCursor(FloorHit);
    if (!bHit)
    {
        bStoragePlacementValid = false;
        StoragePlacementReason = TEXT("NO FACTORY FLOOR UNDER CURSOR; MOVE CURSOR ONTO AN AUTHORISED FACTORY FLOOR");
        const FLBPlacementPreviewStyle Style = BuildPlacementPreviewStyle(
            false, false, StoragePlacementReason);
        DrawMissingFloorCue(World, Camera, Style);
        PlacementCardData = BuildPlacementCardData(ResolveCurrentPlacementTitle(), Style);
        return;
    }

    FVector SnappedFloor = FloorHit.ImpactPoint;
    SnappedFloor.X = FMath::GridSnap(SnappedFloor.X, 100.0f);
    SnappedFloor.Y = FMath::GridSnap(SnappedFloor.Y, 100.0f);
    if (bStorageDragActive)
    {
        const FVector Delta = SnappedFloor - StorageDragAnchor;
        StoragePreviewHalfExtent.X = FMath::Max(50.0f,
            FMath::GridSnap(FMath::Abs(Delta.X) * 0.5f, 50.0f));
        StoragePreviewHalfExtent.Y = FMath::Max(50.0f,
            FMath::GridSnap(FMath::Abs(Delta.Y) * 0.5f, 50.0f));
        SnappedFloor.X = (SnappedFloor.X + StorageDragAnchor.X) * 0.5f;
        SnappedFloor.Y = (SnappedFloor.Y + StorageDragAnchor.Y) * 0.5f;
    }
    FVector PreviewCentre = SnappedFloor;
    PreviewCentre.Z += StoragePreviewHalfExtent.Z;
    StoragePreviewTransform.SetLocation(PreviewCentre);
    StoragePreviewTransform.SetScale3D(FVector::OneVector);
    CurrentPlacementObstructionDisplayName.Reset();
    CurrentPlacementObstructionStableId.Reset();

    ALBPressShopBuildAuthority* Authority = nullptr;
    int32 AuthorityCount = 0;
    for (TActorIterator<ALBPressShopBuildAuthority> It(World); It; ++It)
    {
        Authority = *It;
        ++AuthorityCount;
    }
    if (AuthorityCount == 1 && Authority)
    {
        FString EnvelopeReason;
        FString LayoutReason;
        const bool bEnvelopeValid = Authority->EvaluateStorageTransform(
            SelectedStorageType, StoragePreviewTransform, StoragePreviewHalfExtent, EnvelopeReason);
        const bool bLayoutValid = Authority->CalculateStorageLayout(
            SelectedStorageType, StoragePreviewTransform, StoragePreviewHalfExtent,
            StoragePreviewColumns, StoragePreviewRows, StoragePreviewCapacity, LayoutReason);
        bStoragePlacementValid = bEnvelopeValid && bLayoutValid;
        StoragePlacementReason = bStoragePlacementValid
            ? FString::Printf(TEXT("%s; %s"), *EnvelopeReason, *LayoutReason)
            : (bEnvelopeValid ? LayoutReason : EnvelopeReason);
    }
    else
    {
        bStoragePlacementValid = false;
        StoragePlacementReason = AuthorityCount == 0
            ? TEXT("STORAGE BUILD AUTHORITY OFFLINE") : TEXT("STORAGE BUILD AUTHORITY IS AMBIGUOUS");
    }

    const FLBPlacementPreviewStyle Style = BuildPlacementPreviewStyle(
        true, bStoragePlacementValid, StoragePlacementReason);
    const FLBPlacementPreviewGeometry Geometry = BuildPlacementPreviewGeometry(
        StoragePreviewTransform, FVector::ZeroVector, StoragePreviewHalfExtent,
        SnappedFloor.Z, false, true);
    DrawPlacementGroundFootprint(World, StoragePreviewTransform, Geometry, Style);
    DrawPlacementEnvelope(World, StoragePreviewTransform, Geometry, Style);
    DrawPlacementState(World, StoragePreviewTransform, Geometry, Style);
    DrawProcessFlowIntent(World, Geometry);
    UpdatePlacementPresentation(ResolveCurrentPlacementTitle(), Geometry, Style);
}

void ALBManagementPawn::UpdateInfrastructurePlacementPreview()
{
    APlayerController* PC = Cast<APlayerController>(GetController());
    UWorld* World = GetWorld();
    if (!PC || !World) return;

    FHitResult FloorHit;
    const bool bHit = TraceFactoryFloorUnderCursor(FloorHit);
    if (!bHit)
    {
        bInfrastructurePlacementValid = false;
        InfrastructurePlacementReason = TEXT("NO FACTORY FLOOR UNDER CURSOR; MOVE CURSOR ONTO AN AUTHORISED FACTORY FLOOR");
        const FLBPlacementPreviewStyle Style = BuildPlacementPreviewStyle(
            false, false, InfrastructurePlacementReason);
        DrawMissingFloorCue(World, Camera, Style);
        PlacementCardData = BuildPlacementCardData(ResolveCurrentPlacementTitle(), Style);
        return;
    }
    const FVector Location = SnapInfrastructureRootToFloor(FloorHit.ImpactPoint);
    InfrastructurePreviewTransform.SetLocation(Location);
    InfrastructurePreviewTransform.SetScale3D(FVector::OneVector);
    CurrentPlacementObstructionDisplayName.Reset();
    CurrentPlacementObstructionStableId.Reset();

    ULBFactoryMachineBuilderSubsystem* Builder = World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    bInfrastructurePlacementValid = Builder
        && Builder->ValidateAGVInfrastructurePlacement(SelectedInfrastructureType,
            SelectedInfrastructureTrainIndex, InfrastructurePreviewTransform,
            InfrastructurePlacementReason);
    if (!bInfrastructurePlacementValid
        && InfrastructurePlacementReason.Contains(TEXT("WORLD OBSTRUCTION")))
    {
        FString BlockingActorLabel;
        FString ComponentLabel;
        const FVector Centre = InfrastructurePreviewTransform.TransformPosition(
            FVector(0.0f, 0.0f, InfrastructurePreviewHalfExtent.Z));
        const FVector CollisionHalfExtent(
            FMath::Max(1.0f, InfrastructurePreviewHalfExtent.X - 2.0f),
            FMath::Max(1.0f, InfrastructurePreviewHalfExtent.Y - 2.0f),
            FMath::Max(0.5f, InfrastructurePreviewHalfExtent.Z - 0.5f));
        if (FindNamedBlockingOverlap(World, Centre, CollisionHalfExtent,
            InfrastructurePreviewTransform.GetRotation(), this,
            BlockingActorLabel, ComponentLabel, &CurrentPlacementObstructionStableId))
        {
            CurrentPlacementObstructionDisplayName = BlockingActorLabel;
            InfrastructurePlacementReason = FormatNamedObstructionReason(
                TEXT("INFRASTRUCTURE ENVELOPE"), BlockingActorLabel, ComponentLabel);
        }
    }
    const bool bDirectional = SelectedInfrastructureType == ELBFactoryAGVInfrastructureType::AGVRouteSegment
        || SelectedInfrastructureType == ELBFactoryAGVInfrastructureType::RouteWaypoint
        || SelectedInfrastructureType == ELBFactoryAGVInfrastructureType::WaitPoint
        || SelectedInfrastructureType == ELBFactoryAGVInfrastructureType::PressTrainHandoff;
    const FLBPlacementPreviewStyle Style = BuildPlacementPreviewStyle(
        true, bInfrastructurePlacementValid, InfrastructurePlacementReason);
    const FLBPlacementPreviewGeometry Geometry = BuildPlacementPreviewGeometry(
        InfrastructurePreviewTransform, FVector(0.0f, 0.0f, InfrastructurePreviewHalfExtent.Z),
        InfrastructurePreviewHalfExtent, Location.Z, true, bDirectional);
    DrawPlacementGroundFootprint(World, InfrastructurePreviewTransform, Geometry, Style);
    DrawPlacementEnvelope(World, InfrastructurePreviewTransform, Geometry, Style);
    DrawPlacementState(World, InfrastructurePreviewTransform, Geometry, Style);
    DrawProcessFlowIntent(World, Geometry);
    UpdatePlacementPresentation(ResolveCurrentPlacementTitle(), Geometry, Style);
}

bool ALBManagementPawn::IsInfrastructurePreviewEnvelopeObstructed(
    UWorld* World, const FTransform& RootTransform, const FVector& HalfExtent,
    const UPrimitiveComponent* TracedSupportComponent, const FVector& TracedImpactNormal,
    const AActor* IgnoredActor)
{
    if (!World || !RootTransform.IsValid() || HalfExtent.GetMin() <= 0.0f) return true;
    ALBPressShopBuildAuthority* Authority = nullptr;
    for (TActorIterator<ALBPressShopBuildAuthority> It(World); It; ++It)
    {
        if (!IsValid(*It)) continue;
        if (Authority) return true;
        Authority = *It;
    }
    if (!Authority) return true;
    constexpr float FloorDatumToleranceCm = 1.0f;
    const FVector Root = RootTransform.GetLocation();
    const FBox Candidate(FVector(-HalfExtent.X, -HalfExtent.Y, 0.0f),
        FVector(HalfExtent.X, HalfExtent.Y, HalfExtent.Z * 2.0f));
    const FBox WorldCandidate = Candidate.TransformBy(RootTransform);
    bool bOnAuthorizedFloor = false;
    for (const FLBPressShopBuildBay& Bay : Authority->BuildBays)
    {
        if (!FMath::IsNearlyEqual(Root.Z, Bay.Centre.Z, FloorDatumToleranceCm)) continue;
        const FBox BayBox(Bay.Centre - Bay.HalfExtent, Bay.Centre + Bay.HalfExtent);
        if (BayBox.ExpandBy(FloorDatumToleranceCm).IsInsideOrOn(WorldCandidate.Min)
            && BayBox.ExpandBy(FloorDatumToleranceCm).IsInsideOrOn(WorldCandidate.Max))
        {
            bOnAuthorizedFloor = true;
            break;
        }
    }
    if (!bOnAuthorizedFloor) return true;
    const FVector CollisionHalfExtent(
        FMath::Max(1.0f, HalfExtent.X - 2.0f),
        FMath::Max(1.0f, HalfExtent.Y - 2.0f),
        FMath::Max(0.5f, HalfExtent.Z - 0.5f));
    const FVector Centre = RootTransform.TransformPosition(FVector(0.0f, 0.0f, HalfExtent.Z));
    FCollisionQueryParams Params(SCENE_QUERY_STAT(LBInfrastructurePlacementEnvelope), false);
    if (IgnoredActor) Params.AddIgnoredActor(IgnoredActor);
    // Ignore only the exact horizontal WorldStatic component proved to end at the candidate
    // root. A machine, wall or raised cube hit by the generic visibility trace therefore
    // remains in the overlap query instead of its whole actor being trusted as "the floor".
    const float SupportTop = TracedSupportComponent
        ? TracedSupportComponent->Bounds.GetBox().Max.Z : TNumericLimits<float>::Max();
    if (TracedSupportComponent
        && TracedSupportComponent->GetCollisionObjectType() == ECC_WorldStatic
        && SupportTop <= Root.Z + FloorDatumToleranceCm
        && FVector::DotProduct(TracedImpactNormal.GetSafeNormal(), FVector::UpVector) >= 0.9f)
    {
        Params.AddIgnoredComponent(TracedSupportComponent);
    }
    return World->OverlapBlockingTestByChannel(Centre, RootTransform.GetRotation(),
        ECC_WorldDynamic, FCollisionShape::MakeBox(CollisionHalfExtent), Params);
}

void ALBManagementPawn::UpdateInfrastructureEditPreview()
{
    UWorld* World = GetWorld();
    if (!World || !IsValid(InspectedInfrastructure))
    {
        CancelInfrastructureEdit(true);
        return;
    }

    FHitResult FloorHit;
    if (!TraceFactoryFloorUnderCursor(FloorHit))
    {
        bInfrastructureEditValid = false;
        InfrastructureEditReason = TEXT("NO FACTORY FLOOR UNDER CURSOR; MOVE CURSOR ONTO AN AUTHORISED FACTORY FLOOR");
        const FLBPlacementPreviewStyle Style = BuildPlacementPreviewStyle(
            false, false, InfrastructureEditReason);
        DrawMissingFloorCue(World, Camera, Style);
        PlacementCardData = BuildPlacementCardData(ResolveCurrentPlacementTitle(), Style);
        return;
    }
    FVector Location = FloorHit.ImpactPoint;
    Location.X = FMath::GridSnap(Location.X, 50.0f);
    Location.Y = FMath::GridSnap(Location.Y, 50.0f);
    // Current factories use one level; retaining the saved pivot height prevents a route
    // centreline, fence or charger from jumping vertically when its footprint is edited.
    Location.Z = InfrastructureEditOriginalTransform.GetLocation().Z;
    InfrastructureEditPreviewTransform.SetLocation(Location);
    InfrastructureEditPreviewTransform.SetScale3D(FVector::OneVector);
    CurrentPlacementObstructionDisplayName.Reset();
    CurrentPlacementObstructionStableId.Reset();

    ULBFactoryMachineBuilderSubsystem* Builder = World->GetSubsystem<ULBFactoryMachineBuilderSubsystem>();
    bInfrastructureEditValid = Builder
        && Builder->CanEditAGVInfrastructure(
            InspectedInfrastructure->GetInfrastructureId(), InfrastructureEditReason)
        && Builder->ValidateAGVInfrastructureTransform(
            InspectedInfrastructure->GetInfrastructureId(), InfrastructureEditPreviewTransform,
            InfrastructureEditReason);
    if (!bInfrastructureEditValid && InfrastructureEditReason.Contains(TEXT("WORLD OBSTRUCTION")))
    {
        FString BlockingActorLabel;
        FString ComponentLabel;
        const FVector Centre = InfrastructureEditPreviewTransform.TransformPosition(
            FVector(0.0f, 0.0f, InfrastructureEditHalfExtent.Z));
        const FVector CollisionHalfExtent(
            FMath::Max(1.0f, InfrastructureEditHalfExtent.X - 2.0f),
            FMath::Max(1.0f, InfrastructureEditHalfExtent.Y - 2.0f),
            FMath::Max(0.5f, InfrastructureEditHalfExtent.Z - 0.5f));
        if (FindNamedBlockingOverlap(World, Centre, CollisionHalfExtent,
            InfrastructureEditPreviewTransform.GetRotation(), InspectedInfrastructure,
            BlockingActorLabel, ComponentLabel, &CurrentPlacementObstructionStableId))
        {
            CurrentPlacementObstructionDisplayName = BlockingActorLabel;
            InfrastructureEditReason = FormatNamedObstructionReason(
                TEXT("INFRASTRUCTURE EDIT ENVELOPE"), BlockingActorLabel, ComponentLabel);
        }
    }
    const ELBFactoryAGVInfrastructureType Type = InspectedInfrastructure->GetInfrastructureType();
    const bool bDirectional = Type == ELBFactoryAGVInfrastructureType::AGVRouteSegment
        || Type == ELBFactoryAGVInfrastructureType::RouteWaypoint
        || Type == ELBFactoryAGVInfrastructureType::WaitPoint
        || Type == ELBFactoryAGVInfrastructureType::PressTrainHandoff;
    const FLBPlacementPreviewStyle Style = BuildPlacementPreviewStyle(
        true, bInfrastructureEditValid, InfrastructureEditReason);
    const FLBPlacementPreviewGeometry Geometry = BuildPlacementPreviewGeometry(
        InfrastructureEditPreviewTransform, FVector(0.0f, 0.0f, InfrastructureEditHalfExtent.Z),
        InfrastructureEditHalfExtent, Location.Z, true, bDirectional);
    DrawPlacementGroundFootprint(World, InfrastructureEditPreviewTransform, Geometry, Style);
    DrawPlacementEnvelope(World, InfrastructureEditPreviewTransform, Geometry, Style);
    DrawPlacementState(World, InfrastructureEditPreviewTransform, Geometry, Style);
    DrawProcessFlowIntent(World, Geometry);
    UpdatePlacementPresentation(ResolveCurrentPlacementTitle(), Geometry, Style);
}
